-- Migration 005: Optional descriptive columns for clips table
-- Safe to run multiple times.

ALTER TABLE clips
    ADD COLUMN IF NOT EXISTS title_generated TEXT,
    ADD COLUMN IF NOT EXISTS description_generated TEXT,
    ADD COLUMN IF NOT EXISTS hook_description TEXT,
    ADD COLUMN IF NOT EXISTS payoff_description TEXT;
