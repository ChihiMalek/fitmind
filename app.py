"""
Gym Predictor - Application Streamlit
Theme: POWER GYM — Fire / Dark Energy (upgraded)
Architecture identique a l'originale — seul le CSS est ameliore
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time

from model_utils import load_or_train_models, predict_calories, predict_experience

# ----------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Gym Predictor",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------------------------
# CUSTOM CSS - THEME POWER GYM (upgraded)
# ----------------------------------------------------------------------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@400;500;600;700&family=Orbitron:wght@400;700&display=swap" rel="stylesheet">

<style>
    /* --- Palette couleurs --- */
    :root {
        --primary:    #FF4500;          /* Orange feu intense */
        --secondary:  #CC0000;          /* Rouge sang */
        --dark:       #080808;          /* Noir spatial */
        --dark2:      #111111;
        --dark3:      #1C1C1C;
        --light:      #F5F5F5;
        --accent:     #FFD700;          /* Or */
        --text:       #FFFFFF;
        --text-muted: #888888;
        --border:     rgba(255,69,0,0.32);
        --shadow:     0 8px 40px rgba(255,69,0,0.3);
        --glow:       0 0 40px rgba(255,69,0,0.55);
    }

    /* --- Polices --- */
    * { font-family: 'Rajdhani', sans-serif !important; }
    h1, h2, h3, h4 { font-family: 'Bebas Neue', sans-serif !important; }

    /* --- Fond general --- */
    .stApp {
        background-color: var(--dark) !important;
        background-image: repeating-linear-gradient(
            -60deg,
            transparent 0px, transparent 38px,
            rgba(255,69,0,0.016) 38px, rgba(255,69,0,0.016) 39px
        ) !important;
        color: var(--text);
    }

    /* --- Block container --- */
    .main .block-container {
        padding: 0 2rem 3rem 2rem !important;
        max-width: 1440px !important;
    }

    /* --- SIDEBAR --- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0D0D0D 0%, #080808 100%) !important;
        border-right: 2px solid var(--primary) !important;
        box-shadow: 6px 0 40px rgba(255,69,0,0.14) !important;
    }

    /* --- BOUTON --- */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #FF4500 0%, #CC0000 50%, #FF4500 100%);
        background-size: 200% 100%;
        color: white;
        font-family: 'Bebas Neue', sans-serif !important;
        font-size: 1.25rem !important;
        font-weight: 700;
        padding: 0.85rem;
        border: none;
        border-radius: 3px;
        letter-spacing: 3px;
        text-transform: uppercase;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(255,69,0,0.5);
        clip-path: polygon(10px 0%, 100% 0%, calc(100% - 10px) 100%, 0% 100%);
        animation: btnPulse 3s ease-in-out infinite;
    }
    .stButton > button:hover {
        background-position: 100% 0;
        transform: translateY(-2px) scale(1.01);
        box-shadow: 0 8px 40px rgba(255,69,0,0.8);
        letter-spacing: 4px;
    }
    .stButton > button:active {
        transform: scale(0.98);
    }

    /* --- Info/Alert --- */
    [data-testid="stAlert"] {
        background: rgba(255,69,0,0.07) !important;
        border: 1px solid rgba(255,69,0,0.25) !important;
        border-left: 4px solid var(--primary) !important;
        border-radius: 3px !important;
        color: #BBBBBB !important;
    }

    /* --- Expander --- */
    [data-testid="stExpander"] {
        background: var(--dark2) !important;
        border: 1px solid var(--border) !important;
        border-left: 4px solid var(--primary) !important;
        border-radius: 3px !important;
    }

    /* --- Scrollbar --- */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: var(--dark); }
    ::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 2px; }

    /* ====================================================
       HEADER
    ==================================================== */
    .main-header {
        position: relative;
        overflow: hidden;
        background: linear-gradient(135deg, #080808 0%, #1C0900 45%, #280A00 70%, #080808 100%);
        padding: 3rem 2rem 2.5rem;
        margin: 0 -2rem 2rem -2rem;
        text-align: center;
        border-bottom: 3px solid var(--primary);
        box-shadow: var(--shadow);
        animation: fadeInDown 0.8s ease;
    }
    .main-header::before {
        content: '';
        position: absolute; inset: 0;
        background: repeating-linear-gradient(
            -45deg, transparent 0px, transparent 36px,
            rgba(255,69,0,0.022) 36px, rgba(255,69,0,0.022) 37px
        );
    }
    /* Barre energetique animee en haut du header */
    .main-header::after {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, transparent, var(--primary), var(--accent), var(--primary), transparent);
        background-size: 300% 100%;
        animation: energyFlow 2.5s linear infinite;
    }
    .main-header h1 {
        font-family: 'Bebas Neue', sans-serif !important;
        font-size: clamp(3rem, 8vw, 5.5rem);
        font-weight: 900;
        letter-spacing: 10px;
        margin: 0;
        text-transform: uppercase;
        color: var(--light);
        text-shadow: 0 0 40px rgba(255,69,0,0.45), 0 0 80px rgba(255,69,0,0.18);
        animation: titleSlam 0.7s cubic-bezier(0.16,1,0.3,1);
    }
    .main-header h1 span {
        color: var(--primary);
        text-shadow: 0 0 30px rgba(255,69,0,0.9), 0 0 70px rgba(255,69,0,0.4);
        animation: fireFlicker 5s ease-in-out infinite;
    }
    .main-header p {
        font-size: 1rem;
        color: var(--text-muted);
        margin: 0.75rem 0 0 0;
        letter-spacing: 3px;
        text-transform: uppercase;
        animation: fadeInUp 0.8s ease 0.25s both;
    }
    .main-header .badge {
        display: inline-block;
        background: rgba(255,69,0,0.12);
        color: var(--primary);
        padding: 5px 20px;
        border: 1px solid rgba(255,69,0,0.4);
        font-family: 'Orbitron', monospace !important;
        font-size: 0.7rem;
        margin-top: 1rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        clip-path: polygon(8px 0%, 100% 0%, calc(100% - 8px) 100%, 0% 100%);
        animation: fadeInUp 0.8s ease 0.4s both;
    }

    /* ====================================================
       CARDS RESULTATS
    ==================================================== */
    .result-card {
        background: linear-gradient(145deg, #141414, #1C1C1C);
        border: 1px solid var(--border);
        padding: 1.75rem;
        position: relative;
        overflow: hidden;
        box-shadow: var(--shadow);
        transition: transform 0.3s, box-shadow 0.3s;
        animation: cardEntrance 0.55s cubic-bezier(0.16,1,0.3,1);
        clip-path: polygon(0 0, calc(100% - 14px) 0, 100% 14px, 100% 100%, 14px 100%, 0 calc(100% - 14px));
    }
    /* Ligne brillante en haut */
    .result-card::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, transparent, var(--primary), var(--accent), var(--primary), transparent);
        animation: shimmer 2.5s ease-in-out infinite;
    }
    /* Lueur interne */
    .result-card::after {
        content: '';
        position: absolute; inset: 0;
        background: radial-gradient(ellipse at 50% -20%, rgba(255,69,0,0.07), transparent 65%);
        pointer-events: none;
    }
    .result-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--glow);
        border-color: rgba(255,69,0,0.55);
    }
    .result-card h2 {
        font-family: 'Orbitron', monospace !important;
        color: var(--primary);
        font-size: 0.75rem;
        margin: 0 0 0.75rem 0;
        letter-spacing: 4px;
        text-transform: uppercase;
        font-weight: 700;
    }
    .result-value {
        font-family: 'Bebas Neue', sans-serif !important;
        font-size: 4rem;
        font-weight: 900;
        color: var(--light);
        margin: 0;
        line-height: 1;
        text-shadow: 0 0 30px rgba(255,255,255,0.08);
    }
    .result-value .unit {
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 1.3rem;
        color: var(--text-muted);
        font-weight: 400;
        letter-spacing: 2px;
    }
    .result-sub {
        color: var(--text-muted);
        font-size: 0.85rem;
        margin: 0.4rem 0 0 0;
        letter-spacing: 1px;
    }

    /* ====================================================
       BADGES NIVEAU
    ==================================================== */
    .badge-level {
        display: inline-block;
        padding: 6px 20px;
        font-family: 'Bebas Neue', sans-serif !important;
        font-size: 1.1rem;
        text-transform: uppercase;
        letter-spacing: 3px;
        margin-top: 10px;
        clip-path: polygon(7px 0%, 100% 0%, calc(100% - 7px) 100%, 0% 100%);
        animation: badgePop 0.6s cubic-bezier(0.34,1.56,0.64,1) 0.25s both;
    }
    .badge-debutant {
        background: #0D2010;
        border: 1px solid #4CAF50;
        color: #4CAF50;
        box-shadow: 0 0 20px rgba(76,175,80,0.35);
    }
    .badge-intermediaire {
        background: #2A1800;
        border: 1px solid #FF9800;
        color: #FF9800;
        box-shadow: 0 0 20px rgba(255,152,0,0.35);
    }
    .badge-avance {
        background: #200500;
        border: 1px solid var(--primary);
        color: var(--primary);
        box-shadow: 0 0 25px rgba(255,69,0,0.5);
    }

    /* ====================================================
       METRIC BOXES
    ==================================================== */
    .metric-box {
        background: var(--dark2);
        border: 1px solid rgba(255,69,0,0.12);
        border-top: 2px solid var(--primary);
        padding: 1rem;
        text-align: center;
        transition: all 0.3s;
        animation: fadeInUp 0.5s ease both;
        clip-path: polygon(0 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%);
    }
    .metric-box:hover {
        border-color: rgba(255,69,0,0.45);
        box-shadow: var(--glow);
        transform: translateY(-3px);
    }
    .metric-box .value {
        font-family: 'Bebas Neue', sans-serif !important;
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--primary);
        display: block;
        line-height: 1;
        text-shadow: 0 0 15px rgba(255,69,0,0.35);
    }
    .metric-box .label {
        font-family: 'Orbitron', monospace !important;
        font-size: 0.58rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 5px;
    }

    /* ====================================================
       BARRES SOFTMAX
    ==================================================== */
    .sf-row {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 10px;
    }
    .sf-label {
        width: 110px;
        font-family: 'Orbitron', monospace !important;
        font-size: 0.6rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .sf-track {
        flex: 1;
        height: 8px;
        background: #111111;
        border: 1px solid rgba(255,69,0,0.1);
        overflow: hidden;
        position: relative;
    }
    .sf-track::before {
        content: '';
        position: absolute; inset: 0;
        background: repeating-linear-gradient(
            90deg, rgba(255,255,255,0.022) 0px, rgba(255,255,255,0.022) 3px,
            transparent 3px, transparent 6px
        );
    }
    .sf-fill {
        height: 100%;
        width: 0%;
        transition: width 1.4s cubic-bezier(0.16,1,0.3,1);
        position: relative;
    }
    .sf-fill.green  { background: linear-gradient(90deg, #1B5E20, #4CAF50); box-shadow: 0 0 12px rgba(76,175,80,0.6); }
    .sf-fill.orange { background: linear-gradient(90deg, #BF360C, #FF9800); box-shadow: 0 0 12px rgba(255,152,0,0.6); }
    .sf-fill.red    { background: linear-gradient(90deg, #B71C1C, #FF4500); box-shadow: 0 0 12px rgba(255,69,0,0.7); }
    .sf-fill::after {
        content: '';
        position: absolute; right: -20px; top: 0; bottom: 0; width: 40px;
        background: rgba(255,255,255,0.25);
        animation: shimmer 2s ease-in-out infinite;
    }
    .sf-pct {
        width: 45px;
        text-align: right;
        font-family: 'Bebas Neue', sans-serif !important;
        font-size: 1.05rem;
        font-weight: 700;
        color: var(--primary);
    }

    /* ====================================================
       FOOTER
    ==================================================== */
    .footer {
        text-align: center;
        color: var(--text-muted);
        font-size: 0.75rem;
        padding: 1.5rem 0 0.5rem;
        border-top: 1px solid var(--border);
        margin-top: 2.5rem;
        font-family: 'Orbitron', monospace !important;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    /* ====================================================
       LOADER
    ==================================================== */
    .loader-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
    }
    .loader {
        width: 60px;
        height: 60px;
        border: 3px solid #1A1A1A;
        border-top: 3px solid var(--primary);
        border-right: 3px solid var(--accent);
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        box-shadow: 0 0 20px rgba(255,69,0,0.4);
    }
    @keyframes spin {
        0%   { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .loader-text {
        color: var(--text-muted);
        margin-top: 1rem;
        font-size: 0.85rem;
        letter-spacing: 3px;
        font-family: 'Orbitron', monospace !important;
        text-transform: uppercase;
        animation: pulse 2s infinite;
    }

    /* ====================================================
       ANIMATIONS
    ==================================================== */
    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-22px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(22px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes pulse {
        0%,100% { opacity: 0.6; }
        50%     { opacity: 1; }
    }
    .pulse { animation: pulse 2s infinite; }

    @keyframes energyFlow {
        0%   { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    @keyframes fireFlicker {
        0%,85%,100% {
            text-shadow: 0 0 30px rgba(255,69,0,.9), 0 0 70px rgba(255,69,0,.4);
            color: #FF4500;
        }
        88% {
            text-shadow: 0 0 60px rgba(255,130,0,1), 0 0 120px rgba(255,180,0,.5);
            color: #FF7000;
        }
        93% {
            text-shadow: 0 0 20px rgba(255,0,0,.7), 0 0 40px rgba(200,0,0,.3);
            color: #FF2200;
        }
    }
    @keyframes titleSlam {
        from { transform: scale(0.78) translateY(-30px); opacity: 0; letter-spacing: 30px; }
        to   { transform: scale(1) translateY(0);       opacity: 1; letter-spacing: 10px; }
    }
    @keyframes cardEntrance {
        from { transform: translateY(35px) scale(0.94); opacity: 0; }
        to   { transform: translateY(0) scale(1);      opacity: 1; }
    }
    @keyframes badgePop {
        from { transform: scale(0.4) rotate(-5deg); opacity: 0; }
        to   { transform: scale(1) rotate(0);       opacity: 1; }
    }
    @keyframes shimmer {
        0%,100% { opacity: 0; }
        50%     { opacity: 1; }
    }
    @keyframes btnPulse {
        0%,100% { box-shadow: 0 4px 20px rgba(255,69,0,.5); }
        50%     { box-shadow: 0 4px 38px rgba(255,69,0,.85); }
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# LOAD MODELS (with training if needed)
# ----------------------------------------------------------------------
with st.spinner("⚡ Chargement des modeles neuronaux..."):
    model_reg, model_clf, scaler_reg, scaler_clf = load_or_train_models()

# ----------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>GYM <span>PREDICTOR</span></h1>
    <p>Estimation des calories &bull; Classification du niveau d'experience</p>
    <span class="badge">🔥 R² &gt; 0.99 &bull; Modele entraîne sur 973 observations &bull; TensorFlow / Keras</span>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# SIDEBAR - Saisie des paramètres
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; margin-bottom:1rem; padding-bottom:1rem; border-bottom:1px solid rgba(255,69,0,0.3);'>
        <span style='font-family:Bebas Neue,sans-serif; font-size:1.8rem; font-weight:900;
                     color:#FF4500; letter-spacing:5px;'>⚡ PARAMETRES</span><br>
        <span style='font-size:0.65rem; letter-spacing:3px; color:#555; text-transform:uppercase;'>
            Donnees biometriques
        </span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        age         = st.slider("Age",          18, 80,   30,   help="Annees")
        gender      = st.selectbox("Genre",     ["Homme", "Femme"])
        weight      = st.slider("Poids (kg)",   40.0, 150.0, 70.0, 0.5)
        height      = st.slider("Taille (m)",   1.40, 2.20, 1.75, 0.01)
    with col2:
        avg_bpm     = st.slider("BPM moyen",    60,  200, 140, help="Frequence cardiaque moyenne pendant l'effort")
        resting_bpm = st.slider("BPM repos",    40,  100,  65)
        duration    = st.slider("Duree (h)",    0.5, 4.0,  1.0, 0.1)
        water       = st.slider("Eau (L)",      0.5, 5.0,  2.0, 0.1)

    workout_freq = st.slider("Frequence (j/sem)", 1, 7, 3)
    exp_level    = st.slider("Niveau d'experience", 1, 3, 2,
                              help="1: Debutant, 2: Intermediaire, 3: Avance")

    # Calcul IMC
    bmi = weight / (height ** 2)

    bmi_color = "#4CAF50" if bmi < 25 else "#FF9800" if bmi < 30 else "#FF4500"
    st.markdown(f"""
    <div style='background:rgba(255,69,0,0.07); border:1px solid rgba(255,69,0,0.28);
                border-top:2px solid {bmi_color}; padding:0.85rem; text-align:center;
                margin:0.5rem 0; clip-path:polygon(0 0,calc(100% - 8px) 0,100% 8px,100% 100%,8px 100%,0 calc(100% - 8px));'>
        <span style='font-family:Bebas Neue,sans-serif; font-size:2.2rem;
                     color:{bmi_color}; display:block; line-height:1;
                     text-shadow:0 0 15px {bmi_color};'>{bmi:.1f}</span>
        <span style='font-family:Orbitron,monospace; font-size:0.55rem;
                     letter-spacing:3px; color:#555; text-transform:uppercase;'>IMC — kg/m²</span>
    </div>
    """, unsafe_allow_html=True)

    # Bouton de prédiction
    predict_btn = st.button("🚀 Lancer la prediction", use_container_width=True)

# ----------------------------------------------------------------------
# PREPARATION DES FEATURES
# ----------------------------------------------------------------------
gender_binary = 0 if gender == "Homme" else 1

features = {
    'Age': age,
    'Gender': gender_binary,
    'Weight (kg)': weight,
    'Height (m)': height,
    'Avg_BPM': avg_bpm,
    'Resting_BPM': resting_bpm,
    'Session_Duration (hours)': duration,
    'Water_Intake (liters)': water,
    'Workout_Frequency (days/week)': workout_freq,
    'Experience_Level': exp_level,
    'BMI': bmi
}

# Features pour la classification (sans Experience_Level)
features_clf = {k: v for k, v in features.items() if k != 'Experience_Level'}

# ----------------------------------------------------------------------
# PREDICTION
# ----------------------------------------------------------------------
if predict_btn:
    with st.spinner("🧠 Inference neuronale en cours..."):
        time.sleep(0.5)

        try:
            # 1. Regression
            calories = predict_calories(model_reg, scaler_reg, features)

            # 2. Classification
            class_idx, proba = predict_experience(model_clf, scaler_clf, features_clf)
            levels       = ["Debutant", "Intermediaire", "Avance"]
            level_name   = levels[class_idx]
            level_symbols = ["[--]", "[-+]", "[++]"]
            level_symbol  = level_symbols[class_idx]

            # ------------------------------------------------------------------
            # AFFICHAGE RESULTATS
            # ------------------------------------------------------------------
            col1, col2 = st.columns([3, 2])

            with col1:
                st.markdown(f"""
                <div class="result-card">
                    <h2>⚡ Calories brulees</h2>
                    <p class="result-value">{calories:.0f} <span class="unit">kcal</span></p>
                    <p class="result-sub">Base sur une seance de {duration}h a {avg_bpm} BPM</p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                badge_class = f"badge-{level_name.lower()}"
                st.markdown(f"""
                <div class="result-card">
                    <h2>🏆 Niveau d'experience</h2>
                    <p class="result-value" style="font-size:2.5rem;">
                        {level_symbol} {level_name}
                    </p>
                    <p class="result-sub">Confiance : {proba[class_idx]*100:.1f}%</p>
                    <span class="badge-level {badge_class}">{level_name}</span>
                </div>
                """, unsafe_allow_html=True)

            # ------------------------------------------------------------------
            # METRIQUES
            # ------------------------------------------------------------------
            st.markdown("<h3 style='font-family:Bebas Neue,sans-serif; color:#FF4500; "
                        "letter-spacing:5px; margin-top:1.5rem; border-left:4px solid #FF4500; "
                        "padding-left:12px;'>ANALYSE DETAILLEE</h3>", unsafe_allow_html=True)

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f"""
                <div class="metric-box">
                    <div class="value">{calories:.0f}</div>
                    <div class="label">Calories (kcal)</div>
                </div>
                """, unsafe_allow_html=True)
            with m2:
                st.markdown(f"""
                <div class="metric-box">
                    <div class="value">{proba[class_idx]*100:.1f}%</div>
                    <div class="label">Confiance IA</div>
                </div>
                """, unsafe_allow_html=True)
            with m3:
                st.markdown(f"""
                <div class="metric-box">
                    <div class="value">{avg_bpm}</div>
                    <div class="label">BPM moyen</div>
                </div>
                """, unsafe_allow_html=True)
            with m4:
                st.markdown(f"""
                <div class="metric-box">
                    <div class="value">{bmi:.1f}</div>
                    <div class="label">IMC</div>
                </div>
                """, unsafe_allow_html=True)

            # ------------------------------------------------------------------
            # PROBABILITES SOFTMAX (barres)
            # ------------------------------------------------------------------
            st.markdown("<h4 style='font-family:Bebas Neue,sans-serif; color:#FF4500; "
                        "letter-spacing:4px; margin-top:1rem;'>Distribution des probabilites</h4>",
                        unsafe_allow_html=True)

            colors = ['#4CAF50', '#FF9800', '#E63946']
            for i, (lvl, prob) in enumerate(zip(levels, proba)):
                pct = prob * 100
                color_class = ['green', 'orange', 'red'][i]
                st.markdown(f"""
                <div class="sf-row">
                    <span class="sf-label">{level_symbols[i]} {lvl}</span>
                    <div class="sf-track">
                        <div class="sf-fill {color_class}" style="width: {pct}%;"></div>
                    </div>
                    <span class="sf-pct">{pct:.1f}%</span>
                </div>
                """, unsafe_allow_html=True)

            # ------------------------------------------------------------------
            # INTERPRETATION
            # ------------------------------------------------------------------
            with st.expander("💡 Interpretation des resultats", expanded=True):
                if calories < 300:
                    cal_analysis = "seance legere, ideale pour un echauffement ou une recuperation."
                elif calories < 600:
                    cal_analysis = "seance moderee, bonne pour maintenir une condition physique."
                elif calories < 900:
                    cal_analysis = "seance intense, excellente pour le developpement musculaire."
                else:
                    cal_analysis = "seance tres intense, niveau athletique ! 🔥"

                if class_idx == 0:
                    exp_analysis = "Vous debutez dans le fitness. Concentrez-vous sur la regularite et la technique."
                elif class_idx == 1:
                    exp_analysis = "Vous avez une bonne base. Augmentez progressivement l'intensite."
                else:
                    exp_analysis = "Vous etes un sportif confirme. Pensez a varier vos exercices."

                st.markdown(f"""
                **Analyse de votre profil**

                - **Calories** : {calories:.0f} kcal — {cal_analysis}
                - **Niveau** : {level_symbol} {level_name} — {exp_analysis}
                - **Cardio** : Votre BPM moyen de {avg_bpm} est {"eleve" if avg_bpm > 160 else "modere" if avg_bpm > 130 else "normal"} pour votre profil.
                - **Hydratation** : {water} L/jour — {"✅ Bonne hydratation" if water >= 2 else "⚠️ Pensez a vous hydrater davantage"}
                """)

        except Exception as e:
            st.error(f"Erreur lors de la prediction : {e}")

