"""
confidence_service — interface stable au-dessus de model_utils.compute_global_confidence.

Existe pour que les pages (Dashboard, puis Historique/Analytics) appellent une
seule fonction de service plutot que d'importer model_utils directement.
La logique de calcul elle-meme n'est PAS reimplementee ici.
"""

from model_utils import compute_global_confidence


def get_confidence(features: dict, feature_distributions: dict) -> dict:
    """
    Retourne {'score': float 0-100, 'level': 'green'|'yellow'|'red', 'details': {...}}.
    Delegue entierement a model_utils.compute_global_confidence.
    """
    return compute_global_confidence(features, feature_distributions)
