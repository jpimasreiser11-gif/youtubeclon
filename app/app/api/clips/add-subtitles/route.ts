import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';
import { exec } from 'child_process';
import { promisify } from 'util';
import logger from '@/lib/logger';
import { AddSubtitlesSchema, formatZodErrors } from '@/lib/validators';
import config from '@/lib/config';
import { retryExec } from '@/lib/retry';

const execAsync = promisify(exec);

export async function POST(request: Request) {
    const session = await auth();

    if (!session?.user) {
        logger.warn('Unauthorized subtitle request');
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    try {
        // Parse and validate request body
        const body = await request.json();
        const validation = AddSubtitlesSchema.safeParse(body);

        if (!validation.success) {
            logger.error('Validation failed for add-subtitles', {
                errors: formatZodErrors(validation.error)
            });
            return NextResponse.json({
                error: 'Datos inválidos',
                details: formatZodErrors(validation.error)
            }, { status: 400 });
        }

        const { clipId, style } = validation.data;

        logger.info('Adding subtitles to clip', { clipId, style, userId: session.user.email });

        const client = await pool.connect();
        try {
            // Get clip info from database
            const result = await client.query(
                'SELECT id, project_id FROM clips WHERE id = $1::uuid',
                [clipId]
            );

            if (result.rows.length === 0) {
                logger.warn('Clip not found', { clipId });
                return NextResponse.json({ error: 'Clip no encontrado' }, { status: 404 });
            }

            const clip = result.rows[0];

            // Build paths using config
            const inputVideo = `${config.clipsDir}\\${clipId}.mp4`;
            // FIX: Removed extra space in filename
            const outputVideo = `${config.subtitledDir}\\${clipId}.mp4`;
            const dbPassword = config.database.password;

            // Determining Python path dynamically (Robust VENV detection)
            const path = require('path');
            const fs = require('fs');
            const isWin = process.platform === "win32";
            let pythonPath = "python"; // Default to system python

            // Try to find venv python
            const possibleVenvPaths = [
                path.join(process.cwd(), "venv_sovereign", isWin ? "Scripts" : "bin", isWin ? "python.exe" : "python"),
                path.join(process.cwd(), "..", "venv_sovereign", isWin ? "Scripts" : "bin", isWin ? "python.exe" : "python"), // Check parent dir
                path.join(process.cwd(), "venv", isWin ? "Scripts" : "bin", isWin ? "python.exe" : "python")
            ];

            for (const p of possibleVenvPaths) {
                if (fs.existsSync(p)) {
                    pythonPath = p;
                    logger.info(`[Subtitles] Using venv python: ${pythonPath}`);
                    break;
                }
            }

            // Build command
            // FIX: Explicitly pass db-name and db-user to ensure we hit the correct database with correct credentials
            const cmd = `"${pythonPath}" "${config.scripts.renderWithSubtitles}" --video "${inputVideo}" --output "${outputVideo}" --clip-id "${clipId}" --style "${style}" --db-password "${dbPassword}" --db-name "antigravity" --db-user "n8n" --db-host "127.0.0.1"`;

            // Initial status update to 'processing' before responding
            await client.query(
                "UPDATE clips SET render_status = 'processing', render_progress = 0, render_error = NULL WHERE id::text = $1",
                [clipId]
            );

            logger.info('Executing subtitle generation as background process', { cmd });

            // Execute as background process (non-blocking)
            exec(cmd, async (error, stdout, stderr) => {
                const client = await pool.connect();
                try {
                    if (error) {
                        logger.error('Subtitle generation failed in background', { error: error.message, clipId });
                        // Optionally update a jobs or status table here
                        return;
                    }

                    if (stderr && !stderr.includes('Parsed_')) {
                        logger.warn('Subtitle generation reported warnings', { stderr });
                    }

                    // Parse result from stdout
                    const lines = stdout.split('\n');
                    const jsonLine = lines.find(line => line.trim().startsWith('{'));

                    if (jsonLine) {
                        const result_data = JSON.parse(jsonLine);
                        if (result_data.success) {
                            await client.query(
                                `INSERT INTO clip_edits (clip_id, has_subtitles, subtitle_style) 
                                 VALUES ($1::uuid, true, $2::jsonb) 
                                 ON CONFLICT (clip_id) DO UPDATE 
                                 SET has_subtitles = true, subtitle_style = $2::jsonb, updated_at = NOW()`,
                                [clipId, JSON.stringify({ style })]
                            );
                            logger.info('Background subtitle generation complete', { clipId });
                        }
                    }
                } catch (dbError: any) {
                    logger.error('Error updating DB after background subtitle generation', { error: dbError.message });
                } finally {
                    client.release();
                }
            });

            // Return immediate response to the client
            return NextResponse.json({
                success: true,
                message: 'El proceso de renderizado de subtítulos ha comenzado en segundo plano. Estará listo en unos minutos.',
                isBackground: true
            });

        } finally {
            client.release();
        }

    } catch (error: any) {
        logger.error('Error in add-subtitles endpoint', {
            error: error.message,
            stack: error.stack
        });
        return NextResponse.json({
            error: error.message || 'Error interno del servidor'
        }, { status: 500 });
    }
}
