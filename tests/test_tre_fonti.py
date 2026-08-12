"""Le cinque riparazioni della raccolta a tre fonti, inchiodate.

PERCHE' ESISTE QUESTO FILE. `src/data/tre_fonti.py` non corregge i dati sul
disco (R3): li corregge **in lettura**. Una riparazione che vive nel codice e'
una riparazione che si puo' disfare senza accorgersene — basta un refactoring
che salta un passaggio, e il difetto torna silenzioso perche' i file grezzi lo
contengono ancora.

Ogni test qui sotto fallisce se una riparazione viene disfatta, e il commento
dice quale difetto ha pagato. Sono guardie, non verifiche di funzionamento.
"""
from __future__ import annotations

import pandas as pd
import pytest

from src.data import tre_fonti as tf


@pytest.fixture(scope="module")
def sq():
    return tf.squadre(periodo="Totale")


@pytest.fixture(scope="module")
def gio():
    return tf.giocatori()


# --------------------------------------------------------------------------
# Riparazione 1 — le 2 righe orfane Verona/Hellas Verona
# --------------------------------------------------------------------------
def test_le_righe_orfane_verona_sono_fuori(sq):
    """762 righe «Totale» dove le squadra-partita sono 760.

    Understat scrive «Verona», SofaScore e WhoScored «Hellas Verona»: la
    fusione a monte ha lasciato 2 righe senza `Avversario`, con le sole colonne
    Understat. E' il caso che il §5 del CLAUDE.md porta come esempio storico.
    Se questo test diventa rosso, un conteggio di partite dara' **381** su un
    campionato che ne ha 380.
    """
    assert len(sq) == 760, f"attese 760 squadra-partita, trovate {len(sq)}"
    assert sq["Avversario"].notna().all(), "una riga senza avversario e' un'orfana"


def test_le_due_grafie_di_verona_sono_diventate_una(sq):
    """Il senso della riparazione non e' scartare righe: e' avere UNA squadra.

    Con due grafie vive, «Verona» e «Hellas Verona» restano due squadre per
    qualunque join, e nessun conteggio se ne accorge.
    """
    grafie = {s for s in sq["Squadra"] if isinstance(s, str) and "erona" in s}
    assert len(grafie) == 1, f"Verona ha ancora {len(grafie)} grafie: {grafie}"


def test_il_dato_delle_due_orfane_non_era_da_recuperare(sq):
    """Le orfane erano un duplicato PARZIALE: la partita c'e' gia', completa.

    Conta perche' giustifica lo scarto. Se le due partite NON fossero presenti
    per altra via, scartarle sarebbe perdere dato — e la riparazione giusta
    sarebbe un'altra (fondere, scegliendo quale valore tenere).
    """
    for data in ("2025-09-15", "2025-08-25"):
        righe = sq[(sq["Data"] == data) & (sq["Squadra"] == "Verona")]
        assert len(righe) == 1, f"{data}: attesa 1 riga Verona completa, {len(righe)}"
        assert righe["Avversario"].notna().all()


# --------------------------------------------------------------------------
# Riparazione 2 — la colonna ID partita che impila tre numerazioni
# --------------------------------------------------------------------------
def test_id_partita_misto_e_rinominato_non_cancellato(gio):
    """La colonna con 436 valori distinti su 380 partite non deve restare usabile.

    Impila SofaScore (~14M), WhoScored (~1,9M) e Understat (~30k): un join su
    quella colonna appaia partite diverse SENZA dare errore — finto pieno (R6).
    Il nome nuovo e' la guardia: chi lo legge sa perche' non usarla.
    ⚠️ Rinominata e non cancellata di proposito: una colonna sparita si
    ri-scopre leggendo il grezzo, e si ri-usa.
    """
    assert tf.ID_AVVELENATO not in gio.columns
    assert tf.ID_RINOMINATO in gio.columns


