# Esperimento Mondiali — MAI INIZIATO (bassa priorità)

> **Stato dichiarato al 2026-07-28: lavoro MAI INIZIATO.**
> Questa cartella contiene **solo questo README** — nessun codice, nessun dato,
> nessun modello, nessun run in `experiments/runs.jsonl`, nessuna riga nel
> registro dei risultati del `README.md` di radice. Non c'è nulla di parziale
> da riprendere: chi volesse provarci partirebbe da zero.
> Il README esiste dal **2026-07-23** (Fase 86) e da allora è stato solo
> ri-allineato ai cambi di perimetro del progetto principale, mai riempito.

Cartella riservata a un eventuale esperimento **parallelo e a bassa fiducia**
sui Mondiali, tenuto **separato** dal progetto principale (Football Oracle:
Serie A, Premier League, La Liga, Bundesliga e Ligue 1 — 5 leghe, 9 stagioni
ciascuna, 16.111 partite).

## Perché è un esperimento separato, non il progetto serio

Le nazionali giocano poche partite tra loro, con formazioni variabili e sedi
neutre: poco storico specifico e molto rumore. Le quote di un Mondiale sono tra le
più efficienti in assoluto. E con poche partite residue il campione è troppo
piccolo per distinguere merito da fortuna.

C'è anche un motivo che viene dal progetto principale, e che è **misurato**: su
5 campionati e 9 stagioni il tetto si è rivelato **informativo**, non
architetturale — il mercato di chiusura **ingloba** il modello (α\*=0, Fase 16) e
nessuna leva si è replicata fuori dalla Serie A (Fase 53). Se non si batte il
mercato dove abbiamo 16.111 partite di storia omogenea, non c'è ragione di
aspettarselo dove le partite sono poche e le quote più efficienti.

## Regola d'ingaggio, se un giorno si parte

- **Modello giocattolo** (es. Elo sulle nazionali) con **aspettative basse**.
  Nessun trasferimento acritico degli iperparametri per-lega di
  `src/config.py`: sono tarati su campionati di club, e il principio §7 del
  `CLAUDE.md` vale a maggior ragione qui (formule universali, numeri no).
- Eventuali scommesse vanno trattate come intrattenimento con denaro che si è
  disposti a perdere — **non** come test della bontà del motore. Vale comunque
  l'avvertenza generale del progetto: **non usare il modello per scommettere
  soldi veri allo stato attuale.**
- Prima di scrivere una riga di codice: aprire una voce in `docs/PISTE.md` con
  il costo stimato e il criterio go/no-go, come per ogni altra pista.

_Se questa cartella è ancora vuota alla prossima lettura, è perché la risposta
è sempre stata «non ne vale la pena»: è un esito, non una dimenticanza._
