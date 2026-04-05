const { Pool } = require('pg');
const fs = require('fs');
const pool = new Pool({ connectionString: 'postgres://n8n:n8n@127.0.0.1:5432/antigravity' });
pool.query("SELECT id, project_status, error_log FROM projects WHERE project_status = 'FAILED' ORDER BY created_at DESC LIMIT 1").then(res => {
    fs.writeFileSync('latest_failed.json', JSON.stringify(res.rows, null, 2));
    process.exit(0);
}).catch(console.error);
