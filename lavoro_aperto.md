# Lavoro aperto — indice unico per la prossima sessione

> **Cos'è questo file.** Un **indice**, non una quarta fonte di verità. Le fonti
> canoniche restano `docs/PISTE.md` (piste), `docs/PANCHINA.md` (rosa dei
> modelli), `docs/DIARIO.md` (narrazione) e il registro del `README.md`. Qui
> c'è (a) il **quadro d'insieme** di cosa è aperto, con i rimandi, e (b) le
> cose che **non vivono ancora da nessuna parte**: i tre punti operativi e il
> brainstorming.
>
> **Regola d'uso**: quando una voce si chiude, si aggiorna la **fonte
> canonica** e poi questa riga. Se questo file e PISTE/PANCHINA divergono,
> **hanno ragione loro**.
>
> Scritto il **26 luglio 2026**, dopo la Fase 97; **aggiornato dopo le Fasi 98-99**
> (sette fronti: vedi il registro del README e l'arco 11 del diario). Il piano *datato* per l'inizio
> stagione sta in [`newseason.md`](newseason.md): quello ha una scadenza
> (16 agosto), questo no.

---

## 0 · Il quadro in tre righe

Il tetto del progetto è **informativo, non architetturale**: tutti i dati
*interni* sono esplorati e una decina di architetture alternative sono state
provate e bocciate. Quindi il lavoro aperto si divide in tre famiglie:

1. **cose mai provate che non costano dati nuovi** (le più economiche, §2-§3);
2. **cose che richiedono informazione nuova** — l'unica leva non esaurita, e
   dopo la Fase 93 sappiamo *esattamente* dove punta: **partite equilibrate,
   seconda metà di stagione** (§4);
3. **mercati mai coperti** (Tier 2 e Tier 3, §5).

---

## 1 · Fase 78 — l'unica fase formalmente APERTA

Il **test prospettico 2026-27**: previsioni congelate *prima* del calcio
d'inizio, scorate dopo. È il gold standard del progetto — l'unico disegno in cui
il look-ahead è impossibile per costruzione, non per disciplina.

| pezzo | stato |
|---|---|
| `experiments/prospettico_2026_27.md` | esiste (impostazione) |
| `experiments/prospettico_2026_27_dc.csv` | esiste |
| `experiments/prospettico_2026_27_outright.json` | **congelato** (Fase 96) |
| **livello-partita** | ❌ **manca** |
| **script di scoring** | ❌ **manca** |

⏰ **Ha una scadenza vera: 16 agosto** (via della Liga). Il piano operativo,
con le date e la checklist, è in [`newseason.md`](newseason.md) §5.

---

## 2 · `docs/PISTE.md` — 23 voci, **17 ancora aperte**

Conteggio verificato il 26/07/2026. Ordinate per costo crescente, come nel file.

### Senza dati nuovi (solo codice sugli snapshot già in repo)

| # | pista | stato |
|--:|---|---|
| 1 | **Scontri diretti (head-to-head)** — accoppiamento specifico della coppia | 🟢 mai provata. *Zero occorrenze in 68 fasi: un vuoto sorprendente.* Angolo consigliato: **totali/GG**, non 1X2 |
| 2 | **Covariate anche nel sotto-modello xG** | 🟢 mai provata. Potrebbe far riemergere covariate borderline bocciate *per diluizione* (α=0.75), non perché nulle |
| 3 | **Denoising cross-partita dei λ,μ impliciti** | 🟢 mai provata |
| 4-bis | **θ del router come funzione del MARGINE** | 🟢 mai provata. Unificherebbe F53 (θ ↓ con la liquidità) e F75 (θ ↑ nel tempo) in **una curva universale** |
| 4-quater | **θ_team per gli esiti rari** (LEAD, F86) | 🟢 mai provata |
| 4 | Market-implied multi-mercato su Premier/Liga | ✅ **chiusa positiva** (F76: 13/14 mercati su 3 leghe) |
| 4-ter | Coda a due parametri (tensione di profondità) | ✅ **chiusa** (F87: riprodotte, non adottabili) |

### Nei grezzi **già scaricati** e mai estratti (nessuna rete!)

| # | pista | stato |
|--:|---|---|
| 5 | **Handicap asiatico** → terzo vincolo per l'inversione market-implied | 🟢 mai estratta. È anche il **Tier 2** (§5) |
| 6 | **Primo tempo** (HTHG/HTAG/HTR) → Tier 3 + fondazione live | ✅ **chiusa positiva (F98)**: f=0.4396 misurata, 3 mercati Tier 3 validati con IC conclusivo. 🟢 **resta aperto il residuo**: il 2T è mal calibrato (game-state) → modello a due stadi |
| 8 | **Quota massima** (MaxC\*/Max\*) → ROI realistico | 🟢 mai estratta. Tutti i ROI del progetto usano la media: col massimo cambierebbero |
| 9 | **Pinnacle puro** (PS\*/PSC\*) come benchmark singolo-book | 🟢 mai estratta. È *il* riferimento di efficienza |
| 7 | Statistiche partita (corner, tiri, falli, cartellini) | 🟡 **parziale**: corner e cartellini fatti (F96) + NB (F98, trascurabile); **tiri totali e falli no**; arbitro ❌ chiuso (F98) |
| **7-bis** | **Correzione di LIVELLO dei conteggi** (lead F98) | ❌ **chiusa NEGATIVA (F99)**: 5 stimatori + emivita alla radice, nessuno migliora, 5/8 celle peggiorano con IC conclusivo. Il bias di fold **non persiste** (10/18 stesso segno) → era rumore aggregato, non deriva. Riaprirla richiede informazione nuova (regolamento/direttive arbitrali), non un estimatore migliore |

### Fonte esterna nuova

| # | pista | stato |
|--:|---|---|
| 10 | **Formazioni ufficiali** → assenze VERE | 🟢 aperta — *la più preziosa* (§4). **F98: il surrogato storico è BOCCIATO** (correla +0.9603 col valore rosa; nulla sul bersaglio F93) → resta solo la **formazione ufficiale a T−1h raccolta prospetticamente**. È un argomento *a favore* della raccolta: esclude la scorciatoia |
| 11 | `transfers.csv` → shock di gennaio | 🟢 aperta (va raccolto **a gennaio**) |
| 12 | Risultati di seconda serie → prior neopromosse individualizzato | 🟢 aperta. Puntuale dopo la F97: sbagliamo di **+19.6pp** proprio sulle neopromosse |
| 13 | **Meteo pre-partita** | 🟢 aperta — ferma per mancanza di fonte, ma **open-meteo è gratis e senza chiave** (§6.2) |
| 15 | Altre linee O/U (multi-linea) per vincolare λ,μ | 🟢 aperta |
| 14 | Bundle Understat Premier/Liga | ✅ **chiusa positiva** (F54-57) |

### Raccolta prospettica (mesi, non giorni) — **tutte legate a §7**

| # | pista | stato |
|--:|---|---|
| 16 | **GG/NG quotato + aperture vere** | ✅ **premessa CADUTA (F100)**: le quote GG/NG esistono (1xBet, 5.337 partite 2017-20) e la domanda è misurata — mercato informativo, il nostro prezzo lo pareggia, il DC perde. Resta aperta **solo** la raccolta prospettica sulle stagioni recenti |
| 17 | Paper-trading della strategia draw-bias | 🟢 aperta |
| 18 | **Dati in-play** (quote minuto per minuto) | 🟢 aperta — esiste solo *durante* la stagione. **F98: la fondazione offline c'è** (pista 6) e il modello a due stadi si può provare **senza rete** |
| 19 | Quote O/U 2017-19, chiusura vera | ✅ **CHIUSA (F100)**: dato trovato (1xBet via footiqo, 3.652/3.652) ma **non inserito** — un solo book, peggiore della stima come proxy multi-book |

---

## 3 · `docs/PANCHINA.md` — **134 caselle ⬜** (mai testato lì)

Il principio §1.9 impone due fronti per ogni modello: **per-lega** e
**generale**. La matrice ha **134** celle `⬜` — e la legenda del file lo dice
esplicitamente: *«è lavoro potenziale, non un'assoluzione»*.

> Il conteggio era **24** e vale 138 dal 26/07/2026 (ri-contato dall'audit della
> Fase 101): non è lavoro andato perduto, è la matrice che è passata da 4 a 6
> colonne quando Bundesliga e Ligue 1 sono entrate in produzione (Fase 100).
> Ogni modello ha ora due colonne-lega in più da riempire.
> **Da 138 a 134** nella stessa Fase 101: la riga COM-Poisson ha perso le sue 4
> caselle vuote perché ha smesso di essere un modello a sé (`dp(θ) ≡
> COM-Poisson(ν=θ)` — non c'è nulla da testare su quelle colonne).
>
> Come si ri-conta: `sum(l.count('⬜') for l in open('docs/PANCHINA.md') if
> l.strip().startswith('|'))` dà **134**; il file ne contiene 136, perché due
> stanno nelle legende (righe 20 e 54) e non sono celle della matrice.

**La forma del buco**: quasi tutti i modelli in **panchina** o **bocciati** sono
stati provati **solo sulla Serie A**. Nessuno sa cosa facciano altrove.

| famiglia | modelli con Premier/Liga/generale mai testati |
|---|---|
| 🪑 **in panchina in Serie A** (potrebbero essere titolari altrove) | nudge GG/NG di fine stagione (F48), ensemble emivite 180+730 (F12a), ricalibrazione per-classe del modello (F10), diagonale inflazionata (F12b), temperature scaling post-hoc (F6) |
| ❌ **bocciati in Serie A** (una bocciatura su una lega non è universale) | Poisson bivariato λ3, copula di Frank, GAS/state-space, binomiale negativa · zero-inflazione · Rue-Salvesen, ρ dinamico, power-devig, covariata stakes, vantaggio-casa per-squadra, covariate nel canale-pareggio, ricalibrazione O/U, ensemble standalone, blend modello+mercato, profilo stagionale dinamico, tiri in porta grezzi, covariate squad_value/absence/npxG/forma/luck/ppda/deep |

⚠️ **Attenzione al costo-opportunità.** Riaprire un modello bocciato su un'altra
lega è economico ma raramente paga: la Fase 79-80 ha già mostrato che diverse
leve della Serie A **non si replicano** (φ35 sul path DC, `rest_full`,
`midweek_europe`, il draw-bias). La priorità onesta è **bassa** — salvo dove c'è
una ragione strutturale, non solo una casella vuota.

---

## 4 · Il bersaglio misurato (dove conviene davvero cercare)

Non è un'opinione, è la Fase 93:

- il deficit è **104% informazione e −4% calibrazione** → **nessuna
  ricalibrazione può chiudere il gap**, è misurato, non provarci più;
- siamo perfino **meglio calibrati del mercato** (0.00083 contro 0.00125);
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
prendendolo *interamente* (impossibile) resteremmo a +0.0151 contro +0.0179. È
una direzione, non una soluzione.
*(Autocorrezione: l'ipotesi «il deficit è 4× più grande sulle partite più mosse»
NON sopravvive al placebo — vera +0.0311 contro artefatto +0.0524.)*

---

## 5 · Mercati mai coperti — Tier 2 e Tier 3

Il `CLAUDE.md` §1.8 definisce tre livelli. **Tier 1 è coperto** (1X2, O/U
1.5/2.5/3.5, GG/NG, doppie chance, total-squadra, clean sheet, vince-a-zero,
scarto ≥2, multigol, risultato esatto) più due famiglie nuove: **campione e
posizionali** (F89/F91) e **corner/cartellini** (F96).

| tier | mercati | stato | prerequisito |
|---|---|---|---|
| **Tier 2** | **handicap asiatico** | ✅ **coperto** (F88 benchmark + F98 listino: Brier 0.2044 vs 0.2044, Δ −0.0000 — **l'unica riga del listino che regge un'affermazione di efficienza**) | — |
| **Tier 3** | **HT/FT**, mercati per tempo | 🟡 **tre mercati coperti** (F98: Halftime +0.0537, Second Half +0.0578, risultato esatto +0.1940, tutti IC conclusivo vs baseline); mancano HT/FT congiunto e le altre combinazioni | — |
| Tier 3+ | **live / in-play** | ❌ scoperto | pista 18 (raccolta prospettica) |

Il Tier 3 è anche la **fondazione dei mercati live**, che è la direzione con più
mercato reale — ma richiede il primo tempo (pista 6) come mattone.

---

## 6 · I tre punti operativi

### 6.1 · Ri-sondare le fonti **dal runner GitHub Actions** ⭐

Il proxy di una sessione cloud e il runner Actions hanno **IP e regole
diverse**, e non è mai stato verificato in modo sistematico. Un workflow
`probe.yml` che prova ~20 host e committa una tabella di esiti costa **un'ora**.

**Perché è il punto con il rapporto valore/costo più alto**: la Fase 97 ha
dimostrato che le etichette «presumibilmente bloccato» erano **sbagliate** —
`oddsportal.com` e `betexplorer.com` rispondevano da mesi e nessuno aveva
provato. Due candidati cambierebbero parecchio:

> ⚠️ **SUPERATA dalla Fase 100** (verificato il 26/07/2026, audit Fase 101):
> la rete **è tornata raggiungibile**. Rispondono 200 `football-data.co.uk`,
> `understat.com`, `transfermarkt.com` e Kaggle via `kagglehub` — infatti
> Bundesliga e Ligue 1 sono state scaricate direttamente, senza bundle a
> mano. Restano davvero da provare solo **Betfair** e **SofaScore**; per
> `oddsportal.com` il vincolo non è tecnico ma il `robots.txt` (pagine
> storiche vietate) e BetExplorer ha ritirato le quote vecchie.
> Stato aggiornato in `docs/MANUALE_SOPRAVVIVENZA.md` §1.
> La colonna «qui» qui sotto è quindi **storica**, non lo stato di oggi.

| fonte | cosa darebbe | qui | da Actions |
|---|---|---|---|
| **Betfair Exchange** | la borsa più liquida al mondo; **movimento quote pre-partita** (§7.2) | 403 | ❓ |
| **football-data.co.uk** | è la **nostra fonte primaria**: oggi vive solo di bundle caricati a mano | 403 | ❓ |
| SofaScore | formazioni, statistiche live | 403 | ❓ |
| Understat | xG Premier/Liga | 403 | ❓ |
| Transfermarkt | valori rosa (oggi recupero manuale) | bloccato | ❓ |

### 6.2 · Fonti mai sondate

| fonte | cosa darebbe | nota |
|---|---|---|
| **open-meteo.com** | meteo storico + previsto, **senza chiave, gratis** | **sblocca la pista 13**, ferma solo per mancanza di fonte |
| **Kalshi** | terza borsa — **risponde già** (verificato) | da capire se copre il calcio europeo |
| **The Odds API** | **molti bookmaker insieme, Pinnacle incluso** → sblocca la pista 9 | free tier 500 req/mese: basta per gli outright, non per le partite. **Serve una registrazione gratuita: decisione dell'utente** |
| FotMob / API non ufficiali | formazioni pre-partita | fragile |

### 6.3 · GG/NG: il mercato che si può aprire **subito**

> ⚠️ **La premessa di questo paragrafo è CADUTA (Fase 100).** Il `CLAUDE.md`
> §1.8 diceva che il GG/NG è «l'unico mercato senza quote nei dati, quindi
> l'unico con spazio non ancora chiuso»: le quote **esistono** (1xBet via
> footiqo, 5.337 partite 2017-20 su 5 leghe) e la domanda è stata **misurata**.
> Il mercato GG/NG è informativo (0.6840 contro 0.6921), il nostro prezzo lo
> **pareggia** e il DC **perde** (+0.0104, con il book che lo ingloba).
> La raccolta prospettica resta utile — book diverso, stagioni recenti che
> nessuno quota — ma **non** perché «non abbiamo quote».

Il `CLAUDE.md` §1.8 diceva che il GG/NG è **l'unico mercato senza quote nei
dati** (football-data non le include), quindi **l'unico dove non abbiamo mai
potuto dimostrare l'efficienza del mercato** — *«l'unico con spazio non ancora
chiuso dai risultati delle Fasi 14/16/20»*.

**Polymarket lo quota** (`BTTS`, negli eventi "More Markets"). Raccogliendolo da
subito, fra una stagione la **pista 16 si chiude in un senso o nell'altro**.
**Costo marginale zero**: il raccoglitore di §7.1 lo prende già.

---

## 7 · 💭 Brainstorming — la routine

> Idee da discutere, **non impegni**. Il vincolo di fondo: **il container è
> effimero**, nessuna raccolta ricorrente può girare da una sessione
> interattiva.

### 7.1 · Aggiornamento **giornaliero** dell'elenco mercati

Oggi l'archivio ha **poche istantanee**: fotografa un istante, non un
movimento. Con una istantanea al giorno diventa una **serie storica**, ed è
un'altra cosa: si vede *come si muovono* le quote outright durante la stagione
(la favorita che scivola dopo tre pareggi, la neopromossa che affonda).

- comando già pronto e idempotente: `python scripts/archive_outrights.py`
- costo: ~250-450 righe/giorno → trascurabile
- **serve solo il cron**: GitHub Actions (§7.4)

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
   invece che per-lega, che è esattamente la **pista 4-bis**;
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

---

## 8 · Ordine consigliato per la prossima sessione

1. **Il blocco con la scadenza**, da [`newseason.md`](newseason.md): sondaggi →
   pre-registrazione dei criteri → raccoglitore → previsioni congelate.
   **Entro il 16 agosto**, il resto no.
2. **`probe.yml` dal runner** (§6.1) — un'ora, può sbloccare mezza lista.
3. ⭐ **Il modello a DUE STADI per il secondo tempo** (pista 6, residuo F98): il
   primo residuo *localizzato e non-artefatto* trovato da parecchie fasi, ed è
   anche il primo mattone dell'in-play — sui dati che già abbiamo.
4. **Le piste nei grezzi già scaricati rimaste** (§2: 8, 9): nessuna rete,
   nessuna attesa. *(La 5 e la 6 sono state aperte da F88/F98: Tier 2 e Tier 3
   non sono più scoperti.)*
5. **La coda a zero** (`docs/PISTE.md`, pista aperta dalla F97) — costo basso,
   infrastruttura già presente.
6. Il resto, senza fretta.

**Da non fare adesso**: ~~aggiungere le leghe nuove (Ligue 1/Bundesliga come
leghe *modellate*)~~ → **FATTO alla Fase 100**: sono in `LEAGUE_CONFIGS`, con
snapshot congelati (2.754 e 3.097 partite) e δ 0.28/0.19. Resta valido per
Serie B e Championship. Valore reale, **nessuna scadenza**,
mangerebbe le settimane che servono al punto 1. Dopo settembre.
