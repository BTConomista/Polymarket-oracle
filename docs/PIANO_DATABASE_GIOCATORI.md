# Piano (bozza) — database giocatore per giocatore, arbitri e allenatori

> **Cos'è questo documento e cosa NON è.** È una bozza di ragionamento, aperta
> il **29/07/2026** su richiesta esplicita dell'utente ("prossimo passo:
> database giocatore per giocatore... per ora iniziamo solo a creare la
> struttura") ed **estesa lo stesso giorno** — sempre su richiesta dell'utente
> — a due fronti collegati: un database per gli **arbitri** e uno per gli
> **allenatori** (club e nazionali, incluse le competizioni europee per i
> club), più un **controllo finale di qualità** su Wikipedia per tutti i
> fronti (§6-bis) e un elenco di **arricchimenti aggiuntivi** (§1.8: età ed
> esperienza dei giocatori, esperienza globale di allenatori e arbitri,
> attendance, contesto andata/ritorno, rigori...) individuati continuando a
> ragionarci sopra. Non è una fase del diario (nessun esperimento è stato ancora
> eseguito: la regola `CLAUDE.md` §2 riserva il diario a decisioni/scoperte da
> un run, questo è un piano), non è un impegno di raccolta, e **non autorizza
> da sola** né lo scaricamento di nuovi dati né la scrittura di codice di
> importazione: quello resta un passo successivo, da concordare esplicitamente
> con l'utente (vedi §6). Vive come pista aperta in
> [`PISTE.md`](PISTE.md) (pista 21) e come voce di brainstorming in
> [`lavoro_aperto.md`](../lavoro_aperto.md) §7.
>
> **Nota metodologica sulla verifica.** A differenza della prima stesura (che
> per il Tier A si basava sui nomi di file già annotati nelle piste 10/11,
> mai aperti), le sezioni su arbitri e allenatori sono state scritte **dopo
> aver scaricato per davvero** il dataset `davidcariboo/player-scores` da
> Kaggle in questa sessione (`kagglehub`, licenza CC0) e **ispezionato lo
> schema reale** dei file — non a memoria. I numeri di copertura di questo
> documento (§1.5/§1.6) sono quindi **verificati oggi**, non stimati. Il
> download era solo di controllo: i file NON sono stati committati nel repo
> (708 MB, cache locale ripulita a fine verifica).

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
costruire infrastrutture costose. Divido i dati desiderati per livello di
costo — dal più economico (§1.1, §1.5, §1.6) al più difficile (§1.2, §1.3).

### 1.1 · Tier A — quasi gratis: stesso fornitore già in casa

Il dataset che già usiamo per i valori di rosa (`src/data/player_scores.py`,
Fase 67 — `dcaribou/transfermarkt-datasets` via Kaggle, licenza **CC0**,
aggiornato settimanalmente a monte) **contiene già** i file che servono per
gran parte di questa richiesta. Verificato **oggi** scaricando il dataset per
intero (nota metodologica in testa al documento) — schema reale, non quello
supposto dalle piste 10/11:

| file upstream | dimensione | cosa dà DAVVERO (schema verificato) | stato import |
|---|--:|---|---|
| `appearances.csv` | 143 MB | **già scaricato** in `files/player_scores/appearances.csv.gz` (Fase 67) — colonne: `game_id, player_id, player_club_id, competition_id, yellow_cards, red_cards, goals, assists, minutes_played`. Minuti/gol/assist/cartellini per (giocatore, partita) **ci sono già sul disco**, solo mai uniti in una tabella partita-per-partita | ✅ scaricato, da parsare |
| `games.csv` | 24 MB | `game_id, competition_id, season, date, home_club_id, away_club_id, home/away_club_goals, home/away_club_manager_name, referee, stadium, attendance, home/away_club_formation, competition_type` — **la tabella-cardine**: dà arbitro E allenatore per partita (vedi §1.5/§1.6), e copre anche Champions/Europa/Conference League | ⬜ non importato |
| `club_games.csv` | 11 MB | stessa informazione di `games.csv` ma **una riga per (club, partita)**: `own_manager_name, opponent_manager_name, own/opponent_goals, is_win` — comoda per costruire il pannello per-allenatore senza pivot | ⬜ non importato |
| `game_lineups.csv` | 337 MB | **NON ha il minuto di entrata/uscita** (correzione rispetto alla prima stesura): solo `type` (`starting_lineup`/`substitutes`), `position`, `number`, `team_captain`. Aggiunge titolare/panchina/ruolo/maglia, non i minuti — quelli sono già in `appearances.csv` | ⬜ non importato |
| `game_events.csv` | 150 MB | eventi **con il minuto**: `type` ∈ {Substitutions (631k), Cards (382k), Goals (248k), Shootout}, con `player_id`/`player_in_id`/`player_assist_id` — qui vive il minuto esatto di ogni cambio, gol, assist, cartellino | ⬜ non importato |
| `transfers.csv` (pista 11) | — | data di arrivo/partenza di ogni giocatore da ogni club | ⬜ non importato |
| `players.csv` | — | anagrafica: ruolo, piede, data di nascita, nazionalità | ✅ già scaricato |

