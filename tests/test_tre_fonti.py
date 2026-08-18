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
@pytest.mark.parametrize("lega", ["serie_a", "premier_league", "la_liga", "bundesliga", "ligue_1"])
def test_ogni_lega_aggancia_TUTTE_le_sue_squadra_partita(lega):
    """Il totale NON e' 760 per tutte: Bundesliga e Ligue 1 ne hanno 612.

    Inchiodare 760 avrebbe fatto passare la Bundesliga per rotta quando era
    solo piu' piccola — 18 squadre, 306 partite. `DIMENSIONI` tiene i due
    formati, e il test confronta col numero della LEGA.

    Ogni lega ha richiesto i suoi alias: «Wolverhampton» in Premier,
    «1. FC Heidenheim» e «Borussia M'gladbach» in Bundesliga.
    """
    squadre_attese, partite_attese = tf.DIMENSIONI[lega]
    s = tf.squadre(lega, periodo="Totale")
    snap = pd.read_csv(f"data/{lega}_matches.csv")
    snap = snap[snap["season"].astype(str) == "2526"]
    d = pd.to_datetime(snap["date"]).dt.date
    attese = set(zip(d, snap["home_team"])) | set(zip(d, snap["away_team"]))
    nostre = set(zip(pd.to_datetime(s["Data"]).dt.date, s["Squadra"]))
    assert len(attese) == partite_attese * 2
    assert s["Squadra"].nunique() == squadre_attese
    assert nostre == attese, f"{lega}: {len(attese - nostre)} squadra-partita non agganciate"


@pytest.mark.parametrize("lega", ["serie_a", "premier_league", "la_liga", "bundesliga", "ligue_1"])
def test_ogni_lega_ha_lid_partita_misto_rinominato(lega):
    """Il difetto che SI ripete: presente su entrambe le leghe.

    Serie A 436 valori distinti per 380 partite, Premier 384. Diverso in
    grandezza, identico in natura — a differenza delle righe orfane, che sono
    un incidente della sola Serie A.
    """
    g = tf.giocatori(lega)
    assert tf.ID_AVVELENATO not in g.columns
    assert tf.ID_RINOMINATO in g.columns
    partite = tf.DIMENSIONI[lega][1]
    for col in tf.ID_PARTITA_PER_FONTE.values():
        assert g[col].nunique() == partite, f"{lega}/{col}: {g[col].nunique()} invece di {partite}"


def test_le_righe_orfane_NON_si_ripetono_fuori_dalla_serie_a():
    """Il difetto che NON si ripete, ed e' un'informazione.

    In Serie A la fusione «Verona»/«Hellas Verona» lascia 2 righe orfane; in
    Premier le righe «Totale» sono 760 esatte e nessuna e' senza avversario.
    Quindi non e' un difetto sistematico dell'export ma un incidente su un
    nome: la riparazione resta per-lega e non va promossa a regola.
    """
    for lega in ("premier_league", "la_liga", "bundesliga", "ligue_1"):
        assert lega not in tf.ORFANE
        s = tf.squadre(lega, periodo="Totale")
        attese = tf.DIMENSIONI[lega][1] * 2
        assert len(s) == attese, f"{lega}: {len(s)} righe invece di {attese}"
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
    attesi = {"serie_a": 2, "premier_league": 3, "la_liga": 4,
              "bundesliga": 2, "ligue_1": 2}
    for lega, n in attesi.items():
        assert int(tf.giocatori(lega)["gol_corretto_da_noi"].sum()) == n, lega


def test_un_file_non_ancora_consegnato_da_un_errore_che_lo_dice():
    """Le consegne arrivano a pezzi: l'errore deve dire QUALE pezzo manca.

    Un FileNotFoundError generico manderebbe a cercare un bug dove c'e' solo un
    file che deve ancora arrivare. La Premier e' stata senza `heatmap` per
    un'ora, ed e' il caso che ha imposto il messaggio esplicito.
    """
    with pytest.raises(FileNotFoundError, match="non ha ancora|nessuna raccolta"):
        tf.eventi_opta("uefa_conference_league")


