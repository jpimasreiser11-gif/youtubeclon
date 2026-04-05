import { NextResponse } from 'next/server';
import pool from '@/lib/db';
import { auth } from "@/auth";

export async function POST(request: Request) {
    const session = await auth();

    if (!session || !session.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    try {
        const { projectId, enabled, slots, platforms } = await request.json();

        if (!projectId) {
            return NextResponse.json({ error: 'Missing projectId' }, { status: 400 });
        }

        const client = await pool.connect();
        try {
            await client.query(
                `UPDATE projects 
                 SET auto_publish_enabled = $1, 
                     publish_slots_per_day = $2, 
                     publish_platforms = $3,
                     updated_at = NOW()
                 WHERE id = $4 AND user_id = $5`,
                [enabled, slots || 3, platforms || ['tiktok', 'youtube'], projectId, session.user.id]
            );

            return NextResponse.json({ success: true });
        } finally {
            client.release();
        }
    } catch (error) {
        console.error('Error updating project automation:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
