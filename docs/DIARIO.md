# Diario di bordo — Polymarket Oracle

Resoconto passo-passo di come è stato costruito il progetto, **con il ragionamento
e le scelte** dietro ogni decisione. È pensato per chiunque (persona o AI) voglia
capire *perché* il software è fatto così, non solo *com'è* fatto.

Filo conduttore metodologico, applicato ovunque:

1. **Tracer bullet prima dei moduli** — costruire una fetta verticale reale
   end-to-end, poi raffinare, invece di progettare tutto a tavolino.
2. **Una cosa alla volta, e si misura** — cambiare un solo fattore per volta,
   altrimenti non si sa *cosa* ha funzionato.
3. **Testare la versione economica di un'idea prima di investire** — evita di
   costruire infrastrutture costose su assunzioni non verificate.
4. **Documentare anche i risultati negativi** — sapere cosa *non* funziona vale
   quanto sapere cosa funziona.
5. **Riproducibilità** — ogni numero dev'essere rifacibile da terzi.
6. **Onestà sui limiti** — soprattutto perché in gioco ci sono soldi veri.

---

## Fase 0 — Visione e prime scelte di fondo

**Idea di partenza.** Un motore per stimare la **probabilità reale** di eventi
sportivi (calcio), *indipendente dalle piattaforme* (Polymarket, bookmaker,
exchange). Il valore è il modello, non l'integrazione con un sito.

**Scelte chiave discusse e prese:**

- **Modellare la distribuzione dei gol per squadra**, non i singoli mercati.
  Ragionamento: 1X2 e Over/Under non sono eventi indipendenti — derivano entrambi
  da *quanti gol segna ciascuna squadra*. Modellando la matrice
  P(gol_casa = i, gol_ospite = j) si ricavano **tutti** i mercati in modo
  coerente (niente contraddizioni tipo "55% vittoria casa" + "70% Under 2.5"), e
  aggiungere mercati futuri è gratis. Bonus: per il live basterà condizionare la
  stessa distribuzione al minuto e al punteggio.
- **Serie A come binario serio; Mondiali scartati.** I Mondiali hanno poco
  storico, quote efficientissime e troppe poche partite per validare qualcosa:
  scommettere lì "di corsa" non era realistico. Meglio un campionato con dati
  abbondanti.
- **Modello: Dixon-Coles (1997), scritto da noi.** Rispetto alla Poisson pura
  aggiunge una correzione sui punteggi bassi (0-0, 1-0, 0-1, 1-1, più frequenti
  del previsto) e il decadimento temporale. Scritto a mano invece di usare una
  libreria per capirlo e controllarlo a fondo (è il cuore del progetto).
- **Metriche di successo.** *Calibrazione* con Brier score e log-loss; *edge
  reale* col confronto contro le **quote di chiusura** dei bookmaker (lo
  stimatore più efficiente che esista). Traguardo realistico iniziale: battere
  baseline banali ed essere ben calibrati — non "battere il mercato", che è
  impresa da professionisti.
- **Dati: football-data.co.uk** (gratis, include risultati *e* quote di chiusura).

---

## Fase 1 — Tracer bullet: Dixon-Coles + backtest

**Obiettivo.** Prima pipeline reale end-to-end su Serie A:
dati → modello → probabilità 1X2 e O/U 2.5 → validazione.

**Ostacolo dati (e soluzione).** L'ambiente cloud **blocca football-data.co.uk**
(policy di rete). Invece di arrenderci, abbiamo trovato un **mirror su GitHub**
con lo stesso identico formato (9 stagioni di Serie A, 380 partite ciascuna, con
quote di chiusura). Fonte tenuta **configurabile in un unico punto**
(`sources.py`) così in locale basta cambiare un URL.

**Metodologia del backtest (per evitare il "barare").** Walk-forward: prima di
ogni giornata si riallena il modello usando **solo** le partite già avvenute, poi
si predice quel turno. Nessun look-ahead: il filtro `data < as_of` garantisce che
non si guardi mai il futuro.

**Risultato (stagione 2025-26, config iniziale):**

| Mercato | Modello | Baseline | Mercato |
|---|---:|---:|---:|
| 1X2 log-loss | 1.0047 | 1.0851 | 0.9784 |

