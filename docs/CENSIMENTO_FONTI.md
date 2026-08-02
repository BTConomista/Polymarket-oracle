# Censimento delle fonti — cosa abbiamo e non usiamo (01/08/2026)

> **Cos'è questo file.** Il verbale di un censimento a 13 agenti (6 famiglie di
> fonti × 1 censore + 1 confutatore, più una sintesi) eseguito su richiesta
> dell'utente: *«guarda tutte le fonti che abbiamo usato fino ad ora. da qualche
> fonte ci sono dati che non usiamo?»*
>
> Copre **~1.100 campi** su tutte le fonti del repo. Dopo il filtro restano
> **12 occasioni** — molte meno di quante i censimenti lasciassero credere,
> perché la maggior parte del «non usato» è **già stato provato e bocciato**.

⚠️ **Onestà sul metodo.** La sintesi finale ha ri-verificato personalmente solo
quattro voci; il resto è ereditato dai censori e dai loro confutatori. Ogni
numero qui va ri-eseguito prima di poggiarci una decisione. Le quattro
ri-verificate, più le due che ho controllato io scrivendo questo file, sono
marcate ✅.

---

## 1 · La distinzione che regge tutto

Un dato non usato lo è per **due ragioni opposte**:

- **mai provato** → è un'occasione;
- **provato e bocciato** → riproporlo fa rifare al progetto un lavoro già fatto.

Il repo ha chiuso molto e lo dichiara (`CLAUDE.md` §6: «tutti i dati INTERNI
sono esplorati… ridondanti o rumore, Fasi 4c-33»). **Ogni voce di questo
censimento dichiara in quale dei due casi cade**, e cita la fase che la chiude.

---

## 2 · I numeri d'insieme

| fonte | campi | in produzione | mai letti |
|---|--:|--:|--:|
| football-data grezzo | 180 nomi distinti | 39 | **95** |
| Understat (bundle) | 64 foglie JSON | 19 | 36 — *ma 10 ridondanti per identità misurata* |
| diretta.it (giocatore + squadra) | 124 nomi distinti | **0** | 124 |
| player_scores | 121 colonne | 14 | tutte al servizio di `squad_value`, bocciato 4 volte |

---

## 3 · Le 12 occasioni, in ordine di valore/costo

| # | cosa | costo | perché non è già chiusa |
|--:|---|:--:|---|
| 1 | ✅ **Quote GG/NG di chiusura 2020-25** (8.981 righe mai aperte) | basso | la Fase 100 chiuse il GG/NG *sul 2017-20*, che era il perimetro dei file di allora |
| 2 | ✅ **Gol all'intervallo** già in produzione, letti da nessuno | nullo | l'input della pista 6-bis è arrivato solo alla Fase 133 |
| 3 | **Best price di chiusura** `MaxC*`, 1X2 **e** O/U | basso | la pista 8 è parziale: 1 stagione su 9, e il numero pubblicato non è ri-calcolabile |
| 4 | **Larghezza della distribuzione fra book** (33 colonne + il conta-book `Bb*`) | nullo | nessuna fase nomina la dispersione fra book |
| 5 | ✅ **Falli** `HF/AF` — il regressore mancante dei cartellini | basso | le Fasi 4c-33 riguardano i **gol**; i falli non compaiono in nessuna |
| 6 | **Scomposizione 1T/2T delle 45 metriche** di squadra | basso | pista 6-bis aperta; nessun'altra fonte separa i periodi |
| 7 | **Handicap asiatico**: 2 leghe fuori dal benchmark + linea di apertura | basso | il benchmark della Fase 88 copre 3 leghe e solo la chiusura |
| 8 | **Metà difensiva di diretta.it** (duelli, tackle, intercetti) | basso | ortogonalità misurata \|r\| 0,03-0,11 contro ciò che il modello già vede |
| 9 | **Betfair Exchange** `BFE*` — prezzo di borsa, 3.393 partite | basso | pista 9: rimandato, mai misurato |
| 10 | **Orario del calcio d'inizio** (14.358 partite) | nullo | zero occorrenze in codice, zero voci in PISTE |
| 11 | **Plus-minus difensivo su xGOT** già calcolato dalla fonte | basso | il plus-minus misurato (r=+0,0354) era **sui gol** |
| 12 | **Titolare/Subentrato per-partita** | medio | la Fase 98 bocciò un *surrogato* dei minuti, non chi era in campo dal 1' |

---

## 4 · Le scoperte che valgono più delle occasioni

Il censimento ha trovato **affermazioni false o non verificabili nei nostri
stessi documenti**. Sono il risultato più utile, perché non richiedono un
esperimento per essere sfruttate.

