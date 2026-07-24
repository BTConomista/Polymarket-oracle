# `cantiere/` — lavoro isolato: audit dei dati, verifica delle stime, 2 leghe nuove

Cartella **temporanea e autonoma**, creata su richiesta dell'utente (24 luglio
2026) per lavorare **senza toccare nessun file già in uso** dal progetto mentre
su `main` si lavorava in parallelo. Branch: `claude/verify-data-import-leagues-468euv`.

**Policy di isolamento (decisa dall'utente).** Tutto resta qui: nessuna
numerazione di fase, nessuna modifica ai documenti condivisi del progetto
(`DIARIO.md`, `README.md`, `PANCHINA.md`, `DATI.md`, `experiments/runs.jsonl`),
nessuna modifica a `src/`, `data/`, `scripts/`, `tests/`. Così i due filoni di
lavoro non possono entrare in conflitto. Le checklist di integrazione nei report
sono **proposte**, da eseguire solo quando si deciderà di unire i due filoni:
[`report/03_nuove_leghe.md`](report/03_nuove_leghe.md) §7 e
[`report/01_audit_dati.md`](report/01_audit_dati.md) §6.

**Le regole decise durante il lavoro** (da aggiungere alle regole generali del
progetto quando si integrerà) stanno in **[`REGOLE.md`](REGOLE.md)**: dato del
campo e non del tribunale (R1), valore rosa da Transfermarkt dove la fonte
primaria non copre (R2), nessuna modifica a mano ai dati (R3), isolamento (R4),
anomalie sempre dichiarate (R5).

## I tre lavori, e dove leggerne l'esito

| # | lavoro | report | esito in una riga |
|---|---|---|---|
| 1 | **Audit dei dati esistenti** | [`report/01_audit_dati.md`](report/01_audit_dati.md) | i dati **corrispondono alla fonte riga per riga** (0 differenze su gol/date/tiri/quote/xG); trovate **7 anomalie reali**, tutte nella fonte, 2 da correggere |
| 2 | **Stime: ritentare l'import del dato vero, e verificarle** | [`report/02_stime.md`](report/02_stime.md) | dato vero **ancora non procurabile** (4 vie battute, con prove); la stima **regge** a 8 prove di falsificazione; 3 precisazioni da riportare |
| 3 | **Import Bundesliga + Ligue 1** | [`report/03_nuove_leghe.md`](report/03_nuove_leghe.md) | fatti: **2.754 + 3.097 partite**, 38 colonne identiche alle altre leghe, audit superato |
| 4 | **Istruttoria delle decisioni aperte** | [`report/04_decisioni.md`](report/04_decisioni.md) | Union-Bochum: partita **giocata per intero**, 1-1 sul campo, dati completi; valori rosa 2025-26: **recuperati da Transfermarkt** (16 celle) con la scala misurata; re-import del dataset: via **chiusa** (upstream fermo) |

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

→ da riportare in `docs/MANUALE_SOPRAVVIVENZA.md` all'integrazione.

## Contenuto

```
cantiere/
  REGOLE.md         le regole decise durante il lavoro (R1-R5)
  report/           i quattro report (sopra)
  patch/            proposte di modifica al codice di produzione, non applicate
  scripts/
    fetch_sources.py         scarica football-data + Understat (5 leghe x 9 stagioni)
                             registrando URL/SHA256/timestamp in data/fonti/manifest.json
    audit_snapshots.py       audit A/B/C: struttura + confronto con le fonti + fonte indipendente
    audit_anomalie.py        audit avversariale: "e se la fonte fosse sbagliata?"
    verifica_stime.py        8 prove di falsificazione sulla stima O/U 2017-19
    riconcilia_nomi.py       riconciliazione nomi squadra per le leghe nuove
    recupero_squad_value_tm.py  valori rosa da Transfermarkt + validazione della scala
    nuove_leghe.py           config + alias delle 2 leghe nuove (il "sources.py" provvisorio)
    build_new_snapshot.py    costruisce gli snapshot a 38 colonne di Bundesliga e Ligue 1
    eda_nuove_leghe.py       EDA comparativa sulle 5 leghe (passo 1 del playbook)
    applica_correzioni.py    applica le correzioni dichiarate (registro + verifica, R1/R3)
    applica_squad_value_tm.py  riempie le celle vuote di valore rosa (R2)
  data/
    bundesliga_matches.csv       snapshot 38 colonne (2.754 partite)
    ligue_1_matches.csv          snapshot 38 colonne (3.097 partite)
    club_fixtures_*.csv          calendari di club completi
    correzioni_dichiarate.csv    registro delle correzioni (cosa, perche', fonte, stato)
    squad_value_2526_transfermarkt.csv   16 celle recuperate da Transfermarkt (applicate)
    fonti/                       fonti grezze + manifest con SHA256
  out/              output di ogni run (json + log), rigenerabili
```

## Come rifare tutto da zero

```bash
python cantiere/scripts/fetch_sources.py          # fonti (rete) + manifest
python cantiere/scripts/audit_snapshots.py        # audit A/B/C sulle 5 leghe
python cantiere/scripts/audit_anomalie.py         # audit avversariale
python cantiere/scripts/verifica_stime.py         # verifica delle stime
python cantiere/scripts/build_new_snapshot.py     # ricostruisce i 2 snapshot nuovi
python cantiere/scripts/eda_nuove_leghe.py        # EDA 5 leghe
python cantiere/scripts/applica_correzioni.py     # correzioni dichiarate (idempotente)
python cantiere/scripts/applica_squad_value_tm.py # valore rosa dalle celle TM (idempotente)
```

Gli snapshot delle leghe nuove si rigenerano **offline** dalle fonti versionate
in `data/fonti/` (tranne le assenze stimate, che scaricano il mirror
Transfermarkt, ~102 MB in cache non versionata).

## Regole rispettate

- **nessun file esistente del progetto è stato modificato** (né `src/`, né
  `data/`, né `docs/`, né `scripts/`, né `tests/`): tutto vive qui;
- nessun numero inventato: ogni buco resta `NaN` **dichiarato**;
- ogni anomalia trovata è documentata con la prova e l'impatto quantificato,
  anche quando l'esito è "non è un errore" (§1.4 e §1.6 del CLAUDE.md);
- `pytest` resta verde (153 test).
