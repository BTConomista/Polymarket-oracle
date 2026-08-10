"""Test della porta d'ingresso per le raccolte manuali di coppa (Fase 139).

Il valore di questa porta non e' l'archiviazione: e' il **confronto con la
fonte automatica**. Due fonti indipendenti sulla stessa partita sono l'unico
modo di accorgersi che una delle due sbaglia — e la Fase 138 aveva appena
dimostrato che una delle due sbagliava davvero (68 punteggi su 458 sommavano
i rigori). Questi test proteggono i controlli, non i dati.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.registra_raccolta_coppa_diretta import (
    _appaia_undici,
    _token,
    verifica_punteggio,
    verifica_rigori_eventi,
    verifica_undici,
)

RADICE = Path(__file__).resolve().parents[1]
RACCOLTA = RADICE / "files" / "diretta_coppa_italia_2526"


# --------------------------------------------------------------------------- #
# l'aggancio dei nomi fra le due fonti
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("diretta, registro", [
    ("Motta E.", "Emanuele Motta"),            # ordine invertito + iniziale
    ("Caracciolo Ant.", "Antonio Caracciolo"),  # iniziale di tre lettere
    ("Esposito Sa.", "Salvatore Esposito"),     # due Esposito, iniziale lunga
    ("Gronbaek A.", "Albert Grønbaek"),         # ø: NFKD non lo decompone
    ("Kilicsoy S.", "Semih Kılıçsoy"),          # ı senza punto
    ("Hojlund R.", "Rasmus Højlund"),
    ("Yildiz K.", "Kenan Yıldız"),
    ("Ndri K.", "Konan N'Dri"),                 # apostrofo
])
def test_stesso_giocatore_scritto_dalle_due_fonti(diretta, registro):
    """Ognuno di questi e' UNA persona scritta in due modi.

    Non sono casi di scuola: sono i 15 che, senza la tabella dei caratteri
    del progetto, facevano risultare «formazioni diverse» quindici undici
    che erano identici.
    """
    from scripts.registra_raccolta_coppa_diretta import _stessa_persona
    assert _stessa_persona(_token(diretta), _token(registro)), \
        f"«{diretta}» e «{registro}» non si agganciano"


def test_due_omonimi_in_rosa_non_si_confondono():
    """Salvatore e Francesco Esposito giocano davvero nella stessa Coppa
    Italia: l'iniziale è l'unica cosa che li distingue, e per questo si
    conserva invece di buttarla."""
    from scripts.registra_raccolta_coppa_diretta import _stessa_persona
    assert _stessa_persona(_token("Esposito Sa."), _token("Salvatore Esposito"))
    assert not _stessa_persona(_token("Esposito Sa."), _token("Francesco Esposito"))


def _g(nome, numero=None):
    """Una riga di formazione come la vuole `_appaia_undici`: token, numero, nome."""
    return (_token(nome), numero, nome)


def test_giocatori_diversi_non_si_agganciano():
    a, b, _ = _appaia_undici([_g("Rossi M.", 4)], [_g("Bianchi L.", 9)])
    assert (a, b) == (["Rossi M."], ["Bianchi L."])


def test_convenzione_spagnola_appaiata_solo_in_seconda_passata():
    """«Santiago Perez J.» e «Yellu Santiago» sono la stessa persona ma NON
    in relazione di sottoinsieme: li appaia solo la seconda passata."""
    from scripts.registra_raccolta_coppa_diretta import _stessa_persona
    a, b = _token("Santiago Perez J."), _token("Yellu Santiago")
    assert not _stessa_persona(a, b)
    solo_a, solo_b, da_numero = _appaia_undici([_g("Santiago Perez J.", 7)],
                                               [_g("Yellu Santiago", 7)])
    assert (solo_a, solo_b) == ([], [])
    assert da_numero == 0, "questo lo appaia il NOME, non deve contarsi sul numero"


# --------------------------------------------------------------------------- #
# il numero di maglia — la terza passata (Copa del Rey)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("diretta, registro", [
    ("Pibe", "Agustín Pastoriza"),      # soprannome contro nome anagrafico
    ("Yusi", "Youssef Enríquez"),
    ("Martinez M. G.", "Miguel García"),  # cognome doppio scelto in modo diverso
    ("Sanchez A.", "Álex Salto"),
])
def test_il_numero_di_maglia_aggancia_dove_il_nome_non_puo(diretta, registro):
    """Nessuna normalizzazione arriva a questi: non condividono un carattere.

    Sono 28 coppie su 39 nella Copa del Rey, e sono la ragione della terza
    passata: il numero di maglia e' unico dentro una squadra in una partita,
    quindi due righe con lo stesso numero sono la stessa persona.
    """
    solo_a, solo_b, da_numero = _appaia_undici([_g(diretta, 22)], [_g(registro, 22)])
    assert (solo_a, solo_b, da_numero) == ([], [], 1)


def test_senza_numero_i_nomi_diversi_restano_spaiati():
    """Il numero e' l'unica prova: tolto quello, l'aggancio NON si indovina."""
    solo_a, solo_b, _ = _appaia_undici([_g("Pibe")], [_g("Agustín Pastoriza")])
    assert (solo_a, solo_b) == (["Pibe"], ["Agustín Pastoriza"])


