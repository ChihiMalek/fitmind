"""
test_auth_step3.py — tests de l'Etape 3 de la Phase 4.

Portee : auth/session_manager.py, auth/providers.py, services/auth_service.py.
Aucun test ici ne touche app.py ni dashboard/ (non modifies a cette etape).
Chaque test SQLite tourne sur une base temporaire isolee, jamais sur
data/fitmind.db. st.session_state est remplace par un dict Python nu pour
chaque test (session_manager n'utilise que les operations dict-style).

Lancement : python3 -m pytest tests/test_auth_step3.py -v
"""

import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

import database.database as dbmod
from database.migrations import run_migrations
from database.repositories.auth_log_repository import AuthLogRepository
from database.repositories.user_repository import UserRepository

from auth import providers, session_manager
from auth.auth_config import MAX_FAILED_LOGIN_ATTEMPTS, SESSION_TIMEOUT_MINUTES
from auth.enums import AuthEventType
from auth.exceptions import (
    AccountDeleted,
    AuthError,
    DuplicateEmail,
    InvalidCredentials,
    UserLocked,
    WeakPassword,
)
from auth.security import verify_password

import services.auth_service as auth_service


# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────
@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    """Redirige database.database.DB_PATH vers un fichier temporaire propre a chaque test."""
    db_file = tmp_path / "test_fitmind.db"
    monkeypatch.setattr(dbmod, "DB_PATH", db_file)
    return db_file


@pytest.fixture()
def migrated_db(isolated_db):
    run_migrations()
    return isolated_db


@pytest.fixture(autouse=True)
def fake_session_state(monkeypatch):
    """
    Remplace st.session_state par un dict nu, propre a chaque test.
    session_manager.py n'utilise que des operations dict-style ([], .get(),
    .pop()) : un dict Python suffit, pas besoin du vrai objet Streamlit.
    """
    fake = {}
    monkeypatch.setattr(st, "session_state", fake)
    return fake


# ─────────────────────────────────────────────────────────────
# session_manager.py
# ─────────────────────────────────────────────────────────────
class TestSessionManager:
    def test_start_session_stores_user(self, fake_session_state):
        session_manager.start_session({"id": 1, "email": "a@test.com"})
        assert session_manager.get_current_user() == {"id": 1, "email": "a@test.com"}

    def test_get_current_user_returns_none_when_no_session(self, fake_session_state):
        assert session_manager.get_current_user() is None

    def test_is_authenticated_false_without_session(self, fake_session_state):
        assert session_manager.is_authenticated() is False

    def test_is_authenticated_true_after_start_session(self, fake_session_state):
        session_manager.start_session({"id": 1, "email": "a@test.com"})
        assert session_manager.is_authenticated() is True

    def test_clear_session_removes_all_session_keys(self, fake_session_state):
        session_manager.start_session({"id": 1, "email": "a@test.com"})
        session_manager.clear_session()
        assert session_manager.get_current_user() is None
        assert session_manager.is_authenticated() is False
        assert fake_session_state == {}

    def test_clear_session_is_safe_when_nothing_to_clear(self, fake_session_state):
        session_manager.clear_session()  # ne doit lever aucune exception

    def test_touch_session_updates_last_activity(self, fake_session_state):
        session_manager.start_session({"id": 1, "email": "a@test.com"})
        old_activity = fake_session_state[session_manager._LAST_ACTIVITY_KEY]
        fake_session_state[session_manager._LAST_ACTIVITY_KEY] = (
            datetime.now(timezone.utc) - timedelta(minutes=5)
        ).isoformat()
        session_manager.touch_session()
        new_activity = fake_session_state[session_manager._LAST_ACTIVITY_KEY]
        assert new_activity != old_activity

    def test_touch_session_noop_without_session(self, fake_session_state):
        session_manager.touch_session()  # ne doit lever aucune exception
        assert session_manager._LAST_ACTIVITY_KEY not in fake_session_state

    def test_is_session_expired_true_without_session(self, fake_session_state):
        assert session_manager.is_session_expired() is True

    def test_is_session_expired_false_when_recent(self, fake_session_state):
        session_manager.start_session({"id": 1, "email": "a@test.com"})
        assert session_manager.is_session_expired() is False

    def test_is_session_expired_true_after_timeout(self, fake_session_state):
        """Utilise SESSION_TIMEOUT_MINUTES depuis auth_config.py, aucune valeur codee en dur."""
        session_manager.start_session({"id": 1, "email": "a@test.com"})
        expired_activity = (
            datetime.now(timezone.utc) - timedelta(minutes=SESSION_TIMEOUT_MINUTES + 1)
        ).isoformat()
        fake_session_state[session_manager._LAST_ACTIVITY_KEY] = expired_activity
        assert session_manager.is_session_expired() is True

    def test_is_authenticated_clears_expired_session_automatically(self, fake_session_state):
        session_manager.start_session({"id": 1, "email": "a@test.com"})
        expired_activity = (
            datetime.now(timezone.utc) - timedelta(minutes=SESSION_TIMEOUT_MINUTES + 1)
        ).isoformat()
        fake_session_state[session_manager._LAST_ACTIVITY_KEY] = expired_activity
        assert session_manager.is_authenticated() is False
        assert session_manager.get_current_user() is None  # nettoyage automatique


