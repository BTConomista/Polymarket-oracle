# Champions League 2025-26 da due fonti — SofaScore e Opta (WhoScored)

Consegnata il 13/08/2026 in due zip (il secondo era `Eventi_Opta`, troppo grande
per il primo). Completa la famiglia UEFA: era la competizione che mancava.

Metodo identico alle altre raccolte (`files/tre_fonti_serie_a_2526/README.md`):
i file restano **come consegnati**, le riparazioni vivono in
`src/data/tre_fonti.py` e si applicano **in lettura**.

```python
from src.data import tre_fonti as tf
tf.squadre("uefa_champions_league", periodo="Totale")   # 562 squadra-partita
tf.giocatori("uefa_champions_league")                   # 16.720
tf.eventi_opta("uefa_champions_league")                 # 294.667
tf.heatmap("uefa_champions_league")                     # 346.769
```

| blocco | righe | colonne |
|---|---:|---:|
| `squadre` | 1.594 | 183 |
| `giocatori` | 16.720 | 176 |
| `eventi` | 66.514 | 45 |
| `eventi_opta` | 294.667 | 34 |
| `heatmap` | 346.769 | 18 |
| `legenda` | 499 | 5 |

**281 partite, 82 squadre**, dal 1° turno preliminare alla finale. Delle 82,
**23 sono nostre** (dei cinque campionati): è la competizione UEFA che ne porta
di più — 11 in Europa League, 5 in Conference.

**Due fonti, non tre.** Understat non copre le coppe europee, come già per
Europa League. `tf.fonti()` lo dichiara.

## ⭐ Il punteggio è PULITO — e non è un dettaglio ovvio

Questa è la scoperta della consegna, e ha fatto trovare un difetto altrove.

In Europa League e Conference `Gol casa (SofaScore)` **somma la lotteria dei
rigori**: «Partizan-AEK Larnaca 7-7» era 2-1. Qui **no**: sulle 4 partite decise
ai rigori — compresa la finale PSG-Arsenal 1-1 (4-3 dal dischetto) — il
punteggio è già quello della partita, e la serie finale sta nella sua colonna.

Verificato due volte, non assunto:

| prova | esito |
|---|---|
| gol contati uno per uno negli **eventi** | `Gol` grezzo = eventi su **8/8** squadra-partita ai rigori, e **554/554** senza |
| identità dei tempi `Gol = 1T + 2T + suppl.` | **281/281**, coi supplementari veri dentro (5 partite con gol nei supplementari) |

⚠️ **La convenzione non si eredita fra raccolte della stessa famiglia.** Non si
deduce dal torneo (sono tutte UEFA), né dalla fonte (è sempre SofaScore), né
dalla presenza dei rigori (ci sono ovunque). Va **misurata su ogni consegna**:
`python scripts/_run_punteggio_coppe.py`. `tf.RIGORI_NEL_PUNTEGGIO` tiene il
verdetto per raccolta, e `punteggio_vero()` fa la cosa giusta in entrambi i casi
— sottrarre i rigori **qui** darebbe 1 − 4 = **−3** sulla finale.

## I supplementari esistono, e cambiano il tripwire

A differenza delle supercoppe, qui i tempi supplementari si sono giocati, e la
raccolta li tiene in **tre colonne** (`Casa suppl.`, `Casa 1° suppl.`,
`Casa 2° suppl.`). L'identità da usare è quindi `Gol = 1T + 2T + suppl.`, non
`Gol = 1T + 2T`: quest'ultima regge su 276/281 e le 5 eccezioni sono gol veri
dei supplementari, non un difetto.

## I turni sono 17, e comprendono le qualificazioni

`1°/2°/3° turno preliminare`, `Spareggi di qualificazione`, `Giornata 1-8` (la
fase campionato del nuovo formato), `Spareggi ottavi`, `Ottavi`, `Quarti`,
`Semifinali`, `Finale`. `E_CAMPIONATO` è **False**: trattarla da campionato
butterebbe via tutto ciò che non è «Giornata N», cioè metà del torneo.

## Nessun alias nuovo

Le 82 squadre agganciano senza aggiungere niente a `TEAM_ALIASES`.

⚠️ Ma `eventi_opta` va comunque misurato a parte prima di dichiararlo
agganciato: nelle raccolte in cui esiste, la colonna `Squadra` usa forme corte
che le altre colonne dello stesso file non usano (Liga «Atletico», Bundesliga
«RBL», Supercoppa UEFA «PSG»/«Tottenham»). L'aggancio **per partita** resta
perfetto anche quando quello per squadra-partita è rotto, quindi un controllo
per partita non lo rivela.
