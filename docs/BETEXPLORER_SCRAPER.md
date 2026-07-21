# OU 2.5 apertura/chiusura — scraper BetExplorer (Fase B)

Attua la **Fase B** del piano descritto in
[CACCIA_OU_2017_19.md](CACCIA_OU_2017_19.md): scraper per costruire la tabella
una riga per partita, 6 coppie lega-stagione (Serie A, Premier League, La
Liga × 2017-18, 2018-19 = 2.280 partite), con data, squadre, punteggio finale
e quattro quote decimali: Over/Under 2.5 di apertura e di chiusura. Book
preferito Pinnacle, poi media multi-book, poi Bet365 — la fonte è dichiarata
riga per riga nella colonna `book_source`.

File: `scripts/scrape_betexplorer.py`, `scripts/check_acceptance.py`,
`.github/workflows/betexplorer-scrape.yml`.

## Flusso (probe prima, sempre)

1. Actions → "Scrape BetExplorer OU 2.5" → Run workflow con `probe = true`
   (default) su `serie-a-2017-2018`. Dura ~1 minuto: scrappa 3 partite e salva
   in `debug/` l'HTML grezzo dell'endpoint AJAX.
2. Guarda il log: se le 3 partite escono con `status: ok` e quattro quote
   sensate con apertura ≠ chiusura, il parsing regge. Se no, i dump in
   `debug/ou_*.html` mostrano il markup reale: si aggiusta `parse_ou_html()`
   in `scripts/scrape_betexplorer.py` e si rilancia il probe.
3. Run completo: `probe = false`, una lega-stagione per volta (~380 pagine,
   throttle 2-3 s ≈ 20-25 min). Il CSV finisce in `files/` (commit automatico)
   e come artifact.
4. `scripts/check_acceptance.py` gira da solo nel run completo e stampa il
   report sui criteri del piano (§1 di CACCIA_OU_2017_19.md): copertura ≥95%,
   overround > 1 per riga, apertura ≠ chiusura nella grande maggioranza,
   quote di apertura presenti.
5. Ripetere per le altre 5 lega-stagioni (bastano 6 run del workflow) →
   Fase C del piano.

## Note tecniche

- Le quote O/U sono caricate via AJAX: `GET /match-odds/{id}/1/ou/` con header
  `X-Requested-With: XMLHttpRequest` e `Referer` alla pagina partita. La pagina
  risultati invece è server-side e contiene tutta la stagione.
- Checkpoint JSONL in `files/ckpt_{slug}.jsonl`: un run interrotto riprende da
  dove era (rilanciando il workflow il checkpoint riparte da zero nel runner —
  se serve resume tra run, committare anche il checkpoint).
- Linea filtrata ESATTAMENTE `2.5` (mai 2.25/2.75). Le partite senza linea 2.5
  restano nel CSV con `status = no_line_25` e l'elenco delle linee viste nel
  checkpoint, così il buco di copertura è ispezionabile.
- Punteggio finale incluso per verificare il join con lo snapshot esistente
  (gol fonte == gol snapshot su ogni riga, join canonicalizzato).
- Etica: throttle randomizzato 2-3 s, backoff su 403/429, una stagione per run,
  User-Agent dichiarato.

## Colonne CSV

`league, season, date, home, away, home_goals, away_goals, over_open,
under_open, over_close, under_close, book_source, n_books_line25, match_id,
status`

`book_source`: `pinnacle` | `avgN` (media di N book con 4 quote complete) |
`bet365` | nome del singolo book disponibile.

## Ingresso dei dati

Vedi §3 di [CACCIA_OU_2017_19.md](CACCIA_OU_2017_19.md) per i controlli
d'ingresso (join gol fonte==snapshot, overround, apertura≠chiusura) e come le
colonne entrano poi negli snapshot via la pipeline quote esistente.
