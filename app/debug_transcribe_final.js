const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');

const rootDir = 'c:\\Users\\jpima\\Downloads\\edumind---ai-learning-guide';
const storageBase = path.join(rootDir, 'app', 'storage');
const sourceDir = path.join(storageBase, 'source');
const scriptsDir = path.join(rootDir, 'scripts');

// EXPLICIT VALUES
const projectId = "4358ba66-9f4a-4a10-aeac-363372ecfc3ef";
const clipId = "24d43931-ffed-4911-a2a3-0455c71901c8";
const dbPassword = "n8n";

const videoPath = path.join(sourceDir, `${projectId}.mp4`);
const scriptPath = path.join(scriptsDir, 'transcribe_v2.py');

// Python detection
const isWin = process.platform === "win32";
let pythonPath = "python";

const possibleVenvPaths = [
    path.join(process.cwd(), "..", "venv_sovereign", isWin ? "Scripts" : "bin", isWin ? "python.exe" : "python"),
    path.join(process.cwd(), "venv_sovereign", isWin ? "Scripts" : "bin", isWin ? "python.exe" : "python"),
    path.join(process.cwd(), "venv", isWin ? "Scripts" : "bin", isWin ? "python.exe" : "python")
];

for (const p of possibleVenvPaths) {
    if (fs.existsSync(p)) {
        pythonPath = p;
        break;
    }
}

// Command
const cmd = `"${pythonPath}" "${scriptPath}" --video "${videoPath}" --clip-id "${clipId}" --model large-v3 --db-password "${dbPassword}" --db-name "antigravity" --db-user "n8n"`;

console.log(`[DEBUG] Final Video Path: ${videoPath}`);
console.log(`[DEBUG] Final Command: ${cmd}`);

if (!fs.existsSync(videoPath)) {
    console.error(`[ERROR] Video file NOT FOUND at: ${videoPath}`);
} else {
    exec(cmd, (error, stdout, stderr) => {
        if (error) {
            console.error(`[DEBUG] Execution error: ${error.message}`);
            return;
        }
        console.log(`[DEBUG] stdout: ${stdout}`);
        // Only log stderr if it's not empty
        if (stderr && stderr.trim().length > 0) {
            console.error(`[DEBUG] stderr: ${stderr}`);
        }
    });
}
