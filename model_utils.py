"""
Model utilities for loading/training and predicting.

FitMind AI — moteur de modeles (regression calories, classification niveau
d'experience, classification Workout_Type demonstrative).

Ce module gere :
  - la reproductibilite (seeds)
  - l'entrainement des 3 modeles
  - le calcul automatique des metriques d'evaluation (test set)
  - le calcul des statistiques de distribution des features d'entrainement
    (utilisees par app.py pour le systeme de validation intelligent des
    entrees utilisateur)
  - la sauvegarde d'un fichier de metadonnees models/model_metadata.json
    consomme par les pages "Model Evaluation" et "Model Information"
  - les fonctions de prediction (inference)
"""

import os
import json
import pickle
import random
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
)

import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Dropout, Input
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.utils import to_categorical

MODEL_VERSION = "1.1.0"

# ----------------------------------------------------------------------
# REPRODUCTIBILITE
# ----------------------------------------------------------------------
SEED = 42


def set_seeds(seed: int = SEED):
    """
    Fixe les graines aleatoires pour rendre l'entrainement reproductible.

    Pourquoi :
        Sans seed fixe, l'initialisation des poids du reseau de neurones
        et le tirage aleatoire du Dropout changent a chaque execution.
        Sur ce projet, cela a ete mesure : le R2 du modele de regression
        variait de 0.72 a 0.94 selon le run (3 entrainements identiques,
        seule difference : l'alea non controle). Fixer les seeds elimine
        cette source de variance et garantit qu'un meme code + meme
        dataset produit un modele reproductible.

    Limites connues (a documenter honnetement) :
        - `random.seed` et `np.random.seed` sont deterministes sur toutes
          les plateformes.
        - `tf.random.set_seed` fixe le generateur global de TensorFlow,
          mais certaines operations restent non deterministes par nature :
          * calculs sur GPU (cuDNN) : l'ordre de sommation en parallele
            peut varier legerement d'une execution a l'autre (non
            deterministe au niveau du bit) ;
          * multi-threading CPU : `tf.config.threading` peut aussi
            introduire de petites variations si plusieurs threads sont
            utilises pour les operations de reduction.
        - Ce projet tourne en `tensorflow-cpu`, ce qui limite ce risque,
          mais ne l'elimine pas totalement selon le nombre de coeurs
          disponibles sur la machine d'entrainement.
        - Un changement de version de TensorFlow, de systeme d'exploitation
          ou de nombre de coeurs CPU peut donc, dans de rares cas, produire
          un resultat legerement different meme a seed egal. Les seeds
          reduisent la variance de facon tres significative, mais ne
          garantissent pas un bit-a-bit identique a 100% entre machines.
    """
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)


# ----------------------------------------------------------------------
# CONSTANTES — FEATURES
# ----------------------------------------------------------------------
FEATURES_REG = ['Age', 'Gender', 'Weight (kg)', 'Height (m)', 'Avg_BPM',
                 'Resting_BPM', 'Session_Duration (hours)', 'Water_Intake (liters)',
                 'Workout_Frequency (days/week)', 'Experience_Level', 'BMI']
TARGET_REG = 'Calories_Burned'

FEATURES_CLF = ['Age', 'Gender', 'Weight (kg)', 'Height (m)', 'Avg_BPM',
                 'Resting_BPM', 'Session_Duration (hours)', 'Water_Intake (liters)',
                 'Workout_Frequency (days/week)', 'BMI']
TARGET_CLF = 'Experience_Level'

FEATURES_WORKOUT = FEATURES_CLF.copy()  # memes features physiologiques
TARGET_WORKOUT = 'Workout_Type'

LEVEL_NAMES = ["Debutant", "Intermediaire", "Avance"]

# Note pedagogique honnete affichee partout ou la prediction Workout_Type
# est utilisee dans l'app — a ne jamais retirer ni adoucir.
WORKOUT_TYPE_DISCLAIMER = (
    "Modele demonstratif : une analyse de correlation et un test avec "
    "RandomForest (100% train / ~24% test, en dessous de la baseline "
    "'toujours predire la classe majoritaire' a 26.5%) montrent que "
    "Workout_Type n'est quasiment pas correle aux variables physiologiques "
    "disponibles (correlation max ≈ 0.05). Ce modele est conserve a titre "
    "pedagogique pour illustrer un cas ou le Deep Learning ne peut pas "
    "extraire de signal absent des donnees. Sa prediction ne doit jamais "
    "etre presentee comme fiable."
)


