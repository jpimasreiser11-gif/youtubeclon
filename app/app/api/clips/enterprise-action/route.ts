import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';
import { exec } from 'child_process';
import path from 'path';
import fs from 'fs';

export async function POST(request: Request) {
    const session = await auth();

    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    try {
        const { clipId, action } = await request.json();

        if (!clipId || !action) {
            return NextResponse.json({ error: 'clipId and action required' }, { status: 400 });
        }

        const client = await pool.connect();
        try {
            // Get clip and project info
            const result = await client.query(`
                SELECT c.id, c.project_id, c.start_time, c.end_time, c.title, c.transcript_json,
                       p.source_video_url 
                FROM clips c
                JOIN projects p ON c.project_id = p.id
                WHERE c.id = $1::uuid
            `, [clipId]);

            if (result.rows.length === 0) {
                return NextResponse.json({ error: 'Clip not found' }, { status: 404 });
            }

            const clip = result.rows[0];
            const STORAGE_BASE = 'c:\\Users\\jpima\\Downloads\\edumind---ai-learning-guide\\app\\storage';
            const sourceVideo = path.join(STORAGE_BASE, 'source', `${clip.project_id}.mp4`);

            // Check if restored master exists
            const masterVideo = path.join(STORAGE_BASE, 'source', `${clip.project_id}_master.mp4`);
            const inputPath = fs.existsSync(masterVideo) ? masterVideo : sourceVideo;

            // Prepare for Clipper execution
            const pythonPath = 'c:\\Users\\jpima\\Downloads\\edumind---ai-learning-guide\\venv_sovereign\\Scripts\\python.exe';
            const clipperScript = path.join(process.cwd(), '..', 'scripts', 'clipper.py');

            // Handle words
            let words: any[] = [];
            try {
                const transcript = JSON.parse(clip.transcript_json);
                transcript.forEach((seg: any) => {
                    if (seg.words) words.push(...seg.words);
                });
            } catch (e) {
                console.error("Error parsing transcript for clipper:", e);
            }

            const clipperInput = {
                id: clip.project_id,
                clips: [{
                    title: clip.title,
                    start_time: clip.start_time,
                    end_time: clip.end_time
                }],
                words: words,
                video_path: inputPath
            };

            const inputJson = JSON.stringify(clipperInput).replace(/"/g, '\\"');
            const cmd = `"${pythonPath}" "${clipperScript}" "${inputJson}"`;

            exec(cmd, async (error, stdout, stderr) => {
                if (error) {
                    console.error(`Enterprise Action failed: ${error}`);
                    return;
                }

                // Clipper saves to output/{projectId}_clip_0.mp4 (since we only passed 1 clip)
                const clipperOut = path.join(process.cwd(), '..', 'output', `${clip.project_id}_clip_0.mp4`);
                const destination = path.join(STORAGE_BASE, 'clips', `${clip.id}.mp4`);

                if (fs.existsSync(clipperOut)) {
                    fs.copyFileSync(clipperOut, destination);

                    // Update zoom_data to mark it as professional reframe
                    const updateClient = await pool.connect();
                    try {
                        await updateClient.query(`
                            UPDATE clip_edits 
                            SET zoom_data = $1, subtitle_style = $2
                            WHERE clip_id = $3::uuid
                        `, [
                            JSON.stringify({ x: 0.5, y: 0.5, w: 1, h: 1, is_dynamic: true, action_applied: action }),
                            JSON.stringify({ font: "Montserrat Bold", color: "#FFFF00", size: 24 }),
                            clip.id
                        ]);
                    } finally {
                        updateClient.release();
                    }
                    console.log(`Enterprise action ${action} completed for clip ${clip.id}`);
                }
            });

            return NextResponse.json({
                success: true,
                message: `Enterprise action ${action} started. This may take a few minutes.`
            });

        } finally {
            client.release();
        }

    } catch (error) {
        console.error('Error in enterprise-action endpoint:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}
