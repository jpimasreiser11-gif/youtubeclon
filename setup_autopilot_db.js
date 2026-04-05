// Script to create autopilot_channels table
const { Pool } = require('pg');
require('dotenv').config({ path: 'app/.env' });

const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
});

async function run() {
    const client = await pool.connect();
    try {
        await client.query(`
      CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
      CREATE TABLE IF NOT EXISTS autopilot_channels (
          id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          user_id UUID REFERENCES users(id),
          channel_name VARCHAR(255),
          channel_id VARCHAR(255) NOT NULL,
          min_duration_minutes INT DEFAULT 10,
          ignore_shorts BOOLEAN DEFAULT true,
          is_active BOOLEAN DEFAULT true,
          last_video_processed VARCHAR(255),
          created_at TIMESTAMP DEFAULT NOW()
      );
    `);
        console.log("✅ Created autopilot_channels table successfully.");
    } catch (err) {
        console.error("❌ Error creating table:", err);
    } finally {
        client.release();
        pool.end();
    }
}

run();
