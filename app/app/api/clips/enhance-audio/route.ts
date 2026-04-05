import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';
import { exec } from 'child_process';
import { promisify } from 'util';
import fs from 'fs';
import logger from '@/lib/logger';
import { EnhanceAudioSchema, formatZodErrors } from '@/lib/validators';
import config from '@/lib/config';
import { retryExec } from '@/lib/retry';

const execAsync = promisify(exec);

export async function POST(request: Request) {
    const session = await auth();

    if (!session?.user) {
        logger.warn('Unauthorized audio enhancement request');
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    try {
        // Parse and validate request body
        const body = await request.json();
        const validation = EnhanceAudioSchema.safeParse(body);

        if (!validation.success) {
            logger.error('Validation failed for enhance-audio', {
                errors: formatZodErrors(validation.error)
            });
            return NextResponse.json({
                error: 'Datos inválidos',
                details: formatZodErrors(validation.error)
            }, { status: 400 });
        }

        const { clipId, targetLufs, targetTp } = validation.data;

        logger.info('Enhancing audio for clip', {
            clipId,
            targetLufs,
            targetTp,
            userId: session.user.email
        });

        const client = await pool.connect();
        try {
            // Get clip info
            const result = await client.query(
                'SELECT id, project_id FROM clips WHERE id = $1::uuid',
                [clipId]
            );

            if (result.rows.length === 0) {
                logger.warn('Clip not found', { clipId });
                return NextResponse.json({ error: 'Clip no encontrado' }, { status: 404 });
            }

            // Build paths
            const inputVideo = `${config.clipsDir}\\${clipId}.mp4`;
            const outputVideo = `${config.enhancedDir}\\${clipId}_audio_pro.mp4`;

            // Ensure enhanced directory exists
            if (!fs.existsSync(config.enhancedDir)) {
                fs.mkdirSync(config.enhancedDir, { recursive: true });
                logger.info('Created enhanced directory', { path: config.enhancedDir });
            }

            // Build command
            const cmd = `"${config.pythonExecutable}" "${config.scripts.audioProcessor}" --input "${inputVideo}" --output "${outputVideo}" --target-lufs ${targetLufs} --target-tp ${targetTp}`;

            logger.info('Executing audio normalization', { cmd });

            // Execute with retry and timeout
            const { stdout, stderr } = await retryExec(
                () => execAsync(cmd, { timeout: config.timeouts.audio }),
                { maxRetries: 2 }
            );

            logger.debug('Audio normalization stdout', { stdout });
            if (stderr && !stderr.includes('Parsed_loudnorm')) {
                logger.warn('Audio normalization stderr', { stderr });
            }

            // Parse result
            const lines = stdout.split('\n');
            const jsonLine = lines.find(line => line.trim().startsWith('{'));

            if (!jsonLine) {
                throw new Error('No JSON output from audio processor');
            }

            const result_data = JSON.parse(jsonLine);

            if (result_data.success) {
                // Replace original clip with enhanced version
                fs.copyFileSync(outputVideo, inputVideo);
                fs.unlinkSync(outputVideo); // Clean up temp file

                // Update database
                await client.query(
                    `INSERT INTO clip_edits (clip_id, audio_normalized) 
                     VALUES ($1::uuid, true) 
                     ON CONFLICT (clip_id) DO UPDATE 
                     SET audio_normalized = true, updated_at = NOW()`,
                    [clipId]
                );

                logger.info('Audio enhanced successfully', {
                    clipId,
                    targetLufs,
                    stats: result_data.stats
                });

                return NextResponse.json({
                    success: true,
                    message: `Audio normalizado a ${targetLufs} LUFS`,
                    stats: result_data.stats
                });
            } else {
                throw new Error(result_data.error || 'Audio normalization failed');
            }

        } finally {
            client.release();
        }

    } catch (error: any) {
        logger.error('Error in enhance-audio endpoint', {
            error: error.message,
            stack: error.stack
        });
        return NextResponse.json({
            error: error.message || 'Error interno del servidor'
        }, { status: 500 });
    }
}
