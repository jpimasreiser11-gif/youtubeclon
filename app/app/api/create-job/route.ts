import { NextResponse } from 'next/server';
import pool from '@/lib/db';
import { auth } from "@/auth";
import path from 'path';
import fs from 'fs';

export async function POST(request: Request) {
    const session = await auth();

    if (!session || !session.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const userId = session.user.id;

    try {
        // Parse request body
        let body: {
            url?: string;
            enterpriseOptions?: any;
            creationSystem?: 'legacy' | 'viral_auto' | 'viral_motor_a' | 'viral_motor_b';
            viralNiche?: string;
            viralDryRun?: boolean;
            motorBInput?: {
                tema?: string;
                hook?: string;
                angulo?: string;
                nicho?: string;
                palabras_clave?: string[];
                prebuilt_script?: any;
            };
            motorBTrendMode?: 'internet' | 'manual-only';
        };
        try {
            body = await request.json();
        } catch (jsonError: any) {
            return NextResponse.json({
                error: 'Invalid JSON format',
                details: jsonError.message,
            }, { status: 400 });
        }

        const normalizedCreationSystem = body.creationSystem === 'viral_motor_b' ? 'viral_motor_b' : 'viral_motor_a';
        const isFromScratchMode = normalizedCreationSystem === 'viral_motor_b';
        const normalizedUrl = (body.url || '').trim();
        if (!normalizedUrl && !isFromScratchMode) {
            return NextResponse.json({ error: 'URL is required' }, { status: 400 });
        }

        // Motor B can create videos from scratch without a source URL.
        const sourceUrl = normalizedUrl || `motorb://from-scratch/${Date.now()}`;

        console.log(`[create-job] Creating project for URL: ${sourceUrl}`);

        // Fetch YouTube metadata (thumbnail / title) before inserting — non-blocking
        let thumbnail_url: string | null = null;
        let video_title: string | null = null;

        const isWin = process.platform === 'win32';
        let pythonPath = 'python';
        const possibleVenvPaths = [
            path.join(process.cwd(), 'venv_sovereign', isWin ? 'Scripts' : 'bin', isWin ? 'python.exe' : 'python'),
            path.join(process.cwd(), '..', 'venv_sovereign', isWin ? 'Scripts' : 'bin', isWin ? 'python.exe' : 'python'),
        ];
        for (const p of possibleVenvPaths) {
            if (fs.existsSync(p)) { pythonPath = p; break; }
        }

        if (!isFromScratchMode) {
            try {
            const { exec } = require('child_process');
            const { promisify } = require('util');
            const execPromise = promisify(exec);
            const metaCmd = `"${pythonPath}" -m yt_dlp --skip-download --print thumbnail --print title "${sourceUrl}"`;
            const { stdout } = await execPromise(metaCmd, { timeout: 15000 });
            const lines = stdout.trim().split('\n');
            if (lines.length >= 2) {
                thumbnail_url = lines[0].trim();
                video_title = lines[1].trim();
                console.log(`[create-job] Metadata: "${video_title}"`);
            }
            } catch (metaError) {
                console.error('[create-job] Metadata fetch failed (non-fatal):', (metaError as Error).message);
            }
        } else {
            video_title = `Video desde 0 (${body.viralNiche || 'nicho libre'})`;
        }

        // BUG 3 FIX: Wrap DB insert + queue.add() in a transaction.
        // If queue.add() fails, the project INSERT is rolled back — no ghost jobs.
        const client = await pool.connect();
        try {
            await client.query('BEGIN');

            const insertResult = await client.query(
                `INSERT INTO projects (user_id, source_video_url, project_status, thumbnail_url, title)
                 VALUES ($1, $2, 'QUEUED', $3, $4)
                 RETURNING id`,
                [userId, sourceUrl, thumbnail_url, video_title]
            );
            const projectId: string = insertResult.rows[0].id;
            console.log(`[create-job] Project created: ${projectId}`);

            // Add job to BullMQ BEFORE committing the transaction
            const { getVideoQueue } = require('@/lib/queue');
            const q = getVideoQueue();
            await q.add(
                'process-video',
                {
                    projectId,
                    url: sourceUrl,
                    enterpriseOptions: body.enterpriseOptions || {},
                    creationSystem: normalizedCreationSystem,
                    viralNiche: body.viralNiche || 'finanzas personales',
                    viralDryRun: body.viralDryRun ?? false,
                    motorBInput: body.motorBInput || null,
                    motorBTrendMode: body.motorBTrendMode || 'internet',
                },
                { jobId: `video_${projectId}` }
            );
            console.log(`[create-job] Job added to BullMQ for project: ${projectId}`);

            // Only commit if queue.add() succeeded
            await client.query('COMMIT');

            return NextResponse.json({ success: true, jobId: projectId });
        } catch (txError) {
            await client.query('ROLLBACK');
            throw txError;
        } finally {
            client.release();
        }
    } catch (error: any) {
        console.error('[create-job] Error:', error);
        const errLogPath = path.join(process.cwd(), 'route_error.log');
        fs.appendFileSync(errLogPath, `[${new Date().toISOString()}] Error: ${error?.message}\nStack: ${error?.stack}\n\n`);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
