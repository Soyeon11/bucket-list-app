# Bucket List App — API Specification

**Version:** 1.0  
**Last Updated:** 2026-05-09  
**Base URL:** `https://api.bucketlist.app/v1`  
**Auth:** Supabase JWT (Bearer token in `Authorization` header)

---

## 1. 인증 방식 (Authentication)

모든 보호된 엔드포인트는 아래 헤더를 요구한다.

```
Authorization: Bearer <supabase_access_token>
```

토큰은 Supabase Auth SDK `session.access_token` 값을 사용한다.  
토큰 만료(기본 1시간) 시 `401 Unauthorized`가 반환되며, 클라이언트는 `session.refresh_token`으로 갱신해야 한다.

---

## 2. 통일 에러 응답 형식 (Unified Error Response)

```json
{
  "error": {
    "code": "ITEM_NOT_FOUND",
    "message": "Bucket list item not found.",
    "details": null
  }
}
```

### 2.1 HTTP 상태 코드 매핑

| HTTP Status | 의미 |
|------------|-----|
| 400 | 잘못된 요청 (유효성 오류) |
| 401 | 인증 실패 (토큰 없음/만료) |
| 403 | 권한 없음 (타인 리소스 접근) |
| 404 | 리소스 없음 |
| 409 | 충돌 (중복 데이터) |
| 422 | 처리 불가 엔티티 (비즈니스 규칙 위반) |
| 429 | 요청 한도 초과 |
| 500 | 서버 내부 오류 |

### 2.2 에러 코드 정의

| 에러 코드 | 설명 |
|---------|-----|
| `VALIDATION_ERROR` | 요청 바디/파라미터 유효성 실패 |
| `UNAUTHORIZED` | 인증 토큰 없음 또는 유효하지 않음 |
| `FORBIDDEN` | 해당 리소스에 대한 접근 권한 없음 |
| `ITEM_NOT_FOUND` | 버킷리스트 아이템 없음 |
| `LOG_NOT_FOUND` | 실천 기록 없음 |
| `VIDEO_NOT_FOUND` | 생성된 영상 없음 |
| `RECOMMENDATION_NOT_FOUND` | 해당 주 추천 없음 |
| `USER_NOT_FOUND` | 사용자 없음 |
| `DUPLICATE_ENTRY` | 이미 존재하는 데이터 |
| `STORAGE_UPLOAD_FAILED` | Supabase Storage 업로드 실패 |
| `VIDEO_GENERATION_FAILED` | 영상 생성 작업 실패 |
| `WEATHER_API_ERROR` | 날씨 API 호출 실패 |
| `RATE_LIMIT_EXCEEDED` | 요청 한도 초과 |
| `INTERNAL_SERVER_ERROR` | 서버 내부 오류 |

---

## 3. 엔드포인트 목록 (Endpoint Index)

| Method | Path | 설명 | Auth |
|--------|------|-----|------|
| POST | `/auth/profile` | 프로필 생성 (최초 가입 후 호출) | Required |
| GET | `/auth/profile` | 내 프로필 조회 | Required |
| PATCH | `/auth/profile` | 프로필 수정 | Required |
| DELETE | `/auth/profile` | 계정 삭제 | Required |
| GET | `/items` | 버킷리스트 아이템 목록 조회 | Required |
| POST | `/items` | 아이템 생성 | Required |
| GET | `/items/{item_id}` | 아이템 상세 조회 | Required |
| PATCH | `/items/{item_id}` | 아이템 수정 | Required |
| DELETE | `/items/{item_id}` | 아이템 삭제 | Required |
| PATCH | `/items/{item_id}/complete` | 아이템 완료 처리 | Required |
| GET | `/items/{item_id}/logs` | 특정 아이템의 실천 기록 목록 | Required |
| POST | `/items/{item_id}/logs` | 실천 기록 생성 | Required |
| GET | `/logs/{log_id}` | 실천 기록 상세 조회 | Required |
| DELETE | `/logs/{log_id}` | 실천 기록 삭제 | Required |
| POST | `/logs/{log_id}/media` | 미디어 파일 업로드 (signed URL 발급) | Required |
| GET | `/recommendations/current` | 이번 주 추천 조회 | Required |
| GET | `/recommendations/history` | 추천 히스토리 목록 | Required |
| POST | `/recommendations/{rec_id}/accept` | 추천 수락 | Required |
| POST | `/recommendations/{rec_id}/skip` | 추천 건너뛰기 | Required |
| POST | `/videos` | 영상 생성 작업 요청 | Required |
| GET | `/videos/{video_id}` | 영상 상태 및 정보 조회 | Required |
| DELETE | `/videos/{video_id}` | 영상 삭제 | Required |
| GET | `/videos` | 내 영상 목록 조회 (갤러리) | Required |
| GET | `/videos/{video_id}/download-url` | 영상 다운로드 signed URL 발급 | Required |

