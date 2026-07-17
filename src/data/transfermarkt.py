"""Fonte valori di mercato e infortuni: Transfermarkt (via mirror GitHub).

Cosa fornisce questo modulo allo schema interno:

  Per (squadra, stagione) -- poi propagato a ogni partita:
    home_squad_value, away_squad_value
        valore di mercato TOTALE della rosa a INIZIO stagione (EUR): somma,
        sui giocatori della rosa, dell'ultima valutazione Transfermarkt
        precedente al 1 settembre dell'anno di inizio. Serve come stima di
        forza INDIPENDENTE dai risultati (neopromosse, inizio stagione).

  Per singola partita (SE i dati infortuni lo permettono):
    home_absent_count_est, away_absent_count_est
    home_absent_value_est, away_absent_value_est
        numero e valore di mercato complessivo dei giocatori della rosa
        indisponibili alla data della partita secondo lo storico infortuni.

ATTENZIONE -- QUESTI NUMERI SONO STIME, non letture dirette (per questo le
colonne assenze portano il suffisso ``_est`` e il metodo e' documentato qui):

  1. La composizione della rosa e' STIMATA dai giocatori che risultano avere
     giocato per la squadra in quella stagione su Understat (>=1 minuto).
     Include quindi anche gli arrivi di gennaio (di norma 1-3 per squadra);
     un giocatore trasferito a gennaio conta per entrambe le squadre.
  2. Il collegamento giocatore Understat -> giocatore Transfermarkt avviene
     per NOME normalizzato, con disambiguazione per ruolo/valutazioni e un
     ripiego sul cognome (dettagli in ``map_players``). Il tasso di aggancio
     e' misurato e riportato: se la copertura (pesata sui minuti giocati)
     di una (squadra, stagione) scende sotto ``min_coverage``, il valore
     rosa viene lasciato NaN invece di pubblicare un numero sottostimato.
  3. Nessuna imputazione: i giocatori senza valutazione utilizzabile
     semplicemente non contribuiscono alla somma (e abbassano la copertura).

Cache OFFLINE-FIRST: i CSV grezzi sono salvati in data/raw/ e riscaricati solo
con force=True, come per le altre fonti.
"""

from __future__ import annotations

import html
import logging
import re
import unicodedata
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

from . import sources, understat

log = logging.getLogger(__name__)

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

# Colonne aggiunte allo schema interno da questa fonte.
SQUAD_VALUE_COLUMNS: list[str] = ["home_squad_value", "away_squad_value"]
ABSENCE_COLUMNS: list[str] = [
    "home_absent_count_est", "away_absent_count_est",
    "home_absent_value_est", "away_absent_value_est",
]

# Data di riferimento "inizio stagione": il mercato estivo e' chiuso (o quasi)
# e le valutazioni non incorporano ancora i risultati della stagione.
SEASON_START = "09-01"  # 1 settembre dell'anno di inizio (es. 2017-09-01)

# Una valutazione piu' vecchia di cosi' rispetto alla data richiesta e'
# considerata stantia e NON viene usata (meglio un buco dichiarato che un
# numero fuori epoca).
MAX_VALUE_AGE_DAYS = 550

# Sotto questa copertura (quota dei minuti stagionali della squadra coperta da
# giocatori agganciati e valutati) il valore rosa resta NaN.
MIN_COVERAGE = 0.85

# Compatibilita' ruoli: iniziale del token di ruolo Understat -> main_position
# Transfermarkt. "S" (subentrato) non porta informazione e viene ignorato.
_POSITION_COMPAT = {
    "G": "Goalkeeper",  # Understat usa "GK"
    "D": "Defender",
    "M": "Midfield",
    "F": "Attack",
}


