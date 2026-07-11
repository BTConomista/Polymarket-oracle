# Polymarket Oracle

Motore di stima delle **probabilità reali di eventi sportivi** (calcio),
**indipendente dalle piattaforme** di scommessa.

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

## Stato attuale

Prima pipeline **end-to-end** funzionante su **Serie A**:

`dati storici → modello Dixon-Coles → probabilità 1X2 e Over/Under 2.5 → validazione`

- **Modello**: Dixon-Coles (1997) con decadimento temporale, implementato da zero
  (`src/models/dixon_coles.py`). Stima forza d'attacco/difesa di ogni squadra +
  vantaggio-casa + correzione sui punteggi bassi.
- **Dati**: 9 stagioni di Serie A (2017-18 → 2025-26) in formato football-data.co.uk.
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
| **1X2** (log-loss) | **0.9797** | **0.9632** | 1.0834 | 1.0860 |
| **Over/Under 2.5** | 0.6885 | 0.6816 | 0.6892 | 0.6961 |

*Nota onestà (audit Fase 15): la baseline stampata dalla pipeline usa le frequenze
H/D/A della **stagione di test stessa** (in-sample: è la costante ottima a
posteriori, quindi leggermente troppo forte). La baseline **ex-ante** — frequenze
delle sole stagioni precedenti, l'unica giocabile davvero — è ricalcolata qui
accanto: 1.0860 (1X2) e 0.6961 (O/U). La differenza non cambia nessuna
conclusione.*