def test_le_tre_colonne_id_per_fonte_sono_sane(gio):
    """380 partite, quindi 380 identificatori per ciascuna delle tre fonti.

    E' il controllo che rende la rinomina una scelta e non una rinuncia: le
    colonne buone ci sono, e sono queste.
    """
    for fonte, col in tf.ID_PARTITA_PER_FONTE.items():
        assert gio[col].nunique() == 380, f"{fonte}: {gio[col].nunique()} id invece di 380"


# --------------------------------------------------------------------------
# Riparazione 4 — i 2 gol che Understat perde
# --------------------------------------------------------------------------
def test_i_due_gol_persi_da_understat_sono_allineati(gio):
    """Verificato su QUATTRO fonti indipendenti, non assunto.

    L'ipotesi ovvia era «convenzione sugli autogol», ed e' FALSA: `Autogol`
    vale 0 su entrambe le fonti, gli eventi danno `Gol / regular` con un `Tiro`
    e uno `scoreChange` allo stesso minuto, e lo snapshot football-data
    conferma i punteggi (Torino 1-2 Bologna, Pisa 0-2 Juventus).
    E' una lacuna di Understat.
    """
    corrette = gio[gio["gol_corretto_da_noi"]]
    assert len(corrette) == 2, f"attese 2 correzioni, trovate {len(corrette)}"
    assert set(corrette["Giocatore"]) == {"Nikola Moro", "Pierre Kalulu"}
    assert (corrette["Gol (Understat)"] == corrette["Gol (SofaScore)"]).all()


def test_la_correzione_resta_visibile(gio):
    """Una correzione invisibile e' indistinguibile dal dato originale.

    La colonna esiste per questo: chi legge un `Gol (Understat)` deve poter
    sapere se e' della fonte o nostro.
    """
    assert "gol_corretto_da_noi" in gio.columns
    assert gio["gol_corretto_da_noi"].sum() == 2


# --------------------------------------------------------------------------
# La GRANA di `eventi` — l'errore che sembra un difetto dei dati
# --------------------------------------------------------------------------
def test_la_grana_copre_tutte_le_categorie_presenti():
    """Se la fonte aggiunge una categoria, `GRANA` deve saperlo.

    Senza, `chiave_di` alza — ed e' meglio di un join fatto con la chiave
    sbagliata, che invece riesce e produce righe appaiate a caso.
    """
    presenti = set(tf.eventi()["Categoria"].dropna().unique())
    assert presenti <= set(tf.GRANA), f"categorie senza grana: {presenti - set(tf.GRANA)}"


@pytest.mark.parametrize("categoria,attesa", [
    ("Momentum", ("Data", "Casa", "Trasferta")),
    ("Quota", ("Data", "Casa", "Trasferta")),
    ("Cronaca", ("Data", "Casa", "Trasferta")),
    ("Evento", ("Data", "Squadra")),
    ("Tiro", ("Data", "Squadra")),
])
def test_chiave_di_da_la_grana_giusta(categoria, attesa):
    """Cinque categorie su sette sono di PARTITA e hanno `Squadra` vuota.

    Agganciarle per (data, squadra) fa risultare 96.510 righe «orfane» che
    orfane non sono: un difetto apparente prodotto dalla chiave sbagliata.
    Stessa famiglia dell'errore di LATO gia' pagato su `gol_dedotti`.
    """
    assert tf.chiave_di(categoria) == attesa


def test_le_categorie_di_partita_hanno_squadra_vuota():
    """La ragione per cui la chiave (data, squadra) non puo' funzionare.

    Non e' una convenzione nostra: e' come il file e' fatto. Inchiodarlo
    impedisce di "riparare" quei NaN in una sessione futura.
    """
    e = tf.eventi(categoria="Momentum")
    assert e["Squadra"].isna().all(), "Momentum descrive la partita, non una squadra"


