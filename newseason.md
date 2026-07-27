# Nuova stagione 2026-27 — piano operativo e brainstorming

> **Cos'è questo file.** Un piano **datato e deperibile**, non documentazione
> permanente. Serve a non perdere la finestra che si apre una volta l'anno:
> l'inizio della stagione. Metà di ciò che c'è qui **non si può recuperare
> dopo il calcio d'inizio**.
>
> Le parti marcate **💭 brainstorming** sono idee da discutere, **non impegni**:
> stanno qui per essere valutate insieme, non perché siano decise.
>
> Scritto il **26 luglio 2026** (dopo la Fase 97). Quando la stagione sarà
> avviata e le voci saranno risolte, questo file va **archiviato o cancellato**:
> ciò che sopravvive va spostato in `docs/PISTE.md` (piste), `docs/DIARIO.md`
> (risultati) o `docs/MANUALE_SOPRAVVIVENZA.md` (fatti operativi).

---

## 1 · Il conto alla rovescia

Date di inizio ricavate dagli eventi outright di Smarkets (`start_date`,
scaricate il 25/07/2026 — **da riverificare a inizio agosto**, i calendari si
spostano):

| lega | via | giorni da oggi |
|---|---|--:|
| **La Liga** | **16 agosto** | **21** |
| Premier League | 21 agosto | 26 |
| Ligue 1 | 21 agosto | 26 |
| Serie A | 22 agosto | 27 |
| Bundesliga | 28 agosto | 33 |

**La scadenza vera è il 16 agosto**, non fine mese.

## 2 · Perché c'è una scadenza (cosa non si recupera)

Tre cose esistono solo *prima* del fischio d'inizio e non si ricostruiscono a
posteriori:

1. **Le previsioni congelate** del test prospettico (Fase 78). Una previsione
   prodotta dopo non è una previsione — è il difetto che rende non testabile
   all'indietro tutto il resto del progetto.
2. **Le quote di apertura e la loro traiettoria** verso la chiusura. Il progetto
   ha un intero documento su un buco di questo tipo
   (`docs/CACCIA_OU_2017_19.md`): questa è l'occasione di non aprirne un altro.
3. **Le formazioni ufficiali**, che esistono ~1 ora prima e poi diventano
   cronaca. È l'unica informazione mai avuta che la Fase 93 indica come
   bersaglio (il gap è **104% informazione**, non calibrazione).

Il lavoro di modello, invece, **può aspettare**. Da qui l'ordine del piano.

## 3 · Vincolo tecnico che decide il disegno

**Il container è effimero.** Nessuna raccolta ricorrente può girare da una
sessione interattiva. I canali possibili sono in §8. Vale la lezione della
**Fase 92**: un cron mensile era diventato attivo in silenzio su `main` e
committava ~51 MB senza rigenerare gli snapshot. Qualunque automazione qui
nasce **con i paracadute già scritti**, non aggiunti dopo.

---

## 4 · Passo 0 — sondaggi di fattibilità (mezza giornata)

Tre cose che decidono il disegno e che **non voglio assumere**:

- [ ] **Smarkets ha le quote 1X2 per-partita del 2026-27?** Gli eventi ci sono
      (`Inter Milan vs Monza`, 22/08) ma i libri non li ho guardati. Se sono
      liquidi risolvono in un colpo **calendario + quote** per il test
      prospettico.
- [ ] **Calendario 2026-27 completo.** Se Smarkets non basta: openfootball su
      `raw.githubusercontent.com` è raggiungibile (§8).
- [ ] **Una fonte di formazioni ufficiali pre-partita.** **Timebox: 2 ore**,
      poi si molla. È l'informazione più preziosa rimasta, ma non c'è evidenza
      che sia raggiungibile e non voglio scoprirlo il 20 agosto.

---

## 5 · Blocco A — prima del 16 agosto (non negoziabile)

### A1 · Congelare le previsioni del test prospettico (Fase 78)

