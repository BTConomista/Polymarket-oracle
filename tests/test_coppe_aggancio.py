"""Test dell'appaiamento condiviso fra le due fonti di coppa.

PERCHE' ESISTE. Il codice che questi test coprono nasce da un bug di
DUPLICAZIONE: la porta d'ingresso (`registra_raccolta_coppa_diretta.py`) sapeva
dedurre i club e appaiare per nome, lo script degli agganci
(`aggancia_coppe.py`) no. Stessi file, stesse due fonti, due risultati —
117/117 partite contro 77/117 sulla Copa del Rey, 161/201 contro 0/201 sulla
Coupe de France. Nessun test poteva accorgersene, perché nessuno confrontava le
due implementazioni: erano entrambe «giuste» rispetto a se stesse.

Quindi la proprietà protetta qui non è solo «l'appaiamento funziona»: è che
esista **una sola** implementazione, e che i due script chiamino quella.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.data.club_matching import Agganciatore
from src.data.coppe_aggancio import (
    appaia_partite,
    chiave_partita,
    deduci_club,
    sinonimi_squadra,
)

# Un registro finto: due club soli, così i test non dipendono da
# `club_names.csv.gz` (che cambia quando cambia il dataset a monte).
REGISTRO = pd.DataFrame({
    "club_id": [1, 2],
    "name": ["Inter Milan", "Juventus"],
})


def _ag() -> Agganciatore:
    return Agganciatore(club_names=REGISTRO)


def _manuale(righe) -> pd.DataFrame:
    return pd.DataFrame(righe, columns=["Data", "Casa", "Ospite"])


def _automatica(righe) -> pd.DataFrame:
    return pd.DataFrame(
        righe, columns=["data", "casa", "ospite", "home_club_id", "away_club_id"])


def test_deduce_il_club_quando_la_partita_lo_determina():
    """«Inter» si aggancia, e in quella data c'è UNA sola partita dell'Inter in
    casa: l'ospite è determinato, non indovinato."""
    L = _manuale([("01.01.2026", "Inter", "Squadra Ignota")])
    N = _automatica([("2026-01-01", "Inter Milan", "Chissà Chi", 1, 2)])
    assert deduci_club(L, N, _ag()) == {"Squadra Ignota": 2}


def test_non_deduce_se_lo_stesso_nome_darebbe_due_club_diversi():
    """Garanzia 2: un nome incoerente fra le sue partite viene scartato del
    tutto. Meglio nessun `club_id` che il `club_id` di un altro club."""
    L = _manuale([("01.01.2026", "Inter", "Ignota"),
                  ("02.01.2026", "Juventus", "Ignota")])
    N = _automatica([("2026-01-01", "Inter Milan", "X", 1, 2),
                     ("2026-01-02", "Juventus", "Y", 2, 1)])
    assert deduci_club(L, N, _ag()) == {}


def test_non_deduce_se_la_giornata_ha_piu_di_una_partita_candidata():
    """Garanzia 1: due partite dell'Inter in casa nello stesso giorno e
    l'ospite non è più determinato."""
    L = _manuale([("01.01.2026", "Inter", "Ignota")])
    N = _automatica([("2026-01-01", "Inter Milan", "X", 1, 2),
                     ("2026-01-01", "Inter Milan", "Y", 1, 99)])
    assert deduci_club(L, N, _ag()) == {}


def test_la_chiave_ripiega_sul_nome_quando_il_club_id_non_esiste():
    """Senza ripiego tutte le righe senza `club_id` collassano su
    «data|<NA>|<NA>» e il merge esplode in un prodotto cartesiano (201 partite
    della Coupe de France diventavano 4.804)."""
    a = chiave_partita("2026-01-01", None, None, "Cannes", "Annecy")
    b = chiave_partita("2026-01-01", None, None, "Auby", "Amiens")
    assert a != b
    # lo stesso nome scritto in due grafie deve dare la stessa chiave
    assert a == chiave_partita("2026-01-01", None, None, "cannes", "ANNECY")


def test_appaia_per_nome_dentro_la_giornata_le_forme_corta_e_lunga():
    """Il caso Coupe de France: nessun `club_id` da nessuna delle due parti, e
    i nomi differiscono per una parola intera — non per la sola sigla, che
    `normalizza` già toglie come stopword. Coppia reale della raccolta:
    «Sochaux» contro «FC Sochaux-Montbéliard»."""
    L = _manuale([("01.01.2026", "Sochaux", "Le Puy-en-Velay")])
    N = _automatica([("2026-01-01", "FC Sochaux-Montbéliard", "Le Puy Foot 43",
                      None, None)])
    app = appaia_partite(L, N, _ag())
    assert app.rimappate == 1
    assert app.k_manuale == app.k_automatica


def test_una_partita_contesa_da_due_righe_non_va_a_nessuna():
    """La regola di sempre — un aggancio incerto resta vuoto — applicata alle
    partite. L'alternativa sarebbe far vincere la prima riga del file."""
    L = _manuale([("01.01.2026", "Real Alfa", "Union Beta"),
                  ("01.01.2026", "Real Gamma", "Union Delta")])
    N = _automatica([("2026-01-01", "Real Madrid", "Union Berlin", None, None)])
    app = appaia_partite(L, N, _ag())
    assert app.rimappate == 0
    assert app.contese == 2
    assert not set(app.k_manuale) & set(app.k_automatica)


