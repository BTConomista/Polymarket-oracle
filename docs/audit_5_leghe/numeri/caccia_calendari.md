# Caccia al dato VERO — le partite di coppa mancanti nei calendari di club

> Lavoro di cantiere (regola R4: nessuno snapshot, nessun file di `src/`, `data/`,
> `docs/`, `scripts/` è stato modificato). Prodotto da `caccia_calendari.py`
> (sorgente in appendice); dati grezzi in `cantiere/out/caccia_calendari.json`;
> calendari recuperati in `cantiere/data/ricerca/fixtures_*.csv`.

## 0. In una riga

Il buco c'è, è **molto più grande di quello ipotizzato**, e non è solo una lacuna
di copertura: c'è anche un **filtro sbagliato nel nostro codice** (il Monaco) e
**8 date sbagliate** nella fonte attuale. Ho recuperato **3045 righe di
calendario** da Wikipedia, verificate con una terza fonte indipendente, che
toccano **dal 5,8% al 12,6% delle righe degli snapshot**.

## 1. Aspettative dichiarate PRIMA di guardare i numeri

| # | aspettativa | esito |
|---|---|---|
| 1 | Europa/Conference League 2025-26 assenti per tutte e 5 le leghe | **confermata** |
| 2 | DFB-Pokal assente 2016-17 e 2017-18 | **parzialmente**: 2017-18 sì (80 righe), ma mancano righe anche in 5 stagioni su 9 dove il file *c'è* |
| 3 | Coupe de France presente solo nel 2024-25 | **confermata** (636 righe mancanti sulle altre 8 stagioni) |
| 4 | Champions League "presente ovunque" | **SMENTITA**: mancano i turni preliminari fino al 2023-24 e **tutta l'Europa del Monaco** |
| 5 | impatto piccolo, valore = correttezza | **SMENTITA sul piano quantitativo**: il midweek_europe passa da 5,0-13,6% a 12,0-17,3% delle celle |

## 2. Metodo

1. **Censimento** dei 5 calendari attuali (`club_fixtures*.csv`).
2. **Verità indipendente**: per ogni competizione rilevante 2017-18 → 2025-26 ho
   scaricato il *wikitext* delle pagine Wikipedia (API `action=parse`) e ho
   estratto ogni template `{{Football box}} / {{#invoke:Football box|main}}`,
   seguendo le trasclusioni `{{#lst:...}}` (i turni preliminari UEFA vivono su
   sotto-pagine). **362 pagine utili, 13.289 partite grezze.**
   Le partite UEFA sono filtrate per **codice paese** (`{{fbaicon|ITA}}`…), che è
   il campo autorevole; le coppe nazionali per aggancio del nome squadra.
3. **Confronto** riga per riga su `(squadra, data)`: il censimento delle lacune è
   **misurato contro una fonte esterna**, non asserito.
4. **Controlli obbligatori** (§4) e **quantificazione dell'impatto** ricalcolando
   `fixtures.add_rest_days_full` con e senza il recupero.
5. **Confutazione** con una **terza fonte** (openligadb.de).

**Fonti scartate per motivi legali/tecnici** (aggiornamento della tabella di R6,
passo 3): `transfermarkt.com` ha nel `robots.txt` `User-agent: ClaudeBot →
Disallow: /` (e idem `anthropic-ai`, `Claude-SearchBot`): **non si scrape**, anche
se sarebbe la fonte ideale (calendario per-squadra multi-competizione).
`worldfootball.net` risponde **403** (Cloudflare). `oddsportal` resta vietato per
lo storico. Wikipedia è invece esplicitamente aperta alle API ed è in CC BY-SA.

## 3. Che cosa manca davvero (censimento misurato)

Righe di calendario che **esistono nella realtà e non sono nei nostri file**
(unità = una riga per squadra-partita, come in `club_fixtures`):


**Serie A**

| competizione | 1718 | 1819 | 1920 | 2021 | 2122 | 2223 | 2324 | 2425 | 2526 | TOT |
|---|---|---|---|---|---|---|---|---|---|---|
| Coppa Italia | 72 | 77 | 80 | 11 | 7 | 3 | 9 | 0 | 67 | 326 |
| Europa League | 36 | 30 | 27 | 3 | 0 | 0 | 0 | 0 | 24 | 120 |
| Supercoppa Italiana | 2 | 2 | 2 | 2 | 2 | 2 | 4 | 4 | 4 | 24 |
| Conference League | 0 | 0 | 0 | 0 | 2 | 2 | 2 | 0 | 12 | 18 |
| FIFA Club World Cup | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 8 | 0 | 8 |
| Champions League | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| UEFA Super Cup | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 |

**Premier League**

| competizione | 1718 | 1819 | 1920 | 2021 | 2122 | 2223 | 2324 | 2425 | 2526 | TOT |
|---|---|---|---|---|---|---|---|---|---|---|
| EFL Cup | 89 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 79 | 168 |
| FA Cup | 84 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 79 | 163 |
| Europa League | 24 | 36 | 37 | 3 | 0 | 0 | 0 | 0 | 31 | 131 |
| Conference League | 0 | 0 | 0 | 0 | 2 | 2 | 2 | 0 | 15 | 21 |
| FA Community Shield | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 18 |
| FIFA Club World Cup | 0 | 0 | 2 | 0 | 2 | 0 | 2 | 9 | 2 | 17 |
| UEFA Super Cup | 1 | 0 | 2 | 0 | 1 | 0 | 1 | 0 | 1 | 6 |
| Champions League | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |

**La Liga**

| competizione | 1718 | 1819 | 1920 | 2021 | 2122 | 2223 | 2324 | 2425 | 2526 | TOT |
|---|---|---|---|---|---|---|---|---|---|---|
| Copa del Rey | 113 | 115 | 93 | 9 | 8 | 7 | 9 | 0 | 99 | 453 |
| Europa League | 39 | 44 | 33 | 5 | 0 | 0 | 0 | 0 | 26 | 147 |
| Supercopa de Espana | 4 | 2 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 34 |
| Conference League | 0 | 0 | 0 | 0 | 0 | 2 | 2 | 0 | 13 | 17 |
| FIFA Club World Cup | 2 | 2 | 0 | 0 | 0 | 2 | 0 | 8 | 1 | 15 |
| UEFA Super Cup | 1 | 2 | 0 | 1 | 1 | 1 | 1 | 1 | 0 | 8 |
| Champions League | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| FIFA Intercontinental Cup | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 |

**Bundesliga**

| competizione | 1718 | 1819 | 1920 | 2021 | 2122 | 2223 | 2324 | 2425 | 2526 | TOT |
|---|---|---|---|---|---|---|---|---|---|---|
| DFB-Pokal | 82 | 0 | 0 | 10 | 15 | 7 | 10 | 0 | 22 | 146 |
| Europa League | 30 | 34 | 36 | 4 | 0 | 0 | 0 | 0 | 27 | 131 |
| DFL-Supercup | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 18 |
| Conference League | 0 | 0 | 0 | 0 | 2 | 3 | 2 | 0 | 10 | 17 |
| FIFA Club World Cup | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 8 | 2 | 10 |
| Champions League | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| UEFA Super Cup | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 2 |

**Ligue 1**

| competizione | 1718 | 1819 | 1920 | 2021 | 2122 | 2223 | 2324 | 2425 | 2526 | TOT |
|---|---|---|---|---|---|---|---|---|---|---|
| Coupe de France | 78 | 81 | 79 | 72 | 85 | 79 | 86 | 0 | 76 | 636 |
| Coupe de la Ligue | 61 | 67 | 57 | 2 | 0 | 0 | 0 | 0 | 0 | 187 |
| Europa League | 39 | 28 | 18 | 2 | 0 | 0 | 0 | 0 | 30 | 117 |
| Champions League | 4 | 0 | 0 | 1 | 4 | 2 | 2 | 10 | 10 | 33 |
| Conference League | 0 | 0 | 0 | 0 | 2 | 2 | 2 | 0 | 12 | 18 |
| Trophee des Champions | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 18 |
| FIFA Club World Cup | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 3 | 7 |
| FIFA Intercontinental Cup | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| UEFA Super Cup | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |

### 3.1 Le tre scoperte che nessuno aveva notato

**(a) Il Monaco non è mai esistito in Europa, per noi.** `src/data/fixtures.py`
filtra le partite UEFA con `sources.UEFA_COUNTRY_CODE["ligue_1"] = "FRA"`, ma
openfootball etichetta l'AS Monaco `(MCO)` in una parte dei file (50 lati `FRA`
contro 20 `MCO` nel repo `openfootball/champions-league`, dal 2011-12). Risultato: **26 righe europee del Monaco su 54** non sono nel calendario — comprese
**intere campagne di Champions** (league phase 2024-25 e 2025-26 al completo).
Non è una lacuna della fonte: è un **bug del nostro filtro**. Per stagione:
`{'1718': 7, '1819': 6, '1920': 5, '2021': 6, '2122': 9, '2223': 3, '2324': 3, '2425': 11, '2526': 13}`.

**(b) Le coppe nazionali sono incomplete anche dove il file esiste.**
Non è vero che «c'è» o «non c'è»: la Coppa Italia 2020-21 → 2023-24 ha il file e
mancano comunque 11/7/3/9 righe; la DFB-Pokal ne perde
10/15/7/10 nelle stesse stagioni; la Copa del Rey
9/8/7/9. Complessivamente il nostro calendario copre
**324/650** righe di Coppa Italia, **482/935** di Copa del Rey,
**82/715** di Coupe de France.

