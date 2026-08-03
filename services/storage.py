"""
storage.py — interface de stockage minimale, independante de tout appelant.

But : etre le SEUL point de couplage a st.session_state dans services/.
Aujourd'hui get()/set() lisent et ecrivent st.session_state ; a la phase
User Profile / Historique SQLite, seule l'implementation de ces deux
fonctions changera (lecture/ecriture en base) — aucun service appelant
(ex. goals_service) n'aura besoin d'etre modifie.

Ne contient aucune logique metier : c'est une facade de stockage generique,
pas un service.
"""

import streamlit as st


def get(key: str, default=None):
    """Retourne la valeur stockee sous `key`, ou `default` si absente."""
    return st.session_state.get(key, default)


def set(key: str, value):
    """Ecrit `value` sous `key`."""
    st.session_state[key] = value
