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

### 📐 Il modello in dettaglio — cosa significa "modellare i gol"

La scelta di fondo ("modellare la distribuzione dei gol per squadra") ha una forma
matematica precisa, presa da Dixon & Coles (1997). Per una partita casa `h` vs
ospite `a`, i gol delle due squadre sono due Poisson i cui tassi attesi sono:

```
λ = E[gol casa]   = exp( att_h + dif_a + γ )
μ = E[gol ospite] = exp( att_a + dif_h )
```

- `att_·` = forza d'attacco della squadra (in **log-scala**), `dif_·` = forza di
  difesa (quanto fa segnare gli altri), `γ` = **vantaggio-casa** globale.
- **Perché la scala esponenziale (log-lineare)?** Tre motivi concreti: (1) garantisce
  `λ, μ > 0` (non esistono gol attesi negativi); (2) rende i contributi *additivi in
  log e moltiplicativi in gol* — una squadra "+0,30 in attacco" segna `e^0.30 ≈ 1,35`
  volte tanto contro *qualsiasi* difesa, coerente con l'intuizione "i forti segnano di
  più contro tutti"; (3) è la parametrizzazione canonica del GLM di Poisson, quindi la
  massima verosimiglianza è ben posta.
- **Perché i gol per squadra e non i mercati direttamente?** Se stimassi 1X2 e O/U con
  due modelli separati potrei ottenere `P(vittoria casa)=55%` **e** `P(Under 2.5)=70%`
  reciprocamente incoerenti. Partendo dalla matrice `P(gol_casa=i, gol_ospite=j)` ogni
  mercato è una *somma di celle* della stessa matrice → coerenza garantita per
  costruzione, e ogni nuovo mercato è gratis (basta sommare le celle giuste).

I valori numerici di `att`, `dif`, `γ`, `ρ` non esistono ancora in questa fase: sono
**stimati dai dati** nella Fase 1 (massima verosimiglianza). Qui è fissata solo la
*forma*; il *perché quei numeri* arriva col primo fit.

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

### 📐 Il modello in dettaglio — tutte le formule del tracer bullet

Questa è la fase in cui il modello passa da *forma* (Fase 0) a *numeri stimati*.
Ecco l'intera catena, come è scritta in `src/models/dixon_coles.py`.

**1) Verosimiglianza pesata (la funzione che il fit minimizza).** I parametri
`{att_i, dif_i, γ, ρ}` sono scelti massimizzando la log-verosimiglianza di Poisson
sui gol osservati, **pesata nel tempo**:

```
ℓ = Σ_partite  w_t · [  (g_h·ln λ − λ)  +  (g_a·ln μ − μ)  +  ln τ(g_h, g_a; λ, μ, ρ)  ]
```

dove `g_h, g_a` sono i gol realmente segnati, e i due termini `(g·ln rate − rate)`
sono il nucleo della Poisson (il fattoriale `ln(g!)` è costante e si può ignorare
nell'ottimizzazione, ma nel codice è incluso per completezza).

**2) Peso temporale `w_t` (decadimento).** Una partita giocata `Δ` giorni prima del
momento della predizione pesa:

```
w_t = exp( −ξ · Δ ),   con   ξ = ln 2 / emivita
```

Così il peso si **dimezza ogni `emivita` giorni**: a emivita 365g una gara di una
stagione fa pesa 0,5, di due stagioni 0,25, di tre 0,125. È il meccanismo con cui
"le squadre cambiano nel tempo" entra nel modello *senza buttare via* i dati vecchi
(li sfuma soltanto). Il valore di emivita è un iperparametro, tarato in Fase 2b.

**3) Correzione Dixon-Coles `τ` sui 4 punteggi bassi.** La Poisson pura sottostima
0-0/1-1 e sovrastima 1-0/0-1; `τ` corregge SOLO quelle 4 celle:

```
τ(0,0) = 1 − λ·μ·ρ      τ(0,1) = 1 + λ·ρ
τ(1,0) = 1 + μ·ρ        τ(1,1) = 1 − ρ         (tutti gli altri punteggi: τ = 1)
```

Con `ρ < 0` (il valore che i dati scelgono, tipicamente −0,04…−0,07): `τ(0,0)` e
`τ(1,1)` diventano **>1** (più massa su 0-0 e 1-1, cioè più pareggi bassi) mentre
`τ(0,1), τ(1,0)` diventano **<1**. È esattamente il "le squadre giocano sul
risultato". `ρ` è stimato *dentro* la verosimiglianza, non imposto.

**4) Identificabilità.** Il modello è invariante se sommo una costante a tutti gli
attacchi e la sottraggo a tutte le difese (`att_i += c`, `dif_i −= c` non cambia
`λ, μ`). Si fissa l'indeterminazione con una penalità che impone **media(attacco) =
0**: `penalità = 10⁴ · media(att)²`. È il motivo per cui "forza 0 = squadra media
della lega".

**5) Dalla matrice ai mercati.** Con `(λ, μ)` stimati si costruisce la matrice
`P(i,j) = Poisson(i; λ) · Poisson(j; μ) · τ(i,j)` (troncata a 10 gol/squadra e
rinormalizzata perché `τ` e il troncamento rompono la somma a 1). Da essa:

```
P(1) = Σ_{i>j} P(i,j)   (triangolo inferiore)      P(X) = Σ_i P(i,i)  (diagonale)
P(2) = Σ_{i<j} P(i,j)   (triangolo superiore)
P(Over 2.5) = Σ_{i+j ≥ 3} P(i,j)                   P(GG) = Σ_{i≥1, j≥1} P(i,j)
```

**6) Come si misura (le metriche).** Log-loss 1X2 = `−media( ln P(esito realizzato) )`
(punisce duramente la sicurezza sbagliata); Brier = `media Σ_k (p_k − y_k)²`.

**Perché quei tre numeri (1.0047 / 1.0851 / 0.9784).**
- Il **mercato (0.9784)** è la log-loss delle quote di chiusura *devigate*: le quote
  1X2 si convertono in probabilità con `p_i = (1/quota_i) / Σ_j(1/quota_j)` (metodo
  moltiplicativo: dividere per la somma toglie il margine del bookmaker, che rende
  `Σ 1/quota > 1`). È lo stimatore più efficiente esistente → il numero da battere.
- La **baseline (1.0851)** è la log-loss del predittore banale costante = frequenze
  empiriche (H,D,A) della stagione. Batterla significa "il modello discrimina le
  singole partite meglio del prezzo medio di lega".
- Il **modello (1.0047)** sta **in mezzo**: `1.0851 > 1.0047 > 0.9784`. Ha già chiuso
  `(1.0851−1.0047)/(1.0851−0.9784) = 75%` della distanza baseline→mercato al primo
  colpo, senza tuning. È il risultato "sano" atteso: impara qualcosa di reale, non
  ancora abbastanza da battere il prezzo.

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

### 📐 Il modello in dettaglio — come si misura "dove si perde"

**Definizione operativa del "gap" (usata da qui fino alla Fase 33).** Per ogni
sottoinsieme di partite S:

```
gap(S) = media_{p ∈ S} [ log-loss_modello(p) − log-loss_mercato(p) ]
```

`>0` = il mercato è più accurato; `≈0` = pari; `<0` = il modello batte il mercato.
Il gap medio globale in questa fase è ~+0.018; sulle **neopromosse è +0.037** (il
doppio) e a **inizio stagione +0.030**. Non sono numeri inventati: sono la stessa
media, ristretta alle righe di quel gruppo.

**Perché "calibrato in media ma battuto in discriminazione".** La calibrazione si
misura a *fasce*: si raggruppano le predizioni per probabilità stimata (es. "partite
dove il modello dà 50-60% alla casa") e si confronta la probabilità media stimata con
la **frequenza reale** in quella fascia. Erano allineate → nessun bias sistematico
(nemmeno sul pareggio, il difetto tipico della Poisson pura, che qui la correzione
`τ` con `ρ<0` già evita). Ma calibrazione ≠ discriminazione: il mercato assegna
probabilità *diverse e più giuste alle singole partite*. Due modelli possono avere la
stessa calibrazione media e log-loss diversa; il gap vive lì.

**Perché il gap esplode sulle neopromosse — il meccanismo del bug e della debolezza
strutturale.** Una squadra **mai vista nel training** riceve `att = dif = 0` (la
media di lega, per la penalità di identificabilità della Fase 1). Due conseguenze:
1. *Il bug degli alias.* Il Verona era `"Verona"` nel training e `"Hellas Verona"`
   nel test: due stringhe diverse → il modello lo trattava come **sconosciuto →
   forza media** invece che come la squadra (debole) che era. Da qui predizioni
   sbilanciate e troppo sicure. Corretto con `TEAM_ALIASES` (mappa di
   normalizzazione). *Nota onesta:* l'esatto "87%" citato dipende dalla singola
   partita e non è ri-derivabile dai dati aggregati qui riportati — è un esempio
   illustrativo del sintomo, non una cifra da registro.
2. *La debolezza vera (non un bug).* Anche con gli alias giusti, una neopromossa con
   0-poche partite di Serie A resta ancorata a `forza ≈ 0` (media), mentre in realtà
   è **sotto** la media (viene dalla B). Il modello la **sovrastima** → gap alto.
   È il problema che le Fasi 2b (shrinkage) e 7 (prior) attaccano direttamente.

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

| Config | log-loss 1X2 | gap col mercato |
|---|---:|---:|
| Dixon-Coles puro (media 2 stagioni) | 0.9918 | +0.026 |
| + shrinkage 1.5 (media 2 stagioni) | 0.9879 | +0.022 |
| + shrinkage, emivita 180g (media 3 stagioni) | 0.9863 | +0.021 |
| + emivita 730g (media 3 stagioni) | **0.9829** | **+0.017** |

*(Mercato: 0.9654 sulle 2 stagioni, 0.9658 sulle 3. Nota audit Fase 15: la
versione precedente di questa tabella attribuiva al "puro" il valore 0.9863 con
gap +0.026 — internamente impossibile; il +0.026 appartiene al valore a 2
stagioni 0.9918, il 0.9863 è la config con shrinkage a emivita 180g.)*

**Risultato:** solo con la taratura abbiamo recuperato **circa un terzo** del
divario col mercato, senza informazione nuova. Ma il modello sui *soli gol* è ora
vicino al suo tetto.

### 📐 Il modello in dettaglio — le formule di shrinkage ed emivita

**1) Lo shrinkage è una penalità L2 nella verosimiglianza.** Il fit ora minimizza
`−ℓ + penalità`, dove (con bersaglio 0 = media di lega in questa fase):

```
penalità_shrinkage = s · ( Σ_i att_i²  +  Σ_i dif_i² )
```

con `s` = forza dello shrinkage (l'iperparametro tarato). È letteralmente una molla
che tira ogni forza verso 0.

**Perché è AUTOMATICAMENTE più forte sulle squadre con pochi dati** (il punto
cruciale). La forza di una squadra è stimata bilanciando due termini: il contributo
dei *suoi dati* (che nella verosimiglianza pesa in proporzione al **peso totale delle
sue partite** `n_i = Σ w_t`) contro la penalità fissa `s`. L'attrazione verso 0 vale
in pratica `≈ s / (s + n_i)`: per una squadra con **tante** partite `n_i ≫ s` → quasi
nessuno shrinkage (i dati vincono); per una **neopromossa / inizio stagione**
`n_i` piccolo → la penalità domina → la stima è tirata verso la media. *Non serve
codice speciale per le squadre con pochi dati: la stessa penalità fissa produce
l'effetto giusto.* È il motivo per cui lo shrinkage "attacca proprio neopromosse e
inizio stagione", visibile nei gap: inizio stagione +0.030→+0.022, neopromosse
+0.037→+0.030.

**Perché `s = 1.5`.** Non c'è formula chiusa: `s` è scelto per **griglia**, cercando
il valore che minimizza la log-loss 1X2 walk-forward mediata su più stagioni. Troppo
basso → non regolarizza (varianza alta sulle squadre incerte); troppo alto → schiaccia
anche le forze ben stimate verso la media (bias). Il minimo empirico è `1.5` (vedi
anche lo sweep piatto 0.75–1.5 della Fase 8).

**2) Perché la MEMORIA LUNGA (emivita ~730/365g) batte quella corta (90–180g).** È un
compromesso bias-varianza sul **campione efficace**:

```
N_eff = (Σ w_t)² / Σ w_t²     (numero "effettivo" di partite che entrano nella stima)
```

Un'emivita corta concentra il peso su poche gare recenti → `N_eff` piccolo → stime
**rumorose** (alta varianza). Un'emivita lunga usa più storia → `N_eff` grande →
stime stabili. Il rischio della memoria lunga sarebbe il *bias* (usare dati non più
rappresentativi), ma **in Serie A le rose restano stabili anno su anno**, quindi i
dati vecchi sono ancora informativi: il bias è piccolo e la riduzione di varianza
domina. Ecco perché il dato *preferisce* 730g e l'emivita corta 90g è la peggiore.
(Coerente con la Fase 25, dove tagliare NETTO i dati vecchi peggiora ancora di più.)

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

### 📐 Il modello in dettaglio — la formula del blend e perché α=1

**Come funziona il blend (la "forma generale" citata).** Si allena un secondo
modello identico al primo ma sui **tiri in porta** invece che sui gol (stessa
struttura attacco/difesa/vantaggio-casa, ma **senza** la correzione `τ`: `ρ=0`, perché
i tiri sono un conteggio ad alto volume che non ha il fenomeno "0-0 più frequente").
I due tassi attesi si **mescolano** con un peso `α = shots_blend`:

```
λ = α · λ_gol  +  (1−α) · λ_tiri · c_home
μ = α · μ_gol  +  (1−α) · μ_tiri · c_away
```

Il **fattore di conversione** riporta i tiri sulla scala dei gol (un tiro in porta
non è un gol):

```
c = Σ w_t · gol  /  Σ w_t · tiri     (pesato nel tempo, per casa e ospite)
```

