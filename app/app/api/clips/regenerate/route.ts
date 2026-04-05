import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';
import { exec } from 'child_process';
import path from 'path';

export async function POST(request: Request) {
    const session = await auth();

    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    try {
        const { clipId } = await request.json();

        if (!clipId) {
            return NextResponse.json({ error: 'Clip ID required' }, { status: 400 });
        }

        // Get clip details from database
        const client = await pool.connect();
        let clipData;

        try {
            const result = await client.query(
                'SELECT project_id, start_time, end_time FROM clips WHERE id = $1::uuid',
                [clipId]
            );

            if (result.rows.length === 0) {
                return NextResponse.json({ error: 'Clip not found' }, { status: 404 });
            }

            clipData = result.rows[0];
        } finally {
            client.release();
        }

        // Regenerate clip using Python script
        const pythonPath = 'c:\\Users\\jpima\\Downloads\\edumind---ai-learning-guide\\venv_sovereign\\Scripts\\python.exe';
        const scriptPath = path.join(process.cwd(), '..', 'scripts', 'regenerate_clip.py');

        const cmd = `"${pythonPath}" "${scriptPath}" --project-id "${clipData.project_id}" --clip-id "${clipId}" --start ${clipData.start_time} --end ${clipData.end_time}`;

        exec(cmd, (error, stdout, stderr) => {
            if (error) {
                console.error('Error regenerating clip:', error);
                console.error('stderr:', stderr);
            } else {
                console.log('Clip regenerated:', stdout);
            }
        });

        return NextResponse.json({
            success: true,
            message: 'Clip regeneration started'
        });

    } catch (error) {
        console.error('Error in regenerate endpoint:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}
