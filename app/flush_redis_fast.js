const Redis = require('ioredis');
const redis = new Redis();
redis.flushall().then(() => {
    console.log('Redis Flushed');
    process.exit(0);
});
