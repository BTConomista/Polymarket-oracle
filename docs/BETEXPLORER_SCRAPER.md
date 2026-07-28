# OU 2.5 apertura/chiusura — scraper BetExplorer (Fase B)

> ⚠️ **PISTA CHIUSA, NEGATIVA. Non rilanciare lo scraper senza aver riletto
> questo riquadro.**
>
> - **Fase B è fallita** (probe live via GitHub Actions, 5 giri): **copertura
>   0%**. Il sito ha **ritirato il confronto-quote** per le partite di ~8 anni
>   fa — sulla pagina-partita ci sono **zero** occorrenze di `match-odds`, e il
>   div `#bettingTabs` contiene **solo un "1X2" disabilitato** e **nessun tab
>   O/U**. Non è un problema di parsing né di URL: il dato non è più esposto,
>   quindi **nemmeno un headless browser aiuterebbe**. Stesso identico pattern
>   su **tutte e 3 le leghe** 2017-18 testate → nessuna delle 6 coppie
>   lega-stagione è raggiungibile con questo metodo. Verbale completo in §3 di
>   [CACCIA_OU_2017_19.md](CACCIA_OU_2017_19.md).
> - **La caccia a monte è chiusa alla Fase 100**: il dato è stato poi trovato
>   *altrove* (book **1xBet** via `footiqo.com`, **5.337 partite 2017-20** su 5
>   leghe) ed è stato **deliberatamente NON inserito** negli snapshot — un solo
>   book, peggiore della stima come proxy della media multi-book.
> - **Lo scraper non ha mai prodotto dati**: in `files/` non esiste alcun
>   `ou25_*.csv` né alcun checkpoint. Nessun numero del progetto dipende da
>   questa pista.
> - Restano nel repo, come riferimento storico:
>   `scripts/scrape_betexplorer.py` (402 righe), `scripts/check_acceptance.py`
>   (92 righe), `.github/workflows/betexplorer-scrape.yml`. Il menu del
>   workflow copre **3 leghe su 5**: è precedente all'ingresso di Bundesliga e
>   Ligue 1, e non va esteso (la pista è chiusa).
>
> *Stato del sito, ri-verificato il **2026-07-28** da questa sessione:*
>
> | URL | esito |
> |---|---|
> | `https://www.betexplorer.com/` con **UA da browser** | **200** |
> | `https://www.betexplorer.com/` con UA di default di `curl` | **404** — filtro anti-bot, non «pagina inesistente» |
> | `https://www.betexplorer.com/robots.txt` | **200** (sempre) |
> | `.../football/italy/serie-a-2017-2018/results/` | **200** — le pagine risultati **ci sono ancora** |
> | `https://www.betexplorer.com/outrights/` | **404** (anche con UA da browser) — non esiste una sezione outright |
>
> Cioè: il sito **è raggiungibile**, la pagina risultati funziona, ed è il
> livello sopra (il confronto-quote per partita) a essere sparito. Un `curl`
> senza User-Agent da browser restituisce 404 e fa sembrare bloccato tutto il
> dominio: è la trappola in cui si può ricadere ri-testando a mano. Lo script
> `scrape_betexplorer.py` **non** ci cade, perché dichiara già un UA da browser
> (`scripts/scrape_betexplorer.py:42`).

---

## Cosa doveva fare (obiettivo originario)

Attuare la **Fase B** del piano descritto in
[CACCIA_OU_2017_19.md](CACCIA_OU_2017_19.md): uno scraper per costruire la
tabella una riga per partita, 6 coppie lega-stagione (Serie A, Premier League,
La Liga × 2017-18, 2018-19 = 2.280 partite), con data, squadre, punteggio
finale e quattro quote decimali: Over/Under 2.5 di apertura e di chiusura. Book
preferito Pinnacle, poi media multi-book, poi Bet365 — la fonte è dichiarata
riga per riga nella colonna `book_source`.

> Nota sul bersaglio, per non rileggerlo storto: dalla **Fase 73** si sa che
> l'unica linea O/U di quelle stagioni (`BbAv`) è un'**apertura reale**, non una
> chiusura. Quindi mancava (e manca) solo la **chiusura** O/U — 2.280 celle, non
> 4.564.

File: `scripts/scrape_betexplorer.py`, `scripts/check_acceptance.py`,
`.github/workflows/betexplorer-scrape.yml`.

## Flusso previsto (probe prima, sempre) — mai arrivato oltre il passo 2

*Conservato perché il metodo «probe prima del run completo» è quello che ha
fatto scoprire il fallimento in un minuto invece che in mezza giornata: è la
parte riutilizzabile di questa pista.*

