"""
migrations.py — creation/mise a jour idempotente du schema SQLite.

Chaque migration est un tuple (version: int, migration). `migration` est
soit une liste de requetes SQL (cas simple), soit une fonction
`callable(conn)` quand une logique Python est necessaire (ex. generation
d'UUID par ligne, reconstruction de table). run_migrations() applique,
dans l'ordre, toutes les versions strictement superieures a la version
courante stockee dans schema_meta, dans une seule transaction (rollback
integral en cas d'erreur — voir database.get_connection()). Reexecuter
run_migrations() sur une base deja a jour ne fait rien (idempotent) et ne
perd aucune donnee.

Pour faire evoluer le schema plus tard, ajouter une nouvelle entree a
MIGRATIONS avec le numero de version suivant — ne jamais modifier une
migration deja publiee.

Nuance transactionnelle (migration v2 uniquement) : la reconstruction de
`users` necessite de fermer puis rouvrir une transaction (voir
_migration_v2), car certains PRAGMA SQLite sont des no-op a l'interieur
d'une transaction deja ouverte. Consequence : sur une base totalement
neuve, si la migration v2 echouait apres ce point, la v1 resterait
appliquee (deja committee) mais schema_meta ne serait pas encore passe a
2 — un nouveau run_migrations() reprendrait alors correctement a partir
de la v1, sans etat incoherent. Les migrations qui restent de simples
listes SQL (comme v1) gardent elles une atomicite complete au sein d'une
seule transaction.
"""

import uuid

from database.database import get_connection

MIGRATIONS_V1 = [
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
]


def _migration_v2(conn):
    """
    Etend `users` (public_id, password_hash, auth_provider, email_verified_at,
    last_login_at, failed_login_attempts, locked_until, deleted_at) et cree
    auth_tokens + auth_logs. Reference : ARCHITECTURE_AUTH_v1.md §4.

    SQLite ne permet pas d'ajouter une contrainte UNIQUE ou CHECK via
    ALTER TABLE ADD COLUMN : la table `users` est donc reconstruite (technique
    standard SQLite — table temporaire, copie, remplacement) plutot que
    modifiee colonne par colonne, pour que CHECK(role IN (...)),
    UNIQUE(public_id) et NOT NULL(password_hash) soient reellement imposes
    par la base, pas seulement par convention applicative.

    Les `id` existants sont preserves a l'identique pendant la reconstruction :
    les cles etrangeres predictions.user_id / goals.user_id / settings.user_id
    restent valides sans aucune modification de ces tables.

    Piege SQLite identifie par les tests (voir tests/test_auth_step2.py) :
    par defaut, `ALTER TABLE users RENAME TO ...` reecrit automatiquement la
    definition FOREIGN KEY de `predictions` pour pointer vers le nouveau nom
    (`users_old_v1`), qui est ensuite supprime — ce qui casse la contrainte.
    `PRAGMA legacy_alter_table = ON` desactive cette reecriture automatique
    pendant la reconstruction ; la FK de `predictions` continue de designer
    `users` (jamais renommee de son point de vue) une fois la migration finie.

    Les lignes deja presentes en v1 recoivent un public_id genere (UUID4) et
    un password_hash vide (sentinelle '' — aucun mot de passe utilisable ne
    peut etre reconstitue en SQL pur) : en pratique, `users` est vide avant
    cette migration dans ce projet (aucun compte reel cree avant la Phase 4),
    ce cas ne concerne que la robustesse generale du script.
    """
    conn.commit()  # ferme la transaction implicite ouverte par l'INSERT de _current_version()
                    # (schema_meta) — indispensable : PRAGMA foreign_keys / legacy_alter_table
                    # sont des no-op s'ils sont executes a l'interieur d'une transaction deja
                    # ouverte, meme dans un autre appel de la meme connexion. Voir
                    # tests/test_auth_step2.py::test_foreign_key_rejects_orphan_prediction,
                    # qui a mis ce piege en evidence.
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("PRAGMA legacy_alter_table = ON")
    try:
        conn.execute("ALTER TABLE users RENAME TO users_old_v1")

        conn.execute("""
            CREATE TABLE users (
                id                     INTEGER PRIMARY KEY AUTOINCREMENT,
                public_id              TEXT UNIQUE NOT NULL,
                username               TEXT,
                email                  TEXT UNIQUE NOT NULL,
                password_hash          TEXT NOT NULL DEFAULT '',
                role                   TEXT NOT NULL DEFAULT 'client'
                                            CHECK(role IN ('client','admin')),
                auth_provider          TEXT NOT NULL DEFAULT 'password',
                email_verified_at      TEXT,
                last_login_at          TEXT,
                failed_login_attempts  INTEGER NOT NULL DEFAULT 0,
                locked_until           TEXT,
                created_at             TEXT NOT NULL,
                updated_at             TEXT NOT NULL,
                deleted_at             TEXT
            )
        """)

        old_rows = conn.execute(
            "SELECT id, username, email, role, created_at, updated_at FROM users_old_v1"
        ).fetchall()
        for row in old_rows:
            conn.execute(
                """INSERT INTO users
                   (id, public_id, username, email, role, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (row["id"], str(uuid.uuid4()), row["username"], row["email"],
                 row["role"], row["created_at"], row["updated_at"]),
            )

        conn.execute("DROP TABLE users_old_v1")
    finally:
        conn.execute("PRAGMA legacy_alter_table = OFF")
        conn.execute("PRAGMA foreign_keys = ON")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS auth_tokens (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            purpose     TEXT NOT NULL CHECK(purpose IN ('password_reset','email_verification')),
            token_hash  TEXT NOT NULL,
            expires_at  TEXT NOT NULL,
            used_at     TEXT,
            created_at  TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_tokens_user_id ON auth_tokens(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_tokens_token_hash ON auth_tokens(token_hash)")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS auth_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER REFERENCES users(id),
            event_type  TEXT NOT NULL,
            detail      TEXT,
            created_at  TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_logs_user_id ON auth_logs(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_logs_created_at ON auth_logs(created_at)")


MIGRATIONS = [
    (1, MIGRATIONS_V1),
    (2, _migration_v2),
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
        for version, migration in MIGRATIONS:
            if version <= current:
                continue
            if callable(migration):
                migration(conn)
            else:
                for stmt in migration:
                    conn.execute(stmt)
            conn.execute("UPDATE schema_meta SET version = ?", (version,))
            current = version


def get_schema_version() -> int:
    """Utilitaire de diagnostic/tests : lit la version de schema actuelle."""
    with get_connection() as conn:
        return _current_version(conn)
