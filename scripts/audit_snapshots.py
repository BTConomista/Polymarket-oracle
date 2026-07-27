"""AUDIT dei dati: gli snapshot congelati sono giusti? (verifica, non fiducia)

Tre livelli di controllo, dal piu' debole al piu' forte:

  A. INTERNO      — struttura, coerenza, range, copertura, duplicati. Non serve
                    rete: dice se il file e' internamente sensato.
  B. ESTERNO      — confronto RIGA PER RIGA con le fonti ORIGINALI ri-scaricate
                    oggi (football-data.co.uk + Understat). E' il controllo che
                    conta: dice se il file corrisponde alla realta' a monte.
                    Le 10 colonne quota vengono RI-DERIVATE con lo stesso codice
                    di produzione (loader._odds_from_raw) e confrontate.
  C. INDIPENDENTE — i GOL secondo Understat (fonte terza, non football-data)
                    confrontati con quelli dello snapshot: un errore di
                    risultato che sopravvive a due fonti indipendenti e' molto
                    improbabile.

Ogni controllo produce PASS / WARN / FAIL con i numeri. L'esito completo va in
docs/audit_5_leghe/numeri/audit_<lega>.json e il riassunto a schermo.

Uso:  python scripts/audit_snapshots.py [serie_a premier_league la_liga]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import loader, sources, understat  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
import nuove_leghe  # noqa: E402

nuove_leghe.registra()

FONTI = ROOT / "data" / "fonti"
OUT = ROOT / "docs" / "audit_5_leghe" / "numeri"

SEASONS = sources.SEASONS

# Dove vive lo snapshot di ogni lega (dall'integrazione: tutte in `data/`).
SNAP_DIR = {
    "serie_a": ROOT / "data", "premier_league": ROOT / "data",
    "la_liga": ROOT / "data",
    "bundesliga": ROOT / "data",
    "ligue_1": ROOT / "data",
}

# ECCEZIONI REALI, verificate una per una: non sono errori di dato, sono fatti
# accaduti. Elencarle qui (invece di allargare le soglie) tiene il controllo
# severo per tutto il resto.
ECCEZIONI = {
    # La Ligue 1 2019-20 fu CANCELLATA per COVID il 30/04/2020 (unico grande
    # campionato a non riprendere): 279 gare giocate su 380, ultima l'8/3/2020;
    # PSG e Strasburgo ne giocarono 27 invece di 28 (recupero mai disputato).
    ("ligue_1", "A3.round_robin"): "Ligue 1 2019-20 cancellata per COVID (279/380 gare)",
}
SNAP_COLUMNS = [
    "date", "season", "league", "home_team", "away_team", "home_goals",
    "away_goals", "result", "home_sot", "away_sot", "odds_home", "odds_draw",
    "odds_away", "odds_over25", "odds_under25", "home_xg", "away_xg",
    "home_npxg", "home_ppda", "home_deep", "away_npxg", "away_ppda",
    "away_deep", "home_squad_value", "away_squad_value",
    "home_absent_count_est", "home_absent_value_est", "away_absent_count_est",
    "away_absent_value_est", "odds_home_open", "odds_draw_open",
    "odds_away_open", "odds_over25_open", "odds_under25_open",
    "home_rest_days_full", "away_rest_days_full", "home_midweek_europe",
    "away_midweek_europe",
]
KEY = ["season", "home_team", "away_team"]

# Correzioni DICHIARATE (regole R1/R3 di docs/audit_5_leghe/REGOLE.md): righe in cui lo
# snapshot si discosta VOLUTAMENTE dalla fonte. L'audit non deve segnalarle come
# errori — ma deve continuare a segnalare tutto il resto.
_CORR_PATH = ROOT / "data" / "correzioni_dichiarate.csv"


def _righe_corrette(league: str) -> set[tuple]:
    """{(stagione, casa, ospite)} con almeno una correzione applicata."""
    if not _CORR_PATH.exists():
        raise SystemExit(
            f"registro delle correzioni non trovato: {_CORR_PATH}. "
            "Senza registro il controllo B2 segnalerebbe le correzioni volute "
            "come differenze dalla fonte (regola R3): mi fermo.")
    c = pd.read_csv(_CORR_PATH, dtype={"season": str})
    c = c[(c.league == league) & (c.stato == "applicata")]
    return set(zip(c.season, c.home_team, c.away_team))


class Report:
    """Raccoglitore di esiti: ogni controllo e' (id, livello, messaggio, dati)."""

    def __init__(self, league: str) -> None:
        self.league = league
        self.checks: list[dict] = []

    def add(self, cid: str, ok: bool | str, msg: str, **data) -> None:
        level = ok if isinstance(ok, str) else ("PASS" if ok else "FAIL")
        if level == "FAIL" and (self.league, cid) in ECCEZIONI:
            level = "INFO"
            msg = f"{msg}  [ECCEZIONE NOTA: {ECCEZIONI[(self.league, cid)]}]"
        self.checks.append({"id": cid, "level": level, "msg": msg, "data": data})
        icon = {"PASS": "OK  ", "WARN": "WARN", "FAIL": "FAIL", "INFO": "info"}[level]
        print(f"  [{icon}] {cid}: {msg}")

    @property
    def failed(self) -> list[dict]:
        return [c for c in self.checks if c["level"] == "FAIL"]

    @property
    def warned(self) -> list[dict]:
        return [c for c in self.checks if c["level"] == "WARN"]


