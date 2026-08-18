# LaLiga2 (Segunda División) 2025-26 — la prima raccolta di SECONDA DIVISIONE

Consegna 18/08/2026, due zip (puliti + grezzi). **468 partite, 22 squadre,
stagione completa**: 42 giornate da 11 partite (462) più il playoff promozione
(4 semifinali + 2 finali). Fonti **due**, non tre.

```python
from src.data import tre_fonti as tf
tf.squadre("laliga2", periodo="Totale")                  # 924 squadra-partita (campionato)
tf.squadre("laliga2", periodo="Totale", spareggio=True)  # 936, col playoff
tf.eventi("laliga2", categoria="Tiro")
tf.classifica("laliga2")                                 # 66 righe: generale / casa / trasferta
```

| blocco | righe | note |
|---|--:|---|
| `squadre` | 2.874 | 2.808 di partita (468 × 2 × 3 periodi) + 66 di classifica |
| `giocatori` | 21.483 | 20.868 di partita + 615 di rosa. **Solo SofaScore** |
| `eventi` | 94.404 | **sei** categorie, non sette |
| `heatmap` | 675.209 | 468 partite, 674 giocatori |
| `legenda` | 355 | documenta **328 colonne su 328**, zero scoperte |

I file sono i CSV consegnati, gzippati e non toccati (R3): gli sha256 stanno in
`manifesto.json`. In `grezzi/` ci sono i sette JSON da cui sono stati prodotti,
**come consegnati** (§5-ter) — compresi i due che valgono più di tutti gli
altri, perché contengono la prova dei risultati negativi (vedi sotto).

---

## ⚠️ Perché «a tre fonti» qui sarebbe un nome falso

Understat e l'Opta di WhoScored **non ci sono**, e in nessuno dei due casi è un
incidente di raccolta: entrambe le assenze sono state **misurate**, e la misura
è archiviata.

**Understat non copre la Segunda.** Verificato in tre modi indipendenti: il
menu del sito elenca sei sole leghe, tutte di prima divisione; cinque varianti
di URL (`La_liga_2`, `Segunda`, `Segunda_Division`, `LaLiga2`, `Spain_2`)
rispondono tutte 404; e — il modo che conta — le pagine squadra chieste per il
2025 **servono in silenzio un altro anno**: Almería e Cádiz danno 2023/24,
Deportivo 2026/27. Quest'ultimo è un finto pieno da manuale (R6): chi si
fermasse al primo `200 OK` archivierebbe la stagione sbagliata credendola
giusta. Prova: `grezzi/LL2_2526_understat_verifica.json.gz`.

**WhoScored c'è, ma senza Opta.** Nessun `matchCentreData` su 468 pagine su
468, provate in sei forme di URL diverse: ~101 KB di HTML contro **1,14 MB** di
una partita di LaLiga scaricata nello stesso momento dalla stessa scheda. Quel
**controllo positivo** è ciò che separa «la fonte non copre questa
competizione» da «lo scaricatore si è rotto», ed è per questo che vale più di
sei tentativi falliti. Prova: `grezzi/LL2_2526_ws_controllo2.json.gz`.
Conseguenza: **niente `eventi_opta`** — l'unico blocco che manca rispetto alle
cinque leghe.

Quello che WhoScored dà comunque è `initialMatchDataForScrappers` — gol,
cartellini e cambi al minuto — cioè **8.188 righe dentro `eventi`**, ed è
l'unica seconda fonte su questa competizione.

---

## ⚠️⚠️ La categoria `Evento` arriva da DUE fonti: contare i gol senza filtrare li raddoppia

Nelle altre raccolte l'unica categoria a due fonti è `Tiro`. Qui è anche
`Evento`, con gli **stessi** gol, cartellini e cambi raccontati due volte:

| | SofaScore | WhoScored |
|---|--:|--:|
| righe `Evento` | 9.377 | 8.188 |
| di cui `Gol` | 1.229 | 1.222 |

