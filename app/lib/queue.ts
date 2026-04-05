import { Queue } from 'bullmq';

// Create queues lazily to avoid establishing Redis connections at module import time
// which can break Next.js prerender/build when Redis isn't available locally.
const redisOptions = {
    host: process.env.REDIS_HOST || '127.0.0.1',
    port: parseInt(process.env.REDIS_PORT || '6379'),
    maxRetriesPerRequest: null as null,
    enableAutoPipelining: false,
    retryStrategy: (times: number) => {
        if (times > 30) return null;
        return Math.min(times * 1000, 5000);
    },
};

export const redisConnection = redisOptions;

let _videoQueue: Queue | null = null;
let _autopilotQueue: Queue | null = null;
let _schedulerQueue: Queue | null = null;

export function getVideoQueue() {
    if (_videoQueue) return _videoQueue;
    _videoQueue = new Queue('video-processing', {
        connection: redisOptions,
        defaultJobOptions: {
            attempts: 3,
            backoff: { type: 'exponential', delay: 5000 },
            removeOnComplete: true,
            removeOnFail: false,
        },
    });
    return _videoQueue;
}

export function getAutopilotQueue() {
    if (_autopilotQueue) return _autopilotQueue;
    _autopilotQueue = new Queue('autopilot-processing', {
        connection: redisOptions,
        defaultJobOptions: { removeOnComplete: true, removeOnFail: true },
    });
    return _autopilotQueue;
}

export function getSchedulerQueue() {
    if (_schedulerQueue) return _schedulerQueue;
    _schedulerQueue = new Queue('scheduler-processing', {
        connection: redisOptions,
        defaultJobOptions: { removeOnComplete: true, removeOnFail: true },
    });
    return _schedulerQueue;
}

export const setupRepeatableJobs = async () => {
    const autopilot = getAutopilotQueue();
    const scheduler = getSchedulerQueue();

    await autopilot.add('run-orchestrator', {}, {
        repeat: { every: 3600000 },
        jobId: 'orchestrator-job',
    });

    await scheduler.add('run-scheduler', {}, {
        repeat: { every: 300000 },
        jobId: 'scheduler-job',
    });

    await scheduler.add('run-cleanup', {}, {
        repeat: { every: 86400000 },
        jobId: 'cleanup-job',
    });
};

