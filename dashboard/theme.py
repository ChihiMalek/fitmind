"""
theme.py — source unique des tokens visuels du Dashboard.

Reutilise les variables CSS globales deja definies dans app.py (--accent,
--gold, --green, --panel, ...) et ajoute uniquement ce qui est propre au
Dashboard : cartes a coins plus arrondis, ombres legeres, couleurs de
statut. Aucune variable globale n'est redefinie ici.
"""

import streamlit as st

# Couleurs de statut (Zone 0 — carte Statut & Action)
STATUS_COLORS = {
    'good':      {'accent': '#3DAA55', 'bg': 'rgba(61,170,85,.08)',  'label': 'Tout va bien'},
    'attention': {'accent': '#D4A830', 'bg': 'rgba(212,168,48,.08)', 'label': 'À surveiller'},
}

# Reprend la convention deja utilisee par model_utils.check_feature_status
CONFIDENCE_COLORS = {
    'green':  '#5EC46B',
    'yellow': '#D4A830',
    'red':    '#F08080',
}

TREND_ICONS = {'up': '📈', 'down': '📉', 'stable': '➖', 'n/a': '—'}

_CSS_INJECTED_KEY = '_dashboard_css_injected'


def inject_dashboard_css():
    """Injecte le CSS additionnel du Dashboard une seule fois par session."""
    if st.session_state.get(_CSS_INJECTED_KEY):
        return
    st.session_state[_CSS_INJECTED_KEY] = True
    st.markdown("""
    <style>
    .dash-card {
        background: var(--panel); border: 1px solid var(--border);
        border-radius: 16px; padding: 1.1rem 1.3rem;
        box-shadow: 0 4px 18px rgba(0,0,0,.28);
        transition: border-color .15s ease, transform .15s ease;
    }
    .dash-card:hover { border-color: var(--border2); }

    .dash-status-card {
        border-radius: 18px; padding: 1.3rem 1.6rem; margin: .4rem 0 1.2rem;
        border: 1px solid var(--border2); display: flex; align-items: center;
        justify-content: space-between; flex-wrap: wrap; gap: 1rem;
    }
    .dash-status-badge {
        font-family:'Orbitron',monospace !important; font-size:.6rem; letter-spacing:2px;
        text-transform: uppercase; padding: .3rem .7rem; border-radius: 20px;
        display:inline-block; margin-bottom:.4rem;
    }
    .dash-status-action { font-family:'Rajdhani',sans-serif !important; font-size:1.05rem;
        color: var(--text); margin: 0; font-weight:600; }
    .dash-status-sub { color: var(--text2); font-size:.78rem; margin-top:.2rem; }

    .dash-kpi { position: relative; background: var(--panel); border: 1px solid var(--border);
        border-radius: 14px; padding: .9rem; text-align:center; box-shadow: 0 3px 14px rgba(0,0,0,.22); }
    .dash-kpi .k-icon { font-size: 1.1rem; opacity:.85; }
    .dash-kpi .k-val { font-family:'Bebas Neue',sans-serif !important; font-size:1.7rem;
        color: var(--accent2); display:block; line-height:1.15; }
    .dash-kpi .k-lbl { font-family:'Orbitron',monospace !important; font-size:.5rem;
        letter-spacing:1.5px; color: var(--muted); text-transform:uppercase; }
    .dash-kpi .k-badge { position:absolute; top:.45rem; right:.5rem;
        font-family:'Orbitron',monospace !important; font-size:.42rem; letter-spacing:1px;
        text-transform:uppercase; color:#D4A830; background:rgba(212,168,48,.16);
        border:1px solid rgba(212,168,48,.45); border-radius:8px; padding:.1rem .35rem; }

    .dash-summary-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(90px,1fr));
        gap:.6rem; margin-top:.7rem; padding-top:.6rem; border-top:1px solid var(--border); }
    .dash-summary-grid .ss-lbl { display:block; font-family:'Orbitron',monospace !important;
        font-size:.48rem; letter-spacing:1.2px; color: var(--muted); text-transform:uppercase; }
    .dash-summary-grid .ss-val { display:block; font-family:'Rajdhani',sans-serif !important;
        font-size:.95rem; color: var(--text); font-weight:600; margin-top:.15rem; }

    .dash-section-title { font-family:'Orbitron',monospace !important; font-size:.62rem;
        letter-spacing:3px; color: var(--text2); text-transform:uppercase; margin: 1.1rem 0 .6rem; }

    .dash-empty { text-align:center; padding: 3rem 1rem; border: 1px dashed var(--border2);
        border-radius: 16px; }
    .dash-empty .e-icon { font-size: 2.2rem; margin-bottom:.6rem; }
    .dash-empty .e-title { font-family:'Bebas Neue',sans-serif !important; font-size:1.4rem;
        color: var(--accent2); }
    .dash-empty .e-sub { color: var(--text2); font-size:.85rem; margin-top:.3rem; }

    .dash-error { border: 1px solid rgba(214,88,88,.5); background: rgba(214,88,88,.06);
        border-radius: 14px; padding: 1.2rem; color:#F0A0A0; }

    .dash-temp-banner { font-size:.7rem; color: var(--gold); border: 1px dashed rgba(212,168,48,.4);
        border-radius: 8px; padding:.4rem .7rem; display:inline-block; margin-bottom:.6rem; }

    @media (max-width: 640px) {
        .dash-status-card { flex-direction: column; align-items: flex-start; }
    }
    </style>
    """, unsafe_allow_html=True)
