# `data/stagione_2025_2026/` — tutti i dati della stagione, al loro grano

Generato da `scripts/build_stagione_2025_2026.py`. Non modificare a mano:
ogni correzione vive nel codice che legge la fonte (R3).

**76 tabelle · 129 file · 10.258.960 righe · 255.7 MB** (il più grosso: 25.5 MB. tetto 90 MB).

## La chiave che tiene insieme tutto

Ogni riga **di grana partita** porta **`match_uid`**, ed è la stessa
ovunque:

```
match_uid = competizione | data ISO | casa normalizzata | trasferta normalizzata
```

Quindi qualunque tabella si riaggancia a `partite.csv.gz` con un merge
su quella colonna sola, e due tabelle qualsiasi si incrociano fra loro:

```python
import pandas as pd
p = pd.read_csv('data/stagione_2025_2026/partite.csv.gz', low_memory=False)
t = pd.read_csv('data/stagione_2025_2026/tiri.csv.gz', low_memory=False)
t.merge(p[['match_uid', 'competizione', 'casa', 'trasferta']], on='match_uid')
```

Dove la fonte ha anche i suoi identificatori (`ID partita (SofaScore)`,
`game_id`, `player_id`) quelli restano: servono a incrociare **dentro**
la partita.

⚠️ **Non tutte le tabelle hanno un `match_uid`, e non è una lacuna.**
Le anagrafiche (ranking UEFA, valori rosa, carriere, identità degli
allenatori), la classifica e i livelli `Rosa`/`Stagione` dei giocatori
non sono a grana partita: non c'è una partita a cui agganciarli. Il
manifesto lo dichiara con `aggancio_match_uid: null`.

⚠️ **`aggancio_match_uid` è misurato per APPARTENENZA**, cioè la
frazione di righe la cui chiave esiste davvero in `partite.csv.gz` —
non `notna()`. La differenza non è accademica: la chiave si costruisce
sempre, quindi un tasso calcolato su `notna` direbbe 1.0 anche con
tutte le chiavi penzolanti.

## Perché una cartella e non un file

Perché l'event data Opta, impacchettato in una cella, pesa **1,7 GB
grezzi / 243 MB gzippati** — da solo più del doppio del limite di 100 MB
per file che GitHub impone. Spezzato per competizione ogni pezzo ci sta,
e non si perde niente. Vale lo stesso per le 4,77 milioni di posizioni.

## I file

