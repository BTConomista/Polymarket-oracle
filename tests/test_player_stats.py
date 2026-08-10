"""Test del primo dato "Tier B" del progetto (diretta.it, Serie A 2025-26).

Due famiglie di test, con scopi diversi:
1. **guardiani dei dati** — la copertura e le identita' aritmetiche che il
   report di verifica del 31/07/2026 dichiara. Se il file cambia sotto i piedi
   devono rompersi qui, non dentro un backtest;
2. **guardiani della regola R8** — che `team_form()` non guardi mai la partita
   in corso. E' l'errore piu' facile e piu' difficile da vedere di tutto il
   fronte: il numero sarebbe giusto, sbagliato sarebbe il MOMENTO.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.data import player_stats as ps


@pytest.fixture(scope="module")
def pm() -> pd.DataFrame:
    return ps.load_player_matches("serie_a", "2526")


@pytest.fixture(scope="module")
def manifesto() -> dict:
    """La copertura attesa NON e' piu' incisa nel codice: sta nel manifesto
    della raccolta, cosi' aggiungere una lega non richiede di toccare `src/`."""
    r = [x for x in ps.raccolte() if x["lega"] == "serie_a" and x["stagione"] == "2526"]
    assert r, "raccolta serie_a/2526 non registrata"
    return r[0]


# --------------------------------------------------------------------------
# 1 · Guardiani dei dati
# --------------------------------------------------------------------------

def test_copertura_attesa(pm, manifesto):
    assert len(pm) == manifesto["righe_attese"] == 11894
    assert (pm.groupby(["data", "Squadra", "Avversario"]).ngroups
            == manifesto["team_partita_attesi"] == 758)
    assert pm["Squadra"].nunique() == manifesto["squadre"] == 20
    # la lega e la stagione viaggiano col dato: servono quando le raccolte
    # saranno piu' di una (altre 4 leghe, poi coppe e nazionali)
    assert set(pm["lega"]) == {"serie_a"} and set(pm["stagione"]) == {"2526"}


def test_ogni_raccolta_ha_il_suo_manifesto():
    """Una raccolta senza manifesto e' invisibile al caricatore: e' voluto —
    meglio ignorare una cartella incompleta che caricarla senza guardie."""
    for r in ps.raccolte():
        for chiave in ("lega", "stagione", "righe_attese", "team_partita_attesi", "fonte"):
            assert chiave in r, f"manifesto di {r.get('cartella')} senza '{chiave}'"


def test_raccolta_inesistente_alza_con_elenco():
    with pytest.raises(KeyError, match="Disponibili"):
        ps.load_player_matches("lega_che_non_esiste", "9999")


def test_load_strict_alza_se_la_copertura_cambia(pm, monkeypatch):
    """La guardia deve essere rumorosa: meglio fallire che restituire meno righe.

    Si simula un file troncato: `strict=True` deve alzare, `strict=False` no.
    """
    troncato = pm.drop(columns=["data", "lega", "stagione"]).head(100)
    monkeypatch.setattr(ps, "_read", lambda path: troncato)

    with pytest.raises(ValueError, match="righe giocatore-partita"):
        ps.load_player_matches("serie_a", "2526", strict=True)

    assert len(ps.load_player_matches("serie_a", "2526", strict=False)) == 100


def test_load_strict_alza_se_mancano_team_partita(pm, manifesto, monkeypatch):
    """Il conteggio righe può tornare mentre i team-partita no: va visto lo stesso.

    La soglia viene dal MANIFESTO, non da una costante nel codice: e' la
    differenza che permette di aggiungere una lega senza toccare `src/`.
    """
    meta = manifesto["righe_attese"] // 2
    doppio = pd.concat([pm.drop(columns=["data", "lega", "stagione"]).head(meta)] * 2)
    monkeypatch.setattr(ps, "_read", lambda path: doppio)
    with pytest.raises(ValueError, match="team-partita"):
        ps.load_player_matches("serie_a", "2526", strict=True)


def test_esattamente_undici_titolari(pm):
    """Identita' §1 del report di verifica: 379/379 partite, 11 titolari a testa."""
    t = pm[pm["Titolare/Subentrato"].str.strip().str.lower() == "titolare"]
    per_squadra = t.groupby(["data", "Squadra"]).size()
    assert set(per_squadra.unique()) == {11}


