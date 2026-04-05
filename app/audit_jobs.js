const Redis = require('ioredis');
const { Pool } = require('pg');
require('dotenv').config();

const connection = new Redis();
const pool = new Pool({
    connectionString: process.env.DATABASE_URL
});

async function main() {
    try {
        console.log('Connecting to Redis...');
        const keys = await connection.keys('bull:video-processing:*');
        console.log('Redis Keys found:', keys.length);

        const activeJobs = await connection.lrange('bull:video-processing:active', 0, -1);
        console.log('Active Jobs count:', activeJobs.length);

        for (const jobId of activeJobs) {
            console.log('Inspecting active job:', jobId);
            const jobDataStr = await connection.hget('bull:video-processing:' + jobId, 'data');
            if (jobDataStr) {
                const jobData = JSON.parse(jobDataStr);
                console.log('Job ' + jobId + ' Payload:', JSON.stringify(jobData, null, 2));
                
                const projectId = jobData.projectId;
                if (projectId) {
                    const res = await pool.query('SELECT id, project_status FROM projects WHERE id = ', [projectId]);
                    if (res.rows.length === 0) {
                        console.log('ERROR: Project ' + projectId + ' NOT FOUND IN DB');
                    } else {
                        console.log('Project ' + projectId + ' status in DB:', res.rows[0].project_status);
                    }
                }
            }
        }
    } catch (err) {
        console.error('Job Audit Error:', err);
    }
    process.exit(0);
}
main();
