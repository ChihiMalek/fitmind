"""
FitMind — Neural Performance Analytics v2
Theme : Dark Steel / Cold Precision
Modes : Client | Admin
Auth  : Email/Password + Google (Demo)
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
import plotly.graph_objects as go

from model_utils import (
    load_or_train_models, predict_calories, predict_experience, predict_workout_type,
    check_feature_status, compute_global_confidence, WORKOUT_TYPE_DISCLAIMER
)
import evaluation_utils as ev
from dashboard import dashboard_page
from services.recommendation_service import get_recommendation

from database.migrations import run_migrations
from auth import session_manager
from auth.auth_config import DEMO_ACCOUNTS, PASSWORD_MIN_LENGTH
from auth.exceptions import AuthError
import services.auth_service as auth_service

# ══════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="FitMind — Neural Performance",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════════════
# FONTS + CSS — DARK STEEL THEME
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@400;500;600;700&family=Orbitron:wght@400;700&display=swap" rel="stylesheet">

<style>
:root {
    --bg:      #060A14;
    --bg2:     #08101E;
    --bg3:     #0D1828;
    --panel:   #0F1D2E;
    --steel:   #1A3A5C;
    --blue:    #2460A0;
    --accent:  #3A8FD4;
    --accent2: #6BB8F0;
    --chrome:  #8AAFC5;
    --text:    #C5DFF0;
    --text2:   #6A90AA;
    --muted:   #253A50;
    --gold:    #D4A830;
    --green:   #3DAA55;
    --border:  rgba(58,143,212,0.16);
    --border2: rgba(58,143,212,0.35);
    --border3: rgba(58,143,212,0.60);
    --glow:    0 0 25px rgba(58,143,212,0.22);
    --glow2:   0 0 50px rgba(58,143,212,0.40);
    --shadow:  0 8px 40px rgba(0,0,0,0.65);
}

/* ── Base ── */
* { font-family: 'Rajdhani', sans-serif !important; }
h1, h2, h3, h4 { font-family: 'Bebas Neue', sans-serif !important; }

/* ── Background — dark steel texture ── */
.stApp {
    background-color: var(--bg);
    background-image:
        repeating-linear-gradient(0deg,
            transparent 0, transparent 2px,
            rgba(58,143,212,0.018) 2px, rgba(58,143,212,0.018) 3px),
        repeating-linear-gradient(90deg,
            transparent 0, transparent 80px,
            rgba(255,255,255,0.004) 80px, rgba(255,255,255,0.004) 81px),
        radial-gradient(ellipse at 15% 70%, rgba(15,40,80,0.5) 0%, transparent 55%),
        radial-gradient(ellipse at 90% 10%, rgba(8,20,50,0.4) 0%, transparent 45%),
        linear-gradient(155deg, #040810 0%, #07101C 30%, #091420 55%, #050A10 100%);
}
.main .block-container { padding: 0 2rem 3rem 2rem !important; max-width: 1440px !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #060C18 0%, #040810 100%) !important;
    border-right: 1px solid var(--border2) !important;
    box-shadow: 4px 0 35px rgba(0,0,0,0.6) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Orbitron', monospace !important;
    font-size: 0.62rem !important;
    letter-spacing: 0.12em !important;
    color: var(--muted) !important;
    background: transparent !important;
    border: none !important;
    padding: 0.85rem 1.5rem !important;
    text-transform: uppercase !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent2) !important;
    border-bottom: 2px solid var(--accent) !important;
}
.stTabs [data-baseweb="tab-panel"] { padding: 1.5rem 0 0 0 !important; }

/* ── Inputs ── */
[data-testid="stTextInput"] input {
    background: var(--panel) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 3px !important;
    color: var(--text) !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.6rem 0.8rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: var(--glow) !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background: var(--panel) !important;
    border-color: var(--border2) !important;
    color: var(--text) !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within {
    border-color: var(--accent) !important;
    box-shadow: var(--glow) !important;
}

/* ── Radio (admin nav) ── */
[data-testid="stRadio"] label {
    font-family: 'Orbitron', monospace !important;
    font-size: 0.62rem !important;
    letter-spacing: 0.1em !important;
    color: var(--text2) !important;
    padding: 6px 0 !important;
    text-transform: uppercase !important;
}
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
    font-family: 'Orbitron', monospace !important;
    font-size: 0.62rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}

/* ── Buttons ── */
.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #1A3D6A 0%, #2460A0 50%, #1A3D6A 100%);
    background-size: 200% 100%;
    color: var(--text) !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.15rem !important;
    padding: 0.8rem;
    border: 1px solid rgba(58,143,212,0.45) !important;
    border-radius: 3px;
    letter-spacing: 3px;
    text-transform: uppercase;
    transition: all 0.3s !important;
    box-shadow: 0 4px 20px rgba(36,96,160,0.35) !important;
    clip-path: polygon(8px 0%,100% 0%,calc(100% - 8px) 100%,0% 100%) !important;
    animation: btnPulse 4s ease-in-out infinite !important;
}
.stButton > button:hover {
    background-position: 100% 0 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 40px rgba(58,143,212,0.5) !important;
    letter-spacing: 4px !important;
    border-color: rgba(58,143,212,0.7) !important;
}
.stButton > button:active { transform: scale(0.98) !important; }

/* Google button override */
.google-wrap .stButton > button {
    background: #FFFFFF !important;
    color: #3C4043 !important;
    border: 1px solid #DADCE0 !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1rem !important;
    letter-spacing: 1px !important;
    clip-path: none !important;
    animation: none !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.35) !important;
}
.google-wrap .stButton > button:hover {
    background: #F5F5F5 !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.45) !important;
    transform: translateY(-1px) !important;
    letter-spacing: 1px !important;
}

/* Logout/secondary button */
.secondary-btn .stButton > button {
    background: transparent !important;
    border: 1px solid var(--border2) !important;
    color: var(--text2) !important;
    font-size: 0.85rem !important;
    letter-spacing: 2px !important;
    animation: none !important;
    clip-path: none !important;
    box-shadow: none !important;
}
.secondary-btn .stButton > button:hover {
    border-color: var(--border3) !important;
    color: var(--text) !important;
    transform: none !important;
}

/* ── Alert ── */
[data-testid="stAlert"] {
    background: rgba(58,143,212,0.07) !important;
    border: 1px solid var(--border2) !important;
    border-left: 4px solid var(--accent) !important;
    border-radius: 3px !important;
    color: var(--text2) !important;
}
/* ── Expander ── */
[data-testid="stExpander"] {
    background: var(--panel) !important;
    border: 1px solid var(--border) !important;
    border-left: 3px solid var(--accent) !important;
    border-radius: 3px !important;
}
/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    background: var(--panel) !important;
}
/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--steel); border-radius: 2px; }

/* ═══════════════════════════════════
   COMPOSANTS AUTH
═══════════════════════════════════ */
.auth-outer {
    max-width: 440px;
    margin: 0 auto;
    padding-top: 1.5rem;
    animation: fadeInUp 0.8s cubic-bezier(0.16,1,0.3,1);
}
.auth-logo { text-align: center; margin-bottom: 2rem; }
.auth-rings {
    width: 90px; height: 90px;
    margin: 0 auto 1.2rem;
    position: relative; display: flex;
    align-items: center; justify-content: center;
    animation: floatY 4s ease-in-out infinite;
}
.ar { position: absolute; border-radius: 50%; border: 1px solid; }
.ar1 { inset:0; border-color:rgba(58,143,212,.5); animation:rotateCW 10s linear infinite; }
.ar1::before {
    content:''; position:absolute; top:-5px; left:50%; transform:translateX(-50%);
    width:9px; height:9px; border-radius:50%;
    background:var(--accent); box-shadow:0 0 12px var(--accent),0 0 24px var(--accent2);
}
.ar2 { inset:14px; border-color:rgba(107,184,240,.2); border-style:dashed; animation:rotateCCW 6s linear infinite; }
.ar3 { inset:26px; border-color:rgba(58,143,212,.12); animation:rotateCW 14s linear infinite; }
.ar-core {
    position:absolute; inset:34px; border-radius:50%;
    background:rgba(58,143,212,.1); border:1px solid rgba(58,143,212,.4);
    display:flex; align-items:center; justify-content:center; font-size:1rem;
    box-shadow:0 0 20px rgba(58,143,212,.2),inset 0 0 12px rgba(58,143,212,.1);
    animation:steelGlow 3s ease-in-out infinite;
}
.auth-title {
    font-family:'Bebas Neue',sans-serif !important;
    font-size:2.2rem; letter-spacing:.2em; color:var(--accent2);
    text-shadow:0 0 25px rgba(107,184,240,.4),0 0 50px rgba(58,143,212,.15);
    animation:titleSlide .7s cubic-bezier(.16,1,.3,1);
}
.auth-title span { color:var(--text); }
.auth-ver {
    font-family:'Share Tech Mono',monospace !important;
    font-size:.62rem; color:var(--muted); letter-spacing:.14em;
    margin-top:4px; text-transform:uppercase;
}
.auth-card {
    background:rgba(9,16,30,.9);
    backdrop-filter:blur(20px);
    border:1px solid var(--border2);
    border-radius:8px;
    overflow:hidden;
    position:relative;
    box-shadow:0 40px 80px rgba(0,0,0,.6),var(--glow);
}
.auth-card::before {
    content:''; position:absolute; top:0; left:-60%; width:50%; height:2px;
    background:linear-gradient(90deg,transparent,var(--accent),var(--accent2),transparent);
    animation:sweepX 3s linear infinite; pointer-events:none; z-index:1;
}
.auth-card::after {
    content:''; position:absolute; inset:0; pointer-events:none;
    background:
        linear-gradient(to right,rgba(58,143,212,.35) 10px,transparent 10px) 0 0/10px 1px no-repeat,
        linear-gradient(to bottom,rgba(58,143,212,.35) 10px,transparent 10px) 0 0/1px 10px no-repeat,
        linear-gradient(to left,rgba(58,143,212,.35) 10px,transparent 10px) 100% 100%/10px 1px no-repeat,
        linear-gradient(to top,rgba(58,143,212,.35) 10px,transparent 10px) 100% 100%/1px 10px no-repeat;
}
.auth-inner { padding: 1.75rem 2rem 2rem; }
.auth-divider {
    display:flex; align-items:center; gap:10px;
    margin:1.2rem 0;
    font-family:'Share Tech Mono',monospace !important;
    font-size:.62rem; color:var(--muted); letter-spacing:.1em;
}
.auth-divider::before,.auth-divider::after { content:''; flex:1; height:1px; background:var(--border); }
.demo-note {
    text-align:center; margin-top:1.25rem; padding:0.85rem;
    background:rgba(58,143,212,.05); border:1px solid var(--border);
    border-radius:4px;
    font-family:'Share Tech Mono',monospace !important;
    font-size:.6rem; color:var(--muted); letter-spacing:.06em; line-height:1.7;
}
.demo-note span { color:var(--accent2); }

/* ═══════════════════════════════════
   HEADER APP
═══════════════════════════════════ */
.main-header {
    position:relative; overflow:hidden;
    background:linear-gradient(135deg,#040810 0%,#060D1A 35%,#091520 60%,#040810 100%);
    padding:2.5rem 2rem 2rem;
    margin:0 -2rem 0 -2rem;
    text-align:center;
    border-bottom:2px solid rgba(58,143,212,.3);
    box-shadow:0 8px 40px rgba(0,0,0,.5);
    animation:fadeInDown 0.8s ease;
}
.main-header::before {
    content:''; position:absolute; inset:0;
    background:repeating-linear-gradient(-45deg,
        transparent 0,transparent 36px,
        rgba(58,143,212,.018) 36px,rgba(58,143,212,.018) 37px);
}
.main-header::after {
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background:linear-gradient(90deg,transparent,var(--accent),var(--accent2),var(--accent),transparent);
    background-size:300% 100%; animation:steelFlow 3s linear infinite;
}
.main-header h1 {
    font-family:'Bebas Neue',sans-serif !important;
    font-size:clamp(2.5rem,7vw,4.8rem);
    letter-spacing:10px; color:var(--text); margin:0;
    text-shadow:0 0 40px rgba(58,143,212,.28),0 0 80px rgba(58,143,212,.1);
    animation:titleSlam .7s cubic-bezier(.16,1,.3,1);
}
.main-header h1 span {
    color:var(--accent2);
    text-shadow:0 0 30px rgba(107,184,240,.8),0 0 60px rgba(58,143,212,.4);
    animation:steelFlicker 6s ease-in-out infinite;
}
.main-header p { font-size:.9rem; color:var(--text2); margin:.6rem 0 1.2rem; letter-spacing:3px; text-transform:uppercase; animation:fadeInUp .8s ease .25s both; }
.main-header .badge {
    display:inline-block; background:rgba(58,143,212,.1); color:var(--accent);
    padding:4px 18px; border:1px solid rgba(58,143,212,.35);
    font-family:'Orbitron',monospace !important; font-size:.65rem; letter-spacing:2px;
    text-transform:uppercase;
    clip-path:polygon(7px 0%,100% 0%,calc(100% - 7px) 100%,0% 100%);
    animation:fadeInUp .8s ease .4s both;
}

/* User strip */
.user-strip {
    display:flex; align-items:center; justify-content:space-between;
    background:rgba(10,18,30,.7); border-bottom:1px solid var(--border);
    padding:.6rem 2rem; margin:0 -2rem 1.75rem -2rem;
    font-family:'Share Tech Mono',monospace !important;
    font-size:.68rem; color:var(--text2); letter-spacing:.06em;
}
.u-name { color:var(--accent2); }
.u-role {
    background:rgba(58,143,212,.1); border:1px solid rgba(58,143,212,.25);
    padding:2px 10px; color:var(--accent); border-radius:20px;
    font-size:.58rem; letter-spacing:.1em;
}
.u-role.admin { background:rgba(212,168,48,.1); border-color:rgba(212,168,48,.3); color:var(--gold); }

/* ═══════════════════════════════════
   SIDEBAR COMPONENTS
═══════════════════════════════════ */
.sb-user-card {
    background:rgba(15,30,50,.7); border:1px solid var(--border2);
    border-radius:6px; padding:.85rem; margin-bottom:1rem; text-align:center;
}
.sb-avatar {
    width:44px; height:44px; border-radius:50%;
    background:rgba(58,143,212,.15); border:2px solid rgba(58,143,212,.4);
    display:flex; align-items:center; justify-content:center;
    margin:0 auto .5rem;
    font-family:'Bebas Neue',sans-serif !important; font-size:1.2rem;
    color:var(--accent2); box-shadow:0 0 15px rgba(58,143,212,.25);
}
.sb-avatar.admin-ava { border-color:rgba(212,168,48,.5); color:var(--gold); box-shadow:0 0 15px rgba(212,168,48,.2); }
.sb-name { font-family:'Bebas Neue',sans-serif !important; font-size:1rem; letter-spacing:3px; color:var(--text); }
.sb-role { font-family:'Orbitron',monospace !important; font-size:.55rem; letter-spacing:.1em; color:var(--accent); text-transform:uppercase; }
.sb-role.admin-role { color:var(--gold); }
.sb-section {
    font-family:'Orbitron',monospace !important; font-size:.58rem;
    letter-spacing:.14em; color:var(--muted); text-transform:uppercase;
    margin:.9rem 0 .45rem; padding-bottom:4px; border-bottom:1px solid var(--border);
}

/* IMC Box */
.imc-box {
    background:rgba(58,143,212,.06); border:1px solid var(--border2);
    border-top:2px solid var(--accent); padding:.85rem; text-align:center;
    margin:.75rem 0;
    clip-path:polygon(0 0,calc(100% - 7px) 0,100% 7px,100% 100%,7px 100%,0 calc(100% - 7px));
}
.imc-val { font-family:'Bebas Neue',sans-serif !important; font-size:2.3rem; color:var(--accent2); display:block; line-height:1; text-shadow:0 0 15px rgba(107,184,240,.35); }
.imc-lbl { font-family:'Orbitron',monospace !important; font-size:.55rem; letter-spacing:3px; color:var(--muted); text-transform:uppercase; margin-top:3px; }

/* ── Statut distribution (validation intelligente) ── */
.dist-caption { font-family:'Share Tech Mono',monospace !important; font-size:.62rem; margin:-6px 0 8px 2px; letter-spacing:.02em; }
.dist-green  { color:#5EC46B; }
.dist-yellow { color:#D4A830; }
.dist-red    { color:#F08080; }

.confidence-box {
    border:1px solid var(--border2); border-top:3px solid var(--accent);
    padding:.85rem; text-align:center; margin:.75rem 0; border-radius:4px;
    background:rgba(58,143,212,.05);
}
.confidence-box.yellow { border-top-color:var(--gold); background:rgba(212,168,48,.06); }
.confidence-box.red    { border-top-color:#D65858; background:rgba(214,88,88,.07); }
.confidence-val { font-family:'Bebas Neue',sans-serif !important; font-size:1.9rem; display:block; line-height:1; }
.confidence-box .confidence-val { color:#5EC46B; }
.confidence-box.yellow .confidence-val { color:var(--gold); }
.confidence-box.red .confidence-val { color:#F08080; }
.confidence-lbl { font-family:'Orbitron',monospace !important; font-size:.52rem; letter-spacing:2px; color:var(--muted); text-transform:uppercase; margin-top:2px; }

/* ── Carte demonstrative Workout_Type (volontairement distincte, non "fiable") ── */
.demo-card {
    background:linear-gradient(145deg,#1E1608,#2A1E0C);
    border:1px dashed rgba(212,168,48,.5); padding:1.5rem;
    margin-top:1rem; border-radius:4px;
}
.demo-card h3 {
    font-family:'Orbitron',monospace !important; color:var(--gold);
    font-size:.68rem; letter-spacing:3px; text-transform:uppercase; margin:0 0 .6rem;
}
.demo-card .demo-result { font-family:'Bebas Neue',sans-serif !important; font-size:1.9rem; color:#E8C868; margin:0 0 .5rem; }
.demo-card .demo-warn { color:#D8B878; font-size:.78rem; line-height:1.6; }

/* ═══════════════════════════════════
   RESULT + METRIC CARDS
═══════════════════════════════════ */
.result-card {
    background:linear-gradient(145deg,#0C1820,#111E2E);
    border:1px solid var(--border2); padding:1.75rem;
    position:relative; overflow:hidden;
    box-shadow:var(--shadow); transition:all 0.3s;
    animation:cardSlam .55s cubic-bezier(.16,1,.3,1);
    clip-path:polygon(0 0,calc(100% - 12px) 0,100% 12px,100% 100%,12px 100%,0 calc(100% - 12px));
}
.result-card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background:linear-gradient(90deg,transparent,var(--accent),var(--accent2),transparent);
    animation:shimmer 2.5s ease-in-out infinite;
}
.result-card::after {
    content:''; position:absolute; inset:0;
    background:radial-gradient(ellipse at 50% -20%,rgba(58,143,212,.06),transparent 65%);
    pointer-events:none;
}
.result-card:hover { border-color:var(--border3); box-shadow:var(--glow2); transform:translateY(-3px); }
.result-card h2 {
    font-family:'Orbitron',monospace !important; color:var(--accent);
    font-size:.65rem; margin:0 0 .75rem; letter-spacing:4px; text-transform:uppercase;
}
.result-value { font-family:'Bebas Neue',sans-serif !important; font-size:4rem; font-weight:900; color:var(--text); margin:0; line-height:1; }
.result-value .unit { font-family:'Rajdhani',sans-serif !important; font-size:1.3rem; color:var(--text2); font-weight:400; letter-spacing:2px; }
.result-sub { color:var(--text2); font-size:.83rem; margin:.4rem 0 0; letter-spacing:1px; }

.badge-level {
    display:inline-block; padding:6px 18px; margin-top:10px;
    font-family:'Bebas Neue',sans-serif !important; font-size:1.05rem; letter-spacing:3px;
    clip-path:polygon(6px 0%,100% 0%,calc(100% - 6px) 100%,0% 100%);
    animation:badgePop .6s cubic-bezier(.34,1.56,.64,1) .25s both;
}
.badge-debutant     { background:#0A1E10; border:1px solid #3D8B4A; color:#5EC46B; box-shadow:0 0 18px rgba(61,139,74,.3); }
.badge-intermediaire{ background:#0D1C30; border:1px solid var(--blue); color:var(--accent2); box-shadow:var(--glow); }
.badge-avance       { background:#0A1828; border:1px solid var(--accent); color:#A8D8F8; box-shadow:0 0 25px rgba(58,143,212,.4); }

.metric-box {
    background:var(--panel); border:1px solid var(--border); border-top:2px solid var(--accent);
    padding:1rem; text-align:center; transition:all 0.3s;
    animation:fadeInUp .5s ease both;
    clip-path:polygon(0 0,100% 0,100% calc(100% - 7px),calc(100% - 7px) 100%,0 100%);
}
.metric-box:hover { border-color:var(--border2); box-shadow:var(--glow); transform:translateY(-2px); }
.metric-box .value { font-family:'Bebas Neue',sans-serif !important; font-size:2rem; color:var(--accent2); display:block; line-height:1; }
.metric-box .label { font-family:'Orbitron',monospace !important; font-size:.55rem; color:var(--muted); text-transform:uppercase; letter-spacing:2px; margin-top:4px; }

/* Softmax bars — BLEU uniquement */
.sf-row { display:flex; align-items:center; gap:12px; margin-bottom:10px; }
.sf-label { width:115px; font-family:'Orbitron',monospace !important; font-size:.58rem; color:var(--text2); text-transform:uppercase; letter-spacing:1px; }
.sf-track { flex:1; height:7px; background:#0A1420; border:1px solid var(--border); overflow:hidden; }
.sf-fill { height:100%; transition:width 1.4s cubic-bezier(.16,1,.3,1); }
.sf-fill.g { background:linear-gradient(90deg,#1B5E20,#4CAF50); box-shadow:0 0 10px rgba(76,175,80,.5); }
.sf-fill.b { background:linear-gradient(90deg,var(--steel),var(--accent)); box-shadow:0 0 10px rgba(58,143,212,.6); }
.sf-fill.l { background:linear-gradient(90deg,var(--blue),var(--accent2)); box-shadow:0 0 12px rgba(107,184,240,.5); }
.sf-pct { font-family:'Bebas Neue',sans-serif !important; font-size:1rem; color:var(--accent2); width:44px; text-align:right; }

/* ═══════════════════════════════════
   ADMIN DASHBOARD
═══════════════════════════════════ */
.admin-stat {
    background:linear-gradient(145deg,#0C1820,#111E2E);
    border:1px solid var(--border); border-top:2px solid var(--accent);
    padding:1.2rem; position:relative; overflow:hidden;
    transition:all 0.3s; animation:fadeInUp .5s ease both;
    clip-path:polygon(0 0,calc(100% - 9px) 0,100% 9px,100% 100%,9px 100%,0 calc(100% - 9px));
}
.admin-stat:hover { border-color:var(--border2); box-shadow:var(--glow); transform:translateY(-2px); }
.admin-stat .as-val { font-family:'Bebas Neue',sans-serif !important; font-size:2.5rem; color:var(--accent2); display:block; line-height:1; text-shadow:0 0 12px rgba(107,184,240,.3); }
.admin-stat .as-lbl { font-family:'Orbitron',monospace !important; font-size:.55rem; color:var(--muted); letter-spacing:2px; text-transform:uppercase; margin-top:4px; }
.admin-stat.gold { border-top-color:var(--gold); }
.admin-stat.gold .as-val { color:var(--gold); text-shadow:0 0 12px rgba(212,168,48,.3); }

.hist-row {
    display:flex; align-items:center; gap:10px;
    background:rgba(12,24,40,.7); border:1px solid var(--border);
    border-radius:3px; padding:.7rem 1rem; margin-bottom:6px;
    transition:all .2s; animation:staggerIn .3s ease both;
}
.hist-row:hover { border-color:var(--border2); background:rgba(16,30,50,.8); }
.hist-badge {
    font-family:'Orbitron',monospace !important; font-size:.55rem;
    padding:3px 9px; border-radius:2px; white-space:nowrap;
    background:rgba(58,143,212,.1); color:var(--accent);
    border:1px solid rgba(58,143,212,.2); letter-spacing:.08em;
}
.hist-val { font-family:'Bebas Neue',sans-serif !important; font-size:1rem; color:var(--text); flex:1; }
.hist-time { font-family:'Share Tech Mono',monospace !important; font-size:.58rem; color:var(--muted); }

/* Section title */
.sec-title {
    font-family:'Bebas Neue',sans-serif !important;
    font-size:1.5rem; letter-spacing:5px; color:var(--accent);
    border-left:3px solid var(--accent); padding-left:12px;
    margin:1.5rem 0 1rem; display:block;
    text-shadow:0 0 15px rgba(58,143,212,.25);
}

/* ═══════════════════════════════════
   FOOTER
═══════════════════════════════════ */
.footer {
    text-align:center; color:var(--muted); font-size:.7rem;
    padding:1.5rem 0 .5rem; border-top:1px solid var(--border);
    margin-top:2.5rem;
    font-family:'Orbitron',monospace !important;
    letter-spacing:2px; text-transform:uppercase;
}

/* ═══════════════════════════════════
   ANIMATIONS
═══════════════════════════════════ */
@keyframes rotateCW  { to{transform:rotate(360deg)} }
@keyframes rotateCCW { to{transform:rotate(-360deg)} }
@keyframes floatY    { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-7px)} }
@keyframes steelGlow {
    0%,100%{box-shadow:0 0 20px rgba(58,143,212,.2),inset 0 0 12px rgba(58,143,212,.1)}
    50%    {box-shadow:0 0 35px rgba(58,143,212,.4),inset 0 0 20px rgba(58,143,212,.2)}
}
@keyframes steelFlow { 0%{background-position:-200% 0} 100%{background-position:200% 0} }
@keyframes steelFlicker {
    0%,88%,100%{text-shadow:0 0 30px rgba(107,184,240,.8),0 0 60px rgba(58,143,212,.35);color:var(--accent2)}
    90%{text-shadow:0 0 50px rgba(107,184,240,1),0 0 100px rgba(58,143,212,.5);color:#A0D4F8}
    94%{text-shadow:0 0 20px rgba(58,143,212,.6);color:#5090C0}
}
@keyframes titleSlam  { from{transform:scale(.78) translateY(-25px);opacity:0;letter-spacing:25px} to{transform:scale(1) translateY(0);opacity:1;letter-spacing:10px} }
@keyframes titleSlide { from{transform:translateY(-18px);opacity:0} to{transform:translateY(0);opacity:1} }
@keyframes sweepX     { from{left:-60%} to{left:120%} }
@keyframes shimmer    { 0%,100%{opacity:0} 50%{opacity:1} }
@keyframes fadeInDown { from{opacity:0;transform:translateY(-20px)} to{opacity:1;transform:translateY(0)} }
@keyframes fadeInUp   { from{opacity:0;transform:translateY(20px)}  to{opacity:1;transform:translateY(0)} }
@keyframes cardSlam   { from{transform:translateY(30px) scale(.94);opacity:0} to{transform:translateY(0) scale(1);opacity:1} }
@keyframes badgePop   { from{transform:scale(.4) rotate(-4deg);opacity:0} to{transform:scale(1) rotate(0);opacity:1} }
@keyframes btnPulse   {
    0%,100%{box-shadow:0 4px 20px rgba(36,96,160,.35)!important}
    50%    {box-shadow:0 4px 35px rgba(58,143,212,.6)!important}
}
@keyframes staggerIn  { from{opacity:0;transform:translateX(-10px)} to{opacity:1;transform:translateX(0)} }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════
def init_session():
    defaults = {
        'auth_user_id':  None,       # id interne, pour l'audit log de logout() uniquement
        'google_step':   False,
        'auth_msg':      ('', ''),   # (type, text)  type = 'err'|'ok'
        'predictions':   [],
        'admin_page':    'dashboard',
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


# ══════════════════════════════════════════════════════════════════════
# BASE DE DONNEES — migrations + comptes de demonstration
# ══════════════════════════════════════════════════════════════════════
def seed_demo_accounts():
    """
    Cree les comptes de demonstration en base au premier lancement.
    Idempotent et non-destructif : voir auth_service.ensure_seed_account().
    """
    for account in DEMO_ACCOUNTS:
        auth_service.ensure_seed_account(
            email=account["email"],
            password=account["password"],
            username=account["username"],
            role=account["role"],
        )

run_migrations()
seed_demo_accounts()


# ══════════════════════════════════════════════════════════════════════
# AUTH — orchestration UI uniquement (logique metier dans services/auth_service.py)
# ══════════════════════════════════════════════════════════════════════
def set_msg(t, txt): st.session_state.auth_msg = (t, txt)

def handle_login_success(user):
    """Orchestration UI commune apres une authentification reussie
    (email/mot de passe ou Google demo) : ouvre la session et memorise
    l'id pour l'audit log de la deconnexion."""
    session_manager.start_session(auth_service.to_session_dict(user))
    st.session_state.auth_user_id = user.id

def handle_logout():
    """Orchestration UI de la deconnexion : audit (auth_service) puis
    destruction de la session (session_manager)."""
    auth_service.logout(st.session_state.get('auth_user_id'))
    session_manager.clear_session()
    st.session_state.auth_user_id = None
    st.rerun()


# ══════════════════════════════════════════════════════════════════════
# AUTH PAGE
# ══════════════════════════════════════════════════════════════════════
def show_auth():
    st.markdown('<div class="auth-outer">', unsafe_allow_html=True)

    # Logo animé
    st.markdown("""
    <div class="auth-logo">
        <div class="auth-rings">
            <div class="ar ar1"></div>
            <div class="ar ar2"></div>
            <div class="ar ar3"></div>
            <div class="ar-core">🏋️</div>
        </div>
        <div class="auth-title">Fit<span>Mind</span></div>
        <div class="auth-ver">Neural Performance Analytics · v2.0</div>
    </div>
    """, unsafe_allow_html=True)

    # Messages
    msg_type, msg_txt = st.session_state.auth_msg
    if msg_txt:
        color = "#F08080" if msg_type == 'err' else "#6BB8F0"
        bg    = "rgba(220,50,50,.08)" if msg_type == 'err' else "rgba(58,143,212,.08)"
        bd    = "rgba(220,50,50,.25)" if msg_type == 'err' else "rgba(58,143,212,.25)"
        icon  = "⚠" if msg_type == 'err' else "✓"
        st.markdown(f"""
        <div style="background:{bg};border:1px solid {bd};border-radius:3px;
                    padding:10px 14px;color:{color};font-family:Share Tech Mono,monospace;
                    font-size:.72rem;margin-bottom:1rem;">
            {icon} {msg_txt}
        </div>""", unsafe_allow_html=True)
        st.session_state.auth_msg = ('', '')

    # Auth card
    st.markdown('<div class="auth-card"><div class="auth-inner">', unsafe_allow_html=True)

    # Tabs Connexion / Inscription
    tab_li, tab_rg = st.tabs(["▸  CONNEXION", "▸  INSCRIPTION"])

    # ── LOGIN ──
    with tab_li:
        if st.session_state.google_step:
            # Étape Google email
            st.markdown("""
            <div style="text-align:center;margin-bottom:1rem;">
                <div style="font-size:1.5rem">🔵</div>
                <div style="font-family:Orbitron,monospace;font-size:.65rem;
                            color:var(--accent2);letter-spacing:.1em;margin-top:4px;">
                    CONNEXION GOOGLE
                </div>
            </div>
            """, unsafe_allow_html=True)
            gmail = st.text_input("Adresse Gmail", placeholder="prenom.nom@gmail.com", key="g_email")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✓ Confirmer", key="g_ok", use_container_width=True):
                    try:
                        user = auth_service.login_with_provider("google_demo", {"email": gmail})
                        handle_login_success(user)
                        st.session_state.google_step = False
                        st.rerun()
                    except AuthError as e:
                        set_msg('err', str(e)); st.rerun()
            with c2:
                st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
                if st.button("✕ Annuler", key="g_cancel", use_container_width=True):
                    st.session_state.google_step = False; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            email = st.text_input("Adresse e-mail", placeholder="vous@exemple.com", key="li_email")
            pwd   = st.text_input("Mot de passe",   type="password", placeholder="••••••••",  key="li_pwd")

            if st.button("🔑 SE CONNECTER", key="li_btn", use_container_width=True):
                if email and pwd:
                    try:
                        user = auth_service.login(email, pwd)
                        handle_login_success(user)
                        st.rerun()
                    except AuthError as e:
                        set_msg('err', str(e)); st.rerun()
                else:
                    set_msg('err', 'Veuillez remplir tous les champs.'); st.rerun()

            st.markdown('<div class="auth-divider">── OU ──</div>', unsafe_allow_html=True)

            st.markdown('<div class="google-wrap">', unsafe_allow_html=True)
            if st.button("🔵  Continuer avec Google", key="google_li", use_container_width=True):
                st.session_state.google_step = True; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # ── REGISTER ──
    with tab_rg:
        name  = st.text_input("Nom complet",     placeholder="Prénom NOM",          key="rg_name")
        email = st.text_input("Adresse e-mail",  placeholder="vous@exemple.com",    key="rg_email")
        pwd   = st.text_input("Mot de passe",    type="password",
                               placeholder=f"Min. {PASSWORD_MIN_LENGTH} caractères, 1 lettre + 1 chiffre",
                               key="rg_pwd")

        if st.button("✅ CRÉER MON COMPTE", key="rg_btn", use_container_width=True):
            if name and email and pwd:
                try:
                    auth_service.register(email, pwd, username=name)
                    set_msg('ok', 'Compte créé ! Connectez-vous.')
                except AuthError as e:
                    set_msg('err', str(e))
                st.rerun()
            else:
                set_msg('err', 'Veuillez remplir tous les champs.'); st.rerun()

        st.markdown('<div class="auth-divider">── OU ──</div>', unsafe_allow_html=True)
        st.markdown('<div class="google-wrap">', unsafe_allow_html=True)
        if st.button("🔵  S'inscrire avec Google", key="google_rg", use_container_width=True):
            st.session_state.google_step = True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="demo-note">
        Comptes de démonstration<br>
        <span>Admin</span> : admin@fitmind.ai / Admin2024!<br>
        <span>Client</span> : client@demo.com / Demo2024!
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div></div></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# PREDICTION FORM (partagé Client + Admin)
# ══════════════════════════════════════════════════════════════════════
def dist_caption(feature_key, value, distributions):
    """Retourne le HTML d'une puce de statut 🟢/🟡/🔴 pour une feature."""
    if feature_key not in distributions:
        return ""
    s = check_feature_status(value, distributions[feature_key])
    cls = {'green': 'dist-green', 'yellow': 'dist-yellow', 'red': 'dist-red'}[s['status']]
    icon = {'green': '🟢', 'yellow': '🟡', 'red': '🔴'}[s['status']]
    lo, hi = distributions[feature_key]['min'], distributions[feature_key]['max']
    return f'<div class="dist-caption {cls}">{icon} plage entraînement : {lo:.1f} – {hi:.1f}</div>'


