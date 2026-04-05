import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';

// GET: List scheduled posts enriched with clip data
export async function GET(request: Request) {
    const session = await auth();

    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const userId = session.user.id;

    try {
        const client = await pool.connect();
        try {
            const result = await client.query(
                `SELECT 
                    sp.id,
                    sp.clip_id,
                    sp.platform,
                    sp.scheduled_at,
                    sp.status,
                    sp.title,
                    sp.description,
                    sp.tags as hashtags,
                    c.virality_score,
                    p.title as project_title,
                    p.thumbnail_url
                 FROM scheduled_publications sp
                 JOIN clips c ON sp.clip_id = c.id
                 JOIN projects p ON c.project_id = p.id
                 WHERE p.user_id = $1::uuid
                 ORDER BY sp.scheduled_at ASC`,
                [userId]
            );

            // Group by date for the frontend
            const scheduled = result.rows;

            return NextResponse.json({ success: true, scheduled });
        } finally {
            client.release();
        }
    } catch (error: any) {
        console.error('Error fetching schedule:', error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}

// POST: Schedule a new post
export async function POST(request: Request) {
    const session = await auth();

    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    try {
        const body = await request.json();
        const { clipId, platform, scheduledAt, title, description, hashtags } = body;

        if (!clipId || !platform || !scheduledAt) {
            return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
        }

        const client = await pool.connect();
        try {
            const result = await client.query(
                `INSERT INTO scheduled_publications 
                 (clip_id, platform, scheduled_at, status, title, description, tags)
                 VALUES ($1, $2, $3, 'pending', $4, $5, $6)
                 RETURNING id`,
                [clipId, platform, scheduledAt, title, description, hashtags]
            );

            return NextResponse.json({
                success: true,
                id: result.rows[0].id
            });
        } finally {
            client.release();
        }
    } catch (error: any) {
        console.error('Error scheduling post:', error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
