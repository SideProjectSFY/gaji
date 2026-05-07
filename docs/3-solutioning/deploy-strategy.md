AWS Free Tier 배포 전략 가이드 (설정 중심)

1. 배포 아키텍처 전략
   1.1 서비스 배치 전략
   권장: 단일 EC2 인스턴스 + Docker Compose 방식
   아키텍처 구성:
   [클라이언트]
   ↓ HTTPS
   [EC2 t3.micro - Public Subnet]
   ├─ nginx:80/443 (리버스 프록시)
   │ ├─ / → Vue.js 정적 파일
   │ └─ /api/\* → Spring Boot
   │
   ├─ Spring Boot:8080 (내부 포트)
   │ ├─ MyBatis → RDS PostgreSQL
   │ └─ WebClient → FastAPI:8000
   │
   └─ FastAPI:8000 (내부 전용)
   ├─ ChromaDB (로컬 파일)
   └─ Gemini API (외부)
   왜 이 방식인가?

EC2 Free Tier: 750시간/월 (단일 인스턴스 상시 운영 가능)
ECS Fargate: Free Tier 없음, 최소 월 $15 이상
Lambda: Spring Boot cold start 5초 이상, 비실용적
Elastic Beanstalk: 내부적으로 ELB 생성 시 월 $16 추가 비용

1.2 인스턴스 스펙 및 리소스 할당
EC2 t3.micro 사양:

vCPU: 2코어
메모리: 1GB RAM
스토리지: 30GB EBS gp3 Free Tier

컨테이너별 메모리 할당:
서비스메모리 제한용도nginx50MB리버스 프록시, 정적 파일 서빙Spring Boot400MBAPI Gateway, Heap 384MBFastAPI300MBAI 추론, 벡터 검색시스템 예약250MBOS, 로깅, 모니터링총합1000MBt3.micro 한도 내
Java 힙 메모리 최적화:

-Xms256m: 초기 힙 256MB
-Xmx384m: 최대 힙 384MB
-XX:+UseG1GC: G1 가비지 컬렉터 (메모리 효율)
-XX:MaxGCPauseMillis=200: GC 일시정지 200ms 이하

1.3 VPC 및 네트워크 구성
핵심 전략: NAT Gateway 비용 회피
NAT Gateway 비용:

시간당 $0.045 = 월 $32.40
데이터 전송 GB당 $0.045
→ Free Tier에서 가장 큰 비용 요인

회피 방법:

모든 서비스를 Public Subnet에 배치
보안그룹으로 접근 제어
Private Subnet + NAT Gateway 사용 금지

VPC 구성:

CIDR: 10.0.0.0/16
Public Subnet 1: 10.0.1.0/24 (ap-northeast-2a)
Public Subnet 2: 10.0.2.0/24 (ap-northeast-2c)
Internet Gateway 연결 필수

보안그룹 규칙:
EC2 보안그룹 (Inbound):
프로토콜포트소스용도TCP800.0.0.0/0HTTPTCP4430.0.0.0/0HTTPSTCP22YOUR_IP/32SSH (본인 IP만)
RDS 보안그룹 (Inbound):
프로토콜포트소스용도TCP5432EC2-SGPostgreSQL (EC2에서만)
1.4 RDS PostgreSQL 설정
인스턴스 설정:

인스턴스 클래스: db.t3.micro (750시간/월 Free Tier)
엔진: PostgreSQL 15.4
스토리지: 20GB gp2 (gp3는 유료!)
Multi-AZ: 비활성화 (활성화 시 요금 2배)
Public 액세스: 비활성화 (공인 IP 비용 발생)
백업 보존: 7일 (Free Tier 범위 내)

파라미터 그룹 설정:
파라미터권장 값설명max_connections100동시 연결 수shared_buffers256MB캐시 크기 (25% RAM)effective_cache_size768MB쿼리 플래너 힌트work_mem4MB정렬/해시 작업 메모리maintenance_work_mem64MB유지보수 작업 메모리
연결 풀 설정 (Spring Boot HikariCP):

minimum-idle: 2
maximum-pool-size: 10
idle-timeout: 300000 (5분)
connection-timeout: 30000 (30초)

2. Flyway 마이그레이션 전략
   2.1 의존성 주의사항
   Flyway 10.x부터 PostgreSQL 지원 분리:

