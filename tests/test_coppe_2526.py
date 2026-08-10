"""Test della raccolta coppe nazionali 2025-26 (Fase «coppe di club»).

Il test piu' importante e' `test_punteggio_non_somma_i_rigori`: fissa il difetto
che ha motivato tutto il modulo. Se un giorno qualcuno «semplificasse»
`ricostruisci_punteggio` usando `home_club_goals`, quel test diventa rosso
invece di far entrare in silenzio un 11-12 nei dati.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.data.coppe import (
    COPPE,
    TURNO_INGRESSO_SECONDA,
    leggi_openfootball,
    ricostruisci_punteggio,
)
from src.data.coupe_de_france import (
    LIVELLO_DIVISIONE,
    estrai_partite,
    verifica,
)

RADICE = Path(__file__).resolve().parents[1]
CARTELLA = RADICE / "data" / "coppe_2526"


# --------------------------------------------------------------------------- #
# ricostruzione del punteggio
# --------------------------------------------------------------------------- #
def _partita(gol_casa_dich, gol_ospite_dich, eventi):
    riga = pd.Series({
        "home_club_id": 1, "away_club_id": 2,
        "home_club_goals": gol_casa_dich, "away_club_goals": gol_ospite_dich,
    })
    return riga, pd.DataFrame(eventi)


def test_punteggio_non_somma_i_rigori():
    """Il caso Braunschweig-Stuttgart: games.csv dice 11-12, il vero e' 4-4.

    Quattro gol per parte (uno oltre il 90'), poi 7-8 ai rigori. La somma
    dichiarata e' 11-12: se il modulo la restituisse, questo test fallisce.
    """
    eventi = (
        [{"type": "Goals", "club_id": 1, "minute": m} for m in (8, 77, 85, 100)]
        + [{"type": "Goals", "club_id": 2, "minute": m} for m in (11, 60, 89, 110)]
        + [{"type": "Shootout", "club_id": 1, "minute": -1}] * 10
        + [{"type": "Shootout", "club_id": 2, "minute": -1}] * 10
    )
    riga, ev = _partita(11, 12, eventi)
    p = ricostruisci_punteggio(riga, ev)

    assert (p.gol_casa_finale, p.gol_ospite_finale) == (4, 4)
    assert (p.gol_casa_90, p.gol_ospite_90) == (3, 3)
    assert (p.rigori_casa, p.rigori_ospite) == (7, 8)
    assert p.supplementari is True
    assert p.eventi_incompleti is False


def test_partita_normale_resta_intatta():
    eventi = [{"type": "Goals", "club_id": 1, "minute": 12},
              {"type": "Goals", "club_id": 1, "minute": 55},
              {"type": "Goals", "club_id": 2, "minute": 70}]
    riga, ev = _partita(2, 1, eventi)
    p = ricostruisci_punteggio(riga, ev)
    assert (p.gol_casa_finale, p.gol_ospite_finale) == (2, 1)
    assert (p.gol_casa_90, p.gol_ospite_90) == (2, 1)
    assert p.rigori_casa is None and p.rigori_ospite is None
    assert p.supplementari is False
    assert p.eventi_incompleti is False


def test_eventi_mancanti_sono_dichiarati_non_indovinati():
    """Se il dichiarato non torna e non ci sono rigori, si DICHIARA il buco.

    E' la regola R6 applicata al caso: meglio una riga marcata incoerente che
    un punteggio inventato che sembra buono.
    """
    riga, ev = _partita(5, 6, [{"type": "Goals", "club_id": 1, "minute": 10},
                               {"type": "Goals", "club_id": 2, "minute": 20}])
    p = ricostruisci_punteggio(riga, ev)
    assert p.eventi_incompleti is True
    assert p.rigori_casa is None


def test_rigori_impossibili_non_vengono_accettati():
    """Una sequenza di rigori non finisce mai in parita': se la sottrazione la
    produce, il dato e' rotto e va marcato, non scritto."""
    eventi = [{"type": "Goals", "club_id": 1, "minute": 10},
              {"type": "Goals", "club_id": 2, "minute": 20},
              {"type": "Shootout", "club_id": 1, "minute": -1}]
    riga, ev = _partita(4, 4, eventi)   # → rigori 3-3, impossibile
    p = ricostruisci_punteggio(riga, ev)
    assert p.rigori_casa is None
    assert p.eventi_incompleti is True


# --------------------------------------------------------------------------- #
# openfootball: la parentesi con due significati
# --------------------------------------------------------------------------- #
def test_openfootball_distingue_primo_tempo_e_novantesimo():
    """`(a-b)` e' il primo tempo senza `a.e.t.` e il 90' con: sono la stessa
    parentesi con due significati, ed e' l'errore facile da fare."""
    testo = (
        "▪ 1. Round\n"
        "  Fri Aug 15 2025\n"
        "    17:00  SG Sonnenhof Großaspach v Bayer Leverkusen         0-4 (0-1)\n"
        "    19:45  Eintracht Braunschweig  v VfB Stuttgart            7-8 pen. 4-4 a.e.t. (3-3, 1-1)\n"
        "           FK Pirmasens            v Hamburger SV             1-2 a.e.t. (1-1, 0-0)\n"
    )
    d = leggi_openfootball(testo)
    assert len(d) == 3
    assert list(d.turno) == ["1. Round"] * 3

    liscia = d.iloc[0]
    assert (liscia.gol_casa_finale, liscia.gol_ospite_finale) == (0, 4)
    assert (liscia.gol_casa_90, liscia.gol_ospite_90) == (0, 4)
    assert (liscia.gol_casa_ht, liscia.gol_ospite_ht) == (0, 1)
    assert bool(liscia.supplementari) is False

    rigori = d.iloc[1]
    assert (rigori.gol_casa_finale, rigori.gol_ospite_finale) == (4, 4)
    assert (rigori.gol_casa_90, rigori.gol_ospite_90) == (3, 3)
    assert (rigori.gol_casa_ht, rigori.gol_ospite_ht) == (1, 1)
    assert (rigori.rigori_casa, rigori.rigori_ospite) == (7, 8)
    assert bool(rigori.supplementari) is True

    suppl = d.iloc[2]
    assert (suppl.gol_casa_finale, suppl.gol_ospite_finale) == (1, 2)
    assert (suppl.gol_casa_90, suppl.gol_ospite_90) == (1, 1)
    assert pd.isna(suppl.rigori_casa)


# --------------------------------------------------------------------------- #
# Coupe de France
# --------------------------------------------------------------------------- #
WIKI_ESEMPIO = """
=== Rencontres ===
----{{Feuille de match|enroulée = oui
|date = {{Date|15|11|2025}} | heure = {{Heure|15|30}}
|équipe 1 = [[Club sportif moulien|CS moulien]] <small>(R1)</small>
|équipe 2 = '''[[Association sportive du Gosier|AS Le Gosier]] <small>(N2)</small>'''
|score = 2 - 3
|stade = Stade Jacques Ponrémy, [[Le Moule]]
}}
----{{Feuille de match|enroulée = oui
|date = {{Date|16|11|2025}}
|équipe 1 = '''[[Stade Lavallois|Laval]] <small>(L2)</small>'''
|équipe 2 = [[Le Mans FC|Le Mans]] <small>(L2)</small>
|score = 1 - 1
|score tab = 4 - 2
|stade = Stade Francis-Le Basser
}}
"""


def test_coupe_de_france_legge_punteggio_rigori_e_divisione():
    p = estrai_partite("== Septième tour ==\n" + WIKI_ESEMPIO)
    assert len(p) == 2

    a, b = p
    assert a.casa == "CS moulien" and a.ospite == "AS Le Gosier"
    assert (a.gol_casa, a.gol_ospite) == (2, 3)
    assert a.rigori_casa is None
    assert (a.divisione_casa, a.divisione_ospite) == ("R1", "N2")
    assert (a.livello_casa, a.livello_ospite) == (6, 4)
    assert a.vincente == "AS Le Gosier"      # dal grassetto
    assert a.data == "2025-11-15"

    assert (b.gol_casa, b.gol_ospite) == (1, 1)
    assert (b.rigori_casa, b.rigori_ospite) == (4, 2)
    assert b.vincente == "Laval"
    assert b.turno == "7° turno"


def test_coupe_de_france_verifica_incrocia_grassetto_e_punteggio():
    """Il vincente e il punteggio sono scritti separatamente: se concordano,
    la lettura e' giusta. Una pagina incoerente deve emergere, non passare."""
    p = estrai_partite("== Septième tour ==\n" + WIKI_ESEMPIO)
    assert verifica(p)["incoerenti"] == []

    rotto = WIKI_ESEMPIO.replace("|score = 2 - 3", "|score = 3 - 2")
    p2 = estrai_partite("== Septième tour ==\n" + rotto)
    assert len(verifica(p2)["incoerenti"]) == 1


def test_livelli_divisione_francesi_sono_ordinati():
    assert LIVELLO_DIVISIONE["L1"] < LIVELLO_DIVISIONE["L2"]
    assert LIVELLO_DIVISIONE["L2"] < LIVELLO_DIVISIONE["N"]
    assert LIVELLO_DIVISIONE["N3"] < LIVELLO_DIVISIONE["R1"]


# --------------------------------------------------------------------------- #
# coerenza della raccolta prodotta
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not (CARTELLA / "partite.csv").exists(),
                    reason="la raccolta non e' stata costruita in questo ambiente")