1. Actions → "Scrape BetExplorer OU 2.5" → Run workflow con `probe = true`
   (default) su `serie-a-2017-2018`. Dura ~1 minuto: scrappa 3 partite e salva
   in `debug/` l'HTML grezzo dell'endpoint AJAX.
2. Guarda il log: se le 3 partite escono con `status: ok` e quattro quote
   sensate con apertura ≠ chiusura, il parsing regge. Se no, i dump in
   `debug/ou_*.html` mostrano il markup reale: si aggiusta `parse_ou_html()`
   in `scripts/scrape_betexplorer.py` e si rilancia il probe.
   → **È qui che la pista si è fermata**: l'endpoint AJAX ha risposto 404 su
   tutte le partite testate, e il dump ha mostrato che i tab quote non esistono
   più. Nessun aggiustamento di `parse_ou_html()` poteva rimediare.
3. ~~Run completo: `probe = false`, una lega-stagione per volta (~380 pagine,
   throttle 2-3 s ≈ 20-25 min). Il CSV finisce in `files/` (commit automatico)
   e come artifact.~~ — mai eseguito.
4. ~~`scripts/check_acceptance.py` gira da solo nel run completo e stampa il
   report sui criteri del piano (§1 di CACCIA_OU_2017_19.md): copertura ≥95%,
   overround > 1 per riga, apertura ≠ chiusura nella grande maggioranza,
   quote di apertura presenti.~~ — mai eseguito.
5. ~~Ripetere per le altre 5 lega-stagioni (bastano 6 run del workflow) →
   Fase C del piano.~~ — la Fase C è stata **saltata**: né A né B hanno
   prodotto dati da scalare.

## Note tecniche (com'era costruito)

- Le quote O/U **erano** caricate via AJAX: `GET /match-odds/{id}/1/ou/` con
  header `X-Requested-With: XMLHttpRequest` e `Referer` alla pagina partita.
  **Oggi quell'endpoint risponde 404** per le stagioni target. La pagina
  risultati invece è server-side, contiene tutta la stagione, e **funziona
  ancora** (verificato 2026-07-28).
- Checkpoint JSONL in `files/ckpt_{slug}.jsonl`: un run interrotto riprende da
  dove era (rilanciando il workflow il checkpoint riparte da zero nel runner —
  se serve resume tra run, committare anche il checkpoint).
- Linea filtrata ESATTAMENTE `2.5` (mai 2.25/2.75). Le partite senza linea 2.5
  restano nel CSV con `status = no_line_25` e l'elenco delle linee viste nel
  checkpoint, così il buco di copertura è ispezionabile.
- Punteggio finale incluso per verificare il join con lo snapshot esistente
  (gol fonte == gol snapshot su ogni riga, join canonicalizzato).
- Etica: throttle randomizzato 2-3 s, backoff su 403/429, una stagione per run,
  User-Agent dichiarato (`scripts/scrape_betexplorer.py:42`).

## Colonne CSV (schema previsto, mai popolato)

`league, season, date, home, away, home_goals, away_goals, over_open,
under_open, over_close, under_close, book_source, n_books_line25, match_id,
status`

`book_source`: `pinnacle` | `avgN` (media di N book con 4 quote complete) |
`bet365` | nome del singolo book disponibile.

## Ingresso dei dati (procedura che non è mai stata attivata)

Vedi §3 di [CACCIA_OU_2017_19.md](CACCIA_OU_2017_19.md) per i controlli
d'ingresso (join gol fonte==snapshot, overround, apertura≠chiusura) e come le
colonne sarebbero entrate negli snapshot via la pipeline quote esistente.

## Cosa portarsi via (lezione, principio §1.4 del CLAUDE.md)

1. **Il probe da 3 partite prima del run da 380** ha isolato un fallimento
   strutturale in un minuto. Vale per qualunque scraper futuro.
2. **Un 404 non basta a diagnosticare**: qui è servito guardare l'HTML grezzo
   (`#bettingTabs` con solo un "1X2" disabilitato) per capire che il dato era
   stato *ritirato* e non *spostato*. Senza quel dump si sarebbe continuato a
   indovinare URL.
3. **Quando l'artifact zip del workflow non è scaricabile** dalla sessione
   (dominio Azure blob bloccato), la diagnostica va **stampata nei log del
   job** — leggibili via MCP GitHub — non salvata solo nell'artifact.
4. **Il dato è arrivato da un'altra strada** (footiqo/1xBet, Fase 100): una
   pista chiusa negativa non chiude la domanda, chiude *quel* metodo.
