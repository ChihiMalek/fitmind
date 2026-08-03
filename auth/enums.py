"""
enums.py — enumerations partagees du module auth/.

Les valeurs de Role doivent rester strictement synchronisees avec la
contrainte CHECK(role IN (...)) prevue sur la table `users`
(voir ARCHITECTURE_AUTH_v1.md §4). AuthEventType et TokenPurpose ne sont
volontairement pas contraintes par un CHECK SQL equivalent : elles sont
amenees a grandir (nouveaux evenements d'audit, nouveaux usages de
token) sans que ca doive declencher une migration de schema.
"""

from enum import Enum


class Role(str, Enum):
    """Roles applicatifs. Valeurs alignees avec le CHECK SQL de `users.role`."""

    CLIENT = "client"
    ADMIN = "admin"


class AuthEventType(str, Enum):
    """
    Types d'evenements journalises dans `auth_logs`.

    Extensible sans migration : `auth_logs.event_type` est une colonne TEXT
    libre en base, validee uniquement ici, cote Python.
    """

    REGISTER = "register"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_DELETED = "account_deleted"
    ROLE_CHANGED = "role_changed"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    EMAIL_VERIFIED = "email_verified"


class TokenPurpose(str, Enum):
    """
    Finalites possibles d'une ligne de `auth_tokens`.

    Un seul mecanisme de token a duree de vie limitee, reutilise pour
    plusieurs usages (voir ARCHITECTURE_AUTH_v1.md §3) — evite de creer
    une table par fonctionnalite.
    """

    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