---

## 4. 엔드포인트 상세 명세

---

### 4.1 인증 & 프로필

#### POST `/auth/profile`
최초 소셜/이메일 가입 후 닉네임을 저장한다.

**Request Body**
```json
{
  "nickname": "버킷도전러",
  "timezone": "Asia/Seoul"
}
```

**Response 201**
```json
{
  "id": "usr_01HX...",
  "email": "user@example.com",
  "nickname": "버킷도전러",
  "avatar_url": null,
  "timezone": "Asia/Seoul",
  "created_at": "2026-05-09T00:00:00Z"
}
```

---

#### GET `/auth/profile`

**Response 200**
```json
{
  "id": "usr_01HX...",
  "email": "user@example.com",
  "nickname": "버킷도전러",
  "avatar_url": "https://cdn.supabase.io/storage/v1/object/sign/avatars/usr_01HX.jpg?token=...",
  "timezone": "Asia/Seoul",
  "stats": {
    "total_items": 12,
    "completed_items": 3,
    "total_videos": 5
  },
  "created_at": "2026-05-09T00:00:00Z"
}
```

---

#### PATCH `/auth/profile`

**Request Body** (모든 필드 선택적)
```json
{
  "nickname": "새닉네임",
  "timezone": "Asia/Tokyo"
}
```

**Response 200** — 업데이트된 프로필 (GET `/auth/profile` 동일 구조)

---

#### DELETE `/auth/profile`
계정 및 모든 관련 데이터(아이템, 기록, 영상)를 삭제한다.

**Response 204** — 본문 없음

---

### 4.2 버킷리스트 아이템

#### GET `/items`

**Query Parameters**

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|-------|-----|
| `category` | string | - | 카테고리 필터 (travel, food, hobby, fitness, culture) |
| `status` | string | `active` | `active` \| `completed` \| `all` |
| `priority` | string | - | `high` \| `medium` \| `low` |
| `q` | string | - | 제목 검색 키워드 |
| `page` | int | 1 | 페이지 번호 |
| `limit` | int | 20 | 페이지당 항목 수 (max 50) |

**Response 200**
```json
{
  "data": [
    {
      "id": "item_01HX...",
      "title": "한라산 등반하기",
      "category": "travel",
      "priority": "high",
      "description": "제주도 여행 중 한라산 백록담까지 오르기",
      "tags": ["hiking", "jeju", "nature"],
      "status": "active",
      "last_recommended_at": null,
      "completed_at": null,
      "created_at": "2026-04-01T10:00:00Z",
      "updated_at": "2026-04-01T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "has_next": false
  }
}
```

---

#### POST `/items`

**Request Body**
```json
{
  "title": "한라산 등반하기",
  "category": "travel",
  "priority": "high",
  "description": "제주도 여행 중 한라산 백록담까지 오르기",
  "tags": ["hiking", "jeju", "nature"]
}
```

| 필드 | 필수 | 유효성 |
|-----|-----|-------|
| `title` | Yes | 1–100자 |
| `category` | Yes | 열거형 값 중 하나 |
| `priority` | No | `high` \| `medium` \| `low`, 기본값 `medium` |
| `description` | No | 최대 500자 |
| `tags` | No | 최대 10개, 각 20자 이하 |

**Response 201** — 생성된 아이템 (GET `/items` 배열 요소와 동일 구조)

---

#### GET `/items/{item_id}`

**Response 200**
```json
{
  "id": "item_01HX...",
  "title": "한라산 등반하기",
  "category": "travel",
  "priority": "high",
  "description": "제주도 여행 중 한라산 백록담까지 오르기",
  "tags": ["hiking", "jeju", "nature"],
  "status": "active",
  "logs_count": 2,
  "last_recommended_at": "2026-04-14T00:00:00Z",
  "completed_at": null,
  "created_at": "2026-04-01T10:00:00Z",
  "updated_at": "2026-04-14T00:00:00Z"
}
```

---

#### PATCH `/items/{item_id}`

**Request Body** (모든 필드 선택적)
```json
{
  "title": "한라산 등반하기 (성판악 코스)",
  "priority": "medium",
  "tags": ["hiking", "jeju"]
}
```