**Il portiere è già coperto da qui, senza fonte aggiuntiva**: `game_lineups.csv`
dice chi era in porta partita per partita: bastano lineup + risultato per
avere "gol subiti per portiere" (e, incrociando gli xG di Understat già in
snapshot, anche una stima di shot-stopping).

**Conseguenza pratica per l'ordine dei passi (§6)**: `games.csv` e
`club_games.csv` insieme pesano **35 MB** (contro i 487 MB di
lineups+events) e sbloccano arbitri, allenatori **e** l'estensione alle
coppe europee in un colpo solo — vengono prima, non dopo, nell'ordine di
costo/valore.

**Copertura verificata oggi** (non stimata): su `games.csv`, per le 5 leghe +
Champions/Europa/Conference League (incluse le qualificazioni) nel periodo
2017-2025, `referee` e `home/away_club_manager_name` mancano in **meno dello
0,3%** delle partite in ogni singola competizione (il dettaglio per
competizione è in §1.5). Non ancora verificato: la stessa completezza per
`appearances.csv`/`game_lineups.csv`/`game_events.csv` sulle nostre 5
leghe/9 stagioni — è il primo controllo del tracer bullet (§6).

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

### 1.5 · Arbitri — quasi tutto già misurato altrove, qui è la parte STRUTTURALE

**Non è un fronte nuovo**: l'utente aveva già chiesto di tenere conto degli
arbitri (28/07/2026), e da quella richiesta il progetto ha già prodotto
lavoro reale, misurato — **da riusare, non da rifare**:

- `data/stagione_2026_2027/README.md` §4-bis — l'arbitro vale **quanto il
  fattore campo** nel prevedere i cartellini (+0.00368 contro +0.00371, IC
  entrambi conclusivi, Fase 125), la sua tendenza **persiste** fra stagioni
  (corr +0.352, IC95% [+0.299, +0.405]), ed è **ortogonale ai gol** (Fase 96,
  |corr| ≤ 0.06 — non è la forza-squadra vista da un'altra angolazione);
- `scripts/_run_fase125_cartellini.py` — il backtest che l'ha misurato, e la
  fonte che ha già usato è **esattamente `games.csv`** di
  `davidcariboo/player-scores` (colonna `referee`, non football-data: le 5
  leghe non hanno l'arbitro nei CSV grezzi già in repo, verificato oggi —
  `data/football_data_raw/*.csv` non ha una colonna `Referee`);
- `scripts/raccolta_giornaliera.py` scrive già un record `arbitro_designato`
  (stato `da_implementare`) per la raccolta **prospettica** (designazione
  ~2 giorni prima, irrecuperabile a posteriori).

**Quello che manca, e che è lo scopo di QUESTO piano**: quei numeri vengono
da uno script `_run_*` una tantum (Fase 125), non da una tabella
**strutturale** versionata che backtest/predict possano leggere come
`understat.py`/`transfermarkt.py`. Verificato oggi (§1.1): `games.csv`
copre `referee` su **IT1/GB1/ES1/L1/FR1 2017-2025 con lo 0,0-0,1% di celle
mancanti**, e — punto nuovo rispetto alla Fase 125, che guardava solo le 5
leghe — **anche su CL/EL/UCOL (Conference) e le rispettive qualificazioni**,
sempre 2017-2025, sempre sotto lo 0,3% di mancanti. La tabella
`referee_matches.csv` proposta (§2) non aggiunge dato: **impacchetta in una
fonte unica e versionata** ciò che oggi vive in uno script sperimentale, e lo
estende gratis alle coppe europee.

**Il confine resta quello già scritto nella Fase 125**: vale sul mercato
**cartellini**; sull'1X2 l'arbitro non è mai stato dimostrato utile, e sul
**totale** di partita forma e correlazione non sono separatamente
identificabili (Fase 126) — non promettere di più di quanto già misurato.

**Cosa resta davvero aperto** (non coperto da `games.csv`): VAR/assistenti,
cambi dell'ultimo minuto, e soprattutto la raccolta **prospettica** — tutto
già pianificato in `data/stagione_2026_2027/README.md` §4-bis, che questo
documento NON duplica.

### 1.6 · Allenatori — fronte nuovo, ipotesi dell'utente, testabile da subito

**L'idea dell'utente**: uno stesso allenatore tende a produrre lo stesso
*stile* di squadra (possesso, tiri, dribbling tentati/riusciti, occasioni da
gol create, xG, gol fatti/subiti…) **anche cambiando squadra** — sia per i
club sia per le nazionali —, e per i club l'analisi andrebbe estesa anche
alle **competizioni europee**.

**Perché è testabile meglio del semplice "l'allenatore conta"**: l'utente
descrive esattamente il disegno che rende il test convincente, ed è più
forte di quello già fatto per l'arbitro (Fase 125 confronta lo *stesso*
arbitro fra due stagioni: qui si può confrontare lo *stesso* allenatore su
**due squadre diverse**, isolando il suo contributo da quello della rosa
molto più direttamente — un test quasi "a effetti fissi").