@pytest.mark.parametrize("lega,righe", [("serie_a", 556996), ("premier_league", 573203), ("la_liga", 570768)])
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


def test_meteo_ha_TRE_stati_e_due_non_bastavano():
    """0,0% · 0,3% · 98,4%: e' la terza lega che ha rotto la dicotomia.

    Con Serie A (vuota) e Premier (piena) bastava un booleano. La Liga ha 2
    righe su 760 — ne' l'una ne' l'altra — e lo stato di mezzo e' il piu'
    insidioso dei tre: un `notna().any()` risponde «la colonna funziona» e chi
    ci costruisce sopra lavora su 2 righe credendone 760. E' finto pieno (R6)
    in miniatura, e una colonna a zero almeno si dichiara da sola.
    """
    stati = {L: tf.copertura("Meteo (WhoScored)", L)["stato"]
             for L in ("serie_a", "la_liga", "premier_league")}
    assert stati == {"serie_a": "vuota", "la_liga": "quasi vuota",
                     "premier_league": "piena"}, stati
    # E la conseguenza operativa: la Liga NON compare fra le "vuote", perche'
    # non lo e'. Dichiararla tale sarebbe falso quanto ignorarla.
    assert "squadre" in tf.colonne_vuote("serie_a")
    assert "squadre" not in tf.colonne_vuote("la_liga")


def test_tocchi_e_vuota_su_TUTTE_e_tre_e_quindi_e_del_formato():
    """La distinzione che con una lega sola non si poteva fare.

    Tre leghe indipendenti allo 0,0% dicono che `Tocchi` e' una colonna del
    FORMATO mai riempita, non l'incidente di una consegna.
    """
    for lega in ("serie_a", "premier_league", "la_liga", "bundesliga", "ligue_1"):
        assert tf.copertura("Tocchi", lega, blocco="heatmap")["stato"] == "vuota"


# --------------------------------------------------------------------------
# Il blocco arrivato SPEZZATO, e il difetto che il taglio nasconde
# --------------------------------------------------------------------------
def test_eventi_opta_della_liga_e_ricomposto_dalle_due_parti():
    """577.205 eventi da due file, e la partita a cavallo torna intera.

    Il taglio e' GREZZO, non logico: cade dentro Levante-Espanyol dell'11/01,
    166 eventi in parte1 (fino al 7' del primo tempo) e 1.327 in parte2, contro
    una mediana di 1.517 a partita. Chi leggesse una parte sola vedrebbe quella
    partita monca **senza che nulla glielo dica** — 166 e' un numero plausibile
    per una riga di dati, e nessun conteggio se ne accorge.
    """
    e = tf.eventi_opta("la_liga", colonne=["ID partita", "Minuto", "Periodo"])
    assert len(e) == 577205
    assert e["ID partita"].nunique() == 380

    tagliata = e[e["ID partita"] == 1914070]
    assert len(tagliata) == 1493, "la partita a cavallo del taglio non e' intera"
    assert set(tagliata["Periodo"]) >= {"FirstHalf", "SecondHalf"}
    mediana = e.groupby("ID partita").size().median()
    assert abs(len(tagliata) - mediana) < mediana * 0.3, "resta anomala per numero di eventi"


def test_percorso_alza_se_il_blocco_e_spezzato():
    """Chiedere UN file per un blocco in due parti deve fallire, non troncare.

    E' la guardia che impedisce di reintrodurre il difetto: `_percorso` esiste
    per i blocchi interi, `_percorsi`/`_leggi` per quelli spezzati. Prendere la
    prima parte e chiamarla «il file» perderebbe meta' della stagione in
    silenzio.
    """
    with pytest.raises(RuntimeError, match="in 2 parti"):
        tf._percorso("eventi_opta", "la_liga")
    assert len(tf._percorsi("eventi_opta", "la_liga")) == 2
    assert len(tf._percorsi("eventi_opta", "serie_a")) == 1


