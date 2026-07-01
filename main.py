from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import requests

from database import SessionLocal, DBTeam

app = FastAPI(title="The Sovereign Circuit Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- THE DOORMAN ---
# This function opens the database connection when a request comes in, 
# and safely closes it when the request is done.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- DATA VALIDATION ---
class TeamRegistration(BaseModel):
    clan_name: str
    game_mode: str  # Replaced title_selected
    captain_ingame_id: str
    captain_discord: str

class ScoreUpdate(BaseModel):
    clan_name: str
    elims_scored: int
    placement_points: int

@app.get("/api/secret-purge-database")
def purge_database(db: Session = Depends(get_db)):
    db.query(DBTeam).delete()
    db.commit()
    return {"message": "All test teams have been permanently deleted."}

@app.get("/")
def home():
    return {"status": "Sovereign Circuit Core Online. Database Connected."}

# --- ENDPOINT 1: SAVE A NEW TEAM ---
@app.post("/api/register")
def register_team(team: TeamRegistration, db: Session = Depends(get_db)):
    
    # 1. Check if a team with this name already exists in the database
    existing_team = db.query(DBTeam).filter(DBTeam.clan_name == team.clan_name).first()
    if existing_team:
        # If they exist, throw an error back to the frontend!
        raise HTTPException(status_code=400, detail="Clan name already registered!")

    # 2. Package the new data using our database blueprint
    new_team = DBTeam(
        clan_name=team.clan_name,
        game_mode=team.game_mode, # Save the mode (MP or BR)
        captain_id=team.captain_ingame_id,
        discord_tag=team.captain_discord
    )

    # 3. Save it permanently to the SQLite file
    db.add(new_team)
    db.commit()
    db.refresh(new_team) # Grabs the new auto-generated ID from the database
    
    print(f"✅ SUCCESS: {new_team.clan_name} saved to Database with ID: {new_team.id}")

    return {
        "success": True, 
        "message": f"Sovereign Protocol initiated. Clan '{new_team.clan_name}' secured."
    }

# --- ENDPOINT 2: VIEW ALL SAVED TEAMS ---
@app.get("/api/teams")
def get_all_teams(db: Session = Depends(get_db)):
    # Fetch every single team from the database
    all_teams = db.query(DBTeam).all()
    return all_teams

# --- ENDPOINT 3: UPDATE TEAM SCORES ---
@app.post("/api/update-score")
def update_team_score(score_data: ScoreUpdate, db: Session = Depends(get_db)):
    # 1. Find the exact team in the database
    target_team = db.query(DBTeam).filter(DBTeam.clan_name == score_data.clan_name).first()
    
    if not target_team:
        raise HTTPException(status_code=404, detail="Clan name not found in database.")

    # 2. Calculate the math (1 point per elim + placement points)
    points_earned = score_data.elims_scored + score_data.placement_points

    # 3. Add the new stats to their existing totals
    target_team.matches_played += 1
    target_team.total_elims += score_data.elims_scored
    target_team.circuit_points += points_earned

    # 4. Save the updated stats permanently
    db.commit()
    db.refresh(target_team)

@app.post("/api/create-payment")
def create_payment(payment_data: dict):
    # This URL initializes the payment with Paystack
    url = "https://api.paystack.co/transaction/initialize"
    
    headers = {
        "Authorization": "sk_test_b47776d5d284b512fd8fed6657543f7f1416c378", # USE YOUR SECRET KEY HERE
        "Content-Type": "application/json"
    }
    
    # We tell Paystack how much to charge and where to email the receipt
    payload = {
        "email": payment_data["email"],
        "amount": 25000 * 100, # 25,000 Naira
        "callback_url": "https://your-website-url.netlify.app/"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

    return {
        "success": True, 
        "message": f"{target_team.clan_name} updated! New total: {target_team.circuit_points} pts."
    }