"""Test del ponte fra le statistiche diretta.it e il `player_id` delle carriere."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import player_identity as PI


def _solo_anagrafica(nomi):
    """Sostituisce la lettura di `players.csv.gz` e lascia stare le altre.

    Sostituire `pd.read_csv` in blocco intercettava anche il registro degli
    agganci manuali, che ha colonne tutte diverse: il test falliva su un
    `AttributeError` che non c'entrava niente con ciò che voleva verificare.
    """
    import contextlib

    @contextlib.contextmanager
    def _cm():
        orig = pd.read_csv

        def finto(percorso, *a, **k):
            if "players" in str(percorso):
                return nomi
            return orig(percorso, *a, **k)

        pd.read_csv = finto
        try:
            yield
        finally:
            pd.read_csv = orig
    return _cm()


def test_ordine_dei_token_irrilevante():
    """È il punto del modulo: le due fonti scrivono il nome al contrario.

    diretta.it usa «Cognome Nome», player-scores «Nome Cognome». Con una lista
    sarebbero due chiavi diverse e il ponte non esisterebbe.
    """
    assert PI.normalizza_nome("Garces Facundo") == PI.normalizza_nome("Facundo Garces")


def test_diacritici_ignorati():
    assert PI.normalizza_nome("Facundo Garcés") == PI.normalizza_nome("Garces Facundo")


def test_lettere_che_nfkd_non_decompone():
    """`ı`, `ø`, `ł` non sono lettere accentate: sono lettere a sé, e NFKD non
    le tocca. Senza la tabella esplicita, `Kenan Yıldız` non aggancia
    `Yildiz Kenan` — misurato: 4 giocatori, 101 righe."""
    assert PI.normalizza_nome("Kenan Yıldız") == PI.normalizza_nome("Yildiz Kenan")
    assert PI.normalizza_nome("Jørgen Larsen") == PI.normalizza_nome("Larsen Jorgen")
    assert PI.normalizza_nome("Łukasz Fabiański") == PI.normalizza_nome("Fabianski Lukasz")


def test_iniziali_scartate():
    assert PI.normalizza_nome("J. Smith") == frozenset({"smith"})


def test_nome_vuoto_non_genera_chiave():
    """Una chiave costruita sul vuoto aggancerebbe TUTTI i nomi vuoti fra loro."""
    assert PI.normalizza_nome(None) == frozenset()
    assert PI.normalizza_nome("  ") == frozenset()
    assert PI._chiave("2025-08-16", None) == ""
    assert PI._chiave("2025-08-16", "...") == ""


def test_chiave_include_la_data():
    """Senza la data, un omonimo di un'altra partita aggancerebbe lo stesso."""
    a = PI._chiave("2025-08-16", "Mario Rossi")
    b = PI._chiave("2025-08-17", "Mario Rossi")
    assert a and b and a != b


def test_chiavi_ambigue_non_si_agganciano():
    """Due `player_id` diversi sotto la stessa chiave: NESSUNO dei due vince.

    Sceglierne uno attribuirebbe a un giocatore la carriera di un altro — lo
    stesso errore che la verifica d'identità è servita a chiudere, rifatto qui
    a valle. Un buco dichiarato è meglio di un aggancio inventato.
    """
    app = pd.DataFrame({
        "player_id": [1, 2, 3],
        "date": pd.to_datetime(["2025-08-16", "2025-08-16", "2025-08-16"]),
    })
    nomi = pd.DataFrame({"player_id": [1, 2, 3],
                         "name": ["Mario Rossi", "Rossi Mario", "Ugo Bianchi"]})
    import src.data.careers as C
    orig = pd.read_csv
    try:
        pd.read_csv = lambda *a, **k: nomi          # noqa: ARG005
        t = PI.tabella_aggancio(app)
    finally:
        pd.read_csv = orig
    agganciati = set(t["player_id"])
    assert 3 in agganciati          # univoco: aggancia
    assert 1 not in agganciati and 2 not in agganciati   # ambiguo: nessuno dei due


