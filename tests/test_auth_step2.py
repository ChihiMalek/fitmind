"""
test_auth_step2.py — tests d'integration de l'Etape 2 de la Phase 4.

Portee stricte : database/migrations.py (v2), database/models.py (User
etendu, AuthToken, AuthLog), database/repositories/*. Chaque test tourne
sur une base SQLite isolee (fichier temporaire), jamais sur
data/fitmind.db, pour ne rien laisser trainer et rester rejouable.

Lancement : python3 -m pytest tests/test_auth_step2.py -v
"""

import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import database.database as dbmod
from database.database import get_connection
from database.migrations import MIGRATIONS, get_schema_version, run_migrations
from database.repositories.auth_log_repository import AuthLogRepository
from database.repositories.auth_token_repository import AuthTokenRepository
from database.repositories.user_repository import UserRepository


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


# ─────────────────────────────────────────────────────────────
# Migrations
# ─────────────────────────────────────────────────────────────
class TestMigrations:
    def test_auto_creates_database_file(self, isolated_db):
        assert not isolated_db.exists()
        run_migrations()
        assert isolated_db.exists()

    def test_schema_reaches_version_2(self, migrated_db):
        assert get_schema_version() == 2

    def test_migration_is_idempotent(self, migrated_db):
        run_migrations()
        run_migrations()
        assert get_schema_version() == 2

    def test_all_expected_tables_exist(self, migrated_db):
        with get_connection() as conn:
            tables = {r["name"] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
        for t in ["users", "predictions", "goals", "settings",
                  "auth_tokens", "auth_logs", "schema_meta"]:
            assert t in tables, f"table manquante : {t}"

    def test_users_table_has_v2_columns(self, migrated_db):
        with get_connection() as conn:
            cols = {r["name"] for r in conn.execute("PRAGMA table_info(users)")}
        expected = {"public_id", "password_hash", "auth_provider", "email_verified_at",
                    "last_login_at", "failed_login_attempts", "locked_until", "deleted_at"}
        assert expected <= cols

    def test_v1_data_survives_migration_to_v2(self, isolated_db):
        """
        Simule une base deja en v1 (Phase 3) avant l'arrivee de la Phase 4 :
        applique uniquement v1, insere un utilisateur + une prediction liee,
        puis applique v2 et verifie que rien n'a ete perdu et que la FK
        predictions.user_id reste valide.
        """
        with get_connection() as conn:
            for stmt in MIGRATIONS[0][1]:
                conn.execute(stmt)
            conn.execute("CREATE TABLE IF NOT EXISTS schema_meta (version INTEGER NOT NULL)")
            conn.execute("INSERT INTO schema_meta (version) VALUES (1)")
            conn.execute(
                "INSERT INTO users (username, email, role, created_at, updated_at) "
                "VALUES (?,?,?,?,?)",
                ("Ancien", "ancien@test.com", "client", "2026-01-01T00:00:00", "2026-01-01T00:00:00"),
            )
            user_id = conn.execute(
                "SELECT id FROM users WHERE email=?", ("ancien@test.com",)
            ).fetchone()["id"]
            conn.execute(
                "INSERT INTO predictions (user_id, created_at, calories) VALUES (?,?,?)",
                (user_id, "2026-01-01T00:00:00", 450.0),
            )

        run_migrations()
        assert get_schema_version() == 2

        with get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE email=?", ("ancien@test.com",)).fetchone()
            assert row is not None
            assert row["id"] == user_id, "l'id existant doit etre preserve pour ne pas casser les FK"
            assert row["public_id"], "un public_id doit avoir ete genere pour la ligne v1"

            pred = conn.execute("SELECT * FROM predictions WHERE user_id=?", (user_id,)).fetchone()
            assert pred is not None
            assert pred["calories"] == 450.0


# ─────────────────────────────────────────────────────────────
# UserRepository
# ─────────────────────────────────────────────────────────────
class TestUserRepository:
    def test_create_user(self, migrated_db):
        user = UserRepository().create(email="alice@test.com", password_hash="hash123", username="Alice")
        assert user.id is not None
        assert user.email == "alice@test.com"
        assert user.public_id
        assert user.role == "client"
        assert user.deleted_at is None

    def test_get_by_email(self, migrated_db):
        repo = UserRepository()
        created = repo.create(email="bob@test.com", password_hash="h")
        fetched = repo.get_by_email("bob@test.com")
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.public_id == created.public_id

    def test_get_by_email_not_found_returns_none(self, migrated_db):
        assert UserRepository().get_by_email("inconnu@test.com") is None

    def test_get_by_public_id(self, migrated_db):
        repo = UserRepository()
        created = repo.create(email="carla@test.com", password_hash="h")
        fetched = repo.get_by_public_id(created.public_id)
        assert fetched is not None
        assert fetched.email == "carla@test.com"

    def test_get_by_id(self, migrated_db):
        repo = UserRepository()
        created = repo.create(email="dan@test.com", password_hash="h")
        assert repo.get_by_id(created.id).email == "dan@test.com"

    def test_unique_email_constraint(self, migrated_db):
        repo = UserRepository()
        repo.create(email="dup@test.com", password_hash="h1")
        with pytest.raises(sqlite3.IntegrityError):
            repo.create(email="dup@test.com", password_hash="h2")

    def test_public_id_is_unique_across_users(self, migrated_db):
        repo = UserRepository()
        u1 = repo.create(email="u1@test.com", password_hash="h")
        u2 = repo.create(email="u2@test.com", password_hash="h")
        assert u1.public_id != u2.public_id

    def test_soft_delete_does_not_remove_row(self, migrated_db):
        repo = UserRepository()
        user = repo.create(email="del@test.com", password_hash="h")
        repo.soft_delete(user.id)
        still_there = repo.get_by_id(user.id)
        assert still_there is not None
        assert still_there.deleted_at is not None

    def test_list_users_excludes_deleted_by_default(self, migrated_db):
        repo = UserRepository()
        repo.create(email="a@test.com", password_hash="h")
        b = repo.create(email="b@test.com", password_hash="h")
        repo.soft_delete(b.id)
        emails = {u.email for u in repo.list_users()}
        assert "a@test.com" in emails
        assert "b@test.com" not in emails

    def test_list_users_include_deleted(self, migrated_db):
        repo = UserRepository()
        a = repo.create(email="c@test.com", password_hash="h")
        repo.soft_delete(a.id)
        all_users = repo.list_users(include_deleted=True)
        assert any(u.email == "c@test.com" for u in all_users)

    def test_update_last_login(self, migrated_db):
        repo = UserRepository()
        user = repo.create(email="login@test.com", password_hash="h")
        assert user.last_login_at is None
        repo.update_last_login(user.id)
        assert repo.get_by_id(user.id).last_login_at is not None

    def test_increment_and_reset_failed_attempts(self, migrated_db):
        repo = UserRepository()
        user = repo.create(email="fail@test.com", password_hash="h")
        repo.increment_failed_attempts(user.id)
        repo.increment_failed_attempts(user.id)
        assert repo.get_by_id(user.id).failed_login_attempts == 2
        repo.reset_failed_attempts(user.id)
        after_reset = repo.get_by_id(user.id)
        assert after_reset.failed_login_attempts == 0
        assert after_reset.locked_until is None

    def test_role_check_constraint_rejects_invalid_role(self, migrated_db):
        with get_connection() as conn:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO users (public_id, email, password_hash, role, created_at, updated_at) "
                    "VALUES (?,?,?,?,?,?)",
                    ("x", "invalidrole@test.com", "h", "superadmin", "now", "now"),
                )

    def test_foreign_key_rejects_orphan_prediction(self, migrated_db):
        with get_connection() as conn:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO predictions (user_id, created_at) VALUES (?,?)",
                    (999999, "now"),
                )

    def test_rollback_on_error_leaves_no_partial_row(self, migrated_db):
        UserRepository().create(email="rollback@test.com", password_hash="h1")
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO users (public_id, email, password_hash, role, created_at, updated_at) "
                    "VALUES (?,?,?,?,?,?)",
                    ("y", "rollback@test.com", "h2", "client", "now", "now"),
                )  # doublon email -> IntegrityError, la transaction entiere doit etre annulee
                conn.execute(
                    "INSERT INTO users (public_id, email, password_hash, role, created_at, updated_at) "
                    "VALUES (?,?,?,?,?,?)",
                    ("z", "jamais-insere@test.com", "h3", "client", "now", "now"),
                )
        except sqlite3.IntegrityError:
            pass
        with get_connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) c FROM users WHERE email = ?", ("jamais-insere@test.com",)
            ).fetchone()["c"]
        assert count == 0, "rollback rate : une ligne a fuite malgre l'erreur"


