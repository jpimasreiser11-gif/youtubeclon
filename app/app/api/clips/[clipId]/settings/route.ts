import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';

export async function GET(
    request: Request,
    context: { params: Promise<{ clipId: string }> }
) {
    const session = await auth();
    if (!session?.user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const params = await context.params;
    const clipId = params.clipId;
    if (!/^[0-9a-fA-F-]{36}$/.test(clipId)) {
        return NextResponse.json({ error: 'Invalid clip id' }, { status: 400 });
    }

    try {
        const client = await pool.connect();
        try {
            const result = await client.query(
                `SELECT subtitle_style FROM clip_edits WHERE clip_id = $1::uuid`,
                [clipId]
            );

            if (result.rows.length === 0) {
                return NextResponse.json({ subtitleStyle: 'DEFAULT' });
            }

            const styleData = result.rows[0].subtitle_style;
            // Handle if it's stored as JSON or string
            const style = typeof styleData === 'string' ? styleData : (styleData.style || 'DEFAULT');

            return NextResponse.json({ subtitleStyle: style });
        } finally {
            client.release();
        }
    } catch (error) {
        console.error('Error fetching settings:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}

export async function POST(
    request: Request,
    context: { params: Promise<{ clipId: string }> }
) {
    const session = await auth();
    if (!session?.user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const params = await context.params;
    const clipId = params.clipId;
    if (!/^[0-9a-fA-F-]{36}$/.test(clipId)) {
        return NextResponse.json({ error: 'Invalid clip id' }, { status: 400 });
    }
    const { subtitleStyle } = await request.json();

    try {
        const client = await pool.connect();
        try {
            // Upsert into clip_edits
            await client.query(
                `INSERT INTO clip_edits (clip_id, subtitle_style)
                 VALUES ($1::uuid, $2)
                 ON CONFLICT (clip_id) 
                 DO UPDATE SET subtitle_style = $2`,
                [clipId, subtitleStyle]
            );

            return NextResponse.json({ success: true });
        } finally {
            client.release();
        }
    } catch (error) {
        console.error('Error updating settings:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}