def test_numero_diverso_non_aggancia():
    """Numancia-Maiorca 02/12/2025: diretta.it schiera «Jony» (9), la fonte
    automatica «Berto» (18). Le fonti dissentono davvero — l'undici ufficiale
    (bet365/VAVEL) da' ragione alla manuale — e la differenza deve restare."""
    solo_a, solo_b, _ = _appaia_undici([_g("Jony", 9)], [_g("Berto", 18)])
    assert (solo_a, solo_b) == (["Jony"], ["Berto"])


def test_numero_conteso_non_aggancia_nessuno():
    """Due residui con lo stesso numero: un aggancio incerto resta VUOTO.

    Sceglierne uno vorrebbe dire far vincere l'ordine del file, cioe' scegliere
    a caso — lo stesso guardrail delle partite contese in `coppe_aggancio`.
    """
    solo_a, solo_b, da_numero = _appaia_undici(
        [_g("Pibe", 22), _g("Jogo", 22)],
        [_g("Agustín Pastoriza", 22), _g("Jonathan Gómez", 22)])
    assert da_numero == 0
    assert len(solo_a) == 2 and len(solo_b) == 2


# --------------------------------------------------------------------------- #
# le verifiche sul dato consegnato
# --------------------------------------------------------------------------- #
def test_undici_titolari_anomali_vengono_segnalati():
    f = pd.DataFrame({
        "ID partita": ["A"] * 11 + ["A"] * 10,
        "Squadra": ["Casa"] * 11 + ["Ospite"] * 10,
        "Gruppo": ["Titolare"] * 21,
    })
    r = verifica_undici(f)
    assert r["con_undici_esatti"] == 1
    assert len(r["anomale"]) == 1
    assert r["anomale"][0]["titolari"] == 10


def test_punteggio_ai_rigori_deve_partire_da_una_parita():
    """Se una partita e' andata ai rigori ma il punteggio non e' di parita',
    o il punteggio somma i rigori o e' sbagliato: in entrambi i casi si dice."""
    buona = pd.DataFrame([{
        "Data": "16.08.2025", "Casa": "A", "Ospite": "B",
        "Gol casa 90": 1, "Gol ospite 90": 1,
        "Gol casa dts": None, "Gol ospite dts": None,
        "Rigori casa": 5, "Rigori ospite": 4}])
    assert verifica_punteggio(buona)["incoerenti"] == []

    contaminata = buona.copy()
    contaminata.loc[0, ["Gol casa 90", "Gol ospite 90"]] = [6, 5]  # 1-1 + rigori
    assert len(verifica_punteggio(contaminata)["incoerenti"]) == 1


def test_rigori_in_parita_sono_impossibili():
    d = pd.DataFrame([{
        "Data": "16.08.2025", "Casa": "A", "Ospite": "B",
        "Gol casa 90": 1, "Gol ospite 90": 1,
        "Gol casa dts": None, "Gol ospite dts": None,
        "Rigori casa": 4, "Rigori ospite": 4}])
    assert len(verifica_punteggio(d)["incoerenti"]) == 1


