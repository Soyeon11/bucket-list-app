# Bucket List App — Database Schema

**Version:** 1.0  
**Last Updated:** 2026-05-09  
**Database:** Supabase (PostgreSQL 15)  
**Naming Convention:** snake_case, plural table names

---

## 1. 테이블 목록 (Table Index)

| 테이블명 | 설명 |
|---------|-----|
| `profiles` | 사용자 프로필 (Supabase Auth users 확장) |
| `bucket_items` | 버킷리스트 아이템 |
| `item_tags` | 아이템-태그 매핑 (다대다) |
| `activity_logs` | 실천 기록 |
| `media_files` | 실천 기록에 첨부된 미디어 파일 |
| `weekly_recommendations` | 주간 추천 기록 |
| `generated_videos` | 자동 생성된 쇼츠 영상 |
| `bgm_tracks` | 영상 생성에 사용되는 BGM 트랙 목록 (시스템 관리) |

---

## 2. 테이블 상세 정의

---

### 2.1 `profiles`
Supabase Auth `auth.users`와 1:1 연결. 앱 전용 프로필 데이터를 저장한다.

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|-----|------|---------|-------|-----|
| `id` | `uuid` | Yes | — | PK, `auth.users.id`와 동일값 사용 |
| `email` | `text` | Yes | — | 이메일 (auth.users에서 복사, 조회 편의) |
| `nickname` | `varchar(50)` | Yes | — | 표시 이름 |
| `avatar_url` | `text` | No | `NULL` | Supabase Storage 프로필 이미지 경로 |
| `timezone` | `varchar(50)` | Yes | `'Asia/Seoul'` | IANA 타임존 문자열 |
| `created_at` | `timestamptz` | Yes | `now()` | 생성 시각 |
| `updated_at` | `timestamptz` | Yes | `now()` | 최종 수정 시각 (트리거로 자동 갱신) |

**Constraints:**
- `PK`: `id`
- `FK`: `id` → `auth.users(id)` ON DELETE CASCADE
- `UNIQUE`: `email`

---

### 2.2 `bucket_items`
사용자의 버킷리스트 아이템.

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|-----|------|---------|-------|-----|
| `id` | `uuid` | Yes | `gen_random_uuid()` | PK |
| `user_id` | `uuid` | Yes | — | FK → `profiles(id)` |
| `title` | `varchar(100)` | Yes | — | 아이템 제목 |
| `category` | `category_enum` | Yes | — | 카테고리 (열거형) |
| `priority` | `priority_enum` | Yes | `'medium'` | 우선순위 |
| `description` | `varchar(500)` | No | `NULL` | 상세 설명 |
| `status` | `item_status_enum` | Yes | `'active'` | 상태 |
| `last_recommended_at` | `timestamptz` | No | `NULL` | 마지막으로 주간 추천된 시각 |
| `completed_at` | `timestamptz` | No | `NULL` | 완료 처리 시각 |
| `created_at` | `timestamptz` | Yes | `now()` | 생성 시각 |
| `updated_at` | `timestamptz` | Yes | `now()` | 최종 수정 시각 (트리거로 자동 갱신) |

**Enum 타입 정의:**

```sql
CREATE TYPE category_enum AS ENUM (
  'travel', 'food', 'hobby', 'fitness', 'culture', 'etc'
);

CREATE TYPE priority_enum AS ENUM ('high', 'medium', 'low');

CREATE TYPE item_status_enum AS ENUM ('active', 'completed');
```

**Constraints:**
- `PK`: `id`
- `FK`: `user_id` → `profiles(id)` ON DELETE CASCADE

---

### 2.3 `item_tags`
버킷리스트 아이템과 자유 태그의 다대다 매핑.

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|-----|------|---------|-------|-----|
| `item_id` | `uuid` | Yes | — | FK → `bucket_items(id)` |
| `tag` | `varchar(20)` | Yes | — | 태그 문자열 (소문자 정규화) |

**Constraints:**
- `PK`: (`item_id`, `tag`)
- `FK`: `item_id` → `bucket_items(id)` ON DELETE CASCADE

---

### 2.4 `activity_logs`
버킷리스트 아이템에 대한 실천 기록.

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|-----|------|---------|-------|-----|
| `id` | `uuid` | Yes | `gen_random_uuid()` | PK |
| `user_id` | `uuid` | Yes | — | FK → `profiles(id)` (RLS용 직접 참조) |
| `item_id` | `uuid` | Yes | — | FK → `bucket_items(id)` |
| `note` | `text` | No | `NULL` | 텍스트 메모 |
| `logged_at` | `timestamptz` | Yes | `now()` | 실제 활동 일시 (사용자 입력) |
| `latitude` | `numeric(9,6)` | No | `NULL` | 위도 |
| `longitude` | `numeric(9,6)` | No | `NULL` | 경도 |
| `created_at` | `timestamptz` | Yes | `now()` | 레코드 생성 시각 |