**Response 200** — 수정된 아이템

---

#### DELETE `/items/{item_id}`

**Response 204** — 본문 없음

---

#### PATCH `/items/{item_id}/complete`
아이템을 완료 상태로 전환한다. 이미 완료된 아이템에 재호출하면 `422`를 반환한다.

**Request Body** — 없음

**Response 200**
```json
{
  "id": "item_01HX...",
  "status": "completed",
  "completed_at": "2026-05-09T12:30:00Z"
}
```

---

### 4.3 실천 기록 (Activity Logs)

#### GET `/items/{item_id}/logs`

**Query Parameters**

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|-------|-----|
| `page` | int | 1 | 페이지 번호 |
| `limit` | int | 10 | 페이지당 항목 수 |

**Response 200**
```json
{
  "data": [
    {
      "id": "log_01HX...",
      "item_id": "item_01HX...",
      "note": "오늘 드디어 도전! 날씨가 맑아서 너무 좋았다.",
      "logged_at": "2026-05-09T08:00:00Z",
      "latitude": 33.3617,
      "longitude": 126.5292,
      "media": [
        {
          "id": "med_01HX...",
          "type": "image",
          "url": "https://cdn.supabase.io/storage/v1/object/sign/logs/med_01HX.jpg?token=...",
          "order": 1
        }
      ],
      "created_at": "2026-05-09T09:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1,
    "has_next": false
  }
}
```

---

#### POST `/items/{item_id}/logs`

**Request Body**
```json
{
  "note": "오늘 드디어 도전! 날씨가 맑아서 너무 좋았다.",
  "logged_at": "2026-05-09T08:00:00Z",
  "latitude": 33.3617,
  "longitude": 126.5292
}
```

**Response 201**
```json
{
  "id": "log_01HX...",
  "item_id": "item_01HX...",
  "note": "오늘 드디어 도전! 날씨가 맑아서 너무 좋았다.",
  "logged_at": "2026-05-09T08:00:00Z",
  "latitude": 33.3617,
  "longitude": 126.5292,
  "media": [],
  "created_at": "2026-05-09T09:00:00Z",
  "media_upload_urls": []
}
```

---

#### POST `/logs/{log_id}/media`
미디어 업로드를 위한 Supabase Storage signed URL을 발급한다.  
클라이언트는 발급받은 URL로 직접 PUT 요청을 보내 파일을 업로드한다.

**Request Body**
```json
{
  "files": [
    { "filename": "photo1.jpg", "content_type": "image/jpeg", "size_bytes": 2048000 },
    { "filename": "clip1.mp4",  "content_type": "video/mp4",  "size_bytes": 50000000 }
  ]
}
```

**Response 200**
```json
{
  "upload_urls": [
    {
      "media_id": "med_01HX...",
      "filename": "photo1.jpg",
      "upload_url": "https://cdn.supabase.io/storage/v1/object/logs/med_01HX.jpg?token=...",
      "expires_at": "2026-05-09T10:00:00Z"
    },
    {
      "media_id": "med_02HX...",
      "filename": "clip1.mp4",
      "upload_url": "https://cdn.supabase.io/storage/v1/object/logs/med_02HX.mp4?token=...",
      "expires_at": "2026-05-09T10:00:00Z"
    }
  ]
}
```

---

#### DELETE `/logs/{log_id}`

**Response 204** — 본문 없음

---

### 4.4 주간 추천 (Recommendations)

#### GET `/recommendations/current`
현재 주(월요일 기준) 추천 아이템을 반환한다.

**Response 200**
```json
{
  "id": "rec_01HX...",
  "week_start": "2026-05-04",
  "item": {
    "id": "item_01HX...",
    "title": "한라산 등반하기",
    "category": "travel",
    "priority": "high"
  },
  "reason": "이번 주 맑은 날씨와 봄 계절, 그리고 높은 우선순위를 고려해 선정했어요.",
  "score_breakdown": {
    "priority_score": 40,
    "recency_bonus": 20,
    "season_score": 18,
    "weather_score": 18
  },
  "status": "pending",
  "created_at": "2026-05-04T00:00:00Z"
}
```

**Response 404** (추천 없음)
```json
{
  "error": {
    "code": "RECOMMENDATION_NOT_FOUND",
    "message": "No recommendation found for the current week. Try adding more bucket list items.",
    "details": null
  }
}
```

---

#### GET `/recommendations/history`

