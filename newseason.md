# Nuova stagione 2026-27 — piano operativo e brainstorming

> **Cos'è questo file.** Un piano **datato e deperibile**, non documentazione
> permanente. Serve a non perdere la finestra che si apre una volta l'anno:
> l'inizio della stagione. Metà di ciò che c'è qui **non si può recuperare
> dopo il calcio d'inizio**.
>
> Le parti marcate **💭 brainstorming** sono idee da discutere, **non impegni**:
> stanno qui per essere valutate insieme, non perché siano decise.
>
> Scritto il **26 luglio 2026** (dopo la Fase 97). **Aggiornato il 28 luglio
> 2026**: le due leghe nuove sono in produzione (Fase 100), la rete è tornata
> raggiungibile (`docs/MANUALE_SOPRAVVIVENZA.md` §1), l'audit delle Fasi
> 101/101-bis/101-ter ha rettificato alcuni numeri qui citati, e la checklist
> **eseguibile** del test prospettico è stata scritta dove deve stare
> (`experiments/prospettico_2026_27.md` §5). Questo file resta il **piano
> datato**; quella è la **checklist operativa**.

### Quando si archivia: cosa va dove

A stagione avviata (indicativamente **settembre 2026**) questo file si archivia.
Non si butta: si **smonta**, e ogni pezzo ha già la sua destinazione.

| pezzo di questo file | destinazione | perché |
|---|---|---|
| §4 sondaggi + §8 fonti (esiti misurati) | `docs/MANUALE_SOPRAVVIVENZA.md` §1 | è conoscenza operativa dell'ambiente, non un piano |
| §5 A1/A2 (cosa si è congelato, quando, con che comando) | `experiments/prospettico_2026_27.md` + `docs/DIARIO.md` | è il verbale del test prospettico (Fase 78) |
| §5 A3 (criteri pre-registrati) | `docs/DIARIO.md`, nella fase che li usa | vanno citati *nella* fase, o non servono a niente |
| §6 B1/B2 (coda a zero, «quali tre scendono») | `docs/PISTE.md` §4-bis | sono piste di modello, ricorrenti |
| §8.4 + §10 (finestre irripetibili) | `docs/PISTE.md` §4 (raccolta prospettica) | sopravvivono all'anno |
| §9 (chi fa cosa nell'automazione) | `docs/MANUALE_SOPRAVVIVENZA.md` §3 (Actions) | è un fatto operativo, non un piano |
| §11 (checklist datata) | si butta | scade con la stagione, per costruzione |

---

## 1 · Il conto alla rovescia

Date di inizio ricavate dagli eventi outright di Smarkets (`start_date`,
scaricate il 25/07/2026 — **da riverificare a inizio agosto**, i calendari si
spostano: il comando è nel §4).

| lega | via | giorni residui **al 28/07/2026** |
|---|---|--:|
| **La Liga** | **16 agosto** | **19** |
| Premier League | 21 agosto | 24 |
| Ligue 1 | 21 agosto | 24 |
| Serie A | 22 agosto | 25 |
| Bundesliga | 28 agosto | 31 |

**La scadenza vera è il 16 agosto**, non fine mese. La colonna dei giorni è
riferita al 28/07/2026 e **scade ogni giorno**: le date sono il dato, il conto
è un promemoria.

## 2 · Perché c'è una scadenza (cosa non si recupera)

Tre cose esistono solo *prima* del fischio d'inizio e non si ricostruiscono a
posteriori. Ognuna ha la sua scadenza, e non è la stessa:

| # | cosa | scadenza | se si manca |
|---|---|---|---|
| 1 | **Previsioni congelate** del test prospettico (Fase 78) | **15 agosto** (vigilia della Liga), lega per lega alla vigilia della rispettiva giornata 1 | il test non è più prospettico: una previsione prodotta dopo non è una previsione |
| 2 | ✅ **FATTO (Fasi 116/118, 28 luglio)** — **quote di apertura e traiettoria** verso la chiusura | era «acceso ≈10 agosto»: acceso il **28 luglio**, cioè **13 giorni prima**, e non è un anticipo di lusso — il listino dell'esordio è già quotato e la Fase 118 ha misurato che una finestra a 72 h avrebbe lasciato il raccoglitore fermo **fino al 12 agosto** | il buco sarebbe stato identico a quello di `docs/CACCIA_OU_2017_19.md`, e all'indietro non si chiude |
| 3 | **Formazioni ufficiali** | **T−1h di ogni partita**, per sempre | è l'unica informazione che la Fase 93 indica come bersaglio (il deficit è informazione, non calibrazione), e a posteriori diventa cronaca |

Il lavoro di modello, invece, **può aspettare**. Da qui l'ordine del piano.

## 3 · Vincolo tecnico che decide il disegno

**Il container è effimero.** Nessuna raccolta ricorrente può girare da una
sessione interattiva. I canali possibili sono in §9. Vale la lezione della
**Fase 92**: un cron mensile era diventato attivo in silenzio su `main` e
committava ~51 MB senza rigenerare gli snapshot. Qualunque automazione qui
nasce **con i paracadute già scritti**, non aggiunti dopo.

---

## 4 · Passo 0 — sondaggi di fattibilità (mezza giornata)

Tre cose che decidono il disegno e che **non voglio assumere**. Stato al
28/07/2026:

- [x] ✅ **Smarkets ha le quote 1X2 per-partita del 2026-27? SÌ — misurato**
      (Fasi 115/116/118). L'API espone **una giornata per lega**: al 28/07 sono
      **48 partite** delle nostre 5 (9-10 ciascuna, dal 15 al 30 agosto), e i
      libri **ci sono**: 1X2 + O/U 2.5 + GG/NG con libro a **due lati sull'85%**
      delle righe e overround mediano **1.0034**. Risolve in un colpo
      **calendario + quote**, quindi **il Modello 2 esiste**
      (`experiments/prospettico_2026_27.md` §5.1).
      Raccoglitore: `scripts/fetch_smarkets_matches.py`, acceso in automatico da
      `.github/workflows/smarkets-prematch.yml`. Primo file già in archivio.
      ⚠️ Da fare **prima del join**: la mappa nomi squadra Smarkets→nostri, a
      mano e verificata (vale la stessa avvertenza di `docs/DATI.md` §5-bis).
- [ ] **Calendario 2026-27 completo.** Se Smarkets non basta: openfootball su
      `raw.githubusercontent.com` è raggiungibile (`MANUALE` §1). ⚠️ Verificare
      i nomi squadra contro `TEAM_ALIASES` (`src/data/sources.py`): è un bug già
      capitato («Hellas Verona» → «Verona»).
- [ ] **Una fonte di formazioni ufficiali pre-partita.** **Timebox: 2 ore**,
      poi si molla. È l'informazione più preziosa rimasta, ma non c'è evidenza
      che sia raggiungibile e non voglio scoprirlo il 20 agosto. Stato misurato:
      `sofascore.com` **403** e FotMob vieta l'`/api/*` nel `robots.txt` (con la
      trappola del frammento `#matchId`, `MANUALE` §1); resta API-Football con
      chiave (§8.3). *(La scorciatoia storica è chiusa: il surrogato di assenze
      dalle formazioni passate è **bocciato** alla Fase 98 — correla +0.9603 col
      valore rosa e non dice nulla sul bersaglio della Fase 93.)*

