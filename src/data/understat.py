"""Fonte xG: Understat (via mirror GitHub, vedi sources.py).

Cosa fornisce questo modulo, a livello di SINGOLA PARTITA:

    home_xg,   away_xg     expected goals (xG) delle due squadre;
    home_npxg, away_npxg   xG senza rigori (non-penalty xG);
    home_ppda, away_ppda   PPDA = passaggi concessi all'avversario per azione
                           difensiva nella meta' campo avversaria (piu' BASSO =
                           pressing piu' intenso);
    home_deep, away_deep   "deep completions": passaggi completati entro ~20m
                           dalla porta avversaria (esclusi i cross).

E, come sottoprodotto (usato dal modulo transfermarkt per stimare le rose):

    squadre per stagione dei singoli giocatori (sezione ``players`` del JSON).

Struttura del JSON di lega di Understat (una pagina per stagione):
    dates   una voce per partita: squadre, gol, xG casa/trasferta, datetime;
    teams   per ogni squadra la "history" partita-per-partita con npxG, PPDA
            (dict att/def), deep, ecc.;
    players statistiche stagionali dei giocatori (con team_title).

L'xG a livello partita viene da ``dates``; npxG/PPDA/deep vengono da ``teams``
(history), riallineati alla partita tramite (squadra, datetime).

Cache OFFLINE-FIRST: i JSON grezzi sono salvati in data/raw/ e riscaricati solo
con force=True (coerente con loader.download_season).
"""

from __future__ import annotations

import json
import logging
import urllib.request
from pathlib import Path

import pandas as pd

from . import sources

log = logging.getLogger(__name__)

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

# Colonne aggiunte allo schema interno da questa fonte.
XG_COLUMNS: list[str] = [
    "home_xg", "away_xg",
    "home_npxg", "away_npxg",
    "home_ppda", "away_ppda",
    "home_deep", "away_deep",
]


# --------------------------------------------------------------------------- #
# Download (con cache) e parsing del JSON grezzo
# --------------------------------------------------------------------------- #
def _cache_path(season_code: str, league_key: str) -> Path:
    year = sources.understat_year(season_code)
    return RAW_DIR / f"understat_{league_key}_{year}.json"


def download_season(
    season_code: str, league_key: str = "serie_a", *, force: bool = False
) -> Path:
    """Scarica il JSON Understat di una stagione, con cache su disco."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dest = _cache_path(season_code, league_key)
    if dest.exists() and not force:
        return dest

    url = sources.understat_url(season_code, league_key)
    log.info("Scarico Understat %s -> %s", url, dest)
    with urllib.request.urlopen(url) as resp:
        dest.write_bytes(resp.read())
    return dest


def _load_json(season_code: str, league_key: str, *, force: bool = False) -> dict:
    path = download_season(season_code, league_key, force=force)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _ppda(entry: dict | None) -> float:
    """PPDA da un dict Understat {"att": passaggi, "def": azioni difensive}."""
    if not entry or not entry.get("def"):
        return float("nan")
    return float(entry["att"]) / float(entry["def"])


# --------------------------------------------------------------------------- #
# Normalizzazione nello schema interno
# --------------------------------------------------------------------------- #
def parse_season_xg(data: dict, season_code: str) -> pd.DataFrame:
    """xG a livello partita da un JSON Understat GIA' caricato (dict).

    Separata da ``season_xg`` (che aggiunge il download/cache) cosi' che una fonte
    OFFLINE alternativa -- es. i bundle caricati a mano in files/ (Fase 54) --
    possa riusare esattamente la stessa logica di parsing. Nomi gia' canonici."""
    # 1) npxG / PPDA / deep dalla history per-squadra, indicizzati per
    #    (squadra canonica, datetime) cosi' da riallinearli alla partita.
    history: dict[tuple[str, str], dict] = {}
    for team in data.get("teams", {}).values():
        name = sources.canonical_team(str(team["title"]).strip())
        for h in team.get("history", []):
            history[(name, h["date"])] = h

    rows: list[dict] = []
    for match in data.get("dates", []):
        if not match.get("isResult"):
            continue  # partita non ancora giocata: nessun xG da registrare
        home = sources.canonical_team(str(match["h"]["title"]).strip())
        away = sources.canonical_team(str(match["a"]["title"]).strip())
        when = match["datetime"]

        row = {
            "season": season_code,
            "home_team": home,
            "away_team": away,
            "date": pd.to_datetime(when).normalize(),
            "home_xg": float(match["xG"]["h"]),
            "away_xg": float(match["xG"]["a"]),
        }
        for side, team in (("home", home), ("away", away)):
            h = history.get((team, when))
            row[f"{side}_npxg"] = float(h["npxG"]) if h else float("nan")
            row[f"{side}_ppda"] = _ppda(h.get("ppda")) if h else float("nan")
            row[f"{side}_deep"] = float(h["deep"]) if h else float("nan")
            if h is None:
                log.warning(
                    "Understat %s: history mancante per %s @ %s",
                    season_code, team, when,
                )
        rows.append(row)

    return pd.DataFrame(rows)


