# Report 1 — Audit dei dati: gli snapshot sono giusti?

**Data:** 24 luglio 2026 · **Branch:** `claude/verify-data-import-leagues-468euv`
**Domanda posta:** *«mi serve essere sicuro che i dati sono tutti giusti e che non
abbiamo alcun dato sbagliato»* — con la richiesta esplicita di **cercare di
dimostrare il contrario**, non di confermare.

**Verdetto in una riga:** i dati **corrispondono alla fonte, riga per riga, su
tutte e 5 le leghe** (0 differenze su gol, date, tiri, 10 colonne quota, 8
colonne xG); l'audit avversariale ha però trovato **7 anomalie reali**, tutte
*nella fonte* (non nella pipeline), tutte identificate una per una e quantificate:
2 richiedono un intervento, 5 vanno dichiarate.

---

## 1 · Il fatto nuovo che ha reso possibile l'audit forte

`docs/MANUALE_SOPRAVVIVENZA.md` §1 elenca `football-data.co.uk` e `understat.com`
tra gli **host BLOCCATI** dal proxy (403). **Oggi rispondono 200** — verificato
scaricando 45 CSV e 45 JSON. Anche `data.jsdelivr.com`, `betexplorer.com` e
`oddsportal.com` (mai testati da questa sessione) sono raggiungibili.

Conseguenza metodologica: per la prima volta si può fare **il controllo che
conta davvero** — non «lo snapshot è internamente coerente?» ma «lo snapshot
**corrisponde alla fonte-madre**?».

> ⚠️ Understat ha cambiato struttura: la pagina di lega non contiene più
> `var datesData`. I dati stanno dietro `GET /getLeagueData/{Lega}/{anno}` con
> header `X-Requested-With: XMLHttpRequest` (senza header: 404). Il JSON
> restituito ha esattamente lo schema `{teams, players, dates}` che
> `src/data/understat.parse_season_xg` già sa leggere.

## 2 · Metodo (4 livelli, dal più debole al più forte)

| livello | cosa verifica | script |
|---|---|---|
| **A. interno** | schema, duplicati, girone all'italiana, range, copertura, coerenza gol↔risultato, overround, nomi squadra | `audit_snapshots.py` |
| **B. esterno** | confronto **riga per riga** con football-data ri-scaricato oggi; le 10 colonne quota **ri-derivate** con il codice di produzione (`loader._odds_from_raw`) | idem |
| **C. indipendente** | i **gol secondo Understat** (fonte terza) contro quelli dello snapshot | idem |
| **D. avversariale** | «e se la fonte fosse sbagliata?»: margini impossibili, incoerenza 1X2↔O/U, fisica (gol > tiri in porta), impronte-quota duplicate, riposo, xG impossibile | `audit_anomalie.py` |

Provenienza tracciata: `cantiere/data/fonti/manifest.json` registra URL,
timestamp UTC, byte e **SHA256** di ognuno dei 90 file scaricati.

## 3 · Esito dei controlli

23 controlli × 5 leghe. Riassunto (dettaglio in `cantiere/out/audit_*.json`):

| lega | FAIL | WARN | note |
|---|--:|--:|---|
| serie_a | 0 | 1 | data discordante Udinese-Roma (§4.2) |
| premier_league | 1 | 0 | ordine colonne (§4.6) |
| la_liga | 1 | 0 | ordine colonne (§4.6) |
| bundesliga | 1 | 0 | risultato assegnato Union-Bochum (§4.3) |
| ligue_1 | 0 | 2 | xG mancante + date discordanti (§4.7) |

**I controlli che contano sono tutti verdi, su tutte e 5 le leghe:**

```
B1 stesse partite ............ 0 differenze  (15.788 partite)
B2 gol e tiri in porta ....... 0 differenze
B3 date ...................... 0 differenze
B4 10 colonne quota .......... 0 differenze  (ri-derivate dal grezzo)
C1 gol da fonte INDIPENDENTE . 1 differenza  (§4.3, risultato a tavolino)
C2 8 colonne xG/stile ........ 0 differenze
```

