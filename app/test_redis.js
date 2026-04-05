const Redis = require('ioredis');
const redis = new Redis();

async function main() {
    console.log('Active:', await redis.lrange('bull:video-processing:active', 0, -1));
    console.log('Wait:', await redis.lrange('bull:video-processing:wait', 0, -1));
    console.log('Delayed:', await redis.zrange('bull:video-processing:delayed', 0, -1));
    console.log('Completed:', await redis.zrange('bull:video-processing:completed', 0, -1));
    console.log('Failed:', await redis.zrange('bull:video-processing:failed', 0, -1));
    redis.quit();
}
main();
