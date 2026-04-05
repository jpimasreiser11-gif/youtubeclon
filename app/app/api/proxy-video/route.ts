import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import pool from '@/lib/db';
import { auth } from "@/auth";

export async function GET(request: Request) {
    const session = await auth();
    if (!session || !session.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const clipId = searchParams.get('clipId');

    if (!clipId) {
        return NextResponse.json({ error: 'Clip ID is required' }, { status: 400 });
    }

    const client = await pool.connect();
    try {
        // Hard Anti-Mock Rule: Verifying ownership of the clip before serving the file
        const query = `
            SELECT vv.file_path 
            FROM video_versions vv
            JOIN clips c ON vv.clip_id = c.id
            JOIN projects p ON c.project_id = p.id
            WHERE c.id = $1 AND p.user_id = $2 AND vv.version = 'preview'
        `;
        const result = await client.query(query, [clipId, session.user.id]);

        if (result.rows.length === 0) {
            return NextResponse.json({ error: 'Clip not found or unauthorized' }, { status: 404 });
        }

        const storedPath = result.rows[0].file_path;

        // Fallback path resolution: PRIORITIZE SUBTITLED VERSION
        const storageBase = path.join(process.cwd(), 'storage');
        const candidatePaths = [
            path.join(storageBase, 'subtitled', `${clipId}.mp4`), // Check subtitled first
            storedPath,
            path.join(storageBase, 'processed', `${clipId}.mp4`),
            path.join(storageBase, 'clips', `${clipId}.mp4`),
        ];

        const filePath = candidatePaths.find(p => fs.existsSync(p));

        if (!filePath) {
            console.error(`Video file not found. Tried: ${candidatePaths.join(', ')}`);
            return NextResponse.json({ error: 'Video file missing on disk' }, { status: 404 });
        }

        const stats = fs.statSync(filePath);
        const fileSize = stats.size;
        const range = request.headers.get('range');

        // Handle Range Requests (206 Partial Content) for seek/skip
        if (range) {
            const parts = range.replace(/bytes=/, '').split('-');
            const start = parseInt(parts[0], 10);
            const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;
            const chunkSize = (end - start) + 1;

            const fileStream = fs.createReadStream(filePath, { start, end });

            return new Response(fileStream as any, {
                status: 206,
                headers: {
                    'Content-Range': `bytes ${start}-${end}/${fileSize}`,
                    'Accept-Ranges': 'bytes',
                    'Content-Length': chunkSize.toString(),
                    'Content-Type': 'video/mp4',
                },
            });
        }

        // No range request - stream entire file (200 OK)
        const fileStream = fs.createReadStream(filePath);

        return new NextResponse(fileStream as any, {
            headers: {
                'Content-Type': 'video/mp4',
                'Content-Length': fileSize.toString(),
                'Accept-Ranges': 'bytes',
            },
        });
    } catch (error) {
        console.error('Error serving video:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    } finally {
        client.release();
    }
}