# --------------------------------------------------------------------------
# L'aggancio allo snapshot: il controllo che dice se la raccolta serve
# --------------------------------------------------------------------------
def test_squadre_aggancia_tutte_le_760_squadra_partita(sq):
    """760/760 contro `data/serie_a_matches.csv`.

    E' la misura che giustifica la riparazione 1: prima erano 762 righe per
    760 squadra-partita, e la differenza non era un dato in piu'.
    """
    snap = pd.read_csv("data/serie_a_matches.csv")
    snap = snap[snap["season"].astype(str) == "2526"]
    snap_d = pd.to_datetime(snap["date"]).dt.date
    attese = set(zip(snap_d, snap["home_team"])) | set(zip(snap_d, snap["away_team"]))

    nostre = set(zip(pd.to_datetime(sq["Data"]).dt.date, sq["Squadra"]))
    assert len(attese) == 760
    assert nostre == attese, f"{len(attese - nostre)} squadra-partita non agganciate"


# --------------------------------------------------------------------------
# I limiti DICHIARATI: se cambiano, va aggiornata la documentazione
# --------------------------------------------------------------------------
def test_le_colonne_dichiarate_vuote_sono_ancora_vuote(sq):
    """`Meteo (WhoScored)` allo 0,0% e `Tocchi` al 100% NaN.

    ⚠️ Se questo test diventa ROSSO la fonte ha cominciato a riempirle — ed e'
    una buona notizia che va scritta in README e manifesto, non ignorata.
    """
    for col in tf.colonne_vuote("serie_a").get("squadre", ()):
        assert sq[col].isna().all(), f"{col} non e' piu' vuota: aggiorna la documentazione"


def test_spettatori_e_dichiarato_post_non_pre():
    """La trappola R8 di questa raccolta: sta fra colonne anagrafiche ed e' post.

    `Stadio` e `Capienza` sono noti prima del fischio, `Spettatori` no. Il
    numero e' giusto, e' il MOMENTO a essere sbagliato — l'errore piu' facile
    da commettere e piu' difficile da vedere.
    """
    assert tf.disponibilita("Spettatori (SofaScore)") == "post"
    assert tf.disponibilita("Capienza (SofaScore)") == "pre"
    assert tf.disponibilita("Arbitro (SofaScore)") == "pre"


def test_la_preferenza_xg_non_esiste_ed_e_voluto():
    """Le due xG sono due MODELLI diversi: fonderle e' un errore, non una scelta.

    Somma stagionale: SofaScore 971,4 · Understat 1077,5. Chiedere «quale
    vince» significa non aver capito il dato, quindi la funzione alza con un
    messaggio che lo spiega invece di restituire una fonte a caso.
    """
    with pytest.raises(ValueError, match="due MODELLI diversi"):
        tf.preferita("xG")
    assert tf.preferita("gol") == "SofaScore"


# --------------------------------------------------------------------------
# La legenda: il limite che la seconda consegna ha chiuso
# --------------------------------------------------------------------------
def test_la_legenda_v2_documenta_ogni_colonna_di_ogni_file():
    """503 colonne su 503. La prima consegna ne lasciava scoperte 53.

    ⚠️ Se questo test diventa ROSSO, una consegna futura ha aggiunto colonne
    senza aggiornare la legenda: e' esattamente il lavoro per cui la guardia
    esiste. Non silenziarlo — chiedi la legenda aggiornata.
    """
    scoperte = tf.colonne_non_documentate()
    assert scoperte == {k: [] for k in scoperte}, f"colonne senza legenda: {scoperte}"


def test_la_legenda_v1_resta_leggibile_ed_e_ancora_incompleta():
    """La v1 e' conservata come originale consegnato (regola 5-ter).

    Il test inchioda ANCHE la sua incompletezza: serve a ricordare perche' e'
    stata sostituita, e impedisce che qualcuno la ri-adotti per sbaglio
    credendola equivalente.
    """
    v1 = tf.legenda(versione="v1")
    assert len(v1) == 440
    assert "Dettaglio" in v1.columns, "la v1 ha lo schema vecchio"
    scoperte = tf.colonne_non_documentate(versione="v1")
    assert scoperte["eventi_opta"], "con la v1 eventi_opta era completamente scoperto"


