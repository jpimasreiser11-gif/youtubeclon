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
        console.log('--- RELATIONS (public) ---');
        const rels = await pool.query("SELECT relname, relkind FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'public'");
        console.log(JSON.stringify(rels.rows, null, 2));

        console.log('--- PROJECTS ---');
        const res = await pool.query('SELECT id, status, progress, user_id FROM projects');
        console.log(res.rows);
        if (res.rows.length > 0) {
            console.log('First Project ID Length:', res.rows[0].id.length);
        }

        console.log('\n--- ATTEMPT: SELECT * FROM jobs ---');
        try {
            const jobs = await pool.query('SELECT * FROM jobs LIMIT 1');
            console.log('Jobs table exists and is accessible');
        } catch (e) {
            console.log('Jobs table check failed: ' + e.message);
        }
        try {
            const connTest = await pool.query('SELECT 1 FROM projects LIMIT 1');
            console.log('Connectivity OK');
        } catch (e) {
            console.error('Connectivity failed: ' + e.message);
            return; // Stop if projects table query fails
        }

        console.log('\n--- PROJECTS ---');
        const projects = await pool.query('SELECT * FROM projects');
        console.log(JSON.stringify(projects.rows, null, 2));

        console.log('\n--- CLIPS ---');
        const clips = await pool.query('SELECT id, project_id, virality_score, start_time, end_time FROM clips');
        console.log(JSON.stringify(clips.rows, null, 2));

        console.log('\n--- THUMBNAILS ---');
        const thumbs = await pool.query('SELECT * FROM thumbnails');
        console.log(JSON.stringify(thumbs.rows, null, 2));

    } catch (err) {
        console.error(err);
    } finally {
        await pool.end();
    }
}
run();
