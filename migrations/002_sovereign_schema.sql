-- Sovereign Database Schema
-- Version: 2.0 (1:1 Opus Clip Fidelity)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Authentication Tables (NextAuth)
CREATE TABLE IF NOT EXISTS users (
  id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name          VARCHAR(255),
  email         VARCHAR(255) UNIQUE,
  emailVerified TIMESTAMP WITH TIME ZONE,
  image         TEXT,
  created_at    TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS accounts (
  id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  userId             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type               VARCHAR(255) NOT NULL,
  provider           VARCHAR(255) NOT NULL,
  providerAccountId  VARCHAR(255) NOT NULL,
  refresh_token      TEXT,
  access_token       TEXT,
  expires_at         BIGINT,
  token_type         VARCHAR(255),
  scope              VARCHAR(255),
  id_token           TEXT,
  session_state      VARCHAR(255),
  UNIQUE(provider, providerAccountId)
);

CREATE TABLE IF NOT EXISTS sessions (
  id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  sessionToken VARCHAR(255) UNIQUE NOT NULL,
  userId       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires      TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE IF NOT EXISTS verification_tokens (
  identifier VARCHAR(255) NOT NULL,
  token      VARCHAR(255) NOT NULL,
  expires    TIMESTAMP WITH TIME ZONE NOT NULL,
  PRIMARY KEY (identifier, token)
);

-- 2. Project & Video Tables
DO $$ BEGIN
    CREATE TYPE job_status AS ENUM ('QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS projects (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  source_video_url  TEXT NOT NULL,
  title             TEXT,
  thumbnail_url     TEXT,
  status            job_status DEFAULT 'QUEUED',
  progress          INT DEFAULT 0,
  estimated_time_remaining INT DEFAULT 0,
  created_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Clips & Intelligence
CREATE TABLE IF NOT EXISTS clips (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  start_time      REAL NOT NULL,
  end_time        REAL NOT NULL,
  virality_score  INT CHECK (virality_score BETWEEN 0 AND 100),
  transcript_json JSONB,
  video_path      TEXT, -- Base path for this clip's versions
  created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Thumbnail Management (Frame accurate)
CREATE TABLE IF NOT EXISTS thumbnails (
  id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  clip_id          UUID NOT NULL REFERENCES clips(id) ON DELETE CASCADE,
  url              TEXT NOT NULL,
  frame_timestamp  REAL,
  is_custom        BOOLEAN DEFAULT FALSE,
  created_at       TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Video Versioning (Original, Preview, Export)
DO $$ BEGIN
    CREATE TYPE version_type AS ENUM ('original', 'preview', 'export');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS video_versions (
  id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  clip_id    UUID NOT NULL REFERENCES clips(id) ON DELETE CASCADE,
  version    version_type NOT NULL,
  file_path  TEXT NOT NULL,
  status     job_status DEFAULT 'COMPLETED',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. High-Precision Editor Logic
CREATE TABLE IF NOT EXISTS clip_edits (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  clip_id         UUID NOT NULL REFERENCES clips(id) ON DELETE CASCADE,
  overlay_json    JSONB, -- Subtitle sync, caption positions, images
  subtitle_style  JSONB, -- Font, color, size, stroke
  zoom_data       JSONB, -- MediaPipe calculated coordinates
  updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_clip_edits_updated_at BEFORE UPDATE ON clip_edits FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