I gol veri sono **1.229**. Chi somma senza filtrare `Fonte` ne conta 2.451.
Per i gol la fonte è SofaScore (`preferita("gol")`), e non per convenzione:
ricostruisce il punteggio su **936 squadra-partita su 936** (1.229 gol, 41
autogol e 127 rigori compresi). WhoScored non torna su 5 partite — in 2 sbaglia
anche il risultato finale che pubblica lui stesso.

Le due fonti divergono su **103 partite**: gialli 100, cambi 19, rossi 11, gol 7
(conteggio squadra-partita, playoff incluso). `discordanze_squadra("laliga2")`
le restituisce.

⭐ E qui **non c'è il falso positivo sul possesso** che marcava 760 righe su 760
in Serie A, Premier e Liga. Non perché sia stato riparato: perché WhoScored qui
non pubblica statistiche di squadra, quindi non c'è nessuna percentuale da
confrontare con nessun conteggio. La discordanza falsa spariva se una delle due
grandezze non esisteva — il che conferma, per via indipendente, che era
un'unità di misura diversa e non un disaccordo.

---

## ⚠️⚠️ `ID partita` di `eventi`: il difetto che questa lega ha fatto emergere ovunque

Nel file `Eventi.csv` la colonna `ID partita` è **di testo**, e ha due formati
diversi a seconda della riga:

```
Fonte = SofaScore  ->  "14081721"
Fonte = WhoScored  ->  "14081721 (SofaScore) / 1914700 (WhoScored)"
```

È piena al 100% e sembra una chiave. Non lo è: un join numerico fallisce su
**tutte e 94.404** le righe — comprese le 86.216 SofaScore che un id giusto ce
l'hanno, perché `"14081721" != 14081721`.

Cercando la stessa colonna nelle altre raccolte è venuto fuori che **era
avvelenata da sempre, e nessuno se n'era accorto in dodici consegne**: la Serie
A ha **760 id distinti per 380 partite**, perché le righe `Tiro` di Understat
portano l'id di Understat. Lì il join non fallisce — **perde in silenzio** 9.373
righe di tiri, e chi conta i tiri ne conta metà credendo di averli tutti.

Il difetto era invisibile perché in `squadre` e `giocatori` accanto alla colonna
mista ci sono quelle per-fonte (e `_rinomina_id_avvelenato` scatta), mentre in
`eventi` quelle colonne non esistono: non c'era niente con cui accorgersene.

⭐ È la forma **peggiore** — quella di LaLiga2 — a essere l'unica che si ripara
da sola: la frase **contiene** l'id SofaScore. `_ripara_id_eventi` ora dà a ogni
raccolta una colonna `ID partita (SofaScore)` pulita (LaLiga2 100% dal file, le
altre cinque via la mappa in `squadre`) e rinomina la grezza in
`ID partita (misto, NON usare)`.

---

## Le altre cose da sapere prima di usarla

**Non c'è uno snapshot.** `data/laliga2_matches.csv` non esiste e la Segunda non
è in `LEAGUE_CONFIGS`: niente quote, niente backtest, niente δ tarato. Per
questa raccolta il criterio «aggancio 924/924» delle altre leghe **non esiste**,
e i controlli che lo sostituiscono sono interni: i gol degli eventi contro il
punteggio (936/936) e l'identità `Gol = 1T + 2T` (468/468). `tf.ha_snapshot()`
dice quali raccolte ce l'hanno.

**Il playoff non è lo spareggio di Bundesliga e Ligue 1.** Là le partite fuori
giornata coinvolgono squadre di **seconda divisione**, estranee al campionato.
Qui il playoff promozione è fra squadre di LaLiga2 — Almería, Castellón, Las
Palmas, Málaga, tutte e quattro già nelle 42 giornate — e infatti le squadre
sono **22 con e 22 senza**. Resta fuori per default perché il default del modulo
è il girone all'italiana, ma è competizione vera: `spareggio=True` la riprende.

**I nomi sono accentati, il resto del progetto è ASCII.** La grafia canonica è
quella di football-data, e negli snapshot delle 5 leghe i nomi accentati sono
**zero**. Delle 22 squadre: 6 sono già canoniche, **4 hanno un bersaglio
verificato** nei nostri dati e sono mappate in `ALIAS_RACCOLTA`, **12 non
esistono** perché non hanno mai giocato in prima divisione nella finestra
2017-2025 — per quelle non c'è un bersaglio, e inventarlo sarebbe indovinare un
join.

