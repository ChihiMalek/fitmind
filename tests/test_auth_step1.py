"""
test_auth_step1.py — tests unitaires de l'Etape 1 de la Phase 4 (auth/).

Portee stricte de cette etape : auth_config.py, enums.py, exceptions.py,
security.py. Aucun test ici ne touche Streamlit ni SQLite — conformement a
ARCHITECTURE_AUTH_v1.md, ce sont des fonctions pures.

Lancement : python3 -m pytest tests/test_auth_step1.py -v
"""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auth import auth_config
from auth.enums import AuthEventType, Role, TokenPurpose
from auth.exceptions import (
    AccountDeleted,
    AuthError,
    DuplicateEmail,
    InvalidCredentials,
    InvalidEmailFormat,
    InvalidToken,
    TokenExpired,
    UserLocked,
    UserNotFound,
    WeakPassword,
)
from auth.security import (
    hash_password,
    validate_email_format,
    validate_password_strength,
    verify_password,
)


# ─────────────────────────────────────────────────────────────
# security.py — hash_password / verify_password
# ─────────────────────────────────────────────────────────────
class TestHashPassword:
    def test_hash_then_verify_succeeds(self):
        h = hash_password("MotDePasse1")
        assert verify_password("MotDePasse1", h) is True

    def test_verify_fails_with_wrong_password(self):
        h = hash_password("MotDePasse1")
        assert verify_password("AutreChose1", h) is False

    def test_two_hashes_of_same_password_differ(self):
        """Le sel bcrypt doit etre different a chaque appel."""
        h1 = hash_password("MotDePasse1")
        h2 = hash_password("MotDePasse1")
        assert h1 != h2
        # mais les deux doivent rester valides pour verifier le mot de passe
        assert verify_password("MotDePasse1", h1) is True
        assert verify_password("MotDePasse1", h2) is True

    def test_hash_is_never_the_plain_password(self):
        h = hash_password("MotDePasse1")
        assert h != "MotDePasse1"

    def test_verify_password_with_malformed_hash_returns_false(self):
        """Un hash corrompu ne doit jamais authentifier — pas d'exception non plus."""
        assert verify_password("MotDePasse1", "pas-un-hash-bcrypt") is False

    def test_verify_password_with_empty_hash_returns_false(self):
        assert verify_password("MotDePasse1", "") is False


# ─────────────────────────────────────────────────────────────
# security.py — validate_password_strength
# ─────────────────────────────────────────────────────────────
class TestValidatePasswordStrength:
    def test_valid_password_raises_nothing(self):
        validate_password_strength("MotDePasse1")  # ne doit lever aucune exception

    def test_too_short_raises_weak_password(self):
        with pytest.raises(WeakPassword):
            validate_password_strength("Abc1")

    def test_missing_digit_raises_weak_password(self):
        with pytest.raises(WeakPassword):
            validate_password_strength("SansChiffreDuTout")

    def test_missing_letter_raises_weak_password(self):
        with pytest.raises(WeakPassword):
            validate_password_strength("12345678")

    def test_minimum_length_boundary(self):
        """Exactement PASSWORD_MIN_LENGTH caracteres, avec lettre+chiffre -> valide."""
        pwd = "a1" + "b" * (auth_config.PASSWORD_MIN_LENGTH - 2)
        assert len(pwd) == auth_config.PASSWORD_MIN_LENGTH
        validate_password_strength(pwd)  # ne doit pas lever


# ─────────────────────────────────────────────────────────────
# security.py — validate_email_format
# ─────────────────────────────────────────────────────────────
class TestValidateEmailFormat:
    @pytest.mark.parametrize("email", [
        "client@demo.com",
        "admin@fitmind.ai",
        "a.b+c@sub.example.co",
    ])
    def test_valid_emails_raise_nothing(self, email):
        validate_email_format(email)  # ne doit lever aucune exception

    @pytest.mark.parametrize("email", [
        "",
        "pasunemail",
        "sans-arobase.com",
        "@sansutilisateur.com",
        "utilisateur@",
        "utilisateur@sansdomaine",
        "espace dans@email.com",
    ])
    def test_invalid_emails_raise_invalid_email_format(self, email):
        with pytest.raises(InvalidEmailFormat):
            validate_email_format(email)