def test_nessuna_riga_duplicata(pm):
    assert not pm.duplicated(subset=["Giornata", "Squadra", "Giocatore"]).any()


def test_valori_dentro_i_range_fisici(pm):
    assert pm["Minuti giocati"].between(1, 120).all()
    for col in [c for c in pm.columns if "(%)" in c]:
        v = pm[col].dropna()
        assert v.between(0, 100).all(), f"{col} fuori da 0-100"


def test_minuti_bassi_solo_con_espulsione(pm):
    """§1 del report: 43 squadra-partita sotto 985', TUTTE con un rosso.

    E' un test di *significato*, non di forma: un totale minuti basso senza
    espulsione sarebbe un dato mancante travestito da dato pieno (regola R6).
    """
    agg = pm.groupby(["data", "Squadra"], as_index=False).agg(
        minuti=("Minuti giocati", "sum"),
        rossi=("Cartellini rossi", "sum"),
        doppi_gialli=("Secondo cartellino giallo", "sum"),
    )
    bassi = agg[agg["minuti"] < 985]
    assert len(bassi) == 43
    assert ((bassi["rossi"] + bassi["doppi_gialli"]) > 0).all()


def test_coerenza_gol_col_nostro_snapshot(pm):
    """Il controllo piu' forte: la fonte regge contro football-data.co.uk.

    `gol dei giocatori + autogol degli avversari == risultato dello snapshot`,
    su ogni squadra-partita. Le due fonti sono indipendenti.
    """
    j = ps.join_to_snapshot(pm)
    per_team = j.groupby(["data", "Squadra", "in_casa"], as_index=False).agg(
        gol=("Gol", "sum"), home_goals=("home_goals", "first"),
        away_goals=("away_goals", "first"),
    )
    autogol = (
        pm.groupby(["data", "Avversario"], as_index=False)["Autogol"].sum()
        .rename(columns={"Avversario": "Squadra", "Autogol": "autogol_avversari"})
    )
    per_team = per_team.merge(autogol, on=["data", "Squadra"], how="left").fillna(
        {"autogol_avversari": 0}
    )
    reali = per_team["home_goals"].where(per_team["in_casa"], per_team["away_goals"])
    assert (per_team["gol"] + per_team["autogol_avversari"] == reali).all()


def test_join_allo_snapshot_e_totale(pm):
    """Un join che perde righe in silenzio e' un bug gia' pagato dal progetto."""
    j = ps.join_to_snapshot(pm)
    assert len(j) == len(pm)
    assert j["home_team"].notna().all()


def test_la_partita_mancante_e_solo_quella_dichiarata(pm):
    """Como e Lecce hanno 37 partite, non 38 — e nessun altro."""
    partite = pm.groupby("Squadra")["data"].nunique()
    assert set(partite[partite == 37].index) == {"Como", "Lecce"}
    assert (partite.drop(["Como", "Lecce"]) == 38).all()


def test_colonne_tier_b_presenti_e_piene(pm):
    """Le righe della checklist §1.9 che il piano dava per irraggiungibili."""
    tier_b = [
        "Palloni toccati", "Passaggi totali", "Passaggi riusciti",
        "Dribbling tentati", "Dribbling riusciti", "Contrasti",
        "Palle intercettate", "Palloni recuperati", "Falli commessi",
        "Falli subiti", "Goal previsti (xG)", "Assist previsti (xA)",
        "Grandi occasioni create",
    ]
    for c in tier_b:
        assert c in pm.columns, f"colonna Tier B assente: {c}"
        assert pm[c].notna().all(), f"colonna Tier B con buchi: {c}"


# --------------------------------------------------------------------------
# 2 · Guardiani della regola R8 (anti look-ahead)
# --------------------------------------------------------------------------

