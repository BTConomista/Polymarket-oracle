# Stagione 2026-27 — raccolta quotidiana

> **Stato: SPECIFICA, non ancora implementazione.** Questo file dice *cosa*
> vogliamo, *perché*, *da dove* e *in che ordine*. Il codice arriva dopo, un
> pezzo alla volta, e ogni pezzo aggiorna questo file.
> Scritto il **28 luglio 2026** (Fase 119). Prima partita: **15 agosto**.

---

## 0 · A che cosa serve davvero questa cartella (onestà preliminare)

Va detto subito, perché cambia le priorità e perché il progetto ha già pagato
per impararlo: **questa raccolta non nasce per «dare più feature al modello».**

Le Fasi 4c-33 hanno esplorato **tutti** i dati interni già disponibili (gol, xG,
npxG, PPDA, deep completions, valore rosa, assenze, riposo, forma, poste in
palio) e il verdetto è stato uniforme: **ridondanti o rumore**. Il tetto non è
architetturale, è **informativo** — con ~380 partite a stagione e centinaia di
covariate candidate, aggiungere colonne non sposta il log-loss, lo fa solo
sembrare più basso in-sample. Chi legge questa cartella pensando «più dati =
modello migliore» ripeterà un esperimento già fatto sei volte.

Il valore di questa raccolta è **altrove**, ed è di tre tipi:

1. **L'informazione che il mercato ha e noi no.** La Fase 93 ha isolato dove
   vive il gap col mercato — l'**88% è discriminazione casa-ospite**, non massa
   del pareggio — e la Fase 78 indica il candidato: la **formazione ufficiale a
   T−1h**. È l'unica leva mai identificata e mai testata, e si può raccogliere
   **solo in avanti**.
2. **Il dataset notizia → movimento della quota.** Questo non esiste in nessun
   archivio comprabile: richiede di osservare *insieme*, ogni giorno, la notizia
   e il prezzo. È la cosa più originale che possiamo costruire, ed è
   esattamente ciò che il raccoglitore Smarkets (Fasi 116/118) rende possibile.
3. **Un archivio che vale su più stagioni.** Il principio §1.7 impone 3+
   stagioni prima di concludere. Questa è la stagione 1: quasi nulla di ciò che
   raccogliamo qui produrrà una conclusione entro maggio. Va costruito lo
   stesso, perché il costo di *non* averlo si paga per anni.

**Corollario operativo**: la priorità non è «quanti dati», è **quali dati si
perdono per sempre se non li prendo oggi**. La colonna «⏳ recuperabile?» della
lista al §4 è la vera lista delle priorità.

---

## 1 · La regola che decide l'architettura: fatto ≠ giudizio

Metà di ciò che vogliamo raccogliere (umore dell'ambiente, allenatore a
rischio, probabile formazione, lettura tattica) **non è un dato misurato**: è un
giudizio prodotto leggendo delle notizie. Trattare le due cose allo stesso modo
sarebbe il difetto peggiore del repo, quello che la regola **R6** chiama *finto
pieno*: un valore che **sembra** una misura e non lo è.

Quindi ogni record raccolto porta obbligatoriamente:

```json
{
  "valore": "...",
  "tipo": "fatto" | "giudizio",
  "fonte": "https://…",            // per i fatti: URL + orario di accesso
  "evidenza": ["…"],               // per i giudizi: le frasi su cui si basa
  "confidenza": 0.0-1.0,           // solo per i giudizi
  "raccolto_utc": "2026-08-14T09:00:00Z"
}
```

Regole non negoziabili, ereditate da `CLAUDE.md` §5 e §5-bis:

- un **giudizio** non entra mai in una colonna che sembra una misura;
- un giudizio senza **evidenza citata** non si scrive: si scrive «non lo so»;
- i giudizi **non si usano per simulare ROI**, mai (§5);
- niente modifiche a mano: ogni correzione passa da uno script idempotente che
  verifica il valore-prima (**R3**);
- un'anomalia si dichiara **anche quando non è un errore** (**R4**);
- il dato è il risultato del **campo**, non del tribunale (**R1**).

---

## 2 · Due assi ortogonali (risolve il dubbio «file al giorno *o* cartella per squadra?»)

Non è un aut-aut: sono **due cose diverse** e servono entrambe.

| asse | cosa risponde | proprietà indispensabile |
|---|---|---|
| **tempo** (`giornaliero/`) | «che cosa sapevamo il giorno D?» | **immutabile, append-only** |
| **entità** (`club/`) | «che cos'è l'Inter, e in quali competizioni gioca?» | **anagrafica stabile + viste rigenerabili** |

**Perché l'immutabilità non è pignoleria.** Se lo stato di una squadra vive in
un file che sovrascriviamo ogni giorno, al 20 maggio non sapremo più *che cosa
sapevamo il 14 agosto* — e con quello muore il test prospettico, cioè il motivo
per cui stiamo raccogliendo. Il file del giorno è la **fonte di verità**; la
cartella del club contiene (a) l'anagrafica, che cambia raramente e con un
registro delle modifiche, e (b) viste **rigenerabili** dai file giornalieri,
marcate come tali e mai modificate a mano.

L'intuizione dell'utente — *una cartella per squadra, così serve per Serie A,
Coppa Italia e Champions insieme* — è giusta e va tenuta: la **squadra** è
l'entità, la **competizione** è un attributo della partita, non della cartella.