# ─────────────────────────────────────────────────────────────
# enums.py
# ─────────────────────────────────────────────────────────────
class TestEnums:
    def test_role_values_match_expected_sql_check(self):
        """
        Les valeurs de Role doivent rester strictement synchronisees avec
        CHECK(role IN ('client','admin')) prevu sur la table `users`
        (ARCHITECTURE_AUTH_v1.md §4). Ce test echoue si l'un des deux
        cote (enum Python vs CHECK SQL futur) derive de l'autre.
        """
        assert {r.value for r in Role} == {"client", "admin"}

    def test_role_is_str_enum(self):
        """Role doit se comparer directement a une chaine (ex. row['role'] == Role.ADMIN)."""
        assert Role.ADMIN == "admin"
        assert Role.CLIENT == "client"

    def test_auth_event_type_has_expected_core_events(self):
        values = {e.value for e in AuthEventType}
        for expected in {"register", "login_success", "login_failed", "logout"}:
            assert expected in values

    def test_token_purpose_has_exactly_two_values(self):
        """
        Ancre explicitement la decision d'architecture : un seul mecanisme
        de token, deux finalites preparees pour l'instant.
        """
        assert {p.value for p in TokenPurpose} == {
            "password_reset",
            "email_verification",
        }


# ─────────────────────────────────────────────────────────────
# exceptions.py
# ─────────────────────────────────────────────────────────────
class TestExceptionHierarchy:
    @pytest.mark.parametrize("exc_cls", [
        InvalidCredentials,
        DuplicateEmail,
        WeakPassword,
        InvalidEmailFormat,
        UserLocked,
        UserNotFound,
        AccountDeleted,
        TokenExpired,
        InvalidToken,
    ])
    def test_each_exception_is_subclass_of_auth_error(self, exc_cls):
        assert issubclass(exc_cls, AuthError)

    def test_auth_error_itself_is_an_exception(self):
        assert issubclass(AuthError, Exception)

    def test_catching_auth_error_catches_any_specific_subclass(self):
        """Verifie le contrat exact demande : `except AuthError` doit tout attraper."""
        with pytest.raises(AuthError):
            raise InvalidCredentials("test")


# ─────────────────────────────────────────────────────────────
# auth_config.py
# ─────────────────────────────────────────────────────────────
class TestAuthConfig:
    def test_demo_accounts_have_required_keys(self):
        for account in auth_config.DEMO_ACCOUNTS:
            assert {"email", "username", "password", "role"} <= account.keys()

    def test_demo_account_passwords_pass_the_strength_policy(self):
        """
        Les mots de passe de demo doivent eux-memes respecter la politique
        qu'ils sont censes illustrer — sinon la migration de l'Etape 4
        echouerait silencieusement sur ses propres donnees.
        """
        for account in auth_config.DEMO_ACCOUNTS:
            validate_password_strength(account["password"])  # ne doit pas lever

    def test_demo_account_roles_are_valid(self):
        valid_roles = {r.value for r in Role}
        for account in auth_config.DEMO_ACCOUNTS:
            assert account["role"] in valid_roles

    def test_token_expiry_minutes_covers_both_purposes(self):
        for purpose in TokenPurpose:
            assert purpose.value in auth_config.TOKEN_EXPIRY_MINUTES

    def test_no_streamlit_or_sqlite_import_in_auth_package(self):
        """
        Garde-fou explicite de l'Etape 1 : aucun fichier de auth/ ne doit
        importer streamlit ni sqlite3.
        """
        auth_dir = Path(__file__).resolve().parent.parent / "auth"
        forbidden = re.compile(r"^\s*(import|from)\s+(streamlit|sqlite3)\b", re.MULTILINE)
        offending = []
        for py_file in auth_dir.glob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            if forbidden.search(content):
                offending.append(py_file.name)
        assert offending == [], f"Dependance interdite trouvee dans : {offending}"
