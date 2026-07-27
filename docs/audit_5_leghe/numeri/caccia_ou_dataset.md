# Caccia al dato vero — quote O/U 2.5 di CHIUSURA, 2017-18 e 2018-19, 5 leghe

*Nota di lettura: i numeri di questa nota sono tutti in
`docs/audit_5_leghe/numeri/caccia_ou_dataset.json` e ricalcolabili con gli script elencati in
fondo. Nessun numero è stato scritto a mano.*

---

## 0 · L'aspettativa, dichiarata prima di guardare

**Attesa: esito negativo.** Il buco è strutturale nella fonte a monte
(football-data.co.uk raccoglie due istantanee apertura/chiusura solo dal
2019/20) e le vie note erano già chiuse: 6 dataset Kaggle verificati uno per
uno (tutti riesportazioni di football-data), BetExplorer che ha ritirato il
confronto quote per le partite di ~8 anni fa, Sofascore e fbref a 403.

**Esito effettivo: POSITIVO.** Trovata e validata una fonte che copre
**3.652 partite su 3.652 (100%)**.

**Perché l'attesa era sbagliata — e non per il motivo che pensavo.** Il mandato
diceva "le leghe nuove non sono mai state cercate, è informazione nuova". Non è
quello che ha fatto la differenza: il buco su Bundesliga e Ligue 1 è identico
(verificato per primo, vedi §1). Ha fatto la differenza il fatto che tutte le
ricerche precedenti erano impostate sull'asse *«chi riesporta football-data»*.
La fonte trovata pubblica un book — **1xBet** — che in football-data **non c'è
affatto**, e mercati che lì non esistono (linee 0.5/1.5/3.5/4.5, GG/NG): per
costruzione non poteva comparire in quelle ricerche.

---

## 1 · Prima cosa fatta: il buco esiste davvero anche su D1 e F1?

Sì, identico. Ispezione diretta dei 4 file grezzi già versionati
(`data/fonti/football_data/{bundesliga,ligue_1}_{1718,1819}.csv`):

```
… BbOU, BbMx>2.5, BbAv>2.5, BbMx<2.5, BbAv<2.5, BbAH, … , PSCH, PSCD, PSCA
```

Una sola istantanea O/U (la media Betbrain pre-match = **apertura**, già negli
snapshot come `odds_over25_open`) e nessuna colonna di chiusura O/U. Le colonne
`B365C>2.5, PC>2.5, MaxC>2.5, AvgC>2.5` compaiono solo da `*_1920.csv`.

→ Il buco è una proprietà **della finestra temporale della fonte**, non della
lega. Il bersaglio è di **3.652 celle**, non 2.280.

---

## 2 · La fonte trovata

**footiqo.com — "Football Database", tab *Odds*.**
Esempio: <https://footiqo.com/database/leagues/germany-bundesliga/>

Il sito dichiara: *«historical match data and **closing odds** … Odds are
sourced from **1xBet**»*, con stagioni dal 2015/16 a oggi e un bottone di
**Export CSV/Excel** su ogni tabella. Le colonne sono
`xbetClose1FT/XFT/2FT`, `xbetCloseOver05…Over45`, `xbetCloseUnder05…Under45`,
`xbetCloseBTTSY/N`.

Sotto il cofano è un `wpDataTables` in server-side processing: i dati arrivano
da un POST a `wp-admin/admin-ajax.php?action=get_wdtable&table_id=<id>` con un
filtro di colonna sulla `Season`. `robots.txt` **permette esplicitamente**
`/wp-admin/admin-ajax.php`. Throttle usato: 1,8 s, ~200 richieste in totale.

**Scaricato davvero e ispezionato**, non creduto sulla parola: 5 leghe ×
{2017/18, 2018/19, 2019/20}. Conteggi: 380/380/380/306/380 per stagione — e
**Ligue 1 2019/20 = 279 righe**, cioè l'esatto troncamento COVID a 28 giornate.
Un dataset ricostruito a tavolino avrebbe avuto 380 righe.

---

## 3 · I sette criteri di accettazione, uno per uno

| # | criterio | esito | numero |
|---|---|---|---|
| C1 | linea esattamente 2.5 | **PASS** | colonna dedicata, linee 0.5/1.5/2.5/3.5/4.5 separate |
| C2 | quote decimali > 1.0 | **PASS** | 0 violazioni su 3.652; over ∈ [1.10, 3.24], under ∈ [1.37, 6.45] |
| C3 | apertura ≠ chiusura | **PASS** | coincidono nello **0,03%** delle righe (1 su 3.643) |
| C4 | overround > 1 su ogni riga | **PASS** | 0 violazioni; medio **1.027**, p01 1.0086, p99 1.0637 |
| C5 | copertura ≥ 95% per (lega, stagione) | **PASS** | **100% su tutte e 10** |
| C6 | scrape reale, non ricostruzione | **PASS** | vedi §4 |
| C7 | join per data + squadre | **PASS** | **3.652/3.652**, delta-data 0 giorni ovunque, 7 alias |
| +C8 | *(protocollo INGRESSO)* gol fonte == gol snapshot | **PASS** | **3.652/3.652 identici** |

