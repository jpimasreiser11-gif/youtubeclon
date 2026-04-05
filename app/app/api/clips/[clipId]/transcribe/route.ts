import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import config from '@/lib/config';

const execAsync = promisify(exec);

export async function POST(
    request: Request,
    { params }: { params: { clipId: string } }
) {
    const session = await auth();

    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const clipId = params.clipId;
    let clip: any;

    try {
        const client = await pool.connect();

        try {
            // Verify ownership and get clip details
            const result = await client.query(
                `SELECT c.id, c.start_time, c.end_time, c.transcription_status, p.id as project_id, p.user_id
                 FROM clips c
                 JOIN projects p ON c.project_id = p.id
                 WHERE c.id = $1::uuid`,
                [clipId]
            );

            if (result.rows.length === 0) {
                return NextResponse.json({ error: 'Clip not found' }, { status: 404 });
            }

            clip = result.rows[0];

            if (clip.user_id !== session.user.id) {
                return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
            }

            // Check if already transcribed
            if (clip.transcription_status === 'completed') {
                return NextResponse.json({
                    message: 'Transcription already exists',
                    status: 'completed'
                });
            }

            // Update status to processing
            await client.query(
                'UPDATE clips SET transcription_status = $1 WHERE id = $2::uuid',
                ['processing', clipId]
            );

        } finally {
            client.release();
        }

        // Get file paths
        const videoPath = path.join(config.sourceDir, `${clip.project_id}.mp4`);

        // Determining Python path dynamically (Robust VENV detection)
        const fs = require('fs');
        const isWin = process.platform === "win32";
        let pythonPath = "python"; // Default to system python

        // Try to find venv python
        const possibleVenvPaths = [
            path.join(process.cwd(), "..", "venv_sovereign", isWin ? "Scripts" : "bin", isWin ? "python.exe" : "python"),
            path.join(process.cwd(), "venv_sovereign", isWin ? "Scripts" : "bin", isWin ? "python.exe" : "python"),
            path.join(process.cwd(), "venv", isWin ? "Scripts" : "bin", isWin ? "python.exe" : "python")
        ];

        for (const p of possibleVenvPaths) {
            if (fs.existsSync(p)) {
                pythonPath = p;
                console.log(`[Transcribe] Using venv python: ${pythonPath}`);
                break;
            }
        }

        const scriptPath = path.join(process.cwd(), '..', 'scripts', 'transcribe_v2.py');

        // Get DB password from env
        const dbPassword = process.env.POSTGRES_PASSWORD || 'postgres';

        // Build command
        // FIX: Explicitly pass db-name and db-user to ensure we hit the correct database with correct credentials
        const cmd = `"${pythonPath}" "${scriptPath}" --video "${videoPath}" --clip-id "${clipId}" --model large-v3 --db-password "${dbPassword}" --db-name "antigravity" --db-user "n8n" --db-host "127.0.0.1"`;

        console.log('[Transcribe Debug] Executing command:', cmd);

        // Execute transcription (async, don't wait)
        execAsync(cmd)
            .then(({ stdout, stderr }) => {
                console.log('[Transcribe Debug] Transcription completed stdout:', stdout);
                if (stderr) console.error('[Transcribe Debug] stderr:', stderr);
            })
            .catch(async (error) => {
                console.error('[Transcribe Debug] Transcription failed:', error);
                if (error.stdout) console.log('[Transcribe Debug] stdout dump:', error.stdout);
                if (error.stderr) console.error('[Transcribe Debug] stderr dump:', error.stderr);

                // Update status to failed
                const client = await pool.connect();
                try {
                    await client.query(
                        'UPDATE clips SET transcription_status = $1 WHERE id = $2::uuid',
                        ['failed', clipId]
                    );
                } finally {
                    client.release();
                }
            });

        return NextResponse.json({
            success: true,
            message: 'Transcription started',
            clipId: clipId,
            status: 'processing'
        });

    } catch (error) {
        console.error('Error starting transcription:', error);
        return NextResponse.json({
            error: 'Internal server error'
        }, { status: 500 });
    }
}
