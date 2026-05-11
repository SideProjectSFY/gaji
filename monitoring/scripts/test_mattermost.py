#!/usr/bin/env python3
"""
Mattermost 알림 테스트 스크립트
"""

import os
import sys
import logging
from mattermost_notifier import MattermostNotifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_all_notifications():
    """모든 알림 타입 테스트"""
    
    webhook_url = os.getenv('MATTERMOST_WEBHOOK_URL')
    if not webhook_url:
        logger.error("MATTERMOST_WEBHOOK_URL 환경 변수가 설정되지 않았습니다")
        return False
    
    notifier = MattermostNotifier(webhook_url)
    
    # 1. 연결 테스트
    print("\n1️⃣ 연결 테스트...")
    if not notifier.test_connection():
        print("❌ 연결 실패")
        return False
    print("✅ 연결 성공")
    
    # 2. 경고 알림 테스트
    print("\n2️⃣ 경고 알림 테스트...")
    health = {
        'errors': [],
        'warnings': [
            'Redis 메모리 사용률이 85%입니다',
            'PostgreSQL 캐시 히트율이 92%입니다'
        ],
        'recommendations': [
            'Redis maxmemory 증가 권장',
            'shared_buffers 설정 검토'
        ]
    }
    
    stats = {
        'postgresql': {
            'cache_hit_ratio': 92.5,
            'total_connections': 15,
            'active_connections': 5,
            'database_size': '150 MB',
            'slow_queries_count': 2
        },
        'redis': {
            'memory_usage_pct': 85.2,
            'cache_hit_rate_pct': 88.5,
            'used_memory_mb': 170.4,
            'maxmemory_mb': 200.0,
            'total_keys': 1500,
            'evicted_keys': 50
        }
    }
    
    notifier.send_monitoring_alert(health, stats)
    print("✅ 경고 알림 전송 완료")
    
    # 3. 에러 알림 테스트
    print("\n3️⃣ 에러 알림 테스트...")
    health['errors'] = ['Redis 메모리 사용률이 95%입니다!']
    notifier.send_monitoring_alert(health, stats)
    print("✅ 에러 알림 전송 완료")
    
    # 4. 긴급 알림 테스트
    print("\n4️⃣ 긴급 알림 테스트...")
    notifier.send_critical_alert(
        title="PostgreSQL 연결 불가",
        description="데이터베이스 서버에 연결할 수 없습니다!",
        details={
            '호스트': 'db.example.com',
            '포트': '5432',
            '상태': '연결 거부',
            '시도 횟수': '3'
        }
    )
    print("✅ 긴급 알림 전송 완료")
    
    # 5. 일일 리포트 테스트
    print("\n5️⃣ 일일 리포트 테스트...")
    stats['elasticsearch'] = {
        'cluster_status': 'green',
        'indices_count': 3,
        'total_documents': 10000,
        'store_mb': 58.6
    }
    notifier.send_daily_report(stats)
    print("✅ 일일 리포트 전송 완료")
    
    print("\n✅ 모든 테스트 완료!")
    return True


if __name__ == '__main__':
    sys.exit(0 if test_all_notifications() else 1)
