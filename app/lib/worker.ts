import { Worker, Job } from 'bullmq';
import { redisConnection } from './queue';
import { spawn } from 'child_process';
import pool from './db';
import path from 'path';
import fs from 'fs';

export const videoWorker = new Worker(
    'video-processing',
    async (job: Job) => {
        const { projectId, url, enterpriseOptions, creationSystem, viralNiche, viralDryRun, motorBInput, motorBTrendMode } = job.data;
        console.log(`🚀 Starting job ${job.id} for project ${projectId} (URL: ${url})`);

        // BUG 3 FIX: Pre-flight check — ensure project exists in DB before doing any work.
        // This prevents ghost job ForeignKeyViolation cascades.
        const projectCheck = await pool.query(
            'SELECT id FROM projects WHERE id = $1',
            [projectId]
        );
        if (projectCheck.rows.length === 0) {
            const errMsg = `Ghost job detected: Project ${projectId} not found in DB. Discarding without retry.`;
            console.error(`❌ ${errMsg}`);
            // Throw with a specific flag so BullMQ doesn't retry this job
            const ghost = new Error(errMsg);
            (ghost as any).failParent = true;
            throw ghost;
        }

        // Mark project as PROCESSING
        await pool.query(
            'UPDATE projects SET project_status = $1, updated_at = NOW() WHERE id = $2',
            ['PROCESSING', projectId]
        );

        // Auto-detect virtual environment Python executable
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

        // Auto-detect ingest script location (legacy or bridge)
        const envUseViralSystem = ['1', 'true', 'yes', 'on'].includes((process.env.USE_VIRAL_SYSTEM || '').toLowerCase());
        const jobUseViralSystem = creationSystem && creationSystem !== 'legacy';
        const useViralSystem = envUseViralSystem || jobUseViralSystem;
        let scriptPath = path.join(process.cwd(), 'scripts', 'ingest.py');
        const bridgeCandidates = [
            path.join(process.cwd(), 'scripts', 'ingest_viral_bridge.py'),
            path.join(process.cwd(), 'app', 'scripts', 'ingest_viral_bridge.py'),
            path.join(process.cwd(), '..', 'app', 'scripts', 'ingest_viral_bridge.py'),
        ];
        const ingestCandidates = [
            path.join(process.cwd(), 'scripts', 'ingest.py'),
            path.join(process.cwd(), 'app', 'scripts', 'ingest.py'),
            path.join(process.cwd(), '..', 'app', 'scripts', 'ingest.py'),
        ];
        const possibleScriptPaths = useViralSystem ? [...bridgeCandidates, ...ingestCandidates] : ingestCandidates;
        for (const p of possibleScriptPaths) {
            if (fs.existsSync(p)) { scriptPath = p; break; }
        }

        return new Promise((resolve, reject) => {
            const args = [scriptPath, projectId.toString(), url];

            if (useViralSystem) {
                const modeMap: Record<string, string> = {
                    viral_auto: 'auto',
                    viral_motor_a: 'motor_a',
                    viral_motor_b: 'motor_b',
                };
                const selectedMode = modeMap[creationSystem] || process.env.VIRAL_PIPELINE_MODE || 'auto';
                const selectedNiche = viralNiche || process.env.VIRAL_NICHE || 'finanzas personales';
                const dryRunValue = (viralDryRun ?? ['1', 'true', 'yes', 'on'].includes((process.env.VIRAL_PIPELINE_DRY_RUN || '1').toLowerCase())) ? '1' : '0';

                args.push('--pipeline-mode', selectedMode);
                args.push('--pipeline-niche', selectedNiche);
                args.push('--pipeline-dry-run', dryRunValue);

                if (creationSystem === 'viral_motor_b' && motorBInput) {
                    const encoded = Buffer.from(JSON.stringify(motorBInput), 'utf-8').toString('base64');
                    args.push('--pipeline-input-b64', encoded);
                    args.push('--pipeline-trend-mode', motorBTrendMode || 'internet');
                }
            }

            if (enterpriseOptions?.audioPro) args.push('--audio-pro');
            if (enterpriseOptions?.smartReframe) args.push('--smart-reframe');
            if (enterpriseOptions?.cleanSpeech) args.push('--clean-speech');
            if (enterpriseOptions?.bRoll) args.push('--b-roll');

            console.log(`[worker] useViralSystem=${useViralSystem} script=${scriptPath}`);
            console.log(`🐍 Running: ${pythonPath} ${args.join(' ')}`);
            const pythonProcess = spawn(pythonPath, args);

            let output = '';
            let errorOutput = '';

            pythonProcess.stdout.on('data', (data) => {
                const line = data.toString();
                output += line;
                console.log(`[Python] ${line.trim()}`);
            });

            pythonProcess.stderr.on('data', (data) => {
                errorOutput += data.toString();
                console.error(`[Python Log] ${data.toString().trim()}`);
            });

            pythonProcess.on('close', async (code) => {
                clearTimeout(timeoutHandle);
                if (code === 0) {
                    console.log(`✅ Job ${job.id} completed successfully`);
                    await pool.query(
                        'UPDATE projects SET project_status = $1, updated_at = NOW() WHERE id = $2',
                        ['COMPLETED', projectId]
                    );
                    resolve({ projectId, status: 'COMPLETED' });
                } else {
                    console.error(`❌ Job ${job.id} failed with exit code ${code}`);
                    await pool.query(
                        'UPDATE projects SET project_status = $1, updated_at = NOW() WHERE id = $2',
                        ['FAILED', projectId]
                    );
                    reject(new Error(`Python process failed with code ${code}: ${errorOutput.slice(-500)}`));
                }
            });

            pythonProcess.on('error', async (err) => {
                clearTimeout(timeoutHandle);
                console.error(`❌ Failed to start Python process: ${err.message}`);
                await pool.query(
                    'UPDATE projects SET project_status = $1, updated_at = NOW() WHERE id = $2',
                    ['FAILED', projectId]
                );
                reject(err);
            });

            // Safety timeout: if Python hangs for >3h, mark as FAILED and kill
            const timeoutHandle = setTimeout(async () => {
                console.error(`⏰ Job ${job.id} timed out after 3h, killing process`);
                pythonProcess.kill('SIGKILL');
                await pool.query(
                    'UPDATE projects SET project_status = $1, updated_at = NOW() WHERE id = $2',
                    ['FAILED', projectId]
                );
                reject(new Error('Job timed out after 3 hours'));
            }, 3 * 60 * 60 * 1000);
        });
    },
    {
        connection: redisConnection,
        concurrency: 1,
    }
);

// Log failed jobs
videoWorker.on('failed', (job, err) => {
    console.error(`🚨 Job ${job?.id} FAILED in queue: ${err.message}`);
});

videoWorker.on('completed', (job) => {
    console.log(`🎉 Job ${job?.id} COMPLETED successfully`);
});