def season_xg(
    season_code: str, league_key: str = "serie_a", *, force: bool = False
) -> pd.DataFrame:
    """xG (e metriche collegate) a livello partita per una stagione (con download).

    Ritorna un DataFrame con chiave di join (season, home_team, away_team)
    -- nomi squadra gia' CANONICI -- piu' ``date`` (solo come controllo) e le
    colonne di XG_COLUMNS.
    """
    return parse_season_xg(_load_json(season_code, league_key, force=force),
                           season_code)


def season_players(
    season_code: str, league_key: str = "serie_a", *, force: bool = False
) -> pd.DataFrame:
    """Giocatori della stagione con la/e squadra/e in cui hanno giocato.

    Una riga per (giocatore, squadra): Understat elenca in ``team_title`` piu'
    squadre separate da virgola se il giocatore ha cambiato maglia a gennaio.
    Colonne: season, team (canonico), player_id, player_name, position,
    minutes. Serve al modulo transfermarkt per stimare le rose.
    """
    data = _load_json(season_code, league_key, force=force)
    rows: list[dict] = []
    for p in data.get("players", []):
        for team in str(p.get("team_title", "")).split(","):
            team = sources.canonical_team(team.strip())
            if not team:
                continue
            rows.append({
                "season": season_code,
                "team": team,
                "player_id": str(p["id"]),
                "player_name": str(p["player_name"]).strip(),
                "position": str(p.get("position", "")),
                "minutes": pd.to_numeric(p.get("time"), errors="coerce"),
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Join con lo schema interno (con verifica: NESSUNA partita persa in silenzio)
# --------------------------------------------------------------------------- #
def add_xg(
    matches: pd.DataFrame,
    league_key: str = "serie_a",
    *,
    force: bool = False,
) -> pd.DataFrame:
    """Aggiunge le colonne xG alle partite dello schema interno.

    Join per (season, home_team, away_team) -- la chiave di partita del
    progetto; la data e' usata SOLO come controllo di coerenza. Regole:

      - nessuna riga di ``matches`` viene persa o duplicata (verificato);
      - ogni mancato match viene LOGGATO, sia lato partite (partita senza xG)
        sia lato Understat (riga xG che non trova la partita): un buco puo'
        indicare un alias nome-squadra mancante, non va ignorato;
      - date incoerenti (oltre 1 giorno di scarto) vengono loggate.
    """
    out = matches.copy()
    # Idempotente: se lo snapshot era gia' arricchito, si riparte pulito.
    out = out.drop(columns=[c for c in XG_COLUMNS if c in out.columns])

    frames = [
        season_xg(code, league_key, force=force)
        for code in sorted(out["season"].astype(str).unique())
    ]
    xg = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if xg.empty:
        log.warning("Understat: nessun dato xG disponibile")
        for col in XG_COLUMNS:
            out[col] = float("nan")
        return out

    key = ["season", "home_team", "away_team"]
    dup = xg.duplicated(subset=key)
    if dup.any():
        raise ValueError(
            f"Understat: {dup.sum()} chiavi partita duplicate: "
            f"{xg.loc[dup, key].to_dict('records')[:5]}"
        )

    n_before = len(out)
    merged = out.merge(
        xg.rename(columns={"date": "understat_date"}), on=key,
        how="left", validate="one_to_one",
    )
    assert len(merged) == n_before, "il join xG ha perso/duplicato partite"

    # Controllo di copertura lato partite...
    missing = merged["home_xg"].isna()
    if missing.any():
        for _, r in merged.loc[missing, key + ["date"]].iterrows():
            log.warning(
                "Partita SENZA xG: %s %s-%s (%s) -- alias mancante?",
                r["season"], r["home_team"], r["away_team"], r["date"].date(),
            )
    # ...e lato Understat (righe xG orfane = quasi certamente nomi disallineati).
    orphan = xg.merge(out[key], on=key, how="left", indicator=True)
    orphan = orphan[orphan["_merge"] == "left_only"]
    for _, r in orphan.iterrows():
        log.warning(
            "Riga Understat ORFANA (nessuna partita corrispondente): %s %s-%s",
            r["season"], r["home_team"], r["away_team"],
        )

    # Controllo date (solo diagnostica: la chiave resta season+squadre).
    both = merged["understat_date"].notna() & merged["date"].notna()
    gap = (merged.loc[both, "understat_date"] - merged.loc[both, "date"]).abs()
    bad_dates = int((gap > pd.Timedelta(days=1)).sum())
    if bad_dates:
        log.warning("xG: %d partite con date che differiscono di >1 giorno", bad_dates)

    merged = merged.drop(columns=["understat_date"])
    log.info(
        "xG integrato: %d/%d partite coperte (%d orfane lato Understat)",
        int((~missing).sum()), n_before, len(orphan),
    )
    return merged
