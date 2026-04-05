const { Pool } = require('pg');

const pool = new Pool({
    connectionString: process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:5432/edumind'
});

async function migrate() {
    const client = await pool.connect();
    try {
        console.log('Starting migration...');
        await client.query(`
      ALTER TABLE jobs ADD COLUMN IF NOT EXISTS estimated_time_remaining INT DEFAULT 0;
      ALTER TABLE jobs ADD COLUMN IF NOT EXISTS thumbnail_url TEXT;
      ALTER TABLE jobs ADD COLUMN IF NOT EXISTS title TEXT;
    `);
        console.log('Migration successful: jobs table updated.');
    } catch (err) {
        console.error('Migration failed:', err);
    } finally {
        client.release();
        await pool.end();
    }
}

migrate();
