import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execPromise = promisify(exec);

export async function POST(request: Request) {
    try {
        const { url } = await request.json();

        if (!url) {
            return NextResponse.json({ error: 'URL is required' }, { status: 400 });
        }

        // Robust path resolution from the project root
        // process.cwd() in Next.js usually points to the project root (where /app and /venv_sovereign are)
        const projectRoot = process.cwd();
        // If process.cwd() is inside 'app', we need to go up one level. 
        // Let's check if 'app' is the last segment.
        const rootDir = projectRoot.endsWith('app') ? path.join(projectRoot, '..') : projectRoot;
        const ytdlpPath = path.join(rootDir, 'venv_sovereign', 'Scripts', 'yt-dlp.exe');

        console.log(`Executing metadata fetch for: ${url} using ${ytdlpPath}`);

        const { stdout, stderr } = await execPromise(`"${ytdlpPath}" --get-title --get-thumbnail --no-warnings "${url}"`);

        if (stderr && !stdout) {
            console.error("yt-dlp error:", stderr);
            throw new Error(stderr);
        }

        const lines = stdout.trim().split('\n');
        const title = lines[0];
        const thumbnail = lines[lines.length - 1];

        return NextResponse.json({ title, thumbnail });
    } catch (error: any) {
        console.error('Error fetching metadata:', error);
        return NextResponse.json({ error: 'Failed to fetch video metadata', details: error.message }, { status: 500 });
    }
}
