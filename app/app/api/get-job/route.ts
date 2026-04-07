import { NextResponse } from 'next/server';
import pool from '@/lib/db';
import { auth } from "@/auth";

export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
    const session = await auth();
    if (!session || !session.user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    if (!id) return NextResponse.json({ error: 'ID required' }, { status: 400 });

    const client = await pool.connect();
    try {
                // Keep detail endpoint consistent with get-jobs stale timeout behavior.
        const project = await client.query(`
                        SELECT *,
                                     CASE
                                         WHEN project_status = 'PROCESSING' AND updated_at < NOW() - INTERVAL '90 minutes' THEN 'FAILED'
                                         ELSE project_status
                                     END as status,
                                     progress_percent,
                                     CASE
                                         WHEN project_status = 'PROCESSING' AND updated_at < NOW() - INTERVAL '90 minutes' THEN 0
                                         ELSE eta_seconds
                                     END as eta_seconds,
                                     current_step
            FROM projects 
            WHERE id = $1 AND user_id = $2
        `, [id, session.user.id]);

        if (project.rows.length === 0) return NextResponse.json({ error: 'Not found' }, { status: 404 });

        const clips = await client.query(`
            SELECT *, COALESCE(title_generated, 'Clip') as title 
            FROM clips 
            WHERE project_id = $1
        `, [id]);

        return NextResponse.json({
            job: project.rows[0],
            clips: clips.rows
        });
    } finally {
        client.release();
    }
}
