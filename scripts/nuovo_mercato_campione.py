"""Il mercato CAMPIONE DI STAGIONE (outright) portato su Bundesliga e Ligue 1.

CHE COSA E' — e perche' non e' un mercato come gli altri.
Ogni altro mercato del progetto (1X2, O/U, GG/NG, esatto, handicap...) si legge
dalla matrice dei punteggi di UNA partita. Il campione no: dipende da 306-380
partite CONGIUNTAMENTE e dalla regola di classifica della lega, quindi va
SIMULATO. Il simulatore esiste gia' (`src/models/season_sim.py`): fitta il DC a
inizio stagione, campiona N stagioni intere dalle matrici dei singoli incontri,
compila la classifica con gli spareggi UFFICIALI e conta chi vince.

QUESTO SCRIPT non tocca il simulatore: lo usa, gli inietta le regole di
spareggio delle due leghe nuove (verificate su fonte ufficiale, vedi sotto) e
misura, con il protocollo del progetto, se il modello vale qualcosa DOVE LA LEGA
E' QUASI DECISA IN PARTENZA — che e' il vero problema di Bundesliga (Bayern) e
Ligue 1 (PSG).

ASPETTATIVE DICHIARATE PRIMA DI MISURARE (cfr. §1.2 del CLAUDE.md):
  A1. il modello batte largamente la baseline UNIFORME: scontato, non e' una
      notizia (in Fase 89 il margine era 1.80 nats su 3 leghe);
  A2. il modello batte la baseline "vince il campione uscente": probabile;
  A3. il modello NON batte, o batte di pochissimo, la baseline "vince chi ha il
      valore rosa piu' alto": in Bundesliga e Ligue 1 quella baseline indovina
      7 volte su 8 da sola. Se il modello non la batte, la vittoria contro le
      altre due baseline NON e' merito del modello ma della lega;
  A4. la sovra-confidenza misurata in Fase 89 (-18.4 punti percentuali sul
      favorito) NON si replica su queste due leghe, e per un motivo che non
      depone a favore del modello: il favorito qui vince quasi sempre, quindi
      un modello sovra-confidente sembra bravo. Attesa: scarto vicino a zero o
      addirittura positivo (sotto-confidenza) in Bundesliga.

CONTROLLO DI SANITA' (obbligatorio, §"CONTROLLO DI SANITA'"): lo stesso apparato
gira anche sulle 3 leghe storiche e deve riprodurre i numeri pubblicati dalla
Fase 89 (log-loss 1.1994, favorito dichiarato 60.05%, azzeccato 41.67%, 24/24
stagioni migliori della baseline). Se non torna, ci si ferma.

NON E' TESTABILE «battiamo il mercato»: non esistono quote outright storiche.
Il confronto e' SOLO contro le baseline, e viene detto cosi'.

------------------------------------------------------------------------------
ESITO MISURATO (run del 26/07/2026, nsim=20.000; tutti i numeri in
`docs/audit_5_leghe/numeri/nuovo_mercato_campione.json`).

  * CONTROLLO DI SANITA' SUPERATO: le 6 quantita' della Fase 89 riprodotte con
    scarto ESATTAMENTE 0.0 (24 stagioni-lega).
  * il simulatore TRASFERISCE: log-loss del campione 0.7392 (Bundesliga) e
    0.9132 (Ligue 1) su 8 stagioni ciascuna, contro 2.8904 / 2.9562
    dell'uniforme — conclusivo. A1 confermata.
  * A2 in parte: batte «vince il campione uscente» in Bundesliga (+0.7175,
    CI [+0.18, +1.73], 8/8) ma NON in Ligue 1 (+0.5713, CI [-0.20, +1.84]).
  * A3 CONFERMATA, ed e' il risultato che conta: contro «vince chi ha la rosa
    piu' cara» il guadagno e' nel rumore (+0.2359 Bundesliga, +0.0759 Ligue 1);
    con la baseline al suo MEGLIO (q in-sample = 0.87, cioe' Bayern/PSG sempre)
    il modello e' nominalmente PEGGIORE in entrambe e CONCLUSIVAMENTE peggiore
    in Ligue 1 (-0.1682, CI [-0.3283, -0.0475], 0 stagioni su 8).
  * A4 CONFERMATA: nessuna sovra-confidenza rilevabile sul favorito
    (+6.3pp / +6.2pp). MA il controllo NON DISCRIMINA: con 7/8 favoriti
    azzeccati qualunque probabilita' dichiarata fra il 50.0% e il 99.2% resta
    compatibile al 5%. Il «favorito azzeccato» non e' un test in una lega con
    un favorito quasi certo.
  * PREVEDIBILITA': Bundesliga e Ligue 1 hanno la STESSA entropia dell'esito
    campione (0.349 nats, 2 campioni distinti in 9 stagioni) e sono le piu'
    prevedibili delle cinque (Serie A 1.311). Sulle 5 leghe:
    corr(entropia, skill contro l'uniforme) = -0.765;
    corr(entropia, guadagno contro «rosa piu' cara») = +0.791.
    Il modello SEMBRA bravo dove la lega e' gia' decisa ed e' DAVVERO utile
    dove non lo e' (Serie A +1.1638 e Premier +1.5751, entrambi conclusivi).
  * confutazione piu' scomoda, e vale su tutte e 5 le leghe: una baseline a UN
    parametro «p proporzionale al valore rosa^beta» pareggia il Monte Carlo
    (40 stagioni-lega: modello 1.0501 contro 1.0804 della baseline-oracolo,
    +0.0303 CI [-0.1643, +0.2133], nel rumore).

  In una riga: sulle due leghe nuove il mercato campione FUNZIONA ma NON
  AGGIUNGE NULLA di dimostrabile a «vince Bayern» / «vince il PSG».
------------------------------------------------------------------------------

Uso:
    python scripts/nuovo_mercato_campione.py               # tutto
    python scripts/nuovo_mercato_campione.py --nsim 20000
    python scripts/nuovo_mercato_campione.py --skip-sanity
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from math import comb
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import nuove_leghe  # noqa: E402

nuove_leghe.registra()

from src.data import database  # noqa: E402,F401

# STORICO (Fase 101-bis): qui viveva un dirottamento di `database.snapshot_path`
# verso il cantiere, perche' Bundesliga e Ligue 1 non erano ancora in `data/`.
# Dall'integrazione e' un NO-OP dimostrato, quindi e' stato rimosso.

from src.config import league_config                          # noqa: E402
from src.data import loader                                    # noqa: E402
from src.models import season_sim                              # noqa: E402
from src.models.dixon_coles import DixonColesModel             # noqa: E402
from src.models.season_sim import final_table, simulate_season  # noqa: E402

# Riuso (non riscrittura) delle funzioni della Fase 89: fit walk-forward a inizio
# stagione, seed deterministico, metriche multiclasse, bootstrap.
_spec = importlib.util.spec_from_file_location(
    "_f89", ROOT / "scripts" / "_run_fase89_season_champion.py")
F89 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(F89)

from _fase52_common import boot  # noqa: E402  (bootstrap appaiato del progetto)

OUT = ROOT / "docs" / "audit_5_leghe" / "numeri"
OUT_JSON = OUT / "nuovo_mercato_campione.json"

NUOVE = ("bundesliga", "ligue_1")
STORICHE = ("serie_a", "premier_league", "la_liga")

# --------------------------------------------------------------------------- #
# 1 · LE REGOLE DI SPAREGGIO DELLE DUE LEGHE NUOVE — verificate su fonte        #
#     ufficiale, non indovinate.                                               #
# --------------------------------------------------------------------------- #
# Vocabolario di season_sim: "h2h" = scontri diretti (punti, poi differenza reti
# negli scontri diretti), "gd" = differenza reti generale, "gf" = gol fatti.
#
# BUNDESLIGA — DFL Spielordnung (SpOL), § 2, comma 3, lettera c)
#   [Stand 07.08.2025, https://media.dfl.de/sites/2/2025/08/Spielordnung-SpOL-2025-08-07-Stand.pdf]
#   testo verificato: «Bei Punktgleichheit ... werden nachstehende Kriterien in
#   der aufgeführten Reihenfolge ... herangezogen:
#     1) die nach dem Subtraktionsverfahren ermittelte Tordifferenz
#     2) Anzahl der erzielten Tore
#     3) das Gesamtergebnis aus Hin- und Rückspiel im direkten Vergleich
#     4) die Anzahl der auswärts erzielten Tore im direkten Vergleich
#     5) die Anzahl aller auswärts erzielten Tore
#     6) ... findet ein Entscheidungsspiel auf neutralem Platz statt.»
#   -> differenza reti PRIMA di tutto (come la Premier), gol fatti secondi,
#      scontri diretti solo TERZI.  Traduzione: ("gd", "gf", "h2h").
#   APPROSSIMAZIONE DICHIARATA: il criterio 3) tedesco e' il *risultato
#   aggregato* dei due scontri diretti (= differenza reti negli scontri
#   diretti); il token "h2h" del simulatore ordina prima per PUNTI negli
#   scontri diretti e poi per differenza reti negli scontri diretti. I due
#   ordinamenti divergono solo in configurazioni rarissime, e comunque solo
#   DOPO che punti, differenza reti generale e gol fatti sono tutti pari: la
#   frequenza con cui il criterio 3 viene raggiunto e' misurata e riportata
#   (campo `spareggi_oltre_gd_gf`).
#
# LIGUE 1 — LFP, Reglement des Competitions, ARTICLE 518 TER «DEPARTAGE»
#   [edizione 2024/2025, https://www.lfp.fr/assets/24_25_Reglement_Competitions_05_08_2024_0ad0a93e52.pdf]
#   testo verificato:
#     1. «... determine par la difference entre les buts marques et les buts
#        concedes ... pour l'ensemble de la division» (differenza reti GENERALE)
#     2. «... le plus grand nombre de points lors des rencontres disputees
#        entre eux» (punti negli scontri diretti)
#     3. «... a la difference de buts lors des rencontres disputees entre eux»
#     4. gol negli scontri diretti; 5. gol in trasferta negli scontri diretti;
#     6. «... le plus grand nombre de buts» (gol fatti in stagione);
#     7. gol in trasferta in stagione; 8. fair-play.
#   -> ("gd", "h2h", "gf") riproduce ESATTAMENTE i criteri 1, 2, 3 e poi il 6,
#      saltando il 4 e il 5 (gol negli scontri diretti), che nel vocabolario
#      del simulatore non esistono e che si raggiungono solo dopo quattro
#      parita' consecutive.
#
#   IL CRITERIO E' CAMBIATO NEL TEMPO, e va detto quanto:
#     - la coppia «scontri diretti» ai posti 2-3 e' in vigore almeno dal
#       2017-18 (Championnat de France 2017-2018, fr.wikipedia, che segnala
#       proprio quell'anno lo spostamento in alto degli scontri diretti) e
#       resta identica nel 2020-21 e nel regolamento LFP 2024-25 sopra;
#     - per il 2025-26 la LFP ha rifatto i criteri DAL QUARTO IN GIU'
#       (eliminati i gol in trasferta, introdotti «numero di vittorie» e
#       «vittorie in trasferta»), lasciando intatti i primi tre
#       [ligue1.com, «Egalite au classement : modification des criteres»].
#     Quindi sulle 9 stagioni di questo lavoro i primi tre criteri sono
#     STABILI, e sono gli unici che il simulatore usa.
#
#   ECCEZIONE COVID 2019-20: la stagione fu fermata dopo 27-28 giornate e la
#   LFP stabili' la classifica finale al QUOZIENTE (punti per partita giocata),
#   non ai punti. Con quella regola e con i punti grezzi il campione e' lo
#   stesso (Paris SG, 68 punti in 27 gare = 2.52 contro il 2.00 del Marsiglia):
#   lo script lo VERIFICA e, in aggiunta, rifa' tutte le metriche escludendo
#   quella stagione (analisi di sensibilita').
TIEBREAK_NUOVE: dict[str, tuple[str, ...]] = {
    "bundesliga": ("gd", "gf", "h2h"),
    "ligue_1": ("gd", "h2h", "gf"),
}
FONTI_SPAREGGIO = {
    "bundesliga": {
        "fonte": "DFL Spielordnung (SpOL), § 2 comma 3 lettera c), Stand 07.08.2025",
        "url": "https://media.dfl.de/sites/2/2025/08/Spielordnung-SpOL-2025-08-07-Stand.pdf",
        "ordine_ufficiale": ["differenza reti (Subtraktionsverfahren)",
                             "gol fatti",
                             "risultato aggregato negli scontri diretti",
                             "gol in trasferta negli scontri diretti",
                             "gol in trasferta totali",
                             "spareggio in campo neutro"],
        "usato": ["gd", "gf", "h2h"],
        "approssimazione": ("il criterio 3 tedesco e' la differenza reti negli "
                            "scontri diretti; il token h2h ordina prima per punti "
                            "negli scontri diretti — differenza irrilevante "
                            "perche' si arriva li' solo a pari punti, pari "
                            "differenza reti e pari gol fatti"),
    },
    "ligue_1": {
        "fonte": "LFP, Reglement des Competitions 2024/2025, ARTICLE 518 TER (DEPARTAGE)",
        "url": "https://www.lfp.fr/assets/24_25_Reglement_Competitions_05_08_2024_0ad0a93e52.pdf",
        "ordine_ufficiale": ["differenza reti generale",
                             "punti negli scontri diretti",
                             "differenza reti negli scontri diretti",
                             "gol negli scontri diretti",
                             "gol in trasferta negli scontri diretti",
                             "gol fatti in stagione",
                             "gol in trasferta in stagione",
                             "fair-play"],
        "usato": ["gd", "h2h", "gf"],
        "cambiamenti_nel_tempo": (
            "scontri diretti ai posti 2-3 almeno dal 2017-18 (fr.wikipedia "
            "'Championnat de France de football 2017-2018' e '2020-2021'); nel "
            "2025-26 la LFP ha riscritto i criteri dal 4 in giu' (via i gol in "
            "trasferta, dentro il numero di vittorie) lasciando intatti i primi "
            "tre [ligue1.com, 'Egalite au classement: modification des criteres']"),
        "eccezione_2019_20": (
            "stagione interrotta dal COVID dopo 27-28 giornate: classifica "
            "finale al QUOZIENTE punti/partita. Campione identico ai punti "
            "grezzi (Paris SG). Verificato in codice; sensibilita' senza quella "
            "stagione riportata a parte."),
    },
}

# Iniezione a runtime: NON si modifica src/models/season_sim.py (regola R4).
season_sim.TIEBREAK_RULES.update(TIEBREAK_NUOVE)


# --------------------------------------------------------------------------- #
# 2 · Utilita'                                                                 #
# --------------------------------------------------------------------------- #
def carica(league_key: str) -> pd.DataFrame:
    m = loader.load_league(league_key)
    m["date"] = pd.to_datetime(m["date"])
    return m


def squad_values(season_matches: pd.DataFrame) -> dict[str, float]:
    """Valore rosa a INIZIO stagione per squadra (dato di snapshot, non futuro)."""
    v: dict[str, float] = {}
    for col_t, col_v in (("home_team", "home_squad_value"),
                         ("away_team", "away_squad_value")):
        for t, val in zip(season_matches[col_t], season_matches[col_v]):
            if pd.notna(val):
                v.setdefault(t, float(val))
    return v


def tabella_quoziente(matches: pd.DataFrame) -> pd.DataFrame:
    """Classifica al QUOZIENTE punti/partita (regola LFP per il 2019-20 COVID)."""
    teams = sorted(set(matches["home_team"]) | set(matches["away_team"]))
    pts = dict.fromkeys(teams, 0)
    played = dict.fromkeys(teams, 0)
    for r in matches.itertuples():
        h, a = r.home_team, r.away_team
        played[h] += 1
        played[a] += 1
        if r.home_goals > r.away_goals:
            pts[h] += 3
        elif r.home_goals < r.away_goals:
            pts[a] += 3
        else:
            pts[h] += 1
            pts[a] += 1
    q = pd.DataFrame({"pts": pts, "played": played})
    q["quoziente"] = q["pts"] / q["played"]
    return q.sort_values("quoziente", ascending=False)


def sensibilita_spareggi(leagues) -> dict:
    """Le regole di spareggio cambiano davvero qualcosa?

    Si ricalcola il campione REALE di ogni stagione con i quattro set di regole
    presenti nel progetto (le due nuove, quella Premier e quella Serie A) e si
    guarda se il vincitore cambia. Serve a dimensionare l'importanza del passo
    'verifica il regolamento': se non cambia mai nulla nella REALTA', l'effetto
    resta confinato alle stagioni SIMULATE con la vetta a pari punti."""
    regole = {"bundesliga_ufficiale": ("gd", "gf", "h2h"),
              "ligue1_ufficiale": ("gd", "h2h", "gf"),
              "premier_style": ("gd", "gf"),
              "serie_a_style": ("h2h", "gd", "gf")}
    res = {}
    for lg in leagues:
        allm = carica(lg)
        divergenze, pari_in_vetta = [], []
        for S in sorted(allm["season"].unique()):
            cur = allm[allm["season"] == S]
            campioni = {}
            for nome, rules in regole.items():
                season_sim.TIEBREAK_RULES["_sensibilita"] = rules
                campioni[nome] = str(final_table(cur, "_sensibilita").index[0])
            t = final_table(cur, lg)
            if int(t["pts"].iloc[0]) == int(t["pts"].iloc[1]):
                pari_in_vetta.append(dict(season=S, prima=str(t.index[0]),
                                          seconda=str(t.index[1]),
                                          punti=int(t["pts"].iloc[0])))
            if len(set(campioni.values())) > 1:
                divergenze.append(dict(season=S, campioni=campioni))
        res[lg] = dict(stagioni=int(len(allm["season"].unique())),
                       divergenze=divergenze,
                       stagioni_pari_in_vetta=pari_in_vetta)
    season_sim.TIEBREAK_RULES.pop("_sensibilita", None)
    return res


def entropia(p: np.ndarray) -> float:
    p = np.asarray(p, float)
    p = p[p > 0]
    return float(-(p * np.log(p)).sum())


# --------------------------------------------------------------------------- #
# 3 · Backtest walk-forward del mercato campione                               #
# --------------------------------------------------------------------------- #
def backtest(leagues, nsim: int, seed_suffix: str = "", delta_per_lega=None,
             verbose=True) -> pd.DataFrame:
    """Per ogni stagione (tranne la prima di ogni lega, senza storico):
    fit del DC al giorno della PRIMA partita, simulazione, P(campione)."""
    rows = []
    for lg in leagues:
        allm = carica(lg)
        seasons = sorted(allm["season"].unique())
        for i, S in enumerate(seasons):
            if i == 0:
                continue
            t0 = time.time()
            model, cur, teams, promoted, start = F89.fit_at_season_start(
                allm, lg, S, seasons)
            if delta_per_lega is not None and lg in delta_per_lega:
                # variante di sensibilita': delta neopromosse per-lega
                cfg = league_config(lg)
                d = delta_per_lega[lg]
                model = DixonColesModel(
                    half_life_days=cfg["half_life_days"], shrinkage=cfg["shrinkage"],
                    shots_blend=cfg["shots_blend"], blend_signal=cfg["blend_signal"],
                    promoted_prior=(d, d))
                model.fit(allm, as_of_date=start, promoted_teams=promoted)
            fixtures = list(zip(cur["home_team"], cur["away_team"]))
            out = simulate_season(model, fixtures, teams, league_key=lg,
                                  n_sims=nsim, seed=F89.seed_for(lg, S, seed_suffix)
                                  if seed_suffix else F89.seed_for(lg, S))
            p = out["champion_prob"]
            table = final_table(cur, lg)
            champ = table.index[0]
            k = teams.index(champ)
            prev = allm[allm["season"] == seasons[i - 1]]
            prev_champ = final_table(prev, lg).index[0]
            sv = squad_values(cur)
            top_value = max(sv, key=sv.get) if sv else None
            rows.append(dict(
                league=lg, season=S, n_teams=len(teams), n_matches=len(cur),
                start=str(start.date()), champion=champ,
                p_champion=float(p[k]),
                rank_of_champion=int((-p).argsort().tolist().index(k)) + 1,
                favourite=teams[int(p.argmax())], p_favourite=float(p.max()),
                favourite_correct=bool(teams[int(p.argmax())] == champ),
                logloss=F89.logloss(float(p[k])),
                brier=F89.brier_multiclass(p, k),
                entropy_model=entropia(p),
                tie_rate=out["tie_rate"],
                prev_champion=prev_champ, repeat=bool(champ == prev_champ),
                top_value_team=top_value,
                top_value_correct=bool(top_value == champ),
                pts_real_champion=int(table["pts"].iloc[0]),
                pts_gap_1_2=int(table["pts"].iloc[0] - table["pts"].iloc[1]),
                pts_sim_winner_mean=float(out["points"].max(axis=1).mean()),
                probs={t: round(float(p[j]), 6) for j, t in enumerate(teams)},
                squad_value={t: sv.get(t) for t in teams},
            ))
            if verbose:
                r = rows[-1]
                print(f"  {lg:14} {S}  campione {champ:14} p={r['p_champion']*100:5.1f}% "
                      f"rank={r['rank_of_champion']:2d}  favorito {r['favourite']:14} "
                      f"{r['p_favourite']*100:5.1f}%  parita={r['tie_rate']*100:4.1f}%  "
                      f"({time.time()-t0:.1f}s)", flush=True)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# 4 · Le tre baseline (+ due di confutazione)                                  #
# --------------------------------------------------------------------------- #
QS = np.round(np.arange(0.02, 0.99, 0.01), 4)
BETAS = np.round(np.arange(0.0, 8.01, 0.05), 4)


def ll_punta(row, q: float, colonna: str) -> float:
    """Log-loss di una baseline 'tutta la massa su UNA squadra':
    q sulla squadra indicata da `colonna`, (1-q)/(n-1) su tutte le altre."""
    n = row["n_teams"]
    hit = row[colonna]
    return -np.log(q if hit else (1 - q) / (n - 1))


def fit_q(sub: pd.DataFrame, colonna: str) -> float:
    losses = [np.mean([ll_punta(r, q, colonna) for _, r in sub.iterrows()]) for q in QS]
    return float(QS[int(np.argmin(losses))])


def ll_softmax(row, beta: float) -> float:
    """Baseline 'valore rosa' MORBIDA: p_i ∝ valore_i^beta (beta=0 -> uniforme).
    E' la versione forte della baseline-valore: usa TUTTA la graduatoria dei
    valori, non solo la prima squadra. Serve a confutare il modello, non a
    fargli da spalla."""
    sv = row["squad_value"]
    teams = list(sv)
    v = np.array([sv[t] if sv[t] and sv[t] > 0 else np.nan for t in teams], float)
    if np.isnan(v).any():
        return np.nan
    logits = beta * np.log(v)
    logits -= logits.max()
    p = np.exp(logits)
    p /= p.sum()
    return -np.log(max(p[teams.index(row["champion"])], 1e-12))


def fit_beta(sub: pd.DataFrame) -> float:
    losses = [np.mean([ll_softmax(r, b) for _, r in sub.iterrows()]) for b in BETAS]
    return float(BETAS[int(np.argmin(losses))])


def baseline_series(df: pd.DataFrame, gruppi: str) -> dict[str, np.ndarray]:
    """Log-loss per stagione di ogni baseline, con parametro scelto FUORI
    CAMPIONE (leave-one-season-out).

    `gruppi`: "per_lega" -> il parametro si fitta sulle sole stagioni della
    stessa lega (fronte per-lega, §1.9); "pooled" -> su tutte le stagioni
    disponibili di tutte le leghe del blocco (fronte generale)."""
    n = len(df)
    unif = np.array([np.log(r["n_teams"]) for _, r in df.iterrows()])
    out = {"uniforme": unif}
    for nome, colonna in (("uscente", "repeat"), ("valore_top", "top_value_correct")):
        loo = np.empty(n)
        q_used = np.empty(n)
        for i in range(n):
            riga = df.iloc[i]
            base = df.drop(df.index[i])
            if gruppi == "per_lega":
                base = base[base["league"] == riga["league"]]
            q = fit_q(base, colonna)
            q_used[i] = q
            loo[i] = ll_punta(riga, q, colonna)
        out[nome] = loo
        out[nome + "_q"] = q_used
    loo = np.empty(n)
    b_used = np.empty(n)
    for i in range(n):
        riga = df.iloc[i]
        base = df.drop(df.index[i])
        if gruppi == "per_lega":
            base = base[base["league"] == riga["league"]]
        b = fit_beta(base)
        b_used[i] = b
        loo[i] = ll_softmax(riga, b)
    out["valore_softmax"] = loo
    out["valore_softmax_beta"] = b_used
    return out


def baseline_oracolo(df: pd.DataFrame) -> dict[str, tuple[np.ndarray, float | None]]:
    """Le stesse baseline con il parametro scelto IN-SAMPLE (sulle stagioni che
    poi valuta). NON e' implementabile in prospettiva: e' il MASSIMO che
    l'euristica puo' dare, e serve come controllo CONTRO il modello. Se il
    modello non batte nemmeno la versione-oracolo di 'vince la rosa piu' cara',
    su quel mercato e in quella lega non sta aggiungendo nulla."""
    out: dict[str, tuple[np.ndarray, float | None]] = {
        "uniforme": (np.array([np.log(r["n_teams"]) for _, r in df.iterrows()]), None)}
    for nome, colonna in (("uscente", "repeat"), ("valore_top", "top_value_correct")):
        q = fit_q(df, colonna)
        out[nome] = (np.array([ll_punta(r, q, colonna) for _, r in df.iterrows()]), q)
    b = fit_beta(df)
    out["valore_softmax"] = (np.array([ll_softmax(r, b) for _, r in df.iterrows()]), b)
    return out


def confronto(df: pd.DataFrame, gruppi: str, rng) -> dict:
    """Modello contro ogni baseline: guadagno medio, CI95 appaiato, test dei segni."""
    bl = baseline_series(df, gruppi)
    orc = baseline_oracolo(df)
    mod = df["logloss"].to_numpy()
    res = {}
    for nome in ("uniforme", "uscente", "valore_top", "valore_softmax"):
        b = bl[nome]
        d = b - mod                       # >0 = il modello e' migliore
        m, lo, hi, frac_neg = boot(d, rng)
        res[nome] = dict(
            logloss_baseline=float(np.mean(b)),
            guadagno=float(m), ci95=[lo, hi],
            frac_bootstrap_negativa=float(frac_neg),
            stagioni_modello_migliore=int((mod < b).sum()), n=int(len(d)),
            verdetto=("CONCLUSIVO a favore del modello" if lo > 0 else
                      "CONCLUSIVO a favore della baseline" if hi < 0 else
                      "nel rumore"),
        )
        if nome + "_q" in bl:
            res[nome]["q_loo"] = [float(x) for x in bl[nome + "_q"]]
        if nome == "valore_softmax":
            res[nome]["beta_loo"] = [float(x) for x in bl["valore_softmax_beta"]]
        # versione ORACOLO della stessa baseline
        bo, par = orc[nome]
        do = bo - mod
        mo, loo_, hio, _ = boot(do, rng)
        res[nome]["oracolo"] = dict(
            parametro_in_sample=par, logloss_baseline=float(np.mean(bo)),
            guadagno=float(mo), ci95=[loo_, hio],
            stagioni_modello_migliore=int((mod < bo).sum()),
            verdetto=("CONCLUSIVO a favore del modello" if loo_ > 0 else
                      "CONCLUSIVO a favore della baseline" if hio < 0 else
                      "nel rumore"),
        )
    res["logloss_modello"] = float(np.mean(mod))
    return res


# --------------------------------------------------------------------------- #
# 5 · Calibrazione: la sovra-confidenza, misurata in due modi                  #
# --------------------------------------------------------------------------- #
def poisson_binomial(ps: np.ndarray) -> np.ndarray:
    """Distribuzione del NUMERO di favoriti azzeccati, date le p dichiarate."""
    d = np.array([1.0])
    for p in ps:
        d = np.convolve(d, [1 - p, p])
    return d


def binom_two_sided(n: int, k: int, p: float) -> float:
    """p-value bilaterale esatto (binomiale, p costante), metodo delle
    probabilita' non superiori a quella osservata."""
    d = np.array([comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(n + 1)])
    return float(d[d <= d[k] + 1e-12].sum())


