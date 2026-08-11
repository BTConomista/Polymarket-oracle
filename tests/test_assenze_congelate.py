"""Le assenze del 2025-26 sono una colonna PIENA e VUOTA: qui e' inchiodato.

PERCHE' ESISTE QUESTO FILE (Fase 150). `home/away_absent_count_est` non ha un
solo `NaN` nel 2025-26 — come in tutte le altre otto stagioni — eppure l'83,5%
delle righe vale `0.0` contro il 7-14% storico. La fonte infortuni di
Transfermarkt e' ferma a settembre 2025 e `add_absences` scrive
`float(len(absent))`: con la lista vuota fa `0.0`, che e' indistinguibile da
«zero assenti misurato». E' il caso R6 del CLAUDE.md — il finto pieno — e
nessun controllo di completezza lo vede, perche' il dato **c'e'**.

I test qui fanno due lavori diversi:

1. **Inchiodare il difetto** finche' c'e', cosi' nessuno lo ri-scopre da capo
   e — soprattutto — nessuno usa quella colonna sul 2025-26 credendola buona.
2. **Accorgersi se sparisce.** Se un giorno il dump viene ri-scaricato con la
   fonte avanti, il primo test qui sotto diventa ROSSO. E' voluto: quel rosso
   e' il promemoria che vanno aggiornati `docs/DATI.md` §4-quater, la riga
   della tabella in §3 e questo file. Un difetto riparato in silenzio lascia
   in giro la documentazione che lo dichiara ancora.

La misura che separa «pochi infortuni» da «fonte ferma» non e' il livello, e'
la MONOTONIA: una fonte viva fa arrivare infortuni nuovi, una ferma puo' solo
farli guarire. Vedi il blocco 2 di `scripts/_run_stato_2526.py`.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

LEGHE = ["serie_a", "premier_league", "la_liga", "bundesliga", "ligue_1"]
DATA = Path(__file__).resolve().parents[1] / "data"

# Il mese da cui la fonte non registra piu' un solo infortunio nuovo.
PRIMO_MESE_CONGELATO = "2025-10"


def _passi_per_squadra(stagione: str) -> pd.DataFrame:
    """Una riga per (squadra, partita) con la variazione del conteggio assenti.

    Ogni partita da' DUE righe-squadra (casa e ospite): il conteggio di una
    squadra si segue lungo il suo calendario, non lungo quello della lega.
    """
    pezzi = []
    for lega in LEGHE:
        df = pd.read_csv(DATA / f"{lega}_matches.csv")
        df = df[df["season"].astype(str) == stagione]
        df = df.assign(date=pd.to_datetime(df["date"]))
        casa = df[["date", "home_team", "home_absent_count_est"]].rename(
            columns={"home_team": "team", "home_absent_count_est": "n"})
        fuori = df[["date", "away_team", "away_absent_count_est"]].rename(
            columns={"away_team": "team", "away_absent_count_est": "n"})
        insieme = pd.concat([casa, fuori], ignore_index=True)
        insieme["lega"] = lega
        pezzi.append(insieme)

    tutto = pd.concat(pezzi, ignore_index=True).sort_values("date")
    fuori = []
    for _, g in tutto.groupby(["lega", "team"], sort=False):
        g = g.copy()
        g["passo"] = g["n"].diff()
        fuori.append(g.dropna(subset=["passo"]))
    return pd.concat(fuori, ignore_index=True)


def test_da_ottobre_2025_nessun_infortunio_nuovo_e_registrato():
    """Zero salite = fonte congelata. E' un'implicazione ESATTA, non statistica.

    Se il dump si ferma alla data T, per t > T nessun infortunio puo' iniziare:
    l'insieme degli indisponibili puo' solo perdere elementi, quindi il passo
    e' <= 0 per costruzione. **Una sola salita falsificherebbe l'ipotesi.**

    ⚠️ Se questo test diventa rosso il dato e' stato RIPARATO (bene!): aggiorna
    `docs/DATI.md` §4-quater e la riga delle assenze in §3, che oggi dichiarano
    la colonna inutilizzabile sul 2025-26.
    """
    passi = _passi_per_squadra("2526")
    dopo = passi[passi["date"].dt.strftime("%Y-%m") >= PRIMO_MESE_CONGELATO]

    assert len(dopo) > 2000, (
        f"attesi ~2.946 passi da {PRIMO_MESE_CONGELATO} in poi, trovati {len(dopo)}"
    )
    salite = dopo[dopo["passo"] > 0]
    assert salite.empty, (
        f"{len(salite)} salite dopo {PRIMO_MESE_CONGELATO}: la fonte infortuni "
        "non e' piu' ferma. Vedi la docstring — c'e' documentazione da aggiornare."
    )


def test_il_2025_26_si_distingue_dallo_storico_per_la_monotonia_non_per_il_livello():
    """La firma e' la % di passi in salita, e le due epoche non si sovrappongono.

    Storico: 23,6% - 29,2% di salite (una fonte viva). 2025-26: 1,6%.
    Fra il minimo storico e il valore corrente c'e' piu' di un fattore 14: non
    e' una stagione fortunata, e' un'altra cosa.
    """
    quote = {}
    for stagione in ["1718", "1819", "1920", "2021", "2122", "2223", "2324",
                     "2425", "2526"]:
        passi = _passi_per_squadra(stagione)
        quote[stagione] = (passi["passo"] > 0).mean()

    storiche = [q for s, q in quote.items() if s != "2526"]
    assert min(storiche) > 0.20, (
        f"lo storico dovrebbe stare sopra il 20% di salite, minimo {min(storiche):.1%}"
    )
    assert quote["2526"] < 0.05, (
        f"il 2025-26 dovrebbe stare sotto il 5%, misurato {quote['2526']:.1%}"
    )
    assert quote["2526"] * 10 < min(storiche), (
        "il salto fra le due epoche dovrebbe essere di un ordine di grandezza"
    )


def test_la_colonna_e_piena_al_100_percento_ed_e_questo_il_problema():
    """Il finto pieno, inchiodato: zero NaN e insieme nessuna informazione.

    Serve a rendere esplicito PERCHE' il difetto e' sopravvissuto: qualunque
    controllo del tipo `notna().mean()` promuove questa colonna a piena. La
    differenza fra le due stagioni non e' nei `NaN` — sono zero in entrambe —
    ma nella quota di zeri.
    """
    for stagione, soglia_zeri in (("2425", 0.20), ("2526", 0.70)):
        pezzi = []
        for lega in LEGHE:
            df = pd.read_csv(DATA / f"{lega}_matches.csv")
            pezzi.append(df[df["season"].astype(str) == stagione])
        d = pd.concat(pezzi, ignore_index=True)

        for lato in ("home", "away"):
            col = d[f"{lato}_absent_count_est"]
            assert col.notna().all(), (
                f"{stagione}/{lato}: attesi zero NaN — e' proprio il punto"
            )
            zeri = (col == 0).mean()
            if stagione == "2425":
                assert zeri < soglia_zeri, (
                    f"2024-25 dovrebbe avere pochi zeri, misurato {zeri:.1%}"
                )
            else:
                assert zeri > soglia_zeri, (
                    f"2025-26 dovrebbe essere quasi tutto zeri, misurato {zeri:.1%}"
                )


def test_nessun_backtest_ufficiale_legge_le_assenze():
    """Il difetto e' dormiente: va tenuto tale.

    `covariates` e' `()` di default, quindi nessuna previsione pubblicata usa
    la colonna rotta. Se un giorno una covariata entrasse fra i default mentre
    le assenze sono ancora congelate, questo test lo direbbe subito.
    """
    from src.models.dixon_coles import DixonColesModel

    modello = DixonColesModel()
    assert modello.covariates == (), (
        f"covariate attive di default: {modello.covariates}. Se fra queste c'e' "
        "'absence', il 2025-26 sta entrando in un modello con una colonna vuota."
    )


@pytest.mark.parametrize("lega,partite", [
    ("serie_a", 380), ("premier_league", 380), ("la_liga", 380),
    ("bundesliga", 306), ("ligue_1", 306),
])
def test_il_2025_26_e_una_stagione_intera_su_tutte_e_cinque_le_leghe(lega, partite):
    """Il contorno del controllo: il resto della stagione e' completo.

    Senza questo, i test qui sopra potrebbero passare su una stagione monca —
    e «pochi assenti» avrebbe una spiegazione banale (poche partite).
    """
    df = pd.read_csv(DATA / f"{lega}_matches.csv")
    d = df[df["season"].astype(str) == "2526"]
    assert len(d) == partite, f"{lega}: attese {partite} partite, trovate {len(d)}"
    assert d["home_goals"].notna().all() and d["away_goals"].notna().all()