def test_i_due_script_usano_la_stessa_implementazione():
    """⭐ Il test che sarebbe servito prima: nessuno dei due script può avere
    una propria copia della risoluzione dei club o dell'appaiamento."""
    import scripts.aggancia_coppe as A
    import scripts.registra_raccolta_coppa_diretta as R

    assert A.appaia_partite is appaia_partite
    assert R.appaia_partite is appaia_partite
    for modulo in (A, R):
        assert not hasattr(modulo, "deduci_club"), modulo.__name__
        assert not hasattr(modulo, "_chiave_partita"), modulo.__name__


# --------------------------------------------------------------------------- #
# i club francesi: l'esonimo che serve, e l'omonimo che inganna (Fase 139-sexies)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("diretta, club_id, chi", [
    ("Lilla", 1082, "LOSC Lille"),
    ("Lione", 1041, "Olympique Lyon"),
    ("Marsiglia", 244, "Olympique Marseille"),
    ("Nizza", 417, "OGC Nice"),
    ("PSG", 583, "Paris Saint-Germain"),
    ("Strasburgo", 667, "RC Strasbourg Alsace"),
])
def test_esonimi_italiani_dei_club_francesi(diretta, club_id, chi):
    """diretta.it e' un sito italiano e traduce anche le citta' francesi.

    Erano l'unico buco NON strutturale della Coupe de France: sei club di
    Ligue 1 senza `club_id` perche' «Lione» e «Olympique Lyon» non hanno un
    solo token in comune. Ognuno vale 34 partite di Ligue 1 2025-26 in
    `games.csv` — la verifica indipendente, non solo il candidato unico.
    """
    assert Agganciatore().aggancia(diretta) == club_id, chi


@pytest.mark.parametrize("nome, perche", [
    ("Red Star", "Red Star FC (Ligue 2) — il registro ha solo il Belgrado"),
    ("Lusitanos", "US Lusitanos Saint-Maur (N2) — il registro ha solo l'andorrano"),
])
def test_omonimi_stranieri_restano_vuoti(nome, perche):
    """Il caso «Brest» daccapo: un nome corto che pesca un club estero.

    Non e' un mancato aggancio, e' una CERTEZZA sbagliata (R6) — e non da'
    errore a valle: attribuisce le partite di un club francese a uno serbo.
    Il club vero nel registro non c'e' affatto, quindi l'esito giusto e'
    **vuoto**, non un altro `club_id`.
    """
    assert Agganciatore().aggancia(nome) is None, perche


def test_un_omonimo_che_non_e_un_omonimo_resta_agganciato():
    """Il rovescio: «Pirae» SEMBRA lo stesso caso e non lo e'.

    AS Pirae e' tahitiano, la Coupe de France ammette le squadre d'oltremare,
    e il registro ce l'ha per il Mondiale per club 2021. Bloccarlo «per
    prudenza» toglierebbe un aggancio giusto: la prudenza si applica dopo aver
    guardato, non al posto di guardare.
    """
    assert Agganciatore().aggancia("Pirae") == 17782


# --------------------------------------------------------------------------- #
# la stessa fonte, due consegnati, due grafie dello stesso club (Fase 139-septies)
# --------------------------------------------------------------------------- #
def _p(*coppie):
    return pd.DataFrame([{"Casa": a, "Ospite": b} for a, b in coppie])


def test_sinonimo_accettato_per_sottoinsieme_di_token():
    """Il caso Copa del Rey: «Cieza» nel file di statistiche, «Ciudad Cieza»
    nella raccolta base. Stesse partite, stessi giocatori, un club solo."""
    sin = sinonimi_squadra(_p(("Ciudad Cieza", "Levante")), _p(("Cieza", "Levante")))
    assert sin == {"Cieza": "Ciudad Cieza"}


def test_nessun_sinonimo_se_i_nomi_coincidono_gia():
    assert sinonimi_squadra(_p(("Levante", "Reus")), _p(("Levante", "Reus"))) == {}


def test_un_nome_che_somiglia_a_due_non_si_sceglie():
    """La regola di sempre: dove non c'è un vincitore unico, la casella resta
    vuota. «Ourense» fra «Ourense CF» e «UD Ourense» sono club DIVERSI della
    stessa città — indovinare qui è il caso «Brest» daccapo."""
    sin = sinonimi_squadra(_p(("Ourense CF", "UD Ourense")), _p(("Ourense", "Levante")))
    assert sin == {}


def test_due_nomi_che_puntano_allo_stesso_non_si_scelgono():
    """L'unicità va pretesa nei DUE sensi: se due grafie nuove rivendicano lo
    stesso nome vecchio, una delle due è sbagliata e non si sa quale."""
    sin = sinonimi_squadra(_p(("Ciudad Cieza", "Levante")),
                           _p(("Cieza", "Ciudad"), ("Levante", "Reus")))
    assert sin == {}
