"""
database/ — couche de persistance de FitMind AI.

database.py    : connexion SQLite + transactions, rien d'autre.
models.py       : dataclasses des entites (User, Prediction, Goal, Settings).
migrations.py   : creation/mise a jour idempotente du schema.
repositories/   : acces aux donnees, une classe par domaine (aucune logique metier).
seed.py         : donnees de demonstration, execution manuelle uniquement.

Aucun fichier de ce package ne contient de logique metier (calculs, regles
de recommandation, agregations statistiques) : ca reste dans services/,
comme etabli en Phase 2.
"""
