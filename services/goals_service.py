"""
goals_service — objectifs "session only".

Aucune persistance reelle : l'objectif vit en stockage session et disparait
a la fin de la session. C'est une solution intentionnellement temporaire en
attendant la phase "User Profile" (roadmap validee), qui introduira de vrais
objectifs persistants en base. Ne pas construire ici un systeme de stockage
parallele qui serait jete a cette phase-la.

Ce module ne depend jamais de Streamlit directement : il passe par
services.storage, qui est le seul point de couplage a st.session_state.
Quand la persistance reelle arrivera, seul storage.py devra changer.
"""

from services import storage

DEFAULT_GOAL_KCAL = 2000  # objectif de calories cumulees sur la session, valeur de depart raisonnable
_GOAL_KEY = 'session_goal_kcal'


def get_goal() -> int:
    """Retourne l'objectif de calories de la session (kcal), cree au besoin."""
    value = storage.get(_GOAL_KEY)
    if value is None:
        value = DEFAULT_GOAL_KCAL
        storage.set(_GOAL_KEY, value)
    return value


def set_goal(value: int):
    storage.set(_GOAL_KEY, max(0, int(value)))


def get_progress(total_calories_session: float) -> dict:
    """
    Retourne la progression vers l'objectif de session.
    {'current': float, 'target': int, 'pct': float 0-100, 'reached': bool}
    """
    target = get_goal()
    pct = min(100.0, (total_calories_session / target * 100)) if target > 0 else 0.0
    return {
        'current': total_calories_session,
        'target': target,
        'pct': pct,
        'reached': total_calories_session >= target,
    }
