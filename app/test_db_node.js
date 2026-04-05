const { Pool } = require('pg');
require('dotenv').config({ path: '.env' });

const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

async function main() {
  try {
    const res = await pool.query('SELECT id, project_status, created_at FROM projects ORDER BY created_at DESC LIMIT 10');
    console.log('Recent Projects:', res.rows);
  } catch (err) {
    console.error('DB Error:', err.message);
  } finally {
    await pool.end();
  }
}
main();
