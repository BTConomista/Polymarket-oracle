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

## Fase 4e — Calendario di club completo: la congestione VERA (dato nuovo)

**Obiettivo.** Dare al modello l'unico segnale "indipendente dai risultati"
rimasto con potenziale (Fase 4c): la **congestione vera**. Il riposo calcolato
sulle sole date di Serie A (`loader.add_rest_days`) NON vede coppe ed Europa —
proprio le partite infrasettimanali che causano fatica ASIMMETRICA — quindi non
aiutava. Serve il **calendario COMPLETO di club** di ogni squadra.

**Ragionamento e alternative.**
- *Fonte ideale*: FBref ("Scores & Fixtures" per squadra, colonna Comp) o
  Transfermarkt — entrambe NON raggiungibili dall'ambiente cloud (proxy, come
  gia' per xG e valori rosa). I datalake Transfermarkt su GitHub o non hanno una
  tabella partite (`salimt/football-datasets`), o la tengono dietro Git LFS
  esaurito / su S3 (`dcaribou`): vicolo cieco.
- *Fonte scelta*: **openfootball** (mirror GitHub, testo pubblico raggiungibile
  via raw). Copre per stagione le competizioni UEFA per club
  (Champions/Europa/Conference + preliminari) e la Coppa Italia. Le partite di
  **Serie A NON si scaricano**: si derivano dallo **snapshot congelato** (esatte,
  nomi gia' canonici, copertura 100%). Il calendario completo = Serie A (interno)
  + coppe/Europa (openfootball).

**Cosa abbiamo costruito.**
1. Un fetcher pulito (`src/data/fixtures.py`) con URL centralizzati in
   `sources.py`, cache offline in `data/raw/` (coerente con understat/transfermarkt).
2. La tabella grezza versionata `data/club_fixtures.csv` (una riga per
   squadra-partita: `season, team, date, competition, home_away, opponent`), coi
   nomi allineati ai nostri via `TEAM_ALIASES` (aggiunti gli alias estesi di
   coppa/Europa, es. `ACF Fiorentina`→`Fiorentina`, `SS Lazio`→`Lazio`); i club
   di Serie A non agganciati vengono **loggati**, non ignorati (**0** mancati
   aggancio, verificato).
3. Due colonne nello snapshot e nel DB, STESSA semantica di `add_rest_days` ma
   sul calendario COMPLETO: `home_rest_days_full`, `away_rest_days_full` (giorni
   dall'ultima partita di club di quella squadra in QUALSIASI competizione, cap
   14, solo partite precedenti → niente look-ahead, NaN se ignoto). Piu' due flag
   utili: `home_midweek_europe`, `away_midweek_europe` (gara europea/coppa nei 4
   giorni precedenti).

**Insidie risolte (registrate perche' si ripresentano).**
- Parser di date openfootball: la fase a **gironi** riparte da Settembre a ogni
  girone → un rollover ingenuo "mese tornato indietro = +1 anno" sballava le date
  (Juventus 2019-20 finiva nel 2022). Risolto con una regola **per semestre**
  (Set-Dic→anno d'inizio, Gen-Giu→anno di fine; Ago è preliminari salvo finali
  post-COVID già entrate in year1). Verificato: 0 date fuori finestra stagione.
- La **Coppa Italia** cambia formato tra stagioni (`Casa v Ospite` dal 2024-25,
  `Casa punteggio Ospite` prima): il parser gestisce entrambi.

**Risultato — copertura reale (onesta, verificata).**

| Stagione | Champions | Europa | Conference | Coppa Italia | Partite con congestione VERA catturata* |
|---|:--:|:--:|:--:|:--:|--:|
| 2017-18 | ✅ | — | — | — | 28 (7.4%) |
| 2018-19 | ✅ | — | — | — | 28 (7.4%) |
| 2019-20 | ✅ | — | — | — | 26 (6.8%) |
| 2020-21 | ✅ | ✅ | — | ✅ | 86 (22.6%) |
| 2021-22 | ✅ | ✅ | ✅ | ✅ | 98 (25.8%) |
| 2022-23 | ✅ | ✅ | ✅ | ✅ | 121 (31.8%) |
| 2023-24 | ✅ | ✅ | ✅ | ✅ | 104 (27.4%) |
| 2024-25 | ✅ | ✅ | ✅ | ✅ | 124 (32.6%) |
| 2025-26 | ✅ | — | — | — | 40 (10.5%) |

*(*) partite in cui almeno una squadra aveva una gara "nascosta" (coppa/Europa)
che accorcia il riposo rispetto al proxy solo-lega. **Totale: 655/3420 (19.2%).**
- **Champions League: tutte e 9 le stagioni.** Europa League dal 2020-21,
  Conference dal 2021-22, Coppa Italia 2020-21→2024-25 (openfootball non copre
  EL/Coppa prima, ne' la Coppa 2025-26): dove manca, quelle partite non entrano
  e `rest_days_full` **degrada in modo controllato** verso il valore solo-lega
  (mai in direzione sbagliata), `midweek_europe` puo' essere un falso 0. **Niente
  numeri inventati.**
- **Non-regressione**: impronta dati invariata (`8483944342fc8b15` — le nuove
  colonne non entrano nell'impronta, calcolata su date/squadre/gol); backtest
  2025-26 con la config ufficiale corrente (emivita 365g, Fase 4d) invariato
  (1X2 log-loss 0.9932). Il modello **non** legge ancora le colonne (covariate
  off di default): il dato è pronto, la validazione è il passo successivo.

**Invariante che ci fa fidare del dato.** Il calendario completo e' un
SOVRAINSIEME di quello di Serie A, quindi la partita precedente e' sempre >=:
→ `rest_days_full <= rest_days` (solo-lega) su ogni riga dove entrambi sono
definiti. Verificato su ~3400 partite: **0 violazioni**. Un bug di join o un
look-ahead romperebbero questa disuguaglianza — e' il nostro test di sicurezza.

**Limite onesto.** Il segnale utile (dove `rest_days_full < rest_days`) e'
concentrato nelle stagioni 2020-25 (EL/Conf/Coppa coperte) e per le squadre che
fanno le coppe. Nelle stagioni 2017-20 abbiamo solo la Champions: il test della
congestione sara' piu' potente sulle stagioni recenti. In locale, puntando gli
URL a una fonte per-squadra (FBref) si chiuderebbero i buchi senza toccare il
resto della pipeline.

**Prossimo passo (a cura dell'utente).** Aggiungere una covariata `rest_full` che
legge le nuove colonne e verificare walk-forward se la congestione VERA migliora
le previsioni dove il proxy solo-lega non ci riusciva (Fase 4c). Come sempre: il
diagnostico in-sample va confermato fuori campione, su piu' stagioni.

---

## Fase 4e-bis — Validazione della congestione VERA (walk-forward)

**Obiettivo.** Chiudere il cerchio della Fase 4c: ora che abbiamo il calendario
di club COMPLETO (Fase 4e), la fatica reale aiuta le previsioni dove il proxy
solo-Serie-A falliva?

**Ragionamento / ipotesi.** La Fase 4c aveva trovato la covariata `rest`
(riposo sul solo calendario di Serie A) *leggermente negativa*: non vedeva le
partite infrasettimanali di coppa/Europa, cioe' proprio quelle che causano la
fatica asimmetrica. Ipotesi: sostituendo la sorgente del calendario (Serie A →
completo) e lasciando **identico tutto il resto**, il segno dovrebbe migliorare.

**Alternative considerate.**
- *Config del modello*: riprodurre a emivita 730g (quella della Fase 4c) oppure
  usare la config ufficiale corrente (emivita 365g, Fase 4d). Scelto **365g**:
  e' il modello che usiamo davvero, e il confronto interno `rest` vs `rest_full`
  resta pulito perche' cambia **un solo fattore** (la sorgente del calendario).
- *Stagioni*: tutte e 9 oppure solo quelle con copertura reale delle coppe.
  Scelte le **5 stagioni 2020-21 → 2024-25** (`2021, 2122, 2223, 2324, 2425`):
  sono quelle in cui EL/Conference/Coppa Italia sono coperte e quindi
  `rest_days_full < rest_days` accade davvero (il limite onesto della Fase 4e).
  Sulle 2017-20 (solo Champions) e sul 2025-26 (coppe non ancora coperte) il
  segnale sarebbe quasi identico al proxy solo-lega: test poco potente.

**Scelta.** Aggiunta la covariata `rest_full` (`home/away_rest_days_full`,
trasformazione `identity`) accanto a `rest` in `_COVARIATES`; tripletta
walk-forward **baseline / rest / rest_full** sulle 5 stagioni, config ufficiale.
15 run registrati (`source=fase4e_congestione`), impronta dati invariata
(`8483944342fc8b15`).

**Risultato (1X2 log-loss, piu' basso = meglio; Δ = vs baseline).**

| Stagione | baseline | rest (solo lega) | rest_full (completo) | Δ rest | Δ rest_full |
|---|--:|--:|--:|--:|--:|
| 2020-21 | 0.9538 | 0.9549 | 0.9549 | +0.0011 | +0.0011 |
| 2021-22 | 0.9887 | 0.9891 | 0.9862 | +0.0004 | **−0.0025** |
| 2022-23 | 0.9943 | 0.9940 | 0.9933 | −0.0002 | **−0.0010** |
| 2023-24 | 0.9848 | 0.9862 | 0.9849 | +0.0013 | +0.0001 |
| 2024-25 | 0.9695 | 0.9700 | 0.9701 | +0.0005 | +0.0005 |
| **MEDIA** | **0.9782** | **0.9788** | **0.9779** | **+0.0006** | **−0.0004** |

(Mercato medio: 0.9601 — nessuna variante lo avvicina.)

**Lezione / cosa ne consegue.**
1. Il calendario completo **inverte il segno** rispetto al proxy solo-lega: `rest`
   peggiorava (+0.0006 medio, conferma della Fase 4c), `rest_full` migliora di un
   soffio (−0.0004 medio). La diagnosi della Fase 4c era corretta: il problema era
   la *sorgente*, non l'idea della congestione.
2. Ma il guadagno e' **minuscolo e incoerente**: aiuta 2 stagioni su 5 (le due a
   copertura piu' piena, 2021-22 e 2022-23), e' neutro/negativo sulle altre;
   l'ordine di grandezza (±0.001 su log-loss) e' **dentro il rumore**. Non basta
   per adottarlo nella config ufficiale, e **non tocca il divario col mercato**.
3. Coerente con lo stato del progetto: **il modello e' al tetto pratico dei dati
   attuali**. La fatica reale e' un segnale vero ma debolissimo, probabilmente
   gia' in gran parte implicito in gol+xG recenti (la stanchezza si vede nei
   risultati). Config ufficiale **invariata**; covariata `rest_full` disponibile
   (off di default) per dati futuri a copertura piena (es. calendario per-squadra
   FBref, che chiuderebbe i buchi 2017-20 e 2025-26).

**Riproducibilita'.** `python scripts/_run_fase4e_congestione.py` (tripletta su 5
stagioni), oppure per singola cella: `python scripts/backtest.py --test-season 2122
--covariates rest_full`.

---

## Fase 6 — Ricalibrazione della confidenza (temperature scaling, NEGATIVO-ish)

**Obiettivo.** Spremere il modello attuale SENZA dati nuovi. Il diagnostico
(`scripts/analyze.py`, stagione 2024-25) diceva: il modello e' calibrato sulla
media ma perde contro il mercato dove e' molto sicuro (+0.034) e sulle
neopromosse (+0.029). La leva piu' economica per il primo problema e' il
**temperature scaling**: un SOLO parametro T che rende le probabilita' piu'
nette (T<1) o piu' morbide (T>1), tarato sul passato e applicato al futuro.

**Ragionamento / ipotesi.** Se il modello e' troppo sicuro, T>1 (raffredda)
riduce la log-loss. La tabella di calibrazione per fascia suggeriva invece il
contrario (probabilita' un po' "compresse" verso l'uniforme): da verificare
tarando T empiricamente, senza pregiudizi.

**Alternative considerate.**
- *Cosa tarare*: un T globale (scelto: la versione piu' economica), oppure una
  calibrazione per-fascia/isotonica (piu' parametri, piu' rischio di overfit su
  ~380 partite/stagione). Prima la versione economica, da protocollo.
- *Come evitare il look-ahead*: T si tara SOLO sulle predizioni walk-forward
  delle stagioni PRECEDENTI a quella di test (leave-future-out), mai su quella di
  test. Nuovo modulo puro `src/evaluation/calibration.py` (fit/apply) + test.

**Risultato (1X2 log-loss, T tarato sul passato di ogni stagione).**

| Stagione | T | base | calibrato | Δ |
|---|--:|--:|--:|--:|
| 2020-21 | 0.963 | 0.9538 | 0.9526 | −0.0012 |
| 2021-22 | 0.918 | 0.9887 | 0.9903 | +0.0016 |
| 2022-23 | 0.948 | 0.9943 | 0.9948 | +0.0005 |
| 2023-24 | 0.962 | 0.9848 | 0.9843 | −0.0005 |
| 2024-25 | 0.955 | 0.9695 | 0.9681 | −0.0014 |
| 2025-26 | 0.937 | 0.9932 | 0.9925 | −0.0007 |
| **MEDIA** | **~0.94** | **0.9807** | **0.9804** | **−0.0003** |

(Mercato medio: 0.9632 — la calibrazione non lo tocca.)

**Lezione / cosa ne consegue.**
1. Scoperta reale e **robusta**: **T < 1 in tutte e 6 le stagioni** (0.92–0.96).
   Il modello e' **sistematicamente un po' SOTTOconfidente** — le probabilita'
   vanno rese un filo piu' nette, non piu' morbide (l'opposto dell'ipotesi
   "troppo sicuro": l'eccesso di confidenza del diagnostico e' concentrato in
   poche partite estreme, non nella distribuzione media).
2. Ma il guadagno e' **trascurabile** (−0.0003 medio su log-loss, −0.0002 Brier)
   e **non uniforme** (peggiora 2 stagioni su 6: dove i pronostici sicuri
   sbagliavano di piu', rendere le prob piu' nette punisce). Rendere piu' nette
   le probabilita' e' un'arma a doppio taglio: premia quando il modello ha
   ragione, punisce di piu' quando ha torto — in Serie A i due effetti quasi si
   annullano.
3. Coerente con congestione (Fase 4e-bis) e valori-rosa (Fase 4c): **effetto
   reale, direzione coerente, payoff nel rumore**. Il modello e' al tetto. La
   calibrazione **non entra** nella config ufficiale (guadagno < rumore, e
   inconsistente); il modulo resta disponibile per un uso pratico (probabilita'
   leggermente piu' oneste su singola partita) e per dati/mercati futuri.

**Riproducibilita'.** `python scripts/calibrate.py` (validazione walk-forward su
tutte le stagioni; registra 6 run con `source=calibrate_temperature`).

**Prossimo (se si vuole continuare a spremere).** La perdita piu' grande e
concentrata resta le **neopromosse** (+0.029 su ~28% delle partite): un prior di
cold-start e' la leva con l'aspettativa migliore rimasta dentro il modello
attuale.

---

## Fase 7 — Prior di cold-start per le neopromosse (il miglior guadagno interno)

**Obiettivo.** Aggredire la perdita piu' grande e concentrata individuata dal
diagnostico: le **neopromosse** (+0.029 di log-loss su ~28% delle partite). Il
modello, senza storico recente di Serie A per Como/Parma/Venezia..., le tratta
come squadre di media forza e le **sovrastima**.

**Ragionamento / ipotesi.** Le neopromosse sono strutturalmente piu' deboli
(vengono dalla Serie B). Se diamo loro un **prior** sotto la media finche' non
accumulano partite, il modello smette di sovrastimarle. Misura economica prima
di costruire (protocollo): su tutte le 24 neopromosse 2018-2026, segnano in media
**1.08 gol/partita vs 1.36 della lega** (−20%) e ne subiscono **1.72** (+26%), in
modo consistente. In unita' di log-tasso: **δ ≈ 0.23** su attacco e difesa.

**Alternative considerate.**
- *Dove iniettare il prior*: (a) dati-fantasma per le promosse; (b) shrinkage
  extra verso la media; (c) **spostare il bersaglio dello shrinkage** verso un
  valore sotto la media. Scelto (c): riusa il meccanismo di shrinkage gia' nel
  modello (penalita' L2 fissa), cambia solo il *bersaglio* per le promosse da 0 a
  (−δ_att, +δ_def). Elegante: una promossa con **0 partite** finisce esattamente
  sul prior; man mano che gioca, i dati lo sovrastano allo stesso ritmo con cui
  lo shrinkage cede su qualsiasi squadra. Le promosse entrano nel modello anche a
  0 partite (inizio stagione), non piu' trattate come "sconosciute = media".
- *δ fisso vs stimato*: per evitare il look-ahead, δ e' stimato **leave-future-out**
  (per la stagione S, solo dalle promosse delle stagioni < S). Applicato sia al
  modello-gol sia al modello-xG del blend (la promossa e' piu' debole in entrambi).

**Scelta.** Parametro `promoted_prior=(δ_att, δ_def)` nel modello + set
`promoted_teams` passato a `fit` (calcolato dal backtest: presenti nella stagione
di test, assenti nella precedente). Flag CLI `--promoted-prior DELTA`.

**Risultato (1X2 log-loss, δ leave-future-out, 6 stagioni 2020-25 → 2025-26).**

| Stagione | δ (att, def) | TUTTE base | TUTTE prior | Δ | NEOPROM base | NEOPROM prior | Δ |
|---|:--:|--:|--:|--:|--:|--:|--:|
| 2020-21 | (0.27, 0.23) | 0.9538 | 0.9533 | −0.0006 | 0.9475 | 0.9454 | −0.0022 |
| 2021-22 | (0.26, 0.26) | 0.9887 | 0.9858 | −0.0029 | 0.9835 | 0.9736 | −0.0099 |
| 2022-23 | (0.28, 0.26) | 0.9943 | 0.9914 | −0.0028 | 1.0291 | 1.0188 | −0.0103 |
| 2023-24 | (0.27, 0.24) | 0.9848 | 0.9855 | +0.0007 | 0.9767 | 0.9792 | +0.0025 |
| 2024-25 | (0.25, 0.23) | 0.9695 | 0.9693 | −0.0002 | 1.0250 | 1.0241 | −0.0009 |
| 2025-26 | (0.24, 0.21) | 0.9932 | 0.9925 | −0.0008 | 0.9661 | 0.9634 | −0.0027 |
| **MEDIA** | | **0.9807** | **0.9796** | **−0.0011** | **0.9880** | **0.9841** | **−0.0039** |

**Lezione / cosa ne consegue.**
1. **Il miglior guadagno interno trovato finora.** −0.0011 medio complessivo
   (3-4× congestione −0.0004 e calibrazione −0.0003) e **−0.0039** dove doveva
   colpire (partite con una neopromossa). Migliora **5 stagioni su 6** sia
   complessivamente sia sul sottoinsieme. E' principiato (fatto strutturale), non
   un parametro tirato a caso.
2. **Non e' gratis ovunque**: il 2023-24 peggiora (+0.0007) perche' quel trio di
   promosse (Genoa/Cagliari/Frosinone) era piu' vicino alla media — il prior le
   sotto-stima. E' la varianza attesa: il prior scommette sulla regola generale,
   e ogni tanto la promossa e' buona.
3. **Resta piccolo e NON batte il mercato** (0.9796 vs ~0.963): utile per
   previsioni piu' oneste su partite reali (soprattutto inizio stagione e squadre
   neopromosse), non per un edge.
4. **Adozione**: e' l'unico dei tre esperimenti "di spremitura" che supera il
   rumore in modo consistente ed e' principiato → **ADOTTATO nella config
   ufficiale** (δ=0.23, default in `backtest.py`; `--promoted-prior 0` per
   disattivarlo). La decisione arriva dopo aver chiuso le altre leve economiche
   (Fase 8): siccome non c'e' altro da spremere, non c'e' motivo di tenere spento
   l'unico guadagno reale.

**Riproducibilita'.** `python scripts/_run_fase7_promosse.py` (validazione su 6
stagioni, δ leave-future-out), oppure singola cella:
`python scripts/backtest.py --test-season 2122 --promoted-prior 0.23`.

---

## Fase 8 — Ultimo giro economico (shrinkage, vantaggio-casa): niente da spremere

**Obiettivo.** Prima di dichiarare il modello "al tetto", chiudere le due ultime
leve economiche interne rimaste, una alla volta e misurando.

**#1 — Ri-taratura dello shrinkage col prior attivo.** Lo shrinkage ufficiale
(1.5) era stato tarato in Fase 4d *senza* il prior; con il cold-start ora gestito
dal prior, l'ottimo potrebbe spostarsi. Sweep 0.75→3.0 su 6 stagioni con
`--promoted-prior 0.23` (`scripts/tune.py`, 30 run registrati):

| shrinkage | 0.75 | 1.0 | 1.5 | 2.0 | 3.0 |
|---|--:|--:|--:|--:|--:|
| media 1X2 log-loss | 0.9797 | 0.9797 | 0.9797 | 0.9798 | 0.9803 |

**Curva piatta** tra 0.75 e 1.5 (ottimo nominale 1.0, ma a 0.00002 da 1.5 =
rumore). **Le due leve sono ortogonali**: il prior gestisce il cold-start, lo
shrinkage nell'intervallo utile non ci si combina. Nessun guadagno → shrinkage
resta 1.5.

**#2 — Vantaggio-casa per-squadra (versione economica prima di costruire).** Idea:
dare a ogni squadra il proprio vantaggio-casa invece di uno globale. Test a
costo zero PRIMA della chirurgia sul modello: il vantaggio-casa per-squadra e'
**stabile** anno su anno? Misura (proxy = punti/gara in casa − fuori, tutte le
team-stagioni 2017-2026):
- effetto medio **0.254 punti/gara** (l'effetto GLOBALE esiste — ed e' gia' nel
  modello come `home_adv` globale, che il fit pesato nel tempo fa anche driftare
  post-COVID);
- ma la **persistenza anno-su-anno e' r ≈ 0.004** (n=136 coppie squadra): il
  "forte in casa" di una stagione e' scorrelato dalla successiva.

Con persistenza nulla, un vantaggio-casa per-squadra **fitterebbe solo rumore
stagionale e non generalizzerebbe** al futuro → l'idea muore prima della
chirurgia (principio: testa la versione economica prima di investire).

**Lezione / cosa ne consegue.** Le due ultime leve economiche sono **entrambe
negative**: #1 piatto, #2 rumore non persistente. Sommato ai risultati di
congestione (Fase 4e-bis) e calibrazione (Fase 6), la conclusione e' solida: il
modello Dixon-Coles gol+xG e' al **tetto pratico dei dati attuali**. Il prior
neopromosse (−0.0011) resta l'unico guadagno interno reale, ed e' ora nella
config ufficiale. Il prossimo passo di valore non e' un altro ritocco interno ma
un **cambio di classe** (es. Poisson bivariato per la correlazione dei punteggi /
GG/NG) o l'**uso pratico** del modello.

**Riproducibilita'.** #1: `python scripts/tune.py --sweep shrinkage --values 0.75
1.0 1.5 2.0 3.0 --seasons 2021 2122 2223 2324 2425 2526 --promoted-prior 0.23`.

---

## Fase 9 — Anatomia del gap col mercato (analisi approfondita)

**Obiettivo.** Non "spremere" ma **capire**: quanto vale oggi il divario col
mercato, e come si scompone per stagione, per mercato e per forza delle squadre.
E come si e' ridotto lungo l'evoluzione del modello (dal grezzo all'attuale).
Definizione: **gap = log-loss modello − log-loss mercato** (>0 = mercato meglio;
piu' vicino a 0 = meglio). Tutto walk-forward, 6 stagioni (2020-21→2025-26),
riproducibile con `scripts/analyze_gap.py`.

**Il gap oggi (versione ATTUALE, 1X2).** Modello **0.9797** vs mercato **0.9632**
→ **gap medio +0.0165** di log-loss. Per dare una scala: la baseline banale sta a
~1.085 (gap +0.12), quindi il modello ha gia' chiuso ~**87%** della distanza
baseline→mercato; l'ultimo 13% e' la parte dura.

**1) Evoluzione — il gap 1X2 lungo le versioni (media 6 stagioni).**

| Versione | gap 1X2 | Δ vs precedente |
|---|--:|--:|
| V0 grezzo (gol, no shrink/no decay) | +0.0236 | — |
| V1 gol tarato (shrinkage+emivita, Fase 2b) | +0.0185 | **−0.0051** |
| V2 +xG nel blend (Fase 4b) | +0.0181 | −0.0004 |
| V3 emivita ri-tarata 365g (Fase 4d) | +0.0175 | −0.0006 |
| V4 +prior neopromosse (Fase 7, ATTUALE) | +0.0165 | −0.0010 |

Lezione: il grosso del recupero (**−0.0051 su −0.0071 totali, il 72%**) e' venuto
dalla **regolarizzazione+memoria** (Fase 2b). xG, ri-taratura e prior hanno
limato il resto (−0.0020 combinato). Dopo il tuning di base, i dati e i ritocchi
danno rendimenti decrescenti — coerente col "tetto".

**2) Per STAGIONE (versione attuale, gap 1X2).**

| 2020-21 | 2021-22 | 2022-23 | 2023-24 | 2024-25 | 2025-26 |
|--:|--:|--:|--:|--:|--:|
| +0.0202 | +0.0145 | +0.0146 | +0.0187 | +0.0170 | +0.0141 |

**Sì, varia** (da +0.014 a +0.020). La peggiore e' la **2020-21** (COVID, stadi
vuoti: piu' rumore, vantaggio-casa anomalo). Le piu' recenti (2021-22, 2025-26)
sono le migliori. Nessuna stagione batte il mercato sull'1X2.

**3) Per MERCATO (versione attuale, pool 6 stagioni).**

| Mercato | gap | note |
|---|--:|---|
| **1X2** | +0.0165 | quote dirette |
| **1X** (casa o pari) | +0.0116 | quota derivata 1X2 |
| **2X** (ospite o pari) | +0.0127 | quota derivata 1X2 |
| **12** (no pareggio) | **+0.0020** | quota derivata 1X2 |
| **Over/Under 2.5** | +0.0069 | quote dirette |
| GG/NG | −0.0018 (vs baseline) | **niente quote nei dati** |

**Scoperta chiave: il gap e' quasi tutto nel PAREGGIO.** Il mercato **12**
(vince una delle due, si esclude il pari) ha gap **+0.0020**, cioe' il modello e'
praticamente a livello mercato quando NON deve prezzare il pareggio. Appena il
pari rientra (1X, 2X, 1X2) il gap triplica/quadruplica. Tradotto: la nostra
debolezza vs mercato e' **prezzare i pareggi** (i punteggi bassi correlati), non
stimare chi e' piu' forte. **Over/Under** e' quasi competitivo (+0.0069, e in
2020-21 il modello lo batte: −0.0031). GG/NG non ha quote nei dati: vs baseline
il modello e' ~pari (oscilla per stagione, rumore).

**4) Per FORZA delle squadre (versione attuale, gap 1X2; una partita conta per
entrambe le squadre coinvolte).**

| Gruppo (tier da classifica) | n | gap medio 1X2 |
|---|--:|--:|
| forte (top 6) | 1368 | +0.0180 |
| media (7°-14°) | 1824 | +0.0123 |
| debole (bottom 6) | 1368 | **+0.0206** |
| neopromossa (sottoinsieme) | 648 | +0.0159 |

**Sì, varia, con una U:** il modello perde di piu' sulle **squadre deboli**
(+0.0206) e sulle **forti** (+0.0180), meno sulle **medie** (+0.0123). Sui deboli
il mercato ha informazione che noi non abbiamo (motivazione salvezza, turnover,
episodi); sui forti conta molto la forma/rotazioni nelle coppe. Le neopromosse
(+0.0159) sono ora **sotto** la media dei deboli grazie al prior della Fase 7
(senza prior sarebbero il gruppo peggiore).

**5) Per FAVORITISMO di mercato (versione attuale, gap 1X2).**

| Partita | n | gap medio 1X2 |
|---|--:|--:|
| equilibrata (favorito <45%) | 799 | +0.0167 |
| moderata (45-60%) | 852 | +0.0173 |
| netta (favorito >60%) | 629 | +0.0152 |

Qui la variazione e' **piccola**: il gap e' abbastanza uniforme, leggermente
minore quando c'e' un favorito netto (+0.0152, modello e mercato concordano di
piu'). Non e' l'asse dove si nasconde il divario.

**Lezione / cosa ne consegue.**
1. Il gap medio 1X2 e' **+0.0165** e non e' uniforme: peggiore su **stagioni
   rumorose (COVID)**, su **squadre deboli/forti**, e — soprattutto — **sul
   pareggio** (il mercato 12 senza pari e' gia' a livello mercato).
2. Questo **punta il dito** sul prossimo passo con la miglior aspettativa
   *dentro un cambio di classe*: **modellare la correlazione dei punteggi**
   (es. Poisson bivariato / dipendenza sui punteggi bassi oltre la correzione DC),
   che e' esattamente cio' che serve per prezzare meglio pareggio e GG/NG. Non e'
   un ritocco: e' la mossa mirata suggerita dai numeri.
3. Il resto del gap (deboli/forti, stagioni rumorose) e' **informazione che il
   mercato ha e noi no** e difficilmente si chiude coi dati storici attuali.

**Riproducibilita'.** `python scripts/analyze_gap.py` (5 versioni × 6 stagioni,
scomposizione per stagione/mercato/forza/favoritismo).

### Fase 9-bis — COVID vs post-COVID e trend recente

**Obiettivo.** Il gap 1X2 peggiore era il 2020-21: e' un effetto COVID (stadi
vuoti) o solo la stagione piu' vecchia? E negli ultimi anni dove sta andando?
Periodi: **COVID** = 2020-21 (stadi vuoti tutta la stagione); **transizione** =
2021-22 (capienza ridotta/Omicron); **post-COVID** = 2022-23→2025-26.

**Gap per periodo (versione attuale; GG/NG vs baseline, no quote).**

| Periodo | 1X2 | 1X | 2X | 12 | O/U 2.5 | GG/NG |
|---|--:|--:|--:|--:|--:|--:|
| COVID (2020-21) | +0.0202 | +0.0160 | +0.0151 | +0.0017 | **−0.0031** | +0.0074 |
| transizione (2021-22) | +0.0145 | +0.0082 | +0.0105 | +0.0031 | +0.0147 | −0.0054 |
| post-COVID (2022-26) | +0.0161 | +0.0114 | +0.0127 | +0.0018 | +0.0074 | +0.0035 |
| **Δ (post − COVID)** | **−0.0041** | −0.0047 | −0.0024 | +0.0001 | **+0.0104** | −0.0039 |

**Due movimenti opposti.**
1. **Mercati d'ESITO (1X2/1X/2X): il gap si RIDUCE dopo il COVID** (1X2 da +0.0202
   a +0.0161). Ipotesi: a stadi vuoti il **vantaggio-casa e' crollato**; il
   modello lo eredita dallo storico "normale" e sovra-pesava le squadre di casa,
   mentre il mercato si adeguava piu' in fretta → gap piu' largo. (Confuso in
   parte col fatto che 2020-21 e' la stagione con meno storico di training.)
   Tornato il pubblico, il gap si e' richiuso. Collega la Fase 8: il vantaggio-
   casa GLOBALE conta e drifta, ma quello per-squadra e' rumore — coerente.
2. **Over/Under: l'OPPOSTO. Nel COVID il modello BATTEVA il mercato** (−0.0031),
   post-COVID il mercato e' tornato affilato (+0.0074, Δ +0.0104). I totali
   risentono meno del pubblico; in quella stagione anomala le quote O/U erano
   verosimilmente meno precise. (Cautela: un solo campione COVID, 380 partite.)
3. **12 (senza pari): a livello mercato in ogni periodo** (~+0.002). La debolezza
   sul pareggio non e' un effetto COVID: e' strutturale.

**Trend ultime 3 stagioni (gap; ↓ = migliora).**

| Mercato | 2023-24 | 2024-25 | 2025-26 | Δ(25/26−23/24) |
|---|--:|--:|--:|--:|
| 1X2 | +0.0187 | +0.0170 | +0.0141 | **−0.0046 ↓** |
| 1X | +0.0175 | +0.0082 | +0.0108 | −0.0066 ↓ |
| 2X | +0.0128 | +0.0156 | +0.0096 | −0.0031 ↓ |
| 12 | −0.0021 | +0.0050 | +0.0022 | +0.0043 ↑ (ma ~mercato) |
| O/U 2.5 | +0.0007 | +0.0101 | +0.0020 | +0.0013 ≈ rumoroso |
| GG/NG | −0.0003 | +0.0037 | +0.0039 | +0.0042 ↑ (vs baseline) |

**Lezione.** I **mercati d'esito stanno migliorando**: il gap 1X2 e' al **minimo
nell'ultima stagione (2025-26: +0.0141)**, in calo netto dalle tre precedenti
(aiutano prior neopromosse e maturazione dell'xG). Il **12 resta incollato al
mercato** ovunque. **O/U e GG/NG oscillano vicino a zero** senza trend. La parte
che si chiude e' quella d'esito; quella che non si muove e' il **pareggio** —
ancora una volta il dito punta sulla correlazione dei punteggi.

**Riproducibilita'.** `python scripts/_run_gap_covid.py`.

---

## Fase 10 — Ricalibrazione per-classe 1X2 (attacca il pareggio; robusto ma piccolo)

**Obiettivo.** Sfruttare la pista mirata della Fase 9: il gap col mercato e'
concentrato nel PAREGGIO e la calibrazione media mostra **casa sovrastimata /
pari sottostimato**. Il temperature scaling (Fase 6) non poteva correggerlo
(scala tutto in modo uniforme, non sposta massa tra esiti). Tre moltiplicatori
per classe (casa/pari/ospite) si'.

**Ragionamento.** `q_i ∝ w_i·p_i`, rinormalizzato; solo i rapporti contano, si
fissa `w_ospite=1` (2 parametri). Pesi tarati SOLO sulle stagioni precedenti
(leave-future-out) e applicati alla stagione di test. Modello = ufficiale ATTUALE
(gol+xG+prior). Nuove funzioni in `src/evaluation/calibration.py`.

**Risultato (1X2 log-loss; pesi normalizzati a media geometrica 1).**

| Stagione | w_casa | w_pari | w_ospite | base | rical. | Δ | gap→mercato |
|---|--:|--:|--:|--:|--:|--:|--:|
| 2020-21 | 0.981 | 1.037 | 0.983 | 0.9532 | 0.9532 | −0.0000 | +0.0202 |
| 2021-22 | 0.970 | 1.029 | 1.001 | 0.9860 | 0.9847 | −0.0013 | +0.0131 |
| 2022-23 | 0.949 | 1.036 | 1.017 | 0.9916 | 0.9920 | +0.0004 | +0.0150 |
| 2023-24 | 0.960 | 1.040 | 1.001 | 0.9854 | 0.9840 | −0.0015 | +0.0172 |
| 2024-25 | 0.962 | 1.060 | 0.981 | 0.9693 | 0.9682 | −0.0011 | +0.0159 |
| 2025-26 | 0.960 | 1.061 | 0.982 | 0.9925 | 0.9932 | +0.0007 | +0.0148 |
| **MEDIA** | **~0.96** | **~1.04** | **~0.99** | **0.9797** | **0.9792** | **−0.0005** | **+0.0160** |

**Lezione / cosa ne consegue.**
1. **Diagnosi confermata, robusta**: in TUTTE e 6 le stagioni il fit **abbassa la
   casa (w≈0.96) e alza il pareggio (w≈1.04-1.06)**. Il modello sovrastima
   sistematicamente le vittorie di casa e sottostima i pari — esattamente la
   miscalibrazione direzionale del diagnostico (Fase 9). Piu' informativo del
   temperature (che poteva solo scaldare/raffreddare).
2. **Payoff piccolo e non uniforme**: −0.0005 medio (gap 1X2 +0.0165→+0.0160),
   aiuta 4 stagioni su 6, peggiora 2 (incl. la piu' recente). E' un po' meglio
   del temperature (−0.0003) ma sempre ai margini del rumore. **Non entra nella
   config ufficiale** (come il temperature); le funzioni restano per l'uso pratico
   (probabilita' 1X2 un filo piu' oneste su singola partita).
3. **Perche' cosi' poco?** La ricalibrazione per-classe e' un surrogato *lineare
   e globale* di cio' che servirebbe davvero: modellare la **correlazione dei
   punteggi** partita-per-partita (la probabilita' del pari dipende dai tassi
   attesi, non e' un fattore costante). Spreme lo strato "medio" della
   miscalibrazione (−0.0005), ma il residuo e' strutturale. **Quinto esperimento
   interno di fila con guadagno nel rumore**: la conclusione e' definitiva —
   dentro questo modello e questi dati il margine e' esaurito, e ogni analisi
   punta allo stesso salto (Poisson bivariato).

**Riproducibilita'.** `python scripts/_run_class_recal.py`.

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
