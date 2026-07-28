# `numeri/` — gli artefatti grezzi dietro le tabelle dei report

Ogni file qui è l'**output congelato** della run che ha prodotto un report di
`docs/audit_5_leghe/` (**audit a 5 leghe, Fase 100**). Servono a una cosa sola:
permettere a chiunque di rifare un conto senza ri-eseguire l'audit. Vivevano in
`cantiere/out/` — la cartella `cantiere/` non esiste più, la tabella di
corrispondenza è in testa a [`../00_indice.md`](../00_indice.md).

**Regola d'uso:** quando un numero di un report e il suo JSON divergono, **fa
fede il JSON** e si corregge il report. Le quattro `.md` (`caccia_calendari`,
`caccia_ou_dataset`, `caccia_quote_singole`, `caccia_understat`) sono la lettura
per un umano del `.json` gemello.

Contenuto: **39 artefatti** — 34 `.json`, 4 `.md`, 1 `.csv` — oltre a questo
README.

---

## Catalogo — cosa contiene ogni file

### Report 1 · audit dei dati ([`01_audit_dati.md`](../01_audit_dati.md))

| file | cosa contiene | prodotto da |
|---|---|---|
| `audit_serie_a.json` · `audit_premier_league.json` · `audit_la_liga.json` · `audit_bundesliga.json` · `audit_ligue_1.json` | esito **controllo per controllo** dei livelli A/B/C per una lega: chiavi `league`, `n_rows`, `checks` (schema, duplicati, girone, copertura, overround, nomi squadra; confronto riga-per-riga con football-data ri-scaricato; gol da Understat) | `scripts/audit_snapshots.py` |
| `audit_anomalie.json` | l'audit **avversariale** (livello D), una chiave per famiglia di sospetto: `margini`, `coerenza`, `fisica`, `impronte`, `riposo`, `xg`, `xg_segnaposto` | `scripts/audit_anomalie.py` |

### Report 2 · le stime ([`02_stime.md`](../02_stime.md))

| file | cosa contiene | prodotto da |
|---|---|---|
| `verifica_stime.json` | le otto prove di falsificazione della stima E3: `riproducibilita`, `errore` (in-sample, LOSO, LOLO, walk-forward), `alternative`, `domain_shift`, `falsificazione`, `input_corrotti`, `altre_stime` | `scripts/verifica_stime.py` |

### Report 3 · import di Bundesliga e Ligue 1 ([`03_nuove_leghe.md`](../03_nuove_leghe.md))

| file | cosa contiene | prodotto da |
|---|---|---|
| `eda_5_leghe.json` | la tabella EDA delle 5 leghe (gol/gara, esiti, γ, Var/Media, δ promosse, corr(xG,gol), margine 1X2) + il `deficit_pareggio` per quartile di equilibrio | `scripts/eda_nuove_leghe.py` |
| `riconciliazione_nomi.json` | i 103 alias nuovi lega per lega, con quali sono **esercitati** dalle fonti e quali sono varianti difensive | `scripts/riconcilia_nomi.py` |

### Report 4 · le decisioni ([`04_decisioni.md`](../04_decisioni.md))

| file | cosa contiene | prodotto da |
|---|---|---|
| `recupero_squad_value_tm.json` | il confronto **Transfermarkt ↔ nostro `squad_value`** club per club, per lega, con rapporto mediano e correlazione (⚠️ congelato, vedi sotto) | `scripts/recupero_squad_value_tm.py` |

### Report 6 · tranche 3, il playbook sulle leghe nuove ([`06_tranche3.md`](../06_tranche3.md))

| file | cosa contiene | prodotto da |
|---|---|---|
| `tranche3_tracer.json` | il **tracer bullet** del DC su tutte e 5 le leghe: log-loss modello/baseline/mercato 1X2 e O/U, pooled e per stagione, `vs_baseline` e `vs_mercato` con CI95 | `scripts/tranche3_tracer.py` |
| `tranche3_market_tracer.json` | le **costanti del mercato** per lega: margine, θ (pooled e LOSO), tilt λ/μ, φ0 (pooled e LOSO), κ, ROI pari-equilibrio con CI | `scripts/tranche3_market_tracer.py` |
| `tranche3_mercati.json` | il motore market-implied contro DC-da-gol e baseline sui **15 mercati** Tier 1, per lega, con CI su `mi_meno_dc` | `scripts/tranche3_mercati.py` |
| `tranche3_ritaratura.json` | la ri-taratura per-lega (δ per-lega, emivita 730g, shrinkage 3.0) contro il riferimento, con CI95 | `scripts/tranche3_ritaratura.py` |

### Report 7 e 9 · le righe corrotte, i buchi e la loro chiusura ([`07_dati_corrotti.md`](../07_dati_corrotti.md), [`09_chiusura_buchi.md`](../09_chiusura_buchi.md))