**(c) Ci sono competizioni che non abbiamo MAI modellato.** Non sono lacune di
openfootball: nessuno le ha mai chieste. Sono tutte partite ufficiali di prima
squadra, quasi tutte infrasettimanali:
Supercoppa Italiana (24 righe), Supercopa de España (34), FA Community Shield (18),
DFL-Supercup (18), Trophée des Champions (18), UEFA Super Cup (18 in totale),
FIFA Club World Cup (57), FIFA Intercontinental Cup (2) e — la più pesante —
la **Coupe de la Ligue** francese, 187 righe nelle tre stagioni 2017-18/2019-20
in cui si è giocata (poi abolita).

E i **turni preliminari UEFA**: `clq/elq/confq` esistono su openfootball solo dal
2024-25, quindi ogni play-off d'agosto prima di allora è invisibile (è il caso da
manuale: Milan-Shkëndija il 24/8/2017, tre giorni prima di Milan-Cagliari).

### 3.2 Quello che invece NON è un buco (verificato, non assunto)

- **Spareggi promozione/retrocessione, barrage, Relegation, playoff di Serie B /
  Championship / Segunda**: si giocano *dopo* l'ultima giornata. La pausa estiva
  più corta misurata su 5 leghe × 8 transizioni è di **48 giorni**
  (Serie A e Premier, estate COVID 2020) contro un `cap` di 14: qualunque partita
  di spareggio è già oltre il cap, quindi **non può cambiare `rest_days_full`**
  né `midweek_europe`. Nessun recupero necessario.
- **Seconde serie 2025-26 assenti**: è voluto (`_prelude_rows` carica la seconda
  serie solo per `1617..penultima`, perché serve a radicare il riposo delle
  neopromosse *prima* del loro esordio).
- **FIFA Club World Cup 2025** (14 giugno-13 luglio 2025): recuperata (46 righe),
  ma cade 33-70 giorni prima dell'inizio del 2025-26 → **impatto nullo**, come
  atteso col `cap` a 14 giorni. Le edizioni **invernali** (dicembre 2017/2018/2019/2023,
  febbraio 2022/2023) invece cadono in piena stagione: sono 11 righe, con effetto
  piccolo ma non nullo (1 riga di snapshot toccata in Liga, 3+3 celle di rest fra
  Premier e Liga).

## 4. Controlli obbligatori — esito

| controllo | esito |
|---|---|
| nomi squadra non agganciati (competizioni UEFA, dove il paese è certo) | **0 su 5 leghe** |
| squadre con due partite lo stesso giorno dopo il merge | **0 su 5 leghe** |
| date fuori dalla finestra della stagione (> 60 gg) | **0** (le 6 righe delle super-coppe di agosto 2026 sono state **scartate**: sono già 2026-27) |
| squadra non in quella lega in quella stagione | 608 righe — **atteso e corretto**: sono club di seconda serie (es. Lecce in Coppa Italia 2017-18) che il builder di produzione tratta allo stesso modo |
| doppioni interni prima del dedup | 1 (Amiens, 2021-11-27: due turni di Coupe de France nello stesso giorno sulla pagina) |

**Aggancio dei nomi.** 2908 righe si agganciano
con `sources.canonical_team` senza toccare nulla. Le uniche eccezioni, **elencate
una per una e mai applicate in silenzio**, sono 14 club:

- *proposta esplicita* (alias scritto a mano nello script): Alaves, Almeria,
  Cadiz, Leganes, Malaga, Darmstadt, Greuther Furth, Heidenheim, Nimes,
  St Etienne — più i nomi lunghi già coperti (`Internazionale`→Inter,
  `Manchester United`→Man United, `Atlético Madrid`→Ath Madrid, …);
- *chiave normalizzata* (match univoco dopo rimozione di accenti e sigle):
  Paderborn, Amiens, Lyon, Strasbourg.

Tutte e 14 sono verificabili a occhio; nessuna è ambigua. **Nessun alias è stato
scritto in `sources.TEAM_ALIASES`**: vivono solo nello script e nella colonna
`metodo_nome` dei CSV prodotti.

## 5. Impatto quantificato (nessuno snapshot è stato modificato)

Ricalcolo di `fixtures.add_rest_days_full` sullo snapshot, con e senza le righe
recuperate. `cap=14`, `europe_window=4` (i default di produzione).

| lega | partite | righe agg. | righe toccate (midweek 0→1) | % righe | midweek prima % | midweek dopo % | celle rest cambiate | % celle rest | Δrest medio (gg) | Δrest max |
|---|---|---|---|---|---|---|---|---|---|---|
| Serie A | 3420 | 499 | 220 | 6.43 | 8.57 | 12.02 | 367 | 5.37 | 4.545 | 11 |
| Premier League | 3420 | 526 | 216 | 6.32 | 13.58 | 17.25 | 355 | 5.19 | 4.499 | 11 |
| La Liga | 3420 | 677 | 362 | 10.58 | 10.22 | 16.86 | 527 | 7.7 | 4.37 | 11 |
| Bundesliga | 2754 | 326 | 159 | 5.77 | 12.07 | 15.34 | 221 | 4.01 | 4.774 | 10 |
| Ligue 1 | 3097 | 1017 | 391 | 12.63 | 5.02 | 12.8 | 675 | 10.9 | 5.188 | 11 |

