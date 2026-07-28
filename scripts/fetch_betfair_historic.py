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
MARKET_TYPE = "OVER_UNDER_25"
FILE_TYPE = "M"                      # M = market data (E = event data, senza prezzi)
THROTTLE = 0.4                        # cortesia verso il servizio

# Codici paese Betfair delle 5 leghe del progetto. Il filtro dell'API e' per
# PAESE, non per competizione: si scarica tutto il calcio di quel paese e si
# filtra a valle con il join per squadre sullo snapshot (stesso metodo di
# footiqo). Le partite di serie minori/coppe semplicemente non agganciano.
COUNTRIES = ["IT", "GB", "ES", "DE", "FR"]

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
    print(f"OVER_UNDER_25 presente: {'SI' if MARKET_TYPE in tipi else 'NO'}"
          f"{f' ({tipi[MARKET_TYPE]} mercati)' if MARKET_TYPE in tipi else ''}")
    print("paesi bersaglio:", {c: paesi.get(c, 0) for c in COUNTRIES})
    if MARKET_TYPE not in tipi:
        print("\nSenza OVER_UNDER_25 non c'e' nulla da scaricare per questo scopo.")
        return
    size = _post("GetAdvBasketDataSize",
                 _filter(season, market_types=[MARKET_TYPE], countries=COUNTRIES))
    print(f"\nfiltrato su {MARKET_TYPE} + {COUNTRIES}: "
          f"{size.get('fileCount')} file, {size.get('totalSizeMB')} MB")


# --------------------------------------------------------------------------- #
# Parsing dello stream storico (formato Betfair: JSON per riga, bz2)
# --------------------------------------------------------------------------- #
def _closing_from_stream(raw: bytes) -> dict | None:
    """Estrae la CHIUSURA da un file-mercato dello stream storico.

    Formato: una riga JSON per aggiornamento (`op":"mcm"`), con `pt` = istante
    di pubblicazione (epoch ms) e `mc[]` = cambi di mercato. `mc[].rc[]` porta
    `ltp` (last traded price) per ciascun runner; `mc[].marketDefinition`
    compare quando la definizione cambia e contiene `inPlay`.

    "Chiusura" = ultimo prezzo scambiato PRIMA che il mercato passi in-play,
    cioe' prima del calcio d'inizio. Si usa il flag `inPlay` e non l'orario
    programmato (`marketTime`) perche' e' il fatto reale: una partita che
    inizia in ritardo ha una chiusura piu' tarda dell'orario da calendario, e
    prendere `marketTime` taglierebbe fuori gli ultimi minuti di mercato --
    oppure, peggio, includerebbe prezzi gia' in-play (che riflettono cio' che
    accade in campo: sarebbe look-ahead, l'errore che il progetto insegue da
    sempre, cfr. la trappola di Udinese-Roma in docs/DATI.md).
    """
    last: dict[int, float] = {}
    closing: dict[int, float] | None = None
    closing_pt: int | None = None
    meta: dict = {}
    runners: dict[int, str] = {}
    in_play = False

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
                    # transizione al gioco: congela cio' che c'era un istante prima
                    in_play = True
                    closing = dict(last)
                    closing_pt = pt
            if in_play:
                continue          # dopo il fischio d'inizio non si aggiorna piu'
            # `img` (Image) = "replace existing prices/data with the data
            # supplied: it is not a delta" (specifica ufficiale Exchange Stream
            # API, pagina "Exchange Stream API" della doc Betfair, letta alla
            # Fase 109-bis). Senza questo ramo un ri-invio dell'immagine a meta'
            # stream lascerebbe in cache prezzi che la fonte considera
            # sostituiti: un "finto pieno" (regola R6) invisibile a ogni
            # controllo, perche' il numero resta plausibile.
            if mc.get("img"):
                last.clear()
            for rc in mc.get("rc", []) or []:
                if rc.get("ltp") is not None and rc.get("id") is not None:
                    last[rc["id"]] = float(rc["ltp"])

    if closing is None:
        # il mercato non ha mai segnato inPlay (succede: sospeso, annullato,
        # o file troncato). Si usa l'ultimo stato noto, ma lo si DICHIARA.
        closing, closing_pt = last, None
    if not closing or not runners:
        return None

    over = under = None
    for sel, price in closing.items():
        name = (runners.get(sel) or "").lower()
        if "over" in name:
            over = price
        elif "under" in name:
            under = price
    if over is None or under is None:
        return None

    return {
        "marketId": meta.get("marketId"),
        "eventId": meta.get("eventId"),
        "eventName": meta.get("eventName"),
        "countryCode": meta.get("countryCode"),
        "marketTime": meta.get("marketTime"),
        "odds_over25_close": over,
        "odds_under25_close": under,
        "closing_pt_ms": closing_pt,
        "chiusura_da_inplay": closing_pt is not None,
    }


def cmd_fetch(season: str, limit: int | None) -> None:
    files = _post("DownloadListOfFiles",
                  _filter(season, market_types=[MARKET_TYPE], countries=COUNTRIES))
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

    for i, path in enumerate(files, 1):
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
            rec = _closing_from_stream(bz2.decompress(blob))
        except (urllib.error.URLError, OSError, ValueError) as e:
            falliti += 1
            print(f"  [{i}/{len(files)}] ERRORE su {path}: {e}")
            continue
        if rec is None:
            falliti += 1
        else:
            if not rec["chiusura_da_inplay"]:
                senza_inplay += 1
            rows.append(rec)
        if i % 100 == 0 or i == len(files):
            print(f"  [{i}/{len(files)}] estratte {len(rows)} chiusure")

    if not rows:
        raise SystemExit("nessuna chiusura estratta: controllare il formato dei file.")

    out = OUT_DIR / f"betfair_ou25_{season}.csv"
    cols = ["marketId", "eventId", "eventName", "countryCode", "marketTime",
            "odds_over25_close", "odds_under25_close", "closing_pt_ms",
            "chiusura_da_inplay"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    manifest = {
        "fonte": "historicdata.betfair.com (Betfair Exchange, piano BASIC)",
        "stagione": season, "mercato": MARKET_TYPE, "paesi": COUNTRIES,
        "scaricato": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "file_richiesti": len(files), "chiusure_estratte": len(rows),
        "file_falliti_o_senza_prezzi": falliti,
        "chiusure_senza_flag_inplay": senza_inplay,
        "sha256_csv": hashlib.sha256(out.read_bytes()).hexdigest(),
        "nota_chiusura": ("ultimo last-traded-price prima del passaggio in-play; "
                          "dove il flag inPlay non compare mai si e' usato "
                          "l'ultimo stato noto (colonna chiusura_da_inplay=False)"),
    }
    (OUT_DIR / f"betfair_manifest_{season}.json").write_text(
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
    args = p.parse_args()

    if args.check:
        cmd_check()
        return
    if not args.season:
        p.error("serve --season (oppure --check)")
    if args.dry_run:
        cmd_dry_run(args.season)
        return
    cmd_fetch(args.season, args.limit)


if __name__ == "__main__":
    main()
