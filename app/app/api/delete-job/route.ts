import { NextResponse } from 'next/server';
import pool from '@/lib/db';
import { auth } from "@/auth";
import fs from 'fs';
import path from 'path';


export async function DELETE(request: Request) {
    const session = await auth();

    if (!session || !session.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const userId = session.user.id;
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    if (!id) {
        return NextResponse.json({ error: 'Project ID is required' }, { status: 400 });
    }

    // Hard Anti-Mock Rule: Verifying ownership before deletion
    const client = await pool.connect();
    try {
        await client.query('BEGIN');

        // Fetch clips corresponding to the project to delete physical files later
        const clipsQuery = await client.query('SELECT id FROM clips WHERE project_id = $1', [id]);
        const clipIds = clipsQuery.rows.map(row => row.id);

        // Ensure the project belongs to the user

        const deleteQuery = 'DELETE FROM projects WHERE id = $1 AND user_id = $2';
        const result = await client.query(deleteQuery, [id, userId]);

        if (result.rowCount === 0) {
            await client.query('ROLLBACK');
            return NextResponse.json({ error: 'Project not found or unauthorized' }, { status: 404 });
        }

        await client.query('COMMIT');

        // FASE 4: QA Fix - Limpieza automática de disco (Borrado físico)
        try {
            const storageBase = path.join(process.cwd(), 'storage');

            // 1. Borrar carpeta temporal del proyecto
            const tempDir = path.join(storageBase, 'temp', id);
            if (fs.existsSync(tempDir)) {
                fs.rmSync(tempDir, { recursive: true, force: true });
            }

            // 2. Borrar todos los archivos relacionados a los clips del proyecto
            for (const clipId of clipIds) {
                const pathsToClean = [
                    path.join(storageBase, 'clips', `${clipId}.mp4`),
                    path.join(storageBase, 'processed', `${clipId}.mp4`),
                    path.join(storageBase, 'processed', `${clipId}_vertical.mp4`),
                    path.join(storageBase, 'subtitled', `${clipId}.mp4`),
                    path.join(storageBase, 'previews', `${clipId}.mp4`),
                    path.join(storageBase, 'previews', `${clipId}_subtitled.mp4`),
                    path.join(storageBase, 'enhanced', `${clipId}.mp4`),
                    path.join(storageBase, 'thumbnails', `${clipId}.jpg`),
                    path.join(storageBase, 'thumbnails', `${clipId}.png`),
                    path.join(storageBase, 'upload_logs', `${clipId}_tiktok.log`),
                    path.join(storageBase, 'upload_logs', `${clipId}_youtube.log`),
                ];

                for (const p of pathsToClean) {
                    if (fs.existsSync(p)) {
                        fs.unlinkSync(p);
                    }
                }
            }

            // 3. Borrar archivos fuente del proyecto (incluye variantes .temp/.fXXX)
            const sourceDir = path.join(storageBase, 'source');
            if (fs.existsSync(sourceDir)) {
                const sourceFiles = fs.readdirSync(sourceDir);
                for (const name of sourceFiles) {
                    const matchesProject =
                        (name === `${id}.mp4`) ||
                        (name === `${id}_master.mp4`) ||
                        (name.startsWith(`${id}.`) && name.endsWith('.mp4'));

                    if (matchesProject) {
                        const sourcePath = path.join(sourceDir, name);
                        if (fs.existsSync(sourcePath)) {
                            fs.unlinkSync(sourcePath);
                        }
                    }
                }
            }

            console.log(`✅ Disco limpio para el proyecto ${id}`);
        } catch (fsError) {
            console.error('⚠️ Error limpiando archivos físicos (el proyecto se borró de la BD de todos modos):', fsError);
        }

        return NextResponse.json({ message: 'Project deleted successfully' });
    } catch (error) {
        await client.query('ROLLBACK');
        console.error('Error deleting project:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    } finally {
        client.release();
    }
}
