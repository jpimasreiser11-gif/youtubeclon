const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');

// Mock environment variables from .env
process.env.POSTGRES_PASSWORD = 'n8n';

const clipId = "24d43931-ffed-4911-a2a3-0455c71901c8";
const videoPath = path.join(process.cwd(), '..', 'storage', 'source', '39bf7965-b4f3-7085-858d-fd080de28017.mp4'); // Approximate path, adjust if needed

// Determining Python path dynamically (Exact logic from route.ts)
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
        console.log(`[DEBUG] Found venv python: ${pythonPath}`);
        break;
    }
}

const scriptPath = path.join(process.cwd(), '..', 'scripts', 'transcribe_v2.py');
const dbPassword = process.env.POSTGRES_PASSWORD || 'postgres';

// Command from route.ts
const cmd = `"${pythonPath}" "${scriptPath}" --video "${videoPath}" --clip-id "${clipId}" --model large-v3 --db-password "${dbPassword}" --db-name "antigravity"`;

console.log(`[DEBUG] Executing command: ${cmd}`);

exec(cmd, (error, stdout, stderr) => {
    if (error) {
        console.error(`[DEBUG] Execution error: ${error.message}`);
        console.error(`[DEBUG] stderr dump: ${stderr}`);
        return;
    }
    console.log(`[DEBUG] stdout: ${stdout}`);
    if (stderr) console.error(`[DEBUG] stderr (non-critical): ${stderr}`);
});
