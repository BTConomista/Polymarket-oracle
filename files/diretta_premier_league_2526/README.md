# Statistiche per giocatore, Premier League 2025-26 — diretta.it / Flashscore

> **Seconda raccolta del progetto**, dopo `files/diretta_serie_a_2526/`.
> **11.492 righe giocatore-partita × 97 statistiche**, e — a differenza della
> Serie A — **copertura piena: 380 partite su 380, nessun buco.**

## 1 · Provenienza

| | |
|---|---|
| **fonte** | **diretta.it (Flashscore)**, gruppo Livesport s.r.o. |
| **dato a monte** | **Opta / Stats Perform** |
| **raccolta** | **a mano dall'utente**, nessuno scraping |
| **estrazione** | 31 luglio 2026 |

**Licenza**: il progetto non rivendica alcun diritto su questi dati. Il quadro
per intero — identico a quello della Serie A — è in
`files/diretta_serie_a_2526/README.md` §1-bis, e in `docs/CACCIA_EVENT_DATA.md`
§1. Scelta consapevole del titolare del repo.

## 2 · I file

| file | righe × col |
|---|---|
| `partita_per_partita.csv.gz` | **11.492 × 108** |
| `riepilogo_stagionale.csv.gz` | 570 × 107 |
| `manifesto.json` | perimetro e copertura attesa, letti dalle guardie del caricatore |
| `report_verifica_utente.md` | il report di chi ha raccolto, non modificato |

Le colonne sono **le stesse 97** della Serie A: la `legenda.csv` della prima
raccolta vale anche qui.

## 3 · Copertura

- **380/380 partite**, **760 team-partita**, 20 squadre, **537 giocatori**
- finestra: **15/08/2025 → 24/05/2026**
- **nessuna partita mancante** — il manifesto ha `partite_mancanti` vuoto

## 4 · Verifica indipendente (01/08/2026)

Rieseguiti i controlli del report dell'utente sul file, più il confronto col
nostro snapshot (football-data.co.uk, **fonte diversa**):

| controllo | esito |
|---|---|
| **join** a `data/premier_league_matches.csv` | **760/760 = 100%** |
| **coerenza gol** (`gol giocatori + autogol avversari == risultato snapshot`) | **760/760 = 100%** |
| gol totali del campionato | **1.045** ✓ (come il report) |
| **11 titolari** per squadra-partita | **760/760** ✓ |
| squadra-partita sotto 985′ | **36**, ✓ **tutte con un'espulsione, 0 senza** |
| classifica ricostruita **dal file** | **20/20 con 38 partite ciascuna**, punti coincidenti |
| marcatori | Haaland 27, Thiago 22, Semenyo 17 ✓ |
| assist | Fernandes 21 ✓ |

> ✅ **Il report è confermato per intero, §3.1 compreso** — e qui è una
> differenza sostanziale rispetto al gemello sulla Serie A. Là la
> ricostruzione della classifica «20/20 esatta» **non poteva venire dal
> dataset**, perché Como e Lecce avevano 37 partite (mancava Lecce-Como) e il
> file rendeva 68 punti al Como contro i 71 ufficiali. Qui, **non mancando
> nulla**, la stessa affermazione è vera davvero: ricostruendo dal file si
> ottengono 38 partite per tutte e 20 le squadre e i punti giusti.
> *La differenza non è nel metodo del report: è nel dato.*

## 5 · Un alias mancante, trovato dalla guardia

Alla prima registrazione il join si è fermato a **544/760**. Non un errore dei
dati: **3 nomi squadra su 20** seguono una convenzione diversa dalla nostra —
diretta.it scrive `Manchester Utd` e `Nottingham`, i nostri snapshot (che
vengono da football-data) `Man United` e `Nott'm Forest`.

I due alias sono stati aggiunti a **`src/data/sources.py::TEAM_ALIASES`**, che
è dove il progetto li tiene da sempre, e ora il caricatore li applica: il join
è passato a **760/760**.

> È esattamente il caso per cui `TEAM_ALIASES` esiste — il bug «Hellas Verona»
> del §5 del `CLAUDE.md`. E la parte che conta è che **il join non ha fallito
> in silenzio**: la guardia ha rifiutato la raccolta finché il conto non
> tornava. Con 216 righe orfane su 760, un join permissivo avrebbe prodotto
> statistiche credibili e sbagliate.

## 6 · ⏱️ R8 e limiti

Valgono **identici** alla Serie A (`files/diretta_serie_a_2526/README.md` §5-6):
tutte e 97 le statistiche sono **`post`**, la forma d'uso è aggregare le
partite **precedenti** via `team_form()`, il riepilogo stagionale è utilizzabile
**solo ritardato**, e il `Rating` è un modello proprietario, non una misura.

**Novità sulla potenza**: con Serie A + Premier siamo a **759 partite**, che
supera le **~574** che la Fase 98 indica per l'80% di potenza sull'1X2 contro
il mercato. Il go/no-go di `docs/PIANO_DATABASE_GIOCATORI.md` §12.3 **diventa
conclusivo** invece che indicativo — è la soglia che una lega sola non
raggiungeva.
