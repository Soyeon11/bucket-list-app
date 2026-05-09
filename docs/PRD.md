# Bucket List App — Product Requirements Document (PRD)

**Version:** 1.0  
**Last Updated:** 2026-05-09  
**Status:** Draft

---

## 1. 제품 개요 (Product Overview)

매주 1개씩 실현 가능한 스몰 버킷리스트 아이템을 AI가 추천하고, 사용자가 실천한 과정을 쇼츠/릴스 형식의 세로 영상(9:16)으로 자동 제작·저장하는 모바일 앱.

---

## 2. 기능 요구사항 (Functional Requirements)

### 2.1 인증 & 프로필 (Authentication & Profile)

| ID | User Story | 우선순위 |
|----|-----------|---------|
| AUTH-01 | As a user, I want to sign up with email and password so that I can create a personal account. | Must |
| AUTH-02 | As a user, I want to sign in with Google or Apple so that I can log in quickly without remembering a password. | Should |
| AUTH-03 | As a user, I want to reset my password via email so that I can recover access if I forget it. | Must |
| AUTH-04 | As a user, I want to edit my profile (nickname, profile image) so that the app feels personalized. | Should |
| AUTH-05 | As a user, I want to delete my account and all associated data so that I can exercise my right to be forgotten. | Must |

### 2.2 버킷리스트 관리 (Bucket List CRUD)

| ID | User Story | 우선순위 |
|----|-----------|---------|
| BL-01 | As a user, I want to add a new bucket list item with a title, category, and description so that I can capture my goals. | Must |
| BL-02 | As a user, I want to view all my bucket list items in a categorized list so that I can see my overall goals at a glance. | Must |
| BL-03 | As a user, I want to edit any bucket list item so that I can update details as my goals evolve. | Must |
| BL-04 | As a user, I want to delete a bucket list item so that I can remove goals I no longer care about. | Must |
| BL-05 | As a user, I want to mark an item as completed so that I can track my achievements. | Must |
| BL-06 | As a user, I want to set a priority level (high / medium / low) on each item so that the recommendation system knows what matters most to me. | Should |
| BL-07 | As a user, I want to tag items with one or more categories (travel, food, hobby, fitness, culture, etc.) so that I can filter them easily. | Should |
| BL-08 | As a user, I want to search my bucket list by keyword so that I can quickly find a specific item. | Should |

### 2.3 주간 추천 시스템 (Weekly Recommendation)

| ID | User Story | 우선순위 |
|----|-----------|---------|
| REC-01 | As a user, I want to receive one curated bucket list recommendation every Monday so that I always have a fresh goal for the week. | Must |
| REC-02 | As a user, I want the recommendation to consider the current season and local weather so that the suggestion is realistic right now. | Should |
| REC-03 | As a user, I want to accept or skip the weekly recommendation so that I stay in control of my goals. | Must |
| REC-04 | As a user, I want to see why a particular item was recommended so that I understand the logic. | Could |
| REC-05 | As a user, I want to view past weekly recommendations so that I can track what was suggested previously. | Could |

### 2.4 실천 기록 (Activity Logging)

| ID | User Story | 우선순위 |
|----|-----------|---------|
| LOG-01 | As a user, I want to log progress on an active bucket list item by uploading photos or short video clips so that I can document the experience. | Must |
| LOG-02 | As a user, I want to add a text note to each progress log so that I can describe what happened. | Must |
| LOG-03 | As a user, I want to record the date and location (optional) of each activity so that the timeline is accurate. | Should |
| LOG-04 | As a user, I want to view all logs for a single bucket list item in chronological order so that I can relive the journey. | Must |
| LOG-05 | As a user, I want to delete a log entry so that I can remove mistakes or duplicates. | Must |

### 2.5 쇼츠/릴스 영상 자동 생성 (Shorts / Reels Auto-generation)

| ID | User Story | 우선순위 |
|----|-----------|---------|
| VID-01 | As a user, I want to generate a 9:16 vertical short video from my activity photos and clips with one tap so that I don't need video editing skills. | Must |
| VID-02 | As a user, I want to choose from multiple video templates (cinematic, vlog, minimal, etc.) so that I can match my personal style. | Should |
| VID-03 | As a user, I want to add background music from a preset library so that the video feels polished. | Should |
| VID-04 | As a user, I want the video to include auto-generated title cards and captions based on my notes so that the story is clear. | Should |
| VID-05 | As a user, I want to be notified via push when my video is ready so that I don't have to wait on-screen. | Must |
| VID-06 | As a user, I want to preview the generated video before saving or sharing so that I can approve it. | Must |
| VID-07 | As a user, I want to regenerate the video with a different template if I don't like the first result so that I can iterate freely. | Should |

### 2.6 갤러리 & 공유 (Gallery & Sharing)

| ID | User Story | 우선순위 |
|----|-----------|---------|
| GAL-01 | As a user, I want to browse all generated videos in a gallery view so that I can see everything I've accomplished. | Must |
| GAL-02 | As a user, I want to download a generated video to my device's camera roll so that I can keep it offline. | Must |
| GAL-03 | As a user, I want to share a video directly to Instagram Reels or YouTube Shorts so that I can publish without leaving the app. | Should |
| GAL-04 | As a user, I want to copy a shareable link to a video so that I can send it via any messaging app. | Could |

