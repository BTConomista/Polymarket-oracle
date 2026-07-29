# Lavoro aperto — indice unico per la prossima sessione

> **Cos'è questo file.** Un **indice**, non una quarta fonte di verità. Le fonti
> canoniche restano `docs/PISTE.md` (piste), `docs/PANCHINA.md` (rosa dei
> modelli), `docs/DIARIO.md` (narrazione) e il registro del `README.md`. Qui
> c'è (a) il **quadro d'insieme** di cosa è aperto, con i rimandi, e (b) le
> cose che **non vivono ancora da nessuna parte**: i punti operativi e il
> brainstorming.
>
> **Regola d'uso**: quando una voce si chiude, si aggiorna la **fonte
> canonica** e poi questa riga. Se questo file e PISTE/PANCHINA divergono,
> **hanno ragione loro**.
>
> **Regola aggiunta il 28/07/2026**: questo file **non duplica più i
> conteggi** (piste aperte, caselle `⬜`). Un indice che incide numeri che
> vivono altrove diventa stantio nel giro di una sessione — ed era già
> successo due volte. Dove serviva un numero, ora c'è un **rimando** e, dove
> utile, il **comando per ri-contarlo**.
>
> Scritto il **26 luglio 2026** dopo la Fase 97; aggiornato dopo le Fasi 98-99,
> dopo l'ingresso di Bundesliga e Ligue 1 (Fase 100) e **il 28 luglio 2026**
> con gli esiti dell'audit (Fasi 101 / 101-bis / 101-ter). Il piano *datato*
> per l'inizio stagione sta in [`newseason.md`](newseason.md): quello ha una
> scadenza (**16 agosto**), questo no.

---

> 🗓️ **Stato dell'audit al 28/07/2026.** Dei 13 punti aperti di
> `docs/AUDIT_FASI_80_100.md` §4 ne restano **3**, e **nessuno tocca il
> modello**:
> 1. **punto 6** — le **18 celle `⬜` della PANCHINA che l'audit integrato ha
>    già misurato** (più quattro leve misurate senza riga, la sezione «I
>    titolari» ferma a 3 leghe, e «CI<0» usato con due significati opposti);
> 2. **punto 13** — i documenti storici da rinfrescare (`PLAYBOOK_NUOVA_LEGA`,
>    `STUDIO_PREMIER_LIGA`, `MANUALE_SOPRAVVIVENZA`, `GLOSSARIO`, le sezioni
>    «Struttura»/«Archivio dati» del README): **in lavorazione nella sessione
>    del 28/07**, che ha allineato in parallelo tutti i documenti del repo;
> 3. il **riporto della Fase 100 dentro `STUDIO_PREMIER_LIGA.md`** (le due
>    leghe nuove non sono ancora entrate in quel quaderno).
>
> Restano inoltre le **code dei punti 1 e 2**, chiusi nel README ma non
> ovunque: il numero-bandiera aggiornato (**+0.0167 / log-loss 0.9799** contro
> il **+0.0165 / 0.9797 PRE-fix Fase 92**; ROI **−15.8%** su **866**
> scommesse) e la rettifica della **COM-Poisson** (`dp(θ) ≡ COM-Poisson(ν=θ)`
> mean-matched: **non** è una conferma indipendente; su griglia fine l'argmin è
> **θ=1.18**, Δ −0.00027 IC95 [−0.00083, +0.00027], nel rumore) vanno propagati
> anche a `CLAUDE.md`, `PANCHINA`, `PISTE` e `GLOSSARIO`. Anche questo è
> lavoro **documentale**, non di modello.
>
> I minori non corretti (script con radice o cache incise, lo snippet di
> `experiments/README.md` che solleva `KeyError`, il ramo silenzioso di
> `audit_snapshots.py`) sono elencati nel **cappello** di
> `docs/AUDIT_FASI_80_100.md` §4: mezza giornata a spizzichi.

## 0 · Il quadro in tre righe

Il tetto del progetto è **informativo, non architetturale**: tutti i dati
*interni* sono esplorati e una decina di architetture alternative sono state
provate e bocciate. Quindi il lavoro aperto si divide in tre famiglie:

1. **cose mai provate che non costano dati nuovi** (le più economiche, §2-§3);
2. **cose che richiedono informazione nuova** — l'unica leva non esaurita, e
   dopo la Fase 93 sappiamo *dove* punta: **partite equilibrate, seconda metà
   di stagione** (§4);
3. **mercati mai coperti** (le combinazioni del Tier 3 e il live, §5).

---

## 1 · Fase 78 — l'unica fase formalmente APERTA

Il **test prospettico 2026-27**: previsioni congelate *prima* del calcio
d'inizio, scorate dopo. È il gold standard del progetto — l'unico disegno in cui
il look-ahead è impossibile per costruzione, non per disciplina.

| pezzo | stato |
|---|---|
| `experiments/prospettico_2026_27.md` | esiste (impostazione **+ checklist eseguibile**, §5) |
| `experiments/prospettico_2026_27_dc.csv` | esiste, ma **illustrativo**: 7 partite Premier *plausibili*, congelate il 2026-07-23 |
| `experiments/prospettico_2026_27_outright.json` | **congelato il 2026-07-25** (Fase 95), ma su **3 leghe su 5** (`serie_a`, `premier_league`, `la_liga`) |
| **fixture ufficiali** giornata 1 | ❌ **mancano** |
| **livello-partita congelato** | ❌ **manca** |
| **script di scoring** | ❌ **manca** |

⏰ **Ha una scadenza vera: 16 agosto** (via della Liga). Le **date** e il
*perché* stanno in [`newseason.md`](newseason.md); i **comandi**, i file e i
timebox in `experiments/prospettico_2026_27.md` §5. Vincolo di disegno da non
dimenticare: con **una** giornata la potenza contro il mercato è 9,8% (Fase 98)
— la soglia è ~574 partite, cioè ~12 giornate su 5 leghe.

---

## 2 · Le piste — lo stato canonico è `docs/PISTE.md` §0-bis

`docs/PISTE.md` ha dalla Fase 101-ter un **indice di stato** (§0-bis) che dice,
pista per pista, se è aperta, parziale o chiusa, e rimanda alla voce estesa.
**Non si duplica qui**: quello è il conteggio buono, questo è l'ordine di
priorità.

Cosa conta *adesso*, in ordine di rapporto valore/costo (i dettagli e i numeri
sono nella voce di PISTE indicata):

| priorità | pista | perché adesso |
|---|---|---|
| ⭐ 1 | **6-bis · modello a DUE STADI del secondo tempo** (game-state) | è **il residuo vivo** del progetto: localizzato, non-artefatto, sui dati che già abbiamo, e primo mattone dell'in-play |
| 2 | **6-ter · HT/FT congiunto e combinazioni** | costo quasi nullo una volta che il Tier 3 di base è coperto (F98) |
| 3 | **9 · Pinnacle puro** come benchmark singolo-book | nei grezzi **già scaricati**, mai estratta: è *il* riferimento di efficienza |
| 4 | **8 · quota massima (best-price)** → ROI realistico | idem, e cambia il metro di tutti i ROI del progetto (oggi usano la media) |
| 5 | **1 · scontri diretti (H2H)**, puntati su **totali/GG** | zero occorrenze in tutto il progetto: un vuoto sorprendente, e non costa dati |
| 6 | **15 · altre linee O/U (multi-linea)** | una fonte candidata **è già in repo** (1xBet/footiqo 2017-20) |
| 7 | **12 · seconda serie → prior neopromosse individualizzato** | bersaglio puntuale: sbagliamo di **+19.6pp** proprio sulle neopromosse (F97) |
| 8 | **13 · meteo** | ferma solo per mancanza di fonte, e **open-meteo è gratis e senza chiave** (§6.2) |
| 9 | **10 · formazioni ufficiali a T−1h** | *la più preziosa* (§4) ma **solo prospettica**: il surrogato storico è BOCCIATO (F98, correla +0.9603 col valore rosa) |
| 10 | **11 · `transfers.csv` (shock di gennaio)**, **17 · paper-trading draw-bias**, **18 · in-play** | hanno una finestra temporale propria: gennaio, o la stagione in corso |

