"""
auth_token_repository.py — acces aux donnees de la table `auth_tokens`.

Repository Pattern strict : uniquement du CRUD. Ne genere pas les tokens
en clair, ne decide pas des durees d'expiration (ca vit dans
auth/auth_config.py + services/auth_service.py, Etape 3) — recoit un
token_hash et une expires_at deja calcules par l'appelant.

Reference : ARCHITECTURE_AUTH_v1.md §3 et §4.
"""

from datetime import datetime, timezone
from typing import Optional

from database.database import get_connection
from database.models import AuthToken


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_token(row) -> AuthToken:
    return AuthToken(
        id=row["id"],
        user_id=row["user_id"],
        purpose=row["purpose"],
        token_hash=row["token_hash"],
        expires_at=row["expires_at"],
        created_at=row["created_at"],
        used_at=row["used_at"],
    )


class AuthTokenRepository:
    """CRUD pur sur `auth_tokens`. Aucune decision metier (validite, duree)."""

    def create(self, user_id: int, purpose: str, token_hash: str, expires_at: str) -> AuthToken:
        now = _now()
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO auth_tokens (user_id, purpose, token_hash, expires_at, created_at)
                VALUES (?,?,?,?,?)
                """,
                (user_id, purpose, token_hash, expires_at, now),
            )
            new_id = cur.lastrowid
            row = conn.execute(
                "SELECT * FROM auth_tokens WHERE id = ?", (new_id,)
            ).fetchone()
            return _row_to_token(row)

    def get_by_id(self, token_id: int) -> Optional[AuthToken]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM auth_tokens WHERE id = ?", (token_id,)
            ).fetchone()
            return _row_to_token(row) if row else None

    def get_by_hash(self, token_hash: str, purpose: str) -> Optional[AuthToken]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM auth_tokens WHERE token_hash = ? AND purpose = ?",
                (token_hash, purpose),
            ).fetchone()
            return _row_to_token(row) if row else None

    def list_for_user(self, user_id: int, purpose: Optional[str] = None):
        query = "SELECT * FROM auth_tokens WHERE user_id = ?"
        params = [user_id]
        if purpose:
            query += " AND purpose = ?"
            params.append(purpose)
        query += " ORDER BY created_at DESC"
        with get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [_row_to_token(r) for r in rows]

    def mark_used(self, token_id: int) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE auth_tokens SET used_at = ? WHERE id = ?", (_now(), token_id)
            )

    def delete(self, token_id: int) -> None:
        with get_connection() as conn:
            conn.execute("DELETE FROM auth_tokens WHERE id = ?", (token_id,))