flyway-core: 기본 Flyway 기능
flyway-database-postgresql: PostgreSQL 전용 드라이버 (필수 추가!)

2.2 Spring Boot 설정 값
application.yml 설정:
속성값설명spring.flyway.enabledtrueFlyway 활성화spring.flyway.locationsclasspath:db/migration마이그레이션 파일 위치spring.flyway.baseline-on-migratetrue기존 DB에 Flyway 도입 시 필수spring.flyway.baseline-version'0'베이스라인 버전spring.flyway.validate-on-migratetrue마이그레이션 전 검증spring.flyway.default-schemapublic기본 스키마spring.flyway.tableflyway_schema_history메타데이터 테이블명spring.flyway.out-of-orderfalse순서 무시 비활성화
2.3 마이그레이션 파일 규칙
파일명 규칙:

형식: V{버전}**{설명}.sql
예시: V001**create_initial_schema.sql
버전은 숫자만 사용 (언더스코어 2개 주의!)

권장 마이그레이션 구조:
src/main/resources/db/migration/
├── V001**create_initial_schema.sql # 테이블 생성
├── V002**add_indexes.sql # 인덱스 추가
├── V003**add_s3_metadata_table.sql # 이미지 메타데이터
└── V004**update_character_fields.sql # 컬럼 추가/수정
스키마 설계 원칙:
books 테이블:

id: BIGSERIAL (자동 증가)
title: VARCHAR(500)
author: VARCHAR(255)
isbn: VARCHAR(20) UNIQUE
cover_image_url: VARCHAR(2048) → S3 URL 저장
created_at/updated_at: TIMESTAMP WITH TIME ZONE

characters 테이블:

id: BIGSERIAL
book_id: BIGINT REFERENCES books(id)
name: VARCHAR(255)
role: VARCHAR(50) CHECK (PROTAGONIST, ANTAGONIST, SUPPORTING, MINOR)
character_image_url: VARCHAR(2048) → S3 URL 저장

images 테이블 (메타데이터):

id: BIGSERIAL
entity_type: VARCHAR(50) (BOOK, CHARACTER, RELATIONSHIP_DIAGRAM)
entity_id: BIGINT (외래키는 아님, 다형성)
s3_key: VARCHAR(500) UNIQUE
original_filename, content_type, file_size, width, height
storage_type: VARCHAR(20) DEFAULT 'S3'

2.4 배포 시 Flyway 실행 전략
방법 1: Spring Boot 애플리케이션 시작 시 자동 실행

장점: 코드와 스키마가 항상 동기화
단점: 애플리케이션 재시작 시 마이그레이션 재검증 오버헤드

방법 2: CI/CD 파이프라인에서 사전 실행 (권장)

장점: 배포 전 스키마 문제 조기 발견
단점: 파이프라인 구성 복잡도 증가

GitHub Actions 워크플로우 단계:

코드 체크아웃
Flyway 마이그레이션 실행 (Docker 컨테이너)
마이그레이션 성공 확인
애플리케이션 빌드
EC2에 배포

마이그레이션 실패 시 롤백:

PostgreSQL은 DDL 트랜잭션 지원 → 자동 롤백
flyway repair 명령으로 메타데이터 복구
flyway migrate 재실행

3. Backend ↔ AI Service 통신 모니터링
   3.1 통신 계층 구조
   요청 흐름:
   Client → nginx → Spring Boot → FastAPI → Gemini API
   ↓
   PostgreSQL
   모니터링 포인트:

Spring Boot → FastAPI: 프록시 응답 시간, 에러율
FastAPI → Gemini API: LLM 호출 지연, 토큰 소비량
Spring Boot → PostgreSQL: 쿼리 성능, 커넥션 풀 상태

3.2 Spring Boot WebClient 설정
타임아웃 설정 계층:
계층타임아웃목적WebClient Connect5초TCP 연결 수립WebClient Read60초FastAPI 응답 대기 (LLM 고려)WebClient Write10초요청 전송Resilience4j TimeLimiter55초서킷 브레이커 타임아웃nginx proxy_read_timeout70초클라이언트 응답 대기
왜 이렇게 설정하는가?

LLM 응답은 5~30초 소요
내부 타임아웃 < 외부 타임아웃 계층화
60초는 사용자 경험의 한계치

