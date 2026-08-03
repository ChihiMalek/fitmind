"""
session_manager.py — pont entre auth_service et st.session_state.

Seul fichier de auth/ autorise a toucher st.session_state (voir
ARCHITECTURE_AUTH_v1.md §2 et §4 — meme principe que services/storage.py
pour goals_service en Phase 2). Ne connait ni SQLite, ni bcrypt, ni les
repositories, ni auth_service : il ne fait que gerer l'etat de session
applicatif au sens Streamlit.

Nommage volontairement neutre quant au mecanisme de persistance
(start_session, pas set_current_user) : un futur "Remember Me" (cookies)
ne changerait que l'interieur de ce fichier, jamais ses appelants — voir
ARCHITECTURE_AUTH_v1.md §4 (Option A validee : pas de cookies persistants
pour l'instant).
"""

from datetime import datetime, timezone
from typing import Optional

import streamlit as st

from auth.auth_config import SESSION_TIMEOUT_MINUTES

_USER_KEY = "auth_session_user"
_LOGIN_AT_KEY = "auth_session_login_at"
_LAST_ACTIVITY_KEY = "auth_session_last_activity"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def start_session(user: dict) -> None:
    """
    Ouvre une session applicative pour l'utilisateur donne.

    Args:
        user: dict deja pret a l'affichage (voir
            services.auth_service.to_session_dict) — jamais un objet User
            brut contenant password_hash.
    """
    now = _now_iso()
    st.session_state[_USER_KEY] = user
    st.session_state[_LOGIN_AT_KEY] = now
    st.session_state[_LAST_ACTIVITY_KEY] = now


def clear_session() -> None:
    """Supprime toutes les cles de session liees a l'utilisateur connecte."""
    for key in (_USER_KEY, _LOGIN_AT_KEY, _LAST_ACTIVITY_KEY):
        st.session_state.pop(key, None)


def get_current_user() -> Optional[dict]:
    """Retourne le dict utilisateur de la session courante, ou None si absent."""
    return st.session_state.get(_USER_KEY)


def is_authenticated() -> bool:
    """
    True si une session existe ET n'a pas expire.

    Nettoie automatiquement la session si elle est expiree (l'appelant n'a
    pas besoin d'appeler clear_session() lui-meme dans ce cas).
    """
    if _USER_KEY not in st.session_state:
        return False
    if is_session_expired():
        clear_session()
        return False
    return True


def touch_session() -> None:
    """
    Repousse l'expiration en mettant a jour l'horodatage de derniere
    activite. N'a aucun effet si aucune session n'est ouverte.
    """
    if _USER_KEY in st.session_state:
        st.session_state[_LAST_ACTIVITY_KEY] = _now_iso()


def is_session_expired() -> bool:
    """
    True si la derniere activite remonte a plus de SESSION_TIMEOUT_MINUTES
    (auth_config.py — aucune valeur codee en dur ici). Une session sans
    horodatage de derniere activite est consideree comme expiree.
    """
    last_activity = st.session_state.get(_LAST_ACTIVITY_KEY)
    if last_activity is None:
        return True
    elapsed = _now() - datetime.fromisoformat(last_activity)
    return elapsed.total_seconds() > SESSION_TIMEOUT_MINUTES * 60