def test_team_form_non_guarda_la_partita_in_corso(pm):
    """IL test che conta. Se `team_form` includesse la partita corrente, il
    numero sarebbe giusto e il modello inservibile.

    Verifica diretta: per una squadra, la media dichiarata alla partita k deve
    coincidere con la media calcolata a mano sulle partite 0..k-1, e NON con
    quella su 0..k.
    """
    col = "Palloni toccati"
    forma = ps.team_form(pm, columns=[col], window=5)
    grezzo = (
        pm.groupby(["data", "Squadra"], as_index=False)[col].sum()
        .sort_values(["Squadra", "data"])
    )
    squadra = "Inter"
    g = grezzo[grezzo["Squadra"] == squadra].reset_index(drop=True)
    f = forma[forma["Squadra"] == squadra].sort_values("data").reset_index(drop=True)
    nome = f"{col} (media 5 prec.)"

    for k in (1, 5, 10, 20):
        atteso = g[col].iloc[max(0, k - 5):k].mean()
        assert f[nome].iloc[k] == pytest.approx(atteso), (
            f"partita {k}: la media non è quella delle sole partite precedenti"
        )
        incluso = g[col].iloc[max(0, k - 4):k + 1].mean()
        if atteso != pytest.approx(incluso):
            assert f[nome].iloc[k] != pytest.approx(incluso), (
                f"partita {k}: LOOK-AHEAD — la media include la partita in corso"
            )


def test_team_form_prima_partita_e_nan(pm):
    """Nessuna squadra ha un 'prima' alla prima giornata: deve uscire NaN,
    non zero. Uno zero qui sarebbe un finto pieno (regola R6)."""
    forma = ps.team_form(pm, columns=["Palloni toccati"], window=5)
    prime = forma.sort_values("data").groupby("Squadra").head(1)
    assert prime["Palloni toccati (media 5 prec.)"].isna().all()


def test_team_form_alza_su_colonna_inesistente(pm):
    with pytest.raises(KeyError):
        ps.team_form(pm, columns=["Colonna Che Non Esiste"])


def test_le_statistiche_sono_tutte_post(pm):
    """Documentale ma vincolante: nessuna colonna `pre` deve finire per errore
    nell'elenco delle statistiche, e viceversa."""
    stats = set(ps.statistic_columns(pm))
    assert not stats & set(ps.PRE_COLUMNS)
    assert not stats & set(ps.STATIC_COLUMNS)
    assert "Palloni toccati" in stats and "Goal previsti (xG)" in stats


# --------------------------------------------------------------------------
# 3 · Bundesliga 2025-26 (Fase 138): la prima raccolta con FASE e con i
#     quattro fogli di contorno. Ogni test qui sotto inchioda una cosa
#     misurata durante la verifica della consegna, non un'intenzione.
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def bl() -> pd.DataFrame:
    """Bundesliga, solo campionato (il default)."""
    return ps.load_player_matches("bundesliga", "2526")


@pytest.fixture(scope="module")
def bl_tutto() -> pd.DataFrame:
    """Bundesliga, spareggio compreso."""
    return ps.load_player_matches("bundesliga", "2526", solo_campionato=False)


def test_bundesliga_lo_spareggio_e_fuori_dal_campionato(bl, bl_tutto):
    """Lo spareggio promozione/retrocessione NON e' campionato.

    Wolfsburg-Paderborn (andata 21/05, ritorno 25/05) sono 2 partite vere, ma
    non stanno negli snapshot e non contano per la classifica: mescolarle al
    campionato gonfierebbe ogni conteggio di 2 partite e farebbe comparire una
    19ª squadra (il Paderborn, che gioca in 2. Bundesliga).
    """
    assert "Fase" in bl_tutto.columns
    assert set(bl_tutto["Fase"]) == {"Campionato", "Spareggio"}
    assert set(bl["Fase"]) == {"Campionato"}

    assert bl.groupby(["data", "Squadra", "Avversario"]).ngroups == 612
    assert bl_tutto.groupby(["data", "Squadra", "Avversario"]).ngroups == 616
    assert bl["Squadra"].nunique() == 18
    assert bl_tutto["Squadra"].nunique() == 19          # + Paderborn
    assert len(bl) == 9555 and len(bl_tutto) == 9617


def test_bundesliga_il_manifesto_scompone_le_due_fasi(manifesto_bl):
    """`righe_attese` conta il FILE (guardia sul disco), gli altri due contano
    le due fasi. Se non tornassero, il file e il manifesto racconterebbero due
    storie diverse e nessuno saprebbe quale credere."""
    m = manifesto_bl
    assert m["righe_attese"] == 9617
    assert m["righe_campionato"] + m["righe_fuori_campionato"] == m["righe_attese"]
    assert m["team_partita_attesi"] == 612 and m["partite_attese"] == 306
    assert m["join_snapshot"] == "612/612" and m["snapshot_verificato"] is True


