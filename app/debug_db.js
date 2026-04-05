const { Pool } = require('pg');
require('dotenv').config({ path: '.env' });

console.log('DB_URL:', process.env.DATABASE_URL);

const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

async function main() {
  try {
    const res = await pool.query('SELECT count(*) FROM projects');
    console.log('Total counts:', res.rows[0]);
    
    const active = await pool.query("SELECT id, project_status, progress_percent, current_step FROM projects WHERE id = '430192c1-36bf-41b4-a11c-22a42314e3a1'");
    console.log('Specific Job:', active.rows[0] || 'NOT FOUND');
    
    const latest = await pool.query('SELECT id, project_status, created_at FROM projects ORDER BY created_at DESC LIMIT 5');
    console.log('Latest IDs:', latest.rows.map(r => r.id));
  } catch (err) {
    console.error('CRITICAL DB ERROR:', err.message);
  } finally {
    await pool.end();
  }
}
main();
