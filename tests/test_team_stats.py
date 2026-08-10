"""Test delle statistiche di SQUADRA per periodo (diretta.it, 5 leghe 2025-26).

Tre famiglie di test, con scopi diversi:
1. **guardiani dei dati** — copertura, schema e identita' aritmetiche che la
   verifica del 01/08/2026 ha misurato. Se un file cambia sotto i piedi devono
   rompersi qui, non dentro un backtest;
2. **guardiani della semantica** — le tre cose che si sbagliano leggendo questi
   file: le righe di spareggio scambiate per campionato, il vuoto scambiato per
   dato mancante, `Risultato squadra` scambiato per il punteggio del periodo;
3. **guardiani della regola R8** — che `team_form()` non guardi mai la partita
   in corso. E' l'errore piu' facile e piu' difficile da vedere: il numero
   sarebbe giusto, sbagliato sarebbe il MOMENTO.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.data import player_stats as ps
from src.data import team_stats as ts

LEGHE = ("serie_a", "premier_league", "la_liga", "bundesliga", "ligue_1")


@pytest.fixture(scope="module")
def tm() -> pd.DataFrame:
    """Tutte e 5 le raccolte, sole righe di campionato (il default)."""
    return ts.load_team_matches(tutte=True)


@pytest.fixture(scope="module")
def manifesti() -> dict:
    return {r["lega"]: r for r in ts.raccolte_squadra()}


# --------------------------------------------------------------------------
# 1 · Guardiani dei dati
# --------------------------------------------------------------------------

def test_le_cinque_raccolte_sono_registrate(manifesti):
    assert set(manifesti) == set(LEGHE)
    for lega, m in manifesti.items():
        for chiave in ("lega", "stagione", "fonte", "righe_attese",
                       "team_partita_attesi", "snapshot_verificato"):
            assert chiave in m, f"manifesto di {lega} senza '{chiave}'"
        assert m["stagione"] == "2526"
        assert m["fonte"] == "diretta.it (Flashscore)"


def test_copertura_attesa(tm, manifesti):
    """1.752 partite di campionato: 380x3 leghe da 20 squadre + 306x2 da 18."""
    attesi = {"serie_a": 760, "premier_league": 760, "la_liga": 760,
              "bundesliga": 612, "ligue_1": 612}
    for lega, n in attesi.items():
        d = tm[tm["lega"] == lega]
        assert d.groupby(["data", "Squadra", "Avversario"]).ngroups == n
        assert manifesti[lega]["team_partita_attesi"] == n
        # tre periodi ordinari per ogni squadra-partita
        assert len(d) == 3 * n
    assert tm.groupby(["lega", "data", "Squadra", "Avversario"]).ngroups == 3504
    assert len(tm) == 10512


def test_schema_identico_tra_le_leghe(tm):
    """I 5 file consegnati avevano QUATTRO ordini di colonna diversi.

    La normalizzazione allo schema canonico e' il motivo per cui questo test
    esiste: il repo garantisce lo schema identico fra leghe (stessa scelta gia'
    fatta per gli snapshot), e senza la normalizzazione la garanzia cadeva.
    """
    attese = list(ts.COLONNE_CANONICHE)
    for lega in LEGHE:
        cols = [c for c in tm[tm["lega"] == lega].columns if c in ts.COLONNE_CANONICHE]
        assert cols == attese, f"{lega}: ordine colonne diverso dal canonico"
    assert len(ts.COLONNE_METRICHE) == 45


def test_calendario_completo_e_senza_duplicati(tm):
    for lega in LEGHE:
        tot = tm[(tm["lega"] == lega) & (tm["Periodo"] == ts.PERIODO_TOTALE)]
        squadre = sorted(set(tot["Squadra"]))
        casa = tot[tot["Campo"] == "Casa"]
        coppie = list(zip(casa["Squadra"], casa["Avversario"]))
        # round-robin: ogni coppia ordinata esattamente una volta
        assert len(coppie) == len(set(coppie)) == len(squadre) * (len(squadre) - 1)
        # meta' in casa e meta' fuori, per ogni squadra
        per_squadra = tot.groupby(["Squadra", "Campo"]).size().unstack()
        assert (per_squadra["Casa"] == per_squadra["Trasferta"]).all()
        assert not tot.duplicated(subset=["data", "Squadra"]).any()


def test_additivita_dei_periodi(tm):
    """1T + 2T = Totale sulle metriche di CONTEGGIO.

    Le percentuali e il possesso sono esclusi apposta: sono rapporti e medie,
    non conteggi, e sommarli sarebbe l'errore che il test dovrebbe impedire.
    """
    additive = [c for c in ts.COLONNE_METRICHE if c not in ts.COLONNE_NON_ADDITIVE]
    chiave = ["lega", "data", "Squadra", "Avversario"]
    tempi = tm[tm["Periodo"] != ts.PERIODO_TOTALE].groupby(chiave)[additive].sum()
    totale = tm[tm["Periodo"] == ts.PERIODO_TOTALE].set_index(chiave)[additive]
    diff = (tempi - totale).abs()
    assert int((diff > 0.005).sum().sum()) == 0
    assert diff.size == 3504 * len(additive)
    # ⚠️ Zero violazioni comprende ANCHE la partita col 2 tempo mancante, e non
    # per fortuna: li' il `Totale` e' troncato al primo tempo esattamente come
    # la somma dei periodi, quindi l'identita' torna su un dato incompleto.
    # E' il motivo per cui l'additivita' NON basta a certificare la copertura,
    # e il buco ha un test suo (test_la_partita_incompleta_e_solo_quella_dichiarata).


def test_percentuali_non_sono_additive(tm):
    """Controllo di segno opposto: se un giorno lo diventassero, il dato e'
    cambiato. Serve a evitare che qualcuno «sistemi» il test precedente
    aggiungendo le percentuali all'elenco delle additive."""
    chiave = ["lega", "data", "Squadra", "Avversario"]
    col = "Possesso palla %"
    tempi = tm[tm["Periodo"] != ts.PERIODO_TOTALE].groupby(chiave)[col].sum()
    totale = tm[tm["Periodo"] == ts.PERIODO_TOTALE].set_index(chiave)[col]
    assert (tempi - totale).abs().median() > 10