**Il dato-cardine esiste già ed è quasi completo**: `games.csv`/
`club_games.csv` (§1.1, verificati oggi) hanno `home/away_club_manager_name`
(o `own_manager_name`/`opponent_manager_name` nella vista per-club), **con
meno dello 0,3% di celle mancanti** sulle 5 leghe + CL/EL/UCOL 2017-2025 —
identico alla copertura dell'arbitro, stessa tabella, stesso costo. Da questo
si costruisce senza fonti aggiuntive:

1. una tabella `manager_spells.csv` (club, allenatore, data inizio, data
   fine mandato) per **derivazione** — prima/ultima partita con quel nome in
   quella colonna, non un dato raccolto a parte;
2. un JOIN di quegli intervalli sugli snapshot **già molto più ricchi** che
   il progetto ha per le 5 leghe (xG/npxG/PPDA/deep di Understat, corner e
   cartellini Tier 3, quote di mercato) — molto più stile-di-gioco di quanto
   `games.csv` da solo contenga (che ha solo il risultato secco e la
   formazione, non xG/possesso/tiri).

**Il confine onesto, dichiarato subito**: per le partite di club in
**Champions/Europa/Conference League**, `games.csv` dà allenatore, arbitro,
risultato e modulo — ma **non** possesso/tiri/xG: Understat copre solo le 5
leghe domestiche (nessuna verifica che copra le coppe europee, e nessuna
fonte alternativa nota oggi per lo stile di gioco nelle coppe). Quindi
l'estensione europea è **immediata e gratis per "chi ha allenato, con che
risultato"**, ma resta **aperta** (nuovo Tier B, da cercare) per le
statistiche di stile nelle stesse partite.

**Nazionali — più debole del previsto, verificato oggi**: `national_teams.csv`
ha un campo `coach_name`, ma è **solo l'attuale**, non uno storico
per-partita — non basta per un pannello. E `games.csv` copre le nazionali
**solo nei tornei finali** (Europei, Mondiali, Copa América, Coppa
d'Africa, Coppa d'Asia — es. `EURO`: 215 partite su 5 edizioni 2007-2023;
`FIWC`: 392 partite su 6 edizioni 2005-2025), **non** le qualificazioni, le
amichevoli o la UEFA Nations League che occupano la maggior parte delle
finestre FIFA durante una stagione normale di club — la stessa lacuna già
scritta per i giocatori (§1.3): il fronte-nazionali resta debole, qui un
po' meno (i tornei finali un dato lo danno) ma non risolve il caso d'uso
principale (la fatica da doppio impegno durante la stagione).

**Rischio di matching aggiuntivo**: `manager_name` è una stringa libera
(Transfermarkt), stesso problema di matching già noto per i giocatori — va
normalizzato e il tasso di aggancio dichiarato, non assunto.

### 1.7 · Riepilogo per le richieste dell'utente (giocatori + arbitri + allenatori)

