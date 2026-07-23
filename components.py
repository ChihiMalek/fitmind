"""
components.py — atomes UI generiques, sans donnee metier.

Ces fonctions ne savent rien de "calories" ou "BPM" : elles composent du
HTML/CSS generique (grille, badge, en-tete de section) reutilisable par
n'importe quelle page future.
"""

import streamlit as st


def section_header(title: str):
    st.markdown(f'<div class="dash-section-title">{title}</div>', unsafe_allow_html=True)


def responsive_grid(items_html: list, min_width_px: int = 130, gap_px: int = 10):
    """
    Grille CSS auto-fit : le nombre de colonnes s'adapte a la largeur
    disponible (contrairement a st.columns qui garde un nombre fixe de
    colonnes et devient illisible sur mobile).
    """
    cells = "".join(f'<div>{html}</div>' for html in items_html)
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax({min_width_px}px,1fr));
                gap:{gap_px}px;margin-bottom:.8rem">
        {cells}
    </div>
    """, unsafe_allow_html=True)


def badge_pill(text: str, color_hex: str, bg_rgba: str) -> str:
    """Retourne le HTML (str) d'un badge — a inserer dans une carte parente."""
    return (f'<span style="font-family:\'Orbitron\',monospace;font-size:.55rem;'
            f'letter-spacing:1.5px;text-transform:uppercase;padding:.25rem .6rem;'
            f'border-radius:20px;color:{color_hex};background:{bg_rgba};'
            f'border:1px solid {color_hex}55">{text}</span>')


def temp_history_banner():
    st.markdown('<div class="dash-temp-banner">⏳ Historique temporaire (session uniquement)</div>',
                unsafe_allow_html=True)
