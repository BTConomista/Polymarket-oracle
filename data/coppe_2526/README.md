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


## Statistiche di SQUADRA per periodo (Fasi 139-quinquies → 139-septies)

Secondo consegnato di diretta.it, **complementare** al primo: porta un dato che
la raccolta base non aveva — le statistiche di squadra divise per **periodo**
(Totale / 1° tempo / 2° tempo / Supplementari), 35 metriche per riga.

| coppa | righe | partite | supplementari |
|---|--:|--:|--:|
| Coppa Italia | 272 | 45 | 2 righe (1 partita) |
| DFB-Pokal | 406 | 63 | 28 righe (14 partite) |
| FA Cup | 406 | 63 | 28 righe (14 partite) |
| EFL Cup (Carabao) | 546 | 91 | **0** — e non è un buco, vedi sotto |
| Coupe de France | 476 | **87 su 201** | 0 — copertura parziale, vedi sotto |
| Copa del Rey | 692 | **114 su 117** | 52 righe (13 partite) |

**Ci sono tutte e sei.** 2.798 righe, 463 partite, 35 metriche per riga.

⚠️ **Coupe de France e Copa del Rey hanno la copertura a TRE LIVELLI**, ed è la
fonte a farla così: quanto più il turno è dilettantistico, meno pubblica. Il
livello non è dichiarato da nessuna colonna — si legge da quante metriche sono
piene, e va guardato prima di usare il dato.

| livello | metriche piene | cosa c'è | dove |
|---|--:|---|---|
| **completo** | ~27 su 29 | tutto, xG e possesso compresi | Coupe: dai 32esimi. Rey: dai 1/16 + 15 partite del 2° turno |
| **base** | 8-10 | tiri, angoli, falli, fuorigioco, rimesse, punizioni, cartellini — nessun xG, nessun possesso | Rey: 13 partite del 2° turno |
| **solo cartellini** | 1-2 | i cartellini e basta | Coupe: 24 partite dei turni 7-8. Rey: 53 del 1° turno |

Le righe del terzo livello esistono **perché** c'è stato un cartellino, e il
conteggio combacia con `eventi.csv`: **48/48** sulla Coupe, **106/106** sul Rey.
Le altre colonne sono **vuote**, non zero — se fossero zero sarebbe un finto
pieno (R6). Ed è anche il motivo per cui i periodi non si bilanciano: la riga di
un tempo esiste solo se in quel tempo è successo qualcosa.

Senza statistiche del tutto: **114 partite** della Coupe de France e **3** della
Copa del Rey.

⚠️ **La Carabao Cup non ha righe «Supplementari», e non è un dato mancante: è
il regolamento.** Dal 2018-19 la EFL Cup va **direttamente ai rigori** in ogni
turno; i supplementari restano solo per la finale, che nel 2025-26 è finita 0-2
nei 90 minuti. La conferma viene dal dato indipendente: nelle 91 partite non c'è **un
solo evento** oltre il 90° (`eventi.csv` ha 1T, 2T e Rigori, nessun
«Supplementari»), mentre le altre tre coppe ne hanno 6/131/142. Nessun periodo è
stato perso per strada — non c'era.