# ─────────────────────────────────────────────────────────────
# providers.py
# ─────────────────────────────────────────────────────────────
class TestProviders:
    def test_provider_user_data_is_a_plain_dataclass(self):
        data = providers.ProviderUserData(email="a@test.com", username="a", provider_uid="a@test.com")
        assert data.email == "a@test.com"

    def test_demo_google_provider_satisfies_auth_provider_protocol(self):
        assert isinstance(providers.DemoGoogleProvider(), providers.AuthProvider)

    def test_demo_google_provider_accepts_valid_email(self):
        result = providers.DemoGoogleProvider().authenticate({"email": "user@gmail.com"})
        assert result.email == "user@gmail.com"
        assert result.username == "user"

    def test_demo_google_provider_rejects_missing_at_sign(self):
        with pytest.raises(InvalidCredentials):
            providers.DemoGoogleProvider().authenticate({"email": "pasunemail"})

    def test_demo_google_provider_rejects_empty_credentials(self):
        with pytest.raises(InvalidCredentials):
            providers.DemoGoogleProvider().authenticate({})

    def test_providers_registry_contains_google_demo(self):
        assert "google_demo" in providers.PROVIDERS
        assert isinstance(providers.PROVIDERS["google_demo"], providers.DemoGoogleProvider)


# ─────────────────────────────────────────────────────────────
# auth_service.register()
# ─────────────────────────────────────────────────────────────
class TestRegister:
    def test_register_success_returns_user(self, migrated_db):
        user = auth_service.register("alice@test.com", "Password1", username="Alice")
        assert user.id is not None
        assert user.email == "alice@test.com"
        assert user.password_hash != "Password1"  # jamais stocke en clair

    def test_register_duplicate_email_raises(self, migrated_db):
        auth_service.register("dup@test.com", "Password1")
        with pytest.raises(DuplicateEmail):
            auth_service.register("dup@test.com", "Password2")

    def test_register_weak_password_raises(self, migrated_db):
        with pytest.raises(WeakPassword):
            auth_service.register("weak@test.com", "abc")

    def test_register_invalid_email_raises(self, migrated_db):
        from auth.exceptions import InvalidEmailFormat
        with pytest.raises(InvalidEmailFormat):
            auth_service.register("pasunemail", "Password1")

    def test_register_creates_audit_log_entry(self, migrated_db):
        user = auth_service.register("logtest@test.com", "Password1")
        logs = AuthLogRepository().list_for_user(user.id)
        assert len(logs) == 1
        assert logs[0].event_type == AuthEventType.REGISTER.value

    def test_register_does_not_start_a_session(self, migrated_db, fake_session_state):
        auth_service.register("nosession@test.com", "Password1")
        assert session_manager.get_current_user() is None


