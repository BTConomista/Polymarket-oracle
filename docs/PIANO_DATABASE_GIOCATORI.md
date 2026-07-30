# Piano (bozza) — database giocatore per giocatore, arbitri e allenatori

> **Cos'è questo documento e cosa NON è.** È una bozza di ragionamento,
> costruita a più mani in una sola sessione (29/07/2026), che cresce ad ogni
> giro di brainstorming — non è una fase del diario (nessun esperimento è
> stato ancora eseguito: la regola `CLAUDE.md` §2 riserva il diario a
> decisioni/scoperte da un run, questo è un piano), non è un impegno di
> raccolta, e **non autorizza da sola** né lo scaricamento di nuovi dati né
> la scrittura di codice di importazione: quello resta un passo successivo,
> da concordare esplicitamente con l'utente (vedi §6).
>
> **Cronologia sintetica** (per non perdere il filo — il dettaglio vero sta
> nelle sezioni, non qui): aperto per il database **giocatori**; esteso ad
> **arbitri** e **allenatori** (club e nazionali, incl. coppe europee); poi
> un **controllo finale su Wikipedia** (§6-bis, ora esaustivo su richiesta
> dell'utente); un elenco di **arricchimenti** (§1.8: età, esperienza,
> attendance, rigori...); una **revisione critica** con 10 problemi trovati
> e le correzioni proposte (§6-ter); una **gerarchia esplicita della grana
> dei dati** (§1.0: evento → partita club/nazionale unificata →
> convocazione-finestra → stagione derivata); una **checklist completa dei
> dati giocatore** (§1.9) con un nuovo asse — il **rendimento per livello
> avversario** e un **indice di forza del club** ancora da progettare
> (§1.10); un'**appendice di idee prospettiche catturate ma non ancora
> ricollocate** (§8, es. notizie di infortuni/cambio allenatore/meteo che
> dovrebbero muovere le previsioni in corso di settimana), poi generalizzate
> (§8-bis: erano esempi, non l'elenco — H2H, infortuni ricostruiti,
> squalifiche reali); e un **indice** in testa al documento più un giro di
> **decisioni operative** (§6-quater: da dove si parte, tenere i grezzi
> così come sono, giocatori fuori dalle 5 leghe, test da implementare, e
> la verifica — positiva — che il `player_id` regge anche fuori dalle 5
> leghe). Vive come pista aperta in
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
> (708 MB, cache locale ripulita a fine verifica — ripetuta una seconda
> volta per il controllo di §1.8-bis, stessa disciplina).

## Indice — dove sta cosa

Il documento è cresciuto molto: questo indice serve a non dover rileggere
tutto per trovare una cosa già scritta (stesso motivo per cui `PISTE.md` ha
il suo §0-bis).

| sezione | cosa contiene |
|---|---|
| §0 | perché questo piano esiste, e con che grado di certezza |
| §1.0 | grana dei dati: evento → partita → convocazione-finestra → stagione |
| §1.1 | Tier A giocatori — file già in casa (`appearances.csv`, `games.csv`...) |
| §1.2 | Tier B giocatori — tocchi/passaggi/dribbling, nessuna fonte pulita nota |
| §1.3 | nazionali — il fronte più scoperto, serve l'elenco dei convocati |
| §1.5 | arbitri — struttura ciò che la Fase 125/126 ha già misurato |
| §1.6 | allenatori — fronte nuovo, ipotesi persistenza dello stile |
| §1.7 | riepilogo per le richieste utente (giocatori+arbitri+allenatori) |
| §1.8 | arricchimenti: età, esperienza, attendance, rigori... |
| §1.9 | **checklist completa dei 35 dati-giocatore**, con tier, rimandi e marcatura temporale ⏱️ |
| §1.10 | rendimento per livello avversario, indice forza club, esperienza pesata |
| §1.11 | **dati DERIVATI** — l'inventiva: ritmo dei gol, rimonte, coesione dell'undici... |
| §2 | bozza di schema (tabelle, chiavi, come agganciare i nomi) |
| §3 | come dividere il lavoro fra più agenti |
| §4 | idee d'uso (NON decise) — a, b, c, c-bis, c-ter, d, e, f, g, h |
| §5 | rischi e limiti dichiarati onestamente |
| §6 | primi passi concreti, in ordine (nessuno ancora eseguito) |
| §6-bis | controllo finale con **fonte indipendente** (non solo Wikipedia: due fonti le abbiamo già offline) |
| §6-ter | **10 problemi trovati** rileggendo il piano in modo avversariale, con le correzioni |
| §6-quater | decisioni operative prese e domande ancora aperte, prima di partire |
| §6-quinquies | **terzo giro di problemi** e risposte: regola R8 (⏱️), obiezione ritirata sul "ponte", 3 verifiche tecniche |
| §7 | collegamenti ad altri file del repo |
| §8 | 4 idee prospettiche catturate, da ricollocare quando il piano verrà smontato |
| §8-bis | quelle 4 erano ESEMPI — il principio generale (H2H, infortuni, squalifiche...) |

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

### 1.0 · Gerarchia dei dati: a che grana raccogliere (partita per partita, o stagione per stagione?)

Chiarito ragionandoci insieme (29/07/2026): **la grana di base è la
partita, non la stagione**. Non sono due raccolte alternative — lo
stagionale è una vista **derivata** per somma, mai raccolto a parte, stesso
principio già usato altrove nel piano (`manager_match_style.csv` è
"derivato, non raccolto", §2). Motivo tecnico oltre che di metodo: la fonte
stessa (`appearances.csv`) è già una riga per (giocatore, partita) — un
totale stagionale raccolto a parte sarebbe una **perdita** di informazione
rispetto a quello che si può derivare dal dato già sul disco, e le cose che
contano di più per questo piano (fatica, esperienza cumulata fino a QUELLA
partita) non si possono calcolare da un totale stagionale: servono le date
delle singole partite.

Discutendone è emerso che i livelli utili sono **quattro**, non tre — le
nazionali aggiungono un livello che il campionato non ha:

1. **Evento** (dentro la partita, minuto per minuto) — gol, cambio,
   cartellino. Il livello più fine, già coperto concettualmente da
   `game_events.csv` (§1.1). Vale sia per club sia per nazionale, nessuna
   differenza strutturale;
2. **Presenza a partita** — una riga per (giocatore, partita): minuti
   giocati, titolare/subentrato, gol, assist, cartellini. **Non serve una
   tabella diversa per club e nazionale**: è la stessa identica struttura,
   con un campo `tipo_competizione`/`selezione` in più (campionato, coppa
   nazionale, coppa europea, o nazionale — e per la nazionale, quale
   selezione). Un giocatore in un dato giorno gioca o per il club o per la
   nazionale, mai le due cose insieme: si sommano nella stessa tabella, non
   in due tabelle parallele da far quadrare dopo;
3. **Convocazione/finestra** (livello nuovo, emerso ragionandoci sopra) —
   una finestra FIFA raggruppa più partite di nazionale in ~10 giorni, ed
   **"essere convocato" è un fatto che esiste anche se il giocatore poi fa
   zero minuti**. Un convocato mai sceso in campo ha comunque viaggiato,
   saltato gli allenamenti col club, accumulato fuso orario — tutto conta
   per la fatica anche senza un minuto giocato. Registrare solo le "righe
   di partita giocata" perderebbe esattamente questo caso, probabilmente il
   più insidioso: il giocatore "sparisce" dai dati proprio quando in realtà
   è stato via una settimana. Serve quindi un dato a parte, **l'elenco dei
   convocati per ogni finestra**, non derivabile dalle sole presenze a
   partita (schema in §2, `player_national_callups.csv`);
4. **Stagione** — derivata per somma dai livelli 2 e 3, sommando
   SEPARATAMENTE club e nazionale (per non nascondere quanto viene da dove)
   e insieme (per il totale che serve alla fatica).