**Come si legge.** «righe toccate» = partite dello snapshot in cui almeno una
delle due squadre passa da `midweek_europe = 0` a `1`: **è lo zero che sembrava
un'informazione e non lo era.** «Δrest medio» = di quanto il calendario attuale
**sovrastima** il riposo, sulle sole celle che cambiano (il segno è sempre
positivo per costruzione: aggiungere partite può solo accorciare l'intervallo).

CI95 bootstrap appaiato B=10.000 sul Δrest medio (seed 20260725):
Serie A 4.545 [4.373, 4.728], Premier League 4.499 [4.310, 4.693], La Liga 4.370 [4.216, 4.531], Bundesliga 4.774 [4.575, 4.977], Ligue 1 5.188 [5.015, 5.363].
Tutti **conclusivi** (non attraversano lo zero) — ma va detto con onestà che qui
il CI misura solo la dispersione campionaria di una media su celle: il **conteggio**
delle righe toccate è un censimento **esatto**, non una stima, e non ha CI.

Escludendo super-coppe e Mondiale per club (cioè restando alle sole coppe
nazionali + Europa, semanticamente identiche a quello che il builder già fa):

| lega | righe agg. | righe toccate | % righe | celle rest | Δrest medio |
|---|---|---|---|---|---|
| Serie A | 466 | 216 | 6.32 | 346 | 4.512 |
| Premier League | 485 | 211 | 6.17 | 330 | 4.285 |
| La Liga | 619 | 354 | 10.35 | 508 | 4.278 |
| Bundesliga | 296 | 154 | 5.59 | 207 | 4.691 |
| Ligue 1 | 990 | 388 | 12.53 | 660 | 5.147 |

### 5.1 Chi contribuisce all'impatto


**Serie A**

| competizione | righe | righe toccate (midweek) | celle rest cambiate |
|---|---|---|---|
| Coppa Italia | 326 | 102 | 225 |
| Europa League | 120 | 98 | 103 |
| Supercoppa Italiana | 24 | 4 | 22 |
| Conference League | 18 | 18 | 18 |
| Champions League | 2 | 1 | 2 |
| UEFA Super Cup | 1 | 0 | 1 |
| FIFA Club World Cup | 8 | 0 | 0 |

**Premier League**

| competizione | righe | righe toccate (midweek) | celle rest cambiate |
|---|---|---|---|
| Europa League | 131 | 106 | 110 |
| EFL Cup | 168 | 64 | 108 |
| FA Cup | 163 | 20 | 102 |
| Conference League | 21 | 19 | 19 |
| FA Community Shield | 18 | 0 | 16 |
| UEFA Super Cup | 6 | 5 | 6 |
| FIFA Club World Cup | 17 | 0 | 3 |
| Champions League | 2 | 2 | 2 |

**La Liga**

| competizione | righe | righe toccate (midweek) | celle rest cambiate |
|---|---|---|---|
| Copa del Rey | 453 | 212 | 356 |
| Europa League | 147 | 127 | 134 |
| Conference League | 17 | 15 | 16 |
| Supercopa de Espana | 34 | 2 | 14 |
| UEFA Super Cup | 8 | 4 | 8 |
| FIFA Club World Cup | 15 | 1 | 3 |
| Champions League | 2 | 1 | 2 |
| FIFA Intercontinental Cup | 1 | 1 | 1 |

**Bundesliga**

| competizione | righe | righe toccate (midweek) | celle rest cambiate |
|---|---|---|---|
| Europa League | 131 | 104 | 113 |
| DFB-Pokal | 146 | 35 | 77 |
| Conference League | 17 | 16 | 16 |
| DFL-Supercup | 18 | 3 | 13 |
| Champions League | 2 | 2 | 2 |
| UEFA Super Cup | 2 | 2 | 2 |
| FIFA Club World Cup | 10 | 0 | 0 |

**Ligue 1**

| competizione | righe | righe toccate (midweek) | celle rest cambiate |
|---|---|---|---|
| Coupe de France | 635 | 162 | 409 |
| Coupe de la Ligue | 187 | 82 | 124 |
| Europa League | 117 | 102 | 111 |
| Champions League | 33 | 29 | 31 |
| Trophee des Champions | 18 | 2 | 18 |
| Conference League | 18 | 16 | 16 |
| UEFA Super Cup | 1 | 1 | 1 |
| FIFA Club World Cup | 7 | 0 | 0 |
| FIFA Intercontinental Cup | 1 | 0 | 0 |

## 6. Confutazione — ho provato a dimostrare che il recupero è sbagliato

**Test.** Prendo una terza fonte **indipendente** sia da openfootball sia da
Wikipedia: l'API pubblica **openligadb.de** (DFB-Pokal). Se le date che ho
recuperato non combaciano, il metodo non regge.

| stagione | openligadb | openfootball (attuale) | recuperate | **recuperate NON confermate** | openfootball NON confermate |
|---|---|---|---|---|---|
| 2017-18 | 82 | 0 | 82 | **0** | 0 |
| 2020-21 | 78 | 68 | 10 | **0** | 0 |
| 2025-26 | 83 | 69 | 22 | **0** | **8** |

Su **114 righe recuperate** verificate contro la terza fonte, **zero** non
confermate; e in tutte e tre le stagioni l'insieme openligadb è **esattamente**
coperto da (openfootball ∪ recuperate). **Il tentativo di confutazione è fallito:
il recupero regge.**

Ma ha prodotto un risultato **contro il dato esistente**: nella DFB-Pokal 2025-26
openfootball data 8 partite del 2° turno al **2 dicembre 2025**, mentre Wikipedia
e openligadb concordano sul **3 dicembre**. Sono righe *già presenti* nel nostro
`club_fixtures_bundesliga.csv`, con la data sbagliata.

**Secondo tentativo di confutazione — dall'altra parte.** Ho cercato righe che
*noi* abbiamo e Wikipedia no (`solo_nostre`): su **2.626 righe di coppa nazionale
già presenti**, solo **12** non trovano riscontro (99,5% di accordo), e tutte e 12
hanno una spiegazione:
8 sono le date sbagliate qui sopra;
3 sono turni minori di Coupe de France 2024-25 che Wikipedia elenca in tabella e
non con un *football box* (openfootball è più ricco lì);
1 è Tottenham-Leyton Orient (EFL Cup 22/9/2020), **assegnata a tavolino** per COVID
e mai giocata — openfootball la elenca, Wikipedia no: qui ha ragione Wikipedia,
e per R1 («il dato è quello del campo») quella riga non dovrebbe esserci.

**Terzo controllo.** PSG-İstanbul Başakşehir di Champions: openfootball la data
**9/12/2020**, Wikipedia **8/12/2020**. Hanno ragione entrambe — la partita è
iniziata l'8, è stata **sospesa al 13'** (episodio razzista) e ripresa il 9.
**Non la propongo come recupero**: è un caso da istruire, non un buco.

## 7. Che cosa ho prodotto

**50 file** in `cantiere/data/ricerca/`, schema identico a
`club_fixtures` più due colonne di tracciabilità (`metodo_nome`, `pagina`):

`season, team, date, competition, home_away, opponent, metodo_nome, pagina`


- **Serie A** — 499 righe in 9 file: `fixtures_serie_a_champions_league_qual.csv`, `fixtures_serie_a_conference_league.csv`, `fixtures_serie_a_conference_league_qual.csv`, `fixtures_serie_a_coppa_italia.csv`, `fixtures_serie_a_europa_league.csv`, `fixtures_serie_a_europa_league_qual.csv`, `fixtures_serie_a_fifa_club_world_cup.csv`, `fixtures_serie_a_supercoppa_italiana.csv`, `fixtures_serie_a_uefa_super_cup.csv`
- **Premier League** — 526 righe in 10 file: `fixtures_premier_league_champions_league_qual.csv`, `fixtures_premier_league_conference_league.csv`, `fixtures_premier_league_conference_league_qual.csv`, `fixtures_premier_league_efl_cup.csv`, `fixtures_premier_league_europa_league.csv`, `fixtures_premier_league_europa_league_qual.csv`, `fixtures_premier_league_fa_community_shield.csv`, `fixtures_premier_league_fa_cup.csv`, `fixtures_premier_league_fifa_club_world_cup.csv`, `fixtures_premier_league_uefa_super_cup.csv`
- **La Liga** — 677 righe in 10 file: `fixtures_la_liga_champions_league_qual.csv`, `fixtures_la_liga_conference_league.csv`, `fixtures_la_liga_conference_league_qual.csv`, `fixtures_la_liga_copa_del_rey.csv`, `fixtures_la_liga_europa_league.csv`, `fixtures_la_liga_europa_league_qual.csv`, `fixtures_la_liga_fifa_club_world_cup.csv`, `fixtures_la_liga_fifa_intercontinental_cup.csv`, `fixtures_la_liga_supercopa_de_espana.csv`, `fixtures_la_liga_uefa_super_cup.csv`
- **Bundesliga** — 326 righe in 9 file: `fixtures_bundesliga_champions_league_qual.csv`, `fixtures_bundesliga_conference_league.csv`, `fixtures_bundesliga_conference_league_qual.csv`, `fixtures_bundesliga_dfb_pokal.csv`, `fixtures_bundesliga_dfl_supercup.csv`, `fixtures_bundesliga_europa_league.csv`, `fixtures_bundesliga_europa_league_qual.csv`, `fixtures_bundesliga_fifa_club_world_cup.csv`, `fixtures_bundesliga_uefa_super_cup.csv`
- **Ligue 1** — 1017 righe in 12 file: `fixtures_ligue_1_champions_league.csv`, `fixtures_ligue_1_champions_league_qual.csv`, `fixtures_ligue_1_conference_league.csv`, `fixtures_ligue_1_conference_league_qual.csv`, `fixtures_ligue_1_coupe_de_france.csv`, `fixtures_ligue_1_coupe_de_la_ligue.csv`, `fixtures_ligue_1_europa_league.csv`, `fixtures_ligue_1_europa_league_qual.csv`, `fixtures_ligue_1_fifa_club_world_cup.csv`, `fixtures_ligue_1_fifa_intercontinental_cup.csv`, `fixtures_ligue_1_trophee_des_champions.csv`, `fixtures_ligue_1_uefa_super_cup.csv`

## 8. Limiti — quello che resta fuori

1. **Non ho toccato nulla**: gli snapshot, `club_fixtures*.csv` e `src/` sono
   intatti. I CSV prodotti sono **materiale grezzo da integrare**, non dati
   ufficiali del progetto.
2. **Wikipedia non è una fonte primaria.** È verificata su tre stagioni di
   DFB-Pokal contro openligadb (0 errori su 114 righe) e concorda al 99,5% con
   openfootball dove entrambe coprono, ma per Coppa Italia/Copa del Rey/Coupe de
   France **non ho una terza fonte**: l'errore residuo lì non è misurato.
3. **Turni minori delle coppe nazionali**: dove Wikipedia usa tabelle invece dei
   *football box* (primi turni di Coupe de France, qualificazioni FA Cup) le
   partite sfuggono al parser. Non riguarda i club di prima divisione, che entrano
   nei turni successivi — ma per i club **retrocessi in seconda serie** in una
   data stagione qualche turno può mancare.
4. **L'etichetta `season`** delle righe recuperate è assegnata per prossimità alla
   finestra di campionato. Per le code COVID (agosto 2020) può non coincidere con
   l'etichetta che openfootball dà allo stesso file. **Non incide su nulla**:
   `add_rest_days_full` raggruppa per *squadra*, non per stagione.
5. **Il valore è la correttezza, non la predizione.** Il progetto ha già misurato
   che le variabili di congestione sono rumore (Fasi 4c-33). Questo lavoro non
   promette un guadagno predittivo: dice che una colonna che oggi afferma «non ha
   giocato in settimana» **lo afferma falsamente su 159-391 righe per lega**.
6. **Il buco è ancora aperto** su una cosa: il Monaco è un bug di codice, non di
   dati, e finché `UEFA_COUNTRY_CODE` non accetta anche `MCO` si ripresenterà a
   ogni ricostruzione del calendario.

## 9. Proposte (NON applicate — decide l'orchestratore)

1. **Bug del Monaco** — in `src/data/fixtures.py`/`sources.py`, accettare per
   `ligue_1` sia `FRA` sia `MCO` (o mappare `MCO → FRA` in un dizionario di
   equivalenze paese). È l'intervento con il miglior rapporto valore/rischio:
   una riga di codice, 26 righe di calendario recuperate senza scaricare nulla.
2. **Registro correzioni** (`cantiere/data/correzioni_dichiarate.csv`, regola R3):
   8 righe di data sbagliata nella DFB-Pokal 2025-26 — vedi §10.
3. **Wikipedia come fonte secondaria dichiarata** del calendario di club, con la
   procedura di questo script; da valutare insieme a un `robots`-check periodico.
4. Se e quando si integra: rivalutare se le competizioni «nuove» (super-coppe,
   Mondiale per club, Coupe de la Ligue) debbano contare come `midweek_europe`.
   Semanticamente sì (sono partite non-di-campionato), ma è una scelta da
   dichiarare, non da subire.

## 10. Righe candidate per il registro correzioni

Formato: lega / stagione / data / squadre / colonna / valore prima / valore dopo /
motivo / fonte. **Non applicate.** Riguardano `cantiere/data/club_fixtures_bundesliga.csv`
(non uno snapshot di partite):

| lega | stagione | squadra | colonna | prima | dopo | motivo | fonte |
|---|---|---|---|---|---|---|---|
| bundesliga | 2526 | Bayern Munich (DFB-Pokal, 2° turno) | date | 2025-12-02 | 2025-12-03 | data errata in openfootball | openligadb.de + Wikipedia, concordi |
| bundesliga | 2526 | Bochum (DFB-Pokal, 2° turno) | date | 2025-12-02 | 2025-12-03 | data errata in openfootball | openligadb.de + Wikipedia, concordi |
| bundesliga | 2526 | Darmstadt (DFB-Pokal, 2° turno) | date | 2025-12-02 | 2025-12-03 | data errata in openfootball | openligadb.de + Wikipedia, concordi |
| bundesliga | 2526 | Freiburg (DFB-Pokal, 2° turno) | date | 2025-12-02 | 2025-12-03 | data errata in openfootball | openligadb.de + Wikipedia, concordi |
| bundesliga | 2526 | Hamburg (DFB-Pokal, 2° turno) | date | 2025-12-02 | 2025-12-03 | data errata in openfootball | openligadb.de + Wikipedia, concordi |
| bundesliga | 2526 | Holstein Kiel (DFB-Pokal, 2° turno) | date | 2025-12-02 | 2025-12-03 | data errata in openfootball | openligadb.de + Wikipedia, concordi |
| bundesliga | 2526 | Stuttgart (DFB-Pokal, 2° turno) | date | 2025-12-02 | 2025-12-03 | data errata in openfootball | openligadb.de + Wikipedia, concordi |
| bundesliga | 2526 | Union Berlin (DFB-Pokal, 2° turno) | date | 2025-12-02 | 2025-12-03 | data errata in openfootball | openligadb.de + Wikipedia, concordi |

Caso aperto, **non** proposto come correzione: Tottenham-Leyton Orient
(EFL Cup, 22/9/2020) è nel nostro calendario ma non è mai stata giocata
(assegnata a tavolino per COVID). Per R1 andrebbe rimossa; va istruita a parte.

## 11. Riconciliazione globale per competizione

Righe `(squadra, data)` presenti su Wikipedia vs presenti da noi, su tutte le 9
stagioni (immune all'etichetta di stagione):

| lega | competizione | wikipedia | nostre | mancanti | solo_nostre |
|---|---|---|---|---|---|
| Serie A | Champions League | 313 | 311 | 2 | 0 |
| Serie A | Conference League | 79 | 61 | 18 | 0 |
| Serie A | Coppa Italia | 650 | 324 | 326 | 0 |
| Serie A | Europa League | 260 | 140 | 120 | 0 |
| Serie A | FIFA Club World Cup | 8 | 0 | 8 | 0 |
| Serie A | Supercoppa Italiana | 24 | 0 | 24 | 0 |
| Serie A | UEFA Super Cup | 1 | 0 | 1 | 0 |
| Premier League | Champions League | 399 | 397 | 2 | 0 |
| Premier League | Conference League | 77 | 56 | 21 | 0 |
| Premier League | EFL Cup | 727 | 560 | 168 | 1 |
| Premier League | Europa League | 268 | 137 | 131 | 0 |
| Premier League | FA Community Shield | 18 | 0 | 18 | 0 |
| Premier League | FA Cup | 760 | 597 | 163 | 0 |
| Premier League | FIFA Club World Cup | 17 | 0 | 17 | 0 |
| Premier League | UEFA Super Cup | 6 | 0 | 6 | 0 |
| La Liga | Champions League | 373 | 371 | 2 | 0 |
| La Liga | Conference League | 46 | 29 | 17 | 0 |
| La Liga | Copa del Rey | 935 | 482 | 453 | 0 |
| La Liga | Europa League | 277 | 130 | 147 | 0 |
| La Liga | FIFA Club World Cup | 15 | 0 | 15 | 0 |
| La Liga | FIFA Intercontinental Cup | 1 | 0 | 1 | 0 |
| La Liga | Supercopa de Espana | 34 | 0 | 34 | 0 |
| La Liga | UEFA Super Cup | 8 | 0 | 8 | 0 |
| Bundesliga | Champions League | 332 | 330 | 2 | 0 |
| Bundesliga | Conference League | 48 | 32 | 17 | 1 |
| Bundesliga | DFB-Pokal | 719 | 581 | 146 | 8 |
| Bundesliga | DFL-Supercup | 18 | 0 | 18 | 0 |
| Bundesliga | Europa League | 247 | 116 | 131 | 0 |
| Bundesliga | FIFA Club World Cup | 10 | 0 | 10 | 0 |
| Bundesliga | UEFA Super Cup | 2 | 0 | 2 | 0 |
| Ligue 1 | Champions League | 235 | 203 | 33 | 1 |
| Ligue 1 | Conference League | 58 | 40 | 18 | 0 |
| Ligue 1 | Coupe de France | 715 | 82 | 636 | 3 |
| Ligue 1 | Coupe de la Ligue | 187 | 0 | 187 | 0 |
| Ligue 1 | Europa League | 231 | 114 | 117 | 0 |
| Ligue 1 | FIFA Club World Cup | 7 | 0 | 7 | 0 |
| Ligue 1 | FIFA Intercontinental Cup | 1 | 0 | 1 | 0 |
| Ligue 1 | Trophee des Champions | 18 | 0 | 18 | 0 |
| Ligue 1 | UEFA Super Cup | 1 | 0 | 1 | 0 |

## 12. Come rifare tutto

```bash
python caccia_calendari.py     # scarica (con cache su disco), confronta, scrive
python scrivi_md.py            # rigenera questo report dal JSON
```

Lo script è **idempotente** e mette in cache il wikitext: la seconda esecuzione
non tocca la rete tranne per la confutazione openligadb. Throttle 0,6 s fra le
richieste all'API Wikimedia, User-Agent identificato (policy Wikimedia).

> **Dove vivono gli script.** La sessione che ha prodotto questo lavoro poteva
> scrivere solo in `cantiere/out/caccia_calendari.{json,md}` e
> `cantiere/data/ricerca/fixtures_*.csv` (regola R4 applicata al singolo agente):
> per non perdere la riproducibilità il sorgente **completo** dei due moduli è
> incollato qui sotto. Chi integra il lavoro li estragga in
> `cantiere/scripts/caccia_calendari.py` e `cantiere/scripts/wiki.py` (funzionano
> così come sono: usano solo percorsi assoluti e `sys.path` verso la radice del
> repo), più il generatore del report (`scrivi_md.py`, non riportato: è solo
> impaginazione del JSON).

---

## Appendice A — `caccia_calendari.py`

```python

"""Caccia al dato VERO: le partite di COPPA mancanti nei calendari di club.

Il buco non appare come NaN: dove openfootball non copre una competizione, le
colonne `*_midweek_europe` valgono 0 ("non ha giocato in settimana") anche
quando la squadra HA giocato, e `*_rest_days_full` sovrastima il riposo.

Questo script:
  1. CENSISCE il contenuto dei 5 calendari di club (lega x stagione x competizione);
  2. SCARICA da Wikipedia (API wikitext, licenza CC BY-SA, robots.txt rispettato)
     il calendario COMPLETO di ogni competizione rilevante 2017-18 -> 2025-26;
  3. CONFRONTA le due cose -> censimento delle lacune MISURATO, non asserito;
  4. AGGANCIA i nomi squadra ai nostri canonici (sources.canonical_team +
     proposte esplicite, mai alias silenziosi) e ELENCA i non agganciati;
  5. ESEGUE i controlli obbligatori (doppia partita stesso giorno, finestra di
     stagione, squadra non presente in quella stagione);
  6. QUANTIFICA l'impatto ricalcolando add_rest_days_full con e senza il
     recupero, senza toccare gli snapshot.

Uscite: cantiere/out/caccia_calendari.{json,md}, cantiere/data/ricerca/fixtures_*.csv
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/Polymarket-oracle")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "cantiere" / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import nuove_leghe  # noqa: E402

nuove_leghe.registra()

from src.data import fixtures as fx_mod  # noqa: E402
from src.data import sources  # noqa: E402

import wiki  # noqa: E402

OUT = ROOT / "cantiere" / "out"
RICERCA = ROOT / "cantiere" / "data" / "ricerca"
SEASONS = ["1718", "1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]

SNAPSHOT = {
    "serie_a": ROOT / "data" / "serie_a_matches.csv",
    "premier_league": ROOT / "data" / "premier_league_matches.csv",
    "la_liga": ROOT / "data" / "la_liga_matches.csv",
    "bundesliga": ROOT / "cantiere" / "data" / "bundesliga_matches.csv",
    "ligue_1": ROOT / "cantiere" / "data" / "ligue_1_matches.csv",
}
FIXPATH = {
    "serie_a": ROOT / "data" / "club_fixtures.csv",
    "premier_league": ROOT / "data" / "club_fixtures_premier_league.csv",
    "la_liga": ROOT / "data" / "club_fixtures_la_liga.csv",
    "bundesliga": ROOT / "cantiere" / "data" / "club_fixtures_bundesliga.csv",
    "ligue_1": ROOT / "cantiere" / "data" / "club_fixtures_ligue_1.csv",
}
CC = {"serie_a": "ITA", "premier_league": "ENG", "la_liga": "ESP",
      "bundesliga": "GER", "ligue_1": "FRA"}
OWN = {k: sources.own_league_competition(k) for k in SNAPSHOT}


def sl(code: str) -> str:
    y = 2000 + int(code[:2])
    return f"{y}–{str(y + 1)[2:]}"


def y0(code: str) -> int:
    return 2000 + int(code[:2])


# --------------------------------------------------------------------------- #
# Pagine Wikipedia: competizioni EUROPEE (comuni alle 5 leghe)
# --------------------------------------------------------------------------- #
def uefa_pages(comp: str, code: str) -> list[str]:
    """comp in {'cl','el','conf'} -> pagine della stagione."""
    S, ye = sl(code), y0(code) + 1
    if comp == "cl":
        full, first = "UEFA Champions League", "Champions League"
    elif comp == "el":
        full, first = "UEFA Europa League", "Europa League"
    else:
        full = ("UEFA Conference League" if code in ("2425", "2526")
                else "UEFA Europa Conference League")
        first = "Conference League"
    phase = "league phase" if code in ("2425", "2526") else "group stage"
    return [
        f"{S} {full} {phase}",
        f"{S} {full} knockout phase",
        f"{S} {full} qualifying phase and play-off round",
        f"{ye} {full} final",
        f"{ye} {full} Final",
    ]


UEFA_NAME = {"cl": "Champions League", "el": "Europa League",
             "conf": "Conference League"}
UEFA_SEASONS = {
    "cl": SEASONS, "el": SEASONS,
    "conf": ["2122", "2223", "2324", "2425", "2526"],
}

# --------------------------------------------------------------------------- #
# Pagine Wikipedia: coppe NAZIONALI e super-coppe (per lega)
# --------------------------------------------------------------------------- #
DOMESTIC: dict[str, list[tuple[str, str, list[str]]]] = {
    # lega -> [(nome competizione, template pagina, stagioni)]
    "serie_a": [("Coppa Italia", "{S} Coppa Italia", SEASONS)],
    "la_liga": [("Copa del Rey", "{S} Copa del Rey", SEASONS)],
    "premier_league": [("FA Cup", "{S} FA Cup", SEASONS),
                       ("EFL Cup", "{S} EFL Cup", SEASONS)],
    "bundesliga": [("DFB-Pokal", "{S} DFB-Pokal", SEASONS)],
    "ligue_1": [("Coupe de France", "{S} Coupe de France", SEASONS),
                ("Coupe de la Ligue", "{S} Coupe de la Ligue",
                 ["1718", "1819", "1920"])],
}
# Super-coppe e tornei "una tantum": pagine per EDIZIONE (anno solare).
SUPERCUPS: dict[str, list[tuple[str, str]]] = {
    "serie_a": [("Supercoppa Italiana", "{Y} Supercoppa Italiana")],
    "la_liga": [("Supercopa de Espana", "{Y} Supercopa de España")],
    "premier_league": [("FA Community Shield", "{Y} FA Community Shield")],
    "bundesliga": [("DFL-Supercup", "{Y} DFL-Supercup")],
    "ligue_1": [("Trophee des Champions", "{Y} Trophée des Champions")],
}
GLOBAL_CUPS = [("UEFA Super Cup", "{Y} UEFA Super Cup", list(range(2017, 2026))),
               ("FIFA Club World Cup", "{Y} FIFA Club World Cup",
                [2017, 2018, 2019, 2021, 2022, 2023, 2025]),
               ("FIFA Intercontinental Cup", "{Y} FIFA Intercontinental Cup",
                [2024, 2025])]
SUPERCUP_YEARS = list(range(2017, 2027))


# --------------------------------------------------------------------------- #
# Aggancio nomi
# --------------------------------------------------------------------------- #
def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


_DROP = {"fc", "cf", "ac", "as", "ss", "ssc", "us", "ud", "rc", "rcd", "cd",
         "sd", "ca", "sc", "afc", "bsc", "tsg", "vfl", "vfb", "sv", "spvgg",
         "dsc", "fsv", "kv", "sk", "club", "calcio", "de", "futbol", "football",
         "1846", "1848", "1899", "1909", "1907", "05", "04", "96", "98", "1",
         "2", "07", "sad", "the", "olympique", "stade", "racing"}


def key(s: str) -> str:
    return " ".join(t for t in norm(s).split() if t not in _DROP)


# Proposte di alias ESPLICITE (nome Wikipedia -> nome canonico dello snapshot).
# Nessun alias e' inventato in silenzio: ognuno e' elencato qui e nel report.
PROPOSTE: dict[str, str] = {
    # Italia
    "Internazionale": "Inter", "Inter Milan": "Inter", "Internazionale Milano": "Inter",
    "AC Milan": "Milan", "Hellas Verona": "Verona", "SPAL": "Spal",
    "Chievo Verona": "Chievo", "Chievo": "Chievo",
    # Inghilterra
    "Manchester United": "Man United", "Manchester City": "Man City",
    "Newcastle United": "Newcastle", "Tottenham Hotspur": "Tottenham",
    "Wolverhampton Wanderers": "Wolves", "Nottingham Forest": "Nott'm Forest",
    "West Bromwich Albion": "West Brom", "Brighton & Hove Albion": "Brighton",
    "Brighton and Hove Albion": "Brighton", "Leicester City": "Leicester",
    "Cardiff City": "Cardiff", "Stoke City": "Stoke", "Swansea City": "Swansea",
    "Norwich City": "Norwich", "Ipswich Town": "Ipswich", "Luton Town": "Luton",
    "Huddersfield Town": "Huddersfield", "Leeds United": "Leeds",
    "Sheffield United": "Sheffield United", "West Ham United": "West Ham",
    "AFC Bournemouth": "Bournemouth", "Burnley": "Burnley",
    "Sunderland": "Sunderland", "Watford": "Watford",
    # Spagna
    "Atletico Madrid": "Ath Madrid", "Atlético Madrid": "Ath Madrid",
    "Athletic Bilbao": "Ath Bilbao", "Real Sociedad": "Sociedad",
    "Real Betis": "Betis", "Celta Vigo": "Celta", "Espanyol": "Espanol",
    "RCD Espanyol": "Espanol", "Rayo Vallecano": "Vallecano",
    "Deportivo La Coruña": "La Coruna", "Deportivo de La Coruña": "La Coruna",
    "Real Valladolid": "Valladolid", "Deportivo Alavés": "Alaves",
    "Alavés": "Alaves", "Cádiz": "Cadiz", "Málaga": "Malaga",
    "Almería": "Almeria", "Leganés": "Leganes", "Real Oviedo": "Oviedo",
    "Las Palmas": "Las Palmas", "Real Madrid": "Real Madrid",
    # Germania
    "Bayern Munich": "Bayern Munich", "Borussia Dortmund": "Dortmund",
    "Bayer Leverkusen": "Leverkusen", "Borussia Mönchengladbach": "M'gladbach",
    "Eintracht Frankfurt": "Ein Frankfurt", "1. FC Köln": "FC Koln",
    "Hertha BSC": "Hertha", "Schalke 04": "Schalke 04", "Mainz 05": "Mainz",
    "1. FSV Mainz 05": "Mainz", "Fortuna Düsseldorf": "Fortuna Dusseldorf",
    "Arminia Bielefeld": "Bielefeld", "Greuther Fürth": "Greuther Furth",
    "1. FC Nürnberg": "Nurnberg", "Nürnberg": "Nurnberg",
    "Hamburger SV": "Hamburg", "Hannover 96": "Hannover",
    "St. Pauli": "St Pauli", "FC St. Pauli": "St Pauli",
    "Darmstadt 98": "Darmstadt", "SV Darmstadt 98": "Darmstadt",
    "1. FC Heidenheim": "Heidenheim", "SC Paderborn 07": "Paderborn",
    "1. FC Union Berlin": "Union Berlin", "VfL Bochum": "Bochum",
    "RB Leipzig": "RB Leipzig", "Holstein Kiel": "Holstein Kiel",
    "TSG 1899 Hoffenheim": "Hoffenheim", "Werder Bremen": "Werder Bremen",
    # Francia
    "Paris Saint-Germain": "Paris SG", "Saint-Étienne": "St Etienne",
    "Saint-Etienne": "St Etienne", "Lyon": "Lyon", "Marseille": "Marseille",
    "Nîmes": "Nimes", "Paris FC": "Paris FC", "Le Havre": "Le Havre",
    "Stade Brestois": "Brest", "Brest": "Brest",
}


def build_resolver(teams: set[str]):
    """Risolutore nome-grezzo -> nome canonico, con tracciamento del METODO."""
    by_key: dict[str, set[str]] = {}
    for t in teams:
        by_key.setdefault(key(t), set()).add(t)
    cache: dict[str, tuple[str | None, str]] = {}

    def resolve(raw: str) -> tuple[str | None, str]:
        if raw in cache:
            return cache[raw]
        out: tuple[str | None, str]
        c = sources.canonical_team(raw)
        if c in teams:
            out = (c, "canonical_team")
        elif raw in PROPOSTE and PROPOSTE[raw] in teams:
            out = (PROPOSTE[raw], "proposta")
        else:
            cand = by_key.get(key(raw), set())
            if len(cand) == 1:
                out = (next(iter(cand)), "chiave-normalizzata")
            else:
                k2 = key(sources.canonical_team(raw))
                cand2 = by_key.get(k2, set())
                out = ((next(iter(cand2)), "chiave-normalizzata")
                       if len(cand2) == 1 else (None, "NON AGGANCIATO"))
        cache[raw] = out
        return out

    return resolve




# --------------------------------------------------------------------------- #
# Scarico + parse: una PAGINA -> lista di partite grezze (con tag competizione)
# --------------------------------------------------------------------------- #
def fetch_page(title: str) -> list[dict]:
    """Partite di una pagina + delle sue trasclusioni {{#lst:...}} (1 livello)."""
    x = wiki.wikitext(title)
    if x is None:
        return []
    rows = wiki.parse_matches(x)
    for sub in sorted(set(re.findall(r"\{\{#lst[a-z]*:\s*([^|}]+)", x))):
        y = wiki.wikitext(sub.strip())
        if y is not None:
            rows.extend(wiki.parse_matches(y))
    return rows


def dedup(rows: list[dict]) -> list[dict]:
    seen, out = set(), []
    for r in rows:
        k = (r["date"], r["home_raw"], r["away_raw"], r.get("competition"))
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def raccogli_wikipedia() -> tuple[list[dict], dict]:
    """Tutte le partite grezze rilevanti da Wikipedia, con competizione taggata."""
    rows: list[dict] = []
    pagine: dict[str, int] = {}

    def add(title: str, comp: str, cc_filter: str | None = None):
        rr = fetch_page(title)
        pagine[title] = len(rr)
        for r in rr:
            r = dict(r)
            r["competition"] = comp
            r["pagina"] = title
            rows.append(r)

    # --- competizioni UEFA (una sola volta: valgono per tutte le leghe) ---
    for comp, seas in UEFA_SEASONS.items():
        for code in seas:
            pgs = uefa_pages(comp, code)
            add(pgs[0], UEFA_NAME[comp])
            add(pgs[1], UEFA_NAME[comp])
            add(pgs[2], UEFA_NAME[comp] + " (qual.)")
            add(pgs[3], UEFA_NAME[comp])
            add(pgs[4], UEFA_NAME[comp])
    # --- coppe nazionali (+ FINALE, che su Wikipedia sta su una pagina a se') ---
    for lg, specs in DOMESTIC.items():
        for name, tmpl, seas in specs:
            for code in seas:
                add(tmpl.format(S=sl(code)), name)
                base = tmpl.split(" ", 1)[1]
                for suf in ("Final", "final"):
                    add(f"{y0(code) + 1} {base} {suf}", name)
    # --- super-coppe nazionali (titolo per anno solare e per stagione) ---
    for lg, specs in SUPERCUPS.items():
        for name, tmpl in specs:
            for Y in SUPERCUP_YEARS:
                add(tmpl.format(Y=Y), name)
            for code in SEASONS:
                add(tmpl.format(Y=sl(code)), name)
    # --- coppe globali ---
    for name, tmpl, years in GLOBAL_CUPS:
        for Y in years:
            add(tmpl.format(Y=Y), name)
            add(tmpl.format(Y=Y) + " final", name)
            add(tmpl.format(Y=Y) + " Final", name)
    for grp in "ABCDEFGH":
        add(f"2025 FIFA Club World Cup Group {grp}", "FIFA Club World Cup")
    add("2025 FIFA Club World Cup knockout stage", "FIFA Club World Cup")
    return dedup(rows), pagine


# --------------------------------------------------------------------------- #
# Da partite grezze a righe per-squadra dello schema club_fixtures
# --------------------------------------------------------------------------- #
def stagione_di(d: pd.Timestamp, finestre: dict[str, tuple]) -> tuple[str, int]:
    """Etichetta-stagione di una data = stagione la cui FINESTRA di campionato
    e' piu' vicina (0 se la data ci cade dentro).

    Regola unica e robusta: la convenzione "luglio-giugno" sbaglia sulle
    stagioni COVID (la finale di Champions 2019-20 si e' giocata il 23/8/2020) e
    sui tornei estivi; la distanza dalla finestra reale no. `dist` e' un
    controllo di qualita', non entra in nessun calcolo (add_rest_days_full
    raggruppa per SQUADRA, non per stagione).
    """
    best, bestd = None, 10 ** 9
    for code, (a, b) in finestre.items():
        k = 0 if a <= d <= b else int(min(abs((d - a).days), abs((d - b).days)))
        if k < bestd:
            best, bestd = code, k
    return best, bestd


def righe_per_squadra(rows, lg, teams, finestre, limite: pd.Timestamp):
    """Righe schema club_fixtures per la lega `lg`. Le partite UEFA sono
    filtrate col codice paese della lega (autorevole); le coppe nazionali e le
    super-coppe per aggancio del nome. Fuori dalla finestra dati (oltre
    `limite`) si scarta: sarebbe la stagione successiva."""
    resolve = build_resolver(teams)
    out, non_agganciati, scartate_oltre = [], {}, 0
    cc = CC[lg]
    for r in rows:
        d = pd.Timestamp(r["date"])
        fam = r["competition"].split(" (")[0]
        is_uefa = fam in UEFA_NAME.values()
        for side, opp, ha, scc in ((r["home_raw"], r["away_raw"], "H", r["home_cc"]),
                                   (r["away_raw"], r["home_raw"], "A", r["away_cc"])):
            if is_uefa and scc != cc and not (
                    cc == "FRA" and scc == "MCO"):   # Monaco: UEFA lo dà (MCO)
                continue
            t, how = resolve(side)
            if t is None:
                if is_uefa and (scc == cc or (cc == "FRA" and scc == "MCO")):
                    non_agganciati[side] = non_agganciati.get(side, 0) + 1
                continue
            if d > limite:
                scartate_oltre += 1
                continue
            o, _ = resolve(opp)
            code, dist = stagione_di(d, finestre)
            out.append({"season": code, "team": t, "date": d.strftime("%Y-%m-%d"),
                        "competition": r["competition"], "home_away": ha,
                        "opponent": o or opp, "metodo_nome": how,
                        "pagina": r["pagina"], "giorni_fuori_finestra": dist})
    df = pd.DataFrame(out)
    if not df.empty:
        df = df.sort_values(["date", "team", "competition"]).drop_duplicates(
            subset=["team", "date", "competition", "opponent"])
    return df, non_agganciati, scartate_oltre


EXTRA = {"Supercoppa Italiana", "Supercopa de Espana", "FA Community Shield",
         "DFL-Supercup", "Trophee des Champions", "UEFA Super Cup",
         "FIFA Club World Cup", "FIFA Intercontinental Cup"}


def _boot(d, rng, B: int = 10_000):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return (float(d.mean()), float(np.percentile(m, 2.5)),
            float(np.percentile(m, 97.5)), float((m < 0).mean()))


def _impatto(m, base_fx, add_fx, own, rng):
    base = fx_mod.add_rest_days_full(m, base_fx, own_competition=own)
    merged = pd.concat([base_fx, add_fx[fx_mod.FIXTURE_COLUMNS]], ignore_index=True)
    merged["date"] = pd.to_datetime(merged["date"])
    new = fx_mod.add_rest_days_full(m, merged, own_competition=own)
    flip = sum(int(((base[f"{s}_midweek_europe"] == 0) &
                    (new[f"{s}_midweek_europe"] == 1)).sum()) for s in ("home", "away"))
    righe = int((((base.home_midweek_europe == 0) & (new.home_midweek_europe == 1)) |
                 ((base.away_midweek_europe == 0) & (new.away_midweek_europe == 1))).sum())
    d = pd.concat([base.home_rest_days_full - new.home_rest_days_full,
                   base.away_rest_days_full - new.away_rest_days_full]).dropna()
    d = d[d != 0].to_numpy()
    mean, lo, hi = (_boot(d, rng)[:3] if len(d) else (0.0, 0.0, 0.0))
    return {
        "celle_midweek_flip_0_1": flip,
        "righe_snapshot_toccate_da_midweek": righe,
        "pct_righe_midweek": round(100 * righe / len(m), 2),
        "celle_rest_days_cambiate": int(len(d)),
        "pct_celle_rest_days": round(100 * len(d) / (2 * len(m)), 2),
        "delta_rest_medio_su_celle_cambiate": round(mean, 3),
        "delta_rest_ci95_bootstrap_B10000": [round(lo, 3), round(hi, 3)],
        "delta_rest_max": round(float(d.max()), 1) if len(d) else 0.0,
        "midweek_prima_pct": round(100 * float(pd.concat(
            [base.home_midweek_europe, base.away_midweek_europe]).mean()), 2),
        "midweek_dopo_pct": round(100 * float(pd.concat(
            [new.home_midweek_europe, new.away_midweek_europe]).mean()), 2),
    }


def main() -> None:
    RICERCA.mkdir(parents=True, exist_ok=True)
    report: dict = {"nota": "prodotto da caccia_calendari.py; nessuno snapshot modificato"}

    snap = {k: pd.read_csv(p, dtype={"season": str}) for k, p in SNAPSHOT.items()}
    for d in snap.values():
        d["date"] = pd.to_datetime(d["date"])
    teams = {k: set(d.home_team) | set(d.away_team) for k, d in snap.items()}
    per_season_teams = {
        k: {s: set(g.home_team) | set(g.away_team) for s, g in d.groupby("season")}
        for k, d in snap.items()}
    finestre = {k: {s: (g.date.min(), g.date.max()) for s, g in d.groupby("season")}
                for k, d in snap.items()}
    limite = {k: max(b for _, b in f.values()) + pd.Timedelta(days=30)
              for k, f in finestre.items()}
    old = {k: fx_mod.read_club_fixtures(p) for k, p in FIXPATH.items()}

    # -- 0. controllo: la pausa estiva e' sempre > cap(14g)? (playoff/barrage) --
    pause = {}
    for lg, f in finestre.items():
        cs = sorted(f)
        pause[lg] = {f"{cs[i]}->{cs[i+1]}": int((f[cs[i + 1]][0] - f[cs[i]][1]).days)
                     for i in range(len(cs) - 1)}
    report["pausa_estiva_giorni"] = pause

    # -- 1. censimento del calendario ATTUALE ---------------------------------- #
    cens = []
    for lg, fx in old.items():
        g = fx.groupby(["season", "competition"]).agg(
            righe=("team", "size"), squadre=("team", "nunique")).reset_index()
        g.insert(0, "lega", lg)
        cens.append(g)
    report["censimento_attuale"] = pd.concat(cens, ignore_index=True).to_dict("records")

    # -- 2. verita' indipendente da Wikipedia ---------------------------------- #
    print("Scarico/leggo Wikipedia…")
    raw, pagine = raccogli_wikipedia()
    print(f"  {len(raw)} partite grezze, {sum(1 for v in pagine.values() if v)} pagine utili")
    report["pagine_wikipedia_utili"] = {k: v for k, v in pagine.items() if v}
    report["pagine_wikipedia_vuote_o_assenti"] = sorted(k for k, v in pagine.items() if not v)

    tutte, non_agg, scartate = {}, {}, {}
    for lg in SNAPSHOT:
        tutte[lg], non_agg[lg], scartate[lg] = righe_per_squadra(
            raw, lg, teams[lg], finestre[lg], limite[lg])
    report["nomi_non_agganciati"] = non_agg
    report["righe_scartate_oltre_finestra_dati"] = scartate

    # -- 3. confronto (censimento delle lacune, MISURATO) ---------------------- #
    confronto, disaccordi = [], []
    for lg in SNAPSHOT:
        o = old[lg].copy()
        o["date"] = pd.to_datetime(o["date"]).dt.strftime("%Y-%m-%d")
        o["fam"] = o.competition.str.replace(r" \(qual\.\)$", "", regex=True)
        n = tutte[lg].copy()
        n["fam"] = n.competition.str.replace(r" \(qual\.\)$", "", regex=True)
        have = set(zip(o.team, o.date))
        for (s, fam), g in n.groupby(["season", "fam"]):
            og = o[(o.season == s) & (o.fam == fam)]
            miss = g[[(t, d) not in have for t, d in zip(g.team, g.date)]]
            wset = set(zip(g.team, g.date))
            solo_nostre = og[[(t, d) not in wset for t, d in zip(og.team, og.date)]]
            confronto.append(dict(
                lega=lg, stagione=s, competizione=fam, wikipedia=len(g),
                nostre=len(og), mancanti=len(miss), solo_nostre=len(solo_nostre),
                squadre_mancanti=int(miss.team.nunique())))
            if len(solo_nostre) and len(miss):
                for tm in sorted(set(solo_nostre.team) & set(miss.team)):
                    dn = sorted(solo_nostre[solo_nostre.team == tm].date)
                    dw = sorted(miss[miss.team == tm].date)
                    vicini = [(a, b) for a in dn for b in dw
                              if abs((pd.Timestamp(a) - pd.Timestamp(b)).days) <= 3]
                    if vicini:
                        disaccordi.append(dict(
                            lega=lg, stagione=s, competizione=fam, squadra=tm,
                            coppie_a_meno_di_3_giorni=vicini))
    report["confronto"] = confronto
    report["disaccordi_di_data"] = disaccordi

    # riconciliazione GLOBALE per (lega, competizione): immune all'etichetta di
    # stagione (che per le code COVID di agosto 2020 non coincide fra le fonti)
    glob = []
    for lg in SNAPSHOT:
        o = old[lg].copy()
        o["date"] = pd.to_datetime(o["date"]).dt.strftime("%Y-%m-%d")
        o["fam"] = o.competition.str.replace(r" \(qual\.\)$", "", regex=True)
        n = tutte[lg].copy()
        n["fam"] = n.competition.str.replace(r" \(qual\.\)$", "", regex=True)
        for fam in sorted(set(n.fam) | set(o.fam)):
            og, ng = o[o.fam == fam], n[n.fam == fam]
            hs, ws = set(zip(og.team, og.date)), set(zip(ng.team, ng.date))
            glob.append(dict(lega=lg, competizione=fam, wikipedia=len(ws),
                             nostre=len(hs), mancanti=len(ws - hs),
                             solo_nostre=len(hs - ws)))
    report["riconciliazione_globale"] = glob

    # -- 4. righe DAVVERO nuove + controlli obbligatori ------------------------ #
    nuove, controlli = {}, {}
    for lg in SNAPSHOT:
        o = old[lg].copy()
        o["date"] = pd.to_datetime(o["date"]).dt.strftime("%Y-%m-%d")
        have = set(zip(o.team, o.date))
        n = tutte[lg]
        n = n[[(t, d) not in have for t, d in zip(n.team, n.date)]].copy()
        doppie_interne = n.groupby(["team", "date"]).size()
        n = n.drop_duplicates(subset=["team", "date"], keep="first")
        nuove[lg] = n
        merged = pd.concat([o[fx_mod.FIXTURE_COLUMNS], n[fx_mod.FIXTURE_COLUMNS]])
        dbl = merged.groupby(["team", "date"]).size()
        fuori_rosa = [{"season": r.season, "team": r.team, "date": r.date,
                       "competition": r.competition}
                      for r in n.itertuples(index=False)
                      if r.team not in per_season_teams[lg].get(r.season, set())]
        controlli[lg] = {
            "righe_nuove": int(len(n)),
            "wiki_gia_presenti": int(len(tutte[lg]) - len(n)),
            "doppie_stesso_giorno_dopo_merge": int((dbl > 1).sum()),
            "doppie_dentro_le_nuove_prima_del_dedup": int((doppie_interne > 1).sum()),
            "esempi_doppie_nuove": [
                {"team": t, "date": d, "n": int(v)}
                for (t, d), v in doppie_interne[doppie_interne > 1].head(10).items()],
            "date_fuori_finestra_oltre_60gg": int((n.giorni_fuori_finestra > 60).sum()),
            "esempi_fuori_finestra": n[n.giorni_fuori_finestra > 60].head(10)[
                ["season", "team", "date", "competition"]].to_dict("records"),
            "metodo_aggancio_nome": n.metodo_nome.value_counts().to_dict(),
            "squadra_non_in_lega_quella_stagione": len(fuori_rosa),
            "esempi_squadra_non_in_lega": fuori_rosa[:8],
            "per_competizione": n.competition.value_counts().to_dict(),
        }
    report["controlli"] = controlli

    # -- 5. CSV ---------------------------------------------------------------- #
    scritti = []
    for p in RICERCA.glob("fixtures_*.csv"):
        p.unlink()
    for lg, n in nuove.items():
        for comp, g in n.groupby("competition"):
            slug = re.sub(r"[^a-z0-9]+", "_", comp.lower()).strip("_")
            p = RICERCA / f"fixtures_{lg}_{slug}.csv"
            g[["season", "team", "date", "competition", "home_away", "opponent",
               "metodo_nome", "pagina"]].sort_values(["date", "team"]).to_csv(p, index=False)
            scritti.append(str(p.relative_to(ROOT)))
    report["file_scritti"] = sorted(scritti)

    # -- 6. impatto ------------------------------------------------------------ #
    rng = np.random.default_rng(20260725)
    impatto, impatto_core, per_comp = {}, {}, {}
    for lg in SNAPSHOT:
        m, n = snap[lg], nuove[lg]
        impatto[lg] = {"partite_snapshot": int(len(m)), "righe_aggiunte": int(len(n)),
                       **_impatto(m, old[lg], n, OWN[lg], rng)}
        core = n[~n.competition.str.split(" (", regex=False).str[0].isin(EXTRA)]
        impatto_core[lg] = {"righe_aggiunte": int(len(core)),
                            **_impatto(m, old[lg], core, OWN[lg], rng)}
        pc = {}
        for comp, g in n.groupby(n.competition.str.replace(r" \(qual\.\)$", "", regex=True)):
            r = _impatto(m, old[lg], g, OWN[lg], rng)
            pc[comp] = {"righe": int(len(g)),
                        "righe_snapshot_toccate_da_midweek":
                            r["righe_snapshot_toccate_da_midweek"],
                        "celle_rest_days_cambiate": r["celle_rest_days_cambiate"]}
        per_comp[lg] = dict(sorted(pc.items(),
                                   key=lambda kv: -kv[1]["celle_rest_days_cambiate"]))
    report["impatto"] = impatto
    report["impatto_solo_coppe_ed_europa"] = impatto_core
    report["impatto_per_competizione"] = per_comp

    # -- 7. il caso Monaco (bug di codice paese, non lacuna di copertura) ------ #
    mon = tutte["ligue_1"]
    mon = mon[mon.team == "Monaco"]
    mon_new = nuove["ligue_1"][nuove["ligue_1"].team == "Monaco"]
    report["caso_monaco"] = {
        "righe_europee_wikipedia": int((mon.competition.str.split(" (", regex=False).str[0]
                                        .isin(UEFA_NAME.values())).sum()),
        "righe_europee_mancanti_da_noi": int((mon_new.competition.str.split(" (", regex=False).str[0]
                                              .isin(UEFA_NAME.values())).sum()),
        "per_stagione": mon_new.groupby("season").size().to_dict(),
    }

    # -- 8. CONFUTAZIONE: terza fonte indipendente (openligadb.de, API pubblica) #
    report["confutazione_openligadb"] = confuta_openligadb(
        old["bundesliga"], nuove["bundesliga"], teams["bundesliga"])

    (OUT / "caccia_calendari.json").write_text(
        json.dumps(report, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print("scritto", OUT / "caccia_calendari.json")


def confuta_openligadb(old_fx, nuove_fx, teams) -> dict:
    """Terza fonte INDIPENDENTE (né openfootball né Wikipedia): l'API pubblica
    openligadb.de, che copre la DFB-Pokal. Serve a provare che il recupero e'
    SBAGLIATO: se le date recuperate non combaciano, il metodo non regge."""
    import urllib.request
    out = {}
    o = old_fx.copy()
    o["date"] = pd.to_datetime(o["date"]).dt.strftime("%Y-%m-%d")
    for tag, stag, code in (("dfb2017", "2017", "1718"), ("dfb2020", "2020", "2021"),
                            ("dfb", "2025", "2526")):
        try:
            with urllib.request.urlopen(
                    f"https://api.openligadb.de/getmatchdata/{tag}/{stag}", timeout=90) as r:
                d = json.load(r)
        except Exception as e:                                  # noqa: BLE001
            out[code] = {"errore": str(e)}
            continue
        terza = set()
        for m in d:
            dt = m["matchDateTime"][:10]
            for k in ("team1", "team2"):
                c = sources.canonical_team(m[k]["teamName"])
                if c in teams:
                    terza.add((c, dt))
        nostre = set(zip(o[(o.season == code) & (o.competition == "DFB-Pokal")].team,
                         o[(o.season == code) & (o.competition == "DFB-Pokal")].date))
        rec = set(zip(nuove_fx[(nuove_fx.season == code) &
                               (nuove_fx.competition == "DFB-Pokal")].team,
                      nuove_fx[(nuove_fx.season == code) &
                               (nuove_fx.competition == "DFB-Pokal")].date))
        out[code] = {
            "openligadb": len(terza), "openfootball_attuale": len(nostre),
            "recuperate_da_wikipedia": len(rec),
            "recuperate_NON_confermate": sorted(rec - terza),
            "openfootball_NON_confermate": sorted(nostre - terza),
            "openligadb_non_coperte_da_nessuno": sorted(terza - nostre - rec),
        }
    return out


if __name__ == "__main__":
    main()
```

## Appendice B — `wiki.py` (fetch + parser del wikitext)

```python
"""Fetch + parse di partite da Wikipedia (wikitext), con cache su disco."""
from __future__ import annotations
import json, re, time, urllib.parse, urllib.request
from pathlib import Path

CACHE = Path(__file__).resolve().parent / "wikicache"
CACHE.mkdir(exist_ok=True)
UA = {"User-Agent": "PolymarketOracle-research/1.0 (camarda.federico1@gmail.com)"}
_LAST = [0.0]


def wikitext(title: str, *, force: bool = False) -> str | None:
    fn = CACHE / (re.sub(r"[^A-Za-z0-9]+", "_", title)[:120] + ".txt")
    if fn.exists() and not force:
        t = fn.read_text(encoding="utf-8")
        return None if t == "\x00MISSING" else t
    dt = time.time() - _LAST[0]
    if dt < 0.6:
        time.sleep(0.6 - dt)
    _LAST[0] = time.time()
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "parse", "page": title, "prop": "wikitext",
        "format": "json", "formatversion": "2", "redirects": "1"})
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
            d = json.load(r)
    except Exception as e:                                    # noqa: BLE001
        print(f"  !! errore fetch {title}: {e}")
        return None
    if "error" in d:
        fn.write_text("\x00MISSING", encoding="utf-8")
        return None
    t = d["parse"]["wikitext"]
    fn.write_text(t, encoding="utf-8")
    return t


# --------------------------------------------------------------------------- #
# Estrazione dei blocchi {{Football box ...}} / {{#invoke:Football box|main ...}}
# --------------------------------------------------------------------------- #
_FBOX_START = re.compile(
    r"\{\{\s*(?:#invoke\s*:\s*)?football\s*box(?:\s+collapsible)?\b", re.I)


def _blocks(text: str) -> list[str]:
    out = []
    for m in _FBOX_START.finditer(text):
        i = m.start()
        depth, j = 0, i
        while j < len(text):
            if text.startswith("{{", j):
                depth += 1
                j += 2
            elif text.startswith("}}", j):
                depth -= 1
                j += 2
                if depth == 0:
                    break
            else:
                j += 1
        out.append(text[i:j])
    return out


def _params(block: str) -> dict[str, str]:
    """Splitta i parametri di primo livello di un template."""
    body = block[2:-2]
    parts, depth_c, depth_b, depth_p, buf = [], 0, 0, 0, []
    k = 0
    while k < len(body):
        two = body[k:k + 2]
        if two == "{{":
            depth_c += 1; buf.append(two); k += 2; continue
        if two == "}}":
            depth_c -= 1; buf.append(two); k += 2; continue
        if two == "[[":
            depth_b += 1; buf.append(two); k += 2; continue
        if two == "]]":
            depth_b -= 1; buf.append(two); k += 2; continue
        ch = body[k]
        if ch == "<":
            m = re.match(r"<ref[^>]*?/>|<ref[^>]*?>.*?</ref>|<!--.*?-->", body[k:], re.S)
            if m:
                k += m.end(); continue
        if ch == "|" and depth_c == 0 and depth_b == 0 and depth_p == 0:
            parts.append("".join(buf)); buf = []; k += 1; continue
        buf.append(ch); k += 1
    parts.append("".join(buf))
    out = {}
    for p in parts[1:]:
        if "=" in p:
            k2, v = p.split("=", 1)
            out[k2.strip().lower()] = v.strip()
    return out


_MONTHS = {m.lower(): i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}


def _date(raw: str) -> str | None:
    m = re.search(r"\{\{\s*[Ss]tart date\s*\|\s*(\d{4})\s*\|\s*(\d{1,2})\s*\|\s*(\d{1,2})", raw)
    if m:
        y, mo, d = (int(x) for x in m.groups())
        try:
            return f"{y:04d}-{mo:02d}-{d:02d}"
        except ValueError:
            return None
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", raw)
    if m and m.group(2).lower() in _MONTHS:
        return f"{int(m.group(3)):04d}-{_MONTHS[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"
    m = re.search(r"([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})", raw)
    if m and m.group(1).lower() in _MONTHS:
        return f"{int(m.group(3)):04d}-{_MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    return None


_LINK = re.compile(r"\[\[([^\]\|]+)(?:\|([^\]]+))?\]\]")
_CC = re.compile(r"fbaicon\s*\|\s*([A-Z]{3})|flagicon\s*\|\s*([A-Z]{3})|flagicon\s*\|\s*([A-Za-z ]+)\}\}")


def _team(raw: str) -> tuple[str | None, str | None]:
    """(nome squadra, codice paese 3 lettere se presente)."""
    cc = None
    m = re.search(r"fbaicon\s*\|\s*([A-Za-z]{3})\b", raw)
    if m:
        cc = m.group(1).upper()
    else:
        m = re.search(r"flagicon\s*\|\s*([A-Za-z]{3})\s*(?:\||\}\})", raw)
        if m:
            cc = m.group(1).upper()
    links = _LINK.findall(raw)
    name = None
    for tgt, disp in links:
        cand = (disp or tgt).strip()
        if re.fullmatch(r"[A-Za-z ]{3,}", cand) and cand.lower() in {
                "spain", "italy", "england", "germany", "france"}:
            continue
        name = cand
        break
    if name is None:
        txt = re.sub(r"\{\{[^{}]*\}\}", " ", raw)
        txt = re.sub(r"<[^>]+>", " ", txt)
        txt = txt.replace("'''", "").strip()
        name = txt.split("\n")[0].strip() or None
    if name:
        name = name.replace("\xa0", " ").strip()
        name = re.sub(r"\s*\(\d+\)$", "", name)   # via "(3)" dei rigori
    return name, cc


def parse_matches(text: str) -> list[dict]:
    rows = []
    for b in _blocks(text):
        p = _params(b)
        raw_date = p.get("date", "")
        d = _date(raw_date)
        t1, cc1 = _team(p.get("team1", ""))
        t2, cc2 = _team(p.get("team2", ""))
        if not d or not t1 or not t2:
            continue
        rows.append({"date": d, "home_raw": t1, "home_cc": cc1,
                     "away_raw": t2, "away_cc": cc2})
    return rows
```
