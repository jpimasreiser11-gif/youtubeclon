import { NextResponse } from 'next/server';
import pool from '@/lib/db';
import { auth } from "@/auth";

export const dynamic = 'force-dynamic';

export async function GET() {
    const session = await auth();

    if (!session || !session.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const userId = session.user.id;

    try {
        const fs = require('fs');
        fs.appendFileSync('debug_user.log', `[${new Date().toISOString()}] 🔍 API Request /get-jobs\n  User: ${session.user.email}\n  ID: ${userId}\n----------------\n`);
    } catch (e) { }

    const client = await pool.connect();
    try {
        // Hard Anti-Mock Rule: Only real data from DB, filtered by user_id
        // BUG 4 FIX: Stale timeout changed from 30min → 180min (long videos take >30min to process)
        const query = `
      SELECT 
        id, 
        source_video_url as source_url, 
        CASE WHEN project_status = 'PROCESSING' AND updated_at < NOW() - INTERVAL '180 minutes' THEN 'FAILED' ELSE project_status END as status, 
        progress_percent as progress, 
        created_at, 
        title, 
        thumbnail_url, 
        CASE WHEN project_status = 'PROCESSING' AND updated_at < NOW() - INTERVAL '180 minutes' THEN 0 ELSE eta_seconds END as estimated_time_remaining, 
        current_step,
        auto_publish_enabled,
        publish_slots_per_day,
        publish_platforms
      FROM projects 
      WHERE user_id = $1
      ORDER BY created_at DESC 
      LIMIT 20
    `;
        const result = await client.query(query, [userId]);
        return NextResponse.json({
            jobs: result.rows.map(job => ({
                ...job,
                progress: Number(job.progress || 0),
                estimated_time_remaining: Number(job.estimated_time_remaining || 0)
            }))
        });
    } catch (error) {
        console.error('Error fetching projects:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    } finally {
        client.release();
    }
}