def test_possesso_somma_a_cento(tm):
    p = tm.dropna(subset=["Possesso palla %"])
    somma = p.groupby(["lega", "data", "Periodo",
                       p[["Squadra", "Avversario"]].min(axis=1)])["Possesso palla %"].sum()
    assert (somma == 100).all()


def test_range_fisici(tm):
    for c in ts.COLONNE_NON_ADDITIVE:
        v = tm[c].dropna()
        fuori = v[~v.between(0, 100)]
        # due sole righe sfondano il 100%, ed e' un'incoerenza della FONTE
        # fissata dal test successivo: qui si controlla che non ce ne siano altre
        assert c == "Tackles %" or fuori.empty, f"{c} fuori da [0,100]"
        assert len(fuori) <= 2, f"{c}: {len(fuori)} valori fuori da [0,100]"
    conteggi = [c for c in ts.COLONNE_METRICHE
                if c not in ts.COLONNE_NON_ADDITIVE
                and not any(k in c for k in ("xG", "xA", "Gol evitati", "xGot"))]
    for c in conteggi:
        v = tm[c].dropna()
        assert (v >= 0).all() and (v == v.round()).all(), f"{c} non e' un conteggio"


# --------------------------------------------------------------------------
# 2 · Guardiani della semantica (le tre cose che si sbagliano)
# --------------------------------------------------------------------------

