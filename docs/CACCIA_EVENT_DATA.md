# Caccia all'event data per giocatore (31/07/2026)

> **Cos'è questo file.** Il verbale integrale di un lavoro a 10 agenti eseguito il
> 31/07/2026 su richiesta esplicita dell'utente: *«ci servono gli event data.
> troviamo un modo per ottenerli. su diretta.it navigando partita per partita»*.
>
> **Risposta breve: su diretta.it NO** — non per la rete e non per il `robots.txt`
> (che non ci vieta nulla), ma perché i Termini d'uso vietano lo scraping **per
> nome**, rivendicano il diritto sui generis sulla banca dati, e il dato è **di
> Opta**, non di Livesport. E comunque quella strada **non darebbe event data**
> (zero coordinate x,y) e coprirebbe il **12,7-14,7%** delle nostre partite.
>
> **La via che resta è una sola ed è gratuita**: il rilascio Wyscout/Pappalardo
> 2017-18 su figshare, CC BY 4.0 verificata all'endpoint — 1.826 partite, una
> stagione al 100% su tutte e 5 le leghe, con il log azione-per-azione completo.
>
> ⚠️ **Questo lavoro ha prodotto anche un rilievo su una fonte GIÀ IN PRODUZIONE**
> (Transfermarkt via Kaggle, sorgente di `squad_value` dalla Fase 67): vedi §3.
> È una **decisione da prendere**, non un fatto già deciso.
>
> Metodo dichiarato: sulla fonte proposta dall'utente **non è stata raccolta una
> sola riga di dati** — ~25 pagine aperte a ritmo umano per il solo censimento.
> **Nessuna protezione è stata incontrata né aggirata**: il sito ha risposto 200 a
> ogni richiesta. È esattamente il caso in cui la tentazione è massima e la
> risposta è comunque no.

---


*Redatto il 31/07/2026. Tutti i numeri sono misurati; dove non lo sono è scritto «non misurato».*

---

## 0. Il chiarimento che viene prima di tutto: sono DUE obiettivi, non uno

La richiesta dice «event data». Nel materiale raccolto le cose che cerchiamo sono due, con difficoltà molto diverse:

| | **A · Event data in senso stretto** | **B · Aggregati per giocatore-partita** |
|---|---|---|
| cos'è | log di **ogni azione** con coordinate x,y (~2.000 righe/partita) | **conteggi** di fine partita per giocatore (tocchi, passaggi, dribbling, contrasti, falli) |
| chi ce l'ha, gratis e pulito | **Wyscout/Pappalardo: 1.826 partite = 11,33%** | si **deriva** da A; altrimenti va comprato |
| chi ce l'ha, a pagamento | nessuno alla nostra portata (Opta F24, Hudl raw X&Y: enterprise, cinque cifre/anno) | Sportmonks, con riserve pesanti (§2) |
| copertura aperta fuori dal 2017-18 | **1,37%** (196 partite su 14.285) | idem |

Quasi tutte le righe «Tier B» della checklist del progetto (tocchi, passaggi, dribbling, contrasti) sono **B, non A**. Questo è importante perché **B si ottiene da A** (dal log Wyscout si aggregano tutti quei conteggi) ma **A non si ottiene da B**. Chi vende B (Sportmonks) non vende A.

E c'è una terza cosa che il materiale rende evidente: **i portali consumer (diretta.it, FotMob) non hanno A.** Hanno B con le coordinate sui soli tiri. Quindi la navigazione partita-per-partita, anche se fosse lecita, **non produrrebbe event data.**

---

## 1. diretta.it: si può o no

> **NO.** Il `robots.txt` non ci vieta le pagine-partita, ma i Termini d'uso vietano lo scraping **per nome**, rivendicano il diritto sui generis sulla banca dati, e il dato è **di Opta**, non di Livesport.
> Anche se fosse lecita, quella strada **non darebbe event data** (zero coordinate x,y) e coprirebbe **12,7%-14,7%** delle nostre 16.111 partite.
> Le due cose insieme rendono la decisione facile: si rinuncia a poco, e a un rischio civile/amministrativo/penale esplicitato dal contratto.

### (a) Gate robots.txt — **APERTO**, e irrilevante

