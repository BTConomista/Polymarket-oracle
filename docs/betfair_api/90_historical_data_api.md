# Historical Data API — i 5 endpoint del servizio storico

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: pagina della documentazione API del servizio **Betfair Historical
> Data**, <https://historicdata.betfair.com> (sezione API).
> **Fornita dall'utente** (2026-07-28) perché quel dominio risponde **403
> dall'ambiente cloud del progetto**: è geo-bloccato *prima*
> dell'autenticazione, quindi non è ri-estraibile da qui con uno script — a
> differenza della documentazione dell'Exchange API, che sta su Atlassian ed è
> raggiungibile (vedi `README.md` di questa cartella).
> **In caso di dubbio vince la pagina online**, che può essere più recente.

---

## Perché questa pagina è separata dalle altre

È un servizio **diverso** da quello documentato nel resto della cartella:

| | Exchange API (file `00`-`80`) | **Historical Data (questa pagina)** |
|---|---|---|
| a cosa serve | quote live, scommesse, stream in tempo reale | scaricare i file già registrati |
| host | `api.betfair.com` | `historicdata.betfair.com` |
| autenticazione | application key + session token | **solo** header `ssoid` |
| documentazione | Atlassian, estraibile via API | pagina del sito, **geo-bloccata da qui** |

**Il punto in cui si toccano, e che ci riguarda**: i file che questa API
scarica sono **registrazioni dello stream** descritto in
`40_stream__exchange_stream_api.md`. Quella specifica è quindi la fonte di
verità per il parser di `scripts/fetch_betfair_historic.py` — ed è così che
alla Fase 109-bis è stato trovato il bug sul campo `img`.

## Autenticazione

Tutti gli endpoint vogliono un solo header: `ssoid: <token di sessione>`.
Nel progetto il token si passa **solo** via variabile d'ambiente
`BETFAIR_SSOID` (mai come argomento, mai in un file versionato).

## Le due trappole da conoscere prima di usarli

1. **`GetMyData` elenca ciò che è stato ACQUISITO, non ciò che esiste.** Il
   piano BASIC è gratuito, ma va aggiunto all'account **mese per mese** dal
   sito. Senza, gli altri endpoint rispondono con **liste vuote e nessun
   errore** — sembra che il dato non esista. Per questo
   `fetch_betfair_historic.py --check` esiste ed è il primo comando da
   eseguire.
2. **Il filtro è per PAESE, non per competizione.** Non si può chiedere "solo
   la Serie A": si scarica il calcio di quel paese e si filtra a valle con il
   join per squadre sullo snapshot (stesso metodo usato per footiqo).

---

## `GetMyData` — i pacchetti posseduti

Restituisce l'elenco dei pacchetti acquistati e accessibili. Serve solo il
token di sessione come header.

```bash
curl -X GET https://historicdata.betfair.com/api/GetMyData \
  -H 'ssoid: YOUR_TOKEN_HERE'
```

Risposta di esempio:

```json
[
  {
    "sport": "Cricket",                 // nome dello sport
    "plan": "Basic Plan",               // nome del piano
    "forDate": "2017-04-01T00:00:00",   // il MESE coperto da questo elemento
    "purchaseItemId": 206               // id dell'elemento acquistato
  },
  {
    "sport": "Cricket",
    "plan": "Basic Plan",
    "forDate": "2017-05-01T00:00:00",
    "purchaseItemId": 120
  }
]
```

Nota: `forDate` conferma la **granularità mensile** dei pacchetti.

## `GetCollectionOptions` — quali filtri sono disponibili

I dati storici sono voluminosi e un evento contiene molti mercati: questo
endpoint dice quali mercati, paesi e tipi di file esistono nella finestra
richiesta, così da restringere prima di scaricare.

Prima chiamata, senza filtri, per vedere cosa c'è:

```bash
curl -X POST https://historicdata.betfair.com/api/GetCollectionOptions \
  -H 'content-type: application/json' \
  -H 'ssoid: YOUR_TOKEN_HERE' \
  -d '{
    "sport":"Horse Racing",
    "plan":"Basic Plan",
    "fromDay": 1, "fromMonth": 3, "fromYear": 2017,
    "toDay": 31, "toMonth": 3, "toYear": 2017,
    "eventId": null,
    "eventName": null,
    "marketTypesCollection": [],
    "countriesCollection": [],
    "fileTypeCollection": []
}'
```

Risposta (troncata nell'originale):

```json
{
  "marketTypesCollection": [
    { "name": "PLACE", "count": 4902 },
    { "name": "WIN", "count": 7671 },
    { "name": "ANTEPOST_WIN", "count": 41 }
  ],
  "countriesCollection": [
    { "name": "GB", "count": 5655 },
    { "name": "IE", "count": 1130 },
    { "name": "US", "count": 6917 }
  ],
  "fileTypeCollection": [
    { "name": "E", "count": 1466 },
    { "name": "M", "count": 21622 }
  ]
}
```

Poi si ri-chiama lo stesso endpoint con i filtri scelti, per verificare che
il risultato sia quello atteso:

```bash
curl -X POST https://historicdata.betfair.com/api/GetCollectionOptions \
  -H 'content-type: application/json' \
  -H 'ssoid: YOUR_TOKEN_HERE' \
  -d '{
    "sport":"Horse Racing",
    "plan":"Basic Plan",
    "fromDay": 1, "fromMonth": 3, "fromYear": 2017,
    "toDay": 31, "toMonth": 3, "toYear": 2017,
    "eventId": null,
    "eventName": null,
    "marketTypesCollection": [ "WIN", "PLACE" ],
    "countriesCollection": [ "GB", "IE" ],
    "fileTypeCollection": [ "M" ]
}'
```

**`fileTypeCollection`**: `M` = market data (contiene i **prezzi**, è quello
che serve), `E` = event data.

## `GetAdvBasketDataSize` — quanti file e quanti MB

Stesso corpo di `GetCollectionOptions`. Da usare **prima** di scaricare.

```json
{
  "totalSizeMB": 9,
  "fileCount": 1724
}
```

## `DownloadListOfFiles` — l'elenco dei percorsi

Stesso corpo. Scaricare i file uno per uno da questo elenco è più veloce che
farsi costruire un TAR unico dalla pagina "My Data", e in più rende visibili
i market id.

```json
[
  "/data/xds/historic/BASIC/28139610/1.130129050.bz2",
  "/data/xds/historic/BASIC/28139610/1.130129060.bz2",
  "/data/xds/historic/BASIC/28133820/1.130026702.bz2"
]
```

Struttura del percorso: `.../BASIC/<eventId>/<marketId>.bz2`.

## `DownloadFile` — il singolo file

Il percorso va **URL-encoded** nel parametro `filePath`.

```bash
curl -o data.bz2 \
  'https://historicdata.betfair.com/api/DownloadFile?filePath=%2Fdata%2Fxds%2Fhistoric%2FBASIC%2F28139610%2F1.130129050.bz2' \
  -H 'ssoid: YOUR_TOKEN_HERE'
```

Il file è compresso **bz2** e contiene lo stream registrato (un JSON per
riga). Per il formato interno: `40_stream__exchange_stream_api.md`.

---

## Dove sono implementati, nel progetto

`scripts/fetch_betfair_historic.py` — tutti e 5 gli endpoint più il parsing
dello stream. Il parser è coperto da `tests/test_betfair_historic.py`
(12 casi, fra cui il no-look-ahead e la semantica di `img`).
