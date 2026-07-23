"""
recommendation_service — logique de recommandation.

Extrait de app.py::prediction_form (bloc "Analyse et recommandations") pour
etre reutilisable a la fois par le formulaire de prediction existant et par
le nouveau Dashboard, sans dupliquer le texte ni la logique.

Ceci reste une version a base de regles simples (pas le futur "AI Coach"
generatif de la phase 5 de la roadmap) — mais c'est la meme logique deja
validee et utilisee dans l'application, deplacee ici.
"""

LEVEL_ACTION_TEXT = [
    "Concentrez-vous sur la régularité et la technique.",
    "Augmentez progressivement l'intensité et la variété.",
    "Pensez à la périodisation et à la récupération active.",
]


def _calories_note(calories: float) -> str:
    if calories < 300:
        return "séance légère, idéale pour la récupération."
    if calories < 600:
        return "séance modérée, idéale pour maintenir la condition physique."
    if calories < 900:
        return "séance intense — excellent travail cardiovasculaire !"
    return "séance de niveau athlétique — performance maximale ! 🔥"


def _bpm_note(avg_bpm: float) -> str:
    if avg_bpm > 170:
        return "⚠️ Zone rouge, surveillez la récupération."
    if avg_bpm > 130:
        return "✅ Zone cardio optimale."
    return "💡 Augmentez l'intensité pour plus d'efficacité."


def get_recommendation(calories: float, level_idx: int, avg_bpm: float, water: float) -> dict:
    """
    Retourne l'analyse complete d'une prediction, plus une action unique et une
    priorite ('good'|'attention') destinees a la carte "Statut & Action" du
    Dashboard.

    {
        'calories_note': str,
        'level_note': str,
        'bpm_note': str,
        'hydration_note': str,
        'hydration_ok': bool,
        'action': str,          # la SEULE action la plus importante a afficher en priorite
        'priority': 'good' | 'attention',
    }
    """
    level_idx = max(0, min(level_idx, len(LEVEL_ACTION_TEXT) - 1))
    hydration_ok = water >= 2.5
    hydration_note = ("✅ Hydratation optimale" if hydration_ok
                       else "⚠️ Hydratation insuffisante — visez 2.5L minimum.")

    # Priorite de l'action unique : hydratation > BPM en zone rouge > conseil de niveau
    if not hydration_ok:
        action = "Buvez au moins 2.5L d'eau lors de votre prochaine séance."
        priority = "attention"
    elif avg_bpm > 170:
        action = "Votre BPM était en zone rouge : privilégiez une séance de récupération active."
        priority = "attention"
    else:
        action = LEVEL_ACTION_TEXT[level_idx]
        priority = "good"

    return {
        'calories_note': _calories_note(calories),
        'level_note': LEVEL_ACTION_TEXT[level_idx],
        'bpm_note': _bpm_note(avg_bpm),
        'hydration_note': hydration_note,
        'hydration_ok': hydration_ok,
        'action': action,
        'priority': priority,
    }
