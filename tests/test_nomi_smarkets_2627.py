"""Test della mappa nomi Smarkets -> nostri (Fase 128, passo P1 del test
prospettico).

Perche' esistono. Il join fra le quote e i nostri dati passa tutto da qui: un
nome che non risolve e' una partita che sparisce, e sparisce **in silenzio**
-- lo stesso guasto della Fase 127, un livello piu' in basso. Questi test
fissano per iscritto le 9 corrispondenze verificate a mano il 01/08/2026 e,
soprattutto, la **proprieta' strutturale** che le rende verificabili senza un
occhio umano: in ogni lega, entrate == uscite.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.data.sources import TEAM_ALIASES, canonical_team  # noqa: E402


# Le 9 differenze fra i nomi di Smarkets e i nostri, enumerate sulle 96
# squadre della giornata 1 delle 5 leghe.
@pytest.mark.parametrize("smarkets,canonico", [
    # Accenti: differiscono per UN carattere, e sono squadre con storia vera
    # nei nostri dati. Il confronto esatto le scarterebbe.
    ("Köln", "FC Koln"),
    ("Málaga", "Malaga"),
    # Abbreviazioni e suffissi societari.
    ("PSG", "Paris SG"),
    ("Man Utd", "Man United"),
    ("Nottm Forest", "Nott'm Forest"),
    ("Troyes AC", "Troyes"),
    # Esordienti: nome letto dai file di seconda divisione dello stesso
    # provider, non indovinato (R5).
    ("SV Elversberg", "Elversberg"),
    ("Racing Santander", "Santander"),
    ("Le Mans FC", "Le Mans"),
])
def test_i_nomi_smarkets_risolvono(smarkets, canonico):
    assert canonical_team(smarkets) == canonico


def test_psg_e_paris_fc_restano_due_squadre():
    """La trappola vera della Ligue 1: `PSG` e `Paris FC` sono esposti nella
    STESSA giornata e sono due club diversi. Un match largo su "Paris" li
    fonderebbe, e nessun conteggio se ne accorgerebbe (le squadre resterebbero
    18)."""
    assert canonical_team("PSG") == "Paris SG"
    assert canonical_team("Paris FC") == "Paris FC"
    assert canonical_team("PSG") != canonical_team("Paris FC")


def test_gli_alias_sono_idempotenti():
    """Applicare la mappa due volte deve dare lo stesso risultato: se un
    valore canonico fosse a sua volta chiave di un altro alias, il nome finale
    dipenderebbe da QUANTE volte si passa dalla funzione -- un bug che si
    manifesta solo in alcune pipeline."""
    for nome in TEAM_ALIASES.values():
        assert canonical_team(nome) == nome, f"{nome} e' a sua volta un alias"


def test_la_riconciliazione_torna_su_tutte_e_cinque_le_leghe():
    """Il controllo strutturale, sullo snapshot congelato: in ogni lega il
    numero di squadre entrate deve essere uguale a quelle uscite, e nessun
    nome deve restare da mappare.

    E' il test che protegge davvero, perche' non elenca nomi: se un giorno un
    alias venisse tolto, o Smarkets rinominasse una squadra, l'uguaglianza si
    romperebbe da sola."""
    from _run_fase128_nomi_2627 import classifica, nomi_per_lega

    snap = max((ROOT / "data" / "smarkets_matches").glob("*.json"))
    nomi = nomi_per_lega(snap)
    for lega, squadre in sorted(nomi.items()):
        e = classifica(lega, squadre)
        assert not e["da_mappare"], f"{lega}: nomi non mappati {e['da_mappare']}"
        assert len(e["neopromosse"]) == len(e["uscite_dalla_lega"]), (
            f"{lega}: {len(e['neopromosse'])} entrate contro "
            f"{len(e['uscite_dalla_lega'])} uscite")


def test_ogni_nome_mai_visto_nell_archivio_si_aggancia():
    """La guardia che si mantiene da sola.

    Fra il 30 e il 31/07/2026 Smarkets ha rinominato **40 eventi su 49** in un
    colpo (da "AS Roma vs ACF Fiorentina" a "Roma vs Fiorentina"): una
    convenzione cambiata in blocco, senza preavviso. Questo test non guarda i
    nomi di oggi ma **tutti** quelli mai comparsi nell'archivio, quindi:

      - il giorno in cui la borsa rinomina di nuovo, la suite si rompe alla
        prima esecuzione dopo la raccolta -- cioe' **prima** del calcio
        d'inizio, non durante;
      - e se tornasse alla convenzione vecchia, resta agganciata lo stesso.

    E' la seconda linea di difesa: la prima e' `event_id`, che non cambia."""
    import json

    archivio = sorted((ROOT / "data" / "smarkets_matches").glob("*.json"))
    if not archivio:                                      # pragma: no cover
        pytest.skip("archivio vuoto")

    per_lega: dict[str, set[str]] = {}
    for f in archivio:
        for r in json.loads(f.read_text(encoding="utf-8"))["righe"]:
            casa, ospite = r["partita"].split(" vs ")
            per_lega.setdefault(r["lega"], set()).update([casa, ospite])

    from _run_fase128_nomi_2627 import ESORDIENTI
    import pandas as pd

    orfani = []
    for lega, nomi in sorted(per_lega.items()):
        df = pd.read_csv(ROOT / "data" / f"{lega}_matches.csv")
        canonici = set(df.home_team) | set(df.away_team) | set(ESORDIENTI.get(lega, {}))
        orfani += [(lega, n) for n in sorted(nomi)
                   if canonical_team(n) not in canonici]
    assert not orfani, (
        f"{len(orfani)} nomi Smarkets non agganciati: {orfani}. "
        "Probabile rinominamento a monte: aggiungerli a TEAM_ALIASES SENZA "
        "togliere i vecchi (la borsa puo' tornare indietro).")


def test_le_neopromosse_2627_sono_quattordici():
    """Il numero e' un fatto misurato, non una scelta: 3 per lega tranne la
    Ligue 1 (2). Se cambiasse senza che nessuno l'abbia deciso, vuol dire che
    e' cambiato il listino o la mappa."""
    from _run_fase128_nomi_2627 import classifica, nomi_per_lega

    snap = max((ROOT / "data" / "smarkets_matches").glob("*.json"))
    nomi = nomi_per_lega(snap)
    tot = sum(len(classifica(l, s)["neopromosse"]) for l, s in nomi.items())
    assert tot == 14