**Query Parameters**

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|-------|-----|
| `page` | int | 1 | 페이지 번호 |
| `limit` | int | 10 | 페이지당 항목 수 |

**Response 200**
```json
{
  "data": [
    {
      "id": "rec_01HX...",
      "week_start": "2026-04-27",
      "item": {
        "id": "item_02HX...",
        "title": "야경 사진 찍기",
        "category": "hobby"
      },
      "status": "accepted",
      "accepted_at": "2026-04-27T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 5,
    "has_next": false
  }
}
```

---

#### POST `/recommendations/{rec_id}/accept`

**Response 200**
```json
{
  "id": "rec_01HX...",
  "status": "accepted",
  "accepted_at": "2026-05-09T09:00:00Z"
}
```

---

#### POST `/recommendations/{rec_id}/skip`

**Response 200**
```json
{
  "id": "rec_01HX...",
  "status": "skipped",
  "skipped_at": "2026-05-09T09:00:00Z"
}
```

---

### 4.5 영상 생성 (Video Generation)

#### POST `/videos`
Celery 비동기 작업을 큐에 등록하고 video_id를 즉시 반환한다.

**Request Body**
```json
{
  "log_id": "log_01HX...",
  "template": "cinematic",
  "bgm_track_id": "bgm_spring_01",
  "include_captions": true
}
```

| 필드 | 필수 | 유효성 |
|-----|-----|-------|
| `log_id` | Yes | 존재하는 자신의 log_id |
| `template` | Yes | `cinematic` \| `vlog` \| `minimal` \| `retro` |
| `bgm_track_id` | No | 유효한 BGM 트랙 ID |
| `include_captions` | No | boolean, 기본값 `true` |

**Response 202**
```json
{
  "video_id": "vid_01HX...",
  "status": "queued",
  "estimated_seconds": 120,
  "created_at": "2026-05-09T09:00:00Z"
}
```

---

#### GET `/videos/{video_id}`

**Response 200**
```json
{
  "id": "vid_01HX...",
  "log_id": "log_01HX...",
  "item": {
    "id": "item_01HX...",
    "title": "한라산 등반하기",
    "category": "travel"
  },
  "template": "cinematic",
  "bgm_track_id": "bgm_spring_01",
  "include_captions": true,
  "status": "completed",
  "duration_seconds": 58,
  "thumbnail_url": "https://cdn.supabase.io/storage/v1/object/sign/videos/vid_01HX_thumb.jpg?token=...",
  "stream_url": "https://cdn.supabase.io/storage/v1/object/sign/videos/vid_01HX.mp4?token=...",
  "created_at": "2026-05-09T09:00:00Z",
  "completed_at": "2026-05-09T09:02:10Z"
}
```

`status` 가능 값: `queued` | `processing` | `completed` | `failed`

---

#### DELETE `/videos/{video_id}`

**Response 204** — 본문 없음

---

#### GET `/videos`

**Query Parameters**

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|-------|-----|
| `category` | string | - | 카테고리 필터 |
| `year` | int | - | 연도 필터 (예: 2026) |
| `page` | int | 1 | 페이지 번호 |
| `limit` | int | 20 | 페이지당 항목 수 |

**Response 200**
```json
{
  "data": [
    {
      "id": "vid_01HX...",
      "item_title": "한라산 등반하기",
      "category": "travel",
      "thumbnail_url": "https://...",
      "duration_seconds": 58,
      "status": "completed",
      "created_at": "2026-05-09T09:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 5,
    "has_next": false
  }
}
```

---

#### GET `/videos/{video_id}/download-url`
유효기간 10분의 다운로드 signed URL을 발급한다.

**Response 200**
```json
{
  "download_url": "https://cdn.supabase.io/storage/v1/object/sign/videos/vid_01HX.mp4?token=...",
  "expires_at": "2026-05-09T09:10:00Z"
}
```

---

## 5. 페이지네이션 공통 규칙

- 모든 목록 API는 커서 기반이 아닌 오프셋 페이지네이션 사용
- `page` 는 1-indexed
- 응답에 항상 `pagination.total`, `pagination.has_next` 포함
- 최대 `limit` = 50

---

## 6. Rate Limiting

| 범위 | 한도 |
|-----|-----|
| 인증된 사용자 일반 API | 300 req/min |
| 미디어 업로드 URL 발급 | 30 req/min |
| 영상 생성 요청 | 5 req/day per user |
| 추천 스킵 | 3회/week per user |

한도 초과 시 `429 Too Many Requests` + `Retry-After` 헤더 반환.