# --------------------------------------------------------------------------- #
# A. Controlli INTERNI
# --------------------------------------------------------------------------- #
def audit_internal(df: pd.DataFrame, league: str, rep: Report) -> None:
    # A1 — schema esatto (nomi e ordine)
    rep.add("A1.schema", list(df.columns) == SNAP_COLUMNS,
            f"{len(df.columns)} colonne, ordine {'atteso' if list(df.columns) == SNAP_COLUMNS else 'DIVERSO'}",
            extra=[c for c in df.columns if c not in SNAP_COLUMNS],
            missing=[c for c in SNAP_COLUMNS if c not in df.columns])

    # A2 — una riga per (stagione, casa, ospite)
    dup = df.duplicated(subset=KEY)
    rep.add("A2.chiave_unica", not dup.any(),
            f"{int(dup.sum())} chiavi (stagione,casa,ospite) duplicate",
            examples=df.loc[dup, KEY].head(5).to_dict("records"))

    # A3 — girone all'italiana completo: N squadre, 2(N-1) gare a testa
    problems = []
    for season, sdf in df.groupby("season"):
        teams = set(sdf.home_team) | set(sdf.away_team)
        n = len(teams)
        expected = n * (n - 1)
        counts = pd.concat([sdf.home_team, sdf.away_team]).value_counts()
        bad_counts = counts[counts != 2 * (n - 1)]
        # ogni coppia ordinata (A in casa con B) esattamente una volta
        pair_dup = sdf.duplicated(subset=["home_team", "away_team"]).sum()
        # ogni coppia non ordinata esattamente due volte (andata+ritorno)
        unordered = sdf.apply(
            lambda r: tuple(sorted([r.home_team, r.away_team])), axis=1)
        bad_pairs = (unordered.value_counts() != 2).sum()
        if len(sdf) != expected or len(bad_counts) or pair_dup or bad_pairs:
            problems.append({
                "season": season, "n_teams": n, "n_matches": len(sdf),
                "expected": expected, "teams_wrong_count": bad_counts.to_dict(),
                "pair_dup": int(pair_dup), "unordered_pairs_not_2": int(bad_pairs),
            })
    rep.add("A3.round_robin", not problems,
            f"{len(problems)} stagioni con calendario incompleto/anomalo",
            problems=problems)

    # A4 — gol e risultato coerenti
    exp_result = np.where(df.home_goals > df.away_goals, "H",
                          np.where(df.home_goals == df.away_goals, "D", "A"))
    bad = df.result.values != exp_result
    neg = (df.home_goals < 0) | (df.away_goals < 0)
    huge = (df.home_goals > 12) | (df.away_goals > 12)
    rep.add("A4.result_vs_gol", not bad.any() and not neg.any(),
            f"{int(bad.sum())} risultati incoerenti coi gol, {int(neg.sum())} gol negativi, "
            f"{int(huge.sum())} gol >12 (da ispezionare a mano)",
            examples=df.loc[bad, KEY + ["home_goals", "away_goals", "result"]]
                       .head(5).to_dict("records"),
            big=df.loc[huge, KEY + ["home_goals", "away_goals"]].to_dict("records"))

    # A5 — date: dentro la finestra plausibile della stagione, nessun NaT
    bad_dates = []
    for season, sdf in df.groupby("season"):
        y0 = 2000 + int(season[:2])
        lo, hi = pd.Timestamp(f"{y0}-07-01"), pd.Timestamp(f"{y0 + 1}-08-31")
        out_of_range = sdf[(sdf.date < lo) | (sdf.date > hi)]
        if len(out_of_range):
            bad_dates.append({"season": season,
                              "n": len(out_of_range),
                              "min": str(out_of_range.date.min()),
                              "max": str(out_of_range.date.max())})
    rep.add("A5.date_finestra", not bad_dates and df.date.notna().all(),
            f"{int(df.date.isna().sum())} date mancanti, "
            f"{len(bad_dates)} stagioni con date fuori finestra", bad=bad_dates)

    # A6 — una squadra non puo' giocare due volte lo stesso giorno
    long = pd.concat([
        df[["date", "season", "home_team"]].rename(columns={"home_team": "team"}),
        df[["date", "season", "away_team"]].rename(columns={"away_team": "team"}),
    ])
    same_day = long.duplicated(subset=["date", "team"])
    rep.add("A6.due_gare_stesso_giorno", not same_day.any(),
            f"{int(same_day.sum())} casi squadra con 2 gare nello stesso giorno",
            examples=long[same_day].head(5).astype(str).to_dict("records"))

    # A7 — nomi squadra: alias non applicati / quasi-duplicati
    teams = sorted(set(df.home_team) | set(df.away_team))
    unaliased = [t for t in teams if t in sources.TEAM_ALIASES]
    def _norm(s: str) -> str:
        return "".join(ch for ch in s.lower() if ch.isalnum())
    near = {}
    for i, a in enumerate(teams):
        for b in teams[i + 1:]:
            na, nb = _norm(a), _norm(b)
            if na != nb and (na in nb or nb in na):
                near[f"{a} | {b}"] = True
    rep.add("A7.nomi_squadra", not unaliased and not near,
            f"{len(teams)} squadre distinte; {len(unaliased)} nomi con alias non "
            f"applicato; {len(near)} coppie quasi-duplicate",
            n_teams=len(teams), unaliased=unaliased, near=sorted(near))

    # A8 — quote: validita' e overround (un book vero ha SEMPRE margine >= 0)
    odds_issues = {}
    for name, cols in (("1X2_chiusura", ["odds_home", "odds_draw", "odds_away"]),
                       ("1X2_apertura", ["odds_home_open", "odds_draw_open", "odds_away_open"]),
                       ("OU_chiusura", ["odds_over25", "odds_under25"]),
                       ("OU_apertura", ["odds_over25_open", "odds_under25_open"])):
        sub = df[cols]
        present = sub.notna().all(axis=1)
        partial = sub.notna().any(axis=1) & ~present
        low = (sub[present] <= 1.0).any(axis=1)
        orr = (1.0 / sub[present]).sum(axis=1)
        odds_issues[name] = {
            "coperte": int(present.sum()),
            "parziali": int(partial.sum()),
            "quote<=1": int(low.sum()),
            "overround<1": int((orr < 1.0).sum()),
            "overround_min": float(orr.min()) if present.any() else None,
            "overround_med": float(orr.median()) if present.any() else None,
            "overround_max": float(orr.max()) if present.any() else None,
        }
    bad_odds = any(v["quote<=1"] or v["overround<1"] or v["parziali"]
                   for v in odds_issues.values())
    rep.add("A8.quote_valide", not bad_odds,
            "quote: " + "; ".join(
                f"{k} n={v['coperte']} orr[{v['overround_min']:.3f},{v['overround_max']:.3f}]"
                if v["coperte"] else f"{k} n=0" for k, v in odds_issues.items()),
            **odds_issues)

    # A9 — copertura quote per stagione (la semantica dichiarata in DATI.md:
    #      chiusura O/U assente SOLO nel 2017-19; tutto il resto ~100%)
    cov = df.groupby("season")[["odds_home", "odds_over25", "odds_home_open",
                                "odds_over25_open"]].apply(lambda s: s.notna().mean())
    expected_missing_ou = {"1718", "1819"}
    ou_close_cov = cov["odds_over25"].to_dict()
    viol = {s: round(v, 4) for s, v in ou_close_cov.items()
            if (s in expected_missing_ou and v > 0) or (s not in expected_missing_ou and v < 0.99)}
    rep.add("A9.copertura_quote", not viol,
            f"copertura chiusura O/U conforme alla semantica dichiarata "
            f"(0% nel 2017-19, ~100% dal 2019-20): {len(viol)} deviazioni",
            coverage={k: {s: round(x, 4) for s, x in v.items()} for k, v in cov.to_dict().items()},
            violations=viol)

    # A10 — apertura vs chiusura: devono essere istantanee DIVERSE
    both = df[["odds_home", "odds_home_open"]].notna().all(axis=1)
    identical = (df.loc[both, "odds_home"] == df.loc[both, "odds_home_open"])
    frac = float(identical.mean()) if both.any() else float("nan")
    rep.add("A10.apertura_diversa", "PASS" if frac < 0.25 else "WARN",
            f"quota 1 apertura == chiusura nel {frac:.1%} delle righe "
            f"(n={int(both.sum())}); atteso basso (istantanee diverse)",
            frac_identical=frac)

    # A11 — xG e stile: copertura e range fisici
    xg_cols = ["home_xg", "away_xg", "home_npxg", "away_npxg"]
    cov_xg = float(df[xg_cols].notna().all(axis=1).mean())
    npxg_gt_xg = int(((df.home_npxg > df.home_xg + 1e-9) |
                      (df.away_npxg > df.away_xg + 1e-9)).sum())
    bad_range = int(((df[xg_cols] < 0).any(axis=1) | (df[xg_cols] > 10).any(axis=1)).sum())
    ppda_bad = int(((df[["home_ppda", "away_ppda"]] <= 0).any(axis=1)).sum())
    deep_bad = int(((df[["home_deep", "away_deep"]] < 0).any(axis=1)).sum())
    xg_ok = npxg_gt_xg == 0 and bad_range == 0 and ppda_bad == 0 and deep_bad == 0
    rep.add("A11.xg_stile", ("PASS" if (xg_ok and cov_xg > 0.999)
                             else ("WARN" if xg_ok else "FAIL")),
            f"copertura xG {cov_xg:.2%}; npxG>xG in {npxg_gt_xg} righe; "
            f"{bad_range} xG fuori range; {ppda_bad} PPDA<=0; {deep_bad} deep<0",
            coverage=cov_xg, npxg_gt_xg=npxg_gt_xg)

    # A12 — squad_value: lo stesso (squadra, stagione) deve avere lo STESSO
    #       valore in ogni riga in cui compare (in casa o in trasferta)
    long_sv = pd.concat([
        df[["season", "home_team", "home_squad_value"]]
          .rename(columns={"home_team": "team", "home_squad_value": "value"}),
        df[["season", "away_team", "away_squad_value"]]
          .rename(columns={"away_team": "team", "away_squad_value": "value"}),
    ])
    nun = long_sv.groupby(["season", "team"])["value"].nunique(dropna=False)
    incoherent = nun[nun > 1]
    n_nan = int(df[["home_squad_value", "away_squad_value"]].isna().any(axis=1).sum())
    rep.add("A12.squad_value", len(incoherent) == 0,
            f"{len(incoherent)} coppie (stagione,squadra) con valore rosa NON "
            f"costante; {n_nan} righe con valore mancante",
            incoherent=incoherent.head(10).to_dict(), n_nan=n_nan)

    # A13 — congestione e assenze: NaN e range
    rest = df[["home_rest_days_full", "away_rest_days_full"]]
    mid = df[["home_midweek_europe", "away_midweek_europe"]]
    abs_cnt = df[["home_absent_count_est", "away_absent_count_est"]]
    rep.add("A13.congestione_assenze",
            int(rest.isna().sum().sum()) == 0
            and bool(mid.isin([0, 1]).all().all())
            and bool(((rest >= 0) & (rest <= 60)).all().all()),
            f"riposo NaN={int(rest.isna().sum().sum())} range=[{rest.min().min()},"
            f"{rest.max().max()}]; midweek non binario="
            f"{int((~mid.isin([0, 1])).sum().sum())}; assenze NaN="
            f"{int(abs_cnt.isna().sum().sum())} max={abs_cnt.max().max()}")


