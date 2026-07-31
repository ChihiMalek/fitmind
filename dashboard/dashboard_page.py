"""
dashboard_page.py — point d'entree du Dashboard, appele par app.py.

Seul fichier de dashboard/ autorise a importer services/. Ne contient
aucun HTML/CSS brut : construit un contexte de donnees puis delegue
entierement le rendu a dashboard/layout.py.
"""

import streamlit as st

from dashboard import states, layout, cards
from dashboard.theme import inject_dashboard_css
from services import history_service, confidence_service, recommendation_service, goals_service


def render(user: dict, predictions: list, metadata: dict):
    inject_dashboard_css()

    state = states.resolve_state(predictions)

    if state == 'EMPTY':
        def _go_to_predict():
            st.session_state['client_nav'] = "🔮 Nouvelle prédiction"

        states.render_empty(
            icon="🚀",
            title="Bienvenue sur votre Dashboard",
            subtitle="Lancez votre première prédiction pour voir apparaître vos statistiques ici.",
            cta_label="🔮 Lancer une prédiction",
            on_cta=_go_to_predict,
        )
        return

    try:
        ctx = _build_context(predictions, metadata)
    except Exception as e:
        states.render_error(str(e), retry_key="dashboard_retry")
        return

    layout.render_ready(ctx)


def _build_context(predictions: list, metadata: dict) -> dict:
    dist = metadata['regression']['feature_distributions']

    latest = history_service.get_latest(predictions)
    summary = history_service.get_summary(predictions)

    feat = latest.get('features', {})
    confidence = confidence_service.get_confidence(feat, dist) if feat else \
        {'score': latest.get('confidence_score', 0), 'level': latest.get('confidence_level', 'yellow')}

    recommendation = recommendation_service.get_recommendation(
        calories=latest['calories'], level_idx=latest.get('level_idx', 1),
        avg_bpm=latest['avg_bpm'], water=latest['water'],
    )

    goal_progress = goals_service.get_progress(summary['total_calories'])

    kpis = cards.build_kpis(latest, feat, confidence)

    return {
        'status': {
            'priority': recommendation['priority'],
            'action': recommendation['action'],
            'goal_progress': goal_progress,
            'trend': summary['trend'],
        },
        'kpis': kpis,
        'bmi': latest['bmi'],
        'avg_bpm': latest['avg_bpm'],
        'radar_feat': feat,
        'radar_dist': dist,
        'workout_distribution': summary['workout_type_distribution'],
        'trend_predictions': predictions,
        'recommendation': recommendation,
        'confidence': confidence,
        'goal_progress': goal_progress,
        'latest': latest,
        'predictions': predictions,
    }
