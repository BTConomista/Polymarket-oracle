# Caccia alle quote O/U 2017-19 — specifica del dato e piano di ricerca

Il buco di dati reali (vedi [DATI.md](DATI.md)): le quote Over/Under 2.5 di
**chiusura** delle stagioni **2017-18 e 2018-19** nelle 3 leghe — già coperte
da una stima, ma sostituibili con la verità. Questo documento dice esattamente
COSA cercare, DOVE, con quale piano, e contiene un **prompt pronto** da dare a
un'AI con accesso libero al web.

> ⚠️ **Aggiornamento Fase 73: il bersaglio si è dimezzato.** Si credeva
> mancasse anche l'**apertura** O/U 2017-19 (4.564 celle). In realtà l'unica
> linea O/U di quelle stagioni (`BbAv`) è un'**apertura reale** (pre-match),
> prima erroneamente etichettata come chiusura: ora è nella colonna giusta
> (`odds_over25_open`), dato reale, **non più da cercare**. Resta da procurare
> solo la **chiusura** O/U (2.280 celle) — il resto di questo documento vale
> per quella. La stima di chiusura (E3 pooled) è confermata imbattuta anche
> dopo la correzione (Fase 73, dispersione `BbMx` inclusa).

> ⚠️ **Promemoria per il futuro (luglio 2026).** Fase A (dataset già pronti)
> e Fase B (scraping BetExplorer) sono **entrambe chiuse negative** — vedi
> §3. Su richiesta dell'utente, invece di rincorrere la Fase D (OddsPortal
> headless con login, rischio/complessità più alta) si è scelto di spremere
> al massimo la stima esistente (Fasi 72/73, `docs/DIARIO.md`): confermata
> come tetto pratico. **Questo NON significa che il dato vero sia
> irraggiungibile per sempre** — solo che le vie economiche/sicure note OGGI
> sono esaurite. Da riprovare in futuro, senza ripartire da zero:
> - **Fase A, di tanto in tanto**: nuovi dataset compaiono su Kaggle/GitHub/
>   Hugging Face nel tempo (candidati già controllati e scartati sono elencati
>   in §3 — non ripartire da quelli, cercarne di nuovi o con fonte diversa da
>   football-data.co.uk);
> - **Fase D**: OddsPortal headless con login resta la pista con la
>   probabilità più alta di successo, mai tentata per il costo/rischio
>   (credenziali in un secret) — riconsiderarla se emerge un account "usa e
>   getta" a basso rischio o un partner che lo faccia per noi;
> - **Fonti a pagamento** (§2.D del piano): mai valutate a fondo (costo vs
>   2.280 partite) — se il progetto passa a un uso più operativo, rivalutare.

---

## 1 · Cosa ci serve, esattamente

Una tabella con **una riga per partita** per queste 6 (lega, stagione):

| lega | stagioni | partite |
|---|---|--:|
| Serie A | 2017-18, 2018-19 | 760 |
| Premier League | 2017-18, 2018-19 | 760 |
| La Liga | 2017-18, 2018-19 | 760 |

**Colonne richieste** (nomi liberi, il contenuto conta):

```
data · squadra_casa · squadra_ospite · punteggio_finale (verifica join)
quota_over25_CHIUSURA  · quota_under25_CHIUSURA      <- il dato che manca
quota_over25_APERTURA  · quota_under25_APERTURA      <- utile per il join/verifica
fonte (sito/dataset) · book ("average" oppure nome del bookmaker)
```

Nota (Fase 73): l'**apertura** O/U 2017-19 la abbiamo già (dato reale `BbAv`,
negli snapshot come `odds_over25_open`) — serve per verificare l'abbinamento
riga per riga, ma il dato da procurare è la **chiusura**.

**Bonus** (partite sparse senza apertura 1X2 vera): Torino-Fiorentina
10/01/2022 (Serie A, recupero). *(Alaves-Real Sociedad 14/10/2017 non è più in
lista: dalla Fase 73 la sua apertura 1X2 reale `PSH` è negli snapshot; le resta
però una **chiusura 1X2** mancante — `PSC` vuote nel grezzo — che sarebbe un
bonus da procurare.)* Un tentativo di ricerca esterna diretta (BetExplorer/
OddsPortal da IP italiano) non ha trovato nulla per un blocco geo/ADM (vedi
`docs/MANUALE_SOPRAVVIVENZA.md`); nel frattempo Torino-Fiorentina è **stimata**
(Fase 69, bakeoff di 5 metodi, MAE atteso ~0.016) in
`data/estimates/open_sparse_1x2_ou.csv` — resta comunque candidata a dato vero
se mai si trovasse una fonte percorribile.

### Criteri di accettazione (chi cerca DEVE verificarli)

