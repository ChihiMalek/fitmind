"""
Gym Predictor - Application Streamlit
Theme: Sportif / Dynamique (noir, orange, rouge, blanc)
Animations: transitions CSS, chargement progressif, jauge dynamique
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
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------------------------
# CUSTOM CSS - THEME SPORTIF
# ----------------------------------------------------------------------
st.markdown("""
<style>
    /* --- Palette couleurs --- */
    :root {
        --primary: #FF6B00;      /* Orange vif */
        --secondary: #E63946;    /* Rouge */
        --dark: #0D0D0D;         /* Noir profond */
        --dark2: #1A1A1A;
        --dark3: #2A2A2A;
        --light: #F5F5F5;
        --accent: #FFB347;       /* Orange clair */
        --text: #FFFFFF;
        --text-muted: #AAAAAA;
        --border: #FF6B0040;
        --shadow: 0 8px 32px rgba(255, 107, 0, 0.25);
        --glow: 0 0 30px rgba(255, 107, 0, 0.3);
    }

    /* --- Fond général --- */
    .stApp {
        background: var(--dark);
        color: var(--text);
    }

    /* --- Header --- */
    .main-header {
        background: linear-gradient(135deg, var(--dark) 0%, var(--dark2) 50%, var(--primary) 100%);
        padding: 2rem 2rem 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        border-bottom: 4px solid var(--primary);
        box-shadow: var(--shadow);
        animation: fadeInDown 0.8s ease;
    }
    .main-header h1 {
        font-size: 3rem;
        font-weight: 900;
        letter-spacing: -1px;
        margin: 0;
        text-transform: uppercase;
        color: var(--light);
        text-shadow: 0 0 20px rgba(255, 107, 0, 0.5);
    }
    .main-header h1 span {
        color: var(--primary);
        text-shadow: 0 0 30px var(--primary);
    }
    .main-header p {
        font-size: 1.1rem;
        color: var(--text-muted);
        margin: 0.5rem 0 0 0;
        letter-spacing: 1px;
    }
    .main-header .badge {
        display: inline-block;
        background: var(--primary);
        color: var(--dark);
        padding: 0.2rem 1rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.8rem;
        margin-top: 0.5rem;
        text-transform: uppercase;
    }

    /* --- Cards --- */
    .result-card {
        background: linear-gradient(145deg, var(--dark2), var(--dark3));
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
        transition: transform 0.3s, box-shadow 0.3s;
        animation: fadeInUp 0.6s ease;
    }
    .result-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--glow);
    }
    .result-card h2 {
        color: var(--primary);
        font-size: 1.2rem;
        margin: 0 0 0.5rem 0;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .result-value {
        font-size: 3.2rem;
        font-weight: 900;
        color: var(--light);
        margin: 0;
        line-height: 1.2;
    }
    .result-value .unit {
        font-size: 1.2rem;
        color: var(--text-muted);
        font-weight: 400;
    }
    .result-sub {
        color: var(--text-muted);
        font-size: 0.9rem;
        margin: 0.3rem 0 0 0;
    }

    /* --- Metric boxes --- */
    .metric-box {
        background: var(--dark2);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        border: 1px solid var(--border);
        transition: all 0.3s;
    }
    .metric-box:hover {
        border-color: var(--primary);
        box-shadow: var(--glow);
    }
    .metric-box .value {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--primary);
    }
    .metric-box .label {
        font-size: 0.7rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 0.2rem;
    }

    /* --- Badges de niveau --- */
    .badge-level {
        display: inline-block;
        padding: 0.3rem 1.2rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-debutant { background: #4CAF50; color: #fff; }
    .badge-intermediaire { background: #FF9800; color: #fff; }
    .badge-avance { background: #E63946; color: #fff; }

    /* --- Sidebar --- */
    .css-1d391kg { background-color: var(--dark2); }
    .sidebar-label {
        font-size: 0.75rem;
        font-weight: 700;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.2rem;
    }

    /* --- Bouton --- */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        color: white;
        font-weight: 700;
        padding: 0.8rem;
        border: none;
        border-radius: 8px;
        font-size: 1rem;
        letter-spacing: 1px;
        text-transform: uppercase;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(255, 107, 0, 0.4);
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 30px rgba(255, 107, 0, 0.6);
    }
    .stButton > button:active {
        transform: scale(0.98);
    }

    /* --- Animations --- */
    @keyframes fadeInDown {
        0% { opacity: 0; transform: translateY(-20px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeInUp {
        0% { opacity: 0; transform: translateY(20px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    @keyframes pulse {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
    }
    .pulse {
        animation: pulse 2s infinite;
    }

    /* --- Barres de progression (softmax) --- */
    .sf-row {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 6px;
    }
    .sf-label {
        width: 100px;
        font-size: 0.8rem;
        color: var(--text-muted);
        text-transform: uppercase;
    }
    .sf-track {
        flex: 1;
        height: 8px;
        background: var(--dark3);
        border-radius: 4px;
        overflow: hidden;
    }
    .sf-fill {
        height: 100%;
        border-radius: 4px;
        width: 0%;
        transition: width 1.2s cubic-bezier(0.22, 1, 0.36, 1);
        background: var(--primary);
    }
    .sf-fill.orange { background: var(--primary); }
    .sf-fill.red { background: var(--secondary); }
    .sf-fill.green { background: #4CAF50; }
    .sf-pct {
        width: 40px;
        text-align: right;
        font-weight: 700;
        color: var(--primary);
    }

    /* --- Footer --- */
    .footer {
        text-align: center;
        color: var(--text-muted);
        font-size: 0.8rem;
        padding: 1rem 0;
        border-top: 1px solid var(--border);
        margin-top: 2rem;
    }

    /* --- Loader personnalisé --- */
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
        border: 4px solid var(--dark3);
        border-top: 4px solid var(--primary);
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .loader-text {
        color: var(--text-muted);
        margin-top: 1rem;
        font-size: 0.9rem;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# LOAD MODELS (with training if needed)
# ----------------------------------------------------------------------
with st.spinner("Chargement des modeles neuronaux..."):
    model_reg, model_clf, scaler_reg, scaler_clf = load_or_train_models()

# ----------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>GYM <span>PREDICTOR</span></h1>
    <p>Estimation des calories &bull; Classification du niveau d'experience</p>
    <span class="badge">R² > 0.99 &bull; Modele entraîne sur 973 observations</span>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# SIDEBAR - Saisie des paramètres
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("<div style='text-align:center; margin-bottom:1rem;'><span style='font-size:1.5rem; font-weight:900; color:#FF6B00;'>PARAMETRES</span></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        age = st.slider("Age", 18, 80, 30, help="Annees")
        gender = st.selectbox("Genre", ["Homme", "Femme"])
        weight = st.slider("Poids (kg)", 40.0, 150.0, 70.0, 0.5)
        height = st.slider("Taille (m)", 1.40, 2.20, 1.75, 0.01)
    with col2:
        avg_bpm = st.slider("BPM moyen", 60, 200, 140, help="Frequence cardiaque moyenne pendant l'effort")
        resting_bpm = st.slider("BPM repos", 40, 100, 65)
        duration = st.slider("Duree seance (h)", 0.5, 4.0, 1.0, 0.1)
        water = st.slider("Eau (L)", 0.5, 5.0, 2.0, 0.1)
    
    workout_freq = st.slider("Frequence (j/sem)", 1, 7, 3)
    exp_level = st.slider("Niveau d'experience", 1, 3, 2,
                          help="1: Debutant, 2: Intermediaire, 3: Avance")
    
    # Calcul IMC
    bmi = weight / (height ** 2)
    st.info(f"IMC calcule : {bmi:.1f} kg/m²")
    
    # Bouton de prédiction
    predict_btn = st.button("Lancer la prediction", use_container_width=True)

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
    # Afficher un loader personnalisé
    with st.spinner("Inference neuronale en cours..."):
        time.sleep(0.5)  # Simulation pour l'animation
        
        try:
            # 1. Regression
            calories = predict_calories(model_reg, scaler_reg, features)
            
            # 2. Classification
            class_idx, proba = predict_experience(model_clf, scaler_clf, features_clf)
            levels = ["Debutant", "Intermediaire", "Avance"]
            level_name = levels[class_idx]
            level_symbols = ["[--]", "[-+]", "[++]"]  # Symboles professionnels
            level_symbol = level_symbols[class_idx]
            
            # ------------------------------------------------------------------
            # AFFICHAGE RESULTATS
            # ------------------------------------------------------------------
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.markdown(f"""
                <div class="result-card">
                    <h2>Calories brulees</h2>
                    <p class="result-value">{calories:.0f} <span class="unit">kcal</span></p>
                    <p class="result-sub">Base sur une seance de {duration}h a {avg_bpm} BPM</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Badge CSS selon niveau
                badge_class = f"badge-{level_name.lower()}"
                st.markdown(f"""
                <div class="result-card">
                    <h2>Niveau d'experience</h2>
                    <p class="result-value" style="font-size:2.2rem;">
                        {level_symbol} {level_name}
                    </p>
                    <p class="result-sub">Confiance : {proba[class_idx]*100:.1f}%</p>
                    <span class="badge-level {badge_class}">{level_name}</span>
                </div>
                """, unsafe_allow_html=True)
            
            # ------------------------------------------------------------------
            # METRIQUES
            # ------------------------------------------------------------------
            st.markdown("<h3 style='color:#FF6B00; margin-top:1.5rem;'>ANALYSE DETAILLEE</h3>", unsafe_allow_html=True)
            
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
                    <div class="label">Confiance</div>
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
            st.markdown("<h4 style='color:#FF6B00; margin-top:1rem;'>Distribution des probabilites</h4>", unsafe_allow_html=True)
            
            # Définir les couleurs pour chaque niveau
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
            with st.expander("Interpretation des resultats", expanded=True):
                if calories < 300:
                    cal_analysis = "seance legere, ideale pour un echauffement ou une recuperation."
                elif calories < 600:
                    cal_analysis = "seance moderee, bonne pour maintenir une condition physique."
                elif calories < 900:
                    cal_analysis = "seance intense, excellente pour le developpement musculaire."
                else:
                    cal_analysis = "seance tres intense, niveau athletique !"
                
                if class_idx == 0:
                    exp_analysis = "Vous debutez dans le fitness. Concentrez-vous sur la regularite et la technique."
                elif class_idx == 1:
                    exp_analysis = "Vous avez une bonne base. Augmentez progressivement l'intensite."
                else:
                    exp_analysis = "Vous etes un sportif confirme. Pensez a varier vos exercices."
                
                st.markdown(f"""
                **Analyse de votre profil**
                
                - **Calories** : {calories:.0f} kcal -- {cal_analysis}
                - **Niveau** : {level_symbol} {level_name} -- {exp_analysis}
                - **Cardio** : Votre BPM moyen de {avg_bpm} est { "eleve" if avg_bpm > 160 else "modere" if avg_bpm > 130 else "normal" } pour votre age.
                - **Hydratation** : {water} L/jour -- { "Bon" if water >= 2 else "Pensez a vous hydrater davantage" }
                """)
            
        except Exception as e:
            st.error(f"Erreur lors de la prediction : {e}")

else:
    # Message d'accueil
    st.info("Renseignez vos parametres dans la barre laterale puis cliquez sur 'Lancer la prediction'.")

# ----------------------------------------------------------------------
# FOOTER
# ----------------------------------------------------------------------
st.markdown("""
<div class="footer">
    Developpe avec Streamlit & TensorFlow &bull; Modele entraîne sur le dataset Gym (973 obs.)
    &bull; Predictions a titre indicatif.
</div>
""", unsafe_allow_html=True)