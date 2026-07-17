# La rosa dei modelli — titolari, panchina, bocciati (su due fronti)

Questo file è il **registro unico dello stato di OGNI modello/leva del
progetto**, in tre categorie:

- **⚽ TITOLARI** — in config ufficiale o attivi nei tool;
- **🪑 PANCHINA** — misurati **migliorativi ma NON attivati** (CI che contiene
  lo zero, rumore, una sola lega, multiple testing…);
- **❌ BOCCIATI** — testati e scartati (peggiorativi o nulli in modo robusto).

**I due fronti (regola dalla Fase 65, fissata nel CLAUDE.md).** D'ora in poi
ogni modello si sviluppa e si traccia su DUE fronti:
1. **per-lega** — costanti/iperparametri ritarati sulla singola lega (es. il
   DC della Serie A con δ=0.23, quello della Premier con δ=0.33);
2. **generale** — versione unica cross-lega (pooled/universale, es. lo
   stimatore E3 della Fase 62-bis, fittato su 3 leghe insieme — che ha BATTUTO
   le versioni per-lega).

Ogni cella della matrice sotto dichiara lo stato di quel modello su quel
fronte. `⬜` = **mai testato lì**: è lavoro potenziale, non un'assoluzione.

**Regole del file (fissate nel CLAUDE.md §2):**
1. va aggiornato **a ogni esperimento** che tocca lo stato di un modello
   (nuovo modello → riga nuova; promozione/bocciatura → cella aggiornata e
   voce spostata di sezione, con data e motivo nell'archivio);
2. ogni voce dichiara numeri, motivo dello stato, come si attiva, cosa lo
   cambierebbe;
3. i numeri devono essere ricalcolabili da `runs.jsonl` (regola Fase 15).

> Nota di metodo — l'eccezione che definisce i criteri: il **prior neopromosse
> δ** fu adottato (Fase 7) *nonostante* un CI non conclusivo, per **motivazione
> strutturale** (meccanismo chiaro, direzione confermata su ogni finestra,
> Fasi 17/19). La panchina non è quindi un "mai": è un "non finché non c'è o
> più potenza o una ragione strutturale forte".

---

## La matrice — ogni modello × ogni fronte, a colpo d'occhio

⚽ titolare · 🪑 panchina · ❌ bocciato · ⬜ mai testato · ✱ vedi nota

| modello | Serie A | Premier | La Liga | generale (pooled) |
|---|:-:|:-:|:-:|:-:|
| **Market-implied → matrice DC** (con quote 1X2+O/U) | ⚽ F26/41 | ⬜ ✱1 | ⬜ ✱1 | ⚽ struttura (ρ=−0.06 unico) |
| **+ router v3 (double-Poisson θ)** | ⚽ F52 (θ=1.225) | ❌ F53 (θ=1.069, non paga) | ❌ F53 (θ=1.097, non paga) | ❌ θ decresce con la liquidità |
| **+ φ35 famiglia-pareggio** | ⚽ F41/44 | ⬜ ✱2 | ⬜ ✱2 | ⬜ |
| **+ dp_lvl / sharpen_1x2** (affina la chiusura) | ⚽ nel tool F51/52 ✱3 | ❌ F53 | ❌ F53 | ❌ proprietà della chiusura SA |
| **Dixon-Coles + xG** (fallback senza quote) | ⚽ δ=0.23 | ⚽ δ=0.33 F57 | ⚽ δ=0.22 F57 | ⚽ ✱4 iperparametri comuni |
| **Stimatore chiusura O/U (E3)** | ⚽ tool stime | ⚽ tool stime | ⚽ tool stime | ⚽ F62-bis (il pooled VINCE) |
| GG/NG φ35+knee34 su market-implied | 🪑 F50 | ⬜ | ⬜ | ⬜ |
| Ricalibrazione per-classe del mercato (w_D, w_A) | 🪑 F50-ter | ❌ F53 (direzione OPPOSTA, w_D=0.93) | 🪑 F53 (+3.6% P81) | ❌ segno non universale |
| Devig di Shin | 🪑 F52-ter (P 97%) | 🪑 F53 (P 68%) | 🪑 F53 (P 94%) | 🪑 sempre ≥ moltiplicativo |
| φ35 sul path DC standalone | 🪑 F35 | ⬜ | ⬜ | ⬜ |
| Nudge GG/NG fine stagione (path DC) | 🪑 F48 | ⬜ | ⬜ | ⬜ |
| Ensemble emivite 180+730 | 🪑 F12a | ⬜ | ⬜ | ⬜ |
| Ricalibrazione per-classe del modello | 🪑 F10 | ⬜ | ⬜ | ⬜ |
| Diagonale inflazionata (`--draw-inflation`) | 🪑 F12b | ⬜ | ⬜ | ⬜ |
| Covariata `rest_full` (congestione vera) | 🪑 F4e-bis | ⬜ colonne pronte F59 | ⬜ colonne pronte F59 | ⬜ |
| Temperature scaling post-hoc | 🪑 F6 (T≈0.94) | ⬜ | ⬜ | ⬜ |
| Covariata `midweek_europe` (dummy congestione) | 🪑 F36-bis | ⬜ colonne pronte F59 | ⬜ colonne pronte F59 | ⬜ |
| Temperatura sopra dp_lvl (T=1.056) | 🪑 F52-ter | ❌ (dp_lvl bocciato lì) | ❌ | ❌ |
| GBM (diretto, per mercato, bespoke) | ❌ F21-23/50-quater | ⬜ ✱5 | ⬜ ✱5 | ❌ tetto informativo |
| Poisson bivariato (λ3) | ❌ F42 | ⬜ | ⬜ | ⬜ |
| Copula di Frank | ❌ F43/50 | ⬜ | ⬜ | ⬜ |
| GAS / score-driven (state-space) | ❌ F52-sexies | ⬜ | ⬜ | ⬜ |
| Binomiale negativa · zero-inflazione · Rue-Salvesen | ❌ F27/51 | ⬜ | ⬜ | ⬜ |
| ρ dinamico per-partita | ❌ F18 | ⬜ | ⬜ | ⬜ |
| Power-devig / denoising cross-stagione | ❌ F38/50 | ⬜ | ⬜ | ⬜ |
| Covariata stakes + router stakes-aware | ❌ F32/36/45 | ⬜ | ⬜ | ⬜ |
| Vantaggio-casa per-squadra | ❌ F8 (r≈0.00) | ⬜ | ⬜ | ⬜ |
| Covariate nel canale-pareggio | ❌ F37 | ⬜ | ⬜ | ⬜ |
| Ricalibrazione O/U del mercato | ❌ F51-quater | ⬜ | ⬜ | ⬜ |
| Ensemble standalone (DC+biv+GBM) | ❌ F46 | ⬜ | ⬜ | ⬜ |
| Blend modello+mercato (lineare α / GBM) | ❌ F16 (α*≈0) / F23 | ⬜ | ⬜ | ⬜ |
| Profilo stagionale dinamico (γ/λ,μ nel tempo) | ❌ F47/48 | ⬜ | ⬜ | ⬜ |
| Tiri in porta grezzi nel blend | ❌ F3 | ⬜ | ⬜ | ⬜ |
| Covariate squad_value/absence/npxG/forma/luck/ppda/deep | ❌ F4c/11/13/33 | ⬜ | ⬜ | ⬜ |

Note della matrice:
- **✱1** Il motore market-implied su Premier/Liga non è mai stato backtestato
  multi-mercato (solo il tracer market-side F53); la struttura è la stessa,
  le costanti (ρ, θ, φ) vanno riviste per lega. **Primo candidato del fronte
  per-lega.**
- **✱2** Il draw-bias non si replica in Premier (F53): la φ35 lì potrebbe
  avere segno diverso — da testare, non da copiare.
- **✱3** dp_lvl è nel tool `predict.py` SOLO per la Serie A; è "valore da
  oracolo" (log-loss), NON da scommessa (F51-ter: niente ROI).
- **✱4** F57: la ri-taratura per lega è PIATTA su emivita/shrinkage/α → gli
  iperparametri del DC sono di fatto GENERALI; solo δ è per-lega. È il primo
  esempio documentato di "versione generale" che regge.
- **✱5** Il GBM non è mai stato rifatto su Premier/Liga, ma il tetto
  informativo è universale (F57): riaprirlo richiederebbe una ragione nuova.

---

## ⚽ I titolari (in config ufficiale o nei tool)

| modello | dove è attivo | fronte per-lega | fronte generale |
|---|---|---|---|
| **Market-implied + router v3 + φ35** | pricing con quote 1X2+O/U (`price_markets(dp_theta)`, `predict.py`) | costanti Serie A (θ=1.225/1.138, φ0, κ); **altre leghe da ritarare** | struttura universale; ρ=−0.06 unico |
| **Dixon-Coles + blend xG** | fallback senza quote; `backtest.py` | `LEAGUE_CONFIGS`: δ 0.23/0.33/0.22; il resto è comune (F57) | iperparametri comuni = versione generale di fatto |
| **sharpen_1x2 (dp_lvl)** | `predict.py`, solo Serie A | SA only | bocciato fuori SA (F53) |
| **Stimatore E3 chiusura O/U** | `scripts/build_estimates.py` → `data/estimates/` | (per-lega TESTATO e battuto dal pooled) | **pooled: 5 coefficienti unici, MAE 0.0117** |
| **Baseline frequenze H/D/A** | benchmark in ogni backtest | per-lega per costruzione | — |

---

## 🪑 La panchina (migliorativi misurati, non attivati)

| # | leva (fase) | Δ nominale | perché in panchina | attivazione |
|---|---|---|---|---|
| 1 | GG/NG: φ35+knee34 sul market-implied (50) | **−0.0010** GG (P 98%) | CI al limite + multiple testing | opt-in engine |
| 2 | Ricalibrazione per-classe del MERCATO (50-ter) | −0.0006 pooled (P 78%) | servono ~20 stagioni; **Premier smentisce il segno** (F53) | `market_denoise` |
| 3 | Devig di Shin (52-ter) | −0.0007 1X2 (P 97%); direzione confermata su 3/3 leghe (F53) | non concluso; toccherebbe la fonte unica | funzione pronta |
| 4 | φ(λ−μ) sul path DC standalone (35) | −0.0007 1X2 | CI include 0 | `--draw-balance` |
| 5 | Nudge GG/NG di fine stagione, path DC (48) | −0.006 finale (P 89-92%) | nessun CI esclude 0; si sgonfia con più dati | `btts_season` opt-in |
| 6 | Ensemble di emivite 180+730 (12a) | −0.0006 (4/6) | borderline, rumore | ri-run con 2 fit |
| 7 | Ricalibrazione per-classe 1X2 del MODELLO (10) | −0.0005 | rumore (bias però robusto) | pesi fissi 0.96/1.04/1.00 |
| 8 | Diagonale inflazionata (12b) | −0.0004 (3/6) | rumore; calibra il pari ma non paga in LL | `--draw-inflation` |
| 9 | Covariata congestione vera `rest_full` (4e-bis) | −0.0004 | rumore | `--covariates rest_full` |
| 10 | Temperature scaling post-hoc (6) | −0.0003 | trascurabile (T≈0.94 robusto) | `scripts/calibrate.py` |
| 11 | GBM + finishing-luck (33) | −0.0022 (P 81%) | non conclusivo, e il GBM di suo perde dal DC | — |
| 12 | Covariata `midweek_europe` (36-bis) | −0.0003, ma β=−0.020 **stabile 6/6** | CI include 0; ridondante con rest_full insieme | `--covariates midweek` |
| 13 | Temperatura sopra dp_lvl (52-ter) | 0.9609→**0.9605** (T=1.056) | si somma a una leva già Serie-A-only e da oracolo | sopra `sharpen_1x2` |

### Dettaglio delle voci di panchina

#### 1 · GG/NG: φ35 + ricalibrazione-μ (knee34) sul market-implied — Fase 50
- **Cosa**: la miglior stima GG/NG del progetto: market-implied → ricalibrazione
  dei tassi walk-forward → φ(|λ−μ|). GG **0.6810** vs 0.6820 del motore liscio.
- **Numeri**: Δ −0.0010, CI [−0.0020,−0.0000], P 98%, 5/7 stagioni; guadagno
  concentrato nell'era porte-chiuse 2019-22, ≈neutro nelle ultime 4 stagioni.
- **Perché in panchina**: CI che tocca lo zero dopo ~50 fasi di test sulla
  stessa finestra (disciplina multiple-testing, Fase 17); deriva temporale del
  guadagno sospetta.
- **Fronti**: solo Serie A. **Promozione se**: il guadagno riappare su stagioni
  NUOVE (2026-27+) o sul fronte per-lega di Premier/Liga (mai provato lì).

#### 2 · Ricalibrazione per-classe del MERCATO (w_D≈1.09, w_A≈1.06) — Fase 50-ter
- **Cosa**: correggere la chiusura stessa per il draw-bias noto (pari e
  trasferta sottoprezzati in Serie A).
- **Numeri**: pooled Δ −0.0006, CI [−0.0020,+0.0009], P 78%, ma **5/6 stagioni
  migliorano** e i pesi sono stabili anno su anno.
- **Perché in panchina**: "la crepa più credibile sulla chiusura, non conclusa
  — servono ~20 stagioni per il verdetto" (diario).
- **Fronti**: il segno NON è universale — su Premier i pareggi sono
  SOVRA-prezzati (w_D=0.93, Fase 53), sulla Liga il bias somiglia alla Serie A.
  Una "versione generale" è quindi **bocciata in partenza**; resta il fronte
  per-lega. **Promozione se**: più stagioni per lega o un meccanismo che
  spieghi il segno (liquidità?).

#### 3 · Devig di Shin al posto del moltiplicativo — Fase 52-ter
- **Cosa**: rimozione del margine che modella gli scommettitori informati
  (corregge il favourite-longshot bias); |shin−molt| medio 0.0047.
- **Numeri**: 1X2 0.9617 vs 0.9625 (Δ −0.0007, P 97%) in Serie A; direzione
  confermata su Premier (P 68%) e Liga (P 94%) — Fase 53.
- **Perché in panchina**: P alto ma non concluso (multiple testing); e il devig
  moltiplicativo è la **fonte unica** di tutto il progetto (`metrics.devig_*`):
  cambiarla ricalcolerebbe ogni benchmark storico — costo di coerenza alto per
  −0.0007.
- **Fronti**: è il miglior candidato a promozione sul fronte GENERALE (unica
  voce di panchina con direzione confermata su 3/3 leghe). **Promozione se**:
  migrazione one-shot documentata (tutti i benchmark ricalcolati nello stesso
  commit).

#### 4 · φ(|λ−μ|) draw-balance sul path DC standalone — Fase 35
- **Cosa**: inflazione del pareggio condizionata all'equilibrio della partita.
- **Numeri**: 1X2 0.9790 (Δ −0.0007, migliore di 4 varianti); calibrazione dei
  pareggi nelle partite equilibrate 0.287→0.334 (reale 0.332): **batte il
  mercato in calibrazione** su quel sottoinsieme.
- **Perché in panchina**: CI include lo zero sul log-loss aggregato.
- **Stato particolare**: è **già titolare** nel router market-implied
  (famiglia-pareggio, Fasi 41/44) e in `predict.py`; in panchina resta SOLO
  l'uso sul path DC standalone (senza quote).
- **Fronti**: mai testata su Premier/Liga; su Premier il draw-bias è OPPOSTO
  (F53) → sul fronte per-lega potrebbe servire φ0 di segno diverso.

#### 5 · Nudge GG/NG di fine stagione (path DC) — Fase 48
- **Cosa**: boost stagionale dei tassi (giornate 35-38) per il GG/NG derivato
  dal DC. Vale SOLO sul path senza quote: il mercato prezza già il finale
  (Fase 50-bis).
- **Numeri**: finale −0.006 (P 89-92%), overall P 84-93%; l'effetto si sgonfia
  con più dati (boost-ospite 38ª ×1.148→×1.072 passando a 8 stagioni).
- **Perché in panchina**: nessun CI esclude lo zero; deriva del parametro.
- **Attivazione**: `market_implied.btts_season` (opt-in, off di default).

#### 6 · Ensemble di emivite 180+730 — Fase 12a
- **Numeri**: −0.0006, 4/6 stagioni, "borderline".
- **Perché in panchina**: rumore; raddoppia il costo di fit per un guadagno
  non distinguibile da zero.

#### 7 · Ricalibrazione per-classe 1X2 del modello — Fase 10
- **Cosa**: il bias è **robusto** (casa sovrastimata, pareggio sottostimato,
  conferma in ogni stagione), pesi fissi 0.96/1.04/1.00.
- **Numeri**: −0.0005, nel rumore.
- **Perché in panchina**: il bias è reale ma piccolo; correggerlo non paga in
  log-loss. Utile per l'uso pratico dove serve calibrazione, non ranking.

#### 8 · Diagonale inflazionata (`--draw-inflation`) — Fase 12b
- **Numeri**: −0.0004 (3/6); migliora la calibrazione del pareggio.
- **Perché in panchina**: *quanti* pareggi capitano è quasi-rumore; il log-loss
  non premia. Stessa nicchia d'uso pratico della voce 7.

#### 9 · Covariata congestione vera `rest_full` — Fase 4e-bis
- **Numeri**: −0.0004 medio (2020-25), inverte il segno del proxy solo-lega ma
  resta nel rumore.
- **Perché in panchina**: guadagno non distinguibile da zero.
- **Fronti**: dalla Fase 59 le colonne esistono anche per Premier/Liga, dove la
  covariata **non è mai stata testata** — il test per-lega più facile in lista.

#### 10 · Temperature scaling post-hoc — Fase 6
- **Numeri**: T≈0.94 (sottoconfidenza lieve, robusta), guadagno −0.0003.
- **Perché in panchina**: trascurabile. Modulo pronto
  (`src/evaluation/calibration.py`) per l'uso pratico.

#### 11 · GBM + finishing-luck — Fase 33
- **Numeri**: −0.0022 (P 81%) del GBM con la covariata luck.
- **Perché in panchina**: non conclusivo E il GBM parte comunque dietro al DC
  (Fase 22): un miglioramento di un modello non attivo non è una promozione.

---

## ❌ I bocciati (testati e scartati — coi numeri del verdetto)

| modello/leva (fase) | verdetto | numero chiave |
|---|---|---|
| Tiri in porta grezzi nel blend (3) | nullo/negativo su 6 stagioni | — |
| Vantaggio-casa per-squadra (8) | il γ per-club è solo rumore stagionale | persistenza anno-su-anno r≈0.00 |
| Covariate squad_value / absence / npxG (4c, 11) | ridondanti con gol+xG; squad_value PEGGIORA in ogni combo | +0.0004…+0.0007 |
| Forma / streak / rendimento recente (13) | già catturati dal fit pesato nel tempo | corr residui +0.035 |
| Blend lineare modello+mercato (16) | il mercato INGLOBA il modello | α* ≈ 0 perfino in-sample |
| ρ dinamico per-partita (18) | instabile, sbatte sui bound | +0.0003 [−0.0007,+0.0013] |
| GBM diretto per mercato (21/22/36) | non batte il DC su NESSUN mercato; col feature-set completo overfitta | CI<0 escluso su 5/6; train 0.913→0.867, test ~1.01 |
| GBM modello+mercato (23) | degrada perfino il mercato-feature | 0.9996 vs mercato 0.9632 |
| Finestre dati corte (25) | più storia batte meno, sempre | 3 stag +0.0011, 2 stag +0.0019 |
| Binomiale negativa (27) | i gol NON sono sovra-dispersi dati i tassi | nb_size→Poisson |
| Power-devig / denoising (38, 50) | motore già non-biased | Platt a≈1.06 peggiora +0.0020; η=0.909 mai utile |
| Poisson bivariato λ3 (42) | l'equilibrio \|λ−μ\| batte la correlazione globale | perde vs φ35 |
| Copula di Frank (43, 50) | dipendenza flessibile senza guadagno | tetto = φ35; +compless. per −0.0001 |
| Covariata stakes + router stakes-aware (32/36/45) | segnale reale sul mismatch ma NON sfruttabile: il GBM-stakes non batte il DC nemmeno lì | soft −0.0018, P 53% |
| Covariate nel canale-pareggio (37) | "cruciali → più pari" è FALSO; canale saturo | residuo −0.0017 |
| Ricalibrazione O/U del mercato (51-quater) | il bias O/U è instabile (a differenza del tilt 1X2) | +0.0013 out-of-sample |
| Ensemble standalone DC+biv+GBM (46) | nessun ensemble batte il miglior singolo | 1X2 mean +0.0033 |
| Profilo stagionale dinamico γ/λ,μ (47/48) | l'effetto si sgonfia con più dati | ×1.148→×1.072 |
| GBM bespoke per singolo mercato (50-quater) | perde su ogni mercato e su entrambi i path | anche con l'engine tra le feature |
| Rue-Salvesen · zero-inflazione 0-0 (51) | nulli | γ=+0.03; z≈0 |
| GAS / score-driven (52-sexies); Kalman chiuso-per-argomento (51) | memoria effettiva troppo corta (~25 partite); l'emivita del DC è già lo steady-state di un Kalman | +0.0027 vs DC batch, P 18% |
| dp_lvl fuori dalla Serie A (53) | il beat-the-close è idiosincrasia della chiusura SA | Premier +0.0008, Liga +0.0001 |
| Ri-taratura per-lega di emivita/shrinkage/α (57) | piatta: il gap è informazione, non calibrazione | tutti i Δ entro ±0.0005 |

---

## Lead operativi (non modelli, ma misurati e in attesa)

| lead (fase) | numeri | stato |
|---|---|---|
| **Draw-bias Serie A**: puntare il pari nelle partite equilibrate (40) | ROI **+4.7%** (CI [−4.9,+14.4], P 83%, 4/6 stagioni); conferma indipendente Fase 51-ter: +3.2% (P 76%) | non concluso, alta varianza; NON si replica su Premier (−5.4%, Fase 53), mezzo-gemello in Liga (+3.6%, P 81%) |
| **Stakes-mismatch** (una squadra "decisa", l'altra in corsa) (31/32/45) | gap del modello vs mercato +0.0549 sul mismatch; ma il router stakes-aware NON lo sfrutta (soft −0.0018, P 53%) | informazione del MERCATO, non nostro errore recuperabile (Fase 45 chiude) |

---

## Archivio (voci uscite dalla rosa)

*(vuoto — le voci smentite o promosse si spostano qui con data e motivo)*
