import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';
import { exec } from 'child_process';
import { promisify } from 'util';
import fs from 'fs';
import logger from '@/lib/logger';
import { SmartCropSchema, formatZodErrors } from '@/lib/validators';
import config from '@/lib/config';
import { retryExec } from '@/lib/retry';

const execAsync = promisify(exec);

export async function POST(request: Request) {
    const session = await auth();
    if (!session?.user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    try {
        const { clipId } = await request.json();
        if (!clipId || !/^[0-9a-fA-F-]{36}$/.test(String(clipId))) {
            return NextResponse.json({ error: 'Invalid clipId' }, { status: 400 });
        }
        const client = await pool.connect();
        try {
            const inputVideo = `${config.clipsDir}\\${clipId}.mp4`;
            const outputVideo = `${config.enhancedDir}\\${clipId}_smart_crop.mp4`;

            if (!fs.existsSync(inputVideo)) {
                return NextResponse.json({ error: 'Clip no encontrado' }, { status: 404 });
            }

            // Ensure enhanced directory exists
            if (!fs.existsSync(config.enhancedDir)) {
                fs.mkdirSync(config.enhancedDir, { recursive: true });
            }

            // Llama al nuevo script de Face Tracking
            const scriptPath = `${config.scriptsDir}\\smart_tracker.py`;
            const cmd = `"${config.pythonExecutable}" "${scriptPath}" --input "${inputVideo}" --output "${outputVideo}"`;

            console.log("Ejecutando AI Face Tracking...");
            const { stdout } = await execAsync(cmd);
            const line = stdout.split('\n').find(l => l.trim().startsWith('{'));
            const result = JSON.parse(line || '{"status":"error"}');

            if (result.status === 'success') {
                // Sobrescribe el clip original con la versión reencuadrada
                fs.copyFileSync(outputVideo, inputVideo);
                fs.unlinkSync(outputVideo);

                await client.query(
                    `INSERT INTO clip_edits (clip_id, zoom_data) 
                     VALUES ($1::uuid, $2::jsonb) 
                     ON CONFLICT (clip_id) DO UPDATE 
                     SET zoom_data = $2::jsonb, updated_at = NOW()`,
                    [clipId, JSON.stringify({ tracked: true })]
                );
                return NextResponse.json({ success: true });
            }
            return NextResponse.json({ error: 'Failed Tracker' }, { status: 500 });
        } finally {
            client.release();
        }
    } catch (error: any) {
        console.error(error);
        return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 });
    }
}