### Struttura

```
data/stagione_2026_2027/
├── README.md                        questo file
├── _anagrafica/                     raccolto UNA VOLTA a inizio stagione (+ delta)
│   ├── competizioni.json            quali tornei, formato, date, regole di classifica
│   ├── ranking_uefa_club.json       coefficienti per club
│   ├── ranking_fifa_nazionali.json  per il lavoro sulle nazionali (§7)
│   └── stadi.json                   nome, capienza, superficie, COORDINATE (→ meteo)
├── giornaliero/                     APPEND-ONLY, immutabile
│   └── 2026-08-14/
│       ├── raccolta.json            tutti i record del giorno (fatti + giudizi)
│       ├── fonti.json               URL, orario, esito HTTP, hash di ogni fetch
│       └── quote.json               istantanea del mercato (→ data/smarkets_matches/)
└── club/
    └── ITA/                         ISO-3166 alpha-3 del PAESE del club
        └── inter/                   slug stabile (vedi club/README.md)
            ├── anagrafica.json      rosa, obiettivi, competizioni, allenatore
            ├── rosa_storico.jsonl   una riga per ogni variazione (mercato, valori)
            └── vista_corrente.md    ⚙️ RIGENERABILE — non modificare a mano
```

**Nota sulle nazionalità.** `ITA/` è il paese del **club**, non della lega: serve
perché §7 prevede di aggiungere club di seconda/terza serie e di campionati che
oggi non modelliamo (Turchia, Portogallo, Olanda…), che incontriamo nelle coppe
europee. Un club sta in **una sola** cartella per sempre, anche se cambia
categoria: è la sua identità, non la sua classifica.

---

## 3 · Il vincolo che ho misurato oggi, e che riduce l'ambizione «tutto in automatico»

**⚠️ La maggior parte dei siti di notizie sportive VIETA esplicitamente i
crawler AI.** Misurato il 28/07/2026 leggendo i `robots.txt` (regola **R5.3**):

| fonte | `ClaudeBot` / `anthropic-ai` | uso automatico? |
|---|---|:--:|
| **transfermarkt.it** (rose, valori) | `Disallow: /` | ❌ **NO** |
| **gazzetta.it** | `Disallow: /` | ❌ NO |
| **bbc.co.uk** | `Disallow: /` | ❌ NO |
| **kicker.de** | `Disallow: /` | ❌ NO |
| **marca.com** | `anthropic-ai: Disallow: /` | ❌ NO |
| **theguardian.com** | presenti con **0 regole** = permesso | ✅ **SÌ** |
| **legaseriea.it** | solo `*`, sezioni tecniche escluse | ✅ SÌ |
| **open-meteo.com** | nessuna restrizione | ✅ SÌ |
| **api.football-data.org** | nessun `robots.txt`; API con chiave | ✅ SÌ |
| **wikipedia.org** | consentito (+ REST API ufficiale) | ✅ SÌ |
| **understat.com** | `User-agent: * → Disallow: /` | ⚠️ **vedi sotto** |
| **fbref.com**, **sofascore.com** | — | ❌ 403 (già noto) |

**Conseguenze, da accettare invece di aggirare:**

1. **Transfermarkt non si scrapa.** Le rose e i valori si prendono (a) dalla
   raccolta **manuale dell'utente** — una persona che apre un sito col browser
   non è un crawler, ed è già il metodo dichiarato dalla regola **R2** per i
   valori 2025-26 — oppure (b) da fonti che lo consentono (football-data.org,
   Wikidata). **Nessun aggiramento**: niente user-agent camuffati, niente VPN.
2. **Il livello «notizie» non può poggiare sullo scraping della stampa
   sportiva.** Restano tre vie legittime: fonti che ci consentono (Guardian,
   siti ufficiali di lega e club), **API su licenza**, e la **ricerca web fatta
   da Claude** in una routine — che è una ricerca, non un crawl di massa, e
   rispetta a sua volta i `robots.txt`.
3. **⚠️ Rilievo su codice già in produzione**: `understat.com` vieta tutto a
   `*`, ma `src/data/understat.py` scarica da lì (usato fino alla Fase 103).
   **Non l'ho toccato**: è una decisione dell'utente, non mia, e disattivarlo
   di mia iniziativa romperebbe la pipeline. Va deciso esplicitamente — e la
   decisione va scritta, qualunque sia.

---

## 3-bis · La buona notizia: metà della lista è già disponibile, **su licenza**

Il divieto del §3 sembra chiudere rose, valori e statistiche. **Non è così**, e
la soluzione era già in casa: `davidcariboo/player-scores` su Kaggle — la
**fonte ufficiale** dello `squad_value` del progetto dalla Fase 67, **CC0**
(pubblico dominio, redistribuzione consentita), aggiornata ~settimanalmente.
Misurata oggi (versione 673, 213 MB):

