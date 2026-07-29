# Piano (bozza) — database giocatore per giocatore

> **Cos'è questo documento e cosa NON è.** È una bozza di ragionamento, aperta
> il **29/07/2026** su richiesta esplicita dell'utente ("prossimo passo:
> database giocatore per giocatore... per ora iniziamo solo a creare la
> struttura"). Non è una fase del diario (nessun esperimento è stato ancora
> eseguito: la regola `CLAUDE.md` §2 riserva il diario a decisioni/scoperte da
> un run, questo è un piano), non è un impegno di raccolta, e **non autorizza
> da sola** né lo scaricamento di nuovi dati né la scrittura di codice di
> importazione: quello resta un passo successivo, da concordare esplicitamente
> con l'utente (vedi §6). Vive come pista aperta in
> [`PISTE.md`](PISTE.md) (pista 21) e come voce di brainstorming in
> [`lavoro_aperto.md`](../lavoro_aperto.md) §7.

## 0 · Perché, e con quale grado di certezza

Oggi il motore stima la forza di una squadra **in blocco** (i λ,μ del
Dixon-Coles, o quelli impliciti nel mercato — principio §1.8/§1.9 del
`CLAUDE.md`): non sa *chi* ha giocato, solo *quanto ha segnato/subito la
squadra*. L'ipotesi dell'utente — un giocatore pesa più o meno di un altro, la
stanchezza (anche da nazionale) conta, un portiere non è intercambiabile con
un altro — è ragionevole e **non è mai stata testata con dati veri** in
questo progetto:

- la Fase 98 (pista 10 di `PISTE.md`) ha bocciato un **surrogato** storico
  della formazione schierata (undici ricostruito dai minuti stagionali, non
  dalla formazione reale): quel risultato **non è un argomento contro
  l'informazione-giocatore in sé**, è un argomento contro la scorciatoia. Con
  le formazioni vere l'esperimento è diverso e va rifatto, non dato per
  scontato nella stessa direzione (lo dice esplicitamente la voce della
  pista 10);
- la Fase 92/93 ha misurato **dove** il gap col mercato si concentra: 88%
  discriminazione casa/ospite (non massa-pareggio), soprattutto nelle
  **partite equilibrate della seconda metà di stagione** (`PISTE.md` §0). Se
  l'informazione a livello di singolo giocatore aiuta, è lì che va cercata e
  misurata — non è garantito che aiuti, è un'ipotesi da provare (principio §3
  del `CLAUDE.md`: testare la versione economica prima di investire).

Questo piano quindi non promette un edge: propone **un fronte dati nuovo**,
da costruire un pezzo alla volta (principio §1: tracer bullet prima dei
moduli), e da valutare con lo stesso rigore (per-mercato, con IC, principio
§1.9) di ogni altra pista.

## 1 · Cosa vorremmo raccogliere, in ordine di costo

Principio §3 del `CLAUDE.md`: testare la versione economica prima di
costruire infrastrutture costose. Divido i dati desiderati in tre livelli, dal
più economico al più difficile.

### 1.1 · Tier A — quasi gratis: stesso fornitore già in casa, mai importato

Il dataset che già usiamo per i valori di rosa (`src/data/player_scores.py`,
Fase 67 — `dcaribou/transfermarkt-datasets` via Kaggle, licenza **CC0**,
aggiornato settimanalmente a monte) **contiene già** i file che servono per
gran parte di questa richiesta. Oggi il workflow
`.github/workflows/import_dataset.yml` ne scarica solo 4 (quelli dei valori);
**mai importati** finora (già annotato come pista 10/11 di `PISTE.md`,
prima di questo piano):

