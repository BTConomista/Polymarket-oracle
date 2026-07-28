# Audit delle 5 leghe — i report integrali

Questi undici report sono il **verbale esteso** del lavoro riassunto nella voce
di diario «Cinque leghe» (`docs/DIARIO.md`): audit riga-per-riga dei dati contro
la fonte-madre, caccia ai dati coperti da stime, import di Bundesliga e Ligue 1,
valutazione della rosa dei modelli sulle due leghe nuove, e la verifica
avversariale che ha smontato cinque affermazioni — tre delle quali nostre.

Sono conservati perché contengono i **numeri e le prove** che il diario riassume:
chi vuole rifare un conto o contestare una conclusione parte da qui. I file citati
nei report come `cantiere/...` vivono ora nella struttura del progetto:

| dove era (cartella `cantiere/`, cancellata) | dove è ora |
|---|---|
| `cantiere/report/*.md` | `docs/audit_5_leghe/*.md` (questi) |
| `cantiere/REGOLE.md` | `docs/audit_5_leghe/REGOLE.md` — promosse a **§5-bis del `CLAUDE.md`**. ⚠️ **alla promozione la numerazione è cambiata** (vedi il riquadro qui sotto) |
| `cantiere/out/*.json` | `docs/audit_5_leghe/numeri/` (i numeri grezzi dietro le tabelle) |
| `cantiere/scripts/*.py` | `scripts/` (32 file; i percorsi interni sono stati riparati alla **Fase 101**: fino ad allora nessuno partiva) |
| `cantiere/data/{bundesliga,ligue_1}_matches.csv` | `data/` (snapshot di produzione) |
| `cantiere/data/ricerca/` | `data/ricerca_esterna/` |
| `cantiere/data/correzioni_dichiarate.csv` | `data/correzioni_dichiarate.csv` |
| `cantiere/data/stime/` | `data/estimates/` |
| `cantiere/data/fonti/` | **rimossi** (135 MB, ri-scaricabili con `python scripts/fetch_sources.py`, che oggi li rimette in `data/fonti/`, non versionata). Il manifest `data/ricerca_esterna/manifest_fonti_audit.json` ha **90 voci** (45 `.csv` football-data + 45 `.json` Understat-lega, tutte e 5 le leghe), ma solo **36 dei 141 file cancellati** hanno la loro impronta SHA256: i 18 CSV football-data e i 18 JSON Understat-lega delle due leghe nuove, cioè quelli su cui poggiano i controlli B/C dell'audit (le altre 54 voci del manifest sono le tre leghe storiche, i cui grezzi qui non erano versionati). **NON** coperti **105** file: gli 84 `.txt` openfootball (calendari coppe/Europa), i 16 `.html` Transfermarkt e 5 `.json` (i 4 `understat_match` — il tiro-per-tiro che è la prova del caso di **R5 vigente**, `CLAUDE.md` §5-bis, «procedura per una riga che sembra corrotta», *ex* R6 del cantiere — più il `manifest.json` interno), che vanno ri-raccolti a parte. Attenzione: le chiavi del manifest archiviato sono nella forma `cantiere/data/fonti/…`, mentre `scripts/fetch_sources.py` oggi scrive `data/fonti/…` — per confrontare le impronte va tolto il prefisso `cantiere/` |

**Attenzione leggendoli:** i report 09 e 10 contengono conclusioni poi
**ritirate** dalla verifica avversariale (§15 del report 10). Le ritirate sono
segnalate dentro i report stessi; in caso di conflitto fa fede il `CLAUDE.md` e
il diario, non questi file.

> ⚠️ **Le sigle delle regole (`R1`…`R7`) hanno DUE numerazioni.** Quella
> **vigente** è `CLAUDE.md` §5-bis; quella **storica del cantiere** è ancora
> citata dai docstring dei 32 script migrati. Le due divergono da R4 in poi:
> cantiere R4 = *isolamento* (decaduta), cantiere R5 = vigente **R4**, cantiere
> R6 = vigente **R5**; le vigenti **R6** (*il finto pieno*) e **R7** (*ogni
> statistica vuole il suo intervallo*) sono nate dopo il cantiere. La tabella di
> corrispondenza completa, con l'elenco di quali script citano quale sigla, è in
> testa a [`REGOLE.md`](REGOLE.md).

---

## I lavori, e dove leggerne l'esito