# ─────────────────────────────────────────────────────────────
# auth_service.login()
# ─────────────────────────────────────────────────────────────
class TestLogin:
    def test_login_success_returns_user_and_never_starts_a_session(self, migrated_db, fake_session_state):
        """
        Depuis la decorrelation post-Etape 3, login() n'ouvre plus jamais
        de session lui-meme : il authentifie et retourne un User, un point
        c'est tout. C'est a l'appelant (app.py a l'Etape 4) d'appeler
        session_manager.start_session() s'il le souhaite.
        """
        auth_service.register("bob@test.com", "Password1")
        user = auth_service.login("bob@test.com", "Password1")
        assert user.email == "bob@test.com"
        assert session_manager.is_authenticated() is False
        assert session_manager.get_current_user() is None

    def test_login_updates_last_login_and_resets_attempts(self, migrated_db):
        auth_service.register("carla@test.com", "Password1")
        UserRepository().increment_failed_attempts(
            UserRepository().get_by_email("carla@test.com").id
        )
        user = auth_service.login("carla@test.com", "Password1")
        assert user.last_login_at is not None
        assert user.failed_login_attempts == 0

    def test_login_wrong_password_raises_invalid_credentials(self, migrated_db):
        auth_service.register("dan@test.com", "Password1")
        with pytest.raises(InvalidCredentials):
            auth_service.login("dan@test.com", "MauvaisMdp1")

    def test_login_wrong_password_increments_failed_attempts(self, migrated_db):
        auth_service.register("eve@test.com", "Password1")
        with pytest.raises(InvalidCredentials):
            auth_service.login("eve@test.com", "Mauvais1")
        user = UserRepository().get_by_email("eve@test.com")
        assert user.failed_login_attempts == 1

    def test_login_nonexistent_user_raises_invalid_credentials(self, migrated_db):
        """Meme exception que mot de passe incorrect : ne revele jamais si l'email existe."""
        with pytest.raises(InvalidCredentials):
            auth_service.login("inconnu@test.com", "Password1")

    def test_login_does_not_start_session_on_failure(self, migrated_db, fake_session_state):
        auth_service.register("fail@test.com", "Password1")
        with pytest.raises(InvalidCredentials):
            auth_service.login("fail@test.com", "Mauvais1")
        assert session_manager.get_current_user() is None

    def test_login_deleted_account_raises_account_deleted(self, migrated_db):
        auth_service.register("del@test.com", "Password1")
        user = UserRepository().get_by_email("del@test.com")
        UserRepository().soft_delete(user.id)
        with pytest.raises(AccountDeleted):
            auth_service.login("del@test.com", "Password1")

    def test_login_locks_account_after_max_failed_attempts(self, migrated_db):
        auth_service.register("locktest@test.com", "Password1")
        for _ in range(MAX_FAILED_LOGIN_ATTEMPTS):
            with pytest.raises(InvalidCredentials):
                auth_service.login("locktest@test.com", "Mauvais1")
        user = UserRepository().get_by_email("locktest@test.com")
        assert user.locked_until is not None

    def test_login_raises_user_locked_even_with_correct_password_once_locked(self, migrated_db):
        auth_service.register("locktest2@test.com", "Password1")
        for _ in range(MAX_FAILED_LOGIN_ATTEMPTS):
            with pytest.raises(InvalidCredentials):
                auth_service.login("locktest2@test.com", "Mauvais1")
        with pytest.raises(UserLocked):
            auth_service.login("locktest2@test.com", "Password1")  # bon mot de passe, compte verrouille

    def test_login_success_creates_exactly_one_audit_log(self, migrated_db):
        auth_service.register("auditlog@test.com", "Password1")
        user = UserRepository().get_by_email("auditlog@test.com")
        logs_before = AuthLogRepository().list_for_user(user.id)  # 1 : REGISTER
        auth_service.login("auditlog@test.com", "Password1")
        logs_after = AuthLogRepository().list_for_user(user.id)
        assert len(logs_after) == len(logs_before) + 1
        assert logs_after[0].event_type == AuthEventType.LOGIN_SUCCESS.value

    def test_login_failure_creates_no_audit_log(self, migrated_db):
        """
        Perimetre audit explicite de l'Etape 3 : seuls REGISTER/LOGIN/LOGOUT
        sont journalises — un echec de connexion n'ajoute aucune ligne.
        """
        auth_service.register("nofaillog@test.com", "Password1")
        user = UserRepository().get_by_email("nofaillog@test.com")
        logs_before = len(AuthLogRepository().list_for_user(user.id))
        with pytest.raises(InvalidCredentials):
            auth_service.login("nofaillog@test.com", "Mauvais1")
        logs_after = len(AuthLogRepository().list_for_user(user.id))
        assert logs_after == logs_before


