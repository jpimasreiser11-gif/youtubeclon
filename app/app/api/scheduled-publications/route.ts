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
            const result = await client.query(
                `SELECT 
                    sp.id, sp.clip_id, sp.platform, sp.scheduled_at, sp.status, c.title,
                    pm.views, pm.likes, pm.comments, pm.shares
                 FROM scheduled_publications sp
                 JOIN clips c ON sp.clip_id = c.id
                 JOIN projects p ON c.project_id = p.id
                 LEFT JOIN performance_metrics pm ON pm.clip_id = sp.clip_id AND pm.platform = sp.platform
                 WHERE p.user_id = $1::uuid
                 ORDER BY sp.scheduled_at DESC
                 LIMIT 50`,
                [userId]
            );

            return NextResponse.json({ events: result.rows });
        } finally {
            client.release();
        }
    } catch (error) {
        console.error('Error fetching scheduled publications:', error);
        return NextResponse.json({ events: [] });
    }
}
