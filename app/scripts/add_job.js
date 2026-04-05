#!/usr/bin/env node
const { Queue } = require('bullmq');

const args = process.argv.slice(2);
if (args.length < 2) {
  console.error('Usage: node add_job.js <projectId> <url>');
  process.exit(1);
}
const projectId = args[0];
const url = args[1];

const redisHost = process.env.REDIS_HOST || '127.0.0.1';
const redisPort = parseInt(process.env.REDIS_PORT || '6379', 10);

const q = new Queue('video-processing', {
  connection: {
    host: redisHost,
    port: redisPort,
    maxRetriesPerRequest: null,
    enableAutoPipelining: false,
  },
});

(async () => {
  try {
    const job = await q.add(
      'process-video',
      { projectId, url, enterpriseOptions: {} },
      { jobId: `video_${projectId}` }
    );
    console.log('Added job:', job.id);
    await q.close();
    process.exit(0);
  } catch (err) {
    console.error('Failed to add job:', err);
    process.exit(1);
  }
})();