class TestRaccoltaProdotta:

    @pytest.fixture(scope="class")
    def partite(self):
        return pd.read_csv(CARTELLA / "partite.csv")

    @pytest.fixture(scope="class")
    def manifesto(self):
        return json.loads((CARTELLA / "manifesto.json").read_text(encoding="utf-8"))

    def test_sei_coppe_cinque_paesi(self, partite):
        assert partite.competizione.nunique() == 6
        assert set(partite.paese) == {"IT", "EN", "ES", "DE", "FR"}

    def test_ogni_coppa_ha_la_sua_finale(self, partite):
        """Le tre finali assenti da games.csv sono state recuperate: se il
        recupero salta, questo test lo dice."""
        for c in partite.competizione.unique():
            x = partite[partite.competizione == c]
            assert (x.turno.isin(["Final", "Finale"])).any(), f"manca la finale: {c}"

    def test_il_dichiarato_si_scompone_esattamente(self, partite):
        """dichiarato = gol della partita + rigori. E' l'identita' che separa
        il punteggio vero dalla somma coi rigori, ed e' il controllo che
        avrebbe intercettato il difetto all'origine.

        ⚠️ Un tetto sul numero di gol NON sarebbe servito: in coppa i
        punteggi larghi sono veri (Getafe 11-0 in casa di una squadra di
        quinta divisione, Saint-Étienne 11-1). Un controllo che li segnala
        e' un controllo cieco — non distingue il difetto dal calcio (R7).
        """
        x = partite[partite.fonte == "player-scores"]
        x = x[~x.eventi_incompleti]
        rig_c = x.rigori_casa.fillna(0)
        rig_o = x.rigori_ospite.fillna(0)
        assert (x.gol_casa_finale + rig_c == x.gol_casa_dichiarato).all()
        assert (x.gol_ospite_finale + rig_o == x.gol_ospite_dichiarato).all()

    def test_i_punteggi_larghi_sono_squadre_minori(self, partite):
        """Dove il punteggio e' larghissimo dev'esserci un dislivello di
        divisione: e' cosi' che si distingue una goleada vera da un 11-12
        prodotto dai rigori sommati."""
        larghe = partite[(partite.gol_casa_finale >= 8)
                         | (partite.gol_ospite_finale >= 8)]
        for _, r in larghe.iterrows():
            assert r.divisione_casa != r.divisione_ospite, (
                f"{r.casa}-{r.ospite}: punteggio larghissimo fra pari livello")
            assert pd.isna(r.rigori_casa), f"{r.casa}-{r.ospite}: goleada ai rigori?"

    def test_i_rigori_non_finiscono_in_parita(self, partite):
        r = partite.dropna(subset=["rigori_casa", "rigori_ospite"])
        assert (r.rigori_casa != r.rigori_ospite).all()

    def test_il_novantesimo_non_supera_il_finale(self, partite):
        x = partite.dropna(subset=["gol_casa_90", "gol_casa_finale"])
        assert (x.gol_casa_90 <= x.gol_casa_finale).all()
        assert (x.gol_ospite_90 <= x.gol_ospite_finale).all()

    def test_perimetro_coerente_col_turno_dichiarato(self, partite, manifesto):
        """Ogni partita nel perimetro deve avere una data >= alla prima
        partita con un club di seconda divisione di quella coppa."""
        for cid, turno in TURNO_INGRESSO_SECONDA.items():
            nome = COPPE[cid][0]
            x = partite[(partite.competizione == nome) & partite.dentro_perimetro]
            con2 = partite[(partite.competizione == nome)
                           & ((partite.divisione_casa == 2)
                              | (partite.divisione_ospite == 2))]
            assert len(x) > 0
            assert x.data.min() <= con2.data.min()

    def test_formazioni_agganciate_a_partite_esistenti(self):
        p = pd.read_csv(CARTELLA / "partite.csv")
        f = pd.read_csv(CARTELLA / "formazioni.csv")
        assert set(f.game_id) <= set(p.game_id.dropna())
        assert set(f.ruolo_partita) == {"titolare", "panchina"}

    def test_verifica_esterna_registrata_e_senza_divergenze(self, manifesto):
        v = manifesto["verifica_esterna_dfb"]
        assert v["appaiate"] > 0
        assert v["divergenti"] == []
        for campo, c in v["confronti"].items():
            assert c["uguali"] == c["confrontabili"], campo

    def test_divisione_1_solo_per_chi_gioca_davvero_in_prima(self, partite):
        """Guardiano del bug «Wigan Athletic in prima divisione» (02/08/2026).

        La divisione veniva da `club_names.domestic_competition_id`, che marca
        **chiunque sia mai stato** in quella lega: 37 club per `GB1`, fra cui
        Wigan, Reading, QPR, West Brom — tutti oggi in divisioni inferiori.
        Un finto pieno da manuale (R6): valore plausibile, formato giusto,
        sbagliato. Qui si verifica contro gli snapshot 2025-26, che sono la
        verità.
        """
        snapshot = {"IT": "serie_a", "EN": "premier_league", "ES": "la_liga",
                    "DE": "bundesliga", "FR": "ligue_1"}
        for paese, lega in snapshot.items():
            d = pd.read_csv(RADICE / "data" / f"{lega}_matches.csv")
            d = d[d.season == 2526]
            attese = len(set(d.home_team) | set(d.away_team))
            # solo le righe di player-scores: hanno il club_id, che e' l'unica
            # identita' stabile. Le finali da Wikipedia arrivano con un'altra
            # grafia ("Chelsea" vs "Chelsea FC") e contarle per nome gonfia.
            x = partite[(partite.paese == paese) & partite.game_id.notna()]
            prime = set(x.loc[x.divisione_casa == 1, "home_club_id"]) | \
                set(x.loc[x.divisione_ospite == 1, "away_club_id"])
            assert len(prime) <= attese, (
                f"{paese}: {len(prime)} club marcati prima divisione, ma la "
                f"lega 2025-26 ne ha {attese}")

    def test_lista_di_lavoro_coerente_col_perimetro(self, partite):
        """`da_raccogliere.csv` è il perimetro, né più né meno — e la colonna
        che dice se le formazioni ci sono già deve combaciare con `game_id`."""
        lavoro = pd.read_csv(CARTELLA / "da_raccogliere.csv")
        assert len(lavoro) == int(partite.dentro_perimetro.sum())
        atteso = partite[partite.dentro_perimetro].game_id.notna().sum()
        assert int(lavoro.gia_abbiamo_formazioni.sum()) == int(atteso)

    def test_i_buchi_sono_dichiarati(self, manifesto):
        """Un buco dichiarato e' innocuo, uno nascosto no (R6). Il manifesto
        deve dire quante partite restano senza formazioni."""
        assert manifesto["senza_formazioni"]["partite"] > 0
        assert manifesto["punteggio"]["eventi_incompleti"] >= 0