else:
    # Message d'accueil
    st.markdown("""
    <div style='background:linear-gradient(135deg,#111 0%,#1A0800 100%);
                border:1px solid rgba(255,69,0,0.22); border-left:5px solid #FF4500;
                padding:2.5rem; text-align:center; margin-top:1rem;
                clip-path:polygon(0 0,calc(100% - 16px) 0,100% 16px,100% 100%,16px 100%,0 calc(100% - 16px));'>
        <div style='font-size:3rem; margin-bottom:1rem;'>🔥</div>
        <div style='font-family:Bebas Neue,sans-serif; font-size:2rem;
                    letter-spacing:5px; color:#FF4500; margin-bottom:0.5rem;'>
            PRET A ANALYSER VOS PERFORMANCES ?
        </div>
        <div style='color:#555; font-size:0.9rem; letter-spacing:2px; text-transform:uppercase;'>
            Renseignez vos donnees dans la barre laterale<br>
            puis cliquez sur <strong style='color:#FF4500;'>LANCER LA PREDICTION</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------------------------
# FOOTER
# ----------------------------------------------------------------------
st.markdown("""
<div class="footer">
    Developpe avec Streamlit &amp; TensorFlow &bull;
    Modele entraîne sur le dataset Gym (973 obs.) &bull;
    Predictions a titre indicatif.
</div>
""", unsafe_allow_html=True)