# --------------------------------------------------------------------------- #
# B. Confronto con football-data ORIGINALE (ri-scaricato oggi)
# --------------------------------------------------------------------------- #
def _fresh_raw(league: str, season: str) -> pd.DataFrame:
    path = FONTI / "football_data" / f"{league}_{season}.csv"
    return pd.read_csv(path, encoding="latin-1")


def audit_vs_football_data(df: pd.DataFrame, league: str, rep: Report) -> dict:
    league_obj = sources.LEAGUES[league]   # le leghe nuove sono registrate a runtime
    frames = []
    for season in SEASONS:
        raw = _fresh_raw(league, season)
        norm = loader._normalize(raw, season, league_obj)
        frames.append(norm)
    fresh = pd.concat(frames, ignore_index=True)

    # B1 — stesse partite? (chiave: stagione + squadre canoniche)
    m = df[KEY].merge(fresh[KEY], on=KEY, how="outer", indicator=True)
    only_snap = m[m._merge == "left_only"]
    only_src = m[m._merge == "right_only"]
    rep.add("B1.stesse_partite", len(only_snap) == 0 and len(only_src) == 0,
            f"{len(only_snap)} partite solo nello snapshot, {len(only_src)} solo "
            f"nella fonte ri-scaricata (su {len(df)})",
            only_snapshot=only_snap[KEY].head(10).to_dict("records"),
            only_source=only_src[KEY].head(10).to_dict("records"))

    j = df.merge(fresh, on=KEY, how="inner", suffixes=("", "_src"))

    # B2 — gol e tiri in porta identici (escluse le correzioni DICHIARATE)
    corrette = _righe_corrette(league)
    is_corr = j.apply(lambda r: (r.season, r.home_team, r.away_team) in corrette, axis=1)
    if corrette:
        rep.add("B0.correzioni_dichiarate", "INFO",
                f"{int(is_corr.sum())} righe si discostano VOLUTAMENTE dalla fonte "
                f"(registro data/correzioni_dichiarate.csv, regola R1): "
                f"escluse dal confronto B2",
                righe=j.loc[is_corr, KEY + ["home_goals", "away_goals",
                                            "home_goals_src", "away_goals_src"]]
                        .to_dict("records"))
    j = j[~is_corr]
    gol_bad = j[(j.home_goals != j.home_goals_src) | (j.away_goals != j.away_goals_src)]
    sot_bad = j[((j.home_sot != j.home_sot_src) & j.home_sot.notna() & j.home_sot_src.notna())
                | ((j.away_sot != j.away_sot_src) & j.away_sot.notna() & j.away_sot_src.notna())]
    rep.add("B2.gol_e_tiri", len(gol_bad) == 0 and len(sot_bad) == 0,
            f"{len(gol_bad)} righe con GOL diversi dalla fonte; {len(sot_bad)} con "
            f"tiri in porta diversi",
            gol=gol_bad[KEY + ["home_goals", "away_goals", "home_goals_src",
                               "away_goals_src"]].head(10).to_dict("records"),
            sot=sot_bad[KEY + ["home_sot", "home_sot_src", "away_sot",
                               "away_sot_src"]].head(10).to_dict("records"))

    # B3 — date identiche
    date_bad = j[(j.date - j.date_src).abs() > pd.Timedelta(days=0)]
    rep.add("B3.date", len(date_bad) == 0,
            f"{len(date_bad)} righe con data diversa dalla fonte",
            examples=date_bad[KEY + ["date", "date_src"]].head(10).astype(str)
                             .to_dict("records"))

    # B4 — le 10 colonne quota RI-DERIVATE dalla fonte con il codice di
    #      produzione devono coincidere con quelle dello snapshot
    odds_cols = list(loader._ODDS_PREFERENCE) + list(loader._ODDS_PREFERENCE_OPEN)
    diffs = {}
    for c in odds_cols:
        a, b = j[c], j[f"{c}_src"]
        both_nan = a.isna() & b.isna()
        mism_nan = (a.isna() != b.isna())
        close = np.isclose(a.fillna(-1), b.fillna(-1), rtol=0, atol=1e-9)
        bad = (~close & ~both_nan)
        if int(bad.sum()) or int(mism_nan.sum()):
            ex = j.loc[bad, KEY + ["season", c, f"{c}_src"]].head(5)
            diffs[c] = {"n_diverse": int(bad.sum()),
                        "n_nan_mismatch": int(mism_nan.sum()),
                        "examples": ex.astype(str).to_dict("records")}
    rep.add("B4.quote_riderivate", not diffs,
            f"{len(diffs)}/10 colonne quota differiscono dalla ri-derivazione "
            f"dalla fonte originale", diffs=diffs)
    return {"n_join": len(j)}


