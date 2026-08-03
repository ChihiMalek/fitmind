"""
components.py — atomes UI generiques, sans donnee metier.

Ces fonctions ne savent rien de "calories" ou "BPM" : elles composent du
HTML/CSS generique (grille, badge, en-tete de section) reutilisable par
n'importe quelle page future.
"""

import streamlit as st


def render_html(html: str):
    """
    st.markdown(..., unsafe_allow_html=True) traite tout bloc dont les
    lignes commencent par 4+ espaces comme un bloc de code (regle Markdown
    standard), meme avec unsafe_allow_html=True : le HTML apparait alors en
    texte brut au lieu d'etre rendu (balises <span> visibles a l'ecran).

    Cette fonction aplatit le HTML sur une seule ligne (supprime retours a
    la ligne et indentation) avant de l'envoyer a st.markdown, pour eviter
    tout risque que Markdown l'interprete comme du code plutot que du HTML.
    """
    flat = " ".join(line.strip() for line in html.strip().splitlines())
    st.markdown(flat, unsafe_allow_html=True)


def section_header(title: str):
    st.markdown(f'<div class="dash-section-title">{title}</div>', unsafe_allow_html=True)


def responsive_grid(items_html: list, min_width_px: int = 130, gap_px: int = 10):
    """
    Grille CSS auto-fit : le nombre de colonnes s'adapte a la largeur
    disponible (contrairement a st.columns qui garde un nombre fixe de
    colonnes et devient illisible sur mobile).
    """
    cells = "".join(f'<div>{html}</div>' for html in items_html)
    grid_style = (
        f"display:grid;grid-template-columns:repeat(auto-fit,minmax({min_width_px}px,1fr));"
        f"gap:{gap_px}px;margin-bottom:.8rem"
    )
    render_html(f'<div style="{grid_style}">{cells}</div>')


def badge_pill(text: str, color_hex: str, bg_rgba: str) -> str:
    """Retourne le HTML (str) d'un badge — a inserer dans une carte parente."""
    return (f'<span style="font-family:\'Orbitron\',monospace;font-size:.55rem;'
            f'letter-spacing:1.5px;text-transform:uppercase;padding:.25rem .6rem;'
            f'border-radius:20px;color:{color_hex};background:{bg_rgba};'
            f'border:1px solid {color_hex}55">{text}</span>')


def temp_history_banner():
    st.markdown('<div class="dash-temp-banner">⏳ Historique temporaire (session uniquement)</div>',
                unsafe_allow_html=True)