`https://www.diretta.it/robots.txt`, HTTP 200. `User-agent: *` vieta **4 cose**: `/classifiche/`, `/tabellone/`, `/newsfeed/` e un file JS. Le pagine `/partita/` non sono vietate. ~16 crawler AI sono bloccati **per nome** (CCBot, AI2Bot, Bytespider, Meta-*, Diffbot…); `ClaudeBot` e `anthropic-ai` **non** sono fra questi.

Righe che ci vietano le pagine-partita: **0**.

Non decide. Precedente interno già stabilito (bundesliga.com, riserva DFL ex §44b(3) UrhG): **quando robots.txt e riserva legale divergono, vince la riserva legale.**

### (b) Gate termini di servizio + sui generis — **CHIUSO, quattro volte**

Livesport s.r.o., Praga. Legge e foro: **Repubblica Ceca** (zák. 121/2000 Sb. §88 ss., attuazione Dir. 96/9/CE — l'equivalente del nostro art. 102-bis L.633/41). Clausola 2, quattro divieti **indipendenti**, ognuno sufficiente da solo:

| # | cl. | testo | colpisce |
|---|---|---|---|
| a | 2.2 | *«unicamente per uso personale. L'Utente non può utilizzare il Sito per nessuno scopo commerciale»* | l'uso |
| b | 2.8 | *«riproduzione (copia) per un guadagno economico diretto o indiretto … non è consentito»* | la copia |
| c | 2.9 | *«non sono consentiti l'estrazione (copia) o l'utilizzo … di una sua parte qualitativamente o quantitativamente sostanziale»* | l'estrazione |
| d | 2.10 | *«non è consentito utilizzare il contenuto … effettuando lo **scraping** o ricreandolo»* + *«non è consentito appesantire il nostro server con richieste automatiche»* | il metodo |

La parola **«scraping» è scritta in chiaro**. Non stiamo interpretando una clausola generica.

**«Non ci registriamo, quindi non siamo vincolati» non funziona:** cl. 1.2 dice che agli utenti **non registrati** si applicano *«in particolare le clausole 1, 2 e 10»* — e la clausola 2 è esattamente quella che contiene tutti e quattro i divieti.

**Sui generis, dove cadremmo:** 16.111 partite × 22-30 giocatori ≈ **350.000-480.000 record**. Sostanziale per quantità, per qualità (le Big Five sono il cuore commerciale della banca dati) e comunque colpita dall'**art. 7(5)** Dir. 96/9/CE sull'estrazione **ripetuta e sistematica** — che è la definizione letterale di «navigare 16.111 pagine una per una».

Le due vie d'uscita teoriche non salvano:
- **spin-off** (CGUE C-203/02 *BHB v William Hill*): protegge chi *ottiene* i dati, non chi li *crea*. Livesport i dati **li compra da Opta** → è investimento nell'ottenimento, cioè il nucleo protetto;
- **CGUE C-30/14 *Ryanair v PR Aviation***: per una banca dati **non** protetta il titolare resta libero di imporre restrizioni **contrattuali**. Più il sui generis è debole, più il contratto è forte. Non c'è interstizio;
- **TDM commerciale** (art. 4 Dir. 2019/790, art. 70-quater L.633/41): il divieto in ToS **è** la riserva ex art. 4(3) (cons. 18), e il nostro output sarebbe una banca dati permanente e sostitutiva, non copie transitorie di mining.

Cl. 2.11: *«responsabilità civili, amministrative o penali»*.

Fornitore dichiarato dal sito stesso: *«Utilizziamo **Opta** come fornitore di dati sul calcio per tutte le principali competizioni»*. È lo stesso motivo per cui il progetto ha già chiuso WhoScored. **Ed è lo stesso identico caso della Premier League API**, già chiusa «per licenza, non per rete» — diretta.it è più restrittiva su tre assi (sui generis rivendicato, richieste automatiche vietate, uso personale). Riaprire l'una tenendo chiusa l'altra sarebbe incoerenza.

### (c) Gate «cosa c'è davvero» — **misurato con Chromium+Playwright, ~25 pagine, nessuna protezione incontrata né aggirata**

**Ci sono statistiche per singolo giocatore: sì, 46 campi** (Rating, Palloni toccati, Palloni toccati in area avversaria, Passaggi riusciti n/n%, Dribbling riusciti, Contrasti vinti/aerei/a terra, Palle intercettate, Falli commessi/subiti, xG e xA individuali, Grandi occasioni create, Passaggi chiave, blocco portiere completo).

**Coordinate x,y: ZERO.** Nessuna shot-map, nessuna heatmap, nessuna chiave di traduzione per shot-map nel bundle JS (le uniche voci «field/shot» sono di basket e baseball). L'unico oggetto quasi-spaziale è il **Match Momentum**, che è una serie **per minuto** del modello Opta.

**E soprattutto: l'archivio è povero.** Il confine cade **dentro la stagione 2024-25**, fra il 9 marzo e il 23 aprile 2025:

| stagione campionata | STATS GIOCATORE | xG squadra | voci stat squadra |
|---|---|---|---|
| 2017-18, 2018-19, 2019-20, 2021-22 | no | no | 12 |
| 2022-23, 2023-24 | no | **sì** | intermedio |
| 2024-25 · 09.03.2025 | **no** | sì | intermedio |
| 2024-25 · 23.04.2025 | **sì** | sì | 39 |
| 2025-26 | **sì** | sì | 39 |

Sulle nostre 16.111 partite:

| | partite | % |
|---|---:|---:|
| finestra realmente coperta dal per-giocatore | **2.000-2.400** | **12,7-14,7%** |
| tetto teorico se tutta la 2024-25 fosse coperta (non lo è) | 3.504 | 21,7% |
| **2017-18 … 2023-24: NIENTE oltre a minuti/gol/assist/cartellini/rating (già posseduti)** | **10.607** | **65,8%** |

*Onestà sulla misura: un solo campione per stagione-lega, e solo Serie A e Premier. Liga, Bundesliga e Ligue 1 non sono state campionate.*

### Il costo, per completezza

| voce | valore | come |
|---|---|---|
| pagine da aprire | **32.222** | 16.111 partite × 2 (statistiche + statistiche-giocatore) |
| tempo a 4 s/pagina | **36 h** | limite inferiore ottimistico |
| tempo a 10 s/pagina | **90 h** | ritmo realistico: SPA, contenuto iniettato via JS, ~7-8 s di attesa |
| solo la finestra utile (~2.200 partite) | 4.400 pagine → **5-12 h** | |
| denaro | 0 € | nessun paywall, nessuna registrazione |

**Il costo non è la variabile che decide.** Anche a costo zero e a ritmo umano, il primo passo tecnico sarebbe già la violazione.

**Non aprire codice su diretta.it, né via HTTP né via Playwright.** Il vincolo è legale: un browser funzionante non cambia la risposta.

---

## 2. La classifica delle vie praticabili

Le sfide dello scettico hanno precedenza: dove hanno declassato una fonte, vale il verdetto declassato.

### 🥇 1. Wyscout/Pappalardo (figshare, CC BY 4.0) — **l'unica via gratuita, pulita e con event data VERO**

| | |
|---|---|
| **cosa dà** | **event log completo con coordinate**: un record per azione (Pass, Shot, Duel, Foul, Touch, Save, Interruption…), `positions` = [{x,y} inizio, {x,y} fine] in % 0-100 del campo, `tags` (accurate/not accurate, key pass, counter attack, interception, clearance, sliding tackle, feint, piede dx/sx, testa). **Da qui si derivano TUTTI i conteggi per giocatore-partita richiesti**: tocchi, passaggi tentati/riusciti, dribbling, contrasti, recuperi, falli individuali |
| **NON dà** | xG e xA nativi (il rilascio pubblico li omette); «grandi occasioni» (etichetta Opta) |
| **copertura** | **1.826 / 16.111 = 11,33%** — ma è **una stagione al 100%**: 2017-18, tutte e 5 le leghe (380+380+380+306+380). Zero partite altrove |
| **legale** | **CC BY 4.0 verificata all'endpoint API**, non sulla pagina: `api.figshare.com/v2/articles/{7770599, 7770422, 7765196, 7765310}` → `license.name = "CC BY 4.0"` su tutti e quattro. **Titolare = Wyscout**, che ha rilasciato in proprio con data paper su *Nature Scientific Data*. Nessun ID Opta/Transfermarkt/Understat nel pacchetto: ID nativi Wyscout. **Non è una fonte avvelenata.** Nessun robots.txt in gioco: download diretto da API pubblica |
| **costo** | **0 €**. `events.zip` 77,3 MB + `matches.zip`. Tempo: **~1 giornata**, di cui il grosso è il **join** (nomi squadra Wyscout ≠ nomi football-data: precedente «Hellas Verona»→«Verona», `TEAM_ALIASES` ha già 234 voci) |
| **primo passo** | scaricare i due zip (10 min), aggregare gli eventi a giocatore-partita poi a squadra-partita (2 h), join agli snapshot verificando **1.826/1.826** e non 1.790 in silenzio (2-3 h), backtest walk-forward intra-stagione (1 h) |

### 🥈 2. Sportmonks — **declassata a `A_PAGAMENTO` dallo scettico. Il «58 € e 30 minuti a rischio zero» NON regge**

Il dossier originale la dava vincente. Sette rilievi ad alta gravità la ridimensionano:

| rilievo | prova |
|---|---|
| **«60 tipi per giocatore-partita» è letto dalla pagina sbagliata.** Quella è la tabella delle statistiche di **stagione** (14 descrizioni dicono testualmente «in a season»; nel tutorial ufficiale ogni oggetto `statistics` ha `season_id`, non `fixture_id`) | La pagina master ha una sezione intitolata **«Fixture-level, per player (`fixture.lineups.details`)»** e vi elenca **3 ID**: 5304 xG, 5305 xGoT, 9685 SP. Quanti dei 60 tornino da `lineups.details` **non è documentato**. Prova che l'evidenza era sbagliata in entrambe le direzioni: il dossier scriveva «tocchi NO» e «recuperi NO», mentre la tabella master ha **120 TOUCHES** e **27271 BALL_RECOVERY**. Il «7 su 9» non è affidabile né in difetto né in eccesso |
| **L'archivio è dichiarato incompleto dal fornitore stesso** | Doc seasons: *«our historical data will be integrated gradually. So, the historical data is not yet complete»*. ToS: *«Coverage gaps may exist across certain leagues or competitions. Sportmonks does not guarantee the completeness…»*. La pagina coverage (73 MB, 4.649 righe parsate) ha flag **a livello di lega**, senza granularità per stagione: non dice nulla sul 2017-18 |
| **Il test diagnostico «30 min, 0 €» è CIECO** | La finestra di 3 stagioni è una restrizione di **abbonamento**, non di esistenza: `/seasons` restituisce *«all the seasons available **within your subscription**»* e una fixture fuori piano dà **403 «Resource not in your plan»** — indistinguibile da «dato assente». Bisogna **prima comprare**, e i ToS dicono che le quote sono **non rimborsabili** |
| **L'xG individuale copre 2 stagioni su 9** | Doc coverage xG, verbatim: *«The xG data is available from the **2024/2025 season to date**»* → **3.504/16.111 = 21,7%**. E il prezzo giusto è **19 €/mese** (xG Basic su Starter), non 24 € (quello è il bundle con il Pressure Index, non richiesto) |
| **L'add-on storico è una scatola nera sul 67,4% del perimetro** | *«Historical data. Starting at €29 One-time fee»* — nessuna descrizione di **quali entità** sblocchi. Interrogata la doc ufficiale su scopo e criterio di prezzo: *«I cannot find information about this in the docs.»* Le stagioni **incluse** nei piani base (2023-24…2025-26) sono **5.256/16.111 = 32,6%**; le altre **10.855 (67,4%)** dipendono da quell'add-on |
| **Il join non è gratis, con nessuno dei nostri dati** | 153 nomi-club negli snapshot in forma football-data («Paris SG», «Ath Bilbao», «M'gladbach», «Nott'm Forest»); Sportmonks usa il nome esteso. E il fronte peggiore: `files/player_scores/` è su **ID Transfermarkt** (50.149 giocatori), Sportmonks usa i **propri** `player_id` → nessuna chiave comune |
| **«Nessun problema legale» è più forte dell'evidenza** | Doc: *«We collaborate with … **professional data partners**»* → il sui generis a monte resta di soggetti **non nominati**. ToS: *«you have to arrange **proof of intellectual property yourself**»* e *«We hold no responsibility for any losses»* — nessuna manleva. E la citazione che regge la tesi si ferma una frase prima di: *«Usage of material from Sportmonks is strictly for **personal and non-commercial use**»* |

**Verdetto rettificato:** resta **la miglior via a pagamento self-serve esistente**, ma va comprata **al buio** su due terzi del perimetro, non offre coordinate x,y, e il costo reale del nostro perimetro non è pubblico. Costo nominale: **48-77 € una tantum** (29 Starter + 29 «from» storico + eventuali 19 xG), **348-576 €/anno** in continuo.
**Primo passo onesto:** trial Starter, e **una sola domanda** — con `include=lineups.details` su una fixture **2023-24** (dentro il piano, quindi la risposta non è ambigua) contare **quanti dei 60 tipi tornano davvero**. Se ne tornano 3, la fonte è un'altra cosa da quella descritta.

### 🥉 3. StatsBomb open data — 1,43% lordo, licenza «research»

230 partite nel perimetro, **194 uniche** (36 di Liga 2017-18 sono già dentro Wyscout) = **1,20% aggiuntivo**. Sono **3 club soli**: Barcellona (Liga 2017/18-2020/21, 138), PSG (Ligue 1 2021/22-22/23, 58), Leverkusen (Bundesliga 2023/24, 34). **Serie A e Premier dentro la finestra: 0.**
È l'unica fonte aperta con **xG individuale nativo** (`shot.statsbomb_xg`) e su un sottoinsieme il **360** (freeze-frame dei 22).
**Licenza:** *non* è CC. È lo *StatsBomb Public Data User Agreement* (5 pagine): *«freely available for public use **for research projects and genuine interest in football analytics**»* + attribuzione **con logo** obbligatoria. Per un progetto il cui scopo dichiarato è prezzare mercati con soldi veri, è una riserva sostanziale, non una formalità.

### 4. Highlightly — piano B, profondità storica **non dichiarata**

Prezzi pubblici (gratis 100 req/g; PRO 9,49 $, ULTRA 20,99 $, MEGA 45,99 $/mese), dichiara «per-match box scores». **La profondità storica non è scritta da nessuna parte sulla pagina** — cioè manca proprio la risposta che serve. Da guardare solo se Sportmonks fallisce la verifica.

### 5. API-Football — **non verificabile in questo ambiente**

403 con challenge Cloudflare su sito, doc e `api-sports.io`; anche i 20 snapshot su web.archive.org (2020-03 → 2026-03) pesano 4-7 KB, cioè sono **tutti la pagina di challenge**. **Nessun prezzo e nessuna profondità storica confermati alla fonte.** Non aggirata e non si aggira. Non esclusa nel merito: **non conoscibile**.

### 6. DFL/Sportec (figshare, CC BY 4.0) — il massimo dettaglio, su 2 partite

Event XML **più** positional XML a 25 Hz per tutti i 22 giocatori e la palla. Il dataset è cresciuto da 2 a **7 partite**, ma parsando i 7 XML: **5 sono 2. Bundesliga** (tutte casalinghe del Fortuna Düsseldorf) → **contributo netto nel perimetro: +0**. Restano **2 partite**. Giocattolo. *Nota: la riserva DFL ex §44b(3) che chiuse bundesliga.com **non** si applica qui — lì la DFL vietava il TDM sul proprio sito, qui rilascia in proprio sotto CC BY.*

### ⛔ 7-10. Chiuse

| fonte | motivo | numero |
|---|---|---|
| **Kaggle `davidcariboo/player-scores` (Transfermarkt)** | **DECLASSATA A `CHIUSA_LEGALE` dallo scettico** — vedi §3 | il titolare vieta `ClaudeBot` **per nome** |
| **FotMob** | ToS: *«scraping … strictly prohibited»*, *«systematic, regular, or bulk retrieval … expressly forbidden»*; dato **Opta**; e l'archivio è **irraggiungibile**: l'URL identifica la **coppia di squadre**, la partita sta nel **frammento** `#matchId` che non arriva al server (Juventus-Napoli 22/04/2018 → il server rende `matchTimeUTC = 2026-11-01`) | copertura retrospettiva **0%** |
| **Understat tiro-per-tiro** | `robots.txt` = 26 byte: `User-agent: *` / `Disallow: /`. Zero `Allow`, zero eccezioni, invariato dal 13/07/2020. RFC 9309: `/` combacia con `/match/{id}`. Riserva TDM valida ex art. 4(3) | chiusa |
| **football-data.org** | **0 campi per giocatore**, anche con l'add-on «Stats Pro» a 30 €/mese (metriche di **squadra**). La parola *player* non compare nella pagina di copertura | 59-79 €/mese per zero |
| **Sportradar** | doc: *«Competitions will return a maximum of **three seasons** of data»* | 3 su 9 |
| **fbref / Sofascore** | Cloudflare / 403 anche sul robots.txt | già accertate |
| **Mirror Kaggle/HF di Understat** | **rettifica**: non «dichiarano licenze aperte indebite» — non dichiarano **nessuna** licenza. `mexwell` = *«Other»* con description vuota di licenza; `codytipton` = *«Unknown»*; `douglasbc` = nessuna. Tutti ammettono lo scrape | inutilizzabili |
| **SoccerNet / SkillCorner / PFF / Kaggle football-events** | fuori finestra (2014-17), contenuto cambiato (oggi 10 partite di A-League), nazionali, o scrape di bbc/espn | 0% del perimetro |

**Ecosistema aperto totale, ricontato oggi agli endpoint: 2.022/16.111 = 12,55%.** Identico a tre ricerche fa, **+0 partite**. Per superare la soglia di rilevanza del 20% servirebbero **1.200 partite in più**: raddoppiare l'intero ecosistema aperto mondiale.

---

## 3. Cosa possiamo avere DOMANI senza chiedere permesso a nessuno

**Questa sezione si è ridotta drasticamente rispetto a quanto sembrava, e va detto per primo.**

### ⚠️ Il blocco più grosso è caduto: Kaggle/Transfermarkt

Il dossier «dati già in casa» prometteva **~477.000 righe giocatore-partita** (minuti con minuto di entrata/uscita, ruolo per partita, modulo, motivo del cartellino, motivo della sostituzione, tipo di gol/assist, plus-minus, valore dell'XI). Lo scettico l'ha declassato a **`CHIUSA_LEGALE`** con tre rilievi **fatali** e otto ad alta gravità:

**Legale (fatale × 3):**
1. `curl -A ClaudeBot https://www.transfermarkt.com/robots.txt` → righe 27-31: **`User-agent: ClaudeBot` / `Disallow: /`**. Il titolare del dato vieta il nostro user-agent **per nome**, su tutto il sito. L'affermazione «non c'è alcuno scraping, nessun robots.txt è in gioco» è falsa: il robots.txt che conta è quello di **chi possiede il dato**, non del redistributore.
2. Il robots.txt dichiara `License: /license.xml`. Quel file (169 byte) contiene: `<content url="/"><license><prohibits type="usage">ai-all</prohibits></license></content>`. È una **riserva sull'USO a valle**, machine-readable, su tutto il sito. È il caso identico a bundesliga.com: **vince la riserva**.
3. `dcaribou` si autodescrive come *«built from Transfermarkt data»* con workflow `acquire-transfermarkt-scraper`, **senza** disclaimer né dichiarazione di permesso. Il CC0 copre la compilazione, non il sui generis del titolare. È la definizione di fonte avvelenata — il progetto ne ha già scartate 5 così.

**Qualità (alta):** il numero di punta «+0,00391 log-loss del valore XI, CONCLUSIVO» **è corrotto alla radice**. Il baseline «valore rosa» è costruito raggruppando su `current_club_id` = il club **odierno** del giocatore, non quello alla data → look-ahead diretto. Prova: la «rosa Juventus al 2018-01-01» così costruita ha **59 giocatori / 280 M€** con dentro Vlahović (arrivato nel 2022) e Iaquinta; la rosa vera è **28 giocatori / 585 M€**, sovrapposizione 12/28. Il 76,67% delle righe ha `current_club_name` ≠ club puntato da `current_club_id`. **Il repo lo sapeva già**: `scripts/build_stagione_anagrafica.py:210-215` documenta la trappola parola per parola («*una "rosa" così non è una rosa: è un finto pieno (R6)*»).

**Due conseguenze retroattive da portare all'utente, non da decidere qui:**
- `docs/DATI.md:369` e `files/README.md:26` descrivono questa fonte come **«CC0»** senza la riserva, ed è la fonte **UFFICIALE** di `home/away_squad_value` **dalla Fase 67**. La descrizione va corretta;
- il precedente della Premier League API e di bundesliga.com impone la stessa conclusione qui. Se il progetto vuole tenerla, è una **decisione consapevole di rischio**, non un fatto tecnico.

### Cosa resta davvero disponibile domani

| cosa | numeri misurati | stato |
|---|---|---|
| **Wyscout 2017-18** | **1.826 partite = 11,33%**, event log completo con x,y, da cui si derivano tocchi/passaggi/dribbling/contrasti/recuperi/falli per giocatore-partita | **CC BY 4.0 verificata all'endpoint.** Da scaricare: 77,3 MB, 10 minuti |
| **10.008 righe giocatore-stagione Understat già su disco** | Premier 4.819 + Liga 5.189, in `files/understat_*_bundle.json`, **già versionate**, con **8 campi che il parser butta**: xG, xA, npxG, npg, shots, key_passes, xGChain, xGBuildup. `grep xGChain\|key_passes\|xGBuildup` su `src/ scripts/ tests/` → **0 occorrenze** | dato **già in repo**, acquisito prima della chiusura della Fase 120. Costo: **1-2 ore** (una dict comprehension + un test + una voce in DATI.md) |
| **6.840 `match_id` Understat congelati** | 42,5% delle partite (Premier+Liga, id 7119-29537) | chiave pronta **se** un giorno esistesse una fonte tiro-per-tiro lecita. Per Serie A/Bundesliga/Ligue 1 (9.271 partite) i match_id **non ci sono** |
| **StatsBomb 194 partite uniche** | +1,20% | solo se si accetta la clausola «research projects» + logo |

**Tre avvertenze non negoziabili sulle 10.008 righe Understat:**
1. **R8, look-ahead severissimo**: è un aggregato di **fine stagione**. Usabile **solo** come feature ritardata (stagione precedente);
2. **2 leghe su 5**: zero righe per Serie A, Bundesliga, Ligue 1 — e non c'è via lecita per procurarle;
3. **grana STAGIONE**, non partita. È un surrogato dichiarato, non il dato dell'obiettivo.

---

## 4. Cosa resta comunque fuori portata

Detto senza attenuanti.

1. **Il log azione-per-azione con coordinate, fuori dal 2017-18.** L'ecosistema aperto copre **196 partite su 14.285 = 1,37%** delle otto stagioni non-2017-18, e sono **tre club** (Barcellona, PSG, Leverkusen).
2. **Le ultime due stagioni: 0 partite su 3.418.** Nessuna fonte aperta copre nulla dopo la Bundesliga 2023-24.
3. **Serie A e Premier dopo giugno 2018: 0 partite aperte.** Le due leghe di cui il progetto sa di più sono quelle su cui non c'è niente.
4. **Tocchi, passaggi, dribbling, contrasti, recuperi, intercetti per giocatore** su 8 stagioni su 9. Wyscout li dà su una stagione; Understat non li ha (è un log dei **soli tiri**); i portali consumer sono chiusi; Sportmonks li ha ma su un perimetro non documentato.
5. **xG e xA individuali storici.** Wyscout non li rilascia; Understat è chiuso; StatsBomb copre l'1,2%; Sportmonks parte dal **2024-25 (21,7%)**.
6. **«Grandi occasioni create/sprecate»**: è un'etichetta **Opta**. Non è un dato che si procura, è una voce da riformulare.
7. **Dati fisici/GPS**: FotMob li ha (distanza, sprint, top speed) ed è chiuso; Sportmonks dichiara esplicitamente *«No physical or tracking data … for any competition»*.
8. **Il 65,8% del nostro database (10.607 partite, 2017-18→2023-24)** non riceve **nulla di nuovo** da diretta.it, che era la candidata con la copertura potenzialmente migliore.

E un limite che non è di dato ma di misura, già pagato dal progetto: il tetto è **informativo**, non architetturale. Tutti i dati interni esplorati (xG, npxG, PPDA, deep, valore-rosa, assenze, riposo, forma) sono risultati **ridondanti o rumore**; il mercato di chiusura **ingloba** il modello (α\*=0 su 1X2 e GG/NG); la config ufficiale dà **ROI −15,8% su 866 scommesse**. Nulla in questa ricerca sposta quei numeri.

---

## 5. La raccomandazione unica

> **Scaricare il Wyscout/Pappalardo 2017-18 (1.826 partite, CC BY 4.0, 77,3 MB, 0 €) e usarlo come go/no-go su una domanda sola: «le statistiche per giocatore aggiungono qualcosa che i dati di squadra non hanno già?»**

**Perché questa e non altro, con i numeri:**

| criterio | Wyscout | Sportmonks | diretta.it |
|---|---:|---:|---:|
| costo | **0 €** | 48-77 € al buio, non rimborsabili | 36-90 h + illecito |
| stato legale | **CC BY 4.0 verificata all'endpoint, titolare che rilascia in proprio** | contratto ok, ma nessuna garanzia di titolarità e nessuna manleva | 4 divieti contrattuali |
| coordinate x,y | **sì, ogni azione** | no | no |
| copertura del perimetro | 11,33%, **una stagione al 100%** | 32,6% certo / 67,4% scatola nera | 12,7-14,7% |
| l'incognita chiave è risolvibile prima di spendere? | **sì, è già tutto lì** | **no**: il 403 non distingue «assente» da «non nel piano» | irrilevante |

**Perché una stagione sola basta *per questa domanda*** (e non violiamo il §1.7):
- **1.826 partite** contro le **574** che la Fase 98 ha misurato servire per l'80% di potenza sull'1X2 — un fattore **3,2×**;
- si può fare **walk-forward dentro la stagione** (andata → ritorno, ~900 partite di test out-of-sample);
- e soprattutto **l'esito non può essere «adottiamo»**. Può essere solo:
  - **segnale nullo** → il fronte «dati per giocatore» si chiude, **gratis**, e nessuna sessione futura ci rispende tempo. È il risultato più probabile (tutti i dati interni testati finora sono caduti così) e per il §1.4 vale quanto uno positivo;
  - **segnale presente** → allora, **e solo allora**, ha senso comprare Sportmonks, con in mano una stima quantitativa di quanto vale e un'ipotesi dichiarata prima.

**Il costo dell'alternativa, quantificato:** senza questo test, la decisione su Sportmonks si prende al buio su **10.855 partite (67,4%)** coperte da un add-on di cui la documentazione ufficiale, interrogata direttamente, risponde *«I cannot find information about this in the docs»*. Spendere 48-77 € è irrilevante; spenderli **senza ipotesi** e poi costruirci sopra una feature è il modo in cui si accumula debito, non evidenza.

**Due avvertenze da scrivere prima di iniziare, non dopo:**
1. il risultato varrebbe **2017-18**, un'epoca in cui — misurato alle Fasi 75/81 — il θ del router era diverso da oggi. Un segnale trovato lì **non è automaticamente vivo nel 2026**;
2. il rischio vero non è il download (10 minuti) né l'aggregazione (2 ore): è il **join** (2-3 ore). Va verificato esplicitamente che copra **1.826/1.826** e non 1.790 in silenzio — precedente «Hellas Verona»→«Verona», `TEAM_ALIASES` ha già 234 voci.

**Passo zero, prima ancora (20 minuti, e vale più di quanto costa):** correggere nel repo i **motivi** con cui tre fonti sono state chiuse o descritte, perché una motivazione sbagliata è precisamente ciò che una sessione futura riapre:
- **diretta.it/Flashscore** → da «vincolo tecnico, ambiente senza browser» a **«CHIUSA PER LICENZA, non per rete»**, nel gruppo di Premier League API e bundesliga.com. Con la condizione di riapertura corretta: non «un browser reale», ma «un accordo scritto con Livesport, e comunque subordinato ai diritti Opta»;
- **mirror Understat** → da «dichiarano licenze aperte che non possono concedere» a **«non dichiarano nessuna licenza»** (verificato via API Kaggle: `Other` con description vuota, `Unknown`, nessuna);
- **Transfermarkt/dcaribou** → aggiungere in `docs/DATI.md:369` e `files/README.md:26` che il titolare **vieta `ClaudeBot` per nome** e pubblica una riserva `ai-all` machine-readable, e che la fonte è già usata per `squad_value` **dalla Fase 67**. Questa è una decisione per l'utente, non per la sessione.

---

**Nota di metodo su questa ricerca.** Sulla fonte proposta dall'utente non è stata raccolta una sola riga di dati: ~25 pagine aperte a ritmo umano per il censimento, 6 fetch legali/di indice per l'analisi contrattuale, nessuna protezione incontrata né aggirata (il sito ha risposto **200** a ogni richiesta — è esattamente il caso in cui la tentazione è massima e la risposta è comunque no). Un fatto operativo nuovo da annotare in `docs/MANUALE_SOPRAVVIVENZA.md`: **Chromium+Playwright funziona in HTTPS in questo ambiente**, con `pip install playwright`, `executable_path=/opt/pw-browsers/chromium-*` e **`--ssl-version-max=tls1.2`** (il proxy resetta il TLS 1.3 di Chromium su **qualunque** host — verificato su example.com e wikipedia.org). L'annotazione contraria in archivio è superata. Non cambia nulla per diretta.it: il vincolo lì è legale.