Stato: `experiments/prospettico_2026_27.md`, `_dc.csv` e `_outright.json`
esistono — **l'outright è già congelato** (Fase 96 dell'altra sessione).
**Manca il livello-partita.**

La distinzione che conta:

| | dipende dalle quote? | quando si congela |
|---|---|---|
| **DC standalone** | no | **adesso**, per le prime N giornate |
| **market-implied** | sì (quote di un istante) | va catturato automaticamente → A2 |

- [ ] calendario delle prime 3-5 giornate delle 5 leghe
- [ ] previsioni DC congelate (tutti i mercati Tier 1, non solo 1X2)
- [ ] script di scoring, scritto **ora** e non a settembre

### A2 · Il raccoglitore automatico

Gira ogni 3-6 ore; a ogni giro fotografa le partite entro le 48 ore successive,
marcando ogni riga con le **ore al kickoff**. Ne esce da sola la traiettoria
apertura → chiusura. Più l'archivio outright una volta al giorno
(`scripts/archive_outrights.py`, già pronto).

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
- [ ] la metrica è la **risoluzione**, non il log-loss (la calibrazione non ha
      niente da dare: la nostra mis-calibrazione è 0.00083, *meglio* del
      mercato)
- [ ] soglia di successo dichiarata prima: recuperare **≥ 1/3** del divario
- [ ] confronto sempre col mercato **dello stesso istante**, mai con la chiusura
- [ ] quante ipotesi si testano, dichiarate in anticipo

---

## 6 · Blocco B — dopo il via, nessuna scadenza

- **B1 · La coda a zero** (pista aperta dalla Fase 97). Diamo 0.0% a Man City e
  Liverpool, il mercato 7.6% e 1.1%. Manca l'incertezza sui **parametri**:
  il simulatore campiona i risultati e (con la deriva) l'evoluzione, ma tratta
  le forze del DC come note. `build_cdfs(shift=...)` esiste già — cambia solo
  *da dove* si estrae lo shift. **Costo basso.** Rischio dichiarato: potrebbe
  gonfiare tutto e peggiorare il centro, come è successo al top-4 con la deriva
  → si misura **per-mercato** (§1.8), non si adotta in blocco.
- **B2 · «Quali tre scendono».** Il residuo dopo la deriva: +19.6pp sulle
  neopromosse compensati dal sotto-prezzo del resto della coda, somme
  coincidenti. Non è varianza mancante, è **sicurezza mal riposta**. Più
  difficile di B1.
- **B3 · Il pagamento di A2**, fra 2-3 mesi: quando ci sono abbastanza partite
  equilibrate con la traiettoria delle quote, si testa l'ipotesi della Fase 93.
  **Prima non c'è niente da testare.**
- **B4 · Code sciolte dell'audit** (mezza giornata a spizzichi): mercati
  duplicati nella lista Tier 1, `loader.enrich()` che non propaga la lega,
  8 fasi fondative senza riga nel registro del README.

## 7 · Cosa NON farei adesso

~~**Aggiungere le leghe nuove** (Ligue 1 e Bundesliga come leghe *modellate*)~~
→ **FATTO alla Fase 100**, lo stesso giorno: sono in `LEAGUE_CONFIGS` con
snapshot congelati (2.754 + 3.097 partite), δ 0.28/0.19, e le 45 stagioni-lega
ci sono davvero. Resta valido per **Serie B e Championship**: valore reale,
**nessuna scadenza**, e mangerebbe le tre settimane che servono al Blocco A.
**Dopo settembre.**

---

## 8 · 💭 Brainstorming — posti nuovi da provare

Regola imparata alla Fase 97: **«presumibilmente bloccato» non è un dato.** Due
host marcati per esclusione da mesi rispondevano, e la fonte migliore dopo
Polymarket è emersa dal provare la lista intera.

### 8.1 · L'idea che vale più di tutte: ri-sondare **dal runner Actions**