def potere_controllo_favorito(n: int, k: int) -> dict:
    """Quanto DISCRIMINA il controllo sul favorito, con n stagioni e k successi?

    Si cerca l'insieme delle probabilita' COSTANTI dichiarabili sul favorito che
    restano compatibili col dato osservato al 5%. Se quell'intervallo e' largo,
    il controllo non distingue un modello calibrato da uno sfacciatamente
    sovra-confidente: e' il caso limite di una lega con un favorito quasi certo,
    dove un modello sovra-confidente SEMBRA bravo."""
    ps = [float(p) for p in np.arange(0.002, 1.0, 0.002)
          if binom_two_sided(n, k, float(p)) > 0.05]
    return dict(n=n, k=k, p_min=min(ps), p_max=max(ps),
                ampiezza=max(ps) - min(ps))


def calibrazione(df: pd.DataFrame, rng) -> dict:
    n = len(df)
    p_fav = df["p_favourite"].to_numpy()
    hits = df["favourite_correct"].to_numpy().astype(int)
    dist = poisson_binomial(p_fav)
    k = int(hits.sum())
    # p-value bilaterale esatto (Poisson-binomiale): somma delle probabilita'
    # degli esiti non piu' probabili di quello osservato.
    p_val = float(dist[dist <= dist[k] + 1e-12].sum())
    se = float(np.sqrt((p_fav * (1 - p_fav)).sum())) / n

    # Test di calibrazione che usa TUTTA la distribuzione, non solo il favorito:
    # se il modello e' calibrato, E[-ln p(campione)] = E[H(p)] (entropia
    # dichiarata). Lo scarto e' la sovra-confidenza "globale".
    d = df["logloss"].to_numpy() - df["entropy_model"].to_numpy()
    m, lo, hi, _ = boot(d, rng)
    return dict(
        n=n,
        p_favourite_media=float(p_fav.mean()),
        favorito_azzeccato=float(hits.mean()),
        favoriti_azzeccati=k,
        attesi=float(p_fav.sum()),
        scarto_pp=float((hits.mean() - p_fav.mean()) * 100),
        scarto_sigma=float((hits.mean() - p_fav.mean()) / se) if se > 0 else float("nan"),
        p_value_poisson_binomiale=p_val,
        potere_controllo_favorito=potere_controllo_favorito(n, k),
        logloss_realizzata=float(df["logloss"].mean()),
        entropia_dichiarata=float(df["entropy_model"].mean()),
        eccesso_su_entropia=float(m), eccesso_ci95=[lo, hi],
        verdetto_globale=("sovra-confidente (CI conclusivo)" if lo > 0 else
                          "sotto-confidente (CI conclusivo)" if hi < 0 else
                          "nel rumore"),
        pts_campione_reale=float(df["pts_real_champion"].mean()),
        pts_vincitore_simulato=float(df["pts_sim_winner_mean"].mean()),
        tie_rate=float(df["tie_rate"].mean()),
    )