| # | lavoro | report | esito in una riga |
|---|---|---|---|
| 1 | **Audit dei dati esistenti** | [`01_audit_dati.md`](01_audit_dati.md) | i dati **corrispondono alla fonte riga per riga** (0 differenze su gol/date/tiri/quote/xG); trovate **7 anomalie reali** (6 nella fonte + 1 nostra); un ottavo caso ritirato come falso positivo |
| 2 | **Stime: ritentare l'import del dato vero, e verificarle** | [`02_stime.md`](02_stime.md) | dato vero **ancora non procurabile** (4 vie battute, con prove); la stima **regge** a 8 prove di falsificazione; 3 precisazioni da riportare |
| 3 | **Import Bundesliga + Ligue 1** | [`03_nuove_leghe.md`](03_nuove_leghe.md) | fatti: **2.754 + 3.097 partite**, 38 colonne identiche alle altre leghe, audit superato |
| 4 | **Istruttoria delle decisioni aperte** | [`04_decisioni.md`](04_decisioni.md) | Union-Bochum: partita **giocata per intero**, 1-1 sul campo, dati completi; valori rosa 2025-26: **recuperati da Transfermarkt** (16 celle) con la scala misurata; re-import del dataset: via **chiusa** (upstream fermo) |

| 5 | **Tranche 1 — correzioni dati** | [`05_tranche1.md`](05_tranche1.md) | 8 linee O/U impossibili e 1 xG impossibile a NaN dichiarato; audit avversariale a **0 anomalie** sulle leghe nuove |
| 6 | **Tranche 3 — il playbook sulle leghe nuove** | [`06_tranche3.md`](06_tranche3.md) | il DC batte la baseline e non il mercato (gap +0.018/+0.019, dentro l'attesa); il market-implied batte il DC su **15/15** mercati; curve di taratura **piatte**; φ35 non conclusiva in nessuna lega |

| 7 | **Righe corrotte: recupero, ritiro di un errore, stima** | [`07_dati_corrotti.md`](07_dati_corrotti.md) | una mia «correzione» era un **falso positivo** (autogol) ed è stata ritirata; le 8 quote non sono recuperabili da nessuna fonte lecita → **stimate** con MAE 0.0267 contro 0.0743 di baseline. ⚠️ **stima poi SUPERATA dal lavoro 9** (M5g, MAE 0.0143): lo 0.0267 vale come misura interna a questo report, non come errore corrente |
| 8 | **I buchi: quanti, dove, come si chiudono** | [`08_buchi.md`](08_buchi.md) | 7.353 celle vuote su 612.218 (1.20%), ma il **99.3% è un buco solo** (O/U chiusura 2017-19, assente alla fonte per tutte e 5 le leghe); tolto quello restano **49 celle**, ognuna con nome e causa. Trovato e chiuso un buco **travestito da dato** (xG segnaposto) |
| 9 | **Chiudere i buchi: dato vero + stime** | [`09_chiusura_buchi.md`](09_chiusura_buchi.md) | **1.362 partite stimate** (chiusura O/U delle 2 leghe nuove); **trovato il dato REALE** della chiusura O/U 2017-19 su 3.652 partite (1xBet) — ma NON batte la stima e non va inserito; **quote GG/NG reali** per 3.652 partite, mercato che il progetto dichiarava senza quote; **3.045 righe di calendario coppe** recuperate. Secondo giro: le 9 linee O/U corrotte **ristimate** (MAE 0.0267 → 0.0143), il tiro in porta **ricostruibile all'86,4%** da Understat, 2 celle chiuse con dato vero e 2 lasciate `NaN` con la prova — e il buco più grande rimasto **non è un `NaN`**: 1.603 falsi zero di `midweek_europe`. Lo stimatore O/U **resta pooled**: il ribaltamento per-lega non regge nel regime d'uso |
| 10 | **La rosa dei modelli sulle 2 leghe nuove** | [`10_modelli_nuove_leghe.md`](10_modelli_nuove_leghe.md) | **10 fronti**. Nessuna leva del mercato si replica: router θ **negativo** (0/25 su chiusura *e* apertura), φ35 e power-devig **bocciati**, Shin non regge a cluster, beat-the-close **chiuso** (ROI −22% e −13%), mercato campione battuto da «vince il Bayern/PSG». Il motore invece **funziona anche dall'apertura** (25/25 sul DC). La verifica avversariale ha smontato **2 analisi su 5** del primo giro e 3 dei fronti nuovi: il segnale GG/NG in Bundesliga è **non dimostrato**, il «fronte generale» è **non deciso**, la calibrazione ha un difetto di **forma** che era stato dichiarato assente (§15) |
| 11 | **Il GG/NG contro le quote vere** | [`11_ggng.md`](11_ggng.md) | cade una premessa del progetto: le quote GG/NG **ora esistono** (5 leghe × 3 stagioni, 5.337 partite). Il mercato **è informativo** ma vale 1/3 dell'O/U 2.5 dello stesso book e costa 1,7 pt di margine in più; il nostro market-implied lo **pareggia** (Δ nel rumore in 6 varianti su 6) e il **DC perde di netto** (+0.0104, il book lo ingloba: α\* = 0 nel 70% dei fit). Nessuna leva aiuta su nessuno dei due fronti. Lo «spazio» che `CLAUDE.md` §1.8 attribuiva al GG/NG **era la nostra ignoranza** |

## Il fatto nuovo che ha cambiato le regole

`docs/MANUALE_SOPRAVVIVENZA.md` §1 dà `football-data.co.uk` e `understat.com`
per **bloccati** (403). **Oggi rispondono 200.** Sono raggiungibili anche
`data.jsdelivr.com`, `betexplorer.com`, `oddsportal.com`, **`transfermarkt.com`**
(era il motivo del recupero manuale via browser esterno) e **Kaggle via
`kagglehub`** (prima serviva il runner Actions). Conseguenze:

- si è potuto **verificare gli snapshot contro la fonte-madre**, non solo
  contro se stessi (il controllo forte, mai fatto prima);
- le leghe nuove **non hanno avuto bisogno di bundle caricati a mano**;
- Understat ha cambiato struttura: i dati stanno dietro
  `GET /getLeagueData/{Lega}/{anno}` con header `X-Requested-With: XMLHttpRequest`
  (senza header → 404). Lo schema JSON è quello che il parser esistente già legge.

→ riportato in `docs/MANUALE_SOPRAVVIVENZA.md` all'integrazione (commit 46bf0fc).

> Questo paragrafo racconta il **fatto nuovo del momento**, non lo stato di oggi.
> Per lo **stato corrente** della rete fa fede `docs/MANUALE_SOPRAVVIVENZA.md`
> §1, che è più aggiornato: si è aggiunta `footiqo.com` (le quote di chiusura
> 1xBet, vedi il lavoro 9) e altri host sono stati ri-verificati da allora.

## Contenuto

> Questo albero è la **struttura originale del cantiere**, tenuta perché i
> report la citano; per la posizione odierna di ogni cosa vale la tabella di
> corrispondenza in testa a questo file.

```
cantiere/
  REGOLE.md         le regole decise durante il lavoro (allora R1-R6; oggi
                    R1-R7 nella numerazione vigente di CLAUDE.md §5-bis,
                    con la R4-isolamento decaduta: vedi il riquadro sopra)
  report/           gli undici report (sopra)
  patch/            proposte di modifica al codice di produzione (poi applicate)
  scripts/          32 script, oggi tutti in `scripts/`. Per prefisso:
                    applica_* (correzioni R1/R3, valore rosa R2)
                    audit_*   (snapshot A/B/C; avversariale)
                    build_new_snapshot, cerca_segnaposto, eda_nuove_leghe,
                    fetch_sources, ggng_contro_quote, riconcilia_nomi,
                    recupero_squad_value_tm, nuove_leghe, verifica_stime
                    leve_*    (apertura, beat_close, dc_panchina, devig_shin,
                               phi_griglia, ricalibrazioni, theta_griglia)
                    nuovo_*   (calibrazione, fronte_generale, mercato_campione)
                    stima_*   (celle_residue, ou_close_nuove, ou_corrotte,
                               ou_open_bakeoff, sot_understat)
                    tranche3_* (tracer, market_tracer, ritaratura, mercati)
  data/
    bundesliga_matches.csv       snapshot 38 colonne (2.754 partite)
    ligue_1_matches.csv          snapshot 38 colonne (3.097 partite)
    club_fixtures_*.csv          calendari di club completi
    correzioni_dichiarate.csv    registro delle correzioni (cosa, perche', fonte, stato)
    squad_value_2526_transfermarkt.csv   16 celle recuperate da Transfermarkt (applicate)
    estimates/ou_open_corrotte_2017_19.csv   P(Over) di apertura stimate (MAE 0.0143,
                                 probabilita', FUORI dagli snapshot): 9 righe alla
                                 prima pubblicazione, **12 oggi** (verificato: 7
                                 bundesliga + 3 la_liga + 2 ligue_1) dopo il secondo
                                 giro del lavoro 9. Il file del cantiere si chiamava
                                 stime_ou_corrotte.csv e aveva 8 righe: soppresso,
                                 sostituito da questo. Il diagnostico storico
                                 (metodo M1, MAE 0.0267) scrive oggi in
                                 docs/audit_5_leghe/numeri/stima_ou_corrotte_metodo_storico.csv
    fonti/                       fonti grezze + manifest con SHA256 (oggi RIMOSSE)
  out/              output di ogni run, oggi `docs/audit_5_leghe/numeri/`
                    (39 artefatti versionati e rigenerabili: 34 .json, 4 .md,
                     1 .csv, oltre al README della cartella; due di essi NON
                     riproducono più — vedi quel README per il perché)
```

⚠️ **Cinque artefatti NON sono versionati**: i `tracer_pred_{lega}.csv` (10.735
righe di predizioni walk-forward del DC) sono stati cancellati con il cantiere
senza destinazione, ma cinque script li rileggono da
`docs/audit_5_leghe/numeri/` — `tranche3_mercati.py` si ferma con `SystemExit`
se non li trova. Vanno rigenerati con `python scripts/tranche3_tracer.py`
**prima** di `leve_apertura`, `leve_dc_panchina`, `nuovo_calibrazione`,
`tranche3_mercati` e `tranche3_ritaratura`.

> ⚠️ ~~**`caccia_understat.md` non esiste**: delle quattro «cacce» è l'unica
> senza la sua lettura per un umano (c'è solo `caccia_understat.json`).~~
> **RISOLTO alla Fase 101-bis** (commit `b87368f`): il file
> `docs/audit_5_leghe/numeri/caccia_understat.md` esiste ed è versionato — tutte
> e quattro le cacce hanno ora la loro lettura per un umano. Resta vero che
> ri-eseguire `scripts/cerca_segnaposto.py` per rigenerarlo richiede i grezzi di
> `data/fonti/`, oggi non versionati (serve prima `python scripts/fetch_sources.py`).

## Come rifare tutto da zero

```bash
python scripts/fetch_sources.py          # fonti (rete) + manifest
python scripts/audit_snapshots.py        # audit A/B/C sulle 5 leghe
python scripts/audit_anomalie.py         # audit avversariale
python scripts/verifica_stime.py         # verifica delle stime
python scripts/build_new_snapshot.py     # ricostruisce i 2 snapshot nuovi
python scripts/eda_nuove_leghe.py        # EDA 5 leghe
python scripts/tranche3_tracer.py        # rigenera i 5 tracer_pred_*.csv in
                                         # docs/audit_5_leghe/numeri/ (10.735 righe di
                                         # predizioni walk-forward, NON versionate):
                                         # sono l'input di leve_apertura, leve_dc_panchina,
                                         # nuovo_calibrazione, tranche3_mercati e
                                         # tranche3_ritaratura
python scripts/applica_correzioni.py     # correzioni dichiarate (idempotente)
python scripts/applica_squad_value_tm.py # valore rosa dalle celle TM (idempotente)
```

⚠️ **Il passo 1 non è opzionale** (rettifica della Fase 101). Le fonti grezze
**non sono più versionate**: sono state rimosse all'integrazione perché
ri-scaricabili, quindi `fetch_sources.py` (che richiede rete) va eseguito per
primo e ripopola `data/fonti/`. La frase originale — «gli snapshot delle leghe
nuove si rigenerano offline dalle fonti versionate in `cantiere/data/fonti/`» —
era vera nel cantiere e non lo è più qui. Restano fuori dal manifest gli 84
`.txt` openfootball e i 16 `.html` Transfermarkt (vedi la tabella in testa); le
assenze stimate scaricano a parte il mirror Transfermarkt (~102 MB, cache non
versionata).

## Regole rispettate

- **al tempo del cantiere** nessun file esistente del progetto era stato
  modificato (né `src/`, né `data/`, né `docs/`, né `scripts/`, né `tests/`):
  tutto viveva qui. ⚠️ **Premessa decaduta all'integrazione** (`03d5bec` →
  `6c9b377`), che ha toccato tutte e cinque le cartelle, e poi alla Fase 101
  (`bb6ebe4`), che ha riparato i 32 script migrati;
- nessun numero inventato: ogni buco resta `NaN` **dichiarato**;
- ogni anomalia trovata è documentata con la prova e l'impatto quantificato,
  anche quando l'esito è "non è un errore" (§1.4 e §1.6 del CLAUDE.md);
- **`pytest` è sempre restato verde.** Il conteggio, però, è cresciuto molto: va
  letto come una cronologia, non come un numero unico.

  | quando | test verdi | nota |
  |---|--:|---|
  | chiusura del **cantiere** | **153** | ⚠️ **numero STORICO**, dichiarato allora, non ri-misurato qui |
  | fine **Fase 101** (commit `174f78c`) | **197** | ⚠️ numero STORICO, dichiarato allora. `docs/AUDIT_FASI_80_100.md` riporta **194** per la stessa epoca: la divergenza non è stata sciolta (servirebbe un checkout di quel commit) |
  | **oggi** (27 luglio 2026, Fase 101-ter) | **841** | ✅ **ri-misurato in questa sessione**: `python -m pytest -q` → `841 passed` |

  L'impennata non misura il lavoro svolto: i due file di test aggiunti dalla
  seconda passata sono **parametrizzati sui 159 script** di `scripts/`, quindi
  il totale è un numero di *casi*, non di controlli concettuali.
