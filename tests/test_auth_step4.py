"""
test_auth_step4.py — tests de l'Etape 4 de la Phase 4.

Portee : les deux ajouts a services/auth_service.py necessaires a
l'integration dans app.py (list_users, ensure_seed_account), et
l'idempotence du seeding des comptes de demonstration tel qu'il sera
appele par app.py. app.py lui-meme n'est pas importe dans ces tests : il
execute du code Streamlit au niveau module (chargement des modeles,
routage) qui ne peut pas s'executer proprement hors d'un `streamlit run`
reel — la verification de l'integration app.py se fait par smoke test
(voir rapport), pas par import direct.

Lancement : python3 -m pytest tests/test_auth_step4.py -v
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import database.database as dbmod
from database.migrations import run_migrations
from database.repositories.user_repository import UserRepository

from auth.auth_config import DEMO_ACCOUNTS
from auth.exceptions import DuplicateEmail, InvalidEmailFormat, WeakPassword
from auth.security import verify_password

import services.auth_service as auth_service


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test_fitmind.db"
    monkeypatch.setattr(dbmod, "DB_PATH", db_file)
    return db_file


@pytest.fixture()
def migrated_db(isolated_db):
    run_migrations()
    return isolated_db


def seed_demo_accounts():
    """Reproduit exactement l'appel que app.py effectue au demarrage."""
    for account in DEMO_ACCOUNTS:
        auth_service.ensure_seed_account(
            email=account["email"],
            password=account["password"],
            username=account["username"],
            role=account["role"],
        )


# ─────────────────────────────────────────────────────────────
# auth_service.list_users()
# ─────────────────────────────────────────────────────────────
class TestListUsers:
    def test_empty_by_default(self, migrated_db):
        assert auth_service.list_users() == []

    def test_returns_all_created_users(self, migrated_db):
        auth_service.register("a@test.com", "Password1")
        auth_service.register("b@test.com", "Password1")
        users = auth_service.list_users()
        assert {u.email for u in users} == {"a@test.com", "b@test.com"}

    def test_excludes_deleted_by_default(self, migrated_db):
        u = auth_service.register("del@test.com", "Password1")
        UserRepository().soft_delete(u.id)
        assert "del@test.com" not in {x.email for x in auth_service.list_users()}

    def test_include_deleted_when_requested(self, migrated_db):
        u = auth_service.register("del2@test.com", "Password1")
        UserRepository().soft_delete(u.id)
        assert "del2@test.com" in {x.email for x in auth_service.list_users(include_deleted=True)}

    def test_returns_user_dataclass_not_dict(self, migrated_db):
        auth_service.register("shape@test.com", "Password1")
        users = auth_service.list_users()
        assert hasattr(users[0], "password_hash")  # confirme que c'est bien un User, pas un dict filtre


# ─────────────────────────────────────────────────────────────
# auth_service.ensure_seed_account()
# ─────────────────────────────────────────────────────────────
class TestEnsureSeedAccount:
    def test_creates_account_with_explicit_role(self, migrated_db):
        user = auth_service.ensure_seed_account(
            "admin@fitmind.ai", "Admin2024!", "Admin FitMind", "admin"
        )
        assert user.role == "admin"
        assert user.email == "admin@fitmind.ai"

    def test_password_is_bcrypt_hashed(self, migrated_db):
        user = auth_service.ensure_seed_account(
            "hashcheck@test.com", "Demo2024!", "Demo", "client"
        )
        assert user.password_hash != "Demo2024!"
        assert verify_password("Demo2024!", user.password_hash) is True

    def test_idempotent_second_call_does_not_duplicate(self, migrated_db):
        auth_service.ensure_seed_account("dup@test.com", "Demo2024!", "Demo", "client")
        auth_service.ensure_seed_account("dup@test.com", "Demo2024!", "Demo", "client")
        matches = [u for u in auth_service.list_users() if u.email == "dup@test.com"]
        assert len(matches) == 1

    def test_never_overwrites_existing_password_or_role(self, migrated_db):
        """
        Point 7 explicite : un compte de demo existant n'est jamais
        ecrase, meme si ensure_seed_account() est rappelee avec des
        parametres differents.
        """
        first = auth_service.ensure_seed_account("stable@test.com", "Demo2024!", "Demo", "client")
        original_hash = first.password_hash

        second = auth_service.ensure_seed_account(
            "stable@test.com", "AutreMotDePasse1", "Autre Nom", "admin"
        )
        assert second.id == first.id
        assert second.password_hash == original_hash  # pas ecrase
        assert second.role == "client"                # pas ecrase (toujours 'client', pas 'admin')
        assert second.username == "Demo"               # pas ecrase

    def test_invalid_email_raises(self, migrated_db):
        with pytest.raises(InvalidEmailFormat):
            auth_service.ensure_seed_account("pasunemail", "Demo2024!", "Demo", "client")

    def test_weak_password_raises(self, migrated_db):
        with pytest.raises(WeakPassword):
            auth_service.ensure_seed_account("weak@test.com", "abc", "Demo", "client")

    def test_role_admin_impossible_via_public_register(self, migrated_db):
        """
        Garde-fou de securite : confirme que la fonction publique register()
        (utilisee par le formulaire d'inscription) ne peut jamais creer un
        admin, contrairement a ensure_seed_account() qui est reservee au
        seeding controle depuis app.py.
        """
        user = auth_service.register("publicsignup@test.com", "Password1", username="Public")
        assert user.role == "client"


# ─────────────────────────────────────────────────────────────
# Seeding des comptes de demonstration — comportement reel de app.py
# ─────────────────────────────────────────────────────────────
class TestDemoAccountSeeding:
    def test_seeding_creates_exactly_two_accounts(self, migrated_db):
        seed_demo_accounts()
        emails = {u.email for u in auth_service.list_users()}
        assert emails == {"admin@fitmind.ai", "client@demo.com"}

    def test_admin_demo_account_has_admin_role(self, migrated_db):
        seed_demo_accounts()
        admin = UserRepository().get_by_email("admin@fitmind.ai")
        assert admin.role == "admin"

    def test_client_demo_account_has_client_role(self, migrated_db):
        seed_demo_accounts()
        client = UserRepository().get_by_email("client@demo.com")
        assert client.role == "client"

    def test_demo_accounts_can_login_with_documented_passwords(self, migrated_db):
        """Les mots de passe affiches sur l'ecran de connexion doivent fonctionner reellement."""
        seed_demo_accounts()
        admin = auth_service.login("admin@fitmind.ai", "Admin2024!")
        assert admin.role == "admin"
        client = auth_service.login("client@demo.com", "Demo2024!")
        assert client.role == "client"

    def test_seeding_is_idempotent_across_multiple_app_restarts(self, migrated_db):
        """Simule 3 demarrages successifs de app.py sur la meme base."""
        seed_demo_accounts()
        seed_demo_accounts()
        seed_demo_accounts()
        assert len(auth_service.list_users()) == 2

    def test_seeding_does_not_affect_manually_registered_users(self, migrated_db):
        auth_service.register("manuel@test.com", "Password1")
        seed_demo_accounts()
        emails = {u.email for u in auth_service.list_users()}
        assert emails == {"admin@fitmind.ai", "client@demo.com", "manuel@test.com"}