Per i tiri `c ≈ 0.3` (servono ~3 tiri in porta per un gol); per l'xG (Fase 4b) `c ≈ 1`
(l'xG è già in scala gol). `α=1` = solo gol (modello classico); `α=0` = solo tiri.

**Perché α=1 vince (i tiri grezzi non aiutano).** L'esperimento è un semplice sweep di
`α` che sceglie il valore con log-loss minima su 6 stagioni. Il risultato: `α=1`
(0.9817 su 1X2) < `α=0.5` (0.9833) < `α=0` (0.9913). Interpretazione: i tiri in porta
**contano le occasioni ma non ne pesano la qualità** — un tiro debole da 30 metri e
un colpo di testa a porta vuota valgono uguale. Aggiungere quel segnale sostituisce
rumore-gol con rumore-tiri, senza guadagno netto. L'illusione di un vantaggio su O/U
a 3 stagioni **spariva** allargando a 6 (`N` raddoppia, l'errore standard `∝ 1/√N`
si dimezza e il falso segnale rientra nel rumore): è la ragione per cui la regola
"valida su più stagioni" esiste. Il meccanismo era giusto, mancava la *qualità* del
segnale — che l'xG fornisce.

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

### 📐 In dettaglio — cosa vogliono dire quei numeri

- **52.6% vs 53.9% (accuratezza del segno 1X2).** È la frazione di partite in cui
  `argmax(P_casa, P_pari, P_ospite)` coincide con l'esito reale. Un solo punto di
  distanza, e nel 92% dei casi il favorito scelto è lo stesso → il modello e il
  mercato "vedono" quasi le stesse partite; la differenza non è *chi* è favorito ma
  *quanto*.
- **"più vicini al vero solo nel 43%".** È la frazione di partite in cui la log-loss
  del modello è **minore** di quella del mercato, cioè in cui il modello ha dato
  all'esito realizzato una probabilità *più alta*. 43% < 50% ⇒ quando i due
  dissentono, ha ragione il mercato più spesso. (La Fase 20 spiega *perché* i
  dissensi del modello sono i suoi errori: adverse selection.)
- **Il "margine ~5%" e perché serve batterlo.** Le quote implicano `Σ 1/quota > 1`;
  l'eccesso (`overround`) è il margine del bookmaker, ~5% sull'1X2 di Serie A. Per
  *guadagnare* non basta essere accurati quanto il mercato: bisogna esserlo **più**
  del margine. Essendo un filo *meno* accurati, ogni "value bet" è quasi sempre un
  nostro errore → ROI simulato negativo. È la traduzione quantitativa di "non
  scommettere".

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

### 📐 In dettaglio — le soglie e perché quei valori (non è modello, è provenienza)

Questa fase non introduce formule del modello, ma **decisioni quantitative** sui
dati, ognuna con un perché preciso:

- **Look-ahead sui valori rosa: cutoff al 1° settembre.** Si prende l'ultima
  valutazione Transfermarkt **antecedente al 1° settembre** della stagione. Motivo:
  è informazione *nota prima* che la stagione conti davvero; usare valori aggiornati
  a gennaio sarebbe guardare il futuro. Staleness massima ammessa **550 giorni** (se
  l'ultima valutazione è più vecchia, il dato è troppo datato per fidarsi).
- **Soglia dell'85% dei minuti per pubblicare il valore-rosa.** Il valore squadra è
  la somma dei valori dei giocatori agganciati; si pubblica **solo se i giocatori
  valutati coprono ≥85% dei minuti stagionali** della squadra, altrimenti `NaN`.
  Perché una soglia e non un'imputazione: con un datalake incompleto (~25% dei
  profili senza serie di valutazioni, es. Milinkovic-Savic/Lazio), riempire i buchi
  con una media *inventerebbe* forza; un buco dichiarato (`NaN` → covariata neutra)
  è onesto. Politica: **niente imputazioni, mai un numero inventato.**
- **La catena di aggancio dei nomi è deterministica e ordinata** (dal più sicuro al
  più permissivo), misurata su 1.986 giocatori: esatto 1691 → filtro ruolo 96 →
  spareggio per valore di picco 63 → senza-spazi 3 → sottoinsiemi di token 21 →
  cognome+iniziale 29 → fuzzy con soglia **0.90** 8 → **non agganciati 78 (~4%)**.
  La soglia fuzzy 0.90 è volutamente alta (conservativa): meglio lasciare 78 giocatori
  non agganciati (quasi tutti con pochi minuti, impatto trascurabile) che agganciare
  la persona sbagliata.
- **Perché l'impronta dati resta invariata (`8483944342fc8b15`).** L'impronta è
  calcolata **solo** su date/squadre/gol (l'input del modello-gol), non sulle nuove
  colonne: aggiungere xG/valori/assenze non tocca la riproducibilità dei backtest
  già registrati → il backtest di non-regressione dà metriche **identiche**.

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

### 📐 Il modello in dettaglio — stessa formula dei tiri, segnale migliore

La meccanica è **identica** alla Fase 3 (stessa formula di blend), cambia solo il
segnale secondario: `blend_signal = "xg"` invece di `"sot"`.

```
λ = α · λ_gol  +  (1−α) · λ_xg · c_home        (idem per μ)
c = Σ w·gol / Σ w·xg  ≈  1     (l'xG è GIÀ in scala gol; per i tiri era ~0.3)
```

**Perché l'xG aiuta dove i tiri no.** L'xG **pesa la qualità** di ogni occasione
(probabilità di gol di quel tiro dato posizione/tipo), non la conta e basta. È un
"conteggio di gol attesi" con meno rumore dei gol realizzati (che dipendono dalla
fortuna sotto porta) e con più informazione dei tiri grezzi (che ignorano la
qualità). Il fatto che `c ≈ 1` conferma che è già la grandezza giusta.

**Perché α = 0.75 (e non 0 né 1).** È il valore che minimizza la log-loss **media a
6 stagioni su ENTRAMBI i mercati** (1X2 0.9813 a α=0.75 vs 0.9817 a α=1; l'O/U
migliora già a α più bassi). La scelta è **conservativa**: `0.75` dà ancora il peso
maggiore ai gol (il segnale "duro", ciò che conta davvero), usando l'xG come
correzione del rumore realizzativo, non come sostituto. Presa sulla *media* e non su
una stagione singola (sul solo 2025-26 l'1X2 è appena sotto) proprio per non
inseguire il rumore di piccolo campione — la lezione della Fase 3. È il primo segnale
che aggiunge valore reale e consistente, soprattutto su O/U (la qualità delle
occasioni informa il *volume* di gol più di *chi* vince).

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

### 📐 Il modello in dettaglio — la formula delle covariate

Ogni covariata entra nel **log-tasso** della squadra che segna come vantaggio
*relativo* rispetto all'avversaria. Il termine aggiunto al tasso di CASA è:

```
cov = Σ_k  β_k · ( z_casa,k − z_ospite,k )          → λ = exp(… + cov)
                                                     → μ = exp(… − cov)   (segno opposto)
```

dove `z` è il valore per-squadra **standardizzato** sul training:

```
z = ( trasforma(valore) − media ) / dev.std
```

Le trasformazioni sono scelte per la natura del dato: `squad_value → log` (i valori
rosa spaziano su ordini di grandezza), `absence → log1p` (conteggio/valore ≥0, log1p
gestisce lo zero), `rest → identity` (già in giorni). Valori mancanti → `z=0`
(covariata **neutra**, non penalizzante). I coefficienti `β_k` sono stimati
**insieme** a tutto il resto nella stessa verosimiglianza (fit congiunto), con
`β ∈ [−1, 1]`. Un `β<0` significa "più valore relativo → segna di **meno**": è il
segno atteso per le assenze (più assenze pesanti → meno gol).

**Perché il valore-rosa NON aiuta (nonostante il diagnostico in-sample +0.48).** Il
coefficiente in-sample positivo dice solo che squadre di valore alto segnano di più
*nei dati già visti* — ma quella forza **è già catturata** dal modello gol+xG (una
squadra costosa segna di più e ha xG più alto, e il modello lo vede). Fuori campione
la covariata non aggiunge informazione *indipendente*: aggiunge solo il rumore della
sua stima → l'1X2 peggiora appena (0.9813→0.9818). È la lezione centrale: **un
diagnostico in-sample va sempre confermato walk-forward.**

**Perché il riposo solo-Serie-A dà ~0.** La covariata entra come *differenza*
`z_casa − z_ospite`. Quando tutta la lega gioca infrasettimana, il riposo cala per
**entrambe** → la differenza è ~0 → nessun effetto. E il calendario di sola Serie A
**non vede** coppe/Europa/nazionali, cioè proprio le partite che causano fatica
*asimmetrica*. Questo motiva la Fase 4e (calendario di club completo): il segnale
esiste solo se la sorgente del calendario è completa.

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

### 📐 Il modello in dettaglio — perché l'emivita ottima si accorcia

Nessuna formula nuova: si ri-cerca l'ottimo degli **stessi** iperparametri (shrinkage,
emivita) con il blend xG ora attivo, per **coordinate** (fissa uno, ottimizza l'altro).
Il risultato è un'interazione reale tra due parametri già tarati.

**Il perché, in termini di bias-varianza.** L'emivita bilancia:
- *memoria corta* → più reattiva ma meno campione efficace `N_eff` → più **varianza**;
- *memoria lunga* → più stabile ma rischia di usare forza non più attuale → più **bias**.

Nella Fase 2b il segnale era i soli **gol**, molto rumorosi (fortuna sotto porta):
serviva memoria lunga (730g) per mediare via quel rumore. Ora il blend `α·gol +
(1−α)·xG` fornisce un segnale **meno rumoroso a parità di partite** (l'xG stabilizza
la stima del tasso). Con meno rumore per-partita, il modello può permettersi un
`N_eff` più piccolo (emivita **365g**, più reattiva) **senza** inseguire il rumore:
il termine di varianza è già domato dall'xG, quindi conviene ridurre il bias
diventando più recenti. È il caso da manuale del "cambiare una parte del modello
(aggiungere l'xG) sposta l'ottimo di un'altra (l'emivita)" → dopo ogni modifica
importante si ri-verificano gli iperparametri. Guadagno piccolo (−0.0006 su 1X2,
−0.0009 su O/U) ma su entrambi i mercati e ben fondato.

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

### 📐 Il modello in dettaglio — ogni mercato è una somma di celle

Nessun nuovo parametro: tutti i mercati derivano dalla **stessa** matrice `P(i,j)`.

```
1X  = P(1)+P(X)          2X = P(2)+P(X)          12 = P(1)+P(2)   (= 1 − P(X))
Over 2.5 = Σ_{i+j≥3} P(i,j)                       GG = Σ_{i≥1, j≥1} P(i,j)
```

Ecco perché aggiungere un mercato è "gratis" e perché i mercati d'esito funzionano:
`1X, 2X, 12` sono combinazioni lineari delle probabilità 1X2, che il modello stima
bene → le eredita bene.

**Perché il GG/NG è PEGGIO della baseline (il punto tecnico chiave).** Sotto Poisson
**indipendenti** varrebbe esattamente:

```
P(GG) = P(casa ≥ 1) · P(ospite ≥ 1) = (1 − e^{−λ}) · (1 − e^{−μ})
```

cioè un prodotto di due marginali: **nessuna informazione sulla correlazione** tra i
due punteggi. La correzione `τ` di Dixon-Coles tocca solo 4 celle basse → perturba
`P(GG)` di pochissimo. Ma il GG/NG **è** un evento di correlazione ("segnano
*entrambe*"): dipende da quanto i due punteggi si muovono insieme, che il modello
quasi-indipendente non modella. Risultato: sul GG/NG il modello aggiunge rumore, non
segnale, e finisce **sotto** la media (0.6896 vs baseline 0.6871). È la diagnosi che
motiva il "cambio di classe" (Poisson bivariato / inflazione diagonale, Fase 12b) e
che verrà confermata: il pareggio e il GG/NG vivono nella *correlazione*, non nei
tassi marginali.

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

### 📐 In dettaglio — la definizione del riposo e l'invariante che lo verifica

**Formula della feature** (identica a `add_rest_days`, ma sul calendario COMPLETO):

```
rest_days_full = min( giorni dall'ULTIMA gara di club della squadra
                      in QUALSIASI competizione,  cap = 14 )
```

- `cap = 14`: oltre due settimane il recupero fisico è completo; conta la
  *congestione*, non il riposo lungo → si tronca a 14.
- Solo partite **precedenti** → niente look-ahead. Prima gara nota → `NaN`.

**L'invariante di sicurezza (perché ci fidiamo del dato).** Il calendario completo è
un **sovrainsieme** di quello di Serie A, quindi l'ultima partita precedente è sempre
più vicina o uguale:

```
rest_days_full  ≤  rest_days   (su ogni riga dove entrambi sono definiti)
```

Verificato su ~3400 partite: **0 violazioni**. Un bug di join o un look-ahead
romperebbe questa disuguaglianza → è un test automatico che *dimostra* l'assenza di
errori di allineamento, non una speranza. È lo stesso spirito dei controlli
d'integrità (gol grezzi == gol snapshot) del loader.

**Perché il segnale utile è concentrato in poche stagioni.** Il riposo differisce dal
proxy solo dove `rest_days_full < rest_days`, cioè dove c'è una gara "nascosta"
(coppa/Europa). openfootball copre Champions in tutte le 9 stagioni, ma EL dal
2020-21, Conference dal 2021-22, Coppa Italia 2020-25. Dove una competizione manca,
`rest_days_full` **degrada in modo controllato** verso il valore solo-lega (mai nella
direzione sbagliata, per l'invariante sopra): niente numeri inventati, solo un
segnale più debole. Totale partite con congestione vera catturata: **655/3420
(19.2%)**, quasi tutte nelle stagioni 2020-25.

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

### 📐 Il modello in dettaglio — un solo fattore cambiato, e la soglia del rumore

Meccanicamente `rest_full` è **la stessa covariata** di `rest` (formula in Fase 4c:
`cov = β·(z_casa − z_ospite)`), con l'unica differenza nella *sorgente* della colonna
(`home/away_rest_days_full` invece di `home/away_rest_days`). Tenere identico tutto il
resto è ciò che rende il confronto pulito: **un solo fattore per volta**.

**Perché "migliora ma è rumore".** Il `β` di `rest_full` diventa del segno giusto
(la congestione vera pesa), e il Δ medio passa da **+0.0006** (`rest`, peggiora,
conferma 4c) a **−0.0004** (`rest_full`, migliora appena). Ma −0.0004 va letto
sulla scala della **variabilità stagionale**: il CI bootstrap di un gap 1X2 per
stagione è tipicamente ±0.014 (Fase 17). Un effetto di 0.0004, che aiuta solo 2
stagioni su 5, è **un ordine di grandezza dentro il rumore** → la diagnosi 4c era
giusta (il problema era la sorgente), ma l'effetto è reale-e-minuscolo, non
adottabile. È la prima di una lunga serie di leve "direzione corretta, payoff nel
rumore" che convergono sul tetto.

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

### 📐 Il modello in dettaglio — la formula del temperature scaling

Correzione **post-hoc** a un solo parametro `T`, applicata alle probabilità 1X2 già
prodotte dal modello e poi rinormalizzata (`src/evaluation/calibration.py`):

```
q_i ∝ p_i^(1/T) ,   poi   q_i ← q_i / Σ_j q_j
```

- `T = 1` → nessun cambiamento;
- `T > 1` → "raffredda": probabilità più vicine all'uniforme (meno sicuro);
- `T < 1` → "scalda": probabilità più nette (più sicuro).

**Come si evita il look-ahead.** `T` si **tara** minimizzando la log-loss *solo* sulle
predizioni walk-forward delle stagioni **precedenti** a quella di test
(leave-future-out), e si applica alla stagione di test. `T` non tocca mai i dati che
valuta.

**Perché la scoperta è robusta ma il guadagno no.**
- *Robusta:* `T < 1` in **tutte e 6** le stagioni (0.92–0.96). Il modello è
  sistematicamente un filo **sotto**confidente → le probabilità andrebbero rese un
  po' più nette. (L'eccesso di sicurezza segnalato dal diagnostico era concentrato in
  poche partite estreme, non nella distribuzione media.)
- *Nel rumore:* rendere le probabilità più nette è un'arma a doppio taglio — `−ln p`
  premia molto quando l'esito netto si avvera, ma punisce ancora di più quando no. In
  Serie A i due effetti quasi si annullano: −0.0003 medio, e **peggiora 2 stagioni su
  6**. Sotto la soglia del rumore → non entra nella config ufficiale.
- *Limite strutturale:* `T` scala **tutte** le classi in modo uniforme, non può
  *spostare massa* da un esito all'altro (es. dalla casa al pareggio). Per quello
  serve la ricalibrazione per-classe (Fase 10).

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

### 📐 Il modello in dettaglio — come è costruito δ e perché vale 0.23

**Il meccanismo: si sposta il BERSAGLIO dello shrinkage.** La penalità della Fase 2b
tirava le forze verso 0 (media). Per le neopromosse il bersaglio diventa un valore
**sotto** la media:

```
penalità = s · [ Σ_i (att_i − att_prior_i)² + Σ_i (dif_i − dif_prior_i)² ]
con   att_prior = −δ_att   e   dif_prior = +δ_def   SOLO per le neopromosse
      (0 per tutte le altre)
```

Eleganza del riuso: non serve codice nuovo per il cold-start. Una neopromossa con
**0 partite** non ha contributo dai dati → la penalità la porta *esattamente* sul
prior; man mano che gioca, il termine dati la sovrasta allo stesso ritmo con cui lo
shrinkage cede su qualsiasi squadra (`≈ s/(s+n_i)`, Fase 2b). Le promosse entrano nel
modello anche a inizio stagione, non più trattate come "sconosciute = media".

**Perché δ ≈ 0.23 (l'aritmetica esatta).** In log-scala, uno spostamento `δ`
dell'attacco moltiplica il tasso-gol per `e^{−δ}`. Dai dati storici delle 24
neopromosse 2018-2026:

```
attacco:  segnano 1.08 gol/gara vs 1.36 della lega  →  δ_att = ln(1.36 / 1.08) = 0.230
difesa:   subiscono 1.72 vs 1.36                     →  δ_def = ln(1.72 / 1.36) = 0.235
```

I due coincidono a ~0.23 → si usa un unico `δ = 0.23`. Verifica del segno: `e^{−0.23} =
0.795` (segnano il **−20%**) e `e^{+0.23} = 1.259` (subiscono il **+26%**) —
esattamente i −20%/+26% osservati. **Il numero non è tirato a caso: è il logaritmo del
rapporto di gol osservato.**

**Perché non è look-ahead.** Per la stagione S, `δ` è stimato **solo** dalle
neopromosse delle stagioni `< S` (leave-future-out) e applicato **sia** al modello-gol
**sia** al modello-xG del blend (la promossa è più debole in entrambi).

**Perché è l'unico adottato.** −0.0011 medio complessivo (3-4× congestione e
calibrazione) e **−0.0039** dove deve colpire (partite con una neopromossa),
migliorando 5 stagioni su 6. È l'unica leva che *supera il rumore in modo consistente*
ed è **principiata** (un fatto strutturale — le promosse *sono* più deboli — non un
parametro pescato). Il 2023-24 peggiora (+0.0007) perché quel trio
(Genoa/Cagliari/Frosinone) era vicino alla media: è la varianza attesa di una regola
che scommette sul caso generale.

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

### 📐 Il modello in dettaglio — ortogonalità e il test di persistenza

**#1 — Perché lo shrinkage resta 1.5 (ortogonalità).** Con il prior attivo, lo sweep
dà una curva **piatta** (0.9797 da 0.75 a 1.5, minimo nominale a 1.0 ma a 0.00002 da
1.5 = rumore). Interpretazione: prior e shrinkage agiscono su cose diverse — il
**prior** fissa *dove* punta la molla per le neopromosse (il cold-start), lo
**shrinkage** ne regola la *forza* per tutte. Nell'intervallo utile non interagiscono
→ nessun guadagno a ri-tararlo → resta 1.5.

**#2 — Perché il vantaggio-casa per-squadra muore prima di costruirlo.** Il test
economico misura la **persistenza anno-su-anno** dell'effetto per-squadra:

```
proxy per team-stagione:  (punti/gara in casa) − (punti/gara fuori)
persistenza:  r = corr( proxy_stagione_t , proxy_stagione_t+1 )  su n=136 coppie
```

Risultato: **r ≈ 0.004** (praticamente zero), mentre l'effetto **medio** è reale
(0.254 punti/gara — ed è già nel modello come `home_advantage` globale `γ`). La
regola statistica: l'utilità *out-of-sample* di un predittore è limitata dalla sua
**affidabilità** (quanto si ripete). Con `r ≈ 0`, il "forte in casa" di quest'anno è
scorrelato da quello del prossimo → un vantaggio-casa per-squadra **fitterebbe solo
rumore stagionale** e non generalizzerebbe. L'idea muore *prima* della chirurgia sul
modello: è il principio "testa la versione economica prima di investire". (La Fase 30
troverà che il vantaggio-casa varia *dentro* la stagione — crollo nel finale — che è
un effetto diverso e globale, non per-squadra.)

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

### 📐 In dettaglio — l'aritmetica del "quanto manca" e "dove vive il gap"

**Quanta strada è stata chiusa.** La baseline banale sta a gap ~+0.12 dal mercato,
il modello attuale a +0.0165:

```
frazione chiusa = 1 − (gap_attuale / gap_baseline) = 1 − 0.0165/0.12 ≈ 0.86  (86%)
```

L'ultimo ~14% è la parte dura. (L'audit di Fase 15 ha corretto un precedente "87%"
in **86%**: differenza di arrotondamento, ma va registrata.)

**Perché il gap è "quasi tutto nel pareggio" (scomposizione).** I mercati derivati
isolano *dove* si perde:
- **12 = 1 − P(X)**: prezzarlo non richiede stimare la *massa* del pareggio, solo
  "vince una delle due". Gap **+0.0020** ≈ mercato.
- Appena il pareggio rientra come esito da prezzare (1X, 2X, 1X2) il gap
  **triplica/quadruplica** (+0.012…+0.017).

Poiché `gap(1X2)` ≈ (errore nel prezzare *chi vince*) + (errore nel prezzare *il
pareggio*), e il primo termine è ~0 (lo dice il 12), **il grosso del gap è il secondo
termine**: prezzare i pareggi (= i punteggi bassi correlati). È la firma matematica
che indirizza il "cambio di classe" verso la correlazione dei punteggi (Fase 12b/18),
non verso più feature di forza.

**La "U" per forza squadra** (deboli +0.0206, forti +0.0180, medie +0.0123) e il
picco sulle **stagioni rumorose** (COVID 2020-21 +0.0202) sono coerenti con
l'interpretazione "il mercato ha informazione che noi non abbiamo" (motivazione
salvezza, turnover coppe): non è modellabile con i dati storici → è il residuo
irriducibile.

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

### 📐 In dettaglio — perché il COVID muove il gap d'esito (il ruolo di γ)

Il vantaggio-casa nel modello è un **unico parametro globale** `γ` (in
`λ = exp(att_h + dif_a + γ)`), stimato con i pesi temporali. Come ogni parametro
pesato nel tempo, si adatta **lentamente**: a stadi vuoti (2020-21) il vantaggio-casa
reale è crollato, ma `γ` continuava a riflettere lo storico "normale" a pubblico
pieno → il modello **sovra-pesava** le squadre di casa proprio quando contavano meno.
Il mercato si adeguava più in fretta → gap d'esito più largo (+0.0202). Tornato il
pubblico, il gap si è richiuso (−0.0041). È lo stesso meccanismo che la Fase 30
ritroverà *dentro* la stagione (crollo del vantaggio-casa nel finale) e coerente con
la Fase 8 (il vantaggio-casa **globale** conta e drifta; quello **per-squadra** è
rumore). L'O/U fa l'opposto (nel COVID il modello lo *batte*, −0.0031): i totali gol
risentono meno del pubblico, e in quella stagione anomala le quote O/U erano
verosimilmente meno affilate. *Cautela onesta:* un solo campione COVID (380 partite).

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

### 📐 Il modello in dettaglio — la formula della ricalibrazione per-classe

Tre moltiplicatori, uno per esito (casa/pari/ospite), applicati alle probabilità 1X2
e rinormalizzati:

```
q_i ∝ w_i · p_i ,   poi   q_i ← q_i / Σ_j q_j
```

**Perché 2 parametri e non 3.** Solo i *rapporti* tra i `w` contano: `w=(c,c,c)` si
semplifica nella rinormalizzazione. Si fissa `w_ospite = 1` (restano `w_casa, w_pari`)
e alla fine il vettore è normalizzato a media geometrica 1 per leggibilità. Tarato
**leave-future-out** (solo stagioni precedenti) e applicato al test.

**Cosa la distingue dal temperature (Fase 6).** Il temperature `p^{1/T}` scala tutte
le classi allo stesso modo → non può *spostare massa* tra esiti. Qui `w_i` diverso
per classe **sposta massa**: è ciò che serve per una miscalibrazione **direzionale**.

**Perché w_casa ≈ 0.96 e w_pari ≈ 1.04-1.06 (robusto in 6/6 stagioni).** Il fit, senza
che glielo si dica, **abbassa la casa e alza il pareggio** in ogni stagione: conferma
quantitativa che il modello **sovrastima le vittorie casalinghe e sottostima i pari**
— la stessa direzione del diagnostico (Fase 9) e dell'analisi COVID (γ, Fase 9-bis).

**Perché il guadagno resta piccolo (−0.0005).** È un surrogato **lineare e globale**
di ciò che servirebbe davvero: la probabilità *giusta* del pareggio dipende dai tassi
`(λ, μ)` della **singola partita** (un match da 1.8 gol attesi ha P(pari) diversa da
uno da 3.5), non da un fattore costante `w_pari`. La ricalibrazione spreme lo strato
"medio" della miscalibrazione (−0.0005, un filo meglio del temperature −0.0003) ma il
residuo è strutturale → non entra nella config ufficiale. Punta di nuovo al Poisson
bivariato (Fase 12b).

---

## Fase 11 — Combinazioni delle feature off-di-default (nessuna e' utile)

**Obiettivo.** Finora le feature opzionali erano state provate quasi sempre DA
SOLE. Domanda: esiste una loro **combinazione** che, sul modello attuale (col
prior), supera il rumore in modo consistente? Feature off-di-default:
covariate `squad_value`, `absence`, `rest_full` (livello-modello) + ricalibrazione
per-classe post-hoc (Fase 10).

**Disegno.** Tutti i 2^3 = 8 sottoinsiemi delle covariate, ognuno **con e senza**
la ricalibrazione per-classe strutturale (pesi fissi robusti casa 0.96 / pari
1.04 / ospite 1.00, dalla Fase 10). 48 backtest walk-forward × 6 stagioni. Metrica:
1X2 log-loss, Δ vs ufficiale (0.9797) e n. stagioni migliorate (consistenza).

**Risultato (1X2 log-loss; Δ<0 = meglio).**

| Combinazione | RAW | Δ | migl. | +RECAL | Δ | migl. |
|---|--:|--:|:--:|--:|--:|:--:|
| ufficiale (solo prior) | 0.9797 | — | — | 0.9789 | −0.0008 | 6/6 |
| +squad_value | 0.9804 | +0.0007 | 1/6 | 0.9796 | −0.0001 | 3/6 |
| +absence | 0.9796 | −0.0001 | 2/6 | 0.9789 | −0.0008 | 5/6 |
| +rest_full | 0.9794 | −0.0003 | 2/6 | 0.9786 | −0.0011 | 4/6 |
| +squad+absence | 0.9804 | +0.0007 | 1/6 | 0.9796 | −0.0001 | 3/6 |
| +squad+rest_full | 0.9801 | +0.0004 | 2/6 | 0.9793 | −0.0004 | 4/6 |
| +absence+rest_full | 0.9793 | −0.0004 | 3/6 | **0.9786** | **−0.0011** | 4/6 |
| +tutte e tre | 0.9801 | +0.0004 | 2/6 | 0.9793 | −0.0004 | 2/6 |

Multi-mercato (miglior combo vs ufficiale, pool 6 stagioni): gap 1X2 +0.0165→
+0.0161, doppie chance e O/U ~invariati, GG/NG identico (−0.0018). Nessun mercato
beneficia.

**Lezione / cosa ne consegue.**
1. **Nessuna covariata aiuta, nemmeno in combinazione.** `squad_value` **peggiora**
   in ogni mix (+0.0004/+0.0007); `absence` e `rest_full` sono ~neutre da sole e
   la loro coppia da' il miglior RAW ma solo −0.0004 (3/6, rumore). Aggiungere
   covariate non "impila" nulla: confermato che sono ridondanti con gol+xG (gia'
   visto in Fase 4c, ora anche in combinazione e con la config attuale).
2. **L'unico effetto additivo e' la ricalibrazione per-classe** (~−0.0008 coi
   pesi fissi; l'onesto leave-future-out della Fase 10 e' −0.0005). Applicata al
   modello base aiuta 6/6 stagioni, ma e' piccola e la conosciamo gia'.
3. **La "miglior" combinazione (+absence+rest_full+recal, −0.0011) non e' una
   vera vittoria**: il guadagno e' tutto della ricalibrazione (mildly ottimista
   coi pesi fissi), il contributo delle covariate e' rumore, e migliora solo 4/6
   stagioni — MENO del recal sul modello base (6/6). Le covariate qui **sporcano**
   invece di aiutare.
4. **Sesto esperimento interno di fila senza un guadagno robusto.** La risposta
   alla domanda "c'e' una combinazione off-di-default utile?" e' **no**. Le
   feature restano giustamente off; l'unica ha valore solo per l'uso pratico
   (probabilita' un filo piu' oneste), non per un edge.

**Riproducibilita'.** `python scripts/_run_combo_analysis.py`.

### 📐 In dettaglio — perché unire segnali nulli non "impila" nulla

**Il disegno.** Tutti i `2³ = 8` sottoinsiemi delle covariate off-di-default
(`squad_value`, `absence`, `rest_full`), ciascuno con e senza la ricalibrazione
per-classe a **pesi fissi robusti** (casa 0.96 / pari 1.04 / ospite 1.00, dalla Fase
10) = 48 backtest × 6 stagioni.

**Perché nessuna combinazione aiuta.** Le covariate entrano additivamente nel
log-tasso (`cov = Σ_k β_k (z_h,k − z_a,k)`, Fase 4c). Se ogni `β_k` è ~0
out-of-sample (perché il segnale è già catturato da gol+xG, Fase 4c), la loro somma è
~0 più il rumore accumulato di più stime → in media **peggiora** (`squad_value` fa
+0.0004/+0.0007 in ogni mix). Non c'è sinergia da estrarre: due segnali ridondanti da
soli restano ridondanti insieme.

**Perché la "miglior combo" (−0.0011) non è una vittoria.** Quel guadagno è **tutto**
della ricalibrazione (che aiuta 6/6 sul modello base), mentre il contributo delle
covariate è rumore; e la combo migliora solo **4/6** stagioni — *meno* del recal da
solo (6/6). Scegliere il minimo tra 8 combinazioni è **selezione post-hoc**: con
tante prove, il minimo campionario è ottimisticamente basso anche sotto rumore puro.
Il verdetto onesto è "nessun guadagno robusto", non "abbiamo trovato la combo".

---

## Fase 12a — Ensemble di emivite (ultimo tweak economico; piccolo, borderline)

**Obiettivo / idea.** L'unica idea economica non ancora testata: mescolare un
modello a memoria CORTA (180g, reattivo/forma) e uno LUNGA (730g, forza stabile)
puo' battere la singola emivita 365g? Si mescolano le probabilita' 1X2 (righe
allineate), tutti col prior.

**Risultato (1X2 log-loss, 6 stagioni).**

| Variante | media | Δ vs 365g | migliora |
|---|--:|--:|:--:|
| singola 180g | 0.9806 | +0.0009 | 3/6 |
| singola 365g (ATTUALE) | 0.9797 | — | — |
| singola 730g | 0.9803 | +0.0006 | 3/6 |
| **blend 180+730 (50/50)** | **0.9791** | **−0.0006** | 4/6 |
| blend 180+365+730 (1/3) | 0.9793 | −0.0004 | 4/6 |
| blend 365+730 (50/50) | 0.9798 | +0.0001 | 3/6 |

**Lezione.** La miscela **corta+lunga (180+730)** batte di un soffio ogni singola
emivita (−0.0006, 4/6): combinare forma reattiva e forza stabile cattura un po'
piu' della singola 365g. Ma e' **borderline** (4/6, non 6/6), nella stessa fascia
di prior/calibrazione/ricalibrazione. **Non adottato** (non abbastanza robusto).
Chiude il capitolo dei tweak economici: anche l'ultima idea non testata e'
rumore-adiacente. **Riproducibilita'.** `python scripts/_run_ensemble.py`.

### 📐 Il modello in dettaglio — la media di due modelli

Si allenano **due** modelli identici tranne l'emivita — uno corto (180g, reattivo/
forma) e uno lungo (730g, forza stabile) — e si mediano le probabilità 1X2 riga per
riga:

```
p_blend = 0.5 · p_180g  +  0.5 · p_730g       (media sulle probabilità, non sui tassi)
```

**Perché corto+lungo batte il singolo 365g (di un soffio).** È un mini-ensemble: i due
modelli sbagliano in modo parzialmente **scorrelato** (il corto cattura la forma
recente, il lungo la forza di fondo), quindi mediarli riduce la varianza più di quanto
faccia una singola emivita intermedia. Guadagno −0.0006, ma **4/6** stagioni (non
6/6): nella stessa fascia di rumore di prior/calibrazione/ricalibrazione → **non
adottato**. Il 365g singolo resta la config: cattura già gran parte del beneficio in
un modello solo, più semplice.

---

## Fase 12b — Il cambio di classe: inflazione della diagonale (bivariato)

**Obiettivo.** La mossa strutturale indicata da TUTTE le analisi: attaccare la
correlazione dei punteggi / il pareggio, non piu' con un tampone ma cambiando il
modello. Il Poisson bivariato classico (Karlis-Ntzoufras) impone correlazione
positiva (λ₃≥0) che nel calcio e' ≈0 e non aiuta i pareggi; la variante giusta e'
il **modello a diagonale inflazionata**.

**Cosa abbiamo costruito.** Un parametro **φ** che moltiplica per (1+φ) TUTTI i
punteggi di parita' (0-0,1-1,2-2,3-3…) nella matrice, esteso **oltre le 4 celle**
della correzione Dixon-Coles, e — a differenza della ricalibrazione piatta (Fase
10) — **fittato nella verosimiglianza dei punteggi** e **dipendente dalla partita**
(inflaziona in base ai gol attesi). `draw_inflation` nel modello (`--draw-inflation`),
φ stimato con una 1-D per settimana (formula chiusa sulla prob. di pareggio base).