def test_i_tackles_impossibili_sono_solo_quei_due(tm):
    """`Tackles riusciti` (4) > `Tackles totali` (3) -> 133%, in 2 righe su 10.512.

    Incoerenza della fonte, non nostra: la percentuale e' calcolata sui conteggi
    sbagliati, quindi e' coerente con essi. Non la correggiamo (regola R3: mai
    modifiche a mano al dato) e non la nascondiamo (R4: si dichiara anche
    quando e' innocua). Il test la fissa perche' se ne comparissero altre
    sarebbe un cambiamento della fonte, non piu' un caso isolato.
    """
    b = tm[tm["Tackles riusciti"] > tm["Tackles totali"]]
    assert len(b) == 2
    assert set(b["Squadra"]) == {"Barcelona", "Napoli"}
    assert (b["Tackles %"] == 133).all()
    # nelle altre quattro famiglie riusciti/totali l'incoerenza non esiste.
    # ⚠️ `dropna` non e' cosmetico: sulla riga senza 2 tempo il confronto
    # NaN <= NaN e' False e farebbe fallire il test su una violazione che non
    # c'e'. E' lo stesso inciampo del vuoto scambiato per dato.
    for base, tot in (("Cross riusciti", "Cross totali"),
                      ("Passaggi riusciti", "Passaggi totali"),
                      ("Passaggi lunghi riusciti", "Passaggi lunghi totali"),
                      ("Passaggi offensivi riusciti", "Passaggi offensivi totali")):
        v = tm[[base, tot]].dropna()
        assert (v[base] <= v[tot]).all(), f"{base} > {tot}"


def test_le_partite_di_spareggio_sono_escluse_di_default(tm):
    """Bundesliga e Ligue 1 contengono spareggi con club di 2a divisione, che
    NON sono campionato e non hanno riscontro negli snapshot."""
    assert set(tm["Fase"]) == {"Stagione regolare"}
    for lega, squadre_po in (("ligue_1", {"Red Star", "Rodez", "St. Etienne"}),
                             ("bundesliga", {"Paderborn"})):
        d = tm[tm["lega"] == lega]
        assert not (set(d["Squadra"]) & squadre_po)
        assert not (set(d["Avversario"]) & squadre_po)
        # ...ma con il flag ci sono, e restano dichiarate dalla colonna Fase
        completo = ts.load_team_matches(lega, "2526", solo_campionato=False)
        assert set(completo["Fase"]) == {"Stagione regolare", "Play-off"}
        assert set(completo[completo["Fase"] == "Play-off"]["Squadra"]) >= squadre_po


def test_il_totale_della_bundesliga_include_i_supplementari():
    """La fonte dichiara il CONTRARIO nel proprio foglio Note, e sbaglia.

    Lo spareggio di ritorno del 25/05/2026 e' l'unica partita con i tempi
    supplementari. Se il `Totale` NON li includesse, 1T+2T dovrebbe pareggiare
    il Totale: non lo fa, e 1T+2T+Suppl si'. E' un errore della DOCUMENTAZIONE
    della fonte, non del dato (regola R4: si dichiara comunque).
    """
    d = ts.load_team_matches("bundesliga", "2526", solo_campionato=False)
    suppl = d[d["Periodo"] == ts.PERIODO_SUPPL]
    assert len(suppl) == 2
    partita = d[d["data"] == suppl["data"].iloc[0]]
    additive = [c for c in ts.COLONNE_METRICHE if c not in ts.COLONNE_NON_ADDITIVE]
    for squadra in suppl["Squadra"]:
        r = partita[partita["Squadra"] == squadra].set_index("Periodo")[additive]
        con = r.loc[ts.PERIODO_1T] + r.loc[ts.PERIODO_2T] + r.loc[ts.PERIODO_SUPPL]
        senza = r.loc[ts.PERIODO_1T] + r.loc[ts.PERIODO_2T]
        totale = r.loc[ts.PERIODO_TOTALE]
        # tolleranza sui float: le metriche continue (xG, xGOT, xA) sommano a
        # meno di un ulp, non a zero esatto
        assert ((con - totale).abs() <= 0.005).all(), "coi supplementari deve tornare"
        quante = int(((senza - totale).abs() <= 0.005).sum())
        assert quante < len(additive) / 2, f"senza supplementari tornano {quante}/{len(additive)}"


def test_il_vuoto_e_uno_zero_non_un_dato_mancante():
    """Dimostrato contro football-data; qui si fissa la semantica del loader.

    Caricare i vuoti come mancanti non farebbe sparire dei cartellini: farebbe
    sparire gli ZERI, gonfiando ogni media per partita. Il test misura proprio
    quella differenza, invece di limitarsi a contare i NaN.
    """
    pieno = ts.load_team_matches("serie_a", "2526")
    grezzo = ts.load_team_matches("serie_a", "2526", zeri_espliciti=False)
    for c in ts.COLONNE_ZERO_IMPLICITO:
        assert pieno[c].isna().sum() == 0
        assert grezzo[c].isna().sum() > 0
        # la somma non cambia (i vuoti valgono zero)...
        assert pieno[c].sum() == grezzo[c].sum()
        # ...ma la media si', ed e' il punto
        assert pieno[c].mean() < grezzo[c].mean()