---

## 3. 비기능 요구사항 (Non-Functional Requirements)

### 3.1 성능 (Performance)

| ID | 요구사항 | 목표 수치 |
|----|---------|---------|
| NFR-P01 | API 응답 시간 | 95th percentile ≤ 500 ms (비디오 생성 제외) |
| NFR-P02 | 비디오 생성 완료 시간 | ≤ 3분 (60초 이하 영상 기준) |
| NFR-P03 | 앱 콜드 스타트 | ≤ 2초 |
| NFR-P04 | 이미지 업로드 | 10 MB 이하 단일 파일, 최대 20장/세션 |
| NFR-P05 | 동영상 업로드 | 200 MB 이하 단일 클립, 최대 5개/세션 |

### 3.2 보안 (Security)

| ID | 요구사항 |
|----|---------|
| NFR-S01 | 모든 API 요청은 Supabase JWT Bearer 토큰으로 인증 |
| NFR-S02 | Supabase RLS를 통해 사용자는 자신의 데이터만 읽기/쓰기 가능 |
| NFR-S03 | Storage 버킷은 private; signed URL(유효기간 1시간)로만 접근 |
| NFR-S04 | 민감 환경변수(.env)는 절대 앱 번들에 포함 금지; Expo SecureStore 사용 |
| NFR-S05 | 비밀번호 최소 8자, 특수문자 1개 이상 포함 |

### 3.3 오프라인 지원 (Offline Support)

| ID | 요구사항 |
|----|---------|
| NFR-O01 | 버킷리스트 목록은 로컬 캐시(TanStack Query 오프라인 persistence)로 오프라인 조회 가능 |
| NFR-O02 | 오프라인 상태에서 작성한 메모/사진은 큐에 저장 후 연결 복구 시 자동 업로드 |
| NFR-O03 | 네트워크 없을 때 명확한 오프라인 배너 표시 |

### 3.4 접근성 (Accessibility)

- WCAG 2.1 AA 준수
- 모든 인터랙티브 요소에 accessibilityLabel 제공
- 다이나믹 폰트 크기 지원

### 3.5 지원 플랫폼

| 플랫폼 | 최소 버전 |
|--------|---------|
| iOS | 16.0+ |
| Android | API 26 (Android 8.0)+ |

---

## 4. 화면 목록 (Screen Inventory)

### 4.1 인증 플로우

#### S01 — 온보딩 (Onboarding)
- 앱 소개 슬라이드 3장 (스와이프)
- "시작하기" CTA 버튼
- 이미 계정이 있으면 건너뛰기 링크

#### S02 — 회원가입 (Sign Up)
- 이메일 입력 필드
- 비밀번호 / 비밀번호 확인 필드
- Google 로그인 버튼, Apple 로그인 버튼
- 이용약관 동의 체크박스
- "회원가입" 제출 버튼

#### S03 — 로그인 (Sign In)
- 이메일 / 비밀번호 필드
- Google / Apple 소셜 로그인
- "비밀번호를 잊으셨나요?" 링크

### 4.2 메인 탭 네비게이션

| 탭 | 아이콘 | 스크린 |
|----|-------|-------|
| 홈 | house | S10 홈 |
| 버킷리스트 | list.bullet | S20 버킷리스트 |
| 기록 | camera | S30 기록 |
| 갤러리 | photo.on.rectangle | S40 갤러리 |
| 프로필 | person | S50 프로필 |

#### S10 — 홈 (Home)
- 이번 주 추천 아이템 카드 (대형, 배경 이미지 포함)
- 추천 이유 텍스트 ("이번 주 날씨와 당신의 우선순위를 고려했어요")
- "수락" / "다음 주로 미루기" 버튼
- 진행 중인 아이템 요약 카드 (최대 3개)
- 이번 달 달성 배지 스트립

#### S20 — 버킷리스트 (Bucket List)
- 카테고리 필터 탭 바 (전체 / 여행 / 음식 / 취미 / …)
- 아이템 카드 목록 (제목, 카테고리 뱃지, 우선순위 인디케이터, 달성 여부)
- 우측 하단 FAB (+) → S21

#### S21 — 아이템 추가/편집 (Add / Edit Item)
- 제목 텍스트 필드
- 카테고리 선택 드롭다운
- 우선순위 세그먼트 컨트롤 (높음 / 보통 / 낮음)
- 설명 멀티라인 필드
- 태그 입력 칩
- "저장" / "취소" 버튼

#### S30 — 기록 추가 (Log Activity)
- 버킷리스트 아이템 선택 헤더
- 미디어 선택 (사진첩 / 카메라)
- 미디어 그리드 프리뷰 (최대 20장)
- 메모 텍스트 에어리어
- 날짜 피커 (기본값: 오늘)
- 위치 토글 (선택)
- "저장" 버튼
- 저장 후 → 영상 생성 프롬프트 모달