# --------------------------------------------------------------------------- #
# Download (con cache) e caricamento tabelle
# --------------------------------------------------------------------------- #
def download_table(table: str, *, force: bool = False) -> Path:
    """Scarica una tabella del mirror Transfermarkt, con cache su disco."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dest = RAW_DIR / f"transfermarkt_{table}.csv"
    if dest.exists() and not force:
        return dest

    url = sources.transfermarkt_url(table)
    log.info("Scarico Transfermarkt %s -> %s", url, dest)
    with urllib.request.urlopen(url) as resp:
        dest.write_bytes(resp.read())
    return dest


# Lettere che NFKD non decompone in ASCII (andrebbero perse: "Kjær" -> "kjr").
_TRANSLITERATE = str.maketrans({
    "æ": "ae", "Æ": "ae", "ø": "o", "Ø": "o", "ß": "ss",
    "ı": "i", "İ": "i", "ł": "l", "Ł": "l", "đ": "d", "Đ": "d",
    "ð": "d", "Ð": "d", "þ": "th", "Þ": "th",
})


def normalize_name(name: str) -> str:
    """Nome confrontabile tra fonti: senza entita' HTML, suffissi "(N)" di
    Transfermarkt, accenti, punteggiatura e differenze di maiuscole."""
    s = html.unescape(str(name))
    s = re.sub(r"\s*\(\d+\)\s*$", "", s)          # "Danilo (2)" -> "Danilo"
    s = s.translate(_TRANSLITERATE)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _load_name_index(*, force: bool = False) -> tuple[pd.DataFrame, dict[int, str]]:
    """Mappa nome_normalizzato -> id Transfermarkt (da profili + compagni).

    La sola tabella dei profili e' incompleta sui giocatori del passato; le
    coppie "compagni di squadra" (id + nome del compagno) la estendono a
    ~190k voci. Ritorna (DataFrame [tm_id, name_norm], {tm_id: ruolo}).
    """
    prof = pd.read_csv(
        download_table("player_profiles", force=force),
        usecols=["player_id", "player_name", "main_position"], low_memory=False,
    )
    positions = dict(zip(prof["player_id"].astype(int),
                         prof["main_position"].astype(str)))

    mates = pd.read_csv(
        download_table("player_teammates_played_with", force=force),
        usecols=["teammate_player_id", "teammate_player_name"],
    ).rename(columns={"teammate_player_id": "player_id",
                      "teammate_player_name": "player_name"})

    names = pd.concat(
        [prof[["player_id", "player_name"]], mates], ignore_index=True
    ).dropna()
    names["tm_id"] = names["player_id"].astype(int)
    names["name_norm"] = names["player_name"].map(normalize_name)
    names = names.drop_duplicates(["tm_id", "name_norm"])[["tm_id", "name_norm"]]
    return names, positions


def _load_valuations(*, force: bool = False) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """Storico valutazioni: {tm_id: (date crescenti, valori EUR)}."""
    val = pd.read_csv(download_table("player_market_value", force=force))
    val["date"] = pd.to_datetime(val["date_unix"], errors="coerce")
    val = val.dropna(subset=["date", "value"]).sort_values("date")
    out: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for tm_id, grp in val.groupby(val["player_id"].astype(int)):
        out[tm_id] = (grp["date"].to_numpy(), grp["value"].to_numpy(float))
    return out


def _value_asof(
    valuations: dict[int, tuple[np.ndarray, np.ndarray]],
    tm_id: int,
    when: pd.Timestamp,
    max_age_days: int = MAX_VALUE_AGE_DAYS,
) -> float:
    """Ultima valutazione <= ``when`` (NaN se assente o piu' vecchia del cap)."""
    entry = valuations.get(tm_id)
    if entry is None:
        return float("nan")
    dates, values = entry
    i = int(np.searchsorted(dates, np.datetime64(when), side="right")) - 1
    if i < 0:
        return float("nan")
    age = (when - pd.Timestamp(dates[i])).days
    if age > max_age_days:
        return float("nan")
    return float(values[i])


# --------------------------------------------------------------------------- #
# Aggancio giocatori Understat -> Transfermarkt
# --------------------------------------------------------------------------- #
def _position_ok(understat_pos: str, tm_pos: str | None) -> bool:
    """True se il ruolo Transfermarkt e' compatibile con quello Understat
    (o se una delle due informazioni manca)."""
    if not tm_pos or tm_pos == "nan":
        return True
    wanted = {
        _POSITION_COMPAT[tok[0]]
        for tok in str(understat_pos).split()
        if tok and tok[0] in _POSITION_COMPAT
    }
    return not wanted or tm_pos in wanted


def map_players(
    squads: pd.DataFrame, *, force: bool = False
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Aggancia i giocatori (Understat) agli id Transfermarkt.

    Strategia, nell'ordine (deterministica, tutta misurata nel report):
      1. nome completo normalizzato con UN solo candidato -> agganciato;
      2. piu' candidati: si scartano quelli senza valutazioni e con ruolo
         incompatibile; se ne resta uno -> agganciato;
      3. se ne resta piu' d'uno: si sceglie quello con valutazione di picco
         massima (i titolari di Serie A sono in genere i piu' quotati fra
         gli omonimi) -- scelta CONTATA a parte nel report perche' fallibile;
      4. nessun candidato: nome confrontato SENZA spazi (cattura
         "Gian Marco"/"Gianmarco", "N'Koulou"/"Nkoulou");
      4-bis. stessi token in ORDINE diverso (Fase 63: "Djené Dakonam" Understat
         vs "Dakonam Djené" Transfermarkt — l'inversione nome/cognome, comune
         per i giocatori extra-europei), candidato valutato unico;
      5. sottoinsiemi di token per i nomi lunghi ("Pierre Kalulu Kyatengwa"
         -> "Pierre Kalulu"), accettati solo con candidato valutato unico;
      6. cognome + iniziale del nome (o solo cognome per i nomi a token
         unico, es. "Ibanez"), candidato valutato unico;
      7. fuzzy conservativo (similarita' >= 0.90 sul nome senza spazi tra i
         candidati valutati), accettato solo se il migliore e' unico --
         cattura translitterazioni tipo "Malinovskiy"/"Malinovskyi".

    Ritorna (mappa per giocatore con colonna ``tm_id`` NaN se non agganciato
    e ``method`` usato, statistiche di aggancio).
    """
    from difflib import SequenceMatcher

    names, positions = _load_name_index(force=force)
    valuations = _load_valuations(force=force)
    by_name: dict[str, list[int]] = {
        k: g["tm_id"].tolist() for k, g in names.groupby("name_norm")
    }
    by_squashed: dict[str, set[int]] = {}
    for name_norm, ids in by_name.items():
        by_squashed.setdefault(name_norm.replace(" ", ""), set()).update(ids)
    # Indice a token ORDINATI (Fase 63): cattura le inversioni nome/cognome
    # tra le fonti ("djene dakonam" e "dakonam djene" -> "dakonam djene").
    by_tokensort: dict[str, set[int]] = {}
    for name_norm, ids in by_name.items():
        by_tokensort.setdefault(" ".join(sorted(name_norm.split())), set()).update(ids)
    # Indice per cognome (ultimo token del nome normalizzato).
    by_surname: dict[str, list[tuple[str, int]]] = {}
    for name_norm, ids in by_name.items():
        toks = name_norm.split()
        if len(toks) >= 2:
            for tm_id in ids:
                by_surname.setdefault(toks[-1], []).append((name_norm, tm_id))
    valued_squashed = sorted(
        (n, tuple(sorted(ids_v)))
        for n, ids in by_squashed.items()
        if (ids_v := {c for c in ids if c in valuations})
    )

    def _valid(cands, position) -> list[int]:
        return sorted({
            c for c in cands
            if c in valuations and _position_ok(position, positions.get(c))
        })

    stats = {"exact": 0, "filtered": 0, "peak_tiebreak": 0, "squashed": 0,
             "token_sort": 0, "token_subset": 0, "surname": 0, "fuzzy": 0,
             "unmatched": 0}
    rows: list[dict] = []
    players = squads.drop_duplicates("player_id")
    for _, p in players.iterrows():
        norm = normalize_name(p["player_name"])
        toks = norm.split()
        cands = list(by_name.get(norm, []))
        tm_id, method = None, None

        if len(cands) == 1:
            tm_id, method = cands[0], "exact"
        elif len(cands) > 1:
            good = _valid(cands, p["position"])
            if len(good) == 1:
                tm_id, method = good[0], "filtered"
            elif len(good) > 1:
                tm_id = max(good, key=lambda c: valuations[c][1].max())
                method = "peak_tiebreak"

        if tm_id is None and method is None and not cands:
            # 4) confronto senza spazi
            good = _valid(by_squashed.get(norm.replace(" ", ""), []),
                          p["position"])
            if len(good) == 1:
                tm_id, method = good[0], "squashed"
            # 4-bis) stessi token, ordine diverso (inversione nome/cognome)
            if tm_id is None and len(toks) >= 2:
                good = _valid(by_tokensort.get(" ".join(sorted(toks)), []),
                              p["position"])
                if len(good) == 1:
                    tm_id, method = good[0], "token_sort"
            # 5) sottoinsiemi di token (nomi con parti in piu'/in meno)
            if tm_id is None and len(toks) >= 3:
                subsets = [" ".join(toks[:2]), f"{toks[0]} {toks[-1]}",
                           " ".join(toks[1:])]
                found = {c for sub in subsets
                         for c in _valid(by_name.get(sub, []), p["position"])}
                if len(found) == 1:
                    tm_id, method = found.pop(), "token_subset"
            # 6) cognome (+ iniziale del nome se disponibile)
            if tm_id is None:
                surname, initial = toks[-1], toks[0][:1] if len(toks) >= 2 else ""
                same = {
                    c for n, c in by_surname.get(surname, [])
                    if (not initial or n.split()[0][:1] == initial)
                }
                good = _valid(same, p["position"])
                if len(good) == 1:
                    tm_id, method = good[0], "surname"
            # 7) fuzzy conservativo sulle forme senza spazi
            if tm_id is None:
                target = norm.replace(" ", "")
                best: list[tuple[float, tuple[int, ...]]] = []
                for cand_name, ids_v in valued_squashed:
                    if abs(len(cand_name) - len(target)) > 3:
                        continue
                    r = SequenceMatcher(None, target, cand_name).ratio()
                    if r >= 0.90:
                        best.append((r, ids_v))
                if best:
                    best.sort(reverse=True)
                    top = [ids for r, ids in best if r == best[0][0]]
                    good = _valid({c for ids in top for c in ids},
                                  p["position"])
                    if len(good) == 1:
                        tm_id, method = good[0], "fuzzy"

        stats[method if method else "unmatched"] += 1
        rows.append({"player_id": p["player_id"],
                     "player_name": p["player_name"],
                     "tm_id": tm_id, "method": method})

    mapping = players.merge(pd.DataFrame(rows),
                            on=["player_id", "player_name"], how="left")
    log.info("Aggancio giocatori Understat->Transfermarkt: %s", stats)
    return mapping[["player_id", "player_name", "tm_id", "method"]], stats


# --------------------------------------------------------------------------- #
# Valori rosa per (squadra, stagione)
# --------------------------------------------------------------------------- #
def season_start_date(season_code: str) -> pd.Timestamp:
    """Data di riferimento "inizio stagione" (1 settembre dell'anno iniziale)."""
    return pd.Timestamp(f"{sources.understat_year(season_code)}-{SEASON_START}")


def team_season_values(
    season_codes: list[str],
    league_key: str = "serie_a",
    *,
    min_coverage: float = MIN_COVERAGE,
    force: bool = False,
    squads: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Valore rosa a inizio stagione per ogni (season, team).

    Colonne: season, team, squad_value (EUR, NaN se copertura < min_coverage),
    value_coverage (quota dei minuti stagionali coperta da giocatori agganciati
    e valutati), n_players, n_valued.

    ``squads`` (Fase 59): se fornito, salta il download Understat via rete e usa
    QUESTE rose (schema di ``understat.parse_season_players`` -- season, team,
    player_id, player_name, position, minutes). Serve per Premier/Liga, il cui
    mirror Understat per-stagione e' sparito (Fase 14): le rose vengono invece
    dai bundle locali gia' caricati in files/ (stessa fonte dell'xG, Fase 54).
    """
    if squads is None:
        squads = pd.concat(
            [understat.season_players(c, league_key, force=force)
             for c in season_codes],
            ignore_index=True,
        )
    mapping, _ = map_players(squads, force=force)
    valuations = _load_valuations(force=force)
    squads = squads.merge(mapping[["player_id", "tm_id"]],
                          on="player_id", how="left")

    rows: list[dict] = []
    for (season, team), grp in squads.groupby(["season", "team"]):
        asof = season_start_date(str(season))
        values = np.array([
            _value_asof(valuations, int(t), asof) if pd.notna(t) else np.nan
            for t in grp["tm_id"]
        ])
        minutes = grp["minutes"].fillna(0).to_numpy(float)
        covered = np.isfinite(values)
        coverage = (minutes[covered].sum() / minutes.sum()
                    if minutes.sum() > 0 else 0.0)
        total = float(np.nansum(values)) if covered.any() else float("nan")
        if coverage < min_coverage:
            log.warning(
                "Valore rosa NON pubblicato per %s %s: copertura %.0f%% "
                "sotto la soglia del %.0f%%",
                season, team, coverage * 100, min_coverage * 100,
            )
            total = float("nan")
        rows.append({
            "season": str(season), "team": team, "squad_value": total,
            "value_coverage": round(float(coverage), 4),
            "n_players": int(len(grp)), "n_valued": int(covered.sum()),
        })
    return pd.DataFrame(rows)


def add_squad_values(
    matches: pd.DataFrame,
    league_key: str = "serie_a",
    *,
    force: bool = False,
    squads: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Aggiunge home_squad_value / away_squad_value allo schema interno.

    Join per (season, squadra); nessuna riga persa o duplicata (verificato).
    ``squads``: vedi ``team_season_values`` (bypassa il download Understat).
    """
    out = matches.copy()
    out = out.drop(columns=[c for c in SQUAD_VALUE_COLUMNS if c in out.columns])

    seasons = sorted(out["season"].astype(str).unique())
    values = team_season_values(seasons, league_key, force=force, squads=squads)

    n_before = len(out)
    for side in ("home", "away"):
        lookup = values.rename(columns={
            "team": f"{side}_team", "squad_value": f"{side}_squad_value",
        })[["season", f"{side}_team", f"{side}_squad_value"]]
        out = out.merge(lookup, on=["season", f"{side}_team"],
                        how="left", validate="many_to_one")
        missing = out[out[f"{side}_squad_value"].isna()][f"{side}_team"]
        for team in sorted(missing.unique()):
            log.warning("Valore rosa mancante per %s (%s)", team, side)
    assert len(out) == n_before, "il join valori rosa ha perso/duplicato partite"

    covered = out["home_squad_value"].notna() & out["away_squad_value"].notna()
    log.info("Valori rosa integrati: %d/%d partite con entrambi i valori",
             int(covered.sum()), n_before)
    return out


# --------------------------------------------------------------------------- #
# Assenze per infortunio a livello di singola partita (STIMA, suffisso _est)
# --------------------------------------------------------------------------- #
def _load_injuries(*, force: bool = False) -> pd.DataFrame:
    """Storico infortuni: tm_id, from_date, end_date (una riga per infortunio).

    Se ``end_date`` manca ma ``days_missed`` e' noto, la fine e' ricavata da
    inizio + giorni persi; senza nessuna delle due, il record e' scartato
    (meglio perdere un infortunio che inventarne la durata).
    """
    inj = pd.read_csv(
        download_table("player_injuries", force=force),
        usecols=["player_id", "from_date", "end_date", "days_missed"],
    )
    inj["tm_id"] = inj["player_id"].astype(int)
    inj["from_date"] = pd.to_datetime(inj["from_date"], errors="coerce")
    inj["end_date"] = pd.to_datetime(inj["end_date"], errors="coerce")
    derived = inj["from_date"] + pd.to_timedelta(inj["days_missed"], unit="D")
    inj["end_date"] = inj["end_date"].fillna(derived)
    inj = inj.dropna(subset=["from_date", "end_date"])
    return inj[["tm_id", "from_date", "end_date"]]


def add_absences(
    matches: pd.DataFrame,
    league_key: str = "serie_a",
    *,
    force: bool = False,
    squads: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Aggiunge le colonne assenze stimate (suffisso ``_est``) per partita.

    Per ogni partita e per ciascuna squadra: numero e valore di mercato (alla
    data della partita) dei giocatori della rosa stimata che risultano
    infortunati in quella data. L'informazione "chi e' indisponibile" e'
    nota al mercato PRIMA della partita, quindi la feature e' legittima in
    backtest walk-forward (nessun look-ahead sull'esito).

    ``squads``: vedi ``team_season_values`` (bypassa il download Understat).
    """
    out = matches.copy()
    out = out.drop(columns=[c for c in ABSENCE_COLUMNS if c in out.columns])

    seasons = sorted(out["season"].astype(str).unique())
    if squads is None:
        squads = pd.concat(
            [understat.season_players(c, league_key, force=force)
             for c in seasons],
            ignore_index=True,
        )
    mapping, _ = map_players(squads, force=force)
    squads = squads.merge(mapping[["player_id", "tm_id"]],
                          on="player_id", how="left")
    squads = squads.dropna(subset=["tm_id"])
    squads["tm_id"] = squads["tm_id"].astype(int)

    injuries = _load_injuries(force=force)
    valuations = _load_valuations(force=force)
    # Infortuni dei soli giocatori presenti nelle rose stimate.
    injuries = injuries[injuries["tm_id"].isin(set(squads["tm_id"]))]
    by_player: dict[int, list[tuple]] = {
        tm_id: list(zip(grp["from_date"], grp["end_date"]))
        for tm_id, grp in injuries.groupby("tm_id")
    }
    roster: dict[tuple[str, str], list[int]] = {
        (str(season), team): grp["tm_id"].tolist()
        for (season, team), grp in squads.groupby(["season", "team"])
    }

    counts = {"home": [], "away": []}
    values = {"home": [], "away": []}
    for _, m in out.iterrows():
        when = m["date"]
        for side in ("home", "away"):
            ids = roster.get((str(m["season"]), m[f"{side}_team"]), [])
            absent = [
                tm_id for tm_id in ids
                if any(start <= when <= end
                       for start, end in by_player.get(tm_id, []))
            ]
            counts[side].append(float(len(absent)))
            values[side].append(float(np.nansum([
                _value_asof(valuations, tm_id, when) for tm_id in absent
            ])) if absent else 0.0)

    for side in ("home", "away"):
        out[f"{side}_absent_count_est"] = counts[side]
        out[f"{side}_absent_value_est"] = values[side]

    log.info(
        "Assenze stimate integrate: media indisponibili per squadra %.2f",
        float(np.mean(counts["home"] + counts["away"])),
    )
    return out