| file | che cosa dà | copre la nostra lista |
|---|---|---|
| `player_valuations.csv` | **507.815** valutazioni, 2000-01 → **2026-02-27** | §4.1 valori di mercato |
| `players.csv` | anagrafica giocatori | §4.1 rosa |
| `game_lineups.csv` | **formazioni**: `starting_lineup` vs `substitutes`, ruolo, numero, capitano | 🎯 §4.4 — permette di **scorare** la formazione probabile contro quella vera |
| `game_events.csv` | eventi **col minuto**: gol, cartellini, sostituzioni, rigori | §4.3 fasce di 15′, cartellini per giocatore, pattern di sostituzione |
| `appearances.csv` | presenze e **minuti giocati** per giocatore | §4.2 carico, §4.3 rotazione |
| `transfers.csv` | trasferimenti | §4.2 mercato |
| `games.csv` | 88.958 partite, 2006-06 → **2026-07-06** | calendario e risultati |
| `national_teams.csv` | nazionali | §7.3 |

**Copertura ben oltre le 5 leghe** — 65 competizioni:

- **31 campionati nazionali**: fra cui **Turchia, Portogallo, Olanda, Belgio,
  Scozia, Grecia, Austria, Svizzera, Danimarca, Croazia, Serbia, Ucraina,
  Polonia, Romania**, più Brasile, Argentina, USA, Messico, Giappone, Corea,
  Arabia Saudita, Australia. È esattamente il §7.5 («club di campionati che non
  modelliamo ma che incontriamo nelle coppe»), **già coperto**;
- **10 coppe nazionali**: Coppa Italia, Copa del Rey, DFB-Pokal… (§7.1);
- **coppe internazionali**: Champions League e le sue qualificazioni (§7.2);
- **5 competizioni per nazionali**: Europei, Copa América, Coppa d'Africa,
  Coppa d'Asia (§7.3).

### Il confine che conta: retrospettivo ≠ prospettico

Questo dataset dice **che cosa è successo**, non che cosa succederà. Non
contiene — e non può contenere — nulla di ciò che serve *prima* della partita:
infortuni di oggi, formazione probabile, previsione meteo, allenatore a
rischio, umore. Quindi:

| livello | fonte | cadenza | irrecuperabile? |
|---|---|---|:--:|
| **fatti retrospettivi** (rose, valori, minuti, eventi, formazioni giocate) | Kaggle CC0 | **settimanale** | 🟢 no — si ri-scarica quando si vuole |
| **stato pre-partita** (infortuni, probabili, meteo, quote, notizie) | raccolta quotidiana | **giornaliera** | 🔴 **sì** |

**Conseguenza sul piano**: il lavoro giornaliero si **restringe** a ciò che deve
davvero essere giornaliero. Tutto il resto è un `kagglehub.dataset_download`
una volta a settimana. È il principio §1.3 del progetto — testare la versione
economica di un'idea prima di costruire l'infrastruttura costosa.

**Due limiti dichiarati**, perché non diventino sorprese:

1. le valutazioni si fermano al **27/02/2026** in questa versione: c'è un
   **ritardo di ~5 mesi** sul valore «attuale». Per il valore di **agosto 2026**
   serve o attendere l'aggiornamento a monte, o la raccolta manuale (§3.1);
2. è una fonte **secondaria** rispetto a Transfermarkt (da cui deriva): vale la
   regola **R2** — la scala va misurata contro la primaria dove entrambe
   esistono, mai innestata in silenzio.

---

## 3-ter · ⚠️ IL PROBLEMA DELLA ROSA, e come è stato risolto

Va scritto per esteso perché è il difetto che ha richiesto tre correzioni
successive, e perché chiunque userà questi file deve sapere che cosa sta
leggendo.

### Il problema

Il dataset CC0 associa i giocatori al club con `current_club_id`, che è
**l'ultimo club noto**, e la sua fotografia è ferma al **27/02/2026**. Ne
seguono tre guasti, tutti trovati controllando e non fidandosi:

1. **rose gonfie**: senza filtro il Genoa contava **162** giocatori (gente
   ferma al 2017). Filtrando sull'ultima stagione del giocatore → mediana 36;
2. **residuo sistematico**: anche filtrando restava **+6** sul `squad_size`
   ufficiale della stessa fonte — prestiti in uscita e giovani aggregati;
3. **il guasto grave**: sulle squadre col record vecchio la somma dei valori
   dava **«Frosinone, valore rosa 0.8 M€» su 1 giocatore di 31** — tre ordini
   di grandezza di errore, in un campo che *sembra* una misura (**R6**).

E soprattutto: **il mercato estivo 2026 non c'è**. La rosa di febbraio non è la
rosa che scenderà in campo il 15 agosto.

### La soluzione: Wikipedia come fonte della rosa, dataset per i valori

`scripts/fetch_rose_wikipedia.py` (Fase 121). Wikipedia **ci consente** il bot
(a differenza di Transfermarkt, §3), ha una API ufficiale, ed è aggiornata da
persone in tempo quasi reale: al 28/07/2026 la voce dell'Inter dichiarava
«*Rosa e numerazione aggiornate al 26 luglio 2026*» citando il sito ufficiale
del club.

**Un solo parser**, con la Wikipedia *italiana* anche per i club stranieri: le
altre lingue usano formati diversi (`{{Feff joueur}}` in francese, tabelle in
inglese), e cinque parser sarebbero cinque punti di rottura silenziosa.

⚠️ **Ma l'ipotesi «l'italiana li copre tutti» è FALSA, e va detto.** L'avevo
dedotta da due club grossi (Real Madrid 29, Manchester City 32) e generalizzata:
la misura su tutte e 96 dice altro.

