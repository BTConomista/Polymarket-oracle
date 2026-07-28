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
3. i numeri devono essere ricalcolabili da `runs.jsonl` (regola Fase 15) o da
   un artefatto versionato dell'audit (`docs/audit_5_leghe/numeri/*.json`).

**Caselle vuote: 116** (matrice a 6 colonne = 5 leghe × fronte per-lega + il
fronte generale). Erano **134** prima dell'integrazione dell'audit a 5 leghe
(Fase 101-ter), che ne ha riempite **24** e ne ha aggiunte **6** con le sei
righe nuove (✱10). Il conteggio si ricava con
`awk '/^\| modello \| Serie A/,/^$/' docs/PANCHINA.md | grep -o "⬜" | wc -l`.

> **Nota dalla Fase 92**: le leve della famiglia-pareggio (diagonale inflazionata
> F12b, ρ dinamico F18, φ35) sono state scelte per una diagnosi poi risultata
> **invertita**: il pareggio è solo il **12%** del gap, l'88% è la discriminazione
> casa/ospite. Non è una bocciatura retroattiva — φ35 resta titolare dove misurata
> positiva — ma spiega perché i guadagni siano stati minuscoli, e dice dove NON
> cercare la prossima leva.

> Nota di metodo — l'eccezione che definisce i criteri: il **prior neopromosse
> δ** fu adottato (Fase 7) *nonostante* un CI non conclusivo, per **motivazione
> strutturale** (meccanismo chiaro, direzione confermata su ogni finestra,
> Fasi 17/19). La panchina non è quindi un "mai": è un "non finché non c'è o
> più potenza o una ragione strutturale forte".

---

## La matrice — ogni modello × ogni fronte, a colpo d'occhio

⚽ titolare · 🪑 panchina · ❌ bocciato · ⬜ mai testato · ✱ vedi nota

> **Convenzione dei segni** (esplicitata alla Fase 101-bis, ripassata cella per
> cella alla Fase 101-ter). I guadagni sono **Δ log-loss = con-la-leva −
> senza**, quindi **negativo = la leva migliora**. Di conseguenza «**CI<0**»
> significa *intervallo interamente sotto lo zero* = **miglioramento
> conclusivo**, e «**CI>0**» = **peggioramento conclusivo**. Dove si legge
> «CI<0 escluso» va inteso «non raggiunge la conclusività», non il contrario.
>
> ⚠️ **Due casi usano la convenzione opposta** e vanno tradotti quando se ne
> importano i numeri. (1) I report dell'audit a 5 leghe riportano spesso il
> *guadagno* (`senza − con`: **positivo** = la leva migliora). (2) Le metriche
> in cui «più grande» è «meglio» — **ROI** e **CLV** — hanno il segno
> rovesciato rispetto a qui; Brier, KL ed ECE invece si comportano come il
> log-loss (negativo = meglio). In questo file, quando il numero viene da una
> fonte con la convenzione opposta, sono riportati **i due log-loss**
> (senza → con) oppure il segno è dichiarato per esteso.

