import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';

export async function GET(request: Request) {
    const session = await auth();

    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const status = searchParams.get('status') || 'all';

    try {
        const client = await pool.connect();

        // Build WHERE clause
        let whereClause = 'WHERE p.user_id = $1::uuid';
        const params: any[] = [session.user.id];

        if (status !== 'all') {
            whereClause += ' AND sp.status = $2';
            params.push(status);
        }

        // Get uploads
        const result = await client.query(`
            SELECT 
                sp.id,
                sp.clip_id,
                sp.platform,
                sp.scheduled_at,
                sp.status,
                sp.attempts,
                sp.error_message as last_error,
                sp.video_url,
                COALESCE(c.title_generated, p.title) as clip_title
            FROM scheduled_publications sp
            JOIN clips c ON sp.clip_id = c.id
            JOIN projects p ON c.project_id = p.id
            ${whereClause}
            ORDER BY sp.scheduled_at DESC
            LIMIT 100
        `, params);

        const uploads = result.rows.map(row => ({
            id: row.id,
            clipId: row.clip_id,
            clipTitle: row.clip_title,
            platform: row.platform,
            scheduledAt: row.scheduled_at,
            status: row.status,
            attempts: row.attempts,
            lastError: row.last_error,
            videoUrl: row.video_url
        }));

        // Get stats
        const statsResult = await client.query(`
            SELECT 
                COUNT(*) FILTER (WHERE status = 'pending') as pending,
                COUNT(*) FILTER (WHERE status = 'success') as success,
                COUNT(*) FILTER (WHERE status = 'failed') as failed,
                COUNT(*) FILTER (WHERE DATE(scheduled_at) = CURRENT_DATE) as total_today
            FROM scheduled_publications sp
            JOIN clips c ON sp.clip_id = c.id
            JOIN projects p ON c.project_id = p.id
            WHERE p.user_id = $1::uuid
        `, [session.user.id]);

        const stats = statsResult.rows[0];

        // Return resource back to pool before sending response to avoid leak
        client.release();

        return NextResponse.json({
            uploads,
            stats: {
                pending: parseInt(stats.pending),
                success: parseInt(stats.success),
                failed: parseInt(stats.failed),
                totalToday: parseInt(stats.total_today)
            }
        });

    } catch (error) {
        console.error('Error fetching uploads:', error);
        return NextResponse.json({
            error: 'Internal server error'
        }, { status: 500 });
    }
}
