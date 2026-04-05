import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import fs from 'fs';

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

    try {
        const client = await pool.connect();

        try {
            // Get clip details
            const result = await client.query(
                `SELECT c.id, c.title, c.category, c.start_time, c.end_time, p.id as project_id, p.user_id
                 FROM clips c
                 JOIN projects p ON c.project_id = p.id
                 WHERE c.id = $1::uuid`,
                [clipId]
            );

            if (result.rows.length === 0) {
                return NextResponse.json({ error: 'Clip not found' }, { status: 404 });
            }

            const clip = result.rows[0];

            if (clip.user_id !== session.user.id) {
                return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
            }

        } finally {
            client.release();
        }

        // Paths
        const videoPath = path.join(process.cwd(), '..', 'storage', 'source', `${clip.project_id}.mp4`);
        const outputDir = path.join(process.cwd(), '..', 'storage', 'thumbnails');
        const outputPath = path.join(outputDir, `${clipId}.jpg`);

        // Ensure output directory exists
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }

        const pythonPath = 'c:\\Users\\jpima\\Downloads\\edumind---ai-learning-guide\\venv_sovereign\\Scripts\\python.exe';
        const scriptPath = path.join(process.cwd(), '..', 'scripts', 'generate_thumbnail.py');
        const dbPassword = process.env.POSTGRES_PASSWORD || 'postgres';

        // Build command
        const cmd = [
            `"${pythonPath}"`,
            `"${scriptPath}"`,
            `--video "${videoPath}"`,
            `--clip-id "${clipId}"`,
            `--title "${clip.title}"`,
            `--category "${clip.category || 'general'}"`,
            `--output "${outputPath}"`,
            `--db-password "${dbPassword}"`
        ].join(' ');

        // Execute thumbnail generation
        const { stdout, stderr } = await execAsync(cmd);
        const result = JSON.parse(stdout);

        if (result.success) {
            return NextResponse.json({
                success: true,
                thumbnailId: result.thumbnail_id,
                thumbnailPath: `/thumbnails/${clipId}.jpg`,
                viralText: result.viral_text,
                timestamp: result.selected_timestamp
            });
        } else {
            throw new Error(result.error);
        }

    } catch (error) {
        console.error('Error generating thumbnail:', error);
        return NextResponse.json({
            error: 'Internal server error'
        }, { status: 500 });
    }
}

// GET: Retrieve existing thumbnail
export async function GET(
    request: Request,
    { params }: { params: { clipId: string } }
) {
    const session = await auth();

    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const clipId = params.clipId;

    try {
        const client = await pool.connect();

        try {
            const result = await client.query(
                `SELECT t.id, t.file_path, t.viral_text, t.created_at
                 FROM thumbnails t
                 JOIN clips c ON t.clip_id = c.id
                 JOIN projects p ON c.project_id = p.id
                 WHERE t.clip_id = $1::uuid AND p.user_id = $2::uuid`,
                [clipId, session.user.id]
            );

            if (result.rows.length === 0) {
                return NextResponse.json({
                    error: 'Thumbnail not found'
                }, { status: 404 });
            }

            const thumbnail = result.rows[0];

            return NextResponse.json({
                id: thumbnail.id,
                path: `/thumbnails/${clipId}.jpg`,
                viralText: thumbnail.viral_text,
                createdAt: thumbnail.created_at
            });

        } finally {
            client.release();
        }

    } catch (error) {
        console.error('Error fetching thumbnail:', error);
        return NextResponse.json({
            error: 'Internal server error'
        }, { status: 500 });
    }
}
