# Protocollo di lavoro — istruzioni per l'AI (e per chiunque contribuisca)

Questo file definisce **come si lavora su questo progetto** e soprattutto **cosa
scrivere/aggiornare ogni volta**. Una sessione AI in questa repo lo legge
all'avvio: seguilo. Lo scopo è che il metodo, i risultati e il ragionamento non si
perdano mai tra una sessione e l'altra, e che tutto resti replicabile da terzi.

Se aggiorni il modo di lavorare, aggiorna **anche questo file**.

---

## 1. Principi metodologici (non negoziabili)

1. **Tracer bullet prima dei moduli** — prima una fetta verticale reale
   end-to-end, poi si raffina.
2. **Una cosa alla volta, e si misura** — cambia un solo fattore per esperimento;
   altrimenti non sai *cosa* ha funzionato.
3. **Testa la versione economica di un'idea prima di investire** — non costruire
   infrastrutture costose su assunzioni non verificate.
4. **Documenta anche i risultati negativi** — valgono quanto quelli positivi.
5. **Riproducibilità** — ogni numero dev'essere rifacibile da terzi (stesso
   codice, stessi dati, stessa config).
6. **Onestà sui limiti** — ci sono soldi veri in gioco: niente promesse di edge,
   sempre le avvertenze quando il modello non batte il mercato.
7. **Valida su più stagioni** — mai concludere da una sola stagione (rumore).
   Default: 3+ stagioni; per conclusioni importanti, 6.

---

## 2. Cosa scrivere OGNI VOLTA (checklist di aggiornamento)

Dopo **ogni backtest / tuning / esperimento significativo**, prima di chiudere:

- [ ] **Registro esperimenti** — verifica che il run sia finito in
  `experiments/runs.jsonl` (backtest.py e tune.py lo fanno in automatico:
  config + metriche + commit git + impronta dati + timestamp). Se hai fatto un
  esperimento "a mano", registralo comunque via `experiment_log.append_run`.
- [ ] **Diario di bordo** (`docs/DIARIO.md`) — se l'esperimento ha prodotto una
  *decisione* o una *scoperta* (non ogni singola run), aggiungi/aggiorna una voce
  con questa struttura:
  1. **obiettivo** della fase;
  2. **ragionamento / ipotesi**;
  3. **alternative** considerate;
  4. **scelta** e perché;
  5. **risultato** (numeri, anche se negativo);
  6. **lezione / cosa ne consegue**.
- [ ] **README** — se è cambiata la **configurazione ufficiale** del modello o un
  risultato chiave, aggiorna le tabelle dei risultati e la roadmap.
- [ ] **Test** — mantieni `pytest` verde; aggiungi un test per ogni nuova
  funzionalità del modello/pipeline.
- [ ] **Commit + push** — messaggio chiaro (cosa e perché), sul branch di
  sviluppo. Non lasciare mai lavoro non committato: il container è effimero.

Regola pratica: **il registro** cattura *ogni* run (dati grezzi); **il diario**
cattura le *decisioni e il perché* (narrazione); il **README** è lo stato
*corrente* sintetico.

---

## 3. Come si esegue (comandi principali)

```bash
python scripts/build_database.py       # (ri)costruisce il DB dallo snapshot (offline)
python scripts/build_database.py --refresh   # riscarica dalle fonti, aggiorna lo snapshot
python scripts/backtest.py             # backtest walk-forward (registra il run)
python scripts/backtest.py --test-season 2425 --shots-blend 0.5   # varianti
python scripts/analyze.py              # analisi errori del backtest
python scripts/tune.py --sweep shrinkage --values 0 1 1.5 3       # tuning iperparametro
python -m pytest                       # test
```

Config "ufficiale" corrente del modello (default in `backtest.py`): **emivita
730g, shrinkage 1.5, shots_blend 0.75, blend_signal xg** (blend gol/xG reale,
Fase 4b). Se la cambi, aggiorna README e diario.

---

## 4. Mappa del repo (dove sta cosa)

```
src/data/        sources.py (URL/stagioni/alias), loader.py (offline-first),
                 database.py (snapshot CSV + SQLite)
src/models/      dixon_coles.py (il modello: _fit_counts, blend, predizione)
src/evaluation/  metrics.py (Brier/log-loss/devig), analysis.py (analisi errori),
                 experiment_log.py (compute_metrics = FONTE DI VERITA' unica; registro)
scripts/         download_data, build_database, backtest, analyze, tune
experiments/     runs.jsonl (registro replicabile) + README (formato)
data/            serie_a_matches.csv (SNAPSHOT congelato, versionato)
                 football.db (SQLite, rigenerabile, NON versionato)
docs/DIARIO.md   narrazione passo-passo con ragionamento
tests/           test unitari
```

---

## 5. Convenzioni sui dati

- **Offline-first**: la pipeline legge lo **snapshot congelato**
  (`data/serie_a_matches.csv`, versionato). Si scarica dalle fonti solo con
  `--refresh`/`force_download`. Così i backtest sono riproducibili identici.
- **Fonte configurabile in un punto solo** (`src/data/sources.py`): URL, stagioni,
  alias dei nomi squadra (`TEAM_ALIASES` — es. "Hellas Verona" → "Verona": bug
  reale già capitato, attenzione ai nomi quando si aggiunge una fonte).
- **Aggiungere una nuova fonte/feature**: normalizza nello schema interno del
  loader, aggiorna lo snapshot/DB, e allinea i nomi squadra/partita tra le fonti
  (join per data + squadre). Fai guidare lo schema dai dati reali, non da ipotesi.
- **Metriche**: calcolale SEMPRE via `experiment_log.compute_metrics` (fonte
  unica), mai reimplementarle altrove.

---

## 6. Stato corrente e prossimi passi

Vedi `docs/DIARIO.md` per la storia completa e `README.md` per lo stato sintetico.
In breve: modello Dixon-Coles sui soli gol, tarato; **batte le baseline ma non il
mercato**; i tiri in porta grezzi non aiutano (verificato su 6 stagioni).
**Fase 4a-4c completate:** dati arricchiti (xG/npxG/PPDA/deep, valori rosa,
assenze); il blend gol/**xG reale** (α=0.75) e' la config ufficiale (primo
miglioramento da dati nuovi, soprattutto O/U). npxG≈xG; valori rosa e assenze
(anche in combo) **non aiutano** out-of-sample (gia' impliciti in gol+xG): il
modello e' al **tetto pratico** dei dati attuali. Esiste un layer covariate
(off di default) per dati futuri davvero indipendenti.
**Prossimo bivio:** modello di classe diversa / dati nuovi, oppure uso pratico
(predizione su partite future).

**Non usare il modello per scommettere soldi veri allo stato attuale.**