# --------------------------------------------------------------------------- #
# C. Confronto con Understat ORIGINALE (fonte indipendente per i GOL)
# --------------------------------------------------------------------------- #
def audit_vs_understat(df: pd.DataFrame, league: str, rep: Report) -> None:
    frames_xg, frames_goals = [], []
    for season in SEASONS:
        year = 2000 + int(season[:2])
        path = FONTI / "understat" / f"{league}_{year}.json"
        data = json.loads(path.read_text())
        frames_xg.append(understat.parse_season_xg(data, season))
        rows = []
        for match in data.get("dates", []):
            if not match.get("isResult"):
                continue
            rows.append({
                "season": season,
                "home_team": sources.canonical_team(str(match["h"]["title"]).strip()),
                "away_team": sources.canonical_team(str(match["a"]["title"]).strip()),
                "ud_home_goals": int(match["goals"]["h"]),
                "ud_away_goals": int(match["goals"]["a"]),
            })
        frames_goals.append(pd.DataFrame(rows))
    xg = pd.concat(frames_xg, ignore_index=True)
    goals = pd.concat(frames_goals, ignore_index=True)

    # C1 — GOL secondo Understat == gol dello snapshot (fonte INDIPENDENTE)
    j = df.merge(goals, on=KEY, how="left", validate="one_to_one")
    matched = j.ud_home_goals.notna()
    bad = j[matched & ((j.ud_home_goals != j.home_goals) | (j.ud_away_goals != j.away_goals))]
    n_unmatched = int((~matched).sum())
    rep.add("C1.gol_fonte_indipendente",
            "PASS" if (len(bad) == 0 and n_unmatched == 0)
            else ("WARN" if len(bad) == 0 else "FAIL"),
            f"{len(bad)} righe con gol diversi tra football-data e Understat; "
            f"{n_unmatched} partite senza corrispondenza Understat (lacuna della fonte)",
            examples=bad[KEY + ["home_goals", "away_goals", "ud_home_goals",
                                "ud_away_goals"]].head(10).to_dict("records"),
            unmatched=j.loc[~matched, KEY].head(10).to_dict("records"))

    # C2 — xG/npxG/PPDA/deep ri-parsati == snapshot (escluse le correzioni
    #      dichiarate: quelle righe si discostano VOLUTAMENTE dalla fonte)
    jx = df.merge(xg.rename(columns={"date": "ud_date"}), on=KEY, how="left",
                  suffixes=("", "_src"), validate="one_to_one")
    corrette = _righe_corrette(league)
    if corrette:
        jx = jx[~jx.apply(
            lambda r: (r.season, r.home_team, r.away_team) in corrette, axis=1)]
    diffs = {}
    for c in understat.XG_COLUMNS:
        a, b = jx[c], jx[f"{c}_src"]
        both_nan = a.isna() & b.isna()
        bad = ~np.isclose(a.fillna(-999), b.fillna(-999), rtol=0, atol=1e-6) & ~both_nan
        if int(bad.sum()):
            diffs[c] = {"n_diverse": int(bad.sum()),
                        "examples": jx.loc[bad, KEY + [c, f"{c}_src"]].head(5)
                                      .astype(str).to_dict("records")}
    rep.add("C2.xg_riparsato", not diffs,
            f"{len(diffs)}/8 colonne xG/stile differiscono dal ri-parsing della "
            f"fonte Understat", diffs=diffs)

    # C3 — date coerenti tra le due fonti (diagnostica: la chiave e' squadre+stagione)
    both = jx.ud_date.notna()
    gap = (jx.loc[both, "ud_date"] - jx.loc[both, "date"]).abs()
    n_gap = int((gap > pd.Timedelta(days=1)).sum())
    rep.add("C3.date_due_fonti", "PASS" if n_gap == 0 else "WARN",
            f"{n_gap} partite con date football-data/Understat distanti >1 giorno",
            n=n_gap)