Vive in `files/diretta_<coppa>_2526/stat_squadra.csv`, agganciato in
`data/coppe_2526/aggancio_statistiche_squadra.csv` (`game_id` + `club_id`).
Le righe senza `game_id` sono quelle della **finale**, che la fonte automatica
non ha: 6 per coppa, cioè 2 squadre × 3 periodi. **La Carabao fa eccezione**
(546/546 con `game_id`): è l'unica la cui finale player-scores contiene, e con
lei la **Copa del Rey** (692/692 su entrambi). **La Coupe de France fa
l'eccezione opposta** — 0/476 con `game_id` e 234/476 con `club_id`: la sua
fonte automatica è Wikipedia, che non porta identificatori (assenza a monte, non
un limite dell'aggancio).

⚠️ **La stessa fonte può scrivere un club in due modi fra i due consegnati**:
sulla Copa del Rey `Ciudad Cieza` nella raccolta base e `Cieza` nel file di
statistiche — stesse due partite, stessi 14 giocatori, un club solo (CD Cieza,
`club_id` 56725, confermato dalla fonte automatica). Il sinonimo si accetta solo
per **sottoinsieme di token** e solo se **unico nei due sensi**, si **dichiara**
nel manifesto, e la colonna resta com'è consegnata: si canonicalizza la chiave,
non il dato.

### La coerenza interna dei periodi, misurata

I tempi devono ricomporre il totale, ed è una verifica che non costa niente e
non era mai stata fatta.

| famiglia | Coupe de France | Copa del Rey |
|---|---|---|
| 29 metriche numeriche (xG, tiri, angoli, falli, parate…) | **126/126** | **2.146/2.146** |
| 5 metriche a rapporto (`Passaggi`, `Cross`, `Tackles`…): numeratore e denominatore | **252/252** | **720/720** |
| `Possesso palla` (percentuale, non additiva): casa + ospite = 100 | **189/189** | **197/197** |

⭐ **E ha stabilito un fatto di semantica che nessuno aveva verificato: `Totale`
è la partita INTERA, supplementari compresi.** Non il 90'. Sulle 102
squadra-partita andate ai supplementari nelle quattro coppe che ne hanno:

```
1° tempo + 2° tempo + Supplementari = Totale     2.228 / 2.228 celle
1° tempo + 2° tempo                 = Totale       628 / 2.232   (cioè: falso)
```

⚠️ La prima lettura del possesso diceva «49 gruppi su 238 non fanno 100»: era
un `groupby().sum()` che tratta i `NaN` come zeri. Non c'è **nessuna** riga con
possesso 0%: ci sono righe dove il possesso **manca**, e sono esattamente quelle
del terzo livello.

⭐ **È il primo dato di coppa che separa i due tempi**, cioè la forma che serve
al modello a due stadi (residuo aperto delle Fasi 96/99: il secondo tempo è mal
calibrato perché è *game-state*, e per modellarlo serve il punteggio
all'intervallo). Per i campionati lo stesso dato esiste dalla Fase 131.

Lo stesso file porta anche una versione **migliore** delle statistiche per
giocatore: stessi valori (verificato — 0 celle divergenti oltre l'arrotondamento
su 149.000 confrontate) ma con `ID partita`, che prima mancava, e i decimali per
intero invece che troncati a tre.

**Stato d'uso: raccolto, non usato.** Nessun modello legge queste colonne.


## L'incrocio: i blocchi si uniscono? (Fase 139-octies)

Domanda dell'utente: *«verifica che siamo in grado di incrociare tutti i dati
relativi a queste partite»*. Misurato con
`python scripts/verifica_incrocio_coppe.py` — che produce **quattro** tabelle e
non una, perché un conteggio unico confonde tre cose diverse:

> **fuori perimetro** ≠ buco · **senza ponte** ≠ assente · **presente** ≠ unibile

### 1 · Fonte automatica (player-scores), chiave `game_id` — sul perimetro

| coppa | nel perimetro | arbitro | allenatori | 11+11 titolari | minuti |
|---|--:|--:|--:|--:|--:|
| Coppa Italia | 45 | 45 | 44 | 44 | 41 |
| DFB-Pokal | 63 | 63 | 62 | 62 | 61 |
| EFL Cup | 91 | 91 | 91 | 91 | 89 |
| FA Cup | 63 | 63 | 62 | 62 | 62 |
| Copa del Rey | 117 | 116 | 117 | 117 | 95 |
| Coupe de France | 201 | **0** | **0** | **0** | **0** |

### 2 · Raccolta manuale (diretta.it), chiave `ID partita` — sul raccolto

| coppa | raccolte | sostituzioni | stat. individuali | stat. squadra | con ponte al `game_id` |
|---|--:|--:|--:|--:|--:|
| Coppa Italia | 45 | 45 | 41 | 45 | 44 |
| DFB-Pokal | 63 | 63 | 63 | 63 | 62 |
| EFL Cup | 91 | 91 | 91 | 91 | 91 |
| FA Cup | 63 | 63 | 63 | 63 | 62 |
| Copa del Rey | 117 | 117 | **45** | 114 | 117 |
| Coupe de France | 201 | 63 | 63 | 87 | **0** |

### 3 · L'incrocio vero: TUTTI i blocchi sullo stesso `game_id`

| coppa | nel perimetro | incrociabili | quota |
|---|--:|--:|--:|
| FA Cup | 63 | 62 | **98,4%** |
| EFL Cup | 91 | 89 | **97,8%** |
| DFB-Pokal | 63 | 61 | **96,8%** |
| Coppa Italia | 45 | 40 | **88,9%** |
| Copa del Rey | 117 | 44 | 37,6% |
| Coupe de France | 201 | 0 | 0% |
| **totale** | **580** | **296** | **51,0%** |

Escludendo la Coupe de France — che è un problema di natura diversa — sono
**296/379, il 78,1%**.

### 4 · Il giro completo: dal titolare alla SUA statistica individuale

È il join che conta davvero, e non lo si vede dalle tabelle sopra: una partita
può esserci da entrambe le parti mentre le **persone** non si uniscono. Join per
`player_id` fra due fonti indipendenti:

| coppa | titolari | agganciati alla propria riga | quota |
|---|--:|--:|--:|
| DFB-Pokal | 1.364 | 1.361 | 99,8% |
| Coppa Italia | 880 | 876 | 99,5% |
| FA Cup | 1.364 | 1.353 | 99,2% |
| EFL Cup | 2.002 | 1.975 | 98,7% |
| Copa del Rey | 990 | 924 | 93,3% |
| **totale** | **6.600** | **6.489** | **98,3%** |

### I tre motivi per cui una partita non si incrocia — e sono diversi

1. **Coupe de France (201)**: nessun `game_id`, quindi nessun ponte. La sua
   fonte automatica è Wikipedia, che non porta identificatori. I dati manuali
   ci sono e si incrociano **fra loro**; con arbitro/allenatore/formazioni no,
   perché dall'altra sponda non esistono. Assenza a monte.
2. **Copa del Rey (73)**: il **First Round**, 56 partite, ha **0** statistiche
   individuali — diretta.it non le pubblica per il turno dilettantistico. Dal
   Round of 32 in poi la coppa è al **100%**. È lo stesso taglio a livelli
   delle statistiche di squadra.
3. **Le finali (3)** di Coppa Italia, FA Cup e DFB-Pokal: `games.csv` non le
   contiene, quindi non hanno `game_id`.

### ⚠️ Il meteo non c'è, e non è un dettaglio da sottintendere

**Per il 2025-26 il meteo non esiste in nessuna tabella del progetto.** Non è
«manca in qualche partita»: è zero su 662. L'infrastruttura che esiste
(`scripts/fetch_stadi_coordinate.py`, `data/stagione_2026_2027/giornaliero/`) è
**prospettica** — raccoglie la *previsione* a 16 giorni per la stagione 2026-27,
e una previsione non si ricostruisce all'indietro.

Cosa servirebbe, misurato:

| pezzo | stato |
|---|---|
| coordinate degli stadi | **59 su 422** stadi di coppa (110 partite su 662). Gli altri 363 sono club minori, fuori dalle 96 voci raccolte per le 5 leghe |
| fonte storica | **non ancora usata**. `open-meteo.com` è raggiungibile e senza chiave (`docs/MANUALE_SOPRAVVIVENZA.md` §1) e ha l'archivio storico |
| il dato | sarebbe un **consuntivo** (`post`), non la previsione pre-partita (`pre`) — due cose diverse sotto R8, e per un modello conta la seconda |

Riproducibile con `python scripts/verifica_incrocio_coppe.py --csv`; la matrice
per partita finisce in `incrocio_per_partita.csv`, i conteggi in
`incrocio_manifesto.json`. Per il giro end-to-end su una singola partita:
`--partita <game_id>`.