C3 merita una precisazione onesta: footiqo dà **solo** la chiusura. Il criterio
si verifica confrontandola con l'apertura reale che già abbiamo (`BbAv`), ed è
proprio così che deve essere — l'apertura non ci serve, ci serve la chiusura.

C8 non era nei sette criteri ma è richiesto dal protocollo di INGRESSO del
progetto: ho scaricato anche la tabella *Scores* della stessa fonte e
confrontato i gol riga per riga.

---

## 4 · Il lavoro vero: provare a dimostrare che è FALSA

Passare i criteri non basta. Tre ipotesi alternative, tutte con un test.

### H1 — «è l'apertura rietichettata» → **RESPINTA**
Coincide con `BbAv` nello 0,03% delle righe; overround 1.027 contro 1.056.

### H2 — «è una ricostruzione da modello» → **RESPINTA**

È l'ipotesi seria: la stima E3 *del progetto stesso* raggiunge correlazione
0,75–0,86 col movimento vero della linea partendo dal solo movimento 1X2. Un
modello **può** somigliare a una chiusura.

Il test decisivo sfrutta una cosa che nel 2017-19 **abbiamo già come dato
reale**: l'1X2 di apertura *e* di chiusura (Pinnacle `PSH→PSCH`). footiqo
pubblica anche il proprio 1X2 di chiusura. Se è una fotografia scattata davvero
all'ora di chiusura, deve somigliare alla chiusura vera più che all'apertura
vera — **dentro la finestra bersaglio**, non per estrapolazione.

Su 3.645 partite:

| confronto (p_home devigata) | correlazione |
|---|---|
| footiqo vs **CHIUSURA** vera | **0.9976** |
| footiqo vs **APERTURA** vera | 0.9897 |
| movimento footiqo vs movimento vero | **0.881** (home), 0.861 (X), 0.870 (away) |

E il log-loss 1X2 cade esattamente dove deve:
apertura vera **0.9548** → footiqo **0.9533** → chiusura vera **0.9523**.

**La calibrazione del test** (perché 0.9976 da solo non dice nulla): quanto si
assomigliano *due book veri*?

| coppia | corr |
|---|---|
| B365 vs VC (stesso istante) | 0.99869 |
| B365 vs WH | 0.99819 |
| VC vs WH | 0.99859 |
| Pinnacle **apertura** vs Pinnacle **chiusura** | 0.98977 |
| **footiqo vs Pinnacle chiusura** | **0.99758** |
| **footiqo vs Pinnacle apertura** | **0.98974** |

footiqo sta rispetto alla chiusura vera come un book sta rispetto a un altro
book **allo stesso istante**, e sta rispetto all'apertura vera *esattamente*
come la chiusura sta rispetto all'apertura (0.98974 contro 0.98977). **È
collocato all'ora di chiusura.** Un modello costruito per ricostruire la sola
O/U non avrebbe ragione di riprodurre anche il movimento 1X2 partita per
partita.

Due firme aggiuntive:

- **margine**: 1X2 a 1.0269, che non coincide con nessun book di football-data
  nelle stesse partite (B365 1.0476, BW 1.0514, IW 1.0573, WH 1.0567,
  VC 1.0370, BbAv 1.0489, Pinnacle 1.0249/1.0247);
- **reticolo di prezzo**: l'ultima cifra decimale di footiqo è fortemente non
  uniforme (**30,5%** finisce per 0, 14,0% per 4) — tipico di un book retail.
  Pinnacle è quasi uniforme (12,6 / 9,7 / 9,6 / …), e così sarebbe una media
  multi-book **o l'output di un modello**.
- la scaletta O/U è monotona su **tutte** le 3.493 righe complete.

### H3 — «è comunque inutile, non batte ciò che abbiamo» → **PARZIALMENTE ACCOLTA**

È il risultato più onesto della caccia. Log-loss binaria O/U 2.5 contro l'esito
reale, bootstrap appaiato B=10.000 (`_fase52_common.boot`, seed 20260725):

| confronto | n | log-loss | Δ | CI95 | conclusivo? |
|---|--:|---|---|---|---|
| footiqo vs **apertura reale** | 3.643 | 0.6693 vs 0.6716 | **−0.00229** | [−0.00423, −0.00035] | **SÌ** |
| footiqo vs **stima E3** | 2.279 | 0.6750 vs 0.6752 | −0.00021 | [−0.00278, +0.00243] | **NO** |

