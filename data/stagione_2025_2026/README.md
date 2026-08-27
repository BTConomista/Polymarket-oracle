# `data/stagione_2025_2026/` — tutti i dati della stagione, al loro grano

Generato da `scripts/build_stagione_2025_2026.py`. Non modificare a mano:
ogni correzione vive nel codice che legge la fonte (R3).

**79 tabelle · 117 file · 10.506.631 righe · 263.4 MB** (il più grosso: 25.5 MB. tetto 90 MB).

## La chiave che tiene insieme tutto

Ogni riga di ogni file porta **`match_uid`**, ed è la stessa ovunque:

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

## Perché una cartella e non un file

Perché l'event data Opta, impacchettato in una cella, pesa **1,7 GB
grezzi / 243 MB gzippati** — da solo più del doppio del limite di 100 MB
per file che GitHub impone. Spezzato per competizione ogni pezzo ci sta,
e non si perde niente. Vale lo stesso per le 4,77 milioni di posizioni.

## I file

| tabella | grana | righe | col. | MB | file |
|---|---|--:|--:|--:|--:|
| `anagrafiche/aggancio_manuale.csv.gz` | aggancio_manuale | 1 | 9 | 0.0 | 1 |
| `anagrafiche/allenatori_wikidata_club_qid.csv.gz` | club qid | 153 | 8 | 0.0 | 1 |
| `anagrafiche/allenatori_wikidata_confronto.csv.gz` | confronto | 1.190 | 13 | 0.0 | 1 |
| `anagrafiche/allenatori_wikidata_da_controllare.csv.gz` | da controllare | 294 | 13 | 0.0 | 1 |
| `anagrafiche/allenatori_wikidata_mandati_persona.csv.gz` | mandati persona | 1.373 | 7 | 0.0 | 1 |
| `anagrafiche/allenatori_wikidata_mandati_wikidata.csv.gz` | mandati wikidata | 1.023 | 11 | 0.0 | 1 |
| `anagrafiche/allenatori_wikidata_persone_qid.csv.gz` | persone qid | 494 | 9 | 0.0 | 1 |
| `anagrafiche/allenatori_wikidata_registro_incarichi.csv.gz` | registro incarichi | 1.190 | 23 | 0.1 | 1 |
| `anagrafiche/calendario_club.csv.gz` | una partita nel calendario COMPLETO di un club (coppe ed Europa comprese) | 4.470 | 7 | 0.0 | 1 |
| `anagrafiche/carriere_wikipedia.csv.gz` | una tappa di carriera | 209.809 | 17 | 3.6 | 1 |
| `anagrafiche/correzioni_dichiarate.csv.gz` | una correzione | 44 | 13 | 0.0 | 1 |
| `anagrafiche/presenze_integrate.csv.gz` | presenze_integrate | 2 | 13 | 0.0 | 1 |
| `anagrafiche/ranking_uefa_club.csv.gz` | un club nel ranking UEFA | 410 | 13 | 0.0 | 1 |
| `anagrafiche/ranking_uefa_federazioni_2025-26.csv.gz` | una federazione nel ranking UEFA | 55 | 12 | 0.0 | 1 |
| `anagrafiche/ranking_uefa_federazioni_2026-27.csv.gz` | una federazione nel ranking UEFA | 55 | 12 | 0.0 | 1 |
| `anagrafiche/stime_celle_residue.csv.gz` | una stima dichiarata | 32 | 16 | 0.0 | 1 |
| `anagrafiche/stime_open_sparse_1x2_ou.csv.gz` | una stima dichiarata | 2 | 10 | 0.0 | 1 |
| `anagrafiche/stime_ou_close_2017_19.csv.gz` | una stima dichiarata | 3.638 | 6 | 0.0 | 1 |
| `anagrafiche/stime_ou_open_corrotte_2017_19.csv.gz` | una stima dichiarata | 12 | 20 | 0.0 | 1 |
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
| `giocatori_partita_tre_fonti` | un GIOCATORE in una partita (livello=Partita) / in una rosa (Rosa) / in una stagione (Stagione) | 169.939 | 201 | 20.6 | 16 |
| `giocatori_stagione_diretta.csv.gz` | giocatori stagione diretta | 2.905 | 108 | 0.4 | 1 |
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
| `squadre_partita_tre_fonti` | una SQUADRA in una partita. per PERIODO (Totale / 1° tempo / 2° tempo / supplementari) | 19.852 | 235 | 2.4 | 1 |
| `tiri.csv.gz` | un evento di categoria «Tiro» (squadra) | 125.896 | 40 | 5.1 | 1 |
| `transfermarkt_appearances.csv.gz` | appearances | 78.012 | 14 | 1.8 | 1 |
| `transfermarkt_club_games.csv.gz` | club games | 6.310 | 12 | 0.1 | 1 |
| `transfermarkt_club_names.csv.gz` | club names | 3.173 | 3 | 0.0 | 1 |
| `transfermarkt_clubs.csv.gz` | clubs | 796 | 17 | 0.1 | 1 |
| `transfermarkt_competitions.csv.gz` | competitions | 65 | 11 | 0.0 | 1 |
| `transfermarkt_partite.csv.gz` | una partita 2025-26 vista da Transfermarkt (anche fuori dal nostro perimetro) | 9.554 | 29 | 0.9 | 1 |
| `transfermarkt_player_valuations.csv.gz` | player valuations | 11.370 | 6 | 0.1 | 1 |
| `transfermarkt_players.csv.gz` | players | 50.149 | 26 | 4.1 | 1 |
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
6. **R8 in generale**: questa cartella mescola per costruzione dati
   `pre` (quote, arbitro, moduli, valore rosa) e `post` (gol, xG,
   rating, posizioni). È un **archivio**, non un dataset di
   addestramento.

## Cosa NON c'è

Quattro delle 25 competizioni chieste: **Serie B, Championship,
Ligue 2, EFL Trophy**. Non è una lacuna della cartella: il repo non ha
una riga della loro stagione 2025-26. Esistono altrove nel tempo — in
Smarkets sono 2026-27, in `club_fixtures` sono 1617-2425.