| tabella | grana | righe | col. | MB | file |
|---|---|--:|--:|--:|--:|
| `anagrafiche/aggancio_manuale.csv.gz` | aggancio_manuale | 1 | 9 | 0.0 | 1 |
| `anagrafiche/allenatori_wikidata_club_qid.csv.gz` | club qid | 135 | 8 | 0.0 | 1 |
| `anagrafiche/allenatori_wikidata_confronto.csv.gz` | confronto | 1.088 | 13 | 0.0 | 1 |
| `anagrafiche/allenatori_wikidata_da_controllare.csv.gz` | da controllare | 294 | 13 | 0.0 | 1 |
| `anagrafiche/allenatori_wikidata_mandati_persona.csv.gz` | mandati persona | 1.373 | 7 | 0.0 | 1 |
| `anagrafiche/allenatori_wikidata_mandati_wikidata.csv.gz` | mandati wikidata | 932 | 11 | 0.0 | 1 |
| `anagrafiche/allenatori_wikidata_persone_qid.csv.gz` | persone qid | 494 | 9 | 0.0 | 1 |
| `anagrafiche/allenatori_wikidata_registro_incarichi.csv.gz` | registro incarichi | 1.088 | 23 | 0.1 | 1 |
| `anagrafiche/calendario_club.csv.gz` | una partita nel calendario COMPLETO di un club (coppe ed Europa comprese) | 4.470 | 7 | 0.0 | 1 |
| `anagrafiche/carriere_wikipedia.csv.gz` | una tappa di carriera di un giocatore sceso in campo nel 2025-26 | 32.364 | 17 | 0.5 | 1 |
| `anagrafiche/correzioni_dichiarate.csv.gz` | una correzione | 1 | 13 | 0.0 | 1 |
| `anagrafiche/presenze_integrate.csv.gz` | presenze_integrate | 2 | 13 | 0.0 | 1 |
| `anagrafiche/ranking_uefa_club.csv.gz` | un club nel ranking UEFA | 410 | 13 | 0.0 | 1 |
| `anagrafiche/ranking_uefa_federazioni_2025-26.csv.gz` | una federazione nel ranking UEFA | 55 | 12 | 0.0 | 1 |
| `anagrafiche/stime_celle_residue.csv.gz` | una stima dichiarata | 8 | 16 | 0.0 | 1 |
| `anagrafiche/valore_rose_transfermarkt.csv.gz` | una squadra-stagione | 16 | 9 | 0.0 | 1 |
| `cambi_diretta.csv.gz` | cambi diretta | 5.635 | 14 | 0.1 | 1 |
| `classifiche.csv.gz` | una SQUADRA in una classifica (generale / casa / trasferta) | 732 | 21 | 0.0 | 1 |
| `coppe_aggancio_eventi.csv.gz` | aggancio eventi | 15.121 | 16 | 0.2 | 1 |
| `coppe_aggancio_giocatori.csv.gz` | aggancio giocatori | 18.307 | 14 | 0.3 | 1 |
| `coppe_aggancio_partite.csv.gz` | aggancio partite | 580 | 11 | 0.0 | 1 |
| `coppe_aggancio_squadre.csv.gz` | aggancio squadre | 580 | 3 | 0.0 | 1 |
| `coppe_aggancio_statistiche.csv.gz` | aggancio statistiche | 11.476 | 119 | 0.9 | 1 |
| `coppe_aggancio_statistiche_squadra.csv.gz` | aggancio statistiche squadra | 2.798 | 48 | 0.2 | 1 |
| `coppe_da_raccogliere.csv.gz` | da raccogliere | 580 | 14 | 0.0 | 1 |
| `coppe_diretta_eventi.csv.gz` | eventi | 15.121 | 14 | 0.2 | 1 |
| `coppe_diretta_formazioni_e_cambi.csv.gz` | formazioni e cambi | 18.307 | 19 | 0.3 | 1 |
| `coppe_diretta_note.csv.gz` | note | 137 | 10 | 0.0 | 1 |
| `coppe_diretta_partite.csv.gz` | partite | 580 | 17 | 0.0 | 1 |
| `coppe_diretta_stat_giocatori.csv.gz` | stat giocatori | 11.476 | 117 | 0.9 | 1 |
| `coppe_diretta_stat_squadra.csv.gz` | stat squadra | 2.798 | 46 | 0.2 | 1 |
| `coppe_eventi.csv.gz` | eventi | 8.177 | 13 | 0.1 | 1 |
| `coppe_formazioni.csv.gz` | formazioni | 18.566 | 17 | 0.4 | 1 |
| `coppe_incrocio_per_partita.csv.gz` | incrocio per partita | 580 | 14 | 0.0 | 1 |
| `coppe_partite.csv.gz` | una partita di coppa | 662 | 35 | 0.0 | 1 |
| `cronaca.csv.gz` | un evento di categoria «Cronaca» (partita) | 290.006 | 25 | 6.1 | 1 |
| `elenco_partite_diretta.csv.gz` | elenco partite diretta | 618 | 14 | 0.0 | 1 |
| `eventi.csv.gz` | un evento di categoria «Evento» (squadra) | 73.983 | 31 | 1.8 | 1 |
| `eventi_diretta.csv.gz` | eventi diretta | 4.446 | 18 | 0.2 | 1 |
| `eventi_opta` | un TOCCO Opta | 3.708.677 | 36 | 163.4 | 9 |
| `formazioni_diretta.csv.gz` | formazioni diretta | 24.649 | 18 | 0.4 | 1 |
| `giocatori_partita_diretta.csv.gz` | giocatori partita diretta | 54.303 | 114 | 3.8 | 1 |
| `giocatori_partita_tre_fonti` | un GIOCATORE in una partita (livello=Partita) / in una rosa (Rosa) / in una stagione (Stagione) | 169.939 | 202 | 20.7 | 16 |
| `giocatori_stagione_diretta.csv.gz` | giocatori stagione diretta | 2.905 | 108 | 0.4 | 1 |
| `metadati/legenda_diretta.csv.gz` | una colonna documentata delle raccolte diretta.it | 466 | 8 | 0.0 | 1 |
| `metadati/legenda_tre_fonti.csv.gz` | una colonna documentata | 7.061 | 6 | 0.1 | 1 |
| `metadati/manifesti_delle_raccolte.json` | un manifesto di consegna | 34 | 0 | 0.1 | 1 |
| `migliore_in_campo.csv.gz` | un evento di categoria «Migliore in campo» (partita) | 6.376 | 23 | 0.2 | 1 |
| `momentum.csv.gz` | un evento di categoria «Momentum» (partita) | 295.684 | 21 | 1.8 | 1 |
| `partite.csv.gz` | una PARTITA | 4.169 | 2175 | 8.2 | 1 |
| `posizioni` | una POSIZIONE (un tocco con X/Y) | 4.767.120 | 20 | 25.6 | 16 |
| `quote.csv.gz` | un evento di categoria «Quota» (partita) | 129.116 | 25 | 1.8 | 1 |
| `quote_football_data.csv.gz` | una partita. con le ~108 colonne di quota della fonte | 1.140 | 134 | 0.2 | 1 |
| `serie.csv.gz` | un evento di categoria «Serie» (partita) | 35.819 | 22 | 0.3 | 1 |
| `snapshot_partite.csv.gz` | una partita dei 5 campionati (snapshot congelato) | 1.752 | 42 | 0.1 | 1 |
| `squadre_partita_diretta.csv.gz` | squadre partita diretta | 10.512 | 59 | 0.6 | 1 |
| `squadre_partita_tre_fonti` | una SQUADRA in una partita. per PERIODO (Totale / 1° tempo / 2° tempo / supplementari) | 19.852 | 235 | 2.4 | 16 |
| `tiri.csv.gz` | un evento di categoria «Tiro» (squadra) | 125.896 | 40 | 5.1 | 1 |
| `transfermarkt_appearances.csv.gz` | appearances | 73.065 | 14 | 1.7 | 1 |
| `transfermarkt_club_games.csv.gz` | club games | 5.808 | 12 | 0.1 | 1 |
| `transfermarkt_club_names.csv.gz` | club names | 562 | 3 | 0.0 | 1 |
| `transfermarkt_clubs.csv.gz` | clubs | 226 | 17 | 0.0 | 1 |
| `transfermarkt_competitions.csv.gz` | competitions | 21 | 11 | 0.0 | 1 |
| `transfermarkt_partite.csv.gz` | una partita 2025-26 delle nostre 22 competizioni. vista da Transfermarkt | 3.155 | 29 | 0.2 | 1 |
| `transfermarkt_player_valuations.csv.gz` | player valuations | 4.666 | 6 | 0.1 | 1 |
| `transfermarkt_players.csv.gz` | players | 5.321 | 26 | 0.5 | 1 |
| `uefa_cambi.csv.gz` | cambi | 8.268 | 15 | 0.2 | 1 |
| `uefa_colori_maglie.csv.gz` | colori maglie | 912 | 12 | 0.0 | 1 |
| `uefa_eventi.csv.gz` | eventi | 21.152 | 22 | 0.5 | 1 |
| `uefa_giocatori.csv.gz` | giocatori | 40.067 | 105 | 2.7 | 1 |
| `uefa_momentum.csv.gz` | momentum | 61.758 | 10 | 0.3 | 1 |
| `uefa_note_copertura.csv.gz` | note e copertura | 16 | 2 | 0.0 | 1 |
| `uefa_partite_sofascore.csv.gz` | una partita di coppa UEFA | 912 | 42 | 0.1 | 1 |
| `uefa_posizioni_medie.csv.gz` | posizioni medie | 19.848 | 12 | 0.4 | 1 |
| `uefa_statistiche_squadra.csv.gz` | statistiche squadra | 86.807 | 13 | 0.6 | 1 |
| `uefa_tiri.csv.gz` | tiri | 16.929 | 21 | 0.5 | 1 |