Cioè: **nessun numero dello snapshot è diverso da quello della fonte**. La
politica quote della Fase 73 (chiusura solo da colonne `*C*` genuine) è
riprodotta esattamente; la copertura O/U è conforme al dichiarato (0% nel
2017-19, ~100% dal 2019-20) su tutte e 5 le leghe; il mercato risulta calibrato
(scarto prob.-frequenza ≤ 0.018) e il margine del book conferma la semantica
dichiarata (2017-19 Pinnacle ~2.3-2.8%, dal 2019-20 media ~4-6%).

Controlli avversariali passati **senza un solo caso**: impronte-quota duplicate
(0), riposo incoerente col calendario (0), tiri in porta > tiri (0), gol
negativi/impossibili (0), valore rosa non costante per (squadra, stagione) (0),
squadre con due gare lo stesso giorno (0), nomi squadra quasi-duplicati (0).

---

## 4 · Le 7 anomalie trovate (tutte reali, tutte nella fonte)

### 4.1 · 11 righe con margine IMPOSSIBILE nella linea O/U 2017-19 → **da correggere**

Il guard di produzione (`loader._pick_market_odds`, Fase 58) scarta solo
l'overround **< 1** (arbitraggio). Non esiste un guard sul lato opposto: una
media multi-book con il **28% di margine** è altrettanto impossibile, e passa.

| lega | righe | mercato | overround |
|---|--:|---|---|
| la_liga | 3 | `odds_over25_open` / `odds_under25_open` | 1.128 – 1.283 |
| bundesliga | 6 | idem | 1.276 – 1.339 |
| ligue_1 | 2 | idem | 1.264 – 1.282 |

Tutte e 11 nelle stagioni **2017-18/2018-19** (fonte `BbAv`, Betbrain); **zero**
casi nell'era `Avg` (2019-20+), dove il massimo osservato è 1.076. Distribuzione
sana: mediana 1.052, p99.9 ≈ 1.073 → la soglia 1.12 è ~6σ oltre la mediana.

**Quale dei due lati è rotto?** Dimostrato usando un segnale indipendente (l'1X2
della stessa partita, invertito nella matrice DC):

| partita | P(Over) implicita dall'1X2 | lato Over grezzo | lato Under grezzo |
|---|---|---|---|
| Alaves-Real Madrid 06/10/18 | 0.584 | 1.53 → 0.654 ✅ coerente | 1.59 → 0.629 ❌ implica P(Over)=0.37 |
| Eibar-Real Madrid 24/11/18 | 0.596 | 1.45 → 0.690 ✅ | 1.69 → 0.592 ❌ |
| Leganes-Betis 10/02/19 | 0.368 | 2.48 → 0.403 ✅ | 1.38 → 0.725 ❌ |

In tutti i casi è **il lato Under** a essere incompatibile con l'1X2: le due
quote non appartengono alla stessa linea.

**Impatto:** queste righe sono l'**input** della stima di chiusura O/U 2017-19
(3 stime La Liga poggiano su di esse — vedi Report 2 §3.7) e inquinano ogni
analisi che deviga l'apertura O/U di quelle stagioni.

**Raccomandazione:** aggiungere in `loader._pick_market_odds` un guard
simmetrico a quello della Fase 58 — se l'overround supera una soglia
(proposta: **1.12**, ~6σ oltre la mediana sana), si ritenta col livello di
preferenza successivo e, se anche quello è impossibile, **NaN dichiarato**
(mai un numero corretto a mano: §5 del CLAUDE.md). Costo: 11 celle su 15.788
partite (0.07%). Bozza di patch in `cantiere/patch/guard_overround.md`.

### 4.2 · Udinese-Roma 25/04/2024: quote di chiusura di una partita di 19 minuti → **da dichiarare**

La partita fu **sospesa il 14/04/2024 sull'1-1** (malore di Ndicka) e **ripresa
il 25/04** per gli ultimi ~19 minuti (finale 1-2). Nello snapshot:

```
apertura  (Avg*)  3.41 / 3.27 / 2.22   <- partita intera, prezzo normale
chiusura  (AvgC*) 5.16 / 1.72 / 3.75   <- il PAREGGIO e' favorito: e' il frammento
                                          di 19 minuti, che parte dall'1-1
```

