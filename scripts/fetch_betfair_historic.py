"""Scarica e normalizza le quote di CHIUSURA dal servizio Betfair Historical
Data (historicdata.betfair.com), per il mercato Over/Under 2.5 gol.

PERCHE' ESISTE (Fase 109). La chiusura O/U 2.5 delle stagioni 2017-18 e
2018-19 non esiste in football-data (l'unica linea di quelle stagioni e' una
APERTURA, `BbAv`): e' l'ultimo buco dati vero del progetto, oggi coperto da una
STIMA dichiarata (`data/estimates/ou_close_2017_19.csv`, MAE ~0.014 nel regime
d'uso). Tre cacce precedenti (Fasi 100, 105, 107, 108) hanno escluso ogni
fonte gratuita: l'unico candidato REALE trovato (1xBet via footiqo) e' peggiore
della stima come proxy della media multi-book (MAE 0.0156) e non e' stato
inserito.

Betfair e' un caso diverso, e il motivo e' MISURATO non assunto. Nella sola
stagione dove football-data pubblica anche la chiusura Betfair Exchange
(2024-25, colonne `BFEC>2.5`/`BFEC<2.5`, 1.752 partite su 5 leghe):

    scarto dalla media multi-book (MAE su probabilita' devigata)
      MaxC (massimo book)      0.0057
      Betfair Exchange         0.0060   <-- qui
      Pinnacle                 0.0063
      Bet365                   0.0071
      la nostra STIMA          ~0.014
      1xBet (scartato F100)    0.0156

Betfair sta nel gruppo dei book seri, non fra gli outlier: **2,3 volte piu'
vicino alla media multi-book della stima che sostituirebbe**, con bias
+0.0015 (contro +0.0088 di 1xBet) e log-loss contro l'esito vero almeno pari
alla media dei book (0.6648 vs 0.6652, Delta -0.00039, CI95
[-0.00115,+0.00038], P 84.7% -- non conclusivo ma col segno a favore).

NON e' ancora una decisione di INSERIMENTO: e' la ragione per cui vale la pena
scaricare il dato e sottoporlo allo stesso protocollo di validazione di
footiqo (7 criteri + confutazioni). La decisione si prende sui numeri del
2017-19, non su questi.

PREREQUISITI (li fornisce l'utente, non lo script):
  1. un account Betfair registrato;
  2. i pacchetti BASIC (GRATUITI) di "Soccer" ACQUISITI sul sito per OGNI MESE
     della finestra richiesta -- il servizio ragiona per mese, e `GetMyData`
     elenca solo cio' che e' stato acquisito. Senza questo passo gli endpoint
     rispondono con liste vuote, non con un errore;
  3. il token di sessione (`ssoid`) in variabile d'ambiente BETFAIR_SSOID.
     MAI passarlo come argomento (finisce nella history della shell) e mai
     scriverlo in un file del repo.

⚠️ GEO-BLOCCO: `historicdata.betfair.com` risponde **403 dall'ambiente cloud
del progetto** (blocco del firewall per regione, PRIMA dell'autenticazione:
verificato alla Fase 109 anche sull'endpoint API, non solo sul sito). Questo
script e' pensato per girare sulla macchina dell'utente, non da qui.

PROTOCOLLO DI VALIDAZIONE INTEGRATO (--season 2425 come primo passo).
Prima di fidarsi dell'estrazione sul bersaglio, si scarica la stagione
2024-25 e si confronta il risultato con la colonna `BFEC>2.5` di
football-data, che e' una cattura INDIPENDENTE della stessa fonte: se le due
coincidono, la pipeline di estrazione (parsing dello stream, scelta
dell'istante di chiusura, join per squadre) e' dimostrata corretta e solo
allora ha senso credere all'estrazione del 2017-19, dove nessun controllo
esterno esiste. E' il passo che alle cacce precedenti mancava.

USO (sulla macchina dell'utente):

    export BETFAIR_SSOID='...'                     # il token, mai nel repo
    python scripts/fetch_betfair_historic.py --check          # cosa possiedo?
    python scripts/fetch_betfair_historic.py --season 2425 --dry-run   # quanto pesa?
    python scripts/fetch_betfair_historic.py --season 2425    # VALIDAZIONE
    python scripts/fetch_betfair_historic.py --season 1718    # il bersaglio

Output: `data/ricerca_esterna/betfair_ou25_<stagione>.csv` (una riga per
mercato: data, squadre, quota Over/Under di chiusura, istante usato come
chiusura) + un manifest con impronte SHA256 e conteggi.
"""

