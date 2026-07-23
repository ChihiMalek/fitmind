"""
goals_service — objectifs "session only".

Aucune persistance : l'objectif vit dans st.session_state et disparait a la
fin de la session. C'est une solution intentionnellement temporaire en
attendant la phase "User Profile" (roadmap validee), qui introduira de vrais
objectifs persistants en base. Ne pas construire ici un systeme de stockage
parallele qui serait jete a cette phase-la.
"""

import streamlit as st

DEFAULT_GOAL_KCAL = 2000  # objectif de calories cumulees sur la session, valeur de depart raisonnable


def get_goal() -> int:
    """Retourne l'objectif de calories de la session (kcal), cree au besoin."""
    if 'session_goal_kcal' not in st.session_state:
        st.session_state.session_goal_kcal = DEFAULT_GOAL_KCAL
    return st.session_state.session_goal_kcal


def set_goal(value: int):
    st.session_state.session_goal_kcal = max(0, int(value))


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
