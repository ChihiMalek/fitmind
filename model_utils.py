"""
Model utilities for loading/training and predicting.
TensorFlow remplace par scikit-learn MLPRegressor / MLPClassifier
- Meme architecture : 64 -> 32 -> 16 neurones
- Compatible Python 3.14
- 50x plus leger que TensorFlow
- Interface identique (memes noms de fonctions, memes retours)
"""

import os
import pickle
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.neural_network import MLPRegressor, MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split


# ----------------------------------------------------------------------
# TRAINING FUNCTION
# ----------------------------------------------------------------------
def train_models(data_path='data/gym.csv', models_dir='models'):
    """
    Entraine regression et classification avec sklearn MLP.
    Sauvegarde les modeles dans models_dir.
    Retourne (model_reg, model_clf, scaler_reg, scaler_clf).
    """
    os.makedirs(models_dir, exist_ok=True)

    df = pd.read_csv(data_path)

    # ---- Regression (Calories_Burned) --------------------------------
    features_reg = [
        'Age', 'Gender', 'Weight (kg)', 'Height (m)', 'Avg_BPM',
        'Resting_BPM', 'Session_Duration (hours)', 'Water_Intake (liters)',
        'Workout_Frequency (days/week)', 'Experience_Level', 'BMI'
    ]
    df_reg = df[features_reg + ['Calories_Burned']].copy()
    df_reg['Gender'] = df_reg['Gender'].map({'Male': 0, 'Female': 1})

    X_reg = df_reg[features_reg]
    y_reg = np.log1p(df_reg['Calories_Burned'])   # log transform

    X_train, X_test, y_train, y_test = train_test_split(
        X_reg, y_reg, test_size=0.2, random_state=42
    )
    scaler_reg = StandardScaler()
    X_train_s  = scaler_reg.fit_transform(X_train)

    # MLPRegressor = equivalent Dense(64,32,16,1) relu + adam
    model_reg = MLPRegressor(
        hidden_layer_sizes=(64, 32, 16),
        activation='relu',
        solver='adam',
        max_iter=500,
        early_stopping=True,
        validation_fraction=0.2,
        n_iter_no_change=15,
        random_state=42,
        verbose=False
    )
    model_reg.fit(X_train_s, y_train)

    with open(os.path.join(models_dir, 'regression_model.pkl'), 'wb') as f:
        pickle.dump(model_reg, f)
    with open(os.path.join(models_dir, 'scaler_reg.pkl'), 'wb') as f:
        pickle.dump(scaler_reg, f)

    # ---- Classification (Experience_Level) ---------------------------
    features_clf = [
        'Age', 'Gender', 'Weight (kg)', 'Height (m)', 'Avg_BPM',
        'Resting_BPM', 'Session_Duration (hours)', 'Water_Intake (liters)',
        'Workout_Frequency (days/week)', 'BMI'
    ]
    df_clf = df[features_clf + ['Experience_Level']].copy()
    df_clf['Gender'] = df_clf['Gender'].map({'Male': 0, 'Female': 1})

    X_clf = df_clf[features_clf]
    y_clf = df_clf['Experience_Level'] - 1   # 0, 1, 2

    X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(
        X_clf, y_clf, test_size=0.2, random_state=42, stratify=y_clf
    )
    scaler_clf  = StandardScaler()
    X_train_cs  = scaler_clf.fit_transform(X_train_c)

    # MLPClassifier = equivalent Dense(64,32,16,3 softmax) relu + adam
    model_clf = MLPClassifier(
        hidden_layer_sizes=(64, 32, 16),
        activation='relu',
        solver='adam',
        max_iter=500,
        early_stopping=True,
        validation_fraction=0.2,
        n_iter_no_change=20,
        random_state=42,
        verbose=False
    )
    model_clf.fit(X_train_cs, y_train_c)

    with open(os.path.join(models_dir, 'classification_model.pkl'), 'wb') as f:
        pickle.dump(model_clf, f)
    with open(os.path.join(models_dir, 'scaler_clf.pkl'), 'wb') as f:
        pickle.dump(scaler_clf, f)

    return model_reg, model_clf, scaler_reg, scaler_clf


# ----------------------------------------------------------------------
# LOADING — @st.cache_resource evite le re-entrainement a chaque reload
# ----------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def load_or_train_models(models_dir='models', data_path='data/gym.csv'):
    """
    Charge les modeles depuis le disque si presents,
    sinon les entraine (une seule fois grace au cache).
    """
    reg_path = os.path.join(models_dir, 'regression_model.pkl')
    clf_path = os.path.join(models_dir, 'classification_model.pkl')
    sr_path  = os.path.join(models_dir, 'scaler_reg.pkl')
    sc_path  = os.path.join(models_dir, 'scaler_clf.pkl')

    if all(os.path.exists(p) for p in [reg_path, clf_path, sr_path, sc_path]):
        try:
            with open(reg_path, 'rb') as f: model_reg  = pickle.load(f)
            with open(clf_path, 'rb') as f: model_clf  = pickle.load(f)
            with open(sr_path,  'rb') as f: scaler_reg = pickle.load(f)
            with open(sc_path,  'rb') as f: scaler_clf = pickle.load(f)
            return model_reg, model_clf, scaler_reg, scaler_clf
        except Exception:
            pass   # fichier corrompu → ré-entraîner

    return train_models(data_path, models_dir)


# ----------------------------------------------------------------------
# PREDICTIONS — interface identique a l'originale
# ----------------------------------------------------------------------
def predict_calories(model_reg, scaler_reg, features: dict) -> float:
    """Predit les calories brulees (kcal)."""
    feature_order = [
        'Age', 'Gender', 'Weight (kg)', 'Height (m)', 'Avg_BPM',
        'Resting_BPM', 'Session_Duration (hours)', 'Water_Intake (liters)',
        'Workout_Frequency (days/week)', 'Experience_Level', 'BMI'
    ]
    X         = np.array([[features[k] for k in feature_order]])
    pred_log  = model_reg.predict(scaler_reg.transform(X))[0]
    return float(np.expm1(pred_log))


def predict_experience(model_clf, scaler_clf, features: dict):
    """Predit le niveau d'experience (0,1,2) et les probabilites."""
    feature_order = [
        'Age', 'Gender', 'Weight (kg)', 'Height (m)', 'Avg_BPM',
        'Resting_BPM', 'Session_Duration (hours)', 'Water_Intake (liters)',
        'Workout_Frequency (days/week)', 'BMI'
    ]
    X     = np.array([[features[k] for k in feature_order]])
    proba = model_clf.predict_proba(scaler_clf.transform(X))[0]
    return int(np.argmax(proba)), proba