# --------------------------------------------------------------------------
# La discordanza FALSA: un flag vero per costruzione che non porta informazione
# --------------------------------------------------------------------------
def test_la_discordanza_sul_possesso_e_un_falso_positivo(sq):
    """760 righe su 762 marcate «possesso», e non e' un disaccordo fra fonti.

    `Ball possession (SofaScore)` e' una PERCENTUALE (somma 100 fra le due
    squadre), `possession (WhoScored)` un CONTEGGIO (somma ~898). Non possono
    coincidere mai, quindi il flag e' vero per costruzione.

    E' la regola R7 applicata a una dichiarazione invece che a una misura: il
    difetto non e' il numero, e' la statistica scelta per raccontarlo. Il test
    inchioda le UNITA', non il flag: se un giorno la fonte normalizzasse le due
    colonne alla stessa scala, questo diventa rosso e la discordanza va
    ri-valutata sul serio.
    """
    p1 = pd.to_numeric(sq["Ball possession (SofaScore)"], errors="coerce").dropna()
    p2 = pd.to_numeric(sq["possession (WhoScored)"], errors="coerce").dropna()
    assert p1.max() <= 100, "SofaScore dovrebbe essere una percentuale"
    assert p2.min() > 100, "WhoScored dovrebbe essere un conteggio, non una percentuale"
    assert "possesso" in tf.DISCORDANZE_FALSE


def test_la_discordanza_sui_corner_e_invece_vera(sq):
    """Il contro-esempio che dimostra che il resto delle dichiarazioni regge.

    Il file marca `corner` su 18 righe. Ri-calcolata in modo indipendente
    (SofaScore contro `cornersTotal` di WhoScored, che e' la colonna omogenea)
    escono **le stesse 18**, tutte a −1. Qui il confronto e' fra grandezze
    confrontabili e la dichiarazione e' affidabile.

    Serve a impedire la conclusione sbagliata «le Discordanze del file non sono
    attendibili»: una lo e' meno, le altre si', e la differenza e' misurabile.
    """
    a = pd.to_numeric(sq["Corner kicks (SofaScore)"], errors="coerce")
    tot = pd.to_numeric(sq["cornersTotal (WhoScored)"], errors="coerce")
    divergenti = (a != tot) & a.notna() & tot.notna()
    marcate = sq["Discordanze"].fillna("").str.contains("corner")
    assert divergenti.sum() == 18
    assert (divergenti == marcate).all(), "il file marca esattamente le righe divergenti"


def test_discordanze_esclude_le_false_per_default(sq):
    """Il default e' «solo quelle vere»: contarle tutte gonfia il rumore.

    Con `possesso` dentro, il livello squadra dichiara 760 righe discordanti su
    762 — un tasso che farebbe sembrare la raccolta inutilizzabile. Senza, ne
    restano 18.
    """
    vere = tf.discordanze_squadra()
    tutte = tf.discordanze_squadra(includi_false=True)
    assert len(vere) == 18, f"attese 18 discordanze vere, {len(vere)}"
    assert len(tutte) == 760


# --------------------------------------------------------------------------
# LA SECONDA LEGA — il momento in cui si vede se il modulo generalizza
# --------------------------------------------------------------------------
@pytest.mark.parametrize("lega,snapshot", [
    ("serie_a", "data/serie_a_matches.csv"),
    ("premier_league", "data/premier_league_matches.csv"),
])
def test_ogni_lega_aggancia_le_sue_760_squadra_partita(lega, snapshot):
    """760/760 su entrambe. E' la misura che dice se la raccolta e' usabile.

    Sulla Premier ha richiesto UN alias nuovo: SofaScore scrive
    «Wolverhampton», il nostro snapshot «Wolves», e `TEAM_ALIASES` aveva solo
    «Wolverhampton Wanderers». Le altre 19 squadre passavano gia'.
    """
    s = tf.squadre(lega, periodo="Totale")
    snap = pd.read_csv(snapshot)
    snap = snap[snap["season"].astype(str) == "2526"]
    d = pd.to_datetime(snap["date"]).dt.date
    attese = set(zip(d, snap["home_team"])) | set(zip(d, snap["away_team"]))
    nostre = set(zip(pd.to_datetime(s["Data"]).dt.date, s["Squadra"]))
    assert len(attese) == 760
    assert nostre == attese, f"{lega}: {len(attese - nostre)} squadra-partita non agganciate"


