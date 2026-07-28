# Manuale di sopravvivenza — l'ambiente di lavoro, verificato sul campo

## ⚠️ AGGIORNAMENTO — la rete è tornata raggiungibile (integrazione delle 5 leghe)

Molto di ciò che questo manuale dava per bloccato **risponde 200** dalla Fase 100.
Verificato scaricando davvero, non solo pingando:

| dominio | prima | dalla Fase 100 |
|---|---|---|
| `football-data.co.uk` | 403 | **200** — 45 stagioni ri-scaricate |
| `understat.com` | 403 | **200**, ma dietro `GET /main/getLeagueData/{Lega}/{anno}` con header `X-Requested-With: XMLHttpRequest` (senza header → 404) e risposta **gzip** |
| `transfermarkt.com` | bloccato | **200** |
| Kaggle via `kagglehub` | serviva il runner Actions | **funziona in sessione** |
| `betexplorer.com`, `oddsportal.com` | — | raggiungibili, ma vedi sotto |

**Conseguenza principale:** si può verificare gli snapshot **contro la
fonte-madre**, non solo contro sé stessi. È il controllo forte, e non era mai
stato fatto.

> **La tabella qui sopra è STORIA** (il "prima/dopo" della Fase 100). La mappa
> di rete **autorevole e corrente** è quella di **§1**, ri-verificata host per
> host con `curl` il **2026-07-28**: se le due divergono, ha ragione §1.

**Vincoli che restano, e vanno rispettati:**
- `oddsportal.com` **vieta le pagine storiche** nel suo `robots.txt`
  (`Disallow: *-2017*`, `*-2018*`): non si scrapano, e non si aggira il divieto
  passando da cache o archivi;
- `betexplorer.com` ha **ritirato** il confronto-quote per le partite di ~8 anni
  fa (tab 1X2 disabilitato, nessun tab O/U): ri-verificato, non è un problema di
  parsing;
- `sofascore.com` e `fbref.com` rispondono **403** anche sul `robots.txt`
  (ri-verificato 2026-07-28);
- throttle ≥ 1,5 s fra richieste, sempre.

**Una fonte nuova che funziona:** `footiqo.com` pubblica le quote di chiusura del
book **1xBet** (1X2, O/U 0.5/1.5/2.5/3.5/4.5, **GG/NG**) per stagione, servite
via `admin-ajax.php` — endpoint esplicitamente **permesso** dal suo `robots.txt`,
e il sito offre di suo l'export CSV. È la fonte da cui sono uscite le **5.337
partite 2017-20** con quote GG/NG di chiusura sulle 5 leghe (Fase 100): il dato
esiste, ed è stato **deliberatamente NON inserito** negli snapshot (un solo
book, peggiore della stima come proxy della media multi-book — vedi
[CACCIA_OU_2017_19.md](CACCIA_OU_2017_19.md)).

**Trappola scoperta sul campo (FotMob):** il `robots.txt` vieta il loro `/api/*`,
quindi si usano solo le pagine; e l'URL senza il frammento `#matchId` **rende
un'altra partita** della stessa coppia. Verificare sempre `matchTimeUTC` prima di
leggere i numeri. Nota di merito: il loro xG è un **modello diverso** da
Understat, quindi non va mescolato nella stessa colonna.

---

Questo file raccoglie la conoscenza **operativa** dell'ambiente di sviluppo
cloud: cosa è raggiungibile e cosa no, i limiti reali degli strumenti, i
trucchi di GitHub Actions, le fonti già valutate (e scartate). Serve a NON
ri-scoprire da zero questi fatti a ogni sessione. Le **piste di
miglioramento dei modelli** stanno invece in [PISTE.md](PISTE.md).
**Va aggiornato ogni volta che si scopre un fatto operativo nuovo.**

**Ultimo aggiornamento: 2026-07-28.** La mappa di rete di §1 è stata
**ri-testata host per host** con
`curl -sS -o /dev/null -w "%{http_code}" --max-time 15 <url>` (un timeout, che
si vede come `000`, **non è** un 403: sono cause diverse e vanno distinte). Il
contenuto di fondo viene dalla **Fase 100** (integrazione delle 5 leghe: la rete
è tornata raggiungibile, vedi il banner in testa), verificato dall'audit della
**Fase 101**.

## 1 · Mappa della rete dall'ambiente cloud (tutta verificata, mai presunta)