1. ✅ **`CLAUDE.md` §1.8 dichiarava il falso sul GG/NG.** Diceva che «il book
   non lo quota nelle stagioni recenti». Misurato: **14.358 righe** con la
   quota di chiusura, su **tutti e nove gli anni 2017→2025**.
   **Rettificato il 01/08/2026** nel file stesso.
2. **Il best price è citato ma non esiste in codice.** La Fase 86 pubblica
   «ROI 1X2 2025-26 al best-price −2,4%», ma la stringa `MaxCH` non compare in
   nessun `.py`, `.md` o `.yml`: solo dentro i file di dati. Viola la regola
   della Fase 15 (ogni numero dev'essere ri-calcolabile), e `DIARIO` e `PISTE`
   divergono sullo stato della pista 8.
3. ⭐ **La frazione di primo tempo NON è la stessa per tutte le metriche.**
   Gialli **0,3200** · xG 0,4447 · corner 0,4689 · falli 0,4735 · passaggi
   **0,5177**. Il progetto usa `f = 0,4396` — misurato sui gol — per ri-scalare
   i mercati Tier 3: sui **cartellini sbaglia del 38%**.
4. **`forecast{w,d,l}` di Understat è look-ahead.** Batte la chiusura devigata
   di 0,087-0,107 nat su 3.420 partite per lega — impossibile per una
   previsione pre-partita, quindi è calcolata *dopo*. Da non usare mai (R8).
5. **Il terzo livello della cascata di quote non vince mai.** La preferenza
   dichiarata è `AvgC → B365C → PSC`; eseguita su 16.111 partite dà AvgC
   12.459, PSC 3.650, **B365C zero**. E Pinnacle copre **più** partite (94,7%)
   con overround più stretto (1,0267) della media multi-book che lo precede.
6. **Quattro colonne del per-giocatore di diretta.it non sono individuali**:
   `Gol concessi`, `xGot affrontati`, `Gol evitati` sono valori di **squadra**
   calcolati sul tempo in campo. Nessun documento del repo lo diceva.
7. **Esisteva una misura di liquidità per-partita, inutilizzata.**
   `Bb1X2`/`BbOU`/`BbAH` contano quanti book Betbrain ha mediato (media 36,8 su
   3.652 partite) — mentre la Fase 53 concludeva che «θ decresce con la
   liquidità» usando come proxy il margine mediano, con **5 punti dati**.
8. **`appearances.red_cards` perde il 52,1% delle espulsioni** (1.495 contro
   3.122 vere). Caso R6 da manuale, già documentato nell'audit fonti.
9. **Il grezzo di Bundesliga e Ligue 1 non è versionato**: `data/fonti/` è in
   `.gitignore`. È la ragione strutturale per cui il benchmark handicap si
   ferma a 3 leghe.

---

## 5 · Cosa è stato scartato, e perché

Il filtro ha tolto più di quanto abbia tenuto:

- **tutta la raccolta in avanti 2026-27** (Smarkets, giornaliero, anagrafiche,
  rose): non è «non usata», è **non ancora scorabile** — la stagione inizia il
  15/08/2026;
- **`data/estimates/`**: sono stime dichiarate, non dati (§5 del `CLAUDE.md`);
- **calendario di club** (59.866 righe): alimenta covariate bocciate su 5 leghe
  su 5 (PANCHINA #9 e #12);
- **valore-rosa e parentela**: chiuso da 4 fasi più l'audit;
- **arbitro sui gol**: chiuso dalla Fase 98 — ⚠️ da non confondere con la Fase
  125, che lo misura **positivo sui cartellini**: la tabella di stato di PISTE
  riporta solo la bocciatura;
- **10 colonne Understat** ridondanti *per identità misurata* (0 differenze su
  13.680 righe): `xGA`, `npxGA`, `ppda_allowed`, `deep_allowed`, `npxGD`…

---

## 6 · Deperibile: scade il 15/08/2026

⚠️ **Smarkets espone 115 mercati per partita; ne raccogliamo 3** nel giro
giornaliero e 6 in quello di chiusura. Fra i 109 mai raccolti ci sono
esattamente i mercati che `CLAUDE.md` §6 dichiara **scoperti** (HT/FT, le
combinazioni). È il caso da manuale della regola **§5-ter** (raccogliere tutto):
un prezzo non raccolto prima del fischio non si recupera più.

⚠️ **Difetto operativo in corso**: fra il 30 e il 31/07 Smarkets ha rinominato
gli eventi (`Deportivo Alaves` → `Alaves`, `Atletico Madrid` → `Atlético
Madrid`) e il join anagrafiche-listino sarebbe passato da **96/96 a 32/96**.
Segnalato da un censimento e confermato dal suo confutatore con misura
indipendente — **non ri-verificato da me**: va controllato prima di agire.