1. **Linea 2.5 esatta** — non 2.25/2.75 (linee asiatiche) né altre linee.
2. **Quote decimali europee** (es. 1.85), > 1.0.
3. **Apertura e chiusura DISTINTE**: sono due istantanee temporali diverse
   (apertura = prima quota pubblicata, chiusura = al calcio d'inizio). Se in
   ≥ ~90% delle righe coincidono, la fonte sta dando una sola istantanea
   rietichettata → NON valida.
4. **Overround sano**: `1/over + 1/under > 1` su ENTRAMBE le istantanee, per
   ogni riga (un book vero ha sempre margine; violazioni = dato corrotto).
5. **Copertura ≥ 95%** per ciascuna (lega, stagione) — buchi sparsi ok se
   dichiarati.
6. **Preferenza sul book** (in ordine): **Pinnacle** (il nostro 1X2 2017-19 è
   già Pinnacle apertura→chiusura: coppie coerenti) → media multi-book →
   singolo book maggiore (Bet365). Va bene anche un mix, purché la colonna
   `book` lo dichiari riga per riga.
7. **Provenienza dichiarata**: da quale sito/dataset viene ogni numero, e
   quando è stato raccolto.

### Cosa NON accettare (trappole note)

- Quote "attuali"/"medie storiche di lega" senza granularità per-partita.
- Linee **ricostruite/stimate** da terzi (modelli altrui spacciati per quote:
  chiedere sempre COME il dataset è stato costruito — se è uno scrape di un
  archivio quote è ok, se è un modello no).
- CSV senza data+squadre per riga (impossibile il join).
- Il dataset "Beat the Bookie" (noto, con open+close) si ferma al ~2015: fuori
  finestra.

---

## 2 · Dove cercare (in ordine di costo, §1.3 del protocollo)

**A. Dataset già scrappati da altri (il colpo economico — provare PRIMA):**
- **Kaggle**: query tipo `football odds opening closing 2018`, `oddsportal
  dataset`, `over under odds historical serie a premier`. Esistono scrape
  storici di OddsPortal pubblicati come dataset.
- **GitHub**: repo di scraper OddsPortal/BetExplorer che committano i CSV
  (query: `oddsportal scraper csv 2017 2018 over under`).
- **Hugging Face datasets**, **Zenodo/OSF** (dataset accademici su efficienza
  dei mercati scommesse: spesso includono open+close multi-mercato).
- **football-data.co.uk "Notes"**: chiedere all'autore? il sito vende anche
  archivi estesi — verificare se un archivio storico O/U esiste a pagamento
  modico.

**B. BetExplorer** (`betexplorer.com/football/italy/serie-a-2017-2018/results/`):
pagine risultati per stagione → link partita → tab "O/U" con quote per book e
**movimento** (apertura nel tooltip/endpoint AJAX `.../match-odds/...`). HTML
in gran parte server-rendered: scrappabile con richieste semplici e throttle.
Scraper pronto (workflow GitHub Actions + probe): vedi
[BETEXPLORER_SCRAPER.md](BETEXPLORER_SCRAPER.md).

**C. OddsPortal** (`oddsportal.com/soccer/italy/serie-a-2017-2018/results/`):
il più ricco (open+close per book con timestamp) ma JS-pesante + Cloudflare:
serve headless browser. Solo se B non basta.

**D. API a pagamento** (BetsAPI, OpticOdds, historical odds provider): ultima
spiaggia, valutare costo vs 2.280 partite.

---

## 3 · Piano operativo (con criteri go/no-go)

| fase | azione | costo | go/no-go |
|---|---|---|---|
| **A** | ❌ **FALLITA** — ricognizione dataset esistenti (WebSearch + probe Kaggle via Actions: vedi sotto) | 1 ora | nessun dataset passa i criteri §1 — chiusa |
| **B** | ❌ **FALLITA** — tracer BetExplorer via GitHub Actions (probe live, 5 giri: vedi sotto) | mezza giornata | copertura 0% — chiusa, non scala |
| **C** | scala alle 6 (lega, stagione); bundle `files/ou_2017_19_bundle.json` | — | **salta**: né A né B hanno prodotto dati da scalare |
| **D** | OddsPortal headless (solo se B fallisce) | 2+ giorni, fragile | A e B sono fallite → candidata, ma con un limite noto (vedi sotto) |

**Esito Fase A (WebSearch + probe Kaggle via Actions).** Prima ricerca web
diretta (`WebSearch`, funzionante da questa sessione): confermato — fonte
indipendente dai nostri dati — che **football-data.co.uk** (la fonte-madre di
quasi ogni dataset di quote calcio ripubblicato su Kaggle/GitHub) ha iniziato a
raccogliere due istantanee apertura/chiusura **solo dalla stagione 2019/20**
(prima, un'unica rilevazione media via Betbrain): combacia esattamente col
buco già in `docs/DATI.md`. Nessun repo GitHub con CSV già pronti (solo
scraper/tool, zero dati 2017-19 committati); nulla su Hugging Face (`hub_repo_search`,
query multiple); un dataset accademico su Zenodo (Whelan & Hegarty 2024,
"A Tale of Two Markets") copre 1X2 e Asian handicap, non O/U 2.5 — scartato.

Per verificare i 6 dataset Kaggle più promettenti senza fidarsi delle sole
descrizioni (WebFetch era inutilizzabile in sessione: 403 anche su
`example.com`, bug noto del tool, non un blocco del sito — vedi
`docs/MANUALE_SOPRAVVIVENZA.md`), probe diagnostico via runner Actions
(`scripts/probe_kaggle_ou_datasets.py`, workflow
`.github/workflows/kaggle-ou-probe.yml`, trigger
`.github/kaggle-ou-probe-trigger`): scarica ogni dataset con `kagglehub` e
stampa nel log colonne/copertura, senza committare nulla. Candidati:
`mexwell/historical-football-resultsbetting-odds-data` (mirror completo
football-data, tutte le divisioni/stagioni), `louischen7/football-results-
and-betting-odds-data-of-epl`, `thedevastator/uncovering-betting-patterns-
in-the-premier-leagu`, `eladsil/football-games-odds`, `ahmadasadi00/football-
betting-odds`, `rayenjlassi/more-than-20k-footballsoccer-match` (run
[29881936699](https://github.com/BTConomista/Polymarket-oracle/actions/runs/29881936699)).

**Risultato: negativo su tutti e 6.** I quattro con colonne quote (mexwell,
louischen7, thedevastator, e le stagioni-EPL dentro eladsil/ahmadasadi00/
rayenjlassi non hanno affatto colonne quote) sono ricostruzioni dirette di
football-data.co.uk — stesso schema colonne, incluso **ogni file** che copre
2017-18/2018-19 per le 3 leghe (`E0`=Premier, `I1`=Serie A, `SP1`=La Liga):
`PSH/PSD/PSA` + `PSCH/PSCD/PSCA` (Pinnacle 1X2 apertura/chiusura — li abbiamo
già, Fase 61) e **una sola** istantanea O/U, `BbOU, BbMx>2.5, BbAv>2.5,
BbMx<2.5, BbAv<2.5` — zero colonne apertura/chiusura O/U distinte, su
nessuna delle righe ispezionate. Conferma diretta (non solo per inferenza
dalla ricerca web) che il buco è strutturale nella fonte a monte, non un
limite di un singolo dataset: chiunque riesporti football-data.co.uk eredita
lo stesso buco.

**Fase A chiusa, negativa** (principio §1.4: si documenta anche l'esito
negativo). Nessun dato ingresa negli snapshot.

**Esito Fase B (probe live, runner GitHub Actions, non da questa sessione
cloud).** Il sito è raggiunto correttamente (pagina risultati OK, 380
partite trovate), ma l'endpoint delle quote indovinato
(`/match-odds/{id}/1/ou/`) risponde **404 su tutte le partite testate**.
Diagnostica sulla pagina-partita grezza: **zero** occorrenze della stringa
`match-odds` in tutta la pagina; il div `#bettingTabs` (dove vivono i tab
quote) contiene **solo un "1X2" DISABILITATO** (`class="...disabled..."`) e
**nessun tab O/U**. Non è un problema di parsing/URL sbagliato: BetExplorer
sembra aver **ritirato la funzione di confronto-quote per le partite
archiviate così vecchie** (~8 anni) — un headless browser non aiuterebbe,
il dato non è più esposto lì, non solo nascosto dietro JavaScript.

**Copertura per lega (richiesta utente, "quali campionati raggiungiamo?"):
il blocco è generale, non specifico di una lega.** Stesso identico pattern
(0 occorrenze `match-odds`, `#bettingTabs` con solo "1X2" disabilitato,
0.0% copertura) verificato su **tutte e 3 le leghe** target 2017-18 — Serie
A, Premier League, La Liga — quindi con altissima probabilità su **tutte e
6** le combinazioni lega-stagione del piano (le due stagioni 2017-18/18-19
sono la stessa "età" agli occhi del sito). **Nessuna delle 6 è raggiungibile
con questo metodo**: non è un problema risolvibile lega per lega, è un
limite strutturale del sito per l'intera finestra temporale che serve al
progetto.

**Fase B chiusa, negativa** (principio §1.4 del CLAUDE.md: si documenta
anche l'esito negativo). Nota tecnica scoperta nel processo: quando
l'artifact zip del workflow non è scaricabile dalla sessione (dominio Azure
blob bloccato), la diagnostica va stampata nei log del job (leggibili via
MCP GitHub), non salvata solo nell'artifact.

**Implicazione per la Fase D**: OddsPortal richiede **login** per lo
storico apertura/chiusura per singola quota (già noto da un tentativo
precedente, vedi `docs/MANUALE_SOPRAVVIVENZA.md`) — indipendente dal blocco
geo/ADM per IP italiano, quindi si ripresenterebbe anche dal runner
Actions: servirebbero credenziali reali in un secret, un salto di
complessità/rischio rispetto a un semplice scraper pubblico.

**INGRESSO dei dati** (qualunque fase li produca): stessi controlli di sempre
— gol della fonte == gol dello snapshot su OGNI riga (join per data+squadre
canonicalizzate), overround ≥ 1, apertura≠chiusura nel ~90%+; poi le colonne
entrano negli snapshot via la pipeline quote esistente (`loader.refresh_odds`
accetta nuove preferenze-colonna), le **2.279 stime di chiusura si ritirano**
(`data/estimates/ou_close_2017_19.csv` si rigenera vuoto o quasi) e
DATI.md §2/§5 si aggiorna. Fase nuova nel diario con i numeri.

**Note legali/etiche**: uso di ricerca personale; rispettare robots.txt e
throttling aggressivo (≥2s tra richieste); niente ridistribuzione dei dati
grezzi scrappati fuori dal repo privato di lavoro; preferire SEMPRE un dataset
già pubblicato (fase A) allo scraping diretto.

---

## 4 · Prompt pronto per un'AI con accesso al web

> Copia-incolla da qui in giù a un'AI con navigazione web libera (la nostra
> sessione di sviluppo è dietro un proxy che blocca questi siti).

```
Sto cercando un dataset STORICO di quote calcio con una riga per partita.

BERSAGLIO ESATTO:
- Campionati e stagioni: Serie A, Premier League, La Liga — stagioni 2017-18
  e 2018-19 (760 partite per lega, 2.280 totali).
- Mercato: Over/Under 2.5 goal (linea esattamente 2.5).
- Per ogni partita servono QUATTRO quote decimali: Over e Under di APERTURA
  (prima quota pubblicata) e Over e Under di CHIUSURA (al calcio d'inizio).
  Apertura e chiusura devono essere istantanee DIVERSE, non la stessa quota
  ripetuta.
- Preferenza sul bookmaker: Pinnacle; altrimenti media multi-book; altrimenti
  Bet365. Va bene un mix se dichiarato riga per riga.
- Ogni riga deve avere: data, squadra di casa, squadra ospite e possibilmente
  il punteggio finale (mi serve per verificare gli abbinamenti).

DOVE CERCARE (in quest'ordine):
1. Dataset già pubblicati: Kaggle, GitHub (repo di scraper OddsPortal o
   BetExplorer che committano CSV), Hugging Face, Zenodo/OSF (dataset
   accademici su mercati di scommesse). Query utili: "oddsportal dataset csv",
   "football odds opening closing 2018", "over under 2.5 historical odds".
2. Se non trovi nulla di pronto: verifica che betexplorer.com e oddsportal.com
   espongano, sulle pagine-partita di quelle stagioni, le quote O/U 2.5 con
   apertura e chiusura, e dimmi COME sono strutturate le pagine (URL di una
   pagina-risultati di stagione + URL di una pagina-partita + dove stanno le
   quote O/U e il movimento apertura→chiusura).

CONTROLLI PRIMA DI PROPORMI UNA FONTE (scarta chi li fallisce):
- la linea è esattamente 2.5 (non 2.25/2.75);
- 1/quota_over + 1/quota_under > 1 su ogni riga (margine del book);
- apertura ≠ chiusura nella grande maggioranza delle righe;
- copertura ≥ 95% delle 760 partite per lega;
- il dataset è uno SCRAPE di quote reali, NON una ricostruzione da modello
  (chiedi/verifica come è stato costruito).

FORMATO DELLA RISPOSTA:
1. elenco delle fonti trovate con link diretti, copertura stimata per
   (campionato, stagione), e quale bookmaker/aggregato contengono;
2. per la migliore: un campione di 5 righe con le 4 quote, così verifico;
3. se è un file scaricabile: il link diretto al download;
4. se serve scraping: le istruzioni di struttura del punto 2 sopra.

NON mi servono: quote 1X2 (le ho già), altre linee O/U, stagioni dal 2019-20
in poi (le ho già), quote attuali.
```

---

*Aggiornare questo documento con l'esito di ogni fase (A/B/C/D) e chiuderlo
quando i dati saranno entrati negli snapshot (o quando si decide di fermarsi:
anche quello è un esito, da scrivere).*
