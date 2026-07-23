"""
states.py — gestion explicite des etats d'interface : EMPTY, LOADING, ERROR, READY.

Generique et sans dependance au mot "dashboard" : reutilisable telle quelle
par les futures pages Historique, Analytics, AI Coach.
"""

import streamlit as st


def resolve_state(data, error: str | None = None) -> str:
    """
    Determine l'etat a afficher.
    - 'ERROR' si une erreur a ete capturee en amont
    - 'EMPTY' si data est vide/None (ex: aucune prediction en session)
    - 'READY' sinon
    """
    if error:
        return 'ERROR'
    if not data:
        return 'EMPTY'
    return 'READY'


def render_empty(icon: str = "🧭", title: str = "Aucune donnée pour l'instant",
                  subtitle: str = "", cta_label: str | None = None, on_cta=None):
    """
    Ecran d'invitation generique. Si cta_label et on_cta (callable sans
    argument) sont fournis, un bouton est affiche : on_cta est execute en
    callback (avant le rerun), seule facon fiable de modifier
    st.session_state pour une cle deja liee a un widget dans ce run.
    """
    st.markdown(f"""
    <div class="dash-empty">
        <div class="e-icon">{icon}</div>
        <div class="e-title">{title}</div>
        <div class="e-sub">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)
    if cta_label and on_cta:
        _, mid, _ = st.columns([1, 1, 1])
        with mid:
            st.button(cta_label, use_container_width=True, key="empty_state_cta", on_click=on_cta)


def render_loading(message: str = "Chargement des données..."):
    """Etat de chargement, pour les futures pages avec calcul/requete plus lourde."""
    with st.spinner(message):
        st.empty()


def render_error(message: str, retry_key: str | None = None):
    """Ecran d'erreur clair, sans trace technique brute."""
    st.markdown(f"""
    <div class="dash-error">
        ⚠️ Impossible d'afficher ces données pour le moment.<br>
        <span style="font-size:.8rem;opacity:.85">{message}</span>
    </div>
    """, unsafe_allow_html=True)
    if retry_key and st.button("🔄 Réessayer", key=retry_key):
        st.rerun()