| file upstream | cosa dà | risponde a |
|---|---|---|
| `game_lineups.csv` (~349 MB) | formazione titolare, panchina, **minuto di ingresso/uscita** di ogni cambio, ruolo in campo | "quanti minuti gioca ogni partita", "informazioni su subentrati e sostituti" |
| `game_events.csv` | gol, assist, cartellini **con il minuto**, per giocatore e per partita | "numero di gol e assist di ogni giocatore" (i cartellini già in parte usati via `src/data/disciplina.py`, ma lì solo aggregati per il calcolo di diffide/squalifiche) |
| `transfers.csv` (pista 11) | data di arrivo/partenza di ogni giocatore da ogni club | quando un giocatore è nella rosa che gioca quella partita |
| `players.csv` (già parzialmente usato) | anagrafica: ruolo, piede, data di nascita, nazionalità | anagrafica di base |

**Il portiere è già coperto da qui, senza fonte aggiuntiva**: `game_lineups.csv`
dice chi era in porta partita per partita: bastano lineup + risultato per
avere "gol subiti per portiere" (e, incrociando gli xG di Understat già in
snapshot, anche una stima di shot-stopping).

**Non verificato ancora**: se `game_lineups.csv`/`game_events.csv` coprano
davvero le nostre 5 leghe × 9 stagioni con la stessa completezza dei file già
importati (i valori di rosa hanno margini di copertura dichiarati e sotto
soglia in alcune celle, `docs/DATI.md` §5) — è il primo controllo del tracer
bullet (§6).

### 1.2 · Tier B — dati "event/advanced": tocchi, passaggi, dribbling, interventi

Questo è ciò che manca per rispondere a "un giocatore che tocca tanti palloni
in un certo tipo di partita potrebbe essere avvantaggiato o svantaggiato" con
un dato vero (non un proxy). **Nessuna fonte pulita è nota oggi**, e la
maggior parte è già stata controllata in una sessione recente dedicata
proprio a questo (28/07/2026, verbale in
`cantiere_opta_flashscore/diario_da_integrare.md` — in attesa di entrare nel
diario come nuova fase, indicativamente la successiva libera dopo la 126,
probabile "127"; e in `PISTE.md` come pista 20, non ancora integrata in
questo file al momento in cui scrivo):

| fonte | cosa darebbe | perché è chiusa (o non ancora aperta) |
|---|---|---|
| Opta / Stats Perform | il gold standard dell'event data | nessun tier gratuito o self-serve: solo licenza enterprise. Chiusura **commerciale** |
| WhoScored.com | statistiche derivate da Opta | `robots.txt` permissivo, ma sono dati di terzi ridistribuiti senza licenza di riuso (regola R2 del `CLAUDE.md`) |
| SofaScore.com | tocchi, passaggi, dribbling, contrasti | **403** anche sul `robots.txt`: bloccato a monte |
| FBref.com (Sports Reference) | le stesse statistiche, per-partita, storicamente | **403** dal proxy (`docs/MANUALE_SOPRAVVIVENZA.md`) |
| diretta.it / Flashscore | dati live/match-centre | `robots.txt` non blocca, ma i dati arrivano da un endpoint interno protetto da anti-bot attivo (token + fingerprint TLS); l'ambiente non raggiunge un vero browser in HTTPS. **Vincolo tecnico**, non commerciale — e aggirarlo (spoofing del fingerprint) è stato esplicitamente rifiutato: è detection evasion, indipendentemente da dove finirebbe scritta la tecnica |
| Understat | tocchi/passaggi impliciti nello shot-log | ha **solo aggregato-stagione** per giocatore (minuti totali, non per-partita: vedi `parse_season_players` in `src/data/understat.py`), e dalla Fase 120 **non si può più scaricare** (`robots.txt` lo vieta, regola R5.3) — quello che abbiamo è congelato |
| **StatsBomb open data** (GitHub, gratuito) | eventi dettagliati veri, licenza aperta | **mai verificato in questo progetto** se copre le nostre 5 leghe/9 stagioni — è pubblicamente noto per coprire poche competizioni/stagioni selezionate, ma va controllato prima di scartarlo, non a memoria |
| API-Football | statistiche partita, alcune per giocatore | free tier stretto (già notato altrove per formazioni/infortuni, `newseason.md`); mai verificato per l'uso player-level qui |