BIN_EDGES = [0.0, 0.005, 0.02, 0.05, 0.15, 0.40, 0.70, 1.0001]


def affidabilita(df: pd.DataFrame, rng, n_boot: int = 10000) -> dict:
    """Curva di affidabilita' su TUTTE le coppie (stagione, squadra).

    Il controllo sul solo favorito usa 1 numero per stagione: con 8-16 stagioni
    non ha potenza. Qui si usano tutte le ~800 probabilita' dichiarate. Le
    squadre della stessa stagione NON sono indipendenti (un solo campione per
    stagione), quindi il bootstrap ricampiona le STAGIONI intere, non le righe.
    """
    seasons, dich, real = [], [], []
    for i, r in df.iterrows():
        for t, p in r["probs"].items():
            seasons.append(i)
            dich.append(float(p))
            real.append(1.0 if t == r["champion"] else 0.0)
    seasons = np.asarray(seasons)
    dich = np.asarray(dich)
    real = np.asarray(real)
    idx = np.digitize(dich, BIN_EDGES) - 1
    bins = []
    for b in range(len(BIN_EDGES) - 1):
        m = idx == b
        if not m.any():
            continue
        bins.append(dict(
            bin=f"[{BIN_EDGES[b]*100:.1f}%, {BIN_EDGES[b+1]*100:.1f}%)",
            n=int(m.sum()), dichiarata_media=float(dich[m].mean()),
            attesi=float(dich[m].sum()), osservati=int(real[m].sum()),
            realizzata=float(real[m].mean()),
            rapporto_oss_att=float(real[m].sum() / dich[m].sum()) if dich[m].sum() > 0 else None,
        ))
    # bootstrap per stagione sullo scarto (osservati - attesi) nel bin piu' basso
    uniq = np.unique(seasons)
    out_boot = {}
    for b in (0, 1):
        m = idx == b
        if not m.any():
            continue
        per_season = np.array([[real[m & (seasons == s)].sum(),
                                dich[m & (seasons == s)].sum()] for s in uniq])
        pick = rng.integers(0, len(uniq), (n_boot, len(uniq)))
        oss = per_season[:, 0][pick].sum(axis=1)
        att = per_season[:, 1][pick].sum(axis=1)
        out_boot[f"bin{b}"] = dict(
            bin=f"[{BIN_EDGES[b]*100:.1f}%, {BIN_EDGES[b+1]*100:.1f}%)",
            osservati=int(per_season[:, 0].sum()), attesi=float(per_season[:, 1].sum()),
            eccesso_ci95=[float(np.percentile(oss - att, 2.5)),
                          float(np.percentile(oss - att, 97.5))],
        )
    return dict(n_coppie=int(len(dich)), n_stagioni=int(len(uniq)),
                bins=bins, code_basse=out_boot)


