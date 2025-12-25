#!/usr/bin/env python3
"""
로그 로테이션 스크립트
일주일(7일) 이상 된 로그 파일을 자동으로 삭제
"""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('LogRotation')

# 로그 디렉토리
LOG_DIR = Path(os.getenv('LOG_DIR', '/app/logs'))
REPORT_DIR = Path(os.getenv('REPORT_DIR', '/app/reports'))

# 로그 보관 기간 (일)
RETENTION_DAYS = 7


def get_file_age_days(file_path: Path) -> int:
    """파일의 나이를 일 단위로 반환"""
    try:
        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        age = datetime.now() - file_mtime
        return age.days
    except Exception as e:
        logger.error(f"파일 날짜 확인 실패 {file_path}: {e}")
        return 0


def rotate_logs(directory: Path, retention_days: int = RETENTION_DAYS):
    """오래된 로그 파일 삭제"""
    if not directory.exists():
        logger.warning(f"디렉토리가 존재하지 않음: {directory}")
        return
    
    deleted_count = 0
    deleted_size = 0
    kept_count = 0
    
    try:
        # 로그 파일 패턴 (.log, .json, .txt)
        log_patterns = ['*.log', '*.json', '*.txt', '*.log.*']
        
        for pattern in log_patterns:
            for log_file in directory.rglob(pattern):
                if not log_file.is_file():
                    continue
                
                file_age = get_file_age_days(log_file)
                file_size = log_file.stat().st_size
                
                if file_age > retention_days:
                    try:
                        logger.info(f"삭제: {log_file.name} (나이: {file_age}일, 크기: {file_size:,} bytes)")
                        log_file.unlink()
                        deleted_count += 1
                        deleted_size += file_size
                    except Exception as e:
                        logger.error(f"파일 삭제 실패 {log_file}: {e}")
                else:
                    kept_count += 1
        
        logger.info(f"로테이션 완료 - 삭제: {deleted_count}개 ({deleted_size:,} bytes), 유지: {kept_count}개")
        
    except Exception as e:
        logger.error(f"로그 로테이션 실패: {e}")


def cleanup_empty_dirs(directory: Path):
    """빈 디렉토리 정리"""
    if not directory.exists():
        return
    
    try:
        for subdir in directory.rglob('*'):
            if subdir.is_dir() and not any(subdir.iterdir()):
                logger.info(f"빈 디렉토리 삭제: {subdir}")
                subdir.rmdir()
    except Exception as e:
        logger.error(f"빈 디렉토리 정리 실패: {e}")


def get_directory_size(directory: Path) -> int:
    """디렉토리 전체 크기 계산"""
    total_size = 0
    try:
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
    except Exception as e:
        logger.error(f"디렉토리 크기 계산 실패: {e}")
    return total_size


def print_summary():
    """로그 현황 요약 출력"""
    logger.info("=" * 60)
    logger.info("로그 현황 요약")
    logger.info("=" * 60)
    
    for directory in [LOG_DIR, REPORT_DIR]:
        if directory.exists():
            total_size = get_directory_size(directory)
            file_count = sum(1 for _ in directory.rglob('*') if _.is_file())
            
            logger.info(f"{directory.name}/")
            logger.info(f"  파일 수: {file_count}개")
            logger.info(f"  전체 크기: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")
        else:
            logger.info(f"{directory.name}/ - 존재하지 않음")
    
    logger.info("=" * 60)


def main():
    """메인 실행 함수"""
    logger.info("로그 로테이션 시작")
    logger.info(f"보관 기간: {RETENTION_DAYS}일")
    
    # 현재 상태 출력
    print_summary()
    
    # 로그 로테이션 실행
    logger.info(f"\n로그 디렉토리 로테이션: {LOG_DIR}")
    rotate_logs(LOG_DIR, RETENTION_DAYS)
    
    logger.info(f"\n리포트 디렉토리 로테이션: {REPORT_DIR}")
    rotate_logs(REPORT_DIR, RETENTION_DAYS)
    
    # 빈 디렉토리 정리
    logger.info("\n빈 디렉토리 정리")
    cleanup_empty_dirs(LOG_DIR)
    cleanup_empty_dirs(REPORT_DIR)
    
    # 최종 상태 출력
    logger.info("\n로테이션 완료 후 현황")
    print_summary()
    
    logger.info("로그 로테이션 완료")


if __name__ == '__main__':
    main()
