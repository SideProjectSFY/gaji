#!/usr/bin/env python3
"""
일일 통합 모니터링 리포트 전송 스크립트
매일 정해진 시간에 실행되어 하루 동안의 시스템 상태 요약을 Mattermost로 전송합니다.
"""

import os
import sys
import json
import logging
from datetime import datetime
from mattermost_notifier import MattermostNotifier

# 로깅 설정
LOG_DIR = os.getenv('LOG_DIR', '/app/logs')
REPORT_DIR = os.getenv('REPORT_DIR', '/app/reports')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{LOG_DIR}/monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DailyReport')

def load_daily_report():
    """최신 일일 리포트 파일 로드"""
    report_file = os.path.join(REPORT_DIR, 'daily_report.json')
    
    if not os.path.exists(report_file):
        logger.error(f"리포트 파일을 찾을 수 없습니다: {report_file}")
        return None
        
    try:
        with open(report_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"리포트 파일 읽기 실패: {e}")
        return None

def main():
    """메인 실행 함수"""
    logger.info("일일 리포트 전송 시작")
    
    # 1. 리포트 데이터 로드
    report = load_daily_report()
    if not report:
        logger.error("전송할 리포트 데이터가 없습니다.")
        return 1
    
    # 2. Mattermost 알림 전송
    try:
        notifier = MattermostNotifier()
        
        # 헬스 체크 결과 요약
        health = report.get('health', {})
        errors = len(health.get('errors', []))
        warnings = len(health.get('warnings', []))
        
        # 상태에 따른 이모지 및 색상 결정
        if errors > 0:
            status_emoji = "🔴"
            color = "#FF0000"  # Red
            status_text = f"위험 ({errors}개의 에러)"
        elif warnings > 0:
            status_emoji = "⚠️"
            color = "#FFA500"  # Orange
            status_text = f"주의 ({warnings}개의 경고)"
        else:
            status_emoji = "✅"
            color = "#008000"  # Green
            status_text = "정상"
            
        # 메시지 본문 작성
        title = f"{status_emoji} 일일 데이터베이스 모니터링 리포트"
        
        # 주요 통계 요약
        pg = report.get('postgresql', {})
        rd = report.get('redis', {})
        es = report.get('elasticsearch', {})
        
        stats_summary = []
        
        if pg:
            stats_summary.append(f"**PostgreSQL**: 연결 {pg.get('active_connections', 0)}/{pg.get('total_connections', 0)}, 캐시 {pg.get('cache_hit_ratio', 0)}%")
            
        if rd:
            stats_summary.append(f"**Redis**: 메모리 {rd.get('memory_usage_pct', 0)}%, 캐시 {rd.get('cache_hit_rate_pct', 0)}%")
            
        if es:
            stats_summary.append(f"**Elasticsearch**: 인덱스 {es.get('indices_count', 0)}개, 문서 {es.get('total_documents', 0)}개")
            
        description = "\n".join(stats_summary)
        
        # 상세 필드 구성
        fields = []
        
        # 1. 시스템 상태
        fields.append({
            "short": True,
            "title": "시스템 상태",
            "value": status_text
        })
        
        # 2. 리포트 생성 시간
        fields.append({
            "short": True,
            "title": "생성 시간",
            "value": report.get('timestamp', datetime.now().isoformat())
        })
        
        # 3. 발견된 이슈 (있는 경우)
        if errors > 0 or warnings > 0:
            issues = []
            for err in health.get('errors', []):
                issues.append(f"🔴 {err}")
            for warn in health.get('warnings', []):
                issues.append(f"⚠️ {warn}")
            
            # 너무 길면 자르기
            if len(issues) > 5:
                issues = issues[:5] + [f"...외 {len(issues)-5}건"]
                
            fields.append({
                "short": False,
                "title": "주요 이슈",
                "value": "\n".join(issues)
            })
            
        # 4. 권장 사항 (있는 경우)
        recommendations = health.get('recommendations', [])
        if recommendations:
            fields.append({
                "short": False,
                "title": "권장 조치사항",
                "value": "\n".join([f"💡 {rec}" for rec in recommendations[:3]])
            })

        # 알림 전송
        notifier.send_message(
            title=title,
            text=description,
            color=color,
            fields=fields
        )
        
        logger.info("✓ 일일 리포트 전송 완료")
        return 0
        
    except Exception as e:
        logger.error(f"일일 리포트 전송 실패: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
