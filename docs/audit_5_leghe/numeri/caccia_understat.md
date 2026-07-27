# Caccia ai segnaposto di Understat (5 leghe x 9 stagioni)

Generato da `scripts/cerca_segnaposto.py` il 2026-07-25T20:13:24+00:00 (UTC). Parametri: `{"offline": true, "campione": 120, "coda": 60, "potere": 500, "seed": 20260725}`.

**La domanda.** Un buco (NaN) si vede. Un dato *finto* no: quando la fonte non acquisisce una partita non lascia il campo vuoto, ci scrive un valore di comodo. Nessun confronto snapshot-vs-fonte lo scopre. Qui si cercano quei valori, su tutte e cinque le leghe.

**Aspettativa dichiarata prima di guardare i numeri.** (1) sui due casi puntuali: nessun recupero, perche' una fonte che non ha acquisito una partita raramente torna indietro mesi dopo; (2) sulla caccia generale: da 1 a 5 nuovi segnaposto, sull'idea che 1 su 16.000 sia una stima per difetto. Esito sotto, confrontato voce per voce.


## La batteria di test (gratis, su tutte le 16.110 partite giocate)

Ogni test ha un tasso di falsi positivi **misurato**, non assunto.

| test | cosa guarda | positivi | tasso |
|---|---|--:|--:|
| `A1_xg_uguale_gol` | xG identico ai gol su entrambi i lati | 1 / 16110 | 0.006207% |
| `A2_cifre_povere` | xG e npxG con <=3 cifre significative (tutti e 4) | 1 / 16110 | 0.006207% |
| `A3_forecast_degenere` | previsione della fonte degenere (0/1 esatti) | 1 / 16110 | 0.006207% |
| `A4_ppda_nulla` | PPDA con att=0 o def=0 (flusso eventi vuoto) | 1 / 16110 | 0.006207% |
| `A5_deep_zero` | deep=0 su entrambe le squadre (il filtro di partenza) | 4 / 16110 | 0.024829% |
| `A6_xpts_intero` | xpts intero esatto (0/1/3) | 1 / 16110 | 0.006207% |
| `A7_rigore_finto` | xG-npxG multiplo esatto di 0.75 (rigore di comodo) | 1 / 16110 | 0.006207% |
| `A8_history_mancante` | partita giocata senza history per-squadra | 0 / 16110 | 0.000000% |
| `A9_xg_zero_con_tiri` | xG=0 mentre football-data conta dei tiri | 1 / 16110 | 0.006207% |

Candidati con almeno un flag: **5**.

- `bundesliga 2021` **Bielefeld-Leverkusen** (2020-11-21), gol 1-2, xG [0.0, 1.32693], deep [1.0, 7.0], tiri football-data [1.0, 10.0] -> flag: A9_xg_zero_con_tiri
- `bundesliga 2425` **Holstein Kiel-Bochum** (2025-02-09), gol 2-2, xG [2.0, 2.0], deep [0.0, 0.0], tiri football-data [10.0, 21.0] -> flag: A1_xg_uguale_gol, A2_cifre_povere, A3_forecast_degenere, A4_ppda_nulla, A5_deep_zero, A6_xpts_intero, A7_rigore_finto
- `ligue_1 2021` **Reims-Lille** (2020-08-30), gol 0-1, xG [0.206627, 0.906784], deep [0.0, 0.0], tiri football-data [4.0, 10.0] -> flag: A5_deep_zero
- `premier_league 1718` **West Brom-West Ham** (2017-09-16), gol 0-0, xG [0.781891, 0.266344], deep [0.0, 0.0], tiri football-data [6.0, 9.0] -> flag: A5_deep_zero
- `premier_league 1718` **West Ham-Swansea** (2017-09-30), gol 1-0, xG [0.692185, 0.178568], deep [0.0, 0.0], tiri football-data [9.0, 6.0] -> flag: A5_deep_zero

## Quanto vale la batteria (simulazione di potere)

Un test con zero falsi positivi puo' avere anche zero potere. Si piantano buchi finti su 500 partite vere e si conta quanti ne ripesca.

- **Segnaposto totale** (la regola esatta della fonte): riscoperti **100.0%**, CI95 bootstrap [1.0, 1.0]. Per singolo test: `A1_xg_uguale_gol` 100%, `A2_cifre_povere` 57%, `A3_forecast_degenere` 100%, `A4_ppda_nulla` 100%, `A5_deep_zero` 100%, `A6_xpts_intero` 100%, `A7_rigore_finto` 0%, `A8_history_mancante` 0%, `A9_xg_zero_con_tiri` 43%.
- **Troncamento parziale** (il feed perde una parte dei tiri; l'xG resta plausibile ma scende). Soglia sulla coda z = -1.899 (budget ~32 falsi allarmi su 32.218 lati):

| xG residuo dopo il troncamento | riscoperti | CI95 |
|---|--:|---|
| 0.9 | 0.2% | [0.0, 0.006] |
| 0.75 | 1.0% | [0.002, 0.02] |
| 0.5 | 6.8% | [0.048, 0.09] |
| 0.25 | 28.4% | [0.244, 0.324] |
| 0 | 100.0% | [1.0, 1.0] |

**Lettura onesta:** la batteria e' *cieca* ai troncamenti parziali. Vede benissimo il guasto totale (100%) e quasi niente sotto: e' il limite strutturale del metodo, non un dettaglio.

## Sottoprodotto: riconciliazione stagionale dei tiri

Somma dei tiri stagionali dei giocatori (Understat) contro somma dei tiri di football-data: due contatori indipendenti della stessa cosa.

Rumore di fondo su 41 lega-stagioni sane: |scarto| mediano 0.14%, p95 0.7%. Fuori scala:

| lega | stagione | tiri football-data | tiri Understat | scarto |
|---|---|--:|--:|--:|
| serie_a | 1819 | 7759 | 10556 | +36.05% |
| serie_a | 1920 | 8036 | 10866 | +35.22% |
| serie_a | 2021 | 8323 | 9486 | +13.97% |
| bundesliga | 2324 | 8317 | 8481 | +1.97% |

**Attenzione: qui il sospettato e' football-data, non Understat.** In Serie A 2018-19/2019-20/2020-21 football-data conta ~20-22 tiri a partita contro ~25.5 nelle stagioni contigue, e l'xG-per-tiro che ne risulta sale a 0.135-0.141 contro ~0.11 di tutte le altre lega-stagioni. Non e' il calcio che cambia: e' il contatore. Riguarda le colonne `home_sot`/`away_sot` degli snapshot, non l'xG. **Non e' una conclusione**: e' una pista che merita una verifica dedicata con una terza fonte.

## Limiti (dichiarati)

- La batteria e' cieca ai **troncamenti parziali** (vedi la curva di potere): un feed che perde meta' dei tiri viene ripreso nel ~7% dei casi.
- Il verdetto tiro-per-tiro copre un campione, non le 16.110 partite (sarebbero ~6h30 di download a 1.5s): la prevalenza dei buchi invisibili e' **limitata dall'alto**, non azzerata.
- I test sono tarati sulla regola di ripiego OSSERVATA in un solo caso (27930). Se la fonte ne usasse un'altra in epoche diverse, la batteria potrebbe non vederla; i test A2/A3/A4/A6 sono pero' generici (degenerazione di un contatore) e non dipendono dalla regola specifica.
- La fonte puo' cambiare: i numeri qui valgono alla data del run, e ogni payload scaricato e' registrato con lo `sha256` nel JSON di uscita.