Il dettaglio — nomi di tutte le colonne, fonti, asse di spezzatura,
tasso di aggancio a `match_uid`, sha256 di ogni pezzo — sta in
`MANIFESTO.json`.

## ⚠️ Le trappole che valgono per tutta la cartella

1. **Il «meteo» non è il meteo.** `Meteo (WhoScored)` vale 5.0 e solo
   5.0 ovunque sia pieno: varianza zero, finto pieno da manuale (R6).
   Il progetto non ha dati meteo.
2. **Due punteggi, non uno.** I 90 minuti e il finale con i
   supplementari sono numeri diversi, e la lotteria dei rigori non sta
   mai dentro nessuno dei due. In Europa League e Conference l'export
   la somma dentro `Gol casa`: `Gol casa regolamentari` è la colonna
   riparata.
3. **L'allenatore è chi sedeva in panchina**, non chi era in carica —
   SofaScore registra il vice quando il tecnico era squalificato.
   WhoScored e Transfermarkt danno il tecnico. Divergono su 36 partite
   su 1.752, e non è grafia.
4. **`red_cards` di `transfermarkt_appearances` è muta**: vale 0 su
   tutte le righe del 2025-26.
5. **La classifica è quella FINALE**: su una partita di ottobre è
   look-ahead puro (R8).