⚠️ **La quarta è arrivata solo alla seconda passata, e il motivo insegna
qualcosa.** Tre divergono per un **accento** (Almería/Almeria, Cádiz/Cadiz,
Leganés/Leganes) e uno script che toglie gli accenti le trova subito. La quarta
è `Deportivo de A Coruña` → **`La Coruna`**: fra «A Coruña» e «La Coruña» non
c'è un accento di mezzo, c'è una **lingua** — galiziano contro castigliano — e
nessuna normalizzazione tipografica ci arriva. L'ha trovata solo stampare i 30
nomi dello snapshot e leggerli. **Un'euristica che risolve la famiglia di
difetti che conosci non è una misura di copertura**: dice quanti casi di *quel*
tipo c'erano, non quanti ne restano.

⭐ E non è accademico: **Deportivo è promosso in prima divisione nel 2026-27**
(2° in classifica). Senza quella riga, quando arriverà lo snapshot di LaLiga
2026-27 le sue partite di Segunda non si aggancerebbero a quelle di LaLiga, e
nessun conteggio se ne accorgerebbe.

⚠️ Fra le 22 c'è **`Real Sociedad B`**, la squadra riserve. Un aggancio per
somiglianza le troverebbe `Sociedad`, cioè la **prima squadra**: univoco, sicuro
di sé e falso, e nessun conteggio di celle piene lo vedrebbe. È la stessa
famiglia dell'`Espanol` → «Jove Espanol San Vicente» di `docs/audit_identita`.
Per questo la mappa degli alias è scritta a mano e chiusa.

**`Real Racing Club` resta non mappato, ed è il contrasto che spiega la
regola.** Anche lui sale in prima divisione nel 2026-27 (1° in classifica), come
il Deportivo — ma `Santander`, il nome con cui football-data lo chiamerebbe,
**non compare in nessuno dei nostri snapshot**: la sua ultima stagione in prima
divisione è del 2012, fuori dalla finestra 2017-2025. Nessun bersaglio
verificato, nessun alias. Si aggiungerà quando ci sarà qualcosa a cui
agganciarlo, non prima. (Nel grezzo di WhoScored il nome c'è già come
`Racing Santander`.)

**Promosse in LaLiga 2026-27**: Real Racing Club (1°, 82 punti), Deportivo de A
Coruña (2°, 77) e Málaga (vincitrice del playoff).

**38 colonne vuote**, il numero più alto di ogni campionato, in tre famiglie con
tre cause diverse: 27 `(WhoScored)` (la fonte qui non dà schede partita — solo 2
delle 19 colonne di squadra sono piene, e **zero** delle 10 di giocatore), 8 di
supplementari/rigori (nessuna delle 468 partite è andata oltre il 90', playoff
compreso), e `Note classifica`. Elenco in `COLONNE_VUOTE["laliga2"]`.

**`Spettatori` è quasi vuota: 17 partite su 468** (3,6%). È lo stato di mezzo,
il più insidioso — un `notna().any()` risponde «funziona» — ed è il motivo per
cui esiste `copertura()`, che torna lo stato e non un booleano. Resta comunque
`post` (R8): si sa a partita giocata, non prima.

**`Cronaca` non c'è.** L'endpoint `/comments` risponde 404 su 468 partite su
468: su questa competizione la cronaca minuto per minuto non esiste. È l'unico
dei dodici endpoint per partita a non rispondere.

**Due partite rinviate** (AD Ceuta-Córdoba, Real Sociedad B-Huesca) restano su
SofaScore come gusci vuoti alla data originaria e **non sono nei file**: ci sono
le versioni rigiocate, una volta sola, con la data vera.

**La sfida antibot di SofaScore (novità 2026).** L'API risponde 403
`{reason: challenge}` a chi non manda `X-Captcha`; il token sta in
`localStorage['sofa.captcha.token']` e scade in ~10 minuti. ⚠️ Senza, la
paginazione **si tronca in silenzio**: la prima raccolta si era fermata a 240
partite su 470 senza un errore.