> ✅ **Non sono più sondaggi: sono fatti.** La rete è tornata raggiungibile
> (Fase 100) e gli **outright** si scaricano già da due borse — Polymarket
> (`gamma-api.polymarket.com`) e Smarkets (`api.smarkets.com`), entrambe
> verificate. L'archivio è nato: `data/outright_snapshots/`. Quindi il passo 0
> è ridotto ai tre punti qui sopra, che riguardano **le partite**, non le
> stagioni.

---

## 5 · Blocco A — prima del 16 agosto (non negoziabile)

> 📌 **La checklist eseguibile, con i comandi e i file, vive in
> [`experiments/prospettico_2026_27.md`](experiments/prospettico_2026_27.md)
> §5** (scritta alla Fase 101). Qui restano le **date** e il **perché**: se le
> due divergono, per l'esecuzione ha ragione quella, per le scadenze questa.

### A1 · Congelare le previsioni del test prospettico (Fase 78)

Stato al 28/07/2026, verificato sui file:

| pezzo | stato | dove |
|---|---|---|
| impostazione del test | ✅ esiste | `experiments/prospettico_2026_27.md` |
| previsioni **outright** congelate | ✅ **2026-07-25** — ma **3 leghe su 5** (`serie_a`, `premier_league`, `la_liga`) | `experiments/prospettico_2026_27_outright.json` |
| anteprima **DC per-partita** | ⚠️ **illustrativa**: 7 partite Premier *plausibili*, congelata 2026-07-23 | `experiments/prospettico_2026_27_dc.csv` |
| motore **per-lega** su M1 e M2 | ✅ chiuso (Fasi 83-bis e 92-bis) | `predict.py --league <lega>`, `src.config.MARKET_ENGINE` |
| **fixture ufficiali** giornata 1 | ❌ mancanti | — |
| **livello-partita congelato** | ❌ manca | — |
| **script di scoring** | ❌ non esiste | — |