**Host BLOCCATI o inutilizzabili (ri-testati 2026-07-28):**

| host | esito misurato | uso che se ne farebbe |
|---|---|---|
| `api.github.com` | la **radice** risponde 200 ma con corpo vuoto (`{}`); ogni endpoint reale → **403** con «GitHub access to this repository is not enabled for this session» (session-scoped). In pratica: inutilizzabile, usare l'MCP GitHub (§2) | REST GitHub |
| `pub-*.r2.dev` (CDN di transfermarkt-datasets) | **non ri-testabile sull'URL vero**: nessun URL originale è mai stato registrato nel repo. Un bucket generico (`pub-test.r2.dev`) risponde **401**, cioè la richiesta **esce** dal proxy → l'etichetta storica «000/bloccato» **non è più dimostrata**. Da riprovare solo se ricompare l'URL vero | download diretto player-scores |
| `sofascore.com`, `fbref.com` | **403** anche sul `robots.txt` | statistiche partita alternative |
| `sportsbook-nash.draftkings.com` | **403** (geo-blocco) | quote US |
| `*.betfair.com` | **403** | borsa scommesse |
| `cds-api.bwin.com` | **000** (timeout, non 403) | quote bookmaker |
| `api.the-odds-api.com` | 200 ma **401 senza chiave** — serve una registrazione (nessuna chiave disponibile) | quote multi-book |

**Host RAGGIUNGIBILI (tutti ri-verificati 200 il 2026-07-28 salvo dove detto):**

