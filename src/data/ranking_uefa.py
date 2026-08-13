"""I coefficienti UEFA — federazioni e club — e il PAESE dei club fuori perimetro.

Consegna dell'utente del 13/08/2026 (`data/ranking_uefa/`), fonte dichiarata
uefa.com, aggiornata al 12/08/2026 19:55. E' la prima misura di forza che il
progetto abbia per club **fuori** dai cinque campionati.

A che serve davvero, in ordine di valore misurato:

1. ⭐ **il PAESE**, che nel nostro dataset non esiste come colonna da nessuna
   parte (`docs/CLUB_FUORI_PERIMETRO.md`). Il ranking lo porta per 410 club, e
   di questi **168 agganciano un `club_id` che non ha un campionato domestico**
   — cioe' proprio quelli su cui il dataset taceva;
2. una **scala di forza cross-lega**, che il Dixon-Coles non ha per costruzione:
   fissa `media(attacco) = 0` sul pool su cui e' fittato, quindi un `+0.15` di
   Bundesliga e uno di Super League svizzera non sono confrontabili;
3. la regola d'accesso alle coppe, utile al simulatore di stagione (Fase 89).

⚠️⚠️ TRAPPOLA R8, ed e' la piu' facile da sbagliare qui dentro.
Un coefficiente e' una fotografia con una DATA. Il file ne contiene **due
diverse** per le federazioni:

    finestra 21/22-25/26  -> chiusa a fine 2025/26, decide l'access list 2027/28
    finestra 22/23-26/27  -> in corso (la colonna 26/27 e' 0.0 per tutti)

Usare il coefficiente di OGGI per prevedere una partita di due anni fa e'
look-ahead: quel numero incorpora i risultati di quella partita e di tutte le
successive. `finestra=` obbliga a scegliere, e non ha un default.

⚠️ ALTRE DUE COSE CHE NON SI DEDUCONO DAL NUMERO.
- Il coefficiente di club NON e' la somma delle sue stagioni: e'
  `MAX(somma 5 stagioni; 20% del coefficiente della federazione)`. Il pavimento
  MORDE su **146 club su 410 (35,6%)** — per loro il numero misura il PAESE,
  non il club. `pavimento_attivo()` lo dice riga per riga.
- La **Russia** e' sospesa dal 28/02/2022 e il suo coefficiente e' congelato.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

CARTELLA = Path(__file__).resolve().parents[2] / "data" / "ranking_uefa"
FILE = CARTELLA / "coefficienti_uefa_2026-08-12.xlsx"

#: finestra -> (foglio delle federazioni, access list che decide)
FINESTRE: dict[str, tuple[str, str]] = {
    "2025-26": ("Federazioni 2025-26", "access list 2027/28"),
    "2026-27": ("Federazioni 2026-27", "access list 2028/29 (in corso)"),
}

#: L'unico foglio dei club consegnato. Se ne arrivano altri, questa diventa
#: una mappa come `FINESTRE` — e la firma di `club()` non cambia.
FOGLIO_CLUB = "Club 2026-27"

#: Il pavimento della UEFA sul coefficiente di club.
QUOTA_FEDERAZIONE = 0.20


@lru_cache(maxsize=None)
def _foglio(nome: str) -> pd.DataFrame:
    if not FILE.exists():
        raise FileNotFoundError(
            f"manca {FILE}. E' una consegna manuale (13/08/2026), non si scarica: "
            "vedi data/ranking_uefa/README.md")
    return pd.read_excel(FILE, sheet_name=nome)


def federazioni(finestra: str) -> pd.DataFrame:
    """Il ranking per federazione, per la finestra scelta.

    `finestra` non ha un default **apposta**: le due tabelle sono due momenti
    diversi e sceglierne una di nascosto sarebbe la trappola R8 daccapo.
    """
    if finestra not in FINESTRE:
        raise ValueError(f"finestra {finestra!r} sconosciuta. Valide: {sorted(FINESTRE)}")
    d = _foglio(FINESTRE[finestra][0]).dropna(subset=["Federazione"]).copy()
    d["finestra"] = finestra
    return d.reset_index(drop=True)


def club() -> pd.DataFrame:
    """Il ranking per club, con `Paese` e `Coefficiente UEFA`.

    ⚠️ `Coefficiente UEFA` NON e' `Somma stagioni`: e' il massimo fra questa e
    il 20% del coefficiente della federazione. Verificato sul file: l'identita'
    regge su **410/410** righe e il pavimento e' attivo su 146 (35,6%).
    """
    return _foglio(FOGLIO_CLUB).dropna(subset=["Club"]).reset_index(drop=True)


def pavimento_attivo(d: pd.DataFrame | None = None) -> pd.Series:
    """Dove il coefficiente misura il PAESE invece del club.

    Su 146 club su 410 il numero pubblicato e' il 20% del coefficiente della
    federazione, non il loro. Leggerlo come «forza di questo club» li mette
    tutti alla pari dentro lo stesso paese — che e' vero per la UEFA e falso
    per noi. Chi usa il coefficiente come feature deve almeno **saperlo**, e
    probabilmente escluderli o trattarli a parte.
    """
    d = club() if d is None else d
    return d["Quota federazione (20%)"] > d["Somma stagioni"] + 1e-9


def con_club_id() -> pd.DataFrame:
    """Il ranking dei club con il `club_id` di player-scores, dove e' univoco.

    Usa l'`Agganciatore` del progetto, che su un nome ambiguo **lascia vuoto**
    invece di indovinare (regola aurea del join). Misurato sulla consegna:
    331 univoci, 20 ambigui, 59 assenti su 410.

    ⚠️ I 79 non agganciati sono in gran parte le abbreviazioni UEFA dei club
    PIU' grandi — «Ajax», «Atleti», «B. Dortmund», «Bayern München», «Athletic
    Club» — cioe' proprio quelli per cui il ranking non ci serve: li abbiamo
    gia' nei nostri campionati. Il valore sta nella coda, non in testa.
    """
    from src.data.club_matching import Agganciatore   # import pigro: legge un CSV
    d = club().copy()
    A = Agganciatore()
    d["club_id"] = d["Club"].map(A.aggancia)
    d["stato_aggancio"] = d["Club"].map(
        lambda n: {0: "assente", 1: "univoco"}.get(len(A.candidati(n)), "ambiguo"))
    for (nome, paese), cid in ALIAS_PER_PAESE.items():
        m = (d["Club"] == nome) & (d["Paese"] == paese)
        d.loc[m, "club_id"] = cid
        d.loc[m, "stato_aggancio"] = "univoco (disambiguato dal paese)"
    return d


#: (Club, Paese) -> club_id, per gli OMONIMI che il nome da solo non separa.
#:
#: ⚠️ Trovato dall'invariante `un club_id, un paese` — non guardando i nomi.
#: «Bohemians» (Republic of Ireland) e «Bohemians Praha» (Czechia) sono due
#: club diversi in due paesi diversi, e l'`Agganciatore` li mandava ENTRAMBI
#: sul 715, che e' il ceco (60 partite di TS1 in `games.csv`). Esito «univoco»
#: e club sbagliato: la stessa famiglia di `Espanol` e `Red Star FC` (R6).
#:
#: Qui pero' la riparazione e' facile e SICURA, e il motivo e' interessante:
#: questa fonte porta il **paese**, quindi l'ambiguita' che il nome non risolve
#: la risolve una colonna. E' il caso in cui piu' dati non aggiungono rumore ma
#: tolgono un errore. Il club irlandese nel registro c'e': «Bohemian Football
#: Club» (9211), senza campionato domestico.
ALIAS_PER_PAESE: dict[tuple[str, str], int] = {
    ("Bohemians", "Republic of Ireland"): 9211,
}


def controlla_un_club_un_paese(d: pd.DataFrame | None = None) -> pd.DataFrame:
    """L'INVARIANTE che ha trovato l'omonimo: un `club_id`, un paese solo.

    Se due righe del ranking — due club, due federazioni — finiscono sullo
    stesso `club_id`, almeno una delle due e' un aggancio falso. E' un
    controllo che non guarda le stringhe, quindi non si fa ingannare dal fatto
    che si somiglino: e' proprio la somiglianza a essere il problema.

    Torna le righe in conflitto (vuoto = nessun conflitto).
    """
    d = con_club_id() if d is None else d
    u = d[d["stato_aggancio"].astype(str).str.startswith("univoco")].dropna(subset=["club_id"])
    per_id = u.groupby("club_id")["Paese"].nunique()
    sospetti = set(per_id[per_id > 1].index)
    return u[u["club_id"].isin(sospetti)].sort_values("club_id")


def paese_dei_club() -> dict[int, str]:
    """`club_id` -> paese, per i soli agganci UNIVOCI.

    E' il pezzo che `docs/CLUB_FUORI_PERIMETRO.md` dichiarava mancante: nel
    dataset player-scores nessuna colonna, in nessun file, dice di che paese e'
    un club. Il ranking lo dice per 331 club, e **168 di loro non hanno un
    campionato domestico nel dataset**.

    ⚠️ Il paese NON e' il campionato, e la distinzione conta: sapere che il
    Ludogorets e' bulgaro non da' nessuna delle sue partite di campionato, che
    nel dataset restano zero. Serve a decidere il perimetro, non a prezzare.
    """
    d = con_club_id()
    d = d[(d["stato_aggancio"] == "univoco") & d["Paese"].notna()]
    return {int(c): p for c, p in zip(d["club_id"], d["Paese"])}
