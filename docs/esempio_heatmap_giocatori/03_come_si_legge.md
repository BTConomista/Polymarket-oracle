# Come si legge una mappa — cosa è rilevante e cosa no

Il rischio di questi dati non è calcolarli male: è **leggerci dentro più di
quello che c'è**. 463 punti su 16 partite sono bellissimi da guardare e dicono
molto meno di quanto sembri.

---

## Cosa è rilevante

### 1 · La FORMA, non l'intensità

Due mappe normalizzate ognuna sul proprio massimo sono confrontabili sulla forma
e **non** sul colore. La zona più calda di Malen e quella di Erling sono entrambe
«il suo massimo»: non sono la stessa quantità. L'intensità va detta con un numero
separato (posizioni per 90′).

### 2 · Le differenze che sopravvivono a più misure

Il risultato dell'esempio non è «Malen è più offensivo». È questo:

| | Malen | Erling |
|---|--:|--:|
| X media | 70,6 | 64,9 |
| terzo difensivo | 4,0% | 8,4% |
| escursione verticale (sd) | 18,8 | 22,7 |

Tre misure **indipendenti** che raccontano la stessa storia — Haaland arretra per
ricevere — e per questo è credibile. Una sola sarebbe stata un aneddoto.

Regola: se una differenza compare in una misura e non nelle altre due che
dovrebbero muoversi con lei, **non è un fatto, è rumore**.

### 3 · Le uguaglianze, che nessuno guarda

Il risultato più interessante dell'esempio è un **pareggio**: dentro l'area
27,9% contro 27,2%. Presenza in area identica, forma opposta.

Questo è ciò che i dati spaziali aggiungono sopra gli aggregati: i per-90
dicevano già «Malen tocca più palloni, Erling vince più duelli aerei», ma non
potevano dire che occupano lo *stesso* spazio finale per strade diverse. Se la
conclusione di un'analisi spaziale si poteva ottenere dagli aggregati, la mappa
non ha aggiunto niente.

### 4 · La coerenza fra mappe diverse dello stesso giocatore

I tiri confermano le posizioni: Erling calcia dal corridoio centrale nel 94,6%
dei casi contro il 78,6% di Malen, e il ventaglio di Malen si apre a destra —
esattamente dove la sua heatmap è più calda. Due dati distinti che concordano
valgono più di uno solo, e la loro **discordanza** sarebbe un segnale d'allarme
sulla pipeline.

---

## Cosa NON è rilevante

### 1 · I picchi sui punti fissi — sono artefatti

In **entrambe** le mappe c'è un massimo locale esatto sul centro del campo. Sono
i **calci d'inizio**: un attaccante li batte, e la fonte registra la posizione.

Va saputo per due motivi. È una **controprova** che si sta guardando una
registrazione e non un modello — nessun lisciamento inventerebbe un picco isolato
lì. Ed è una **contaminazione**: gonfia di poco la corsia centrale e la propria
metà, quindi una differenza di mezzo punto su quelle due voci non significa
niente. Chi ha giocato più partite ha più calci d'inizio.

Lo stesso vale per gli altri punti fissi: dischetto (rigori), bandierine
(angoli), centro area (punizioni battute).

### 2 · Il singolo punto, e la coda della densità

Un punto è un campione di posizione, non un evento con un significato. Le zone
tiepide ai bordi della mappa sono spesso **un pomeriggio solo** — una partita in
cui il giocatore ha fatto un ripiegamento insolito. Con 463 punti su 16 partite,
una zona all'1% sono 4-5 punti: non è una tendenza.

### 3 · La differenza fra due leghe letta come differenza fra due giocatori

Malen gioca in Serie A, Erling in Premier. Parte di ogni differenza è **il
campionato, la squadra e gli avversari**, non il giocatore. Il Manchester City
tiene più palla del Roma; questo da solo sposta le mappe.

Questo confronto **non separa** i due effetti, e non pretende di farlo. Per
separarli servirebbe un riferimento per lega (la mappa media del ruolo in quel
campionato) e non è stato costruito.

### 4 · Il conteggio dei punti come misura di volume

Vedi trappola 5 del capitolo 01: 605 punti non sono 605 tocchi. Il rapporto
posizioni/tocchi è ~1,23 in Serie A e non è garantito che sia lo stesso altrove.

---

## Cosa NON si può dire con questi dati

- **«Malen è più forte / più utile».** Una mappa dice dove uno è stato, non
  quanto è servito. Per il valore servono gol, xG, e un modello.
- **«Erling è in calo perché arretra».** La direzione causale non è nei dati: può
  arretrare perché la squadra glielo chiede, perché lo marcano più alto, o perché
  sta peggio. La mappa registra la posizione, non il motivo.
- **«Questa è la mappa di Haaland».** È la mappa di **16 partite** di Haaland in
  **un** campionato in **mezza** stagione. Sull'intera stagione i punti sono 1.005
  su 35 partite, e la forma **cambia davvero** — misurato, non supposto:

  | | 1ª metà (542 pt) | 2ª metà (463 pt) | Δ |
  |---|--:|--:|--:|
  | terzo offensivo | 47,6% | 53,8% | **+6,2** |
  | terzo difensivo | 14,9% | 8,4% | **−6,5** |
  | corsia centrale | 60,0% | 65,2% | +5,3 |
  | dentro l'area | 30,1% | 27,2% | −2,9 |

  E cambia nella direzione **opposta** all'intuizione: nella seconda metà Haaland
  è stato più avanzato, non più arretrato — pur segnando 8 gol contro 19. Chi
  avesse letto la mappa della seconda metà come «si è abbassato, ecco perché
  segna meno» avrebbe costruito una spiegazione su un fatto che il dato nega.
  Una metà di stagione non è una proprietà del giocatore.
- **Qualsiasi cosa di predittivo.** Questa è un'analisi descrittiva. Che una
  differenza sia *misurata* non la rende *prevedibile* — è la lezione della Fase
  99 del progetto, dove un bias di livello misurato su un pool **peggiorava** le
  cose quando applicato in avanti. Per dire che una forma di gioco predice
  qualcosa serve un walk-forward con il suo intervallo di confidenza.

---

## La domanda da farsi alla fine

> **Cosa avrei visto se i due giocatori fossero stati identici?**

Con 605 e 463 punti, una differenza di uno o due punti percentuali su una zona è
compatibile col caso. Le differenze dell'esempio che superano largamente questa
soglia — corsia destra 36,9% contro 13,4%, corridoio dei tiri 78,6% contro
94,6% — sono le sole su cui vale la pena costruire una frase. Il pareggio in area
(27,9 / 27,2) è *dentro* la soglia, e per questo va detto come «uguale», non come
«Malen leggermente superiore».
