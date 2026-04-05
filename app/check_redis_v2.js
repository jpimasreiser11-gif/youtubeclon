const Redis = require('ioredis');
const redis = new Redis();
async function main() {
    const jobs = await redis.keys('bull:video-processing:*');
    console.log('Redis Keys:', jobs);
    const active = await redis.lrange('bull:video-processing:active', 0, -1);
    console.log('Active Jobs:', active);
    const wait = await redis.lrange('bull:video-processing:wait', 0, -1);
    console.log('Wait Jobs:', wait);
    process.exit(0);
}
main();
