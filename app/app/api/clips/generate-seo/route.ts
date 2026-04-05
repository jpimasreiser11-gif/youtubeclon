import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execPromise = promisify(exec);

export async function POST(request: Request) {
    const session = await auth();

    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    try {
        const { clipId } = await request.json();

        if (!clipId) {
            return NextResponse.json({ error: 'clipId required' }, { status: 400 });
        }

        const client = await pool.connect();

        try {
            // Obtener clip info
            const clipResult = await client.query(
                `SELECT c.*, p.user_id 
                 FROM clips c
                 JOIN projects p ON c.project_id = p.id
                 WHERE c.id = $1::uuid`,
                [clipId]
            );

            if (clipResult.rows.length === 0) {
                return NextResponse.json({ error: 'Clip not found' }, { status: 404 });
            }

            const clip = clipResult.rows[0];

            // Verify ownership
            if (clip.user_id !== session.user.id) {
                return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
            }

            // Ejecutar script de auto-SEO
            const scriptPath = path.join(process.cwd(), '..', 'scripts', 'auto_seo.py');

            const metadata = {
                hook_description: clip.hook_description,
                payoff_description: clip.payoff_description,
                category: clip.category,
                duration: clip.end_time - clip.start_time
            };

            const command = `python "${scriptPath}" '${JSON.stringify(metadata)}'`;
            const { stdout } = await execPromise(command);

            const seoData = JSON.parse(stdout);

            // Actualizar clip en DB
            await client.query(
                `UPDATE clips 
                 SET title_generated = $1,
                     description_generated = $2,
                     hashtags = $3
                 WHERE id = $4::uuid`,
                [
                    seoData.title,
                    seoData.description,
                    seoData.hashtags,
                    clipId
                ]
            );

            return NextResponse.json({
                success: true,
                metadata: seoData
            });

        } finally {
            client.release();
        }

    } catch (error) {
        console.error('Error generating SEO:', error);
        return NextResponse.json({
            error: 'Internal server error'
        }, { status: 500 });
    }
}
