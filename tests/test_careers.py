"""Test del database CARRIERE, strato 1 (da `appearances.csv`).

Come per `test_player_stats.py`, due famiglie: guardiani dei numeri e
guardiani della regola R8. Qui i secondi contano ancora di più, perché
«presenze in carriera» è la feature che **per sua natura contiene il futuro**:
un test che si limitasse a controllare i totali passerebbe anche su un
calcolo palesemente look-ahead.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.data import careers as C


@pytest.fixture(scope="module")
def app() -> pd.DataFrame:
    return C._load_appearances()


@pytest.fixture(scope="module")
def careers(app) -> pd.DataFrame:
    """Il perimetro DEFAULT: tutto l'universo (29.531 giocatori)."""
    return C.load_careers(app)


@pytest.fixture(scope="module")
def careers_pop(app) -> pd.DataFrame:
    """Il sottoinsieme delle nostre 5 leghe (7.709 giocatori)."""
    return C.load_careers(app, only_population=True)


# --------------------------------------------------------------------------
# 1 · Guardiani dei numeri
# --------------------------------------------------------------------------

def test_popolazione(app):
    """7.709 giocatori con >=1 presenza nelle 5 leghe dal 2017-07."""
    pop = C.population(app)
    assert len(pop) == 7709
    assert pop.is_unique


def test_copertura(app):
    r = C.coverage_report(app)
    assert r["giocatori"] == 7709
    assert r["competizioni"] == 48           # non 5: e' la scoperta che regge lo strato 1
    assert r["con_presenze_fuori_top5"] == 6580
    assert r["censurati_a_sinistra"] == 1045
    assert r["senza_storia_precedente"] == 2875


def test_perimetro_default_e_tutto_luniverso(careers, careers_pop):
    """Decisione utente 31/07/2026: il database copre TUTTI i giocatori di
    TUTTE le 48 competizioni, non solo i nostri — cosi' allargarsi oltre le 5
    leghe un domani non richiede di ricostruire nulla."""
    assert careers["player_id"].nunique() == 29531
    assert careers["competition_id"].nunique() == 48
    assert careers["club_id"].nunique() == 1231
    assert len(careers) == 197812
    # e il filtro restringe davvero
    assert careers_pop["player_id"].nunique() == 7709
    assert len(careers_pop) == 89625
    assert set(careers_pop["player_id"]) <= set(careers["player_id"])


def test_struttura_carriere(careers):
    assert (careers["appearances"] > 0).all()
    assert (careers["date_to"] >= careers["date_from"]).all()
    assert (careers["fonte"] == C.FONTE_STRATO1).all()
    # una riga e' univoca per giocatore x club x competizione x stagione
    assert not careers.duplicated(
        subset=["player_id", "club_id", "competition_id", "season"]
    ).any()


def test_ogni_riga_dichiara_la_fonte(careers):
    """Regola R2 a livello di RIGA: quando arrivera' lo strato 2 (Wikipedia)
    si dovra' poter distinguere una tappa misurata da una ricostruita."""
    assert "fonte" in careers.columns
    assert careers["fonte"].notna().all()


def test_i_totali_coincidono_con_le_presenze_grezze(app, careers):
    """La tabella e' un'aggregazione: non deve perdere ne' inventare partite."""
    assert careers["appearances"].sum() == len(app)
    assert careers["goals"].sum() == app["goals"].sum()
    assert careers["minutes"].sum() == app["minutes_played"].sum()


def test_season_taglia_a_luglio():
    """Il taglio a luglio non e' un dettaglio: la coda COVID della 2019-20
    arriva al 2 agosto 2020 e con un taglio a gennaio finirebbe nella
    stagione sbagliata."""
    d = pd.Series(pd.to_datetime(
        ["2019-08-01", "2020-01-15", "2020-06-30", "2020-08-02", "2020-09-01"]
    ))
    s = C.season_of(d)
    assert list(s) == ["2019-20", "2019-20", "2019-20", "2020-21", "2020-21"]


