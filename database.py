from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# This tells Python to look for a secret Environment Variable called DATABASE_URL
# If it can't find it (like when you test on your laptop), it defaults to a local SQLite file
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sovereign.db")

# Render's Postgres URLs sometimes start with 'postgres://' but SQLAlchemy requires 'postgresql://'
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Connect to the Database
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class DBTeam(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    clan_name = Column(String, unique=True, index=True)  
    game_mode = Column(String)
    captain_id = Column(String)
    discord_tag = Column(String)
    matches_played = Column(Integer, default=0) 
    total_elims = Column(Integer, default=0)    
    circuit_points = Column(Integer, default=0) 

# Build the tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()