import { NextResponse } from 'next/server';
import pool from '@/lib/db';
import { auth } from "@/auth";
import fs from 'fs';
import path from 'path';

export async function POST(request: Request) {
    const session = await auth();
    if (!session || !session.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    try {
        const formData = await request.formData();
        const clipId = formData.get('clipId') as string;
        const file = formData.get('file') as File;
        const frameTimestamp = formData.get('frameTimestamp') as string;

        if (!clipId) {
            return NextResponse.json({ error: 'Clip ID is required' }, { status: 400 });
        }

        const client = await pool.connect();
        try {
            // Verify ownership
            const ownerRes = await client.query(`
                SELECT 1 FROM clips c 
                JOIN projects p ON c.project_id = p.id 
                WHERE c.id = $1 AND p.user_id = $2
            `, [clipId, session.user.id]);

            if (ownerRes.rows.length === 0) {
                return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
            }

            let thumbUrl = '';

            if (file) {
                // Handle manual upload
                const buffer = Buffer.from(await file.arrayBuffer());
                const fileName = `${clipId}_custom_${Date.now()}.jpg`;
                const storagePath = path.join(process.cwd(), 'storage', 'thumbnails', fileName);
                fs.writeFileSync(storagePath, buffer);
                thumbUrl = storagePath;

                await client.query(`
                    INSERT INTO thumbnails (clip_id, url, is_custom)
                    VALUES ($1, $2, TRUE)
                    ON CONFLICT (id) DO UPDATE SET url = EXCLUDED.url
                `, [clipId, thumbUrl]);
            } else if (frameTimestamp) {
                // Handle frame selection (Simplified: we'd ideally trigger FFmpeg here)
                // For now, we update the placeholder record
                await client.query(`
                    UPDATE thumbnails SET frame_timestamp = $2, is_custom = FALSE
                    WHERE clip_id = $1
                `, [clipId, parseFloat(frameTimestamp)]);
                thumbUrl = 'pending_frame_render';
            }

            return NextResponse.json({ success: true, url: thumbUrl });
        } finally {
            client.release();
        }
    } catch (error) {
        console.error('Error updating thumbnail:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
