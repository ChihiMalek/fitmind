"""
Model utilities for loading/training and predicting.
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Dropout, Input
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.utils import to_categorical

# ----------------------------------------------------------------------
# TRAINING FUNCTION (if models are missing)
# ----------------------------------------------------------------------
def train_models(data_path='data/gym.csv', models_dir='models'):
    """
    Train regression and classification models from scratch.
    Saves models and scalers in models_dir.
    Returns (model_reg, model_clf, scaler_reg, scaler_clf).
    """
    os.makedirs(models_dir, exist_ok=True)
    
    # Load dataset
    df = pd.read_csv(data_path)
    
    # ---- Regression ----
    features_reg = ['Age', 'Gender', 'Weight (kg)', 'Height (m)', 'Avg_BPM',
                    'Resting_BPM', 'Session_Duration (hours)', 'Water_Intake (liters)',
                    'Workout_Frequency (days/week)', 'Experience_Level', 'BMI']
    target_reg = 'Calories_Burned'
    
    df_reg = df[features_reg + [target_reg]].copy()
    df_reg['Gender'] = df_reg['Gender'].map({'Male': 0, 'Female': 1})
    
    X_reg = df_reg[features_reg]
    y_reg = df_reg[target_reg]
    y_reg_log = np.log1p(y_reg)  # log transform for stability
    
    X_train, X_test, y_train_log, y_test_log = train_test_split(
        X_reg, y_reg_log, test_size=0.2, random_state=42
    )
    
    scaler_reg = StandardScaler()
    X_train_scaled = scaler_reg.fit_transform(X_train)
    X_test_scaled = scaler_reg.transform(X_test)
    
    model_reg = Sequential([
        Input(shape=(X_train_scaled.shape[1],)),
        Dense(64, activation='relu'),
        Dropout(0.2),
        Dense(32, activation='relu'),
        Dropout(0.1),
        Dense(16, activation='relu'),
        Dense(1)
    ])
    model_reg.compile(optimizer='adam', loss='mse', metrics=['mae'])
    early_stop = EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True)
    model_reg.fit(X_train_scaled, y_train_log,
                  validation_split=0.2, epochs=150, batch_size=32,
                  callbacks=[early_stop], verbose=0)
    
    model_reg.save(os.path.join(models_dir, 'regression_model.keras'))
    with open(os.path.join(models_dir, 'scaler_reg.pkl'), 'wb') as f:
        pickle.dump(scaler_reg, f)
    
    # ---- Classification ----
    features_clf = ['Age', 'Gender', 'Weight (kg)', 'Height (m)', 'Avg_BPM',
                    'Resting_BPM', 'Session_Duration (hours)', 'Water_Intake (liters)',
                    'Workout_Frequency (days/week)', 'BMI']
    target_clf = 'Experience_Level'
    
    df_clf = df[features_clf + [target_clf]].copy()
    df_clf['Gender'] = df_clf['Gender'].map({'Male': 0, 'Female': 1})
    
    X_clf = df_clf[features_clf]
    y_clf = df_clf[target_clf] - 1  # shift to 0,1,2
    
    X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(
        X_clf, y_clf, test_size=0.2, random_state=42, stratify=y_clf
    )
    
    scaler_clf = StandardScaler()
    X_train_c_scaled = scaler_clf.fit_transform(X_train_c)
    X_test_c_scaled = scaler_clf.transform(X_test_c)
    
    y_train_cat = to_categorical(y_train_c, num_classes=3)
    
    model_clf = Sequential([
        Input(shape=(X_train_c_scaled.shape[1],)),
        Dense(64, activation='relu'),
        Dropout(0.3),
        Dense(32, activation='relu'),
        Dropout(0.2),
        Dense(16, activation='relu'),
        Dense(3, activation='softmax')
    ])
    model_clf.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    early_stop_c = EarlyStopping(monitor='val_accuracy', patience=20,
                                 restore_best_weights=True, mode='max')
    model_clf.fit(X_train_c_scaled, y_train_cat,
                  epochs=200, batch_size=32, validation_split=0.2,
                  callbacks=[early_stop_c], verbose=0)
    
    model_clf.save(os.path.join(models_dir, 'classification_model.keras'))
    with open(os.path.join(models_dir, 'scaler_clf.pkl'), 'wb') as f:
        pickle.dump(scaler_clf, f)
    
    return model_reg, model_clf, scaler_reg, scaler_clf

# ----------------------------------------------------------------------
# LOADING FUNCTION (with fallback to training)
# ----------------------------------------------------------------------
def load_or_train_models(models_dir='models', data_path='data/gym.csv'):
    """
    Load models from disk if present, otherwise train them.
    Returns (model_reg, model_clf, scaler_reg, scaler_clf).
    """
    try:
        model_reg = load_model(os.path.join(models_dir, 'regression_model.keras'))
        model_clf = load_model(os.path.join(models_dir, 'classification_model.keras'))
        with open(os.path.join(models_dir, 'scaler_reg.pkl'), 'rb') as f:
            scaler_reg = pickle.load(f)
        with open(os.path.join(models_dir, 'scaler_clf.pkl'), 'rb') as f:
            scaler_clf = pickle.load(f)
        return model_reg, model_clf, scaler_reg, scaler_clf
    except (FileNotFoundError, OSError):
        # Train if missing
        return train_models(data_path, models_dir)

# ----------------------------------------------------------------------
# PREDICTION FUNCTIONS
# ----------------------------------------------------------------------
def predict_calories(model_reg, scaler_reg, features):
    """
    Predict calories burned (kcal) from input features dict.
    Features must contain all 11 variables.
    """
    # Order must match training
    feature_order = ['Age', 'Gender', 'Weight (kg)', 'Height (m)', 'Avg_BPM',
                     'Resting_BPM', 'Session_Duration (hours)', 'Water_Intake (liters)',
                     'Workout_Frequency (days/week)', 'Experience_Level', 'BMI']
    X = np.array([[features[k] for k in feature_order]])
    X_scaled = scaler_reg.transform(X)
    pred_log = model_reg.predict(X_scaled, verbose=0)[0][0]
    return np.expm1(pred_log)

def predict_experience(model_clf, scaler_clf, features):
    """
    Predict experience level (0,1,2) and class probabilities.
    features: dict with 10 variables (excluding Experience_Level).
    Returns (pred_class, probabilities array).
    """
    feature_order = ['Age', 'Gender', 'Weight (kg)', 'Height (m)', 'Avg_BPM',
                     'Resting_BPM', 'Session_Duration (hours)', 'Water_Intake (liters)',
                     'Workout_Frequency (days/week)', 'BMI']
    X = np.array([[features[k] for k in feature_order]])
    X_scaled = scaler_clf.transform(X)
    proba = model_clf.predict(X_scaled, verbose=0)[0]
    return int(np.argmax(proba)), proba