| host | note |
|---|---|
| `football-data.co.uk` | **200 dalla Fase 100** (era 403: vedi il banner in testa). È la fonte primaria: 45 stagioni ri-scaricate |
| `understat.com` | **200 dalla Fase 100** (era 403). Richiede `GET /main/getLeagueData/{Lega}/{anno}` con header `X-Requested-With: XMLHttpRequest` (senza header → 404) e risposta **gzip** |
| `transfermarkt.com` / `.it` | **200 dalla Fase 100** (era «curl 000 + WebFetch fallisce»). Valori rosa ufficiali |
| `footiqo.com` | **200**. Attenzione: `www.footiqo.com` fa **301** verso l'apex `footiqo.com` — seguire i redirect (`curl -L`). Quote di chiusura 1xBet, incluso **GG/NG** (vedi banner in testa) |
| `raw.githubusercontent.com` | tutti i repo pubblici (openfootball, salimt, …) |
| `github.com` (pagine HTML) | utile per verifiche di esistenza |
| pypi / npm / crates | in NO_PROXY, installazioni ok |
| `gamma-api.polymarket.com` | Gamma API di Polymarket, quote LIVE di eventi/mercati aperti (verificato 2026-07-24). Vedi §2-bis e `scripts/fetch_polymarket_open.py` |
| `api.smarkets.com` | API v3 **pubblica, senza chiave**, JSON (verificato 2026-07-25). Borsa scommesse a soldi veri. Quota gli **outright** (campione, retrocessione, Top 2/3/4/5/6, top-half) delle 5 leghe. Vedi §1-bis e `scripts/fetch_smarkets_outrights.py` |
| `huggingface.co` (download file `/resolve/`) | **RAGGIUNGIBILE** (ri-verificato 2026-07-27, era CONNECT 403): 307→200 su un file reale del dataset `ngeorgea/transfermarkt-player-scores` |
| `datasets-server.huggingface.co` (API righe/filtri) | **RAGGIUNGIBILE** (ri-verificato 2026-07-27, era CONNECT 403): righe reali restituite per un dataset valido (es. `stanfordnlp/imdb`). Attenzione: la **radice** del dominio risponde 404 — non è un blocco, è che non esiste una pagina lì: testare sempre un endpoint vero (`/rows?dataset=…`) |
| `data.jsdelivr.com` | **RAGGIUNGIBILE** (ri-verificato 2026-07-27, era CONNECT 403; già notato raggiungibile nell'audit Fase 100/101 senza però correggere questa tabella): JSON reale dei tag npm di `react` |
| `oddsportal.com` | **200** — ma le pagine storiche sono vietate dal suo `robots.txt` e il feed outright è cifrato (vedi sotto) |
| `betexplorer.com` | **200 solo con User-Agent da browser.** Con lo UA di default di `curl` risponde **404 anche sulla home**: un 404 qui non è «pagina inesistente», è filtro anti-bot. Il `robots.txt` invece risponde 200 sempre |

Polymarket e Smarkets sono le **due** fonti di quote **prospettiche reali**
aperte dall'ambiente cloud (test prospettico 2026-27, Fase 78).

**Trappola generale, pagata due volte:** un codice di stato va letto **insieme
al modo in cui è stato chiesto**. `000` = timeout/connessione rifiutata; `403` =
il proxy o il sito rifiutano; `404` può essere un filtro anti-bot
(betexplorer con UA `curl`) o semplicemente una radice senza pagina
(`datasets-server.huggingface.co`); `401` significa che la richiesta è **uscita**
e il servizio chiede credenziali. Marcare un host «bloccato» senza distinguerli
è ciò che ha tenuto etichette false in questo file per mesi.

**Perché OddsPortal e BetExplorer, pur raggiungibili, non si usano
(~~Non ancora testati~~ → TESTATI il 2026-07-25, Fase 97: la previsione era
SBAGLIATA).** Nessuno dei due è bloccato dal proxy cloud, e `oddsportal.com`
**non** subisce il redirect ADM da qui (l'IP del container non è italiano: il
vincolo geo descritto sotto vale per il browser dell'utente, non per questa
sessione). Sono comunque **inutilizzabili**, per motivi diversi da quelli
attesi:

| host | esito reale | perché non si usa |
|---|---|---|
| `oddsportal.com` | 200, pagina outright servita | il feed `/feed/outrights/1-*.dat` restituisce un **blob base64 cifrato (AES)**: servirebbe estrarre la chiave dal bundle JS a ogni loro rilascio — fragile e sproporzionato; in più il `robots.txt` vieta le pagine storiche |
| `betexplorer.com` | 200 sulla home **con UA da browser**, **404** su `/outrights/` e `/winner/` (anche con UA da browser: ri-verificato 2026-07-28) | non ha proprio una sezione outright; e per le partite di ~8 anni fa ha **ritirato** il confronto-quote (vedi [BETEXPLORER_SCRAPER.md](BETEXPLORER_SCRAPER.md)) |

Le pagine **risultati** di BetExplorer, invece, ci sono ancora: la stagione
`/football/italy/serie-a-2017-2018/results/` risponde **200** (con UA da
browser, ri-verificato 2026-07-28). È il livello sopra a mancare, non il sito.

**Lezione operativa**: «presumibilmente bloccato» non è un fatto. Questi due
host erano marcati per esclusione da mesi e bastava un `curl` per smentirlo —
e la sorpresa vera (Smarkets, §1-bis) è arrivata proprio dal provare tutta la
lista invece di fidarsi delle etichette. Corollario scoperto il 2026-07-28: e
bastava **uno User-Agent** per smentire pure il 404 di BetExplorer.

**Vincolo geo/ADM (testato da IP italiano, browser utente, non dalla
sessione cloud)**: `betexplorer.com` forza l'edizione `/it/` per IP
italiani, e in quell'edizione il sotto-percorso `/1x2/` (tabella di
confronto quote) reindirizza silenziosamente alla pagina base della
partita (che mostra solo bonus di operatori ADM); forzare `/en/` da'
404, il prefisso `/it/` viene reinserito lato server. `oddsportal.com` fa
un 302 server-side verso `centroquote.it` (mirror italiano ADM-compliant):
non e' un consent banner, e quel mirror elenca solo bookmaker con licenza
ADM (niente Pinnacle, mai). Su entrambi i siti lo storico
apertura/chiusura per singola quota (tooltip/modal `archiveOddsModal`) e'
visibile solo da **loggati**. Rilevante perche' e' un blocco DIVERSO da
quello del proxy cloud (dipende dalla geolocalizzazione IP, non
dall'ambiente): un runner GitHub Actions (IP tipicamente US/EU non
italiano) presumibilmente non lo incontra, ma va verificato sul campo
(dump HTML del probe) prima di darlo per scontato.

**Il canale che aggira tutto**: un workflow **GitHub Actions** — il runner ha
rete libera, scarica e committa i dati compressi nel repo, e la sessione li
legge dal branch (pattern della Fase 67, v. §3).

