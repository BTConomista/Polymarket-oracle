"""Scaricamento e normalizzazione dei dati partita.

Responsabilita' del modulo:
  1. scaricare i CSV grezzi (con cache locale in data/raw/);
  2. tradurli in uno SCHEMA INTERNO PULITO, indipendente dalle idiosincrasie del
     provider (nomi colonna che cambiano di stagione in stagione, formati data,
     quote presenti o assenti).

Il resto del progetto (modello, valutazione) lavora SOLO su questo schema pulito,
non sui CSV grezzi. Cosi' se un domani cambiamo fonte dati, si riscrive solo
questo file.

Schema interno (un DataFrame pandas con queste colonne):
    date         datetime   data della partita
    season       str        codice stagione (es. "2425")
    league       str        chiave campionato (es. "serie_a")
    home_team    str
    away_team    str
    home_goals   int
    away_goals   int
    result       str        "H" / "D" / "A"
    odds_home    float      quota 1 (migliore disponibile, vedi sotto)  -- puo' essere NaN
    odds_draw    float      quota X
    odds_away    float      quota 2
    odds_over25  float      quota Over 2.5
    odds_under25 float      quota Under 2.5
    odds_home_open    float  quota 1 PRE-chiusura (linea "di apertura", vedi sotto)
    odds_draw_open    float  quota X pre-chiusura
    odds_away_open    float  quota 2 pre-chiusura
    odds_over25_open  float  quota Over 2.5 pre-chiusura
    odds_under25_open float  quota Under 2.5 pre-chiusura

Colonne di ARRICCHIMENTO (vedi understat.py e transfermarkt.py; NaN se la
fonte non copre la partita/squadra):
    home_xg, away_xg           float  expected goals (Understat)
    home_npxg, away_npxg       float  xG senza rigori
    home_ppda, away_ppda       float  passaggi avversari per azione difensiva
    home_deep, away_deep       float  passaggi profondi completati
    home_squad_value, away_squad_value  float  valore rosa a inizio stagione (EUR)
    home_absent_count_est, away_absent_count_est  float  n. assenti STIMATO
    home_absent_value_est, away_absent_value_est  float  valore assenti STIMATO (EUR)

Politica sulle quote: per ogni mercato prendiamo la MIGLIORE fonte disponibile in
ordine di preferenza (quote di CHIUSURA medie -> chiusura Bet365 -> pre-match
medie -> pre-match Bet365). Le quote di chiusura sono lo stimatore di mercato
piu' efficiente; sono pero' assenti nelle stagioni piu' vecchie, dove ripieghiamo
sulle pre-match. Le quote servono in fase di VALUTAZIONE (benchmark di mercato),
non per stimare il modello.

Quote "di apertura" (colonne *_open, Fase 14): le colonne football-data SENZA
suffisso C (AvgH, B365H, ...) sono raccolte GIORNI prima della partita (tipicam.
venerdi' pomeriggio per i turni del weekend): sono la linea PRE-chiusura, il
benchmark "battibile" contro cui misurare il Closing Line Value del modello.
NON e' l'apertura vera del mercato (ora ignota nei dati storici), ma una linea
intermedia onesta e documentata. REGOLA CRITICA (rafforzata dall'audit Fase 15):
le colonne *_open NON ripiegano MAI sulle colonne di chiusura (*C*), e sono
valorizzate SOLO dove la chiusura proviene davvero da una colonna *C* -- se per
una riga la chiusura e' il fallback pre-match, open e close coinciderebbero per
costruzione e il confronto open-vs-close (CLV) confronterebbe il mercato con se'
stesso: in quel caso *_open resta NaN (righe escluse, mai contaminate). Ne
consegue che nelle stagioni senza colonne di chiusura (< 2019-20) le colonne
*_open sono interamente NaN.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import sources
from .sources import League

# Cartella di cache dei CSV grezzi.
RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

# Ordine di preferenza delle colonne per ciascun mercato.
# Il primo nome presente (e valorizzato) nella riga viene usato.
_ODDS_PREFERENCE: dict[str, list[str]] = {
    "odds_home":   ["AvgCH", "B365CH", "AvgH", "BbAvH", "B365H"],
    "odds_draw":   ["AvgCD", "B365CD", "AvgD", "BbAvD", "B365D"],
    "odds_away":   ["AvgCA", "B365CA", "AvgA", "BbAvA", "B365A"],
    "odds_over25": ["AvgC>2.5", "B365C>2.5", "Avg>2.5", "BbAv>2.5", "B365>2.5"],
    "odds_under25": ["AvgC<2.5", "B365C<2.5", "Avg<2.5", "BbAv<2.5", "B365<2.5"],
}

# Quote PRE-chiusura ("apertura", Fase 14): SOLO colonne senza suffisso C.
# Mai ripiegare sulla chiusura: un NaN e' onesto, una chiusura spacciata per
# apertura invaliderebbe il confronto open-vs-close in modo silenzioso.
_ODDS_PREFERENCE_OPEN: dict[str, list[str]] = {
    "odds_home_open":    ["AvgH", "BbAvH", "B365H"],
    "odds_draw_open":    ["AvgD", "BbAvD", "B365D"],
    "odds_away_open":    ["AvgA", "BbAvA", "B365A"],
    "odds_over25_open":  ["Avg>2.5", "BbAv>2.5", "B365>2.5"],
    "odds_under25_open": ["Avg<2.5", "BbAv<2.5", "B365<2.5"],
}


def _cache_path(season_code: str, league: League) -> Path:
    return RAW_DIR / f"{league.key}_{season_code}.csv"


def download_season(
    season_code: str, league: League, *, force: bool = False
) -> Path:
    """Scarica il CSV grezzo di una stagione, con cache su disco.

    Ritorna il percorso del file locale. Se il file esiste gia' e ``force`` e'
    False, non riscarica.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dest = _cache_path(season_code, league)
    if dest.exists() and not force:
        return dest

    url = sources.csv_url(season_code, league)
    # pandas legge direttamente da URL; centralizziamo qui la lettura remota.
    raw = pd.read_csv(url, encoding="latin-1")
    raw.to_csv(dest, index=False)
    return dest