**Constraints:**
- `PK`: `id`
- `FK`: `user_id` → `profiles(id)` ON DELETE CASCADE
- `FK`: `item_id` → `bucket_items(id)` ON DELETE CASCADE
- `CHECK`: `latitude BETWEEN -90 AND 90`
- `CHECK`: `longitude BETWEEN -180 AND 180`

---

### 2.5 `media_files`
실천 기록에 첨부된 이미지/영상 파일 메타데이터.

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|-----|------|---------|-------|-----|
| `id` | `uuid` | Yes | `gen_random_uuid()` | PK |
| `log_id` | `uuid` | Yes | — | FK → `activity_logs(id)` |
| `user_id` | `uuid` | Yes | — | FK → `profiles(id)` (RLS용) |
| `type` | `media_type_enum` | Yes | — | 파일 유형 |
| `storage_path` | `text` | Yes | — | Supabase Storage 오브젝트 경로 |
| `size_bytes` | `bigint` | Yes | — | 파일 크기 (바이트) |
| `mime_type` | `varchar(100)` | Yes | — | MIME 타입 (예: image/jpeg) |
| `order` | `smallint` | Yes | `1` | 동일 로그 내 표시 순서 |
| `upload_status` | `upload_status_enum` | Yes | `'pending'` | 업로드 상태 |
| `created_at` | `timestamptz` | Yes | `now()` | 생성 시각 |

**Enum 타입 정의:**

```sql
CREATE TYPE media_type_enum AS ENUM ('image', 'video');

CREATE TYPE upload_status_enum AS ENUM ('pending', 'uploaded', 'failed');
```

**Constraints:**
- `PK`: `id`
- `FK`: `log_id` → `activity_logs(id)` ON DELETE CASCADE
- `FK`: `user_id` → `profiles(id)` ON DELETE CASCADE
- `CHECK`: `size_bytes > 0`
- `CHECK`: `order >= 1`

---

### 2.6 `weekly_recommendations`
매주 사용자에게 생성되는 추천 기록.

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|-----|------|---------|-------|-----|
| `id` | `uuid` | Yes | `gen_random_uuid()` | PK |
| `user_id` | `uuid` | Yes | — | FK → `profiles(id)` |
| `item_id` | `uuid` | Yes | — | FK → `bucket_items(id)` |
| `week_start` | `date` | Yes | — | 해당 주 월요일 날짜 |
| `reason` | `text` | No | `NULL` | 추천 이유 텍스트 |
| `score_breakdown` | `jsonb` | No | `NULL` | 점수 세부 내역 (priority, recency, season, weather) |
| `status` | `rec_status_enum` | Yes | `'pending'` | 추천 처리 상태 |
| `accepted_at` | `timestamptz` | No | `NULL` | 수락 시각 |
| `skipped_at` | `timestamptz` | No | `NULL` | 건너뛰기 시각 |
| `created_at` | `timestamptz` | Yes | `now()` | 생성 시각 |

**Enum 타입 정의:**

```sql
CREATE TYPE rec_status_enum AS ENUM ('pending', 'accepted', 'skipped');
```

**Constraints:**
- `PK`: `id`
- `FK`: `user_id` → `profiles(id)` ON DELETE CASCADE
- `FK`: `item_id` → `bucket_items(id)` ON DELETE CASCADE
- `UNIQUE`: (`user_id`, `week_start`) — 한 주에 사용자당 추천 1개

---

### 2.7 `generated_videos`
FFmpeg + moviepy로 생성된 쇼츠 영상.

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|-----|------|---------|-------|-----|
| `id` | `uuid` | Yes | `gen_random_uuid()` | PK |
| `user_id` | `uuid` | Yes | — | FK → `profiles(id)` (RLS용) |
| `log_id` | `uuid` | Yes | — | FK → `activity_logs(id)` |
| `celery_task_id` | `varchar(255)` | No | `NULL` | Celery task ID (진행 상태 추적용) |
| `template` | `varchar(50)` | Yes | — | 사용된 템플릿 이름 |
| `bgm_track_id` | `uuid` | No | `NULL` | FK → `bgm_tracks(id)` |
| `include_captions` | `boolean` | Yes | `true` | 자막 포함 여부 |
| `status` | `video_status_enum` | Yes | `'queued'` | 생성 상태 |
| `duration_seconds` | `smallint` | No | `NULL` | 최종 영상 재생 시간(초) |
| `storage_path` | `text` | No | `NULL` | Supabase Storage 영상 파일 경로 |
| `thumbnail_path` | `text` | No | `NULL` | 썸네일 이미지 경로 |
| `error_message` | `text` | No | `NULL` | 생성 실패 시 에러 메시지 |
| `created_at` | `timestamptz` | Yes | `now()` | 생성 요청 시각 |
| `completed_at` | `timestamptz` | No | `NULL` | 생성 완료 시각 |