def test_risultato_squadra_e_di_fine_partita_non_del_periodo(tm):
    """R8: colonna `post` incollata su righe che sembrano descrivere un periodo.

    E' identica nelle tre righe, quindi la riga «1° tempo» porta il risultato
    FINALE. Chi la usasse come punteggio all'intervallo starebbe leggendo il
    futuro. Il punteggio all'intervallo NON e' in questo dataset.
    """
    per_periodo = tm.groupby(["lega", "data", "Squadra"])["Risultato squadra"].nunique()
    assert (per_periodo == 1).all()
    assert "Risultato squadra" in ts.POST_COLUMNS
    assert "Risultato squadra" not in ts.PRE_COLUMNS


def test_risultato_squadra_e_dal_punto_di_vista_della_riga(tm):
    """Invertito sulla riga di trasferta: leggerlo come casa-ospite sbaglierebbe
    il segno su tutte le partite non pareggiate."""
    tot = tm[tm["Periodo"] == ts.PERIODO_TOTALE]
    coppia = tot.groupby(["lega", "data",
                          tot[["Squadra", "Avversario"]].min(axis=1)])["Risultato squadra"]
    non_pari = [g for _, g in coppia if g.iloc[0].split("-")[0] != g.iloc[0].split("-")[1]]
    assert non_pari, "nessuna partita non pareggiata: dato sospetto"
    for g in non_pari:
        a, b = g.iloc[0].split("-"), g.iloc[1].split("-")
        assert a == b[::-1], "le due righe non sono specchiate"


def test_la_partita_incompleta_e_solo_quella_dichiarata():
    """Nantes-Toulouse 17/05/2026: la riga `Totale` copre 22 MINUTI, non 90.

    La partita fu interrotta definitivamente al 22' per invasione di campo e la
    LFP omologo' lo 0-0 (`docs/DATI.md` §1-quater). Il secondo tempo non manca:
    non e' mai stato giocato, e infatti football-data riporta gli stessi
    22 minuti. Il dato e' CORRETTO — la trappola e' d'uso: mettere quel `Totale`
    in media con partite da 90' mescola durate diverse. E' la R6 applicata al
    TEMPO invece che al valore. Il test la fissa: se comparissero altre righe
    cosi', non sarebbero piu' un caso isolato spiegato.
    """
    tutte = ts.load_team_matches(tutte=True)
    non_sparse = [c for c in ts.COLONNE_METRICHE if c not in ts.COLONNE_ZERO_IMPLICITO]
    buche = tutte[tutte[non_sparse].isna().any(axis=1)]
    assert len(buche) == 2
    assert set(buche["Squadra"]) == {"Nantes", "Toulouse"}
    assert set(buche["Data"]) == {"17.05.2026"}
    assert set(buche["Periodo"]) == {ts.PERIODO_2T}

    d = ts.load_team_matches("ligue_1", "2526")
    m = d[(d["Data"] == "17.05.2026") & (d["Squadra"] == "Nantes")].set_index("Periodo")
    assert (m.loc[ts.PERIODO_TOTALE, list(ts.COLONNE_METRICHE)]
            == m.loc[ts.PERIODO_1T, list(ts.COLONNE_METRICHE)]).all()


# --------------------------------------------------------------------------
# 3 · Controllo forte: contro una fonte INDIPENDENTE (i nostri snapshot)
# --------------------------------------------------------------------------

def test_join_allo_snapshot_e_totale():
    """Gli snapshot vengono da football-data.co.uk: fonte diversa da diretta.it.

    Senza i 18 alias italiani il join si fermava a 264/612 (Ligue 1) e 60/612
    (Bundesliga): e' esattamente il caso per cui TEAM_ALIASES esiste.
    """
    for lega in LEGHE:
        d = ts.load_team_matches(lega, "2526")
        agganciato = ts.join_to_snapshot(d)   # alza se anche una riga resta orfana
        assert len(agganciato) == len(d)
        assert agganciato["home_team"].notna().all()


