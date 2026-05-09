-- =============================================================================
-- Migration 001: Initial Schema
-- Database: Supabase (PostgreSQL 15)
-- Run this script once via Supabase SQL Editor or psql.
-- =============================================================================

-- =============================================================================
-- SECTION 1: Enum Types
-- =============================================================================

CREATE TYPE category_enum AS ENUM (
    'travel', 'food', 'hobby', 'fitness', 'culture', 'etc'
);

CREATE TYPE priority_enum AS ENUM ('high', 'medium', 'low');

CREATE TYPE item_status_enum AS ENUM ('active', 'completed');

CREATE TYPE media_type_enum AS ENUM ('image', 'video');

CREATE TYPE upload_status_enum AS ENUM ('pending', 'uploaded', 'failed');

CREATE TYPE rec_status_enum AS ENUM ('pending', 'accepted', 'skipped');

CREATE TYPE video_status_enum AS ENUM ('queued', 'processing', 'completed', 'failed');


-- =============================================================================
-- SECTION 2: Trigger Function (auto-update updated_at)
-- =============================================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- =============================================================================
-- SECTION 3: Tables
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 3.1 profiles
-- 1:1 extension of auth.users — stores app-specific user data.
-- ---------------------------------------------------------------------------
CREATE TABLE profiles (
    id          uuid        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email       text        NOT NULL UNIQUE,
    nickname    varchar(50) NOT NULL,
    avatar_url  text,
    timezone    varchar(50) NOT NULL DEFAULT 'Asia/Seoul',
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TRIGGER trg_profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ---------------------------------------------------------------------------
-- 3.2 bucket_items
-- ---------------------------------------------------------------------------
CREATE TABLE bucket_items (
    id                    uuid             PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id               uuid             NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title                 varchar(100)     NOT NULL,
    category              category_enum    NOT NULL,
    priority              priority_enum    NOT NULL DEFAULT 'medium',
    description           varchar(500),
    status                item_status_enum NOT NULL DEFAULT 'active',
    last_recommended_at   timestamptz,
    completed_at          timestamptz,
    created_at            timestamptz      NOT NULL DEFAULT now(),
    updated_at            timestamptz      NOT NULL DEFAULT now()
);

CREATE TRIGGER trg_bucket_items_updated_at
    BEFORE UPDATE ON bucket_items
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ---------------------------------------------------------------------------
-- 3.3 item_tags
-- Many-to-many: bucket_items <-> tags (free-text, lowercase)
-- ---------------------------------------------------------------------------
CREATE TABLE item_tags (
    item_id uuid        NOT NULL REFERENCES bucket_items(id) ON DELETE CASCADE,
    tag     varchar(20) NOT NULL,
    PRIMARY KEY (item_id, tag)
);


-- ---------------------------------------------------------------------------
-- 3.4 activity_logs
-- ---------------------------------------------------------------------------
CREATE TABLE activity_logs (
    id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid        NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    item_id     uuid        NOT NULL REFERENCES bucket_items(id) ON DELETE CASCADE,
    note        text,
    logged_at   timestamptz NOT NULL DEFAULT now(),
    latitude    numeric(9,6) CHECK (latitude BETWEEN -90 AND 90),
    longitude   numeric(9,6) CHECK (longitude BETWEEN -180 AND 180),
    created_at  timestamptz NOT NULL DEFAULT now()
);


-- ---------------------------------------------------------------------------
-- 3.5 media_files
-- ---------------------------------------------------------------------------
CREATE TABLE media_files (
    id             uuid               PRIMARY KEY DEFAULT gen_random_uuid(),
    log_id         uuid               NOT NULL REFERENCES activity_logs(id) ON DELETE CASCADE,
    user_id        uuid               NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    type           media_type_enum    NOT NULL,
    storage_path   text               NOT NULL,
    size_bytes     bigint             NOT NULL CHECK (size_bytes > 0),
    mime_type      varchar(100)       NOT NULL,
    "order"        smallint           NOT NULL DEFAULT 1 CHECK ("order" >= 1),
    upload_status  upload_status_enum NOT NULL DEFAULT 'pending',
    created_at     timestamptz        NOT NULL DEFAULT now()
);


-- ---------------------------------------------------------------------------
-- 3.6 weekly_recommendations
-- One recommendation per user per week (enforced by UNIQUE constraint).
-- ---------------------------------------------------------------------------
CREATE TABLE weekly_recommendations (
    id               uuid             PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          uuid             NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    item_id          uuid             NOT NULL REFERENCES bucket_items(id) ON DELETE CASCADE,
    week_start       date             NOT NULL,
    reason           text,
    score_breakdown  jsonb,
    status           rec_status_enum  NOT NULL DEFAULT 'pending',
    accepted_at      timestamptz,
    skipped_at       timestamptz,
    created_at       timestamptz      NOT NULL DEFAULT now(),
    UNIQUE (user_id, week_start)
);


-- ---------------------------------------------------------------------------
-- 3.7 bgm_tracks  (system-managed, populated by admins)
-- ---------------------------------------------------------------------------
CREATE TABLE bgm_tracks (
    id               uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    name             varchar(100) NOT NULL,
    artist           varchar(100),
    storage_path     text         NOT NULL,
    duration_seconds smallint     NOT NULL,
    mood_tags        text[]       NOT NULL DEFAULT '{}',
    is_active        boolean      NOT NULL DEFAULT true,
    created_at       timestamptz  NOT NULL DEFAULT now()
);


-- ---------------------------------------------------------------------------
-- 3.8 generated_videos
-- ---------------------------------------------------------------------------
CREATE TABLE generated_videos (
    id               uuid               PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          uuid               NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    log_id           uuid               NOT NULL REFERENCES activity_logs(id) ON DELETE CASCADE,
    celery_task_id   varchar(255),
    template         varchar(50)        NOT NULL,
    bgm_track_id     uuid               REFERENCES bgm_tracks(id) ON DELETE SET NULL,
    include_captions boolean            NOT NULL DEFAULT true,
    status           video_status_enum  NOT NULL DEFAULT 'queued',
    duration_seconds smallint,
    storage_path     text,
    thumbnail_path   text,
    error_message    text,
    created_at       timestamptz        NOT NULL DEFAULT now(),
    completed_at     timestamptz
);


-- =============================================================================
-- SECTION 4: Indexes
-- =============================================================================

-- bucket_items: common query patterns
CREATE INDEX idx_bucket_items_user_status
    ON bucket_items (user_id, status);

CREATE INDEX idx_bucket_items_user_category
    ON bucket_items (user_id, category);

CREATE INDEX idx_bucket_items_last_recommended
    ON bucket_items (user_id, last_recommended_at NULLS FIRST);

-- Full-text search on title (Korean + English via 'simple' config)
CREATE INDEX idx_bucket_items_title_fts
    ON bucket_items USING GIN (to_tsvector('simple', title));

-- activity_logs
CREATE INDEX idx_activity_logs_item_logged
    ON activity_logs (item_id, logged_at DESC);

CREATE INDEX idx_activity_logs_user
    ON activity_logs (user_id);

-- media_files
CREATE INDEX idx_media_files_log_order
    ON media_files (log_id, "order");

-- weekly_recommendations
CREATE INDEX idx_weekly_rec_user_week
    ON weekly_recommendations (user_id, week_start DESC);

-- generated_videos
CREATE INDEX idx_generated_videos_user_created
    ON generated_videos (user_id, created_at DESC);

CREATE INDEX idx_generated_videos_status
    ON generated_videos (status)
    WHERE status IN ('queued', 'processing');


-- =============================================================================
-- SECTION 5: Row Level Security (RLS)
-- =============================================================================

-- Enable RLS on every table
ALTER TABLE profiles              ENABLE ROW LEVEL SECURITY;
ALTER TABLE bucket_items          ENABLE ROW LEVEL SECURITY;
ALTER TABLE item_tags             ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_logs         ENABLE ROW LEVEL SECURITY;
ALTER TABLE media_files           ENABLE ROW LEVEL SECURITY;
ALTER TABLE weekly_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_videos      ENABLE ROW LEVEL SECURITY;
ALTER TABLE bgm_tracks            ENABLE ROW LEVEL SECURITY;


-- ---------------------------------------------------------------------------
-- 5.1 profiles
-- ---------------------------------------------------------------------------
CREATE POLICY "profiles_select_own"
    ON profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "profiles_update_own"
    ON profiles FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- INSERT and DELETE are handled by service role (no user-facing policy)


-- ---------------------------------------------------------------------------
-- 5.2 bucket_items
-- ---------------------------------------------------------------------------
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


-- ---------------------------------------------------------------------------
-- 5.3 item_tags  (inherit ownership via parent bucket_items)
-- ---------------------------------------------------------------------------
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


-- ---------------------------------------------------------------------------
-- 5.4 activity_logs
-- ---------------------------------------------------------------------------
CREATE POLICY "activity_logs_select_own"
    ON activity_logs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "activity_logs_insert_own"
    ON activity_logs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "activity_logs_update_own"
    ON activity_logs FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "activity_logs_delete_own"
    ON activity_logs FOR DELETE
    USING (auth.uid() = user_id);


-- ---------------------------------------------------------------------------
-- 5.5 media_files
-- ---------------------------------------------------------------------------
CREATE POLICY "media_files_select_own"
    ON media_files FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "media_files_insert_own"
    ON media_files FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "media_files_update_own"
    ON media_files FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "media_files_delete_own"
    ON media_files FOR DELETE
    USING (auth.uid() = user_id);


-- ---------------------------------------------------------------------------
-- 5.6 weekly_recommendations
-- ---------------------------------------------------------------------------
CREATE POLICY "weekly_recommendations_select_own"
    ON weekly_recommendations FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "weekly_recommendations_insert_own"
    ON weekly_recommendations FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "weekly_recommendations_update_own"
    ON weekly_recommendations FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "weekly_recommendations_delete_own"
    ON weekly_recommendations FOR DELETE
    USING (auth.uid() = user_id);


-- ---------------------------------------------------------------------------
-- 5.7 generated_videos
-- ---------------------------------------------------------------------------
CREATE POLICY "generated_videos_select_own"
    ON generated_videos FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "generated_videos_insert_own"
    ON generated_videos FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "generated_videos_update_own"
    ON generated_videos FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "generated_videos_delete_own"
    ON generated_videos FOR DELETE
    USING (auth.uid() = user_id);


-- ---------------------------------------------------------------------------
-- 5.8 bgm_tracks  (read-only for authenticated users; writes via service role)
-- ---------------------------------------------------------------------------
CREATE POLICY "bgm_tracks_select_authenticated"
    ON bgm_tracks FOR SELECT
    TO authenticated
    USING (is_active = true);

-- INSERT / UPDATE / DELETE: service role only (no user-facing policy)


-- =============================================================================
-- SECTION 6: Supabase Storage Buckets
-- (Run separately via Supabase dashboard or Storage API if SQL not supported)
-- =============================================================================

-- NOTE: Bucket creation via SQL is not supported in all Supabase tiers.
-- If the following INSERT fails, create buckets manually in the dashboard:
--   - avatars  (private, 5 MB,  image/*)
--   - logs     (private, 200 MB, image/* + video/*)
--   - videos   (private, 500 MB, video/mp4)
--   - bgm      (private, 20 MB,  audio/*)

-- INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
-- VALUES
--     ('avatars', 'avatars', false, 5242880,    ARRAY['image/*']),
--     ('logs',    'logs',    false, 209715200,  ARRAY['image/*', 'video/*']),
--     ('videos',  'videos',  false, 524288000,  ARRAY['video/mp4']),
--     ('bgm',     'bgm',     false, 20971520,   ARRAY['audio/*']);
