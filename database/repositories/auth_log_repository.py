"""
auth_log_repository.py — acces aux donnees de la table `auth_logs`.

Repository Pattern strict : uniquement du CRUD. Ne decide jamais quel
evenement journaliser ni quand (ca vit dans services/auth_service.py,
Etape 3) — recoit un event_type deja determine par l'appelant. Pas de
CHECK SQL sur event_type par choix d'architecture (voir
ARCHITECTURE_AUTH_v1.md §4) : la validite est garantie cote Python par
auth.enums.AuthEventType chez l'appelant, pas ici.

Reference : ARCHITECTURE_AUTH_v1.md §4.
"""

from datetime import datetime, timezone
from typing import List, Optional

from database.database import get_connection
from database.models import AuthLog


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_log(row) -> AuthLog:
    return AuthLog(
        id=row["id"],
        user_id=row["user_id"],
        event_type=row["event_type"],
        detail=row["detail"],
        created_at=row["created_at"],
    )


class AuthLogRepository:
    """CRUD pur sur `auth_logs`."""

    def create(self, event_type: str, user_id: Optional[int] = None,
               detail: Optional[str] = None) -> AuthLog:
        now = _now()
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO auth_logs (user_id, event_type, detail, created_at)
                VALUES (?,?,?,?)
                """,
                (user_id, event_type, detail, now),
            )
            new_id = cur.lastrowid
            row = conn.execute(
                "SELECT * FROM auth_logs WHERE id = ?", (new_id,)
            ).fetchone()
            return _row_to_log(row)

    def list_for_user(self, user_id: int, limit: int = 100) -> List[AuthLog]:
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM auth_logs WHERE user_id = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (user_id, limit),
            ).fetchall()
            return [_row_to_log(r) for r in rows]

    def list_recent(self, limit: int = 100) -> List[AuthLog]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM auth_logs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [_row_to_log(r) for r in rows]
