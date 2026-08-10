"""Test dei tre ponti fra le raccolte di coppa e il resto del database.

La proprietà da proteggere non è la copertura: è che un aggancio **incerto
resti vuoto**. Una copertura alta ottenuta indovinando è peggio di una bassa
dichiarata, perché attribuisce a un giocatore la carriera di un altro.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.aggancia_coppe import _aggancia_giocatori

RADICE = Path(__file__).resolve().parents[1]
CARTELLA = RADICE / "data" / "coppe_2526"

# ⚠️ Coppe la cui fonte AUTOMATICA non ha identificatori da agganciare. Non è
# un limite del nostro aggancio: la Coupe de France non esiste in player-scores
# e viene da Wikipedia (Fase 138), che non ha `game_id`, non ha `club_id` e non
# ha formazioni. Misurato: 0/201 righe automatiche con un `game_id`, 0 con un
# `home_club_id`. Il ponte non può esistere perché manca la sponda opposta —
# `test_la_coupe_de_france_non_ha_una_sponda` lo verifica sul dato, così se un
# giorno la fonte cambiasse questa esenzione cadrebbe da sola.
SENZA_IDENTIFICATORI = {"Coupe de France"}

# Quota MINIMA di righe di formazione agganciate, dichiarata per coppa dove
# supera la soglia generale un residuo spiegato (R4: un'anomalia si dichiara
# anche quando non è un errore).
QUOTA_MINIMA = 0.95
QUOTA_DICHIARATA = {
    # 265 righe su 5.040 (98 squadre-partita). NON sono righe mancanti: le due
    # fonti hanno lo stesso numero di giocatori per squadra-partita (delta medio
    # +0,02). È la convenzione spagnola sui DUE cognomi — diretta.it scrive
    # «Sanchez Alonso M.», il registro «Mario Sánchez»: nessuno dei due insiemi
    # di token contiene l'altro, quindi la regola del sottoinsieme non li
    # aggancia e l'eliminazione scatta solo dove resta un candidato solo.
    "Copa del Rey": 0.94,
}


def _finte(nostre_giocatori, manuali):
    """Un (game_id, club_id) solo, con le due fonti da appaiare."""
    nostre = pd.DataFrame({
        "game_id": 1, "club_id": 10, "giocatore": nostre_giocatori,
        "player_id": list(range(100, 100 + len(nostre_giocatori))),
    })
    F = pd.DataFrame({
        "ID partita": "abc", "Squadra": "Tal", "Giocatore": manuali,
    })
    partite = pd.DataFrame({"id_diretta": ["abc"], "game_id": [1]})
    return nostre, F, partite


def test_eliminazione_solo_quando_resta_una_possibilita(tmp_path, monkeypatch):
    """Un nome spaiato e un candidato libero: sono la stessa persona.
    Due e due: **nessuno** viene agganciato."""
    import scripts.aggancia_coppe as A

    # caso 1-1 → eliminazione
    nostre, F, partite = _finte(["Emanuele Motta", "Ignoto Assoluto"],
                                ["Motta E.", "Sconosciuto X."])
    nostre.to_csv(tmp_path / "formazioni.csv", index=False)
    monkeypatch.setattr(A, "USCITA", tmp_path)
    out = _aggancia_giocatori(F, partite, lambda n: 10)
    assert out.player_id.notna().all()
    assert set(out.metodo) == {"nome", "eliminazione"}

    # caso 2-2 → nessun aggancio per eliminazione
    nostre, F, partite = _finte(["Tizio Uno", "Caio Due"], ["Alfa A.", "Beta B."])
    nostre.to_csv(tmp_path / "formazioni.csv", index=False)
    out = _aggancia_giocatori(F, partite, lambda n: 10)
    assert out.player_id.isna().all()


def test_partita_non_agganciata_lascia_i_giocatori_vuoti(tmp_path, monkeypatch):
    """Senza `game_id` non ci sono candidati: le righe restano vuote invece di
    essere agganciate a qualcuno di un'altra partita."""
    import scripts.aggancia_coppe as A

    nostre, F, _ = _finte(["Emanuele Motta"], ["Motta E."])
    nostre.to_csv(tmp_path / "formazioni.csv", index=False)
    monkeypatch.setattr(A, "USCITA", tmp_path)
    partite = pd.DataFrame({"id_diretta": ["abc"], "game_id": [pd.NA]})
    out = _aggancia_giocatori(F, partite, lambda n: 10)
    assert out.player_id.isna().all()


