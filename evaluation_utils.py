"""
Evaluation utilities for FitMind AI.

Fournit les fonctions de chargement des metadonnees de modeles et la
construction des graphiques Plotly utilises par les pages Streamlit
"Model Evaluation" et "Model Information".

Toutes les metriques affichees proviennent directement de
models/model_metadata.json, genere automatiquement par
model_utils.train_models() a chaque entrainement — rien n'est recalcule
ni invente ici.
"""

import json
import os

import numpy as np
import plotly.graph_objects as go


def load_metadata(models_dir='models'):
    path = os.path.join(models_dir, 'model_metadata.json')
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ----------------------------------------------------------------------
# GRAPHIQUES — COURBES D'ENTRAINEMENT / VALIDATION
# ----------------------------------------------------------------------
def training_curves_figure(history: dict, loss_key='loss', val_loss_key='val_loss',
                            title='Courbe de perte (Loss)', y_title='Loss'):
    epochs = list(range(1, len(history[loss_key]) + 1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=epochs, y=history[loss_key], mode='lines',
                              name='Train', line=dict(color='#3A8FD4', width=2)))
    if val_loss_key in history:
        fig.add_trace(go.Scatter(x=epochs, y=history[val_loss_key], mode='lines',
                                  name='Validation', line=dict(color='#D4A830', width=2)))
    fig.update_layout(
        title=title, xaxis_title='Epoque', yaxis_title=y_title,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(8,16,28,.6)',
        height=280, margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation='h', y=1.15),
        font=dict(family='Rajdhani', color='#C5DFF0'),
        xaxis=dict(gridcolor='rgba(58,143,212,.08)'),
        yaxis=dict(gridcolor='rgba(58,143,212,.08)'),
    )
    return fig


def accuracy_curves_figure(history: dict):
    acc_key = 'accuracy' if 'accuracy' in history else None
    val_acc_key = 'val_accuracy' if 'val_accuracy' in history else None
    if not acc_key:
        return None
    epochs = list(range(1, len(history[acc_key]) + 1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=epochs, y=history[acc_key], mode='lines',
                              name='Train', line=dict(color='#3A8FD4', width=2)))
    if val_acc_key in history:
        fig.add_trace(go.Scatter(x=epochs, y=history[val_acc_key], mode='lines',
                                  name='Validation', line=dict(color='#D4A830', width=2)))
    fig.update_layout(
        title='Courbe de precision (Accuracy)', xaxis_title='Epoque', yaxis_title='Accuracy',
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(8,16,28,.6)',
        height=280, margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation='h', y=1.15),
        font=dict(family='Rajdhani', color='#C5DFF0'),
        xaxis=dict(gridcolor='rgba(58,143,212,.08)'),
        yaxis=dict(gridcolor='rgba(58,143,212,.08)', range=[0, 1]),
    )
    return fig


# ----------------------------------------------------------------------
# MATRICE DE CONFUSION
# ----------------------------------------------------------------------
def confusion_matrix_figure(cm, class_names, title='Matrice de confusion'):
    cm = np.array(cm)
    fig = go.Figure(data=go.Heatmap(
        z=cm, x=class_names, y=class_names,
        colorscale=[[0, '#08111E'], [1, '#3A8FD4']],
        text=cm, texttemplate='%{text}', textfont=dict(size=14, color='#E8F4FF'),
        showscale=False,
    ))
    fig.update_layout(
        title=title, xaxis_title='Predit', yaxis_title='Reel',
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(8,16,28,.6)',
        height=320, margin=dict(l=10, r=10, t=40, b=10),
        font=dict(family='Rajdhani', color='#C5DFF0'),
        yaxis=dict(autorange='reversed'),
    )
    return fig


# ----------------------------------------------------------------------
# HELPERS D'AFFICHAGE
# ----------------------------------------------------------------------
def metric_rows(metrics: dict, keys_labels):
    """Retourne une liste de tuples (label, valeur formattee) pour affichage."""
    rows = []
    for key, label, fmt in keys_labels:
        if key in metrics:
            rows.append((label, fmt.format(metrics[key])))
    return rows