**Canale alternativo per un recupero manuale una tantum (Fase 70)**: quando
serve un numero pubblico ma non rigenerabile via script (es. il valore rosa
attuale di un club su Transfermarkt), un'AI con un vero browser (Claude
Cowork + estensione Chrome, sessione utente) raggiunge siti bloccati dal
proxy di QUESTA sessione — diverso dal canale Actions perché e'
interattivo/una tantum, non automatizzabile in un workflow.
~~(`transfermarkt.com`)~~ **PREMESSA CADUTA**: l'esempio d'epoca era proprio
Transfermarkt, che **dalla Fase 100 risponde 200 da qui** (§1) e non ha più
bisogno di questo canale. Il canale resta valido in generale, per i siti
ancora fuori portata (`sofascore.com`, `fbref.com`, …) o per ciò che richiede
una sessione loggata.
**Attenzione al timing**: la pagina PROFILO club (`startseite`, `kader`
senza `saison_id`) mostra sempre il valore LIVE di oggi, non quello storico
della stagione che serve (il nostro `squad_value` è "a inizio stagione",
1° settembre — mesi prima di oggi se la stagione è già in corso/conclusa).
Il dato storico corretto sta nella pagina di **competizione filtrata per
stagione** (`.../{lega}/startseite/wettbewerb/{codice}/saison_id/{anno}`,
es. `IT1` Serie A, `GB1` Premier, `ES1` LaLiga — i codici di **Bundesliga e
Ligue 1 non sono registrati nel repo**: vanno letti sulla fonte prima di
usarli, non indovinati), che elenca ogni club con il
valore rosa registrato in quella specifica annata. Verifica di sanità che
ha funzionato: club poi retrocessi mostrano un valore storico ben diverso
(più alto) di quello attuale — se i due numeri coincidessero, la pagina
sarebbe quella live sbagliata.

**Nota tecnica**: nella stessa sessione, `WebFetch` può smettere di
funzionare **del tutto** (403 anche su `example.com`, non solo sui domini
attesi) — segnale di un problema del tool stesso, non del sito target;
prima di concludere "sito bloccato" testare un URL banale per escluderlo.

## 1-bis · Smarkets: la SECONDA borsa (Fase 97)

*(Sezione spostata qui il 2026-07-28: stava dopo §2-bis, fuori ordine. Testo
invariato.)*

`api.smarkets.com` è raggiungibile e la sua **API v3 è pubblica e senza
chiave** → **`scripts/fetch_smarkets_outrights.py`**. Smarkets è una *borsa*
(come Polymarket, non come un bookmaker): i prezzi sono ordini di utenti,
somma dei mercati esclusivi ~100-104% invece di 108-115%.

- **Navigazione dell'albero**: `GET /v3/events/?parent_id=N` — attenzione,
  `/v3/events/N/children/` **non esiste** (404). Radice calcio `121005`;
  gli outright di stagione vivono TUTTI sotto il nodo **`649058`**
  (`/sport/football/outright`), non sotto la lega.
- **Prezzi**: `/v3/markets/{id}/contracts/` (gli esiti) + `/v3/markets/{id}/quotes/`
  (libro ordini). Gli interi sono **centesimi di punto percentuale**: `3448` =
  34.48%.
- **Rate limit**: senza pause il giro completo prende un **429** a metà. Lo
  script mette 0.35 s fra le chiamate e ritenta con backoff.
- **Cosa aggiunge rispetto a Polymarket** (misurato il 2026-07-25):
  la **retrocessione** (che Polymarket non quota in nessuna lega) e i
  piazzamenti **Top 2/3/4/5/6 e top-half**. Sulla **Premier** è molto più
  liquido (spread 0.11pp contro un overround Polymarket del 5.8%); sulla
  **Serie A** è il contrario (spread ~5-11pp). **Le due fonti sono
  complementari: nessuna domina.**
- **Trappola dei libri monchi**: molti mercati Top-N hanno **solo offerte**.
  Un ask senza bid non è un prezzo (è un *tetto* al valore equo) e va marcato,
  non buttato — buttandolo sparivano 6 mercati interi.
- **Omonimie**: esistono due eventi `Championship 26/27` (inglese e scozzese)
  con **slug identico** e nessun campo che li distingua, e un `Serie A Women
  26/27` che un match ingenuo sul prefisso archivierebbe come Serie A. Vedi i
  filtri `EXCLUDE_COMP` / `LEAGUE_EVENTS` nello script.

