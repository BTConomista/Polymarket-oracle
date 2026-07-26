# Manuale di sopravvivenza — l'ambiente di lavoro, verificato sul campo

## ⚠️ AGGIORNAMENTO — la rete è tornata raggiungibile (integrazione delle 5 leghe)

Molto di ciò che questo manuale dà per bloccato **oggi risponde 200**. Verificato
scaricando davvero, non solo pingando:

| dominio | prima | oggi |
|---|---|---|
| `football-data.co.uk` | 403 | **200** — 45 stagioni ri-scaricate |
| `understat.com` | 403 | **200**, ma dietro `GET /main/getLeagueData/{Lega}/{anno}` con header `X-Requested-With: XMLHttpRequest` (senza header → 404) e risposta **gzip** |
| `transfermarkt.com` | bloccato | **200** |
| Kaggle via `kagglehub` | serviva il runner Actions | **funziona in sessione** |
| `betexplorer.com`, `oddsportal.com` | — | raggiungibili, ma vedi sotto |

**Conseguenza principale:** si può verificare gli snapshot **contro la
fonte-madre**, non solo contro sé stessi. È il controllo forte, e non era mai
stato fatto.

**Vincoli che restano, e vanno rispettati:**
- `oddsportal.com` **vieta le pagine storiche** nel suo `robots.txt`
  (`Disallow: *-2017*`, `*-2018*`): non si scrapano, e non si aggira il divieto
  passando da cache o archivi;
- `betexplorer.com` ha **ritirato** il confronto-quote per le partite di ~8 anni
  fa (tab 1X2 disabilitato, nessun tab O/U): ri-verificato, non è un problema di
  parsing;
- `sofascore.com` e `fbref.com` rispondono **403** anche sul `robots.txt`;
- throttle ≥ 1,5 s fra richieste, sempre.

**Una fonte nuova che funziona:** `footiqo.com` pubblica le quote di chiusura del
book **1xBet** (1X2, O/U 0.5/1.5/2.5/3.5/4.5, **GG/NG**) per stagione, servite
via `admin-ajax.php` — endpoint esplicitamente **permesso** dal suo `robots.txt`,
e il sito offre di suo l'export CSV.

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
Ultimo aggiornamento: Fase 70 (luglio 2026).

## 1 · Mappa della rete dall'ambiente cloud (tutta verificata, mai presunta)

**Host BLOCCATI dal proxy:**

| host | esito | uso che se ne farebbe |
|---|---|---|
| `transfermarkt.com` / `.it` | curl 000 + WebFetch fallisce | valori rosa ufficiali |
| `huggingface.co` (download file `/resolve/`) | CONNECT 403 | dataset |
| `datasets-server.huggingface.co` (API righe/filtri) | CONNECT 403 | query server-side sui dataset HF |
| `pub-*.r2.dev` (CDN di transfermarkt-datasets) | 000 | download diretto player-scores |
| `data.jsdelivr.com` | CONNECT 403 | listing pacchetti |
| `football-data.co.uk`, `understat.com` | 403 (già noto, docs storiche) | fonti originali |
| `api.github.com` | endpoint generici → "sessions are bound to their configured repositories"; endpoint Actions → negati anche repo-scoped ("GitHub access is not enabled for this session") | REST GitHub |

**Host RAGGIUNGIBILI:**

| host | note |
|---|---|
| `raw.githubusercontent.com` | tutti i repo pubblici (openfootball, salimt, …) |
| `github.com` (pagine HTML) | utile per verifiche di esistenza |
| pypi / npm / crates | in NO_PROXY, installazioni ok |
| `gamma-api.polymarket.com` | **RAGGIUNGIBILE** (verificato 2026-07-24): Gamma API di Polymarket, quote LIVE di eventi/mercati aperti. Vedi §2-bis e `scripts/fetch_polymarket_open.py`. |
| `api.smarkets.com` | **RAGGIUNGIBILE** (verificato 2026-07-25): API v3 **pubblica, senza chiave**, JSON. Borsa scommesse a soldi veri. Quota gli **outright** (campione, retrocessione, Top 2/3/4/5/6, top-half) delle 5 leghe. Vedi §1-bis e `scripts/fetch_smarkets_outrights.py`. |

