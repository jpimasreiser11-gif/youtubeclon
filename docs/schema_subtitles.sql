-- Subtitle System Schema
-- Add transcriptions table for storing Whisper output

CREATE TABLE IF NOT EXISTS transcriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clip_id UUID NOT NULL REFERENCES clips(id) ON DELETE CASCADE,
    language VARCHAR(10) DEFAULT 'es',
    words JSONB NOT NULL,
    -- words format: [{"word": "Hola", "start": 0.5, "end": 1.0, "confidence": 0.99}]
    edited BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(clip_id)
);

-- Add subtitle style preferences to clips
ALTER TABLE clips ADD COLUMN IF NOT EXISTS subtitle_style VARCHAR(50) DEFAULT 'tiktok';
-- Possible values: 'tiktok', 'youtube_shorts', 'instagram_reels', 'custom'

ALTER TABLE clips ADD COLUMN IF NOT EXISTS subtitle_config JSONB DEFAULT '{}';
-- Custom config: {"font": "Arial-Bold", "size": 70, "color": "yellow", "position": "bottom", "animation": "pop"}

-- Add transcription status
ALTER TABLE clips ADD COLUMN IF NOT EXISTS transcription_status VARCHAR(20) DEFAULT 'pending';
-- Values: 'pending', 'processing', 'completed', 'failed'

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_transcriptions_clip_id ON transcriptions(clip_id);
CREATE INDEX IF NOT EXISTS idx_clips_transcription_status ON clips(transcription_status);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_transcription_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_transcription_timestamp
BEFORE UPDATE ON transcriptions
FOR EACH ROW
EXECUTE FUNCTION update_transcription_timestamp();