def test_sequenza_rigori_confrontata_col_totale():
    partite = pd.DataFrame([{
        "ID partita": "X", "Data": "16.08.2025", "Casa": "A", "Ospite": "B",
        "Rigori casa": 5, "Rigori ospite": 4}])
    eventi = pd.DataFrame(
        [{"ID partita": "X", "Periodo": "Rigori", "Tipo evento": "Rigore",
          "Lato": "Casa"}] * 5
        + [{"ID partita": "X", "Periodo": "Rigori", "Tipo evento": "Rigore",
            "Lato": "Ospite"}] * 4)
    assert verifica_rigori_eventi(partite, eventi)["sequenza_ricompone"] == 1

    monca = eventi.iloc[:-1]           # un rigore non registrato
    r = verifica_rigori_eventi(partite, monca)
    assert r["sequenza_ricompone"] == 0
    assert len(r["divergenti"]) == 1


# --------------------------------------------------------------------------- #
# la raccolta effettivamente registrata
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not (RACCOLTA / "manifesto_coppa.json").exists(),
                    reason="la raccolta Coppa Italia non e' presente")
class TestCoppaItaliaRegistrata:

    @pytest.fixture(scope="class")
    def manifesto(self):
        return json.loads((RACCOLTA / "manifesto_coppa.json").read_text(encoding="utf-8"))

    def test_conteggi(self, manifesto):
        c = manifesto["conteggi"]
        assert c["partite"] == 45
        assert c["titolari"] == 45 * 22      # 11 per squadra, 2 squadre
        assert c["metriche_per_giocatore"] > 100

    def test_tutte_le_verifiche_interne_passano(self, manifesto):
        v = manifesto["verifiche"]
        assert v["undici_titolari"]["anomale"] == []
        assert v["punteggio_non_somma_i_rigori"]["incoerenti"] == []
        sr = v["sequenza_rigori"]
        assert sr["sequenza_ricompone"] == sr["partite_ai_rigori"] > 0

    def test_le_due_fonti_indipendenti_concordano(self, manifesto):
        """Il risultato che dà senso a tutto il resto.

        Se un giorno diverge, questo test lo dice — ed è il momento in cui si
        va a capire QUALE delle due sbaglia, non quello in cui si sceglie la
        più comoda.
        """
        c = manifesto["verifiche"]["confronto_con_fonte_automatica"]
        assert c["eseguito"]
        p, f = c["partite"], c["formazioni"]
        assert p["appaiate"] == p["manuale"] == p["automatica"]
        assert p["divergenti"] == []
        # i buchi che la fonte automatica aveva DICHIARATO e la manuale colma
        # non sono divergenze: sono il motivo per cui la seconda fonte esiste.
        assert p["identiche_su_tutti_i_punteggi"] == p["appaiate"]
        assert f["con_differenze"] == []
        assert f["undici_identici"] == f["squadre_partita_confrontabili"]

    def test_originali_conservati(self):
        """§5-ter: senza l'originale, un bug della nostra conversione diventa
        indistinguibile dal dato."""
        assert (RACCOLTA / "originale_coppa.xlsx").exists()