from __future__ import annotations

import argparse
import bz2
import csv
import datetime as dt
import gzip
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_DIR = ROOT / "data" / "ricerca_esterna"
RAW_DIR = ROOT / "data" / "raw" / "betfair_historic"   # in .gitignore (data/raw/)

API = "https://historicdata.betfair.com/api"
SPORT = "Soccer"
PLAN = "Basic Plan"

# ⚠️ ASSUNZIONE NON CONFERMATA DALLA SPECIFICA (verificato alla Fase 110
# specchiando l'intera documentazione ufficiale in docs/betfair_api/): Betfair
# **non pubblica l'elenco dei marketType**. La pagina `listMarketTypes` ne cita
# due come esempio ("i.e. MATCH_ODDS, NEXT_GOAL") e per il resto rimanda a
# scoprirli a runtime. "OVER_UNDER_25" e' quindi una convenzione diffusa
# nell'ecosistema, non un valore documentato.
# Per questo `--dry-run` NON si limita a dire si'/no: stampa i nomi REALI
# trovati nel pacchetto, cosi' se l'etichetta fosse diversa si vede subito
# invece di concludere "il mercato non esiste". E' la stessa lezione del bug
# `img` (Fase 109-bis): non dedurre cio' che si puo' verificare.
MARKET_TYPE = "OVER_UNDER_25"
FILE_TYPE = "M"                      # M = market data (E = event data, senza prezzi)
THROTTLE = 0.4                        # cortesia verso il servizio

# Codici paese Betfair delle 5 leghe del progetto. Il filtro dell'API e' per
# PAESE, non per competizione: si scarica tutto il calcio di quel paese e si
# filtra a valle con il join per squadre sullo snapshot (stesso metodo di
# footiqo). Le partite di serie minori/coppe semplicemente non agganciano.
COUNTRIES = ["IT", "GB", "ES", "DE", "FR"]

# Endpoint di keep-alive per giurisdizione (docs/betfair_api/10_accesso__*).
# ⚠️ La sessione dura **20 MINUTI sull'exchange italiano e spagnolo**, contro
# 12-24 ore sul .com: un download di qualche migliaio di file muore a meta'
# senza rinnovo. Il rinnovo NON e' automatico ne' legato all'attivita' API
# ("Session times aren't determined or extended based on API activity").
KEEPALIVE = {
    "com": "https://identitysso.betfair.com/api/keepAlive",
    "it": "https://identitysso.betfair.it/api/keepAlive",
    "es": "https://identitysso.betfair.es/api/keepAlive",
    "ro": "https://identitysso.betfair.ro/api/keepAlive",
}
KEEPALIVE_OGNI = 600      # 10 min: meta' della finestra italiana, con margine

# Finestre delle stagioni: agosto -> maggio. 2425 e' la stagione di VALIDAZIONE
# (football-data pubblica li' la colonna BFEC di confronto), le altre sono il
# bersaglio.
SEASONS = {
    "1718": ((2017, 8, 1), (2018, 5, 31)),
    "1819": ((2018, 8, 1), (2019, 5, 31)),
    "2425": ((2024, 8, 1), (2025, 5, 31)),
}


def _token() -> str:
    tok = os.environ.get("BETFAIR_SSOID", "").strip()
    if not tok:
        raise SystemExit(
            "BETFAIR_SSOID non impostata.\n"
            "  export BETFAIR_SSOID='il-tuo-token'\n"
            "Il token NON va passato come argomento (finirebbe nella history "
            "della shell) ne' scritto in un file del repo."
        )
    return tok


def _post(endpoint: str, payload: dict) -> object:
    req = urllib.request.Request(
        f"{API}/{endpoint}",
        data=json.dumps(payload).encode(),
        headers={"content-type": "application/json", "ssoid": _token()},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def _get(endpoint: str) -> object:
    req = urllib.request.Request(f"{API}/{endpoint}", headers={"ssoid": _token()})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def _keep_alive(giurisdizione: str) -> bool:
    """Rinnova la sessione. Ritorna True se il servizio conferma.

    Non solleva: un keep-alive fallito non deve buttare via un download in
    corso -- lo si segnala e si prosegue finche' il token regge davvero.
    """
    url = KEEPALIVE.get(giurisdizione, KEEPALIVE["com"])
    req = urllib.request.Request(url, headers={
        "Accept": "application/json", "X-Authentication": _token()})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode("utf-8", "replace"))
        ok = str(d.get("status", "")).upper() == "SUCCESS"
        if not ok:
            print(f"  [keep-alive] risposta inattesa: {d}")
        return ok
    except (urllib.error.URLError, OSError, ValueError) as e:
        print(f"  [keep-alive] fallito ({e}) -- proseguo finche' il token regge")
        return False