# --------------------------------------------------------------------------
# Due convenzioni di nome nello STESSO file
# --------------------------------------------------------------------------
def test_atletico_nudo_di_eventi_opta_viene_riportato_al_nome_intero():
    """`eventi_opta` della Liga scrive «Atletico» in Squadra e «Atlético Madrid» in Casa.

    Due convenzioni in due colonne dello stesso file. Effetto misurato prima
    della riparazione: eventi_opta agganciava 722/760 squadra-partita, e le 38
    mancanti erano tutte dell'Atletico — mentre le PARTITE agganciavano
    380/380, il che rendeva il difetto invisibile a un controllo per partita.

    ⚠️ L'alias sta in `ALIAS_RACCOLTA`, non in `sources.TEAM_ALIASES`: quella
    mappa e' globale al progetto e «Atletico» da solo e' ambiguo fuori dalla
    Liga (Mineiro, Nacional, decine di altri). Metterlo li' sarebbe un join che
    indovina.
    """
    assert "Atletico" not in __import__("src.data.sources", fromlist=["x"]).TEAM_ALIASES
    assert tf.ALIAS_RACCOLTA["la_liga"]["Atletico"] == "Atlético Madrid"
    e = tf.eventi_opta("la_liga", colonne=["Squadra"])
    assert "Atletico" not in set(e["Squadra"].dropna())
    assert "Ath Madrid" in set(e["Squadra"].dropna())


@pytest.mark.parametrize("lega", ["serie_a", "premier_league", "la_liga", "bundesliga", "ligue_1"])
def test_eventi_opta_aggancia_tutte_le_squadra_partita(lega):
    """La misura che ha scoperto DUE volte lo stesso difetto.

    La colonna `Squadra` di `eventi_opta` usa una forma che le altre colonne
    dello stesso file non usano: «Atletico» nudo in Liga, la sigla «RBL» in
    Bundesliga. Due leghe su quattro, sempre UNA squadra, sempre quella colonna.
    ⚠️ L'aggancio per PARTITA resta perfetto in entrambi i casi, quindi solo il
    controllo per squadra-partita lo rivela.
    """
    snap = pd.read_csv(f"data/{lega}_matches.csv")
    snap = snap[snap["season"].astype(str) == "2526"]
    d = pd.to_datetime(snap["date"]).dt.date
    attese = set(zip(d, snap["home_team"])) | set(zip(d, snap["away_team"]))
    e = tf.eventi_opta(lega, colonne=["Data", "Squadra"])
    nostre = {x for x in zip(pd.to_datetime(e["Data"]).dt.date, e["Squadra"].astype(str))
              if x[1] != "nan"}
    assert nostre >= attese, f"{lega}: {len(attese - nostre)} squadra-partita senza eventi"


def test_id_evento_NON_e_una_chiave_univoca():
    """44-82 ID ripetuti per lega, e ci sono anche nei file NON spezzati.

    Quindi non e' un effetto della ricomposizione: e' una proprieta' del dato.
    Parte dei doppioni sta dentro la stessa partita, parte fra partite diverse.
    Chi usasse `ID evento` come chiave primaria perderebbe righe in silenzio —
    e questo test esiste perche' nessuno lo faccia credendolo sicuro.
    """
    for lega, attesi in (("serie_a", 45), ("premier_league", 82), ("la_liga", 44),
                         ("bundesliga", 79), ("ligue_1", 42),
                         ("uefa_europa_league", 199)):
        e = tf.eventi_opta(lega, colonne=["ID evento"])
        assert e["ID evento"].duplicated().sum() == attesi, lega


