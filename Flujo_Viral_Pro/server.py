import os
import uvicorn
import subprocess
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class IdeationRequest(BaseModel):
    dummy: Optional[str] = None

class TTSRequest(BaseModel):
    text: str
    output: str

class FetchRequest(BaseModel):
    keywords: str
    output: str

class RenderRequest(BaseModel):
    audio: str
    video: str
    output: str

@app.post("/ideation")
def run_ideation():
    try:
        # Calls the python script and captures stdout (JSON)
        result = subprocess.run(
            ["python", "scripts/ideation.py"], 
            capture_output=True, 
            text=True, 
            cwd=os.getcwd()
        )
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr)
        return json.loads(result.stdout)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tts")
def run_tts(req: TTSRequest):
    cmd = ["python", "scripts/tts.py", "--text", req.text, "--output", req.output]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=result.stderr)
    return {"status": "success", "file": req.output}

@app.post("/fetch")
def run_fetch(req: FetchRequest):
    cmd = ["python", "scripts/fetch_video.py", "--keywords", req.keywords, "--output", req.output]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=result.stderr)
    return {"status": "success", "file": req.output}

@app.post("/render")
def run_render(req: RenderRequest):
    cmd = ["python", "scripts/render.py", "--audio", req.audio, "--video", req.video, "--output", req.output]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=result.stderr)
    return {"status": "success", "file": req.output}

if __name__ == "__main__":
    import json
    # Ensure temp dir exists
    os.makedirs("temp", exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)
