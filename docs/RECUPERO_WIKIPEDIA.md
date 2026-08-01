# Recupero dei giocatori Wikipedia falliti — piano verificato (01/08/2026)

> **Lavoro a 9 agenti**: 4 analisi indipendenti sui quattro fronti, 4 scettici che
> hanno rieseguito ogni misura, una sintesi. **Dove lo scettico ha corretto un
> numero o una conclusione, vale la sua versione.**
>
> **Esito della verifica: 3 fronti su 4 reggono, 1 cade** (il gazetteer sui 404:
> non per il rischio, ma perché la resa non è più misurata dopo il fix di un bug
> nel suo stesso codice). E **cinque rettifiche obbligatorie** cambiano il piano,
> non solo i numeri — sono in §0-bis.
>
> ⚠️ **Nulla di questo è stato applicato.** Il codice proposto vive qui, non nei
> moduli. Le tre identità sbagliate identificate in §B sono **ancora nel
> database**.


> Sintesi finale. **I verdetti dello scettico hanno precedenza sulle quattro analisi**: dove le due fonti divergono, qui sotto compare il numero dello scettico e l'analisi originale è citata solo come misura ritirata. Tutte le misure sono state fatte sulla cache (`data/wikipedia_cache/en/`, 24.052 pagine) e su una copia in sola lettura di `data/carriere_wikipedia/esiti.jsonl`. Richieste di rete spese in totale dai cinque agenti: **~140**, una alla volta, solo su `/wiki/<Nome>`.

---

## 0. Premessa: i numeri del brief sono scaduti, e non di poco

La raccolta è girata in background durante tutto il lavoro. Denominatori a HEAD (01/08/2026), 26.816 righe / 26.504 `player_id` distinti:

| stato | brief | HEAD | in cache |
|---|---:|---:|---:|
| `nessun_infobox` (pagine-indice) | 2.102 | **2.519** | 2.519 = **100%** |
| `nessuna_pagina` (404) | 1.354 | **2.085** | 0 (ovvio) |
| `nessun_blocco` | 557 | **711** | 711 = **100%** |
| `errore` | 312 | **315** | 286 = 90,8% |
| `identita_non_confermata` | 152 | **205** | 205 = **100%** |
| `quarantena` (dentro gli `ok`) | 199 | **262** | — |
| **totale falliti** | **4.477** | **5.835** | |
| *mai tentati* | — | **3.027** | — |

**Due conseguenze operative.**

1. La colonna «in cache» del brief (1.516/2.102, 477/557, 118/152) è **stale**: su tutti i fronti diversi dai 404 la cache è al **100%**. Quindi l'obiezione «avete misurato sul sottoinsieme facile già scaricato» **non si applica** e va dichiarata refutata (R4): il censimento è sulla popolazione intera, non su un campione.
2. Tutte le percentuali qui sotto **trasferiscono**, i valori assoluti **no**. Vanno ricontati sul file finale prima di scriverli nel README.

---

## 0-bis. Rettifiche obbligatorie prima di eseguire qualunque cosa

Sono i verdetti dello scettico che **cambiano il piano**, non solo i numeri.

| # | fronte | cosa va corretto | conseguenza se non si corregge |
|---|---|---|---|
| R1 | pagine-indice | La frase «il ramo-indice **non peggiora** la qualità del database» è **falsa**: confronta uno 0,268% *pre-filtro* (audit §1.1, misurato prima che `verifica_identita` esistesse) con un limite *post-filtro*. | Si dichiara neutrale un canale che moltiplica per ~5-11× il conteggio residuo di persone sbagliate. |
| R2 | pagine-indice | Il limite sui falsi positivi va da **pooled** a **stratificato per notabilità**: 0,224% → **0,50%**. | Si sottostima di 2× il rischio, e i 3.027 mai tentati stanno **al 100%** nello strato non vincolato. |
| R3 | gazetteer (404) | `varianti_da_gazetteer` ha il dedup su `chiavi(t)[0]` inizializzato a `{a}`: ogni titolo indicizzato sotto `A{a}` ha per costruzione la stessa chiave → **lo strato A è irraggiungibile**. Eseguito: 301 candidati, strato A = **0** invece di 291. | Si perde il **48%** della resa e si esegue codice diverso da quello che ha prodotto i numeri (viola §1.5). |
| R4 | respinte/quarantena | Il ramo `k == 0 → respinta` confonde **prova contraria** e **assenza di prova**: 6 delle 11 respinte hanno **zero club** nello strato 1, e 4 di queste hanno Δ FORTE (4, 10, 14, 18 giorni). Serve la guardia `k == 0 **and** n_club > 0`. | Si **cancellano ~4 identità corrette** per rimuoverne 3 sbagliate: bilancio negativo. |
| R5 | `nessun_blocco` | `casi_routing.json` risolve la data di nascita **per nome**, non per `player_id`: 40/126 righe duplicate, 86 titoli distinti su 126, i **sei** Danilo (1984/1986/1990/1991/1999/2001) tutti instradati su «Danilo (footballer, born 1986)». | Il recupero scende da ~126 a ~79, **e il colpo cade esattamente sui mononimi brasiliani**, cioè sulla confondente. |

---

## 1. Il piano di recupero, in ordine di rapporto valore/costo

### Riepilogo

| # | fronte | popolaz. | recuperati (IC) | falsi positivi | richieste | tempo @1/s |
|---|---|---:|---:|---:|---:|---:|
| **A** | parser: vincolo sull'anno | 20.981 pagine `ok` | **+7.900 tappe** (non giocatori) | 0 per costruzione | **0** | 0 (≈16 min CPU) |
| **B** | quarantena → `verifica_identita_v2` | 262 | **245 rietichettate** [89,9-95,9%] · **−3 sbagliate** | 0-2 righe | **0** | 0 |
| **B2** | respinte risolte dalla sola cache | 205 | **16** [4,9-12,3%] | incluso in B | **0** | 0 |
| **C** | `nessun_blocco` → instradamento | 711 | **126** [111-133] | **0 punto, ≤9** | **137** | 2,3 min |
| **D** | pagine-indice | 2.519+376+24 | **2.070-2.335** | **0 punto, ≤11,8** | **2.842** | 47,4 min |
| **E** | 404 → gazetteer (**pilota, poi decidere**) | 2.085 | **non misurato** (603 candidati) | 0 punto, ≤28 | 603 | 10,1 min |
| **F** | respinte → titolo nuovo | 189 | **~81** [44-118] | incluso in B | **189** | 3,2 min |
| | **TOTALE** | | **≈2.400-3.100 giocatori** | **0 osservati, ≤51 al 95%** | **3.771** | **1,05 ore** |