**Lettura.** Il modello **batte la baseline** (impara qualcosa di reale) ma **non
il mercato** — esito atteso e sano per un primo modello. La simulazione di
scommesse dava ROI negativo: onesto e prevedibile. *La pipeline funziona: da qui
si può migliorare con basi solide.*

---

## Fase 2a — Analisi degli errori (e un bug trovato)

**Perché prima di aggiungere feature.** Invece di aggiungere segnali a caso,
abbiamo costruito uno strumento (`analyze.py`) per capire *dove* il modello perde
contro il mercato.

**Scoperte:**

1. **Sulla media il modello è ben calibrato** — nessun bias sistematico, nemmeno
   sui pareggi (difetto tipico dei modelli Poisson, che noi *non* avevamo). Quindi
   il mercato ci batte in **discriminazione** delle singole partite, non in
   calibrazione media.
2. **Bug trovato e corretto.** La stagione di test chiamava il Verona "Hellas
   Verona", le stagioni di training "Verona": il modello lo trattava come squadra
   *sconosciuta* e sparava predizioni assurde (87% a una neopromossa). Risolto con
   una mappa di normalizzazione nomi (`TEAM_ALIASES`). *Questo da solo giustifica
   aver analizzato prima di aggiungere feature.*
3. **Dove perdiamo di più:** partite con **neopromosse** (gap col mercato +0.037,
   doppio della media) e **inizio stagione** (+0.030). Radice comune: dati storici
   scarsi o datati → stime inaffidabili e troppo sicure.

---

## Fase 2b — Tuning: regolarizzazione e memoria

Guidati dalla diagnosi, due interventi, **uno alla volta**, validati su più
stagioni.

**1. Shrinkage (regolarizzazione).** Una "molla" che tira le stime di forza verso
la media della lega, più forte quando i dati sono pochi (la penalità è fissa
mentre il contributo dei dati cresce col numero di partite). Attacca proprio
neopromosse e inizio stagione. Tarato → valore ottimo **1.5**. Gap sull'inizio
stagione da +0.030 a +0.022, sulle neopromosse da +0.037 a +0.030: colpisce i
bersagli previsti.

**2. Emivita del decadimento temporale.** Quanto pesare le partite recenti.
Scoperta controintuitiva: l'emivita corta (90g) è la *peggiore*; il modello
preferisce **memoria lunga (~730g, due stagioni)**. Ha senso: in Serie A le rose
restano stabili anno su anno, quindi pesare troppo le ultime partite butta via
segnale.

| Config | log-loss 1X2 (media 3 stagioni) | gap col mercato |
|---|---:|---:|
| Dixon-Coles puro | ~0.9863 | +0.026 |
| + shrinkage 1.5 | 0.9863 | +0.021 |
| + emivita 730g | **0.9829** | **+0.017** |

**Risultato:** solo con la taratura abbiamo recuperato **circa un terzo** del
divario col mercato, senza informazione nuova. Ma il modello sui *soli gol* è ora
vicino al suo tetto.

---

## Fase 3 — Informazione nuova: i tiri in porta (risultato NEGATIVO)

**Ipotesi.** I gol sono rumorosi (fortuna sotto porta). I **tiri in porta**
misurano le occasioni con meno rumore — un "xG dei poveri" — e sono già nella
nostra fonte dati. Forse aiutano.

**Come l'abbiamo testato (scelta elegante).** Invece di scegliere a tavolino tra
"solo gol" e "solo tiri", abbiamo costruito la **forma generale**: si allena un
modello sui gol e uno sui tiri, e si **mescolano** i tassi attesi con un peso α
tarabile (`shots_blend`). α=1 = solo gol (modello attuale); α=0 = solo tiri;
intermedio = miscela. Così B ("solo tiri") è semplicemente il caso α=0, testato
*gratis* dentro lo stesso tuning — niente da indovinare, decide il dato.

**Esito, validato su SEI stagioni** (2020-21 → 2025-26, regimi diversi, COVID
inclusi):

| α (peso gol) | 1X2 (media) | O/U 2.5 (media) |
|---:|---:|---:|
| 0 (solo tiri) | 0.9913 | 0.6964 |
| 0.5 | 0.9833 | 0.6909 |
| **1 (solo gol)** | **0.9817** | **0.6904** |

**Conclusione: i tiri in porta *grezzi* non aiutano in modo affidabile.** Su 3
stagioni sembrava esserci un vantaggio sull'Over/Under, ma **si è dissolto su 6**:
era rumore di piccolo campione (allargare il backtest — su suggerimento giusto —
ha *chiarito* il quadro).