# ─────────────────────────────────────────────────────────────
# AuthTokenRepository
# ─────────────────────────────────────────────────────────────
class TestAuthTokenRepository:
    def test_create_and_get_by_hash(self, migrated_db):
        user = UserRepository().create(email="tok@test.com", password_hash="h")
        repo = AuthTokenRepository()
        repo.create(user.id, purpose="password_reset", token_hash="abc123",
                    expires_at="2099-01-01T00:00:00")
        fetched = repo.get_by_hash("abc123", "password_reset")
        assert fetched is not None
        assert fetched.user_id == user.id
        assert fetched.used_at is None

    def test_mark_used(self, migrated_db):
        user = UserRepository().create(email="tok2@test.com", password_hash="h")
        repo = AuthTokenRepository()
        token = repo.create(user.id, "email_verification", "hash2", "2099-01-01T00:00:00")
        repo.mark_used(token.id)
        assert repo.get_by_id(token.id).used_at is not None

    def test_list_for_user_filtered_by_purpose(self, migrated_db):
        user = UserRepository().create(email="tok3@test.com", password_hash="h")
        repo = AuthTokenRepository()
        repo.create(user.id, "password_reset", "h1", "2099-01-01T00:00:00")
        repo.create(user.id, "email_verification", "h2", "2099-01-01T00:00:00")
        resets = repo.list_for_user(user.id, purpose="password_reset")
        assert len(resets) == 1
        assert resets[0].purpose == "password_reset"

    def test_purpose_check_constraint(self, migrated_db):
        user = UserRepository().create(email="tok4@test.com", password_hash="h")
        with get_connection() as conn:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO auth_tokens (user_id, purpose, token_hash, expires_at, created_at) "
                    "VALUES (?,?,?,?,?)",
                    (user.id, "not_a_valid_purpose", "h", "2099-01-01", "now"),
                )

    def test_delete(self, migrated_db):
        user = UserRepository().create(email="tok5@test.com", password_hash="h")
        repo = AuthTokenRepository()
        token = repo.create(user.id, "password_reset", "hdel", "2099-01-01T00:00:00")
        repo.delete(token.id)
        assert repo.get_by_id(token.id) is None