def _parse_dates(raw_dates: pd.Series) -> pd.Series:
    """Interpreta le date football-data (gg/mm/aaaa nelle stagioni recenti,
    gg/mm/aa in quelle vecchie). Proviamo i formati espliciti per evitare
    l'inferenza riga-per-riga (lenta e con warning); ripieghiamo su dateutil
    solo per eventuali residui."""
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        parsed = pd.to_datetime(raw_dates, format=fmt, errors="coerce")
        if parsed.notna().mean() > 0.9:
            return parsed
    return pd.to_datetime(raw_dates, dayfirst=True, errors="coerce")


def _pick_odds(row: pd.Series, candidates: list[str]) -> float:
    """Ritorna la prima quota disponibile e valida tra le colonne candidate."""
    for col in candidates:
        if col in row.index:
            val = row[col]
            if pd.notna(val) and val > 1.0:
                return float(val)
    return float("nan")


# Mercati le cui colonne _ODDS_PREFERENCE(_OPEN) vanno validate INSIEME (Fase 58):
# un book vero non puo' mai avere overround implicito < 1 (arbitraggio garantito).
_ODDS_MARKET_GROUPS: list[list[str]] = [
    ["odds_home", "odds_draw", "odds_away"],
    ["odds_over25", "odds_under25"],
]


def _pick_market_odds(row: pd.Series, targets: list[str],
                       preference: dict[str, list[str]]) -> dict[str, float]:
    """Sceglie le quote di un intero mercato (es. 1X2) per una riga, con un
    controllo di coerenza che la scelta colonna-per-colonna (_pick_odds) non fa.

    Perche' (Fase 58, audit dati): una quota "Avg" e' singolarmente valida
    (>1.0) ma puo' comunque essere inquinata da un bookmaker anomalo incluso
    nella media della fonte (osservato: un "Max" fuori scala di 3-4x rispetto
    a tutti gli altri book dello stesso mercato/riga). Il sintomo e' un
    overround implicito < 1 -- impossibile per un book vero, quindi la fonte
    scelta per quella riga e' inaffidabile. In tal caso si scarta IN BLOCCO
    (mai un solo lato) e si ritenta col livello di preferenza successivo per
    OGNI colonna del mercato; se anche il ripiego resta impossibile, NaN
    dichiarato (mai un numero corretto a mano).
    """
    picks = {t: _pick_odds(row, preference[t]) for t in targets}
    if all(pd.notna(v) for v in picks.values()):
        if sum(1.0 / v for v in picks.values()) < 1.0:
            retry = {t: _pick_odds(row, preference[t][1:]) for t in targets}
            if all(pd.notna(v) for v in retry.values()) and \
                    sum(1.0 / v for v in retry.values()) >= 1.0:
                picks = retry
            else:
                picks = {t: float("nan") for t in targets}
    return picks