| richiesta | tier | dato |
|---|---|---|
| minuti giocati a partita, subentrati/sostituti | A | `appearances.csv` (**già scaricato**) per i minuti; `game_events.csv` per il minuto esatto del cambio |
| gol e assist per giocatore | A | `appearances.csv` (**già scaricato**) |
| tocchi, passaggi, dribbling, interventi | B | nessuna fonte pulita nota oggi; StatsBomb/API-Football da controllare |
| stanchezza da minuti consecutivi + nazionale | A (club) + fronte nuovo (nazionale) | minuti-club da Tier A; minuti-nazionale **senza fonte** oggi |
| vantaggio/svantaggio da tocchi in un certo tipo di partita | B | dipende dal Tier B |
| gol subiti per portiere | **nessuna fonte nuova**: derivabile da Tier A + snapshot esistenti | — |
| **arbitro per partita** | A | `games.csv` (24 MB, ⬜ da importare) — struttura ciò che la Fase 125 ha già misurato |
| **allenatore per partita, club** | A | `games.csv`/`club_games.csv` — stile di gioco dal join con gli snapshot già ricchi (5 leghe) |
| **allenatore, competizioni europee** | A (chi/risultato) + B (stile) | risultato/allenatore/arbitro gratis da `games.csv`; possesso/tiri/xG senza fonte nota |
| **allenatore, nazionali** | 🟠 parziale | solo tornei finali in `games.csv`; qualificazioni/amichevoli/Nations League senza fonte, come per i giocatori |

### 1.8 · Arricchimenti aggiuntivi (brainstorming del 29/07/2026 — "quasi tutto già nei file noti")

Continuando a ragionarci sopra dopo la prima stesura: nessuna di queste voci
richiede una fonte nuova — sono tutte derivabili dagli stessi file già
identificati in §1.1 (`games.csv`, `club_games.csv`, `appearances.csv`,
`players.csv`, `game_events.csv`), a costo marginale ~zero rispetto
all'importazione già proposta.

**Partita** (da `games.csv`, colonne già viste in §1.1 ma non ancora usate):

- **`attendance`** (spettatori) — proxy diretta della forza del
  fattore-campo **partita per partita**, invece di un flag binario. Si lega
  al regime "porte chiuse" 2020-22 già noto nel progetto (Fase 51/52): con
  l'attendance vera si può misurare il vantaggio-casa in funzione del
  pubblico invece di trattare quell'era come un blocco unico;
- **`aggregate` + `round`** — risultato aggregato e turno della
  competizione: per le coppe europee dà il contesto andata/ritorno; per i
  gironi già decisi, identifica le partite dove un allenatore fa turnover
  perché la qualificazione è già acquisita ("dead rubber") — si lega alla
  rotazione già in `data/stagione_2026_2027/README.md`;
- **`home/away_club_formation`** — modulo schierato: un confronto di moduli
  (es. difesa a 3 contro difesa a 4) è gratis e mai sfruttato finora nel
  piano.

**Giocatore** (da `players.csv`/`appearances.csv`/`game_events.csv`):

- **età esatta a partita** — derivata da data di nascita + data partita, mai
  usata finora: utile per isolare l'effetto "squadra giovane/vecchia"
  dall'effetto valore-rosa;
