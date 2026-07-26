# Report 2 — Le stime: ritentare l'import del dato vero, e verificare la stima

**Domanda posta:** *«riprova ad importare i dati che abbiamo raccolto come stime;
se ancora non riesci, verifica che i risultati delle stime (e il ragionamento che
ha portato ad esse) sia corretto»*.

**Verdetto in due righe:** il dato vero **non è ancora procurabile** (4 vie
battute oggi, tutte chiuse, con prove di prima mano). La stima e il ragionamento
che la sostiene **reggono**: riproducibile al decimale, errore dichiarato
confermato sotto protocolli più severi di quelli usati per dichiararlo, e —
verifica **nuova** — batte l'apertura reale nel predire gli esiti veri del
2017-19, nella stessa direzione e misura con cui li batte la chiusura vera dove
esiste. Tre precisazioni da riportare nei documenti (§4).

---

## 1 · Il bersaglio

`data/estimates/ou_close_2017_19.csv` (2.279 righe, 3 leghe): la **chiusura
Over/Under 2.5** delle stagioni 2017-18 e 2018-19, che le fonti non pubblicano.
Stimata con l'estimatore E3 pooled (Fasi 62/62-bis).

## 2 · Ritentativo di import del dato VERO — esito NEGATIVO (con prove)

La rete è cambiata (vedi Report 1 §1): host prima bloccati oggi rispondono. Le
vie percorribili sono state ritentate **tutte**, di prima mano.

| via | esito oggi | prova |
|---|---|---|
| **football-data.co.uk** (la fonte-madre) | ❌ **la chiusura O/U non esiste** prima del 2019-20 | Scaricati i CSV 2017-18/2018-19 di **5 leghe**: le uniche colonne O/U sono `BbMx>2.5, BbAv>2.5, BbMx<2.5, BbAv<2.5`. **Nessuna** colonna `*C*`. Dal 2019-20 compaiono `B365C>2.5, PC>2.5, MaxC>2.5, AvgC>2.5`. Il `notes.txt` conferma: quote «collected Friday afternoons / Tuesday afternoons» (= pre-match) e fonti «Betbrain.com, Oddsportal.com». |
| **BetExplorer** | ❌ funzione ritirata per le partite vecchie | Pagina-partita Serie A 2017-18 (`ac-milan-fiorentina`): `#bettingTabs` contiene **solo un tab «1X2» disabilitato**, zero occorrenze di `match-odds`, nessuna tabella quote. Identico all'esito della Fase B (probe da runner Actions): ora ri-verificato **da questa sessione**, con IP e percorso di rete diversi → non era un blocco geografico. |
| **OddsPortal** | ❌ **vietato dal robots.txt** | `robots.txt` contiene `Disallow: *-2017*`, `Disallow: *-2018*` … cioè **esattamente** le URL delle stagioni storiche che servirebbero. Il progetto si è dato la regola di rispettare robots.txt: la via è chiusa per regola, prima ancora che per il login. È un motivo più netto di quello registrato finora («serve il login»). |
| **dataset di terzi** | ❌ nulla di nuovo | Ricerca web (luglio 2026): i dataset «historical odds» sono ri-pubblicazioni di football-data (ereditano il buco). **Princeton DSS** «Historical Sports Odds Database» copre solo sport USA (MLB/NBA/NFL). **Footiqo**: quote di sola **chiusura 1xBet**, tier gratuito limitato alla stagione in corso. Restano API a pagamento (bettingiscool, TheStatsAPI, Apify): decisione dell'utente, non tecnica. |

**Conclusione:** le Fasi A e B di `docs/CACCIA_OU_2017_19.md` restano chiuse
negative; la Fase D (OddsPortal headless) va **declassata da «pista più
probabile» a «pista non percorribile»**, perché il robots.txt la esclude a
prescindere dalle credenziali. Il documento va aggiornato.

---

## 3 · Verifica della stima (otto prove, cercando di falsificarla)

Re-implementazione **indipendente** dalla formula documentata, senza chiamare
`scripts/build_estimates.py` (`cantiere/scripts/verifica_stime.py`).

