#!/usr/bin/env python3
"""
통합 데이터베이스 모니터링 시스템
PostgreSQL, Redis, Elasticsearch의 통합 메트릭 수집
"""

import os
import sys
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from logging.handlers import TimedRotatingFileHandler

import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import requests
from mattermost_notifier import MattermostNotifier

# 로그 디렉토리 생성
LOG_DIR = os.getenv('LOG_DIR', '/app/logs')
os.makedirs(LOG_DIR, exist_ok=True)

# 로깅 설정 (7일 보관, 매일 로테이션)
logger = logging.getLogger('UnifiedMonitor')
logger.setLevel(logging.INFO)

# 파일 핸들러 (일일 로테이션, 7일 보관)
file_handler = TimedRotatingFileHandler(
    f'{LOG_DIR}/monitor.log',
    when='midnight',
    interval=1,
    backupCount=7,
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# 콘솔 핸들러
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger.addHandler(file_handler)
logger.addHandler(console_handler)


class UnifiedMonitor:
    """통합 모니터링 클래스"""
    
    def __init__(self):
        """초기화"""
        self.pg_conn = None
        self.redis_client = None
        self.elasticsearch_url = os.getenv('ELASTICSEARCH_URL', 'http://elasticsearch:9200').rstrip('/')
        self.notifier = MattermostNotifier()
        self._connect_databases()
    
    def _connect_databases(self):
        """데이터베이스 연결"""
        # PostgreSQL 연결
        try:
            self.pg_conn = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                connect_timeout=10
            )
            logger.info("✓ PostgreSQL 연결 성공")
        except Exception as e:
            logger.error(f"✗ PostgreSQL 연결 실패: {e}")
            self.pg_conn = None
        
        # Redis 연결
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'redis'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=True,
                socket_connect_timeout=10
            )
            self.redis_client.ping()
            logger.info("✓ Redis 연결 성공")
        except Exception as e:
            logger.error(f"✗ Redis 연결 실패: {e}")
            self.redis_client = None
        
        # Elasticsearch 연결
        try:
            response = requests.get(f"{self.elasticsearch_url}/_cluster/health", timeout=10)
            response.raise_for_status()
            logger.info("✓ Elasticsearch 연결 성공")
        except Exception as e:
            logger.error(f"✗ Elasticsearch 연결 실패: {e}")
    
    def get_postgresql_stats(self) -> Optional[Dict[str, Any]]:
        """PostgreSQL 통계 수집"""
        if not self.pg_conn:
            return None
        
        try:
            cursor = self.pg_conn.cursor(cursor_factory=RealDictCursor)
            stats = {}
            
            # 1. 캐시 히트율
            cursor.execute("""
                SELECT 
                    ROUND(100.0 * blks_hit / NULLIF(blks_hit + blks_read, 0), 2) as cache_hit_ratio
                FROM pg_stat_database 
                WHERE datname = current_database()
            """)
            result = cursor.fetchone()
            stats['cache_hit_ratio'] = float(result['cache_hit_ratio']) if result['cache_hit_ratio'] else 0
            
            # 2. 연결 수
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_connections,
                    COUNT(CASE WHEN state = 'active' THEN 1 END) as active_connections,
                    COUNT(CASE WHEN state = 'idle' THEN 1 END) as idle_connections
                FROM pg_stat_activity
            """)
            connections = cursor.fetchone()
            stats.update(dict(connections))
            
            # 3. DB 크기
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database())) as db_size")
            stats['database_size'] = cursor.fetchone()['db_size']
            
            # 4. 트랜잭션 통계
            cursor.execute("""
                SELECT 
                    xact_commit as commits,
                    xact_rollback as rollbacks,
                    ROUND(100.0 * xact_commit / NULLIF(xact_commit + xact_rollback, 0), 2) as commit_ratio
                FROM pg_stat_database
                WHERE datname = current_database()
            """)
            txn = cursor.fetchone()
            stats.update(dict(txn))
            
            # 5. 느린 쿼리 (pg_stat_statements 있을 경우)
            try:
                cursor.execute("""
                    SELECT COUNT(*) as slow_queries_count
                    FROM pg_stat_statements 
                    WHERE mean_exec_time > 1000
                """)
                stats['slow_queries_count'] = cursor.fetchone()['slow_queries_count']
            except:
                stats['slow_queries_count'] = 0
            
            # 6. 테이블 통계 (상위 5개)
            cursor.execute("""
                SELECT 
                    schemaname || '.' || tablename as table_name,
                    n_live_tup as live_rows,
                    n_dead_tup as dead_rows,
                    ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_ratio
                FROM pg_stat_user_tables
                WHERE n_live_tup > 0
                ORDER BY n_dead_tup DESC
                LIMIT 5
            """)
            stats['top_tables_by_dead_tuples'] = [dict(row) for row in cursor.fetchall()]
            
            cursor.close()
            logger.info("✓ PostgreSQL 통계 수집 완료")
            return stats
            
        except Exception as e:
            logger.error(f"✗ PostgreSQL 통계 수집 실패: {e}")
            return None
    
    def get_redis_stats(self) -> Optional[Dict[str, Any]]:
        """Redis 통계 수집"""
        if not self.redis_client:
            return None
        
        try:
            stats = {}
            
            # 1. 메모리 정보
            info_memory = self.redis_client.info('memory')
            stats['used_memory_mb'] = round(info_memory['used_memory'] / (1024 * 1024), 2)
            stats['used_memory_peak_mb'] = round(info_memory['used_memory_peak'] / (1024 * 1024), 2)
            stats['maxmemory_mb'] = round(info_memory.get('maxmemory', 0) / (1024 * 1024), 2)
            stats['mem_fragmentation_ratio'] = info_memory['mem_fragmentation_ratio']
            
            # 메모리 사용률
            if stats['maxmemory_mb'] > 0:
                stats['memory_usage_pct'] = round(
                    stats['used_memory_mb'] / stats['maxmemory_mb'] * 100, 2
                )
            else:
                stats['memory_usage_pct'] = 0
            
            # 2. 성능 통계
            info_stats = self.redis_client.info('stats')
            stats['total_commands'] = info_stats['total_commands_processed']
            stats['ops_per_sec'] = info_stats['instantaneous_ops_per_sec']
            stats['keyspace_hits'] = info_stats['keyspace_hits']
            stats['keyspace_misses'] = info_stats['keyspace_misses']
            stats['evicted_keys'] = info_stats['evicted_keys']
            stats['expired_keys'] = info_stats['expired_keys']
            stats['rejected_connections'] = info_stats['rejected_connections']
            
            # 캐시 히트율
            total_ops = stats['keyspace_hits'] + stats['keyspace_misses']
            stats['cache_hit_rate_pct'] = round(
                stats['keyspace_hits'] / total_ops * 100, 2
            ) if total_ops > 0 else 0
            
            # 3. 클라이언트 정보
            info_clients = self.redis_client.info('clients')
            stats['connected_clients'] = info_clients['connected_clients']
            stats['blocked_clients'] = info_clients['blocked_clients']
            
            # 4. 키스페이스 정보
            info_keyspace = self.redis_client.info('keyspace')
            total_keys = sum(
                db_info['keys'] 
                for db_info in info_keyspace.values()
            )
            stats['total_keys'] = total_keys
            
            # 5. 슬로우 로그 (최근 5개)
            slow_logs = self.redis_client.slowlog_get(5)
            stats['recent_slow_commands'] = [
                {
                    'duration_ms': log['duration'] / 1000,
                    'command': ' '.join(str(arg) for arg in log['command'][:3])
                }
                for log in slow_logs
            ]
            
            logger.info("✓ Redis 통계 수집 완료")
            return stats
            
        except Exception as e:
            logger.error(f"✗ Redis 통계 수집 실패: {e}")
            return None
    
    def get_elasticsearch_stats(self) -> Optional[Dict[str, Any]]:
        """Elasticsearch 통계 수집"""
        try:
            health = requests.get(f"{self.elasticsearch_url}/_cluster/health", timeout=10).json()
            indices = requests.get(
                f"{self.elasticsearch_url}/_cat/indices?format=json&bytes=mb",
                timeout=10
            ).json()

            total_docs = 0
            total_store_mb = 0.0
            index_details = []
            for index in indices:
                docs = int(index.get('docs.count') or 0)
                store_mb = float(index.get('store.size') or 0)
                total_docs += docs
                total_store_mb += store_mb
                index_details.append({
                    'name': index.get('index'),
                    'status': index.get('status'),
                    'document_count': docs,
                    'store_mb': round(store_mb, 2)
                })

            logger.info("✓ Elasticsearch 통계 수집 완료")
            return {
                'cluster_status': health.get('status'),
                'active_shards': health.get('active_shards'),
                'indices_count': len(index_details),
                'total_documents': total_docs,
                'store_mb': round(total_store_mb, 2),
                'indices': index_details
            }
        except Exception as e:
            logger.error(f"✗ Elasticsearch 통계 수집 실패: {e}")
            return None
    
    def analyze_health(self, stats: Dict) -> Dict[str, list]:
        """시스템 헬스 체크 및 경고 생성"""
        warnings = []
        errors = []
        recommendations = []
        
        # PostgreSQL 체크
        if stats.get('postgresql'):
            pg = stats['postgresql']
            
            if pg['cache_hit_ratio'] < 95:
                warnings.append(f"PostgreSQL 캐시 히트율이 낮습니다: {pg['cache_hit_ratio']}%")
                recommendations.append("shared_buffers 설정을 늘리거나 자주 사용하는 테이블에 인덱스 추가")
            
            if pg.get('slow_queries_count', 0) > 10:
                warnings.append(f"느린 쿼리가 많습니다: {pg['slow_queries_count']}개")
                recommendations.append("pg_stat_statements로 느린 쿼리 분석 필요")
            
            if pg['active_connections'] > 50:
                warnings.append(f"활성 연결이 많습니다: {pg['active_connections']}개")
            
            # Dead tuple 체크
            for table in pg.get('top_tables_by_dead_tuples', []):
                if table['dead_ratio'] > 20:
                    warnings.append(
                        f"테이블 {table['table_name']}에 dead tuple이 많습니다: {table['dead_ratio']}%"
                    )
                    recommendations.append(f"VACUUM {table['table_name']} 실행 권장")
        
        # Redis 체크
        if stats.get('redis'):
            rd = stats['redis']
            
            if rd['memory_usage_pct'] > 90:
                errors.append(f"Redis 메모리 사용률이 위험합니다: {rd['memory_usage_pct']}%")
                recommendations.append("maxmemory 증가 또는 TTL 설정 검토")
            elif rd['memory_usage_pct'] > 80:
                warnings.append(f"Redis 메모리 사용률이 높습니다: {rd['memory_usage_pct']}%")
            
            if rd['cache_hit_rate_pct'] < 80:
                warnings.append(f"Redis 캐시 히트율이 낮습니다: {rd['cache_hit_rate_pct']}%")
                recommendations.append("캐시 전략 재검토 또는 TTL 조정")
            
            if rd['evicted_keys'] > 100:
                warnings.append(f"Redis 키가 많이 삭제되고 있습니다: {rd['evicted_keys']}개")
                recommendations.append("maxmemory 증가 필요")
            
            if rd['mem_fragmentation_ratio'] > 1.5:
                warnings.append(f"Redis 메모리 단편화가 높습니다: {rd['mem_fragmentation_ratio']}")
                recommendations.append("Redis 재시작 고려")
            
            if rd['rejected_connections'] > 0:
                errors.append(f"Redis 연결 거부 발생: {rd['rejected_connections']}개")
                recommendations.append("maxclients 설정 증가 필요")
        
        # Elasticsearch 체크
        if stats.get('elasticsearch'):
            es = stats['elasticsearch']

            if es.get('cluster_status') == 'red':
                errors.append("Elasticsearch 클러스터 상태가 red입니다")
                recommendations.append("Elasticsearch shard allocation과 disk watermark를 확인")
            elif es.get('cluster_status') == 'yellow':
                warnings.append("Elasticsearch 클러스터 상태가 yellow입니다")

            if es.get('store_mb', 0) > 10240:
                warnings.append(f"Elasticsearch 저장소 사용량이 큽니다: {es['store_mb']} MB")
                recommendations.append("오래된 인덱스 정리 또는 rollover 정책 검토")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'recommendations': recommendations
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """통합 리포트 생성"""
        logger.info("=" * 80)
        logger.info("통합 모니터링 리포트 생성 시작")
        logger.info("=" * 80)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'postgresql': self.get_postgresql_stats(),
            'redis': self.get_redis_stats(),
            'elasticsearch': self.get_elasticsearch_stats()
        }
        
        # 헬스 체크
        report['health'] = self.analyze_health(report)
        
        # 콘솔 출력
        self._print_report(report)
        
        # JSON 파일로 저장
        self._save_report(report)
        
        # Mattermost 알림 전송
        health = report['health']
        if health['errors'] or health['warnings']:
            logger.info("에러/경고 감지, Mattermost 알림 전송 중...")
            self.notifier.send_monitoring_alert(health, report)
        else:
            logger.info("✅ 시스템 정상, 알림 전송 생략")
        
        return report
    
    def check_critical_thresholds(self, stats: Dict) -> None:
        """
        긴급 임계값 체크 및 즉시 알림
        (리포트 생성과 별도로 실시간 체크)
        """
        # Redis 메모리 위험 수준
        if stats.get('redis'):
            rd = stats['redis']
            if rd['memory_usage_pct'] > 95:
                self.notifier.send_critical_alert(
                    title="Redis 메모리 부족",
                    description=f"Redis 메모리 사용률이 {rd['memory_usage_pct']:.1f}%입니다!",
                    details={
                        '사용 메모리': f"{rd['used_memory_mb']} MB",
                        '최대 메모리': f"{rd['maxmemory_mb']} MB",
                        '삭제된 키': f"{rd['evicted_keys']}개",
                        '권장 조치': 'maxmemory 증가 또는 불필요한 키 삭제'
                    }
                )
        
        # PostgreSQL 연결 수 과다
        if stats.get('postgresql'):
            pg = stats['postgresql']
            if pg['total_connections'] > 80:  # max_connections의 80%
                self.notifier.send_critical_alert(
                    title="PostgreSQL 연결 수 과다",
                    description=f"PostgreSQL 연결 수가 {pg['total_connections']}개입니다!",
                    details={
                        '총 연결': f"{pg['total_connections']}개",
                        '활성 연결': f"{pg['active_connections']}개",
                        '권장 조치': '커넥션 풀 설정 확인 또는 max_connections 증가'
                    }
                )
    
    def _print_report(self, report: Dict):
        """리포트 콘솔 출력"""
        print(f"\n{'='*80}")
        print(f"통합 데이터베이스 모니터링 리포트")
        print(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        # PostgreSQL
        if report['postgresql']:
            pg = report['postgresql']
            print(f"\n[PostgreSQL]")
            print(f"  캐시 히트율: {pg['cache_hit_ratio']:.2f}%")
            print(f"  연결 수: {pg['total_connections']} (활성: {pg['active_connections']}, 유휴: {pg['idle_connections']})")
            print(f"  DB 크기: {pg['database_size']}")
            print(f"  커밋 비율: {pg['commit_ratio']:.2f}%")
            print(f"  느린 쿼리: {pg['slow_queries_count']}개")
        
        # Redis
        if report['redis']:
            rd = report['redis']
            print(f"\n[Redis]")
            print(f"  메모리 사용: {rd['used_memory_mb']} MB / {rd['maxmemory_mb']} MB ({rd['memory_usage_pct']}%)")
            print(f"  캐시 히트율: {rd['cache_hit_rate_pct']}%")
            print(f"  총 키: {rd['total_keys']}개")
            print(f"  초당 명령어: {rd['ops_per_sec']}")
            print(f"  연결 수: {rd['connected_clients']}개")
            print(f"  삭제된 키: {rd['evicted_keys']}개")
        
        # Elasticsearch
        if report['elasticsearch']:
            es = report['elasticsearch']
            print(f"\n[Elasticsearch]")
            print(f"  클러스터 상태: {es['cluster_status']}")
            print(f"  인덱스 수: {es['indices_count']}개")
            print(f"  총 문서: {es['total_documents']}개")
            print(f"  저장소 사용량: {es['store_mb']} MB")
        
        # 헬스 체크
        health = report['health']
        
        if health['errors']:
            print(f"\n[🔴 에러]")
            for error in health['errors']:
                print(f"  • {error}")
        
        if health['warnings']:
            print(f"\n[⚠️ 경고]")
            for warning in health['warnings']:
                print(f"  • {warning}")
        
        if health['recommendations']:
            print(f"\n[💡 권장사항]")
            for rec in health['recommendations']:
                print(f"  • {rec}")
        
        if not health['errors'] and not health['warnings']:
            print(f"\n[✅ 상태] 모든 시스템 정상 작동 중")
        
        print(f"\n{'='*80}\n")
    
    def _save_report(self, report: Dict):
        """리포트 파일 저장"""
        try:
            # 일일 리포트 (덮어쓰기)
            daily_file = f"{os.getenv('REPORT_DIR', '/app/reports')}/daily_report.json"
            with open(daily_file, 'w') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            # 이력 보관 (날짜별)
            date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            history_file = f"{os.getenv('REPORT_DIR', '/app/reports')}/report_{date_str}.json"
            with open(history_file, 'w') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ 리포트 저장 완료: {daily_file}")
            
            # 7일 이상 된 이력 파일 삭제
            self._cleanup_old_reports()
            
        except Exception as e:
            logger.error(f"✗ 리포트 저장 실패: {e}")
    
    def _cleanup_old_reports(self):
        """오래된 리포트 파일 정리"""
        try:
            report_dir = os.getenv('REPORT_DIR', '/app/reports')
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for filename in os.listdir(report_dir):
                if filename.startswith('report_') and filename.endswith('.json'):
                    filepath = os.path.join(report_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    if file_time < cutoff_date:
                        os.remove(filepath)
                        logger.info(f"✓ 오래된 리포트 삭제: {filename}")
        
        except Exception as e:
            logger.error(f"✗ 리포트 정리 실패: {e}")
    
    def close(self):
        """연결 종료"""
        if self.pg_conn:
            self.pg_conn.close()
            logger.info("PostgreSQL 연결 종료")


def main():
    """메인 실행 함수"""
    try:
        monitor = UnifiedMonitor()
        monitor.generate_report()
        monitor.close()
        return 0
    except Exception as e:
        logger.error(f"모니터링 실패: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