# --------------------------------------------------------------------------
# LA QUARTA LEGA — 18 squadre, e due partite che non sono di campionato
# --------------------------------------------------------------------------
def test_lo_spareggio_e_fuori_per_default():
    """4 righe di Wolfsburg-Paderborn che nei nostri snapshot NON esistono.

    Sono lo spareggio promozione/retrocessione contro una squadra di seconda
    divisione, marcate `Turno == "Finale"`. Tenerle dentro fa due danni: porta
    il conteggio a 616 dove le squadra-partita di campionato sono 612, e tira
    dentro una 19a squadra (Paderborn) che nel campionato non c'e'.

    E' la stessa convenzione di `player_stats.load_player_matches`, che le
    esclude per default con la colonna `Fase`. Qui `Fase` non c'e' e il
    marcatore e' `Turno`.
    """
    senza = tf.squadre("bundesliga", periodo="Totale")
    con = tf.squadre("bundesliga", periodo="Totale", spareggio=True)
    assert len(senza) == 612 and senza["Squadra"].nunique() == 18
    assert len(con) == 616 and con["Squadra"].nunique() == 19
    assert "Paderborn" in set(con["Squadra"]) and "Paderborn" not in set(senza["Squadra"])


def test_in_bundesliga_lo_spareggio_e_un_turno_solo():
    """Un turno in Bundesliga, TRE in Ligue 1: per questo la regola non e' una costante.

    La prima stesura inchiodava `Turno == "Finale"`, che qui basta e sulla
    Ligue 1 no. Il test tiene il fatto per la Bundesliga, e quello sulla
    Ligue 1 tiene il contro-esempio che ha imposto la regola generale.
    """
    s = tf.squadre("bundesliga", periodo="Totale", spareggio=True)
    fuori = {t for t in s["Turno"].dropna().unique()
             if not str(t).startswith(tf.PREFISSO_GIORNATA)}
    assert fuori == {"Finale"}


def test_la_bundesliga_ha_la_colonna_che_ripara_il_possesso_a_monte():
    """La quarta consegna aggiunge `possession % (normalizzato)`, e funziona.

    Fino alla Liga il file marcava «possesso» come discordanza su 760 righe su
    760 — un falso positivo, perche' confrontava una percentuale con un
    conteggio. Qui l'export aggiunge la colonna normalizzata, e la discordanza
    dichiarata scende da 760 a **2**: il difetto e' stato chiuso A MONTE.

    ⚠️ Il test verifica che la colonna sia DAVVERO una percentuale confrontabile
    (610 righe su 612 entro 1 punto da SofaScore), non solo che esista: una
    colonna col nome giusto e i valori sbagliati sarebbe peggio di nessuna.
    """
    s = tf.squadre("bundesliga", periodo="Totale")
    assert "possession % (normalizzato) (WhoScored)" in s.columns
    a = pd.to_numeric(s["Ball possession (SofaScore)"], errors="coerce")
    b = pd.to_numeric(s["possession % (normalizzato) (WhoScored)"], errors="coerce")
    vicine = ((a - b).abs() <= 1).sum()
    assert vicine >= 600, f"solo {vicine}/612 righe entro 1 punto: la colonna non e' comparabile"
    # E la conseguenza: quasi nessuna discordanza dichiarata sul possesso.
    marcate = s["Discordanze"].fillna("").str.contains("possesso").sum()
    assert marcate <= 5, f"{marcate} righe ancora marcate: il falso positivo non e' chiuso"


# ==========================================================================
# LA QUINTA LEGA, E LE PRIME DUE COMPETIZIONI CHE NON SONO CAMPIONATI
# ==========================================================================
def test_lo_spareggio_francese_e_a_TRE_turni_non_uno():
    """La costante `Turno == "Finale"` ne avrebbe preso un quarto.

    In Bundesliga lo spareggio e' un turno solo (2 partite). In Ligue 1 sono
    TRE — «1° turno preliminare», «2° turno preliminare», «Finale» — per 4
    partite in totale. Inchiodare «Finale» avrebbe lasciato dentro 3 squadre di
    Ligue 2 e portato il conteggio a 616 invece di 612.

    Da cui la regola: in un CAMPIONATO, tutto cio' che non e' «Giornata N» e'
    spareggio. Il test inchioda che i turni fuori schema siano piu' di uno,
    cosi' nessuno torni a una costante.
    """
    con = tf.squadre("ligue_1", periodo="Totale", spareggio=True)
    fuori = {t for t in con["Turno"].dropna().unique()
             if not str(t).startswith(tf.PREFISSO_GIORNATA)}
    assert len(fuori) == 3, f"attesi 3 turni di spareggio, trovati {fuori}"
    senza = tf.squadre("ligue_1", periodo="Totale")
    assert len(senza) == 612 and senza["Squadra"].nunique() == 18
    assert len(con) == 620 and con["Squadra"].nunique() == 21


