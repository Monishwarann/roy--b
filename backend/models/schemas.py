from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ─── Auth Schemas ───────────────────────────────────────────────────────────

class UserSignup(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserOut(BaseModel):
    username: str
    email: str
    created_at: Optional[datetime] = None


# ─── Drug Prediction Schemas ─────────────────────────────────────────────────

class ToxicityInput(BaseModel):
    molecular_weight: float
    logp: float
    h_bond_donors: int
    h_bond_acceptors: int
    rotatable_bonds: int
    aromatic_rings: int


class ToxicityResult(BaseModel):
    compound_name: Optional[str] = "Unknown"
    toxicity_class: str          # Low / Medium / High
    risk_level: str              # Non-Toxic / Possibly-Toxic / Toxic
    confidence: float
    probability_scores: dict


class DrugEffectivenessInput(BaseModel):
    compound_id: str
    molecular_weight: float
    h_bond_donors: int
    logp: float


class DrugEffectivenessResult(BaseModel):
    compound_id: str
    binding_score: float
    success_probability: float
    classification: str


# ─── History Schema ───────────────────────────────────────────────────────────

class AnalysisHistoryItem(BaseModel):
    user_email: str
    analysis_type: str
    input_data: dict
    result: dict
    timestamp: Optional[datetime] = None
