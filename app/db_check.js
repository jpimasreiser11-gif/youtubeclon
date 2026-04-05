const { Pool } = require('pg');

const pool = new Pool({
    user: process.env.POSTGRES_USER || 'n8n',
    host: process.env.POSTGRES_HOST || 'localhost',
    database: process.env.POSTGRES_DB || 'antigravity',
    password: process.env.POSTGRES_PASSWORD || 'n8n',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
});

async function run() {
    try {
        const res = await pool.query("SELECT column_name FROM information_schema.columns WHERE table_name = 'projects'");
        console.log('---BEGIN_COLUMNS---');
        res.rows.forEach(r => console.log(r.column_name));
        console.log('---END_COLUMNS---');
        process.exit(0);
    } catch (err) {
        console.error('FAIL:' + err.message);
        process.exit(1);
    }
}

run();