**Diagnosi che lo motiva.** rho fittato −0.04/−0.07, **interno** (non saturo) ma
vincolato alla struttura a 4 celle; deficit pareggio residuo **+0.020** (modello
0.264 vs reale 0.284). C'e' margine per una leva-pareggio dedicata.

**Risultato (1X2 log-loss + calibrazione pareggio, 6 stagioni).**

| Stagione | base | +infl | Δ | P(pari) base→infl | reale |
|---|--:|--:|--:|:--:|--:|
| 2020-21 | 0.9532 | 0.9536 | +0.0003 | 0.250→0.245 | 0.255 |
| 2021-22 | 0.9860 | 0.9854 | −0.0006 | 0.242→0.248 | 0.258 |
| 2022-23 | 0.9916 | 0.9917 | +0.0001 | 0.247→0.257 | 0.263 |
| 2023-24 | 0.9854 | 0.9825 | **−0.0029** | 0.253→0.267 | 0.295 |
| 2024-25 | 0.9693 | 0.9687 | −0.0006 | 0.264→0.288 | 0.284 |
| 2025-26 | 0.9925 | 0.9939 | +0.0014 | 0.264→0.283 | 0.261 |
| **MEDIA** | **0.9797** | **0.9793** | **−0.0004** | | |

Multi-mercato (pool): gap 1X2 +0.0165→+0.0161, **12** +0.0020→+0.0016, O/U e
GG/NG ~invariati. φ fittato ~0.10-0.14 (positivo, come da deficit).

**Lezione / cosa ne consegue — la conclusione dell'intera indagine.**
1. **Il meccanismo funziona come progettato**: P(pari) sale verso il reale in
   OGNI stagione (2024-25: 0.264→0.288 vs 0.284, quasi perfetto). La calibrazione
   del pareggio migliora davvero: il cambio di classe **fa la cosa giusta**.
2. **Ma il log-loss guadagna solo −0.0004 (3/6 stagioni)**, perche' *quanti*
   pareggi capitano in una stagione e' in larga parte **rumore**: dove ne capitano
   pochi (2025-26, reale 0.261) l'inflazione tarata sul passato **sovrastima** e
   peggiora. Migliorare la calibrazione MEDIA del pareggio non basta se la
   deviazione stagionale e' imprevedibile.
3. **Questo chiude il cerchio.** Anche la mossa strutturalmente corretta — quella
   che tre analisi indipendenti indicavano — da' lo stesso ordine di grandezza
   (−0.0004) di ogni tampone. Ragione profonda: **il pareggio e' quasi-casuale per
   tutti, mercato incluso** (il mercato 12 senza pari e' gia' a livello mercato,
   gap +0.0020). Non e' un difetto del nostro modello: e' irriducibilita' del
   fenomeno. Il gap col mercato NON e' "cattiva modellazione del pareggio" da
   sistemare, ma **informazione che il mercato ha e noi no** su singole partite.
4. **Verdetto definitivo**: 7 esperimenti (5 tweak + 1 combinazione + 1 cambio di
   classe) convergono. Il modello e' al **tetto reale**, non solo pratico.
   `draw_inflation` resta **off di default** (−0.0004, non robusto), disponibile
   come opzione (migliora la calibrazione del pareggio per l'uso pratico).

**Riproducibilita'.** `python scripts/_run_draw_infl.py`, oppure
`python scripts/backtest.py --draw-inflation`.

### 📐 Il modello in dettaglio — la formula dell'inflazione diagonale φ

**La correzione.** Un parametro `φ` moltiplica per `(1+φ)` **tutti** i punteggi di
parità (non solo le 4 celle di Dixon-Coles), poi si rinormalizza:

```
P_φ(i, j) ∝ M(i, j) · ( 1 + φ · [i = j] )        (i = j: 0-0, 1-1, 2-2, 3-3, …)
```

`φ > 0` sposta massa **verso** i pareggi (a tutte le altezze), non solo 0-0/1-1.

**Come si stima `φ` (fittato nella verosimiglianza, non post-hoc).** Il termine della
log-verosimiglianza che dipende da `φ` si riduce a una **1-D** (formula chiusa):

```
ℓ(φ) = Σ_partite  w · [ ln(1 + φ·1{pareggio_reale})  −  ln(1 + φ·d_match) ]
```

dove `d_match` = P(pareggio) del **modello base per quella partita** (calcolata
vettorialmente riga per riga). Ecco perché è "dipendente dalla partita": pur essendo
`φ` un unico scalare, l'effetto è normalizzato dalla massa-pareggio *specifica* di
ogni match. Fittato con `φ ∈ [−0.5, 2.0]`; qui esce **~0.10-0.14** (positivo, come da
deficit-pareggio).

**Perché fa la cosa giusta ma non guadagna.** Il meccanismo **funziona**: `P(pari)`
sale verso il reale in OGNI stagione (2024-25: 0.264→0.288 vs reale 0.284,
quasi-perfetto). Migliora la *calibrazione media* del pareggio. Ma il log-loss guadagna
solo −0.0004 (3/6) perché **quanti** pareggi capitano in una stagione è in larga parte
**rumore**: dove ne capitano pochi (2025-26, reale 0.261) l'inflazione tarata sul
passato **sovrastima** e peggiora. È la prova definitiva: anche la mossa
strutturalmente corretta — quella indicata da tre analisi — dà lo stesso ordine di
grandezza (−0.0004) di ogni tampone, perché **il pareggio è quasi-casuale per tutti,
mercato incluso** (il 12 senza pari è già a livello mercato). Non è cattiva
modellazione: è irriducibilità del fenomeno.

---

## Fase 13 — Stato di forma: un pattern nascosto? (NO, gia' catturato)

**Obiettivo.** Verificare l'ultima intuizione: c'e' un momentum ("forma")
predittivo che la forza pesata nel tempo non vede? Il modello cattura la forma
GIA' in modo implicito (emivita 365g: le gare recenti pesano di piu'), e un
indizio c'era (l'emivita corta 180g, piu' reattiva, era peggio, Fase 12a). Ma
una covariata di forma ESPLICITA e' un segnale diverso dal ri-pesare: da provare.

**Feature.** `add_form` nel loader: `home_form`/`away_form` = punti per partita
nelle ultime 5 gare di ciascuna squadra prima di questa (no look-ahead, scorre
tra stagioni). Covariata `form`.

**Metodo: prima il diagnostico del pattern nascosto, poi la covariata.**

*(1) La forma predice l'ERRORE del modello?* Se le squadre in forma battono
sistematicamente l'aspettativa, c'e' segnale non catturato. Su 6 stagioni:
- **corr(forma_casa − forma_ospite, residuo punti casa) = +0.035** → ~zero.
- Residuo medio per terzile di differenza-forma: ~0 in ogni gruppo. Nessun bias
  sistematico legato alla forma.

*(2) Covariata `form` walk-forward (1X2 log-loss):* base 0.9797 → +form **0.9799
(+0.0002, peggio)**, 3/6 stagioni. Come `squad_value`: ridondante e un filo dannosa.

**Lezione.** **Nessun pattern nascosto nella forma.** La ragione e' strutturale:
la "forma" (punti recenti) SONO i risultati recenti, che il fit pesato nel tempo
gia' pesa di piu' → la forma esplicita e' quasi perfettamente collineare con la
forza recente che il modello stima. Il residuo del modello e' scorrelato dalla
forma (+0.035): non resta momentum da spremere. (Una forma su xG sarebbe ancora
piu' ridondante: l'xG e' gia' nel blend.) La covariata `form` resta off. Ottavo
esperimento convergente: il tetto e' reale, la forma non lo scalfisce.

**Riproducibilita'.** `python scripts/_run_form.py`.

---

## Fase 13-bis — Streak e rendimento recente: ricerca DATA-DRIVEN (nessun pattern)

**Obiettivo.** Uscire dall'arbitrarieta' della "finestra 5". Due intuizioni:
(a) **streak** (serie utile / di sconfitte in corso) invece di una media a finestra
fissa — effetti di soglia/psicologici; (b) guardare anche **gol fatti/subiti e xG**
recenti, lasciando che siano i **dati** a dire se c'e' un pattern, non soglie
scelte a mano. Solo Serie A (i risultati che abbiamo; le coppe in `club_fixtures`
non hanno i punteggi).

**Metodo.** Diagnostico: le feature di rendimento recente predicono l'ERRORE
(residuo punti casa) del modello walk-forward? Se il modello gia' cattura tutto,
il residuo e' scorrelato da qualsiasi rendimento recente.

**(1) Streak (`scripts/_run_streaks.py`).** corr con residuo: serie utile +0.041,
serie vittorie +0.030, serie sconfitte −0.004 → ~zero. I bucket per lunghezza
serie *sembrano* mostrare qualcosa (serie utile 10-14 → +0.135; sconfitte 3-4 →
+0.130) ma **i segni si ribaltano in modo erratico** (sconfitte 2→−0.157, 3-4→
+0.130, 5+→−0.159) su n=27-146: errore standard ~0.29 > effetti → **rumore**.

**(2) Ventaglio completo (`scripts/_run_recent_patterns.py`).** 23 feature (gol
fatti/subiti/differenza, xG fatti/subiti, "fortuna"=gol−xG, punti, serie),
finestre 3/5/10, differenziale casa-ospite, su 2273 partite. Verdetto in un
numero:

> **R² (residuo spiegato dal rendimento recente) = 0.0101**
> **R² atteso da puro rumore (23 feature / 2273 partite) = 0.0101** — IDENTICI.

Le correlazioni singole piu' alte sono l'**xG recente** (xgf10 +0.069, xga10
−0.058, gd10 +0.055): statisticamente sopra la soglia-rumore (2·SE≈0.042) ma
**minuscole** (~0.4% di varianza) e **collineari** → in multivariata l'R² non
supera il rumore. Le streak e i punti (risultati) sono ancora piu' deboli.

**Lezione.** **Nessun pattern nascosto nel rendimento recente**, ne' nelle streak
ne' nei gol/xG recenti, con qualunque finestra. La ragione e' la stessa della
forma: il rendimento recente (risultati E gol E xG) e' cio' che il fit **pesato
nel tempo** gia' usa e pesa di piu' → il residuo del modello non contiene
momentum residuo. L'unico filo di segnale (xG recente) e' gia' nel blend. Se
mai, conferma che l'xG e' la strada giusta — ma non ne resta da spremere.
Nono/decimo esperimento convergente: il tetto e' reale.

**(3) Interazione STREAK × avversario (`scripts/_run_streak_interaction.py`).**
Ipotesi mirata: una squadra in serie CONTRO un avversario debole sposta l'esito
oltre il modello. "Debolezza avversario" = favoritismo del modello (P(casa)−
P(ospite), out-of-sample). Risultato:
- corr(interazione streak×favoritismo, residuo) = **−0.005** (~zero);
- R² con interazione − R² senza = **+0.00003** (meno di quanto darebbe una feature
  di puro rumore, ~0.00044);
- Griglia 2×2 (residuo medio): casa in serie ≥5 & avversario debole = **−0.018**
  (n=224), perfino piu' basso di casa senza serie & avversario debole (+0.013).
  La cella che dovrebbe "accendersi" e' spenta.

L'interazione **non esiste**: il residuo del modello e' gia' condizionato a
entrambe le forze (l'avversario debole e' gia' prezzato), e la striscia non
aggiunge nulla nemmeno in combinazione. Chiude in modo definitivo il filone
"forma/streak/rendimento recente": il modello prezza gia' in modo ottimale tutto
cio' che sta nei risultati recenti.

**Riproducibilita'.** `python scripts/_run_streaks.py`,
`python scripts/_run_recent_patterns.py`, `python scripts/_run_streak_interaction.py`.

---

## Fase 14 — Il modello contro la linea di APERTURA (CLV) — NEGATIVO, e definitivo

**Obiettivo.** Tutti i confronti fatti finora erano contro le quote di
**chiusura** — lo stimatore piu' efficiente che esista, l'avversario piu' duro.
Ma nessuno e' obbligato a scommettere alla chiusura: si puo' prendere il prezzo
**prima**, quando la linea contiene meno informazione. Domanda: il modello batte
la linea **pre-chiusura** ("apertura")? Se si', esiste un edge *tradeable* anche
senza battere la chiusura — e il **CLV** (la chiusura si muove verso di noi?) e'
il criterio che i professionisti usano per distinguere edge da fortuna.

**Ragionamento.** Le colonne football-data senza suffisso "C" (AvgH...) sono
raccolte ~1-3 giorni prima della partita; quelle con "C" (dal 2019-20) sono la
chiusura. Le predizioni del modello non dipendono dalla quota → si riusano le 5
versioni x 6 stagioni di `analyze_gap` cambiando solo il benchmark, sempre sulle
STESSE righe (entrambe le linee presenti), altrimenti i log-loss non sono
comparabili. Onesta': la "apertura" football-data e' la linea del venerdi', non
l'apertura vera del mercato (piu' morbida ancora, ma non esiste nei dati storici).

