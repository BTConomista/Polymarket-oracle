#!/usr/bin/env python3
"""Test di CONFUTAZIONE decisivi sul candidato footiqo (chiusura 1xBet).

L'obiezione piu' seria che resta dopo i 7 criteri: "e' comunque una
RICOSTRUZIONE da modello". Il test CONF-B (movimento 2019-20) non la esclude
del tutto, perche' la stima E3 del progetto raggiunge gia' una correlazione
0.75-0.86 col movimento vero partendo dall'1X2.

Servono discriminanti che un modello NON puo' produrre. Qui tre:

CONF-D (decisivo, DENTRO la finestra bersaglio).
  Per il 2017-19 l'1X2 di apertura E di chiusura sono dati REALI e li abbiamo
  gia' (Pinnacle PSH/PSD/PSA -> PSCH/PSCD/PSCA). footiqo pubblica anche il suo
  1X2 di chiusura (xbetClose1FT/XFT/2FT). Se footiqo e' una fotografia scattata
  davvero all'ora di chiusura, il suo 1X2 deve somigliare alla CHIUSURA vera
  piu' che all'APERTURA vera, e il suo movimento deve correlare col movimento
  vero -- proprio nelle stagioni bersaglio, non per estrapolazione.
  Un modello che ricostruisse la sola O/U non avrebbe motivo di riprodurre
  anche il movimento 1X2 partita per partita.

CONF-E (firma del bookmaker).
  1xBet NON e' fra i book di football-data. Se footiqo riesportasse
  football-data, il suo margine e il suo reticolo di prezzi coinciderebbero con
  quelli di un book presente li'. Si confrontano margine 1X2 e margine O/U con
  tutti i book di football-data disponibili nelle stagioni bersaglio.

CONF-F (utilita' pratica).
  Il dato trovato batte davvero cio' che abbiamo gia' (apertura reale + stima
  E3) sulle stagioni bersaglio, dove la verita' (i gol) esiste?
  Log-loss binaria O/U 2.5, bootstrap appaiato B=10.000.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/Polymarket-oracle")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "cantiere" / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

import nuove_leghe  # noqa: E402
nuove_leghe.registra()

from src.data import sources                 # noqa: E402
from src.evaluation import metrics            # noqa: E402
from _fase52_common import boot               # noqa: E402

RIC = ROOT / "cantiere" / "data" / "ricerca"
FD = ROOT / "cantiere" / "data" / "fonti" / "football_data"
SNAP = {
    "serie_a": ROOT / "data" / "serie_a_matches.csv",
    "premier_league": ROOT / "data" / "premier_league_matches.csv",
    "la_liga": ROOT / "data" / "la_liga_matches.csv",
    "bundesliga": ROOT / "cantiere" / "data" / "bundesliga_matches.csv",
    "ligue_1": ROOT / "cantiere" / "data" / "ligue_1_matches.csv",
}
EXTRA_ALIAS = {"Manchester Utd": "Man United", "Atl. Madrid": "Ath Madrid",
               "Dep. La Coruna": "La Coruna", "B. Monchengladbach": "M'gladbach",
               "Schalke": "Schalke 04", "Dusseldorf": "Fortuna Dusseldorf",
               "PSG": "Paris SG"}
SEAS = [("2017/2018", "1718"), ("2018/2019", "1819")]


def canon(name):
    n = sources.canonical_team(str(name).strip())
    return sources.canonical_team(EXTRA_ALIAS.get(n, n))


def p_over(o, u):
    o, u = np.asarray(o, float), np.asarray(u, float)
    return (1 / o) / (1 / o + 1 / u)


def devig3(h, d, a):
    inv = np.column_stack([1 / np.asarray(h, float), 1 / np.asarray(d, float),
                           1 / np.asarray(a, float)])
    return inv / inv.sum(axis=1, keepdims=True)


def build():
    fr = []
    for lega, fp in SNAP.items():
        snap = pd.read_csv(fp)
        snap["home_team"] = snap["home_team"].map(canon)
        snap["away_team"] = snap["away_team"].map(canon)
        for lab, st in SEAS:
            f = pd.DataFrame(json.loads(
                (RIC / f"footiqo_{lega}_{lab.replace('/', '-')}.json").read_text(encoding="utf-8")))
            for c in f.columns:
                if c.startswith("xbetClose"):
                    f[c] = pd.to_numeric(f[c].replace("", np.nan), errors="coerce")
            f["home_team"] = f["homeTeam"].map(canon)
            f["away_team"] = f["awayTeam"].map(canon)
            raw = pd.read_csv(FD / f"{lega}_{st}.csv", encoding="latin-1")
            raw["home_team"] = raw["HomeTeam"].astype(str).str.strip().map(canon)
            raw["away_team"] = raw["AwayTeam"].astype(str).str.strip().map(canon)
            s = snap[snap["season"].astype(str) == st].copy()
            m = s.merge(f, on=["home_team", "away_team"], how="left")
            m = m.merge(raw, on=["home_team", "away_team"], how="left", suffixes=("", "_fd"))
            m["lega"], m["stagione"] = lega, st
            fr.append(m)
    return pd.concat(fr, ignore_index=True)


def main():
    A = build()
    out = {}
    rng = np.random.default_rng(20260725)

    # ---------- CONF-D: 1X2 di footiqo vs 1X2 vero (apertura e chiusura Pinnacle) ----------
    need = ["xbetClose1FT", "xbetCloseXFT", "xbetClose2FT",
            "PSH", "PSD", "PSA", "PSCH", "PSCD", "PSCA"]
    D = A.dropna(subset=need).copy()
    p_fq = devig3(D["xbetClose1FT"], D["xbetCloseXFT"], D["xbetClose2FT"])
    p_op = devig3(D["PSH"], D["PSD"], D["PSA"])
    p_cl = devig3(D["PSCH"], D["PSCD"], D["PSCA"])
    res_d = {"righe": int(len(D)),
             "nota": ("1X2 2017-19: apertura e chiusura REALI (Pinnacle, gia' negli "
                      "snapshot). footiqo e' 1xBet: livelli diversi, ma se e' una "
                      "istantanea di chiusura deve MUOVERSI come la chiusura vera.")}
    for j, lbl in enumerate(["home", "draw", "away"]):
        mv_fq = p_fq[:, j] - p_op[:, j]
        mv_tr = p_cl[:, j] - p_op[:, j]
        res_d[f"corr_footiqo_vs_CHIUSURA_vera_{lbl}"] = round(float(np.corrcoef(p_fq[:, j], p_cl[:, j])[0, 1]), 4)
        res_d[f"corr_footiqo_vs_APERTURA_vera_{lbl}"] = round(float(np.corrcoef(p_fq[:, j], p_op[:, j])[0, 1]), 4)
        res_d[f"corr_MOVIMENTO_footiqo_vs_vero_{lbl}"] = round(float(np.corrcoef(mv_fq, mv_tr)[0, 1]), 4)
    # log-loss 1X2 contro l'esito vero
    outc = D["result"].tolist()
    res_d["logloss_1x2_footiqo"] = round(metrics.log_loss_1x2(p_fq, outc), 4)
    res_d["logloss_1x2_apertura_vera_Pinnacle"] = round(metrics.log_loss_1x2(p_op, outc), 4)
    res_d["logloss_1x2_chiusura_vera_Pinnacle"] = round(metrics.log_loss_1x2(p_cl, outc), 4)
    out["CONF_D_1x2_dentro_la_finestra_bersaglio"] = res_d

    # ---------- CONF-E: firma del margine vs tutti i book di football-data ----------
    orr_fq_ou = (1 / A["xbetCloseOver25"] + 1 / A["xbetCloseUnder25"]).dropna()
    orr_fq_1x2 = (1 / D["xbetClose1FT"] + 1 / D["xbetCloseXFT"] + 1 / D["xbetClose2FT"])
    books = {"B365": ("B365H", "B365D", "B365A"), "BW": ("BWH", "BWD", "BWA"),
             "IW": ("IWH", "IWD", "IWA"), "PS_open": ("PSH", "PSD", "PSA"),
             "PS_close": ("PSCH", "PSCD", "PSCA"), "WH": ("WHH", "WHD", "WHA"),
             "VC": ("VCH", "VCD", "VCA"), "BbAv": ("BbAvH", "BbAvD", "BbAvA"),
             "BbMx": ("BbMxH", "BbMxD", "BbMxA")}
    marg = {}
    for b, (h, d, a) in books.items():
        if set((h, d, a)) <= set(A.columns):
            v = (1 / A[h] + 1 / A[d] + 1 / A[a]).dropna()
            if len(v):
                marg[b] = round(float(v.mean()), 4)
    out["CONF_E_firma_margine"] = {
        "margine_1x2_footiqo_1xBet": round(float(orr_fq_1x2.mean()), 4),
        "margine_1x2_book_di_football_data": marg,
        "margine_OU_footiqo_1xBet": round(float(orr_fq_ou.mean()), 4),
        "margine_OU_BbAv_apertura": round(float((1 / A["odds_over25_open"] + 1 / A["odds_under25_open"]).dropna().mean()), 4),
        "nota": ("se footiqo riesportasse football-data, il margine coinciderebbe con "
                 "quello di uno dei book elencati; 1xBet non e' fra questi"),
    }

    # ---------- CONF-F: il dato trovato batte cio' che abbiamo gia'? ----------
    est = pd.read_csv(ROOT / "data" / "estimates" / "ou_close_2017_19.csv")
    est["home_team"] = est["home_team"].map(canon)
    est["away_team"] = est["away_team"].map(canon)
    est = est.rename(columns={"league": "lega", "season": "stagione"})
    est["stagione"] = est["stagione"].astype(str)
    F = A.merge(est[["lega", "stagione", "home_team", "away_team", "p_over25_close_est"]],
                on=["lega", "stagione", "home_team", "away_team"], how="left")
    F = F.dropna(subset=["xbetCloseOver25", "xbetCloseUnder25",
                         "odds_over25_open", "odds_under25_open",
                         "home_goals", "away_goals"])
    is_over = ((F["home_goals"] + F["away_goals"]) > 2.5).to_numpy().astype(float)
    p_f = p_over(F["xbetCloseOver25"], F["xbetCloseUnder25"])
    p_o = p_over(F["odds_over25_open"], F["odds_under25_open"])

    def ll(p):
        p = np.clip(np.asarray(p, float), 1e-12, 1 - 1e-12)
        return -(is_over * np.log(p) + (1 - is_over) * np.log(1 - p))

    d1 = boot(ll(p_f) - ll(p_o), rng)
    res_f = {
        "righe": int(len(F)),
        "logloss_chiusura_footiqo": round(float(ll(p_f).mean()), 4),
        "logloss_apertura_reale_BbAv": round(float(ll(p_o).mean()), 4),
        "brier_chiusura_footiqo": round(metrics.brier_binary(p_f, is_over), 4),
        "brier_apertura_reale_BbAv": round(metrics.brier_binary(p_o, is_over), 4),
        "delta_logloss_footiqo_meno_apertura": {
            "media": round(d1[0], 5), "ci95": [round(d1[1], 5), round(d1[2], 5)],
            "P(delta<0)": round(d1[3], 4), "conclusivo": bool(d1[1] * d1[2] > 0)},
    }
    sub = F.dropna(subset=["p_over25_close_est"])
    if len(sub):
        m = F["p_over25_close_est"].notna().to_numpy()
        pe = np.clip(F.loc[m, "p_over25_close_est"].to_numpy(), 1e-12, 1 - 1e-12)
        io = is_over[m]
        lle = -(io * np.log(pe) + (1 - io) * np.log(1 - pe))
        llf = ll(p_f)[m]
        llo = ll(p_o)[m]
        d2 = boot(llf - lle, rng)
        res_f["confronto_con_la_STIMA_E3"] = {
            "righe_con_stima": int(m.sum()),
            "leghe": sorted(F.loc[m, "lega"].unique().tolist()),
            "logloss_stima_E3": round(float(lle.mean()), 4),
            "logloss_chiusura_footiqo": round(float(llf.mean()), 4),
            "logloss_apertura_reale": round(float(llo.mean()), 4),
            "delta_logloss_footiqo_meno_stima": {
                "media": round(d2[0], 5), "ci95": [round(d2[1], 5), round(d2[2], 5)],
                "P(delta<0)": round(d2[3], 4), "conclusivo": bool(d2[1] * d2[2] > 0)},
            "MAE_prob_footiqo_vs_stima": round(float(np.abs(p_f[m] - pe).mean()), 4),
            "corr_prob_footiqo_vs_stima": round(float(np.corrcoef(p_f[m], pe)[0, 1]), 4),
        }
    out["CONF_F_utilita_pratica"] = res_f

    print(json.dumps(out, ensure_ascii=False, indent=1))
    (RIC / "confutazione_footiqo.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
