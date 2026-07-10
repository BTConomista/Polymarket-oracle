# Fase 4e — Calendario di club completo (congestione vera)

Branch: `claude/sports-prediction-engine-7qcqiy`
Repo:   https://github.com/BTConomista/Polymarket-oracle

Non ho potuto pushare da solo (nessuna credenziale in questo ambiente), quindi
trovi qui **patch git + bundle**, come le volte precedenti. Il commit è basato
sul tip attuale del branch (`19828dc`, Fase 5). Verificato end-to-end su un clone
fresco: applica pulito e `pytest` resta verde (42/42), impronta dati invariata.

## Consigliato — patch (`git am`)
È il metodo più robusto: applica il diff sul tip corrente anche se nel frattempo
il branch si è mosso (a meno di conflitti sulle stesse righe, che non ci sono —
tocco file diversi dalle Fasi 4d/5).

```bash
git checkout claude/sports-prediction-engine-7qcqiy
git pull
git am 0001-fase-4e-calendario-club-completo.patch
python -m pytest -q          # atteso: 42 passed
git push
```

## Alternativa — bundle (fast-forward)
Funziona solo se il tip del branch è ancora `19828dc` (se il branch è avanzato,
usa la patch).

```bash
git fetch ./polymarket-oracle-fase4e.bundle claude/sports-prediction-engine-7qcqiy
git checkout claude/sports-prediction-engine-7qcqiy
git merge --ff-only FETCH_HEAD
python -m pytest -q
git push
```

## Cosa contiene il commit
- `src/data/fixtures.py` — fetcher openfootball (mirror GitHub) con cache offline,
  parser Europa/Coppa Italia (gestisce i due formati), assemblaggio del calendario
  di club, `add_rest_days_full` + flag `midweek_europe` (cap 14, no look-ahead).
- `src/data/sources.py` — URL centralizzati openfootball + alias nomi estesi
  (es. `ACF Fiorentina`→`Fiorentina`, `SS Lazio`→`Lazio`).
- `data/club_fixtures.csv` — tabella grezza versionata (7676 righe squadra-partita:
  `season, team, date, competition, home_away, opponent`).
- `data/serie_a_matches.csv` + DB — nuove colonne `home/away_rest_days_full`,
  `home/away_midweek_europe`.
- `scripts/build_database.py` — nuovo step `--fixtures` (e refresh integrato).
- `tests/test_fixtures.py` — 21 test.
- `docs/DIARIO.md` (Fase 4e, copertura per stagione), `README.md`, `CLAUDE.md`.

## Note
- **Offline-first**: lo snapshot resta la fonte congelata; i backtest non
  scaricano nulla. Per rigenerare il calendario: `python scripts/build_database.py --fixtures`.
- **Non-regressione**: impronta dati invariata (`8483944342fc8b15`); il modello
  non legge ancora le colonne (covariate off). Per validare la congestione,
  aggiungi la covariata `rest_full` che legge `*_rest_days_full`.
- **Copertura onesta** (dettagli nel diario): Champions League tutte e 9 le
  stagioni; Europa dal 2020-21; Conference dal 2021-22; Coppa Italia
  2020-21→2024-25. Dove manca, `rest_days_full` degrada verso il valore solo-lega
  — nessun numero inventato.
