import { Queue } from 'bullmq';
import { redisConnection } from './lib/queue';

const videoQueue = new Queue('video-processing', { connection: redisConnection });

async function trigger() {
    await videoQueue.add('video-process', {
        projectId: 'f4ca43dd-6928-43e6-93bf-b2fdba88fdce',
        url: 'https://youtu.be/95oYTSICA30', // Removed si token just in case
        enterpriseOptions: {
            audioPro: false,
            smartReframe: false,
            cleanSpeech: false,
            bRoll: true
        }
    }, {
        jobId: `video_f4ca43dd-6928-43e6-93bf-b2fdba88fdce`,
        attempts: 1
    });
    console.log("Job f4ca43dd-6928-43e6-93bf-b2fdba88fdce queued.");
    process.exit(0);
}

trigger();
