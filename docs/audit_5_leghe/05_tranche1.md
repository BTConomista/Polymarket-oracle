# Report 5 — Tranche 1: le correzioni dati (parte eseguibile nel cantiere)

La tranche 1 era divisa in due dalla regola di isolamento (R4): ciò che si può
correggere **dentro il cantiere** e ciò che tocca `src/` o i documenti condivisi
e quindi aspetta l'integrazione. Qui la prima parte, **fatta**.

---

## 1 · Cosa è stato corretto

Tutto tramite il registro [`data/correzioni_dichiarate.csv`](../../data/correzioni_dichiarate.csv)
e lo script `scripts/applica_correzioni.py` (regole R1/R3: nessuna modifica a
mano, verifica del valore-prima cella per cella, idempotente).

### 1.1 · Otto linee O/U con margine impossibile → NaN dichiarato

| lega | stagione | partita | over | under | overround |
|---|---|---|--:|--:|--:|
| bundesliga | 2017-18 | Leverkusen-Dortmund | 1.45 | 1.69 | 1.2814 |
| bundesliga | 2017-18 | Hoffenheim-RB Leipzig | 1.59 | 1.52 | 1.2868 |
| bundesliga | 2017-18 | Ein Frankfurt-Bayern Munich | 1.56 | 1.55 | 1.2862 |
| bundesliga | 2017-18 | Bayern Munich-Hertha | 1.42 | 1.75 | 1.2757 |
| bundesliga | 2017-18 | Werder Bremen-Leverkusen | 1.45 | 1.70 | 1.2779 |
| bundesliga | 2018-19 | Dortmund-Wolfsburg | 1.54 | 1.45 | **1.3390** |
| ligue_1 | 2017-18 | Lyon-Metz | 1.30 | 2.02 | 1.2643 |
| ligue_1 | 2017-18 | Monaco-Lyon | 1.58 | 1.54 | 1.2823 |

Il mercato si scarta **in blocco** (mai un solo lato), come già fa il guard
esistente per l'overround < 1: 16 celle a NaN. Soglia 1.12, motivata dal fatto
che nell'era `Avg` il massimo mai osservato su 12.457 righe è **1.0765**.

### 1.2 · Un xG «impossibile» che impossibile non era → correzione RITIRATA

Avevo portato a NaN `home_xg`/`home_npxg` di Bielefeld-Leverkusen 21/11/2020
(xG 0.0 con un gol segnato). Approfondendo su richiesta, il dato è risultato
**corretto**: il gol era un **autogol del portiere avversario** e il Bielefeld
non ha tirato nemmeno una volta. La correzione è stata **ritirata** e lo 0.0
ripristinato; il registro conserva sia le righe sbagliate (`stato = ritirata`,
col motivo) sia quelle di ripristino. Dettaglio in
[`07_dati_corrotti.md`](07_dati_corrotti.md) §1.

Il controllo automatico è stato corretto: ora verifica gli autogol sul dato
tiro-per-tiro prima di dichiarare un'impossibilità.

### 1.3 · Verifica dopo le correzioni

```
audit avversariale, leghe nuove:   margini impossibili 0 (erano 8)
                                   xG impossibili      0 (su 5 leghe, con la
                                                       verifica degli autogol)
audit A/B/C/D, bundesliga:         0 FAIL, 0 WARN su 24 controlli
audit A/B/C/D, ligue_1:            0 FAIL, 2 WARN (lacune note della fonte)
pytest:                            153 test verdi
```

L'audit **non** è stato ammorbidito: le righe corrette sono escluse dal solo
confronto con la fonte (segnalate come `INFO`, con il registro come
giustificazione), e tutto il resto resta severo.

---

## 2 · Cosa resta in attesa dell'integrazione (tranche 2)

| # | cosa | perché è bloccato |
|---|---|---|
| 1 | il **guard sull'overround** in `loader._pick_market_odds` (patch pronta in [`patch_guard_overround_APPLICATA.md`](patch_guard_overround_APPLICATA.md)) | tocca `src/` |
| 2 | le **3 celle La Liga** con lo stesso difetto (Alaves-Real Madrid, Eibar-Real Madrid, Leganes-Betis) e le **3 stime** che ne dipendono | tocca `data/` e `data/estimates/` |
| 3 | il guard generale sull'**xG impossibile** in `understat.parse_season_xg` | tocca `src/` |
| 4 | l'**ordine colonne** di Premier/Liga + il test cross-lega | tocca `data/` e `tests/` |
| 5 | le **dichiarazioni** in `DATI.md` (Udinese-Roma, Ligue 1 2019-20, lacuna Europa League 2025-26) e le 3 precisazioni sulle stime | tocca `docs/` |

Nel cantiere le due leghe nuove sono **già pulite**; le tre leghe storiche
restano come sono finché non si decide di unire i filoni.
