import { Pool } from 'pg';

// Use environment variables or default to local docker settings
const pool = new Pool({
    user: process.env.POSTGRES_USER || 'n8n',
    host: process.env.POSTGRES_HOST || 'localhost',
    database: process.env.POSTGRES_DB || 'antigravity',
    password: process.env.POSTGRES_PASSWORD || 'n8n',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
});

// Add error logging handler
pool.on('error', (err) => {
    console.error('Unexpected error on idle client', err);
});

export default pool;