Il modello **batte nettamente la baseline** ma **non il mercato**: gap 1X2
**+0.0165** (ha chiuso **~86%** della distanza baseline→mercato: 86.3% sulla
baseline in-sample, 86.6% su quella ex-ante). Su una singola stagione i numeri
oscillano → si giudica sulla media. Il *value betting* simulato con la config
ufficiale dà **ROI medio −15.7%** su 6 stagioni (864 scommesse; per stagione da
−4.7% a −23.0%; pooled −15.6%): chi non batte la linea di chiusura perde contro
il margine del bookmaker. **Non usare questo modello per scommettere soldi
veri.** *(Il "ROI ≈ −8.5%" riportato in precedenza era il valore del primo
backtest di Fase 1 — una sola stagione, modello iniziale — rimasto per errore
accanto a metriche a 6 stagioni: corretto nell'audit di Fase 15.)*

### Come si è chiuso il gap (dal modello grezzo all'attuale)

| Versione | gap 1X2 vs mercato | Δ |
|---|--:|--:|
| V0 — grezzo (soli gol, no shrinkage/decay) | +0.0236 | — |
| V1 — gol tarato (shrinkage + emivita, Fase 2b) | +0.0185 | **−0.0051** |
| V2 — +xG nel blend (Fase 4b) | +0.0181 | −0.0004 |
| V3 — emivita ri-tarata 365g (Fase 4d) | +0.0175 | −0.0006 |
| V4 — +prior neopromosse (Fase 7, **ATTUALE**) | **+0.0165** | −0.0010 |

*Il Δ del prior compare come −0.0010 qui e come −0.0011 nella tabella degli
esperimenti: non è un refuso ma due stime diverse dello stesso intervento —
−0.0010 con δ=0.23 fisso (config ufficiale: 0.9797 vs 0.9807), −0.0011 con δ
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
| 14 | quote di apertura + CLV (codice pronto) | — (dati `*_open` non ancora estesi) | ⏸ in attesa dati |
| 15 | **audit dei calcoli** (verifica di ogni numero) | ROI corretto (−15.7%, non −8.5%); resto confermato | ✅ doc corretta |

**Adottato**: solo il tuning (2b/4b/4d) e il **prior neopromosse (7)**. Tutto il
resto è al livello del rumore o dannoso, e resta **off di default** — alcune
opzioni (ricalibrazione, `--draw-inflation`) restano utili per l'uso pratico.

**Dove vive il gap col mercato** (anatomia completa in [Fase 9](#anatomia-del-gap-col-mercato--fase-9-dove-vive-il-divario)):
è **quasi tutto nel PAREGGIO** — escluso il pari (mercato "12") il modello è già a
livello mercato. Il pareggio è quasi-casuale per tutti (mercato incluso): il gap
residuo non è cattiva modellazione ma **informazione che il mercato ha e noi no**
sulle singole partite (infortuni, motivazioni, notizie dell'ultima ora).

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

| Mercato | modello (uff.) | Mercato | Baseline |
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
scompone. Gap 1X2 medio attuale **+0.0165** (modello 0.9797 vs mercato 0.9632);
il modello ha chiuso ~86% della distanza baseline→mercato. Tre tagli:

**Per mercato** — il gap è **quasi tutto nel PAREGGIO**:

| 1X2 | 1X | 2X | **12 (no pari)** | O/U 2.5 | GG/NG |
|--:|--:|--:|--:|--:|--:|
| +0.0165 | +0.0116 | +0.0127 | **+0.0020** | +0.0069 | −0.0018 |

Escluso il pari (mercato 12) il modello è **a livello mercato**: la debolezza è
prezzare i pareggi, non stimare chi è più forte.

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

**La tabella di riferimento, per stagione** (config ufficiale, valori reali dal
registro — 1X2 log-loss):

| Stagione | Modello | Mercato | Gap | ROI value bet (n) |
|---|--:|--:|--:|--:|
| 2020-21 | 0.9532 | 0.9331 | +0.0202 | −23.0% (129) |
| 2021-22 | 0.9860 | 0.9715 | +0.0145 | −15.1% (152) |
| 2022-23 | 0.9916 | 0.9770 | +0.0146 | −14.9% (152) |
| 2023-24 | 0.9854 | 0.9668 | +0.0187 | −15.0% (125) |
| 2024-25 | 0.9693 | 0.9523 | +0.0170 | −21.2% (159) |
| 2025-26 | 0.9925 | 0.9784 | +0.0141 | −4.7% (147) |
| **MEDIA** | **0.9797** | **0.9632** | **+0.0165** | **−15.7% (864 tot)** |

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
batte la baseline (anche quella ex-ante), non batte il mercato (+0.0165), il
value betting perde (più di quanto scritto prima: −15.7%, non −8.5%). Il tetto
resta reale. **Non usare il modello per scommettere soldi veri.**

## Struttura

```
src/
  data/         raccolta e normalizzazione dati (schema interno pulito)
    sources.py    UNICO punto con URL e stagioni (cambiare fonte = 1 riga)
    loader.py     download + parsing + normalizzazione
  models/
    dixon_coles.py   il modello (stima + predizione)
  evaluation/
    metrics.py    Brier, log-loss, devigging quote, baseline
scripts/
  download_data.py   scarica i CSV (cache in data/raw/)
  backtest.py        esegue il backtest walk-forward e stampa il report
tests/              test unitari del modello e delle metriche
worldcup/           esperimento parallelo a bassa priorità (Mondiali)
```

## Come si usa

```bash
pip install -e .            # oppure: pip install numpy pandas scipy pytest

python scripts/download_data.py     # scarica i dati storici (una volta)
python scripts/backtest.py          # esegue il backtest sulla stagione 2025-26
python scripts/analyze.py           # analizza gli errori del backtest
python scripts/tune.py --sweep shrinkage          # tara un iperparametro su piu' stagioni
python scripts/markets.py           # grande backtest su TUTTI i mercati (1X2, O/U, GG/NG, doppie chance)
python -m pytest                    # esegue i test
```

Opzioni utili:

```bash
python scripts/backtest.py --test-season 2425          # testa un'altra stagione
python scripts/tune.py --sweep half_life_days --values 0 180 365 730
python scripts/tune.py --sweep shots_blend --values 0 0.5 1
```

## Roadmap (idee, non impegni)

1. ✅ **Fase 1** — tracer bullet: Dixon-Coles + backtest su Serie A.
2. ✅ **Fase 2a** — analisi degli errori: capito dove il modello perde (neopromosse,
   inizio stagione) e corretto il bug dei nomi squadra.
3. ✅ **Fase 2b** — tuning: shrinkage + memoria lunga (emivita 730g). Divario
   medio col mercato da +0.026 a +0.017.
4. ✅ **Fase 3** — tiri in porta come informazione nuova: **risultato negativo**
   (i tiri grezzi non aiutano in modo affidabile). Codice mantenuto per l'xG reale.
5. ✅ **Fase 4a** — arricchimento dati: **xG reale Understat per il 100% delle
   3420 partite**, valori rosa Transfermarkt a inizio stagione (copertura 63-80%
   per stagione) e assenze stimate da infortuni. Snapshot e DB rigenerati, base
   invariata (stessa impronta dati). Vedi `docs/DIARIO.md`, Fase 4a.
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
    gap 1X2 medio **+0.0165** (modello 0.9797 vs mercato 0.9632). Scomposto: varia
    per stagione (+0.014→+0.020, peggio nel COVID 2020-21), per forza-squadra (a U:
    deboli +0.0206 e forti +0.0180 peggio delle medie +0.0123), e — soprattutto —
    **è quasi tutto nel PAREGGIO** (il mercato 12 senza pari ha gap +0.0020 ≈
    mercato). Punta al prossimo passo mirato: **correlazione dei punteggi**. Vedi
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
19. 🔶 **Fase 14** — **quote di apertura e CLV** (codice pronto, dati in attesa):
    loader per le colonne `*_open` (linea pre-chiusura football-data), metriche
    vs apertura, value bet @open e CLV in `experiment_log`, script
    `_run_fase14_openline.py`, test. I dati `*_open` **non sono ancora nello
    snapshot** (serve `build_database.py --open-odds` con accesso ai CSV grezzi):
    nessun numero pubblicato finché non arrivano.
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
21. **Prossimo bivio** — **dati davvero nuovi** (l'unica via rimasta per un edge)
    oppure **uso pratico** del modello attuale (comando di predizione).
22. **Estensione** a nuovi campionati (già predisposto in `sources.py`).
23. **Integrazioni** con piattaforme esterne (Polymarket, exchange, …).

## Archivio dati interno (riproducibilità)

Per non dipendere dalla disponibilità *in tempo reale* di una fonte esterna (che
può cambiare o sparire) e permettere a chiunque di rieseguire gli stessi calcoli,
i dati sono **congelati** in un archivio interno con due artefatti:

- **snapshot** `data/serie_a_matches.csv` — **versionato in git**, testo diffabile:
  è la fonte di verità congelata (3420 partite, 9 stagioni). Chi clona il repo ha
  esattamente gli stessi dati, **senza rete**.
- **database** `data/football.db` — SQLite queryable, **rigenerabile** dallo
  snapshot (non versionato).

```bash
python scripts/build_database.py            # ricostruisce il DB dallo snapshot (offline)
python scripts/build_database.py --enrich   # ricalcola xG/rose/assenze sullo snapshot esistente
python scripts/build_database.py --fixtures # assembla il calendario di club completo + congestione vera
python scripts/build_database.py --refresh  # riscarica TUTTO dalle fonti e aggiorna lo snapshot
sqlite3 data/football.db "SELECT season, COUNT(*) FROM matches GROUP BY season"
```

### Colonne di arricchimento (Fase 4a)

Oltre alle 15 colonne base (partita, gol, tiri in porta, quote), lo snapshot
contiene 14 colonne da fonti esterne (`NaN` dove la fonte non copre):

| Colonne | Fonte | Note |
|---|---|---|
| `home_xg`, `away_xg`, `home_npxg`, `away_npxg` | Understat | xG e xG senza rigori; **100% delle partite** |
| `home_ppda`, `away_ppda`, `home_deep`, `away_deep` | Understat | pressing e passaggi profondi |
| `home_squad_value`, `away_squad_value` | Transfermarkt | valore rosa (EUR) all'inizio stagione (valutazioni ≤ 1 settembre, **niente look-ahead**); pubblicato solo con copertura ≥85% dei minuti, altrimenti `NaN` |
| `home_absent_count_est`, `away_absent_count_est`, `home_absent_value_est`, `away_absent_value_est` | Transfermarkt | assenze per infortunio alla data della partita: **stime** (suffisso `_est`), rosa ricostruita dai minutaggi Understat |

Il join usa la chiave `(season, home_team, away_team)` con nomi squadra
canonicalizzati (alias in `sources.TEAM_ALIASES`); la data serve solo da
controllo di coerenza.

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

Tutta la pipeline è **offline-first**: `backtest.py`/`tune.py` leggono lo snapshot
congelato (nessun download per run), quindi i risultati sono riproducibili identici.
Ogni backtest è inoltre registrato in `experiments/runs.jsonl` con l'impronta dei
dati usati (vedi `experiments/README.md`).

### Fonti originali

L'ambiente di sviluppo cloud non raggiunge direttamente `football-data.co.uk`,
`understat.com` né `transfermarkt.com` (policy di rete), quindi si usano mirror
su GitHub con **lo stesso formato**:

- **football-data** e **Understat**: stesso repo mirror (aggiornato da un
  workflow giornaliero) — URL in `sources.BASE_URL` / `sources.UNDERSTAT_URL`;
- **Transfermarkt**: datalake `salimt/football-datasets` — URL in
  `sources.TRANSFERMARKT_MIRROR_URL`. Limite noto: ~25% dei profili è privo di
  serie di valutazioni (per questo alcune squadre-stagione hanno `squad_value = NaN`).

Girando il progetto in locale è sufficiente sostituire gli URL in
`src/data/sources.py` con quelli ufficiali (per Understat c'è già
`UNDERSTAT_OFFICIAL_URL`).
