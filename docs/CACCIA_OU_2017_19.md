# Caccia alle quote O/U 2017-19 — specifica del dato e piano di ricerca

L'**ultimo blocco di dati reali mancante** (vedi [DATI.md](DATI.md)): le quote
Over/Under 2.5 di **apertura** (4.564 celle, mai avute) e — già coperte da una
stima, ma sostituibili con la verità — quelle di **chiusura** delle stagioni
**2017-18 e 2018-19** nelle 3 leghe. Questo documento dice esattamente COSA
cercare, DOVE, con quale piano, e contiene un **prompt pronto** da dare a
un'AI con accesso libero al web.

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
quota_over25_APERTURA  · quota_under25_APERTURA
quota_over25_CHIUSURA  · quota_under25_CHIUSURA
fonte (sito/dataset) · book ("average" oppure nome del bookmaker)
```

**Bonus** (2 partite sparse senza 1X2 di apertura): Torino-Fiorentina
10/01/2022 (Serie A, recupero) e Alaves-Real Sociedad 14/10/2017 (La Liga).

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
| **A** | ricognizione dataset esistenti (prompt AI qui sotto, oppure a mano) | 1-2 ore | trovato un dataset che passa i criteri §1 → salta a INGRESSO |
| **B** | tracer BetExplorer via GitHub Actions: **una sola stagione** (Serie A 2017-18, 380 partite, throttle 2-3s/richiesta ≈ 25 min) | mezza giornata | copertura ≥95% E apertura≠chiusura reali → scala |
| **C** | scala alle 6 (lega, stagione); bundle `files/ou_2017_19_bundle.json` | 1 giorno | — |
| **D** | OddsPortal headless (solo se B fallisce) | 2+ giorni, fragile | — |

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
