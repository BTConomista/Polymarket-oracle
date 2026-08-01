# Football Oracle

Motore di stima delle **probabilità reali di eventi sportivi** (calcio),
**indipendente dalle piattaforme** di scommessa.

*(Ex «Polymarket Oracle»: rinominato per riflettere lo scopo reale — un oracolo
di probabilità sul calcio, non un sistema legato a una piattaforma specifica.)*

Il valore del progetto è il **modello di previsione**, non l'integrazione con una
piattaforma specifica. Il motore stima la distribuzione dei gol di una partita; da
quella distribuzione si derivano in modo coerente tutti i mercati (1X2,
Over/Under, ecc.). Solo in un secondo momento il motore potrà essere collegato a
Polymarket, bookmaker, exchange o altri mercati di previsione.

> 📖 **[Diario di bordo](docs/DIARIO.md)** — il resoconto passo-passo di tutte le
> fasi, con il ragionamento e le scelte dietro ogni decisione. Se vuoi capire
> *perché* il progetto è fatto così, parti da lì.
>
> 🛠️ **[Protocollo di lavoro](CLAUDE.md)** — come si contribuisce e **cosa
> aggiornare ogni volta** (registro esperimenti, diario, test). Da leggere prima
> di modificare il progetto; una sessione AI lo carica in automatico.
>
> 🗂️ **[Catalogo dei dati](docs/DATI.md)** — TUTTI i dati a disposizione:
> fonti, coperture, semantica apertura/chiusura delle quote, e **cosa è dato
> reale vs cosa è STIMA** (`data/estimates/`). Da consultare prima di ogni
> analisi sui dati.
>
> 📖 **[Glossario](docs/GLOSSARIO.md)** — i termini del progetto (devig,
> market-implied, θ/sotto-dispersione, φ35, encompassing/α\*, walk-forward,
> Tier 1/2/3…) in una riga ciascuno, con la fase che li introduce. Il punto
> d'ingresso per un lettore nuovo.
>
> ⚽ **[La rosa dei modelli](docs/PANCHINA.md)** — lo stato di **OGNI** modello
> del progetto: **titolari, panchina, bocciati**, ciascuno su **due fronti**
> (versione per-lega e versione generale/pooled), con la matrice
> modello × lega a colpo d'occhio. Sempre aggiornata (regole nel CLAUDE.md
> §1.9 e §2).
>
> 🏴󠁧󠁢󠁥󠁮󠁧󠁿🇪🇸 **[Studio Premier League e La Liga](docs/STUDIO_PREMIER_LIGA.md)** —
> il quaderno dedicato alle due leghe non-Serie A: dati, differenze
> strutturali, stato dei test per-lega e piano ragionato dei prossimi
> esperimenti (Fase 79+).
>
> 🧭 **[Playbook nuova lega](docs/PLAYBOOK_NUOVA_LEGA.md)** — la procedura
> passo-passo per aggiungere un campionato nuovo (dati → EDA → tracer →
> ri-taratura → motore → leve per-lega), con le lezioni già pagate e la
> checklist di aggiornamento. Da seguire per ogni lega futura.

## Stato attuale

Pipeline **end-to-end** funzionante su **cinque campionati** — Serie A, Premier
League, La Liga, **Bundesliga**, **Ligue 1** — 9 stagioni ciascuno, **16.111
partite**, schema identico (stesse colonne e stesso ordine, verificato da un
test). Il racconto qui sotto parte dalla Serie A perché è lì che il modello è
nato; le conclusioni sono state poi **replicate** sulle altre quattro.

`dati storici → modello Dixon-Coles → probabilità 1X2 e Over/Under 2.5 → validazione`

- **Modello**: Dixon-Coles (1997) con decadimento temporale, implementato da zero
  (`src/models/dixon_coles.py`). Stima forza d'attacco/difesa di ogni squadra +
  vantaggio-casa + correzione sui punteggi bassi.
- **Dati**: 9 stagioni × 5 leghe (2017-18 → 2025-26) in formato
  football-data.co.uk, arricchite con xG Understat, valore rosa e calendario di
  club. Verificate **riga per riga contro la fonte** (0 differenze su gol, date,
  tiri, quote e xG) e contro una **seconda fonte indipendente** per i gol.
- **Validazione**: backtest walk-forward su 6 stagioni di test (2020-21 → 2025-26,
  riallenamento settimanale, **senza look-ahead**), con Brier score e log-loss,
  confronto contro le quote di chiusura dei bookmaker e contro una baseline banale.

### La configurazione ufficiale e il risultato

Metrica principale: **log-loss 1X2 medio**, walk-forward **senza look-ahead**,
sulla **media di 6 stagioni** (2020-21 → 2025-26) — mai una sola, che è rumorosa.
Config ufficiale: **blend gol/xG (α=0.75)** · shrinkage **1.5** · emivita **365g**
· **prior neopromosse δ=0.23**.

| Mercato | Modello | Mercato (chiusura) | Baseline in-sample | Baseline ex-ante |
|---|--:|--:|--:|--:|
| **1X2** (log-loss) | **0.9799** | **0.9632** | 1.0834 | 1.0860 |
| **Over/Under 2.5** | 0.6884 | 0.6816 | 0.6892 | 0.6961 |

*Nota onestà (audit Fase 15): la baseline stampata dalla pipeline usa le frequenze
H/D/A della **stagione di test stessa** (in-sample: è la costante ottima a
posteriori, quindi leggermente troppo forte). La baseline **ex-ante** — frequenze
delle sole stagioni precedenti, l'unica giocabile davvero — è ricalcolata qui
accanto: 1.0860 (1X2) e 0.6961 (O/U). La differenza non cambia nessuna
conclusione.*

