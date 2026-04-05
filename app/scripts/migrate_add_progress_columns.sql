-- Migration: Add missing progress tracking columns to projects table
-- Run once against the antigravity DB

-- progress_percent: 0-100 integer, replaces the old 'progress' column usage
ALTER TABLE projects ADD COLUMN IF NOT EXISTS progress_percent INTEGER DEFAULT 0;

-- eta_seconds: estimated seconds remaining, replaces 'estimated_time_remaining'
ALTER TABLE projects ADD COLUMN IF NOT EXISTS eta_seconds INTEGER DEFAULT 0;

-- current_step: human-readable description of the current processing step
ALTER TABLE projects ADD COLUMN IF NOT EXISTS current_step TEXT DEFAULT NULL;

-- Backfill legacy data: copy old 'progress' values to progress_percent
UPDATE projects SET progress_percent = progress WHERE progress_percent = 0 AND progress IS NOT NULL;

-- Backfill legacy: copy estimated_time_remaining to eta_seconds
UPDATE projects SET eta_seconds = estimated_time_remaining WHERE eta_seconds = 0 AND estimated_time_remaining IS NOT NULL;