#### S31 — 영상 생성 옵션 (Video Generation Options)
- 템플릿 선택 캐러셀 (Cinematic / Vlog / Minimal / Retro)
- BGM 선택 리스트 (5–8개 트랙)
- 자막 켜기/끄기 토글
- "영상 만들기" 버튼 → 진행 중 모달 → 완료 시 S32

#### S32 — 영상 미리보기 (Video Preview)
- 전체화면 세로 비디오 플레이어
- "저장" / "공유" / "다시 만들기" 버튼

#### S40 — 갤러리 (Gallery)
- 2열 그리드 비디오 썸네일
- 필터: 전체 / 연도 / 카테고리
- 썸네일 탭 → S32

#### S50 — 프로필 (Profile)
- 프로필 이미지 + 닉네임
- 달성 통계 (완료 아이템 수, 생성 영상 수)
- 계정 설정, 알림 설정, 앱 정보 섹션

---

## 5. 추천 알고리즘 상세 로직 (Recommendation Algorithm)

### 5.1 개요

매주 월요일 00:00 KST, Celery Beat 스케줄러가 모든 활성 사용자에 대해 추천 작업을 실행한다.  
각 미완료 버킷리스트 아이템에 **추천 점수(recommendation score)** 를 계산하고 최고 점수 아이템 1개를 선정한다.

### 5.2 점수 계산 공식

```
final_score = priority_score
            + recency_bonus
            + season_score
            + weather_score
            - completion_penalty
```

#### priority_score (최대 40점)

```
high   → 40
medium → 25
low    → 10
```

#### recency_bonus (최대 20점)
마지막으로 추천받은 날로부터 경과된 주 수에 비례한다.

```
weeks_since_last_recommended = (today - last_recommended_at) / 7 days
recency_bonus = min(weeks_since_last_recommended * 4, 20)
# 한 번도 추천받지 않은 아이템 → 20점 (최대)
```

#### season_score (최대 20점)
아이템의 카테고리-태그와 현재 계절의 적합도를 미리 정의한 매핑 테이블로 조회.

```python
SEASON_MAP = {
    "spring": {"travel": 18, "outdoor": 20, "food": 12, "fitness": 16, "culture": 14, "hobby": 12},
    "summer": {"travel": 20, "outdoor": 18, "food": 14, "fitness": 14, "culture": 10, "hobby": 12},
    "fall":   {"travel": 16, "outdoor": 14, "food": 18, "fitness": 14, "culture": 18, "hobby": 16},
    "winter": {"travel": 10, "outdoor":  8, "food": 20, "fitness": 12, "culture": 20, "hobby": 18},
}
```

#### weather_score (최대 20점)
사용자 위치의 현재 날씨(OpenWeatherMap API)를 기반으로 산출.

```python
WEATHER_MAP = {
    "clear":    {"outdoor": 20, "travel": 18, "fitness": 18, "food": 10, "culture": 10, "hobby": 10},
    "clouds":   {"outdoor": 12, "travel": 12, "fitness": 12, "food": 14, "culture": 16, "hobby": 16},
    "rain":     {"outdoor":  2, "travel":  4, "fitness":  4, "food": 18, "culture": 20, "hobby": 18},
    "snow":     {"outdoor": 16, "travel": 14, "fitness": 10, "food": 16, "culture": 14, "hobby": 14},
    "extreme":  {"outdoor":  0, "travel":  0, "fitness":  0, "food": 10, "culture": 10, "hobby": 10},
}
```

날씨 API 호출 실패 시 `weather_score = 10` (중립값) 적용.

#### completion_penalty
이미 완료된 아이템 또는 해당 주에 이미 추천된 아이템은 후보에서 제외 (score = -999).

### 5.3 동점 처리 (Tie-breaking)

동점 시 아래 순서로 우선:
1. `created_at` 오래된 아이템 우선 (먼저 만든 목표 존중)
2. 알파벳 순

### 5.4 추천 아이템 없는 경우

미완료 아이템이 0개이면 "새 버킷리스트 아이템을 추가해보세요!" 안내 카드 표시.

### 5.5 날씨 API 연동

- 제공업체: OpenWeatherMap Current Weather API
- 호출 시점: Celery Beat 작업 실행 시 (유저별 저장된 위치 좌표 사용)
- 위치 정보가 없으면 사용자 기기 타임존으로 계절만 적용, weather_score = 10

---

## 6. 용어 정의 (Glossary)

| 용어 | 정의 |
|-----|-----|
| 버킷리스트 아이템 | 사용자가 달성하고 싶은 하나의 목표 항목 |
| 주간 추천 | 매주 월요일 시스템이 선정한 1개의 실천 권장 아이템 |
| 실천 기록 (Log) | 아이템 진행 과정에서 남기는 사진/영상/메모 묶음 |
| 쇼츠 영상 | 실천 기록 미디어를 9:16 세로 포맷으로 자동 편집한 영상 |
| 템플릿 | 쇼츠 영상의 레이아웃·트랜지션·폰트 스타일 조합 |
