"""
security.py — primitives de securite du module auth/.

Fonctions pures : aucun acces a la base de donnees, a Streamlit ou a
st.session_state. Isole volontairement le code sensible (hachage de mot
de passe) dans un seul fichier, facile a auditer et a faire evoluer
(ex. migrer de bcrypt vers Argon2 plus tard sans toucher aux appelants).

Voir ARCHITECTURE_AUTH_v1.md §5 pour la justification du choix bcrypt.
"""

import re

import bcrypt

from auth.auth_config import (
    BCRYPT_ROUNDS,
    PASSWORD_MIN_LENGTH,
    PASSWORD_REQUIRE_DIGIT,
    PASSWORD_REQUIRE_LETTER,
)
from auth.exceptions import InvalidEmailFormat, WeakPassword

# Regex pragmatique de validation de format (pas de verification de
# delivrabilite — hors perimetre, necessiterait un envoi d'email reel).
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(plain_password: str) -> str:
    """
    Hache un mot de passe en clair avec bcrypt.

    Le sel est genere et integre automatiquement au hash retourne : deux
    appels avec le meme mot de passe produisent deux hash differents.

    Args:
        plain_password: mot de passe en clair.

    Returns:
        Le hash bcrypt, encode en str (utf-8), pret a etre stocke.
    """
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Verifie qu'un mot de passe en clair correspond a un hash bcrypt.

    Args:
        plain_password: mot de passe en clair fourni par l'utilisateur.
        password_hash: hash bcrypt stocke (tel que retourne par hash_password).

    Returns:
        True si le mot de passe correspond, False sinon. Ne leve jamais
        d'exception pour un hash malforme — retourne False (defensif :
        un hash corrompu ne doit jamais authentifier un utilisateur).
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), password_hash.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


def validate_password_strength(plain_password: str) -> None:
    """
    Valide qu'un mot de passe respecte la politique de securite courante
    (voir auth_config.py). Ne retourne rien : une politique respectee
    n'a rien a signaler.

    Args:
        plain_password: mot de passe en clair a valider.

    Raises:
        WeakPassword: si une regle de la politique n'est pas respectee.
    """
    if len(plain_password) < PASSWORD_MIN_LENGTH:
        raise WeakPassword(
            f"Le mot de passe doit contenir au moins {PASSWORD_MIN_LENGTH} caracteres."
        )
    if PASSWORD_REQUIRE_DIGIT and not any(c.isdigit() for c in plain_password):
        raise WeakPassword("Le mot de passe doit contenir au moins un chiffre.")
    if PASSWORD_REQUIRE_LETTER and not any(c.isalpha() for c in plain_password):
        raise WeakPassword("Le mot de passe doit contenir au moins une lettre.")


def validate_email_format(email: str) -> None:
    """
    Valide le format d'une adresse email (syntaxe uniquement, pas de
    verification de delivrabilite).

    Args:
        email: adresse a valider.

    Raises:
        InvalidEmailFormat: si le format ne correspond pas a un email valide.
    """
    if not email or not _EMAIL_PATTERN.match(email):
        raise InvalidEmailFormat(f"Format d'email invalide : {email!r}")