**Nota tenuta agli atti.** Nella stagione più recente (2025-26) dare peso ai tiri
*migliora* l'Over/Under: ipotesi che lo stile di gioco stia cambiando e le
occasioni diventino via via più informative. Da ri-verificare.

**Perché è comunque un buon risultato.** Aver testato la versione *economica*
dell'idea "le occasioni aiutano" ci ha **evitato** di costruire una pipeline
xG/database sull'assunzione — sbagliata — che bastassero i tiri grezzi. Il codice
del blend resta, pronto per l'**xG reale** (che pesa la *qualità* delle occasioni,
non solo il conteggio).

---

## Infrastruttura — Tracciabilità e database interno

Man mano che gli esperimenti si accumulavano, sono diventate necessarie due
fondamenta:

**1. Registro degli esperimenti** (`experiments/runs.jsonl`). Ogni backtest scrive
un record con **configurazione + metriche + commit git + impronta dei dati +
data**. Così ogni numero è replicabile e verificabile da terzi. Il calcolo delle
metriche è centralizzato in una **fonte di verità unica** (`compute_metrics`).

**2. Archivio dati interno.** Per non dipendere dalla disponibilità *live* di un
mirror esterno (che può cambiare o sparire):
- **snapshot** `data/serie_a_matches.csv` — versionato in git, testo diffabile:
  la fonte di verità *congelata* (chi clona il repo ha gli stessi dati, senza
  rete);
- **database SQLite** `data/football.db` — queryable, rigenerabile dallo snapshot.

La pipeline è **offline-first**: i backtest leggono lo snapshot congelato, quindi
i risultati sono riproducibili identici.

---

## Dove siamo — cosa sappiamo con onestà

**Il modello NON è scarso a predire.** Indovina il segno giusto dell'1X2 il
**52.6%** delle volte, contro il **53.9%** del mercato: un solo punto di distanza,
e nel 92% dei casi scegliamo lo stesso favorito. Il calcio è caotico: nessuno fa
molto meglio del ~54%.

**Ma non batte il mercato**, e questo ha un significato preciso. "Battere il
mercato" = produrre probabilità *più accurate* delle quote di chiusura. Quando ci
discostiamo dal mercato, ha ragione lui più spesso di noi (siamo più vicini al
vero solo nel 43% delle partite). Per *guadagnare* scommettendo servirebbe essere
più accurati del mercato di *almeno* il suo margine (~5%): siamo un pelo *meno*
accurati, quindi ogni "value bet" è quasi sempre un nostro errore travestito da
opportunità → ROI simulato negativo.

**Conseguenza pratica:** allo stato attuale il modello **non va usato per
scommettere soldi veri**. È un motore pulito, calibrato e onesto che *approssima*
il mercato senza superarlo.

---

## Fase 4a — I dati per l'xG reale (e per le rose): arricchimento completato

**Obiettivo.** Prima di ri-tarare il modello con l'xG (Fase 4), servivano i
dati: xG per *ogni* partita storica, valori rosa a inizio stagione e una stima
delle assenze. Tutto nello snapshot congelato, offline-first, senza toccare la
base football-data.

**Ragionamento e alternative.**
- *xG*: understat.com e fbref.com non sono raggiungibili da questo ambiente
  (proxy). Alternativa trovata: lo **stesso repo mirror** GitHub gia' usato per
  football-data espone anche i JSON di lega Understat (aggiornati da un workflow
  giornaliero). Verificato: 380/380 partite con xG per tutte e 9 le stagioni.
- *Valori rosa*: transfermarkt.com non raggiungibile; nessuna tabella con valori
  rosa per squadra-stagione nei datalake GitHub esplorati. Scelta: ricostruzione
  **bottom-up** = rosa stimata dai giocatori con minuti su Understat + ultima
  valutazione Transfermarkt (datalake `salimt/football-datasets`) **antecedente
  al 1° settembre** della stagione (niente look-ahead, staleness max 550 giorni).
- *Assenze*: dalla tabella infortuni dello stesso datalake, contando per ogni
  partita i giocatori della rosa infortunati in quella data (informazione nota
  pre-partita). Sono **stime**, marcate col suffisso `_est`.