Contro l'apertura il dato vero vince, con CI conclusivo. **Contro la stima E3
del progetto no: sono indistinguibili.** La stima era davvero buona, come le
Fasi 72/73 avevano concluso — e va detto.

---

## 5 · Il limite più importante da dichiarare

**È la chiusura di UN book, non la chiusura del mercato medio.** Dal 2019/20 in
poi gli snapshot usano la chiusura di football-data (media multi-book). Mettere
1xBet nel 2017-19 crea una **rottura di regime nella stessa colonna**.

Misurato dove esistono entrambe (2019/20, 1.687 partite):

| | MAE vs chiusura media |
|---|---|
| 1xBet chiusura, grezzo | **0.0156** |
| apertura (per riferimento) | 0.0206 |
| **stima E3 del progetto** | **~0.012** *(dichiarato in `data/estimates/README.md`)* |
| 1xBet dopo ricalibrazione logit *(in-sample, ottimistica)* | 0.0122 |

Bias medio +0.0088 verso l'Over (overround 1.035 contro 1.054); per lega da
+0.0039 (Ligue 1) a +0.0108 (Premier).

**Come proxy della chiusura media di mercato, il dato grezzo è *peggiore* della
stima.** Il suo vantaggio è di natura diversa: è un **prezzo reale** — quindi
ammesso dove il protocollo vieta le stime (simulazioni ROI/CLV) — e copre
**Bundesliga e Ligue 1, 1.373 partite dove nessuna stima esiste**.

---

## 6 · Il ritrovamento collaterale, forse più importante del bersaglio

`CLAUDE.md` §1.8: *«il GG/NG non ha quote nei dati (football-data non le
include), quindi è l'unico mercato dove non possiamo dimostrare l'efficienza
del mercato — l'unico con "spazio" non ancora chiuso. Priorità lì.»*

**Quelle quote esistono, e sono qui: `xbetCloseBTTSY/N`, copertura 100% su
tutte e 3.652 le partite bersaglio.** Primo numero, mai calcolato prima nel
progetto:

- log-loss del mercato GG devigato: **0.6852**
- log-loss della baseline costante: 0.6928
- overround 1.0433, frequenza GG osservata 0.514

Il mercato batte la baseline. La domanda *«il nostro GG/NG batte il mercato?»*
diventa per la prima volta rispondibile, su 3.652 partite e 5 leghe. **Non l'ho
testato**: è materiale per una fase a sé.

In dote arrivano anche le linee **1.5 e 3.5 al 100%**, la 4.5 al 99,9% e la 0.5
al 95,8% — mercati Tier 1 che oggi il progetto deriva solo per modello.

---

## 7 · Le altre piste, e perché sono state scartate

