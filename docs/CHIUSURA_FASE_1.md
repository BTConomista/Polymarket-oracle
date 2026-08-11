# Chiusura della Fase 1 — piano operativo

> **Cos'è questo documento.** Il programma per dichiarare **davvero conclusa la
> Fase 1** del progetto: non «abbiamo finito di avere idee», ma *ogni modello e
> ogni leva della matrice di `docs/PANCHINA.md` ha una decisione scritta, su
> tutti i fronti dove la decisione è possibile*.
>
> **Da dove nasce.** Da una richiesta esplicita dell'utente (10/08/2026):
> *«vorrei riuscire a finire del tutto la fase 1 del progetto, dato che molti
> modelli sono stati lasciati incompiuti (magari provati solo con la serie a
> oppure provati su altri campionati con costanti relative alla serie a)»*, e
> da una bozza di piano fornita dall'utente stesso. Questo file è quella bozza
> **verificata contro il repo e corretta in sei punti**: il registro delle
> modifiche è in §9, così si vede cosa è cambiato e perché.
>
> **Regola d'uso.** Questo è un **piano**, non una fonte di verità. Le fonti
> canoniche restano `docs/PANCHINA.md` (stato dei modelli), `docs/PISTE.md`
> (piste), `docs/DIARIO.md` (narrazione) e il registro del `README.md`. Quando
> una casella si chiude si aggiorna **PANCHINA**, e solo dopo questa checklist.
>
> **Stato**: APERTO. Nessuna tranche eseguita.

---

## 0 · Il problema, in tre numeri

### (a) Una lega su cinque è finita. Le altre quattro sono a metà

Conteggio delle celle `⬜` («mai testato lì») **per colonna** della matrice —
51 righe di modello × 6 fronti = 306 celle:

| fronte | celle `⬜` | decise |
|---|---|---|
| Serie A | **2** su 51 | 96% |
| Premier League | **23** su 51 | 55% |
| La Liga | **24** su 51 | 53% |
| Bundesliga | **26** su 51 | 49% |
| Ligue 1 | **25** su 51 | 51% |
| generale (pooled) | **16** su 51 | 69% |
| **totale** | **116** su 306 | **62%** |

Ri-calcolabile con:

```bash
awk '/^\| modello \| Serie A/,/^$/' docs/PANCHINA.md | awk -F'|' '
NR<=2{next} NF>=8{for(i=3;i<=8;i++){tot[i]++; if($i ~ /⬜/) v[i]++}}
END{for(i=3;i<=8;i++) printf "col %d: %d/%d\n", i-2, v[i], tot[i]}'
```

Il totale **116** coincide con la ricetta ufficiale dichiarata in testa a
`PANCHINA.md`. **Questo è il problema, ed è quantificato**: il modello che
manderemo in campo su cinque campionati è stato scelto con cura su uno solo.
Sugli altri quattro, per metà delle righe, la configurazione di produzione non
è *scelta*: è **rimasta**.

⚠️ Non tutte e 116 sono lavoro mancante — e distinguere è il primo compito
(§2). Ma la sproporzione fra colonne non è un artefatto di classificazione: la
Serie A ha 2 caselle vuote, la Bundesliga 26.

### (b) L'unica cosa con una scadenza scade fra pochi giorni

`newseason.md` §5 fissa il **16 agosto** (parte La Liga) come termine non
negoziabile per congelare le previsioni del test prospettico 2026-27
(`experiments/prospettico_2026_27.md`, **Fase 78 — l'unica fase formalmente
APERTA** secondo `lavoro_aperto.md` §1). Tutto il resto di questo piano non ha
orologio; quello sì, e ciò che non si congela prima del fischio **non si
recupera** (`CLAUDE.md` §5-ter).

### (c) Una stagione non basta per tutto, e si sa già quanto basta