*(Correzione: il congelamento degli outright è della **Fase 95** — «Il primo
confronto con un mercato VERO sull'outright», 25/07 — non della Fase 96, che è
corner e cartellini. Il JSON stesso cita «Fase 78/95».)*

La distinzione che conta:

| | dipende dalle quote? | quando si congela |
|---|---|---|
| **DC standalone** (M1) | no | **adesso**, per le prime N giornate |
| **market-implied** (M2) | sì (quote di un istante) | va catturato automaticamente → A2 |

- [ ] calendario delle prime 3-5 giornate delle 5 leghe (§4)
- [ ] previsioni DC congelate (**tutti i mercati Tier 1**, non solo 1X2: dopo non
      si recuperano). Comando, partita per partita:
      `python scripts/predict.py --league <lega> --date <YYYY-MM-DD> "<casa>" "<ospite>"`.
      ⚠️ `scripts/_run_prospettico_2627.py` ha `FIXTURES` e `AS_OF` **hardcoded**
      (solo Premier, 7 partite): vanno sostituiti coi fixture veri prima di
      rigenerare il CSV.
- [ ] **estendere l'outright alle 5 leghe** (`python scripts/archive_outrights.py`,
      due fonti in un comando). Se Bundesliga e Ligue 1 non sono quotate,
      **dichiararlo nel JSON**: un buco dichiarato è innocuo, uno silenzioso no
      (regola R6).
- [ ] script di scoring, scritto **ora** e non a settembre — via
      `experiment_log.compute_metrics` (fonte unica) e `append_run`
      (`config.source = "prospettico_2627"`).

### A2 · Il raccoglitore automatico

Gira ogni 3-6 ore; a ogni giro fotografa le partite entro le 48 ore successive,
marcando ogni riga con le **ore al kickoff**. Ne esce da sola la traiettoria
apertura → chiusura. Più l'archivio outright una volta al giorno.

**Stato misurato (28/07/2026): il cron NON esiste ancora.**
`data/outright_snapshots/` contiene **2 istantanee** (`2026-07-25.json`,
`2026-07-26.json`) per **930 righe** in `history.csv`: è un archivio nato a
mano, che oggi fotografa un istante e non un movimento. Il comando è pronto e
idempotente — `python scripts/archive_outrights.py` — **manca solo il cron**.

Paracadute **da scrivere insieme al workflow**, non dopo:

- [ ] file partizionati per mese, con tetto di dimensione
- [ ] `data/*_matches.csv` **mai** toccati (gli snapshot congelati sono sacri)
- [ ] il workflow scrive **solo** dentro la sua cartella
- [ ] `workflow_dispatch` prima di `schedule`: si vede girare a mano, poi si
      arma il cron
- [ ] scadenza esplicita del cron o promemoria di revisione (lezione Fase 92)

### A3 · Pre-registrare i criteri, prima di vedere un dato

**Costa un'ora e vale più di tutto il resto del blocco.** Il progetto ha già una
disciplina sul multiple-testing (Fase 17) e una fase in cui il metro sbagliato
ha ribaltato la conclusione (Fase 95-bis). Da fissare **per iscritto adesso**:

- [ ] si testa **solo sulle partite equilibrate** — è lì che il mercato stacca
      (−0.00793 contro −0.00198 sui mismatch, Fase 93)
- [ ] la metrica è la **risoluzione**, non il log-loss: è l'unico termine della
      scomposizione di Murphy che risulti **conclusivo** (+0.00981 [+0.00747,
      +0.01246], Fase 93). ⚠️ **Rettifica dell'audit Fase 101**: la frase «siamo
      *meglio* calibrati del mercato» (0.00083 contro 0.00125) **non regge** —
      IC95 [−0.00135, +0.00049], segno che si inverte a 50 e 100 fasce, ed
      entrambi i valori sono al pavimento di rumore. La conclusione che
      sopravvive è più debole e basta lo stesso: **dalla calibrazione non c'è
      niente da prendere**, il divario è informazione.