@pytest.fixture(scope="module")
def manifesto_bl() -> dict:
    r = [x for x in ps.raccolte()
         if x["lega"] == "bundesliga" and x["stagione"] == "2526"]
    assert r, "raccolta bundesliga/2526 non registrata"
    return r[0]


def test_bundesliga_join_totale_e_lo_spareggio_alza(bl, bl_tutto):
    """Il join dev'essere totale sul campionato — e deve ALZARE sullo spareggio.

    Non e' un difetto: e' la guardia che fa il suo mestiere. Le 62 righe dello
    spareggio non hanno una partita corrispondente in `data/bundesliga_matches.csv`
    perche' quella partita, in campionato, non e' mai stata giocata.
    """
    j = ps.join_to_snapshot(bl)
    assert len(j) == len(bl)
    assert j["home_team"].notna().all()
    with pytest.raises(ValueError, match="non agganciate"):
        ps.join_to_snapshot(bl_tutto)


def test_fase_non_e_una_statistica(bl):
    """`Fase` e' un'etichetta di competizione. Contarla fra le statistiche
    farebbe dichiarare 99 misure dove ne esistono 98 (97 Opta + il rating), e
    il manifesto erediterebbe il numero sbagliato."""
    assert "Fase" not in ps.statistic_columns(bl)
    assert len(ps.statistic_columns(bl)) == 98


def test_gol_concessi_e_una_statistica_individuale(bl):
    """⚠️ `Gol concessi` NON e' il totale di squadra ripetuto su ogni riga: e'
    quanti gol ha preso la squadra **mentre quel giocatore era in campo**.

    E' la trappola piu' facile di questo dataset — la colonna e' piena per tutti
    e dieci i ruoli, portieri compresi, e sommarla sulla rosa da' un numero che
    *sembra* i gol subiti moltiplicati per undici, perche' e' esattamente quello.
    Il controllo giusto e' sui soli portieri, e li' torna esatto.
    """
    bl = bl.copy()
    bl["subiti"] = bl["Risultato squadra"].str.split("-").map(lambda v: int(v[1]))
    chiave = ["data", "Squadra", "Avversario"]

    por = bl[bl["Ruolo"] == "Portiere"].groupby(chiave)["Gol concessi"].sum()
    veri = bl.groupby(chiave)["subiti"].first()
    assert (por == veri).all(), "somma sui portieri != gol subiti"

    tutti = bl.groupby(chiave)["Gol concessi"].sum()
    rapporto = (tutti / veri.replace(0, float("nan"))).dropna()
    assert 10.0 <= rapporto.mean() <= 11.0
    assert rapporto.max() <= 11.0      # non piu' di 11 in campo per gol