Due prove indipendenti: (a) il pareggio a 1.72 è impossibile per una
Udinese-Roma intera; (b) Understat data la partita al **14/04** (unica
discordanza di data in Serie A, WARN C3). Anche l'O/U di chiusura è coerente col
frammento (P(Over 2.5) = 0.488 = «almeno un altro gol in 19 minuti»).

**Impatto:** 1 riga su 3.420. Le quote di **chiusura** di quella riga non sono
confrontabili col resto (il controllo D2 la segnala come unica coppia 1X2/O/U
incoerente, residuo 0.11). L'apertura invece è regolare.

**Raccomandazione:** dichiararla in `docs/DATI.md` come eccezione nota ed
escluderla dalle analisi basate sulla chiusura (o marcarla con una colonna-flag).

### 4.3 · Union Berlin-Bochum 14/12/2024: risultato ASSEGNATO a tavolino → **da dichiarare**

Unica riga su 15.788 con **tutte le statistiche assenti** (tiri, tiri in porta,
gol primo tempo: NaN) — la firma tipica del risultato d'ufficio.

| fonte | risultato | xG |
|---|---|---|
| football-data | **0-2** (assegnato) | — |
| Understat | **1-1** (giocato) | 3.01 – 1.24 |

È l'unica differenza di risultato tra due fonti indipendenti su 15.788 partite:
il campo dice 1-1, il giudice sportivo 0-2 (accensino lanciato dagli spalti sul
portiere del Bochum). Lo snapshot mette insieme **gol amministrativi** e **xG
del match giocato**.

**Raccomandazione:** dichiararla; valutare l'esclusione dal fit (un 0-2
d'ufficio non è una realizzazione del processo che il modello stima). Riga
nuova, arrivata con la Bundesliga.

### 4.4 · Bielefeld-Leverkusen 21/11/2020: NON era un errore — **falso positivo, ritirato**

> ⚠️ **Questa voce è stata corretta dopo un approfondimento: il dato era giusto,
> era il mio controllo a essere cieco.** Storia completa in
> [`07_dati_corrotti.md`](07_dati_corrotti.md) §1.

Understat pubblica `xG: 0` per il Bielefeld, che però ha **segnato 1 gol** e che
football-data dà con **1 tiro in porta**. Sembrava impossibile. Non lo è: il dato
tiro-per-tiro della stessa fonte (`getMatchData/15207`) mostra che il Bielefeld
ha **0 tiri** e che il suo gol è un **autogol del portiere avversario**
(Hrádecky, 47′ — confermato da fonte indipendente). Una squadra che non tira e
segna solo per un autogol avversario ha davvero xG = 0.00. Il «tiro in porta» di
football-data è solo una convenzione diversa sullo stesso autogol.

Il controllo `audit_anomalie.check_xg` ora **verifica gli autogol** sul dato
tiro-per-tiro prima di dichiarare un'impossibilità: con la verifica attiva, gli
xG impossibili sono **0 su tutte e 5 le leghe**. Gli altri 10 casi di `xG = 0.00`
restano legittimi (squadre con 0 tiri).

### 4.5 · Ligue 1 2019-20: campionato CANCELLATO → **fatto reale, da dichiarare**

279 gare su 380, ultima l'**8 marzo 2020**: la Ligue 1 è l'unico grande
campionato **non ripreso** dopo il COVID (decisione del 30/04/2020). PSG e
Strasburgo ne hanno giocate 27 invece di 28. Non è un errore d'importazione:
rompe legittimamente il controllo «girone all'italiana completo».

**Conseguenza pratica:** ogni analisi cross-lega che assume 380 gare/stagione va
adattata; la stagione resta utilizzabile ma è **strutturalmente più corta**.

### 4.6 · Ordine delle colonne diverso tra snapshot → **da uniformare**

`docs/DATI.md` §1 afferma «lo **schema è identico** su tutte e tre le leghe
(dalla Fase 60)». L'**insieme** delle 38 colonne è identico; l'**ordine** no:
in Premier e Liga le 5 colonne `*_open` stanno in posizione 15-19, in Serie A in
posizione 29-33.

Nessun effetto sui calcoli (si legge per nome), ma: (a) l'affermazione del
documento è imprecisa; (b) `loader.refresh_odds` conserva l'ordine *di ciascun
file*, quindi la divergenza si perpetua. I due snapshot nuovi sono stati scritti
**nell'ordine della Serie A**.