def _filter(season: str, *, market_types: list[str], countries: list[str]) -> dict:
    (fy, fm, fd), (ty, tm, td) = SEASONS[season]
    return {
        "sport": SPORT, "plan": PLAN,
        "fromDay": fd, "fromMonth": fm, "fromYear": fy,
        "toDay": td, "toMonth": tm, "toYear": ty,
        "eventId": None, "eventName": None,
        "marketTypesCollection": market_types,
        "countriesCollection": countries,
        "fileTypeCollection": [FILE_TYPE],
    }


# --------------------------------------------------------------------------- #
# Diagnostica: cosa possiede l'account, e quanto pesa il bersaglio
# --------------------------------------------------------------------------- #
def cmd_check() -> None:
    """Elenca i pacchetti posseduti. Se il calcio non c'e' per i mesi che
    servono, ogni altra chiamata tornera' VUOTA senza dare errore: e' la
    trappola principale di questo servizio, quindi si controlla per prima."""
    data = _get("GetMyData")
    if not isinstance(data, list) or not data:
        print("GetMyData non ha restituito pacchetti: l'account non ha ancora "
              "ACQUISITO nulla (il piano BASIC e' gratuito ma va aggiunto, mese "
              "per mese, dal sito).")
        return
    soccer = [d for d in data if str(d.get("sport", "")).lower() == SPORT.lower()]
    print(f"pacchetti totali: {len(data)}  |  di cui {SPORT}: {len(soccer)}")
    mesi = sorted({str(d.get("forDate", ""))[:7] for d in soccer})
    print(f"mesi di {SPORT} posseduti: {len(mesi)}")
    for m in mesi:
        print(f"  {m}")
    for season, ((fy, fm, _), (ty, tm, _)) in SEASONS.items():
        attesi = []
        y, mth = fy, fm
        while (y, mth) <= (ty, tm):
            attesi.append(f"{y}-{mth:02d}")
            mth = mth % 12 + 1
            if mth == 1:
                y += 1
        mancanti = [m for m in attesi if m not in mesi]
        stato = "COMPLETA" if not mancanti else f"MANCANO {len(mancanti)}: {', '.join(mancanti)}"
        print(f"stagione {season}: {stato}")


def cmd_dry_run(season: str) -> None:
    """Quante partite e quanti MB, prima di scaricare. Mostra anche le opzioni
    disponibili: se OVER_UNDER_25 non compare, il mercato non era quotato (o
    non e' nel pacchetto) e il resto non ha senso."""
    opts = _post("GetCollectionOptions", _filter(season, market_types=[], countries=[]))
    tipi = {t["name"]: t["count"] for t in opts.get("marketTypesCollection", [])}
    paesi = {c["name"]: c["count"] for c in opts.get("countriesCollection", [])}
    print(f"--- stagione {season}: cosa esiste nel pacchetto ---")
    print(f"{MARKET_TYPE} presente: {'SI' if MARKET_TYPE in tipi else 'NO'}"
          f"{f' ({tipi[MARKET_TYPE]} mercati)' if MARKET_TYPE in tipi else ''}")
    print("paesi bersaglio:", {c: paesi.get(c, 0) for c in COUNTRIES})

    # I nomi REALI, sempre: l'elenco dei marketType non e' documentato da
    # Betfair (vedi il commento su MARKET_TYPE), quindi questa e' l'unica
    # verifica possibile dell'etichetta che stiamo usando.
    simili = {k: v for k, v in tipi.items() if "OVER" in k.upper() or "UNDER" in k.upper()}
    if simili:
        print("mercati totali/gol disponibili:",
              dict(sorted(simili.items(), key=lambda x: -x[1])))
    if MARKET_TYPE not in tipi:
        print(f"\n{MARKET_TYPE} NON e' fra i tipi disponibili. Prima di concludere "
              "che il mercato non esiste, controllare l'elenco qui sopra: "
              "l'etichetta potrebbe essere diversa (l'elenco dei marketType non "
              "e' documentato da Betfair). I 15 tipi piu' frequenti nel pacchetto:")
        for k, v in sorted(tipi.items(), key=lambda x: -x[1])[:15]:
            print(f"    {k:32s} {v}")
        return
    size = _post("GetAdvBasketDataSize",
                 _filter(season, market_types=[MARKET_TYPE], countries=COUNTRIES))
    print(f"\nfiltrato su {MARKET_TYPE} + {COUNTRIES}: "
          f"{size.get('fileCount')} file, {size.get('totalSizeMB')} MB")


