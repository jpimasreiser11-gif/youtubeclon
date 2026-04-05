import { Queue } from 'bullmq';
import { redisConnection } from './lib/queue';

const videoQueue = new Queue('video-processing', { connection: redisConnection });

async function resetJob() {
    const activeJobs = await videoQueue.getActive();
    for (const job of activeJobs) {
        console.log(`Active job: ${job.id}`);
        await job.moveToFailed(new Error('Manual reset'), 'token', false);
        await job.remove();
    }
    const stalledJobs = await videoQueue.getDelayed();
    for (const job of stalledJobs) {
        await job.remove();
    }
    console.log("Cleared queue");
    process.exit(0);
}

resetJob();