### 3.1 Riproducibilità — ✅
2.279 righe ri-derivate, **2.279 combaciano**, scarto massimo **0.000000**.
Nessuna riga in più o in meno. Il file committato è esattamente ciò che il
metodo dichiarato produce.

### 3.2 I coefficienti hanno senso — ✅
```
logit(P_close) = 0.0209 + 0.9788·logit(P_open)
                 + 1.2453·Δlogit(pH) − 0.8113·Δlogit(pD) + 1.2457·Δlogit(pA)
```
- intercetta ≈ 0 e β ≈ **0.98** su `logit(P_open)`: «la chiusura somiglia
  moltissimo all'apertura», coerente con il rapporto quasi-identità già
  misurato alla Fase 69 (corr 0.96-0.99);
- **i coefficienti su casa e ospite sono identici a 4 decimali** (1.2453 vs
  1.2457) e quello sul pareggio è negativo: il segnale che il modello usa è
  «il mercato si è spostato verso un esito **deciso**» → più gol attesi. È
  simmetrico rispetto a *quale* squadra migliora, come dev'essere. Questa
  simmetria non è imposta: emerge dal fit, ed è una conferma forte che il
  meccanismo catturato è reale e non un artefatto.

### 3.3 L'errore dichiarato (MAE ~0.012) regge a protocolli più severi — ✅

| protocollo | MAE |
|---|---|
| in-sample | 0.0122 |
| **leave-one-season-out** | **0.0123** (min 0.0101, max 0.0152) |
| **leave-one-league-out** | **0.0124** (SA 0.0123, PL 0.0126, Liga 0.0123) |
| **walk-forward stretto** (fit solo sul passato) | **0.0117** |

Il valore dichiarato (0.012) non è ottimistico: regge anche togliendo un'intera
lega dal fit — cioè il **pooling** cross-lega è legittimo.

### 3.4 La stima vale davvero la pena? — ✅ (e si scopre *perché*)

| metodo (leave-one-season-out) | MAE |
|---|---|
| media di lega (costante) | 0.0769 |
| **identità** (chiusura = apertura) | 0.0210 |
| solo `logit(OU)`, senza il movimento 1X2 | 0.0209 |
| **E3 completo** | **0.0123** (−41.7% vs identità) |

Scoperta non registrata finora: **tutto il valore aggiunto viene dal movimento
1X2**, non dalla regressione sul livello. Da sola, la regressione sul livello
dell'apertura pareggia l'identità (0.0209 vs 0.0210). È coerente col meccanismo
del §3.2 e va scritto: se un domani il movimento 1X2 non fosse disponibile, la
stima varrebbe quanto copiare l'apertura.

### 3.5 Il limite dichiarato «input di provenienza diversa», ora MISURATO — ✅

I coefficienti sono fittati su input `Avg` (media multi-book) ma applicati a
input `BbAv` (Betbrain): un cambio di provider mai quantificato. Misurato
sostituendo l'input con un provider diverso (Bet365 pre-match) sulle stesse
partite:

| input | MAE |
|---|---|
| stesso provider del fit (`Avg`) | 0.0122 |
| **provider diverso** (`B365`) | **0.0132** (+8.1%) |

→ l'errore reale sul 2017-19 è plausibilmente **~0.012–0.013**, non un ordine di
grandezza diverso. Numero nuovo, da aggiungere ai limiti dichiarati.

### 3.6 Falsificazione sul bersaglio (la prova che mancava) — ✅ direzione giusta, ⚠️ non conclusiva

Se la stima aggiunge informazione vera, deve **predire meglio dell'apertura
reale** gli esiti Over/Under effettivamente accaduti nel 2017-19.

| finestra | log-loss |
|---|---|
| 2019-20+ apertura reale | 0.67522 |
| 2019-20+ **chiusura VERA** | 0.67348 → guadagno reale **+0.00173** |
| 2019-20+ stima E3 | 0.67412 → ne recupera **+0.00109 (63%)** |
| **2017-19 apertura reale** | 0.67667 |
| **2017-19 stima E3** | **0.67523** → guadagno **+0.00144** |

