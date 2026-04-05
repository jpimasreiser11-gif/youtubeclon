import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';
import fs from 'fs';
import path from 'path';

export async function GET(request: Request) {
    const session = await auth();

    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const clipId = searchParams.get('clipId');
    const format = searchParams.get('format') || 'original'; // 'original', 'subtitled', 'vertical'

    if (!clipId) {
        return NextResponse.json({ error: 'clipId required' }, { status: 400 });
    }

    try {
        const client = await pool.connect();

        try {
            // Verificar ownership del clip
            const clipResult = await client.query(
                `SELECT c.id, c.title, p.user_id, p.id as project_id,
                        c.start_time, c.end_time
                 FROM clips c
                 JOIN projects p ON c.project_id = p.id
                 WHERE c.id = $1::uuid`,
                [clipId]
            );

            if (clipResult.rows.length === 0) {
                return NextResponse.json({ error: 'Clip not found' }, { status: 404 });
            }

            const clip = clipResult.rows[0];

            // Verificar que el usuario es dueño
            if (clip.user_id !== session.user.id) {
                return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
            }

            // Buscar archivo en orden de prioridad
            const basePath = path.join(process.cwd(), '..', 'storage');
            let filePath: string | null = null;
            let filename = `${clip.title || 'clip'}.mp4`.replace(/[^a-zA-Z0-9._-]/g, '_');

            if (format === 'subtitled') {
                const subtitledPath = path.join(basePath, 'subtitled', `${clipId}.mp4`);
                if (fs.existsSync(subtitledPath)) {
                    filePath = subtitledPath;
                }
            }

            if (!filePath && format === 'vertical') {
                const verticalPath = path.join(basePath, 'processed', `${clipId}_vertical.mp4`);
                if (fs.existsSync(verticalPath)) {
                    filePath = verticalPath;
                }
            }

            // Fallback: generar clip desde video original
            if (!filePath) {
                const sourcePath = path.join(basePath, 'source', `${clip.project_id}.mp4`);
                if (!fs.existsSync(sourcePath)) {
                    return NextResponse.json({
                        error: 'Source video not found'
                    }, { status: 404 });
                }

                // Generar clip on-the-fly con FFmpeg
                const outputPath = path.join(basePath, 'temp', `${clipId}.mp4`);
                await generateClip(sourcePath, outputPath, clip.start_time, clip.end_time);
                filePath = outputPath;
            }

            // Registrar descarga en DB
            await client.query(
                `INSERT INTO clip_downloads (clip_id, user_id, format)
                 VALUES ($1::uuid, $2::uuid, $3)`,
                [clipId, session.user.id, format]
            );

            // Stream del archivo
            const fileBuffer = fs.readFileSync(filePath);

            return new NextResponse(fileBuffer, {
                headers: {
                    'Content-Type': 'video/mp4',
                    'Content-Disposition': `attachment; filename="${filename}"`,
                    'Content-Length': fileBuffer.length.toString()
                }
            });

        } finally {
            client.release();
        }

    } catch (error) {
        console.error('Error downloading clip:', error);
        return NextResponse.json({
            error: 'Internal server error'
        }, { status: 500 });
    }
}

async function generateClip(
    sourcePath: string,
    outputPath: string,
    startTime: number,
    endTime: number
): Promise<void> {
    const { execSync } = require('child_process');
    const ffmpegPath = path.join(process.cwd(), '..', 'data', 'ffmpeg.exe');

    const duration = endTime - startTime;

    const command = `"${ffmpegPath}" -y -ss ${startTime} -i "${sourcePath}" -t ${duration} -c:v libx264 -preset fast -crf 23 -c:a aac "${outputPath}"`;

    execSync(command);
}