- [ ] soglia di successo dichiarata prima: recuperare **≥ 1/3** del divario
- [ ] confronto sempre col mercato **dello stesso istante**, mai con la chiusura
- [ ] quante ipotesi si testano, dichiarate in anticipo
- [ ] **potenza dichiarata**: con **una** giornata non si conclude niente contro
      il mercato (9,8%, Fase 98). La soglia di disegno è ~574 partite — ≥19
      giornate su 3 leghe, **~12 su 5** (`prospettico_2026_27.md` §4-bis)

---

## 6 · Blocco B — dopo il via, nessuna scadenza

- **B1 · La coda a zero** (pista aperta dalla Fase 97). Diamo 0.0% a Man City e
  Liverpool, il mercato 7.6% e 1.1%. Manca l'incertezza sui **parametri**:
  il simulatore campiona i risultati e (con la deriva) l'evoluzione, ma tratta
  le forze del DC come note. `build_cdfs(shift=...)` esiste già — cambia solo
  *da dove* si estrae lo shift. **Costo basso.** Rischio dichiarato: potrebbe
  gonfiare tutto e peggiorare il centro, come è successo al top-4 con la deriva
  → si misura **per-mercato** (§1.8), non si adotta in blocco.
- **B1-bis · Rilanciare la Fase 89 su 5 leghe** (novità Fase 101-ter,
  `docs/PISTE.md` §4-bis): il campione passa da **24 a ~40 stagioni-lega** con
  **un run**, contro le +3 che ogni stagione nuova regala. Le regole di
  spareggio di Bundesliga e Ligue 1 sono già in `season_sim.py`. È il modo più
  economico di stringere gli IC dell'intera famiglia outright — e non ha
  scadenza, ma conviene farlo **prima** di riprezzare il 2027 Champion.
- **B2 · «Quali tre scendono».** Il residuo dopo la deriva: +19.6pp sulle
  neopromosse compensati dal sotto-prezzo del resto della coda, somme
  coincidenti. Non è varianza mancante, è **sicurezza mal riposta**. Più
  difficile di B1.
- **B3 · Il pagamento di A2**, fra 2-3 mesi: quando ci sono abbastanza partite
  equilibrate con la traiettoria delle quote, si testa l'ipotesi della Fase 93.
  **Prima non c'è niente da testare.**
- **B4 · Code sciolte dell'audit.** ⚠️ **In gran parte assorbite dalle Fasi
  101/101-bis/101-ter**: `loader.enrich()` **propaga** ora la lega (e alza
  un errore se lo snapshot non corrisponde, `src/data/loader.py:288-311`), e 10
  dei 13 punti aperti del verbale sono chiusi. I residui minori (script con
  radice o cache incise, snippet di `experiments/README.md` che solleva
  `KeyError`, il ramo silenzioso di `audit_snapshots.py`) sono elencati nel
  cappello di `docs/AUDIT_FASI_80_100.md` §4: mezza giornata a spizzichi,
  nessuna urgenza.

## 7 · Cosa NON farei adesso

~~**Aggiungere le leghe nuove** (Ligue 1 e Bundesliga come leghe *modellate*)~~
→ **FATTO alla Fase 100**, lo stesso giorno: sono in `LEAGUE_CONFIGS` con
snapshot congelati (2.754 + 3.097 partite), δ 0.28/0.19, e le 45 stagioni-lega
ci sono davvero. Resta valido per **Serie B e Championship**: valore reale,
**nessuna scadenza**, e mangerebbe le settimane che servono al Blocco A.
**Dopo settembre.**

---

## 8 · 💭 Brainstorming — posti nuovi da provare

Regola imparata alla Fase 97: **«presumibilmente bloccato» non è un dato.** Due
host marcati per esclusione da mesi rispondevano, e la fonte migliore dopo
Polymarket è emersa dal provare la lista intera. Corollario del 28/07: bastava
**uno User-Agent** da browser per smentire anche il 404 di BetExplorer.

> 📌 **La mappa di rete autorevole è `docs/MANUALE_SOPRAVVIVENZA.md` §1**
> (ri-testata host per host con `curl` il 2026-07-28). Qui sotto resta solo
> ciò che serve a **decidere** in questo piano: non duplicare gli esiti, che
> lì sono aggiornati e qui invecchiano.