# ----------------------------------------------------------------------
# STATISTIQUES DE DISTRIBUTION (pour la validation intelligente des inputs)
# ----------------------------------------------------------------------
def compute_feature_distributions(df: pd.DataFrame, features: list) -> dict:
    """
    Calcule min/max/mean/std/p5/p95 pour chaque feature d'entrainement.
    Utilise par app.py pour classer une valeur saisie par l'utilisateur en
    zone verte / jaune / rouge par rapport a la distribution reellement vue
    pendant l'entrainement.
    """
    stats = {}
    for f in features:
        col = df[f]
        stats[f] = {
            'min': float(col.min()),
            'max': float(col.max()),
            'mean': float(col.mean()),
            'std': float(col.std()),
            'p5': float(col.quantile(0.05)),
            'p95': float(col.quantile(0.95)),
        }
    return stats


# ----------------------------------------------------------------------
# METRIQUES D'EVALUATION
# ----------------------------------------------------------------------
def _regression_metrics(y_true, y_pred):
    return {
        'mae': float(mean_absolute_error(y_true, y_pred)),
        'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred))),
        'r2': float(r2_score(y_true, y_pred)),
    }


def _classification_metrics(y_true, y_pred, class_names):
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(class_names))))
    return {
        'accuracy': float(accuracy_score(y_true, y_pred)),
        'precision_macro': float(precision_score(y_true, y_pred, average='macro', zero_division=0)),
        'recall_macro': float(recall_score(y_true, y_pred, average='macro', zero_division=0)),
        'f1_macro': float(f1_score(y_true, y_pred, average='macro', zero_division=0)),
        'confusion_matrix': cm.tolist(),
        'class_names': class_names,
    }


def _history_to_dict(history):
    return {k: [float(v) for v in vals] for k, vals in history.history.items()}


