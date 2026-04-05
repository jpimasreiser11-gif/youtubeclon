const { spawn } = require('child_process');
const fs = require('fs');
const log = fs.createWriteStream('worker_direct.log');
const worker = spawn('node', ['node_modules/tsx/dist/cli.mjs', 'scripts/run-worker.ts'], {
    cwd: 'c:/Users/jpima/Downloads/edumind---ai-learning-guide/app',
    env: process.env
});
worker.stdout.pipe(log);
worker.stderr.pipe(log);
console.log('Worker spawned with PID:', worker.pid);
