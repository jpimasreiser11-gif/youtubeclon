-- AI Thumbnails Schema
CREATE TABLE IF NOT EXISTS thumbnails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clip_id UUID NOT NULL REFERENCES clips(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    viral_text VARCHAR(200),
    score FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(clip_id)
);

CREATE INDEX IF NOT EXISTS idx_thumbnails_clip_id ON thumbnails(clip_id);
