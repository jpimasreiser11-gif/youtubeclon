const { Pool } = require('pg');
const pool = new Pool({
    user: 'n8n',
    host: 'localhost',
    database: 'antigravity',
    password: 'n8n',
    port: 5432
});

async function run() {
    try {
        const userRes = await pool.query("INSERT INTO users (email, name) VALUES ('test@example.com', 'Test User') ON CONFLICT (email) DO UPDATE SET email=EXCLUDED.email RETURNING id");
        const userId = userRes.rows[0].id;
        const projRes = await pool.query("INSERT INTO projects (user_id, source_video_url, status) VALUES ($1, 'https://www.youtube.com/watch?v=aqz-KE-bpKQ', 'QUEUED') RETURNING id", [userId]);
        console.log('PROJECT_ID:' + projRes.rows[0].id);
    } catch (err) {
        console.error(err);
    } finally {
        await pool.end();
    }
}
run();