Bootstrap appaiato B=10.000 sul bersaglio: **+0.00144, CI95 [−0.00099, +0.00393]
→ NON conclusivo** (2.279 partite non bastano per un effetto di questa
grandezza: nemmeno la chiusura *vera* lo sarebbe).

Lettura onesta: la stima si comporta **esattamente come dovrebbe** — stesso
segno, stessa grandezza del guadagno che la chiusura vera ottiene dove esiste, e
senza mai «superare» il guadagno reale (una stima gonfiata lo farebbe). È la
conferma più forte ottenibile senza il dato vero, ma **non è una prova
statistica**: va scritta così.

### 3.7 Righe la cui stima poggia su un input rotto — ⚠️ **da ritirare**

Le **3 righe** con margine impossibile del Report 1 §4.1 sono input di 3 stime:

| partita | overround input | P(Over) input | P(Over) stimata |
|---|--:|--:|--:|
| Alaves-Real Madrid 06/10/2018 | 1.2825 | 0.5096 | 0.4852 |
| Eibar-Real Madrid 24/11/2018 | 1.2814 | 0.5382 | 0.5578 |
| Leganes-Betis 10/02/2019 | 1.1279 | 0.3575 | 0.3691 |

Per le prime due l'1X2 indica P(Over) ≈ 0.58-0.60: le stime (0.49 e 0.56) sono
**fuori bersaglio di 6-10 punti**, ben oltre il MAE dichiarato di 0.012. Sono
3 righe su 2.279 (0.13%): irrilevanti sull'aggregato, sbagliate una per una.

**Raccomandazione:** con il guard del Report 1 §4.1 l'input diventa NaN e le 3
stime spariscono da sole (`build_estimates.py` salta le righe senza input).

### 3.8 Le altre due stime — ✅ conformi al dichiarato
- `open_sparse_1x2_ou.csv`: **2 righe** (Verona-Genoa 2020-21, O/U; Torino-Fiorentina
  2022, 1X2+O/U), come dichiara `docs/DATI.md`. Verificato che ogni riga stima
  **solo** il mercato che le manca davvero nello snapshot.
- `squad_value_2017_26.csv`: **0 righe**, come dichiarato dopo la Fase 70.

---

## 4 · Le tre precisazioni da riportare nei documenti

1. **Correlazione col movimento vero: dichiarata «0.75-0.86», misurata
   0.719-0.877 per stagione** (media 0.803; per lega 0.759 / 0.792 / 0.845 —
   *dentro* il range dichiarato). Il range va corretto o qualificato come
   «per-lega»; per-stagione è più largo (2023-24 scende a 0.72).
2. **Quota di movimento non catturata:** dichiarata «~35-45%», misurata 23-48%
   per stagione (per lega: Serie A 42%, Premier 37%, **Liga 29%**). Il dichiarato
   è giusto per SA/PL, pessimista per la Liga.
3. **Nuovi numeri da aggiungere ai limiti:** +8.1% di MAE per cambio provider
   dell'input (§3.5); tutto il valore aggiunto viene dal movimento 1X2 (§3.4);
   3 stime da ritirare (§3.7).

## 5 · Aggiornamenti da fare a `docs/CACCIA_OU_2017_19.md`

- Fase A: **ri-confermata negativa**, ora per verifica **diretta sulla
  fonte-madre** (prima era un'inferenza da mirror Kaggle + ricerca web).
- Fase B: **ri-confermata negativa da questa sessione** → non era il blocco
  geo/ADM da IP italiano, è il sito che ha ritirato il dato.
- Fase D (OddsPortal): da «pista con la probabilità più alta di successo» a
  **pista esclusa dal robots.txt** del sito.
- Aggiungere: la rete dell'ambiente è cambiata (Report 1 §1), quindi le
  ricognizioni future costano meno; ma il buco è **strutturale a monte** e
  nessuna via gratuita e lecita lo colma oggi.