@pytest.mark.parametrize("uefa", ["uefa_europa_league", "uefa_conference_league"])
def test_nelle_uefa_non_si_esclude_nessun_turno(uefa):
    """Qui i turni fuori schema SONO la competizione, non uno spareggio.

    «3° turno preliminare», «Ottavi di finale», «Spareggi di knockout»:
    applicare la regola dei campionati butterebbe meta' del torneo. Da cui
    `E_CAMPIONATO`, che e' False per le UEFA.
    """
    assert tf.E_CAMPIONATO[uefa] is False
    a = tf.squadre(uefa, periodo="Totale")
    b = tf.squadre(uefa, periodo="Totale", spareggio=True)
    assert len(a) == len(b) > 0


def test_le_uefa_non_hanno_tutte_e_tre_le_fonti():
    """Understat non copre le coppe europee, e non e' un difetto.

    Chiamare «a tre fonti» una raccolta che ne ha una sarebbe un finto pieno
    nel nome. `fonti(lega)` dice quali ci sono davvero, e le colonne delle
    fonti assenti NON esistono — chiederle da' KeyError, non NaN.
    """
    assert tf.fonti("serie_a") == ("SofaScore", "WhoScored", "Understat")
    assert tf.fonti("uefa_europa_league") == ("SofaScore", "WhoScored")
    assert tf.fonti("uefa_conference_league") == ("SofaScore",)
    e = tf.squadre("uefa_europa_league", periodo="Totale")
    assert "xG (Understat)" not in e.columns
    c = tf.squadre("uefa_conference_league", periodo="Totale")
    assert "ratings (WhoScored)" not in c.columns


def test_il_punteggio_delle_uefa_somma_la_lotteria_dei_rigori():
    """`Gol casa (SofaScore)` legge «6» dove il campo ha detto 1.

    Omonia-Wolfsberger del 28/08/2025: 1-1 sul campo, 5 rigori. La colonna
    normale somma i due. E' lo stesso difetto che il CLAUDE.md documenta per
    games.csv sulle coppe nazionali — li' e' costato una ricostruzione.

    ⭐ Qui l'export lo DICHIARA con le colonne derivate, e `punteggio_vero()`
    le usa. Il test verifica che la differenza esista davvero: se un giorno la
    colonna normale smettesse di sommare, andrebbe aggiornata la
    documentazione, non ignorato il rosso.
    """
    s = tf.squadre("uefa_conference_league", periodo="Totale")
    ai_rigori = s["Decisa ai rigori (derivata)"] == "si"
    assert ai_rigori.sum() // 2 == 6, "attese 6 partite decise ai rigori"

    casa, _ = tf.punteggio_vero(s)
    sommato = pd.to_numeric(s.loc[ai_rigori, "Gol casa (SofaScore)"], errors="coerce")
    vero = pd.to_numeric(casa[ai_rigori], errors="coerce")
    assert (vero < sommato).all(), "il punteggio derivato dovrebbe essere piu' basso"
    # E nei campionati non c'e' lotteria: punteggio_vero torna la colonna normale.
    sa = tf.squadre("serie_a", periodo="Totale")
    c2, _ = tf.punteggio_vero(sa)
    assert c2.equals(sa["Gol casa (SofaScore)"])