**Onestà**: questa tabella non è stata riverificata riga per riga oggi per il
Tier B — è la fotografia della sessione del 28/07 più i due candidati non
ancora controllati (StatsBomb, API-Football). Prima di scriverci sopra
qualunque codice, i due candidati aperti vanno controllati con lo stesso
rigore (robots.txt, licenza, copertura reale) usato per gli altri.

### 1.3 · Nazionali — il fronte più scoperto di tutti

**Nessuna fonte è mai stata cercata in questo progetto** per calendario e
presenze delle nazionali (zero occorrenze, come già constatato per altre
piste mai aperte). Serve per calcolare l'affaticamento da doppio impegno
("un giocatore che gioca molti minuti di fila, tenendo conto anche della
nazionale, sarà più stanco"). Candidati **da verificare, nessuno testato**:

- **openfootball** (già usato per calendari di coppa, Fase 100/68): copre
  soprattutto competizioni per club; non è verificato se abbia anche
  risultati/formazioni delle nazionali con dettaglio per giocatore;
- **Wikipedia**: ha già funzionato come fonte per calendari di coppa (Fase
  100, 3.045 righe recuperate) — potrebbe avere le rose/i marcatori delle
  partite di nazionale, ma **non** tipicamente i minuti giocati per giocatore
  con la stessa granularità del club;
- **Transfermarkt**: le pagine-giocatore hanno spesso una sezione "presenze in
  nazionale" — ma il mirror GitHub che alimenta `src/data/transfermarkt.py`
  oggi copre solo valori/infortuni per club, **non verificato** se includa
  anche questo.

Questo fronte resta, dichiaratamente, allo stesso stadio della pista 13
(meteo) in `PISTE.md`: aperto, senza nemmeno un candidato verificato.

### 1.4 · Riepilogo per la richiesta originale dell'utente

| richiesta | tier | dato |
|---|---|---|
| minuti giocati a partita, subentrati/sostituti | A | `game_lineups.csv` (da importare) |
| gol e assist per giocatore | A | `game_events.csv` (da importare) |
| tocchi, passaggi, dribbling, interventi | B | nessuna fonte pulita nota oggi; StatsBomb/API-Football da controllare |
| stanchezza da minuti consecutivi + nazionale | A (club) + fronte nuovo (nazionale) | minuti-club da Tier A; minuti-nazionale **senza fonte** oggi |
| vantaggio/svantaggio da tocchi in un certo tipo di partita | B | dipende dal Tier B |
| gol subiti per portiere | **nessuna fonte nuova**: derivabile da Tier A + snapshot esistenti | — |

## 2 · Come strutturare i dati (bozza di schema)

Rispettando le convenzioni già consolidate (`CLAUDE.md` §5/§5-bis):
offline-first, snapshot versionati, **niente modifica a mano** (regola R3),
matching dichiarato e misurato (non imputato) dove serve unire fonti diverse.

**Chiave di partita**: riusare quella già in uso in tutto il progetto,
`(season, home_team, away_team)` con nomi canonicalizzati via
`sources.TEAM_ALIASES` — non inventare un `match_id` nuovo se non serve.

**Chiave giocatore**: qui nasce il problema già noto. `transfermarkt.py`
aggancia Understat ↔ Transfermarkt per **nome normalizzato**, con
disambiguazione per ruolo/valutazioni e un tasso di aggancio **misurato e
dichiarato** (mai imputato sotto una soglia di copertura). Ogni fonte nuova
per il database giocatori va agganciata con lo stesso metodo — e il tasso di
aggancio per (fonte, lega, stagione) va **pubblicato**, non assunto al 100%.

Tabelle proposte (nomi provvisori, tutte con licenza/fonte dichiarata in
testa come fa ogni modulo di `src/data/`):

```
players.csv
    player_id (interno, stabile), nome, data_nascita, ruolo, piede,
    nazionalita

player_match_appearances.csv        # Tier A — una riga per (player_id, partita)
    season, home_team, away_team, player_id, team, titolare (bool),
    minuto_in, minuto_out, minuti_giocati, ruolo_in_campo,
    gol, assist, ammonizioni, espulsione (bool)

player_match_advanced.csv           # Tier B — SOLO se/quando una fonte esiste
    season, home_team, away_team, player_id, tocchi, passaggi_tentati,
    passaggi_riusciti, dribbling_tentati, dribbling_riusciti,
    contrasti, tiri, tiri_in_porta, duelli_aerei_vinti

player_national_duty.csv            # fronte nazionali — SOLO se/quando una
    player_id, data, competizione, minuti_giocati   # fonte esiste
```

Un file per lega o un unico file con `season`+`league` in chiave: da decidere
quando si scrive il primo importer reale, seguendo lo stesso pattern già
usato per gli snapshot di club (`data/{lega}_matches.csv`).

## 3 · Come raccoglierli — la proposta di più agenti in parallelo

L'utente ha proposto di mettere agenti a lavorare in parallelo (uno per
stagione, uno sui club, uno sulle nazionali). L'idea è valida ma **solo dopo
un tracer bullet** (principio §1 del `CLAUDE.md`): mai scalare un parsing non
ancora validato su una sola lega-stagione.