Chiuse di recente, per non riproporle: **19** (O/U 2017-19 di chiusura: dato
**trovato e NON inserito** — un solo book), **16** (GG/NG: premessa caduta,
resta solo la raccolta prospettica), **7-bis** (correzione di livello dei
conteggi: chiusa NEGATIVA alla F99), **4-quater** (θ_team), **4-ter** (coda a
due parametri). Motivi ed esiti nelle voci di PISTE: **il motivo è la parte
che serve**, perché è ciò che impedisce di rifarle.

---

## 3 · `docs/PANCHINA.md` — le caselle `⬜` (mai testato lì)

Il principio §1.9 impone due fronti per ogni modello: **per-lega** e
**generale**. La matrice della PANCHINA ha molte celle `⬜`, e la legenda del
file lo dice esplicitamente: *«è lavoro potenziale, non un'assoluzione»*.

> **Il numero corrente si legge dalla PANCHINA, non da qui.** Storia del
> conteggio, che spiega perché è cresciuto senza che si perdesse lavoro: era
> **24** finché le leghe erano 3; è salito quando la matrice è passata da 4 a 6
> colonne con l'ingresso di Bundesliga e Ligue 1 (Fase 100) — ogni modello ha
> due colonne-lega in più da riempire; ed è sceso di 4 alla Fase 101, quando la
> riga COM-Poisson ha smesso di essere un modello a sé (`dp(θ) ≡
> COM-Poisson(ν=θ)`: non c'è nulla da testare su quelle colonne).
>
> Come si ri-conta (le celle della matrice, escluse le legende):
> ```bash
> python - <<'EOF'
> n = sum(l.count('⬜') for l in open('docs/PANCHINA.md') if l.strip().startswith('|'))
> print(n)
> EOF
> ```
> Il file ne contiene qualcuna in più, perché alcune stanno nelle **legende** e
> non sono celle della matrice: il filtro `startswith('|')` da solo non basta a
> distinguerle, controllare a vista se il numero deve essere citato altrove.

**La forma del buco**: quasi tutti i modelli in **panchina** o **bocciati** sono
stati provati **solo sulla Serie A**. Nessuno sa cosa facciano altrove.

| famiglia | modelli con Premier/Liga/Bundesliga/Ligue 1/generale mai testati |
|---|---|
| 🪑 **in panchina in Serie A** (potrebbero essere titolari altrove) | nudge GG/NG di fine stagione (F48), ensemble emivite 180+730 (F12a), ricalibrazione per-classe del modello (F10), diagonale inflazionata (F12b), temperature scaling post-hoc (F6) |
| ❌ **bocciati in Serie A** (una bocciatura su una lega non è universale) | Poisson bivariato λ3, copula di Frank, GAS/state-space, binomiale negativa · zero-inflazione · Rue-Salvesen, ρ dinamico, power-devig, covariata stakes, vantaggio-casa per-squadra, covariate nel canale-pareggio, ricalibrazione O/U, ensemble standalone, blend modello+mercato, profilo stagionale dinamico, tiri in porta grezzi, covariate squad_value/absence/npxG/forma/luck/ppda/deep |

⚠️ **Attenzione al costo-opportunità.** Riaprire un modello bocciato su un'altra
lega è economico ma raramente paga: le Fasi 79-80 hanno già mostrato che diverse
leve della Serie A **non si replicano** (φ35 sul path DC, `rest_full`,
`midweek_europe`, il draw-bias), e la Fase 100 lo ha confermato sulle due leghe
nuove (router θ negativo su 0/25 mercati). La priorità onesta è **bassa** —
salvo dove c'è una ragione strutturale, non solo una casella vuota.

**Eccezione a priorità alta**: le **18 celle che l'audit integrato ha già
misurato** (punto 6 del verbale). Lì il lavoro è fatto e manca solo la
trascrizione: è documentazione, non ricerca.

---

## 4 · Il bersaglio misurato (dove conviene davvero cercare)

Non è un'opinione, è la Fase 93 — **con le rettifiche dell'audit della Fase 101,
che ne indeboliscono due affermazioni su quattro senza cambiare la direzione**:

- il deficit è **informazione, non calibrazione** → **nessuna ricalibrazione
  può chiudere il gap**. ⚠️ Le quote «**−4% calibrazione / +104%
  informazione**» sono normalizzate sulla parte che la scomposizione
  **attribuisce**: **0.0094 sui 0.0215** del deficit, cioè il **44%** — il
  restante **56% resta non attribuito**;
- l'unico termine **conclusivo** è la **risoluzione**: 0.05270 contro 0.06251,
  **+0.00981 [+0.00747, +0.01246]**;
- ⚠️ **DECLASSATA**: «siamo perfino meglio calibrati del mercato» (0.00083
  contro 0.00125) **non regge** — IC95 **[−0.00135, +0.00049]**, segno che si
  inverte a 50 e 100 fasce, ed entrambi i valori sono al pavimento di rumore
  (p95 = 0.00083 sotto calibrazione perfetta). Ciò che resta vero, e basta per
  decidere: **dalla calibrazione non c'è niente da prendere**;
- **sui mismatch siamo quasi alla pari** (−0.00198); **sulle equilibrate il
  mercato stacca** (−0.00793, **quattro volte tanto**);
- la forbice **si allarga durante la stagione** (−0.00829 nelle prime 5
  giornate → −0.00991 dalla 26ª).

**Conclusione operativa**: qualunque fonte nuova va valutata **prima di tutto
sulle partite equilibrate della seconda metà di stagione**. È lì che c'è il
divario, ed è il criterio con cui ordinare tutto il §2.

**Aggiornamento Fase 98 — il primo indizio su COSA sia quell'informazione.** Il
movimento apertura→chiusura è stato misurato: non sappiamo anticiparlo (β
−0.0039, R² 0.0001) e il CLV è **negativo con IC conclusivo** (−0.0022
[−0.0033,−0.0012], 45,7% positivi — coerente col −0.0028 della Fase 14). Ma:

- corr(nostro deficit, deficit dell'**apertura**) = **+0.4270**, pendenza
  +1.0336 [+0.9291,+1.1318], contro un placebo per permutazione di **+0.0884**;
- il guadagno del movimento è concentrato sulle **equilibrate** (Q1 +0.0039 vs
  Q4 +0.0007) e nella **seconda metà** (+0.0038 vs +0.0020).

Cioè: **lo stesso profilo del deficit F93**. L'informazione che manca è in buona
parte quella che **arriva nelle ultime ore prima del fischio** — che è
esattamente ciò che le formazioni ufficiali a T−1h (pista 10) contengono. Ordine
di grandezza onesto: tutto il movimento vale **15,6% del nostro gap**;
prendendolo *interamente* (impossibile) resteremmo a +0.0151 contro +0.0179
(numeri interni alla Fase 98, misurati **PRE-fix del prior della Fase 92**: il
gap ufficiale al codice di HEAD è **+0.0167**). È una direzione, non una
soluzione.
*(Autocorrezione: l'ipotesi «il deficit è 4× più grande sulle partite più mosse»
NON sopravvive al placebo — vera +0.0311 contro artefatto +0.0524.)*

---

## 5 · Mercati coperti e mercati mai coperti — Tier 2 e Tier 3

Il `CLAUDE.md` §1.8 definisce tre livelli. **Tier 1 è coperto** (1X2, O/U
1.5/2.5/3.5, GG/NG, doppie chance, total-squadra, clean sheet, vince-a-zero,
scarto ≥2, multigol, risultato esatto) più due famiglie nuove: **campione e
posizionali** (F89/F91) e **corner/cartellini** (F96).

| tier | mercati | stato | prerequisito |
|---|---|---|---|
| **Tier 2** | **handicap asiatico** | ✅ **coperto** (F88 benchmark + F98 listino): **pareggio in Brier** col mercato sharp, 0.2044 vs 0.2044, ΔBrier −0.000136 [−0.000362, +0.000083]. ⚠️ **rettifica F101**: l'affermazione «α\*=0 su un mercato nuovo» non fu mai calcolata — rifatta dà α\* **+1.082** [+0.143, +2.026], IC che **esclude** lo zero. La conclusione onesta è il pareggio, non l'encompassing | — |
| **Tier 3** | **HT/FT**, mercati per tempo | 🟡 **tre mercati coperti** (F98: Halftime +0.0537, Second Half +0.0578, risultato esatto +0.1940, tutti IC conclusivo vs baseline); mancano **HT/FT congiunto** e le combinazioni (pista 6-ter) | — |
| Tier 3+ | **live / in-play** | ❌ scoperto | pista 6-bis (offline, gratis) **poi** pista 18 (raccolta prospettica) |

Il residuo vivo è uno solo ed è localizzato: il **secondo tempo è mal
calibrato** mentre il primo, che passa per lo stesso codice, non lo è → è
**game-state**, e chiede il modello a due stadi (1T indipendente → 2T
condizionato al punteggio dell'intervallo). È anche il primo mattone
dell'in-play, e **si prova senza rete**.

---

## 6 · I punti operativi

### 6.1 · Ri-sondare le fonti — ✅ in gran parte FATTO, e il resto vale meno

> ⚠️ **SUPERATA dalla Fase 100** (verificato il 26/07/2026, ri-testato host per
> host il **28/07/2026**): la rete **è tornata raggiungibile**. Rispondono 200
> `football-data.co.uk`, `understat.com`, `transfermarkt.com`, Kaggle via
> `kagglehub`, `footiqo.com`, `gamma-api.polymarket.com`, `api.smarkets.com`, e
> dal 27/07 anche `huggingface.co`, `datasets-server.huggingface.co`,
> `data.jsdelivr.com`. Bundesliga e Ligue 1 sono infatti state scaricate
> direttamente, senza bundle a mano.
>
> **La mappa autorevole e corrente è `docs/MANUALE_SOPRAVVIVENZA.md` §1**: qui
> non si duplicano gli esiti host per host, perché lì sono datati e aggiornati.

Cosa resta, e vale molto meno di prima:

- un `probe.yml` **dal runner GitHub Actions** per i pochi host che da qui non
  rispondono davvero (**Betfair** e **SofaScore** in testa) e per verificare il
  **vincolo geo/ADM** di oddsportal e betexplorer, che dipende dall'IP e non
  dall'ambiente. Costo: un'ora. Non è più «il punto a valore più alto»;
- `oddsportal.com`: il vincolo **non è tecnico** ma il `robots.txt` (pagine
  storiche vietate) più un feed cifrato; `betexplorer.com` ha **ritirato** le
  quote vecchie. Entrambi: chiusi per merito, non per rete.

**Lezione che resta valida** (Fase 97, riconfermata il 28/07): «presumibilmente
bloccato» **non è un dato**, e un codice di stato va letto insieme al modo in
cui è stato chiesto — `000` (timeout) ≠ `403` (rifiuto) ≠ `404` da filtro
anti-bot ≠ `401` (la richiesta è **uscita**).

### 6.2 · Fonti mai sondate

| fonte | cosa darebbe | nota |
|---|---|---|
| **open-meteo.com** | meteo storico + previsto, **senza chiave, gratis** | **sblocca la pista 13**, ferma solo per mancanza di fonte |
| **Kalshi** | terza borsa — **risponde già** (verificato) | da capire se copre il calcio europeo |
| **The Odds API** | **molti bookmaker insieme, Pinnacle incluso** → sblocca la pista 9 | verificato: 200 ma **401 senza chiave**. Free tier 500 req/mese: basta per gli outright, non per le partite. **Serve una registrazione gratuita: decisione dell'utente** |
| FotMob / API non ufficiali | formazioni pre-partita | fragile: `/api/*` vietato dal loro `robots.txt`, e l'URL senza `#matchId` rende un'altra partita |

### 6.3 · GG/NG: non è più «il mercato con lo spazio aperto»

> ⚠️ **La premessa di questo paragrafo è CADUTA (Fase 100).** Il `CLAUDE.md`
> §1.8 diceva che il GG/NG è «l'unico mercato senza quote nei dati, quindi
> l'unico con spazio non ancora chiuso»: le quote **esistono** (1xBet via
> footiqo, **5.337 partite 2017-20** su 5 leghe) e la domanda è stata
> **misurata**. Il mercato GG/NG **è informativo** (log-loss **0.6840** contro
> **0.6921** di baseline, CI conclusivo), il nostro miglior prezzo lo
> **pareggia e non lo batte** (6 varianti su 6 con CI a cavallo dello zero) e
> il DC **perde di netto** (**+0.0104** [+0.0063, +0.0145], col book che lo
> ingloba: α\*=0 nel 70% dei fit). **Lo "spazio" non era una proprietà del
> mercato: era la nostra ignoranza.**

~~Il GG/NG è **l'unico mercato senza quote nei dati**, quindi **l'unico dove non
abbiamo mai potuto dimostrare l'efficienza del mercato**.~~
Quel che resta, ed è comunque vero: **Polymarket lo quota** (`BTTS`, negli
eventi "More Markets") e il book non lo quota nelle **stagioni recenti**.
Raccoglierlo da subito costa **zero** — il raccoglitore di §7.1 lo prende già —
e dà un campione su un **book diverso** e su anni che nessun archivio copre.

---

## 7 · 💭 Brainstorming — la routine

> Idee da discutere, **non impegni**. Il vincolo di fondo: **il container è
> effimero**, nessuna raccolta ricorrente può girare da una sessione
> interattiva.

### 7.1 · Aggiornamento **giornaliero** dell'elenco mercati

**Stato misurato (28/07/2026)**: `data/outright_snapshots/` contiene **2
istantanee** (`2026-07-25.json` e `2026-07-26.json`) per **930 righe** in
`history.csv`. Cioè: fotografa un istante, **non un movimento**. Con una
istantanea al giorno diventa una **serie storica**, ed è un'altra cosa: si vede
*come si muovono* le quote outright durante la stagione (la favorita che scivola
dopo tre pareggi, la neopromossa che affonda).

- comando già pronto e idempotente: `python scripts/archive_outrights.py`
  (**due fonti** in un colpo: Polymarket + Smarkets)
- costo: ~250-450 righe/giorno → trascurabile
- **serve solo il cron**: GitHub Actions (§7.4). È l'unico pezzo mancante.

### 7.2 · Movimento quote **pre-partita** (l'idea Betfair)

Diverso e più interessante del §7.1: non l'outright ma la **singola partita**,
campionata più volte fra l'apertura e il fischio d'inizio.

**Perché conta.** Il progetto ha un intero documento su un buco di questo tipo
(`docs/CACCIA_OU_2017_19.md`): le quote di **apertura** 2017-19 mancavano e sono
state in parte ricostruite. La traiettoria apertura → chiusura **non l'abbiamo
mai avuta a nessuna scala**, per nessuna lega, in nessuna stagione.

**Cosa si potrebbe chiedere ai dati** (in ordine di serietà):
1. la **direzione e ampiezza** del movimento predicono l'esito oltre la
   chiusura? (la F16 dice che la chiusura ingloba il *nostro modello*, non che
   inglobi il *proprio percorso*);
2. il movimento identifica le chiusure **più affilate** → un θ per-partita
   invece che per-lega, che è esattamente la **pista 4-bis** (la cui versione
   per-lega è stata **falsificata** dalla Fase 100: resta viva solo la
   per-partita);
3. quanto vale, in log-loss, arrivare **in anticipo** su una linea?

**Fonte**: Smarkets ce l'ha già (l'abbiamo), Betfair sarebbe meglio (più
liquida) **se raggiungibile dal runner** → §6.1.

### 7.3 · 💭 Notizie, probabili formazioni, motivazioni ⭐

L'idea dell'utente: far raccogliere alla routine anche **notizie sulla partita,
probabili formazioni e le motivazioni** — l'ex che vuole segnare contro la sua
squadra, il panchinaro che ha l'occasione per prendersi il posto, la squadra
già salva contro quella che si gioca tutto.

**Perché è la cosa più interessante del file.** Punta **esattamente** dove la
Fase 93 ha misurato il buco: il deficit è *informazione*, si concentra sulle
**partite equilibrate**, e cresce durante la stagione. Le motivazioni sono per
definizione informazione **non nei gol e non nell'xG** — sono l'unica cosa che
nessuna delle 30 covariate già bocciate poteva contenere.

**Ma va disegnata con tre paletti, o non misura niente:**

1. **Non è backtestabile. Mai.** Gli archivi di notizie si aggiornano, le date
   di pubblicazione sono inaffidabili, e un articolo scritto *dopo* la partita
   contamina tutto. La regola n.1 del progetto è **niente look-ahead** — e la
   Fase 92 ha scoperto che quella regola *non aveva nemmeno un test*. Quindi:
   **solo raccolta prospettica, con l'istante del fetch congelato** e
   registrato. Il verdetto arriverà fra una stagione, non prima.
2. **L'estrazione dev'essere CIECA alle quote.** Se il modello che legge le
   notizie vede anche il prezzo di mercato, tenderà a riprodurlo, e non
   staremmo misurando l'informazione delle notizie ma la nostra capacità di
   copiare il book. È il paletto più facile da dimenticare e quello che
   invaliderebbe tutto.
3. **L'output dev'essere STRUTTURATO, non prosa.** Uno schema fisso, deciso
   *prima*, con campi numerici — per esempio: assenze pesate per minuti giocati
   nella stagione, indisponibilità del portiere titolare, indice di posta in
   gioco per squadra, flag «derby», flag «ex in campo». La prosa non si può
   né scorare né mettere in un modello.

**Come si valuta** (criteri da fissare prima, §A3 di `newseason.md`): solo
partite equilibrate, metrica = **risoluzione**, e sempre contro un **controllo**
identico senza notizie. Se non recupera almeno **1/3** del divario −0.0079, è
un negativo — e si scrive, come tutti gli altri.

**Rischio onesto, dichiarato in anticipo**: è del tutto possibile che il mercato
abbia già prezzato queste notizie *meglio e prima* (F16: α\*=0 contro la
chiusura). In quel caso il risultato sarà «informazione vera ma già nel prezzo»,
che è comunque un risultato pubblicabile nel diario.

### 7.4 · Chi fa cosa

| canale | forte in | debole in | proposta |
|---|---|---|---|
| **GitHub Actions** (cron) | deterministico, rete libera, gratis, **committa nel repo**, alta frequenza | zero giudizio | ✅ **raccolta**: §7.1 + §7.2 + il fetch grezzo di §7.3 |
| **Routine Claude Code** | ha giudizio: legge, nota le anomalie, scrive il diario, avvisa | consuma budget, va tenuta a guinzaglio corto | ✅ **settimanale**: scorare, estrarre le feature strutturate di §7.3, segnalare |
| **Task ChatGPT** | zero attrito | **non esegue il nostro codice né committa** | ❌ ridondante |

**Cautele** (lezione Fase 92, un cron attivo in silenzio che committava ~51 MB):
`workflow_dispatch` prima di `schedule`; gli snapshot congelati **mai** toccati;
file partizionati con tetto di dimensione; in caso di dubbio la routine **si
ferma e avvisa** invece di decidere.

**Due domande aperte** (nessuna preferenza forte da parte mia): la routine
**settimanale o dopo ogni giornata**? E può **committare da sola** o deve solo
segnalare?

### 7.5 · 💭 Database giocatore/arbitri/allenatori ⭐ (idea dell'utente, 29/07/2026)

L'idea: il calcio è un gioco di squadra ma ogni giocatore incide più o meno
di un altro — raccogliere minuti giocati, subentri, gol, assist e (dove
possibile) tocchi/passaggi/dribbling/interventi per ogni giocatore, più
l'affaticamento da minuti consecutivi (club **e** nazionale), più i gol
subiti per portiere. **Estesa lo stesso giorno** ad arbitri e allenatori
(ipotesi: lo stile di una squadra sotto un allenatore si ripete quando
l'allenatore cambia squadra), per club **e** nazionali, incluse le
competizioni europee per i club.

**Non è ancora una pista prioritizzata** come quelle di §2: è aperta oggi come
**pista 21** in `docs/PISTE.md` con un piano dedicato,
[`docs/PIANO_DATABASE_GIOCATORI.md`](docs/PIANO_DATABASE_GIOCATORI.md).
Riassunto: gran parte della richiesta giocatori (minuti, subentri,
gol/assist, portiere) è **quasi gratis** — stesso dataset CC0 già importato
per i valori di rosa (Fase 67), un file (`appearances.csv`) già scaricato
sul disco e mai parsato, altri due (`game_lineups.csv`/`game_events.csv`,
piste 10/11) mai importati; i dati "event/advanced"
(tocchi/passaggi/dribbling/contrasti) non hanno oggi **nessuna fonte pulita
nota** (Opta commerciale, WhoScored/SofaScore/FBref/Flashscore chiusi il
28/07/2026). **Scoperta verificata oggi** (scaricato per davvero il dataset,
non a memoria): lo stesso CC0 ha anche `games.csv`/`club_games.csv` (35 MB),
con **arbitro e allenatore per partita al >99,7% di copertura**, sulle 5
leghe **e** su Champions/Europa/Conference League 2017-2025 — sblocca da
solo il fronte arbitri (che il progetto misura già dalla Fase 125/126, qui
si struttura soltanto) e l'estensione europea degli allenatori chiesta
dall'utente. Restano scoperti: lo stile di gioco (possesso/xG) nelle coppe
europee, e l'affaticamento/gli allenatori da **nazionale** nelle finestre
FIFA regolari (terreno mai esplorato). Nessun dato ancora importato nel
repo, nessun codice scritto: il piano propone `games.csv`/`club_games.csv`
come primo passo (miglior rapporto valore/costo) più un tracer bullet su
una lega-stagione, un **controllo finale su Wikipedia** (§6-bis del piano,
richiesta utente — **completo su ogni dato, non a campione**) per
verificare con una fonte indipendente che i dati raccolti siano corretti, e
un elenco di **arricchimenti aggiuntivi** (§1.8: età ed esperienza di
giocatori/allenatori/arbitri — anche pregressa fuori dalle 5 leghe, essendo
il dataset globale —, attendance, andata/ritorno, rigori) da aggiungere
**una funzionalità alla volta** (richiesta utente). Una revisione critica
(§6-ter) elenca dieci problemi trovati nel ragionamento — dai nomi senza ID
stabile per allenatori/arbitri alla riproducibilità su un dataset che si
aggiorna ogni settimana — ciascuno con una correzione proposta. Chiarita
anche la **grana dei dati** (§1.0): base = partita, non stagione (lo
stagionale è sempre derivato per somma); per le nazionali serve un livello
in più fra partita e stagione, la **convocazione per finestra FIFA**
(conta per la fatica anche senza un minuto giocato). Nessuna idea d'uso
(§4 del piano) è stata decisa — resta da concordare con l'utente.

---

## 8 · Ordine consigliato per la prossima sessione

1. **Il blocco con la scadenza**, da [`newseason.md`](newseason.md) §5 e dalla
   checklist eseguibile di `experiments/prospettico_2026_27.md` §5:
   pre-registrazione dei criteri → sondaggi (libri Smarkets per-partita,
   fixture) → raccoglitore + cron → previsioni congelate. **Entro il 16
   agosto**, il resto no.
2. ⭐ **Il modello a DUE STADI per il secondo tempo** (pista 6-bis, residuo
   F98): il primo residuo *localizzato e non-artefatto* trovato da parecchie
   fasi, primo mattone dell'in-play — **sui dati che già abbiamo**.
3. **Le piste nei grezzi già scaricati** (PISTE 8 e 9: quota massima, Pinnacle
   puro): nessuna rete, nessuna attesa. *(Le piste 5 e 6 sono state chiuse da
   F88/F98: Tier 2 e Tier 3 di base non sono più scoperti.)*
4. **La coda a zero** (`docs/PISTE.md` §4-bis, aperta dalla F97) e, prima di
   riprezzare il 2027 Champion, **rilanciare la Fase 89 su 5 leghe**: da 24 a
   ~40 stagioni-lega con **un run**, contro le +3 che ogni stagione regala.
5. **Il lavoro documentale rimasto** (audit §4, punti 6 e 13): le 18 celle
   PANCHINA già misurate, il riporto della Fase 100 in `STUDIO_PREMIER_LIGA.md`,
   e la propagazione di numero-bandiera e rettifica COM-Poisson fuori dal
   README. È trascrizione, non ricerca — ma finché non è fatta il repo dice due
   cose diverse.
6. **`probe.yml` dal runner** (§6.1) — un'ora, ma ormai vale solo per Betfair,
   SofaScore e il vincolo geo.
7. Il resto, senza fretta.

**Da non fare adesso**: ~~aggiungere le leghe nuove (Ligue 1/Bundesliga come
leghe *modellate*)~~ → **FATTO alla Fase 100**: sono in `LEAGUE_CONFIGS`, con
snapshot congelati (2.754 e 3.097 partite) e δ 0.28/0.19. Resta valido per
**Serie B e Championship**: valore reale, **nessuna scadenza**, mangerebbe le
settimane che servono al punto 1. **Dopo settembre.**
