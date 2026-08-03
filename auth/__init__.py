"""
auth/ — module d'authentification de FitMind AI.

Etape 1 de la Phase 4 : socle pur, sans aucune dependance a Streamlit, a
SQLite ou aux autres couches du projet (services/, database/, dashboard/).

Contenu de cette etape :
    auth_config.py  : constantes de securite (source unique, voir ce fichier).
    enums.py         : Role, AuthEventType, TokenPurpose.
    exceptions.py    : hierarchie AuthError, remplace le pattern (ok, message).
    security.py      : hachage bcrypt + validations mot de passe / email.

Reference : ARCHITECTURE_AUTH_v1.md (racine du depot).
"""
