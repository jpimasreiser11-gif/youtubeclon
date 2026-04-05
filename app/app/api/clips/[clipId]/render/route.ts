import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import fs from 'fs';
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
    const { style } = await request.json();

    try {
        const client = await pool.connect();
        let projectId: string;

        try {
            // Get clip details
            const result = await client.query(
                `SELECT c.id, c.start_time, c.end_time, c.title, p.id as project_id, p.user_id
                 FROM clips c
                 JOIN projects p ON c.project_id = p.id
                 WHERE c.id = $1::uuid`,
                [clipId]
            );

            if (result.rows.length === 0) {
                return NextResponse.json({ error: 'Clip not found' }, { status: 404 });
            }

            const clip = result.rows[0];
            projectId = clip.project_id;

            if (clip.user_id !== session.user.id) {
                return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
            }

            // Check transcription exists
            const transCheck = await client.query(
                'SELECT 1 FROM transcriptions WHERE clip_id = $1::uuid',
                [clipId]
            );

            if (transCheck.rows.length === 0) {
                return NextResponse.json({
                    error: 'No transcription found. Generate one first.'
                }, { status: 400 });
            }

        } finally {
            client.release();
        }

        // Paths
        const videoPath = path.join(process.cwd(), '..', 'storage', 'source', `${projectId}.mp4`);
        const outputDir = path.join(process.cwd(), '..', 'storage', 'subtitled');
        const outputPath = path.join(outputDir, `${clipId}.mp4`);

        // Ensure output directory exists
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }

        const pythonPath = config.pythonExecutable;
        // config.scripts.renderWithSubtitles exists, let's use it or build properly
        const scriptPath = config.scripts.renderWithSubtitles;
        const dbPassword = process.env.POSTGRES_PASSWORD || 'n8n';

        // Build command
        const cmd = [
            `"${pythonPath}"`,
            `"${scriptPath}"`,
            `--video "${videoPath}"`,
            `--output "${outputPath}"`,
            `--clip-id "${clipId}"`,
            `--style "${style || 'tiktok'}"`,
            `--db-password "${dbPassword}"`
        ].join(' ');

        // Execute rendering (async)
        execAsync(cmd)
            .then(({ stdout, stderr }) => {
                console.log('Render completed:', stdout);
            })
            .catch((error) => {
                console.error('Render failed:', error);
            });

        return NextResponse.json({
            success: true,
            message: 'Rendering started. This may take several minutes.',
            clipId: clipId,
            status: 'processing'
        });

    } catch (error) {
        console.error('Error starting render:', error);
        return NextResponse.json({
            error: 'Internal server error'
        }, { status: 500 });
    }
}
