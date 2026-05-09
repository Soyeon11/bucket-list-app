-- Migration 003: Add 'outdoor' to category_enum
-- Reason: Frontend uses 'outdoor' (아웃도어 🏔️) but DB only had 'etc'.
-- Run once via Supabase SQL Editor.

ALTER TYPE category_enum ADD VALUE IF NOT EXISTS 'outdoor';
