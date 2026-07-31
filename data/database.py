"""
database.py — connexion SQLite et gestion des transactions.

Responsabilite unique : ouvrir une connexion vers le fichier .db et
garantir qu'un bloc de travail est soit entierement commit, soit
entierement annule (rollback). Aucune requete SQL propre a une table ne
doit vivre ici — c'est le role de database/repositories/*.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "fitmind.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row      # lignes accessibles comme des dicts (row['calories'])
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_connection():
    """
    Context manager transactionnel.

    - commit automatique si le bloc s'execute sans exception ;
    - rollback automatique si une exception est levee (l'exception est
      re-levee ensuite, elle n'est jamais avalee silencieusement) ;
    - la connexion est toujours fermee en sortie de bloc.

    Usage :
        with get_connection() as conn:
            conn.execute("INSERT INTO predictions (...) VALUES (...)", (...))
    """
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
