# 🎮 Gaji Monitoring System

실시간 인프라 모니터링 시스템 - PostgreSQL, Redis, Elasticsearch의 통합 모니터링 및 대시보드

## 📊 주요 기능

### 1. 실시간 대시보드

- **URL**: `http://localhost:5001`
- **자동 갱신**: 5초마다 자동으로 메트릭 업데이트
- **반응형 디자인**: 모바일/태블릿/데스크톱 모두 지원

### 2. 모니터링 메트릭

#### PostgreSQL 🐘

- **Cache Hit Rate**: 캐시 히트율 (95% 이상 권장)
- **Active Connections**: 활성 연결 수 / 최대 연결 수
- **Database Size**: 데이터베이스 크기
- **Total Queries**: 총 쿼리 실행 수

#### Redis ⚡

- **Hit Rate**: 캐시 히트율 (90% 이상 권장)
- **Memory Usage**: 메모리 사용량 / 전체 메모리
- **Connected Clients**: 연결된 클라이언트 수
- **Total Keys**: 저장된 키 개수

#### Elasticsearch 🔎

- **Cluster Status**: 클러스터 상태
- **Indices**: 인덱스 수
- **Total Documents**: 저장된 문서 수
- **Store**: 저장소 사용량

### 3. 자동 스케줄 모니터링 (Cron)

- **매 시간 정각**: 통합 모니터링 실행
- **매일 오전 7시**: 일일 상세 리포트 생성
- **매일 오전 9시**: Mattermost로 일일 리포트 전송

## 🚀 사용 방법

### 대시보드 접속

```bash
# 프로덕션 환경
http://localhost:5001

# Docker 컨테이너 내부
http://gaji-monitor:5000
```

### API 엔드포인트

#### 메트릭 조회

```bash
curl http://localhost:5001/api/metrics
```

**응답 예시**:

```json
{
  "timestamp": "2025-12-25T14:12:00.000000",
  "postgresql": {
    "status": "healthy",
    "cache_hit_rate": 98.5,
    "active_connections": 5,
    "max_connections": 100,
    "database_size": 52428800,
    "total_queries": 1234567
  },
  "redis": {
    "status": "healthy",
    "used_memory": 10485760,
    "total_system_memory": 4294967296,
    "connected_clients": 3,
    "total_keys": 456,
    "hit_rate": 95.2
  },
  "elasticsearch": {
    "status": "healthy",
    "cluster_status": "green",
    "indices_count": 2,
    "total_documents": 150,
    "store_mb": 15.2
  }
}
```

#### 헬스체크

```bash
curl http://localhost:5001/health
```

## 📁 디렉토리 구조

```
monitoring/
├── Dockerfile              # Docker 이미지 정의
├── README.md              # 이 문서
├── requirements.txt       # Python 패키지 목록
├── config/
│   └── crontab           # Cron 스케줄 정의
├── scripts/
│   ├── dashboard.py      # 웹 대시보드 (Flask)
│   ├── unified_monitor.py    # 통합 모니터링
│   ├── send_daily_report.py  # 일일 리포트 전송
│   └── mattermost_notifier.py # Mattermost 알림
├── logs/                 # 로그 파일
└── reports/             # 생성된 리포트
```

## 🔧 환경 변수

```bash
# PostgreSQL
DB_HOST=postgres
DB_NAME=gaji_db
DB_USER=gaji_user
DB_PASSWORD=your_password

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Elasticsearch
ELASTICSEARCH_URL=http://elasticsearch:9200

# Dashboard
DASHBOARD_PORT=5000

# Mattermost (선택사항)
MATTERMOST_WEBHOOK_URL=https://your-mattermost.com/hooks/xxx
```

## 📊 상태 임계값

### PostgreSQL

- ✅ **Good**: Cache Hit Rate ≥ 95%
- ⚠️ **Warning**: 85% ≤ Cache Hit Rate < 95%
- ❌ **Bad**: Cache Hit Rate < 85%

### Redis

- ✅ **Good**: Hit Rate ≥ 90%
- ⚠️ **Warning**: 70% ≤ Hit Rate < 90%
- ❌ **Bad**: Hit Rate < 70%

### Elasticsearch

- ✅ **Good**: Cluster status green/yellow
- ⚠️ **Warning**: Cluster status yellow
- ❌ **Bad**: Cluster status red

## 🛠️ 개발 가이드

### 로컬 실행 (개발 모드)

```bash
cd monitoring

# 가상 환경 생성
python3 -m venv venv
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt

# 환경 변수 설정
export DB_HOST=localhost
export DB_NAME=gaji_db
export DB_USER=gaji_user
export DB_PASSWORD=your_password
export REDIS_HOST=localhost
export CHROMADB_HOST=localhost

# 대시보드 실행
python scripts/dashboard.py
```

### Docker 빌드

```bash
# 이미지 빌드
docker compose -f docker-compose.prod.yml build monitor

# 컨테이너 실행
docker compose -f docker-compose.prod.yml up -d monitor

# 로그 확인
docker logs -f gaji-monitor
```

## 📈 모니터링 베스트 프랙티스

1. **정기적 확인**: 매일 대시보드를 확인하여 이상 징후 파악
2. **임계값 모니터링**: Warning 상태가 지속되면 조사 필요
3. **로그 분석**: `/app/logs/monitor.log`에서 상세 로그 확인
4. **리포트 검토**: `/app/reports/`의 일일 리포트 분석
5. **알림 설정**: Mattermost Webhook 설정으로 실시간 알림 수신

## 🐛 트러블슈팅

### 대시보드 접속 불가

```bash
# 컨테이너 상태 확인
docker ps | grep monitor

# 로그 확인
docker logs gaji-monitor

# 포트 확인
netstat -an | grep 5001
```

### 메트릭 수집 실패

```bash
# 데이터베이스 연결 확인
docker exec gaji-monitor python3 -c "
import psycopg2
conn = psycopg2.connect(host='postgres', database='gaji_db', user='gaji_user', password='your_password')
print('PostgreSQL OK')
"

# Redis 연결 확인
docker exec gaji-monitor python3 -c "
import redis
r = redis.Redis(host='redis')
r.ping()
print('Redis OK')
"
```

### Cron 작업 확인

```bash
# Cron 로그 확인
docker exec gaji-monitor cat /app/logs/cron.log

# Crontab 확인
docker exec gaji-monitor cat /etc/crontabs/root
```

## 📸 스크린샷

![Dashboard Preview](https://via.placeholder.com/800x500?text=Gaji+Monitoring+Dashboard)

_실시간 대시보드에서 모든 인프라 메트릭을 한눈에 확인할 수 있습니다._

## 📝 변경 이력

### v1.1.0 (2025-12-25)

- ✨ 실시간 웹 대시보드 추가
- 🎨 반응형 UI 디자인
- 📊 자동 갱신 기능 (5초)
- 🔧 포트 5001로 변경

### v1.0.0 (2025-12-24)

- 🎉 초기 릴리즈
- 📈 PostgreSQL, Redis, Elasticsearch 모니터링
- ⏰ Cron 기반 스케줄링
- 💬 Mattermost 알림

## 📝 라이선스

MIT License

## 👥 기여

이슈 및 풀 리퀘스트는 언제나 환영합니다!

---

**Made with ❤️ by Gaji Team**