# --------------------------------------------------------------------------- #
# Parsing dello stream storico (formato Betfair: JSON per riga, bz2)
# --------------------------------------------------------------------------- #
def _minuti_al_via(pt_ms: int, market_time: str | None) -> float | None:
    """Minuti fra l'istante del prezzo e il calcio d'inizio programmato.
    Positivo = prima del via. E' l'asse su cui si legge la traiettoria."""
    if not market_time or pt_ms is None:
        return None
    try:
        via = dt.datetime.fromisoformat(market_time.replace("Z", "+00:00"))
    except ValueError:
        return None
    return round((via.timestamp() * 1000 - pt_ms) / 60000, 2)


def _over_under(last: dict[int, float], runners: dict[int, str]) -> tuple[float, float] | None:
    """Da (selectionId -> prezzo) + (selectionId -> nome) ai due lati del
    mercato. None se manca anche solo un lato: mai mezzo mercato."""
    over = under = None
    for sel, price in last.items():
        nome = (runners.get(sel) or "").lower()
        if "over" in nome:
            over = price
        elif "under" in nome:
            under = price
    return (over, under) if over is not None and under is not None else None


def _serie_from_stream(raw: bytes) -> dict | None:
    """Estrae da un file-mercato TUTTA la traiettoria pre-partita, non solo la
    chiusura.

    Perche' la serie e non solo l'ultimo punto (Fase 112): i file contengono
    entrambe le cose, ma un'estrazione che tiene solo la chiusura costringe a
    **ri-scaricare tutto** il giorno in cui si vuole la traiettoria (pista B:
    `newseason.md` la da' per non recuperabile, ed e' il dato che manca alla
    diagnosi della Fase 93). Un solo passaggio serve entrambe le piste.

    Formato: una riga JSON per aggiornamento, `pt` = istante di pubblicazione
    (epoch ms), `mc[].rc[].ltp` = last traded price, `mc[].img` = immagine che
    SOSTITUISCE la cache (non un delta -- specifica ufficiale, vedi
    `data/ricerca_esterna/betfair_stream_spec_estratto.md`).

    La serie si ferma al passaggio **in-play**: dopo il fischio d'inizio i
    prezzi riflettono cio' che accade in campo e non sono piu' pre-partita.

    ASSUNZIONE DICHIARATA: lo stream registrato comincia con un'immagine
    iniziale che porta la `marketDefinition` (e quindi i nomi dei runner), come
    prevede il protocollo. I punti eventualmente precedenti non sono
    risolvibili e vengono contati in `punti_senza_runner`: se quel numero non
    fosse zero, l'assunzione andrebbe rivista.
    """
    last: dict[int, float] = {}
    runners: dict[int, str] = {}
    meta: dict = {}
    serie: list[tuple[int, float, float]] = []
    closing_pt: int | None = None
    in_play = False
    ultimo: tuple[float, float] | None = None
    punti_senza_runner = 0

    for line in raw.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        pt = msg.get("pt")
        for mc in msg.get("mc", []) or []:
            md = mc.get("marketDefinition")
            if md:
                meta.setdefault("marketId", mc.get("id"))
                for k in ("eventId", "eventName", "marketTime", "countryCode",
                          "marketType"):
                    if md.get(k) is not None:
                        meta[k] = md[k]
                for r in md.get("runners", []) or []:
                    if r.get("id") is not None and r.get("name"):
                        runners[r["id"]] = r["name"]
                if md.get("inPlay") and not in_play:
                    in_play = True
                    closing_pt = pt
            if in_play:
                continue
            if mc.get("img"):
                last.clear()
            for rc in mc.get("rc", []) or []:
                if rc.get("ltp") is not None and rc.get("id") is not None:
                    last[rc["id"]] = float(rc["ltp"])
        if in_play or pt is None or not last:
            continue
        if not runners:
            punti_senza_runner += 1
            continue
        ou = _over_under(last, runners)
        if ou and ou != ultimo:          # solo i CAMBI: la serie resta compatta
            serie.append((pt, ou[0], ou[1]))
            ultimo = ou

    if not serie:
        return None
    # Lo stato ALL'ISTANTE della chiusura, che NON coincide sempre con l'ultimo
    # punto della serie: se un'immagine finale lascia prezzato un solo lato, la
    # chiusura non esiste e va detto. Ripiegare sull'ultimo punto completo
    # significherebbe spacciare per chiusura un prezzo di minuti prima -- un
    # "finto pieno" (R6). Distinzione trovata da
    # test_img_sostituisce_la_cache_non_la_fonde, che ha bocciato il primo
    # tentativo di refactor (Fase 112).
    finale = _over_under(last, runners)
    return {
        "finale": finale,
        "marketId": meta.get("marketId"),
        "eventId": meta.get("eventId"),
        "eventName": meta.get("eventName"),
        "countryCode": meta.get("countryCode"),
        "marketTime": meta.get("marketTime"),
        "serie": serie,
        "closing_pt_ms": closing_pt,
        "chiusura_da_inplay": closing_pt is not None,
        "punti_senza_runner": punti_senza_runner,
    }


