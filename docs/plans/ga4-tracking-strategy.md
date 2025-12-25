# GA4 추적 전략 - Gaji 플랫폼

## 📊 개요

이 문서는 Gaji 플랫폼의 사용자 행동, 성능, 전환을 추적하기 위한 Google Analytics 4 (GA4) 전략을 정의합니다.

## 🗺️ 페이지 사용 경로 기반 추적 맵

### 1. 신규 사용자 여정

```
랜딩 페이지(/)
  → 로그인(/login) or 회원가입(/register)
  → 책 목록(/books)
  → 책 상세(/books/:id)
  → 시나리오 생성
  → 시나리오 상세(/scenarios/:id)
  → AI 대화 시작(/conversations/:id)
  → 대화 세션 (핵심 전환 포인트)
```

**추적 이벤트:**

- `page_view` (각 단계)
- `sign_up` (회원가입)
- `login` (로그인)
- `view_book_detail` (책 관심도)
- `scenario_created` (첫 시나리오 생성)
- `chat_session_start` (첫 대화 시작)
- `first_chat_completion` (3개 이상 메시지 교환) ⭐ 핵심 전환

### 2. 재방문 사용자 여정

```
랜딩 페이지(/)
  → 자동 로그인
  → 내 대화 목록(/conversations)
  → 기존 대화 이어하기 or 새 시나리오 탐색
  → 검색(/search)
  → 시나리오 탐색(/scenarios)
  → 새 대화 시작
```

**추적 이벤트:**

- `returning_user` (7일 내 재방문)
- `search` (검색 의도)
- `filter_scenarios` (탐색 패턴)
- `conversation_started` (대화 재개/신규)
- `engaged_user` (5분+ 체류, 2페이지+ 방문) ⭐ 참여도 전환

### 3. 파워 유저 여정

```
매일 접속
  → 여러 책 탐색
  → 다양한 시나리오 생성
  → 여러 캐릭터와 동시 대화
  → 대화 포크/공유
  → 소셜 기능 활용 (팔로우, 좋아요)
```

**추적 이벤트:**

- `power_user` (하루 3개+ 시나리오와 대화) ⭐ 고가치 전환
- `conversation_forked` (고급 기능)
- `share` (바이럴)
- `follow` / `like` (커뮤니티 참여)

## 📈 추적 카테고리

### 1. 페이지뷰 추적 (Page Views)

| 페이지        | 경로                 | 추적 목적        | 메타데이터                    |
| ------------- | -------------------- | ---------------- | ----------------------------- |
| 홈            | `/`                  | 랜딩 유입 분석   | title, description            |
| 소개          | `/about`             | 서비스 이해도    | title, description            |
| 책 목록       | `/books`             | 콘텐츠 탐색 시작 | title, description            |
| 책 상세       | `/books/:id`         | 책 관심도        | book_id, title, author, genre |
| 시나리오 목록 | `/scenarios`         | 시나리오 탐색    | title, description            |
| 시나리오 상세 | `/scenarios/:id`     | 시나리오 선택    | scenario_id, book_id          |
| 대화 목록     | `/conversations`     | 사용자 히스토리  | title, description            |
| AI 대화       | `/conversations/:id` | 핵심 기능 사용   | conversation_id, scenario_id  |
| 검색          | `/search`            | 검색 패턴        | query, results                |
| 프로필        | `/profile/:username` | 소셜 기능        | user_id, is_own               |
| 로그인        | `/login`             | 인증 시작        | redirect_from                 |
| 회원가입      | `/register`          | 신규 등록        | -                             |

**구현 상태:** ✅ 완료 (`router/index.ts`)

### 2. 콘텐츠 발견 단계 (Content Discovery)

#### A. 책 탐색 이벤트

| 이벤트명           | 트리거      | 파라미터                      | 의미           |
| ------------------ | ----------- | ----------------------------- | -------------- |
| `search_books`     | 검색창 제출 | query, results_count          | 검색 의도      |
| `filter_books`     | 필터 적용   | filter_type, filter_value     | 선호 장르/작가 |
| `sort_books`       | 정렬 변경   | sort_by                       | 정렬 선호도    |
| `view_book_detail` | 책 클릭     | book_id, title, author, genre | 인기 도서      |

**적용 컴포넌트:** `BookBrowsePage.vue`, `BookCard.vue`

#### B. 시나리오 탐색 이벤트

