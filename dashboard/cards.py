"""
cards.py — cartes metier du Dashboard.

Regle stricte : ces fonctions ne calculent RIEN et ne lisent jamais
st.session_state ou model_utils. Elles recoivent des valeurs deja
calculees par services/ et ne font que les mettre en forme.
"""

import streamlit as st

from dashboard.theme import STATUS_COLORS, CONFIDENCE_COLORS, TREND_ICONS
from dashboard.components import badge_pill


# ────────────────────────────────────────────────────────────────
# ZONE 0 — Statut & Action (page orientee action)
# ────────────────────────────────────────────────────────────────
def status_action_card(priority: str, action_text: str, goal_progress: dict, trend: str):
    colors = STATUS_COLORS[priority]
    trend_icon = TREND_ICONS.get(trend, '—')
    pct = goal_progress['pct']
    st.markdown(f"""
    <div class="dash-status-card" style="background:{colors['bg']};border-color:{colors['accent']}66">
        <div>
            <span class="dash-status-badge" style="color:{colors['accent']};background:{colors['accent']}22">
                {colors['label']}
            </span>
            <p class="dash-status-action">🎯 {action_text}</p>
            <p class="dash-status-sub">Objectif session : {goal_progress['current']:.0f} / {goal_progress['target']} kcal
                ({pct:.0f}%) &nbsp;·&nbsp; Tendance {trend_icon}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ────────────────────────────────────────────────────────────────
# LIGNE 1 — KPI cards (rendues via components.responsive_grid)
# ────────────────────────────────────────────────────────────────
def kpi_card_html(icon: str, value: str, label: str) -> str:
    return f"""<div class="dash-kpi">
        <span class="k-icon">{icon}</span>
        <span class="k-val">{value}</span>
        <span class="k-lbl">{label}</span>
    </div>"""


# ────────────────────────────────────────────────────────────────
# COLONNE LATERALE — detail derriere la recommandation Zone 0
# ────────────────────────────────────────────────────────────────
def recommendation_detail_card(recommendation: dict):
    st.markdown(f"""
    <div class="dash-card">
        <div style="font-family:'Orbitron',monospace;font-size:.55rem;letter-spacing:2px;
                    color:var(--text2);text-transform:uppercase;margin-bottom:.5rem">
            💡 Analyse détaillée
        </div>
        <p style="font-size:.85rem;color:var(--text);margin:.2rem 0">
            <b>Calories</b> — {recommendation['calories_note']}</p>
        <p style="font-size:.85rem;color:var(--text);margin:.2rem 0">
            <b>Cardio</b> — {recommendation['bpm_note']}</p>
        <p style="font-size:.85rem;color:var(--text);margin:.2rem 0">
            <b>Hydratation</b> — {recommendation['hydration_note']}</p>
        <p style="font-size:.85rem;color:var(--text);margin:.2rem 0">
            <b>Niveau</b> — {recommendation['level_note']}</p>
    </div>
    """, unsafe_allow_html=True)


def confidence_score_card(confidence: dict):
    color = CONFIDENCE_COLORS[confidence['level']]
    st.markdown(f"""
    <div class="dash-card">
        <div style="font-family:'Orbitron',monospace;font-size:.55rem;letter-spacing:2px;
                    color:var(--text2);text-transform:uppercase;margin-bottom:.5rem">
            🛡️ Confiance IA
        </div>
        <span style="font-family:'Bebas Neue',sans-serif;font-size:2rem;color:{color}">
            {confidence['score']:.0f}%
        </span>
        <p style="font-size:.78rem;color:var(--text2);margin:.3rem 0 0">
            Basé sur la proportion de vos données dans la distribution d'entraînement du modèle.
        </p>
    </div>
    """, unsafe_allow_html=True)


def goal_card(goal_progress: dict):
    pct = goal_progress['pct']
    st.markdown(f"""
    <div class="dash-card">
        <div style="font-family:'Orbitron',monospace;font-size:.55rem;letter-spacing:2px;
                    color:var(--text2);text-transform:uppercase;margin-bottom:.5rem">
            🎯 Objectif (session, temporaire)
        </div>
        <div style="background:rgba(58,143,212,.12);border-radius:20px;height:10px;overflow:hidden;margin:.4rem 0">
            <div style="width:{pct:.0f}%;height:100%;background:var(--accent)"></div>
        </div>
        <p style="font-size:.78rem;color:var(--text2)">{goal_progress['current']:.0f} / {goal_progress['target']} kcal</p>
    </div>
    """, unsafe_allow_html=True)


# ────────────────────────────────────────────────────────────────
# BAS DE PAGE — resume + historique
# ────────────────────────────────────────────────────────────────
def session_summary_card(latest: dict):
    st.markdown(f"""
    <div class="dash-card">
        <div style="font-family:'Orbitron',monospace;font-size:.55rem;letter-spacing:2px;
                    color:var(--text2);text-transform:uppercase;margin-bottom:.5rem">
            📋 Dernière séance
        </div>
        <p style="font-size:.85rem;color:var(--text);margin:.2rem 0">
            {latest['time']} · {latest['calories']:.0f} kcal · {latest['level']} · {latest.get('workout_type','—')}
        </p>
    </div>
    """, unsafe_allow_html=True)


def history_list(predictions: list, limit: int = 5):
    from dashboard.components import temp_history_banner
    temp_history_banner()
    for p in reversed(predictions[-limit:]):
        st.markdown(f"""
        <div class="hist-row">
            <span class="hist-badge">{p.get('workout_type','—')[:4].upper()}</span>
            <span class="hist-val">{p['calories']:.0f} kcal</span>
            <span class="hist-time">{p['time']}</span>
        </div>""", unsafe_allow_html=True)