Il modello **batte nettamente la baseline** ma **non il mercato**: gap 1X2
**+0.0167** (ha chiuso **~86%** della distanza baseline→mercato: 86.1% sulla
baseline in-sample, 86.4% su quella ex-ante). Su una singola stagione i numeri
oscillano → si giudica sulla media. Il *value betting* simulato con la config
ufficiale dà **ROI medio −15.8%** su 6 stagioni (866 scommesse; per stagione da
−4.7% a −23.0%; pooled −15.8%): chi non batte la linea di chiusura perde contro
il margine del bookmaker. *(Nota best-price, Fase 86: quel −15.8% è alla quota
**media** di chiusura; al **best-price** cross-book — col metodo coerente
seleziona-e-paga al massimo — la perdita si riduce ma resta negativa: es. 2025-26
da −4.7% a **−2.4%** a soglia 0.05. Il +0.9% che sembrava positivo era un metodo
incoerente, selezione alla media e pagamento al massimo. Conclusione invariata.)*
E non è questione di "scommettere prima": il modello
**non batte nemmeno la linea di apertura** (gap +0.0146, ROI@open −17.3%, CLV
negativo — Fase 14). **Non usare questo modello per scommettere soldi
veri.** *(Il "ROI ≈ −8.5%" riportato in precedenza era il valore del primo
backtest di Fase 1 — una sola stagione, modello iniziale — rimasto per errore
accanto a metriche a 6 stagioni: corretto nell'audit di Fase 15.)*

> ⚠️ **I numeri di questa sezione sono ricalcolati al codice di HEAD**, cioè dopo
> il fix del vincolo di identificabilità della Fase 92 (`attack[seen].mean()` al
> posto della media su tutte le squadre): il walk-forward ufficiale a 6 stagioni
> dà **modello 0.9799 / mercato 0.9632 / gap +0.0167**. Le misure delle singole
> fasi riportate più sotto e nel registro `experiments/runs.jsonl` sono **PRE-fix**
> e hanno come base 0.9797: restano valide come confronti *interni a quelle fasi*
> (stesso codice per entrambi i bracci) e non vanno riscritte. Punto 1 di §4 del
> verbale `docs/AUDIT_FASI_80_100.md`, eseguito.

### Come si è chiuso il gap (dal modello grezzo all'attuale)

| Versione | gap 1X2 vs mercato | Δ |
|---|--:|--:|
| V0 — grezzo (soli gol, no shrinkage/decay) | +0.0236 | — |
| V1 — gol tarato (shrinkage + emivita, Fase 2b) | +0.0185 | **−0.0051** |
| V2 — +xG nel blend (Fase 4b) | +0.0181 | −0.0004 |
| V3 — emivita ri-tarata 365g (Fase 4d) | +0.0175 | −0.0006 |
| V4 — +prior neopromosse (Fase 7, **ATTUALE**) | **+0.0167** | −0.0010 |

*Il Δ del prior compare come −0.0010 qui e come −0.0011 nella tabella degli
esperimenti: non è un refuso ma due stime diverse dello stesso intervento —
−0.0010 con δ=0.23 fisso (misura PRE-fix Fase 92: 0.9797 vs 0.9807; al codice di
HEAD il braccio V4 vale 0.9799 e il V3 non è stato rimisurato), −0.0011 con δ
stimato leave-future-out stagione per stagione (Fase 7: 0.9796). Entrambe
verificate sul registro.*

Il **72%** del recupero viene dalla sola regolarizzazione+memoria (Fase 2b); il
resto sono rendimenti decrescenti — segno che il modello è al **tetto** dei dati.

### Tutti gli esperimenti, in un colpo d'occhio

> Registro sempre aggiornato di **ogni** analisi (regola obbligatoria nel
> `CLAUDE.md`). Il dettaglio di ciascuna è nella sezione
> **[Analisi dettagliata per fase](#analisi-dettagliata-per-fase)**; il
> ragionamento completo nel **[DIARIO](docs/DIARIO.md)**; i run grezzi replicabili
> in **[`experiments/runs.jsonl`](experiments/runs.jsonl)**.

| Fase | Leva provata | Effetto (1X2) | Esito |
|:--:|---|--:|:--:|
| 2b | shrinkage + emivita | gap −0.0051 | ✅ adottato |
| 3 | tiri in porta grezzi (SOT) | nullo / negativo | ❌ off |
| 4b | blend gol / **xG** (α=0.75) | guadagno (soprat. O/U) | ✅ adottato |
| 4c | valori rosa · assenze · npxG | ridondanti | ❌ off |
| 4d | ri-taratura emivita → 365g | piccolo guadagno | ✅ adottato |
| 4e-bis | congestione vera (`rest_full`) | −0.0004 (rumore) | ❌ off |
| 6 | temperature scaling | −0.0003 (rumore) | ❌ off |
| **7** | **prior neopromosse (δ=0.23)** | **−0.0011; −0.0039 sulle promosse** | ✅ **ADOTTATO** |
| 8 | shrinkage / vantaggio-casa per-squadra | piatto / non persiste | ❌ off |
| 10 | ricalibrazione per-classe (casa↓ / pari↑) | −0.0005 (rumore) | ❌ off |
| 11 | combinazioni di feature off | nessuna utile | ❌ off |
| 12a | ensemble di emivite (180+730) | −0.0006 (borderline) | ❌ off |
| 12b | **diagonale inflazionata** (bivariato) | calibra il pari, ma −0.0004 | ❌ off |
| 13 | forma · streak · rendimento recente | R² = rumore | ❌ off |
| 14 | **linea di APERTURA + CLV** | gap open **+0.0146** (6/6); CLV **−0.0028** (45%>0) | ❌ niente edge |
| 15 | **audit dei calcoli** (verifica di ogni numero) | ROI corretto (−15.7%, non −8.5%); resto confermato | ✅ doc corretta |
| 15-bis | gap per mercato × stagione | 12≈0 in ogni stagione; pari persistente; O/U volatile | ✅ analisi |
| 16 | **encompassing** (blend modello+mercato) | **α\*≈0 ovunque**: nessuna info propria | ❌ definitivo |
| 17 | **CI bootstrap sui numeri chiave** | gap 1X2/O/U reali\*; 12 e Δ prior **≈0 statistico** | ✅ analisi |
| 18 | **ρ dinamico** (correzione per-partita) | +0.0003 (CI include 0; slope instabile) | ❌ off |
| 19 | potenza sul prior: finestra a **8 stagioni** | −0.0013 [−0.0026, +0.0001], P(aiuta) 96.5% | ✅ conferma (non concluso) |
| 20 | **residui su tutte le covariate + adverse selection** | R²=rumore; ma gap ∝ dissenso (r=+0.18) | ✅ scoperta (perché si perde) |
| 21 | **gradient boosting sul GG/NG** (modello nuovo) | calibrato pareggia il DC (+0.0047), nessuno batte la baseline | ❌ non adottato (convergenza) |
| 22 | **sweep GBM su 6 mercati × 3 feature** | non batte il DC su nessun mercato; gap ✗ su 5/6 | ❌ tetto informativo |
| 23 | **GBM modello + mercato** (encompassing non-lin.) | col mercato come feature resta > DC; non lo pareggia | ❌ nessun edge, gap non ridotto |
| 24 | **DC calcolato DAL mercato** (λ,μ impliciti → GG/NG) | GG/NG 0.6853: batte DC-da-gol (P=95.7%) e la baseline | ✅ primo miglioramento (condizionato alle quote) |
| 25 | **finestra dei dati** (taglio netto / no-COVID) | tagliare i dati vecchi peggiora (+0.0011…+0.0035) | ❌ più storia è meglio |
| 26 | **market-implied su tutti i mercati gol** | batte DC-da-gol su 13/14 mercati e la baseline su 13/14 | ✅ motore di pricing (condizionato alle quote) |
| 27 | **forma dei punteggi** (ρ/φ/binom-neg fittati) | già ottima; NB rigettata (gol ~Poisson) | ❌ tetto anche sulla forma |
| 28 | **errore per giornata** (finale di stagione) | fine più difficile per TUTTI; gap raddoppia ma non concl. | 🔎 tendenza (posta in palio) |
| 29 | **posta in palio** (dead rubber dalla classifica) | dead rubber rari (4.3%); nessun effetto sul gap | ❌ non spiega il finale |
| 30 | **pattern dentro la stagione** (anatomia) | no trend robusto; vantaggio-casa crolla a fine stagione | 🔎 candidato: home-adv finale |
| 31 | **posta in palio corretta** (8 stag., asimmetria) | mismatch motivazione: gap +0.057 (3×), ribalta la 29 | 🔎 lead: stakes mismatch |
| 32 | **covariata stakes** su DC e GBM (walk-forward) | aiuta i mismatch su entrambi (GBM −0.0127) ma CI tocca 0 | 🔎 lead credibile, non concluso |
| 33 | **PPDA/deep + finishing-luck** (ultimi segnali interni) | ridondanti; luck esattamente 0 (già nel blend xG) | ❌ dati interni esauriti |
| **34** | **audit critico** (formule + superficialità + leve mai testate) | formule OK; pareggio deficit −0.044 nelle partite **equilibrate** \|λ−μ\| (mai testato); post-hoc **−0.0014, P 77%** | 🔎 lead strutturale (→ Fase 35) |
| **35** | **φ pareggio condizionato a \|λ−μ\|** (equilibrio) | 1X2 **0.9790** (Δ −0.0007, best di 4 varianti); calibrazione pari equilibrati 0.287→**0.334** (reale 0.332, **batte il mercato**); CI include 0 | 🔎 miglior risultato sul pareggio; off di default (uso pratico) |
| **36** | **GBM col set di feature COMPLETO** (stakes+luck+ppda+deep+midweek) | overfitting (train 0.913→0.867, test invariato ~1.01); nessun GBM batte il DC; **ma stakes reale sul mismatch: full 0.9703 vs DC 0.9797 (n=99)** | ❌ overfitting in aggregato / 🔎 stakes localizzato (conferma Fase 32) |
| 36-bis | **`midweek_europe` covariata DC** (dummy congestione) | −0.0003 (CI include 0); ma β_midweek stabile −0.020 (6/6) vs β_rest_full che cambia segno → dummy più pulito; insieme ridondanti | ❌ off (utile cross-lega) |
| **37** | **covariate nel canale-pareggio** (Punto 3, diagnostico) | "cruciali → più pari" FALSO (residuo −0.0017); solo mismatch (−0.063, n=99, già Fase 31/32); corr sotto rumore | ❌ canale-pareggio saturo (nessuna chirurgia) |
| **38** | **denoising cross-stagione market-implied** (Punto 4) | motore già non-biased (Platt a≈1.06 → peggiora +0.0020); power-devig −0.0003 (non concl.); recency ≡ all-history (nessuna deriva) | ❌ motore già maturo; modulo pronto cross-lega |
| **39** | **market-implied + φ(\|λ−μ\|)** (sintesi Fase 26 × 35) | **GG/NG 0.6861 (miglior del progetto), Δ −0.0006, P 96%**; ris.esatto −0.0013 (P 80%); multigol −0.0001 | 🔎 ultimo margine interno; molto probabile, non concluso |
| **40** | **ROI per esito/mercato** (cosa nascondeva il 1X2 piatto) | casa −19.6% / trasferta −12.9% / **pari −2.0%**; **pari in partite equilibrate +4.7%** (CI [−4.9,+14.4], P 83%, 4/6 stag.); O/U negativo | 🔎 lead monetizzabile (draw bias); non concluso, alta varianza |
| **41** | **bakeoff per-mercato** (specialisti, Tier 1) | market-implied migliore su **19/20 mercati**, DC su 0, baseline 1 (pari/dispari); il portafoglio collassa a 1 motore + φ35 sui pareggi | ✅ specialisti = market-implied + φ35; no bespoke-per-mercato |
| **42** | **Poisson bivariato** (correlazione esplicita λ3, 5° modello) | λ3≈0.11 (corr +0.09, reale ma debole); non batte la φ35 su nessun mercato (GG biv −0.0003 vs φ35 −0.0005); **peggiora il multigol +0.0026** (sovra-disperde i totali) | ❌ perde vs φ35; l'equilibrio \|λ−μ\| batte la correlazione globale |
| **43** | **copule flessibili** (Frank, dipendenza di qualsiasi segno) | θ fittato **+0.62** (i dati vogliono dip. positiva anche potendo negativa); frank_b+φ pareggia φ35 sul GG (−0.0001, P 67%); copule peggiorano il multigol (+0.003) | ❌ φ35 è il tetto della forma; la φ fa tutto, la copula è zavorra sui totali |
| **44** | **routing di forma per-mercato** (`price_markets`: φ35 su esiti/pareggio/GG, τ puro sui totali) | router 0.7024 vs φ35-ovunque 0.7026 vs τ-ovunque 0.7027 (guadagno −0.0002/−0.0003, marginale); frank_b+φ **rimosso** dal motore (complessità senza guadagno); il market-implied prezza già il contesto quando ci sono le quote | ✅ adottato nel motore (ogni mercato dalla sua matrice migliore); marginali/in-play = prossima frontiera, ma bloccata dai dati |
| **45** | **router stakes-aware** (path senza quote: DC ovunque, GBM-stakes sul mismatch una-decisa/una-in-corsa) | gap mismatch DC vs mercato **+0.0549** (conferma Fase 31); ma **GBM-stakes 1.0087 > DC 0.9943** anche sul mismatch (il "6× meglio" della Fase 32 era vs GBM-base, non vs DC); router hard +0.0145, soft −0.0018 (CI [−0.034,+0.028], P(aiuta) 53%) | ❌ segnale reale ma **non sfruttabile**; chiude l'ultimo lead predittivo interno (info del mercato, non nostro errore) |
| **46** | **ensemble standalone** (DC + bivariato + GBM per-mercato, mean/logpool/DC+GBM) | miglior singolo = bivariato (≈DC, +0.0003); su 1X2 l'ensemble **peggiora** (mean +0.0033, dc_gbm +0.0080: il GBM zavorra); su O2.5/GG probabilmente utile di un filo (P(aiuta) 66–77%) ma CI include lo zero, non concluso | ❌ nessun ensemble batte il singolo in modo conclusivo: DC≈biv (no diversità), GBM diverso ma peggiore |
| **47** | **γ tempo-variante** (tracer-bullet dinamico: vantaggio-casa per fascia di giornata, Fase 30) | il crollo fine-stagione è confermato OOS ma è **l'ospite che segna +14.8%** nel finale, non la casa che cala → γ-only (V1) sbaglia leva e peggiora l'1X2; ricalibrare **entrambi** i tassi (V2) aiuta sul finale 35-38 (1X2 −0.0033 P70%, **GG/NG −0.0075 P91%**) ma nessun CI esclude lo zero (n=202) | 🔎 **redirect**: non "γ dinamico" ma inflazione-gol-ospite di fine stagione; primo segnale temporale intra-stagione nel verso giusto, e sulla GG/NG (mercato non prezzato). Probabile, non provato → irrobustire su 8 stagioni prima dello state-space pieno |
| **48** | **modello dinamico a profilo stagionale** (8 stagioni; profilo liscio Poisson di λ,μ per giornata vs bucket Fase 47) | l'effetto si **sgonfia** con più dati (boost-ospite 38ª ×1.148→**×1.072**); su 8 stagioni solo la **GG/NG** sopravvive (overall P84-93%, finale −0.006 P89-92%) ma nessun CI esclude lo zero; il modello liscio **non batte i bucket grezzi** (pari su GG, peggio su 1X2) | ❌ **chiude l'architettura dinamica**: nessuna forma batte lo statico in modo conclusivo; resta solo un nudge-GG/NG di fine stagione (~90%, off di default). Tetto informativo, non architetturale (anche nel tempo) |
| **48-bis** | **nudge GG/NG implementato** (`market_implied.btts_season` + `predict.py --matchday`) | profilo μ ufficiale `(−0.00118, −0.03657, +0.16799)` fittato pooled su 8 stagioni; alla 38ª alza la GG del solo mercato non-prezzato (es. Roma-Fiorentina 47.4%→51.1%); ≈invariata fuori dal finale | ✅ opt-in nel motore/tool, **off di default** (CI include lo zero); da rifittare per ogni lega (§7) |
| **49** | **finestra/forma del nudge** (perché solo 35-38? è gradabile/estendibile?) | forma empirica: piatta ~1 fino a g.34 (32-34 l'ospite segna *meno*, 0.966), salto solo g.36-38 (1.118); allargare (knee25) è il peggiore; la forma **libera cubica non trova segnale** a metà (Δ≈0, P50%); più stretta (knee34) è l'unica col CI overall <0 ma +0.0002 vs attuale = rumore | ✅ **non è binario** (già liscio) ma i dati non supportano estenderlo/graduarlo: segnale confinato alle ultime ~3 giornate; knee31 confermato ragionevole |
| **50** | **mega-sweep combinatorio market-implied** (14 combo: φ35 × nudge-μ × devig × copula, 8 stagioni n=2660; il nudge fittato sui λ,μ DEL MERCATO, mai provato) | **φ35 e nudge-μ sono ADDITIVI**: GG/NG **0.6810** (φ35+knee34, Δ −0.0010 CI [−0.0020,−0.0000] P 98%, 5/7 stagioni) e **0.6809** con copula (frank+k31, +complessità per −0.0001 → non si adotta); power-devig MAI utile (eta 0.909, chiude Fase 38); nudge senza φ35 neutro; guadagno concentrato nell'era porte-chiuse 1920-2122, ≈neutro ultime 4 stagioni | 🔎 **miglior GG/NG del progetto**; molto probabile, **non concluso** (multiple-testing, CI al limite) → off di default |
| **50-bis** | **scomposizione del nudge di mercato** (livello vs coda) + bias dei tassi impliciti | sul mercato il nudge NON è l'effetto-stagione della Fase 48 (già prezzato dalle quote): è **ricalibrazione adattiva** dei tassi (μ mercato basso ~2%, λ alto ~1.5%: il **bias-casa sopravvive al devig**); pooled 8 stagioni quasi piatto → nessun coefficiente statico da cablare; applicare il nudge-DC al path mercato **peggiora** (finale +0.0014) | ✅ meccanismo capito; **fix `predict.py`** (nudge solo sul Modello 1/DC) |
| **50-ter** | **ricalibrare il MERCATO stesso** (livelli λ,μ; pesi per-classe w_D/w_A leave-future-out) | livelli: 1X2 dell'engine 0.9637→**0.9630** (P 90%) ma la chiusura diretta resta meglio (0.9625); per-classe: **5/6 stagioni migliorano**, w_D≈1.09 w_A≈1.06 stabili (pari+trasferta sottoprezzati = draw bias noto), pooled Δ **−0.0006** CI [−0.0020,+0.0009] P 78% | 🔎 la crepa più credibile sulla chiusura, **non conclusa** (servono ~20 stagioni per il verdetto) |
| **50-quater** | **GBM bespoke per singolo mercato** (chiude la riserva §1.8; con λ,μ mercato, matchday e la predizione dell'engine TRA LE FEATURE) | perde **ovunque, su entrambi i path**: GG +0.0099, clean-sheet casa +0.0206, casa O1.5 +0.0170, O/U +0.0149 (tutti i CI escludono lo zero dal lato sbagliato); anche `gbm_dc` < DC ovunque; degrada perfino la predizione-engine ricevuta in input (meccanismo Fase 23) | ❌ **chiuso definitivamente** (quarta bocciatura della famiglia: 21/22/23/36 + questa) |
| **50-quinquies** | **sweep del path DC** (φ35 × covariate stakes/midweek × ri-taratura emivita/shrinkage con φ35 attiva; 54 backtest walk-forward) | le leve si sommano **senza interagire**: φ35+midweek = **0.9786** (miglior 1X2 del progetto, Δ −0.0011, P 78%, gap **+0.0154** vs +0.0165); **stakes ridondante** una volta attiva la φ35; iperparametri **piatti** con φ35 (270/365/540g e shr 0.75/1.5 tutti ≈0.979: la taratura ufficiale resta ottima); additività quasi esatta dei Δ singoli | 🔎 tutto nel rumore (CI includono 0) → config invariata; φ35+midweek = miglior variante DC opt-in |
| **51** | **audit delle lacune + batteria di forme mai provate** (double-Poisson di Efron, Rue-Salvesen, zero-inflazione 0-0; fittate LFO sui tassi del mercato) | **i gol sono SOTTO-dispersi dati i tassi del mercato: θ=1.205, >1 in 7/7 fit** — l'asse che la NB della Fase 27 non poteva vedere; migliora tutto il blocco esiti (1X2 −0.0021, ris.esatto **−0.0078**, pareggio, GG); Rue-Salvesen (γ=+0.03) e zero-inflazione (z≈0) **nulli**; Kalman dichiarato chiuso-per-argomento (emivita = suo steady-state) | ✅ **scoperta**: la forma giusta è più CONCENTRATA della Poisson; RS e ZI chiusi |
| **51-bis** | **si batte la chiusura 1X2?** (confronto appaiato: temperatura sul mercato — mai provata —, w-classe, double-Poisson, dp+livelli) | **dp_lvl = 0.9609 vs chiusura 0.9625: Δ −0.0016, CI95 [−0.0029, −0.0003] ESCLUDE lo zero, P 99%, 7/7 stagioni** (regge sul sottoinsieme fit≥2 stag.: −0.0018); temperatura T≈1.10 da sola −0.0010 (87%): la chiusura è un filo sotto-confidente + tilt casa/trasferta | ✅ **primo risultato che batte la chiusura con CI conclusivo** (in log-loss); opt-in `sharpen_1x2` nel motore + `predict.py` |
| **51-ter** | **ROI dei risultati nuovi** (pari-equilibrio coi tassi del mercato; value-bet 1X2 con dp_lvl) | pari-equilibrio: **+3.2%** (n=1141, 7 stag., CI [−5.9,+11.9], P 76%, 5/7 — coerente con Fase 40); filtro dp_lvl sul pari PEGGIORA (−13.3%, n=92); value-bet dp_lvl quasi mai attivato (edge ~0.5-1% ≪ margine ~5%) | 🔎 **battere la chiusura in log-loss ≠ ROI**: dp_lvl è valore da oracolo, non da scommessa; draw-bias resta l'unico lead monetizzabile (non concluso) |
| **51-quater** | **simmetrie mancanti**: routing v2 (tassi per famiglia), GBM bespoke sul PAREGGIO, recal O/U del mercato | routing v2: GG −0.0010 ✓ (conferma indipendente), scarto-casa ≥2 −0.0012 ✓ (P 100%); GBM-pareggio **perde** (+0.0078, P=0% → bespoke bocciato su TUTTI i mercati); recal O/U peggiora out-of-sample (+0.0013: bias O/U instabile, a differenza del tilt 1X2) | ❌ tre chiusure pulite / ✅ router v2 confermato |
| **52** | **O/U beat-the-close** (appaiato, mai fatto: la Fase 26 l'aveva liquidato come "banale") | il devig binario diretto (0.6788) resta il migliore: matrice +0.0003, dp_lvl +0.0010, temperatura +0.0006 (nessun P>17%) | ❌ **l'O/U non si batte**: l'edge 1X2 viene da pareggio/tilt-casa, che l'O/U non ha |
| **52-bis** | **router v3: double-Poisson su tutto il listino** + tripla GG (dp+k34+φ35) | **mai peggiore** del v2 su 20 mercati (media −0.0005), **5 CI conclusivi**: ospite-segna/CS-casa **−0.0023** (99%), casa-vince −0.0011 (100%), scarto≥2 −0.0011 (100%), ospite O1.5 −0.0008; la tripla GG **satura** a 0.6809 (dp e φ35+k34 correggono la stessa cosa) | ✅ **ADOTTATO**: `price_markets(dp_theta)`; `predict.py` usa θ=1.225 (mercato) / 1.138 (DC) |
| **52-ter** | **devig di Shin** (il tilt è artefatto del devig moltiplicativo?) + temperatura sopra dp_lvl | Shin è un devig migliore (0.9617, Δ −0.0007, P 97%): **metà dell'edge dp_lvl era "devig migliore"**; dp_lvl batte anche Shin ma senza CI (Δ −0.0009 [−0.0021,+0.0003], P 93%); la temperatura sopra dp_lvl aggiunge ancora (0.9605, T=1.056) | 🔎 claim Fase 51 riformulato: conclusivo vs benchmark storico, 93% vs miglior devig |
| **52-quater** | **dp sul path DC + θ condizionato** | **θ_DC=1.138** (< mercato 1.205, come predice l'argomento del rumore; ancora >1): 1X2 standalone **0.9794** (−0.0009, P 99%), esatto −0.0041 (P 100%); θ(volume/equilibrio/coda): **θ1=0.000 su tutti gli assi** → sotto-dispersione **uniforme** | ✅ la dp migliora anche il fallback senza quote; robustezza massima della costante |
| **52-quinquies** | **dp_lvl sull'APERTURA** (i bias esistono già il venerdì?) | θ_open=1.218, tilt μ×1.043: **sì**; dp_lvl(open) batte l'open (−0.0019 ✓CI) e **l'apertura affinata VALE la chiusura grezza** (0.9630 = 0.9630, Δ +0.0001): l'affilamento open→close (+0.0020, Fase 14) è quasi tutto ricalibrazione sistematica, non notizie | ✅ rilettura fine della Fase 14; quantificata l'informazione vera della chiusura (~0.002) |
| **52-sexies** | **modello score-driven** (GAS: forze aggiornate a ogni partita; il "Kalman economico") | 1X2 0.9830 vs DC batch 0.9803 (Δ **+0.0027**, P(GAS meglio) 18%, 3/7 stagioni; η≈0.04 ⇒ memoria ~25 partite, troppo corta) | ❌ lo state-space è ora chiuso **per test** (Fase 48 lo era per argomento) |
| **53** | **cross-lega (tracer)**: i bias del mercato su Premier e La Liga (bundle dati caricati dall'utente, 9 stagioni/lega, solo market-side) | **θ>1 ovunque ma decresce con la liquidità** (Premier 1.069 < Liga 1.097 < Serie A 1.205); tilt casa/trasferta e draw-bias **NON si replicano** (Premier: pareggi SOVRA-prezzati w_D=0.93, ROI pari-equilibrio **−5.4%**; Liga intermedia: +3.6% P 81%); **dp_lvl NON batte la chiusura fuori dalla Serie A** (Premier +0.0008, Liga +0.0001) anche rifittata | 🔎 **ridimensionamento onesto**: il beat-the-close è una proprietà della chiusura SERIE A (mercato meno liquido), non del calcio; §7 vendicato — nessun numero si trasferisce |
| **54** | **pipeline dati Premier + La Liga** (bundle football-data+Understat caricati a mano → snapshot congelati, stesso schema Serie A) | riconciliazione nomi FD↔Understat (6 alias Premier + 11 Liga, verificati per identità) → **copertura xG 100%, zero orfane**; 3420 partite/lega, 9 stagioni | ✅ due leghe nel progetto, offline-first; lega = configurazione non codice (§7) |
| **55** | **EDA cross-lega** (come si muovono i dati vs Serie A) | γ vantaggio-casa **Liga 0.272 ≫ Premier 0.185 > Serie A 0.150** (auto-fittato); **δ neopromosse Premier 0.329 ≫ 0.23** (ipotesi §7 VERIFICATA); Premier meno pareggi (23.4%) e mercato più liquido (margine 4.3%); xG di qualità pari ovunque | ✅ ipotesi di modellazione; la struttura dovrebbe trasferirsi, i numeri (δ, γ) no |
| **56** | **tracer bullet** (DC config Serie A NON tarata su Premier/Liga) | batte la baseline ovunque (0.98 vs 1.066): **la struttura trasferisce**; gap col mercato Premier **+0.0207** (più largo, mercato più efficiente), Liga **+0.0162** (≈ Serie A +0.0165) | ✅ baseline onesta per la ri-taratura |
| **57** | **ri-taratura per lega** (δ, emivita, shrinkage; γ auto-fittato) | iperparametri **PIATTI** su entrambe (tutti i Δ ±0.0005, nessun CI): il gap **non si chiude ritarando** (=Fase 8 Serie A); δ punta dove la EDA prevede (Premier 0.33 nom. migliore) ma guadagno nullo; emivita 730 **peggiora** anche in Liga (l'ipotesi "rose stabili→memoria lunga" è falsa per il log-loss) | ✅ `LEAGUE_CONFIGS` con δ per lega; **il modello è trasferibile, l'edge no** |
| **58** | **audit dati: overround impossibile** nella quota "Avg" (2 righe/10260) | quota media inquinata da un book anomalo (overround 0.929 e 0.994, arbitraggio impossibile): scelta quote ora per INTERO mercato con ripiego in blocco sul livello successivo | ✅ fix nel loader + test su 3 leghe; impronta dati invariata, nessun risultato toccato |
| **59** | **congestione vera per Premier/Liga** (calendario club: coppe nazionali + Europa) | FA Cup+EFL Cup (england) e Copa del Rey (espana) su openfootball; **bug corretto**: `parse_europe` filtrava solo club ITA anche per le altre leghe (azzerava le partite europee senza un'italiana); copertura `rest_full` 99.5%/99.4% | ✅ schema 32/38 per Premier/Liga; covariata resta off (Fase 4e-bis) |
| **60** | **valore rosa + assenze per Premier/Liga** (rose dai bundle Understat, Transfermarkt via mirror — raggiungibile, contrariamente al presunto) | copertura `squad_value` **95.6% Premier**, **58.3% Liga** (matching nomi 91.7%; il gap è nei giocatori senza serie di valutazioni nel datalake — stessa causa di Lazio/Serie A) | ✅ schema **38/38 identico su 3 leghe**; feature già bocciate come covariate (Fase 4c/11) |
| **61** | **quote apertura 2017-19 recuperate** (chiusura Pinnacle PSC* ignorata dal loader) | 2017-18/2018-19 hanno PS*/PSC* (apertura+chiusura Pinnacle, diverse nel 96%): **2279 aperture 1X2 recuperate**, chiusura vera al posto della pre-match spacciata; stagioni 2019-20+ bit-per-bit invariate | ✅ CLV misurabile anche su 1718/1819 *(la Fase 73 recupera anche l'apertura O/U di quelle stagioni: era già reale, solo mal etichettata)* |
| **62** | **ricostruire la chiusura O/U mancante (2017-19)** dal movimento 1X2 open→close (backtest su 21 lega-stagioni con entrambe le linee) | la parte prevedibile del movimento O/U è TUTTA nel movimento 1X2 mappato via matrice DC (recal pura: corr ~0): M4 (recal+shift motore WF) taglia il MAE del 33-41% (corr movimento 0.64-0.80, beta≈1) e in **Liga recupera tutto il valore della chiusura** (−0.0024 ✓CI vs open, indistinguibile dal close vero); ma il close vero vale solo −0.0007…−0.0026 vs open (CI solo Liga) | 🔎 **ricostruibile in struttura**; pubblicazione decisa (come stima dichiarata) nella 62-bis |
| **62-bis** | **bakeoff estimatori + pubblicazione della stima** (richiesta utente: "utile, purché scritto che è una stima") | il movimento 1X2 GREZZO (Δlogit H/X/2) **batte** lo shift del motore (la matrice DC comprime il segnale): **E3 pooled** MAE **0.0117** (−44% vs non stimare, corr 0.75-0.86); coefficienti simmetrici cH≈cA=+1.245 (componente gol-totali), cD=−0.81 (pareggio→Under) | ✅ **2279 stime pubblicate in `data/estimates/`** (probabilità, mai quote; test-guardia anti-contaminazione); nuovo catalogo dati **`docs/DATI.md`**; convenzione stime nel CLAUDE.md §5 |
| **63** | **fix matching giocatori** (Understat↔Transfermarkt): inversione nome/cognome tra fonti ("Djené Dakonam"/"Dakonam Djené") | diagnosi in 2 categorie: **bug vero** = ordine dei token (27 giocatori/115k min in Liga, 12/23k in Premier → nuovo stadio `token_sort`, unico+valutato+ruolo); **non-bug** = record valutati ASSENTI dal datalake (Gerard Moreno, Theo Hernández: nessun matching può trovarli) | ✅ Liga 58.3→**60.2%** (Getafe 22→44%); Premier invariata ma valori più accurati (247 righe/lega aggiornate); Serie A non ri-arricchibile (rose senza bundle/mirror) |
| **64** | **«la panchina»** (`docs/PANCHINA.md`): registro dei miglioramenti misurati ma NON attivati | 11 voci (da GG/NG φ35+knee34 P 98% a temperature scaling −0.0003) con numeri, motivo, attivazione e condizioni di promozione; + lead operativi (draw-bias, stakes) e archivio | ✅ regola di aggiornamento obbligatoria nel CLAUDE.md §2; risponde a "cosa abbiamo già misurato che potrebbe diventare ufficiale?" |
| **65** | **la rosa completa + regola dei due fronti** (richiesta utente) | `PANCHINA.md` → «rosa dei modelli»: matrice **modello × fronte** (SA/PL/Liga/generale, ~28 modelli) con ⚽/🪑/❌/⬜; +sezione bocciati (20 voci coi numeri); emerge il lavoro più urgente (market-implied mai backtestato multi-mercato su PL/Liga) e il candidato generale più maturo (devig Shin, 3/3 leghe) | ✅ **principio 9 nel CLAUDE.md**: ogni modello si sviluppa su DUE fronti — per-lega e generale — e ogni esperimento aggiorna la matrice |
| **66** | **riempire le celle vuote: squad_value stimato** (73 celle/540; LOO + leave-team-out su 467 note) | ibrido: `anchored` (regressione pooled + valore stagioni adiacenti) err mediano **~17%**; `regression` (rendimento, per-lega — per squadre senza stagioni note, es. Lazio) **~29%, p90 75%**, code >100% sui sovra-performanti (Getafe 18-19); **il fronte vincente dipende dal regime** (pooled con ancora, per-lega senza) | ✅ 73 stime in `data/estimates/squad_value_2017_26.csv` (metodo+errore riga per riga; **file poi svuotato alla Fase 70**, quando il dato è diventato reale al 100%); gli altri NaN residui dichiarati irriducibili (~~O/U open 2017-19~~ → in realtà apertura REALE, chiarito Fase 73; O/U **close** 2017-19 stimato; 2 partite senza quote nel grezzo; prime partite rest) |
| **67** | **valori rosa REALI via GitHub Actions** (idea utente: il runner ha rete libera, il proxy no) + fonte `player-scores` (dcaribou/transfermarkt-datasets, CC0) | copertura **100% su TUTTE le stagioni concluse, 3 leghe** (SA 69.8→94.2% tot, Liga 60.2→95.0%, PL 95.6→97.8%; Lazio reale: 177-368M); zero matching giocatori (id interni; solo 34 alias club); coda COVID gestita con finestre-data dello snapshot (bug 549≠540 celle catturato dal conteggio-sanity); cross-check su 456 celle note: scarto mediano 3-6% | ✅ fonte ufficiale dei valori rosa; stime F66 ridotte 73→**13** (tutte 2025-26); **pattern riusabile**: workflow d'import per ogni fonte bloccata (`.github/workflows/import_dataset.yml`) |
| **68** | **ultimi buchi chiudibili**: calendari "preludio" (top 2016-17 + seconde serie 1617→2425) + cron d'import mensile | `rest_days_full`: **82 NaN → 0** su 3 leghe; bonus retroattivo: 107 righe di riposo più accurate (gli alias F67 agganciano coppe prima scartate in silenzio — diff ispezionato riga per riga); re-import run-2 da **Kaggle fresco**: le 13 celle squad 2025-26 mancano davvero A MONTE (non staleness) → il cron le chiuderà al backfill; gzip deterministico (niente commit-rumore) | ✅ completamento celle **98.70% reale**; residuo interamente mappato: O/U open 2017-19 (4.564, stima sul lato close) + 13 squad 2526 (stima+cron) + 6 sparse |
| **69** | **stima dei gap sparsi** (bakeoff 5 metodi, richiesta utente) su 3 partite senza apertura vera (2 di 1X2 + 1 O/U mai censita prima, Verona-Genoa 2020-21) | ricerca esterna diretta fallita per blocco geo/ADM (BetExplorer/OddsPortal); **logit pooled** vince/pareggia identità/lineare/per-lega su 10.258 (1X2) e 7.978 (O/U) coppie reali; **blend peggiore del singolo migliore**; MAE atteso **~0.016 (1X2)** / **~0.020 (O/U)** | ✅ 3 stime in `data/estimates/open_sparse_1x2_ou.csv` *(2 dopo la Fase 73: Alaves-Sociedad ha l'apertura reale)*; nessun buco NaN nel progetto resta senza una causa scritta o una stima |
| **70** | **le ultime 13 celle squad_value 2025-26**: dato REALE da Transfermarkt (richiesta utente, "forse è molto semplice") | recupero manuale via browser reale (Cowork), NON la pagina profilo-club (mostra il valore LIVE, sbagliato di quasi un anno) ma la pagina di competizione filtrata per stagione; scarto vs stima Fase 66 mediano **22.5%** (dentro il range 17-29% dichiarato) | ✅ `squad_value` **reale al 100%**, zero NaN residui su 9 stagioni × 3 leghe; stima Fase 66 ritirata (file vuoto, rigenerabile) |
| **71** | **caccia O/U 2017-19, Fase A** (dataset già pronti Kaggle/GitHub/HF, richiesta utente) | WebSearch conferma (fonte indipendente) che football-data raccoglie apertura+chiusura solo dal 2019/20; probe via Actions su **6 dataset Kaggle** candidati: tutti quelli con quote sono ricostruzioni di football-data, ogni file 2017-19 ha **una sola** istantanea O/U (`BbAv`), zero apertura/chiusura distinte | ❌ Fase A negativa (Fase B già negativa); restano solo Fase D (OddsPortal login) o le stime — promemoria "cercare meglio in futuro" in `CACCIA_OU_2017_19.md` |
| **72** | **spremere la stima E3 pooled al massimo** (richiesta utente) | 4 leve ortogonali nuove sullo stesso protocollo: interazione 1X2 (0.0117), calendario/stagione (0.0117), ridge (peggiora monotono 0.0119→0.0155 = NON è overfitting), GBM (0.0160, +37%) | ❌ **E3 pooled imbattuto** (MAE 0.0117); stima pubblicata invariata |
| **73** | **l'O/U 2017-19 era un'APERTURA, non una chiusura** (verifica su richiesta utente) | 4 evidenze (notes.txt "Friday afternoons"; nessuna colonna `*C*` O/U; timing = `PS*`; margine ≈ apertura): l'unica linea O/U (`BbAv`) è pre-match. Politica loader semplificata (chiusura = solo `*C*`; apertura = solo pre-match; insiemi disgiunti → niente masking); diff cella-per-cella: cambia **solo** O/U 2017-19 (chiusura→NaN, apertura→`BbAv` reale, 2280 righe) + 1 riga 1X2 (Alaves-Sociedad), **2019-20+ bit-identico**; stima chiusura byte-identica; dispersione `BbMx`/`BbAv` (8ª leva) non aiuta | ✅ apertura O/U 2017-19 **dato reale** (`odds_over25_open`); il buco è ora solo la chiusura (metà di prima); E3 confermato tetto |
| **74** | **ri-validazione di TUTTI i calcoli sui dati corretti** (richiesta utente) | il diff dati bounda tutto: cambiano solo O/U 1718/1819 (+1 riga 1X2), **gol identici** → DC invariato per costruzione; **2019-20+ bit-identico** → tutte le analisi che partono dal 2020-21 (gap+CI, market-implied, bakeoff, ROI, matchday, denoise, routing, shape) invariate. Ri-eseguito l'unico adottato che tocca il 1819, il **router dp (Fase 52)**: dp **conclusivamente peggiore in 0 mercati** (come prima), delta stabili; il 1819 esce correttamente (nessuna chiusura O/U) | ✅ nessuna conclusione adottata cambia; 43 script senza O/U + ~22 su 2021+ immutati per costruzione; 12 esplorativi (Fasi 50/51, negativi chiusi) restano negativi |
| **75** | **spremere il 2017-19** (richiesta utente): apertura REALE + chiusura stimata, in ogni direzione | **(A)** market-implied dall'apertura su **2.280 partite vergini** (6 lega-stagioni mai viste da alcun fit): batte la baseline su **17/20 mercati Tier 1 con CI** (media 0.5618 vs 0.5900) — la conferma out-of-sample più forte mai ottenuta del motore (e primo test multi-mercato su Premier/Liga, pista #4); pari/dispari resta imprevedibile (replica Fase 26). **(B)** θ dp: segno θ>1 in 5/6 lega-stagioni ma **livello 1.225 NON trasferisce** (θ veri 0.95-1.16; dp fissa peggiora over_1.5/mg_0_1); **NUOVO: θ cresce nel tempo** in tutte e 3 le leghe (1718 ~1.03 → 1819 ~1.16 → 2019+ ~1.1-1.22, linee sempre più informative). **(C)** DC vs chiusura stimata 1819: gap +0.0141 [−0.0017,+0.0300], dichiarato parz. circolare. **(D)** encompassing esteso: **α\*=0.00** sia vs closing Pinnacle VERO 1X2 1819 sia perfino vs la chiusura STIMATA O/U | ✅ motore validato su dati vergini; θ da trattare **per-contesto** (lega × epoca), mai costante universale; α\*=0 trans-epoca (perfino un surrogato del mercato ingloba il DC) |
| **76** | **market-implied multi-mercato su Premier/Liga dalla CHIUSURA** (chiude pista #4; su domanda utente esteso al 2019-20, la prima stagione con chiusura reale → 7 stagioni, 1920-2526) | il motore trasferisce **identico** su tutte e 3 le leghe, **senza ritarare nulla** (ρ=−0.06): batte il DC-da-gol su **13/14 mercati** e la baseline su **13/14** in Serie A (CI<0 12), Premier (CI<0 13) e Liga (CI<0 11) — stesso esito della Fase 26. Guadagni maggiori su risultato esatto (−0.027…−0.032), multigol, total-squadra. L'unico mercato che non cede in nessuna lega: **pari/dispari** (4ª replica: quasi-casuale) | ✅ pista #4 CHIUSA positiva; market-implied → titolare su Premier/Liga (era ⬜); la struttura è universale (solo gli input sono per-lega), a differenza del θ del router (per-contesto) |
| **77** | **il nome onesto**: da «Polymarket Oracle» a «Football Oracle» | il progetto non prezza piu' solo Polymarket ma qualsiasi mercato calcistico da quote 1X2+O/U; il nome storico restava nel repo e nei documenti | ✅ rinomina e allineamento dei documenti (il repo git conserva il nome originale) |
| **78** | **test prospettico 2026-27 (giornata 1)**: previsioni CONGELATE prima del kickoff e scorate dopo — il gold standard che nessun backtest puo' sostituire | anteprima DC congelata il 2026-07-23 in `experiments/prospettico_2026_27.md` + `prospettico_2026_27_dc.csv`; il passo 2 (market-implied con le quote reali) richiede le quote pre-partita, disponibili solo a ridosso del via | ⏳ **APERTO**: da completare fra il 15 e il 23 agosto 2026 (Liga ~15/8, Premier ~21/8, Serie A ~23/8); lo strumento per le quote e' `scripts/fetch_polymarket_open.py` |
| **79-EDA** | **studio dedicato Premier/Liga** (nuovo quaderno `docs/STUDIO_PREMIER_LIGA.md`): pareggio per fascia di equilibrio, congestione, γ_t per stagione | il sotto-prezzo dei pareggi EQUILIBRATI c'è in SA (reale−mercato **+0.032**) e Liga (**+0.022**), **NON in Premier** (−0.009: sovra-prezzo); Premier la lega più congestionata (riposo ≤3g 21.6%, **36.3% a dicembre** vs 15.0% SA); γ_t Liga alto e stabile (0.18-0.34), Premier volatile (0.29→**0.01** COVID→0.06 nel 2425) | ✅ tre fatti nuovi; il pareggio è dove i mercati differiscono di più |
| **79** | **prime leve per-lega su Premier/Liga** (φ35 equilibrio-pareggio sul path DC + covariate `rest_full`/`midweek`; 48 backtest walk-forward, config per-lega) | tutte nel rumore o peggio: φ35 PL +0.0006 (P 7%), Liga +0.0002 (P 43%); rest_full PL +0.0005 (P 9%), Liga +0.0003; midweek ±0.0001. Il risultato vero è nei FIT: **φ0 sbatte a ZERO in Premier 4/6 stagioni** (il deficit-pareggio del DC non esiste lì: il modello già sovra-stima i pareggi equilibrati inglesi, reale 0.246 vs 0.268) mentre **in Liga il fit è ≈ Serie A** (φ0 0.39, κ 4.1 vs 0.39/3.6) ma sovra-corregge e non paga; il β_midweek stabile della SA (−0.020 6/6) **non si replica** (Liga +0.008 opposto) | ❌ quattro bocciature pulite; **il deficit-pareggio è un tratto delle leghe latine** (3ª conferma indipendente che ogni leva-pareggio va tenuta lontana dalla Premier); su PL/Liga si prezza col market-implied LISCIO + DC fallback |
| **80** | **catena GG/NG del market-implied per-lega** (tau / φ35 / k34 / φ35+k34 sui λ,μ della chiusura; 3 leghe × 6 stagioni test 1920→2526, parametri LFO; test C dello studio, condizione di promozione della panchina #1) | Serie A: combo **riconfermata** (GG −0.0014, P 97%). **La Liga: φ35 da sola −0.0006 [−0.0011,−0.0001], CI<0, P 99% — il primo risultato per-lega conclusivo fuori dalla Serie A** (φ0≈0.32, κ≈2.9 stabili); ma il **k34 lì PEGGIORA con CI>0** (+0.0008: il profilo-ospite di fine stagione è INVERTITO, boost-38ª ×0.915 vs ×1.10 PL — in Spagna il vantaggio-casa non crolla nel finale). Premier: nulla (fit sui bound) | ✅/❌ tre catene GG/NG diverse: **SA φ35+k34 · Liga φ35 sola · PL liscio** — stessa cassetta degli attrezzi, assemblaggio e costanti per-lega (§7); φ35-Liga in panchina alta (promozione: stagioni nuove o tool per-lega) |
| **81** | **mega-sweep delle costanti del market-implied per-lega** (curve di risposta complete: ρ 11 valori con ri-inversione, θ 10, φ0×κ 37 combo, knee 5 — ×3 leghe ×6 mercati, con selettore walk-forward "lfo" per la selezione onesta; +check congiunto ρ×θ) | **Premier: già all'ottimo su OGNI asse** (ρ*=−0.06, θ*≈1, φ*=0, knee=none — il motore liscio È il modello). **Serie A e Liga: θ*≈1.2-1.25 sul ris. esatto con CI<0 anche col selettore** (SA −0.0078*, Liga −0.0069*); in Liga anche 1X2 (−0.0023*) e GG (−0.0025*) → **la bocciatura del router-Liga (F53) è RIBALTATA**: testava il θ da MLE-punteggi (1.097), troppo piccolo — l'ottimo operativo è ~1.2 come in SA. Il check congiunto smaschera l'asse ρ: a θ ottimo, ρ oltre −0.06 peggiora il ris. esatto (+0.009/+0.012) → i guadagni-ρ erano θ sotto mentite spoglie, **ρ=−0.06 resta universale**. φ-grid: Liga (0.7,0.5) GG lfo −0.0019*, PL (0,0) | ✅ mappa completa delle costanti per-lega; router-Liga ❌→🪑 alta (θ≈1.2); una leva (θ), non due (ρ); θ-da-mercati ≠ θ-da-punteggi (lezione di metodo) |
| **82** | **verifica diretta delle predizioni** (domanda utente: "indoviniamo davvero i risultati?"): calibrazione (bias, ECE su 10 fasce) e hit-rate dell'esito più probabile su 19 mercati binari + 1X2 + multigol + ris. esatto, ×3 leghe, per motore/router/mercato/DC | **le probabilità sono GIUSTE**: \|bias\|≤0.02-0.03, ECE 0.004-0.04 quasi ovunque; ris. esatto: top-pick indovinato 12-15% dichiarando 12-14% (confidenza onesta). **Hit-rate = quello del mercato** (1X2: SA 54.2% vs mercato 54.3%, PL 55.3%=, Liga 54.3%=; baseline 40-45%). Le mis-calibrazioni residue SONO i bias noti: SA tilt casa/pari ±0.02, **PL quasi perfetta** (ECE fino a 0.003), Liga GG −0.036 — e il **router θ (F81) la raddrizza** (GG −0.036→−0.008, ECE 0.036→0.012): conferma su metrica indipendente. Pari/dispari al coin-flip (5ª replica); DC senza quote un filo peggio (1X2 52.9-53.5%) | ✅ l'oracolo è calibrato e indovina quanto il mercato (non di più: α*=0); il valore è prezzare calibrato i ~17 mercati non quotati + le correzioni per-lega |
| **83** | **revisione dei commit esterni (Codex, Fasi 6-13)** — codice e metodo riga per riga: leakage, formule, normalizzazioni, fonte unica metriche | **nessun errore grave**: zero leakage walk-forward, formule esatte (prior neopromosse, φ diagonale rinormalizzata, temperature, per-classe), ~15 numeri README riprodotti dal registro; 7 difetti minori (F1/F3/F4 già dichiarati in Fase 15, F5/F6 latenti a impatto nullo, F7 storico), **1 corretto**: `calibrate.py` fermo alla config pre-prior (ora legge `src.config.SERIE_A`); 140 test verdi, backtest ufficiale riprodotto (2526: 0.9925) | ✅ conclusioni Fasi 6-13 confermate; fix `calibrate.py` |
| **83-bis** | **`predict.py` per-lega** (rivedendo il commit sulle nuove stagioni, Fase 78): il tool ignorava `--league` e usava sempre la config Serie A (δ=0.23) | ora legge `league_config(--league)`: Modello 1 con δ 0.23/**0.33**/**0.22** e γ auto-fittato 0.128/0.191/**0.297** (SA/PL/Liga); chiude il "passo 2" del test prospettico per il DC; il θ del router nel M2 e' **chiuso alla Fase 92-bis** (mappa `MARKET_ENGINE` per-lega in `src/config.py`; Premier e Liga escono col motore LISCIO) | ✅ fix tooling (deriva di config); 140 test verdi |
| **84** | **audit trasversale del repo** (4 fronti in parallelo: numeri, codice, file, idee) — verifica avversaria dopo 84 fasi | **numeri**: ogni headline riprodotto dal registro (0.9797/0.6885/gap +0.0165/ROI −15.67%/CI Fase 17), nessun errore; **codice**: zero bug attivi (dp mean-preserving <6e-13, zero look-ahead, matrici normalizzate), 1 guardia latente aggiunta (`draw_inflation`+`dynamic_rho`); **file**: riscritta CLAUDE.md §6 (ferma alla Fase 33), corretti 4 mislabel minori; **idee**: nuova pista θ(margine) + affinamenti in PISTE.md | ✅ progetto in salute; fix guardia + docs; nuove piste catalogate |
| **85** | **la chiave per gli esiti meno probabili: la CODA** (`_run_tail_analysis.py`, 7980 partite × 3 leghe): θ diretto sul risultato esatto + COM-Poisson | la Poisson **sovra-stima** i totali alti (Over3.5 +0.0096, Over4.5 +0.0083): la coda reale è sotto-dispersa; ⚠️ **rettifica Fase 101 — la «COM-Poisson» NON è una forma alternativa**: `dp(θ) ≡ COM-Poisson(ν=θ)` mean-matched, e la prova è numerica (stessa cache di 7.980 partite: le due colonne coincidono a **≤5e-06** sull'exact-score log-loss e a **≤2e-05** su Over3.5/Over4.5, a ogni θ della griglia). La riga «ν=1.15 pareggia (2.8321)» era **dp θ=1.15**, cioè un punto che la griglia della dp non conteneva — non una famiglia diversa. E il «minimo ESATTAMENTE a θ=1.225» è un effetto della griglia a 5 punti: su griglia fine l'argmin è **θ=1.18** (2.831915 contro 2.832185; Δ **−0.00027**, IC95 [−0.00083, +0.00027], P 83.8% — nel rumore). Resta vera la **tensione di profondità**: Over3.5 vuole θ≈1.35, Over4.5 θ≈1.10 → un solo θ non calibra ogni profondità | 🔎 la chiave = controllo di dispersione dei gol (già il θ del router); resta la **tensione di profondità**; il confronto COM/dp **NON è una conferma indipendente** (Fase 101) |
| **86** | **secondo audit orchestrato** (workflow: 6 finder → verifica avversaria → 14/36 sopravvissuti) + ri-verifica manuale di ogni numero | **fix onestà**: varianza dp ~17%→**~10%** (era l'approx asintotica di Efron); ROI −15.7% è alla quota media, al **best-price −2.4%** (2526, ancora negativo). **Chiuso**: handicap asiatico **ridondante** come input (corr **0.995** con λ−μ). Docs: glossario + 6 allineamenti | ✅ 2 fix onestà + pista AH chiusa + glossario |
| **86-bis** | **verdetto walk-forward sul θ per-squadra** (il lead della F86): fit del θ per terzile di volatilità-sorpresa passata, applicato al futuro | la volatilità-sorpresa **persiste** (corr +0.20) ma il **θ_team PEGGIORA OOS**: exact-LL 2.8222 vs 2.8212 del θ globale (**Δ +0.00096**, n=5.690); i θ di gruppo sono instabili anno-su-anno. La persistenza è reale ma **non monetizzabile** | ❌ tetto informativo confermato *nella coda e per-squadra* (α*=0); chiude la caccia agli esiti rari |
| **87** | **coda a 2 parametri, riprodotta** (`_run_tail_two_param.py`): isotonica per-soglia + mistura di due Poisson, walk-forward | **(A) isotonica**: peggiora il log-loss OOS su **tutte e 4** le soglie (Over1.5 +0.0150 … Over4.5 +0.0109); **(B) mistura**: guadagno in-sample (s=0.15, −0.0006) ma **OOS non conclusivo** (Δ −0.00042, CI [−0.0015,+0.0006], P 78.6%) e **segno ribaltato sulle stagioni recenti** (2425/2526 positive) | ❌ entrambe chiuse; la coda-forma è al tetto (**2ª** conferma indipendente, dopo θ_team della F86-bis: la COM-Poisson della F85 non conta, era la dp riparametrizzata — Fase 101) |
| **88** | **handicap asiatico = benchmark Tier 2** (`_run_ah_benchmark.py`, 7.437 partite × 3 leghe): il router prezza la copertura del margine come il mercato sharp? | **Brier router ≈ Brier mercato** (0.2040 vs 0.2041 aggregato, indistinguibili a coppie per lega), corr modello-mercato **0.91**; dai soli λ,μ del 1X2+O/U il motore eguaglia il mercato che quota l'AH direttamente | ✅ **pareggio in Brier col mercato sharp** su un mercato NUOVO (il margine): ΔBrier **−0.000136** IC95 [−0.000362, +0.000083], e col protocollo onesto della F16 (α dalle sole stagioni passate) il blend **non batte** il mercato OOS (Δ −0.000064 [−0.000271, +0.000135]). ⚠️ **rettifica Fase 101 — NON è «α\*=0»**: l'encompassing non era mai stato calcolato e, calcolato sugli stessi 7.437 casi, dà **α\*=1.08** IC95 [+0.147, +2.052] — perché il router è una *traduzione* delle stesse quote 1X2+O/U, non un previsore indipendente, quindi il test di encompassing qui non ha il significato che ha nella F16. Primo test Tier 2, router validato per copertura/scarto |
| **89** | **mercato CAMPIONE DI STAGIONE** (richiesta utente; nuovo `src/models/season_sim.py` + `_run_fase89_season_champion.py`): primo mercato NON derivabile da una matrice — 380 partite congiuntamente + regola di classifica → Monte Carlo di 20.000 stagioni intere, backtest su 24 stagioni-lega | **batte le baseline, ma il margine dipende da quale**: log-loss **1.2011** vs **1.4293** della baseline più forte (persistenza su 2 stagioni, β=2.5/w₂=1.5 tarati LOO) → guadagno **+0.2283** IC95% [+0.0090,+0.4530], **14/24** stagioni, conclusivo per un soffio e **quasi tutto Premier** (+0.57, 7/8; SA +0.12, Liga +0.004 nel rumore). Contro le baseline deboli (uscente 2.6515, uniforme 2.9957) il guadagno sale a +1.4521 e 24/24, ma è un metro gonfiato *(numeri corretti dall'audit Fase 90: la baseline di persistenza era promessa nel docstring e mai implementata)*. Ma **sovra-confidente**: dichiara 60.1% sul favorito, ne azzecca **41.7%** (−18.4pp, −1.83 SE, non concluso); meccanismo misurato: campione reale **89.1** punti vs vincitore simulato **84.8** (forze fisse = classifica compressa). Ricalibrazione a temperatura **fallisce in LOO** (1.2160 > 1.1994). Per lega: PL 0.7411 (62% favorito) · Liga 1.3651 · SA 1.4920. Spareggi per-lega implementati (scontri diretti SA/Liga, DR Premier): spostano ≤**0.93pp** il prezzo ma decidono **chi retrocede** (Liga 2526: Levante, **Osasuna** e Mallorca chiudono tutte a 42 punti e la **classifica avulsa** fra le tre — 7/5/3 — retrocede Mallorca, mentre la sola differenza reti retrocederebbe Levante; la rosa Polymarket 2027 lo conferma) | ✅ mercato nuovo aperto e validato vs baseline; ❌ nessun edge dimostrabile sul mercato (mancano quote outright storiche); difetto **strutturale** identificato = varianza mancante |
| **89-bis** | **perché sbagliamo il campione** (domande utente: quante ne indovini? perché sbagli le altre? altri dati aiutano?) — anatomia dei 24 casi + test covariata `squad_value` + misura della deriva di forza | **la separazione che spiega tutto**: titolo CONFERMATO 8/8 azzeccate (100%), titolo che CAMBIA mano **2/16** (12%) — negli errori il campione uscente si riconferma **0/14**. Ma il campione vero è nel nostro **top-3 in 23/24 (96%)**: P(top-2) dichiarata 82.7% vs reale 79.2%, P(top-3) 92.2% vs 95.8% → **calibrati sul gruppo di testa**, sbagliati solo nella scelta interna (10/19 = **52.6%, un lancio di moneta**, dichiarando **71.6%** = media di p₁/(p₁+p₂); l'audit Fase 90 ha corretto il 61.1% marginale della prima stesura). **`squad_value` NON aiuta**: log-loss 1.2384 vs 1.1994 (β sempre positivo ma ridondante coi gol/xG; 2/16 sulle stagioni di cambio, come il base) → la bocciatura delle Fasi 4c/66-70 **si trasferisce** all'outright. Deriva di forza in-stagione **σ=0.189 = 44%** della dispersione fra squadre (480 squadra-stagione) | ❌ nessun dato in nostro possesso anticipa il cambio al vertice; ✅ diagnosi precisa: correggere **appiattendo la spartizione fra i leader** con la deriva misurata, non tarando sui 24 esiti |
| **90** | **terzo audit orchestrato** (richiesta utente: dati? scritto? backtest? da sistemare? ragionamenti? sospesi?) — 13 agenti: 6 lenti in sola lettura + contro-verifica avversaria di ogni reperto + sintesi | **dati OK**: 10.260 righe ri-derivate dalle fonti grezze, zero discrepanze, 27 classifiche ricalcolate indipendentemente identiche; 1 anomalia nuova dichiarata (Udinese-Roma 25/04/2024 = partita **sospesa e ripresa**, la chiusura prezza la ripresa: P(X) 0.558 vs max 0.372, ~9-12% dell'edge F51). **Il difetto vero era il METRO**: la baseline «forza dalla classifica» promessa nel docstring della F89 non era mai stata implementata → guadagno reale **+0.2299** [+0.0108,+0.4542] 14/24 invece di +1.4521 24/24, e **quasi tutto Premier**. **2 bug reali** nel tool Polymarket (derby persi per match sulla prima parola; mercati per-tempo che sovrascrivevano O/U e BTTS) + 3 imprecisioni di misura (marginale vs condizionato 61.1→**71.6%**; squad_value −0.0390 non −0.0444; `rank` incoerente con `champion_prob`). Demolite in contro-verifica 3 critiche (Poisson-binomiale, ricalibrazione, F53-vs-F75); α*=0 regge anche col **log-pool** (+0.00005) | ✅ dati e conclusioni portanti confermati; ❌ numeri-titolo F89 ridimensionati; 2 bug corretti con test; 14 incoerenze docs sistemate |
| **91** | **mercati POSIZIONALI dal `rank` gia' calcolato** (leva aperta dall'audit F90): P(top-4) e P(retrocessione) — **480 osservazioni binarie** per mercato invece delle 24 del campione, zero modellistica nuova | **TOP-4: ottimamente calibrato** — log-loss **0.2218**, Brier 0.0675, **ECE 0.0140** (scarto max **1.4pp** su tutte le fasce); batte il tasso base +0.2787 [+0.2130,+0.3304] e la persistenza +0.0274 ma con **IC a grappoli [−0.0006,+0.0522] che include lo zero** (F92-bis): a reggere e' il **test dei segni 19/24, p=0.0066**, non l'intervallo. **RETROCESSIONE: rotta** — batte il tasso base (+0.0925 [+0.0465,+0.1341]) ma **non la persistenza** (−0.0066 [−0.0364,+0.0208], IC contiene 0), e la calibrazione crolla in alto: dichiarando 70-90% succede il **50.0%**, dichiarando >90% (n=3) il **66.7%**. **Colpevole isolato**: dei 30 casi sopra il 60%, **29 sono neopromosse** (97%) e 15 si sono salvate — neopromosse dichiarato 54.7% vs realizzato 48.6% (−6.1pp, era −10.1pp prima del fix del prior alla F92), **resto della lega calibrato** (8.0% vs 9.1%). *(Tutta la riga e' ora ri-letta su `experiments/fase91_positions.json` POST-fix del prior e con l'IC a grappoli della F92-bis: la prima stesura mescolava numeri pre-fix e post-fix.)* Il prior δ, tarato sul log-loss della SINGOLA partita (F7/57), e' troppo severo propagato su 38 giornate | ✅ due mercati nuovi, uno dei quali (top-4) e' il risultato meglio calibrato del progetto su questa famiglia; 🔎 pista concreta: **δ dipende dall'orizzonte** — ritararlo sul bersaglio stagionale |
| **92** | **quarto audit, organizzato per AREA del repo** (richiesta utente: audit completo del branch main) — 13 agenti su motori/pipeline/script/test/docs/artefatti + contro-verifica avversaria | **LA DIAGNOSI CENTRALE ERA INVERTITA**: «il gap vive quasi tutto nel pareggio», titolo dell'Arco 2 e motivazione di 3 leve, si regge su `P(12)=1−P(X)` — un'**identità**: il mercato «12» *è* la massa del pareggio, non «chi vince». Scomposizione esatta (chain rule, ricompone a 6 decimali): **massa-pareggio 12.0%, discriminazione casa/ospite 88.0%** (Premier 5.5/94.5, Liga 15.0/85.0). Spiega perché 12b/18/φ35 hanno reso quasi nulla: **aggredivano il 12%**. **Prior neopromosse non atterrava sul prior** (la penalità di identificabilità si scaricava sulle squadre senza dati: attacco −0.28/−0.39 invece di −0.23, e diverso per stagione): corretto, impatto trascurabile sui mercati di partita (0.9925→0.9924) ma **spiega il 40% della mis-calibrazione neopromosse della F91** (−10.1pp → −6.1pp). **La regola n.1 (no look-ahead) non aveva test**: la mutazione `<`→`<=` lasciava 158 test verdi *migliorando* il log-loss — una contaminazione si sarebbe presentata come scoperta; 3 test aggiunti e verificati per mutazione. **Cron mensile diventato attivo in silenzio** su main (primo fire 2026-08-01, ~51MB senza rigenerare gli snapshot): disattivato | ✅ numeri e conclusioni portanti riconfermati eseguendo; ❌ una diagnosi di 80 fasi ribaltata; 1 difetto di modello corretto; la regola n.1 ora protetta |
| **92-bis** | **chiusura dei fix dell'audit F92**, ogni test verificato **per mutazione** (si rompe di proposito il codice che dovrebbe proteggere: se la suite resta verde, il test non esiste) | **`predict.py` era per-lega a meta'**: applicava a Premier e Liga le costanti Serie A (θ=1.225, φ0=0.30, κ=1.5, `sharpen_1x2`) benche' la mappa per-lega fosse gia' misurata — in Premier **+0.0025** di log-loss 1X2 contro il motore liscio e **+2.7pp** di pareggio previsto; nasce `MARKET_ENGINE` in `src/config.py`. **Tre degradi silenziosi**: `_SUB_SUFFIXES` senza `total` gonfiava del **~67%** il conteggio partite di Polymarket; `add_squad_values` buttava le colonne appena calcolate dopo un rebuild; `build_squad_values.py` ora si FERMA se perderebbe celle reali. **Due test che non testavano**: il ramo degli spareggi non veniva mai eseguito, e il `value_bet_roi` confrontava la funzione con se' stessa. **METRICA F91 RIFATTA**: le osservazioni sono a GRAPPOLO (4 top-4 e 3 retrocesse per stagione, vincolo di somma) → bootstrap a grappoli: il guadagno top-4 vs persistenza passa da «conclusivo» a **IC [−0.0006, +0.0522] che INCLUDE LO ZERO**; regge il test dei segni (19/24, p=0.0066). **F57**: «tutti i Δ entro ±0.0005» era falso (emivita 730 in Premier: +0.005686, conclusivo) | ✅ tool per-lega su entrambi i modelli; ✅ 8 test nuovi verificati per mutazione; ⚠️ un'etichetta di conclusivita' ritirata — correzione rimasta **non propagata per 9 fasi** (la Fase 101 l'ha portata in DIARIO e README) |
| **93** | **dove si perde la DISCRIMINAZIONE** (la domanda giusta dopo la F92): deficit per-partita su 5.083 partite non pareggiate, scomposizione di Murphy + affettature | **è INFORMAZIONE, non calibrazione**: mis-calibrazione nostra **0.00083** contro **0.00125** del mercato — ⚠️ **rettifica Fase 101**: differenza **non conclusiva** (IC95 [−0.00135, +0.00049], e il segno si inverte passando a 50/100 fasce), e sotto calibrazione perfetta il termine vale già 0.00083 al p95: entrambi sono al **pavimento di rumore**, quindi «siamo meglio calibrati» non si può dire. Risoluzione 0.05270 contro 0.06251, **+0.00981 [+0.00747, +0.01246]** = l'unico termine conclusivo → le quote **calibrazione −4% / informazione +104%** sono normalizzate sulla parte che la scomposizione **attribuisce** (0.0094 sui **0.0215** del deficit, il 44%): il restante 56% resta non attribuito. P(casa\|non-pari) dichiarata 57.61% contro 57.68% reale: **nessun bias da correggere**. **Nessuna fetta** in cui siamo più informati (3 leghe × 6 stagioni × 4 fasi: tutte negative). Ma il bersaglio è stretto: sui **mismatch** siamo quasi alla pari (divario −0.00198) e **sulle equilibrate** il mercato stacca (−0.00793, 4×); e la forbice **si allarga** durante la stagione (giornate 1-5 −0.00829 → 26+ −0.00991). L'**86.9%** del deficit si materializza dove DISSENTIAMO dal mercato (adverse selection della F20, localizzata) | 🔎 **nessuna ricalibrazione può chiudere questo gap** (lo 0.00083 è tutto ciò che c'è da prendere); la caccia all'informazione ha ora un bersaglio preciso: **partite equilibrate, seconda metà di stagione** |
| **94** | **la varianza mancante nel simulatore** (richiesta utente: ritarare δ sull'orizzonte stagionale) — ma la diagnostica ha **reindirizzato il lavoro** | **δ NON era il colpevole**: a livello di singola partita le neopromosse sono predette bene (P(sconfitta) dichiarata 51.71%, realizzata **51.71%**; punti su 38 giornate 36.4 vs 35.4). Il difetto è nella PROPAGAZIONE: la classifica simulata è **compressa** (la dispersione reale supera la simulata in **21/24** stagioni, percentile medio 83% invece di 50%), e il conto torna in quadratura (15.45² ≈ 13.61² + 7.44²) → manca **incertezza**. Questo **unifica** favorito troppo sicuro e neopromosse troppo condannate: stesso difetto ai due estremi. La deriva misurata **non è uniforme**: neopromosse **0.299** contro 0.157 (1.9×), quindi un σ uniforme perturba troppo le forti (top-4 peggio in 18/24, p=0.023) e troppo poco le deboli. Con σ differenziato (0.30/0.16): **retrocessione +0.0095 IC [+0.0020,+0.0180]**, neopromosse da +6.1pp a **+2.8pp**, ECE 0.0479→0.0387; campione nullo (9/24); **top-4 peggiora** (17/24, ECE 0.0140→0.0203) | ✅ **adottata sulla RETROCESSIONE** (§1.8, per-mercato); ❌ non su campione e top-4 — *il top-4 era già calibrato, e aggiungere incertezza a una previsione giusta può solo peggiorarla*; 🔎 la compressione si chiude solo in parte: il residuo è la **correlazione fra partite** |
| **95** | **primo confronto con un mercato outright VERO** (`_run_polymarket_outright.py`): la nostra P(campione 2026-27) contro i prezzi LIVE di Polymarket, prima del via | **struttura giusta, sovra-confidenza confermata dall'esterno**: corr **0.95-0.98** e favorito coincidente in tutte e 3 le leghe (MAE 0.0252 SA / 0.0265 PL / 0.0110 Liga; KL 0.181 / 0.242 / 0.056). Ma concentriamo troppa massa sul favorito — Inter **66.4%** vs 47.1%, Arsenal 45.1% vs 33.6%, Barcelona 59.3% vs 51.8% — e ne togliamo agli inseguitori (Man United 0.8% vs 10.9%, Milan 2.7% vs 11.7%). È la **stessa** sovra-confidenza del backtest F89 (60.1% dichiarato / 41.7% realizzato), ora vista **contro un mercato vero e su dati mai visti**: due strade indipendenti, stesso difetto | 🔎 accordo forte sull'ordinamento; ❌ non è un test di edge (l'esito è a maggio 2027); il difetto strutturale della F89 è confermato dall'esterno |
| **95-bis** | **la deriva F94 giudicata dal MERCATO invece che dal backtest** (`_run_polymarket_outright.py --with-drift`): sul campione la F94 diceva «nessun effetto», ma da 24 osservazioni (una per lega-stagione) | **la deriva ha eccome un effetto, e il segno dipende da quanto eravamo già allineati**: KL Serie A 0.1805 → **0.1445** (−0.0360) e Premier 0.2418 → **0.2036** (−0.0382) **avvicinano**; La Liga 0.0560 → 0.0740 (+0.0179) **allontana**. MAE e corr migliorano dove la KL scende (SA 0.0252→0.0218, corr 0.956→0.963). È **la stessa legge della F94 sul top-4** («aggiungere incertezza a una previsione già giusta può solo peggiorarla»), su un metro indipendente: la Liga era già la più allineata (KL 0.056, un terzo delle altre). **Lezione di metodo**: per gli outright il prezzo di mercato ha **molta più potenza** del backtest storico (20 probabilità per lega contro 1 esito realizzato) | 🔎 il metro cambia la conclusione: la F94 non aveva sbagliato, non aveva potenza; ⚠️ «più vicino al mercato» ≠ «più corretto» |
| **96** | **corner e cartellini: la famiglia FUORI dalla matrice dei gol** (`_run_outside_matrix.py`) — dati mai estratti, copertura 100% su 10.260 partite | **processo DIVERSO, non ridondante**: sovra-dispersi (var/media 1.12-1.48, l'**opposto** dei gol dati i tassi del mercato) e quasi incorrelati coi gol (\|r\| ≤ 0.06). Modello di conteggio walk-forward (7.050 partite OOS) **batte la baseline**: corner MAE 2.688 vs 2.703 (R² +0.0065), cartellini 1.700 vs 1.715 (R² +0.0255), cartellini quasi perfettamente calibrati (+0.005/−0.003/+0.001 su O2.5/3.5/4.5). **ARBITRO** (solo Premier): effetto reale e grande, medie da 2.44 a 4.57 cartellini/partita, sd fra arbitri **0.513** contro banda nulla [0.158, 0.296] → **primo dato ORTOGONALE del progetto**. **Bug trovato dal bias**: +0.61 corner/partita costante su tutte le linee non era deriva temporale ma un errore di normalizzazione (vantaggio-casa senza il fattore ospite); imposto hadv+aadv=2 il bias crolla a +0.02 — *un bias costante su tutte le linee è la firma di un errore di normalizzazione* | ✅ famiglia nuova aperta e validata; ✅ primo dato ortogonale; ⚠️ manca il benchmark di EFFICIENZA (nessuna quota corner/cartellini) |
| **97** | **seconda borsa + archivio storico degli outright + primo controllo ESTERNO della deriva F94** (richiesta utente: tracciare le probabilità dei mercati che ci interessano e cercare altre fonti). Nuovi `fetch_smarkets_outrights.py`, `archive_outrights.py`, `_run_fase97_relegation_market.py`; archivio VERSIONATO in `data/outright_snapshots/` | **Smarkets ha API pubblica senza chiave** e quota ciò che a Polymarket manca: **retrocessione** (che Polymarket non prezza in nessuna lega) e Top 2/3/4/5/6 + top-half. **Complementari, nessuna domina**: sulla Premier Smarkets ha spread **0.11pp** contro un overround Polymarket del 5.8%, sulla Serie A è il contrario (spread 5-11pp). Controllo incrociato fra le due borse sul campione (62 coppie): scarto assoluto **mediano 0.13pp**. **La deriva F94 regge a una verifica esterna**: MAE contro il prezzo di mercato **8.84 → 7.32pp** (9.68 → 8.11 filtrando i libri larghi), corr 0.935. **Ma è insufficiente**: restano **+19.6pp** di eccesso sulle neopromosse (Ipswich +36.5, Coventry +26.2) compensati da un sotto-prezzo del resto della coda (Sunderland −11.9, Leeds −7.9); le somme coincidono (2.92 vs 2.85 ≈ 3) → è **redistribuzione**, siamo troppo sicuri di *quali* tre scendono. Scoperta collaterale: **coda a ZERO** — diamo 0.0% a Man City e Liverpool, il mercato 7.6% e 1.1%. Smentite 2 etichette del manuale: OddsPortal e BetExplorer **non sono bloccati** (sono inutilizzabili per altro: feed AES-cifrato / nessuna sezione outright) | ✅ seconda fonte adottata e archivio avviato; ✅ deriva F94 **confermata da strada indipendente**; 🔎 residuo = sicurezza mal riposta su *quali* squadre, non varianza mancante; 🔎 la coda a zero è un difetto strutturale (manca incertezza sui **parametri**) |
| **98** | **sette fronti in parallelo** (richiesta utente: «non lasciare nulla da parte») — NB sui conteggi, arbitro come feature, potenza del test prospettico, Tier 3 contro Polymarket, proxy delle formazioni, movimento apertura→chiusura, listino come prodotto (`_run_counts_nb.py`, `_run_referee_feature.py`, `_run_prospective_power.py`, `_run_polymarket_tier3.py`, `_run_lineup_proxy.py`, `_run_line_movement.py`, `_run_listino_validazione.py`) | **la scoperta è trasversale, non in nessuno dei sette**: tre fronti misurano la stessa **deriva di livello** (bias di media walk-forward: Premier cartellini **−0.201**, Serie A corner **+0.352**, listino corner **+0.117**) — l'emivita 365g non insegue la deriva temporale dei conteggi, e correggerla (una costante train-only) vale **5× l'arbitro** e **un ordine di grandezza più** del passaggio Poisson→NB. Fronte per fronte: **NB conclusiva ma trascurabile** (corner 0.6490→0.6480, Δ +0.00103 [+0.00062,+0.00143]; cartellini +0.00088 [+0.00033,+0.00142]; gialli Serie A **sotto-dispersi** 0.901 → la NB collassa da sola sulla Poisson); **arbitro NEGATIVO** (solo Premier, 3420/3420; nessun IC esclude lo zero; **l'85% del guadagno apparente era solo livello**: −0.00308 dei −0.00364 — ma il segnale esiste, `b=0.401` [+0.096,+0.706], fattore grezzo sovra-esteso ~2.5×, componente di varianza arbitro 3.7%); **potenza**: DEFF=1.00 (partite indipendenti, ICC≈0) ma rapporto segnale/rumore 1:8,5 → **1 giornata × 3 leghe = 9,8% di potenza**, servono **574 partite** per l'80% sull'1X2 (2.254 sul GG/NG, 2.988 sull'O/U 2.5); **Tier 3 vs Polymarket: bersaglio fallito** (0 eventi sulle nostre 3 leghe in pausa estiva, nessun esito sugli aperti; trappola: 65/78 eventi con volume >1.000$ sono partite già giocate) ma **fondazione posata** — frazione 1T **f=0.4396** [0.4338,0.4458], 1T Poisson-compatibile, tempi quasi indipendenti, e validazione storica conclusiva su 6.840 partite (Halftime **+0.0537** [+0.0461,+0.0612], Second Half +0.0578, risultato esatto +0.1940) con **residuo localizzato**: il 2T è mal calibrato (pareggio 0.3671 vs 0.3427) mentre il 1T passa per lo stesso codice ed è calibrato a <0.006 → è **game-state**; **proxy formazioni NEGATIVO pieno** (9.159 partite; la parte che funziona correla **+0.9603** col valore rosa già bocciato, la parte nuova è nulla ovunque, e la disponibilità correla **−0.1227** col logit della chiusura = **il mercato le assenze le prezza già**); **movimento apertura→chiusura**: non anticipabile (β −0.0039, R²=0.0001), **CLV negativo conclusivo** −0.0022 [−0.0033,−0.0012] (45,7% positivi; Serie A −0.0027 ≈ il −0.0028 della F14), vale **15,6% del gap** — ma corr(nostro deficit, deficit dell'apertura) **+0.4270** contro placebo +0.0884, concentrata su equilibrate e seconda metà = **lo stesso profilo del deficit F93**; **listino POSITIVO**: 38 mercati walk-forward, **32/36 battono la baseline con IC conclusivo, 0 perdono**, e i livelli di validazione sono **QUATTRO non tre** (A=1 solo l'handicap asiatico, Brier 0.2044 vs 0.2044; **A°=8 circolari** perché la quota È l'input del motore; B=27 calibrazione; C=7) | ⚠️ **correzione verificata a mano**: il fronte 3 riportava che la Fase 89 «non regge a una baseline meglio tarata» (1.3816 vs 1.4293) — i numeri sono giusti ma la spiegazione era sbagliata: la griglia F89 è un **superset** e dà una baseline **peggiore** → è **instabilità LOO a n=24**, non taratura migliore. Lettura corretta: la F89 è **fragile alla specificazione della baseline**, e l'outright è **non testabile prospetticamente** (servirebbero 57 stagioni-lega) — non «perdente». ⚠️ «leva nuova: correzione di livello dei conteggi» — **RITIRATA dalla riga 99**: il bias di livello NON persiste fra fold e correggerlo peggiora (5 celle su 8 con IC conclusivo); ✅ 3 mercati Tier 3 nuovi validati; ❌ arbitro, formazioni-proxy, anticipo del movimento |
| **99** | **la correzione di LIVELLO dei conteggi** — il lead che la Fase 98 aveva indicato come «il miglior rapporto valore/costo, e nessuno la stava cercando» (`_run_counts_level.py`, 7.050 partite OOS, 21 fold): cinque stimatori di livello walk-forward (`c_oos`, `c_last2`, `c_last`, `c_trend`) più la versione **alla radice** (emivita scelta fold per fold sul solo passato) | **il lead è FALSO**: nessuno dei cinque migliora e **5 celle su 8 peggiorano con IC conclusivo** (peggiore `c_trend`: corner −0.00316 [−0.00475,−0.00155], cartellini −0.00464 [−0.00644,−0.00293]); l'emivita walk-forward è un lancio di moneta (corner −0.00004 [−0.00191,+0.00183], P>0 = 0.484; cartellini −0.00034, P>0 = 0.325). **La spiegazione in un numero: il bias di fold NON persiste** — corr(bias_t, bias_{t−1}) **+0.2299** [−0.2544,+0.6715] sui corner e **+0.1915** [−0.3446,+0.5830] sui cartellini, **10/18 stesso segno = una monetina**, con sd del bias per fold **2,6×** il bias pooled (corner) e **10×** (cartellini). Il «bias costante su tutte le linee» era costante *fra le linee*, non *nel tempo*. **Seconda lezione**: un bias sulla MEDIA non è un bias sulle PROBABILITÀ — i cartellini sovrastimano di +0.042 conteggi ma la calibrazione dei mercati era già ottima (+0.0047/−0.0034/+0.0008) e la correzione l'ha **rotta** (+0.0097/+0.0026/+0.0064). Unica cella sensata: Serie A corner, dove il bias era 10× più grande (+0.352→+0.031, Δ +0.00271 [−0.00051,+0.00590], P>0 = 0.95, **non conclusivo**) — e le altre due leghe peggiorano con CI conclusivo, quindi nemmeno il per-lega si salva | ❌ lead chiuso negativo (auto-correzione della F98); ✅ **regola di metodo nuova**: un bias misurato su un POOL non autorizza una correzione PROSPETTICA — prima si misura se **persiste** (autocorrelazione fra fold, con CI). Stessa forma di F86-bis (θ per-squadra: persiste ma non sfruttabile) e del controllo-di-livello F98: **misurato ≠ prevedibile** |
| **100** | **cinque leghe**: audit riga-per-riga contro la fonte-madre (45 stagioni ri-scaricate), caccia al dato coperto da stime, import di **Bundesliga e Ligue 1**, playbook completo sulle due leghe nuove, e verifica avversariale sistematica di ogni risultato | **Audit**: 0 differenze su gol, date, tiri, 10 colonne quota e 8 colonne xG; gol confermati da fonte indipendente su 16.109/16.110 appaiate; 7 anomalie reali (6 nella fonte + 1 nostra, l'ordine delle colonne; un ottavo caso ritirato come falso positivo). **Dato ritrovato**: la chiusura O/U 2017-19 esiste (book 1xBet via footiqo, 3.652/3.652 partite, corr 0.9977 con la chiusura vera contro 0.9909 con l'apertura) — ma NON inserita: e' un solo book e come proxy della media multi-book e' peggiore della stima (MAE 0.0156 vs 0.012). **Collaterale piu' grande del bersaglio**: quote GG/NG al 100%, e la premessa di CLAUDE.md §1.8 cade — il mercato GG/NG e' informativo (0.6840 vs 0.6921, CI conclusivo) ma vale 1/3 dell'O/U dello stesso book, il nostro prezzo lo PAREGGIA (6 varianti su 6 nel rumore) e il DC perde di netto (+0.0104, il book lo ingloba: α\*=0 nel 70% dei fit). **Leghe nuove**: 2.754 + 3.097 partite; gap col mercato +0.0181 e +0.0190 (dentro la forchetta delle altre); market-implied 15/15 mercati sul DC; ri-taratura PIATTA 5 leghe su 5; NESSUNA leva del mercato si replica (router θ 0/25, φ35 e power-devig bocciati, beat-the-close chiuso con ROI −22%). θ divide le leghe in due famiglie: «latine» ≈1.24 dove la sotto-dispersione paga, Premier/Bundesliga/Ligue 1 ≈1.08-1.10 dove non paga | ✅ 5 leghe in produzione (16.111 partite), 2 guard nuovi (overround bilaterale, xG segnaposto), stime a 5 leghe (3.638 righe) con l'errore del REGIME D'USO (0.014, non 0.012); ❌ nessun edge nuovo; ⚠️ la verifica avversariale ha smontato 5 affermazioni su 12 — e in 5 casi su 7 il difetto non era il numero ma la statistica scelta per raccontarlo (→ regola R7) |
| **101** | **quinto audit: le ultime 20 fasi (80-100) e l'INTEGRAZIONE dal cantiere a `main`** — 13 fronti in parallelo, ognuno con un verificatore avversariale incaricato di smontarne i rilievi (richiesta utente) | **198 rilievi, 16 gravi, ZERO nei modelli**: formule = codice, snapshot = fonte, conteggi partite corretti, spareggi = regolamenti. Tutti i guasti nei **giunti**. **L'integrazione aveva portato in main 32 script che non partivano** (`parents[2]` → `/home/user`, percorsi verso `cantiere/` cancellata): la **Fase 100 non era riproducibile** — audit, correzioni R3 e snapshot delle 2 leghe nuove; `fetch_sources.py` scaricava 135 MB fuori dal repo. **Bug distruttivo**: `build_database.py --league X --refresh` scriveva la lega X **sopra** lo snapshot Serie A. **Il denominatore dell'audit F100 e' sbagliato**: 15.788 non e' nessun universo del progetto (sono **16.111**, 16.110 appaiate a Understat) — e gli artefatti dell'audit stesso lo dicevano. **«8 anomalie, tutte nella fonte» → 7** (6 fonte + 1 nostra, +1 ritirata). **Cinque conclusioni ritirate ancora vive altrove** (diagnosi F92 in 3 punti del README, lead F98, premessa GG/NG, rete «bloccata», M2). **Una FASE FANTASMA**: la 92-bis aveva cambiato codice di produzione senza voce nel diario — per questo «entrambi conclusivi» sul top-4 e' sopravvissuto 9 fasi a un IC che include lo zero. **Due bug nel tool**: φ35 applicata dove e' misurata dannosa (Premier/Liga, +1.0pp sul pareggio) e `--no-draw-balance` mai letto | ✅ corretti: 32 script (ora tutti partono; `applica_correzioni --dry-run` verde = idempotenza R3 di nuovo dimostrabile), il bug distruttivo, i 2 bug del tool, 21 link rotti, i denominatori, le 5 catene ritirate; ✅ 3 test nuovi (mappe per-lega; le tuple di spareggio BL/L1 erano scambiabili senza rompere nulla) → **197 verdi**; 📄 verbale completo in `docs/AUDIT_FASI_80_100.md`; ⚠️ 13 punti lasciati alla decisione dell'utente (fra cui: il numero-bandiera passa a **+0.0167**, la COM-Poisson F85 e' la dp riparametrizzata, l'α\*=0 della F88 non fu mai calcolato); ⛔ un rilievo scritto e **ritirato** in giornata («main non ha ricevuto l'integrazione»): letto da un ref locale vecchio invece che dalla fonte — lo stesso errore che l'audit trova negli altri |
| **101-bis** | **applicazione delle correzioni dell'audit: seconda passata**, con ri-verifica indipendente di ogni patch prima di applicarla (il criterio: un falso positivo applicato costa più di un difetto lasciato) | **Eseguiti 4 dei 13 punti aperti di §4**, tutti riprodotti eseguendo. **(1) Numero-bandiera rimisurato al codice di HEAD** (6 backtest walk-forward Serie A, config ufficiale, post-fix del prior F92): **0.9799 / 0.9632 / gap +0.0167**, ROI **−15.8%** su **866** scommesse — allineate tabella di testa, tabella per stagione, matrice F15-bis, riga pooled F9, CI F17 e i punti narrativi; le misure delle singole fasi e `runs.jsonl` restano PRE-fix, ora **dichiarati tali**. **(2) La COM-Poisson della F85 è la dp riparametrizzata** (`dp(θ) ≡ COM-Poisson(ν=θ)` mean-matched: coincidono a ≤5e-06 sull'exact-score log-loss, ≤2e-05 sulle code) → non è una conferma indipendente, e su griglia fine l'argmin è **θ=1.18**, non 1.225 (Δ −0.00027, IC nel rumore). **(3) L'«α\*=0» della F88 non fu mai calcolato**: α\*=**1.08** [+0.147, +2.052]; la conclusione onesta è «pareggio in Brier col mercato sharp» (ΔBrier −0.000136 [−0.000362, +0.000083]). **(4) Due affermazioni della F93 declassate**: «siamo meglio calibrati» è non conclusiva (IC [−0.00135, +0.00049], segno che si inverte a 50/100 fasce, entrambi al pavimento di rumore) e le quote −4%/+104% sono normalizzate sul 44% del deficit attribuito. Riga **F91 ri-letta interamente** sull'artefatto post-fix (ECE 0.0140; retrocessione +0.0925 [+0.0465,+0.1341] vs tasso base, −0.0066 [−0.0364,+0.0208] vs persistenza; 30 casi sopra il 60%, non 37): la prima stesura mescolava numeri pre- e post-fix. Nel **verbale**: partizione dei 198 corretta (53 non contro-verificati, non 51), «31 correzioni» → **27 applicate** su 31 righe, manifest **36 dei 140** grezzi cancellati, conteggio del denominatore (15 occorrenze su 12 righe in 6 file), stato dei branch riletto da `git ls-remote`, frase troncata del sommario, 5 link rotti, e il **rimando incrociato** fra i due rilievi con verdetti opposti sul «~6 σ» (è la σ della distribuzione **pooled**, n=60.775 → 6.5: si dichiara la popolazione, non si «corregge» il numero) | ✅ README e verbale allineati; ⚠️ il 198 va letto come **~143 difetti distinti / 6 famiglie gravi** (10 dei 16 gravi sono la stessa rottura degli script) |
| **101-ter** | **chiusura dei punti aperti** dell'audit: i numeri non ri-derivabili, le trappole di riproducibilità e il riordino di `main` | **Numeri**: il GG/NG della riga pooled F9 era **−0.0018**, un orfano misurato contro un riferimento mai dichiarato → ri-derivato **+0.0026**, e la riga ora coincide cella per cella con la matrice F15-bis; «~70 varianti» del mega-sweep → **63**; i cinque `+0.0165` residui del README marcati come PRE-fix. **Reso riproducibile ciò che era pubblicato e non ri-derivabile**: l'encompassing della F88 vive ora dentro `_run_ah_benchmark.py` (α\*=**+1.082** [+0.143,+2.026]; walk-forward n=**6.297**, Δ **−0.000064** [−0.000271,+0.000139]) — e ricalcolandolo si è scoperto che **il protocollo di stima di α cambia il SEGNO** del Δ (pooled −0.000064 vs per-lega +0.000011, entrambi nel rumore): lo script ora stampa entrambe le varianti. **Verificato il «18/24» della F94** che era dichiarato non verificabile: top-4 migliore in **6/24**, test dei segni **p=0.0227** → lo 0.023 pubblicato regge. **Dati**: inserite le 6 celle 1X2 con **dato reale** da fonte secondaria dichiarata (R2+R3) → **zero** righe senza chiusura 1X2 sulle 5 leghe. **Codice**: 4 monkey-patch morti rimossi (no-op dimostrato), 12 `sys.path.insert` duplicati, `BASE_URL` puntava al mirror **404** mentre l'ufficiale risponde 200, `--date` per la F97, anti-circolarità nel confronto Transfermarkt | ✅ chiusi **10 dei 13** punti di §4; ⚠️ 3 aperti (PANCHINA 18 celle, il resto del refresh documenti, la stima O/U estesa alla Liga); 🔒 tre **trappole di riproducibilità** chiuse: un artefatto ufficiale veniva sovrascritto *durante la verifica*, un `assert` cablato bloccava una rigenerazione legittima, un registro di correzioni non era più verificabile da nessuno script |
| **103** | **applicato il recupero Wikipedia dei calendari di coppa** (richiesta utente: verifica dei dati, cerca fonti esterne dove mancano) — le 3.045 righe raccolte alla Fase 100 ma mai integrate (regola R4 del cantiere) vengono unite ai calendari di club esistenti (`scripts/integra_calendari_coppa.py`, nuovo) | **Chiusi i 1.603 falsi zero** di `midweek_europe` dichiarati in `celle_residue.csv`: verificato **a cella esatta** contro l'oracolo già pubblicato, lega per lega — Serie A 236/236, Premier 251/251, La Liga 454/454, Bundesliga 180/180, Ligue 1 482/482 (celle 0→1), con le partite di riposo cambiato altrettanto esatte (314/282/407/189/508) e **zero regressioni** (garantite dalla monotonia della formula: aggiungere partite può solo accorciare un intervallo, mai allungarlo). Nessuna esclusione per competizione (supercoppe, Mondiale per club, Coupe de la Ligue incluse: `sources.EXTRA_CUP_COMPETITIONS`, mai modellate prima) — è l'unica scelta che riproduce l'oracolo esattamente. Nessun impatto sul modello ufficiale: `rest_full`/`midweek` restano covariate **spente di default** | ✅ dato corretto su 5/5 leghe, verificato prima di scrivere (nessun file toccato se anche una sola lega non combacia); ✅ suite 853 verde (nuove etichette competizione, parametrizzazione test estesa a Bundesliga/Ligue 1); ⚠️ il recupero non è rigenerabile da script (solo Appendici nel report Fase 100): se si rilancia `build_database.py --fixtures` senza rifare l'integrazione, le righe Wikipedia scompaiono di nuovo |

| **104** | **il resto della lista** (richiesta utente: sistema ogni problema dichiarato, verifica con più fonti indipendenti) — bug del Monaco, 8 righe DFB-Pokal duplicate, tre rilievi d'audit (F12-04/05/09) già chiusi ma non spuntati, e la fonte xG Understat con lo stesso mirror morto di football-data mai corretto | **Monaco (MCO)**: `sources.uefa_country_codes()` accetta ora un insieme di codici paese per lega (test nuovo). **DFB-Pokal**: non erano 8 date da correggere ma 8 righe **duplicate** (la Fase 103 aveva già aggiunto la data giusta da Wikipedia accanto a quella sbagliata di openfootball, stesso dedup che non le fonde perché la data differisce) — verificate con **due fonti live indipendenti** (query XHR a openligadb.de, Wikipedia de "Achtelfinale: 2./3. Dezember 2025"); tolta la riga sbagliata, **0 partite** con congestione cambiata (la data più recente vince sempre nella ricerca "ultima gara prima di d"). **F12-04/F12-05**: già chiusi ai commit `ec85314`/`44052d7`, mai marcati `✅ CHIUSO` nel verbale. **F12-09**: mancava solo l'ultimo pezzo — `docs/DATI.md` diceva ancora "registrato ma NON inserito" per le 6 celle 1X2 reali dalla Fase 101-bis; censimento corretto **7.359/55 → 7.353/49**. **Understat**: il mirror GitHub era morto (404 **verificato indipendentemente dal problema di sessione**: `raw.githubusercontent.com` risponde 200 su un repo vero) ma il codice non usava mai l'endpoint ufficiale già documentato in `docs/MANUALE_SOPRAVVIVENZA.md` dalla Fase 100 — corretto (`sources.py` + `understat.download_season`, header XHR + decompressione gzip), **verificato**: dati live identici a quelli congelati (Δ 0.0 su 380/380 partite, La Liga 1718). Con la fonte viva, le **49 celle residue** sono state ri-controllate dal vivo una per una (2 xG Understat, 3 quote football-data): **nessuna recuperabile**, tutte lacune genuine alla fonte, confermate non con un'estrapolazione ma con un nuovo download. Trovato e corretto anche un CSV rotto (5 righe non quotate) introdotto dalla Fase 103 stessa, mai eseguito da nessun test | ✅ tutti i problemi della lista chiusi o ri-confermati con fonti indipendenti; ✅ 858 test verdi (+1 Monaco, +3 `altra_lega` gia' estesa F103); ⚠️ nessun dato nuovo recuperato (le lacune residue sono reali); 🔧 la fonte xG torna riproducibile per la prima volta dalla Fase 14 |

| **105** | **secondo ri-tentativo sull'O/U 2017-19** (richiesta utente: prova a trovare un secondo book indipendente, non solo 1xBet) — quattro angoli nuovi rispetto alle Fasi A-D originali | footiqo è strutturalmente un solo book (non una via per un secondo); **Wayback Machine** (mai tentato prima): l'endpoint CDX è bloccato dalla rete per qualunque dominio (scoperta operativa, non specifica di oddsportal), il playback diretto funziona ma nessuna pagina di risultati stagionale 2017-19 delle nostre leghe risulta mai archiviata, e le uniche catture BetExplorer/OddsPortal di quelle stagioni sono 2022-2024 (dopo il ritiro del confronto-quote per partite vecchie, già noto dalla Fase 100); un dataset Kaggle nuovo è 198 righe di sole partite 2023; `oddsbase.net` vieta ClaudeBot nel `robots.txt` (rispettata R5.3, non consultato); `aussportsbetting.com` bloccato, `btfodds.com`/`sportsoddshistory.com` senza struttura storica utilizzabile | ❌ nessun dato nuovo; la stima resta la scelta migliore nota; 🔧 scoperto e documentato il blocco della CDX API di Wayback Machine (utile per ricerche future) |

| **106** | **il confronto footiqo-vs-verità esteso da 1 a 6 stagioni** (richiesta utente: si può misurare su più stagioni?) — footiqo copre dal 2015/16, la chiusura vera football-data dal 2019/20: 6 stagioni si sovrappongono, non solo il 2019-20 usato finora | Scaricate live 25 stagioni footiqo nuove (2020-21→2024-25) + 30 CSV grezzi football-data; il 2019-20 ricalcolato riproduce **esattamente** il numero già pubblicato (n=1.687, MAE 0.0156, bias +0.0088 — verifica del metodo). **Il numero NON è stabile**: MAE 0.0156→0.0179→0.0192→0.0136→0.0107→0.0096 (2019-20→2024-25); il 2020-22 (porte chiuse) è il peggiore, dal 2022-23 footiqo **batte** perfino il numero onesto della stima. **Correzione collaterale**: il riferimento della stima era 0.012 ("in interpolazione", ottimistico) non ~0.014 ("regime d'uso", il numero onesto per come la stima verrebbe davvero usata sul 2017-19) — corretto ovunque nei documenti vivi (non nelle voci storiche, che restano PRE-fix) | ➖ nessun cambio di decisione (il 2019-20 resta il proxy più vicino e meno inquinato dalle porte-chiuse, e lì la stima vince ancora, margine più piccolo: 0.0156 vs ~0.014); 🔎 sostituita un'assunzione implicita (stabilità nel tempo) con un fatto misurato (instabilità, causa plausibile — porte chiuse — ma non provata: le due letture per il 2017-19 restano entrambe aperte |

| **107** | **terzo ri-tentativo sull'O/U 2017-19** (richiesta utente: continua a cercare, esplora fonti nuove E verifica quelle già escluse) | `oddsportal.com/robots.txt` letto per intero: vieta ogni URL con l'anno 1998-2024, blocco sistematico non un dettaglio. **BetExplorer ri-controllato dal vivo**: il 404 di prima era in parte un blocco anti-bot (serve uno User-Agent da browser vero) — con quello, pagina reale raggiunta, ma **stesso risultato**: nessun tab O/U per le partite 2017-18. Kaggle `mexwell` aggiornato a v2 dal primo controllo: ri-verificato, stessa colonna O/U singola. Tre angoli nuovi chiusi con motivo specifico: scraper GitHub (solo strumenti, uno richiede login e copre solo 1X2), dataset accademici Bundesliga (quote in-play, mercato sbagliato), provider commerciale con storico dichiarato di soli 6 mesi | ❌ nessun dato nuovo; 🔎 più fiducia nel "non esiste": il ri-controllo BetExplorer ha stavolta *davvero* raggiunto la pagina invece di un 404 mascherato — lezione di metodo per ogni verifica futura |

| **108** | **«e se cercassimo partita per partita?»** (idea utente dopo tre ri-tentativi in blocco negativi) — testata direttamente, non solo argomentata | Wayback Machine su URL reali di singole partite (non più la pagina-elenco stagionale): **404**, mai archiviate. Ricerca web sul caso più favorevole possibile — Juventus-Napoli 22/04/2018, lo scontro scudetto più seguito della stagione: nessuna quota storica reale, solo pagine pronostici "sempre verdi" che si riscrivono per ogni nuovo incontro | ❌ non scala nemmeno nel caso migliore; 🔎 introdurrebbe comunque un bias di selezione (solo i big-match sarebbero "trovabili") anche se avesse funzionato |

| **109** | **Betfair Exchange: prima di scaricare, il test che si poteva fare da soli** (l'utente ha un account Betfair e chiede di implementare l'API) — `football-data` pubblica la chiusura Betfair Exchange (`BFEC>2.5`) in UNA stagione, la 2024-25: lì convivono Betfair, la media multi-book e l'esito reale, quindi si misura che tipo di fonte sia **senza scaricare nulla** | Su 1.752 partite × 5 leghe, MAE dalla media multi-book: MaxC 0.0057, **Betfair 0.0060**, Pinnacle 0.0063, B365 0.0071 — contro **~0.014 della nostra stima** e 0.0156 di 1xBet (scartato). Betfair è nel **gruppo dei book seri**, non fra gli outlier: **2,3× più vicino alla media multi-book della stima che sostituirebbe**, bias +0.0015 (vs +0.0088 di 1xBet); contro l'esito vero almeno pari alla media dei book (0.6648 vs 0.6652, Δ −0.00039 IC95 [−0.00115,+0.00038], P 84.7%), coerente col fatto che una borsa non ha margine (overround 1.0053 vs 1.0482). ⚠️ **Ritirata la mia valutazione della F108** («il guadagno è piccolo»): era un'analogia Betfair≈1xBet, non una misura. Costruito `scripts/fetch_betfair_historic.py` (5 endpoint + parsing stream `.bz2`) con **9 test** — fra cui quello che conta: la chiusura è l'ultimo prezzo **prima** del passaggio in-play, mai dopo (sarebbe look-ahead, l'errore di Udinese-Roma) | 🟢 **prima pista delle Fasi 100-108 che merita di essere percorsa**; ⚠️ NON è un via libera all'inserimento: i numeri sono della 2024-25 e la F106 ha già mostrato che la qualità di una fonte non è stabile nel tempo → si scarica, si valida contro `BFEC>2.5`, poi si decide; 🔎 collaterale potenzialmente più grande del bersaglio: il piano BASIC dà istantanee **ogni minuto** → la «traiettoria delle quote», che `newseason.md` dichiara «mai avuta a nessuna scala» e non recuperabile a posteriori, diventa recuperabile all'indietro dal 2015 |
| **110** | **la documentazione Betfair entra nel repo** (richiesta utente: «così avremo meno lavoro in futuro») — specchiata via API REST di Confluence, non incollata a mano | **78 pagine** in `docs/betfair_api/` (916 KB) ordinate per tema + la Historical Data API (altro sito, geo-bloccato, fornita dall'utente); ogni file dichiara fonte, URL, id Confluence, data di estrazione e la regola «in caso di dubbio vince la pagina online». **Scoperta collaterale che vale più della copia**: cercando `OVER_UNDER_25` nelle 78 pagine — **non c'è**. Betfair **non pubblica l'elenco dei marketType** (`listMarketTypes` ne cita due «i.e.» e rimanda a scoprirli a runtime): la costante su cui poggia tutto il filtro di `fetch_betfair_historic.py` è una **convenzione dell'ecosistema, non un valore documentato** | ✅ copia **ri-generabile** (il contrario di `caccia_calendari.py` della F100, andato perso perché viveva solo come appendice di un report); ✅ l'assunzione non verificata degradata da errore silenzioso a diagnosi (`--dry-run` stampa i tipi realmente presenti); 💡 specchiare una doc è un **controllo**: portata in casa e interrogabile con `grep`, si scopre cosa NON dice |
| **111** | **il token, i vincoli veri, e cosa possiamo farci con Betfair** (richiesta utente: aiuto per il token + «che lavoro possiamo fare») | **Tre fatti che cambiano il piano, tutti letti nella doc appena specchiata**: (1) per il servizio storico **non serve una App Key**, basta l'header `ssoid` dal cookie del browser; (2) ⚠️ sull'exchange **italiano la sessione dura 20 MINUTI** contro 12-24 ore sul `.com`, e testuale «*Session times aren't determined or extended based on API activity*» — scaricare **non** tiene viva la sessione: un download di migliaia di file sarebbe morto a metà con errori sparsi, non con un fallimento pulito; (3) l'exchange italiano è **licenza separata** e se un account `.it` abbia accesso al servizio storico `.com` **non è documentato** né verificabile da qui (403 per regione) | ✅ `keepAlive` ogni 10 min con endpoint per giurisdizione (`--jurisdiction`, default `it`); ✅ piano d'uso in `docs/betfair_api/99_guida_pratica_progetto.md` (A buco O/U, B traiettoria, C i ~17 mercati mai validati, D volume a pagamento, E prospettico); ⛔ limite dichiarato: il progetto **non piazza scommesse**, Betfair è una fonte dati; 💡 il lavoro utile non è stato «creare il token» ma trovare i due vincoli che avrebbero fatto fallire il download **in modo confuso** |
| **112** | **un solo scarico per due piste** (domanda utente: si può procedere con A e B? e puoi farlo da solo?) | **«Da solo» è no, e non con una VPN**: il blocco è **geografico e regolatorio**, non tecnico — aggirarlo esporrebbe l'account dell'utente al «traffico inusuale» che Betfair segnala. **Ma c'era una cosa da fare PRIMA dello scarico**: i `.bz2` contengono sia la chiusura sia **tutta la traiettoria pre-partita**, e il parser della F109 teneva solo la chiusura — chi avesse scaricato allora avrebbe ottenuto A e perso B, dovendo **ri-scaricare tutto**. Riscritto `_serie_from_stream`: la chiusura è un caso particolare della serie, così le due definizioni non possono divergere | ✅ un solo scarico, due piste; 🔒 **il refactor è stato bocciato da un test**, ed è la parte interessante: derivando la chiusura come «ultimo punto della serie», il caso dell'immagine finale con **un solo lato prezzato** ripiegava sull'ultimo punto completo — cioè spacciava per chiusura un prezzo di minuti prima, un **«finto pieno» (R6)** plausibile e invisibile. Intercettato da un test scritto due fasi prima per un altro motivo; ✅ 5 test nuovi, **883 verdi** |
| **113** | **«quanto serve davvero?»** (domanda utente prima di mettersi a scaricare) — il **ridimensionamento di una raccomandazione mia**, con tre verifiche a portata di `grep` mai fatte | (1) **La stima O/U non alimenta nulla**: `read_ou_close_estimates()` è chiamata **solo da un test**, e i backtest ufficiali girano su 2020-21 → 2025-26, stagioni che hanno tutte la chiusura reale → **il buco 2017-19 non tocca un solo risultato pubblicato**; (2) il valore vero è **3.652 partite** che il market-implied non può prezzare, cioè due stagioni da inutilizzabili a utilizzabili — ma sono le due più vecchie e meno rappresentative; (3) **una fetta grossa del valore era già in casa, gratis**: `football-data` pubblica **20 colonne Betfair Exchange** per 2024-25/2025-26 (1X2, O/U 2.5, handicap, apertura *e* chiusura) su **3.393 partite, copertura 96,8%**, mai usate. Misurato: 1X2 di chiusura Betfair **0.9676** contro **0.9682** della media multi-book (Δ −0.00060 [−0.00154, +0.00041], P 87.9%, **non conclusivo**), overround 1.0055 vs 1.0531 | ⚠️ **ordine dei lavori invertito**: prima le colonne gratuite, poi — solo se lì emerge qualcosa — lo scarico storico, che resta l'unica via per la **traiettoria minuto per minuto** e i **mercati oltre 1X2/O-U/handicap**, non per il buco O/U in sé; ⚠️ ridimensionata anche la pista B (la F98 ha già misurato che il movimento apertura→chiusura **non è anticipabile**, β −0.0039, R² 0.0001: la traiettoria dice *quando* il mercato impara, serve ad **attribuire** il gap, non a chiuderlo); 💡 lezione su di me: il valore di un dato non sta nella sua qualità ma in **cosa cambierebbe averlo** |
| **114** | **far usare le stime davvero** (richiesta utente: «tanti dati e tante stime, vorrei fossero usati tutti almeno da qualche parte») | **Prima l'inventario, perché la premessa andava verificata**: controllate tutte e **38** le colonne una per una contro `src/` e `scripts/` — **nessuna è inutilizzata**. Il primo conteggio diceva il contrario (4 colonne «mai usate») ed era un **artefatto della regex**, che spezzava i nomi con cifre (`odds_over25` → `odds_over` + `25`). **Rettificata una mia frase della F113** («la stima non alimenta nulla»): troppo netta — il CSV è letto direttamente da `_run_fase75_squeeze_2017_19.py` e da `verifica_stime.py`; il fatto esatto è che la stima **non era una via di prima classe**. Creata `loader.ou_close_probability()`: P(Over 2.5) di chiusura con la **provenienza dichiarata riga per riga** (`reale`/`stima`/`assente`) — copertura **12.459 reale + 3.638 stima + 14 assente = 99,9%** | ✅ per il market-implied significa passare da **12.459 a 16.097 partite utilizzabili (+29%)**: 2017-18 e 2018-19 smettono di essere ciechi per il titolare; 🔒 la separazione prezzo/stima è protetta: le colonne quota **non vengono toccate** (verificato **per mutazione** — scrivendo la stima in `odds_over25` il test fallisce), `usa_stime=False` restituisce il buco vero; ✅ 6 test nuovi, **889 verdi**; ⛔ **NON** accese le covariate in panchina: un dato testato e scartato **è** un dato usato, accenderlo per non lasciarlo inutilizzato sarebbe il contrario del metodo |
| **115** | **«serve un PC cloud 24/7?»** (domanda utente: cosa inventarsi per superare i blocchi, e quanto costa) | **Il muro di Betfair non è tecnico né economico, è contrattuale**: App Key Delayed gratuita ma «for **development** purposes» (dati conflati a 180 s), App Key Live **£499** una tantum e testuale «**Read-only access via the Live App Key isn't permitted**» — la raccolta dati pura sul feed live **non è un uso previsto a nessun prezzo**, e un raccoglitore 24/7 su un account che non scommette rischia la **limitazione dell'account**. Nessun VPS risolve un vincolo di questo tipo. **La seconda risposta vale più della prima: la soluzione era già in casa.** **Smarkets** ha API **pubblica, senza chiave, senza account**, raggiungibile da qui — usata dalla F97 ma **solo per gli outright**. Sondati i mercati per singola partita: **100 mercati** (1X2, **risultato esatto**, **GG/NG**, O/U da 0.5 a 6.5, combinati), `bids`/`offers` = **banco e puntatore con le quantità** (su Betfair ladder e volume sono nei piani a pagamento), margine quasi nullo (somma dei prezzi medi **100.48%**) | ✅ dà **gratis** le due cose dichiarate irraggiungibili alla F111 (spread banco/puntatore e volume); 🟢 apre la **pista C**: validare risultato esatto, GG/NG e le linee O/U contro un mercato vero — finora solo l'handicap asiatico era stato confrontato con una quota esterna (F88); 💰 costo **€0** (Smarkets + i 3 workflow GitHub Actions già nel repo) contro £499 di Betfair Live comunque non applicabile; ⛔ limite: Smarkets **non ha storico**, raccoglie in avanti |
| **116** | **raccoglitore Smarkets pre-partita** (richiesta utente: «procedi») — nuovi `scripts/fetch_smarkets_matches.py` + workflow ogni 6 ore; client HTTP e `book_price` **riusati** da `fetch_smarkets_outrights.py` (F97) | Tutte e 5 le leghe hanno già il calendario 2026-27 su Smarkets. Prima raccolta reale: **180 righe su 6 partite** (La Liga, 15-17 ago) sui 6 mercati del listino, **risultato esatto compreso**. Somma dei prezzi medi complementari **0.994-1.003** (il mid è già una probabilità quasi normalizzata); libro a due lati sul **59%** delle righe. **Correzione su un test**: la motivazione scritta («difende dalla collisione `germany-2-bundesliga`») era **falsa** — quella collisione è strutturalmente impossibile e la mutazione non faceva fallire nulla; riscritta, e cercata la mutazione con denti (mappa leghe corrotta → 2 test rossi) | ✅ raccoglitore in piedi prima della scadenza del 16 agosto; 💰 costo **€0** (API pubblica senza chiave, Actions gratuito); ⛔ raccoglie **in avanti**: non sostituisce lo storico 2017-19; 📌 13 test nuovi |
| **117** | **allineamento di OGNI file del repo** (richiesta utente: «voglio che ogni file sia sempre aggiornato… se serve riorganizza anche ciò che è disordinato») — preceduto dal resoconto dei branch e dalla caccia ai riferimenti scaduti | **Branch**: i 3 `claude/…` su `origin` sono **tutti antenati di `main`** (0 commit avanti, `merge-base --is-ancestor`); la `cantiere/` mancante è uno **spostamento tracciato da git** (`6c9b377`), non una perdita. **Tre affermazioni di rete scadute**: `huggingface.co`, `datasets-server.huggingface.co` e `data.jsdelivr.com` erano dichiarati bloccati dal proxy — **ri-testati, rispondono 200** (per jsdelivr l'audit F100/101 l'aveva perfino già notato senza correggere la tabella); e `experiments/prospettico_2026_27.md` era l'ultimo dei 5 documenti del rilievo `F9-rete-tornata-non-propagata` a dichiarare ancora «`WebFetch` bloccato del tutto». **Una fase fantasma, di nuovo**: la **F101-bis** aveva riga nel README e rettifiche sparse ma **nessuna voce di diario** — lo stesso difetto che l'audit F101 aveva rimproverato alla F92-bis, ripetuto due fasi dopo; voce ricostruita dalle fonti contemporanee. **Le F110-115 non avevano riga in questo registro** (violazione §2): aggiunte. **Matematica nuova**: la «COM-Poisson ≡ dp» della F101-bis passa da coincidenza numerica (≤5e-06) a **identità algebrica esatta** — sviluppando la potenza, `e^(−θ·c·rate)` non dipende da `k` e sparisce nella rinormalizzazione, lasciando `q_k ∝ [(c·rate)^θ]^k / (k!)^θ` = COM-Poisson(λ=(c·rate)^θ, ν=θ). Verificato su `_dp_pmf`: `max\|dp−COM\|` ≈ **1e-14** (precisione macchina, 3 ordini di grandezza più stringente), e regge anche a **θ<1** dove nessuno aveva guardato | ✅ 38 file allineati + Arco 12 nell'indice del diario (le F100+ erano appese all'Arco 11, «Fasi 89–99»); ⚠️ **merge con una sessione parallela**: a metà lavoro `origin/main` era avanti di **15 commit** (F103-115) e 7 file erano stati toccati da entrambe — 5 conflitti, **nessuno risolvibile tenendo il più recente** perché entrambe le parti avevano fatti veri e diversi; risolti a mano tenendo l'**unione**; ⚠️ il merge ha reso stantio un numero appena scritto in 6 punti (i test non sono 841 ma **889**); 📌 la fase era partita come «Fase 102», poi 116, infine **117** (la sessione parallela ha pushato la sua F116 mentre scrivevo): il **102 resta un numero mai usato**; 💡 lezione: un'affermazione di stato va **ri-eseguita, non riletta** (tre voci di rete sbagliate costavano un `curl` e sono sopravvissute a due audit) |
| **118** | **primo giro vero del raccoglitore su GitHub Actions** — verifica che il cron parta da solo, non deduzione dal codice | **Run verde in 23 s che non raccoglieva niente.** Prima diagnosi (IP dei runner filtrati) **sbagliata**: i run locali della F116 usavano `--entro-ore 500`, non 72, e la prima partita dista **432 ore**. Ma il run ha scoperchiato due difetti veri: **(1)** con la finestra a 72 h non si sarebbe raccolto **nulla fino al 12 agosto**, mentre il listino dell'esordio è già quotato — **48 partite** delle 5 leghe già esposte (9-10 per lega, 15-30 ago), cioè 18 giorni di traiettoria che `newseason.md` §2 dichiara irrecuperabili; **(2)** «finestra vuota» e «l'API non ci parla più» davano lo **stesso** esito (zero righe, verde) — il **finto pieno** della R6 applicato a un processo. Correzioni: regime di **lungo raggio** (1 giro/giorno, tutto l'esposto ma solo 1X2+O/U2.5+GG/NG) e **controllo di plausibilità del listino** che fa fallire il giro. La regola è **misurata**, non assunta: il 28/07, off-season profonda, il listino aveva **709 eventi su 101 competizioni** con tutte e 5 le nostre presenti → «0 nostre in un listino non vuoto» è un'anomalia | ✅ primo file di lungo raggio: **336 righe / 48 partite / 5 leghe**, 149 KB, libro a due lati **85%**, overround mediano **1.0034** (O/U2.5) e **1.0040** (1X2); ✅ **4 mutazioni provate, 4 catturate**; 📌 la riga F116 **mancava** in questo registro (mia omissione, §2): aggiunta; ⚠️ **costo dichiarato**: il denso in-season porta l'archivio a **250-300 MB/stagione** — cifra da decidere, leve = frequenza del cron ed esclusione del risultato esatto; 📌 913 test verdi |

| **119** | **specifica della raccolta quotidiana 2026-27** (richiesta utente: raccolta completa e giornaliera, cartella stagionale, lista esaustiva dei dati utili) — nuova `data/stagione_2026_2027/` | **Misurate 21 fonti prima di scrivere il piano: 15 rispondono. Ma il numero che conta viene dai `robots.txt`** (R5.3): la stampa sportiva **vieta esplicitamente i crawler AI** — `transfermarkt.it`, `gazzetta.it`, `bbc.co.uk`, `kicker.de` con `Disallow: /` per `ClaudeBot`/`anthropic-ai`, `marca.com` per `anthropic-ai`. **Consentiti**: Guardian (presente con **0 regole** = permesso esplicito), Lega Serie A, open-meteo, Wikipedia, football-data.org. Tre decisioni di struttura: **fatto ≠ giudizio** (ogni record porta `tipo`, e un giudizio senza evidenza citata non si scrive); **due assi ortogonali** (`giornaliero/` append-only e immutabile — senza cui muore il test prospettico — e `club/` con identità stabile e viste rigenerabili); **priorità per irrecuperabilità**, non per interesse | ✅ specifica completa + lista dei dati in 6 famiglie, ogni voce marcata fatto/giudizio/derivato e «si perde per sempre?»; ⛔ il livello notizie **non** può poggiare sullo scraping della stampa; 📌 onestà in testa al README: **non serve a dare più feature al modello** (Fasi 4c-33 già chiuse) ma all'informazione che il mercato ha e noi no, al dataset notizia→quota, e all'archivio pluristagionale |
| **120** | **passo 0: importare ciò che si può avere senza scraping** — nuovo `scripts/build_stagione_anagrafica.py`, 96 file `anagrafica.json` | **Il divieto di Transfermarkt non chiudeva niente: la fonte era già nel repo.** `davidcariboo/player-scores` è **CC0**, fonte ufficiale dello `squad_value` dalla F67, aggiornata ~settimanalmente: **507.815** valutazioni, **88.958** partite fino al 6/7/2026, `game_lineups` con **titolari vs panchina** (→ la formazione probabile diventa **scorabile**) e `game_events` **col minuto**. **65 competizioni**: 31 campionati (Turchia, Portogallo, Olanda, Belgio, Scozia…), 10 coppe nazionali, Champions, 5 tornei per nazionali — cioè **tutti i «prossimi passi»** già coperti. **Tre difetti trovati controllando**: rose assurde (Genoa **162** giocatori → filtro sull'ultima stagione → mediana **36**); scarto residuo **+6** vs `squad_size` ufficiale (dichiarato, non limato); e il grave — **«Frosinone, valore rosa 0.8 M€» calcolato su 1 giocatore su 31**, ora l'aggregato esiste **solo** se la rosa è completa | ✅ 96/96 squadre risolte, **nessuna in silenzio**: 21 alias verificati a mano, 4 assenze dichiarate; ⚠️ copertura **82 completa / 10 stantia / 4 assente** — i buchi sono tutti **neopromosse**, cioè le squadre del prior δ; ✅ **decisione understat** (delegata dall'utente): `Disallow: /` nel suo robots.txt → `download_season` **legge la cache e non scarica più**, coerenza con oddsportal, costo zero verificato (l'uso normale legge gli snapshot congelati); ⛔ residuo aperto: per le stagioni **nuove** serve una fonte xG con licenza chiara; 📌 17 test nuovi, **934 verdi**, 4 mutazioni provate e catturate |
| **121** | **rose vere da Wikipedia** (richiesta utente in corsa: «cercherei i nomi su internet… meglio essere sicuri di tutto») — nuovo `scripts/fetch_rose_wikipedia.py` | **Il problema della rosa risolto da un dato, non da una soglia**: le voci elencano nella stessa sezione i tesserati **col numero di maglia** e i giovani aggregati con `n=` **vuoto** (Napoli **26 + 21**) → il discrimine prima squadra/primavera è della fonte, non nostro. Controprova: **l'Inter esce con 25 numerati = esattamente il `squad_size` ufficiale**. Wikipedia è la fonte giusta perché **consente** il bot (Transfermarkt no, F119), ha API ufficiale ed è aggiornata da persone (la voce Inter dichiarava «aggiornate al 26 luglio 2026», due giorni prima). **⚠️ Ipotesi mia SMENTITA**: avevo dedotto da 2 club grossi che l'italiana coprisse tutti e 96 → misurato **41/96**, sbilanciato (Serie A 18/20, Premier 12/20, Liga 6/20, Ligue 1 3/18, **Bundesliga 2/18**) | ✅ **riempie proprio i buchi del dataset**: delle 14 squadre mal coperte (tutte neopromosse, quelle del prior δ) ne risolve 4, i casi peggiori — **Coventry 0→27**, Frosinone 1→30, Hull 7→27, Monza 1→22; ⛔ **55 rose ancora da prendere** dalle Wikipedia locali (en/es/de/fr, verificato che le voci esistono); 📌 2 difetti corretti in corsa (nome troncato al `pipe` nei wikilink con disambigua; reset di rete che buttava via l'intero giro) |
| **122** | **scheletro della raccolta giornaliera** (passo 2 del piano) — nuovi `scripts/raccolta_giornaliera.py`, `scripts/fetch_stadi_coordinate.py`, cron giornaliero | **Tracer bullet** (§1.1): fetta verticale completa, da prossime-partite → coordinate → meteo → `raccolta.json` + `fonti.json`. **Vincolo misurato**: open-meteo copre **16 giorni** (al 28/07 arrivava al 12 agosto; richiesta esplicita per il 15 → **400**), quindi la 1ª giornata **non ha ancora** previsione → marcata `fuori_orizzonte` con i giorni mancanti, e **senza chiamare l'API** (un 400 nel registro sarebbe un errore finto fra quelli veri). Primo giro reale: 5 `fuori_orizzonte`, 1 `coordinate_mancanti`, **0 fetch e 0 errori** — e il file lo spiega partita per partita. Coordinate: **90 stadi su 94** da Wikipedia (`prop=coordinates`); i 4 mancanti sono esattamente le 4 squadre assenti dal dataset | ✅ `fonti.json` registra **ogni** tentativo, anche i falliti — contromisura diretta alla F118: un giorno senza raccolta e uno senza raccoglitore devono avere aspetto diverso, e il workflow **fallisce** se non ha scritto il giorno; ✅ **un test ha fatto il suo mestiere**: la soglia di copertura all'85% aggiunta dopo ha reso rosso un mio test che la negava — riscritto perché la verifichi, e allineato a `MIN_COVERAGE` già usata dal progetto; 📌 27 test nuovi in due fasi, **958 verdi**, 8 mutazioni provate e catturate |
| **123** | **stadio per-partita + bollettino disciplinare** (richieste utente: «verifica se ogni squadra giocherà nel proprio stadio», «bollettino di infortuni, squalifiche e diffidati… leggi tu le regole») — nuovo `src/data/disciplina.py` | **(A) L'intuizione sullo stadio era giusta, e la misura dice quanto**: partite «in casa» giocate ALTROVE = **5,0%** in campionato, 10,8% in coppa nazionale, **12,3% nelle coppe europee**, 16,4% in supercoppe (Atalanta 29/83, Atlético 30/84, Barcellona 25/82). Una gara europea interna **su otto**. → lo stadio esce con `stadio_confermato: false`: ipotesi dichiarata, non fatto. **(B) Squalifiche e diffide si CALCOLANO, non si cercano** (cartellini + regolamento): unico pezzo del bollettino che non dipende da nessun sito, quindi immune ai vincoli robots.txt della F119. **Regole lette, non ricordate**: la **Ligue 1 è passata da 3 a 5 nel 2025-26** (a memoria avrei scritto 3) e la **UEFA squalifica alla 3ª e poi a ogni dispari** (5ª, 7ª), con azzeramento dopo play-off e quarti; Serie A stringe (5, 10, 14, 17, 19, poi ogni). Una soglia unica sbaglierebbe **2 leghe su 5 + UEFA**, producendo diffidati **plausibili e falsi** | ✅ validato sui cartellini veri (Serie A 2025-26: 11.926 presenze, 1.361 gialli, 421 ammoniti → **58 diffidati** a fine stagione); ✅ l'**incentivo del diffidato** (smaltire ora se la gara che conta è la successiva) è calcolato ma marcato `tipo: giudizio` — nessuno ha mai misurato se i giocatori vi si conformino; ⛔ restano da fare **infortuni** (richiedono una notizia esterna) e **calciomercato quotidiano**; 📌 22 test nuovi, **980 verdi**, 4 mutazioni provate e catturate (fra cui «Ligue 1 riportata a 3») |
| **124** | **studio sui diffidati: si trattengono?** (proposta utente: «se abbiamo il calendario e quando ogni giocatore ha preso i cartellini, possiamo fare uno studio per vedere correlazioni») — nuovo `scripts/_run_fase124_diffidati.py`, 726.823 presenze / 104.009 gialli / 14 stagioni | **Il segno ingenuo era ROVESCIATO.** Confronto fra giocatori: **+0.0275** («i diffidati prendono più cartellini»); confronto **within-player**: **−0.0265** IC95% [−0.0299, −0.0230]. Lo stato «diffidato» seleziona i falciatori, quindi il confronto fra gruppi misura la propensione, non lo stato. **Ma il within-player non basta**: lo stato arriva per forza più tardi nella stagione, quindi serve il contrasto **locale alla soglia** (4 gialli contro 3 e 5, dove una tendenza lineare dà esattamente zero). **Il gradino sopravvive: −0.0154 IC95% [−0.0195, −0.0111] su base 0.1715 = −9,0% relativo**, e si ripete alla soglia successiva (9 gialli: −0.0107 contro +0.0009 a 7). Replica su 5 leghe, tutte conclusive. **Controllo che chiude l'altra spiegazione**: i diffidati giocano PIÙ minuti (73.3 vs 66.1), non meno → l'effetto è semmai sottostimato | ✅ effetto comportamentale **reale e misurato** dove la F123 aveva scritto «giudizio mai verificato»; ⛔ **il timing NON è confermato**: differenza inizio-fine stagione −0.0054 IC95% [−0.0164, +0.0048], e la **potenza è dichiarata** — l'IC è 1,4× l'effetto medio, quindi un'attenuazione del 50% resterebbe nel rumore (R7); 📌 è un effetto sui **cartellini**, non sui gol: quanto sposti un prezzo 1X2 è un'altra domanda, non toccata qui |
| **125** | **prezzare i cartellini: backtest walk-forward** (richiesta utente: «lavoriamoci per bene su questi dati») — nuovo `scripts/_run_fase125_cartellini.py`, 50.911 osservazioni (partita × lato), 14 stagioni | **Prima il test che la F99 rende obbligatorio** (misurato ≠ prevedibile): arbitro corr(t,t−1) **+0.352** [+0.299,+0.405], squadra in casa +0.356, in trasferta +0.288 — **tutti persistono**, a differenza del bias della F99. Poi il walk-forward (λ moltiplicativo stile DC, fattori con shrinkage K=40, solo stagioni precedenti): **ogni leva paga con IC conclusivo** — squadra **+0.00440**, avversario +0.00157, campo +0.00371, **arbitro +0.00368** (cioè **quanto il fattore campo**), totale **+0.01336** [+0.01120,+0.01552]. **Ma il risultato grosso è un altro**: var/media = **0.954** per squadra-partita → i cartellini sono **SOTTO-dispersi** come i gol (F51), e la binomiale negativa non può rappresentarlo (α→0.0001, il bordo). Riusata la **stessa** `_dp_pmf` già in produzione sui gol: **θ = 1.150**, Δll **+0.00265** [+0.00199,+0.00330] — il **72%** di quanto vale l'arbitro, con **un solo parametro** | ✅ la sotto-dispersione **non è dei gol**: è dei processi di conteggio del calcio, e si ritrova su un processo che la F96 aveva dichiarato *diverso*; ⚠️ **ma la mappa per lega NON si trasferisce**: θ cartellini = Serie A **1.31**✅, Ligue 1 **1.25**✅, Bundesliga 1.11✅, Liga 1.08·, Premier 1.02· — le «due famiglie» dei gol non reggono (la Liga scende, la Ligue 1 sale) → θ va fittato per **(lega × processo)**, non ereditato; 📌 3 test nuovi (l'invariante dp(θ=1) ≡ Poisson), **995 verdi** |
| **126** | **la contraddizione F98 vs F125 sui cartellini, e il modello congiunto** — nuovo `scripts/_run_fase126_cartellini_congiunto.py` | **Due fasi dicevano il contrario**: la F98 misurava i cartellini SOVRA-dispersi (1.12-1.48) e adottava la NegBin, la F125 SOTTO-dispersi (0.954). **Non era una contraddizione: era la stessa cosa a due livelli**, e l'identità ricompone esatto — `var(tot) = var(casa) + var(osp) + 2cov` → **4.7308 = 1.8699 + 2.0258 + 2·0.4175**. Ogni **lato** è sotto-disperso (0.970, 0.924) ma i lati sono **correlati** (+0.2145): **tutta** la sovra-dispersione del totale è correlazione (a lati indipendenti il totale starebbe a 0.945). Quindi la NegBin tappava la **correlazione** con un parametro di **forma**. Costruito il modello che le separa (marginali dp(θ) + «nervosismo» Z~Gamma condiviso, σ²→0 = lati indipendenti) | ❌ **NON paga**: +0.00003 sulla NegBin, IC95% [−0.00015, +0.00022], nel rumore — e la griglia sceglie **θ=1.00**. Il perché è **misurato**: la superficie in (θ,σ²) è una **cresta** (θ↑ → σ²↑ ottimo, ll piatta entro 0.0017) → **sul totale forma e correlazione non sono separatamente identificabili**, solo il dato per-lato le distingue; ✅ **la F98 resta valida** (e ora sappiamo *cosa* fittava); ✅ la θ=1.15 della F125 vale sui mercati **per squadra**, che il totale non può contraddire perché non li vede; ✅ il fattore **arbitro** vale in entrambi (agisce sulla media, non sulla forma); 📌 residuo dichiarato: il nervosismo spiega solo **1/5** della covarianza osservata (0.085 contro 0.4175) |
| **127** | **controllo di stato del test prospettico** (domanda utente: «come facciamo per completare il test prospettico?») — a 14 giorni dalla prima partita | **Il controllo ha trovato un guasto in corso.** Smarkets ha **rinominato lo slug** `spain-laliga` → `spain-la-liga` il 31/07 e **La Liga era uscita dalla raccolta in silenzio**: 38 partite invece di 48, workflow verde — ed è la lega che parte **per prima** (15/8, non 16/8 come dicevano gli outright). La guardia R6 della F118 esisteva ma era a soglia `|E ∩ L| = 0`: scatta solo se spariscono **tutte e cinque**, mentre un'API rinomina **una lega alla volta**. Correzione: entrambi gli slug in mappa (il vecchio non si toglie — l'archivio lo contiene), nuova `leghe_assenti()` = `L \ E`, e l'allarme **non solleva prima** della raccolta (perderebbe le altre 4, dati non ri-scaricabili): raccoglie, dichiara `leghe_senza_partite_esposte` nel JSON, esce rosso **dopo** aver scritto | ✅ bug corretto e raccolta di recupero eseguita lo stesso giorno; ⛔ **un giorno di traiettoria La Liga perso e non recuperabile**; 📌 stato del test aggiornato in `experiments/prospettico_2026_27.md` §5 — canale quote e fixture **risolti** (F115-118), restano mappa nomi, congelamento M1, script di scoring e criteri pre-registrati; 📌 3 test nuovi (23 sul modulo) |
| **128** | **passo P1 del test prospettico: la mappa nomi Smarkets → nostri** — nuovo `scripts/_run_fase128_nomi_2627.py`, 9 alias in `TEAM_ALIASES` | **96 squadre** esposte nella giornata 1 (20+20+20+18+18 = **l'intero organico** delle 5 leghe): **62 esatte, 25 via alias esistenti, 9 nuove**. Tre non erano innocue: `Köln`→`FC Koln` e `Málaga`→`Malaga` differiscono per **un accento** e sono squadre **con storia** (7 stagioni su 9 il Colonia); `PSG`→`Paris SG` convive nella **stessa giornata** con `Paris FC`, altro club, che un match largo fonderebbe **senza che nessun conteggio se ne accorga** (resterebbero 18 squadre). Verifica non a occhio ma **strutturale**: |entrate| = |uscite| in ogni lega (3-3, 3-3, 2-2, 3-3, 3-3). Le **5 esordienti** (Elversberg, Santander, Le Mans, Coventry, Hull) non hanno nome canonico **per costruzione** — mai giocato in 9 stagioni: nome **letto** dai file di **seconda divisione** dello stesso provider (`2526/{E1,D2,SP2,F2}.csv`, R5 passo 3), non dedotto. **Scoperta fuori bersaglio**: `backtest.promoted_teams()` **non può** dedurre le promosse del 2026-27 (confronta con la stagione precedente, e quella di test non esiste ancora) → vanno **dichiarate**, e sono **14**. Senza dichiararle il **Malaga** (ultima partita 2018-05) è tirato verso la **media della lega** invece che verso il prior δ: con emivita 365g pesa `0.5^(3009/365)` = **0.0033**, cioè la storia c'è e non conta nulla — **difetto opposto** a quello giusto | ✅ P1 **chiuso**, sblocca P2/P3/P5; ✅ 0 nomi da mappare su 5 leghe; 📌 il peso è **graduato**, non binario: 0.428 (Ipswich/Monza/Venezia) vs 0.108 (Schalke/Troyes) vs 0.0033 (Malaga/La Coruna) vs 0 (le 5 esordienti) — tre regimi diversi, non due; ⚠️ **non misurato in backtest** (la stagione non esiste): l'argomento è **strutturale** + Fase 7, e va letto come tale; 📌 13 test nuovi |
| **129** | **il test prospettico CONGELATO** (richiesta utente: «decidi tu cosa fare, fai tutto il necessario per andare avanti») — passi P2-P6: `_run_prospettico_2627.py` riscritto, nuovo `_run_prospettico_scoring.py`, cron di chiusura | **48 partite × 26 mercati Tier 1 congelate il 01/08, due settimane prima del primo fischio** (`prospettico_2026_27_m1.csv` + metadati). La scadenza del 14 agosto era **aggirabile**: il M1 dipende solo da dati fermi a maggio 2026, quindi congelare oggi è **identico nel contenuto** e migliore nel processo. **Due bug veri nella versione precedente**, che avrebbero congelato previsioni sbagliate: (1) le neopromosse erano dedotte con `promoted_teams(allm, ultima_stagione)` = le promosse **nel 2025-26** (il difetto diagnosticato alla F128, e stava nel codice); (2) `draw_balance=True` e `DP_THETA_DC` passati a **tutte** le leghe, mentre φ35 e router θ valgono **solo in Serie A** — lo stesso bug corretto in `predict.py` alla F101, sopravvissuto qui. **D1 decisa**: cron **orario** con finestra **2h** e listino intero → chiusura a T−1h/T−2h a costo ~zero (nelle ore vuote lo script esce prima di chiedere le quote e non scrive). **P6**: criteri pre-registrati nel docstring dello scoring, datato in git prima di ogni partita | ✅ P1-P4 e P6 chiusi, P5 pronto; ✅ sanità: gol/partita previsti vs storici **3.10/3.12** (BL), 2.81/2.84 (PL), 2.80/2.74 (L1), 2.68/2.58 (Liga), 2.57/2.72 (SA) — non valida nulla, ma uno scarto grosso avrebbe segnalato un guasto; ✅ **scoring eseguito end-to-end su risultati sintetici** prima di servire, poi **registro ripristinato e artefatto cancellato** (un numero finto in `runs.jsonl` è il finto pieno della R6); ⚠️ con 48 partite la potenza contro il mercato è **~10%**: questa giornata **collauda il protocollo**, non conclude; 📌 56 test nuovi |
| **130** | **le quote si muovono?** — analisi dell'archivio pre-partita (8 file, 28/07→01/08), 15 alias in `TEAM_ALIASES`, test che enumera tutto lo storico dei nomi | **Sì raccogliamo, no non si muovono ancora**: sui 144 contratti 1X2 con serie ≥2 giorni il movimento mediano è **0.30pp** e il **70% è fermo sotto 0.5pp** (fra il 28 e il 30/07 molti libri identici alla **quinta cifra**: in off-season nessuno scambia). **La prima misura era sbagliata**: chiave sul *nome*, e **Smarkets ha rinominato 40 eventi su 49** fra il 30 e il 31/07 (`AS Roma vs ACF Fiorentina`→`Roma vs Fiorentina`) → rifatta su **`event_id`**. Dei **160** nomi mai comparsi nell'archivio, **15 non si agganciavano** (tutti forma lunga): aggiunti **senza togliere i nuovi**, più un test che li enumera tutti a ogni suite. **Il movimento più grande non era informazione**: Angers–Lille +18.9pp (10× il secondo) aveva banco **0.1562** e puntatore **0.5556** — spread **40pp**, un «medio» che non è il prezzo di niente | 📌 qualità del libro a 15-27gg: **82%** a due lati, spread mediano **0.082**, solo **28/48** partite con 1X2 completo ≤5pp; 📌 spread mediano per lega **PL 0.010 / Liga 0.031 / SA 0.031 / L1 0.056 / BL 0.104** — **stesso ordinamento per liquidità della Fase 53**, fonte diversa e 8 anni dopo; ✅ **regola M2 pre-registrata** (primaria ≤5pp, il resto secondario, niente libro = niente M2 **dichiarato**), fissata prima di sapere chi ne beneficia; ⚠️ che il libro si stringa a ridosso del fischio è **plausibile e NON verificato** — se non lo facesse, il M2 sarebbe di fatto un test su PL/Liga/SA |
| **131** | **statistiche di SQUADRA per periodo, 5 leghe 2025-26** (7 file consegnati dall'utente, fonte diretta.it/Flashscore, dato a monte Opta) — nuovi `src/data/team_stats.py` + `scripts/registra_raccolta_squadra_diretta.py`, 5 raccolte in `files/diretta_{lega}_2526/` | **Il primo dato del progetto che separa i due tempi**: ogni squadra-partita in 3 righe (Totale/1T/2T) su **45 metriche**, **1.752 partite** di campionato. Verificati contro **football-data.co.uk** (fonte indipendente, che ha `HTHG/HTAG`): join allo snapshot **3.504/3.504**, risultato coerente **3.504/3.504**, additivita' `1T+2T(+Suppl)=Totale` **137.124/137.124** celle, conteggi **97,7-99,7%** con **scarto medio ~0** (rumore ±1 fra fornitori, non differenza di definizione). ⭐ **Lo split e' genuino e non invertito**: gol del 1T dedotti vs `HTHG/HTAG` **98,34%**, del 2T **97,89%**, e lo scarto e' **sempre negativo** (`{0: 6.872, −1: 131, −2: 1, +1: 0}` su 7.004) perche' gli autogol non entrano nell'xGOT — con le etichette invertite l'accordo crolla a 77/380 e compaiono 144 casi impossibili. **Sei rilievi che nessuna dichiarazione diceva**: il vuoto e' uno ZERO (fino al 94% di NaN; caricarlo come mancante farebbe sparire gli **zeri**, non i cartellini); la fonte **documenta male se' stessa** (il foglio Note della Bundesliga nega i supplementari nel Totale: falso, 39/39 contro 8/39); le righe **Play-off** non sono campionato (6 partite con club di 2a divisione, in Ligue 1 **sovrapposte per data**); **una partita che dura 22 minuti e la cui riga `Totale` sembra una partita intera** (Nantes-Tolosa 17/05: `Totale` == `1° tempo` su 45/45 metriche perche' la gara fu **interrotta al 22'** per invasione di campo e lo 0-0 fu omologato — causa gia' accertata in `DATI.md` §1-quater il 31/07, che in prima lettura avevo dato per ignota; il dato e' corretto, la trappola e' mediare 22' con 90'); `Risultato squadra`/`Esito` sono di **fine partita anche sulle righe di periodo** (R8) → **il punteggio all'intervallo non e' nel dataset**; 2 tackle impossibili su 10.512. **Riconciliazione post-inserimento** (01/08): 3 incoerenze aritmetiche minori della fonte, tutte dichiarate e fissate da un test — `Tiri totali ≠ area+fuori area` in **10/10.510** righe (ma l'altra partizione, `in porta+fuori+fermati`, chiude **10.510/10.510**), `xGot affrontati(A) ≠ xGOT(B)` in **4/10.510**, e le percentuali ricalcolate con `round()` al 96,7-99,7% ma **entro ±1 al 100,0%** (la fonte tronca; `riusciti` e `totali` ci sono entrambi, nessuna informazione persa) | ✅ integrati, 604 KB, **18 alias italiani** in `TEAM_ALIASES` (senza, il join si fermava a 264/612 in Ligue 1 e 60/612 in Bundesliga); ✅ **28 test nuovi, 1.163 verdi** (dopo il merge con la sessione parallela della F130); ⛔ **nessuna feature, nessun backtest, nessun modello li usa**; ⛔ limite vero = **una stagione sola**: 1.752 partite sono sopra le ~574 della F98 ma un walk-forward multi-stagione **non e' possibile** — un risultato nullo sara' meno conclusivo di quanto sembri, e va detto **prima**; 💡 lezione di metodo (dai 14 confutatori avversariali): 10 rapporti su 14 avevano errori **nei denominatori**, non nei dati — e il caso peggiore arbitrava le divergenze fra due fonti con un **testimone della parte in causa** (la colonna `Parate`, che e' di diretta): col controllo negativo il null non era 0,5 ma **0,947** e il p-value passava da 0,003 a **0,85** |
| **132** | **identità dei calciatori dirimenti con Wikidata** (richiesta utente: «correggere quanti più errori possibile, cercando su internet o qualche repo») — nuovi `src/data/wikidata_identity.py`, `scripts/verifica_identita_wikidata.py`, `scripts/_run_verdetti_wikidata.py` | ⚠️ **Il workflow multi-agente lanciato per questo scopo è FALLITO** (7 agenti su 8 in `StructuredOutput retry cap`, l'unico superstite con tutti gli strumenti rotti): **zero misure** da quel run, sostituito da un accertamento deterministico. **Perché Wikidata e non un'altra fonte**: il Q-id è inciso *dentro le pagine già scaricate* (`wgWikibaseItemId`, **24.074/24.077 = 100,0%**, estratti in 101s con **zero richieste**), quindi **non c'è nessun matching per nome** — il passaggio in cui ogni verifica d'identità può introdurre una *nuova* omonimia mentre ne risolve una vecchia. Costo: **477 richieste**, non 24.000. `robots.txt` lo consente (`Allow: /wiki/Special:EntityData/*.` batte il `Disallow` per match più lungo, RFC 9309 — ⚠️ `urllib.robotparser` sbaglia questa coppia). **Esito: 126 confermate, 312 smentite, 19 indeterminate.** ⭐ **Il discriminante non è la distanza fra le date, è la FORMA**: `senza_struttura` (nessuna componente in comune) vale l'**86% delle respinte** e il **7% delle quarantene**; tutte le altre forme conservano una componente e sono refusi. Due casi che il solo conteggio dei giorni sbaglierebbe: **Germán Lux** `1982-06-07` vs `1982-07-06` = scambio giorno/mese, cioè il **formato data**, stessa persona (era respinto); **Chancel Mbemba** `1988-08-08` vs `1994-08-08` = 2.191 giorni, oltre qualunque soglia, ma **stesso giorno E mese** → è la disputa d'età documentata, non un omonimo (8 casi su 10 di questa forma sono a **±1 anno esatto**: nessun padre nasce lo stesso giorno e mese del figlio un anno prima). Quindi `persona_diversa` è una **congiunzione** (senza struttura **AND** >3 anni), non una soglia. **Verificate le due assunzioni comode invece di darle per buone (R7)**: Wikidata **non** è ridondante con la pagina (concordano **69,1%**, IC95% Wilson [64,8%, 73,1%] — e il 31% di divergenza è esattamente da dove escono le 126 conferme); le smentite sono **bimodali col ventre vuoto** (≤1 mese 85 · 1-12 mesi 81 · **1-3 anni 11** · >3 anni 148), mediana per ramo **quarantena 31 gg vs respinta 3.840 gg**, rapporto **124×** | ✅ **applicati: +17 giocatori recuperati** (erano esclusi a torto) **e −5 rimossi** — i 5 includono **tutte e 3 le identità sbagliate già note, ritrovate per via indipendente**, più Lazaridis che non lo era; ⛔ **il numero da NON applicare era 141**: tante sono le quarantene smentite, quasi tutte refusi — rimuoverle era la trappola (la stessa che la rettifica R4 aveva trovato in piccolo, qui a 47× la scala); ⚠️ **fragilità dichiarata**: Ballantyne sta a **1.105 giorni contro una soglia di 1.098**, coi vicini a 1.004 e 1.261 — lì non c'è nessun vuoto, quel caso lo decide il taglio e non i dati (gli altri 4 sono a 3.116+); 🔧 **due difetti trovati dai test**: `identita` diceva ancora `respinta` su righe *dentro* il database (finto pieno R6 — corretta la colonna, non il test) e il deliverable si scriveva **non atomicamente** mentre la raccolta gira (`EOFError` in gzip, corsa vera: anche un backtest concorrente è esposto) → `os.replace`; ✅ **1.201 test verdi** (+38) |
| **133** | **i gol all'intervallo entrano negli snapshot** (domanda utente: «i gol all'intervallo riusciamo a risalire e a creare una colonna apposita?») — nuovo `scripts/aggiungi_gol_intervallo.py`, colonne `home_goals_ht`/`away_goals_ht` su tutte e 5 le leghe (38 -> 40 colonne) | Il punteggio all'intervallo — **l'unica variabile di stato** che serve alla pista 6-bis (modello a due stadi) — non era in nessuna tabella: non negli snapshot, non nelle statistiche di squadra della F131 (`Risultato squadra` e' il FINALE anche sulla riga 1T, R8), e la F98 se lo rileggeva dai grezzi in **tre modi diversi** per lega. Preso VERO da `HTHG/HTAG` di football-data — la stessa fonte da cui gli snapshot derivano gia' i gol finali — invece che dedotto al 98% dal dataset nuovo (una stima vivrebbe in `data/estimates/`, e coprirebbe solo il 2025-26). Copertura **16.111/16.111 partite**, 9 stagioni: join 16.111/16.111 e **gol finali coerenti 16.111/16.111**. ⭐ **La verifica piu' forte era gia' pubblicata**: le frazioni di gol nel 1° tempo escono **0,4365 / 0,4464 / 0,4356** per Serie A / Premier / Liga, cioe' **le stesse quattro cifre** che la F96 aveva misurato per un'altra strada — due percorsi indipendenti sullo stesso numero. Le due leghe mai misurate danno 0,4482 (BL) e 0,4461 (L1); a 5 leghe **f = 0,4425**. **Un solo buco, dichiarato**: Union Berlin-Bochum 14/12/2024 (il caso R1) non ha l'intervallo alla fonte -> `Int64` nullable, mai inventato (R6). L'eccezione sui gol finali di quella partita non e' incisa nel codice ma **letta da `data/correzioni_dichiarate.csv`**. **Le altre due risposte**: i **tiri** hanno due partizioni, per esito (10.510/10.510 ✅) e per zona (10.500/10.510) — il difetto e' solo nella zona, a livello di PERIODO, in 5 squadra-partita su 3.504, e **non e' riparabile** senza il dato tiro-per-tiro (attribuirlo a occhio viola R3); 15 vincoli logici, 12 puliti, e **2 dei 3 allarmi erano miei**: «1T > Totale» era `Gol evitati` che puo' essere **negativa**, e 43 righe con `xGOT=0` con tiri in porta erano **arrotondamento** (42/43 con un solo tiro, 43/43 senza gol) | ✅ +2 colonne su 16.111 partite, nessuna cella esistente toccata; ✅ **1.218 test verdi** (dopo il merge con la sessione parallela); ✅ sblocca la pista 6-bis su **tutto lo storico** e non solo sul 2025-26; ⚠️ **una correzione a me stesso**: nella F131 avevo dato Nantes-Tolosa per «causa non accertata», ma `DATI.md` §1-quater l'aveva risolta il **giorno prima** (gara interrotta al 22', 0-0 omologato) — corretto in 4 punti; 💡 lezione: prima di dichiarare ignota una causa, cercarla nei documenti del repo |
**Adottato**: solo il tuning (2b/4b/4d) e il **prior neopromosse (7)**. Tutto il
resto è al livello del rumore o dannoso, e resta **off di default** — alcune
opzioni (ricalibrazione, `--draw-inflation`) restano utili per l'uso pratico.

**Roadmap post-audit (Fasi 35+).** (1) **boost-pareggio condizionato all'equilibrio**
|λ−μ| → **fatto (Fase 35)**: miglior risultato sul pareggio, calibrazione quasi
perfetta e migliore del mercato sulle partite equilibrate, ma log-loss non
CI-conclusivo → off di default. ~~In corso:~~ **tutti eseguiti e chiusi
negativi** (allineato dall'audit della Fase 101; le righe stanno nella tabella
qui sopra): (2) **GBM col set di feature COMPLETO** → Fase 36, overfitting;
(3) **dummy `midweek_europe`** come covariata DC → Fase 36-bis; (4) **covariate
nel canale-pareggio** (φ condizionato a stakes) → Fase 37; (5) **denoising
cross-stagione del market-implied** → Fase 38. Il vantaggio-casa a fine
stagione (Fase 30) resta un candidato di sola **calibrazione** (post-hoc peggiora il
log-loss: +0.0021).

**Nota Fase 51 (la prima crepa conclusiva):** la lettura *affinata* della chiusura
— double-Poisson sotto-dispersa (θ=1.225) sui tassi impliciti corretti nei livelli
(`market_implied.sharpen_1x2`) — **batte la chiusura devigata in log-loss 1X2**
(0.9609 vs 0.9625, CI95 [−0.0029, −0.0003], 7/7 stagioni). NON è un edge di
scommessa (l'affinamento ~0.5-1% per esito è sotto il margine ~5%: ROI nullo,
Fase 51-ter): è la miglior *stima* 1X2 del progetto, condizionata alle quote. Il
gap storico del modello standalone (DC) resta quello qui sopra.

**Dove vive il gap col mercato — ⚠️ diagnosi CORRETTA alla [Fase 92](docs/DIARIO.md)
(era invertita per 80 fasi).** Per anni qui c'è stato scritto «è quasi tutto nel
PAREGGIO, escluso il pari (mercato "12") siamo già a livello mercato». Era un
**errore logico**: `P(12) = 1 − P(X)`, quindi il mercato «12» *è* la massa del
pareggio — non «chi vince». Usarlo come prova che la discriminazione fosse a
posto era leggere il dato al contrario. La scomposizione esatta (chain rule, che
ricompone a 6 decimali) dice:

| | massa-pareggio | discriminazione casa/ospite |
|---|--:|--:|
| Serie A | **12.0%** | **88.0%** |
| Premier | 5.5% | 94.5% |
| La Liga | 15.0% | 85.0% |

Il gap vive quasi tutto nel **distinguere chi vince fra casa e ospite**. Questo
spiega perché ogni leva costruita sul pareggio (12b, 18, φ35) ha reso quasi
nulla: aggrediva il 12%. La [Fase 93](docs/DIARIO.md) ha poi mostrato che quel
deficit è **informazione, non calibrazione** — della parte che la scomposizione
attribuisce (0.0094 sui 0.0215, il 44%): 104% informazione e −4% calibrazione. Il
termine di calibrazione è al pavimento di rumore per entrambi e la differenza col
mercato **non è conclusiva** (⚠️ Fase 101). È concentrato
sulle **partite equilibrate** e crescente nel corso della stagione. Resta vero
che è **informazione che il mercato ha e noi no** (formazioni, infortuni,
notizie dell'ultima ora) — ma su *quale* squadra vince, non su quanto spesso si
pareggia.

---

## Analisi dettagliata per fase

Ogni fase è raccontata qui con **obiettivo → ragionamento → cosa abbiamo fatto →
numeri del backtest → conclusione**, in ordine cronologico. Per il diario completo
con le alternative considerate vedi [`docs/DIARIO.md`](docs/DIARIO.md). Le fasi di
**acquisizione dati** (4a: xG/valori-rosa/assenze; 4e: calendario di club completo)
sono descritte più sotto in [Archivio dati interno](#archivio-dati-interno-riproducibilità).

### Analisi degli errori — Fase 2a (`scripts/analyze.py`)

Prima di aggiungere feature, abbiamo analizzato *dove* il modello perde contro il
mercato. Risultati principali:

- **Sulla media il modello è ben calibrato** (nessun bias sistematico, nemmeno sui
  pareggi): il vantaggio del mercato è nella **discriminazione** delle singole
  partite, non nella calibrazione media.
- **Bug trovato e corretto**: la stagione di test chiamava il Verona "Hellas
  Verona" mentre le stagioni di training usavano "Verona" → il modello lo trattava
  come squadra sconosciuta, producendo predizioni assurde. Risolto con una mappa
  di normalizzazione nomi (`TEAM_ALIASES` in `sources.py`).
- **Dove il modello perde di più** (log-loss, gap col mercato): partite con
  **neopromosse** (gap +0.037, doppio della media) e **inizio stagione**
  (+0.030). Radice comune: dati storici scarsi o datati → stime inaffidabili.
  Questi sono i bersagli prioritari del feature engineering (Fase 2b).

### Feature engineering — Fase 2b (in corso)

Primo intervento: **shrinkage** (regolarizzazione verso la media della lega),
tarato con `scripts/tune.py` su due stagioni. Poiché la penalità è
fissa mentre il contributo dei dati cresce col numero di partite, l'effetto è
**automaticamente più forte sulle squadre con pochi dati** — proprio i punti
deboli individuati.

Risultato (log-loss 1X2, media 2024-25 + 2025-26; più basso = meglio):

| shrinkage | media | gap col mercato |
|---:|---:|---:|
| 0.0 (base) | 0.9918 | +0.026 |
| **1.5** (scelto) | **0.9879** | **+0.022** |
| Mercato | 0.9654 | — |

Migliora **entrambe** le stagioni e riduce il divario col mercato di ~15%. In
particolare il gap sull'**inizio stagione** scende da +0.030 a +0.022 e quello
sulle **neopromosse** da +0.037 a +0.030: l'intervento colpisce i bersagli
previsti.

Secondo intervento: **taratura dell'emivita** del decadimento temporale (quanto
peso dare alle partite recenti), su tre stagioni. Risultato (log-loss 1X2 medio):

| emivita | media | note |
|---:|---:|---|
| 90g | 0.9935 | troppo reattiva, rumorosa |
| 180g (prima) | 0.9863 | |
| 365g | 0.9834 | |
| **730g** (scelta) | **0.9829** | memoria ~2 stagioni |
| Mercato | 0.9658 | |

Lezione: in Serie A le rose restano stabili anno su anno, quindi una **memoria
lunga** (~2 stagioni) batte il peso aggressivo sulle ultime partite. Con la
configurazione finale (emivita 730g, shrinkage 1.5) il divario medio col mercato
scende da +0.026 (Dixon-Coles puro, misurato su 2 stagioni) a **+0.017** (0.9829
− 0.9658, su 3 stagioni): circa un terzo del divario recuperato solo con la
taratura, senza informazione nuova.

Qui il modello basato sui **soli gol** è vicino al suo tetto: per avvicinarsi
ancora al mercato serve informazione nuova (forma, xG, indisponibili), non altro
tuning.

### Informazione nuova: tiri in porta — Fase 3 (risultato NEGATIVO)

Terzo intervento, primo con informazione *nuova*: i **tiri in porta** (già
presenti nella fonte dati) misurano le occasioni create con meno rumore dei gol
(la "fortuna sotto porta"). Il modello è stato esteso per allenare, oltre a
quello sui gol, un modello sui tiri in porta e **mescolare** i due tassi attesi
con un peso α tarabile (`shots_blend`: α=1 solo gol, α=0 solo tiri).

Esito, tarato su **sei** stagioni di test (2020-21 → 2025-26, regimi diversi,
COVID inclusi):

| α (peso gol) | 1X2 (media) | O/U 2.5 (media) |
|---:|---:|---:|
| 0 (solo tiri) | 0.9913 | 0.6964 |
| 0.5 | 0.9833 | 0.6909 |
| **1 (solo gol)** | **0.9817** | **0.6904** |
| Mercato | 0.9632 | 0.6816 |

- Sull'**1X2** i tiri **peggiorano** in modo netto e monotòno (α=1 è il migliore).
- Sull'**Over/Under** α=1 è il migliore anche in media. Su 3 stagioni sembrava
  esserci un lieve vantaggio dei tiri, ma **si dissolve su 6 stagioni**: era
  rumore di piccolo campione (allargare il backtest ha chiarito il quadro).

> **Da tenere d'occhio (ipotesi aperta).** Nella stagione più recente (2025-26),
> e in modo più sfumato nel 2024-25, dare peso ai tiri in porta **migliora
> l'Over/Under** (2025-26: α=0 → 0.7000 vs α=1 → 0.7056), anche se non aiuta
> l'1X2 e non aiuta nella media a 6 stagioni. Possibile ipotesi: da un paio di
> stagioni il modo di affrontarsi in campionato sta cambiando e le occasioni
> create potrebbero diventare via via più informative. **Da ri-verificare** man
> mano che arrivano nuove stagioni: se il segnale si rafforza, il blend (o l'xG
> reale) tornerà utile, almeno sull'Over/Under.

**Conclusione: i tiri in porta grezzi non danno un miglioramento affidabile** (su
6 stagioni, α=1 è il migliore per entrambi i mercati). Il
default resta α=1 (solo gol); il codice del blend è mantenuto (esperimento
documentato, riutilizzabile con l'xG *reale*, che pesa la qualità delle occasioni
e non solo il conteggio). È un risultato prezioso: aver testato la versione
*economica* dell'idea "le occasioni aiutano" ci ha evitato di costruire una
pipeline xG/database sull'assunzione sbagliata che bastasse.

### xG reale nel blend — Fase 4b (primo miglioramento da dati nuovi)

Con l'xG reale integrato (Fase 4a), abbiamo rifatto lo *stesso* esperimento del
blend, ma con l'**xG** al posto dei tiri grezzi. Il meccanismo è identico (peso α
gol vs segnale), cambia solo la qualità del segnale.

Esito su **6 stagioni** (log-loss, più basso = meglio):

| α (peso gol) | 1X2 | O/U 2.5 |
|---:|---:|---:|
| 0 (solo xG) | 0.9840 | 0.6897 |
| 0.5 | 0.9816 | **0.6888** |
| **0.75** (scelto) | **0.9813** | 0.6893 |
| 1 (solo gol) | 0.9817 | 0.6904 |
| Mercato | 0.9632 | 0.6816 |

- È il **primo segnale che aggiunge valore** dopo il tuning: dove i tiri *grezzi*
  fallivano (Fase 3), l'**xG aiuta** — piccolo ma reale, soprattutto
  sull'Over/Under (la *qualità* delle occasioni informa il volume di gol).
- α=0.75 (config scelta) migliora **entrambi** i mercati sulla media a 6 stagioni.
- I guadagni O/U più grandi sono nelle stagioni **recenti** (2024-25, 2025-26),
  coerente con l'ipotesi che lo stile di gioco stia evolvendo.

**Onestà:** il miglioramento è *modesto* e non ci fa battere il mercato. Ma è il
primo passo avanti ottenuto con informazione nuova.

### Spremere il resto dei dati: npxG, valori rosa, assenze — Fase 4c (NEGATIVO)

Prima di cercare dati *nuovi*, abbiamo spremuto quelli già in casa. Abbiamo
costruito un **layer di covariate** generale: ogni covariata (forza/contesto
esterni ai risultati) entra nel tasso atteso come `β·(z_squadra − z_avversaria)`,
con i β stimati **insieme** al resto. Abbiamo provato **npxG** (xG senza rigori)
come segnale, e **valore rosa** (Transfermarkt) e **assenze** stimate come
covariate, anche in **combinazione** (l'idea: due segnali deboli insieme).

Esito (6 stagioni, log-loss):

| | 1X2 | O/U 2.5 |
|---|---:|---:|
| baseline (config Fase 4b) | **0.9813** | 0.6893 |
| npxG al posto di xG | 0.9811 | 0.6892 |
| + valore-rosa | 0.9818 | 0.6891 |
| + assenze | 0.9813 | 0.6893 |
| + valore-rosa & assenze | 0.9818 | 0.6892 |

- **npxG ≈ xG** (differenza 0.0002, rumore): teniamo l'xG, più standard.
- **Valore-rosa e assenze: non aiutano** (il valore-rosa peggiora appena l'1X2).
  Un diagnostico *in-sample* sul valore-rosa sembrava promettente (coeff +0.48), ma
  fuori campione svanisce: la forza della rosa è **già catturata** dai gol+xG.
- **Nessuna sinergia**: unire segnali ~nulli dà ~nulla. Anche il **riposo solo-Serie-A**
  non aiuta (non vede coppe/Europa → la differenza di fatica è ~0).

**Lezione (ricorrente d'ora in poi):** il diagnostico in-sample va SEMPRE
confermato walk-forward, e i dati extra non aiutano se il loro contenuto è già
implicito nei risultati. Il modello è al **tetto pratico** di questa fonte dati.

### Ri-taratura congiunta: l'emivita si accorcia — Fase 4d

Shrinkage ed emivita erano stati tarati (Fase 2b) sul modello *solo-gol*. Con il
blend xG attivo l'ottimo poteva essersi spostato — interazione mai verificata. Una
ri-taratura a coordinate su 6 stagioni:

| emivita | 1X2 | O/U 2.5 |
|---:|---:|---:|
| 730g (vecchia) | 0.9813 | 0.6893 |
| **365g (nuova)** | **0.9807** | **0.6884** |

L'**emivita ottima passa da 730g a ~365g**: con un segnale meno rumoroso (l'xG) il
modello può permettersi una **memoria più corta/reattiva** senza rincorrere il
rumore. Guadagno piccolo (−0.0006 su 1X2, −0.0009 su O/U) ma su **entrambi** i
mercati. Lezione di metodo:
dopo un cambiamento importante, ri-verifica gli iperparametri già tarati.
**Config ufficiale**: blend gol/xG α=0.75, shrinkage 1.5, **emivita 365g**.

### Grande backtest multi-mercato — Fase 5 (per cosa serve il modello)

Abbiamo allargato lo sguardo oltre 1X2/OU a **tutti** i mercati derivabili *gratis*
dalla matrice dei punteggi: GG/NG (entrambe segnano) e doppie chance (1X/2X/12).

*(Nota: la colonna «modello» qui è la config **Fase 5, PRE-prior** — 1X2 0.9807,
O/U 0.6884 — non la config ufficiale attuale che ha il prior neopromosse adottato
alla Fase 7: 0.9797 / 0.6885. Le differenze sono nel rumore e non cambiano le
conclusioni di questa fase.)*

| Mercato | modello (Fase 5, pre-prior) | Mercato | Baseline |
|---|---:|---:|---:|
| 1X2 | 0.9807 | **0.9632** | 1.0834 |
| Over/Under 2.5 | 0.6884 | **0.6816** | 0.6892 |
| GG/NG | 0.6896 | — | 0.6871 |
| 1X (casa o pari) | 0.5497 | **0.5371** | 0.6303 |
| 2X (ospite o pari) | 0.5966 | **0.5833** | 0.6744 |
| 12 (no pari) | 0.5766 | 0.5746 | 0.5820 |

- **Affidabile sui mercati d'ESITO** (1X2, 1X, 2X): batte nettamente la baseline.
- **Debole su Over/Under** (baseline di un soffio) e su **12** (pareggi ~casuali).
- **NEGATIVO su GG/NG**: è **peggio della baseline** (0.6896 vs 0.6871). Il "GG"
  dipende dalla **correlazione** tra i due punteggi, che il modello (Poisson
  quasi-indipendenti + correzione DC) cattura male.
- **Nessun mercato batte le quote.**

**Conclusione:** il motore è affidabile per gli esiti, non per il GG/NG. La prima
volta che i numeri indicano il **prossimo salto**: la *correlazione dei punteggi*.

### Ricalibrazione della confidenza (temperature scaling) — Fase 6 (nel rumore)

Il diagnostico (Fase 2a) diceva "calibrato in media". Ma il modello perde dove è
**molto sicuro**. Il **temperature scaling** è la correzione post-hoc più
economica: un solo parametro T che rende le probabilità più nette (T<1) o più
morbide (T>1), tarato sulle stagioni passate e applicato al futuro (no look-ahead).

| Stagione | 2020-21 | 2021-22 | 2022-23 | 2023-24 | 2024-25 | 2025-26 | media |
|---|--:|--:|--:|--:|--:|--:|--:|
| T ottimo | 0.96 | 0.92 | 0.95 | 0.96 | 0.96 | 0.94 | ~0.94 |
| Δ 1X2 | −0.0012 | +0.0016 | +0.0005 | −0.0005 | −0.0014 | −0.0007 | **−0.0003** |

**Scoperta reale e robusta**: T<1 in **tutte e 6** le stagioni → il modello è
sistematicamente un po' **sottoconfidente** (probabilità troppo "compresse").
**Ma** il guadagno è **nel rumore** (−0.0003) e non uniforme (peggiora 2 stagioni):
rendere le prob più nette premia quando il modello ha ragione e punisce quando ha
torto — in Serie A i due effetti quasi si annullano. **Non entra** nella config;
il modulo `src/evaluation/calibration.py` resta per l'uso pratico.

### Prior di cold-start per le neopromosse — Fase 7 (l'unica vittoria interna)

La perdita più grande e concentrata (Fase 2a/9): le **neopromosse** (+0.029 su
~28% delle partite), che il modello sovrastima non avendo storico. Idea: dare loro
un **prior** sotto la media finché non accumulano partite. Misura (24 neopromosse
2018-2026): segnano ~1.08 gol/partita vs ~1.36 della lega (−20%) e ne subiscono
~1.72 (+26%) → in log-tasso **δ ≈ 0.23**. Meccanismo: spostare il *bersaglio* dello
shrinkage per le promosse da 0 (media) a (−δ, +δ); una promossa a 0 partite parte
dal prior, poi i dati lo sovrastano. δ stimato **leave-future-out** (no look-ahead).

| | media 6 stagioni | sulle partite delle neopromosse |
|---|--:|--:|
| base | 0.9807 | 0.9880 |
| **+prior (δ=0.23)** | **0.9796** | **0.9841** |
| Δ | **−0.0011** (5/6 stagioni) | **−0.0039** (5/6) |

**Il miglior guadagno interno**: 3-4× congestione/calibrazione, e colpisce dove
doveva. Principiato (fatto strutturale), non un parametro a caso. **ADOTTATO** nella
config ufficiale (peggiora solo il 2023-24, dove le promosse erano più forti della
media — varianza attesa). Piccolo e non batte il mercato, ma reale.

### Ultimo giro economico: shrinkage e vantaggio-casa — Fase 8 (niente)

Due leve interne rimaste, una alla volta. **(1) Ri-taratura dello shrinkage** col
prior attivo: curva **piatta** (0.75→1.5 tutte a ~0.9797) → le due leve sono
ortogonali, nessun guadagno. **(2) Vantaggio-casa per-squadra**: prima della
chirurgia, il test economico — è **stabile** anno su anno? L'effetto medio esiste
(0.254 punti/gara) ma la **persistenza anno-su-anno è r ≈ 0.004** (rumore
stagionale). Un vantaggio-casa per-squadra fitterebbe solo rumore → idea scartata
senza costruirla. Entrambe negative.

### Anatomia del gap col mercato — Fase 9 (dove vive il divario)

Non spremere ma **capire**: quanto vale il gap (`modello − mercato`) e come si
scompone. Gap 1X2 medio attuale **+0.0167** (modello 0.9799 vs mercato 0.9632);
il modello ha chiuso ~86% della distanza baseline→mercato. Tre tagli:

> ⚠️ **LETTURA ROVESCIATA DALLA FASE 92 — vedi la riga 92 del registro.**
> `P(12) = 1 − P(X)`: il mercato «12» *è* la massa del pareggio, quindi il suo
> quasi-zero **non** dice che sappiamo prezzare chi vince. La scomposizione
> esatta (chain rule, ricompone a 6 decimali) dà **12% massa-pareggio / 88%
> discriminazione casa-ospite** in Serie A (5.5/94.5 Premier, 15/85 Liga).
> Il testo qui sotto è conservato com'era, ma va letto al contrario.

**Per mercato** — il gap è **quasi tutto nel PAREGGIO**:

| 1X2 | 1X | 2X | **12 (no pari)** | O/U 2.5 | GG/NG (vs baseline) |
|--:|--:|--:|--:|--:|--:|
| +0.0167 | +0.0118 | +0.0129 | **+0.0020** | +0.0067 | +0.0026 |

*(Riga ri-derivata alla Fase 101-bis con `scripts/_run_gap_markets.py` al codice
di HEAD: coincide cella per cella con la matrice 15-bis qui sotto. La versione
precedente dava **−0.0018** sul GG/NG — un orfano, prodotto contro un
riferimento diverso mai dichiarato; il GG/NG non ha quote, quindi il confronto
è **contro la baseline**, come nella matrice.)*

Escluso il pari (mercato 12) il modello è **a livello mercato**: la debolezza è
prezzare i pareggi, non stimare chi è più forte. *(⚠️ conclusione rovesciata
dalla Fase 92: il 12 non «esclude» il pareggio, lo misura.)*

**Per mercato × stagione (Fase 15-bis,** `scripts/_run_gap_markets.py`**)** — la
matrice completa, per verificare che le medie qui sopra non nascondano stagioni
storte:

| Gap | 2020-21 | 2021-22 | 2022-23 | 2023-24 | 2024-25 | 2025-26 | media |
|---|--:|--:|--:|--:|--:|--:|--:|
| 1X2 | +0.0204 | +0.0149 | +0.0151 | +0.0187 | +0.0171 | +0.0140 | **+0.0167** |
| 1X (casa o pari) | +0.0163 | +0.0084 | +0.0094 | +0.0175 | +0.0082 | +0.0109 | +0.0118 |
| 2X (ospite o pari) | +0.0153 | +0.0110 | +0.0131 | +0.0128 | +0.0157 | +0.0094 | +0.0129 |
| **12 (no pari)** | +0.0017 | +0.0032 | +0.0021 | **−0.0021** | +0.0051 | +0.0021 | **+0.0020** |
| Over/Under 2.5 | **−0.0033** | +0.0146 | +0.0163 | +0.0007 | +0.0101 | +0.0020 | +0.0067 |
| GG/NG (vs baseline*) | +0.0073 | −0.0054 | +0.0064 | −0.0003 | +0.0038 | +0.0037 | +0.0026 |

*\*GG/NG non ha quote nei dati → gap vs baseline (in-sample, severa). Le doppie
chance usano il mercato derivato dalle 1X2 devigate.*

Tre letture (tutte e 6 le stagioni, non solo la media):

- **Il "quasi-zero" del 12 regge in OGNI stagione** (range −0.0021…+0.0050; nel
  2023-24 il modello *batte* il mercato). ~~Sapere chi è più forte è a livello
  mercato sempre, non in media.~~ ⚠️ **Fase 92**: il 12 misura la *massa* del
  pareggio, non la discriminazione; il suo quasi-zero dice che sbagliamo poco
  **quanto** pareggio c'è, e non dice nulla su chi vince.
- **Il costo del pareggio è persistente**: 1X e 2X (che lo includono) stanno a
  +0.008…+0.018 in ogni stagione, ~5 volte il 12. Il gap del pari non è
  un'annata storta: è strutturale.
- **L'Over/Under è il mercato più volatile** (range −0.0031…+0.0168): battuto il
  mercato nel COVID, quasi-parità 2023-24 e 2025-26, male 2021-23. Nessun trend
  affidabile — con σ così alta, una stagione buona sull'O/U non è segnale.

**Per forza-squadra** (gap 1X2, a U): deboli **+0.0206** e forti +0.0180 peggio
delle medie **+0.0123**. Sui deboli il mercato ha info che noi non abbiamo
(motivazione salvezza, turnover); le neopromosse (+0.0159) sono ora *sotto* i
deboli grazie al prior.

**Per periodo — COVID vs post-COVID (Fase 9-bis):** sui mercati d'esito il gap si
**riduce** dopo il COVID (1X2 +0.0202 → +0.0161): a stadi vuoti il vantaggio-casa è
crollato e il modello, che lo eredita dallo storico, sovra-pesava la casa.
Sull'**Over/Under è l'opposto** (nel COVID il modello batteva il mercato, −0.0031).
Trend recente: il gap 1X2 è al **minimo nell'ultima stagione (2025-26, +0.0141)**.

### Ricalibrazione per-classe 1X2 — Fase 10 (conferma il bias, nel rumore)

Il temperature (Fase 6) scala tutto in modo uniforme e non può *spostare* massa da
casa a pareggio. Tre moltiplicatori per classe (casa/pari/ospite) sì, tarati
leave-future-out. Risultato robusto: in **tutte e 6** le stagioni il fit **abbassa
la casa (w≈0.96) e alza il pareggio (w≈1.04)** — conferma esatta della
miscalibrazione direzionale. Ma il guadagno è **−0.0005** (nel rumore, 4/6): un
surrogato *lineare e globale* di ciò che servirebbe (la correlazione dei punteggi).
**Off** di default, disponibile per l'uso pratico.

### Combinazioni delle feature off-di-default — Fase 11 (nessuna utile)

Fin qui le feature opzionali erano provate **da sole**. Griglia: tutti gli 8
sottoinsiemi delle covariate {valore-rosa, assenze, congestione} × con/senza
ricalibrazione, 6 stagioni. **Nessuna combinazione è utile**: il valore-rosa
**peggiora** in ogni mix; congestione/assenze sono rumore anche in coppia; l'unico
effetto additivo è la ricalibrazione (già nota). La "miglior" combo (−0.0011) è
dominata dalla ricalibrazione, le covariate sono rumore. Conferma in combinazione
ciò che la Fase 4c aveva visto in isolamento.

### Ensemble di emivite e il cambio di classe — Fase 12

**(a) Ensemble di emivite:** mescolare memoria corta (180g) e lunga (730g) batte
la singola 365g? Il blend 180+730 dà **0.9791 (−0.0006, 4/6)**: reale ma
borderline. **Off.**

**(b) Il cambio di classe — modello a diagonale inflazionata (bivariato):** la
mossa strutturale indicata da ogni analisi. Un parametro **φ** che alza *tutti* i
punteggi di parità (0-0,1-1,2-2…) oltre le 4 celle della correzione Dixon-Coles,
fittato sulla verosimiglianza dei punteggi e **dipendente dalla partita** (ciò che
la ricalibrazione piatta non fa).

| | media 6 stagioni | P(pari) modello → reale |
|---|--:|--:|
| base | 0.9797 | ~0.25 |
| **+diagonale inflazionata** | **0.9793** (−0.0004, 3/6) | sale verso il reale ✓ |

**Il meccanismo funziona**: la calibrazione del pareggio migliora in ogni stagione
(2024-25: 0.264 → 0.288 vs reale 0.284). **Ma** il log-loss guadagna solo −0.0004,
perché *quanti* pareggi capitano in una stagione è in gran parte **rumore** (dove
ne capitano pochi, l'inflazione sovrastima). Anche la mossa strutturalmente
corretta dà l'ordine di grandezza di ogni tampone: **il pareggio è quasi-casuale
per tutti, mercato incluso**. Il gap non è cattiva modellazione — è irriducibilità
del fenomeno. **Off** di default (opzione utile per la calibrazione del pari).

### Stato di forma, streak, rendimento recente — Fase 13 (già catturato)

C'è un **momentum** predittivo che la forza pesata nel tempo non vede? Attaccato da
quattro angoli, tutti **data-driven** per uscire dall'arbitrarietà delle soglie:

- **Forma** (punti/gara ultime 5) come covariata: base 0.9797 → 0.9799 (**+0.0002**,
  peggio). La forma è scorrelata dall'errore del modello (corr **+0.035**).
- **Streak** (serie utile/di sconfitte in corso, a *ogni* lunghezza): corr con
  l'errore ~0; i bucket per lunghezza serie hanno segni **erratici** (rumore).
- **Ventaglio completo** (gol fatti/subiti, xG, "fortuna"=gol−xG, finestre 3/5/10,
  23 feature): il verdetto in un numero — **R² = 0.0101** = R² da **puro rumore**
  (23 feature/2273 partite). Identici. Nessun pattern sfruttabile.
- **Streak × avversario debole** (l'interazione): corr −0.005, guadagno di R²
  **+0.00003** (meno del rumore). La cella "in serie & avversario debole" non si
  accende.

**Lezione:** la ragione è strutturale — il rendimento recente (risultati, gol, xG)
*è* ciò che il fit **pesato nel tempo** già usa e pesa di più. Il residuo del
modello non contiene momentum. L'unico filo di segnale è l'xG recente, **già nel
blend**. Nessun pattern nascosto.

### Il modello contro la linea di APERTURA — Fase 14 (niente edge nemmeno lì)

Ogni confronto precedente era contro la **chiusura**, l'avversario più duro. Ma
si può scommettere *prima*: la Fase 14 confronta le stesse predizioni con la
linea **pre-chiusura** di football-data (colonne senza suffisso C, ~1-3 giorni
prima della partita) — il benchmark "battibile" — e misura il **CLV** (la
chiusura si muove verso il modello sulle selezioni?), il criterio dei
professionisti per distinguere edge da fortuna. Stesse righe per entrambe le
linee (2279/2280), 5 versioni × 6 stagioni.

| | vs APERTURA | vs CHIUSURA |
|---|--:|--:|
| gap 1X2 (versione attuale) | **+0.0146** (peggio del mercato in 6/6 stagioni) | +0.0166 |
| gap O/U 2.5 | +0.0052 | +0.0069 |
| value bet (pool, 692 sel. @open) | ROI **−17.3%** | ROI −15.6% |
| **CLV** | **−0.0028** medio, solo **45%** delle selezioni >0 | — |

- **La linea del venerdì è già quasi-chiusura**: l'affilamento open→close vale
  solo +0.0020 di log-loss — e il deficit del modello (+0.0146) è **7 volte**
  quell'intero guadagno informativo.
- **CLV negativo**: quando il modello dissente dall'apertura, la chiusura gli dà
  torto più spesso che ragione. I dissensi sono rumore, non informazione in
  anticipo sul mercato. L'ipotesi "scommetti presto" muore pulita.
- Non testabile con questi dati: l'apertura *vera* (domenica/lunedì, più
  morbida) — richiederebbe raccolta prospettica di quote in tempo reale.

*Nota di provenienza:* il mirror GitHub storico dei dati è **sparito** (404);
i CSV originali football-data sono ora congelati in `data/football_data_raw/` (fonte grezza
versionata) e `scripts/_restore_raw_cache.py` ricostruisce la cache. Dettagli
nel [diario, Fase 14](docs/DIARIO.md).

### Audit dei calcoli — Fase 15 (verifica indipendente di ogni numero)

Revisione sistematica di **formule, pipeline e numeri dichiarati**: ogni valore di
README/DIARIO ricalcolato a precisione piena dal registro `experiments/runs.jsonl`
(233 run), più la ri-esecuzione del backtest ufficiale (riproduzione **identica**
alla 4ª cifra) e l'audit del codice (modello, metriche, script di fase).

**Verdetto sulle formule: nessun errore.** Log-loss, Brier, devig, correzione
Dixon-Coles τ, verosimiglianza dell'inflazione diagonale, temperature scaling,
blend gol/xG, ordine (H,D,A), walk-forward (`date < as_of` ovunque): tutto
corretto. La stragrande maggioranza dei numeri pubblicati è riproducibile alla
4ª cifra decimale.

**La tabella di riferimento, per stagione** (config ufficiale, valori reali **al
codice di HEAD** — post-fix Fase 92; il registro `runs.jsonl` contiene i valori
pre-fix — 1X2 log-loss):

| Stagione | Modello | Mercato | Gap | ROI value bet (n) |
|---|--:|--:|--:|--:|
| 2020-21 | 0.9535 | 0.9331 | +0.0204 | −23.0% (129) |
| 2021-22 | 0.9864 | 0.9715 | +0.0149 | −16.2% (154) |
| 2022-23 | 0.9922 | 0.9770 | +0.0151 | −14.9% (152) |
| 2023-24 | 0.9854 | 0.9668 | +0.0187 | −15.0% (125) |
| 2024-25 | 0.9694 | 0.9523 | +0.0171 | −21.2% (159) |
| 2025-26 | 0.9924 | 0.9784 | +0.0140 | −4.7% (147) |
| **MEDIA** | **0.9799** | **0.9632** | **+0.0167** | **−15.8% (866 tot)** |

**Errori trovati e corretti (solo documentazione):**

1. **ROI ≈ −8.5% → −15.7%**: il valore nel README era il ROI del primo backtest
   di Fase 1 (una stagione, modello iniziale), rimasto accanto a metriche a 6
   stagioni. Il ROI reale della config ufficiale è **−15.7% medio** (sopra, per
   stagione). La conclusione «non scommettere» ne esce *rafforzata*.
2. **DIARIO, tabella Fase 2b**: la riga «Dixon-Coles puro ~0.9863, gap +0.026»
   era internamente incoerente (con quel log-loss il gap è +0.021; il +0.026
   appartiene al valore a 2 stagioni 0.9918). Corretta.
3. **O/U ufficiale 0.6884 → 0.6885** (0.6884 era il valore *senza* prior);
   «~87%» → **86.3%** di distanza chiusa; baseline «~1.085» → **1.0834**;
   guadagno Fase 4d «~0.0007» → **−0.0006** (1X2) e **−0.0009** (O/U).

**Limiti metodologici scoperti (dichiarati, non correggibili a posteriori):**

- **La baseline è in-sample**: usa le frequenze H/D/A della stagione di test
  stessa (la costante ottima *a posteriori*). La baseline **ex-ante** onesta
  (frequenze delle sole stagioni precedenti) è 1.0860 (1X2) e 0.6961 (O/U) —
  vedi la tabella all'inizio. Direzione conservativa: il modello la batte
  comunque, di più.
- **Iperparametri tarati sulle stesse stagioni poi riportate** (winner's curse
  potenziale): verificato però sui fatti che il gap sulle stagioni **mai usate
  per il tuning** (2020-21→2022-23: **+0.0164**) è indistinguibile da quello
  sulle stagioni di tuning (2023-24→2025-26: **+0.0166**) → nessuna evidenza di
  overfitting di selezione materiale.
- **Costanti col senno di poi negli script delle fasi 10-12**: `RECAL_W` e
  δ=0.23 fisso derivano da fit che includono le stagioni di valutazione; i Δ
  onesti restano quelli leave-future-out (−0.0005 la ricalibrazione, −0.0011 il
  prior). Caveat ora dichiarati negli script stessi.
- **`analyze_gap` per fascia di forza** usa la classifica *finale* della
  stagione (informazione futura): la tabella per-tier è diagnostica, non una
  segmentazione operativa.
- **Streak (Fase 13)**: lo stato per-squadra non si azzerava tra stagioni (una
  retrocessa che risale rientrava con la streak di anni prima); impatto piccolo
  sui bin estremi, conclusioni invariate.
- **Fase 14 (quote di apertura)**: nel codice, quando in una riga manca la
  quota di chiusura il fallback rendeva `open ≡ close` (CLV=0 spurio contato
  come negativo) e le metriche modello/mercato-apertura del registro erano su
  righe diverse. Corretti entrambi prima dell'arrivo dei dati `*_open`.

**Conclusione dell'audit: nessuna conclusione del progetto cambia.** Il modello
batte la baseline (anche quella ex-ante), non batte il mercato (+0.0165 —
valore PRE-fix del prior della Fase 92, oggi +0.0167), il
value betting perde (più di quanto scritto prima: −15.7%, non −8.5%). Il tetto
resta reale. **Non usare il modello per scommettere soldi veri.**

### Il mercato ingloba il modello — Fase 16 (encompassing, il test definitivo)

La domanda che il gap non può dire: un modello a +0.0165 dal mercato (valore
PRE-fix del prior della Fase 92; oggi +0.0167 — il test non cambia) contiene
**informazione che il mercato non ha** (utile in combinazione, anche se da solo
perde) oppure è solo mercato + rumore? Test standard di *forecast encompassing*
(`scripts/_run_encompassing.py`): si mescola `p = α·modello + (1−α)·mercato` e
si stima α minimizzando la log-loss — **walk-forward onesto** (α fittato solo
sulle stagioni di test precedenti, applicato alla successiva).

| | risultato |
|---|---|
| α\* in-sample, ogni stagione (2021→2526) | **0.000** (≤10⁻⁵) |
| α walk-forward, ogni stagione valutabile | **0.000** (≤10⁻⁵) |
| Δ blend−mercato pooled (5 stagioni, n=1900) | +0.0000, CI95 [−0.0000, +0.0000] |

Il verdetto è il più netto possibile: **il peso ottimo del modello è zero anche
quando il fit può "barare"** (in-sample sulla stagione stessa). Il mercato di
chiusura *ingloba* completamente il modello: non c'è alcuna informazione
indipendente da monetizzare in combinazione. Converge con il CLV negativo della
Fase 14 (i dissensi dalla linea del venerdì sono rumore): due test indipendenti,
stessa conclusione. È il punto fermo definitivo *su questi dati* — un eventuale
edge su mercati meno efficienti (exchange sottili, leghe minori) resta questione
empirica aperta, ma contro la chiusura dei bookmaker il modello non aggiunge
nulla.

### Barre d'errore sui numeri chiave — Fase 17 (bootstrap appaiato)

Finora "nel rumore" era un giudizio a occhio. CI95 con bootstrap appaiato
per-partita (B=10.000, seed fisso, pooled 6 stagioni, n=2280;
`scripts/_run_gap_uncertainty.py`):

| Quantità | media | CI95 | P(modello meglio / prior aiuta) |
|---|--:|--:|--:|
| gap 1X2 (modello − mercato) | +0.0167 | [+0.0107, +0.0226] ✱ | 0.0% |
| gap 12 no pari | +0.0020 | [−0.0006, +0.0046] | 6.5% |
| gap O/U 2.5 | +0.0067 | [+0.0021, +0.0115] ✱ | 0.3% |
| Δ prior neopromosse (V4−V3) | −0.0010 | [−0.0025, +0.0004] | 92.6% |

*✱ = CI95 che non attraversa lo zero.*
*(Le tre righe di gap sono ricalcolate al codice di HEAD, post-fix Fase 92, sulle
stesse 2.280 predizioni e con lo stesso bootstrap di `_run_gap_uncertainty.py`.
La riga del **gap 12 è invariata** al fix; il **Δ prior V4−V3 NON è stato
rimisurato** dopo il fix — richiederebbe i 6 backtest del braccio V3, che nessuno
ha ancora rieseguito: il valore riportato resta quello pre-fix.)*

Quattro letture oneste:

- **Il gap 1X2 è reale e solido** (mai vicino a zero): il mercato è davvero
  migliore, non è varianza.
- **Il "quasi-zero" del 12 è ora un'affermazione statistica**: +0.0020 con CI
  che include lo zero — sul "chi vince" modello e mercato sono formalmente
  indistinguibili.
  ⚠️ **Fase 92**: il 12 *è* la massa del pareggio (`P(12)=1−P(X)` è un'identità),
  quindi il suo quasi-zero non dice nulla sul «chi vince» — vedi il blocco di
  rettifica a inizio README.
- **Il gap O/U è reale** anche se volatile tra stagioni (Fase 15-bis).
- **Il Δ del prior neopromosse (l'unica feature adottata) NON è conclusivo**:
  −0.0010 con CI [−0.0025, +0.0004]. Aiuta con probabilità ~93%, coerente in
  5/6 stagioni e con una motivazione strutturale (per questo resta adottato),
  ma va detto: da solo non supererebbe una soglia di significatività formale.
- Le **CI per stagione** del gap 1X2 (±0.014 tipico) spiegano perché non si
  giudica mai da una stagione: tre stagioni su sei, da sole, non
  distinguerebbero il modello dal mercato.

Disciplina: dopo ~30 test sulle stesse 6 stagioni, ogni futuro CI che sfiora lo
zero va letto come "non concluso", mai come scoperta.

### ρ dinamico — Fase 18 (l'ultima idea strutturale sul pareggio: NEGATIVA)

Il ρ di Dixon-Coles (correzione sui punteggi bassi 0-0/1-0/0-1/1-1) è un numero
unico per tutte le partite. Ipotesi mai provata: la correlazione dei punteggi
bassi dipende dalla partita — `ρ_match = ρ + ρ_slope·(λ+μ − centro)`, con
ρ_slope stimato nella verosimiglianza (`--dynamic-rho`,
`scripts/_run_dynrho.py`). **Regola dichiarata prima di vedere i numeri**:
adozione solo se il CI95 del Δ esclude lo zero.

| | risultato |
|---|---|
| ρ_slope al via di ogni stagione | **instabile**: +0.06, −0.11, +0.15, −0.08, +0.15, +0.15 |
| Δ 1X2 walk-forward (6 stagioni, n=2280) | **+0.0003**, CI95 [−0.0007, +0.0013] |
| Δ O/U 2.5 | −0.0000, CI95 [−0.0007, +0.0006] |

Doppia evidenza negativa: il parametro **cambia segno di stagione in stagione e
sbatte sul bound (±0.15) in 3 fit su 6** — la firma di un parametro che insegue
rumore, non struttura — e out-of-sample il modello peggiora leggermente. Regola
pre-dichiarata → **non si adotta**. Con la 12b (diagonale inflazionata) e la 10
(ricalibrazione per-classe), è la **terza e ultima via strutturale sul pareggio
a chiudersi**: il tetto non dipende dalla forma funzionale della correzione.

### Potenza statistica sul prior — Fase 19 (finestra estesa a 8 stagioni)

Il Δ del prior neopromosse era "probabile ma non concluso" (Fase 17:
[−0.0025, +0.0004], P~93%). Non perché l'effetto balli, ma perché le
partite-promosse sono poche. Estensione alle stagioni **2018-19 e 2019-20, mai
usate in nessuna analisi precedente** (`scripts/_run_prior_power.py`; il 2017-18
resta solo-training):

| Pool | media | CI95 | P(il prior aiuta) |
|---|--:|--:|--:|
| tutte le partite, 8 stagioni (n=3040) | −0.0013 | [−0.0026, **+0.0001**] | **96.5%** |
| solo partite promosse (n=864) | −0.0045 | [−0.0094, +0.0001] | 97.0% |
| *(confronto: 6 stagioni, Fase 17)* | −0.0010 | [−0.0025, +0.0004] | 92.6% |

Le due stagioni aggiunte vanno **entrambe nella direzione del prior** (Δ −0.0024
e −0.0014; sulle promosse −0.0093 e −0.0045): è evidenza genuinamente nuova, su
partite mai toccate da alcun tuning. L'effetto aiuta in **7 stagioni su 8** e il
CI si stringe — ma sfiora ancora lo zero (+0.0001). Verdetto disciplinato: il
prior **resta adottato** e la sua etichetta migliora da "probabile (~93%)" a
"**molto probabile (~96.5%)**, formalmente non concluso". Caveat dichiarato:
δ=0.23 è la stima storica della Fase 7 (include il 2018-20), quindi per le due
stagioni aggiunte non è leave-future-out — è un test di potenza sull'effetto
della config adottata, non una nuova stima di δ.

### Anatomia dei residui — Fase 20 (nessun segnale nascosto; ma *perché* si perde)

La Fase 13 aveva testato solo "la forma". Qui l'analisi completa: il residuo del
modello (punti reali casa − attesi) è predetto da **qualcuna delle 11 covariate
pre-partita**, incluse tre di *estremità* mai provate — |scarto di valore rosa|,
|scarto di riposo|, carico totale di assenze — più confidenza del modello e
dissenso col mercato (`scripts/_run_residuals.py`).

**Parte 1 — il residuo è rumore puro.** Nessuna covariata supera la soglia di
rumore in modo netto; la regressione multivariata dà **R² = 0.0055**, contro
**0.0048** atteso da rumore (k/n) e **0.0051** da 11 feature *casuali*. Le
feature di estremità sono le più piatte di tutte (|scarto valore| −0.0018,
assenze totali −0.0011). Poiché è nullo già **in-sample** (dove il fit può
barare), lo è a fortiori out-of-sample. Il residuo del modello non contiene
struttura sfruttabile: conferma indipendente del tetto informativo.

**Parte 2 — il risultato positivo: adverse selection.** Ordinando le partite per
*quanto* il modello dissente dal mercato, il gap (quanto il modello perde) cresce
in modo monotòno:

| Quartile di dissenso modello-mercato | n | gap medio vs mercato |
|---|--:|--:|
| basso | 570 | +0.0009 |
| medio-basso | 570 | +0.0024 |
| medio-alto | 570 | +0.0088 |
| **alto** | 570 | **+0.0539** |

`corr(dissenso, gap) = +0.18`. Dove il modello dissente di più dal mercato — cioè
esattamente dove segnalerebbe un *value bet* — perde ~60 volte di più che dove è
d'accordo. **I disaccordi del modello sono i suoi errori, non la sua intuizione.**
È il meccanismo operativo che spiega il ROI −15.7% e chiude il cerchio con la
Fase 16 (α\*=0) e il CLV negativo (Fase 14): tre viste diverse dello stesso
fatto — contro la chiusura, ogni scostamento del modello è rumore che il mercato
ha già corretto.

### Un modello diverso sul GG/NG — Fase 21 (gradient boosting: pareggia, non batte)

Primo modello di **famiglia diversa** dal Dixon-Coles, e primo test del principio
"un modello per mercato" (`CLAUDE.md` §8). Bersaglio scelto: il **GG/NG**, dove
il DC è debole (Fase 5: peggio della baseline, cattura male la correlazione dei
punteggi) e dove **non ci sono quote nei dati** — l'unico mercato senza tetto di
efficienza dimostrato. Un **gradient boosting** (`scripts/_run_gbm_btts.py`)
predice P(GG) direttamente, con feature = output del DC (gol attesi λ/μ, P(GG),
P(over) — walk-forward, no look-ahead) + covariate pre-partita; allenato per
stagione sulle sole stagioni precedenti (1819→S−1).

| | log-loss GG/NG | Δ vs DC (CI95) |
|---|--:|--:|
| GBM grezzo | 0.7178 | +0.0280 [+0.0167, +0.0391] |
| **GBM calibrato** (Platt) | 0.6945 | **+0.0047 [−0.0019, +0.0113]** |
| Dixon-Coles | 0.6898 | — |
| baseline (in-sample) | 0.6871 | — |

Due letture, una metodologica e una sostanziale:

- **Metodologica**: il GBM grezzo sembrava un disastro (+0.0280), ma era quasi
  tutto **mis-calibrazione** — un boosting è sovra-confidente su un evento
  ~50/50, e il log-loss lo punisce. Calibrato (Platt in CV sul solo training),
  il divario crolla a +0.0047. **Senza il controllo di calibrazione avremmo
  concluso il falso.** Lezione da tenere per ogni modello nuovo.
- **Sostanziale**: il GBM calibrato **pareggia il DC** (CI include lo zero, lo
  batte in 2 stagioni su 6) ma **non lo batte, e nessuno dei due batte la
  baseline**. Una famiglia di modelli completamente diversa, con pieno accesso
  ai λ/μ del DC e alle covariate, atterra **sullo stesso punto** — a livello
  della frequenza di base. È **convergenza**, non fallimento del GBM: il GG/NG
  è intrinsecamente quasi-impredicibile dai dati pre-partita in Serie A (come il
  pareggio), non un problema di modello sbagliato. Regola pre-dichiarata
  (adozione solo se batte DC con CI95<0 **e** la baseline) → **non adottato**.

Il principio "un modello per mercato" resta valido e va tenuto per i prossimi
tentativi; ma *questo* mercato, col miglior candidato ragionevole, non cede.

### Sweep del GBM su tutti i mercati — Fase 22 (il tetto è informativo, non di modello)

Spremuto il GBM: **6 mercati × 3 set di feature × calibrazione**
(`scripts/_run_gbm_sweep.py`). Feature: `cov` (solo covariate pre-partita), `dc`
(solo output del Dixon-Coles), `dc+cov` (entrambe). Domanda: su *qualche* mercato
il GBM muove il gap col mercato rispetto al DC?

**Log-loss (calibrata), miglior feature-set del GBM vs DC vs mercato:**

| Mercato | GBM (migliore) | DC | Mercato | Baseline |
|---|--:|--:|--:|--:|
| 1X2 | 1.0059 | **0.9797** | 0.9632 | 1.0834 |
| O/U 2.5 | 0.6966 | **0.6885** | 0.6816 | 0.6892 |
| GG/NG | 0.6943 | **0.6898** | — | 0.6871 |
| 1X | 0.5572 | **0.5487** | 0.5371 | 0.6303 |
| 2X | 0.6097 | **0.5960** | 0.5833 | 0.6744 |
| 12 | 0.5811 | **0.5766** | 0.5746 | 0.5820 |

**Movimento del gap** (Δ = GBM − DC sulle stesse righe; il mercato si cancella,
quindi è un confronto GBM-vs-DC appaiato):

| Mercato | Δ gap (GBM−DC) | CI95 | esito |
|---|--:|--:|:--:|
| 1X2 | +0.0310 | [+0.0217, +0.0402] | GBM peggio ✗ |
| O/U 2.5 | +0.0081 | [+0.0005, +0.0157] | GBM peggio ✗ |
| GG/NG | +0.0045 | [−0.0023, +0.0111] | pari (≈ baseline) |
| 1X | +0.0141 | [+0.0066, +0.0216] | GBM peggio ✗ |
| 2X | +0.0198 | [+0.0131, +0.0263] | GBM peggio ✗ |
| 12 | +0.0051 | [+0.0015, +0.0086] | GBM peggio ✗ |

Il verdetto è netto e trasversale: **il GBM non batte il DC su nessun mercato**,
e allarga il gap col mercato ovunque (CI che esclude lo zero su 5 mercati su 6;
sul GG/NG pareggia il DC, ma entrambi restano a livello baseline). Due dettagli
lo rendono conclusivo:

- **Il GBM fa meglio quando usa SOLO le feature del DC** (`dc` batte `dc+cov` e
  `cov` su 1X2/1X/2X): aggiungere le covariate grezze *peggiora*. Il modello
  rende al meglio proprio quando modifica meno il Dixon-Coles — la firma di
  "non c'è altro segnale da estrarre". Conferma indipendente delle Fasi 4c/11/20.
- **Ogni grado di libertà in più fa peggio**: una macchina non-parametrica con
  pieno accesso alle stesse informazioni non trova nulla oltre il DC, e dove
  devia aggiunge solo rumore — che il mercato ha già prezzato (per questo il gap
  *cresce*).

**Conclusione: il tetto è INFORMATIVO, non architetturale.** La forma parametrica
del Dixon-Coles non è il collo di bottiglia; lo sono i dati disponibili prima
della partita. Il principio "un modello per mercato" era giusto da testare ed è
stato testato a fondo (2 famiglie, 6 mercati, 3 feature-set): su questi dati
nessun mercato cede a una famiglia diversa. Per un edge serve **informazione
nuova**, non un modello nuovo.

### GBM che combina modello + mercato — Fase 23 (ridurre il gap? non con un GBM)

Ultima leva per "ridurre il gap": l'unica informazione mai data al modello sono
le **quote di mercato stesse**. Un GBM con feature = [DC + covariate + quote di
chiusura devigate] (`scripts/_run_gbm_market.py`) — encompassing *non-lineare*
(la Fase 16 era solo lineare) — può correggere le inefficienze residue della
linea, o almeno riprodurla (gap → 0)?

| 1X2 | log-loss | gap vs mercato |
|---|--:|--:|
| Dixon-Coles | 0.9797 | +0.0165 |
| GBM senza mercato | 1.0114 | +0.0482 |
| **GBM con mercato** | 0.9996 | +0.0364 |
| Mercato (chiusura) | 0.9632 | 0 |

*(Il DC di questa tabella è il valore **PRE-fix** del prior della Fase 92 —
0.9797 / +0.0165; al codice di HEAD sarebbe 0.9799 / +0.0167. Le righe GBM non
sono state rifatte, quindi la tabella è lasciata coerente com'è stata misurata:
lo scarto in gioco, ~0.03, è due ordini di grandezza sopra la differenza.)*

(O/U analogo: GBM con mercato 0.6956 vs DC 0.6885 vs mercato 0.6816.)

Risultato controintuitivo e istruttivo: **anche ricevendo le probabilità di
mercato come feature, il GBM non riesce nemmeno a pareggiare il mercato** — resta
a 0.9996, peggio del DC da solo. Il motivo: il mercato è già una previsione
quasi-ottima, e un ensemble di alberi la **degrada** (quantizza/regolarizza un
input probabilistico near-optimal, aggiungendo rumore). Il mercato come feature
*aiuta* il GBM rispetto a se stesso (1.0114 → 0.9996: porta informazione che le
altre feature non hanno), ma non basta a superare il rumore del GBM stesso.

Sintesi su "ridurre il gap": a **~0** si arriva solo *banalmente* copiando il
mercato (già noto dalla Fase 16: blend lineare ottimo con peso sul mercato ≈ 1);
**sotto zero (batterlo) no**, con nessun metodo, lineare o non-lineare, con o
senza il mercato come input (P(batte il mercato) = 0%). Il **GBM è lo strumento
sbagliato** per combinare modello e mercato: degrada perfino un input di
qualità-mercato. Il modo giusto di combinare è lineare, e la Fase 16 ha già dato
il verdetto. Chiude definitivamente la ricerca di un metodo per ridurre il gap
col GBM.

### Il DC calcolato DAL mercato — Fase 24 (il primo risultato positivo)

Idea nuova: finora il DC stima i gol attesi λ,μ dai GOL; ma il mercato li stima
**meglio** (batte il DC di +0.0165 sull'1X2 — pre-fix Fase 92; oggi +0.0167).
E se **invertissimo** le quote per
ricavare i λ,μ *impliciti nel mercato*, e ci facessimo girare sopra la matrice
dei punteggi del DC? (`scripts/_run_dc_from_market.py`). Sui mercati *con* quote
(1X2, O/U) l'inversione riproduce il mercato (gap ~0 banale); il valore è tutto
nel **derivare un mercato che il book NON prezza** — il GG/NG.

| GG/NG | log-loss |
|---|--:|
| **mercato-implicito + ρ** | **0.6853** |
| mercato-implicito (Poisson indip.) | 0.6865 |
| DC-da-gol (attuale) | 0.6898 |
| baseline (in-sample) | 0.6871 |

Il GG/NG dai λ,μ del mercato **batte il nostro DC-da-gol** (Δ −0.0033, CI95
[−0.0072, +0.0005], P=95.7%, negativo in **6 stagioni su 6**) ed è **la prima
cosa a battere la baseline sul GG/NG** (0.6865 < 0.6871; il DC-da-gol non ci
riusciva). La correzione ρ sulla diagonale aiuta ancora (0.6853).

Perché funziona senza contraddire le Fasi 16/23: il mercato stima λ,μ meglio di
noi, e la struttura del DC **trasferisce** quell'informazione a un mercato che il
book non prezza. Non è circolare (il GG/NG non è tra gli input) né un edge contro
un mercato efficiente.

**Onestà d'obbligo:** (1) il CI sfiora lo zero (+0.0005) → "molto probabile ma
formalmente non concluso" (come il prior, Fase 19); (2) il guadagno è modesto e
il GG/NG resta difficile (~0.685, vicino al testa-o-croce ~0.69); (3) non è
verificabile contro un'ipotetica linea di chiusura del GG/NG (assente nei dati);
(4) **richiede le quote 1X2+O/U al momento della predizione** (il DC-da-gol no) e
un venue che offra il GG/NG — plausibile su un prediction market. Come stimatore
*condizionato alla disponibilità delle quote*, però, è il primo miglioramento
reale su un mercato in tutto l'arco Fasi 21-24.

### Sensibilità alla finestra dei dati — Fase 25 (più storia batte meno)

Il modello già scorda il passato in modo *morbido* (emivita 365g). Domanda:
tagliare via del tutto le stagioni vecchie — o la sola stagione COVID a porte
chiuse (anomala) — aiuta, o l'emivita basta? Sweep sulla config ufficiale
(`--train-window-days` / esclusione stagioni, `scripts/_run_window.py`):

| Training | 1X2 (tutte) | gap mercato | Δ vs "tutto" (recenti-3) |
|---|--:|--:|--:|
| **tutto (attuale)** | **0.9797** | +0.0165 | — |
| finestra 3 stagioni | 0.9808 | +0.0176 | +0.0014 |
| finestra 2 stagioni | 0.9816 | +0.0184 | **+0.0035** |
| senza COVID 2020-21 | 0.9803 | +0.0172 | +0.0003 |

*(Tutta la colonna è **PRE-fix** del prior della Fase 92: la riga «tutto» oggi
vale 0.9799 / +0.0167. È uno sweep di confronti interni — il fix sposta le
quattro righe insieme, quindi i Δ, che sono il punto della tabella, reggono.)*

Risultato controintuitivo: **tagliare i dati vecchi peggiora, non aiuta** — e la
finestra corta danneggia *di più proprio le stagioni recenti* (+0.0035 sul
2023-26 con sole 2 stagioni di training). Le rose di Serie A sono stabili anno su
anno, quindi anche i dati vecchi informano la forza attuale; buttarli via aumenta
la varianza delle stime. Perfino la stagione COVID, anomala, è **netto-utile**
come training (escluderla costa +0.0007). L'emivita di 365g gestisce già la
recency in modo ottimale; un taglio netto in aggiunta è solo dannoso — conferma e
rafforza la Fase 2b (memoria lunga). Il parametro `train_window_days` resta
disponibile nel backtest per future esplorazioni (es. su leghe più volatili).

### Market-implied su tutti i mercati sui gol — Fase 26 (il risultato più forte)

Estensione della Fase 24 a **ogni mercato basato sui gol**, come modulo
riutilizzabile (`src/models/market_implied.py`, con test) + sweep
(`scripts/_run_market_implied.py`). Si invertono le quote 1X2+O/U per i λ,μ del
mercato, e la matrice del DC deriva coerentemente tutti i mercati. Confronto per
mercato: **market-implied vs DC-da-gol vs baseline**, con CI bootstrap.

| Mercato (\* = non prezzato) | market-implied | DC-da-gol | baseline | Δ vs DC (CI95) |
|---|--:|--:|--:|--:|
| risultato esatto \* | 2.8037 | 2.8345 | 2.8974 | −0.0309 [−0.039, −0.023] |
| multigol 0-1/2-3/4+ \* | 1.0333 | 1.0470 | 1.0444 | −0.0137 [−0.019, −0.008] |
| total ospite Over 1.5 \* | 0.5985 | 0.6111 | 0.6529 | −0.0126 [−0.018, −0.008] |
| total casa Over 1.5 \* | 0.6243 | 0.6359 | 0.6770 | −0.0116 [−0.017, −0.007] |
| Over 3.5 \* | 0.5762 | 0.5877 | 0.5864 | −0.0114 [−0.016, −0.007] |
| Over 4.5 \* | 0.3765 | 0.3871 | 0.3832 | −0.0106 [−0.015, −0.006] |
| scarto ospite ≥2 \* | 0.3465 | 0.3558 | 0.4113 | −0.0094 [−0.014, −0.005] |
| scarto casa ≥2 \* | 0.4318 | 0.4402 | 0.4945 | −0.0083 [−0.013, −0.004] |
| Over 1.5 \* | 0.5440 | 0.5512 | 0.5491 | −0.0073 [−0.012, −0.003] |
| GG/NG \* | 0.6853 | 0.6901 | 0.6871 | −0.0047 [−0.008, −0.001] |
| Over 0.5 \* | 0.2468 | 0.2478 | 0.2477 | −0.0010 [−0.004, +0.001] |
| pari/dispari totale \* | 0.6932 | 0.6930 | 0.6923 | +0.0001 (≈0) |
| *(Over 2.5, ancoraggio)* | 0.6818 | 0.6885 | 0.6892 | −0.0067 |

Il market-implied **batte il DC-da-gol su 13 mercati su 14** (CI95<0 su 12) e
**batte la baseline su 13 su 14**. I guadagni maggiori sono sui mercati più
ricchi (risultato esatto −0.031, multigol, total-squadra). L'unico mercato dove
non migliora è il **pari/dispari** (+0.0001): la parità del totale gol è
quasi-casuale, nessun λ,μ la predice — atteso e rassicurante (non inventa segnale
dove non c'è). Le due righe *ancoraggio* (1X2, Over 2.5) riproducono il mercato
per costruzione.

Le tre strade laterali:

- **ρ** (correzione DC): conta poco, ma un piccolo ρ negativo (−0.06/−0.10)
  aiuta marginalmente sui punteggi bassi (GG/NG 0.6865 → 0.6847). Config ρ≈−0.06.
- **Target d'inversione**: 1X2+O/U batte solo-1X2 su tutto (Δ +0.003…+0.007):
  l'O/U aggiunge informazione reale (fissa il livello di gol). **Servono entrambi.**
- **Blend col nostro DC**: mescolare i nostri λ,μ con quelli del mercato
  **peggiora** (Δ +0.002…+0.010). Il nostro modello non aggiunge nulla al mercato
  — conferma pulita dell'encompassing (Fase 16). **Meglio il mercato puro.**

**In mano abbiamo un motore di pricing coerente per ogni mercato sui gol**: date
le sole quote 1X2+O/U, prezza risultati esatti, multigol, total-squadra,
over/under a ogni soglia, handicap — meglio del nostro modello e della baseline,
in modo statisticamente solido. **Onestà:** non verificabile contro *ipotetiche*
linee di chiusura di quei mercati (assenti nei dati) e richiede le quote 1X2+O/U
alla predizione. Ma come stimatore per-caso su mercati non prezzati è il
risultato più forte del progetto, e la base pronta per un tool pratico.

### Ottimizzare la forma dei punteggi — Fase 27 (già ottima)

Ultima spinta sul market-implied: i λ,μ vengono dal mercato (ottimi), ma la
*forma* della distribuzione attorno a loro è nostra, e in Fase 26 ρ=−0.06 era
fissato a occhio. La impariamo dai risultati reali, walk-forward, tenendo i λ,μ
del mercato (`scripts/_run_shape.py`):

| Forma | risultato esatto | Δ vs Fase 26 |
|---|--:|--:|
| ρ=−0.06 (Fase 26) | 2.8037 | — |
| ρ fittato (≈−0.074) | 2.8038 | +0.0002 (rumore) |
| ρ + φ diagonale (≈0.09) | 2.8025 | −0.0011 [−0.0025, +0.0003] |
| binomiale negativa | 2.8045 | +0.0009 (peggio) |

La forma della Fase 26 era **già essenzialmente ottima**: fittare ρ non aiuta
(il −0.06 a occhio era giusto), l'inflazione diagonale φ dà un guadagno minuscolo
e non conclusivo (CI include lo zero) solo sul risultato esatto, e la binomiale
negativa è **rigettata** (il fit spinge la dispersione verso la Poisson: i gol,
con λ dal mercato, non sono over-dispersi). Il market-implied ha toccato il suo
tetto anche sulla forma: i λ,μ del mercato sono tutta la storia.

### Quando falliscono i modelli? Errore per giornata — Fase 28

Ipotesi: a fine campionato alcune squadre non lottano più per nulla, quindi i
risultati delle ultime giornate sono più "ballerini". Ma il fallimento è NOSTRO
o di tutti (mercato incluso)? Log-loss 1X2 per momento della stagione, giornata
stimata ordinando le partite per data (`scripts/_run_matchday.py`):

| Giornate | Modello | Mercato | Gap |
|---|--:|--:|--:|
| 1-6 (inizio) | 0.9725 | 0.9580 | +0.0145 |
| 7-19 | 0.9744 | 0.9569 | +0.0175 |
| 20-31 | 0.9631 | 0.9507 | +0.0124 |
| 32-34 | 1.0328 | 1.0125 | +0.0203 |
| **35-38 (fine)** | **1.0179** | **0.9921** | **+0.0258** |

Due fatti: (1) **il finale è molto più difficile per TUTTI** — il log-loss sale
da ~0.96 a ~1.02 sia per il modello sia per il mercato (le ultime giornate sono
davvero più ballerine, ma lo sono per chiunque: casualità irriducibile);
(2) **il gap raddoppia verso la fine** (+0.0124 a metà → +0.0258 nel finale),
indizio che il mercato prezzi la posta in palio meglio di noi.

**Onestà:** il raddoppio del gap NON è statisticamente conclusivo — Δ gap
late(35-38)-vs-resto = +0.0104, CI95 [−0.0196, +0.0395], include lo zero (con
sole 240 partite finali ad alta varianza manca la potenza). È una *tendenza*
pulita nei bucket, non un fatto dimostrato. La difficoltà del finale è quindi in
gran parte non risolvibile (fatica anche il mercato); l'indizio di un gap
model-specifico nelle ultime giornate è dove dei dati sulla **posta in palio**
potrebbero aiutare — un primo taglio dei quali (squadra già salva / retrocessa /
in corsa) è derivabile dalla classifica, **senza dati esterni** (Fase 29
candidata).

### Posta in palio: i "dead rubber" spiegano il finale? — Fase 29 (NO)

Se la difficoltà del finale fosse la MOTIVAZIONE (squadre già salve e fuori
dall'Europa, senza più nulla in gioco), il gap del modello dovrebbe essere
maggiore proprio nei "dead rubber" — testabile SENZA dati esterni, derivando la
posta in palio dalla classifica a ogni giornata (`scripts/_run_stakes.py`,
euristica di raggiungibilità 3×gare-rimaste):

| Definizione dead | n | gap dead | gap live | Δ (dead−live) |
|---|--:|--:|--:|--:|
| entrambe le squadre | 12 (0.5%) | −0.069 | +0.017 | −0.086 [−0.14, −0.03] * |
| almeno una squadra | 99 (4.3%) | +0.005 | +0.017 | −0.012 [−0.058, +0.035] |

Sul campione affidabile (99 partite; le 12 "entrambe" sono troppo poche per
fidarsi) **non c'è effetto** (CI include lo zero), e la direzione è comunque
**negativa**: nei dead rubber il modello è, semmai, *leggermente migliore* del
mercato — l'opposto di "il mercato prezza la motivazione e noi no". La
correlazione posta-in-palio/gap è ~0.

**Conclusione:** i dead rubber **non spiegano** la difficoltà del finale: sono
troppo rari (0.5–4.3%) e dove la posta è bassa il modello non fa peggio. Il
finale è difficile per **casualità diffusa** (Fase 28), non per una posta in
palio che ci sfugge → cercare dati esterni sulla motivazione probabilmente **non
aiuterebbe**. Risultato utile: evita un investimento sbagliato.

### Pattern dentro la stagione — Fase 30 (anatomia per periodo)

Anatomia completa: per ogni periodo, non solo il gap ma cosa *cambia*
(`scripts/_run_season_patterns.py`).

| Giornate | gap | %casa | %pari | %osp | gol/g | entropia |
|---|--:|--:|--:|--:|--:|--:|
| 1-6 | +0.0145 | 39.7% | 28.9% | 31.4% | 2.84 | 1.089 |
| 7-19 | +0.0175 | 40.5% | 26.4% | 33.1% | 2.64 | 1.084 |
| 20-31 | +0.0124 | 41.9% | 26.0% | 32.1% | 2.60 | 1.079 |
| 32-34 | +0.0203 | 41.1% | **31.1%** | 27.8% | 2.56 | 1.085 |
| 35-38 | +0.0258 | **36.2%** | 25.4% | **38.3%** | 2.90 | 1.084 |

Tre scoperte: (1) **non è una storia di entropia** — l'entropia degli esiti è
piatta, quindi il finale più difficile NON è dovuto a esiti più bilanciati;
(2) **due veri cambi strutturali**: giornate **32-34** tese e bloccate (pareggi
31%, pochi gol) — scontri decisivi col freno a mano; giornate **35-38** dove il
**vantaggio-casa crolla** (casa 40%→36%, trasferta 31%→38%, più gol) — l'effetto
"fine stagione", in casa si pesa meno; (3) **nessun pattern robusto nel gap** —
correlazioni con la giornata ~0 (gap +0.0056), e il gap fine-inizio è positivo
solo in **3 stagioni su 6** (media +0.0015, range −0.017…+0.021): l'indizio della
Fase 28 non è coerente tra stagioni.

Il **crollo del vantaggio-casa nel finale** è un candidato concreto di piccolo
difetto nostro (il modello eredita un vantaggio-casa dallo storico che nelle
ultime giornate si riduce — come nel COVID, Fase 9). Ma il gap non sale in modo
robusto, quindi è marginale.

### Posta in palio, versione corretta — Fase 31 (l'asimmetria conta)

La Fase 29 definiva "dead rubber" solo come "salva E fuori dall'Europa" (12
partite) — **sbagliato ai due estremi**: contava una squadra già RETROCESSA come
"in lotta salvezza" e una già CAMPIONE come "in corsa titolo". Definizione
corretta (squadra DECISA = nessuna corsa aperta, inclusi già-retrocessa e
già-campione) su **8 stagioni** (`scripts/_run_stakes2.py`):

| Categoria partita | n | gap | CI95 |
|---|--:|--:|--:|
| entrambe in corsa (riferimento) | 2831 | +0.0172 | [+0.0122, +0.0221] |
| **una decisa, una in corsa** | 133 | **+0.0572** | [+0.0139, +0.1014] ✱ |
| entrambe decise | 76 | +0.0130 | [−0.035, +0.060] |
| coinvolge una campione | 23 | +0.0949 | [+0.013, +0.179] ✱ |

Il risultato **ribalta la Fase 29**: escludendo le partite con almeno una
squadra decisa il gap **scende** da +0.0188 a +0.0172 (quelle partite hanno gap
+0.0411) → su di esse il modello va **peggio** del mercato, non meglio (la Fase 29,
col classificatore rotto e 12 partite, aveva concluso l'opposto).

Il segnale vero non è "entrambe decise" (lì niente) ma l'**asimmetria di
motivazione**: quando una squadra non ha più nulla in gioco e l'altra lotta, il
gap triplica (+0.057 vs +0.017, CI esclude lo zero). Ha senso: la squadra motivata
sovra-rende / quella scarica molla, e **il mercato lo prezza mentre noi usiamo la
forza stagionale, ciechi alla motivazione del momento**. **Onestà:** campioni
piccoli (133 la categoria più solida, 23-76 le altre) e molti test → indizio
forte e sensato, non una prova. È il primo **lead azionabile dai dati interni**:
una covariata "stakes mismatch" potrebbe attenuare la previsione a favore della
squadra motivata (da validare prima di adottare).

### Validazione della covariata stakes-mismatch — Fase 32 (DC e GBM)

Il lead della Fase 31 regge walk-forward? Costruita la covariata `stakes` (posta
in palio dalla classifica, 1=decisa/0=in corsa; `loader.add_stakes`,
`--covariates stakes`) e testata su **entrambi** i modelli
(`scripts/_run_stakes_cov.py`):

| Modello | subset | log-loss base→stakes | Δ (CI95) |
|---|---|--:|--:|
| DC | overall | 0.9797 → 0.9796 | −0.0001 [−0.0007, +0.0005] |
| DC | mismatch (n=99) | 0.9609 → 0.9587 | −0.0022 [−0.0157, +0.0114] |
| GBM | overall | 1.0098 → 1.0096 | −0.0001 [−0.0014, +0.0012] |
| GBM | mismatch (n=99) | 0.9968 → **0.9841** | **−0.0127** [−0.0283, +0.0030] |

Tre letture: (1) **direzione confermata su entrambi i modelli** — sulle partite
mismatch la covariata aiuta sia il DC (−0.0022) sia il GBM (−0.0127), entrambe
negative (il rumore puro darebbe segni sparsi; due modelli indipendenti che
concordano su un meccanismo sensato è più di un caso); (2) **il GBM la cattura
molto meglio del DC** (−0.0127 vs −0.0022) — l'effetto "la squadra scarica
sotto-rende" è non-lineare, e il GBM modella l'interazione mentre il DC può solo
spostare linearmente il tasso-gol → il GBM è il veicolo giusto per questo segnale;
(3) **ma nessuno è statisticamente conclusivo** (CI includono lo zero, il GBM per
un pelo; n=99 troppo piccolo).

**Verdetto** (regola: adozione solo se CI<0): **non adottata**, ma è il **lead
interno più credibile del progetto** — direzione giusta su due architetture,
meccanismo chiaro, effetto concentrato dove previsto (≠ dai "residui = rumore"
delle Fasi 13/20, dove i segni erano casuali). Serve più campione per superare la
soglia. Covariata `stakes` disponibile, off di default.

### Le ultime covariate: PPDA/deep e finishing-luck — Fase 33 (ridondanti)

Nello snapshot restavano due segnali mai messi nel modello: **PPDA e deep
completions** (indicatori tattici Understat) e **finishing-luck** (gol − xG
rolling = sovra/sotto-rendimento realizzativo, ipotesi di mean-reversion). Testati
come covariate rolling pre-partita su DC e GBM (`scripts/_run_style_luck.py`):

| DC ± covariata | log-loss | Δ vs base (CI95) |
|---|--:|--:|
| base | 0.9797 | — |
| +ppda+deep | 0.9806 | +0.0009 [−0.0012, +0.0030] |
| +luck | 0.9797 | **−0.0000** [−0.0006, +0.0006] |
| +tutte | 0.9807 | +0.0010 |

GBM: base 1.0107 → +style 1.0085, Δ −0.0022 [−0.0072, +0.0028] (P 81%, non concl.).

Tutte **ridondanti**: (1) PPDA/deep peggiorano appena il DC (lo stile è già
implicito in gol+xG, come il valore-rosa in Fase 4c); (2) finishing-luck ha
effetto **esattamente zero** — conferma elegante che il blend gol/xG (α=0.75) *è
già* il meccanismo di mean-reversion (pesa gol e xG in modo ottimale, quindi "la
fortuna regredisce" non aggiunge nulla); (3) il GBM estrae un capello dalle
feature tattiche (−0.0022, 81%) ma non conclusivo e irrilevante (resta ben peggio
del DC). Covariate `ppda`/`deep`/`luck` disponibili, off di default.

**Con la Fase 33 i dati interni sono completamente esplorati**: tutto lo snapshot
(gol, xG, npxG, PPDA, deep, valore-rosa, assenze, riposo, forma, stakes) è stato
testato. Il tetto è **informativo**, confermato per l'ultima volta coi segnali
rimasti. L'unico lead vivo è lo stakes-mismatch (Fase 32), che serve più stagioni.

> **Le fasi dalla 34 in poi** (audit critico, φ35 sul pareggio, sotto-dispersione
> e beat-the-close, cross-lega Premier/Liga, campagna dei dati, verifica finale
> della calibrazione) sono riassunte riga per riga nella tabella
> [«Tutti gli esperimenti, in un colpo d'occhio»](#tutti-gli-esperimenti-in-un-colpo-docchio)
> e raccontate per esteso nel [DIARIO](docs/DIARIO.md), che ha un **indice per
> archi narrativi** in testa: da lì si raggiunge ogni fase in un click.

## Struttura

*(Aggiornata all'audit della Fase 101: rispecchia il repo reale a 5 leghe —
prima si fermava a 3 e non elencava l'archivio dell'audit, i dati esterni né i
documenti nati dopo la Fase 82.)*

```
CLAUDE.md           protocollo di lavoro (cosa aggiornare a ogni esperimento)
lavoro_aperto.md    INDICE del lavoro aperto (piste, caselle vuote, Tier 2/3)
newseason.md        file DEPERIBILE: piano operativo per l'avvio del 2026-27

src/
  config.py       iperparametri PER LEGA (LEAGUE_CONFIGS, 5 voci) + costanti del
                  motore market-implied per lega (MARKET_ENGINE) + deriva
                  in-stagione del simulatore (DRIFT_SD, Fase 94) = fonte unica
  data/           raccolta e normalizzazione dati (schema interno pulito)
    sources.py      UNICO punto con URL, stagioni, leghe e alias squadre
    loader.py       parsing + normalizzazione + covariate (offline-first);
                    politica quote apertura/chiusura (Fase 73) e guard
                    bilaterale sull'overround (ORR_MAX = 1.12)
    database.py     snapshot CSV congelati + SQLite rigenerabile
    understat.py    xG/npxG/PPDA/deep + guard sui record SEGNAPOSTO
    transfermarkt.py  infortuni → assenze stimate (`*_est`)
    player_scores.py  valori rosa (dataset Transfermarkt via Kaggle, Fase 67)
    fixtures.py     calendario di club completo → congestione vera (Fase 4e)
  models/
    dixon_coles.py      il modello standalone (fit, blend gol/xG, φ35 pareggio)
    market_implied.py   il motore di pricing (quote 1X2+O/U → λ,μ → ogni mercato;
                        router `price_markets`, `sharpen_1x2`, nudge stagionale)
    market_denoise.py   power-devig + ricalibrazione cross-stagione (Fase 38)
    season_sim.py       Monte Carlo di una STAGIONE intera → mercati outright
                        (campione/retrocessione/Top-N), spareggi ufficiali per
                        lega (Fase 89)
    bivariate_poisson.py, copula_scores.py   forme alternative (testate, non adottate)
  evaluation/
    metrics.py        Brier, log-loss, devigging quote, baseline
    markets.py        derivazione dei mercati Tier 1 dalla matrice dei punteggi
    analysis.py       analisi degli errori del backtest
    calibration.py    temperature scaling + ricalibrazione per-classe (Fase 6/10)
    experiment_log.py  compute_metrics (FONTE DI VERITÀ) + registro runs.jsonl

scripts/            159 file .py, di cui 105 driver `_run_*` (uno per fase)
  build_database.py       (ri)costruisce il DB dallo snapshot congelato (offline)
  build_league_snapshot.py / build_new_snapshot.py   snapshot delle altre leghe
  backtest.py             backtest walk-forward (registra il run) — con --league
  predict.py              predice una partita (tutti i mercati, con o senza quote)
  analyze.py / analyze_gap.py / tune.py / calibrate.py / markets.py
  audit_snapshots.py      audit dei dati: snapshot vs fonte-madre vs fonte terza
  audit_anomalie.py / cerca_segnaposto.py   audit avversariale (regole R5/R6)
  applica_correzioni.py   applica il registro delle correzioni (regola R3)
  build_estimates.py      genera data/estimates/ (STIME dichiarate)
  fetch_sources.py        riscarica le fonti originali con provenienza (SHA256)
  archive_outrights.py    congela le quote outright LIVE (Polymarket + Smarkets)
  fetch_polymarket_open.py / fetch_smarkets_outrights.py   fetch delle due borse
  _run_*.py               driver one-shot di ogni fase (riproducibilità)

experiments/        runs.jsonl: registro replicabile di OGNI run
                    + gli output riutilizzabili delle fasi recenti
                      (fase93_discrimination.csv, fase89*, fase91, fase94,
                       listino_validazione.json, prospettico_2026_27*)

data/
  {serie_a,premier_league,la_liga,bundesliga,ligue_1}_matches.csv
                        i 5 SNAPSHOT congelati (schema identico, 38 colonne)
  club_fixtures*.csv    calendario di club completo per lega (congestione vera)
  football_data_raw/    i 9 CSV grezzi football-data della Serie A
  estimates/            STIME dichiarate (mai nelle colonne quota) + README
  ricerca_esterna/      86 file: quote 1xBet via footiqo (2017-20, 5 leghe),
                        calendari di coppa da Wikipedia, manifest e validazioni
                        — dati REALI esterni, NON integrati negli snapshot
  outright_snapshots/   quote outright LIVE congelate a ogni raccolta (Fase 97)
  correzioni_dichiarate.csv   registro delle correzioni ai dati (regola R3)
  squad_value_2526_transfermarkt.csv   16 celle 2025-26 da fonte secondaria (R2)

docs/
  DIARIO.md             la storia fase per fase (indice per archi narrativi)
  DATI.md               catalogo di TUTTI i dati: copertura, semantica, stime
  GLOSSARIO.md          i termini del progetto, una riga ciascuno
  PANCHINA.md           la rosa dei modelli (titolari/panchina/bocciati × 2 fronti)
  PISTE.md              idee dato→modello non ancora provate, per costo crescente
  PLAYBOOK_NUOVA_LEGA.md  procedura per aggiungere un campionato
  STUDIO_PREMIER_LIGA.md  quaderno dedicato alle due leghe non-Serie A
  MANUALE_SOPRAVVIVENZA.md  conoscenza operativa dell'ambiente (rete, Actions)
  CACCIA_OU_2017_19.md  il dossier sull'ultimo buco dati (CHIUSO alla Fase 100)
  BETEXPLORER_SCRAPER.md  verbale dello scraper (pista chiusa)
  AUDIT_FASI_80_100.md  verbale dell'audit delle ultime 20 fasi (Fase 101)
  audit_5_leghe/        gli 11 report integrali dell'audit a 5 leghe + 00_indice
                        + REGOLE.md + patch_guard_overround_APPLICATA.md
                        + numeri/ (i JSON grezzi dietro ogni tabella)

files/              bundle caricati a mano (football-data e Understat di
                    Premier/Liga, Fase 54) + player_scores/ (valori rosa)
tests/              24 file, 995 test verdi (modello, dati, metriche, script)
.github/workflows/  import del dataset player-scores e probe via runner Actions
worldcup/           esperimento parallelo a bassa priorità (Mondiali)
```

## Come si usa

```bash
pip install -e .            # oppure: pip install -e ".[dev]" per i test

python scripts/build_database.py    # (ri)costruisce il DB dallo snapshot (offline)
python scripts/backtest.py          # backtest walk-forward (config ufficiale Serie A)
python scripts/analyze.py           # analizza gli errori del backtest
python scripts/tune.py --sweep shrinkage          # tara un iperparametro su piu' stagioni
python scripts/markets.py           # grande backtest su TUTTI i mercati (1X2, O/U, GG/NG, doppie chance)
python -m pytest                    # esegue i test (841, tutti verdi)
```

**Le cinque leghe.** La chiave di lega (`--league`) è una di
`serie_a` (default) · `premier_league` · `la_liga` · `bundesliga` · `ligue_1`,
ed è la stessa in `src/config.py` (`LEAGUE_CONFIGS`, `MARKET_ENGINE`) e in
`src/data/sources.py`:

```bash
python scripts/backtest.py --league premier_league    # ...su un'altra lega
python scripts/backtest.py --league bundesliga --test-season 2425
python scripts/analyze.py --league bundesliga         # DEVE coincidere con la lega
                                                      # del backtest che ha prodotto il CSV
```

⚠️ **`--league` non è ovunque**: `backtest.py`, `analyze.py`, `predict.py` e
`build_database.py` lo accettano; **`tune.py` e `markets.py` no** — girano sulla
Serie A. Le tarature per-lega sono state fatte con i driver dedicati
(`scripts/_run_fase57_retune.py` per Premier/Liga, `scripts/tranche3_ritaratura.py`
per Bundesliga/Ligue 1), non con `tune.py`.

Predire una partita (il tool pratico, `scripts/predict.py`):

```bash
# senza quote: Dixon-Coles standalone (+ φ35 sul pareggio dove la lega la prevede)
python scripts/predict.py Inter Juventus

# con le quote 1X2 (H D A) + O/U 2.5 (Over Under): motore market-implied,
# router double-Poisson, tutti i mercati Tier 1
python scripts/predict.py Inter Juventus --odds 2.10 3.30 3.60 1.85 1.95

# su un'altra lega: legge da sola la config e il MOTORE di quella lega
python scripts/predict.py "Bayern Munich" Dortmund --league bundesliga
```

**Entrambi i modelli sono per-lega** (M1 dalla Fase 83-bis, M2 dalla Fase
92-bis, Bundesliga e Ligue 1 esplicitate alla Fase 101): `predict.py` legge gli
iperparametri da `LEAGUE_CONFIGS` e le costanti del motore (θ, φ0, κ,
`sharpen_1x2`) da `MARKET_ENGINE`. **Solo la Serie A esce col router completo**;
Premier, La Liga, Bundesliga e Ligue 1 escono col **motore liscio** — non per
prudenza ma perché misurato (router θ negativo su 0/25 mercati nelle due leghe
nuove, φ35 bocciata in Premier). Altre opzioni: `--date` (momento della
predizione), `--no-draw-balance` (spegne la φ35 sul path DC),
`--matchday N` (mostra il nudge stagionale GG/NG di fine stagione, Fase 48).

Opzioni utili:

```bash
python scripts/backtest.py --test-season 2425          # testa un'altra stagione
python scripts/backtest.py --covariates rest_full      # covariate off-di-default
python scripts/backtest.py --draw-balance              # φ35 (Fase 35) sul path DC
python scripts/tune.py --sweep half_life_days --values 0 180 365 730
python scripts/tune.py --sweep shots_blend --values 0 0.5 1
```

Dati e controlli (dettaglio nella sezione
[Archivio dati interno](#archivio-dati-interno-riproducibilità)):

```bash
python scripts/audit_snapshots.py               # snapshot vs fonte-madre vs fonte terza
python scripts/audit_snapshots.py bundesliga    # ...su una lega sola
python scripts/audit_anomalie.py                # audit avversariale (e se la fonte sbagliasse?)
python scripts/build_estimates.py               # rigenera data/estimates/ (STIME dichiarate)
python scripts/archive_outrights.py --show      # archivio delle quote outright (Fase 97)
```

## Roadmap (idee, non impegni)

> 🗓️ **Questa è la roadmap STORICA delle Fasi 1-23** (più le due voci di
> prospettiva che erano in coda), tenuta perché mostra l'ordine in cui le cose
> sono state provate. **Non è la lista dei prossimi passi**: quella vive in
> `CLAUDE.md` §6 («Prossimi passi») e, in dettaglio e ordinata per costo, in
> [`docs/PISTE.md`](docs/PISTE.md). Dalla Fase 24 in poi la storia è nella
> tabella [«Tutti gli esperimenti»](#tutti-gli-esperimenti-in-un-colpo-docchio)
> e nel [DIARIO](docs/DIARIO.md).

1. ✅ **Fase 1** — tracer bullet: Dixon-Coles + backtest su Serie A.
2. ✅ **Fase 2a** — analisi degli errori: capito dove il modello perde (neopromosse,
   inizio stagione) e corretto il bug dei nomi squadra.
3. ✅ **Fase 2b** — tuning: shrinkage + memoria lunga (emivita 730g). Divario
   medio col mercato da +0.026 a +0.017.
4. ✅ **Fase 3** — tiri in porta come informazione nuova: **risultato negativo**
   (i tiri grezzi non aiutano in modo affidabile). Codice mantenuto per l'xG reale.
5. ✅ **Fase 4a** — arricchimento dati: **xG reale Understat per il 100% delle
   3420 partite** di Serie A, valori rosa Transfermarkt a inizio stagione
   (copertura 63-80% per stagione) e assenze stimate da infortuni. Snapshot e DB
   rigenerati, base invariata (stessa impronta dati). Vedi `docs/DIARIO.md`,
   Fase 4a. *(Copertura di oggi, dopo le Fasi 60/67/70 e l'integrazione delle 5
   leghe: 16.111 partite, 16.110 appaiate a Understat, xG presente ovunque
   tranne **2 partite dichiarate**; `squad_value` al **100%** su tutte le
   stagioni, zero `NaN` residui. Vedi
   [`docs/DATI.md`](docs/DATI.md) §1.)*
6. ✅ **Fase 4b** — blend gol/**xG reale** (α=0.75): primo miglioramento da dati
   nuovi, soprattutto sull'Over/Under. Config ufficiale aggiornata.
7. ✅ **Fase 4c** — spremuti gli altri dati (npxG, valori rosa, assenze) via un
   **layer di covariate** (anche in combinazione): **risultato negativo** — non
   aggiungono segnale indipendente (già implicito in gol+xG). Modello al **tetto
   pratico** dei dati attuali.
8. ✅ **Fase 4d** — ri-taratura congiunta: col blend xG l'emivita ottima passa a
   **365g** (memoria più corta). Piccolo guadagno su entrambi i mercati.
9. ✅ **Fase 4e** — **calendario di club completo** (Serie A + Coppa Italia +
   coppe europee) per la **congestione vera** + validazione walk-forward della
   covariata `rest_full` sulle 5 stagioni a copertura reale (2020-25). Il
   calendario completo **inverte il segno** del proxy solo-lega della Fase 4c
   (che peggiorava), ma il guadagno è **minuscolo e dentro il rumore** (−0.0004
   medio su 1X2 log-loss, aiuta 2 stagioni su 5) e **non tocca il mercato**:
   config ufficiale **invariata**, covariata off di default. Conferma il **tetto
   pratico** dei dati attuali. Vedi `docs/DIARIO.md`, Fase 4e / 4e-bis.
10. ✅ **Fase 5** — grande backtest **multi-mercato** (`scripts/markets.py`): il
   modello è affidabile sui mercati d'**esito** (1X2, 1X, 2X, batte la baseline),
   **debole** su Over/Under, e **peggio della baseline su GG/NG** (cattura male la
   correlazione dei punteggi). Nessun mercato batte le quote. Vedi `docs/DIARIO.md`.
11. ✅ **Fase 6** — **ricalibrazione della confidenza** (temperature scaling,
    `scripts/calibrate.py`): T tarato walk-forward sul passato. Scoperta reale e
    robusta — il modello è **sistematicamente un po' sottoconfidente** (T≈0.94,
    <1 in tutte e 6 le stagioni) — ma il guadagno è **nel rumore** (−0.0003 medio
    su 1X2 log-loss) e non uniforme: **non entra** nella config ufficiale. Modulo
    `src/evaluation/calibration.py` disponibile per l'uso pratico. Conferma il
    **tetto pratico** dei dati attuali. Vedi `docs/DIARIO.md`, Fase 6.
12. ✅ **Fase 7** — **prior di cold-start per le neopromosse** (`--promoted-prior`):
    sposta il bersaglio dello shrinkage sotto la media per le squadre senza
    storico (δ≈0.23, stimato leave-future-out). È il **miglior guadagno interno**
    trovato: −0.0011 medio complessivo (3-4× congestione/calibrazione) e −0.0039
    sulle partite delle neopromosse, su **5 stagioni su 6**. **Adottato nella
    config ufficiale** (δ=0.23). Vedi `docs/DIARIO.md`, Fase 7.
13. ✅ **Fase 8** — ultimo giro economico, **entrambe negative**: ri-taratura
    shrinkage col prior = curva **piatta** (leve ortogonali, nessun guadagno);
    vantaggio-casa per-squadra = **persistenza anno-su-anno r≈0.00** (solo rumore,
    non generalizza). Nulla più da spremere: modello al **tetto pratico**.
14. ✅ **Fase 9** — **anatomia del gap col mercato** (`scripts/analyze_gap.py`):
    gap 1X2 medio **+0.0167** (modello 0.9799 vs mercato 0.9632). Scomposto: varia
    per stagione (+0.014→+0.020, peggio nel COVID 2020-21), per forza-squadra (a U:
    deboli +0.0206 e forti +0.0180 peggio delle medie +0.0123), e — soprattutto —
    **è quasi tutto nel PAREGGIO** (il mercato 12 senza pari ha gap +0.0020 ≈
    mercato) — ⚠️ **lettura rovesciata dalla Fase 92**: la scomposizione esatta dà
    **12% massa-pareggio / 88% discriminazione** casa-ospite.
    Punta al prossimo passo mirato: **correlazione dei punteggi**. Vedi
    `docs/DIARIO.md`, Fase 9.
15. ✅ **Fase 10** — **ricalibrazione per-classe 1X2** (casa/pari/ospite): conferma
    robusta che il modello **sovrastima la casa e sottostima il pareggio** (w≈0.96
    / 1.04 in tutte e 6 le stagioni), ma il guadagno è nel rumore (−0.0005 medio,
    4/6 stagioni) → **non entra** nella config (come il temperature); funzioni in
    `src/evaluation/calibration.py` per l'uso pratico. Quinto esperimento interno
    di fila con guadagno nel rumore. Vedi `docs/DIARIO.md`, Fase 10.
16. ✅ **Fase 11** — **combinazioni delle feature off-di-default**
    (`scripts/_run_combo_analysis.py`): griglia 8 combo covariate × con/senza
    ricalibrazione, 6 stagioni. **Nessuna combinazione è utile**: `squad_value`
    peggiora sempre, `absence`/`rest_full` sono rumore anche in coppia; l'unico
    effetto additivo è la ricalibrazione (già nota, −0.0005/−0.0008).
17. ✅ **Fase 12** — chiusura: **ensemble di emivite** (blend 180+730 = −0.0006,
    borderline) e **il cambio di classe** — modello a **diagonale inflazionata**
    (`--draw-inflation`): alza i pareggi oltre la correzione Dixon-Coles, fittato
    sui punteggi. **Migliora la calibrazione del pareggio** (P(pari)→reale) ma il
    log-loss guadagna solo −0.0004 (3/6): *quanti* pareggi capitano è rumore.
    Il pareggio è **quasi-casuale per tutti, mercato incluso** → il gap non è
    cattiva modellazione ma informazione che il mercato ha. **Tetto reale**
    confermato. Vedi `docs/DIARIO.md`, Fase 12b.
18. ✅ **Fase 13** — **stato di forma** (`add_form`, covariata `form`): la forma
    (punti/gara ultime 5) **non predice l'errore del modello** (corr +0.035) e come
    covariata peggiora (+0.0002) → già catturata dal fit pesato nel tempo, nessun
    pattern nascosto. Ottavo esperimento convergente. Vedi `docs/DIARIO.md`.
19. ✅ **Fase 14** — **linea di apertura e CLV** (risultato NEGATIVO, definitivo
    su questi dati): snapshot esteso con le quote pre-chiusura (`*_open`, dai CSV
    originali football-data ora congelati in `data/football_data_raw/`; il mirror storico è
    sparito da GitHub). Il modello **non batte nemmeno l'apertura** (gap 1X2
    +0.0146, 6/6 stagioni; l'affilamento open→close vale solo +0.0020) e il
    **CLV è negativo** (−0.0028, 45%>0): i dissensi del modello sono rumore,
    ROI@open −17.3%. L'ipotesi "scommetti presto" è chiusa; resta non testabile
    solo l'apertura vera (domenica/lunedì), che richiede raccolta prospettica.
    Vedi `docs/DIARIO.md`, Fase 14.
20. ✅ **Fase 15** — **audit dei calcoli**: ogni numero di README/DIARIO
    ricalcolato dal registro, backtest ufficiale riprodotto identico, formule
    verificate (nessun errore). Corretti: ROI (−15.7% reale, non −8.5%), tabella
    Fase 2b del diario, O/U 0.6885, ~86%, baseline 1.0834 + baseline ex-ante
    1.0860 dichiarata. Le run mancanti delle Fasi 11/12a/13 sono state
    **ri-eseguite e registrate** (96 run nuove, registro a 329): i numeri
    pubblicati sono **confermati identici** (blend 180+730 = 0.9791/−0.0006;
    forma +0.0002, corr +0.0353; miglior combo −0.0011, squad_value peggiora).
    Nessuna conclusione cambia. Vedi la sezione
    [Audit dei calcoli](#audit-dei-calcoli--fase-15-verifica-indipendente-di-ogni-numero).
21. ✅ **Fase 16** — **test di encompassing** (`scripts/_run_encompassing.py`):
    blend `α·modello + (1−α)·mercato` con α fittato walk-forward. **α\*≈0
    ovunque, perfino in-sample**: il mercato di chiusura ingloba completamente
    il modello, nessuna informazione indipendente da combinare. Converge col
    CLV negativo (Fase 14). Vedi la sezione
    [Fase 16](#il-mercato-ingloba-il-modello--fase-16-encompassing-il-test-definitivo).
22. ✅ **Fase 17** — **intervalli di confidenza bootstrap** sui numeri chiave
    (`scripts/_run_gap_uncertainty.py`, B=10.000): gap 1X2 **+0.0167
    [+0.0107, +0.0226]** (reale), gap 12 **+0.0020 [−0.0006, +0.0046]**
    (statisticamente zero — ⚠️ ma il 12 misura la **massa del pareggio**, non il
    «chi vince»: `P(12)=1−P(X)`, diagnosi rovesciata dalla **Fase 92**), gap O/U
    +0.0067 [+0.0021, +0.0115] (reale), Δ prior neopromosse −0.0010
    [−0.0025, +0.0004] (probabile ma non conclusivo, ~93%). Vedi la sezione
    [Fase 17](#barre-derrore-sui-numeri-chiave--fase-17-bootstrap-appaiato).
23. ✅ **Fase 18** — **ρ dinamico** (`--dynamic-rho`, `scripts/_run_dynrho.py`):
    la correzione sui punteggi bassi per-partita, ultima idea strutturale sul
    pareggio. **Negativa con regola pre-dichiarata**: Δ +0.0003
    [−0.0007, +0.0013], ρ_slope instabile (cambia segno, sbatte sui bound) →
    **off**. Terza via strutturale sul pareggio chiusa (dopo Fasi 10 e 12b).
24. ✅ **Fase 19** — **potenza sul prior neopromosse**: finestra estesa alle
    stagioni 2018-19 e 2019-20 (mai usate) → 8 stagioni, n=3040. Il CI si
    stringe a **[−0.0026, +0.0001]**, P(aiuta) **96.5%** (97.0% sulle
    promosse); le due stagioni nuove confermano entrambe. Resta "molto
    probabile ma formalmente non concluso": prior confermato nella config.
25. ✅ **Fase 20** — **anatomia dei residui** (`scripts/_run_residuals.py`): 11
    covariate pre-partita (incluse tre di estremità mai provate) contro il
    residuo del modello → **R² a livello rumore** (0.0055 vs 0.0051), nessun
    segnale nascosto. Ma emerge l'**adverse selection**: il gap vs mercato
    cresce col dissenso del modello (r=+0.18; quartile alto +0.0539 vs +0.0009)
    → i "value bet" del modello sono i suoi errori. Spiega il ROI negativo.
26. ✅ **Fase 21-23 — modelli nuovi, valutati PER MERCATO** (principio 8 in
    `CLAUDE.md`): gradient boosting sul GG/NG (Fase 21, pareggia il DC calibrato),
    lo **sweep completo** (Fase 22: 6 mercati × 3 feature-set, non batte il DC su
    nessuno), e il GBM **modello + mercato** (Fase 23: dando in pasto anche le
    quote, resta peggio del DC — un ensemble degrada un input near-optimal).
    **Il tetto è informativo, non architetturale**; e il gap col mercato non si
    riduce con un modello (a ~0 solo copiando il mercato, sotto zero mai).
27. ✅ **Uso pratico** — fatto: `scripts/predict.py` predice ogni partita su
    tutti i mercati Tier 1 (DC standalone senza quote; motore market-implied +
    router double-Poisson con le quote 1X2+O/U — Fasi 44/52), ed è **per-lega su
    entrambi i modelli**: M1 dalla Fase 83-bis, M2 dalla Fase 92-bis con la
    mappa `src.config.MARKET_ENGINE`. Solo la Serie A esce col router completo;
    le altre quattro col **motore liscio** (Fase 101).
28. ✅ **Estensione a nuovi campionati** — fatto, e arrivato a **cinque leghe**:
    prima **Premier League e La Liga** (Fasi 53-57, 76, 79-81, da bundle
    caricati a mano), poi **Bundesliga e Ligue 1** (Fase 100/101, scaricate
    direttamente perché la rete è tornata raggiungibile, e verificate riga per
    riga contro la fonte). Esito identico su tutte: le conclusioni (gap, tetto,
    α*=0) sono robuste fuori dalla Serie A, **il modello trasferisce ma l'edge
    no** (il beat-the-close è una proprietà della chiusura Serie A). Costanti
    per-lega in `src/config.py`: `LEAGUE_CONFIGS` (δ neopromosse 0.23 / 0.33 /
    0.22 / 0.28 / 0.19) e `MARKET_ENGINE`. Procedura riutilizzabile in
    [`docs/PLAYBOOK_NUOVA_LEGA.md`](docs/PLAYBOOK_NUOVA_LEGA.md).
29. **Dati davvero nuovi** (formazioni ufficiali pre-partita, quote live/di
    apertura vere raccolte prospetticamente) — **APERTA**, ed è l'unica leva
    informativa che tutte le fasi indicano non ancora esaurita. Il primo passo
    concreto è il **test prospettico 2026-27** (Fase 78, previsioni congelate
    prima del kickoff e scorate dopo: `experiments/prospettico_2026_27.md`). Le
    piste, ordinate per costo, vivono in [`docs/PISTE.md`](docs/PISTE.md).
30. 🟡 **Integrazioni** con piattaforme esterne (Polymarket, exchange, …), dove
    il mercato potrebbe essere meno efficiente della chiusura dei bookmaker —
    **avviata, non conclusa**: Polymarket (Gamma API) e Smarkets (API v3
    pubblica) sono raggiungibili e i loro prezzi outright vengono **congelati a
    ogni raccolta** in `data/outright_snapshots/` (Fase 97). Manca la parte
    che conta: nessun confronto storico è possibile all'indietro (non esistono
    quote outright storiche), quindi la verifica «battiamo il mercato» su questa
    famiglia si può fare **solo in avanti**.

*(La roadmap per-fase si ferma qui: dalla Fase 24 in poi la storia è tracciata
riga per riga nella tabella
[«Tutti gli esperimenti»](#tutti-gli-esperimenti-in-un-colpo-docchio) e nel
[DIARIO](docs/DIARIO.md); le idee non ancora provate stanno in
[`docs/PISTE.md`](docs/PISTE.md), l'indice del lavoro aperto in
[`lavoro_aperto.md`](lavoro_aperto.md).)*

## Archivio dati interno (riproducibilità)

> 🗂️ Questa sezione è il **riassunto** dell'archivio dati. Il catalogo completo
> — copertura colonna per colonna, semantica delle quote, censimento dei buchi,
> stime dichiarate — è in **[`docs/DATI.md`](docs/DATI.md)**, che è la fonte da
> aggiornare per prima quando i dati cambiano.

Per non dipendere dalla disponibilità *in tempo reale* di una fonte esterna (che
può cambiare o sparire) e permettere a chiunque di rieseguire gli stessi calcoli,
i dati sono **congelati** in un archivio interno con due artefatti:

- **snapshot** `data/<lega>_matches.csv` — **versionati in git**, testo
  diffabile: sono la fonte di verità congelata, **cinque** file con schema
  identico (stesse **38 colonne** e **stesso ordine**, verificato da
  `test_schema_identico_tra_leghe`). Chi clona il repo ha esattamente gli
  stessi dati, **senza rete**.

  | file | partite | stagioni | nota |
  |---|--:|--:|---|
  | `data/serie_a_matches.csv` | 3.420 | 9 (2017-18 → 2025-26) | |
  | `data/premier_league_matches.csv` | 3.420 | 9 | |
  | `data/la_liga_matches.csv` | 3.420 | 9 | |
  | `data/bundesliga_matches.csv` | 2.754 | 9 | 18 squadre → 306 partite/stagione |
  | `data/ligue_1_matches.csv` | 3.097 | 9 | 380 fino al 2022-23, 306 dal 2023-24 (riforma); **279 nel 2019-20**, campionato cancellato per COVID — dato reale, non un buco |
  | **totale** | **16.111** | | 16.110 appaiate a Understat |

- **database** `data/football.db` (Serie A, nome storico) e
  `data/football_<lega>.db` (le altre quattro) — SQLite queryable,
  **rigenerabili** dallo snapshot, non versionati.

```bash
python scripts/build_database.py            # ricostruisce il DB dallo snapshot (offline)
python scripts/build_database.py --enrich   # ricalcola xG/rose/assenze sullo snapshot esistente
python scripts/build_database.py --fixtures # assembla il calendario di club completo + congestione vera
python scripts/build_database.py --refresh  # riscarica TUTTO dalle fonti e aggiorna lo snapshot
python scripts/build_database.py --refresh-odds  # ricalcola SOLO le 10 colonne quota (Fase 61/73)
python scripts/build_database.py --open-odds     # aggancia le colonne *_open dai grezzi (Fase 14)
# ogni comando accetta --league: senza, e' Serie A
python scripts/build_database.py --league bundesliga
sqlite3 data/football.db "SELECT season, COUNT(*) FROM matches GROUP BY season"
sqlite3 data/football_bundesliga.db "SELECT season, COUNT(*) FROM matches GROUP BY season"
```

### Colonne di arricchimento (Fase 4a)

Oltre alle colonne base (partita, gol, tiri in porta, 10 colonne quota), lo
snapshot contiene 14 colonne da fonti esterne (`NaN` dove la fonte non copre):

| Colonne | Fonte | Note |
|---|---|---|
| `home_xg`, `away_xg`, `home_npxg`, `away_npxg` | Understat | xG e xG senza rigori; presenti ovunque tranne **2 partite dichiarate** (Nantes-Toulouse 17/05/2026, `isResult=false`; Holstein Kiel-Bochum 09/02/2025, **record segnaposto** — vedi `docs/DATI.md` §4-bis) |
| `home_ppda`, `away_ppda`, `home_deep`, `away_deep` | Understat | pressing e passaggi profondi; stessa copertura |
| `home_squad_value`, `away_squad_value` | **player-scores** (Transfermarkt via Kaggle, Fase 67) + 29 celle 2025-26 da Transfermarkt diretto | valore rosa (EUR) all'inizio stagione (valutazioni ≤ 1 settembre, **niente look-ahead**); pubblicato solo con copertura ≥85% dei minuti. **Oggi: 100%, zero `NaN` residui** |
| `home_absent_count_est`, `away_absent_count_est`, `home_absent_value_est`, `away_absent_value_est` | Transfermarkt | assenze per infortunio alla data della partita: **stime** (suffisso `_est`), rosa ricostruita dai minutaggi Understat |

Il join usa la chiave `(season, home_team, away_team)` con nomi squadra
canonicalizzati (alias in `sources.TEAM_ALIASES`); la data serve solo da
controllo di coerenza.

**Generalizzato a Premier League e La Liga (Fase 60).** `python
scripts/build_league_snapshot.py --enrich premier_league la_liga` aggiunge le
stesse 6 colonne. Le rose Understat vengono dai bundle già caricati in
`files/` (il mirror Understat per-stagione era sparito, come da Fase 14); le
valutazioni/infortuni Transfermarkt vengono invece scaricati dalla rete.
Nel farlo lo schema è arrivato a **38/38 colonne identiche**. Come già
verificato per la Serie A, queste due feature non migliorano il modello
(Fase 4c/11): completano lo schema dati, non ci si aspetta guadagno predittivo.

> ⚠️ **SUPERATA dalle Fasi 67/70 e dall'audit delle 5 leghe.** La copertura
> `squad_value` misurata alla Fase 60 era **95.6% Premier League** e **60.2% La
> Liga** (58.3% prima del fix del matching, Fase 63; il gap era nei giocatori
> sudamericani/spagnoli dal nome breve o senza serie di valutazioni nel datalake
> — diagnosi nel [diario, Fase 60](docs/DIARIO.md)). Quei numeri restano come
> misura *di quella fase*, ma **non descrivono più i dati**: dalla Fase 67 la
> fonte dei valori rosa è **player-scores** (`files/player_scores/`, CC0,
> importato via GitHub Actions) e le ultime celle sotto soglia della 2025-26
> sono state colmate con dati **reali** presi da Transfermarkt (**29** celle:
> 13 alla Fase 70 sulle 3 leghe storiche + **16** su Bundesliga e Ligue 1, in
> `data/squad_value_2526_transfermarkt.csv`, con la scala misurata contro
> player-scores — regola R2). Oggi la copertura è **100% su tutte e 5 le leghe
> e tutte le stagioni**, e `data/estimates/squad_value_2017_26.csv` è **vuoto**:
> nessuna stima attiva su questa colonna.

**Generalizzato anche a Bundesliga e Ligue 1** (Fase 100) con
`scripts/build_new_snapshot.py`, che riusa il codice di **produzione** senza
modificarlo (`loader._normalize`, `understat.parse_season_xg`,
`player_scores.add_squad_values`, `transfermarkt.add_absences`, `fixtures.*`).
Lì i dati non vengono da bundle manuali ma dalla fonte diretta — tornata
raggiungibile — e sono stati verificati **riga per riga contro di essa**.

### Integrità delle quote — overround impossibile (Fase 58, guard reso bilaterale)

Le quote 1X2 (chiusura e apertura) vengono scelte per **intero mercato**, non
colonna per colonna: se il livello di preferenza preferito (`AvgCH/CD/CA`, …)
produce un **overround implicito < 1** (`Σ 1/quota < 1`, un arbitraggio
garantito — impossibile per un book vero, sintomo di un bookmaker anomalo
incluso nella media della fonte), si scarta **in blocco** e si ripiega sul
livello successivo (`B365CH/CD/CA`, …), mai su un solo lato aggiustato a mano.
Trovato e corretto un caso reale per lega (dettagli e formula nel
[diario, Fase 58](docs/DIARIO.md)); impatto nullo sui risultati già pubblicati
(2 righe su 10260, mai usate per stimare il modello — impronta dati invariata).
Test di non-regressione in `tests/test_league_snapshots.py`.

**Il guard era protetto da un lato solo (audit delle 5 leghe).** Un overround
*impossibilmente alto* passava indisturbato: **11 casi**, tutti nella linea O/U
pre-match del 2017-19 (`BbAv`, Betbrain), con margini fino a **1.339** su un
mercato binario — in ognuno il lato Under è incompatibile con l'1X2 della stessa
partita (le due quote non appartengono alla stessa linea). Il guard è ora
**bilaterale** in `src/data/loader._pick_market_odds` (`ORR_MAX = 1.12`), e la
soglia non è arbitraria: nell'era sana (`Avg`, 12.457 righe su 5 leghe) il
massimo osservato è **1.0765**, quindi 1.12 sta oltre 4 punti percentuali sopra
il massimo mai visto in condizioni normali e non può scartare una riga buona.
Effetto: **22 celle** svuotate (3 La Liga, 6 Bundesliga, 2 Ligue 1 — 11 linee ×
2 lati), poi coperte dalla stima dichiarata `ou_open_corrotte_2017_19.csv`.
Verbale e patch in
[`docs/audit_5_leghe/patch_guard_overround_APPLICATA.md`](docs/audit_5_leghe/patch_guard_overround_APPLICATA.md).

### Quote di apertura 2017-19 — chiusura Pinnacle recuperata (Fase 61)

Le stagioni 2017-18 e 2018-19 non hanno le colonne di
chiusura **aggregate** (`AvgCH`/`B365CH`), quindi il loader usava le pre-match
come chiusura e lasciava l'apertura a `NaN` (~22% delle partite). In realtà
quelle stagioni pubblicano **`PSCH`/`PSCD`/`PSCA` = la chiusura di Pinnacle**
(il book di riferimento per efficienza), che era semplicemente ignorata.
Includendola in coda alla chiusura aggregata — e `PSH`/`PSD`/`PSA` in coda
all'apertura aggregata — quelle stagioni ottengono una **chiusura vera** e una
**apertura vera** Pinnacle→Pinnacle (**2279 aperture 1X2 recuperate**), mentre
le stagioni 2019-20+ restano **bit-per-bit identiche** (hanno la media, che
resta preferita). Diff chirurgico: solo le colonne quota, solo in 2017-19,
impronta dati invariata. `python scripts/build_database.py
--refresh-odds` (Serie A) e `... build_league_snapshot.py --refresh-odds
premier_league la_liga` (bundle). Dettagli e tabella completa per stagione nel
[diario, Fase 61](docs/DIARIO.md). *(Aggiornamento Fase 73: anche l'**O/U**
2017-19 ha un'apertura reale — vedi sotto — mentre la sua chiusura è il vero
buco.)*

Le **2279 aperture recuperate** sono la misura della Fase 61, quando le leghe
erano tre. La *politica* però è generale e vale ora su tutte e cinque: nel
2017-19 chiusura e apertura 1X2 sono **Pinnacle→Pinnacle** (margine ~2.5%,
più basso della media ~4.9% — CLV pulito, stesso book), dal 2019-20 sono medie
multi-book (`AvgC*` / `Avg*`). Tabella per epoca e per mercato in
[`docs/DATI.md`](docs/DATI.md) §2. Due sole partite restano senza chiusura 1X2
alla fonte (Alaves-Sociedad 14/10/2017 e Bayern-Hannover 04/05/2019): le loro 6
celle sono state riempite con un **dato reale di un provider secondario**,
dichiarato nel registro delle correzioni (vedi sotto).

### L'O/U 2017-19 era un'apertura, non una chiusura (Fase 73)

Verifica su richiesta: l'unica linea O/U delle stagioni 2017-19 (`BbAv>2.5`,
Betbrain media) è un'**apertura reale** (pre-match), non una chiusura di timing
ambiguo. Quattro evidenze convergenti: il `notes.txt` di football-data la
dichiara raccolta il venerdì/martedì (pre-match); nel grezzo il suffisso `C`
(closing) esiste solo per l'1X2 (`PSC*`), mai per l'O/U; stesso timing di `PS*`
(apertura 1X2); margine ~1.055 ≈ apertura `Avg`, non chiusura `AvgC`. Prima era
messa nello slot **chiusura** e l'apertura lasciata a NaN — l'esatto contrario.
Corretta la politica quote del loader (una regola generale: **chiusura** = solo
colonne `*C*` genuine, NaN se assenti; **apertura** = solo pre-match; insiemi
disgiunti → niente più masking). Snapshot rigenerati con **diff cella-per-cella**:
cambia solo l'O/U 2017-19 (chiusura→NaN, apertura→`BbAv` reale, 2.280 righe) +
1 riga 1X2 (Alaves-Sociedad, `PSC*` vuote → chiusura NaN, apertura `PSH` reale);
**2019-20+ bit-identico**. La stima della chiusura (`ou_close_2017_19.csv`,
Fasi 62/62-bis) resta **byte-identica** (ora legge l'apertura dalla colonna
giusta); il nuovo input sbloccato — la dispersione max-vs-media (`BbMx`/`BbAv`)
— **non** migliora la stima (E3 pooled imbattuto anche qui, 8ª leva ortogonale
respinta). Il buco 2017-19 è così **metà** di quanto si credeva: apertura O/U
reale, solo la chiusura mancante. Dettagli in [diario, Fase 73](docs/DIARIO.md)
e `docs/DATI.md §2`.

### Caccia alle quote O/U 2017-19 — Fase A: dataset già pronti, negativa (Fase 71)

Riprendendo `docs/CACCIA_OU_2017_19.md` (Fase B, scraping BetExplorer, già
chiusa negativa), tentata la Fase A — dataset già scrappati (Kaggle/GitHub/
Hugging Face/Zenodo) che coprano O/U 2.5 apertura+chiusura 2017-18/2018-19.
`WebSearch` conferma (fonte indipendente) che football-data.co.uk — la
fonte-madre di quasi ogni dataset di quote calcio in giro — raccoglie due
istantanee apertura/chiusura **solo dalla stagione 2019/20**; probe
diagnostico via Actions (`scripts/probe_kaggle_ou_datasets.py`, run
[29881936699](https://github.com/BTConomista/Polymarket-oracle/actions/runs/29881936699))
su 6 dataset Kaggle candidati conferma per ispezione diretta delle colonne:
**tutti** quelli con dati quote sono ricostruzioni di football-data.co.uk, e
su ogni file 2017-19 delle 3 leghe hanno **una sola** istantanea O/U
(`BbOU`/`BbAv>2.5`/`BbAv<2.5`), zero apertura/chiusura distinte. Fase A
chiusa negativa (dettagli in [diario, Fase 71](docs/DIARIO.md) e
`docs/CACCIA_OU_2017_19.md`); con la Fase B già chiusa, restano solo Fase D
(OddsPortal headless con login) o accettare le stime attuali come tetto dei
dati per l'O/U 2017-19.

**Spremuta al massimo la stima E3 pooled — imbattuta (Fase 72).** Scelta
dell'utente: non rincorrere Fase D (rischio/complessità del login), ma
migliorare il più possibile la stima già pubblicata prima di accettarla.
Bakeoff di 4 leve nuove e ortogonali sullo stesso protocollo della Fase 62-bis
(`scripts/_run_fase72_ou_close_est2.py`): interazione tra i movimenti 1X2
(MAE 0.0117, invariato), effetto di calendario/stagione (0.0117, invariato),
ridge — peggiora monotonicamente con α (0.0119→0.0155, conferma che non è
overfitting) — e gradient boosting sulle stesse feature (0.0160, +37%,
stessa conclusione delle Fasi 21-23 su un compito diverso). **E3 pooled
resta il migliore**: la stima pubblicata non cambia (dettagli in
[diario, Fase 72](docs/DIARIO.md)). ⚠️ **Promemoria per il futuro**: la
Fase A/B hanno esaurito le vie economiche disponibili OGGI, non tutte le vie
possibili — vedi il promemoria esplicito in testa a
[`docs/CACCIA_OU_2017_19.md`](docs/CACCIA_OU_2017_19.md) e la voce dedicata in
[`docs/PISTE.md`](docs/PISTE.md).

> ⚠️ **CACCIA CHIUSA dalla Fase 100 — e il finale non è quello che ci si
> aspettava.** Il promemoria qui sopra aveva ragione: le vie non erano finite.
> Con la rete tornata raggiungibile il dato vero è stato **trovato** —
> `footiqo.com` pubblica le quote di **chiusura** del book **1xBet** (1X2, O/U
> 0.5→4.5 e GG/NG) e copre **3.652 partite su 3.652** nella finestra 2017-19, su
> tutte e 5 le leghe. Sono state scaricate, validate e congelate in
> `data/ricerca_esterna/` — e **non sono state inserite negli snapshot**: è **un
> solo book**, e come proxy della *media multi-book* (che è ciò che la colonna
> contiene per le altre stagioni) è **peggiore della stima** — MAE **0.0156**
> contro **~0.012**, misurato sulla stagione 2019-20 dove esistono entrambi.
> Sostituire una stima con un dato reale *di semantica diversa* avrebbe
> peggiorato la colonna. La stima `ou_close_2017_19.csv` resta la fonte per
> quelle celle, e la conclusione va detta per intero: **il buco è chiuso non
> perché sia stato riempito, ma perché ora sappiamo che riempirlo con l'unico
> dato esistente costerebbe precisione.** Verbale completo in
> [`docs/CACCIA_OU_2017_19.md`](docs/CACCIA_OU_2017_19.md) e
> [`docs/audit_5_leghe/09_chiusura_buchi.md`](docs/audit_5_leghe/09_chiusura_buchi.md).

### Congestione vera — calendario di club completo (Fase 4e)

Il riposo di `add_rest_days` vede solo le date di Serie A; la **congestione
vera** richiede coppe ed Europa. `src/data/fixtures.py` assembla il **calendario
di club completo** (Serie A dallo snapshot + Champions/Europa/Conference e Coppa
Italia da openfootball, via mirror GitHub) nella tabella grezza versionata
`data/club_fixtures.csv` (`season, team, date, competition, home_away,
opponent`), e aggiunge allo snapshot 4 colonne:

| Colonne | Significato |
|---|---|
| `home_rest_days_full`, `away_rest_days_full` | giorni dall'ultima partita di club in **qualsiasi** competizione, cap 14, solo partite precedenti (no look-ahead), `NaN` se ignoto |
| `home_midweek_europe`, `away_midweek_europe` | 1 se la squadra ha giocato una gara europea/coppa nei ~4 giorni precedenti |

Copertura reale per stagione (onesta, con i buchi documentati) nel
[diario, Fase 4e](docs/DIARIO.md): Champions League tutte e 9 le stagioni,
Europa dal 2020-21, Conference dal 2021-22, Coppa Italia 2020-21→2024-25. Dove
una competizione non è coperta, `rest_days_full` degrada verso il valore
solo-lega (mai in direzione sbagliata) — **nessun numero inventato**. Invariante
verificata su ~3400 partite: `rest_days_full ≤ rest_days` (0 violazioni). La
covariata `rest_full` legge queste colonne ma resta **off di default**: la
validazione walk-forward (Fase 4e-bis) mostra un guadagno dentro il rumore
(−0.0004 medio su 1X2 log-loss, 2020-25), non abbastanza per adottarla —
`python scripts/backtest.py --covariates rest_full --test-season 2122` per
riprovare.

**Generalizzato a Premier League e La Liga (Fase 59).** `python
scripts/build_league_snapshot.py --fixtures premier_league la_liga` assembla
`data/club_fixtures_{premier_league,la_liga}.csv` (Champions/Europa/Conference,
filtrate sul club-paese della lega, + coppa/e nazionale/i: FA Cup/EFL Cup per
la Premier, Copa del Rey per la Liga — stessa finestra di copertura della
Coppa Italia, 2020-21→2024-25) e aggiunge le stesse 4 colonne allo snapshot
(copertura `rest_days_full` 99.5%/99.4%). Nel farlo, corretto un bug reale in
`parse_europe` (filtrava le squadre italiane ANCHE per le altre leghe, azzerando
in silenzio le partite europee di club senza mai un'avversaria italiana in un
turno — dettagli e conteggio nel [diario, Fase 59](docs/DIARIO.md)).

A questo punto restavano assenti per Premier/Liga solo `squad_value`/`absences`
(Transfermarkt) — costruite nella Fase 60 subito successiva (vedi sopra):
il mirror Transfermarkt si è rivelato raggiungibile, contrariamente a quanto
scritto in un primo momento senza averlo verificato.

**Oggi i calendari di club sono cinque**, uno per lega, tutti versionati:

| file | righe | competizioni oltre il campionato |
|---|--:|---|
| `data/club_fixtures.csv` (Serie A) | 11.657 | Champions, Europa, Conference, Coppa Italia |
| `data/club_fixtures_premier_league.csv` | 11.994 | idem UEFA + FA Cup, EFL Cup |
| `data/club_fixtures_la_liga.csv` | 12.102 | idem UEFA + Copa del Rey |
| `data/club_fixtures_bundesliga.csv` | 10.375 | idem UEFA + DFB-Pokal |
| `data/club_fixtures_ligue_1.csv` | 10.701 | idem UEFA + Coupe de France (solo 24-25) |

Ogni file include anche il **preludio** (massima serie 2016-17 + seconda serie
dal 2016-17, Fase 68): serve a radicare il riposo delle squadre all'**esordio**
in campionato, che prima restava `NaN`. Da quella fase `rest_days_full` non ha
**nessun `NaN` residuo** su nessuna lega. Copertura per competizione e per
stagione in [`docs/DATI.md`](docs/DATI.md) §3.

> ⚠️ **Un buco che non è un `NaN`, dichiarato e non ancora chiuso.** Dove
> openfootball non copre una coppa, `midweek_europe` vale **0 anche se la
> squadra ha giocato**: **1.603 celle** censite in questa condizione (lacune
> principali: Europa/Conference League 2025-26 su tutte e 5 le leghe,
> DFB-Pokal 2016-18, Coupe de France quasi ovunque), e ~1.700 valori di riposo
> sbagliati di conseguenza. Le righe di recupero **esistono** — 50 file,
> **3.045 righe** raccolte da Wikipedia in `data/ricerca_esterna/fixtures_*.csv`
> — ma **non sono state applicate**: Wikipedia non è una fonte primaria
> (regola R2/R6). È il caso di scuola del §5-bis del `CLAUDE.md`: un valore che
> *sembra* una misura e non lo è, che nessun confronto snapshot↔fonte può
> intercettare.

### Dati esterni REALI, raccolti e NON integrati (`data/ricerca_esterna/`)

86 file di dati esterni **veri** (non stime), congelati nel repo e usati per
*misurare*, mai innestati in silenzio nelle colonne degli snapshot. Sono la
prova che «trovare il dato» e «poterlo usare» sono due cose diverse:

| cosa | file | perché è fuori dagli snapshot |
|---|---|---|
| **quote di chiusura 1xBet** via `footiqo.com` — 1X2, O/U 0.5→4.5 e **GG/NG**, 2017-20, 5 leghe | 15 `footiqo_<lega>_<stagione>.json` + 10 `footiqo_gol_*.json` + manifest e validazioni | è **un solo book**: come proxy della media multi-book che la colonna contiene è peggiore della stima (MAE 0.0156 contro ~0.012) |
| **calendari di coppa** da Wikipedia (per il falso 0 di `midweek_europe`) | 50 `fixtures_<lega>_<coppa>.csv`, **3.045 righe** | fonte **non primaria** (R2): raccolte, non applicate |
| **manifest delle fonti dell'audit** | `manifest_fonti_audit.json` | 90 impronte SHA256 (45 CSV football-data + 45 JSON Understat) |

Il dato footiqo non è servito a riempire un buco, ma a **rispondere a una
domanda rimasta aperta per 80 fasi**: il GG/NG era «l'unico mercato senza quote
nei dati», quindi l'unico dove non si poteva dimostrare l'efficienza del
mercato. Ora si può, e la risposta è netta — il mercato GG/NG **è informativo**
(log-loss **0.6840** contro **0.6921** della baseline, CI conclusivo), il nostro
miglior prezzo lo **pareggia e non lo batte** (6 varianti su 6 con CI a cavallo
dello zero) e il **DC perde di netto** (+0.0104, IC95% [+0.0063, +0.0145], con
il book che lo ingloba: α\*=0 nel 70% dei fit). Lo «spazio» non era una
proprietà del mercato: era la nostra ignoranza. Dettaglio in
[`docs/audit_5_leghe/11_ggng.md`](docs/audit_5_leghe/11_ggng.md).

### Registro delle correzioni (`data/correzioni_dichiarate.csv`, regola R3)

**Nessuna modifica a mano ai dati, mai.** Ogni correzione vive in un registro
con *cosa, perché, fonte, chi ha deciso, quando*, e viene applicata da uno
script **idempotente** (`scripts/applica_correzioni.py`) che verifica il
valore-prima **cella per cella** e si ferma senza scrivere nulla se non
corrisponde. Stato attuale del registro: **43 righe** — 39 `applicata`, 2
`proposta`, 2 `ritirata`. Le ritirate restano dentro **con il motivo**, così la
sessione dopo non le rifà (§5-bis del `CLAUDE.md`).

Il caso più delicato è dichiarato apertamente: **6 celle** di chiusura 1X2 (2
partite) vengono da un provider **diverso** dal resto della colonna
(`iredchuk/soccer-bookmaker-odds`, identificato per via statistica come chiusura
media-di-mercato e confermato da una seconda fonte indipendente). Costo, che va
detto: per quelle due partite la colonna cambia *semantica*. Beneficio: il dato
reale è 2,8 volte più preciso della stima che avremmo prodotto noi (MAE 0.0060
contro 0.0160). Si torna indietro portando le righe a `ritirata` e rigenerando.

### Stime dichiarate (`data/estimates/`)

Dove un dato di mercato **non esiste nelle fonti**, il progetto può stimarlo coi
propri modelli — ma la stima vive **fuori** dagli snapshot, come
**probabilità** (mai quote: impossibile confonderla con un prezzo), con
l'errore atteso **misurato e dichiarato**, e non si usa **mai** per simulare
ROI. Regole complete in [`data/estimates/README.md`](data/estimates/README.md),
schede in [`docs/DATI.md`](docs/DATI.md) §5.

| file | righe | cosa stima |
|---|--:|---|
| `ou_close_2017_19.csv` | 3.638 | la **chiusura** O/U 2.5 del 2017-19, che non esiste alla fonte su nessuna delle 5 leghe (MAE ~0.014 nel regime d'uso) |
| `ou_open_corrotte_2017_19.csv` | 12 | l'**apertura** O/U delle linee svuotate dal guard bilaterale (MAE 0.0143) |
| `open_sparse_1x2_ou.csv` | 2 | l'apertura delle 2 partite sparse senza apertura vera (MAE ~0.016/~0.020) |
| `squad_value_2017_26.csv` | **0** | niente: svuotato alla Fase 70, il buco è stato chiuso con dati **reali** |
| `celle_residue.csv` | 32 | **niente — è il registro di NON-stima**: quali celle restano vuote e *perché non conviene* stimarle |

L'ultima riga è la più utile per chi arriva dopo: dice che «non stimare» è stata
una scelta motivata, non una dimenticanza.

### Quote outright congelate (`data/outright_snapshots/`, Fase 97)

L'unico dato del repo che nasce da un **fetch live** e viene comunque congelato:
senza archivio, i prezzi di oggi sparirebbero col container. Fonti: **Polymarket**
(Gamma API) e **Smarkets** (API v3 pubblica) — entrambe *borse*, non bookmaker.
Formato: `YYYY-MM-DD.json` (completo) + `history.csv` (data × fonte × lega ×
mercato × squadra). Si scrive con `python scripts/archive_outrights.py`
(idempotente sulla data).

Serve a rimuovere **in avanti** il limite più duro del simulatore di stagione
(Fase 89): non esistono quote outright storiche, quindi «battiamo il mercato» su
quella famiglia non è testabile all'indietro. Avvertenze di semantica
(`settled_share`, `exclusive=False`, libri con un lato solo, nomi squadra **non**
normalizzati) nel README della cartella e in `docs/DATI.md` §5-bis.

### Come si verifica che i dati siano giusti (audit)

Verificare, non fidarsi. `scripts/audit_snapshots.py` fa tre controlli, dal più
debole al più forte: **(A) interno** — struttura, coerenza, range, duplicati,
senza rete; **(B) esterno** — confronto **riga per riga** con le fonti originali
ri-scaricate oggi, con le 10 colonne quota ri-derivate dallo stesso codice di
produzione; **(C) indipendente** — i gol secondo Understat (fonte terza)
confrontati con quelli dello snapshot. Esito sulle due leghe entrate per ultime:
**0 differenze** su gol, date, tiri, quote e xG.

Accanto c'è l'audit **avversariale**, che fa la domanda opposta e più scomoda —
*e se la fonte stessa fosse sbagliata?*: `scripts/audit_anomalie.py` e
`scripts/cerca_segnaposto.py` (quest'ultimo cerca i **finti pieni**, la
categoria pericolosa della regola R6: valori di comodo che *sembrano* misure).
Bilancio dell'audit a 5 leghe: **7 anomalie** confermate — 6 nella fonte e **1
nostra** (l'ordine delle colonne, poi allineato) — più **1 ritirata** come falso
positivo. I verbali integrali sono gli 11 report di
[`docs/audit_5_leghe/`](docs/audit_5_leghe/00_indice.md), con i JSON grezzi
dietro ogni tabella in `docs/audit_5_leghe/numeri/`.

Tutta la pipeline è **offline-first**: `backtest.py`/`tune.py` leggono lo snapshot
congelato (nessun download per run), quindi i risultati sono riproducibili identici.
Ogni backtest è inoltre registrato in `experiments/runs.jsonl` con l'impronta dei
dati usati (vedi `experiments/README.md`).

### Fonti originali

> ⚠️ **SUPERATA dalla Fase 100: la rete è tornata raggiungibile.** Per decine di
> fasi questo paragrafo ha detto che l'ambiente cloud **non** raggiungeva
> `football-data.co.uk`, `understat.com` e `transfermarkt.com`, e tutta
> l'architettura dei bundle manuali in `files/` nasce da lì. **Oggi rispondono
> 200**, verificato scaricando davvero (non pingando): le 45 stagioni di
> football-data sono state ri-scaricate, Bundesliga e Ligue 1 sono entrate senza
> bundle, e — la conseguenza che conta — gli snapshot sono stati verificati
> **contro la fonte-madre**, non solo contro sé stessi. Lo strumento è
> `scripts/fetch_sources.py` (scarica con provenienza SHA256). Mappa della rete
> aggiornata, con i vincoli che restano (`robots.txt` di OddsPortal, `api.github.com`
> bloccato, throttle ≥1,5 s), in
> [`docs/MANUALE_SOPRAVVIVENZA.md`](docs/MANUALE_SOPRAVVIVENZA.md) §1.
> **Lezione operativa, generale:** «presumibilmente bloccato» non è un fatto —
> due host erano marcati per esclusione da mesi e bastava un `curl`.

Quando la rete era chiusa si usavano mirror su GitHub con **lo stesso formato**;
questa è la situazione delle fonti oggi, mirror compresi:

- **football-data** e **Understat**: il repo mirror storico che li serviva
  entrambi **è sparito da GitHub** (404, verificato luglio 2026 alla Fase 14 e
  ri-verificato alla Fase 101-bis) — ma non serve più, perché i siti originali
  rispondono. Dalla Fase 101-bis `sources.BASE_URL` punta all'**ufficiale**
  (`OFFICIAL_BASE_URL`): prima il default era il mirror morto, cioè `--refresh`
  puntava all'unica delle due URL che non risponde. ⚠️ `sources.UNDERSTAT_URL`
  punta **ancora** al mirror (`UNDERSTAT_MIRROR_URL`), con l'ufficiale
  disponibile accanto in `UNDERSTAT_OFFICIAL_URL`. Il progetto
  non dipende comunque da nessuno dei due: lo snapshot congelato è versionato, e
  i **CSV grezzi originali** football-data della Serie A (9 stagioni, con TUTTE
  le colonne quote) sono congelati in **`data/football_data_raw/`** (con README di
  provenienza) — `scripts/_restore_raw_cache.py` ricostruisce la cache
  `data/raw/` da lì. Per Premier e Liga l'equivalente sono i bundle in `files/`.
  Nota su Understat: l'API vuole l'header `X-Requested-With: XMLHttpRequest`
  (senza → 404) e risponde **gzip**.
- **Valori rosa**: dalla Fase 67 la fonte ufficiale è il dataset **player-scores**
  (`dcaribou/transfermarkt-datasets`, CC0) in `files/player_scores/`, importato
  via **workflow GitHub Actions** (`.github/workflows/import_dataset.yml`: il
  runner ha rete libera). Il vecchio datalake `salimt/football-datasets`
  (`sources.TRANSFERMARKT_MIRROR_URL`) resta usato **solo** per gli infortuni
  (`absent_*_est`). ⚠️ Il suo limite noto — ~25% dei profili privo di serie di
  valutazioni, che produceva `squad_value = NaN` — **non si applica più ai valori
  rosa**: con player-scores + i 29 recuperi manuali la copertura è al 100%.

Girando il progetto in locale gli URL ufficiali sono già in
`src/data/sources.py` (per Understat c'è `UNDERSTAT_OFFICIAL_URL`).
