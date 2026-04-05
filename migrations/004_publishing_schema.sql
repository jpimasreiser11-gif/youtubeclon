-- Migration 004: Publishing & Connections
-- Unifies the schema for YouTube/TikTok automation

-- 1. Platform Connections (Status & Metadata)
CREATE TABLE IF NOT EXISTS platform_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR(20) NOT NULL, -- 'youtube', 'tiktok'
    connected BOOLEAN DEFAULT true,
    account_name VARCHAR(255),
    last_sync TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, platform)
);

-- 2. Platform Credentials (Tokens/Cookies) 
-- Ensure consistency with scripts that use this table name
CREATE TABLE IF NOT EXISTS platform_credentials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR(20) NOT NULL,
    credentials_type VARCHAR(50), -- 'cookies', 'oauth'
    credentials_data JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, platform)
);

-- 3. Upload History (Results & Logs)
CREATE TABLE IF NOT EXISTS upload_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clip_id UUID NOT NULL REFERENCES clips(id) ON DELETE CASCADE,
    platform VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'success', 'failed', 'pending'
    video_url TEXT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Update trigger for platform_credentials
CREATE TRIGGER update_platform_credentials_updated_at 
BEFORE UPDATE ON platform_credentials 
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