def test_omonimi_nella_stessa_squadra_non_si_scambiano(tmp_path, monkeypatch):
    """Due Esposito nello stesso undici: l'iniziale li separa, e se non
    bastasse nessuno dei due va agganciato a caso."""
    import scripts.aggancia_coppe as A

    nostre, F, partite = _finte(["Salvatore Esposito", "Francesco Esposito"],
                                ["Esposito Sa.", "Esposito Fr."])
    nostre.to_csv(tmp_path / "formazioni.csv", index=False)
    monkeypatch.setattr(A, "USCITA", tmp_path)
    out = _aggancia_giocatori(F, partite, lambda n: 10)
    coppie = dict(zip(out.Giocatore, out.player_id))
    assert coppie["Esposito Sa."] == 100      # Salvatore
    assert coppie["Esposito Fr."] == 101      # Francesco


@pytest.mark.skipif(not (CARTELLA / "aggancio_manifesto.json").exists(),
                    reason="gli agganci non sono stati costruiti")
class TestAgganciProdotti:

    @pytest.fixture(scope="class")
    def quadro(self):
        return json.loads(
            (CARTELLA / "aggancio_manifesto.json").read_text(encoding="utf-8"))

    def test_la_coupe_de_france_non_ha_una_sponda(self):
        """L'esenzione di `SENZA_IDENTIFICATORI` va verificata sul DATO.

        Altrimenti è un'esenzione che si auto-giustifica: basterebbe scriverci
        dentro una coppa per far tacere il controllo. Qui si pretende che la
        causa sia vera — zero `game_id` e zero `club_id` nella fonte automatica
        — così il giorno in cui quella fonte cambiasse il test cadrebbe e
        l'esenzione andrebbe rifatta.
        """
        N = pd.read_csv(CARTELLA / "partite.csv")
        for coppa in SENZA_IDENTIFICATORI:
            d = N[N.competizione == coppa]
            assert len(d), coppa
            assert d.game_id.notna().sum() == 0, coppa
            assert d.home_club_id.notna().sum() == 0, coppa

    def test_tutte_le_squadre_agganciate(self, quadro):
        """Un club senza `club_id` rompe a valle sia le partite sia i
        giocatori: dev'essere zero, non «quasi zero»."""
        for q in quadro:
            if q["coppa"] in SENZA_IDENTIFICATORI:
                continue
            assert q["squadre"]["non_agganciate"] == [], q["coppa"]

    def test_partite_agganciate_tranne_quelle_che_non_esistono(self, quadro):
        """L'unico buco ammesso è la finale, che la fonte automatica non ha e
        che quindi non ha un `game_id` da agganciare (Fase 138). Se ne
        comparisse un altro, è un problema di aggancio."""
        for q in quadro:
            if q["coppa"] in SENZA_IDENTIFICATORI:
                continue
            manca = q["partite"]["totali"] - q["partite"]["agganciate"]
            assert manca <= 1, f"{q['coppa']}: {manca} partite non agganciate"

    def test_ogni_foglio_raccolto_e_agganciato(self):
        """⭐ Il controllo di completezza: nessun foglio raccolto resta fuori.

        Quando l'utente l'ha chiesto, 8.475 righe di evento e 8.115 di
        statistica erano raccolte e collegate a NIENTE — e non se n'era accorto
        nessuno, perché i numeri che guardavamo (partite, formazioni) erano
        ottimi. Un foglio dimenticato non dà errore: dà silenzio.
        """
        from scripts.verifica_aggancio_coppe import verifica

        righe, problemi = verifica()
        assert problemi == [], problemi
        assert righe, "nessuna raccolta trovata"
        for r in righe:
            # ⭐ Questo vale per TUTTE le coppe, esenzioni comprese: la
            # completezza non dipende da quanto la fonte automatica sappia. Una
            # riga che non si riesce ad agganciare resta comunque in tabella,
            # con la colonna vuota — sparire è un'altra cosa.
            assert r["in_tabella"] == r["raccolte"], r
            if r["coppa"] in SENZA_IDENTIFICATORI:
                continue
            assert r["quota"] >= QUOTA_DICHIARATA.get(r["coppa"], QUOTA_MINIMA), r

    def test_copertura_giocatori_alta_e_niente_e_indovinato(self, quadro):
        for q in quadro:
            g = q["giocatori"]
            assert g["agganciate"] <= g["righe"]
            if q["coppa"] in SENZA_IDENTIFICATORI:
                continue
            soglia = QUOTA_DICHIARATA.get(q["coppa"], QUOTA_MINIMA)
            assert g["quota"] >= soglia, f"{q['coppa']}: {g['quota']:.1%}"

    def test_nessun_player_id_usato_due_volte_nella_stessa_partita(self):
        """La stessa persona non può essere due giocatori diversi della stessa
        squadra nella stessa partita: se succede, l'appaiamento ha sbagliato."""
        g = pd.read_csv(CARTELLA / "aggancio_giocatori.csv").dropna(
            subset=["player_id", "game_id"])
        doppi = g.groupby(["game_id", "club_id", "player_id"]).size()
        assert (doppi == 1).all(), doppi[doppi > 1].head().to_dict()
