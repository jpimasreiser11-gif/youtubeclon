import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';

export async function POST(request: Request) {
    const session = await auth();

    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    try {
        const { clipId, platform, scheduledAt, title } = await request.json();

        if (!clipId || !platform || !scheduledAt) {
            return NextResponse.json({
                error: 'Missing required fields'
            }, { status: 400 });
        }

        const client = await pool.connect();
        try {
            await client.query(
                `INSERT INTO scheduled_publications (clip_id, platform, scheduled_at, status, title)
                 VALUES ($1::uuid, $2, $3, 'pending', $4)`,
                [clipId, platform, scheduledAt, title]
            );

            return NextResponse.json({ success: true });
        } finally {
            client.release();
        }
    } catch (error) {
        console.error('Error scheduling publication:', error);
        return NextResponse.json({
            error: 'Internal server error'
        }, { status: 500 });
    }
}
