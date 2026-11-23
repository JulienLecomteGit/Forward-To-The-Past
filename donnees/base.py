"""Base SQLite : emplacement du fichier, structure des tables, ouverture des connexions, lectures libres.

Fichier : data/fttp.db, ou l'emplacement donné par la variable d'environnement FTTP_BDD (utilisée par le kit).

Utilise     : config (avatars, chemins)
Utilisé par : app, demo (generation), donnees (carnet, interactions, journal, membres, reglages), etat (actions),
              vues (profil), vues/admin (chargement, onglet_journal, onglet_qualite, simulation)
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from config.avatars import ANCIENS
from config.chemins import BDD_PAR_DEFAUT

CHEMIN_BDD = Path(os.environ.get("FTTP_BDD", BDD_PAR_DEFAUT))


SCHEMA = """
CREATE TABLE IF NOT EXISTS utilisateurs(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE COLLATE NOCASE,
  prenom TEXT NOT NULL,
  nom TEXT NOT NULL DEFAULT '',
  pseudo TEXT NOT NULL,
  mdp_hash TEXT NOT NULL,
  avatar TEXT NOT NULL,
  tranche_age TEXT,
  ville TEXT,
  newsletter INTEGER NOT NULL DEFAULT 0,
  consentement_rgpd TEXT NOT NULL,
  date_inscription TEXT NOT NULL,
  derniere_connexion TEXT,
  est_fictif INTEGER NOT NULL DEFAULT 0,
  est_demo INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS preferences(
  utilisateur_id INTEGER PRIMARY KEY REFERENCES utilisateurs(id) ON DELETE CASCADE,
  genres TEXT NOT NULL,
  decennies TEXT NOT NULL,
  format_duree TEXT NOT NULL DEFAULT 'indifferent',
  origine TEXT NOT NULL DEFAULT 'indifferent',
  style TEXT NOT NULL DEFAULT 'indifferent',
  maj TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS interactions(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs(id) ON DELETE CASCADE,
  tconst TEXT NOT NULL,
  type TEXT NOT NULL CHECK(type IN ('like','dislike','liste','vu','note')),
  valeur REAL,
  source TEXT,
  date TEXT NOT NULL,
  UNIQUE(utilisateur_id, tconst, type)
);
CREATE INDEX IF NOT EXISTS ix_inter_user ON interactions(utilisateur_id);
CREATE INDEX IF NOT EXISTS ix_inter_film ON interactions(tconst, type);
CREATE TABLE IF NOT EXISTS evenements(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  utilisateur_id INTEGER REFERENCES utilisateurs(id) ON DELETE SET NULL,
  type TEXT NOT NULL,
  detail TEXT,
  date TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_evt_date ON evenements(date);
CREATE TABLE IF NOT EXISTS seances(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs(id) ON DELETE CASCADE,
  tconst TEXT NOT NULL,
  date_seance TEXT NOT NULL,
  lieu TEXT NOT NULL DEFAULT 'cinema',
  note INTEGER,
  avis TEXT,
  date TEXT NOT NULL,
  UNIQUE(utilisateur_id, tconst)
);
CREATE TABLE IF NOT EXISTS parametres(
  cle TEXT PRIMARY KEY,
  valeur TEXT NOT NULL,
  maj TEXT NOT NULL
);
"""


def maintenant() -> str:
    """Date et heure actuelles au format de la base (« AAAA-MM-JJ HH:MM:SS »)."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@contextmanager
def connexion():
    """Ouvre la base SQLite le temps d'un bloc `with` : valide si tout va bien, annule sinon."""
    CHEMIN_BDD.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(CHEMIN_BDD, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def initialiser() -> None:
    """Crée les tables si besoin et met à niveau une base d'une version précédente."""
    # migration douce : anciennes clés d'avatars → nouvelles images (correspondances dans config/avatars.py)
    with connexion() as con:
        con.execute("PRAGMA journal_mode = WAL")
        con.executescript(SCHEMA)
        colonnes = {r["name"] for r in con.execute("PRAGMA table_info(utilisateurs)")}
        if "est_demo" not in colonnes:  # base créée par une version précédente
            con.execute("ALTER TABLE utilisateurs ADD COLUMN est_demo INTEGER NOT NULL DEFAULT 0")
        con.executemany("UPDATE utilisateurs SET avatar = ? WHERE avatar = ?", [(n, a) for a, n in ANCIENS.items()])


def nb_membres() -> int:
    """Nombre de comptes enregistrés (réels et fictifs)."""
    with connexion() as con:
        return con.execute("SELECT COUNT(*) FROM utilisateurs").fetchone()[0]


def requete(sql: str, params=()) -> list[dict]:
    """Lecture seule pour les statistiques admin."""
    with connexion() as con:
        return [dict(r) for r in con.execute(sql, params)]
