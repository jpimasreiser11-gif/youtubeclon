import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Enum, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class VideoProject(Base):
    __tablename__ = 'video_projects'
    
    id = Column(Integer, primary_key=True)
    topic = Column(String, nullable=False)
    niche = Column(String, nullable=False)
    script_content = Column(Text, nullable=True) # JSON stored as text
    status = Column(Enum('idea', 'scripted', 'assets_ready', 'rendered', 'uploaded', name='video_status'), default='idea')
    local_path = Column(String, nullable=True)
    platform_tags = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    scheduled_time = Column(DateTime, nullable=True)

def init_db():
    # Ensure database directory exists
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database', 'viral_factory.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    print(f"Database initialized at: {db_path}")

if __name__ == "__main__":
    init_db()