# --------------------------------------------------------------------------
# 2 · Guardiani della regola R8 (anti look-ahead) — i test che contano
# --------------------------------------------------------------------------

def test_career_before_esclude_tutto_cio_che_viene_dopo(app):
    """IL test. `career_before(D)` non deve contenere una sola partita >= D."""
    for data in ("2018-01-01", "2020-06-01", "2023-09-15"):
        cb = C.career_before(data, app)
        atteso = app[app["date"] < pd.Timestamp(data)]
        assert cb["appearances_before"].sum() == len(atteso), (
            f"{data}: il totale non coincide con le sole partite precedenti"
        )
        # e nessun giocatore che ha esordito DOPO puo' comparire
        esordi = app.groupby("player_id")["date"].min()
        dopo = set(esordi[esordi >= pd.Timestamp(data)].index)
        assert not (set(cb.index) & dopo), f"{data}: presenti giocatori non ancora esorditi"


def test_career_before_e_monotona(app):
    """Una carriera non si accorcia. Se il taglio fosse sbagliato (per esempio
    su un confronto `<=` contro `<` mal gestito) la monotonia si romperebbe."""
    a = C.career_before("2019-01-01", app)
    b = C.career_before("2021-01-01", app)
    comuni = a.index.intersection(b.index)
    assert (b.loc[comuni, "appearances_before"] >= a.loc[comuni, "appearances_before"]).all()
    assert (b.loc[comuni, "goals_before"] >= a.loc[comuni, "goals_before"]).all()


def test_career_before_e_stretta_non_inclusiva(app):
    """Il confine e' `< as_of`, non `<=`: la partita del giorno stesso e' la
    partita da prevedere, e non puo' entrare nella sua stessa feature."""
    giorno = pd.Timestamp("2019-03-02")
    quel_giorno = int((app["date"] == giorno).sum())
    assert quel_giorno > 0, "scegliere un giorno con partite per rendere il test vero"
    prima = C.career_before(giorno, app)["appearances_before"].sum()
    dopo = C.career_before(giorno + pd.Timedelta(days=1), app)["appearances_before"].sum()
    assert dopo - prima == quel_giorno


def test_censored_left_marca_chi_e_tagliato_dal_bordo(app):
    """Chi ha la prima presenza al bordo del dataset non e' un esordiente:
    i suoi totali sono un LIMITE INFERIORE. Non marcarlo e' l'errore che e'
    gia' costato 155 allenatori su 496 (audit §D.2)."""
    cb = C.career_before("2026-01-01", app)
    assert cb["censored_left"].sum() > 0
    assert (cb.loc[cb["censored_left"], "first_appearance"] <= C.CENSORING_CUTOFF).all()
    assert (cb.loc[~cb["censored_left"], "first_appearance"] > C.CENSORING_CUTOFF).all()


def test_top5_e_altre_sommano_al_totale(app):
    cb = C.career_before("2024-01-01", app)
    assert (
        cb["top5_appearances_before"] + cb["other_appearances_before"]
        == cb["appearances_before"]
    ).all()


def test_career_before_filtra_per_giocatore(app):
    ids = list(C.population(app)[:50])
    cb = C.career_before("2023-01-01", app, player_ids=ids)
    assert set(cb.index) <= set(ids)


# --------------------------------------------------------------------------
# 3 · Strato 2 (Wikipedia) — struttura e CONTENIMENTO DELLA LICENZA
# --------------------------------------------------------------------------

def test_strato2_opzionale_non_alza_se_manca(tmp_path, monkeypatch):
    """Lo strato 2 e' opzionale per costruzione: se la raccolta non e' stata
    eseguita, il codice deve restituire una tabella vuota, non rompersi."""
    monkeypatch.setattr(C, "ROOT_DATA", tmp_path)
    w = C.load_wikipedia_careers()
    assert w.empty
    assert "fonte" in w.columns