### 8.1 · L'idea che valeva più di tutte: ri-sondare **dal runner Actions**

> ⚠️ **RIDIMENSIONATA dalla Fase 100** (verificato il 26/07/2026, audit Fase
> 101, ri-testato il 28/07): la rete **è tornata raggiungibile** da questa
> sessione. Rispondono 200 `football-data.co.uk`, `understat.com`,
> `transfermarkt.com`, Kaggle via `kagglehub`, `footiqo.com`,
> `gamma-api.polymarket.com`, `api.smarkets.com` — e dal 27/07 anche
> `huggingface.co`, `datasets-server.huggingface.co`, `data.jsdelivr.com`.
> Bundesliga e Ligue 1 sono infatti state scaricate direttamente, senza bundle
> a mano. **Il probe `probe.yml` non è più la mossa a più alto valore**: resta
> utile solo per gli host che da qui **non** rispondono davvero (fra questi
> `*.betfair.com` 403, `sofascore.com` 403, `fbref.com` 403,
> `cds-api.bwin.com` 000, `sportsbook-nash.draftkings.com` 403 geo — elenco
> completo e aggiornato in `MANUALE` §1) e per verificare il **vincolo geo
> ADM** su oddsportal/betexplorer, che dipende dall'IP e non dall'ambiente.
> La colonna «qui» della tabella è **storica**, non lo stato di oggi.