Polymarket e Smarkets sono le **due** fonti di quote **prospettiche reali**
aperte dall'ambiente cloud (test prospettico 2026-27, Fase 78).

**~~Non ancora testati~~ → TESTATI il 2026-07-25 (Fase 97): la previsione era
SBAGLIATA.** `betexplorer.com` e `oddsportal.com` **NON sono bloccati** dal
proxy cloud, e `oddsportal.com` **non** subisce il redirect ADM da qui (l'IP
del container non è italiano: il vincolo geo descritto sotto vale per il
browser dell'utente, non per questa sessione). Sono comunque **inutilizzabili**,
per motivi diversi da quelli attesi:

| host | esito reale | perché non si usa |
|---|---|---|
| `oddsportal.com` | 200, pagina outright servita | il feed `/feed/outrights/1-*.dat` restituisce un **blob base64 cifrato (AES)**: servirebbe estrarre la chiave dal bundle JS a ogni loro rilascio — fragile e sproporzionato |
| `betexplorer.com` | 200 sulla home, **404** su `/outrights/` e `/winner/` | non ha proprio una sezione outright |
| `api.the-odds-api.com` | 200 ma **401 senza chiave** | serve una registrazione (nessuna chiave disponibile) |
| `sportsbook-nash.draftkings.com` | 403 | geo-blocco |
| `cds-api.bwin.com`, `*.betfair.com` | 000 / 403 | bloccati |

**Lezione operativa**: «presumibilmente bloccato» non è un fatto. Questi due
host erano marcati per esclusione da mesi e bastava un `curl` per smentirlo —
e la sorpresa vera (Smarkets, §1-bis) è arrivata proprio dal provare tutta la
lista invece di fidarsi delle etichette.

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
proxy di QUESTA sessione (`transfermarkt.com`) — diverso dal canale Actions
perché e' interattivo/una tantum, non automatizzabile in un workflow.
**Attenzione al timing**: la pagina PROFILO club (`startseite`, `kader`
senza `saison_id`) mostra sempre il valore LIVE di oggi, non quello storico
della stagione che serve (il nostro `squad_value` è "a inizio stagione",
1° settembre — mesi prima di oggi se la stagione è già in corso/conclusa).
Il dato storico corretto sta nella pagina di **competizione filtrata per
stagione** (`.../{lega}/startseite/wettbewerb/{codice}/saison_id/{anno}`,
es. `IT1` Serie A, `GB1` Premier, `ES1` LaLiga), che elenca ogni club con il
valore rosa registrato in quella specifica annata. Verifica di sanità che
ha funzionato: club poi retrocessi mostrano un valore storico ben diverso
(più alto) di quello attuale — se i due numeri coincidessero, la pagina
sarebbe quella live sbagliata.

**Nota tecnica**: nella stessa sessione, `WebFetch` può smettere di
funzionare **del tutto** (403 anche su `example.com`, non solo sui domini
attesi) — segnale di un problema del tool stesso, non del sito target;
prima di concludere "sito bloccato" testare un URL banale per escluderlo.

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

## 1-bis · Smarkets: la SECONDA borsa (Fase 97)

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

## 3 · GitHub Actions: fatti operativi

- **`workflow_dispatch` e `schedule` partono SOLO dal branch di default**
  (main). Il nostro main è vuoto → il pulsante "Run workflow" e il cron
  mensile di `import_dataset.yml` si attiveranno solo quando il file arriverà
  su main. Workaround attivo: **trigger `on: push` sul file-segnale
  `.github/import-dataset-trigger`**, che legge il workflow dal branch pushato.
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

---

*Cosa NON sta qui (perché già scritto altrove): le fasi in DIARIO.md, il
catalogo dati in DATI.md, la rosa dei modelli in PANCHINA.md, la caccia alle
quote O/U in CACCIA_OU_2017_19.md, i commenti del workflow.*