def test_risultato_coerente_con_lo_snapshot():
    for lega in LEGHE:
        d = ts.load_team_matches(lega, "2526")
        j = ts.join_to_snapshot(d[d["Periodo"] == ts.PERIODO_TOTALE])
        propri = j["Risultato squadra"].str.split("-").str[0].astype(int)
        attesi = j["home_goals"].where(j["in_casa"], j["away_goals"]).astype(int)
        assert (propri == attesi).all(), f"{lega}: risultato discorde"


def test_join_alza_sulle_partite_di_spareggio():
    """Non hanno riscontro nello snapshot — sono di seconda divisione — e il
    join deve fallire rumorosamente invece di restituire righe orfane."""
    d = ts.load_team_matches("bundesliga", "2526", solo_campionato=False)
    with pytest.raises(ValueError, match="non agganciate"):
        ts.join_to_snapshot(d)


def test_gol_dedotti_possono_solo_sottostimare():
    """Gli autogol non entrano nell'xGOT di chi ne beneficia, quindi la
    deduzione sbaglia sempre in difetto. Misurato: mai +1, solo -1 o -2."""
    d = ts.load_team_matches("serie_a", "2526")
    tot = ts.join_to_snapshot(d[d["Periodo"] == ts.PERIODO_TOTALE])
    subiti_veri = tot["away_goals"].where(tot["in_casa"], tot["home_goals"])
    scarto = ts.gol_dedotti(tot) - subiti_veri
    assert (scarto <= 0).all(), "la deduzione non puo' sovrastimare"
    assert (scarto == 0).mean() > 0.90


# --------------------------------------------------------------------------
# 4 · Guardiani della regola R8 (anti look-ahead)
# --------------------------------------------------------------------------

def test_team_form_non_guarda_la_partita_in_corso():
    """Il test piu' importante del file.

    Se `team_form` guardasse la partita in corso il numero sarebbe *giusto* e
    il modello inservibile. Si verifica che la media alla partita k coincida
    con quella calcolata a mano su 0..k-1 e NON con quella su 0..k.
    """
    d = ts.load_team_matches("serie_a", "2526")
    col = "Tiri totali"
    forma = ts.team_form(d, columns=[col], window=5)
    nome = f"{col} (media 5 prec.)"

    squadra = sorted(set(d["Squadra"]))[0]
    storia = (d[(d["Squadra"] == squadra) & (d["Periodo"] == ts.PERIODO_TOTALE)]
              .sort_values("data")[col].tolist())
    f = forma[forma["Squadra"] == squadra].sort_values("data")[nome].tolist()

    for k in range(1, len(storia)):
        precedenti = storia[max(0, k - 5):k]
        atteso = sum(precedenti) / len(precedenti)
        assert abs(f[k] - atteso) < 1e-9, f"partita {k}: guarda oltre le precedenti"
        incluso = storia[max(0, k - 4):k + 1]
        sbagliato = sum(incluso) / len(incluso)
        if abs(sbagliato - atteso) > 1e-9:
            assert abs(f[k] - sbagliato) > 1e-9, f"partita {k}: include la partita in corso"


def test_team_form_prima_partita_e_nan():
    d = ts.load_team_matches("serie_a", "2526")
    forma = ts.team_form(d, columns=["Tiri totali"], window=5)
    prime = forma.sort_values("data").groupby("Squadra").head(1)
    assert prime["Tiri totali (media 5 prec.)"].isna().all()


def test_team_form_sul_primo_tempo():
    """La ragion d'essere del dataset: la forma del solo primo tempo."""
    d = ts.load_team_matches("serie_a", "2526")
    f1 = ts.team_form(d, columns=["Tiri totali"], window=5, periodo=ts.PERIODO_1T)
    ftot = ts.team_form(d, columns=["Tiri totali"], window=5)
    assert len(f1) == len(ftot)
    c = "Tiri totali (media 5 prec.)"
    assert f1[c].mean() < ftot[c].mean()


def test_team_form_alza_su_colonna_inesistente():
    with pytest.raises(KeyError):
        ts.team_form(ts.load_team_matches("serie_a", "2526"), columns=["Non esiste"])


