import { videoWorker } from '../lib/worker';
import { setupRepeatableJobs, redisConnection, getVideoQueue } from '../lib/queue';
import { Worker } from 'bullmq';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import pool from '../lib/db';

console.log('--------------------------------------------------');
console.log('🤖 ENTERPRISE VIDEO WORKER STARTING');
console.log('Redis: ' + (process.env.REDIS_URL || 'redis://localhost:6379'));
console.log('DB:    ' + (process.env.POSTGRES_HOST || 'localhost') + ':' + (process.env.POSTGRES_PORT || '5432'));
console.log('Status: Listening for jobs...');
console.log('--------------------------------------------------');

const requeueOrphanQueuedProjects = async () => {
    try {
        const queue = getVideoQueue();
        const { rows } = await pool.query(
            `SELECT id, source_video_url
             FROM projects
             WHERE project_status = 'QUEUED'
             ORDER BY created_at ASC
             LIMIT 100`
        );

        let recovered = 0;
        for (const project of rows) {
            const projectId = String(project.id);
            const jobId = `video_${projectId}`;
            const existingJob = await queue.getJob(jobId);
            if (existingJob) continue;

            const sourceUrl = String(project.source_video_url || '').trim();
            const isFromScratch = sourceUrl.startsWith('motorb://from-scratch/');

            await queue.add(
                'process-video',
                {
                    projectId,
                    url: sourceUrl || `motorb://from-scratch/recovered/${Date.now()}`,
                    enterpriseOptions: {},
                    creationSystem: isFromScratch ? 'viral_motor_b' : 'legacy',
                    viralNiche: 'finanzas personales',
                    viralDryRun: isFromScratch ? false : true,
                },
                { jobId }
            );
            recovered += 1;
        }

        if (recovered > 0) {
            console.log(`[Recovery] Re-enqueued ${recovered} QUEUED project(s) missing in BullMQ.`);
        }
    } catch (err: any) {
        console.error('[Recovery] Failed to re-enqueue orphan QUEUED projects:', err?.message || err);
    }
};

// BUG 6 FIX: Prevent silent crashes. Log all uncaught errors instead of dying silently.
process.on('uncaughtException', (err) => {
    console.error('🔴 UNCAUGHT EXCEPTION (worker will continue):', err.message);
    console.error(err.stack);
    // Don't exit — let the worker keep running for the next job
});

process.on('unhandledRejection', (reason) => {
    console.error('🔴 UNHANDLED REJECTION (worker will continue):', reason);
    // Don't exit — let the worker keep running
});

// Graceful shutdown on CTRL+C
process.on('SIGINT', async () => {
    console.log('\n⏸  Gracefully shutting down worker...');
    await videoWorker.close();
    process.exit(0);
});

process.on('SIGTERM', async () => {
    console.log('\n⏸  Worker received SIGTERM, shutting down...');
    await videoWorker.close();
    process.exit(0);
});

// Launch the python scheduler periodically
const runScheduler = async () => {
    const isWin = process.platform === 'win32';
    let pythonPath = 'python';

    // Use the exact venv logic seen in worker for path resolution
    const possibleVenvPaths = [
        path.join(process.cwd(), 'venv_sovereign', isWin ? 'Scripts' : 'bin', isWin ? 'python.exe' : 'python'),
        path.join(process.cwd(), '..', 'venv_sovereign', isWin ? 'Scripts' : 'bin', isWin ? 'python.exe' : 'python'),
        path.join(process.cwd(), 'venv', isWin ? 'Scripts' : 'bin', isWin ? 'python.exe' : 'python'),
    ];

    for (const p of possibleVenvPaths) {
        if (fs.existsSync(p)) { pythonPath = p; break; }
    }

    let scriptPath = path.join(process.cwd(), 'scripts', 'upload_scheduler.py');
    const possiblePaths = [
        path.join(process.cwd(), 'scripts', 'upload_scheduler.py'),
        path.join(process.cwd(), '..', 'scripts', 'upload_scheduler.py')
    ];
    for (const p of possiblePaths) {
        if (fs.existsSync(p)) { scriptPath = p; break; }
    }

    if (!fs.existsSync(scriptPath)) {
        console.error(`[Scheduler] Could not find upload_scheduler.py at ${scriptPath}`);
        return;
    }

    const schedulerProcess = spawn(pythonPath, [
        scriptPath,
        '--db-host', process.env.POSTGRES_HOST || 'localhost',
        '--db-name', process.env.POSTGRES_DB || 'antigravity',
        '--db-user', process.env.POSTGRES_USER || 'n8n',
        '--db-password', process.env.POSTGRES_PASSWORD || 'n8n'
    ]);

    schedulerProcess.stdout.on('data', (data) => {
        const str = data.toString().trim();
        if (str) console.log(`[Scheduler] ${str}`);
    });

    schedulerProcess.stderr.on('data', (data) => {
        const str = data.toString().trim();
        if (str) console.error(`[Scheduler Error] ${str}`);
    });
};