def test_le_uefa_portano_le_nostre_squadre_in_europa():
    """E' la ragione per cui servono: 11 nostre squadre in EL, 5 in Conference.

    Non hanno uno snapshot a cui agganciarsi — sono competizioni, non
    campionati — quindi il criterio non e' «760/760» ma «quante delle nostre
    ci sono, e sotto che nome».
    """
    from src.data.sources import TEAM_ALIASES
    nostre = set()
    for lega in [x for x in tf.DIMENSIONI if tf.ha_snapshot(x)]:
        s = pd.read_csv(f"data/{lega}_matches.csv")
        s = s[s["season"].astype(str) == "2526"]
        nostre |= set(s["home_team"]) | set(s["away_team"])

    for uefa, attese in (("uefa_europa_league", 11), ("uefa_conference_league", 5)):
        s = tf.squadre(uefa, periodo="Totale")
        sq = {TEAM_ALIASES.get(x, x) for x in s["Squadra"].dropna()}
        assert len(sq & nostre) == attese, f"{uefa}: {sorted(sq & nostre)}"


# --------------------------------------------------------------------------
# LE COPPE DELLA CONSEGNA 13/08/2026: Champions + sei supercoppe (Fase 155)
# --------------------------------------------------------------------------
SUPERCOPPE = ["supercoppa_uefa", "supercoppa_italiana", "supercopa_espana",
              "community_shield", "dfl_supercup", "trophee_des_champions"]


@pytest.mark.parametrize("chiave, partite", [
    ("supercoppa_uefa", 1), ("community_shield", 1), ("dfl_supercup", 1),
    ("trophee_des_champions", 1),
    ("supercoppa_italiana", 3), ("supercopa_espana", 3),   # final four
])
def test_ogni_supercoppa_ha_le_partite_che_dichiara(chiave, partite):
    """Due delle sei sono a FINAL FOUR, non a partita secca.

    Inchiodare «1 partita» avrebbe fatto sembrare rotte Supercoppa Italiana e
    Supercopa de España, che sono solo piu' grandi — stessa lezione della
    Bundesliga a 612 righe contro le 760 delle prime tre leghe.
    """
    assert tf.SUPERCOPPE[chiave] == partite
    s = tf.squadre(chiave, periodo="Totale")
    assert len(s) == partite * 2, f"{chiave}: {len(s)} righe per {partite} partite"


@pytest.mark.parametrize("chiave", SUPERCOPPE)
def test_nelle_supercoppe_il_punteggio_non_contiene_i_rigori(chiave):
    """Il TRIPWIRE: `Gol = 1T + 2T`, e quattro di queste partite sono ai rigori.

    Non e' una verifica di comodo. La stessa colonna, nelle raccolte di Europa
    League e Conference, **somma** la lotteria: «Partizan-AEK Larnaca 7-7» era
    2-1. Qui l'identita' regge su tutte, quindi il punteggio e' quello della
    partita e la serie finale sta nella sua colonna.

    ⚠️ Se una consegna futura contenesse i TEMPI SUPPLEMENTARI, questo test
    diventerebbe rosso **pur essendo il dato giusto** — i gol dei supplementari
    non stanno ne' nel 1T ne' nel 2T. In quel caso non si aggiusta il test: si
    guarda la partita e si scrive cosa e' successo (R5), come per la Champions,
    dove l'identita' giusta e' `Gol = 1T + 2T + suppl.`.
    """
    s = tf.squadre(chiave, periodo="Totale")
    ok = tf.gol_sono_regolamentari(s)
    assert ok.all(), f"{chiave}: {(~ok).sum()} righe dove Gol != 1T + 2T"


