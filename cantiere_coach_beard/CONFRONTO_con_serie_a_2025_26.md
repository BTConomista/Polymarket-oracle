# Guida all'Asta 2026-27 (fantacalcio) contro i dati di Serie A 2025-26 del repo

*Documento di confronto — 01/09/2026. Ogni numero viene da un comando eseguito; gli script
stanno in `/tmp/claude-0/-home-user-Polymarket-oracle/da53300b-a794-5cca-88c6-1408cb9fe921/scratchpad/`
(cartelle `verdetto_operativo_guida/`, `AV/`, `adv/`, `adv2/`, `confronto_squadre_allenatori/`, più
`DOC01_note_flag.py` e `DOC02_somma_titolarita.py`). Dove un verificatore avversariale ha smentito
un numero della prima analisi, qui c'è il valore del verificatore e la smentita è dichiarata.
Nessun file di dati è stato modificato.*

---

## 1. La risposta in dieci righe

1. Non sono due versioni della stessa cosa: sono **una misura** e **una previsione**.
2. Il repo ha, per la sola Serie A 2025-26, **11.894 righe giocatore-partita** con 114 colonne, 17.829 righe a tre fonti con 202 colonne, 2.280 righe squadra-partita-periodo con 235 colonne. Tutto **POST**: esiste perché le partite sono state giocate.
3. La guida ha **504 righe × 17 colonne** e **20 righe di squadra**, datate **18/08/2026 09:39**, sul campionato **2026-27**. Tutto **PRE**, e per lo più **giudizio umano**.
4. Le uniche due colonne della guida che sono misure — MV e FMV — misurano **la stagione che abbiamo già**, e in una scala che non possediamo: MV correla +0,72 col nostro rating (R² 0,54), FMV è **ricostruibile** dai nostri eventi con MAE 0,015 una volta data la MV.
5. Ciò che la guida aggiunge davvero sono **cinque colonne PRE che il repo non ha in nessuna forma**: Titolarità, Titolare XI, Ballottaggio, gerarchia dei piazzati, allenatore/modulo attesi.
6. Il campionato è cambiato: **17 club su 20** in comune, **9 allenatori su 20** confermati sullo stesso club, **7 allenatori su 20** non erano in Serie A 2025-26.
7. Il join non ha una chiave: la guida scrive il cognome, noi il nome intero in **tre convenzioni diverse**. Il tasso di aggancio è **fra il 70% e l'80% a seconda dell'implementazione** — non è una proprietà del dato.
8. Il rischio non è il buco, è l'aggancio **falso e sicuro di sé**: ne abbiamo **8 accertati**, tutti giocatori di neopromosse che condividono il cognome con un titolare vero.
9. La guida è **coerente al suo interno** in modo verificabile (504/504 con il listone ufficiale, ruolo 0/495 discorde, 11 titolari per squadra su 20/20) ma **non calibrata**: la somma delle sue Titolarità fa **249,79** dove gli undici in campo ne chiedono **220** (+13,5%).
10. Uso onesto: la guida è un **prior di stagione**, pre-registrabile e testabile in poche giornate. Non è una fonte di misure e non entra in nessun modello di pricing.

---

## 2. Le due grane

| | **LATO NUOVO — Guida all'Asta 2026-27** | **LATO REPO — Serie A 2025-26** |
|---|---|---|
| che cos'è una riga | un **giocatore in rosa a inizio stagione** (foglio Giocatori) | un **giocatore in una partita** (`giocatori_partita_diretta`, `giocatori_partita_tre_fonti`), o un **giocatore-squadra-stagione** (`giocatori_stagione_diretta`) |
| righe | **504** × 17 col. (non 505: header a riga 1; il foglio Info dichiara «Giocatori estratti 504») | 11.894 × 114 (diretta) · 17.829 × 202 a Livello=Partita (tre fonti) · **607** × 108 stagionali · 11.926 (Transfermarkt IT1) |
| altre grane | squadra 20×10 · ballottaggi 70×7 · piazzati 159×5 · note 155×5 · punti chiave 62×4 | squadra-partita-periodo 2.280 × 235 · partita 380 × 2.186 · tiro 18.754 righe · tocco Opta 562.672 · posizione 556.996 |
| soggetti coperti | 504 giocatori, 20 squadre, 20 allenatori | 584-774 giocatori (a seconda della fonte), 20 squadre, **30 mandati** di allenatore su 20 club |
| copertura | 100% del perimetro dichiarato; 100% di aggancio col listone ufficiale (`Tutti`+`Ceduti`) | 379/380 partite in diretta (manca `Serie A\|2025-12-27\|lecce\|como`), 380/380 nelle tre fonti, 758/758 squadre-partita con esattamente 11 titolari |
| **R8 — quando si sa** | **`pre`** al 18/08/2026: pubblicata prima del calcio d'inizio 2026-27 | **`post`**: gol, minuti, rating, xG esistono solo a partita finita. Fanno eccezione arbitro designato, quote, valore rosa |
| natura del dato | **previsione umana** su 11 colonne su 17; misura su 2 (MV, FMV); anagrafica su 3 | **misura** strumentale (SofaScore, Opta/WhoScored, Understat, Transfermarkt), più stime dichiarate col suffisso `_est` |
| stagione | 2026-27 (non ancora giocata) | 2025-26 (conclusa: classifiche a 38 partite) |
| chiave | `Id` ufficiale Lega Fantacalcio (504/504 via listone) | `match_uid`, `player_id` Transfermarkt, nome nelle tre convenzioni |

