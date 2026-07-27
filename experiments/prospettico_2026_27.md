# Test prospettico — giornata 1, stagione 2026-27 (5 leghe: Serie A, Premier, La Liga, Bundesliga, Ligue 1)

> **Stato: APERTO.** Anteprima illustrativa congelata il 2026-07-23. Il test
> vero (con quote reali e risultati) va **completato più avanti** — vedi §5.
>
> ⚠️ **Allargato a 5 leghe all'audit della Fase 101.** Il documento nasceva a 3
> leghe perché Bundesliga e Ligue 1 non erano ancora in produzione; ora lo sono
> (16.111 partite, `LEAGUE_CONFIGS` e `MARKET_ENGINE` complete), quindi non c'è
> ragione di lasciarle fuori dal gold standard. L'anteprima illustrativa del §2
> resta a 3 leghe — è congelata e non si riscrive — ma il **protocollo del §3
> vale per tutte e cinque**.
>
> **Le date di inizio** (fonte unica: `newseason.md` §1, `start_date` degli
> eventi outright Smarkets scaricati il 25/07/2026, da riverificare a inizio
> agosto): **La Liga 16 agosto**, **Premier e Ligue 1 21 agosto**, **Serie A 22
> agosto**, **Bundesliga 28 agosto**. La scadenza vera del congelamento è quindi
> il **16 agosto**.

## 1 · Perché questo test

È il **gold standard** della validazione: si congelano le previsioni **prima**
del calcio d'inizio e si controllano **dopo**. Nessun senno di poi è possibile —
a differenza di ogni backtest (dove i dati passati sono già noti). Il progetto
insegue dati prospettici dalla Fase 14; ora che il motore market-implied è
validato su ogni asse (3 leghe, apertura e chiusura, 2017-2026 — Fasi 26/75/76),
ha senso puntarlo su partite **davvero mai viste**: la prossima stagione.

L'idea: al primo turno 2026-27, per ogni partita, produrre **due** previsioni —
il Dixon-Coles da solo (Modello 1) e il market-implied dalle quote di chiusura
reali (Modello 2) — e, a risultati acquisiti, **scorarle** (log-loss, Brier) per
lega e per mercato, controllando anche la **calibrazione** (le probabilità
dichiarate corrispondono alle frequenze reali?).

## 2 · Anteprima illustrativa (congelata 2026-07-23) — SOLO Modello 1 (DC)

⚠️ **Non è il test scorato.** È ciò che si può produrre *oggi* dalla sessione di
sviluppo, con questi limiti **dichiarati**:
- i **calendari** 2026-27 non sono verificabili in modo affidabile da qui
  (`WebFetch` bloccato; gli snippet di ricerca su stagioni future sono
  speculativi — mescolavano squadre di Championship): le partite qui sotto sono
  **plausibili, non ufficiali**;
- i **dati si fermano a 2025-26** → le forze delle squadre sono "vecchie" di
  un'estate di mercato (nuovi acquisti/cessioni non pesati);
- **niente quote** raggiungibili da qui → **niente Modello 2** (market-implied).
  Solo il DC-da-solo;
- l'anteprima è generata con la **config giusta per lega** (`LEAGUE_CONFIGS`,
  δ Premier 0.33) via `scripts/_run_prospettico_2627.py`. **Da Fase 83-bis anche
  `predict.py` è per-lega** (`--league premier_league` usa δ=0.33 ecc.): il
  "passo 2" del Modello 1 è chiuso, il tool ufficiale può ora produrre M1 per
  ogni lega. ~~Resta per-contesto solo il θ del router nel path market-implied
  (M2): per Premier il M2 andrà prodotto con `dp_theta` neutro.~~ **Chiuso dalla
  Fase 92-bis**: anche il M2 è per-lega, `predict.py --league <lega>` prende
  θ/φ0/κ/sharpen da `src.config.MARKET_ENGINE` — nessun passo manuale.

**Premier League — previsione DC (as_of 2026-08-15, dati fino a 2025-26):**