@pytest.mark.parametrize("lega", ["serie_a", "premier_league"])
def test_ogni_lega_ha_lid_partita_misto_rinominato(lega):
    """Il difetto che SI ripete: presente su entrambe le leghe.

    Serie A 436 valori distinti per 380 partite, Premier 384. Diverso in
    grandezza, identico in natura — a differenza delle righe orfane, che sono
    un incidente della sola Serie A.
    """
    g = tf.giocatori(lega)
    assert tf.ID_AVVELENATO not in g.columns
    assert tf.ID_RINOMINATO in g.columns
    for col in tf.ID_PARTITA_PER_FONTE.values():
        assert g[col].nunique() == 380


def test_le_righe_orfane_NON_si_ripetono_in_premier():
    """Il difetto che NON si ripete, ed e' un'informazione.

    In Serie A la fusione «Verona»/«Hellas Verona» lascia 2 righe orfane; in
    Premier le righe «Totale» sono 760 esatte e nessuna e' senza avversario.
    Quindi non e' un difetto sistematico dell'export ma un incidente su un
    nome: la riparazione resta per-lega e non va promossa a regola.
    """
    assert "premier_league" not in tf.ORFANE
    s = tf.squadre("premier_league", periodo="Totale")
    assert len(s) == 760
    assert s["Avversario"].notna().all()


def test_meteo_e_vuota_in_serie_a_e_piena_in_premier():
    """Il caso che ha imposto `colonne_vuote` PER LEGA invece che costante.

    `Meteo (WhoScored)` e' allo 0,0% in Serie A e al 95,9% in Premier: non e'
    un difetto dell'export ma una copertura diversa della fonte. Trattarla
    come costante avrebbe fatto scartare un dato buono su una lega per un buco
    che stava sull'altra.
    """
    sa = tf.squadre("serie_a", periodo="Totale")
    pl = tf.squadre("premier_league", periodo="Totale")
    assert sa["Meteo (WhoScored)"].isna().all()
    assert pl["Meteo (WhoScored)"].notna().mean() > 0.9
    assert "squadre" in tf.colonne_vuote("serie_a")
    assert "squadre" not in tf.colonne_vuote("premier_league")


def test_lallineamento_dei_gol_e_una_regola_non_una_lista():
    """Su Premier corregge 3 righe che nessuno aveva elencato a mano.

    E' il senso della riscrittura: una lista di eccezioni per (data,giocatore)
    sarebbe girata sulla Premier correggendo ZERO righe e senza dire niente —
    un silenzio indistinguibile da «qui non ci sono difetti».
    """
    assert int(tf.giocatori("serie_a")["gol_corretto_da_noi"].sum()) == 2
    assert int(tf.giocatori("premier_league")["gol_corretto_da_noi"].sum()) == 3


def test_un_file_non_ancora_consegnato_da_un_errore_che_lo_dice():
    """Le consegne arrivano a pezzi: l'errore deve dire QUALE pezzo manca.

    Un FileNotFoundError generico manderebbe a cercare un bug dove c'e' solo un
    file che deve ancora arrivare. La Premier e' stata senza `heatmap` per
    un'ora, ed e' il caso che ha imposto il messaggio esplicito.
    """
    with pytest.raises(FileNotFoundError, match="non ha ancora|nessuna raccolta"):
        tf.heatmap("bundesliga")


@pytest.mark.parametrize("lega,righe", [("serie_a", 556996), ("premier_league", 573203)])
def test_la_heatmap_c_e_su_entrambe_le_leghe_e_aggancia(lega, righe):
    """380 partite per lega, schema identico, e `Tocchi` vuota su ENTRAMBE.

    Il fatto che `Tocchi` sia al 100% NaN su due leghe indipendenti dice che e'
    una colonna del FORMATO mai riempita, non un incidente di una consegna —
    distinzione che con una lega sola non si poteva fare.
    """
    h = tf.heatmap(lega)
    assert len(h) == righe
    assert h["ID partita"].nunique() == 380
    assert h["Tocchi"].isna().all()