Una volta validato il tracer, la divisione più naturale **non è per
stagione**, ma **per fonte/compito** — perché i vincoli sono molto diversi
fra Tier A, Tier B e nazionali, mentre le 9 stagioni di una fonte già
funzionante sono repliche a costo marginale quasi nullo (è il pattern già
visto con football-data/Understat: una volta scritto il parser, le altre
stagioni sono un ciclo, non un problema nuovo). Proposta di suddivisione
compatibile con l'idea originale dell'utente:

1. **un fronte "Tier A club"**: estendere l'import esistente
   (`import_dataset.yml`) a `game_lineups.csv`/`game_events.csv`, scrivere il
   parser, validarlo su una lega-stagione, poi ripeterlo sulle altre 44
   (5 leghe × 9 stagioni meno quella del tracer);
2. **un fronte "Tier B"**: verificare StatsBomb open data e API-Football
   (copertura reale, licenza, robots.txt) prima di scrivere qualunque parser;
3. **un fronte "nazionali"**: cercare una fonte da zero (§1.3) — oggi è
   ricerca, non raccolta.

Ogni fronte segue le regole già consolidate del progetto quando tocca una
fonte esterna: `robots.txt` rispettato (regola R5.3), licenza dichiarata
(regola R2), **nessun aggiramento di anti-bot o di blocchi tecnici** — è già
stato rifiutato una volta in questo stesso ambito (Flashscore, §1.2) e la
regola non cambia qui.

## 4 · Come potremmo usare questi dati (idee, NON decise)

⚠️ **Questa sezione è un elenco di ipotesi da discutere, non un piano di
implementazione.** Quale di queste idee provare, in che ordine, e con quale
modello, **lo deciderà l'utente in futuro** — qui si abbozza solo perché
esistano candidati pronti quando si arriverà a quel punto.

a. **Fatica cumulata** (club + nazionale): somma dei minuti giocati negli
   ultimi N giorni per i titolari attesi. Concettualmente vicina a
   `rest_full`/`midweek_europe`, già in `docs/PANCHINA.md` — ma quelle sono
   feature di **squadra**, questa sarebbe **individuale**. Da testare con lo
   stesso controllo-di-solo-livello che le Fasi 96-99 hanno reso obbligatorio,
   per non confondere una feature moltiplicativa con la deriva del modello
   base.

b. **Forza della formazione realmente schierata** (non stimata): il
   surrogato storico è bocciato (pista 10, Fase 98) — ma con dati VERI
   l'esperimento è diverso, e va rifatto senza dare per scontato lo stesso
   esito.