3.3 Resilience4j 서킷 브레이커 설정
서킷 브레이커 상태 전환:
CLOSED (정상)
→ 실패율 50% 초과 or 느린 호출 80% 초과
→ OPEN (차단, 30초 대기)
→ HALF_OPEN (3회 테스트)
→ 성공 시 CLOSED / 실패 시 OPEN
설정 값:
파라미터값설명slidingWindowSize10최근 10개 요청 기준minimumNumberOfCalls5최소 5개 요청 후 판단failureRateThreshold50%실패율 50% 초과 시 OPENslowCallRateThreshold80%느린 호출 80% 초과 시 OPENslowCallDurationThreshold10초10초 이상은 느린 호출waitDurationInOpenState30초OPEN 상태 유지 시간permittedNumberOfCallsInHalfOpenState3HALF_OPEN 시 테스트 호출 수
Retry 설정:

최대 재시도: 3회
재시도 간격: 1초 (지수 백오프 x2)
재시도 대상: IOException, TimeoutException

Fallback 전략:

FastAPI 장애 시 → "AI 서비스 일시 중단" 메시지 반환
사용자에게 에러 대신 대체 응답 제공

3.4 Health Check 엔드포인트 설계
Spring Boot Actuator 엔드포인트:

/actuator/health: 전체 상태 (Liveness + Readiness)
/actuator/health/liveness: 컨테이너 생존 확인
/actuator/health/readiness: 의존성 확인 (DB, FastAPI)

Custom Health Indicator:

FastAPIHealthIndicator: FastAPI /health 엔드포인트 호출
타임아웃: 5초
실패 시: DOWN 상태, 에러 메시지 포함

FastAPI Health Check:

/health/live: 컨테이너 생존 (항상 200 OK)
/health/ready: ChromaDB + Gemini API 연결 확인

ChromaDB 연결 실패 → 503 Service Unavailable
Gemini API 키 검증 실패 → 503

3.5 메트릭 수집 전략
Spring Boot Micrometer 메트릭:

http.client.requests: WebClient 호출 통계

태그: uri, method, status, exception
백분위수: p50, p95, p99
SLO: 100ms, 500ms, 1s, 5s, 30s

FastAPI Prometheus 메트릭:

http_requests_total: 전체 요청 수
http_request_duration_seconds: 요청 처리 시간
llm_request_duration_seconds: LLM API 호출 시간 (커스텀)
llm_request_total: LLM 호출 횟수 (커스텀)

주요 모니터링 지표:
지표임계값의미p95 응답 시간> 5초95%의 요청이 5초 이내에러율> 5%100개 중 5개 실패서킷 브레이커 OPEN발생 시 알림FastAPI 장애커넥션 풀 사용률> 80%DB 연결 부족 위험

4. 로깅 전략
   4.1 로그 레벨 및 포맷
   운영 환경 로그 레벨:
   컴포넌트로그 레벨이유com.yourcompanyINFO비즈니스 로직 추적org.springframeworkWARN프레임워크 경고만org.hibernate.SQLWARN쿼리 로그 비활성화 (성능)io.nettyERROR네트워크 에러만FastAPIINFOAPI 호출 추적
   JSON 로그 포맷 (권장):

CloudWatch Logs Insights 파싱 용이
구조화된 검색 가능
표준 필드: timestamp, level, message, service, traceId

로그에 포함할 필드:

timestamp: ISO 8601 형식
level: INFO, WARN, ERROR
service: api-gateway, fastapi
traceId: 분산 추적 ID
requestId: 요청 고유 ID
userId: 사용자 ID (있을 경우)
duration_ms: 처리 시간 (밀리초)
http.method, http.path, http.status

4.2 MDC (Mapped Diagnostic Context) 전략
MDC 사용 목적:

요청 전체 생명주기에 걸쳐 traceId 전파
다중 스레드 환경에서도 컨텍스트 유지

MDC 필터 동작:

요청 수신 시 X-Trace-Id 헤더 확인
없으면 UUID 생성
MDC에 traceId, requestId 저장
응답 헤더에 X-Trace-Id 추가
필터 종료 시 MDC.clear()

FastAPI로 traceId 전파:

Spring Boot → FastAPI 호출 시 X-Trace-Id 헤더 전달
FastAPI 미들웨어에서 structlog contextvars에 저장