# --------------------------------------------------------------------------- #
# il secondo consegnato: le statistiche (Fase 139-quater)
# --------------------------------------------------------------------------- #
def _scrivi_raccolta_finta(cartella: Path, turno_vecchio: str, turno_nuovo: str,
                           valore_nuovo: float = 1.234,
                           squadra_casa_nuova: str = "A") -> Path:
    """Una raccolta minima + il suo file di statistiche, con i due consegnati
    che scrivono il TURNO in due modi diversi.

    E' il caso reale della Carabao Cup: la raccolta base dice «1/64 FINALE», il
    file di statistiche «1° turno». Stesse partite, stessi giocatori, stessi
    numeri — solo un'etichetta scritta diversamente.
    """
    cartella.mkdir(parents=True, exist_ok=True)
    partite = pd.DataFrame([
        {"Competizione": "C", "Turno": turno_vecchio, "Data": "12.08.2025",
         "Casa": "A", "Ospite": "B", "ID partita": "p1"},
        {"Competizione": "C", "Turno": turno_vecchio, "Data": "13.08.2025",
         "Casa": "C", "Ospite": "D", "ID partita": "p2"},
    ])
    partite.to_csv(cartella / "partite.csv", index=False)

    def giocatori(turno, valore, ordine, squadra_casa="A"):
        d = pd.DataFrame([
            {"Competizione": "C", "Turno": turno, "Data": "12.08.2025",
             "Casa": squadra_casa, "Ospite": "B", "Squadra": squadra_casa,
             "Giocatore": "Rossi M.", "Stato": "Titolare",
             "Tocchi": 40, "Rating": valore},
            # ⚠️ stesso nome, stessa squadra, stessa partita — e sono DUE
            # persone: e' il caso «Fernandez P.» del Reus (numeri 3 e 24).
            # Senza `Stato` nella chiave, il confronto le vede come un doppione.
            {"Competizione": "C", "Turno": turno, "Data": "12.08.2025",
             "Casa": squadra_casa, "Ospite": "B", "Squadra": squadra_casa,
             "Giocatore": "Rossi M.", "Stato": "Subentrato",
             "Tocchi": 12, "Rating": valore + 2},
            {"Competizione": "C", "Turno": turno, "Data": "13.08.2025",
             "Casa": "C", "Ospite": "D", "Squadra": "C", "Giocatore": "Bianchi L.",
             "Stato": "Titolare", "Tocchi": 51, "Rating": valore + 1},
        ])
        return d.iloc[ordine].reset_index(drop=True)

    # il vecchio in un ordine, il nuovo nell'altro: e' proprio quello che
    # l'ordinamento deve rimettere a posto
    giocatori(turno_vecchio, 1.234, [0, 1, 2]).to_csv(
        cartella / "stat_giocatori.csv", index=False)

    xlsx = cartella / "statistiche.xlsx"
    squadra = pd.DataFrame([
        {"Competizione": "C", "Turno": turno_nuovo, "Data": "12.08.2025",
         "Casa": squadra_casa_nuova, "Ospite": "B", "Periodo": p, "Lato": lato,
         "Squadra": sq, "ID partita": "p1", "Tiri": 3}
        for p in ("Totale", "1° tempo", "2° tempo")
        for lato, sq in (("Casa", squadra_casa_nuova), ("Ospite", "B"))
    ])
    with pd.ExcelWriter(xlsx) as w:
        (partite.assign(Turno=turno_nuovo)
                .replace({"Casa": {"A": squadra_casa_nuova}})
                .to_excel(w, sheet_name="Partite", index=False))
        nuovo = giocatori(turno_nuovo, valore_nuovo, [2, 1, 0],
                          squadra_casa=squadra_casa_nuova)
        nuovo["ID partita"] = ["p2", "p1", "p1"]   # la colonna che il vecchio non ha
        nuovo.to_excel(w, sheet_name="Statistiche giocatori", index=False)
        squadra.to_excel(w, sheet_name="Statistiche squadra", index=False)
        pd.DataFrame({"Nota": []}).to_excel(w, sheet_name="Note", index=False)
    return xlsx


def test_un_turno_scritto_diversamente_non_e_un_dato_diverso(tmp_path):
    """La regressione della Carabao Cup: 122.401 celle «divergenti» su un dato
    identico riga per riga.

    L'ordinamento del confronto includeva `Turno`, che i due consegnati
    scrivono in modo diverso: le due tabelle finivano allineate male e OGNI
    cella risultava diversa. Il controllo bocciava il dato buono. Qui la
    differenza d'etichetta dev'essere **dichiarata**, non bloccante.
    """
    from scripts.registra_raccolta_coppa_diretta import integra_statistiche

    cartella = tmp_path / "raccolta"
    xlsx = _scrivi_raccolta_finta(cartella, "1/64 FINALE", "1° turno")
    q = integra_statistiche(cartella, xlsx)

    f = q["fedelta_giocatori"]
    assert f["celle_divergenti_oltre_arrotondamento"] == 0
    assert f["colonne_testuali_con_etichette_diverse"] == {"Turno": 3}
    assert f["colonne_nuove"] == ["ID partita"]
    assert q["statistiche_squadra"]["righe"] == 6
    assert (cartella / "stat_squadra.csv").exists()


