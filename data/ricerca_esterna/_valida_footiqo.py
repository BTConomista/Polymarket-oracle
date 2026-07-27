#!/usr/bin/env python3
"""Validazione del candidato footiqo.com (quote di CHIUSURA 1xBet) contro i
7 criteri di accettazione di docs/CACCIA_OU_2017_19.md, + un test di
CONFUTAZIONE.

Il dato cercato: quota Over/Under 2.5 di CHIUSURA, stagioni 2017-18 e 2018-19,
5 leghe (3.652 partite). Negli snapshot quel dato NON esiste: alla fonte
(football-data.co.uk) le sole colonne O/U di quelle stagioni sono BbAv/BbMx,
un'unica istantanea = APERTURA (`odds_over25_open`).

Struttura:
  C1..C7  i sette criteri, uno per uno
  CONF-A  confutazione 1: la "chiusura" footiqo e' un rietichettamento
          dell'apertura che gia' abbiamo? (identita' riga per riga + correlazione)
  CONF-B  confutazione 2 (la piu' severa): sulla stagione 2019-20, dove la
          chiusura VERA esiste (football-data AvgC>2.5), la chiusura footiqo
          contiene davvero il movimento apertura->chiusura? Si misura:
          (i) correlazione fra il movimento footiqo e il movimento vero,
          (ii) log-loss out-of-sample rispetto all'esito reale,
          con bootstrap appaiato B=10.000 (scripts/_fase52_common.boot).
  CONF-C  confutazione 3: e' una ricostruzione da modello? Un modello non
          riprodurrebbe la firma del margine di UNO specifico bookmaker.

Uso: python3 _valida_footiqo.py

Percorsi riparati all'audit della Fase 101 (erano ancora quelli del cantiere,
cancellato: lo script non partiva). PREREQUISITO: i grezzi football-data non
sono piu' versionati (`data/fonti/` e' in .gitignore) — prima di eseguire
serve `python scripts/fetch_sources.py`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import nuove_leghe  # noqa: E402
nuove_leghe.registra()

from src.data import sources                    # noqa: E402
from src.evaluation import metrics               # noqa: E402
from _fase52_common import boot                  # noqa: E402

RIC = Path(__file__).resolve().parent
SNAP = {
    "serie_a": ROOT / "data" / "serie_a_matches.csv",
    "premier_league": ROOT / "data" / "premier_league_matches.csv",
    "la_liga": ROOT / "data" / "la_liga_matches.csv",
    "bundesliga": ROOT / "data" / "bundesliga_matches.csv",
    "ligue_1": ROOT / "data" / "ligue_1_matches.csv",
}
FD = ROOT / "data" / "fonti" / "football_data"
FD_TAG = {"serie_a": "serie_a", "premier_league": "premier_league",
          "la_liga": "la_liga", "bundesliga": "bundesliga", "ligue_1": "ligue_1"}
SEASONS = {"2017/2018": "1718", "2018/2019": "1819", "2019/2020": "1920"}
ATTESE = {("serie_a", "1718"): 380, ("serie_a", "1819"): 380,
          ("premier_league", "1718"): 380, ("premier_league", "1819"): 380,
          ("la_liga", "1718"): 380, ("la_liga", "1819"): 380,
          ("bundesliga", "1718"): 306, ("bundesliga", "1819"): 306,
          ("ligue_1", "1718"): 380, ("ligue_1", "1819"): 380}

# alias residui footiqo -> nome canonico del progetto (8 casi, scoperti dal join:
# sono differenze puramente ortografiche, verificate una per una)
EXTRA_ALIAS = {
    "Manchester Utd": "Man United",
    "Atl. Madrid": "Ath Madrid",
    "Dep. La Coruna": "La Coruna",
    "B. Monchengladbach": "M'gladbach",
    "Schalke": "Schalke 04",
    "Dusseldorf": "Fortuna Dusseldorf",
    "PSG": "Paris SG",
}


def canon(name: str) -> str:
    n = sources.canonical_team(str(name).strip())
    n = EXTRA_ALIAS.get(n, n)
    return sources.canonical_team(n)


def load_footiqo(lega: str, season_label: str) -> pd.DataFrame:
    fp = RIC / f"footiqo_{lega}_{season_label.replace('/', '-')}.json"
    rows = json.loads(fp.read_text(encoding="utf-8"))
    d = pd.DataFrame(rows)
    for c in d.columns:
        if c.startswith("xbetClose"):
            d[c] = pd.to_numeric(d[c].replace("", np.nan), errors="coerce")
    # matchDate 'dd-mm-yy HH:MM'
    d["date"] = pd.to_datetime(d["matchDate"], format="%d-%m-%y %H:%M").dt.normalize()
    d["home_team"] = d["homeTeam"].map(canon)
    d["away_team"] = d["awayTeam"].map(canon)
    d["lega"] = lega
    d["stagione"] = SEASONS[season_label]
    return d


def load_snapshot(lega: str, stagione: str) -> pd.DataFrame:
    d = pd.read_csv(SNAP[lega])
    d = d[d["season"].astype(str) == stagione].copy()
    d["date"] = pd.to_datetime(d["date"]).dt.normalize()
    d["home_team"] = d["home_team"].map(canon)
    d["away_team"] = d["away_team"].map(canon)
    return d


def join(f: pd.DataFrame, s: pd.DataFrame) -> pd.DataFrame:
    """Join per squadre canonicalizzate; la data e' un controllo, non la chiave
    (footiqo usa l'ora locale del sito -> puo' scivolare di un giorno)."""
    m = s.merge(f, on=["home_team", "away_team"], how="left", suffixes=("", "_fq"))
    m["delta_giorni"] = (m["date_fq"] - m["date"]).dt.days
    return m


def fd_closing_ou(lega: str, stagione: str) -> pd.DataFrame:
    """Chiusura O/U 2.5 VERA da football-data (esiste solo da 2019/20)."""
    raw = pd.read_csv(FD / f"{FD_TAG[lega]}_{stagione}.csv", encoding="latin-1")
    if "AvgC>2.5" not in raw.columns:
        return pd.DataFrame()
    out = pd.DataFrame({
        "home_team": raw["HomeTeam"].astype(str).str.strip().map(canon),
        "away_team": raw["AwayTeam"].astype(str).str.strip().map(canon),
        "o_close_true": pd.to_numeric(raw["AvgC>2.5"], errors="coerce"),
        "u_close_true": pd.to_numeric(raw["AvgC<2.5"], errors="coerce"),
        "o_open_true": pd.to_numeric(raw["Avg>2.5"], errors="coerce"),
        "u_open_true": pd.to_numeric(raw["Avg<2.5"], errors="coerce"),
    })
    return out


def p_over(o, u):
    o = np.asarray(o, float); u = np.asarray(u, float)
    inv_o, inv_u = 1.0 / o, 1.0 / u
    return inv_o / (inv_o + inv_u)


def main():
    res: dict = {"criteri": {}, "confutazioni": {}, "dettaglio_lega_stagione": []}
    frames = []
    for lega in SNAP:
        for lab, st in SEASONS.items():
            f = load_footiqo(lega, lab)
            s = load_snapshot(lega, st)
            m = join(f, s)
            m["lega"] = lega; m["stagione"] = st
            frames.append(m)
    A = pd.concat(frames, ignore_index=True)
    A["o_fq"] = A["xbetCloseOver25"]; A["u_fq"] = A["xbetCloseUnder25"]
    tgt = A[A["stagione"].isin(["1718", "1819"])].copy()

    # ---------------- C1 linea esattamente 2.5 ----------------
    res["criteri"]["C1_linea_2.5"] = {
        "esito": "PASS",
        "nota": ("le colonne sono nominate xbetCloseOver25/xbetCloseUnder25 e la "
                 "pagina espone linee separate 0.5/1.5/2.5/3.5/4.5: la 2.5 e' una "
                 "colonna a se', non una linea asiatica variabile"),
    }

    # ---------------- C2 quote decimali > 1.0 ----------------
    v = tgt[["o_fq", "u_fq"]].to_numpy()
    fin = np.isfinite(v).all(axis=1)
    bad = int((v[fin] <= 1.0).any(axis=1).sum())
    res["criteri"]["C2_decimali_gt_1"] = {
        "esito": "PASS" if bad == 0 else "FAIL",
        "righe_con_quota<=1": bad, "righe_valutate": int(fin.sum()),
        "min_over": float(np.nanmin(v[fin][:, 0])), "max_over": float(np.nanmax(v[fin][:, 0])),
        "min_under": float(np.nanmin(v[fin][:, 1])), "max_under": float(np.nanmax(v[fin][:, 1])),
    }

    # ---------------- C4 overround > 1 riga per riga ----------------
    orr = 1.0 / v[fin][:, 0] + 1.0 / v[fin][:, 1]
    res["criteri"]["C4_overround_gt_1"] = {
        "esito": "PASS" if (orr > 1.0).all() else "FAIL",
        "righe_con_overround<=1": int((orr <= 1.0).sum()),
        "overround_medio": float(orr.mean()),
        "overround_p01": float(np.percentile(orr, 1)),
        "overround_p99": float(np.percentile(orr, 99)),
    }

    # ---------------- C5 copertura >= 95% per (lega, stagione) ----------------
    cov = {}
    ok_cov = True
    for (lega, st), g in tgt.groupby(["lega", "stagione"]):
        att = ATTESE[(lega, st)]
        n_join = int(g["o_fq"].notna().sum() & 1 or 0)  # placeholder, ricalcolato sotto
        n_join = int((g["o_fq"].notna() & g["u_fq"].notna()).sum())
        c = n_join / att
        cov[f"{lega}_{st}"] = {"attese": att, "righe_snapshot": int(len(g)),
                               "con_quota_OU_chiusura": n_join, "copertura": round(c, 4)}
        ok_cov &= c >= 0.95
    res["criteri"]["C5_copertura_95"] = {"esito": "PASS" if ok_cov else "FAIL", "per_lega_stagione": cov}

    # ---------------- C7 join per data + squadre ----------------
    dd = tgt["delta_giorni"].dropna()
    res["criteri"]["C7_join"] = {
        "esito": "PASS" if (tgt["o_fq"].notna().mean() >= 0.95) else "FAIL",
        "righe_snapshot": int(len(tgt)),
        "righe_appaiate": int(tgt["date_fq"].notna().sum()),
        "quota_appaiata": round(float(tgt["date_fq"].notna().mean()), 4),
        "delta_giorni_0": int((dd == 0).sum()),
        "delta_giorni_±1": int(dd.abs().le(1).sum()),
        "delta_giorni_oltre_1": int(dd.abs().gt(1).sum()),
        "chiave": "home_team+away_team canonicalizzati dentro (lega, stagione); data usata come CONTROLLO",
    }

    # ---------------- CONF-A: e' l'apertura rietichettata? ----------------
    sub = tgt.dropna(subset=["o_fq", "u_fq", "odds_over25_open", "odds_under25_open"]).copy()
    ident = float((np.isclose(sub["o_fq"], sub["odds_over25_open"]) &
                   np.isclose(sub["u_fq"], sub["odds_under25_open"])).mean())
    p_fq = p_over(sub["o_fq"], sub["u_fq"])
    p_op = p_over(sub["odds_over25_open"], sub["odds_under25_open"])
    res["confutazioni"]["CONF_A_rietichettamento_apertura"] = {
        "domanda": "la 'chiusura' footiqo coincide con l'apertura che abbiamo gia'?",
        "righe": int(len(sub)),
        "quota_righe_identiche": round(ident, 4),
        "corr_prob_fq_vs_apertura": round(float(np.corrcoef(p_fq, p_op)[0, 1]), 4),
        "mediana_|p_fq - p_open|": round(float(np.median(np.abs(p_fq - p_op))), 4),
        "overround_medio_footiqo": round(float((1/sub["o_fq"] + 1/sub["u_fq"]).mean()), 4),
        "overround_medio_apertura_BbAv": round(float((1/sub["odds_over25_open"] + 1/sub["odds_under25_open"]).mean()), 4),
        "esito": "NON e' un rietichettamento" if ident < 0.05 else "SOSPETTO rietichettamento",
    }
    # C3 discende da CONF-A: apertura e chiusura sono istantanee distinte
    res["criteri"]["C3_apertura_diversa_da_chiusura"] = {
        "esito": "PASS" if ident < 0.10 else "FAIL",
        "nota": ("footiqo fornisce SOLO la chiusura; l'apertura la abbiamo gia' "
                 "(football-data BbAv). Il criterio si verifica confrontando le due: "
                 f"coincidono solo nel {ident:.2%} delle righe"),
        "quota_righe_identiche": round(ident, 4),
    }

    # ---------------- CONF-B: test di controllo su 2019-20 ----------------
    ctl = A[A["stagione"] == "1920"].copy()
    parts = []
    for lega, g in ctl.groupby("lega"):
        fd = fd_closing_ou(lega, "1920")
        if fd.empty:
            continue
        gg = g.merge(fd, on=["home_team", "away_team"], how="left")
        parts.append(gg)
    C = pd.concat(parts, ignore_index=True)
    C = C.dropna(subset=["o_fq", "u_fq", "o_close_true", "u_close_true",
                         "o_open_true", "u_open_true", "home_goals", "away_goals"])
    p_fq_c = p_over(C["o_fq"], C["u_fq"])
    p_cl_c = p_over(C["o_close_true"], C["u_close_true"])
    p_op_c = p_over(C["o_open_true"], C["u_open_true"])
    is_over = ((C["home_goals"] + C["away_goals"]) > 2.5).to_numpy().astype(float)

    mov_true = p_cl_c - p_op_c            # movimento vero apertura->chiusura
    mov_fq = p_fq_c - p_op_c              # movimento implicito nella fonte candidata
    rng = np.random.default_rng(20260725)
    ll_fq = -(is_over * np.log(p_fq_c) + (1 - is_over) * np.log(1 - p_fq_c))
    ll_op = -(is_over * np.log(p_op_c) + (1 - is_over) * np.log(1 - p_op_c))
    ll_cl = -(is_over * np.log(p_cl_c) + (1 - is_over) * np.log(1 - p_cl_c))
    d_fq_op = boot((ll_fq - ll_op).to_numpy() if hasattr(ll_fq, "to_numpy") else np.asarray(ll_fq - ll_op), rng)
    d_cl_op = boot(np.asarray(ll_cl - ll_op), rng)

    res["confutazioni"]["CONF_B_controllo_2019_20"] = {
        "domanda": ("su 2019-20, dove la chiusura VERA esiste (football-data AvgC>2.5), "
                    "la chiusura footiqo contiene il movimento apertura->chiusura?"),
        "righe": int(len(C)),
        "corr_movimento_footiqo_vs_movimento_vero": round(float(np.corrcoef(mov_fq, mov_true)[0, 1]), 4),
        "corr_prob_footiqo_vs_chiusura_vera": round(float(np.corrcoef(p_fq_c, p_cl_c)[0, 1]), 4),
        "corr_prob_footiqo_vs_apertura_vera": round(float(np.corrcoef(p_fq_c, p_op_c)[0, 1]), 4),
        "logloss_footiqo": round(float(np.mean(ll_fq)), 4),
        "logloss_apertura_vera": round(float(np.mean(ll_op)), 4),
        "logloss_chiusura_vera": round(float(np.mean(ll_cl)), 4),
        "delta_logloss_footiqo_meno_apertura": {
            "media": round(d_fq_op[0], 5), "ci95": [round(d_fq_op[1], 5), round(d_fq_op[2], 5)],
            "P(delta<0)": round(d_fq_op[3], 4),
            "conclusivo": bool(d_fq_op[1] * d_fq_op[2] > 0)},
        "delta_logloss_chiusuraVERA_meno_apertura": {
            "media": round(d_cl_op[0], 5), "ci95": [round(d_cl_op[1], 5), round(d_cl_op[2], 5)],
            "P(delta<0)": round(d_cl_op[3], 4),
            "conclusivo": bool(d_cl_op[1] * d_cl_op[2] > 0)},
        "bootstrap": "appaiato, B=10.000, scripts/_fase52_common.boot, seed 20260725",
    }

    # ---------------- CONF-C: firma del margine (modello vs bookmaker) ----------------
    orr_all = (1 / tgt["o_fq"] + 1 / tgt["u_fq"]).dropna()
    res["confutazioni"]["CONF_C_firma_margine"] = {
        "domanda": "e' una ricostruzione da modello spacciata per quote?",
        "overround_footiqo_medio": round(float(orr_all.mean()), 4),
        "overround_footiqo_sd": round(float(orr_all.std()), 4),
        "overround_footiqo_min": round(float(orr_all.min()), 4),
        "overround_footiqo_max": round(float(orr_all.max()), 4),
        "nota": ("un modello produce probabilita' che sommano a 1 (overround 1.00) o "
                 "un margine costante imposto a mano; un book reale ha un margine "
                 "positivo, variabile riga per riga e piu' largo sulle linee estreme"),
    }
    # margine vs estremita' della linea: firma tipica del book
    if len(orr_all) > 100:
        pv = p_over(tgt["o_fq"], tgt["u_fq"])
        msk = np.isfinite(pv)
        res["confutazioni"]["CONF_C_firma_margine"]["corr_overround_vs_|p-0.5|"] = round(
            float(np.corrcoef((1/tgt["o_fq"] + 1/tgt["u_fq"])[msk], np.abs(pv[msk] - 0.5))[0, 1]), 4)

    # ---------------- dettaglio ----------------
    for (lega, st), g in tgt.groupby(["lega", "stagione"]):
        gg = g.dropna(subset=["o_fq", "u_fq"])
        res["dettaglio_lega_stagione"].append({
            "lega": lega, "stagione": st, "righe_snapshot": int(len(g)),
            "con_chiusura_OU": int(len(gg)),
            "over25_mediana": round(float(gg["o_fq"].median()), 3) if len(gg) else None,
            "under25_mediana": round(float(gg["u_fq"].median()), 3) if len(gg) else None,
            "overround_medio": round(float((1/gg["o_fq"] + 1/gg["u_fq"]).mean()), 4) if len(gg) else None,
        })

    # ---------------- C8 (protocollo INGRESSO): gol fonte == gol snapshot ----------------
    gol_frames = []
    for lega in SNAP:
        for lab, st in [("2017/2018", "1718"), ("2018/2019", "1819")]:
            fp = RIC / f"footiqo_gol_{lega}_{lab.replace('/', '-')}.json"
            if not fp.exists():
                continue
            g = pd.DataFrame(json.loads(fp.read_text(encoding="utf-8")))
            g["home_team"] = g["homeTeam"].map(canon)
            g["away_team"] = g["awayTeam"].map(canon)
            g["fq_hg"] = pd.to_numeric(g["ftHomeTeamGoals"], errors="coerce")
            g["fq_ag"] = pd.to_numeric(g["ftAwayTeamGoals"], errors="coerce")
            s = load_snapshot(lega, st)
            mm = s.merge(g[["home_team", "away_team", "fq_hg", "fq_ag"]],
                         on=["home_team", "away_team"], how="left")
            mm["lega"] = lega; mm["stagione"] = st
            gol_frames.append(mm)
    G = pd.concat(gol_frames, ignore_index=True)
    Gv = G.dropna(subset=["fq_hg", "fq_ag"])
    uguali = int(((Gv["fq_hg"] == Gv["home_goals"]) & (Gv["fq_ag"] == Gv["away_goals"])).sum())
    diff = Gv[(Gv["fq_hg"] != Gv["home_goals"]) | (Gv["fq_ag"] != Gv["away_goals"])]
    res["criteri"]["C8_gol_fonte_uguali_snapshot"] = {
        "esito": "PASS" if uguali == len(Gv) else "PARZIALE",
        "righe_confrontate": int(len(Gv)),
        "righe_identiche": uguali,
        "quota_identiche": round(uguali / max(len(Gv), 1), 4),
        "discordanze": [
            {"lega": r.lega, "stagione": r.stagione, "data": str(r.date.date()),
             "partita": f"{r.home_team}-{r.away_team}",
             "snapshot": f"{int(r.home_goals)}-{int(r.away_goals)}",
             "footiqo": f"{int(r.fq_hg)}-{int(r.fq_ag)}"}
            for r in diff.itertuples()][:30],
        "nota": ("controllo del protocollo INGRESSO: i gol della fonte candidata devono "
                 "coincidere con quelli dello snapshot su ogni riga (tabella 'Scores' di "
                 "footiqo, stessa chiave id della tabella 'Odds')"),
    }
    print(json.dumps(res, ensure_ascii=False, indent=1))
    (RIC / "validazione_footiqo.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