def test_le_statistiche_sono_tutte_post(tm):
    assert set(ts.statistic_columns(tm)) == set(ts.COLONNE_METRICHE)
    assert not set(ts.COLONNE_METRICHE) & set(ts.PRE_COLUMNS)


# --------------------------------------------------------------------------
# 5 · Convivenza col dato per GIOCATORE (stessa cartella, dataset diversi)
# --------------------------------------------------------------------------

def test_non_rompe_il_caricatore_per_giocatore():
    """I due dataset vivono nella stessa cartella e non devono vedersi.

    Una cartella che ha **solo** il dato di squadra non deve comparire fra le
    raccolte per giocatore: se `player_stats` la scoprisse,
    `load_player_matches(tutte=True)` fallirebbe su un file che non c'e'. Il
    manifesto separato (`manifesto_squadra.json`) e' cio' che lo impedisce.

    Il test non incide piu' l'elenco delle leghe (lo faceva, e alla Fase 145 e'
    diventato falso il giorno in cui la **Bundesliga** ha avuto anche il dato
    per giocatore). Verifica la PROPRIETA': `player_stats` vede tutte e sole le
    cartelle che hanno davvero il file per giocatore. Oggi l'unica con il solo
    dato di squadra e' la Ligue 1, e il test lo scopre invece di saperlo.
    """
    per_squadra = {r["lega"] for r in ts.raccolte_squadra()}
    per_giocatore = {r["lega"] for r in ps.raccolte()}
    assert per_giocatore <= per_squadra

    for r in ts.raccolte_squadra():
        ha_il_file = (r["cartella"] / ps.FILE_PARTITE).exists()
        assert ha_il_file == (r["lega"] in per_giocatore), (
            f"{r['lega']}: file per giocatore {'presente' if ha_il_file else 'assente'} "
            f"ma la raccolta {'non ' if ha_il_file else ''}e' visibile a player_stats")

    # e il caricamento cumulativo funziona davvero, senza esplodere sulle
    # cartelle che il file per giocatore non ce l'hanno
    tutte = ps.load_player_matches(tutte=True)
    assert set(tutte["lega"]) == per_giocatore
    assert len(tutte) == sum(r["righe_campionato"] if "righe_campionato" in r
                             else r["righe_attese"] for r in ps.raccolte())


def test_periodi_affiancati():
    d = ts.load_team_matches("serie_a", "2526")
    w = ts.periodi_affiancati(d, columns=["Tiri totali"])
    assert len(w) == 760
    assert (w["Tiri totali (1T)"] + w["Tiri totali (2T)"]
            == w["Tiri totali (Totale)"]).all()


def test_raccolta_inesistente_alza_con_elenco():
    with pytest.raises(KeyError, match="Disponibili"):
        ts.load_team_matches("lega_che_non_esiste", "9999")


def test_load_strict_alza_se_la_copertura_cambia(monkeypatch):
    vero = ts._raccolta

    def finto(lega, stagione):
        r = dict(vero(lega, stagione))
        r["righe_attese"] = 1
        return r

    monkeypatch.setattr(ts, "_raccolta", finto)
    with pytest.raises(ValueError, match="attese 1 righe"):
        ts.load_team_matches("serie_a", "2526")


def test_le_incoerenze_aritmetiche_minori_sono_solo_quelle(tm):
    """Tre scostamenti della fonte, trovati riconciliando dopo l'inserimento.

    Nessuno è corretto (R3) e nessuno è nascosto (R4). Il test li fissa: se il
    conteggio cresce, la fonte è cambiata e va riguardata.
    """
    # (a) delle DUE partizioni dei tiri, una chiude sempre e l'altra no
    perfetta = tm["Tiri totali"] - (tm["Tiri in porta"] + tm["Tiri fuori"] + tm["Tiri fermati"])
    assert int((perfetta.dropna() != 0).sum()) == 0

    zona = tm["Tiri totali"] - (tm["Tiri dall'area di rigore"] + tm["Tiri da fuori area"])
    assert int((zona.dropna() != 0).sum()) == 10

    # (b) xGot affrontati di A deve essere l'xGOT di B: 4 righe non tornano
    m = tm.merge(tm, left_on=["lega", "data", "Squadra", "Periodo"],
                 right_on=["lega", "data", "Avversario", "Periodo"], suffixes=("", "_avv"))
    d = (m["xGot affrontati"] - m["xG sui Tiri in porta (xGOT)_avv"]).dropna()
    assert int((d.abs() > 1e-9).sum()) == 4

    # (c) `Falli` e `Punizioni` sono la STESSA quantità vista dai due lati:
    #     identità esatta, e serve da controprova che il merge qui sopra è sano
    f = (m["Falli"] - m["Punizioni_avv"]).dropna()
    assert int((f.abs() > 1e-9).sum()) == 0


