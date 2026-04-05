import { Queue, Worker, Job } from 'bullmq';
import Redis from 'ioredis';
import { Pool } from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const connection = new Redis();
const pool = new Pool({
    connectionString: process.env.DATABASE_URL
});

async function main() {
    try {
        const activeJobs = await connection.lrange('bull:video-processing:active', 0, -1);
        console.log('Active Job Keys:', activeJobs);

        for (const jobId of activeJobs) {
            const jobDataStr = await connection.hget('bull:video-processing:' + jobId, 'data');
            if (jobDataStr) {
                const jobData = JSON.parse(jobDataStr);
                console.log('Job Data for ' + jobId + ':', JSON.stringify(jobData, null, 2));
                
                const projectId = jobData.projectId;
                if (projectId) {
                    const res = await pool.query('SELECT * FROM projects WHERE id = ', [projectId]);
                    if (res.rows.length === 0) {
                        console.log('CRITICAL: Project ' + projectId + ' FOUND IN REDIS BUT MISSING IN DB');
                    } else {
                        console.log('Project ' + projectId + ' found in DB. Status: ' + res.rows[0].project_status);
                    }
                }
            }
        }
    } catch (err) {
        console.error('Error:', err);
    }
    process.exit(0);
}
main();
