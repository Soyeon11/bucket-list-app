-- =============================================================================
-- Migration 002: Auto-create profile on user signup
-- Run via Supabase SQL Editor.
-- =============================================================================

-- Trigger function: fires after INSERT on auth.users
-- Creates a matching row in public.profiles using email prefix as default nickname.
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, nickname)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(
      NEW.raw_user_meta_data->>'nickname',
      split_part(NEW.email, '@', 1)
    )
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- Backfill: create profile rows for any existing auth.users without a profile
INSERT INTO public.profiles (id, email, nickname)
SELECT
  id,
  email,
  split_part(email, '@', 1)
FROM auth.users
ON CONFLICT (id) DO NOTHING;
