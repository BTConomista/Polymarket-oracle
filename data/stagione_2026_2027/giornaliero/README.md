# `giornaliero/` — la fonte di verità temporale (APPEND-ONLY)

Una cartella per giorno, `YYYY-MM-DD/`. **Non si sovrascrive e non si corregge
un file di ieri**: se un dato di ieri era sbagliato, la correzione è un record
di **oggi** che cita quello di ieri. Il motivo è uno solo, ed è il motivo per
cui questa cartella esiste: deve restare sempre possibile rispondere a *«che
cosa sapevamo il giorno D?»*. Un file riscritto rende il test prospettico
(Fase 78) invalido senza lasciare traccia.

| file | contenuto |
|---|---|
| `raccolta.json` | i record del giorno, ognuno con `tipo` (fatto/giudizio), `fonte`/`evidenza`, `raccolto_utc` |
| `fonti.json` | **ogni** fetch tentato: URL, orario, esito HTTP, byte. Anche i falliti |
| `quote.json` | istantanea del mercato per le partite imminenti (vedi `data/smarkets_matches/`) |

**`fonti.json` non è un accessorio.** È ciò che distingue «quel giorno non è
successo niente» da «quel giorno il raccoglitore non ha girato» — la stessa
ambiguità che alla Fase 118 ha prodotto un workflow verde che non raccoglieva
nulla. Un giorno senza `fonti.json` è un giorno di cui non sappiamo niente,
e va trattato come tale in ogni analisi.
