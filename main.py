from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import requests
import os

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
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- DATA VALIDATION ---
class TeamRegistration(BaseModel):
    clan_name: str
    game_mode: str
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

@app.post("/api/update-score")
def update_score(score_data: ScoreUpdate, db: Session = Depends(get_db)):
    # 1. Find team
    target_team = db.query(DBTeam).filter(DBTeam.clan_name == score_data.clan_name).first()
    
    if not target_team:
        raise HTTPException(status_code=404, detail="Clan name not found in database.")

    # 2. Calculate the math
    points_earned = score_data.elims_scored + score_data.placement_points

    # 3. Add the new stats
    target_team.matches_played += 1
    target_team.total_elims += score_data.elims_scored
    target_team.circuit_points += points_earned

    # 4. Save
    db.commit()
    db.refresh(target_team)
    return {"message": "Stats updated successfully"}

@app.post("/api/create-payment")
def create_payment(payment_data: dict):
    # USE YOUR SECRET KEY HERE
    # WARNING: Keep this key private. Do not commit it to public GitHub.
    # Recommended: Set this as an Environment Variable in Render.
    SECRET_KEY = "sk_test_b47776d5d284b512fd8fed6657543f7f1416c378"
    
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "email": payment_data["email"],
        "amount": 25000 * 100, # 25,000 Naira in kobo
        "callback_url": "https://sovereign-circuit.netlify.app/"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()