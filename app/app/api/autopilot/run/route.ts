import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import pool from '@/lib/db';
import { getVideoQueue } from '@/lib/queue';

const execAsync = promisify(exec);

// Autopilot CRON / Polling Route (Protected)
export async function GET(request: Request) {
    const authHeader = request.headers.get('authorization');

    // Security measure so random bots cannot flood YouTube via our server
    if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
        return new NextResponse('Unauthorized', { status: 401 });
    }

    const client = await pool.connect();

    try {
        // Fetch all active channels
        const res = await client.query("SELECT * FROM autopilot_channels WHERE is_active = true");
        const channels = res.rows;

        if (channels.length === 0) {
            return NextResponse.json({ message: "No active channels to monitor." });
        }

        let queuedCount = 0;
        const results = [];

        const path = require('path');
        const fs = require('fs');
        const appDir = process.cwd();
        const projectRoot = path.join(appDir, '..');

        let pythonPath = path.join(projectRoot, 'venv_sovereign', 'Scripts', 'python.exe');
        if (!fs.existsSync(pythonPath)) {
            pythonPath = 'python';
        }

        const scriptPath = path.join(projectRoot, 'scripts', 'full_autopilot.py');
        const dbPassword = process.env.POSTGRES_PASSWORD || 'postgres';

        for (const channel of channels) {
            const cmd = `"${pythonPath}" "${scriptPath}" --channel-id "${channel.channel_id}" --db-password "${dbPassword}"`;
            try {
                const { stdout } = await execAsync(cmd);

                // The python script will print some debug, but the last line is the JSON result
                const lines = stdout.trim().split('\n');
                const jsonResp = lines[lines.length - 1];
                const parsed = JSON.parse(jsonResp);

                results.push({ channel: channel.channel_name, ...parsed });

                if (parsed.success && parsed.action === 'queued') {
                    // We have a new video! We need to add it to our DB and BullMQ.
                    const insertRes = await client.query(
                        `INSERT INTO projects (user_id, source_video_url, project_status, title) 
                            VALUES ($1, $2, 'PENDING_AUTOPILOT', $3) RETURNING id`,
                        [channel.user_id, parsed.url, `[Autopilot] ${parsed.video_id}`]
                    );
                    const projectId = insertRes.rows[0].id;

                    // Staggering (Pacing): Delay each queued job by 2 hours progressively
                    // to prevent killing the PC if 10 channels uploaded today
                    const delayMs = queuedCount * (2 * 60 * 60 * 1000);

                    const q = getVideoQueue();
                    await q.add('process-video', {
                        projectId: projectId,
                        url: parsed.url,
                        userId: channel.user_id,
                        autopilot: true
                    }, { delay: delayMs });

                    queuedCount++;
                }

            } catch (scriptErr: any) {
                console.error(`Autopilot error for ${channel.channel_name}:`, scriptErr);
                results.push({ channel: channel.channel_name, error: scriptErr.message });
            }
        }

        return NextResponse.json({
            success: true,
            queued_jobs: queuedCount,
            details: results
        });

    } catch (error) {
        console.error('Error running autopilot cron:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    } finally {
        client.release();
    }
}

