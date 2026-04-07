import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';

// GET: Retrieve transcription for a clip
export async function GET(
    request: Request,
    context: { params: Promise<{ clipId: string }> }
) {
    const session = await auth();

    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const params = await context.params;
    const clipId = params.clipId;
    if (!/^[0-9a-fA-F-]{36}$/.test(clipId)) {
        return NextResponse.json({ error: 'Invalid clip id' }, { status: 400 });
    }

    try {
        const client = await pool.connect();

        try {
            // Verify ownership and get transcription
            const result = await client.query(
                `SELECT t.id, t.clip_id, t.language, t.words, t.edited, t.created_at, t.updated_at
                 FROM transcriptions t
                 JOIN clips c ON t.clip_id = c.id
                 JOIN projects p ON c.project_id = p.id
                 WHERE t.clip_id = $1::uuid AND p.user_id = $2::uuid`,
                [clipId, session.user.id]
            );

            if (result.rows.length === 0) {
                return NextResponse.json({
                    error: 'Transcription not found. Generate one first.'
                }, { status: 404 });
            }

            const transcription = result.rows[0];

            return NextResponse.json({
                id: transcription.id,
                clipId: transcription.clip_id,
                language: transcription.language,
                words: transcription.words,
                edited: transcription.edited,
                createdAt: transcription.created_at,
                updatedAt: transcription.updated_at
            });

        } finally {
            client.release();
        }

    } catch (error) {
        console.error('Error fetching transcription:', error);
        return NextResponse.json({
            error: 'Internal server error'
        }, { status: 500 });
    }
}

// POST: Update transcription (edited by user)
export async function POST(
    request: Request,
    context: { params: Promise<{ clipId: string }> }
) {
    const session = await auth();

    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const params = await context.params;
    const clipId = params.clipId;
    if (!/^[0-9a-fA-F-]{36}$/.test(clipId)) {
        return NextResponse.json({ error: 'Invalid clip id' }, { status: 400 });
    }
    const { words } = await request.json();

    if (!words || !Array.isArray(words)) {
        return NextResponse.json({
            error: 'Invalid data. Expected {words: Array}'
        }, { status: 400 });
    }

    // Validate word structure
    for (const word of words) {
        if (!word.word || typeof word.start !== 'number' || typeof word.end !== 'number') {
            return NextResponse.json({
                error: 'Invalid word format. Expected {word, start, end}'
            }, { status: 400 });
        }
    }

    try {
        const client = await pool.connect();

        try {
            // Verify ownership
            const ownerCheck = await client.query(
                `SELECT 1 FROM clips c
                 JOIN projects p ON c.project_id = p.id
                 WHERE c.id = $1::uuid AND p.user_id = $2::uuid`,
                [clipId, session.user.id]
            );

            if (ownerCheck.rows.length === 0) {
                return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
            }

            // Update transcription
            const result = await client.query(
                `UPDATE transcriptions
                 SET words = $1, edited = true, updated_at = NOW()
                 WHERE clip_id = $2::uuid
                 RETURNING id, updated_at`,
                [JSON.stringify(words), clipId]
            );

            if (result.rows.length === 0) {
                return NextResponse.json({
                    error: 'Transcription not found'
                }, { status: 404 });
            }

            return NextResponse.json({
                success: true,
                transcriptionId: result.rows[0].id,
                updatedAt: result.rows[0].updated_at
            });

        } finally {
            client.release();
        }

    } catch (error) {
        console.error('Error updating transcription:', error);
        return NextResponse.json({
            error: 'Internal server error'
        }, { status: 500 });
    }
}
