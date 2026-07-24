# `cantiere/` — lavoro isolato: audit dei dati, verifica delle stime, 2 leghe nuove

Cartella **temporanea e autonoma**, creata su richiesta dell'utente (24 luglio
2026) per lavorare **senza toccare nessun file già in uso** dal progetto mentre
su `main` si lavorava in parallelo. Branch: `claude/verify-data-import-leagues-468euv`.

Nulla qui dentro è ancora "ufficiale": quando il lavoro verrà accettato, i
contenuti si spostano negli alberi del progetto seguendo la procedura del
`CLAUDE.md` §2 (diario, README, PANCHINA, DATI, runs.jsonl, test) e questa
cartella sparisce. La checklist di integrazione è in
[`report/03_nuove_leghe.md`](report/03_nuove_leghe.md) §7 e in
[`report/01_audit_dati.md`](report/01_audit_dati.md) §6.

## I tre lavori, e dove leggerne l'esito

| # | lavoro | report | esito in una riga |
|---|---|---|---|
| 1 | **Audit dei dati esistenti** | [`report/01_audit_dati.md`](report/01_audit_dati.md) | i dati **corrispondono alla fonte riga per riga** (0 differenze su gol/date/tiri/quote/xG); trovate **7 anomalie reali**, tutte nella fonte, 2 da correggere |
| 2 | **Stime: ritentare l'import del dato vero, e verificarle** | [`report/02_stime.md`](report/02_stime.md) | dato vero **ancora non procurabile** (4 vie battute, con prove); la stima **regge** a 8 prove di falsificazione; 3 precisazioni da riportare |
| 3 | **Import Bundesliga + Ligue 1** | [`report/03_nuove_leghe.md`](report/03_nuove_leghe.md) | fatti: **2.754 + 3.097 partite**, 38 colonne identiche alle altre leghe, audit superato |

## Il fatto nuovo che ha cambiato le regole

`docs/MANUALE_SOPRAVVIVENZA.md` §1 dà `football-data.co.uk` e `understat.com`
per **bloccati** (403). **Oggi rispondono 200.** Anche `data.jsdelivr.com`,
`betexplorer.com`, `oddsportal.com` sono raggiungibili. Conseguenze:

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
  report/           i tre report (sopra)
  patch/            proposte di modifica al codice di produzione, non applicate
  scripts/
    fetch_sources.py         scarica football-data + Understat (5 leghe x 9 stagioni)
                             registrando URL/SHA256/timestamp in data/fonti/manifest.json
    audit_snapshots.py       audit A/B/C: struttura + confronto con le fonti + fonte indipendente
    audit_anomalie.py        audit avversariale: "e se la fonte fosse sbagliata?"
    verifica_stime.py        8 prove di falsificazione sulla stima O/U 2017-19
    riconcilia_nomi.py       riconciliazione nomi squadra per le leghe nuove
    nuove_leghe.py           config + alias delle 2 leghe nuove (il "sources.py" provvisorio)
    build_new_snapshot.py    costruisce gli snapshot a 38 colonne di Bundesliga e Ligue 1
    eda_nuove_leghe.py       EDA comparativa sulle 5 leghe (passo 1 del playbook)
  data/
    bundesliga_matches.csv       snapshot 38 colonne (2.754 partite)
    ligue_1_matches.csv          snapshot 38 colonne (3.097 partite)
    club_fixtures_*.csv          calendari di club completi
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