@pytest.mark.parametrize("lega", ["serie_a", "premier_league", "la_liga"])
def test_aggancio_reale_sopra_il_90_percento(lega):
    """Il ponte deve reggere sui dati veri, non solo sugli esempi costruiti."""
    from src.data import player_stats as PS
    try:
        d = PS.load_player_matches(lega=lega, stagione="2526")
    except Exception:
        pytest.skip(f"raccolta {lega} non disponibile")
    if d.empty:
        pytest.skip("raccolta vuota")
    out = PI.collega(d)
    assert out["player_id"].notna().mean() > 0.90


def test_collega_non_muta_lingresso():
    """`collega` ritorna una copia: chi passa un DataFrame non se lo ritrova
    modificato sotto i piedi."""
    from src.data import player_stats as PS
    try:
        d = PS.load_player_matches(lega="serie_a", stagione="2526")
    except Exception:
        pytest.skip("raccolta non disponibile")
    colonne_prima = list(d.columns)
    PI.collega(d)
    assert list(d.columns) == colonne_prima


# ------------------------------------------ secondo e terzo passaggio

def test_eliminazione_aggancia_senza_guardare_il_nome():
    """Un solo libero per parte in quella partita: sono la stessa persona.

    È l'argomento strutturale che chiude i nomi che nessuna normalizzazione
    può chiudere, perché il nome *non è lo stesso*: `Pope Nicholas David` e
    `Nick Pope` non condividono i token giusti, ma non c'è nessun altro che
    possano essere.
    """
    app = pd.DataFrame({
        "player_id": [10, 11],
        "date": pd.to_datetime(["2025-08-16"] * 2),
        "player_club_id": [7, 7],
    })
    d = pd.DataFrame({
        "Data": ["16.08.2025", "16.08.2025"],
        "Squadra": ["Tal", "Tal"],
        "Giocatore": ["Rossi Mario", "Pope Nicholas David"],
    })
    nomi = pd.DataFrame({"player_id": [10, 11],
                         "name": ["Mario Rossi", "Nick Pope"]})
    with _solo_anagrafica(nomi):
        out = PI.collega_per_eliminazione(d, app)
    assert list(out["player_id"]) == [10, 11]


def test_eliminazione_non_inventa_se_i_liberi_sono_due():
    """Due righe libere e due candidati senza token che li separino: NESSUNO.

    Sceglierne uno attribuirebbe a un giocatore le partite di un altro.
    """
    app = pd.DataFrame({
        "player_id": [10, 11],
        "date": pd.to_datetime(["2025-08-16"] * 2),
        "player_club_id": [7, 7],
    })
    d = pd.DataFrame({
        "Data": ["16.08.2025", "16.08.2025"],
        "Squadra": ["Tal", "Tal"],
        "Giocatore": ["Sconosciuto Uno", "Sconosciuto Due"],
    })
    nomi = pd.DataFrame({"player_id": [10, 11], "name": ["Alfa Beta", "Gamma Delta"]})
    with _solo_anagrafica(nomi):
        out = PI.collega_per_eliminazione(d, app)
    assert out["player_id"].isna().all()


@pytest.mark.parametrize("lega", ["serie_a", "premier_league", "la_liga"])
def test_copertura_reale_sopra_il_99_percento(lega):
    from src.data import player_stats as PS
    try:
        d = PS.load_player_matches(lega=lega, stagione="2526")
    except Exception:
        pytest.skip(f"raccolta {lega} non disponibile")
    if d.empty:
        pytest.skip("raccolta vuota")
    out = PI.collega_per_eliminazione(d)
    assert out["player_id"].notna().mean() > 0.99


