# ⚠️ `data/estimates/` — STIME di modello, NON dati di mercato

Questa cartella contiene **stime prodotte dai nostri modelli** per dati che le
fonti **non hanno**. Sono deliberatamente tenute **fuori dagli snapshot**
(`data/*_matches.csv`) e pubblicate come **probabilità** (mai come quote, così
è impossibile scambiarle per prezzi di un bookmaker).

## Regole d'uso (non negoziabili)

1. **Non farci troppo affidamento.** Sono ricostruzioni statistiche con un
   errore atteso misurato e dichiarato — utili come *benchmark di analisi*,
   NON come verità di mercato.
2. **Ogni analisi che le usa deve dichiararlo** esplicitamente (nel diario e
   nel registro `runs.jsonl`).
3. **Mai** copiarle dentro le colonne quota degli snapshot, né usarle per
   simulare scommesse/ROI (non esiste una quota reale a cui "scommettere").
4. Ogni file è **rigenerabile** con `python scripts/build_estimates.py` e ha
   la sua provenienza registrata in `experiments/runs.jsonl`.

## Contenuto

### `ou_close_2017_19.csv` — chiusura O/U 2.5 stimata, stagioni 2017-18 / 2018-19

**Perché.** In quelle 2 stagioni (Serie A, Premier League, La Liga)
football-data pubblica **una sola linea O/U** (media pre-match): la chiusura
O/U non esiste nei dati, mentre l'1X2 ha sia apertura sia chiusura (Pinnacle,
Fase 61). Il file colma il buco con una stima.

**Come (Fasi 62/62-bis).** Regressione in spazio logit della chiusura O/U su
(linea O/U pre-match + movimento 1X2 apertura→chiusura), fittata pooled su
7.978 partite 2019-20+ dove la chiusura vera esiste. Convalidata walk-forward:

| errore atteso | valore |
|---|---|
| MAE vs chiusura vera (prob.) | **~0.012** |
| correlazione col movimento vero della linea | 0.75–0.86 |
| quota del movimento NON catturabile | ~35-45% (notizie puro-totali, ignote all'1X2) |

**Limiti dichiarati.**
- I coefficienti sono fittati su stagioni **successive** a quelle stimate
  (unico dato possibile): accettabile per un benchmark storico, non per
  predizione.
- Nel 2017-19 le linee input sono Pinnacle/BbAv; il fit usa le medie `Avg`.
- La colonna è `p_over25_close_est` (probabilità devigata stimata);
  `P(Under) = 1 − P(Over)`.

Documentazione completa dei dati e delle stime: **[docs/DATI.md](../../docs/DATI.md)**.
