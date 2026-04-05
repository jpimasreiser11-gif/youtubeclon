import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';

export async function GET(request: Request) {
    const session = await auth();

    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const userId = session.user.id;

    try {
        const client = await pool.connect();
        try {
            // Get all clips from completed projects for this user
            const result = await client.query(
                `SELECT 
                    c.id,
                    c.title_generated as title,
                    c.virality_score,
                    c.start_time,
                    c.end_time,
                    (c.end_time - c.start_time) as duration,
                    p.id as project_id,
                    p.title as project_title
                 FROM clips c
                 JOIN projects p ON c.project_id = p.id
                 WHERE p.user_id = $1::uuid
                   AND p.project_status = 'COMPLETED'
                 ORDER BY c.virality_score DESC
                 LIMIT 100`,
                [userId]
            );

            return NextResponse.json({
                clips: result.rows.map(row => ({
                    ...row,
                    duration: Math.round(Number(row.duration)),
                    start_time: Number(row.start_time),
                    end_time: Number(row.end_time),
                    virality_score: Number(row.virality_score),
                }))
            });
        } finally {
            client.release();
        }
    } catch (error) {
        console.error('Error fetching available clips:', error);
        return NextResponse.json({ clips: [] });
    }
}