def _open_odds_market(raw: pd.DataFrame, targets: list[str]) -> dict[str, pd.Series]:
    """Quote di apertura di un intero mercato, oscurate (NaN) dove la CHIUSURA
    proverrebbe dal fallback pre-match (nessuna colonna *C* valida): li' open e
    close coinciderebbero per costruzione, e ogni confronto open-vs-close (gap,
    CLV) confronterebbe il mercato con se' stesso. Overround impossibile ->
    stesso ripiego in blocco di _pick_market_odds (Fase 58)."""
    picks = raw.apply(
        lambda r: _pick_market_odds(r, targets, _ODDS_PREFERENCE_OPEN), axis=1)
    open_vals = {t: picks.map(lambda d: d[t]) for t in targets}

    # Mascheramento invariato rispetto a prima (per-colonna, non di gruppo): la
    # colonna open di UN esito resta NaN solo se LA SUA chiusura specifica non
    # viene da una colonna *C*, indipendentemente dagli altri esiti dello
    # stesso mercato.
    out = {}
    for t in targets:
        close_only = [c for c in _ODDS_PREFERENCE[t[: -len("_open")]]
                      if c not in _ODDS_PREFERENCE_OPEN[t]]
        close_c = raw.apply(lambda r: _pick_odds(r, close_only), axis=1)
        out[t] = open_vals[t].where(close_c.notna())
    return out


def _normalize(raw: pd.DataFrame, season_code: str, league: League) -> pd.DataFrame:
    """Traduce un CSV grezzo nello schema interno pulito."""
    # Righe valide: devono avere le squadre e i gol finali.
    raw = raw.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"]).copy()

    out = pd.DataFrame()
    out["date"] = _parse_dates(raw["Date"])
    out["season"] = season_code
    out["league"] = league.key
    out["home_team"] = raw["HomeTeam"].astype(str).str.strip().map(sources.canonical_team)
    out["away_team"] = raw["AwayTeam"].astype(str).str.strip().map(sources.canonical_team)
    out["home_goals"] = raw["FTHG"].astype(int)
    out["away_goals"] = raw["FTAG"].astype(int)
    out["result"] = raw["FTR"].astype(str).str.strip()

    # Tiri in porta (HST/AST): segnale meno rumoroso dei gol per stimare la
    # forza delle squadre (vedi models/dixon_coles.py, blend gol/tiri). Puo'
    # mancare in qualche riga/stagione: in quel caso resta NaN.
    out["home_sot"] = pd.to_numeric(raw.get("HST"), errors="coerce")
    out["away_sot"] = pd.to_numeric(raw.get("AST"), errors="coerce")

    for group in _ODDS_MARKET_GROUPS:
        picks = raw.apply(
            lambda r: _pick_market_odds(r, group, _ODDS_PREFERENCE), axis=1)
        for target in group:
            out[target] = picks.map(lambda d: d[target])
    for group in _ODDS_MARKET_GROUPS:
        open_group = [f"{t}_open" for t in group]
        for target, series in _open_odds_market(raw, open_group).items():
            out[target] = series

    out = out.dropna(subset=["date"])
    out = out.sort_values("date").reset_index(drop=True)
    return out


def enrich(matches: pd.DataFrame, *, force_download: bool = False) -> pd.DataFrame:
    """Arricchisce le partite con le colonne da fonti esterne.

    In ordine: xG di Understat (add_xg), valori rosa Transfermarkt
    (add_squad_values) e assenze stimate da infortuni (add_absences).
    E' idempotente: le colonne gia' presenti vengono ricalcolate.
    Le leghe non coperte da Understat vengono restituite invariate.
    """
    leagues = set(matches["league"].unique())
    if not leagues <= set(sources.UNDERSTAT_LEAGUES):
        return matches

    from . import transfermarkt, understat

    matches = understat.add_xg(matches, force=force_download)
    matches = transfermarkt.add_squad_values(matches, force=force_download)
    matches = transfermarkt.add_absences(matches, force=force_download)
    return matches


