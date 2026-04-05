import sys
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # New import
from fastapi.responses import FileResponse # New import
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.db_init import VideoProject, Base

app = FastAPI()

# Allow CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route for Static Files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
print(f"Mounting static files from: {static_dir}")
if not os.path.exists(static_dir):
    print(f"WARNING: Static directory not found at {static_dir}")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    index_path = os.path.join(static_dir, "index.html")
    if not os.path.exists(index_path):
        return {"error": f"Index not found at {index_path}"}
    return FileResponse(index_path)

# Database Setup
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database', 'viral_factory.db')
engine = create_engine(f'sqlite:///{DB_PATH}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ... imports ...
import subprocess

# ... existing code ...

# Pydantic Models
class VideoSchema(BaseModel):
    id: int
    topic: str
    niche: str
    status: str
    script_content: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True

class CreateVideoSchema(BaseModel):
    topic: str
    niche: str

# ... existing code ...

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/videos", response_model=List[VideoSchema])
def get_videos():
    db = SessionLocal()
    videos = db.query(VideoProject).all()
    db.close()
    return videos

@app.post("/api/videos", response_model=VideoSchema)
def create_video(video: CreateVideoSchema):
    from src.utils.db_manager import add_video_idea
    video_id = add_video_idea(video.topic, video.niche)
    
    # Return the created video object
    db = SessionLocal()
    new_video = db.query(VideoProject).filter(VideoProject.id == video_id).first()
    db.close()
    
    # Auto-trigger script generation? Or wait for user action?
    # Let's wait for user to click "Generate Script" or do it automatically if they prefer.
    # For now, just create the idea.
    return new_video

@app.post("/api/actions/{id}/{action}")
def update_status(id: int, action: str):
    db = SessionLocal()
    video = db.query(VideoProject).filter(VideoProject.id == id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Execute Python Scripts based on action
    script_path = None
    
    if action == "generate_script":
        # Run script_writer.py
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generators', 'script_writer.py')
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'script_v{id}.log')
        
        try:
            with open(log_file, "w") as f:
                subprocess.Popen(
                    [sys.executable, script_path, str(id)], 
                    cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    stdout=f,
                    stderr=f
                )
            print(f"Triggered script_writer for {id}, logging to {log_file}")
            video.status = 'idea'
        except Exception as e:
            print(f"Error running script: {e}")

    elif action == "approve":
        video.status = 'scripted'
        # Log to show approval
        print(f"Script approved for Video ID {id}. Ready for production.")
        
    elif action == "render":
        # Launch the Master Video Producer
        producer_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generators', 'video_producer.py')
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'producer_v{id}.log')
        
        try:
            with open(log_file, "w") as f:
                subprocess.Popen(
                    [sys.executable, producer_script, str(id)], 
                    cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    stdout=f,
                    stderr=f
                )
            print(f"Triggered video_producer for {id}, logging to {log_file}")
            video.status = 'assets_ready' # Triggering production
        except Exception as e:
            print(f"Error running producer: {e}")
        
    elif action == "upload":
        video.status = 'rendered'
        
    db.commit()
    db.close()
    return {"status": "success", "message": f"Action {action} triggered"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