# --------------------------------------------------------------------------
# 6 · I gol all'intervallo negli snapshot (Fase 133)
# --------------------------------------------------------------------------

def test_gol_intervallo_presenti_e_coerenti():
    """`home_goals_ht`/`away_goals_ht` esistono su tutte e 5 le leghe.

    Sono il dato che mancava al modello a due stadi (pista 6-bis) e che questo
    dataset NON contiene (`Risultato squadra` e' il finale anche sulla riga
    «1° tempo»). Vengono da football-data.co.uk, la stessa fonte da cui gli
    snapshot derivano gia' i gol finali.
    """
    import pandas as pd
    from src.data import database

    totale_ht = totale = 0
    for lega in LEGHE:
        s = pd.read_csv(database.snapshot_path(lega))
        assert {"home_goals_ht", "away_goals_ht"} <= set(s.columns), lega
        h, a = s["home_goals_ht"], s["away_goals_ht"]
        v = s.dropna(subset=["home_goals_ht", "away_goals_ht"])
        # un intervallo non puo' avere piu' gol del finale
        assert (v["home_goals_ht"] <= v["home_goals"]).all(), lega
        assert (v["away_goals_ht"] <= v["away_goals"]).all(), lega
        assert (v["home_goals_ht"] >= 0).all() and (v["away_goals_ht"] >= 0).all()
        totale_ht += int(v["home_goals_ht"].sum() + v["away_goals_ht"].sum())
        totale += int(v["home_goals"].sum() + v["away_goals"].sum())

    # f = frazione di gol nel 1 tempo. La Fase 96 misurava 0.4396
    # [0.4338, 0.4458] su 3 leghe; su 5 leghe e 9 stagioni deve restare li'.
    f = totale_ht / totale
    assert 0.43 < f < 0.46, f"frazione 1T fuori scala: {f}"


def test_l_unico_intervallo_mancante_e_quello_dichiarato():
    """Union Berlin-Bochum 14/12/2024: la fonte non ha l'intervallo.

    E' la partita del caso R1 (1-1 sul campo, 0-2 dal tribunale DFB): il
    nostro snapshot porta il risultato del campo, football-data quello del
    tribunale e **nessun intervallo**. Il valore resta vuoto invece di essere
    inventato (R3): un buco dichiarato e' innocuo, il finto pieno no (R6).
    """
    import pandas as pd
    from src.data import database

    buchi = []
    for lega in LEGHE:
        s = pd.read_csv(database.snapshot_path(lega))
        b = s[s[["home_goals_ht", "away_goals_ht"]].isna().any(axis=1)]
        buchi += [(lega, r.date, r.home_team, r.away_team) for r in b.itertuples()]
    assert buchi == [("bundesliga", "2024-12-14", "Union Berlin", "Bochum")]


def test_ogni_raccolta_conserva_l_originale():
    """Regola §5-ter del CLAUDE.md: si conserva il file COME CONSEGNATO.

    Per tre leghe su cinque il CSV di lavoro l'abbiamo prodotto noi dall'.xlsx:
    senza l'originale, un bug nella nostra conversione sarebbe indistinguibile
    dal dato. Il test verifica che l'originale ci sia — non che sia leggibile
    (aprirlo qui costerebbe secondi a ogni esecuzione della suite; la fedelta'
    e' verificata al momento della registrazione).
    """
    for r in ts.raccolte_squadra():
        orig = r["cartella"] / "originale_squadra.xlsx"
        assert orig.is_file(), f"{r['lega']}: manca l'originale consegnato"
        assert orig.stat().st_size > 100_000, f"{r['lega']}: originale sospettosamente piccolo"