def test_i_cartellini_di_squadra_si_ricompongono_da_quelli_individuali(bl):
    """⭐ L'identita' esatta fra le due viste della stessa fonte.

        gialli(squadra) = Σ gialli(in campo) + 2 × Σ secondi_gialli + gialli in panchina

    Il «2 ×» e' la convenzione di Opta: a chi viene espulso per doppia
    ammonizione le statistiche individuali NON registrano il primo giallo —
    tengono solo il flag `Secondo cartellino giallo` e il rosso. La pagina di
    squadra invece conta tutti i cartellini **mostrati**.

    Misurato: l'identita' (senza il terzo addendo) torna su **606/612**
    squadra-partita. Dei 6 residui, **5** sono un giallo a un giocatore mai
    entrato — verificati uno per uno nel foglio Formazioni, `Stato = "Non
    entrato"` — e **1** e' una divergenza vera fra le due pagine del sito.
    Senza questo test la divergenza sembrerebbe un errore di estrazione.
    """
    from src.data import team_stats

    ts = team_stats.load_team_matches(lega="bundesliga", stagione="2526")
    ts = ts[ts["Periodo"] == "Totale"].set_index(["data", "Squadra"])

    a = bl.groupby(["data", "Squadra"])[
        ["Cartellini gialli", "Secondo cartellino giallo"]].sum()
    j = a.join(ts[["Cartellini gialli"]].rename(
        columns={"Cartellini gialli": "squadra"}), how="inner")
    ricostruito = j["Cartellini gialli"] + 2 * j["Secondo cartellino giallo"]

    assert len(j) == 612
    assert int((ricostruito == j["squadra"]).sum()) == 606
    residui = (ricostruito - j["squadra"]).loc[ricostruito != j["squadra"]]
    assert sorted(residui.value_counts().to_dict().items()) == [(-1.0, 5), (1.0, 1)]

    # e i 5 residui negativi hanno davvero un ammonito rimasto in panchina
    form = ps.load_lineups("bundesliga", "2526")
    ev = ps.load_events("bundesliga", "2526")
    for (data, squadra) in residui[residui < 0].index:
        gialli = ev[(ev["data"] == data) & (ev["Squadra"] == squadra)
                    & ev["Evento"].astype(str).str.contains("Giallo")]
        in_campo = set(bl[(bl["data"] == data) & (bl["Squadra"] == squadra)]["Giocatore"])
        fuori = [g for g in gialli["Giocatore"].dropna().unique() if g not in in_campo]
        assert fuori, f"{data} {squadra}: nessun ammonito fuori dal campo"
        stati = form[(form["data"] == data) & (form["Squadra"] == squadra)
                     & form["Giocatore"].isin(fuori)]["Stato"]
        assert (stati == "Non entrato").any(), f"{data} {squadra}: {stati.tolist()}"


def test_i_fogli_di_contorno_ci_sono_e_dicono_chi_li_ha(bl):
    """I quattro fogli nuovi si caricano; chiederli a una raccolta che non li
    ha alza un errore che ELENCA chi li ha, invece di restituire un vuoto —
    che sarebbe indistinguibile da «non e' successo niente» (regola R6)."""
    assert len(ps.load_match_list("bundesliga", "2526")) == 308
    assert len(ps.load_lineups("bundesliga", "2526")) == 12299
    assert len(ps.load_substitutions("bundesliga", "2526")) == 2884
    assert len(ps.load_events("bundesliga", "2526")) == 2261

    with pytest.raises(FileNotFoundError, match="bundesliga/2526"):
        ps.load_events("serie_a", "2526")


def test_le_formazioni_contengono_chi_non_e_entrato(bl):
    """E' l'unico foglio che vede la panchina: senza, i cartellini ai non
    entrati resterebbero inspiegabili (vedi il test dell'identita')."""
    form = ps.load_lineups("bundesliga", "2526")
    assert set(form["Stato"]) >= {"Titolare", "Subentrato", "Non entrato"}
    assert (form["Stato"] == "Non entrato").sum() > 0
    # chi e' sceso in campo sta in entrambi i fogli; chi non e' entrato solo qui
    scesi = set(zip(bl["data"], bl["Squadra"], bl["Giocatore"]))
    non_entrati = form[form["Stato"] == "Non entrato"]
    fuori = set(zip(non_entrati["data"], non_entrati["Squadra"], non_entrati["Giocatore"]))
    assert not (scesi & fuori), "un giocatore non puo' essere insieme in campo e non entrato"


def test_la_cronaca_eventi_e_dichiaratamente_incompleta(bl):
    """⚠️ Il foglio Eventi e' la cronaca REDAZIONALE del sito, non un tracciato.

    Elenca 887 gol piu' 20 autogol = 907, contro i **990** realmente segnati in
    campionato piu' spareggio. Il test lo inchioda apposta: serve a impedire
    che qualcuno, un domani, la usi per CONTARE. Per contare ci sono le
    statistiche individuali, che tornano esatte (test sopra).
    """
    ev = ps.load_events("bundesliga", "2526")
    in_cronaca = int(ev["Evento"].astype(str).isin(["Gol", "Autogol"]).sum())
    bl = bl.copy()
    bl["fatti"] = bl["Risultato squadra"].str.split("-").map(lambda v: int(v[0]))
    veri = int(bl.groupby(["data", "Squadra", "Avversario"])["fatti"].first().sum())
    assert veri == 990
    assert in_cronaca < veri, "se la cronaca fosse completa questo test va aggiornato"
    assert in_cronaca == 907
