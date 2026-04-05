import { NextResponse } from 'next/server';
import pool from '@/lib/db';
import { auth } from "@/auth";

export async function GET(request: Request) {
    const session = await auth();
    if (!session || !session.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    if (!id) {
        return NextResponse.json({ error: 'Clip ID is required' }, { status: 400 });
    }

    const client = await pool.connect();
    try {
        const query = `
            SELECT c.*, ce.overlay_json, ce.subtitle_style, ce.zoom_data
            FROM clips c
            LEFT JOIN clip_edits ce ON c.id = ce.clip_id
            JOIN projects p ON c.project_id = p.id
            WHERE c.id = $1 AND p.user_id = $2
        `;
        const result = await client.query(query, [id, session.user.id]);

        if (result.rows.length === 0) {
            return NextResponse.json({ error: 'Clip not found or unauthorized' }, { status: 404 });
        }

        return NextResponse.json({ clip: result.rows[0] });
    } catch (error) {
        console.error('Error fetching clip:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    } finally {
        client.release();
    }
}