def test_la_champions_ha_i_supplementari_e_il_punteggio_resta_pulito():
    """La Champions e' l'unica coppa con supplementari GIOCATI e registrati.

    Ha tre colonne per i supplementari (`Casa suppl.`, `Casa 1° suppl.`,
    `Casa 2° suppl.`), 5 partite con gol nei supplementari e 4 decise ai
    rigori. L'identita' giusta e' quindi a tre addendi, e regge su 281/281.
    """
    s = tf.squadre("uefa_champions_league", periodo="Totale")
    s = s[s["Campo"] == "Casa"]
    def n(c):
        return pd.to_numeric(s[c], errors="coerce").fillna(0)
    casa = n("Casa 1T (SofaScore)") + n("Casa 2T (SofaScore)") + n("Casa suppl. (SofaScore)")
    via = (n("Trasferta 1T (SofaScore)") + n("Trasferta 2T (SofaScore)")
           + n("Trasferta suppl. (SofaScore)"))
    ok = (s["Gol casa (SofaScore)"] == casa) & (s["Gol trasferta (SofaScore)"] == via)
    assert len(s) == 281
    assert ok.all(), f"{(~ok).sum()} partite di Champions dove Gol != 1T+2T+suppl"
    # e ci sono davvero le partite ai rigori, altrimenti il test non prova nulla
    ai_rigori = pd.to_numeric(s[tf.COLONNE_RIGORI[0]], errors="coerce").notna()
    assert int(ai_rigori.sum()) == 4


def test_la_convenzione_sul_punteggio_e_per_raccolta_e_non_si_eredita():
    """⚠️ Il difetto che questo test esiste per impedire, in una riga.

    L'integrazione UEFA aveva ragionato per FILE: «la Conference dichiara le
    colonne derivate, quindi le raccolte UEFA sono coperte». Falso — l'Europa
    League ha lo stesso difetto e NON le dichiara, quindi `punteggio_vero()` le
    restituiva il punteggio gonfiato su 7 partite. E la Champions, stessa
    famiglia e stessa fonte, e' invece pulita: la convenzione **non si eredita**.
    """
    assert tf.RIGORI_NEL_PUNTEGGIO["uefa_europa_league"] is True
    assert tf.RIGORI_NEL_PUNTEGGIO["uefa_conference_league"] is True
    assert tf.RIGORI_NEL_PUNTEGGIO["uefa_champions_league"] is False
    for chiave in SUPERCOPPE:
        assert tf.RIGORI_NEL_PUNTEGGIO[chiave] is False, chiave


def test_partizan_aek_larnaca_era_2_1_non_7_7():
    """Il caso simbolo, con il numero prima e il numero dopo.

    `Gol casa/trasferta` legge 7-7 su una partita del 1° turno preliminare di
    Europa League. La riparazione la riporta a **2-1**, ed e' verificata contro
    i gol contati negli eventi (`scripts/_run_punteggio_coppe.py`).
    """
    s = tf.squadre("uefa_europa_league", periodo="Totale")
    r = s[(s["Data"] == "2025-07-17") & (s["Squadra"] == "FK Partizan")]
    assert len(r) == 1
    assert (r["Gol casa (SofaScore)"].iloc[0], r["Gol trasferta (SofaScore)"].iloc[0]) == (7, 7)
    casa, fuori = tf.punteggio_vero(r)
    assert (casa.iloc[0], fuori.iloc[0]) == (2, 1)


def test_la_riparazione_dei_rigori_non_tocca_chi_e_gia_pulito():
    """Applicarla alla Champions darebbe 1 − 4 = **−3** sulla finale.

    E' il motivo per cui `RIGORI_NEL_PUNTEGGIO` e' una tabella e non una
    regola: la sottrazione applicata dove non serve non e' innocua, produce
    punteggi negativi.
    """
    s = tf.squadre("uefa_champions_league", periodo="Totale")
    f = s[s["Turno"] == "Finale"]
    casa, fuori = tf.punteggio_vero(f)
    assert (casa.iloc[0], fuori.iloc[0]) == (1, 1)
    assert (casa >= 0).all() and (fuori >= 0).all()
    # le colonne derivate NON devono essere state aggiunte
    assert tf.COLONNE_PUNTEGGIO_VERO[0] not in s.columns