| file | cosa contiene | prodotto da |
|---|---|---|
| `caccia_ou_dataset.json` + `caccia_ou_dataset.md` | la caccia al **dato vero** della chiusura O/U 2017-19: bersaglio, aspettativa dichiarata prima, fonte trovata (1xBet via footiqo), criteri di accettazione e le confutazioni A-G | sorgente in appendice al `.md` (non è un file di `scripts/`) |
| `caccia_quote_singole.json` + `caccia_quote_singole.md` | la caccia alle **celle-quota singole** mancanti, una partita alla volta: censimento, esito per caso, casi nuovi trovati, natura della fonte esterna | idem |
| `caccia_calendari.json` + `caccia_calendari.md` | il recupero dei **calendari di coppa** contro Wikipedia: censimento, pagine utili/vuote, nomi non agganciati, confronto con la terza fonte | idem (il `.md` dichiara che `caccia_calendari.py` e `wiki.py` non esistono come file: il sorgente è l'appendice A) |
| `caccia_understat.json` + `caccia_understat.md` | la caccia ai **segnaposto di Understat**: le 9 firme indipendenti su 16.110 partite, la prova di potenza con 500 segnaposto piantati, copertura e riconciliazione | `scripts/cerca_segnaposto.py` |
| `stima_ou_close_nuove.json` | la stima della **chiusura O/U** per Bundesliga e Ligue 1: `n_fit`, `n_target`, `non_stimabili`, diagnostico del movimento 1X2, e il confronto fra candidati nel regime d'uso | `scripts/stima_ou_close_nuove.py` |
| `stima_ou_open_bakeoff.json` | il **bakeoff di 26 varianti** sulle 9 linee O/U di apertura corrotte (M1 → M4 → M5g), k-fold, copertura footiqo, confutazioni | `scripts/stima_ou_open_bakeoff.py` |
| `stima_ou_corrotte_metodo_storico.csv` | il **diagnostico storico** delle stesse righe col metodo M1 (MAE 0.0267), tenuto per confronto: il file di produzione è `data/estimates/ou_open_corrotte_2017_19.csv` | `scripts/stima_ou_corrotte.py` |
| `stima_sot_understat.json` | la ricostruzione del **tiro in porta** di football-data dai tiri di Understat: copertura, campione stratificato, le 8 regole candidate, classifica, dettaglio per lega/stagione/epoca | `scripts/stima_sot_understat.py` |
| `stima_celle_residue.json` | le **celle residue** una per una: natura della fonte esterna del caso A, la stima, l'xG (caso B) e la partita non consolidata (caso C) | `scripts/stima_celle_residue.py` |

### Report 10 · la rosa dei modelli ([`10_modelli_nuove_leghe.md`](../10_modelli_nuove_leghe.md))

| file | cosa contiene | prodotto da |
|---|---|---|
| `leve_theta_griglia.json` | il **router double-Poisson**: griglia θ 1.000-1.400 passo 0.025 su 25 mercati × 5 leghe × 7 stagioni, selezione LOSO e leave-future-out | `scripts/leve_theta_griglia.py` |
| `leve_phi_griglia.json` | la **φ(\|λ−μ\|)**: griglia bidimensionale φ₀ × κ, 11 mercati per lega. ⚠️ Contiene anche il numero della **ricalibrazione-μ sul GG/NG** citato al §6 del report | `scripts/leve_phi_griglia.py` |
| `leve_devig_shin.json` | il **devig di Shin** contro il moltiplicativo e il power-devig: `per_lega`, `pooled`, `nove_stagioni` | `scripts/leve_devig_shin.py` |
| `leve_ricalibrazioni.json` | le **ricalibrazioni del mercato**: pesi per-classe (w_D, w_A), tilt dei livelli, power-devig, per lega | `scripts/leve_ricalibrazioni.py` |
| `leve_beat_close.json` | il **beat-the-close** (`sharpen_1x2` contro la chiusura devigata) sulle 5 leghe, con la scomposizione tilt/scala e il ROI | `scripts/leve_beat_close.py` |
| `leve_apertura.json` | il motore market-implied invertito dall'**apertura**: listino a 25 mercati, θ/φ, apertura contro chiusura, movimento, confutazioni | `scripts/leve_apertura.py` |
| `leve_dc_panchina.json` | le **leve di panchina del DC** e le 6 covariate sul path standalone (112 backtest walk-forward) | `scripts/leve_dc_panchina.py` |
| `nuovo_mercato_campione.json` | il **mercato campione di stagione**: regole di spareggio verificate, controllo di sanità sulla Fase 89, backtest e confronti con le baseline | `scripts/nuovo_mercato_campione.py` |
| `nuovo_fronte_generale.json` | il **fronte generale** (pooled vs per-lega) su θ, φ, ρ e DC, più la confutazione col placebo di leghe rimescolate e il DC congiunto | `scripts/nuovo_fronte_generale.py` |
| `nuovo_calibrazione.json` | l'**audit di calibrazione** su 28 mercati × 3 leghe: bias, ECE, ECE nullo, il path DC e i controlli di sanità | `scripts/nuovo_calibrazione.py` |
| `verifica_blocco_precedente.json` | il verbale della **verifica avversariale** delle cinque analisi del primo giro (θ, φ, Shin, ricalibrazioni, stima O/U), con `tabella_verdetti`, `correzioni_proposte_ai_report` e il commit git su cui è stata fatta | sorgente non versionata (l'esito è riassunto al §15 del report 10) |

### Report 11 · il GG/NG contro le quote vere ([`11_ggng.md`](../11_ggng.md))

| file | cosa contiene | prodotto da |
|---|---|---|
| `ggng_contro_quote.json` | tutto il report: `lucchetti` del join, `D1` (il mercato è informativo?), `D2` (i nostri sei predittori contro il book), `D2bis` encompassing, `D2ter`/`D2quater` lo scarto appaiato e il livello, `D3` le leve sui due fronti, `D4` ROI, soglia di risoluzione e molteplicità | `scripts/ggng_contro_quote.py` |

---

## ⚠️ Congelati al momento del report — non "correggerli" ri-eseguendo

Due artefatti **non riproducono più** i loro numeri se si ri-esegue lo script
oggi. In nessuno dei due casi si tratta di un errore, e in entrambi la versione
da tenere è quella committata (verificato all'audit della Fase 101).

**`eda_5_leghe.json`** — tre valori Bundesliga cambiano ri-eseguendo
`scripts/eda_nuove_leghe.py`:

| valore | artefatto | ri-eseguendo oggi |
|---|--:|--:|
| `gamma` | 0.216 | 0.217 |
| `corr(xG,gol)` | 0.644 | 0.645 |
| deficit-pareggio `Q3` | 0.0132 | 0.0146 |

Causa isolata: la correzione **R1 su Union Berlin-Bochum 14/12/2024** (0-2
assegnato dal tribunale → **1-1 sul campo**, `data/correzioni_dichiarate.csv`),
applicata allo snapshot **dopo** la scrittura di `03_nuove_leghe.md`. Verifica:
`ln(gol_casa/gol_ospite)` su `data/bundesliga_matches.csv` vale 0.217 con l'1-1
e 0.216 rimettendo lo 0-2. L'artefatto resta allineato alla tabella di
[`../03_nuove_leghe.md`](../03_nuove_leghe.md) §6.

**`recupero_squad_value_tm.json`** — ri-eseguire
`scripts/recupero_squad_value_tm.py` porta `n` da 13 a 18 club e lo scarto
mediano dal 14,8% all'8,6%. È **circolarità**: le 16 celle recuperate da
Transfermarkt sono state nel frattempo scritte nello snapshot
(`applica_squad_value_tm.py`), quindi il confronto TM↔player-scores finisce per
confrontare Transfermarkt con sé stesso. La misura della scala vale solo nella
versione congelata, fatta **prima** dell'applicazione.

## Cosa manca

- ~~**`caccia_understat.md`**: delle quattro «cacce» è l'unica senza la sua
  lettura per un umano (c'è solo il `.json`).~~ **RISOLTO alla Fase 101-bis**: il
  file esiste ed è versionato — tutte e quattro le cacce hanno la loro lettura
  per un umano. Resta vero che **rigenerarlo** con `scripts/cerca_segnaposto.py`
  richiede i grezzi di `data/fonti/`, oggi non versionati (`.gitignore`): serve
  prima `python scripts/fetch_sources.py`.
- **`tracer_pred_{lega}.csv`** (5 file, 10.735 righe di predizioni walk-forward
  del DC): cancellati con il cantiere senza destinazione, ma cinque script li
  rileggono **da questa cartella** — `tranche3_mercati.py` si ferma con
  `SystemExit` se non li trova. Si rigenerano con
  `python scripts/tranche3_tracer.py`, da eseguire prima di `leve_apertura`,
  `leve_dc_panchina`, `nuovo_calibrazione`, `tranche3_mercati` e
  `tranche3_ritaratura`.
- **Quattro artefatti non hanno uno script in `scripts/`**: `caccia_calendari`,
  `caccia_ou_dataset`, `caccia_quote_singole` (il sorgente sta in appendice al
  `.md` gemello) e `verifica_blocco_precedente` (verifica avversariale eseguita
  una volta, riassunta al §15 del report 10). Sono riproducibili leggendo quelle
  appendici, non lanciando un comando.