c. **Portiere**: shot-stopping individuale (gol subiti contro gol attesi
   concessi dalla difesa, usando l'xG già in snapshot) come possibile
   modificatore della forza difensiva quando cambia il portiere titolare.

d. **Mercati "player prop"** (marcatore, ammonito, ecc.): oggi il listino
   Tier 1-3 del progetto non li contempla — sarebbe una famiglia di mercati
   completamente nuova. Nota di onestà, coerente col principio §1.8: per
   questi mercati **non raccogliamo quote** (a differenza di 1X2/O/U), quindi
   non potremmo nemmeno misurare se un prezzo li batte o li pareggia — solo
   stimarli in assoluto, come già capitato per il GG/NG prima che le quote
   1xBet fossero trovate (`PISTE.md` pista 16).

Nessuna di queste idee è approvata all'implementazione. Il primo passo reale,
qualunque sia l'idea scelta poi, resta la qualità del dato Tier A (§6).

## 5 · Rischi e limiti dichiarati onestamente

- **Matching giocatore↔fonte**: lo stesso problema già noto in
  `transfermarkt.py` (nome normalizzato, disambiguazione, copertura
  misurata), moltiplicato per più fonti se si arriva al Tier B o alle
  nazionali.
- **Copertura non uniforme sulle 5 leghe/9 stagioni**: già successo con altri
  dati (Bundesliga/Ligue 1 spesso meno coperte su fronti diversi) — da
  misurare, non da assumere identica alla Serie A.
- **Il Tier B potrebbe restare chiuso a lungo**: nessuna fonte pulita nota
  oggi, e la sessione del 28/07 ne ha già chiuse quattro negativamente.
- **Nessuna garanzia di segnale sopra il mercato**: il gap misurato (Fase
  92/93) è "discriminazione casa/ospite nelle partite equilibrate", ma non è
  detto che l'informazione mancante sia proprio quella a livello di
  giocatore — è un'ipotesi, non una certezza (principio §6 del `CLAUDE.md`:
  onestà sui limiti).
- **Volume**: `game_lineups.csv` upstream pesa da solo ~349 MB (già annotato
  in pista 10) — va verificato l'impatto prima di importarlo per intero.

## 6 · Primi passi concreti proposti (nessuno ancora eseguito)

Tutti reversibili, in ordine di costo crescente, **ciascuno subordinato a un
via libera esplicito dell'utente** prima di scrivere codice o importare dati:

0. Aggiungere `game_lineups.csv` e `game_events.csv` alla lista `WANTED` del
   workflow `import_dataset.yml` — stessa fonte già fidata (CC0,
   `dcaribou/transfermarkt-datasets`), nessun nuovo rischio di licenza.
1. **Tracer bullet**: UNA lega-stagione (candidata naturale: Serie A
   2025-26, la più recente) → costruire `player_match_appearances.csv`
   grezzo e validarlo contro `understat.season_players` (i minuti totali per
   giocatore-stagione devono tornare, entro una tolleranza da definire) e
   contro il conteggio cartellini già usato da `disciplina.py`.
2. **Solo dopo la validazione**: estendere alle altre 4 leghe × 9 stagioni.
3. **Fronte nazionali** (indipendente, nessuna fonte nota): ricerca da zero,
   non raccolta.
4. **Fronte Tier B** (indipendente): verificare copertura reale di StatsBomb
   open data e limiti del free tier di API-Football prima di decidere se
   vale la pena scriverci sopra un importer.

## 7 · Collegamenti

- [`PISTE.md`](PISTE.md) — pista 21 (questo fronte) e piste 10/11 (che questo
  piano estende).
- [`lavoro_aperto.md`](../lavoro_aperto.md) §7 — voce di brainstorming.
- [`docs/DATI.md`](DATI.md) — catalogo dati, da aggiornare quando (e se) il
  primo file player-level entrerà negli snapshot.
- `src/data/player_scores.py`, `src/data/transfermarkt.py` — l'infrastruttura
  di matching giocatore↔fonte già esistente, da riusare.
- `cantiere_opta_flashscore/` — il verbale (da integrare) della sessione che
  ha chiuso quattro delle fonti Tier B.