// Launch the python orchestrator periodically to schedule new videos
const runOrchestrator = async () => {
    const isWin = process.platform === 'win32';
    let pythonPath = 'python';

    const possibleVenvPaths = [
        path.join(process.cwd(), 'venv_sovereign', isWin ? 'Scripts' : 'bin', isWin ? 'python.exe' : 'python'),
        path.join(process.cwd(), '..', 'venv_sovereign', isWin ? 'Scripts' : 'bin', isWin ? 'python.exe' : 'python'),
        path.join(process.cwd(), 'venv', isWin ? 'Scripts' : 'bin', isWin ? 'python.exe' : 'python'),
    ];

    for (const p of possibleVenvPaths) {
        if (fs.existsSync(p)) { pythonPath = p; break; }
    }

    let scriptPath = path.join(process.cwd(), 'scripts', 'automation_orchestrator.py');
    const possiblePaths = [
        path.join(process.cwd(), 'scripts', 'automation_orchestrator.py'),
        path.join(process.cwd(), '..', 'scripts', 'automation_orchestrator.py')
    ];
    for (const p of possiblePaths) {
        if (fs.existsSync(p)) { scriptPath = p; break; }
    }

    if (!fs.existsSync(scriptPath)) {
        console.error(`[Orchestrator] Could not find automation_orchestrator.py at ${scriptPath}`);
        return;
    }

    console.log(`[Orchestrator] Running: ${pythonPath} ${path.basename(scriptPath)}`);
    const orchestratorProcess = spawn(pythonPath, [
        scriptPath
    ]);

    orchestratorProcess.stdout.on('data', (data) => {
        const str = data.toString().trim();
        if (str) console.log(`[Orchestrator] ${str}`);
    });

    orchestratorProcess.stderr.on('data', (data) => {
        const str = data.toString().trim();
        if (str) console.error(`[Orchestrator Error] ${str}`);
    });
};

// Launch the python cleanup script to free up disk space
const runCleanup = async () => {
    const isWin = process.platform === 'win32';
    let pythonPath = 'python';

    const possibleVenvPaths = [
        path.join(process.cwd(), 'venv_sovereign', isWin ? 'Scripts' : 'bin', isWin ? 'python.exe' : 'python'),
        path.join(process.cwd(), '..', 'venv_sovereign', isWin ? 'Scripts' : 'bin', isWin ? 'python.exe' : 'python'),
        path.join(process.cwd(), 'venv', isWin ? 'Scripts' : 'bin', isWin ? 'python.exe' : 'python'),
    ];

    for (const p of possibleVenvPaths) {
        if (fs.existsSync(p)) { pythonPath = p; break; }
    }

    let scriptPath = path.join(process.cwd(), 'scripts', 'cleanup_storage.py');
    const possiblePaths = [
        path.join(process.cwd(), 'scripts', 'cleanup_storage.py'),
        path.join(process.cwd(), '..', 'scripts', 'cleanup_storage.py'),
        path.join(process.cwd(), 'app', 'scripts', 'cleanup_storage.py')
    ];
    for (const p of possiblePaths) {
        if (fs.existsSync(p)) { scriptPath = p; break; }
    }

    if (!fs.existsSync(scriptPath)) {
        console.error(`[Cleanup] Could not find cleanup_storage.py at ${scriptPath}`);
        return;
    }

    console.log(`[Cleanup] Running: ${pythonPath} ${path.basename(scriptPath)}`);
    const cleanupProcess = spawn(pythonPath, [scriptPath]);

    cleanupProcess.stdout.on('data', (data) => {
        const str = data.toString().trim();
        if (str) console.log(`[Cleanup] ${str}`);
    });

    cleanupProcess.stderr.on('data', (data) => {
        const str = data.toString().trim();
        if (str) console.error(`[Cleanup Error] ${str}`);
    });
};

// Create Workers for Repeatable Jobs
const autopilotWorker = new Worker('autopilot-processing', async (job) => {
    if (job.name === 'run-orchestrator') {
        runOrchestrator();
    }
}, { connection: redisConnection, concurrency: 1 });

const schedulerWorker = new Worker('scheduler-processing', async (job) => {
    if (job.name === 'run-scheduler') {
        runScheduler();
    } else if (job.name === 'run-cleanup') {
        runCleanup();
    }
}, { connection: redisConnection, concurrency: 1 });


// Start loops
setupRepeatableJobs().then(() => {
    console.log('[System] Repeatable jobs registered with BullMQ.');
}).catch(err => {
    console.error('[System Error] Failed to set up repeatable jobs', err);
});

// Heal QUEUED rows if Redis was flushed/restarted and jobs disappeared from BullMQ.
requeueOrphanQueuedProjects();
setInterval(requeueOrphanQueuedProjects, 60 * 1000);