## 2 · Strumenti della sessione: limiti misurati

- **MCP Hugging Face**: autenticato (utente BTConomista); `hf_fs cat` legge
  max **80 KB per chiamata** (un file da 32 MB = ~400 chiamate: impraticabile);
  `hub_repo_search`/`hub_repo_details` funzionano; `hf_hub_query` naviga solo
  METAdati, non contenuti; il viewer del mirror
  `ngeorgea/transfermarkt-player-scores` è **rotto** (cast error, niente
  export parquet → niente API righe).
- **MCP GitHub**: unico canale per le Actions (il REST è negato, v. §1);
  `get_job_logs` richiede il `job_id` (da `list_workflow_jobs`).
- **WebSearch** funziona (US-only); **WebFetch** funziona sui domini permessi.
- **Monitorare un workflow Actions dalla sessione**: il segnale più affidabile
  ed economico è il **polling di `git ls-remote`** sul branch (il workflow
  committa alla fine) — usato col tool Monitor. In alternativa, MCP
  `actions_list`.
- **`pytest` NON è preinstallato nel container** (verificato 2026-07-28): a
  sessione fresca `python -m pytest` fallisce. Il primo comando di ogni
  sessione che deve toccare codice è
  ```bash
  pip install -e ".[dev]"
  ```
  che installa il pacchetto in editable più le dipendenze di test dichiarate in
  `pyproject.toml`. Dopo di che `python -m pytest -q` gira: la suite raccoglie
  **841 test** (`python -m pytest -q --collect-only`, 2026-07-28). Se un
  documento del repo cita un numero di test diverso come stato *attuale*, è
  scaduto; se lo cita come stato storico di una fase, va lasciato ma marcato
  come tale.
- **`curl` esce dal proxy senza configurazione** (il CA bundle è già a posto):
  è lo strumento giusto per ri-testare la mappa di §1. Non disattivare mai la
  verifica TLS né togliere `HTTPS_PROXY` per far passare una richiesta.

## 2-bis · Polymarket: quote LIVE dall'ambiente (script pronto)

`gamma-api.polymarket.com` è **raggiungibile** (§1) → abbiamo uno strumento
riutilizzabile: **`scripts/fetch_polymarket_open.py`**. Serve a non rifare la
fatica ogni volta che servono quote reali di partite non ancora giocate.

- **Endpoint**: `GET /events/keyset?closed=false&limit=100`, paginazione
  **keyset** (`next_cursor` in risposta → si passa come `?after_cursor=`; stop
  quando manca il cursore o il batch è vuoto). Il 2026-07-24: **13.5k eventi
  aperti / ~113k mercati**.
- **Struttura**: un *event* raggruppa più *markets* (`event["markets"]`);
  `outcomes`/`outcomePrices` sono **stringhe JSON**; una partita è **spezzata
  in più eventi**: `A vs. B` = 1X2 (3 mercati Yes/No), `A vs. B - More Markets`
  = O/U 1.5/2.5/3.5/4.5 + BTTS, poi Halftime/Exact Score ecc. I prezzi sono già
  **probabilità implicite (con vig)**.
- **Uso**:
  ```bash
  python scripts/fetch_polymarket_open.py                  # dump completo
  python scripts/fetch_polymarket_open.py --tag Soccer     # solo calcio (~5k eventi)
  python scripts/fetch_polymarket_open.py --soccer-matches # partite -> 1X2+O/U+BTTS
  ```
  `--soccer-matches` ricostruisce ogni partita, deviga l'1X2 (normalizza a 1) e
  produce il record `{one_x_two, over_under, btts}` — **l'input che
  `market_implied.py` sa invertire** in λ,μ.
- **Attenzione stagionalità**: a fine luglio Serie A/Premier/La Liga sono **fuori
  stagione** (solo futures "2027 Champion"); ripartono a metà agosto. Le quote
  match ci sono per le leghe estive (MLS, Brasile, Sudamerica, ecc.). Overround
  osservato sui match minori ~1.17 (vig alta).
- **Output NON versionato**: è un tool LIVE, scrive in `data/polymarket/`
  (in `.gitignore`) — mai dentro gli snapshot congelati. Test puro delle funzioni
  in `tests/test_polymarket_fetch.py` (senza rete).

## 3 · GitHub Actions: fatti operativi

