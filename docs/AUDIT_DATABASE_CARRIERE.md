# Audit del database carriere (01/08/2026)

> **Verbale integrale** di un lavoro a 10 agenti: 6 analisi indipendenti su tre
> fronti (omonimi, aggancio dei club, audit avversariale di codice/dati/uso),
> poi una verifica scettica che ha **rieseguito ogni prova**. Dove lo scettico
> ha corretto un numero o una gravità **vale la sua versione**; due rilievi
> sono stati refutati e non compaiono fra i difetti.
>
> **72 rilievi grezzi → 45 confermati.**
>
> ⚠️ Ogni numero dello strato Wikipedia vale **alla sua data**: la raccolta era
> attiva durante l'audit. I *tassi* sono stabili fra le istantanee, i conteggi
> assoluti no.
>
> **Cosa è già stato corretto** (stesso giorno, subito dopo l'audit):
> la **verifica d'identità** contro gli omonimi (§1.1-1.3), i tre **falsi
> positivi** dell'aggancio club (§1.5) e il **non-aggancio delle riserve**.
> Il resto è nella lista dei prossimi passi, §6.


**Data:** 1 agosto 2026, ore 01:41
**Oggetto:** `src/data/careers.py`, `wikipedia_careers.py`, `club_matching.py`, `player_stats.py`, i loro test e i dati che producono.
**Metodo:** 6 analisi indipendenti, poi una verifica avversariale che ha rieseguito ogni prova. **Dove lo scettico ha corretto un numero o una gravità, vale la sua versione**; due rilievi sono stati refutati e non compaiono fra i difetti.

> ⚠️ **Ogni numero dello strato Wikipedia è valido solo alla sua data.** La raccolta era attiva durante l'audit: il deliverable è passato da 16.483 righe (23:43 del 31/07) a **54.001 righe / 6.007 giocatori** (01:30 del 01/08). I tassi (percentuali) sono stabili fra le istantanee; i conteggi assoluti no. Ho segnalato l'istante di ogni misura.

---

## 1. COSA NON VA — in ordine di gravità

### 🔴 ALTA

#### 1.1 · Pagine Wikipedia di un'altra persona, già nel deliverable versionato
**Cosa succede.** `fetch_player` costruisce l'URL dal nome (`nome.replace(' ','_')`, poi i suffissi `(footballer)` e `(soccer)` in caso di 404) e accetta la prima pagina non-404. **Non verifica mai** che la pagina parli di quel giocatore. `load_database()` ci attacca sopra il `player_name` dello strato 1, quindi a valle si legge «Stefan Mitrović, Stella Rossa 2022-2024» e sembra un dato.

**Il numero.** Confrontando `span.bday` dell'infobox con `players.date_of_birth`:

| istantanea | pagine | bday discordi | **persona sbagliata** | tasso | tappe fabbricate |
|---|---|---|---|---|---|
| 31/07 23:43 | 1.301 | 7 | 2 | 0,154% [0,042–0,559] | 21 |
| 01/08 ~01:00 | 5.158 | 45 | **13** | **0,252%** | 118 |
| 01/08 ~01:30 | 5.589 | 50 | **15** | **0,268%** | 111 tappe, 6.340 presenze |

Il tasso **non si muove** fra le istantanee: non è un incidente, cresce linearmente con la raccolta. Casi: Pelé (il pid 99189, nato 1991, riceve Bauru 1953 / Santos 1956 / New York Cosmos 1975), Quini, Luis Suárez, João Moutinho (692 presenze fantasma), Idrissa Gueye, Javi Martínez, Ximo Navarro, Stefan Mitrović, Antoñito, Uche Agbo, Babacar Gueye, Pablo Ibáñez, Marcus Pedersen, Aaron Ramsey, Abdoulaye Faye, Marquinhos, Filip Jørgensen, Vitinha.

**È R6 puro:** nessun NaN, nessun errore, carriere vere e coerenti — di un'altra persona.

**Correzione.** Verifica d'identità **obbligatoria nel fetcher**: `span.bday` contro `players.date_of_birth`, con esito scritto in colonna (`identita_verificata`), mai un filtro silenzioso. Costo: **zero richieste in più** (il bday è nella pagina già scaricata), copertura **5.181/5.181 = 100%** delle voci di calciatore. Espellere intanto le 111-118 righe dei 13-15 `player_id` e registrarlo in `data/correzioni_dichiarate.csv` (R3).
⚠️ **Non un gate secco sulla data**: 32 delle 45 discordanze sono la persona *giusta* con anagrafica contestata (Chancel Mbemba 1988 vs 1994 con 5 club su 5 coincidenti, Mehdi Lacen mese invertito, Kara Mbodj 11 giorni). Serve lo stato `quarantena` con verifica-club di supporto.
⚠️ **Non il gate «almeno un club in comune»**: eseguito, boccia 34 giocatori di cui ~29 corretti (i giocatori del Mainz, perché «Mainz 05» è un aggancio *ambiguo* e non riceve mai un `club_id`). ~85% di falsi positivi.

#### 1.2 · Il caso peggiore non è coperto dal fix già applicato: l'omonimo che è *primary topic*
**Cosa succede.** `/wiki/Ximo_Navarro` (bday 1988-09-12) e `/wiki/Andrea_Costa` (bday 1851-11-29, l'anarchico) sono pagine vere, con infobox, di un'altra persona, raggiunte dal **titolo nudo**. Il commit `ed84c52` ha chiuso il ciclo sui suffissi, ma non tocca questo caso: il titolo è identico a quello giusto.

**Il numero.** **12 dei 13 omonimi entrati vengono dal titolo nudo**, uno solo dal suffisso. Nessuna euristica sul titolo può risolverlo.

**Correzione.** È la stessa del §1.1 (bday), che è l'unica difesa che copre anche questo caso. Strutturalmente: risolvere via **Wikidata** (P569 data di nascita + P54 squadre) invece che via titolo.

#### 1.3 · Il tasso misurato è un **limite inferiore**: il rischio è in ciò che deve ancora essere raccolto
**Cosa succede.** La raccolta procede per presenze decrescenti, e dentro un gruppo di omonimi il più presente è quasi sempre il proprietario del titolo nudo — cioè quello che riceve la pagina *giusta*. Finora abbiamo raccolto i proprietari.

**I numeri.**

| strato | pagina sbagliata | tasso |
|---|---|---|
| ambiguo **non-primo** del gruppo | 3 / 5 | **60,0%** [23,1–88,2] |
| ambiguo primo del gruppo | 4 / 36 | 11,1% |
| nome unico | 6 / 5.140 | 0,117% |

Fisher non-primi vs unici: **p = 3,7·10⁻⁸**. Tentati finora: 153 primi / 64 non-primi. **Da fare: 315 primi / 592 non-primi.** Proiezione: ~28 carriere sbagliate in più.

⚠️ **Crepa dichiarata**, che taglia il ragionamento a metà: **6 dei 13 omonimi hanno un nome UNICO** nel nostro dataset. Il tetto strutturale di 656 giocatori (2,22% dei candidati, `Σ(g−1)` sui 468 gruppi) **non è un tetto**: quasi metà degli errori nasce fuori, perché lo spazio dei nomi di Wikipedia è molto più grande dei 50.149 di `players.csv`. Rafforza la conclusione operativa (attivare la conferma *prima* di proseguire), indebolisce la stima quantitativa.

#### 1.4 · Il buco della raccolta non è casuale: è brasiliano e iberico
**Cosa succede.** Il 12,20% dei giocatori fallisce, ma non a caso: i mononimi (Pedro, Marcelo, Danilo, Fred, Neto, Vitolo) finiscono su pagine di disambigua e producono zero righe.

**Il numero.** Tasso di fallimento per cittadinanza (≥25 osservazioni): **Brasile 48,5% · Spagna 27,7% · Portogallo 24,2% · Serbia 21,4%** contro **Olanda 0,7% · Germania 3,8% · Francia 3,4% · Italia 3,9%**. **χ² = 696,8, dof = 38, p = 4,6·10⁻¹²²**.

**Perché è alta.** È l'unico rilievo che, se ignorato, **avvelena una feature** invece di sporcare qualche riga: una copertura che dipende dalla nazionalità non è un dato mancante, è una **confondente** — e la nazionalità correla con lega, età, valore rosa e stile di gioco. Oggi costa zero dichiararlo in `docs/DATI.md`; costa molto scoprirlo dopo un backtest.

#### 1.5 · Tre agganci di club dichiarati «univoco» puntano al club sbagliato
**Cosa succede.** `club_matching` promette che «un aggancio ambiguo non si sceglie a caso: si lascia vuoto». Il rischio che la promessa non copre è il **candidato unico e sbagliato**, che esce come *certezza*.

| nome wiki | agganciato a | doveva essere | tappe (01/08) | conferme contro lo strato 1 |
|---|---|---|---|---|
| `Brest` | 6131 **Dynamo Brest** (Bielorussia) | 3911 Stade Brestois 29 | **108-113** | **0 / 108** → 80/108 col club giusto; 73 dei 94 giocatori hanno presenze reali al 3911 e **zero** al 6131 |
| `PAOK` | 101813 **PAOK Kristonis** (dilettanti) | 1091 «Panthessalonikios Athlitikos Omilos Konstantinoupoliton» | **50** | **0 / 50** → 44/50 col club giusto; il 101813 non compare **mai** in `appearances` (club_id penzolante) |
| `Bilbao Athletic` (la squadra B) | 621 **Athletic Bilbao** (prima squadra) | *assente* | **32-50** | `normalizza` torna un frozenset: `{bilbao,athletic} == {athletic,bilbao}` |

Cause: `{brest} ⊆ {dynamo,brest}` mentre lo Stade Brestois normalizza in `{stade,brestois}`; il nostro dataset usa per la Grecia la ragione sociale traslitterata per esteso (per lo stesso motivo `AEK Athens`, `OFI`, `Volos` non trovano **nessun** candidato).

**Nota sulla gravità.** Lo scettico ha confermato **alta** su Brest e PAOK presi singolarmente (errore deterministico al 100% delle occorrenze, etichettato «univoco», dentro il database — R6 da manuale) e **media** sull'aggregato (213 tappe = 0,42%, nessun consumatore a valle). Tengo alta per il determinismo, dichiarando il volume.

**Correzione.** Alias verificati `'Brest'→'Stade Brestois 29'` e `'PAOK'→ragione sociale`; `Bilbao Athletic` → **assente** (non la prima squadra: nel nostro dataset le riserve non esistono).
⚠️ L'alias su Brest **non è a rischio zero**: il Dynamo Brest esiste e ha 10 righe in `appearances` — per un giocatore bielorusso l'alias sbaglierebbe in silenzio. ⚠️ `AEL` è già ambiguo (AEL Limassol vs AEL Kalloni): mapparlo a AEL Larissa introdurrebbe un errore nuovo al posto di un vuoto onesto.

#### 1.6 · I cartellini rossi della stagione 2025-26 sono un finto pieno: 0 significa «non registrato»
**Cosa succede.** La colonna `red_cards` è piena di zeri, senza un solo NaN, per l'intera stagione in corso.

**Il numero.** **7 osservati contro 551,7 attesi**, IC95 [506, 598], **p = 8·10⁻²²⁵** (tasso per-minuto delle 13 stagioni precedenti applicato ai 10.039.282 minuti della 2025-26). Nelle cinque leghe del progetto il conteggio è **esattamente zero** (ES1 0, FR1 0, GB1 0, IT1 0, L1 0, contro 58/46/26/41/28 nel 2024-25). L'ultimo rosso dell'intero dataset è del **2026-01-03**, contro una data massima 2026-06-28. I 7 superstiti stanno solo in KLUB e AFCN.

**Non è un artefatto della statistica scelta:** i gialli della stessa stagione sono presenti in *tutti* i mesi (592–2.254 al mese), quindi la stagione è caricata e le righe ci sono — manca solo quella colonna.

**Esiste già un consumatore reale**: `scripts/_run_fase124_diffidati.py`. E la 2025-26 è la stagione da cui parte il test prospettico (Fase 78).

**Correzione.** `red_cards` a **NaN** oltre la data dell'ultimo rosso reale (o colonna di copertura per-stagione-per-colonna), più un **test di regressione** che confronti il tasso per-minuto di ogni colonna-conteggio con la banda delle stagioni precedenti e fallisca sotto −3 sd.
⚠️ **Il contorno sui gialli va lasciato cadere**: il −7,9% è per-minuto, e la 2025-26 ha un mix di competizioni diverso (KLUB e AFCN nuove, minuti al massimo storico) — il confronto non è omogeneo. **Non misurato**: se ci sia sotto-registrazione anche lì.

---

### 🟠 MEDIA

#### 1.7 · `season_of` etichetta la coda COVID 2019-20 come «2020-21» — l'opposto di ciò che il suo docstring dichiara
Il docstring dice che il taglio a luglio serve a evitare che «la coda COVID finisca nella stagione dopo». `season_of('2020-08-02')` restituisce **`'2020-21'`**: la stagione dopo. Il taglio non evita l'errore, lo produce.
**Numeri:** 10.509 partite-giocatore della 2019-20 in 12 competizioni (IT1 fino al 2/8, GB1 26/7, ES1 19/7, CL 23/8, EL 21/8…); **2.770 righe aggregate «2020-21» contaminate = 18,77%** di quelle righe, di cui **1.100 interamente 2019-20**. Sul totale: 1,40% delle 197.812 righe.
**Onestà:** verificato che **nessuna delle 48 competizioni è ad anno solare** e il gap mediano attorno al 1° luglio è ≥40 giorni ovunque → il difetto è localizzato al **solo 2020**.
**Correzione (costo zero):** correggere il docstring e dichiarare il 18,8% misto. L'alternativa (taglio per-competizione dalla pausa estiva vera) è più invasiva e cambierebbe la costante 197.812 dei test.

#### 1.8 · La regola del sottoinsieme genera falsi positivi: l'unicità è verificata su 3.171 club, non sul mondo
**Numeri:** 1.731 nomi distinti agganciati univocamente, di cui **464 (26,8%) per sottoinsieme** — **7.397 tappe = 21,7%** di tutti gli agganci riusciti. Audit a mano su 60 estratti a caso: **8 sbagliati = 13,3%**, IC95 Wilson [6,9–24,1] (compatibile col 10,0% [4,7–20,5] della prima misura). Casi: `Molde 2`→Molde FK (riserve→prima squadra), `Emirates`→**United Arab Emirates** (nazionale), `FC Malmö`→Malmö FF, `Almagro`→San Lorenzo de Almagro, `CSV '28`→CSV Apeldoorn, `Sigma FC`→SK Sigma Olomouc, `Vancouver FC`→Vancouver Whitecaps, `VfL Ulm`→SSV Ulm 1846.
**Ordine di grandezza:** ~700–1.000 tappe agganciate al club sbagliato, **~1,6–2% del database**. È il difetto più grande in volume di tutto l'audit.
⚠️ **È un audit a giudizio umano**, dichiarato come tale: meno solido delle misure oggettive.
**Correzione misurata e a saldo positivo:** **tenere le cifre** in `normalizza` (oggi `not t.isdigit()` le butta) → univoco 34.123→34.221 (+98), ambiguo 1.264→1.082 (−182); le 102 tappe che «perde» sono in schiacciante maggioranza riserve numerate che erano collassate per errore (Dynamo-2 Kyiv, Shakhtar-3 Donetsk, Krasnodar-2, Portland Timbers 2). Più: marcare l'esito `univoco_sottoinsieme` invece di `univoco`, così a valle si può scegliere se fidarsi.

#### 1.9 · La censura a sinistra rende la feature non confrontabile fra stagioni
Il dataset comincia il 2012-07-03: nel 2017-18 il **40,5%** dei giocatori di Serie A ha la prima presenza al bordo (6,4% nel 2024-25). La feature «esperienza media della squadra» passa da **108,4 a 162,9 (+50%)** attraverso la finestra.
**La prova che è artefatto e non invecchiamento delle rose** (misurata dallo scettico, era prosa nell'analisi): la stessa feature a **finestra mobile di 2 anni è piatta** — 50,1 → 54,0 (+7,8%) — nello stesso identico campione. E sui soli **non** censurati la cumulativa deriva ancora di più (70,6 → 150,4, +113%): non è un problema del sottoinsieme censurato, è la finestra di osservazione che cresce per tutti → **`censored_left` da solo non basta**.
**Correzione:** normalizzare dentro la stagione (rango/z-score) **oppure** usare la variante a finestra mobile, che è validata piatta. Esporre `days_observed` in `career_before`.

#### 1.10 · `career_before()` omette gli esordienti invece di restituirli con zero
Chi non ha presenze precedenti **non compare nell'indice**. Il consumatore naturale scrive `undici.merge(cb, how='left').mean()` e pandas, saltando i NaN, **elimina gli esordienti** invece di contarli 0.
**Numeri:** 6.321 giocatori con esordio assoluto in una delle 5 leghe; **4.246 club-partita colpiti su 50.409 = 8,4%**; gonfiaggio medio **+6,6 presenze** (mediana +5,4, max +76). Verificato alla radice: su una data campione i giocatori in campo sono 247, `career_before` ne restituisce **244**.
Il difetto distorce **nella direzione opposta** a quella che la feature dovrebbe segnalare.
**Correzione:** quando `player_ids` è passato, fare `reindex` con zeri e colonna `esordiente=True`. Non rompe nulla: oggi quel parametro è solo un filtro e nessuno lo usa.

#### 1.11 · Le nazionali entrano nel database delle carriere **di club**
`FIWC` (Mondiale 2026, 2.251 righe, 48 «club» chiamati Brazil, Mexico, Morocco…) e `AFCN` (Coppa d'Africa, 776 righe, 22 nazionali) diventano **1.201 tappe per 1.125 giocatori**. `career_before` conta `clubs_before = nunique(player_club_id)`: fra il 1° giugno e il 1° luglio 2026, **712 giocatori guadagnano +1 club** (media 2,68→3,68) in un mese in cui non si è giocata una partita di club.
**Dato nuovo dallo scettico:** l'effetto non è solo il Mondiale (fuori finestra) — la **sola Coppa d'Africa dà +1 club a 487 giocatori dentro la stagione 2025-26**, cioè dentro il perimetro modellato. Verificato che siano solo 2 competizioni su 48.
**Correzione:** `COMPETIZIONI_NAZIONALI = ('FIWC','AFCN')` + colonna `nazionale`, esclusa di default da `career_before`.

#### 1.12 · «almeno un club in comune» sembra una conferma e non lo è
Riprodotto con un placebo costruito da zero (stessa cittadinanza, ±3 anni, 5.138 coppie): il criterio conferma il **10,53%** [9,72–11,40] degli accoppiamenti *sbagliati*, contro lo **0,234%** [0,134–0,408] del confronto sulla data. Rapporto ~45×.
La causa è strutturale, non un difetto dell'aggancio: **i compagni di squadra condividono i club**. Contro-esempio vivo: Javi Martínez (pid 471474) condivide «Osasuna» con la pagina del centrocampista del Bayern pur essendo un'altra persona.
**Conseguenza:** mai in OR con la data (porterebbe il falso positivo da 0,23% a ~10,5%). Solo come **ripiego** quando la data non è confrontabile (0,1% dei casi), con soglia forte.

#### 1.13 · La scelta del candidato su una pagina di omonimi **non** è una conferma
La regola «prendi il candidato il cui anno di nascita coincide» risolve il 91,96% delle pagine-indice e *sembra* una prova d'identità. Non lo è: con un giocatore **sbagliato** (stessa nazione, ±3 anni) pesca comunque un candidato nel **17,26%** [15,96–18,64] dei casi.
⚠️ **Numero corretto dallo scettico:** l'analisi dichiarava 31,67%, l'IC lo esclude. La sostanza non cambia (17% contro 0,23% = 74× più permissiva), ma il numero va scritto giusto nella docstring, o si mette nel repo una cifra non ri-derivabile (§2-bis del CLAUDE.md).
**Correzione:** separazione esplicita — `scegli_candidato()` = **proposta di navigazione**, `conferma_pagina()` = **prova d'identità**. Nessun ramo accetta una tappa senza aver superato la seconda.

#### 1.14 · Nessun test copre la risoluzione dell'identità
39 test verdi fra `test_careers.py` (22) e `test_player_stats.py` (17): coprono struttura, fonte, licenza, taglio temporale, censura e i tre test sull'aggancio dei club. **Nessuno chiede se la pagina sia della persona giusta.** È lo stesso vuoto che il CLAUDE.md §5-bis registra per la regola anti-look-ahead («non aveva nemmeno un test»).
**Correzione (costo quasi nullo, i fixture sono già in cache):** `Andrea_Costa.html.gz` come negativo (bday 1851 → zero tappe), `Stefan_Mitrovic_(soccer).html.gz` come secondo negativo, una pagina con bday coincidente come positivo. Tutti offline.

---

### 🟡 BASSA — l'elenco, con il numero che li ridimensiona

| # | rilievo | il numero che lo tiene in basso |
|---|---|---|
| 1.15 | La vecchia politica dei suffissi fabbricava omonimi (1 su 23) | Fisher contro il titolo nudo **p = 0,056, non concludente**; la vecchia politica spiega **1 dei 13** omonimi (8%); meccanismo già chiuso da `ed84c52`; 22 dei 23 record hanno la data coincidente |
| 1.16 | Il test di coerenza-club è azzoppato dai nomi dei club | A soglia 0,25 segnala 26 casi, 12 veri (precisione 46%). ⚠️ **Metà degli esempi citati era sbagliata**: `ALIAS` contiene già `Rennes→Stade Rennais FC` e `Olympiacos→…`, e `candidati('Rennes')` restituisce quello giusto. Restano validi solo Brest, Volos, PAOK — che sono già §1.5 |
| 1.17 | `"infobox" in html` è un finto pieno (la stringa vive nel CSS) | 39 pagine su 101 `nessun_blocco`, **tutte disambigua**. ⚠️ Tre delle sei pagine citate come prova (Pedro, Danilo, Felipe) hanno una tabella infobox **vera**: la diagnosi non le spiega. **Impatto sui dati: zero righe contaminate** — è un'etichetta sbagliata su un risultato già vuoto. Conta solo se un recupero futuro filtrerà per stato (−7% di pagine recuperabili) |
| 1.18 | Il suffisso `(soccer)` non ha guadagnato nulla | 94 tentativi: 92 404, 1 senza infobox, **1 solo «ok» ed era la persona sbagliata**. Campione = 1 evento, IC [20,7–100%]. E sotto la politica attuale quel percorso è già chiuso |
| 1.19 | `ALIAS` mappa nome→nome, quindi non può disambiguare | Meccanismo reale (`normalizza` del Lokomotiv Mosca in cirillico = `set()` vuoto → non esprimibile), ma **danno oggi = 24 tappe su 54.001 = 0,05%**; tutti e 5 gli ALIAS presenti risolvono univocamente e senza di loro `candidati()` = `[]`. È manutenibilità, non un difetto in essere |
| 1.20 | 43 **nazionali** dentro `club_names` come se fossero club | ⚠️ La premessa «oggi non fanno danni» è **falsa**: `Qatar SC` (club vero) ha token `{qatar}` perché «sc» è stopword → agganciato al club_id 14162 = **nazionale del Qatar**, 8 tappe. Ma 8-9 su 54.001 = 0,02%. La raccomandazione (**non** aggiungere la regola inversa) è sana e verificata: darebbe `Austria Wien`→Austria, `Universidad de Chile`→Chile, `CSKA Moscow`→CSKA 1948 bulgaro |
| 1.21 | Due `ALIAS` collassano le riserve sulla prima squadra | **102 tappe** (`SC Freiburg II` 56 + `Bayern Munich II` 46 = 0,22%) contro **2.961** tappe di riserve lasciate correttamente `assente`. Correzione sicura e verificata: senza gli alias entrambi tornano `[]`. *(Questo rilievo era **duplicato** in due fronti con tre volumi diversi — 43, 79, 102: sono lo stesso difetto misurato in tre istanti.)* |
| 1.22 | 134 tappe con residui di riferimento wiki nel nome (`Werder Bremen [ 4 ]`) | 0,308%, ripartite 102 assente / 29 univoco / 3 ambiguo. **Resa della pulizia misurata: 6 tappe recuperate** (0,013%) — gli altri 96 club non esistono nel nostro indice. Il valore vero è cosmetico (`Antiguoko [2]` e `[3]` contati due volte) |
| 1.23 | `_RE_ANNI` non riconosce il minus U+2212 | **80 righe su 52.919 = 0,151%**: 51 con intervallo collassato (`'2018−2024'`→2018-2018, di cui 4 tappe *aperte* chiuse d'ufficio), 22 senza anno d'inizio (`'–2003'`→2003-2003: l'anno **inventato**), 7 con zeri spaziati. Le due varianti sospettate e **non** materializzate (`'2005–06'`, `'2019–present'`): **0 occorrenze**. Il valore della correzione non è la regex, è la colonna **`anni_grezzi`** |
| 1.24 | `career_before` è cieco allo strato 2 | ⚠️ **Non è look-ahead**: il filtro `date < as_of` non può far entrare futuro; è sotto-copertura del passato, ed è precisamente ciò che `censored_left` dichiara. 8.063 tappe pre-2012 (18,5%), ma ripara solo il **18,6%** dei censurati (951 su 5.114). Includerle *introdurrebbe* look-ahead (grana annuale: «2019» non dice se precede il 3 novembre 2019). Funzionalità mancante, non difetto |
| 1.25 | La grana annuale non è approssimabile | Misura utile e riprodotta (a cavallo del taglio: **53,2%** delle presenze al 2017, **47,1%** al 2019, **38,2%** al 2022; 3.543 tappe aperte con 158.867 presenze al 2026). Ma **nessun codice usa oggi presenze/gol dello strato 2 come feature datata**: è un rischio, non un difetto |
| 1.26 | `test_season_taglia_a_luglio` passa anche col taglio al 1° agosto | Mutazione `month>=8` → **1 failed, 21 passed**, e a cadere è `test_perimetro_default_e_tutto_luniverso` (costante 197.812), non il test che dichiara di guardare il taglio. Mutazione «`player_name` corrotto» → **22 passed**. Ma la suite *intercetta* la regressione (con messaggio inutile): disegno del test, non buco di copertura |
| 1.27 | `load_database(appearances=sottoinsieme)` mescola popolazioni | Con `appearances` = sola Serie A: 8.478 righe strato 1 contro 47.110 strato 2, 68,7% delle righe wiki senza `player_name`. **Difetto latente**: nessun chiamante nel repo passa un sottoinsieme, e le righe orfane si vedono (`player_name` nullo) |
| 1.28 | Colonne omonime con semantiche diverse fra i due strati | `appearances` mediana **4** (stagione×competizione) contro **26** (tappa pluriennale); `season` valorizzata su 197.812 righe e **zero** wiki; `is_top5` dtype object con tre valori. Osservazione di metodo corretta («sommare» è l'errore visibile, «filtrare» quello silenzioso), ma nessuna riga è sbagliata |
| 1.29 | Gli strati si sovrappongono al 90,9% | Sommando: 1.529.017 presenze wiki + 833.182 strato 1 sugli stessi giocatori = **423 a testa**. Ma il numero è una misura vera di una cosa diversa, la colonna `fonte` esiste per distinguerle, e l'avvertenza è già in maiuscolo due volte. Uso scorretto **ipotetico** |
| 1.30 | Manca il ponte snapshot→`club_id` | 0 squadre orfane su 5 leghe, 0 collisioni: funziona. Ma `CLUBS` (riga 45) e `PLAYERS` (riga 46) sono definite e **mai usate**, e le stesse 5 righe esistono già in `player_scores.py`. Richiesta di funzionalità + una costante morta |
| 1.31 | `career_before()` è O(dataset) per chiamata | Misure riprodotte (2,98 s senza precarico, 0,439 s con, **0,41 s** la forma cumulativa su tutte le date, 244 confronti con **0 differenze**). ⚠️ Ma l'estrapolazione era sbagliata di **3,5×**: le date distinte delle 16.111 partite sono **1.658**, quindi il caso realistico costa **12,2 minuti**, non 42,9 — e le «14,2 ore» presuppongono di ricaricare 377 MB a ogni partita. Una feature di carriera si calcola una volta e si salva |
| 1.32 | Manca il ponte nomi-giocatore ↔ `player_id` | Match esatto **3,6%** (diretta scrive «Acerbi Francesco», appearances «Francesco Acerbi»); per insieme di token **95,4% univoco, 0 ambigui** (Premier 93,9%, Liga 92,3%, ambigui 0 ovunque). Assenza di funzione, nessun join errato prodotto. ⚠️ Il match per insieme cancella l'ordine: è lo stesso meccanismo che fonde `Bilbao Athletic` in `Athletic Bilbao` → il contesto lega+stagione va reso **obbligatorio** |
| 1.33 | `load_wikipedia_careers()` preferisce il CSV versionato | Scarto **867 tappe (1,7%)**, non 3.662, e i due file distano **un minuto**: è la fotografia di un processo in corso, non un file che scavalca. Il rischio durevole (raccolta finita senza ri-export) si copre con un `log.warning` |
| 1.34 | Le righe wiki non hanno competizione, stagione né minuti | Riprodotto (NaN al 100% su `season`/`competition_id`/`minutes`/`data_da`; `appearances` 21,6%; aggancio 72,2/2,6/25,2). Ma **è la fonte**: l'infobox non contiene competizioni né date esatte, e il modulo lo dichiara già in tabella. Miglioramento di documentazione |
| 1.35 | L'undici titolare non è ricostruibile da `appearances` | 13 colonne, nessun flag titolare, mediana 14 giocatori per club-partita. Copertura del titolare vero **7,1%** (2.278 squadra-partita: Serie A + Premier + **Liga**, non 4,7%). Limite della fonte, non difetto — e §4 mostra che per aggregati non è il vincolo |
| 1.36 | La rifondazione societaria come causa degli ambigui | I fatti descrittivi reggono (97 nomi con marcatore d'epoca `(-AAAA)`, 50 righe in collisione di token, 24 gruppi) ma **la tesi è refutata di un ordine di grandezza**: le tappe che il *periodo* disambiguerebbe davvero sono **17 su 1.264 = 1,3%**, non «il resto». L'ambiguità vera è omonimia internazionale, che il periodo non risolve |

---

### ❌ REFUTATI — non sono difetti

1. **«Il 3,04% di ambigui è per due terzi falsa ambiguità»** — il fenomeno esiste, la misura e due esempi su tre no. Gli ambigui sono 1.264 su 47.110 (**2,68%**) e quelli con un solo candidato coperto sono **565 = 44,7%**, non 402 = 64,5%. `Ajax Amateurs` **ha** una presenza in `appearances`, quindi la regola binaria «tieni solo i candidati coperti» lascia Ajax ambiguo esattamente come prima; `Aris` ha **tre** candidati coperti, non uno. Soprattutto: `Club Brugge` pesca Cercle Brugge (5.110 presenze) e Club Brugge KV (8.169), `Verona` pesca Hellas (6.516) e Chievo (3.906) — lì la regola sceglierebbe **a caso fra due club veri della stessa città**, cioè rifarebbe il bug «Hellas Verona» che il CLAUDE.md §5 cita come lezione fondativa. La direzione praticabile è una **soglia**, non un binario: con presenze≥20 si risolvono 753 tappe su 1.264 (59,6%), ne restano 206; Brugge e Verona vanno risolti con alias a mano.
2. **«Omoglifi cirillici irraggiungibili da qualunque normalizzazione latina»** — falso. `normalizza` fa `re.sub(r'[^a-z0-9 ]',' ',s)`: la С cirillica viene **cancellata** e il token distintivo sopravvive. `candidati('FC Taganrog')` restituisce la riga; è ambigua per normale omonimia, non per l'omoglifo. E **zero tappe** menzionano Taganrog o Vologda: danno = 0. Le righe con *lettere* non latine sono 4, non 7 (le altre sono l'apostrofo di Newell's, il º e il №). Resta vero un solo caso: il Lokomotiv Mosca (932), unico club dell'indice con token vuoto — 24 tappe — che è già §1.19.

---

### ⚪ Non passati allo scettico (riportati, non verificati)

Nessuno di questi ha una gravità assegnata: sono **non verificati**. Le più utili: le 4 discrepanze anagrafiche che *non* sono omonimi (Mbemba, Lacen, Mbodj, Ideye — da dichiarare in `docs/DATI.md` o la sessione dopo le conta come errori e il tasso passa da 0,25% a 0,54%); 2 pagine assegnate a due `player_id` diversi (Danilo, Marcelo — 0 tappe, ma il meccanismo è dimostrato); 14 partite contate due volte il 26/11/2016 (UKR1/UKRP, +1.972 minuti fantasma); 925 tappe con `presenze = 0`, di cui 284 su tappe aperte e 302 iniziate nel 2025-26 («non ancora», non zero); 161 club-partita delle 5 leghe con <11 giocatori (0,5%); la selezione non casuale del campione wiki (mediana 209 presenze contro 28 della popolazione, nessun raccolto sotto il 36° percentile); le due fonti che si contraddicono nell'1,91% delle coppie (giocatore, anno), di cui il 23% spiegato da Brest+PAOK; `load_wikipedia_careers(solo_ok=...)` parametro morto; `career_before` che alza `TypeError` su un `as_of` tz-aware; le anomalie R4 che **non** sono errori (minuti/presenza fino a 120 = supplementari, 588 righe con più gol che presenze = poker in gara secca, Falcao a 13 anni = vero, 12 coppie prestito+definitivo che collidono sulla chiave naturale).

---

## 2. OMONIMI — il tasso, il placebo, la soluzione

### Il tasso

> **13-15 pagine su 5.158-5.589 = 0,25%–0,27%**
> (prima misura: 2/1.301 = 0,154%, IC95 Wilson [0,042–0,559])

**È basso, e va detto che è basso.** Il difetto è grave per *natura* (righe false in un file versionato, invisibili a ogni controllo di forma) e per *tendenza* (cresce con la raccolta, ed è concentrato in ciò che manca), non per volume: sono **111-118 righe su 54.001 = 0,21%**.

Ma è un **limite inferiore**, e la ragione è strutturale (§1.3): i 592 collidenti non-primi hanno un tasso di errore misurato del **60%** [23,1–88,2] contro lo **0,117%** dei nomi unici, e sono tutti ancora davanti.

### I placebo (R7)

| test | sensibilità (coppie vere) | falsi positivi, placebo **duro** |
|---|---|---|
| **data di nascita, \|Δ\| ≤ 3 giorni** | **99,32%** ⚠️ | **0,234%** [0,134–0,408] |
| ≥1 club in comune | 99,32% | **10,53%** [9,72–11,40] |
| copertura club ≥0,5 | 98,91% | 5,55% |
| ≥2 club in comune | 82,17% | 0,876% |
| *scelta* del candidato su pagina-indice | 91,96% (reale) | **17,26%** [15,96–18,64] |

*Placebo duro* = 5.138 accoppiamenti con giocatori della **stessa cittadinanza, età entro ±3 anni** — il profilo di un omonimo vero, non di un giocatore a caso. Senza questo, «99,77% di sensibilità» avrebbe fatto sembrare il club una prova forte quanto la data.

⚠️ **Correzione dello scettico**: la sensibilità del test-data è **99,32%** (99,24% a tolleranza zero, 99,38% a 7 giorni), **non 99,95%** come dichiarato dall'analisi — che contraddiceva anche la propria proposta (99,60%). La differenza conta: su 5.181 pagine, **45 bday discordi di cui solo 13 persona sbagliata**; le altre 32 sono la persona giusta con data contestata o sbagliata su Wikipedia.

**Perché 3 giorni e non 30:** nel lotto ci sono **due Vitinha portoghesi nati a 31 giorni di distanza** (2000-02-13 e 2000-03-15). La soglia sta fra un rumore misurato di 1 giorno e una collisione reale a 31.

### La soluzione

```
1) |bday_wiki − date_of_birth| ≤ 3 giorni          → CONFERMA        (via='data')
2) data non confrontabile e copertura-club ≥ 0,5   → CONFERMA        (via='club')
3) |Δdata| > 3 giorni ma copertura-club ≥ 0,5      → QUARANTENA      (a mano)
4) altrimenti                                      → RESPINTA, stato 'identita_non_confermata'
```

**Gerarchica, non un OR.** Un OR non può essere più forte del suo ramo più debole: `data OR ≥1 club` porterebbe il falso positivo da 0,23% a ~10,5%.

**Cosa recupera:**
- copertura del test: **5.181 / 5.181 = 100%** delle pagine che producono tappe (le 120 senza bday sono `nessun_infobox`/`nessun_blocco`/404: zero tappe, zero contaminazione possibile);
- scarta le 13-15 pagine sbagliate (111-118 righe);
- mette in **quarantena dichiarata** i ~4-6 casi in cui la carriera coincide e sono le due fonti a dissentire (32 tappe buone che un gate secco butterebbe);
- sulla ricaduta: il **92,7%** dei falliti sono pagine-indice, e la scelta per anno→mese→nazionalità ne risolve il **93,03%** [89,13–95,60] — chiudendo quasi tutto il divario brasiliano-iberico del §1.4.

**Cosa costa in richieste:**
- **la conferma: ZERO.** Il `bday` è nella pagina già scaricata, e la ripulitura di ciò che c'è oggi gira interamente sulla cache HTML su disco;
- **la ricaduta sulle pagine-indice: +1 richiesta** per il ~10% dei giocatori che ci passa → **1,07 richieste per giocatore** in media *(misura dell'analisi, non riverificata)*.

⚠️ **La ricaduta va attivata solo con la conferma già in funzione**: recuperare il 93% dei brasiliani portandosi dentro il 17,26% di falsi positivi della *scelta* sarebbe scambiare un buco dichiarato con un finto pieno.
⚠️ **Non estendere i suffissi**: `(soccer)` ha prodotto 1 solo esito utile in 94 tentativi, ed era la persona sbagliata.

---

## 3. CLUB — classificazione, alias, falsi positivi

### 3.1 La resa, e la sua deriva

| istantanea | tappe | univoco | ambiguo | assente |
|---|---|---|---|---|
| docstring (lotto ~1.000 giocatori) | — | 75,2% | 3,1% | 21,8% |
| 20.466 | 20.466 | 74,64% | 3,04% | 22,32% |
| 47.110 | 47.110 | **72,43%** | 2,68% | 24,88% |
| **54.001 (01/08 01:30)** | 54.001 | **72,2%** | 2,6% | **25,2%** |

Il docstring dichiara numeri di un lotto vecchio. La discesa è **deriva del campione**, non peggioramento: la coda dei giocatori meno noti ha carriere più periferiche. Per **club distinti** (non per tappe) la resa è 33,03% / 1,67% / 65,30%: l'asimmetria è la coda lunga.

### 3.2 Classificazione del non-agganciato *(misura su 20.466 tappe — la ripartizione, non i conteggi assoluti)*

| categoria | nomi | tappe | % assenti |
|---|---:|---:|---:|
| **riserve / giovanili** | 266 | 1.248 | **27,33%** ⚠️ (il docstring dice 17%) |
| variante di grafia (recuperabile) | 33 | 303 | 6,63% |
| rinominazione societaria | 4 | 15 | 0,33% |
| sigla puntata (`A.C. Milan`) | 20 | 24 | 0,53% |
| errore di parser (`[ 4 ]`) | 39 | 41 | 0,90% |
| **genuinamente assente** | 2.028 | 2.936 | **64,29%** |

**Le riserve non esistono a monte** — verificato, non stimato: su 3.173 righe di `club_names.csv.gz` solo 11 somigliano a una riserva e sono tutte prime squadre. `Real Madrid Castilla`, `Barcelona B`, `Bayern Munich II`, `Jong Ajax`, `Benfica B`: **nessuno esiste**. Collassarle sulla prima squadra è tecnicamente possibile ma è una **scelta semantica**, non un aggancio (e oggi è fatta per **2 club su 268** — §1.21).

**La coda è davvero coda:** 2.028 club, il **77,9% con una sola tappa**. Sui 60 più pesanti (Châteauroux 27, Basconia 23, Tours 18, Le Mans 17, Peñarol, Colo-Colo, Al-Arabi…), **56 su 60 non hanno in `club_names` nulla che somigli** — controllo per substring + `difflib` a soglia 0,86. Ligue 2, National, Golfo, Sudamerica, Asia, dilettanti: irrecuperabili.

**E la vera concentrazione del buco:** il non-aggancio è **16,4% sulle tappe senior contro 45,0% sulle giovanili**. Se una feature usa solo le tappe senior, la resa di partenza non è 72% ma **80,6%**.

### 3.3 Gli alias proposti

**60 alias, ogni destinazione verificata in `club_names.csv.gz` (esiste, nome unico) e, dove lo strato 1 copre, confermata dai club realmente giocati.** I principali per peso:

```
# varianti di grafia / ragione sociale per esteso
"AEK Athens"       -> "Athlitiki Enosi Konstantinoupoleos"      # 32 tappe, conferma 41/41
"PAOK"             -> "Panthessalonikios …Konstantinoupoliton"   # CORREZIONE, vedi 3.4
"İstanbul Başakşehir" -> "Basaksehir FK"        # 29, 38/43
"1. FC Nürnberg"   -> "1.FC Nuremberg"          # 27, 14/15
"Spartak Moscow"   -> "FK Spartak Moskva"       # 27, 47/52
"Dynamo Moscow"    -> "FK Dinamo Moskva"        # 14, 29/32
"Sint-Truiden"     -> "Sint-Truidense VV"       # 14,  9/11
"CSKA Moscow"      -> "PFK CSKA Moskva"         # 13, 18/22
"Fortuna Sittard"  -> "Fortuna Sittardia Combinatie"   # 10, 11/11
"OFI" · "Volos" · "AGF" · "AaB" · "Union SG" · "Zorya Luhansk" …   # 4-6 ciascuno, conferma piena
# rinominazioni: Mouscron-Péruwelz, Montreal Impact, Waasland-Beveren, Osmanlıspor
# disambiguazioni: Ajax, Mainz 05, AZ, Club Brugge, Aris, Young Boys, Verona, Excelsior …
```

**Resa raggiunta:** 74,64% → **78,59% univoco**, ambiguo 3,04% → **0,67%**, assente 22,32% → **20,74%**. **+3,95 punti = 808 tappe recuperate e 79 corrette** *(misura sul lotto da 20.466)*.

**E la prova che sono giusti, non solo numerosi:** i nuovi agganci si confermano contro lo strato 1 al **93,44%** (969/1.037, IC95 [91,77–94,79]), **sopra** il 90,12% degli agganci già esistenti. Il ~10% di scarto di base non è errore: è l'artefatto dei prestiti e delle stagioni doppie.

⚠️ **Cinque non funzionano col meccanismo attuale** (`ALIAS` mappa nome→nome e la destinazione viene ri-risolta dalla stessa regola ambigua): Feyenoord, Rubin Kazan, Logroñés, Metalist Kharkiv, Lokomotiv Moscow. Rimedio: **mappare al `club_id`** (+0,48 punti, e rende esprimibile il Lokomotiv, il cui nome da noi è in cirillico).
⚠️ **`Dnipro` va lasciato fuori**: sistemerebbe 2 tappe e ne romperebbe 1, perché `normalizza` scarta le cifre e `Dnipro-1` ≡ `Dnipro`. Vuole disambiguazione **per periodo**.
⚠️ **`Club Brugge` e `Verona` sono i casi da fare a mano uno per uno** (due club veri della stessa città), non da regola.
⚠️ **La regola inversa (i nostri token contenuti in quelli di Wikipedia) è stata misurata e BOCCIATA**: aggiungerebbe 254 tappe, ma `Austria Wien`→nazionale austriaca, `Universidad de Chile`→nazionale cilena, `CSKA Moscow`→CSKA 1948 bulgaro. Non aggiungerla.

### 3.4 La caccia ai falsi positivi — la parte che nessuno aveva guardato

| nome | agganciato a | conferme contro lo strato 1 | tappe (01/08) |
|---|---|---|---|
| `Brest` | Dynamo Brest (BLR) | **0/108** → 80/108 con Stade Brestois | 108-113 |
| `PAOK` | PAOK Kristonis (dilettanti) | **0/50** → 44/50 con il PAOK vero | 50 |
| `Bilbao Athletic` | Athletic Bilbao (prima squadra) | riserve fuse per insensibilità all'ordine | 32-50 |
| `Dnipro` | SC Dnipro-1 | 0/6 | 2 |
| **regola sottoinsieme** (§1.8) | varie | **~13,3%** [6,9–24,1] sbagliato su 7.397 tappe | **~700-1.000** |

Complessivamente sui tre nomi principali: conferma **3/87 = 3,45%** prima, **120/129 = 93,02%** dopo la correzione.

**Perché non si vedevano — e la lezione R7.** Il **punto cieco**: il **8,55%** delle tappe univoche (2.918 su 34.123) punta a club che `appearances` non ha **mai** visto in campo. Lì nessuna verifica è possibile: il test le dichiara «non giudicabili», mai «giuste». **PAOK Kristonis sta esattamente dentro quel cieco** (0 righe in `appearances`). *Un conteggio di conferme che non dichiara la propria copertura non è una misura.*
⚠️ Il rovescio va detto: buona parte di quel 8,55% è **legittima e attesa** (riserve, giovanili, divisioni inferiori che esistono nell'anagrafica ma non in campo). Non trattare 2.918 tappe come sospette.

**Due test che NON hanno funzionato, e vanno scritti come risultati negativi:**
- **il test del continente** (un giocatore finito in un club di un altro continente): **17 casi su 21.031 = 0,081%** [0,050–0,129], e **tutte e 17 sono corrette** (Boca, River, Al-Hilal, Flamengo, LAFC: il club è giusto, è lo strato 1 che non copre quei campionati). Non trova nulla, e in particolare non trova Brest e PAOK, perché quei club hanno `domestic_competition_id` a NaN;
- **il tasso aggregato della regola di sottoinsieme**: 90,32% [89,29–91,26] contro 89,98% [89,53–90,42] della corrispondenza esatta — **intervalli sovrapposti**. La diagnosi è arrivata dalla controprova sul singolo nome, non dal tasso medio.

---

## 4. IL DATABASE È USABILE?

### Verdetto

> **Sì, il dato regge. Manca lo strato di giunzione — e sono tre funzioni, non un dato.**

La feature si costruisce end-to-end e i valori sono verificabili a mano. Bologna-Lazio del 3/11/2023: esperienza media **134,5 contro 235,2** presenze, il più esperto Pedro con **479** (correttamente marcato `censored_left`, perché giocava dal 2008 e il dataset comincia nel 2012). Estesa alle 5 leghe: copertura **16.104/16.111 = 99,96%**, correlazione con la differenza reti **0,4193** [0,4065–0,4323], quota di vittorie casa per quartile di Δesperienza **24,3% → 37,6% → 48,7% → 63,5%**.

**Valore incrementale sopra il valore-rosa già in snapshot** (che correla 0,807 con la feature): logistica walk-forward, 10.707 partite di test → log-loss 1X2 da **1,0036 a 1,0015**, **Δ = −0,0021, IC95 [−0,0037, −0,0005]**, 4.000 ricampionamenti.
⚠️ **Non verificato dallo scettico.** È un terzo decimale, misurato contro il valore-rosa e **non contro il mercato**; nel progetto ci sono precedenti di leve di questa taglia che non sono sopravvissute al confronto col motore vero. Il segno è determinato, la portata no.

### Il vincolo delle formazioni — per quali partite l'undici è costruibile `pre`

| forma della feature | copertura | disponibilità R8 |
|---|---|---|
| **undici TITOLARE** | **ZERO partite storiche** | `pre` impossibile: nessuna fonte del repo raccoglie le formazioni ufficiali pre-kickoff |
| undici titolare, retrospettivo | **2.278 squadra-partita su 32.222 = 7,1%** (Serie A + Premier + Liga 2025-26, da diretta) | `post` — legittimo per studiare, **mai** per prevedere |
| chi è **sceso in campo** | 99,96% | `post` — usarla per la partita che l'ha prodotta è look-ahead |
| **rosa delle 3 partite precedenti** | 99,9% | ✅ `pre` per costruzione |

**E la misura che ridimensiona il vincolo** (invece di darlo per scontato): la rosa recente si sovrappone al **92,5%** (mediana 93,8%) con chi gioca davvero, e la feature costruita su di essa correla con la differenza reti **0,4193** contro **0,3602** [0,3470–0,3733] della versione che sa chi ha giocato. **La versione ignorante è migliore**, perché quella informata eredita il rumore delle rotazioni.

**Conclusione operativa:** per feature d'**aggregato** le formazioni **non sono il vincolo**. Lo diventano solo per feature sul **singolo** (il portiere titolare è quello abituale? quanti titolari mancano?), e lì il vincolo è duro e prospettico.

### Le quattro trappole che un consumatore ignaro sbaglierebbe in silenzio

1. **la censura deriva** (§1.9): +50% attraverso la finestra per artefatto di bordo — in un walk-forward è uno spostamento sistematico della distribuzione fra train e test. **Rimedio validato:** finestra mobile di 2 anni (piatta: 50,1→54,0);
2. **gli esordienti spariscono** (§1.10): 8,4% dei club-partita, +6,6 presenze di gonfiaggio;
3. **lo strato 2 non è raggiungibile dall'API sicura** (§1.24) — e includerlo *introdurrebbe* look-ahead, quindi è una scelta prudente, non un buco;
4. **il deliverable si muove** (§1.33): ogni numero wiki va datato.

### Il costo, corretto

| forma | costo |
|---|---|
| `career_before(d)` come da docstring (`appearances=None`) | 2,98 s (ricarica 377 MB) |
| `career_before(d, app)` | 0,439 s |
| corpus intero, una chiamata per **data distinta** (1.658) con precarico | **12,2 minuti** ⚠️ (non 42,9) |
| forma **cumulativa vettoriale** (assente dall'API) | **0,41 s** — verificata identica su 244 confronti, 0 differenze |

⚠️ La conclusione «è la differenza fra una feature usabile e una no» **è falsa**: una feature di carriera si calcola una volta e si salva, non si ricalcola dentro il loop. È ergonomia, non blocco.

---

## 5. COSA REGGE — dove non tornare a scavare

Attaccato deliberatamente, ha tenuto:

**Look-ahead (R8) sullo strato 1 — la garanzia principale.**
- `career_before` filtra con `date < as_of` ed è **davvero stretto**: `before(d+1) − before(d)` = esattamente le partite di quel giorno. Retti tutti i casi limite (partita esattamente ad `as_of` esclusa; giocatore con una sola presenza; `as_of` prima del dataset; `player_ids=[]`).
- **Mutazione `<` → `<=`: 2 test su 22 cadono.** La copertura R8 dello strato 1 funziona.
- `player_current_club_id` — la colonna più look-ahead del file, il club di *oggi* — è correttamente **fuori** dalle `usecols`.

**Integrità strutturale dello strato 1.**
- **0 difetti su 8 controlli × 197.812 righe** (minuti=0 con presenze>0, gol/assist/minuti negativi, minuti>120×presenze, date fuori range, `data_a<data_da`, `club_id` nullo, `is_top5`, taglio stagione) → IC95 del tasso di difetto **[0, 0,002%]**.
- 0 duplicati su `appearance_id`, 0 su `(player_id, game_id)`; `minutes_played==0` su 3 righe di 1.894.350.
- `player_name` con `first` è **sicuro per costruzione**: 0 `player_id` su 29.531 con più di un nome.
- Trasferimento di gennaio dentro la stessa competizione: 4.162 gruppi (2,15%) → restano righe separate. Corretto.

**Il taglio delle stagioni, ovunque tranne il 2020.**
- Verificato su tutte le 48 competizioni × 2013-2025: **nessuna competizione ad anno solare**, gap mediano ≥40 giorni attorno al 1° luglio. Le competizioni con più partite di luglio (BESC 100%, RUSS 92,6%) sono supercoppe che *aprono* la stagione, e il taglio le assegna correttamente.

**Il parser degli anni.**
- Le due varianti sospettate — `'2005–06'` (fine a due cifre) e `'2019–present'` — hanno **0 occorrenze su 52.919 righe**. Il rischio esisteva e non si è materializzato.
- Il segnaposto `'0000'` è gestito: **947 casi su 954** intercettati dal controllo `da == 0`.
- **Contaminazione da nazionali nella carriera di club: cercata, non trovata** — 0 righe su 34.945 (le 24 «U21/U23» sono squadre riserve di club, legittime). Le 329 pagine senza intestazione di chiusura finiscono davvero con l'ultimo club.

**L'aggancio dei club, nelle parti attaccate.**
- La regola di **sottoinsieme non è statisticamente più rischiosa** di quella esatta: 90,32% [89,29–91,26] contro 89,98% [89,53–90,42], intervalli sovrapposti. Brest e PAOK sono collisioni singole, non la punta di un iceberg.
- Il **test del continente** non trova nulla: 17/21.031 = 0,081%, tutte corrette.
- `ALIAS` contiene già `Rennes→Stade Rennais FC` e `Olympiacos→…`, e funzionano. **Tutti e 5 gli ALIAS servono**: senza, `candidati()` restituisce `[]`.
- La **normalizzazione raggiunge gli omoglifi cirillici**: `FС Taganrog` (С = U+0421) viene agganciato. Danno = 0.
- La **coerenza fra le due fonti** è 98,09% su 27.772 coppie (giocatore, anno); dei 530 conflitti, 120 sono il mercato di gennaio (disallineamento legittimo fra grana annuale e giornaliera) e il 23% dei restanti è Brest+PAOK.

**Il metodo del placebo.**
- Il 12% di falsi positivi del criterio-club è stato **riprodotto indipendentemente** (10,53%) con un placebo costruito da zero. Il rapporto fra i due criteri (~45×) è identico e la conclusione non si muove di un millimetro.

**Anomalie che sembrano difetti e non lo sono (R4).**
Minuti/presenza fino a **120 esatti** (supplementari — il tetto netto è la prova che il dato è sano); 588 righe con più gol che presenze (poker in gara secca: Piatek 2 presenze e 7 gol in Coppa Italia); Falcao con la prima tappa senior a 13 anni (vero, Lanceros Boyacá 1999); 12 coppie prestito+definitivo che collidono sulla chiave naturale (deduplicarle **perderebbe dato vero**); il calo dei minuti per presenza da 71,5 a 64,4 dal 2020-21 (le cinque sostituzioni); `clubs.csv` copre 796 club mentre `appearances` ne referenzia 1.231 (per risolvere un `club_id` serve `club_names.csv.gz`, 3.173 righe).

---

## 6. I PROSSIMI PASSI

### Correzioni — vanno fatte

| # | cosa | perché ora | costo |
|---|---|---|---|
| **C1** | **Conferma d'identità nel fetcher** (`bday` ↔ `players.csv`), con **quarantena** per i discordi che hanno la carriera coincidente — mai gate secco, mai il criterio-club da solo | Chiude la classe di difetto più grave, e i **592 collidenti al 60% di errore sono tutti ancora davanti** (§1.3). Farlo *dopo* costa 28 carriere sbagliate in più | **0 richieste**, offline sulla cache |
| **C2** | **Quarantena delle 111-118 righe** dei 13-15 `player_id` + registro in `data/correzioni_dichiarate.csv` (R3) + colonna `identita_verificata` nel deliverable | Sono righe false in un file versionato | 0 richieste |
| **C3** | **`red_cards` 2025-26 → NaN** + test di regressione a −3 sd per ogni colonna-conteggio | C'è già un consumatore (`_run_fase124_diffidati.py`) e la 2025-26 è la stagione del test prospettico | mezz'ora |
| **C4** | **Alias `Brest` e `PAOK`; `Bilbao Athletic` → assente; tenere le cifre in `normalizza`** | 213 tappe deterministicamente sbagliate ed etichettate «univoco»; le cifre valgono +98 univoci e −182 ambigui | mezz'ora. ⚠️ Brest **non** è a rischio zero: il Dynamo Brest esiste con 10 righe |
| **C5** | **`season_of`: correggere il docstring** e dichiarare il 18,8% di righe «2020-21» miste | Il docstring afferma l'opposto di ciò che il codice fa | 5 minuti |
| **C6** | **`COMPETIZIONI_NAZIONALI = ('FIWC','AFCN')`** + colonna `nazionale`, esclusa da `career_before` | +1 club a 712 giocatori (Mondiale) e a **487 dentro la stagione modellata** (Coppa d'Africa) | un'ora |
| **C7** | **`career_before`: reindex con zeri** per gli esordienti quando `player_ids` è passato | 8,4% dei club-partita, distorsione nella direzione sbagliata | mezz'ora, non rompe nulla |
| **C8** | **Regex anni**: U+2212, inizio mancante che resta `None`, zeri spaziati — **e la colonna `anni_grezzi`** | 80 righe (0,151%) di finto pieno; senza il testo originale nessun audit futuro può distinguere una tappa di un anno da un parsing rotto | tre righe + ri-parse offline |
| **C9** | **Due test di identità** offline dalla cache (Andrea Costa negativo, `Stefan_Mitrovic_(soccer)` negativo, una pagina coincidente positivo) + **vincolo di unicità sull'URL** | Oggi l'asse identità ha **zero** test | un'ora |
| **C10** | **Dichiarare in `docs/DATI.md`** (R4): il **bias di copertura per nazionalità** (χ²=696,8, p=4,6e-122), la **selezione per presenze** (mediana 209 vs 28), le 4 discrepanze anagrafiche non-errori, gli zeri «non ancora», le anomalie che non sono errori | Il bias di nazionalità è l'unico rilievo che avvelena una feature invece di sporcare righe; le discrepanze non dichiarate verranno ri-contate come omonimi (0,25% → 0,54%) | un'ora |

### Miglioramenti — si possono fare

| # | cosa | resa misurata |
|---|---|---|
| **M1** | **Ricaduta sulle pagine-indice** (scelta anno→mese→nazionalità) | recupera il **93,03%** [89,13–95,60] dei falliti e chiude il divario brasiliano-iberico. **+1 richiesta** solo per chi ci passa (1,07/giocatore). ⚠️ **Solo con C1 attiva** |
| **M2** | **`ALIAS` da nome→nome a nome→`club_id`** + test a import-time | +0,48 punti e rende esprimibili i 5 alias oggi impossibili (Lokomotiv, Feyenoord, Rubin, Logroñés, Metalist) |
| **M3** | **I 60 alias verificati** (senza `Dnipro`) | **+3,95 punti**: 808 tappe recuperate, e i nuovi agganci si confermano al **93,44%**, sopra il 90,12% degli esistenti |
| **M4** | **`club_ids()` / `attach_club_ids()`** e **`player_ids(nomi, contesto)`** | il primo ha resa 100% su 5 leghe; il secondo 92-95% univoco, **0 ambigui** (⚠️ contesto lega+stagione obbligatorio, non opzionale) |
| **M5** | **`career_panel()` cumulativo + `career_at()`** | 0,41 s per l'intero corpus contro 12,2 minuti; verificata identica su 244 confronti |
| **M6** | **Feature a finestra mobile** (o normalizzazione per stagione) | l'unica versione **validata piatta** (50,1→54,0) contro il +50% della cumulativa |
| **M7** | **Matrice di disponibilità per COLONNA e per fonte** (`pre`/`post`/`statico` + unità di misura + su quale strato esiste), come chiede §5-bis R8 | ⚠️ **non** rinominare le colonne comuni: romperebbe `test_database_unico_ha_le_colonne_comuni` e l'idea stessa di «una tabella sola». Una colonna `grana` è la strada meno invasiva |
| **M8** | **Togliere i due `ALIAS` riserve** (`SC Freiburg II`, `Bayern Munich II`) | 102 tappe tornano `assente` come le altre 2.961. Costo: −0,22 pp di resa dichiarata, guadagno: coerenza |
| **M9** | `log.warning` quando `esiti.jsonl` è più recente di `tappe.csv.gz`; scrittura atomica + `MANIFEST.json` | copre il rischio durevole (raccolta finita senza ri-export) |
| **M10** | Pulizia dei residui `[ .. ]` **nel parser**, non nella normalizzazione | **6 tappe** recuperate (0,013%). Vale come igiene del conteggio dei club distinti, non come resa |
| **M11** | Test-filtro riutilizzabile: «≥4 tappe testabili, 0 conferme dallo strato 1» | 23 candidati, 22 spiegati dalla copertura e **1 errore vero**. Buono come regressione |
| **M12** | Risoluzione via **Wikidata** (P569 + P54) invece che via titolo | è l'unica strada che chiude anche il caso *primary topic*. Costo: fronte nuovo, robots.txt da verificare — **non misurato** |

### Cosa **non** fare

- **Non** aggiungere la regola inversa nell'aggancio dei club (misurata e bocciata: 254 tappe, ma nazionali e club omonimi di altri paesi).
- **Non** usare il criterio-club in OR con la data (10,5% di falsi positivi contro 0,23%).
- **Non** applicare la regola binaria «tieni solo i candidati coperti dallo strato 1» agli ambigui: rifarebbe il bug «Hellas Verona». Serve una soglia (presenze≥20 → 753 tappe risolte su 1.264) più alias a mano per Brugge e Verona.
- **Non** provare `(soccer)` alla cieca.
- **Non** trattare le 2.918 tappe del punto cieco come sospette: buona parte è legittima.

---

### Nota finale sull'onestà del perimetro

Ciò che **nessun controllo interno può vedere**: un valore *sbagliato ma plausibile* — un gol attribuito al giocatore sbagliato, una presenza al club sbagliato dentro la stessa lega. Per quello serve una terza fonte indipendente, e non c'è.

La potenza dei controlli eseguiti, dichiarata: strato 1 **esaustivo** su 8 assi (difetto minimo rilevabile 0,002%); buco di una colonna-conteggio rilevabile dal ~4,5% in su (quello dei rossi è del 98,7%, quello ipotetico dei gialli sarebbe al 9% ed è già al limite); identità delle pagine wiki **quasi completa, non campionaria** (copertura 100%, sensibilità 99,32%); aggancio dei club **cieco sull'8,55%** delle tappe univoche; falsi positivi del sottoinsieme stimati **a giudizio umano** su 60 casi, non oggettivamente.