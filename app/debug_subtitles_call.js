const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');

// Mock config (simplified version of what's in config.ts)
const rootDir = 'c:\\Users\\jpima\\Downloads\\edumind---ai-learning-guide';
const storageBase = path.join(rootDir, 'app', 'storage');
const clipsDir = path.join(storageBase, 'clips');
const subtitledDir = path.join(storageBase, 'subtitled');
const scriptsDir = path.join(rootDir, 'scripts');

// Mock inputs
const clipId = "24d43931-ffed-4911-a2a3-0455c71901c8";
const style = "CLEAN";
const dbPassword = "n8n";

const inputVideo = path.join(clipsDir, `${clipId}.mp4`);
const outputVideo = path.join(subtitledDir, `${clipId}.mp4`);
const renderScript = path.join(scriptsDir, 'render_with_subtitles.py');

// Python detection (same as route)
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
const cmd = `"${pythonPath}" "${renderScript}" --video "${inputVideo}" --output "${outputVideo}" --clip-id "${clipId}" --style "${style}" --db-password "${dbPassword}" --db-name "antigravity"`;

console.log(`[DEBUG] Executing command: ${cmd}`);

exec(cmd, (error, stdout, stderr) => {
    if (error) {
        console.error(`[DEBUG] Execution error: ${error.message}`);
        return;
    }
    console.log(`[DEBUG] stdout: ${stdout}`);
    if (stderr) console.error(`[DEBUG] stderr: ${stderr}`);
});