@pytest.mark.parametrize("chiave", SUPERCOPPE + ["uefa_champions_league"])
def test_le_colonne_dichiarate_vuote_lo_sono_davvero(chiave):
    """E il rovescio: nessuna colonna vuota resta fuori dalla dichiarazione.

    Le due direzioni misurano cose diverse. Una dichiarazione sbagliata per
    eccesso fa scartare un dato buono; una per difetto lascia credere che una
    colonna contenga qualcosa. Nelle supercoppe sono 41-43 colonne e la
    dichiarazione le copre tutte.
    """
    grezze = pd.read_csv(f"files/tre_fonti_{chiave}_2526/squadre.csv.gz", low_memory=False)
    dichiarate = set(tf.colonne_vuote(chiave).get("squadre", ()))
    vuote = {c for c in grezze.columns if grezze[c].isna().all()}
    assert dichiarate - vuote == set(), f"dichiarate vuote e non lo sono: {dichiarate - vuote}"
    assert vuote - dichiarate == set(), f"vuote e non dichiarate: {sorted(vuote - dichiarate)}"


def test_solo_la_supercoppa_uefa_e_la_champions_hanno_due_fonti():
    """Cinque supercoppe su sei arrivano con SofaScore soltanto.

    E portano lo stesso 19 colonne `(WhoScored)` vuote: lo schema le prevede.
    Chiedere «quante fonti» all'elenco delle colonne da' la risposta sbagliata,
    ed e' esattamente per questo che `fonti()` esiste.
    """
    assert tf.fonti("supercoppa_uefa") == ("SofaScore", "WhoScored")
    assert tf.fonti("uefa_champions_league") == ("SofaScore", "WhoScored")
    for chiave in SUPERCOPPE:
        if chiave == "supercoppa_uefa":
            continue
        assert tf.fonti(chiave) == ("SofaScore",), chiave
        g = pd.read_csv(f"files/tre_fonti_{chiave}_2526/squadre.csv.gz", low_memory=False)
        ws = [c for c in g.columns if "(WhoScored)" in c]
        assert ws, f"{chiave}: nessuna colonna WhoScored — lo schema e' cambiato"
        assert all(g[c].isna().all() for c in ws), f"{chiave}: WhoScored non e' vuota"


def test_le_supercoppe_sono_tutte_di_squadre_nostre():
    """Zero club fuori perimetro: e' la differenza con le coppe UEFA.

    Europa League e Conference portano soprattutto squadre che non modelliamo
    (66 su 77 in EL). Le supercoppe nazionali, per costruzione, no: ci giocano
    campione e vincitrice di coppa dello stesso campionato. Anche la Supercoppa
    UEFA 2025-26 lo e' — PSG e Tottenham sono entrambe nostre.
    """
    from src.data.sources import TEAM_ALIASES
    nostre = set()
    for lega in [x for x in tf.DIMENSIONI if tf.ha_snapshot(x)]:
        s = pd.read_csv(f"data/{lega}_matches.csv")
        s = s[s["season"].astype(str) == "2526"]
        nostre |= set(s["home_team"]) | set(s["away_team"])
    for chiave in SUPERCOPPE:
        s = tf.squadre(chiave, periodo="Totale")
        sq = {TEAM_ALIASES.get(x, x) for x in s["Squadra"].dropna()}
        assert sq <= nostre, f"{chiave}: fuori perimetro {sorted(sq - nostre)}"


def test_eventi_opta_della_supercoppa_uefa_usa_i_nomi_corti():
    """TERZA occorrenza dello stesso difetto, e la piu' estesa.

    La colonna `Squadra` di `eventi_opta` scrive «PSG» e «Tottenham» mentre
    `Casa`/`Trasferta` dello stesso file scrivono il nome intero — su 1.393
    righe su 1.393, cioe' il 100% (Liga 5%, Bundesliga 6%). Tre raccolte su
    quattro che hanno `eventi_opta` ce l'hanno: e' la regola, non l'eccezione.
    """
    assert tf.ALIAS_RACCOLTA["supercoppa_uefa"] == {
        "PSG": "Paris Saint-Germain", "Tottenham": "Tottenham Hotspur"}
    e = tf.eventi_opta("supercoppa_uefa")
    s = tf.squadre("supercoppa_uefa", periodo="Totale")
    assert set(e["Squadra"].dropna()) <= set(s["Squadra"].dropna())
