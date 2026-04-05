-- Automated Upload System Schema

-- Scheduled uploads table
CREATE TABLE IF NOT EXISTS scheduled_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clip_id UUID NOT NULL REFERENCES clips(id) ON DELETE CASCADE,
    platform VARCHAR(20) NOT NULL, -- 'tiktok', 'youtube', 'instagram'
    scheduled_at TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'uploading', 'success', 'failed', 'cancelled'
    attempts INT DEFAULT 0,
    max_attempts INT DEFAULT 3,
    last_error TEXT,
    video_url TEXT, -- URL of published video
    platform_video_id VARCHAR(200), -- TikTok/YouTube video ID
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Platform credentials table (encrypted)
CREATE TABLE IF NOT EXISTS platform_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR(20) NOT NULL,
    credentials_type VARCHAR(50), -- 'cookies', 'oauth', 'api_key'
    credentials_data JSONB NOT NULL, -- Encrypted tokens/cookies
    is_active BOOLEAN DEFAULT true,
    last_used TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, platform)
);

-- Upload logs for debugging
CREATE TABLE IF NOT EXISTS upload_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheduled_upload_id UUID REFERENCES scheduled_uploads(id) ON DELETE CASCADE,
    level VARCHAR(20), -- 'info', 'warning', 'error'
    message TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_scheduled_uploads_status ON scheduled_uploads(status);
CREATE INDEX IF NOT EXISTS idx_scheduled_uploads_scheduled_at ON scheduled_uploads(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_scheduled_uploads_platform ON scheduled_uploads(platform);
CREATE INDEX IF NOT EXISTS idx_platform_credentials_user_platform ON platform_credentials(user_id, platform);

-- Function to update updated_at
CREATE OR REPLACE FUNCTION update_scheduled_upload_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_scheduled_upload
BEFORE UPDATE ON scheduled_uploads
FOR EACH ROW
EXECUTE FUNCTION update_scheduled_upload_timestamp();

-- Function to clean old completed uploads (keep last 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_uploads()
RETURNS void AS $$
BEGIN
    DELETE FROM scheduled_uploads
    WHERE status IN ('success', 'cancelled')
    AND completed_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- View for upload statistics
CREATE OR REPLACE VIEW upload_stats AS
SELECT 
    platform,
    status,
    DATE(scheduled_at) as date,
    COUNT(*) as count
FROM scheduled_uploads
GROUP BY platform, status, DATE(scheduled_at);
