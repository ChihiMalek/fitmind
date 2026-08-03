"""
models.py — structure des entites persistees.

Dataclasses pures : aucune methode d'acces aux donnees ici (SELECT/INSERT
vivent dans database/repositories/), aucune logique metier (ca vit dans
services/). Ces classes ne font que decrire la forme d'une ligne de table.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: Optional[int]
    public_id: str
    email: str
    password_hash: str
    username: str = ""
    role: str = "client"
    auth_provider: str = "password"
    email_verified_at: Optional[str] = None
    last_login_at: Optional[str] = None
    failed_login_attempts: int = 0
    locked_until: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    deleted_at: Optional[str] = None


@dataclass
class AuthToken:
    id: Optional[int]
    user_id: int
    purpose: str
    token_hash: str
    expires_at: str
    created_at: str
    used_at: Optional[str] = None


@dataclass
class AuthLog:
    id: Optional[int]
    event_type: str
    created_at: str
    user_id: Optional[int] = None
    detail: Optional[str] = None


@dataclass
class Prediction:
    id: Optional[int]
    user_id: int
    created_at: str
    age: float
    gender: float
    height: float
    weight: float
    duration: float
    avg_bpm: float
    resting_bpm: float
    max_bpm: float
    hydration: float
    bmi: float
    calories: float
    level: str
    confidence_score: float
    confidence_level: str
    workout_prediction: str
    features_json: str
    model_version: Optional[str] = None
    app_version: Optional[str] = None
    prediction_time_ms: Optional[float] = None


@dataclass
class Goal:
    id: Optional[int]
    user_id: int
    weekly_goal: float
    calories_goal: float
    sessions_goal: int
    created_at: str


@dataclass
class Settings:
    id: Optional[int]
    user_id: int
    theme: str = "dark"
    language: str = "fr"
    notifications: bool = True