Il proxy di questa sessione e il runner GitHub Actions hanno **IP e regole
diverse**. Diverse fonti bloccate qui potrebbero essere libere lì, e non è mai
stato verificato in modo sistematico. Un workflow `probe.yml` che prova 20 host
e committa una tabella di esiti costa **un'ora** e potrebbe sbloccare mezza
lista qui sotto.

Candidati per cui cambierebbe qualcosa davvero:

| fonte | cosa darebbe | qui | da Actions |
|---|---|---|---|
> ⚠️ **SUPERATA dalla Fase 100** (verificato il 26/07/2026, audit Fase 101):
> la rete **è tornata raggiungibile**. Rispondono 200 `football-data.co.uk`,
> `understat.com`, `transfermarkt.com` e Kaggle via `kagglehub` — infatti
> Bundesliga e Ligue 1 sono state scaricate direttamente, senza bundle a
> mano. Restano davvero da provare solo **Betfair** e **SofaScore**; per
> `oddsportal.com` il vincolo non è tecnico ma il `robots.txt` (pagine
> storiche vietate) e BetExplorer ha ritirato le quote vecchie.
> Stato aggiornato in `docs/MANUALE_SOPRAVVIVENZA.md` §1.

| **Betfair Exchange** | la borsa più liquida del mondo: prezzi migliori di Smarkets su tutto | 403 | **da provare** |
| **football-data.co.uk** | è la **nostra fonte primaria**: oggi viviamo di bundle caricati a mano | 403 | **da provare** |
| SofaScore | formazioni, statistiche live | 403 | da provare |
| Understat | xG per Premier/Liga (pista 14: port completo del DC) | 403 | da provare |
| Transfermarkt | valori rosa (oggi recupero manuale una tantum) | bloccato | da provare |

### 8.2 · Fonti mai sondate

| fonte | cosa darebbe | costo |
|---|---|---|
| **open-meteo.com** | meteo storico + previsto, **senza chiave, gratis** → apre la pista 13 (meteo) che è ferma per mancanza di fonte | basso |
| **Kalshi** (`api.elections.kalshi.com`) | **risponde già** (verificato): terza borsa, mercati sportivi USA — da capire se copre il calcio europeo | basso |
| **FotMob / API non ufficiali** | formazioni pre-partita | medio, fragile |
| **StatsBomb open data** (GitHub) | eventi dettagliati, ma poche competizioni | basso |

### 8.3 · Fonti che richiedono una chiave (serve una tua decisione)

| fonte | cosa darebbe | nota |
|---|---|---|
| **The Odds API** | **molti bookmaker insieme**, Pinnacle incluso — il benchmark che la pista 9 chiede | free tier 500 richieste/mese: basterebbe per gli outright, non per le partite |
| **API-Football** | formazioni ufficiali, infortuni, calendari | free tier stretto |

> Se vuoi, di queste due la **prima** è quella che cambierebbe di più: darebbe
> il confronto multi-book che oggi non abbiamo, e Pinnacle è il riferimento
> storico per l'efficienza. Serve solo una registrazione gratuita.

### 8.4 · Il mercato che solo questa stagione può aprire

