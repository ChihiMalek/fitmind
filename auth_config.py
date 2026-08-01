"""
auth_config.py — constantes de securite de FitMind AI.

Source unique de verite : aucune constante de securite (duree, seuil,
politique de mot de passe...) ne doit etre definie ailleurs dans le
projet. Un futur changement de politique (ex. durcir le mot de passe
minimum) se fait ici, et nulle part ailleurs.

Aucune dependance : ce fichier ne contient que des valeurs pures.
"""

from typing import Final

# ─────────────────────────────────────────────────────────────
# Hachage des mots de passe (bcrypt)
# ─────────────────────────────────────────────────────────────
BCRYPT_ROUNDS: Final[int] = 12  # facteur de cout — voir ARCHITECTURE_AUTH_v1.md §5

# ─────────────────────────────────────────────────────────────
# Politique de mot de passe
# ─────────────────────────────────────────────────────────────
PASSWORD_MIN_LENGTH: Final[int] = 8
PASSWORD_REQUIRE_DIGIT: Final[bool] = True
PASSWORD_REQUIRE_LETTER: Final[bool] = True

# ─────────────────────────────────────────────────────────────
# Verrouillage anti brute-force
# ─────────────────────────────────────────────────────────────
MAX_FAILED_LOGIN_ATTEMPTS: Final[int] = 5
LOCKOUT_DURATION_MINUTES: Final[int] = 15

# ─────────────────────────────────────────────────────────────
# Session applicative (Option A validee : pas de cookies persistants)
# ─────────────────────────────────────────────────────────────
SESSION_TIMEOUT_MINUTES: Final[int] = 120  # expiration par inactivite

# ─────────────────────────────────────────────────────────────
# Tokens (password reset / email verification — prepare, non branche)
# ─────────────────────────────────────────────────────────────
TOKEN_EXPIRY_MINUTES: Final[dict] = {
    "password_reset": 30,
    "email_verification": 1440,  # 24h
}

# ─────────────────────────────────────────────────────────────
# Comptes de demonstration — migres vers SQLite a l'Etape 4,
# mots de passe reharches en bcrypt a ce moment-la.
# ─────────────────────────────────────────────────────────────
DEMO_ACCOUNTS: Final[list] = [
    {
        "email": "admin@fitmind.ai",
        "username": "Admin FitMind",
        "password": "Admin2024!",
        "role": "admin",
    },
    {
        "email": "client@demo.com",
        "username": "Client Demo",
        "password": "Demo2024!",
        "role": "client",
    },
]