- **`workflow_dispatch` e `schedule` partono SOLO dal branch di default**
  (main). Il fatto in sé regge; ~~il nostro main è vuoto → il pulsante "Run
  workflow" e il cron mensile di `import_dataset.yml` si attiveranno solo
  quando il file arriverà su main~~ — **PREMESSA CADUTA.** Dalla Fase 82 si
  lavora e si committa **direttamente su `main`** (regola §3-bis del
  CLAUDE.md), e i tre workflow sono **su main** (verificato 2026-07-28:
  `git ls-tree --name-only main .github/workflows/` elenca
  `betexplorer-scrape.yml`, `import_dataset.yml`, `kaggle-ou-probe.yml`).
  Quindi `workflow_dispatch` è ora azionabile dalla tab Actions. Resta valido
  e utile il workaround **trigger `on: push` sul file-segnale**
  (`.github/import-dataset-trigger`), che legge il workflow dal branch pushato
  e funziona da qualsiasi branch. **Nota**: i commenti dentro i due file
  `.yml` ripetono ancora la premessa caduta («main, qui ancora vuoto») — è
  documentazione scaduta nel codice, non un fatto.
- **Nessuno dei tre workflow è un'automazione viva**: `import_dataset.yml` ha
  il cron mensile disattivato (motivazione dell'audit Fase 92 scritta nel
  file), e `betexplorer-scrape.yml` / `kaggle-ou-probe.yml` puntano alla
  caccia O/U 2017-19, **chiusa alla Fase 100**. Sono conservati come
  riferimento: non lanciarli senza aver riletto
  [CACCIA_OU_2017_19.md](CACCIA_OU_2017_19.md).
- **`kagglehub` scarica dataset pubblici SENZA credenziali** dal runner
  (verificato nei run 1 e 2); banda ~250 MB/s; run completo ~35-40 s.
- **gzip non è deterministico di default** (timestamp nell'header): senza
  `mtime=0` ogni run committava file "cambiati" a contenuto identico. Fixato
  nel workflow (i run a contenuto invariato saltano il commit).
- Vintage dei dati in `files/player_scores/`: **Kaggle, 18 luglio 2026**;
  l'upstream si aggiorna ~settimanalmente e **backfilla lo storico**.

## 4 · Fonti esterne valutate in sessione

| fonte | esito |
|---|---|
| `davidcariboo/player-scores` (Kaggle, CC0) | **fonte ufficiale squad_value** (Fase 67); contiene ALTRI file mai importati → [PISTE.md](PISTE.md) §3 |
| `ngeorgea/transfermarkt-player-scores` (HF) | mirror valido (agg. giu 2026), fallback nel workflow; viewer rotto |
| `dcaribou/transfermarkt-datasets` (GitHub) | repo sorgente: dati via DVC/R2, non in git; 508k valutazioni, 31.5k giocatori, 2000-01→2026-02 |
| dataset "Beat the Bookie" (open+close storici) | **fuori finestra** (si ferma ~2015) — non riproporre |
| `salimt/football-datasets` | resta la fonte degli infortuni; per i valori è superato (~25% profili senza valutazioni) |
| `footiqo.com` (quote di chiusura 1xBet) | **trovata e misurata** (Fase 100): 1X2, O/U 0.5→4.5 e **GG/NG** per 5.337 partite 2017-20 su 5 leghe. Dato reale, **deliberatamente NON inserito** negli snapshot: un solo book, peggiore della stima come proxy della media multi-book. Vedi [CACCIA_OU_2017_19.md](CACCIA_OU_2017_19.md) |
| `betexplorer.com` (O/U 2017-19 apertura/chiusura) | ❌ **chiusa negativa** (Fase B): il sito ha ritirato il confronto-quote per le partite di ~8 anni fa, copertura 0%. Scraper e verbale conservati in [BETEXPLORER_SCRAPER.md](BETEXPLORER_SCRAPER.md) |
| `oddsportal.com` | ❌ **esclusa**: `robots.txt` vieta le pagine storiche; il feed outright è un blob AES; lo storico per singola quota richiede login |

---

*Cosa NON sta qui (perché già scritto altrove): le fasi in DIARIO.md, il
catalogo dati in DATI.md, la rosa dei modelli in PANCHINA.md, la caccia alle
quote O/U in CACCIA_OU_2017_19.md, i commenti del workflow.*