**Enum 타입 정의:**

```sql
CREATE TYPE video_status_enum AS ENUM ('queued', 'processing', 'completed', 'failed');
```

**Constraints:**
- `PK`: `id`
- `FK`: `user_id` → `profiles(id)` ON DELETE CASCADE
- `FK`: `log_id` → `activity_logs(id)` ON DELETE CASCADE
- `FK`: `bgm_track_id` → `bgm_tracks(id)` ON DELETE SET NULL

---

### 2.8 `bgm_tracks`
시스템 관리자가 사전 등록한 BGM 트랙 목록.

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|-----|------|---------|-------|-----|
| `id` | `uuid` | Yes | `gen_random_uuid()` | PK |
| `name` | `varchar(100)` | Yes | — | 트랙 표시 이름 |
| `artist` | `varchar(100)` | No | `NULL` | 아티스트/출처 |
| `storage_path` | `text` | Yes | — | Supabase Storage 오디오 파일 경로 |
| `duration_seconds` | `smallint` | Yes | — | 트랙 길이(초) |
| `mood_tags` | `text[]` | No | `'{}'` | 분위기 태그 배열 (예: {upbeat, cinematic}) |
| `is_active` | `boolean` | Yes | `true` | 사용자에게 노출 여부 |
| `created_at` | `timestamptz` | Yes | `now()` | 생성 시각 |

**Constraints:**
- `PK`: `id`

---

## 3. 테이블 관계 (ERD — 텍스트 형식)

```
auth.users (Supabase 관리)
    │ 1
    │ FK: profiles.id → auth.users.id
    ▼ 1
profiles
    │ 1
    ├──────────────────────────────── 1:N ──▶ bucket_items
    │                                              │ 1
    │                                              ├──── 1:N ──▶ item_tags
    │                                              │
    │                                              └──── 1:N ──▶ weekly_recommendations
    │
    ├──────────────────────────────── 1:N ──▶ activity_logs
    │                                              │ 1
    │                                              ├──── 1:N ──▶ media_files
    │                                              │
    │                                              └──── 1:N ──▶ generated_videos
    │                                                                │
    │                                                                └── N:1 ──▶ bgm_tracks
    │
    └──────────────────────────────── 1:N ──▶ generated_videos (user_id 직접 참조)

notes:
- bucket_items ──── 1:N ──▶ activity_logs  (item_id FK)
- bucket_items ──── 1:N ──▶ weekly_recommendations (item_id FK)
```

---

## 4. Supabase RLS (Row Level Security) 정책

모든 테이블에 RLS를 활성화하고 기본 정책을 deny로 설정한다.

```sql
-- Enable RLS on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE bucket_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE item_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE media_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE weekly_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE bgm_tracks ENABLE ROW LEVEL SECURITY;
```

---

### 4.1 `profiles` RLS

```sql
-- Users can read only their own profile
CREATE POLICY "profiles_select_own"
  ON profiles FOR SELECT
  USING (auth.uid() = id);

-- Users can update only their own profile
CREATE POLICY "profiles_update_own"
  ON profiles FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Profile is created by backend service role after auth signup
-- INSERT/DELETE are handled by service role (no user-facing policy)
```

---

### 4.2 `bucket_items` RLS

```sql
CREATE POLICY "bucket_items_select_own"
  ON bucket_items FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "bucket_items_insert_own"
  ON bucket_items FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "bucket_items_update_own"
  ON bucket_items FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "bucket_items_delete_own"
  ON bucket_items FOR DELETE
  USING (auth.uid() = user_id);
```

---

### 4.3 `item_tags` RLS

```sql
-- Users can manage tags for their own items only
CREATE POLICY "item_tags_select_own"
  ON item_tags FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM bucket_items
      WHERE bucket_items.id = item_tags.item_id
        AND bucket_items.user_id = auth.uid()
    )
  );

CREATE POLICY "item_tags_insert_own"
  ON item_tags FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM bucket_items
      WHERE bucket_items.id = item_tags.item_id
        AND bucket_items.user_id = auth.uid()
    )
  );

CREATE POLICY "item_tags_delete_own"
  ON item_tags FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM bucket_items
      WHERE bucket_items.id = item_tags.item_id
        AND bucket_items.user_id = auth.uid()
    )
  );
```

---

