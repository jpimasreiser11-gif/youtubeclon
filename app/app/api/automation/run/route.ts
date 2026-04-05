import { NextResponse } from 'next/server';
import { auth } from '@/auth';
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
        const { profileId } = await request.json();

        if (!profileId) {
            return NextResponse.json({ error: 'profileId required' }, { status: 400 });
        }

        // Determining Python path dynamically
        const isWin = process.platform === "win32";
        let pythonPath = "python"; // Default to system python

        // Try to find venv python
        const possibleVenvPaths = [
            path.join(process.cwd(), "venv_sovereign", isWin ? "Scripts" : "bin", isWin ? "python.exe" : "python"),
            path.join(process.cwd(), "..", "venv_sovereign", isWin ? "Scripts" : "bin", isWin ? "python.exe" : "python"), // Check parent dir
            path.join(process.cwd(), "venv", isWin ? "Scripts" : "bin", isWin ? "python.exe" : "python")
        ];

        for (const p of possibleVenvPaths) {
            const fs = require('fs');
            if (fs.existsSync(p)) {
                pythonPath = p;
                console.log(`Using venv python: ${pythonPath}`);
                break;
            }
        }

        // Path to full_autopilot.py - robust search
        let scriptPath = path.join(process.cwd(), '..', 'scripts', 'full_autopilot.py'); // Default guess

        const possibleScriptPaths = [
            path.join(process.cwd(), 'scripts', 'full_autopilot.py'),
            path.join(process.cwd(), 'app', 'scripts', 'full_autopilot.py'),
            path.join(process.cwd(), '..', 'scripts', 'full_autopilot.py'),
            path.join(process.cwd(), '..', '..', 'scripts', 'full_autopilot.py')
        ];

        for (const p of possibleScriptPaths) {
            const fs = require('fs');
            if (fs.existsSync(p)) {
                scriptPath = p;
                console.log(`Using autopilot script: ${scriptPath}`);
                break;
            }
        }

        const command = `"${pythonPath}" "${scriptPath}" "${profileId}"`;
        console.log(`Executing Auto-pilot: ${command}`);

        // No esperar a que termine (background execution)
        exec(command, (error, stdout, stderr) => {
            if (error) {
                console.error(`Auto-pilot error: ${error}`);
                if (stderr) console.error(`Auto-pilot stderr: ${stderr}`);
                return;
            }
            console.log(`Auto-pilot started successfully. Output: ${stdout}`);
        });

        return NextResponse.json({
            success: true,
            message: 'Auto-pilot execution started'
        });

    } catch (error) {
        console.error('Error starting autopilot:', error);
        return NextResponse.json({
            error: 'Internal server error'
        }, { status: 500 });
    }
}