| 이벤트명           | 트리거        | 파라미터                       | 의미            |
| ------------------ | ------------- | ------------------------------ | --------------- |
| `filter_scenarios` | 필터 적용     | filter_type, filter_value      | 탐색 패턴       |
| `scenario_viewed`  | 시나리오 클릭 | scenario_id, book_id           | 시나리오 인기도 |
| `scenario_created` | 시나리오 생성 | book_id, type, has_fork_parent | 콘텐츠 생성률   |

**적용 컴포넌트:** `ScenarioCard.vue`, `CreateScenarioModal.vue`

### 3. AI 대화 세션 추적 (Chat Session) ⭐ 최우선

#### A. 세션 생명주기

| 이벤트명             | 트리거         | 파라미터                               | 의미        |
| -------------------- | -------------- | -------------------------------------- | ----------- |
| `chat_session_start` | 대화 시작 버튼 | scenario_id, conversation_id, is_fork  | 대화 시작률 |
| `chat_session_end`   | 대화 종료/이탈 | duration, message_count, was_completed | 세션 길이   |

#### B. 대화 품질 지표

| 이벤트명                 | 트리거       | 파라미터                                        | 의미          |
| ------------------------ | ------------ | ----------------------------------------------- | ------------- |
| `chat_message_sent`      | 메시지 전송  | conversation_id, message_length, message_number | 참여도        |
| `chat_response_received` | AI 응답 수신 | response_time_ms, was_error                     | 성능 체감     |
| `chat_retry`             | 재생성 버튼  | retry_count                                     | 응답 불만족도 |
| `chat_save`              | 대화 저장    | message_count                                   | 콘텐츠 가치   |
| `chat_share`             | 대화 공유    | share_method                                    | 바이럴 가능성 |

**적용 컴포넌트:** `ConversationChat.vue`, `ChatInput.vue`, `ChatMessage.vue`

### 4. 이미지 인터랙션 (Image Interaction)

| 이벤트명           | 트리거           | 파라미터                     | 의미          |
| ------------------ | ---------------- | ---------------------------- | ------------- |
| `image_view`       | 이미지 클릭/확대 | image_type, entity_id, url   | 이미지 중요도 |
| `image_load_error` | 로딩 실패        | url, error_type, entity_type | CDN 이슈 감지 |
| `image_load_slow`  | 3초 이상 로딩    | load_time_ms, image_type     | CDN 성능 문제 |

**적용 방법:** `useImageTracking` composable

### 5. 전환 이벤트 (Conversion Events) 🎯

| 전환 이벤트             | 정의                       | 측정 시점    | 목표 전환율 |
| ----------------------- | -------------------------- | ------------ | ----------- |
| `first_chat_completion` | 첫 대화 완료 (3개+ 메시지) | 대화 종료 시 | 60%         |
| `engaged_user`          | 5분+ 체류 + 2페이지+       | 세션 종료 시 | 40%         |
| `power_user`            | 하루 3개+ 시나리오와 대화  | 일일 집계    | 10%         |
| `returning_user`        | 7일 내 재방문              | 페이지 로드  | 30%         |

### 6. 성능 메트릭 (Performance Metrics)

#### A. Core Web Vitals

| 메트릭 | 측정 위치        | 임계값  | 이벤트명     |
| ------ | ---------------- | ------- | ------------ |
| LCP    | 페이지 로드 완료 | < 2.5초 | `web_vitals` |
| INP    | 사용자 입력 시   | < 200ms | `web_vitals` |
| CLS    | 페이지 생명주기  | < 0.1   | `web_vitals` |

**구현 상태:** ✅ 완료 (`utils/webVitals.ts`)

#### B. API 성능

| 이벤트명            | 측정 대상     | 파라미터                      | 분석 목적     |
| ------------------- | ------------- | ----------------------------- | ------------- |
| `api_call_duration` | 모든 API 호출 | endpoint, duration_ms, status | 백엔드 성능   |
| `llm_response_time` | AI 응답 대기  | scenario_id, duration_ms      | LLM 체감 성능 |
| `image_cdn_time`    | S3/CloudFront | cdn_time_ms, image_size       | CDN 효율성    |

**구현 상태:** ✅ 완료 (`services/api.ts`)

### 7. 소셜 기능 (Social Features)

| 이벤트명   | 트리거      | 파라미터                 | 의미          |
| ---------- | ----------- | ------------------------ | ------------- |
| `like`     | 좋아요 클릭 | content_type, content_id | 콘텐츠 선호도 |
| `unlike`   | 좋아요 취소 | content_type, content_id | 선호도 변화   |
| `follow`   | 팔로우      | followed_user_id         | 소셜 그래프   |
| `unfollow` | 언팔로우    | unfollowed_user_id       | 관계 변화     |
| `share`    | 공유        | content_type, method     | 바이럴 채널   |

