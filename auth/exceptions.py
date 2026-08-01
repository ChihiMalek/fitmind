"""
exceptions.py — hierarchie d'exceptions du module auth/.

Remplace le pattern historique `(ok, message)` utilise par do_login()/
do_register() dans app.py. Toute erreur d'authentification doit etre une
sous-classe d'AuthError, afin que l'appelant (a terme, app.py) puisse soit
capturer AuthError generiquement, soit reagir a un cas precis.
"""


class AuthError(Exception):
    """Classe de base de toutes les erreurs d'authentification."""


class InvalidCredentials(AuthError):
    """Email inconnu ou mot de passe incorrect."""


class DuplicateEmail(AuthError):
    """Une inscription est tentee avec un email deja utilise."""


class WeakPassword(AuthError):
    """Le mot de passe ne respecte pas la politique de securite."""


class InvalidEmailFormat(AuthError):
    """L'adresse email n'a pas un format valide."""


class UserLocked(AuthError):
    """Le compte est temporairement verrouille (trop d'echecs de connexion)."""


class UserNotFound(AuthError):
    """Aucun utilisateur ne correspond a l'identifiant fourni."""


class AccountDeleted(AuthError):
    """Le compte a ete supprime (soft delete, `deleted_at` non nul)."""


class TokenExpired(AuthError):
    """Le token (reset de mot de passe / verification email) a expire."""


class InvalidToken(AuthError):
    """Le token fourni est invalide, inconnu ou deja utilise."""