4.3 PostgreSQL 로깅 설정
RDS 파라미터 그룹:
파라미터권장 값목적log_statementddlDDL(CREATE, ALTER, DROP)만 로깅log_min_duration_statement10001초 이상 쿼리만 로깅log_connections1연결 로그 활성화log_disconnections1연결 해제 로그 활성화log_lock_waits1락 대기 로깅log_temp_files0임시 파일 생성 로깅
느린 쿼리 분석:

CloudWatch Logs에서 duration > 1000ms 필터링
쿼리 패턴 분석 후 인덱스 추가
EXPLAIN ANALYZE로 실행 계획 확인

4.4 Docker 로깅 드라이버
CloudWatch Logs 직접 전송:

드라이버: awslogs
로그 그룹: /app/{service-name}
스트림: docker/{container-id}
멀티라인 패턴: JSON 로그 첫 줄 ^\{ 인식

로그 보존 기간:

개발 환경: 7일
스테이징: 14일
운영 환경: 30일 (Free Tier: 5GB/월까지 무료)

4.5 CloudWatch Logs Insights 쿼리 예시
자주 사용하는 쿼리:

1. 에러 로그 조회 (최근 1시간)

필터: level = "ERROR"
정렬: 최신순
출력: timestamp, service, message, traceId, error.type

2. 특정 traceId 요청 추적

필터: traceId = "abc123-def456"
정렬: timestamp 오름차순
전체 서비스 로그 통합 조회

3. 느린 요청 분석 (500ms 이상)

필터: http.duration_ms > 500
통계: avg, max, count by http.path
정렬: avg_duration 내림차순

4. API 엔드포인트별 에러율

그룹화: http.path
계산: 에러 수 / 전체 요청 수
임계값: 5% 이상 알림

5. Frontend 로깅 전략
   5.1 글로벌 에러 핸들링
   Vue.js 에러 핸들러 등록:

app.config.errorHandler: 컴포넌트 에러 포착
window.addEventListener('unhandledrejection'): Promise rejection 처리

에러 정보 수집:

에러 메시지 및 스택 트레이스
발생 컴포넌트 이름
사용자 행동 정보 (라우트, 액션)
브라우저 정보 (userAgent, viewport)

5.2 API 호출 로깅
Axios 인터셉터 활용:

요청 시작 시간 기록 (performance.now())
응답 시 소요 시간 계산
에러 발생 시 상세 정보 로깅

로깅할 정보:

URL, HTTP Method
응답 상태 코드
소요 시간 (ms)
에러 메시지 (실패 시)

에러 상태별 처리:

401: 인증 실패 → 로그아웃 처리
500/502/503: 서버 에러 → 에러 로깅 + 사용자 알림
타임아웃: 네트워크 문제 → 재시도 권장

5.3 성능 메트릭 수집
Core Web Vitals 측정:
메트릭좋음나쁨의미LCP (최대 콘텐츠 렌더링)< 2.5초> 4초주요 콘텐츠 로딩 시간INP (다음 페인트까지 상호작용)< 200ms> 500ms사용자 입력 반응성CLS (누적 레이아웃 이동)< 0.1> 0.25레이아웃 안정성FCP (첫 콘텐츠 렌더링)< 1.8초> 3초첫 콘텐츠 표시TTFB (첫 바이트까지 시간)< 800ms> 1.8초서버 응답 시간
메트릭 전송 시점:

페이지 언로드 시 (visibilitychange 이벤트)
navigator.sendBeacon() 사용 (비동기, 보장된 전송)

5.4 로깅 솔루션 비교
솔루션Free Tier장점단점CloudWatch RUM1M 이벤트/월AWS 네이티브, X-Ray 통합설정 복잡도 중간Sentry5K 에러/월, 10K 트랜잭션상세 에러 추적, 세션 리플레이외부 의존성LogRocket1K 세션/월세션 녹화, DevTools 재생무료 티어 제한적자체 구현CloudWatch Logs 무료 티어 내완전한 제어, 커스터마이징초기 개발 비용
권장: Sentry (초기) + CloudWatch Logs (장기)

Sentry: 개발 초기 버그 추적
CloudWatch: 운영 안정화 후 비용 절감

5.5 프론트엔드 성능 개선 포인트
로깅 데이터로 발견 가능한 문제:

느린 API 호출: 특정 엔드포인트 p95 > 3초

해결: 백엔드 쿼리 최적화, 캐싱 추가

높은 LCP: 이미지 로딩 지연

해결: CloudFront CDN, WebP 변환, 레이지 로딩

높은 CLS: 동적 콘텐츠 삽입 시 레이아웃 이동

해결: 스켈레톤 UI, 고정 높이 지정

JavaScript 에러: 특정 브라우저에서 반복 발생

해결: 폴리필 추가, 브라우저 호환성 테스트

6. S3 이미지 관리 전략
   6.1 S3 버킷 설계
   버킷 구조:
   my-image-bucket/
   ├── books/
   │ ├── cover/
   │ │ └── {book*id}*{timestamp}.jpg
   │ └── relationship-diagram/
   │ └── {book*id}*{timestamp}.png
   └── characters/
   └── portrait/
   └── {character*id}*{timestamp}.jpg
   파일명 규칙:

형식: {entity*type}/{category}/{id}*{timestamp}.{ext}
예시: characters/portrait/12345_1703001234567.jpg
타임스탬프: 캐시 무효화 (버전 관리)

6.2 CloudFront CDN 연동
CloudFront 배포 설정:
속성설정 값목적OriginS3 버킷 (Regional Domain)OAC 사용Price ClassPriceClass_200아시아+유럽+북미Default TTL86400초 (24시간)캐싱 효율성Max TTL31536000초 (1년)장기 캐싱Compress ObjectsYesGzip 압축 (대역폭 절약)Viewer ProtocolRedirect HTTP to HTTPS보안
OAC (Origin Access Control) 설정:

S3 버킷 퍼블릭 액세스 차단
CloudFront만 S3 접근 허용
IAM 정책으로 권한 제어

Free Tier 한도:

데이터 전송: 1TB/월
요청: 10M HTTP/HTTPS 요청/월

6.3 데이터베이스 스키마 설계
images 테이블:

id: 고유 식별자
entity_type: BOOK, CHARACTER, RELATIONSHIP_DIAGRAM
entity_id: 연결된 엔티티 ID
s3_key: S3 객체 키 (버킷 제외) → books/cover/123_1703001234567.jpg
original_filename: 원본 파일명
content_type: image/jpeg, image/png
file_size: 바이트 단위
width, height: 이미지 해상도
storage_type: S3 (향후 다른 스토리지 지원 대비)

URL 생성 전략:

DB에는 S3 키만 저장
조회 시 CloudFront Domain + S3 Key 조합
예시: https://d1234567890abc.cloudfront.net/books/cover/123.jpg

장점:

CloudFront 도메인 변경 시 DB 수정 불필요
스토리지 마이그레이션 용이

6.4 이미지 업로드 워크플로우
Pre-signed URL 방식 (권장):
단계:

클라이언트 → 백엔드: 업로드 요청 (POST /api/images/upload-url)
백엔드 → 클라이언트: Pre-signed URL 반환 (10분 유효)
클라이언트 → S3: 직접 업로드 (PUT)
클라이언트 → 백엔드: 업로드 완료 알림 + 메타데이터 저장

장점:

백엔드 서버 트래픽 절약
업로드 속도 향상 (S3 직접 연결)
보안 (시간 제한, 서명 필요)

Pre-signed URL 생성 설정:

만료 시간: 10분
HTTP Method: PUT
Content-Type 지정 필수

6.5 S3 수명 주기 정책
정책 목적:

자주 접근하지 않는 이미지 비용 절감
불완전한 멀티파트 업로드 정리

수명 주기 규칙:
규칙 1: 이미지 파일 전환

Prefix: images/
30일 후 → Standard-IA (Infrequent Access, 50% 절감)
90일 후 → Glacier (80% 절감)

규칙 2: 미완료 멀티파트 업로드 정리

7일 후 자동 삭제
스토리지 비용 방지

비용 예측:

Standard: $0.023/GB-month
Standard-IA: $0.0125/GB-month
Glacier: $0.004/GB-month

6.6 이미지 최적화 전략
업로드 전 최적화 (클라이언트):

최대 해상도: 1920x1080 (Full HD)
JPEG 품질: 80-85%
WebP 변환 (브라우저 지원 시)
메타데이터 제거 (EXIF)

Lambda@Edge를 통한 동적 리사이징 (선택사항):

URL 파라미터로 크기 지정: ?w=300&h=300
CloudFront 캐싱으로 변환 비용 최소화
주의: Lambda@Edge는 Free Tier 없음

대안: 사전 리사이징

업로드 시 여러 크기 생성 (썸네일, 중간, 원본)
S3에 별도 저장: /thumbnails/, /medium/, /original/

7. 모니터링 및 알림 전략
   7.1 CloudWatch 대시보드 구성
   대시보드 레이아웃:
   섹션 1: 인프라 지표

EC2 CPU 사용률 (평균, 최대)
EC2 메모리 사용률 (CloudWatch Agent 필요)
RDS CPU 사용률
RDS 데이터베이스 연결 수

섹션 2: 애플리케이션 지표

Spring Boot 요청 처리 시간 (p50, p95, p99)
FastAPI 요청 처리 시간
서킷 브레이커 상태 (OPEN/CLOSED)
에러율 (4xx, 5xx)

섹션 3: 비즈니스 지표

분당 AI 대화 요청 수
Gemini API 호출 수 및 토큰 소비량
사용자 활성도 (DAU, MAU)

7.2 CloudWatch 알람 설정
필수 알람 목록:
알람 이름지표임계값평가 기간액션High-CPU-EC2EC2 CPU80%5분간 2회SNS 알림High-Memory-EC2EC2 메모리85%5분간 2회SNS 알림RDS-High-CPURDS CPU75%5분간 2회SNS 알림RDS-High-ConnectionsRDS 연결 수805분간 1회SNS 알림API-High-Latencyp95 응답시간5초5분간 2회SNS 알림API-High-Error-Rate5xx 에러율5%5분간 2회SNS 알림Circuit-Breaker-Open서킷 브레이커OPEN 상태즉시SNS 알림Disk-Space-LowEC2 디스크90%1회SNS 알림
알람 액션:

SNS 토픽으로 이메일/SMS 전송
Free Tier: 1,000개 SNS 알림/월

7.3 AWS X-Ray 분산 추적
X-Ray 활성화 (선택사항):

Spring Boot: AWS X-Ray SDK 추가
FastAPI: AWS X-Ray SDK for Python
nginx: X-Ray 데몬 사이드카 컨테이너

추적 가능한 정보:

서비스 간 호출 경로 (Service Map)
각 구간별 소요 시간
에러 발생 지점 정확히 파악

Free Tier 한도:

100,000개 추적/월
초과 시 $5/100만 추적

사용 여부 판단:

초기 개발: 불필요 (로그만으로 충분)
복잡도 증가 후: 고려

7.4 비용 모니터링 및 알림
AWS Budgets 설정:
예산 1: Zero Spend Budget

예산 금액: $0.01
알림 임계값: $0.01 초과 시 즉시
목적: Free Tier 이탈 조기 감지

예산 2: Monthly Budget

예산 금액: $5.00
알림 임계값:

50% 사용 시
80% 사용 시
100% 사용 시

Cost Explorer 주요 확인 지표:

일별 비용 추세
서비스별 비용 분포
예상 월말 비용

Free Tier 사용량 추적:

AWS Free Tier 사용량 페이지 주간 확인
주요 지표:

EC2 인스턴스 시간 (750시간/월 한도)
RDS 인스턴스 시간 (750시간/월 한도)
S3 스토리지 (5GB 한도)
CloudFront 전송량 (1TB 한도)

7.5 로그 집계 및 분석
CloudWatch Logs 스트림 전략:

서비스별 로그 그룹 분리
구조: /app/{environment}/{service}
예시: /app/prod/api-gateway, /app/prod/fastapi

Logs Insights 저장된 쿼리:

에러 대시보드: 시간별 에러 수, 상위 에러 타입
성능 대시보드: p50/p95/p99 응답 시간 추이
사용자 행동: API 엔드포인트 호출 빈도
서킷 브레이커 이벤트: OPEN/CLOSED 전환 이력

8. 배포 자동화 (CI/CD)
   8.1 GitHub Actions 워크플로우 구조
   트리거:

main 브랜치에 push
Pull Request 생성 시 테스트만 실행

작업 단계:

테스트: 단위 테스트, 통합 테스트 실행
Flyway 마이그레이션: RDS에 스키마 변경 적용
빌드: Gradle/Maven 빌드, Docker 이미지 생성
배포: EC2에 SSH 접속, Docker Compose 재시작
헬스 체크: 배포 후 /health 엔드포인트 확인

8.2 배포 롤백 전략
Blue-Green 배포 (단일 EC2에서 간소화):

새 컨테이너를 다른 포트로 시작 (예: 8081)
헬스 체크 통과 확인
nginx upstream을 새 포트로 변경
구 컨테이너 종료

롤백 트리거:

헬스 체크 실패 3회 연속
5분 내 5xx 에러율 10% 초과

8.3 배포 체크리스트
배포 전:

Flyway 마이그레이션 로컬 테스트
환경 변수 .env 파일 업데이트
Docker 이미지 빌드 성공 확인
RDS 백업 수동 스냅샷 생성

배포 중:

CloudWatch Logs 실시간 모니터링
/health 엔드포인트 응답 확인
서킷 브레이커 상태 정상 확인

배포 후:

주요 API 엔드포인트 수동 테스트
CloudWatch 대시보드 지표 확인
에러 로그 확인 (5분간)
사용자 피드백 모니터링 (24시간)

9. 보안 고려사항
   9.1 EC2 보안 강화
   SSH 접근 제한:

키 페어 방식만 허용 (비밀번호 비활성화)
본인 IP만 22번 포트 허용 (YOUR_IP/32)
fail2ban 설치 (무차별 대입 공격 방어)

Docker 컨테이너 보안:

최소 권한 원칙 (non-root 사용자 실행)
이미지 취약점 스캔 (Trivy)
베이스 이미지 정기 업데이트

9.2 데이터베이스 보안
RDS 보안 설정:

퍼블릭 액세스 비활성화
보안그룹으로 EC2만 허용
SSL/TLS 암호화 연결 강제
강력한 마스터 암호 (16자 이상, 특수문자 포함)

애플리케이션 보안:

PreparedStatement 사용 (SQL Injection 방어)
비밀번호 해싱 (BCrypt, Argon2)
API Rate Limiting (Spring Boot Bucket4j)

9.3 시크릿 관리
환경 변수 저장 방식:

AWS Systems Manager Parameter Store (권장)
또는 .env 파일 (절대 Git 커밋 금지)

관리할 시크릿:

DB 접속 정보 (호스트, 사용자, 비밀번호)
Gemini API 키
JWT 서명 키
S3 액세스 키

10. Free Tier 한도 요약
    서비스Free Tier 한도초과 시 비용주의사항EC2 t3.micro750시간/월$0.0104/시간1개 인스턴스 상시 운영 가능RDS db.t3.micro750시간/월$0.017/시간gp2 스토리지만 무료EBS gp330GB$0.08/GB-월gp2는 20GB만 무료S3 스토리지5GB$0.023/GB-월Standard 클래스S3 요청20K GET, 2K PUTPUT $0.005/1000건-CloudFront1TB 전송, 10M 요청$0.085/GB아시아 가격 기준RDS 백업20GB$0.095/GB-월DB 크기만큼 무료CloudWatch Logs5GB 수집, 5GB 저장$0.50/GBJSON 로그 권장CloudWatch 메트릭10개 커스텀 메트릭$0.30/메트릭기본 메트릭은 무료Lambda1M 요청, 400K GB-초$0.20/100만 요청사용 안 함NAT GatewayFree Tier 없음$32.40/월절대 사용 금지

결론
이 가이드는 AWS Free Tier 한도 내에서 Vue.js, Spring Boot, FastAPI로 구성된 다중 서비스를 운영하기 위한 실전 전략입니다. 단일 EC2에서 Docker Compose를 활용하면 12개월간 완전 무료 운영이 가능하며, NAT Gateway 회피와 gp2 스토리지 사용이 핵심입니다.
Backend와 AI Service 간 통신은 Resilience4j 서킷 브레이커로 안정성을 확보하고, 구조화된 JSON 로깅으로 CloudWatch에서 분산 추적이 가능합니다. S3 + CloudFront 조합으로 이미지를 효율적으로 관리하며, Zero Spend Budget 설정으로 예상치 못한 비용을 사전에 차단할 수 있습니다.
가장 중요한 것은 지속적인 모니터링과 Free Tier 사용량 추적입니다. 이 가이드의 전략을 따르면 안정적이고 비용 효율적인 프로덕션 환경을 구축할 수 있습니다.