**Il problema vero: allineare i nomi.** Squadre: bastano 3 alias
(`AC Milan`→`Milan`, `Parma Calcio 1913`→`Parma`, `SPAL 2013`→`Spal`).
Giocatori: molto piu' duro (accenti, translitterazioni, "Gian Marco"/"Gianmarco",
nomi accorciati). Catena deterministica di aggancio misurata su 1.986 giocatori:
esatto 1691, filtro ruolo/valutazioni 96, spareggio per valore di picco 63,
senza-spazi 3, sottoinsiemi di token 21, cognome+iniziale 29, fuzzy conservativo
(soglia 0.90) 8, **non agganciati 78** (~4%, quasi tutti con pochi minuti).

**Risultato.**
- 14 nuove colonne nello snapshot (3420 righe invariate, impronta dati
  invariata `8483944342fc8b15` perche' calcolata solo su date/squadre/gol):
  `home_xg, away_xg, home_npxg, away_npxg, home_ppda, away_ppda, home_deep,
  away_deep, home_squad_value, away_squad_value, home_absent_count_est,
  away_absent_count_est, home_absent_value_est, away_absent_value_est`.
- Copertura xG: **100% in tutte le stagioni**. Copertura valori rosa (entrambe
  le squadre): 63-80% a seconda della stagione.
- Backtest di non-regressione: metriche **identiche** a quelle documentate
  (log-loss 1X2 0.9890 / baseline 1.0851 / mercato 0.9784).

**Limite onesto (documentato, non aggirato).** Il datalake Transfermarkt e'
incompleto: ~25% dei profili **non ha alcuna serie di valutazioni** (mancano
anche titolari, es. Milinkovic-Savic; la Lazio ne soffre in tutte le stagioni).
Politica: il valore rosa e' pubblicato **solo** se i giocatori valutati coprono
almeno l'85% dei minuti della squadra, altrimenti `NaN`. **Niente imputazioni**:
meglio un buco dichiarato che un numero inventato. Le assenze restano stime
(`_est`) perche' rosa e infortuni derivano da fonti ricostruite.

**Lezione.** Con vincoli di rete stretti, il collo di bottiglia non e' il
modello ma la *provenienza* dei dati: trovare mirror affidabili e allineare i
nomi tra fonti vale piu' di qualunque raffinatezza statistica a valle.

---

## Fase 4b — xG reale nel blend: primo miglioramento da dati nuovi

**Obiettivo.** Rifare l'esperimento del blend della Fase 3 (fallito coi tiri
grezzi) usando l'**xG reale** ora disponibile: le occasioni pesate per qualita'
aiutano dove i tiri grezzi non aiutavano?

**Ragionamento e scelta.** L'infrastruttura c'era gia': abbiamo generalizzato il
blend a un `blend_signal` qualsiasi ("sot"=tiri, "xg"=xG, "npxg"). L'xG e' gia' in
scala gol (la conversione risulta ~1, contro ~0.3 dei tiri). Il modello sull'xG
usa lo stesso `_fit_counts` (Poisson-famiglia su valori continui, senza la
correzione sui punteggi bassi).

**Risultato (6 stagioni, log-loss).**

| α (peso gol) | 1X2 | O/U 2.5 |
|---:|---:|---:|
| 0 (solo xG) | 0.9840 | 0.6897 |
| 0.5 | 0.9816 | 0.6888 |
| **0.75** | **0.9813** | 0.6893 |
| 1 (solo gol) | 0.9817 | 0.6904 |

- **Primo segnale che aggiunge valore.** Dove i tiri grezzi fallivano, l'xG
  aiuta: piccolo, ma reale e consistente, soprattutto sull'Over/Under (la qualita'
  delle occasioni informa il volume di gol; sull'1X2 conta meno chi *crea*, piu'
  chi *concretizza*).
- **Scelta config: α = 0.75** (blend_signal xg). Migliora *entrambi* i mercati
  sulla media a 6 stagioni ed e' conservativa. Presa sulla media, non su una
  stagione: sul solo 2025-26 l'1X2 e' appena sotto (0.9900 vs 0.9890) ma l'O/U
  migliora — variabilita' attesa.

**Lezione.** La *qualita'* del segnale conta piu' del segnale in se': stessa idea
("le occasioni aiutano"), stesso meccanismo, ma coi tiri grezzi -> nulla, con
l'xG -> primo passo avanti. Conferma anche l'ipotesi tenuta agli atti: i guadagni
O/U piu' grandi sono nelle stagioni recenti (stile di gioco in evoluzione).