Una stagione 2026-27 su cinque leghe vale **1.752 partite** (380 × 3 +
306 × 2, contate sull'ultima stagione di ogni snapshot). Contro i requisiti di
potenza misurati alla Fase 98 per il confronto **modello contro mercato**:

| confronto | n per l'80% di potenza | una stagione ×5 leghe basta? |
|---|---|---|
| 1X2 | 574 | ✅ sì, pooled (1.752) — ❌ no per singola lega (380 / 306) |
| GG/NG | 2.254 | ❌ no (servono ~1,3 stagioni) |
| O/U 2.5 | 2.988 | ❌ no (servono ~1,7 stagioni) |

È il vincolo che decide la forma di tutto il piano: **le domande pooled
sull'1X2 si chiudono in una stagione, quelle per-lega e per-mercato no.**

---

## 1 · Perimetro congelato

Prima di lanciare qualsiasi backtest, si fissa cosa è dentro. Un'idea nuova che
emerge durante la chiusura si registra nella roadmap della Fase 2 — **non
riapre la Fase 1**.

### Dentro (dati)

Risultati e gol · gol all'intervallo · xG/npxG · tiri e tiri in porta · quote
di apertura e chiusura (1X2, O/U, e il GG/NG dove esiste) · valore rosa
aggregato · proxy aggregati delle assenze · forma e streak · riposo e
congestione · posta in palio · PPDA e deep completions · statistiche di squadra
per periodo (Totale/1T/2T) · corner e cartellini aggregati · classifiche e
regole di spareggio per gli outright.

### Dentro (modelli)

Dixon-Coles e sue covariate · market-implied e sue ricalibrazioni · Poisson
bivariato · copule · modelli di dispersione (dp/NB/ZIP/COM) · GBM · ensemble ·
modelli dinamici (GAS, ρ dinamico, profilo stagionale) · simulatore di stagione
e mercati outright · conteggi corner/cartellini · Tier 3 da ri-scalamento 1T/2T
· **modello a due stadi del secondo tempo** (vedi il riquadro qui sotto).

### ⚠️ Correzione al perimetro della bozza: il modello a due stadi è Fase 1

La bozza collocava il modello *game-state* del secondo tempo nella Fase 2,
motivando che *«richiede la nuova granularità temporale»*. **È falso, ed è
verificabile in un comando.** I gol all'intervallo sono negli snapshot:

| lega | partite | con `home_goals_ht`/`away_goals_ht` |
|---|---|---|
| Serie A | 3.420 | 3.420 |
| Premier League | 3.420 | 3.420 |
| La Liga | 3.420 | 3.420 |
| Bundesliga | 2.754 | **2.753** (un solo buco, dichiarato) |
| Ligue 1 | 3.097 | 3.097 |

**16.110 su 16.111.** In più, `src/data/team_stats.py` (Fase 131) ha le
statistiche di squadra già divise in periodi. E `lavoro_aperto.md` §8 mette il
modello a due stadi al **numero 2** delle priorità, con la nota *«sui dati che
già abbiamo»*: è l'unico residuo **localizzato e non-artefatto** che il
progetto abbia trovato in decine di fasi (il 2T è mal calibrato — pareggio
0.3671 previsto contro 0.3427 reale — mentre il 1T passa per lo stesso codice
ed è calibrato a <0.006).

Esiliarlo alla Fase 2 avrebbe tolto dalla chiusura **il pezzo con più valore
atteso di tutta la lista**. Entra in Tranche 1.

### Fuori (è Fase 2)

Valore del singolo giocatore · formazioni ufficiali e probabili · carriere
individuali come feature · allenatore come individuo · **acquisizione** di
nuove fonti arbitrali · meteo · notizie e infortuni nominativi · modello
in-play alimentato dalla raccolta live · qualunque architettura inventata dopo
il congelamento di questo perimetro.

---

## 2 · Che cosa significa «chiusa»

La Fase 1 è chiusa quando **nessuna cella della matrice è `⬜`**. Ma `⬜` si
svuota in **sei** modi, non in uno, e cinque di questi non richiedono un
backtest:

| stato | significato | serve un esperimento? |
|---|---|---|
| ⚽ **titolare** | adottato in config o nei tool | sì |
| 🪑 **panchina** | migliorativo ma non conclusivo | sì |
| ❌ **bocciato** | peggiorativo o nullo in modo robusto | sì |
| ➖ **non applicabile** | la domanda non ha senso lì, con motivazione esplicita | no |
| 🗄️ **archiviato** | decisione consapevole di non spendere, con costo-opportunità dichiarato | no |
| ⛔ **non decidibile** | **i dati della Fase 1 non hanno la potenza per produrre un verdetto** | no — ma il calcolo di potenza va fatto e scritto |

Lo stato ⛔ è la novità di questo piano ed è quello che permette di svuotare la
matrice **onestamente** invece che per esaurimento. Vedi §3.

### L'invariante di chiusura

```
chiusa(Fase 1)  ⟺  ∀ c ∈ matrice :  stato(c) ∈ {⚽, 🪑, ❌, ➖, 🗄️, ⛔}
                    e ogni ➖ / 🗄️ / ⛔ porta la sua motivazione scritta
```

Il criterio è verificabile da un test automatico (§7). **Non** è «zero celle
vuote» inteso come «tutto testato»: è «zero celle **senza decisione**».

### Esempi di celle già `➖` travestite da `⬜`

- **Stimatore `squad_value` in Bundesliga e Ligue 1** — la cella dice già *«mai
  servito: `squad_value` REALE al 100%»*. Non c'è niente da stimare: è ➖.
- **θ di calibrazione in Premier** — la cella dice già *«lì il router usa già
  θ=1 e il difetto è assente»*. La domanda non si pone: è ➖.
- **Temperatura sopra `dp_lvl`** dove `dp_lvl` è bocciato con CI conclusivo —
  una correzione post-hoc sopra un modello dominato: ➖, non un esperimento.

Il primo lavoro della Tranche 0 è trovarle tutte. Una parte delle 116 si chiude
leggendo la cella, non eseguendola.

---

## 3 · La regola di potenza — il cancello d'ammissione

**Motivo.** La regola **R7** del progetto impone che ogni «non c'è effetto»
porti la sua misura di potenza. Finora la si è applicata *dopo*. Qui diventa un
**cancello d'ingresso**: una cella si esegue solo se il suo confronto è
decidibile con i dati disponibili. Altrimenti è ⛔, e si dichiara.

**Perché non è pedanteria.** Molte celle rimaste sono confronti fra varianti
quasi identiche, con effetti al terzo o quarto decimale. Eseguirle senza
potenza produce «nel rumore» — che non è una decisione, è una spesa di calcolo
che lascia la casella dov'era.

### Esempio lavorato, dalla matrice vera

`Ensemble emivite 180+730`, cella **Bundesliga**:

```
effetto misurato   Δ = −0.000496          (log-loss, guadagno)
IC95%              [−0.00137, +0.00037]   semi-ampiezza h ≈ 0.00087
n disponibile      2.754 partite (9 stagioni, tutto lo snapshot)
```

Perché l'IC escluda lo zero serve `h < |Δ|`, cioè restringerlo di un fattore
`k = 0.00087 / 0.000496 ≈ 1.75`. Poiché `h ∝ 1/√n`, servono `k² ≈ 3.1` volte i
dati: **≈ 8.500 partite**. In Bundesliga non esistono e non esisteranno per
decenni.

**Conseguenza operativa**, e non è una brutta notizia: quella cella è ⛔ **sul
fronte per-lega** e **decidibile sul fronte pooled** (5 leghe = 16.111 partite,
5,8× la Bundesliga). Il calcolo di potenza non chiude solo delle porte: dice
**quale fronte** può rispondere. È l'argomento più forte a favore del fronte
generale, e nasce da un conto, non da una preferenza.

⚠️ **I numeri della Fase 98 (574 / 2.254 / 2.988) non sono trasferibili a
queste celle.** Sono tarati sul confronto *modello contro mercato*, che ha un
effetto e una varianza appaiata suoi. Per un confronto *leva contro base* le
due previsioni sono molto correlate: effetto più piccolo **e** varianza
appaiata più piccola. Quindi `n₈₀` va **ricalcolato per ogni cella** dalla sua
deviazione standard appaiata osservata — come nell'esempio sopra. I numeri
della Fase 98 restano l'illustrazione del fatto che il vincolo morde, non una
costante universale.

---

## 4 · ⭐ Il conflitto col test prospettico, e come si scioglie

**La domanda dell'utente (10/08/2026):** *«così noi prevediamo i risultati
della stagione utilizzando i dati e i modelli che usavamo nella fase 1 (e molti
modelli della fase 1 non sono neanche stati sperimentati, soprattutto quelli
dei campionati esteri come premier e liga)»*.

È il punto più importante di tutto il documento, ed è ben posto. Congelare le
previsioni il 16 agosto significa congelare **la configurazione di oggi**: per
Premier e Liga, il motore liscio — che in parte è misurato (φ35 ❌ F80 in
Premier, `dp_lvl` ❌ F53) e in parte è soltanto **il default prudente su celle
mai aperte** (23 e 24 rispettivamente).

Il caso che rende il problema concreto: **il router θ in La Liga è 🪑 con
`lfo` CI<0 su tre bersagli** (cs −0.0069, 1X2 −0.0023, GG −0.0025 — la Fase 81
ha ribaltato la Fase 53). Cioè abbiamo **evidenza positiva a favore di una leva
che la produzione non usa**. Se congeliamo solo la configurazione ufficiale, la
stagione passa e quella casella resta 🪑 per un altro anno.

### La soluzione: non congelare *un* modello, congelare una *rosa dichiarata*

Il test prospettico chiede che le previsioni siano **pre-registrate** prima del
fischio. Non chiede che ce ne sia **una sola**. Quindi:

> **Si congelano, prima del 16 agosto, la configurazione ufficiale *e* ogni
> variante candidata che la Tranche 1 dovrebbe decidere. Tutte scorate a fine
> stagione sugli stessi identici incontri.**

Questo rovescia il problema. La stagione 2026-27 smette di essere «un test di
un modello incompleto» e diventa **l'arbitro fuori campione proprio per le
celle indecise** — e un verdetto pre-registrato fuori campione vale
**qualitativamente più** di un backtest, perché non c'è modo di averlo tarato
dopo.

### La rosa da congelare (tutte leve di configurazione, non codice nuovo)

| # | variante | stato oggi | cella che deciderebbe |
|---|---|---|---|
| 0 | **configurazione ufficiale** (`LEAGUE_CONFIGS` + `MARKET_ENGINE`) | ⚽ | è il riferimento |
| 1 | La Liga: router θ **acceso** | 🪑 F81 (lfo CI<0 su 3 bersagli) | router × Liga |
| 2 | La Liga: φ35 **accesa** | 🪑 F80 (CI<0 sul GG) | φ35 × Liga |
| 3 | La Liga: θ + φ35 insieme | mai misurata l'interazione | attribuzione doppia |
| 4 | Serie A: `dp_tilt` al posto di `dp_lvl` | 🪑 (eguaglia con un parametro in meno, 7/7 e 6/6) | dp_tilt × SA |
| 5 | `dp_tilt` come **costante unica pooled** | ⬜ mai testato | dp_tilt × generale |
| 6 | DC con **ensemble emivite 180+730** | ⬜ Premier, ⬜ Liga, 🪑 Bund, 🪑 Ligue 1 | 3 celle + pooled |
| 7 | **devig di Shin** al posto del moltiplicativo | 🪑 su tutte e cinque | 5 celle + pooled |
| 8 | **estremizzazione della chiusura O/U** (α) su SA/Premier/Liga | ⬜⬜⬜ | 3 celle |

Nove previsioni per partita invece di una. Il costo è un `dict` di
configurazione e una colonna in più nello scoring — **non** nove esperimenti.

### Il costo asimmetrico, che è la ragione vera

Congelare una variante costa una riga di config. **Non** congelarla costa **una
stagione intera**, perché il prezzo di chiusura di una partita giocata non
torna. È la stessa asimmetria del principio §1.10 del `CLAUDE.md`: *riaprire
una pista chiusa costa un esperimento; non riaprirla costa non sapere mai*.

### ⚠️ Che cosa questa soluzione NON risolve — da dire prima, non dopo

1. **Non rende la config di oggi quella giusta.** Le previsioni ufficiali
   2026-27 restano quelle della configurazione attuale, incompleta. La rosa non
   corregge il presente: **compra il verdetto per il futuro**.
2. **Una stagione decide poco.** Con 1.752 partite (§0c) è powered il confronto
   **1X2 pooled**; per-lega (380 / 306) e per-mercato (GG/NG, O/U 2.5) **no**.
   Le varianti per-lega della rosa vanno lette come *accumulo*, non come
   verdetto al 30 giugno.
3. **Nove varianti sono nove confronti.** La pre-registrazione esistente
   (`experiments/prospettico_2026_27.md` §5.1, criterio 5) impone di dichiarare
   il numero di ipotesi e di tenere **un solo** primario. Resta valido:
   il primario è e rimane **M1 vs baseline, log-loss 1X2, pooled**; la rosa è
   una **famiglia secondaria pre-registrata** con correzione di Holm al suo
   interno. Scegliere il vincitore a posteriori senza correzione sarebbe
   esattamente il giardino dei sentieri che si biforcano.
4. **Non si tocca la configurazione ufficiale adesso.** Accendere il router θ
   in Liga oggi, su evidenza da panchina, è precisamente ciò che lo stato 🪑
   esiste per impedire. La promozione avviene con la regola pre-registrata,
   dopo.

### Decisione da prendere (non tecnica)

Va aggiunta come **D3** nella sezione «Decisioni aperte» di
`experiments/prospettico_2026_27.md`, con **default dichiarato**: se nessuno
decide entro il **15/08**, si congela la rosa completa (nove varianti) — perché
il costo è trascurabile e l'omissione è irreversibile. Stessa forma del
timebox già usato per D2.

---

## 5 · Protocollo unico

La chiusura fallisce se ogni cella usa un protocollo suo: i verdetti non
sarebbero confrontabili e la matrice diventerebbe un collage.

**Dati.** I cinque snapshot congelati · stesso intervallo storico applicabile ·
apertura e chiusura sempre separate e dichiarate · **nessuna stima nelle
colonne presentate come dato reale** (`data/estimates/` resta separato, §5 del
`CLAUDE.md`) · stessa politica sui mancanti · disponibilità temporale
verificata (R8): solo colonne `pre` della partita in corso, o `post` di partite
precedenti.

**Validazione.** Walk-forward per stagione · nessun look-ahead · iperparametri
selezionati **solo sul passato** (leave-future-out) · stesso insieme di partite
nei confronti appaiati · ri-allenamento con cadenza identica fra le varianti.

**Benchmark.** Pre-match: baseline ex ante, il DC ufficiale della lega,
il mercato di apertura, il mercato di chiusura dove esiste. Market-implied: le
probabilità devigate del book, il motore liscio, la configurazione ufficiale.
Outright: uniforme, campione uscente, valore rosa, persistenza storica, e il
mercato reale dove esiste.

**Metriche.** Sempre via `experiment_log.compute_metrics` (fonte unica):
log-loss, Brier, calibrazione (ECE), risoluzione, bias per classe, per mercato,
delta appaiato, IC bootstrap, stabilità per stagione.

**Confronti multipli.** Da pre-registrare **prima** di ogni tranche: famiglia di
ipotesi, metrica primaria, mercato primario, correzione (Holm o
Benjamini-Hochberg), soglia di promozione, soglia di archiviazione.

> ⚠️ **Aspettativa dichiarata in anticipo**: sotto questo protocollo la grande
> maggioranza delle celle si chiuderà come ❌ o «nel rumore». **È l'esito
> previsto, non un fallimento del piano** — il tetto del progetto è
> *informativo*, non architetturale. Scriverlo qui serve a impedire che la
> prima sessione che esegue la Tranche 3 sia tentata di allentare la soglia.

### ⚠️ Il placebo obbligatorio del fronte pooled

Ogni verdetto «pooled vince / per-lega vince / gerarchico vince» deve portare
il **controllo a leghe rimescolate**:

```
1. si calcola la statistica S sul raggruppamento VERO (per lega)
2. la si ricalcola su B raggruppamenti CASUALI delle stesse partite,
   di uguale numerosità
3. il verdetto vale SOLO se S_vero cade fuori dalla distribuzione dei S_placebo
```

**Non è una precauzione teorica: il progetto ha già sbagliato qui.** La cella
pooled del router θ porta scritto: *«audit §10: per-lega vs pooled non deciso
(il conteggio 73-8 esce identico da leghe rimescolate a caso: misurava solo che
il pooled ha 4× dati di selezione)»*. Un confronto che sopravvive alle leghe
mescolate non sta misurando la lega.

### Le tre forme del fronte generale

| forma | che cosa condivide |
|---|---|
| **H1 · pooled puro** | un solo insieme di parametri per le 5 leghe |
| **H2 · formula universale, parametri per-lega** | è il disegno attuale del DC: formule comuni, δ per lega |
| **H3 · gerarchico** | media globale + deviazione per lega, shrinkage verso il pooled (basta leave-one-league-out o una regolarizzazione semplice: non serve un bayesiano completo) |

Ogni famiglia dichiara quale delle tre vince — o che nessuna batte la baseline.

---

## 6 · Il programma, per tranche

### Tranche −1 · Ciò che ha una scadenza (entro il 16 agosto)

1. Congelare le previsioni 2026-27 secondo `experiments/prospettico_2026_27.md`
   §5.1, con i controlli fissi già in checklist lì.
2. **Congelare la rosa di varianti di §4** (o registrare la decisione D3).
3. Verificare che il raccoglitore prenda il prezzo di chiusura vero (il
   guardiano riporta `anticipo_chiusura_min`).

**Perché prima di tutto:** è l'unica parte del piano che, se salta, salta per
un anno. La Tranche 0 può cominciare il 17 agosto senza perdere nulla.

### Tranche 0 · Inventario e bonifica — nessun modello girato

1. **Congelare il perimetro** (§1) e dichiararlo chiuso.
2. **Generare** la matrice leggibile da macchina (§7) — generarla, non
   trascriverla.
3. **Classificare le 116 celle** in: (a) test necessario · (b) già misurato,
   manca la trascrizione · (c) ➖ non applicabile · (d) 🗄️ archiviabile per
   costo-opportunità · (e) duplicato matematico di un'altra riga · (f)
   dipendente da una base già bocciata · (g) **⛔ non decidibile per potenza**.
4. **Trascrivere i risultati che l'audit ha già misurato** (`lavoro_aperto.md`
   §3 ne segnala 18): è trascrizione, non ricerca.