| fonte | cosa darebbe | qui (storico, ante-F100) | oggi (`MANUALE` §1) |
|---|---|---|---|
| **Betfair Exchange** | la borsa più liquida del mondo: prezzi migliori di Smarkets su tutto | 403 | **403** — resta da provare da Actions |
| **football-data.co.uk** | è la **nostra fonte primaria** | 403 | **200** ✅ |
| SofaScore | formazioni, statistiche live | 403 | **403** — resta da provare da Actions |
| Understat | xG per Premier/Liga | 403 | **200** ✅ (serve l'header `X-Requested-With`) |
| Transfermarkt | valori rosa | bloccato | **200** ✅ |

### 8.2 · Fonti mai sondate

| fonte | cosa darebbe | costo |
|---|---|---|
| **open-meteo.com** | meteo storico + previsto, **senza chiave, gratis** → apre la pista 13 (meteo), ferma per mancanza di fonte | basso |
| **Kalshi** (`api.elections.kalshi.com`) | **risponde già** (verificato): terza borsa, mercati sportivi USA — da capire se copre il calcio europeo | basso |
| **FotMob / API non ufficiali** | formazioni pre-partita | medio, fragile — `/api/*` **vietato** dal loro `robots.txt`, e l'URL senza `#matchId` rende un'altra partita |
| **StatsBomb open data** (GitHub) | eventi dettagliati, ma poche competizioni | basso |

### 8.3 · Fonti che richiedono una chiave (serve una tua decisione)

| fonte | cosa darebbe | nota |
|---|---|---|
| **The Odds API** | **molti bookmaker insieme**, Pinnacle incluso — il benchmark che la pista 9 chiede | verificato: `api.the-odds-api.com` risponde 200 ma **401 senza chiave**. Free tier 500 richieste/mese: basterebbe per gli outright, non per le partite |
| **API-Football** | formazioni ufficiali, infortuni, calendari | free tier stretto |

> Se vuoi, di queste due la **prima** è quella che cambierebbe di più: darebbe
> il confronto multi-book che oggi non abbiamo, e Pinnacle è il riferimento
> storico per l'efficienza. Serve solo una registrazione gratuita.

### 8.4 · Il mercato che solo questa stagione può aprire

> ⚠️ **Premessa CADUTA alla Fase 100** (allineato dall'audit della Fase 101):
> le quote GG/NG **esistono** per il 2017-20 (1xBet via footiqo, 5.337 partite,
> 5 leghe) e la domanda è già misurata — il mercato **è informativo** (log-loss
> 0.6840 contro 0.6921 di baseline, CI conclusivo), il nostro prezzo lo
> **pareggia** (6 varianti su 6 con CI a cavallo dello zero) e il DC **perde**
> (+0.0104 [+0.0063, +0.0145], col book che lo ingloba: α\*=0 nel 70% dei fit).
> Raccogliere le quote GG/NG di questa stagione resta utile (**book diverso,
> stagioni recenti che nessun archivio copre**), ma non è più «il mercato che
> nessuno ha mai quotato».

~~**GG/NG quotato.** Era il punto §1.8 del `CLAUDE.md`: il GG/NG sarebbe
**l'unico mercato senza quote nei dati** (football-data non le include), quindi
l'unico dove non abbiamo mai potuto dimostrare l'efficienza del mercato —
«l'unico con spazio non ancora chiuso».~~ **Polymarket lo quota** (`BTTS`, negli
eventi "More Markets"): raccoglierlo prospetticamente resta a **costo marginale
zero** — il raccoglitore di A2 lo prende già — e dà il primo campione di quote
GG/NG **recenti** del progetto.

---

## 9 · 💭 Brainstorming — l'automazione: chi fa cosa

Tre canali possibili, con caratteristiche molto diverse. La mia proposta è
**usarne due, con una divisione del lavoro netta**.

| canale | forte in | debole in | verdetto |
|---|---|---|---|
| **GitHub Actions** (cron) | deterministico, rete libera, gratis, **committa nel repo**, alta frequenza | zero giudizio: fa solo ciò che è scritto | ✅ **la raccolta dati** |
| **Routine Claude Code** (sessione schedulata) | ha giudizio: legge i risultati, nota le anomalie, scrive il diario, avvisa | consuma budget, va tenuta a guinzaglio corto | ✅ **il lavoro settimanale che richiede di capire** |
| **Task ChatGPT** | zero attrito per te | **non può eseguire il nostro codice né committare** | ❌ ridondante: la Routine fa già gli avvisi |

**Divisione proposta:**

- **Actions, ogni 3-6 ore** → quote per-partita entro 48h dal via + archivio
  outright giornaliero (`scripts/archive_outrights.py`). Solo raccolta, nessuna
  analisi.
- **Routine Claude Code, una volta a settimana** (es. martedì, a giornata
  conclusa) → *«controlla che l'archivio sia cresciuto, scora la giornata
  appena finita contro le previsioni congelate, aggiorna il registro, e dimmi
  solo se qualcosa non torna»*. È il tipo di compito dove una checklist
  automatica fallisce e serve capire cosa si sta guardando.
- **Una Routine una tantum il 14 agosto** → promemoria di congelare tutto prima
  della Liga.

**Le cautele, che sono la parte seria della proposta.** Una routine che gira da
sola su `main` può fare danni silenziosi — è già successo (Fase 92). Quindi:
prompt stretto e verificabile, mai toccare gli snapshot congelati, e in caso di
dubbio **si ferma e avvisa** invece di decidere.

> **Da decidere insieme**: settimanale o dopo ogni giornata? La routine può
> committare da sola o deve solo segnalare? Su questo non ho una preferenza
> forte — dipende da quanto vuoi restare nel giro.

---

## 10 · 💭 Brainstorming — cose che *solo* la stagione in corso permette

Elenco delle finestre che si chiudono, in ordine di quanto sono irripetibili:

1. **Traiettoria apertura → chiusura** delle quote (mai avuta a nessuna scala).
2. **Formazioni ufficiali** pre-partita (pista 10) — esistono un'ora, poi no.
   La Fase 98 ha **escluso la scorciatoia** (surrogato storico bocciato): o si
   raccoglie a T−1h, o non esiste.
3. **Quote GG/NG** (§8.4) — book diverso e stagioni recenti che nessun archivio
   copre (la premessa «unico mercato senza quote» è caduta alla Fase 100).
4. **Dati in-play** minuto per minuto (pista 18) — fondazione dei mercati live,
   Tier 3. *(Nota: il mattone offline c'è già — il modello a due stadi del
   secondo tempo, pista 6-bis, si prova **senza rete** e conviene farlo prima.)*
5. **Ri-prezzatura degli outright** a inizio stagione (`docs/PISTE.md` §4-bis,
   promemoria ricorrente) — **e l'appunto esplicito**: rifare il lavoro sul
   «2027 Champion» ora che il simulatore ha la deriva, confrontando la
   previsione nuova con quella della Fase 89 e coi prezzi di allora. È
   l'occasione migliore che il progetto avrà per **misurare quanto è valsa una
   correzione**, e va colta prima che la stagione finisca. Da fare **dopo**
   B1-bis (5 leghe), altrimenti si riprezza col campione vecchio.
6. **Shock di gennaio** (pista 11, mercato dei trasferimenti) — va raccolto a
   gennaio, non dopo.

---

## 11 · Checklist datata

Riferita al **28/07/2026**. Le prime due righe sono **in ritardo di zero
giorni**: erano «fine luglio». **Tre righe sono già chiuse** (Fasi 116/118): il
raccoglitore pre-partita era previsto per il 5-10 agosto ed è in funzione dal
28 luglio.

| entro | cosa | comando / file | blocco |
|---|---|---|:--:|
| **subito** | **pre-registrare i criteri** (prima di guardare qualunque dato) | scrivili in `experiments/prospettico_2026_27.md` §5.1 | A3 |
| ~~subito~~ ✅ **28 lug** | sondaggi: libri Smarkets per-partita ✅ (48 partite, libri liquidi) — restano calendario completo e formazioni | `scripts/fetch_smarkets_matches.py` | 0 |
| **~2 agosto** | `probe.yml` dal runner Actions — **solo** per Betfair/SofaScore e il vincolo geo | — | 8.1 |
| ~~~5 agosto~~ ✅ **28 lug** | raccoglitore Actions scritto e **visto girare a mano** (`workflow_dispatch`, run `30383527812`) — ed è servito: girava **verde raccogliendo zero** (Fase 118) | `scripts/fetch_smarkets_matches.py` | A2 |
| ~~~10 agosto~~ ✅ **28 lug** | cron armato (denso ogni 6 h + lungo raggio 1×/giorno). **Resta da osservare**: due giri completi *automatici*, cioè non lanciati a mano | `.github/workflows/smarkets-prematch.yml` | A2 |
| **~12 agosto** | previsioni DC congelate (tutti i Tier 1, 5 leghe) + script di scoring pronto | `scripts/predict.py --league …` | A1 |
| **14 agosto** | istantanea outright pre-stagione + ri-prezzatura campione | `scripts/archive_outrights.py`, `scripts/_run_fase89_season_champion.py` | 10.5 |
| **15 agosto** | ultimo controllo: tutto gira? commit datato delle previsioni congelate | — | A1 |
| **16 agosto** | **La Liga parte.** Da qui si raccoglie e basta | — | — |
| settembre+ | B1 (coda a zero), B1-bis (Fase 89 su 5 leghe), poi B2, B4 | — | B |
| ottobre+ | B3: il test della Fase 93 sui dati raccolti | — | B |

---

## 12 · ⚠️ Questo non è tutto ciò che resta da fare

Perché il file non venga letto come «finito questo, il progetto è finito».
Stato al 28 luglio 2026 — **senza duplicare i conteggi**, che invecchiano: le
fonti sono `docs/PISTE.md` §0-bis (indice di stato delle piste) e
`docs/PANCHINA.md` (matrice della rosa).

- **`docs/PISTE.md`**: la maggior parte delle piste numerate è **mai provata**.
  L'indice di stato §0-bis dice quali sono aperte, quali parziali e quali
  chiuse, con il rimando alla voce estesa. Il quadro d'insieme, con le priorità,
  sta in [`lavoro_aperto.md`](lavoro_aperto.md).
- **`docs/PANCHINA.md`**: molte caselle `⬜` = modelli testati **solo sulla
  Serie A** e mai sul fronte per-lega o generale (principio §1.9). Il numero
  esatto si legge dalla matrice, non da qui: non sono assoluzioni, sono lavoro
  potenziale.
- **Fase 78** è l'unica fase formalmente **APERTA** — ed è proprio questa.
- **Mercati non ancora coperti**: HT/FT congiunto, le combinazioni e il live. Il
  **Tier 2** (handicap asiatico) è coperto e validato contro quota esterna
  (Fase 88: **pareggio in Brier** col mercato sharp, 0.2044 vs 0.2044) e il
  **Tier 3** di base — Halftime, Second Half, risultato esatto — dalle Fasi
  96/98, con il residuo vivo del **secondo tempo mal calibrato** (game-state).

Quello che invece **è chiuso** e non va riproposto senza informazione nuova:
tutti i dati **interni** (gol/xG/npxG/PPDA/deep/valore-rosa/assenze/riposo/
forma/stakes), il GBM bespoke per-mercato (bocciato 4 volte), il Poisson
bivariato, le copule di Frank, gli ensemble di emivite, la draw-inflation, il
ρ dinamico, la zero-inflazione, Rue-Salvesen, GAS/state-space.
**Il tetto è informativo, non architetturale** — ed è esattamente il motivo per
cui la raccolta prospettica di questa stagione conta più di qualunque modello
nuovo.
