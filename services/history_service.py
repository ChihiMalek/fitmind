"""
history_service — agregations sur l'historique de predictions (session-only
pour l'instant, remplace par une vraie requete SQLite a la phase Historique
de la roadmap sans changer la forme des donnees retournees ici).
"""

from collections import Counter


def get_latest(predictions: list) -> dict | None:
    """Derniere prediction de la session, ou None si aucune."""
    return predictions[-1] if predictions else None


def get_summary(predictions: list) -> dict:
    """
    Agregations reutilisables par le Dashboard et par les futures pages
    Historique/Analytics.

    {
        'count': int,
        'avg_calories': float,
        'total_calories': float,
        'best_session': dict | None,      # prediction avec le plus de calories
        'trend': 'up' | 'down' | 'stable' | 'n/a',
        'workout_type_distribution': {'Cardio': n, 'HIIT': n, ...},
    }
    """
    if not predictions:
        return {
            'count': 0, 'avg_calories': 0.0, 'total_calories': 0.0,
            'best_session': None, 'trend': 'n/a', 'workout_type_distribution': {},
        }

    calories_list = [p['calories'] for p in predictions]
    total = sum(calories_list)
    avg = total / len(predictions)
    best = max(predictions, key=lambda p: p['calories'])

    trend = 'n/a'
    if len(predictions) >= 2:
        mid = len(predictions) // 2
        first_half_avg = sum(calories_list[:mid]) / mid if mid else calories_list[0]
        second_half_avg = sum(calories_list[mid:]) / (len(calories_list) - mid)
        if second_half_avg > first_half_avg * 1.05:
            trend = 'up'
        elif second_half_avg < first_half_avg * 0.95:
            trend = 'down'
        else:
            trend = 'stable'

    wt_counts = Counter(p.get('workout_type') for p in predictions if p.get('workout_type'))

    return {
        'count': len(predictions),
        'avg_calories': avg,
        'total_calories': total,
        'best_session': best,
        'trend': trend,
        'workout_type_distribution': dict(wt_counts),
    }