def test_strato2_dichiara_fonte_e_licenza_su_ogni_riga():
    """Regola R2 a livello di riga + attribuzione CC BY: senza `source_url` la
    licenza Wikipedia non e' rispettata."""
    w = C.load_wikipedia_careers()
    if w.empty:
        pytest.skip("raccolta Wikipedia non ancora eseguita")
    assert (w["fonte"] == "wikipedia").all()
    assert (w["licenza"] == "CC BY-SA 4.0").all()
    assert w["source_url"].notna().all()
    assert w["source_url"].str.startswith("https://").all()


def test_strato2_struttura_delle_tappe():
    w = C.load_wikipedia_careers()
    if w.empty:
        pytest.skip("raccolta Wikipedia non ancora eseguita")
    # `anno_da` puo' essere NULLO: Wikipedia usa `0000` come segnaposto per
    # "inizio ignoto" e il parser lo traduce in None invece di lasciare uno
    # zero che sembrerebbe una misura (regola R6). Cio' che NON deve mai
    # esserci e' proprio lo zero.
    assert (w["anno_da"].dropna() >= 1900).all()
    assert not (w["anno_da"] == 0).any(), "segnaposto 0000 non neutralizzato (R6)"
    entrambi = w["anno_a"].notna() & w["anno_da"].notna()
    assert (w.loc[entrambi, "anno_a"] >= w.loc[entrambi, "anno_da"]).all()
    # una tappa "aperta" e' quella senza anno di fine, e viceversa
    assert (w.loc[w["aperta"], "anno_a"].isna()).all()
    assert w["giovanili"].dtype == bool and w["prestito"].dtype == bool


# --------------------------------------------------------------------------
# 4 · Il DATABASE UNICO
# --------------------------------------------------------------------------

def test_database_unico_contiene_entrambe_le_fonti():
    db = C.load_database()
    fonti = set(db["fonte"])
    assert C.FONTE_STRATO1 in fonti
    # ogni riga sa da dove viene: e' la condizione perche' i numeri delle due
    # fonti non vengano sommati per sbaglio (contano cose diverse)
    assert db["fonte"].notna().all()
    assert len(db[db["fonte"] == C.FONTE_STRATO1]) == len(C.load_careers())
    if not C.load_wikipedia_careers().empty:
        assert "wikipedia" in fonti


def test_database_unico_ha_le_colonne_comuni():
    db = C.load_database()
    for c in ("player_id", "player_name", "club_id", "club_name", "anno_da",
              "anno_a", "appearances", "goals", "fonte", "aggancio"):
        assert c in db.columns, f"colonna assente nel database: {c}"
    # Il nome c'e' su tutte le righe wikipedia (arriva per player_id, non per
    # matching di nome).
    w = db[db["fonte"] == "wikipedia"]
    if len(w):
        assert w["player_name"].notna().all()
    # ⚠️ ANOMALIA DICHIARATA (R4), non un bug nostro: nella fonte a monte
    # esiste UN giocatore senza nome — player_id 380365, due presenze in Copa
    # del Rey nel settembre 2018, e non compare affatto in players.csv. E' un
    # buco di `appearances.csv`, non della nostra aggregazione.
    senza_nome = db[db["player_name"].isna()]
    assert set(senza_nome["player_id"]) <= {380365}


def test_aggancio_dichiara_sempre_il_proprio_stato():
    """`nativo` / `univoco` / `ambiguo` / `assente`: un club non agganciato
    deve dirlo, non sparire ne' fingere un id."""
    db = C.load_database()
    assert set(db["aggancio"].unique()) <= {"nativo", "univoco", "ambiguo", "assente"}
    # dove l'aggancio non e' riuscito, il club_id DEVE essere nullo
    non_agganciate = db[db["aggancio"].isin(["ambiguo", "assente"])]
    assert non_agganciate["club_id"].isna().all()
    # e dove e' riuscito, no
    agganciate = db[db["aggancio"].isin(["nativo", "univoco"])]
    assert agganciate["club_id"].notna().all()