# --------------------------------------------------------------------------- #
# D. Sanita' statistica (i numeri "di lega" devono somigliare alla realta')
# --------------------------------------------------------------------------- #
def audit_stats(df: pd.DataFrame, league: str, rep: Report) -> None:
    stats = {}
    for season, s in df.groupby("season"):
        gh, ga = s.home_goals.mean(), s.away_goals.mean()
        stats[season] = {
            "gare": len(s),
            "gol_gara": round(float(gh + ga), 3),
            "casa%": round(float((s.result == "H").mean()), 3),
            "pari%": round(float((s.result == "D").mean()), 3),
            "over25%": round(float(((s.home_goals + s.away_goals) > 2.5).mean()), 3),
            "gamma_ln_casa_ospite": round(float(np.log(gh / ga)), 3),
        }
    g = np.array([v["gol_gara"] for v in stats.values()])
    h = np.array([v["casa%"] for v in stats.values()])
    ok = bool((g > 2.0).all() and (g < 3.6).all() and (h > 0.30).all() and (h < 0.60).all())
    rep.add("D1.statistiche_lega", ok,
            f"gol/gara {g.min():.2f}-{g.max():.2f}; vittorie casa "
            f"{h.min():.1%}-{h.max():.1%} (range plausibili per un campionato)",
            per_season=stats)

    # D2 — il mercato deve essere CALIBRATO: la probabilita' devigata della
    #      chiusura 1X2 deve stare vicino alla frequenza osservata.
    from src.evaluation.metrics import devig_1x2
    sub = df.dropna(subset=["odds_home", "odds_draw", "odds_away"])
    p = np.array([devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                  for r in sub.itertuples()])
    obs = np.array([[r.result == "H", r.result == "D", r.result == "A"]
                    for r in sub.itertuples()], dtype=float)
    bias = (p.mean(axis=0) - obs.mean(axis=0))
    ok = bool(np.abs(bias).max() < 0.03)
    rep.add("D2.mercato_calibrato", ok,
            f"scarto medio prob.mercato - frequenza osservata: "
            f"H {bias[0]:+.4f}, D {bias[1]:+.4f}, A {bias[2]:+.4f} (n={len(sub)})",
            bias=[float(b) for b in bias], n=len(sub))

    # D3 — margine del book per stagione: deve riflettere la semantica
    #      dichiarata (2017-19 Pinnacle ~2.5%, dal 2019-20 media ~5%)
    marg = {}
    for season, s in df.groupby("season"):
        ss = s.dropna(subset=["odds_home", "odds_draw", "odds_away"])
        if len(ss):
            marg[season] = round(float((1 / ss.odds_home + 1 / ss.odds_draw
                                        + 1 / ss.odds_away).mean() - 1), 4)
    early = [marg[s] for s in ("1718", "1819") if s in marg]
    late = [v for s, v in marg.items() if s not in ("1718", "1819")]
    ok = bool(early and late and max(early) < min(late))
    rep.add("D3.margine_per_stagione", "PASS" if ok else "WARN",
            f"margine 1X2: 2017-19 {['%.2f%%' % (v*100) for v in early]} (Pinnacle) "
            f"vs dal 2019-20 {min(late)*100:.2f}%-{max(late)*100:.2f}% (media book)",
            per_season=marg)