| partita | 1 | X | 2 | Over 2.5 | GG |
|---|--:|--:|--:|--:|--:|
| Newcastle–Liverpool | 34.1% | 26.5% | 39.5% | 64.0% | 68.1% |
| Man City–Bournemouth | 65.1% | 20.9% | 14.0% | 61.7% | 57.7% |
| Brighton–Aston Villa | 41.3% | 28.1% | 30.6% | 54.2% | 60.4% |
| Fulham–Chelsea | 33.5% | 29.5% | 37.0% | 52.1% | 59.2% |
| Brentford–Tottenham | 48.6% | 25.3% | 26.1% | 61.1% | 64.4% |
| Everton–Crystal Palace | 38.9% | 31.4% | 29.7% | 41.4% | 50.5% |
| Nott'm Forest–Leeds | 45.1% | 28.0% | 26.9% | 51.0% | 57.1% |

Dati grezzi (λ,μ e tutti i mercati): `experiments/prospettico_2026_27_dc.csv`.
Serie A e La Liga: calendari non reperiti in modo affidabile → **slot vuoti**,
da riempire coi fixture ufficiali (§5).

**Come leggerla, onestamente.** Sono previsioni *ragionevoli* di un modello che
non ha ancora visto il mercato 2026-27 né i trasferimenti estivi. Ci si aspetta
che il DC-da-solo sia **battuto dal mercato** (α\*=0, dimostrato ovunque): il
valore del test non è "vincere", è **misurare quanto** perde e se resta ben
calibrato su dati mai visti — e, quando ci saranno le quote, mostrare che il
market-implied riproduce il mercato ed estende ai mercati non quotati.

## 3 · Il protocollo del test VERO (da eseguire vicino al calcio d'inizio)

Per ciascuna delle **5** leghe, giornata 1:
1. **Fixture ufficiali** (fonte: lega/Wikipedia, verificati).
2. **Modello 1 — DC**: `scripts/_run_prospettico_2627.py` oppure, ora che è
   per-lega, `predict.py --league <lega>` (config δ/γ giusta), congelato PRIMA
   del kickoff.
3. **Modello 2 — market-implied**: raccogliere le **quote di chiusura** reali
   (1X2 + O/U 2.5) di ogni match e invertirle (`predict.py --odds …` /
   `price_markets`). Da fare vicino al calcio d'inizio. **Nessun passo manuale**:
   dalla Fase 92-bis `predict.py --league <lega>` prende θ/φ0/κ/sharpen da
   `src.config.MARKET_ENGINE` — motore con θ=1.225 per la Serie A, **liscio**
   (θ neutro, φ0=0) per Premier, Liga, Bundesliga e Ligue 1.
4. **Baseline**: frequenza storica dell'esito (già nota) per riferimento.
5. **Dopo il full-time**: risultati reali → log-loss/Brier per mercato e per
   lega, di Modello 1, Modello 2 e baseline; controllo di calibrazione
   (reliability diagram). Registrare un run `source=prospettico_2627` in
   `runs.jsonl`. Aspettativa dichiarata: Modello 2 ≈ mercato; Modello 1 peggio;
   nessun edge di ROI (non si simula denaro — §CLAUDE.md).

## 4 · Vincoli ambientali (perché il test non si chiude in un colpo)

Dalla sessione di sviluppo cloud: `WebFetch` è **bloccato del tutto** (403 anche
su Wikipedia, bug noto — `docs/MANUALE_SOPRAVVIVENZA.md`); i siti di quote
(oddschecker, ecc.) bloccano i bot; gli snippet di ricerca non danno quote
decimali pulite né fixture affidabili di stagioni future. Quindi le **quote
reali vanno raccolte per un canale diverso** vicino al kickoff:
- **GitHub Actions** (runner con rete libera, pattern Fase 67), oppure
- una **sessione browser reale** (Cowork, pattern Fase 70),
- o inserite a mano dall'utente in un piccolo bundle in `files/`.

## 4-bis · Quanta POTENZA ha questo test (Fase 98) — il vincolo di disegno

Il calcolo è stato fatto sui dati veri (6.840 partite, differenze appaiate
per-partita, `scripts/_run_prospective_power.py`). Controllo di validità
superato: gap 1X2 pooled +0.0179, che riproduce il +0.0165 noto.

**Buona notizia**: le partite sono **indipendenti** — autocorrelazione di ordine
1 +0.007, ICC ≈ 0, **DEFF = 1.00**. Non c'è penalità da clustering (per giornata
o per stagione): ogni partita raccolta conta per una.