def add_open_odds(matches: pd.DataFrame, *, force_download: bool = False) -> pd.DataFrame:
    """Aggancia le quote PRE-chiusura (colonne *_open) a uno snapshot esistente.

    Rilegge i CSV grezzi football-data (cache in data/raw/, download solo se
    mancanti o ``force_download``) ed estrae le colonne senza suffisso C
    (_ODDS_PREFERENCE_OPEN), oscurate riga per riga dove la chiusura non
    proviene da una colonna *C* (vedi _open_odds_market). Join per
    (season, home_team, away_team) con nomi canonicalizzati — stessa chiave
    usata per xG/rose (vedi README, Fase 4a).

    Controlli d'integrita' (falliscono rumorosamente, mai in silenzio):
      - i GOL del CSV grezzo devono coincidere con quelli dello snapshot su ogni
        riga agganciata (un join sbagliato o una fonte cambiata li sballerebbe);
      - le righe di snapshot senza aggancio vengono contate e stampate (le
        colonne restano NaN: nessun numero inventato).
    Le colonne esistenti dello snapshot NON vengono toccate.
    """
    league = sources.LEAGUES[matches["league"].iloc[0]]
    out = matches.copy()
    open_cols = list(_ODDS_PREFERENCE_OPEN)

    frames = []
    for code in sorted(out["season"].unique()):
        path = download_season(code, league, force=force_download)
        raw = pd.read_csv(path, encoding="latin-1")
        raw = raw.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"]).copy()
        part = pd.DataFrame({
            "season": code,
            "home_team": raw["HomeTeam"].astype(str).str.strip().map(sources.canonical_team),
            "away_team": raw["AwayTeam"].astype(str).str.strip().map(sources.canonical_team),
            "_raw_hg": raw["FTHG"].astype(int),
            "_raw_ag": raw["FTAG"].astype(int),
        })
        for group in _ODDS_MARKET_GROUPS:
            open_group = [f"{t}_open" for t in group]
            for target, series in _open_odds_market(raw, open_group).items():
                part[target] = series.values
        frames.append(part)
    open_df = pd.concat(frames, ignore_index=True)

    key = ["season", "home_team", "away_team"]
    dup = open_df.duplicated(subset=key)
    if dup.any():
        raise ValueError(f"CSV grezzi: {dup.sum()} chiavi (stagione, casa, ospite) duplicate")

    merged = out.drop(columns=open_cols, errors="ignore").merge(
        open_df, on=key, how="left", validate="one_to_one")

    # Integrita': gol del grezzo == gol dello snapshot su ogni riga agganciata.
    matched = merged["_raw_hg"].notna()
    bad = matched & ((merged["_raw_hg"] != merged["home_goals"])
                     | (merged["_raw_ag"] != merged["away_goals"]))
    if bad.any():
        raise ValueError(
            f"add_open_odds: {bad.sum()} righe con GOL diversi tra CSV grezzo e "
            f"snapshot — join sbagliato o fonte cambiata a monte. Mi fermo.")
    n_miss = int((~matched).sum())
    if n_miss:
        print(f"  [open_odds] {n_miss} partite di snapshot senza aggancio nel "
              f"grezzo (restano NaN)")
    cov = merged.groupby("season")["odds_home_open"].apply(lambda s: s.notna().mean())
    print("  [open_odds] copertura quota apertura 1X2 per stagione:")
    for season, frac in cov.items():
        print(f"    {season}: {frac:6.1%}")

    return merged.drop(columns=["_raw_hg", "_raw_ag"])


def add_rest_days(matches: pd.DataFrame, cap: int = 14) -> pd.DataFrame:
    """Aggiunge home_rest_days / away_rest_days: giorni dall'ultima partita di
    ciascuna squadra (fatica / congestione di calendario).

    Feature derivata, deterministica e INDIPENDENTE dai risultati: cattura la
    stanchezza, che il modello gol/xG non puo' dedurre. Rispetta la cronologia
    (usa solo partite precedenti -> niente look-ahead). Prima partita di una
    squadra nei dati -> NaN (covariata neutra). Cap a ``cap`` giorni: oltre due
    settimane il recupero e' completo, conta solo la congestione.
    """
    df = matches.sort_values("date").reset_index(drop=True)
    last_seen: dict[str, pd.Timestamp] = {}
    home_rest, away_rest = [], []
    for _, r in df.iterrows():
        d = r["date"]
        for team, out in ((r["home_team"], home_rest), (r["away_team"], away_rest)):
            prev = last_seen.get(team)
            out.append(min((d - prev).days, cap) if prev is not None else float("nan"))
        last_seen[r["home_team"]] = d
        last_seen[r["away_team"]] = d
    df["home_rest_days"] = home_rest
    df["away_rest_days"] = away_rest
    return df


