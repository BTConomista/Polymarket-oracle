# Audit delle fonti del database giocatori/allenatori/arbitri (31/07/2026)

> **Cos'è questo file.** Il verbale integrale di un lavoro a 13 agenti eseguito il
> 31/07/2026 su richiesta dell'utente («per gli infortuni potremmo cercare su
> internet o da qualche altra parte per verificare le informazioni? [...] per tutti
> gli altri dati relativi ai database giocatori e allenatori che avevamo
> individuato le fonti sono a posto?»).
>
> Sta a `docs/PIANO_DATABASE_GIOCATORI.md` come `docs/audit_5_leghe/` sta al
> `DIARIO`: il piano riassume, questo file è la prova. **Dove i due divergono,
> vince questo**, che è posteriore e misurato.
>
> **Nessun dato è stato importato nel repo**, nessuna riga di `src/` è stata
> modificata: è un documento di *stato delle fonti*. I dataset esterni sono stati
> scaricati temporaneamente in `/root/.cache/kagglehub` e cancellati.
>
> Struttura: **A** infortuni · **B** carriere extra-Europa · **C** tabella di audit
> delle 118 voci · **D** cosa NON è a posto · **E** sorprese · **F** conteggi.
> Chi ha poco tempo legga **D** e **F**.
>
> ⚽ **AGGIORNAMENTO 04/08/2026 — il fronte ALLENATORI (F1-F32) è stato
> COSTRUITO** (Fase 140, `src/data/allenatori.py`). Non è più «stato delle
> fonti»: è dato importato e misurato. Cosa cambia rispetto a questo verbale:
> - **confermati**: F1 (copertura quasi totale — anzi **99,994%**, 2 club-partita
>   su 32.222: il «meno dello 0,3%» del piano era pessimista di 50×), F3
>   (`club_games.is_win` è lossy — e in più il file è un **duplicato esatto**:
>   0 celle divergenti su 1.957.076), F4/F27 (la chiave è già scissa nella
>   fonte: 2 gruppi nel perimetro, **485 partite = 3,01%**), F25/F26
>   (l'esperienza è visibile al dataset, non globale), F30 (`clubs.coach_name`
>   è la trappola R8: il modulo non la legge);
> - **NUOVO, e nessuna delle 118 voci lo prevedeva**: il nome sbaglia anche
>   nella direzione **opposta** — due allenatori diversi dietro una stringa
>   sola. Dimostrato con un test di impossibilità fisica: **11 nomi globali**,
>   2 nel perimetro (`michel` = Míchel Sánchez + Míchel González, il 2022-10-02
>   su due panchine lo stesso giorno);
> - **NUOVO**: `manager_name` è **chi sedeva in panchina quella partita**, non
>   chi era in carica. Il pattern A→X→A vale **836 mandati su 13.810**, e F9
>   (l'effetto rimbalzo) va misurato sui mandati **ricuciti**, altrimenti
>   parte da 4.416 eventi invece di 3.720.

---


*Documento di chiusura del lavoro a più agenti del 31/07/2026. Tutti i numeri sotto sono misurati, non stimati; dove una cosa non è stata misurata è scritto «mai misurata». Nessun file del repo è stato modificato, nessun dato importato: questo è un documento di **stato delle fonti**, non un'importazione.*

---

## A · INFORTUNI — verdetto unico dai tre angoli

### A.1 · Le fonti sono reali (e questo è dimostrato due volte, in modi indipendenti)

**Angolo 1 — controllo contro le presenze del repo** (`files/player_scores/appearances.csv.gz`, 1.894.350 righe). Se un giocatore è dichiarato infortunato dal giorno X al giorno Y, non deve avere presenze nelle partite che il suo club gioca in quella finestra. Con una **baseline placebo** (stessa finestra traslata di +180 e +365 giorni, riattribuzione del club e ricalcolo dell'esposizione inclusi):

| convenzione della finestra | A: zero presenze | A: placebo | B: zero presenze | B: placebo |
|---|---|---|---|---|
| `[from, until]` (letterale) | 0,8280 [0,8222; 0,8336] | 0,2360 | 0,8253 [0,8199; 0,8306] | 0,2337 |
| `[from+1, until]` | **0,9175** [0,9132; 0,9216] | 0,2399 | **0,9239** [0,9200; 0,9276] | 0,2371 |
| `[from+1, until-1]` | 0,9545 [0,9511; 0,9576] | 0,2437 | 0,9604 [0,9575; 0,9632] | 0,2395 |

Il placebo **non si muove** (~0,24 in tutte e tre le convenzioni): la convenzione non gonfia il segnale, toglie un artefatto che colpisce solo la finestra vera. Sul campione appaiato (composizione identica nelle tre condizioni) il McNemar dà chi² **3.845,9** (A, n=6.655) e **4.403,6** (B, n=7.635), con discordanze massicciamente asimmetriche: per A, 4.413 «zero solo nel vero» contro **200** «zero solo nel placebo». Misura continua: un infortunato gioca il **4,5%** delle partite del suo club (A: 0,0454; B: 0,0431); lo stesso giocatore nella stessa finestra spostata di sei mesi ne gioca il **58-59%**.

**Angolo 2 — controllo contro la stampa d'epoca** (29 casi verificati, giocatori notissimi, infortuni >60 giorni, 2017-2024): **29/29 eventi realmente avvenuti**, **29/29 tipo di lesione corretto**, 23 CONFERMATI / 6 PARZIALI / **0 SMENTITI** / 0 non verificabili. Il sospetto «due scrape dello stesso sito si confermano a vicenda» **non si materializza sul contenuto**.

### A.2 · Il difetto residuo non è l'invenzione, sono le DATE

Tre difetti sistematici, tutti misurati e tutti nello stesso verso (comprimono la finestra):

1. **`from` è la data della PARTITA in cui il giocatore si è fatto male**, non il giorno da cui è indisponibile. Prova: il **61,4%** (A) e **65,0%** (B) delle contraddizioni ha la prima presenza a offset **esattamente 0 giorni** da `from`, e la maggioranza ha *una sola* presenza in tutta la finestra, proprio lì. Conferma indipendente dalla stampa: offset medio **+0,68 giorni** (IC95 [+0,34, +1,01]), **18/20** offset non nulli positivi, test dei segni **p = 2,0e-04**.
2. **`until` è sistematicamente in anticipo sul rientro reale**: **−4,2 giorni** (IC95 [−7,7, −0,7], 9/10 negativi) concatenando la riga `Fitness` che Transfermarkt appende dopo l'infortunio; **−11,2 giorni** (IC95 [−18,1, −4,3], 10/10 negativi) usando la sola riga d'infortunio. Chi filtra via `Fitness` come «non infortunio» **sottostima l'assenza di settimane** (Reus da −29 a +3, Chiesa da −27 a −1, De Bruyne da −20 a −8).
3. **Il verso pericoloso esiste, raro**: 2 casi su 29 hanno l'inizio *prima* dell'evento — Laporte `from 29/08/2019` contro l'infortunio del **31/08/2019** (data confermata da `data/premier_league_matches.csv` e da mancity.com: «his first game in 143 days»); Chilwell `from 22/11/2021` contro Chelsea-Juventus del **23/11/2021**, partita che giocò per intero. È l'errore-specchio del look-ahead: **fabbrica un fatto falso nel passato**.

**Frazione-rumore implicita** (modello a due componenti, `q = (1 − zero_vero)/(1 − zero_placebo)`, limite *superiore* ai record con date sbagliate):

| convenzione | q(A) | q(B) |
|---|---|---|
| `[from, until]` | 0,2251 | 0,2280 |
| `[from+1, until]` | 0,1085 | 0,0998 |
| `[from+1, until-1]` | 0,0602 | 0,0521 |

**Il tasso d'errore vero è fra il 5% e l'11%**, non il 17% che si legge senza correggere la convenzione e non lo 0% che si crederebbe fidandosi della fonte. Le contraddizioni **profonde** (presenza ≥2 giorni dopo `from` *e* ≥2 giorni prima di `until`, cioè un giocatore che gioca in mezzo al suo infortunio) sono **2,50%** (A) e **2,22%** (B).

### A.3 · Il collo di bottiglia non è la specificità, è la SENSIBILITÀ

Costruendo dalle sole presenze le finestre in cui un titolare abituale sparisce (≥3 partite consecutive del club saltate, span ≥23 giorni, ≥60' in ≥3 delle 5 partite-club precedenti, stesso club prima e dopo) si ottengono **8.201 finestre** (mediana 47 giorni, 5 partite saltate; solo l'**1,79%** è preceduto da un rosso, quindi le squalifiche dirette non spiegano il fenomeno).

| | copertura vera | plac. +180 | plac. +365 | plac. −365 | copertura ≥50% della finestra |
|---|---|---|---|---|---|
| A | **0,4604** [0,4497; 0,4712] | 0,2139 | 0,2102 | 0,2589 | 0,3363 (plac. 0,061-0,071) |
| B | **0,5249** [0,5141; 0,5357] | 0,2513 | 0,2517 | 0,2586 | 0,3891 (plac. 0,072-0,084) |
| A ∪ B | **0,5769** | — | — | — | — |

**Le fonti dichiarano circa metà delle assenze prolungate osservabili.** Un modello che usasse «nessun infortunio dichiarato ⇒ giocatore disponibile» sbaglierebbe **circa una volta su due** sulle assenze lunghe — e in **Ligue 1 due volte su tre** (A 0,2892, B 0,3946; la meglio coperta è la Bundesliga, A 0,5720 / B 0,6159). La copertura cresce con la durata (23-35 gg: 0,41/0,46 → ≥121 gg: 0,57/0,66). **Nota onesta**: il 46-52% non è un tasso di errore — squalifiche per somma di ammonizioni, esclusioni tecniche, Coppa d'Africa, motivi personali e prestiti non rilevati producono assenze legittime non-infortunio. È un **limite inferiore alla copertura**.

### A.4 · A o B? La risposta ai numeri: **B come base, A come complemento sul 2017-2023. NON sostituire.**

L'utente ha proposto di prendere direttamente la B. Tre confronti, tre esiti diversi:

**(a) Sovrapposizione.** Chiavi `(player_id, from, until)` identiche: **72.898**. Solo A: **24.658**. Solo B: **68.418**. B è quasi un superset di A — quindi la domanda non è «quale è migliore» ma «cosa perdo buttando i 24.658 record esclusivi di A».

**(b) Pulizia — vince B, con IC disgiunti.** Sui record **esclusivi**:

| | n | zero presenze | IC95 |
|---|---|---|---|
| solo A | 2.343 | **0,8924** | [0,8793; 0,9044] |
| solo B | 4.412 | **0,9309** | [0,9230; 0,9380] |

I record che solo A possiede sono i **meno** coerenti dell'intero campione; quelli che solo B possiede sono i **più** coerenti. Aggiungi: duplicati esatti **A 9,6%** (9.386) contro **B 0,24%** (334).

**(c) Sensibilità a parità di stagioni — vince A, e non di poco.** Sul 2017-18..2022-23, dove entrambe sono vive:

| | copertura | IC95 |
|---|---|---|
| A | **0,5975** | [0,5848; 0,6100] |
| B | 0,5459 | [0,5331; 0,5586] |

McNemar appaiato: **420** finestre coperte solo da A contro **119** solo da B, **chi² = 167,0**. Nel 2017-18 A ha 2.434 infortuni valutabili nel perimetro contro i 1.770 di B, nonostante B abbia il doppio dei giocatori (34.561 contro 18.825).

**(d) Il vero discrimine è temporale.** A si ferma al **25/02/2024**, B al **12/09/2025**. Sul 2023-24..2025-26: A **0,1232**, B **0,4734**.

| stagione | A | B |
|---|---|---|
| 2017-18 | 2.434 | 1.770 |
| 2018-19 | 2.588 | 1.997 |
| 2019-20 | 2.297 | 1.979 |
| 2020-21 | 3.022 | 2.801 |
| 2021-22 | 2.636 | 2.626 |
| 2022-23 | 2.245 | 2.347 |
| 2023-24 | 1.295 | 2.392 |
| 2024-25 | **0** | 2.545 |
| 2025-26 | **0** | 129 |

> **Verdetto operativo.** Sostituire A con B **costa 426 finestre di assenza** che solo A copre e fa scendere la copertura totale da **57,69% a 52,49%** (−5,2 punti). Quindi: **B come base** (superset, 40 volte più pulita sui duplicati, arriva a settembre 2025), **A come complemento sul solo 2017-2023**, sapendo che i suoi record esclusivi sono i meno affidabili del lotto (0,8924 contro 0,9309). **Nessuna delle due copre la stagione 2025-26.**

### A.5 · Nessuna fonte alternativa a Transfermarkt esiste (sei angoli nuovi, sei esiti negativi)

| angolo | esito | numero che chiude |
|---|---|---|
| **Fantasy Premier League** (API ufficiale, l'unica origine genuinamente non-Transfermarkt, con `news_added` = il MOMENTO in cui il fatto diventa noto, R8) | **CHIUSA due volte** | ToS Premier League vietano *testualmente* «creating a database … that includes material obtained from the Website or App»; e l'archivio storico (vaastav) ha i campi infortunio solo in `players_raw.csv` = **892 record in 10 stagioni, Premier sola**, contro ~31.297 di Transfermarkt su 5 leghe |
| **`news` di FPL come campo infortuni** | **finto pieno (R6)** | 2023-24: 317 news non vuote, di cui **99 infortuni e 218 trasferimenti/prestiti** («Transferred to Monaco», «Contract terminated»). Chi conta le celle non vuote sbaglia di 3,2× |
| **UEFA Elite Club Injury Study** | **CHIUSO** | «**No data are available**» (verbatim); unità = incidenza per 1000 ore; club e giocatori **anonimizzati** (29 club, 913 giocatori) → nessun join possibile |
| **Wikidata / SPARQL** | **CHIUSO** | `query.wikidata.org/robots.txt`: `Disallow: /sparql`, `Disallow: /bigdata`. E comunque Wikidata **non ha una proprietà** per gli spell di infortunio |
| **GDELT** | permesso ma inservibile | API senza robots (permessa), rate limit 1 req/5s **rispettato con attese**; finestra storica funziona (gen 2019, 5 articoli) ma sono titoli multilingua senza entità risolte né date di rientro. Utile solo come fonte del *momento* in cui una notizia diventa pubblica: **mai quantificato** |
| **Fantasy di Bundesliga / Serie A / Liga / Ligue 1** | **CHIUSE o inesistenti** | `fantacalcio.it` vieta *esattamente* `/probabiliformazioniseriea`; `fantasy.laliga.com` API 404; Bundesliga nessun endpoint trovato (4 tentativi, **assenza di prova non prova di assenza**); **zero archivi storici** tipo vaastav per le altre 4 leghe |

**E una fonte avvelenata smascherata.** `sananmuzaffarov/european-football-injuries-2020-2025` — CC BY-SA 4.0, 15.603 righe, **esattamente le nostre 5 leghe**, nessun ID né URL Transfermarkt: il controllo anti-avvelenamento *superficiale* l'avrebbe promossa. Il confronto record-per-record con lo scrape già in casa: **87,6%** (9.824/11.219) con giocatore e data d'inizio identici; vocabolario cause **275/276 in comune**; data di fine identica al **97,38%**; e la firma decisiva: il campo `Days` differisce di **esattamente +1 nel 97,43% dei casi** (9.746/10.003) — l'off-by-one di chi ricalcola `(until − from)` inclusivo **dalle stesse due date**. Uno scrape indipendente produce discrepanze casuali, non un errore sistematico di un giorno su 97 record su 100.

> **Lezione di metodo da incidere:** l'anti-avvelenamento **non può fermarsi agli identificatori**. Il test forte è il confronto quantitativo con una fonte nota già in casa, e le **firme numeriche** (un off-by-one sistematico) sono più probanti dei metadati.

### A.6 · Regole d'importazione, se e quando gli infortuni entreranno nel repo

1. **Convenzione `[from+1, until]`**, mai letterale. Chi importa con `[from, until]` inietta un **look-ahead di un giorno** (R8): la partita del giorno `from` è già stata giocata quando l'infortunio diventa noto.
2. **Includere le righe `Fitness`** (1,94% del file) come coda del recupero; escludere invece «Corona virus» (3.082), «Rest» (786), «Ill», «flu», «Quarantine» — **10,7% delle righe non sono infortuni**.
3. **Deduplicare prima di qualunque statistica**: 9.275 righe duplicate identiche (8,6%), con 2.819 gruppi ripetuti 4 volte e uno 8 volte.
4. **Non usare `Days`, `games_missed` né la colonna durata come misure**: la durata coincide con `until − from` nel **100,00%** dei casi in *entrambe* le fonti (è una colonna ricalcolata, non una misura indipendente); `games_missed` supera le partite effettive del club nel **16,4%** (A) e **16,8%** (B) dei casi.
5. **Non sommare i giorni**: 890 coppie di intervalli consecutivi si sovrappongono (1,1%) — Pogba 2022-23 ha menisco, chirurgia e flessore attivi insieme.
6. **Trattare come censurato** il `until` al 30/06 o 31/05: il **7,6%** degli infortuni >60 giorni finisce lì (contro il 2,3% sul totale), 1.105 righe al 30/06. Van Dijk, Gavi e Zaniolo hanno tutti `until` a fine stagione con rientro reale mesi dopo: **non è un rientro, è la chiusura della riga**.
7. **La feature giusta è «era indisponibile alla data D?»**, con margine ±2 giorni sugli estremi, **mai** «giorni di infortunio», e **mai applicata alla partita che ha causato l'infortunio**.
8. **Il TIPO di infortunio è un finto pieno (R6)**: `Injury` non è mai nullo, ma vale letteralmente `unknown injury` su **4.058 righe del perimetro = 8,1%** (A) — ed è il valore *più frequente* (il secondo, `Hamstring injury`, è 2.900). Globalmente: **15,51%** (A, 346 etichette) e **18,91%** (B, 349 etichette).
9. **Secondo segnaposto non dichiarato**: `Games missed` ha **due** segnaposti, `-` (3.339 celle nel perimetro) **e `?`** (114 nel perimetro, 425 globali). Un parser che gestisce solo `-` produce NaN silenziosi.
10. **Licenza (R2, invariata dal lavoro sulla qualità)**: A è CC BY 4.0 e B è CC0, ma **entrambi sono scrape di Transfermarkt e nessuno dei due dichiaranti è titolare del dato**. Né la CC0 né la CC BY sono opponibili. **La qualità alta non sana la licenza**: sono due questioni da decidere separatamente.

### A.7 · Il limite più importante di tutto l'angolo 1, dichiarato

**L'indipendenza è di MODULO, non di FONTE.** `appearances.csv.gz` è a sua volta uno scrape di Transfermarkt. Il test falsifica il *database infortuni* (le presenze non ne derivano) ma **non l'ecosistema Transfermarkt**: un errore a monte sulla scheda del giocatore si propagherebbe in modo correlato a entrambi i lati. Una verifica davvero esterna richiederebbe presenze da un provider terzo — che non esiste per il nostro perimetro. Prova indiretta che l'allineamento dei `player_id` regge: se gli id fossero disallineati il test vero somiglierebbe al placebo, e invece dista **58 punti percentuali**.

---

## B · CARRIERE EXTRA-EUROPA — verdetto netto

> ### **RISOLTO al 99,7% sulla COPERTURA e sull'ELENCO DEI CLUB. NON RISOLTO sul CONTEGGIO DELLE PRESENZE: separabile pre/post debutto solo per 246/333 = 73,9%.**
> **E l'idea che motivava il fronte — le Wikipedia in altra lingua — è SMENTITA: 0 giocatori su 333 = 0,0%.**

### B.1 · Cosa è successo davvero

Il fronte era rimasto aperto per **due ricerche consecutive** per un **errore di oggetto, non di fonte**:

| oggetto misurato | copertura sui 333 |
|---|---|
| DBpedia (numero ereditato dal piano) | 250 = 75,1% — **0 date di fine** su 2.965 stazioni |
| en.wikipedia, tabella «Career statistics» (il «62,5%» del piano) | 207-228 = **62,2% → 68,5%** |
| en.wikipedia, **blocco carriera dell'INFOBOX** | **332 = 99,7%** |
| **guadagno dalle Wikipedia in altra lingua** | **0 = 0,0%** |
| Wikidata, ≥1 claim P54 | 311 = 93,4% (condizionata all'articolo inglese) |

La tabella «Career statistics» è la forma **più ricca e più rara**; il blocco `Senior career` dell'infobox è la forma **più povera e quasi universale** — e contiene già i tre campi che servivano: anni **con fine**, club, presenze. Le date di fine **non mancano su Wikipedia: le perde il parser di DBpedia** (`dbo:years` è un `xsd:gYear` di solo inizio).

Il rilevatore è **tarato**: sulla definizione del piano restituisce **62,2%** contro il **62,5%** dichiarato da un'altra sessione su un campione diverso — due misure indipendenti che concordano a 0,3 punti su un oggetto che nessuno dei due aveva definito formalmente.

### B.2 · Cosa è stato recuperato

- **2.854 tappe di carriera pre-debutto** su 332 giocatori (mediana 8 a testa)
- **2.260/2.854 = 79,2%** con **anno di fine** (DBpedia: 0 su 2.965)
- **2.394/2.854 = 83,9%** con **numero di presenze**
- **96.164 presenze pre-debutto** recuperate (mediana 284 a giocatore)
- Wikidata come verifica incrociata: **1.846 claim P54**, di cui **73,1%** con data di fine (P582) e **67,0%** con presenze (P1350) — CC0, ma **5,7 tappe per giocatore contro le 10,8 dell'infobox**: verifica, non sostituto

### B.3 · Perché l'idea nuova non paga (misurato, non argomentato)

- I 9 giocatori recuperati oltre la prima passata vengono **tutti da `en.wikipedia`** con varianti del nome (ASCII, ordine invertito, diacritici). Zero dalla lingua di casa.
- La pagina nella lingua di casa esiste per **252/268 = 94,0%** dei giocatori con lingua ≠ inglese: **il test è potente**. Esito: **23 casi** in cui l'inglese ha il blocco carriera e la lingua di casa no; **0 casi** viceversa.
- **`es.wikipedia` è strutturalmente peggiore**: la «Ficha de deportista» non contiene tappe (solo debutto e ritiro), la carriera sta in una wikitable separata **senza presenze**. Per i 93 giocatori ispanofoni — il gruppo più numeroso — la lingua di casa è un *downgrade*.
- Gli **868 «club in più»** attribuiti alla lingua di casa da un rilevatore generico sono **rumore**: contro **852** attribuiti all'inglese. La quasi-simmetria è la firma della misura, non dell'informazione; l'ispezione dei 10 casi peggiori dà `amsterdam`, `buenosaires`, `copalibertadores`, `ekstraklasa`, `fnbstadium` — città, stadi, competizioni. **Regola R7 applicata e pagata.**

### B.4 · Controllo antifrode (R2 + R6) e limite residuo

Coorte di **controllo**: 484 giocatori stesso criterio ma **con** passato nel dato primario; campione di 150 (seed 20260731).
- **Elenco dei club**: 176 club pre-debutto noti al primario, **15 non ritrovati (8,5%)** — e all'ispezione sono **tutti e 15 sigle** (AEK, PAOK, AZ, AIK, Union SG). **Zero omissioni vere accertate.** *(Con matching ingenuo davano 25,0%: la differenza è tutta normalizzazione dei nomi.)*
- **Presenze**: 47,1% identiche su 342 coppie, correlazione 0,62 — ma i disaccordi grandi sono Arminia Bielefeld 195 vs 54, Paderborn 161 vs 29, Fulham 151 vs 34, **tutte stagioni di seconda divisione**, cioè esattamente ciò che al primario manca. **Il disaccordo è il buco, non l'errore** — e per la stessa ragione il numero delle presenze **non è validabile** con i mezzi che abbiamo.

**Il limite che resta**: **27,9%** delle tappe pre-debutto è a cavallo del debutto o senza anno di fine (tocca l'89,8% dei giocatori). Sommando la tabella per stagione dove c'è, il conteggio è **davvero separabile per 246/333 = 73,9%**. Chi volesse una feature «presenze prima del debutto» deve accettare o **26,1% di NaN** o una stima. **R8**: la pagina scaricata oggi contiene tutta la carriera, post-debutto compreso; senza il taglio esplicito sull'anno di fine è look-ahead diretto.

### B.5 · Una premessa del piano da correggere (R4)

**Il fronte si chiama «carriere fuori Europa», ma la coorte è europea per due terzi**: 223/333 = **67,0%** (Spagna 74, Francia 37, Italia 26, Inghilterra 24, Germania 17) contro 110 = **33,0%** extra-europei. Il buco vero sono le **seconde e terze divisioni europee**. Coerente col «79% degli spell mancanti» già scritto nel piano, ma **in contraddizione col nome del fronte e con l'idea che lo motivava**.

### B.6 · Conformità (R5.3) — tutto verificato prima di scaricare

- **41 domini linguistici Wikipedia** verificati uno per uno: **nessuno vieta `/wiki/<Nome>`**. Usati solo quelli; mai `/w/`, mai `/api/`, mai `Special:`. Ritmo ≤4,5 req/s con cache su disco.
- **Anomalia dichiarata (R4)**: `ar.wikipedia` vieta un **singolo articolo**, `/wiki/سليم_دبور`, che è un calciatore. Non ci riguarda, ma chi userà questa via deve controllare l'URL singolo, non solo il pattern.
- **Trappola da registrare**: `Special:EntityData/*.json` è **permesso** per longest-match RFC 9309, ma `urllib.robotparser` di Python applica *first-match-wins* e restituisce `False`. **Chi verifica con quello si auto-chiude una fonte lecita.**
- Fonti alternative del piano ri-verificate: `footballdatabase.eu`, `playmakerstats.com`, `zerozero.pt`, `fbref.com` → **403 Cloudflare, CHIUSE** (le prime due erano 🟡 nel piano: **vanno declassate a ❌**). `national-football-teams.com` → aperta ma `Crawl-delay: 60` (5,5 ore per 333 giocatori) e solo nazionali.

### B.7 · Cosa NON è stato misurato

**Il valore predittivo.** Se questi 96.164 numeri di presenza, entrati come feature «esperienza», migliorino il log-loss di un mercato: **mai misurato**. Il fronte era di *recupero dato* e su quello risponde. Visto il tetto informativo misurato per 100 fasi, **non darei per scontato che ci sia**.

---

## C · TABELLA DI AUDIT COMPLETA (118 voci, stato CORRETTO dopo le refutazioni)

Legenda stati: **VERIFICATO** = misurato sul perimetro reale · **DERIVATO** = calcolabile da dati verificati, ma è un calcolo con assunzioni · **ASSUNTO** = dato dato per buono e mai misurato, o misurato male · **MANCANTE** = non esiste fonte utilizzabile · **CHIUSO_LICENZA** = esiste, raggiungibile, vietato dai termini.
Le celle marcate **⚠️ [rett.]** sono quelle dove la verifica avversariale ha corretto il numero o lo stato dell'audit; hanno precedenza.

### Fetta 1 — dati di base giocatore (righe 1-20 della checklist §1.9)

| # | dato | stato | fonte | copertura | rischio |
|---|---|---|---|---|---|
| 1 | minuti giocati (titolare/subentrato, min in/out) | VERIFICATO | `appearances` + `game_lineups` + `game_events` | ⚠️ **[rett.] 99,683% dei titolari, non 100%**: 1.119 titolari su 353.235 senza riga in appearances; buco lega×stagione (ES1 2020 **4,60%**, FR1 2021 1,51%, IT1 2021 1,22%), 764 partite | R6 costruito a valle: `lineups LEFT JOIN appearances + fillna(0)` registra 1.119 titolari con 0 minuti. Minuto in/out **troncato**: 0 cambi oltre il 90', 6.056 al 90' contro 2.195 all'89' |
| 2 | gol | VERIFICATO | `appearances.goals` + `game_events` (44.929) | accordo per-partita 16.008/16.111 = 99,361% | ⚠️ **[rett.]** «sempre in difetto» è **falso**: 102 in difetto e **1 in eccesso** (Granada-Celta 01/05/2022). Su almeno un autogol appearances **promuove a gol il tiratore avversario**. R1: mai da `games.csv` (verdetto del tribunale, 2 casi) |
| 3 | assist | VERIFICATO | `appearances.assists` (33.726) vs eventi | accordo per-partita 91,1% (14.677/16.110) | ⚠️ **[rett.]** la discrepanza dichiarata (1.169) è **gonfiata del 48,0%**: 561 dei 34.895 `player_assist_id` sono su eventi **Own-goal**. Divario reale **608**. La regola di riconciliazione è nota, non «da decidere» |
| 4 | tocchi | MANCANTE | nessuna (Wyscout 1.826 partite, StatsBomb 230, DFL 2) | **12,55%** al massimo | Fonte avvelenata: StatFootDB (8.970) e mirror Understat (12.651) «dichiarano licenze che non possono concedere» |
| 5 | passaggi (tentati/riusciti) | MANCANTE | come 4 | 12,55% | come 4. Unico proxy: `key_passes` per giocatore-STAGIONE, 2 leghe |
| 6 | dribbling | MANCANTE | come 4 | 12,55% | come 4. Nessun proxy nemmeno aggregato |
| 7 | contrasti | MANCANTE | come 4 | 12,55% | come 4 |
| 8 | stanchezza da minuti (club + nazionale) | DERIVATO | `appearances` | **Coupe de France: 0 partite nel dataset.** DFB 86,6%, CDR 89,9%, CIT 92,2%, FAC 94,3%. Conference League **0 righe su 728**. Nazionale **0,16%** | Fatica sottostimata **in misura diversa per lega**: un giocatore di Ligue 1 non accumula MAI carico da coppa nazionale |
| 9 | vantaggio/svantaggio dai tocchi | MANCANTE | dipende da riga 4 | **0% utilizzabile** | Derivato che poggia interamente su un MANCANTE |
| 10 | gol subiti per portiere | DERIVATO | `game_lineups` + `game_events` | **32.113/32.113 team-partita (100,000%) con esattamente 1 portiere titolare**; lineups su 16.057/16.111 | Cambio portiere in corsa richiede lo stato di campo minuto-per-minuto, che eredita il troncamento (8,9% dei gol senza minuto esatto) |
| 11 | età esatta a partita | VERIFICATO | `players.date_of_birth` | 99,96% (3 null su 7.709), range 1977-2010, nessun segnaposto | R4: 0,53% nasce il 1° gennaio contro un atteso di ~0,27% (~20 date amministrative). Innocuo per l'età in anni |
| 12 | esperienza (presenze/minuti cumulati) | DERIVATO | `appearances` cumulata | 22 competizioni su 70 con **zero** presenze (MLS, Brasile, Argentina, Saudi, J1, K League, Liga MX…). **Nessuna seconda divisione** | Bias di selezione: «esperienza = 0» significa due cose diverse (debuttante vero / carriera invisibile). Serve un flag esplicito |
| 13 | elenco convocati per finestra nazionale | MANCANTE | nessuna | **0%** — 5 tornei finali (742 partite), 0 qualificazioni, 0 amichevoli, 0 Nations League | Blocca il ramo nazionale della riga 8, la riga 40 e metà della riga 14 |
| 14 | confronto del carico fra giocatori | DERIVATO | query sopra 1 e 8 | ⚠️ **[rett.] NON «100% sui minuti di campionato»**: tetto **99,68%**, e il buco è concentrato nelle stagioni COVID, cioè proprio dove il carico è l'oggetto d'interesse | Confrontare il carico di un Ligue 1 con un Bundesliga oggi misura **in parte la copertura della fonte**, non la fatica |
| 15 | capitano per partita | VERIFICATO | `game_lineups.team_captain` | **97,05%** (31.165/32.114); bias forte: ES1 **92,79%**, GB1 95,99%, FR1 98,38%, IT1 99,11%, L1 99,51%; per stagione 92,03% (2020) → 99,94% (2024-25) | 🔴 **Finto pieno da manuale (R6)**: 0 null, quindi ogni controllo dice «colonna piena», ma lo `0` significa insieme «non è il capitano» e «non sappiamo chi era» |
| 16 | cambio di ruolo recente | DERIVATO | `game_lineups.position` nel tempo | 0 null su 654.316, 13 ruoli; 4.167 titolari su 6.597 (**63,2%**) con ≥2 ruoli distinti | R4: 10 righe con etichetta fuori vocabolario. R8: `pre` solo se calcolato sulle partite precedenti |
| 17 | falli per singolo giocatore | MANCANTE | nessuna a livello giocatore | **0%**; a livello squadra football-data HF/AF | Trappola: la description dei cartellini sembra dare i falli e non li dà — misurerebbe la propensione a **essere ammonito**, non a fare fallo |
| 18 | xG e xA individuali | DERIVATO | `files/understat_*_bundle.json` — **già nel repo** | **10.008 righe (Premier 4.819 + Liga 5.189)**, grana STAGIONE; **0 righe** per Serie A, Bundesliga, Ligue 1 | 🔴 **Look-ahead severissimo (R8)**: è un aggregato di FINE stagione. Il piano diceva «solo i minuti»: **sbagliato**, ci sono xG/xA/npxG/xGChain/xGBuildup/key_passes/shots — è il parser del repo a scartarli |
| 19 | recuperi palla e intercetti | MANCANTE | come 4-7 | 12,55% | come 4 |
| 20 | chi calcia corner e punizioni | DERIVATO | `game_events.description` | 2.344 gol da corner, 1.435 da punizione, 4.159 rigori — su 44.929 gol | 🔴 **Survivorship bias totale, mai dichiarato nel piano**: si osserva solo il piazzato che ha prodotto un gol. Il denominatore (piazzati battuti) sta nel Tier B al 12,55%. I rigori sbagliati non esistono nel dato |

### Fetta 2 — righe 21-40

| # | dato | stato | fonte | copertura | rischio |
|---|---|---|---|---|---|
| 21 | grandi occasioni create/sprecate | MANCANTE | nessuna | 0% in casa; 12,55% via Tier B | «Grandi occasioni» è un'etichetta Opta: **nemmeno le fonti aperte la pubblicano**. Voce da riformulare, non da procurare |
| 22 | storia infortuni per giocatore | VERIFICATO | Kaggle (A + B) — vedi §A | **70,3%** dei giocatori del perimetro (5.418/7.709); per lega da 49,5% a 20,9%; sensibilità **46-52%** | ⚠️ **[rett.]** secondo segnaposto `?` (114 perimetro / 425 globali) non dichiarato; due perimetri mescolati (3.339 vs 878); **il TIPO è un finto pieno**: `unknown injury` su 4.058 righe = **8,1%**, valore più frequente. R8: solo `from` è pre-partita |
| 23 | altezza (e peso) | VERIFICATO | `players.height_in_cm` — già in repo | altezza **98,66%** (min 162, max 206, nessun segnaposto); **peso 0%** (colonna inesistente in tutti e 12 i file) | Nessuno rilevante. R8 minore: l'altezza dei giovani cambia, il file dà il valore attuale |
| 24 | rendimento per livello avversario | DERIVATO | `appearances` + Elo in casa | ⚠️ **[rett.]** la voce dichiara «100%» tre righe dopo aver scritto 16.110/16.111 = 99,99%; Elo: corr 0,9329 con la chiusura, log-loss OOS 0,9857 vs 1,0730 | Segmentando per fascia di avversario le celle si svuotano e i minuti di chi gioca poco arrivano quasi tutti a partita decisa |
| 25 | squadre passate in carriera | DERIVATO | `appearances` + Elo; toppa DBpedia/Wikipedia | `appearances` **parte dal 2012-07-03** (censura a sinistra mai dichiarata nel piano); 21 competizioni su 65 a zero; **0 seconde divisioni**; 31,0% dei giocatori con prima presenza dopo i 23 anni | Il derivato poggia su un buco **misurato**: chi viene dal Sudamerica o dalla B risulta «senza passato». Vedi §B: recuperabile al 99,7% via infobox |
| 26 | esperienza pesata per competizione | DERIVATO | `competitions.sub_type` + `games.round` | ossatura del peso **100%** (65 competizioni, 16 categorie, `round` 0 nulli su 88.958) | Peso fra competizioni **dichiaratamente soggettivo**; Conference League 0 presenze; EURO/Copa/AFC 0 presenze |
| 27 | squalifiche REALI | DERIVATO | `game_events` + `game_lineups` | progressivo stagionale nel **93,4%** dei cartellini, sequenza 1..k esatta nel **99,99%** di 17.926 player-season. Dopo il 5° giallo (Serie A): assente in **1.156/1.193 = 96,9%** contro un fondo del 4,6-5,5% | L'assenza **non è** la squalifica: proxy contaminato da infortuni e scelte tecniche (~4% presenti nonostante la soglia). Da dichiarare come stima |
| 28 | H2H a livello di singolo giocatore | DERIVATO | `appearances` + `games` | 386.239 coppie (Serie A), **mediana 1 incontro**, media 2,00; ≥5 incontri solo **7,3%** | Il dato c'è e la statistica no: con n mediano 1 è **rumore puro**. Usabile solo aggregando |
| 29 | caratteristiche di gioco individuali | MANCANTE | dipende dal Tier B | 0% oggi; 12,55% tetto teorico | L'unica voce dove il piano ammette «nessuna fonte nota nemmeno per i conteggi grezzi». Tenere MANCANTE |
| 30 | minuti in inferiorità/superiorità | DERIVATO | `game_events` Cards + stato di campo | **3.122 espulsioni** (1.784 rossi + 1.338 secondi gialli) su 2.715/16.111 partite (16,9%), tutte con minuto | `appearances.red_cards` somma 1.495: **perde il 52,1% delle espulsioni**. Troncamento: 643 espulsioni (20,6%) al minuto 90 |
| 31 | ruolo giocato ≠ ruolo naturale | VERIFICATO | `game_lineups.position` vs `players.sub_position` | **27,56%** dei titolari fuori ruolo (n=353.196); ma a **macro-ruolo scende al 10,50%** | Il confronto è contro il ruolo naturale **ATTUALE** (istantanea, non serie storica): un terzino riconvertito risulta «in emergenza» per 9 stagioni. **La cifra difendibile è il 10,5%** |
| 32 | già ammonito, e da che minuto | VERIFICATO | `game_events` (minute + description) | 64.560 gialli, solo **27 con minute=−1 (0,04%)**, description mai nulla | Troncamento a 45/90: un giallo «al 45» può essere al 45+3. R8: `post` per la partita in corso |
| 33 | contratto (scadenza) e giorni dall'arrivo | **ASSUNTO** | `players.contract_expiration_date` | **76,66%** (5.910/7.709) come valore attuale; **0% come valore storico datato**. Dei 674 giocatori usciti entro il 2020, il **100%** ha scadenza ≥ 2023-01-01 | 🔴 R6 + R8: colonna piena, plausibile e **sbagliata di anni** per ogni partita non recente. Il piano la dava ✅. `transfers.csv` copre **14,4%** dei giocatori |
| 34 | prestito (e prestito dalla squadra che affronti) | MANCANTE | `transfers.csv` — non servibile | 14,4% dei giocatori, **0% del flag prestito** (0 occorrenze di «loan» in qualunque campo) | Irrecuperabile anche a valle: un ritorno di prestito è indistinguibile da un definitivo a fee 0. R4: `transfer_date` arriva al **2030-06-30** |
| 35 | numero di maglia | VERIFICATO | `game_lineups.number` | **99,996%** (26 righe con `-` su 654.316), 0 null, 0 zeri | Nessuno sostanziale |
| 36 | rientro da infortunio, curva di reinserimento | DERIVATO | riga 22 + `minutes_played` | limitata dal fronte infortuni: ~70% dei giocatori, **meno della metà degli episodi** | Chi manca dal dataset infortuni entra nel gruppo di controllo come «mai infortunato»: **la curva si misurerebbe contro un controllo avvelenato** |
| 37 | sensibilità individuale al riposo | DERIVATO | `appearances` + calendario club | 927.579 coppie di presenze consecutive; mediana 7 giorni, 14,5% ≤3 giorni | Trappola non segnalata dal piano: `appearances` contiene solo chi è **entrato in campo** (301.081 panchinari non impiegati stanno solo in lineups). Va costruito sul calendario del **club** |
| 38 | partite in N giorni | DERIVATO | come 37 | 100% delle presenze | Come 37, più il buco delle competizioni assenti: il carico è sottostimato **proprio per le squadre che giocano di più in Europa** |
| 39 | usura di carriera / età calcistica | DERIVATO | `appearances` + `date_of_birth` | dal **2012-07-03** in poi, e solo su 48 competizioni su 65; 31,0% con prima presenza dopo i 23 anni, 17,0% al bordo del file | Errore **orientato**, non casuale: l'età calcistica è più bassa per chi arriva da Sudamerica/seconde serie, cioè per chi la voce servirebbe |
| 40 | fuso orario del viaggio in nazionale | MANCANTE | nessuna | **0%** — EURO, Copa America, AFC hanno **zero** righe in appearances | Non manca il fuso (banale), **manca l'EVENTO viaggio**. Il rischio è illudersi che sia «quasi fatta» |

### Fetta 3 — righe 41-61

| # | dato | stato | fonte | copertura | rischio |
|---|---|---|---|---|---|
| 41 | piede vs lato di impiego (ala invertita) | VERIFICATO | `players.foot` + `game_lineups.position` | ⚠️ **[rett.] 64,04% (23.238/36.288), non 60,9%**: 1.868 ali con `foot='both'` (4,9%) stavano nel denominatore ma non possono mai stare nel numeratore. Ruoli lateralizzati: **29,52%**, non 28,6% | `foot` ha **TRE** valori: i 10.002 titolari ambidestri (2,8%) sono forzati a «non invertita» senza che nessuno l'abbia deciso. Lato definito solo per il **31,1%** dei titolari |
| 42 | probabilità di partire titolare | DERIVATO | `game_lineups.type` | ⚠️ **[rett.]** le partite senza distinta sono **54, non 48**: oltre alle 48 di ES1 2018 ce ne sono 6 mai censite, fra cui **IT1 2025 e FR1 2025** | Il denominatore giusto non esiste: `substitutes` è la panchina, **non l'elenco dei disponibili**. R4: 2 club-partita con 9 e 5 titolari |
| 43 | gerarchie dei rigori e delle punizioni | ASSUNTO | `game_events.description` | 4.159 rigori segnati, 932 rigoristi, **4,84 rigori per club-stagione** e 2,23 rigoristi distinti; punizioni **1,61 gol/club-stagione** | Campione **censurato** (i rigori sbagliati sono invisibili, ~24%) e numerosità insufficiente: la «2ª scelta» è rumore, la «3ª» non esiste. La gerarchia delle punizioni **non è ricostruibile** |
| 44 | rendimento casa/trasferta individuale | DERIVATO | `appearances` × `games` | aggancio **perfetto**: 238.341 in casa + 238.041 in trasferta, **0 orfane su 476.382**. Segnale reale: 0,136 vs 0,111 gol/90 | Per il **58,7%** dei giocatori la stima poggia su <50 partite: va shrinkata o non stimata |
| 45 | «mai sostituito» (partite intere consecutive) | DERIVATO | `appearances.minutes_played` | max 90, zero valori sopra; 234.054 presenze da 90' esatti; **66,3%** dei titolari completa | `minutes_played` è **troncato a 90**: il recupero è invisibile. Un espulso al 70' non è «sostituito» ma nemmeno «intero» — la regola va scritta |
| 46 | primo anno in un campionato nuovo | DERIVATO | `appearances` (non `transfers`) | 🔴 ⚠️ **[rett.] 34,8%, non 55,9%.** Due errori: (a) perimetro esteso al 2012 (9.883 ingressi invece di 9.365); (b) «passato» contava **qualsiasi** competizione, incluse Coppa Italia/CL dello stesso club nella stessa settimana. Filtrando ai soli `domestic_league`: **3.438/9.883 = 34,8%** | Il confondente (esordiente dal vivaio vs arrivato da campionato non coperto) non riguarda il 44,1% dei casi ma il **65,2%** |
| 47 | gol decisivi vs ininfluenti | DERIVATO | `game_events` (ricostruzione del punteggio) | ⚠️ **[rett.]** le divergenze sono **3, non 2**, e la terza **non è un caso a tavolino**: Toulouse-Brest 11/01/2020 finì 2-5 (confermato da `data/ligue_1_matches.csv`) ma gli eventi hanno **1 solo gol del Toulouse**. 44.933 gol in games.csv contro 44.929 eventi | 🔴 Un gol mancante **non sbaglia un record: riclassifica lo stato di TUTTI i gol successivi** di quella partita, e nessun controllo di completezza lo vede (R6). La ricostruzione va usata come **controllo permanente**, non una tantum |
| 48 | disciplina fine (falli/cartellini, partite tese) | MANCANTE | falli individuali: nessuna | falli individuali **0%**; cartellini individuali ~100% | Il **cuore** della voce (falli commessi / cartellini ricevuti) non è calcolabile: **manca il numeratore** |
| 49 | giocatore × allenatore (minuti) | VERIFICATO | `games` manager + `appearances` | 99,99% (2 club-partita su 32.222 senza allenatore), 496 allenatori, 824 coppie club-allenatore (mediana 26 partite) | ⚠️ **[rett.]** i nomi ambigui sono **2, non 1**, e quello omesso è il più grande: **Bruno Génésio/Genesio pesa 34 club-partita** contro le 11 di Jurić. Contraddice F4 dello stesso audit. Il piano §9.2 scrive «copertura sotto lo 0,3%» che è il tasso di **mancanza** |
| 50 | valore di mercato nel tempo | VERIFICATO | `player_valuations.csv` — già in repo | **93,00%** dei giocatori (7.169/7.709), 154.022 valutazioni, mediana 22 a testa, mediana 156 giorni fra due, 0 null | **Unico campo di valore che porta la propria data**: nessun look-ahead se si usa l'ultima precedente. Si ferma al **2026-02-27** (coda 2025-26 scoperta) |
| 51 | distanza dal picco di carriera | VERIFICATO | `players.highest_market_value_in_eur` | 93,00%; **è esattamente il massimo dell'intera serie nel 100% dei casi** | 🔴 **LOOK-AHEAD ATTIVO (R8)**: la checklist la marca `pre`, ma su una partita del 2018 inietta il massimo raggiunto fino al 2026. **Il repo lo legge già** (`scripts/build_stagione_anagrafica.py:225`). Correzione gratuita: massimo progressivo fino alla data |
| 52 | presenze e gol in nazionale | ASSUNTO | `players.international_caps/goals` | **58,20%** (mai misurata prima nel piano); `current_national_team_id` **2,74%** | 🔴 Tre rischi cumulativi: (a) R8 — snapshot **non datato**, applicato a una partita del 2018 è look-ahead puro; (b) R6 — 3.222 NaN non distinguono «mai convocato» da «non rilevato»; (c) **il repo lo legge già** (`build_stagione_anagrafica.py:222`) |
| 53 | posizione in classifica delle due squadre | VERIFICATO | `games.home/away_club_position` | **100,00%** (16.111/16.111), range 1-20 | R8 dichiarato: è la classifica **DOPO** la giornata (88,7% di accordo contro 44,9% per «prima»). Il ritardo va fatto **per squadra**, non per data di calendario |
| 54 | campo di casa temporaneo | VERIFICATO | `games.stadium` | 100% pieno, 174 stadi, 28 club con >1 stadio, 603 partite fuori dal modale (3,74%) | ⚠️ **[rett.]** la correzione dell'audit sgonfia troppo: i campi **davvero temporanei con ritorno documentato** sono **≥77** (Tottenham a Wembley 33, Real Madrid al Di Stéfano 25, Betis alla Cartuja 19), **118 = 0,73%** contando il Barcellona al Lluís Companys — **non 33 = 0,20%**. E lo stesso campo compare sotto due grafie: la **tabella di alias-stadio serve PRIMA di contare** |
| 55 | contesto-club (squad_size, average_age, …) | VERIFICATO | `clubs.csv` — già in repo | ⚠️ **[rett.]** perimetro sbagliato: i club che hanno **giocato** nel perimetro sono **153, non 176**. Ricalcolando: `coach_name` **69,28%** (non 60,23%), `average_age`/`foreigners_percentage` **99,35%** (non 99,43%). `total_market_value` **0,00%** | 🔴 Diagnosi confermata e grave: sono **snapshot singoli per club**, e l'annata dipende dall'ultima stagione in lega, **cioè da un ESITO (retrocessione)**. Un modello ci si aggancia e sembra funzionare |
| 56 | `sub_position` (ruolo di dettaglio) | VERIFICATO | `players.csv` — già letto dal repo | 99,97% (la % è giusta) | ⚠️ **[rett.]** (a) i conteggi pubblicati (Centre-Back 8.766…) sono **globali, non del perimetro** — impossibili, visto che superano i 7.709 giocatori totali; sul perimetro sono 1.361/1.152/…/70. (b) **`position` ha un segnaposto letterale `'Missing'`**: 100% non-null ma non 100% informativa (2 perimetro, 586 globali = 1,17%) — R6 puro |
| 57 | rigori, autogol, parte del corpo, tipo assist | VERIFICATO | `game_events.description` | description 100% dei 44.929 gol; **ma parte del corpo solo 78,8%** (35.412), oscillante 73,7-82,3% per stagione; `player_assist_id` 77,67% | La mancanza **non è casuale**: rigori (4.159) e autogol (1.333) non la dichiarano mai → ogni tasso «gol di testa su totali» è distorto. `Through ball`/`Headed assist`: **0 occorrenze** |
| 58 | motivo del cartellino, rosso vs doppio giallo | VERIFICATO | `game_events.description` | motivo mancante nel **12,15%**; 18 etichette; espulsioni separabili 1.784 + 1.338 | Trappola di parsing **non scritta da nessuna parte nel piano**: `N. Yellow card` è il **contatore stagionale del giocatore**, non «ennesima ammonizione nella partita» — leggerlo male produce **15.077 espulsioni invece di 3.122 (11×)** |
| 59 | sostituzione per infortunio | VERIFICATO | `game_events.description` | 10.558 cambi-infortunio; motivo presente sul **91,23%** (0% mancante dal 2024-25, **30-43% nel 2017-18**) | ⚠️ **[rett.]** Il «calo 11,71% → 8,10%» **non esiste**: quei numeri sono la quota sulle sostituzioni **ETICHETTATE**, cioè condizionata alla variabile da neutralizzare. Per sostituzione **effettuata**: **8,20% (2017-18) → 8,09% (2025-26), PIATTA**. La conclusione dell'audit (il +56% è il regolamento, non gli infortuni) **esce rafforzata**; i numeri pubblicati per sostenerla no |
| 60 | orario di inizio della partita | VERIFICATO | football-data `Time` | **assente in 2017-18 e 2018-19**, 100% dal 2019-20; **~77,3-77,8%** e solo 3 leghe su 5 nei file in repo | Il piano lo dà «✅ RISOLTO, file già in repo»: **vero a metà**. Bundesliga e Ligue 1 vanno raccolte; e `Time` è in **ora britannica** (+60 min per le 4 leghe non inglesi): importarla senza correggere sfalsa di un'ora **senza che nessun controllo se ne accorga** |
| 61 | meteo della partita | ASSUNTO | open-meteo archive (mai interrogata) + `stadi.json` | **mai misurata**. Coordinate: 90 stadi (stagione 2026-27) contro **174 stadi storici**; orario 77,3% | (1) R8/train-serve skew: l'archivio dà il meteo **osservato** (`post`), in produzione si avrebbe la **previsione** (`pre`) — scarto mai discusso; (2) dipende dalla riga 60, bucata proprio sul 2017-19; (3) coordinate storiche inesistenti, e il file avverte: «un meteo sulla città sbagliata è peggio di nessun meteo» |

### Fetta 4 — fronte ALLENATORI (F1-F32)

| # | dato | stato | fonte | copertura | rischio |
|---|---|---|---|---|---|
| F1 | allenatore per partita | VERIFICATO | `games.home/away_club_manager_name` | **16.110/16.111 = 99,99%** (il piano diceva «meno dello 0,3% mancante»: pessimista di 30×) | Nessun ID: stringa libera (F4). Licenza CC0 **dichiarata da chi non è titolare** — il 100% del fronte poggia su questa contraddizione, mai discussa |
| F2 | semantica: è chi era IN PANCHINA quel giorno | VERIFICATO | `games` | verificata su 5 esoneri di metà stagione, tutti con la data giusta; Bayern 01/10/2017 = **Willy Sagnol per una sola partita** | Proprio perché è così, il **26,2%** degli spell contigui globali (7,4% nel perimetro) dura **una partita**: vice/traghettatori, non mandati |
| F3 | `club_games.csv` (vista per-club) | ASSUNTO | `club_games` | **mai misurata** (cache cancellata prima del controllo) | `club_games.is_win` è **LOSSY** (pareggio codificato come sconfitta): il record V-N-P di un allenatore costruito lì sarebbe sistematicamente sbagliato |
| F4 | chiave allenatore (nome libero) | VERIFICATO | `games` | 7.031 nomi globali, **36 gruppi ambigui**; nel perimetro 496 nomi, **2 gruppi** | ⚠️ **[rett.]** l'impatto è **3,01% (485/16.111), non 5,33% (858)**: numeratore globale su denominatore di perimetro. R7 in forma pura |
| F5 | `manager_spells.csv` (mandati) | DERIVATO | derivato da F1 | 13.854 spell globali, 907 nel perimetro (906 normalizzati); **8,7%** delle coppie ha >1 spell contiguo | ⚠️ **[rett.]** (a) i «casi estremi» sono sbagliati: il massimo è **Génésio al Lille 13+13 = 26 spell**, interamente artefatto di grafia (normalizzando → **1**). (b) **Secondo modo di fallire non dichiarato**: 7 mandati su 906 **saldano una RETROCESSIONE** in un unico spell (Andreazzoli @ Empoli: 49 partite dal 17/03/2019 al 21/05/2022, **818 giorni di buco interno**). Nessuno dei flag proposti lo intercetta |
| F6 | esordio / data di inizio mandato | DERIVATO | F5 | **3.085/13.854 = 22,3%** iniziano alla prima partita nota del club → censura a sinistra | Finto pieno (R6): la colonna sembra una misura ed è il bordo del dataset. Serve un flag `censura_sx` che lo schema §2 **non prevede** |
| F7 | come è finito il mandato (esonero/dimissioni) | MANCANTE | nessuna | **0%** — nessun campo in nessuno dei 12 file | Il piano formula la domanda **come se il dato ci fosse**, e nemmeno una fonte alternativa è stata cercata |
| F8 | «le ultime 3-4 partite prima di un esonero» | DERIVATO | F5 + snapshot | **511 cambi in-stagione** (ES1 105, FR1 88, GB1 110, IT1 106, L1 102) | Misurabile solo come «prima di un CAMBIO», perché la causa (F7) non esiste. Va filtrato per durata minima, altrimenti misura i vice |
| F9 | effetto rimbalzo del nuovo allenatore | DERIVATO | F5 + snapshot | 511 eventi; **322/876 club-stagione (36,8%)** con più di un allenatore | ~57 cambi/stagione su 5 leghe: **da stimare pooled, non per lega**. Rimbalzo e firma stilistica si confondono |
| F10 | stile di gioco dal join con gli snapshot | DERIVATO | `data/{lega}_matches.csv` | ⚠️ **[rett.] non «100,0% su tutte e cinque»**: Bundesliga **99,96%**, Ligue 1 **99,97%** (una partita scoperta ciascuna) | 🔴 Il piano afferma che gli snapshot contengono «corner e cartellini Tier 3»: **FALSO**. E **possesso e dribbling non esistono per NESSUNA lega** — cioè proprio ciò che l'utente cita come firma dello stile è Tier B, non Tier A |
| F11 | estensione alle coppe europee | VERIFICATO | `games` | CL 1.246 (0,00% mancanti), EL 1.603 (0,12%), UCOL 728 (0,14%), qualificazioni 0,22-0,26% | «Gratis» è vero per la copertura, **falso per l'identità**: la grafia cambia fra competizioni (F4) — Lille 2025-26 è «Bruno Genesio» in 34 gare di Ligue 1 e «Bruno Génésio» in 12 di EL |
| F12 | stile di gioco nelle coppe europee | MANCANTE | nessuna | **0%** — Understat copre solo le 5 leghe domestiche | È **la metà dell'ipotesi utente** (lo stile, non il risultato) a restare scoperta proprio dove il test sarebbe più informativo |
| F13 | allenatori delle NAZIONALI | VERIFICATO | `games` (tornei finali) | 742 partite, **238 CT distinti, 0,00% mancanti** su tutti e 5 i tornei; `national_teams.coach_name` **0 non-null su 124** | ⚠️ **[rett.]** i CT che sono anche allenatori di club sono **118 = 50%, non 109 = 46%**: «meno della metà» non regge, è **metà esatta**. Nessuna qualificazione, amichevole o Nations League |
| F14 | modulo schierato | VERIFICATO | `games.home/away_club_formation` | **99,65%**; 30 valori distinti; **non è un default**: mediana 6 moduli per club-stagione, solo 2,9% con modulo unico | (a) Il **36,1%** porta annotazioni editoriali («4-3-3 Attacking» 5.438, «4-4-2 double 6» 2.839): senza normalizzare sono moduli diversi. (b) R8 **non verificabile dal dato**: è plausibilmente codificato a posteriori dai redattori |
| F15 | reattività (cambia modulo dopo una sconfitta?) | DERIVATO | F14 + risultati | 99,65% (eredita F14) | Eredita il dubbio R8 di F14: se il modulo è codificato ex-post, «ha cambiato modulo» riflette ciò che si è visto in campo |
| F16 | uso della rosa (quanti impiega, età media, U21) | DERIVATO | `appearances` + `players` — in repo | 99,99% delle partite; `date_of_birth` 99,90% | L'**undici titolare esatto** non è in repo: serve `game_lineups.csv` (352 MB, mai importato) |
| F17 | turnover per competizione | DERIVATO | `appearances` + `games` | CL 34.209 righe, EL 27.055, CDR 17.019, FAC 12.332, DFB 11.178, CIT 10.627 | **UCOL (Conference) = 0 righe**: per Fiorentina, Roma, West Ham… il turnover verso la coppa **dove è massimo** non è misurabile |
| F18 | uso delle sostituzioni (quante, quando la quinta) | VERIFICATO | `game_events` | 124.073 sostituzioni su 16.110/16.111; **un solo** evento con minute=−1; regime 3→5 quantificato (2,87 → 4,51 per squadra-partita; ≥5 cambi: 0,0% nel 2017-18 → 66,2% nel 2025-26) | R6 sul minuto: **6.056 cambi al 90' contro 2.195 all'89', zero oltre** — «quando fa la quinta» è cieco **proprio nel recupero**. R4: massimo 10 sostituzioni per squadra-partita nel 2023, oltre qualunque regolamento |
| F19 | curva del mandato (1° vs 3° anno) | DERIVATO | F5 | **solo 103 mandati su 906 (11,4%)** arrivano al 3° anno (603 durano 1 stagione) | (a) 103 è poco per una curva. (b) **Look-ahead R8 non dichiarato**: «3° anno di mandato» esiste solo dopo, perché la durata totale è `post`. La versione usabile è «partite di mandato FINORA» |
| F20 | rendimento per livello dell'avversario | DERIVATO | F1 + Elo in casa | eredita l'Elo (fronte altrui, dichiarato risolto) | Derivato che poggia su un derivato: al 31/07/2026 l'Elo **non è un artefatto versionato del repo** |
| F21 | testa a testa fra allenatori | DERIVATO | F1 | **7.349 coppie, mediana 2 incontri**; ≥5 solo 9,4%, ≥10 solo 0,8% | **Praticamente inutilizzabile** per-coppia. O si abbandona o si riformula come effetto gerarchico con shrinkage fortissimo |
| F22 | gestione del risultato (in vantaggio chiude o attacca) | DERIVATO | `game_events` (157 MB, non in repo) | ricostruzione già **provata** su 16.111/16.111: 94,92% minuti esatti, 99,986% entro ±1, invariante «11 in campo» 99,39% | L'**8,9%** dei gol sta in un secchio senza minuto esatto: «cosa fa dal 75' quando è avanti di uno» è **l'analisi più danneggiata** dal troncamento |
| F23 | reazione dopo una sconfitta pesante | DERIVATO | F5 + snapshot | 100% del perimetro | ⚠️ R1: se i gol vengono da `games.csv` si importa il **risultato del tribunale**. ⚠️ **[rett. F29]** i casi sono esattamente **2 su 16.111**: Verona-Roma 19/09/2020 e Union Berlin-Bochum 14/12/2024. Nessun altro |
| F24 | disciplina della squadra (cartellini) | DERIVATO | `game_events` / `appearances` / football-data | eventi 99,99%; football-data **3 leghe su 5** nel repo | `appearances.red_cards` conta **solo i rossi diretti**, ignorando i 9.741 secondi gialli: chi misura «quanto fa espellere» da lì **dimezza il segnale** |
| F25 | primo anno in QUEL campionato | 🔴 **ASSUNTO** ⚠️ *[declassato]* | F1 | ⚠️ **[rett.]** L'audit lo dava «solido quanto F1». **È il contrario**: `games.csv` per le top-5 comincia il **2012-08-10**. **155/496 allenatori (31,2%)** hanno la prima apparizione prima del 2014 e compaiono in **11.344/16.111 partite = 70,4%** | 🔴 Falsi conclamati: **Ancelotti debutta in Serie A il 2018-08-18**, Mourinho il 2021-08-22, Ranieri il 2019-03-11, Hodgson in Premier il 2017-09-16, Koeman in Liga il 2020-09-27. La feature dice «primo anno **visibile dal 2012**». È lo stesso R6 che l'audit segnala per A12/A13 **e assolve qui** |
| F26 | esperienza globale dell'allenatore | ASSUNTO | `games` | **153/496 (30,8%)** hanno ZERO partite precedenti visibili, e nessuno è spiegabile dal bordo. Mediana esperienza visibile: **8 partite**. Brasile/Argentina/MLS/Giappone/Arabia partono dal **2024-2025**; nessuna seconda divisione | 🔴 **È IL finto pieno del fronte, ora con un numero.** Esempi: Robert Moreno, Coudet, Almirón, Christian Gross, Di Biagio, Pirlo, Terzić. Il campo `esperienza_globale_a_inizio_mandato` va **rinominato «esperienza VISIBILE AL DATASET» o non costruito** |
| F27 | giocatore × allenatore (minuti) | **ASSUNTO** ⚠️ *[declassato]* | `appearances` × `games` | il join regge: **476.382/476.382, 0 orfane**, manager attribuibile al 100% | ⚠️ **[rett.]** falso il «nessun rischio strutturale, unico avvertimento SE si normalizzano male i nomi»: **la chiave è GIÀ scissa nella fonte**, con intervalli **disgiunti** — «Ivan Juric» 231 partite (2017→2025-04) vs «Ivan Jurić» 11 (2025-08→2025-11); «Bruno Génésio» 209 vs «Bruno Genesio» 34 (dal 2025-08). Dichiarare «nessun rischio» **invita a non normalizzare** |
| F28 | «i suoi giocatori» (chi si porta dietro) | DERIVATO | F5 × `transfers.csv` | **~8,7%** (eredita transfers: 0 righe per Ronaldo, Lukaku, Immobile, Dybala, Mbappé) | Derivato che poggia su un ASSUNTO già refutato. Alternativa solida: ricostruire i cambi di club dai `player_club_id` in appearances (100%) |
| F29 | `manager_match_style.csv` (join sugli snapshot) | **ASSUNTO** ⚠️ *[declassato]* | F5 × snapshot | ⚠️ **[rett.] 16.105/16.111, non 16.111.** L'audit dichiarava 100% appoggiandosi a un risultato **riferito e non rieseguito**. Le 6 orfane sono disallineamenti di **un giorno** (Liga 2, Ligue 1 4) | Difetto piccolo e riparabile (tolleranza ±1 giorno), ma **è esattamente il modo in cui si accumulano affermazioni sbagliate**. Il contenuto è quello di F10, non quello promesso dal nome «style» |
| F30 | `clubs.coach_name` (mai nominata dal piano) | VERIFICATO | `clubs.csv` — già in repo | **403/796 = 50,6%** | Trappola R8 pura: è il tecnico **CORRENTE**. Usarlo su una partita del 2019 le attribuisce l'allenatore del 2026. **Va marcato inutilizzabile prima che qualcuno lo scopra e lo usi** |
| F31 | allenatore × arbitro | MANCANTE | — | n/a | **Scartata esplicitamente dall'utente** il 30/07/2026. Non è un buco, è una decisione: non riproporre |
| F32 | firma stilistica «stesso allenatore, due squadre» | DERIVATO | F5 × F10 | **parzialmente misurata**: 1.084 coppie globali con più spell; quanti allenatori abbiano ≥2 club con abbastanza partite **non è mai stato contato** | La firma va misurata su xG/PPDA/deep (F10), **non su possesso/dribbling che non abbiamo**: il test eseguibile è più stretto di quello che l'utente ha descritto, e va detto **prima** |

### Fetta 5 — fronte ARBITRI (A1-A25)

| # | dato | stato | fonte | copertura | rischio |
|---|---|---|---|---|---|
| A1 | arbitro per partita (nome) | 🔴 **ASSUNTO** ⚠️ *[declassato]* | `games.referee` | copertura **16.105/16.111 = 99,96%** (confermata). **Accuratezza mai testata** finché non l'ha fatto lo scettico | ⚠️ **[rett.]** Contro football-data (bundle Premier, 3.420/3.420 agganciate): **13 partite = 0,38% con un COGNOME DIVERSO** — persone diverse, non varianti (2018-02-05 Watford-Chelsea: «M Dean» vs «Craig Pawson»; 2025-02-26 Liverpool-Newcastle: «C Kavanagh» vs «Stuart Attwell»). **1 caso su 263, e il progetto non lo sapeva.** Misurabile solo in Premier: sulle altre 4 leghe **non verificabile**. R8: è l'arbitro che HA arbitrato, usato come proxy del DESIGNATO |
| A2 | arbitro nelle coppe europee | VERIFICATO | `games` | CL 100,00%, EL 99,94%, UCOL 100,00%, CLQ 99,74%, ELQ 99,92%, ECLQ 99,85% | L'estensione «gratis» vale **solo per l'arbitro**: in Conference la Conference ha 0 appearances, quindi arbitro×cartellini non si incrocia |
| A3 | arbitro da football-data (`Referee`) | VERIFICATO | football-data, file in repo | Premier **3.420/3.420 = 100%**; **La Liga: colonna assente** in tutte e 9 le stagioni; **Serie A raw: colonna assente** | Grafie **incompatibili** fra le fonti («M Oliver» vs nome esteso). Il dizionario di aggancio **non esisteva**; misurato ora: **98,92%** (3.383/3.420) con la regola iniziale+cognome |
| A4 | cartellini per arbitro | VERIFICATO | 3 fonti indipendenti | 67.682 eventi Cards, description mai nulla, 27 con minute=−1 (0,04%); HY/AY/HR/AR 100% nei file in repo | Nessuno di copertura. Il confine regge: vale sul mercato **cartellini**, non sull'1X2 (Fase 125: +0,00368, IC [+0,00269, +0,00469]) |
| A5 | rossi diretti vs doppie ammonizioni | DERIVATO | `game_events.description` | 64.560 gialli, **1.338 secondi gialli**, 1.784 rossi diretti — separabili | **Corregge in positivo** §9.1 n.6: `appearances.red_cards` ignora i secondi gialli, ma gli eventi li distinguono. La voce è **fattibile, non persa** |
| A6 | motivo del cartellino | **ASSUNTO** ⚠️ *[declassato]* | `game_events.description` | 12,34% senza motivo in totale; FR1 2018-19 **84,0%**, GB1 2018-19 47,4%, IT1 2017-18 42,1% | ⚠️ **[rett.]** «dal 2019-20 si stabilizza (0-13%)» è **falso**: FR1 2019-20 = **34,2%**, GB1 = 19,8%; FR1 2020-21 = 18,1%, GB1 = 15,9%, ES1 = 13,5%. La prima stagione in cui tutte e 5 stanno in 0-13% è il **2021-22**. La finestra danneggiata è **2017-2021 = 4 stagioni su 9 (44% del perimetro)**, non 2 |
| A7 | rigori assegnati per arbitro | 🔴 MANCANTE | nessuna | **0%.** `game_events` ha solo 4 tipi (Substitutions, Cards, Goals, Shootout): un rigore compare **solo se segnato** (4.159 = 9,26% dei gol). Rigori sbagliati o parati: **inesistenti in tutti e 12 i file** | 🔴 **Il piano se la dà per risolta DUE volte** (§10.4, §10.8). Il derivato «rigori realizzati» sotto-conta di ~un quinto, e il sotto-conteggio dipende da tiratore e portiere: usarlo come propensione dell'arbitro è **R6 esatto** |
| A8 | falli fischiati per partita | VERIFICATO | football-data HF/AF | **10.260/16.111**: Serie A 3.420, Premier 3.420, Liga 3.420. **Bundesliga e Ligue 1: nessun CSV grezzo nel repo** | Il costo residuo vero è procurare i grezzi delle due leghe nuove — che §10.4/§10.8 **non menzionano** |
| A9 | recupero concesso (minuti aggiunti) | CHIUSO_LICENZA | api.fifa.com | non derivabile dai file in casa: minuto troncato a 90, **17.982 eventi al minuto 90** contro 3.782 all'89' | ToS FIFA §5.3 + robots 503 persistente = disallow per RFC 9309. **Non si aggira.** La catena «recupero → Over → gol nel finale» è interrotta **a monte** |
| A10 | uso del VAR | CHIUSO_LICENZA | api.fifa.com (5.603 partite), API Premier League | `referee` è **l'unica colonna arbitrale** dei 12 file: 0 VAR, 0 assistenti | Chiusura pulita e ben documentata. Unica via: **raccolta prospettica** dalla 2026-27 |
| A11 | terna arbitrale completa | CHIUSO_LICENZA | Wyscout 2017-18 (CC BY 4.0) è l'unica aperta | **11,3%** della finestra (1.826 partite) | §9.8 la dà 🟡 con «api.fifa.com dal 2020/21»; §10.4 (successiva) dichiara quella fonte **CHIUSA**. Le due sezioni si contraddicono: chi legge §9.8 senza §10.4 **pianifica una raccolta impossibile** |
| A12 | esperienza dell'arbitro (partite arbitrate prima) | 🔴 DERIVATO | `games` intero | **123/250 arbitri (49,2%) censurati a sinistra** (prima apparizione 2012-2013), e arbitrano **10.661/16.105 = 66,2% del perimetro**. Nessuna seconda divisione nel dataset | 🔴 **R6 conclamato e MISURATO**: per due terzi delle partite «partite arbitrate finora» è un numero che sembra una misura e non lo è. Va rinominata («partite visibili dal 2012») o accompagnata da un flag di censura |
| A13 | esperienza nella competizione specifica | DERIVATO | `games` | affidabile solo per i **127/250** non censurati | Stesso R6 di A12, **aggravato**: «prima partita di Champions» è una variabile di coda, cioè proprio dove la censura morde |
| A14 | quanto spesso gli affidano i big match | DERIVATO | `games` + indice di forza | base arbitrale verificata; indice di forza **non nel dataset** (`clubs.total_market_value` **0 valori non-null**) | Derivato di secondo livello su un derivato non ancora versionato |
| A15 | nazionalità dell'arbitro | MANCANTE | nessuna: il campo **non esiste** | proxy possibile ma selettivo: solo **318/539 arbitri di coppa (59,0%)** hanno anche una lega domestica nel dataset | Il proxy manca **proprio gli arbitri delle federazioni minori**, cioè quelli su cui l'ipotesi «lo stile del suo campionato si trasferisce» sarebbe più interessante |
| A16 | arbitro × squadra | DERIVATO | `games` | **4.920 coppie, mediana 5 partite**; solo il **25,2%** arriva a ≥10 | Quasi tutto rumore alla grana proposta. Con shrinkage K=40 passa **~11%** del segnale grezzo: da dichiarare **prima** di costruirci sopra |
| A17 | bias casa/trasferta per arbitro | DERIVATO | `games` + `appearances` | 250 arbitri, mediana 54 partite; 98 con <30 partite ma pesano **solo il 5,5%** delle partite | Lo schema §2 **non prevedeva lo shrinkage**, rilevato e mai corretto. Tono descrittivo obbligatorio: sono persone reali |
| A18 | coerenza/variabilità dell'arbitro | DERIVATO | come A17 | **mai calcolata da nessuna fase** | R7: se si conclude «questo arbitro è più imprevedibile» **serve l'intervallo**, altrimenti si legge la varianza campionaria. Errore standard ~sd/√(2·53): rumorosa per il quartile basso (q25 = 11 partite) |
| A19 | `attendance` | 🔴 **ASSUNTO** ⚠️ *[declassato]* | `games.attendance` | 86,70% (13.969/16.111), NaN mai zero, minimo 100 | 🔴 ⚠️ **[rett.] Nessuno aveva guardato dentro le celle piene.** In **BUNDESLIGA 796/2.382 (33,42%)** hanno attendance **esattamente uguale a `stadium_seats`** — la capienza, non una misura (altre 4 leghe: 0,03-0,41%). Controprova: valori distinti/partite in casa ha mediana 0,95-1,00 in ES1/FR1/GB1/IT1 e **0,617 in L1**; il **Bayern ha 9 valori distinti su 130 partite, l'86% esattamente 75.000**; l'Heidenheim 49/51 a 15.000. Per l'uso proposto («vantaggio-casa in funzione del pubblico») in Bundesliga **si misurerebbe la CAPIENZA**. R8: è comunque `post` |
| A20 | `round` (turno) | VERIFICATO | `games.round` | **16.111/16.111 = 100%** | Nessuno: è `pre` per natura |
| A21 | `home/away_club_formation` nella riga arbitro | VERIFICATO | `games` | 99,65% / 99,66% | R8 sottile **non dichiarato dal piano**: il modulo è noto al più ~1h prima, mentre il resto della raccolta prospettica è ancorato a **T−2 giorni**. Mescolarli nella stessa riga di feature è look-ahead |
| A22 | `aggregate` | MANCANTE | `games.aggregate` — esiste, 100% piena, **inutile** | copia letterale del risultato in 88.958/88.958 righe | **Incoerenza interna del piano**: §1.8 l'ha barrata, ma lo schema §2 la elenca ancora. Chi scrive l'importer leggendo §2 **importa una colonna morta**. Finto pieno da manuale |
| A23 | chiave / identità dell'arbitro | **ASSUNTO** ⚠️ *[declassato]* | `games.referee` (nessun ID) | l'audit concludeva «**ZERO** gruppi collassano → rischio arbitro-fantasma BASSO» | ⚠️ **[rett.] Artefatto del test scelto**: cercava collisioni esatte dopo normalizzazione, che per costruzione **non vedono la stessa persona con un token in più o in meno**. Trovati almeno **3 casi**: «Samuel Allison» (15 gare, fino al 2024-08-28) vs «Sam Allison» (2, dal 2024-08-24) — **coesistono a 4 giorni**; «Dr. Robin Braun» vs «Robin Braun»; «Andrea Airaghi Colombo» (15) vs «Andrea Colombo» (47), intervalli disgiunti. **«250 arbitri» è un sovra-conteggio**, e ogni feature cumulativa (A12/A16/A17/A18) **si azzera al cambio di grafia**. Bonus: «Transfermarkt scrive il nome per esteso» è falso — «De Burgos Bengoetxea», 176 gare, 7° per volume, non ha nome proprio |
| A24 | designazione arbitrale PROSPETTICA | MANCANTE | nessuna storica, **per costruzione** | 0%. `scripts/raccolta_giornaliera.py` scrive già il record `arbitro_designato` con `"arbitro": None` | 🔴 È **l'unico modo per rendere `pre` il dato di A1**. Finché non parte, **ogni backtest che usa l'arbitro sta usando un dato `post` come se fosse `pre`** — e il piano non lo scrive. AIA e FFF: 403 anti-bot, non si aggirano |
| A25 | tabella `referee_matches.csv` | MANCANTE | da costruire da `games` | **nessun file `referee_*` esiste in `data/`** | Finché non esiste sono violate tre regole del CLAUDE.md: **riproducibilità** (i numeri della Fase 125 non sono rifacibili da terzi coi file del repo — `_run_fase125_cartellini.py` fa `kagglehub.dataset_download` **a runtime**, e l'upstream si aggiorna ogni settimana), **offline-first** (§5), **catalogo dati** (`docs/DATI.md` non contiene **nessuna** voce sull'arbitro) |

---

## D · COSA NON È A POSTO — da leggere per primo

*In ordine di gravità. Sono le voci che il piano dà per risolte, o che l'audit dava per verificate, e non lo sono.*

### Gravità ALTA

1. **`attendance` in Bundesliga è la CAPIENZA, non il pubblico.** 796 partite su 2.382 (**33,42%**) hanno `attendance` esattamente uguale a `stadium_seats`. Il Bayern ha **9 valori distinti su 130 partite in casa**, l'86% esattamente 75.000. L'uso che il piano propone — «misurare il vantaggio-casa in funzione del pubblico» — in Bundesliga misurerebbe la capienza dello stadio. L'audit aveva dichiarato VERIFICATO guardando solo la copertura (86,70%). **Declassato ad ASSUNTO.**

2. **«Primo anno in QUEL campionato» (F25) è falso per 155 allenatori su 496 (31,2%), che coprono il 70,4% delle partite.** `games.csv` per le top-5 parte dal 2012-08-10, e la feature legge il bordo del dataset come un esordio. Falsi verificabili: **Ancelotti «debutta» in Serie A il 18/08/2018**, Mourinho il 22/08/2021, Ranieri l'11/03/2019, Hodgson in Premier il 16/09/2017, Koeman in Liga il 27/09/2020. L'audit riconosce questo identico difetto per gli arbitri (A12) e lo assolve qui. **Declassato ad ASSUNTO.**

3. **«Primo anno in un campionato nuovo» (voce 46) copre il 34,8%, non il 55,9%.** Due errori sommati: perimetro esteso al 2012 e definizione di «passato» che contava anche la Coppa Italia dello stesso club nella stessa settimana. Con il filtro corretto (`domestic_league`) il confondente «esordiente dal vivaio vs arrivato da campionato non coperto» tocca **due terzi dei casi (65,2%)**, non il 44%.

4. **1.119 titolari (0,317%) non hanno minuti**, e il buco è lega×stagione: **ES1 2020 al 4,60%**, FR1/IT1/GB1 2021 allo 0,8-1,5%, 2017 e 2023-25 a ~0. Chi costruisce «minuti per giocatore» con `lineups LEFT JOIN appearances + fillna(0)` registra 1.119 titolari che hanno giocato come «non hanno giocato», **proprio nelle stagioni COVID**, cioè dove il carico è l'oggetto d'interesse (voce 14).

### Gravità MEDIA

5. **L'accuratezza dell'arbitro non era mai stata testata (A1).** Contro football-data, **13 partite su 3.420 (0,38%) hanno un cognome diverso** — persone diverse, non varianti di grafia. Sulle altre 4 leghe l'accuratezza **non è verificabile con i dati in repo** (La Liga e Serie A non hanno la colonna `Referee`).

6. **Gli «arbitri fantasma» esistono (A23).** L'audit concludeva «zero gruppi collassano → rischio BASSO», ma il test cercava collisioni *esatte*: per costruzione non vede la stessa persona con un token in più. Trovati ≥3 casi, fra cui «Samuel Allison» e «Sam Allison» che **coesistono a 4 giorni di distanza**. Ogni feature cumulativa per arbitro **si azzera al cambio di grafia**.

7. **La finestra danneggiata sul motivo del cartellino è 2017-2021 (44% del perimetro), non 2017-19 (A6).** FR1 2019-20 ha il **34,2%** dei cartellini senza motivo, GB1 il 19,8%. Chi accettasse il perimetro suggerito dall'audit costruirebbe **comunque** il profilo-arbitro su un campione mutilato per lega.

8. **La chiave allenatore è già scissa nella fonte (F27), non «se la normalizziamo male».** «Ivan Juric» 231 partite (fino al 2025-04) contro «Ivan Jurić» 11 (dal 2025-08); «Bruno Génésio» 209 contro «Bruno Genesio» 34 — **intervalli disgiunti**: la fonte ha cambiato grafia in corsa. Dichiarare «nessun rischio strutturale» invita a non normalizzare.

9. **Due look-ahead ATTIVI, già dentro il codice del repo.**
 - `highest_market_value_in_eur` (voce 51) è il massimo dell'**intera** serie nel 100% dei casi, ma è letto da `scripts/build_stagione_anagrafica.py:225`. Correzione gratuita: massimo progressivo fino alla data della partita.
 - `international_caps`/`international_goals` (voce 52) sono uno **snapshot non datato**, coperti al 58,20%, letti da `build_stagione_anagrafica.py:222`, con 3.222 NaN che non distinguono «mai convocato» da «non rilevato».

10. **`contract_expiration_date` (voce 33) è un finto pieno di anni.** 76,66% come valore attuale, **0% come valore storico**: dei 674 giocatori usciti dalle nostre leghe entro il 2020, il **100%** ha una scadenza ≥ 2023-01-01. Il piano la dava ✅. Va declassata ad ASSUNTO/parziale.

11. **`clubs.csv` (voce 55) è uno snapshot la cui annata dipende da un ESITO.** Le sei colonne sembrano piene al 99-100%, ma l'annata dello scrape coincide con l'ultima stagione in cui il club era in quella lega — cioè con la **retrocessione**. Un modello ci si aggancia e sembra funzionare. *(Nota: le coperture pubblicate dall'audit sono su 176 club di anagrafica invece dei 153 che hanno davvero giocato: `coach_name` è **69,28%**, non 60,23%.)*

12. **I rigori per arbitro (A7) NON sono risolti, e il piano se li dà per risolti due volte.** `game_events` ha solo 4 tipi: un rigore esiste **solo se segnato** (4.159). I rigori sbagliati o parati **non esistono in nessuno dei 12 file**. Usare i rigori realizzati come propensione dell'arbitro misura il tiratore e il portiere.

13. **L'esperienza dell'arbitro (A12) è censurata per il 66,2% delle partite** (123/250 arbitri hanno la prima apparizione nel 2012-2013). E non esiste **nessuna seconda divisione** nel dataset: un arbitro promosso dalla Serie B risulta a zero esperienza.

14. **L'esperienza globale dell'allenatore (F26) è falsa per il 30,8%.** 153 allenatori su 496 con zero partite precedenti visibili — Moreno, Coudet, Almirón, Gross, Di Biagio, Pirlo, Terzić. Brasile/Argentina/MLS/Giappone/Arabia entrano nel dataset **dal 2024-2025**.

15. **Un gol manca dagli eventi, silenziosamente (voce 47).** Toulouse-Brest 11/01/2020 finì 2-5 (confermato dal nostro snapshot indipendente) ma `game_events` ha un solo gol del Toulouse. Un gol mancante **riclassifica lo stato di tutti i gol successivi** della partita, e nessun controllo lo vede. La ricostruzione del punteggio va usata come **controllo permanente dell'importatore**.

16. **Il «+56% di infortuni» della voce 59 è il regolamento, e i numeri pubblicati per dimostrarlo sono sbagliati.** Il calo 11,71% → 8,10% è calcolato sulle sostituzioni **etichettate**, cioè condizionato alla variabile da neutralizzare (30,0% senza motivo nel 2017-18, 0,04% nel 2025-26). Per sostituzione **effettuata**: **8,20% → 8,09%, piatta**. La conclusione regge, la statistica no.

### Gravità BASSA (ma da correggere prima che si propaghi)

17. **Il join snapshot ↔ `games.csv` (F29) è 16.105/16.111, non 16.111** — l'audit dichiarava 100% appoggiandosi a un risultato **riferito e non rieseguito**. Le 6 orfane sono disallineamenti di un giorno. *(Buona notizia dallo stesso test: i casi in cui i gol differiscono sono **esattamente 2** — Verona-Roma e Union Berlin-Bochum. Nessun altro. Il rischio R1 di F23 è chiuso.)*
18. **I campi temporanei (voce 54) sono ≥77-118 partite (0,48-0,73%), non 33 (0,20%).** L'audit corregge giustamente il 3,74% gonfiato ma sgonfia troppo: dentro le «19 coppie ≥10 partite» ci sono Tottenham a Wembley (33), Real Madrid al Di Stéfano (25), Betis alla Cartuja (19). La **tabella di alias-stadio serve PRIMA di contare**, non dopo.
19. **Le partite senza distinta sono 54, non 48** (voce 42): oltre alle 48 di ES1 2018 ce ne sono 6 mai censite, fra cui **IT1 2025 e FR1 2025**. Attribuirle a un blocco «già noto e chiuso» significa che nessuno le cercherà più.
20. **F5: 7 mandati su 906 saldano una retrocessione** dentro un unico spell contiguo (Andreazzoli @ Empoli, **818 giorni di buco interno**). Non è il caso min/max né la censura a sinistra: è il **buco in mezzo**, e nessuno dei flag proposti lo intercetta. Due dei 7 stanno nella coda dei 103 mandati «≥3 stagioni» su cui poggia F19.
21. **Percentuali da rettificare**: ala invertita **64,04%** non 60,9% (voce 41, ambidestri nel denominatore); CT anche allenatori di club **50%** non 46% (F13); impatto dei nomi ambigui **3,01%** non 5,33% (F4, numeratore globale su denominatore di perimetro); discrepanza assist **608** non 1.169 (voce 3, il 48% erano autogol); xG negli snapshot **99,96-99,97%** non 100,0% in Bundesliga e Ligue 1 (F10).
22. **`position` ha un segnaposto letterale `'Missing'`** (voce 56): 100% non-null ma non 100% informativa. E i conteggi per ruolo pubblicati dall'audit sono **globali, non del perimetro** (aritmeticamente impossibili: «Centre-Back 8.766» supera i 7.709 giocatori totali).

---

## E · SORPRESE — cose emerse che il piano non diceva

**Sui dati già in casa**

1. **Gli xG/xA individuali sono sul disco da mesi.** Il piano afferma che Understat «ha solo aggregato-stagione per giocatore (minuti totali, non per-partita)». La prima metà è giusta, la seconda è **sbagliata**: i bundle contengono xG, xA, npxG, npg, xGChain, xGBuildup, key_passes, shots — **10.008 righe** (Premier 4.819 + Liga 5.189). È il parser del repo (`parse_season_players` in `src/data/understat.py`, righe 214-241) a scartarli.
2. **`clubs.coach_name` esiste e il piano non lo sa** (F30): 403/796 = 50,6% pieno. È il tecnico **corrente**: trappola R8 pura, da marcare inutilizzabile *prima* che qualcuno lo scopra.
3. **Il portiere titolare è identificabile nel 100,000% dei casi** (32.113/32.113 team-partita con esattamente 1 portiere): il piano lo dava «già coperto» senza mai contarlo.
4. **`appearances.csv` comincia il 2012-07-03.** Censura a sinistra **mai dichiarata da nessuna fase del piano**, e sta sotto le voci 12, 25, 39, A12, A13, F25, F26.
5. **La Coupe de France non esiste nel dataset.** `competitions.csv` ha 10 coppe nazionali (Spagna, Italia, Germania, Inghilterra, Danimarca, Grecia, Olanda, Russia, Scozia, Ucraina) — **nessuna francese**. Un giocatore di Ligue 1 non accumula MAI carico da coppa nazionale, uno di Bundesliga lo accumula all'86,6%: **il confronto cross-lega del carico è distorto per costruzione**.
6. **Il prefisso «N. Yellow card» è il contatore STAGIONALE del giocatore**, non «ennesima ammonizione nella partita». Leggerlo male produce **15.077 espulsioni invece di 3.122 (11×)**. Non è scritto da nessuna parte nel piano. *(In compenso, quello stesso contatore rende ricostruibili le squalifiche: dopo il 5° giallo in Serie A il giocatore manca dalla distinta successiva nel **96,9%** dei casi contro un fondo del 4,6-5,5%.)*
7. **Il `robots.txt` di Transfermarkt NON vieta un bot generico** (vieta `/ceapi`, `/quickselect`, `/jumplist`, e nominalmente CCBot/GPTBot/ChatGPT-User). Registrato per onestà, non usato e non proposto: è l'**unico caso in cui la catena della licenza non sarebbe rotta**, visto che è il titolare del dato che già usiamo via Kaggle.

**Sul metodo**

8. **Il fronte «carriere» è rimasto aperto per due ricerche consecutive per un errore di OGGETTO, non di fonte.** «La copertura è del 62,5%» era vero e insieme fuorviante: era la copertura della tabella più ricca, non del dato che serviva. Nessuna nuova fonte, nessuna nuova lingua, nessun nuovo permesso — bastava guardare **un altro pezzo della stessa pagina**. È la versione-dati della lezione della Fase 92. **Quando un fronte resiste, prima di cercare una fonte nuova va scritto in modo esatto CHE COSA si sta contando.**
9. **L'anti-avvelenamento non può fermarsi agli identificatori.** `sananmuzaffarov` non aveva né ID né URL Transfermarkt: l'ha smascherato una **firma numerica** (off-by-one di +1 nel 97,43%). Le firme numeriche sono più difficili da ripulire dei metadati — ma servono solo se hai già una fonte nota in casa contro cui misurare.
10. **`urllib.robotparser` di Python non implementa RFC 9309.** Applica *first-match-wins* invece di longest-match: su `Special:EntityData/*.json` (permesso da un `Allow` più lungo) restituisce `False`. **Chi verifica con quello si auto-chiude una fonte lecita.**
11. **Il rilevatore del blocco carriera ha avuto DUE bug veri prima di funzionare** (estraeva il testo di navigazione dello skin invece del corpo: 29/333 trovati; e scambiava un link a disambigua per una pagina di disambigua). La prova che ora è tarato è la **replica indipendente**: 62,2% contro il 62,5% dichiarato da un'altra sessione su un campione diverso.
12. **La regola R7 si è pagata tre volte in questo lavoro**: gli 868 «club in più» dalla lingua di casa (rumore, contro 852 dall'inglese); il 25,0% di club «non ritrovati» che era normalizzazione dei nomi (vero: 8,5%, e tutte sigle); e il calo apparente 11,71→8,10 delle sostituzioni per infortunio (denominatore condizionato).

**Sulle fonti esterne**

13. **L'unica fonte infortuni a origine genuinamente indipendente esiste** — l'API FPL, con `news_added` che è il **timestamp in cui il fatto diventa noto** (esattamente ciò che a Transfermarkt manca per R8) — **ed è chiusa dai ToS**, non dal `robots.txt`. Il muro non si supera con più codice.
14. **`fantacalcio.it` vieta esattamente e soltanto `/probabiliformazioniseriea`**: la fonte è chiusa proprio nel punto in cui vive l'informazione sugli indisponibili.
15. **`footballdatabase.eu` e `playmakerstats.com`, 🟡 nel piano, oggi sono 403 Cloudflare: vanno declassate a ❌.**
16. **Il `robots.txt` di `ar.wikipedia` vieta un singolo articolo** — `/wiki/سليم_دبور`, che è un calciatore. Non ci riguarda (non è nella coorte), ma chi userà questa via **deve controllare l'URL singolo, non solo il pattern** (R4).
17. **Gli allenatori delle NAZIONALI sono completi al 100%** su tutti e 5 i tornei finali (742 partite, 238 CT), mentre §9.9 chiude il fronte nazionali — **ma lo chiude per i GIOCATORI**. La distinzione non è scritta da nessuna parte, e il piano la appiattisce.

---

## F · CONTEGGIO FINALE

**118 voci auditate** (righe 1-61 della checklist §1.9, F1-F32 allenatori, A1-A25 arbitri), stato **dopo** l'applicazione delle refutazioni:

| stato | n | % | cosa significa |
|---|---:|---:|---|
| **VERIFICATO** | **36** | 30,5% | misurato sul perimetro reale (16.111 partite, 5 leghe, 2017-2026) |
| **DERIVATO** | **45** | 38,1% | calcolabile da dati verificati, ma è un calcolo con assunzioni da dichiarare |
| **MANCANTE** | **21** | 17,8% | nessuna fonte utilizzabile trovata |
| **ASSUNTO** | **13** | 11,0% | dato per buono e mai misurato, o misurato male → **da non usare finché non è chiuso** |
| **CHIUSO_LICENZA** | **3** | 2,5% | esiste, raggiungibile, vietato dai termini (recupero, VAR, terna completa) |
| **TOTALE** | **118** | 100% | |

**Ripartizione per fetta:**

| fetta | VER | DER | MANC | ASS | LIC | tot |
|---|---:|---:|---:|---:|---:|---:|
| Dati base giocatore (1-20) | 5 | 7 | 8 | 0 | 0 | 20 |
| Righe 21-40 | 5 | 10 | 4 | 1 | 0 | 20 |
| Righe 41-61 | 12 | 5 | 1 | 3 | 0 | 21 |
| Allenatori (F1-F32) | 8 | 16 | 3 | 5 | 0 | 32 |
| Arbitri (A1-A25) | 6 | 7 | 5 | 4 | 3 | 25 |
| **totale** | **36** | **45** | **21** | **13** | **3** | **118** |

**Declassamenti operati dalla verifica avversariale: 7** — A19 (attendance), F25 (primo anno in quel campionato), A1 (arbitro), A23 (identità arbitro), A6 (motivo cartellino), F27 (giocatore×allenatore), F29 (join manager_match_style). Tutti da VERIFICATO/DERIVATO ad **ASSUNTO**.
**Voci con numeri rettificati senza cambio di stato: 18.**

---

### Avvertenza finale (§1.6 del CLAUDE.md)

Nessuna delle 118 voci è stata **importata** nel repo: questo documento fotografa lo stato delle *fonti*, non un dato disponibile. Le **58 voci** in stato DERIVATO o ASSUNTO non sono pronte per una feature: le prime richiedono che l'assunzione sia scritta e testata, le seconde che qualcuno le misuri. E **il valore predittivo di tutto questo — infortuni, carriere, allenatori, arbitri — non è mai stato misurato su nessun mercato.** Visto il tetto informativo misurato per oltre 100 fasi (il mercato di chiusura ingloba il modello, α\*=0 sull'1X2 e sul GG/NG), **non è da dare per scontato che esista**. Il modello resta quello dichiarato dal README: **non usare per scommettere soldi veri allo stato attuale.**