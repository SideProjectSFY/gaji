# Gutenberg 데이터 마이그레이션 자동화 구현 계획 (n8n + Spring Batch)

## 1. 개요
이 문서는 Project Gutenberg 데이터(또는 CMS 콘텐츠)를 효율적으로 **Gaji 플랫폼**으로 이관하기 위한 자동화 파이프라인 구축 계획을 기술합니다.
**n8n**을 오케스트레이터로 사용하여 작업 흐름을 제어하고, **Spring Batch**를 실행 엔진으로 사용하여 대용량 데이터의 안정적인 처리를 담당합니다.

## 2. 아키텍처 (Architecture)

```mermaid
graph LR
    User[Admin / Scheduler] -->|Trigger| n8n
    subgraph "Orchestration Layer (n8n)"
        n8n -->|1. Start Job (HTTP Request)| BatchAPI
        n8n -->|2. Poll Status (Loop)| BatchAPI
        n8n -->|3. Notify Result| Slack/Email
    end
    
    subgraph "Execution Layer (Spring Batch)"
        BatchAPI[Batch Controller] -->|Launch| JobLauncher
        JobLauncher -->|Execute| Job[Migration Job]
        Job -->Step1[Reader: Gutenberg Source]
        Step1 -->Step2[Processor: HTML parsing / Vector Embedding]
        Step2 -->Step3[Writer: Gaji DB / Vector DB]
    end
```

## 3. 상세 구현 단계 (Implementation Steps)

### Phase 1: Spring Batch 환경 구성 (`apps:batch-app`)

**목표**: `gajiBE` 내에 배치 애플리케이션 모듈을 활성화하고 기본 설정을 마칩니다.

1.  **의존성 추가 (`build.gradle`)**
    *   `org.springframework.boot:spring-boot-starter-batch`
    *   `org.springframework.boot:spring-boot-starter-web` (API 트리거용)
    *   `h2` (메타데이터 저장용, 운영 시 PostgreSQL 권장)

2.  **Batch Configuration**
    *   `@EnableBatchProcessing` 설정 (Spring Boot 3.x에서는 자동 설정 활용 권장)
    *   `JobRepository` 및 `TransactionManager` 빈 구성

3.  **Entity / Domain 정의**
    *   Migration 대상 테이블 (예: `Book`, `Content`) 엔티티 생성 (있는 경우 재사용)
    *   Source 데이터 모델 정의 (DTO)

### Phase 2: Batch Job 개발 (Migration Logic)

**목표**: 데이터를 읽고(Read), 가공하여(Process), 저장하는(Write) 로직을 구현합니다.

1.  **ItemReader 구현 (`GutenbergItemReader`)**
    *   옵션 A (File): Gutenberg 텍스트 파일(.txt)을 줄 단위 또는 문단 단위로 읽기
    *   옵션 B (API/DB): 외부 소스에서 데이터 조회
    *   *핵심*: 대량 데이터 처리를 위해 `Chunk` 지향 처리 (예: 1000개씩 커밋)

2.  **ItemProcessor 구현 (`ContentProcessor`)**
    *   데이터 정제 (불필요한 공백, 특수문자 제거)
    *   메타데이터 추출 (제목, 저자 등)
    *   (선택) 텍스트 청킹(Chunking) 및 임베딩 준비

3.  **ItemWriter 구현 (`GajiContentWriter`)**
    *   `JpaItemWriter` 또는 `JdbcBatchItemWriter`를 사용하여 DB에 저장
    *   Insert 성능 최적화 (Bulk Insert)

4.  **Job & Step 구성**
    *   Job 이름: `importGutenbergJob`
    *   Step 구성: `reader` -> `processor` -> `writer` 연결
    *   Fault Tolerance: `skipLimit`, `retryLimit` 설정으로 일부 오류 발생 시 전체 중단 방지

### Phase 3: 외부 실행 인터페이스 (Controller)

**목표**: n8n에서 배치를 실행하고 상태를 조회할 수 있는 API를 제공합니다.

1.  **JobLauncher API (`BatchJobController`)**
    *   `POST /api/batch/run/{jobName}`: Job 실행 (`JobParameters`로 날짜/ID 전달)
    *   `GET /api/batch/status/{executionId}`: 실행 상태 조회 (COMPLETED, FAILED, RUNNING)

### Phase 4: n8n 워크플로우 구축

**목표**: n8n을 통해 배치를 주기적으로 실행하거나 수동으로 트리거하고, 결과를 통지합니다.

1.  **Webhook / Schedule Node**
    *   매일 새벽 2시 또는 관리자 요청 시 시작
2.  **HTTP Request (Start Job)**
    *   Spring Boot API 호출 (`POST /api/batch/run/importGutenbergJob`)
    *   Response로 `executionId` 획득
3.  **Loop & Wait (Status Check)**
    *   `executionId`를 사용하여 10초마다 상태 확인 (`GET /api/batch/status`)
    *   상태가 `COMPLETED` 또는 `FAILED`가 될 때까지 반복
4.  **Result Notification**
    *   Slack / Email 노드를 사용하여 결과(처리 건수, 오류 메시지) 전송

## 4. 데이터베이스 고려사항
*   **Batch Meta Tables**: Spring Batch가 실행 이력을 관리하기 위한 테이블 (`BATCH_JOB_INSTANCE`, `BATCH_JOB_EXECUTION` 등)이 필요합니다. 앱 기동 시 자동 생성(`spring.batch.jdbc.initialize-schema=always`)되거나 SQL로 수동 생성해야 합니다.
*   **Transaction**: Reader-Processor-Writer는 하나의 트랜잭션 덩어리(Chunk)로 묶입니다. 중간 실패 시 해당 Chunk만 롤백됩니다.

## 5. 예상 일정 (Timeline)
*   **Week 1**: Spring Batch 기본 설정 및 Reader/Writer 프로토타입 개발
*   **Week 2**: n8n 워크플로우 연동 및 예외 처리 로직 구현
*   **Week 3**: 대용량 데이터 테스트 및 성능 튜닝

## 6. 실행 계획 (Action Items)
1.  [ ] `apps:batch-app` 모듈의 `build.gradle`에 의존성 추가
2.  [ ] Spring Batch 설정 클래스 (`BatchConfig`) 생성
3.  [ ] Gutenberg 데이터 소스 분석 및 `ItemReader` 구현