**Cattiva notizia**: il rapporto segnale/rumore è **1:8,5** (sd delle differenze
0.1527 contro un gap di 0.0179). Da cui:

| campione | potenza sul gap col mercato | verdetto |
|---|--:|---|
| **30 partite** (1 giornata × 3 leghe) | **9,8%** | MDE 0.0781 = 4,7× il gap: **non conclude mai** |
| 380 (1 stagione, 1 lega) | 62,5% | sotto-dimensionato |
| **574** | **80%** | ≈ 19 giornate su 3 leghe |
| 1140 (1 stagione × 3 leghe) | 97,7% | il disegno giusto |

⚠️ **Questa tabella è calcolata su 3 leghe** (6.840 partite appaiate, Fase 98) e
**non è stata rifatta** dopo l'ingresso di Bundesliga e Ligue 1. Cambia solo il
rapporto giornate↔partite, non il segnale/rumore: una giornata su **5** leghe
vale **~48 partite** (10+10+10+9+9) invece di 30, quindi le ~574 partite della
soglia 80% si raggiungono in **~12 giornate** invece di 19. Le percentuali di
potenza in colonna restano quelle misurate: ri-calcolarle sulle 5 leghe è un
lavoro aperto, non un numero da dedurre a mente.

Gerarchia netta fra i bersagli: contro la **baseline** bastano **184** partite
(6 giornate); contro il **mercato** ne servono **574** sull'1X2, **2.254** sul
GG/NG, **2.988** sull'O/U 2.5.

**Conseguenze operative su questo test:**

1. **la giornata 1 da sola non può concludere nulla** contro il mercato. Va
   trattata per quello che è: il **collaudo del protocollo** (fixture veri,
   quote reali, congelamento, scoring) — non la prova.
2. **il bersaglio realistico della giornata 1 è la baseline**, non il mercato:
   con 30 partite nemmeno quella conclude (servono 184), ma la direzione è
   leggibile e i 6 turni si accumulano in fretta.
3. **si scora l'1X2 per primo**: dà potenza **4-5×** prima di GG/NG e O/U.
   Riportare gli altri mercati va bene, ma dichiarando che sono
   sotto-dimensionati.
4. **il piano va esteso a ~19 giornate su 3 leghe** (≈ metà stagione) per una
   prima conclusione onesta sul mercato, e a una stagione intera per il 97,7%.
   Cioè: questo file resta APERTO per mesi, per costruzione.
5. **l'outright NON è testabile qui**: servirebbero ~57 stagioni-lega, 3 leghe in
   una stagione danno **9,8%** di potenza (vedi Fase 98 e `docs/PISTE.md` §4-bis).

---

## 5 · «DA RIPETERE / COMPLETARE PIÙ AVANTI» — checklist

- [ ] **Vicino al primo turno 2026-27** — date da `newseason.md` §1: Liga
  **16/8**, Premier e Ligue 1 **21/8**, Serie A **22/8**, Bundesliga **28/8**
  (la scadenza vera è il **16 agosto**):
  - [ ] verificare i **fixture ufficiali** di giornata 1 (**5 leghe**);
  - [ ] rigenerare il **Modello 1 (DC)** coi fixture veri e congelarlo;
  - [ ] raccogliere le **quote di chiusura** reali e generare il **Modello 2**;
  - [ ] congelare tutto PRIMA del calcio d'inizio (commit con data).
- [ ] **Dopo il full-time**: risultati reali → scoring (log-loss/Brier/
  calibrazione) di M1/M2/baseline, per lega e per mercato; run in `runs.jsonl`;
  voce nel diario (nuova fase) con i numeri.
- [ ] Confrontare l'anteprima DC congelata oggi (§2) coi risultati reali: quanto
  è costata l'estate di mercato non vista + la config non ancora per-lega.
- [ ] **(NON opzionale, Fase 98) estendere a ≥19 giornate su 3 leghe** (~574
  partite) prima di dichiarare qualsiasi cosa sul confronto col mercato: con 30
  partite la potenza è 9,8% (vedi §4-bis).

---

*Aggiornare questo file a ogni passo del test (fixture → previsioni congelate →
risultati → scoring). Finché resta APERTO, il test non è concluso.*