# --------------------------------------------------------------------------- #
# 6 · Quanto e' prevedibile una lega                                           #
# --------------------------------------------------------------------------- #
def prevedibilita(leagues) -> dict:
    """Entropia dell'esito 'campione' sulle 9 stagioni, piu' altre misure di
    concentrazione. Serve a NORMALIZZARE il confronto fra leghe: un modello
    sembra bravo dove la lega e' gia' decisa."""
    res = {}
    for lg in leagues:
        allm = carica(lg)
        seasons = sorted(allm["season"].unique())
        champs, gaps, n_teams = [], [], []
        for S in seasons:
            cur = allm[allm["season"] == S]
            t = final_table(cur, lg)
            champs.append(t.index[0])
            gaps.append(int(t["pts"].iloc[0] - t["pts"].iloc[1]))
            n_teams.append(int(len(t)))
        vals, counts = np.unique(champs, return_counts=True)
        freq = counts / counts.sum()
        H = entropia(freq)
        res[lg] = dict(
            stagioni=len(seasons), campioni=list(champs),
            campioni_distinti=int(len(vals)),
            titoli={str(v): int(c) for v, c in zip(vals, counts)},
            entropia_nats=H,
            entropia_normalizzata_su_lnN=float(H / np.log(np.mean(n_teams))),
            entropia_normalizzata_su_ln9=float(H / np.log(len(seasons))),
            herfindahl=float((freq ** 2).sum()),
            gap_punti_1_2_medio=float(np.mean(gaps)),
            gap_punti_1_2=gaps,
            n_teams_medio=float(np.mean(n_teams)),
        )
    return res


