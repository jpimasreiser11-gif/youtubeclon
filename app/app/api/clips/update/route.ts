import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';

export async function POST(request: Request) {
    const session = await auth();

    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    try {
        const { clipId, newStart, newEnd } = await request.json();

        if (!clipId || newStart === undefined || newEnd === undefined) {
            return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
        }

        // Validate duration (min 30 seconds, max 3 minutes)
        const duration = newEnd - newStart;
        if (duration < 30) {
            return NextResponse.json({ error: 'Clip must be at least 30 seconds' }, { status: 400 });
        }
        if (duration > 180) {
            return NextResponse.json({ error: 'Clip must be no longer than 3 minutes' }, { status: 400 });
        }

        const client = await pool.connect();
        try {
            // Update clip times in database
            await client.query(
                'UPDATE clips SET start_time = $1, end_time = $2, updated_at = NOW() WHERE id = $3::uuid',
                [newStart, newEnd, clipId]
            );

            return NextResponse.json({ success: true });
        } finally {
            client.release();
        }
    } catch (error) {
        console.error('Error updating clip:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}