Il totale dei falsi positivi è la **somma dei limiti superiori** (conservativa, non additiva in probabilità): ≤51 su ~2.900 recuperi = **≤1,8%**. Il valore **osservato** su ~180 verifiche end-to-end indipendenti (30 sul fronte-indice + 50 sull'instradamento + 79 sul placebo gazetteer + 9 candidati reali + 16 pagine nuove) è **0 agganci sbagliati**.

---

### A · Il vincolo sull'anno in `parse_career` — 0 richieste, il miglior rapporto in assoluto

Non recupera **giocatori**, recupera **righe**: Wikipedia lascia la colonna *Years* vuota quando gli anni non si sanno, e il parser pretende `\d{4}`.

- **+757 tappe su 1.999 pagine = +4,08%** (analisi: +3,96%) → estrapolato su 20.981 pagine `ok`: **≈7.900 tappe**;
- **26,81%** delle pagine toccate (IC95 [24,9%, 28,8%]); mediana +1 riga, massimo +4;
- **99,74% giovanili** — quindi il guadagno è quasi tutto sulla ricostruzione del settore giovanile, non sulle tappe senior;
- forma della cella: **757/757 vuote** → la guardia proposta (`cella vuota o sole cifre/?/trattini`) non ammette nulla che non sia già visto;
- controllo spazzatura: i club aggiunti sono club veri (Real Sociedad 6, Roma 3, Valencia 3, Lazio 3; sul campione più grande Ajax 35, Feyenoord 25, Boca Juniors 20).

**Costo: zero richieste, ~16 minuti di CPU** per ri-girare il parser sulla cache. Due effetti di schema da dichiarare (R8): le 7.900 tappe hanno `anno_da=None` (dato mancante **dichiarato**, non finto pieno), e il campo `ordine` si rinumera sul 26,8% delle pagine.

**Falsi positivi: zero per costruzione** — non si scarica nulla, non si cambia identità, si leggono righe di pagine già confermate.

---

### B · Le 262 quarantene e le 16 false respinte — 0 richieste

L'errore diagnosticato è giusto: `verifica_identita` confronta **insiemi di nomi di club**, e il nome di un club non identifica nessuno. Il caso conclamato è nel campione: **Javier Olaizola** padre (28/11/1969, Eibar/Real Burgos/**Mallorca**) contro il nostro figlio (15/03/2007, **Mallorca** 2025-26). 37 anni di scarto, club in comune, e la regola attuale lo mette in quarantena *per la copertura-club*. Con le finestre temporali `k = 0`: le due permanenze al Mallorca non si sovrappongono.

**Che le quarantene siano la persona giusta è dimostrato per via indipendente, non per intuizione**: sulle 2.219 coppie di persone **diverse con lo stesso nome** dentro `players.csv`, solo lo **0,96%** ha le date entro 31 giorni e l'**8,96%** entro 366; nella quarantena sono il **53,1%** e il **94,8%**. Limite inferiore di miscela: **π ≥ 94,3%** (≥89,9% con gli estremi di Wilson).

Esito con `verifica_identita_v2` **e la guardia R4**:

| | quante | tasso |
|---|---:|---:|
| promosse a `confermata_coerenza` | 245 | **93,5%** [89,9; 95,9] |
| lasciate in `quarantena` (giudizio umano) | ~14 | |
| **respinte — identità davvero sbagliate, oggi dentro il DB** | **3** | Olaizola 1969/2007 · Bruno Alves 1981/1990 · Nilson Júnior 1975/1991 |
| false respinte recuperate dalla sola cache | **16/205** | **7,8%** [4,9; 12,3] |

Le 16 sono refusi veri: **Germán Lux** 07/06/1982 contro 06/07/1982 (giorno e mese invertiti), **Georgievski** 5 giorni di scarto con **4 club su 4** coerenti anche negli anni (bocciato dai diacritici nel matcher).

**Regressione nota e non riportata dall'analisi**: il ramo `Δ ignoto → serve k≥2` **declassa 9 delle 15** `confermata_club` odierne a quarantena. Piccola in assoluto, reale, va messa a verbale.

**Il 72,3% dichiarato va scisso**, perché mescola due cose diverse: **245 righe cambiano solo etichetta** (sono già nel DB come `ok`) e **16 sono dato nuovo**. Il valore vero di questo passo è: 1.643 tappe senior passano da «dubbie» a «confermate con una misura», e **18 tappe di due-tre persone sbagliate escono**.

**Falsi positivi: 0-2 righe.** Lo **0,11%** pubblicato dall'analisi è **ritirato**: viene da un placebo che condivide un club ma ha **un altro nome**, e in produzione quell'avversario non può presentarsi (si scarica `/wiki/<Nome>`, quindi l'avversario è **sempre** un omonimo). I due avversari differiscono proprio sull'asse a cui si attribuiva il taglio di 40×: la corroborazione passa nel **13,9%** [7,7; 23,7] sull'omonimo contro il **2,3%** [1,8; 2,9] sullo stesso-club — **6×**. Sull'avversario vero: **0/72 = 0,0% [0,0; 5,1]**, e condizionato ai club condivisi n=3 → IC [0; 56]: **nessuna potenza**, e va detto. Con ~38 incontri attesi, FP = **0-2 righe**.

---

### C · `nessun_blocco` → instradamento — 137 richieste, 2,3 minuti

**L'ipotesi del fronte era sbagliata e questo è il risultato negativo più utile del lavoro.** Non è un problema di parsing:

| che cos'è davvero (censimento completo, 711) | n | % |
|---|---:|---:|
| soggetto diverso (NBA, baseball, ciclismo, città, santi, re, club) | 320 | 45,0% |
| pagina di disambigua | 220 | 30,9% |
| pagina di NOME (lista antroponimica) | 154 | 21,7% |
| senza infobox | 14 | 2,0% |
| **biografia di calcio vera** | **3** | **0,42%** |

E le 3 di calcio sono **tutte e tre omonimi**, tutte e tre respinte. **Recupero dall'ampliamento delle etichette: 0/711, IC95 [0%, 0,54%].** Nella variante generica `career` l'ampliamento **rompe il 93,2%** delle pagine che oggi funzionano (+7.701 righe spurie — le nazionali giovanili promosse a tappe di club — e **−3.161 righe perse**). Le varianti prudenti non rompono nulla ma iniettano 31 carriere NBA/ciclismo su `player_id` di calciatori: guadagno esattamente zero. **`INTESTAZIONI_SENIOR` va lasciato com'è.**

Lo strumento di classificazione è stato validato (cosa che l'analisi non fa): la firma `club domestic league appearances and goals` è presente in **1.998/1.999 = 99,95%** delle pagine `ok` → il tasso di calciatori veri etichettati per errore «soggetto_diverso» è ~0,05%, cioè **~0,4 pagine su 711**.

**Quello che i 711 danno davvero**: la pagina sbagliata è una **tabella di instradamento**. Ri-derivando per `player_id` (fix R5):

- almeno un candidato calcistico: **395/711 = 55,6%**
- **esattamente uno** con l'anno di nascita atteso: **137/711 = 19,3%** [16,5%, 22,3%] — **137 titoli distinti, 0 collisioni**
- precisione della regola su **50** verifiche di rete (25 dell'analisi + 25 dello scettico su casi *esclusi* dal campione originale): **46/50 = 92,0%** [81,2%, 96,8%]
- **dopo `verifica_identita` invariata: 0/50 agganci sbagliati**, IC95 superiore **7,1%**

**Recuperati: 126** (range 111-133). Tappe attese ≈126 × 10,8 = **~1.360**. **Falsi positivi: 0 punto, ≤9.**

Residuo non misurato, ed è **diverso** da quello dichiarato dall'analisi: il ramo che può far passare un omonimo non è la data, è la **quarantena** (date discordi + ≥50% club coincidenti → `ok`). Quel ramo si attiva solo quando la data discorda: **4 casi su 50**, 0 sfuggiti. La difesa lì è misurata a n=4, non a n=50.

---

### D · Le pagine-indice — 2.842 richieste, 47 minuti. È il fronte grosso, ed è il più rischioso

**Il fronte non è 2.519 pagine, è 2.919**: il test `"infobox" not in html` è una **stringa**, non una forma. «Danilo», «Fernando», «Roberto» sono voci di *nome proprio* che hanno un `infobox name`, passano il test e finiscono in `nessun_blocco`. Ri-eseguito: **376/711** `nessun_blocco` e **24/315** `errore` sono pagine-indice; **0/205** `identita_non_confermata` — e quello zero è un **controllo negativo genuino** che funziona.

Copertura del selettore sulla popolazione attuale: **2.145/2.490 = 86,1%** (astensioni: 275 sotto soglia, 59 ambiguo, 11 senza candidati) → **2.335 `player_id` accettati unici**. Tasso di conferma sul campione di 30, riverificato offline: **30/30 `confermata_data`** (data esatta in 29, ±1 giorno in 1 — Ignatenko 2006-05-11 vs 2006-05-12, dentro tolleranza, R4). IC95 [88,6%, 100%] → **recuperati attesi 2.070-2.335**.

**Prova di non-regressione, fatta bene**: il test sui 600 `ok` misurava un percorso irraggiungibile (`not tappe and ... and e_pagina_indice(html)` va in corto circuito). La prova che serviva: su **2.866** pagine classificate INDICE, **0** contengono la nostra data di nascita; delle 2.490 `nessun_infobox` indice, **0** hanno uno `span.bday` (sono disambigue pure); per contro **227 delle 335** `nessun_blocco` non-indice hanno un bday — sono voci vere, e vengono correttamente lasciate stare.

#### I falsi positivi, riscritti (R1 + R2)

Il bound *pooled* della proposta è persino leggermente **migliore** del dichiarato: la decomposizione non è circolare, perché un bersaglio assente viene comunque respinto nel 97,9% dei casi → `(1 − 0,979·z)^30 = 0,05` → **z ≤ 9,7%**; col leak rimisurato su **20.394** accoppiamenti (**2,10%** [1,91%, 2,31%], contro 2,02% su 3.914) → **FP ≤ 0,224% = ≤5,3 giocatori**.

**Ma il bound pooled non vale per la coda**, ed è lì che il lavoro andrà:

| presenze in carriera | n | accettazione |
|---|---:|---:|
| <5 | 351 | **78,3%** [73,7-82,5] |
| 5-20 | 703 | 76,4% [73,1-79,5] |
| 20-50 | 616 | 81,8% |
| 50-100 | 530 | 81,3% |
| 100-200 | 442 | 86,2% |
| 200+ | 248 | **89,5%** [85,0-93,0] |

Il selettore è **sensibile** alla notabilità (si astiene di più sugli oscuri) — credito. Ma accetta comunque il **78,3%** dei giocatori con <5 presenze, cioè proprio quelli che quasi certamente non hanno una voce propria. Il campione di 30 ha mediana **44** presenze e solo il 20% sotto le 20; le 2.335 scelte hanno mediana **38** e il 34,2% sotto le 20. Lo strato debole è coperto da **6 osservazioni**.

```
strato <20 presenze :   812 scelte, z <= 40,1%  ->  FP <= 0,927%  ->  <= 7,5
strato >=20 presenze: 1.538 scelte, z <= 12,0%  ->  FP <= 0,277%  ->  <= 4,3
TOTALE                                          <= 11,8 giocatori = 0,50%
```

**Il doppio del limite pooled.** E i **3.027 mai tentati** (mediana **1** presenza, **100%** sotto le 20) porteranno ~446 scelte in più **tutte** nella fascia peggiore. L'audit §1.3 aveva già misurato che il tasso di persona-sbagliata sale sulla coda (60% sugli omonimi non-primi contro 0,117% sui nomi unici, Fisher p=3,7e-8).

**La formulazione onesta**, che sostituisce «non peggiora il database»:

> Il ramo-indice recupera ~2.335 giocatori al prezzo di **al più ~12 agganci sbagliati (0,50%)**. È un canale d'errore **~40× più sporco per recupero** del ramo per-nome (residuo post-filtro 0,268% × 2,10% = **0,0056%**, cioè ~1,2 giocatori sui 20.981 `ok` di oggi), e ha un **meccanismo**: sul ramo per-nome l'omonimo ha un anno di nascita scorrelato dal nostro e il test a ±3 giorni lo respinge quasi sempre; sul ramo-indice la persona sbagliata è **year-matched per costruzione** — l'abbiamo scelta *perché* l'anno coincideva — quindi il leak collassa esattamente sul pavimento del paradosso dei compleanni, 7/365 = 1,92%. **La strategia costruisce la correlazione che rende il filtro a valle massimamente debole.** In assoluto ≤12 giocatori sono lo **0,02%** del database e il prezzo è accettabile — ma è un **aumento dichiarato**, non un pareggio.

**Prima di lanciare: 30 richieste di validazione stratificate sotto le 20 presenze**, non a caso. Costo 30 secondi, e chiudono l'unico strato dove il bound non c'è.

#### Il controllo che mancava (regola Fase 98/99)

Classificando i 1.840 titoli scelti: **83,9% è generabile da template deterministici** — `(footballer)` 24,6%, `(footballer, born <anno>)` 54,0%, `(<Nazionalità> footballer)` 5,2%. Il meccanismo **esiste già** (`SUFFISSI` in `fetch_wikipedia_careers.py`): semplicemente non viene provato su `nessun_infobox`, perché il loop fa `break` su qualunque stato ≠ `nessuna_pagina`. Il contributo **unico** del selettore è il **16,1%** restante (qualificatori col mese come `Fernandinho (footballer, born May 1985)`, e titoli davvero diversi: `Antunes → Vitorino Antunes`, `Fabri → Fabricio Agosto Ramírez`, `Jonathas → Jonathas de Jesus`) più un risparmio di **2-3×** in richieste rispetto a provare i template in sequenza. Resta un buon affare, ma «il fronte recupera 2.335» attribuisce al selettore recuperi che un cambio di **una riga** otterrebbe. Il codice proposto registra `template_equivalente` in `dettaglio`, così il controllo si misura a posteriori gratis.

**Ancora due cose da sistemare**: la mappa `DEMONIMI` del codice proposto ha **75** paesi, quella che ha prodotto i numeri ne ha **96** — 23 persi (Northern Ireland 24 giocatori, Cape Verde 31, DR Congo, Egypt, Korea South, Kosovo, Ivory Coast…), **219/3.545 = 6,2% del fronte** che perde il segnale nazionalità **e**, con `dem=()`, anche il **−2,0 per nazionalità sbagliata**: l'anno decide da solo. È R6 applicato al codice: degrado silenzioso, nessuna eccezione. E il placebo A è **6,30%** [5,79%, 6,83%] (la tabella del dettaglio aveva ragione, la sezione `numeri` col 6,87% no).

---

### E · I 404 e il gazetteer — 603 richieste, ma **prima un pilota di 100**

**L'idea regge, il consegnato no.** Il nucleo è reale e vale: le pagine già in cache contengono, nei loro wikilink, i **titoli veri** di en.wikipedia, e il titolo giusto di un giocatore che ha fallito per grafia sta quasi sempre lì dentro perché la sua pagina è linkata da quella di un compagno. Costo: **zero richieste**. Il fronte 404 non è quello dei mononimi — è **traslitterazione** (Ucraina 29,5%, Bosnia 22,7%, Croazia 15,5%, Grecia 14,0%; Brasile solo 5,5%), e le quattro chiavi (grafia / traslitterazione / ordine / cognome) coprono insieme ucraino, russo, bielorusso e kazako senza una regola per lingua.

**Ma va respinto come consegnato**, per cinque motivi misurati:

1. **Il codice cancella lo strato più grande** (R3): 301 candidati invece di 587, strato A = **0**. Tutti e cinque gli esempi che l'analisi dichiara verificati 5/5 allo strato A restituiscono lista vuota. Col dedup corretto (sull'**URL esatto** già tentato, non sulla chiave appiattita — è il punto: `Bosko Sutalo` e `Boško Šutalo` sono due URL diversi con la *stessa* forma appiattita): **587 candidati, A = 291**.
2. **Il 34,3% non si estrapola.** Per blocchi di raccolta, a gazetteer costante: **46,6% → 29,6% → 22,4% → 16,1%**. La raccolta è ordinata per priorità e il gazetteer contiene i *linkati*, cioè i famosi: i ~3.000 ancora da fare renderanno **~16%**, non 34%.
3. **Il placebo è contaminato.** Il null assume che, tolto il titolo vero, ogni candidato sia un'altra pagina: falso proprio dove pesa, perché en.wikipedia compare nei wikilink con **entrambe** le grafie. Misurato: **1.223 su 1.223** candidati-placebo di strato A hanno la data di nascita coincidente (Modric/Modrić, Džeko, Rakitić, Szczęsny). I null validi sono ~70, non 107.
4. **La stratificazione del rischio è sbagliata.** «Solo D può agganciare un'altra persona» è falsificato: dei 587 candidati **reali**, 9 hanno la pagina già in cache e **9 su 9 sono un'altra persona** — uno di **strato A** (`Alex Sola` → `Álex Sola`, 1999-06-09 contro 2003-12-14). Tutti e 9 **respinti dal giudice-data**: la difesa funziona, la stratificazione no.
5. **Numeri secondari non riproducibili**: i «218.026 titoli» non tornano (con un *sovrainsieme* di file lo stesso codice ne dà **186.562** — impossibile, l'insieme è monotono); cade con essi il «volano ~4 titoli/pagina». Il filtro `class="new"` sui link rossi è **inerte** (gli href dei red link contengono `?action=edit&redlink=1` e sono già esclusi dalla regex): risultato giusto, meccanismo dichiarato sbagliato.

**E un claim strutturale falsificato a costo zero**: «un 404 sul nome nudo dice che quel nome su en.wikipedia non esiste in nessuna forma» è **falso**, 19 controesempi già dentro la cache (`Lasse Sörensen` → `Lasse Sørensen (footballer, born 1999)`; `Nikola Stankovic` → `Nikola Stanković (footballer, born 1993)`). La conclusione *operativa* (non provare `(footballer, born AAAA)` alla cieca — bisognerebbe indovinare **anche** la grafia, resa 0/6) resta valida, ma **indicizzando i titoli disambiguati per la loro forma base si ottengono +16 recuperi gratis**, che la proposta buttava via.

**Falsi positivi**: ripulendo il denominatore, i confronti validi sono **70** (placebo B/C/D in cache) **+ 9** candidati reali = **0 falsi positivi passati su 79** → Wilson 95% superiore **4,64%** (non 3,47%) → su 603 recuperi: punto **0**, **≤28** agganci sbagliati. Nota strutturale che restringe il rischio e che nessuno aveva scritto: perché un aggancio passi servono due persone con nome quasi identico **e** data entro 3 giorni; a parità di nome la data è indipendente, e su una finestra anagrafica realistica la collisione vale **~0,1%** — un ordine di grandezza sotto il bound empirico.

**Recuperi attesi: NON MISURATI sul codice corretto.** Due misure parziali divergono (18/18 dal prototipo dell'analisi, 0/9 sui candidati reali in cache dello scettico) e il fix sblocca 291 candidati di strato A che **nessun null valido copre**. Il rischio è limitato (≤28), la **resa no** → per il criterio del brief questo fronte è **non valutabile come consegnato**: si esegue un **pilota di 100 richieste stratificato per chiave (A/B/C/D)**, si misura la resa per strato, e solo allora si impegnano le restanti ~500.

---

### F · Le respinte con un titolo nuovo — 189 richieste, 3,2 minuti

Due sorgenti, in quest'ordine:

- **hatnote della pagina sbagliata che abbiamo già in cache**: **21,0%** [16,0; 27,1] contiene il titolo esatto col nostro anno, **43/43 link BLU, zero rossi**. Trovarlo costa **0 richieste**, prenderlo 1. Sonda su 8: pagina esistente **8/8**, aggancio corretto **7/8 = 87,5%** [52,9; 97,8];
- **titolo costruito alla cieca** `Nome (footballer, born AAAA)`: pagina esistente **8/20 = 40%**, aggancio corretto **6/20 = 30%** [14,5; 51,9]. Il **60% dà 404**, ed è la risposta onesta: quei giocatori una voce non ce l'hanno.

**Recuperati attesi ~81** (≈38 via hatnote + ≈44 alla cieca), range **44-118** — l'intervallo è largo per un motivo solo e dichiarato: il ramo cieco è misurato su **n=20**.

⚠️ **Il titolo con l'anno non è univoco**: `Burak Yilmaz (footballer, born 1995)` esiste ed è una **terza** persona (7 febbraio contro il nostro 27 novembre); idem `Romario (footballer, born 1992)` e `Liam Henderson (footballer, born 1996)`. Ogni pagina nuova **ripassa** dalla verifica. End-to-end: **16 pagine trovate → 13 attaccate → 0 identità sbagliate**, e le 3 scartate sono esattamente le 3 di un'altra persona. Fra le attaccate c'è `Pele (footballer, born 1991)` — il giovane brasiliano che dà il nome al caso peggiore dell'audit: **8 club su 8** coerenti anche negli anni. Stavolta prende la sua carriera, non quella di Pelé.

**Il passo rende la spesa permanente** (+1 richiesta su *ogni* futura respinta), non una-tantum. Trascurabile, ma va detto.

---

### Cosa NON conviene fare — due voci, con il numero

| non fare | perché, misurato |
|---|---|
| **ampliare `INTESTAZIONI_SENIOR`** | recupero **0/711**, IC95 [0%, 0,54%]. Le varianti prudenti iniettano 31 carriere NBA/ciclismo; `career` generico rompe il **93,2%** delle pagine buone (+7.701 spurie, −3.161 perse). |
| **provare `(footballer, born AAAA)` alla cieca sui 1.482 404 senza candidato** | 1.482 richieste per una resa **0/6** sul ramo puro-404, IC [0%, 39%], e l'argomento strutturale (il titolo disambiguato nasce solo quando il nudo è occupato, e allora il nudo dà una *disambigua*, non un 404) punta nella stessa direzione. Spendere 25 minuti per riconfermare un fatto già noto. |

---

## 2. Il codice

Da aggiungere a `src/data/wikipedia_careers.py` (dopo `verifica_identita`) e la modifica a `scripts/fetch_wikipedia_careers.py`. **Nessun file del repo è stato toccato.** Il codice **non aggira** `verifica_identita`: la usa come secondo stadio obbligatorio e, sul ramo-indice, la stringe (`solo_data=True`).

```python
# ===========================================================================
# RECUPERO DEI FALLITI DELLO STRATO 2 — proposta unificata (01/08/2026)
#
# Quattro meccanismi, un solo secondo stadio: `verifica_identita*`, MAI aggirata.
#   (1) classifica_pagina()      dice PERCHE' una pagina non ha dato carriera
#   (2) risolvi_da_indice()      pagina-indice -> il titolo giusto (1 richiesta)
#   (3) verifica_identita_v2()   club x ANNI + forma del Delta + corroborazione
#   (4) gazetteer + varianti     404 -> titoli VERI letti dalla cache (0 richieste)
#
# Dipendenze: solo quelle gia' nel modulo (re, gzip, glob, os, urllib.parse,
# dataclass/field, BeautifulSoup, datetime, unicodedata).
# ===========================================================================

import collections
import datetime as _dt
import glob
import os
import unicodedata as _ud


# ─────────────────────────────────────────────────────────────────────────────
# (1) PERCHE' la pagina non ha dato una carriera. Zero richieste: legge la cache.
# ─────────────────────────────────────────────────────────────────────────────

_FIRMA_CALCIO = "club domestic league appearances and goals"

def classifica_pagina(html: str) -> str:
    """Sostituisce il test `if "infobox" not in html`, che NON testa cio' che dice.

    La stringa "infobox" sta nel CSS TemplateStyles incorporato in quasi ogni
    voce, disambigue comprese (R6): **278 delle 711** pagine finite in
    `nessun_blocco` non hanno NESSUN `<table class="infobox">`, e **215** di
    quelle sono disambigue. Il confine fra `nessun_infobox` e `nessun_blocco`
    e' arbitrario: sono lo stesso fenomeno.

    Censimento completo dei 711 `nessun_blocco` (tutti in cache, 0 richieste):
      soggetto_diverso  320 (45,0%)   NBA, baseball, ciclismo, citta', santi, re
      disambigua        220 (30,9%)
      pagina_di_nome    154 (21,7%)   liste antroponimiche
      senza_infobox      14 ( 2,0%)
      senza_blocco        3 ( 0,4%)   biografie di calcio VERE — tutte e tre omonimi
    Cioe': il 99,6% di questo fronte non e' parsing, e' la pagina sbagliata.

    ⚠️ La firma usata per «e' una voce di calcio» NON sono le categorie: la voce
    del GOLFISTA Sergio Garcia porta tre categorie di calcio, fra cui «Men's
    association football players not categorized by position» (R4: anomalia
    dichiarata anche se non e' un errore nostro). La firma affidabile e' la nota
    a pie' d'infobox `* Club domestic league appearances and goals`, presente in
    1.998/1.999 pagine `ok` = **99,95%** -> falsi «soggetto_diverso» ~0,4/711.
    """
    soup = BeautifulSoup(html, "lxml")
    if soup.find(id="disambigbox") or "Category:All_disambiguation_pages" in html:
        return "disambigua"
    sd = soup.find("div", class_="shortdescription")
    sd = sd.get_text(" ", strip=True) if sd else ""
    if re.search(r"name list|given name|surname|list of people with the same", sd, re.I):
        return "pagina_di_nome"
    cats = " ".join(a.get_text() for a in soup.select("#mw-normal-catlinks li a")).lower()
    if "disambiguation" in cats or "given name" in cats or "surname" in cats:
        return "pagina_di_nome"
    if _FIRMA_CALCIO in html.lower():
        return "senza_blocco"            # e' una voce di calcio: manca il dato
    if soup.find("table", class_=_e_infobox) is None:
        return "senza_infobox"
    return "soggetto_diverso"


STATI_INDICE = ("disambigua", "pagina_di_nome", "soggetto_diverso")


# ─────────────────────────────────────────────────────────────────────────────
# (2) La pagina sbagliata e' una TABELLA DI INSTRADAMENTO
# ─────────────────────────────────────────────────────────────────────────────

NS_ESCLUSI = ("Category:", "Help:", "Wikipedia:", "File:", "Template:",
              "Portal:", "Special:", "Talk:", "Module:", "MOS:", "WP:")
SEZ_ESCLUSE = ("see also", "references", "external links", "places",
               "other uses", "fictional", "ships", "further reading",
               "in fiction", "music", "films")

# ⚠️ MAPPA COMPLETA (96 voci). Il codice proposto dall'analisi ne aveva 75:
# 23 paesi persi = **219/3.545 = 6,2% del fronte** che perde il segnale
# nazionalita' E, con `dem=()`, anche il -2,0 per nazionalita' SBAGLIATA —
# l'anno decide da solo. R6 applicato al codice: nessuna eccezione, degrado
# silenzioso. Una nazione assente non rompe nulla ma abbassa la copertura e
# alza il rischio, entrambi in silenzio.
DEMONIMI: dict[str, tuple[str, ...]] = {
    "Brazil": ("brazilian",), "Spain": ("spanish",), "Portugal": ("portuguese",),
    "England": ("english",), "Scotland": ("scottish",), "Wales": ("welsh",),
    "Ireland": ("irish",), "Northern Ireland": ("northern irish",),
    "France": ("french",), "Italy": ("italian",), "Germany": ("german",),
    "Netherlands": ("dutch",), "Argentina": ("argentine", "argentinian"),
    "Russia": ("russian",), "Denmark": ("danish",), "Sweden": ("swedish",),
    "Norway": ("norwegian",), "Belgium": ("belgian",), "Poland": ("polish",),
    "Croatia": ("croatian",), "Serbia": ("serbian",), "Turkey": ("turkish",),
    "Türkiye": ("turkish",), "Greece": ("greek",), "Austria": ("austrian",),
    "Switzerland": ("swiss",), "Ukraine": ("ukrainian",),
    "Colombia": ("colombian",), "Uruguay": ("uruguayan",), "Mexico": ("mexican",),
    "Chile": ("chilean",), "Japan": ("japanese",), "Korea South": ("south korean",),
    "United States": ("american",), "Nigeria": ("nigerian",), "Ghana": ("ghanaian",),
    "Senegal": ("senegalese",), "Cote d'Ivoire": ("ivorian",),
    "Ivory Coast": ("ivorian",), "Cameroon": ("cameroonian",),
    "Morocco": ("moroccan",), "Algeria": ("algerian",), "Tunisia": ("tunisian",),
    "Egypt": ("egyptian",), "Czech Republic": ("czech",), "Slovakia": ("slovak",),
    "Hungary": ("hungarian",), "Romania": ("romanian",), "Finland": ("finnish",),
    "Iceland": ("icelandic",), "Israel": ("israeli",), "Australia": ("australian",),
    "Canada": ("canadian",), "Bosnia-Herzegovina": ("bosnian",),
    "Albania": ("albanian",), "Kosovo": ("kosovar", "kosovan"),
    "North Macedonia": ("macedonian",), "Montenegro": ("montenegrin",),
    "Slovenia": ("slovenian", "slovene"), "Bulgaria": ("bulgarian",),
    "Georgia": ("georgian",), "Armenia": ("armenian",), "Azerbaijan": ("azerbaijani",),
    "Congo": ("congolese",), "DR Congo": ("congolese",), "Mali": ("malian",),
    "Guinea": ("guinean",), "Guinea-Bissau": ("bissau-guinean",),
    "Angola": ("angolan",), "Gabon": ("gabonese",), "Benin": ("beninese",),
    "Togo": ("togolese",), "Burkina Faso": ("burkinabe",),
    "Cape Verde": ("cape verdean",), "Mozambique": ("mozambican",),
    "South Africa": ("south african",), "Zimbabwe": ("zimbabwean",),
    "Kenya": ("kenyan",), "Jamaica": ("jamaican",), "Costa Rica": ("costa rican",),
    "Honduras": ("honduran",), "Panama": ("panamanian",), "China": ("chinese",),
    "Iran": ("iranian",), "Iraq": ("iraqi",), "Estonia": ("estonian",),
    "Latvia": ("latvian",), "Lithuania": ("lithuanian",),
    "Belarus": ("belarusian",), "Moldova": ("moldovan",), "Cyprus": ("cypriot",),
    "Peru": ("peruvian",), "Ecuador": ("ecuadorian",), "Venezuela": ("venezuelan",),
    "Paraguay": ("paraguayan",), "Bolivia": ("bolivian",),
    "New Zealand": ("new zealand",), "Kazakhstan": ("kazakh", "kazakhstani"),
}
_TUTTI_DEMONIMI = {x for v in DEMONIMI.values() for x in v}

RUOLI: dict[str, tuple[str, ...]] = {
    "Goalkeeper": ("goalkeeper", "keeper"),
    "Defender": ("defender", "centre-back", "center-back", "full-back", "back", "defence"),
    "Midfield": ("midfielder", "midfield"),
    "Attack": ("forward", "striker", "winger", "attacker"),
}

_MESI = {m: i + 1 for i, m in enumerate(
    ("january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"))}

_RE_NATO = re.compile(r"born\s+(?:\d{1,2}\s+)?([A-Za-z]+)?\s*(?:\d{1,2},?\s*)?(\d{4})")
_RE_CALCIO = re.compile(r"footballer|football player|soccer", re.I)
_RE_HREF = re.compile(
    r"^(?:https?:)?//[a-z-]+\.wikipedia\.org/wiki/(.+)$|^/wiki/(.+)$", re.I)

# Punto operativo del selettore, misurato il 01/08/2026 sulle 2.490 pagine-indice:
#   (soglia, margine)   copertura   placebo (profilo NON sulla pagina)
#      (3, 2)             88,6%       8,35%
#      (5, 3)  <-- qui    86,1%       6,30% [5,79%, 6,83%]
#      (7, 5)             77,7%       3,63%
#      anno + (mese|club) obbligatori:  10,2% / 0,10%
# Stringere costa 8 punti di copertura per 3 di placebo; stringere davvero ne
# costa 76 per 6,2. E non serve, perche' la difesa e' `verifica_identita` a
# valle. ⚠️ MA il placebo ADVERSARIALE (impostore con stessa nazionalita' E
# stesso anno) e' **77,0%** [76,1%, 77,9%]: da solo il selettore NON basta,
# mai riusarlo senza il secondo stadio.
SOGLIA = 5.0
MARGINE = 3.0

_STOP_CLUB = {"fc", "cf", "sc", "ac", "as", "cd", "ud", "sv", "afc", "club",
              "de", "of", "the", "city", "united", "real", "athletic",
              "atletico", "sporting", "racing", "deportivo", "ii", "b", "and"}


@dataclass
class Candidato:
    """Una riga di pagina-indice: link a persona + il testo che la descrive.

    Il testo e' oro: `Koke (footballer, born 1992), full name Jorge
    Resurreccion Merodio, Spanish football midfielder for Atletico Madrid` da
    solo basta. Aprire il link e' l'unica cosa che costa una richiesta.
    """
    titolo: str
    testo: str
    sezione: str = ""
    punteggio: float = 0.0
    dettaglio: dict = field(default_factory=dict)


def _norm(s: str) -> str:
    s = _ud.normalize("NFKD", s)
    s = "".join(c for c in s if not _ud.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def _titolo_da_href(href: str) -> str | None:
    """`/wiki/X`, `//en.wikipedia.org/wiki/X`, `https://en.wikipedia.org/wiki/X`.

    ⚠️ Nella cache gli href del CORPO sono **protocollo-relativi assoluti**
    (`//en.wikipedia.org/wiki/...`); i `/wiki/...` relativi sono SOLO la
    navigazione del sito (`/wiki/Main_Page`, `/wiki/Special:Random`). Un parser
    che accetta solo la forma relativa estrae **0 link a calciatori su 250
    disambigue** e non solleva nulla: sembra funzionare. Verificato: `title=`
    ne trova 232/250 = 92,8%.
    ⚠️ Non e' vero, come si era scritto, che «convivono due dialetti HTML»: su
    500 pagine campionate il **100%** contiene `href="/wiki/`. La regola
    operativa (usare `title=`, mai `href^=/wiki/`) e' giusta; la diagnosi
    «pagine Parsoid» era sbagliata e chi la cercasse non la troverebbe.
    """
    m = _RE_HREF.match(href.split("#")[0])
    return (m.group(1) or m.group(2)) if m else None


def e_pagina_indice(html: str, minimo: int = 2) -> bool:
    """La pagina e' un ELENCO DI PERSONE omonime, non una voce?

    Due segnali in OR: la **dichiarazione** di Wikipedia (disambigbox/categoria)
    e la **forma** (>=2 righe «... (born AAAA), ...»). Il secondo serve perche'
    le voci di nome proprio non si dichiarano disambigue; il primo perche' le
    disambigue corte non hanno righe a sufficienza.

    Ri-eseguito su HEAD: pagine-indice fuori da `nessun_infobox` -> **376/711**
    `nessun_blocco`, **24/315** `errore`, e **0/205** `identita_non_confermata`
    (controllo negativo: quelle sono voci VERE di un'altra persona, fronte
    diverso, e vengono correttamente lasciate stare).
    Non-regressione, provata direttamente: su **2.866** pagine classificate
    INDICE, **0** contengono la nostra data di nascita; delle 2.490
    `nessun_infobox` indice, **0** hanno uno `span.bday`.
    """
    soup = BeautifulSoup(html, "lxml")
    if soup.find(id="disambigbox") or soup.find(class_="dmbox"):
        return True
    cats = " ".join(a.get_text() for a in soup.select("#mw-normal-catlinks li a")).lower()
    if "disambiguation" in cats or "given name" in cats or "surname" in cats:
        return True
    return sum(1 for c in estrai_candidati(html) if "born" in c.testo.lower()) >= minimo


def estrai_candidati(html: str) -> list[Candidato]:
    """Le righe di elenco che puntano a una persona. Zero richieste."""
    soup = BeautifulSoup(html, "lxml")
    body = soup.find("div", class_="mw-parser-output")
    if body is None:
        return []
    sezione, out, visti = "", [], set()
    for el in body.find_all(["h2", "h3", "li"]):
        if el.name in ("h2", "h3"):
            sezione = el.get_text(" ", strip=True).lower()
            continue
        if any(s in sezione for s in SEZ_ESCLUSE):
            continue
        # ⚠️ `find_parent(class_=re.compile("...|toc"))` risale fino a <html>,
        # che su Vector-2022 porta la classe `vector-toc-available`: la regola
        # «salta le righe dentro un TOC» scartava OGNI riga di OGNI pagina.
        # Si risale a mano e ci si ferma al corpo voce.
        cattivo = False
        for anc in el.parents:
            if anc is body:
                break
            if {"navbox", "reflist", "catlinks", "toc", "hatnote"} & set(anc.get("class") or []):
                cattivo = True
                break
        if cattivo:
            continue
        testo = el.get_text(" ", strip=True)
        if not testo or len(testo) > 400:
            continue
        link = None
        for a in el.find_all("a", href=True):
            t = _titolo_da_href(a["href"])
            if t is None or any(t.startswith(n) for n in NS_ESCLUSI):
                continue
            if "disambiguation" in t.lower():
                continue
            link = t
            break
        if link is None or link in visti:
            continue
        visti.add(link)
        out.append(Candidato(titolo=link, testo=testo, sezione=sezione))
    return out


def _anni_e_mese(c: Candidato) -> tuple[set[int], int | None]:
    """Anni di nascita citati nella riga, e il mese se dichiarato.

    Il mese risolve i casi altrimenti indecidibili: «Ederson (footballer, born
    January 1986)» contro «born March 1986» sono due brasiliani, stesso anno,
    stesso ruolo. Senza il mese sono indistinguibili; col mese uno fa 10,0 e
    l'altro 4,0.
    """
    src = c.titolo.replace("_", " ") + " || " + c.testo
    anni, mese = set(), None
    for m in _RE_NATO.finditer(src):
        anni.add(int(m.group(2)))
        if m.group(1) and m.group(1).lower() in _MESI:
            mese = _MESI[m.group(1).lower()]
    return anni, mese


def punteggio_candidato(c: Candidato, prof: dict) -> tuple[float, dict]:
    """Punteggio della riga per `prof` = {anno, mese, paese, ruolo, club_noti}.

    I pesi sono ORDINI DI GRANDEZZA, non un'ottimizzazione: l'anno domina (e'
    l'unico campo quasi sempre presente e quasi sempre discriminante), mese e
    club corroborano, nazionalita' e ruolo fanno da rompi-parita'.
      anno   +5,0 / -5,0 (off-by-1: -1,5)     mese  +2,0 / -4,0
      club   +2,5 (max 2)                     naz   +2,0 / -2,0
      ruolo  +1,0 / -1,5                      non-calciatore -6,0

    ⚠️ Il ruolo e' FRAGILE: `position` nel nostro dataset e' la posizione
    attuale/prevalente, la riga d'indice descrive spesso il ruolo d'inizio
    carriera. Pesa poco apposta, ma su un riconvertito puo' togliere 2,5 punti
    al candidato giusto: e' una delle cause plausibili delle 275 astensioni.
    """
    src = _norm(c.titolo.replace("_", " ") + " " + c.testo)
    d: dict = {}
    s = 0.0
    d["calcio"] = bool(_RE_CALCIO.search(c.titolo.replace("_", " ") + " " + c.testo)) \
        or "football" in c.sezione or "soccer" in c.sezione

    anni, mese = _anni_e_mese(c)
    d["anni_riga"] = sorted(anni)
    if prof.get("anno") and anni:
        if prof["anno"] in anni:
            s += 5.0
            d["anno"] = "match"
            if mese is not None:
                if prof.get("mese") == mese:
                    s += 2.0; d["mese"] = "match"
                else:
                    s -= 4.0; d["mese"] = "discorde"
        elif min(abs(a - prof["anno"]) for a in anni) == 1:
            s -= 1.5; d["anno"] = "off_by_1"
        else:
            s -= 5.0; d["anno"] = "discorde"
    else:
        d["anno"] = "assente"

    dem = DEMONIMI.get(prof.get("paese") or "", ())
    if dem:
        if any(x in src for x in dem):
            s += 2.0; d["naz"] = "match"
        elif any(x in src for x in _TUTTI_DEMONIMI - set(dem)):
            s -= 2.0; d["naz"] = "altra"
        else:
            d["naz"] = "assente"

    kw = RUOLI.get(prof.get("ruolo") or "", ())
    if kw:
        if any(k in src for k in kw):
            s += 1.0; d["ruolo"] = "match"
        elif any(k in src for p, v in RUOLI.items() if p != prof.get("ruolo") for k in v):
            s -= 1.5; d["ruolo"] = "altro"
        else:
            d["ruolo"] = "assente"

    tok = set(src.split())
    n_club = sum(
        1 for cl in (prof.get("club_noti") or [])
        if (t := {x for x in _norm(cl).split() if x not in _STOP_CLUB and len(x) > 2})
        and t <= tok
    )
    d["club"] = n_club
    s += min(n_club, 2) * 2.5
    if not d["calcio"]:
        s -= 6.0
    c.punteggio, c.dettaglio = s, d
    return s, d


def scegli_da_indice(html, prof, *, soglia=SOGLIA, margine=MARGINE):
    """Sceglie la riga giusta, oppure **si astiene**.

    L'astensione e' una decisione, non un fallimento: costa zero richieste e
    zero rischio. Misurato su HEAD (2.490 pagine-indice `nessun_infobox`):
    scelto 2.145 = **86,1%**; astensioni 275 sotto soglia, 59 ambiguo,
    11 senza candidati.
    ⚠️ Il **63,0%** delle scelte ha s1 < 8 (anno + al piu' un segnale debole) e
    il **5,9%** (137 giocatori) ha s1 = 5,0 esatto, cioe' l'anno E BASTA.
    """
    val = []
    for c in estrai_candidati(html):
        s, _ = punteggio_candidato(c, prof)
        val.append((s, c))
    val.sort(key=lambda x: -x[0])
    diag = {"n_cand": len(val), "top": [(round(s, 2), c.titolo) for s, c in val[:3]]}
    if not val:
        return None, diag | {"motivo": "nessun_candidato"}
    s1, c1 = val[0]
    s2 = val[1][0] if len(val) > 1 else -99.0
    diag |= {"s1": s1, "s2": s2, "dettaglio": c1.dettaglio}
    if s1 < soglia:
        return None, diag | {"motivo": "sotto_soglia"}
    if s1 - s2 < margine:
        return None, diag | {"motivo": "ambiguo"}
    return c1, diag | {"motivo": "scelto"}


_RE_ANNO_TIT = re.compile(r"born\s+(?:\w+\s+)?(\d{4})")

def candidati_calcistici(html: str, anno_atteso: int | None) -> list[str]:
    """Fallback quando `scegli_da_indice` si astiene: i titoli-candidato letti
    dagli attributi `title=`, filtrati sull'anno di nascita atteso.

    E' il ramo che copre le pagine di SOGGETTO DIVERSO (NBA, ciclismo, citta'),
    dove non ci sono righe d'elenco descrittive ma i link ci sono comunque.
    Misurato sui 711 `nessun_blocco`, ri-derivato **per player_id** (fix R5:
    l'artefatto originale risolveva la data per NOME e i sei Danilo — 1984,
    1986, 1990, 1991, 1999, 2001 — finivano tutti su «Danilo (born 1986)»):
      almeno un candidato        395/711 = 55,6%
      ESATTAMENTE UNO con l'anno atteso  **137/711 = 19,3%** [16,5%, 22,3%]
      -> 137 titoli DISTINTI, 0 collisioni
    Precisione su 50 verifiche di rete: **46/50 = 92,0%** [81,2%, 96,8%]; i 4
    errori sono tutti omonimi nati lo STESSO ANNO, giorno diverso, e
    `verifica_identita` li respinge tutti e quattro -> **0/50 agganci sbagliati**.
    Si scarica SOLO se la lista ha lunghezza 1.
    """
    soup = BeautifulSoup(html, "lxml")
    corpo = soup.find("div", class_="mw-parser-output") or soup
    titoli: list[str] = []
    for a in corpo.find_all("a"):
        t = a.get("title")
        if not t or t in titoli:
            continue
        if "page does not exist" in t or t.startswith("Edit section"):
            continue
        if _RE_CALCIO.search(t):
            titoli.append(t)
    if anno_atteso is None:
        return titoli
    return [t for t in titoli
            if (m := _RE_ANNO_TIT.search(t)) and int(m.group(1)) == anno_atteso]


_RE_TEMPLATE = re.compile(
    r"^(.+?) \((?:footballer|soccer)(?:, born \d{4})?\)$|"
    r"^(.+?) \(\w+ footballer\)$", re.I)

def risolvi_da_indice(html, player_id, nome, lang="en", *, nascita_attesa=None,
                      paese=None, ruolo=None, club_noti=None, club_anni=None,
                      solo_data=True, **kw) -> Esito:
    """Dalla pagina-indice all'`Esito`. **Una** richiesta in piu'.

    ⚖️ DUE BARRIERE INDIPENDENTI, e vanno tenute distinte.
      1. il **selettore** sceglie quale riga aprire usando solo il testo
         dell'indice (0 richieste). Sbaglia il **6,30%** [5,79; 6,83] delle
         volte quando la persona giusta NON e' sulla pagina; se l'impostore ha
         anche lo stesso anno di nascita sbaglia il **77,0%**. DA SOLO NON BASTA:
         chi riusasse `scegli_da_indice` senza il secondo stadio introdurrebbe
         errori a due cifre percentuali.
      2. `verifica_identita*` giudica la pagina scaricata sulla data AL GIORNO.
         Su **20.394** impostori stesso-paese/stesso-anno ne fa passare il
         **2,10%** [1,91%, 2,31%] — il pavimento del paradosso dei compleanni
         (7/365 = 1,92%), non un difetto del codice.

    ⚠️ ONESTA' SUL RISCHIO (rettifica del 01/08/2026). Il ramo-indice **peggiora**
    la qualita' del DB, di poco ma misurabilmente: seleziona sull'anno e
    consegna al filtro **esattamente** il caso in cui il filtro e' piu' debole
    (year-matched per costruzione). Limite superiore STRATIFICATO per notabilita':
        <20 presenze :   812 scelte, z<=40,1% -> FP <= 0,927%  -> <= 7,5
        >=20 presenze: 1.538 scelte, z<=12,0% -> FP <= 0,277%  -> <= 4,3
        TOTALE <= 11,8 giocatori = **0,50%** (il DOPPIO del limite pooled 0,224%)
    Da confrontare con il residuo POST-filtro del ramo per-nome, 0,268% x 2,10%
    = **0,0056%** (~1,2 giocatori su 20.981). Il ramo-indice e' ~40x piu' sporco
    per recupero. Accettabile (0,02% del DB), ma e' un AUMENTO, non un pareggio.

    `solo_data=True` chiude la terza via: sul ramo-indice `quarantena` NON e'
    ammessa. Sul ramo per-nome una data discorde e' spesso un'anagrafica
    contestata; qui abbiamo scelto la pagina *proprio perche'* l'anno
    coincideva, quindi una data discorde e' un **sintomo**. Costo: **1,19%**.
    """
    nascita = str(nascita_attesa)[:10] if nascita_attesa else None
    anno = int(nascita[:4]) if nascita and len(nascita) >= 4 else None
    prof = {"anno": anno,
            "mese": int(nascita[5:7]) if nascita and len(nascita) >= 7 else None,
            "paese": paese, "ruolo": ruolo, "club_noti": list(club_noti or ())}

    cand, diag = scegli_da_indice(html, prof)
    titolo = urllib.parse.unquote(cand.titolo) if cand else None
    via = "selettore"
    if titolo is None:                       # fallback per le pagine-soggetto
        alt = candidati_calcistici(html, anno)
        if len(alt) == 1:
            titolo, via = alt[0], "titolo_instradato"
    if titolo is None:
        # stato NUOVO. Sta in STATI_DEFINITIVI (vedi il commento la'): senza,
        # le ~345 astensioni vengono riprocessate e RISCRITTE a ogni run, e i
        # contatori di stato si sdoppiano — e' gia' successo con i 312 `errore`
        # ritentati, che hanno costretto a deduplicare per player_id.
        return Esito(player_id, nome, None, "indice_non_risolto",
                     dettaglio=f"{diag['motivo']} | {diag.get('top')}")

    # CONTROLLO (regola Fase 98/99): il **83,9%** dei titoli scelti e'
    # generabile da template deterministici — `(footballer)` 24,6%,
    # `(footballer, born AAAA)` 54,0%, `(<Naz> footballer)` 5,2%. Il contributo
    # UNICO del selettore e' il 16,1% restante piu' un risparmio di 2-3x in
    # richieste. Registrarlo qui rende il confronto col controllo misurabile
    # a posteriori a costo zero, invece di attribuire al selettore recuperi che
    # un cambio di una riga otterrebbe.
    templ = bool(_RE_TEMPLATE.match(titolo))

    url = f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(titolo.replace(' ', '_'))}"
    try:
        pagina = fetch_page(titolo, lang, **kw)
    except Exception as e:                                   # pragma: no cover
        return Esito(player_id, nome, url, "errore", dettaglio=repr(e))
    if pagina is None:
        # ⚠️ stato PROPRIO, non `nessuna_pagina`: il loop chiamante fa
        # `if e.stato != "nessuna_pagina": break`, quindi restituire
        # `nessuna_pagina` lo farebbe proseguire con i suffissi, ognuno dei
        # quali rientra nel ramo-indice -> fino a 3 risoluzioni e 6 richieste
        # per un giocatore. Fuori budget.
        return Esito(player_id, nome, url, "indice_link_rotto",
                     dettaglio=f"link rotto sull'indice: {titolo}")

    tappe = parse_career(pagina, player_id, url)
    if not tappe:
        return Esito(player_id, nome, url, classifica_pagina(pagina),
                     dettaglio=f"via={via} titolo={titolo} template={templ}")
    bday = bday_pagina(pagina)
    identita = verifica_identita_v2(
        bday, nascita, tappe, club_anni,
        corrob=corroborazione(pagina, paese, ruolo))
    for t in tappe:
        t.identita = identita
    dett = f"via={via} titolo={titolo} template={templ}"
    if identita != "confermata_data" and (solo_data or identita in ("respinta", "quarantena")):
        return Esito(player_id, nome, url, "identita_non_confermata", tappe,
                     dettaglio=dett, bday_pagina=bday, identita=identita)
    return Esito(player_id, nome, url, "ok", tappe,
                 dettaglio=dett, bday_pagina=bday, identita=identita)


# ─────────────────────────────────────────────────────────────────────────────
# (3) LA VERIFICA D'IDENTITA', VERSIONE 2 — club x ANNI, forma del Delta,
#     corroborazione. NON sostituisce `verifica_identita`: la estende.
# ─────────────────────────────────────────────────────────────────────────────

_STOP_CLUB_V2 = {"fc","cf","ac","sc","afc","cd","ud","sd","ss","as","club","de",
                 "futbol","football","calcio","sa","sad","spa","s","p","a","the",
                 "sportiva","societa","atletico","e","associacao","esporte","clube",
                 "gmbh","co","kgaa","ev","f","c","u","d","team","kulubu","spor","ii","1"}

# ⚠️ TOKEN GENERICI — lista nera. Il matcher lasco (token condiviso >=4 caratteri)
# NON fa solo «i diacritici», come la sua motivazione dichiarava: su coppie di
# club DIVERSI della stessa lega coincide nel **2,32%** dei casi, e genera un k
# SPURIO nel **4,2%** [3,6; 4,9] contro un avversario della stessa lega senza
# club condivisi (matcher stretto: 2,6%). Colpevoli misurati: Manchester United
# ~ Newcastle United, Manchester City ~ Norwich City, Real Madrid ~ Real
# Sociedad, Inter Milan ~ AC Milan, Union Berlin ~ Hertha Berlin (20 coppie su
# 22 provate a mano). Aggravante: il **62%** delle quarantene e il **68%** delle
# respinte hanno UN SOLO club nello strato 1, quindi k=1 e' l'intera prova per
# la maggioranza della popolazione. Sulle popolazioni reali il danno NON si
# vede (quarantena 245 lasco vs 243 stretto) — e' un rischio latente, non un
# difetto attuale: si tiene il matcher lasco CON la lista nera.
_TOKEN_GENERICI = {"united", "city", "real", "sport", "sports", "deportivo",
                   "athletic", "atletico", "sporting", "racing", "olympique",
                   "dynamo", "spartak", "zagreb", "prague", "praha", "zurich",
                   "sydney", "berlin", "milan", "madrid", "london", "moscow"}


def _norm_club(s: str) -> str:
    """'Fudbalski Klub Rabotnicki Skopje' e 'Rabotnicki' devono coincidere.

    Il matcher precedente e' un `in` fra stringhe minuscole: i diacritici lo
    fanno fallire in silenzio. Costo misurato: Svyatoslav Georgievski, **4 club
    su 4** coincidenti anche negli anni, respinto per 5 giorni di scarto.
    """
    s = _ud.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9 ]", " ", s).lower()
    return " ".join(t for t in s.split() if t and t not in _STOP_CLUB_V2)


def club_coincide(nostro: str, loro: str) -> bool:
    a, b = _norm_club(nostro), _norm_club(loro)
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    comuni = {t for t in set(a.split()) & set(b.split())
              if len(t) >= 4 and t not in _TOKEN_GENERICI}
    return bool(comuni)


def coerenza_temporale(club_anni, tappe, *, tolleranza=1, anno_corrente=None):
    """Quanti club dello STRATO 1 la pagina conferma **anche negli anni**.

    `club_anni`: iterabile di `(nome_club, primo_anno, ultimo_anno)` da
    `appearances.csv` — quindi su `player_id`, immune all'omonimia.
    Ritorna `(k_club, k_club_e_anni, n_club)`.

    E' `k_club_e_anni` che discrimina: il solo NOME del club non basta, perche'
    padre e figlio giocano nello stesso club — Javier Olaizola padre al
    Mallorca negli anni '90 contro il nostro figlio al Mallorca 2025-26, 37
    anni di scarto, e la copertura-club lo confermava. Con le finestre: k=0.

    Sensibilita' misurata (almeno 1 club confermato anche negli anni):
      identita' CERTA  93,9%   |  QUARANTENA  95,8%
      RESPINTE          9,8%   |  placebo casuale  0,6%
    La quarantena non e' «intermedia»: e' SOPRA le confermate.
    (La proposta originale dava 96,9 / 99,1 / 11,8 / 1,1 — l'ordinamento regge,
     le cifre esatte no: non citarle senza rifare il conto.)

    ⚠️ `tolleranza=1` e' fissata a priori sulla grana annuale dell'infobox, NON
    ottimizzata per griglia. Alzarla aumenta recupero e falsi positivi; i numeri
    qui sopra valgono per 1.
    """
    anno_corrente = anno_corrente or _dt.date.today().year
    club_anni = list(club_anni or ())
    k_c = k_ct = 0
    for club, y0, y1 in club_anni:
        m_c = m_ct = False
        for t in tappe:
            if not club_coincide(club, t.club):
                continue
            m_c = True
            da, a = t.anno_da, t.anno_a
            if da is None and a is None:
                continue
            if a is None:
                a = anno_corrente if t.aperta else da
            if da is None:
                da = a
            if max(da, y0 - tolleranza) <= min(a + tolleranza, y1):
                m_ct = True
        k_c += m_c
        k_ct += m_ct
    return k_c, k_ct, len(club_anni)


def _data(x):
    if not x:
        return None
    try:
        return _dt.date.fromisoformat(str(x)[:10])
    except ValueError:
        return None


def livello_delta(bday, nascita_attesa) -> str:
    """Non «quanto» differiscono le due date, ma **come**.

    Misurato sulle **2.219 coppie di persone DIVERSE con lo stesso nome** dentro
    `players.csv`: solo lo **0,96%** ha le date entro 31 giorni, lo **0,25%**
    condivide giorno+mese, l'**8,96%** sta entro 366 giorni. Nella nostra
    quarantena: 53,1%, 8,1%, **94,8%**. Non e' un indizio, e' un rapporto di
    verosimiglianza schiacciante -> limite inferiore di miscela **pi >= 94,3%**
    (>= 89,9% con gli estremi di Wilson), e conservativo, perche' assume che
    nessun refuso vero superi l'anno (Chancel Mbemba: 6 anni, 5 club su 6).
    """
    a, b = _data(bday), _data(nascita_attesa)
    if a is None or b is None:
        return "ignoto"
    dd = abs((a - b).days)
    if dd <= 31:                                return "FORTE"    # giorno o mese
    if a.month == b.month and a.day == b.day:   return "FORTE"    # solo l'anno
    if a.day == b.month and a.month == b.day:   return "FORTE"    # gg/mm invertiti
    if dd <= 366:                               return "DEBOLE"
    return "ESTRANEO"


_RE_ALTEZZA = re.compile(r"(\d)\.(\d{2})\s*m")

def corroborazione(html: str, paese: str | None = None,
                   ruolo: str | None = None, altezza_cm: int | None = None):
    """Tre tratti INDIPENDENTI da data e club, gia' dentro l'HTML scaricato:
    nazionalita' (place of birth + categorie «X men's footballers»), ruolo,
    altezza +-3 cm. Zero richieste. Ritorna `(concordi, discordi)`.

    ⚠️ PRESI DA SOLI NON BASTANO, e va detto forte: Aaron Ramsey nato 1990
    corrobora 3 su 3 con il nostro nato 2003 (gallese, centrocampista, stessa
    statura) ed e' un'altra persona. Servono come TERZO voto, dopo club x anni.
    Sono anche RUMOROSI sulla popolazione sbagliata: altezza e nazionalita' sono
    contestate fra le fonti proprio per i giocatori la cui data e' contestata.

    Confronto quarantena promossa vs identita' CERTA (R7, con potenza):
      nazionalita' -1,8% IC95 [-6,2; +2,6]  (MDE 80%: 6,3%)
      ruolo        +4,7%      [-0,5; +9,9]  (MDE 80%: 7,4%)
      altezza      -2,8%      [-7,0; +1,4]  (MDE 80%: 6,0%)
    Tutti e tre a cavallo dello zero: una contaminazione >=6-7% l'avremmo vista.
    Il **nullo giusto non e' «un giocatore a caso»** (nazionalita' concorde solo
    il 2,0% delle volte) ma **un omonimo**: 65,3%. Gli omonimi condividono la
    nazionalita' quasi due volte su tre — e' la stessa confondente dei mononimi.
    """
    testo = BeautifulSoup(html, "lxml").get_text(" ", strip=True).lower()
    conc = disc = 0
    dem = DEMONIMI.get(paese or "", ())
    if dem:
        if any(x in testo for x in dem):
            conc += 1
        elif any(x in testo for x in _TUTTI_DEMONIMI - set(dem)):
            disc += 1
    kw = RUOLI.get(ruolo or "", ())
    if kw:
        if any(k in testo for k in kw):
            conc += 1
        elif any(k in testo for p, v in RUOLI.items() if p != ruolo for k in v):
            disc += 1
    if altezza_cm and (m := _RE_ALTEZZA.search(testo)):
        h = int(m.group(1)) * 100 + int(m.group(2))
        conc += abs(h - altezza_cm) <= 3
        disc += abs(h - altezza_cm) > 3
    return conc, disc


def verifica_identita_v2(bday, nascita_attesa, tappe, club_anni=None,
                         corrob=(0, 0), tolleranza_giorni=3) -> str:
    """Tre assi INDIPENDENTI, non una cascata.
    Esiti: `confermata_data` · `confermata_coerenza` · `quarantena` · `respinta`.

    ⚠️ NUMERO RITIRATO. Lo «0,11% di falsi positivi» pubblicato viene da un
    placebo che condivide un club ma ha **un altro nome**: in produzione quel
    avversario non puo' presentarsi, perche' si scarica `/wiki/<Nome>` e chi si
    incontra e' per forza un **omonimo**. E i due avversari differiscono proprio
    sull'asse a cui si attribuiva il taglio di 40x:
        corroborazione passa    omonimo 13,9% [7,7; 23,7]  vs  stesso-club 2,3%
        nazionalita' concorde   omonimo 65,3%              vs  stesso-club 23,9%
    Sull'avversario VERO: **0/72 = 0,0% [0,0; 5,1]**; condizionato ai club
    condivisi n=3 -> [0; 56]. **Nessuna potenza**, e va dichiarato (R7).
    Con ~38 incontri attesi: **0-2 righe** di falso positivo.

    ⚠️ LA GUARDIA `n_club > 0` E' OBBLIGATORIA. Senza, il ramo `k==0 ->
    respinta` confonde PROVA CONTRARIA e ASSENZA DI PROVA: **6 delle 11**
    respinte hanno ZERO club nello strato 1 (`appearances.csv` non li copre), e
    **4 di queste hanno Delta FORTE** — Tayrell Wouter 4 giorni, Simone
    Dell'Agnello 10, Yarin Levi 14, Logan Ross 18. Sono quasi certamente la
    persona giusta, oggi stanno nel DB come `ok`, e senza la guardia la regola
    li CANCELLA: ~4 identita' corrette perse per rimuoverne 3 sbagliate. E'
    R6 commessa dalla regola scritta per far rispettare R6.
    """
    senior = [t for t in tappe if not t.giovanili] or list(tappe)
    _, k, n_club = coerenza_temporale(club_anni or [], senior)
    liv = livello_delta(bday, nascita_attesa)
    conc, disc = corrob

    a, b = _data(bday), _data(nascita_attesa)
    if a and b and abs((a - b).days) <= tolleranza_giorni:
        return "confermata_data"

    if n_club == 0:
        # nessun club nello strato 1: non c'e' evidenza indipendente, ne' PRO
        # ne' CONTRO. Non si promuove e non si cancella.
        return "quarantena" if liv == "FORTE" else "respinta"
    if k == 0:
        # club noti che la pagina NON conferma negli anni: prova contraria.
        # E' qui che cadono le 3 identita' davvero sbagliate (Olaizola 1969
        # contro il nostro 2007 con lo stesso Mallorca; Bruno Alves 1981/1990;
        # Nilson Junior 1975/1991).
        return "respinta"
    if liv == "FORTE":
        return "confermata_coerenza"
    if liv == "DEBOLE":
        return "confermata_coerenza" if (conc >= 2 and disc == 0) else "quarantena"
    if liv == "ignoto":
        return "confermata_coerenza" if k >= 2 else "quarantena"
    return "quarantena"       # ESTRANEO: giudizio umano, mai promozione automatica


# ─────────────────────────────────────────────────────────────────────────────
# (4) I 404 — il titolo giusto non si INDOVINA, si LEGGE dalla cache
# ─────────────────────────────────────────────────────────────────────────────

# ⚠️ Il filtro sui link rossi via `class="new"` e' INERTE: gli href dei red link
# contengono `?action=edit&redlink=1` e sono gia' esclusi da `[^"?#]+`. Il
# risultato (niente link rossi) e' giusto, il meccanismo dichiarato no.
_RE_WIKILINK = re.compile(
    rb'rel="mw:WikiLink" href="https://en\.wikipedia\.org/wiki/([^"?#]+)"')

_ONORIFICI = frozenset({"jr", "sr", "ii", "iii", "jnr", "snr"})
# Due falsi positivi VERI venivano dallo stesso bug — «Jr.» usato come cognome:
# Charly Musonda Jr. -> Chavo Guerrero Jr. (un wrestler, 1970 contro 1996) e
# Aleksey Eremenko Jr. -> Alejandro Alvarado Jr. Due nomi che condividono un
# suffisso onorifico non condividono niente (R6).

_IPOCORISTICI = {
    "konstantinos": {"kostas"}, "georgios": {"giorgos", "yorgos"},
    "athanasios": {"thanasis", "sakis"}, "ioannis": {"giannis", "yiannis"},
    "emmanouil": {"manolis"}, "charalampos": {"babis", "charis"},
    "anastasios": {"tasos"}, "dimosthenis": {"dimos"}, "eleftherios": {"lefteris"},
    "panagiotis": {"panos"}, "vasilios": {"vasilis"}, "nikolaos": {"nikos"},
    "dimitrios": {"dimitris"}, "stylianos": {"stelios"}, "efstathios": {"stathis"},
    "theodoros": {"thodoris"}, "alexandros": {"alexis"}, "evangelos": {"vangelis"},
    "efthymios": {"efthymis"},
}


def _piatto(s: str) -> str:
    s = "".join(c for c in _ud.normalize("NFD", str(s))
                if _ud.category(c) != "Mn")
    for a, b in (("ø","o"),("Ø","O"),("æ","ae"),("Æ","Ae"),("ð","d"),("Ð","D"),
                 ("ł","l"),("Ł","L"),("đ","d"),("Đ","D"),("þ","th"),("Þ","Th"),
                 ("ı","i"),("İ","I"),("ß","ss")):
        s = s.replace(a, b)
    return s


def _tok(s: str) -> list[str]:
    return re.sub(r"[^a-z0-9 ]", " ", _piatto(s).lower()).split()


def _collassa(t: str) -> str:
    """Collassa le differenze di TRASLITTERAZIONE, non quelle di persona.

    Ogni sostituzione ha un caso misurato dietro:
      g/h    Gromov -> Hromov, Bogdanov -> Bohdanov   (ucraino: г e' h nello
             schema ufficiale, g in quello di Transfermarkt);
      j/i/y  Pesjakov -> Pesyakov, Ilya -> Illia      (russo/ucraino);
      w/v    Wagner/Vagner;  z/s  Adzic/Adzic;  ck/k;
      doppie e ie/ei -> e:   Matvienko -> Matviyenko.
    Una sola chiave copre insieme ucraino, russo, bielorusso e kazako: non serve
    una regola per lingua, serve una metrica che ignori l'asse su cui le lingue
    differiscono.
    """
    t = t.replace("kh", "h").replace("ch", "h")
    t = (t.replace("g","h").replace("j","i").replace("y","i")
          .replace("ck","k").replace("w","v").replace("z","s"))
    t = re.sub(r"(.)\1+", r"\1", t)
    return t.replace("ie", "e").replace("ei", "e")


def chiavi(nome: str) -> tuple[str, str, str, str]:
    """A grafia · B traslitterazione · C ordine · D cognome."""
    tok = _tok(nome)
    if not tok:
        return "", "", "", ""
    utili = [t for t in tok if t not in _ONORIFICI] or tok
    piatto = "".join(tok)
    return (piatto, _collassa(piatto),
            "|".join(sorted(_collassa(t) for t in utili)), _collassa(utili[-1]))


_RE_QUALIF = re.compile(r"^(.+?)\s*\((?:footballer|soccer)[^)]*\)$", re.I)

def costruisci_gazetteer(cache_dir=None) -> dict[str, list[str]]:
    """I titoli REALI di en.wikipedia linkati dalle pagine gia' in cache.

    Zero richieste. Misurato il 01/08/2026 su **24.052** file: **186.562**
    titoli, ~70 s.
    ⚠️ Il «218.026 titoli / 35 s» pubblicato NON si riproduce e va ritirato:
    con un SOVRAINSIEME dei file lo stesso codice ne da' meno, il che e'
    impossibile (l'insieme e' monotono nei file). Cade con esso anche il
    «volano ~4 titoli nuovi per pagina».
    ⚠️ Le pagine in cache sono HTML Parsoid: i link del corpo sono ASSOLUTI. Un
    parser che cerca `href="/wiki/` trova 5 link per pagina invece di 450.

    NOVITA': i titoli DISAMBIGUATI vengono indicizzati **anche per la loro forma
    base**. Motivo misurato: il claim «un 404 sul nome nudo significa che quel
    nome non esiste in nessuna forma» e' **falso** — 19 controesempi su 2.085
    gia' dentro la cache (`Lasse Sorensen` -> `Lasse Sørensen (footballer, born
    1999)`; `Nikola Stankovic` -> `Nikola Stankovic (footballer, born 1993)`).
    Costa zero e vale **+16 recuperi**.
    """
    cache_dir = str(cache_dir or (CACHE_DIR / "en"))
    titoli: set[str] = set()
    for p in glob.glob(os.path.join(cache_dir, "*.html.gz")):
        try:
            raw = gzip.decompress(open(p, "rb").read())
        except Exception:
            continue
        for m in _RE_WIKILINK.finditer(raw):
            t = urllib.parse.unquote(
                m.group(1).decode("utf-8", "replace")).replace("_", " ")
            if ":" in t:
                continue
            if 1 < len(t.split()) <= 6:
                titoli.add(t)
    idx: dict[str, list[str]] = collections.defaultdict(list)
    for t in titoli:
        forme = [t]
        if (m := _RE_QUALIF.match(t)):
            forme.append(m.group(1).strip())     # indicizza anche la forma base
        for f in forme:
            a, b, c, d = chiavi(f)
            if 1 < len(f.split()) <= 4:
                for k in (f"A{a}", f"B{b}", f"C{c}", f"D{d}"):
                    if t not in idx[k]:
                        idx[k].append(t)
    return dict(idx)


def _prefisso(a: str, b: str) -> int:
    a, b = _piatto(a).lower(), _piatto(b).lower()
    k = 0
    for x, y in zip(a, b):
        if x != y:
            break
        k += 1
    return k


def _nome_compatibile(a: str, b: str) -> bool:
    """Filtro della chiave D: il nome di battesimo dev'essere la stessa persona.

    Senza, la chiave-cognome aggancia «Adu Ares» -> «Austin Aries» e «Dong-jun
    Lee» -> «Derrek Lee». Con: >=3 lettere iniziali in comune (Javi/Javier,
    Alex/Alejandro, Nikolaos/Nikos) o lista chiusa di ipocoristici greci.
    """
    if _prefisso(a, b) >= 3:
        return True
    fa, fb = _piatto(a).lower(), _piatto(b).lower()
    return any((fa == L and fb in S) or (fb == L and fa in S)
               for L, S in _IPOCORISTICI.items())


def _titolo_norm(t: str) -> str:
    """Identita' di un TITOLO: l'URL esatto, diacritici COMPRESI."""
    return t.replace("_", " ").strip().lower()


def varianti_da_gazetteer(nome, idx, max_per_chiave=2):
    """I titoli candidati per un nome che ha dato 404, in ordine di fiducia.

    ⚠️ FIX OBBLIGATORIO. La versione precedente inizializzava il dedup con
    `visti = {chiavi(nome)[0]}` e poi scartava i candidati con
    `chiavi(t)[0] in visti`: ma ogni titolo indicizzato sotto `A{a}` ha per
    costruzione **la stessa chiave A**, quindi lo strato A era STRUTTURALMENTE
    irraggiungibile. Eseguito sul fronte: 301 candidati, **strato A = 0**
    invece di 291 — il **48%** della resa. Il dedup va fatto sull'**URL esatto
    gia' tentato**, non sulla chiave appiattita: e' esattamente il punto dello
    strato A che `Bosko Sutalo` e `Boško Šutalo` siano due URL diversi con la
    stessa forma appiattita.
    Con il fix, sul fronte attuale (2.085 `nessuna_pagina`): **587 candidati** —
    A 291 · B 142 · C 48 · D 106.

    ⚠️ LA RESA NON SI ESTRAPOLA. Per blocchi di raccolta, a gazetteer costante:
    **46,6% -> 29,6% -> 22,4% -> 16,1%**. La raccolta e' ordinata per priorita' e
    il gazetteer contiene i *linkati*, cioe' i famosi: i ~3.000 ancora da fare
    renderanno ~16%, non 34%.

    ⚠️ IL RISCHIO NON E' CONFINATO ALLA CHIAVE D, come si era scritto. Dei 587
    candidati reali, 9 hanno la pagina gia' in cache: **9 su 9 sono un'altra
    persona**, e uno e' di **strato A** (`Alex Sola` -> `Álex Sola`, 1999-06-09
    contro 2003-12-14). Tutti e 9 respinti dal giudice-data.
    """
    a, b, c, d = chiavi(nome)
    tentati = {_titolo_norm(nome)}
    fuori: list[tuple[str, str]] = []
    for chiave, strato in ((f"A{a}", "A-grafia"), (f"B{b}", "B-translit"),
                           (f"C{c}", "C-ordine")):
        for t in idx.get(chiave, [])[:max_per_chiave]:
            tn = _titolo_norm(t)
            if tn in tentati:
                continue
            tentati.add(tn)
            fuori.append((t, strato))
    if fuori:
        return fuori[:max_per_chiave]           # D = ultima spiaggia
    primo = (_tok(nome) or [""])[0]
    for t in idx.get(f"D{d}", [])[:8]:
        tk = _tok(t)
        tn = _titolo_norm(t)
        if tk and tn not in tentati and _nome_compatibile(primo, tk[0]):
            tentati.add(tn)
            fuori.append((t, "D-cognome"))
    return fuori[:max_per_chiave]


def recupera_404(player_id, nome, idx, *, nascita_attesa, club_noti=None,
                 club_anni=None, paese=None, ruolo=None, **kw) -> Esito:
    """Un tentativo di recupero. UNA richiesta per candidato, al massimo 2.

    ⚠️ Sul percorso-variante si accetta SOLO `confermata_data`: il nome non e'
    piu' una prova d'identita' (l'abbiamo cambiato noi), quindi l'unica prova
    indipendente che resta e' la data di nascita — presente per il **100%** dei
    2.085. La conferma-da-club, ragionevole sul titolo esatto, qui sarebbe
    circolare, e rinunciarci non costa nulla.

    ⚠️ RESA NON MISURATA sul codice corretto: due misure parziali divergono
    (18/18 dal prototipo, 0/9 sui candidati reali gia' in cache) e il fix
    sblocca 291 candidati di strato A che nessun null valido copre. Eseguire
    prima un **pilota di 100 richieste stratificato per chiave**, misurare la
    resa per strato, e solo allora impegnare le restanti ~500.
    """
    for titolo, strato in varianti_da_gazetteer(nome, idx):
        e = fetch_player(player_id, titolo, nascita_attesa=nascita_attesa,
                         club_noti=club_noti, club_anni=club_anni,
                         paese=paese, ruolo=ruolo, segui_indice=False, **kw)
        if e.stato == "ok" and e.identita == "confermata_data":
            e.dettaglio = f"recuperato_via={strato} titolo={titolo}"
            return e
    return Esito(player_id, nome, None, "nessuna_pagina",
                 dettaglio="404 anche dopo le varianti da gazetteer")


# ─────────────────────────────────────────────────────────────────────────────
# (5) parse_career — UNA sola modifica, sulla riga del vincolo sull'anno
# ─────────────────────────────────────────────────────────────────────────────

# Cella-anni senza anno: ammessa solo se vuota o «quasi-anno» ('200?–200?').
# Tiene fuori le righe-etichetta di ALTRI template ("High school", "College",
# "NBA draft", "Drafted by"). Misurato: **757 celle su 757** sono vuote.
_RE_ANNI_AMMESSI = re.compile(r"[\d?–—\-\s]*")

#  ⬇️  dentro parse_career, sostituire
#         if not re.search(r"\d{4}", anni) or not club:
#             continue
#      con
#         if not club:
#             continue
#         if not re.search(r"\d{4}", anni):
#             # Wikipedia lascia la colonna Years VUOTA quando gli anni non si
#             # sanno. Pretendere \d{4} buttava via in silenzio tappe con il
#             # club scritto per esteso — un **finto vuoto**, gemello del finto
#             # pieno di R6. Censimento su 1.999 pagine gia' riuscite:
#             #   18.541 -> 19.298 tappe = **+4,08%**, su **26,81%** delle pagine
#             #   (mediana +1, max +4), **99,74% giovanili**.
#             #   Club aggiunti reali: Real Sociedad 6, Roma 3, Valencia 3, Lazio 3.
#             # Estrapolato alle 20.981 pagine `ok`: **~7.900 tappe**, 0 richieste.
#             # Sui 711 falliti recupera 3 pagine — le uniche 3 di calcio — e
#             # sono TUTTE E TRE omonimi, tutte e tre respinte. Guadagno su
#             # QUEL fronte: **zero**. Il guadagno e' su chi gia' funzionava.
#             # ⚠️ R8: le 7.900 tappe hanno `anno_da=None` — dato mancante
#             # DICHIARATO, non finto pieno; chi ordina la carriera per anno
#             # deve gestirle esplicitamente. E il campo `ordine` si rinumera
#             # sul 26,8% delle pagine: effetto di schema, va dichiarato.
#             if not _RE_ANNI_AMMESSI.fullmatch(anni.strip()):
#                 continue


# ─────────────────────────────────────────────────────────────────────────────
# (6) fetch_player — lo stato dice la CAUSA, e l'indice si segue
# ─────────────────────────────────────────────────────────────────────────────

def fetch_player(player_id, nome, lang="en", *, nascita_attesa=None,
                 club_noti=None, club_anni=None, paese=None, ruolo=None,
                 segui_indice=True, **kw) -> Esito:
    titolo = nome.replace(" ", "_")
    url = f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(titolo)}"
    try:
        html = fetch_page(titolo, lang, **kw)
    except Exception as e:                                   # pragma: no cover
        return Esito(player_id, nome, url, "errore", dettaglio=repr(e))
    if html is None:
        return Esito(player_id, nome, url, "nessuna_pagina")

    tappe = parse_career(html, player_id, url)
    if not tappe:
        classe = classifica_pagina(html)
        if segui_indice and classe in STATI_INDICE:
            return risolvi_da_indice(
                html, player_id, nome, lang, nascita_attesa=nascita_attesa,
                paese=paese, ruolo=ruolo, club_noti=club_noti,
                club_anni=club_anni, **kw)
        return Esito(player_id, nome, url, classe)

    bday = bday_pagina(html)
    identita = verifica_identita_v2(bday, nascita_attesa, tappe, club_anni,
                                    corrob=corroborazione(html, paese, ruolo))
    for t in tappe:
        t.identita = identita
    if identita == "respinta":
        # NOVITA': la pagina e' di un ALTRO, ma la persona giusta puo' avere la
        # sua voce. Oggi i suffissi si provano SOLO sul 404, quindi non si
        # tenta mai. Due sorgenti, in quest'ordine:
        #   (a) l'HATNOTE della pagina sbagliata, che abbiamo gia' in mano:
        #       **21,0%** [16,0; 27,1] contiene il titolo esatto col nostro
        #       anno, **43/43 link BLU, zero rossi**. Trovarlo costa 0 richieste;
        #       sonda 8/8 pagina esistente, **7/8 = 87,5%** aggancio corretto;
        #   (b) il titolo COSTRUITO `Nome (footballer, born AAAA)`: pagina
        #       esistente **8/20 = 40%**, aggancio corretto **6/20 = 30%**
        #       [14,5; 51,9]. Il **60% da' 404**: per quei giocatori la voce
        #       non esiste, e questa e' la risposta, non un fallimento.
        # ⚠️ Il titolo con l'anno NON e' univoco: `Burak Yilmaz (footballer,
        # born 1995)` esiste ed e' una TERZA persona (7 febbraio contro il
        # nostro 27 novembre); idem Romario 1992 e Liam Henderson 1996. Il
        # titolo e' un CANDIDATO, mai una prova: la pagina nuova ripassa
        # sempre di qui. End-to-end: 16 trovate -> 13 attaccate -> **0
        # identita' sbagliate**, e le 3 scartate sono le 3 di un'altra persona.
        if segui_indice and nascita_attesa:
            anno = str(nascita_attesa)[:4]
            cand = candidati_calcistici(html, int(anno)) or \
                [f"{nome} (footballer, born {anno})"]
            if len(cand) == 1:
                e2 = fetch_player(player_id, cand[0], lang,
                                  nascita_attesa=nascita_attesa,
                                  club_noti=club_noti, club_anni=club_anni,
                                  paese=paese, ruolo=ruolo,
                                  segui_indice=False, **kw)
                if e2.stato == "ok" and e2.identita == "confermata_data":
                    e2.dettaglio = f"recuperato_da_respinta titolo={cand[0]}"
                    return e2
        return Esito(player_id, nome, url, "identita_non_confermata", tappe,
                     bday_pagina=bday, identita=identita)
    return Esito(player_id, nome, url, "ok", tappe,
                 bday_pagina=bday, identita=identita)
```

### La modifica a `scripts/fetch_wikipedia_careers.py`

```python
# ── 1. elenco_giocatori: servono TRE dati nuovi, tutti gia' presenti ─────────
#    club_anni  (nome_club, primo_anno, ultimo_anno) da appearances.csv, per
#               player_id -> immune all'omonimia. E' l'asse che mancava.
#    paese      country_of_citizenship  |  ruolo  position
#
    players = pd.read_csv(
        W.ROOT / "files" / "player_scores" / "players.csv.gz",
        usecols=["player_id", "name", "date_of_birth",
                 "country_of_citizenship", "position"],      # <-- +position
    )
    ...
    app["anno"] = pd.to_datetime(app["date"]).dt.year
    span = (app.assign(nome_club=app["player_club_id"].map(nomi_club))
               .dropna(subset=["nome_club"])
               .groupby(["player_id", "nome_club"])["anno"].agg(["min", "max"])
               .reset_index())
    club_anni = span.groupby("player_id").apply(
        lambda g: [(r.nome_club, int(r.min), int(r.max)) for r in g.itertuples()])
    players["club_anni"] = players["player_id"].map(club_anni)


# ── 2. STATI_DEFINITIVI: il vocabolario cambia, e va dichiarato ─────────────
# `indice_non_risolto` STA fra i definitivi. Motivo: fuori, le ~345 astensioni
# verrebbero riprocessate e RISCRITTE a ogni run, e i contatori di stato si
# sdoppierebbero — e' gia' successo con i 312 `errore` ritentati, che hanno
# costretto a deduplicare per player_id (2.038 -> 2.017). Un indice non risolto
# oggi puo' esserlo domani: si ritenta con `--ritenta-indici`, esplicitamente.
STATI_DEFINITIVI = frozenset({
    "ok", "identita_non_confermata", "nessuna_pagina",
    "nessun_infobox", "nessun_blocco",                  # storici, restano
    "disambigua", "pagina_di_nome", "soggetto_diverso",  # NUOVI: dicono la causa
    "senza_infobox", "senza_blocco",
    "indice_non_risolto", "indice_link_rotto",
})
if args.ritenta_indici:
    STATI_DEFINITIVI = STATI_DEFINITIVI - {"indice_non_risolto"}


# ── 3. il loop: gazetteer una volta sola, poi i suffissi solo sul 404 ───────
    GAZ = W.costruisci_gazetteer() if args.gazetteer else None   # 0 richieste, ~70 s

    for i, r in enumerate(da_fare.itertuples(), 1):
        esito = None
        for suff in SUFFISSI:
            e = W.fetch_player(
                r.player_id, f"{r.name}{suff}",
                nascita_attesa=r.date_of_birth,
                club_noti=r.club_noti if isinstance(r.club_noti, set) else None,
                club_anni=r.club_anni if isinstance(r.club_anni, list) else None,
                paese=r.country_of_citizenship, ruolo=r.position,
                use_cache=not args.no_cache,
            )
            esito = e
            # `indice_link_rotto` NON e' `nessuna_pagina`: fermarsi qui evita
            # che i suffissi rientrino nel ramo-indice (fino a 3 risoluzioni e
            # 6 richieste per un giocatore).
            if e.stato != "nessuna_pagina":
                break
        if esito.stato == "nessuna_pagina" and GAZ is not None:
            esito = W.recupera_404(
                r.player_id, r.name, GAZ, nascita_attesa=r.date_of_birth,
                club_noti=r.club_noti if isinstance(r.club_noti, set) else None,
                club_anni=r.club_anni if isinstance(r.club_anni, list) else None,
                paese=r.country_of_citizenship, ruolo=r.position,
                use_cache=not args.no_cache)
        ...
```

---

## 3. L'effetto sul bias brasiliano-iberico

**Risposta breve: il divario si RIDUCE di circa un quarto. Non si chiude, e non si chiuderà con Wikipedia inglese.**

### Il fronte-indice, misurato end-to-end (l'unico numero completo)

| paese | tentati | PRIMA | DOPO | recuperato |
|---|---:|---:|---:|---:|
| Brasile | 1.449 | **57,3%** | **27,1%** | 52,7% |
| Portogallo | 859 | 44,4% | **17,2%** | 61,3% |
| Scozia | 620 | 32,7% | 9,8% | 70,0% |
| Spagna | 1.570 | 30,3% | 9,7% | 68,1% |
| Inghilterra | 1.082 | 22,1% | 6,9% | 68,6% |
| **Ucraina** | 1.056 | **37,7%** | **36,0%** | **4,5%** |
| **Grecia** | 773 | **24,4%** | **23,0%** | **5,7%** |
| Italia | 905 | 7,0% | 4,3% | 38,1% |
| Francia | 1.303 | 7,3% | 4,9% | 32,6% |
| Olanda | 952 | 5,7% | 4,7% | 16,7% |

| | PRIMA | DOPO |
|---|---:|---:|
| **V di Cramér** (forza del legame paese↔fallimento) | **0,3372** | **0,2573** (**−23,7%**) |
| rapporto **Brasile / Olanda** | 7,5× | **4,2×** |
| chi-quadro | 2.365 | 1.250 (df 37, **p ≈ 0**) |

⚠️ La tabella «DOPO» assume che il **100%** delle scelte diventi un recupero: va scontata per il tasso di conferma ([88,6%, 100%]).

### Gli altri fronti, misurati **separatamente** su denominatori diversi

- **404 → gazetteer**: chi-quadro del tasso di 404 per cittadinanza **1.439 → 1.029** (Croazia 15,5%→4,8%, Serbia 10,4%→2,7%, Cechia 8,5%→0,6%, Danimarca 10,0%→6,1%, **Ucraina 29,5%→21,2%**). ⚠️ Con il fix R3 e il decadimento della resa il numero va **rimisurato**: non è mai stato calcolato sul codice corretto.
- **`nessun_blocco` → instradamento**: il fronte è al **41,8% brasiliano** (265/634 alla misura) e al **62,6% mononimi**, ma solo 137 sono instradabili → contributo di ordine ~50 brasiliani.

**L'effetto congiunto NON è misurato**: i tre fronti hanno denominatori diversi e popolazioni parzialmente sovrapposte. L'ordine di grandezza atteso è V di Cramér **0,337 → ~0,24-0,25**, ma è una proiezione, non una misura.

### Che cosa dice questo, in sostanza

**Il divario si dimezza dove il fallimento era mononimia pura** — Spagna, Portogallo, Scozia, Inghilterra crollano di due terzi. Il residuo brasiliano **cambia natura**: da «pagina di disambigua» diventa «voce che non esiste o è di un altro soggetto», ed è per questo che il Brasile si ferma al 27,1% invece di scendere ai livelli iberici.

**E c'è una cosa che va a verbale (R4) e che nessuno aveva separato**: l'**Ucraina** (37,7% → 36,0%) e la **Grecia** (24,4% → 23,0%) **non si muovono**. Il loro fallimento **non è mai stato mononimia**: è traslitterazione e assenza di voce. Stavano nel gruppo «alto tasso» per un meccanismo completamente diverso, e vengono aggrediti solo dal fronte gazetteer — dove l'Ucraina scende 29,5%→21,2% **sul solo sotto-fronte 404** e resta comunque il buco maggiore, perché **metà dei suoi 404 non ha candidato**: quelle pagine non sono linkate da nessuna delle nostre. Chiudere quel divario richiede la **Wikipedia ucraina**, cioè un'altra decisione — e l'audit citato nel modulo dice che le altre lingue avevano dato guadagno zero su 333, ma su *quel* campione, non su questo.

**Il chi-quadro resta enorme (p < 1e-180) e resterà tale.** La confondente si riduce di oltre un quarto; non sparisce. **Ogni analisi che usi lo strato 2 deve continuare a dichiararla.**

---

## 4. Cosa NON è recuperabile, e perché

| che cosa | quanti | perché |
|---|---:|---|
| pagine-indice: astensioni del selettore | **345** (275 sotto soglia, 59 ambiguo, 11 senza candidati) | L'astensione è la parte **onesta** del metodo: costa zero richieste e zero rischio. Le più promettenti sono le 59 ambigue, che si sbloccherebbero con un segnale in più (nazionale, o `first_name`/`last_name` confrontati col nome completo). **Costo: zero richieste.** Non fatto. |
| 404 senza candidato nel gazetteer | **≈1.480** su 2.085 | Quelle pagine **non sono linkate da nessuna delle nostre**. Il gazetteer legge ciò che la cache contiene: non può inventare. |
| 404 con titolo costruito alla cieca | **60%** dà 404 (n=20) | Babacar Gueye, Moustapha Sall, Rodrigo Macedo, Miguel Monteiro: **la voce non esiste**. Fine. Non è un difetto della strategia: è un'assenza. |
| `nessun_blocco` non instradabili | **574** su 711 (236 con candidati ma anno sbagliato, 316 senza candidati, 22 multi-candidato dello stesso anno) | I 22 multi-candidato: l'anno non basta e vanno risolti con la ricerca per nome+data, **la cui precisione non è stata misurata in questo lavoro**. |
| quarantene lasciate al giudizio umano | **~14** | Δ ESTRANEO o DEBOLE senza corroborazione. La regola non le indovina: le **dichiara**. Fra queste ci sono casi che sono la persona giusta con l'anagrafica sbagliata **sulla pagina** — Haris Belkebla, la voce dice 3/8/2000 ma è l'algerino di Brest/Angers nato 28/1/1994, **stessa altezza al centimetro**, stesso ruolo, stesso club: la data della pagina è un **finto pieno** (R6). |
| respinte senza pagina alternativa | **~110** | Il 60% dei titoli costruiti dà 404. |
| **giocatori con `date_of_birth` sbagliata da noi** | **non misurato** | Tutto il selettore si appoggia all'anno del nostro dataset. Se è sbagliato, il selettore sceglie **con sicurezza** la persona sbagliata e `verifica_identita` la respinge: il danno è **una richiesta sprecata, non un dato falso** — comportamento voluto. Ma quei giocatori **non saranno mai recuperati**, per costruzione. |
| **omonimi con lo stesso giorno di nascita esatto** | **non osservati** | Zero eventi in 50 (instradamento) + 30 (indice) prove. La potenza esclude solo tassi > **7,1%**. È il residuo vero, ed è irriducibile con la data come unico giudice. |
| **i 3.027 mai tentati** | 3.027 | Mediana **1 presenza**, **100%** sotto le 20. Renderanno meno di tutti (resa gazetteer ~16%) e stanno **interamente** nello strato dove il bound sui falsi positivi del fronte-indice **non esiste**. |

**Un claim che va ritirato, e uno che resta.** Non è vero che «un 404 sul nome nudo significa che quel nome su en.wikipedia non esiste in nessuna forma»: 19 controesempi su 2.085 (0,9%) sono già dentro la cache. Resta invece vero, ed è misurato, che provare `(footballer, born AAAA)` alla cieca sui 404 rende **0/6**: il titolo disambiguato nasce solo quando il nudo è occupato, e in quel caso il nudo restituisce una **disambigua**, non un 404.

**Totale non recuperabile: ~2.900 sui 5.835 falliti attuali** (~50%), di cui la maggioranza è **assenza vera della voce**. Va registrata come esito definitivo, non inseguita.

---

## 5. L'ordine di esecuzione consigliato

| # | passo | richieste | tempo | condizione |
|---|---|---:|---:|---|
| **0** | applicare le 5 rettifiche obbligatorie (§0-bis) e i test | 0 | — | **bloccante** |
| **1** | `parse_career` rilassato, ri-girato sulla cache | **0** | ~16 min CPU | — |
| **2** | `verifica_identita_v2` sulle 262 quarantene + 16 false respinte | **0** | ~2 min CPU | **con la guardia `n_club>0`** |
| **3** | rimuovere dal DB le 3 identità sbagliate | 0 | — | non basta non promuoverle: vanno **tolte** |
| **4** | instradamento `nessun_blocco` (elenco ricostruito **per player_id**) | **137** | **2,3 min** | — |
| **5** | validazione stratificata `<20 presenze` per il fronte-indice | **30** | **0,5 min** | **bloccante per il passo 6** |
| **6** | pagine-indice (`nessun_infobox` + 376 `nessun_blocco` + 24 `errore`) | **2.812** | **46,9 min** | dopo il passo 5 |
| **7** | pilota gazetteer, 100 richieste stratificate per chiave A/B/C/D | **100** | 1,7 min | **bloccante per il passo 8** |
| **8** | gazetteer, resto | **503** | 8,4 min | solo se il pilota conferma la resa |
| **9** | respinte → hatnote, poi titolo costruito | **189** | 3,2 min | — |
| | **TOTALE** | **3.771** | **62,9 min = 1,05 ore** | |

**Perché quest'ordine.** I passi 1-3 costano **zero richieste** e vanno prima di tutto: cambiano la baseline contro cui si misura tutto il resto (e il passo 3 **toglie** dati sbagliati, che vale quanto aggiungerne di giusti). Il passo 4 ha il miglior rapporto fra i fronti a pagamento (**0,92 recuperi per richiesta**) ed è quello con il bound sui falsi positivi più stretto (0/50, ≤7,1%). Il passo 5 costa **30 secondi** e chiude l'unico strato in cui il fronte più grosso non ha un limite: farlo dopo il passo 6 significherebbe scoprire il problema con 2.800 richieste già spese. I passi 7-8 sono spezzati perché il fronte gazetteer, dopo il fix, ha un **rischio limitato (≤28) e una resa ignota**: per il criterio del brief è **non valutabile**, e la risposta corretta non è «promettente», è **misurarlo su 100 richieste prima di impegnarne 600**.

### Il bilancio finale

```
recuperati            ≈ 2.400 - 3.100 giocatori   (punto ~2.900)
rietichettati            245 quarantene -> confermata_coerenza
rimossi                    3 identità sbagliate (18 tappe)
tappe aggiunte        ≈ 7.900 (parser) + ~1.360 (instradamento)
                        + ~19.000 (recuperi × ~8 tappe senior)

falsi positivi        0 osservati su ~180 verifiche end-to-end
                      ≤ 51 al 95% (somma dei limiti superiori) = ≤ 1,8%
                      ripartiti: indice ≤11,8 · gazetteer ≤28 · instrad. ≤9 · v2 ≤2

costo                 3.771 richieste = 1,05 ore a 1 al secondo
                      + ~20 minuti di CPU su cache
                      un solo processo, mai in parallelo
```

**Il criterio del brief è soddisfatto per tre fronti su quattro.** Instradamento (0/50, ≤7,1%), quarantene (0/72, ≤5,1%) e pagine-indice (0/30, ≤0,50% stratificato) sanno dire quanti errori introducono. Il **gazetteer no** — non sul rischio, che è limitato, ma sulla **resa**, che dopo il fix non è misurata da nessun campione valido. Va etichettato **non valutabile** e trattato con un pilota, non con un lancio.

E la frase che non va scritta nel README: *«il recupero non peggiora la qualità del database»*. La peggiora, di poco e in modo quantificato — **da ~1,2 a ~13 persone sbagliate residue su ~24.000 pagine, cioè dallo 0,006% allo 0,05%** — perché il ramo-indice seleziona sull'anno di nascita e consegna al filtro esattamente il caso in cui il filtro è più debole. Il prezzo è accettabile. Presentarlo come neutro non lo è.
---

## 8. Wikidata: la terza fonte (01/08/2026)

Il piano qui sopra è stato scritto quando l'unica prova d'identità disponibile
era la `bday` letta **dall'HTML** della pagina. Da lì venivano tutte le sue
difficoltà: il ramo `k == 0 → respinta` che confonde prova contraria e assenza
di prova (R4), le 263 quarantene che restano nel database senza conferma, le
205 respinte perse. Tutte forme dello stesso problema: **quando il markup non
dà la data, non abbiamo niente da confrontare.**

Wikidata lo chiude, e lo chiude a un costo che non ha rapporto col piano sopra.

### Perché è la fonte giusta (e non una fonte in più)

Tre proprietà, in ordine di importanza:

1. **Non c'è matching per nome.** Il Q-id è inciso **dentro la pagina che
   abbiamo già scaricato** (`wgWikibaseItemId`), presente in **24.074 pagine su
   24.077 = 100,0%**, estratto in 101 secondi con **zero richieste di rete**.
   Questo è il punto: ogni verifica d'identità basata sul nome può introdurre
   una *nuova* omonimia mentre ne risolve una vecchia. Qui quel passaggio non
   esiste — l'entità interrogata è per costruzione quella della pagina letta.
2. **`P569` è strutturata.** È un valore tipizzato con una **precisione
   dichiarata**, non testo da estrarre: non dipende dal template né dalla
   lingua. Dove l'HTML non dava la `bday`, Wikidata dà comunque la data.
3. **`P54` porta i qualificatori `P580`/`P582`** — la *finestra temporale*
   della carriera, che l'infobox dà in modo irregolare. È ciò che permette il
   ramo 2 del verdetto (il caso del padre omonimo) anche senza data di nascita.

Costo: **una richiesta per giocatore da dirimere**. 483, non 24.000.

### Robots.txt — verificato riga per riga

```
Disallow: /wiki/Special:EntityData/
Allow:    /wiki/Special:EntityData/*.
```

Vince il pattern **più lungo** (RFC 9309 §2.2.2): un URL con estensione
(`.json`) è **permesso**. È l'endpoint che Wikidata pubblica apposta per
l'accesso automatico.

⚠️ `urllib.robotparser` della standard library implementa *first-match-wins* e
su questa coppia risponde `False` — **sbagliato**. Il controllo in
`src/data/wikidata_identity.py` è scritto a mano per questo, e non riusa
`wikipedia_careers.PATH_VIETATI` (che vieta tutto `/wiki/Special:`: giusto per
i domini Wikipedia, sbagliato per questo).

⚖️ Wikidata è **CC0**, non CC BY-SA: ciò che deriva da qui non porta vincoli di
condivisione allo stesso modo.

### 📐 Il modello in dettaglio

**La regola di verdetto è gerarchica**, non un OR — un OR non è mai più forte
del suo ramo più debole (stesso argomento di `verifica_identita`):

```
1. nascita_wikidata != None  and  nascita_attesa != None
       Δ = |data(P569) − data(attesa)| in giorni
       Δ ≤ 3  → confermata
       Δ > 3  → smentita

2. altrimenti, se ultimo_anno(P54) != None and prima_presenza != None
       ultimo_anno < anno(prima_presenza)  → smentita  (incompatibilità temporale)

3. altrimenti → indeterminato
```

**Perché 3 giorni.** Stessa soglia di `verifica_identita`, e per la stessa
ragione: le fonti calcistiche discordano di un giorno con frequenza non
trascurabile (fuso della registrazione, data di dichiarazione vs data di
nascita). Non si introduce una seconda soglia per la stessa domanda, altrimenti
lo stesso giocatore può essere confermato da un modulo e smentito dall'altro.

**Perché il ramo 3 è `indeterminato` e non `confermata`.** Un'assenza di prova
non è una prova. È la regola che tiene in piedi tutta la verifica: marcare come
confermato ciò che non lo è ricrea *esattamente* il problema che questo modulo
esiste per chiudere. È anche la correzione strutturale della rettifica **R4**
(il ramo `k == 0 → respinta`), che sbagliava nella direzione opposta.

**Due casi di «finto pieno» (R6) chiusi nel codice:**

- `P569` con **precisione < 11** (solo anno, solo mese) è scritta
  `+1994-00-00T00:00:00Z`. Leggerla come «1° gennaio» produrrebbe uno scarto di
  mesi contro una data vera, cioè una **smentita fabbricata dal nostro codice**
  su un giocatore che potrebbe essere quello giusto. Si scarta.
- una militanza **aperta** (`P580` senza `P582`) non ha un ultimo anno. Se
  `ultimo_anno` restituisse l'anno d'inizio, il ramo 2 dichiarerebbe «carriera
  chiusa nel 2015» un giocatore ancora in attività.
- le date dei qualificatori si troncano alla **precisione dichiarata**:
  scrivere `2015-01-01` dove la fonte dice `2015` è inventare due campi su tre.

### Le due domande che il numero da solo non risponde

Misurate in `scripts/_run_verdetti_wikidata.py`, non assunte (R7):

**(a) Le smentite sono una popolazione sola?** No — la prova su 20 casi mostra
già due fenomeni incompatibili: `Q12897` a **18.603 giorni** (una pagina del
1940 per un giocatore nato nel 1991: un'altra persona, senza dubbio) e
`Q431562` a **61 giorni** (`1984-03-15` contro `1984-05-15` — stesso giorno,
mese scambiato: una discrepanza di fonte sulla **stessa** persona). Trattarle
allo stesso modo butterebbe via giocatori buoni per rimuoverne di sbagliati —
lo stesso bilancio negativo che la rettifica R4 aveva già trovato.

**(b) Wikidata è INDIPENDENTE dalla pagina?** Da verificare, non da dare per
scontato: la data attesa viene da Transfermarkt, ma la `bday` della pagina e la
`P569` vengono **entrambe dall'ecosistema Wikimedia**. Se concordano quasi
sempre, una smentita significa «Wikimedia discorda da Transfermarkt», **non**
«è un'altra persona» — e il valore di Wikidata non è l'indipendenza, è che la
data è *leggibile* dove l'HTML non la dava. Lo script misura la concordanza con
un **intervallo di Wilson** (a `p` vicino a 1 il normale darebbe estremi > 1).

### Cosa questo NON fa

Lo script **non modifica nessun dato**: scrive solo il proprio verdetto in
`data/carriere_wikipedia/verdetti_wikidata.csv.gz`. Applicarlo al database è un
passo separato, che passa dal registro delle correzioni (**R3**).

### Nota sul workflow

Il workflow multi-agente lanciato per lo stesso scopo è **fallito**: 7 agenti su
8 in errore (`StructuredOutput retry cap`), l'unico sopravvissuto ha riportato
tutti gli strumenti rotti nel proprio ambiente. **Zero misure nuove da quel
run.** Il lavoro di questa sezione è deterministico e non ne deriva nulla.