| modello | Serie A | Premier | La Liga | **Bundesliga** | **Ligue 1** | generale (pooled) |
|---|---|---|---|---|---|---|
| **Market-implied → matrice DC** (con quote 1X2+O/U) | ⚽ F26/41 | ⚽ F76 (13/14 vs DC, chiusura 2019-26) + F75 (apertura) | ⚽ F76 (13/14 vs DC) + F75 | ⚽ 15/15 vs DC | ⚽ 15/15 vs DC | ⚽ struttura (ρ=−0.06 unico; F76: 13/14 su TUTTE e 3 le leghe dalla chiusura, zero ritarature; F75: 17/20 dall'apertura su 2.280 partite vergini; audit GG/NG: **pareggia il prezzo del book** su 5 leghe, 6 varianti su 6 con CI a cavallo dello zero). ⚠️ audit §10: la raccomandazione «ρ=−0.06 non è ottimale» è **RITIRATA** — al θ di produzione il segno si capovolge (GG/NG da −0.00099 a **+0.00117 [+0.00057,+0.00177]**): ρ e θ sono **sostituti quasi perfetti**, il ρ ereditato è innocuo |
| **Market-implied dall'APERTURA** (1X2+O/U pre-partita) ✱10 | ⚽ F75 | ⚽ F75 | ⚽ F75 | ⚽ 25/25 vs DC (1X2 −0.0151 [−0.0215,−0.0087]) | ⚽ 25/25 vs DC (1X2 −0.0169 [−0.0229,−0.0107]) | ⚽ 17/20 vs baseline su 2.280 partite vergini (F75); audit: 5.842 partite, 24/25 vs baseline, 18/25 e 21/25 con CI conclusivo. **La chiusura resta migliore sui totali** (O/U 2.5 +0.0044 [+0.0027,+0.0061], Bonferroni-resistente); sull'1X2 il divario non raggiunge la soglia (+0.0019, p=0.055) |
| **+ router v3 (double-Poisson θ)** | ⚽ F52 (θ=1.225; riconf. F81: cs −0.0078 lfo CI<0) | ❌ F53/F81 (curva piatta, θ*≈1.05: nulla) | 🪑 **F81 RIBALTA F53**: θ≈1.2 → cs −0.0069*, 1X2 −0.0023*, GG −0.0025* (tutti lfo CI<0); la F53 testava il θ da MLE-punteggi (1.097), troppo piccolo | ❌ 0/25 mercati (θ MLE 1.080, valle −0.0012 contro −0.0081 della SA), su chiusura **e** su apertura; a θ fisso l'effetto esiste (over 2.5 −0.00076 [−0.00135,−0.00016] a θ=1.10) ma p=0.011 > Bonferroni 0.002 ✱9 | ❌ 0/25 mercati (θ 1.103, valle −0.0017); il «rovesciamento» su over 1.5 era del **selettore** (a θ fisso +0.00009, p=0.86) ✱9 | ❌ θ per-contesto (lega × epoca); lezione F81: **θ-da-mercati ≠ θ-da-punteggi**. ⚠️ audit §10: per-lega vs pooled **non deciso** (il conteggio 73-8 esce identico da leghe *rimescolate a caso*: misurava solo che il pooled ha 4× dati di selezione). E «θ decresce con la liquidità» è **falsa come covariata**: corr di rango margine↔θ **+0.10** |
| **+ φ35 famiglia-pareggio** | ⚽ F41/44 | ❌ F80 (nulla, fit sui bound) | 🪑 F80 (**CI<0 sul GG**, φ0 0.32/κ 2.9) ✱2 | ❌ nel rumore sull'1X2 (0.9744 → 0.9738); **peggiora la doppia 1X** (0.5488 → 0.5496, CI conclusivo) sia da chiusura sia da apertura | ❌ φ0 fittato = 0 in 7/7 stagioni dalla chiusura e **9/9** dall'apertura: la lega non ha deficit-pareggio; peggiora over 2.5 (0.6714 → 0.6718) e over 1.5 con CI conclusivo | ❌ costanti e segno per-lega; e **indistinguibile da una φ costante** (effetti fra 7×10⁻⁶ e 4×10⁻⁴, cioè 5-100× sotto la soglia di risoluzione) — che a sua volta non paga sul path DC ✱9 |
| **+ dp_lvl / sharpen_1x2** (affina la chiusura) | ⚽ nel tool F51/52 ✱3 | ❌ F53; audit: 0.9639 → 0.9649 (+0.0010 [−0.0001,+0.0022]), 3/7 | ❌ F53; audit: 0.9697 → 0.9687 (−0.0010 [−0.0022,+0.0003]), 5/7, non conclusivo | ❌ **PEGGIORA** la chiusura: 0.9739 → 0.9754 (+0.0016 [+0.0004,+0.0027]), 1/7; walk-forward +0.0026 [+0.0007,+0.0045]; bocciata **anche in-sample**; ROI −22,46% [−36,79%,−7,10%] | ❌ +0.0003 [−0.0009,+0.0014], 3/7; walk-forward +0.0020 [+0.0001,+0.0039] = conclusivo CONTRO; ROI −12,90% [−23,21%,−2,20%] | ❌ proprietà della chiusura SA: servono **entrambi** θ≈1.23 **e** tilt≈−0.027, ed è un'**interazione** (θ solo −0.0010, tilt solo +0.0002, insieme −0.0020). Le leghe nuove non hanno né l'uno né l'altro |
| **dp_tilt** (θ + solo tilt, senza la scala) ✱10 | 🪑 −0.0020 su **entrambi** i protocolli (7/7 e 6/6): eguaglia `dp_lvl` con un parametro in meno, ed è l'unica variante conclusiva anche in walk-forward | ❌ +0.0009 | 🪑 −0.0010 (come `dp_lvl`, non conclusivo) | ❌ +0.0012 | ❌ +0.0003 | ⬜ mai testato come costante unica |
| **Dixon-Coles + xG** (fallback senza quote) | ⚽ δ=0.23 | ⚽ δ=0.33 F57 | ⚽ δ=0.22 F57 | ⚽ δ=0.28 | ⚽ δ=0.19 | ⚽ ✱4 iperparametri comuni |
| **Simulatore di stagione → mercato CAMPIONE** (MC dal DC, F89) | ⚽ F89 | ⚽ F89 | ⚽ F89 | 🪑 log-loss 0.7392: batte l'uniforme (+2.1512) e il campione uscente (+0.7175 [+0.18,+1.73], 8/8) ma **non** «vince la rosa più cara» (+0.2359 [−0.15,+0.86]; contro la stessa baseline al suo meglio −0.0082) | ❌ log-loss 0.9132: contro «la rosa più cara» al suo meglio **−0.1682 [−0.33,−0.05], 0/8** = conclusivamente peggiore (non regge Bonferroni 0.0031; ciò che regge è il **segno**, negativo in 4 confronti su 4) | ⚽ struttura universale (spareggi e δ per-lega; +0.2299 sulla baseline forte di persistenza, IC>0, 14/24 — vantaggio concentrato in Premier). ⚠️ **F98: fragile alla specificazione della baseline** — cambiando la griglia LOO la baseline passa 1.4293→1.3816 e l'IC include lo zero. ⚠️ **audit §9**: su tutte e 40 le stagioni-lega il MC **pareggia** una baseline a **un solo parametro** p ∝ valore^β (+0.0303 [−0.16,+0.21]), e il modello «sembra bravo dove la lega è già decisa» (corr entropia↔skill vs uniforme −0.765; entropia↔guadagno vs rosa più cara +0.791, su 5 punti = direzione, non misura). Il mercato è **non testabile prospetticamente**: servirebbero ~57 stagioni-lega, 3 leghe in una stagione danno **9,8% di potenza** |
| **… → mercati POSIZIONALI (top-4 / retrocessione)** (F91) | ⚽ F91 | ⚽ F91 | ⚽ F91 | ⬜ | ⬜ | ⚽ top-4 **calibrato** (ECE 0.0140, 480 oss.; batte la persistenza +0.0274 ma l'IC a grappoli [−0.0006, +0.0522] **include lo zero** — a reggere è il test dei segni 19/24, p=0.0066, F92-bis); retrocessione ❌ **non** batte la persistenza (−0.0066 [−0.0364,+0.0208]; mis-calibrazione tutta sulle neopromosse: −6.1pp). Numeri dell'artefatto `experiments/fase91_positions.json` post-fix del prior (F92); i precedenti ECE 0.0137 / −10.1pp erano PRE-fix |
| **… + deriva di forza in-stagione** (F94) | ⚽/❌/🪑 ✱7 | ⚽/❌/🪑 ✱7 | ⚽/❌/❌ ✱7 | ⬜ | ⬜ | ⚽ **solo RETROCESSIONE** (+0.0095, IC [+0.0020,+0.0180]; neopromosse −6.1pp→−2.8pp); ❌ top-4 (peggio 17/24); campione: **nullo nel backtest, non nullo contro il mercato** ✱7 |
| **Stimatore chiusura O/U (E3)** | ⚽ tool stime | ⚽ tool stime | ⚽ tool stime | ⚽ tool stime (MAE 0.0143 regime d'uso) | ⚽ tool stime (MAE 0.0125) | ⚽ F62-bis (il pooled VINCE; il «ribaltamento a per-lega» dell'audit è un **artefatto di protocollo**: nel regime d'uso vero vince il pooled con CI conclusivo) |
| **Stimatore squad_value (ibrido A3/A2)** | ⚽ nel tool, ma **0 celle attive dalla F70** | ⚽ idem | ⚽ idem | ⬜ mai servito: `squad_value` REALE al 100% (2.754 righe) | ⬜ mai servito: reale al 100% (3.097 righe) | ⚽/⚽ F66 ✱6 (pooled per anchored, per-lega per il resto) |
| GG/NG φ35+knee34 su market-implied | 🪑 F50 (riconf. F80: −0.0014 P97%) | ❌ F80 (nulla) | ❌ combo F80 (il k34 PEGGIORA con CI>0: profilo-ospite invertito); φ35-sola 🪑 | ⬜ **misurata ma NON dimostrata**: la sola ricalibrazione-μ dà 0.6654 → 0.6648 con CI conclusivo, ma è **7 celle conclusive su 300** = quante ne dà il caso, non replica, e il giudice esterno (quote 1xBet) dà −0.00008 [−0.00092,+0.00075] su 917 partite ✱9 | ❌ ricalibrazione-μ 0.6847 → 0.6845, nel rumore | ❌ il nudge ha segno per-lega; contro le quote vere la ricalibrazione-μ è nel rumore su **tutte e 5** le leghe (nessun CI conclusivo) |
| Ricalibrazione per-classe del mercato (w_D, w_A) | 🪑 F50-ter | ❌ F53 (direzione OPPOSTA, w_D=0.93) | 🪑 F53 (il draw-bias assomiglia alla SA; ROI pari-equilibrio +3.6%, P 81%) — ⚠️ audit §5A: **w_D fittato = 0.978**, cioè < 1 come in Premier | 🪑 w_D=1.089, ma il guadagno è **negativo** (peggiora di 0.00078, nel rumore) | ❌ w_D=0.981; peggiora di 0.00076, nel rumore | ❌ segno non universale — e la tassonomia «latine/inglesi» proposta per il w_D è **RITIRATA**: col numero giusto della Liga il segno è sparso |
| Devig di Shin | 🪑 F52-ter (P 97%); audit: conclusivo a favore nel protocollo LFO del beat-close (−0.0008) | 🪑 F53 (P 68%); audit: Δ Brier +0.00002 (nulla) | 🪑 F53 (P 94%); audit: **CI conclusivo su entrambi i protocolli** del beat-close (−0.0008 LOSO, −0.0009 LFO); Δ Brier −0.00054 | 🪑 Δ Brier +0.00003 (nulla); nel rumore anche a 9 stagioni | 🪑 Δ Brier −0.00009; nel rumore | 🪑 pooled 5 leghe (12.459 partite): log-loss −0.00034 [−0.00068,+0.0000] (p=0.052), Brier −0.00021 [−0.00039,−0.00001] **ma a cluster di lega [−0.000414,−0.0000008]** = tocca lo zero; migliora 3 leghe su 5. Conclusivo solo nelle «latine» |
| **Estremizzazione della chiusura O/U** (α ≈ 1.15-1.33) ✱10 | ⬜ | ⬜ | ⬜ | 🪑 nel rumore, ma α > 1 in **tutte** le stagioni | 🪑 idem | 🪑 la chiusura O/U devigata è sistematicamente **meno estrema dei fatti**; unico candidato vivo del fronte apertura. Promozione: replica su una terza lega |
| **θ come rimedio di CALIBRAZIONE** (famiglia GG/clean-sheet) ✱10 | 🪑 bias GG −0.0292 → **+0.0049** | ⬜ (lì il router usa già θ=1 e il difetto è assente) | ⬜ | 🪑 bias GG −0.0238 → −0.0106 | 🪑 bias GG −0.0206 → −0.0049 | 🪑 raddrizza il bias in **3 leghe su 3** e regge a devig di Shin, ancoraggio coerente e θ walk-forward; una θ **leave-one-league-out** (mai vista la lega bersaglio, θ 1.09-1.17) migliora tutte e tre. **Ma** una baseline a un parametro (shift LOSO del bias) fa meglio, e l'alternativa ρ non è esclusa |
| **Inversione a ρ LIBERO** (3 parametri su 4 bersagli) ✱10 | 🪑 | 🪑 | 🪑 | 🪑 | 🪑 | 🪑 misurata sul solo GG/NG 2017-20 (5.337 partite): centra 1X2 e O/U 2.5 **esattamente** (residui 0.0000) con ρ medio **−0.0928** (sd 0.0505) e azzera quasi il bias di livello (−0.0022 [−0.0152,+0.0112]), ma in log-loss resta nel rumore (−0.00050 [−0.00165,+0.00059]). Vale come **diagnostico**: il ρ implicito del book non è −0.06 |
| **Ricalibrazione Platt del prezzo del BOOK** (GG/NG) ✱10 | ❌ | ❌ | ❌ | ❌ | ❌ | 🪑 per-lega **peggiora con CI conclusivo** (+0.00198 [+0.00064,+0.00333]: 2 stagioni di training per lega = pura varianza); pooled nel rumore (+0.00012 [−0.00037,+0.00062]), offset puro idem. Il bias di livello del book (+0,84 pt) esiste ma **non è correggibile in modo dimostrabile** |
| φ35 sul path DC standalone | 🪑 F35 | ❌ F79 (φ0→0: deficit inesistente) | ❌ F79 (fit ≈SA ma non paga) | ⬜ (l'audit ha misurato la φ **costante**, non la φ35: vedi «diagonale inflazionata») | ⬜ idem | ❌ segno non universale (PL invertita) |
| Nudge GG/NG fine stagione (path DC) | 🪑 F48 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Ensemble emivite 180+730 | 🪑 F12a | ⬜ | ⬜ | 🪑 0.99194 → 0.99144 (−0.000496 [−0.00137,+0.00037]), 4/6 | 🪑 **alta**: 1.00407 → 1.00314 (−0.000938 [−0.00177,−0.00013]), 5/6 — CI conclusivo | 🪑 **l'unico candidato vivo del path DC**: negativo in 12/12 sottoinsiemi LOSO e il meccanismo è verificato (180g e 730g **da sole** sono peggiori: il guadagno è riduzione di varianza). Ma p=0.019 contro Bonferroni 0.00625 su 8 test, e non replica in Bundesliga. Il test che decide: pooled 5 leghe (~10.000 partite), **pre-registrato** |
| Ricalibrazione per-classe del modello | 🪑 F10 | ⬜ | ⬜ | ❌ 0.99194 → 0.99474 (+0.0028 [−0.0001,+0.0057]), 1/6 | ❌ **conclusivo CONTRO**: 1.00407 → 1.00627 (+0.0022 [+0.00036,+0.00402]), 1/6 | ⬜ mai misurata pooled — ma la causa della bocciatura è generale: il bias per classe **non è stabile nel tempo dentro la stessa lega** (oscilla di ±0.03 stagione su stagione, quanto la sua incertezza campionaria) |
| Diagonale inflazionata (`--draw-inflation`, φ costante) | 🪑 F12b | ⬜ | ⬜ | ❌ 0.99194 → 0.99262 (+0.00069 [−0.00018,+0.00154]), 2/6 | ❌ 1.00407 → 1.00402 (−0.000056 [−0.0012,+0.0011]), 2/6: nullo | ❌ era «la leva a più alta probabilità a priori» del path DC (§3 dell'audit la dava promettente): **non paga in nessuna delle due leghe nuove** |
| Covariata `rest_full` (congestione vera) | 🪑 F4e-bis | ❌ F79 (+0.0005, P 9%) | ❌ F79 (β instabile) | ❌ +0.000796 [−0.0002,+0.0018], 2/6 | ❌ +0.000371 [−0.0003,+0.0010], 1/6 | ❌ **rumore su 5/5 leghe** |
| Temperature scaling post-hoc | 🪑 F6 (T≈0.94) | ⬜ | ⬜ | 🪑 −0.000236 [−0.00163,+0.00116], 5/6 (nel rumore) | ❌ +0.00037 [−0.00072,+0.00144], 2/6 (peggiora) | ⬜ mai misurato pooled; ⚠️ col test del rapporto di verosimiglianza **nessuna T è distinguibile da 1** tranne La Liga (0.890, p=0.018), che non supera Bonferroni su 5 leghe |
| Covariata `midweek_europe` (dummy congestione) | 🪑 F36-bis | ❌ F79 (β alterno) | ❌ F79 (β segno opposto a SA) | ❌ −0.000393 [−0.0016,+0.0009], 3/6; col dato di coppa **corretto** −0.000345, e il confronto diretto bucato-vs-corretto è +0.000048 [−0.00074,+0.00083] | ❌ +0.000321 [−0.0005,+0.0012], 2/6; col dato corretto +0.000227 | ❌ il β stabile SA non si replica — e **misurare bene la congestione non la fa funzionare**: il difetto del dato non era la ragione ✱9 |
| Temperatura sopra dp_lvl (T=1.056) | 🪑 F52-ter | ❌ (dp_lvl bocciato lì) | ❌ | ❌ (dp_lvl bocciato lì con CI conclusivo) | ❌ (idem) | ❌ |
| GBM (diretto, per mercato, bespoke) | ❌ F21-23/50-quater | ⬜ ✱5 | ⬜ ✱5 | ⬜ ✱5 | ⬜ ✱5 | ❌ tetto informativo |
| Poisson bivariato (λ3) | ❌ F42 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Copula di Frank | ❌ F43/50 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| GAS / score-driven (state-space) | ❌ F52-sexies | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Binomiale negativa · zero-inflazione · Rue-Salvesen | ❌ F27/51 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| ρ dinamico per-partita | ❌ F18 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Power-devig / denoising cross-stagione | ❌ F38/50 | ⬜ | ⬜ | ❌ PEGGIORA a 7 e a 9 stagioni (+0.00035 [+0.00004,+0.00066], CI conclusivo) | ❌ nel rumore | 🪑 **come devig alternativo** (da non confondere col denoising): pooled 5 leghe −0.00042 [−0.0011,+0.0002], nel rumore, e Shin−power +0.00009 [−0.0004,+0.0006] |
| Covariata stakes + router stakes-aware | ❌ F32/36/45 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Vantaggio-casa per-squadra | ❌ F8 (r≈0.00) | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Covariate nel canale-pareggio | ❌ F37 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Ricalibrazione O/U del mercato | ❌ F51-quater | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Ensemble standalone (DC+biv+GBM) | ❌ F46 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Blend modello+mercato (lineare α / GBM) | ❌ F16 (α*≈0) / F23 | ⬜ | ⬜ | ⬜ | ⬜ | ❌ **replicato su un mercato nuovo e 5 leghe**: sul GG/NG (1xBet 2017-20) il prezzo del book ingloba il DC — α\* = 0.060, con α\* = 0 nel **70%** dei fit; col market-implied α\*=0.717 ma il guadagno è nullo (è lo stesso oggetto letto due volte) |
| Profilo stagionale dinamico (γ/λ,μ nel tempo) | ❌ F47/48 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Tiri in porta grezzi nel blend | ❌ F3 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Covariate squad_value/absence/npxG/forma/luck/ppda/deep | ❌ F4c/11/13/33 | ⬜ | ⬜ | ❌ `squad_value` +0.000873 (**0/6 stagioni**, e dalla 6ª giornata peggiora con CI conclusivo +0.0012 [+0.00034,+0.00207]); `absence` +0.000252 | ❌ `squad_value` +0.000799; `absence` +0.000313 | ❌ **la stabilità del segno di un β non è evidenza di valore predittivo**: `squad_value` ha il β più grande e più stabile mai visto (6/6 in entrambe le leghe, +0.056 e +0.095) e non guadagna nulla |
| **Modello di conteggio corner/cartellini** (fuori matrice, F96) | ⚽ F96 | ⚽ F96 | ⚽ F96 | ⬜ | ⬜ | ⚽ struttura unica (attacco/difesa moltiplicativi, vincolo `hadv+aadv=2`); processo DIVERSO dai gol, non ridondante |
| **… + binomiale negativa sui conteggi** (F98) | ⚽/❌ ✱8 | ⚽ F98 | ⚽ F98 | ⬜ | ⬜ | 🪑 conclusiva ma trascurabile (corner +0.00103 [+0.00062,+0.00143], cartellini +0.00088 [+0.00033,+0.00142]) |
| **… + correzione di LIVELLO train-only** (F98 lead → **F99 bocciato**) | ❌ F99 | ❌ F99 | ❌ F99 | ⬜ | ⬜ | ❌ **F99: il lead era falso.** 5 stimatori walk-forward + emivita alla radice: nessuno migliora, 5/8 celle peggiorano con IC conclusivo. Causa: **il bias di fold NON persiste** (corr lag-1 +0.23/+0.19, IC attraversa lo zero, **10/18 stesso segno**; sd del bias 2,6×/10× il bias pooled) → non era deriva, era rumore aggregato |
| **Mercati Tier 3 dal ri-scalamento 1T/2T** (Halftime, Second Half, risultato esatto — F98) | ⚽ F98 | ⚽ F98 | ⚽ F98 | ⬜ mai misurato lì (audit §14 p.7) | ⬜ idem | ⚽ fondazione misurata (f=0.4396 [0.4338,0.4458], 1T Poisson-compatibile, tempi quasi indipendenti); batte la baseline con IC conclusivo (HT +0.0537, 2T +0.0578, esatto +0.1940). ⚠️ **il 2T è mal calibrato** (pareggio 0.3671 vs 0.3427) mentre il 1T no → game-state, non normalizzazione |
| Arbitro come feature moltiplicativa (cartellini) | ⬜ dato assente (0/3420) | ❌ F98 (nessun IC esclude lo zero; **85% del guadagno era solo livello**) | ⬜ dato assente (0/3420) | ⬜ (dato mai estratto) | ⬜ (dato mai estratto) | ❌ il dato `Referee` non è in nessuno dei 5 snapshot: esiste solo nei grezzi Premier |
| Proxy storico delle formazioni (undici attesi, disponibilità del nucleo) | ❌ F98 | ❌ F98 | ❌ F98 | ⬜ | ⬜ | ❌ la parte che funziona correla +0.9603 col valore rosa (già bocciato F4c/11); la disponibilità correla −0.1227 col logit della chiusura = **il mercato le assenze le prezza già** |
| Anticipo del movimento apertura→chiusura | ❌ F98 (β −0.0039, R² 0.0001; CLV −0.0022, IC interamente **sotto** zero — qui la metrica è il CLV, non il Δ log-loss: sotto zero = si **perde** valore) | ❌ F98 | ❌ F98 | ❌ estrapolare il β del movimento sui totali (1.75): β LOSO e walk-forward entrambi nel rumore, 4/7 stagioni, sensibile al devig, ROI −3,95% | ❌ idem (β 1.90; ROI +0,91% con CI larghissimo) | ❌ non anticipabile; il movimento vale 15,6% del gap anche se lo si prendesse tutto. **Rumore selezionato, non edge** |

Note della matrice:
- **✱1** ~~mai backtestato multi-mercato su Premier/Liga~~ → **FATTO (F76)**:
  batte il DC-da-gol su **13/14 mercati dalla chiusura** su tutte e 3 le leghe
  (2019-26), **senza ritarare ρ** — la struttura è davvero universale (solo gli
  input, le quote, sono per-lega). La φ35 resta da testare per-lega (✱2); il θ
  del router NON si trasferisce (F75: per-contesto, lega × epoca).
- **✱2** Il draw-bias non si replica in Premier (F53) e le F79/F80 hanno
  chiuso il cerchio su ENTRAMBI i path: **φ0 fitta ZERO in Premier** sul path
  DC (F79) e resta instabile/inefficace sui tassi di mercato (F80) — il
  deficit-pareggio non esiste lì. In **Liga** invece la φ35 di mercato ha il
  **primo CI<0 per-lega del progetto** (GG −0.0006 [−0.0011,−0.0001], P 99%,
  φ0≈0.32 κ≈2.9 stabili, F80): in panchina alta, si promuove quando riappare
  su stagioni nuove. *(La seconda condizione — «quando `predict.py` diventa
  per-lega» — è **soddisfatta** dalla Fase 92-bis: `src.config.MARKET_ENGINE`.
  Resta quindi la sola conferma su stagioni nuove. Allineato dalla Fase 101.)* Il k34 in Liga
  PEGGIORA con CI>0 (profilo-ospite di fine stagione invertito, ×0.915).
  ⚠️ **Ridimensionamento (audit a 5 leghe, report 6 passo 5).** Sul percorso
  market-implied con finestra 6 stagioni (2020-26) e φ0 leave-one-season-out,
  la φ35 **non è conclusiva in nessuna delle 5 leghe, Serie A compresa**
  (1X2 0.9642 → 0.9628; IC95 sul *guadagno* [−0.0010, +0.0038]), pur con φ0
  che si fitta stabilmente fra 0.235 e 0.370. Non è una smentita della F80
  (percorso, mercato bersaglio e finestra diversi): è la constatazione che con
  ~2.000 partite per lega un guadagno atteso di 1-1,5 millesimi è **sotto la
  soglia di risoluzione**. Chi vuole promuoverla deve allargare la finestra o
  cambiare metrica, non ri-fittare gli stessi dati.
- **✱3** dp_lvl è nel tool `predict.py` SOLO per la Serie A; è "valore da
  oracolo" (log-loss), NON da scommessa (F51-ter: niente ROI). L'audit a 5
  leghe lo conferma per via economica: perfino in Serie A, dove il vantaggio in
  log-loss è reale e conclusivo, il ROI è **+0,75% [−6,86%, +8,61%]** =
  indistinguibile da zero.
- **✱4** F57: la ri-taratura per lega è PIATTA su emivita/shrinkage/α → gli
  iperparametri del DC sono di fatto GENERALI; solo δ è per-lega. È il primo
  esempio documentato di "versione generale" che regge. Confermato a **5 leghe
  su 5** (audit, report 6 passo 3: nessuna delle tre leve dà un CI conclusivo;
  l'emivita 730g peggiora ovunque). Il tracer cross-lega dello stesso report
  misura il gap 1X2 del DC contro il mercato su 6 stagioni (2020-26):
  SA +0.0165, Premier +0.0207, Liga +0.0162, Bundesliga +0.0181
  [+0.0109,+0.0253], Ligue 1 +0.0190 [+0.0121,+0.0258]. ⚠️ il valore Serie A di
  quella tabella è il **+0.0165 PRE-fix del prior (Fase 92)**; lo stato
  ufficiale del progetto al codice di HEAD è **+0.0167** (log-loss 0.9799
  contro 0.9632 del mercato). Le altre quattro leghe non sono state rimisurate
  dopo il fix: vanno lette sulla stessa scala del +0.0165.
- **✱5** Il GBM non è mai stato rifatto fuori dalla Serie A, ma il tetto
  informativo è universale (F57, e ora 5 leghe su 5): riaprirlo richiederebbe
  una ragione nuova.
- **✱6** Caso istruttivo per il principio 9: per lo stimatore squad_value il
  fronte VINCENTE dipende dal regime — con l'ancora adiacente vince il pooled
  (17% vs 17.8%), senza ancore vince il per-lega (28.5% vs 31.4%, leave-team-out
  F66). Nessun fronte domina: si misura caso per caso. *(Dalla Fase 70 lo
  stimatore non ha celle attive: il `squad_value` è dato REALE al 100% su tutte
  e 5 le leghe — il metodo resta pronto se il buco si riaprisse.)*
- **✱7 (Fase 94, corretta dalla Fase 95-bis)** — la deriva di forza in-stagione
  (σ 0.30 neopromosse / 0.16 resto, misurata su 480 squadre-stagione) è
  adottata **solo sul mercato retrocessione**: è l'unico con IC che esclude lo
  zero (+0.0095 [+0.0020,+0.0180]). Sul **top-4 PEGGIORA** (17 stagioni su 24,
  ECE 0.0140→0.0203) per una ragione istruttiva: quel mercato era **già
  calibrato**, e aggiungere incertezza a una previsione giusta può solo
  peggiorarla.
  ~~Sul campione non ha effetto.~~ **AFFERMAZIONE SUPERATA dalla Fase 95-bis.**
  Nel backtest il campione era «nullo» (+0.0017, meglio in 9 stagioni su 24) ma
  quel test ha **24 osservazioni**: una per lega-stagione, il campione più
  povero del progetto. Giudicata dai prezzi Polymarket sul campione 2026-27 —
  che confrontano **20 probabilità per lega** invece di un solo esito
  realizzato — la deriva ha eccome un effetto, **e il segno dipende da quanto
  eravamo già allineati**:

  | lega | KL base | KL +deriva | Δ | esito |
  |---|--:|--:|--:|---|
  | Serie A | 0.1805 | **0.1445** | **−0.0360** | avvicina |
  | Premier | 0.2418 | **0.2036** | **−0.0382** | avvicina |
  | La Liga | 0.0560 | 0.0740 | +0.0179 | allontana |

  (MAE e correlazione migliorano dove la KL scende: SA 0.0252→0.0218, corr
  0.956→0.963; PL 0.0265→0.0224, corr 0.948→0.955.) È **la stessa legge del
  top-4 su un metro indipendente**: la Liga era già la lega più allineata al
  mercato (KL 0.056, un terzo delle altre) e la deriva la peggiora; Serie A e
  Premier erano sovra-confidenti e la deriva le corregge. *L'incertezza
  aggiunta paga solo dove manca davvero.* Per questo la cella del campione è
  ora **⚽/❌/🪑** (retrocessione / top-4 / campione): sul campione la leva è in
  **panchina**, non «senza effetto». Onestà: «più vicino al mercato» non è «più
  corretto», e questo è un diagnostico su dati LIVE senza run in `runs.jsonl`.
- **✱8** La NB sui conteggi è **per-lega di fatto**: i gialli di Serie A sono
  **sotto-dispersi** (var/μ condizionata 0.901) e lì la stima di `r` collassa da
  sola sulla Poisson (Δ esattamente 0.00000) — la forma NB è auto-protettiva, non
  dannosa. In 3 celle su 21 però PEGGIORA con IC conclusivo, e la causa è
  identificata: dove la media walk-forward è storta per **deriva di livello**,
  allargare la distribuzione sposta massa dal lato sbagliato. La promozione piena era
  condizionata alla correzione di livello: la **Fase 99 l'ha bocciata** (il bias
  non persiste fra i fold), quindi quelle 3 celle restano tali e il guadagno
  della NB è **invariante** alla correzione (+0.00103→+0.00106 corner,
  +0.00088→+0.00067 cartellini). La NB resta titolare per forma, non per centro.
- **✱9 — che cosa vale davvero, dell'audit a 5 leghe.** I numeri delle celle
  Bundesliga/Ligue 1 vengono da `docs/audit_5_leghe/` (report 6, 10 e 11) e dai
  JSON in `docs/audit_5_leghe/numeri/`. Vanno letti con tre avvertenze scritte
  dall'audit stesso: (a) con ~2.100-2.300 partite per lega la **soglia di
  risoluzione** del bootstrap è 1-2 millesimi di log-loss — sotto quella soglia
  «non dimostrato» non è «dimostrato nullo»; (b) diversi «CI conclusivi» delle
  bocciature **non sopravvivono alla molteplicità** (φ p=0.0054 su 10 test;
  router, 4 mercati con p ≥ 0.002 su 50); (c) la lezione trasversale, valida
  ovunque: **ogni statistica di testa deve avere il suo intervallo, e ogni
  «non c'è effetto» la sua misura di potenza** (in 5 casi su 7 il difetto non
  era il numero ma la statistica scelta per raccontarlo).
- **✱10 — righe nuove alla Fase 101-ter.** Sei leve erano state misurate
  dall'audit senza avere una riga in questa matrice: market-implied
  dall'**apertura**, **dp_tilt**, **estremizzazione della chiusura O/U**, la
  **θ come rimedio di calibrazione**, l'**inversione a ρ libero** e la
  **ricalibrazione Platt del prezzo del book**. Sono qui perché la regola del
  file è che una leva misurata ha una riga, anche quando l'esito è negativo.

> ⚠️ **COM-Poisson: fuori dalla matrice dalla Fase 101, e non è una svista.**
> Non è una famiglia alternativa alla double-Poisson: `dp(θ) ≡ COM-Poisson(ν=θ)`
> mean-matched, cioè la **stessa** distribuzione riparametrizzata
> (`_dp_pmf` è `q_k ∝ a^k/(k!)^θ` rinormalizzata). Non poteva quindi avere una
> riga propria né valere come «conferma indipendente» della dp. Il verdetto e i
> numeri restano, nella tabella dei bocciati.

---

## ⚽ I titolari (in config ufficiale o nei tool) — a 5 leghe

| modello | dove è attivo | fronte per-lega | fronte generale |
|---|---|---|---|
| **Market-implied + router v3 + φ35** | pricing con quote 1X2+O/U (`price_markets(dp_theta)`, `predict.py`) | costanti Serie A (θ=1.225/1.138, φ0=0.30, κ=1.5, `sharpen_1x2`); le **altre quattro leghe escono col motore LISCIO**, dichiarato in `src.config.MARKET_ENGINE` (F92-bis per Premier/Liga, F101 per Bundesliga/Ligue 1 — lì lo stato è **MISURATO**, non prudenziale: router θ negativo su **0/25 mercati** in entrambe, φ35 e power-devig bocciati, beat-the-close chiuso) | struttura universale; ρ=−0.06 unico (e l'audit lo conferma innocuo: ρ e θ sono sostituti) |
| **Market-implied dall'APERTURA** | stesso motore, alimentato dalle quote pre-partita quando la chiusura non c'è (`predict.py --odds`) | nessuna costante per-lega: l'inversione non ha parametri fittati | ⚽ 5 leghe: 25/25 mercati contro il DC su Bundesliga e Ligue 1 (5.842 partite), 17/20 contro la baseline su 2.280 partite vergini 2017-19 (F75). **Regola d'uso: con la chiusura O/U disponibile si usa la chiusura**, conclusivamente migliore sui totali |
| **Dixon-Coles + blend xG** | fallback senza quote; `backtest.py` | `LEAGUE_CONFIGS`: δ **0.23** Serie A / **0.33** Premier / **0.22** La Liga / **0.28** Bundesliga / **0.19** Ligue 1 (5 leghe, F100); il resto è comune (F57, curve piatte 5/5) | iperparametri comuni = versione generale di fatto. ⚠️ il δ per-lega è adottato per **motivazione strutturale**: il guadagno misurato è nel rumore in tutte le leghe (+0.0001 Bundesliga, +0.0000 Ligue 1), e in Ligue 1 va nella direzione **opposta** alle altre (promosse meno deboli del campione) |
| **sharpen_1x2 (dp_lvl)** | `predict.py`, solo Serie A | SA only | bocciato fuori SA: F53 (Premier, Liga) e audit a 5 leghe (Bundesliga +0.0016 [+0.0004,+0.0027] conclusivo CONTRO; Ligue 1 conclusivo contro in walk-forward) |
| **Stimatore E3 chiusura O/U** | `scripts/build_estimates.py` → `data/estimates/` | (per-lega TESTATO e battuto dal pooled) | **pooled: 5 coefficienti unici, MAE 0.0117** in interpolazione, ~0.014 nel regime d'uso (0.0143 Bundesliga, 0.0125 Ligue 1) |
| **Stimatore squad_value (ibrido)** | `scripts/build_estimates.py` → `data/estimates/` | A2 per-lega per squadre senza stagioni note (err ~29%) | A3 pooled dove c'è l'ancora adiacente (err ~17%). ⚠️ **0 celle attive dalla Fase 70**: il `squad_value` è dato REALE al 100% su tutte e 5 le leghe (16.111 partite), il file CSV è a 0 righe. Il metodo resta pronto se il buco si riaprisse |
| **Baseline frequenze H/D/A** | benchmark in ogni backtest | per-lega per costruzione | — |
| **Simulatore di stagione (mercato campione)** | `season_sim.py`, `_run_fase89_season_champion.py` | spareggi per-lega a **5 leghe**: h2h prima in SA/Liga, DR in Premier, `('gd','gf','h2h')` in Bundesliga e `('gd','h2h','gf')` in Ligue 1 (F100, verificati su DFL *Spielordnung* §2 c.3 e LFP art. 518 TER; test che li distinguono dalla F101) + δ da `LEAGUE_CONFIGS` | struttura unica; **sovra-confidente** (60.1% dichiarato vs 41.7% realizzato): correzione strutturale da fare. ⚠️ su Bundesliga e Ligue 1 il simulatore **funziona ma non aggiunge valore** rispetto a «vince la rosa più cara» (§9 dell'audit): titolare solo dove la lega non è già decisa |

---

## 🪑 La panchina (migliorativi misurati, non attivati)

| # | leva (fase) | Δ nominale | perché in panchina | attivazione |
|---|---|---|---|---|
| 1 | GG/NG: φ35+knee34 sul market-implied (50) | **−0.0010** GG (P 98%); riconf. F80 −0.0014 (P 97%) | CI al limite + multiple testing | opt-in engine |
| 1-bis | **GG/NG Liga: φ35 sola sul market-implied (80/81)** | **−0.0006 CI<0 (fit MLE, F80)**; con costanti da griglia (φ0 0.7, κ 0.5) **lfo −0.0019 CI<0 (F81)** | primo test su quella lega (prudenza F17); ~~tool non ancora per-lega~~ (il tool **è** per-lega dalla F92-bis) | φ per la Liga in `price_markets` (griglia > MLE, come per θ) |
| 1-ter | **Router θ per la Liga (81)** | **θ≈1.2: cs −0.0069*, 1X2 −0.0023*, GG −0.0025* (lfo CI<0)**; F82: raddrizza anche la CALIBRAZIONE (GG bias −0.036→−0.008, ECE 0.036→0.012 — metrica indipendente) | ribalta F53 (che usava il θ MLE 1.097); primo giro di conferme. ~~tool non per-lega~~: il tool **è** per-lega dalla F92-bis, quindi la promozione richiede solo la conferma su stagioni nuove | `price_markets(dp_theta≈1.2)` per la Liga |
| 2 | Ricalibrazione per-classe del MERCATO (50-ter) | −0.0006 pooled (P 78%) | servono ~20 stagioni; **Premier smentisce il segno** (F53) e l'audit toglie la spiegazione «latine/inglesi» | `market_denoise` |
| 3 | Devig di Shin (52-ter) | −0.0007 1X2 (P 97%); pooled 5 leghe −0.00034 (p=0.052) | non concluso; il CI sul Brier **non regge a cluster di lega**; toccherebbe la fonte unica | funzione pronta |
| 4 | φ(λ−μ) sul path DC standalone (35) | −0.0007 1X2 | CI include 0 | `--draw-balance` |
| 5 | Nudge GG/NG di fine stagione, path DC (48) | −0.006 finale (P 89-92%) | nessun CI esclude 0; si sgonfia con più dati | `btts_season` opt-in |
| 6 | Ensemble di emivite 180+730 (12a) | −0.0006 (4/6) in SA; **−0.000938 CI<0 in Ligue 1** (audit) | borderline in SA; in Ligue 1 conclusivo ma p=0.019 > Bonferroni, e non replica in Bundesliga | ri-run con 2 fit; il test che decide è il pooled 5 leghe pre-registrato |
| 7 | Ricalibrazione per-classe 1X2 del MODELLO (10) | −0.0005 | rumore (bias però robusto) | pesi fissi 0.96/1.04/1.00 |
| 8 | Diagonale inflazionata (12b) | −0.0004 (3/6) | rumore; calibra il pari ma non paga in LL; e sul path DC delle leghe nuove non paga affatto | `--draw-inflation` |
| 9 | Covariata congestione vera `rest_full` (4e-bis) | −0.0004 | rumore — e ora rumore su **5 leghe su 5** | `--covariates rest_full` |
| 10 | Temperature scaling post-hoc (6) | −0.0003 | trascurabile (T≈0.94 robusto); nessuna T è distinguibile da 1 al test del rapporto di verosimiglianza | `scripts/calibrate.py` |
| 11 | GBM + finishing-luck (33) | −0.0022 (P 81%) | non conclusivo, e il GBM di suo perde dal DC | — |
| 12 | Covariata `midweek_europe` (36-bis) | −0.0003, ma β=−0.020 **stabile 6/6** | CI include 0; ridondante con rest_full insieme; **F79: il β stabile NON si replica** (PL alterno, Liga +0.008 opposto); e col dato di coppa corretto (audit) non cambia nulla | `--covariates midweek` |
| 13 | Temperatura sopra dp_lvl (52-ter) | 0.9609→**0.9605** (T=1.056) | si somma a una leva già Serie-A-only e da oracolo | sopra `sharpen_1x2` |
| 14 | **Estremizzazione della chiusura O/U** (α ≈ 1.15-1.33 — audit §8.2) | nel rumore in Bundesliga e Ligue 1, ma **α > 1 in tutte le stagioni** | una sola coppia di leghe; è l'unico candidato vivo del fronte apertura | da implementare: nessuna funzione dedicata in `src/` (l'estremizzazione vive solo negli script dell'audit) |
| 15 | **θ come rimedio di CALIBRAZIONE** (famiglia GG/clean-sheet — audit §11) | bias GG **−0.0238 → −0.0106** (BL), −0.0206 → −0.0049 (L1), −0.0292 → **+0.0049** (SA) | il guadagno in **log-loss** è minuscolo (0.6847 → 0.6842): è un argomento che il log-loss non sa vedere. E una baseline a **un** parametro fa meglio | `price_markets(dp_theta)` acceso per la sola famiglia GG/clean-sheet |
| 16 | **dp_tilt** — θ + solo tilt, senza la scala (audit §7.3) | Serie A **−0.0020** su entrambi i protocolli (7/7 e 6/6) | eguaglia `dp_lvl` con **un parametro in meno** ed è l'unica variante conclusiva anche in walk-forward — ma è **una sola lega** | sostituire i due livelli con un solo tilt in `sharpen_1x2` |
| 17 | **Inversione a ρ LIBERO** (3 parametri — report 11 C7) | centra 1X2 e O/U 2.5 **esattamente** (residui 0.0000), ρ medio −0.0928 (sd 0.0505); bias di livello GG −0.0022 [−0.0152,+0.0112] | in **log-loss** è nel rumore (−0.00050 [−0.00165,+0.00059]): vale come diagnostico, non come guadagno | terzo parametro in `implied_lambda_mu` |
| 18 | **GG/NG dalla scaletta completa del book** (report 11 §8) | 0.6833 vs 0.6840 del book (−0.00067 [−0.00182,+0.00048]); MAE dal book 0.0159 contro 0.0186 | segno favorevole 3/3 blocchi, mai conclusivo | invertire più linee O/U invece della sola 2.5 |

### Dettaglio delle voci di panchina

#### 1 · GG/NG: φ35 + ricalibrazione-μ (knee34) sul market-implied — Fase 50
- **Cosa**: la miglior stima GG/NG del progetto: market-implied → ricalibrazione
  dei tassi walk-forward → φ(|λ−μ|). GG **0.6810** vs 0.6820 del motore liscio.
- **Numeri**: Δ −0.0010, CI [−0.0020,−0.0000], P 98%, 5/7 stagioni; guadagno
  concentrato nell'era porte-chiuse 2019-22, ≈neutro nelle ultime 4 stagioni.
- **Perché in panchina**: CI che tocca lo zero dopo ~50 fasi di test sulla
  stessa finestra (disciplina multiple-testing, Fase 17); deriva temporale del
  guadagno sospetta.
- **Fronti (aggiornato F80)**: la condizione "riappare su Premier/Liga" è
  stata TESTATA — esito misto e istruttivo: la combo NON trasferisce (PL
  nulla; in Liga il k34 peggiora con CI>0, profilo-ospite invertito ×0.915),
  ma la **φ35 da sola in Liga dà il primo CI<0 per-lega del progetto**
  (voce 1-bis). In Serie A la combo si riconferma sulla finestra pulita
  1920-2526 (−0.0014, P 97%). **Promozione se**: il guadagno riappare su
  stagioni NUOVE (2026-27+).
- **Fronti (aggiornato dall'audit a 5 leghe)**: la sola **ricalibrazione-μ** era
  l'unica cella conclusiva positiva del primo giro sulle leghe nuove
  (Bundesliga 0.6654 → 0.6648, CI conclusivo). È stata **declassata a ⬜ non
  dimostrata**: vive in un blocco di 300 celle che ne produce 7 conclusive
  positive (esattamente quante ne dà il caso a α=0.05), **non replica** — in
  La Liga la stessa leva *peggiora* con CI conclusivo, in Premier p=0.58 e in
  Ligue 1 p=0.36 — la variante contigua (ricalibrare λ *e* μ) è nel rumore
  (+0.00078 [−0.00007,+0.00165]: un verdetto che si ribalta cambiando un
  dettaglio non è un verdetto), e il **giudice esterno** — le quote GG/NG di
  1xBet, report 11 — dà **−0.00008 [−0.00092,+0.00075]** su 917 partite. Non è
  una smentita (finestra e n diversi): è una **mancata conferma**.

#### 2 · Ricalibrazione per-classe del MERCATO (w_D≈1.09, w_A≈1.06) — Fase 50-ter
- **Cosa**: correggere la chiusura stessa per il draw-bias noto (pari e
  trasferta sottoprezzati in Serie A).
- **Numeri**: pooled Δ −0.0006, CI [−0.0020,+0.0009], P 78%, ma **5/6 stagioni
  migliorano** e i pesi sono stabili anno su anno.
- **Perché in panchina**: "la crepa più credibile sulla chiusura, non conclusa
  — servono ~20 stagioni per il verdetto" (diario).
- **Fronti**: il segno NON è universale — su Premier i pareggi sono
  SOVRA-prezzati (w_D=0.93, Fase 53). ~~Sulla Liga il bias somiglia alla Serie
  A.~~ ⚠️ **corretto dall'audit (§5A)**: il run dà **w_D = 0.978** per la Liga,
  cioè < 1 come in Premier. Con i cinque numeri giusti (SA > 1, Liga 0.978,
  Bundesliga 1.089, Premier < 1, Ligue 1 0.981) la tassonomia «latine /
  inglesi» **non esiste**: il segno è sparso, e l'archiviazione originale del
  progetto («segno non universale») era quella corretta. Sulle due leghe nuove
  la leva **peggiora** di poco (+0.00078 e +0.00076, nel rumore), e portata sul
  path DC peggiora in Ligue 1 **con CI conclusivo**. Il motivo misurato: il
  bias per classe non è stabile **nemmeno nel tempo dentro la stessa lega**
  (oscilla di ±0.03 stagione su stagione, quanto la sua incertezza
  campionaria). Una "versione generale" resta **bocciata in partenza**.
  **Promozione se**: più stagioni per lega o un meccanismo che spieghi il segno.

#### 3 · Devig di Shin al posto del moltiplicativo — Fase 52-ter
- **Cosa**: rimozione del margine che modella gli scommettitori informati
  (corregge il favourite-longshot bias); |shin−molt| medio 0.0047.
- **Numeri**: 1X2 0.9617 vs 0.9625 (Δ −0.0007, P 97%) in Serie A; direzione
  confermata su Premier (P 68%) e Liga (P 94%) — Fase 53.
- **Numeri a 5 leghe (audit §4, 12.459 partite)**: log-loss 1X2 −0.00034
  [−0.00068, +0.0000], p = 0.052; Brier −0.00021 [−0.00039, −0.00001], che
  però **a cluster di lega diventa [−0.000414, −0.0000008]**, cioè tocca lo
  zero. Migliorano solo 3 leghe su 5 (Serie A −0.00038, La Liga −0.00054,
  Ligue 1 −0.00009; Premier +0.00002, Bundesliga +0.00003). Nel lavoro sul
  beat-the-close Shin batte il moltiplicativo **con CI conclusivo in La Liga**
  (−0.0008 LOSO, −0.0009 LFO) e in Serie A LFO (−0.0008): la partizione è
  ancora quella delle «latine». Il parametro z passa da ~0.0128 nel 2017-19 a
  ~0.0245 dal 2019-20, coerente col margine che raddoppia.
- **Perché in panchina**: P alto ma non concluso (multiple testing); il pooled
  non regge a un bootstrap che rispetti la struttura dei dati; e il devig
  moltiplicativo è la **fonte unica** di tutto il progetto (`metrics.devig_*`):
  cambiarla ricalcolerebbe ogni benchmark storico — costo di coerenza alto per
  −0.0007.
- **Fronti**: resta il miglior candidato a promozione sul fronte GENERALE (la
  direzione è confermata su 5/5 leghe, la conclusività no). **Promozione se**:
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
- **Fronti (aggiornato F79)**: TESTATA su Premier/Liga e **bocciata su
  entrambe** — Premier φ0→0 (deficit inesistente, il modello sovra-stima già
  i pareggi equilibrati inglesi), Liga fit ≈SA (φ0 0.39, κ 4.1) ma
  sovra-corregge e non paga (+0.0002). Resta in panchina SOLO per la Serie A.
  Su Bundesliga e Ligue 1 la **φ35 non è mai stata provata sul path DC**:
  l'audit ha misurato lì la φ **costante** (voce 8), che non paga.

#### 5 · Nudge GG/NG di fine stagione (path DC) — Fase 48
- **Cosa**: boost stagionale dei tassi (giornate 35-38) per il GG/NG derivato
  dal DC. Vale SOLO sul path senza quote: il mercato prezza già il finale
  (Fase 50-bis).
- **Numeri**: finale −0.006 (P 89-92%), overall P 84-93%; l'effetto si sgonfia
  con più dati (boost-ospite 38ª ×1.148→×1.072 passando a 8 stagioni).
- **Perché in panchina**: nessun CI esclude lo zero; deriva del parametro.
- **Attivazione**: `market_implied.btts_season` (opt-in, off di default).

#### 6 · Ensemble di emivite 180+730 — Fase 12a
- **Numeri (Serie A)**: −0.0006, 4/6 stagioni, "borderline".
- **Numeri a 5 leghe (audit §12)**: Bundesliga 0.99194 → 0.99144 (−0.000496
  [−0.00137, +0.00037], 4/6); **Ligue 1 1.00407 → 1.00314 (−0.000938
  [−0.00177, −0.00013], 5/6, CI conclusivo)**. È **l'unica leva positiva del
  path DC** su quel blocco: negativa (cioè migliorativa) in **12/12**
  sottoinsiemi leave-one-season-out, e il meccanismo è verificato — 180g e 730g
  **prese da sole sono entrambe peggiori** della base in entrambe le leghe, il
  guadagno viene dalla media, cioè da riduzione di varianza, non da un'emivita
  migliore.
- **Perché in panchina**: rumore in Serie A; raddoppia il costo di fit. E in
  Ligue 1 il p = 0.019 non supera la soglia di Bonferroni sugli 8 test
  pre-dichiarati (0.00625), **e non replica in Bundesliga**.
- **Promozione se**: pooled a 5 leghe (~10.000 partite, 24 dei 60 walk-forward
  già su disco), **pre-registrato prima** — altrimenti si ricade nella
  molteplicità che ha già ucciso questo giro.

#### 7 · Ricalibrazione per-classe 1X2 del modello — Fase 10
- **Cosa**: il bias è **robusto** (casa sovrastimata, pareggio sottostimato,
  conferma in ogni stagione), pesi fissi 0.96/1.04/1.00.
- **Numeri**: −0.0005, nel rumore.
- **Perché in panchina**: il bias è reale ma piccolo; correggerlo non paga in
  log-loss. Utile per l'uso pratico dove serve calibrazione, non ranking.
- **Fronti (audit §12)**: portata sul path DC delle leghe nuove **peggiora** —
  Bundesliga +0.0028 (1/6 stagioni), **Ligue 1 +0.0022 [+0.00036, +0.00402],
  CI conclusivo CONTRO**. Il bias per classe di quelle leghe non è
  significativo in nessuna delle 6 celle (|z| ≤ 1.26).

#### 8 · Diagonale inflazionata (`--draw-inflation`, φ costante) — Fase 12b
- **Numeri**: −0.0004 (3/6); migliora la calibrazione del pareggio.
- **Perché in panchina**: *quanti* pareggi capitano è quasi-rumore; il log-loss
  non premia. Stessa nicchia d'uso pratico della voce 7.
- **Fronti (audit §12)**: era **la leva a più alta probabilità a priori** del
  blocco, perché la φ costante sembrava fare meglio della φ35. Misurata:
  Bundesliga +0.00069 (2/6), Ligue 1 −0.000056 (2/6) — **non paga in nessuna
  delle due**. L'indicazione va letta come «la parte intelligente della φ35 non
  si ripaga», **non** come «la φ costante funziona».

#### 9 · Covariata congestione vera `rest_full` — Fase 4e-bis
- **Numeri**: −0.0004 medio (2020-25), inverte il segno del proxy solo-lega ma
  resta nel rumore.
- **Perché in panchina**: guadagno non distinguibile da zero.
- **Fronti (aggiornato F79 + audit)**: testata su Premier/Liga e **bocciata** —
  Premier +0.0005 (P 9%) malgrado sia la lega più congestionata (riposo ≤3g
  nel 21.6% delle partite) e il β abbia direzione sensata (−0.019, 5/6);
  Liga β instabile (+0.053…−0.040). Su Bundesliga +0.000796 e Ligue 1
  +0.000371: **rumore su 5/5 leghe**. Il fit pesato nel tempo assorbe già la
  congestione.

#### 10 · Temperature scaling post-hoc — Fase 6
- **Numeri**: T≈0.94 (sottoconfidenza lieve, robusta), guadagno −0.0003.
- **Perché in panchina**: trascurabile. Modulo pronto
  (`src/evaluation/calibration.py`) per l'uso pratico.
- **Fronti (audit §12)**: Bundesliga −0.000236 [−0.00163, +0.00116] (5/6, nel
  rumore), Ligue 1 +0.00037 (2/6, peggiora). ⚠️ col **test del rapporto di
  verosimiglianza nessuna T è distinguibile da 1** (Bundesliga 1.063,
  LR = 1.32, p = 0.25); l'unica lega con T ≠ 1 al 5% è La Liga (0.890,
  p = 0.018), che non supera Bonferroni su 5 leghe. La domanda «il DC è più
  sovra-confidente sulle leghe nuove?» **non ha risposta misurabile**.

#### 11 · GBM + finishing-luck — Fase 33
- **Numeri**: −0.0022 (P 81%) del GBM con la covariata luck.
- **Perché in panchina**: non conclusivo E il GBM parte comunque dietro al DC
  (Fase 22): un miglioramento di un modello non attivo non è una promozione.

#### 12 · Covariata `midweek_europe` — Fase 36-bis
- **Numeri**: −0.0003 in Serie A, con β = −0.020 **stabile 6/6**.
- **Perché in panchina**: CI include lo zero, ed è ridondante con `rest_full`.
- **Fronti (F79 + audit §12.1)**: il β stabile della Serie A **non si replica**
  (Premier alterno, Liga +0.008 di segno opposto; Bundesliga −0.000393,
  Ligue 1 +0.000321). E la pista indicata come più interessante si chiude: col
  dato di coppa **corretto** (3.045 calendari recuperati; 68 celle 0→1 in
  Bundesliga, tasso 12,07% → 15,34%, e 212 in Ligue 1, tasso 5,02% →
  **12,80%**) il confronto diretto
  fra covariata bucata e corretta è +0.000048 [−0.00074, +0.00083] e
  −0.000094 [−0.00127, +0.00104]: **misurare bene la congestione non la fa
  funzionare**. L'integrazione dei calendari resta giusta per *correttezza del
  dato*, non per guadagno predittivo.

#### 13 · Temperatura sopra dp_lvl — Fase 52-ter
- **Numeri**: 1X2 0.9609 → **0.9605** con T = 1.056.
- **Perché in panchina**: si somma a una leva già Serie-A-only e "da oracolo"
  (`sharpen_1x2` non produce ROI): un affinamento sopra un affinamento.

#### 14 · Estremizzazione della chiusura O/U (α ≈ 1.15-1.33) — audit §8.2
- **Cosa**: la chiusura O/U **devigata** è sistematicamente *meno estrema* dei
  fatti; estremizzarla in spazio logit con α > 1 la avvicina.
- **Numeri**: nel rumore in entrambe le leghe nuove, ma **α > 1 in tutte le
  stagioni**; è emersa come sotto-prodotto della confutazione della leva
  «estrapolare il movimento apertura→chiusura» (estremizzando, il β residuo di
  quel movimento crolla da 1.75 e 1.90 a 1.40 e 1.60).
- **Perché in panchina**: misurata su due sole leghe, mai su un mercato diverso
  dai totali. **Promozione se**: replica su una terza lega.

#### 15 · θ come rimedio di CALIBRAZIONE (famiglia GG/clean-sheet) — audit §11
- **Cosa**: il difetto di calibrazione del motore è **una famiglia sola** e si
  replica: GG/NG **sotto**-prezzato, clean-sheet e vince-a-zero **sovra**-prezzati
  (pooled 2 leghe nuove: GG −0.0221 con z −3.01, clean sheet casa +0.0180,
  vince-a-zero casa +0.0132). Accendere il router θ raddrizza quel bias.
- **Numeri**: bias GG Bundesliga −0.0238 → −0.0106, Ligue 1 −0.0206 → −0.0049,
  Serie A −0.0292 → +0.0049; dopo la θ il CI del GG contiene lo zero ovunque.
  Regge al devig di Shin (−0.0234 invece di −0.0238), a un ancoraggio coerente
  sotto la matrice double-Poisson e a una θ **walk-forward**. Una θ
  leave-one-**league**-out (θ 1.09-1.17, mai vista la lega bersaglio) migliora
  tutte e tre le leghe: è l'unica candidata seria del fronte **generale**.
- **Perché in panchina**: il guadagno in **log-loss** è minuscolo (0.6847 →
  0.6842) — è esattamente il motivo per cui la griglia sul log-loss aveva
  bocciato la θ su quelle leghe: *è un argomento per la leva che il log-loss
  non sa vedere*. E manca la baseline onesta: uno **shift LOSO del bias medio**
  (un solo parametro) azzera il bias GG meglio della θ in tutte e tre le leghe.
  L'alternativa **ρ** non è esclusa: ρ\* = −0.240 (Bundesliga) e −0.199
  (Ligue 1) azzerano lo stesso bias, e in Bundesliga un ρ ri-tarato è un
  rimedio globale *migliore* della θ (media |bias| su 9 mercati 0.0075 contro
  0.0132) — anche se ρ\* è scelto in-sample mentre la θ è LOSO.

#### 16 · dp_tilt — θ + solo tilt, senza la scala — audit §7.3
- **Cosa**: la correzione dei livelli di `sharpen_1x2` si scompone in **tilt**
  (parte asimmetrica, bias-casa, a scala invariata) e **scala** (parte
  simmetrica). In Serie A l'affinamento è **quasi puro tilt** (−0.0270 contro
  −0.0006 di scala).
- **Numeri**: Serie A −0.0020 su **entrambi** i protocolli (7/7 e 6/6 stagioni)
  — cioè eguaglia `dp_lvl` con **un parametro in meno**, ed è l'unica variante
  conclusiva anche in walk-forward. Fuori: Premier +0.0009, Ligue 1 +0.0003,
  Bundesliga +0.0012, La Liga −0.0010.
- **Perché in panchina**: è una sola lega, ed è la stessa lega su cui la leva
  madre è già "da oracolo" (nessun ROI). **Promozione se**: sostituzione
  documentata dentro `sharpen_1x2` con i benchmark ricalcolati.

#### 17 · Inversione a ρ LIBERO (3 parametri su 4 bersagli) — report 11, C7
- **Cosa**: `implied_lambda_mu` è un minimo quadrati con **2** parametri su
  **4** bersagli (1X2 + O/U): non può centrarli tutti, e il residuo è
  sistematico. Liberando ρ i bersagli si centrano.
- **Numeri**: residui 0.0000 su tutti e quattro, ρ medio **−0.0928**
  (sd 0.0505) contro il −0.06 ufficiale; lo scarto fra prezzo del book e nostro
  prezzo sul GG scende da +0.0160 a **+0.0107** (*un terzo dello scarto era il
  nostro vincolo su ρ, non il book*), e il bias di livello diventa −0.0022
  [−0.0152, +0.0112].
- **Perché in panchina**: in **log-loss** non guadagna (−0.00050 [−0.00165,
  +0.00059]); e il residuo che resta è indistinguibile dalla cattiva
  specificazione della nostra famiglia Poisson (le linee O/U *non* usate come
  bersaglio sbagliano della stessa taglia: over 0.5 +0.0107, over 1.5 +0.0132,
  over 3.5 −0.0102, over 4.5 −0.0151). Vale come **diagnostico**, non come
  leva. Rimedio alternativo mai testato: **pesare i 4 bersagli** nell'inversione.

#### 18 · GG/NG dalla scaletta completa del book — report 11 §8
- **Cosa**: invertire più linee O/U del book invece della sola 2.5, prima di
  derivare il GG/NG.
- **Numeri**: 0.6833 contro 0.6840 del prezzo del book (−0.00067 [−0.00182,
  +0.00048]); MAE dal book 0.0159 contro 0.0186 della variante a una linea;
  segno favorevole in 3 blocchi su 3.
- **Perché in panchina**: mai conclusiva — e il confronto diretto fra le due
  varianti è nel rumore (−0.00026 [−0.00067, +0.00016]). **Promozione se**:
  replica su più partite o su un secondo book.

---

## ❌ I bocciati (testati e scartati — coi numeri del verdetto)

| modello/leva (fase) | verdetto | numero chiave |
|---|---|---|
| Tiri in porta grezzi nel blend (3) | nullo/negativo su 6 stagioni | — |
| Vantaggio-casa per-squadra (8) | il γ per-club è solo rumore stagionale | persistenza anno-su-anno r≈0.00 |
| Covariate squad_value / absence / npxG (4c, 11) | ridondanti con gol+xG; squad_value PEGGIORA in ogni combo | +0.0004…+0.0007 |
| **Le stesse covariate sulle leghe nuove (audit §12.1)** | 6 su 6 bocciate, 12 Δ su 14 peggiorativi; e **la stabilità del segno di un β non è evidenza di valore** | `squad_value` +0.000873 in Bundesliga con **0/6** stagioni migliorate, β +0.056/+0.095 stabile 6/6 |
| Forma / streak / rendimento recente (13) | già catturati dal fit pesato nel tempo | corr residui +0.035 |
| Blend lineare modello+mercato (16) | il mercato INGLOBA il modello | α* ≈ 0 perfino in-sample |
| **Encompassing sul GG/NG (report 11)** | replica del risultato su un mercato nuovo, un book nuovo e 5 leghe: il prezzo del book **ingloba il DC** | α\* = 0.060, con α\* = 0 nel **70%** dei fit; DC +0.01036 [+0.00632, +0.01454] |
| Temperatura post-hoc su P(campione) (89) | con n=24 non si stima onestamente nemmeno **1** parametro: guadagna in-sample, **peggiora** in leave-one-out | LOO 1.2160 vs 1.1994 (T=1.15 in-sample, guadagno 0.0088) |
| Covariata `squad_value` sul mercato campione (89-bis) | il mercato estivo NON e' informazione nuova: gia' contenuto nei gol/xG (β>0 ma ridondante), come sulle singole partite (4c/66-70) | log-loss 1.2384 vs **1.1994**; 2/16 sulle stagioni di cambio, identico al base |
| ρ dinamico per-partita (18) | instabile, sbatte sui bound | +0.0003 [−0.0007,+0.0013] |
| GBM diretto per mercato (21/22/36) | non batte il DC su NESSUN mercato; col feature-set completo overfitta | nessun CI conclusivo a favore su 5/6; train 0.913→0.867, test ~1.01 |
| GBM modello+mercato (23) | degrada perfino il mercato-feature | 0.9996 vs mercato 0.9632 |
| Finestre dati corte (25) | più storia batte meno, sempre | 3 stag +0.0011, 2 stag +0.0019 |
| Binomiale negativa (27) | i gol NON sono sovra-dispersi dati i tassi | nb_size→Poisson |
| COM-Poisson (85) — **ritirata come modello distinto (F101)** | non era una famiglia alternativa: `_dp_pmf` è `q_k ∝ a^k/(k!)^θ` rinormalizzata, cioè **la COM-Poisson con ν=θ**, entrambe mean-matched. Ri-eseguito `scripts/_run_tail_analysis.py` su 7.980 partite: a parametri appaiati le tre statistiche coincidono (ν=θ=1.35 → 2.8359/2.8358, Δ Over3.5 e Over4.5 identici alla quarta cifra). Il «ν=1.15 pareggia la dp θ=1.225» confrontava la stessa famiglia a due θ diversi | exact-LL a ν=θ=1.15: dp 2.832060 vs COM 2.832057 (Δ 3.8e-06); max\|dp−COM\| sulla pmf ≤ 9.6e-05. Su griglia fine l'argmin è **θ=1.18** (Δ −0.00027 [−0.00083,+0.00027], nel rumore), non 1.225 |
| Coda a 2 parametri: isotonica per-soglia + mistura di 2 Poisson (87) | (A) l'isotonica peggiora il log-loss OOS su tutte 4 le soglie; (B) la mistura guadagna in-sample ma OOS non conclusiva e si ribalta sulle stagioni recenti | A: +0.0061…+0.0150; B: Δ −0.00042 CI [−0.0015,+0.0006] P 78.6%, 2425/2526 positive |
| Power-devig / denoising (38, 50) | motore già non-biased | Platt a≈1.06 peggiora +0.0020; η=0.909 mai utile |
| **Power-devig fuori dalla Serie A (audit §5C)** | pista chiusa anche altrove: peggiora con CI conclusivo in Bundesliga (a 7 **e** a 9 stagioni), nel rumore in Ligue 1 | +0.00035 [+0.00004, +0.00066] |
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
| **Beat-the-close su Bundesliga e Ligue 1 (audit §7)** | pista **chiusa** anche con la selezione più favorevole: peggiora la chiusura, e in Bundesliga il CI **esclude** perfino l'effetto Serie A (caso raro di «dimostrato assente»). Bocciata anche **in-sample, barando** (BL +0.0005). Servono entrambi gli ingredienti — θ≈1.23 **e** tilt≈−0.027 — e lì non c'è né l'uno né l'altro | BL +0.0016 [+0.0004,+0.0027] (walk-forward +0.0026 [+0.0007,+0.0045]); L1 walk-forward +0.0020 [+0.0001,+0.0039]; **ROI −22,46% e −12,90%**, cioè 3-5 volte peggio che scommettere alla cieca |
| **Estrapolazione del movimento apertura→chiusura sui totali (audit §8.2)** | leva proposta e uccisa nella stessa sessione: β LOSO e walk-forward nel rumore, 4/7 stagioni, sensibile al devig, e in gran parte spiegata dal fatto che la chiusura O/U devigata è **sotto-estrema** | β 1.75 (BL) e 1.90 (L1) → 1.40 e 1.60 dopo l'estremizzazione; ROI −3,95% e +0,91% con CI larghissimi |
| **Ricalibrazione Platt del prezzo del BOOK sul GG/NG (report 11)** | per-lega peggiora con CI conclusivo (2 stagioni di training per lega = pura varianza); pooled e offset puro nel rumore. Il bias di livello del book (+0,84 pt) esiste ma **non è correggibile in modo dimostrabile** | per-lega +0.00198 [+0.00064,+0.00333]; pooled +0.00012 [−0.00037,+0.00062] |
| **Ricalibrazione dei livelli λ+μ sul GG/NG (report 11 §4)** | peggiora **con CI conclusivo su entrambi i fronti** — è la conferma che il fronte generale non salva una leva che non c'è | per-lega +0.00092 [+0.00007,+0.00178]; pooled +0.00075 [+0.00012,+0.00137] |
| Ri-taratura per-lega di emivita/shrinkage/α (57) | piatta: il gap è informazione, non calibrazione | tutti i Δ entro ±0.0005 — e ora **5 leghe su 5** (audit, report 6 passo 3) |
| **θ per-squadra sulla coda (86/86-bis)** | la volatilità-sorpresa PERSISTE (corr +0.20 controllata per forza) ma il θ_team **peggiora OOS** (θ di gruppo instabili anno-su-anno): non sfruttabile | walk-forward Δ **+0.00096** su 5.690 partite (exact-LL 2.8222 vs 2.8212) |
| **Simulatore di stagione in Ligue 1 (audit §9)** | il simulatore trasferisce, il valore no: contro «vince la rosa più cara» al suo meglio è **conclusivamente peggiore**, 0 stagioni su 8 | −0.1682 [−0.33, −0.05]; e su tutte e 40 le stagioni-lega il MC pareggia una baseline a **un** parametro (+0.0303 [−0.16, +0.21]) |
| **Pari/dispari (playbook, 6ª replica)** | l'unico mercato dove la baseline batte il motore, in tutte le leghe provate | Bundesliga +0.0002, Ligue 1 +0.0000 |

---

## Lead operativi (non modelli, ma misurati e in attesa)

| lead (fase) | numeri | stato |
|---|---|---|
| **Draw-bias Serie A**: puntare il pari nelle partite equilibrate (40) | ROI **+4.7%** (CI [−4.9,+14.4], P 83%, 4/6 stagioni); conferma indipendente Fase 51-ter: +3.2% (P 76%) | non concluso, alta varianza; NON si replica su Premier (−5.4%, Fase 53), mezzo-gemello in Liga (+3.6%, P 81%). **Audit a 5 leghe**: il ROI pari-equilibrio non è conclusivo in **nessuna** lega (tutti i CI attraversano lo zero), Bundesliga compresa nonostante il +5.04% di stima puntuale, e la Ligue 1 è a −7.82% |
| **Stakes-mismatch** (una squadra "decisa", l'altra in corsa) (31/32/45) | gap del modello vs mercato +0.0549 sul mismatch; ma il router stakes-aware NON lo sfrutta (soft −0.0018, P 53%) | informazione del MERCATO, non nostro errore recuperabile (Fase 45 chiude) |
| **θ e φ0 sono la stessa cosa vista da due angoli** (audit, report 6 passo 2b) | corr(θ, φ0) = **+0.755** sulle 5 leghe; le due «latine» hanno entrambi alti (θ≈1.24, φ0≈0.245), le «inglesi» entrambi bassi, la Bundesliga è l'unico caso intermedio (θ 1.080, φ0 0.183) | osservazione strutturale, non una leva: la Bundesliga è il posto giusto dove separare i due effetti, se si vorrà |
| **T del temperature scaling e θ del mercato sono in corrispondenza di rango perfetta e inversa** (audit §12.2) | Spearman **−1.000** sulle 5 leghe (p esatto di permutazione 2/120 = 0.017) | **pista, non risultato**: quattro T su cinque sono indistinguibili da 1 e tre θ su cinque stanno in una valle sei volte più piatta; il contenuto reale è la spaccatura a due gruppi, la cui concordanza casuale vale 1/10 |

---

## Archivio (voci uscite dalla rosa)

- **2026-07-27 (Fase 101-ter, integrazione dell'audit a 5 leghe)** —
  *Simulatore del mercato campione, Ligue 1*: da 🪑 a **❌** (conclusivamente
  peggiore della baseline «vince la rosa più cara» al suo meglio, 0/8).
  *Ricalibrazione-μ per il GG/NG, Bundesliga*: entra in matrice come **⬜
  misurata ma non dimostrata** — nel primo giro dell'audit era 🪑, poi
  declassata (7 celle conclusive su 300 = quante ne dà il caso; non replica;
  il giudice esterno non conferma). *Temperature scaling e ricalibrazione per-classe del
  modello*: prime celle fuori dalla Serie A, rispettivamente 🪑/❌ e ❌/❌.
  *Ensemble di emivite*: prima cella con **CI conclusivo** (Ligue 1), non
  promossa per molteplicità. Sei righe nuove (✱10) per leve che erano state
  misurate senza avere una riga.
- **2026-07-27 (Fase 101)** — *COM-Poisson*: **uscita dalla matrice**. Non è
  una famiglia alternativa alla double-Poisson ma la stessa dp riparametrizzata
  (`dp(θ) ≡ COM-Poisson(ν=θ)`, coincidenza a ≤5e-06 sull'exact-score log-loss):
  non poteva avere una riga propria né valere come conferma indipendente. Il
  verdetto resta fra i bocciati.
- **2026-07-23 (Fase 81)** — *Router v3 su La Liga*: da ❌ (F53) a 🪑 alta.
  Motivo: la bocciatura F53 usava il θ fittato per MLE sui punteggi (1.097);
  il mega-sweep F81 mostra che l'ottimo operativo sui mercati è θ≈1.2 (come
  in Serie A: MLE 1.205 → router 1.225) e con quello il router migliora
  ris. esatto/1X2/GG con selettore walk-forward e CI<0. La regola nuova:
  le costanti operative si scelgono sui MERCATI (griglia+lfo), non sulla
  verosimiglianza dei punteggi.
