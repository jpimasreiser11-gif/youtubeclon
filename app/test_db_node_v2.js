const { Pool } = require('pg');
require('dotenv').config();

const pool = new Pool({
    connectionString: process.env.DATABASE_URL || 'postgres://n8n:n8n@127.0.0.1:5432/antigravity'
});

async function main() {
    try {
        const res = await pool.query('SELECT current_database(), current_user');
        console.log('Connected to:', res.rows[0]);
        const projects = await pool.query('SELECT id, project_status, source_video_url, created_at FROM projects ORDER BY created_at DESC LIMIT 10');
        console.log('Recent Projects:', JSON.stringify(projects.rows, null, 2));
    } catch (err) {
        console.error('Connection Error:', err.message);
    }
    process.exit(0);
}
main();
