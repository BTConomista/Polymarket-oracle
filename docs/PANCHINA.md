# La panchina — miglioramenti misurati ma NON attivati

Questo file elenca **ogni leva che nei backtest è risultata nominalmente
migliorativa rispetto alla config attiva, ma che NON è stata adottata** —
perché il CI contiene lo zero, perché il guadagno è nel rumore, o per altre
mancanze di robustezza (una sola lega, multiple testing, alta varianza).

**Perché esiste.** Il registro (`runs.jsonl`) ha *tutte* le run e il diario ha
il *perché* delle decisioni, ma nessuno dei due risponde a colpo d'occhio alla
domanda: *"cosa abbiamo in casa di già misurato che potrebbe diventare
ufficiale se arrivassero più dati/robustezza?"* Questo file sì.

**Regole (fissate nel CLAUDE.md §2):**
1. va **aggiornato ogni volta** che un esperimento si chiude "migliorativo ma
   non adottato" (nuova riga) o che una voce cambia stato (promossa → si
   sposta nella config ufficiale; smentita → si sposta nell'archivio in fondo);
2. ogni voce dichiara **numeri, motivo della panchina, come si attiva, cosa
   la promuoverebbe**;
3. i numeri devono essere ricalcolabili da `runs.jsonl` (regola Fase 15).

> Nota di metodo — l'eccezione che definisce i criteri: il **prior neopromosse
> δ** fu adottato (Fase 7) *nonostante* un CI non conclusivo ([−0.0025,+0.0004],
> P≈93→96.5% con 8 stagioni, Fase 17/19), per **motivazione strutturale**
> (meccanismo chiaro, direzione confermata su ogni finestra). La panchina non è
> quindi un "mai": è un "non finché non c'è o più potenza o una ragione
> strutturale forte".

---

## Vista d'insieme

| # | leva (fase) | Δ nominale | perché in panchina | attivazione |
|---|---|---|---|---|
| 1 | GG/NG: φ35+knee34 sul market-implied (50) | **−0.0010** GG (P 98%) | CI al limite + multiple testing | opt-in engine |
| 2 | Ricalibrazione per-classe del MERCATO (50-ter) | −0.0006 pooled (P 78%) | servono ~20 stagioni | `market_denoise` |
| 3 | Devig di Shin (52-ter) | −0.0007 1X2 (P 97%) | non concluso; toccherebbe la fonte unica | funzione pronta |
| 4 | φ(λ−μ) sul path DC standalone (35) | −0.0007 1X2 | CI include 0 | `--draw-balance` |
| 5 | Nudge GG/NG di fine stagione, path DC (48) | −0.006 finale (P 89-92%) | nessun CI esclude 0; si sgonfia con più dati | `btts_season` opt-in |
| 6 | Ensemble di emivite 180+730 (12a) | −0.0006 (4/6) | borderline, rumore | ri-run con 2 fit |
| 7 | Ricalibrazione per-classe 1X2 del MODELLO (10) | −0.0005 | rumore (bias però robusto) | pesi fissi 0.96/1.04/1.00 |
| 8 | Diagonale inflazionata (12b) | −0.0004 (3/6) | rumore; calibra il pari ma non paga in LL | `--draw-inflation` |
| 9 | Covariata congestione vera `rest_full` (4e-bis) | −0.0004 | rumore | `--covariates rest_full` |
| 10 | Temperature scaling post-hoc (6) | −0.0003 | trascurabile (T≈0.94 robusto) | `scripts/calibrate.py` |
| 11 | GBM + finishing-luck (33) | −0.0022 (P 81%) | non conclusivo, e il GBM di suo perde dal DC | — |

Le voci sono ordinate per (credibilità × grandezza) a giudizio del diario; il
dettaglio di ciascuna è sotto.

---

## Dettaglio delle voci

### 1 · GG/NG: φ35 + ricalibrazione-μ (knee34) sul market-implied — Fase 50
- **Cosa**: la miglior stima GG/NG del progetto: market-implied → ricalibrazione
  dei tassi walk-forward → φ(|λ−μ|). GG **0.6810** vs 0.6820 del motore liscio.
- **Numeri**: Δ −0.0010, CI [−0.0020,−0.0000], P 98%, 5/7 stagioni; guadagno
  concentrato nell'era porte-chiuse 2019-22, ≈neutro nelle ultime 4 stagioni.
- **Perché in panchina**: CI che tocca lo zero dopo ~50 fasi di test sulla
  stessa finestra (disciplina multiple-testing, Fase 17); deriva temporale del
  guadagno sospetta.
- **Promozione se**: il guadagno riappare su stagioni NUOVE (2026-27+) o su
  una lega mai usata per il tuning.

### 2 · Ricalibrazione per-classe del MERCATO (w_D≈1.09, w_A≈1.06) — Fase 50-ter
- **Cosa**: correggere la chiusura stessa per il draw-bias noto (pari e
  trasferta sottoprezzati in Serie A).
- **Numeri**: pooled Δ −0.0006, CI [−0.0020,+0.0009], P 78%, ma **5/6 stagioni
  migliorano** e i pesi sono stabili anno su anno.
- **Perché in panchina**: "la crepa più credibile sulla chiusura, non conclusa
  — servono ~20 stagioni per il verdetto" (diario). E la Fase 53 ha mostrato
  che il draw-bias NON si replica su Premier (pareggi sovra-prezzati lì).
- **Promozione se**: più stagioni Serie A confermano; o si capisce il
  *meccanismo* (liquidità? cultura di scommessa?) così da prevederne il segno
  per lega.