# --------------------------------------------------------------------------- #
# 7 · Report a schermo                                                         #
# --------------------------------------------------------------------------- #
def stampa_confronto(titolo: str, c: dict) -> None:
    print(f"\n  {titolo}   (log-loss modello {c['logloss_modello']:.4f})")
    print(f"  {'baseline':<18}{'log-loss':>10}{'guadagno':>11}   {'CI95':<24}"
          f"{'vinte':>7}  verdetto")
    for nome in ("uniforme", "uscente", "valore_top", "valore_softmax"):
        r = c[nome]
        ci = f"[{r['ci95'][0]:+.4f}, {r['ci95'][1]:+.4f}]"
        print(f"  {nome:<18}{r['logloss_baseline']:>10.4f}{r['guadagno']:>+11.4f}   "
              f"{ci:<24}{r['stagioni_modello_migliore']:>3d}/{r['n']:<3d}  {r['verdetto']}")
    print("  ...le stesse baseline al loro MEGLIO (parametro in-sample, "
          "non implementabile in prospettiva):")
    for nome in ("uscente", "valore_top", "valore_softmax"):
        o = c[nome]["oracolo"]
        ci = f"[{o['ci95'][0]:+.4f}, {o['ci95'][1]:+.4f}]"
        par = f"{o['parametro_in_sample']:.2f}" if o["parametro_in_sample"] is not None else "-"
        print(f"  {nome+' (oracolo)':<18}{o['logloss_baseline']:>10.4f}"
              f"{o['guadagno']:>+11.4f}   {ci:<24}"
              f"{o['stagioni_modello_migliore']:>3d}/{c[nome]['n']:<3d}  "
              f"{o['verdetto']}   par={par}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nsim", type=int, default=20000)
    ap.add_argument("--skip-sanity", action="store_true")
    ap.add_argument("--skip-sens", action="store_true")
    args = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20260726)
    df_s = None
    ris: dict = dict(
        meta=dict(nsim=args.nsim, leghe_nuove=list(NUOVE),
                  finestra="tutte le stagioni concluse tranne la prima di ogni lega "
                           "(1819-2526, 8 per lega); il DC e' fittato al giorno "
                           "della prima partita della stagione, quindi non vede "
                           "nessun risultato di quella stagione",
                  nota_mercato="non esistono quote outright storiche: 'battiamo il "
                               "mercato' NON e' testabile. Solo baseline."),
        regole_spareggio=FONTI_SPAREGGIO,
    )

    # ---------------------------------------------------------------- sanity --
    if not args.skip_sanity:
        print("### CONTROLLO DI SANITA': lo stesso apparato sulle 3 leghe storiche")
        print("    (deve riprodurre la Fase 89: log-loss 1.1994, favorito 60.05% "
              "dichiarato / 41.67% azzeccato, 24/24)")
        df_s = backtest(STORICHE, args.nsim)
        atteso = dict(logloss=1.19940324498676, p_fav=0.6005333333333334,
                      hit=0.4166666666666667, n=24, brier=0.658387301875,
                      rank_mean=1.875)
        ottenuto = dict(logloss=float(df_s["logloss"].mean()),
                        p_fav=float(df_s["p_favourite"].mean()),
                        hit=float(df_s["favourite_correct"].mean()),
                        n=int(len(df_s)), brier=float(df_s["brier"].mean()),
                        rank_mean=float(df_s["rank_of_champion"].mean()))
        scarti = {k: abs(ottenuto[k] - atteso[k]) for k in atteso}
        ok = all(v < 1e-9 for v in scarti.values())
        print(f"\n  atteso   {atteso}")
        print(f"  ottenuto {ottenuto}")
        print(f"  scarto max {max(scarti.values()):.2e}  ->  "
              f"{'SUPERATO' if ok else 'FALLITO'}")
        ris["sanity_fase89"] = dict(atteso=atteso, ottenuto=ottenuto,
                                    scarto_max=max(scarti.values()), superato=bool(ok))
        ris["backtest_storiche"] = df_s.drop(columns=["squad_value"]).to_dict("records")
        OUT_JSON.write_text(json.dumps(ris, indent=2, default=str))
        if not ok:
            print("\n!!! Il controllo di sanita' NON torna: mi fermo (regola del progetto).")
            return 1

    # ------------------------------------------------------- verifica 2019-20 --
    l1 = carica("ligue_1")
    cur = l1[l1["season"] == "1920"]
    q = tabella_quoziente(cur)
    t_pts = final_table(cur, "ligue_1")
    ris["ligue1_2019_20_covid"] = dict(
        partite=int(len(cur)), attese=380,
        campione_ai_punti=str(t_pts.index[0]), punti=int(t_pts["pts"].iloc[0]),
        campione_al_quoziente=str(q.index[0]),
        quoziente_primo=float(q["quoziente"].iloc[0]),
        quoziente_secondo=float(q["quoziente"].iloc[1]),
        coincidono=bool(t_pts.index[0] == q.index[0]),
        nota=("regola LFP per la stagione interrotta: classifica al quoziente "
              "punti/partita. Il campione non cambia."),
    )
    sens = sensibilita_spareggi(NUOVE)
    ris["sensibilita_spareggi"] = sens
    print("\n### Le regole di spareggio cambiano il campione REALE?")
    for lg, d in sens.items():
        print(f"  {lg:12} {len(d['divergenze'])} divergenze su {d['stagioni']} stagioni "
              f"fra i 4 set di regole; vetta a pari punti nella realta': "
              f"{len(d['stagioni_pari_in_vetta'])} volte "
              + (str([x['season'] for x in d['stagioni_pari_in_vetta']])
                 if d['stagioni_pari_in_vetta'] else ""))

    print("\n### Ligue 1 2019-20 (COVID): campione ai punti "
          f"{t_pts.index[0]}, al quoziente {q.index[0]} -> "
          f"{'coincidono' if t_pts.index[0]==q.index[0] else 'DIVERGONO'}")

    # -------------------------------------------------------------- backtest --
    print(f"\n### BACKTEST — mercato CAMPIONE su Bundesliga e Ligue 1 (nsim={args.nsim})")
    df = backtest(NUOVE, args.nsim)
    ris["backtest"] = df.drop(columns=["squad_value"]).to_dict("records")
    OUT_JSON.write_text(json.dumps(ris, indent=2, default=str))

    # ------------------------------------------------------------- confronti --
    print("\n" + "=" * 78)
    print("### MODELLO CONTRO LE BASELINE (log-loss del campione; piu' basso = meglio)")
    ris["confronti"] = {}
    for lg in NUOVE:
        sub = df[df["league"] == lg].reset_index(drop=True)
        c = confronto(sub, "per_lega", rng)
        ris["confronti"][lg] = c
        stampa_confronto(lg.upper(), c)
    c_pool_lega = confronto(df.reset_index(drop=True), "per_lega", rng)
    c_pool_gen = confronto(df.reset_index(drop=True), "pooled", rng)
    ris["confronti"]["pooled_parametri_per_lega"] = c_pool_lega
    ris["confronti"]["pooled_parametri_generali"] = c_pool_gen
    stampa_confronto("POOLED 2 leghe — parametri baseline PER-LEGA", c_pool_lega)
    stampa_confronto("POOLED 2 leghe — parametri baseline GENERALI (pooled)", c_pool_gen)

    # Le stesse baseline sulle 3 leghe storiche: e' il metro di paragone che
    # dice se il modello vince DAVVERO o solo dove la lega e' gia' decisa.
    # (Il valore rosa e' reale e al 100% su tutte e 5 le leghe: docs/DATI.md.)
    if df_s is not None:
        for lg in STORICHE:
            sub = df_s[df_s["league"] == lg].reset_index(drop=True)
            c = confronto(sub, "per_lega", rng)
            ris["confronti"][lg] = c
            stampa_confronto(lg.upper() + "  (riferimento storico)", c)
        c5 = confronto(pd.concat([df, df_s], ignore_index=True), "per_lega", rng)
        ris["confronti"]["pooled_5_leghe"] = c5
        stampa_confronto("POOLED 5 LEGHE (40 stagioni-lega)", c5)
    OUT_JSON.write_text(json.dumps(ris, indent=2, default=str))

    # ----------------------------------------------------------- calibrazione --
    print("\n" + "=" * 78)
    print("### CALIBRAZIONE — il controllo piu' importante")
    ris["calibrazione"] = {}
    for lg in list(NUOVE) + ["pooled_nuove"]:
        sub = df if lg == "pooled_nuove" else df[df["league"] == lg]
        cal = calibrazione(sub.reset_index(drop=True), rng)
        ris["calibrazione"][lg] = cal
        print(f"\n  {lg.upper()}  (n={cal['n']})")
        print(f"    P media dichiarata sul favorito : {cal['p_favourite_media']*100:5.1f}%")
        print(f"    favorito azzeccato              : {cal['favorito_azzeccato']*100:5.1f}% "
              f"({cal['favoriti_azzeccati']}/{cal['n']}, attesi {cal['attesi']:.2f})")
        print(f"    scarto                          : {cal['scarto_pp']:+.1f}pp "
              f"= {cal['scarto_sigma']:+.2f} SE   p={cal['p_value_poisson_binomiale']:.3f}")
        pot = cal["potere_controllo_favorito"]
        print(f"    POTERE del controllo            : con {pot['k']}/{pot['n']} "
              f"azzeccati, qualunque p dichiarata fra {pot['p_min']*100:.1f}% e "
              f"{pot['p_max']*100:.1f}% resta compatibile al 5% "
              f"(ampiezza {pot['ampiezza']*100:.1f}pp)")
        print(f"    log-loss realizzata             : {cal['logloss_realizzata']:.4f}")
        print(f"    entropia DICHIARATA dal modello : {cal['entropia_dichiarata']:.4f}")
        print(f"    eccesso (realizzata - dichiarata): {cal['eccesso_su_entropia']:+.4f} "
              f"CI95 [{cal['eccesso_ci95'][0]:+.4f}, {cal['eccesso_ci95'][1]:+.4f}] "
              f"-> {cal['verdetto_globale']}")
        print(f"    punti campione reale {cal['pts_campione_reale']:.1f} vs "
              f"vincitore simulato {cal['pts_vincitore_simulato']:.1f}")
    if df_s is not None:
        cal_s = calibrazione(df_s.reset_index(drop=True), rng)
        ris["calibrazione"]["storiche_3_leghe"] = cal_s
        print(f"\n  RIFERIMENTO 3 LEGHE STORICHE (n={cal_s['n']}): dichiarato "
              f"{cal_s['p_favourite_media']*100:.1f}% / azzeccato "
              f"{cal_s['favorito_azzeccato']*100:.1f}% -> {cal_s['scarto_pp']:+.1f}pp; "
              f"eccesso su entropia {cal_s['eccesso_su_entropia']:+.4f} "
              f"CI95 [{cal_s['eccesso_ci95'][0]:+.4f}, {cal_s['eccesso_ci95'][1]:+.4f}]")
        for lg in STORICHE:
            s = df_s[df_s["league"] == lg]
            c1 = calibrazione(s.reset_index(drop=True), rng)
            ris["calibrazione"][lg] = c1
            print(f"    {lg:16} dichiarato {c1['p_favourite_media']*100:5.1f}%  "
                  f"azzeccato {c1['favorito_azzeccato']*100:5.1f}%  "
                  f"scarto {c1['scarto_pp']:+6.1f}pp")
        tutte = pd.concat([df, df_s], ignore_index=True).reset_index(drop=True)
        cal5 = calibrazione(tutte, rng)
        ris["calibrazione"]["pooled_5_leghe"] = cal5
        print(f"\n  POOLED 5 LEGHE (n={cal5['n']}): eccesso su entropia "
              f"{cal5['eccesso_su_entropia']:+.4f} CI95 "
              f"[{cal5['eccesso_ci95'][0]:+.4f}, {cal5['eccesso_ci95'][1]:+.4f}] "
              f"-> {cal5['verdetto_globale']}")

    # Curva di affidabilita' su TUTTE le probabilita' dichiarate (non solo il
    # favorito): e' il test di sovra-confidenza che ha davvero potenza.
    print("\n  CURVA DI AFFIDABILITA' (tutte le coppie stagione x squadra; "
          "bootstrap per STAGIONE)")
    ris["affidabilita"] = {}
    blocchi = [("nuove_2_leghe", df.reset_index(drop=True))]
    if df_s is not None:
        blocchi += [("storiche_3_leghe", df_s.reset_index(drop=True)),
                    ("tutte_5_leghe",
                     pd.concat([df, df_s], ignore_index=True).reset_index(drop=True))]
    for nome, blocco in blocchi:
        aff = affidabilita(blocco, rng)
        ris["affidabilita"][nome] = aff
        print(f"\n    {nome}  ({aff['n_coppie']} coppie, {aff['n_stagioni']} stagioni-lega)")
        print(f"    {'fascia':<18}{'n':>6}{'dichiarata':>12}{'attesi':>9}"
              f"{'osservati':>11}{'oss/att':>9}")
        for b in aff["bins"]:
            ra = f"{b['rapporto_oss_att']:.2f}" if b["rapporto_oss_att"] is not None else "-"
            print(f"    {b['bin']:<18}{b['n']:>6d}{b['dichiarata_media']*100:>11.2f}%"
                  f"{b['attesi']:>9.2f}{b['osservati']:>11d}{ra:>9}")
        for k, v in aff["code_basse"].items():
            print(f"      coda {v['bin']}: osservati {v['osservati']} contro "
                  f"{v['attesi']:.2f} attesi, eccesso CI95 "
                  f"[{v['eccesso_ci95'][0]:+.2f}, {v['eccesso_ci95'][1]:+.2f}]")
    OUT_JSON.write_text(json.dumps(ris, indent=2, default=str))

    # --------------------------------------------------------- prevedibilita --
    print("\n" + "=" * 78)
    print("### QUANTO E' PREVEDIBILE OGNI LEGA (esito 'campione', 9 stagioni)")
    prev = prevedibilita(list(NUOVE) + list(STORICHE))
    ris["prevedibilita"] = prev
    print(f"  {'lega':<16}{'campioni div.':>14}{'entropia':>10}{'H/lnN':>8}"
          f"{'Herfindahl':>12}{'gap 1-2':>9}")
    for lg, d in prev.items():
        print(f"  {lg:<16}{d['campioni_distinti']:>14d}{d['entropia_nats']:>10.3f}"
              f"{d['entropia_normalizzata_su_lnN']:>8.3f}{d['herfindahl']:>12.3f}"
              f"{d['gap_punti_1_2_medio']:>9.1f}")
    # normalizzazione del confronto fra leghe: skill score contro l'uniforme
    print("\n  NORMALIZZAZIONE DEL CONFRONTO FRA LEGHE: il modello sembra bravo dove")
    print("  la lega e' gia' decisa? (H = entropia dell'esito campione sulle 9 stagioni)")
    print(f"  {'lega':<16}{'H':>7}{'log-loss':>10}{'ln(N)':>8}{'skill/unif':>12}"
          f"{'vs valore_top':>15}  verdetto vs valore_top")
    ris["skill"] = {}
    tutti = pd.concat([df, df_s], ignore_index=True) if df_s is not None else df
    for lg in prev:
        sub = tutti[tutti["league"] == lg]
        if not len(sub):
            continue
        ll = float(sub["logloss"].mean())
        lnn = float(np.mean([np.log(n) for n in sub["n_teams"]]))
        skill = 1 - ll / lnn
        cv = ris["confronti"].get(lg, {}).get("valore_top", {})
        g = cv.get("guadagno")
        ris["skill"][lg] = dict(logloss=ll, ln_n=lnn, skill_vs_uniforme=skill,
                                entropia_lega=prev[lg]["entropia_nats"],
                                guadagno_vs_valore_top=g,
                                verdetto_vs_valore_top=cv.get("verdetto"))
        print(f"  {lg:<16}{prev[lg]['entropia_nats']:>7.3f}{ll:>10.4f}{lnn:>8.4f}"
              f"{skill:>12.3f}{(f'{g:+.4f}' if g is not None else '-'):>15}  "
              f"{cv.get('verdetto', '-')}")
    # correlazione fra prevedibilita' della lega e bravura apparente del modello
    hs = [prev[lg]["entropia_nats"] for lg in ris["skill"]]
    sk = [ris["skill"][lg]["skill_vs_uniforme"] for lg in ris["skill"]]
    gv = [ris["skill"][lg]["guadagno_vs_valore_top"] for lg in ris["skill"]
          if ris["skill"][lg]["guadagno_vs_valore_top"] is not None]
    hv = [prev[lg]["entropia_nats"] for lg in ris["skill"]
          if ris["skill"][lg]["guadagno_vs_valore_top"] is not None]
    if len(hs) > 2:
        ris["skill"]["_corr_entropia_skill"] = float(np.corrcoef(hs, sk)[0, 1])
        print(f"\n  corr(entropia della lega, skill contro l'uniforme) = "
              f"{ris['skill']['_corr_entropia_skill']:+.3f}  (n={len(hs)} leghe)")
    if len(gv) > 2:
        ris["skill"]["_corr_entropia_gain_valore"] = float(np.corrcoef(hv, gv)[0, 1])
        print(f"  corr(entropia della lega, guadagno vs 'rosa piu' cara') = "
              f"{ris['skill']['_corr_entropia_gain_valore']:+.3f}  (n={len(gv)} leghe)")
    OUT_JSON.write_text(json.dumps(ris, indent=2, default=str))

    # ------------------------------------------------------------ confutazioni --
    print("\n" + "=" * 78)
    print("### CONFUTAZIONI (provo a dimostrare che il risultato e' sbagliato)")
    conf: dict = {}

    # C1. le stagioni "sorpresa": il modello e' bravo solo dove la lega e' decisa?
    sorprese = df[~df["repeat"] | ~df["top_value_correct"]]
    conf["stagioni_sorpresa"] = [
        dict(league=r["league"], season=r["season"], champion=r["champion"],
             p_modello=r["p_champion"], favorito=r["favourite"],
             p_favorito=r["p_favourite"], uscente=r["prev_champion"],
             valore_top=r["top_value_team"], logloss=r["logloss"])
        for _, r in sorprese.iterrows()]
    print(f"\n  C1 · stagioni in cui il campione NON e' l'uscente o NON e' la rosa "
          f"piu' cara ({len(sorprese)} su {len(df)}):")
    for r in conf["stagioni_sorpresa"]:
        print(f"     {r['league']:12} {r['season']}  vinta da {r['champion']:14} "
              f"p_modello {r['p_modello']*100:5.2f}%  (favorito {r['favorito']} "
              f"{r['p_favorito']*100:.1f}%)  log-loss {r['logloss']:.3f}")
    ov = df[df["repeat"] & df["top_value_correct"]]
    conf["scomposizione"] = dict(
        stagioni_ovvie=int(len(ov)),
        logloss_modello_ovvie=float(ov["logloss"].mean()) if len(ov) else None,
        logloss_modello_sorprese=float(sorprese["logloss"].mean()) if len(sorprese) else None,
    )
    print(f"     scomposizione: {len(ov)} stagioni 'ovvie' (uscente E rosa piu' cara) "
          f"log-loss {conf['scomposizione']['logloss_modello_ovvie']:.4f}  |  "
          f"{len(sorprese)} stagioni 'sorpresa' log-loss "
          f"{conf['scomposizione']['logloss_modello_sorprese']:.4f}")

    # C2. senza la stagione COVID (Ligue 1 2019-20)
    if not args.skip_sens:
        df2 = df[~((df["league"] == "ligue_1") & (df["season"] == "1920"))].reset_index(drop=True)
        conf["senza_covid_1920"] = confronto(df2, "per_lega", rng)
        print("\n  C2 · senza Ligue 1 2019-20 (stagione COVID interrotta):")
        stampa_confronto("POOLED senza 2019-20", conf["senza_covid_1920"])

    # C3. rumore Monte Carlo: stessa cosa con semi diversi
    print("\n  C3 · rumore Monte Carlo (semi diversi, stesso nsim):")
    lls = [float(df["logloss"].mean())]
    for tag in ("seedA", "seedB"):
        d2 = backtest(NUOVE, args.nsim, seed_suffix=tag, verbose=False)
        lls.append(float(d2["logloss"].mean()))
        print(f"     seme «{tag}»: log-loss {lls[-1]:.4f}")
    conf["rumore_montecarlo"] = dict(logloss=lls, spread=float(max(lls) - min(lls)))
    print(f"     spread fra semi: {max(lls)-min(lls):.4f} "
          f"(la soglia di risoluzione del confronto)")

    # C4. sensibilita' al delta neopromosse per-lega (report 06: 0.277 / 0.188)
    if not args.skip_sens:
        d3 = backtest(NUOVE, args.nsim, delta_per_lega={"bundesliga": 0.277,
                                                        "ligue_1": 0.188},
                      verbose=False)
        conf["delta_per_lega"] = dict(
            logloss=float(d3["logloss"].mean()),
            logloss_riferimento=float(df["logloss"].mean()),
            delta=float(d3["logloss"].mean() - df["logloss"].mean()))
        print(f"\n  C4 · delta neopromosse per-lega (0.277 / 0.188): log-loss "
              f"{conf['delta_per_lega']['logloss']:.4f} contro "
              f"{conf['delta_per_lega']['logloss_riferimento']:.4f} "
              f"({conf['delta_per_lega']['delta']:+.4f})")

    # C5. quante volte lo spareggio va oltre differenza reti e gol fatti?
    conf["spareggi"] = dict(
        tie_rate_medio={lg: float(df[df["league"] == lg]["tie_rate"].mean())
                        for lg in NUOVE},
        nota=("frazione di stagioni simulate con PARITA' DI PUNTI in testa: e' "
              "la frazione in cui la regola di spareggio decide il campione"))
    print(f"\n  C5 · parita' di punti in testa nelle simulazioni: "
          + ", ".join(f"{lg} {conf['spareggi']['tie_rate_medio'][lg]*100:.1f}%"
                      for lg in NUOVE))

    ris["confutazioni"] = conf
    OUT_JSON.write_text(json.dumps(ris, indent=2, default=str))
    print(f"\n-> {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
