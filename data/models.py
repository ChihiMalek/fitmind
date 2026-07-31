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
    email: str
    username: str = ""
    role: str = "client"
    created_at: str = ""
    updated_at: str = ""


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