# ─────────────────────────────────────────────────────────────
# auth_service.logout()
# ─────────────────────────────────────────────────────────────
class TestLogout:
    def test_logout_writes_audit_log_with_given_user_id(self, migrated_db):
        user = auth_service.register("logout2@test.com", "Password1")
        auth_service.logout(user.id)
        logs = AuthLogRepository().list_for_user(user.id)
        assert any(log.event_type == AuthEventType.LOGOUT.value for log in logs)

    def test_logout_without_user_id_does_not_crash(self, migrated_db):
        auth_service.logout()  # ne doit lever aucune exception, user_id=None accepte

    def test_logout_never_touches_session_manager(self, migrated_db, fake_session_state):
        """
        Coeur de la decorrelation demandee : logout() ne doit ni lire, ni
        modifier, ni detruire une session existante — meme si une session
        Streamlit est active au moment de l'appel, elle doit rester
        parfaitement intacte apres auth_service.logout(). C'est a
        l'appelant (app.py) d'appeler explicitement
        session_manager.clear_session() lui-meme.
        """
        user = auth_service.register("stillsession@test.com", "Password1")
        session_manager.start_session({"email": "stillsession@test.com", "name": "x",
                                        "initials": "x", "role": "client"})
        auth_service.logout(user.id)
        assert session_manager.is_authenticated() is True  # session INTACTE
        assert session_manager.get_current_user() is not None

    def test_logout_accepts_a_user_id_unrelated_to_any_session(self, migrated_db, fake_session_state):
        """auth_service n'a plus aucun moyen de connaitre 'qui est connecte' : il fait confiance a l'appelant."""
        user = auth_service.register("explicitid@test.com", "Password1")
        auth_service.logout(user.id)  # aucune session ouverte, ca ne change rien pour logout()
        logs = AuthLogRepository().list_for_user(user.id)
        logout_logs = [l for l in logs if l.event_type == AuthEventType.LOGOUT.value]
        assert len(logout_logs) == 1
        assert logout_logs[0].user_id == user.id


# ─────────────────────────────────────────────────────────────
# auth_service.login_with_provider() — Google Demo
# ─────────────────────────────────────────────────────────────
class TestLoginWithProvider:
    def test_google_demo_creates_account_automatically(self, migrated_db, fake_session_state):
        user = auth_service.login_with_provider("google_demo", {"email": "newuser@gmail.com"})
        assert user.email == "newuser@gmail.com"
        assert user.auth_provider == "google_demo"

    def test_google_demo_reuses_existing_account(self, migrated_db, fake_session_state):
        auth_service.register("existing@gmail.com", "Password1")
        user = auth_service.login_with_provider("google_demo", {"email": "existing@gmail.com"})
        all_users = UserRepository().list_users()
        matching = [u for u in all_users if u.email == "existing@gmail.com"]
        assert len(matching) == 1  # pas de doublon cree

    def test_google_demo_never_starts_a_session(self, migrated_db, fake_session_state):
        auth_service.login_with_provider("google_demo", {"email": "session@gmail.com"})
        assert session_manager.is_authenticated() is False

    def test_google_demo_invalid_email_raises_invalid_credentials(self, migrated_db, fake_session_state):
        with pytest.raises(InvalidCredentials):
            auth_service.login_with_provider("google_demo", {"email": "pasunemail"})

    def test_google_demo_deleted_account_raises_account_deleted(self, migrated_db, fake_session_state):
        auth_service.register("deletedgoogle@gmail.com", "Password1")
        user = UserRepository().get_by_email("deletedgoogle@gmail.com")
        UserRepository().soft_delete(user.id)
        with pytest.raises(AccountDeleted):
            auth_service.login_with_provider("google_demo", {"email": "deletedgoogle@gmail.com"})

    def test_unknown_provider_name_raises_key_error(self, migrated_db, fake_session_state):
        with pytest.raises(KeyError):
            auth_service.login_with_provider("microsoft_oauth_inexistant", {"email": "a@test.com"})

    def test_google_demo_updates_last_login(self, migrated_db, fake_session_state):
        user = auth_service.login_with_provider("google_demo", {"email": "lastlogin@gmail.com"})
        assert user.last_login_at is not None

    def test_google_demo_always_creates_client_role_never_admin(self, migrated_db, fake_session_state):
        """
        Garde-fou de securite explicite (revue Etape 3, point 5) : un compte
        cree via un provider externe ne doit jamais pouvoir devenir admin.
        """
        user = auth_service.login_with_provider("google_demo", {"email": "roletest@gmail.com"})
        assert user.role == "client"
        assert user.role != "admin"


