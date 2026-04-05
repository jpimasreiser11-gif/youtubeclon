import pool from './lib/db';
import * as fs from 'fs';

async function listColumns() {
    try {
        const result = await pool.query(
            "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'projects'"
        );
        const output = JSON.stringify(result.rows, null, 2);
        fs.writeFileSync('db_schema_debug.json', output);
        console.log('Schema written to db_schema_debug.json');
        process.exit(0);
    } catch (err) {
        console.error('Failed to list columns:', err);
        process.exit(1);
    }
}

listColumns();