**La saga dei dati (lezione di provenienza).** Il mirror GitHub storico
(`Mentaturan/ScoutFootball_for_World_Cup`, fonte di `BASE_URL` e dell'xG
Understat) **e' sparito da GitHub** (404 verificato fuori dal proxy): la
pipeline `--refresh` oggi non ha piu' una fonte a monte, e lo snapshot congelato
e' cio' che ha salvato il progetto — esattamente lo scenario per cui era stato
versionato. Nessun mirror alternativo conserva le quote (footballcsv e datahub
le spogliano; i dataset HF hanno un solo set). Soluzione: i **CSV originali**
scaricati dall'utente da football-data.co.uk e versionati in `data/football_data_raw/`
(fonte grezza congelata, README dedicato nella cartella) — ora la
fonte grezza congelata del repo (`scripts/_restore_raw_cache.py` li identifica
per data e ricostruisce la cache `data/raw/`).

**Risultato (30 backtest, `source=fase14_openline`; 2279/2280 righe comparabili).**

Gap 1X2 (model_ll − market_ll) per versione, STESSE righe:

| Versione | vs APERTURA | vs CHIUSURA |
|---|--:|--:|
| V0 grezzo | +0.0217 | +0.0237 |
| V1 gol tarato | +0.0166 | +0.0186 |
| V4 ATTUALE | **+0.0146** | **+0.0166** |

Versione attuale per stagione (gap vs apertura): +0.0199, +0.0089, +0.0115,
+0.0173, +0.0174, +0.0123 → **positivo in TUTTE e 6 le stagioni**. O/U 2.5:
gap vs apertura +0.0052 medio (batte l'apertura solo nel COVID 2020-21, −0.0029,
e nel 2023-24, −0.0046: non consistente).

Il test decisivo — value bet all'apertura e CLV (pool 6 stagioni):

| bet@open | ROI@open | CLV medio (prob) | CLV>0 |
|--:|--:|--:|--:|
| 692 | **−17.3%** | **−0.0028** | **45%** |

**Lezione / cosa ne consegue.**
1. **La linea del venerdi' e' gia' quasi-chiusura**: l'affilamento open→close
   vale solo **+0.0020** di log-loss (identico per ogni versione del modello,
   com'e' logico: e' una proprieta' del mercato, non nostra). L'informazione
   dell'ultimo giorno (formazioni, notizie) sposta poco la linea 1X2 media.
2. **Il modello non batte nemmeno l'apertura** (+0.0146, 6 stagioni su 6): il
   suo deficit e' 7 volte l'intero guadagno informativo open→close. Anche
   l'avversario "morbido" disponibile nei dati storici e' troppo affilato.
3. **CLV negativo (−0.0028, 45% positivo)**: quando il modello dissente
   dall'apertura, la chiusura si muove **contro** di lui piu' spesso che verso.
   I dissensi del modello sono rumore, non informazione che il mercato deve
   ancora incorporare. E' la morte pulita dell'ipotesi "scommetti presto":
   ROI@open −17.3% (peggio del ROI@close −15.6%).
