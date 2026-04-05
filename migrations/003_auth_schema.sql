-- NextAuth Schema for PostgreSQL
-- Based on standard @auth/pg-adapter schema using UUIDs

CREATE TABLE IF NOT EXISTS accounts
(
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  "userId" UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type TEXT NOT NULL,
  provider TEXT NOT NULL,
  "providerAccountId" TEXT NOT NULL,
  refresh_token TEXT,
  access_token TEXT,
  expires_at BIGINT,
  id_token TEXT,
  scope TEXT,
  session_state TEXT,
  token_type TEXT,
 
  CONSTRAINT provider_account_unique UNIQUE(provider, "providerAccountId")
);
 
CREATE TABLE IF NOT EXISTS sessions
(
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  "userId" UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires TIMESTAMPTZ NOT NULL,
  "sessionToken" TEXT NOT NULL,
 
  CONSTRAINT session_token_unique UNIQUE("sessionToken")
);
 
CREATE TABLE IF NOT EXISTS verification_token
(
  identifier TEXT NOT NULL,
  expires TIMESTAMPTZ NOT NULL,
  token TEXT NOT NULL,
 
  PRIMARY KEY (identifier, token)
);

-- Ensure users table has correct columns if they don't exist (idempotent checks)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='emailVerified') THEN
        -- It might exist as emailverified (lowercase), if so, we might need to rely on that or rename.
        -- If strictly missing, add it.
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='emailverified') THEN
             ALTER TABLE users ADD COLUMN "emailVerified" TIMESTAMPTZ;
        END IF;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='image') THEN
        ALTER TABLE users ADD COLUMN image TEXT;
    END IF;
END
$$;
