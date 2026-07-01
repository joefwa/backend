from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import requests
import os
from fastapi import HTTPException
from pydantic import BaseModel


ADMIN_USERNAME = "Joseph"
ADMIN_PASSWORD = "YourStrongPassword123"

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

class LoginRequest(BaseModel):
    username: str
    password: str

ADMIN_USERNAME = "Joseph"
ADMIN_PASSWORD = "Isabella1212"


@app.post("/api/admin/login")
def admin_login(data: LoginRequest):

    if (
        data.username == ADMIN_USERNAME
        and
        data.password == ADMIN_PASSWORD
    ):

        return {
            "success": True
        }

    raise HTTPException(
        status_code=401,
        detail="Invalid credentials."
    )

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

    SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

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

# -------------------------
# ADMIN DASHBOARD
# -------------------------

@app.get("/api/admin/dashboard")
def admin_dashboard(db: Session = Depends(get_db)):

    teams = db.query(DBTeam).all()

    total_teams = len(teams)

    battle_royale = len([
        team for team in teams
        if team.game_mode == "BR"
    ])

    multiplayer = len([
        team for team in teams
        if team.game_mode == "MP"
    ])

    total_revenue = total_teams * 25000

    total_matches = sum(team.matches_played for team in teams)

    total_elims = sum(team.total_elims for team in teams)

    total_points = sum(team.circuit_points for team in teams)

    return {
        "totalTeams": total_teams,
        "battleRoyale": battle_royale,
        "multiplayer": multiplayer,
        "revenue": total_revenue,
        "matchesPlayed": total_matches,
        "totalElims": total_elims,
        "totalPoints": total_points
    }