| lega | rose trovate |
|---|:--:|
| Serie A | **18/20** |
| Premier League | 12/20 |
| La Liga | 6/20 |
| Ligue 1 | 3/18 |
| Bundesliga | 2/18 |
| **totale** | **41/96** |

La Wikipedia italiana scrive la voce-stagione dei club esteri solo per i più
noti. **Il seguito è già chiaro e non ancora fatto**: per le altre quattro
leghe si va sulla Wikipedia *locale* (`en`, `es`, `de`, `fr`), una voce-stagione
per club, con il parser del template di quella lingua — verificato che esistono
(es. `Saison 2026-2027 du Paris Saint-Germain` con `{{Feff joueur}}`, 36 voci).

**Il discrimine prima squadra / giovani aggregati è MISURATO, non stimato.**
Le voci elencano nella stessa sezione i tesserati con il **numero di maglia** e
i giovani aggregati con `n=` **vuoto**: al Napoli sono **26 + 21**. È il numero
di maglia a separarli, non una soglia di età o di valore inventata da noi.
Verifica che chiude il cerchio: l'Inter esce con **25** numerati, cioè
*esattamente* il `squad_size` ufficiale.

### Come si combinano le due fonti

| domanda | fonte | perché |
|---|---|---|
| **chi** è in rosa oggi | Wikipedia | sta al passo col mercato estivo; dichiara la sua data |
| **quanto vale** ciascuno | dataset CC0 | Wikipedia non ha i valori |
| **chi è disponibile** oggi | ❌ nessuna delle due | infortuni e squalifiche sono **stato quotidiano**: §4.2, cartella `giornaliero/` |

Le due liste **non coincidono**, ed è informazione: chi c'è su Wikipedia e non
nel dataset è un acquisto estivo (valore da recuperare); chi c'è nel dataset e
non su Wikipedia è partito. Lo scarto va **letto**, non appianato.

### Il risultato che conta: Wikipedia riempie proprio i buchi del dataset

Delle **14** squadre che il dataset copre male (10 stantie + 4 assenti — tutte
neopromosse), Wikipedia ne risolve **4**, e sono i casi peggiori:

| squadra | rosa dal dataset | rosa da Wikipedia |
|---|:--:|:--:|
| Coventry City | **0** (assente) | **27** |
| Frosinone Calcio | 1 | **30** |
| Hull City | 7 | **27** |
| AC Monza | 1 | **22** |

Le altre 10 aspettano le Wikipedia locali. È il motivo per cui questa fonte
vale: non aggiunge un decimale ai club che già conoscevamo, **riempie i vuoti**.

### Che cosa resta aperto

- **55 rose su 96** (le leghe non italiane): serve il passaggio alle Wikipedia
  locali descritto sopra;
- i **valori** dei nuovi acquisti mancano finché il dataset non aggiorna;
- le rose che nessuna Wikipedia copre vanno risolte **a mano**, mai stimate;
- «infortunato o squalificato oggi» non è in nessuna delle due fonti: è
  esattamente il lavoro del livello giornaliero (§5, passo 4).

---

## 3-quater · Due cose che il piano dava per scontate, e non lo sono (Fase 123)

### A · Lo stadio è un dato PER-PARTITA, non una proprietà della squadra

Domanda dell'utente: *«verifica se ogni squadra giocherà nel proprio stadio
tutte le partite (magari in europa gioca in un altro stadio)»*. **Misurato** su
`games.csv` (stagioni 2023+, impianto abituale = il più frequente in
campionato), quota di partite «in casa» giocate **altrove**:

| competizione | quota |
|---|---:|
| campionato | **5,0%** (958/19.067) |
| coppa nazionale | **10,8%** (94/868) |
| **coppe europee** | **12,3%** (74/604) |
| supercoppe e altro | **16,4%** (202/1.232) |

Cioè **una gara europea interna su otto** non si gioca nell'impianto abituale.
I casi non sono marginali: Atalanta 29/83, Atlético 30/84, Barcellona 25/82,
Shakhtar 25/67 (ristrutturazioni, requisiti UEFA, campi squalificati, guerre).

**Conseguenza applicata**: nel record giornaliero lo stadio esce con
`stadio_confermato: false` e la nota del perché. È l'impianto **abituale**, cioè
un'ipotesi dichiarata — non un fatto verificato per quella partita. Confermarlo
di volta in volta è lavoro aperto (fonte: voce Wikipedia della partita, sito
ufficiale della lega).

### B · Squalifiche e diffide si CALCOLANO, non si cercano

`src/data/disciplina.py`. Bastano i cartellini (che abbiamo, col minuto) e il
regolamento: è **l'unico pezzo del bollettino che non dipende da nessun sito**,
quindi l'unico immune ai vincoli di `robots.txt` del §3.

⚠️ **Le soglie non sono universali e cambiano.** Lette il 28/07/2026, non a
memoria:

| competizione | squalifica a | poi | note |
|---|:--:|---|---|
| Serie A | **5** | 10, 14, 17, 19, poi **ogni** | diffida già al 4° |
| Premier League | **5** | 10 (2 turni), 15 (3 turni) | soglie legate alla 19ª/32ª giornata |
| LaLiga | **5** | ogni 5 | |
| Bundesliga | **5** | ogni 5 | |
| **Ligue 1** | **5** | ogni 5 | ⚠️ **cambiata nel 2025-26**: prima erano 3 |
| **UEFA** | **3** | 5ª, 7ª… (**dispari**) | azzerate dopo play-off e dopo i quarti |