# ─────────────────────────────────────────────────────────────
# auth_service.change_password()
# ─────────────────────────────────────────────────────────────
class TestChangePassword:
    def test_change_password_success(self, migrated_db):
        user = auth_service.register("pwchange@test.com", "OldPassword1")
        auth_service.change_password(user.id, "OldPassword1", "NewPassword2")
        updated = UserRepository().get_by_id(user.id)
        assert verify_password("NewPassword2", updated.password_hash) is True
        assert verify_password("OldPassword1", updated.password_hash) is False

    def test_change_password_wrong_old_password_raises(self, migrated_db):
        user = auth_service.register("pwchange2@test.com", "OldPassword1")
        with pytest.raises(InvalidCredentials):
            auth_service.change_password(user.id, "MauvaisAncien1", "NewPassword2")

    def test_change_password_weak_new_password_raises(self, migrated_db):
        user = auth_service.register("pwchange3@test.com", "OldPassword1")
        with pytest.raises(WeakPassword):
            auth_service.change_password(user.id, "OldPassword1", "abc")

    def test_change_password_nonexistent_user_raises(self, migrated_db):
        with pytest.raises(InvalidCredentials):
            auth_service.change_password(999999, "peu importe", "NewPassword2")

    def test_change_password_old_password_no_longer_works_for_login(self, migrated_db, fake_session_state):
        user = auth_service.register("pwchange4@test.com", "OldPassword1")
        auth_service.change_password(user.id, "OldPassword1", "NewPassword2")
        with pytest.raises(InvalidCredentials):
            auth_service.login("pwchange4@test.com", "OldPassword1")
        auth_service.login("pwchange4@test.com", "NewPassword2")  # ne doit pas lever


# ─────────────────────────────────────────────────────────────
# auth_service.to_session_dict()
# ─────────────────────────────────────────────────────────────
class TestToSessionDict:
    def test_shape_matches_expected_keys(self, migrated_db):
        user = auth_service.register("shape@test.com", "Password1", username="Shape Test")
        d = auth_service.to_session_dict(user)
        assert set(d.keys()) == {"email", "name", "initials", "role"}

    def test_never_contains_password_hash(self, migrated_db):
        user = auth_service.register("nohash@test.com", "Password1")
        d = auth_service.to_session_dict(user)
        assert "password_hash" not in d
        assert "password" not in d

    def test_initials_from_two_word_name(self, migrated_db):
        user = auth_service.register("twoword@test.com", "Password1", username="Client Demo")
        assert auth_service.to_session_dict(user)["initials"] == "CD"

    def test_initials_from_single_word_name(self, migrated_db):
        user = auth_service.register("oneword@test.com", "Password1", username="Solo")
        assert auth_service.to_session_dict(user)["initials"] == "S"

    def test_name_falls_back_to_email_prefix_when_no_username(self, migrated_db):
        user = auth_service.register("noname@test.com", "Password1")
        assert auth_service.to_session_dict(user)["name"] == "noname"

    def test_role_is_preserved(self, migrated_db):
        user = auth_service.register("roletest@test.com", "Password1")
        assert auth_service.to_session_dict(user)["role"] == "client"


