import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';
import { exec } from 'child_process';
import path from 'path';
import config from '@/lib/config';

export async function POST(request: Request) {
    const session = await auth();

    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const userId = session.user.id;

    try {
        const {
            clipId,
            platform,
            title,
            description,
            tags,
            scheduleAt
        } = await request.json();

        if (!clipId || !platform) {
            return NextResponse.json({ error: 'Missing clipId or platform' }, { status: 400 });
        }

        const client = await pool.connect();
        try {
            // 1. Verify existence and get metadata if needed
            const clipRes = await client.query(
                'SELECT title_generated, description_generated FROM clips WHERE id = $1',
                [clipId]
            );

            if (clipRes.rows.length === 0) {
                return NextResponse.json({ error: 'Clip not found' }, { status: 404 });
            }

            const clip = clipRes.rows[0];
            const finalTitle = title || clip.title_generated || 'Viral Clip';

            // Handle description and tags parsing if provided as one field or separate
            let finalDesc = description || "";
            let finalTags = tags || "";

            if (!description && !tags && clip.description_generated) {
                const parts = clip.description_generated.split('\n\n');
                finalDesc = parts[0];
                finalTags = parts[1] || "";
            }

            // 2. Add to scheduled_publications
            const scheduledDate = scheduleAt ? new Date(scheduleAt) : new Date();

            await client.query(
                `INSERT INTO scheduled_publications 
                 (clip_id, platform, scheduled_at, status, title, description, tags, attempts, max_attempts)
                 VALUES ($1, $2, $3, 'pending', $4, $5, $6, 0, 3)`,
                [clipId, platform, scheduledDate, finalTitle, finalDesc, finalTags]
            );

            return NextResponse.json({
                success: true,
                message: scheduleAt
                    ? `✅ Programado para el ${new Date(scheduleAt).toLocaleString()}`
                    : `🚀 Publicación iniciada (se procesará en breve)`
            });
        } finally {
            client.release();
        }
    } catch (error) {
        console.error('Error in publish API:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
