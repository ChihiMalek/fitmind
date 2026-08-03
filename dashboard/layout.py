"""
layout.py — orchestration de la grille de page.

Ne calcule rien, n'appelle jamais services/ ni model_utils : recoit un
contexte deja entierement calcule par dashboard_page.py et decide
uniquement OU chaque carte/graphique s'affiche.
"""

import streamlit as st

from dashboard import cards, charts
from dashboard.components import section_header, responsive_grid, badge_pill


def render_ready(ctx: dict):
    """
    ctx attend les cles :
    status {priority, action, goal_progress, trend}, kpis (list of dicts:
    icon, value, label, badge optionnel — cf. cards.build_kpis),
    bmi, avg_bpm, radar_feat, radar_dist, workout_distribution, trend_predictions,
    recommendation, confidence, goal_progress, latest, predictions
    """
    # ── Zone 0 — Statut & Action ──
    s = ctx['status']
    cards.status_action_card(s['priority'], s['action'], s['goal_progress'], s['trend'])

    # ── Ligne 1 — KPI cards ──
    section_header("◆ Vue d'ensemble")
    kpi_html = [cards.kpi_card_html(**k) for k in ctx['kpis']]
    responsive_grid(kpi_html, min_width_px=125)

    # ── Ligne 2 — Graphiques principaux + colonne laterale ──
    section_header("◆ Performances")
    main_col, side_col = st.columns([2.2, 1])

    with main_col:
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(charts.bmi_gauge(ctx['bmi']), use_container_width=True)
        with g2:
            st.plotly_chart(charts.hr_zone_gauge(ctx['avg_bpm']), use_container_width=True)

        g3, g4 = st.columns(2)
        with g3:
            st.plotly_chart(charts.radar_profile(ctx['radar_feat'], ctx['radar_dist']),
                            use_container_width=True)
        with g4:
            if ctx['workout_distribution']:
                st.markdown(
                    badge_pill('🧪 Type d\'entraînement — Démo', '#D4A830', 'rgba(212,168,48,.14)'),
                    unsafe_allow_html=True,
                )
                st.plotly_chart(charts.workout_donut(ctx['workout_distribution']),
                                use_container_width=True)
            else:
                st.markdown('<div class="dash-card" style="text-align:center;color:var(--text2);'
                            'padding:2rem 1rem">Pas encore assez de séances pour une répartition.</div>',
                            unsafe_allow_html=True)

        if len(ctx['trend_predictions']) >= 2:
            st.plotly_chart(charts.calories_trend(ctx['trend_predictions']), use_container_width=True)
        else:
            st.markdown('<div class="dash-card" style="text-align:center;color:var(--text2);'
                        'padding:1.2rem">Lancez une 2ᵉ prédiction pour voir apparaître une tendance.</div>',
                        unsafe_allow_html=True)

    with side_col:
        cards.recommendation_detail_card(ctx['recommendation'])
        cards.confidence_score_card(ctx['confidence'])
        cards.goal_card(ctx['goal_progress'])

    # ── Bas de page — resume + historique ──
    section_header("◆ Dernière séance & historique")
    b1, b2 = st.columns([1, 2])
    with b1:
        cards.session_summary_card(ctx['latest'])
    with b2:
        cards.history_list(ctx['predictions'])