def main() -> int:
    leagues = sys.argv[1:] or list(SNAP_DIR)
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {}
    for league in leagues:
        print(f"\n=== AUDIT {league} ===")
        df = pd.read_csv(SNAP_DIR[league] / f"{league}_matches.csv",
                         dtype={"season": str}, parse_dates=["date"])
        rep = Report(league)
        print(" A. controlli interni")
        audit_internal(df, league, rep)
        print(" B. confronto con football-data.co.uk (ri-scaricato oggi)")
        audit_vs_football_data(df, league, rep)
        print(" C. confronto con Understat (fonte indipendente)")
        audit_vs_understat(df, league, rep)
        print(" D. sanita' statistica")
        audit_stats(df, league, rep)
        (OUT / f"audit_{league}.json").write_text(
            json.dumps({"league": league, "n_rows": len(df),
                        "checks": rep.checks}, indent=2, default=str))
        summary[league] = {"FAIL": len(rep.failed), "WARN": len(rep.warned),
                           "totale": len(rep.checks)}
        print(f" -> {len(rep.failed)} FAIL, {len(rep.warned)} WARN su {len(rep.checks)} controlli")

    print("\n=== RIASSUNTO ===")
    for lg, s in summary.items():
        print(f"  {lg:16s} FAIL={s['FAIL']}  WARN={s['WARN']}  ({s['totale']} controlli)")
    return 1 if any(s["FAIL"] for s in summary.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