def _closing_from_stream(raw: bytes) -> dict | None:
    """La CHIUSURA: ultimo punto della traiettoria prima del passaggio in-play.

    E' un caso particolare di `_serie_from_stream` -- cosi' la definizione di
    "chiusura" e la serie non possono divergere.
    """
    s = _serie_from_stream(raw)
    if s is None or s["finale"] is None:
        return None
    over, under = s["finale"]
    return {
        "marketId": s["marketId"], "eventId": s["eventId"],
        "eventName": s["eventName"], "countryCode": s["countryCode"],
        "marketTime": s["marketTime"],
        "odds_over25_close": over, "odds_under25_close": under,
        "closing_pt_ms": s["closing_pt_ms"],
        "chiusura_da_inplay": s["chiusura_da_inplay"],
    }


def cmd_fetch(season: str, limit: int | None, market_type: str = MARKET_TYPE,
              giurisdizione: str = "it", traiettoria: bool = True) -> None:
    files = _post("DownloadListOfFiles",
                  _filter(season, market_types=[market_type], countries=COUNTRIES))
    if not isinstance(files, list) or not files:
        raise SystemExit(
            "DownloadListOfFiles ha restituito 0 file. Cause tipiche, in ordine:\n"
            "  1) i pacchetti BASIC di Soccer per quei mesi non sono stati "
            "acquisiti (esegui --check);\n"
            "  2) il mercato OVER_UNDER_25 non esiste in quella finestra "
            "(esegui --dry-run)."
        )
    if limit:
        files = files[:limit]
    print(f"stagione {season}: {len(files)} file da scaricare")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows, falliti, senza_inplay = [], 0, 0
    serie_rows, senza_chiusura, orfani = [], 0, 0
    ultimo_ka = time.monotonic()
    print(f"keep-alive ogni {KEEPALIVE_OGNI//60} min su giurisdizione '{giurisdizione}'")

    for i, path in enumerate(files, 1):
        if time.monotonic() - ultimo_ka > KEEPALIVE_OGNI:
            _keep_alive(giurisdizione)
            ultimo_ka = time.monotonic()
        dest = RAW_DIR / f"{season}_{Path(path).parent.name}_{Path(path).name}"
        try:
            if dest.exists():
                blob = dest.read_bytes()
            else:
                url = f"{API}/DownloadFile?filePath={urllib.parse.quote(path, safe='')}"
                req = urllib.request.Request(url, headers={"ssoid": _token()})
                with urllib.request.urlopen(req, timeout=180) as r:
                    blob = r.read()
                dest.write_bytes(blob)
                time.sleep(THROTTLE)
            s = _serie_from_stream(bz2.decompress(blob))
        except (urllib.error.URLError, OSError, ValueError) as e:
            falliti += 1
            print(f"  [{i}/{len(files)}] ERRORE su {path}: {e}")
            continue
        if s is None:
            falliti += 1
        else:
            if not s["chiusura_da_inplay"]:
                senza_inplay += 1
            if s["finale"] is not None:
                over, under = s["finale"]
                rows.append({
                    "marketId": s["marketId"], "eventId": s["eventId"],
                    "eventName": s["eventName"], "countryCode": s["countryCode"],
                    "marketTime": s["marketTime"],
                    "odds_over25_close": over, "odds_under25_close": under,
                    "closing_pt_ms": s["closing_pt_ms"],
                    "chiusura_da_inplay": s["chiusura_da_inplay"]})
            else:
                senza_chiusura += 1
            if traiettoria:
                for pt, o, u in s["serie"]:
                    serie_rows.append({
                        "marketId": s["marketId"], "eventName": s["eventName"],
                        "marketTime": s["marketTime"], "pt_ms": pt,
                        "minuti_al_via": _minuti_al_via(pt, s["marketTime"]),
                        "odds_over25": o, "odds_under25": u})
            orfani += s["punti_senza_runner"]
        if i % 100 == 0 or i == len(files):
            print(f"  [{i}/{len(files)}] estratte {len(rows)} chiusure")

    if not rows:
        raise SystemExit("nessuna chiusura estratta: controllare il formato dei file.")

    tag = market_type.lower()
    out = OUT_DIR / f"betfair_{tag}_{season}.csv"
    cols = ["marketId", "eventId", "eventName", "countryCode", "marketTime",
            "odds_over25_close", "odds_under25_close", "closing_pt_ms",
            "chiusura_da_inplay"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    if traiettoria and serie_rows:
        # gzip: la serie e' ~2 ordini di grandezza piu' grande delle chiusure
        tpath = OUT_DIR / f"betfair_traiettoria_{tag}_{season}.csv.gz"
        tcols = ["marketId", "eventName", "marketTime", "pt_ms", "minuti_al_via",
                 "odds_over25", "odds_under25"]
        with gzip.open(tpath, "wt", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=tcols)
            w.writeheader()
            w.writerows(serie_rows)
        print(f"scritta traiettoria {tpath.name}  ({len(serie_rows)} punti)")

    manifest = {
        "fonte": "historicdata.betfair.com (Betfair Exchange, piano BASIC)",
        "punti_traiettoria": len(serie_rows),
        "mercati_senza_chiusura_valida": senza_chiusura,
        "punti_prima_della_market_definition": orfani,
        "stagione": season, "mercato": market_type, "paesi": COUNTRIES,
        "scaricato": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "file_richiesti": len(files), "chiusure_estratte": len(rows),
        "file_falliti_o_senza_prezzi": falliti,
        "chiusure_senza_flag_inplay": senza_inplay,
        "sha256_csv": hashlib.sha256(out.read_bytes()).hexdigest(),
        "nota_chiusura": ("ultimo last-traded-price prima del passaggio in-play; "
                          "dove il flag inPlay non compare mai si e' usato "
                          "l'ultimo stato noto (colonna chiusura_da_inplay=False)"),
    }
    (OUT_DIR / f"betfair_manifest_{tag}_{season}.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\nscritto {out}  ({len(rows)} righe)")
    print(f"  falliti/senza prezzi: {falliti}")
    print(f"  senza flag inPlay (chiusura = ultimo stato noto): {senza_inplay}")
    if season == "2425":
        print("\nPASSO SUCCESSIVO (validazione): confrontare questo CSV con la "
              "colonna BFEC>2.5 di football-data 2024-25. Se coincidono, la "
              "pipeline e' dimostrata corretta e ha senso fidarsi del 2017-19.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--check", action="store_true",
                   help="elenca i pacchetti posseduti (da fare per PRIMO)")
    p.add_argument("--season", choices=sorted(SEASONS),
                   help="stagione da trattare (2425 = validazione)")
    p.add_argument("--dry-run", action="store_true",
                   help="quanti file e quanti MB, senza scaricare")
    p.add_argument("--limit", type=int,
                   help="scarica solo i primi N file (prova rapida)")
    p.add_argument("--market-type", default=MARKET_TYPE,
                   help=f"tipo di mercato (default {MARKET_TYPE}). L'elenco NON "
                        "e' documentato da Betfair: usare --dry-run per vedere i "
                        "nomi reali, poi eventualmente passarli qui (es. per "
                        "scaricare risultato esatto o GG/NG)")
    p.add_argument("--no-trajectory", action="store_true",
                   help="NON estrarre la traiettoria (pista B). Sconsigliato: "
                        "e' nello stesso file, costa zero download in piu', e "
                        "senza di essa servirebbe ri-scaricare tutto")
    p.add_argument("--jurisdiction", default="it", choices=sorted(KEEPALIVE),
                   help="giurisdizione dell'account, per il keep-alive: la "
                        "sessione dura 20 MINUTI su it/es, 12-24h su com "
                        "(default: it)")
    args = p.parse_args()

    if args.check:
        cmd_check()
        return
    if not args.season:
        p.error("serve --season (oppure --check)")
    if args.dry_run:
        cmd_dry_run(args.season)
        return
    cmd_fetch(args.season, args.limit, args.market_type, args.jurisdiction,
              traiettoria=not args.no_trajectory)


if __name__ == "__main__":
    main()