def test_un_valore_davvero_diverso_blocca_ancora(tmp_path):
    """Il rovescio del test precedente: allentare il confronto sulle etichette
    non deve renderlo cieco sui NUMERI, che sono il motivo per cui esiste."""
    from scripts.registra_raccolta_coppa_diretta import integra_statistiche

    cartella = tmp_path / "raccolta"
    # 1.234 -> 7.5: non e' un decimale in piu', e' un'altra misura
    xlsx = _scrivi_raccolta_finta(cartella, "1/64 FINALE", "1° turno",
                                  valore_nuovo=7.5)
    with pytest.raises(ValueError, match="OLTRE l'arrotondamento"):
        integra_statistiche(cartella, xlsx)
    # e non deve aver scritto niente: si sovrascrive solo dopo la verifica
    assert not (cartella / "stat_squadra.csv").exists()


def test_si_puo_ri_integrare_dall_originale_gia_archiviato(tmp_path):
    """Rifare il lavoro partendo dall'originale conservato dev'essere possibile.

    E' il motivo per cui la §5-ter lo conserva: quando cambia qualcosa a monte
    — un alias di club, una regola di aggancio — si ri-registra e si re-integra
    dagli originali. Senza la guardia, `copy2` alzava `SameFileError` **dopo**
    aver riscritto i due CSV e **prima** del manifesto: la raccolta restava a
    meta', che e' lo stato peggiore in cui lasciarla.
    """
    from scripts.registra_raccolta_coppa_diretta import integra_statistiche

    cartella = tmp_path / "raccolta"
    xlsx = _scrivi_raccolta_finta(cartella, "1/64 FINALE", "1° turno")
    integra_statistiche(cartella, xlsx)

    archivio = cartella / "originale_statistiche.xlsx"
    assert archivio.exists()
    q = integra_statistiche(cartella, archivio)          # non deve sollevare
    assert q["fedelta_giocatori"]["celle_divergenti_oltre_arrotondamento"] == 0
    assert archivio.exists()


def test_due_omonimi_nella_stessa_squadra_non_sono_un_doppione(tmp_path):
    """Copa del Rey: DUE `Fernandez P.` nel Reus il 03/12/2025, numeri 3 e 24.

    Uno titolare per 90', uno subentrato al 59'; i due rating (5.9 e 6.2)
    combaciano riga per riga con la raccolta base, che li distingue per numero
    di maglia. Sono due persone. La chiave del confronto pretende l'unicità, e
    senza `Stato` avrebbe rifiutato il file dicendo «doppione» — cioè avrebbe
    bocciato il dato buono per la terza volta in tre coppe.
    """
    from scripts.registra_raccolta_coppa_diretta import integra_statistiche

    cartella = tmp_path / "raccolta"
    xlsx = _scrivi_raccolta_finta(cartella, "1/64 FINALE", "1° turno")
    q = integra_statistiche(cartella, xlsx)
    assert q["fedelta_giocatori"]["righe_dopo"] == 3
    scritto = pd.read_csv(cartella / "stat_giocatori.csv")
    omonimi = scritto[scritto.Giocatore == "Rossi M."]
    assert len(omonimi) == 2
    assert sorted(omonimi.Stato) == ["Subentrato", "Titolare"]


def test_un_club_scritto_diversamente_fra_i_due_consegnati(tmp_path):
    """«Cieza» nel file di statistiche, «Ciudad Cieza» nella raccolta base.

    Il controllo «le partite devono essere le stesse» bocciava due partite che
    ci sono. Il sinonimo va **accettato e dichiarato**, non applicato in
    silenzio: finisce nel manifesto, e la colonna resta com'è consegnata.
    """
    from scripts.registra_raccolta_coppa_diretta import integra_statistiche

    cartella = tmp_path / "raccolta"
    xlsx = _scrivi_raccolta_finta(cartella, "1° turno", "1° turno",
                                  squadra_casa_nuova="A Ciudad")
    q = integra_statistiche(cartella, xlsx)
    assert q["partite"]["sinonimi_di_squadra_accettati"] == {"A Ciudad": "A"}
    assert q["partite"]["solo_nella_raccolta"] == []
    assert q["fedelta_giocatori"]["celle_divergenti_oltre_arrotondamento"] == 0
    # la grafia consegnata NON viene riscritta: si canonicalizza solo la chiave
    assert set(pd.read_csv(cartella / "stat_giocatori.csv").Squadra) == {"A Ciudad", "C"}
