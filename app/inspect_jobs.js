const Redis = require('ioredis');
const redis = new Redis();

async function main() {
    const activeJobs = await redis.lrange('bull:video-processing:active', 0, -1);
    console.log('Active Jobs:', activeJobs);
    
    for (const jobKey of activeJobs) {
        const jobData = await redis.hgetall(ull:video-processing:);
        console.log(Job  data:, jobData.data);
    }
    
    const waitJobs = await redis.lrange('bull:video-processing:wait', 0, -1);
    console.log('Wait Jobs:', waitJobs);
    for (const jobKey of waitJobs) {
        const jobData = await redis.hgetall(ull:video-processing:);
        console.log(Job  data:, jobData.data);
    }
    
    redis.quit();
}
main();
