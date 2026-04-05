const { Pool } = require('pg');
const pool = new Pool({
    user: 'n8n', host: 'localhost', database: 'antigravity', password: 'n8n', port: 5432
});

async function run() {
    const projectId = 'ad355c8b-e0d4-444e-3bb7-64b5648bd0c99';
    try {
        console.log('Testing update...');
        await pool.query(
            "UPDATE projects SET status = $1, progress = $2, estimated_time_remaining = $3 WHERE id = $4",
            ['PROCESSING', 15, 12, projectId]
        );
        console.log('Update successful!');
    } catch (err) {
        console.error('Update failed:', err.message);
    } finally {
        await pool.end();
    }
}
run();