def add_form(matches: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """Aggiunge home_form / away_form: punti per partita nelle ultime ``window``
    gare di ciascuna squadra PRIMA di questa (stato di forma recente).

    Feature derivata dai risultati recenti: cattura eventuale momentum che la
    forza pesata nel tempo non vedesse. Rispetta la cronologia (solo partite
    precedenti -> niente look-ahead), scorre tra le stagioni. Squadra con nessuna
    gara precedente -> NaN (covariata neutra). Punti: vittoria 3, pari 1, sconf. 0.
    """
    from collections import deque
    df = matches.sort_values("date").reset_index(drop=True)
    recent: dict[str, deque] = {}
    home_form, away_form = [], []
    for _, r in df.iterrows():
        for team, out in ((r["home_team"], home_form), (r["away_team"], away_form)):
            dq = recent.get(team)
            out.append(sum(dq) / len(dq) if dq else float("nan"))
        # Aggiorna DOPO aver letto (no look-ahead): punti di QUESTA gara.
        hg, ag = r["home_goals"], r["away_goals"]
        hp = 3 if hg > ag else (1 if hg == ag else 0)
        recent.setdefault(r["home_team"], deque(maxlen=window)).append(hp)
        recent.setdefault(r["away_team"], deque(maxlen=window)).append(3 - hp if hp != 1 else 1)
    df["home_form"] = home_form
    df["away_form"] = away_form
    return df


def add_style_luck(matches: pd.DataFrame, window: int = 8) -> pd.DataFrame:
    """Aggiunge feature ROLLING pre-partita mai usate nel modello (Fase 33):
      - home/away_ppda_roll : media PPDA (intensita' di pressing) ultime N gare;
      - home/away_deep_roll : media 'deep completions' (dominio territoriale);
      - home/away_luck      : media (gol - xG) = sovra/sotto-rendimento realizzativo
        ('fortuna sotto porta'), ipotesi di mean-reversion (chi ha segnato sopra
        l'xG regredisce).
    Ognuna usa SOLO le gare precedenti della squadra (qualsiasi campo) -> niente
    look-ahead. Prima gara di una squadra -> NaN (covariata neutra)."""
    from collections import deque
    df = matches.sort_values("date").reset_index(drop=True)
    dq: dict[str, dict[str, deque]] = {}
    cols = {c: [] for c in ("home_ppda_roll", "away_ppda_roll", "home_deep_roll",
                            "away_deep_roll", "home_luck", "away_luck")}

    def _mean(d):
        return float(np.mean(d)) if d else float("nan")

    for _, r in df.iterrows():
        for side in ("home", "away"):
            t = r[f"{side}_team"]
            d = dq.get(t)
            cols[f"{side}_ppda_roll"].append(_mean(d["ppda"]) if d else float("nan"))
            cols[f"{side}_deep_roll"].append(_mean(d["deep"]) if d else float("nan"))
            cols[f"{side}_luck"].append(_mean(d["luck"]) if d else float("nan"))
        for side in ("home", "away"):
            t = r[f"{side}_team"]
            slot = dq.setdefault(t, {"ppda": deque(maxlen=window),
                                     "deep": deque(maxlen=window),
                                     "luck": deque(maxlen=window)})
            if pd.notna(r.get(f"{side}_ppda")):
                slot["ppda"].append(float(r[f"{side}_ppda"]))
            if pd.notna(r.get(f"{side}_deep")):
                slot["deep"].append(float(r[f"{side}_deep"]))
            if pd.notna(r.get(f"{side}_xg")):
                slot["luck"].append(float(r[f"{side}_goals"]) - float(r[f"{side}_xg"]))
    for c, v in cols.items():
        df[c] = v
    return df


def add_stakes(matches: pd.DataFrame, n_teams: int = 20, relegated: int = 3,
               europe_rank: int = 7) -> pd.DataFrame:
    """Aggiunge home_settled / away_settled: 1.0 se la squadra non ha piu' NESSUNA
    corsa aperta (posta in palio 'decisa'), 0.0 se e' ancora in corsa (Fase 31/32).

    'Decisa' = ne' in lotta salvezza, ne' in corsa Europa, ne' in corsa titolo,
    inclusi i due estremi (gia' matematicamente retrocessa o gia' campione).
    Usa la classifica PRIMA della partita (solo gare precedenti della stessa
    stagione -> niente look-ahead). Euristica di raggiungibilita' 3*gare-rimaste.
    """
    total = 2 * (n_teams - 1)
    df = matches.sort_values("date").reset_index(drop=True)
    settled_h = np.full(len(df), 0.0)
    settled_a = np.full(len(df), 0.0)
    for _, sdf in df.groupby("season"):
        pts: dict[str, int] = {}
        played: dict[str, int] = {}
        for _, day in sdf.groupby("date", sort=True):
            board = sorted(pts.values(), reverse=True)

            def line(rk):
                return board[rk] if len(board) > rk else 0
            safe_line = line(n_teams - relegated - 1)   # ultima salva (17a)
            releg_line = line(n_teams - relegated)       # prima retrocessa (18a)
            euro_line = line(europe_rank - 1)            # ~Europa (7a)
            title_line = line(0)
            second_line = line(1)
            for i, m in day.iterrows():
                for who, arr in (("home", settled_h), ("away", settled_a)):
                    t = m[f"{who}_team"]
                    p = pts.get(t, 0)
                    reach = 3 * (total - played.get(t, 0))
                    math_safe = p > releg_line + reach
                    math_releg = p + reach < safe_line
                    releg_open = (not math_safe) and (not math_releg)
                    euro_open = abs(p - euro_line) <= reach
                    is_leader = p >= title_line
                    champion = is_leader and (p - second_line) > reach
                    title_open = (abs(p - title_line) <= reach) and (not champion)
                    arr[i] = 0.0 if (releg_open or euro_open or title_open) else 1.0
            for _, m in day.iterrows():
                h, a, r = m["home_team"], m["away_team"], m["result"]
                pts[h] = pts.get(h, 0) + (3 if r == "H" else 1 if r == "D" else 0)
                pts[a] = pts.get(a, 0) + (3 if r == "A" else 1 if r == "D" else 0)
                played[h] = played.get(h, 0) + 1
                played[a] = played.get(a, 0) + 1
    df["home_settled"] = settled_h
    df["away_settled"] = settled_a
    return df


def load_league(
    league_key: str = "serie_a",
    season_codes: list[str] | None = None,
    *,
    force_download: bool = False,
) -> pd.DataFrame:
    """Carica e normalizza una o piu' stagioni di un campionato.

    Args:
        league_key: chiave in sources.LEAGUES (default "serie_a").
        season_codes: stagioni da caricare (default: tutte in sources.SEASONS).
        force_download: se True riscarica dalle fonti ignorando lo snapshot.

    Comportamento OFFLINE-FIRST: se esiste lo snapshot congelato
    (data/serie_a_matches.csv, versionato in git) lo si usa senza rete, cosi' i
    calcoli sono riproducibili identici da chiunque. Si scarica dalle fonti solo
    con force_download=True o se lo snapshot manca.

    Ritorna un unico DataFrame ordinato per data, nello schema interno.
    """
    league = sources.LEAGUES[league_key]
    seasons = season_codes if season_codes is not None else sources.SEASONS

    # Import locale per evitare qualsiasi ciclo di import.
    from . import database
    # OFFLINE-FIRST per QUALSIASI lega con snapshot congelato (Serie A da sempre;
    # Premier/La Liga da Fase 54, costruiti dai bundle). L'xG e' gia' nello
    # snapshot: le feature derivate (riposo/forma/stakes/luck) si ricalcolano dai
    # dati stessi, senza rete. Le fonti di arricchimento SOLO-Serie-A (valori rosa,
    # congestione da openfootball) non si applicano alle altre leghe.
    snap = database.snapshot_path(league_key)
    if not force_download and snap.exists():
        df = database.read_snapshot(snap)
        # Riposo e forma calcolati su TUTTE le stagioni (per avere le partite
        # precedenti a cavallo tra stagioni), poi si filtra a quelle richieste.
        df = add_rest_days(df)
        df = add_form(df)
        df = add_stakes(df)
        df = add_style_luck(df)
        wanted = {str(s) for s in seasons}
        df = df[df["season"].isin(wanted)]
        return df.sort_values("date").reset_index(drop=True)

    frames: list[pd.DataFrame] = []
    for code in seasons:
        path = download_season(code, league, force=force_download)
        raw = pd.read_csv(path, encoding="latin-1")
        frames.append(_normalize(raw, code, league))

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values("date").reset_index(drop=True)
    combined = enrich(combined, force_download=force_download)
    combined = add_rest_days(combined)
    combined = add_form(combined)
    combined = add_stakes(combined)
    combined = add_style_luck(combined)
    return combined