### 4.4 `activity_logs`, `media_files`, `weekly_recommendations`, `generated_videos` RLS

모두 동일 패턴: `user_id = auth.uid()` 조건.

```sql
-- Pattern applies to: activity_logs, media_files, weekly_recommendations, generated_videos
-- Replace <TABLE> with the actual table name

CREATE POLICY "<TABLE>_select_own"
  ON <TABLE> FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "<TABLE>_insert_own"
  ON <TABLE> FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "<TABLE>_update_own"
  ON <TABLE> FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "<TABLE>_delete_own"
  ON <TABLE> FOR DELETE
  USING (auth.uid() = user_id);
```

---

### 4.5 `bgm_tracks` RLS

모든 인증된 사용자가 읽기 가능, 쓰기는 서비스 롤 전용.

```sql
CREATE POLICY "bgm_tracks_select_authenticated"
  ON bgm_tracks FOR SELECT
  TO authenticated
  USING (is_active = true);

-- INSERT/UPDATE/DELETE: service role only (no user policy)
```

---

## 5. 인덱스 설계 (Index Design)

```sql
-- bucket_items: 자주 쓰이는 조회 패턴 최적화
CREATE INDEX idx_bucket_items_user_status
  ON bucket_items (user_id, status);

CREATE INDEX idx_bucket_items_user_category
  ON bucket_items (user_id, category);

CREATE INDEX idx_bucket_items_last_recommended
  ON bucket_items (user_id, last_recommended_at NULLS FIRST);

-- Full-text search on title (Korean + English)
CREATE INDEX idx_bucket_items_title_fts
  ON bucket_items USING GIN (to_tsvector('simple', title));

-- activity_logs: 아이템별 기록 목록 조회
CREATE INDEX idx_activity_logs_item_logged
  ON activity_logs (item_id, logged_at DESC);

CREATE INDEX idx_activity_logs_user
  ON activity_logs (user_id);

-- media_files: 로그별 미디어 순서 조회
CREATE INDEX idx_media_files_log_order
  ON media_files (log_id, "order");

-- weekly_recommendations: 이번 주 추천 조회
CREATE INDEX idx_weekly_rec_user_week
  ON weekly_recommendations (user_id, week_start DESC);

-- generated_videos: 갤러리 조회
CREATE INDEX idx_generated_videos_user_created
  ON generated_videos (user_id, created_at DESC);

CREATE INDEX idx_generated_videos_status
  ON generated_videos (status)
  WHERE status IN ('queued', 'processing');
```

---

## 6. 자동 updated_at 트리거

```sql
-- Generic trigger function for updated_at
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to tables with updated_at column
CREATE TRIGGER trg_profiles_updated_at
  BEFORE UPDATE ON profiles
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_bucket_items_updated_at
  BEFORE UPDATE ON bucket_items
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

---

## 7. Supabase Storage 버킷 설계

| 버킷 이름 | 접근 수준 | 파일 크기 제한 | 허용 MIME 타입 | 용도 |
|---------|---------|------------|-------------|-----|
| `avatars` | private | 5 MB | `image/*` | 프로필 이미지 |
| `logs` | private | 200 MB | `image/*`, `video/*` | 실천 기록 미디어 |
| `videos` | private | 500 MB | `video/mp4` | 생성된 쇼츠 영상 |
| `bgm` | private | 20 MB | `audio/*` | BGM 트랙 (서비스 롤 전용 업로드) |

모든 버킷은 **private**; 클라이언트는 반드시 signed URL을 통해서만 접근.  
Signed URL 기본 유효 기간: 열람용 1시간, 다운로드용 10분.

---

## 8. 주요 쿼리 패턴 예시

### 8.1 추천 알고리즘 후보 목록 조회

```sql
-- Fetch all active items for a user, ordered by recommendation score candidates
SELECT
    id,
    title,
    category,
    priority,
    last_recommended_at,
    EXTRACT(EPOCH FROM (now() - COALESCE(last_recommended_at, created_at))) / 604800 AS weeks_since_recommended
FROM bucket_items
WHERE user_id = $1
  AND status = 'active'
ORDER BY last_recommended_at ASC NULLS FIRST;
```

### 8.2 갤러리 목록 (완료된 영상만)

```sql
SELECT
    gv.id,
    gv.thumbnail_path,
    gv.duration_seconds,
    gv.created_at,
    bi.title AS item_title,
    bi.category
FROM generated_videos gv
JOIN activity_logs al ON al.id = gv.log_id
JOIN bucket_items bi ON bi.id = al.item_id
WHERE gv.user_id = $1
  AND gv.status = 'completed'
ORDER BY gv.created_at DESC
LIMIT $2 OFFSET $3;
```
