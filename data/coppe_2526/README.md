# `data/coppe_2526/` — le coppe nazionali 2025-26

Sei coppe, cinque paesi, **662 partite**. Prodotto da
`scripts/build_coppe_2526.py` (Fase 138). Rigenerabile:

```bash
python scripts/build_coppe_2526.py            # scarica, verifica e riscrive
python scripts/build_coppe_2526.py --verifica # solo i controlli, non scrive
```

## ⚠️ Da leggere prima di usare `partite.csv`

**Il punteggio della fonte non è il punteggio della partita.** In `games.csv`
di player-scores, su **68 partite (14,8%)** il risultato è **sommato ai
rigori**: Braunschweig-Stuttgart risulta `11-12` mentre è finita **4-4** (poi
8-7 ai rigori). Qui il punteggio è stato **ricostruito dagli eventi** e sta in
colonne separate:

| colonna | cosa contiene |
|---|---|
| `gol_casa_90` / `gol_ospite_90` | il punteggio al **90°** |
| `gol_casa_finale` / `gol_ospite_finale` | dopo eventuali **supplementari** ← *usa questa per i gol* |
| `rigori_casa` / `rigori_ospite` | la serie di rigori, **separata** |
| `gol_casa_dichiarato` / `gol_ospite_dichiarato` | il valore **grezzo** della fonte, conservato apposta |
| `eventi_incompleti` | `True` sulle 10 righe dove la ricomposizione non torna |
| `supplementari` | `True` se ci sono gol oltre il 90° |

`*_dichiarato` è tenuto **di proposito**: senza l'originale non ci si accorge
di un bug nella nostra conversione (§5-ter). Non usarlo come punteggio.

## I file

| file | righe | cos'è |
|---|--:|---|
| `partite.csv` | 662 | una riga per partita: data, turno, squadre, punteggio nei quattro pezzi, divisione delle due squadre, arbitro, allenatori, modulo, stadio, spettatori |
| `formazioni.csv` | 18.566 | una riga per giocatore-partita: `titolare`/`panchina`, ruolo, numero, capitano, **minuti giocati**, gol, assist, cartellini |
| `eventi.csv` | 8.177 | una riga per evento **col minuto**: 4.328 sostituzioni, 1.437 gol, 1.699 cartellini, 713 rigori |
| `da_raccogliere.csv` | 580 | **la lista di lavoro** per la raccolta manuale: solo il perimetro, ordinata per coppa e data, con `gia_abbiamo_formazioni` per vedere la priorità riga per riga |
| `manifesto.json` | — | provenienza, conteggi e **tutti** i controlli, compresi quelli falliti |
| `DA_RACCOGLIERE.md` | — | il **foglio da passare a chi raccoglie a mano**: da che turno partire in ogni coppa, cosa saltare, cosa annotare |

## Copertura, e i buchi dichiarati

| coppa | partite | 2ª div. entra a | nel perimetro | formazioni |
|---|--:|---|--:|:--:|
| Coppa Italia | 45 | Qualifying Round | 45 | ✅ (tranne finale) |
| FA Cup | 123 | Third Round | 63 | ✅ (tranne finale) |
| EFL Cup (Carabao) | 93 | First Round | 91 | ✅ |
| Copa del Rey | 137 | First Round | 117 | ✅ |
| DFB-Pokal | 63 | First Round | 63 | ✅ (tranne finale) |
| Coupe de France | 201 | 7° turno | 201 | ❌ |

⚠️ **204 partite non hanno le formazioni**: le 201 di Coupe de France (che
player-scores non copre affatto — `competitions.csv` non ha coppe francesi) e
le 3 finali assenti da `games.csv`, prese da Wikipedia. È un buco **dichiarato**,
non nascosto (R6): sono esattamente le partite dove `game_id` è vuoto.

**`dentro_perimetro`** applica il criterio deciso dall'utente il 02/08/2026 —
*«da dove iniziano a giocare i club di seconda divisione»*. Il turno d'ingresso
è **misurato** (primo turno con un club che football-data elenca in 2ª
divisione 2025-26), non copiato da una scheda di formato. Le partite fuori
perimetro sono **tenute lo stesso** e marcate `False`: il perimetro è un filtro
a valle, non un confine di raccolta (§5-ter).

**`divisione_casa` / `divisione_ospite`**: `1` prima divisione, `2` seconda,
`3` terza o sotto — il registro non distingue oltre la seconda.

⚠️ La prima divisione viene dagli **snapshot congelati 2025-26**, non da
`club_names.domestic_competition_id`: quel campo marca chiunque sia *mai* stato
in quella lega (37 club per `GB1`, fra cui Wigan, Reading, QPR, West Brom) e
faceva risultare **Wigan Athletic in prima divisione**. Corretto il 02/08/2026;
un test lo verifica lega per lega. Il perimetro non ne era stato toccato. Per la Coupe de
France ci sono anche `sigla_divisione_*` con la sigla esatta di Wikipedia
(`L2`, `N2`, `R1`…), che è più fine.

## Le tre fonti, e perché tre

| fonte | cosa dà | ruolo |
|---|---|---|
| **player-scores** (Kaggle `davidcariboo/player-scores`) | 5 coppe: formazioni, panchina, sostituzioni al minuto, gol, cartellini, arbitro, allenatore, modulo, spettatori | ossatura |
| **openfootball** (`deutschland/2025-26/cup.txt`) | DFB-Pokal turni 1-2, coi quattro punteggi già separati | **verifica esterna** |
| **Wikipedia** (fr + en) | Coupe de France dal 7° turno; le 3 finali mancanti | ciò che manca |

La verifica esterna non è decorazione: è ciò che ha reso la ricostruzione del
punteggio un fatto invece di un'ipotesi — **42 partite appaiate, 42/42
identiche su tutti e sei i campi**, zero divergenze. openfootball copre solo
la Germania per il 2025-26, e solo fino al 2° turno (dagli ottavi in poi il
file ha `N.N.`): è un verificatore parziale, non una fonte alternativa.

## Licenza e provenienza

`player-scores` deriva da **Transfermarkt**: vale la stessa riserva già
dichiarata in `docs/DATI.md` §4 (il dataset si dichiara CC0, ma Transfermarkt
pubblica una riserva `ai-all` e il diritto sui generis sulla banca dati resta
suo). openfootball è pubblico; Wikipedia è CC BY-SA. Il progetto non rivendica
alcuna licenza su questi dati.
