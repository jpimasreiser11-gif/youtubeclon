from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.db_init import VideoProject, Base

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database', 'viral_factory.db')
engine = create_engine(f'sqlite:///{DB_PATH}')
Session = sessionmaker(bind=engine)

def add_video_idea(topic, niche):
    session = Session()
    new_video = VideoProject(topic=topic, niche=niche, status='idea')
    session.add(new_video)
    session.commit()
    video_id = new_video.id
    session.close()
    return video_id

def update_video_script(video_id, script_content):
    session = Session()
    video = session.query(VideoProject).filter_by(id=video_id).first()
    if video:
        video.script_content = script_content
        video.status = 'scripted'
        session.commit()
    session.close()

def get_video_by_id(video_id):
    session = Session()
    video = session.query(VideoProject).filter_by(id=video_id).first()
    session.close()
    return video

def update_video_status(video_id, status, local_path=None):
    session = Session()
    video = session.query(VideoProject).filter_by(id=video_id).first()
    if video:
        video.status = status
        if local_path:
            video.local_path = local_path
        session.commit()
    session.close()
