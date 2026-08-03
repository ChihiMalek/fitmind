"""
database/repositories/ — acces aux donnees, une classe par domaine.

Aucune logique metier ici (ca vit dans services/), aucun acces a
Streamlit. Chaque methode ouvre sa propre connexion via
database.database.get_connection() (transactionnel, voir ce module) et
retourne des instances de database/models.py, jamais des dicts ou des
sqlite3.Row bruts.
"""