# ─────────────────────────────────────────────────────────────
# AuthLogRepository
# ─────────────────────────────────────────────────────────────
class TestAuthLogRepository:
    def test_create_and_list_for_user(self, migrated_db):
        user = UserRepository().create(email="log@test.com", password_hash="h")
        repo = AuthLogRepository()
        repo.create(event_type="login_success", user_id=user.id, detail="ok")
        logs = repo.list_for_user(user.id)
        assert len(logs) == 1
        assert logs[0].event_type == "login_success"

    def test_create_without_user_id(self, migrated_db):
        """Un login echoue sur un email inexistant ne doit pas exiger de user_id."""
        log = AuthLogRepository().create(event_type="login_failed", user_id=None, detail="email inconnu")
        assert log.id is not None
        assert log.user_id is None

    def test_list_recent_orders_by_most_recent_first(self, migrated_db):
        user = UserRepository().create(email="log2@test.com", password_hash="h")
        repo = AuthLogRepository()
        repo.create("register", user_id=user.id)
        repo.create("login_success", user_id=user.id)
        recent = repo.list_recent(limit=10)
        assert recent[0].event_type == "login_success"


# ─────────────────────────────────────────────────────────────
# Persistance reelle entre deux processus (simulation de redemarrage)
# ─────────────────────────────────────────────────────────────
class TestPersistenceAcrossProcesses:
    def test_data_survives_a_full_process_restart(self, tmp_path):
        db_file = tmp_path / "persist_test.db"

        script_a = f"""
import sys
sys.path.insert(0, {str(PROJECT_ROOT)!r})
import database.database as dbmod
from pathlib import Path
dbmod.DB_PATH = Path({str(db_file)!r})
from database.migrations import run_migrations
from database.repositories.user_repository import UserRepository
run_migrations()
user = UserRepository().create(email="persist@test.com", password_hash="hash-persist", username="Persist")
print(user.id)
"""
        result_a = subprocess.run([sys.executable, "-c", script_a], capture_output=True, text=True)
        assert result_a.returncode == 0, result_a.stderr
        assert result_a.stdout.strip().isdigit()

        script_b = f"""
import sys
sys.path.insert(0, {str(PROJECT_ROOT)!r})
import database.database as dbmod
from pathlib import Path
dbmod.DB_PATH = Path({str(db_file)!r})
from database.repositories.user_repository import UserRepository
user = UserRepository().get_by_email("persist@test.com")
assert user is not None, "utilisateur perdu apres redemarrage"
assert user.username == "Persist"
print("OK")
"""
        result_b = subprocess.run([sys.executable, "-c", script_b], capture_output=True, text=True)
        assert result_b.returncode == 0, result_b.stderr
        assert "OK" in result_b.stdout