### 3 · Devig di Shin al posto del moltiplicativo — Fase 52-ter
- **Cosa**: rimozione del margine che modella gli scommettitori informati
  (corregge il favourite-longshot bias); |shin−molt| medio 0.0047.
- **Numeri**: 1X2 0.9617 vs 0.9625 (Δ −0.0007, P 97%); metà dell'edge del
  dp_lvl era in realtà "devig migliore".
- **Perché in panchina**: P 97% ma non concluso (multiple testing); e il devig
  moltiplicativo è la **fonte unica** di tutto il progetto (`metrics.devig_*`):
  cambiarla ricalcolerebbe ogni benchmark storico — costo di coerenza alto per
  −0.0007.
- **Promozione se**: si decide una migrazione one-shot documentata (tutti i
  benchmark ricalcolati nello stesso commit) e il guadagno regge cross-lega.
- Nota: `shin_devig` esiste già (`scripts/_run_fase52_shin.py`).

### 4 · φ(|λ−μ|) draw-balance sul path DC standalone — Fase 35
- **Cosa**: inflazione del pareggio condizionata all'equilibrio della partita.
- **Numeri**: 1X2 0.9790 (Δ −0.0007, migliore di 4 varianti); calibrazione dei
  pareggi nelle partite equilibrate 0.287→0.334 (reale 0.332): **batte il
  mercato in calibrazione** su quel sottoinsieme.
- **Perché in panchina**: CI include lo zero sul log-loss aggregato.
- **Stato particolare**: è **già attiva** nel router ufficiale market-implied
  (famiglia-pareggio, Fasi 41/44) e in `predict.py`; in panchina resta SOLO
  l'uso sul path DC standalone (senza quote).
- **Promozione se**: più stagioni; o se l'uso pratico privilegia la
  calibrazione del pareggio sul log-loss aggregato (per certi mercati è già
  la scelta giusta — vedi router).

### 5 · Nudge GG/NG di fine stagione (path DC) — Fase 48
- **Cosa**: boost stagionale dei tassi (giornate 35-38) per il GG/NG derivato
  dal DC. Vale SOLO sul path senza quote: il mercato prezza già il finale
  (Fase 50-bis).
- **Numeri**: finale −0.006 (P 89-92%), overall P 84-93%; l'effetto si sgonfia
  con più dati (boost-ospite 38ª ×1.148→×1.072 passando a 8 stagioni).
- **Perché in panchina**: nessun CI esclude lo zero; deriva del parametro.
- **Attivazione**: `market_implied.btts_season` (opt-in, off di default).

### 6 · Ensemble di emivite 180+730 — Fase 12a
- **Numeri**: −0.0006, 4/6 stagioni, "borderline".
- **Perché in panchina**: rumore; raddoppia il costo di fit per un guadagno
  non distinguibile da zero.

### 7 · Ricalibrazione per-classe 1X2 del modello — Fase 10
- **Cosa**: il bias è **robusto** (casa sovrastimata, pareggio sottostimato,
  conferma in ogni stagione), pesi fissi 0.96/1.04/1.00.
- **Numeri**: −0.0005, nel rumore.
- **Perché in panchina**: il bias è reale ma piccolo; correggerlo non paga in
  log-loss. Utile per l'uso pratico dove serve calibrazione, non ranking.

### 8 · Diagonale inflazionata (`--draw-inflation`) — Fase 12b
- **Numeri**: −0.0004 (3/6); migliora la calibrazione del pareggio.
- **Perché in panchina**: *quanti* pareggi capitano è quasi-rumore; il log-loss
  non premia. Stessa nicchia d'uso pratico della voce 7.

### 9 · Covariata congestione vera `rest_full` — Fase 4e-bis
- **Numeri**: −0.0004 medio (2020-25), inverte il segno del proxy solo-lega ma
  resta nel rumore.
- **Perché in panchina**: guadagno non distinguibile da zero.
- **Nota**: dalla Fase 59 le colonne esistono anche per Premier/Liga, dove la
  covariata **non è mai stata testata** — un test facile se si riapre il tema.

### 10 · Temperature scaling post-hoc — Fase 6
- **Numeri**: T≈0.94 (sottoconfidenza lieve, robusta), guadagno −0.0003.
- **Perché in panchina**: trascurabile. Modulo pronto
  (`src/evaluation/calibration.py`) per l'uso pratico.

### 11 · GBM + finishing-luck — Fase 33
- **Numeri**: −0.0022 (P 81%) del GBM con la covariata luck.
- **Perché in panchina**: non conclusivo E il GBM parte comunque dietro al DC
  (Fase 22): un miglioramento di un modello non attivo non è una promozione.

---

## Lead operativi (non modelli, ma misurati e in attesa)

| lead (fase) | numeri | stato |
|---|---|---|
| **Draw-bias Serie A**: puntare il pari nelle partite equilibrate (40) | ROI **+4.7%** (CI [−4.9,+14.4], P 83%, 4/6 stagioni); conferma indipendente Fase 51-ter: +3.2% (P 76%) | non concluso, alta varianza; NON si replica su Premier (−5.4%, Fase 53), mezzo-gemello in Liga (+3.6%, P 81%) |
| **Stakes-mismatch** (una squadra "decisa", l'altra in corsa) (31/32/45) | gap del modello vs mercato +0.0549 sul mismatch; ma il router stakes-aware NON lo sfrutta (soft −0.0018, P 53%) | informazione del MERCATO, non nostro errore recuperabile (Fase 45 chiude) |

---

## Archivio (voci uscite dalla panchina)

*(vuoto — le voci smentite o promosse si spostano qui con data e motivo)*