- **esperienza del giocatore** (idea dell'utente) — presenze e/o minuti
  cumulati **fino a quella partita, o a inizio stagione**, non solo l'età
  anagrafica. Poiché `appearances.csv`/`games.csv` NON sono filtrati alle
  nostre 5 leghe (coprono ~89.000 partite globali, decine di competizioni —
  Brasile, Argentina, MLS, Arabia Saudita, Giappone, Corea, le principali
  leghe europee, verificato scaricando il dataset in questa sessione),
  l'esperienza si può contare **anche da prima che il giocatore entrasse in
  una delle nostre 5 leghe** (es. un giovane arrivato dal Brasile, o un
  giocatore con anni di carriera in un altro campionato) — stesso file di
  `player_match_appearances.csv`, nessuna fonte in più;
- **altezza** — se presente in `players.csv` (schema non ancora ispezionato
  riga per riga per questo campo): rilevante per calci piazzati/duelli
  aerei, asse mai toccato dal progetto;
- **rigori** — `game_events.csv` ha probabilmente il dettaglio nel campo
  `description` (non ancora ispezionato oltre al conteggio dei `type`): chi
  li calcia, chi li para. Primo passo verso uno shot-stopping da rigore per
  portiere, più specifico del PSxG−GA già in
  `data/stagione_2026_2027/README.md`.

**Allenatori**:

- **esperienza globale** — partite dirette in carriera anche fuori dalle
  nostre 5 leghe/coppe europee (stesso ragionamento del giocatore): un
  allenatore straniero esperto non va trattato come un debuttante solo
  perché è nuovo nelle nostre leghe;
- **effetto "nuovo allenatore"** — le prime N partite dopo un cambio in
  panchina hanno spesso un rimbalzo di risultati indipendente dallo stile:
  derivabile subito da `manager_spells.csv`, distinto dalla "firma
  stilistica" (idea c-bis, §4).

**Arbitri**:

- **esperienza globale** — stesso ragionamento, partite arbitrate in
  carriera anche fuori dalle nostre competizioni;
- **bias casa/trasferta per singolo arbitro** — scomporre "quanto ammonisce"
  (Fase 125) per squadra-in-casa vs squadra-in-trasferta, per capire se un
  arbitro è sistematicamente più severo con gli ospiti.

**Nota di onestà**: due voci sopra NON sono ancora verificate riga per riga
(altezza in `players.csv`, dettaglio rigori nel campo `description` di
`game_events.csv`) — vanno controllate nel tracer bullet (§6), non assunte
presenti solo perché sarebbe comodo che lo fossero.

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
    nazionalita, altezza (se presente in players.csv, da verificare)

player_match_appearances.csv        # Tier A — una riga per (player_id, partita)
    season, home_team, away_team, player_id, team, titolare (bool),
    minuto_in, minuto_out, minuti_giocati, ruolo_in_campo,
    gol, assist, ammonizioni, espulsione (bool),
    eta_esatta                      # derivata: data_nascita vs data partita
    presenze_carriera_a_oggi        # derivata: conteggio su TUTTO appearances.csv,
    minuti_carriera_a_oggi          #   non filtrato alle 5 leghe (§1.8)

player_match_advanced.csv           # Tier B — SOLO se/quando una fonte esiste
    season, home_team, away_team, player_id, tocchi, passaggi_tentati,
    passaggi_riusciti, dribbling_tentati, dribbling_riusciti,
    contrasti, tiri, tiri_in_porta, duelli_aerei_vinti

player_national_duty.csv            # fronte nazionali — SOLO se/quando una
    player_id, data, competizione, minuti_giocati   # fonte esiste

referee_matches.csv                 # Tier A — una riga per partita (5 leghe + coppe UEFA)
    season, competition, date, home_team, away_team, referee,
    attendance, aggregate, round, home_formation, away_formation,  # §1.8: gia' in
                                                                    #   games.csv, stessa riga
    esperienza_arbitro_a_oggi       # derivata: partite arbitrate PRIMA di questa,
                                     #   su TUTTO games.csv (§1.8)

manager_spells.csv                  # Tier A — mandati per club/nazionale, DERIVATI
    club_or_national_team, manager_name, data_inizio, data_fine,
    fonte_derivazione ("prima/ultima partita in games.csv"),
    esperienza_globale_a_inizio_mandato   # derivata: partite dirette PRIMA
                                            #   dell'inizio mandato (§1.8)

manager_match_style.csv             # JOIN di manager_spells su snapshot esistenti
    season, competition, home_team, away_team, home_manager, away_manager,
    <tutte le colonne di stile già in snapshot: xg, npxg, ppda, deep, ...>

referee_home_away_bias.csv          # derivata/aggregata (§1.8, NON una riga per
    referee, n_partite,             #   partita): scomposizione casa/trasferta di
    cartellini_medi_casa,           #   "quanto ammonisce" (Fase 125), utile per
    cartellini_medi_trasferta       #   capire se un arbitro e' sbilanciato
```

`presenze_carriera_a_oggi`/`minuti_carriera_a_oggi`/`esperienza_arbitro_a_oggi`/
`esperienza_globale_a_inizio_mandato` sono tutte contate su `appearances.csv`/
`games.csv` **per intero** (non filtrati alle 5 leghe): è il vantaggio pratico
di partire da un dataset globale invece che da 5 snapshot isolati — l'unico
posto dove questo piano propone di guardare fuori dalle 5 leghe senza che sia
una fonte nuova da cercare.

Un file per lega o un unico file con `season`+`league` in chiave: da decidere
quando si scrive il primo importer reale, seguendo lo stesso pattern già
usato per gli snapshot di club (`data/{lega}_matches.csv`).
`manager_match_style.csv` non è un file raccolto ma **derivato** (join): non
serve versionarlo separatamente se si può ricalcolare da
`manager_spells.csv` + gli snapshot, stesso principio di riproducibilità
(`CLAUDE.md` §1.5).

**Chiave allenatore/arbitro**: stesso principio della chiave giocatore —
`manager_name`/`referee` sono stringhe libere di Transfermarkt, vanno
normalizzate (probabilmente con lo stesso approccio nome-normalizzato +
disambiguazione già usato in `transfermarkt.py`) e il tasso di aggancio
dichiarato, non assunto al 100%.

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

1. **un fronte "arbitri + allenatori"**: estendere l'import esistente
   (`import_dataset.yml`) a `games.csv`/`club_games.csv` (35 MB, già
   verificati oggi) — è il fronte più economico e più pronto di tutti, e
   sblocca da solo tre delle richieste dell'utente (arbitro, allenatore
   club, estensione europea di "chi ha allenato/arbitrato/vinto");
2. **un fronte "Tier A giocatori"**: parsare `appearances.csv` (già
   scaricato) in `player_match_appearances.csv`, poi valutare se estendere a
   `game_lineups.csv`/`game_events.csv` per titolare/panchina e minuto esatto
   dei cambi;
3. **un fronte "Tier B"**: verificare StatsBomb open data e API-Football
   (copertura reale, licenza, robots.txt) prima di scrivere qualunque parser
   — vale sia per i giocatori (tocchi/passaggi) sia per lo stile di gioco
   nelle coppe europee (§1.6);
4. **un fronte "nazionali"**: cercare una fonte da zero per le finestre FIFA
   regolari (qualificazioni, amichevoli, Nations League — §1.3/§1.6) — oggi
   è ricerca, non raccolta, per giocatori E allenatori.

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

c-bis. **Firma stilistica dell'allenatore, testata col disegno che l'utente
   ha proposto**: misurare lo stile di una squadra (possesso, tiri, xG,
   dribbling…) sotto un allenatore, e verificare se **la stessa firma
   ricompare quando lo stesso allenatore cambia squadra** — un test più
   diretto della semplice persistenza-nel-tempo già usata per l'arbitro
   (Fase 125), perché confronta due squadre diverse invece di due stagioni
   della stessa. Da disegnare come backtest walk-forward con lo stesso
   rigore (shrinkage sulle poche partite, IC, controllo-di-solo-livello per
   non confondere "stile del nuovo allenatore" con "la squadra che eredita è
   diversa" — stesso principio delle Fasi 96-99 sul controllo di livello).

c-ter. **Arbitro**: nessuna nuova idea d'uso qui — è già misurato e in uso
   (Fase 125/126, §1.5). L'unico passo aperto è **strutturale**
   (`referee_matches.csv`), non di modellazione.

d. **Mercati "player prop"** (marcatore, ammonito, ecc.): oggi il listino
   Tier 1-3 del progetto non li contempla — sarebbe una famiglia di mercati
   completamente nuova. Nota di onestà, coerente col principio §1.8: per
   questi mercati **non raccogliamo quote** (a differenza di 1X2/O/U), quindi
   non potremmo nemmeno misurare se un prezzo li batte o li pareggia — solo
   stimarli in assoluto, come già capitato per il GG/NG prima che le quote
   1xBet fossero trovate (`PISTE.md` pista 16).

e. **Attendance come proxy continua del vantaggio-casa** (§1.8): oggi il
   regime "porte chiuse" 2020-22 è trattato come un blocco (Fase 51/52) —
   con l'`attendance` vera si potrebbe stimare il vantaggio-casa in funzione
   del pubblico presente, dentro e fuori quell'era, invece che con un flag
   binario.

f. **Esperienza (giocatore/allenatore/arbitro) come covariata**, non solo
   età anagrafica (§1.8, idea dell'utente): presenze/minuti/partite dirette
   cumulate fino a quella data — compresa l'esperienza maturata FUORI dalle
   nostre 5 leghe, dato che `appearances.csv`/`games.csv` sono globali. Da
   testare separatamente dall'età (un ventenne con 100 presenze in Brasile
   non è un debuttante) e con lo stesso controllo-di-solo-livello delle Fasi
   96-99, perché "più esperienza" correla anche con "squadra più forte".

g. **Effetto "nuovo allenatore" e bias casa/trasferta dell'arbitro** (§1.8):
   due ipotesi puntuali, entrambe derivabili senza fonti nuove da
   `manager_spells.csv`/`referee_home_away_bias.csv` — il primo è un
   rimbalzo di breve periodo indipendente dalla firma stilistica (idea
   c-bis), il secondo scompone il fattore-arbitro già misurato (Fase 125)
   per capire se è sbilanciato verso casa o trasferta.

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
- **Volume**: `game_lineups.csv` (337 MB) e `game_events.csv` (150 MB) pesano
  molto più di `games.csv`/`club_games.csv` (35 MB insieme) — un motivo in
  più per farli DOPO, non prima (§6).
- **Coppe europee, solo mezza vittoria**: chi ha allenato/arbitrato/vinto è
  quasi gratis (§1.5/§1.6); possesso/tiri/xG per le stesse partite **non
  hanno una fonte nota oggi** — Understat copre solo le 5 leghe domestiche,
  non verificato se esista un equivalente per Champions/Europa/Conference.
  Non dare per scontato che l'estensione europea sia completa solo perché
  la parte "chi" lo è.
- **`manager_name`/`referee` sono stringhe libere**: stesso rischio di
  matching già noto per i giocatori (`transfermarkt.py`), e va misurato per
  ogni competizione — la copertura verificata oggi (§1.5/§1.6) è sulla
  COMPLETEZZA della colonna in `games.csv`, non sulla qualità del matching
  contro altre fonti (che qui non serve, essendo un dato auto-contenuto).

## 6 · Primi passi concreti proposti (nessuno ancora eseguito)

Tutti reversibili, in ordine di costo crescente, **ciascuno subordinato a un
via libera esplicito dell'utente** prima di scrivere codice o importare dati:

0. Aggiungere `games.csv` e `club_games.csv` alla lista `WANTED` del
   workflow `import_dataset.yml` (35 MB insieme, stessa fonte già fidata CC0)
   — il passo col miglior rapporto valore/costo: sblocca arbitri, allenatori
   club e l'estensione europea in un colpo solo. Aggiungere anche
   `game_lineups.csv`/`game_events.csv` alla stessa lista è a costo
   marginale di codice quasi nullo (stesso workflow), ma pesano 20× di più
   (487 MB) — separarli non è obbligatorio, ma va dichiarato l'impatto
   prima di farlo.
1. **Tracer bullet arbitri/allenatori**: UNA lega-stagione → costruire
   `referee_matches.csv` e `manager_spells.csv` grezzi da `games.csv`/
   `club_games.csv`, e validare `manager_spells` contro fonte indipendente
   (es. Wikipedia "manager history" del club, già usata con successo per
   altre cose in questo progetto, Fase 100) prima di fidarsi del solo
   dato derivato.
2. **Tracer bullet giocatori**: parsare `appearances.csv` (già scaricato)
   in `player_match_appearances.csv` per UNA lega-stagione, e validarlo
   contro `understat.season_players` (i minuti totali per
   giocatore-stagione devono tornare, entro una tolleranza da definire) e
   contro il conteggio cartellini già usato da `disciplina.py`.
3. **Solo dopo la validazione di 1 e 2**: estendere alle altre 4 leghe × 9
   stagioni, e valutare se importare anche `game_lineups.csv`/
   `game_events.csv` per titolare/panchina e minuto esatto dei cambi.
4. **Fronte nazionali** (indipendente, nessuna fonte nota per le finestre
   FIFA regolari): ricerca da zero, non raccolta — vale sia per i
   giocatori sia per gli allenatori.
5. **Fronte Tier B** (indipendente): verificare copertura reale di StatsBomb
   open data e limiti del free tier di API-Football, sia per i dati
   giocatore (tocchi/passaggi) sia per lo stile di gioco nelle coppe
   europee (§1.6), prima di decidere se vale la pena scriverci sopra un
   importer.
6. **Controllo finale, DOPO ogni importazione**: verifica indipendente su
   Wikipedia dei dati raccolti (arbitri, allenatori, e dove possibile i
   conteggi giocatore) — dettaglio del disegno in §6-bis. Nessuna tabella
   derivata da `games.csv`/`appearances.csv` si considera pronta per il
   modeling prima di questo passo.

**Nota sugli arricchimenti di §1.8**: non sono un passo a parte — età,
esperienza (giocatore/allenatore/arbitro), attendance, aggregate/round,
formazione e rigori si ottengono dagli stessi file già previsti nei passi
0-2 (nessuna riga in più nel `WANTED` del workflow). Vanno solo incluse nel
parser quando si scrivono `player_match_appearances.csv`/
`referee_matches.csv`/`manager_spells.csv` — un dettaglio di
implementazione, non un fronte nuovo con la sua priorità.

## 6-bis · Controllo finale: verifica indipendente su Wikipedia (richiesta utente, 29/07/2026)

**Perché**: `games.csv`/`appearances.csv` sono un'unica fonte (Transfermarkt
via Kaggle) — anche se la copertura interna è quasi completa (§1.1/§1.5/§1.6),
un dato sbagliato A MONTE non si vede confrontando la stessa fonte con se
stessa. Serve un'informazione **indipendente**: è la regola R5 del
`CLAUDE.md` ("diagnosticare con informazione indipendente... un'altra
fonte"), già seguita con successo in questo progetto — i calendari di coppa
(Fase 100, Wikipedia) e le rose 2026-27 dove il dataset non arriva
(`data/stagione_2026_2027/README.md` §3-ter, "Wikipedia come fonte della
rosa"). Qui si applica lo stesso schema a arbitri, allenatori e giocatori.

**Cosa verificare, fronte per fronte, e con quale pagina Wikipedia**:

| tabella | pagina Wikipedia candidata | affidabilità attesa |
|---|---|---|
| `manager_spells.csv` (allenatori) | "Managerial history of \<club\>" / tabelle "List of \<club\> F.C. managers" — quasi tutti i club delle 5 leghe ne hanno una, con date di inizio/fine mandato | **alta**: è un formato standard e sistematico su Wikipedia, il più adatto dei tre a questo controllo |
| `referee_matches.csv` (arbitri) | pagine di stagione delle leghe principali (es. "20XX–XX Serie A season") includono a volte tabelle/tabellini con l'arbitro, più spesso per big-match e finali di coppa che per il turno generico | **non uniforme, da misurare**: nessuna verifica preliminare in questo progetto su quanto sia sistematica — potrebbe risultare parziale |
| `player_match_appearances.csv` (aggregati stagionali) | tabelle "Career statistics" nelle pagine giocatore (presenze/gol/assist per stagione e competizione) | **media-alta** per i giocatori di rilievo, più debole per le rotazioni minori |

**Metodo proposto** (coerente con la disciplina statistica già richiesta dal
progetto, regola R7 del `CLAUDE.md`: ogni controllo ha la sua misura, non un
"sembra giusto"):

1. **campione, non censimento**: un numero dichiarato in anticipo di casi
   per fronte e per lega (es. 30-50) — validare l'intero dataset contro
   Wikipedia sarebbe uno scraping sproporzionato allo scopo (un controllo
   qualità, non una fonte primaria) e andrebbe comunque a carico del
   `robots.txt`/rate-limit di Wikipedia, che va rispettato anche per un
   uso "consentito" (regola R5.3);
2. **tasso di concordanza pubblicato**, non assunto: quante voci del
   campione coincidono, quante divergono, quante Wikipedia non le copre
   affatto (un "non trovato" non è un errore, va contato a parte);
3. **soglia di allarme dichiarata prima di guardare i numeri**: se il
   mismatch (sulle voci che Wikipedia COPRE, non sul totale) supera una
   soglia da fissare (indicativamente 5%, coerente con le tolleranze già
   usate altrove nel progetto per il matching nome↔fonte), ci si ferma e si
   applica la procedura R5-§5-bis (spiegare prima di accusare, cercare il
   dato vero con un'ulteriore fonte indipendente, mai correggere a mano —
   regola R3) prima di usare quella tabella per modellare;
4. **il controllo è un gate, non un'operazione singola**: se un fronte non
   supera la soglia, la tabella resta marcata "non verificata" (si registra
   comunque, principio §1.4 del `CLAUDE.md`: anche un controllo negativo si
   scrive) — non si butta il lavoro, si dichiara il limite.

**Limiti onesti, dichiarati subito**:

- **Wikipedia non sostituisce la fonte primaria**: è un controllo
  incrociato, non un dato migliore di Transfermarkt. Se le due fonti
  divergono, la procedura R5 decide qual è quella vera — non si sceglie a
  priori quale fidarsi;
- **copertura sconosciuta, non zero ma non garantita**: per gli arbitri in
  particolare, non c'è oggi nessuna misura di quanto sistematicamente
  Wikipedia riporti l'arbitro partita-per-partita nelle 5 leghe — potrebbe
  risultare che il campione utile è più piccolo del previsto, e va
  dichiarato se succede, non nascosto;
- **ordine**: questo controllo va fatto DOPO l'importazione (passi 0-3 di
  §6), non prima — prima si costruisce la tabella dai dati già in casa, poi
  si verifica con una fonte indipendente, esattamente come richiesto.

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
- `data/stagione_2026_2027/README.md` §4-bis — il lavoro già fatto e in corso
  sull'arbitro (Fase 125/126, raccolta prospettica): questo piano lo
  struttura, non lo duplica.
- `scripts/_run_fase125_cartellini.py` — il backtest che ha già usato
  `games.csv` (colonna `referee`) e ha misurato il guadagno sui cartellini.
- `scripts/raccolta_giornaliera.py` — dove vive già lo stub
  `arbitro_designato` per la raccolta prospettica del 2026-27.