4. Resta aperta (non testabile con questi dati) solo la linea di apertura VERA
   (domenica sera/lunedi'), piu' morbida del venerdi'. Servirebbe raccolta
   prospettica di quote in tempo reale — un progetto dati, non un backtest.
5. Nona conferma convergente del quadro: l'edge non e' nei dati storici. Le vie
   rimaste sono quelle gia' indicate: dati davvero nuovi (formazioni ufficiali)
   o mercati strutturalmente meno efficienti della Serie A 1X2.

**Riproducibilita'.** `python scripts/_restore_raw_cache.py && python
scripts/build_database.py --open-odds && python scripts/_run_fase14_openline.py`.

---

## Fase 15 — Audit dei calcoli (verifica indipendente; 1 errore vero trovato)

**Obiettivo.** Prima di investire altro lavoro sul modello: c'e' qualche errore
di calcolo nei backtest fatti finora? Verifica sistematica di formule, pipeline
e di OGNI numero dichiarato in README/DIARIO.

**Ragionamento / metodo.** Quattro verifiche indipendenti e incrociate:
(1) audit del codice di modello e metriche (formule, segni, allineamenti,
look-ahead); (2) audit di tutti gli script di fase; (3) ricalcolo a precisione
piena di ogni numero di README/DIARIO dal registro `runs.jsonl` (233 run);
(4) ri-esecuzione del backtest ufficiale dallo snapshot congelato.

**Risultato.**
- **Formule: nessun errore.** Log-loss, Brier, devig, correzione DC τ,
  verosimiglianza dell'inflazione diagonale, temperature scaling, blend: tutto
  corretto. Walk-forward pulito (`date < as_of` ovunque, nessun leakage
  per-partita). Backtest ufficiale **riprodotto identico** alla 4ª cifra.
- **1 errore numerico vero**: il ROI del value betting nel README (**≈ −8.5%**)
  era il valore della Fase 1 (una stagione, modello iniziale); quello reale
  della config ufficiale su 6 stagioni e' **−15.7% medio** (da −4.7% a −23.0%,
  864 scommesse). Corretto. La conclusione "non scommettere" si rafforza.
- **Sbavature corrette**: tabella Fase 2b di questo diario (riga "puro"
  incoerente), O/U ufficiale 0.6885 (non 0.6884), ~86% di distanza chiusa (non
  ~87%), baseline 1.0834 (non ~1.085), guadagno Fase 4d −0.0006/−0.0009 (non
  ~0.0007), doppia stima del prior (−0.0010 δ fisso / −0.0011 leave-future-out)
  ora spiegata.
- **Limiti metodologici dichiarati** (non correggibili a posteriori senza
  rifare la storia): baseline in-sample (quella ex-ante onesta e' 1.0860/0.6961:
  il modello batte anche quella); iperparametri tarati su stagioni poi
  riportate — ma il gap sulle stagioni MAI usate per il tuning (+0.0164,
  2020-23) e' indistinguibile da quello sulle stagioni di tuning (+0.0166,
  2023-26), quindi nessuna evidenza di overfitting di selezione; costanti
  RECAL_W e δ=0.23 fisso col senno di poi negli script delle fasi 10-12 (i Δ
  onesti restano i leave-future-out); tier di `analyze_gap` dalla classifica
  finale (diagnostica, non operativa); streak (Fase 13) senza reset tra
  stagioni (impatto marginale).
- **Fix preventivi alla Fase 14** (prima che arrivino i dati): niente righe
  open≡close spurie nel CLV; metriche modello/apertura sulle stesse righe nel
  registro.
- **Registro completato e numeri riconfermati**: le run delle Fasi 11, 12a e 13
  (assenti da `runs.jsonl` nonostante la promessa di replicabilita') sono state
  ri-eseguite (96 backtest, registro a 329 run) e i numeri pubblicati sono
  usciti **identici**: blend 180+730 = 0.9791 (−0.0006, 4/6); forma +0.0002
  (corr +0.0353); miglior combo −0.0011 (+absence+rest_full +RECAL, rumore
  selezionato), squad_value peggiora in ogni mix.

**Lezione.** L'errore sopravvissuto piu' a lungo non era in una formula ma in un
**numero copiato tra contesti diversi** (ROI di Fase 1 accanto a metriche a 6
stagioni). Il registro automatico funziona: tutto cio' che passava da
`runs.jsonl` era giusto; gli errori vivevano solo nei documenti scritti a mano e
negli script che NON registravano le run. Regola rafforzata: ogni numero
pubblicato deve essere ricalcolabile dal registro.

---

## Fase 15-bis — Gap per mercato, stagione per stagione (la matrice completa)

**Obiettivo.** La Fase 9 aveva scomposto il gap per mercato solo in aggregato
(pool 6 stagioni) e per stagione solo sull'1X2. Domanda: le medie per-mercato
nascondono stagioni storte? Il "quasi-zero" del mercato 12 regge sempre?

**Ragionamento.** Una media a 6 stagioni puo' coprire una varianza enorme (l'O/U
lo dimostrera'). Prima di trarre conclusioni operative da un gap medio serve la
matrice completa mercato x stagione, con la config ufficiale e le stesse
convenzioni di analyze_gap (gap = model_ll − market_ll; GG/NG vs baseline
perche' non ha quote).

**Alternative.** Estendere analyze_gap.py (gia' lungo, 4 assi) o script
dedicato: scelto lo script dedicato (`scripts/_run_gap_markets.py`), che
registra le 6 run in `runs.jsonl` (regola Fase 15).

**Risultato** (gap col mercato; >0 = mercato migliore):

| Gap | 2021 | 2122 | 2223 | 2324 | 2425 | 2526 | media |
|---|--:|--:|--:|--:|--:|--:|--:|
| 1X2 | +0.0202 | +0.0145 | +0.0146 | +0.0187 | +0.0170 | +0.0141 | +0.0165 |
| 1X | +0.0160 | +0.0082 | +0.0089 | +0.0175 | +0.0082 | +0.0108 | +0.0116 |
| 2X | +0.0151 | +0.0105 | +0.0127 | +0.0128 | +0.0156 | +0.0096 | +0.0127 |
| 12 (no pari) | +0.0017 | +0.0031 | +0.0021 | −0.0021 | +0.0050 | +0.0022 | +0.0020 |
| O/U 2.5 | −0.0031 | +0.0147 | +0.0168 | +0.0007 | +0.0101 | +0.0020 | +0.0069 |
| GG/NG (vs base) | +0.0074 | −0.0054 | +0.0069 | −0.0003 | +0.0037 | +0.0039 | +0.0027 |

Tre fatti:
1. **Il 12 e' a livello mercato in OGNI stagione** (−0.0021…+0.0050; nel
   2023-24 il modello lo batte). Non e' un artefatto della media.
2. **Il costo del pareggio e' strutturale**: 1X/2X restano a +0.008…+0.018 in
   tutte le stagioni, ~5x il 12. Nessuna annata in cui il modello "impara" il
   pari.
3. **L'O/U e' il mercato piu' volatile** (σ tra stagioni ~0.008, range 0.02):
   dal battere il mercato (COVID) al gap peggiore di tutti (2022-23). Una
   stagione buona sull'O/U non e' segnale.

**Lezione.** La media aggregata della Fase 9 era rappresentativa per i mercati
d'esito (12 stabile, pari stabile) ma NON per l'O/U, dove il gap medio +0.0069
e' quasi privo di significato operativo (varianza della stessa scala del
valore). Conferma la gerarchia: esiti > totali-gol per affidabilita' del
modello.

**Riproducibilita'.** `python scripts/_run_gap_markets.py` (6 run registrate,
source `gap_markets`).

---

## Fase 16 — Encompassing: il modello ha informazione propria? (NO, α*=0)

**Obiettivo.** L'ultima domanda che il gap non puo' dire: un modello a +0.0165
dal mercato puo' comunque contenere informazione INDIPENDENTE (utile in blend,
monetizzabile su mercati meno efficienti) oppure e' mercato degradato con
rumore? E' la distinzione tra "modello inutile" e "modello con segnale proprio
ma non abbastanza".

**Ragionamento.** Test standard di forecast encompassing: p_blend =
α·modello + (1−α)·mercato, α stimato minimizzando la log-loss. Se il mercato
"ingloba" il modello, α*≈0; se α*>0 stabile e il blend migliora out-of-sample,
c'e' segnale proprio.

**Alternative.** Regressione logistica sui residui del mercato (equivalente ma
meno leggibile) o blend fittato in-sample (barare). Scelto il blend con α
fittato SOLO sulle stagioni di test precedenti, applicato alla successiva
(walk-forward onesto; la prima stagione non e' valutabile → 5 valutazioni).
L'α* in-sample per stagione e' riportato come descrittivo.

**Risultato** (`scripts/_run_encompassing.py`; 6 run + summary nel registro,
source `fase16_encompassing`):
- α* in-sample = **0.000 in TUTTE le stagioni** (≤10⁻⁵): anche potendo barare,
  il fit non da' alcun peso al modello;
- α walk-forward = 0.000 ovunque → blend ≡ mercato, Δ pooled +0.0000,
  CI95 [−0.0000, +0.0000] (bootstrap appaiato, B=10.000, n=1900);
- verdetto: **il mercato di chiusura ingloba completamente il modello**.

**Lezione.** Il gap +0.0165 non e' "informazione nostra meno informazione
loro": e' informazione loro + il nostro rumore di stima. Converge con il CLV
negativo della Fase 14 (due test indipendenti, stessa conclusione). Contro la
chiusura non c'e' NULLA da monetizzare, nemmeno in combinazione; l'unica
speranza pratica residua sono avversari meno efficienti (exchange sottili,
leghe minori) — questione empirica aperta, non promessa.

---

## Fase 17 — Intervalli di confidenza: quali numeri sono reali e quali rumore

**Obiettivo.** Dare barre d'errore ai quattro numeri che reggono le
conclusioni: gap 1X2, gap 12, gap O/U, Δ del prior neopromosse (l'unica
feature adottata).

**Ragionamento / metodo.** Bootstrap APPAIATO per-partita (si ricampionano le
differenze di log-loss della stessa partita, B=10.000, seed fisso, pooled 6
stagioni, n=2280). Per il Δ prior: V4 e V3 rifatti sulle stesse partite
(allineamento verificato per costruzione).

**Risultato** (`scripts/_run_gap_uncertainty.py`; 12 run + summary nel
registro, source `fase17_bootstrap`):

| quantita' | media | CI95 | P(modello meglio / prior aiuta) |
|---|--:|--:|--:|
| gap 1X2 | +0.0165 | [+0.0106, +0.0225] * | 0.0% |
| gap 12 (no pari) | +0.0020 | [−0.0006, +0.0046] | 6.5% |
| gap O/U 2.5 | +0.0069 | [+0.0022, +0.0116] * | 0.2% |
| Δ prior (V4−V3) | −0.0010 | [−0.0025, +0.0004] | 92.6% |

*(\* = CI95 che non attraversa lo zero.)* Per stagione (gap 1X2): CI tipico
±0.014 → 3 stagioni su 6, da sole, non distinguerebbero il modello dal
mercato: e' la giustificazione statistica della regola "mai giudicare da una
stagione".

**Lezione (tre punti onesti).**
1. Il gap 1X2 e l'O/U sono REALI (CI lontani da zero): il mercato e' davvero
   migliore, non e' varianza.
2. Il "quasi-zero" del 12 e' ora un'affermazione statistica: sul "chi vince"
   siamo formalmente indistinguibili dal mercato.
3. Il Δ del prior (−0.0010) NON e' conclusivo da solo (CI include lo zero,
   P(aiuta)~93%). Resta adottato perche' coerente (5/6 stagioni), concentrato
   dove deve agire (−0.0039 sulle promosse) e motivato strutturalmente — ma la
   dichiarazione corretta e' "probabilmente utile", non "dimostrato". Con ~30
   test sulle stesse 6 stagioni, qualunque futuro CI che sfiora lo zero va
   letto come "non concluso".

---

## Fase 18 — Rho dinamico: l'ultima idea strutturale sul pareggio (NEGATIVA)

**Obiettivo.** Il rho di Dixon-Coles e' un numero unico per tutte le partite.
Ipotesi (l'unica strutturale mai provata dopo la 12b): la correlazione dei
punteggi bassi varia con la partita — un match da 1.8 gol attesi ha dinamiche
di 0-0/1-1 diverse da uno da 3.5.

**Ragionamento.** rho_match = rho + rho_slope*(lam+mu − centro), con rho_slope
stimato NELLA verosimiglianza (non post-hoc) e centro = media pesata dei gol
totali del training (costante fissata prima del fit). rho_slope=0 riproduce
esattamente il modello classico (test di regressione in tests/).

**Alternative.** Spline/bucket di rho per fascia di gol attesi (piu' parametri,
piu' overfitting) o rho per-squadra (gia' escluso in Fase 8 per il
vantaggio-casa: non persiste). Scelta la parametrizzazione lineare a 1
parametro: la versione economica dell'idea.

**Regola di decisione dichiarata PRIMA di vedere i numeri** (disciplina Fase
17): adozione solo se il CI95 bootstrap del Δ esclude lo zero.

**Risultato** (`scripts/_run_dynrho.py`; 13 run nel registro, source
`fase18_dynrho`):
- diagnostico del parametro (fit al via di ogni stagione): rho_slope
  **instabile** — +0.06, −0.11, +0.15, −0.08, +0.15, +0.15 — cambia segno e
  sbatte sul bound (±0.15) in 3 fit su 6;
- walk-forward 6 stagioni: Δ **+0.0003**, CI95 [−0.0007, +0.0013],
  P(migliora)=25.9%; O/U −0.0000 [−0.0007, +0.0006];
- regola pre-dichiarata → **NON si adotta**.

**Lezione.** Doppia firma del rumore: parametro senza segno stabile E nessun
guadagno out-of-sample. Con la ricalibrazione per-classe (Fase 10) e la
diagonale inflazionata (Fase 12b), e' la **terza e ultima via strutturale sul
pareggio a chiudersi**: il tetto non dipende dalla forma funzionale della
correzione, ma dall'informazione disponibile. Nota di metodo: dichiarare la
regola di adozione prima di vedere i numeri costa zero e vale molto.

---

## Fase 19 — Potenza sul prior: 8 stagioni (l'evidenza si rafforza, non conclude)

**Obiettivo.** Il Δ del prior neopromosse (unica feature adottata) era
"probabile ma non concluso" in Fase 17 (CI [−0.0025, +0.0004], P~93%). Colpa
dell'effetto o del campione? Le partite-promosse in 6 stagioni sono solo 648.

**Ragionamento.** Il dataset ha 9 stagioni ma i test ne usavano 6: le stagioni
2018-19 e 2019-20 non sono MAI state usate in nessuna analisi (il 2017-18
resta solo-training). Estenderle e' potenza gratis e genuinamente
out-of-sample rispetto a ogni scelta fatta finora. Caveat dichiarato: δ=0.23
(stima storica Fase 7) include informazione 2018-20, quindi per le due
stagioni aggiunte il VALORE del prior non e' leave-future-out: e' un test di
potenza sull'effetto della config adottata, non una nuova stima di δ.

**Risultato** (`scripts/_run_prior_power.py`; 17 run nel registro, source
`fase19_prior_power`):

| pool | media | CI95 | P(aiuta) | n |
|---|--:|--:|--:|--:|
| tutte, 8 stagioni | −0.0013 | [−0.0026, +0.0001] | 96.5% | 3040 |
| solo promosse | −0.0045 | [−0.0094, +0.0001] | 97.0% | 864 |
| (Fase 17, 6 stagioni) | −0.0010 | [−0.0025, +0.0004] | 92.6% | 2280 |

Le due stagioni aggiunte confermano ENTRAMBE il prior (Δ −0.0024 e −0.0014;
sulle promosse −0.0093 e −0.0045); l'effetto aiuta in 7 stagioni su 8 (l'unica
contraria resta il 2023-24, promosse piu' forti della media).

**Lezione.** L'evidenza si muove nella direzione giusta man mano che arrivano
dati (93% → 96.5%): comportamento da effetto reale piccolo, non da rumore. Ma
il CI sfiora ancora lo zero (+0.0001): per la disciplina multiple-testing il
verdetto resta "**molto probabile, formalmente non concluso**". Il prior resta
adottato; l'etichetta onesta migliora. Per chiudere davvero servirebbero altre
~2-3 stagioni di dati nuovi (o piu' leghe).

---

## Fase 20 — Anatomia dei residui: nessun segnale nascosto, ma si scopre il PERCHE'

**Obiettivo.** La Fase 13 aveva testato solo "la forma" come predittore
dell'errore del modello. Domanda completa: QUALCUNA delle covariate pre-partita
disponibili predice il residuo del modello? Incluse quelle di ESTREMITA' mai
provate (lo scarto di valore-rosa e' gia' stato bocciato come valore assoluto in
Fase 4c, ma il suo MODULO — mismatch estremo — no).

**Ragionamento.** Due domande in una:
1. il residuo (punti reali casa − attesi) e' predetto da 11 covariate
   pre-partita? Regressione multivariata con benchmark di rumore (R²≈k/n +
   200 draw di feature casuali), come in Fase 13.
2. il modello perde di piu' dove DISSENTE dal mercato? (adverse selection: se
   si', i "value bet" del modello sono i suoi errori — spiegherebbe il ROI).

**Alternative.** Target = gap vs mercato invece di residuo vs esito (piu'
diretto ma confonde errore-modello con forza-mercato); scelto il residuo vs
esito per la Parte 1 (continuita' con Fase 13) e il gap per la Parte 2
(adverse selection). Feature di estremita' incluse esplicitamente perche' sono
l'unica classe mai testata.

**Risultato** (`scripts/_run_residuals.py`; 7 run nel registro, source
`fase20_residuals`):

*Parte 1 — il residuo e' rumore puro.* R² multivariata = **0.0055** vs 0.0048
(k/n) e 0.0051 (feature casuali). Ogni covariata a livello rumore; le tre di
estremita' sono le piu' piatte (|scarto valore| −0.0018, |scarto riposo|
−0.0046, assenze totali −0.0011). Nullo gia' in-sample → a fortiori
out-of-sample. Nessun pattern nascosto oltre la forma.

*Parte 2 — adverse selection, forte e pulita.* Il gap vs mercato cresce
monotono coi quartili di dissenso modello-mercato:

| quartile dissenso | n | gap medio |
|---|--:|--:|
| basso | 570 | +0.0009 |
| medio-basso | 570 | +0.0024 |
| medio-alto | 570 | +0.0088 |
| alto | 570 | +0.0539 |

corr(dissenso, gap) = **+0.18**. Dove il modello dissente di piu' — cioe' dove
segnalerebbe un value bet — perde ~60 volte di piu'.

**Lezione.** Due conclusioni. (1) Il residuo non contiene struttura sfruttabile
con NESSUNA covariata disponibile: l'analisi dei residui e' chiusa. (2) Ma
l'adverse selection e' il **meccanismo operativo** del fallimento: i disaccordi
del modello sono i suoi errori, non la sua intuizione. Chiude il cerchio con
l'encompassing (Fase 16, α*=0) e il CLV negativo (Fase 14) — tre viste dello
stesso fatto. E' il risultato che rende ONESTO il "non scommettere": non "il
modello e' un po' peggio", ma "ogni volta che il modello crede di avere ragione
contro la chiusura, ha torto in media".

---

## Fase 21 — Un modello diverso sul GG/NG: gradient boosting (pareggia, non batte)

**Obiettivo.** Primo modello di famiglia diversa dal Dixon-Coles e primo test
del principio "un modello per mercato" (CLAUDE.md §8). Bersaglio: il GG/NG,
dove il DC e' debole (Fase 5: peggio della baseline, cattura male la
correlazione dei punteggi) e — cruciale — l'unico mercato SENZA quote nei dati,
quindi l'unico dove il tetto di efficienza (Fasi 14/16/20) non e' dimostrato.

**Ragionamento.** Un gradient boosting che predice P(GG) direttamente, con
feature = output del DC (gol attesi lam/mu, P(GG), P(over), tutti walk-forward)
+ covariate pre-partita (forma, riposo, valore rosa, assenze). Cosi' il GBM
puo' imparare la correzione di correlazione non-lineare che al DC manca,
partendo pero' dall'informazione che il DC gia' estrae.

**Alternative.** Modello a punteggio con correlazione esplicita (bivariato
Poisson) o GBM sulle sole covariate grezze. Scelto lo stacking DC+GBM: la
versione piu' potente e onesta (il GBM ha tutto cio' che ha il DC, piu' spazio
per correggerlo). Walk-forward per stagione (allena su 1819..S-1); niente
look-ahead ne' nelle feature ne' nel target.

**Controllo di equita' (decisivo).** Il log-loss punisce durissimo la
mis-calibrazione, e un boosting e' sovra-confidente su un evento ~50/50. Per
non incolpare il modello di un difetto di taratura, valutata anche una versione
CALIBRATA (Platt in cross-validation sul solo training).

**Regola di adozione (dichiarata PRIMA dei numeri):** il GBM (raw o calibrato)
entra come modello ufficiale del GG/NG solo se batte il DC con CI95<0 E almeno
pareggia la baseline (che il DC non batteva).

**Risultato** (`scripts/_run_gbm_btts.py`; 9 run nel registro, source
`fase21_gbm_btts`):

| | log-loss GG/NG | Δ vs DC (CI95) |
|---|--:|--:|
| GBM grezzo | 0.7178 | +0.0280 [+0.0167, +0.0391] |
| GBM calibrato | 0.6945 | +0.0047 [−0.0019, +0.0113] |
| Dixon-Coles | 0.6898 | — |
| baseline (in-sample) | 0.6871 | — |

- il GBM grezzo sembrava un disastro, ma era quasi tutto **mis-calibrazione**:
  calibrato, il divario dal DC crolla da +0.0280 a +0.0047 (CI che include lo
  zero; batte il DC in 2 stagioni su 6);
- ma il GBM calibrato **non batte il DC** ne' la baseline; **nessuno dei due
  batte la baseline** sul GG/NG;
- regola pre-dichiarata → **non adottato**.

**Lezione.** Due conclusioni. (1) Metodologica: il controllo di calibrazione e'
stato decisivo — senza avremmo concluso il falso ("GBM molto peggio"); la
verita' e' "GBM pareggia il DC una volta calibrato". Da tenere per ogni modello
nuovo. (2) Sostanziale: una famiglia di modelli COMPLETAMENTE diversa, con
pieno accesso ai lam/mu del DC e alle covariate, atterra sullo STESSO punto —
a livello della frequenza di base. E' **convergenza sul tetto**, non fallimento
del GBM: il GG/NG e' intrinsecamente quasi-impredicibile dai dati pre-partita
in Serie A, come il pareggio. Il principio "un modello per mercato" resta
valido per i prossimi tentativi; ma questo mercato, col miglior candidato
ragionevole, non cede — e il fatto che un modello non-parametrico non trovi
nulla oltre il DC abbassa molto le attese anche per un bivariato Poisson.

---

## Fase 22 — Sweep del GBM su tutti i mercati: il tetto e' informativo, non di modello

**Obiettivo.** La Fase 21 ha provato il GBM solo sul GG/NG. Qui lo spremiamo:
molte varianti su molti mercati, per vedere se su QUALCUNO il GBM muove il gap
col mercato rispetto al Dixon-Coles. E' il test a fondo del principio 8.

**Ragionamento.** 6 mercati (1X2, O/U 2.5, GG/NG, doppie chance 1X/2X/12) x 3
set di feature (cov = solo covariate pre-partita; dc = solo output del DC;
dc+cov = entrambe) x calibrazione. Ogni GBM walk-forward per stagione (allena
su 1819..S-1). Headline calibrata (la Fase 21 ha mostrato che il grezzo mente
per mis-calibrazione). Verdetto inferenziale sulla variante pre-scelta dc+cov
calibrata, gap vs mercato con CI bootstrap appaiato per-riga.

**Alternative.** Sweep di iperparametri (profondita', regolarizzazione) invece
dei feature-set: scartato in favore dei feature-set, che rispondono alla
domanda vera ("da dove viene il segnale?"). Un tuning fine avrebbe al piu'
avvicinato il GBM al DC, non battuto — vedi la lezione sotto.

**Risultato** (`scripts/_run_gbm_sweep.py`; 9 run nel registro, source
`fase22_gbm_sweep`). Log-loss calibrata, miglior feature-set del GBM:

| mercato | GBM migliore | DC | mercato | baseline |
|---|--:|--:|--:|--:|
| 1X2 | 1.0059 | 0.9797 | 0.9632 | 1.0834 |
| O/U 2.5 | 0.6966 | 0.6885 | 0.6816 | 0.6892 |
| GG/NG | 0.6943 | 0.6898 | — | 0.6871 |
| 1X | 0.5572 | 0.5487 | 0.5371 | 0.6303 |
| 2X | 0.6097 | 0.5960 | 0.5833 | 0.6744 |
| 12 | 0.5811 | 0.5766 | 0.5746 | 0.5820 |

Movimento del gap (Δ = GBM − DC appaiato per-riga):

| mercato | Δ gap | CI95 |
|---|--:|--:|
| 1X2 | +0.0310 | [+0.0217, +0.0402] |
| O/U 2.5 | +0.0081 | [+0.0005, +0.0157] |
| GG/NG | +0.0045 | [−0.0023, +0.0111] (pari) |
| 1X | +0.0141 | [+0.0066, +0.0216] |
| 2X | +0.0198 | [+0.0131, +0.0263] |
| 12 | +0.0051 | [+0.0015, +0.0086] |

- il GBM **non batte il DC su nessun mercato**; allarga il gap ovunque, con CI
  che esclude lo zero su 5 mercati su 6 (solo il GG/NG pareggia, entrambi a
  livello baseline);
- il GBM fa MEGLIO quando usa SOLO le feature del DC (dc batte dc+cov e cov su
  1X2/1X/2X): aggiungere covariate grezze peggiora → rende al meglio quando
  modifica MENO il DC.

**Lezione.** Due famiglie di modelli (parametrica e non), 6 mercati, 3
feature-set: il tetto e' **informativo, non architetturale**. La forma del
Dixon-Coles non e' il collo di bottiglia — lo sono i dati pre-partita. Il
segnale utile e' tutto e solo quello che il DC gia' estrae (gol/xG pesati nel
tempo); ogni grado di liberta' in piu' aggiunge rumore, che sui mercati con
quote il mercato ha gia' prezzato (gap che cresce). Il principio "un modello per
mercato" era corretto da testare e ora e' testato a fondo: su questi dati
nessun mercato cede. Per un edge serve **informazione nuova**, non un modello
nuovo. Chiude il filone "modelli alternativi" avviato in Fase 21.

---

## Fase 23 — GBM modello + mercato: si puo' ridurre il gap? (no, non con un GBM)

**Obiettivo.** Ultima leva per ridurre il gap col mercato: l'unica informazione
mai data al modello sono le QUOTE di mercato stesse. Un GBM che le riceve puo'
(a) correggere inefficienze non-lineari della linea e batterla, o almeno (b)
riprodurla, portando il gap a ~0?

**Ragionamento.** Encompassing NON-lineare: la Fase 16 aveva mescolato
alpha*modello+(1-alpha)*mercato (lineare, alpha*=0 -> mercato ottimo). Un GBM su
[DC + covariate + quote devigate di chiusura] cattura bias non-lineari
(favourite-longshot, mispricing del pareggio per fascia) che un alpha scalare non
vede. Le quote di chiusura sono pre-esito: usarle come feature e' lecito (nessun
look-ahead sull'outcome), ma e' informazione del mercato.

**Alternative.** Blend lineare gia' fatto (Fase 16). Regressione logistica sulle
quote (equivalente al GBM ma meno flessibile). Scelto il GBM: la forma piu'
potente per trovare struttura non-lineare, se c'e'.

**Regola (dichiarata prima):** "edge sul mercato" solo se il GBM-con-mercato
batte il MERCATO con CI95 del gap < 0. Pareggiarlo (gap ~0) non e' un edge ma un
miglioramento come stimatore per un mercato diverso.

**Risultato** (`scripts/_run_gbm_market.py`; 9 run, source `fase23_gbm_market`):

| 1X2 | log-loss | gap vs mercato |
|---|--:|--:|
| DC | 0.9797 | +0.0165 |
| GBM senza mercato | 1.0114 | +0.0482 |
| GBM con mercato | 0.9996 | +0.0364 |
| mercato | 0.9632 | 0 |

(O/U: GBM con mercato 0.6956 vs DC 0.6885 vs mercato 0.6816.)

- il GBM-con-mercato NON batte il mercato (P=0%, CI [+0.0275, +0.0454]);
- piu' sorprendente: non lo **pareggia** nemmeno, e resta **peggio del DC da
  solo** (0.9996 vs 0.9797). Anche ricevendo le probabilita' di mercato, il GBM
  le degrada;
- il mercato come feature AIUTA il GBM rispetto a se stesso (1.0114 -> 0.9996):
  porta informazione che le altre feature non hanno, ma non basta.

**Lezione.** Il mercato di chiusura e' una previsione quasi-ottima, e un ensemble
di alberi non puo' che degradarla (quantizza/regolarizza un input probabilistico
near-optimal, aggiungendo rumore). Sintesi su "ridurre il gap": a ~0 si arriva
solo BANALMENTE copiando il mercato (gia' noto dalla Fase 16, peso sul mercato
~1); sotto zero (batterlo) NO, con nessun metodo lineare o non-lineare, con o
senza il mercato come input. Il GBM e' lo strumento sbagliato per combinare
modello e mercato: il modo giusto e' lineare, e la Fase 16 ha gia' dato il
verdetto. Chiude la ricerca di un metodo per ridurre il gap.

---

## Fase 24 — DC calcolato DAL mercato: il primo risultato positivo dell'arco modelli

**Obiettivo.** Nessuna fase l'aveva fatto: finora il DC stima lambda,mu dai GOL,
e finora abbiamo sempre MESCOLATO gli output (DC+mercato) o dato il mercato a un
GBM. Domanda nuova: e se COSTRUISSIMO il DC a partire dal mercato? Il mercato
stima lambda,mu meglio di noi (batte il DC di +0.0165 sull'1X2); invertendo le
quote si ricavano i lambda,mu impliciti, e la matrice del DC ci deriva sopra gli
altri mercati.

**Ragionamento.** Sui mercati CON quote (1X2, O/U) l'inversione riproduce il
mercato -> gap ~0 banale. Il valore e' tutto nel DERIVARE un mercato che il book
NON prezza: il GG/NG (nessuna quota nei dati, l'unico con "spazio" per il
principio 8). Se lambda,mu del mercato + struttura DC battono il nostro GG/NG e
la baseline, e' l'informazione superiore del mercato trasferita a un mercato non
prezzato — non circolare (il GG/NG non e' tra gli input), non un edge contro un
mercato efficiente.

**Metodo.** Per ogni partita: devig 1X2 + O/U -> 4 probabilita' target; si trova
(lambda,mu) che le riproduce meglio via la matrice a Poisson indipendenti
(rho=0; il mercato 1X2+O/U non vincola rho). Da quella matrice si legge P(GG).
Sensibilita' con un rho della diagonale (-0.06, correzione dei punteggi bassi).

**Alternative.** Prior di forza dal mercato nel fit del DC (piu' invasivo);
scelto il piu' pulito: inversione per-partita, nessun ri-fit.

**Risultato** (`scripts/_run_dc_from_market.py`; 7 run, source
`fase24_dc_from_market`):

| GG/NG | log-loss |
|---|--:|
| mercato-implicito + rho | 0.6853 |
| mercato-implicito (rho=0) | 0.6865 |
| DC-da-gol (attuale) | 0.6898 |
| baseline (in-sample) | 0.6871 |

- il GG/NG dai lambda,mu del mercato BATTE il nostro DC-da-gol: Δ -0.0033, CI95
  [-0.0072, +0.0005], P=95.7%, negativo in 6 stagioni su 6;
- e' la PRIMA cosa a battere la baseline sul GG/NG (0.6865 < 0.6871; il DC-da-gol
  no); la correzione rho aiuta ancora (0.6853).

**Lezione.** Dopo 8 risultati negativi sui modelli (Fasi 18, 21-23), il primo
positivo — e viene da una domanda giusta: non "quale modello", ma "quale
informazione, e come trasferirla". Il mercato conosce i gol attesi meglio di noi;
la struttura del DC li porta su un mercato non prezzato. Onesta': (1) il CI
sfiora lo zero -> "molto probabile, formalmente non concluso" (come il prior,
Fase 19); (2) guadagno modesto, il GG/NG resta difficile (~0.685 vicino al
testa-o-croce); (3) non verificabile contro un'ipotetica linea GG/NG; (4)
richiede le quote 1X2+O/U al momento della predizione (il DC-da-gol no) + un
venue che offra il GG/NG. Come stimatore CONDIZIONATO alle quote, il GG/NG
"specialista" (principio 8) diventa: inverti il mercato -> matrice DC -> P(GG),
invece del DC-da-gol. E' la prova che la leva vera e' l'informazione (qui: quella
del mercato su un mercato non prezzato), non l'architettura.

---

## Fase 25 — Finestra dei dati: piu' storia batte meno (anche per il calcio di oggi)

**Obiettivo.** Il modello scorda il passato in modo MORBIDO (emivita 365g).
Ipotesi da testare (proposta: "fai finta che il calcio pre-COVID non sia
esistito"): tagliare via del tutto le stagioni vecchie, o la sola stagione COVID
a porte chiuse (anomala), aiuta le stagioni recenti?

**Ragionamento.** L'emivita e' un decadimento morbido (una partita di 3 stagioni
fa pesa <0.06). Un taglio NETTO e' diverso: rimuove del tutto quei dati. Se il
calcio evolve, i dati vecchi potrebbero fare rumore -> finestra corta meglio. Se
invece le rose sono stabili, i dati vecchi informano ancora -> finestra corta
peggio (piu' varianza).

**Metodo.** Aggiunti al backtest ``train_window_days`` (taglio netto) e
``drop_train_seasons`` (esclude intere stagioni), senza toccare test o
neopromosse. Sweep sulla config ufficiale, 6 test season, spezzato in
recenti-3 (2023-26) vs vecchie-3 (2020-23).

**Risultato** (`scripts/_run_window.py`; 24 run, source `fase25_window`):

| training | 1X2 tutte | gap | Δ vs "tutto" (recenti-3) |
|---|--:|--:|--:|
| tutto (attuale) | 0.9797 | +0.0165 | — |
| finestra 3 stag | 0.9808 | +0.0176 | +0.0014 |
| finestra 2 stag | 0.9816 | +0.0184 | +0.0035 |
| senza COVID 2020-21 | 0.9803 | +0.0172 | +0.0003 |

Controintuitivo: tagliare i dati vecchi PEGGIORA, e la finestra corta danneggia
DI PIU' proprio le stagioni recenti (+0.0035 sul 2023-26 con 2 stagioni). Perfino
la stagione COVID e' netto-utile (escluderla costa +0.0007).

**Lezione.** Piu' storia batte meno, sempre: le rose di Serie A sono stabili anno
su anno, quindi anche i dati vecchi informano la forza attuale, e buttarli via
aumenta solo la varianza. L'emivita 365g gestisce gia' la recency in modo
ottimale; un taglio netto in aggiunta e' dannoso. Conferma e rafforza la Fase 2b
(memoria lunga). Nota: il parametro ``train_window_days`` resta nel backtest per
leghe piu' volatili, dove il verdetto potrebbe cambiare.

---

## Fase 26 — Market-implied su TUTTI i mercati sui gol (il risultato piu' forte)

**Obiettivo.** La Fase 24 ha mostrato che il GG/NG derivato dai lambda,mu del
mercato batte il nostro DC-da-gol e la baseline. Domanda: vale per OGNI mercato
sui gol? Costruire il motore completo e provarlo a fondo (molte strade).

**Ragionamento.** Il mercato stima lambda,mu meglio di noi (+0.0165 sull'1X2);
la matrice del DC li trasferisce coerentemente a ogni mercato basato sui gol,
inclusi quelli che il book NON prezza. Sui mercati con quote (1X2, O/U 2.5)
l'inversione riproduce il mercato (ancoraggi); il valore e' nei mercati derivati.

**Metodo.** Modulo riutilizzabile `src/models/market_implied.py` (inversione ai
minimi quadrati + derivazione di tutti i mercati dalla matrice), con test. Sweep
`scripts/_run_market_implied.py`: ~15 mercati, walk-forward per stagione, CI
bootstrap appaiato. Tre strade laterali: rho della correzione, target
d'inversione (1X2+O/U vs solo 1X2), blend coi nostri lambda,mu.

**Risultato** (7 run, source `fase26_market_implied`):

| mercato | mkt-impl | DC-gol | baseline | Δ vs DC |
|---|--:|--:|--:|--:|
| risultato esatto | 2.8037 | 2.8345 | 2.8974 | -0.0309 |
| multigol | 1.0333 | 1.0470 | 1.0444 | -0.0137 |
| total ospite Ov1.5 | 0.5985 | 0.6111 | 0.6529 | -0.0126 |
| Over 3.5 | 0.5762 | 0.5877 | 0.5864 | -0.0114 |
| GG/NG | 0.6853 | 0.6901 | 0.6871 | -0.0047 |
| pari/dispari | 0.6932 | 0.6930 | 0.6923 | +0.0001 |

- il market-implied batte il DC-da-gol su 13 mercati su 14 (CI95<0 su 12) e la
  baseline su 13 su 14; guadagni maggiori sui mercati ricchi (risultato esatto
  -0.031, multigol, total-squadra);
- l'unica eccezione e' il pari/dispari (+0.0001): la parita' del totale e'
  quasi-casuale, nessun lambda,mu la predice (atteso: non inventa segnale);
- rho: conta poco, un piccolo negativo (-0.06/-0.10) aiuta i punteggi bassi;
- target: 1X2+O/U batte solo-1X2 (l'O/U fissa il livello di gol, servono
  entrambi);
- blend coi nostri lambda,mu: PEGGIORA (il nostro modello non aggiunge nulla al
  mercato — conferma dell'encompassing, Fase 16). Meglio il mercato puro.

**Lezione.** E' il risultato piu' forte del progetto: un MOTORE di pricing
coerente per ogni mercato sui gol, che date le sole quote 1X2+O/U prezza
risultati esatti/multigol/total-squadra/over-under/handicap meglio del nostro
modello e della baseline, in modo statisticamente solido. Conferma la tesi
centrale: la leva e' l'INFORMAZIONE (quella del mercato, trasferita a mercati non
prezzati), non l'architettura. Onesta': non verificabile vs ipotetiche linee di
chiusura di quei mercati (assenti nei dati), richiede le quote 1X2+O/U alla
predizione. Config del motore: inversione 1X2+O/U, rho -0.06, lambda,mu puri del
mercato (niente blend). E' la base pronta per il tool pratico.

---

## Fase 27 — Ottimizzare la forma dei punteggi sul market-implied (gia' ottima)

**Obiettivo.** Spremere il market-implied: i lambda,mu vengono dal mercato
(ottimi), ma la FORMA della distribuzione attorno a loro e' nostra, e in Fase 26
rho=-0.06 era fissato a occhio. Impararla dai risultati reali puo' migliorare i
mercati derivati (soprattutto risultato esatto e code)?

**Ragionamento.** La forma e' un parametro GLOBALE (non per-squadra), quindi
fittabile a bassa varianza sui risultati passati e applicabile in avanti (niente
look-ahead). Varianti: rho fittato; rho + inflazione diagonale phi (Fase 12b);
binomiale negativa (over-dispersione dei gol). Non serve il DC: il motore usa
solo quote + matrice, si lavora dallo snapshot.

**Risultato** (`scripts/_run_shape.py`; 1 run summary, source `fase27_shape`):

| forma | risultato esatto | Δ vs Fase 26 |
|---|--:|--:|
| rho=-0.06 (Fase 26) | 2.8037 | — |
| rho fittato (~-0.074) | 2.8038 | +0.0002 (rumore) |
| rho + phi (~0.09) | 2.8025 | -0.0011 [-0.0025, +0.0003] |
| binom. negativa | 2.8045 | +0.0009 (peggio) |

- rho fittato ~ rho fisso: il -0.06 a occhio era gia' giusto, fittarlo non aiuta;
- inflazione diagonale phi: guadagno minuscolo e NON conclusivo (CI include lo
  zero) solo sul risultato esatto -> non adottata;
- binomiale negativa RIGETTATA: il fit spinge la dispersione verso la Poisson
  (nb_size ~200) e peggiora -> i gol, con lambda dal mercato, sono Poisson, non
  over-dispersi.

**Lezione.** La forma della Fase 26 era gia' essenzialmente ottima: i lambda,mu
del mercato sono tutta la storia, la Poisson+rho attorno a loro e' il meglio.
Il market-implied ha toccato il suo tetto anche sulla dimensione della forma:
per spingere oltre servirebbero PIU' input di mercato (altre linee O/U, handicap
asiatici) per vincolare meglio i lambda,mu — che lo snapshot non ha. Il motore
e' maturo cosi' com'e'.

---

## Fase 28 — Quando falliscono i modelli? Errore per momento della stagione

**Obiettivo.** Ipotesi: a fine campionato alcune squadre non lottano piu' per
nulla (gia' salve o retrocesse), quindi le ultime giornate sono piu' "ballerine".
Ma la domanda decisiva: e' un fallimento NOSTRO o falliscono TUTTI (mercato
incluso)?

**Ragionamento.** Se a fine stagione peggiorano sia modello SIA mercato e il GAP
resta piatto -> casualita' irriducibile, non un nostro difetto (nemmeno dati
sulla motivazione aiuterebbero, neanche il mercato la prezza). Se il GAP si
allarga -> il mercato prezza la posta in palio e noi no: difetto nostro, dati
nuovi utili. Log-loss modello e mercato per giornata (stimata ordinando le
partite per data, gruppi di 10).

**Risultato** (`scripts/_run_matchday.py`; 7 run, source `fase28_matchday`):

| giornate | modello | mercato | gap |
|---|--:|--:|--:|
| 1-6 | 0.9725 | 0.9580 | +0.0145 |
| 7-19 | 0.9744 | 0.9569 | +0.0175 |
| 20-31 | 0.9631 | 0.9507 | +0.0124 |
| 32-34 | 1.0328 | 1.0125 | +0.0203 |
| 35-38 | 1.0179 | 0.9921 | +0.0258 |

- il finale (32-38) e' molto piu' difficile per ENTRAMBI (log-loss ~0.96 ->
  ~1.02 sia modello sia mercato): le ultime giornate sono davvero piu' ballerine,
  ma per chiunque -> casualita' irriducibile;
- il gap RADDOPPIA verso la fine (+0.0124 a meta' -> +0.0258 nel finale): indizio
  che il mercato prezzi la posta in palio meglio di noi;
- MA il test e' non conclusivo: Δ gap late(35-38)-vs-resto +0.0104, CI95
  [-0.0196, +0.0395], include lo zero (240 partite finali ad alta varianza, poca
  potenza). Tendenza pulita nei bucket, non un fatto dimostrato.

**Lezione.** L'ipotesi "finale ballerino" e' confermata ma in gran parte
UNIVERSALE (fatica anche il mercato -> non risolvibile). C'e' un indizio non
provato di un gap model-specifico nelle ultime giornate: e' li' che dei dati
sulla POSTA IN PALIO potrebbero aiutare. Nota chiave: un primo taglio di "posta
in palio" NON richiede dati esterni -- e' derivabile dalla classifica a ogni
giornata (squadra gia' matematicamente salva / retrocessa / in corsa). E' la
Fase 29 naturale, a costo zero di dati nuovi.

---

## Fase 29 — Posta in palio: i "dead rubber" spiegano il finale? (NO)

**Obiettivo.** La Fase 28 ha visto un indizio (non concluso) che il modello ci
perda un po' piu' del mercato nel finale. Se la causa e' la MOTIVAZIONE (squadre
gia' salve e fuori dall'Europa senza piu' nulla in gioco), il gap dovrebbe essere
maggiore proprio nei "dead rubber". Testabile SENZA dati esterni, dalla classifica.

**Ragionamento.** Per ogni squadra, con la classifica PRIMA della partita:
reach=3*gare_rimaste; fighting_relegation se (punti - linea_salvezza) <= reach;
chasing_europe se punti >= linea_europa - reach; dead_rubber se nessuno dei due
(limbo mid-table). Partita dead = entrambe (o almeno una) in dead_rubber. Test
diagnostico: gap modello-mercato dead vs live, CI bootstrap.

**Risultato** (`scripts/_run_stakes.py`; 7 run, source `fase29_stakes`):

| definizione | n | gap dead | gap live | Δ (dead-live) |
|---|--:|--:|--:|--:|
| entrambe dead | 12 (0.5%) | -0.069 | +0.017 | -0.086 [-0.14,-0.03] * |
| almeno una dead | 99 (4.3%) | +0.005 | +0.017 | -0.012 [-0.058,+0.035] |

- sul campione affidabile (99; le 12 "entrambe" troppo poche) NESSUN effetto (CI
  include lo zero);
- direzione comunque NEGATIVA: nei dead rubber il modello e' semmai leggermente
  MIGLIORE del mercato — l'opposto di "il mercato prezza la motivazione e noi no";
- corr(dead, gap) ~ 0.

**Lezione.** I dead rubber NON spiegano la difficolta' del finale: sono troppo
rari (0.5-4.3%) e dove la posta e' bassa il modello non fa peggio. Il finale e'
difficile per casualita' diffusa (Fase 28), non per una posta in palio che ci
sfugge. Consegue che cercare dati esterni sulla motivazione probabilmente NON
aiuterebbe: risultato utile, evita un investimento sbagliato. La caccia al
"perche' il finale e' piu' difficile" si sposta da "motivazione" a "varianza
strutturale delle ultime giornate" (Fase 30: pattern dentro la stagione).

---

## Fase 30 — Pattern dentro la stagione: anatomia per periodo

**Obiettivo.** Cercare pattern DENTRO la stagione: per ogni periodo, non solo il
gap ma cosa cambia (pareggi, gol, vantaggio-casa, entropia degli esiti), per
capire perche' certi momenti sono piu' difficili e se il pattern e' coerente tra
le 6 stagioni.

**Risultato** (`scripts/_run_season_patterns.py`; 7 run, source
`fase30_season_patterns`):

| giornate | gap | %casa | %pari | %osp | gol/g | entropia |
|---|--:|--:|--:|--:|--:|--:|
| 1-6 | +0.0145 | 39.7% | 28.9% | 31.4% | 2.84 | 1.089 |
| 7-19 | +0.0175 | 40.5% | 26.4% | 33.1% | 2.64 | 1.084 |
| 20-31 | +0.0124 | 41.9% | 26.0% | 32.1% | 2.60 | 1.079 |
| 32-34 | +0.0203 | 41.1% | 31.1% | 27.8% | 2.56 | 1.085 |
| 35-38 | +0.0258 | 36.2% | 25.4% | 38.3% | 2.90 | 1.084 |

Tre scoperte:
1. NON e' entropia: l'entropia degli esiti e' piatta -> il finale piu' difficile
   non e' dovuto a esiti piu' bilanciati (spiegazione meccanica esclusa);
2. due cambi strutturali reali: giornate 32-34 tese e bloccate (pareggi 31%,
   pochi gol, log-loss alto per tutti = scontri decisivi col freno a mano);
   giornate 35-38 dove il VANTAGGIO-CASA CROLLA (casa 40%->36%, trasferta
   31%->38%, piu' gol) = effetto fine stagione;
3. nessun pattern robusto nel gap: correlazioni con la giornata ~0 (gap +0.0056),
   gap fine-inizio positivo solo in 3 stagioni su 6 (media +0.0015, range
   -0.017..+0.021) -> l'indizio della Fase 28 NON e' coerente tra stagioni.

**Lezione.** Il finale piu' difficile e' reale ma non ha un pattern-gap robusto:
riguarda tutti (mercato incluso), non e' entropia ne' motivazione (Fase 29). Il
candidato concreto che emerge e' il CROLLO DEL VANTAGGIO-CASA nel finale (il
modello eredita un home-advantage dallo storico che nelle ultime giornate si
riduce, come nel COVID Fase 9) -- molto piu' promettente della motivazione, ma
marginale finche' il gap non sale in modo robusto. E' un candidato per una
covariata "giornata avanzata -> attenua il vantaggio-casa", da valutare con
prudenza (rischio overfitting su un effetto piccolo).

---

## Fase 31 — Posta in palio corretta (8 stagioni): conta l'ASIMMETRIA

**Obiettivo.** La Fase 29 (dead rubber = "salva E fuori dall'Europa") era
sbagliata ai due estremi: contava una squadra gia' RETROCESSA come "in lotta
salvezza" e una gia' CAMPIONE come "in corsa titolo". Definizione corretta
(DECISA = nessuna corsa aperta, inclusi retrocessa e campione), su 8 stagioni,
con molte combinazioni a livello partita.

**Risultato** (`scripts/_run_stakes2.py`; 9 run, source `fase31_stakes2`; n=3040):

Stati-squadra (su 6080): in_corsa 5795, salva_limbo 147, europa_decisa 70,
retrocessa 45, campione 23 (solo 4.7% "deciso").

| categoria | n | gap | CI95 |
|---|--:|--:|--:|
| entrambe in corsa | 2831 | +0.0172 | [+0.0122, +0.0221] |
| una decisa, una in corsa | 133 | +0.0572 | [+0.0139, +0.1014] * |
| entrambe decise | 76 | +0.0130 | [-0.035, +0.060] |
| coinvolge una campione | 23 | +0.0949 | [+0.013, +0.179] * |

- RIBALTA la Fase 29: escludendo le partite con >=1 squadra decisa il gap SCENDE
  da +0.0188 a +0.0172 (quelle partite hanno gap +0.0411) -> su di esse il
  modello va PEGGIO del mercato, non meglio (la Fase 29, col classificatore rotto
  e 12 partite, concludeva l'opposto);
- il segnale e' l'ASIMMETRIA: "una decisa, una in corsa" ha gap triplo (+0.057 vs
  +0.017, CI esclude lo zero); "entrambe decise" invece niente.

**Lezione.** Quando una squadra non ha piu' nulla in gioco e l'altra lotta, la
squadra motivata sovra-rende / quella scarica molla: il mercato lo prezza, noi
no (usiamo la forza stagionale, ciechi alla motivazione del momento). E' il primo
LEAD azionabile dai dati interni. Onesta': campioni piccoli (133 la categoria piu'
solida, 23-76 le altre) e molti test -> indizio forte e sensato, non una prova; e
l'effetto e' SOLO nell'asimmetria, non quando entrambe sono decise (coerente col
meccanismo). Candidato: una covariata "stakes mismatch" (una squadra decisa vs
una in corsa) che attenui la previsione a favore della squadra motivata, da
validare walk-forward prima di adottare. Indica anche quali dati esterni
cercherebbero valore (indicatori di motivazione/asimmetria), ma il primo taglio
e' gia' nei dati (dalla classifica). METODO: la Fase 29 mostra quanto conta una
definizione corretta -- un classificatore sbagliato ai bordi ribaltava la
conclusione.

---

## Fase 32 — Validazione della covariata stakes-mismatch (DC e GBM)

**Obiettivo.** Il lead della Fase 31 (una squadra decisa vs una in corsa -> il
modello perde piu' del mercato) regge WALK-FORWARD, come covariata? Testato su
ENTRAMBI i modelli (richiesta esplicita: non solo il DC).

**Ragionamento.** Covariata `stakes` (1=decisa/0=in corsa, dalla classifica;
`loader.add_stakes`, registrata in `_COVARIATES`, off di default). Nel DC entra
nel fit come le altre covariate (`--covariates stakes`); nel GBM come feature
aggiuntive (home_settled, away_settled, differenza). Il segnale e' su ~5% di
partite (mismatch), quindi l'effetto OVERALL sara' minuscolo per costruzione: il
test vero e' sulla riga MISMATCH.

**Risultato** (`scripts/_run_stakes_cov.py`; 15 run, source `fase32_stakes_cov`):

| modello | subset | log-loss base->stakes | Δ (CI95) |
|---|---|--:|--:|
| DC | overall | 0.9797->0.9796 | -0.0001 [-0.0007,+0.0005] |
| DC | mismatch (n=99) | 0.9609->0.9587 | -0.0022 [-0.0157,+0.0114] |
| GBM | overall | 1.0098->1.0096 | -0.0001 [-0.0014,+0.0012] |
| GBM | mismatch (n=99) | 0.9968->0.9841 | -0.0127 [-0.0283,+0.0030] |

- direzione CONFERMATA su entrambi: sulle partite mismatch la covariata aiuta sia
  il DC (-0.0022) sia il GBM (-0.0127), entrambe negative;
- il GBM la cattura MOLTO meglio del DC (-0.0127 vs -0.0022): l'effetto "la
  squadra scarica sotto-rende" e' non-lineare, il GBM modella l'interazione
  mentre il DC puo' solo spostare linearmente il tasso-gol;
- MA nessuno e' conclusivo (CI includono lo zero, il GBM per un pelo: +0.0030).

**Lezione.** Non adottata (regola: CI<0), ma e' il LEAD interno piu' credibile
del progetto: direzione giusta su DUE architetture indipendenti, meccanismo
chiaro, effetto concentrato dove previsto -- diverso dai "residui = rumore" delle
Fasi 13/20, dove i segni erano casuali. Il rumore puro non darebbe due negativi
concordi. Serve solo piu' campione (piu' stagioni o il futuro out-of-sample) per
superare la soglia. Nota per il futuro: se si usera' questo segnale, il GBM e' il
veicolo giusto (lo cattura ~6x meglio del DC). Infrastruttura pronta: covariata
`stakes` disponibile, off di default.

---

## Fase 33 — Ultime covariate mai provate: PPDA/deep e finishing-luck (ridondanti)

**Obiettivo.** Chiudere onestamente il capitolo "spremere i dati interni": nello
snapshot restavano DUE segnali mai messi nel modello -- PPDA/deep (tattica) e
finishing-luck (gol-xG rolling, mean-reversion). Sono gli ultimi segnali interni
inesplorati.

**Ragionamento.** Feature ROLLING pre-partita (no look-ahead), aggiunte al loader
(`add_style_luck`) e registrate come covariate `ppda`/`deep`/`luck` (off di
default). Testate su DC (nel fit) e GBM (feature), disciplina solita (overall 1X2
log-loss + gap, CI). Aspettativa onesta: probabilmente ridondanti (l'xG cattura
gia' la qualita' delle occasioni), ma vanno provate per chiudere il libro.

**Risultato** (`scripts/_run_style_luck.py`; 27 run, source `fase33_style_luck`):

DC: base 0.9797; +ppda+deep 0.9806 (Δ +0.0009 [-0.0012,+0.0030]); +luck 0.9797
(Δ -0.0000 [-0.0006,+0.0006]); +tutte 0.9807. GBM: 1.0107 -> 1.0085 (Δ -0.0022
[-0.0072,+0.0028], P 81%).

- PPDA/deep RIDONDANTI: peggiorano appena il DC (lo stile e' gia' implicito in
  gol+xG, come il valore-rosa Fase 4c);
- finishing-luck effetto ESATTAMENTE ZERO sul DC: conferma elegante che il blend
  gol/xG (alpha=0.75) e' gia' il meccanismo di mean-reversion -- pesa gol e xG in
  modo ottimale, quindi "la fortuna regredisce" non aggiunge nulla;
- il GBM estrae un capello dalle feature tattiche (-0.0022, 81%) che il DC lineare
  non vede, ma non conclusivo e irrilevante (resta ben peggio del DC).

**Lezione.** Con la Fase 33 i DATI INTERNI SONO COMPLETAMENTE ESPLORATI: tutto lo
snapshot (gol, xG, npxG, PPDA, deep, valore-rosa, assenze, riposo, forma, stakes)
e' stato testato. Il tetto e' informativo, confermato per l'ultima volta coi
segnali rimasti. Il finishing-luck a zero e' la nota piu' istruttiva: un'ipotesi
sensata (mean-reversion) che il modello incorporava gia'. L'unico lead vivo resta
lo stakes-mismatch (Fase 32), che serve piu' stagioni. Ogni altro guadagno ora
richiede INFORMAZIONE NUOVA (formazioni, quote live) o un avversario meno
efficiente (leghe/mercati diversi): finisce la strada "spremere lo snapshot".

---

## Prossimo passo — il modello e' al tetto REALE dei dati attuali

Sette esperimenti convergenti (Fasi 6-13) + l'audit di Fase 15 + il test della
linea di apertura (Fase 14) + l'**encompassing** (Fase 16: α*=0, il mercato
ingloba il modello) + il **rho dinamico** (Fase 18: anche l'ultima via
strutturale sul pareggio e' rumore) + l'**anatomia dei residui** (Fase 20: R² a
livello rumore su 11 covariate, e i disaccordi del modello sono i suoi errori):
il gap residuo col mercato (+0.0165 vs chiusura, +0.0146 vs apertura, quasi
tutto nel pareggio) non e' cattiva modellazione ne' errore di calcolo, ma
**informazione che il mercato ha e noi no** — ce l'ha gia' il venerdi' (CLV
negativo) e il modello non aggiunge nulla nemmeno in blend. Il bivio:
1. **Dati davvero nuovi** (formazioni ufficiali pre-partita; oppure la linea di
   apertura VERA di domenica/lunedi', che richiede raccolta prospettica di quote);
2. **Uso pratico** del modello attuale (comando di predizione);
3. **Mercati strutturalmente meno efficienti** (leghe minori, exchange lenti):
   stessa infrastruttura, avversario diverso.

Nota di realismo invariata: battere le quote di chiusura resta difficilissimo;
il value betting simulato perde il **15.7%** — piu' di quanto credevamo prima
dell'audit. **Non scommettere soldi veri con questo modello.**

---

*Questo diario viene aggiornato ad ogni fase. Per i dettagli tecnici e i comandi
vedi il [README](../README.md); per i risultati grezzi e replicabili
`experiments/runs.jsonl`.*