def prediction_form(model_reg, model_clf, model_wt, scaler_reg, scaler_clf, scaler_wt,
                     wt_encoder, metadata, user):
    initials = user.get('initials', user['name'][0].upper())
    role     = user.get('role', 'client')
    dist     = metadata['regression']['feature_distributions']
    aux_dist = metadata.get('auxiliary_feature_distributions', {})

    with st.sidebar:
        st.markdown('<div class="sb-section">◆ Paramètres physiologiques</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            age         = st.slider("Âge",       18, 80,    28)
            st.markdown(dist_caption('Age', age, dist), unsafe_allow_html=True)
            gender      = st.selectbox("Genre",   ["Homme", "Femme"])
            weight      = st.slider("Poids (kg)", 40.0, 150.0, 75.0, 0.5)
            st.markdown(dist_caption('Weight (kg)', weight, dist), unsafe_allow_html=True)
            height      = st.slider("Taille (m)", 1.40, 2.10, 1.75, 0.01)
            st.markdown(dist_caption('Height (m)', height, dist), unsafe_allow_html=True)
        with col2:
            avg_bpm     = st.slider("BPM moyen",  60,  200, 140)
            st.markdown(dist_caption('Avg_BPM', avg_bpm, dist), unsafe_allow_html=True)
            resting_bpm = st.slider("BPM repos",  40,  100,  65)
            st.markdown(dist_caption('Resting_BPM', resting_bpm, dist), unsafe_allow_html=True)
            max_bpm     = st.slider("BPM max (info)", 100, 220, 175,
                                     help="Non utilisé par les modèles — suivi informatif pour le Dashboard.")
            st.markdown(dist_caption('Max_BPM', max_bpm, aux_dist), unsafe_allow_html=True)
            duration    = st.slider("Durée (h)",  0.5, 4.0,  1.2, 0.1)
            st.markdown(dist_caption('Session_Duration (hours)', duration, dist), unsafe_allow_html=True)
            water       = st.slider("Eau (L)",    0.5, 5.0,  2.5, 0.1)
            st.markdown(dist_caption('Water_Intake (liters)', water, dist), unsafe_allow_html=True)

        freq      = st.slider("Fréquence (j/sem)", 1, 7, 3)
        st.markdown(dist_caption('Workout_Frequency (days/week)', freq, dist), unsafe_allow_html=True)
        exp_level = st.slider("Niveau expérience", 1, 3, 2, help="1=Débutant · 2=Inter · 3=Avancé")

        bmi = weight / (height ** 2)
        bc  = "#5EC46B" if bmi < 25 else "#6BB8F0" if bmi < 30 else "#F08080"
        st.markdown(f"""
        <div class="imc-box" style="border-top-color:{bc}">
            <span class="imc-val" style="color:{bc}">{bmi:.1f}</span>
            <span class="imc-lbl">IMC — kg/m²</span>
        </div>
        """, unsafe_allow_html=True)

        # ── Indicateur de confiance global (validation intelligente) ──
        gb_preview = 0 if gender == "Homme" else 1
        feat_preview = {
            'Age': age, 'Gender': gb_preview, 'Weight (kg)': weight, 'Height (m)': height,
            'Avg_BPM': avg_bpm, 'Resting_BPM': resting_bpm, 'Max_BPM': max_bpm,
            'Session_Duration (hours)': duration, 'Water_Intake (liters)': water,
            'Workout_Frequency (days/week)': freq, 'Experience_Level': exp_level, 'BMI': bmi
        }
        confidence = compute_global_confidence(feat_preview, dist)
        st.markdown(f"""
        <div class="confidence-box {confidence['level']}">
            <span class="confidence-val">{confidence['score']:.0f}%</span>
            <span class="confidence-lbl">Confiance — entrées dans la distribution</span>
        </div>
        """, unsafe_allow_html=True)

        predict_btn = st.button("🚀 Lancer la prédiction", use_container_width=True)

        # Historique sidebar
        if st.session_state.predictions:
            st.markdown('<div class="sb-section">◆ Historique session</div>', unsafe_allow_html=True)
            for p in reversed(st.session_state.predictions[-5:]):
                st.markdown(f"""
                <div class="hist-row">
                    <span class="hist-badge">RÉGR.</span>
                    <span class="hist-val">{p['result']}</span>
                    <span class="hist-time">{p['time']}</span>
                </div>""", unsafe_allow_html=True)

    # ── Features ──
    feat = feat_preview
    feat_clf = {k: v for k, v in feat.items() if k != 'Experience_Level'}
    feat_wt  = feat_clf  # mêmes features physiologiques que la classification niveau

    if predict_btn:
        with st.spinner("🧠 Inférence neuronale..."):
            time.sleep(0.3)
            try:
                calories = predict_calories(model_reg, scaler_reg, feat)
                ci, proba = predict_experience(model_clf, scaler_clf, feat_clf)
                wt_class, wt_proba, wt_names = predict_workout_type(model_wt, scaler_wt, wt_encoder, feat_wt)
            except Exception as e:
                st.error(f"Erreur : {e}"); return

        LEVELS  = ["Débutant", "Intermédiaire", "Avancé"]
        SYMS    = ["[--]", "[-+]", "[++]"]
        LBCLS   = ["badge-debutant", "badge-intermediaire", "badge-avance"]
        EMOJIS  = ["🌱", "💪", "🔥"]
        conf    = proba[ci] * 100

        st.session_state.predictions.append({
            'result': f"{calories:.0f} kcal", 'time': datetime.now().strftime("%H:%M"),
            'timestamp': datetime.now().isoformat(),
            'calories': calories, 'level': LEVELS[ci], 'level_idx': ci, 'mode': 'Régression',
            'workout_type': wt_class, 'avg_bpm': avg_bpm, 'water': water, 'bmi': bmi,
            'confidence_score': confidence['score'], 'confidence_level': confidence['level'],
            'features': feat.copy(),
        })

        # Cards résultats
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown(f"""
            <div class="result-card">
                <h2>⚡ Calories brûlées</h2>
                <p class="result-value">{calories:.0f} <span class="unit">kcal</span></p>
                <p class="result-sub">Séance de {duration}h à {avg_bpm} BPM moyen</p>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="result-card">
                <h2>🏆 Niveau d'expérience</h2>
                <p class="result-value" style="font-size:2.4rem">{EMOJIS[ci]} {LEVELS[ci]}</p>
                <p class="result-sub">Confiance IA : {conf:.1f}%</p>
                <span class="badge-level {LBCLS[ci]}">{SYMS[ci]} {LEVELS[ci]}</span>
            </div>""", unsafe_allow_html=True)

        # Métriques
        st.markdown('<span class="sec-title">ANALYSE DÉTAILLÉE</span>', unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        for col, val, lbl in zip([m1,m2,m3,m4],
            [f"{calories:.0f}", f"{conf:.0f}%", str(avg_bpm), f"{bmi:.1f}"],
            ["Calories (kcal)", "Confiance IA", "BPM moyen", "IMC"]):
            col.markdown(f'<div class="metric-box"><div class="value">{val}</div><div class="label">{lbl}</div></div>', unsafe_allow_html=True)

        # Softmax bars
        st.markdown('<span class="sec-title">DISTRIBUTION SOFTMAX</span>', unsafe_allow_html=True)
        for i, (lvl, cls) in enumerate(zip(LEVELS, ['g','b','l'])):
            pct = proba[i] * 100
            st.markdown(f"""
            <div class="sf-row">
                <span class="sf-label">{EMOJIS[i]} {lvl}</span>
                <div class="sf-track"><div class="sf-fill {cls}" style="width:{pct:.1f}%"></div></div>
                <span class="sf-pct">{pct:.1f}%</span>
            </div>""", unsafe_allow_html=True)

        # Interprétation
        with st.expander("💡 Analyse et recommandations", expanded=True):
            reco = get_recommendation(calories, ci, avg_bpm, water)
            st.markdown(f"""
**Analyse biométrique**

- **Calories** : {calories:.0f} kcal — {reco['calories_note']}
- **Niveau** : {EMOJIS[ci]} {LEVELS[ci]} — {reco['level_note']}
- **Cardio** : BPM {avg_bpm} — {reco['bpm_note']}
- **Hydratation** : {reco['hydration_note']}
            """)

        # ── Carte démonstrative Workout_Type (jamais présentée comme fiable) ──
        wt_meta = metadata['classification_workout_type']
        wt_acc  = wt_meta['metrics_test']['accuracy'] * 100
        wt_base = wt_meta['majority_class_baseline_accuracy'] * 100
        st.markdown('<span class="sec-title">DÉMONSTRATION — TYPE D\'ENTRAÎNEMENT</span>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="demo-card">
            <h3>⚠️ Modèle pédagogique — non fiable</h3>
            <p class="demo-result">Prédiction : {wt_class}</p>
            <p class="demo-warn">
                {WORKOUT_TYPE_DISCLAIMER}<br><br>
                <b>Précision réelle mesurée sur le jeu de test :</b> {wt_acc:.1f}%
                (baseline « toujours prédire la classe majoritaire » : {wt_base:.1f}%).
                Cette prédiction est proche du hasard et ne doit pas guider vos décisions.
            </p>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("Détail des probabilités par classe (démonstratif)"):
            for name, p in zip(wt_names, wt_proba):
                pct = p * 100
                st.markdown(f"""
                <div class="sf-row">
                    <span class="sf-label">{name}</span>
                    <div class="sf-track"><div class="sf-fill b" style="width:{pct:.1f}%"></div></div>
                    <span class="sf-pct">{pct:.1f}%</span>
                </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background:linear-gradient(135deg,#08111E 0%,#0D1A2E 100%);
                    border:1px solid rgba(58,143,212,.18);border-left:4px solid var(--accent);
                    padding:2.5rem;text-align:center;margin-top:1rem;
                    clip-path:polygon(0 0,calc(100% - 14px) 0,100% 14px,100% 100%,14px 100%,0 calc(100% - 14px))'>
            <div style='font-size:3rem;margin-bottom:1rem'>🏋️</div>
            <div style='font-family:Bebas Neue,sans-serif;font-size:1.8rem;letter-spacing:5px;color:var(--accent2);margin-bottom:.5rem'>
                PRÊT À ANALYSER VOS PERFORMANCES ?
            </div>
            <div style='color:var(--muted);font-size:.9rem;letter-spacing:2px;text-transform:uppercase'>
                Renseignez vos données dans la barre latérale<br>
                puis cliquez sur <strong style='color:var(--accent)'>LANCER LA PRÉDICTION</strong>
            </div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# CLIENT PAGE
# ══════════════════════════════════════════════════════════════════════
def show_client(model_reg, model_clf, model_wt, scaler_reg, scaler_clf, scaler_wt, wt_encoder, metadata):
    user = session_manager.get_current_user()
    r2_display = metadata['regression']['metrics_test']['r2']
    n_samples  = metadata['dataset']['n_samples']
    st.markdown(f"""
    <div class="main-header">
        <h1>Fit<span>Mind</span></h1>
        <p>Neural Performance Analytics — Prédiction IA</p>
        <span class="badge">⚙️ R² test = {r2_display:.2f} &bull; {n_samples} Athlètes &bull; Neural MLP</span>
    </div>
    <div class="user-strip">
        <span>Opérateur : <span class="u-name">{user['name']}</span> ({user.get('email','')})</span>
        <span class="u-role">CLIENT</span>
    </div>""", unsafe_allow_html=True)

    with st.sidebar:
        ini = user.get('initials', user['name'][0].upper())
        st.markdown(f"""
        <div class="sb-user-card">
            <div class="sb-avatar">{ini}</div>
            <div class="sb-name">{user['name']}</div>
            <div class="sb-role">⚡ Client</div>
        </div>
        <div class="sb-section">◆ Navigation</div>
        """, unsafe_allow_html=True)
        nav = st.radio("", ["🏠 Dashboard", "🔮 Nouvelle prédiction"],
                        key="client_nav", label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
        if st.button("🚪 Déconnexion", key="logout_client", use_container_width=True):
            handle_logout()
        st.markdown('</div>', unsafe_allow_html=True)

    if nav == "🏠 Dashboard":
        dashboard_page.render(user, st.session_state.predictions, metadata)
    else:
        prediction_form(model_reg, model_clf, model_wt, scaler_reg, scaler_clf, scaler_wt,
                         wt_encoder, metadata, user)

    st.markdown('<div class="footer">FitMind · Neural Performance Analytics · Neural MLP · '
                f'{n_samples} obs.</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# ADMIN PAGE
# ══════════════════════════════════════════════════════════════════════
def show_admin(model_reg, model_clf, model_wt, scaler_reg, scaler_clf, scaler_wt, wt_encoder, metadata):
    user  = session_manager.get_current_user()
    preds = st.session_state.predictions

    st.markdown(f"""
    <div class="main-header">
        <h1>Fit<span>Mind</span> Admin</h1>
        <p>Tableau de bord — Administration & Monitoring</p>
        <span class="badge">👑 Mode Administrateur</span>
    </div>
    <div class="user-strip">
        <span>Administrateur : <span class="u-name">{user['name']}</span></span>
        <span class="u-role admin">👑 ADMIN</span>
    </div>""", unsafe_allow_html=True)

    # Sidebar admin
    with st.sidebar:
        ini = user.get('initials', 'A')
        st.markdown(f"""
        <div class="sb-user-card">
            <div class="sb-avatar admin-ava">{ini}</div>
            <div class="sb-name">{user['name']}</div>
            <div class="sb-role admin-role">👑 Administrateur</div>
        </div>
        <div class="sb-section">◆ Navigation</div>
        """, unsafe_allow_html=True)

        page = st.radio("", ["📊 Dashboard", "📈 Prédictions", "👥 Utilisateurs", "🔮 Prédire",
                              "🧪 Évaluation", "ℹ️ Info Modèle"],
                        key="admin_nav", label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
        if st.button("🚪 Déconnexion", key="logout_admin", use_container_width=True):
            handle_logout()
        st.markdown('</div>', unsafe_allow_html=True)

    n_users = len(auth_service.list_users())
    n_preds = len(preds)
    avg_cal = np.mean([p['calories'] for p in preds]) if preds else 0

    # ── DASHBOARD ──
    if page == "📊 Dashboard":
        st.markdown("<br>", unsafe_allow_html=True)
        exp_acc = metadata['classification_experience']['metrics_test']['accuracy'] * 100
        c1, c2, c3, c4 = st.columns(4)
        data = [
            (str(n_users),  "Utilisateurs",       "", c1),
            (str(n_preds),  "Prédictions Session", "", c2),
            (f"{avg_cal:.0f}", "Moy. Calories (kcal)", " gold", c3),
            (f"{exp_acc:.1f}%", "Précision Modèle (Niveau)", " gold", c4),
        ]
        for val, lbl, extra, col in data:
            col.markdown(f'<div class="admin-stat{extra}"><span class="as-val">{val}</span><span class="as-lbl">{lbl}</span></div>', unsafe_allow_html=True)

        st.markdown('<span class="sec-title">PRÉDICTIONS RÉCENTES</span>', unsafe_allow_html=True)
        if preds:
            for i, p in enumerate(reversed(preds[-8:])):
                st.markdown(f"""
                <div class="hist-row" style="animation-delay:{i*.05}s">
                    <span class="hist-badge">RÉGR.</span>
                    <span class="hist-val">{p['result']}</span>
                    <span style="font-family:Share Tech Mono,monospace;font-size:.65rem;color:var(--text2)">
                        Niveau : {p.get('level','—')}
                    </span>
                    <span class="hist-time">{p['time']}</span>
                </div>""", unsafe_allow_html=True)

            if len(preds) >= 2:
                st.markdown('<span class="sec-title">ÉVOLUTION CALORIES</span>', unsafe_allow_html=True)
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=list(range(1, len(preds)+1)),
                    y=[p['calories'] for p in preds],
                    mode='lines+markers',
                    line=dict(color='#3A8FD4', width=2),
                    marker=dict(color='#6BB8F0', size=7),
                    fill='tozeroy', fillcolor='rgba(58,143,212,0.07)'
                ))
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(8,16,28,.6)',
                    height=240, margin=dict(l=0,r=0,t=0,b=0),
                    xaxis=dict(showgrid=True, gridcolor='rgba(58,143,212,.07)', color='#6A90AA'),
                    yaxis=dict(showgrid=True, gridcolor='rgba(58,143,212,.07)', color='#6A90AA'),
                    font=dict(family='Rajdhani')
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune prédiction effectuée dans cette session.")

    # ── PRÉDICTIONS ──
    elif page == "📈 Prédictions":
        st.markdown('<span class="sec-title">TOUTES LES PRÉDICTIONS</span>', unsafe_allow_html=True)
        if preds:
            df = pd.DataFrame([{
                'Heure': p['time'], 'Résultat': p['result'],
                'Niveau': p.get('level','—'), 'Calories': f"{p['calories']:.0f}"
            } for p in reversed(preds)])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune prédiction en session.")

    # ── UTILISATEURS ──
    elif page == "👥 Utilisateurs":
        st.markdown('<span class="sec-title">GESTION UTILISATEURS</span>', unsafe_allow_html=True)
        rows = [{
            'Nom': u.username or u.email.split('@')[0], 'Email': u.email,
            'Rôle': '👑 Admin' if u.role == 'admin' else '👤 Client',
            'Méthode': '🔵 Google' if u.auth_provider == 'google_demo' else '📧 Email'
        } for u in auth_service.list_users()]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ── PRÉDIRE ──
    elif page == "🔮 Prédire":
        prediction_form(model_reg, model_clf, model_wt, scaler_reg, scaler_clf, scaler_wt,
                         wt_encoder, metadata, user)

    # ── ÉVALUATION (métriques calculées automatiquement à l'entraînement) ──
    elif page == "🧪 Évaluation":
        show_model_evaluation(metadata)

    # ── INFO MODÈLE ──
    elif page == "ℹ️ Info Modèle":
        show_model_information(metadata)

    if page not in ("🔮 Prédire", "🧪 Évaluation", "ℹ️ Info Modèle"):
        st.markdown('<div class="footer">FitMind Admin · Neural Performance Analytics · Panel d\'administration</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# PAGE — MODEL EVALUATION
# ══════════════════════════════════════════════════════════════════════
def show_model_evaluation(metadata):
    st.markdown('<span class="sec-title">ÉVALUATION AUTOMATIQUE DES MODÈLES</span>', unsafe_allow_html=True)
    st.caption(f"Calculée automatiquement lors du dernier entraînement · {metadata['trained_at']} "
               f"· seed={metadata['seed']} · {metadata['dataset']['n_samples']} échantillons")

    tab_reg, tab_exp, tab_wt = st.tabs(
        ["📐 Régression — Calories", "🏆 Classification — Niveau", "⚠️ Démo — Workout_Type"]
    )

    # ---- Régression ----
    with tab_reg:
        reg = metadata['regression']
        m = reg['metrics_test']
        c1, c2, c3, c4 = st.columns(4)
        for col, val, lbl in zip([c1, c2, c3, c4],
            [f"{m['mae']:.1f}", f"{m['rmse']:.1f}", f"{m['r2']:.4f}", str(reg['epochs_trained'])],
            ["MAE (kcal)", "RMSE (kcal)", "R²", "Époques (early stop)"]):
            col.markdown(f'<div class="metric-box"><div class="value">{val}</div><div class="label">{lbl}</div></div>',
                         unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        cL, cR = st.columns(2)
        with cL:
            st.plotly_chart(ev.training_curves_figure(reg['history'], 'loss', 'val_loss',
                             'Perte (MSE, espace log)', 'MSE'), use_container_width=True)
        with cR:
            st.plotly_chart(ev.training_curves_figure(reg['history'], 'mae', 'val_mae',
                             'MAE (espace log)', 'MAE'), use_container_width=True)
        st.caption(f"Jeu de test : {reg['n_test']} échantillons ({reg['n_train']} en entraînement).")

    # ---- Classification niveau d'expérience ----
    with tab_exp:
        clf = metadata['classification_experience']
        m = clf['metrics_test']
        c1, c2, c3, c4 = st.columns(4)
        for col, val, lbl in zip([c1, c2, c3, c4],
            [f"{m['accuracy']*100:.1f}%", f"{m['precision_macro']*100:.1f}%",
             f"{m['recall_macro']*100:.1f}%", f"{m['f1_macro']*100:.1f}%"],
            ["Accuracy", "Precision (macro)", "Recall (macro)", "F1-score (macro)"]):
            col.markdown(f'<div class="metric-box"><div class="value">{val}</div><div class="label">{lbl}</div></div>',
                         unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        cL, cR = st.columns(2)
        with cL:
            acc_fig = ev.accuracy_curves_figure(clf['history'])
            if acc_fig: st.plotly_chart(acc_fig, use_container_width=True)
        with cR:
            st.plotly_chart(ev.confusion_matrix_figure(m['confusion_matrix'], m['class_names']),
                            use_container_width=True)
        st.caption(f"Jeu de test : {clf['n_test']} échantillons ({clf['n_train']} en entraînement).")

    # ---- Démo Workout_Type ----
    with tab_wt:
        wt = metadata['classification_workout_type']
        m = wt['metrics_test']
        st.warning(wt['disclaimer'])
        c1, c2, c3, c4 = st.columns(4)
        for col, val, lbl in zip([c1, c2, c3, c4],
            [f"{m['accuracy']*100:.1f}%", f"{wt['majority_class_baseline_accuracy']*100:.1f}%",
             f"{m['f1_macro']*100:.1f}%", str(wt['epochs_trained'])],
            ["Accuracy réelle", "Baseline classe majoritaire", "F1-score (macro)", "Époques"]):
            col.markdown(f'<div class="metric-box"><div class="value">{val}</div><div class="label">{lbl}</div></div>',
                         unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        cL, cR = st.columns(2)
        with cL:
            st.plotly_chart(ev.training_curves_figure(wt['history'], 'loss', 'val_loss'),
                            use_container_width=True)
        with cR:
            st.plotly_chart(ev.confusion_matrix_figure(m['confusion_matrix'], m['class_names']),
                            use_container_width=True)
        st.caption("L'accuracy proche de la baseline confirme l'absence de signal exploitable — "
                   "conforme à l'analyse critique menée dans le notebook d'origine.")


# ══════════════════════════════════════════════════════════════════════
# PAGE — MODEL INFORMATION
# ══════════════════════════════════════════════════════════════════════
def show_model_information(metadata):
    st.markdown('<span class="sec-title">INFORMATIONS SUR LES MODÈLES</span>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="hist-row">
        <span class="hist-badge">VERSION</span>
        <span class="hist-val">{metadata['version']}</span>
        <span class="hist-time">Entraîné le {metadata['trained_at']}</span>
    </div>
    """, unsafe_allow_html=True)
    st.info(f"🌱 Seed de reproductibilité : **{metadata['seed']}** — {metadata['reproducibility_note']}")
    st.caption(f"Dataset : `{metadata['dataset']['path']}` · {metadata['dataset']['n_samples']} échantillons au total")

    for key, title in [('regression', '📐 Régression — Calories brûlées'),
                        ('classification_experience', '🏆 Classification — Niveau d\'expérience'),
                        ('classification_workout_type', '⚠️ Démonstration — Workout_Type (non fiable)')]:
        m = metadata[key]
        with st.expander(title, expanded=(key == 'regression')):
            if not m.get('is_reliable', True):
                st.warning(m['disclaimer'])
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
**Architecture**
```
{chr(10).join(m['architecture'])}
```
**Hyperparamètres**
- Optimiseur : `{m['hyperparameters']['optimizer']}`
- Loss : `{m['hyperparameters']['loss']}`
- Batch size : `{m['hyperparameters']['batch_size']}`
- Early stopping : `{m['hyperparameters']['early_stopping_monitor']}` (patience {m['hyperparameters']['early_stopping_patience']})
- Époques effectuées : `{m['epochs_trained']}` / {m['hyperparameters']['epochs_max']} max
                """)
            with c2:
                st.markdown(f"""
**Données**
- Échantillons entraînement : `{m['n_train']}`
- Échantillons test : `{m['n_test']}`
- Variables utilisées ({len(m['features'])}) : {', '.join(f'`{f}`' for f in m['features'])}
- Cible : `{m['target']}`
                """)
                if 'metrics_test' in m:
                    metrics = m['metrics_test']
                    if 'r2' in metrics:
                        st.markdown(f"**Performance** — MAE `{metrics['mae']:.1f}` · RMSE `{metrics['rmse']:.1f}` · R² `{metrics['r2']:.4f}`")
                    else:
                        st.markdown(f"**Performance** — Accuracy `{metrics['accuracy']*100:.1f}%` · F1 (macro) `{metrics['f1_macro']*100:.1f}%`")

            st.markdown("**Domaine de validité (plages vues à l'entraînement)**")
            dist_rows = [{'Variable': f, 'Min': f"{s['min']:.1f}", 'Max': f"{s['max']:.1f}",
                          'Moyenne': f"{s['mean']:.1f}", 'Écart-type': f"{s['std']:.1f}"}
                         for f, s in m['feature_distributions'].items()]
            st.dataframe(pd.DataFrame(dist_rows), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════
# MAIN — CHARGEMENT + ROUTAGE
# ══════════════════════════════════════════════════════════════════════
with st.spinner("⚡ Initialisation des modèles neuraux..."):
    (model_reg, model_clf, model_wt, scaler_reg, scaler_clf, scaler_wt,
     wt_encoder, metadata) = load_or_train_models()

if not session_manager.is_authenticated():
    show_auth()
elif session_manager.get_current_user().get('role') == 'admin':
    show_admin(model_reg, model_clf, model_wt, scaler_reg, scaler_clf, scaler_wt, wt_encoder, metadata)
else:
    show_client(model_reg, model_clf, model_wt, scaler_reg, scaler_clf, scaler_wt, wt_encoder, metadata)
