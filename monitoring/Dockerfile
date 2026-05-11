FROM python:3.11-alpine

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 타임존 설정
RUN apk add --no-cache tzdata && \
    cp /usr/share/zoneinfo/Asia/Seoul /etc/localtime && \
    echo "Asia/Seoul" > /etc/timezone

# 필요한 패키지 설치
RUN apk add --no-cache \
    postgresql-client \
    redis \
    dcron \
    bash \
    && rm -rf /var/cache/apk/*

# Python 패키지 설치
RUN uv pip install --system --no-cache \
    psycopg2-binary \
    redis \
    schedule \
    requests \
    flask \
    gunicorn

WORKDIR /app

# 스크립트 복사 (빌드 컨텍스트가 프로젝트 루트이므로 monitoring/ 경로 포함)
COPY monitoring/scripts/ /app/scripts/
COPY monitoring/config/crontab /etc/crontabs/root

# 실행 권한 부여
RUN chmod +x /app/scripts/*.py && \
    chmod 0644 /etc/crontabs/root

# 로그 디렉토리 생성
RUN mkdir -p /app/logs /app/reports

# Entrypoint 스크립트 생성
RUN echo '#!/bin/bash' > /entrypoint.sh && \
    echo 'set -e' >> /entrypoint.sh && \
    echo 'echo "Starting monitor service..."' >> /entrypoint.sh && \
    echo 'echo "Testing Python environment..."' >> /entrypoint.sh && \
    echo 'python3 --version' >> /entrypoint.sh && \
    echo 'echo "Starting dashboard with Gunicorn on port 5000..."' >> /entrypoint.sh && \
    echo 'cd /app/scripts && gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 60 --access-logfile /app/logs/gunicorn-access.log --error-logfile /app/logs/gunicorn-error.log dashboard:app &' >> /entrypoint.sh && \
    echo 'DASHBOARD_PID=$!' >> /entrypoint.sh && \
    echo 'echo "Dashboard started with PID $DASHBOARD_PID"' >> /entrypoint.sh && \
    echo 'echo "Starting crond..."' >> /entrypoint.sh && \
    echo 'crond -f -d 8' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

EXPOSE 5000

CMD ["/entrypoint.sh"]