def test_omonimi_veri_restano_distinti():
    """Due persone diverse con lo stesso nome diretta NON vanno fuse.

    Al Getafe giocano due `Kiko` (Femenía 1991 e Kiko 2002); a Girona e
    Mallorca due `David López` (1989 e 2003). Se l'aggancio li collassasse su
    un `player_id` solo, attribuirebbe a uno la carriera dell'altro — e il
    conteggio delle righe non se ne accorgerebbe.
    """
    from src.data import player_stats as PS
    try:
        d = PS.load_player_matches(lega="la_liga", stagione="2526")
    except Exception:
        pytest.skip("raccolta non disponibile")
    out = PI.collega_per_eliminazione(d)
    out = out[out["player_id"].notna()]
    for nome in ("Kiko", "Lopez David"):
        sub = out[out["Giocatore"] == nome]
        if len(sub):
            assert sub["player_id"].nunique() == 2, f"{nome} collassato"


def test_registro_manuale_solo_dove_manca_laggancio():
    """Il registro R3 riempie i buchi, non sovrascrive l'automatismo.

    Una riga che sovrascrivesse un aggancio già fatto sarebbe una modifica a
    mano dei dati mascherata da eccezione — esattamente ciò che R3 vieta.
    """
    import pandas as pd
    from src.data import careers as C
    reg = C.ROOT_DATA / "aggancio_manuale.csv"
    if not reg.exists():
        pytest.skip("nessun registro manuale")
    m = pd.read_csv(reg)
    for col in ("giocatore_diretta", "squadra", "player_id", "motivo",
                "fonte", "verificato_il", "deciso_da"):
        assert col in m.columns, f"il registro deve dichiarare `{col}`"
    assert m["motivo"].str.len().min() > 40, "un motivo di una riga non è un motivo"
    assert m["fonte"].notna().all()


def test_copertura_del_ponte_su_tutte_le_raccolte():
    """La copertura del ponte, lega per lega, con le eccezioni NOMINATE.

    Era «35.339 righe su 35.339» sulle prime tre leghe. Con tutte e cinque
    (Fasi 145-146) le righe sono **54.303** e la copertura e' **54.270**.
    Le 33 righe scoperte hanno tutte una causa nominata:

    - **22** sono una partita sola, **Nantes-Tolosa del 17/05/2026**, fermata
      al 22' e omologata 0-0 — cioe' TUTTE le sue righe: nel dataset
      player-scores le presenze di una gara mai finita non ci sono;
    - **11** sono **sei giocatori** che nel dataset **non esistono affatto**
      (Bobzien e Moreno Fell del Mainz; Nduquidi del Metz; Cabral Pape,
      Nibombe e Toure del Monaco). Cercati per cognome: zero righe.

    Nessuna delle due e' un difetto del ponte: sono limiti di copertura della
    FONTE, e vanno dichiarati invece che nascosti dietro una soglia morbida —
    un `> 0.99` lascerebbe passare in silenzio anche una raccolta futura che
    ne perde duecento.
    """
    from src.data import player_stats as PS
    try:
        d = PS.load_player_matches(tutte=True)
    except Exception:
        pytest.skip("raccolte non disponibili")
    out = PI.collega_per_eliminazione(d)

    per_lega = out.groupby("lega")["player_id"].apply(lambda s: s.isna().sum())
    for lega in ("serie_a", "premier_league", "la_liga"):
        if lega in per_lega.index:
            assert per_lega[lega] == 0, f"{lega}: {per_lega[lega]} righe senza player_id"

    scoperte = out[out["player_id"].isna()]
    assert len(scoperte) == 33

    interrotta = scoperte[(scoperte["data"] == pd.Timestamp("2026-05-17"))
                          & (scoperte["Squadra"].isin(["Nantes", "Toulouse"]))]
    assert len(interrotta) == 22            # tutte le righe di quella partita
    assert set(interrotta.groupby("Squadra").size()) == {11}

    ignoti = set(scoperte.drop(interrotta.index)["Giocatore"])
    assert ignoti == {"Bobzien Ben", "Moreno Fell Fabio", "Nduquidi Joseph",
                      "Cabral Pape", "Nibombe Samuel", "Toure Ilane"}, \
        f"nuovi giocatori fuori dal ponte: {sorted(ignoti)}"
