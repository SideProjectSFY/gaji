#!/usr/bin/env python3
"""
Mattermost 웹훅 알림 모듈
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import requests

logger = logging.getLogger('MattermostNotifier')


class MattermostNotifier:
    """Mattermost 알림 클래스"""
    
    # 알림 레벨
    LEVEL_ERROR = 'error'
    LEVEL_WARNING = 'warning'
    LEVEL_INFO = 'info'
    
    # 색상 코드
    COLOR_ERROR = '#ef4444'      # 빨강
    COLOR_WARNING = '#f59e0b'    # 주황
    COLOR_INFO = '#3b82f6'       # 파랑
    COLOR_SUCCESS = '#22c55e'    # 초록
    
    def __init__(self, webhook_url: Optional[str] = None, enabled: bool = True):
        """
        초기화
        
        Args:
            webhook_url: Mattermost 웹훅 URL
            enabled: 알림 활성화 여부
        """
        self.webhook_url = webhook_url or os.getenv('MATTERMOST_WEBHOOK_URL')
        self.enabled = enabled and bool(self.webhook_url)
        
        if not self.webhook_url and enabled:
            logger.warning("⚠️ Mattermost 웹훅 URL이 설정되지 않았습니다")
            self.enabled = False
        
        # 알림 설정
        self.notification_level = os.getenv('NOTIFICATION_LEVEL', 'warning')  # error, warning, info
        self.username = os.getenv('MATTERMOST_USERNAME', 'DB Monitor')
        self.icon_url = os.getenv('MATTERMOST_ICON_URL', 'https://cdn-icons-png.flaticon.com/512/2721/2721293.png')
        self.channel = os.getenv('MATTERMOST_CHANNEL', '')  # 빈 문자열이면 기본 채널
        
        logger.info(f"Mattermost 알림 {'활성화' if self.enabled else '비활성화'} (레벨: {self.notification_level})")
    
    def should_notify(self, level: str) -> bool:
        """
        알림 전송 여부 판단
        
        Args:
            level: 알림 레벨 (error, warning, info)
        
        Returns:
            알림 전송 여부
        """
        if not self.enabled:
            return False
        
        level_priority = {
            'error': 3,
            'warning': 2,
            'info': 1
        }
        
        return level_priority.get(level, 0) >= level_priority.get(self.notification_level, 0)
    
    def send_message(
        self, 
        text: str, 
        level: str = LEVEL_INFO,
        attachments: Optional[List[Dict]] = None
    ) -> bool:
        """
        단순 메시지 전송
        
        Args:
            text: 메시지 내용
            level: 알림 레벨
            attachments: 첨부 내용
        
        Returns:
            전송 성공 여부
        """
        if not self.should_notify(level):
            return False
        
        try:
            payload = {
                'username': self.username,
                'icon_url': self.icon_url,
                'text': text
            }
            
            if self.channel:
                payload['channel'] = self.channel
            
            if attachments:
                payload['attachments'] = attachments
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✓ Mattermost 알림 전송 성공 (레벨: {level})")
                return True
            else:
                logger.error(f"✗ Mattermost 알림 전송 실패: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Mattermost 알림 전송 오류: {e}")
            return False
    
    def send_monitoring_alert(
        self, 
        health: Dict,
        stats: Dict
    ) -> bool:
        """
        모니터링 알림 전송
        
        Args:
            health: 헬스 체크 결과
            stats: 통계 데이터
        
        Returns:
            전송 성공 여부
        """
        errors = health.get('errors', [])
        warnings = health.get('warnings', [])
        recommendations = health.get('recommendations', [])
        
        # 에러나 경고가 없으면 전송하지 않음
        if not errors and not warnings:
            return False
        
        # 레벨 결정
        level = self.LEVEL_ERROR if errors else self.LEVEL_WARNING
        
        if not self.should_notify(level):
            return False
        
        # 메시지 구성
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 메인 텍스트
        if errors:
            main_text = f"🔴 **데이터베이스 모니터링 에러 감지**"
        else:
            main_text = f"⚠️ **데이터베이스 모니터링 경고**"
        
        # Attachment 구성
        attachments = []
        
        # 에러 섹션
        if errors:
            error_text = "**🔴 에러:**\n" + "\n".join(f"• {err}" for err in errors)
            attachments.append({
                'color': self.COLOR_ERROR,
                'text': error_text
            })
        
        # 경고 섹션
        if warnings:
            warning_text = "**⚠️ 경고:**\n" + "\n".join(f"• {warn}" for warn in warnings)
            attachments.append({
                'color': self.COLOR_WARNING,
                'text': warning_text
            })
        
        # 권장사항 섹션
        if recommendations:
            rec_text = "**💡 권장사항:**\n" + "\n".join(f"• {rec}" for rec in recommendations[:3])  # 최대 3개
            attachments.append({
                'color': self.COLOR_INFO,
                'text': rec_text
            })
        
        # 통계 요약
        summary_fields = []
        
        if stats.get('postgresql'):
            pg = stats['postgresql']
            summary_fields.append({
                'short': True,
                'title': 'PostgreSQL',
                'value': f"캐시: {pg['cache_hit_ratio']:.1f}% | 연결: {pg['total_connections']}"
            })
        
        if stats.get('redis'):
            rd = stats['redis']
            summary_fields.append({
                'short': True,
                'title': 'Redis',
                'value': f"메모리: {rd['memory_usage_pct']:.1f}% | 캐시: {rd['cache_hit_rate_pct']:.1f}%"
            })
        
        if summary_fields:
            attachments.append({
                'color': self.COLOR_INFO,
                'title': '📊 현재 상태',
                'fields': summary_fields
            })
        
        # 푸터
        attachments.append({
            'color': self.COLOR_INFO,
            'text': f"🕐 {timestamp}",
            'footer': 'Database Monitoring System'
        })
        
        return self.send_message(main_text, level, attachments)
    
    def send_critical_alert(
        self,
        title: str,
        description: str,
        details: Optional[Dict] = None
    ) -> bool:
        """
        긴급 알림 전송 (즉시)
        
        Args:
            title: 알림 제목
            description: 설명
            details: 상세 정보
        
        Returns:
            전송 성공 여부
        """
        if not self.enabled:
            return False
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        main_text = f"🚨 **긴급 알림: {title}**"
        
        attachments = [{
            'color': self.COLOR_ERROR,
            'text': description,
            'footer': f'{timestamp} | Database Monitoring System'
        }]
        
        if details:
            fields = [
                {'short': True, 'title': k, 'value': str(v)}
                for k, v in details.items()
            ]
            attachments[0]['fields'] = fields
        
        return self.send_message(main_text, self.LEVEL_ERROR, attachments)
    
    def send_recovery_notification(self, message: str) -> bool:
        """
        복구 알림 전송
        
        Args:
            message: 복구 메시지
        
        Returns:
            전송 성공 여부
        """
        if not self.enabled:
            return False
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        main_text = f"✅ **시스템 복구**"
        
        attachments = [{
            'color': self.COLOR_SUCCESS,
            'text': message,
            'footer': f'{timestamp} | Database Monitoring System'
        }]
        
        return self.send_message(main_text, self.LEVEL_INFO, attachments)
    
    def send_daily_report(self, stats: Dict) -> bool:
        """
        일일 리포트 전송
        
        Args:
            stats: 통계 데이터
        
        Returns:
            전송 성공 여부
        """
        if not self.enabled:
            return False
        
        timestamp = datetime.now().strftime('%Y-%m-%d')
        
        main_text = f"📊 **일일 데이터베이스 리포트** ({timestamp})"
        
        attachments = []
        
        # PostgreSQL 섹션
        if stats.get('postgresql'):
            pg = stats['postgresql']
            pg_text = (
                f"**캐시 히트율:** {pg['cache_hit_ratio']:.2f}%\n"
                f"**연결 수:** {pg['total_connections']} (활성: {pg['active_connections']})\n"
                f"**DB 크기:** {pg['database_size']}\n"
                f"**느린 쿼리:** {pg['slow_queries_count']}개"
            )
            attachments.append({
                'color': self.COLOR_SUCCESS if pg['cache_hit_ratio'] >= 95 else self.COLOR_WARNING,
                'title': '🐘 PostgreSQL',
                'text': pg_text
            })
        
        # Redis 섹션
        if stats.get('redis'):
            rd = stats['redis']
            rd_text = (
                f"**메모리 사용:** {rd['used_memory_mb']} / {rd['maxmemory_mb']} MB ({rd['memory_usage_pct']:.1f}%)\n"
                f"**캐시 히트율:** {rd['cache_hit_rate_pct']:.2f}%\n"
                f"**총 키:** {rd['total_keys']}개\n"
                f"**삭제된 키:** {rd['evicted_keys']}개"
            )
            attachments.append({
                'color': self.COLOR_SUCCESS if rd['memory_usage_pct'] < 80 else self.COLOR_WARNING,
                'title': '🔴 Redis',
                'text': rd_text
            })
        
        # Elasticsearch 섹션
        if stats.get('elasticsearch'):
            es = stats['elasticsearch']
            es_text = (
                f"**클러스터 상태:** {es['cluster_status']}\n"
                f"**인덱스 수:** {es['indices_count']}개\n"
                f"**총 문서:** {es['total_documents']}개\n"
                f"**저장소:** {es['store_mb']} MB"
            )
            attachments.append({
                'color': self.COLOR_SUCCESS if es['cluster_status'] in ('green', 'yellow') else self.COLOR_ERROR,
                'title': '🔎 Elasticsearch',
                'text': es_text
            })
        
        return self.send_message(main_text, self.LEVEL_INFO, attachments)
    
    def test_connection(self) -> bool:
        """
        웹훅 연결 테스트
        
        Returns:
            연결 성공 여부
        """
        if not self.webhook_url:
            logger.error("웹훅 URL이 설정되지 않았습니다")
            return False
        
        try:
            test_message = "✅ Mattermost 알림 연결 테스트 성공!"
            
            payload = {
                'username': self.username,
                'icon_url': self.icon_url,
                'text': test_message
            }
            
            if self.channel:
                payload['channel'] = self.channel
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✓ Mattermost 연결 테스트 성공")
                return True
            else:
                logger.error(f"✗ Mattermost 연결 실패: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Mattermost 연결 오류: {e}")
            return False