**Il confronto fra giocatori** (idea dell'utente: "potremmo anche
confrontare i minuti giocati da ogni giocatore") non è un livello a sé, è
una **query** sopra i livelli 2+3: presa una finestra temporale (es. "ultimi
15 giorni"), sommare minuti-club + minuti-nazionale per ogni giocatore e
ordinare — è così che si individua chi è più a rischio fatica rispetto ai
compagni o rispetto a chi affronterà nella prossima partita, incrociabile
con l'esperienza cumulata (§1.8: un giovane con molti minuti consecutivi
rischia diversamente da un veterano).

**Nota di onestà, che non cambia il resto del piano**: la
convocazione-per-finestra resta esattamente il pezzo che §1.3/§1.6
segnalano già come scoperto (nessuna fonte nota per le finestre FIFA
regolari, solo per i tornei finali). Questa gerarchia non risolve quel
buco, lo **precisa**: il bersaglio da cercare è specificamente "elenco dei
convocati per finestra", non genericamente "partite di nazionale giocate".

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
nazionale, sarà più stanco").

**Il bersaglio, precisato in §1.0**: non genericamente "partite di
nazionale giocate" — quello lo dà in parte già `games.csv` per i tornei
finali (§1.6). Serve specificamente l'**elenco dei convocati per ogni
finestra FIFA**, perché un giocatore chiamato ma mai sceso in campo conta
comunque per la fatica (viaggio, allenamenti saltati col club) e sparirebbe
da qualunque fonte basata solo sulle partite giocate. Candidati **da
verificare, nessuno testato**:

- **openfootball** (già usato per calendari di coppa, Fase 100/68): copre
  soprattutto competizioni per club; non è verificato se abbia anche
  risultati/formazioni delle nazionali con dettaglio per giocatore, e
  quasi certamente non ha le liste dei convocati (è un calendario, non un
  registro di selezione);
- **Wikipedia**: ha già funzionato come fonte per calendari di coppa (Fase
  100, 3.045 righe recuperate) — potrebbe avere le rose/i marcatori delle
  partite di nazionale, ma **non** tipicamente i minuti giocati per giocatore
  con la stessa granularità del club. Le pagine "\<Nazionale\> squad" per
  singola finestra/amichevole (quando esistono) sarebbero il candidato più
  vicino a un elenco-convocati, ma la copertura per le finestre "minori"
  (non tornei finali) non è verificata;
- **Transfermarkt**: le pagine-giocatore hanno spesso una sezione "presenze in
  nazionale" — ma il mirror GitHub che alimenta `src/data/transfermarkt.py`
  oggi copre solo valori/infortuni per club, **non verificato** se includa
  anche questo. Le federazioni nazionali pubblicano di norma la lista dei
  convocati sul proprio sito ufficiale ad ogni finestra: mai controllato se
  raggiungibile/con `robots.txt` permissivo, fonte primaria migliore di un
  aggregatore ma da verificare una federazione alla volta.

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
| stanchezza da minuti consecutivi + nazionale | A (club) + fronte nuovo (nazionale) | minuti-club da Tier A; per la nazionale serve l'**elenco dei convocati per finestra** (§1.0/§1.3), non solo le partite giocate — **senza fonte** oggi |
| confronto del carico fra giocatori | query, non dato a sé | somma minuti-club+nazionale su una finestra, da `player_match_appearances.csv`+`player_national_callups.csv` (§1.0, §4h) |
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
  > ✅ **VERIFICATO (30/07/2026), punto 7 di §6-quater**: a differenza di
  > arbitri/allenatori (§6-ter problema 1, nessun ID, solo un nome libero),
  > il giocatore ha un `player_id` **stabile e globale**. Controllato
  > scaricando di nuovo il dataset: `players.csv` ha **50.149 righe, 50.149
  > `player_id` distinti** (zero duplicati — è una chiave pulita). Su
  > **10.596 giocatori** visti in una delle nostre 5 leghe, **5.270 (50%)**
  > compaiono con lo STESSO `player_id` anche in una coppa europea
  > (CL/EL/Conference/qualificazioni), e **8.401 (79%)** anche in
  > un'altra lega/competizione. Esempio concreto: il `player_id` di Sofyan
  > Amrabat compare sotto **18 competizioni diverse** (5 leghe, coppe
  > nazionali, coppe europee, e il Mondiale `FIWC`), sempre con lo stesso
  > numero. Il player_id regge quindi bene anche fuori dalle 5 leghe — un
  > rischio in meno rispetto a quanto temuto;
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

### 1.9 · Checklist completa dei dati giocatore (elenco unico, richiesta utente)

**Principio di raccolta per questo fronte, dichiarato esplicitamente
dall'utente**: qui NON si filtra per utilità immediata al modello. Il
principio §3 del `CLAUDE.md` ("testare la versione economica prima di
investire") resta valido per l'infrastruttura **costosa** (Tier B, nuove
fonti da cercare) — ma per i campi a **costo marginale ~zero** (già negli
stessi file identificati in §1.1) la scelta è raccogliere ora, anche senza
un uso identificato oggi, e decidere l'utilizzo più avanti. Non è uno
strappo al metodo: nessun campo qui sotto richiede un'infrastruttura nuova
da costruire, solo una colonna in più nel parser.

Elenco unico di tutto ciò che è stato proposto per il giocatore, con dove è
trattato in dettaglio nel piano, il tier, e — **obbligatoria dalla regola R8
del `CLAUDE.md`** (§6-quinquies punto 1) — la **disponibilità temporale**:
`pre` = noto prima del fischio, `post` = esiste solo a partita finita,
`statico` = anagrafica che non dipende dalla partita. La colonna `post` non
è inutilizzabile: è utilizzabile **come storia delle partite precedenti**,
mai della partita da prevedere.

| # | dato | tier | ⏱️ | dove nel piano |
|---|---|---|:--:|---|
| 1 | minuti giocati a partita (titolare/subentrato, minuto in/out) | A | `post` | §1.0, §1.1 |
| 2 | gol | A | `post` | §1.1 |
| 3 | assist | A | `post` | §1.1 |
| 4 | tocchi | B | `post` | §1.2 |
| 5 | passaggi (tentati/riusciti) | B | `post` | §1.2 |
| 6 | dribbling (tentati/riusciti) | B | `post` | §1.2 |
| 7 | interventi difensivi (contrasti) | B | `post` | §1.2 |
| 8 | stanchezza da minuti consecutivi, club + nazionale | A (club) / scoperto (nazionale) | **`pre`** (somma di `post` passati) | §1.0, §1.3, §4a |
| 9 | vantaggio/svantaggio dai tocchi in un certo tipo di partita | B (+ §1.10 per "tipo di partita" = livello avversario) | `post` | §1.2, §1.10 |
| 10 | gol subiti per portiere | nessuna fonte nuova | `post` | §1.1 |
| 11 | età esatta a partita | A, derivata | **`pre`** | §1.8 |
| 12 | esperienza (presenze/minuti cumulati, anche pregressa fuori le 5 leghe) | A, derivata | **`pre`** (cumulata *fino a* quella partita) | §1.8 |
| 13 | elenco convocati per finestra nazionale (non solo chi ha giocato) | scoperto | **`pre`** | §1.0, §1.3 |
| 14 | confronto del carico fra giocatori | query, non dato a sé | **`pre`** | §1.0, §4h |
| 15 | capitano per partita | A — `game_lineups.csv` ha già `team_captain` | `post` (⚠️ noto a T−1h con la formazione ufficiale) | nuovo qui |
| 16 | cambio di ruolo recente | A, derivata da `ruolo_in_campo` nel tempo | **`pre`** (dalle partite passate) | nuovo qui |
| 17 | falli commessi/subiti per singolo giocatore | B (oggi solo a livello squadra, Fase 96) | `post` | nuovo qui |
| 18 | xG e xA individuali (non di squadra) | B | `post` | nuovo qui |
| 19 | recuperi palla e intercetti | B | `post` | nuovo qui |
| 20 | chi calcia corner e punizioni | B (estende l'idea rigori) | `post` (ma la *tendenza* storica è `pre`) | §1.8 |
| 21 | grandi occasioni create/sprecate | B | `post` | nuovo qui |
| 22 | storia infortuni per giocatore, **ricostruita per intero all'indietro** (non solo da qui in avanti) — date, tipo, durata | scoperto — oggi solo stima aggregata per squadra (`transfermarkt.py`) | **`pre`** ⚠️ *solo se la data di inizio è nota prima*, vedi §6-quinquies | nuovo qui, ampliato §8-bis |
| 23 | peso, accanto all'altezza | A da verificare | `statico` | nuovo qui, come §1.8 |
| 24 | rendimento per livello avversario (più forte/pari/più debole) | nuovo asse, richiede l'indice di forza (§1.10) | **`pre`** | §1.10 |
| 25 | squadre passate in carriera, con un indice di forza 0-1 ciascuna | nuovo, richiede l'indice di forza (§1.10) | **`pre`** | §1.10 |
| 26 | **esperienza PESATA per livello di competizione** (una finale di Champions da titolare ≠ un girone minore) | nuovo, richiede `peso_competizione` (§1.10) | **`pre`** | §1.10 |
| 27 | squalifiche REALI (storico di quelle scontate davvero, non solo calcolate dalle regole) | scoperto — oggi solo calcolate da `disciplina.py` sui cartellini, mai verificate contro un dato reale | **`pre`** | nuovo qui, ampliato §8-bis |
| 28 | testa a testa (H2H) a livello di **singolo giocatore**, non solo di squadra | nuovo asse | **`pre`** | nuovo qui, ampliato §8-bis |
| 29 | caratteristiche di gioco individuali, oltre i conteggi grezzi (es. "recupera molto e riparte veloce" invece del solo numero di recuperi) | C — dipende interamente dallo sblocco del Tier B, nessuna fonte nota nemmeno per i conteggi grezzi | `post` → tendenza `pre` | nuovo qui |
| 30 | **minuti giocati in inferiorità/superiorità numerica** (dal minuto del rosso) | A — `red_cards` in `appearances.csv` + minuto in `game_events.csv` | `post` | §1.11 |
| 31 | **ruolo giocato ≠ ruolo naturale** (schieramento d'emergenza) | A — `players.csv` vs `game_lineups.csv` | `post` (⚠️ `pre` con la formazione ufficiale) | §1.11 |
| 32 | **già ammonito, e da che minuto** (comportamento nel resto della partita) | A — minuto del giallo in `game_events.csv` | `post` | §1.11 |
| 33 | situazione contrattuale (scadenza) e giorni dall'arrivo al club | A da verificare — `transfers.csv`, campo contratto **non verificato** | **`pre`** | §1.11 |
| 34 | prestito, e prestito **dalla squadra che si affronta** | A — `transfers.csv` | **`pre`** | §1.11 |
| 35 | numero di maglia (proxy grezza dello status in rosa) | A — già in `game_lineups.csv` | **`pre`** | §1.11 |

**Nota sulla riga 15/31 (`post` con asterisco)**: capitano e ruolo effettivo
sono `post` nel **dato storico** (li leggiamo a partita finita), ma nella
raccolta **prospettica** diventano `pre`, perché escono con la formazione
ufficiale ~1h prima. È il caso che rende la marcatura obbligatoria: la stessa
informazione cambia categoria a seconda di **come** la ottieni.

**Onestà su cosa resta fuori portata**: heatmap/zone di campo, distanza
percorsa, velocità di sprint — dati da tracking GPS/video, prodotti dagli
stessi fornitori già chiusi per il Tier B (§1.2). Nessun motivo di
aspettarsi che diventino disponibili dove tocchi/passaggi non lo sono.

### 1.10 · Rendimento per livello avversario, indice di forza del club, ed esperienza PESATA per livello

**L'idea dell'utente**: non fermarsi a "quanto conta la partita" (posta in
gioco) ma guardare **quanto è forte l'avversario** — squadre più forti,
dello stesso livello, più deboli — sia per il singolo giocatore sia per la
squadra.

**Distinta dalla covariata già bocciata**: `docs/PANCHINA.md` registra già
una covariata `stakes` (posta in gioco) **bocciata** a livello squadra —
ma "posta in gioco" e "forza dell'avversario" sono assi diversi (una
partita-salvezza contro l'ultima in classifica ha posta alta e avversario
debole). Non è la stessa idea travestita, va trattata come un test
indipendente. Un'idea consanguinea **esiste già** a livello squadra in
`data/stagione_2026_2027/README.md` §4.3 ("Rendimento contro alta/bassa
classifica", 🟢 misurabile) — qui si propone di (a) **estenderla al singolo
giocatore**, (b) renderla **continua** invece che binaria alta/bassa
classifica.

**Per farlo serve un indice di forza del club**, da 0 a 1, che oggi non
esiste. Candidati per costruirlo, in ordine di quanto sono già in casa:

- **valore di rosa** — già calcolato per le 5 leghe (`player_scores.py`/
  `transfermarkt.py`): un percentile del valore-rosa dentro la
  lega-stagione è un candidato diretto, ma copre solo le nostre 5 leghe;
- **posizione in classifica** — già nello snapshot per le 5 leghe;
- **`clubs.csv`** (upstream `davidcariboo/player-scores`, **non ancora
  ispezionato in questa sessione** — a differenza degli altri file elencati
  in §1.1, questo va dichiarato non verificato): candidato naturale per un
  indice **già pronto e globale** (non solo le 5 leghe), perché
  `national_teams.csv` — stesso dataset — ha già un campo
  `total_market_value` per le nazionali: è plausibile (da controllare, non
  assumere) che `clubs.csv` abbia un equivalente per i club, utile proprio
  per i club **fuori** dalle 5 leghe che compaiono nella carriera di un
  giocatore/allenatore.

**Due usi collegati, stesso indice**:

1. segmentare le performance (giocatore e squadra) per livello avversario,
   invece del solo alta/bassa classifica binario (voce 24 di §1.9);
2. caratterizzare il **percorso di carriera** di un giocatore o di un
   allenatore — non solo *quanta* esperienza (§1.8) ma *di che qualità*:
   ha giocato/allenato squadre forti o deboli? Si somma/media l'indice delle
   squadre passate, usando lo stesso storico-club-in-carriera già
   derivabile dal dataset globale (§1.8) — nessuna fonte in più (voce 25 di
   §1.9).

**Onestà**: è un indice **nuovo da progettare**, non esiste ancora in
nessuna forma; e la versione più semplice di "quanto conta la partita"
(stakes) è già stata provata a livello squadra e bocciata — un motivo in
più per trattare "forza dell'avversario" come un'ipotesi da verificare, non
un risultato scontato.

**Estensione (29/07/2026, esempio dell'utente): l'esperienza non è solo un
conteggio, è anche un LIVELLO.** "Un giocatore che ha giocato 3 finali di
Champions League da titolare dovrebbe essere più forte di uno che ha
sempre giocato in Serie B" — l'esperienza cumulata di §1.8/§4f
(`presenze_carriera_a_oggi`, `minuti_carriera_a_oggi`) tratta ogni partita
allo stesso modo: 90 minuti in un girone di Conference League contano
quanto 90 minuti in una finale di Champions. Serve un secondo indice,
**gemello** di quello di forza-del-club ma sulla **competizione/il turno**
invece che sul club:

- **`peso_competizione` (0-1)**: un ordinamento per tipo di competizione
  (finale > semifinale > fase a gironi di Champions > campionato top-5 >
  coppa nazionale > campionati minori...), costruibile da campi già
  identificati — `competition_type`/`round` di `games.csv` (§1.8, già
  proposti per il contesto andata/ritorno) danno competizione e turno
  precisi, la `confederation`/`type` di `competitions.csv` (visto
  scaricando il dataset, non ancora usato nel piano) distingue campionati
  da coppe e coppe nazionali da internazionali;
- **esperienza pesata**: invece di sommare 1 per ogni presenza, sommare
  `peso_competizione` (ed eventualmente un peso titolare/subentrato) — così
  il giocatore delle 3 finali di Champions da titolare pesa più del
  giocatore con lo stesso numero di presenze tutte in Serie B, esattamente
  l'esempio dell'utente;
- **relazione con l'indice di forza del club**: sono complementari, non lo
  stesso indice — un club forte può giocare partite di basso livello
  (campionato debole) e un club debole può giocare una partita di alto
  livello (una finale di coppa nazionale contro una big). Tenerli separati
  finché non si misura se uno predice l'altro.

**Onestà**: anche questo indice è nuovo da progettare, e la scelta
dell'ordinamento fra competizioni (dove va una finale di Coppa Italia
rispetto a un girone di Champions?) è in parte soggettiva — da dichiarare
come tale, non da presentare come un fatto oggettivo.

### 1.11 · Dati DERIVATI — l'inventiva (30/07/2026)

Sezione diversa da tutte le precedenti: qui non si tratta di **procurarsi**
dati nuovi, ma di **inventare** informazioni nuove da quelli che avremo già.
Costo di raccolta **zero** (è tutto calcolo), e — come chiede l'utente —
l'elenco non è filtrato per utilità dimostrata: serve inventiva, e alcune di
queste voci saranno rumore.

**Gli esempi dell'utente, generalizzati.**

- **Ritmo di un evento, e tempo trascorso dall'ultimo** — "un giocatore che
  segna ogni 150 minuti, e sono passati 120 minuti dall'ultimo gol". Si
  generalizza a ogni evento contabile: minuti per gol, per assist, per
  cartellino, per rigore guadagnato; e il **tempo trascorso dall'ultimo**.
  ⚠️ **Attenzione statistica, da dichiarare subito**: se i gol fossero un
  processo di Poisson, il tempo trascorso dall'ultimo gol **non direbbe
  nulla** su quando arriva il prossimo (assenza di memoria) — l'idea è
  interessante proprio perché mette alla prova quell'assunzione, che è la
  base di tutto il motore del progetto. Due esiti entrambi utili: se non
  c'è effetto, si conferma il Poisson; se c'è, si è trovata una crepa vera.
- **Rimonte e crolli** — "una squadra va sempre in svantaggio e poi rimonta?
  come gioca?". Dal minuto dei gol (`game_events.csv`) si ricostruisce il
  **punteggio minuto per minuto**, e da lì: quante volte va sotto, quanti
  punti recupera da sotto, quanti ne butta da avanti, e come cambia il suo
  ritmo di gioco nei due stati. È lo stesso ingrediente della pista 6-bis
  (il modello a due stadi, "game state") — con l'angolo nuovo che qui
  diventa una **caratteristica della squadra**, non solo uno stato della
  partita.

**Altre idee nello stesso spirito** (tutte calcolabili, nessuna già nel
progetto salvo dove indicato):

*Sul tempo e sul punteggio*
- distribuzione dei gol per fascia di 15′, **per giocatore** (a livello
  squadra è già previsto in `data/stagione_2026_2027/README.md` §4.3);
- minuto medio del primo gol, fatto e subito; quanto spesso segna per
  prima, e quanto vince quando lo fa;
- gol negli ultimi 5-10 minuti — la squadra "che segna sempre alla fine";
- rendimento **dopo** un rosso (proprio o avversario), e dopo un rigore
  sbagliato;
- serie aperte: partite consecutive segnando, senza subire, senza vincere.

*Sul giocatore*
- **over/underperformance sull'xG**: chi segna molto più di quanto i suoi
  tiri valgano è candidato a raffreddarsi (ritorno alla media) — richiede
  l'xG individuale (voce 18, Tier B);
- **impatto da subentrato**: gol/assist per minuto giocato entrando dalla
  panchina, distinto da quello da titolare;
- **sostituito presto ripetutamente**: un giocatore tolto sistematicamente
  al 60' è un segnale di condizione o di fiducia dell'allenatore;
- **quota di gol+assist della squadra** che passa da un solo giocatore
  (dipendenza da un singolo, già ipotizzata a livello squadra);
- **distanza dal picco di carriera**, incrociando età e curva di rendimento.

*Sulla squadra e sull'undici*
- **coesione dell'undici**: quanti minuti hanno già giocato **insieme** gli
  undici titolari — una squadra sempre uguale contro un undici rimaneggiato;
- **turnover rispetto alla partita precedente**: quanti cambi nell'undici;
- **rendimento con/senza un certo giocatore** (e con/senza una certa
  coppia) — il modo più diretto di quantificare "quanto incide";
- **pattern di sostituzione dell'allenatore**: minuto del primo cambio,
  quanti ne usa, se cambia prima quando è sotto (firma dell'allenatore
  diversa da quella stilistica di §4 c-bis);
- **"i suoi giocatori"**: quali giocatori un allenatore si porta dietro
  cambiando squadra (incrocio `manager_spells` × `transfers`).

*Sul contesto*
- **distanza di trasferta**: `games.csv` ha già il campo `stadium`;
  servirebbero le coordinate (fonte esterna, costo basso) per trasformarlo
  in km — si somma bene alla fatica;
- **derby / rivalità**: stessa città o regione, derivabile se `clubs.csv`
  porta la città (**non verificato**);
- **orario di inizio**: se il campo `date` di `games.csv` contiene anche
  l'ora (**non verificato**) — una partita delle 12:30 non è come una delle
  20:45.

**Due avvertenze oneste, valide per tutta la sezione.** (1) Diverse di
queste idee sono cugine di cose **già bocciate a livello squadra** (la
covariata `stakes`, la forma, il valore rosa: `docs/PANCHINA.md`): il fatto
che siano nuove *a livello giocatore* non garantisce che funzionino. (2)
Sono tutte **derivate**, quindi ereditano la marcatura temporale della
fonte (R8): una tendenza calcolata sulle partite passate è `pre` ed è
utilizzabile; la stessa quantità misurata **sulla partita in corso** è
`post` e non lo è.

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

player_match_appearances.csv        # Tier A — livello 2 di §1.0: una riga per
    season, date, tipo_competizione,  #   (player_id, partita), CLUB e NAZIONALE
    selezione_o_club, avversario,     #   nella STESSA tabella (§1.0) — distinte
    titolare (bool), minuto_in,       #   dal campo tipo_competizione/selezione,
    minuto_out, minuti_giocati,       #   non da due tabelle parallele
    ruolo_in_campo, gol, assist,
    ammonizioni, espulsione (bool),
    eta_esatta                      # derivata: data_nascita vs data partita
    presenze_carriera_a_oggi        # derivata: conteggio su TUTTO appearances.csv,
    minuti_carriera_a_oggi          #   non filtrato alle 5 leghe (§1.8)

player_match_advanced.csv           # Tier B — SOLO se/quando una fonte esiste
    season, home_team, away_team, player_id, tocchi, passaggi_tentati,
    passaggi_riusciti, dribbling_tentati, dribbling_riusciti,
    contrasti, tiri, tiri_in_porta, duelli_aerei_vinti

player_national_callups.csv         # livello 3 di §1.0 — SOLO se/quando una fonte
    player_id, selezione, finestra_fifa (es. "2026-09"),  # esiste (§1.3): NON
    data_convocazione, ha_giocato (bool)                  # derivabile dalle sole
                                                           # presenze a partita —
                                                           # un convocato mai sceso
                                                           # in campo non lascia
                                                           # traccia altrove, ma
                                                           # conta per la fatica

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
(`CLAUDE.md` §1.5). **Stesso discorso per lo stagionale del giocatore**
(§1.0, livello 4): niente `player_season_stats.csv` raccolto a parte — è un
`GROUP BY player_id, season` su `player_match_appearances.csv` (+
`player_national_callups.csv` per la quota-nazionale), calcolabile a volo e
quindi non versionato separatamente, salvo serva pubblicarlo per il
confronto con Wikipedia/Understat in §6-bis.

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

h. **Confronto del carico fra giocatori** (§1.0, idea dell'utente): non un
   dato a sé ma una query sopra `player_match_appearances.csv` +
   `player_national_callups.csv` — presa una finestra temporale (es. gli
   ultimi 15 giorni), sommare minuti-club + minuti-nazionale per ogni
   giocatore e ordinare, per individuare chi è più a rischio fatica rispetto
   ai compagni o a chi affronterà nella prossima partita. Da incrociare con
   l'esperienza (idea f): un giovane con molti minuti consecutivi rischia
   diversamente da un veterano — due covariate distinte, da testare
   separatamente (principio "una cosa alla volta", §6-ter problema 9).

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

**Nota sugli arricchimenti di §1.8 — AGGIORNATA (decisione utente,
29/07/2026): una funzionalità alla volta, non in blocco.** Tecnicamente età,
esperienza, attendance, aggregate/round, formazione e rigori vengono dagli
stessi file già previsti nei passi 0-2 (nessuna riga in più nel `WANTED` del
workflow) — ma questo NON significa importarle e usarle tutte insieme.
L'utente ha confermato il problema 9 della revisione critica (§6-ter,
principio "una cosa alla volta" del `CLAUDE.md` §2): ogni campo va
**aggiunto, testato e valutato singolarmente** — un esperimento per feature,
non un unico backtest con dieci covariate nuove — altrimenti non si saprà
mai quale delle dieci ha funzionato. Ordine proposto (dal più semplice/meno
ambiguo al più delicato, si può rivedere): età esatta → esperienza
giocatore → attendance → aggregate/round → formazione → esperienza
allenatore/arbitro → effetto "nuovo allenatore" → bias casa/trasferta
arbitro → altezza/rigori (questi ultimi due subordinati alla verifica dello
schema, ancora da fare).

## 6-bis · Controllo finale: verifica con fonte indipendente (richiesta utente, 29-30/07/2026)

**Perché**: `games.csv`/`appearances.csv` sono un'unica fonte (Transfermarkt
via Kaggle) — anche se la copertura interna è quasi completa (§1.1/§1.5/§1.6),
un dato sbagliato A MONTE non si vede confrontando la stessa fonte con se
stessa. Serve un'informazione **indipendente**: è la regola R5 del
`CLAUDE.md` ("diagnosticare con informazione indipendente... un'altra
fonte"), già seguita con successo in questo progetto — i calendari di coppa
(Fase 100, Wikipedia) e le rose 2026-27 dove il dataset non arriva
(`data/stagione_2026_2027/README.md` §3-ter, "Wikipedia come fonte della
rosa").

> 🔄 **RISTRUTTURATO il 30/07/2026 — non è (solo) "il controllo Wikipedia".**
> Domanda dell'utente: *"possiamo cercare info sulla singola partita? o il
> controllo deve diventare un controllo su internet o simile?"*. Ragionandoci,
> la risposta è che **Wikipedia era la scelta sbagliata come punto di
> partenza**, per un motivo che avevamo sotto gli occhi:
>
> **due delle fonti indipendenti migliori ce le abbiamo già in casa, offline
> e complete.**
>
> | cosa verifichiamo | fonte indipendente | dove sta | copertura |
> |---|---|---|---|
> | risultati, date, squadre di `games.csv` | i nostri **snapshot** `data/*_matches.csv` (origine football-data, **indipendente** da Transfermarkt) | già nel repo | **100%** sulle 5 leghe × 9 stagioni, offline, zero rete |
> | minuti per giocatore-stagione | **Understat** (`understat.season_players`, indipendente da Transfermarkt) | già nel repo | 5 leghe, aggregato-stagione |
> | mandati degli allenatori | Wikipedia ("List of \<club\> managers") | rete | alta, formato sistematico |
> | arbitri per partita | Wikipedia (pagine di stagione) o siti delle leghe | rete | **ignota, da misurare** |
> | cartellini per giocatore | i nostri snapshot (totali di squadra) + `disciplina.py` | già nel repo | incrocio parziale |
>
> **Il principio giusto non è "si controlla su Wikipedia", è: ogni tabella
> deve essere verificata contro almeno UNA fonte indipendente, dichiarata,
> e si sceglie la migliore disponibile per quel fronte** — preferendo, dove
> esiste, quella che abbiamo già offline (più veloce, riproducibile, e senza
> caricare siti di terzi, coerente con la regola R5.3).
>
> **Sulla singola partita**: sì, ma non da Wikipedia. Per la singola partita
> il controllo migliore è **contro i nostri snapshot** (risultato, data,
> squadre: verificabile al 100% e gratis). Wikipedia sulla singola partita
> esiste solo per le gare importanti (finali, big match) — utile come spot
> check, inutile come censimento.
>
> **Correzione onesta a quanto scritto sotto**: "completo su ogni dato" è
> realizzabile **alla grana della partita** per il fronte
> risultati/arbitri/allenatori, ma **non** alla grana giocatore-partita —
> `appearances.csv` ha **1.894.350 righe** (misurate) e Wikipedia pubblica
> **totali di stagione**, non tabellini per partita. Per i giocatori il
> censimento completo è quindi **per giocatore-stagione** (contro Understat,
> offline), non per giocatore-partita: la differenza va dichiarata, non
> lasciata intendere.
>
> **Ogni fonte esterna nuova** (siti delle leghe per gli arbitri, ecc.) passa
> per il controllo di rito prima dell'uso: `robots.txt`, licenza, e nessun
> aggiramento di blocchi — le stesse regole che hanno chiuso quattro fonti in
> §1.2.

**Cosa verificare, fronte per fronte, e con quale pagina Wikipedia**:

| tabella | pagina Wikipedia candidata | affidabilità attesa |
|---|---|---|
| `manager_spells.csv` (allenatori) | "Managerial history of \<club\>" / tabelle "List of \<club\> F.C. managers" — quasi tutti i club delle 5 leghe ne hanno una, con date di inizio/fine mandato | **alta**: è un formato standard e sistematico su Wikipedia, il più adatto dei tre a questo controllo |
| `referee_matches.csv` (arbitri) | pagine di stagione delle leghe principali (es. "20XX–XX Serie A season") includono a volte tabelle/tabellini con l'arbitro, più spesso per big-match e finali di coppa che per il turno generico | **non uniforme, da misurare**: nessuna verifica preliminare in questo progetto su quanto sia sistematica — potrebbe risultare parziale |
| `player_match_appearances.csv` (aggregati stagionali) | tabelle "Career statistics" nelle pagine giocatore (presenze/gol/assist per stagione e competizione) | **media-alta** per i giocatori di rilievo, più debole per le rotazioni minori |

**Metodo proposto — AGGIORNATO (decisione utente, 29/07/2026): controllo
COMPLETO, non a campione.** La prima stesura proponeva un campione (30-50
casi) con una soglia di allarme statistica; l'utente ha chiesto esplicitamente
il controllo **su ogni dato raccolto**, non su un sottoinsieme. Cambia il
disegno:

1. **censimento, non campione**: ogni riga di `referee_matches.csv`/
   `manager_spells.csv`/`player_match_appearances.csv` per cui Wikipedia offre
   un dato comparabile va verificata, non solo un sottoinsieme. Conseguenza
   diretta e positiva: **il problema 4 della revisione critica (§6-ter) sparisce
   da solo** — un censimento non ha bisogno di un intervallo di confidenza o di
   una soglia-su-campione, perché non stima una percentuale ignota: la
   riporta esatta;
2. **per farlo senza sovraccaricare Wikipedia** (resta valida la regola
   R5.3 sul rispetto di `robots.txt`/rate-limit anche per un uso
   "consentito"): recuperare **una pagina per volta** (es. una pagina di
   stagione, o una pagina "manager history" di un club) e confrontarla con
   **tutte** le righe nostre che quella pagina copre, invece di fare una
   richiesta per ogni singola partita — così il costo di rete scala con il
   numero di pagine Wikipedia (poche centinaia), non con il numero di
   partite (migliaia). Dove disponibile, preferire l'API strutturata di
   Wikipedia (REST/Action API) alla scrematura dell'HTML grezzo, per
   un'estrazione più affidabile delle tabelle;
3. **tasso di concordanza pubblicato riga per riga**: quante voci
   coincidono, quante divergono, quante Wikipedia **non copre affatto** (un
   "non trovato" non è un errore, va contato separatamente — vedi il limite
   sulla copertura sotto: un censimento completo dei NOSTRI dati non
   garantisce che Wikipedia li copra tutti);
4. **ogni divergenza reale (non "non trovato") si istruisce singolarmente**
   con la procedura R5-§5-bis (spiegare prima di accusare, cercare il dato
   vero con un'ulteriore fonte indipendente, mai correggere a mano — regola
   R3) — un censimento completo produrrà più divergenze in valore assoluto
   di un campione, quindi conviene classificarle per tipo (typo di grafia,
   nome diverso per la stessa persona, dato davvero sbagliato) prima di
   istruirle una per una;
5. **il controllo è un gate, non un'operazione singola**: nessuna tabella si
   considera pronta per il modeling finché il censimento non è completo — si
   registra comunque il risultato anche se negativo (principio §1.4 del
   `CLAUDE.md`).

**Limiti onesti, dichiarati subito**:

- **Wikipedia non sostituisce la fonte primaria**: è un controllo
  incrociato, non un dato migliore di Transfermarkt. Se le due fonti
  divergono, la procedura R5 decide qual è quella vera — non si sceglie a
  priori quale fidarsi;
- **"completo sui NOSTRI dati" ≠ "Wikipedia li copre tutti"**: anche
  facendo un censimento invece di un campione, restano partite che
  Wikipedia semplicemente non riporta (per gli arbitri in particolare, non
  c'è oggi nessuna misura di quanto sistematicamente Wikipedia riporti
  l'arbitro partita-per-partita nelle 5 leghe) — il censimento è completo
  sul lato "quante ne abbiamo controllate", non garantisce una copertura
  del 100% sul lato "quante Wikipedia sapeva confermare";
- **costo**: un controllo esaustivo è più lento di un campione — è una
  scelta dichiarata dall'utente (completezza prima della velocità), non una
  sottovalutazione del costo;
- **ordine**: questo controllo va fatto DOPO l'importazione (passi 0-3 di
  §6), non prima — prima si costruisce la tabella dai dati già in casa, poi
  si verifica con una fonte indipendente, esattamente come richiesto.

## 6-ter · Problemi trovati e correzioni (revisione critica, 29/07/2026)

Su richiesta dell'utente ("cerchiamo di trovare problemi in tutto questo
ragionamento e cerchiamo di risolverli"): una rilettura avversariale del
piano, non solo dell'idea originale. Dieci problemi, ciascuno con la
correzione proposta; due hanno già una risposta esplicita dell'utente.

**1. Allenatori e arbitri non hanno un ID stabile — solo un nome libero.**
A differenza del giocatore (`player_id` numerico in `appearances.csv`/
`players.csv`), `games.csv` dà `referee` e `home/away_club_manager_name`
come **testo puro**, senza ID interno Transfermarkt. Una variante di grafia
(accenti, "Jr.", nome vs cognome) crea silenziosamente un "allenatore
fantasma" diverso — un problema più serio di quanto dichiarato in §1.6/§2
("stringa libera, va normalizzata"), perché qui non c'è nemmeno un ID di
riferimento contro cui disambiguare, a differenza dei giocatori.
*Correzione*: costruire un dizionario nome→entità canonica **con tasso di
aggancio dichiarato**, stesso trattamento già riservato ai nomi-squadra
(`TEAM_ALIASES`) — ogni nome non riconosciuto va **loggato**, mai scartato
in silenzio (la lezione già pagata con "Verona" nei nomi-squadra).

**2. `manager_spells.csv` derivato con "prima/ultima partita" si rompe sui
ritorni.** Un allenatore che lascia un club e **ci torna anni dopo** (capita
spesso) verrebbe fuso in un unico mandato lunghissimo che include l'era di
chi lo ha sostituito nel mezzo, perché la derivazione proposta in §2 prende
solo min/max data.
*Correzione*: derivare i mandati da **sequenze contigue** (ordinare le
partite per club/data, aprire un nuovo mandato ogni volta che il nome
cambia), non da min/max.

**3. "Esperienza globale" rischia di essere il "finto pieno" della regola
R6.** Non è verificato quanto indietro nel tempo arrivi davvero la
copertura di `games.csv` per ogni competizione/paese. Se è parziale, un
giocatore/allenatore/arbitro con carriera vera in un campionato o
un'epoca poco coperti risulterebbe con "poca esperienza" — un numero che
**sembra** una misura e non lo è, esattamente il caso che la regola R6 del
`CLAUDE.md` mette in guardia ("il buco peggiore non è il NaN: è il finto
pieno").
*Correzione*: misurare la profondità storica reale per competizione prima
di fidarsi del conteggio, e trattare l'esperienza come "visibile al
dataset", **mai** come verità assoluta — dichiarare il limite invece di
sottintenderlo.

**4. La soglia del controllo Wikipedia non aveva un intervallo.** ✅
**Risposta dell'utente**: il controllo va fatto **completo, su ogni dato
raccolto**, non a campione. Aggiornato in §6-bis: un censimento non stima
una percentuale ignota da un campione, quindi non serve un intervallo di
confidenza o una soglia arbitraria — il problema si risolve cambiando
disegno, non aggiungendo statistica. Resta comunque da gestire il costo
operativo (§6-bis: recuperare pagine intere invece di una richiesta a
partita) e il limite di copertura (Wikipedia non ha necessariamente un
dato per ogni nostra riga, anche controllandole tutte).

**5. Il rimbalzo "nuovo allenatore" confonde il test sulla firma
stilistica.** Le idee c-bis (lo stile persiste da un club all'altro) e g
(rimbalzo nelle prime partite, §4) non sono indipendenti: se non si
escludono le prime N partite del nuovo mandato, il rimbalzo di breve
periodo contamina la misura di "quanto persiste lo stile".
*Correzione*: modellarle insieme, non separatamente — o escludere la
finestra-rimbalzo dal test di persistenza, o stimare entrambe nello stesso
modello con un termine dedicato al rimbalzo.

**6. La persistenza dello stile può essere selezione, non causa.** Un club
spesso assume un allenatore **perché** il suo stile noto si adatta già alla
rosa/filosofia del club — trovare che "lo stile persiste" potrebbe
riflettere questo bias di selezione nell'assunzione, non un effetto
causale dell'allenatore in sé.
*Correzione*: dichiararlo esplicitamente come limite, stesso spirito di
"misurato ≠ prevedibile" (Fase 99) — il test confermerebbe una
correlazione utile per prevedere, non stabilirebbe la causa.

**7. Il bias casa/trasferta dell'arbitro, senza shrinkage, è rumore per gli
arbitri con poche partite.** La Fase 125 usa già uno shrinkage (K=40, verso
la media di lega) proprio per questo motivo sul fattore-arbitro aggregato;
`referee_home_away_bias.csv` (§2) non lo menzionava.
*Correzione*: stesso shrinkage-verso-la-media già in
`scripts/_run_fase125_cartellini.py`, non una media grezza casa/trasferta.

**8. Riproducibilità: il dataset upstream si aggiorna ogni settimana.**
"Esperienza a oggi" calcolata sul dataset "corrente" darebbe numeri diversi
in sessioni diverse se le righe storiche vengono corrette a monte — viola
il principio di riproducibilità (§1.5 del `CLAUDE.md`: "ogni numero dev'essere
rifacibile da terzi, stesso codice, stessi dati, stessa config").
*Correzione*: fissare/hashare lo snapshot scaricato (stesso pattern già
usato per gli altri file grezzi in `data/raw/`), mai ricalcolare
sull'"ultima versione disponibile" del dataset upstream.

**9. Rischio "kitchen sink": troppe feature nuove insieme.** §1.8 aggiunge
~10 campi in un colpo solo — il principio "una cosa alla volta" (§2 del
`CLAUDE.md`) impone di testarli uno per volta, non in blocco, altrimenti
non si saprà mai quale ha funzionato. ✅ **Risposta dell'utente**: confermato
— tutte queste funzionalità vanno aggiunte un po' per volta. Aggiornato in
§6: un esperimento per feature, con un ordine proposto (età → esperienza
giocatore → attendance → aggregate/round → formazione → esperienza
allenatore/arbitro → nuovo-allenatore → bias arbitro → altezza/rigori).

**10. Minori, ma da dichiarare.** L'esperienza "in nazionale" resta
scoperta anche con la scoperta del dataset globale (solo quella per-club
ne beneficia, §1.8); le date di inizio/fine mandato derivate in
`manager_spells.csv` sono **approssimate ai giorni-partita**, non le date
reali di nomina/esonero — vanno dichiarate come tali, non come esatte; e —
dato che arbitri e allenatori sono persone reali — un punteggio di "bias"
(problema 7) andrebbe presentato con un tono descrittivo/statistico, non
accusatorio, se e quando diventasse pubblico (stesso spirito del principio
§1.6 del `CLAUDE.md`: onestà sui limiti, niente promesse).

## 6-quater · Decisioni operative e domande aperte prima di partire (30/07/2026)

Continuando a rileggere il piano è emerso un secondo giro di osservazioni,
più operative delle prime dieci — con le risposte che l'utente ha già dato
per alcune, e le domande che restano aperte per altre.

**1. Da dove si parte, fra tutti i fronti?** Il piano non ha mai messo in
fila arbitri/allenatori/giocatori/nazionali/big-match/H2H/infortuni fra
loro (§1.8 ha un ordine solo per le sue feature interne). **Proposta**
(da valutare quando si parte davvero, NON vincolante — l'utente ha chiesto
esplicitamente di sottolinearlo): partire da `games.csv`/`club_games.csv`
(arbitri + allenatori, §1.5/§1.6) perché è il passo più economico e
sblocca tre fronti insieme; poi `appearances.csv` (giocatori Tier A,
già scaricato); poi le feature derivate a costo zero (§1.8/§1.10); e per
ultimi i fronti che richiedono una fonte ancora da trovare (nazionali,
Tier B, infortuni, squalifiche reali, H2H). Questo ordine può cambiare
completamente una volta che si guardano i dati da vicino.

**2. Quanto teniamo dei file grezzi?** **Deciso dall'utente**: si scaricano
**tutti** i file già identificati e si tengono **così come sono**, non
distillati in tabelle più piccole — "è importante avere accesso a tutti i
dati in qualsiasi momento". Vale anche per `game_lineups.csv`/
`game_events.csv` (487 MB) oltre a `games.csv`/`club_games.csv`/
`appearances.csv`. Conseguenza pratica per quando si scriverà il codice:
i grezzi vanno comunque **compressi** per stare nel repo (stesso schema
già in uso per `files/player_scores/*.csv.gz`), "teneteli così come sono"
riguarda il contenuto, non il formato del file su disco.

**3. Giocatori che non sono nelle nostre 5 leghe.** Osservazione
dell'utente: nelle partite di Champions/Europa/Conference League, o in
nazionale, incontreremo giocatori di club che non fanno parte delle 5
leghe che il progetto segue (es. un giocatore di un club portoghese o
scozzese in Champions League). **Vanno tracciati anche loro — come,
resta da decidere.** Il punto 7 qui sotto aiuta: il `player_id` di questi
giocatori è lo stesso, stabile, in tutto il dataset (verificato oggi),
quindi tecnicamente non sono "invisibili" — la domanda aperta è
**logistica**: li aggiungiamo a `players.csv` (la nostra tabella
giocatori) fin da subito, con tutti i ~50.000 del dataset globale, o solo
quando compaiono per la prima volta in una partita che ci riguarda
(club delle 5 leghe in coppa, o nazionali)? Nessuna delle due opzioni è
stata scelta.

**4. Il database si aggiornerà da solo?** **Confermato dall'utente**: sì,
una volta finito il lavoro sul passato si continuerà a raccogliere i dati
delle partite nuove per tenere tutto aggiornato (stesso principio già
attivo per il resto del progetto, `scripts/raccolta_giornaliera.py`). Ma
**la priorità adesso è fare bene il lavoro sul passato** — l'aggancio alla
raccolta quotidiana è un passo successivo, non descritto qui in dettaglio.

**5. Controlli automatici (test) — da iniziare a pensarci.** Il `CLAUDE.md`
chiede un test per ogni nuova funzionalità della pipeline; questo piano non
lo aveva mai citato. **Da implementare quando si scriverà il codice vero**
(non ora). Un primo abbozzo di cosa dovranno controllare, per iniziare a
pensarci:
   - **coerenza fra fonti**: i minuti totali di un giocatore in una
     stagione, sommati da `player_match_appearances.csv`, devono tornare
     (entro una tolleranza) con `understat.season_players` — stesso
     controllo già proposto come tracer bullet in §6, ma va reso un test
     permanente, non solo un controllo una tantum;
   - **nessuna riga orfana**: ogni `player_id` in `player_match_appearances.csv`
     deve esistere in `players.csv`, ogni partita deve avere una chiave
     valida — stesso principio di `test_schema_identico_tra_leghe` già nel
     progetto;
   - **tasso di aggancio dichiarato**: un test che fallisce se il tasso di
     match nome→entità di allenatori/arbitri (§6-ter problema 1) scende
     sotto una soglia, così un peggioramento silenzioso della fonte non
     passa inosservato;
   - **copertura minima**: un test che controlla che ogni lega/stagione
     abbia almeno una soglia di copertura minima prima di essere usata,
     stesso principio di `MIN_COVERAGE` già usato in `transfermarkt.py`.

**6. Rapporto fra assenze STIMATE (oggi) e infortuni VERI (se li
troviamo).** `src/data/transfermarkt.py` calcola già `home_absent_count_est`/
`away_absent_count_est` — una **stima aggregata per squadra**, basata sulle
rose Understat incrociate con lo storico infortuni (§DATI.md). Se il fronte
infortuni di §8-bis produce dati **reali per singolo giocatore**, va deciso:
sostituiscono la stima esistente, o convivono (es. la stima resta come
fallback dove il dato reale manca)? **Nessuna decisione presa.**
> ⚠️ **PROMEMORIA per l'utente**: questo punto resta aperto e richiede una
> soluzione — da riprendere in una sessione futura, non dimenticarlo.

**7. `player_id` è stabile anche fuori dalle 5 leghe? — VERIFICATO,
risposta positiva.** Vedi il riquadro in §1.8 (voce "esperienza del
giocatore"): controllato scaricando di nuovo il dataset, `players.csv` è
una chiave pulita (50.149 righe, 50.149 ID distinti, zero duplicati), e la
maggioranza dei giocatori delle 5 leghe compare con lo stesso ID anche in
coppe europee (50%) o altre competizioni (79%). A differenza di
arbitri/allenatori (nessun ID, §6-ter problema 1), per i giocatori questo
rischio è **basso**, non assente: resta da controllare, quando si scriverà
il codice vero, che non esistano rari casi di doppio profilo per la stessa
persona (non cercato in questa verifica, che ha controllato la coerenza
dell'ID, non l'unicità delle persone dietro ID diversi).

## 6-quinquies · Terzo giro di problemi, e le risposte dell'utente (30/07/2026)

**1. Nessun campo diceva QUANDO il dato diventa noto — ✅ RISOLTO, ed è
diventata una regola del progetto.** Era il problema più serio: nella stessa
tabella convivono dati noti prima del fischio (arbitro, formazione, età,
esperienza) e dati che esistono solo dopo (minuti, gol, tocchi), e usare i
secondi per prevedere la partita che li ha prodotti è look-ahead — con la
sfumatura che rende l'errore invisibile: **il numero è giusto, è il momento a
essere sbagliato**. Su richiesta dell'utente ("sistemalo in questo file e in
tutto il resto del repo") è stato sistemato in **quattro punti**:
   - **`CLAUDE.md` §5-bis, nuova regola R8** — la sede autorevole: ogni
     colonna dichiara `pre`/`post`/`statico`, e una feature di backtest usa
     solo `pre` della partita in corso o `post` di partite **precedenti**;
   - **`docs/DATI.md`** — un riquadro in testa al catalogo che classifica le
     colonne degli **snapshot esistenti** (le quote sono `pre`, l'xG è `post`:
     nel DC entra sempre e solo come storia delle partite già giocate);
   - **`data/stagione_2026_2027/README.md` §3-bis** — dove il concetto era
     nato come «retrospettivo ≠ prospettico», ora rimanda alla regola generale;
   - **questo piano, §1.9** — una colonna ⏱️ per ognuno dei 35 dati-giocatore.
   Il caso che dimostra perché serviva: **capitano e ruolo effettivo sono
   `post` nel dato storico ma `pre` nella raccolta prospettica**, perché
   escono con la formazione ufficiale. La stessa informazione cambia
   categoria a seconda di come la ottieni.

**2. "Manca il ponte da giocatore a squadra" — ⚠️ obiezione RITIRATA, era
un'inquadratura sbagliata mia.** Avevo scritto che i dati-giocatore devono
"diventare un numero di squadra" perché il motore attuale lavora su λ e μ di
squadra. L'utente ha giustamente obiettato che **non è quello lo scopo**: i
dati si raccolgono per avere più informazione sui calciatori, punto — e l'uso
previsto è già stato descritto, ed è diverso: *nella settimana della partita
si hanno le probabili formazioni, quindi si sa chi gioca, e si usano insieme
i dati di squadra, dei giocatori, del meteo, dell'arbitro, dell'allenatore
per fare una previsione*. Questa è un'architettura legittima e **non**
richiede di collassare tutto in λ e μ. Resta vera solo la parte piccola
dell'osservazione, declassata da "problema" a **nota di progettazione**: nel
momento in cui si produrrà una previsione, un modo di combinare quelle
informazioni andrà scelto — ma è una decisione da prendere allora, con i dati
in mano, non un prerequisito per raccoglierli.

**3. Il controllo "completo" e la sua grana — ✅ RISTRUTTURATO in §6-bis.**
Domanda dell'utente: cercare le info sulla singola partita? diventa un
controllo "su internet"? Risposta emersa ragionandoci: il principio giusto è
"**ogni tabella verificata contro almeno una fonte indipendente
dichiarata**", scegliendo la migliore per quel fronte — e per due fronti la
fonte migliore **ce l'abbiamo già offline** (i nostri snapshot per
risultati/date/squadre, Understat per i minuti di stagione). Wikipedia resta
la fonte giusta per i mandati degli allenatori. Dettaglio e tabella in §6-bis,
inclusa la correzione onesta sulla grana: per i giocatori il censimento
completo è **per giocatore-stagione**, non per giocatore-partita (1.894.350
righe, e Wikipedia pubblica totali di stagione).

**4. Il repo git cresce per sempre — spiegato semplice.** Git non tiene solo
la versione attuale di un file: tiene **tutte** le versioni passate, per
sempre. Se mettiamo nel repo un file da 100 MB e ogni settimana lo
aggiorniamo, dopo un anno nel repo non ci sono 100 MB: ce ne sono ~5 GB
(52 copie), anche se guardando la cartella se ne vede una sola. E non si
possono cancellare senza riscrivere la storia. Il progetto ha già avuto un
episodio simile (un cron che committava ~51 MB in silenzio, Fase 92).
**Conseguenza pratica, da decidere quando si scriverà il codice**: o si
committa il dataset **una volta sola** (lo storico non cambia: le partite
del 2019 restano quelle) aggiornando solo la coda recente, oppure i grezzi
grossi restano fuori dal repo e si ri-scaricano. La decisione dell'utente
("teniamo tutti i dati, sempre accessibili") **non è in discussione**: è
compatibile con entrambe le soluzioni, riguarda solo *come* si versiona.

**5. Bias di selezione nelle medie "per 90 minuti" — chiarimento.** L'utente
ha chiesto di cosa parlassi: è un rischio d'**uso**, non di raccolta. Se un
domani si confrontano i giocatori con una media "per 90 minuti" (es. "gol
ogni 90'"), quella media è calcolata solo sulle partite in cui l'allenatore
lo ha schierato — e chi gioca poco spesso entra a partita già decisa, o
gioca quando è in condizione peggiore. Non è un motivo per non raccogliere
niente: è un promemoria per quando si faranno i confronti fra giocatori
(idea §4h). Nessuna azione richiesta ora.

**6. Troppe ipotesi insieme — ridimensionato dall'utente.** Avevo posto il
problema come "testare 29 feature produce falsi positivi per caso". L'utente
ha chiarito che **non si tratta di testare tutto**: si tratta di aggregare
dati che, messi insieme, danno un quadro più ricco della partita. L'obiezione
resta valida solo nel momento in cui si **valida** se una singola feature
migliora davvero le previsioni (lì servono IC e disciplina, come sempre nel
progetto), non nella fase di raccolta e di costruzione del quadro. Ridotto da
"problema" a **avvertenza per la fase di validazione**.

**7. Semantica di `minutes_played` e dei gol — ✅ VERIFICATO (30/07/2026),
tre risposte su tre.** Controllato scaricando il dataset ed elaborando le
1.894.350 righe di `appearances.csv` (cache ripulita a fine verifica):
   - **il recupero NON è incluso**: il valore 90 compare **990.536 volte** (è
     di gran lunga il più frequente) e significa "partita intera"; i valori
     sopra 90 sono **11.041** e arrivano fino a **148** — sono i tempi
     supplementari delle coppe, non il recupero;
   - **gli autogol NON contano come gol del giocatore**: su 4.955 casi
     risolvibili (giocatore con un autogol in quella partita, incrociando i
     6.729 eventi `Own-goal` di `game_events.csv` con `appearances.csv`),
     in **4.954** il campo `goals` esclude l'autogol — il 99,98%. È la
     semantica che ci aspettavamo, ed è quella giusta: un autogol non è un
     gol del marcatore. *(Il progetto si era già fatto male una volta con un
     autogol: la lezione R5 sull'xG a 0.00 con un gol segnato.)*;
   - **l'espulso ha i minuti TRONCATI al rosso**: su 14.472 espulsioni
     incrociabili, **12.835 (88,7%)** hanno `minutes_played` uguale al minuto
     del cartellino rosso (differenza mediana **0**); le 1.980 con 90 pieni
     sono rossi mostrati a fine gara o dopo il fischio. Il dato è quindi già
     corretto per il calcolo della fatica, senza aggiustamenti.
   **Un limite trovato per strada, da dichiarare**: `game_events.csv` copre
   **più** competizioni/anni di `appearances.csv` — solo 14.472 delle 19.638
   espulsioni (74%) e 4.955 dei 6.710 autogol hanno una riga corrispondente
   nelle presenze. Non è un errore, ma va tenuto presente quando si incrociano
   i due file: non tutti gli eventi hanno una presenza dietro.

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

## 8 · Idee catturate qui, in attesa di essere ricollocate (richiesta utente, 29/07/2026)

**Nota di metodo.** Ragionando sul database giocatori sono emerse quattro
idee **prospettiche** — non sull'uso dei dati storici, ma su come una
notizia saputa **durante la settimana** dovrebbe cambiare le
quote/previsioni della partita successiva. Nessuna di queste è davvero
"nuova": toccano tutte piste già esistenti altrove nel progetto. L'utente
ha chiesto di scriverle **qui per ora**, senza deciderne subito la sede
definitiva, e di **ricollocarle quando questo piano — che resta una bozza
di brainstorming — verrà smontato o superato da qualcosa di più
strutturato**. Stesso schema già usato per `cantiere_opta_flashscore/`: un
contenitore temporaneo che dichiara esplicitamente dove il contenuto dovrà
essere spostato, per non perdere idee valide solo perché non hanno ancora
una sede decisa.

1. **Un giocatore-chiave infortunato, saputo durante la settimana, dovrebbe
   cambiare le quote/previsioni della partita.** Non nuova in assoluto — è
   imparentata con la pista 10 di `PISTE.md` (formazioni ufficiali a T−1h,
   l'unica versione della pista che conta) e con §7.3 di `lavoro_aperto.md`
   ("notizie, probabili formazioni, motivazioni"), che pone già gli stessi
   paletti (solo raccolta prospettica, mai backtestabile sul passato, cieca
   alle quote). **Sede futura probabile**: pista 10 di `PISTE.md`, o §7.3 di
   `lavoro_aperto.md`.
2. **Un cambio di allenatore, saputo in corso di stagione, dovrebbe
   impattare subito la previsione.** Diversa dall'idea già in §4g di questo
   piano ("effetto nuovo allenatore", che è una correzione
   **retrospettiva** misurabile nei dati storici) — qui l'accento è
   sull'uso **prospettico** della notizia appena accade. **Sede futura
   probabile**: insieme all'idea 1 (§7.3 di `lavoro_aperto.md`), o come
   estensione di §4g quando si scriverà davvero.
3. **Un arbitro designato, saputo in anticipo, dovrebbe aggiornare le quote
   sul mercato cartellini.** Non nuova: è esattamente ciò che
   `data/stagione_2026_2027/README.md` §4-bis pianifica già (raccolta
   prospettica della designazione), e ciò che la Fase 125/126 ha già
   misurato in retrospettiva. **Sede futura**: nessuna nuova da creare — è
   già scritta in quel §4-bis, questa voce serve solo a non perderla di
   vista mentre si lavora su questo piano.
4. **Se piove, e sappiamo che con la pioggia ci sono meno gol, possiamo
   giocare Under 3.5.** Tocca la pista 13 (meteo) di `PISTE.md`, aperta da
   tempo ma **senza nemmeno un candidato di fonte verificato** — una delle
   poche piste del progetto in questo stato. L'ipotesi specifica — pioggia
   → meno gol — **non è mai stata misurata** in questo progetto: è un'idea
   da testare, non un fatto acquisito. **Sede futura probabile**: pista 13
   di `PISTE.md`.

**Nessuna di queste quattro idee è stata sviluppata oltre l'enunciato** —
sono promemoria da non perdere, non piani pronti da eseguire.

## 8-bis · Le quattro idee erano ESEMPI, non l'elenco — il principio generale (richiesta utente, 29/07/2026)

**Chiarimento dell'utente**: le quattro idee di §8 non erano una lista
chiusa, erano **esempi** di un principio più ampio — con tutti questi dati
incrociati (giocatori, arbitri, allenatori, e i dati di partita che il
progetto ha già) si potranno fare **molte più valutazioni di quelle
elencate finora**, su assi che vanno lavorati uno per volta, nel file,
mano a mano che si approfondiscono (non solo elencati e lasciati lì).

Gli assi che l'utente ha indicato esplicitamente, con lo stato attuale nel
piano:

- **Testa a testa (H2H)** — non è un fronte nuovo: esiste già come pista 1
  di `PISTE.md` ("scontri diretti, puntati su totali/GG"), 🟢 aperta ma
  **mai provata**, oggi pensata a livello **squadra**. L'angolo nuovo,
  emerso qui, è l'H2H a livello di **singolo giocatore** (voce 28 di
  §1.9) — un attaccante che segna sempre/mai contro una certa difesa, un
  centrocampista che soffre un certo avversario diretto — mai considerato
  né a livello squadra né a livello giocatore in questo progetto come
  fonte di dato STRUTTURATA (oggi la pista 1 è solo un'ipotesi, zero
  implementazione).
- **Partite delle squadre** — il cuore dei dati che il progetto ha già
  (snapshot di 5 leghe, 9 stagioni); non è un fronte nuovo, è la base su
  cui tutto il resto si innesta.
- **Infortuni dei giocatori, ricostruiti nello storico completo** —
  l'utente chiede esplicitamente di **risalire a tutti quelli passati**,
  non solo raccoglierli da qui in avanti (voce 22 di §1.9, ampliata):
  oggi il progetto ha solo una stima **aggregata per squadra** derivata
  dalle rose Understat (`transfermarkt.py`, Fase 4/pista vecchia) — mai
  un infortunio **individuale reale** con date di inizio/fine e tipo.
  Nessuna fonte nota oggi per uno storico così dettagliato: è ricerca, non
  raccolta, esattamente come il Tier B (§1.2).
- **Squalifiche dei giocatori** — attenzione a una distinzione già scritta
  altrove nel progetto ma da ribadire qui: `src/data/disciplina.py` **calcola**
  le squalifiche dalle regole (soglie di cartellini) e dal conteggio dei
  cartellini reali, non le **osserva**. Funziona bene come proiezione in
  avanti, ma non è mai stato verificato **retrospettivamente** se le
  squalifiche calcolate coincidano con quelle davvero scontate (casi come
  il rosso diretto, che scatta una squalifica di durata VARIABILE decisa
  dal giudice sportivo in base alla gravità — non dalle soglie di
  accumulo — sfuggono al modello a regole). Uno storico REALE delle
  squalifiche (voce 27 di §1.9) servirebbe sia come dato sia come
  **controllo indipendente** del calcolo esistente (stesso spirito del
  controllo Wikipedia, §6-bis, applicato a un altro modulo del progetto).
- **Livello di esperienza, non solo quantità** — l'esempio dell'utente ("3
  finali di Champions da titolare" vs "sempre in Serie B") è già stato
  sviluppato in dettaglio in §1.10 (`peso_competizione`, esperienza
  pesata, voce 26 di §1.9).
- **Età** — già coperta (§1.8, voce 11 di §1.9).
- **Caratteristiche di gioco, di squadra e del singolo** — di squadra è la
  "firma stilistica" dell'allenatore (idea c-bis, §4) e i dati event/Tier B
  di squadra già impliciti nello snapshot (xG, PPDA, deep); del singolo è
  il Tier B individuale (§1.2, voce 29 di §1.9) — entrambi dipendono dallo
  sblocco di una fonte oggi non nota.

**Come si lavora da qui**: uno alla volta, come già deciso per gli
arricchimenti di §1.8 (§6-ter problema 9) — non tutti insieme. L'ordine di
approfondimento non è ancora deciso, va scelto insieme all'utente.
