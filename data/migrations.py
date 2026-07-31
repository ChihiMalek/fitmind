"""
migrations.py — creation/mise a jour idempotente du schema SQLite.

Chaque migration est un tuple (version: int, statements: list[str]).
run_migrations() applique, dans l'ordre, toutes les versions strictement
superieures a la version courante stockee dans la table schema_meta, puis
met a jour cette version. Reexecuter run_migrations() sur une base deja a
jour ne fait rien (idempotent) et ne perd aucune donnee.

Pour faire evoluer le schema plus tard (nouvelle colonne, nouvelle table),
ajouter une nouvelle entree a MIGRATIONS avec le numero de version suivant
— ne jamais modifier une migration deja publiee.
"""

from database.database import get_connection

MIGRATIONS = [
    (1, [
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT,
            email      TEXT UNIQUE NOT NULL,
            role       TEXT NOT NULL DEFAULT 'client',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id             INTEGER NOT NULL REFERENCES users(id),
            created_at          TEXT NOT NULL,
            age                 REAL,
            gender              REAL,
            height              REAL,
            weight              REAL,
            duration            REAL,
            avg_bpm             REAL,
            resting_bpm         REAL,
            max_bpm             REAL,
            hydration           REAL,
            bmi                 REAL,
            calories            REAL,
            level               TEXT,
            confidence_score    REAL,
            confidence_level    TEXT,
            workout_prediction  TEXT,
            features_json       TEXT,
            model_version       TEXT,
            app_version         TEXT,
            prediction_time_ms  REAL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON predictions(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at)",
        """
        CREATE TABLE IF NOT EXISTS goals (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER NOT NULL REFERENCES users(id),
            weekly_goal    REAL,
            calories_goal  REAL,
            sessions_goal  INTEGER,
            created_at     TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS settings (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER NOT NULL UNIQUE REFERENCES users(id),
            theme          TEXT DEFAULT 'dark',
            language       TEXT DEFAULT 'fr',
            notifications  INTEGER DEFAULT 1
        )
        """,
    ]),
]


def _current_version(conn) -> int:
    conn.execute("CREATE TABLE IF NOT EXISTS schema_meta (version INTEGER NOT NULL)")
    row = conn.execute("SELECT version FROM schema_meta").fetchone()
    if row is None:
        conn.execute("INSERT INTO schema_meta (version) VALUES (0)")
        return 0
    return row["version"]


def run_migrations():
    """Cree la base si besoin et applique toutes les migrations manquantes."""
    with get_connection() as conn:
        current = _current_version(conn)
        for version, statements in MIGRATIONS:
            if version <= current:
                continue
            for stmt in statements:
                conn.execute(stmt)
            conn.execute("UPDATE schema_meta SET version = ?", (version,))
            current = version


def get_schema_version() -> int:
    """Utilitaire de diagnostic/tests : lit la version de schema actuelle."""
    with get_connection() as conn:
        return _current_version(conn)