# ─────────────────────────────────────────────────────────────
# Contraintes d'architecture (garde-fous automatises)
# ─────────────────────────────────────────────────────────────
class TestArchitectureConstraints:
    def test_auth_service_never_imports_sqlite3_or_streamlit(self):
        content = (PROJECT_ROOT / "services" / "auth_service.py").read_text(encoding="utf-8")
        assert "import sqlite3" not in content
        assert "import streamlit" not in content
        # Le docstring du module MENTIONNE volontairement "st.session_state" pour
        # expliquer que ce fichier ne doit jamais y toucher directement — on verifie
        # donc l'absence d'un appel reel (st.session_state[...]/.get/.pop), pas la
        # simple presence de la chaine dans un commentaire.
        assert "st.session_state[" not in content
        assert "st.session_state.get" not in content
        assert "st.session_state.pop" not in content

    def test_auth_service_never_imports_session_manager(self):
        """
        Garde-fou de la decorrelation demandee : auth_service.py doit rester
        totalement independant du mecanisme de session, y compris de
        auth.session_manager (pas seulement de streamlit directement).
        C'est ce qui rend le service reutilisable tel quel par une future
        API REST/JWT ou une application mobile sans aucune modification.

        Le docstring du module MENTIONNE volontairement "session_manager"
        pour expliquer cette regle — on cherche donc un import reel, pas
        la simple presence du mot dans un commentaire.
        """
        import ast
        tree = ast.parse((PROJECT_ROOT / "services" / "auth_service.py").read_text(encoding="utf-8"))
        imported_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported_names.append(node.module or "")
                imported_names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.Import):
                imported_names.extend(alias.name for alias in node.names)
        assert not any("session_manager" in name for name in imported_names)

    def test_providers_never_imports_sqlite3(self):
        content = (PROJECT_ROOT / "auth" / "providers.py").read_text(encoding="utf-8")
        assert "import sqlite3" not in content
        assert "import streamlit" not in content

    def test_session_manager_is_the_only_auth_file_using_streamlit(self):
        auth_dir = PROJECT_ROOT / "auth"
        offenders = []
        for py_file in auth_dir.glob("*.py"):
            if py_file.name == "session_manager.py":
                continue
            content = py_file.read_text(encoding="utf-8")
            if "import streamlit" in content:
                offenders.append(py_file.name)
        assert offenders == []

    def test_all_public_auth_service_exceptions_are_auth_error_subclasses(self):
        for exc_cls in (InvalidCredentials, DuplicateEmail, WeakPassword, AccountDeleted, UserLocked):
            assert issubclass(exc_cls, AuthError)

    def test_register_never_raises_a_bare_tuple_style_result(self, migrated_db):
        """register() doit retourner un User, jamais un tuple (ok, message)."""
        result = auth_service.register("tuplecheck@test.com", "Password1")
        assert not isinstance(result, tuple)

    def test_login_raises_instead_of_returning_false(self, migrated_db):
        with pytest.raises(AuthError):
            auth_service.login("inexistant@test.com", "Password1")

    def test_all_public_methods_have_docstring_and_type_annotations(self):
        """
        Revue Etape 3, point 9 : chaque fonction/methode publique de
        session_manager.py, providers.py et auth_service.py doit avoir une
        docstring et des annotations de type (arguments + retour).
        """
        import ast
        files = ["auth/session_manager.py", "auth/providers.py", "services/auth_service.py"]
        problems = []
        for fname in files:
            tree = ast.parse((PROJECT_ROOT / fname).read_text(encoding="utf-8"), fname)
            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef) or node.name.startswith("_"):
                    continue
                if ast.get_docstring(node) is None:
                    problems.append(f"{fname}:{node.name} — docstring manquante")
                if node.returns is None:
                    problems.append(f"{fname}:{node.name} — annotation de retour manquante")
                for arg in node.args.args:
                    if arg.arg != "self" and arg.annotation is None:
                        problems.append(f"{fname}:{node.name}({arg.arg}) — annotation manquante")
        assert problems == [], "\n".join(problems)

    def test_provider_user_data_is_independent_of_sqlite(self):
        """Revue Etape 3, point 10 : providers.py ne connait pas SQLite."""
        content = (PROJECT_ROOT / "auth" / "providers.py").read_text(encoding="utf-8")
        assert "sqlite3" not in content
        assert "database" not in content

    def test_no_circular_dependency_between_auth_services_database(self):
        """
        Revue Etape 3, point 11 : auth/ ne doit jamais importer database/ ou
        services/ ; database/ ne doit jamais importer auth/ ou services/.
        Seul services/ est autorise a importer les deux (sens unique de la
        Clean Architecture : Services -> Repositories -> Database, et
        Services -> auth/).
        """
        problems = []
        for py_file in (PROJECT_ROOT / "auth").glob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            if "import database" in content or "from database" in content:
                problems.append(f"auth/{py_file.name} importe database/")
            if "import services" in content or "from services" in content:
                problems.append(f"auth/{py_file.name} importe services/")
        for py_file in (PROJECT_ROOT / "database").rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            if "import auth" in content or "from auth" in content:
                problems.append(f"database/{py_file.relative_to(PROJECT_ROOT)} importe auth/")
            if "import services" in content or "from services" in content:
                problems.append(f"database/{py_file.relative_to(PROJECT_ROOT)} importe services/")
        assert problems == [], "\n".join(problems)