**Onestà.** Il miglioramento e' modesto e non basta a battere il mercato. Restano
da spremere gli altri dati gia' disponibili (npxG, valori rosa, assenze).

---

## Fase 4c — Spremere il resto dei dati: npxG, valori rosa, assenze (NEGATIVO)

**Obiettivo.** Sfruttare al massimo i dati gia' in casa prima di cercarne altri:
npxG come segnale, e valori rosa / assenze come **covariate** (forza/contesto
esterni ai risultati), anche in **combinazione** (l'idea: due segnali deboli da
soli potrebbero valere di piu' insieme).

**Cosa abbiamo costruito.** Un **layer di covariate** generale: ogni covariata
entra nel tasso atteso della squadra che segna come `beta*(z_squadra -
z_avversaria)`, con i `beta` stimati **insieme** al resto via ML. Piu' covariate =
fit congiunto (cattura il contributo reciproco). Retrocompatibile.

**Metodo onesto.** Prima un diagnostico *economico* in-sample sul valore-rosa:
segnale residuo apparente (coeff +0.48). Ma il test vero e' walk-forward.

**Risultati (6 stagioni, log-loss).**

| | 1X2 | O/U 2.5 |
|---|---:|---:|
| baseline (config Fase 4b) | **0.9813** | 0.6893 |
| npxG al posto di xG | 0.9811 | 0.6892 |
| + valore-rosa | 0.9818 | 0.6891 |
| + assenze | 0.9813 | 0.6893 |
| + valore-rosa & assenze | 0.9818 | 0.6892 |

- **npxG ≈ xG** (differenza 0.0002, entro il rumore): tenuto xG, piu' standard.
- **Valore-rosa: non aiuta** (peggiora appena l'1X2). Il diagnostico in-sample era
  ottimistico: la forza della rosa e' **gia' catturata** dal modello gol+xG (si
  vede nei risultati e nell'xG). Fuori campione aggiunge piu' rumore che segnale.
- **Assenze: effetto nullo** (dato stimato e rumoroso; gli infortuni sono in parte
  gia' nei risultati recenti che il decadimento pesa).
- **Nessuna sinergia** dalle combinazioni: unire segnali ~nulli da' ~nulla.
- **Riposo/congestione (solo Serie A): non aiuta** (1X2 0.9817 vs 0.9813).
  Motivo: calcolato dalle sole date di Serie A, NON vede coppe/Europa/nazionali —
  proprio le partite che causano fatica asimmetrica. Quando tutta la lega gioca
  infrasettimana, il riposo e' basso per entrambe -> la *differenza* e' ~0. Il
  layer covariate "rest" resta: con un **calendario di club completo** (dato
  nuovo) calcolerebbe la congestione vera. E' l'unico segnale "indipendente dai
  risultati" rimasto con potenziale, ma va reperito.

**Lezione.** Con questa fonte dati il modello ha raggiunto il suo **tetto
pratico**: gol + xG + taratura. I dati extra (rosa, assenze) non aggiungono
segnale *indipendente* out-of-sample perche' cio' che contengono e' gia' implicito
nei risultati. Il diagnostico in-sample va sempre confermato walk-forward.

**Config (dopo la Fase 4d):** emivita 365g, shrinkage 1.5, blend gol/xG α=0.75,
nessuna covariata. Il layer covariate resta (documentato, off di default),
riutilizzabile per dati futuri davvero indipendenti (es. formazioni ufficiali
last-minute, meteo, motivazione).

---

## Fase 4d — Ri-taratura congiunta: l'emivita si accorcia col blend xG

**Obiettivo.** Shrinkage ed emivita erano stati tarati (Fase 2b) sul modello
*solo-gol*. Con il blend xG (Fase 4b) attivo, l'ottimo potrebbe essere cambiato:
interazione mai verificata. Ri-taratura a coordinate su 6 stagioni, alla config
attuale (blend xG 0.75).

**Risultato.** Lo shrinkage resta buono a 1.5. L'**emivita ottima si sposta da
730g a ~365g** (una stagione): rifinita, minimo netto a 365 per *entrambi* i
mercati.

| emivita | 1X2 | O/U 2.5 |
|---:|---:|---:|
| 730 (vecchia) | 0.9813 | 0.6893 |
| **365 (nuova)** | **0.9807** | **0.6884** |

**Lezione.** Con un segnale meno rumoroso (l'xG), il modello puo' permettersi una
**memoria piu' corta** / piu' reattiva senza rincorrere il rumore. E' un'interazione
reale: cambiare una parte (aggiungere l'xG) sposta l'ottimo di un'altra (l'emivita).
Per questo, dopo un cambiamento importante, conviene ri-verificare gli iperparametri
gia' tarati. Guadagno piccolo (~0.0007) ma su entrambi i mercati e ben fondato.

**Config ufficiale aggiornata:** blend gol/xG α=0.75, shrinkage 1.5, **emivita 365g**.

---

## Fase 5 — Grande backtest multi-mercato: per cosa il modello serve davvero

**Obiettivo.** Allargare lo sguardo oltre 1X2/OU: GG/NG (entrambe segnano) e
doppie chance (1X/2X/12). Sono tutti derivabili GRATIS dalla stessa matrice dei
punteggi. Grande operazione: 2 config (gol base vs ufficiale gol+xG) x 6 stagioni
x tutti i mercati.

**Risultato (log-loss medio 6 stagioni).**

| Mercato | gol+xG (uff.) | Mercato | Baseline |
|---|---:|---:|---:|
| 1X2 | 0.9807 | 0.9632 | 1.0834 |
| Over/Under 2.5 | 0.6884 | 0.6816 | 0.6892 |
| GG/NG | 0.6896 | — | 0.6871 |
| 1X (casa o pari) | 0.5497 | 0.5371 | 0.6303 |
| 2X (ospite o pari) | 0.5966 | 0.5833 | 0.6744 |
| 12 (no pari) | 0.5766 | 0.5746 | 0.5820 |

**Lettura.**
- **Bravo (batte nettamente la baseline): 1X2, 1X, 2X** — i mercati d'ESITO. Il
  modello stima bene chi vince; tutto cio' che ne deriva funziona.
- **Debole: Over/Under** (baseline di un soffio) e **12/no-pari** (~pari a mercato
  e baseline: i pareggi sono quasi casuali per tutti).
- **NEGATIVO: GG/NG e' PEGGIO della baseline** (0.6896 vs 0.6871). La probabilita'
  congiunta "entrambe segnano" dipende dalla correlazione tra i due punteggi, che
  il modello (Poisson quasi-indipendenti + correzione DC solo sui punteggi bassi)
  cattura male: sul GG aggiunge rumore, non segnale.
- La config gol+xG e' uniformemente >= alla base solo-gol: config ufficiale
  validata anche multi-mercato. **Nessun mercato batte le quote.**

**Lezione / cosa ne consegue.** Il motore e' uno strumento d'analisi affidabile
per i mercati d'ESITO (1X2, doppie chance), NON per il GG/NG (lì meglio la media)
e a malapena per l'Over/Under. Un'eventuale prossima mossa sul modello sarebbe
proprio la **correlazione dei punteggi** (es. bivariate Poisson) per il GG/NG.

---

## Prossimo passo — il modello e' al tetto dei dati attuali

Il divario residuo richiede **informazione che il mercato ha e noi no**: la
*qualità* delle occasioni. Abbiamo trovato una fonte **xG reale** raggiungibile
(mirror Understat su GitHub) con copertura storica completa (2016-17 → 2024-25).

Piano in due binari:
1. **Validazione (in questo ambiente):** integrare l'xG storico nel database e
   ri-tarare il blend usando l'**xG reale** al posto dei tiri grezzi — la prova
   pulita dell'ipotesi "le occasioni aiutano", fatta coi dati giusti. La stessa
   infrastruttura della Fase 3 la abilita già (basta puntare il "secondo modello"
   sull'xG).
2. **Uso reale (in locale):** un fetcher Understat per dati *completi e correnti*,
   sostituibile in `sources.py`, che scrive nello stesso snapshot/database.

Nota di realismo: anche con l'xG, battere le quote di chiusura resta difficile
(i professionisti parlano di 2-5% di edge dopo anni). L'xG è la mossa con la
miglior probabilità di aprire un vantaggio, ma senza garanzie.

---

*Questo diario viene aggiornato ad ogni fase. Per i dettagli tecnici e i comandi
vedi il [README](../README.md); per i risultati grezzi e replicabili
`experiments/runs.jsonl`.*