5. **Audit di contaminazione Serie A.** Per ogni esperimento storico non-Serie
   A registrare quale `league_config` e quale `market_engine` usava, e se
   ρ, θ, φ0, κ, shrinkage, emivita e δ erano fittati sulla lega, selezionati
   leave-future-out, pooled, **copiati dalla Serie A**, o lasciati al default
   neutro. La domanda non è «è stato testato in Premier?» ma *«è stato testato
   in Premier con un protocollo che non ha visto il futuro e con costanti
   Premier o selezionate correttamente?»*.
6. **Uccidere il fallback silenzioso.** Oggi `league_config()` restituisce
   `SERIE_A` per una chiave ignota, mentre `market_engine()` restituisce il
   motore liscio: **due default in direzioni opposte**, che è la forma con cui i
   bug sopravvivono. Nei tool ufficiali una lega ignota deve **sollevare
   errore**; il fallback può restare solo in API dichiaratamente diagnostiche.
   Test parametrico sulle 5 leghe, test che una sesta chiave inventata
   fallisca, test che `backtest.py`, `predict.py`, simulatore e scoring
   propaghino la stessa lega — **ognuno verificato per mutazione** (standard
   Fase 92-bis: si rompe il codice di proposito, se la suite resta verde il
   test non esiste).

**Risultato atteso: le 116 scendono parecchio senza un solo backtest.**

