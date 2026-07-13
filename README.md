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
il margine del bookmaker. E non è questione di "scommettere prima": il modello
**non batte nemmeno la linea di apertura** (gap +0.0146, ROI@open −17.3%, CLV
negativo — Fase 14). **Non usare questo modello per scommettere soldi
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

**Adottato**: solo il tuning (2b/4b/4d) e il **prior neopromosse (7)**. Tutto il
resto è al livello del rumore o dannoso, e resta **off di default** — alcune
opzioni (ricalibrazione, `--draw-inflation`) restano utili per l'uso pratico.

**Dove vive il gap col mercato** (anatomia completa in [Fase 9](#anatomia-del-gap-col-mercato--fase-9-dove-vive-il-divario)):
è **quasi tutto nel PAREGGIO** — escluso il pari (mercato "12") il modello è già a
livello mercato (dalla Fase 17, con CI95: il gap del 12 è **statisticamente
indistinguibile da zero**). Il pareggio è quasi-casuale per tutti (mercato incluso): il gap
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

**Per mercato × stagione (Fase 15-bis,** `scripts/_run_gap_markets.py`**)** — la
matrice completa, per verificare che le medie qui sopra non nascondano stagioni
storte:

| Gap | 2020-21 | 2021-22 | 2022-23 | 2023-24 | 2024-25 | 2025-26 | media |
|---|--:|--:|--:|--:|--:|--:|--:|
| 1X2 | +0.0202 | +0.0145 | +0.0146 | +0.0187 | +0.0170 | +0.0141 | **+0.0165** |
| 1X (casa o pari) | +0.0160 | +0.0082 | +0.0089 | +0.0175 | +0.0082 | +0.0108 | +0.0116 |
| 2X (ospite o pari) | +0.0151 | +0.0105 | +0.0127 | +0.0128 | +0.0156 | +0.0096 | +0.0127 |
| **12 (no pari)** | +0.0017 | +0.0031 | +0.0021 | **−0.0021** | +0.0050 | +0.0022 | **+0.0020** |
| Over/Under 2.5 | **−0.0031** | +0.0147 | +0.0168 | +0.0007 | +0.0101 | +0.0020 | +0.0069 |
| GG/NG (vs baseline*) | +0.0074 | −0.0054 | +0.0069 | −0.0003 | +0.0037 | +0.0039 | +0.0027 |

*\*GG/NG non ha quote nei dati → gap vs baseline (in-sample, severa). Le doppie
chance usano il mercato derivato dalle 1X2 devigate.*

Tre letture (tutte e 6 le stagioni, non solo la media):

- **Il "quasi-zero" del 12 regge in OGNI stagione** (range −0.0021…+0.0050; nel
  2023-24 il modello *batte* il mercato). Sapere chi è più forte è a livello
  mercato sempre, non in media.
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

### Il mercato ingloba il modello — Fase 16 (encompassing, il test definitivo)

La domanda che il gap non può dire: un modello a +0.0165 dal mercato contiene
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
| gap 1X2 (modello − mercato) | +0.0165 | [+0.0106, +0.0225] ✱ | 0.0% |
| gap 12 no pari | +0.0020 | [−0.0006, +0.0046] | 6.5% |
| gap O/U 2.5 | +0.0069 | [+0.0022, +0.0116] ✱ | 0.2% |
| Δ prior neopromosse (V4−V3) | −0.0010 | [−0.0025, +0.0004] | 92.6% |

*✱ = CI95 che non attraversa lo zero.*

Quattro letture oneste:

- **Il gap 1X2 è reale e solido** (mai vicino a zero): il mercato è davvero
  migliore, non è varianza.
- **Il "quasi-zero" del 12 è ora un'affermazione statistica**: +0.0020 con CI
  che include lo zero — sul "chi vince" modello e mercato sono formalmente
  indistinguibili.
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
**meglio** (batte il DC di +0.0165 sull'1X2). E se **invertissimo** le quote per
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
    (`scripts/_run_gap_uncertainty.py`, B=10.000): gap 1X2 **+0.0165
    [+0.0106, +0.0225]** (reale), gap 12 **+0.0020 [−0.0006, +0.0046]**
    (statisticamente zero: sul "chi vince" siamo a livello mercato), gap O/U
    +0.0069 [+0.0022, +0.0116] (reale), Δ prior neopromosse −0.0010
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
27. **Dati davvero nuovi** (formazioni ufficiali pre-partita, quote di apertura
    vere) — l'unica leva che le 22 fasi indicano non ancora esaurita — oppure
    **uso pratico** del modello attuale (comando di predizione).
28. **Estensione** a nuovi campionati (già predisposto in `sources.py`): non per
    un edge ma per capire se le conclusioni (gap, tetto, prior) sono robuste
    fuori dalla Serie A.
29. **Integrazioni** con piattaforme esterne (Polymarket, exchange, …), dove il
    mercato potrebbe essere meno efficiente della chiusura dei bookmaker.

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
`understat.com` né `transfermarkt.com` (policy di rete), quindi si usavano mirror
su GitHub con **lo stesso formato**:

- **football-data** e **Understat**: stesso repo mirror — URL in
  `sources.BASE_URL` / `sources.UNDERSTAT_URL`. ⚠️ **Il mirror è sparito da
  GitHub** (404, verificato luglio 2026, Fase 14): `--refresh` non ha più una
  fonte a monte raggiungibile dal cloud. Il progetto non ne dipende: lo snapshot
  congelato è versionato, e i **CSV grezzi originali** football-data (9 stagioni,
  con TUTTE le colonne quote) sono congelati in **`data/football_data_raw/`** (con
README di provenienza) —
  `scripts/_restore_raw_cache.py` ricostruisce la cache `data/raw/` da lì.
- **Transfermarkt**: datalake `salimt/football-datasets` — URL in
  `sources.TRANSFERMARKT_MIRROR_URL`. Limite noto: ~25% dei profili è privo di
  serie di valutazioni (per questo alcune squadre-stagione hanno `squad_value = NaN`).

Girando il progetto in locale è sufficiente sostituire gli URL in
`src/data/sources.py` con quelli ufficiali (football-data.co.uk è raggiungibile
da un browser/rete normale; per Understat c'è già `UNDERSTAT_OFFICIAL_URL`).
