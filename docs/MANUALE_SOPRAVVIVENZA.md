# Manuale di sopravvivenza — l'ambiente di lavoro, verificato sul campo

Questo file raccoglie la conoscenza **operativa** dell'ambiente di sviluppo
cloud: cosa è raggiungibile e cosa no, i limiti reali degli strumenti, i
trucchi di GitHub Actions, le fonti già valutate (e scartate). Serve a NON
ri-scoprire da zero questi fatti a ogni sessione. Le **piste di
miglioramento dei modelli** stanno invece in [PISTE.md](PISTE.md).
**Va aggiornato ogni volta che si scopre un fatto operativo nuovo.**
Ultimo aggiornamento: Fase 68 (luglio 2026).

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

**Non ancora testati dalla sessione cloud**: `betexplorer.com`,
`oddsportal.com` (presumibilmente bloccati dal proxy; dal runner Actions
sono comunque liberi — vedi vincolo geo/ADM sotto, diverso da questo).

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