6. **Il meteo, quando c'è, è una lega sola.** `Meteo (WhoScored)` è
   piena su 2.262 righe squadra-partita su 19.852 (11,4%), e sono
   quasi tutte Premier League: Serie A, Ligue 1, LaLiga2 e ogni coppa
   hanno ZERO. E dove è piena vale sempre lo stesso numero.
7. **14 `match_uid` hanno un lato vuoto** — turni preliminari di Copa
   del Rey dove l'avversario manca alla fonte: la chiave esiste ma non
   si può ricostruire da (competizione, data, casa, trasferta).
8. **Lo spareggio Bundesliga/2.Bundesliga compare due volte**, una per
   competizione (4 righe per 2 partite): è così che le due raccolte lo
   consegnano, e i dati fini stanno sotto una delle due.
9. **Otto partite di Europa League** hanno i tempi che non sommano al
   risultato, cinque con entrambi i tempi a zero e gol nella partita:
   è un difetto della FONTE, ereditato e non corretto (R5 — va
   istruito a mano, non zittito).
10. **Una sola colonna JSON sopravvive**: `provenienza_json` in
    `partite.csv.gz`, che dice quale fonte ha vinto per ogni campo
    normalizzato. Non è un dato impacchettato: è la provenienza.
11. **R8 in generale**: questa cartella mescola per costruzione dati
    `pre` (quote, arbitro, moduli, valore rosa) e `post` (gol, xG,
    rating, posizioni). È un **archivio**, non un dataset di
    addestramento.

## Cosa NON c'è

### Il perimetro, e come è tagliato

Le anagrafiche di Transfermarkt e le carriere di Wikipedia coprono per
costruzione ogni epoca. Qui sono **ristrette al perimetro**: i
giocatori che sono scesi in campo nel 2025-26 e i club che hanno
giocato. Le stime dichiarate di altre stagioni, e la finestra 2026-27
del ranking UEFA, restano fuori: sono dato di un'altra stagione.

### Le competizioni che mancano

Quattro delle 25 chieste: **Serie B, Championship,
Ligue 2, EFL Trophy**. Non è una lacuna della cartella: il repo non ha
una riga della loro stagione 2025-26. Esistono altrove nel tempo — in
Smarkets sono 2026-27, in `club_fixtures` sono 1617-2425.
