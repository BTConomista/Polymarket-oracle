"""I coefficienti UEFA: le identita' del file e le trappole del suo uso.

Consegna del 13/08/2026. Il valore non e' il ranking in se': e' il **paese** dei
club che il nostro dataset non ha (vedi `docs/CLUB_FUORI_PERIMETRO.md`).
"""
from __future__ import annotations

import pandas as pd
import pytest

from src.data import ranking_uefa as ru


@pytest.mark.parametrize("finestra", ["2025-26", "2026-27"])
def test_il_coefficiente_di_federazione_e_la_somma_delle_cinque_stagioni(finestra):
    """L'identita' dichiarata nel foglio `Note`, verificata sul dato."""
    f = ru.federazioni(finestra)
    stagioni = [c for c in f.columns if "/" in str(c)]
    assert len(stagioni) == 5, stagioni
    scarti = (abs(f[stagioni].sum(axis=1) - f["Punti"]) >= 0.01).sum()
    assert scarti == 0, f"{scarti} federazioni dove la somma non fa Punti"
    assert len(f) == 55


def test_la_finestra_va_scelta_e_non_ha_un_default():
    """⚠️ R8 in forma di firma di funzione.

    Il file contiene DUE finestre — 21/22-25/26 e 22/23-26/27 — che decidono
    due access list diverse. Sceglierne una di nascosto vorrebbe dire usare un
    coefficiente di oggi per una partita di ieri: look-ahead, perche' quel
    numero incorpora il risultato che si sta cercando di prevedere.
    """
    with pytest.raises(TypeError):
        ru.federazioni()                      # nessun default: e' voluto
    with pytest.raises(ValueError):
        ru.federazioni("2024-25")             # finestra che il file non contiene


def test_il_coefficiente_di_club_non_e_la_somma_ma_il_massimo_col_pavimento():
    """`MAX(somma 5 stagioni; 20% del coefficiente della federazione)`.

    E il pavimento non e' un dettaglio: morde su 146 club su 410. Per quelli il
    numero pubblicato misura il PAESE, non la squadra — leggerlo come «forza di
    questo club» mette alla pari tutti i club della stessa federazione.
    """
    c = ru.club()
    atteso = pd.concat([c["Somma stagioni"], c["Quota federazione (20%)"]], axis=1).max(axis=1)
    assert (abs(c["Coefficiente UEFA"] - atteso) < 1e-3).all()
    assert int(ru.pavimento_attivo().sum()) == 146
    assert len(c) == 410


def test_nessun_club_id_riceve_due_paesi_diversi():
    """L'invariante che ha trovato l'omonimo, e che nessun conteggio vede.

    Due righe del ranking — due club, due federazioni — sullo stesso `club_id`
    vogliono dire che almeno uno dei due agganci e' falso. Non guarda le
    stringhe: e' proprio la somiglianza dei nomi a essere il problema.
    """
    conflitti = ru.controlla_un_club_un_paese()
    assert conflitti.empty, conflitti[["Club", "Paese", "club_id"]].to_string(index=False)


def test_bohemians_irlandese_non_e_il_bohemians_ceco():
    """Il caso trovato dall'invariante, con i due numeri.

    `Agganciatore.aggancia("Bohemians")` da' **715**, che e' Bohemians Praha
    1905 (ceco, 60 partite di TS1 in `games.csv`). Ma nel ranking «Bohemians»
    con `Paese = Republic of Ireland` e' il club irlandese, che nel registro
    esiste col nome per esteso: «Bohemian Football Club» (9211).

    La riparazione usa il **paese**, che questa fonte porta: e' il caso in cui
    un dato in piu' non aggiunge rumore ma toglie un errore.
    """
    d = ru.con_club_id()
    irl = d[(d["Club"] == "Bohemians") & (d["Paese"] == "Republic of Ireland")]
    assert len(irl) == 1
    assert int(irl["club_id"].iloc[0]) == 9211
    cec = d[d["Club"] == "Bohemians Praha"]
    assert int(cec["club_id"].iloc[0]) == 715


def test_il_ranking_da_il_paese_ai_club_che_il_dataset_non_sa_collocare():
    """Il motivo per cui questa fonte e' stata presa, in un numero.

    Nel dataset player-scores nessuna colonna dice di che paese e' un club:
    c'e' solo `domestic_competition_id`, pieno al 25,1%. Il ranking porta il
    paese per 331 club agganciati, e la meta' abbondante di questi non ha un
    campionato domestico — sono esattamente quelli su cui il dataset taceva.
    """
    from pathlib import Path
    reg = pd.read_csv(Path("files/player_scores/club_names.csv.gz"))
    con_lega = {int(c) for c, l in zip(reg["club_id"], reg["domestic_competition_id"])
                if isinstance(l, str)}
    paesi = ru.paese_dei_club()
    assert len(paesi) >= 300
    scoperti = [c for c in paesi if c not in con_lega]
    assert len(scoperti) > 150, f"solo {len(scoperti)} club nuovi coperti"


def test_i_non_agganciati_sono_le_abbreviazioni_dei_club_GRANDI():
    """⚠️ Il tasso di aggancio va letto sapendo CHI resta fuori.

    331/410 sembra un buco dell'81%; ma i 79 fuori sono in gran parte le forme
    abbreviate della UEFA per i club maggiori («Atleti», «B. Dortmund»,
    «Bayern München»), che sono gia' nei nostri cinque campionati. Il valore di
    questa fonte sta nella coda, non in testa: aggiungere alias per quelli non
    aggiungerebbe nessuna informazione che non abbiamo.
    """
    d = ru.con_club_id()
    fuori = set(d[~d["stato_aggancio"].astype(str).str.startswith("univoco")]["Club"])
    assert {"Atleti", "B. Dortmund", "Bayern München"} <= fuori
