# Test prospettico — giornata 1, stagione 2026-27 (Serie A, Premier, La Liga)

> **Stato: APERTO.** Anteprima illustrativa congelata il 2026-07-23. Il test
> vero (con quote reali e risultati) va **completato più avanti** — vedi §5.

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
  ogni lega. Resta per-contesto solo il θ del router nel path market-implied
  (M2): Fase 81 ha trovato θ*≈1 in Premier vs ~1.2 in Serie A/Liga, quindi per
  Premier il M2 andrà prodotto con `dp_theta` neutro (nota nel protocollo §3).

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

Per ciascuna delle 3 leghe, giornata 1:
1. **Fixture ufficiali** (fonte: lega/Wikipedia, verificati).
2. **Modello 1 — DC**: `scripts/_run_prospettico_2627.py` oppure, ora che è
   per-lega, `predict.py --league <lega>` (config δ/γ giusta), congelato PRIMA
   del kickoff.
3. **Modello 2 — market-implied**: raccogliere le **quote di chiusura** reali
   (1X2 + O/U 2.5) di ogni match e invertirle (`predict.py --odds …` /
   `price_markets`). Da fare vicino al calcio d'inizio. **Nota Fase 81**: per la
   **Premier** il router θ ottimo è ≈1 (non 1.225): produrre il M2 Premier con
   `dp_theta` neutro; Serie A/Liga tengono θ≈1.2.
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

## 5 · «DA RIPETERE / COMPLETARE PIÙ AVANTI» — checklist

- [ ] **Vicino al primo turno 2026-27** (Premier ~21/8, Liga ~15/8, SA ~23/8):
  - [ ] verificare i **fixture ufficiali** di giornata 1 (3 leghe);
  - [ ] rigenerare il **Modello 1 (DC)** coi fixture veri e congelarlo;
  - [ ] raccogliere le **quote di chiusura** reali e generare il **Modello 2**;
  - [ ] congelare tutto PRIMA del calcio d'inizio (commit con data).
- [ ] **Dopo il full-time**: risultati reali → scoring (log-loss/Brier/
  calibrazione) di M1/M2/baseline, per lega e per mercato; run in `runs.jsonl`;
  voce nel diario (nuova fase) con i numeri.
- [ ] Confrontare l'anteprima DC congelata oggi (§2) coi risultati reali: quanto
  è costata l'estate di mercato non vista + la config non ancora per-lega.
- [ ] (Opzionale) ripetere a più giornate/stagioni per potenza statistica.

---

*Aggiornare questo file a ogni passo del test (fixture → previsioni congelate →
risultati → scoring). Finché resta APERTO, il test non è concluso.*