Chi codificasse «il calcio» con una soglia unica sbaglierebbe **due leghe su
cinque più la UEFA**, e il difetto non si vedrebbe: produrrebbe una lista di
diffidati **plausibile** e sbagliata. Per questo le soglie stanno in una
tabella con la fonte accanto, e un test le fissa una per una.

**Validato sui cartellini veri** (Serie A 2025-26): 11.926 presenze, 1.361
gialli, 421 giocatori ammoniti; a fine stagione **58 diffidati** e 45 sulla
soglia. La distribuzione è quella attesa (103 giocatori a 1 giallo, 41 a 5,
1 a 12).

**Il comportamento del diffidato è un GIUDIZIO, e resta marcato tale.** La
domanda dell'utente — *un diffidato potrebbe evitare il giallo se la partita
imminente conta, o prenderselo se quella che conta è due gare dopo* — è
sensata, e il **motivo** è meccanico: la squalifica cade sulla partita
**successiva** a quella del cartellino. Quindi con `p` = importanza della
prossima e `s` = della successiva, l'incentivo a «smaltire» è `s − p`.
`incentivo_cartellino()` lo calcola, ma dichiara `tipo: "giudizio"`: **nessuno
ha mai misurato se i giocatori vi si conformino davvero**, e il valore sta nel
segno, non nel numero.

### C · Che cosa manca ancora al bollettino

| voce | stato |
|---|---|
| squalifiche, diffide | ✅ **calcolate** (vuote finché la stagione non produce cartellini) |
| stadio della partita | ⚠️ ipotesi dichiarata, da confermare per gara |
| **infortuni** | ❌ richiedono per forza una notizia esterna: è il pezzo difficile |
| **calciomercato quotidiano** | ❌ da fare: notizie per squadra, giorno per giorno |

Infortuni e mercato sono il livello «notizie» del §3: fonti che ci consentono
(Guardian, siti ufficiali), API su licenza, o ricerca web dentro una routine.

---

## 4 · La lista COMPLETA dei dati

Legenda — **tipo**: 📏 fatto misurato · 🧠 giudizio (LLM/modello) · 🔢 derivato
per calcolo. **⏳**: 🔴 si perde per sempre se non raccolto oggi · 🟡 recuperabile
a fatica · 🟢 sempre recuperabile a posteriori.

### 4.1 · Anagrafica — una volta a inizio stagione, poi *delta*

| dato | tipo | ⏳ | perché conta / note |
|---|:--:|:--:|---|
| Rosa completa (nome, data nascita, ruolo, piede, altezza, nazionalità, numero) | 📏 | 🟡 | base di tutto il resto |
| **Valore di mercato per giocatore** | 📏 | 🔴 | i valori vengono **riscritti** dalle fonti: quello di agosto sparisce |
| Valore totale rosa + valore dell'XI titolare | 🔢 | 🔴 | l'XI pesa più della rosa: 11 giocatori giocano |
| Anno di scadenza contratto | 📏 | 🟡 | in scadenza = rischio distrazione/mercato |
| Provenienza (acquisto, prestito, rientro, vivaio) | 📏 | 🟡 | l'integrazione dei nuovi ha un costo |
| **Giocatori fuori progetto / fuori lista** | 📏 | 🔴 | rosa nominale ≠ rosa disponibile |
| **Lista UEFA (25 + lista B)** | 📏 | 🔴 | chi è escluso dalle coppe: cambia la rosa *per competizione* |
| Allenatore: nome, data nomina, contratto, precedenti | 📏 | 🟡 | |
| **Obiettivi dichiarati** (società e pubblici) | 📏/🧠 | 🔴 | dichiarazioni di luglio: a maggio nessuno le ripubblica |
| Competizioni a cui partecipa | 📏 | 🟢 | campionato, coppa nazionale, supercoppa, UEFA, Mondiale per club |
| Stadio: nome, capienza, superficie, **coordinate**, altitudine | 📏 | 🟢 | le coordinate servono al meteo |
| Coefficiente/ranking UEFA del club | 📏 | 🟡 | |
| Situazione societaria: proprietà, FFP, **penalizzazioni di punti** | 📏 | 🟡 | una penalizzazione cambia gli obiettivi a stagione in corso |
| Cambio stadio / stadio provvisorio | 📏 | 🟡 | il vantaggio-casa non è trasferibile |

### 4.2 · Stato quotidiano — FATTI

