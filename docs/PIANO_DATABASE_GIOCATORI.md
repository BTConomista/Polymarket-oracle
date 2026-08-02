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

> 🔴 **LEGGERE PRIMA §9.** Il 30/07/2026 il dataset è stato verificato a fondo
> (14 agenti, sei fronti d'indagine e otto verifiche avversariali). Sono emerse
> **14 affermazioni sbagliate** in questo documento, dati nuovi mai nominati, e
> la classificazione finale raggiungibile/irraggiungibile. **§9 ha la precedenza
> su tutto ciò che viene prima**; le sezioni §1-§8 sono conservate come storia
> del ragionamento, con un richiamo dove sono state rettificate.
>
> 🔴🔴 **E PRIMA ANCORA, `docs/AUDIT_FONTI_GIOCATORI.md`** (31/07/2026, 13 agenti):
> ha auditato **tutte e 118 le voci** dei tre fronti (61 giocatore + 32 allenatore
> + 25 arbitro) con un giro di verifica avversariale sopra, e ha prodotto **7
> declassamenti** e **18 numeri rettificati** — inclusi **due look-ahead ATTIVI
> nel codice del repo** (`scripts/build_stagione_anagrafica.py`, righe 222 e 225).
> Bilancio: **36 VERIFICATE, 45 DERIVATE, 21 MANCANTI, 13 ASSUNTE, 3 CHIUSE per
> licenza**. Quel file ha la precedenza **anche su §9 e §10**, ed è riassunto qui
> in **§11**.

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
| §1.9 | **checklist completa dei 61 dati-giocatore**, con tier, rimandi e marcatura temporale ⏱️ |
| §1.10 | rendimento per livello avversario, indice forza club, esperienza pesata |
| §1.11 | **dati DERIVATI** — l'inventiva: ritmo dei gol, rimonte, coesione dell'undici... |
| §1.12 | **terzo giro di idee fronte per fronte**: 14 nuove per i giocatori, 13 per gli allenatori, 11 per gli arbitri (+ 2 interazioni scartate) |
| §2 | bozza di schema (tabelle, chiavi, come agganciare i nomi) |
| §3 | come dividere il lavoro fra più agenti |
| §4 | idee d'uso (NON decise) — a, b, c, c-bis, c-ter, d, e, f, g, h |
| §5 | rischi e limiti dichiarati onestamente |
| §6 | primi passi concreti, in ordine (nessuno ancora eseguito) |
| §6-bis | controllo con **fonte indipendente** — ✅ **già ESEGUITO** sul livello-partita: 16.111 partite, 99,99% identiche, le 2 divergenze sono partite a tavolino |
| §6-ter | **10 problemi trovati** rileggendo il piano in modo avversariale, con le correzioni |
| §6-quater | decisioni operative prese e domande ancora aperte, prima di partire |
| §6-quinquies | **terzo giro di problemi** e risposte: regola R8 (⏱️), obiezione ritirata sul "ponte", 3 verifiche tecniche |
| §7 | collegamenti ad altri file del repo |
| §8 | 4 idee prospettiche catturate, da ricollocare quando il piano verrà smontato |
| §8-bis | quelle 4 erano ESEMPI — il principio generale (H2H, infortuni, squalifiche...) |
| **§9** | 🔴 **VERIFICA COMPLETA (30/07/2026)** — 14 affermazioni sbagliate, dati nuovi, classificazione delle fonti **dentro** il CSV |
| **§10** | 🌍 **OLTRE IL CSV (30/07/2026)** — fonti esterne, verifica incrociata, **indice di forza costruito in casa**. Insieme a §9 ha la precedenza su tutto |
| **§11** | 🔴🔴 **AUDIT DELLE 118 VOCI (31/07/2026)** — sintesi; il verbale integrale è in `docs/AUDIT_FONTI_GIOCATORI.md`, che ha la precedenza su §9 e §10 |
| **§13** | 🏗️ **DATABASE CARRIERE — disegno a strati (31/07/2026)**: strato 1 COSTRUITO (`src/data/careers.py`), strato 2 (Wikipedia) fermo su una decisione di licenza |
| **§12** | ⭐ **IL TIER B È ENTRATO (31/07/2026)** — 97 statistiche per giocatore-partita, Serie A 2025-26, in `files/diretta_serie_a_2526/`. Ribalta §1.2 e §10.5 **per una lega e una stagione** |

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
| `game_events.csv` | 150 MB | ⚠️ *§9.1 n.11: `minute` usa −1 come segnaposto, e i minuti sono troncati a 45/90 (§9.7). Il campo `description` è STRUTTURATO: vedi §9.4* — eventi **con il minuto**: `type` ∈ {Substitutions (631k), Cards (382k), Goals (248k), Shootout}, con `player_id`/`player_in_id`/`player_assist_id` — qui vive il minuto esatto di ogni cambio, gol, assist, cartellino | ⬜ non importato |
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

> 🔴 **SUPERATA il 31/07/2026 — vedi `docs/CACCIA_EVENT_DATA.md`** (10 agenti,
> ricerca su richiesta dell'utente «troviamo un modo per ottenerli»). Tre cose che
> cambiano questa tabella:
> 1. **diretta.it/Flashscore va spostata nel gruppo «chiuse per LICENZA»**, non per
>    vincolo tecnico. Il `robots.txt` **non ci vieta nulla** (0 righe contrarie), ma
>    i ToS Livesport vietano lo **scraping per nome** (cl. 2.10), rivendicano il
>    **sui generis** (cl. 2.9), limitano all'**uso personale** (cl. 2.2) e valgono
>    anche per i **non registrati** (cl. 1.2). Il dato è dichiaratamente **di Opta**.
>    ⚠️ La vecchia motivazione («l'ambiente non raggiunge un browser in HTTPS») era
>    **tecnicamente superata** — Chromium+Playwright funziona — ed è proprio il tipo
>    di motivazione sbagliata che fa riaprire una pista chiusa. **La condizione di
>    riapertura non è "un browser vero": è un accordo scritto con Livesport.**
> 2. **Nemmeno avrebbe dato event data**: 46 campi per giocatore ma **zero
>    coordinate x,y**, e l'archivio per-giocatore comincia **dentro la 2024-25**
>    (fra il 9 marzo e il 23 aprile 2025) → **12,7-14,7%** delle 16.111 partite, e
>    **niente** sul 65,8% (2017-18 → 2023-24).
> 3. **La via che invece esiste**: **Wyscout/Pappalardo** su figshare, **CC BY 4.0
>    verificata all'endpoint API**, titolare che rilascia in proprio — **1.826
>    partite = 11,33%**, ma è **una stagione al 100% su tutte e 5 le leghe**, con il
>    log azione-per-azione completo (coordinate comprese) da cui si derivano
>    **tutti** i conteggi di questa sezione. 77,3 MB, 0 €.
>
> Ecosistema aperto ricontato agli endpoint: **2.022/16.111 = 12,55%**, **+0
> partite** rispetto a tre ricerche fa. Per superare la soglia di rilevanza del 20%
> servirebbe **raddoppiare l'intero ecosistema aperto mondiale**.

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

**Nazionali — più debole del previsto** ❌ *(RETTIFICATO §9.1 n.4: `coach_name` è
vuota al 100%, non «solo l'attuale»; e §9.9: il fronte nazionali è chiuso da
questa fonte)*: `national_teams.csv`
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
- ~~**`aggregate` + `round`**~~ — ❌ **RETTIFICATO (§9.1 n.1): `aggregate` è la
  copia letterale del risultato, in 88.958 righe su 88.958. Resta valido solo
  `round`.** Il testo originale diceva: risultato aggregato e turno della
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
| 12 | esperienza (presenze/minuti cumulati) | A, derivata — ⚠️ **NON** «anche fuori le 5 leghe»: `appearances` ha zero righe per Brasile/Argentina/MLS/ecc. e nessuna seconda divisione; il 32,6% dei debuttanti ≥26 anni risulta senza passato (§9.1 n.2) | **`pre`** | §1.8, §9.1 |
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
| 23 | ~~peso~~, **altezza** | ✅ `height_in_cm` c'è (98,66%); ❌ il **peso non esiste** in nessuno dei 12 file (§9.1 n.12) | `statico` | §9.4 |
| 24 | rendimento per livello avversario (più forte/pari/più debole) | nuovo asse, richiede l'indice di forza (§1.10) | **`pre`** | §1.10 |
| 25 | squadre passate in carriera, con un indice di forza 0-1 ciascuna | nuovo, richiede l'indice di forza (§1.10) | **`pre`** | §1.10 |
| 26 | **esperienza PESATA per livello di competizione** (una finale di Champions da titolare ≠ un girone minore) | nuovo, richiede `peso_competizione` (§1.10) | **`pre`** | §1.10 |
| 27 | squalifiche REALI (storico di quelle scontate davvero, non solo calcolate dalle regole) | scoperto — oggi solo calcolate da `disciplina.py` sui cartellini, mai verificate contro un dato reale | **`pre`** | nuovo qui, ampliato §8-bis |
| 28 | testa a testa (H2H) a livello di **singolo giocatore**, non solo di squadra | nuovo asse | **`pre`** | nuovo qui, ampliato §8-bis |
| 29 | caratteristiche di gioco individuali, oltre i conteggi grezzi (es. "recupera molto e riparte veloce" invece del solo numero di recuperi) | C — dipende interamente dallo sblocco del Tier B, nessuna fonte nota nemmeno per i conteggi grezzi | `post` → tendenza `pre` | nuovo qui |
| 30 | **minuti giocati in inferiorità/superiorità numerica** (dal minuto del rosso) | A — ⚠️ **NON** `red_cards` di `appearances.csv`, che ignora i 9.741 secondi gialli (§9.1 n.6): usare gli eventi `Cards` | `post` | §1.11, §9.7 |
| 31 | **ruolo giocato ≠ ruolo naturale** (schieramento d'emergenza) | A — `players.csv` vs `game_lineups.csv` | `post` (⚠️ `pre` con la formazione ufficiale) | §1.11 |
| 32 | **già ammonito, e da che minuto** (comportamento nel resto della partita) | A — minuto del giallo in `game_events.csv` | `post` | §1.11 |
| 33 | situazione contrattuale (scadenza) e giorni dall'arrivo al club | A — ✅ `contract_expiration_date` è in **`players.csv`**, non in `transfers.csv` (§9.1 n.8) | **`pre`** | §1.11, §9.4 |
| 34 | prestito, e prestito **dalla squadra che si affronta** | ❌ **non servibile**: `transfers.csv` non ha un flag prestito e copre l'8,7% dei giocatori (§9.1 n.8) | **`pre`** | §1.11 |
| 35 | numero di maglia (proxy grezza dello status in rosa) | A — già in `game_lineups.csv` | **`pre`** | §1.11 |
| 36 | rientro da infortunio, con la **curva di reinserimento** (20′ → 45′ → 70′) | dipende dagli infortuni (scoperto) + minuti | **`pre`** | §1.12 |
| 37 | **sensibilità individuale al riposo** (chi crolla sotto i 4 giorni e chi no) | A, derivata | **`pre`** | §1.12 |
| 38 | partite in N giorni (non solo minuti totali) | A, derivata | **`pre`** | §1.12 |
| 39 | usura di carriera / "età calcistica" (minuti cumulati vs età) | A, derivata | **`pre`** | §1.12 |
| 40 | fuso orario del viaggio in nazionale | dipende dalle convocazioni (scoperto) | **`pre`** | §1.12 |
| 41 | piede rispetto al lato di impiego (ala invertita) | A da verificare (piede in `players.csv`) | `statico` + `post` (`pre` con formazione) | §1.12 |
| 42 | **probabilità di partire titolare** (dallo storico recente) | A, derivata | **`pre`** | §1.12 |
| 43 | gerarchie dei rigori/punizioni (2ª e 3ª scelta) | B, derivata | **`pre`** | §1.12 |
| 44 | rendimento casa/trasferta del **singolo giocatore** | A, derivata | **`pre`** | §1.12 |
| 45 | "mai sostituito": partite consecutive giocate per intero | A, derivata | **`pre`** | §1.12 |
| 46 | primo anno in un **campionato nuovo** (distinto dai giorni dall'arrivo) | ⚠️ indebolita: `transfers.csv` copre l'8,7%, e `appearances` non ha i campionati extra-europei (§9.1 n.2/n.8) | **`pre`** | §1.12 |
| 47 | **gol decisivi vs ininfluenti** (l'1-0 e il 4-0 non sono uguali) | A, derivata dal punteggio minuto per minuto | `post` | §1.12 |
| 48 | disciplina fine: falli/cartellini, e cartellini nelle partite tese | B (falli individuali) | `post` → tendenza `pre` | §1.12 |
| 49 | **giocatore × allenatore**: minuti sotto un certo allenatore | A, derivata (incrocio con `manager_spells`) | **`pre`** | §1.12 |
| 50 | **valore di mercato nel tempo** (serie storica datata) | A — `player_valuations.csv`, **già nel repo**, 154.022 valutazioni | **`pre`** | §9.4 |
| 51 | **distanza dal picco di carriera** (`highest_market_value_in_eur`, 93%) | A — `players.csv` | **`pre`** | §9.4 |
| 52 | presenze e gol in **nazionale** (`international_caps`/`international_goals`) | A — `players.csv`, **già letto dal repo** | **`pre`** | §9.4, §9.5 |
| 53 | **posizione in classifica** delle due squadre (`club_position`, 100% piena) | A — `games.csv`; è la classifica **DOPO** la giornata, quindi si usa **ritardata** | `post` → ritardata **`pre`** | §9.4 |
| 54 | **campo di casa temporaneo** (lo `stadium` cambia dentro la stessa squadra) | A — `games.csv`; si aggancia alla Fase 123 | **`pre`** | §9.4 |
| 55 | contesto-club: `squad_size`, `average_age`, `foreigners_percentage`, `national_team_players`, `stadium_seats`, `net_transfer_record` | A — `clubs.csv`, **già nel repo** | **`pre`** | §9.4 |
| 56 | **`sub_position`** (ruolo di dettaglio) oltre a `position` | A — `players.csv`, **già letto dal repo** | `statico` | §9.4, §9.5 |
| 57 | **rigori segnati** (4.061), **autogol** (1.333), **parte del corpo** del gol, **tipo di assist** (2.323 da corner) | A — dal campo `description` di `game_events.csv` | `post` | §9.4 |
| 58 | **motivo del cartellino** (17 etichette nel perimetro) e **rosso diretto vs doppia ammonizione** | A — `description`; ⚠️ copertura **per lega × stagione**, vedi §9.6 | `post` | §9.4, §9.6 |
| 59 | **sostituzione per INFORTUNIO** (10.558 nelle 5 leghe) | A — `description`; ⚠️ tasso per partita **+56%** nel tempo (§9.6) | `post` | §9.4, §9.6 |
| 60 | **orario di inizio** della partita | ✅ **RISOLTO** — openfootball (100%) o la colonna `Time` di football-data, **già in repo** (77,3%) | **`pre`** | §9.8 |
| 61 | **meteo** della partita | ✅ **RISOLTO** — open-meteo archive API, CC BY 4.0, senza chiave | **`pre`** | §9.8 |

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
- ❌ **`clubs.csv` — RETTIFICATO (§9.1 n.3 e n.14): `total_market_value` è VUOTA
  al 100%, e il file era GIÀ nel repo. Il rimpiazzo è `player_valuations.csv`
  (§9.4).** Testo originale: (upstream `davidcariboo/player-scores`, **non ancora
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

> 🔗 **Collegamento (30/07/2026)**: la pista 23 di `PISTE.md` propone di dare
> un numero vero a questo `peso_competizione`, misurando quanto cambia il
> rendimento di un giocatore passando di categoria (l'esempio dell'utente: un
> attaccante da 25 gol in Serie B, promosso, quanti ne fa in Serie A?). Oggi
> manca ancora la fonte per il rendimento individuale in seconda serie — vedi
> quella pista prima di partire da zero qui.

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
- ~~**derby / rivalità**~~ — ❌ **VERIFICATO E CHIUSO (§9.1 n.13): `clubs.csv` non
  ha nessun campo città.** Serve un'altra fonte;
- ~~**orario di inizio**~~ — ❌ **verificato il 30/07/2026: NON disponibile.**
  Il campo `date` di `games.csv` contiene solo `AAAA-MM-GG`, senza ora. Una
  partita delle 12:30 non è come una delle 20:45, ma per saperlo servirebbe
  un'altra fonte (§6-quinquies punto 7-bis).

**Due avvertenze oneste, valide per tutta la sezione.** (1) Diverse di
queste idee sono cugine di cose **già bocciate a livello squadra** (la
covariata `stakes`, la forma, il valore rosa: `docs/PANCHINA.md`): il fatto
che siano nuove *a livello giocatore* non garantisce che funzionino. (2)
Sono tutte **derivate**, quindi ereditano la marcatura temporale della
fonte (R8): una tendenza calcolata sulle partite passate è `pre` ed è
utilizzabile; la stessa quantità misurata **sulla partita in corso** è
`post` e non lo è.

### 1.12 · Terzo giro di idee, fronte per fronte (30/07/2026)

Brainstorming dedicato: cosa manca ancora per **giocatori**, **allenatori** e
**arbitri**, oltre a tutto ciò che è già nelle sezioni precedenti. Vale il
principio di §1.9 (non si filtra per utilità immediata finché il costo è
~zero) e la marcatura temporale della regola R8.

#### Giocatori (righe 36-49 della checklist §1.9)

*Fisico e condizione*
- **rientro da infortunio con la curva di reinserimento** — non "è stato
  infortunato" ma *a che punto è*: prima gara 20′, poi 45′, poi 70′. Un
  giocatore alla terza gara dal rientro è un altro giocatore rispetto alla
  prima;
- **sensibilità individuale al riposo** — alcuni crollano sotto i 4 giorni di
  recupero, altri no. ⚠️ Da non confondere con le feature di riposo di
  squadra, **già bocciate** (`rest_full`, `midweek_europe`,
  `docs/PANCHINA.md`): lì si misurava un effetto medio uguale per tutti, qui
  è l'**eterogeneità fra giocatori**. È un'ipotesi diversa, non la stessa
  ripresentata;
- **partite in N giorni**, non solo minuti totali: "3 partite in 8 giorni"
  pesa diversamente da "270 minuti" distribuiti;
- **usura di carriera** ("età calcistica"): un 28enne con 500 partite nelle
  gambe non è un 28enne con 200 — si deriva dai minuti cumulati (§1.8);
- **fuso orario del viaggio in nazionale** — un sudamericano che vola in
  Argentina e torna perde ~24 ore di volo, un europeo due. Oggi tutte le
  convocazioni peserebbero uguale.

*Ruolo e contesto*
- **piede rispetto al lato** — un mancino sulla fascia destra (ala invertita)
  fa un altro mestiere. Il piede dovrebbe essere in `players.csv` (**da
  verificare**, come altezza e peso);
- **probabilità di partire titolare**, stimata dallo storico recente: serve
  esattamente al caso d'uso descritto dall'utente (le probabili formazioni
  nella settimana della partita);
- **gerarchie dei rigori e delle punizioni** — chi tira quando il rigorista
  designato non è in campo (seconda e terza scelta);
- **casa/trasferta per singolo giocatore** — il fattore campo di squadra è
  noto, quello individuale non è mai stato guardato;
- **mai sostituito**: partite consecutive giocate per intero, proxy della
  fiducia dell'allenatore;
- **cambio di campionato**: il primo anno in un campionato nuovo
  (Brasile→Serie A) è diverso da un trasferimento interno — distinto dai
  "giorni dall'arrivo" già in lista (§1.9 riga 33).

*Peso degli eventi*
- **gol decisivi vs ininfluenti** — l'1-0, il pareggio al 90′ e il quarto gol
  a partita chiusa oggi contano uguale. Si lega direttamente al bias di
  selezione (§6-quinquies punto 5): è lo stesso problema visto dal lato
  dell'evento invece che dal lato dei minuti;
- **disciplina fine**: rapporto falli commessi / cartellini ricevuti (chi fa
  molti falli e prende pochi gialli), e cartellini nelle partite ad alta
  tensione.

*Una interazione, l'unica tenuta*
- **giocatore × allenatore** — quanti minuti gioca un certo giocatore sotto
  un certo allenatore. È l'unica delle tre interazioni proposte che l'utente
  ha ritenuto utile, e il motivo è pratico: quando cambia la panchina serve
  a **prevedere chi giocherà**, che è il caso d'uso centrale del progetto.

> ❌ **Due interazioni proposte e SCARTATE dall'utente (30/07/2026)**:
> *giocatore × arbitro* (cartellini presi da quello specifico arbitro) e
> *allenatore × arbitro*. Giudicate poco utili. Scritte qui per la regola
> §1.4 — anche le idee scartate si registrano, altrimenti la sessione dopo
> le ripropone.

#### Allenatori (si aggiungono a §1.6)

*Come schiera*
- **modulo preferito e quanto lo cambia** — `home/away_club_formation` è già
  in `games.csv`, mai sfruttato;
- **reattività**: cambia modulo dopo una sconfitta? dopo quante?
- **uso della rosa**: quanti giocatori diversi impiega, età media dell'undici,
  minuti concessi agli under-21 ("lancia i giovani");
- **turnover per competizione**: chi stravolge la formazione in coppa e chi
  no — utile per prevedere le formazioni;
- **uso delle sostituzioni**: quante ne fa, quando fa la quinta. ⚠️ **Cambio
  di regime nei dati**: le sostituzioni sono passate da 3 a 5 nel 2020 —
  qualunque media che attraversi quella data mescola due mondi diversi. Da
  trattare come il progetto tratta già l'era porte-chiuse.

*Come rende*
- **curva del mandato**: primo anno vs terzo anno — diverso dal "rimbalzo del
  nuovo allenatore" (§4g), che riguarda le prime settimane;
- **rendimento per livello avversario**: chi fa bene con le grandi e male con
  le piccole, e viceversa (usa l'indice di forza di §1.10);
- **testa a testa fra allenatori**: il record di uno specifico allenatore
  contro un altro;
- **gestione del risultato**: quando è in vantaggio si chiude o continua ad
  attaccare? Misurabile dal punteggio minuto per minuto (§1.11);
- **reazione dopo una sconfitta pesante**;
- **disciplina della squadra sotto di lui** (cartellini per partita) — è il
  fronte-allenatore con l'aggancio più diretto a un mercato dove il progetto
  ha già risultati veri (Fasi 125/126).

*Contesto*
- **come è finito il mandato** (esonero o dimissioni), e soprattutto: le
  ultime 3-4 partite prima di un esonero sono sistematicamente peggiori? È
  una domanda che si può guardare all'indietro sui dati storici;
- **primo anno in *quel* campionato**, distinto dall'esperienza globale
  (§1.8).

#### Arbitri (si aggiungono a §1.5)

*Oltre i cartellini — che è tutto ciò che il progetto misura oggi*
- **rigori assegnati per partita** — il dato più interessante che manca:
  tocca direttamente i **gol**, non solo il mercato cartellini;
- **falli fischiati per partita** — l'asse "lascia correre" vs "fischia
  tutto", che cambia il ritmo della partita;
- **recupero concesso** — quanto tempo aggiunge: rilevante per i gol nel
  finale e per gli Over;
- **rossi diretti vs doppie ammonizioni** — profilo di severità, non solo il
  conteggio;
- **uso del VAR**: quante volte va al monitor, quante volte ribalta.

*Chi è e dove arbitra*
- **squadra arbitrale completa** — assistenti, quarto uomo e soprattutto
  l'**arbitro VAR**, che ha una propria propensione a intervenire
  (`data/stagione_2026_2027/README.md` §4-bis annota già che "costano zero
  raccolti insieme");
- **esperienza nella competizione specifica**, non solo globale: la prima
  partita di Champions di un arbitro;
- **quanto spesso gli affidano i big match** — proxy del suo ranking interno;
- **nazionalità dell'arbitro rispetto a quella delle squadre** — nelle coppe
  europee, se lo stile del suo campionato si trasferisce (è misurabile);
- **arbitro × squadra**: i precedenti con un club specifico;
- **coerenza, non solo media** — un arbitro prevedibile vale diversamente da
  uno che oscilla molto. Oggi la Fase 125 stima solo la media.

**Nota di realismo su tutto il blocco arbitri**: quasi nulla di questo sta in
`games.csv`, che dà **solo il nome** dell'arbitro. Rigori, falli, recupero,
VAR e squadra arbitrale richiedono una fonte che oggi **non abbiamo** —
alcuni (rigori, falli) sono già nei nostri snapshot a livello di squadra e si
possono aggregare per arbitro, il resto è Tier B o raccolta prospettica.

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

### ✅ Il controllo è stato ESEGUITO sul livello-partita (30/07/2026) — e funziona

Non è più una proposta: la parte offline del controllo **è stata fatta**, e
il risultato è il pezzo di lavoro più solido di questo piano. Incrociate
tutte e **16.111** le partite dei nostri snapshot con `games.csv`, per
`(data, squadra di casa, squadra ospite)`, canonicalizzando i nomi
Transfermarkt con `sources.canonical_team` — **senza scrivere un solo alias
nuovo**: i 234 `TEAM_ALIASES` già nel progetto bastano.

| lega | nostre partite | agganciate | gol identici | gol diversi |
|---|--:|--:|--:|--:|
| Serie A | 3.420 | 3.420 | 3.419 | **1** |
| Premier League | 3.420 | 3.420 | 3.420 | 0 |
| La Liga | 3.420 | 3.418 (+2 a ±1 giorno) | 3.420 | 0 |
| Bundesliga | 2.754 | 2.754 | 2.753 | **1** |
| Ligue 1 | 3.097 | 3.093 (+4 a ±1 giorno) | 3.097 | 0 |
| **totale** | **16.111** | **16.111** (100%, con tolleranza ±1 giorno) | **16.109** | **2** |

Le **6 partite non agganciate** al primo colpo sono tutte a **±1 giorno** di
distanza (fuso orario / posticipo serale che scavalca la mezzanotte) e hanno
**gol identici**: non sono discrepanze, sono un dettaglio di allineamento
delle date da gestire con una tolleranza di un giorno.

**Le 2 differenze vere sono la dimostrazione che il controllo serve — ed
entrambe sono partite assegnate dal giudice sportivo:**

1. **Union Berlin-Bochum, 14/12/2024** — noi 1-1, Transfermarkt 0-2. È il
   caso **già documentato**: la regola R1 del `CLAUDE.md` lo cita per nome, e
   `data/correzioni_dichiarate.csv` contiene le tre righe della correzione
   applicata il 24/07/2026. Il controllo ha **ritrovato da solo** l'unica
   anomalia che già conoscevamo — la miglior prova possibile che il metodo
   funziona e non produce rumore;
2. **Verona-Roma, 19/09/2020** — noi 0-0, Transfermarkt 3-0. **Trovata
   nuova**: stesso identico schema (0-0 sul campo, 3-0 assegnato a tavolino
   per la posizione irregolare di un giocatore in distinta). Il nostro dato è
   **già corretto** secondo R1 — non c'è niente da correggere — ma va
   **dichiarato** per la regola R4 («un'anomalia si dichiara anche quando NON
   è un errore»), altrimenti la prossima sessione che confronta con
   Transfermarkt vede 3-0 contro il nostro 0-0 e ci "corregge" al contrario.
   Registrata in `docs/DATI.md` §1-quater.

**Cosa dimostra, in pratica:**

- il livello-partita è verificato al **99,99%** contro una fonte
  indipendente, **senza rete, senza Wikipedia, in pochi secondi** e in modo
  perfettamente riproducibile;
- il tasso di falsi allarmi è **zero**: le uniche due divergenze su 16.111
  sono reali, spiegabili e della stessa famiglia;
- quando `games.csv` verrà importato, questo confronto diventa un **test
  automatico** permanente (§6-quater punto 5), non un controllo una tantum;
- resta da fare la parte che questa verifica non copre: **arbitri e
  allenatori** (colonne che i nostri snapshot non hanno — lì servono
  Wikipedia e i siti delle leghe) e i **minuti per giocatore-stagione**
  (contro Understat, anch'esso già offline).

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

> 📏 **MISURATO il 30/07/2026** (vedi anche §6-quinquies punto 4). I numeri
> veri, invece delle stime a occhio:
>
> | file | grezzo | compresso (gzip) |
> |---|--:|--:|
> | `game_lineups.csv` | 336,0 MB | **114,2 MB** |
> | `game_events.csv` | 149,6 MB | 42,4 MB |
> | `appearances.csv` | 142,2 MB | 41,0 MB *(già nel repo)* |
> | `player_valuations.csv` | 23,5 MB | 5,4 MB *(già nel repo)* |
> | `games.csv` | 23,8 MB | 4,5 MB |
> | `players.csv` | 16,3 MB | 3,9 MB *(già nel repo)* |
> | `club_games.csv` | 10,5 MB | 1,8 MB |
> | `transfers.csv` | 2,8 MB | 1,0 MB |
> | altri (clubs, competitions…) | 0,1 MB | ~0 MB |
> | **totale** | **705,2 MB** | **214,6 MB** |
>
> Per capire la scala: **l'intero repo oggi pesa 66,3 MB** (`git
> count-objects`), e `appearances.csv.gz` da solo — già dentro — ne è il
> **63%**. Aggiungere tutto il resto porterebbe il repo a **~280 MB**, oltre
> **4 volte** l'attuale, in un solo commit. Il file più pesante è
> `game_lineups.csv` (114 MB gz), da solo più della metà del totale nuovo.
>
> **Buona notizia**: la storia di git è ancora pulita — `appearances.csv.gz`
> ha **un solo blob** in tutta la storia del repo (verificato), segno che il
> gzip deterministico (`mtime=0`) del workflow di import funziona: a
> contenuto identico non crea una versione nuova. Il problema quindi **non è
> già avvenuto**, è tutto davanti a noi.
>
> **La soluzione proposta (da decidere quando si scriverà il codice)**: la
> gran parte di questi dati è **storia immutabile** — le presenze del 2019
> non cambieranno mai più. Quindi **partizionare per stagione**: le stagioni
> chiuse si committano **una volta sola** e git le conserva in una copia
> sola per sempre; solo il file della **stagione in corso** cambia. Quella
> vale circa un nono del totale, e la sua quota di righe nuove ogni
> settimana è dell'ordine di **1-3 MB**, non 214. Senza partizionamento,
> ri-committare tutto ogni settimana costerebbe ~214 MB × 52 = **oltre 10 GB
> l'anno** di storia git irrecuperabile.

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

**5. Bias di selezione nelle medie "per 90 minuti" — chiarito, e con quattro
rimedi concreti.** L'utente ha chiesto di cosa parlassi: è un rischio
d'**uso**, non di raccolta. Il problema in una riga: se si confrontano i
giocatori con una media "per 90 minuti" (gol ogni 90′, tocchi ogni 90′),
quella media viene **solo dalle partite in cui l'allenatore lo ha
schierato** — e i minuti di una riserva non sono i minuti di un titolare.
Chi gioca poco entra spesso **a partita già decisa** (dove tutti segnano di
più e si difende di meno), o contro avversari più deboli in coppa, o quando
non è al meglio. Due giocatori con "0,4 gol ogni 90′" possono aver fatto
cose completamente diverse.

Non è un motivo per non raccogliere: è un motivo per **raccogliere il
contesto dei minuti insieme ai minuti** — e la buona notizia è che il piano
lo prevede già quasi tutto. I rimedi, in ordine di forza:

  a. **normalizzare per il contesto**, non solo per i minuti: livello
     dell'avversario (§1.10), peso della competizione (§1.10), stato del
     punteggio (§1.11). Sono già in progetto per altri motivi, e servono
     esattamente a questo;
  b. **segmentare invece di aggregare**: la resa da titolare e quella da
     subentrato sono due numeri diversi, non uno solo — idem per fascia di
     avversario;
  c. **minuti in punteggio equilibrato**: dal punteggio minuto per minuto
     (§1.11) si può contare quanti minuti un giocatore ha giocato con la
     partita ancora in bilico, e calcolare le medie **solo su quelli**.
     Questo rimedio ha un valore particolare per il progetto: la Fase 93 ha
     misurato che il divario col mercato si concentra **proprio sulle
     partite equilibrate** — quindi la versione "depurata" della statistica
     è anche quella puntata dove il bersaglio è più grande;
  d. **shrinkage verso la media** per chi ha pochi minuti, esattamente come
     il progetto fa già altrove (K=40 sul fattore-arbitro nella Fase 125,
     shrinkage 1.5 nel Dixon-Coles): un attaccante con 90 minuti totali e un
     gol non "segna ogni 90′".

  **Un quinto pezzo, che nessun rimedio risolve e va solo dichiarato**: un
  giocatore infortunato **non compare affatto** nelle presenze. La sua
  assenza è informativa (§1.9 voce 22) ma è invisibile in qualunque media
  per-90: le medie descrivono chi c'era, mai chi mancava.

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

**7-bis. Altri quattro controlli di semantica, fatti nello stesso giro
(30/07/2026).** Tre rassicuranti e **uno serio**:
   - ✅ **i rigori della lotteria finale NON contano come gol**: verificato
     nel modo decisivo, cioè confrontando la somma dei gol di
     `appearances.csv` con il risultato ufficiale nelle 407 partite andate
     ai rigori — **zero** casi in cui la somma è maggiore. *(Un primo test
     più grossolano sembrava dire il contrario: era un falso allarme, e
     l'ho corretto invece di lasciarlo scritto.)*;
   - ✅ **nessuna riga duplicata**: 0 coppie (partita, giocatore) ripetute su
     1.894.350 righe. La chiave è pulita;
   - ✅ **`minutes_played` = 0 è un caso trascurabile**: 3 righe su 1.894.350;
   - ❌ **il campo `date` di `games.csv` NON contiene l'ora** (solo
     `AAAA-MM-GG`). Conseguenza diretta: l'idea "orario di inizio" di §1.11
     **non è realizzabile con questa fonte** — servirebbe un'altra fonte.
     Depennata, non lasciata come speranza.

**7-ter. ⚠️ TROVATA UNA TRAPPOLA VERA: nelle partite decise ai rigori, i gol
di `games.csv` sono inutilizzabili.** È il caso da manuale della regola
**R6** («il buco peggiore non è il NaN: è il finto pieno») — il numero
sembra un risultato e non lo è:

| partita | `games.csv` dice | ma il risultato vero era |
|---|:--:|---|
| Paraguay-Giappone, Mondiale 2010 | **5-3** | 0-0, poi 5-3 **ai rigori** |
| Inghilterra-Italia, Europeo 2012 | **2-4** | 0-0, poi 2-4 **ai rigori** |
| Chemnitzer-Mainz, DFB-Pokal 2014 | **10-9** | 5-5 dopo i supplementari, poi 5-4 ai rigori (**somma dei due**) |

❌ *RETTIFICATO (§9.1 n.5): sono **1.292** partite e **786**, non 407/394.*
Nelle 407 partite ai rigori, in **394** la somma dei gol dei giocatori è
*inferiore* al "risultato" di `games.csv`: la differenza sono i tiri dagli
undici metri. Il campo mescola quindi tre semantiche diverse (risultato
dei tempi regolamentari, punteggio dei rigori, o la loro somma) senza
dichiararlo.

**Impatto e rimedio.** Le **5 leghe non sono toccate** — in campionato non
esistono i rigori finali, e infatti l'incrocio di §6-bis dà 16.109 risultati
identici su 16.111. Ma il piano vuole estendersi proprio a
**Champions/Europa/Conference** (dove i turni a eliminazione vanno ai
rigori) e alle **nazionali** (dove i tornei finali ne sono pieni): lì il
dato è **silenziosamente sbagliato**. Rimedio proposto: individuare le
partite con eventi `Shootout` in `game_events.csv` e, per quelle,
**ricostruire il risultato dai soli eventi-gol** invece di leggere
`home/away_club_goals` — oppure marcarle e trattarle a parte. Da fare
**prima** di qualunque analisi che includa le coppe, non dopo.

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

---

# 9 · ⭐ VERIFICA COMPLETA DEL DATASET (30/07/2026) — la sezione che rettifica tutte le precedenti

> **Come è stata fatta.** Sei fronti d'indagine in parallelo sul dataset scaricato
> (poi cancellato: nulla è entrato nel repo), più otto verifiche **avversariali**
> incaricate di *refutare* le scoperte più importanti. In totale 14 agenti,
> ~1,5 milioni di token, 89 minuti. Tre refutazioni sono andate a segno — non sui
> numeri, che si sono riprodotti tutti alla cifra, ma sulle **interpretazioni**
> (§9.6). È esattamente il caso previsto dalla regola R7 del `CLAUDE.md`: il
> difetto non era il numero, era la statistica scelta per raccontarlo.
>
> **Questa sezione ha la precedenza su tutte le precedenti.** Dove §1.x o §6.x
> dicono altro, vale quanto scritto qui.

## 9.1 · Le 14 affermazioni SBAGLIATE trovate nel piano

L'audit ha verificato una per una tutte le affermazioni numeriche del documento.
**Il nucleo regge** (§9.2), ma quattordici affermazioni erano sbagliate o
fuorvianti, e **tre demoliscono ipotesi su cui il piano costruiva interi
paragrafi**:

| # | dove | cosa dicevamo | cosa è vero |
|---|---|---|---|
| 1 | §1.8 | «`aggregate` dà il contesto andata/ritorno nelle coppe» | ❌ `aggregate` è la **copia letterale** del risultato della singola partita, in **88.958 righe su 88.958**. Nessun contesto di doppio confronto. L'idea muore |
| 2 | §1.8, §4f | «l'esperienza si può contare anche da prima delle 5 leghe (es. un giovane dal Brasile)» | ❌ **`appearances.csv` ha ZERO righe** per Brasile, Argentina, MLS, Arabia Saudita, Giappone, Corea, Messico, Colombia, Australia. **22 competizioni su 70** non hanno alcuna presenza. L'esempio scelto è esattamente il caso che non funziona |
| 3 | §1.10 | «`clubs.csv` avrà un `total_market_value` come `national_teams.csv`: indice di forza già pronto e globale» | ❌ La colonna esiste ma è **vuota al 100%** (796 righe su 796), e `clubs.csv` copre **793 club su 3.274**. L'indice "già pronto" non esiste |
| 4 | §1.6 | «`national_teams.csv` ha `coach_name`, ma solo l'attuale» | ❌ La colonna è **vuota al 100%**: non c'è nemmeno l'attuale |
| 5 | §7-ter | «407 partite ai rigori, 394 con somma inferiore» | ❌ Sono **1.292** e **786**: la trappola che avevamo scoperto è **2-3× più grande** di come l'avevamo misurata |
| 6 | §1.9 voce 30 | «minuti in inferiorità: `red_cards` di `appearances.csv` + minuto in `game_events`» | ❌ `red_cards` conta **solo i rossi diretti**: ignora tutti i **9.741 secondi gialli**, cioè metà delle espulsioni |
| 7 | §6-quinquies p.7 | «12.835 espulsi troncati (88,7%) … le 1.980 con 90 pieni sono rossi a fine gara» | ❌ **Errore aritmetico mio**: 12.835 + 1.980 = 14.815 > 14.472. I due gruppi si sovrappongono; il residuo vero è **1.654** |
| 8 | §1.9 voci 33-34-46 | contratto, prestiti, primo anno in un campionato nuovo: «A — `transfers.csv`» | ❌ `transfers.csv` **non ha** il campo contratto **né** un flag prestito, e copre l'**8,7%** dei giocatori (Ronaldo, Lukaku, Immobile, Dybala, Mbappé: zero righe). Il contratto sta in **`players.csv`** |
| 9 | §1.5-1.7 | «l'estensione alle coppe europee in un colpo solo» | ⚠️ Vero per `games.csv`, falso a livello giocatore: la **Conference League ha ZERO** righe in `appearances.csv` (728 partite) |
| 10 | §1.6 | «i tornei finali delle nazionali un dato lo danno» | ⚠️ A livello **giocatore** no: gli Europei hanno **0 appearances e 0 lineups**; i minuti in nazionale esistono solo per Mondiale 2026 e Coppa d'Africa 2025-26 = **3.027 righe su 1.894.350 (0,16%)** |
| 11 | §1.1 | «`game_events`: il minuto esatto di ogni evento» | ⚠️ Il campo `minute` usa **−1 come segnaposto** di "ignoto" (tutti i 13.574 Shootout, 3.784 cartellini, 118 gol, 99 cambi) — un "finto pieno" della regola R6 |
| 12 | §1.8, §1.9 v.23 | «altezza e peso da verificare» | ✅/❌ L'**altezza c'è** (`height_in_cm`, 98,66%); il **peso non esiste** in nessuno dei 12 file |
| 13 | §1.11 | «derby derivabile se `clubs.csv` porta la città» | ❌ `clubs.csv` **non ha** nessun campo città. L'idea muore qui (serve un'altra fonte) |
| 14 | §1.10, §1.1 | «`clubs.csv` non ancora ispezionato» | ❌ **`clubs.csv.gz` è GIÀ nel repo** da `files/player_scores/`. E peggio (§9.5): il repo **legge già** altezza, piede, contratto e presenze in nazionale |

## 9.2 · Cosa invece REGGE (verificato in modo indipendente)

Tutto il nucleo "misurato" delle sezioni precedenti si è riprodotto **alla cifra**:
1.894.350 righe di `appearances.csv` con 0 duplicati e 3 righe a zero minuti;
990.536 valori a 90 e 11.041 sopra 90 con massimo 148; `players.csv` 50.149/50.149
senza duplicati; 10.596 giocatori delle 5 leghe di cui 5.270 in coppa europea e
8.401 altrove; Amrabat in 18 competizioni; 4.954/4.955 autogol esclusi dai gol;
date senza ora su 88.958 righe su 88.958; copertura arbitro/allenatore sotto lo
0,3%; tutte le dimensioni dei file (705,2 MB → 214,6 MB) e il repo a 66,33 MiB.

**E soprattutto il controllo di §6-bis è stato riprodotto da zero da un agente
indipendente**: 16.111/16.111 partite agganciate, 6 con tolleranza ±1 giorno,
16.109 gol identici, **le stesse identiche 2 divergenze**. È la parte più solida
del documento.

## 9.3 · ⚠️ La scoperta strutturale: `games.csv` dà il risultato del TRIBUNALE, `game_events` quello del CAMPO

La scoperta più importante per chi scriverà l'importatore. Ricostruendo il
punteggio dai soli eventi e confrontandolo con `games.csv` su tutte e 16.111 le
partite, i due divergono in **3 casi**:

| partita | eventi (campo) | `games.csv` | cos'è |
|---|:--:|:--:|---|
| Verona-Roma 19/09/2020 | **0-0** | 3-0 | assegnata a tavolino |
| Union Berlin-Bochum 14/12/2024 | **1-1** | 0-2 | assegnata a tavolino |
| Toulouse-Brest 11/01/2020 | 1-5 | **2-5** | un gol davvero **mancante** negli eventi |

Cioè: **gli eventi sono conformi alla regola R1** del `CLAUDE.md` (il dato è il
risultato del campo), **`games.csv` no**. Chi importasse i gol da `games.csv`
importerebbe il risultato del tribunale, contraddicendo una regola del progetto
senza accorgersene. La terza riga dice però che nemmeno gli eventi sono perfetti:
la regola operativa è **incrociare le due fonti e istruire le divergenze una per
una** (sono tre in nove stagioni: costo nullo).

## 9.4 · Dati NUOVI trovati — mai nominati nel piano

Il dataset ha **163 colonne**; il piano ne nominava **52**. Le più utili fra
quelle mai viste:

| dato | dove | perché conta |
|---|---|---|
| **`home/away_club_position`** | `games.csv`, **100% piena** | posizione in classifica. Semantica misurata: è la classifica **DOPO** la giornata (88,7% di accordo contro 44,9% per "prima") → colonna `post`, ma la sua **versione ritardata è `pre` e gratis** |
| **`player_valuations.csv`** | già nel repo | l'**unica serie storica datata per giocatore** del dataset (154.022 valutazioni per i nostri giocatori). È il **rimpiazzo naturale** della vuota `clubs.total_market_value` per l'indice di forza di §1.10 |
| **`competitions.sub_type`** | `competitions.csv` | l'ossatura **già pronta** del `peso_competizione` che §1.10 diceva di dover inventare da zero |
| **`contract_expiration_date`** | `players.csv` (non `transfers.csv`) | la voce 33 cercava nel file sbagliato |
| **`international_caps`, `international_goals`** | `players.csv` | toccano il fronte che il piano dichiara più scoperto (le nazionali) |
| **`highest_market_value_in_eur`** (93%) | `players.csv` | rende calcolabile la "**distanza dal picco di carriera**" (§1.12) |
| **`fifa_ranking`** | `national_teams.csv` | indice di forza **pronto** per le nazionali |
| `squad_size`, `average_age`, `foreigners_percentage`, `national_team_players`, `stadium_seats`, `net_transfer_record` | `clubs.csv` | sei colonne di contesto-club, tutte mai nominate |
| **`stadium` cambia dentro la stessa squadra** | `games.csv` | rileva il **campo di casa temporaneo** — si aggancia direttamente alla Fase 123 (il 5% di partite "in casa" giocate altrove) |
| `date`, `player_name`, `player_current_club_id` | `appearances.csv` | tre colonne che il piano non elencava |

**Due misure nuove, fatte sul posto**: il **27,6% dei titolari gioca fuori dal
proprio ruolo naturale** (dà sostanza alla voce 31); e `club_games.is_win` è
**lossy** — il pareggio è codificato come sconfitta, quindi non va usato.

## 9.5 · 🔴 Il repo usa GIÀ metà di ciò che il piano voleva "verificare"

`scripts/build_stagione_anagrafica.py` legge **già** `foot`, `height_in_cm`,
`contract_expiration_date`, `international_caps` e `sub_position`; e quattro dei
dodici file (`appearances`, `clubs`, `players`, `player_valuations`) sono **già
versionati** in `files/player_scores/`.

È lo stesso errore delle piste 10/11 (file elencati e mai aperti) che questo
piano era nato per correggere, ripetuto un livello più in basso. **Regola che ne
esce**: prima di dichiarare un dato "da verificare" o "da procurare", cercarlo
nel repo — sia nei file, sia nel codice che li legge.

## 9.6 · Le tre refutazioni: i numeri erano giusti, le conclusioni no

| affermazione | numeri | conclusione |
|---|:--:|---|
| «il motivo del cartellino: 18 etichette, 52 combinazioni» | ✅ riprodotti al terzo decimale | ❌ sono cifre **globali**. Nel perimetro del progetto (5 leghe 2017-2025) sono **17 etichette e 46 combinazioni**, e il motivo è coperto **meglio** del globale (12,3% mancante contro 26,4%) |
| «la copertura del motivo si stabilizza sopra il 94%» | ✅ tutti riprodotti | ❌ **falso per lega**: FR1 98,5%, IT1 96,6%, L1 95,6% — ma **GB1 93,5% ed ES1 92,1%, entrambe in CALO** (ES1: 93,7 → 92,6 → 91,1 → 90,6). Sui **rossi diretti** la copertura resta all'**86,3%** anche nel periodo buono. Il bias è **lega × stagione**, non stagione: 18 celle su 35 dal 2019 sono sotto il 94%, con Ligue 1 2018-19 al **16,0%** |
| «la quota di infortuni è piatta, quindi il segnale non è inflazionato dall'epoca» | ✅ riprodotti | ❌ **la quota è piatta perché numeratore e denominatore crescono insieme**. I cambi-infortunio **per partita** passano da 0,469 a 0,730: **+56%**. E non è artefatto di etichettatura: nelle due leghe già pulite nel 2017 il tasso sale comunque con uno scalino al 2020 (regola dei 5 cambi) |

**Una quarta cosa emersa dalle refutazioni, operativamente importante**: la
tassonomia delle sostituzioni è **collassata**, non migliorata. `Resting`
(1,77% → 0,05%), `Risk of booking` (0,55% → 0,11%), `Delay`, `Special
achievements` sono **morte dal 2020**: "Tactical" le ha assorbite. Chi contasse
di usare "Risk of booking" come segnale troverebbe la categoria vuota.

## 9.7 · I dati DERIVATI sono tutti fattibili — provato, non ipotizzato

Un agente ha **ricostruito lo stato di campo minuto per minuto** su tutte e
16.111 le partite (~40 righe di codice, 1,2 s di esecuzione) e lo ha validato in
tre modi indipendenti:

- minuti ricostruiti vs `appearances.minutes_played`: **94,92% esatti, 99,986%
  entro ±1** su 476.913 coppie giocatore-partita;
- invariante "11 in campo ogni minuto, meno le espulsioni": **99,39%** delle partite;
- identità Σ(gol-fatti-col-giocatore-in-campo)/gol = **11,000 esatto** per le
  squadre senza espulsioni.

Su questa base sono **FATTIBILI**: plus/minus, punteggio minuto per minuto
(rimonte, stato di gioco), minuti in inferiorità numerica, gol subiti per
portiere, coesione dell'undici, turnover, ritmo/tempo dall'ultimo gol.

⚠️ **Limite trasversale a tutti**: i minuti degli eventi sono **troncati a 45 e
90** — il recupero è ripiegato lì dentro (il minuto 90 concentra 3.341 gol
contro ~500 dei minuti vicini). Circa l'**8,9% dei gol** sta in un secchio senza
minuto esatto. Ogni analisi temporale fine è compromessa in coda di tempo.

## 9.8 · Classificazione finale: raggiungibile / irraggiungibile

**✅ RISOLTI (fonte trovata, licenza pulita)**

| dato | fonte | licenza | copertura |
|---|---|---|---|
| **orario di inizio** | `openfootball/football.json` | **dominio pubblico** | **16.111/16.111** (100%) |
| *(idem, ripiego)* | `football-data.co.uk` colonna `Time` — **file già in repo** | come le altre nostre quote | 12.459/16.111 (77,3%), dal 2019-20 |
| **meteo storico** | **open-meteo** archive API, senza chiave | CC BY 4.0 (free = non commerciale) | testata fino al 1990 |
| **infortuni storici** | Kaggle `irrazional/transfermarkt-injuries` | **CC BY 4.0** | 107.971 record, **66.982 nella nostra finestra**; si ferma a 2023-24 |
| **coordinate stadi** | Wikipedia/Wikidata, **già in uso nel repo** | CC BY-SA / CC0 | 90/94 |

L'orario è il caso più istruttivo: **il dato non mancava, mancava il fatto di
averlo portato nello snapshot** — la colonna `Time` è nei CSV di football-data
che il repo ha già.

**🟡 PARZIALI**

| dato | fonte | limite |
|---|---|---|
| **event data** (tocchi, passaggi, dribbling…) | Wyscout/Pappalardo su figshare, **CC BY 4.0**, esattamente le nostre 5 leghe | **solo 2017-18**: 1.826 partite = **11,3%** della finestra |
| *(alternativa)* | StatsBomb open data — **mai verificato prima dal progetto** | nella nostra finestra vale **230 partite (1,4%)**, 3 club soli |
| **terna arbitrale + VAR** | Wyscout 2017-18 + `api.fifa.com` dal 2020/21 | buco 2018-19 e 2019-20 |
| **rigori, falli, recupero concesso per arbitro** | derivabili dagli eventi Wyscout | solo 2017-18 |

**❌ IRRAGGIUNGIBILI oggi**
- **PSxG / dati portiere avanzati**: nessuna fonte con licenza chiara.
- **Convocazioni per finestra FIFA**: nessuna fonte aperta trovata.

**🔒 CHIUSE PER LICENZA, non per rete** — la distinzione che la Fase 126 chiedeva
di fare esplicitamente:
- **API ufficiale Premier League** (`footballapi.pulselive.com`): tecnicamente
  aperta, **161 metriche Opta** per squadra, terna completa **VAR incluso**, 9/9
  stagioni. Ma i T&C vietano testualmente *«creating a database … that includes
  material downloaded … from the Website»* — cioè esattamente ciò che faremmo;
- **bundesliga.com**: il `robots.txt` **consente** ClaudeBot, ma la stessa pagina
  porta la riserva DFL ex §44b(3) UrhG che vieta bot e training. **Quando le due
  divergono, vince la riserva legale**;
- **Transfermarkt diretto**: il `robots.txt` vieta **esplicitamente** ClaudeBot e
  anthropic-ai (ri-verificato oggi). Il dataset Kaggle CC0 resta l'unica via.

## 9.9 · Il fronte NAZIONALI è chiuso da questa fonte

Misurato: il dataset ha **5 soli tornei finali, 742 partite**. **Nessuna
qualificazione, nessuna amichevole, nessuna Nations League** (verificato per
parola chiave su tutte le 65 competizioni). Gli Europei hanno **0 appearances e
0 lineups**. I minuti in nazionale sono **3.027 righe su 1.894.350 (0,16%)**.

**Conseguenza**: l'affaticamento da doppio impegno club+nazionale (§1.0 livello 3,
§1.3) **non è servibile da qui**, e nemmeno dai tornei finali. Serve una fonte
esterna che oggi non esiste (vedi §9.8). Il livello "convocazione per finestra"
resta il buco più grande del piano.

## 9.10 · Aggiornamento nel tempo: il dataset non è un calendario

- si ferma al **2026-07-06** e non contiene **nessun fixture futuro** (0 partite
  dopo oggi): **non è una fonte di calendario**;
- la stagione **2025-26 delle 5 leghe è completa**;
- ma la freschezza è **per-competizione e inaffidabile**: mancano le **tre finali
  europee 2025-26**, il Mondiale 2026 ha solo i gironi, e il ritardo va da **24 a
  236 giorni** a seconda della competizione.

Per la manutenzione (§6-quater punto 4) significa: il dataset va bene per il
**backfill storico**, non per l'aggiornamento tempestivo della giornata in corso —
quello resta compito della raccolta quotidiana già esistente.

## 9.11 · Copertura sulle nostre 5 leghe: il controllo che §6 rimandava al tracer bullet

Fatto adesso, sulle **16.111 partite** (numero che coincide **esattamente** con
gli snapshot del repo):

| file | copertura | buco |
|---|--:|---|
| `appearances.csv` | 16.110/16.111 (**99,99%**) | 1 partita |
| `game_events.csv` | 16.110/16.111 (**99,99%**) | 1 partita (FR1) |
| `game_lineups.csv` | 16.057/16.111 (**99,66%**) | **48 partite di Liga 2018-19** |

Risponde alla domanda che il piano teneva aperta: **sì, lineups ed events coprono
le nostre leghe quanto `appearances`**. Il tracer bullet del passo 1-2 di §6 non
deve più misurare questo: è misurato.

---

# 10 · 🌍 OLTRE IL CSV: fonti esterne, verifica incrociata, e l'indice di forza costruito in casa (30/07/2026)

> **Perché.** Il §9 aveva verificato solo cosa è raggiungibile **dentro** il
> dataset Kaggle. Su richiesta dell'utente («allarghiamo lo sguardo… le carriere
> fuori dall'Europa le possiamo raggiungere con altre fonti; l'indice di forza
> possiamo ottenerlo noi a modo nostro, ingegniamoci»), sette fronti di ricerca
> esterna + dieci verifiche avversariali. **Sette refutazioni su dieci**: le
> scoperte più entusiasmanti erano quasi tutte troppo ottimistiche, e quanto
> segue è la versione già ridimensionata.

## 10.1 · Carriere fuori Europa — **PARZIALE**, non risolta

> 🔴 **SUPERATA il 31/07/2026 — vedi `docs/AUDIT_FONTI_GIOCATORI.md` §B.**
> Il fronte era rimasto aperto per **due ricerche consecutive** per un **errore di
> oggetto, non di fonte**: si contava la tabella «Career statistics» (la forma più
> ricca e più rara, 62,2%) invece del **blocco carriera dell'infobox** (la forma più
> povera e quasi universale, **332/333 = 99,7%**), che contiene già i tre campi che
> servivano — anni **con fine**, club, presenze. *Le date di fine non mancano su
> Wikipedia: le perde il parser di DBpedia* (`dbo:years` è `xsd:gYear` di solo inizio).
> **Recuperate 2.854 tappe pre-debutto** (79,2% con anno di fine, 83,9% con presenze,
> 96.164 presenze totali). Verdetto corretto: **risolto sulla copertura e
> sull'elenco dei club; NON risolto sul conteggio delle presenze**, separabile
> pre/post debutto solo per **246/333 = 73,9%**.
> ⚠️ Due rettifiche: l'idea delle **Wikipedia in altra lingua è SMENTITA**
> (guadagno **0 su 333**, e `es.wikipedia` è strutturalmente *peggiore*); e il fronte
> è mal chiamato — la coorte è **europea per il 67,0%**, il buco vero sono le
> **seconde e terze divisioni europee**, non l'extra-Europa.
> `footballdatabase.eu` e `playmakerstats.com`, 🟡 qui sotto, oggi sono **403
> Cloudflare → ❌**.

Il problema (§9.1 n.2): `appearances.csv` non ha nessun campionato
extra-europeo né seconde divisioni, e **333 giocatori** delle nostre 5 leghe
(debutto dopo il 2017-07, età ≥26) risultano con **zero passato**.

**Cosa funziona.** **DBpedia** (`dbpedia.org/sparql`, HTTP 200 verificato,
`robots.txt` **non** vieta `/sparql`, Crawl-delay 10 rispettato) espone
`dbo:careerStation` con squadra, anni e presenze. Copre Brasile fino alla Série
D, Argentina, Liga MX, MLS, J1, K League, Chinese Super League, Perù, Uruguay,
Algeria — **e le seconde/terze divisioni europee, dove sta il 79% degli spell
mancanti**.

**Perché NON è la soluzione che sembrava** — tre difetti, tutti misurati:

1. **Il 96,1% dichiarato non è ottenibile in modo conforme.** Dipendeva da un
   passaggio via `query.wikidata.org/sparql`, il cui `robots.txt` dice
   `Disallow: /sparql`. Per la regola del progetto quella via è **chiusa**
   (stesso motivo per cui Understat è chiuso). Con la sola via conforme
   (nome → IRI dentro DBpedia) la copertura misurata scende a **250/333 =
   75,1%**, ed è un tetto perché non filtra gli omonimi;
2. **la carriera non è ricostruibile, solo intuibile**: su **2.965 stazioni,
   ZERO hanno una data di fine** (`dbo:years` è un `xsd:gYear` di solo inizio);
   appena il **33%** dei giocatori coperti ha le presenze su *tutte* le tappe
   pre-debutto; e per il **33%** l'ultima tappa è a cavallo del debutto, quindi
   le presenze non sono separabili prima/dopo. DBpedia mescola inoltre
   **settore giovanile e prima squadra** nella stessa stazione;
3. **Wikidata come ripiego è conforme ma il dato è debole.**
   `Special:EntityData/Q<id>.json` **è permesso** (riga 436 `Allow:` batte la
   435 `Disallow:` per longest-match RFC 9309) ed è **CC0** — ma su un campione
   di 90 giocatori: join valido all'82,2%, **41,9% senza alcun numero di
   presenze**, **62,2% sottostima** il nostro dato. L'esempio-vetrina era
   sbagliato (25 presenze al Milan contro 51 reali).

**Verdetto onesto**: si può sapere **se** un giocatore ha un passato e
grosso modo **dove**, non **quanto**. Utile per un flag/categoria
("proviene da campionato minore/extra-europeo"), **non** per un conteggio di
presenze. E la licenza DBpedia è **CC BY-SA 3.0 + GFDL**, non CC0: lo
share-alike è un vincolo reale in ridistribuzione, da dichiarare (regola R2).

### 10.1-bis · Seconda ricerca (30/07/2026, richiesta utente: «non riusciamo a trovare altre fonti?»)

**Trovato un complemento, non un sostituto: le pagine-articolo di
`en.wikipedia.org`, fetch diretto (NON l'API).** Verificato riga per riga il
`robots.txt` (711 righe): `/api/` e `/w/` sono **vietati**, ma le pagine
`/wiki/NomeGiocatore` **non lo sono** (solo `Special:` e simili). La tabella
"Career statistics → Club" delle pagine-giocatore dà presenze **per stagione e
per competizione**, e — a differenza di DBpedia — il passaggio da una riga alla
successiva **fissa implicitamente la fine di ogni tappa a livello di
stagione**: la lacuna più grave di DBpedia (zero date di fine su 2.965
stazioni) qui è colmata.

**Copertura misurata** (campione casuale 40/333, riproducibile): **100%**
trova l'articolo giusto (3 casi di disambiguazione, risolvibili in automatico
incrociando età/nazionalità già in `players.csv`); ma solo **62,5%** ha la
tabella strutturata (il resto sono biografie in sola prosa, senza nulla da
estrarre). Dove la tabella c'è, **100%** contiene dati veri pre-debutto. Su un
campione mirato di 20 giocatori extra-europei noti, la tabella c'è nel **90%**.

**Verdetto**: **complementare a DBpedia, non superiore** — copre meno (62,5%
contro 75,1%) ma dove copre è più ricco (fine-tappa a livello di stagione).
Licenza **CC BY-SA 4.0** (nota bene: 4.0, non 3.0 come il resto del sito),
stesso vincolo di attribuzione/share-alike di DBpedia.

**Altre piste, tutte verificate e CHIUSE**:

| fonte | esito |
|---|---|
| worldfootball.net / weltfussball.de | ❌ `robots.txt` vieta **esplicitamente** `User-agent: ClaudeBot` |
| eu-football.info | ❌ permissivo in generale, ma vieta **specificamente** `/*player=*` |
| RSSSF | 🟡 aperto ma senza pagine-carriera per giocatore: solo risultati/classifiche |
| bdfutbol.com | 🟡 permissivo ma copre solo la Spagna: non tocca il buco Brasile/Argentina/Asia |
| ceroacero.es | ❌ dietro Cloudflare anti-bot |
| CBF, AFA, Liga MX, J.League, K League (siti ufficiali) | 🟡 raggiungibili, nessuna API/bulk data aperta trovata |

> ⚠️ **Una fonte "avvelenata" trovata e scartata, da non riprendere**: un
> dataset su Zenodo (*"Comprehensive Ontology and Dataset for Football
> Players"*) dichiara licenza **CC0**, ma è verificabilmente uno **scrape
> diretto di Transfermarkt** (URL e ID Transfermarkt nei dati, immagini dal
> CDN di Transfermarkt) — chi l'ha caricato non aveva il diritto di
> concedere quella licenza. È lo stesso schema già chiuso per StatFootDB e i
> mirror Understat/API-Football (§10.5): **una licenza dichiarata non vale
> se chi la dichiara non è il titolare del dato**.

*(Correzione tecnica: `dbo:SoccerPlayer` sono **194.850** entità distinte, non
536.455 — quello era un `COUNT(*)` su triple duplicate fra grafi di lingua.)*

## 10.2 · ⭐ Indice di forza: **RISOLTO**, e vince l'Elo calcolato in casa

L'utente chiedeva di ingegnarci. Quattro vie prototipate e validate contro un
metro indipendente — le **quote 1X2 di chiusura** dei nostri snapshot (16.111
partite, copertura 100%), più il log-loss 1X2 fuori campione:

| indice | correlazione col mercato | log-loss OOS |
|---|--:|--:|
| **Elo pre-partita (in casa)** | **0,9329** | **0,9857** |
| valore rosa mediano | 0,8508 | 0,9974 |
| valore rosa top-11 | 0,8492 | — |
| coefficiente UEFA ricostruito | 0,7687 | — |
| `national_team_players` | 0,7517 | — |
| `stadium_seats` | 0,6195 | — |
| `foreigners_%` | 0,2587 | — |
| `average_age` | 0,0288 | — |
| *(riferimenti)* | mercato **0,9663** | baseline **1,0730** |

**Ricetta raccomandata** (iperparametri scelti su griglia col log-loss OOS,
superficie piatta su 36 combinazioni → robusti): **K=12**, vantaggio-casa **65**,
regressione di fine stagione **0,15** verso la media della **propria** lega,
cold-start delle mai-viste a **media − 70** (l'analogo del `promoted_prior δ`
del Dixon-Coles). **Includere sempre le coppe UEFA**: sono l'**unico ponte** che
rende comparabili leghe diverse (4.897 partite, log-loss OOS 0,9902 contro
1,0487 di baseline).

Normalizzazione 0-1: `forza01 = 1/(1+10^(−(elo−1407,3)/148,6))`.
⚠️ **Avvertenza misurata**: la *differenza* di due `forza01` correla **meno** del
delta Elo grezzo (0,8347 contro 0,8812) perché la logistica schiaccia le code →
per **segmentare/modellare** usare il **delta Elo grezzo**, per **pesare le
squadre passate** il **0-1**.

**Copertura**: 5.655 club-stagione, 903 club, 2012-2025. Fuori dalle 5 leghe
**4.279 club-stagione**, di cui 452 visti **solo in coppa** e quindi fragili
(mediana 10 partite di storia) → serve una colonna `n_games_prima` come flag.

**Fonte esterna trovata e CONFERMATA: ClubElo** (`api.clubelo.com`) —
⚠️ **solo `http://`, l'HTTPS non funziona**. Licenza: permesso esplicito
dell'autore *«You can use my calculations… Please cite me»* → uso libero **con
attribuzione obbligatoria**. Confronto testa a testa: ClubElo 0,9376 contro il
nostro 0,9308, correlazione fra i due **0,9921**, e nella regressione congiunta
il nostro Elo è **inglobato** (pesi 0,952 ClubElo / 0,034 nostro).

**Perché costruirlo comunque in casa**: è CC0, offline, riproducibile e
calcolabile per **qualunque** club presente in `games.csv`. **Onestà**: non
batte il mercato (0,9857 contro 0,9663) e **non è pensato per farlo** — serve a
segmentare e a pesare, non a prezzare.

## 10.3 · Infortuni: **precisione ~97%, sensibilità ~37-63%**

> 🔴 **AGGIORNATA il 31/07/2026 — vedi `docs/AUDIT_FONTI_GIOCATORI.md` §A**, che
> misura la stessa cosa con **due controlli indipendenti nuovi** e cambia la
> raccomandazione operativa.
> **(1) Le fonti sono reali, dimostrato due volte**: contro le nostre presenze, un
> infortunato gioca il **4,5%** delle partite del suo club contro il **58-59%** dello
> stesso giocatore nella stessa finestra spostata di sei mesi (placebo); e contro la
> **stampa d'epoca**, 29 casi su 29 realmente avvenuti, **0 smentiti**.
> **(2) Il difetto non è l'invenzione, sono le DATE**: `from` è il giorno della
> *partita* in cui il giocatore si è fatto male (offset medio **+0,68 gg**, test dei
> segni p=2,0e-04), `until` è in anticipo di **4-11 giorni** sul rientro vero.
> Convenzione obbligatoria all'import: **`[from+1, until]`** — quella letterale
> inietta un look-ahead di un giorno (R8). Tasso d'errore reale: **5-11%**.
> **(3) Il collo di bottiglia è la SENSIBILITÀ**: sulle 8.201 assenze prolungate
> ricostruite dalle sole presenze, le fonti ne dichiarano **il 46-52%** (A∪B: 57,69%).
> «Nessun infortunio dichiarato» **non** significa «disponibile».
> **(4) Risposta alla domanda A-o-B: NON sostituire.** B è più pulita (record
> esclusivi coerenti al 93,1% contro 89,2%; duplicati 0,24% contro 9,6%) e arriva al
> **12/09/2025** contro il **25/02/2024**; ma A è più **sensibile** a parità di
> stagioni (**59,75% vs 54,59%**, McNemar chi²=167). Sostituire costa **426 finestre**
> e **−5,2 punti** di copertura. Uso corretto: **B come base, A come complemento sul
> 2017-2023**.
> **(5) Nessuna fonte non-Transfermarkt esiste**: sei angoli nuovi, sei esiti
> negativi. L'unica a origine genuinamente indipendente — l'API **Fantasy Premier
> League**, che ha pure `news_added` = il momento in cui il fatto diventa noto (R8) —
> è **chiusa dai ToS**, non dal robots.txt.
> ⚠️ **La licenza resta rotta per entrambe** (CC BY 4.0 e CC0, ma nessuno dei due
> dichiaranti è titolare del dato Transfermarkt): **l'alta qualità non sana la
> licenza**, sono due decisioni separate.

Il dataset `irrazional/transfermarkt-injuries` (CC BY 4.0 verificata) si
aggancia **per `player_id` di Transfermarkt: 18.824/18.825 = 100%** — nessun
matching per nome.

**La verifica incrociata** (la parte che conta): incrociando le **10.558
sostituzioni per infortunio** degli eventi con le date del dataset —
**36,7% di corrispondenza a ±1 giorno**, contro **1,0%** delle sostituzioni
tattiche e **1,0-1,4%** dei placebo con la data spostata di ±91/182/365 giorni:
un **lift di 35×**. Il tasso sale **monotonamente con la gravità**: 11,5% se il
giocatore non salta nulla → **63,2%** se salta le 3 partite successive. Nella
direzione inversa la **precisione è 97,3%**.

> **Profilo della fonte: quando parla dice il vero; quando tace, spesso mente
> per omissione.**

⚠️ **Tre limiti che ne condizionano l'uso**: (1) si ferma a **febbraio 2024**;
(2) la copertura **non è uniforme fra leghe** — Serie A 49,5%, Premier 41,4%,
Liga 36,7%, Bundesliga 29,0%, **Ligue 1 20,9%**, e gli infortuni per
giocatore-stagione vanno da 1,886 (Bundesliga) a 0,598 (Ligue 1): un fattore
**3,2** che nessuna medicina sportiva giustifica, quindi è **difetto di
registrazione**; (3) contiene **9.275 duplicati esatti**.

### 10.3-bis · Seconda fonte cercata e trovata (30/07/2026, richiesta utente: «verifichiamo che le due combacino»)

**Nessuna fonte a origine DAVVERO indipendente da Transfermarkt è utilizzabile
oggi.** Verificate e chiuse: `premierinjuries.com` (403 con challenge
Cloudflare, non aggirabile); `physioroom.com` (non è più un archivio infortuni,
è un e-commerce); lo studio accademico sulla Bundesliga (*Sports Medicine –
Open* 2023, fonte genuinamente indipendente — i media, non Transfermarkt —
licenza CC BY 4.0) ha però il dato grezzo **non pubblico**, solo "su richiesta
motivata all'autore"; vari dataset Kaggle scartati per licenza "Unknown" o
perché troppo piccoli (657 righe, 7 club).

**Trovato invece un SECONDO SCRAPE di Transfermarkt, fatto da un altro
autore**: `xfkzujqjvx97n/football-datasets` su Kaggle. Licenza verificata
all'endpoint pubblico dell'API Kaggle: **CC0**. 143.195 record, 34.561
giocatori, stesso schema (player_id, date inizio/fine, giorni persi) —
aggiornato fino al **dicembre 2025**, molto oltre il febbraio 2024 della
fonte già nota.

**Verifica incrociata fra le due fonti**, sul perimetro delle 5 leghe
2017-2025 (A = `irrazional`, 31.297 infortuni; B = `xfkzujqjvx97n`, 37.511):
appaiando per `player_id` + data di inizio (±1 giorno), **27.588 coppie**,
con **date identiche nel 99,98%** dei match. Dove appaiate: **data di fine
identica nel 99,3%**, causa dell'infortunio testualmente identica nel
**99,3%** (le differenze sono quasi sempre sinonimi, "Calf injury" contro
"Calf problems"). Ristretto alla sola finestra in cui **entrambe** le fonti
potevano vedere lo stesso evento (fino a febbraio 2024): **A ritrova il
94,0%** di B e **B ritrova l'88,8%** di A — **le due fonti indipendentemente
scritte si confermano a vicenda**, con un margine di rumore fisiologico di
due scrape dello stesso sito crowd-sourced, non un errore sistematico.

**E B estende quello che A non poteva dare**: dei 9.923 infortuni che B ha e
A no, l'**80%** cade **dopo** febbraio 2024 — cioè non è un buco, è
semplicemente il periodo che A non poteva coprire. Il restante 20% (1.985
casi) sono buchi genuini di A dentro la propria finestra.

**Un effetto secondario interessante sul limite già noto** (lo squilibrio fra
leghe): B **riduce ma non chiude** il divario. Il rapporto
Bundesliga/Ligue-1 passa da **2,43×** (fonte A) a **1,97×** (fonte B) — la
Ligue 1 guadagna il **+45,6%** di infortuni registrati in più rispetto ad A,
il salto maggiore fra le 5 leghe. Quindi lo squilibrio era **in parte un
difetto di scraping reale** (si è attenuato con una seconda passata), ma
**non del tutto un artefatto** — resta comunque la lega con meno infortuni
registrati anche nella fonte migliore.

**Raccomandazione operativa**: non sostituire la fonte primaria — usare la
seconda come **estensione dichiarata** (regola R2, fonte secondaria
dichiarata): riempie il periodo dopo febbraio 2024 e i 1.985 buchi genuini
interni alla prima. Nessuna importazione fatta in questa sessione, resta una
decisione da prendere quando si scriverà il codice.

## 10.4 · Arbitri: la via "gratis" funziona, quella ricca è chiusa per licenza

**Funziona**: `games.csv` dà l'arbitro sul **99,96%** delle nostre 16.111
partite (250 arbitri, mediana 54 gare a testa), e gli eventi danno cartellini e
rigori **senza alcun join**. Il segnale c'è ed è stato misurato contro una
**banda nulla da permutazione**: la deviazione standard fra arbitri sui gialli
la supera in **tutte e 5 le leghe** (Serie A 0,582 contro [0,183, 0,303]).

**I falli** non sono nel dataset ma sono in **football-data** (colonne `HF`/`AF`,
100%): il join `games.csv` ↔ football-data aggancia il **93,3%** e arriverebbe
quasi al 100% con i `TEAM_ALIASES` già nel repo.

> ⚠️ **Correzione a un'assunzione implicita**: la colonna `Referee` di
> football-data esiste **solo per la Premier League**. Per le altre quattro
> leghe l'arbitro **deve** venire da `games.csv`.

**Chiuso per licenza, non per rete**: `api.fifa.com` ha la **terna al 100%** su
9.975 partite, il **VAR** su 5.603 e persino il **recupero concesso** —
ma i ToS §5.3 vietano l'uso fuori dalle piattaforme FIFA, e il `robots.txt`
risponde 503 persistente (per RFC 9309 va letto come *disallow*). Come per
l'API della Premier League: **raggiungibile e ricca, non utilizzabile**.
`legaseriea.it` non ha endpoint (307 sulla homepage); AIA e FFF sono dietro
anti-bot (403) e **non si aggirano**.

## 10.5 · Event data: resta al **12,55%**, e le scorciatoie sono avvelenate

Caccia esaustiva (figshare, Zenodo, OSF, HuggingFace, Kaggle, le liste
canoniche KU Leuven e PySport): **l'ecosistema aperto è esattamente quello già
noto**. StatsBomb **non è cambiato** (230 partite = 1,43%, un club per
stagione); i "nuovi" depositi Wyscout sono **campionato russo**; **SkillCorner
ha cambiato contenuto** (oggi A-League australiana, zero delle nostre).

**Unico guadagno pulito**: 2 partite di Bundesliga 2022-23 dal dataset
DFL/Sportec (figshare, CC BY 4.0, rilasciato **col consenso della DFL**) — è
minuscolo, ma è la **prima event data ufficiale** di una delle nostre 5 leghe
con licenza inequivocabile.

⚠️ **La scoperta avvelenata**: esistono tre **re-depositi di scrape** che
coprono dal 55,7% all'82,7% della finestra con esattamente le variabili che
servono (StatFootDB su figshare 8.970 partite; i mirror Understat su Kaggle
12.651 partite con xG/xA per giocatore-partita; un mirror API-Football).
**Dichiarano licenze aperte che non possono concedere**, perché i dati non sono
loro. È lo stesso motivo per cui il progetto ha chiuso WhoScored: non è la
raggiungibilità il problema, è il diritto di riuso.

## 10.6 · Seconde divisioni: ci sono già, **ma l'ipotesi della pista 12 è falsa**

**La fonte migliore non è openfootball, è football-data.co.uk** — quella che il
progetto **già usa**: pubblica le stesse cinque seconde divisioni (`I2`, `E1`,
`SP2`, `D2`, `F2`) con **schema identico a 105 colonne**, cioè con quote di
chiusura, tiri, corner e cartellini: **18.515 partite, 9/9 stagioni**, e il
2025-26 **completo** (openfootball è fermo a novembre 2025 su 4 repo su 5).
Manca solo l'xG. ⚠️ Licenza: *«© Football-Data. All Rights Reserved»* — **non è
aperta**; il progetto ci convive già per le massime serie, ma va dichiarato.

**Il risultato che conta è però una misura, e chiude la pista 12.** Agganciate
**108/108** neopromosse alla loro ultima stagione di seconda serie, e testati
tre indici contro il rendimento reale nella prima stagione in massima serie:

| indice della forza in seconda serie | correlazione | IC95% |
|---|--:|---|
| punti/gara standardizzati | **+0,004** | [−0,185, +0,193] → **zero** |
| Elo ClubElo al 15 luglio | +0,073 | [−0,117, +0,259] → rumore |
| **mercato** (prob. devigata media di stagione) | **+0,218** | **[+0,030, +0,391]** |

L'ipotesi della pista 12 — *«stimare la forza della neopromossa dal suo
rendimento reale in B»* — **non regge**. L'unico indice il cui intervallo
esclude lo zero è il **mercato** della seconda serie (R² = 4,75%). Anche la via
di promozione non ordina nulla (playoff 1,032 punti/gara contro 0,988 delle
promozioni dirette).

## 10.7 · Verifica incrociata: i nostri snapshot reggono, e saltano fuori due anomalie

Scaricati e confrontati per intero i 45 file di campionato di **openfootball**
(CC0) contro i nostri snapshot:

- **16.111/16.111 partite agganciate (100%)**, **date identiche al 100%**,
  **risultati identici al 99,981%** (16.108/16.111);
- le **101 partite in più** di openfootball sono le gare di Ligue 1 2019-20
  annullate dal COVID, marcate `[cancelled]`: il nostro snapshot fa bene a non
  averle.

⚠️ **Un avvertimento metodologico importante**: openfootball e `games.csv`
concordano fra loro al **100%** — **anche sulle due partite a tavolino**. Quindi
**non sono una conferma indipendente della regola R1**: riportano entrambe il
verdetto del giudice sportivo. **Il nostro snapshot è l'unico dei tre a portare
il risultato del campo**, ed è una scelta consapevole.

**Due anomalie nuove, da dichiarare per la regola R4** (registrate in
`docs/DATI.md` §1-quater):

1. **Nantes-Toulouse, 17/05/2026** (Ligue 1) — ✅ **risolta il 31/07/2026**:
   il nostro snapshot la conta **0-0**, e una ricerca su fonti di stampa
   esterne (non solo dataset) ha chiarito che è il dato **giusto**: ultima
   giornata, Nantes già retrocesso, gara **interrotta definitivamente al 22'**
   sullo 0-0 per un'invasione di campo dei tifosi in protesta, **omologata
   0-0 dalla Commissione Disciplinare della LFP** il 27/05/2026 — stesso
   meccanismo del caso Montpellier-Saint-Étienne sotto (regola R1). Le
   quattro "anomalie" viste il 30/07 (openfootball `[cancelled]`,
   football-data con statistiche basse, Understat senza xG, Kaggle senza
   presenze/eventi) sono tutte spiegate dal fatto che la partita è durata 22
   minuti, non 90: non era un "finto pieno" (R6), era R1 una terza volta.
   Nessuna correzione ai dati;
2. **Montpellier-Saint-Étienne, 16/03/2025**: marcata `[awarded]` da
   openfootball (0-2, sospesa all'88' per incidenti). Qui il risultato assegnato
   **coincide** con quello del campo, quindi non c'è nulla da correggere — ma va
   dichiarata lo stesso. L'inventario completo di openfootball sui 45 file è
   esattamente **3 `[awarded]` e 102 `[cancelled]`**.

### ⚠️ L'orario: §9.8 lo dava per «risolto», e mancava un controllo

Confrontate le due fonti dell'orario (football-data `Time` vs openfootball) su
**12.459 partite**: accordo **99,10%**, ma **solo dopo aver misurato un offset
di fuso orario** invece di assumerlo:

- **Premier League**: moda della differenza **0 minuti** (98,87%);
- **le altre quattro leghe**: moda **+60 minuti** (99,49%-99,89%).

**La colonna `Time` di football-data è in ora britannica.** Importarla senza
correggere il fuso avrebbe sfalsato di un'ora l'orario di **tutte** le partite
non inglesi — un errore che nessun controllo di completezza avrebbe rilevato,
perché il dato *c'è* ed è *plausibile*.

## 10.8 · Classificazione finale aggiornata

| dato | stato | fonte | licenza |
|---|:--:|---|---|
| orario di inizio | ✅ | openfootball (100%) / football-data `Time` ⚠️ **fuso da correggere** | CC0 / proprietaria |
| meteo | ✅ | open-meteo | CC BY 4.0 |
| **indice di forza club** | ✅ **costruito in casa** | Elo da `games.csv` (+ ClubElo come controllo) | CC0 / attribuzione |
| infortuni | 🟡 | Kaggle `irrazional/transfermarkt-injuries` (fino a 2024-02) + `xfkzujqjvx97n/football-datasets` (estensione, confermata al 94% nella finestra comune) | CC BY 4.0 + CC0 |
| seconde divisioni | ✅ | football-data (`I2`/`E1`/`SP2`/`D2`/`F2`) | ⚠️ proprietaria |
| arbitro per partita + cartellini/rigori | ✅ | `games.csv` + eventi | CC0 |
| falli per partita | ✅ | football-data (`HF`/`AF`) | ⚠️ proprietaria |
| carriere extra-europee | 🟡 **solo come flag** | DBpedia (75,1%) + Wikipedia pagine-articolo (62,5%, complementare) | CC BY-SA 3.0 / CC BY-SA 4.0 |
| event data per giocatore | 🟡 **12,55%** | Wyscout 2017-18, StatsBomb, DFL/Sportec | CC BY 4.0 |
| terna arbitrale, VAR, recupero | 🔒 **chiuso per licenza** | api.fifa.com | ToS FIFA |
| convocazioni FIFA storiche | ❌ | — | — |
| PSxG / portiere avanzato | ❌ | — | — |

## 11 · 🔴🔴 AUDIT DELLE 118 VOCI (31/07/2026) — sintesi

> **Verbale integrale: `docs/AUDIT_FONTI_GIOCATORI.md`** (13 agenti, 5 fette di
> audit + 3 giri di verifica avversariale + 4 fronti di ricerca esterna).
> **Quel file ha la precedenza su §9 e §10 di questo**, che sono anteriori.
> Qui sotto solo ciò che cambia le decisioni.

### 11.1 · Il bilancio delle fonti, dopo le refutazioni

| stato | n | % | cosa significa |
|---|---:|---:|---|
| **VERIFICATO** | 36 | 30,5% | misurato sul perimetro reale (16.111 partite, 5 leghe, 2017-2026) |
| **DERIVATO** | 45 | 38,1% | calcolabile da dati verificati, ma è un calcolo con assunzioni da dichiarare |
| **MANCANTE** | 21 | 17,8% | nessuna fonte utilizzabile trovata |
| **ASSUNTO** | 13 | 11,0% | dato per buono e **mai misurato**, o misurato male → **non usare finché non è chiuso** |
| **CHIUSO_LICENZA** | 3 | 2,5% | esiste, raggiungibile, vietato dai termini (recupero concesso, VAR, terna completa) |

**Solo il 30,5% delle voci è davvero verificato.** La verifica avversariale ha
**declassato 7 voci** da VERIFICATO/DERIVATO ad ASSUNTO e **rettificato 18 numeri**
senza cambiare stato.

### 11.2 · I due look-ahead ATTIVI nel codice (R8) — l'unica cosa urgente

Non sono ipotesi sul futuro database: sono **già dentro `scripts/build_stagione_anagrafica.py`**.

1. **riga 225 — `highest_market_value_in_eur`**: è il massimo dell'**intera serie
   storica** nel 100% dei casi, quindi include il futuro rispetto alla partita.
   Correzione **gratuita**: massimo *progressivo* fino alla data della partita.
2. **riga 222 — `international_caps`/`international_goals`**: snapshot **non datato**
   (copertura 58,20%), con 3.222 NaN che non distinguono «mai convocato» da «non
   rilevato».

⚠️ **Da decidere se e come correggerli**: tocca codice in produzione, quindi non è
stato fatto in sede di audit.

### 11.3 · Le 4 voci di gravità ALTA (dettaglio in §D del verbale)

1. **`attendance` in Bundesliga è la CAPIENZA, non il pubblico** — 796/2.382 partite
   (**33,42%**) hanno `attendance` == `stadium_seats`; il Bayern ha 9 valori distinti
   su 130 gare interne. L'idea §1.8 di misurare il vantaggio-casa col pubblico, lì,
   misurerebbe la capienza. **Declassata ad ASSUNTO.**
2. **«Primo anno in quel campionato» (allenatori) è falso per 155/496 (31,2%)** —
   `games.csv` parte dal 2012-08-10 e la feature legge il **bordo del dataset** come
   un esordio: Ancelotti «debutta» in Serie A nel 2018, Mourinho nel 2021.
   Lo stesso difetto era già riconosciuto per gli arbitri e assolto qui.
3. **«Primo anno in un campionato nuovo» (voce 46) copre il 34,8%, non il 55,9%.**
4. **1.119 titolari (0,317%) non hanno minuti**, concentrati per lega×stagione
   (**ES1 2020 al 4,60%**): un `LEFT JOIN + fillna(0)` li registra come «non ha
   giocato» **proprio nelle stagioni COVID**, dove il carico è l'oggetto d'interesse.

### 11.4 · La censura a sinistra che nessuna fase aveva dichiarato

**`appearances.csv` comincia il 2012-07-03.** Sta sotto le voci 12, 25, 39 (esperienza,
usura), A12/A13 (esperienza arbitro) e F25/F26 (esperienza allenatore) — cioè sotto
**tutto ciò che è cumulativo**. Conseguenze misurate: l'esperienza dell'arbitro è
censurata per il **66,2%** delle partite; quella globale dell'allenatore è falsa per
il **30,8%**.

### 11.5 · Sei trappole nei dati, tutte con il numero accanto

| trappola | numero |
|---|---|
| il prefisso `N. Yellow card` è il **contatore stagionale**, non l'ennesima ammonizione della partita | leggerlo male dà **15.077 espulsioni invece di 3.122 (11×)** |
| **la Coupe de France non esiste** in `competitions.csv` (10 coppe nazionali, nessuna francese) | un giocatore di Ligue 1 non accumula MAI carico da coppa; uno di Bundesliga all'86,6% → **confronto cross-lega distorto per costruzione** |
| `contract_expiration_date` è un **finto pieno di anni** | 76,66% come valore *attuale*, **0% come valore storico** |
| `clubs.csv` è uno snapshot la cui annata **coincide con la retrocessione** del club | un modello ci si aggancia e *sembra* funzionare |
| **i rigori sbagliati non esistono** in nessuno dei 12 file (un rigore c'è solo se segnato: 4.159) | usare i rigori realizzati come propensione dell'arbitro misura **il tiratore e il portiere** |
| **un gol manca dagli eventi**, silenziosamente: Toulouse-Brest 11/01/2020 (2-5 nel nostro snapshot, un solo gol del Toulouse in `game_events`) | un gol mancante **riclassifica lo stato di tutti i gol successivi** → la ricostruzione del punteggio va usata come **controllo permanente dell'importatore** |

### 11.6 · Una buona notizia grossa: gli xG/xA individuali sono già sul disco

Il piano afferma che Understat dà «solo aggregato-stagione per giocatore». È
**sbagliato**: i bundle in `files/` contengono **xG, xA, npxG, npg, xGChain,
xGBuildup, key_passes, shots** per giocatore — **10.008 righe** (Premier 4.819 +
Liga 5.189). È **il parser del repo a scartarli**
(`parse_season_players` in `src/data/understat.py`, righe 214-241). Non serve
nessuna fonte nuova: serve leggere colonne che stiamo già scaricando.

### 11.7 · Tre lezioni di metodo, generalizzabili fuori da questo fronte

1. **Quando un fronte resiste, prima di cercare una fonte nuova scrivi in modo
   esatto CHE COSA stai contando.** Le carriere sono rimaste aperte per *due*
   ricerche consecutive per un **errore di oggetto, non di fonte**: «la copertura è
   62,5%» era vero *e* fuorviante (era la copertura della tabella più ricca, non del
   dato che serviva). Bastava guardare **un altro pezzo della stessa pagina**:
   l'infobox copre il **99,7%**. È la versione-dati della lezione della Fase 92.
2. **L'anti-«fonte avvelenata» non può fermarsi agli identificatori.** Un dataset
   senza alcun ID/URL Transfermarkt è stato smascherato da una **firma numerica**:
   il campo `Days` differiva di **esattamente +1 nel 97,43%** dei casi — l'off-by-one
   di chi ricalcola `(until − from)` inclusivo dalle stesse due date. Le firme
   numeriche sono più difficili da ripulire dei metadati.
3. **`urllib.robotparser` di Python NON implementa RFC 9309**: applica
   *first-match-wins* invece di longest-match, e su `Special:EntityData/*.json`
   (permesso da un `Allow` più lungo) restituisce `False`. **Chi verifica con quello
   si auto-chiude una fonte lecita.**

## 12 · ⭐ Il Tier B è ENTRATO (31/07/2026) — Serie A 2025-26, 97 statistiche per giocatore-partita

> **Questa sezione ribalta §1.2 e §10.5 per una lega e una stagione.** Il Tier B
> era dichiarato irraggiungibile da tre ricerche consecutive. Non lo è più —
> non perché sia stata trovata una fonte aperta, ma perché **l'utente ha raccolto
> i dati a mano** da diretta.it/Flashscore e ha deciso di inserirli.
> **Dati: `files/diretta_serie_a_2526/` — leggere il suo README PRIMA di usarli.**

### 12.1 · Cosa è entrato

**11.894 righe giocatore-partita × 108 colonne**, Serie A 2025-26, 379/380
partite, 20 squadre, 584 giocatori. Copre **tutte** le righe Tier B della
checklist §1.9 — e alcune che non c'erano nemmeno:

| riga §1.9 | dato | stato prima | ora |
|:--:|---|---|---|
| 4 | tocchi | ❌ nessuna fonte | ✅ `Palloni toccati` (media 39,2) |
| 5 | passaggi tentati/riusciti | ❌ | ✅ + precisione, lunghi, filtranti, nel terzo finale, **progressivi** |
| 6 | dribbling tentati/riusciti | ❌ | ✅ (0,91 / 0,39) |
| 7 | interventi difensivi | ❌ | ✅ `Contrasti`, `Tackle`, separati per duelli **aerei e a terra** |
| 17 | **falli individuali** | ❌ solo a livello squadra (F96) | ✅ commessi **e** subiti |
| 18 | **xG e xA individuali** | ❌ | ✅ + **xGOT** (mai in checklist) |
| 19 | recuperi e intercetti | ❌ | ✅ `Palloni recuperati`, `Palle intercettate` |
| 21 | grandi occasioni create/sprecate | ❌ «etichetta Opta, non un dato che si procura» | ✅ create, fallite, parate |
| 48 | disciplina fine | parziale | ✅ falli individuali + cartellini + motivo |
| — | *non in checklist* | — | conduzioni progressive, ingressi in area e nel terzo finale, sponde, palloni persi, palloni toccati in area avversaria, blocco portiere completo (gol evitati, uscite alte, respinte di pugno) |

### 12.2 · La verifica, prima di fidarsi

Controllato contro `data/serie_a_matches.csv`, che viene da **football-data.co.uk**
— fonte completamente diversa: **join 758/758 team-partita (100,00%)**, **zero
alias necessari** sui 20 nomi squadra, **coerenza dei gol 758/758 (100,00%)**
(`gol dei giocatori + autogol avversari == risultato dello snapshot`), e l'unica
partita mancante è **esattamente** quella che il file dichiara (Lecce-Como
27/12/2025, che alla fonte ha solo i rating). **758 controlli indipendenti, 758
passati.**

### 12.3 · Il primo passo proposto — e la domanda giusta da fargli

**Non** costruire feature. Il primo passo è un **go/no-go a una domanda sola**,
che ora è finalmente ponibile con dati veri:

> **Sapere COME hanno giocato i singoli aggiunge qualcosa che i dati di squadra e
> le quote non hanno già?**

È il gemello della domanda a cui il **plus-minus** ha già risposto per metà
(`docs/CACCIA_EVENT_DATA.md` §6): sapere **chi** gioca vale **r = +0,0354** su
10.161 partite. Questa è la metà mancante.

**Disegno onesto, da fissare PRIMA di guardare i risultati:**
1. le feature si costruiscono **solo** da colonne `post` di partite **precedenti**
   (regola R8, §5 del README dei dati): forma recente del giocatore, aggregata a
   livello squadra sull'undici schierato;
2. il confronto è contro il **market-implied** sulle stesse partite — le quote
   2025-26 sono già nel nostro snapshot;
3. **la potenza va dichiarata prima**: 379 partite contro le ~574 che la Fase 98
   misura per l'80% sull'1X2. Un nullo **non** chiude il fronte, un positivo sì;
4. la stagione 2025-26 è **una sola**: qualunque risultato è per costruzione
   fragile alla stagione, come lo era il θ della Fase 75/81.

### 12.3-bis · ⭐ Entra la Premier (01/08/2026): la potenza diventa sufficiente

Seconda raccolta: **Premier League 2025-26**, `files/diretta_premier_league_2526/`
— **11.492 righe**, **380/380 partite** (nessun buco, a differenza della Serie A).
Verifica indipendente contro il nostro snapshot: **760/760** sul join e
**760/760** sulla coerenza dei gol; classifica ricostruita dal file 20/20 con 38
partite ciascuna; marcatori e assist coincidenti.

**Cosa cambia per il go/no-go di §12.3.** Con due leghe siamo a **759 partite**,
sopra le **~574** che la Fase 98 misura servire per l'80% di potenza sull'1X2
contro il mercato. **Il test diventa conclusivo invece che indicativo**: un esito
nullo ora chiuderebbe davvero il fronte, mentre con la sola Serie A (379 partite)
sarebbe rimasto ambiguo. Era il limite dichiarato in §12.4 e in §6.2 del README
della prima raccolta: è caduto.

**Un alias mancante, trovato dalla guardia.** Alla prima registrazione il join si
è fermato a **544/760**: diretta.it scrive `Manchester Utd` e `Nottingham`, i
nostri snapshot `Man United` e `Nott'm Forest`. I due alias sono entrati in
`src/data/sources.py::TEAM_ALIASES` — dove il progetto li tiene da sempre — e il
join è tornato a 760/760. La parte che conta: **il join non ha fallito in
silenzio**, la guardia ha rifiutato la raccolta finché il conto non tornava.

### 12.3-ter · Tre leghe (01/08/2026): 1.139 partite, 35.339 righe

Terza raccolta: **La Liga 2025-26** — 11.953 righe, **380/380 partite**, 599
giocatori (la più ricca delle tre). Join **760/760** e coerenza gol **760/760**
contro il nostro snapshot.

| raccolta | righe | partite | giocatori | join |
|---|---:|---:|---:|---|
| Serie A 2025-26 | 11.894 | 379/380 | 584 | 758/758 |
| Premier 2025-26 | 11.492 | 380/380 | 537 | 760/760 |
| **La Liga 2025-26** | **11.953** | **380/380** | **599** | **760/760** |
| **totale** | **35.339** | **1.139** | — | **2.278/2.278** |

**⚠️ Per la Liga non esiste un report dell'utente**: il terzo file caricato era
di nuovo quello della Premier. La verifica è interamente della sessione, senza
un secondo parere con cui incrociarla.

**Un'anomalia ridimensionata misurandola meglio (R4/R7).** Il controllo
«squadra-partita sotto 985 minuti», che su Serie A e Premier dava 0 casi senza
espulsione, sulla Liga ne dava 2. Rifatta la domanda sul deficit rispetto ai 990
minuti attesi, su tutte e tre le raccolte: **2.077 su 2.086 (99,57%) stanno
esattamente a 990**, i 9 residui hanno deficit 1-12 e sono **distribuiti su tutte
e tre le leghe**. Non è arrotondamento per sostituzione (correlazione col numero
di cambi: **+0,0004**). È un'imprecisione minore della fonte sullo **0,43%** dei
team-partita — e **la soglia dei 985 usata dai report era arbitraria**: faceva
sembrare la Liga diversa quando il fenomeno è comune.

**Gli alias, e cosa aspettarsi dopo.** Il join partiva da 420/760 per **5 nomi su
20**. Due famiglie che **si ripeteranno su Bundesliga e Ligue 1**: i nomi sono
**italianizzati** (`Barcellona`, `Siviglia`, `Maiorca` — poi *Bayern Monaco*,
*Colonia*, *Marsiglia*, *Lilla*) e le **abbreviazioni portano il punto**
(`Ath. Bilbao`, `Atl. Madrid`). Tutti in `TEAM_ALIASES`.

### 12.4 · Il limite che non si supera con questi dati

**Una lega, una stagione.** Le altre 4 leghe e le 8 stagioni precedenti restano
scoperte, e nessuna fonte aperta le copre (ecosistema aperto: **12,55%**, `+0`
partite in tre ricerche — `docs/CACCIA_EVENT_DATA.md` §2). Quindi anche un esito
positivo **non** produrrebbe una feature utilizzabile in produzione sul perimetro
completo: produrrebbe la **prova che vale la pena procurarsi il dato**, che è una
cosa diversa e va detta così.

## 13 · Il database CARRIERE — disegno a strati (31/07/2026)

> **Strato 1 COSTRUITO** (`src/data/careers.py`, 12 test). Strato 2 **non**
> costruito: dipende da una decisione dell'utente, vedi §13.4.

### 13.1 · La popolazione: 7.709 giocatori, ≥1 presenza (non «≥1 stagione»)

> ⚠️ **AGGIORNATO al 02/08/2026: sono 7.710.** Il +1 è Alessandro Romano, che
> ha esordito in Serie A il 06/01/2026 e che la fonte primaria delle presenze
> non registra: la sua presenza arriva da `data/presenze_integrate.csv`, letta
> dalla nostra raccolta diretta.it e confermata da una fonte esterna. Il numero
> si è mosso perché è cambiato il **dato**, non la regola — chi ha giocato in
> Serie A appartiene alla popolazione, e prima ne restava fuori per un buco
> della fonte. Il vecchio 7.709 resta qui sotto perché è il numero con cui la
> soglia è stata *decisa*.


Definizione adottata: **ogni giocatore con almeno UNA presenza in una delle 5
leghe dal 2017-07**. Sono **7.709**.

| soglia | giocatori |
|---|---:|
| ≥ 1 presenza | **7.709** ← adottata |
| ≥ 5 | 6.308 |
| ≥ 10 | 5.714 |
| ≥ 19 (~«una stagione») | 4.870 |

**Perché ≥1 e non «una stagione»**: (a) «una stagione» richiede una soglia
arbitraria di partite, ≥1 presenza è oggettivo e riproducibile; (b) alzare la
soglia escluderebbe **proprio i giocatori di rotazione** — quelli la cui
presenza varia di più da una partita all'altra, cioè esattamente il segnale che
un database di giocatori dovrebbe catturare. Sarebbe una selezione avversa; (c)
i 2.839 giocatori in più costano solo tempo di calcolo.

### 13.2 · ⭐ Lo strato 1 era già in casa, e nessuno l'aveva guardato

**`appearances.csv` copre 48 competizioni, non 5.** È il fatto che cambia il
disegno, e contraddice quanto il piano dava per scontato:

- oltre alle nostre 5, i **massimi campionati** di Turchia, Olanda, Portogallo,
  Belgio, Russia, Grecia, Scozia, Danimarca, Ucraina;
- le **coppe europee** (CL/EL/Conference + qualificazioni);
- le **coppe nazionali** e le supercoppe, la **Coppa d'Africa**, il **Mondiale
  per club**.

Risultato: **89.625 righe di carriera** (giocatore × club × competizione ×
stagione), mediana **8 tappe** a testa, **costo zero**, nessuna rete.

| | |
|---|---:|
| giocatori con **storia precedente** al debutto nelle 5 leghe | **4.834** (62,7%) |
| con almeno una presenza **fuori** dalle 5 leghe | **6.580** (85,4%) |
| **senza** alcuna storia precedente | 2.875 (37,3%) |

### 13.3 · ⏱️ Il nodo R8: perché l'API non è una colonna

«Presenze in carriera» è la feature che **per sua natura contiene il futuro** —
la carriera di un giocatore comprende anche le partite che deve ancora giocare.
Usarla per una partita del 2019 significa sapere cosa farà nel 2024, e un test
che controllasse solo i totali **passerebbe lo stesso**.

Per questo l'API sicura non è una colonna ma una funzione:
**`career_before(as_of)`** conta solo ciò che precede *strettamente* quella
data. Tre test lo verificano: che nessuna partita `>= as_of` entri, che la
carriera sia **monotona** nel tempo, e che il confine sia `<` e non `<=` — la
partita del giorno stesso è quella da prevedere e non può entrare nella propria
feature.

**E `censored_left`**: chi ha la prima presenza al bordo del dataset
(**1.045 giocatori**) non è un esordiente, è un **troncato** — i suoi totali
sono un limite inferiore. È lo stesso errore che l'audit ha misurato costare
**155 allenatori su 496** (§D.2 di `AUDIT_FONTI_GIOCATORI.md`, «Ancelotti
debutta in Serie A nel 2018»).

### 13.4 · Lo strato 2 (Wikipedia) — cosa aggiungerebbe, e la decisione aperta

Lo strato 1 **non** copre tre cose:

| buco | dimensione |
|---|---|
| tutto ciò che precede il **2012-07-03** | **1.045** giocatori censurati al bordo |
| le **seconde divisioni** (nessuna nel dataset) | non misurato |
| i campionati **extra-europei** | non misurato |

Il metodo per riempirli è misurato e funziona (**infobox** di Wikipedia,
**99,7%** di copertura sui 333 già testati — `AUDIT_FONTI_GIOCATORI.md` §B), ma
**non è stato eseguito su nessun giocatore** e ha un prezzo che non è tecnico:

> ⚠️ **Wikipedia e DBpedia sono CC BY-SA: share-alike VIRALE.** Il repo è
> **pubblico**, quindi importare quelle carriere **vincola la licenza del
> progetto** — e questa è la decisione **A3/A5** di `lavoro_aperto.md` §7-bis,
> ancora aperta. Va presa **prima** dell'importazione: dopo è molto più
> scomodo. *(Rendere il repo privato la scioglie, perché lo share-alike scatta
> sulla distribuzione.)*

**Ordine consigliato**: usare prima lo strato 1 — c'è, è gratis e copre l'85%
dei giocatori con almeno una tappa esterna — e **misurare quanto lo strato 2
aggiungerebbe davvero** su un campione, prima di pagarne il costo di licenza.
È il principio §1.3 del `CLAUDE.md`: la versione economica prima
dell'investimento.


---

## 14 · Nazionali e coppe: disegno deciso il 02/08/2026

Sessione di ragionamento con l'utente, dopo che il ponte statistiche↔`player_id`
è arrivato al 100%. Qui stanno le **decisioni di struttura** e — altrettanto
importante — le **premesse che si sono rivelate false prima di spendere**.

### 14.1 · Due premesse cadute (misurate, non discusse)

**(a) «Il passo 0 è procurarsi la lista delle nazionali».** Non serve: il blocco
`International career` dell'infobox Wikipedia è **già nella nostra cache**. Il
parser lo tratta come marcatore di *fine* (`INTESTAZIONI_FINE`) e lo scarta,
ma il testo è stato scaricato. Misurato su 400 pagine campionate: **62,3% ha il
blocco**, nella stessa forma del blocco club —

```
2011–2012 | Hungary U19 |  5 | (0)
2014–2024 | Hungary     | 70 | (2)
```

Anni, nazionale, presenze, gol, **e le giovanili** (U19/U20/U21). Estrarlo costa
**zero richieste di rete**: è lo stesso regalo dei Q-id Wikidata (§13). E la
lista delle nazionali ne esce come *sottoprodotto già filtrato sui nostri
giocatori*, invece che come elenco di 210 federazioni di cui usiamo un terzo.

**(b) «Per le coppe europee avremo club nuovi che non abbiamo».** Falso, e di
molto. Le coppe sono **già dentro `appearances`**:

| competizione | presenze |
|---|---|
| Europa League | 55.834 |
| Champions League | 49.536 |
| qualificazioni EL | 19.460 |
| qualificazioni CL | 10.580 |

**415 club europei distinti, 415 con un nome nel registro, ZERO mancanti.** E la
sola 2025-26 ha già 14.450 presenze, 122 club, 2.243 giocatori. Quello che
manca non è l'ossatura: sono le **statistiche di dettaglio** partita per
partita, che player-scores non ha e diretta.it sì.

⭐ **Conseguenza operativa**: per le coppe europee il ponte funzionerà
**esattamente come per i campionati**, senza codice nuovo. Le due fonti
elencheranno gli stessi giocatori per ogni (data, club), quindi l'eliminazione
di `player_identity.collega_per_eliminazione` ha il suo insieme di candidati.
Per le nazionali **no**: lì la controparte non esiste (vedi §14.4).

### 14.2 · L'identità delle squadre: `team_id` con `tipo`

Il problema posto dall'utente: una nazionale non può essere un `club_id`.
Giusto, ma la soluzione non è un secondo spazio di identificatori.

**Scelta: UN registro `data/squadre.csv`**, chiave `team_id`, con:

| campo | cosa | note |
|---|---|---|
| `team_id` | chiave universale «chi ha giocato» | club: **uguale al `club_id`** (leggibilità); nazionali: **negativo** |
| `tipo` | `club` / `nazionale` / `nazionale_giovanile` | il guard sta qui, in un posto solo |
| `club_id` | l'id player-scores | **solo** per `tipo=club`, altrimenti vuoto |
| `qid` | ancoraggio Wikidata | esterno e stabile |
| `paese`, `citta`, `lat`, `lon` | geografia | serve al calcolo dei viaggi (§14.3) |

**Perché una chiave sola e non due.** Una riga-partita ha UNA colonna «squadra
di casa». Con due spazi servirebbero `home_club_id` + `home_nazionale_id` e ogni
query diventerebbe un `coalesce`: il tipo di complicazione che si dimentica una
volta e sbaglia per sempre.

**Perché i negativi.** Un `club_id` è sempre positivo. Se qualcuno unisce per
sbaglio `team_id` a `club_id`, con i negativi non trova **nessuna riga** — un
buco visibile. Con un intervallo alto e positivo troverebbe righe **sbagliate**,
che è il modo peggiore di fallire (R6: non è il `NaN` il pericolo, è il finto
pieno). Qui la scelta rende l'errore *impossibile*, non solo improbabile.

⚠️ **Il pericolo vero non è l'id: è l'aggregazione.** «Per quanti club ha
giocato» non deve contare l'Italia. Quindi il filtro NON può vivere nella testa
di chi scrive la query: le funzioni di carriera devono escludere `tipo≠club`
**per default**, e chi vuole le nazionali le chiede esplicitamente.

### 14.3 · Il viaggio: la fetta economica ad alto valore

Meccanismo, come formulato dall'utente e qui precisato: si incrociano **dove
vive** (città del club) e **dove va a giocare** (città della partita di
nazionale), più le **date** delle partite di club prima e dopo la finestra —
così si ottengono insieme i chilometri, i fusi orari attraversati e il riposo
reale.

Perché vale la pena prima delle statistiche individuali:

1. è **informazione che i dati di club non contengono**. Le Fasi 4c-33 hanno
   chiuso riposo/congestione/forma come rumore, ma erano tutte misurate *dentro*
   il campionato: un brasiliano dell'Arsenal fa ~20 ore di volo due volte a
   finestra, un francese del PSG prende un treno, e questa differenza nel
   dataset attuale **non esiste**;
2. è dato **`pre`** (R8): noto quando esce il calendario, quindi utilizzabile
   per *prevedere* invece che per raccontare;
3. non richiede **nessuna** statistica partita per partita — solo calendario,
   convocazioni e geografia.

⚠️ **L'entità da raccogliere è la CONVOCAZIONE, non la nazionale.** E i **non
convocati contano quanto i convocati**: sono il gruppo di controllo senza cui si
misura solo che i convocati sono i giocatori più forti. Li abbiamo già gratis,
perché abbiamo le rose complete dei club.

### 14.4 · La difficoltà nota in anticipo

Per le nazionali **l'eliminazione non funziona**. Coi club reggeva perché le due
fonti elencavano gli stessi 14-18 giocatori per partita; per le nazionali
player-scores non ha alcuna partita, quindi non c'è insieme di candidati da cui
eliminare. La leva sostitutiva è la **nazionalità**, che restringe il campo a
poche centinaia di persone, ed è su Wikidata (`P1532`) sugli stessi Q-id già
estratti.

### 14.5 · Avvertenza sul campione (scritta PRIMA di spendere)

Il confronto club↔nazionale **su una stagione sola non concluderà nulla** — la
stessa lezione della Fase 131:

| | partite per giocatore, 2025-26 |
|---|---|
| club | ~35-50 |
| nazionale | ~10-15 (ed è stagione di Mondiale, cioè il massimo) |

Dieci partite per giocatore, con avversari, compagni e sistemi diversi, non
bastano a dire «si comporta diversamente in nazionale». Il dato va raccolto —
costa poco e si accumula — ma **l'analisi va messa in conto come pluriennale**.
Il valore immediato è il *collegamento*, non la conclusione.

### 14.6 · Arbitri e allenatori — stato, per non ricercarlo di nuovo

L'utente chiede se serva un database di allenatori e arbitri. **Sì, e c'era
già**: è in questo stesso documento dal 29/07/2026 (il titolo lo dice, e l'audit
§11 copre **32 voci allenatore + 25 arbitro** oltre alle 61 giocatore).

Quello che manca non è il piano, è **l'importazione**: la fonte valutata è
`games.csv` di `davidcariboo/player-scores`, che dà arbitro **e** allenatore al
**>99,7%** anche su CL/EL/Conference. ⚠️ **Non è fra i file che abbiamo**:
`files/player_scores/` contiene solo `appearances`, `club_names`, `clubs`,
`player_valuations`, `players`. Va scaricato.

📌 **Da ricordare** (richiesta esplicita dell'utente, 02/08/2026): quando si
apriranno le coppe e le nazionali arriveranno **allenatori nuovi** (i ct) e
**arbitri nuovi** (internazionali) che nessuna delle nostre fonti attuali copre.
Vanno trattati con lo stesso disegno di §14.2: registro proprio, tipo esplicito,
e **niente** riuso di un id che significa un'altra cosa.

### 14.7 · Ordine di lavoro concordato

1. **Nazionali, strato presenze** — dal blocco `International career` in cache,
   costo zero di rete. Dà lista nazionali + presenze + gol + giovanili;
2. **Registro squadre** (`team_id`/`tipo`) — prima di importare qualunque
   partita di nazionale, altrimenti si sceglie la chiave sotto pressione;
3. **Calendario + convocazioni + geografia** → il viaggio;
4. **Statistiche individuali di nazionale**, partita per partita, come per i
   club — collegate allo stesso `player_id`;
5. **Coppe europee**: le statistiche di dettaglio si innestano sull'ossatura che
   già esiste, riusando `collega_per_eliminazione` senza codice nuovo.
