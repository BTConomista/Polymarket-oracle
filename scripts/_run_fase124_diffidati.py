"""Il diffidato si trattiene? Studio within-player sui cartellini (Fase 124).

LA DOMANDA (utente): «se abbiamo il calendario della squadra e quando ogni
giocatore ha preso i cartellini, possiamo fare un backtest o uno studio per
vedere correlazioni e simili».

L'ipotesi piu' netta che questi dati possono falsificare e' quella nata alla
Fase 123: **un giocatore a una ammonizione dalla squalifica gioca piu'
prudente**. Se e' vero, si vede come una caduta della probabilita' di prendere
il giallo proprio nello stato "diffidato".

⚠️ IL DISEGNO E' LA PARTE DIFFICILE, NON IL CONTO.
Un confronto ingenuo "diffidati contro non diffidati" e' **garantito** a dare un
falso positivo di segno OPPOSTO: per arrivare a 4 gialli bisogna essere un
giocatore che i gialli li prende: lo stato "diffidato" seleziona i falciatori.
Il confronto va quindi fatto **dentro lo stesso giocatore** (ogni giocatore fa
da controllo di se stesso), e l'incertezza va calcolata con un bootstrap
**a grappolo sul giocatore**, non sulle singole partite: le presenze dello
stesso giocatore non sono osservazioni indipendenti.

⚠️ LA SOGLIA NON E' 5 DAPPERTUTTO. In Ligue 1 e' passata da 3 a 5 solo nel
2025-26 (Fase 123): fino al 2024-25 li' "diffidato" vuol dire **2** gialli, non
4. Applicare 5 a tutti mescolerebbe stati diversi in entrambi i gruppi.

USO:
    python scripts/_run_fase124_diffidati.py
    python scripts/_run_fase124_diffidati.py --min-minuti 60
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

KAGGLE = "davidcariboo/player-scores"
LEGHE = {"IT1": "serie_a", "GB1": "premier_league", "ES1": "la_liga",
         "L1": "bundesliga", "FR1": "ligue_1"}
DEST = ROOT / "experiments" / "fase124_diffidati.json"


def prima_soglia(lega: str, stagione: int) -> int:
    """La prima soglia di squalifica, che dipende da lega **e stagione**."""
    if lega == "ligue_1" and stagione < 2025:
        return 3          # la regola semplificata e' del 2025-26 (Fase 123)
    return 5


def carica() -> pd.DataFrame:
    import kagglehub
    base = Path(kagglehub.dataset_download(KAGGLE))
    ap = pd.read_csv(base / "appearances.csv",
                     usecols=["player_id", "player_name", "date", "competition_id",
                              "yellow_cards", "red_cards", "minutes_played"])
    ap["date"] = pd.to_datetime(ap["date"], errors="coerce")
    ap = ap[ap.competition_id.isin(LEGHE)].dropna(subset=["date"]).copy()
    ap["lega"] = ap.competition_id.map(LEGHE)
    # stagione europea: da luglio a giugno
    ap["stagione"] = np.where(ap.date.dt.month >= 7, ap.date.dt.year, ap.date.dt.year - 1)

    # Cartellini accumulati PRIMA della partita: nessun look-ahead. Il conteggio
    # e' per (giocatore, competizione, stagione), perche' i gialli non si
    # sommano fra competizioni ne' fra stagioni.
    ap = ap.sort_values(["player_id", "competition_id", "stagione", "date"])
    cum = ap.groupby(["player_id", "competition_id", "stagione"])["yellow_cards"].cumsum()
    ap["gialli_prima"] = cum - ap.yellow_cards
    ap["ammonito"] = (ap.yellow_cards > 0).astype(int)
    ap["soglia"] = [prima_soglia(l, s) for l, s in zip(ap.lega, ap.stagione)]
    ap["diffidato"] = ap.gialli_prima == ap.soglia - 1
    ap["controllo"] = ap.gialli_prima < ap.soglia - 1
    return ap


def confronto_within(df: pd.DataFrame) -> dict:
    """Differenza di tasso diffidato-vs-controllo, DENTRO ogni giocatore."""
    usabili = df[df.diffidato | df.controllo]
    per = usabili.groupby(["player_id", "diffidato"])["ammonito"].agg(["mean", "size"])
    per = per.unstack("diffidato")
    per.columns = ["tasso_ctrl", "tasso_diff", "n_ctrl", "n_diff"]
    per = per.dropna()                      # solo chi ha vissuto ENTRAMBI gli stati
    per["delta"] = per.tasso_diff - per.tasso_ctrl
    return {"per_giocatore": per, "n_giocatori": len(per)}


def bootstrap_grappolo(per: pd.DataFrame, n: int = 5000, seme: int = 12345) -> tuple:
    """IC95% ricampionando i GIOCATORI, non le partite.

    Le presenze dello stesso giocatore sono correlate: un bootstrap sulle righe
    darebbe un intervallo troppo stretto e una conclusione troppo sicura (R7).
    """
    rng = np.random.default_rng(seme)
    d = per["delta"].to_numpy()
    peso = per["n_diff"].to_numpy(float)
    stime = np.empty(n)
    idx = np.arange(len(d))
    for i in range(n):
        c = rng.choice(idx, size=len(idx), replace=True)
        stime[i] = np.average(d[c], weights=peso[c])
    punt = float(np.average(d, weights=peso))
    return punt, float(np.percentile(stime, 2.5)), float(np.percentile(stime, 97.5))


def gradino_alla_soglia(df: pd.DataFrame, n_boot: int = 1000,
                        seme: int = 7) -> dict:
    """L'effetto e' un GRADINO alla soglia, o una discesa liscia?

    E' la domanda che decide se il risultato e' comportamento o artefatto.
    Lo stato "diffidato" arriva per forza **piu' tardi** nella stagione (per
    avere 4 gialli bisogna averne presi 4): se il tasso di ammonizione calasse
    da solo col passare delle giornate, vedremmo lo stesso effetto senza che
    nessuno si trattenga.

    Il test che separa le due spiegazioni: confrontare lo stato a soglia-1
    **solo con i due stati confinanti** (uno prima, uno dopo). Una tendenza
    liscia da' zero; un gradino sopravvive.
    """
    sub = df[(df.lega != "ligue_1") & df.gialli_prima.between(3, 5)].copy()
    sub["res"] = sub.ammonito - sub.groupby("player_id").ammonito.transform("mean")
    r = sub.res.to_numpy(); l = sub.gialli_prima.to_numpy(); g = sub.player_id.to_numpy()
    punt = r[l == 4].mean() - r[l != 4].mean()
    unici = np.unique(g)
    ip = {x: np.where(g == x)[0] for x in unici}
    rng = np.random.default_rng(seme)
    st = []
    for _ in range(n_boot):
        sc = rng.choice(unici, size=len(unici), replace=True)
        rr = np.concatenate([ip[x] for x in sc])
        a, b = r[rr], l[rr]
        st.append(a[b == 4].mean() - a[b != 4].mean())
    lo, hi = np.percentile(st, [2.5, 97.5])
    base = float(sub.ammonito.mean())
    return {"gradino": float(punt), "ic95": [float(lo), float(hi)],
            "tasso_base": base, "riduzione_relativa": float(punt / base),
            "n_presenze": int(len(sub)), "n_giocatori": int(len(unici))}


def effetto_per_fase_stagione(df: pd.DataFrame, n_boot: int = 800,
                              seme: int = 23) -> dict:
    """Il gradino si attenua a fine stagione, quando la squalifica costa meno?

    ⚠️ La differenza si TESTA, non si deduce da intervalli che si sovrappongono
    (regola R7): due IC sovrapposti non dimostrano assenza di differenza.
    """
    sub = df[(df.lega != "ligue_1") & df.gialli_prima.between(3, 5)].copy()
    sub["prog"] = sub.groupby(["lega", "stagione"])["date"].transform(
        lambda s: s.rank(pct=True))
    sub["res"] = sub.ammonito - sub.groupby("player_id").ammonito.transform("mean")
    sub["fase"] = np.where(sub.prog < .333, "inizio",
                           np.where(sub.prog < .666, "meta", "fine"))
    r = sub.res.to_numpy(); l = sub.gialli_prima.to_numpy()
    f = sub.fase.to_numpy(); g = sub.player_id.to_numpy()

    def grad(m):
        a, b = r[m], l[m]
        return float(a[b == 4].mean() - a[b != 4].mean())

    per_fase = {x: grad(f == x) for x in ("inizio", "meta", "fine")}
    unici = np.unique(g); ip = {x: np.where(g == x)[0] for x in unici}
    rng = np.random.default_rng(seme); st = []
    for _ in range(n_boot):
        sc = rng.choice(unici, size=len(unici), replace=True)
        rr = np.concatenate([ip[x] for x in sc])
        a, b, c = r[rr], l[rr], f[rr]
        gi = a[(c == "inizio") & (b == 4)].mean() - a[(c == "inizio") & (b != 4)].mean()
        gf = a[(c == "fine") & (b == 4)].mean() - a[(c == "fine") & (b != 4)].mean()
        st.append(gi - gf)
    lo, hi = np.percentile(st, [2.5, 97.5])
    medio = grad(np.ones(len(r), bool))
    return {"per_fase": per_fase,
            "differenza_inizio_meno_fine": per_fase["inizio"] - per_fase["fine"],
            "ic95_differenza": [float(lo), float(hi)],
            "conclusiva": bool(lo > 0 or hi < 0),
            "potenza": {
                "larghezza_ic": float(hi - lo),
                "rapporto_su_effetto_medio": float((hi - lo) / abs(medio)),
                "lettura": ("l'IC sulla differenza e' piu' largo dell'effetto "
                            "stesso: un'attenuazione anche del 50% resterebbe "
                            "dentro il rumore. Questo test NON puo' vederla.")}}


def main(argv=None) -> None:
    ap_ = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap_.add_argument("--min-minuti", type=int, default=0,
                     help="tieni solo le presenze con almeno N minuti")
    a = ap_.parse_args(argv)

    df = carica()
    if a.min_minuti:
        df = df[df.minutes_played >= a.min_minuti]
    print(f"presenze: {len(df):,} | stagioni {df.stagione.min()}-{df.stagione.max()} "
          f"| gialli {int(df.yellow_cards.sum()):,}")

    grezzo_d = df[df.diffidato].ammonito.mean()
    grezzo_c = df[df.controllo].ammonito.mean()
    print(f"\n1) CONFRONTO INGENUO (fra giocatori diversi) — da NON credere")
    print(f"   diffidati  {grezzo_d:.4f}  (n={int(df.diffidato.sum()):,})")
    print(f"   controllo  {grezzo_c:.4f}  (n={int(df.controllo.sum()):,})")
    print(f"   differenza {grezzo_d - grezzo_c:+.4f}  <-- gonfiata dalla selezione:"
          f" per essere diffidato devi prendere cartellini")

    ris = confronto_within(df)
    per = ris["per_giocatore"]
    punt, lo, hi = bootstrap_grappolo(per)
    print(f"\n2) CONFRONTO WITHIN-PLAYER (ogni giocatore controlla se stesso)")
    print(f"   giocatori con entrambi gli stati: {ris['n_giocatori']:,}")
    print(f"   presenze da diffidato: {int(per.n_diff.sum()):,} | "
          f"di controllo: {int(per.n_ctrl.sum()):,}")
    print(f"   Δ tasso di ammonizione = {punt:+.4f}  IC95% [{lo:+.4f}, {hi:+.4f}]")
    concl = ("SI TRATTIENE" if hi < 0 else
             "PRENDE PIU' CARTELLINI" if lo > 0 else "NESSUN EFFETTO CONCLUSIVO")
    print(f"   -> {concl}")

    print(f"\n3) PER LEGA (stesso stimatore, campioni piu' piccoli)")
    per_lega = {}
    for lega, sub in df.groupby("lega"):
        r = confronto_within(sub)
        if r["n_giocatori"] < 50:
            print(f"   {lega:15s} troppo pochi giocatori ({r['n_giocatori']})")
            continue
        p, l, h = bootstrap_grappolo(r["per_giocatore"], n=2000)
        segno = "▼" if h < 0 else ("▲" if l > 0 else "·")
        print(f"   {lega:15s} {p:+.4f}  IC95% [{l:+.4f}, {h:+.4f}]  {segno}  "
              f"(n={r['n_giocatori']} giocatori)")
        per_lega[lega] = {"delta": p, "ic95": [l, h], "n_giocatori": r["n_giocatori"]}

    # Il manager risponde? Un diffidato potrebbe essere sostituito prima.
    m_d = df[df.diffidato].minutes_played.mean()
    m_c = df[df.controllo].minutes_played.mean()
    print(f"\n4) CONTROLLO: i minuti cambiano? (un diffidato potrebbe uscire prima)")
    print(f"   minuti medi da diffidato {m_d:.1f} | di controllo {m_c:.1f} "
          f"| Δ {m_d - m_c:+.1f}")

    grad = gradino_alla_soglia(df)
    print(f"\n5) E' UN GRADINO O UNA DISCESA LISCIA? (soglia-1 contro i due stati confinanti)")
    print(f"   gradino = {grad['gradino']:+.4f}  IC95% [{grad['ic95'][0]:+.4f}, "
          f"{grad['ic95'][1]:+.4f}]  su base {grad['tasso_base']:.4f}")
    print(f"   -> riduzione relativa {grad['riduzione_relativa']:+.1%}, "
          f"{'CONCLUSIVA' if grad['ic95'][1] < 0 else 'non conclusiva'}")

    fasi = effetto_per_fase_stagione(df)
    print(f"\n6) SI ATTENUA A FINE STAGIONE? (la domanda sul timing)")
    for k, v in fasi["per_fase"].items():
        print(f"   {k:8s} {v:+.4f}")
    print(f"   differenza inizio-fine = {fasi['differenza_inizio_meno_fine']:+.4f}  "
          f"IC95% [{fasi['ic95_differenza'][0]:+.4f}, {fasi['ic95_differenza'][1]:+.4f}]")
    print(f"   -> {'conclusiva' if fasi['conclusiva'] else 'NON conclusiva'}; "
          f"{fasi['potenza']['lettura']}")

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps({
        "fase": 124,
        "domanda": "un giocatore a una ammonizione dalla squalifica si trattiene?",
        "disegno": ("within-player: ogni giocatore fa da controllo di se stesso; "
                    "bootstrap a grappolo sul giocatore"),
        "presenze": int(len(df)),
        "min_minuti": a.min_minuti,
        "ingenuo": {"diffidati": float(grezzo_d), "controllo": float(grezzo_c),
                    "differenza": float(grezzo_d - grezzo_c),
                    "avvertenza": "confuso dalla selezione, NON usare"},
        "within_player": {"delta": punt, "ic95": [lo, hi],
                          "n_giocatori": int(ris["n_giocatori"]),
                          "n_presenze_diffidato": int(per.n_diff.sum())},
        "per_lega": per_lega,
        "minuti": {"diffidato": float(m_d), "controllo": float(m_c)},
        "gradino_alla_soglia": grad,
        "per_fase_stagione": fasi,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nscritto {DEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