| dato | tipo | ⏳ | perché conta / note |
|---|:--:|:--:|---|
| **Infortuni**: giocatore, tipo, data, rientro previsto | 📏 | 🔴 | il *rientro previsto* è una previsione che poi nessuno archivia |
| **Squalificati**: giornate, competizione | 📏 | 🟡 | ⚠️ le squalifiche sono **per competizione** |
| **Diffidati** (a un cartellino dalla squalifica) | 📏 | 🔴 | quasi mai archiviato, e cambia il modo di giocare del singolo |
| Allenamenti differenziati / a parte | 📏 | 🔴 | il primo segnale, giorni prima del bollettino ufficiale |
| **Convocazioni in nazionale**: partenza, n. partite, fuso, minuti, rientro | 📏 | 🔴 | la sosta è il maggiore shock di disponibilità della stagione |
| Minuti giocati per giocatore (7/14/30 giorni) | 🔢 | 🟢 | carico → turnover |
| Km percorsi e fusi orari attraversati | 🔢 | 🟡 | trasferte europee lontane |
| Riposo fra le partite | 🔢 | 🟢 | già in `rest_days_full` |
| Prossime 3 partite: data, competizione, avversario | 📏 | 🟢 | base del turnover atteso |
| **Meteo previsto allo stadio** (T, pioggia, vento, umidità) | 📏 | 🔴 | la *previsione* è irrecuperabile; il consuntivo no |
| Orario del match (12:30 vs 20:45) | 📏 | 🟢 | caldo, ritmo |
| **Quote della prossima partita + movimento** | 📏 | 🔴 | ✅ già coperto (Fasi 116/118) |
| Trasferimenti conclusi o imminenti | 📏 | 🟡 | |
| **Cambio allenatore** (avvenuto) | 📏 | 🟢 | |
| 🎯 **Arbitro designato** + sue statistiche (cartellini, rigori) | 📏 | 🔴 | **PRIORITÀ ALTA, misurata**: vedi §4-bis. La designazione esce ~2 giorni prima e poi sparisce |
| Stadio: porte chiuse, settore ospiti chiuso, campo neutro | 📏 | 🔴 | tocca direttamente il vantaggio-casa |
| **Contestazione tifosi / sciopero della curva** | 📏/🧠 | 🔴 | il vantaggio-casa è anche pubblico |
| Biglietti venduti / affluenza attesa | 📏 | 🔴 | |

### 4-bis · 🎯 L'ARBITRO: perché è priorità alta, e non un dettaglio di colore

**Decisione dell'utente (28/07/2026), su evidenza misurata alla Fase 125.**
Nella raccolta della nuova stagione **l'arbitro va registrato per ogni
partita**, alla pari di meteo e quote.

**Non è un'opinione, sono tre numeri.** Backtest walk-forward su 14 stagioni e
50.911 osservazioni (partita × lato), `scripts/_run_fase125_cartellini.py`:

| fattore che aiuta a prevedere i cartellini | guadagno | IC95% |
|---|---:|---|
| quale squadra gioca | +0.00440 | [+0.00309, +0.00576] |
| contro chi gioca | +0.00157 | [+0.00050, +0.00260] |
| in casa o in trasferta | +0.00371 | [+0.00281, +0.00464] |
| **chi arbitra** | **+0.00368** | [+0.00269, +0.00469] |

**L'arbitro vale quanto il fattore campo.** Ed è un'informazione che nessun
altro dato del progetto contiene: la Fase 96 aveva già misurato che i
cartellini sono **ortogonali ai gol** (|corr| ≤ 0.06), quindi qui non stiamo
ri-scoprendo la forza delle squadre da un'altra angolazione.

**E si può usare per prevedere, non solo per descrivere.** Il test che la Fase
99 rende obbligatorio — *misurato ≠ prevedibile* — è superato: la tendenza di
un arbitro in una stagione **si ritrova** in quella dopo, corr **+0.352**
IC95% [+0.299, +0.405]. Un arbitro severo quest'anno è severo anche il
prossimo.

**Perché è 🔴 irrecuperabile.** Le designazioni si pubblicano **due giorni
prima** della giornata e poi spariscono dai siti: a stagione finita si trova
chi *ha* arbitrato (e infatti il dato storico ce l'abbiamo, sul 100% delle
partite), ma **non si ricostruisce che cosa sapevamo prima del fischio**. Per
il test prospettico serve la prima.

**Che cosa registrare, per partita:**

| campo | note |
|---|---|
| nome dell'arbitro designato | la chiave del join: attenzione alle grafie (§`club/README.md`) |
| data e ora della designazione | serve a dimostrare che la sapevamo **prima** |
| VAR e assistenti | non ancora misurati, ma costano zero raccolti insieme |
| eventuale cambio dell'ultimo minuto | sostituzioni per infortunio capitano: se non lo registriamo, il join dà l'arbitro sbagliato |

**Dove prenderlo.** Le leghe pubblicano le designazioni ufficialmente e
`legaseriea.it` è fra le fonti **consentite** dal §3 (il suo `robots.txt` non ci
vieta nulla). Per le altre quattro va verificato sito per sito, con la stessa
regola: prima il `robots.txt`, poi il fetch.

⚠️ **Un avvertimento sul valore, per non promettere troppo.** Tutto questo vale
sul mercato **cartellini**. Sull'1X2 l'arbitro non è mai stato dimostrato utile,
e la Fase 126 ha aggiunto un limite ulteriore: sul **totale** di partita la
forma della distribuzione e la correlazione fra i due lati non sono
separatamente identificabili, quindi non tutto ciò che si misura per-squadra si
traduce in un guadagno sul totale.

### 4.3 · Prestazione e stile — misurabili