# ----------------------------------------------------------------------
# TRAINING FUNCTION
# ----------------------------------------------------------------------
def train_models(data_path='data/gym.csv', models_dir='models'):
    """
    Entraine les 3 modeles (regression calories, classification niveau
    d'experience, classification demonstrative Workout_Type), calcule
    automatiquement leurs metriques sur le jeu de test, et sauvegarde :
      - les modeles .keras + scalers .pkl
      - models/model_metadata.json (metriques, historique, hyperparametres,
        plages de distribution, version, date)

    Retourne (model_reg, model_clf, model_wt, scaler_reg, scaler_clf,
    scaler_wt, metadata).
    """
    set_seeds(SEED)
    os.makedirs(models_dir, exist_ok=True)

    df = pd.read_csv(data_path)
    trained_at = datetime.now().isoformat(timespec='seconds')

    # Statistiques auxiliaires : variables du dataset qui ne sont PAS des
    # entrees de modele (Max_BPM, Fat_Percentage) mais que l'UI (Dashboard,
    # futures pages Analytics) peut vouloir afficher/valider honnetement.
    auxiliary_distributions = compute_feature_distributions(df, ['Max_BPM', 'Fat_Percentage'])

    metadata = {
        'version': MODEL_VERSION,
        'trained_at': trained_at,
        'seed': SEED,
        'reproducibility_note': (
            "Seeds fixees (random, numpy, tensorflow) pour limiter la "
            "variance d'entrainement. Determinisme non garanti a 100% : "
            "certaines operations TensorFlow (notamment sur GPU/cuDNN, ou "
            "selon le nombre de coeurs CPU utilises) restent susceptibles "
            "de produire de tres legeres variations d'une machine a l'autre."
        ),
        'dataset': {
            'path': data_path,
            'n_samples': int(len(df)),
        },
        'auxiliary_feature_distributions': auxiliary_distributions,
    }

    # ============================================================
    # 1) REGRESSION — Calories_Burned
    # ============================================================
    df_reg = df[FEATURES_REG + [TARGET_REG]].copy()
    df_reg['Gender'] = df_reg['Gender'].map({'Male': 0, 'Female': 1})

    X_reg = df_reg[FEATURES_REG]
    y_reg = df_reg[TARGET_REG]
    y_reg_log = np.log1p(y_reg)

    X_train, X_test, y_train_log, y_test_log = train_test_split(
        X_reg, y_reg_log, test_size=0.2, random_state=SEED
    )

    scaler_reg = StandardScaler()
    X_train_scaled = scaler_reg.fit_transform(X_train)
    X_test_scaled = scaler_reg.transform(X_test)

    reg_hparams = {
        'optimizer': 'adam', 'loss': 'mse', 'metrics': ['mae'],
        'epochs_max': 150, 'batch_size': 32,
        'early_stopping_monitor': 'val_loss', 'early_stopping_patience': 15,
        'validation_split': 0.2,
    }

    model_reg = Sequential([
        Input(shape=(X_train_scaled.shape[1],)),
        Dense(64, activation='relu'),
        Dropout(0.2),
        Dense(32, activation='relu'),
        Dropout(0.1),
        Dense(16, activation='relu'),
        Dense(1)
    ])
    model_reg.compile(optimizer=reg_hparams['optimizer'], loss=reg_hparams['loss'],
                       metrics=reg_hparams['metrics'])
    early_stop = EarlyStopping(monitor=reg_hparams['early_stopping_monitor'],
                                patience=reg_hparams['early_stopping_patience'],
                                restore_best_weights=True)
    history_reg = model_reg.fit(X_train_scaled, y_train_log,
                                 validation_split=reg_hparams['validation_split'],
                                 epochs=reg_hparams['epochs_max'], batch_size=reg_hparams['batch_size'],
                                 callbacks=[early_stop], verbose=0)

    model_reg.save(os.path.join(models_dir, 'regression_model.keras'))
    with open(os.path.join(models_dir, 'scaler_reg.pkl'), 'wb') as f:
        pickle.dump(scaler_reg, f)

    y_pred_log = model_reg.predict(X_test_scaled, verbose=0).flatten()
    y_pred_kcal = np.expm1(y_pred_log)
    y_test_kcal = np.expm1(y_test_log)

    metadata['regression'] = {
        'target': TARGET_REG,
        'features': FEATURES_REG,
        'architecture': ['Dense(64, relu)', 'Dropout(0.2)', 'Dense(32, relu)',
                          'Dropout(0.1)', 'Dense(16, relu)', 'Dense(1, linear)'],
        'hyperparameters': reg_hparams,
        'target_transform': 'log1p (inverse: expm1)',
        'epochs_trained': len(history_reg.history['loss']),
        'n_train': int(len(X_train)), 'n_test': int(len(X_test)),
        'metrics_test': _regression_metrics(y_test_kcal, y_pred_kcal),
        'history': _history_to_dict(history_reg),
        'feature_distributions': compute_feature_distributions(X_train, FEATURES_REG),
    }

    # ============================================================
    # 2) CLASSIFICATION — Experience_Level (modele conserve tel quel)
    # ============================================================
    df_clf = df[FEATURES_CLF + [TARGET_CLF]].copy()
    df_clf['Gender'] = df_clf['Gender'].map({'Male': 0, 'Female': 1})

    X_clf = df_clf[FEATURES_CLF]
    y_clf = df_clf[TARGET_CLF] - 1

    X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(
        X_clf, y_clf, test_size=0.2, random_state=SEED, stratify=y_clf
    )

    scaler_clf = StandardScaler()
    X_train_c_scaled = scaler_clf.fit_transform(X_train_c)
    X_test_c_scaled = scaler_clf.transform(X_test_c)

    y_train_cat = to_categorical(y_train_c, num_classes=3)

    clf_hparams = {
        'optimizer': 'adam', 'loss': 'categorical_crossentropy', 'metrics': ['accuracy'],
        'epochs_max': 200, 'batch_size': 32,
        'early_stopping_monitor': 'val_accuracy', 'early_stopping_patience': 20,
        'validation_split': 0.2,
    }

    model_clf = Sequential([
        Input(shape=(X_train_c_scaled.shape[1],)),
        Dense(64, activation='relu'),
        Dropout(0.3),
        Dense(32, activation='relu'),
        Dropout(0.2),
        Dense(16, activation='relu'),
        Dense(3, activation='softmax')
    ])
    model_clf.compile(optimizer=clf_hparams['optimizer'], loss=clf_hparams['loss'],
                       metrics=clf_hparams['metrics'])
    early_stop_c = EarlyStopping(monitor=clf_hparams['early_stopping_monitor'],
                                  patience=clf_hparams['early_stopping_patience'],
                                  restore_best_weights=True, mode='max')
    history_clf = model_clf.fit(X_train_c_scaled, y_train_cat,
                                 epochs=clf_hparams['epochs_max'], batch_size=clf_hparams['batch_size'],
                                 validation_split=clf_hparams['validation_split'],
                                 callbacks=[early_stop_c], verbose=0)

    model_clf.save(os.path.join(models_dir, 'classification_model.keras'))
    with open(os.path.join(models_dir, 'scaler_clf.pkl'), 'wb') as f:
        pickle.dump(scaler_clf, f)

    proba_test = model_clf.predict(X_test_c_scaled, verbose=0)
    y_pred_c = np.argmax(proba_test, axis=1)

    metadata['classification_experience'] = {
        'target': TARGET_CLF,
        'features': FEATURES_CLF,
        'architecture': ['Dense(64, relu)', 'Dropout(0.3)', 'Dense(32, relu)',
                          'Dropout(0.2)', 'Dense(16, relu)', 'Dense(3, softmax)'],
        'hyperparameters': clf_hparams,
        'epochs_trained': len(history_clf.history['loss']),
        'n_train': int(len(X_train_c)), 'n_test': int(len(X_test_c)),
        'metrics_test': _classification_metrics(y_test_c.values, y_pred_c, LEVEL_NAMES),
        'history': _history_to_dict(history_clf),
        'feature_distributions': compute_feature_distributions(X_train_c, FEATURES_CLF),
        'is_reliable': True,
    }

    # ============================================================
    # 3) CLASSIFICATION DEMONSTRATIVE — Workout_Type (nouveau, honnete)
    # ============================================================
    df_wt = df[FEATURES_WORKOUT + [TARGET_WORKOUT]].copy()
    df_wt['Gender'] = df_wt['Gender'].map({'Male': 0, 'Female': 1})

    wt_encoder = LabelEncoder()
    y_wt = wt_encoder.fit_transform(df_wt[TARGET_WORKOUT])
    wt_class_names = list(wt_encoder.classes_)
    X_wt = df_wt[FEATURES_WORKOUT]

    X_train_w, X_test_w, y_train_w, y_test_w = train_test_split(
        X_wt, y_wt, test_size=0.2, random_state=SEED, stratify=y_wt
    )

    scaler_wt = StandardScaler()
    X_train_w_scaled = scaler_wt.fit_transform(X_train_w)
    X_test_w_scaled = scaler_wt.transform(X_test_w)

    y_train_w_cat = to_categorical(y_train_w, num_classes=len(wt_class_names))

    wt_hparams = {
        'optimizer': 'adam', 'loss': 'categorical_crossentropy', 'metrics': ['accuracy'],
        'epochs_max': 150, 'batch_size': 32,
        'early_stopping_monitor': 'val_loss', 'early_stopping_patience': 15,
        'validation_split': 0.2,
    }

    model_wt = Sequential([
        Input(shape=(X_train_w_scaled.shape[1],)),
        Dense(32, activation='relu'),
        Dropout(0.3),
        Dense(16, activation='relu'),
        Dense(len(wt_class_names), activation='softmax')
    ])
    model_wt.compile(optimizer=wt_hparams['optimizer'], loss=wt_hparams['loss'],
                      metrics=wt_hparams['metrics'])
    early_stop_w = EarlyStopping(monitor=wt_hparams['early_stopping_monitor'],
                                  patience=wt_hparams['early_stopping_patience'],
                                  restore_best_weights=True)
    history_wt = model_wt.fit(X_train_w_scaled, y_train_w_cat,
                               epochs=wt_hparams['epochs_max'], batch_size=wt_hparams['batch_size'],
                               validation_split=wt_hparams['validation_split'],
                               callbacks=[early_stop_w], verbose=0)

    model_wt.save(os.path.join(models_dir, 'workout_type_model.keras'))
    with open(os.path.join(models_dir, 'scaler_workout.pkl'), 'wb') as f:
        pickle.dump(scaler_wt, f)
    with open(os.path.join(models_dir, 'workout_type_encoder.pkl'), 'wb') as f:
        pickle.dump(wt_encoder, f)

    proba_test_w = model_wt.predict(X_test_w_scaled, verbose=0)
    y_pred_w = np.argmax(proba_test_w, axis=1)
    majority_baseline = float(pd.Series(y_train_w).value_counts(normalize=True).max())

    metadata['classification_workout_type'] = {
        'target': TARGET_WORKOUT,
        'features': FEATURES_WORKOUT,
        'architecture': ['Dense(32, relu)', 'Dropout(0.3)', 'Dense(16, relu)',
                          f'Dense({len(wt_class_names)}, softmax)'],
        'hyperparameters': wt_hparams,
        'epochs_trained': len(history_wt.history['loss']),
        'n_train': int(len(X_train_w)), 'n_test': int(len(X_test_w)),
        'metrics_test': _classification_metrics(y_test_w, y_pred_w, wt_class_names),
        'majority_class_baseline_accuracy': majority_baseline,
        'history': _history_to_dict(history_wt),
        'feature_distributions': compute_feature_distributions(X_train_w, FEATURES_WORKOUT),
        'is_reliable': False,
        'disclaimer': WORKOUT_TYPE_DISCLAIMER,
    }

    with open(os.path.join(models_dir, 'model_metadata.json'), 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return model_reg, model_clf, model_wt, scaler_reg, scaler_clf, scaler_wt, metadata


# ----------------------------------------------------------------------
# LOADING FUNCTION (with fallback to training)
# ----------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def load_or_train_models(models_dir='models', data_path='data/gym.csv'):
    """
    Charge les modeles + metadonnees depuis le disque, ou reentraine si
    absents. Retourne (model_reg, model_clf, model_wt, scaler_reg,
    scaler_clf, scaler_wt, wt_encoder, metadata).
    """
    try:
        model_reg = load_model(os.path.join(models_dir, 'regression_model.keras'))
        model_clf = load_model(os.path.join(models_dir, 'classification_model.keras'))
        model_wt = load_model(os.path.join(models_dir, 'workout_type_model.keras'))
        with open(os.path.join(models_dir, 'scaler_reg.pkl'), 'rb') as f:
            scaler_reg = pickle.load(f)
        with open(os.path.join(models_dir, 'scaler_clf.pkl'), 'rb') as f:
            scaler_clf = pickle.load(f)
        with open(os.path.join(models_dir, 'scaler_workout.pkl'), 'rb') as f:
            scaler_wt = pickle.load(f)
        with open(os.path.join(models_dir, 'workout_type_encoder.pkl'), 'rb') as f:
            wt_encoder = pickle.load(f)
        with open(os.path.join(models_dir, 'model_metadata.json'), 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        return (model_reg, model_clf, model_wt, scaler_reg, scaler_clf,
                scaler_wt, wt_encoder, metadata)
    except (FileNotFoundError, OSError, ValueError):
        # ValueError : Keras >= 3 leve ValueError (pas FileNotFoundError) quand
        # un fichier .keras est absent. Sans ce cas, le fallback vers
        # l'entrainement automatique ne se declenchait jamais (bug preexistant).
        model_reg, model_clf, model_wt, scaler_reg, scaler_clf, scaler_wt, metadata = \
            train_models(data_path, models_dir)
        with open(os.path.join(models_dir, 'workout_type_encoder.pkl'), 'rb') as f:
            wt_encoder = pickle.load(f)
        return (model_reg, model_clf, model_wt, scaler_reg, scaler_clf,
                scaler_wt, wt_encoder, metadata)


# ----------------------------------------------------------------------
# PREDICTION FUNCTIONS
# ----------------------------------------------------------------------
def predict_calories(model_reg, scaler_reg, features):
    """Predit les calories brulees (kcal) a partir d'un dict de 11 features."""
    X = np.array([[features[k] for k in FEATURES_REG]])
    X_scaled = scaler_reg.transform(X)
    pred_log = model_reg.predict(X_scaled, verbose=0)[0][0]
    return np.expm1(pred_log)


def predict_experience(model_clf, scaler_clf, features):
    """Predit le niveau d'experience (0,1,2) + probabilites (10 features)."""
    X = np.array([[features[k] for k in FEATURES_CLF]])
    X_scaled = scaler_clf.transform(X)
    proba = model_clf.predict(X_scaled, verbose=0)[0]
    return int(np.argmax(proba)), proba


def predict_workout_type(model_wt, scaler_wt, wt_encoder, features):
    """
    Predit le Workout_Type (demonstratif, non fiable — voir
    WORKOUT_TYPE_DISCLAIMER). Retourne (nom_classe, probabilites, class_names).
    """
    X = np.array([[features[k] for k in FEATURES_WORKOUT]])
    X_scaled = scaler_wt.transform(X)
    proba = model_wt.predict(X_scaled, verbose=0)[0]
    idx = int(np.argmax(proba))
    class_names = list(wt_encoder.classes_)
    return class_names[idx], proba, class_names


# ----------------------------------------------------------------------
# VALIDATION INTELLIGENTE DES ENTREES (systeme 🟢🟡🔴)
# ----------------------------------------------------------------------
def check_feature_status(value: float, stats: dict, yellow_margin: float = 0.15):
    """
    Classe une valeur saisie par l'utilisateur par rapport a la distribution
    d'entrainement d'une feature.

    🟢 green  : value dans [min, max] observes a l'entrainement.
    🟡 yellow : value en dehors de [min, max] mais dans une marge de
                tolerance de `yellow_margin` (15% par defaut) de l'etendue
                (max-min) au-dela des bornes.
    🔴 red    : value au-dela de cette marge — le modele extrapole
                fortement, la prediction est peu fiable.

    Retourne un dict {'status': 'green'|'yellow'|'red', 'message': str}.
    """
    vmin, vmax = stats['min'], stats['max']
    span = max(vmax - vmin, 1e-9)
    margin = span * yellow_margin

    if vmin <= value <= vmax:
        return {'status': 'green',
                'message': f"Dans la plage d'entrainement ({vmin:.1f} – {vmax:.1f})."}
    if (vmin - margin) <= value <= (vmax + margin):
        return {'status': 'yellow',
                'message': f"Proche de la limite d'entrainement ({vmin:.1f} – {vmax:.1f}). "
                            "Le modele commence a extrapoler."}
    return {'status': 'red',
            'message': f"Hors de la plage d'entrainement ({vmin:.1f} – {vmax:.1f}). "
                        "Le modele extrapole fortement : la prediction est peu fiable."}


def compute_global_confidence(features: dict, feature_distributions: dict, yellow_margin: float = 0.15):
    """
    Indicateur de confiance global (0-100%) base sur la proportion de
    variables dans/hors distribution : vert=1.0, jaune=0.5, rouge=0.0,
    moyenne sur toutes les features fournies.

    Retourne {'score': float 0-100, 'level': 'green'|'yellow'|'red',
    'details': {feature: status_dict}}.
    """
    weights = {'green': 1.0, 'yellow': 0.5, 'red': 0.0}
    details = {}
    total = 0.0
    n = 0
    for feat, value in features.items():
        if feat not in feature_distributions:
            continue
        status = check_feature_status(value, feature_distributions[feat], yellow_margin)
        details[feat] = status
        total += weights[status['status']]
        n += 1

    score = (total / n * 100) if n else 100.0
    if score >= 85:
        level = 'green'
    elif score >= 60:
        level = 'yellow'
    else:
        level = 'red'
    return {'score': score, 'level': level, 'details': details}
