from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Create the SQLite Database File (This will automatically generate a file called 'sovereign.db')
SQLALCHEMY_DATABASE_URL = "sqlite:///./sovereign.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# 2. Create the Session (The "pen" we use to write in the database)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Create the Base Blueprint
Base = declarative_base()

# 4. Define the exact structure of our "Teams" table
class DBTeam(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    clan_name = Column(String, unique=True, index=True)  
    game_mode = Column(String)
    captain_id = Column(String)
    discord_tag = Column(String)
    matches_played = Column(Integer, default=0) # NEW
    total_elims = Column(Integer, default=0)    # NEW
    circuit_points = Column(Integer, default=0)

# 5. Execute the build (Creates the actual table inside the sovereign.db file)
Base.metadata.create_all(bind=engine)