| pista | esito | motivo |
|---|---|---|
| [iredchuk/soccer-bookmaker-odds](https://github.com/iredchuk/soccer-bookmaker-odds) (5 leghe, 2005-06→2018-19, CSV committati) | scartata | **solo 1X2**, nessuna linea O/U; quote medie senza apertura/chiusura |
| [win-1x2.com → odds-office.com](https://www.win-1x2.com/quotenarchive.html), archivio Betfair tedesco | scartata | i `.xls` liberi hanno *last-modified* 21/02/2014 → arrivano al 2013. L'archivio aggiornato (`Odds-Analyse-23-Ligen.7z`, ago 2024) **scaricato**: è **protetto da password**, la consegna richiede di contattare l'autore. Non chiusa in assoluto — non percorribile senza contatto umano. |
| [oddalerts.com/downloads](https://www.oddalerts.com/downloads) | non verificabile | 403 sia da WebFetch sia da curl con UA browser; non forzato |
| [the-odds-api](https://the-odds-api.com/historical-odds-data/) | scartata | storico **dal 6 giugno 2020**, solo piani a pagamento: il 2017-19 non esiste |
| Hugging Face datasets | scartata | `hub_repo_search` non restituisce alcun dataset pertinente |
| GitHub code search CSV con chiusura O/U | scartata | `"AvgC>2.5" extension:csv` dà moltissimi risultati, ma **quella colonna esiste solo dal 2019/20**: tutte riesportazioni di football-data |
| Zenodo / OSF / figshare / dataverse | scartata | nulla di nuovo (Whelan & Hegarty 2024 copre 1X2 e handicap asiatico) |
| archivi francesi (footamax) e tedeschi (fussballwitwe, sportwettennerd) | scartata | archivi di **risultati** o pagine editoriali; rimandano tutti a OddsPortal |
| OddsPortal storico | **non tentato per scelta** | `robots.txt` vieta esplicitamente `*-2017*`, `*-2018*`. Nessuna richiesta, nessun aggiramento via cache/archive. |
| Kaggle (6 dataset), BetExplorer | già chiuse | riesportazioni di football-data / funzione ritirata |

---

## 8 · Come si farebbe il join, esattamente

- **chiave**: `(lega, stagione, home_team, away_team)`, nomi passati per
  `src.data.sources.canonical_team`;
- **verifica 1**: `matchDate` di footiqo (`dd-mm-yy HH:MM`) contro `date` dello
  snapshot → **delta 0 giorni su tutte e 3.652 le righe**;
- **verifica 2**: gol della tabella *Scores* contro `home_goals/away_goals` →
  **3.652/3.652 identici**;
- **7 alias da aggiungere** (differenze puramente ortografiche):
  `Manchester Utd→Man United`, `Atl. Madrid→Ath Madrid`,
  `Dep. La Coruna→La Coruna`, `B. Monchengladbach→M'gladbach`,
  `Schalke→Schalke 04`, `Dusseldorf→Fortuna Dusseldorf`, `PSG→Paris SG`;
- **colonne**: `xbetCloseOver25 → odds_over25`, `xbetCloseUnder25 →
  odds_under25`, **solo** stagioni `1718` e `1819`;
- **avvertenza obbligatoria**: se entrano nelle colonne di chiusura degli
  snapshot va scritto in `docs/DATI.md` che nel 2017-19 la chiusura O/U è
  1xBet e dal 2019/20 è la media multi-book — due definizioni nella stessa
  colonna. Alternative: colonne dedicate (`odds_over25_close_1xbet`) oppure
  ricalibrazione logit con coefficienti stimati **fuori campione**.

---

## 9 · Nota legale ed etica (da leggere prima di usare i dati)

- `footiqo.com/robots.txt` vieta solo `/wp-admin/` e **permette esplicitamente**
  `/wp-admin/admin-ajax.php`, l'endpoint usato. Throttle 1,8 s.
- Il sito offre di suo l'**Export CSV/Excel** e dichiara *«Can I download the
  data? Yes»*: il download è previsto.
- **⚠️ Redistribuzione.** I *Terms of Use* (par. 8) dicono: *«You may not copy,
  reproduce or redistribute content without our prior written permission,
  except as permitted by fair dealing»*; il par. 9 vieta lo *«scraping at
  abusive rates»* (rispettato). **Conseguenza operativa**: i grezzi restano nel
  repo privato di lavoro; **prima di qualunque pubblicazione o
  ridistribuzione serve il permesso scritto**. Il sito invita al contatto:
  chiederlo è il passo corretto se il dato deve diventare parte pubblica del
  progetto.
- `oddsportal.com` storico: **vietato dal suo robots.txt, non toccato**.

---

## 10 · Raccomandazione

La pista è **aperta** e il dato **c'è al 100%**. Ma sostituire la stima E3 col
dato vero **non è una decisione automatica**: contro l'esito reale i due sono
indistinguibili (Δ −0.0002, CI non conclusivo) e il dato vero cambia
definizione di "chiusura" a metà serie storica.

Il guadagno **certo** è altrove:

1. **Bundesliga e Ligue 1** — 1.373 partite dove nessuna stima esiste;
2. è un **prezzo reale**, ammesso dove il protocollo vieta le stime;
3. porta in dote **GG/NG e le linee 1.5/3.5/4.5 di chiusura** — e il GG/NG è il
   mercato che il progetto dichiara "senza quote nei dati", l'unico dove
   l'efficienza del mercato non era mai stata verificabile.

---

## File prodotti

**Grezzi** (`data/ricerca_esterna/`): `footiqo_{lega}_{stagione}.json` (15
file: 5 leghe × 2017-2018 / 2018-2019 / 2019-2020), `footiqo_gol_{lega}_{stagione}.json`
(10 file, controllo gol), `footiqo_manifest.json` (URL, timestamp, sha256, conteggi).

**Script riproducibili** (`data/ricerca_esterna/`):
`_fetch_footiqo.py` (quote) · `_fetch_footiqo_gol.py` (gol) ·
`_valida_footiqo.py` (criteri C1-C8 + confutazioni A/B/C) ·
`_confuta_footiqo.py` (confutazioni D/E/F, le decisive).

**Risultati**: `validazione_footiqo.json`, `confutazione_footiqo.json`,
`confutazione_footiqo_G.json`, `scarto_book_2019_20.json`,
`ricalibrazione_book_2019_20.json`.

**Questa nota**: `docs/audit_5_leghe/numeri/caccia_ou_dataset.md` + `docs/audit_5_leghe/numeri/caccia_ou_dataset.json`.
