"""
user_repository.py — acces aux donnees de la table `users`.

Repository Pattern strict : uniquement du CRUD, aucune regle metier (pas
de hachage de mot de passe, pas de decision de verrouillage, pas de
validation). Chaque methode ouvre sa propre connexion via
database.database.get_connection() et retourne des instances de
database.models.User — jamais un dict ou un sqlite3.Row brut.

Reference : ARCHITECTURE_AUTH_v1.md §2 et §4.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from database.database import get_connection
from database.models import User


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_user(row) -> User:
    return User(
        id=row["id"],
        public_id=row["public_id"],
        email=row["email"],
        password_hash=row["password_hash"],
        username=row["username"] or "",
        role=row["role"],
        auth_provider=row["auth_provider"],
        email_verified_at=row["email_verified_at"],
        last_login_at=row["last_login_at"],
        failed_login_attempts=row["failed_login_attempts"],
        locked_until=row["locked_until"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        deleted_at=row["deleted_at"],
    )


class UserRepository:
    """CRUD pur sur `users`. Aucune methode ne prend de decision metier."""

    def create(
        self,
        email: str,
        password_hash: str,
        username: str = "",
        role: str = "client",
        auth_provider: str = "password",
    ) -> User:
        now = _now()
        public_id = str(uuid.uuid4())
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO users
                    (public_id, username, email, password_hash, role,
                     auth_provider, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (public_id, username, email, password_hash, role,
                 auth_provider, now, now),
            )
            new_id = cur.lastrowid
            row = conn.execute("SELECT * FROM users WHERE id = ?", (new_id,)).fetchone()
            return _row_to_user(row)

    def get_by_id(self, user_id: int) -> Optional[User]:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return _row_to_user(row) if row else None

    def get_by_email(self, email: str) -> Optional[User]:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            return _row_to_user(row) if row else None

    def get_by_public_id(self, public_id: str) -> Optional[User]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE public_id = ?", (public_id,)
            ).fetchone()
            return _row_to_user(row) if row else None

    def list_users(self, include_deleted: bool = False) -> List[User]:
        query = "SELECT * FROM users"
        if not include_deleted:
            query += " WHERE deleted_at IS NULL"
        query += " ORDER BY created_at ASC"
        with get_connection() as conn:
            rows = conn.execute(query).fetchall()
            return [_row_to_user(r) for r in rows]

    def update_last_login(self, user_id: int) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET last_login_at = ?, updated_at = ? WHERE id = ?",
                (_now(), _now(), user_id),
            )

    def increment_failed_attempts(self, user_id: int) -> None:
        with get_connection() as conn:
            conn.execute(
                """UPDATE users
                   SET failed_login_attempts = failed_login_attempts + 1,
                       updated_at = ?
                   WHERE id = ?""",
                (_now(), user_id),
            )

    def reset_failed_attempts(self, user_id: int) -> None:
        with get_connection() as conn:
            conn.execute(
                """UPDATE users
                   SET failed_login_attempts = 0, locked_until = NULL, updated_at = ?
                   WHERE id = ?""",
                (_now(), user_id),
            )

    def set_locked_until(self, user_id: int, locked_until: str) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET locked_until = ?, updated_at = ? WHERE id = ?",
                (locked_until, _now(), user_id),
            )

    def set_email_verified(self, user_id: int, verified_at: Optional[str] = None) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET email_verified_at = ?, updated_at = ? WHERE id = ?",
                (verified_at or _now(), _now(), user_id),
            )

    def update_password_hash(self, user_id: int, password_hash: str) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
                (password_hash, _now(), user_id),
            )

    def soft_delete(self, user_id: int) -> None:
        """Positionne deleted_at — ne supprime jamais physiquement la ligne."""
        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET deleted_at = ?, updated_at = ? WHERE id = ?",
                (_now(), _now(), user_id),
            )