### Tranche 1 · Ciò che può cambiare la produzione

1. ⭐ **Modello a due stadi del secondo tempo** (1T indipendente → 2T
   condizionato al punteggio dell'intervallo). Il residuo localizzato e
   non-artefatto, sui dati che già abbiamo.
2. **Ensemble emivite**: Premier, Liga, e il **pooled pre-registrato**, che la
   matrice indica come il test decisivo.
3. **Router θ in La Liga** e **φ35 in La Liga**, separate e poi congiunte (il
   rischio è attribuire due volte lo stesso miglioramento a correzioni
   sostitutive).
4. **`dp_tilt` pooled** come costante unica.
5. **Devig di Shin**: bakeoff unico moltiplicativo / Shin / power, 5 leghe,
   apertura e chiusura separate, 1X2 e derivati separati.
6. **Estremizzazione della chiusura O/U** su una terza lega (oggi solo
   Bundesliga e Ligue 1).
7. **θ di calibrazione** dove è applicabile (Premier è probabilmente ➖).

### Tranche 2 · Mercati operativi ma incompleti

Posizionali (top-4 / retrocessione) su Bundesliga e Ligue 1 · deriva di forza
in-stagione sulle due nuove, **per mercato e non in blocco** (`DRIFT_SD` è
adottata solo sulla retrocessione: sul top-4 peggiora, 17 stagioni su 24) ·
conteggi corner/cartellini sulle due nuove · binomiale negativa dei conteggi ·
Tier 3 (1T/2T, risultato esatto) sulle due nuove · **baseline ufficiale del
mercato campione, scelta prima del test** (a n=24 il risultato è fragile alla
specificazione, e l'outright **non è testabile prospetticamente**: servirebbero
57 stagioni-lega).

### Tranche 3 · Leve economiche del path Dixon-Coles

φ35 standalone su Bundesliga e Ligue 1 · nudge GG/NG di fine stagione su
quattro leghe + pooled (con controllo dell'era porte-chiuse) · temperature
scaling · ricalibrazione per classe · diagonale inflazionata costante ·
covariate aggregate mancanti.

**Efficienza:** non un backtest per covariata. Tre bundle pre-registrati —
*forza* (squad value, assenze, npxG), *recenti* (forma, luck, PPDA, deep),
*contesto* (riposo, congestione, stakes, vantaggio casa) — e l'ablazione
**solo** se un bundle produce qualcosa.

### Tranche 4 · Architetture alternative — **default: archiviazione**

Poisson bivariato, copula di Frank, GAS, NB/ZIP/Rue-Salvesen, ρ dinamico, GBM,
ensemble standalone, profilo stagionale dinamico: tutte ❌ in Serie A, `⬜`
altrove.

> **Inversione rispetto alla bozza.** Qui il default è **🗄️ archiviato con
> motivazione**, e serve un **argomento positivo scritto** per eseguirne una —
> non il contrario. Motivo: il tetto del progetto è informativo, il
> costo-opportunità è alto e molte di queste celle sono comunque ⛔ per potenza
> (§3). Dove si esegue, si esegue con **un solo harness**
> `modello × lega × stagione × mercato`, mai con decine di driver ad hoc.

### Tranche 5 · Chiusura formale

Nessuna cella applicabile ancora `⬜` · config di produzione aggiornata **solo**
per le promozioni · `runs.jsonl` completo · `PANCHINA.md` allineata ·
`DIARIO.md` con la fase di chiusura e il suo blocco 📐 · README aggiornato ·
questo documento compilato con gli esiti · **tag git `phase-1-complete`** ·
apertura formale della roadmap Fase 2.

---

## 7 · Deliverable e criterio oggettivo

**L'artefatto:** `experiments/fase1_closure_matrix.csv`, con colonne
`famiglia, modello, lega, fronte, stato, applicabile, fase_storica,
costanti_usate, protocollo, artefatto, n_disponibile, n80_richiesto,
decidibile, stato_finale, motivo`.

> ⚠️ **Va GENERATO da `docs/PANCHINA.md`, non mantenuto a mano.** Due file che
> devono coincidere divergono, ed è già successo: il 28/07/2026
> `lavoro_aperto.md` ha smesso di duplicare i conteggi con la motivazione *«un
> indice che incide numeri che vivono altrove diventa stantio nel giro di una
> sessione — ed era già successo due volte»*. PANCHINA resta l'unico posto dove
> si scrive a mano; il CSV è un prodotto del parser, e il test controlla il
> parse **e** l'invariante.

**Il criterio di completamento**, come test automatico:

```
celle_applicabili_senza_stato_finale == 0
```

dove «applicabile» esclude ➖ e ⛔, e ogni ➖ / 🗄️ / ⛔ ha una motivazione non
vuota.

---

## 8 · Cosa questo piano NON promette

- **Non promette un edge.** Chiudere la matrice non sposta il tetto
  informativo. La configurazione ufficiale dà **ROI −15.8% su 866 scommesse**:
  resta valida l'avvertenza del `CLAUDE.md` — *non usare per scommettere soldi
  veri*.
- **Non promette che la chiusura cambi la produzione.** L'esito più probabile è
  che cambi poco o nulla, e che il valore stia nel **sapere** che non cambia.
- **Non chiude la Fase 78.** Il test prospettico si accumula per stagioni; la
  Fase 1 può essere dichiarata chiusa con la Fase 78 ancora aperta, purché lo
  si scriva.
- **Non sospende il metodo.** Intervallo di confidenza (R7), più stagioni
  (§1.7), disponibilità temporale (R8), onestà sui limiti (§1.6) valgono
  identici dentro la chiusura.

---

## 9 · Modifiche rispetto alla bozza dell'utente

La bozza è stata verificata contro il repo. **Le sue affermazioni sulla matrice
sono risultate corrette**: il conteggio di 116 celle coincide con la ricetta
ufficiale di `PANCHINA.md`, e le descrizioni delle righe citate (`dp_tilt`,
ensemble emivite, devig di Shin, estremizzazione O/U, θ-calibrazione,
posizionali, deriva, conteggi, Tier 3, arbitro, proxy formazioni) corrispondono
al contenuto reale. Modificate sei cose:

| # | modifica | motivo |
|---|---|---|
| 1 | **Aggiunta la Tranche −1** (test prospettico prima di tutto) | la bozza non nominava la Fase 78, che è l'unica formalmente aperta e l'unica con una scadenza (16/08). La Tranche 0 avrebbe mangiato esattamente quei giorni |
| 2 | **Il modello a due stadi passa da Fase 2 a Tranche 1** | la bozza lo escludeva dicendo che serve granularità nuova; i gol all'intervallo ci sono su 16.110/16.111 partite e `lavoro_aperto.md` §8 lo mette al #2 |
| 3 | **Aggiunto lo stato ⛔ «non decidibile» e il cancello di potenza** | «zero celle vuote» è un criterio di copertura; una parte delle celle non produce verdetto nemmeno se eseguita (esempio lavorato in §3) |
| 4 | **Aggiunto il placebo a leghe rimescolate nel fronte pooled** | l'errore è già stato commesso e scoperto: il conteggio 73-8 del router θ usciva identico da leghe casuali |
| 5 | **Il CSV va generato, non mantenuto** | evita la seconda fonte di verità accanto a PANCHINA — cicatrice del 28/07 |
| 6 | **Tranche 4 invertita: archiviazione di default** | replicare architetture già bocciate in Serie A ha costo-opportunità alto e spesso è ⛔ per potenza |

⚠️ **Un rilievo sulla bozza, minore ma da registrare.** I riferimenti in forma
`【F:docs/PANCHINA.md†L62】` puntano a righe **spostate di circa 17** rispetto al
file reale (`dp_tilt` è alla riga 79, non 62; il devig di Shin alla 88, non
71). Il contenuto attribuito è giusto — sono le àncore a essere sbagliate. In
questo documento i riferimenti sono **per nome di riga della matrice**, perché
i numeri di riga si spostano al primo inserimento.

---

## 📐 Il modello in dettaglio

Questo documento non introduce matematica nuova: fissa **tre criteri**, e sono
questi a dover essere espliciti.

### (a) L'invariante di chiusura

```
M = matrice di PANCHINA.md,  |M| = 51 righe × 6 fronti = 306 celle
S = {⚽, 🪑, ❌, ➖, 🗄️, ⛔}

chiusa(Fase 1) ⟺ ∀ c ∈ M : stato(c) ∈ S
                 ∧ ∀ c con stato(c) ∈ {➖, 🗄️, ⛔} : motivo(c) ≠ ∅
```

Stato al 10/08/2026: `|{c : stato(c) = ⬜}| = 116`, cioè **62,1% deciso**
(190/306). La distribuzione per fronte è in §0a.

### (b) Il criterio di decidibilità

Per una cella il cui confronto ha effetto appaiato `Δ` e semi-ampiezza dell'IC95%
`h` su `n` partite, poiché `h ∝ 1/√n`:

```
n₈₀(cella) ≈ n · (h / |Δ|)²          (fattore di allargamento per portare l'IC
                                      a escludere lo zero, a effetto invariato)

decidibile(cella, fronte) ⟺ n_disponibile(fronte) ≥ n₈₀(cella)
```

Applicato all'esempio di §3 (ensemble emivite × Bundesliga): `Δ = −0.000496`,
`h = 0.00087`, `n = 2.754` →
`n₈₀ ≈ 2.754 · (0.00087/0.000496)² ≈ 2.754 · 3.08 ≈ 8.480` partite.
Non disponibili in Bundesliga (2.754) → **⛔ per-lega**; disponibili sul fronte
pooled (16.111) → **decidibile lì**.

⚠️ `Δ` e `h` vanno presi **dalla cella stessa**, non trasferiti da un'altra: i
numeri della Fase 98 (n₈₀ = 574 / 2.254 / 2.988 per 1X2 / GG-NG / O-U 2.5) sono
tarati sul confronto *modello contro mercato*, che ha effetto e varianza
appaiata diversi da un confronto *leva contro base*. Sono citati come
illustrazione del vincolo, non come costante.

### (c) Il placebo del fronte pooled

Dato un verdetto `V` che confronta la forma per-lega con quella pooled tramite
una statistica `S` (per esempio: quanti mercati preferiscono il pooled):

```
S_vero      = S(raggruppamento per lega)
S_placebo^b = S(raggruppamento CASUALE, stesse numerosità),  b = 1…B

V vale  ⟺  S_vero ∉ [percentile 2.5, percentile 97.5] di {S_placebo^b}
```

Senza questo passaggio la statistica può misurare soltanto quanti dati di
selezione ha il pooled — che è esattamente ciò che è successo al conteggio
73-8 del router θ (audit a 5 leghe, §10).

---

**Ultimo aggiornamento**: 10/08/2026 · **Stato**: APERTO, nessuna tranche
eseguita · **Prossimo passo**: Tranche −1, entro il 16 agosto.
