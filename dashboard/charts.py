"""
charts.py — figures Plotly du Dashboard.

Ces fonctions ne font aucune mise en page Streamlit (pas de st.columns) et
ne lisent aucune donnee de session : elles recoivent des valeurs deja
extraites et retournent un go.Figure, affiche ensuite par layout.py via
st.plotly_chart.
"""

import plotly.graph_objects as go

_FONT = dict(family='Rajdhani', color='#C5DFF0')
_PAPER = 'rgba(0,0,0,0)'
_PLOT = 'rgba(8,16,28,.6)'


def _base_layout(fig, height=220, **kwargs):
    fig.update_layout(
        paper_bgcolor=_PAPER, plot_bgcolor=_PLOT, font=_FONT,
        height=height, margin=dict(l=20, r=20, t=30, b=10), **kwargs
    )
    return fig


def bmi_gauge(bmi: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=bmi,
        number={'suffix': " kg/m²", 'font': {'size': 22, 'color': '#6BB8F0'}},
        gauge={
            'axis': {'range': [15, 40], 'tickcolor': '#6A90AA'},
            'bar': {'color': '#3A8FD4'},
            'steps': [
                {'range': [15, 18.5], 'color': 'rgba(107,184,240,.18)'},
                {'range': [18.5, 25], 'color': 'rgba(61,170,85,.25)'},
                {'range': [25, 30], 'color': 'rgba(212,168,48,.25)'},
                {'range': [30, 40], 'color': 'rgba(240,128,128,.25)'},
            ],
        }
    ))
    return _base_layout(fig, height=200)


def hr_zone_gauge(avg_bpm: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=avg_bpm,
        number={'suffix': " bpm", 'font': {'size': 22, 'color': '#6BB8F0'}},
        gauge={
            'axis': {'range': [40, 200], 'tickcolor': '#6A90AA'},
            'bar': {'color': '#3A8FD4'},
            'steps': [
                {'range': [40, 100], 'color': 'rgba(138,175,197,.18)'},
                {'range': [100, 150], 'color': 'rgba(61,170,85,.25)'},
                {'range': [150, 200], 'color': 'rgba(240,128,128,.25)'},
            ],
        }
    ))
    return _base_layout(fig, height=200)


def radar_profile(feat: dict, distributions: dict) -> go.Figure:
    """
    Normalise chaque feature entre 0 et 100 par rapport a sa plage
    d'entrainement (min/max reelles issues de model_metadata.json).
    """
    axes = ['Age', 'BMI', 'Avg_BPM', 'Session_Duration (hours)', 'Workout_Frequency (days/week)']
    axis_labels = ['Âge', 'IMC', 'BPM', 'Durée', 'Fréquence']
    values = []
    for a in axes:
        if a not in distributions or a not in feat:
            values.append(0)
            continue
        lo, hi = distributions[a]['min'], distributions[a]['max']
        span = max(hi - lo, 1e-9)
        pct = (feat[a] - lo) / span * 100
        values.append(max(0, min(100, pct)))

    fig = go.Figure(go.Scatterpolar(
        r=values + [values[0]], theta=axis_labels + [axis_labels[0]],
        fill='toself', line=dict(color='#3A8FD4', width=2),
        fillcolor='rgba(58,143,212,.18)'
    ))
    fig.update_layout(
        polar=dict(
            bgcolor=_PLOT,
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, gridcolor='rgba(58,143,212,.15)'),
            angularaxis=dict(gridcolor='rgba(58,143,212,.15)', color='#8AAFC5')
        ),
        showlegend=False,
    )
    return _base_layout(fig, height=240)


def workout_donut(distribution: dict) -> go.Figure:
    labels = list(distribution.keys())
    values = list(distribution.values())
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=.62,
        marker=dict(colors=['#3A8FD4', '#D85A30', '#3DAA55', '#7F77DD'][:len(labels)],
                    line=dict(color='#08111E', width=2)),
        textfont=dict(color='#C5DFF0', size=11),
    ))
    fig.update_layout(showlegend=True, legend=dict(font=dict(size=10, color='#8AAFC5')))
    return _base_layout(fig, height=240)


def calories_trend(predictions: list) -> go.Figure:
    x = [p['time'] for p in predictions]
    y = [p['calories'] for p in predictions]
    fig = go.Figure(go.Scatter(
        x=x, y=y, mode='lines+markers',
        line=dict(color='#3A8FD4', width=2),
        marker=dict(color='#6BB8F0', size=7),
        fill='tozeroy', fillcolor='rgba(58,143,212,0.08)'
    ))
    fig.update_layout(
        xaxis=dict(showgrid=True, gridcolor='rgba(58,143,212,.07)', color='#6A90AA'),
        yaxis=dict(showgrid=True, gridcolor='rgba(58,143,212,.07)', color='#6A90AA'),
    )
    return _base_layout(fig, height=220)
