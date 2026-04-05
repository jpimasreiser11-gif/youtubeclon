import { NextResponse } from 'next/server';
import pool from '@/lib/db';
import { auth } from "@/auth";

export async function POST(request: Request) {
    const session = await auth();
    if (!session || !session.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    try {
        const body = await request.json();
        const { clipId, overlay_json, subtitle_style, zoom_data } = body;

        if (!clipId) {
            return NextResponse.json({ error: 'Clip ID is required' }, { status: 400 });
        }

        const client = await pool.connect();
        try {
            // Verify ownership first
            const ownerQuery = `
                SELECT 1 FROM clips c
                JOIN projects p ON c.project_id = p.id
                WHERE c.id = $1 AND p.user_id = $2
            `;
            const ownerRes = await client.query(ownerQuery, [clipId, session.user.id]);

            if (ownerRes.rows.length === 0) {
                return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
            }

            const updateQuery = `
                INSERT INTO clip_edits (clip_id, overlay_json, subtitle_style, zoom_data)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (clip_id) DO UPDATE SET
                    overlay_json = EXCLUDED.overlay_json,
                    subtitle_style = EXCLUDED.subtitle_style,
                    zoom_data = EXCLUDED.zoom_data,
                    updated_at = NOW()
            `;
            await client.query(updateQuery, [clipId, overlay_json, subtitle_style, zoom_data]);

            return NextResponse.json({ success: true });
        } finally {
            client.release();
        }
    } catch (error) {
        console.error('Error updating clip edit:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
