const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');

const pool = new Pool({
    user: 'n8n',
    host: 'localhost',
    database: 'antigravity',
    password: 'n8n',
    port: 5432
});

async function run() {
    try {
        const sqlPath = path.join(__dirname, '..', 'migrations', '002_sovereign_schema.sql');
        const sql = fs.readFileSync(sqlPath, 'utf8');

        console.log('Running migration...');
        await pool.query(sql);
        console.log('Migration successful!');
    } catch (err) {
        console.error('Migration failed:', err);
    } finally {
        await pool.end();
    }
}
run();