**La riga che conta.** Le due tabelle non hanno **nessuna riga in comune per costruzione**: una descrive
partite che sono successe, l'altra giocatori che non hanno ancora giocato. Confrontarle è legittimo solo
in due modi: come *validazione retrospettiva* della guida (quanto la sua previsione somiglia a ciò che
è successo l'anno prima) o come *feature pre-registrata* per il 2026-27. Sono due domande diverse e
hanno due disegni diversi (§6).

---

## 3. Cosa abbiamo noi, cosa aggiunge la guida — colonna per colonna

Verdetto: **RIDONDANTE** = già nel repo o già in un altro foglio del bundle · **DERIVABILE** = ricostruibile
dai nostri dati con errore misurato · **NUOVA** = informazione che il repo non ha in nessuna forma ·
**NUOVA-MA-PREVISIONE** = non l'abbiamo, ma non è una misura: è un giudizio del 18/08/2026.

### 3.1 Foglio `Giocatori` (504 × 17)

| colonna | riempimento | controparte nel repo (Serie A 25-26) | verdetto | numeri |
|---|---|---|---|---|
| `Squadra` | 504/504, 20 valori | `data/calendari_2026_27/originali/serie_a_2026-27.csv` (380 partite, stesse 20 squadre) | **RIDONDANTE** | 20/20 identiche |
| `Ruolo` (P/D/C/A) | 504/504 | Transfermarkt `position` (4) e `sub_position` (13); diretta 9 valori; tre fonti G/D/M/F | **RIDONDANTE** col listone, **DERIVABILE** dal repo | ruolo guida vs listone **0/495 discordi**; nessuna mappatura fra i 5 vocabolari esiste oggi nel repo |
| `Giocatore` | 504/504, 504 distinti | — | chiave, non dato | è il **cognome**; noi scriviamo il nome intero in 3 convenzioni |
| `Titolarità` | 504/504, **5 livelli** {0,01·0,25·0,50·0,75·0,95} | quota di partite da titolare 25-26 (`Da titolare`/38) | **NUOVA-MA-PREVISIONE** | rho +0,709 IC95 [+0,638,+0,769] col 25-26 (n=366); solo per chi resta nello stesso club rho +0,771; **per chi ha cambiato club rho +0,180 IC95 [−0,126,+0,471], nel rumore** |
| `MV` (media voto) | 504/504, **0 su 151 (30,0%)** = «nessun dato» | `Rating medio` diretta/SofaScore/WhoScored | **NUOVA come scala, RIDONDANTE come informazione** | r(MV, rating diretta) = **0,7244**, R² 0,525, residuo sd 0,155. Il 47% di varianza non è nostro: la scala fantavoto non si ricostruisce |
| `FMV` (fantamedia) | 504/504, 0 sulle **stesse** 151 righe | eventi diretta (gol, assist, cartellini, rigori, gol concessi) | **DERIVABILE** | ricostruendo FMV−MV col tariffario standard dai NOSTRI eventi: **r = 0,9983 · MAE 0,0153 · RMSE 0,0334** (n=337); il 92,3% entro 0,05. Delta medio per ruolo: A +0,60 · C +0,25 · D +0,06 · **P −1,00** |
| `PMA` (prezzo medio d'asta) | 485/504 (19 vuoti) | **niente**: nessuna colonna «fanta» in tutte e 90 le tabelle | **NUOVA** | corr con `Qt.A` del listone 0,827; con la quota da titolare 25-26 rho +0,444 |
| `Titolare XI` | **220 = 11 × 20** esatti | formazione titolare di ogni partita (`formazione_casa/trasferta` 380/380; `Stato` nelle tre fonti) | **NUOVA-MA-PREVISIONE** | ridondante col foglio Squadre: gli insiemi coincidono **20/20** (15 identici, 5 divergono solo per maiuscole) |
| `Rigorista` (1/2/3) | 59 | 106 rigori calciati da 57 giocatori distinti, 25-26 | **NUOVA-MA-PREVISIONE** | ricostruita esattamente dal foglio Piazzati 58/59. Il designato #1 coincide col nostro primo rigorista misurato in **9/17 club** (52,9%), in top-3 12/17 |
| `Punizioni` (1/2) | 40 | 96 battitori distinti di punizione, 25-26 | **NUOVA-MA-PREVISIONE** | Piazzati 40/40. Identità del #1: **4/17** (23,5%), in top-3 10/17 |
| `Corner` (1/2/3) | 60 | 3.367 corner attribuiti nominalmente, 429 battitori distinti | **NUOVA-MA-PREVISIONE** | Piazzati 60/60. Identità del #1: **4/17** (23,5%), in top-3 8/17 |
| `Ballottaggio` | 138 (= i 138 giocatori del foglio Ballottaggi) | **niente** | **NUOVA-MA-PREVISIONE** | la percentuale ha **4 soli valori distinti** (0,34 · 0,51 · 0,55 · 0,60) su 70 righe: è una scala ordinale, non una probabilità. 68/70 sommano a 1,00 |
| `Valorizzato` | 40 | — | **NUOVA-MA-PREVISIONE** | 40 = 40 distinti nel foglio Note |
| `Penalizzato` | 25 | — | **NUOVA-MA-PREVISIONE** | il foglio Note ne ha **28**: Lucumì (Bologna), Frattesi (Inter) e una riga senza nome non hanno il flag |
| `Nome nascosto` | 19 | — | **NUOVA-MA-PREVISIONE** | il foglio Note ne ha 20 (manca il flag a Kristensen T., Udinese) |
| `Giovane` | 19 | data di nascita (100% su 585 giocatori Transfermarkt) | **NUOVA-MA-PREVISIONE**, e **non è l'età** | i 13 agganciati con età hanno **19-25 anni**; ci sono **161** giocatori non marcati con ≤25 anni. È una selezione editoriale |
| `Note guida` | 103 | — | **NUOVA** (testo libero) | ricostruibile dal foglio Note solo per **59/103** |

### 3.2 Foglio `Squadre` (20 × 10)

| colonna | controparte nel repo | verdetto | numeri |
|---|---|---|---|
| `Modulo` (5 valori) | modulo di **ogni partita** da due fonti indipendenti (accordo 759/760 dopo normalizzazione) | **NUOVA-MA-PREVISIONE** | coincide col modulo più usato 25-26 in **4/17** (23,5%) |
| `Allenatore` (20) | 30 mandati verificati contro Wikidata (31/31) | **NUOVA-MA-PREVISIONE** | 13/20 erano in Serie A 25-26, **9/20** sullo stesso club |
| `Attacco (0-5)` | gol fatti 25-26 | **DERIVABILE** | r = **+0,880** (Spearman +0,941), R² 0,774, n=17 |
| `Difesa (0-5)` | gol subiti 25-26 | **DERIVABILE** | r = **−0,935** (Spearman −0,899), R² 0,874, n=17 |
| `N. giocatori` | — | **RIDONDANTE** | somma 504 = righe del foglio Giocatori, 0 discordanze su 20 |
| `Titolari 95%` | — | **FINTO PIENO (R6)** | vale **0 su tutte e 20** le righe, varianza zero, mentre i giocatori a 0,95 sono **95** (media 4,75 per squadra). Il verificatore del taglio-join ha letto la cella: contiene `=_xlfn.COUNTIFS(...)`, una formula non valutabile, con 0 in cache |
| `XI titolare` (stringa) | — | **RIDONDANTE** | ricostruisce i flag `Titolare XI` in **20/20** squadre |
| `Punti chiave` | — | **RIDONDANTE** | è la concatenazione esatta del foglio PuntiChiave in **20/20** |
| `Ruoli chiave (schema)` | — | **RIDONDANTE** | è **funzione deterministica del Modulo**: 5 moduli → 5 schemi, uno a uno |

### 3.3 Listone ufficiale (accessorio, 507 + 17 righe)

| colonna | verdetto | numeri |
|---|---|---|
| `Id` | **NUOVA — è la chiave** | 507 distinti; copre **504/504** righe della guida |
| `R` / `RM` (Mantra) | RIDONDANTE / **NUOVA** | `R` 0/495 discorde con la guida; `RM` ha **24** valori (vocabolario Mantra, non nostro) |
| `Qt.A`, `Qt.I` | **NUOVA** | identiche su **507/507**: l'asta non è iniziata, sono un duplicato algoritmico *oggi* |
| `Diff.`, `Diff.M` | **FINTO PIENO (R6)** | 0 su 507/507, le uniche due colonne a varianza zero |
| `FVM`, `FVM M` | **NUOVA** | range 1-370 |

**La lezione della tabella.** Su 17 colonne del foglio Giocatori: **2 ridondanti**, **1 derivabile con errore
misurato** (FMV), **1 misura in scala nostra non ricostruibile** (MV), **11 previsioni umane**, 2 chiavi.
Il valore della guida **non sta nei numeri che assomigliano a statistiche**: sta nelle undici colonne che
sono opinioni, perché sono opinioni *disponibili prima*.

---

## 4. Squadre e allenatori: 2025-26 → 2026-27

### 4.1 La tabella

| club 26-27 | in A 25-26? | allenatore guida 26-27 | ultimo allenatore 25-26 (nostro) | stesso? | modulo guida | modulo più usato 25-26 (quota) | moduli distinti 25-26 | Att. | Dif. | GF | GS |
|---|---|---|---|---|---|---|--:|--:|--:|--:|--:|
| Atalanta | sì | M. Sarri | Raffaele Palladino | **no** | 4-3-3 | 3-4-2-1 (89%) | 3 | 4,0 | 4,0 | 51 | 36 |
| Bologna | sì | **D. Tedesco** | Vincenzo Italiano | **no** | 4-3-3 | 4-2-3-1 (71%) | 4 | 4,0 | 3,5 | 49 | 46 |
| Cagliari | sì | F. Pisacane | Fabio Pisacane | sì | 4-3-3 | 3-5-2 (47%) | **11** | 2,5 | 2,5 | 40 | 53 |
| Como | sì | C. Fabregas | Cesc Fàbregas | sì | 4-2-3-1 | 4-2-3-1 (89%) | 4 | 5,0 | 4,5 | 65 | 29 |
| Fiorentina | sì | F. Grosso | Paolo Vanoli | **no** | 4-3-2-1 | 4-3-3 (39%) | 10 | 3,0 | 3,0 | 41 | 50 |
| **Frosinone** | **no** | **M. Alvini** | — | — | 4-3-3 | — | — | 2,5 | 2,0 | — | — |
| Genoa | sì | D. De Rossi | Daniele De Rossi | sì | 3-4-2-1 | 3-5-2 (47%) | 7 | 3,0 | 3,0 | 41 | 51 |
| Inter | sì | C. Chivu | Cristian Chivu | sì | 3-5-2 | 3-5-2 (**100%**) | **1** | 5,0 | 5,0 | 89 | 35 |
| Juventus | sì | L. Spalletti | Luciano Spalletti | sì | 4-2-3-1 | 3-4-2-1 (63%) | 7 | 4,5 | 4,5 | 61 | 34 |
| Lazio | sì | **G. Gattuso** | Maurizio Sarri | **no** | 4-3-3 | 4-3-3 (95%) | 2 | 3,5 | 4,0 | 41 | 40 |
| Lecce | sì | E. Di Francesco | Eusebio Di Francesco | sì | 4-3-3 | 4-2-3-1 (58%) | 4 | 2,0 | 2,5 | 28 | 50 |
| Milan | sì | **R. Amorim** | Massimiliano Allegri | **no** | 3-4-2-1 | 3-5-2 (89%) | 4 | 4,5 | 4,5 | 53 | 35 |
| **Monza** | **no** | I. Jurić *(era all'Atalanta)* | — | — | 3-4-2-1 | — | — | 2,0 | 2,0 | — | — |
| Napoli | sì | M. Allegri *(era al Milan)* | Antonio Conte | **no** | 4-3-3 | 3-4-2-1 (55%) | 4 | 4,5 | 4,5 | 58 | 36 |
| Parma | sì | C. Cuesta | Carlos Cuesta | sì | 4-3-3 | 3-5-2 (50%) | 9 | 2,0 | 2,5 | 28 | 46 |
| Roma | sì | G. Piero Gasperini | Gian Piero Gasperini | sì | 3-4-2-1 | 3-4-2-1 (79%) | 4 | 4,5 | 5,0 | 59 | 31 |
| Sassuolo | sì | **A. Aquilani** | Fabio Grosso | **no** | 4-2-3-1 | 4-3-3 (95%) | 3 | 3,0 | 2,5 | 46 | 50 |
| Torino | sì | **I. Abate** | Roberto D'Aversa | **no** | 3-4-2-1 | 3-5-2 (42%) | 8 | 2,5 | 2,0 | 44 | 63 |
| Udinese | sì | K. Runjaic | Kosta Runjaić | sì | 3-4-2-1 | 3-5-2 (50%) | 9 | 3,0 | 3,0 | 45 | 48 |
| **Venezia** | **no** | **G. Stroppa** | — | — | 3-5-2 | — | — | 2,5 | 2,0 | — | — |

**Escono** Cremonese, Pisa, Verona (18ª, 20ª, 19ª nella nostra `classifiche.csv.gz`); **entrano** Frosinone,
Monza, Venezia. **17/20 club in comune.**

**Allenatori (misurato).** 13/20 erano in Serie A 25-26; **9/20 sono confermati sullo stesso club**;
**11/20 sono abbinamenti nuovi**. I sette nomi che il nostro 2025-26 di Serie A non contiene: Tedesco,
Alvini, Gattuso, Amorim, Aquilani, Abate, Stroppa.

**Moduli (misurato).** Il modulo dichiarato dalla guida coincide col modulo più usato nel 25-26 in
**4/17 = 23,5%** (Como, Inter, Lazio, Roma). Ma il confronto è debole in partenza: nel 25-26 il modulo
più usato copre in media **67,6%** delle partite di quella squadra e ogni squadra ne ha usati **5,6 in
media** (Inter 1, Cagliari 11). Un solo modulo per stagione è una semplificazione che i nostri dati
smentiscono per 19 squadre su 20.

### 4.2 Controllo di realtà: dati veri o sintetici?

**Verdetto: dati veri.** Cinque prove indipendenti, tutte misurate:

| prova | risultato | perché è una prova |
|---|---|---|
| FMV ricostruita dai NOSTRI eventi 25-26 | **r = 0,9983 · MAE 0,0153** (n=337) | un file generato a caso non riproduce il tariffario bonus/malus applicato ai gol e agli assist veri |
| Attacco/Difesa in stelle contro i gol veri | r = **+0,880** / **−0,935** (n=17) | le stelle seguono la stagione realmente giocata |
| MV = 0 ⇔ mai visto in Serie A 25-26 | tabella 2×2: agganciati 366 (di cui MV=0 solo 14) · non agganciati 136 (di cui MV=0 **135**, 99,3%) | la colonna «nessun dato» sa davvero chi non ha giocato |
| rose della guida contro `rosa_wikipedia.json` 2026-27 del repo (15 club validi) | **316/368 = 85,9%** agganciati; concordanza di ruolo **291/316 = 92,1%**, le 25 divergenze sono tutte C↔A (20) e D↔C (5) | due fonti indipendenti descrivono le stesse rose post-mercato |
| coerenza col listone ufficiale | **504/504** agganciati, ruolo **0/495** discorde, squadra **0** discorde, `N. giocatori` somma 504, `Titolare XI` esattamente 11 per **20/20** squadre | il file è allineato all'anagrafica ufficiale della Lega |

**Ma tre difetti reali, misurati:**
- `Titolari 95%` = 0 su 20 (formula rotta) e `Diff.`/`Diff.M` = 0 su 507 nel listone: **finti pieni** (R6);
- lo **stesso file** scrive lo stesso giocatore in due modi: `McKennie`/`Mckennie`, `McTominay`/`Mctominay`, `N'Dri`/`N'dri`, `Esposito F.P.`/`Esposito F.p.`;
- il foglio `Note` marca 5 giocatori che il foglio `Giocatori` non marca (3 Penalizzati, 1 Nome nascosto, 2 Giovani — con un giocatore in comune fra le liste).

**E un difetto di calibrazione, che è il reperto più importante del lato guida e non ha richiesto
nessun join** (`DOC02_somma_titolarita.py`):

> La somma delle Titolarità delle 504 righe fa **249,79**. Gli undici in campo per 20 squadre ne chiedono **220**.
> **Eccesso +29,79 = +13,5%.** **18 squadre su 20** dichiarano più di 11 titolari attesi (min Bologna 10,20, max Milan 14,34).
> I **portieri** sono invece calibrati quasi esattamente: **19,86 su 20**. L'eccesso sta tutto nei giocatori di movimento (229,93 contro 200, +15,0%).

Lo stesso segno esce dal confronto col 25-26: le classi alte sono **sovra-dichiarate** (classe 0,75 →
quota vera media 0,541, scarto **+0,209**; classe 0,95 → 0,760, scarto **+0,190**) e la classe più bassa è
**sotto-dichiarata** (0,01 → 0,121, scarto −0,111). Due misure indipendenti, stessa direzione.

---

## 5. Il join: si agganciano?

### 5.1 Dentro il bundle il problema non esiste

| criterio | agganciati |
|---|---|
| guida → listone `Tutti`, nome normalizzato | 502/504 = 99,6% |
| guida → listone `Tutti` + **`Ceduti`** | **504/504 = 100,0%** |
| duplicati di chiave (per lato) | 0 e 0 |
| squadra discorde | 0 · ruolo discorde 0/495 |
| righe del listone assenti dalla guida | 5 (Vicario, Montipò, Favasuli, Mora, De Martis) + 15 dei 17 Ceduti |

**L'`Id` ufficiale è quindi disponibile per tutti e 504.** Attenzione: l'aggancio *senza* normalizzazione
ne perde 9-12 per sole maiuscole (`Ederson D.S.`/`Ederson D.s.`, `McKennie`/`Mckennie`).

### 5.2 Verso il repo: il tasso dipende dall'implementazione, non dal dato

Cinque implementazioni indipendenti dello stesso join hanno dato:

| implementazione | agganciati | % |
|---|--:|--:|
| analisi del taglio-join (cognome + squadra, classi A+B) | 379/504 | 75,2% |
| verificatore del taglio-join (indice unione, union-find sulle identità) | **402/504** | **79,8%** |
| taglio-verdetto (indice a suffissi, rifiuto degli ambigui) | 353/504 | 70,0% |
| verificatore, join corretto senza fallback sull'iniziale | 358/504 | 71,0% |
| verificatore, join aggiudicato a mano | **360/504** | **71,4%** (0 ambigui) |

⚠️ **Il 75,2% dell'analisi è stato smentito**: il verificatore, con criteri dichiarati identici, ha
ottenuto 79,8%. La conclusione onesta non è «è 75» né «è 80»: è che **il tasso misura quanto è
aggressiva la fusione delle identità, non quanto i due dataset si sovrappongono**. La banda vera è
**70-80%**, e il numero da citare è sempre accompagnato dal metodo.

### 5.3 Il validatore indipendente: la colonna MV

La guida dichiara MV = 0 quando non ha dati della scorsa Serie A. È un **tripwire** che non dipende dal
nostro matcher:

| | non agganciato | agganciato |
|---|--:|--:|
| **MV = 0** (mai giocato in A 25-26) | 137 | 14 |
| **MV > 0** (ha giocato in A 25-26) | **1** | **352** |

**352/353 = 99,7%**: dove la guida dice che il giocatore c'era, noi lo troviamo. L'unico buco è
**`Zambo Anguissa`**, che il repo scrive `Frank Anguissa`: nessuna regola di stringa lo recupera,
serve un alias.

### 5.4 Cosa si perde

- **144-146 righe senza aggancio alla Serie A 25-26.** Di queste, **61 sono delle tre neopromosse**: il repo **non copre la Serie B 2025-26**, è un buco **strutturale**, non un difetto del join.
- Delle 136 assenti censite dal verificatore: **26** hanno un candidato unico in una delle altre 4 leghe del repo (Spence→Tottenham, Akpoguma→Hoffenheim, Mastantuono→Real Madrid…), **7** ne hanno più di uno (ambigui), **25** compaiono solo nell'anagrafica Transfermarkt, **78 sono invisibili su entrambi i canali**.
- Copertura allargando alle altre 4 leghe: **399/504 = 79,2%**. Tetto teorico (il cognome esiste da qualche parte fra i 14.558 nomi del repo): **458/504 = 90,9%** — ma è un tetto per **cognome**, cioè per definizione pieno di falsi.

### 5.5 ⚠️ Gli agganci pericolosi — elenco esplicito

**A · Gli 8 falsi accertati.** Univoci, sicuri di sé, sbagliati. Tutti hanno MV=0 e giocano in una neopromossa:

| riga guida | squadra 26-27 | si aggancia (falsamente) a | come si smaschera |
|---|---|---|---|
| `Adams A.` | Venezia | Ché Adams (Torino) | collide con `Adams C.` [Torino] |
| `Rrahmani Al.` | Venezia | Amir Rrahmani (Napoli) | collide con `Rrahmani` [Napoli] |
| `Stankovic F.` | Venezia | Aleksandar Stanković (Inter) | collide con `Stankovic A.` [Inter] |
| `Colombo L.` | Monza | Lorenzo Colombo (Genoa) | collide con `Colombo` [Genoa]; **l'iniziale coincide**: è il più insidioso |
| `Pessina` | Monza | Massimo Pessina (Bologna) | collide con `Pessina Mas.` [Bologna] |
| `El Azzouzi A.` | Frosinone | Oussama El Azzouzi (Bologna) | collide con `El Azzouzi O.` [Bologna] |
| `Moreno M.` | Venezia | Alberto Moreno (Como) | iniziale `M.` ≠ Alberto |
| `Perez K.` | Venezia | Matías Pérez (Lecce) | iniziale `K.` ≠ Matías |

**Il tripwire che li prende tutti:** un giocatore con MV=0 (la guida dice «non ha dati di Serie A»)
non può essere agganciato a chi in Serie A ha giocato mezza stagione. Cercando le contraddizioni,
il verificatore ne ha isolati 6 con ≥5 presenze — Colombo L. (38 presenze!), Adams A. (33),
Tourè E. (32), Marin R. (23), Rrahmani Al. (21), Moreno M. (18) — e dopo l'aggiudicazione a mano
**il residuo del tripwire è 0**.

**B · Le ambiguità che la squadra non risolve (≥2 candidati nello stesso club): almeno 12.**
`Martinez Jo.`/`Martinez L.` (Inter), `Sulemana I.`/`Sulemana K.` (Atalanta), `Oyono A.`/`Oyono J.`
(Frosinone), `Gelli J.`/`Gelli F.` (Frosinone), `Russo A.` (Sassuolo: Flavio e Alessandro),
`Terracciano` (Milan: Pietro e Filippo). ⚠️ La prima analisi ne contava 9 e ne perdeva 3 che erano
nella sua stessa tabella dei cognomi ambigui.

**C · Sei «ambiguità» che sono nostre, non della guida.** Lo stesso giocatore scritto in due modi nelle
nostre fonti: `Manu Koné`/`Kouadio Kone` (Roma), `Khéphren`/`Kephren Thuram` (Juventus),
`Michel Adopo`/`Ndary Adopo` (Cagliari), `Anastasios`/`Tasos Douvikas` (Como),
`Abdoulaye`/`Niakhate Ndiaye` (Parma), `Tino`/`Faustino Anjorin` (Torino). È un problema di identità
del repo, esiste anche senza il fantacalcio.

**D · Due trappole di metodo, pagate durante il lavoro.**
1. **Restringere il perimetro peggiora le cose.** Con un indice limitato a «chi ha giocato» (585 Transfermarkt IT1), `Marin R.` (Napoli) finisce su Marius Marin del Pisa e `Tourè E.` (Parma) su Idrissa Touré del Pisa: i veri (Rafa Marín, El Bilal Touré) esistono **solo al livello `Rosa`** delle tre fonti. Togliere il candidato giusto lascia solo quello sbagliato.
2. **NFKD non basta.** Non scompone ø, ł, đ, ı: `Hojlund` non aggancia `Højlund`. E l'apostrofo va **rimosso**, non sostituito con uno spazio (`N'Dicka` → `ndicka`). È la stessa famiglia di difetti di `Fürth`/`Fuerth` e `Deportivo de A Coruña`/`La Coruna` già pagata dal progetto.

---

## 6. Che cosa ci si può onestamente fare — e cosa no

### 6.1 Si può

**(a) Usare la guida come PRIOR PRE-REGISTRATO di titolarità e di formazione.** È l'unica cosa che il
repo non ha e non può fabbricare: una previsione **datata prima** del calcio d'inizio. Il CLAUDE.md §6
dice che l'unica leva non ancora esaurita è «informazione DAVVERO nuova (formazioni ufficiali
pre-partita)»: la guida non è la formazione ufficiale — quella arriva un'ora prima — ma è un prior di
stagione, e costa zero perché è già sul disco.

**(b) Testare la sua calibrazione.** Vedi §6.3: si chiude in poche giornate, con potenza misurata.

**(c) Prendere l'`Id` ufficiale come chiave.** 504/504. Se la Lega mantiene gli Id stabili fra stagioni
(**non verificato**, servirebbe un listone di un'altra annata), la tabella di alias `Id fanta → player_id`
si scrive una volta sola.

**(d) Usare Ballottaggio, gerarchia dei piazzati e XI atteso come feature qualitative** su un perimetro
dichiarato (i ~360 agganciati sicuri), sapendo che sono giudizi.

### 6.2 Non si può

- **Usare MV/FMV come dati nuovi.** MV misura il 25-26 che già misuriamo meglio; FMV è ricostruibile dai nostri eventi con MAE 0,015. Aggiungere una colonna che sappiamo già ricalcolare non è informazione, è ridondanza con rumore in più.
- **Usare `Attacco`/`Difesa` come segnale di squadra.** R² 0,77 e 0,87 contro i gol 25-26: è la nostra stessa stagione, arrotondata a mezze stelle.
- **Portare la guida dentro il pricing 1X2 / O-U.** Non esiste nel progetto nessun canale misurato che porti dalla titolarità di un giocatore alla probabilità di un esito; costruirlo è una pista aperta (§8), non un uso.
- **Fare medie su MV o FMV senza filtrare gli zeri.** 151 righe su 504 (30,0%) valgono 0 = «non lo so», e i valori veri stanno fra 5,50 e 7,50: la media grezza è 4,19 contro 5,98. Errore del 30% garantito.
- **Toccare i 61 giocatori delle tre neopromosse.** Il repo non ha la Serie B 25-26: per loro non esiste un confronto, esiste solo la guida.
- **Fidarsi di un fuzzy match.** Otto falsi accertati su ~500, tutti univoci e tutti sicuri di sé.

### 6.3 Il disegno del test di calibrazione (e la sua potenza)

**Bersaglio.** Per ogni classe *c* ∈ {0,01 · 0,25 · 0,50 · 0,75 · 0,95} della colonna `Titolarità`, il tasso
vero di partite da titolare nel 2026-27. Ipotesi nulla: il tasso vero è *c*.

**Unità e dipendenza — la parte che si sbaglia.** L'osservazione è giocatore × giornata, ma l'unità
**indipendente è il giocatore**: sui dati veri 25-26 l'ICC fra giornate dentro lo stesso giocatore è
**0,320** e l'autocorrelazione lag-1 è **+0,57** (infortuni e squalifiche fanno serie). Il design effect a
K=38 vale **12,84**: **le 38 giornate valgono 2,96 osservazioni indipendenti per giocatore.** Un IC che
tratta le giornate come indipendenti è falso e stretto.

**Potenza** (test binomiale esatto, α=0,05 a due code, classe 0,95 che ha 95 righe nella guida,
n_eff = 95·K/(1+(K−1)·0,320)):

| K giornate | n_eff | potenza per uno scarto 0,15 | 0,10 | 0,05 |
|--:|--:|--:|--:|--:|
| 1 | 95 | 99,5% | **91,9%** | 48,2% |
| 3 | 174 | 100% | **99,6%** | 76,3% |
| 5 | 208 | 100% | 99,8% | 77,3% |
| 10 | 245 | 100% | 100% | **85,8%** |

Semiampiezza dell'IC95 sulla classe 0,95, misurata col bootstrap a cluster sui giocatori sulle giornate
vere: **±0,138 a K=1 · ±0,080 a K=3 · ±0,070 a K=5 · ±0,057 a K=10 · ±0,045 a K=38**.
⚠️ **La prima analisi dichiarava ±0,021 a K=38: è aritmeticamente incompatibile col suo stesso design
effect** (per ottenerlo servirebbe deff 2,27, non 13,5). Il valore da usare è ±0,045.

**Che cosa ci aspettiamo (predizione, da scrivere prima).** Dal proxy sul 25-26 e dalla somma interna:
scarto **+0,19** sulla classe 0,95, **+0,21** sulla 0,75, **−0,11** sulla 0,01, ed eccesso complessivo
**+13,5%**. Con Δ=0,19 la potenza è **~100% già alla prima giornata**: se la guida è mal calibrata come
sembra, **una giornata basta**. È il contrario del test prospettico sull'1X2 (Fase 78), dove una giornata
su 3 leghe vale il 9,8% di potenza — perché qui l'unità è il giocatore, non la partita, e ce ne sono 504.

**Baseline obbligatorie** (misurate sul 25-26, altrimenti non si sa contro cosa si vince):
- tasso di base per squadra 11/|rosa|: Brier **0,2428**;
- quota da titolare della stagione precedente del singolo giocatore;
- **XI della giornata precedente: 8,31/11 azzeccati = 75,6%** — è l'avversario vero, e batte l'oracolo di fine stagione (7,84/11 = 71,3%) e i più usati fino a ieri (7,47/11 = 67,9%).

⚠️ **Un tetto, non una promessa.** Applicando la griglia a 5 livelli alla quota *vera* (cioè con
look-ahead) si ottiene Brier 0,1662 contro 0,2428 della baseline-squadra, ΔBrier **−0,0766**
IC95 [−0,0852, −0,0679]. **Non è una misura della guida**: è il massimo che quella griglia potrebbe
valere se fosse perfettamente calibrata. La guida vera starà sotto.

**Protocollo (R8).** Congelare guida e listone in `data/` con sha256 e un commit **datato prima della
prima giornata**; la previsione è il file, non una sua rielaborazione. Scorare a K = 1, 3, 5, 10, 19, 38.
Perimetro dichiarato: le 504 righe, non i ~360 agganciati (l'aggancio serve alle baseline, non al test).

---

## 7. Reperti da non perdere

### Bloccanti

1. **Tre file di rosa 2026-27 del repo contengono la rosa di un altro club.** `cagliari-calcio` e `frosinone-calcio` hanno i **33 nomi del Milan** (`voce = "Associazione Calcio Milan 2026-2027"`), `udinese-calcio` ha i **47 del Napoli**. 3 file su 18 = 16,7%; `genoa-cfc` e `venezia-fc` non ce l'hanno affatto. Sono file pieni, ben formati e con la fonte dichiarata: **nessun conteggio di celle li vede**. Riparazione via script + registro R3, mai a mano.
2. **Gli 8 agganci falsi** dell'elenco §5.5-A. Un fuzzy match li accetta tutti.
3. **La guida non è calibrata: somma 249,79 contro 220** (+13,5%), 18/20 squadre sopra 11, portieri esatti (19,86/20). Chi legge `Titolarità` come una probabilità sta leggendo un ordinamento.
4. **MV = 0 su 151 righe (30,0%) significa «non lo so», non «zero».** Stessa cosa per FMV, sulle stesse righe. È dichiarato nella legenda del foglio Info.
5. **La colonna unificata `allenatore_casa`/`allenatore_trasferta` del repo è chi *sedeva in panchina*, non il tecnico.** Segue SofaScore 380/380 per lato; WhoScored/Transfermarkt concordano fra loro 759/760. Conseguenza misurata: **46 nomi distinti invece di 30**. ⚠️ La prima analisi diceva «39 contro 29»: **valori sbagliati**, il verificatore ha misurato 46 e 30. E la spiegazione «sono tutti vice per squalifica» è una **deduzione mai misurata**, falsa in almeno 1 caso su 24 (Sassuolo-Genoa 03/11/2025: Vieira non era squalificato, era stato esonerato cinque giorni prima).

### Da sapere

6. **`Titolari 95%` (guida) e `Diff.`/`Diff.M` (listone) sono finti pieni** (R6): 0 su 20 e 0 su 507. La prima è una formula `_xlfn` non valutabile con 0 in cache; le seconde sono zero perché l'asta non è iniziata. Da raccogliere lo stesso: `Qt.A`/`Qt.I` divergeranno a stagione avviata (§5-ter).
7. **`tiri.csv.gz` conta i tiri due volte.** Le 18.754 righe di Serie A sono 9.381 SofaScore + 9.373 Understat sulle stesse 380 partite. ⚠️ La prima analisi le chiamava «18.754 tiri»: chi somma l'xG senza filtrare `Fonte` **raddoppia gli expected goals**. E l'xGOT è pieno solo al **49,9%**.
8. **Cinque colonne dichiarate «vuote in tutta la Serie A» sono vuote solo al Livello=Partita.** ⚠️ Rettifica del verificatore: `Valore di mercato (SofaScore)` ha 682 valori ai livelli Rosa/Stagione, `Piede` 702, `Contratto fino al` 645, `npxG` 586. L'unica davvero vuota è `Motivo assenza (SofaScore)` (0/19.126). E a Livello=Partita le colonne vuote sono **12**, non 5.
9. **`classifiche.csv.gz`: `Partite giocate` = 38 solo nelle righe `Generale`**, 19 in `Casa` e `Trasferta`. ⚠️ Rettifica del verificatore; la sostanza (classifica finale = look-ahead) resta.
10. **La guida si contraddice al suo interno in 5 casi**: Lucumì, Frattesi e una riga senza nome sono «Penalizzato» nelle Note e non nel flag; Kristensen T. «Nome nascosto»; Dominguez B. ed Esposito F.P. «Giovane». Più 4 nomi scritti in due modi nello stesso file.
11. **`Giovane` non è l'età.** I 13 agganciati hanno 19-25 anni, e **161** giocatori non marcati hanno ≤25 anni.
12. **La `Titolarità` non trasferisce fra club.** Per chi resta nello stesso club rho +0,771 IC95 [+0,709, +0,822]; per i 49 che hanno cambiato club rho **+0,180 IC95 [−0,126, +0,471]**: nel rumore. Chi cambia squadra va trattato come un giocatore nuovo.
13. **La gerarchia dei piazzati è poco persistente.** Il #1 designato per il 26-27 coincide col nostro primo battitore misurato nel 25-26 in **9/17** club sui rigori, **4/17** sulle punizioni, **4/17** sui corner. È il motivo per cui il dato ha valore (non è copiato dall'anno prima) ed è anche il motivo per cui non ci si può contare.
14. **`formazioni_diretta`, `cambi_diretta`, `eventi_diretta` non coprono la Serie A** (0 righe: solo Bundesliga e Ligue 1). La formazione titolare di Serie A si prende da `partite.csv.gz` (`formazione_casa/trasferta`, 380/380) o dallo `Stato` delle tre fonti.
15. **`transfermarkt_appearances.red_cards` è muta in Serie A 25-26**: somma 0 su 11.926 presenze, contro i 66 rossi che diretta conta. E `transfermarkt_clubs.coach_name` è la trappola R8 (dà Vieira, Pioli, Tudor, Jurić: quattro esonerati).

### Curiosità

16. Il repo sa **chi era in panchina e non è entrato**: 774 convocati contro 587 scesi in campo, 23,5 convocati in media per squadra-partita. Nessuna guida ha questa informazione.
17. Il nostro predittore `pre` più stupido — «quota di partite da titolare fino a ieri» — azzecca il **77,4%** delle titolarità contro il 52,4% della classe maggioritaria, su 17.055/17.829 righe. È la baseline che la guida deve battere per valere qualcosa.
18. **Fini** compare nel listone con uno spazio in coda (`'Fini '`): un join esatto senza `strip()` lo perde.

---

## 8. Domande aperte — decisioni che spettano all'utente

1. **Quale delle tre domande vogliamo rispondere?** (a) la guida concorda col 25-26 (validazione retrospettiva, si fa oggi, non dice niente sul 26-27); (b) la guida aggiunge qualcosa che non abbiamo (risposta già data: cinque colonne PRE); (c) la guida come **feature pre-registrata** per il 26-27 (l'unico uso che rispetta R8, e va congelata **adesso**, prima della prima giornata). Sono lavori diversi.
2. **La tabella di alias la scriviamo, e chi la firma?** Servono ~20-26 righe (12 ambigui nello stesso club, 5 ambigui senza candidato, 8 falsi da marcare «nessun aggancio», 1 alias vero: Zambo Anguissa → Frank Anguissa). R3 dice che ogni correzione ha un registro con chi ha deciso e quando: una tabella di alias è una correzione a tutti gli effetti.
3. **Chiave `Id` fanta o `player_id` Transfermarkt?** L'`Id` copre 504/504 ma **non sappiamo se è stabile fra stagioni** (servirebbe un listone di un'altra annata: non l'abbiamo). Se è stabile, il ponte si scrive una volta; se no, va rifatto ogni agosto.
4. **Ripariamo i tre `rosa_wikipedia.json` sbagliati?** È un difetto accertato e riprodotto. La riparazione va fatta con uno script che ri-scarica dalla voce giusta e verifica il valore-prima (R3), più una riga in `data/correzioni_dichiarate.csv`. E va deciso cosa fare di Genoa e Venezia, che il file non ce l'hanno.
5. **Raccogliamo il listone a più date?** Oggi `Qt.A` e `Qt.I` sono identiche su 507/507 (fotografia pre-asta) e `Diff.` è zero. La traiettoria delle quotazioni durante la stagione **non si recupera dopo** (§5-ter). Se la vogliamo, si decide ora.
6. **Vale la pena costruire il ponte titolarità → esito?** Oggi nel progetto non esiste nessun canale misurato che porti da «chi gioca» a «come finisce». È una pista nuova e costosa; senza di essa la guida resta un dato di fantacalcio, non un dato di pricing.
7. **Serve la mappatura fra i cinque vocabolari di ruolo?** Il repo ne ha già quattro (diretta 9 valori, tre fonti G/D/M/F, Transfermarkt `position` 4 + `sub_position` 13, Wikipedia P/D/C/A); la guida porta il quinto e il listone il sesto (`RM` Mantra, 24 valori). Nessuna mappatura esiste oggi.
8. **Il perimetro 2026-27 va verificato contro una fonte esterna?** Guida, listone e nostro calendario concordano sulle stesse 20 squadre — ma sono tre file che potrebbero derivare dalla stessa fonte. La verifica delle promozioni dalla Serie B non è mai stata fatta, e il repo non copre la Serie B 25-26.