| dato | tipo | ⏳ | perché conta / note |
|---|:--:|:--:|---|
| Possesso, PPDA, xG/xGA, npxG, deep completions | 📏 | 🟢 | già nel repo (attenzione a §3.3) |
| **Modulo per partita e cambi di modulo** | 📏 | 🟡 | «sta cambiando modo di giocare» diventa misurabile solo così |
| Giocatori spostati di ruolo | 📏 | 🟡 | |
| **Distribuzione dei gol per fascia di 15′** (fatti e subiti) | 🔢 | 🟢 | il pattern «segna sempre alla fine» |
| Gol da palla inattiva (fatti/subiti) | 🔢 | 🟢 | |
| Rendimento casa/trasferta separato | 🔢 | 🟢 | |
| Rendimento contro alta/bassa classifica | 🔢 | 🟢 | |
| Serie aperte (imbattibilità, clean sheet, sconfitte) | 🔢 | 🟢 | |
| Rotazione: n. giocatori usati, età media dell'XI | 🔢 | 🟢 | |
| **Dipendenza da singoli**: % gol+assist del migliore | 🔢 | 🟢 | **il numero che rende quantificabile «giocatore chiave»** |
| Rigori concessi/ottenuti, chi li tira | 📏 | 🟢 | |
| Portiere: parate, **gol evitati (PSxG−GA)** | 📏 | 🟡 | un portiere in stato di grazia sposta i totali |
| Cartellini per giocatore e per squadra | 📏 | 🟢 | già coperto (Fase 96) |
| Falli commessi/subiti, corner | 📏 | 🟢 | già coperto |

### 4.4 · Giudizi — utili, ma **marcati** (§1)

| dato | tipo | ⏳ | perché conta / note |
|---|:--:|:--:|---|
| **Probabile formazione** della prossima partita | 🧠 | 🔴 | il proxy di ciò che la Fase 93 indica come bersaglio |
| Formazione **ufficiale** a T−1h | 📏 | 🔴 | 🎯 **il dato più prezioso in assoluto**: fatto, non giudizio |
| Sentiment / umore dell'ambiente | 🧠 | 🔴 | |
| **Allenatore a rischio esonero** | 🧠 | 🔴 | |
| Lettura tattica del prossimo avversario | 🧠 | 🔴 | |
| Importanza percepita della partita | 🧠 | 🔴 | «devono vincere per forza» vs «gara ininfluente» |
| Rischio turnover in vista della prossima | 🧠 | 🔴 | |
| Giocatore in forma / giocatore chiave assente | 🧠 | 🔴 | **con accanto il numero di §4.3** (dipendenza), o è aria |
| Impatto stimato di un'assenza | 🧠 | 🔴 | |

### 4.5 · Contesto di competizione

| dato | tipo | ⏳ | perché conta / note |
|---|:--:|:--:|---|
| Classifica aggiornata e distanza dagli obiettivi | 🔢 | 🟢 | |
| Fase del torneo (gruppi, eliminazione, andata/ritorno) | 📏 | 🟢 | |
| Possibilità matematiche residue | 🔢 | 🟢 | si calcola con `season_sim.py` (Fase 89) |
| Scontri diretti recenti | 🔢 | 🟢 | |
| **Derby / rivalità** | 📏 | 🟢 | più cartellini, meno gol |
| Prima/ultima giornata, turno infrasettimanale | 📏 | 🟢 | |
| **Partita importante subito dopo** (guardare avanti) | 🔢 | 🟢 | la causa più comune di turnover |
| Sosta nazionali imminente | 📏 | 🟢 | |
| Ranking UEFA club / FIFA nazionali | 📏 | 🟡 | |

### 4.6 · Il dato che nasce dall'incrocio — **il vero prodotto originale**

| dato | tipo | ⏳ | perché conta |
|---|:--:|:--:|---|
| **notizia (t) → movimento della quota (t+δ)** | 🔢 | 🔴 | non esiste in nessun archivio: richiede di osservare **insieme** notizia e prezzo, ogni giorno |
| Quota **prima** e **dopo** l'annuncio delle formazioni | 🔢 | 🔴 | quantifica quanto vale l'informazione che ci manca |
| Notizie che **non** muovono il prezzo | 🔢 | 🔴 | il risultato negativo vale quanto il positivo (§1.4) |

> **Perché questo è il pezzo forte.** Il progetto ha dimostrato (Fase 16) che il
> mercato di chiusura **ingloba** il nostro modello. Ma *quanto* si muove il
> prezzo, e *su quale notizia*, è una misura diretta di **quale informazione il
> mercato considera rilevante** — cioè la mappa di dove cercare. Non promette
> edge: promette di sapere dove guardare.

---

## 5 · Come si sviluppa (ordine per rapporto valore/costo)

**Il criterio d'ordine è la colonna ⏳, non l'interesse.** Prima ciò che si
perde, poi il resto.

