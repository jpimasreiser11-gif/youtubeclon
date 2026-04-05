-- Migration to add daily automation features
ALTER TABLE projects ADD COLUMN IF NOT EXISTS auto_publish_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS publish_slots_per_day INTEGER DEFAULT 3;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS publish_platforms TEXT[] DEFAULT '{tiktok, youtube}';

-- Column for max attempts in scheduled_publications (fixing missing columns from upload_scheduler.py)
ALTER TABLE scheduled_publications ADD COLUMN IF NOT EXISTS attempts INTEGER DEFAULT 0;
ALTER TABLE scheduled_publications ADD COLUMN IF NOT EXISTS max_attempts INTEGER DEFAULT 3;