**적용 컴포넌트:** `LikeButton.vue`, `FollowButton.vue`, `ShareButton.vue`

### 8. 사용자 인증 (Authentication)

| 이벤트명  | 트리거        | 파라미터 | 의미          |
| --------- | ------------- | -------- | ------------- |
| `sign_up` | 회원가입 완료 | method   | 신규 사용자   |
| `login`   | 로그인 성공   | method   | 재방문 사용자 |
| `logout`  | 로그아웃      | -        | 세션 종료     |

**적용 컴포넌트:** `Login.vue`, `Register.vue`, `Logout.vue`

## 👥 사용자 세그먼트 (User Segments)

### 맞춤 측정기준 (Custom Dimensions)

| 속성명                    | 수집 시점      | 값                    | 활용                |
| ------------------------- | -------------- | --------------------- | ------------------- |
| `user_type`               | 세션 시작      | new/returning         | 신규 vs 재방문 분석 |
| `device_type`             | 첫 페이지 로드 | mobile/tablet/desktop | 디바이스별 UX       |
| `engagement_level`        | 행동 기반 계산 | low/medium/high       | 리텐션 전략         |
| `favorite_genre`          | 책 클릭 패턴   | genre_name            | 개인화 추천         |
| `total_scenarios_created` | 누적           | number                | 사용자 가치         |
| `total_conversations`     | 누적           | number                | 참여도              |

**구현 상태:** ✅ 일부 완료 (`main.ts`)

## 📊 대시보드 구성 제안

### 1. 핵심 지표 대시보드 (Executive Dashboard)

- 일일 활성 사용자 (DAU)
- 신규 회원가입 수
- 대화 세션 수
- 평균 세션 지속 시간
- 전환율 (first_chat_completion, engaged_user, power_user)

### 2. 콘텐츠 성과 대시보드

- 인기 책 Top 10 (`view_book_detail`)
- 인기 시나리오 Top 10 (`scenario_viewed`)
- 장르별 선호도 (`filter_books`)
- 검색 키워드 트렌드 (`search_books`)

### 3. AI 대화 품질 대시보드

- 평균 AI 응답 시간 (`llm_response_time`)
- 재생성 비율 (`chat_retry`)
- 대화 완료율 (`first_chat_completion`)
- 평균 메시지 수 (`chat_message_sent`)

### 4. 성능 모니터링 대시보드

- Core Web Vitals 추세 (`web_vitals`)
- API 응답 시간 분포 (`api_call_duration`)
- 이미지 로딩 에러율 (`image_load_error`)
- CDN 성능 (`image_cdn_time`)

### 5. 사용자 여정 분석

- 깔때기 분석 (Funnel)
  1. 랜딩 → 회원가입 → 책 탐색 → 시나리오 생성 → 대화 시작 → 첫 대화 완료
- 경로 탐색 (Path Exploration)
- 세그먼트 비교 (new vs returning, mobile vs desktop)

## 🚀 구현 우선순위

### Phase 1: 핵심 기능 (P0) - 완료

- [x] `useAnalytics` composable 확장
- [x] 페이지뷰 자동 추적
- [x] Web Vitals 추적
- [x] API 성능 추적
- [x] 사용자 속성 초기화

### Phase 2: 주요 기능 (P1) - 다음 단계

- [ ] AI 대화 세션 전체 추적 (`ConversationChat.vue`)
- [ ] 콘텐츠 탐색 추적 (`BookBrowsePage.vue`, `BookDetailPage.vue`)
- [ ] 사용자 인증 추적 (`Login.vue`, `Register.vue`)

### Phase 3: 보조 기능 (P2) - 추후

- [ ] 이미지 추적 적용 (모든 이미지 컴포넌트)
- [ ] 소셜 기능 추적 (`Profile.vue`, `LikeButton.vue`)
- [ ] 전환 이벤트 로직 (`App.vue`)

## 📝 개발자 가이드

상세한 구현 방법은 다음 문서를 참조하세요:

- [GA4 구현 가이드](./ga4-implementation-guide.md)

## 🔍 디버깅

개발 환경에서는 모든 GA4 이벤트가 콘솔에 로그됩니다:

```
[GA4 Event] chat_session_start { scenario_id: '123', ... }
[GA4 PageView] /books/123 "책 상세 - Gaji"
```

프로덕션 환경에서는 GA4 DebugView를 사용하여 실시간 이벤트를 확인할 수 있습니다.

## 📞 문의

GA4 설정 또는 이벤트 추가가 필요한 경우 프론트엔드 팀에 문의하세요.