# --------------------------------------------------------------------------
# 5 · Normalizzazione dei nomi di club
# --------------------------------------------------------------------------

def test_normalizzazione_toglie_le_sigle_ma_non_i_nomi():
    """Le sigle societarie non distinguono un club; i nomi si'. Confondere le
    due cose e' costato un bug: `sporting` fra le stopword annullava
    «Sporting CP», che restava senza token e quindi senza candidati."""
    from src.data.club_matching import normalizza
    assert normalizza("SSC Napoli") == normalizza("Napoli")
    assert normalizza("Associazione Sportiva Roma") >= normalizza("Roma")
    assert "sporting" in normalizza("Sporting CP")
    # caratteri che NFKD NON decompone: secondo bug pagato
    assert normalizza("Brøndby") == normalizza("Brondby")
    assert normalizza("Lech Poznań") == normalizza("Lech Poznan")


def test_aggancio_e_univoco_o_niente():
    """Un aggancio ambiguo non si sceglie a caso: si lascia vuoto. E' la
    lezione di TEAM_ALIASES (caso «Hellas Verona»)."""
    from src.data.club_matching import Agganciatore
    a = Agganciatore()
    assert a.aggancia("Bayern Munich") is not None
    assert a.aggancia("Lech Poznań") is not None
    assert a.aggancia("Club Che Non Esiste Affatto") is None


def test_aggancio_serie_rende_uno_stato_per_riga():
    from src.data.club_matching import Agganciatore
    s = pd.Series(["Bayern Munich", "Club Che Non Esiste Affatto", None])
    out = Agganciatore().aggancia_serie(s)
    assert list(out["aggancio"]) == ["univoco", "assente", "assente"]
    assert out.loc[0, "club_id_agganciato"] is not None
    assert pd.isna(out.loc[1, "club_id_agganciato"])


# --------------------------------------------------------------------------
# 6 · VERIFICA D'IDENTITA' — la difesa contro gli omonimi (audit 01/08/2026)
# --------------------------------------------------------------------------

def test_verifica_identita_e_gerarchica_non_un_or():
    """L'audit ha misurato che senza questo controllo lo 0,268% delle pagine
    raccolte era di UN'ALTRA PERSONA. E che un OR (`data OR club`) porterebbe
    il falso positivo da 0,23% a ~10,5%: un OR non e' mai piu' forte del suo
    ramo piu' debole."""
    from src.data.wikipedia_careers import Tappa, verifica_identita

    def tappa(club):
        return Tappa(1, 1, club, 2015, 2018, False, 10, 0, False, False, "u")

    # 1 · data che coincide -> confermata, senza bisogno dei club
    assert verifica_identita("1988-08-21", "1988-08-21", []) == "confermata_data"
    assert verifica_identita("1988-08-21", "1988-08-23", []) == "confermata_data"  # 2 gg

    # 4 · data discorde e nessun club in comune -> RESPINTA. E' il caso Pele':
    # player_id nato nel 1991 che riceveva la pagina del Pele' del 1940.
    assert verifica_identita("1940-10-23", "1991-09-29", [tappa("Santos")],
                             club_noti={"Fluminense"}) == "respinta"

    # 3 · date discordi MA i club coincidono -> QUARANTENA, non scarto: sono i
    # casi in cui la persona e' giusta e sono le due FONTI a dissentire
    # sull'anagrafica (Chancel Mbemba 1994 contro 1988, 5 club su 5 uguali).
    assert verifica_identita(
        "1988-08-08", "1994-08-08",
        [tappa("Anderlecht"), tappa("Newcastle")],
        club_noti={"Anderlecht", "Newcastle"},
    ) == "quarantena"

    # 2 · data non confrontabile ma club coincidenti -> confermata via club
    assert verifica_identita(None, "1994-08-08", [tappa("Anderlecht")],
                             club_noti={"Anderlecht"}) == "confermata_club"
    # ...e senza club noti resta respinta: l'assenza di prova non e' prova
    assert verifica_identita(None, "1994-08-08", [tappa("Anderlecht")]) == "respinta"