**Raccomandazione:** riordinare Premier/Liga all'ordine canonico e aggiungere un
test che confronta le liste di colonne fra leghe (oggi `tests/test_league_snapshots.py`
non lo fa).

### 4.7 · Lacune di copertura minori → **già dichiarate in linea di principio**

- **Europa/Conference League 2025-26 assenti in openfootball** (esistono solo i
  file di qualificazione). Vale per **tutte e 5** le leghe: `data/club_fixtures*.csv`
  della stagione in corso contengono solo Champions + qual. Conference.
  Effetto: `midweek_europe` è un **falso 0** per i club impegnati in EL/Conference
  nel 2025-26. Rientra nella lacuna già dichiarata in `docs/DATI.md` §3, ma
  merita una nota specifica perché riguarda la stagione più recente.
- **Nantes-Toulouse 17/05/2026** (Ligue 1): Understat marca la partita
  `isResult=false` → xG mancante (NaN dichiarato). Copertura xG Ligue 1: 99.97%.
- **3 date discordanti in Ligue 1** tra le due fonti (Caen-Toulouse 2018: 11
  giorni; Strasbourg-Lyon 2023 e Metz-Lille 2026: 2 giorni). La data canonica
  del progetto è quella di football-data (base dello snapshot); lo scarto
  influenza solo il peso temporale e i giorni di riposo, in modo trascurabile.
- **74 righe con gol > tiri in porta** (0.5% del totale): **non** sono errori —
  gli **autogol** non vengono conteggiati come tiri in porta della squadra che
  segna. Verificato su casi noti (Napoli-Spezia 22/12/2021, autogol di Juan
  Jesus: 1 gol, 0 tiri in porta). Zero casi dell'anomalia opposta (tiri in porta
  > tiri), che sarebbe invece un errore vero.

---

## 5 · Cosa è stato provato e NON è risultato sbagliato

Per onestà simmetrica (§1.4 e §1.6 del CLAUDE.md), l'elenco delle ipotesi di
errore **respinte dai dati**:

- «lo snapshot è derivato da una fonte che nel frattempo è cambiata» → **no**:
  ri-scaricando oggi tutte e 45 le stagioni, ogni gol, data, tiro e quota
  coincide;
- «la politica quote apertura/chiusura è applicata male» → **no**: le 10 colonne
  ri-derivate dal grezzo coincidono al bit;
- «i risultati potrebbero essere sbagliati alla fonte» → **no**: confermati da
  una seconda fonte indipendente (Understat) su 15.787 partite su 15.788;
- «gli xG a zero sono buchi mascherati» → **no** in 10 casi su 11 (0 tiri
  confermati dalla fonte indipendente); sì in 1 (§4.4);
- «potrebbero esserci quote copiate da una partita all'altra» → **no**: zero
  impronte-quota duplicate nello stesso giorno;
- «il calendario di club potrebbe gonfiare il riposo» → **no**: `rest_days_full`
  non supera mai il riposo calcolato sul solo campionato, in nessuna riga;
- «il valore rosa potrebbe variare tra righe della stessa squadra-stagione» →
  **no**: zero incoerenze.

## 6 · Cosa fare (in ordine di priorità)

1. **Guard sull'overround alto** in `loader._pick_market_odds` (§4.1) →
   11 celle a NaN, e rigenerare le stime che vi poggiano.
2. ~~Portare a NaN l'xG di Bielefeld-Leverkusen~~ → **non serve**: falso
   positivo, ritirato (§4.4). Va invece portato in produzione il controllo
   corretto, quello che verifica gli autogol.
3. **Dichiarare** in `docs/DATI.md`: Udinese-Roma (§4.2), Union-Bochum (§4.3),
   Ligue 1 2019-20 (§4.5), lacuna EL/Conference 2025-26 (§4.7).
4. **Uniformare l'ordine colonne** di Premier/Liga + test cross-lega (§4.6).
5. Correggere in `docs/DATI.md` la frase «schema identico» → «stesse 38 colonne;
   ordine da uniformare».

Tutti gli script dell'audit sono riutilizzabili e parametrici sulle 5 leghe:
`cantiere/scripts/audit_snapshots.py`, `cantiere/scripts/audit_anomalie.py`.