| # | passo | perché ora | scadenza |
|:--:|---|---|---|
| **0** | **Importare il dataset CC0** (§3-bis) e costruirci sopra l'anagrafica | costa un `dataset_download`: è la versione **economica** di metà della lista (§1.3). Va fatto per primo perché dice quanto resta davvero da raccogliere | **subito** |
| **1** | **Anagrafica di partenza** (§4.1) delle 5 leghe: rosa, valori, obiettivi, competizioni, stadi+coordinate | è la fotografia di **agosto**: i valori vengono riscritti, gli obiettivi dichiarati non si ripubblicano. ⚠️ dopo il passo 0 resta soprattutto ciò che il dataset **non** ha: obiettivi, liste UEFA, fuori-progetto | **prima del 15/8** |
| **2** | ✅ **FATTO (Fase 122)** — scheletro giornaliero + meteo + quote | `scripts/raccolta_giornaliera.py` + cron giornaliero. Scrive `raccolta.json` e `fonti.json`; il meteo oltre l'orizzonte di 16 giorni è marcato `fuori_orizzonte`, non «mancante». Coordinate di **90 stadi su 94** in `_anagrafica/stadi.json` | fatto il 28/7 |
| **3** | **Formazioni ufficiali a T−1h** | 🎯 il bersaglio della Fase 93; **timebox 2 ore** per la fonte, poi si ripiega sulle probabili | **prima del 15/8** |
| **3-bis** | 🎯 **Arbitro designato** per ogni partita (§4-bis) | vale **quanto il fattore campo** sui cartellini, la tendenza **persiste** fra stagioni, ed esce solo ~2 giorni prima | **dal 15/8, ogni giornata** |
| **4** | Bollettino quotidiano dei **fatti** (infortuni, squalifiche, diffidati, convocazioni) | 🔴 in gran parte | dal 15/8 |
| **5** | Livello **giudizi** (sentiment, rischio panchina, probabili) | serve il livello 4 come evidenza | settembre |
| **6** | **Incrocio notizia→quota** (§4.6) | serve una massa di giorni | ottobre |
| **7** | Derivati di §4.3 (fasce di 15′, dipendenza dai singoli, PSxG) | 🟢 ricalcolabili **quando vogliamo** | quando c'è tempo |

**Come gira, tecnicamente.** Due canali, e ognuno fa ciò per cui è adatto:

- **GitHub Actions** (già in uso, gratuito, affidabile) per i **fatti da API**:
  meteo, quote, calendario, classifiche. Deterministico, testabile, senza LLM.
- **Routine Claude Code** per i **giudizi** e per le notizie che richiedono
  lettura: gira, cerca, scrive un file datato, committa. Qui l'LLM serve
  davvero — ma ciò che produce è marcato `"tipo": "giudizio"` con l'evidenza.

Sono separati apposta: se un giorno la routine LLM non gira, i fatti si
raccolgono lo stesso. **Il livello 1 non deve dipendere dal livello 2.**

⚠️ **Il paracadute obbligatorio (lezione della Fase 118).** Ogni raccoglitore
automatico deve **fallire rumorosamente** quando la risposta è implausibile.
Un job verde che non raccoglie niente è indistinguibile da uno che funziona, e
in questa cartella il dato mancante **non si recupera**. Ogni giro scrive anche
`fonti.json` con esito e orario di ogni fetch: un giorno con 0 fatti dev'essere
visibile come un'anomalia, non come un file assente.

---

## 6 · Come si controlla che non stiamo raccogliendo spazzatura

Regola del progetto (**R7**): ogni statistica di testa ha il suo intervallo, e
ogni «non c'è effetto» la sua misura di potenza. Applicata qui:

- **copertura dichiarata**: per ogni giorno e ogni campo, quante squadre coperte
  su quante attese. Un campo sotto il 50% è un campo che **non** si può usare in
  un'analisi senza dirlo;
- **i giudizi si scorano**: la «probabile formazione» va confrontata con quella
  **ufficiale** appena esce. Senza questo numero, il livello 5 è intrattenimento;
- **niente conclusioni su una stagione** (§1.7): questa è la stagione 1;
- **niente ROI simulato** con dati raccolti in questo modo (§5).

---

## 7 · Prossimi passi già previsti (non ancora fatti)

1. **Coppe nazionali** (Coppa Italia, FA Cup, Copa del Rey, DFB-Pokal, Coupe de
   France) e **supercoppe**: la squadra è la stessa cartella, cambia la
   competizione della partita. Serve la regola delle **liste per competizione**
   (chi è squalificato dove).
2. **Coppe europee** (Champions, Europa, Conference) + **Mondiale per club**:
   introducono avversari di campionati che non modelliamo → §4 della struttura.
3. **Nazionali** — *da questa stagione si comincia*: convocazioni, minuti,
   risultati, e l'effetto rientro. È anche il ponte verso i tornei per nazionali.
4. **Ranking UEFA (club) e FIFA (nazionali)**: sia come feature sia come
   contesto per gli obiettivi.
5. **Club fuori dalle 5 leghe**: seconde/terze/quarte serie e campionati esteri
   (Turchia, Portogallo, Olanda, Belgio…). Non li modelliamo, ma li
   **incontriamo** nelle coppe: servono almeno anagrafica e ranking.
6. **Mappa nomi squadra** Smarkets ↔ nostri snapshot ↔ fonti nuove: da fare **a
   mano e verificata**, mai con un match approssimato. È un bug già capitato nel
   repo («Hellas Verona» → «Verona»), ed è il modo tipico di rovinare un join.

---

## 8 · Che cosa NON va in questa cartella

- **quote come numeri decimali**: qui si scrivono probabilità, come ovunque nel
  repo (`docs/DATI.md`);
- **stime del nostro modello**: vivono in `data/estimates/` (§5 di `CLAUDE.md`);
- **dati modificati a mano**: mai (**R3**);
- **contenuti scaricati da fonti che ci vietano il crawling** (§3);
- **niente di tutto questo serve a scommettere soldi veri.** Vale qui come in
  tutto il repo.
