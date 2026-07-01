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


# -------------------------
# DATABASE
# -------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------
# MODELS
# -------------------------

class TeamRegistration(BaseModel):
    clan_name: str
    game_mode: str
    captain_ingame_id: str
    captain_discord: str


class ScoreUpdate(BaseModel):
    clan_name: str
    elims_scored: int
    placement_points: int


# -------------------------
# REGISTER TEAM
# -------------------------

@app.post("/api/register")
def register_team(team: TeamRegistration, db: Session = Depends(get_db)):

    existing = db.query(DBTeam).filter(
        DBTeam.clan_name == team.clan_name
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Clan name already exists."
        )

    new_team = DBTeam(
        clan_name=team.clan_name,
        game_mode=team.game_mode,
        captain_id=team.captain_ingame_id,
        discord_tag=team.captain_discord,
        matches_played=0,
        total_elims=0,
        circuit_points=0
    )

    db.add(new_team)
    db.commit()
    db.refresh(new_team)

    return {
        "status": True,
        "message": "Registration successful."
    }


# -------------------------
# GET ALL TEAMS
# -------------------------

@app.get("/api/teams")
def get_teams(db: Session = Depends(get_db)):
    teams = db.query(DBTeam).all()
    return teams


# -------------------------
# UPDATE SCORES
# -------------------------

@app.post("/api/update-score")
def update_score(score_data: ScoreUpdate, db: Session = Depends(get_db)):

    target_team = db.query(DBTeam).filter(
        DBTeam.clan_name == score_data.clan_name
    ).first()

    if not target_team:
        raise HTTPException(
            status_code=404,
            detail="Clan not found."
        )

    points = score_data.elims_scored + score_data.placement_points

    target_team.matches_played += 1
    target_team.total_elims += score_data.elims_scored
    target_team.circuit_points += points

    db.commit()
    db.refresh(target_team)

    return {
        "status": True,
        "message": "Score updated."
    }


# -------------------------
# PAYSTACK
# -------------------------

@app.post("/api/create-payment")
def create_payment(payment_data: dict):

    SECRET_KEY = "sk_test_b47776d5d284b512fd8fed6657543f7f1416c378"

    url = "https://api.paystack.co/transaction/initialize"

    headers = {
        "Authorization": f"Bearer {SECRET_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "email": payment_data["email"],
        "amount": 25000 * 100,
        "callback_url": "https://sovreignesportsng.netlify.app/"
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload
    )

    return response.json()


# -------------------------
# CLEAR DATABASE
# -------------------------

@app.get("/api/secret-purge-database")
def purge_database(db: Session = Depends(get_db)):

    db.query(DBTeam).delete()
    db.commit()

    return {
        "message": "Database cleared."
    }