def test_le_respinte_non_entrano_nel_database():
    """Il test che conta davvero: una carriera di un'altra persona non deve
    poter arrivare a valle. Restano in `esiti.jsonl` per sapere CHI era, ma
    fuori dal deliverable e fuori da `load_database()`."""
    w = C.load_wikipedia_careers()
    if w.empty:
        pytest.skip("raccolta Wikipedia non ancora eseguita")
    if "identita" in w.columns:
        assert "respinta" not in set(w["identita"])
        # e cio' che resta e' dichiarato, non implicito
        assert set(w["identita"].unique()) <= {
            "confermata_data", "confermata_club", "quarantena", "non_verificata",
            # Wikidata puo' RIBALTARE una respinta: la `bday` dell'HTML e' un
            # ripiego, la `P569` e' un valore tipizzato sulla stessa entita'.
            # Quando lo fa, la riga cambia etichetta — non entra nel database
            # continuando a dichiararsi «respinta» (sarebbe un finto pieno, R6).
            "confermata_wikidata",
        }


def test_una_respinta_ribaltata_cambia_etichetta():
    """Il seguito del test qui sopra, sul punto che l'ha fatto fallire.

    17 giocatori respinti dalla verifica HTML sono stati confermati da
    Wikidata a scarto ZERO ed entrano nel database. Devono entrarci con
    l'etichetta nuova: se una riga dentro il deliverable dicesse ancora
    `respinta`, ogni filtro futuro su quella colonna darebbe la risposta
    sbagliata, e nessun confronto snapshot-contro-fonte se ne accorgerebbe.
    Il giudizio originale resta leggibile in `identita_wikipedia`.
    """
    w = C.load_wikipedia_careers()
    if w.empty or "identita_wikidata" not in w.columns:
        pytest.skip("verifica Wikidata non ancora eseguita")
    ribaltate = w[w["identita"] == "confermata_wikidata"]
    if ribaltate.empty:
        pytest.skip("nessuna respinta ribaltata in questo deliverable")
    assert (ribaltate["identita_wikidata"] == "confermata").all()
    assert set(ribaltate["identita_wikipedia"]) <= {
        "respinta", "quarantena", "confermata_club", "confermata_data"
    }


def test_club_riserve_non_si_agganciano_alla_prima_squadra():
    """«Bilbao Athletic» e' la squadra B: agganciarla all'Athletic Bilbao
    attribuirebbe presenze di terza divisione al club maggiore. `normalizza`
    torna un frozenset, quindi i due nomi collassano sullo stesso insieme e
    l'ordine dei token NON protegge: serve l'elenco esplicito."""
    from src.data.club_matching import Agganciatore, normalizza

    assert normalizza("Bilbao Athletic") == normalizza("Athletic Bilbao")
    a = Agganciatore()
    assert a.aggancia("Bilbao Athletic") is None
    assert a.aggancia("Real Madrid B") is None
    assert a.aggancia("Bayern Munich") is not None       # la prima squadra si'


def test_falsi_positivi_dellaudit_sono_corretti():
    """Erano il difetto peggiore: uscivano etichettati «univoco», cioe' come
    CERTEZZA sbagliata. Brest andava alla Dynamo Brest (Bielorussia, 0/108
    conferme) e PAOK a una squadra dilettanti che in `appearances` non compare
    mai."""
    from src.data.club_matching import Agganciatore

    nomi = pd.read_csv(C.DATA_DIR.parent / "player_scores" / "club_names.csv.gz")
    per_id = nomi.set_index("club_id")["name"]
    a = Agganciatore()
    assert per_id[a.aggancia("Brest")] == "Stade Brestois 29"
    assert "Panthessalonikios" in per_id[a.aggancia("PAOK")]
    assert "Athlitiki Enosi" in per_id[a.aggancia("AEK Athens")]