> ⚠️ **Premessa CADUTA alla Fase 100** (allineato dall'audit della Fase 101):
> le quote GG/NG **esistono** per il 2017-20 (1xBet via footiqo, 5.337 partite,
> 5 leghe) e la domanda è già misurata — il mercato è informativo, il nostro
> prezzo lo pareggia, il DC perde. Raccogliere le quote GG/NG di questa stagione
> resta utile (**book diverso, stagioni recenti che nessun archivio copre**), ma
> non è più «il mercato che nessuno ha mai quotato».

**GG/NG quotato.** Era il punto §1.8 del `CLAUDE.md`: il GG/NG sarebbe **l'unico
mercato senza quote nei dati** (football-data non le include), quindi l'unico
dove non abbiamo mai potuto dimostrare l'efficienza del mercato — «l'unico con
spazio non ancora chiuso». **Polymarket lo quota** (`BTTS`, negli eventi
"More Markets"). Raccogliendolo prospettivamente da subito, fra una stagione
avremo il primo campione di quote GG/NG della storia del progetto e la pista 16
si chiude in un senso o nell'altro. **Costo marginale zero**: il raccoglitore
di A2 lo prende già.

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
  outright giornaliero. Solo raccolta, nessuna analisi.
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
3. **Quote GG/NG** (§8.4) — l'unico mercato ancora aperto.
4. **Dati in-play** minuto per minuto (pista 18) — fondazione dei mercati live,
   Tier 3.
5. **Ri-prezzatura degli outright** a inizio stagione (`docs/PISTE.md` §4-bis,
   promemoria ricorrente) — **e l'appunto esplicito**: rifare il lavoro sul
   «2027 Champion» ora che il simulatore ha la deriva, confrontando la
   previsione nuova con quella della Fase 89 e coi prezzi di allora. È
   l'occasione migliore che il progetto avrà per **misurare quanto è valsa una
   correzione**, e va colta prima che la stagione finisca.
6. **Shock di gennaio** (pista 11, mercato dei trasferimenti) — va raccolto a
   gennaio, non dopo.

---

## 11 · Checklist datata

| entro | cosa | blocco |
|---|---|:--:|
| **fine luglio** | sondaggi di fattibilità + `probe.yml` dal runner Actions | 0, 8.1 |
| **fine luglio** | **pre-registrare i criteri** (prima di guardare qualunque dato) | A3 |
| **~5 agosto** | raccoglitore Actions scritto, **visto girare a mano** | A2 |
| **~10 agosto** | cron armato, due giri completi osservati | A2 |
| **~12 agosto** | previsioni DC congelate + script di scoring pronto | A1 |
| **14 agosto** | istantanea outright pre-stagione + ri-prezzatura campione | 10.5 |
| **15 agosto** | ultimo controllo: tutto gira? | — |
| **16 agosto** | **La Liga parte.** Da qui si raccoglie e basta | — |
| settembre+ | B1 (coda a zero), poi B2, B4 | B |
| ottobre+ | B3: il test della Fase 93 sui dati raccolti | B |

---

## 12 · ⚠️ Questo non è tutto ciò che resta da fare

Perché il file non venga letto come «finito questo, il progetto è finito».
Stato al 26 luglio 2026:

- **`docs/PISTE.md`**: 19 piste numerate, **la maggior parte mai provate** —
  4 senza dati nuovi, 5 nei grezzi già scaricati e mai estratti (handicap
  asiatico, primo tempo, quota massima, Pinnacle puro), 6 con fonte esterna,
  4 di raccolta prospettica.
- **`docs/PANCHINA.md`**: **24 caselle ⬜** = modelli testati solo sulla Serie A
  e **mai** sul fronte per-lega o generale (principio §1.9). Non sono
  assoluzioni: sono lavoro potenziale.
- **Fase 78** è l'unica fase formalmente **APERTA** — ed è proprio questa.
- **Mercati non ancora coperti**: Tier 2 (handicap asiatico), Tier 3 (HT/FT e
  tempi).

Quello che invece **è chiuso** e non va riproposto senza informazione nuova:
tutti i dati **interni** (gol/xG/npxG/PPDA/deep/valore-rosa/assenze/riposo/
forma/stakes), il GBM bespoke per-mercato (bocciato 4 volte), il Poisson
bivariato, le copule di Frank, gli ensemble di emivite, la draw-inflation, il
ρ dinamico, la zero-inflazione, Rue-Salvesen, GAS/state-space.
**Il tetto è informativo, non architetturale** — ed è esattamente il motivo per
cui la raccolta prospettica di questa stagione conta più di qualunque modello
nuovo.
