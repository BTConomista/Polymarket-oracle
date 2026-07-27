# Audit delle ultime 20 fasi (80 → 100) — il verbale

> **Cos'è.** Il controllo completo delle Fasi 80-100 e dell'**integrazione del
> lavoro dal branch di cantiere a `main`**, richiesto dall'utente: cercare
> errori, calcoli sbagliati, cose importate male, lavoro lasciato a metà e cose
> scritte in un documento e non nell'altro. È il quinto audit del progetto
> (dopo le Fasi 84, 86, 90 e 92) e il primo che copre un'**integrazione**.
>
> **Come.** 13 fronti di ricerca in parallelo (le fasi del diario in sei
> gruppi, README, PANCHINA, gli altri documenti, il codice, i dati, gli script,
> il lavoro incompiuto), ognuno seguito da un **verificatore avversariale** il
> cui compito era *smontare* i rilievi, non confermarli — più le verifiche
> dirette rifatte a mano su tutto ciò che ha portato a una modifica.
>
> **Esito in una riga:** **198 rilievi**, di cui **16 gravi**; nessun errore nei
> *modelli*, tutti gli errori stanno nel **passaggio dal cantiere al progetto** e
> nella **propagazione delle conclusioni ritirate**. Più un fatto che nessun
> Più un rilievo che ho scritto e poi **ritirato** — «`main` non ha ricevuto
> l'integrazione» — perché si basava su un ref locale vecchio invece che sulla
> fonte: la smentita, e il perché è istruttiva, sono al punto 7.

---

## 1 · Gli otto fatti che contano

**1. L'integrazione ha portato in `main` 32 script che non partivano.** Spostati
da `cantiere/scripts/` a `scripts/`, hanno conservato `ROOT =
Path(__file__).resolve().parents[2]`: giusto quando il file stava un livello più
in basso, ma da `scripts/` punta a `/home/user`, **fuori dal repository**. 24 di
essi morivano su `import src`; tutti e 32 leggevano e scrivevano dentro
`cantiere/`, cartella cancellata dallo stesso commit. Conseguenza vera, non
teorica: la **Fase 100 non era riproducibile** — né l'audit dei dati, né le
correzioni dichiarate (regola R3), né gli snapshot delle due leghe nuove. E
`fetch_sources.py` avrebbe scaricato 135 MB in `/home/user/cantiere/`, un albero
fantasma fuori da git. ✅ **Corretto e verificato**: tutti e 32 partono, e
`applica_correzioni.py --dry-run` ripercorre le 31 correzioni dichiarate
confermando che sono già applicate (l'idempotenza R3 è tornata dimostrabile).

**2. `build_database.py --league <lega>` distruggeva lo snapshot della Serie A.**
Ogni ramo dello script leggeva e scriveva `database.SNAPSHOT_PATH`, cablato su
`data/serie_a_matches.csv`, mentre `--league` veniva onorato solo dal
*download*. `python scripts/build_database.py --league bundesliga --refresh`
avrebbe scaricato la Bundesliga e l'avrebbe scritta **sopra** uno snapshot
congelato e versionato. Il bug era latente da prima delle 20 fasi in esame, ma
è diventato pericoloso proprio con l'ingresso delle leghe nuove.
✅ **Corretto**: ogni lettura/scrittura passa da `database.snapshot_path(lega)`,
e i rami `--fixtures`/`--refresh` sono diventati per-lega invece che
solo-Serie-A. Per la Serie A il comportamento è identico a prima.

**3. Il denominatore dell'audit dei dati era sbagliato: 15.788 invece di
16.111.** Il numero non corrisponde a **nessun** universo del progetto: non è il
totale delle 5 leghe (16.111), non è la copertura Understat (16.110), non è
nessun sottoinsieme filtrato (verificato provando xG, quote, apertura, tiri,
valore rosa e l'esclusione di ogni singola stagione). Gli artefatti **dell'audit
stesso** (`docs/audit_5_leghe/numeri/audit_*.json`, campo `n_rows`) sommano a
16.111. Era il numero-titolo di tutta la Fase 100, ripetuto in 11 punti fra
diario, README, report e patch. ✅ **Corretto** ovunque; il claim sostanziale
(«0 differenze contro la fonte») non cambia — cambia solo su quante partite.

**4. «8 anomalie reali, tutte nella fonte» non regge sui suoi stessi report.**
Delle otto numerate, una (§4.4, Bielefeld-Leverkusen) è un **falso positivo
ritirato** — l'xG a 0.00 era un autogol — e un'altra (§4.6, ordine delle colonne
fra snapshot) è un difetto **nostro**, non della fonte. Il report 01 lo dice già
in testa («7 anomalie reali») e si contraddice 77 righe più sotto nel titolo del
§4. ✅ **Corretto**: 7 reali = 6 nella fonte + 1 nostra, più una ritirata.

**5. Le conclusioni ritirate non erano state propagate.** È il difetto più
diffuso dell'intero audit e tocca cinque catene:
- la **diagnosi rovesciata dalla Fase 92** («il gap vive nel pareggio») era
  ancora affermata in tre punti del README, senza marcatura, in contraddizione
  con la correzione scritta 300 righe più su nello stesso file;
- il **lead della Fase 98** (correzione di livello dei conteggi) restava
  «✅ leva nuova» nella tabella del README, benché la riga successiva lo
  smentisca;
- la **premessa GG/NG** caduta con la Fase 100 sopravviveva come vigente in
  `lavoro_aperto.md`, `newseason.md`, `docs/PISTE.md` e `STUDIO_PREMIER_LIGA.md`;
- la **rete «bloccata»** era ancora la premessa operativa di due documenti di
  pianificazione, con tabelle di 403 — mentre la Fase 100 ha scaricato due leghe
  intere direttamente dalla fonte;
- il **residuo M2** («rendere per-lega il θ del router») era elencato fra i
  prossimi passi del `CLAUDE.md`, ma era stato **chiuso** dalla Fase 92-bis.
✅ **Corretto** in tutti e cinque i casi, marcando il testo storico invece di
riscriverlo (come si era fatto, correttamente, per la Fase 89).

**6. Esiste una fase fantasma: la «Fase 92-bis».** Ha cambiato codice di
produzione (`MARKET_ENGINE` per-lega in `src/config.py`, il suo consumo in
`predict.py`, il bootstrap a grappoli che ha **tolto la conclusività all'IC del
top-4 della Fase 91**), ma non ha voce nel DIARIO, riga nel README né stato in
PANCHINA: la stringa «92-bis» non compariva in nessun `.md` del repo. Ne segue
un errore concreto: la Fase 91 e il README continuavano a dichiarare «entrambi
conclusivi» su un intervallo che, ricalcolato, **include lo zero**.
✅ **Corretto**: la Fase 92-bis ha ora la sua voce nel diario e la sua riga nel
registro, e la Fase 91 porta il blocco di rettifica coi numeri dell'artefatto.

**7. ~~`main` non ha mai ricevuto l'integrazione.~~ RILIEVO RITIRATO — ed è
istruttivo che sia successo proprio qui.** Al momento di committare avevo letto
`origin/main` **dal ref locale**, fermo a `644795f` (Fasi 87-88, 24 luglio),
e ne avevo concluso che le 43 commit dell'integrazione vivessero solo sul branch
di sessione. Interrogando GitHub, `main` è invece a **`6c9b377` — «Integrazione
3/3c», 26 luglio 14:32**: l'integrazione c'è, e la regola §3-bis è stata
rispettata. Il ref locale era semplicemente vecchio di un `fetch`.

È esattamente l'errore che questo audit trova negli altri: **una copia locale
scambiata per la fonte**. La lezione della Fase 100 («verificare contro la
fonte-madre, non contro sé stessi») vale anche per lo stato di un branch, e il
costo di non applicarla è stato un rilievo grave inventato di sana pianta.
Resta agli atti, con la sua smentita, per la regola §1.4 — e perché la prossima
sessione non lo ri-trovi.

**Lo stato vero dei branch (27 luglio, da GitHub):** `main` = `6c9b377`
(Fase 100); `claude/audit-ultimi-20-step-gzwro2` = questa fase, **1 commit
avanti e 0 indietro** rispetto a main (fast-forward pulito);
`claude/premier-liga-analysis-nqwa5c` = `8636258` (Fase 82) e
`claude/verify-data-import-leagues-468euv` = `4711d41` (cantiere della Fase 100)
sono **interamente contenuti in `main`** (0 commit avanti): confluiti, quindi
cancellabili senza perdere nulla.

**8. `predict.py` applicava la φ35 dove è stata misurata dannosa.** Il motore
per-lega copriva il θ ma non la φ: su Premier e Liga il path DC riceveva
comunque `phi0`/`kappa` dal fit, spostando il pareggio di **+1.0pp** nella
direzione che la Fase 79 misura come sbagliata — lo stesso difetto che la Fase
92-bis dichiarava di aver corretto sul path market-implied. E l'opzione
`--no-draw-balance` era dichiarata nel parser e **non veniva mai letta**: due
esecuzioni con e senza il flag davano output identici byte per byte.
✅ **Corretti entrambi**, con verifica prima/dopo.

---

## 2 · Il quadro numerico

| | rilievi |
|---|--:|
| totale | **198** |
| gravi (🔴) | 16 |
| medi (🟠) | 88 |
| minori (🟡) | 94 |
| confermati dalla verifica avversariale | 108 |
| ridimensionati (esistono ma meno gravi) | 35 |
| **smontati** (rilievo sbagliato) | 2 |
| non contro-verificati (il verificatore si è fermato per limite di sessione) | 51 |

I tre fronti rimasti senza contro-verifica sono *script migrati*, *integrità dei
dati* e *lavoro incompiuto*: i loro rilievi gravi sono però stati **riprodotti a
mano** in questa sessione prima di correggerli (i 32 script, il bug di
`build_database.py`, il denominatore, il registro delle correzioni), e sono
segnalati uno per uno nell'appendice.

**Dove NON sono stati trovati errori** — vale la pena dirlo, perché è il grosso
del lavoro: nessun errore nei **modelli** (le formule del blocco 📐 corrispondono
al codice), nessuna differenza fra snapshot e fonte, nessun problema nei
conteggi delle partite (16.111 = 3.420×3 + 2.754 + 3.097, con le irregolarità
vere: Bundesliga 306/stagione, Ligue 1 279 nel 2019-20 per il COVID e 306 dalla
riforma 2023-24), le 6 celle La Liga svuotate dal guard sono davvero `NaN`, le
regole di spareggio per-lega corrispondono alle fonti ufficiali citate, e i 197
test sono verdi.

---

## 3 · Cosa è stato corretto in questa sessione

**Codice**

| # | correzione | file |
|--:|---|---|
| 1 | `ROOT` da `parents[2]` a `parents[1]` + tutti i percorsi `cantiere/` ri-puntati alle destinazioni reali (32 script); smoke test su ognuno | `scripts/*.py` |
| 2 | `--league` onorato in lettura **e scrittura**; rami `--fixtures`/`--refresh` per-lega | `scripts/build_database.py` |
| 3 | φ35 sul path DC presa dal motore per-lega; `--no-draw-balance` finalmente attivo | `scripts/predict.py` |
| 4 | `MARKET_ENGINE` completato con Bundesliga e Ligue 1 (stato **misurato**, non default implicito) | `src/config.py` |
| 5 | tre test nuovi: copertura delle mappe per-lega, e due che **distinguono** le tuple di spareggio di Bundesliga e Ligue 1 (prima uno scambio fra le due passava la suite) | `tests/` |
| 6 | `data/fonti/` in `.gitignore` (ci scrive `fetch_sources.py`) | `.gitignore` |

**Numeri**

| # | correzione | dove |
|--:|---|---|
| 7 | 15.788 → **16.111** (e 15.787/15.788 → 16.109/16.110 appaiate) | 11 punti in DIARIO, README, report 01, report 08, patch, `audit_anomalie.py` |
| 8 | «8 anomalie, tutte nella fonte» → **7 (6 fonte + 1 nostra), +1 ritirata** | DIARIO, README, report 01, indice |
| 9 | «6 celle su 8 peggiorano» → **5** (lo diceva già la tabella della stessa fase) | DIARIO, README, PISTE, PANCHINA, CLAUDE, lavoro_aperto |
| 10 | griglia φ0×κ: «31 combo» → **37** (`[(0,0)] + 6×6`) | DIARIO, README, docstring dello script |
| 11 | GG/NG: i numeri sono su **5.337 partite (2017-20)**, non 3.652 (che è la finestra 2017-19 della caccia O/U) | CLAUDE.md §1.8 |
| 12 | Fase 91: rettifica completa coi numeri dell'artefatto — «entrambi conclusivi» **non regge**, l'IC a grappoli del top-4 è [−0.0006, +0.0522] e a reggere è il test dei segni (19/24, p=0.0066) | DIARIO, README |
| 13 | `_run_fase96_relegation_market.py` → `_run_fase97_...` (script inesistente citato nel blocco «riproducibilità») | DIARIO ×2 |
| 14 | manifest delle fonti: «l'impronta di ognuno» → **90 file su 141** (fuori: 84 `.txt` openfootball e 16 `.html` Transfermarkt) | indice dell'audit |

**Documenti**

| # | correzione | dove |
|--:|---|---|
| 15 | 21 link markdown rotti + tutti i percorsi `cantiere/` nei report | `docs/audit_5_leghe/*` |
| 16 | tabella di corrispondenza vecchio→nuovo **ripristinata** (una sostituzione di massa l'aveva resa «X → X») e blocco «come rifare tutto» reso eseguibile, con l'avvertenza che il passo 1 non è opzionale | `docs/audit_5_leghe/00_indice.md` |
| 17 | la patch del guard non dice più «Non applicata» nel corpo di un file chiamato `...APPLICATA.md` | `patch_guard_overround_APPLICATA.md` |
| 18 | diagnosi della Fase 92 marcata come rovesciata nei 3 punti superstiti; lead della Fase 98 ritirato in tabella; roadmap «In corso» → chiusa (erano 4 esperimenti finiti da oltre 60 fasi) | `README.md` |
| 19 | piste **16** (GG/NG) e **19** (O/U 2017-19) chiuse con l'esito e il **motivo del non-inserimento**, perché la prossima sessione non ci riprovi | `docs/PISTE.md` |
| 20 | premessa GG/NG, tabelle di rete superate, «aggiungere le leghe nuove» → fatto, caselle vuote 24 → **138** | `lavoro_aperto.md`, `newseason.md`, `CLAUDE.md` |
| 21 | Tier 2 e Tier 3 non sono più «in futuro» (Fasi 88/96/98); M2 dichiarato **chiuso** dalla Fase 92-bis; mappa del repo con `docs/audit_5_leghe/` e la caccia O/U chiusa | `CLAUDE.md` |
| 22 | stima O/U: 5 leghe, fit su **12.457** partite, MAE **del regime d'uso** (~0.014) accanto a quello di interpolazione (~0.012); `squad_value` stimato: **0 righe**, non 13 | `data/estimates/README.md` |
| 23 | voce di diario della **Fase 92-bis** (mancava del tutto) e di questa **Fase 101**, con le righe corrispondenti nel registro del README | `docs/DIARIO.md`, `README.md` |

---

## 4 · Cosa resta aperto (in ordine di valore)

Non è stato corretto qui perché richiede una **decisione** o un **ricalcolo**,
non una riscrittura. Ogni voce ha il suo rilievo nell'appendice.

1. **Il numero-bandiera del progetto va rimisurato.** Dopo il fix del prior
   della Fase 92 il gap 1X2 Serie A risulta **+0.0167 / 0.9799** contro il
   **+0.0165 / 0.9797** dichiarato in 17 punti fra README e `CLAUDE.md`. La
   differenza è irrilevante nel merito e rilevante nel metodo: è il numero più
   citato del repo. Serve rieseguire il walk-forward ufficiale e allineare tutto
   in un colpo solo. *(`F92-headline-0.0165-non-riproducibile`)*
2. **La COM-Poisson della Fase 85 non è una famiglia diversa dalla
   double-Poisson: è la stessa, riparametrizzata** (`dp(θ) ≡ COM-Poisson(ν=θ)`
   mean-matched). Il confronto presentato come «conferma indipendente» è la dp
   contro sé stessa. Va riscritta la sezione, e con essa le voci derivate in
   README, PANCHINA, PISTE e GLOSSARIO. *(`F85-com-poisson-e-la-stessa-dp`)*
3. **«α\*=0 su un mercato nuovo» (Fase 88) non è mai stato calcolato.** Rifatto
   sugli stessi 7.437 casi dà α\*≈1.08 con IC che **esclude** lo zero. La
   conclusione onesta è «pareggio in Brier col mercato sharp», che è comunque il
   risultato interessante. *(`F88-alpha-star-zero-mai-testato`)*
4. **Due affermazioni della Fase 93 vanno declassate**: «siamo meglio calibrati
   del mercato» ha IC a cavallo dello zero e cambia segno col numero di fasce; e
   le quote «−4% calibrazione / +104% informazione» sono normalizzate su 0.0094,
   non sul deficit di 0.0215 che la frase nomina (il 56% resta non attribuito).
   *(`F93-meglio-calibrati-senza-intervallo`, `F93-quote-104-percento`)*
5. **`docs/DATI.md` non è più il catalogo di tutti i dati**: mancano
   `data/ricerca_esterna/` (86 file, incluse le quote 1xBet), il registro delle
   correzioni, i due calendari di club nuovi e due stime; il censimento dei
   buchi è pre-guard (7.353 contro 7.359) e la tabella di dettaglio somma 47
   celle su 55. *(`F9-dati-header-e-omissioni`, `F12-02-censimento-buchi-7353`,
   `F13-10-DATI-catalogo-incompleto`)*
6. **La PANCHINA ha 18 celle `⬜` che l'audit integrato ha già misurato**, quattro
   leve misurate senza riga, la sezione «I titolari» ferma a 3 leghe, e usa
   «CI<0» col significato opposto in celle diverse. *(fronte PANCHINA)*
7. **Il registro `runs.jsonl` non copre le fasi recenti**: 89-bis, 90, 93, 96 e
   100 non hanno né un run né la dichiarazione «nessun run». Per la Fase 100 la
   fonte grezza è di fatto `docs/audit_5_leghe/numeri/`: va detto, o vanno
   registrati i run a posteriori. *(`F100-runs-jsonl`, `F13-14-registro-run-mancanti`)*
8. **Sei celle con verdetto «USARE IL DATO REALE»** in
   `data/estimates/celle_residue.csv` non sono state né inserite né dichiarate:
   la decisione vive solo dentro un CSV. E il registro stesso è stantio (3 righe
   La Liga già svuotate dal guard, un verdetto logicamente inapplicabile).
   *(`F13-11-celle-residue-caso-A-non-eseguito`, `F12-09-celle-residue-stale`)*
9. **Riproducibilità della Fase 97**: «il confronto è rifacibile identico» è
   falso finché `_run_fase97_relegation_market.py` legge sempre l'**ultimo**
   snapshot; basta un `--date`. *(`F97-riproducibilita-data`)*
10. **Il σ differenziato della Fase 94 (0.30/0.16) non è ri-derivabile** da nulla
    di committato: lo script accetta solo uno scalare e non calcola IC.
    *(`F94-sigma-differenziato-non-riproducibile`)*
11. **`BASE_URL` punta ancora al mirror morto** (404) mentre la fonte ufficiale
    risponde 200: è una scelta legittima solo se dichiarata, oggi il commento
    dice il contrario di quello che il progetto ha verificato.
    *(`F10-base-url-mirror-morto`)*
12. **`recupero_squad_value_tm.py` non riproduce più i suoi numeri, ed è
    corretto così.** Rieseguendolo oggi la «scala misurata» fra Transfermarkt e
    player-scores passa da mediana **1.131 su 13 club** a **1.038 su 18**, con lo
    scarto mediano da 14.8% a 8.6%: il confronto è diventato **circolare**,
    perché le 16 celle recuperate da Transfermarkt sono ormai *dentro* lo
    snapshot che fa da termine di paragone. L'artefatto congelato in
    `docs/audit_5_leghe/numeri/recupero_squad_value_tm.json` è quello valido
    (misurato prima dell'applicazione) ed è stato **ripristinato** dopo che un
    agente lo aveva sovrascritto. Serve che lo script escluda le righe di
    provenienza Transfermarkt dal confronto, o che dichiari di non essere
    ri-eseguibile dopo l'applicazione. *(rilievo emerso durante questa sessione,
    non presente nei 198)*
13. Documenti da rinfrescare: `PLAYBOOK_NUOVA_LEGA.md` (non ha incorporato
    l'onboarding che pure lo ha usato), `STUDIO_PREMIER_LIGA.md` (header fermo
    alla Fase 79), `MANUALE_SOPRAVVIVENZA.md` (header alla Fase 70),
    `GLOSSARIO.md` (mancano i termini delle ultime fasi), e le sezioni
    «Struttura»/«Archivio dati» del README, ancora a 3 leghe.

---

## 5 · Le due lezioni di metodo

**Un'integrazione va eseguita, non solo spostata.** Il commit di integrazione
dichiarava correttamente ogni spostamento e ne pubblicava perfino la tabella di
corrispondenza — ma nessuno ha **lanciato** uno degli script spostati, e il
difetto era di una riga (`parents[2]`). Il costo non è stato estetico: la fase
più grande del progetto è rimasta non riproducibile fino a oggi. Regola pratica
per la prossima volta: dopo ogni spostamento di file eseguibili, uno **smoke
test** che li importi tutti — che ora esiste come procedura in questa sessione e
va reso un test.

**Una conclusione ritirata deve essere inseguita, non solo corretta dov'è
nata.** Cinque catene su cinque erano state corrette nel punto d'origine e
lasciate vive altrove; e il caso peggiore — la Fase 92-bis — è nato da una fase
che non è mai stata scritta, quindi la sua correzione non poteva propagarsi. La
checklist §2 del `CLAUDE.md` esiste esattamente per questo: **la fase non è
chiusa finché non è scritta ovunque**, anche quando è una fase «-bis» che tocca
solo il tooling.

---

## Appendice — tutti i 198 rilievi

Legenda: 🔴 grave · 🟠 medio · 🟡 minore. «**confermato**» = riprodotto dal
verificatore avversariale; «ridimensionato» = il difetto esiste ma è meno grave
di come era descritto; «~~smontato~~» = il rilievo era sbagliato (tenuto per
memoria, così non viene ri-trovato); «*non contro-verificato*» = il fronte si è
fermato per limite di sessione, il rilievo è del solo auditor salvo dove questa
sessione lo ha riprodotto a mano.

### Fasi 80-83-bis  ·  14 rilievi
**🟠 `F83bis-residuo-chiuso-non-propagato` — Il residuo "M2 per-lega" della Fase 83-bis è stato chiuso (commit 1ad6c30, "Fase 92-bis") ma 8 punti nei documenti lo dichiarano ancora aperto**  
*incoerenza-doc · media · **confermato***

- **Dove**: CLAUDE.md:507-508; README.md:237; README.md:199; experiments/prospettico_2026_27.md:34-39; experiments/prospettico_2026_27.md:75; docs/PANCHINA.md:117,162,163; docs/STUDIO_PREMIER_LIGA.md:254; docs/DIARIO.md:8251
- **Atteso**: Dopo l'introduzione di MARKET_ENGINE/market_engine() in src/config.py:124-148 e del suo uso in scripts/predict.py:124-133, il θ (e φ0/κ/sharpen_1x2) del path market-implied È per-lega (Premier e Liga = motore liscio, dp_theta=None). I documenti dovrebbero dirlo, e le condizioni di promozione della PANCHINA formulate come «quando predict.py diventa per-lega» andrebbero riformulate.
- **Trovato**: CLAUDE.md §6: «resta da rendere per-lega il θ del router nel path market-implied (M2 Premier con θ neutro)». README riga 83-bis: «resta per-contesto il θ del router nel M2». README riga 52-bis: «predict.py usa θ=1.225 (mercato) / 1.138 (DC)» (vero solo per la Serie A). prospettico_2026_27.md: «per Premier il M2 andrà prodotto con dp_theta neutro (nota nel protocollo §3)» — ora avviene da solo. PANCHINA 162/163: condizione di promozione «tool non ancora per-lega» / «tool non per-lega», ormai falsa.
- **Come è stato accertato**: Lettura di scripts/predict.py (righe 124-133: `eng = market_engine(args.league)` … `dp_theta=eng["dp_theta"]`) e src/config.py:124-148 (MARKET_ENGINE: premier_league e la_liga con dp_theta=None). `git log -S MARKET_ENGINE -- src/config.py` → 1ad6c30 «Fase 92-bis — Chiusura dei fix dell'audit: predict.py per-lega…». Esecuzione: `python scripts/predict.py --league premier_league Newcastle Liverpool` stampa «[motore LISCIO per premier_league…]». grep delle 8 occorrenze sopra.
- **Correzione**: Aggiornare le 8 righe: CLAUDE.md §6 → «predict.py è per-lega su ENTRAMBI i modelli (Fase 92-bis, src/config.MARKET_ENGINE)»; README 237/199 → nota che θ/φ0/κ/sharpen valgono solo per la Serie A; prospettico_2026_27.md → il M2 Premier esce già liscio; PANCHINA 117/162/163 → sostituire la condizione «tool per-lega» (soddisfatta) con quella residua (conferma su stagioni nuove).

**🟠 `F92bis-fase-non-documentata` — La «Fase 92-bis» ha cambiato codice di produzione ma non ha voce nel DIARIO, riga nel README né aggiornamento in PANCHINA (violazione CLAUDE.md §2)**  
*omissione · media · **confermato***

- **Dove**: docs/DIARIO.md (nessuna sezione «## Fase 92-bis»); README.md (nessuna riga 92-bis fra le righe 248 e 249); docs/PANCHINA.md; commit 1ad6c30
- **Atteso**: Ogni fase significativa: riga nel «Registro completo dei risultati» del README, voce nel DIARIO col blocco 📐, stato in PANCHINA (CLAUDE.md §2). Il commit 1ad6c30 quantifica anche un effetto misurato («in Premier costava +0.0025 di log-loss 1X2 contro il motore liscio e +2.7pp di pareggio previsto»), quindi è un risultato, non solo tooling.
- **Trovato**: `grep -rn "92-bis" docs/*.md README.md CLAUDE.md lavoro_aperto.md` non restituisce nulla; `grep -rn "market_engine\|MARKET_ENGINE" --include=*.md .` non restituisce nulla. Il numero +0.0025/+2.7pp vive solo nel messaggio di commit e nel commento di src/config.py:110-115, non nel registro né nel DIARIO.
- **Come è stato accertato**: grep sui .md (0 hit) + `git log --oneline -- src/config.py` (1ad6c30) + `git show --stat 1ad6c30`. In README le righe passano da 92 (riga 248) a 93 (riga 249) senza 92-bis.
- **Correzione**: Aggiungere la voce «Fase 92-bis» al DIARIO (con blocco 📐 sul perché φ0=0/θ=None per PL/Liga e i numeri +0.0025 / +2.7pp, ri-derivabili), la riga corrispondente al README e l'aggiornamento delle celle PANCHINA toccate; se il numero +0.0025 non è nel registro, registrarlo via experiment_log.append_run o dichiararlo non ri-derivabile (§2-bis punto 3).

**🟠 `F3-predict-phi35-path-DC` — predict.py applica la φ35 al Modello 1 (path DC) anche su Premier e Liga, contro la conclusione operativa della Fase 79 e contro il commento immediatamente sopra la riga**  
*bug-codice · media · **confermato***

- **Dove**: scripts/predict.py:113-126; conclusione violata: docs/DIARIO.md:8159-8161 (Fase 79 §4)
- **Atteso**: Fase 79 §4: «su PL/Liga il listino si prezza col market-implied liscio (niente θ, niente dp_lvl, niente φ35 sul path DC)»; il commento a predict.py:121-123 ribadisce «In Premier il motore LISCIO e' l'ottimo misurato (Fase 81) e la φ35 peggiora (Fase 79)». Il path DC dovrebbe quindi passare phi0=0 dove eng["phi0"]==0.
- **Trovato**: Riga 125-126: `d_dc = mi.price_markets(lam_dc, mu_dc, rho=m.rho, phi0=m.draw_phi0, kappa=m.draw_kappa, dp_theta=eng["dp_theta_dc"])` — solo il dp_theta è per-lega; φ0/κ vengono dal fit del DC (Premier φ0=0.108, κ=5.000; Liga φ0=0.390, κ=2.717) e la φ35 viene applicata comunque.
- **Come è stato accertato**: Esecuzione `python scripts/predict.py --league premier_league Newcastle Liverpool` → «φ35: φ0=0.108, κ=5.000», λ=1.56 μ=1.69. Ricalcolo diretto: mi.price_markets(1.56,1.69,rho=-0.06,phi0=0.108,kappa=5.0) vs phi0=0 → pareggio 0.2543 contro 0.2440 (**+1.03pp**), casa −0.48pp, ospite −0.55pp. È la stessa direzione che la Fase 79 misura come sbagliata in Premier (Δ +0.0006, P 7%) e lo stesso ordine del danno (+2.7pp) che il commit 1ad6c30 dichiarava di correggere sul M2.
- **Correzione**: Passare la φ dal motore per-lega anche al path DC, es. `phi0=(m.draw_phi0 if eng["phi0"] else 0.0), kappa=(m.draw_kappa if eng["phi0"] else 0.0)`, oppure non fittare draw_balance quando eng["phi0"]==0; aggiungere un test che su premier_league il listino M1 coincida con quello liscio.

**🟡 `F4-flag-morto-predict` — L'opzione `--no-draw-balance` di predict.py è dichiarata ma non fa nulla**  
*bug-codice · bassa · **confermato***

- **Dove**: scripts/predict.py:87-89 (definizione), main() (mai letta)
- **Atteso**: Passando `--no-draw-balance` il tool non dovrebbe mostrare/applicare la variante φ(|λ−μ|) della Fase 35.
- **Trovato**: `args.no_draw_balance` non compare mai nel corpo di main(); il modello è sempre costruito con `draw_balance=True` (riga 114) e la φ è sempre applicata (riga 125).
- **Come è stato accertato**: `grep -n "no_draw_balance\|draw_balance" scripts/predict.py` → solo la definizione dell'argomento e `draw_balance=True`. Esecuzione comparata: output di `predict.py Roma Fiorentina` e di `predict.py --no-draw-balance Roma Fiorentina` byte-identici (confronto in Python: «IDENTICI»).
- **Correzione**: Usare il flag (`draw_balance=not args.no_draw_balance` e phi0/kappa a 0 quando disattivato) oppure rimuovere l'opzione dal parser.

**🟡 `F81-conteggio-31-combo` — La griglia φ0×κ della Fase 81 è di 37 combinazioni, non 31 (errore replicato in 4 file)**  
*numero-errato · bassa · **confermato***

- **Dove**: docs/DIARIO.md:8314; README.md:234; docs/STUDIO_PREMIER_LIGA.md:259; scripts/_run_fase81_mega_sweep_mi.py:17
- **Atteso**: PHI0S = [0.0,0.1,0.2,0.3,0.4,0.5,0.7] e KAPPAS = [0.5,1.0,1.5,2.0,3.0,5.0] (script righe 62-63) → combos = [(0,0)] + 6×6 = **37**.
- **Trovato**: «φ0×κ ∈ {0…0.7}×{0.5…5} (31 combo)» in tutti e quattro i punti.
- **Come è stato accertato**: Lettura di scripts/_run_fase81_mega_sweep_mi.py:62-63 e :250 (`combos = [(0.0,0.0)] + [(p,k) for p in PHI0S[1:] for k in KAPPAS]`); conferma dal registro: tutti e 6 i run `axis=phi_grid` hanno `len(metrics['curves']) == 37` (script Python su experiments/runs.jsonl).
- **Correzione**: Correggere «31 combo» → «37 combo» nei 4 punti (e, se si aggiorna il totale, «~70 varianti/lega» → 64: 11 ρ + 10 θ + 37 φ + 6 knee).

**🟡 `F81-docstring-griglie-stantie` — Il docstring di _run_fase81_mega_sweep_mi.py descrive le griglie vecchie (ρ 9 valori, θ 7) mentre il codice e il DIARIO usano quelle estese (11 e 10)**  
*incoerenza-doc · bassa · **confermato***

- **Dove**: scripts/_run_fase81_mega_sweep_mi.py:14-16 vs :60-61
- **Atteso**: Docstring coerente col codice: ρ ∈ {−0.22…+0.02} 11 valori, θ ∈ {1.00…1.50} 10 valori (come DIARIO:8311-8314 e README:234).
- **Trovato**: Docstring: «ρ ∈ {−0.14 … +0.02} (9 valori)», «θ ∈ {1.00 … 1.30} (7 valori)»; codice: RHOS 11 valori fino a −0.22, THETAS 10 fino a 1.50.
- **Come è stato accertato**: Lettura del file; conferma nel registro: i 12 run del commit 3c4cd164 hanno curves di 9/7 valori, i 12 del commit a0667fe4 (quelli citati dal DIARIO) ne hanno 11/10.
- **Correzione**: Allineare il docstring alle costanti effettive (l'estensione è del commit a0667fe «Fase 81: estende le griglie del mega-sweep ai bordi»).

**🟡 `F81-rho-star-premier` — Fase 81: «le valli Premier sono centrate esattamente sul riferimento: ρ*=−0.06/−0.04» non corrisponde agli argmin registrati**  
*numero-errato · bassa · **confermato***

- **Dove**: docs/DIARIO.md:8321-8323
- **Atteso**: Gli argmin per mercato dell'asse ρ in Premier, dal run registrato.
- **Trovato**: best ρ = −0.08 (1X2, GG, multigol), −0.06 (pareggio), −0.02 (ris. esatto), −0.18 (O/U). Nessun mercato ha argmin −0.04.
- **Come è stato accertato**: Dump di experiments/runs.jsonl (source=fase81_mega_sweep_mi, league=premier_league, axis=rho, commit a0667fe4): campo `best[mk]['value']`. La curva 1X2 è però pari a 5 decimali fra −0.08 e −0.06 (0.96220 entrambe) e l'intero range vale 1e-3, quindi la CONCLUSIONE (valle piatta, nessun margine) regge; è il numero citato a essere sbagliato. README:234 riporta la versione corretta («ρ*=−0.06»).
- **Correzione**: Sostituire con «ρ* fra −0.08 e −0.02 a seconda del mercato, curva piatta entro 1e-3 attorno a −0.06» oppure allineare al README.

**🟡 `F81-knee-CI-in-sample` — Fase 81: «SA k34 GG −0.0012 CI<0 (replica F80)» mescola la statistica in-sample con quella del selettore, e in F80 lo stesso Δ NON aveva CI<0**  
*conclusione-non-supportata · bassa · **confermato***

- **Dove**: docs/DIARIO.md:8357
- **Atteso**: La fase stessa dichiara (DIARIO:8316-8319) che «solo un guadagno che sopravvive al selettore [lfo] è reale»; e la Fase 80 riporta lo stesso Δ come non conclusivo.
- **Trovato**: Il CI<0 citato è quello del valore scelto a posteriori (best=34.0, Δ −0.001200, CI [−0.002409, −0.0000146]); il selettore lfo dà Δ −0.000751 con CI [−0.002026, +0.000540] (P 88%), che include lo zero. In Fase 80 lo stesso Δ −0.0012 aveva CI [−0.002427, +0.0000299] → includeva lo zero (P 97%), quindi «replica F80» + «CI<0» insieme sovra-dichiarano.
- **Come è stato accertato**: experiments/runs.jsonl: run fase81_mega_sweep_mi serie_a axis=knee (best.gg.ci e lfo.gg.ci) e run fase80_ggng_mi_league serie_a variant=k34 (gg_ci). Valori estratti con script Python a piena precisione.
- **Correzione**: Riscrivere: «SA k34 GG: best in-sample −0.0012 (CI<0 solo dopo selezione), lfo −0.0008 CI che include lo zero — coerente col P 97% della F80»; lo stato 🪑 in tabella resta corretto.

**🟡 `F81-residuo-rho-1x2-SA` — Fase 81-bis dichiara il residuo di ρ sul GG ma tace quello, di pari grandezza, sull'1X2 della Serie A**  
*omissione · bassa · **confermato***

- **Dove**: docs/DIARIO.md:8342-8351
- **Atteso**: Stessa onestà applicata al residuo GG («sul solo GG un filo di ρ-in-più aiuta ancora ~−0.0014»).
- **Trovato**: Nel run congiunto, a θ ottimo, ρ=−0.22 vs −0.06 dà: cs SA +0.008836 e Liga +0.011947 (citati), Liga 1X2 +0.001356 (citato), **SA 1X2 −0.001173** (non citato: ρ più negativo continua ad aiutare, quanto il residuo GG di −0.0014).
- **Come è stato accertato**: experiments/runs.jsonl, source=fase81_joint_rho_theta: serie_a x2 rho_gain_at_best_theta = −0.0011729 (best (−0.14,1.3)); la_liga x2 = +0.0013560; gg = −0.0015378 (SA) e −0.0014157 (Liga).
- **Correzione**: Aggiungere al residuo dichiarato: «e sull'1X2 della sola Serie A ρ=−0.22 aiuta ancora di −0.0012 a θ=1.3» — non cambia la scelta (una leva, non due), ma completa il quadro.

**🟡 `F82-riproducibilita-path-DC` — I risultati del path DC di Premier/Liga della Fase 82 non si riproducono col comando indicato: dipendono da cache della Fase 79 che lo script non rigenera (e senza le quali sparisce in silenzio)**  
*incompiuto · bassa · **confermato***

- **Dove**: scripts/_run_fase82_verifica_predizioni.py:102-123; docs/DIARIO.md:8488-8489 (nota di riproducibilità)
- **Atteso**: «python scripts/_run_fase82_verifica_predizioni.py (~5 min la prima volta: 6 backtest DC Serie A in cache)» dovrebbe riprodurre anche il Risultato 4 (1X2 argmax DC 52.9-53.5% su 3 leghe).
- **Trovato**: `_dc_cached` per premier_league/la_liga legge `outputs/db79_{league}_base_{s}.csv` e, se mancano, fa `return None`: la sezione DC viene saltata senza errore e il run registra `dc: {}`. Quei file li produce solo scripts/_run_fase79_leve_per_lega.py (~40 min). Oggi outputs/ contiene un solo file (implied_lammu_cache.csv), quindi il ri-run non riprodurrebbe il Risultato 4 per PL/Liga.
- **Come è stato accertato**: Lettura di scripts/_run_fase82_verifica_predizioni.py:102-123 e scripts/_run_fase79_leve_per_lega.py:68-82 (`fp = CACHE / f"db79_{league}_{name}_{season}.csv"`); `ls outputs/` → 1 file.
- **Correzione**: Nella nota di riproducibilità aggiungere la dipendenza («eseguire prima _run_fase79_leve_per_lega.py»), oppure far calcolare al fallback anche PL/Liga invece di `return None` (e almeno stampare un avviso).

**🟡 `F81-conteggio-run-registro` — La Fase 81 dichiara «12+2 run» ma nel registro i run con source=fase81_mega_sweep_mi sono 24 (due griglie diverse sotto lo stesso tag)**  
*incoerenza-doc · bassa · ridimensionato*

- **Dove**: docs/DIARIO.md:8308 e 8393-8395; docs/STUDIO_PREMIER_LIGA.md:257
- **Atteso**: Chi ri-deriva i numeri dal registro deve poter isolare i run corretti (griglia estesa, commit a0667fe4).
- **Trovato**: 24 righe con `source=fase81_mega_sweep_mi`: 12 al commit 3c4cd164 (griglia stretta: ρ 9, θ 7) e 12 al commit a0667fe4 (griglia estesa). I due gruppi danno best diversi (es. Premier O/U: best ρ=−0.14 nel primo, −0.18 nel secondo). Il DIARIO cita solo «(12)».
- **Come è stato accertato**: Conteggio su experiments/runs.jsonl per source e git_commit (script Python): 12 + 12; `grep -c fase81_mega_sweep_mi experiments/runs.jsonl` → 24.
- **Correzione**: Nel DIARIO/STUDIO precisare «24 run registrati, i numeri della fase sono i 12 del commit a0667fe (griglia estesa)»; in alternativa taggare le due passate in modo distinto.
- **Verifica avversariale**: Il conteggio e' esatto ma il difetto descritto («chi ri-deriva non puo' isolare i run corretti») non regge: il registro si disambigua da solo. Ogni riga porta git_commit e timestamp, e il DIARIO identifica univocamente la passata giusta citando le griglie estese (ρ 11 valori fino a −0.22, θ 10 fino a 1.50), che esistono SOLO nei run del commit a0667fe4 (quelli di 3c4cd164 hanno 9 e 7 valori). Inoltre «(12)» e' una descrizione corretta di una passata (3 leghe x 4 assi), non un conteggio di righe del file. Da segnalare pero' un fatto che l'auditor non poteva vedere e che rafforza la sua richiesta di una nota: nel working tree di adesso le righe fase81_mega_sweep_mi sono 40, non 24 — `git diff --stat experiments/runs.jsonl` mostra +16 righe NON committate, tutte con git_commit 6c9b3773 e timestamp 2026-07-26T21:18-21:23, cioe' una ri-esecuzione dello sweep fatta oggi da una sessione parallela. Il tag continua ad accumulare passate: una riga di nota nel DIARIO («i numeri sono quelli del commit a0667fe») costa poco.

**🟡 `F80-SA-nudge-alzato` — Fase 80 §📐: «in SA/PL alzato ~0-10%» è falso per la Serie A, il cui boost-38ª medio è 0.976 (una RIDUZIONE)**  
*numero-errato · bassa · ridimensionato*

- **Dove**: docs/DIARIO.md:8283-8285
- **Atteso**: Coerenza con la tabella della stessa fase (DIARIO:8228-8230: «boost-μ alla 38ª: SA 0.976»).
- **Trovato**: Il testo del blocco 📐 contrappone la Liga («RIDOTTO ~8.5%») a «SA/PL alzato ~0-10%», ma in Serie A la media LFO è 0.976 (−2.4%), con fit per-stagione 0.844, 0.864, 0.972, 1.032, 1.051, 1.095.
- **Come è stato accertato**: Registro (metrics.boost38_mean serie_a = 0.97620) e ri-esecuzione del fit LFO della Fase 80 (script che riusa _load/_invert/_fit_nudge del file di fase): serie merie ['0.844','0.864','0.972','1.032','1.051','1.095'], media 0.9762 — identica al registro.
- **Correzione**: Scrivere «in PL alzato ~+10%, in SA sostanzialmente neutro in media (0.976) ma crescente nel tempo (0.84 → 1.10 fra il primo e l'ultimo fit)».
- **Verifica avversariale**: Ho riprodotto il fit LFO della Fase 80 io stesso, riusando _load/_invert/_fit_nudge del file di fase: Serie A boost-38a per stagione = 0.844, 0.864, 0.972, 1.032, 1.051, 1.095, media 0.9762 — identica al boost38_mean del registro (0.97620); Premier 1.0970, Liga 0.9147. Quindi in media la Serie A RIDUCE del 2.4% e «alzato» e' la parola sbagliata. Ma il rilievo e' etichettato «numero-errato» e non lo e': il numero corretto (0.976) e' scritto due volte nella stessa fase (tabella DIARIO:8228-8230 «boost-μ alla 38a: SA 0.976») e ripreso dalla F81 («PL x1.10, SA ~1.0, Liga x0.92»), quindi nessun lettore viene indotto a un valore falso; e 3 dei 6 fit di Serie A ALZANO davvero μ (+3.2%, +5.1%, +9.5%), per cui «~0-10%» e' una forchetta lasca ma non inventata. E' un'imprecisione lessicale dentro il blocco 📐, non un numero errato, e non regge nessuna conclusione. Nota di contesto (non nel rilievo): la stessa lasco-formulazione tocca anche «profilo INVERTITO» per la Liga — SA 0.976 e Liga 0.915 sono ENTRAMBE riduzioni, l'inversione vera e' rispetto alla Premier (1.097).

**🟡 `F83-range-commit-non-verificabile` — Il range di commit citato dalla Fase 83 (a605e68…3e18c63) non è risolvibile in questo checkout: la storia è troncata (clone shallow)**  
*non-verificabile · bassa · ridimensionato*

- **Dove**: docs/DIARIO.md:8497-8499
- **Atteso**: Poter ri-verificare i 19 commit «Codex» del 10-11 luglio 2026.
- **Trovato**: `git cat-file -t a605e68` e `3e18c63` → «Not a valid object name»; la repo ha 68 commit, il più vecchio del 2026-07-22, ed esiste .git/shallow. NON è un errore del diario: l'hash a605e682 compare come `git_commit` di un run del 2026-07-10 in experiments/runs.jsonl, il che corrobora il range.
- **Come è stato accertato**: `git cat-file -t`, `git rev-list --all --count` (68), `ls .git/shallow`, e grep del campo git_commit in runs.jsonl (run del 2026-07-10T16:38 con a605e682…).
- **Correzione**: Nessuna correzione al testo; eventualmente annotare nel DIARIO/manuale che la verifica di quel range richiede un clone completo (in ambiente shallow gli hash pre-2026-07-22 non risolvono).
- **Verifica avversariale**: I fatti sono esatti e li ho riprodotti: `git cat-file -t a605e68` e `3e18c63` -> «Not a valid object name»; `git rev-list --all --count` = 68; `.git/shallow` esiste; il commit piu' vecchio raggiungibile e' del 2026-07-22. Ma non e' un difetto del repository ne' del DIARIO, e l'auditor lo dice lui stesso proponendo «nessuna correzione al testo»: e' una limitazione dell'ambiente di verifica (clone shallow), corroborata anzi in senso favorevole al diario dal fatto che l'hash a605e682 compare come git_commit di un run del 2026-07-10 in runs.jsonl. Va classificato come «non verificabile qui», non come rilievo: nella lista dei difetti occupa uno slot che non gli spetta. Al massimo merita una riga nel MANUALE_SOPRAVVIVENZA.md fra i fatti operativi sull'ambiente.

**🟡 `F83-F5-premessa-superata` — La premessa del difetto latente F5 della Fase 83 («zero quote mancanti nelle stagioni valutate») non è più esatta dopo l'ingresso delle 5 leghe**  
*incoerenza-doc · bassa · ~~smontato~~*

- **Dove**: docs/DIARIO.md:8539 (riga F5 della tabella); src/evaluation/markets.py:42-55 e :64-75
- **Atteso**: model_ll e market_ll confrontabili perché calcolati sulle stesse righe (la Fase 83 lo giustifica con «zero quote mancanti nelle stagioni valutate → impatto nullo»).
- **Trovato**: Il codice calcola `model_ll` su tutte le righe e `market_ll` solo dove le quote sono finite (mascheratura `has`). Dopo l'import di Bundesliga/Ligue 1: bundesliga 2018-19 ha 1 partita senza quote 1X2 e la_liga 2017-18 ne ha 1; l'O/U 2.5 manca su TUTTE le partite 2017-18 e 2018-19 di tutte e 5 le leghe. L'impatto resta trascurabile (1/306), ma «zero» non è più vero per una stagione utilizzabile come test.
- **Come è stato accertato**: Lettura di src/evaluation/markets.py; conteggio per lega/stagione delle righe con quote non finite via loader.load_league (script Python): bundesliga 1819 no1x2=1, la_liga 1718 no1x2=1, noou=380/306 su 1718 e 1819 ovunque.
- **Correzione**: O correggere markets.py calcolando anche model_ll sulla maschera `has` (cambia numeri registrati: farlo solo con una fase dedicata), o aggiornare la nota F5 dichiarando i casi residui misurati (2 righe su 5 leghe, O/U assente nelle prime due stagioni).
- **Verifica avversariale**: La premessa della F5 e' scoped: «zero quote mancanti NELLE STAGIONI VALUTATE». Ho controllato quali stagioni valutano tutti i chiamanti di compute_market_metrics — scripts/markets.py:29 (DEFAULT_SEASONS), scripts/_run_gap_markets.py:32, scripts/analyze_gap.py:29, scripts/_run_gap_covid.py:21, piu' _run_combo_analysis.py e _run_draw_infl.py che riusano quei pool: tutti [2021, 2122, 2223, 2324, 2425, 2526]. Poi ho contato le quote mancanti su tutte e 5 le leghe x 9 stagioni con loader.load_league: le uniche celle non finite stanno in 1718 e 1819 (la_liga 1718: 1 riga senza 1X2; bundesliga 1819: 1 riga; O/U di chiusura assente su tutte le righe di 1718/1819 in tutte e 5 le leghe — conseguenza dichiarata e voluta della Fase 73, che ha riclassificato quella linea come APERTURA reale). Nelle stagioni 2021-2526, su tutte e 5 le leghe, le quote mancanti sono ESATTAMENTE ZERO. Quindi la premessa della F5 e' ancora esatta e «impatto nullo» resta vero: il rilievo confonde «esistono righe senza quote nello snapshot» con «esistono righe senza quote nelle stagioni valutate». Le 2 righe citate sono per di piu' gia' catalogate altrove (Fasi 69/73, docs/DATI.md). Correggere markets.py o riscrivere la nota F5 sarebbe esattamente il falso positivo costoso di cui parla il protocollo.

<details><summary>Verifiche con esito OK su questo fronte</summary>

- Fase 80 — tabella dei Δ GG/NG riprodotta ESATTAMENTE dai 12 run `fase80_ggng_mi_league`: SA φ35 −0.000287 (P 95%), k34 −0.001200 (P 97%), combo −0.001381 (P 97%); PL +0.000141 (16%), −0.000214 (62%), −0.000183 (62%); Liga −0.000587 CI [−0.001084,−0.0000829] (99%), +0.000823 CI [+0.0000333,+0.001608] (2%), +0.000194 (28%). Tutti i «CI esclude lo zero» verificati a piena precisione (il +0.0000 del k34-Liga è un arrotondamento di 3.33e-5 > 0, il CI esclude davvero lo zero).
- Fase 80 — costanti fittate RI-DERIVATE da zero (ri-eseguito il fit LFO con _load/_invert/_fit_nudge/fit_balance_phi): medie identiche al registro (φ0 SA 0.1612 / PL 0.1712 / Liga 0.3204; κ 1.536/3.473/2.886; boost-38ª 0.9762/1.0970/0.9147) e claim per-stagione esatti: PL 0.681→0.000 con κ al bound 5.00, Liga primo fit 0.098 poi 0.311-0.473 (stabile 5/6).
- Fase 80 — la citazione della Fase 50 («GG 0.6810, Δ −0.0010, P 98%») coincide col registro: run `fase50_mi_sweep`, variante prop-phi35+k34 → gg 0.6810412, delta −0.0010091, p 0.9797, CI [−0.0019576,−0.0000399].
- Fase 81 — headline verificate dai run `fase81_mega_sweep_mi` (commit a0667fe4): ris. esatto θ* 1.25 con Δ −0.0079 (SA) e −0.0085 (Liga), lfo −0.0078 CI [−0.0129,−0.0028] e −0.0069 CI [−0.0109,−0.0027]; Liga 1X2 lfo −0.002334 CI [−0.004564,−0.0000294] e GG lfo −0.002452 CI [−0.004421,−0.000458] — tutti CI<0 come dichiarato; φ-grid Liga (0.7,0.5) lfo −0.0019 CI<0 e SA (0.7,0.5) lfo −0.0013 P 92%; boost-38ª per knee (PL 1.097, SA 0.976, Liga 0.915, k37 0.772). Verificata anche la monotonia dell'1X2 in θ fino a 1.50 (SA 0.96418→0.96054).
- Fase 81-bis — i numeri del check congiunto ρ×θ coincidono col run `fase81_joint_rho_theta`: a θ ottimo, ρ=−0.22 vs −0.06 peggiora il risultato esatto di +0.008836 (SA) e +0.011947 (Liga), e l'1X2 Liga di +0.001356; residuo GG −0.0014 (Liga) / −0.0015 (SA).
- Fase 82 — tutte le cifre-titolo riprodotte dai 3 run: 1X2 argmax SA 54.21% vs mercato 54.30% e baseline-casa 40.44%; PL 55.26% = mercato; Liga 54.34% = mercato, baseline 45.04%; ris. esatto top-pick 14.61/13.87 (SA), 12.28/12.02 (PL), 15.44/14.25 (Liga); DC senza quote 52.9-53.5%; bias/ECE per-lega (SA casa +0.0236 / pareggio −0.0202 / scarto-casa≥2 +0.0346; PL |bias|≤0.0158 con ECE minimo 0.0034; Liga GG −0.0356, cs +0.0246/+0.0274) e l'effetto del router in Liga (GG bias −0.0356→−0.0075, ECE 0.0356→0.0122; cs_home ECE 0.0246→0.0122; ECE giù su 15 mercati su 19).
- Fase 82 — controllo indipendente della baseline «sempre 1-1»: il punteggio modale della finestra di test è davvero 1-1 in tutte e 3 le leghe con frequenze 289/2280=12.68%, 250/2280=10.96%, 313/2280=13.73% (= i 'base' del registro). Verificata anche l'attribuzione del tilt Serie A al MERCATO: il devig della chiusura ha bias H +0.0200 / X −0.0129, stesso segno e ordine del motore (+0.0236/−0.0202).
- Blocchi 📐 verificati riga per riga contro src/: balance_phi = φ0·exp(−κ|λ−μ|) con bound [0,2]×[0,5] (market_implied.py:218-250); τ di Dixon-Coles su (0,0),(0,1),(1,0),(1,1) e inflazione diagonale con rinormalizzazione finale (score_matrix:66-96); dp mean-preserving per bisezione (_dp_pmf:47-63); devig moltiplicativo (metrics.devig_1x2/devig_binary); base del nudge [1,(g−19.5)/18.5,max(0,g−34)/4] e boost-38ª = exp(X(38)·ĉ); definizioni di ECE (10 fasce) e hit-rate binario/argmax nello script F82; selettore _lfo_pick.
- Fase 83 — il fix F2 è realmente in `scripts/calibrate.py` (legge half-life/shrinkage/blend/blend_signal/PRIOR da src.config.SERIE_A e registra `promoted_prior` nel config del run); i difetti latenti F5 e F6 sono descritti correttamente (markets.py maschera solo il market_ll; `_draw_base_arrays` chiama `expected_goals(h,a)` senza `features`, quindi la φ è fittata senza covariate); tutti gli script citati nella tabella dei 7 difetti esistono; il backtest ufficiale «2526: 1X2 0.9925» coincide col registro (0.992502, commit 4ecf3902/c297279f/0b63fcd2).
- Fase 83-bis — verificata ESEGUENDO `scripts/predict.py` sulle 3 leghe: δ 0.23 / 0.33 / 0.22 e γ auto-fittato +0.128 / +0.191 / +0.297, identici a quanto dichiarato in DIARIO:8602 e README:237.
- Copertura documentale delle Fasi 80/81/82/83/83-bis: tutte hanno riga nel README (233-237), voce nel DIARIO col blocco 📐, run nel registro (12 + 24+2 + 3; la 83/83-bis non ne richiedono) e aggiornamento in PANCHINA/STUDIO_PREMIER_LIGA con numeri coerenti (PANCHINA:60,68,161-163; STUDIO §6-bis/6-ter/6-quater).

</details>

### Fasi 84-88  ·  8 rilievi
**🔴 `F85-com-poisson-e-la-stessa-dp` — La "COM-Poisson" della Fase 85 NON è una forma alternativa: è la stessa double-Poisson del router, riparametrizzata**  
*conclusione-non-supportata · alta · **confermato***

- **Dove**: docs/DIARIO.md:8767-8787 e 8813-8818 (blocco 📐); README.md:239; docs/PANCHINA.md:85 e 300; docs/PISTE.md:139-140 e 165-166; docs/GLOSSARIO.md:44-45; docs/DIARIO.md:9044 ("terza conferma indipendente, dopo COM-Poisson")
- **Atteso**: Se la COM-Poisson è "la versione seria della sotto-dispersione che la dp (scorciatoia) non è", deve essere una famiglia DIVERSA, e il suo confronto con la dp deve essere una prova indipendente.
- **Trovato**: dp(θ) ≡ COM-Poisson(ν=θ): sono la stessa famiglia a un parametro, mean-matched, quindi identiche punto per punto. Il confronto della Fase 85 mette la dp contro se stessa a un parametro diverso; non è una conferma indipendente, e la frase "la NB e la dp non sono la versione seria" è falsa per la dp.
- **Come è stato accertato**: Codice: src/models/market_implied.py:47-63 calcola q ∝ exp(θ·(k·ln(c·rate) − c·rate − ln k!)) = (c·rate)^{θk}e^{−θc·rate}/(k!)^θ ∝ a^k/(k!)^θ con a=(c·rate)^θ — che è esattamente la forma p(x) ∝ a^x/(x!)^ν di scripts/_run_tail_analysis.py:70-84 con ν=θ (per ν fisso la media è strettamente crescente in a, quindi il mean-matching individua LA stessa distribuzione). Numerico: max|_dp_pmf(rate,θ) − compois_pmf(rate,ν=θ)| ≤ 7.1e-06 su rate∈{0.8,1.24,1.6,2.2} × θ∈{1.15,1.225,1.35,1.5}. E l'output stesso dello script lo mostra: `python scripts/_run_tail_analysis.py` dà righe IDENTICHE per dp θ=1.35 e COM ν=1.35 (2.8358 / +0.0002 / −0.0103) e per θ=1.5 e ν=1.50 (2.8455 / −0.0042 / −0.0177).
- **Correzione**: Riscrivere la sezione COM-Poisson della Fase 85 (e le voci derivate in README/PANCHINA/PISTE/GLOSSARIO) come: «la dp mean-preserving È una COM-Poisson riparametrizzata (∝ a^x/(x!)^θ); la griglia ν non è una forma nuova ma una griglia θ più fine». Togliere "versione seria/scorciatoia", declassare la voce PANCHINA "COM-Poisson" a duplicato della dp, e correggere il conteggio di F87/PISTE: le conferme indipendenti sono DUE (isotonica+mistura e θ_team), non tre.

**🟠 `F88-alpha-star-zero-mai-testato` — Fase 88: «È α*=0 su un mercato NUOVO (il margine)» — l'encompassing non è mai stato calcolato, e se lo si calcola dà α*≈1, CI che esclude lo zero**  
*conclusione-non-supportata · media · **confermato***

- **Dove**: docs/DIARIO.md:9096-9098; README.md:243 ("✅ α*=0 su un mercato NUOVO (il margine)"); scripts/_run_ah_benchmark.py:118-140 (calcola solo corr, Brier, medie)
- **Atteso**: Nel linguaggio del progetto (Fase 16) α*=0 significa: nella combinazione α·modello+(1−α)·mercato il peso ottimo sul MODELLO è zero, cioè il mercato ingloba il modello. Va stabilito con una regressione di encompassing.
- **Trovato**: Lo script non fa alcun test di encompassing. Rifacendolo sugli stessi 7.437 casi: α* (peso sul modello che minimizza il Brier) = 1.082, bootstrap CI95 [0.190, 2.011] → NON include lo zero; il guadagno della combinazione sul mercato è +0.000166 [+0.0000048, +0.000472]. Quello che i dati sostengono è il PAREGGIO in Brier: ΔBrier (modello−mercato) = −0.00014, CI95 appaiato [−0.00035, +0.00008] (per lega: SA +0.00000 [−0.00038,+0.00037], PL −0.00019 [−0.00059,+0.00020], Liga −0.00022 [−0.00060,+0.00014]).
- **Come è stato accertato**: Ho ri-eseguito `python scripts/_run_ah_benchmark.py` (tabella riprodotta esatta) salvando model_p/market_p/realized, poi calcolato α* = mean((y−k)(m−k))/mean((m−k)²) con bootstrap a 2.000 ricampionamenti e il bootstrap appaiato (3.000) sulla differenza di Brier.
- **Correzione**: Riformulare Fase 88 e la riga README come «pareggio in Brier col mercato sharp, differenza dentro l'IC» e togliere la formula α*=0 (o eseguire davvero l'encompassing e riportarlo — con la nota che il modello NON è indipendente dal mercato, essendo derivato dalle sue quote 1X2+O/U, e che l'α è in-sample).

**🟡 `F86bis-descrizione-instabilita-theta` — Fase 86-bis: la descrizione dei θ fittati per stagione non corrisponde all'output dello script**  
*numero-errato · bassa · **confermato***

- **Dove**: docs/DIARIO.md:8961-8964
- **Atteso**: «il gruppo alto va 1.0 nel 2021-22 → 1.1 nelle stagioni dopo; il medio oscilla 1.225↔1.1»
- **Trovato**: Output reale di `python scripts/_run_team_dispersion.py`: 2122 {low 1.225, mid 1.225, high 1.0}; 2223 {1.225, 1.1, 1.0}; 2324 {1.225, 1.1, 1.0}; 2425 {1.225, 1.1, 1.1}; 2526 {1.225, 1.1, 1.1}. Il gruppo alto resta 1.0 per TRE stagioni e passa a 1.1 nelle ultime due; il medio cambia una sola volta (1.225→1.1) e poi resta fermo: nessuna oscillazione.
- **Come è stato accertato**: Esecuzione completa dello script (verdetto riprodotto esatto: n=5.690, exact-LL 2.8212 globale vs 2.8222 θ_team, Δ +0.00096) — il log stampa i θ_g stagione per stagione.
- **Correzione**: Correggere la frase: i θ di gruppo sono STABILMENTE diversi da 1.225 (1.0-1.1) sul passato e quel contrasto non trasferisce; il verdetto negativo non cambia, ma il meccanismo va descritto come "contrasto-θ stimato sul passato che non si conferma nel futuro", non come oscillazione anno-su-anno.

**🟡 `F85-zero-over45` — Fase 85: «Over 4.5 è azzerato a θ≈1.10» — lo zero è a θ≈1.15**  
*numero-errato · bassa · **confermato***

- **Dove**: docs/DIARIO.md:8762-8764; README.md:239; docs/PISTE.md:138-139
- **Atteso**: Il θ che azzera lo scarto di calibrazione su Over 4.5 (P media − frequenza reale).
- **Trovato**: Sulla stessa cache: θ=1.10 → +0.0028; θ=1.15 → +0.0001; θ=1.175 → −0.0012; θ=1.225 → −0.0039. Lo zero è a θ≈1.152, non 1.10. Il dato era già nella tabella della fase (riga COM ν=1.15 → +0.0001). Over 3.5 invece è confermato: zero a θ≈1.35 (+0.0002).
- **Come è stato accertato**: Stesso ricalcolo a griglia fine descritto in F85-minimo-esatto-a-theta-1225 (colonne O3.5 Δ / O4.5 Δ).
- **Correzione**: Scrivere «Over 4.5 vuole θ≈1.15, Over 3.5 θ≈1.35»: la "tensione di profondità" resta reale ma più stretta (1.15 vs 1.35).

**🟡 `F84-nota-F2-non-nel-codice` — Fase 84: la svista F2 è dichiarata «lasciata con nota», ma nel codice la nota non c'è**  
*incompiuto · bassa · **confermato***

- **Dove**: docs/DIARIO.md:8668-8671 ("F2 in implied_lambda_mu l'O/U è sotto-pesato 3:1 su input incoerenti … lasciato con nota"); src/models/market_implied.py:109-127
- **Atteso**: Un commento/nota in `implied_lambda_mu` che documenti il peso relativo dell'obiettivo O/U rispetto ai tre residui 1X2 e il contratto (i chiamanti devigano prima).
- **Trovato**: La docstring e il corpo di `implied_lambda_mu` non contengono alcuna nota in merito; il commit della Fase 84 tocca `market_implied.py` solo per il commento di `DP_THETA`. Nessun "3:1"/"sotto-pes*" in src/ o tests/.
- **Come è stato accertato**: `git show 6542a22 -- src/models/market_implied.py` mostra un'unica riga modificata (DP_THETA); lettura diretta di src/models/market_implied.py:109-127; grep di "3:1" e "sotto-pes" su src/ e tests/ senza esiti (solo .pyc).
- **Correzione**: O aggiungere davvero la nota in `implied_lambda_mu` (una riga: obiettivo = 3 residui 1X2 + 1 residuo O/U, valido perché i chiamanti passano probabilità già devigate), oppure correggere il diario in «lasciato invariato, documentato solo qui».

**🟡 `F88-theta-serie-a-su-tre-leghe` — Fase 88: il benchmark AH usa θ=1.225 (costante Serie A) anche su Premier e Liga, senza dichiararlo come limite**  
*omissione · bassa · **confermato***

- **Dove**: scripts/_run_ah_benchmark.py:38 (THETA = 1.225, applicato a tutte e 3 le leghe); docs/DIARIO.md:9078-9081 e 9114-9116 (blocco 📐: «matrice del router (dp θ=1.225)»)
- **Atteso**: Secondo §7 del CLAUDE.md e la Fase 81 (docs/DIARIO.md:8366, tabella: «θ router | ⚽ 1.225 (SA) | ❌ 1.0 (liscio) Premier | ~1.2 Liga»), il router è per-lega: su Premier la costante adottata è θ=1.0.
- **Trovato**: Il benchmark applica la costante Serie A a tutte e tre le leghe e non lo dichiara. Sensibilità misurata su Premier (2.490 partite): Brier 0.20813 con θ=1 (nessuna dp), 0.20819 con θ=1.10, 0.20825 con θ=1.225, contro 0.20844 del mercato. La conclusione (pareggio col mercato) NON cambia, ma il "router" usato non è quello adottato per quella lega.
- **Come è stato accertato**: Lettura dello script + ri-esecuzione limitata a Premier (stessa pipeline: devig 1X2/O-U → implied_lambda_mu(ρ=−0.06) → cover fraction) con dp_theta ∈ {None, 1.10, 1.225}.
- **Correzione**: Aggiungere una riga di limite in Fase 88 ("θ=1.225 anche fuori Serie A; con il θ per-lega il Brier Premier scende a 0.20813, conclusione invariata") oppure parametrizzare THETA per lega nello script.

**🟡 `F84-riferimento-run-nel-registro` — Fase 84: «I 6 run del backtest ufficiale … registrati in runs.jsonl (config c297279f)» — i 6 run stanno su DUE commit e c297279f è un git_commit, non una config**  
*non-verificabile · bassa · **confermato***

- **Dove**: docs/DIARIO.md:8714-8717 (blocco 📐)
- **Atteso**: Un puntatore che permetta di isolare i 6 run dell'audit nel registro.
- **Trovato**: In experiments/runs.jsonl non esiste un campo `config_hash`; con git_commit=c297279f ci sono 4 run (2021 due volte, 2122, 2526), i restanti 5 (2122, 2223, 2324, 2425, 2526) hanno git_commit=0b63fcd2. I NUMERI però si riproducono esattamente prendendo l'ultimo run per stagione della finestra 2026-07-23T10:10→10:17: media 1X2 0.979687, O/U 0.688484.
- **Come è stato accertato**: Scansione di experiments/runs.jsonl per timestamp/commit; media ricalcolata sulle 6 stagioni distinte.
- **Correzione**: Sostituire il puntatore con «6 run del 2026-07-23 10:10-10:17 in runs.jsonl (commit c297279f e 0b63fcd2)», oppure registrare un config_hash come dichiarato.

**🟡 `F85-minimo-esatto-a-theta-1225` — «L'exact-score log-loss ha il minimo ESATTAMENTE a θ=1.225» è un artefatto della griglia grossolana: il minimo è a θ≈1.175**  
*conclusione-non-supportata · bassa · ridimensionato*

- **Dove**: docs/DIARIO.md:8757-8761 e 8821-8825 (blocco 📐); README.md:239; docs/PISTE.md:136-137
- **Atteso**: Se θ=1.225 è "l'ottimo diretto sul risultato esatto" e quindi "una conferma indipendente e non banale" della costante del router, il minimo deve reggere a un raffinamento della griglia.
- **Trovato**: Sulla stessa cache (outputs/implied_lammu_cache.csv, 7.980 partite) e con lo stesso mi.score_matrix(ρ=−0.06): θ=1.150 → 2.832060, θ=1.175 → 2.831921 (MINIMO), θ=1.200 → 2.831963, θ=1.225 → 2.832185. Il minimo della famiglia è ≈1.175, migliore di 1.225 di 0.00027. Lo mostrava già la tabella stessa della fase: la riga "COM-Poisson ν=1.15" (che è dp θ=1.15, vedi finding precedente) dà 2.8321 < 2.8322 di θ=1.225 — letta come "pareggia ma non batte" invece che come "il minimo è sotto 1.225".
- **Come è stato accertato**: Ricalcolo diretto: per θ∈{1.10,1.125,1.15,1.175,1.20,1.225,1.25} ho ricostruito exact-LL = mean(−log M[hg,ag]) con M=mi.score_matrix(lam,mu,rho=−0.06,dp_theta=θ) sulla cache dei λ,μ (stesso codice dello script). Output: 2.832903 / 2.832386 / 2.832060 / 2.831921 / 2.831963 / 2.832185 / 2.832581.
- **Correzione**: Sostituire "minimo ESATTAMENTE a θ=1.225" con "il minimo della famiglia dp sul risultato esatto è a θ≈1.175 (2.8319); sulla griglia {1, 1.1, 1.225, 1.35, 1.5} cade su 1.225, e la differenza vale 0.0003". Togliere la qualifica di "conferma indipendente" della costante del router (la costante resta giustificata dalla Fase 52 sui mercati, non da questo minimo).
- **Verifica avversariale**: Il FATTO è confermato, la CONSEGUENZA che l'auditor ne trae è un'over-reach. Fatto: ricalcolando exact-LL = mean(−log M[hg,ag]) con M=mi.score_matrix(lam,mu,rho=−0.06,dp_theta=θ) sulla stessa cache (7.980 partite) ottengo θ=1.100→2.832903, 1.125→2.832386, 1.150→2.832060, 1.160→2.831982, 1.175→2.831921 (MINIMO), 1.200→2.831963, 1.225→2.832185, 1.250→2.832581, 1.350→2.835851. Il minimo della famiglia è a θ≈1.175, non 1.225, quindi la parola «ESATTAMENTE» (DIARIO:8757, README:239) è un artefatto della griglia {1, 1.1, 1.225, 1.35, 1.5}. MA: il vantaggio di 1.175 su 1.225 vale 0.000264 e NON è distinguibile dal rumore — bootstrap appaiato (4.000 ricampionamenti) sulla differenza per-partita: −0.000264, CI95 [−0.000866, +0.000312], P(1.175 meglio)=80.3%. Quindi la conclusione sostanziale della fase («θ≈1.2 è anche l'ottimo diretto sul risultato esatto: una conferma indipendente e non banale») REGGE, ed è formulata nel diario proprio come «θ≈1.2», non «1.225 al millesimo». Il fix proposto dall'auditor («togliere la qualifica di conferma indipendente») andrebbe oltre l'evidenza e cancellerebbe un risultato valido: il log-loss del risultato esatto È una metrica indipendente dal listino della Fase 52, e conferma la costante entro il proprio CI. Da correggere solo la parola «ESATTAMENTE» → «il minimo sulla griglia cade su 1.225; a griglia fine è ≈1.175, differenza 0.0003 dentro l'IC».

<details><summary>Verifiche con esito OK su questo fronte</summary>

- Fase 88 — tabella riprodotta ESATTA rieseguendo `python scripts/_run_ah_benchmark.py`: n=7437; Serie A 2478/corr 0.9110/Brier 0.2029-0.2029/reale 0.4740; Premier 2490/0.9087/0.2083-0.2084/0.4916; Liga 2469/0.9242/0.2007-0.2009/0.4995; TUTTE 0.9147/0.2040-0.2041/0.4883; e l'"onestà" (P media modello 0.5019 e mercato 0.5013 contro realizzato 0.4883, ~1.4pp condivisi).
- Nessun conflitto fra il «Brier 0.2040 vs 0.2041» della Fase 88 e il «0.2044 vs 0.2044» citato in CLAUDE.md:478 / README:255 / lavoro_aperto.md:171: il secondo viene dal listino della Fase 98 (experiments/listino_validazione.json → handicap_asiatico_dettaglio: n=6839, brier_model 0.2043989, brier_market 0.2044090, Δ −1.01e-05, CI [−0.000255,+0.000232]), setup diverso (walk-forward, costanti ri-fittate). Entrambi corretti.
- Fase 85 — tabella riprodotta ESATTA (`_run_tail_analysis.py`, 7980 partite): Poisson 2.8369/+0.0096/+0.0083; dp 1.10 2.8329/+0.0071/+0.0028; dp 1.225 2.8322/+0.0037/−0.0039; dp 1.35 2.8359/+0.0002/−0.0103; dp 1.5 2.8455/−0.0042/−0.0177; COM 1.15 2.8321/+0.0057/+0.0001.
- Fase 85 — controprova sul lato esiti riprodotta: calibrazione della chiusura devigata su 10.259 partite, fascia <5% n=161 (rumore), favoriti 0.5-0.7 prezzati 0.5888 vs realizzati 0.6128 (+0.0240); e il numero del blocco 📐 sul risultato esatto (fascia P 0.10-0.20: Poisson 0.1209 vs reale 0.1290, +0.0081) torna a 4 decimali.
- Fase 86 — persistenza della volatilità-sorpresa riprodotta: corr grezza +0.2522 e controllata per forza +0.1961 su n=306, bande nulle per permutazione [−0.111,+0.119] e [−0.114,+0.111]; corr(vol, forza)=0.267; θ* per terzile OOS: low/mid 1.225, high 1.10 con exact-LL 2.9187 vs 2.9199.
- Fase 86 — E1 (fix di onestà sulla varianza dp) verificato numericamente e propagato: Var/μ = 0.8991 a μ=1.24, θ=1.205 (−10.1%, std −5.2%) e 0.8789 a μ=1.5, θ=1.225 (−12.1%); testo corretto in DIARIO:5629-5630 e 5722-5727 e in GLOSSARIO:37-40; i riferimenti «DIARIO:5550/5643» puntavano correttamente alle righe PRE-fix (verificato su 0698fe7^).
- Fase 86 — E2 (caveat best-price) riprodotto integralmente sul 2025-26: odds_home == AvgCH in 380/380 righe; ROI a soglia 0.05 = −4.73% (avg/avg, = il −4.7% del backtest ufficiale), −2.44% (max/max coerente), +0.91% (avg/max incoerente = il finto sign-flip); a soglia 0.03 = −9.72% (max/max). Caveat presente in README:95-99.
- Fase 86 — ridondanza dell'handicap asiatico come input riprodotta: n=2660 partite Serie A, corr(linea AH di chiusura, λ−μ) = −0.9952 (|0.9952|), regressione −linea ≈ 0.944·(λ−μ).
- Fase 86-bis — verdetto walk-forward riprodotto ESATTO: n=5.690 OOS, exact-LL 2.8212 (θ globale 1.225) vs 2.8222 (θ_team), Δ +0.00096.
- Fase 87 — entrambe le vie riprodotte ESATTE: (A) isotonica Δ log-loss OOS +0.0150 / +0.0061 / +0.0104 / +0.0109 su O1.5/2.5/3.5/4.5; (B) in-sample minimo a s=0.15 (−0.00059), walk-forward Δ −0.00042 con CI95 [−0.00145, +0.00059] e P 78.6%, e la tabella per stagione (2021 s*=0 Δ 0; 2122 −0.00301; 2223 −0.00164; 2324 −0.00055; 2425 +0.00140; 2526 +0.00125) combacia riga per riga.
- Fase 84 — headline ricalcolati dal registro (6 run del 2026-07-23): 1X2 0.979687, O/U 0.688484, mercato 0.963191/0.681630, baseline in-sample 1.083427/0.689187, gap +0.016496, 86.28% di distanza chiusa (86.56% con la baseline ex-ante 1.0860), ROI medio −15.666% su 864 scommesse. Anche «704 run registrati» è esatto (runs.jsonl a c297279f ha 704 righe) e «3420 partite × 9 stagioni» vale per tutte e 3 le leghe.
- Fase 84 — claim di codice verificati: double-Poisson mean-preserving con errore massimo 5.33e-13 su rate 0.2-4.0 × θ∈{0.9,1.05,1.1,1.225,1.35,1.5} (< 6e-13 dichiarato) e θ=1 identica alla Poisson (diff 0.0); guardia F1 presente in src/models/dixon_coles.py:252-257 con test in tests/test_dixon_coles.py:282-285; commento DP_THETA corretto (market_implied.py:308). Suite: 194 test verdi in 58s.
- Fase 84/86 — fix documentali dichiarati e verificati presenti: CLAUDE.md §2 dice ora «commit su main» (§3-bis); README Fase 5 ri-etichettata «modello (Fase 5, pre-prior)» con nota; files/README.md riempito; docs/GLOSSARIO.md creato; blocchi 📐 presenti in Fase 34 e Fase 77; header Arco 10 aggiornato (oggi 76-88); DATI.md marker Fase 73.
- Coerenza cross-documento dei verdetti negativi: PANCHINA.md:85/300 (COM-Poisson ❌), :301 (coda a 2 parametri ❌ con +0.0061…+0.0150 e Δ −0.00042 CI [−0.0015,+0.0006] P 78.6%), :315 (θ per-squadra ❌ con Δ +0.00096, 2.8222 vs 2.8212) e PISTE.md §4-ter/§4-quater riportano gli STESSI numeri del diario e del README.

</details>

### Fasi 89-91  ·  12 rilievi
**🔴 `F91-conclusivo-ritirato` — Fase 91: «top-4 batte la persistenza, entrambi conclusivi» è stato ritirato dalla Fase 92-bis (IC a grappoli che include lo zero) ma resta scritto in DIARIO e README**  
*conclusione-non-supportata · alta · **confermato***

- **Dove**: docs/DIARIO.md:9622-9623, README.md:247
- **Atteso**: Guadagno top-4 vs persistenza +0.0274 con IC95% a grappoli [−0.00057, +0.05220] → NON conclusivo per IC (il test dei segni 19/24, p=0.0066, resta a favore). È esattamente ciò che dichiara il commit 1ad6c30: «passa da conclusivo per IC a IC [-0.0006, +0.0522] NON conclusivo … l'etichetta era troppo forte».
- **Trovato**: DIARIO 9622-9623: «+0.0273 sulla persistenza (IC95% [+0.0037, +0.0502]): entrambi conclusivi». README:247: «batte il tasso base +0.2786 [+0.2208,+0.3345] E la persistenza +0.0273 [+0.0037,+0.0502], entrambi conclusivi».
- **Come è stato accertato**: experiments/fase91_positions.json → report.top4.gain_vs_persistence=0.027420, ci_persistence=[-0.000567314256972206, 0.052196548055272136], sign_test=[19,24,0.00661]. Il file è stato rigenerato dal commit 1ad6c30 (git log -- experiments/fase91_positions.json) e scripts/_run_fase91_positions.py:135-146 usa ora `_cluster_ci`. grep -rn "92-bis" --include=*.md . → nessun risultato: la ritrattazione non è mai entrata nella documentazione.
- **Correzione**: Correggere DIARIO 9622-9623 e README:247 con IC [−0.0006, +0.0522] «non conclusivo per IC, confermato dal test dei segni 19/24 p=0.0066», e aggiornare anche l'IC vs tasso base ([+0.2130, +0.3304] nell'artefatto corrente).

**🔴 `F100-script-campione-rotto` — scripts/nuovo_mercato_campione.py (mercato campione su Bundesliga e Ligue 1) non parte più dopo l'integrazione: ROOT calcolato per la vecchia posizione cantiere/scripts/ e percorsi cantiere/ inesistenti**  
*import-rotto · alta · **confermato***

- **Dove**: scripts/nuovo_mercato_campione.py:94, scripts/nuovo_mercato_campione.py:96, scripts/nuovo_mercato_campione.py:112, scripts/nuovo_mercato_campione.py:133-134, scripts/nuove_leghe.py:28
- **Atteso**: Uno script spostato in scripts/ deve avere ROOT = Path(__file__).resolve().parents[1] e leggere gli snapshot da data/ (dove l'integrazione ha messo bundesliga_matches.csv e ligue_1_matches.csv).
- **Trovato**: ROOT = Path(__file__).resolve().parents[2] → /home/user invece di /home/user/Polymarket-oracle; _snapshot_path() punta a ROOT/"cantiere"/"data"/*.csv e OUT a ROOT/"cantiere"/"out" (la cartella cantiere/ è stata cancellata dal commit 6c9b377). `python scripts/nuovo_mercato_campione.py --help` termina con ModuleNotFoundError: No module named 'src'. Non è un caso isolato: 25 script migrati dal cantiere falliscono allo stesso modo (27 file contengono `parents[2]`).
- **Come è stato accertato**: Esecuzione: `timeout 120 python scripts/nuovo_mercato_campione.py --help` → Traceback in scripts/nuove_leghe.py:31, ModuleNotFoundError: No module named 'src'. Ciclo su tutti gli script che citano «cantiere»: 25 BROKEN (audit_snapshots, audit_anomalie, build_new_snapshot, eda_nuove_leghe, leve_*, nuovo_calibrazione, tranche3_*, verifica_stime, …), 7 ok. `ls cantiere` → No such file or directory.
- **Correzione**: Sostituire `parents[2]` con `parents[1]` e i percorsi `ROOT/"cantiere"/{data,out,scripts}` con `data/`, `experiments/` (o docs/audit_5_leghe/numeri/) e `scripts/` nei 25 script migrati; aggiungere un test di fumo che importi ogni script di scripts/ per non ripetere la migrazione a mano.

**🟠 `F92bis-fase-fantasma` — La Fase 92-bis esiste come commit (codice, metriche e test cambiati) ma non ha voce nel DIARIO, riga nel README né run nel registro**  
*omissione · media · **confermato***

- **Dove**: docs/DIARIO.md (nessuna sezione «Fase 92-bis»), README.md:248-249 (si passa da 92 a 93), experiments/runs.jsonl
- **Atteso**: §2 del CLAUDE.md: ogni fase significativa ha riga nel README, voce nel DIARIO col blocco 📐, stato in PANCHINA e run in runs.jsonl. La 92-bis cambia predict.py (MARKET_ENGINE per-lega), _SUB_SUFFIXES di fetch_polymarket_open.py, la registrazione di backtest.py, aggiunge 8 test e RITIRA un'etichetta «conclusivo» della Fase 91.
- **Trovato**: grep -rn "92-bis" su tutti i .md del repo: 0 occorrenze. In runs.jsonl le uniche fasi taggate sono 89 (×2), 91, 94; nessuna riga per la rigenerazione dell'artefatto 91 fatta dalla 92-bis.
- **Come è stato accertato**: git log -1 --format=%B 1ad6c30 (elenca CODICE/TEST/METRICHE/DOCS); grep -rn "92-bis" --include=*.md . → vuoto; conteggio fasi in runs.jsonl via python (Counter sui config.phase).
- **Correzione**: Aggiungere la voce «Fase 92-bis» al DIARIO (con blocco 📐 sul bootstrap a grappoli e sul perché le 480 righe sono a grappolo) e la riga corrispondente nel «Registro completo dei risultati» del README; registrare il run rigenerato della Fase 91.

**🟠 `F91-numeri-misti` — Fase 91: la correzione del prior (Fase 92) è stata propagata SOLO in parte — README, PANCHINA e PISTE mescolano numeri pre-fix e post-fix nella stessa frase, il DIARIO è tutto pre-fix senza nota**  
*incoerenza-doc · media · **confermato***

- **Dove**: docs/DIARIO.md:9618, docs/DIARIO.md:9648-9656, docs/DIARIO.md:9658, docs/DIARIO.md:9663, docs/DIARIO.md:9671, README.md:247, docs/PANCHINA.md:64, docs/PISTE.md:603
- **Atteso**: Artefatto corrente (rigenerato dopo il fix): neopromosse dichiarato 54.7% vs realizzato 48.6% (−6.1pp), resto della lega 8.0% vs 9.1% (+1.1pp), ECE retrocessione 0.0479, ECE top-4 0.0140; casi con P(retro)>60%: 30, di cui 29 neopromosse, 15 salvate; fasce 50-70% 41.4%, 70-90% 50.0%, ≥90% 66.7%; Verona 1920 94.1%, Sunderland 2526 81.1%, Nott'm Forest 78.7%, Leeds 76.2%, Sheffield Utd 68.8%.
- **Trovato**: DIARIO 9648-9671 riporta ancora 40.6%/46.7%/60.0%, 37 casi/36 neopromosse/19 salvate, 58.7% vs 48.6% (−10.1pp), resto +1.8pp, Verona 92.5% ecc., senza alcuna nota di rettifica (mentre la Fase 89 fu annotata a mano dalla Fase 90). README:247 usa 54.7%/48.6%/−6.1pp (post-fix) ACCANTO a «37 casi … 36 neopromosse … 19 salvate», «70-90% → 46.7%», «>90% → 60.0%», «resto 7.3%» (pre-fix). PANCHINA:64 dice −10.1pp e ECE 0.0137, mentre la nota ✱7 dello stesso file usa 0.0140 e −6.1pp. PISTE:603 dice 58.7%/+1.8pp mentre PISTE:615 usa +6.1pp.
- **Come è stato accertato**: Ricalcolo dei bin dall'artefatto corrente e da quello del commit 70ba37e (script python con gli stessi 6 tagli e la stessa ECE a 10 fasce dello script: ECE riprodotte esattamente, 0.058864 vecchia / 0.047882 nuova). report.relegation_split corrente = promoted {n:72, declared:0.54744, realised:0.48611}, rest {n:408, declared:0.079863, realised:0.090686}.
- **Correzione**: Aggiornare la Fase 91 del DIARIO ai numeri dell'artefatto corrente (o annotarla come si è fatto con la Fase 89), e rendere coerenti README:247, PANCHINA:64 e PISTE:603 — oggi ogni documento contiene una miscela diversa delle due versioni.

**🟠 `F92-fascia-90-non-sparita` — Fase 92: «sparisce del tutto la fascia oltre il 90%» non è vero — la fascia esiste ancora (3 casi, dichiarato 94.3% vs realizzato 66.7%), sparisce solo dalla stampa perché lo script salta le fasce con n<5**  
*conclusione-non-supportata · media · **confermato***

- **Dove**: docs/DIARIO.md:9800-9803, scripts/_run_fase91_positions.py:200
- **Atteso**: Dopo il fix del prior restano 3 squadre-stagione con P(retrocessione) ≥ 0.90: Verona 1920 0.9415 (NON retrocessa, 9ª), Benevento 2021 0.9162 (retrocessa), Norwich 2122 0.9702 (retrocessa) → dichiarato 94.3%, realizzato 66.7%, scarto −27.6pp. Il caso peggiore (Verona) PEGGIORA col fix (0.9254 → 0.9415).
- **Trovato**: Il DIARIO della Fase 92 scrive «corretto il bug, scende a −6.1pp (ECE 0.0589 → 0.0479, e sparisce del tutto la fascia «oltre il 90%»)», che si legge come «non dichiariamo più nulla sopra il 90%».
- **Come è stato accertato**: Enumerazione delle righe con p_rel≥0.9 in experiments/fase91_positions.json (3 righe, elencate sopra) contro le 5 della versione 70ba37e; scripts/_run_fase91_positions.py:200 `if mm.sum() >= 5:` filtra la stampa della fascia, non i casi.
- **Correzione**: Riformulare: «la fascia >90% scende da 5 a 3 casi e scompare dalla tabella stampata (soglia n≥5), ma resta mal calibrata: 94.3% dichiarato contro 66.7% realizzato».

**🟠 `F100-sanity-fase89-obsoleta` — Il controllo di sanità di nuovo_mercato_campione.py è cablato sui valori PRE-fix del prior con tolleranza 1e-9: col codice corrente fallisce e lo script si ferma; i numeri campione di Bundesliga/Ligue 1 sono stati prodotti col DC pre-Fase 92**  
*bug-codice · media · **confermato***

- **Dove**: scripts/nuovo_mercato_campione.py:749-767, docs/audit_5_leghe/10_modelli_nuove_leghe.md:515-530
- **Atteso**: Il gate dovrebbe confrontarsi con i valori riproducibili dal codice corrente (log-loss 1.201061, Brier 0.658920, p_fav 0.600658) o leggere l'artefatto invece di cablare le costanti.
- **Trovato**: atteso = dict(logloss=1.19940324498676, p_fav=0.6005333333333334, hit=0.4166666666666667, n=24, brier=0.658387301875, rank_mean=1.875) con `ok = all(v < 1e-9 …)` e `return 1` in caso di scarto. Col codice corrente lo scarto sul log-loss è 1.7e-3 ≫ 1e-9 → «FALLITO», lo script si ferma prima di calcolare qualsiasi cosa. Di conseguenza l'affermazione dell'audit «le 6 quantità della Fase 89 riprodotte con scarto ESATTAMENTE 0.0» vale solo per il codice pre-Fase 92, e i numeri pubblicati (Bundesliga 0.7392, Ligue 1 0.9132 e tutte le baseline del §9) sono stati calcolati con il prior difettoso.
- **Come è stato accertato**: git show 4711d41:src/models/dixon_coles.py | grep -c "attack\[seen\]" → 0 (il cantiere non aveva il fix della Fase 92, entrato in quel ramo solo col merge 12da9e0 del 26/07 13:56, dopo i run); artefatto corrente della Fase 89 = 1.201061; ri-esecuzione di 2 stagioni col codice corrente identica all'artefatto corrente.
- **Correzione**: Aggiornare le costanti attese (o farle leggere da experiments/fase89_season_champion.json), rieseguire lo script sulle 5 leghe col prior corretto e ricontrollare i numeri del §9 dell'audit prima di considerarli acquisiti.

**🟠 `F100-tiebreak-senza-test` — Le regole di spareggio di Bundesliga e Ligue 1 sono entrate in produzione senza test: uno scambio fra le due tuple passerebbe la suite**  
*omissione · media · **confermato***

- **Dove**: src/models/season_sim.py:66-72, tests/test_season_sim.py:65-69, tests/test_season_sim.py:198-208
- **Atteso**: §2 del CLAUDE.md: un test per ogni nuova funzionalità. Le due tuple nuove differiscono solo per la posizione di «h2h» (bundesliga ('gd','gf','h2h') vs ligue_1 ('gd','h2h','gf')): serve un caso che le distingua, sia su final_table sia sul ramo _resolve_sim_tie.
- **Trovato**: test_tiebreak_rules_per_league asserisce solo serie_a[0]=='h2h', la_liga[0]=='h2h', premier_league[0]=='gd' e il default; test_simulated_tie_is_resolved_by_league_rule copre solo serie_a e premier_league. Nessun test nomina bundesliga o ligue_1 (grep su tests/test_season_sim.py: 0 occorrenze).
- **Come è stato accertato**: grep -n "bundesliga|ligue_1" tests/test_season_sim.py → nessun risultato; `python -m pytest tests/test_season_sim.py -q` → 12 passed. Verifica comportamentale fatta a mano (caso costruito con A e B a pari punti e pari DR, A con più gol fatti, B vincitore degli scontri diretti): bundesliga ordina A prima di B, ligue_1 B prima di A, serie_a B, premier A — il codice fa ciò che dichiara, ma nulla lo protegge.
- **Correzione**: Estendere test_tiebreak_rules_per_league alle tuple complete di bundesliga e ligue_1 e aggiungere un caso su final_table (e uno su simulate_season) che distingua ('gd','gf','h2h') da ('gd','h2h','gf').

**🟠 `F89-91-registro-mancante` — Le rigenerazioni degli artefatti 89 e 91 non sono mai state registrate in runs.jsonl, la Fase 89-bis non ha alcuna riga di registro e il suo artefatto non contiene il blocco squad_value citato nel diario**  
*incompiuto · media · **confermato***

- **Dove**: experiments/runs.jsonl:714-716, experiments/fase89bis_anatomy.json, scripts/_run_fase89bis_anatomy.py:289-294, docs/DIARIO.md:9396-9418, docs/PANCHINA.md:293-294
- **Atteso**: §2 e regola 3 di PANCHINA: ogni run registrato, ogni numero ricalcolabile da runs.jsonl. Il diario dichiara «Riproducibile: python scripts/_run_fase89bis_anatomy.py --squad-value … dettaglio in experiments/fase89bis_anatomy.json».
- **Trovato**: runs.jsonl contiene solo 3 righe per questa famiglia (2 per la fase 89, 1 per la 91), tutte PRE-fix; le rigenerazioni fatte da d5eb581 e 1ad6c30 non hanno riga. _run_fase89bis_anatomy.py non chiama mai experiment_log.append_run. L'artefatto 89-bis ha solo le chiavi anatomy/temperature/drift: manca «squad_value», quindi i numeri 1.2384, −0.0390, IC [−0.1055,+0.0205], β medio +0.115 non stanno in nessun artefatto né nel registro.
- **Come è stato accertato**: python su runs.jsonl (Counter dei config.phase: {'89':2,'91':1,'94':1}); json.load(experiments/fase89bis_anatomy.json).keys() → ['anatomy','temperature','drift']; grep append_run scripts/_run_fase89bis_anatomy.py → nessuna occorrenza.
- **Correzione**: Rieseguire i tre script col codice corrente registrando i run (aggiungere append_run a _run_fase89bis_anatomy.py ed eseguirlo con --squad-value, così il blocco finisce nell'artefatto).

**🟡 `F89-diario-tiebreak-incompleto` — Il blocco 📐 della Fase 89 cita TIEBREAK_RULES con 3 leghe: dopo l'integrazione ne contiene 5, e il DIARIO non lo dice da nessuna parte**  
*incoerenza-doc · bassa · **confermato***

- **Dove**: docs/DIARIO.md:9315-9316, src/models/season_sim.py:66-72, docs/audit_5_leghe/10_modelli_nuove_leghe.md:522
- **Atteso**: §2-bis: la formula nel blocco 📐 va verificata riga per riga contro il codice; l'estensione a bundesliga/ligue_1 (commit 327aa55) doveva riflettersi nel DIARIO.
- **Trovato**: DIARIO 9315: «TIEBREAK_RULES = {serie_a: (h2h, gd, gf), la_liga: (h2h, gd, gf), premier_league: (gd, gf)}». Il codice contiene anche bundesliga ('gd','gf','h2h') e ligue_1 ('gd','h2h','gf'). La Fase 100 del DIARIO (righe 10949+) non menziona gli spareggi: l'informazione vive solo nel commento del codice e nel report dell'audit.
- **Come è stato accertato**: sed -n '9310,9325p' docs/DIARIO.md; grep -n TIEBREAK src/models/season_sim.py; grep -n "spareggi" nella sezione Fase 100 → nessun risultato.
- **Correzione**: Aggiornare il blocco 📐 della Fase 89 con le 5 leghe e la fonte ufficiale (DFL §2 c.3 lett. c) / LFP art. 518 ter), oppure rimandare esplicitamente alla sezione della Fase 100.

**🟡 `F89-pred2627-vuoto` — La tabella «confronto col mercato 2026-27» della Fase 89 non è più ri-derivabile: l'artefatto è stato rigenerato con --skip-2627 e pred_2627 è vuoto**  
*non-verificabile · bassa · **confermato***

- **Dove**: docs/DIARIO.md:9252-9268, experiments/fase89_season_champion.json (chiave pred_2627), scripts/_run_fase89_season_champion.py:379
- **Atteso**: I 9 valori del modello citati (Inter 66.8%, Milan 2.9%, Napoli 5.7%, Arsenal 44.8%, Man City 42.9%, Man United 0.7%, Chelsea 0.8%, Barcelona 62.4%, Real Madrid 30.6%) dovrebbero stare in pred_2627.
- **Trovato**: pred_2627 = [] nell'artefatto corrente. I prezzi di mercato citati sono invece verificabili (MARKET_2627 nello script: Inter .470, Milan .116, Napoli .126, Arsenal .340, Man City .283, Man United .110, Chelsea .091, Barcelona .514, Real Madrid .409 — tutti coincidenti col diario). Valori di modello simili ma non uguali stanno in experiments/prospettico_2026_27_outright.json (Inter 0.66435, Arsenal 0.4514, Man City 0.42075), che però è un congelamento diverso (25/07, Fase 95).
- **Come è stato accertato**: json.load(experiments/fase89_season_champion.json)['pred_2627'] → lista vuota; scripts/_run_fase89_season_champion.py:388 `pred = predict_2627(...) if not args.skip_2627 else []`.
- **Correzione**: Rieseguire senza --skip-2627 (o dichiarare nel diario che la tabella 2026-27 è superata da experiments/prospettico_2026_27_outright.json, indicando quale delle due è la fotografia ufficiale).

**🟡 `F89-inversione-imprecisa` — Fase 89: «con la sola differenza reti l'ordine sarebbe esattamente invertito» — è una rotazione, non un'inversione**  
*conclusione-non-supportata · bassa · **confermato***

- **Dove**: docs/DIARIO.md:9180-9186
- **Atteso**: Ordine con classifica avulsa: Levante 16ª, Osasuna 17ª, Mallorca 18ª. Ordine per sola differenza reti (−6/−10/−14): Osasuna 16ª, Mallorca 17ª, Levante 18ª. L'inversione esatta sarebbe Mallorca-Osasuna-Levante.
- **Trovato**: Il testo dice «l'ordine sarebbe esattamente invertito». La conclusione operativa (retrocede Levante invece di Mallorca) è invece corretta.
- **Come è stato accertato**: final_table(la_liga 2526) → Levante 42 (−14), Osasuna 42 (−6), Mallorca 42 (−10) nell'ordine 16/17/18; mini-classifica avulsa ricalcolata sulle 6 partite fra le tre: Levante 7, Osasuna 5, Mallorca 3 (esattamente i numeri del diario).
- **Correzione**: Sostituire «esattamente invertito» con «ordine diverso: retrocederebbe Levante invece di Mallorca».

**🟠 `F89-numeri-non-riproducibili` — I numeri-titolo della Fase 89 nel DIARIO/CLAUDE/PISTE/PANCHINA non sono più riproducibili: l'artefatto è stato rigenerato dalla Fase 92 e nessuno li ha aggiornati (il README sì, gli altri no)**  
*numero-errato · media · ridimensionato*

- **Dove**: docs/DIARIO.md:9195, docs/DIARIO.md:9211, docs/DIARIO.md:9400, docs/DIARIO.md:9501-9506, docs/DIARIO.md:9597, CLAUDE.md:461-462, docs/PISTE.md:474, docs/PANCHINA.md:63, README.md:244
- **Atteso**: Ogni numero pubblicato deve essere ricalcolabile col codice corrente (§1.5, §2-bis). Valori riproducibili oggi (= experiments/fase89_season_champion.json, rigenerato in d5eb581): log-loss modello 1.201061, guadagno vs persistenza-2 +0.22829 IC95% [+0.00900, +0.45300], per lega SA +0.11428 / PL +0.56763 / Liga +0.00295, Brier 0.658920, punti vincitore simulato 84.73, per-lega log-loss 0.7391 / 1.3667 / 1.4974.
- **Trovato**: DIARIO 9195/9211 e 9501-9506, CLAUDE.md §6, PISTE 474 e PANCHINA 63 riportano 1.1994, +0.2299, [+0.0108,+0.4542], +0.5657/+0.1197/+0.0045, Brier 0.6584, 84.8, 0.7411/1.3651/1.4920 — i valori del run PRE-fix (runs.jsonl riga 715). Il README:244 riporta invece i valori post-fix (1.2011, +0.2283, [+0.0090,+0.4530]): lo stesso numero è citato diverso in due documenti. Il README:244 è per di più internamente misto (titolo post-fix, ma "PL 0.7411 · Liga 1.3651 · SA 1.4920", "84.8", "1.2160 > 1.1994" pre-fix).
- **Come è stato accertato**: python -c su experiments/fase89_season_champion.json → report.logloss_model=1.2010612629342141, gain_vs_persistence2=0.22828804266972905, gain_ci_persistence2=[0.009002507739049717, 0.45300221847320876]. Ri-esecuzione col codice corrente di 2 stagioni con seed del progetto: serie_a 1819 p=0.54200 e premier 2122 p=0.82370, IDENTICI all'artefatto corrente e diversi dall'artefatto pre-F92 (0.54395 / 0.82395). Causa: git show d5eb581 -- src/models/dixon_coles.py (vincolo di identificabilità su attack[seen]) + git show d5eb581 --stat che elenca la rigenerazione di experiments/fase89_season_champion.json.
- **Correzione**: Rieseguire `python scripts/_run_fase89_season_champion.py --nsim 20000` registrando il run, e allineare DIARIO 9195/9211/9501-9506/9597, CLAUDE.md:461-462, PISTE:474, PANCHINA:63 ai valori dell'artefatto (1.2011 / +0.2283 / [+0.0090,+0.4530] / +0.1143-+0.5676-+0.0030), oppure aggiungere in ognuno la nota «numeri pre-fix del prior, vedi Fase 92» come è stato fatto per le correzioni della Fase 90.
- **Verifica avversariale**: I FATTI sono tutti riprodotti: l'artefatto e' stato rigenerato in d5eb581 (Fase 92, il fix del vincolo di identificabilita' su attack[seen]) e il codice CORRENTE produce i valori nuovi, non quelli del DIARIO. Ma la severita' 'alta' non regge per due ragioni verificate: (1) NESSUNA conclusione cambia — il CI nuovo [+0.0090,+0.4530] esclude ancora lo zero, 14/24 resta, Liga resta 'nel rumore' (+0.0045 -> +0.0030), lo scarto sul log-loss e' 0.0017 nat; (2) i numeri del DIARIO NON sono 'non ri-derivabili' nel senso del §2-bis: coincidono esattamente con le righe 714-715 di runs.jsonl (logloss_model 1.19940324498676), che sono il registro ufficiale di quella fase. Il difetto reale e' quindi un'INCOERENZA fra documenti (README dice 1.2011/+0.2283, DIARIO/CLAUDE/PISTE/PANCHINA dicono 1.1994/+0.2299) piu' la staleness dopo una rigenerazione non annotata — esattamente la definizione di 'media' nel rubric. Confermata anche la miscela interna del README:244 (titolo post-fix, per-lega/84.8/1.1994 pre-fix).

<details><summary>Verifiche con esito OK su questo fronte</summary>

- Fase 89-bis, anatomia: TUTTI i numeri riprodotti dagli artefatti — 8/8 quando il titolo resta e 2/16 quando cambia, campione uscente 0/14 negli errori, favorito = campione uscente 17/24 (71%), campione nel top-3 23/24 (96%), unico rank 5 = Milan 2021-22, P(top-2) dichiarata 82.66% vs 79.17%, P(top-3) 92.2% vs 95.8%, scelta dentro il top-2 71.56% dichiarato vs 10/19 = 52.6%, fascia >70% 78.4% vs 55.6%, campione dai primi 2 dell'anno prima 18/24 = 75%, ripetizione del campione 8/24 = 33%.
- Fase 89-bis, controlli su squad_value ricalcolati dagli snapshot (non dall'artefatto): la squadra col valore rosa più alto è campione 11/24 = 46% ✓ e il rank medio del NUOVO campione è 2.31 sia col valore rosa sia col modello ✓ — entrambi esattamente come scritto.
- Fase 89-bis, deriva di forza: rieseguendo il calcolo col codice PRE-Fase 92 si riproduce l'artefatto alla quarta cifra (sd deriva 0.1895 vs 0.18948, dispersione 0.4336 vs 0.43357, rapporto 43.7% → «44%», corr 0.9032 vs 0.90322) e Leeds/Sheffield United/Sunderland sono davvero 3 delle 6 derive maggiori (+0.808, +0.643, +0.625 → «+0.81, +0.64, +0.63»).
- Fase 89, caso Liga 2025-26 verificato sullo snapshot: Levante, Osasuna e Mallorca chiudono tutte a 42 punti; la mini-classifica avulsa sulle 6 partite dà 7-5-3 esattamente come dichiarato; final_table retrocede Mallorca. Verificata anche l'affermazione «parità in vetta 0 volte su 27»: nessuna delle 27 stagioni-lega ha due squadre a pari punti al primo posto.
- TIEBREAK_RULES: l'ordine nel codice (serie_a/la_liga ('h2h','gd','gf'), premier ('gd','gf'), bundesliga ('gd','gf','h2h'), ligue_1 ('gd','h2h','gf')) coincide con quanto dichiarato nel commit 327aa55 e nel report dell'audit; verificato per COMPORTAMENTO con un caso costruito che distingue le due leghe nuove (bundesliga premia i gol fatti, ligue_1 gli scontri diretti).
- Correzioni della Fase 90: propagate ovunque. Nessun documento contiene più il numero-titolo gonfiato «+1.4521 / 24/24» presentato come risultato onesto (README:244/246, CLAUDE.md §6, PISTE:474, PANCHINA:63 riportano tutti la baseline di persistenza); i due bug Polymarket sono corretti e protetti da test (tests/test_polymarket_fetch.py: test_derby_with_shared_first_word_keeps_1x2, test_half_and_team_markets_do_not_overwrite_full_match); la coerenza rank↔champion_prob è implementata in src/models/season_sim.py:337-348 con il commento che cita l'audit.
- Coerenza interna degli artefatti: le metriche del report di experiments/fase89_season_champion.json si ricalcolano tutte dalle 24 righe per stagione (log-loss 1.201061, Brier 0.658920, hit 41.67%, dichiarato 60.07%, rank medio 1.875, punti 89.125/84.726, sovra-confidenza −18.40pp = −1.83 SE); la mia implementazione dell'ECE riproduce esattamente i valori dello script (0.058864 vecchio, 0.047882 nuovo).
- Fase 91, definizioni e potenza: 480 righe = 20 squadre × 24 stagioni-lega ✓; p_top4 = P(rank ≤ 4) e p_rel = P(rank ≥ n−2) corrispondono a is_top4/is_rel calcolati dalla classifica reale; la calibrazione top-4 ha davvero scarto massimo 1.4pp su tutte le fasce (sia nella versione pre-fix sia in quella corrente).
- tests/test_season_sim.py: 12 test verdi (`python -m pytest tests/test_season_sim.py -q`), inclusi il caso reale a tre della Liga 2025-26 e i test sulla deriva della Fase 94.
- Il codice corrente riproduce l'artefatto corrente della Fase 89 bit per bit sui casi campionati (serie_a 1819 p=0.54200, premier 2122 p=0.82370): il simulatore è deterministico e riproducibile fra processi come dichiarato (seed via zlib.crc32).

</details>

### Fasi 92-95-bis  ·  13 rilievi
**🔴 `F92bis-IC-F91-non-propagato` — «Entrambi conclusivi» sul top-4 della Fase 91: l'IC corretto dalla Fase 92-bis INCLUDE LO ZERO e la correzione non è mai arrivata nei documenti**  
*conclusione-non-supportata · alta · **confermato***

- **Dove**: docs/DIARIO.md:9622-9623; README.md:247; (numeri collegati: docs/DIARIO.md:9640-9641)
- **Atteso**: top-4 vs persistenza: guadagno +0.0274, IC95% a grappoli [-0.0006, +0.0522] → NON conclusivo (il test dei segni 19/24, p=0.0066 è ciò che regge). Retrocessione vs tasso base +0.0925 [+0.0465,+0.1341]; vs persistenza -0.0066 [-0.0364,+0.0208]; «resto della lega» 8.0% vs 9.1%.
- **Trovato**: DIARIO:9622 «Guadagno +0.2786 sul tasso base (IC95% [+0.2208, +0.3345]) e +0.0273 sulla persistenza (IC95% [+0.0037, +0.0502]): entrambi conclusivi» e README:247 identico. DIARIO:9640-9641 «+0.0875, IC95% [+0.0369, +0.1360]» e «−0.0116, IC95% [−0.0410, +0.0150]»; README:247 «resto della lega calibrato (7.3% vs 9.1%)».
- **Come è stato accertato**: L'artefatto è stato rigenerato due volte dopo la stesura della F91. `for c in 70ba37e d5eb581 1ad6c30; do git show $c:experiments/fase91_positions.json` dà: 70ba37e (F91) top4 gain_pers 0.0273 [0.0037,0.0502] / rel 0.0875 [0.0369,0.136] / -0.0116 [-0.041,0.015] / split promoted 58.68% rest 7.29%; d5eb581 (F92, fix del prior) rel 0.0925 [0.0456,0.1379] / -0.0066 / rest 7.99%; 1ad6c30 (F92-bis, bootstrap a grappoli) top4 gain_pers 0.0274 con ci_persistence [-0.000567, +0.052197] e sign_test [19,24,0.00661]. Il messaggio di commit 1ad6c30 lo dice esplicitamente («passa da "conclusivo" per IC a IC [-0.0006,+0.0522] NON conclusivo … l'etichetta era troppo forte») ma nessun .md è stato toccato: `git show 1ad6c30 -- README.md docs/DIARIO.md` mostra solo l'aggiunta delle righe 77/78 e la correzione della Fase 57.
- **Correzione**: Riscrivere DIARIO:9622-9623 e README:247 con gli IC a grappoli correnti + il test dei segni (19/24, p=0.0066), togliendo «entrambi conclusivi» per la persistenza; allineare anche i numeri della retrocessione (+0.0925 [+0.0465,+0.1341]; −0.0066 [−0.0364,+0.0208]; 8.0% vs 9.1%), che sono fermi al pre-fix del prior.

**🟠 `F92-headline-0.0165-non-riproducibile` — Dopo il fix del prior della Fase 92 il numero-bandiera del progetto è +0.016699 / 0.9799, ma README e CLAUDE.md continuano a dichiarare +0.0165 / 0.9797 (17 occorrenze)**  
*numero-errato · media · **confermato***

- **Dove**: README.md:571 (e 79, 90, 115, 496, 561, 578, …); CLAUDE.md:416; docs/DIARIO.md:9834-9836 (Risultato 5 della Fase 92)
- **Atteso**: Walk-forward ufficiale Serie A 6 stagioni al codice di HEAD: modello 0.979890, mercato 0.963191, gap +0.016699 (→ +0.0167 / 0.9799).
- **Trovato**: README.md:571 «Gap 1X2 medio attuale +0.0165 (modello 0.9797 vs mercato 0.9632)»; CLAUDE.md:416 «gap 1X2 +0.0165 in Serie A»; e la Fase 92 stessa (Risultato 5) dichiara di aver ri-verificato ESEGUENDO «0.979687 / 0.963191 / +0.016496 (il +0.0165 del README)» mentre la sua tabella di scomposizione, poche righe sopra, riporta gap totale +0.016699 — i due numeri convivono nella stessa fase senza spiegazione.
- **Come è stato accertato**: Eseguito run_backtest+compute_metrics sulle 6 stagioni 2021-2526 con la config ufficiale: media model 0.979890 / market 0.963191 / gap +0.016699. Poi mutato `penalty = _IDENTIFIABILITY_PENALTY * attack[seen].mean()**2` → `attack.mean()**2` (il codice pre-fix) e rieseguito: media 0.979687 / 0.963191 / +0.016496 — esattamente i numeri del Risultato 5. Quindi la 'riproduzione' dell'audit è pre-fix. Per stagione pre→post: 2021 0.953236→0.953514, 2122 0.985997→0.986449, 2223 0.991637→0.992169, 2324 invariata, 2425 0.969321→0.969378, 2526 0.992502→0.992403: la fase cita SOLO il 2025-26 («0.9925 → 0.9924»), l'unica che migliora, mentre l'aggregato peggiora di +0.0002. File ripristinati (git status pulito).
- **Correzione**: Ri-eseguire e aggiornare il numero-bandiera in README (0.9797→0.9799, +0.0165→+0.0167) e CLAUDE.md §6, e correggere il Risultato 5 della Fase 92 dichiarando che 0.979687/+0.016496 è il valore PRE-fix e 0.979890/+0.016699 quello post-fix. Nota di impatto: +0.0002 è la stessa scala con cui il progetto boccia le leve (es. DIARIO:2105 «base 0.9797 → +form 0.9799 = peggiora»), quindi la baseline va riallineata prima di riusare quei confronti.

**🟠 `F93-meglio-calibrati-senza-intervallo` — «Siamo MEGLIO calibrati del mercato» (0.00083 vs 0.00125) è dentro il rumore: IC a cavallo dello zero e segno che si inverte cambiando il numero di fasce**  
*conclusione-non-supportata · media · **confermato***

- **Dove**: docs/DIARIO.md:9903-9906; README.md:249
- **Atteso**: Statistica di testa con il suo intervallo (regola R7, CLAUDE.md §5-bis): il confronto rel_modello − rel_mercato = −0.00042 ha IC95% bootstrap appaiato [−0.00137, +0.00048] (include lo zero, P(modello meglio)=82%) e il pavimento di rumore sotto calibrazione perfetta con 12 fasce su n=5.083 vale 0.00049 (p95 0.00088), cioè dello stesso ordine dei due valori confrontati.
- **Trovato**: «Le nostre probabilità condizionate sono **meglio calibrate di quelle del mercato** (0.00083 contro 0.00125)» presentato come fatto, senza intervallo, e ripreso nel README con punto esclamativo («siamo meglio calibrati!»).
- **Come è stato accertato**: Ricalcolato dal CSV con la stessa funzione `murphy` dello script: 12 fasce → rel_m 0.00083 / rel_k 0.00125 (riproduce il diario). Bootstrap appaiato su 1.000 ricampionamenti delle 5.083 partite: diff media −0.00041, IC95% [−0.00137, +0.00048]. Simulazione sotto calibrazione perfetta (y~Bernoulli(p_modello), 300 repliche): rel atteso 0.00049, p95 0.00088. Sensibilità alle fasce: 25 fasce 0.00127 vs 0.00147; 50 fasce 0.00230 vs 0.00190 (SEGNO INVERTITO); 100 fasce 0.00388 vs 0.00339 (invertito).
- **Correzione**: Declassare l'affermazione: scrivere che il termine di mis-calibrazione è, per entrambi, indistinguibile dal pavimento di rumore (≤4% del deficit in ogni configurazione di fasce) e che la differenza fra i due non è conclusiva. La conclusione operativa della fase («nessuna ricalibrazione chiude il gap») NON cambia e anzi si rafforza; il termine di risoluzione è invece conclusivo (−0.00981, IC95% [−0.01246, −0.00754], verificato).

**🟠 `F93-quote-104-percento` — «Calibrazione −4%, informazione +104%»: sono quote di 0.00939, non del deficit di 0.02153 che la frase nomina**  
*conclusione-non-supportata · media · **confermato***

- **Dove**: docs/DIARIO.md:9908-9910; scripts/_run_fase93_discrimination.py:129-131
- **Atteso**: Le due componenti di Murphy dovrebbero sommare al deficit che dichiarano di scomporre (+0.02153).
- **Trovato**: (rel_m−rel_k)+(res_k−res_m) = −0.00042 + 0.00981 = 0.00939, cioè il **44%** del deficit misurato (+0.02153); il restante 56% è il residuo di discretizzazione, non attribuito. Le percentuali −4%/+104% sono normalizzate su 0.00939 e sommano a 100% dando l'impressione di esaurire il deficit.
- **Come è stato accertato**: Dal CSV: `df.c_model.mean()-df.c_market.mean() = 0.02153`. Somma delle componenti con 6/12/25/50/100 fasce: 0.00961/0.00939/0.00918/0.00901/0.00907 = 45%/44%/43%/42%/42% del deficit, stabile — non è un artefatto del binning scelto.
- **Correzione**: Riformulare: «della PARTE del deficit che la scomposizione a fasce attribuisce (0.0094 su 0.0215), la calibrazione pesa −4% e l'informazione +104%», oppure esprimere il termine di calibrazione come frazione del deficit vero (≤4%), che è comunque la lettura che sostiene la conclusione.

**🟠 `F94-sigma-differenziato-non-riproducibile` — Fase 94: il risultato ADOTTATO (σ 0.30/0.16) non è ri-derivabile da nulla di committato — lo script accetta solo uno scalare, non calcola IC, e in runs.jsonl c'è solo σ=0.28**  
*non-verificabile · media · **confermato***

- **Dove**: scripts/_run_fase94_drift.py:52,132-133,77; experiments/fase94_drift.json; experiments/runs.jsonl (record del 2026-07-25T18:31:11); docs/DIARIO.md:10061-10075 e 10118-10120; src/config.py:160-171
- **Atteso**: §2-bis punto 4: ogni numero citato ricalcolabile da runs.jsonl o da uno script `_run_*`. I numeri che hanno motivato la modifica di src/config.py sono: retrocessione +0.0095 [+0.0020,+0.0180] 15/24; campione +0.0017 [−0.0356,+0.0431] 9/24; top-4 +0.0007 [−0.0075,+0.0113] 7/24 (p=0.064); neopromosse +6.1pp→+2.8pp; ECE 0.0479→0.0387 e 0.0140→0.0203; favorito +18.4pp→+14.6pp.
- **Trovato**: `ap.add_argument("--sd", type=float)` e `evaluate(sd)` passano uno SCALARE a `simulate_season(drift_sd=sd)`: lo script non sa costruire la mappa per-squadra {promosse:0.30, altre:0.16}. `bootstrap_ci` è importato alla riga 52 e non usato mai (import morto): nessun IC, e `markets()` restituisce solo aggregati, quindi nemmeno i conteggi «meglio in X/24» sono producibili. `fase94_drift.json` contiene solo la griglia uniforme (0.0/0.08/0.12/0.15/0.18/0.22/0.28) senza IC; l'unico record in runs.jsonl per la fase 94 ha `"drift_sd": 0.28`.
- **Come è stato accertato**: grep bootstrap_ci scripts/_run_fase94_drift.py → una sola riga (l'import). Dump di fase94_drift.json: chiavi ['0.0','0.08','0.12','0.15','0.18','0.22','0.28'], ogni voce con solo spread_pct/score/markets. Scansione di runs.jsonl (725 righe) per phase=94: un solo record, config {drift_sd:0.28, grid:[...], nsim:20000}. Verificabili dal JSON solo i valori a σ=0.28 citati nel diario (campione 1.2229 ✓, top-4 0.2253 ✓) e il +18.4pp senza deriva (0.60066−0.41667 ✓) e il +6.1pp (0.54744−0.48611 ✓).
- **Correzione**: Aggiungere allo script un'opzione per il σ per-squadra (es. `--sd-promoted/--sd-other` che costruiscono `drift_sd_map`), usare davvero `bootstrap_ci` a grappoli sulle 24 stagioni-lega, emettere i conteggi per stagione, rieseguire e registrare il run adottato in runs.jsonl con la griglia completa nel JSON.

**🟠 `F92-diagnosi-non-propagata-README` — Il README ripete in tre punti, senza alcuna marcatura, la diagnosi che la Fase 92 ha dichiarato rovesciata — e si contraddice con la propria correzione a riga 280**  
*incoerenza-doc · media · **confermato***

- **Dove**: README.md:574, 580-581, 601-602, 605-607, 1482-1484 (contro README.md:280-296)
- **Atteso**: Ogni affermazione residua della lettura pre-F92 marcata come superata (come è stato fatto, correttamente, in docs/DIARIO.md:71-73 per l'indice dell'Arco 2 e in docs/DIARIO.md:1696-1712 dentro la Fase 9).
- **Trovato**: README:574 «**Per mercato** — il gap è **quasi tutto nel PAREGGIO**»; README:580-581 «Escluso il pari (mercato 12) il modello è **a livello mercato**: la debolezza è prezzare i pareggi, non stimare chi è più forte»; README:601-602 «Il "quasi-zero" del 12 regge in OGNI stagione … **Sapere chi è più forte è a livello mercato sempre**»; README:1482-1484 «è quasi tutto nel PAREGGIO (il mercato 12 senza pari ha gap +0.0020 ≈ mercato). Punta al prossimo passo mirato: correlazione dei punteggi». Nessuna nota, nessun rimando alla Fase 92 — che invece a README:280-296 dichiara la stessa frase un errore logico.
- **Come è stato accertato**: grep -n "quasi tutto nel PAREGGIO" README.md → 574, 1482; grep -n "Escluso il pari" → 580; grep -n "Sapere chi è più forte" → 602. Il blocco di correzione sta a README:280-296 («Dove vive il gap col mercato — ⚠️ diagnosi CORRETTA alla Fase 92»), in una sezione diversa e distante ~300 righe. Residui analoghi non marcati anche in docs/DIARIO.md:1618 (dentro la Fase 9, ~80 righe sopra la sua correzione), 2080 e 4896.
- **Correzione**: Inserire in ciascuno dei tre punti del README un richiamo esplicito («⚠️ lettura rovesciata, vedi Fase 92: massa-pareggio 12%, discriminazione 88%») lasciando il testo storico, come già fatto nel DIARIO; opzionalmente aggiungere la stessa marcatura a DIARIO:1618, 2080, 4896.

**🟠 `F92bis-fase-senza-documentazione` — La Fase 92-bis non esiste in nessun documento: né sezione nel DIARIO, né riga nel README, né voce in PANCHINA — la stringa «92-bis» non compare in alcun .md**  
*omissione · media · **confermato***

- **Dove**: docs/DIARIO.md (nessuna sezione ## Fase 92-bis, né voce di indice); README.md (tabella «Tutti gli esperimenti»: righe 92 e 93 consecutive); docs/PANCHINA.md
- **Atteso**: CLAUDE.md §2: ogni esperimento/decisione significativa ha voce nel DIARIO col blocco 📐, riga nel README, stato in PANCHINA. Il commit 1ad6c30 ha modificato codice di produzione (MARKET_ENGINE per-lega in src/config.py:124-147 + scripts/predict.py, guardie dati, 8 test nuovi) e ha CORRETTO un intervallo di confidenza già pubblicato (Fase 91).
- **Trovato**: `grep -rn "92-bis" --include=*.md .` non restituisce nulla. `git show 1ad6c30 -- README.md docs/DIARIO.md` mostra che il commit ha toccato i due file solo per aggiungere le righe 77/78 (arretrati di altre fasi) e correggere la Fase 57: nessuna riga su sé stesso. Nel README le righe della tabella passano da **92** a **93**.
- **Come è stato accertato**: grep -rn "92-bis" --include=*.md . → vuoto; grep -n "^| \*\*9[0-9]" README.md → 90,91,92,93,94,95,95-bis,96,97,98,99 (nessun 92-bis); grep -n "^## Fase 9" docs/DIARIO.md → 90,91,92,93,94,95,95-bis,96,97,98,99. Il contenuto del commit è consistente e verificato (vedi verificato_ok), ma non è tracciato da nessuna parte se non nel messaggio di commit.
- **Correzione**: Aggiungere la voce «Fase 92-bis» al DIARIO (con il blocco 📐 sulla mappa MARKET_ENGINE per-lega e sul bootstrap a grappoli), la riga corrispondente nel README, e — poiché ha cambiato quali leve sono attive di default su Premier/Liga nel tool — la nota in PANCHINA.

**🟡 `PANCHINA-campione-deriva-non-aggiornata` — PANCHINA ✱7 dice «Sul campione non ha effetto», ma la Fase 95-bis conclude il contrario sullo stesso mercato e non è mai entrata nella rosa**  
*incoerenza-doc · bassa · **confermato***

- **Dove**: docs/PANCHINA.md:30-35 (nota ✱7) e 65; docs/DIARIO.md:10223-10259 (Fase 95-bis)
- **Atteso**: CLAUDE.md §2: la rosa va aggiornata dopo ogni esperimento che tocca lo stato di un modello. La Fase 95-bis è un esperimento sulla deriva, sul mercato campione, con esito non nullo e dipendente dalla lega.
- **Trovato**: ✱7 (Fase 94) chiude con «Sul campione non ha effetto.», mentre la Fase 95-bis scrive «la deriva ha eccome un effetto sul campione, e il segno dipende da quanto eravamo già allineati» (KL Serie A 0.1805→0.1445, Premier 0.2418→0.2036, La Liga 0.0560→**0.0740** = peggiora). In PANCHINA non compare alcun riferimento a Fase 95 o 95-bis.
- **Come è stato accertato**: grep -n -i "deriva|drift|Fase 94|Fase 95" docs/PANCHINA.md → solo le righe 30 e 65 (Fase 94); nessuna occorrenza di 95/95-bis. I numeri della 95-bis li ho ri-derivati e confermati da experiments/prospettico_2026_27_outright.json.
- **Correzione**: Aggiornare la nota ✱7: «sul campione il backtest a 24 osservazioni non vede nulla, ma contro i prezzi Polymarket la deriva avvicina Serie A e Premier e allontana La Liga (F95-bis) — resta non adottata perché l'accordo col mercato non è un esito», e aggiungere la riga/colonna corrispondente nella matrice.

**🟡 `DIARIO-separatore-mancante-F94-F95` — Manca il separatore `---` fra la Fase 94 e la Fase 95 nel diario**  
*incoerenza-doc · bassa · **confermato***

- **Dove**: docs/DIARIO.md:10120-10121
- **Atteso**: Riga vuota + `---` + riga vuota prima di ogni `## Fase N`, come per tutte le altre fasi.
- **Trovato**: La riga «`experiments/fase94_drift.json`.» (10120) è seguita direttamente da «## Fase 95 — …» (10121), senza `---`.
- **Come è stato accertato**: sed -n '10115,10123p' docs/DIARIO.md | cat -A: l'ultima riga della Fase 94 è immediatamente seguita dall'intestazione della Fase 95; confronto con le altre fasi (es. 9992-9994, 10221-10223) dove il `---` c'è.
- **Correzione**: Inserire una riga vuota, `---`, riga vuota fra le due fasi.

**🟡 `F93-nessun-run-nel-registro` — La Fase 93 non ha alcuna riga in runs.jsonl e, a differenza delle Fasi 95/95-bis, non dichiara il perché**  
*omissione · bassa · *non contro-verificato**

- **Dove**: experiments/runs.jsonl; scripts/_run_fase93_discrimination.py:207-231; docs/DIARIO.md:9989-9992
- **Atteso**: CLAUDE.md §2: il run finisce in runs.jsonl, oppure lo si registra a mano con `experiment_log.append_run` (le Fasi 95 e 95-bis dichiarano esplicitamente «nessun run in runs.jsonl» e ne danno la ragione: dati live non versionati).
- **Trovato**: `main()` di _run_fase93_discrimination.py scrive solo CSV e JSON, non importa `experiment_log` e non registra nulla; nella scansione di runs.jsonl (725 record) non c'è alcuna voce riconducibile alla fase 93; il diario chiude con «Riproducibile: … Dataset per-partita in experiments/…» senza nominare il registro.
- **Come è stato accertato**: grep experiment_log scripts/_run_fase93_discrimination.py → nessun risultato; scansione di runs.jsonl per phase in (92,93,94,95) → solo il record phase=94 del 2026-07-25T18:31:11.
- **Correzione**: Registrare il run (18 backtest walk-forward, config e impronta dati) o dichiarare nel diario perché non è registrato, come fatto per le Fasi 95/95-bis.

**🟡 `F93-artefatti-stale-matchday` — Fase 93: CSV e JSON committati sono PRE-fix del bug `matchday`, e il JSON non contiene affatto i numeri-titolo della fase**  
*incompiuto · bassa · ridimensionato*

- **Dove**: experiments/fase93_discrimination.csv (colonna matchday); experiments/fase93_discrimination.json; scripts/_run_fase93_discrimination.py:87-90; docs/DIARIO.md:9924-9936 (Risultato 3) e 9989-9992; CLAUDE.md §4 (riga «fase93_discrimination.csv … input riutilizzabile»)
- **Atteso**: Artefatti rigenerati con lo script corretto: `matchday` = cumcount()//8+1 (max ~36-38), JSON con le fasce «giornate 1-5 / 6-12 / 13-25 / 26+» e la chiave `natura` (scomposizione di Murphy) scritta da main().
- **Trovato**: Il CSV ha `matchday` min 1 **max 134** (il vecchio rank sulle date distinte) e il JSON contiene le vecchie fasce con **3.829 righe su 5.083 (75,3%) in «ultime 10 giornate»** — cioè esattamente il difetto che il commento nel codice descrive («il rank sulle DATE distinte … schiacciava il 75% delle partite in un'unica fascia»). Il JSON ha 6 chiavi e NON ha `natura`: i numeri di Murphy (0.00083/0.05270 vs 0.00125/0.06251) e l'intera tabella «fase della stagione» del diario non stanno in alcun artefatto.
- **Come è stato accertato**: `git log -- experiments/fase93_discrimination.csv` → un solo commit, 1ad6c30 (Fase 92-bis); `git log -p --follow -- scripts/_run_fase93_discrimination.py` mostra che 773d479 (Fase 93) ha cambiato `nd.groupby("season")["date"].rank(method="dense")` in `groupby("season").cumcount()//8+1` SENZA rigenerare gli artefatti (`git show 773d479 --stat`: solo README, DIARIO, PISTE, script). Verifica sul CSV: matchday max 134; <=10: 435, 11-28: 819, >28: 3829 = identici al JSON. Ricostruendo il matchday con la formula corretta ottengo giornate 1-5 −0.00894, 6-12 −0.00635, 13-25 −0.00940, 26+ −0.00989 contro il diario −0.00829/−0.00465/−0.00957/−0.00991: la tabella del Risultato 3 non è riproducibile dagli artefatti committati.
- **Correzione**: Rieseguire `python scripts/_run_fase93_discrimination.py` e ricommittare CSV+JSON (il JSON conterrà anche `natura`); oppure, se il costo dei 18 backtest è proibitivo, ricalcolare almeno la colonna `matchday` dal CSV esistente e correggere la tabella del Risultato 3. Finché il CSV ha la colonna rotta, la riga di CLAUDE.md §4 che lo pubblicizza come «input riutilizzabile per affettare il gap» è una trappola.
- **Verifica avversariale**: La META' del rilievo regge, la sua accusa centrale NO. Regge: `git log -- experiments/fase93_discrimination.csv` da' un solo commit (1ad6c30), mentre 773d479 (Fase 93) ha cambiato la formula del matchday (`rank(method='dense')` -> `groupby('season').cumcount()//8+1`) toccando solo README/DIARIO/PISTE/script (`git show 773d479 --stat`); il CSV committato ha infatti matchday max 134 e il JSON ha le vecchie fasce 435/819/3829 e non ha la chiave `natura`. NON regge l'affermazione decisiva: «la tabella del Risultato 3 non e' riproducibile dagli artefatti committati». L'ho ricostruita e riproduce il diario alla quinta cifra. La differenza e' che il matchday va ricostruito per (LEGA, stagione) — `build()` gira una lega alla volta e poi si concatena — mentre l'auditor ha evidentemente raggruppato per sola stagione. Con il raggruppamento giusto ottengo giornate 1-5 noi 0.06387 / loro 0.07215 -> -0.00829; 6-12 0.05150/0.05615 -> -0.00465; 13-25 0.05662/0.06619 -> -0.00957; 26+ 0.04895/0.05886 -> -0.00991, cioe' ESATTAMENTE DIARIO:9934-9938. Idem per tutti gli altri numeri-titolo della fase, che il JSON non contiene ma il CSV consente di ricalcolare: Murphy 0.00083/0.05270 vs 0.00125/0.06251, deficit medio 0.02153, 58.3% di partite in cui il mercato fa meglio, P(casa|non-pari) 57.61/58.02/57.68, mismatch -0.00198, equilibrate -0.00793. Inoltre nessun numero del JSON stale e' citato nei documenti (grep di 0.0268 / 0.00983 / 0.02344: zero occorrenze). Resta dunque un solo difetto vero e circoscritto: una colonna DERIVATA obsoleta nel CSV (ricostruibile in una riga) e un JSON non rigenerato — non una fase irriproducibile, e la riga di CLAUDE.md §4 non e' «una trappola» per le altre 24 colonne, che sono corrette e post-fix.

**🟡 `F94-sigma-0.28-non-chiude` — «Per chiuderla tutta servirebbe σ≈0.28»: a σ=0.28 la compressione resta al 66° percentile (bersaglio 50°), e 0.28 è solo l'estremo della griglia**  
*conclusione-non-supportata · bassa · ridimensionato*

- **Dove**: docs/DIARIO.md:10086-10089; scripts/_run_fase94_drift.py:58 (GRID) e 103-107 (spread_score)
- **Atteso**: Il bersaglio dichiarato è il 50° percentile. Il σ che lo raggiunge non è nella griglia testata: a σ=0.28, l'estremo superiore di GRID, il percentile medio è ancora 66.06%.
- **Trovato**: «Anche col σ misurato la compressione si chiude solo in parte (83° percentile → ~76°). **Per chiuderla tutta servirebbe σ≈0.28**» — presentato come il valore che chiude la compressione; più sotto la stessa fase lo chiama, correttamente, «il σ che ottimizza la sola dispersione».
- **Come è stato accertato**: experiments/fase94_drift.json: spread_pct 0.0→0.83144, 0.18→0.76320, 0.22→0.72711, **0.28→0.66058**; `score` = |spread_pct − 0.5| = 0.16058 a 0.28, che è il minimo SOLO perché `GRID = (0.00,0.08,0.12,0.15,0.18,0.22,0.28)` si ferma lì (spread_score in scripts/_run_fase94_drift.py:103-107).
- **Correzione**: Riscrivere: «σ=0.28 è il massimo della griglia e riduce la compressione dall'83° al 66° percentile — non la chiude; per il 50° servirebbe un σ ancora maggiore, ben oltre la deriva misurata, e già a 0.28 il danno supera il beneficio (campione 1.2229, top-4 0.2253)».
- **Verifica avversariale**: Il fatto e' vero: experiments/fase94_drift.json da' spread_pct 0.83144 a sigma 0, 0.76320 a 0.18, 0.72711 a 0.22 e 0.66058 a 0.28; il bersaglio dichiarato e' il 50 percentile, quindi a 0.28 la compressione NON e' chiusa (66%, non 50%), e 0.28 e' semplicemente l'estremo superiore di GRID (scripts/_run_fase94_drift.py:58), scelto da spread_score = |percentile - 0.5| solo perche' la griglia si ferma li'. La frase di DIARIO:10086-10088 «Per chiuderla tutta servirebbe sigma≈0.28» e' quindi scorretta. Ma la severita' «media» e' eccessiva: (a) sta nel paragrafo intitolato «Onesta' su cosa NON e' stato risolto», la cui tesi — «la deriva spiega una parte della compressione, non tutta» — e' quella giusta e non cambia; (b) la stessa frase prosegue con «e a quel livello il danno supera il beneficio (campione 1.2229, top-4 0.2253)», numeri che ho verificato nel JSON (0.28: champion_logloss 1.2229…, top4 0.2253…); (c) trenta righe piu' sotto, nel blocco 📐, la stessa fase lo qualifica correttamente come «il sigma che ottimizza la sola dispersione (0.28)… la calibrazione sulla dispersione, da sola, e' il criterio sbagliato». Nessuna decisione poggia sulla frase difettosa: e' un'imprecisione locale, non una conclusione non supportata.

**🟡 `F95-artefatto-senza-produttore` — L'unico artefatto che rende verificabili le Fasi 95 e 95-bis non è prodotto né citato da alcuno script o dal diario; la riga «Riproducibile» punta a un dump non versionato**  
*non-verificabile · bassa · ridimensionato*

- **Dove**: experiments/prospettico_2026_27_outright.json; docs/DIARIO.md:10214-10221 e 10274-10277; scripts/_run_polymarket_outright.py:78-86
- **Atteso**: Il file che congela p_model_base / p_model_drift / p_polymarket dovrebbe essere scritto (o almeno citato) dallo script della fase, e le due fasi dovrebbero rimandarci per la verifica.
- **Trovato**: `grep -rn prospettico_2026_27_outright` su tutto il repo trova UNA sola occorrenza, in lavoro_aperto.md:45 («congelato (Fase 96)»): nessuno script lo scrive, il DIARIO non lo nomina. Le due fasi indicano invece `python scripts/_run_polymarket_outright.py --all [--with-drift]`, che a `load_dump()` cerca `data/polymarket/open_events_*.json` — cartella che non esiste nel repo (esce con SystemExit).
- **Come è stato accertato**: grep -rn "prospettico_2026_27_outright" . --exclude-dir=.git → solo lavoro_aperto.md:45; `git log --oneline -- experiments/prospettico_2026_27_outright.json` → 7f06c7d (aggiunto a mano con la Fase 95-bis); `ls data/polymarket/` → inesistente. Nota positiva: i prezzi sono comunque verificabili in modo indipendente da data/outright_snapshots/2026-07-25.json.
- **Correzione**: Far scrivere il congelamento a `_run_polymarket_outright.py` (flag `--freeze`) e citarlo nelle righe «Riproducibile» delle Fasi 95/95-bis, indicando che i prezzi sono ricontrollabili contro data/outright_snapshots/2026-07-25.json.
- **Verifica avversariale**: La parte di tracciabilita' regge, l'etichetta «non-verificabile» no. Regge: `grep -rn prospettico_2026_27_outright . --exclude-dir=.git` trova una sola occorrenza (lavoro_aperto.md:45), nessuno script scrive il file, `git log` lo mostra aggiunto a mano in 7f06c7d, e `ls data/polymarket` non esiste. NON regge il cuore dell'accusa: i numeri delle due fasi sono pienamente verificabili dall'artefatto committato. Ricalcolandoli ho ottenuto KL Serie A 0.1805 -> 0.1445, Premier 0.2418 -> 0.2036, La Liga 0.0560 -> 0.0740, MAE 0.0252/0.0218, 0.0265/0.0224, 0.0110/0.0120 e corr 0.956/0.963, 0.948/0.955, 0.982/0.978 — tutti identici a DIARIO:10231-10237 e alla riga 95 del README. Inoltre la riga «Riproducibile» della Fase 95 NON e' rotta: DIARIO:10218-10221 dice «python scripts/fetch_polymarket_open.py --tag Soccer poi python scripts/_run_polymarket_outright.py --all», e fetch_polymarket_open.py:294-295 scrive proprio in data/polymarket/ (default, dichiarato non versionato); la stessa riga chiude con «Diagnostico su dati LIVE: nessun run in runs.jsonl (il dump non e' versionato, cambia ogni giorno)», cioe' il progetto dichiara apertamente il limite (§1.4/§2). L'artefatto stesso dichiara la sua fonte («fonte_prezzi»: data/polymarket/open_events_20260725.json). Resta un solo difetto minore e reale: la 95-bis abbrevia la riga «Riproducibile» omettendo il passo di fetch, e nessuna delle due fasi rimanda al congelamento in experiments/. Difetto di rimando, non di verificabilita'.

<details><summary>Verifiche con esito OK su questo fronte</summary>

- SCOMPOSIZIONE FASE 92 — RI-DERIVATA ESEGUENDO su tutte e tre le leghe (`python scripts/_run_fase92_gap_decomposition.py [--league …]`): Serie A gap +0.016699 = massa-pareggio +0.002010 (12.0%) + discriminazione +0.014690 (88.0%); Premier +0.020632 = +0.001127 (5.5%) + +0.019505 (94.5%); La Liga +0.016250 = +0.002440 (15.0%) + +0.013810 (85.0%). Identici al diario (righe 9757-9770) e al README. La ricomposizione è esatta (0.576618+0.403273 = 0.979890 stampato, cioè a 6 decimali) e l'identità P(12)=1−P(X) è verificata a 4.44e-16.
- CHAIN RULE — matematicamente corretta come scritta: `LL = LL(pari/non-pari) + P(non-pari)·LL(casa vs ospite | non-pari)`; nel codice il secondo termine è `sum(-log cond)/n`, cioè già pesato da P(non-pari), e i due addendi ricompongono il totale per identità (per un pareggio il secondo termine è 0 e il primo vale −log P(X); per un non-pareggio −log(1−P(X)) + −log(P(esito)/(1−P(X))) = −log P(esito)). Il blocco 📐 del diario coincide con il codice riga per riga.
- COERENZA INCROCIATA FASE 92 ↔ FASE 93 — la somma dei `deficit` del CSV per lega, divisa per le 2.280 partite, riproduce ESATTAMENTE i termini di discriminazione della Fase 92: serie_a +0.014690, premier_league +0.019505, la_liga +0.013810 (6 decimali, tutte e tre). «I due conti si chiudono» è vero.
- FASE 93, NUMERI-TITOLO — verificati contro il CSV: 5.083 righe (5.084 col header) ✓; deficit medio +0.02153 ✓; il mercato fa meglio nel 58.3% ✓; Murphy modello 0.00083/0.05270 e mercato 0.00125/0.06251 ✓ (ricalcolati con la stessa funzione); equilibrate 0.00419 vs 0.01211 = −0.00793 ✓ e mismatch 0.10692 vs 0.10891 = −0.00198 ✓; P(casa|non-pari) 57.61% / 58.02% / 57.68% ✓; Risultato 4 dal JSON: accordo stretto +0.00134 (2.1%), disaccordo forte +0.05504 (86.9%) ✓. Confermata anche «nessuna fetta in cui siamo più informati»: 3 leghe e 6 stagioni, tutte negative (da −0.00488 a −0.01082).
- FASI 95 E 95-BIS — ogni numero ri-derivato da experiments/prospettico_2026_27_outright.json: MAE 0.0252/0.0265/0.0110, corr 0.956/0.948/0.982, KL 0.1805/0.2418/0.0560; con deriva KL 0.1445/0.2036/0.0740 (Δ −0.0360/−0.0382/+0.0179), MAE 0.0218/0.0224, corr 0.963/0.955; overround +7.2%/+5.8%/+3.2%; volumi 29k$/1,37M$/318k$; Inter 66.4 vs 47.1, Arsenal 45.1 vs 33.6, Man City 42.1 vs 27.9, Barcelona 59.3 vs 51.8, Man United 0.8 vs 10.9, Chelsea 1.0 vs 9.0, Milan 2.7 vs 11.7. I prezzi Polymarket sono confermati da una fonte indipendente nello stesso repo (data/outright_snapshots/2026-07-25.json): scarto massimo 0.00045 sulle squadre appaiate, price_sum 1.0715/1.0580/1.0325 coerenti con gli overround dichiarati.
- FASE 92, FIX E PROTEZIONI — verificati eseguendo: (a) mutando `matches["date"] < as_of_date` in `<=` in src/models/dixon_coles.py:354 il test `test_fit_ignores_matches_on_and_after_as_of_date` FALLISCE (la regola n.1 è davvero protetta; file ripristinato); (b) il vincolo di identificabilità è su `attack[seen]` (src/models/dixon_coles.py:556-585) e il test di regressione `test_promoted_prior_lands_exactly_on_prior` è presente e verde; su dati reali Serie A ho confrontato pre-fix e post-fix per 8 stagioni: le neopromosse senza partite passano da valori sparsi (−0.28…−0.39) a −0.2300 esatti; (c) lo schedule del cron è effettivamente commentato in .github/workflows/import_dataset.yml:41-42; (d) suite completa: 194 test verdi in 49s.
- FASE 92-BIS, FIX DI CODICE — tutti presenti: `MARKET_ENGINE` in src/config.py:124 con lettore per-lega a 147 e uso in scripts/predict.py; `"total"` in `_SUB_SUFFIXES` di scripts/fetch_polymarket_open.py:54 col commento dell'audit; backtest.py registra draw_balance/draw_inflation/train_window_days/drop_train_seasons (righe 295-297); test nuovi presenti e verdi (test_open_odds.py:356-383 sul value_bet_roi, test_season_sim.py sugli spareggi per-lega).
- FASE 94, MECCANISMO E ADOZIONE — l'iniezione in src/models/season_sim.py:249-268 corrisponde esattamente al blocco 📐 (attacco +ε/2, difesa −ε/2 così che il livello-gol non si sposti, perturbazione costante dentro il blocco di simulazioni e ripristino dei parametri); `DRIFT_SD = {promoted:0.30, other:0.16}` in src/config.py:171 con `drift_sd_map`; l'adozione limitata è coerente col codice (scripts/_run_fase97_relegation_market.py usa `drift=True` di default per la retrocessione, nessun path di produzione la applica a campione/top-4). Coerenza interna dei σ: 0.299/0.157 = 1.90 («1.9 volte» ✓) e la miscela 72×0.299 / 408×0.157 dà un sd pooled ≈0.185, compatibile con lo 0.1895 su 480 squadre-stagione registrato in experiments/fase89bis_anatomy.json. Verificati dal JSON anche i valori a σ=0.28 citati nel diario (campione 1.2229, top-4 0.2253), il +18.4pp del favorito senza deriva e il +6.1pp delle neopromosse.

</details>

### Fasi 96-99  ·  12 rilievi
**🟠 `F99-celle-6-vs-5` — «6 celle su 8 peggiorano con IC conclusivo» sono in realtà 5 — e lo dice la tabella della stessa Fase 99**  
*numero-errato · media · **confermato***

- **Dove**: docs/DIARIO.md:10853; README.md:256; docs/PISTE.md:283; docs/PANCHINA.md:99; lavoro_aperto.md:79; CLAUDE.md:494
- **Atteso**: cinque celle su otto (forma Poisson): corner c_trend + cartellini c_oos/c_last2/c_last/c_trend
- **Trovato**: «sei celle su otto peggiorano con IC conclusivo» (stessa formula ripetuta in 6 documenti)
- **Come è stato accertato**: Ri-eseguito `python scripts/_run_counts_level.py` (output completo salvato). Blocco «log-loss OOS», colonna `conclusivo`: SI su corners/c_trend, cards/c_oos, cards/c_last2, cards/c_last, cards/c_trend = 5 su 8 stimatori non-controllo; corners c_oos/c_last2/c_last = «no». Conteggio automatico: `conclusive SI (Poisson): 5`. La tabella del diario stesso (DIARIO.md:10842-10851) marca esattamente 5 righe «peggiora, conclusivo». Nessun altro raggruppamento dà 6: forma NB = 4 conclusive su 8; per-lega = 3 conclusive su 6.
- **Correzione**: Sostituire «6 celle su 8» → «5 celle su 8» nei sei punti citati (la conclusione — lead negativo — non cambia).

**🟠 `F97-script-inesistente` — La Fase 97 rimanda due volte a `scripts/_run_fase96_relegation_market.py`, che non esiste**  
*import-rotto · media · **confermato***

- **Dove**: docs/DIARIO.md:10435; docs/DIARIO.md:10554
- **Atteso**: scripts/_run_fase97_relegation_market.py (il file realmente presente, citato correttamente in README.md:254)
- **Trovato**: `scripts/_run_fase96_relegation_market.py` sia nel corpo della fase sia nel blocco «6) Riproducibilità»
- **Come è stato accertato**: `ls scripts/_run_fase96_relegation_market.py` → No such file or directory; `ls scripts/_run_fase97_relegation_market.py` → presente (8379 byte). Grep in repo: le uniche due occorrenze del nome sbagliato sono le due righe del diario.
- **Correzione**: Rinominare il riferimento in entrambe le righe del diario.

**🟠 `F97-riproducibilita-data` — «Il confronto è rifacibile identico» è falso: lo script legge sempre l'ULTIMO snapshot e non ha un'opzione per fissare la data**  
*conclusione-non-supportata · media · **confermato***

- **Dove**: docs/DIARIO.md:10553-10557; scripts/_run_fase97_relegation_market.py:77-78
- **Atteso**: un modo per fissare la data dell'istantanea (es. `--date 2026-07-25`), coerente con la rivendicazione «l'archivio è versionato, quindi il confronto è rifacibile identico anche quando i prezzi live saranno cambiati — al contrario della Fase 95»
- **Trovato**: `last = max(r["snapshot_date"] for r in rows)` senza parametro: con lo snapshot del 26/07 già in archivio, il comando documentato dà 16 mid invece di 17, MAE 7.36/8.77pp invece di 7.32/8.84pp e, filtrando, 8.65/10.22pp invece di 8.11/9.68pp (Leeds sparisce, Liverpool passa da 1.1% a 2.8%)
- **Come è stato accertato**: Eseguito `python scripts/_run_fase97_relegation_market.py` → «17 esiti» sostituito da «16 esiti col mid su 20», MAE con deriva 7.36 / senza 8.77, filtrato 8.65/10.22. Ri-eseguito lo stesso modulo forzando `HIST` su una copia di history.csv filtrata a `snapshot_date==2026-07-25`: riproduce ESATTAMENTE tutti i numeri del diario (17 mid, 8.84→7.32, 9.68→8.11, 87.9%→81.0% vs 61.4%, Ipswich +36.5, Coventry +26.2, Sunderland −11.9, Leeds −7.9, Forest 9.90pp, Man United 6.57pp, somme 2.92 vs 2.85).
- **Correzione**: Aggiungere `--date` (default: ultima) a `_run_fase97_relegation_market.py` e scrivere nel diario la data usata (2026-07-25); altrimenti la rivendicazione di riproducibilità va tolta.

**🟠 `F96-cartellini-vs-gialli` — La Fase 96 misura la struttura sui «cartellini» (gialli + 2×rossi) ma modella e calibra solo i GIALLI — e lo script stampa l'etichetta sbagliata**  
*incoerenza-doc · media · **confermato***

- **Dove**: docs/DIARIO.md:10293-10318 (tabelle struttura e modello); scripts/_run_outside_matrix.py:163 (`name = "CARTELLINI (gialli, rossi×2)"`) vs :127 (`ch, ca = ("HC","AC") if kind=="corners" else ("HY","AY")`)
- **Atteso**: che la σ²/μ portata come prova di «sono SOVRA-dispersi» sia quella della variabile effettivamente modellata
- **Trovato**: la colonna «cartellini μ / σ²/μ» (4.78/1.34, 3.72/1.24, 5.31/1.48) è calcolata su HY+AY+2·(HR+AR), mentre MAE 1.700 vs 1.715 e le linee O2.5/3.5/4.5 sono su HY+AY (μ 4.36 / 3.49 / 4.84); sui gialli di Serie A la dispersione marginale è 0.977, cioè SOTTO-dispersa
- **Come è stato accertato**: Calcolato con lo stesso `load_raw()`: gialli μ SA 4.362 vs cards μ 4.779; PL 3.493 vs 3.724; LL 4.844 vs 5.315. Lo stesso `_run_counts_nb.py` etichetta correttamente il blocco «CARTELLINI (gialli HY+AY, come F96)» e stampa «gialli mu 4.36 var/mu 0.977» per la Serie A, contro «cart.(+R) var/mu 1.335». L'header stampato da `_run_outside_matrix.py` («gialli, rossi×2») è quindi falso per il modello.
- **Correzione**: Correggere l'etichetta nello script e, nel diario, distinguere le due colonne (struttura sui punti-cartellino, modello sui gialli), notando che la sotto-dispersione dei gialli SA è coerente con la scoperta della F98 (0.901 condizionata).

**🟡 `F99-emivita-60g` — «60g in 8 fold» nell'emivita walk-forward: i fold a 60g sono 14 (11 corner + 3 cartellini)**  
*numero-errato · bassa · **confermato***

- **Dove**: docs/DIARIO.md:10932
- **Atteso**: 60g in 14 fold su 42 (720g in 3, quello è giusto)
- **Trovato**: «Le scelte oscillano (60g in 8 fold, 720g in 3)»
- **Come è stato accertato**: Parsing delle due tabelle «Alla RADICE … emivita scelta fold per fold» dell'output di `_run_counts_level.py`: corners Counter({60:11, 365:6, 120:3, 540:1}); cards Counter({120:6, 365:4, 720:3, 180:3, 60:3, 540:1, 270:1}); totale 42 fold, 60g=14, 720g=3.
- **Correzione**: Correggere in «60g in 14 fold su 42, 720g in 3» (rafforza, non indebolisce, l'argomento dell'oscillazione).

**🟡 `PISTE-5x-arbitro` — «−0.00308 contro i −0.00041 dell'arbitro (5×)»: il rapporto fra i due numeri citati è 7,5×**  
*numero-errato · bassa · **confermato***

- **Dove**: docs/PISTE.md:276; (formulazione analoga in docs/DIARIO.md:10755-10757 e README.md:255, «vale 5× l'arbitro»)
- **Atteso**: 0.00308/0.00041 = 7.5×; il «5×» si ottiene solo confrontando il livello con l'incremento dell'arbitro SOPRA il livello (−0.00056), che è un altro numero e non è quello citato
- **Trovato**: «la sola costante di livello valeva −0.00308 contro i −0.00041 dell'arbitro (5×)»
- **Come è stato accertato**: Ri-eseguito `scripts/_run_referee_feature.py`: blocco CONTROLLO → «BASE x c_fold (SOLO livello) −0.00308», «BASE x f_arb/c_fold (SOLO arbitro) −0.00041», «+ARBITRO vs SOLO-livello su O3.5: −0.00056». 0.00308/0.00041=7.5; 0.00308/0.00056=5.5.
- **Correzione**: Scrivere «7,5×» accanto ai due numeri citati, oppure esplicitare che il 5× è rispetto all'incremento marginale −0.00056.

**🟡 `F98-listino-38-vs-36` — La tabella dei quattro livelli somma 36, ma il listino ha 38 righe: mancano le 2 «B-limitato»**  
*omissione · bassa · **confermato***

- **Dove**: docs/DIARIO.md:10721-10731; experiments/listino_validazione.json (chiave `listino`)
- **Atteso**: A=1, A°=8, B=27, B-limitato=2 → 38 righe (le due outright: campione di stagione e retrocessione)
- **Trovato**: la tabella riporta A 1 / A° 8 / B 27 / C 7 famiglie accanto alla frase «38 mercati prezzati walk-forward»: 1+8+27 = 36
- **Come è stato accertato**: python: `Counter(r['level'] for r in json.load(...)['listino'])` → {'B':27, 'A°':8, 'B-limitato':2, 'A':1}, len=38. Le due B-limitato sono 'retrocessione (outright)' e 'campione di stagione (outright)'. Coerente col «32/36» (36 = 38 meno le 2 righe senza CI vs baseline).
- **Correzione**: Aggiungere la riga «B-limitato = 2 (outright)» alla tabella dei livelli.

**🟡 `F96-bias-002` — Il bias corner «crollato a +0.02» dopo il fix hadv+aadv=2 non è ri-derivabile: il modello spedito ha bias +0.123**  
*numero-errato · bassa · ridimensionato*

- **Dove**: docs/DIARIO.md:10327; README.md:253
- **Atteso**: il bias medio OOS del modello di conteggio della Fase 96 sui corner è +0.1234 (è lo stesso numero che la Fase 99 riporta come punto di partenza, `c=1 bias +0.12344`)
- **Trovato**: «Imposto `hadv + aadv = 2`, il bias è crollato a +0.02»
- **Come è stato accertato**: Chiamato direttamente `walk_forward(df,'corners')` di scripts/_run_outside_matrix.py: n=7050, media attesa 9.8752, media reale 9.7518, bias +0.1234. Stesso numero indipendentemente da `scripts/_run_counts_nb.py` (blocco «dispersione CONDIZIONATA…»: TUTTE bias +0.123) e da `scripts/_run_counts_level.py` (riga `corners Poisson c=1 ... bias +0.12344`). Testata anche la lettura in-sample (fit su tutte le stagioni, predizione sulle stesse): bias −0.1938, quindi nemmeno lì esce +0.02.
- **Correzione**: Correggere il diario/README con il valore misurabile (+0.12 pooled OOS) o dichiarare esplicitamente a quale diagnostica di sviluppo si riferiva il +0.02; è rilevante perché Fasi 98/99 hanno poi speso un intero giro su un bias di livello che la F96 dichiarava già azzerato.
- **Verifica avversariale**: Il numero +0.1234 è giusto (ho chiamato direttamente `walk_forward(df,'corners')`: n=7050, exp 9.8752, real 9.7518, bias +0.1234; cards +0.0424 = il `c=1 bias +0.04238` della F99), ma la tesi «il +0.02 non è ri-derivabile» è troppo forte: il +0.02 ESISTE nella stessa fase, su un'altra scala. La frase precedente cita esplicitamente le due scale — «+0.61 corner/partita (+0.07 su TUTTE le linee Over)» — e la calibrazione post-fix sui corner, nella tabella della F96 stessa, è +0.011…+0.021 (l'ho ri-ottenuta: `cal_pre` per linea = +0.0213/+0.0161/+0.0128/+0.0111). Il testo della F96 chiude infatti con «resta un lieve ottimismo (+0.01–0.02)». Quindi «+0.07 → +0.02» sulla scala-probabilità è coerente; il difetto è l'unità mancante in una frase, non un numero sbagliato propagato. Cade anche la motivazione di rilevanza dell'auditor: la F96 NON «dichiarava il bias azzerato» — dichiara per iscritto un ottimismo residuo.

**🟡 `F98-lead-vivo-README` — Il lead della Fase 98 (correzione di livello) resta marcato «✅ leva nuova» nel README e senza rimando alla smentita nel diario**  
*incoerenza-doc · bassa · ridimensionato*

- **Dove**: README.md:255 (colonna esito: «✅ leva nuova: correzione di livello dei conteggi»); docs/DIARIO.md:10754-10758
- **Atteso**: la Fase 99 prescrive essa stessa (DIARIO.md:10899-10901) che la chiusura negativa «va scritta dov'era stato annunciato (README, PISTE §7-bis, PANCHINA, lavoro_aperto.md §8)»: il punto di annuncio nel README è la riga 98 e la sezione «Cosa è cambiato davvero» della F98
- **Trovato**: README riga 98 chiude ancora con «✅ leva nuova: correzione di livello dei conteggi» senza ⚠️ né rimando; il diario F98 dice «È la leva col miglior rapporto valore/costo emersa qui — e nessuno la stava cercando» senza puntatore alla F99 (il rimando esiste solo nell'indice narrativo, DIARIO.md:239-242)
- **Come è stato accertato**: grep «deriva di livello|miglior rapporto valore/costo» su README/PISTE/PANCHINA/lavoro_aperto/CLAUDE: PISTE §7-bis (283), PANCHINA:99, lavoro_aperto:79 e CLAUDE.md:494 sono aggiornati con la bocciatura; README:255 e DIARIO:10757 no. La riga 99 del README smentisce, ma chi legge la riga 98 prende il lead per vivo.
- **Correzione**: Aggiungere in README riga 98 «⚠️ smentito dalla Fase 99» e una riga di rimando in coda alla sezione «Cosa è cambiato davvero» della Fase 98.
- **Verifica avversariale**: Il fatto è vero (README.md:255 chiude con «✅ leva nuova: correzione di livello dei conteggi» senza ⚠️), ma il difetto è molto meno grave di come è descritto, e metà del rilievo è infondato. (a) La riga IMMEDIATAMENTE successiva (README.md:256, Fase 99) si intitola «la correzione di LIVELLO dei conteggi — il lead che la Fase 98 aveva indicato come “il miglior rapporto valore/costo…”» e conclude «il lead è FALSO / ❌ lead chiuso negativo (auto-correzione della F98)»: la smentita è adiacente e cita testualmente l'annuncio. (b) La prescrizione della F99 (DIARIO.md:10899-10901) elenca README, PISTE §7-bis, PANCHINA, lavoro_aperto §8 — ed è stata eseguita in tutti e quattro (verificato: PISTE:283 «ESITO (Fase 99) — ❌ NEGATIVO, il lead era falso», PANCHINA:99 «❌ F99», lavoro_aperto:79 «chiusa NEGATIVA (F99)», README riga 99). (c) La parte sul DIARIO è contraria al metodo del progetto: il diario è cronologico, la stessa prescrizione della F99 NON lo include, e l'indice narrativo (DIARIO.md:239-242) porta il rimando. Resta solo l'opportunità (non l'obbligo) di retro-annotare la cella 98, per cui esiste un precedente sparso (README:244 riga 89 ha «numeri corretti dall'audit Fase 90») ma non una convenzione sistematica (la riga 89 non è annotata con la correzione della F98).

**🟡 `F98-listinoC-tier3` — L'artefatto del fronte 7 elenca «Tier 3 mai costruito» fra le 7 famiglie non validabili, mentre il fronte 4 della stessa fase lo costruisce e lo valida**  
*incoerenza-doc · bassa · ridimensionato*

- **Dove**: experiments/listino_validazione.json (chiave `livello_C`, voce 2); docs/DIARIO.md:10729-10731 (tabella dei livelli, «C | non validabile | 7 famiglie»)
- **Atteso**: coerenza interna alla Fase 98: il fronte 4 valida Halftime (+0.0537 [+0.0461,+0.0612]), Second Half (+0.0578) e risultato esatto (+0.1940) con IC conclusivo su 6.840 partite
- **Trovato**: livello_C: «Primo/Secondo tempo, HT/FT, gol nei 15' — … il motore NON ha una matrice per tempo: Tier 3 mai costruito»
- **Come è stato accertato**: Letto experiments/listino_validazione.json (`livello_C` è una lista di 7 voci, la seconda è quella citata) e ri-eseguito il blocco [3] di scripts/_run_polymarket_tier3.py: Halftime 1.0251 vs 1.0787 baseline, delta +0.0537 IC [+0.0461,+0.0612] CONCLUSIVO. Il diario segnala due «correzioni obbligatorie» al listino (doppie chance = identità; righe outright da riscrivere) ma non questa.
- **Correzione**: Rigenerare/annotare la voce `livello_C` («superata dal fronte 4 della stessa fase») e aggiornare il conteggio «C = 7 famiglie» nel diario.
- **Verifica avversariale**: Ho verificato la voce (`livello_C` è una lista di 7 dict, la #1 è quella citata; il testo è hard-coded in scripts/_run_listino_validazione.py:528-530) e una delle due clausole regge ancora: «il motore NON ha una matrice per tempo» è VERO oggi — `mi.price_markets` non prezza nessun mercato per tempo (grep su src/: nessuna occorrenza di frazione-primo-tempo/halftime; il ri-scalamento λ_1T=f·λ vive solo dentro scripts/_run_polymarket_tier3.py, non in src/models/). È stale solo la seconda clausola («Tier 3 mai costruito») rispetto al fronte 4 della stessa fase. Inoltre l'evidenza dell'auditor è in parte fuori bersaglio: la voce C parla di «Primo/Secondo tempo, HT/FT, gol nei 15'» e NON include il risultato esatto, che è già una riga di livello B del listino (`exact_score`, n=6840), quindi il +0.1940 non contraddice nulla. Impatto: una voce di un artefatto JSON e una cella della tabella dei livelli; tutti i documenti narrativi (README:255, PANCHINA, lavoro_aperto §6) riportano correttamente il Tier 3 come validato.

**🟡 `F96-dati-mai-estratti` — «HS/AS/HST/AST … mai estratti dal loader» è falso per HST/AST, e la «copertura 100%» non vale per `Referee`**  
*conclusione-non-supportata · bassa · ridimensionato*

- **Dove**: docs/DIARIO.md:10286-10289; README.md:253
- **Atteso**: HST/AST sono estratti da sempre (`home_sot`/`away_sot`, colonne dello snapshot, usate dal blend ufficiale shots_blend=0.75); la copertura 100% vale per HC/AC/HY/AY/HR/AR/HS/AS/HF/AF ma non per Referee (3420/10260 = 33%)
- **Trovato**: «`HC/AC`, `HY/AY/HR/AR`, `HS/AS/HST/AST`, `HF/AF`, `Referee` — copertura 100% su 10.260 partite …, mai estratti dal loader»
- **Come è stato accertato**: src/data/loader.py:262-263 `out["home_sot"] = pd.to_numeric(raw.get("HST"))` / `out["away_sot"] = ... raw.get("AST")`; `head -1 data/serie_a_matches.csv` contiene home_sot/away_sot. Conteggio non-null su `load_raw()`: tutti 10260/10260 tranne Referee 3420/10260.
- **Correzione**: Togliere HST/AST dall'elenco dei campi mai estratti e circoscrivere il «100%» ai campi che lo rispettano (la frase successiva già chiarisce il caso arbitro).
- **Verifica avversariale**: Metà del rilievo cade, metà regge. REGGE: HST/AST sono estratti dal loader da sempre — src/data/loader.py:262-263 `out["home_sot"]=pd.to_numeric(raw.get("HST"))` / `away_sot ← AST`, e `home_sot,away_sot` sono colonne dello snapshot congelato (verificato in testa a data/serie_a_matches.csv), usate dal blend ufficiale shots_blend=0.75; quindi l'elenco «mai estratti dal loader» è sbagliato per 2 campi su 11 (HS/AS invece NON sono estratti, quindi il resto della lista è corretto). CADE: la parte sul «100%» e il Referee, perché la frase IMMEDIATAMENTE successiva del diario dice già «L'arbitro è nei bundle Premier (100%); assente dai grezzi Serie A e Liga» — l'auditor lo ammette lui stesso, e per il progetto un'imprecisione chiarita nella riga dopo non è un difetto. Inoltre README.md:253 NON contiene la lista dei campi («dati mai estratti, copertura 100% su 10.260 partite»), quindi la citazione del README nel rilievo è infondata. Conteggi non-null verificati: HC/AC/HY/AY/HR/AR/HS/AS/HF/AF tutti 10260/10260, Referee 3420/10260.

**🟡 `F98-tier3-dump-non-versionato` — `_run_polymarket_tier3.py` non è eseguibile offline: l'inventario Polymarket dipende da un dump non versionato e assente**  
*non-verificabile · bassa · ridimensionato*

- **Dove**: scripts/_run_polymarket_tier3.py:88-101 (`load_dump`) e :608-616 (`main`); data/polymarket/ (assente, in .gitignore)
- **Atteso**: che i numeri-titolo del fronte 4 citati in README/PISTE/PANCHINA (4.854 eventi Soccer, 2.840 Tier 3, 65/78 con volume >1.000$) siano ri-derivabili dal repo, come rivendicato altrove per l'archivio versionato
- **Trovato**: `data/polymarket/` non esiste; `main()` chiama `load_dump()` prima di tutto e, senza dump, tenta un download di rete — i numeri d'inventario non sono riproducibili dallo snapshot congelato
- **Come è stato accertato**: `ls data/polymarket/` → No such file or directory. Ho potuto verificare i blocchi [2] e [3] solo bypassando `main()` e chiamando `load_history()`, `block_fractions()`, `block_validation()` direttamente (tutti i numeri tornano). Segnalato come NON VERIFICABILE, non come errore: i numeri d'inventario possono essere giusti.
- **Correzione**: Congelare accanto al diario le sole cifre d'inventario (o un mini-JSON versionato), oppure separare `main()` in modo che i blocchi [2]/[3] girino senza dump.
- **Verifica avversariale**: I fatti sono confermati (`ls data/polymarket` → No such file or directory; `.gitignore:22` contiene `data/polymarket/`; `main()` a scripts/_run_polymarket_tier3.py:608-616 chiama `load_dump()` come prima cosa e senza dump tenta il download), ma non è una lacuna non dichiarata: il progetto scrive apertamente e più volte che quel dump non è versionato e cambia ogni giorno — DIARIO.md:10219 «Diagnostico su dati LIVE: nessun run in runs.jsonl (il dump non è versionato, cambia ogni giorno)», data/outright_snapshots/README.md «al contrario del dump grezzo di fetch_polymarket_open.py (che sta in data/polymarket/, in .gitignore)», e DIARIO.md:10557 lo usa come termine di paragone. Per le regole del progetto un limite dichiarato non è un difetto. Resta valido un solo residuo azionabile, minore: `main()` accoppia i blocchi [2]/[3] (che sono offline e ri-derivabili — li ho ri-eseguiti bypassando main: Halftime 1.0251 vs 1.0787, Δ +0.0537 [+0.0461,+0.0612] CONCLUSIVO) al blocco [1] che richiede la rete.

<details><summary>Verifiche con esito OK su questo fronte</summary>

- Fase 98 fronte 4 — f = 0.4396 RI-DERIVATO da zero: Σ(HTHG+HTAG)/Σ(FTHG+FTAG) su 10.260 partite = 0.439639; per lega SA 0.4365 / PL 0.4464 / LL 0.4356 (identici al diario); IC bootstrap sulle 27 stagioni-lega [0.4336, 0.4457] vs [0.4338, 0.4458] dichiarato (differenza = rumore del bootstrap, lo script non fissa il seed); dispersione 1T pooled 0.9857 e corr(1T,2T) +0.0485 identici.
- Fase 98 fronte 4 — validazione storica Tier 3 ri-eseguita (blocco [3] di _run_polymarket_tier3.py): 6.840 partite; Halftime 1.0251 vs baseline 1.0787, Δ +0.0537 IC [+0.0461,+0.0612] CONCLUSIVO; Second Half +0.0578 [+0.0499,+0.0657]; risultato esatto +0.1940 [+0.1809,+0.2065]; 2T pareggio dichiarato 0.3671 vs reale 0.3427; 1T calibrato a 0.002/0.005/0.003 (<0.006). Tutti i numeri del diario, README, PISTE e PANCHINA combaciano.
- Fase 96 — script `_run_outside_matrix.py` ri-eseguito integralmente: 10.260 partite; tabella struttura identica (corner μ 9.79/10.35/9.43, σ²/μ 1.25/1.12/1.13; cartellini μ 4.78/3.72/5.31, σ²/μ 1.34/1.24/1.48; corr coi gol −0.062…−0.004); modello corner MAE 2.688 vs 2.703 R² +0.0065; cartellini 1.700 vs 1.715 R² +0.0255; calibrazione +0.005/−0.003/+0.001; arbitro: 27 arbitri ≥30 partite, medie 2.44–4.57, sd 0.513 vs banda nulla [0.158, 0.296], ampiezza netta 0.46 = 12.4% della media. Verificata anche la deriva dei corner (10.17 prime 3 stagioni → 9.72 ultime 3).
- Fase 98 fronte 1 (NB sui conteggi) — `_run_counts_nb.py` ri-eseguito: corner LL 0.6490 → 0.6480, Δ +0.00103 [+0.00062,+0.00143]; cartellini 0.6069 → 0.6060, Δ +0.00088 [+0.00033,+0.00142]; gialli Serie A var/μ condizionata 0.901 con Δ esattamente 0.00000 su tutte e tre le linee; corner O8.5 calibrazione da +0.021 a +0.005; conteggio delle celle che peggiorano con IC conclusivo = 3 su 21 (SA corner O11.5, PL cartellini O2.5 e O3.5), esattamente come dichiarato; bias Premier cartellini −0.201 e Serie A corner +0.352 confermati.
- Fase 98 fronte 2 (arbitro) — `_run_referee_feature.py` ri-eseguito: copertura Referee 3420/3420 in Premier e 0/3420 in Serie A e Liga; 2.324 partite OOS; miglior caso O3.5 Δ −0.00364 [−0.00853,+0.00133] (nessun IC esclude lo zero); costante di solo livello −0.00308 (= 85% del guadagno apparente); arbitro netto −0.00041 [−0.00511,+0.00414]; b = 0.401 [+0.096,+0.706]; componenti di varianza arbitro 3.7% / casa 2.5% / ospite 2.2% / accoppiamento 4.9%; c_fold da 1.0062 a 1.0559 in 7 fold; fattore medio applicato 1.0247; 3.1% di arbitri mai visti.
- Fase 99 — `_run_counts_level.py` ri-eseguito per intero: tutte e dieci le righe della tabella del diario combaciano cifra per cifra (bias, log-loss, Δ, IC95); emivita walk-forward corner −0.00004 [−0.00191,+0.00183] P>0 0.484 e cartellini −0.00034 [−0.00179,+0.00109] P>0 0.325; persistenza del bias corr lag-1 +0.2299 [−0.2544,+0.6715] e +0.1915 [−0.3446,+0.5830], 10/18 stesso segno su entrambi, sd 0.3558/0.3841 contro pooled +0.1387/+0.0383 (rapporti 2,6× e 10,0×); Serie A corner +0.352→+0.031 Δ +0.00271 [−0.00051,+0.00590] P>0 0.95 non conclusivo, Liga −0.00342 e Premier −0.00105 conclusivi; rottura della calibrazione cartellini +0.0047/−0.0034/+0.0008 → +0.0097/+0.0026/+0.0064; i sette bias per fold della Liga (+0.41, +0.73, −0.42, −0.27, −0.07, −0.20, −0.17) sono esatti.
- Fase 97 — tutti i numeri del confronto retrocessione riprodotti ESATTAMENTE fissando l'istantanea del 2026-07-25: 17 esiti col mid su 20; MAE 8.84 → 7.32pp e, filtrando a spread ≤5pp, 9.68 → 8.11pp; corr 0.937/0.935; neopromosse 87.9% → 81.0% contro 61.4% (+26.5 → +19.6pp); Ipswich +36.5, Coventry +26.2, Sunderland −11.9, Leeds −7.9, Crystal Palace −7.4, Brentford −6.6, Bournemouth −6.2; coda a zero (Man City 7.6% e Liverpool 1.1% dal mercato, 0.0% da noi); Forest spread 9.90pp e Man United 6.57pp; somme 2.92 (noi) vs 2.85 (mercato).
- Fase 97 — archivio outright: `data/outright_snapshots/` contiene 2026-07-25.json, 2026-07-26.json, history.csv (931 righe) e un README che documenta formato e trappole. Il contenuto conferma il censimento della fase: retrocessione solo Smarkets/Premier (mai su Polymarket), Top 2/3/4/5/6 e top-half solo Smarkets, campione su tutte e 5 le leghe da entrambe le fonti, overround Polymarket Premier 1.058 (+5.8%) e Serie A 1.0715 (+7.1%), spread mediano Smarkets Premier 0.0011 (0.11pp) contro 5.2–10.9pp sui primi contratti di Serie A. Il controllo incrociato fra borse riproduce mediana 0.12pp e massimo 5.98pp (PSG 82.5% vs 76.6%) — le 62 coppie esatte dipendono da una tabella di alias non versionata, io ne ho appaiate 49 con normalizzazione semplice.
- tests/test_outright_archive.py: 12 test passati (`python -m pytest tests/test_outright_archive.py -q`), coprono i sei bug reali dichiarati nella Fase 97 (classificazione qual_* prima di champion, mercati non esclusivi non rinormalizzati, mercati «w/o»/novelty esclusi, omonimi femminili/U21 esclusi, libri a un lato conservati, Top2 ≠ Top4) più i segnaposto e le code di stagione conclusa.
- Fase 98 fronte 7 — artefatto `experiments/listino_validazione.json` verificato: 38 righe di listino, 32 battono la baseline con IC interamente sotto zero, 0 perdono, 4 non conclusivi (Over 9.5/10.5/11.5 corner + totale dispari −0.0003); livello A = 1 (handicap asiatico, Brier 0.204399 vs 0.204409, Δ −0.0000101 IC [−0.00025,+0.00023]); A° = 8, B = 27, C = 7 famiglie; bias di livello corner del listino +0.1169 (≈ +0.117); nei 18 fold il θ ri-fittato è 1.225 in 6/6 fold Serie A e 1.000–1.150 in Premier, e φ0 = 0.000 negli ultimi 3 fold Premier — esattamente i «due fatti noti ri-scoperti» dichiarati.
- Propagazione dell'auto-correzione F98 → F99: la bocciatura è scritta in docs/PISTE.md §7-bis (pista marcata «❌ CHIUSA NEGATIVA (Fase 99)»), docs/PANCHINA.md:99 (cella ❌ F99 su tutte e tre le leghe + nota ✱8 aggiornata) e lavoro_aperto.md:79; la lista di priorità di lavoro_aperto.md §8 non contiene più la correzione di livello. CLAUDE.md §6 riassume correttamente il verdetto (a meno del conteggio delle celle, vedi finding).
- Residuo «secondo tempo mal calibrato → game-state → modello a due stadi»: registrato come pista aperta in docs/PISTE.md (§6, righe 236-241, e §18 in-play, righe 434-439) e in lavoro_aperto.md (riga 75 «resta aperto il residuo», riga 98 e priorità n.3 di §8), oltre che in PANCHINA.md:100 e nell'istantanea di CLAUDE.md — non vive solo nel diario.

</details>

### Fase 100 e gli 11 report  ·  22 rilievi
**🔴 `F100-denominatore-15788` — Il denominatore dell'audit è 15.788 ma le partite sono 16.111 (errore di 323, propagato in DIARIO, README, report 01, patch e registro correzioni)**  
*numero-errato · alta · **confermato***

- **Dove**: docs/DIARIO.md:11003; docs/DIARIO.md:11110; README.md:257; docs/audit_5_leghe/01_audit_dati.md:65,125,153,161,260,280; docs/audit_5_leghe/patch_guard_overround_APPLICATA.md:61; data/correzioni_dichiarate.csv (6 celle 'motivo')
- **Atteso**: 16.111 partite (e 16.110 quelle appaiate a Understat, quindi «16.109 su 16.110» per il confronto con la fonte indipendente)
- **Trovato**: «0 differenze (15.788 partite)», «gol confermati da fonte indipendente su 15.787 partite su 15.788», «11 celle su 15.788 partite», «Unica riga su 15.788»
- **Come è stato accertato**: pandas su tutti gli snapshot: 3420+3420+3420+2754+3097 = 16.111 righe. Gli stessi JSON dell'audit lo confermano riga per riga: audit_serie_a/premier_league/la_liga.json n_rows=3420, audit_bundesliga.json 2754, audit_ligue_1.json 3097, e i messaggi B1 dicono «su 3420 / 2754 / 3097». Il report 08 dello stesso bundle usa il numero giusto: docs/audit_5_leghe/08_buchi.md:25 dà «16.111 | 612.218» e 16.111×38 = 612.218 esatto. Nessun conteggio di colonna, né l'esclusione della stagione 2526, né la copertura Understat (16.110, caccia_understat.json) dà 15.788. Anche CLAUDE.md §5-bis usa il denominatore giusto (16.110) per lo stesso xG segnaposto che il report 01 §4.8 conta «su 15.788».
- **Correzione**: Sostituire 15.788 → 16.111 e 15.787/15.788 → 16.109/16.110 nei sei file; il claim sostanziale («0 differenze») non cambia, cambia solo il denominatore. Aggiungere un test che il totale delle righe degli snapshot sia 16.111 così che il numero non possa più divergere.

**🔴 `F100-script-cantiere-rotti` — 32 script della Fase 100 spostati in scripts/ puntano ancora a cantiere/ (cartella cancellata): non partono, la fase non è riproducibile**  
*import-rotto · alta · **confermato***

- **Dove**: scripts/applica_correzioni.py:28; scripts/audit_snapshots.py:36,41,42,50,51,80; scripts/audit_anomalie.py:53,61,62,65,66; scripts/build_new_snapshot.py:37,43,44; scripts/eda_nuove_leghe.py:28,35,37,38; scripts/ggng_contro_quote.py:99,114,115,132,133,136; scripts/stima_ou_close_nuove.py:106,107,108,114; scripts/tranche3_*.py; scripts/leve_*.py; scripts/nuovo_*.py (32 file in totale)
- **Atteso**: Dopo l'integrazione (commit 6c9b377 «smantellato il cantiere») i path dovevano puntare a data/ (snapshot, correzioni_dichiarate.csv), data/ricerca_esterna/ (ex data/ricerca), data/estimates/ (ex data/stime) e a una cartella di output esistente. CLAUDE.md §1.5 chiede che ogni numero sia rifacibile da terzi.
- **Trovato**: `DATA = ROOT / "cantiere" / "data"`, `OUT = ROOT / "cantiere" / "out"`, `SNAP_DIR{"bundesliga": ROOT/"cantiere"/"data"}`, `sys.path.insert(0, ROOT/"cantiere"/"scripts")` — tutti verso una cartella che non esiste più.
- **Come è stato accertato**: `grep -rl cantiere scripts/*.py | wc -l` → 32. Eseguito `python3 scripts/applica_correzioni.py --dry-run`: FileNotFoundError su cantiere/data/correzioni_dichiarate.csv (il file vive in data/correzioni_dichiarate.csv). Eseguito `python3 scripts/eda_nuove_leghe.py`: ModuleNotFoundError 'src' (il sys.path viene puntato a cantiere/scripts invece che a ROOT). `git log` conferma che cantiere/ è stato cancellato in 6c9b377.
- **Correzione**: Sostituire ROOT/"cantiere"/"data" → ROOT/"data", ROOT/"cantiere"/"data"/"ricerca" → ROOT/"data"/"ricerca_esterna", ROOT/"cantiere"/"data"/"stime" → ROOT/"data"/"estimates", ROOT/"cantiere"/"out" → docs/audit_5_leghe/numeri/ (o experiments/), e ROOT/"cantiere"/"scripts" → ROOT (per l'import di src) e ROOT/"scripts". Priorità a applica_correzioni.py, che la regola R3 rende obbligatorio e idempotente.

**🟠 `F100-link-rotti-indice` — Il 00_indice.md — proprio il file che documenta lo spostamento — ha 11 link rotti a report/*.md; altri 10 link rotti negli altri report**  
*incoerenza-doc · media · **confermato***

- **Dove**: docs/audit_5_leghe/00_indice.md:36-48; docs/audit_5_leghe/04_decisioni.md:168,170,214; docs/audit_5_leghe/05_tranche1.md:11,66; docs/audit_5_leghe/07_dati_corrotti.md:15,128; docs/audit_5_leghe/09_chiusura_buchi.md:339; docs/audit_5_leghe/REGOLE.md:32,96
- **Atteso**: I link devono risolvere: i report sono in docs/audit_5_leghe/*.md (come dice la tabella di mapping in cima all'indice), REGOLE.md è in docs/audit_5_leghe/REGOLE.md, correzioni_dichiarate.csv in ../../data/, la patch in ./patch_guard_overround_APPLICATA.md
- **Trovato**: `[report/01_audit_dati.md](report/01_audit_dati.md)` → docs/audit_5_leghe/report/01_audit_dati.md (inesistente), ×11; `../REGOLE.md` → docs/REGOLE.md; `../data/correzioni_dichiarate.csv` → docs/data/...; `../patch/guard_overround.md` → docs/patch/...
- **Come è stato accertato**: Script Python che estrae ogni link markdown relativo dai 12 .md di docs/audit_5_leghe/ e verifica os.path.exists: 21 link rotti su 21 target relativi non-http. Nessuno dei 21 path esiste.
- **Correzione**: Riscrivere i target: `report/NN_x.md` → `NN_x.md`; `../REGOLE.md` → `REGOLE.md`; `../data/correzioni_dichiarate.csv` → `../../data/correzioni_dichiarate.csv`; `../data/stime_ou_corrotte.csv` → `../../data/estimates/ou_open_corrotte_2017_19.csv`; `../patch/guard_overround.md` → `patch_guard_overround_APPLICATA.md`; in REGOLE.md `data/...` → `../../data/...`.

**🟠 `F100-estimates-readme-stale` — data/estimates/README.md descrive ancora la stima O/U a 3 leghe, 7.978 partite di fit e MAE 0.012, in contraddizione con DATI.md, README e il file stesso (3.638 righe, 5 leghe, 12.457, 0.014)**  
*incoerenza-doc · media · **confermato***

- **Dove**: data/estimates/README.md:29,38,43,59 (contro docs/DATI.md:230 e README.md:257)
- **Atteso**: «5 leghe, 3.638 righe; fit pooled su 12.457 partite; MAE ~0.014 nel REGIME D'USO (~0.012 in interpolazione)», come già scritto in docs/DATI.md:230 e nella riga 100 del README
- **Trovato**: «In quelle 2 stagioni (Serie A, Premier League, La Liga)», «fittata pooled su 7.978 partite», «MAE vs chiusura vera (prob.) | ~0.012», e §squad_value «restano 13 celle» mentre il CSV è vuoto (0 righe)
- **Come è stato accertato**: pandas: data/estimates/ou_close_2017_19.csv ha 3.638 righe su 5 leghe (bundesliga 604, la_liga 756, ligue_1 758, premier 760, serie_a 760); stima_ou_close_nuove.json dà n_fit=12457 e mae_atteso_regime_uso {bundesliga 0.0143, ligue_1 0.0125}; runs.jsonl (2026-07-26T14:12:43) registra expected_mae_wf 0.014 coi coefficienti nuovi. squad_value_2017_26.csv: 0 righe. Le sezioni più recenti dello stesso README (ou_open_corrotte, celle_residue) SONO aggiornate: l'aggiornamento è stato parziale.
- **Correzione**: Aggiornare la sezione `ou_close_2017_19.csv` di data/estimates/README.md (5 leghe, 3.638 righe, 12.457 di fit, MAE 0.014 regime d'uso / 0.012 interpolazione) e la sezione squad_value (0 righe, non 13). Verificare anche che il CSV porti davvero le due colonne di errore che 09_chiusura_buchi.md:213 dichiara «scritte riga per riga»: oggi il CSV ha solo 6 colonne, senza errore.

**🟠 `F100-piste-non-aggiornate` — docs/PISTE.md non è stato aggiornato: la pista 16 dichiara ancora che le quote GG/NG «NON esistono in nessun archivio» e la pista 19 dà la chiusura O/U 2017-19 «da procurare», entrambe smentite dalla Fase 100**  
*omissione · media · **confermato***

- **Dove**: docs/PISTE.md:407-412 (pista 16), docs/PISTE.md:442-444 (pista 19), docs/PISTE.md:11 (header «Ultimo aggiornamento: Fase 89»)
- **Atteso**: CLAUDE.md §2 impone di aggiornare PISTE.md «se l'esperimento apre, prova o chiude una pista». La pista 16 è chiusa (quote GG/NG reali trovate e misurate: il mercato è informativo, non lo battiamo); la pista 19 è chiusa positiva ma con dato non inserito.
- **Trovato**: Pista 16: «Dato: NON esiste in nessun archivio (verificato); solo raccolta da oggi in avanti» + «il GG/NG è l'unico mercato senza tetto di efficienza dimostrato (principio §1.8)». Pista 19: «Dato: da procurare», «Stato (Fase 73)».
- **Come è stato accertato**: Le quote GG/NG di chiusura 1xBet sono versionate in repo: 15 file data/ricerca_esterna/footiqo_*.json, 5.377 partite (contate con python). docs/CACCIA_OU_2017_19.md:1 è già intitolato «CHIUSA: il dato è stato trovato». CLAUDE.md §1.8 barra la premessa. PISTE.md è il file che CLAUDE.md dichiara prevalente su lavoro_aperto.md, quindi la divergenza non è innocua.
- **Correzione**: Marcare la pista 16 CHIUSA con l'esito (log-loss book 0.6840 vs baseline 0.6921 su 5.337 partite; il nostro prezzo pareggia, il DC perde +0.0104) e la pista 19 CHIUSA rimandando a CACCIA_OU_2017_19.md; aggiornare l'header a Fase 100.

**🟠 `F100-premessa-ggng-non-propagata` — lavoro_aperto.md e newseason.md presentano ancora come valida la premessa GG/NG che la Fase 100 ha fatto cadere**  
*conclusione-non-supportata · media · **confermato***

- **Dove**: lavoro_aperto.md:210-218 (§6.3); newseason.md:203-212 (§8.4)
- **Atteso**: Coerenza con CLAUDE.md §1.8, dove la frase è barrata (~~...~~) e sostituita da «PREMESSA CADUTA»
- **Trovato**: «Il CLAUDE.md §1.8 dice che il GG/NG è l'unico mercato senza quote nei dati … l'unico con spazio non ancora chiuso»; newseason.md aggiunge «fra una stagione avremo il primo campione di quote GG/NG della storia del progetto»
- **Come è stato accertato**: grep su tutti i documenti vivi: CLAUDE.md:45-47 barra la frase; docs/DIARIO.md:11016 la dichiara caduta; lavoro_aperto.md:214 e newseason.md:205-207 la citano come corrente. Il «primo campione di quote GG/NG» esiste già: 5.377 righe in data/ricerca_esterna/, misurate in docs/audit_5_leghe/11_ggng.md. I due file sono stati committati (6c2e0f7, 10292a5) PRIMA dei 5 commit di integrazione e non toccati dopo.
- **Correzione**: In entrambi i file sostituire la motivazione: la raccolta prospettica Polymarket resta utile (book diverso, stagione recente), ma non perché «non abbiamo quote» — abbiamo 3 stagioni × 5 leghe di chiusura 1xBet e la risposta è già misurata.

**🟠 `F100-dati-md-buchi` — docs/DATI.md, che si dichiara «mappa unica di TUTTI i dati», non censisce data/ricerca_esterna/ e conserva due voci smentite dalla Fase 100**  
*omissione · media · **confermato***

- **Dove**: docs/DATI.md:251 («la caccia al dato vero di chiusura resta aperta»), docs/DATI.md:260 («GG/NG storico: molto più incerto, servirebbe una validazione esterna»), docs/DATI.md:6 («Ultimo aggiornamento: Fase 73»)
- **Atteso**: CLAUDE.md §5: DATI.md è il «catalogo completo di tutti i dati (reali e stimati) — da aggiornare a ogni modifica dei dati». data/ricerca_esterna/ (86 file versionati, incluse le quote di chiusura 1xBet 1X2+O/U completo+GG/NG per 5.377 partite e il manifesto SHA256 delle 90 fonti) è un blocco di dati REALI nuovo e non compare.
- **Trovato**: Zero occorrenze di «footiqo», «1xBet» o «ricerca_esterna» in docs/DATI.md; la caccia O/U è data per aperta mentre CACCIA_OU_2017_19.md:1 la dichiara chiusa; il GG/NG storico è dato per non validato mentre 11_ggng.md lo ha validato.
- **Come è stato accertato**: grep -in 'footiqo|ricerca_esterna|1xbet' docs/DATI.md → nessun risultato. `ls data/ricerca_esterna | wc -l` → 86. Il resto di DATI.md È aggiornato alla Fase 100 (righe 24-25 con 2754/3097, riga 230 con 3638/12.457/0.014, riga 63 con le 11 linee O/U svuotate), quindi l'omissione è selettiva, non un file dimenticato.
- **Correzione**: Aggiungere a DATI.md una sezione «§5-ter · Dati di ricerca esterna (data/ricerca_esterna/)» con natura (chiusura 1xBet, un solo book, NON negli snapshot e perché), copertura (5 leghe × 3 stagioni, 5.377 righe) e uso lecito (verifica/ricerca); correggere le righe 251 e 260 e l'header di riga 6.

**🟠 `F100-otto-anomalie` — «8 anomalie reali, tutte nella fonte» non è sostenuto dal report che riassume: una delle otto è un falso positivo ritirato e un'altra è un difetto NOSTRO, non della fonte**  
*conclusione-non-supportata · media · **confermato***

- **Dove**: docs/DIARIO.md:11003-11004; README.md:257; docs/audit_5_leghe/00_indice.md:36; contro docs/audit_5_leghe/01_audit_dati.md:10 e :87
- **Atteso**: 7 anomalie reali (4.1, 4.2, 4.3, 4.5, 4.7, 4.8 nella fonte + 4.6 nostra), di cui 6 nella fonte e 1 nella nostra pipeline
- **Trovato**: «Trovate 8 anomalie reali, tutte nella fonte, non nostre»
- **Come è stato accertato**: 01_audit_dati.md ha 8 sottosezioni §4.1-§4.8, ma §4.4 è intitolata «Bielefeld-Leverkusen: NON era un errore — falso positivo, ritirato» (e data/correzioni_dichiarate.csv registra quelle due righe con stato='ritirata'), quindi non è un'anomalia; §4.6 «Ordine delle colonne diverso tra snapshot» è un difetto dei NOSTRI snapshot («loader.refresh_odds conserva l'ordine di ciascun file, quindi la divergenza si perpetua»), non della fonte. Lo stesso report, nel verdetto di riga 10, dice «7 anomalie reali … 2 richiedono un intervento, 5 vanno dichiarate».
- **Correzione**: Uniformare a «7 anomalie reali: 6 nella fonte + 1 nostra (ordine colonne, poi corretto); un ottavo caso segnalato dall'audit si è rivelato un falso positivo ed è stato ritirato». Correggere anche il titolo di §4 del report 01, che dice «Le 8 anomalie trovate (tutte reali, tutte nella fonte)».

**🟠 `F100-runs-jsonl` — La Fase 100 è di fatto non registrata in experiments/runs.jsonl, contro la checklist §2 del CLAUDE.md e la regola 3 della PANCHINA**  
*incompiuto · media · **confermato***

- **Dove**: experiments/runs.jsonl (725 righe; solo 12 con timestamp 24-26 luglio, 2 sole citano le leghe nuove)
- **Atteso**: «Registro esperimenti — verifica che il run sia finito in experiments/runs.jsonl … Se hai fatto un esperimento a mano, registralo comunque via experiment_log.append_run» (CLAUDE.md §2); PANCHINA.md:29 «i numeri devono essere ricalcolabili da runs.jsonl (regola Fase 15)»
- **Trovato**: Su 725 run, 1 sola contiene 'bundesliga' e 1 'ligue_1' (i due tracer del 26/07 alle 14:05) e 8 run totali il 26/07; tutti i risultati dei report 06/10/11 (tracer 5 leghe, griglie θ e φ su 25 mercati, bakeoff O/U, GG/NG, calibrazione, mercato campione) vivono solo in docs/audit_5_leghe/numeri/*.json
- **Come è stato accertato**: Conteggio per ora sui timestamp di runs.jsonl: 2026-07-24T18 ×1, T22 ×2, 2026-07-25T18 ×1, 2026-07-26T14 ×8. Ricerca testuale nelle 725 righe: 'bundesliga' 1, 'ligue_1' 1, 'ggng' 12 (ma sono chiavi di metrica di fasi precedenti, non run della Fase 100).
- **Correzione**: O registrare a posteriori i run principali della Fase 100 via experiment_log.append_run (config + metriche + commit + impronta dati), oppure dichiarare esplicitamente in DIARIO/PANCHINA che per questa fase la fonte grezza è docs/audit_5_leghe/numeri/ e allineare la regola 3 della PANCHINA.

**🟡 `F100-report11-riga-c` — Nel report 11 la riga (c) del confronto DC-vs-book non torna: 0.6934 − 0.6840 = 0.0094, non +0.01036**  
*numero-errato · bassa · **confermato***

- **Dove**: docs/audit_5_leghe/11_ggng.md, tabella §3, riga «c | DC gol+xG walk-forward»
- **Atteso**: Riferimento 0.6830 (il log-loss del book sulle stesse 3.512 partite), che dà esattamente 0.6934 − 0.6830 = +0.01036
- **Trovato**: «0.6934 | 0.6840 | +0.01036 | [+0.00632, +0.01454] | 3.512»
- **Come è stato accertato**: ggng_contro_quote.json, D2_nostro_prezzo_vs_book → «tutte e 3 le stagioni» → c_DC_gol+xG_walkforward: ll_a=0.69340, ll_b=0.68304, delta=+0.010360. Il 0.6840 è il log-loss del book su tutte e 5.337 le righe, non sul sottocampione del DC.
- **Correzione**: Sostituire la colonna «riferimento» della riga (c) con 0.6830 e aggiungere una nota che il DC copre solo 2018-19 e 2019-20 (il 2017-18 non ha storico), quindi il riferimento è ricalcolato sul suo sottocampione. Il Δ e il CI sono corretti e non cambiano.

**🟡 `F100-patch-celle-vs-righe` — La patch dell'overround dice «11 celle» dove si tratta di 11 righe = 22 celle (il report 05, sulle stesse righe, conta correttamente 16 celle per 8 righe)**  
*numero-errato · bassa · **confermato***

- **Dove**: docs/audit_5_leghe/patch_guard_overround_APPLICATA.md:61; contro docs/audit_5_leghe/05_tranche1.md:29
- **Atteso**: «11 righe (22 celle): 3 La Liga, 6 Bundesliga, 2 Ligue 1», coerente con la regola dichiarata «il mercato si scarta IN BLOCCO (mai un solo lato)»
- **Trovato**: «11 celle su 15.788 partite (0.07%) passano da valore impossibile a NaN dichiarato: 3 La Liga, 6 Bundesliga, 2 Ligue 1»
- **Come è stato accertato**: Il report 05 §1.1 elenca 8 righe e conclude «16 celle a NaN» (8×2, over+under): la stessa contabilità applicata a 11 righe dà 22 celle. Il DIARIO usa invece il termine correttamente («il guard cambia 6 celle», cioè le 3 righe La Liga × 2 colonne — verificato: la_liga odds_over25_open passa da 3420 a 3417 valori non-nulli).
- **Correzione**: Correggere in «11 righe / 22 celle». Il tasso 0.07% è comunque riferito alle righe, non alle celle.

**🟡 `F100-15-25-percento` — Il blocco 📐 del diario dichiara che l'errore nel regime d'uso è «il 15-25% più alto»: i numeri dello stesso paragrafo danno +15% e +10%**  
*numero-errato · bassa · **confermato***

- **Dove**: docs/DIARIO.md, Fase 100, blocco «📐 Il modello in dettaglio», paragrafo «Lo stimatore della chiusura O/U»; stesso claim in docs/DATI.md:230
- **Atteso**: «il 10-15% più alto» (0.0143/0.0124 = +15.3%; 0.0125/0.0114 = +9.6%)
- **Trovato**: «l'errore è 0.0143 in Bundesliga e 0.0125 in Ligue 1, il 15-25% più alto»
- **Come è stato accertato**: docs/audit_5_leghe/09_chiusura_buchi.md:209-212 dà la tabella esplicita: bundesliga 0.0143 regime d'uso contro 0.0124 in interpolazione, ligue_1 0.0125 contro 0.0114. Anche prendendo come base il 0.012 storicamente pubblicato si ottiene +19% e +4%, mai 15-25%.
- **Correzione**: Sostituire «15-25%» con «10-15%» in docs/DIARIO.md e docs/DATI.md:230, oppure esplicitare i due rapporti lega per lega.

**🟡 `F100-delta-senza-derivazione` — Il blocco 📐 del diario dà δ = 0.28 e 0.19 per le due leghe NUOVE senza la derivazione ln(x/y), che lo standard §2-bis impone esplicitamente**  
*omissione · bassa · **confermato***

- **Dove**: docs/DIARIO.md, Fase 100, tabella dei δ nel blocco 📐; src/config.py:78,86
- **Atteso**: CLAUDE.md §2-bis punto 2: «Non 'δ ≈ 0.23' ma 'δ = ln(1.36/1.08) = 0.230'». Le righe Serie A e La Liga della stessa tabella hanno la derivazione; le due leghe che la fase introduce no.
- **Trovato**: «Bundesliga | 0.28 | promosse tedesche più deboli della media» e «Ligue 1 | 0.19 | direzione opposta»; src/config.py commenta «δ = ln(gol lega / gol promosse) ≈ 0.277» senza i due numeri
- **Come è stato accertato**: Il dato esiste ed è corretto: docs/audit_5_leghe/03_nuove_leghe.md:148-149 dà ln(1.5608/1.1834)=0.2768 e ln(1.3710/1.1358)=0.1882. Ricalcolato in prima persona dagli snapshot (gol medi per squadra-gara di lega vs neopromosse alla prima stagione): Bundesliga 1.5608/1.1834 → 0.2768 su 17 promosse e 578 gare-squadra; Ligue 1 1.3710/1.1358 → 0.1882 su 19 promosse e 670 gare-squadra. Coincidono a 4 decimali.
- **Correzione**: Riportare nella tabella del diario e nei commenti di src/config.py le due frazioni esplicite, come già fatto per Serie A, Premier e La Liga.

**🟡 `F100-sei-sigma` — Il «~6 σ oltre la mediana sana» che motiva ORR_MAX = 1.12 non si riproduce su nessuna delle basi plausibili (5.0 σ, 9.3 σ o 15.4 σ)**  
*non-verificabile · bassa · **confermato***

- **Dove**: docs/DIARIO.md, Fase 100, blocco 📐 «Il guard sull'overround»; docs/audit_5_leghe/01_audit_dati.md:118; docs/audit_5_leghe/patch_guard_overround_APPLICATA.md:36
- **Atteso**: Un σ dichiarato con la sua base (quale epoca, prima o dopo la pulizia)
- **Trovato**: «1.12 sta ~6 σ oltre la mediana sana»
- **Come è stato accertato**: Calcolato sugli snapshot attuali: era Avg (2019-20+), n=12.457, mediana 1.0507, sd 0.00743 → (1.12−1.0507)/sd = 9.3 σ. Era BbAv 2017-19 dopo il guard, n=3.640, sd 0.00420 → 15.4 σ. Era BbAv PRIMA del guard (rimettendo le 11 righe corrotte), n=3.651, mediana 1.0554, sd 0.01283 → 5.0 σ. Nessuna dà 6. L'argomento sostanziale regge comunque: il massimo mai osservato nell'era Avg è 1.0765 (verificato: n=12.457, max 1.0765 — esattamente il numero dichiarato), quindi 1.12 non può scartare una riga buona.
- **Correzione**: Sostituire con la formulazione verificabile e più forte: «1.12 sta 4 punti percentuali sopra il massimo mai osservato in 12.457 righe dell'era Avg (1.0765), e 9 sd oltre la mediana di quella distribuzione».

**🟡 `F100-indice-riga-05` — Il riassunto del report 05 nell'indice dichiara «1 xG impossibile a NaN dichiarato», mentre il report 05 dice che quella correzione è stata RITIRATA**  
*incoerenza-doc · bassa · **confermato***

- **Dove**: docs/audit_5_leghe/00_indice.md:41; contro docs/audit_5_leghe/05_tranche1.md:33-45 (§1.2)
- **Atteso**: «8 linee O/U impossibili a NaN; la correzione su un xG “impossibile” è stata ritirata (era un autogol)»
- **Trovato**: «8 linee O/U impossibili e 1 xG impossibile a NaN dichiarato; audit avversariale a 0 anomalie sulle leghe nuove»
- **Come è stato accertato**: 05_tranche1.md §1.2 è intitolato «Un xG “impossibile” che impossibile non era → correzione RITIRATA», e il suo §1.3 riporta «xG impossibili 0 (su 5 leghe, con la verifica degli autogol)». data/correzioni_dichiarate.csv contiene le due righe Bielefeld con stato='ritirata' più due righe di ripristino a 0.0. L'unico xG davvero portato a NaN è il segnaposto Holstein Kiel-Bochum, che è del 25/07 e appartiene al report 01 §4.8, non alla tranche 1.
- **Correzione**: Correggere la riga 41 dell'indice.

**🟡 `F100-report02-footiqo` — Il report 02 chiude la via «dataset di terzi» citando footiqo come limitato alla stagione in corso; il report 09 vi trova poi il dato completo, e il report 02 non porta alcuna nota di rettifica**  
*incoerenza-doc · bassa · **confermato***

- **Dove**: docs/audit_5_leghe/02_stime.md:33; contro docs/audit_5_leghe/09_chiusura_buchi.md:58-59
- **Atteso**: Una nota inline come quelle già usate altrove nel bundle («⚠️ questa voce è stata corretta dopo un approfondimento», 01_audit_dati.md §4.4), oppure l'inclusione del report 02 nell'avvertenza dell'indice
- **Trovato**: «Footiqo: quote di sola chiusura 1xBet, tier gratuito limitato alla stagione in corso» dato come motivo di chiusura della via, senza correzione
- **Come è stato accertato**: 09_chiusura_buchi.md:58 documenta «Scaricate 5 leghe × 3 stagioni: 3.652 partite su 3.652 per la finestra bersaglio, copertura 100%», verificato in prima persona contando i 15 file data/ricerca_esterna/footiqo_*.json (760×4 + 612 = 3.652 nella finestra 2017-19, 5.377 in totale). L'avvertenza di 00_indice.md:30 copre solo i report 09 e 10.
- **Correzione**: Aggiungere in 02_stime.md:33 una riga «→ SUPERATO dal report 9 §2.1: l'endpoint storico esiste ed è permesso dal robots.txt» ed estendere l'avvertenza dell'indice al report 02.

**🟡 `F100-market-engine-2-leghe` — src/config.py: LEAGUE_CONFIGS ha 5 leghe, MARKET_ENGINE solo 3 — Bundesliga e Ligue 1 non hanno una voce esplicita**  
*omissione · bassa · **confermato***

- **Dove**: src/config.py:126-141 (MARKET_ENGINE) contro src/config.py:89-95 (LEAGUE_CONFIGS)
- **Atteso**: CLAUDE.md §4/§7: «nuova lega = nuova voce, non codice». Il commento di MARKET_ENGINE elenca esplicitamente la scelta di ogni lega («Premier — motore LISCIO … La Liga — motore LISCIO»): le due leghe nuove andrebbero dichiarate lì con l'esito misurato.
- **Trovato**: MARKET_ENGINE contiene solo serie_a, premier_league, la_liga; bundesliga e ligue_1 cadono sul fallback di market_engine()
- **Come è stato accertato**: Lettura di src/config.py. Non è un bug funzionale: il fallback restituisce il motore liscio (dp_theta=None, phi0=0, sharpen_1x2=False), che è esattamente ciò che la Fase 100 ha misurato come corretto per le due leghe (router θ 0/25, φ35 e dp_lvl bocciati). Ma la scelta è implicita invece che dichiarata, e la §7 vuole una voce per lega.
- **Correzione**: Aggiungere due voci esplicite bundesliga/ligue_1 col motore liscio e il commento del perché (θ MLE 1.080/1.103, valle 6× più piatta della Serie A; φ0 fittato ≈ 0 in Ligue 1), così che la scelta sia leggibile e non dipenda dal default.

**🟡 `F100-report08-preguard` — Il censimento dei buchi del report 08 è pre-guard: le celle vuote oggi sono 7.359 e le residue 55, non 7.353 e 49**  
*incoerenza-doc · bassa · **confermato***

- **Dove**: docs/audit_5_leghe/08_buchi.md:25
- **Atteso**: Una nota che il conteggio è antecedente all'applicazione del guard sull'overround alle 3 righe La Liga (integrazione 2/3, commit ec85314)
- **Trovato**: «| totale | 16.111 | 612.218 | 7.353 | 7.304 | 49 |»
- **Come è stato accertato**: pandas su tutti gli snapshot: 612.218 celle totali (= 16.111 × 38, corretto), 7.359 NaN, di cui 7.304 sono odds_over25/odds_under25 del 2017-19 (612×2 + 760×2×4) → residue 55. La differenza di 6 è esattamente il guard sulle 3 righe La Liga (Alaves-Real Madrid, Eibar-Real Madrid, Leganes-Betis) × 2 colonne, che il report stesso raccomandava.
- **Correzione**: Aggiungere una riga di nota al report 08 («conteggio al 25/07, prima dell'applicazione del guard: dopo l'integrazione 7.359 / 55») oppure aggiornare la tabella.

**🟡 `F100-theta-liga-non-propagato` — La riconciliazione del θ La Liga/Premier del report 10 non è arrivata in README/DIARIO, dove restano i valori 1.097 e 1.069 accanto ai nuovi 1.242 e 1.085 senza spiegazione**  
*incoerenza-doc · bassa · **confermato***

- **Dove**: docs/audit_5_leghe/10_modelli_nuove_leghe.md:110-122; README.md:204 (Fase 53) e README.md:234 (Fase 81)
- **Atteso**: Una nota che i due numeri non sono confrontabili (media di 8 fit espandenti vs pooled) e che la ri-derivazione dà 1.103 e 1.075, non 1.097 e 1.069
- **Trovato**: README riga 204: «Premier 1.069 < Liga 1.097 < Serie A 1.205»; riga 234: «testava il θ da MLE-punteggi (1.097)». Il diario della Fase 100 dà 1.085 / 1.242 / 1.232 senza raccordo.
- **Come è stato accertato**: Report 10 §2.2(b): «quel numero è la media di 8 fit MLE a finestra espandente, non un fit unico. Riprodotto: 1.103 per la Liga e 1.075 per la Premier (pubblicato 1.069). Il pooled sulla stessa finestra a 9 stagioni dà 1.199 … due terzi del divario sono l'aggregazione dello stimatore, un terzo la finestra». I θ pooled della Fase 100 sono verificati esatti: tranche3_market_tracer.json theta_pooled serie_a 1.2324, la_liga 1.2420, premier 1.0853, bundesliga 1.0796, ligue_1 1.1025.
- **Correzione**: Aggiungere una nota al blocco 📐 della Fase 100 (o alle righe 204/234 del README) che spiega la differenza fra θ da media di fit espandenti e θ pooled, con la scomposizione 2/3–1/3 già misurata nel report 10.

**🟡 `F100-report06-vs-10-phi35` — Sullo stato della φ35 in Bundesliga il report 06 conclude «resta in panchina», il report 10 e la PANCHINA la danno bocciata**  
*incoerenza-doc · bassa · **confermato***

- **Dove**: docs/audit_5_leghe/06_tranche3.md:155-157; contro docs/audit_5_leghe/10_modelli_nuove_leghe.md:140 e docs/PANCHINA.md:60
- **Atteso**: Coerenza fra i due report o una nota in 06 che rimanda alla misura più recente
- **Trovato**: 06: «In Bundesliga il segno è giusto e la grandezza plausibile, ma con 1.836 partite il CI non conclude: la leva resta in panchina». 10 e PANCHINA: ❌ bocciata («peggiora la doppia 1X»).
- **Come è stato accertato**: I due numeri sono entrambi corretti ma vengono da protocolli diversi: tranche3_mercati.json (φ0/κ fittati per MLE, LOSO) dà per bundesliga dc_1x guadagno −2.5e-05, CI [−0.00130, +0.00128], verdetto «nel rumore»; il report 10 §3 usa una griglia bidimensionale di 341 punti e ottiene doppia 1X Δ −0.00076, CI [−0.0013, −0.0003], «peggiora». L'avvertenza dell'indice segnala i report 09/10 come quelli con ritiri, non il 06 come superato.
- **Correzione**: Aggiungere in 06_tranche3.md una nota «→ misura più fine nel report 10 §3 (griglia 341 punti): la doppia 1X peggiora con CI conclusivo, da cui il ❌ in PANCHINA».

**🟡 `F100-claude-ggng-campione` — CLAUDE.md §1.8 attacca il campione sbagliato ai numeri GG/NG: 0.6840/0.6921 sono misurati su 5.337 partite (3 stagioni), non sulle 3.652 del 2017-19 che la stessa frase cita**  
*numero-errato · bassa · ridimensionato*

- **Dove**: CLAUDE.md §1.8 (blocco «PREMESSA CADUTA», righe ~46-58)
- **Atteso**: «3.652 partite del 2017-19» oppure «5.337 partite su 3 stagioni», ma i numeri 0.6840 / 0.6921 / +0.0104 vanno riferiti al campione su cui sono stati calcolati (5.337 e, per il DC, 3.512)
- **Trovato**: «…3.652 partite del 2017-19 su tutte e 5 le leghe … Risposta: il mercato GG/NG è informativo (log-loss 0.6840 contro 0.6921 di baseline, CI conclusivo)»
- **Come è stato accertato**: ggng_contro_quote.json: lucchetti.n_finale = 5337 (1718: 1825, 1819: 1825, 1920: 1687); D1 GG/NG log_loss_mercato 0.68399, baseline LOSO 0.69213 su n=5337. Sul blocco 2017-19 (n=3.650) il log-loss del book è 0.6851, non 0.6840 (D2 «2017-19 (principale)» ll_book=0.68508). Il DC +0.01036 è su n=3.512. Verificato in prima persona ricalcolando dai JSON grezzi footiqo + snapshot: LL book 0.68409, baseline LOSO 0.69211, overround 1.0462 su 5.377 righe pre-scarti.
- **Correzione**: Riscrivere: «quote trovate per 3 stagioni e 5 leghe (5.377 partite, 5.337 dopo gli scarti dichiarati; 3.652 delle quali nella finestra bersaglio 2017-19). Il mercato è informativo: log-loss 0.6840 vs 0.6921 su 5.337 partite…».
- **Verifica avversariale**: Nessun numero di CLAUDE.md è sbagliato, quindi la classificazione «numero-errato» non regge: 3.652 è il conteggio corretto delle partite trovate nella finestra bersaglio 2017-19, e 0.6840/0.6921/+0.0104 sono i valori corretti sul loro campione. CLAUDE.md non afferma da nessuna parte che le metriche siano calcolate su 3.652: la giustapposizione è ambigua, non falsa. Resta un difetto reale ma minore (attribuzione del campione non esplicitata, §2-bis punto 4), non un errore fattuale.

**🟡 `F100-panchina-senza-tag` — La PANCHINA ha le colonne Bundesliga/Ligue 1 popolate ma nessun riferimento «F100» e nessuna voce di archivio per le bocciature nuove**  
*incompiuto · bassa · ridimensionato*

- **Dove**: docs/PANCHINA.md:56-103 (matrice) e sezione «Archivio (voci uscite dalla rosa)», in coda
- **Atteso**: CLAUDE.md §2: «promozione/bocciatura → voce spostata di sezione, archivio in fondo con data e motivo»; ogni cella della matrice cita la fase che la stabilisce (F26/41, F76, F53/F81, F98, F99…)
- **Trovato**: Le celle nuove sono senza tag di fase («⚽ 15/15 vs DC», «❌ 0/25 mercati (θ 1.080)», «⚽ δ=0.28»); l'ultima voce di archivio è del 2026-07-23 (Fase 81); zero occorrenze di «F100»/«Fase 100» nel file, benché la fase abbia bocciato router θ, φ35, dp_lvl e power-devig su due leghe nuove.
- **Come è stato accertato**: grep -n 'F100|Fase 100' docs/PANCHINA.md → nessun risultato; le altre 8 righe toccate dalla Fase 98/99 portano regolarmente «F98»/«F99». `tail -40 docs/PANCHINA.md` mostra l'archivio fermo alla Fase 81.
- **Correzione**: Aggiungere il tag F100 alle celle Bundesliga/Ligue 1 e le voci di archivio datate (router θ ❌ F100, φ35 ❌ F100, dp_lvl ❌ F100, power-devig ❌ F100) con il numero e il motivo; valutare anche il recepimento della rosa GG/NG del report 11 §8 (varianti «scaletta completa», «ρ libero», «Platt sul book»), oggi assente dalla matrice.
- **Verifica avversariale**: La prima metà è verificata (zero «F100»/«Fase 100» nel file, celle nuove senza tag di fase mentre tutte le altre lo portano). La seconda metà è debole e non la sottoscrivo: l'Archivio è definito «voci uscite dalla rosa», cioè voci che cambiano SEZIONE; le bocciature della Fase 100 riguardano celle nuove (da ⬜ a ❌) di modelli che erano GIÀ nelle sezioni panchina/bocciati, quindi non c'è nessuna voce spostata da archiviare. Inoltre le celle nuove rispettano la regola 2 (numeri e motivo dichiarati): manca solo la tracciabilità della fase. Difetto reale ma di tag, non di sostanza.

<details><summary>Verifiche con esito OK su questo fronte</summary>

- CONTEGGI SNAPSHOT — letti con pandas: serie_a 3420, premier_league 3420, la_liga 3420, bundesliga 2754, ligue_1 3097 = 16.111 righe, 38 colonne ciascuno E NELLO STESSO ORDINE su tutte e 5 (il FAIL 'ordine DIVERSO' presente in audit_premier_league.json/audit_la_liga.json è stato risolto all'integrazione); tests/test_league_snapshots.py::test_schema_identico_tra_leghe esiste e presidia la cosa; `python -m pytest` → 194 passed.
- δ PER-LEGA RICALCOLATI DAI DATI — δ = ln(gol medi per squadra-gara della lega / gol medi delle neopromosse alla prima stagione): Bundesliga ln(1.5608/1.1834) = 0.2768 (17 promosse, 578 gare-squadra) e Ligue 1 ln(1.3710/1.1358) = 0.1882 (19 promosse, 670 gare-squadra) — identici a 03_nuove_leghe.md:148-149 e coerenti con src/config.py (0.28 e 0.19). Ricalcolati anche i tre storici: Serie A 0.2292, Premier 0.3286, La Liga 0.2179, coincidenti con i valori in config.
- θ PER LEGA — i cinque valori della tabella del diario (1.232, 1.242, 1.085, 1.080, 1.103) coincidono a 3 decimali con tranche3_market_tracer.json theta_pooled (1.23235, 1.24205, 1.08534, 1.07964, 1.10251). Anche le profondità di valle (−0.0081/−0.0081/−0.0012/−0.0012/−0.0017) coincidono con 10_modelli_nuove_leghe.md:85-89.
- GAP DC vs MERCATO SULLE LEGHE NUOVE — tranche3_tracer.json: bundesliga gap 0.018088 CI [0.010878, 0.025276] su 1.836 partite; ligue_1 gap 0.019019 CI [0.012100, 0.025752] su 2.058. Corrispondono a «+0.0181» e «+0.0190» del diario/README e alla tabella di 06_tranche3.md:25-26; sono dentro la forchetta delle altre tre leghe (serie_a 0.01650, premier 0.02071, la_liga 0.01623), come dichiarato.
- GG/NG — HEADLINE RIPRODOTTO IN PRIMA PERSONA dai dati grezzi versionati: join dei 15 file data/ricerca_esterna/footiqo_*.json con gli snapshot (0 righe non appaiate su 5.377), devig moltiplicativo su BTTSY/BTTSN → log-loss del book 0.68409 e baseline leave-one-season-out di lega 0.69211, overround 1.0462. Il report dichiara 0.6840 / 0.6921 / 1.0461 su n=5.337 (5.377 meno i 38+2 scarti dichiarati): coincide. Verificati anche dal JSON il DC +0.01036 CI [+0.00632, +0.01454] su 3.512 e l'encompassing α*=0 nel 70% dei fit (quota_alpha_zero = 0.7, alpha_medio 0.06).
- COPERTURA FOOTIQO 3.652/3.652 — contati i file JSON versionati: finestra 2017-19 = 760×4 (Serie A, Premier, Liga, Ligue 1) + 612 (Bundesliga) = 3.652, cioè il 100% delle partite di quelle 10 coppie lega-stagione; totale sulle 3 stagioni 5.377, con Ligue 1 2019-20 a 279 righe (troncamento COVID esatto, come dichiarato). corr 0.99773 con la chiusura e 0.99091 con l'apertura sono nel report 09 §2.2 come «verifica indipendente rifatta dall'orchestratore».
- GUARD SULL'OVERROUND — ORR_MAX = 1.12 è in produzione (src/data/loader.py:99 e il controllo bilaterale a :218), con due test dedicati (tests/test_league_snapshots.py:144 e :173). Verificato sui dati: era Avg n = 12.457 con massimo 1.0765 (esattamente i due numeri dichiarati), era BbAv ora n = 3.640 con massimo 1.0947; le 3 righe La Liga 2018-19 sono NaN (6 celle, come dice il diario) e in totale 11 righe svuotate + 1 assente alla fonte (bundesliga 7 = 6 + 1, ligue_1 2, la_liga 3).
- STIMATORE E3 — coefficienti [0.024793, 0.979835, 1.392864, −0.839769, 1.393283] identici in stima_ou_close_nuove.json, in experiments/runs.jsonl (2026-07-26T14:12:43) e nel blocco 📐 del diario; n_fit 12.457 (= le righe con chiusura O/U dell'era Avg, verificato sui dati); data/estimates/ou_close_2017_19.csv ha 3.638 righe (604+756+758+760+760) e le 1.362 stime delle due leghe nuove tornano con le 10 righe non stimabili elencate nel JSON.
- SNAPSHOT SERIE A CONTRO LA FONTE — ri-verificato offline con i grezzi versionati in data/football_data_raw/: 3.420 righe appaiate su 3.420, 0 differenze su gol e 0 su tiri in porta. Conferma indipendentemente il check B2 dell'audit («0 righe con GOL diversi dalla fonte») almeno per la lega dove i grezzi sono ancora in repo.
- ARTEFATTI NUMERICI — tutti i JSON citati dai report esistono in docs/audit_5_leghe/numeri/ (38 file); nessun riferimento a un artefatto perso nello spostamento cantiere→docs. Il manifesto delle 90 fonti scaricate (45 football-data + 45 Understat, con URL/SHA256/timestamp) è conservato in data/ricerca_esterna/manifest_fonti_audit.json, come promesso dall'indice.
- CONCLUSIONI RITIRATE NON PROPAGATE COME VALIDE — cercate in README.md, CLAUDE.md, docs/DIARIO.md e docs/PANCHINA.md tutte e cinque le affermazioni smontate dalla verifica avversariale (10_modelli_nuove_leghe.md §15): il ribaltamento «stimatore per-lega» (il diario e DATI.md dicono correttamente che resta pooled), «una φ costante batte la φ35», «w_D > 1 in La Liga», «il segnale GG/NG in Bundesliga», «griglia > MLE». Nessuna compare come valida nei documenti vivi; la correzione su «griglia > MLE» è anzi riportata esplicitamente nel blocco 📐 del diario.
- CORREZIONI DATI E REGOLA R1 — Union Berlin-Bochum 14/12/2024 è 1-1 (D) nello snapshot, cioè il risultato del CAMPO come prescrive R1, con le tre righe corrispondenti in data/correzioni_dichiarate.csv (stato 'applicata', fonte e decisore indicati); il falso positivo Bielefeld-Leverkusen è nel registro con stato 'ritirata' più due righe di ripristino a 0.0; il segnaposto Holstein Kiel-Bochum ha 6 colonne portate a NaN. docs/CACCIA_OU_2017_19.md è correttamente riscritto («CHIUSA: il dato è stato trovato») e docs/DATI.md dichiara i 1.603 falsi zero di midweek_europe e le 2 sole partite senza xG.

</details>

### README e registro dei risultati  ·  12 rilievi
**🟠 `F7-fase89-due-numeri` — Lo stesso guadagno della Fase 89 compare con due valori diversi in due righe adiacenti del README (e un terzo nel CLAUDE.md)**  
*numero-errato · media · **confermato***

- **Dove**: README.md:244 (riga «89») vs README.md:246 (riga «90») vs CLAUDE.md §6
- **Atteso**: Un solo valore, quello dell'artefatto versionato experiments/fase89_season_champion.json: log-loss modello 1.2010613, gain_vs_persistence2 = 0.2282880, ci [0.0090025, 0.4530022], seasons_better_persistence2 = 14.
- **Trovato**: README.md:244 riporta «log-loss 1.2011 … guadagno +0.2283 IC95% [+0.0090,+0.4530], 14/24» (= artefatto, corretto). README.md:246 (riga Fase 90) riporta per la stessa quantità «guadagno reale +0.2299 [+0.0108,+0.4542] 14/24». CLAUDE.md §6 riporta «1.1994 contro 1.4293 … +0.2299, IC95% [+0.0108,+0.4542]». I valori +0.2299/[+0.0108,+0.4542]/1.1994 sono quelli PRE-Fase 92 e non esistono più in nessun artefatto.
- **Come è stato accertato**: python3 -c "import json;d=json.load(open('experiments/fase89_season_champion.json'))['report'];print(d['logloss_model'],d['gain_vs_persistence2'],d['gain_ci_persistence2'],d['seasons_better_persistence2'])" → 1.2010612629342141 0.22828804266972905 [0.009002507739049717, 0.45300221847320876] 14. `git log --oneline -- experiments/fase89_season_champion.json` → l'artefatto è stato rigenerato nel commit d5eb581 (Fase 92, fix del prior neopromosse); README.md:244 fu aggiornato, README.md:246, il DIARIO (docs/DIARIO.md:9195, 9211, 9503) e CLAUDE.md §6 no.
- **Correzione**: Allineare README.md:246 e CLAUDE.md §6 ai valori dell'artefatto (1.2011 / +0.2283 / [+0.0090,+0.4530]), oppure — se si preferisce conservare i numeri storici — annotarli esplicitamente come «pre-fix del prior (Fase 92)». Stessa correzione va portata in docs/DIARIO.md (Fasi 89 e 90).

**🟠 `F7-riga89-numeri-misti` — Dentro la riga 89 del README convivono numeri rigenerati e numeri pre-Fase 92 (quattro sotto-cifre stantie)**  
*incoerenza-doc · media · **confermato***

- **Dove**: README.md:244
- **Atteso**: Tutte le cifre della riga coerenti con experiments/fase89_season_champion.json: gain_vs_reigning 1.4504109; log-loss per lega premier 0.7391, la_liga 1.3667, serie_a 1.4974; gain per lega serie_a 0.11428, la_liga 0.00295; base della ricalibrazione 1.2011.
- **Trovato**: Nella stessa cella: «Ricalibrazione a temperatura **fallisce in LOO** (1.2160 > 1.1994)» — 1.1994 è il log-loss vecchio, mentre il titolo della riga dice 1.2011; «il guadagno sale a +1.4521 e 24/24» (artefatto: 1.4504); «Per lega: PL 0.7411 · Liga 1.3651 · SA 1.4920» (artefatto: 0.7391 / 1.3667 / 1.4974); «SA +0.12, Liga +0.004» (artefatto: +0.114 / +0.003). Anche README.md:245 (riga 89-bis) cita «log-loss 1.2384 vs 1.1994».
- **Come è stato accertato**: Ricalcolo per lega dall'artefatto: media dei 24 record `backtest` → serie_a 1.4974 (hit 0.375), premier_league 0.7391 (hit 0.625), la_liga 1.3667 (hit 0.250); report['gain_vs_reigning']=1.4504109353470278; report['gain_persistence2_by_league']={'serie_a':0.11427941865440262,'premier_league':0.5676344146829175,'la_liga':0.002950294671867089}. Il valore 1.2160 e la base 1.1994 vengono da experiments/fase89bis_anatomy.json ({'temperature':{'base':1.1994032449948853,'ll_loo':1.2160426707767784}}), file NON rigenerato al commit d5eb581 (`git log -- experiments/fase89bis_anatomy.json` → ultimo tocco 4094be5, Fase 90).
- **Correzione**: Rieseguire `scripts/_run_fase89_season_champion.py` e `_run_fase89bis*` per rigenerare anche fase89bis_anatomy.json, poi riallineare le sotto-cifre di README.md:244-245; in alternativa marcare esplicitamente quali cifre sono pre-fix.

**🟠 `F7-roadmap-in-corso` — Il README dichiara «In corso» quattro esperimenti chiusi da oltre 60 fasi (e già presenti nella sua stessa tabella)**  
*incompiuto · media · **confermato***

- **Dove**: README.md:266-269 (blocco «Roadmap post-audit (Fasi 35+)»)
- **Atteso**: Il testo dovrebbe dire che (2)(3)(4)(5) sono stati eseguiti e chiusi negativi — le righe corrispondenti esistono nella tabella dello stesso README.
- **Trovato**: «In corso: (2) **GBM col set di feature COMPLETO** …; (3) **dummy `midweek_europe`** come covariata DC; (4) **covariate nel canale-pareggio** …; (5) **denoising cross-stagione del market-implied**.» Tutti e quattro sono chiusi: Fase 36 (README.md:173, ❌ overfitting), Fase 36-bis (README.md:174, ❌ off), Fase 37 (README.md:175, ❌ canale-pareggio saturo), Fase 38 (README.md:176, ❌ motore già maturo).
- **Come è stato accertato**: Lettura diretta di README.md:263-271 confrontata con le righe 173-176 della tabella «Tutti gli esperimenti»; docs/DIARIO.md contiene le sezioni «## Fase 36», «## Fase 37», «## Fase 38» (righe 4078, 4244, 4302) e il sotto-blocco 36-bis.
- **Correzione**: Riscrivere il blocco come consuntivo («fatti e chiusi negativi alle Fasi 36/36-bis/37/38») oppure eliminarlo, dato che la tabella lo copre già.

**🟠 `F7-stato-non-a-5-leghe` — Roadmap, Struttura e Archivio dati del README sono fermi a 3 leghe (o a 1) dopo l'ingresso di Bundesliga e Ligue 1**  
*incoerenza-doc · media · **confermato***

- **Dove**: README.md:1566-1570, README.md:1590-1591, README.md:1633-1634, README.md:40, README.md:1364-1392
- **Atteso**: 5 leghe (Serie A, Premier, La Liga, Bundesliga, Ligue 1), 16.111 partite, 5 snapshot congelati, schema 38/38 identico su tutte e cinque — come dichiarato in README.md:52 e in CLAUDE.md §6/§4.
- **Trovato**: README.md:1566-1567 (roadmap #28) «Estensione a nuovi campionati — fatto: **Premier League e La Liga** (Fasi 53-57, 76, 79-81)»: Bundesliga e Ligue 1 assenti. README.md:1590-1591 «snapshot `data/serie_a_matches.csv` … (3420 partite, 9 stagioni)»: unico snapshot citato. README.md:1633-1634 «Schema ora **38/38 colonne, identico su tutte e tre le leghe**». README.md:40 «il quaderno dedicato alle **due** leghe non-Serie A». README.md:1364-1392 (Struttura): `src/models/` non elenca `season_sim.py` (esiste, Fase 89), `data/` non cita `outright_snapshots/` (Fase 97), `docs/` non cita `audit_5_leghe/` (13 file, esito della Fase 100) né `GLOSSARIO.md`.
- **Come è stato accertato**: Conteggio righe degli snapshot: serie_a 3420, premier_league 3420, la_liga 3420, bundesliga 2754, ligue_1 3097 → totale 16111 (= il numero dichiarato in README.md:52). Schema verificato: tutti e 5 i CSV hanno 38 colonne nello stesso ordine. `ls src/models/` → season_sim.py presente; `ls data/` → outright_snapshots presente; `ls docs/audit_5_leghe` → 13 file + numeri/ con 37 JSON. Bundesliga/Ligue 1 compaiono nel README solo alle righe 52 e 257 (`grep -in "bundesliga|ligue" README.md`).
- **Correzione**: Aggiornare la voce 28 della roadmap con Fase 100; nell'Archivio elencare i 5 snapshot con i rispettivi conteggi e correggere «tre leghe»→«cinque leghe»; nella Struttura aggiungere `season_sim.py`, `data/outright_snapshots/`, `docs/audit_5_leghe/` e `docs/GLOSSARIO.md`; correggere «due leghe non-Serie A» alla riga 40.

**🟡 `F7-etichette-fase-solo-readme` — Quattordici etichette di fase esistono solo nel README: nel DIARIO non c'è un heading corrispondente**  
*incoerenza-doc · bassa · **confermato***

- **Dove**: README.md:187 (48-bis), 190-193 (50-bis/ter/quater/quinquies), 196-197 (51-ter/quater), 199-203 (52-bis/ter/quater/quinquies/sexies), 231 (79-EDA)
- **Atteso**: Poter risalire dalla riga della tabella alla voce di diario (il README stesso rimanda a «il ragionamento completo nel DIARIO»).
- **Trovato**: `grep -c "Fase 50-bis"` ecc. su docs/DIARIO.md restituisce 0 per: 48-bis, 50-bis, 50-ter, 50-quater, 50-quinquies, 51-ter, 51-quater, 52-bis, 52-ter, 52-quater, 52-sexies, 79-EDA (52-quinquies 1 sola occorrenza incidentale). I CONTENUTI ci sono, dentro le sezioni ombrello «## Fase 50/51/52» e «## Fase 79»: verificato per 48-bis (profilo μ −0.03657/+0.16799 presente nel DIARIO) e per 79-EDA (21.6%/36.3% presenti in docs/STUDIO_PREMIER_LIGA.md:84-85).
- **Come è stato accertato**: Estrazione degli heading `^#{2,4} Fase` dal DIARIO (i soli sotto-heading esistenti sono 9-bis, 36-bis, 54, 55, 56, 57) e grep mirato per ciascuna etichetta; grep di controllo sui numeri caratteristici per confermare che il contenuto esiste.
- **Correzione**: Aggiungere sotto-heading «### Fase 50-bis …» ecc. nel DIARIO, oppure indicare nella riga del README la sezione ombrello («vedi DIARIO, Fase 50»).

**🟡 `F7-fase2b-in-corso` — Titolo di sezione «Fase 2b (in corso)» per una fase adottata da ~98 fasi**  
*incompiuto · bassa · **confermato***

- **Dove**: README.md:332
- **Atteso**: «Fase 2b (adottata)» — shrinkage 1.5 ed emivita sono nella config ufficiale (README.md:74-75, src/config.py).
- **Trovato**: «### Feature engineering — Fase 2b (in corso)»
- **Come è stato accertato**: Lettura di README.md:332-374; la riga 136 della tabella la marca «✅ adottato» e src/config.py contiene shrinkage 1.5 / half_life_days 365 per tutte e 5 le leghe.
- **Correzione**: Sostituire «(in corso)» con «(adottata)» — il testo della sezione è già scritto al passato.

**🟡 `F7-15788-non-riconcilia` — Nella riga 100 il totale dell'audit (15.788) non riconcilia con le 16.111 partite dichiarate nello stesso README**  
*non-verificabile · bassa · **confermato***

- **Dove**: README.md:257 vs README.md:52
- **Atteso**: Un solo denominatore, o una spiegazione dello scarto. Gli artefatti per-lega dell'audit riportano i controlli su 3420+3420+3420+2754+3097 = 16.111 righe.
- **Trovato**: README.md:257: «gol confermati da fonte indipendente su **15.787/15.788**»; README.md:52: «**16.111 partite**». Scarto 323 righe non spiegato in nessun punto del README.
- **Come è stato accertato**: docs/audit_5_leghe/numeri/audit_*.json: n_rows = 3420/3420/3420/2754/3097 (totale 16.111) e il check C1 dice «0 righe con gol diversi tra football-data e Understat; 0/1 partite senza corrispondenza Understat» — cioè 16.110/16.111, non 15.787/15.788. Il 15.788 viene dal report narrativo docs/audit_5_leghe/01_audit_dati.md:65,280 e non è ri-derivabile dai JSON né dagli snapshot (copertura xG misurata: 16.109 righe su 16.111).
- **Correzione**: Chiarire nella riga 100 (e nel report 01_audit_dati.md) a quale sottoinsieme si riferisce il 15.788, oppure riportare il denominatore reale dei JSON (16.111). Nota: la verifica va fatta sul fronte «audit_5_leghe», qui si segnala solo che il README propaga un numero non riconciliabile.

**🟠 `F7-diagnosi-92-non-propagata` — La diagnosi ribaltata dalla Fase 92 è corretta solo in testa al README: 5 punti più sotto affermano ancora l'opposto, senza nota**  
*conclusione-non-supportata · media · ridimensionato*

- **Dove**: README.md:574-581, README.md:601-603, README.md:834-836, README.md:1478-1484, README.md:1535-1536 (correzione presente solo in README.md:281-303)
- **Atteso**: Dopo la Fase 92 (README.md:248, CLAUDE.md §6) il gap col mercato è 12% massa-pareggio / 88% discriminazione casa-ospite; il mercato «12» misura ESATTAMENTE la massa del pareggio perché P(12)=1−P(X), quindi il suo gap ≈0 NON dimostra che «sul chi vince siamo a livello mercato». Ogni punto del README che usa quella lettura va corretto o annotato.
- **Trovato**: README.md:574 «il gap è **quasi tutto nel PAREGGIO**»; README.md:580-581 «Escluso il pari (mercato 12) il modello è **a livello mercato**: la debolezza è prezzare i pareggi, non stimare chi è più forte»; README.md:602-603 «Sapere chi è più forte è a livello mercato sempre, non in media»; README.md:834-836 «sul "chi vince" modello e mercato sono formalmente indistinguibili»; README.md:1482-1483 (roadmap #14) «è quasi tutto nel PAREGGIO (il mercato 12 senza pari ha gap +0.0020 ≈ mercato)»; README.md:1535-1536 (roadmap #22) «gap 12 +0.0020 [−0.0006,+0.0046] (statisticamente zero: sul "chi vince" siamo a livello mercato)». Nessuno dei cinque ha un rimando alla Fase 92.
- **Come è stato accertato**: grep -n "quasi tutto nel|mercato 12|senza pari" README.md → righe 574,580,592,601,1482,1535; la correzione esiste solo alle righe 281-303 («⚠️ diagnosi CORRETTA alla Fase 92 (era invertita per 80 fasi)», tabella 12.0%/88.0%). Confermato dal commit d5eb581 («LA DIAGNOSI CENTRALE DEL PROGETTO ERA ROVESCIATA … scomposizione: massa-pareggio +0.002010 (12.0%) + discriminazione +0.014690 (88.0%)») e da README.md:248 (riga 92 della tabella).
- **Correzione**: Aggiungere in ognuno dei 5 punti una nota di ritiro con rimando a README.md:281 (es. «⚠️ lettura INVERTITA, corretta alla Fase 92: P(12)=1−P(X), quindi questo numero misura la massa del pareggio, non «chi vince» — vedi §Dove vive il gap»), come già fatto in CLAUDE.md §6 e §2-bis.
- **Verifica avversariale**: Il fatto è riprodotto: i cinque punti esistono e ripetono la lettura ritirata, senza nota locale. MA la descrizione «conclusione non supportata rimasta nel documento» è solo a metà vera, e questo abbassa la gravità da alta a media: (a) tutti i NUMERI citati sono corretti (il gap 12 +0.0020 È esattamente la componente massa-pareggio 0.002010 della scomposizione F92 — coincidono); l'errore è solo interpretativo; (b) il README RITIRA esplicitamente quella lettura in un blocco ⚠️ dedicato (righe 281-303) che CITA ALLA LETTERA le frasi incriminate («Per anni qui c'è stato scritto "è quasi tutto nel PAREGGIO, escluso il pari (mercato "12") siamo già a livello mercato"»), e quel blocco sta PRIMA (riga 281) delle sezioni offensive (574+), quindi chi legge in ordine incontra prima la smentita; (c) le righe 574/580/602 e 835 stanno dentro «## Analisi dettagliata per fase» (riga 307), dichiarata narrazione cronologica per fase, e le righe 1482/1536 dentro la lista storica della «## Roadmap» (riga 1428). Resta un difetto reale di propagazione (nessun rimando in nessuno dei 5 punti, e il punto 22 della roadmap è a 1250 righe di distanza dalla smentita), ma è incoerenza interna a un documento che la correzione la contiene, non una conclusione sbagliata lasciata in piedi.

**🟡 `F7-squad-value-copertura-stantia` — L'Archivio dati del README dichiara ancora coperture squad_value 95.6%/60.2%, superate da tempo (oggi 100% su 5 leghe)**  
*numero-errato · bassa · ridimensionato*

- **Dove**: README.md:1627-1628
- **Atteso**: Copertura `squad_value` 100% (Fasi 67 e 70: «squad_value **reale al 100%**, zero NaN residui», riportato nello stesso README alle righe 219 e 222; le leghe nuove sono entrate già complete).
- **Trovato**: «Copertura `squad_value`: **95.6% Premier League**, **60.2% La Liga** (58.3% prima del fix del matching, Fase 63 …)», presentata come stato corrente dell'archivio, senza nota di superamento.
- **Come è stato accertato**: Verificato sugli snapshot: frazione di righe con home_squad_value E away_squad_value non-NaN = 1.000 per tutte e 5 le leghe (serie_a, premier_league, la_liga, bundesliga, ligue_1). Contraddetto dalle stesse righe 219 («SA 69.8→94.2%, Liga 60.2→95.0%, PL 95.6→97.8%») e 222 («reale al 100%, zero NaN residui») della tabella del README.
- **Correzione**: Sostituire il paragrafo con la copertura attuale (100% su 5 leghe) e lasciare la storia 95.6/58.3/60.2% come nota cronologica con rimando alle Fasi 63/67/70.
- **Verifica avversariale**: La misura dell'auditor è giusta (copertura oggi 100% su tutte e 5 le leghe, verificata da me), ma la classificazione «numero-errato» è sbagliata e la severità va abbassata. Il paragrafo NON è presentato come stato corrente generico: è introdotto in grassetto da «**Generalizzato a Premier League e La Liga (Fase 60).**» (README.md:1622) ed è tutto scritto nell'epoca F60/F63 — i valori 95.6% e 60.2% ERANO corretti allora (la parentesi «58.3% prima del fix del matching, Fase 63» lo dice esplicitamente). Inoltre lo stesso README dà due volte il dato aggiornato, alle righe 219 (F67: PL 95.6→97.8, Liga 60.2→95.0) e 222 (F70: «reale al 100%, zero NaN residui»), quindi nessun numero è sbagliato e nessuna informazione è persa: manca solo una nota di superamento in una sezione di riferimento. Difetto reale ma minore.

**🟡 `F7-ggng-premessa-caduta` — Nel README resta l'affermazione che il GG/NG è «l'unico mercato senza tetto di efficienza dimostrato» — premessa dichiarata CADUTA alla Fase 100**  
*conclusione-non-supportata · bassa · ridimensionato*

- **Dove**: README.md:935, README.md:1081 (contraddette da README.md:257)
- **Atteso**: Come in CLAUDE.md §1.8 («~~…l'unico con "spazio" non ancora chiuso~~ **PREMESSA CADUTA**»): il mercato GG/NG è stato misurato ed è informativo (log-loss 0.6840 contro 0.6921 di baseline, CI conclusivo), il nostro prezzo lo pareggia e il DC perde (+0.0104, α*=0 nel 70% dei fit).
- **Trovato**: README.md:935 «il **GG/NG**, dove … **non ci sono quote nei dati** — l'unico mercato senza tetto di efficienza dimostrato»; README.md:1081 «non è verificabile contro un'ipotetica linea di chiusura del GG/NG (assente nei dati)». Entrambe al presente, senza nota; la riga 257 (Fase 100) afferma il contrario nello stesso file.
- **Come è stato accertato**: CLAUDE.md §1.8 barra esplicitamente il testo e scrive «PREMESSA CADUTA (integrazione delle 5 leghe) … 3.652 partite del 2017-19 su tutte e 5 le leghe … il mercato GG/NG è informativo». README.md:257 riporta gli stessi numeri (0.6840 vs 0.6921, α*=0 nel 70% dei fit). Verificato che le quote GG/NG non sono negli snapshot (38 colonne, nessuna colonna BTTS), quindi resta vero solo il «non ci sono quote nei dati».
- **Correzione**: Annotare le due frasi con la caduta della premessa (rimando alla riga 100 della tabella e a CLAUDE.md §1.8), lasciando in piedi solo il fatto letterale «gli snapshot non contengono quote GG/NG».
- **Verifica avversariale**: Le due frasi esistono e la premessa è davvero caduta, ma il rilievo sovrastima il danno. Dei due addebiti, uno è FALSO e l'altro è più debole di come è scritto: (a) README.md:935 «non ci sono quote nei dati» resta LETTERALMENTE VERO (verificato: nessuna colonna BTTS nelle 38 dello snapshot; le quote GG/NG del book 1xBet vivono in data/ricerca_esterna/footiqo_*.json e NON sono state inserite negli snapshot) — l'unica parte superata è l'inciso «l'unico mercato senza tetto di efficienza dimostrato»; (b) README.md:1081 sta dentro un elenco intitolato «**Onestà d'obbligo:**» che elenca i caveat della Fase 24, cioè il contesto in cui quell'affermazione era vera. Entrambe stanno in sezioni per-fase esplicitamente cronologiche («### … — Fase 21», «### … — Fase 24»), e la smentita è nello stesso README alla riga 257 e in CLAUDE.md §1.8 con il testo barrato. Resta una propagazione mancata, ma localizzata e senza numeri sbagliati: bassa, non media.

**🟡 `F7-riga98-lead-non-ritirato` — La riga 98 della tabella chiude con «✅ leva nuova: correzione di livello dei conteggi», lead che la riga successiva dichiara FALSO**  
*incoerenza-doc · bassa · ridimensionato*

- **Dove**: README.md:255 (esito) vs README.md:256
- **Atteso**: Un lettore che si ferma alla riga 98 deve vedere che il lead è stato chiuso negativo (auto-correzione della Fase 99), come già fa l'indice del DIARIO.
- **Trovato**: README.md:255 termina con «✅ leva nuova: correzione di livello dei conteggi; …» senza rimando; README.md:256 (Fase 99) dice «**il lead è FALSO** … 6 celle su 8 peggiorano con IC conclusivo».
- **Come è stato accertato**: Lettura delle due righe. docs/DIARIO.md:241 (indice per archi) contiene il puntatore «la deriva di livello dei conteggi — che la Fase 99 misura e **boccia**», ma né la sezione «## Fase 98» del DIARIO (riga 10563) né la riga 98 del README lo riportano.
- **Correzione**: Aggiungere in coda alla cella-esito della riga 98 «(⚠️ lead chiuso NEGATIVO alla Fase 99)» e la stessa nota in testa alla sezione «## Fase 98» del DIARIO.
- **Verifica avversariale**: Il fatto letterale è vero (la cella-esito della riga 98 termina con «✅ leva nuova: correzione di livello dei conteggi» senza rimando), ma la sostanza del rilievo — auto-correzione non propagata — è smontata: la bocciatura è registrata in TUTTI i registri che il CLAUDE.md §2 richiede, e in tre casi su quattro senza che il lettore debba cercarla. README.md:256 è la riga IMMEDIATAMENTE successiva nella stessa tabella e dice «**il lead è FALSO** … 6 celle su 8 peggiorano con IC conclusivo»; docs/DIARIO.md:10805 ha la sezione «## Fase 99 — … il lead della Fase 98 è FALSO» e l'indice per archi (riga 241) la anticipa; docs/PANCHINA.md:136 registra «la **Fase 99 l'ha bocciata**»; CLAUDE.md §6 riporta la regola nata dalla bocciatura. Per la regola esplicita del brief («una fase che dice che il lead della precedente è falso NON è un errore, è il metodo; semmai verifica che l'auto-correzione sia stata propagata OVUNQUE»), qui la propagazione c'è: resta solo un puntatore in avanti di cortesia. Difetto puramente cosmetico.

**🟡 `F7-fasi-senza-riga` — Otto fasi del DIARIO non hanno riga nella tabella «Tutti gli esperimenti», che si dichiara registro di OGNI analisi**  
*omissione · bassa · ridimensionato*

- **Dove**: README.md:128-134 (intestazione della tabella) — fasi mancanti: 0, 1, 2a, 4a, 4e, 5, 9, 13-bis
- **Atteso**: Per CLAUDE.md §2 la tabella è il punto UNICO dove vedere i numeri chiave di OGNI backtest e analisi.
- **Trovato**: Confronto automatico: 111 heading «## Fase» nel DIARIO contro 122 righe della tabella; presenti nel DIARIO e assenti dalla tabella: Fase 0, 1, 2a, 4a, 4e, 5, 9, 13-bis. (Tutte hanno una copertura altrove nel README — sezioni di dettaglio 2a/5/9, «Archivio dati» per 4a/4e, roadmap per 0/1, e la 13-bis è di fatto assorbita dalla riga «13 | forma · streak · rendimento recente» — quindi è un buco di registro, non di contenuto.)
- **Come è stato accertato**: Script di confronto: estrazione di `^## Fase N` da docs/DIARIO.md e della prima colonna delle righe della tabella README (dalla riga 136 alla 257). Le fasi 80-100 e le loro -bis sono TUTTE presenti: nessun buco nell'arco recente.
- **Correzione**: Aggiungere le 7-8 righe mancanti (anche solo in forma sintetica, tipo «1 | tracer bullet DC | 1X2 … | ✅ base»), oppure ammorbidire l'intestazione della tabella dichiarando che copre le leve provate dalla Fase 2b in poi.
- **Verifica avversariale**: Il conteggio l'ho rifatto e il difetto è reale ma va corretto in due sensi. In eccesso di gravità: la colonna della tabella si chiama «**Leva provata**», e nessuna delle fasi mancanti è una leva — sono fasi di impianto o di sola diagnosi (0 setup, 1 tracer bullet, 2a analisi errori, 4a arricchimento dati, 4e calendario, 5 backtest multi-mercato, 9 anatomia del gap, 13-bis) e TUTTE hanno copertura numerica altrove nello stesso README (sezioni dedicate «### … — Fase 2a» :315, «Fase 5» :489, «Fase 9» :568; voci 1-10 della Roadmap :1429-1460). Nessun numero è irreperibile, quindi è un buco di indicizzazione, non di registro. In difetto: le fasi mancanti sono NOVE, non otto — manca anche la **Fase 9-bis** (docs/DIARIO.md:1723, «COVID vs post-COVID e trend recente»), che l'auditor non ha elencato.

<details><summary>Verifiche con esito OK su questo fronte</summary>

- HEADLINE SERIE A RICALCOLATI DAL REGISTRO — tutti coincidono col README (righe 78-105): media 6 stagioni 2020-21→2025-26 dei run con config ufficiale (365g/1.5/0.75/xg/δ=0.23) in experiments/runs.jsonl → modello 0.9797, mercato 0.9632, gap +0.0165, baseline in-sample 1.0834, O/U 0.6885 vs 0.6816, ROI medio −15.67% su 864 scommesse, range per stagione da −4.73% a −23.03%.
- «~86% della distanza baseline→mercato» (README:110-112) — ricalcolato: (1.0834−0.9797)/(1.0834−0.9632)=86.3% in-sample e (1.0860−0.9797)/(1.0860−0.9632)=86.6% ex-ante. Corretto.
- Tabella «Come si è chiuso il gap» (README:113-121) — i Δ (−0.0051, −0.0004, −0.0006, −0.0010) sommati a V0 +0.0236 danno esattamente +0.0165; il «72%» della riga 123 è 0.0051/0.0071 = 71.8%. Coerente, inclusa la nota che spiega il −0.0010 vs −0.0011.
- Conteggi della Fase 100 (README:52 e 257) — 16.111 partite = 3420+3420+3420+2754+3097 righe dei 5 snapshot; 3.638 stime = righe di data/estimates/ou_close_2017_19.csv (3639 linee incl. header); 2.754 e 3.097 per le due leghe nuove verificati; «MAE 0.0156 vs 0.012» del dato 1xBet coincide con docs/audit_5_leghe/09_chiusura_buchi.md:105.
- FALSO ALLARME EVITATO — Fase 81: i valori del README (SA −0.0078, Liga −0.0069, Liga 1X2 −0.0023, GG −0.0025, φ-grid −0.0019) NON contraddicono il DIARIO (che cita −0.0079/−0.0085): sono i delta del selettore walk-forward «lfo» in experiments/runs.jsonl (source=fase81_mega_sweep_mi: lfo.cs serie_a −0.007849, la_liga −0.006887; lfo.gg −0.002452; lfo.x2 −0.002334; phi lfo.gg −0.001922), mentre il DIARIO cita i minimi in-sample. Il README è corretto e coerente con la sua stessa frase «anche col selettore».
- FALSO ALLARME EVITATO — Brier handicap asiatico: README:243 (Fase 88) 0.2040 vs 0.2041 su n=7.437 e README:255 / CLAUDE.md §6 0.2044 vs 0.2044 sono due campioni diversi, non una contraddizione: experiments/listino_validazione.json → handicap_asiatico_dettaglio n=6839, brier_model 0.2043989, brier_market 0.2044090.
- Fase 93 (README:249) — tutti i numeri ri-trovati: 86.9% ri-derivato da experiments/fase93_discrimination.json (share del terzile «disaccordo forte» = 0.86893); 0.00083/0.00125, risoluzione 0.05270/0.06251, −0.00198/−0.00793, giornate 1-5 −0.00829 → 26+ −0.00991 e 57.61%/57.68% coincidono con docs/DIARIO.md:9878-9960.
- Fase 89-bis (README:245) — 82.7% / 79.2% / 95.8% / 52.6% / 71.6% / σ=0.189 / 44% ri-derivati da experiments/fase89bis_anatomy.json (p_top2_declared 0.82664, realised 0.79167, champion_in_top3 23/24, pick_within_top2 10/19, declared 0.71561, drift_sd 0.18948, ratio 0.43702).
- Confronto sistematico README↔DIARIO su TUTTE le righe 80-100: estratte le cifre di ogni riga e cercate nella sezione «## Fase N» del DIARIO. Gli unici numeri che non compaiono da nessuna parte nel DIARIO sono quelli della Fase 89 (1.2011, +0.2283, [+0.0090,+0.4530] — oggetto del reperto F7-fase89-due-numeri) e 16.111/3.638 (verificati direttamente sui dati). Tutte le altre righe 80-100 sono numericamente coerenti col DIARIO.
- Link e percorsi del README — nessun link markdown rotto: verificati tutti i link relativi (file esistenti) e tutte le ancore interne contro i 55 heading del file; verificati i 21 script citati nelle righe 88-100 (`_run_fase89_season_champion.py`, `_run_polymarket_outright.py`, `_run_outside_matrix.py`, `_run_counts_nb.py`, `_run_referee_feature.py`, `_run_prospective_power.py`, `_run_polymarket_tier3.py`, `_run_lineup_proxy.py`, `_run_line_movement.py`, `_run_listino_validazione.py`, `_run_counts_level.py`, `_run_ah_benchmark.py`, `_run_tail_*`, `fetch_smarkets_outrights.py`, `archive_outrights.py`, `_run_fase97_relegation_market.py`, `fetch_polymarket_open.py`, …): esistono tutti.
- Coerenza README↔CLAUDE.md §6 sui punti portanti: 5 leghe, 9 stagioni, 16.111 partite, gap Serie A +0.0165, gap leghe nuove +0.0181/+0.0190, market-implied 13/14 (3 leghe storiche) e 15/15 (nuove), θ «latine» ≈1.24 vs Premier/Bundesliga/Ligue 1 ≈1.08-1.10, f=0.4396 [0.4338,0.4458], δ per-lega 0.23/0.33/0.22/0.28/0.19 (verificato in src/config.py: LEAGUE_CONFIGS). Coincidono tutti; l'unica divergenza è quella della Fase 89 (reperto F7-fase89-due-numeri).

</details>

### PANCHINA (rosa dei modelli)  ·  16 rilievi
**🟠 `F8-02-6-su-8-celle-e-in-realta-5` — «6 celle su 8 peggiorano con IC conclusivo» (Fase 99): le celle conclusive sono 5, e lo dice la tabella stessa del diario**  
*numero-errato · media · **confermato***

- **Dove**: docs/PANCHINA.md:99; README.md:256; CLAUDE.md:494; docs/PISTE.md:283; lavoro_aperto.md:79; docs/DIARIO.md:10853
- **Atteso**: 5 celle su 8 (corner `c_trend`; cartellini `c_oos`, `c_last2`, `c_last`, `c_trend`)
- **Trovato**: «6/8 celle peggiorano con IC conclusivo» in tutti e sei i documenti
- **Come è stato accertato**: Ri-eseguito `python3 scripts/_run_counts_level.py`: forma Poisson, 8 celle non-controllo, colonna `conclusivo` = SI solo per corners/c_trend (−0.00316 [−0.00475,−0.00155]) e per le 4 celle cartellini. Le tre celle corner c_oos/c_last2/c_last hanno CI che contiene lo zero (c_last: −0.00176 [−0.00360, +0.00006]). La stessa tabella di docs/DIARIO.md:10842-10852 marca «no» quelle tre righe.
- **Correzione**: Sostituire «6/8» con «5/8» nei sei punti (la conclusione «il lead è falso» non cambia: nessuno dei cinque stimatori migliora e la diagnosi della non-persistenza del bias regge).

**🟠 `F8-08-sezione-titolari-ferma-a-3-leghe` — La sezione «I titolari» non è stata aggiornata all'integrazione a 5 leghe (la matrice sì)**  
*incompiuto · media · **confermato***

- **Dove**: docs/PANCHINA.md:147, 148, 153
- **Atteso**: δ 0.23/0.33/0.22/0.28/0.19 (5 voci in `LEAGUE_CONFIGS`); spareggi per-lega comprensivi di Bundesliga `("gd","gf","h2h")` e Ligue 1 `("gd","h2h","gf")`; per il motore market-implied non più «altre leghe da ritarare» ma «ritarate: Premier/Liga/BL/L1 → motore liscio (Fasi 79/80/81/100)»
- **Trovato**: «`LEAGUE_CONFIGS`: δ 0.23/0.33/0.22; il resto è comune (F57)» (riga 148); «spareggi per-lega (h2h SA/Liga, DR Premier)» (riga 153); «costanti Serie A …; **altre leghe da ritarare**» (riga 147)
- **Come è stato accertato**: src/config.py:75-89 (BUNDESLIGA δ=0.28, LIGUE_1 δ=0.19) e :90-97 (LEAGUE_CONFIGS a 5 voci); src/models/season_sim.py:66-72 (TIEBREAK_RULES a 5 leghe, BL e L1 incluse); src/config.py:126-142 (MARKET_ENGINE: Premier e Liga già a motore liscio, BL/L1 assenti → fallback liscio in `market_engine`).
- **Correzione**: Allineare le tre righe della sezione titolari ai 5 campionati e allo stato reale del codice.

**🟠 `F8-09-24-caselle-vuote` — «24 caselle vuote della PANCHINA»: la matrice ne ha 138**  
*incoerenza-doc · media · **confermato***

- **Dove**: lavoro_aperto.md:103-116; CLAUDE.md:297
- **Atteso**: 138 celle ⬜ su 276 (46 righe × 6 fronti): Serie A 1, Premier 22, La Liga 23, Bundesliga 36, Ligue 1 36, generale 20
- **Trovato**: «`docs/PANCHINA.md` — **24 caselle ⬜** (mai testato lì)» e «la matrice ha 24 celle `⬜`»; identica cifra in CLAUDE.md §4
- **Come è stato accertato**: Conteggio programmatico sulle righe 58-103 di docs/PANCHINA.md → 138 ⬜ (⚽ 48, 🪑 25, ❌ 72). Il numero non tornava nemmeno prima dell'integrazione: al commit 6c2e0f7 (quando lavoro_aperto.md è stato scritto) erano 64, al commit 81e174b 66. Inoltre la tabella di lavoro_aperto.md:114-115 elenca fra i «mai testati altrove» cinque leve che l'audit ha poi misurato su BL/L1 (nudge escluso: ensemble emivite, ricalibrazione per-classe del modello, diagonale inflazionata, temperature scaling, più le covariate).
- **Correzione**: Ricontare (o smettere di citare un numero assoluto) e riscrivere lavoro_aperto.md §3 dopo la Fase 100; nota collaterale: lavoro_aperto.md:337-339 dice ancora «Da non fare adesso: aggiungere le leghe nuove (Ligue 1/Bundesliga…)», cosa fatta nella Fase 100.

**🟠 `F8-10-fasi-95bis-97-non-in-rosa` — La deriva di forza: le Fasi 95-bis e 97 (che la mettono alla prova contro un mercato vero) non compaiono nella rosa, che cita solo la F94**  
*omissione · media · **confermato***

- **Dove**: docs/PANCHINA.md:30-35 (nota ✱7) e :65
- **Atteso**: Aggiornamento della nota: sul mercato CAMPIONE la deriva ha un effetto misurato contro Polymarket (KL Serie A 0.1805→0.1445, Premier 0.2418→0.2036, La Liga 0.0560→0.0740) e sulla retrocessione Premier è confermata da Smarkets (eccesso sulle neopromosse 8.84pp→7.32pp); più il residuo nuovo («coda a zero»: 0.0% su Man City/Liverpool contro 7.6%/1.1% del mercato)
- **Trovato**: La nota ✱7 dice solo «Sul campione non ha effetto» (F94, 24 osservazioni) e la riga 65 cita solo F94; nessuna occorrenza di F95-bis o F97 in tutto il file
- **Come è stato accertato**: docs/DIARIO.md:10223-10277 (Fase 95-bis, tabella KL per lega) e :10440-10470 (Fase 97, 8.84pp→7.32pp e coda a zero). `grep -n "F95\|F97" docs/PANCHINA.md` → nessun risultato. CLAUDE.md §2 impone l'aggiornamento della rosa «dopo ogni esperimento che tocca lo stato di un modello».
- **Correzione**: Aggiornare ✱7 con l'esito dei due metri indipendenti e con il residuo aperto (incertezza sui parametri), che oggi vive solo in docs/PISTE.md.

**🟠 `F8-11-link-rotti-audit-5-leghe` — 16 link relativi rotti in docs/audit_5_leghe/ dopo lo spostamento da cantiere/**  
*import-rotto · media · **confermato***

- **Dove**: docs/audit_5_leghe/00_indice.md:36-48 (11 link `report/NN_*.md`); docs/audit_5_leghe/04_decisioni.md:170,214; 07_dati_corrotti.md:15; 09_chiusura_buchi.md:339 (`../REGOLE.md`); 05_tranche1.md:66 (`../patch/guard_overround.md`)
- **Atteso**: `01_audit_dati.md` … `11_ggng.md` (stessa cartella), `REGOLE.md` (stessa cartella), `patch_guard_overround_APPLICATA.md`
- **Trovato**: I link puntano ancora alla struttura del cantiere (`report/…`, `../REGOLE.md`, `../patch/…`), che non esiste più
- **Come è stato accertato**: Script di verifica dei link markdown su docs/audit_5_leghe/*.md → 16 target inesistenti (elencati sopra). Controllo speculare su README.md, CLAUDE.md, lavoro_aperto.md, newseason.md, docs/*.md, experiments/*.md, data/estimates/*.md → 0 link rotti.
- **Correzione**: Sostituire il prefisso `report/` con il nome del file nella stessa cartella, `../REGOLE.md` → `REGOLE.md`, `../patch/guard_overround.md` → `patch_guard_overround_APPLICATA.md`.

**🟡 `F8-12-convenzione-segno-CI` — «CI<0» significa «migliora» in tre celle della matrice e «peggiora» in un'altra**  
*incoerenza-doc · bassa · **confermato***

- **Dove**: docs/PANCHINA.md:60 (cella Bundesliga) contro :59 (Serie A e La Liga), :68, :162, :163
- **Atteso**: Una convenzione unica (nel resto del progetto Δ<0 sul log-loss = miglioramento)
- **Trovato**: Riga 60 Bundesliga: «peggiora la doppia 1X (CI<0)» — il segno viene dalla tabella del report, che usa Δ = senza − con (positivo = migliora); riga 59 e voci 1-bis/1-ter usano «CI<0» per indicare un miglioramento
- **Come è stato accertato**: docs/audit_5_leghe/10_modelli_nuove_leghe.md:141: bundesliga doppia 1X «senza 0.5488 | con 0.5496 | Δ −0.00076 [−0.0013,−0.0003] | peggiora» (convenzione invertita rispetto a docs/PANCHINA.md:59, dove «cs −0.0069* lfo CI<0» è un guadagno, verificato re-eseguendo lo sweep).
- **Correzione**: Riscrivere la cella Bundesliga con la convenzione del progetto (es. «+0.00076 [+0.0003,+0.0013] = peggiora, CI conclusivo»).

**🟡 `F8-14-bocciati-senza-riga-e-voci-senza-dettaglio` — Cinque voci della tabella «bocciati» non hanno riga nella matrice; quattro voci di panchina non hanno il blocco di dettaglio**  
*omissione · bassa · **confermato***

- **Dove**: docs/PANCHINA.md:293, 294, 298, 301, 315 (bocciati senza riga) e :162, 163, 174, 175 (voci 1-bis, 1-ter, 12, 13 senza dettaglio in :177-281)
- **Atteso**: La matrice è presentata come «ogni modello × ogni fronte»; la sezione di dettaglio copre «le voci di panchina»
- **Trovato**: Senza riga in matrice: temperatura post-hoc su P(campione) (F89), covariata squad_value sul mercato campione (F89-bis), finestre dati corte (F25), coda a 2 parametri isotonica+mistura (F87), θ per-squadra sulla coda (F86/86-bis). Senza blocco di dettaglio: voci 1-bis, 1-ter, 12 e 13 (il dettaglio si ferma alla voce 11).
- **Come è stato accertato**: Confronto riga per riga fra la matrice (46 righe) e le tabelle «bocciati» (:288-315) e «panchina» (:159-175) di docs/PANCHINA.md.
- **Correzione**: Aggiungere le cinque righe mancanti alla matrice (almeno θ per-squadra e coda a 2 parametri, che sono leve di modello) e i quattro blocchi di dettaglio mancanti.

**🟡 `F8-16-script-inesistente-fase97` — Il diario della Fase 97 rimanda a uno script che non esiste**  
*import-rotto · bassa · **confermato***

- **Dove**: docs/DIARIO.md:10556 («python scripts/_run_fase96_relegation_market.py»)
- **Atteso**: `scripts/_run_fase97_relegation_market.py`
- **Trovato**: `_run_fase96_relegation_market.py` — non presente in scripts/
- **Come è stato accertato**: `ls scripts/ | grep relegation` → solo `_run_fase97_relegation_market.py`; il modulo è importato con quel nome anche in scripts/_run_polymarket_outright.py.
- **Correzione**: Correggere il nome nel blocco di riproducibilità della Fase 97.

**🟠 `F8-01-simulatore-ligue1-stato-sbagliato` — Simulatore di stagione: Ligue 1 marcata 🪑 dove la misura integrata dice ❌ (conclusivamente peggiore della baseline)**  
*conclusione-non-supportata · media · ridimensionato*

- **Dove**: docs/PANCHINA.md:63 (cella «Ligue 1»)
- **Atteso**: ❌ bocciato in Ligue 1, come stabilito dal report integrato: «vs stessa baseline al suo meglio: −0.1682 [−0.33, −0.05], 0/8» e riga di rosa «simulatore campione di stagione | 🪑 panchina (BL) | ❌ bocciato (L1)»
- **Trovato**: «🪑 idem, non batte «vince il PSG»» — stato panchina e formulazione che nasconde l'unico CI conclusivo CONTRO il modello sull'outright
- **Come è stato accertato**: docs/audit_5_leghe/10_modelli_nuove_leghe.md:534 (tabella §9: Ligue 1 «−0.1682 [−0.33,−0.05], 0/8»), :537 («in Ligue 1 è conclusivamente peggiore»), :924 (riga della rosa proposta: «🪑 panchina | ❌ bocciato»). Confronto con docs/PANCHINA.md:63 letto riga per riga.
- **Correzione**: Portare la cella Ligue 1 della riga «Simulatore di stagione → mercato CAMPIONE» a ❌ con il numero (−0.1682 [−0.33,−0.05], 0/8 stagioni) e la riserva del report (il CI non sopravvive a Bonferroni, soglia 0.0031; la baseline «al suo meglio» ha il parametro scelto in-sample → lettura corretta «il modello non dimostra valore aggiunto»).
- **Verifica avversariale**: La divergenza esiste ma NON e' una «conclusione non supportata» di gravita' alta. Il testo della cella («🪑 idem, non batte «vince il PSG»») e' FATTUALMENTE VERO: contro la baseline «vince la rosa piu' cara» (LOO) il modello fa +0.0759 [−0.15,+0.43], cioe' non la batte. Il difetto reale e' solo la LETTERA dello stato: il report integrato propone ❌ per la Ligue 1 e la rosa scrive 🪑 (la cella Bundesliga invece coincide, 🪑 in entrambi). Inoltre l'aggravante dichiarata dall'auditor («nasconde l'unico CI conclusivo contro il modello») e' proprio cio' che il report stesso ritira nelle righe successive a quelle citate: «la baseline al suo meglio ha il parametro scelto in-sample e non e' implementabile in prospettiva, quindi la lettura corretta e' *il modello non dimostra valore aggiunto*» e «il solo CI conclusivo contro il modello non sopravvive a Bonferroni (soglia 0.0031)». Un −0.1682 contro una baseline tarata in-sample e non-Bonferroni non e' materiale da severita' alta. Da correggere: allineare la lettera (❌) o dichiarare in cella perche' si e' scelto 🪑.

**🟠 `F8-03-celle-vuote-gia-misurate` — 18 celle Bundesliga/Ligue 1 dichiarate ⬜ «mai testato lì» pur essendo state misurate nell'audit integrato (Fase 100)**  
*incoerenza-doc · media · ridimensionato*

- **Dove**: docs/PANCHINA.md:68 (cella Ligue 1), 73, 74, 75, 76, 77, 78, 96, 103 (celle Bundesliga e Ligue 1)
- **Atteso**: Gli stati misurati in docs/audit_5_leghe/10_modelli_nuove_leghe.md §12-§13: ensemble emivite 🪑/🪑-alta (BL −0.000496 [−0.00137,+0.00037] 4/6; L1 −0.000938 [−0.00177,−0.00013] 5/6); ricalibrazione per-classe del modello ❌/❌ (BL +0.002807; L1 +0.002200 [+0.00036,+0.00402] «conclusivo CONTRO»); diagonale inflazionata ❌/❌ (BL +0.000687; L1 −0.000056); temperature scaling 🪑/❌ (BL −0.000236 5/6; L1 +0.000370 2/6); `rest_full` ❌/❌ (+0.000796 / +0.000371); `midweek_europe` ❌/❌ (−0.000393 / +0.000321, e anche col calendario corretto); squad_value/absence ❌/❌ (+0.000873 con 0/6 stagioni / +0.000799); anticipo del movimento apertura→chiusura ❌/❌; ricalibrazione-μ GG/NG ❌ in Ligue 1
- **Trovato**: Tutte queste celle contengono ⬜, che la legenda del file (docs/PANCHINA.md:20) definisce esplicitamente «mai testato lì: è lavoro potenziale»
- **Come è stato accertato**: Confronto cella per cella fra la matrice (parsing programmatico delle 46 righe × 7 colonne) e le tabelle di docs/audit_5_leghe/10_modelli_nuove_leghe.md:801-812 (leve di panchina del DC), :836-842 (covariate), :906-930 (§13 «La rosa aggiornata, per le due leghe nuove»). Il commit di integrazione 46bf0fc dichiara «ogni modello ha ora il suo stato anche su Bundesliga e Ligue 1 (46 righe estese)», ma 36 righe su 46 hanno ricevuto ⬜ e in 9 di esse la misura esiste.
- **Correzione**: Riportare nelle 18 celle gli stati e i Δ del report 10 §12-13; aggiornare anche la cella «generale» della riga `rest_full` (docs/PANCHINA.md:76: «rumore su 3/3 leghe» → 5/5, come scritto nel report: «`rest_full` è ora rumore su 5 leghe su 5»).
- **Verifica avversariale**: Il fatto e' vero e l'ho ricontato: le celle Bundesliga/Ligue 1 marcate ⬜ su righe che l'audit integrato HA misurato sono ~17-18 (ensemble emivite, ricalibrazione per-classe del modello, diagonale inflazionata, temperature scaling, rest_full, midweek_europe, covariate squad_value/absence = 14 celle; + movimento apertura→chiusura 2; + ricalibrazione-μ GG/NG in Ligue 1 1; + la cella «generale» di rest_full che dice ancora 3/3 leghe). Ma la severita' «alta» non regge per due motivi verificati: (a) ⬜ E' uno stato della legenda, quindi il messaggio del commit 46bf0fc («ogni modello ha ora il suo stato anche su Bundesliga e Ligue 1») non e' letteralmente falso; (b) nessun numero e nessuna conclusione del progetto e' sbagliata — e' un registro non allineato al report da cui doveva essere compilato. Attenzione a un dettaglio dove l'auditor sbaglia: la cella Bundesliga della riga GG/NG (PANCHINA:68) e' correttamente ⬜, perche' il report stesso scrive «⬜ non dimostrata (era 🪑)»; solo la cella Ligue 1 va portata a ❌. Anche il suo conteggio dei simboli e' impreciso (❌ 72 contro i 65 reali: 138+48+25+72=283 > 276 celle).

**🟠 `F8-04-leve-nuove-senza-riga` — Quattro leve misurate nell'audit integrato non hanno alcuna riga nella rosa**  
*omissione · media · ridimensionato*

- **Dove**: docs/PANCHINA.md:56-103 (matrice) e :159-175 (tabella panchina)
- **Atteso**: Per CLAUDE.md §2 («modello nuovo → riga nuova») dovrebbero esistere: (a) «market-implied dall'APERTURA» ⚽ titolare su BL/L1 (25/25 sul DC, 24/25 sulla baseline, 5.842 partite); (b) «estremizzazione della chiusura O/U» (α≈1.15-1.33) 🪑 su entrambe; (c) «θ leave-one-league-out sulla famiglia GG/clean-sheet in calibrazione» 🪑 su entrambe; (d) «dp_tilt» (θ + solo tilt) in Serie A, −0.0020 su entrambi i protocolli, 7/7 e 6/6, «eguaglia dp_lvl con un parametro in meno»
- **Trovato**: Nessuna riga per nessuna delle quattro; `grep -rn "dp_tilt|estremizzazione" docs/ README.md` non trova nulla fuori dai report dell'audit
- **Come è stato accertato**: docs/audit_5_leghe/10_modelli_nuove_leghe.md:911 (apertura), :921 (estremizzazione O/U), :922 (θ calibrazione), :386-389 (§7.3 dp_tilt); `grep -rn "dp_tilt\|estremizzazione\|leave-one-league-out" docs/PANCHINA.md docs/PISTE.md README.md` → 0 occorrenze.
- **Correzione**: Aggiungere le quattro righe con stato per lega + fronte generale, oppure — se si ritiene che (b)(c)(d) siano piste e non modelli — registrarle in docs/PISTE.md e dirlo nella rosa. Oggi non sono in nessuno dei due registri.
- **Verifica avversariale**: Tre delle quattro leve sono davvero assenti da OGNI registro (rosa e piste): l'estremizzazione della chiusura O/U (α≈1.15-1.33), il θ sulla famiglia GG/clean-sheet in calibrazione e `dp_tilt` — greppati a zero occorrenze fuori dai report dell'audit. La quarta, «market-implied dall'APERTURA», e' invece un falso positivo: il modello HA una riga (PANCHINA:58) e la colonna «generale» di quella riga cita gia' esplicitamente «F75: 17/20 dall'apertura su 2.280 partite vergini»; quello che manca e' solo la menzione dell'apertura nelle due celle nuove, non «alcuna riga nella rosa». Da notare anche che il θ-in-calibrazione non e' semplicemente «assente»: e' in tensione con quanto la riga 59 gia' dice (❌ 0/25 mercati in BL/L1), perche' il report lo promuove a 🪑 su un criterio diverso dal log-loss (raddrizza il bias GG −0.0238→−0.0106 in BL e −0.0206→−0.0049 in L1) — quindi la correzione giusta e' una riga nuova o una nota, non la riscrittura della cella del router.

**🟠 `F8-06-tassonomia-latine-inglesi-ritirata` — Ricalibrazione per-classe del mercato: la riga usa ancora la tassonomia «latina/inglese» che il report integrato ha esplicitamente RITIRATO, assegna 🪑 a un guadagno negativo e cita in La Liga un numero che è un ROI di un'altra leva**  
*incoerenza-doc · media · ridimensionato*

- **Dove**: docs/PANCHINA.md:69 (celle La Liga, Bundesliga, Ligue 1)
- **Atteso**: Nessuna etichetta «latina/inglese» (la spiegazione è ritirata: w_D La Liga = 0.978, il segno è sparso); stessa classificazione per BL e L1, che hanno risultati identici (+0.00078 e +0.00076, entrambi «nel rumore», entrambi peggiorativi); per La Liga il Δ della ricalibrazione (F53 w_D=1.010; F100 delta +0.00002 «nel rumore»), non un ROI
- **Trovato**: «🪑 w_D=1.089 («latina») ma guadagno negativo» (BL), «❌ w_D=0.981 («inglese»)» (L1), «🪑 F53 (+3.6% P81)» (Liga — che è il ROI pari-equilibrio del draw-bias, non la ricalibrazione)
- **Come è stato accertato**: docs/audit_5_leghe/10_modelli_nuove_leghe.md:216-243 §5A: «Qui c'era un errore di tabella… Con il numero giusto la tassonomia «latine / inglesi» non esiste… La spiegazione che era stata proposta qui va ritirata». Artefatto docs/audit_5_leghe/numeri/leve_ricalibrazioni.json: bundesliga delta +0.00078 «nel rumore», ligue_1 +0.00076 «nel rumore», la_liga w_D 0.9778. docs/DIARIO.md (Fase 53, tabella): w_D Liga 1.010 e «ROI pari-equilibrio +3.6% (P 81%)» — il +3.6% appartiene al lead draw-bias, che in PANCHINA sta a riga 323. Inoltre 🪑 contraddice la legenda del file (riga 7: «misurati migliorativi ma NON attivati»).
- **Correzione**: Togliere le etichette «latina»/«inglese», uniformare lo stato di BL e L1 (misure equivalenti), sostituire il «+3.6% P81» della cella Liga col Δ della ricalibrazione e spostare l'ROI dove appartiene (riga «Lead operativi»).
- **Verifica avversariale**: Il rilievo e' composito: una parte regge, una e' SBAGLIATA e il suo `fix` sarebbe dannoso. REGGE: le etichette «latina»/«inglese» nelle celle BL/L1 della riga sono esattamente l'uso che il report §5A dichiara ritirato per QUESTA leva (con w_D Liga = 0.978 la tassonomia «non esiste»); ed e' vero che il «+3.6% P81» della cella La Liga e' il ROI pari-equilibrio della Fase 53 (cioe' il lead draw-bias, che nel file ha gia' la sua riga fra i «Lead operativi»), non il Δ della ricalibrazione, la cui grandezza in Liga e' w_D=1.010 ≈ nessuna correzione. CADE il punto centrale: «uniformare lo stato di BL e L1 perche' i risultati sono identici». Gli stati 🪑 (BL) / ❌ (L1) NON sono un'invenzione della rosa — sono precisamente quelli proposti dal report integrato, e hanno un motivo misurato che l'auditor non ha letto: sul path DC la stessa leva peggiora in Ligue 1 con CI CONCLUSIVO (+0.002200 [+0.00036,+0.00402]) mentre in Bundesliga no (+0.002807 [−0.00009,+0.00572]). Applicare il `fix` proposto cancellerebbe una distinzione corretta. Nota: l'etichetta «latine» non e' bandita in generale (README:257 la usa legittimamente per il θ); e' ritirata solo come spiegazione del w_D.

**🟡 `F8-05-shin-conclusivo-senza-caveat` — Devig di Shin: la riga dichiara «CI conclusivo sul Brier» proprio dove la verifica avversariale ha tolto la conclusività, e il fronte generale dice «sempre ≥ moltiplicativo» quando 2 leghe su 5 peggiorano**  
*conclusione-non-supportata · bassa · ridimensionato*

- **Dove**: docs/PANCHINA.md:70 (celle Bundesliga, Ligue 1 e «generale»)
- **Atteso**: «conclusivo su Brier ma NON a cluster di lega ([−0.000414, −0.0000008], tocca lo zero); migliora 3 leghe su 5; conclusivo solo nelle latine» — cioè la formulazione già scritta nel report integrato
- **Trovato**: «🪑 pooled 5 leghe: CI conclusivo sul Brier, p=0.052 sul log-loss» (BL e L1) e «🪑 sempre ≥ moltiplicativo» (generale), mentre il dettaglio per lega dà Premier Δ Brier +0.00002 e Bundesliga +0.00003 (peggiorano)
- **Come è stato accertato**: docs/audit_5_leghe/10_modelli_nuove_leghe.md:178-196: tabella pooled (Brier −0.00021 [−0.00039,−0.00001]), poi «rifatto a cluster di lega, il CI sul Brier diventa [−0.000414, −0.0000008], cioè tocca lo zero» e la tabella per lega con premier_league +0.00002 e bundesliga +0.00003.
- **Correzione**: Riscrivere le tre celle con il caveat del cluster e sostituire «sempre ≥ moltiplicativo» con «≥ in 3 leghe su 5; conclusivo solo nelle latine, e non a cluster di lega».
- **Verifica avversariale**: Il rilievo confonde una sfumatura con un errore. (1) «CI conclusivo sul Brier» NON e' un numero inventato ne' un CI letto male: e' esattamente la riga della tabella di testa del report (Brier −0.00021 [−0.00039,−0.00001]); quello che manca in cella e' il caveat del bootstrap a cluster di lega — un'omissione di sfumatura, non una conclusione sbagliata, tanto piu' che lo stato resta 🪑 (non attivato) in tutte e cinque le leghe, cioe' la decisione operativa e' identica con o senza caveat. (2) «sempre ≥ moltiplicativo» e' invece davvero inaccurato dopo il passaggio a 5 leghe, ma l'ho quantificato: le due leghe che «peggiorano» lo fanno di +0.000053 (Premier) e +0.000161 (Bundesliga) sul log-loss e +1.7e-05 / +2.6e-05 sul Brier, entrambe con verdetto «nel rumore» nell'artefatto stesso. E' il quinto decimale: una frase da ritoccare, non una conclusione non supportata.

**🟡 `F8-07-titolari-non-in-produzione` — Corner/cartellini, binomiale negativa e mercati Tier 3 sono ⚽ «titolari» nella matrice ma non esistono in src/models/, non sono in predict.py e non compaiono nella sezione «I titolari»**  
*incoerenza-doc · bassa · ridimensionato*

- **Dove**: docs/PANCHINA.md:97, 98, 100 (celle ⚽) contro docs/PANCHINA.md:143-153 (sezione «⚽ I titolari»)
- **Atteso**: Per la definizione del file (riga 6: «⚽ TITOLARI — in config ufficiale o attivi nei tool») un titolare deve essere in `src/config.py`/`src/models/`/`scripts/predict.py`, ed essere elencato nella tabella dei titolari
- **Trovato**: Il modello di conteggio della Fase 96, la NB della Fase 98 e i mercati Tier 3 vivono solo in script diagnostici (`scripts/_run_counts_nb.py`, `_run_counts_level.py`, `_run_listino_validazione.py`, `_run_polymarket_tier3.py`); `ls src/models/` non contiene nulla sui conteggi né sui tempi; `scripts/predict.py` non stampa né corner/cartellini né HT/2T; la tabella dei titolari (7 righe) non li menziona
- **Come è stato accertato**: `ls src/models/` → bivariate_poisson, copula_scores, dixon_coles, market_denoise, market_implied, season_sim. `grep -rn "corner\|halftime\|second_half" src/ scripts/predict.py` → 0 occorrenze. Esecuzione di `python3 scripts/predict.py Bayern\ Munich Dortmund --league bundesliga --odds …`: il listino stampato è solo Tier 1 sui gol.
- **Correzione**: O si aggiungono le tre voci alla tabella «I titolari» dichiarando dove sono attive (script del listino, non `predict.py`), o si abbassa lo stato a 🪑/nota «validato, non ancora in un tool».
- **Verifica avversariale**: I fatti materiali sono confermati (nessun modulo sui conteggi o sui tempi in src/models/, nessuna traccia in scripts/predict.py, e le tre voci mancano dalla tabella «⚽ I titolari»), ma la tesi «non sono in produzione / vivono solo in script diagnostici» e' fuorviante. Il modello di conteggio della Fase 96 vive in scripts/_run_outside_matrix.py e viene IMPORTATO (non copiato) sia da _run_counts_nb.py sia da scripts/_run_listino_validazione.py, che il progetto presenta esplicitamente come «il LISTINO come prodotto» e che salva l'artefatto experiments/listino_validazione.json: la legenda della rosa dice «in config ufficiale o attivi nei tool», e quello e' un tool. Il residuo reale e' quindi solo documentale (tabella dei titolari non estesa e nessuna indicazione di DOVE sono attivi), non un titolare inesistente. Da segnalare, ma bassa.

**🟡 `F8-13-segno-pp-neopromosse` — Deriva di forza: lo scarto di calibrazione delle neopromosse è riportato col segno opposto alla fonte**  
*incoerenza-doc · bassa · ridimensionato*

- **Dove**: docs/PANCHINA.md:65 (cella «generale»)
- **Atteso**: «+6.1pp → +2.8pp» (scarto dichiarato − realizzato), come in src/config.py:164-166 e docs/DIARIO.md (Fase 94, tabella «calibrazione»)
- **Trovato**: «neopromosse −6.1pp→−2.8pp»
- **Come è stato accertato**: src/config.py:165-166 («calibrazione delle neopromosse da +6.1pp a +2.8pp»); docs/DIARIO.md:10063-10067 (tabella con «+6.1pp / +2.8pp»). La riga 64 della PANCHINA usa invece la convenzione opposta (realizzato − dichiarato, «−10.1pp» dalla Fase 91): le due convenzioni convivono nella stessa colonna.
- **Correzione**: Uniformare la convenzione dei pp in tutta la matrice e dichiararla una volta in testa al file.
- **Verifica avversariale**: Il `fix` proposto («uniformare la convenzione dei pp in tutta la matrice») e' basato su una lettura sbagliata: la matrice E' gia' uniforme. Le righe 64 e 65 usano entrambe la convenzione realizzato−dichiarato (−10.1pp e −6.1pp→−2.8pp); sono le FONTI a usarne due, ed entrambe le dichiarano — docs/DIARIO.md:9663 (F91) scrive «−10.1pp» come realizzato−dichiarato, docs/DIARIO.md:10061 (F94) scrive «scarto dichiarato−realizzato +6.1pp → +2.8pp» con l'etichetta esplicita nella colonna. Quindi non c'e' nessun «segno invertito» dentro la rosa, solo una convenzione diversa da quella di src/config.py, non dichiarata in testa al file. Segnalo per contro che il vero problema di quelle due celle e' un ALTRO, che l'auditor non ha visto e anzi ha usato come metro: il «−10.1pp» della riga 64 e' il valore PRE-Fase 92, superato dal fix del prior (−10.1 → −6.1) come dice il README stesso.

**🟡 `F8-15-squad-value-titolare-ma-zero-stime` — Lo stimatore squad_value è dichiarato titolare «tool stime» ma dalla Fase 70 non produce più alcuna stima**  
*incoerenza-doc · bassa · ridimensionato*

- **Dove**: docs/PANCHINA.md:67 e :151
- **Atteso**: Coerenza con docs/DATI.md:231 e :245 («0 righe — svuotato alla Fase 70; nessuna stima attiva»)
- **Trovato**: «⚽ tool stime» su tre leghe e riga fra i titolari con «dove è attivo: `scripts/build_estimates.py` → `data/estimates/`»
- **Come è stato accertato**: `data/estimates/squad_value_2017_26.csv` contiene solo l'intestazione (0 righe, verificato con pandas); docs/DATI.md:231 lo dichiara. Collaterale nella stessa catena: `data/estimates/README.md:57-60` dice ancora «restano 13 celle, tutte della stagione in corso 2025-26», in contraddizione con DATI.md.
- **Correzione**: Marcare la voce come «⚽ pronto ma inattivo (0 stime dalla F70)» in PANCHINA e allineare data/estimates/README.md a DATI.md.
- **Verifica avversariale**: Il fatto base regge (il CSV ha 0 righe dati e DATI.md lo dichiara), ma il collaterale — la parte piu' seria del rilievo — e' SMONTATO: data/estimates/README.md NON contraddice DATI.md, perche' si apre alla riga 1 con un banner «⚠️ Nessuna stima `squad_value` attiva dalla Fase 70: le ultime 13 celle sono state sostituite da dato REALE (Transfermarkt) e il file CSV e' a 0 righe. Quanto segue resta il metodo storico, valido se il buco si riaprisse». Le «13 celle» della riga 59 stanno dentro la sezione che quel banner copre, ed e' pure intitolata «Perche' (ridimensionato dalla Fase 67)»: e' narrazione storica dichiarata, non un dato corrente sbagliato. Quanto alla cella ⚽, la rosa non afferma che esistano stime: la voce dei titolari dichiara «dove e' attivo: scripts/build_estimates.py → data/estimates/», che e' vero (lo script gira e produce 0 righe perche' non ci sono buchi). Resta solo il suggerimento cosmetico di aggiungere «pronto ma inattivo».

<details><summary>Verifiche con esito OK su questo fronte</summary>

- Struttura della matrice: 46 righe-modello, tutte con esattamente 7 colonne (modello + 5 leghe + generale); nessuna riga malformata, nessuna colonna mancante (parsing programmatico di docs/PANCHINA.md:56-103). Prima dell'integrazione erano 46 righe × 5 colonne (git show 12da9e0).
- Riga 62 (Dixon-Coles + xG): δ 0.23/0.33/0.22/0.28/0.19 coincidono esattamente con src/config.py (SERIE_A, PREMIER_LEAGUE, LA_LIGA, BUNDESLIGA, LIGUE_1) e con la tabella δ della Fase 100 nel diario.
- Righe 59/60/61 (router θ, φ35, dp_lvl) contro il codice di produzione: src/config.py MARKET_ENGINE attiva θ=1.225/1.138, φ0=0.30, κ=1.5 e sharpen_1x2 SOLO per la Serie A; Premier e Liga sono a motore liscio; Bundesliga e Ligue 1 non sono in MARKET_ENGINE e cadono sul fallback liscio di market_engine(). Verificato eseguendo scripts/predict.py --league bundesliga --odds: stampa «motore LISCIO per bundesliga». Nessun titolare dichiarato che sia off nel codice, e nessuna leva attiva di default che sia dichiarata panchina.
- Riga 59 Serie A e riga 59 La Liga + voci 1-bis/1-ter: numeri lfo RIPRODOTTI ri-eseguendo scripts/_run_fase81_mega_sweep_mi.py — Serie A ris.esatto lfo Δ−0.0078 (P100%)*; La Liga ris.esatto lfo Δ−0.0069*, 1X2 lfo Δ−0.0023*, GG/NG lfo Δ−0.0025*, tutti con CI che esclude lo zero, esattamente come scritto.
- Riga 98 e nota ✱8 (binomiale negativa sui conteggi): ri-eseguito scripts/_run_counts_nb.py — corner +0.00103 [+0.00062,+0.00143], cartellini +0.00088 [+0.00033,+0.00142], gialli Serie A var/μ condizionata 0.901 con Δ esattamente 0.00000, e 3 celle su 21 (lega × linea) che peggiorano con IC conclusivo. Tutto esatto.
- Riga 99 e ✱8 (correzione di livello): ri-eseguito scripts/_run_counts_level.py — corr(bias_t, bias_{t−1}) +0.2299 [−0.2544,+0.6715] e +0.1915 [−0.3446,+0.5830], 10/18 stesso segno, sd 0.3558/0.3841 contro bias pooled 0.1387/0.0383 (2,6× e 10×), Serie A corner +0.352→+0.031 con Δ +0.00271 [−0.00051,+0.00590] non conclusivo, invarianza della NB +0.00103→+0.00106 e +0.00088→+0.00067. Tutti i numeri della cella tranne il conteggio «6/8» (finding F8-02).
- Righe 85, 100, 101, 102, 103 e voci dei bocciati F87/F89/F89-bis/F86-bis: verificate contro il diario — COM-Poisson 2.8321 vs 2.8322 e ν=1.15; θ per-squadra +0.00096 su 5.690 partite (2.8222 vs 2.8212); isotonica +0.0061…+0.0150 e mistura −0.00042 [−0.00145,+0.00059] P 78.6%; Tier 3 f=0.4396 [0.4338,0.4458], HT +0.0537, 2T +0.0578, esatto +0.1940, pareggio 2T 0.3671 vs 0.3427; arbitro 0/3420 in SA e Liga e «85% del guadagno era livello»; formazioni +0.9603 e −0.1227; movimento β −0.0039 R² 0.0001, CLV −0.0022, 15,6% del gap; temperatura sul campione LOO 1.2160 vs 1.1994; squad_value sul campione 1.2384 vs 1.1994 con 2/16.
- Riga 63 (mercato campione) e riga 64 (mercati posizionali): +0.2299 [+0.0108,+0.4542] 14/24, 60.1% dichiarato vs 41.7% realizzato, baseline 1.4293→1.3816 con IC che include lo zero, ~57 stagioni-lega e 9,8% di potenza, ECE top-4 0.0137 e −10.1pp sulle neopromosse: tutti coincidenti col diario (Fasi 89/91/98).
- Riga 66 (stimatore E3): MAE 0.0143 (Bundesliga) e 0.0125 (Ligue 1) nel regime d'uso coincidono con docs/audit_5_leghe/09_chiusura_buchi.md §3 e con il blocco 📐 della Fase 100; scripts/build_estimates.py copre davvero 5 leghe e data/estimates/ou_close_2017_19.csv ha 3.638 righe su 5 leghe.
- Tutte le «attivazioni» citate nelle voci di panchina esistono: --draw-balance, --draw-inflation, --covariates (scripts/backtest.py), market_implied.btts_season / season_mu_factor / sharpen_1x2, src/models/market_denoise.py, src/evaluation/calibration.py, scripts/calibrate.py, scripts/build_estimates.py, src/models/season_sim.py, scripts/_run_fase89_season_champion.py.
- Nessun link markdown rotto in README.md, CLAUDE.md, lavoro_aperto.md, newseason.md, docs/*.md, experiments/*.md e data/estimates/*.md (verifica programmatica di tutti i target relativi).
- Righe 61 (dp_lvl fuori dalla Serie A) e 87 (power-devig) sulle due leghe nuove: «PEGGIORA la chiusura (CI conclusivo), ROI −22%» e «−13%» coincidono con docs/audit_5_leghe/10_modelli_nuove_leghe.md §7 (bundesliga +0.0016 [+0.0004,+0.0027] e ROI −22,46%; ligue_1 ROI −12,90%) e §5C (power-devig BL +0.00035 [+0.00004,+0.00066]).

</details>

### Coerenza fra i documenti  ·  26 rilievi
**🔴 `F9-script-cantiere-rotti` — I 27 script importati dal cantiere hanno ROOT sbagliato e leggono da cantiere/: nessuno parte, e gli snapshot Bundesliga/Ligue 1 non sono piu' rigenerabili**  
*import-rotto · alta · **confermato***

- **Dove**: scripts/eda_nuove_leghe.py:27-37, scripts/build_new_snapshot.py:35-45, scripts/audit_snapshots.py:36-42, scripts/tranche3_tracer.py:37-49, scripts/nuovo_mercato_campione.py:96-133, e altri 22 file (elenco: applica_correzioni, applica_squad_value_tm, audit_anomalie, cerca_segnaposto, fetch_sources, leve_beat_close, leve_dc_panchina, leve_devig_shin, leve_ricalibrazioni, leve_theta_griglia, nuove_leghe, nuovo_calibrazione, recupero_squad_value_tm, riconcilia_nomi, stima_celle_residue, stima_ou_close_nuove, stima_ou_corrotte, stima_sot_understat, tranche3_market_tracer, tranche3_mercati, tranche3_ritaratura, verifica_stime)
- **Atteso**: Dopo lo spostamento cantiere/scripts/ -> scripts/, ROOT deve essere parents[1] e i percorsi dati devono puntare a data/ e data/ricerca_esterna/. Gli script devono partire e gli snapshot delle 2 leghe nuove devono essere rigenerabili offline (CLAUDE.md §1.5 riproducibilita').
- **Trovato**: ROOT = Path(__file__).resolve().parents[2] e' rimasto invariato: da scripts/ punta a /home/user invece che alla radice del repo, quindi `import src` fallisce prima di qualsiasi altra cosa. Inoltre i percorsi dati sono ancora ROOT/'cantiere'/'data' e ROOT/'cantiere'/'out', cartelle cancellate.
- **Come è stato accertato**: `timeout 60 python scripts/eda_nuove_leghe.py` -> ModuleNotFoundError: No module named 'src' (via scripts/nuove_leghe.py:31). Idem `python scripts/build_new_snapshot.py`. `grep -l 'parents\[2\]' scripts/*.py | wc -l` -> 27. `ls -d data/fonti` -> No such file or directory (e 00_indice.md:23 dichiara che quelle fonti sono state rimosse). Nessun altro percorso rigenera data/bundesliga_matches.csv: scripts/build_league_snapshot.py:59 richiede files/football_data_{key}_bundle.json e `ls files/` mostra bundle solo per premier_league e la_liga.
- **Correzione**: Sostituire parents[2] -> parents[1] in tutti e 27 gli script e ri-puntare CANTIERE_DATA/FONTI/OUT a data/, data/ricerca_esterna/ e outputs/ (o docs/audit_5_leghe/numeri/). Se le fonti grezze non tornano in repo, dichiarare esplicitamente in docs/DATI.md §6 che i due snapshot nuovi si rigenerano solo ri-scaricando con scripts/fetch_sources.py (rete ora raggiungibile).

**🟠 `F9-link-rotti-audit` — 13 link markdown rotti in docs/audit_5_leghe/: i report si linkano ancora come report/NN_*.md e REGOLE.md punta a data/*.csv sotto la propria cartella**  
*import-rotto · media · **confermato***

- **Dove**: docs/audit_5_leghe/00_indice.md:36,37,38,39,41,42,44,45,46,47,48; docs/audit_5_leghe/REGOLE.md:32,96
- **Atteso**: [`01_audit_dati.md`](01_audit_dati.md) (fratelli nella stessa cartella) e [`data/correzioni_dichiarate.csv`](../../data/correzioni_dichiarate.csv).
- **Trovato**: I link puntano a docs/audit_5_leghe/report/01_audit_dati.md ... /11_ggng.md e a docs/audit_5_leghe/data/correzioni_dichiarate.csv, docs/audit_5_leghe/data/squad_value_2526_transfermarkt.csv: 13 percorsi inesistenti. E' l'indice da cui parte chi vuole rifare un conto (righe 9-10).
- **Come è stato accertato**: Script di risoluzione dei link relativi su tutti i doc del fronte: 13 target non esistenti, tutti in docs/audit_5_leghe/. I file veri sono docs/audit_5_leghe/0N_*.md, data/correzioni_dichiarate.csv e data/squad_value_2526_transfermarkt.csv (verificati con ls).
- **Correzione**: Sed sui link: `report/` -> `` in 00_indice.md; `data/` -> `../../data/` in REGOLE.md.

**🟠 `F9-celle-residue-stantie` — data/estimates/celle_residue.csv descrive come «finto pieno da svuotare» tre celle che il guard applicato all'integrazione ha gia' svuotato, e rimanda a percorsi cantiere/ inesistenti**  
*incoerenza-doc · media · **confermato***

- **Dove**: data/estimates/celle_residue.csv righe 22,23,25 (colonne valore_attuale/verdetto) e righe 22-25,27-31 (colonne note/metodo)
- **Atteso**: Il registro delle celle non stimate deve riflettere lo snapshot attuale e puntare a percorsi esistenti (data/ricerca_esterna/, docs/audit_5_leghe/numeri/).
- **Trovato**: Alaves-Real Madrid (valore_attuale «1.53/1.59»), Eibar-Real Madrid e Leganes-Betis sono elencate come «FINTO PIENO: valori presenti ma fuori scala ... Da svuotare»: nello snapshot odds_over25_open/odds_under25_open sono gia' NaN. Le note dicono «gia' segnalata in cantiere/out/caccia_quote_singole.json» e il metodo delle 5 righe midweek_europe cita «cantiere/data/ricerca/fixtures_*.csv»: entrambe le cartelle non esistono.
- **Come è stato accertato**: pandas su data/la_liga_matches.csv: le 3 partite hanno odds_over25_open NaN. Il guard e' in produzione (src/data/loader.py:99 `ORR_MAX = 1.12`, :218 `if orr < 1.0 or orr > ORR_MAX`). I file veri esistono in docs/audit_5_leghe/numeri/caccia_quote_singole.json e data/ricerca_esterna/fixtures_*.csv (ls).
- **Correzione**: Rigenerare celle_residue.csv contro lo snapshot corrente (le 3 righe escono, restano Leganes-Getafe orr 1.0127 e Dortmund-Hannover orr 1.0947 che il guard non intercetta) e riscrivere i percorsi in note/metodo.

**🟠 `F9-patch-guard-non-applicata` — patch_guard_overround_APPLICATA.md dichiara nel corpo «Non applicata» mentre il guard e' in produzione**  
*incoerenza-doc · media · **confermato***

- **Dove**: docs/audit_5_leghe/patch_guard_overround_APPLICATA.md:3-4 e 84-88
- **Atteso**: Il corpo deve dire che la patch e' stata applicata all'integrazione (nome del file) e che la verifica va rifatta con comandi eseguibili.
- **Trovato**: Riga 3: «**Non applicata**: il lavoro di questa sessione non tocca `src/`. Da valutare all'integrazione.» Il blocco «Verifica dopo l'applicazione» propone `python cantiere/scripts/audit_anomalie.py`, comando morto.
- **Come è stato accertato**: src/data/loader.py:99 definisce ORR_MAX = 1.12 e :218 lo usa esattamente come nella patch; il test suggerito dalla patch e' coperto dalla suite (194 test verdi). `ls cantiere` -> assente.
- **Correzione**: Aggiungere in testa «APPLICATA all'integrazione (commit ec85314), guard in src/data/loader.py:99/218» e correggere i comandi di verifica.

**🟠 `F9-caccia-apertura-invertita` — Due documenti ripetono l'inversione apertura/chiusura che la Fase 73 aveva corretto (e ignorano che la caccia e' chiusa)**  
*conclusione-non-supportata · media · **confermato***

- **Dove**: CLAUDE.md:294-295; lavoro_aperto.md:246-247
- **Atteso**: Il buco 2017-19 e' sulla **chiusura** O/U (l'apertura `BbAv` e' dato reale dalla Fase 73), e la caccia e' **chiusa** dalla Fase 100 (dato 1xBet trovato, non inserito perche' single-book).
- **Trovato**: CLAUDE.md:294: «docs/CACCIA_OU_2017_19.md piano dedicato per l'ultimo buco dati reale (O/U **apertura** 2017-19)». lavoro_aperto.md:246: «le quote di **apertura** 2017-19 mancavano e sono state in parte ricostruite».
- **Come è stato accertato**: docs/DATI.md:101-110 e docs/CACCIA_OU_2017_19.md:55-64 dichiarano l'opposto («Il buco O/U 2017-19 e' sulla CHIUSURA, non sull'apertura (chiarito Fase 73)»); docs/CACCIA_OU_2017_19.md:1 «CHIUSA: il dato e' stato trovato». Verificato sui dati: NaN di odds_over25 (chiusura) nel 2017-19 = 760+760+760+612+758 su 5 leghe; NaN di odds_over25_open = 12 in tutto.
- **Correzione**: CLAUDE.md:294 -> «piano (CHIUSO alla Fase 100) per la chiusura O/U 2017-19»; lavoro_aperto.md:246 -> «le quote di chiusura 2017-19 mancavano e sono coperte da una stima dichiarata».

**🟠 `F9-piste-non-aggiornate-f100` — docs/PISTE.md non e' mai stato aggiornato dopo la Fase 100: le piste 16 e 19 restano aperte con motivazioni gia' falsificate**  
*omissione · media · **confermato***

- **Dove**: docs/PISTE.md:11; 407-413 (pista 16); 442-461 (pista 19)
- **Atteso**: Regola §2 del CLAUDE.md: «Va aggiornato quando una pista si apre, si prova o si chiude». La Fase 100 ha trovato le quote GG/NG (5.337 partite) e la chiusura O/U 1xBet 2017-19 (3.652 partite, 100%).
- **Trovato**: Pista 16 (407-410): «**Dato**: NON esiste in nessun archivio (verificato); solo raccolta da oggi in avanti» e «il GG/NG e' l'unico mercato senza tetto di efficienza dimostrato (principio §1.8)». Pista 19 (447-461): «Fase A ... e Fase B ... chiuse negative», «Non e' un buco chiuso per sempre: solo le vie economiche note oggi sono esaurite», con promemoria a riprovare. Header riga 11: «Ultimo aggiornamento: Fase 89» (il file contiene gia' F92/F93/F98/F99).
- **Come è stato accertato**: `grep -in 'footiqo|1xbet|Fase 100' docs/PISTE.md` -> 0 occorrenze. docs/CACCIA_OU_2017_19.md:1-45 e docs/audit_5_leghe/11_ggng.md documentano entrambi i ritrovamenti; docs/audit_5_leghe/numeri/ggng_contro_quote.json ha n_finale = 5337.
- **Correzione**: Aggiungere a pista 16 e 19 un blocco «Aggiornamento Fase 100» come gia' fatto per la pista 18, e aggiornare l'header a Fase 100.

**🟠 `F9-premessa-ggng-non-propagata` — La premessa caduta «il GG/NG e' l'unico mercato senza quote / senza tetto» sopravvive in tre documenti che la citano come vigente**  
*conclusione-non-supportata · media · **confermato***

- **Dove**: lavoro_aperto.md:96 e 210-217; newseason.md:204-211 e 255; docs/STUDIO_PREMIER_LIGA.md:178
- **Atteso**: CLAUDE.md §1.8 (righe 45-62) barra la premessa: «PREMESSA CADUTA ... Lo spazio non era una proprieta' del mercato: era la nostra ignoranza».
- **Trovato**: lavoro_aperto.md:212-215: «Il `CLAUDE.md` §1.8 dice che il GG/NG e' **l'unico mercato senza quote nei dati** ... quindi **l'unico dove non abbiamo mai potuto dimostrare l'efficienza del mercato**». newseason.md:204-206 ripete la stessa frase citando §1.8; newseason.md:255: «Quote GG/NG (§8.4) — l'unico mercato ancora aperto». STUDIO_PREMIER_LIGA.md:178: «il GG/NG e' il mercato senza tetto dimostrato».
- **Come è stato accertato**: CLAUDE.md:45-62 (testo barrato + PREMESSA CADUTA). L'artefatto docs/audit_5_leghe/numeri/ggng_contro_quote.json documenta il tetto: nessuna variante nostra batte il book (D2 tutti «nel rumore»), D4_ROI «NON misurato: nessun nostro prezzo batte il book».
- **Correzione**: In tutti e tre i punti: sostituire con «il GG/NG e' quotato dal 2017-20 (1xBet, 5.337 partite): il mercato e' informativo e il nostro prezzo lo pareggia — resta interessante solo perche' il book non lo quota nelle stagioni recenti».

**🟠 `F9-rete-tornata-non-propagata` — «La rete e' bloccata» sopravvive in cinque documenti (con tabelle di 403) dopo che la Fase 100 ha verificato il contrario**  
*incoerenza-doc · media · **confermato***

- **Dove**: lavoro_aperto.md:182-196 (§6.1); newseason.md:164-180 (§8.1); experiments/prospettico_2026_27.md:25-26 e 85-89; docs/PISTE.md:724-731 (§6); docs/DATI.md:166; docs/MANUALE_SOPRAVVIVENZA.md:49
- **Atteso**: docs/MANUALE_SOPRAVVIVENZA.md:3-14 dichiara football-data.co.uk, understat.com, transfermarkt.com e Kaggle **raggiungibili (200)** dalla sessione.
- **Trovato**: lavoro_aperto.md §6.1 e newseason.md §8.1 propongono come «il punto con il rapporto valore/costo piu' alto» un probe.yml dal runner Actions, con tabelle che danno football-data/Understat/SofaScore a 403 e Transfermarkt «bloccato»; newseason.md:177 «oggi viviamo di bundle caricati a mano». prospettico_2026_27.md:85 «`WebFetch` e' **bloccato del tutto** (403 anche su Wikipedia)» — mentre la Fase 100 ha recuperato 3.045 righe di calendario coppe proprio da Wikipedia. PISTE.md:726 «Canale unico per tutto cio' che il proxy blocca: workflow GitHub Actions». DATI.md:166 «il sito originale non e' raggiungibile dal cloud». MANUALE stesso: «Ultimo aggiornamento: Fase 70».
- **Come è stato accertato**: docs/MANUALE_SOPRAVVIVENZA.md:8-14 (tabella prima/oggi). Verifica indipendente in sessione: `curl -sS -o /dev/null -w '%{http_code}' -H 'X-Requested-With: XMLHttpRequest' https://understat.com/getLeagueData/Serie_A/2024` -> 200. data/ricerca_esterna/ contiene 25 JSON footiqo + fixtures_* da Wikipedia scaricati in quella fase.
- **Correzione**: Marcare come superate le tabelle §6.1/§8.1 (o degradare probe.yml da ⭐ a nota storica), aggiornare PISTE §6 e DATI:166, e portare «Ultimo aggiornamento» del MANUALE a Fase 100.

**🟠 `F9-leghe-nuove-da-non-fare` — newseason.md e lavoro_aperto.md sconsigliano ancora di «aggiungere le leghe nuove», cosa gia' fatta dalla Fase 100**  
*conclusione-non-supportata · media · **confermato***

- **Dove**: newseason.md:149-154 (§7 «Cosa NON farei adesso»); lavoro_aperto.md:338-340
- **Atteso**: Bundesliga e Ligue 1 sono leghe modellate in produzione (voci in LEAGUE_CONFIGS, snapshot versionati, δ 0.28 e 0.19).
- **Trovato**: newseason.md:151-154: «**Aggiungere le leghe nuove** (Ligue 1 e Bundesliga come leghe *modellate* ...) — a parita' di stagioni si passerebbe da 27 a oltre 45 stagioni-lega — ma **non ha scadenza** ... **Dopo settembre.**» lavoro_aperto.md:338-340 ripete la stessa raccomandazione.
- **Come è stato accertato**: CLAUDE.md:410-419 (5 leghe, 16.111 partite, δ per-lega 0.23/0.33/0.22/0.28/0.19); `ls data/*_matches.csv` -> bundesliga_matches.csv (2.754) e ligue_1_matches.csv (3.097); src/config.py LEAGUE_CONFIGS; 45 = 5 leghe × 9 stagioni, il numero citato come ipotetico.
- **Correzione**: Sostituire le due voci con «FATTO (Fase 100)» e ricontrollare che non restino altri item del blocco B/§7 gia' chiusi.

**🟠 `F9-estimates-readme-stantio` — data/estimates/README.md descrive la stima O/U su 3 leghe e 7.978 partite, mentre il file e' a 5 leghe e il fit e' su 12.457**  
*numero-errato · media · **confermato***

- **Dove**: data/estimates/README.md:22-23, 29, 38, 43; confronto con docs/DATI.md:230 e data/estimates/ou_close_2017_19.csv
- **Atteso**: Coerenza con DATI.md:230: «`ou_close_2017_19.csv` (**3638 righe, 5 leghe**) ... fit pooled su **12.457** partite 2019-20+ e **5 leghe** ... MAE ~0.014 nel REGIME D'USO, ~0.012 in interpolazione».
- **Trovato**: Riga 29: «In quelle 2 stagioni (Serie A, Premier League, La Liga)»; riga 38: «fittata pooled su 7.978 partite 2019-20+»; riga 43: «MAE vs chiusura vera (prob.) | **~0.012**» senza la distinzione di regime. Inoltre la regola 4 (righe 22-23) dice «Ogni file e' **rigenerabile** con `python scripts/build_estimates.py`», ma quello script produce solo 3 dei 5 file presenti.
- **Come è stato accertato**: pandas: data/estimates/ou_close_2017_19.csv -> 3638 righe, league = {serie_a 760, premier_league 760, ligue_1 758, la_liga 756, bundesliga 604}. `grep -n 'def build_' scripts/build_estimates.py` -> build_ou_close, build_squad_value, build_open_sparse; `ou_open_corrotte_2017_19.csv` e `celle_residue.csv` sono prodotti da scripts/stima_ou_open_bakeoff.py:103 e scripts/stima_celle_residue.py:70 (entrambi scrivono in cantiere/data/stime/, percorso inesistente).
- **Correzione**: Aggiornare 29/38/43 ai numeri a 5 leghe e riscrivere la regola 4 elencando lo script rigeneratore di ciascun file (e sistemare i due script rotti).

**🟠 `F9-dati-censimento-buchi` — Il censimento dei buchi di docs/DATI.md non e' stato rigenerato dopo l'applicazione del guard: 7.353 dichiarate contro 7.359 effettive, e tre voci della tabella sbagliate**  
*numero-errato · media · **confermato***

- **Dove**: docs/DATI.md:55-56 e 61-67 (tabella §1-bis); anche docs/audit_5_leghe/08_buchi.md:6,25 e 00_indice.md:45
- **Atteso**: Somma verificabile sugli snapshot versionati.
- **Trovato**: «7.353 celle vuote su 612.218» -> effettive 7.359 (le 3 linee O/U La Liga svuotate dal guard ORR_MAX all'integrazione valgono esattamente 6 celle: 7.353+6). Nella tabella: «5 celle quota | Torino-Fiorentina, Verona-Genoa» -> effettive 7 (Torino-Fiorentina 3 di 1X2 open + 2 di O/U open; Verona-Genoa 2 di O/U open); «12 celle xG/stile | 2 partite» -> effettive 16 (xg, npxg, ppda, deep × 2 lati × 2 partite); mancano del tutto le 2 celle `home_sot`/`away_sot`.
- **Come è stato accertato**: Somma pandas su data/*_matches.csv: 16.111 partite, 612.218 celle, **7.359** NaN (1.2020%). Decomposizione: 7.304 (buco sistemico O/U chiusura 2017-19) + 55 residue, con dettaglio per colonna: bundesliga odds_over25_open 7 / under 7, la_liga 3/3, ligue_1 2/2, serie_a 2/2 + 3 di 1X2 open; 16 celle xG/stile; 6 celle di terne 1X2 di chiusura; 2 celle sot. 7.304+55 = 7.359.
- **Correzione**: Rigenerare il censimento contro gli snapshot attuali e correggere le tre righe della tabella (7 celle quota, 16 celle xG/stile, +1 riga per i 2 `sot`).

**🟠 `F9-dati-header-e-omissioni` — docs/DATI.md, che si dichiara «mappa unica di tutti i dati», non cataloga tre insiemi di dati versionati entrati con la Fase 100 ed e' rimasto a «tre leghe» in piu' punti**  
*omissione · media · **confermato***

- **Dove**: docs/DATI.md:6, 91, 150-155 (§3), 162-172 (§4), 312-328 (§6)
- **Atteso**: CLAUDE.md §5: «catalogo completo di tutti i dati (reali e stimati) in docs/DATI.md — da aggiornare a ogni modifica dei dati».
- **Trovato**: Header riga 6: «Ultimo aggiornamento: **Fase 73**» (il file contiene gia' §4-bis segnaposto e §5-bis outright). Riga 91: «questa tabella vale per tutte e 3 le leghe» (mentre riga 43 dice «su tutte e 5 le leghe»). §3 elenca 3 calendari di club su 5 (mancano data/club_fixtures_bundesliga.csv, 10.375 righe, e data/club_fixtures_ligue_1.csv, 10.701). §4 non ha righe per le fonti grezze di Bundesliga/Ligue 1. §6 non dice come si rigenerano i 2 snapshot nuovi. Non compaiono da nessuna parte: data/correzioni_dichiarate.csv (31 righe), data/squad_value_2526_transfermarkt.csv (16 celle), data/ricerca_esterna/ (25 JSON footiqo con le quote 1X2/O/U/GG-NG 1xBet + manifest + fixtures di coppa).
- **Come è stato accertato**: `ls data/` e conteggi riga: club_fixtures_bundesliga.csv 10375, club_fixtures_ligue_1.csv 10701, correzioni_dichiarate.csv 31 righe (pandas), squad_value_2526_transfermarkt.csv 16 righe; `ls data/ricerca_esterna/` -> 25 file footiqo_* + manifest_fonti_audit.json + footiqo_manifest.json + validazione_footiqo.json.
- **Correzione**: Aggiungere le righe mancanti a §3/§4/§6, una voce per data/ricerca_esterna/ (dichiarando che le quote 1xBet NON sono negli snapshot e perche'), correggere «3 leghe» -> «5 leghe» a riga 91 e aggiornare l'header.

**🟠 `F9-claude-ggng-n-sbagliato` — CLAUDE.md attribuisce i risultati GG/NG a «3.652 partite del 2017-19» mentre l'artefatto li calcola su 5.337 (2017-20)**  
*numero-errato · media · **confermato***

- **Dove**: CLAUDE.md:48-59; confronto con docs/audit_5_leghe/00_indice.md:48 e docs/audit_5_leghe/numeri/ggng_contro_quote.json
- **Atteso**: «5 leghe × 3 stagioni, 5.337 partite» come dichiara 00_indice.md:48 (3.652 e' la finestra 2017-19 della caccia O/U, 2 stagioni).
- **Trovato**: CLAUDE.md:48-52: «Le quote GG/NG di chiusura sono state trovate — un book (1xBet) ..., **3.652 partite del 2017-19** su tutte e 5 le leghe — ... Risposta: il mercato GG/NG e' informativo (log-loss 0.6840 contro 0.6921 di baseline, CI conclusivo)». Ma 0.6840/0.6921 e il +0.0104 del DC vengono dal pool a 3 stagioni.
- **Come è stato accertato**: docs/audit_5_leghe/numeri/ggng_contro_quote.json: `lucchetti.n_finale` = 5337 (n_per_stagione 1718:1825, 1819:1825, 1920:1687); D1 log_loss_mercato 0.68399, log_loss_baseline_LOSO 0.69213 su n=5337; D2 blocco «tutte e 3 le stagioni» c_DC delta +0.0104 ci [+0.00632, +0.01454] su n=3512. Il blocco 2017-19 ha n=3650 e c_DC +0.0093.
- **Correzione**: CLAUDE.md:50 -> «5.337 partite del 2017-20 (3 stagioni × 5 leghe; la finestra 2017-19 della caccia O/U ne conta 3.652)».

**🟠 `F9-playbook-non-aggiornato` — docs/PLAYBOOK_NUOVA_LEGA.md non ha incorporato nulla dell'onboarding Bundesliga/Ligue 1, che pure lo ha usato**  
*omissione · media · **confermato***

- **Dove**: docs/PLAYBOOK_NUOVA_LEGA.md:4, 20-24, 75-78, 79-82, 88-91, 110-113, 148-158, 162-164
- **Atteso**: CLAUDE.md §7 lo indica come «la procedura completa e collaudata ... per ogni lega futura si parte da li'», e CLAUDE.md §5-bis codifica le regole R1-R7 nate proprio da quell'onboarding.
- **Trovato**: Riga 4 elenca ancora «(Bundesliga, Ligue 1, Eredivisie…)» come leghe da fare. Riga 22: «Se il proxy blocca le fonti: bundle JSON caricati dall'utente in `files/`» (la rete e' tornata e i 2 snapshot nuovi sono stati scaricati direttamente). Riga 25 indica `scripts/build_league_snapshot.py`, che per Bundesliga/Ligue 1 non funziona (serve un bundle in files/). Riga 77 «SA 0.23, PL 0.33, Liga 0.22» senza BL 0.28 / L1 0.19. Riga 80 «curve piatte (successo su 3/3 leghe)» -> ora 5/5. Riga 91 «batte il DC-da-gol su ~13/14 (3/3 leghe finora)» -> 15/15 sulle nuove. Righe 112-113 «Fase 79: 4/4 bocciate; Fase 80: 1 leva su 3 leghe» senza lo 0/25 del router della Fase 100. Nessuna menzione di R1-R7 ne' della verifica riga-per-riga contro la fonte. Il «quaderno di studio» imposto dal Passo 1 (riga 54-55) non esiste per le 2 leghe nuove.
- **Come è stato accertato**: `grep -in 'R1|riga per riga|riga-per-riga|Fase 100|footiqo' docs/PLAYBOOK_NUOVA_LEGA.md` -> 0. `ls files/` -> bundle solo premier_league e la_liga. `ls docs/` -> nessun STUDIO_* per Bundesliga/Ligue 1. CLAUDE.md:412-418 (δ 0.28/0.19) e CLAUDE.md §5-bis (R1-R7).
- **Correzione**: Aggiornare i contatori a 5 leghe, aggiungere δ BL/L1, sostituire il Passo 0 con la procedura «scarica dalla fonte + verifica riga-per-riga + R1-R7», e decidere/annotare dove vive il quaderno di studio delle 2 leghe nuove (oggi: docs/audit_5_leghe/03 e 06).

**🟠 `F9-studio-pl-liga-stantio` — docs/STUDIO_PREMIER_LIGA.md e' fermo alla Fase 79 nell'header e a «3 leghe» nei riferimenti trasversali**  
*incoerenza-doc · media · **confermato***

- **Dove**: docs/STUDIO_PREMIER_LIGA.md:12, 32, 169, 178, 308
- **Atteso**: Il file dichiara di andare aggiornato «a ogni fase che tocca Premier/Liga»; la Fase 100 le ha ri-misurate entrambe (bakeoff a 5 leghe, stima O/U pooled a 5, GG/NG contro quote vere).
- **Trovato**: Riga 12: «Ultimo aggiornamento: **Fase 79**», mentre il file contiene §6-bis (F80), §6-ter (F81), §6-quater (F82). Riga 169: «E3 pooled per la chiusura O/U 2017-19 (vale per le **3 leghe**, F62-bis)» — lo stimatore e' ora pooled a 5 e la versione a 5 batte quella a 3 con CI conclusivo. Riga 308: «**Chiusura O/U 2017-19** (PISTE #19): stesso buco su tutte e **tre** le leghe» — e' su 5, e il dato vero e' stato trovato. Riga 32: «GG/NG quotato | 0% | 0%» e riga 178 «il GG/NG e' il mercato senza tetto dimostrato».
- **Come è stato accertato**: docs/DATI.md:230 (pooled a 5, 12.457 partite, «il pooled a 5 batte quello a 3 con CI conclusivo»); data/estimates/ou_close_2017_19.csv con 760 righe Premier e 756 La Liga; docs/CACCIA_OU_2017_19.md:1-30.
- **Correzione**: Aggiungere una sezione «Fase 100: cosa cambia per PL/Liga» e correggere 12/169/178/308.

**🟡 `F9-glossario-lacune` — Il glossario non definisce i termini introdotti dalle ultime fasi e cita ancora costanti a 3 leghe**  
*omissione · bassa · **confermato***

- **Dove**: docs/GLOSSARIO.md:18, 27; e assenze in tutto il file
- **Atteso**: Il file dichiara di dare «1-2 righe e la fase che lo introduce» a ogni termine ricorrente.
- **Trovato**: Mancano: **deriva di forza** (F94, titolare sul mercato retrocessione), **game-state** (F98, l'unico residuo vivo del progetto), **mercato campione di stagione / season_sim / outright** (F89/F95/F97, una famiglia di mercati intera), **E3** (nome dello stimatore O/U usato in DATI.md:230, PISTE.md:449, STUDIO:169 senza mai essere definito), **segnaposto / finto pieno** e **ORR_MAX** (R6 e il guard entrati con la Fase 100). Riga 18: «`ρ=−0.06` e' risultato universale sulle **3 leghe**». Riga 27: «δ ... per-lega (0.23 SA / 0.33 PL / 0.22 Liga)» senza Bundesliga 0.28 e Ligue 1 0.19.
- **Come è stato accertato**: `grep -ci` su docs/GLOSSARIO.md: 'deriva di forza' 0, 'game-state' 0, 'season_sim' 0, 'outright' 0, 'E3' 0, 'segnaposto' 0, 'ORR_MAX' 0. CLAUDE.md:412-414 (δ a 5 leghe), src/data/loader.py:99 (ORR_MAX), docs/DATI.md §4-bis (segnaposto).
- **Correzione**: Aggiungere le sei voci mancanti e aggiornare 18/27 ai numeri a 5 leghe.

**🟡 `F9-regole-numerazione-divergente` — docs/audit_5_leghe/REGOLE.md e CLAUDE.md §5-bis usano la stessa sigla per regole diverse (R4, R5, R6) e REGOLE.md non ha R7**  
*incoerenza-doc · bassa · **confermato***

- **Dove**: docs/audit_5_leghe/REGOLE.md:113 (R4), 124 (R6), 198 (R5); CLAUDE.md §5-bis; docs/audit_5_leghe/00_indice.md:16, 71
- **Atteso**: Una numerazione sola, visto che 00_indice.md:16 dichiara le regole «promosse a §5-bis del CLAUDE.md» e che vari script e report citano «R1/R3», «R4», «R6» come riferimenti.
- **Trovato**: In REGOLE.md: R4 = «Isolamento del cantiere», R5 = «Le anomalie si dichiarano», R6 = «Partite con dati corrotti: la procedura». In CLAUDE.md §5-bis: R4 = «Un'anomalia si dichiara anche quando NON e' un errore», R5 = «Procedura per una riga che sembra corrotta», R6 = «Il buco peggiore non e' il NaN: e' il finto pieno», R7 = «Ogni statistica di testa deve avere il suo intervallo». REGOLE.md non contiene ne' R6-finto-pieno ne' R7. 00_indice.md:71 le descrive «(R1-R6)».
- **Come è stato accertato**: `grep -n '^## R' docs/audit_5_leghe/REGOLE.md` -> R1(11), R2(45), R3(100), R4(113), R6(124), R5(198); `grep -n 'finto pieno|R7' docs/audit_5_leghe/REGOLE.md` -> 0.
- **Correzione**: Mettere in testa a REGOLE.md una nota di rinumerazione («versione storica; la numerazione vigente e' CLAUDE.md §5-bis, dove R4/R5/R6 significano altro») oppure allineare i titoli.

**🟡 `F9-dati-caccia-aperta` — docs/DATI.md dice che «la caccia al dato vero di chiusura resta aperta» e linka un documento che si apre con «CHIUSA: il dato e' stato trovato»**  
*incoerenza-doc · bassa · **confermato***

- **Dove**: docs/DATI.md:249-251 vs docs/CACCIA_OU_2017_19.md:1-45
- **Atteso**: Coerenza: il dato vero (1xBet, 3.652/3.652 partite) e' stato trovato e deliberatamente NON inserito perche' e' single-book contro una colonna multi-book; resta aperta solo la chiusura come **media multi-book**.
- **Trovato**: DATI.md:250-251: «Resta un buco solo la **chiusura** O/U di quelle stagioni ...; la caccia al dato vero di chiusura **resta aperta** → [CACCIA_OU_2017_19.md]».
- **Come è stato accertato**: docs/CACCIA_OU_2017_19.md:1 «# Caccia alle quote O/U 2017-19 — CHIUSA: il dato e' stato trovato» e :39-42 «Cosa resta aperto: la chiusura O/U 2017-19 come *media multi-book* non esiste da nessuna parte».
- **Correzione**: Riformulare: «la caccia e' chiusa (Fase 100): il dato 1xBet esiste ma non e' la media multi-book e non e' stato inserito — vedi CACCIA_OU_2017_19.md».

**🟡 `F9-experiments-readme-snippet` — L'esempio di rilettura di experiments/README.md solleva KeyError sul registro reale**  
*bug-codice · bassa · **confermato***

- **Dove**: experiments/README.md:27-33
- **Atteso**: Lo snippet deve girare: il file dichiara «chiunque deve poter ricostruire come e' stato ottenuto un numero».
- **Trovato**: `r = [x for x in runs if x['config']['test_season'] == '2526']` fallisce: molti record (gli `_run_*` di fase) non hanno `config.test_season`.
- **Come è stato accertato**: Eseguito lo snippet su experiments/runs.jsonl (725 record) -> `FAIL: KeyError 'test_season'`. Esempio di record senza il campo: l'ultimo, con config keys ['bakeoff_metodi','model','n_folds','source'].
- **Correzione**: `x.get('config',{}).get('test_season')` (e analogamente per `metrics`).

**🟡 `F9-prospettico-3-vs-5-leghe` — Il test prospettico e' impostato su 3 leghe nel file dell'esperimento e su 5 nel piano operativo, con date di via diverse**  
*incoerenza-doc · bassa · **confermato***

- **Dove**: experiments/prospettico_2026_27.md:1, 66, 139 vs newseason.md:24-30, 92
- **Atteso**: Un solo perimetro e un solo calendario, ora che le leghe modellate sono 5.
- **Trovato**: prospettico_2026_27.md:1 «(Serie A, Premier, La Liga)» e §3 «Per ciascuna delle 3 leghe»; newseason.md:92 «calendario delle prime 3-5 giornate delle **5 leghe**». Date: prospettico :139 «Premier ~21/8, Liga ~15/8, SA ~23/8»; newseason §1 «La Liga 16 agosto, Premier 21 agosto, Serie A 22 agosto».
- **Come è stato accertato**: Lettura dei due file; newseason.md:20-22 dichiara che le date vengono da `start_date` di Smarkets scaricate il 25/07/2026.
- **Correzione**: Estendere il protocollo a 5 leghe (o dichiarare perche' resta a 3) e allineare le date su un'unica fonte.

**🟡 `F9-root-hardcoded` — scripts/stima_ou_open_bakeoff.py ha la radice del repo scritta a mano come percorso assoluto**  
*bug-codice · bassa · **confermato***

- **Dove**: scripts/stima_ou_open_bakeoff.py:69
- **Atteso**: `ROOT = Path(__file__).resolve().parents[1]`, come negli altri script di produzione.
- **Trovato**: `ROOT = Path("/home/user/Polymarket-oracle")` — lo script che ha prodotto data/estimates/ou_open_corrotte_2017_19.csv non gira su nessun altro clone, e scrive comunque in `ROOT/cantiere/data/stime/` (riga 103), cartella inesistente.
- **Come è stato accertato**: Lettura del file; confronto con gli altri scripts/*.py che usano `Path(__file__).resolve().parents[N]`.
- **Correzione**: Sostituire con parents[1] e puntare OUT_CSV a data/estimates/ e OUT_JSON a docs/audit_5_leghe/numeri/.

**🟡 `F9-outright-fase96` — Il congelamento delle previsioni outright e' attribuito alla Fase 96 in due documenti e alla Fase 95 nel file stesso**  
*incoerenza-doc · bassa · **confermato***

- **Dove**: lavoro_aperto.md:45; newseason.md:81-82; experiments/prospettico_2026_27_outright.json (campo `nota`)
- **Atteso**: Una sola attribuzione.
- **Trovato**: lavoro_aperto.md:45 «`experiments/prospettico_2026_27_outright.json` | **congelato** (Fase 96)»; newseason.md:82 «l'outright e' gia' congelato (Fase 96 dell'altra sessione)». Il JSON dice: «Previsioni congelate PRIMA dell'inizio della stagione 2026-27 (test prospettico, **Fase 78/95**)», congelato_il 2026-07-25.
- **Come è stato accertato**: `python -c "import json; print(json.load(open('experiments/prospettico_2026_27_outright.json'))['nota'])"`; docs/DIARIO.md:10121 «## Fase 95 — Il primo confronto con un mercato VERO sull'outright».
- **Correzione**: Uniformare a «Fase 95» (o «95/96» se il congelamento e' stato ripreso), in entrambi i documenti.

**🟠 `F9-indice-contraddittorio` — docs/audit_5_leghe/00_indice.md si contraddice e conserva l'intera sezione pre-integrazione (cantiere/, 153 test, «nessun file del progetto e' stato modificato»)**  
*incoerenza-doc · media · ridimensionato*

- **Dove**: docs/audit_5_leghe/00_indice.md:23 vs 116-118; 67-101; 103-114; 122-123; 127
- **Atteso**: L'indice deve descrivere lo stato POST-integrazione, coerente con la propria tabella di mappatura (righe 13-23).
- **Trovato**: Riga 23 dichiara `cantiere/data/fonti/` **rimossi**; riga 116-118 dice «Gli snapshot delle leghe nuove si rigenerano **offline** dalle fonti versionate in `data/fonti/`». Le sezioni «Contenuto» (67-101) e «Come rifare tutto da zero» (103-114) descrivono ancora l'albero cantiere/ e propongono 8 comandi `python cantiere/scripts/...` inesistenti. Riga 122-123: «nessun file esistente del progetto e' stato modificato (ne' src/, ne' data/, ne' docs/, ne' scripts/, ne' tests/): tutto vive qui» — falso dopo i 5 commit di integrazione. Riga 127: «pytest resta verde (153 test)».
- **Come è stato accertato**: Lettura diretta del file; `ls -d data/fonti` -> assente; `ls data/` mostra bundesliga_matches.csv e ligue_1_matches.csv in produzione; `python -m pytest -q` -> **194 passed** (non 153).
- **Correzione**: Riscrivere le sezioni 67-127 al passato («com'era il cantiere») o sostituirle con la mappa attuale; correggere 116-118 (le fonti NON sono in repo), 122-123 (dire cosa e' stato integrato) e 127 (194 test).
- **Verifica avversariale**: Tutti i fatti citati sono veri e riprodotti: la riga 116-118 rimanda a `data/fonti/` che la tabella dello stesso file (riga 23) dichiara rimossa; le sezioni 'Contenuto' e 'Come rifare tutto da zero' descrivono l'albero cantiere/ e propongono 8 comandi `python cantiere/scripts/...` inesistenti; la riga 122 dice che nessun file del progetto è stato modificato (falso dopo i 5 commit); la riga 127 dice 153 test contro 194 attuali. Ridimensiono la severità da alta a media per due ragioni: (a) il rilievo è documentazione stantia, non un numero/conclusione scientifica errata né codice di produzione rotto — l'unico pezzo 'rotto' (gli script) è già il rilievo F9-script-cantiere-rotti e sarebbe doppio conteggio; (b) le righe 11-23 del file contengono una tabella di mappatura esplicita 'dove era -> dove è ora' che mitiga in parte le sezioni successive. Nota: '153 test' è plausibilmente vero al momento del cantiere (a 12da9e0 conto 168 funzioni test_* contro 172 di oggi), quindi va letto come frase storica non aggiornata, non come numero inventato.

**🟠 `F9-conteggi-indice-sbagliati` — I conteggi-titolo dell'indice del lavoro aperto (17 piste / 21 voci / 19 piste / 24 caselle) non corrispondono ai file che indicizzano**  
*numero-errato · media · ridimensionato*

- **Dove**: lavoro_aperto.md:54 e 103; CLAUDE.md:296-297; newseason.md:291-295
- **Atteso**: docs/PISTE.md ha 23 piste numerate; la matrice di docs/PANCHINA.md ha 138 celle ⬜ (46 righe × 6 fronti dopo l'ingresso di Bundesliga e Ligue 1).
- **Trovato**: lavoro_aperto.md:54 «21 voci, **17 ancora aperte**. Conteggio verificato il 26/07/2026» — la tabella immediatamente sotto ha 23 righe, di cui 16 🟢 e 2 🟡. lavoro_aperto.md:103 e newseason.md:295 e CLAUDE.md:297: «24 caselle ⬜». newseason.md:291-294: «19 piste numerate — 4 senza dati nuovi, 5 nei grezzi, 6 con fonte esterna, 4 di raccolta prospettica» (i gruppi reali di PISTE.md sono 7/6/6/4).
- **Come è stato accertato**: `grep -n '^### [0-9]' docs/PISTE.md` -> 23 intestazioni (1,2,3,4,4-bis,4-ter,4-quater,5,6,7,7-bis,8,9,10,...,19). Parser sulla tabella §2 di lavoro_aperto.md -> 23 righe. Conteggio ⬜ nella matrice di PANCHINA.md (46 righe dopo l'header «| modello | Serie A») -> 138; 140 in tutto il file.
- **Correzione**: Ricalcolare i tre conteggi e, meglio, sostituirli con un rimando («vedi PISTE.md/PANCHINA.md») o generarli con uno script, visto che divergono ogni volta che si aggiunge una lega o una pista.
- **Verifica avversariale**: Tre conteggi su quattro sono sbagliati, ma il quarto — quello di newseason.md — è CORRETTO e l'auditor l'ha frainteso. newseason.md:291-294 dice «19 piste numerate — 4 senza dati nuovi, 5 nei grezzi, 6 con fonte esterna, 4 di raccolta prospettica»: contando le sole piste a numero INTERO (1-19), come la frase dichiara esplicitamente, i gruppi di PISTE.md sono 1-4 = 4, 5-9 = 5, 10-15 = 6, 16-19 = 4, totale 19. Torna a ogni cifra. I 7/6/6/4 dell'auditor si ottengono solo includendo 4-bis/4-ter/4-quater/7-bis, che quella frase esclude per costruzione. Restano confermati: lavoro_aperto.md:54 «21 voci» contro 23 righe nella tabella immediatamente sotto (e 23 intestazioni ### in PISTE.md) — per giunta con «Conteggio verificato il 26/07/2026»; e «24 caselle ⬜» in tre punti (lavoro_aperto.md:103 e :106, newseason.md:295, CLAUDE.md:297) contro 138 celle ⬜ effettive nella matrice. Il «17 ancora aperte» non lo dichiaro errato: dipende da come si contano le 🟡 e il residuo aperto della pista 6 (16 🟢 + 2 🟡), quindi è ambiguo, non falso.

**🟡 `F9-lavoro-aperto-pista5` — Dentro lo stesso lavoro_aperto.md la pista 5 (handicap asiatico) e' «mai estratta» in §2 e «coperta» in §5 e §8**  
*incoerenza-doc · bassa · ridimensionato*

- **Dove**: lavoro_aperto.md:72 vs 165-171 (§5) vs 329-330 (§8, punto 4)
- **Atteso**: Uno stato solo, allineato a docs/PISTE.md:199-221 (chiusa negativa come input di inversione, Fase 86; aperta e validata come benchmark Tier 2, Fase 88).
- **Trovato**: Riga 72: «| 5 | **Handicap asiatico** → terzo vincolo per l'inversione market-implied | 🟢 mai estratta. E' anche il **Tier 2** (§5) |». §5: «Tier 2 | handicap asiatico | ✅ **coperto** (F88 benchmark + F98 listino ...)». §8 punto 4: «*(La 5 e la 6 sono state aperte da F88/F98: Tier 2 e Tier 3 non sono piu' scoperti.)*».
- **Come è stato accertato**: Lettura delle tre sezioni; docs/PISTE.md:210-221 conferma lo stato reale.
- **Correzione**: Portare la riga 72 a «🟡 chiusa come input (F86), aperta e validata come benchmark Tier 2 (F88/F98); resta l'estrazione nel loader».
- **Verifica avversariale**: La contraddizione descritta non c'è: le tre affermazioni parlano di oggetti DIVERSI e sono tutte vere. §2 riga 74 dice «mai estratta» e sta nella sezione «Nei grezzi già scaricati e mai estratti»: ho verificato ed è letteralmente esatto — nello snapshot non esiste alcuna colonna AH (38 colonne, nessuna handicap) e `grep -in 'AHh|AHCh|handicap|asian' src/data/loader.py` non trova nulla; anche docs/PISTE.md:221-222 conferma «Resta da fare (facoltativo): estrarre l'AH nel loader». §5 dice che il MERCATO Tier 2 è coperto (F88/F98), che è un'altra affermazione. E §8 punto 4 (righe 331-333) segnala esplicitamente «La 5 e la 6 sono state aperte da F88/F98», cioè il file la contraddizione non ce l'ha nemmeno implicitamente. Resta un difetto minore e reale: la riga 74 porta il marcatore 🟢 (= aperta) e non registra che l'IPOTESI originale della pista — l'AH come terzo vincolo d'inversione — è chiusa NEGATIVA dalla Fase 86 (corr 0.9952 con λ−μ). È un'omissione, non un'incoerenza; e lavoro_aperto.md si dichiara non-fonte-di-verità rispetto a PISTE.md.

**🟡 `F9-sot-100-percento` — docs/DATI.md dichiara i tiri in porta al 100% ma 2 celle sono NaN, e la correzione che le riempirebbe e' registrata come «proposta» mai decisa**  
*incompiuto · bassa · ridimensionato*

- **Dove**: docs/DATI.md:42; data/correzioni_dichiarate.csv righe 3-4 (stato «proposta»)
- **Atteso**: O copertura 100% reale, o buco dichiarato in §1/§1-bis (regola R4/R5: «un'anomalia si dichiara anche quando NON e' un errore»).
- **Trovato**: DATI.md:42: «| tiri in porta | `home_sot, away_sot` | football-data | 100% |». Nello snapshot Bundesliga, Union Berlin-Bochum 14/12/2024 (la partita della regola R1) ha home_sot e away_sot NaN. Il registro delle correzioni propone home_sot=4 / away_sot=3 da understat.com/getMatchData/27866 ma lo stato e' «proposta»: nessuna decisione registrata, nessuna traccia in DATI.md.
- **Come è stato accertato**: pandas su data/bundesliga_matches.csv: `df[df.home_sot.isna()|df.away_sot.isna()]` -> 1 riga (2425, 2024-12-14, Union Berlin-Bochum, home_sot NaN, away_sot NaN, gol 1-1 gia' corretti a norma R1). data/correzioni_dichiarate.csv righe 3-4: colonna=home_sot/away_sot, valore_prima=NaN, valore_dopo=4/3, stato=proposta.
- **Correzione**: Chiudere la proposta (applicarla con lo script idempotente o marcarla «respinta» col motivo) e, in ogni caso, portare la copertura `sot` in DATI.md §1 a «100% meno 1 partita dichiarata».
- **Verifica avversariale**: Metà del rilievo è smontata. È VERO che docs/DATI.md:42 dichiara i tiri in porta al 100% mentre 2 celle sono NaN (Union Berlin-Bochum 14/12/2024 in Bundesliga) — errore fattuale reale, per giunta in contrasto con la riga 45 dello stesso file, che per l'xG usa la formula corretta «100% meno 2 partite dichiarate». È FALSO invece che la correzione sia «registrata come proposta mai decisa» e senza motivo: data/correzioni_dichiarate.csv righe 3-4 contengono la decisione per esteso nel campo `motivo` — «NON applicata: la definizione Understat non e' identica a quella football-data della colonna, e mescolare due definizioni in una cella e' peggio di un NaN dichiarato. Registrata perche' il dato esiste, se un giorno si decidesse di usarlo». È esattamente il comportamento che le regole R4/R5 del CLAUDE.md impongono; l'unico appunto legittimo è che il campo `stato` dice 'proposta' invece di 'respinta'. Scendo a bassa anche perché le 2 celle sono già coperte dal rilievo F9-dati-censimento-buchi.

<details><summary>Verifiche con esito OK su questo fronte</summary>

- CLAUDE.md §1.8 GG/NG — i numeri reggono tutti tranne l'n: log-loss book 0.6840 vs baseline LOSO 0.6921 con CI [-0.01164,-0.00464]; «vale un terzo dell'O/U 2.5» = 0.008141/0.025169 = 0.32; «1,7 punti di margine in piu'» = overround 1.04612 - 1.02948 = 1.66pp; «DC +0.0104, CI [+0.0063,+0.0145]»; «α*=0 nel 70% dei fit» = quota_alpha_zero 0.7 nel blocco con_c_DC. Tutti ricalcolati da docs/audit_5_leghe/numeri/ggng_contro_quote.json.
- Falso allarme scartato: STUDIO_PREMIER_LIGA.md:307 «Brier 0.2040 vs 0.2041» e CLAUDE.md:478 «Brier 0.2044 vs 0.2044» NON si contraddicono — sono due run diverse (Fase 88, 7.437 partite × 3 leghe, docs/DIARIO.md:9091; e la validazione del listino della Fase 98, docs/DIARIO.md:10733).
- Falso allarme scartato: l'endpoint Understat differisce fra docs/MANUALE_SOPRAVVIVENZA.md:11 (`/main/getLeagueData/`) e docs/audit_5_leghe/00_indice.md:62 (`/getLeagueData/`), ma entrambe le forme rispondono 200 (curl con header X-Requested-With). Non e' un difetto.
- docs/DATI.md §1: le 5 righe della tabella snapshot (3420/3420/3420/2754/3097 partite, 9 stagioni, 38 colonne) corrispondono esattamente ai file versionati; totale 16.111 partite e 612.218 celle (16.111×38) come dichiarato.
- docs/DATI.md §1-bis, riga «11 linee O/U di apertura (3 La Liga, 6 Bundesliga, 2 Ligue 1)» + «1 linea assente alla fonte»: verificata sui dati (NaN di odds_over25_open nel 2017-19 = la_liga 3, bundesliga 7, ligue_1 2 = 12 = 11+1). Coerente anche con patch_guard_overround (11 celle attese).
- CLAUDE.md §4: `experiments/fase93_discrimination.csv` ha davvero 5.083 righe (premier 1743, la_liga 1674, serie_a 1666), come dichiarato.
- Propagazione OK dell'auto-correzione della Fase 92 (gap 88% discriminazione / 12% pareggio): presente e corretta in docs/PISTE.md §0 (righe 13-40), docs/GLOSSARIO.md:90-93, docs/PANCHINA.md (nota in testa), lavoro_aperto.md §4. Nessuna occorrenza residua della lettura invertita nei documenti del fronte.
- Propagazione OK dell'auto-correzione della Fase 98 sui numeri-titolo della Fase 89 (baseline 1.4293 -> 1.3816, IC che include lo zero, «fragile alla specificazione della baseline, non perdente»): docs/PISTE.md §4-bis righe 481-495. E propagazione OK della chiusura negativa della Fase 99 sulla correzione di livello: docs/PISTE.md:265-301 e lavoro_aperto.md:79.
- Link relativi markdown: tutti risolti correttamente in CLAUDE.md, PISTE.md, DATI.md, MANUALE_SOPRAVVIVENZA.md, STUDIO_PREMIER_LIGA.md, PLAYBOOK_NUOVA_LEGA.md, CACCIA_OU_2017_19.md, GLOSSARIO.md, lavoro_aperto.md, newseason.md, data/estimates/README.md, experiments/README.md. Le uniche 13 rotture sono in docs/audit_5_leghe/ (vedi finding dedicato).
- `python -m pytest -q` -> 194 passed in 52s: la suite e' verde dopo l'integrazione (nonostante i 27 script rotti, che non sono coperti da test).

</details>

### Codice entrato con l'integrazione  ·  12 rilievi
**🔴 `F10-scripts-root-parents2` — I 27 script migrati da cantiere/ hanno ROOT sbagliato: 24 crashano all'import, tutti puntano fuori dal repo**  
*import-rotto · alta · **confermato***

- **Dove**: scripts/build_new_snapshot.py:35, scripts/nuove_leghe.py:28, scripts/audit_snapshots.py:31, scripts/applica_correzioni.py:27-28, scripts/fetch_sources.py:41-42, + altri 22 (tutti quelli che contengono `parents[2]`)
- **Atteso**: Dopo lo spostamento cantiere/scripts/ -> scripts/ (commit 6c9b377), ROOT deve essere `Path(__file__).resolve().parents[1]` (= radice repo) e i percorsi `ROOT/"cantiere"/...` devono diventare `ROOT/"data"`, `ROOT/"docs/audit_5_leghe"`, ecc. Gli script devono partire.
- **Trovato**: Tutti e 27 conservano `ROOT = Path(__file__).resolve().parents[2]`, che ora vale `/home/user` (un livello SOPRA il repo). 24 di essi importano `src` da ROOT e muoiono con `ModuleNotFoundError: No module named 'src'`; i 3 restanti (applica_correzioni, applica_squad_value_tm, fetch_sources) partono ma leggono/scrivono in `/home/user/cantiere/...`, cioe' fuori dal repo. Fra i rotti ci sono gli strumenti che COSTRUISCONO le due leghe nuove (build_new_snapshot.py, nuove_leghe.py) e quelli che le AUDITANO (audit_snapshots.py, audit_anomalie.py, verifica_stime.py, cerca_segnaposto.py); fra quelli che sbagliano percorso c'e' applica_correzioni.py, cioe' lo script idempotente preteso dalla regola R3 del CLAUDE.md §5-bis.
- **Come è stato accertato**: `for f in ...; do python3 scripts/$f.py --help; done` -> 24 volte "ROTTO" con ModuleNotFoundError 'src' (audit_anomalie, audit_snapshots, build_new_snapshot, cerca_segnaposto, eda_nuove_leghe, leve_beat_close, leve_dc_panchina, leve_devig_shin, leve_ricalibrazioni, leve_theta_griglia, nuove_leghe, nuovo_calibrazione, nuovo_mercato_campione, recupero_squad_value_tm, riconcilia_nomi, stima_celle_residue, stima_ou_close_nuove, stima_ou_corrotte, stima_sot_understat, tranche3_market_tracer, tranche3_mercati, tranche3_ritaratura, tranche3_tracer, verifica_stime). `python3 scripts/applica_correzioni.py --dry-run` -> `FileNotFoundError: '/home/user/cantiere/data/correzioni_dichiarate.csv'` (il file vero e' `data/correzioni_dichiarate.csv`, 32 righe). `grep -rln 'parents\[2\]' scripts/` -> 27 file.
- **Correzione**: Sostituire `parents[2]` con `parents[1]` nei 27 file e ri-puntare i percorsi `ROOT/"cantiere"/"data"` -> `ROOT/"data"`, `ROOT/"cantiere"/"scripts"` -> `ROOT/"scripts"`, `ROOT/"cantiere"/"report"` -> `ROOT/"docs/audit_5_leghe"`. Aggiungere un test di fumo che importa (o esegue `--help` su) ogni script di scripts/, altrimenti la prossima migrazione ripete l'errore.

**🟠 `F10-base-url-mirror-morto` — BASE_URL e UNDERSTAT_URL puntano al mirror MORTO (404) mentre le fonti ufficiali rispondono 200**  
*bug-codice · media · **confermato***

- **Dove**: src/data/sources.py:19-38 (BASE_URL), src/data/sources.py:388-398 (UNDERSTAT_URL)
- **Atteso**: Il commit 03d5bec dichiara che Bundesliga e Ligue 1 sono state "scaricate direttamente da football-data (D1/F1) e Understat" perche' "il provider originale e' tornato raggiungibile (200)". Se e' cosi', `BASE_URL` doveva passare a `OFFICIAL_BASE_URL` e `UNDERSTAT_URL` a `UNDERSTAT_OFFICIAL_URL` (o a un fetcher equivalente), e i commenti che dichiarano le fonti irraggiungibili andavano corretti.
- **Trovato**: `BASE_URL = MIRROR_BASE_URL` e `UNDERSTAT_URL = UNDERSTAT_MIRROR_URL` puntano ancora al repo Mentaturan/ScoutFootball_for_World_Cup, che risponde 404. I commenti sopra affermano ancora che football-data.co.uk e understat.com "non sono raggiungibili dall'ambiente cloud (403)". Conseguenza: `loader.download_season`, `understat.download_season`, quindi `build_database.py --refresh`, `enrich(force_download=True)` e `add_open_odds` con cache vuota falliscono con HTTP 404 per TUTTE e 5 le leghe.
- **Come è stato accertato**: `curl -o /dev/null -w '%{http_code}'` -> https://www.football-data.co.uk/mmz4281/2425/D1.csv = 200; https://understat.com/league/Bundesliga/2024 = 200; https://raw.githubusercontent.com/Mentaturan/.../2425/D1.csv = 404. `python3 -c "from src.data import sources; print(sources.csv_url('2425', sources.LEAGUES['bundesliga']))"` -> URL del mirror. Ho scaricato le 18 stagioni D1/F1 dalla URL ufficiale senza alcun problema di rete.
- **Correzione**: Portare `BASE_URL = OFFICIAL_BASE_URL` (e l'equivalente per Understat, o esplicitare che l'xG passa da scripts/fetch_sources.py) e riscrivere i due blocchi di commento con la data e l'esito della verifica di raggiungibilita'. Se si vuole restare offline-first per scelta, dirlo esplicitamente invece di lasciare un URL morto come default.

**🟠 `F10-guard-retry-livello-sbagliato` — Il ripiego del guard sull'overround salta il livello sbagliato: quando la prima colonna di preferenza non esiste, il "ritentativo" ri-sceglie la stessa quota**  
*bug-codice · media · **confermato***

- **Dove**: src/data/loader.py:219 (`retry = {t: _pick_odds(row, preference[t][1:]) ...}`), docstring src/data/loader.py:200-206
- **Atteso**: La docstring promette: overround impossibile -> "si scarta IN BLOCCO e si ritenta col livello di preferenza SUCCESSIVO per OGNI colonna del mercato". Il livello successivo va calcolato rispetto alla colonna EFFETTIVAMENTE usata da `_pick_odds`, non rispetto al primo nome della lista.
- **Trovato**: Il ripiego taglia sempre e solo il primo NOME della lista di preferenza. Se la prima colonna e' assente dalla riga (caso di tutta l'era 2017-19: `AvgC*` e `Avg*` non esistono), `_pick_odds` aveva gia' scelto la seconda; `preference[t][1:]` la ri-sceglie identica, l'overround del ripiego e' lo stesso, e il mercato finisce SEMPRE a NaN — buttando via quote valide di livello inferiore (PSC*, B365) che il guard avrebbe dovuto recuperare.
- **Come è stato accertato**: Riproduzione con codice di produzione: `r = pd.Series({'B365CH':1.20,'B365CD':4.00,'B365CA':6.00,'PSCH':1.55,'PSCD':4.20,'PSCA':6.50})` (nessuna colonna AvgC*, come nel 2017-19); orr B365 = 1.2500 (fuori banda), orr PSC = 1.0371 (sana). `loader._pick_market_odds(r, ['odds_home','odds_draw','odds_away'], loader._ODDS_PREFERENCE)` -> `{nan, nan, nan}` invece di `{1.55, 4.20, 6.50}`. Impatto sui dati ATTUALI: nullo — ho scandito tutti i grezzi disponibili (Serie A da data/football_data_raw, Premier e Liga dai bundle) e le uniche accensioni a livello>0 sono le 3 righe La Liga 1819, dove nessun ripiego sano esiste (le colonne B365>2.5/<2.5 non ci sono in quella stagione).
- **Correzione**: Far tornare a `_pick_odds` anche l'indice della colonna usata (o iterare i livelli finche' l'overround rientra in [1, ORR_MAX]) e costruire il ripiego da `preference[t][idx_usato+1:]`. Aggiungere il test del ramo di ripiego: quello attuale (tests/test_league_snapshots.py, `test_overround_impossibilmente_alto_scartato`) usa colonne `Avg>2.5`/`Avg<2.5`, cioe' il solo caso indice 0.

**🟠 `F10-m2-gia-fatto-ma-dichiarato-aperto` — CLAUDE.md elenca fra i prossimi passi un lavoro (M2, θ del router per-lega) chiuso dalla Fase 92-bis**  
*incoerenza-doc · media · **confermato***

- **Dove**: CLAUDE.md:507-508; src/config.py:105-149 (MARKET_ENGINE + market_engine()); scripts/predict.py:29,124-158; commit 1ad6c30
- **Atteso**: Un lavoro chiuso non deve restare nella lista dei prossimi passi: chi legge CLAUDE.md §6 crede che predict.py applichi ancora θ=1.225 a tutte le leghe.
- **Trovato**: CLAUDE.md §6 dice ancora: "reso per-lega alla Fase 83-bis (M1); resta da rendere per-lega il θ del router nel path market-implied (M2 Premier con θ neutro)". Ma la Fase 92-bis (commit 1ad6c30) ha introdotto `MARKET_ENGINE` in src/config.py e predict.py legge `eng = market_engine(args.league)` usando `eng['dp_theta']`, `eng['dp_theta_dc']`, `eng['phi0']`, `eng['kappa']`, `eng['sharpen_1x2']`: Premier e Liga girano gia' con motore LISCIO (θ neutro) e le leghe ignote pure. Anche la riga 237 del README riporta la stessa cosa come residuo.
- **Come è stato accertato**: `git show --stat 1ad6c30` e messaggio di commit ("Aggiunto MARKET_ENGINE in src/config.py ... Premier e Liga motore LISCIO"); `sed -n 90,160p scripts/predict.py`; `grep -n 'resta da rendere' CLAUDE.md` -> riga 507.
- **Correzione**: Riscrivere il punto "uso pratico" di CLAUDE.md §6 (e la riga 83-bis del README) dicendo che M2 e' chiuso alla Fase 92-bis, con il rimando a `src.config.MARKET_ENGINE`; se resta un residuo vero (es. il θ per Bundesliga/Ligue 1, vedi F10-market-engine-incompleta) dichiararlo come tale.

**🟡 `F10-market-engine-incompleta` — MARKET_ENGINE e' l'unica mappa per-lega senza le due leghe nuove**  
*omissione · bassa · **confermato***

- **Dove**: src/config.py:124-149
- **Atteso**: Il file si dichiara "l'unico punto di verita'" per lega e il suo commento enumera lo stato del motore lega per lega; con 5 leghe in `sources.LEAGUES` e 5 voci in `LEAGUE_CONFIGS`, `MARKET_ENGINE` dovrebbe avere 5 voci esplicite (anche solo per dire "motore LISCIO, misurato: router θ negativo su 0/25 mercati").
- **Trovato**: `MARKET_ENGINE` ha solo serie_a, premier_league, la_liga. Bundesliga e Ligue 1 cadono nel fallback di `market_engine()` (motore liscio) — comportamento CORRETTO secondo la misura riportata in CLAUDE.md §6, ma non dichiarato nel punto di verita' e non distinguibile da "lega mai considerata".
- **Come è stato accertato**: Controllo di completezza su 10 mappe per-lega: UNDERSTAT_LEAGUES, UEFA_COUNTRY_CODE, OPENFOOTBALL_DOMESTIC_REPO, DOMESTIC_CUP_COMPETITIONS, PRELUDE_TOP_FILES, SECOND_TIER_FILES, SECOND_TIER_NAMES, LEAGUE_CONFIGS, TIEBREAK_RULES = complete; MARKET_ENGINE -> mancano ['bundesliga','ligue_1'].
- **Correzione**: Aggiungere le due voci esplicite (dp_theta=None, phi0=0.0, kappa=0.0, sharpen_1x2=False) con il commento della misura che le motiva, e un test che asserisca `set(MARKET_ENGINE) == set(LEAGUE_CONFIGS) == set(sources.LEAGUES)`.

**🟡 `F10-test-mancanti-nuove-leghe` — Nessun test sulle regole di spareggio delle due leghe nuove ne' sulla completezza delle mappe per-lega**  
*omissione · bassa · **confermato***

- **Dove**: tests/test_season_sim.py, tests/test_league_snapshots.py, src/models/season_sim.py:66-72, src/config.py:92-149
- **Atteso**: Regola §2 ("aggiungi un test per ogni nuova funzionalita'"): le TIEBREAK_RULES di Bundesliga e Ligue 1 — l'unica logica nuova del commit 327aa55, e un TERZO ordine di criteri mai presente prima — e la completezza delle mappe per-lega dovrebbero avere una copertura.
- **Trovato**: `grep -rn 'bundesliga|ligue_1' tests/` compare solo in test_estimates.py, test_league_snapshots.py e test_outright_archive.py; nessun test esercita `league_tiebreak('bundesliga')`/('ligue_1') ne' `final_table` su quelle leghe, e nessun test asserisce che ogni lega di `sources.LEAGUES` abbia una voce in LEAGUE_CONFIGS/MARKET_ENGINE/TIEBREAK_RULES (e' proprio il buco che ha lasciato passare MARKET_ENGINE a 3 voci). Anche il nuovo test del guard overround copre solo il ramo indice 0 (vedi F10-guard-retry-livello-sbagliato).
- **Come è stato accertato**: `grep -rn 'bundesliga\|ligue_1' tests/` (3 file, nessuno su season_sim/config); `python -m pytest` -> 194 verdi anche azzerando MARKET_ENGINE['premier_league'].
- **Correzione**: Aggiungere: (a) un test che per ognuna delle 5 leghe verifichi campione e ordine dei primi criteri su una stagione reale (Bayern 2024-25, PSG, Leverkusen 2023-24 sono gia' verificati a mano); (b) un test di completezza `set(mappa) == set(sources.LEAGUES)` su LEAGUE_CONFIGS, MARKET_ENGINE, TIEBREAK_RULES, UEFA_COUNTRY_CODE; (c) il ramo di ripiego del guard.

**🟡 `F10-db-meta-serie-a` — La tabella di provenienza del database SQLite dice "Serie A ... via mirror" in un progetto a 5 leghe con mirror morto**  
*incoerenza-doc · bassa · **confermato***

- **Dove**: src/data/database.py:96-98
- **Atteso**: La `note` di provenienza scritta in `meta` dovrebbe riportare la lega effettiva delle partite salvate e la fonte reale.
- **Trovato**: `"note": "Serie A, schema football-data.co.uk (via mirror). Ricostruibile con scripts/build_database.py."` e' una stringa fissa: qualunque lega si costruisca, il DB dichiara Serie A e un mirror che non esiste piu' (404, vedi F10-base-url-mirror-morto).
- **Come è stato accertato**: `sed -n 90,100p src/data/database.py`.
- **Correzione**: Derivare la nota dalla colonna `league` del DataFrame (o dal parametro di lega) e togliere il riferimento al mirror.

**🟡 `F10-guard-nan-parziale` — Con un lato del mercato mancante il guard non viene applicato affatto e la riga resta a meta'**  
*bug-codice · bassa · *non contro-verificato**

- **Dove**: src/data/loader.py:216-226
- **Atteso**: La docstring dice "si scarta IN BLOCCO (mai un solo lato)". Un mercato con un lato NaN e l'altro valorizzato non e' una linea: o si scarta tutto, o si dichiara esplicitamente che il caso e' ammesso.
- **Trovato**: Il guard e' dentro `if all(pd.notna(v) for v in picks.values())`: se anche una sola colonna del gruppo non trova candidati, il controllo viene saltato e il dict misto (alcuni valori, alcuni NaN) esce cosi' com'e'. Il codice non puo' nemmeno calcolare l'overround, quindi la riga passa senza alcuna verifica.
- **Come è stato accertato**: Lettura di src/data/loader.py:216-226. Impatto sui dati attuali: NULLO — controllo sui 5 snapshot: righe con notna parziale su ciascuno dei 4 gruppi di mercato = 0 (1X2 chiusura/apertura e O/U chiusura/apertura, tutte e 5 le leghe).
- **Correzione**: Portare il caso "NaN parziale" dentro la stessa politica: se il gruppo non e' completo, azzerare tutto il gruppo (o documentare esplicitamente che un lato solo e' ammesso e perche').

**🟡 `F10-grezzi-nuove-leghe-assenti` — Bundesliga e Ligue 1 non hanno alcun grezzo congelato nel repo: i loro snapshot non sono ri-derivabili offline**  
*omissione · bassa · ridimensionato*

- **Dove**: data/football_data_raw/ (solo serie_a_*.csv), files/ (solo bundle premier_league e la_liga), docs/DATI.md:164-168
- **Atteso**: Regola §5 (offline-first/riproducibilita'): come per Serie A (`data/football_data_raw/`, versionata) e per Premier/Liga (`files/football_data_*_bundle.json`, `files/understat_*_bundle.json`), anche le due leghe nuove devono avere i grezzi congelati e versionati, e docs/DATI.md §4 deve elencarli.
- **Trovato**: `data/football_data_raw/` contiene solo le 9 stagioni di Serie A; `files/` solo i 4 bundle di Premier e Liga. Per bundesliga e ligue_1 non esiste alcun CSV football-data ne' JSON Understat congelato: gli snapshot sono ri-derivabili solo ri-scaricando dalla rete (e col BASE_URL attuale nemmeno quello, vedi F10-base-url-mirror-morto). docs/DATI.md §4 "Fonti grezze congelate" non ha righe per le due leghe nuove e dichiara ancora "il sito originale non e' raggiungibile dal cloud" e "il mirror per-stagione e' sparito".
- **Come è stato accertato**: `ls data/football_data_raw/` -> README.md + serie_a_1718..2526.csv (10 file). `ls files/` -> football_data_{la_liga,premier_league}_bundle.json, understat_{la_liga,premier_league}_bundle.json, player_scores, README.md. `find . -iname '*bundesliga*' -not -path './.git/*'` -> nessun grezzo football-data/Understat. `sed -n 163,168p docs/DATI.md`.
- **Correzione**: Congelare i 18 CSV football-data (D1/F1, 2017-18..2025-26) in `data/football_data_raw/` e i JSON Understat delle due leghe in `files/` (o dichiarare esplicitamente in DATI.md §4 che le due leghe nuove NON hanno grezzo congelato e cosa comporta). Aggiungere le due righe alla tabella §4 e aggiornare lo stato della colonna "stato" delle righe esistenti.
- **Verifica avversariale**: Il fatto materiale c'e' (`ls data/football_data_raw/` = solo 9 CSV Serie A + README; `ls files/` = solo i 4 bundle Premier/Liga; nessun grezzo football-data/Understat per le due leghe nuove) e il buco in docs/DATI.md §4 e' reale: la tabella «Fonti grezze congelate» non ha righe per Bundesliga/Ligue 1 e ripete «il sito originale non e' raggiungibile dal cloud», affermazione che il manifest della stessa sessione falsifica. Ma la cornice «i loro snapshot non sono ri-derivabili» e' sbagliata su due punti che ho verificato: (1) NON e' una perdita da integrazione mal riuscita, e' una DECISIONE dichiarata — commit 6c9b377 («cantiere/data/fonti/ -> RIMOSSI: 135 MB di CSV e JSON ri-scaricabili. L'impronta SHA256 di ognuno resta nel manifest») e docs/audit_5_leghe/00_indice.md riga 23; (2) la ri-derivazione e' esatta e verificabile: ho riscaricato oggi le 18 stagioni D1/F1 dall'URL ufficiale e TUTTI E 18 gli SHA256 coincidono byte per byte con data/ricerca_esterna/manifest_fonti_audit.json (18 uguali, 0 diversi). Inoltre l'«atteso» invocato non e' una regola scritta: §5 dice offline-first sullo SNAPSHOT congelato (che c'e', versionato, 38 colonne), non sui grezzi. Il residuo e' quindi solo documentale: due righe mancanti in DATI.md §4 + una frase di raggiungibilita' da riscrivere.

**🟡 `F10-rank-spareggi-non-ufficiali` — season_sim.rank ordina con differenza reti anche dove la lega usa gli scontri diretti: retrocessione e top-4 sono prezzati con una regola e scorati con un'altra**  
*bug-codice · bassa · ridimensionato*

- **Dove**: src/models/season_sim.py:332-336 (chiave di `rank`), src/models/season_sim.py:219-223 (limite dichiarato), scripts/_run_fase94_drift.py:83-96, scripts/_run_fase97_relegation_market.py:110-111, CLAUDE.md:§4 (descrizione di season_sim.py)
- **Atteso**: Coerenza fra la probabilita' simulata e la verita' con cui la si scora: `final_table` (verita') applica gli spareggi ufficiali per lega — h2h come PRIMO criterio in Serie A e Liga — quindi anche le posizioni simulate usate per retrocessione/top-4 dovrebbero usarli.
- **Trovato**: `rank` e' costruito con la chiave punti -> differenza reti -> gol fatti per TUTTE le leghe; solo la vetta viene poi riallineata a `champion`. Le Fasi 94 e 97 calcolano `p_rel = (rank >= nt-2).mean()` e `p_top4 = (rank <= 4).mean()` e li confrontano con `is_rel`/`is_top4` derivati da `final_table(cur, lg)`, che usa gli spareggi ufficiali: modello e verita' usano due regole diverse proprio nelle posizioni in gioco. Il limite e' dichiarato nella docstring, ma con la motivazione "applicati solo alla vetta, l'unica che ci serve" — premessa decaduta quando la Fase 94 ha ADOTTATO la deriva sul mercato RETROCESSIONE e la Fase 97 ha costruito il mercato retrocessione.
- **Come è stato accertato**: Confronto sulle classifiche REALI (`final_table` con regola ufficiale vs ('gd','gf')): Serie A media 2.56 posizioni diverse per stagione, La Liga 3.33; posizioni toccate 3-4 e 16-18 in piu' stagioni. Esempio citabile — Serie A 2022-23, Spezia e Verona entrambe a 31 punti: ordine ufficiale (h2h) = 17 Spezia, 18 Verona; ordine di `rank` (gd: -31 vs -28) = 17 Verona, 18 Spezia. La 18a e' zona retrocessione (`is_rel = pos > nt-3`).
- **Correzione**: O si applicano le regole di lega anche a `rank` (almeno ai gruppi a pari punti attorno alle soglie 4 / nt-2), o si scorano le Fasi 94/97 contro una verita' costruita con la STESSA regola di `rank`. In ogni caso aggiornare la docstring (righe 219-223) e la descrizione in CLAUDE.md §4, che oggi dice "classifica con spareggi UFFICIALI per lega" senza riserve.
- **Verifica avversariale**: La misura si riproduce (`final_table` ufficiale vs ordinamento pts->gd->gf sulle 45 stagioni reali): Serie A 2.56 posizioni diverse per stagione, La Liga 3.33, e l'esempio Spezia/Verona 2022-23 esce identico (ufficiale 17 Spezia / 18 Verona; gd 17 Verona / 18 Spezia). E il difetto di fondo c'e': season_sim.py:332-336 costruisce `rank` con pts->gd->gf per TUTTE le leghe e la Fase 94 (scripts/_run_fase94_drift.py:83-96) scora p_rel/p_top4 contro `is_rel`/`is_top4` derivati da final_table con gli spareggi ufficiali. Ma il rilievo e' sovradimensionato su quattro punti verificati: (1) Premier, Bundesliga e Ligue 1 danno 0 differenze su 9 stagioni reali ciascuna (i loro criteri ufficiali iniziano con gd->gf, cioe' proprio la chiave di `rank`) — il problema riguarda 2 leghe su 5; (2) la citazione della Fase 97 e' SBAGLIATA: `_run_fase97_relegation_market.py` e' un confronto Premier-only (SMARKETS_TO_OURS, Premier 2026-27), dove la regola di `rank` COINCIDE con quella ufficiale, e per sua stessa dichiarazione «NON e' un test di edge... il verdetto e' a maggio 2027», quindi non esiste alcuna verita' contro cui scorare; (3) il limite NON e' nascosto: sta in docstring con «ATTENZIONE» (season_sim.py:219-223), quindi e' una motivazione da aggiornare, non un bug taciuto; (4) non ribalta nulla: la Fase 94 confronta due varianti che usano la STESSA chiave di rank, quindi l'adozione della deriva sulla retrocessione non e' toccata. Il residuo vero e' quantificabile: su Serie A 2024-25 con 4.000 simulazioni la parita' di punti cade al confine 17/18 nel 15.1% delle stagioni e al confine 4/5 nel 16.0%, quindi in SA/Liga vale la pena o allineare `rank` o dirlo nella docstring.

**🟡 `F10-registro-correzioni-percorso-morto` — Il registro delle correzioni rimanda a un file del cantiere cancellato**  
*import-rotto · bassa · ridimensionato*

- **Dove**: data/correzioni_dichiarate.csv, colonna `motivo` delle 16 righe odds_*_open (righe 5-20)
- **Atteso**: Un registro versionato che deve restare leggibile a distanza di sessioni non puo' citare percorsi cancellati (§5-bis R3: "un numero cambiato a mano e' un numero che nessuno potra' piu' spiegare").
- **Trovato**: Tutte e 16 le righe di correzione delle quote chiudono con "Proposta di guard generale in cantiere/patch/guard_overround.md"; la cartella cantiere/ e' stata cancellata dal commit 6c9b377 e quel file non esiste piu' da nessuna parte nel repo.
- **Come è stato accertato**: `python3 -c "import pandas as pd; d=pd.read_csv('data/correzioni_dichiarate.csv'); print(d[d.colonna.str.contains('odds')].motivo.iloc[0])"`; `find . -name 'guard_overround.md' -not -path './.git/*'` -> nessun risultato.
- **Correzione**: Sostituire il riferimento con il puntatore reale al guard adottato (`src/data/loader.py:91-99`, ORR_MAX, commit ec85314), oppure recuperare il documento in docs/audit_5_leghe/.
- **Verifica avversariale**: Il documento NON e' perduto: `find . -iname '*guard*'` lo trova in docs/audit_5_leghe/patch_guard_overround_APPLICATA.md — stesso contenuto (problema, tabella dell'overround, soglia 1.12, patch, effetto atteso 11 celle, test da aggiungere), rinominato col suffisso APPLICATA che registra che la patch e' stata applicata. La ricerca dell'auditor ha fallito perche' cercava il basename esatto `guard_overround.md`; il suo stesso «fix» («recuperare il documento in docs/audit_5_leghe/») era gia' stato eseguito dal commit di integrazione. Vero e riprodotto il resto: le 16 righe odds_* di data/correzioni_dichiarate.csv chiudono con «Proposta di guard generale in cantiere/patch/guard_overround.md», e la tabella di corrispondenza di docs/audit_5_leghe/00_indice.md:15-23 mappa report/REGOLE/out/data ma NON patch/. Difetto quindi puramente cosmetico (una stringa di percorso stantia in un registro versionato), non una perdita di contenuto — e segnalarlo come perdita rischia di far ri-creare un file che esiste gia'.

**🟡 `F10-orr-max-sigma` — Il commento di ORR_MAX attribuisce alla distribuzione O/U un "~6 sigma" che e' quello dell'1X2 (per l'O/U sono 10.3), e il conteggio righe non torna**  
*numero-errato · bassa · ~~smontato~~*

- **Dove**: src/data/loader.py:91-99
- **Atteso**: "Distribuzione dell'overround O/U sulle 5 leghe: nell'era Avg (12.457 righe) il MASSIMO mai osservato e' 1.0765 ... 1.12 sta ~6 sigma oltre la mediana sana" — i tre numeri devono riferirsi alla stessa popolazione.
- **Trovato**: Sulle righe con O/U di CHIUSURA nei 5 snapshot: n = 12.459 (non 12.457), mediana 1.0503, sd 0.0068, massimo 1.0755 (non 1.0765) e 1.12 dista 10.3 sigma. Il valore 1.0765 e' il massimo dell'O/U di APERTURA nell'era Avg (Ligue 1) e il "~6 sigma" corrisponde alla distribuzione 1X2 (6.7 sigma su odds_home, 6.2 su odds_home_open, con massimo 1.0797 ~ il "1.080" citato nella frase successiva). Il 12.457 e' il numero di partite usate dal fit pooled delle stime (che richiede anche la chiusura 1X2), non le righe con O/U.
- **Come è stato accertato**: Ricalcolo sui 5 snapshot: O/U chiusura n=12459, med 1.0503, sd 0.0068, max 1.0755, (1.12-med)/sd = 10.3; 1X2 chiusura n=16109, med 1.0439, sd 0.0114, sigma 6.7, max 1.0755; 1X2 apertura max 1.0797. Massimo assoluto su tutti i mercati e tutte le leghe: 1.0947 (Bundesliga O/U apertura, era Betbrain).
- **Correzione**: Riscrivere il commento separando le due popolazioni (O/U: n, max, sigma; 1X2: n, max, sigma), oppure citare il solo dato che conta e che ho verificato: il massimo osservato su TUTTI i mercati e tutte le leghe e' 1.0947, quindi 1.12 non puo' scartare una riga buona. La conclusione operativa non cambia.
- **Verifica avversariale**: I due numeri accusati di essere sbagliati sono ESATTI per la popolazione che il commento descrive, e l'auditor ha misurato la serie sbagliata. Ricalcolo sui 5 snapshot: O/U di APERTURA nell'era Avg (stagioni 1920+) -> n = 12.457 e massimo 1.0765, cifra per cifra come nel commento; e' l'O/U di CHIUSURA a dare n=12.459 e max 1.0755. Che il commento parli della linea di apertura e' obbligato dalla frase successiva («nell'era Betbrain 2017-19 si arriva a 1.339»): nel 2017-19 la CHIUSURA O/U non esiste affatto (Fase 73), quindi 1.339 puo' venire solo dalla pre-match, ed e' li' che vivevano le 11 celle corrotte che il guard doveva prendere. Il documento sorgente lo conferma: docs/audit_5_leghe/patch_guard_overround_APPLICATA.md riporta la tabella «2017-19 (BbAv) n 3.651 ... max 1.339 | 2019-20+ (Avg) n 12.457, p99.9 1.0757, max 1.0765» — e 3.651 meno le 11 celle svuotate dal guard fa 3.640, esattamente quante ne conto oggi nello snapshot. Cade anche la spiegazione alternativa proposta («12.457 e' l'n del fit pooled»): coincide, ma perche' quel fit gira sulle stesse righe. Corretto pure il «massimo osservato 1.080» per l'1X2 (misurato 1.0797 sull'apertura). Resta in piedi UN SOLO dettaglio, minore: il «~6 sigma» non e' quello della serie citata (9.3) ma della distribuzione POOLED dei quattro gruppi di quote (n=60.775, mediana 1.0479, sd 0.0110 -> 6.5 sigma), ed e' trascritto tale e quale dal documento d'audit; la conclusione operativa non cambia, come ammette lo stesso rilievo. Da non «correggere» i numeri: semmai aggiungere la parola «apertura» e dire su quale popolazione e' il sigma.

<details><summary>Verifiche con esito OK su questo fronte</summary>

- Snapshot Bundesliga e Ligue 1 ri-derivati integralmente col codice di PRODUZIONE (`loader._normalize`) dai CSV football-data.co.uk scaricati oggi, tutte e 9 le stagioni: 5.851 partite × 14 colonne (gol, tiri in porta, 10 colonne quota) + date -> 0 celle diverse, con la sola eccezione delle 2 celle della correzione dichiarata R1 (Union Berlin-Bochum 14/12/2024, 1-1 del campo contro 0-2 del tribunale). La verifica 'riga per riga' del commit 03d5bec regge.
- Snapshot Serie A: le 10 colonne quota ri-derivate da `data/football_data_raw/` con `loader._odds_from_raw` (guard bilaterale incluso) -> 0 celle diverse su 3.420 righe, e conteggi NaN identici colonna per colonna.
- Guard overround: applicato a TUTTI e 4 i gruppi (1X2 chiusura, O/U chiusura, 1X2 apertura, O/U apertura), somma corretta su 3 esiti per l'1X2 e 2 per l'O/U, sia in `_normalize` sia in `_odds_from_raw`/`_open_odds_market`/`add_open_odds`; quote <= 1.0, negative o assenti sono gia' filtrate da `_pick_odds`. Sui 5 snapshot nessuna riga ha overround fuori da [1.0, 1.12] su nessuno dei 4 mercati (massimo assoluto 1.0947).
- Le 11 righe con overround impossibile citate dal commit ec85314 sono confermate e localizzate: 3 in La Liga 1819 (Alaves-Real Madrid 1.2825, Eibar-Real Madrid 1.2814, Leganes-Betis 1.1279 — ricalcolate dal bundle) prodotte dal guard, e 8 in Bundesliga/Ligue 1 gia' registrate in `data/correzioni_dichiarate.csv`; il massimo dichiarato 1.339 e' Dortmund-Wolfsburg 1819. Per le 3 righe La Liga nessun ripiego sano esisteva davvero (le colonne B365>2.5/<2.5 non ci sono in quella stagione).
- Guard xG segnaposto: la condizione in `understat._e_segnaposto` e' davvero congiuntiva (xG intero == gol su ENTRAMBI i lati AND deep==0 su entrambi AND ppda NaN su entrambi) e il confronto e' esatto su float che valgono interi, quindi senza rischio di tolleranza. Sui 5 snapshot una sola riga risulta annullata (Holstein Kiel-Bochum 09/02/2025) su 16.110 partite con record Understat — l'altra riga senza xG e' Nantes-Toulouse 17/05/2026, che in fonte ha `isResult=false`. Le 3 partite davvero sterili con deep=0 su entrambi i lati (Reims-Lille 30/08/2020, West Brom-West Ham 16/09/2017, West Ham-Swansea 30/09/2017) restano intatte con xG misurato. Ri-eseguito `parse_season_xg` sui bundle Understat di Premier e Liga (6.840 partite): 0 falsi positivi.
- TEAM_ALIASES: 234 chiavi totali, esattamente 104 aggiunte dal commit 03d5bec, 0 chiavi duplicate nel dict letterale, 0 chiavi che sono anche un valore canonico di un'altra voce, 0 chiavi mappate a valori diversi; `canonical_team` e' idempotente su tutti i 153 nomi squadra presenti nei 5 snapshot (nessuna collisione fra leghe). L'affermazione '0 conflitti con gli esistenti' e' verificata.
- Mappe per-lega: 9 su 10 complete per tutte e 5 le leghe (UNDERSTAT_LEAGUES, UEFA_COUNTRY_CODE, OPENFOOTBALL_DOMESTIC_REPO, DOMESTIC_CUP_COMPETITIONS, PRELUDE_TOP_FILES, SECOND_TIER_FILES, SECOND_TIER_NAMES, LEAGUE_CONFIGS, TIEBREAK_RULES); i campi di LEAGUE_CONFIGS per Bundesliga e Ligue 1 sono gli stessi 5 delle altre tre e sono letti davvero da backtest.py e predict.py via `league_config`.
- Builder URL openfootball generalizzato: verificato 200 su italy/england/espana/deutschland con lo schema `{season}/{comp}` e sul mono-repo francese con `france/{season}_{comp}` (fr1 e fr2, 9 stagioni su 9). L'unico 404 e' la Coupe de France fuori dal 2024-25 — gestito senza crash (`download_openfootball` tratta il 404 come lacuna di copertura) e gia' dichiarato in docs/DATI.md:75-76 e nel report caccia_calendari; coerente con le 82 righe di Coupe de France, tutte in stagione 2425.
- TIEBREAK_RULES nuove: le classifiche finali danno i campioni veri su 9 stagioni (Bayern ×8 + Leverkusen 2023-24; PSG ×8 + Lille 2020-21). L'ordine Ligue 1 ('gd','h2h','gf') e' empiricamente indistinguibile da ('gd','gf') e da ('gd','gf','h2h') su tutte e 9 le stagioni reali (0 posizioni diverse), quindi il 'terzo ordine' non introduce rischio; `league_tiebreak` su lega ignota ricade su DEFAULT_TIEBREAK senza crash, e `_resolve_sim_tie` indicizza correttamente `hg/ag` in locale e `gdiff/gfor` in globale.
- Costanti del motore: `DixonColesModel` fitta (φ0, κ) dai dati di allenamento (nessun valore Serie A cablato); `predict.py` legge sia `league_config` sia `market_engine` per lega e stampa a video quando il motore e' LISCIO; le costanti DP_THETA=1.225 / DP_THETA_DC=1.138 restano solo come default della firma di `sharpen_1x2`, invocata unicamente dove `eng['sharpen_1x2']` e' True (Serie A). `backtest.py` non applica dp/φ35 di default.
- Suite di test: `python -m pytest` -> 194 passati in 49s, coerente con il numero dichiarato dal commit ec85314.

</details>

### Script migrati dal cantiere  ·  19 rilievi
**🔴 `F11-01-root-parents2` — ROOT sbagliato in 27 script su 32: `parents[2]` punta a /home/user, non alla radice del repo — 24 script non partono neppure**  
*bug-codice · alta · *non contro-verificato**

- **Dove**: scripts/tranche3_tracer.py:37, scripts/tranche3_ritaratura.py:33, scripts/audit_snapshots.py:33, scripts/nuove_leghe.py:28, scripts/audit_anomalie.py:~50, scripts/build_new_snapshot.py:~34, scripts/cerca_segnaposto.py:~86, scripts/eda_nuove_leghe.py:~25, scripts/leve_beat_close.py:~102, scripts/leve_dc_panchina.py:~66, scripts/leve_devig_shin.py:~82, scripts/leve_ricalibrazioni.py:~76, scripts/leve_theta_griglia.py:~50, scripts/nuovo_calibrazione.py:~99, scripts/nuovo_mercato_campione.py:~93, scripts/recupero_squad_value_tm.py:~36, scripts/riconcilia_nomi.py:~30, scripts/stima_celle_residue.py:~66, scripts/stima_ou_close_nuove.py:~93, scripts/stima_ou_corrotte.py:~31, scripts/stima_sot_understat.py:~80, scripts/tranche3_market_tracer.py:~34, scripts/tranche3_mercati.py:~32, scripts/verifica_stime.py:~47, scripts/applica_correzioni.py:27, scripts/applica_squad_value_tm.py:26, scripts/fetch_sources.py:41
- **Atteso**: ROOT = radice del repo (/home/user/Polymarket-oracle), come nei 122 script nativi di scripts/ che usano `Path(__file__).resolve().parents[1]`
- **Trovato**: `ROOT = Path(__file__).resolve().parents[2]`, corretto quando il file stava in `cantiere/scripts/` ma che dopo lo spostamento in `scripts/` vale `/home/user`. Conseguenza immediata: `sys.path.insert(0, str(ROOT))` inserisce /home/user e `from src... import ...` fallisce.
- **Come è stato accertato**: `python3 -c "from pathlib import Path; p=Path('/home/user/Polymarket-oracle/scripts/tranche3_tracer.py'); print(p.resolve().parents[1], p.resolve().parents[2])"` -> `/home/user/Polymarket-oracle /home/user`. Eseguendo `python3 scripts/<f> --help` su tutti e 32 gli script mossi: 24 muoiono con `ModuleNotFoundError: No module named 'src'` (audit_anomalie, audit_snapshots, build_new_snapshot, cerca_segnaposto, eda_nuove_leghe, leve_beat_close, leve_dc_panchina, leve_devig_shin, leve_ricalibrazioni, leve_theta_griglia, nuove_leghe, nuovo_calibrazione, nuovo_mercato_campione, recupero_squad_value_tm, riconcilia_nomi, stima_celle_residue, stima_ou_close_nuove, stima_ou_corrotte, stima_sot_understat, tranche3_market_tracer, tranche3_mercati, tranche3_ritaratura, tranche3_tracer, verifica_stime). `grep -l "parents\[2\]" scripts/*.py | wc -l` = 27, e tutti e 27 sono fra i 32 file mossi dal commit 6c9b377 (nessun falso positivo fra i nativi); `grep -l "parents\[1\]" scripts/*.py | wc -l` = 122.
- **Correzione**: In tutti e 27 i file: `parents[2]` -> `parents[1]`. Fix meccanico, verificabile con uno smoke test `--help` su tutti gli script di scripts/ (vedi F11-16).

**🔴 `F11-02-percorsi-cantiere` — 31 script su 32 (+2 in data/ricerca_esterna/) contengono percorsi FUNZIONALI verso cantiere/, cancellata: nessuno dei 32 gira oggi**  
*import-rotto · alta · *non contro-verificato**

- **Dove**: scripts/tranche3_ritaratura.py:44-45, scripts/tranche3_tracer.py:48-49, scripts/audit_snapshots.py:41-42,50-51,80, scripts/leve_beat_close.py:117,127-128, scripts/ggng_contro_quote.py:114-115,132-133,136,339, scripts/leve_apertura.py:118,123,1194, scripts/stima_celle_residue.py:69-70,77-78,84-85,87,533,876, scripts/stima_ou_open_bakeoff.py:99-103,864, scripts/stima_sot_understat.py:98-104, scripts/nuovo_fronte_generale.py:97,104-105,407,1078, scripts/build_new_snapshot.py:43-44, scripts/fetch_sources.py:42, scripts/applica_correzioni.py:28, scripts/applica_squad_value_tm.py:27, scripts/recupero_squad_value_tm.py:46-47,118, scripts/verifica_stime.py:50,228, scripts/riconcilia_nomi.py:33-34, scripts/eda_nuove_leghe.py:35,37-38, scripts/audit_anomalie.py:61-62,65-66, scripts/cerca_segnaposto.py:99,104, scripts/leve_devig_shin.py:97,104-105, scripts/leve_dc_panchina.py:80-82, scripts/leve_phi_griglia.py:72, scripts/leve_ricalibrazioni.py:91,98-99, scripts/leve_theta_griglia.py:64,71-72, scripts/nuovo_calibrazione.py:118,124-125, scripts/nuovo_mercato_campione.py:112,133, scripts/stima_ou_close_nuove.py:106-108,114, scripts/stima_ou_corrotte.py:43, scripts/tranche3_market_tracer.py:47,49-50, scripts/tranche3_mercati.py:47, data/ricerca_esterna/_valida_footiqo.py:37,47,52-53,55, data/ricerca_esterna/_confuta_footiqo.py:43,53-54,59-60
- **Atteso**: Percorsi verso le destinazioni reali di oggi, secondo la tabella che l'integrazione stessa dichiara in docs/audit_5_leghe/00_indice.md: cantiere/data/{lega}_matches.csv -> data/{lega}_matches.csv; cantiere/data/correzioni_dichiarate.csv -> data/correzioni_dichiarate.csv; cantiere/data/stime/ -> data/estimates/; cantiere/data/ricerca/ -> data/ricerca_esterna/; cantiere/out/*.json -> docs/audit_5_leghe/numeri/; cantiere/scripts -> scripts; cantiere/data/club_fixtures_*.csv e squad_value_2526_transfermarkt.csv -> data/
- **Trovato**: I percorsi puntano ancora a cantiere/. Classificazione precisa: 31 dei 32 script mossi hanno almeno un path-join funzionale `ROOT / "cantiere" / ...` (l'unico con sola menzione nel docstring e' scripts/nuove_leghe.py:4). Anche 2 dei 4 script finiti in data/ricerca_esterna/ leggono via cantiere i file che ora stanno nella loro STESSA cartella.
- **Come è stato accertato**: Esecuzioni reali. `python3 scripts/applica_correzioni.py --dry-run` -> `FileNotFoundError: '/home/user/cantiere/data/correzioni_dichiarate.csv'`. `python3 scripts/applica_squad_value_tm.py --dry-run` -> `FileNotFoundError: '/home/user/cantiere/data/squad_value_2526_transfermarkt.csv'`. `python3 scripts/leve_apertura.py` e `python3 scripts/leve_phi_griglia.py` -> `FileNotFoundError: '/home/user/Polymarket-oracle/cantiere/data/bundesliga_matches.csv'`. `python3 scripts/ggng_contro_quote.py` -> `FileNotFoundError: '/home/user/Polymarket-oracle/cantiere/data/ricerca/footiqo_serie_a_2017-2018.json'` (il file esiste, in data/ricerca_esterna/). `python3 data/ricerca_esterna/_valida_footiqo.py` e `_confuta_footiqo.py` -> stesso FileNotFoundError. Conteggio dei join funzionali via script di classificazione riga-per-riga su tutti i .py del repo.
- **Correzione**: Introdurre in ognuno le costanti nuove (o meglio: un modulo comune `scripts/_audit_paths.py` con ROOT/DATA/OUT/RIC/STIME) e sostituire i join. Dopo il fix va rieseguito almeno `applica_correzioni.py --dry-run` (che ha guardie R3 e si ferma da solo se i dati non tornano) come prova di non-regressione.

**🔴 `F11-03-fetch-scrive-fuori-repo` — fetch_sources.py scarica 135 MB FUORI dalla radice del repo, in /home/user/cantiere/, senza errore**  
*bug-codice · alta · *non contro-verificato**

- **Dove**: scripts/fetch_sources.py:41-45
- **Atteso**: Le fonti grezze vanno in una cartella dentro il repo (e ignorata da git), es. `data/raw_audit/` o `data/fonti/`, coerente con quanto il manifest promette di poter riprodurre.
- **Trovato**: `ROOT = Path(__file__).resolve().parents[2]` (= /home/user) e `OUT = ROOT / "cantiere" / "data" / "fonti"` -> lo script crea e riempie `/home/user/cantiere/data/fonti/`, cioe' un albero fantasma FUORI dal repository, invisibile a git e mai piu' trovato da nessuno. E' l'unico dei 32 script che 'funziona' senza eccezione, il che lo rende il piu' pericoloso: fallisce in silenzio.
- **Come è stato accertato**: Eseguito `timeout 100 python3 scripts/fetch_sources.py`; subito dopo `find /home/user/cantiere -type f` elencava file realmente scaricati, es. `/home/user/cantiere/data/fonti/football_data/serie_a_1718.csv`, `/home/user/cantiere/data/fonti/football_data/premier_league_2021.csv`. Ho rimosso l'albero che avevo creato io (`rm -rf /home/user/cantiere`). E' inoltre il PRIMO comando del blocco 'Come rifare tutto da zero' in docs/audit_5_leghe/00_indice.md:106.
- **Correzione**: `parents[2]` -> `parents[1]` e `OUT = ROOT / "data" / "fonti"` (aggiungendo `data/fonti/` a .gitignore, come gia' fatto per `data/raw/`). Il MANIFEST (riga 45) va scritto invece in una posizione versionata, perche' e' l'unica prova di riproducibilita' (vedi F11-06).

**🟠 `F11-04-input-cancellato-ggng` — Riferimenti a file di dati CANCELLATI dallo stesso commit: correggere il prefisso cantiere/ non basta**  
*import-rotto · media · *non contro-verificato**

- **Dove**: scripts/ggng_contro_quote.py:136, scripts/stima_ou_close_nuove.py:107-108, scripts/stima_ou_open_bakeoff.py:103
- **Atteso**: ggng_contro_quote.py deve leggere `data/estimates/ou_close_2017_19.csv` (3.638 righe, tutte e 5 le leghe, bundesliga 604 + ligue_1 758 = le 1.362 righe del file soppresso); stima_ou_open_bakeoff.py deve scrivere `data/estimates/ou_open_corrotte_2017_19.csv` (nome nuovo).
- **Trovato**: ggng_contro_quote.py:136 elenca fra le STIME `ROOT/'cantiere'/'data'/'stime'/'ou_close_2017_19_nuove_leghe.csv'`, file che il commit 6c9b377 ha ELIMINATO come superato. stima_ou_close_nuove.py:107 lo produce ancora e :108 legge `cantiere/data/stime_ou_corrotte.csv`, anch'esso eliminato. stima_ou_open_bakeoff.py:103 scrive `ou_open_corrotte_v2.csv`, mentre in `data/estimates/` il file e' stato RINOMINATO in `ou_open_corrotte_2017_19.csv`: un fix meccanico del solo prefisso creerebbe un doppione con nome vecchio.
- **Come è stato accertato**: `git show --numstat -M 6c9b377` mostra `0 1363 cantiere/data/stime/ou_close_2017_19_nuove_leghe.csv` e `0 9 cantiere/data/stime_ou_corrotte.csv` come cancellazioni pure (nessuna destinazione), e `cantiere/data/stime/ou_open_corrotte_v2.csv => data/estimates/ou_open_corrotte_2017_19.csv` come rinomina. Verificata la supersessione: `pd.read_csv('data/estimates/ou_close_2017_19.csv')` -> 3638 righe, bundesliga 604 / la_liga 756 / ligue_1 758 / premier_league 760 / serie_a 760 (604+758=1362 = le righe del file soppresso). `ls data/estimates/` non contiene ne' `ou_close_2017_19_nuove_leghe.csv` ne' `stime_ou_corrotte.csv` ne' `ou_open_corrotte_v2.csv`.
- **Correzione**: In ggng_contro_quote.py:135-136 ridurre STIME alla sola `data/estimates/ou_close_2017_19.csv`. In stima_ou_open_bakeoff.py:103 usare il nome nuovo. stima_ou_close_nuove.py e' di fatto superato dal fit pooled a 5 leghe: o si riadatta a scrivere `data/estimates/ou_close_2017_19.csv`, o va marcato come storico nel suo docstring.

**🟠 `F11-05-tracer-pred-persi` — I 5 `tracer_pred_*.csv` (input di 5 script) cancellati senza destinazione e senza menzione nel messaggio di commit, e il rigeneratore e' rotto**  
*omissione · media · *non contro-verificato**

- **Dove**: git 6c9b377 (cantiere/out/tracer_pred_{serie_a,premier_league,la_liga,bundesliga,ligue_1}.csv); consumatori: scripts/leve_dc_panchina.py:247,640, scripts/leve_apertura.py:123, scripts/nuovo_calibrazione.py:534, scripts/tranche3_mercati.py:61, scripts/tranche3_ritaratura.py:92; produttore: scripts/tranche3_tracer.py:119
- **Atteso**: O spostati accanto agli altri artefatti (es. docs/audit_5_leghe/numeri/ o experiments/, come si e' fatto per experiments/fase93_discrimination.csv), oppure cancellati dichiarando esplicitamente che si rigenerano — e con il rigeneratore funzionante.
- **Trovato**: Cancellati puri: 5 file, 10.735 righe complessive di predizioni walk-forward per partita. Il messaggio di commit elenca tutte le altre soppressioni (fonti, ou_close_nuove_leghe, ou_open_corrotte, celle_residue) ma NON questi. Sono l'input di 5 script, e l'unico che li rigenera (tranche3_tracer.py) e' fra i 24 che non partono (F11-01).
- **Come è stato accertato**: `git show --numstat -M 6c9b377 | grep tracer_pred` -> `0 1837 cantiere/out/tracer_pred_bundesliga.csv`, `0 2281 .../la_liga.csv`, `0 2059 .../ligue_1.csv`, `0 2281 .../premier_league.csv`, `0 2281 .../serie_a.csv`, tutti senza `=>`. `grep -n tracer_pred scripts/*.py` mostra i 6 consumatori/produttore. `python3 scripts/tranche3_tracer.py --help` -> ModuleNotFoundError.
- **Correzione**: Dopo il fix di F11-01/F11-02, rigenerare i 5 CSV con `python scripts/tranche3_tracer.py` e versionarli in `docs/audit_5_leghe/numeri/` (o experiments/), oppure dichiarare nell'indice che sono rigenerabili con quel comando. La seconda opzione e' accettabile solo se il comando funziona davvero.

**🟠 `F11-06-manifest-incompleto` — «L'impronta SHA256 di OGNUNO resta nel manifest» e' falso: il manifest copre 36 dei 140 file grezzi cancellati**  
*conclusione-non-supportata · media · *non contro-verificato**

- **Dove**: git 6c9b377 (corpo del messaggio); docs/audit_5_leghe/00_indice.md:22 (riga della tabella `cantiere/data/fonti/`); data/ricerca_esterna/manifest_fonti_audit.json
- **Atteso**: Se si cancellano 135 MB di fonti dichiarandole ri-scaricabili, l'impronta deve coprire TUTTI i file cancellati, altrimenti l'audit non e' piu' riproducibile per la parte scoperta.
- **Trovato**: Il manifest (che e' l'ex `cantiere/data/fonti/manifest.json`, scritto solo da fetch_sources.py) ha 90 voci e copre esclusivamente football-data + Understat-lega. Dei 140 file versionati sotto cantiere/data/fonti/ e cancellati, 36 hanno impronta e 104 NO: 84 .txt openfootball (calendari coppe/seconde divisioni/coppe europee, da cui derivano club_fixtures_* e le 3.045 righe di calendario), 16 .html transfermarkt_web (la cache da cui vengono le 16 celle di valore rosa 2025-26 della regola R2), 4 .json understat_match (proprio i tiro-per-tiro che sono la PROVA del caso R5 dell'xG 0.00 con gol).
- **Come è stato accertato**: Script di confronto: `json.load(data/ricerca_esterna/manifest_fonti_audit.json)['files']` -> 90 chiavi, 0 senza sha256; `git ls-tree -r --name-only 46bf0fc | grep 'cantiere/data/fonti/'` (escluso manifest.json) -> 140 file; intersezione = 36, differenza = 104 (elencata per intero). Nota accessoria: le 90 chiavi del manifest sono ancora nella forma `cantiere/data/fonti/...`, quindi anche la verifica delle 36 coperte richiede una traduzione dei percorsi.
- **Correzione**: Correggere la riga dell'indice e il claim, dicendo cosa e' coperto e cosa no; e/o rigenerare un manifest completo (openfootball e understat_match sono ri-scaricabili e andrebbero aggiunti a fetch_sources.py). I 16 HTML Transfermarkt vanno trattati a parte: sono la fonte secondaria dichiarata di R2 e non necessariamente ri-ottenibili identici.

**🟠 `F11-07-link-rotti-indice` — 21 link relativi rotti nei report spostati, 11 dei quali sono l'INTERA tabella dei report nell'indice**  
*incoerenza-doc · media · *non contro-verificato**

- **Dove**: docs/audit_5_leghe/00_indice.md:36-48 (11 link a `report/NN_*.md`), docs/audit_5_leghe/04_decisioni.md:168,170,214, 05_tranche1.md:11,66, 07_dati_corrotti.md:15,128, 09_chiusura_buchi.md:339, REGOLE.md:32,96
- **Atteso**: I link devono puntare ai file vicini (`01_audit_dati.md`, …, `REGOLE.md`, `patch_guard_overround_APPLICATA.md`, `../../data/correzioni_dichiarate.csv`).
- **Trovato**: L'indice — l'unico file che il commit ha DAVVERO riscritto (30 inserzioni / 23 cancellazioni) e in cui e' stata aggiunta la tabella di corrispondenza vecchio->nuovo — continua a linkare `report/01_audit_dati.md` … `report/11_ggng.md`. `docs/audit_5_leghe/report/` non esiste: i file stanno un livello sopra. Altri 10 link nei report puntano a `../REGOLE.md`, `../data/...`, `../patch/guard_overround.md`.
- **Come è stato accertato**: Checker dei link relativi su tutti i .md di docs/audit_5_leghe/: 21 bersagli inesistenti (elenco completo con file:riga). `ls docs/audit_5_leghe/report` -> `No such file or directory`. Il commit ha rinominato `cantiere/patch/guard_overround.md` -> `docs/audit_5_leghe/patch_guard_overround_APPLICATA.md`, quindi anche `../patch/guard_overround.md` va riscritto.
- **Correzione**: Sostituire `report/NN` -> `NN`, `../REGOLE.md` -> `REGOLE.md`, `../patch/guard_overround.md` -> `patch_guard_overround_APPLICATA.md`, `../data/correzioni_dichiarate.csv` -> `../../data/correzioni_dichiarate.csv`, `../data/stime_ou_corrotte.csv` -> `../../data/estimates/ou_open_corrotte_2017_19.csv` (vedi F11-13).

**🟠 `F11-08-come-rifare-tutto` — Il blocco «Come rifare tutto da zero» dell'indice e' interamente non eseguibile, e la frase che lo chiude e' ora falsa**  
*incoerenza-doc · media · *non contro-verificato**

- **Dove**: docs/audit_5_leghe/00_indice.md:104-119 (8 comandi) e :117-119 (la frase sulle fonti versionate); stesso file :81-102 (blocco «Contenuto» che descrive l'albero cantiere/)
- **Atteso**: Comandi `python scripts/<f>.py` funzionanti, e una descrizione della struttura odierna.
- **Trovato**: Gli 8 comandi sono nella forma `python cantiere/scripts/fetch_sources.py` ecc.: il percorso non esiste piu' (errore immediato) e, anche corretto in `scripts/`, 7 degli 8 script su 8 falliscono per F11-01/F11-02. La frase «Gli snapshot delle leghe nuove si rigenerano offline dalle fonti versionate in `data/fonti/`» e' oggi falsa due volte: le fonti sono state cancellate proprio da questo commit, e non sono mai state in `data/fonti/`. Il blocco «Contenuto» descrive ancora l'albero `cantiere/` con `out/`, `patch/`, `report/`, `data/fonti/`.
- **Come è stato accertato**: Lettura di docs/audit_5_leghe/00_indice.md righe 81-119; esecuzione degli script citati (F11-01/F11-02); `ls data/fonti` inesistente; `git show --numstat -M 6c9b377 | grep 'cantiere/data/fonti'` -> 140 cancellazioni.
- **Correzione**: Riscrivere il blocco con i percorsi `scripts/`, aggiungere l'avvertenza che il passo 1 (fetch_sources) e' obbligatorio perche' le fonti NON sono versionate, e aggiornare il blocco «Contenuto» alla struttura odierna (o rimuoverlo, dato che la tabella di corrispondenza in testa lo rende ridondante).

**🟠 `F11-09-audit5leghe-orfano` — docs/audit_5_leghe/ (11 report + 37 artefatti numerici) non e' referenziato da NESSUN documento del progetto; nemmeno data/correzioni_dichiarate.csv e data/ricerca_esterna/**  
*omissione · media · *non contro-verificato**

- **Dove**: CLAUDE.md §4 «Mappa del repo» (righe ~330-395), docs/DATI.md, README.md, docs/DIARIO.md:10960
- **Atteso**: Per la regola §2 del CLAUDE.md e per la mappa §4 («dove sta cosa»), l'esito della Fase 100 dev'essere raggiungibile: la mappa dovrebbe elencare `docs/audit_5_leghe/`; `docs/DATI.md`, che per mandato e' il «catalogo di TUTTI i dati (reali e stimati)», dovrebbe elencare `data/ricerca_esterna/` (quote 1xBet reali + 3.045 righe di calendario coppe) e `data/correzioni_dichiarate.csv` (il registro che §5-bis R3 rende obbligatorio).
- **Trovato**: `grep -rn 'audit_5_leghe' --include='*.md' .` fuori dalla cartella stessa: ZERO occorrenze. Il DIARIO (riga 10960-10961) dice «Il lavoro e' stato svolto in una cartella isolata (`cantiere/`, poi integrata) e ha prodotto undici report» senza mai dire dove siano finiti — e nomina una cartella che non esiste piu'. `grep -rn 'correzioni_dichiarate|ricerca_esterna' CLAUDE.md docs/DATI.md README.md` -> ZERO occorrenze (mentre `outright_snapshots` e `football_data_raw` sono correttamente catalogati in DATI.md:265,166).
- **Come è stato accertato**: grep ricorsivi sopra; lettura di CLAUDE.md §4 per intero (elenca src/, scripts/, experiments/, data/*_matches.csv, football.db, i 7 file docs/*.md, lavoro_aperto.md, newseason.md, tests/ — e nient'altro); lettura di docs/DIARIO.md:10949-10975.
- **Correzione**: Aggiungere a CLAUDE.md §4 le voci `docs/audit_5_leghe/` (+ `numeri/`), `data/correzioni_dichiarate.csv`, `data/ricerca_esterna/`; aggiungere in docs/DATI.md la scheda di `data/ricerca_esterna/` e del registro correzioni; nel DIARIO Fase 100 sostituire «cartella isolata (cantiere/)» con il puntatore a `docs/audit_5_leghe/00_indice.md`.

**🟠 `F11-10-fase96-vs-97` — Il DIARIO cita due volte `scripts/_run_fase96_relegation_market.py`, che non esiste: il file e' `_run_fase97_relegation_market.py`**  
*incoerenza-doc · media · *non contro-verificato**

- **Dove**: docs/DIARIO.md:10435 e docs/DIARIO.md:10554
- **Atteso**: `scripts/_run_fase97_relegation_market.py`, come scrivono correttamente README.md:254 e docs/DATI.md:305.
- **Trovato**: Entrambe le citazioni sono dentro la sezione `## Fase 97` (che inizia a riga 10375) e usano il numero 96. La riga 10554 e' il blocco «6) Riproducibilita'», cioe' proprio il comando che un terzo dovrebbe rieseguire: `python scripts/_run_fase96_relegation_market.py` fallisce con file-not-found.
- **Come è stato accertato**: `grep -n '^## Fase ' docs/DIARIO.md` -> Fase 96 a 10278, Fase 97 a 10375, Fase 98 dopo 10554. `ls scripts/ | grep relegation` -> solo `_run_fase97_relegation_market.py`, il cui docstring inizia con «Fase 97 — La nostra RETROCESSIONE contro un prezzo di mercato vero (Smarkets)» e la cui riga 31 documenta `python scripts/_run_fase97_relegation_market.py`. Checker dei riferimenti `scripts/*.py` su tutti i .md: solo 3 nomi mancanti in tutto il progetto, questo e' uno.
- **Correzione**: Correggere `_run_fase96_` -> `_run_fase97_` alle righe 10435 e 10554 di docs/DIARIO.md.

**🟠 `F11-11-caccia-calendari-mai-estratti` — `caccia_calendari.py` e `wiki.py` sono rimasti incollati dentro un report: l'estrazione richiesta esplicitamente non e' mai stata fatta**  
*incompiuto · media · *non contro-verificato**

- **Dove**: docs/audit_5_leghe/numeri/caccia_calendari.md:468-478 (nota «Dove vivono gli script» + Appendice A)
- **Atteso**: Due file sorgente in `scripts/` (`caccia_calendari.py`, `wiki.py`, piu' `scrivi_md.py` non riportato), come il report stesso chiede a chi integra il lavoro.
- **Trovato**: Il report dice: «Chi integra il lavoro li estragga in `cantiere/scripts/caccia_calendari.py` e `cantiere/scripts/wiki.py`». Il commit di integrazione non lo ha fatto, e ora la destinazione indicata non esiste nemmeno. I due moduli hanno prodotto le 3.045 righe di calendario coppe oggi in `data/ricerca_esterna/fixtures_*.csv`: il sorgente sopravvive solo come testo dentro un .md, quindi il dato NON e' rigenerabile senza copia-e-incolla manuale. `scrivi_md.py` non e' riportato nemmeno nel report.
- **Come è stato accertato**: Lettura di docs/audit_5_leghe/numeri/caccia_calendari.md:468-480; `ls scripts/ | grep -E 'caccia_calendari|^wiki'` -> nulla; `git log --all --name-only --pretty=format: | grep -E 'caccia_calendari\.py|/wiki\.py'` -> nessun risultato in TUTTA la storia del repo (non sono mai stati file).
- **Correzione**: Estrarre le due appendici in `scripts/caccia_calendari.py` e `scripts/wiki.py` (il report dichiara che usano solo percorsi assoluti + sys.path verso la radice, quindi vanno adattati come gli altri), aggiornare la nota del report al percorso reale, e dichiarare che `scrivi_md.py` e' perduto (e' solo impaginazione).

**🟡 `F11-12-24-vs-32` — Il commit di integrazione dichiara «24 script», ma ne ha spostati 32; l'indice ne descrive 16**  
*numero-errato · bassa · *non contro-verificato**

- **Dove**: git 6c9b377 (corpo: «cantiere/scripts/*.py -> scripts/ (24 script: gli audit, le leve, le stime, i tracer)»), docs/audit_5_leghe/00_indice.md:86-99
- **Atteso**: 32.
- **Trovato**: 32 file .py rinominati da `cantiere/scripts/` a `scripts/`. Il numero 24 e' stato poi ripreso a valle come dato acquisito. Il blocco «Contenuto» dell'indice, che dovrebbe descriverli, ne elenca 16 (mancano tutti i `leve_*`, i `nuovo_*`, `stima_celle_residue`, `stima_ou_close_nuove`, `stima_ou_open_bakeoff`, `stima_sot_understat`, `cerca_segnaposto`, `ggng_contro_quote`).
- **Come è stato accertato**: `git show --numstat -M 6c9b377 | grep -oP 'scripts\}/\K\S+\.py' | sort | wc -l` -> 32; tutti e 32 verificati presenti oggi in scripts/ (loop di `[ -f scripts/$f ]`, 0 mancanti). `git ls-tree -r --name-only 46bf0fc | grep '^cantiere/scripts/' | wc -l` -> 32. Conteggio a mano dei nomi elencati in 00_indice.md:86-99 -> 16.
- **Correzione**: Correggere il numero dove viene ripreso e completare l'elenco dell'indice (o sostituirlo con un rimando: 32 script, prefissi `audit_*`, `leve_*`, `nuovo_*`, `stima_*`, `tranche3_*`).

**🟡 `F11-13-stime-ou-corrotte-fantasma` — Tre documenti puntano a `data/stime_ou_corrotte.csv`, file che non esiste piu'**  
*incoerenza-doc · bassa · *non contro-verificato**

- **Dove**: docs/audit_5_leghe/07_dati_corrotti.md:128 (link), docs/audit_5_leghe/08_buchi.md:62, docs/audit_5_leghe/REGOLE.md:183, docs/audit_5_leghe/00_indice.md:98
- **Atteso**: `data/estimates/ou_open_corrotte_2017_19.csv` (la versione del bakeoff, MAE 0.0143), con la nota che la stima storica a MAE 0.0267 e' stata soppressa.
- **Trovato**: `cantiere/data/stime_ou_corrotte.csv` (9 righe) e' stato cancellato dal commit come superato, ma i riferimenti documentali sono rimasti. Nel report 07 e' un link markdown, quindi rotto; negli altri e' una citazione di percorso.
- **Come è stato accertato**: `grep -rn 'stime_ou_corrotte' docs/ scripts/ data/`; `ls data/estimates/` -> `celle_residue.csv, open_sparse_1x2_ou.csv, ou_close_2017_19.csv, ou_open_corrotte_2017_19.csv, squad_value_2017_26.csv, README.md`. `head data/estimates/ou_open_corrotte_2017_19.csv` mostra le colonne `p_over25_open_est_M1_precedente` e `mae_*`, cioe' contiene anche la stima vecchia come colonna di confronto: nessun dato perso, solo il file.
- **Correzione**: Riscrivere i 4 riferimenti verso `data/estimates/ou_open_corrotte_2017_19.csv`, precisando che la colonna `p_over25_open_est_M1_precedente` conserva la stima storica.

**🟡 `F11-14-scratchpad-hardcoded` — Tre script hanno la cartella di cache incisa su uno scratchpad di sessione altrui, senza override da variabile d'ambiente**  
*bug-codice · bassa · *non contro-verificato**

- **Dove**: scripts/leve_apertura.py:119-120, scripts/leve_phi_griglia.py:73-74, scripts/nuovo_fronte_generale.py:98-99
- **Atteso**: Lo stesso schema usato dagli altri 7 script della famiglia: `Path(os.environ.get("SCRATCH", <default>))`.
- **Trovato**: `SCRATCH = Path("/tmp/claude-0/-home-user-Polymarket-oracle/a5fc6f34-4b89-5526-a47c-c72cff4ac735/scratchpad")` — l'UUID e' quello della sessione che scrisse lo script. In un'altra sessione la cartella non esiste; poiche' viene creata con `mkdir(parents=True, exist_ok=True)`, la cache riparte silenziosamente da vuota (nessun errore, solo ore di ricalcolo). Non e' una perdita di dati, ma rende non deterministico il costo di un rerun.
- **Come è stato accertato**: `grep -rn 'tmp/claude-0' scripts/*.py` -> 10 script; con `grep -B2` si vede che leve_beat_close, leve_devig_shin, leve_theta_griglia, nuovo_calibrazione, leve_ricalibrazioni usano `os.environ.get("SCRATCH", …)`, ggng_contro_quote usa `GGNG_SCRATCH`, stima_sot_understat usa `SOT_CACHE`; i tre elencati no.
- **Correzione**: Uniformare al pattern `Path(os.environ.get("SCRATCH", tempfile.gettempdir() + "/..."))`.

**🟡 `F11-15-registra-dead-code` — `nuove_leghe.registra()` doveva sparire all'integrazione: e' rimasto ed e' oggi un no-op chiamato da 15 script**  
*incompiuto · bassa · *non contro-verificato**

- **Dove**: scripts/nuove_leghe.py:192-214 (docstring alla riga 197: «All'integrazione, questa funzione sparisce e le voci vivono in sources.py»); chiamanti: scripts/tranche3_ritaratura.py:38, tranche3_tracer.py:42, nuovo_fronte_generale.py:95 e altri 12
- **Atteso**: Funzione rimossa e chiamate eliminate, visto che Bundesliga e Ligue 1 sono ora in `src/data/sources.py` e `src/config.py`.
- **Trovato**: La funzione c'e' ancora. Verificata innocua (usa `setdefault` ovunque e la validazione degli alias non trova conflitti), ma resta impalcatura morta su cui gli script continuano a dipendere — e il ciclo sugli alias alle righe 209-214 NON usa setdefault: se un giorno un alias di produzione divergesse da quello di nuove_leghe.py, tutti e 15 gli script morirebbero con ValueError.
- **Come è stato accertato**: Test eseguito: import di `nuove_leghe`, snapshot di `sources.TEAM_ALIASES` prima/dopo `registra()` -> «registra() OK», «alias aggiunti/cambiati: 0», `LEAGUES` gia' con tutte e 5 le chiavi prima della chiamata. `grep -n 'bundesliga' src/config.py src/data/sources.py` -> presenti (config.py:94, sources.py:73,405,507,533,541,590,594,599).
- **Correzione**: Rimuovere `registra()` e le sue 15 chiamate; se si vuole tenere il modulo per gli URL openfootball, lasciare solo `openfootball_url()` e le costanti.

**🟡 `F11-16-nessun-test-nessuna-citazione` — 32 script entrano in scripts/ tutti rotti senza che nulla se ne accorga: zero copertura di test e 16 su 32 mai nominati in un documento**  
*omissione · bassa · *non contro-verificato**

- **Dove**: tests/ (nessun test tocca i 32 script), docs/audit_5_leghe/10_modelli_nuove_leghe.md:967
- **Atteso**: Almeno uno smoke test che importi o esegua `--help` su ogni script di scripts/ (avrebbe intercettato F11-01 in un secondo); e ogni artefatto numerico citato dovrebbe nominare lo script che lo produce (§1.5 riproducibilita').
- **Trovato**: `pytest` passa 194 test su 194 con tutti e 32 gli script rotti. E 16 dei 32 non compaiono in nessun .md del progetto: cerca_segnaposto, leve_apertura, leve_beat_close, leve_dc_panchina, leve_devig_shin, leve_phi_griglia, leve_ricalibrazioni, leve_theta_griglia, nuovo_calibrazione, nuovo_fronte_generale, nuovo_mercato_campione, stima_celle_residue, stima_ou_close_nuove, stima_ou_open_bakeoff (+ leve_apertura). Il report 10, che espone i loro risultati, rimanda ai «loro output grezzi (`cantiere/out/leve_*.json`)» — percorso oggi inesistente — e nomina un solo .py in tutto il documento.
- **Come è stato accertato**: `python3 -m pytest -q` -> «194 passed in 53.57s» a fronte delle 25 rotture di F11-01/F11-02. Script di conteggio delle citazioni: per ognuno dei 32 nomi, occorrenze in docs/**/*.md + README.md + CLAUDE.md + lavoro_aperto.md + newseason.md -> 16 con cit=0. `grep -n 'cantiere/out/leve' docs/audit_5_leghe/10_modelli_nuove_leghe.md` -> riga 967.
- **Correzione**: Aggiungere `tests/test_scripts_smoke.py` che fa `runpy`/`--help` (o almeno un `ast.parse` + verifica che ROOT risolva alla radice) su ogni .py di scripts/; e nel report 10 sostituire `cantiere/out/leve_*.json` con `docs/audit_5_leghe/numeri/leve_*.json`, nominando lo script accanto a ogni tabella.

**🟡 `F11-17-indice-numeri-stantii` — L'indice dell'audit riporta ancora «pytest resta verde (153 test)» e «nessun file esistente del progetto e' stato modificato»**  
*incoerenza-doc · bassa · *non contro-verificato**

- **Dove**: docs/audit_5_leghe/00_indice.md:127-135 (sezione «Regole rispettate»)
- **Atteso**: Il numero corrente (194) o nessun numero; e la nota di isolamento va storicizzata, perche' dopo l'integrazione src/, data/, docs/, scripts/ e tests/ SONO stati modificati.
- **Trovato**: Il file dice «pytest resta verde (153 test)» mentre il commit stesso di integrazione chiude con «pytest 194 verdi» e oggi il conteggio e' 194; e afferma «nessun file esistente del progetto e' stato modificato (ne' src/, ne' data/, ne' docs/, ne' scripts/, ne' tests/)», vero nell'epoca del cantiere, fuorviante ora che il file vive dentro docs/.
- **Come è stato accertato**: Lettura di docs/audit_5_leghe/00_indice.md:127-135; `python3 -m pytest -q` -> 194 passed; `git show --stat 03d5bec ec85314 327aa55 46bf0fc` mostra modifiche a src/, data/, docs/, scripts/, tests/.
- **Correzione**: Datare la sezione («al momento della chiusura del cantiere: 153 test; oggi 194») o rimuoverla, dato che la premessa di isolamento e' decaduta.

**🟡 `F11-18-caccia-understat-md` — Manca `caccia_understat.md` fra gli artefatti: e' l'unica delle quattro «cacce» senza la sua lettura per un umano**  
*omissione · bassa · *non contro-verificato**

- **Dove**: docs/audit_5_leghe/numeri/ (presenti caccia_calendari.{json,md}, caccia_ou_dataset.{json,md}, caccia_quote_singole.{json,md}, caccia_understat.json soltanto); scripts/cerca_segnaposto.py:67-68,685,845
- **Atteso**: `docs/audit_5_leghe/numeri/caccia_understat.md`, come per le altre tre cacce.
- **Trovato**: Lo script lo produce davvero (riga 685: `(OUT / "caccia_understat.md").write_text(...)`) e lo dichiara nel docstring, ma il file non e' mai stato committato nemmeno in `cantiere/out/`: non e' stato perso nell'integrazione, non e' proprio mai entrato. I numeri restano nel .json, quindi la perdita e' solo di leggibilita'.
- **Come è stato accertato**: `ls docs/audit_5_leghe/numeri/ | grep caccia` -> 3 coppie + `caccia_understat.json` solo. `git ls-tree -r --name-only 46bf0fc | grep '^cantiere/out/'` (50 file) -> `caccia_understat.json` presente, nessun `caccia_understat.md`. `grep -n 'caccia_understat' scripts/cerca_segnaposto.py` -> righe 67,68,685,782,843,845.
- **Correzione**: Dopo il fix di F11-01/F11-02, rieseguire `python scripts/cerca_segnaposto.py --offline` e versionare l'.md accanto agli altri; oppure togliere l'.md dal docstring se lo si considera superfluo.

**🟡 `F11-19-sklearn-assente` — `stima_ou_open_bakeoff.py` non e' verificabile in questo ambiente: richiede scikit-learn, dichiarato in pyproject.toml ma non installato**  
*non-verificabile · bassa · *non contro-verificato**

- **Dove**: scripts/stima_ou_open_bakeoff.py:79-81; pyproject.toml:19
- **Atteso**: Nessun difetto imputabile al repo: la dipendenza e' dichiarata correttamente.
- **Trovato**: `python3 scripts/stima_ou_open_bakeoff.py --help` muore su `ModuleNotFoundError: No module named 'sklearn'` PRIMA di arrivare ai suoi percorsi cantiere. E' l'unico dei 32 la cui rottura non ho potuto attribuire per esecuzione a F11-01/F11-02; l'analisi statica pero' mostra che ha ROOT hard-coded corretto e 7 join funzionali verso cantiere (righe 99-103, 864), quindi fallirebbe comunque a runtime.
- **Come è stato accertato**: Esecuzione `--help` (traceback su sklearn); `grep -n sklearn scripts/stima_ou_open_bakeoff.py` -> righe 79-81 (HistGradientBoostingRegressor, IsotonicRegression, KFold, import a livello di modulo); `grep -n 'scikit' pyproject.toml` -> riga 19 `"scikit-learn>=1.3"`.
- **Correzione**: Nessuna correzione al repo. Per chiudere la verifica basta `pip install scikit-learn` e rieseguire dopo il fix dei percorsi.

<details><summary>Verifiche con esito OK su questo fronte</summary>

- INVENTARIO COMPLETO dei riferimenti a «cantiere»: 66 file nel repo (esclusa .git). Distinti con precisione: 31/32 script mossi hanno path-join FUNZIONALI (si rompono), 1 solo ha menzione nel docstring (scripts/nuove_leghe.py:4, innocua); in data/ricerca_esterna/ 2 su 4 sono funzionali (_valida_footiqo.py, _confuta_footiqo.py) e 1 e' docstring-only innocuo (_fetch_footiqo.py:13, che scrive correttamente in `Path(__file__).parent`); i restanti sono documentazione (19 occorrenze in 00_indice.md, 6 in 01_audit_dati.md, ecc.) e metadati di provenienza dentro i JSON di numeri/.
- TUTTI E 32 gli script dichiarati dal commit 6c9b377 sono davvero arrivati in scripts/: loop `[ -f scripts/$f ]` su tutti i nomi estratti dal numstat -> 0 mancanti. Nessuna collisione di nome: `git cat-file -e 46bf0fc:scripts/<nome>` fallisce per tutti e 32, quindi nessuno ha sovrascritto uno script preesistente.
- CONTABILITA' COMPLETA dei 329 file di cantiere/ al commit padre 46bf0fc: 173 rinominati (tutte le 173 destinazioni ESISTONO oggi su disco, verificato con os.path.exists) + 156 cancellati puri. Dei 156: 140 sono le fonti grezze sotto cantiere/data/fonti/, 8 sono log di run, 5 sono i tracer_pred (vedi F11-05), 2 sono stime superate dichiarate nel commit, 1 e' cantiere/.gitignore. Nessun report, nessuno script, nessun JSON di out/ e' andato perduto.
- I 37 artefatti di cantiere/out/ (json+md) sono tutti in docs/audit_5_leghe/numeri/ (37 file presenti, 37 rinomine nel commit) e sono tutti JSON VALIDI (json.load su 34/34 .json: nessun errore). Gli 11 report + REGOLE.md + patch_guard_overround_APPLICATA.md + 00_indice.md (ex cantiere/README.md) sono tutti presenti in docs/audit_5_leghe/.
- data/ricerca_esterna/ ha ricevuto tutti gli 86 file di cantiere/data/ricerca/ (86 rinomine nel commit = 86 file presenti). data/correzioni_dichiarate.csv, data/estimates/celle_residue.csv, data/estimates/ou_open_corrotte_2017_19.csv, data/football_data_raw/ (10 file + README), data/outright_snapshots/ (2 snapshot + history.csv + README) esistono tutti.
- IL MANIFEST ESISTE davvero (data/ricerca_esterna/manifest_fonti_audit.json, ex cantiere/data/fonti/manifest.json, 90 voci, 0 senza sha256) — ma copre solo 36 dei 140 file cancellati; l'incompletezza e' riportata come F11-06, l'esistenza e' verificata.
- LA SUPERSESSIONE DICHIARATA NEL COMMIT E' VERA: data/estimates/ou_close_2017_19.csv ha 3.638 righe su 5 leghe (bundesliga 604, la_liga 756, ligue_1 758, premier_league 760, serie_a 760) e 604+758 = 1.362 = esattamente le righe del ou_close_2017_19_nuove_leghe.csv soppresso (1363 linee nel numstat, header incluso). Nessun dato perso in quella cancellazione.
- LE 27 CORREZIONI DICHIARATE SONO EFFETTIVAMENTE APPLICATE agli snapshot di produzione: rieseguito a mano il controllo di applica_correzioni.py contro data/bundesliga_matches.csv e data/ligue_1_matches.csv -> 27 celle al valore_dopo, 0 problemi, 0 chiavi ambigue. Il registro (31 righe: 27 applicate, 2 proposte, 2 ritirate) copre solo bundesliga e ligue_1, coerente con il dict SNAPSHOTS dello script. Lo script ha guardie R3 corrette (idempotenza + verifica del valore-prima + arresto senza scrivere).
- NESSUN RIFERIMENTO MORTO A FILE DI DATI oltre a quelli segnalati: scansione di tutti i literal `"(data|docs|experiments|src|tests|files)/..."` in tutti i 159 .py di scripts/ -> 0 percorsi inesistenti. Le uniche rotture di dati sono via prefisso cantiere/ (F11-02) o via file cancellati (F11-04).
- RIFERIMENTI A SCRIPT NELLA DOCUMENTAZIONE: checker su tutti i .md di docs/ + README.md + CLAUDE.md + lavoro_aperto.md + newseason.md -> su ~130 nomi di script citati, solo 3 non esistono (_run_fase96_relegation_market.py = refuso, F11-10; caccia_calendari.py e wiki.py = mai estratti, F11-11). Tutti gli altri esistono con quel nome esatto.
- `nuove_leghe.registra()` e' oggi un no-op sicuro: test eseguito con import reale -> nessuna eccezione, 0 alias aggiunti o modificati, src.data.sources.LEAGUES gia' completo con tutte e 5 le leghe prima della chiamata. Nessun conflitto fra la config provvisoria del cantiere e quella di produzione.
- pytest: 194 passed in 53.57s, come dichiarato dal commit 6c9b377. scripts/__pycache__/ non e' tracciato da git (coperto da .gitignore).

</details>

### Integrità dei dati  ·  14 rilievi
**🔴 `F12-06-script-root-parents2` — 27 script spostati da cantiere/scripts/ a scripts/ calcolano ROOT = parents[2]: puntano fuori dal repo e sono tutti inservibili**  
*bug-codice · alta · *non contro-verificato**

- **Dove**: scripts/applica_correzioni.py:27-32; scripts/audit_snapshots.py:36,41-51,80; scripts/audit_anomalie.py:53,61-66; scripts/build_new_snapshot.py:37,43-44; scripts/stima_celle_residue.py; scripts/stima_ou_corrotte.py; scripts/verifica_stime.py; +20 altri
- **Atteso**: ROOT = Path(__file__).resolve().parents[1] (come i 122 script gia' in scripts/) e percorsi data/, docs/audit_5_leghe/numeri/ al posto di cantiere/data/, cantiere/out/
- **Trovato**: ROOT = Path(__file__).resolve().parents[2] -> /home/user (fuori dal repo); poi DATA = ROOT/'cantiere'/'data', OUT = ROOT/'cantiere'/'out', sys.path.insert(0, ROOT) e sys.path.insert(0, ROOT/'cantiere'/'scripts')
- **Come è stato accertato**: grep -l 'parents\[2\]' scripts/*.py -> 27 file (contro 122 con parents[1]). Esecuzione: `python3 scripts/applica_correzioni.py --dry-run` -> FileNotFoundError su /home/user/cantiere/data/correzioni_dichiarate.csv; `python3 scripts/verifica_stime.py --help`, `scripts/stima_celle_residue.py --help`, `scripts/riconcilia_nomi.py --help` -> ModuleNotFoundError: No module named 'src' (perche' sys.path riceve /home/user). Path.resolve().parents[2] di /home/user/Polymarket-oracle/scripts/x.py = /home/user, verificato programmaticamente; /home/user/cantiere non esiste.
- **Correzione**: In tutti e 27: parents[2] -> parents[1] e sostituire i prefissi cantiere/data -> data, cantiere/data/ricerca -> data/ricerca_esterna, cantiere/data/stime -> data/estimates, cantiere/out -> docs/audit_5_leghe/numeri, cantiere/scripts -> scripts. Priorita' ad applica_correzioni.py (e' lo script idempotente richiesto da R3), audit_snapshots.py e audit_anomalie.py (sono la riproducibilita' dei numeri dell'audit).

**🟠 `F12-01-denominatore-15788` — Il denominatore dell'audit e' 15.788 ma le partite delle 5 leghe sono 16.111 (e l'universo Understat e' 16.110)**  
*numero-errato · media · *non contro-verificato**

- **Dove**: README.md:257; docs/DIARIO.md:11003; docs/DIARIO.md:11110; docs/audit_5_leghe/01_audit_dati.md:65,125,153,161,260,280; docs/audit_5_leghe/08_buchi.md:95; docs/audit_5_leghe/patch_guard_overround_APPLICATA.md:61; scripts/audit_anomalie.py:305
- **Atteso**: «0 differenze (16.111 partite)» per i controlli B1-B4 e «gol confermati da fonte indipendente su 16.110/16.110 confrontabili (1 partita senza corrispondenza Understat)»
- **Trovato**: «B1 stesse partite ... 0 differenze (15.788 partite)» e «gol confermati da fonte indipendente su 15.787/15.788», ripetuto in 12 punti; nella STESSA cella del README convive con «5 leghe in produzione (16.111 partite)»
- **Come è stato accertato**: pandas su data/*_matches.csv: 3420+3420+3420+2754+3097 = 16.111. Gli artefatti dell'audit stesso lo confermano: docs/audit_5_leghe/numeri/audit_*.json riportano n_rows 3420/3420/3420/2754/3097 (somma 16.111) e i messaggi B1 dicono «(su 3420)», «(su 2754)», «(su 3097)». La C1 registra un solo unmatched (ligue_1 2526 Nantes-Toulouse), quindi l'universo Understat e' 16.110 — ed e' esattamente il numero che usa il codice: src/data/understat.py:164 «su 16.110 partite delle 5 leghe accende una sola riga» e docs/DATI.md:200,205. Verificato inoltre che gli snapshot del cantiere al primo commit d'audit (git show d19ec89:cantiere/data/{bundesliga,ligue_1}_matches.csv | wc -l = 2755/3098 righe con header) avevano gia' 2754/3097 righe: 15.788 non corrisponde a nessuno stato passato dei dati.
- **Correzione**: Sostituire 15.788 -> 16.111 (universo snapshot) e 15.787/15.788 -> 16.110/16.110 confrontabili + 1 senza corrispondenza, nei 12 punti elencati; allineare il commento in scripts/audit_anomalie.py:305.

**🟠 `F12-02-censimento-buchi-7353` — docs/DATI.md §1-bis: il censimento dei buchi e' pre-guard (7.353 invece di 7.359) e la tabella di dettaglio somma 47 celle invece di 55**  
*numero-errato · media · *non contro-verificato**

- **Dove**: docs/DATI.md:55-58,63,66,67
- **Atteso**: 7.359 celle vuote su 612.218 (1,20%); tolto il buco O/U-chiusura restano 55 celle; voci: 22 celle (11 linee O/U apertura svuotate) + 2 (Bayern-Hoffenheim) + 6 (2 terne 1X2) + 7 (Torino-Fiorentina 5 + Verona-Genoa 2) + 16 (xG/stile, 8 colonne x 2 partite) + 2 (home_sot/away_sot di Union Berlin-Bochum)
- **Trovato**: «7.353 celle vuote su 612.218»; tabella con «5 celle quota | Torino-Fiorentina, Verona-Genoa», «12 celle xG/stile | 2 partite», nessuna voce per i 2 tiri-in-porta mancanti. Somma delle voci = 22+2+6+5+12 = 47
- **Come è stato accertato**: Conteggio diretto su data/*_matches.csv: NaN totali 7.359 su 612.218 celle (16.111x38); odds_over25+odds_under25 = 7.304 (99,25%), resto = 55. Dettaglio per colonna: over/under25_open 14+14, odds_home/draw/away 2+2+2, odds_*_open 1+1+1, xg/npxg/ppda/deep 2 per ciascuna delle 8 colonne = 16, home_sot/away_sot 1+1. La differenza 7.359-7.353 = 6 e' esattamente il numero di celle La Liga svuotate dal guard nel commit 03d5bec (verificato col diff cella-per-cella contro git show 03d5bec^:data/la_liga_matches.csv); e 55-6 = 49, cioe' il «49 celle» dichiarato in docs/audit_5_leghe/00_indice.md:57. La tabella e' quindi mista: la riga «11 linee» e' post-guard, il totale e i sotto-conteggi sono pre-guard e per giunta sbagliati (5 invece di 7, 12 invece di 16).
- **Correzione**: Ricalcolare il censimento post-guard: 7.359 / 55 residue; correggere «5 celle quota» -> 7, «12 celle xG/stile» -> 16, aggiungere la riga «2 celle tiri in porta | Union Berlin-Bochum 14/12/2024 | statistiche assenti alla fonte».

**🟠 `F12-03-estimates-readme-stale` — data/estimates/README.md descrive ancora la stima O/U a 3 leghe / 7.978 partite / MAE 0.012, mentre docs/DATI.md la descrive a 5 leghe / 12.457 partite / MAE 0.014**  
*incoerenza-doc · media · *non contro-verificato**

- **Dove**: data/estimates/README.md:29,38,43 vs docs/DATI.md:230
- **Atteso**: «In quelle 2 stagioni (tutte e 5 le leghe)», «fittata pooled su 12.457 partite 2019-20+», «MAE ~0.014 nel regime d'uso (~0.012 in interpolazione)» — coerente con DATI.md e con la riga 100 del README di progetto («l'errore del REGIME D'USO (0.014, non 0.012)»)
- **Trovato**: «In quelle 2 stagioni (Serie A, Premier League, La Liga)», «fittata pooled su 7.978 partite 2019-20+», «| MAE vs chiusura vera (prob.) | ~0.012 |»
- **Come è stato accertato**: Il file stimato copre 5 leghe: pandas su data/estimates/ou_close_2017_19.csv -> 3.638 righe, league.value_counts() = serie_a 760, premier_league 760, ligue_1 758, la_liga 756, bundesliga 604. Il fit set corretto e' ri-derivabile: 16.111-3.652 (righe con chiusura O/U) = 12.459, meno Verona-Genoa e Torino-Fiorentina che non hanno l'apertura O/U = 12.457 (il numero di DATI.md:230 e di patch_guard_overround_APPLICATA.md:36). Il 7.978 e' l'universo a 3 leghe: 3x(3420-760)-2 = 7.978. La correzione del MAE (0.012 -> 0.014 nel regime d'uso) e' dichiarata in README.md:257 e docs/DATI.md:230 ma non e' arrivata al README delle stime, che e' il file letto da chi usa i dati.
- **Correzione**: Aggiornare le tre affermazioni in data/estimates/README.md (5 leghe, 12.457 partite di fit, MAE 0.014 nel regime d'uso con 0.012 come interpolazione).

**🟠 `F12-04-laliga-fuori-registro` — Le 6 celle La Liga svuotate dal guard non hanno una riga nel registro delle correzioni, a differenza delle 16 celle identiche di Bundesliga e Ligue 1 (regola R3)**  
*omissione · media · *non contro-verificato**

- **Dove**: data/correzioni_dichiarate.csv (0 righe league=la_liga); data/la_liga_matches.csv righe 450/502/606 (Alaves-Real Madrid 06/10/2018, Eibar-Real Madrid 24/11/2018, Leganes-Betis 10/02/2019)
- **Atteso**: Ogni correzione vive nel registro con cosa/perche'/fonte/chi/quando (CLAUDE.md §5-bis R3); le 6 celle La Liga sono correzioni con lo stesso identico motivo delle 16 registrate per le altre due leghe
- **Trovato**: data/correzioni_dichiarate.csv ha 31 righe, tutte bundesliga (27) o ligue_1 (4); zero righe la_liga, benche' i valori 1.53/1.59, 1.45/1.69, 2.48/1.38 siano stati sostituiti da NaN nel commit 03d5bec
- **Come è stato accertato**: Diff cella-per-cella fra git show 03d5bec^:data/la_liga_matches.csv e data/la_liga_matches.csv (join su season+home_team+away_team): unica differenza = odds_over25_open e odds_under25_open su quelle 3 partite, da valore a NaN. pandas su data/correzioni_dichiarate.csv: reg.league.value_counts() = {bundesliga: 27, ligue_1: 4}; (reg.league=='la_liga').sum() = 0. Le 8 partite gemelle di Bundesliga/Ligue 1 SONO nel registro (16 celle odds_over25_open/odds_under25_open, stato 'applicata').
- **Correzione**: Aggiungere al registro le 6 righe La Liga con lo stesso motivo/fonte delle gemelle e data_decisione dell'integrazione; oppure dichiarare esplicitamente nel registro che le correzioni derivate dal guard di produzione non vi si registrano (e in tal caso togliere le 16 gia' presenti, per non avere due politiche).

**🟠 `F12-05-tre-righe-liga-senza-stima` — Le 3 linee O/U di apertura La Liga svuotate dal guard non hanno stima e non sono censite: il README delle stime dice che le 9 righe stimate sono «l'unico buco di apertura rimasto»**  
*incompiuto · media · *non contro-verificato**

- **Dove**: data/estimates/README.md:128-131; data/estimates/ou_open_corrotte_2017_19.csv (9 righe, 0 la_liga); data/estimates/celle_residue.csv righe 22-25
- **Atteso**: Le aperture O/U mancanti nel 2017-19 sono 12 (3 La Liga + 7 Bundesliga + 2 Ligue 1): o sono tutte stimate, o le non stimate hanno una riga «NON STIMABILE» aggiornata in celle_residue.csv
- **Trovato**: ou_open_corrotte_2017_19.csv copre solo bundesliga (7) e ligue_1 (2); le 3 righe La Liga restano senza apertura, senza stima e con l'unica traccia in celle_residue.csv che le dichiara ancora «FINTO PIENO ... Da svuotare ... oppure estendere il guard» (verdetto ormai eseguito). Il README delle stime afferma «Sono l'unico buco di *apertura* rimasto»
- **Come è stato accertato**: pandas: righe con odds_over25_open NaN = bundesliga 7, la_liga 3, ligue_1 2, serie_a 2 (tot 14); data/estimates/ou_open_corrotte_2017_19.csv league.value_counts() = {bundesliga: 7, ligue_1: 2}; data/estimates/open_sparse_1x2_ou.csv copre le 2 Serie A. Restano scoperte Alaves-Real Madrid 06/10/2018, Eibar-Real Madrid 24/11/2018, Leganes-Betis 10/02/2019. Coerente col fatto che la stima fu prodotta nel cantiere PRIMA che il guard fosse esteso a La Liga (commit 03d5bec).
- **Correzione**: O rigenerare ou_open_corrotte_2017_19.csv includendo le 3 righe La Liga (stesso metodo M5g), o aggiungerle a celle_residue.csv come «non stimabili» con l'errore atteso; in entrambi i casi correggere la frase «l'unico buco di apertura rimasto» e il conteggio «Nove partite (6 Bundesliga, 2 Ligue 1, 1 assente alla fonte)».

**🟠 `F12-07-indice-link-rotti` — Tutti gli 11 link dell'indice dell'audit puntano a docs/audit_5_leghe/report/*.md, cartella che non esiste**  
*import-rotto · media · *non contro-verificato**

- **Dove**: docs/audit_5_leghe/00_indice.md:35-53 (13 occorrenze di «report/»)
- **Atteso**: [`01_audit_dati.md`](01_audit_dati.md) ecc. — i file stanno in docs/audit_5_leghe/ senza sottocartella
- **Trovato**: [`report/01_audit_dati.md`](report/01_audit_dati.md) ... [`report/11_ggng.md`](report/11_ggng.md)
- **Come è stato accertato**: `ls docs/audit_5_leghe/report` -> No such file or directory; i file 01..11 sono direttamente in docs/audit_5_leghe/. grep -c 'report/' docs/audit_5_leghe/00_indice.md = 13. Ironia dell'errore: la tabella subito sopra (righe 14-23) mappa correttamente cantiere/report/*.md -> docs/audit_5_leghe/*.md, ma i link non sono stati riscritti.
- **Correzione**: Rimuovere il prefisso report/ dai 11 link (e dalle 2 occorrenze restanti) in docs/audit_5_leghe/00_indice.md.

**🟠 `F12-08-patch-doc-contraddittoria` — Il documento del guard si chiama ...APPLICATA.md ma il testo dice «Non applicata», e conta 11 celle dove sono 11 righe = 22 celle**  
*incoerenza-doc · media · *non contro-verificato**

- **Dove**: docs/audit_5_leghe/patch_guard_overround_APPLICATA.md:3-4,61,78-83
- **Atteso**: Testo allineato al nome: il guard E' in produzione (src/data/loader.py:99 ORR_MAX = 1.12, usato a loader.py:218); effetto reale = 11 righe / 22 celle (3 La Liga, 6 Bundesliga, 2 Ligue 1); comandi di verifica con i percorsi attuali
- **Trovato**: «**Non applicata**: il lavoro di questa sessione non tocca `src/`. Da valutare all'integrazione»; «**11 celle** su 15.788 partite (0.07%) passano da valore impossibile a NaN dichiarato: 3 La Liga, 6 Bundesliga, 2 Ligue 1»; blocco di verifica che invoca `python cantiere/scripts/audit_anomalie.py` e rimanda a `cantiere/report/01_audit_dati.md`
- **Come è stato accertato**: grep ORR_MAX src/data/loader.py -> definito a riga 99 e applicato a riga 218 (`if orr < 1.0 or orr > ORR_MAX`). Verifica sui dati: 0 righe con overround O/U o 1X2 > 1.12 in tutte e 5 le leghe; nella versione pre-integrazione (git show 03d5bec^:data/la_liga_matches.csv) ce n'erano 3, max 1.2825. Le celle svuotate sono 2 per riga (over + under): 11 righe x 2 = 22 celle, confermato dal registro (16 celle registrate per le 8 righe BL/L1) + le 6 celle La Liga del diff.
- **Correzione**: Riscrivere l'intestazione come «APPLICATA nel commit 03d5bec/ec85314», correggere «11 celle» -> «11 righe (22 celle)», e aggiornare i percorsi cantiere/ dei comandi di verifica.

**🟠 `F12-09-celle-residue-stale` — data/estimates/celle_residue.csv (registro versionato, in produzione) porta verdetti superati e uno logicamente inapplicabile**  
*incoerenza-doc · media · *non contro-verificato**

- **Dove**: data/estimates/celle_residue.csv righe 0-5 (caso A), 22-26 (caso D), colonna note di tutte le righe
- **Atteso**: Un registro allineato allo stato attuale: 3 righe La Liga gia' svuotate, 1 riga (Leganes-Getafe) con verdetto proprio, riferimenti ai percorsi attuali
- **Trovato**: (a) le 3 righe La Liga gia' svuotate portano ancora «Da svuotare come le 8 righe gemelle, oppure estendere il guard con un tetto superiore»; (b) Leganes-Getafe 07/12/2018 ha lo stesso verdetto ma il suo metodo dice «overround 1.0127 (z robusto -11.2)», cioe' un margine SOTTO la mediana: un «tetto superiore» non potra' mai intercettarlo, e infatti la riga e' ancora piena; (c) il caso A dice «USARE IL DATO REALE ... da dichiarare in docs/DATI.md» per 6 celle 1X2 che sono ancora NaN e di cui DATI.md non parla; (d) la colonna note rimanda a `cantiere/out/caccia_quote_singole.json` e `cantiere/data/ricerca/fixtures_*.csv`, percorsi inesistenti (ora docs/audit_5_leghe/numeri/ e data/ricerca_esterna/)
- **Come è stato accertato**: pandas su data/estimates/celle_residue.csv (32 righe, casi A 6 / B 8 / C 8 / D 10). Snapshot: Leganes-Getafe 2018-12-07 ha ancora odds_over25_open 2.89 / odds_under25_open 1.50, overround 1/2.89+1/1.50 = 1.0127 < ORR_MAX 1.12; Dortmund-Hannover 26/01/2019 ha 1.34/2.87, overround 1.0947 < 1.12 (e per questa l'esclusione E' motivata in docs/audit_5_leghe/09_chiusura_buchi.md:598-606). Alaves-Sociedad 14/10/2017 e Bayern-Hannover 04/05/2019 hanno odds_home/draw/away NaN nello snapshot; docs/DATI.md:43,65 le dichiara mancanti senza citare il dato esterno trovato.
- **Correzione**: Rigenerare/aggiornare celle_residue.csv: marcare come CHIUSE le 3 righe La Liga, dare a Leganes-Getafe un verdetto coerente col segno del suo z (margine anomalo per difetto, non intercettabile da un tetto superiore), aggiornare i percorsi nella colonna note, e riportare in docs/DATI.md la decisione presa sulle 6 celle 1X2 del caso A.

**🟠 `F12-10-dati-md-non-catalogo` — docs/DATI.md — dichiarato «catalogo di TUTTI i dati» — non elenca 3 file dati nuovi e 2 stime attive entrate con l'integrazione**  
*omissione · media · *non contro-verificato**

- **Dove**: docs/DATI.md:225-233 (tabella «Stime attualmente pubblicate»); docs/DATI.md §1/§4 (nessuna voce per i file di data/)
- **Atteso**: Voci per data/correzioni_dichiarate.csv (31 righe, registro R3), data/squad_value_2526_transfermarkt.csv (16 celle, fonte secondaria dichiarata R2), data/ricerca_esterna/ (86 file, fra cui i 3.045 fixture di coppa e i JSON footiqo); e righe in tabella per data/estimates/ou_open_corrotte_2017_19.csv (9 stime ATTIVE) e data/estimates/celle_residue.csv
- **Trovato**: La tabella delle stime elenca solo ou_close_2017_19.csv, squad_value_2017_26.csv, open_sparse_1x2_ou.csv; grep in docs/DATI.md di «squad_value_2526_transfermarkt», «correzioni_dichiarate», «ricerca_esterna», «ou_open_corrotte», «celle_residue» -> 0 occorrenze
- **Come è stato accertato**: ls data/estimates/ -> 5 CSV + README (ou_close 3638 righe, ou_open_corrotte 9, open_sparse 2, celle_residue 32, squad_value 0). ls data/ -> correzioni_dichiarate.csv, squad_value_2526_transfermarkt.csv, ricerca_esterna/ (86 file). grep -n su docs/DATI.md non trova nessuno di questi nomi. I file SONO invece mappati in docs/audit_5_leghe/00_indice.md:20-21,96-97, ma CLAUDE.md §4 assegna a DATI.md il ruolo di catalogo unico da aggiornare a ogni modifica dei dati.
- **Correzione**: Aggiungere in docs/DATI.md: due righe nella tabella delle stime (ou_open_corrotte_2017_19.csv con MAE 0.0143 e il suo limite, celle_residue.csv come registro di non-stima) e una sezione sui registri/fonti ausiliarie in data/ (correzioni_dichiarate.csv, squad_value_2526_transfermarkt.csv, ricerca_esterna/).

**🟡 `F12-11-transfermarkt-13-vs-29` — docs/DATI.md continua a dire «13 celle 2025-26 da Transfermarkt diretto»: con le leghe nuove le celle da quella fonte sono 29 (13 + 16)**  
*incoerenza-doc · bassa · *non contro-verificato**

- **Dove**: docs/DATI.md:47,171,176,179,231,243-244; data/squad_value_2526_transfermarkt.csv
- **Atteso**: «13 celle (Fase 70, 3 leghe storiche) + 16 celle (audit 5 leghe: 5 Bundesliga, 11 Ligue 1) da Transfermarkt diretto», con il file citato per nome
- **Trovato**: Tutte le occorrenze parlano solo delle 13 celle della Fase 70; il file data/squad_value_2526_transfermarkt.csv (16 righe: Augsburg, FC Koln, Hamburg, Hoffenheim, St Pauli + 11 Ligue 1, recuperato_il 2026-07-24) non e' mai citato
- **Come è stato accertato**: pandas: data/squad_value_2526_transfermarkt.csv shape (16, 9), groupby league = {bundesliga: 5, ligue_1: 11}; verificato che tutte e 16 sono applicate negli snapshot (confronto valore-per-valore contro home/away_squad_value: 16/16 coincidono). docs/audit_5_leghe/00_indice.md:97 e 04_decisioni.md le dichiarano («16 celle»), docs/DATI.md no.
- **Correzione**: Aggiornare le 6 occorrenze in docs/DATI.md e citare il file, la scala misurata (colonna rapporto_TM_su_playerscores_mediano_lega) e la regola R2.

**🟡 `F12-12-dati-md-tre-leghe` — docs/DATI.md dice ancora «questa tabella vale per tutte e 3 le leghe» e «player-scores (… 3 leghe)» dopo il passaggio a 5**  
*incoerenza-doc · bassa · *non contro-verificato**

- **Dove**: docs/DATI.md:91; docs/DATI.md:169
- **Atteso**: «per tutte e 5 le leghe»; «player-scores (… 5 leghe)» — la semantica quote apertura/chiusura e' verificata identica su tutte e 5 e i valori rosa sono al 100% anche in Bundesliga e Ligue 1
- **Trovato**: «La provenienza cambia con la stagione — questa tabella vale per tutte e 3 le leghe» e «player-scores (valutazioni complete + presenze/rose, 3 leghe)»
- **Come è stato accertato**: Copertura verificata sui dati: odds_over25 (chiusura) NaN esattamente nelle stagioni 1718/1819 di tutte e 5 le leghe (3.652 righe: 760x4 + 612); squad_value senza NaN e costante per (stagione, squadra) in tutte e 5 (0 celle con piu' di un valore). docs/DATI.md:43 stessa sezione dice gia' «su tutte e 5 le leghe».
- **Correzione**: Sostituire «3 leghe» con «5 leghe» nelle due righe.

**🟡 `F12-13-rigenerabilita-stime` — «Ogni file e' rigenerabile con python scripts/build_estimates.py» e' falso per 2 dei 5 file di data/estimates/**  
*incoerenza-doc · bassa · *non contro-verificato**

- **Dove**: data/estimates/README.md:22; scripts/build_estimates.py:73-75,196,201
- **Atteso**: Indicare lo script giusto per ciascun file: build_estimates.py per ou_close/open_sparse/squad_value, scripts/stima_ou_corrotte.py per ou_open_corrotte_2017_19.csv, scripts/stima_celle_residue.py per celle_residue.csv
- **Trovato**: Regola 4: «Ogni file e' rigenerabile con `python scripts/build_estimates.py`». Ma build_estimates.py definisce solo OU_CLOSE_PATH, SQUAD_VALUE_PATH, OPEN_SPARSE_PATH; ou_open_corrotte e celle_residue non vi compaiono, e i due script che li producono sono fra i 27 rotti dal ROOT sbagliato (F12-06)
- **Come è stato accertato**: grep -n 'ESTIMATES_DIR /' scripts/build_estimates.py -> solo ou_close_2017_19.csv, squad_value_2017_26.csv, open_sparse_1x2_ou.csv; nessuna occorrenza di 'corrotte' o 'celle_residue'. scripts/stima_ou_corrotte.py e scripts/stima_celle_residue.py usano ROOT=parents[2] e falliscono all'import (ModuleNotFoundError: No module named 'src').
- **Correzione**: Precisare in data/estimates/README.md quale script rigenera quale file, dopo aver sistemato il ROOT dei due script.

**🟡 `F12-14-udinese-roma-minuti` — La durata del frammento di Udinese-Roma e' «~19 minuti» in un documento e «~18 minuti» nell'altro**  
*incoerenza-doc · bassa · *non contro-verificato**

- **Dove**: docs/audit_5_leghe/01_audit_dati.md:130-136 vs docs/DATI.md:133
- **Atteso**: Un solo numero in entrambi i punti
- **Trovato**: 01_audit_dati.md: «ripresa il 25/04 per gli ultimi ~19 minuti»; docs/DATI.md: «ripresa l'25/04 per gli ultimi ~18 minuti» (con anche l'apostrofo di troppo)
- **Come è stato accertato**: grep sui due file. Nessuno dei due numeri e' ri-derivabile dai dati dello snapshot (il minutaggio non e' una colonna): e' una discordanza di fonte narrativa, non un errore di calcolo.
- **Correzione**: Uniformare a un solo valore e correggere «l'25/04» -> «il 25/04».

<details><summary>Verifiche con esito OK su questo fronte</summary>

- CONTEGGI PER LEGA E PER STAGIONE — tutti veri. pandas su data/*_matches.csv: serie_a 3.420, premier_league 3.420, la_liga 3.420, bundesliga 2.754, ligue_1 3.097; totale 16.111 (= il numero citato in README/CLAUDE.md). Bundesliga 306 in tutte e 9 le stagioni (18 squadre); Ligue 1 380 fino al 2022-23, 306 dal 2023-24 (18 squadre, riforma) e 279 nel 2019-20 (20 squadre, COVID: 28 gare per 18 club e 27 per PSG/Strasburgo) — esattamente come dichiarato in docs/audit_5_leghe/03_nuove_leghe.md:92-97.
- SCHEMA IDENTICO E RIORDINO NON DISTRUTTIVO — verificato. Le 5 leghe hanno le stesse 38 colonne nello stesso ordine (md5 dell'header identico su tutti e 5 i file da 03d5bec in poi; a 03d5bec^ premier e la_liga avevano un ordine diverso). Diff cella-per-cella fra git show 03d5bec^:data/premier_league_matches.csv e il file attuale (join su season+home_team+away_team, confronto numerico con tolleranza 1e-9 e NaN==NaN): stesse chiavi, ZERO colonne divergenti. Per la_liga l'unica differenza sono le 6 celle volute del guard. Il test tests/test_league_snapshots.py sullo schema passa.
- I DUE GUARD SONO IN PRODUZIONE E FANNO EFFETTO. (a) Overround: src/data/loader.py:99 ORR_MAX=1.12 applicato a loader.py:218; sui dati attuali 0 righe con overround >1.12 o <1 su 1X2 e O/U, apertura e chiusura, in tutte e 5 le leghe; le 3 righe La Liga (Alaves-Real Madrid, Eibar-Real Madrid, Leganes-Betis) sono NaN come dichiarato. (b) xG segnaposto: src/data/understat.py:134-176 richiede tutte le firme insieme; Holstein Kiel-Bochum 09/02/2025 ha xg/npxg/ppda/deep a NaN e conserva gol 2-2 e tiri 3/6; Bielefeld-Leverkusen 21/11/2020 conserva correttamente xG 0.00 (correzione RITIRATA, autogol). Entrambi coperti da test (test_overround_impossibilmente_alto_scartato, test_league_snapshots).
- REGISTRO DELLE CORREZIONI FEDELE AGLI SNAPSHOT — 27/27 correzioni con stato 'applicata' sono riflesse cella per cella nei file (confronto programmatico valore_dopo vs valore nello snapshot su chiave season+home_team+away_team: nessuna discrepanza). Union Berlin-Bochum 14/12/2024 e' 1-1 con result 'D' (risultato del CAMPO, regola R1) e i tiri in porta restano NaN (correzione 'proposta', non applicata) — coerente con la motivazione scritta.
- NUMERO DI RIGHE DELLA STIMA O/U DI CHIUSURA RI-DERIVATO ESATTAMENTE. Le partite senza chiusura O/U sono 3.652 (760 x 4 leghe + 612 Bundesliga) — lo stesso 3.652 citato per il dato 1xBet e per il GG/NG. Le stime pubblicate sono 3.638, e le 14 mancanti sono tutte spiegate da input assenti: 12 righe senza apertura O/U (7 BL, 3 Liga, 2 L1) + 2 righe senza chiusura 1X2 (Bayern-Hannover 04/05/2019, Alaves-Sociedad 14/10/2017). Per lega: bundesliga 612-8=604, la_liga 760-4=756, ligue_1 760-2=758, serie_a e premier 760 ciascuna. Il '3.638 righe, 5 leghe' di docs/DATI.md:230 e del README e' corretto.
- NESSUNA STIMA E' FINITA NELLE COLONNE QUOTA DEGLI SNAPSHOT (regola §5). Le celle stimate corrispondono una a una a celle NaN nello snapshot: le 3.652 righe di odds_over25/odds_under25 sono NaN, le 9 righe di ou_open_corrotte hanno odds_over25_open NaN, le 2 di open_sparse pure. Tutti i valori nei file di stima sono probabilita' in (0,1) — ou_close [0.2977, 0.8888], ou_open_corrotte [0.5837, 0.7344], open_sparse [0.2851, 0.5464] — mai quote. squad_value_2017_26.csv e' vuoto (0 righe) e squad_value negli snapshot ha 0 NaN e 0 incoerenze per (stagione, squadra).
- IL CENSIMENTO DEI FALSI ZERO DI midweek_europe REGGE E LO STATO E' QUELLO DICHIARATO. I 1.603 di docs/DATI.md:73 coincidono con la somma per lega di celle_residue.csv (236+251+454+180+482) e con i delta percentuali di docs/audit_5_leghe/09_chiusura_buchi.md §4 (serie_a +3,4pp x 6.840 celle ~= 232, la_liga +6,7pp ~= 458, ligue_1 +7,8pp ~= 483 ecc.). I 3.045 fixture di coppa esistono davvero su disco (50 file in data/ricerca_esterna/fixtures_*.csv, somma 3.045, ripartizione per lega 499/526/677/326/1.017 identica alla tabella). La correzione NON e' stata applicata agli snapshot — i tassi attuali (serie_a 8,6%, premier 13,6%, la_liga 10,2%, bundesliga 12,1%, ligue_1 5,0%) sono esattamente i valori 'prima' — e docs/DATI.md:73-77 lo dichiara esplicitamente («Non ancora corretto ... Dichiarato»).
- QUALITA' DELLE DUE LEGHE NUOVE — nessun valore impossibile. Bundesliga e Ligue 1: 0 gol NaN o negativi, 0 result incoerenti con i gol, 0 quote <= 1 su tutte e 10 le colonne, 0 duplicati (data+squadre) e (stagione+squadre), 0 date fuori dalla finestra di stagione, 0 casi di squadra con due gare lo stesso giorno, file ordinato cronologicamente dentro ogni stagione. Nomi squadra normalizzati: 29 squadre distinte in Bundesliga e 30 in Ligue 1, nessuna coppia quasi-duplicata (similarita' > 0.80). Le statistiche descrittive dichiarate nel report 03 sono ri-derivabili al terzo decimale: gol/gara 3.122 (BL) e 2.742 (L1), esiti 43.7/24.9/31.4 e 43.3/25.3/31.4.
- SUITE DI TEST VERDE SUI DATI — `python -m pytest tests/ -k 'schema or snapshot or leghe or dati or overround or segnaposto'` -> 49 passed. tests/test_league_snapshots.py copre le 5 leghe (conteggi per stagione, xG mancanti attesi 1 per Bundesliga e 1 per Ligue 1, 1X2 mancanti attesi, overround bilaterale con ORR_MAX) e tests/test_estimates.py verifica i massimi per lega (760/760/760/760/612).

</details>

### Lavoro lasciato a metà  ·  18 rilievi
**🔴 `F13-01-script-root-parents2` — 24 dei 27 script spostati da cantiere/scripts a scripts/ non partono più: ROOT = parents[2] punta fuori dalla repo**  
*import-rotto · alta · *non contro-verificato**

- **Dove**: scripts/audit_snapshots.py:31, scripts/audit_anomalie.py:48, scripts/nuove_leghe.py:28, scripts/verifica_stime.py, scripts/tranche3_*.py, scripts/leve_*.py, scripts/stima_*.py, scripts/nuovo_*.py, scripts/build_new_snapshot.py:35, scripts/cerca_segnaposto.py:87, scripts/eda_nuove_leghe.py:26, scripts/riconcilia_nomi.py:28, scripts/recupero_squad_value_tm.py:37 (27 file in tutto)
- **Atteso**: Gli script del lavoro di Fase 100, spostati in scripts/ dall'integrazione 3/3c (docs/audit_5_leghe/00_indice.md dichiara la mappatura `cantiere/scripts/*.py -> scripts/`), devono essere eseguibili come tutti gli altri: `python scripts/<nome>.py`.
- **Trovato**: Quando vivevano in `cantiere/scripts/` la riga `ROOT = Path(__file__).resolve().parents[2]` dava la radice della repo; ora che il file sta in `scripts/` la stessa riga dà `/home/user` (un livello SOPRA la repo). Il successivo `sys.path.insert(0, str(ROOT))` non mette la repo sul path e ogni `from src... import` esplode. 24 script su 27 falliscono all'avvio con `ModuleNotFoundError: No module named 'src'`.
- **Come è stato accertato**: Calcolo statico: script che dichiarano `parents[2]` in scripts/ = 27, tutti risolvono a /home/user invece di /home/user/Polymarket-oracle. Verifica per esecuzione: loop `timeout 20 python scripts/<nome>.py --help` sui 27 → 24 terminano con `ModuleNotFoundError: No module named 'src'` (elenco: audit_anomalie, audit_snapshots, build_new_snapshot, cerca_segnaposto, eda_nuove_leghe, leve_beat_close, leve_dc_panchina, leve_devig_shin, leve_ricalibrazioni, leve_theta_griglia, nuove_leghe, nuovo_calibrazione, nuovo_mercato_campione, recupero_squad_value_tm, riconcilia_nomi, stima_celle_residue, stima_ou_close_nuove, stima_ou_corrotte, stima_sot_understat, tranche3_market_tracer, tranche3_mercati, tranche3_ritaratura, tranche3_tracer, verifica_stime). In più `scripts/audit_snapshots.py:36-37` fa `sys.path.insert(0, ROOT/'cantiere'/'scripts')` + `import nuove_leghe`, cartella che l'integrazione ha cancellato (`find cantiere -type f` → 0 file).
- **Correzione**: In tutti e 27 i file: `ROOT = Path(__file__).resolve().parents[1]`; in audit_snapshots.py togliere l'insert su `cantiere/scripts` (nuove_leghe è già accanto, quindi importabile) e ripuntare `FONTI`/`OUT` (righe 41-42) su percorsi esistenti (es. `docs/audit_5_leghe/numeri/` per l'OUT). Aggiungere un test di smoke che importi ogni script di scripts/ (o almeno che `python scripts/<x>.py --help` esca 0) per impedire che una futura riorganizzazione di cartelle rompa di nuovo tutto in silenzio.

**🔴 `F13-02-R3-script-idempotente-rotto` — Gli script idempotenti richiesti dalla regola R3 puntano a cantiere/data cancellata: le correzioni dichiarate non sono più ri-applicabili**  
*bug-codice · alta · *non contro-verificato**

- **Dove**: scripts/applica_correzioni.py:27-32, scripts/applica_squad_value_tm.py:26-30, docs/audit_5_leghe/REGOLE.md:35
- **Atteso**: La regola R3 (CLAUDE.md §5-bis, e REGOLE.md:35 «si applicano **solo** con `scripts/applica_correzioni.py`») esige che ogni correzione ai dati sia riapplicabile da uno script idempotente che verifica il valore-prima cella per cella. Con il registro in `data/correzioni_dichiarate.csv` (31 righe, 27 `applicata`) e gli snapshot in `data/`, lo script deve girare.
- **Trovato**: Entrambi gli script calcolano `DATA = ROOT / "cantiere" / "data"` con ROOT = parents[2] = /home/user, quindi cercano `/home/user/cantiere/data/...`, che non esiste. Puntano inoltre agli snapshot `cantiere/data/{bundesliga,ligue_1}_matches.csv` invece di `data/{bundesliga,ligue_1}_matches.csv`.
- **Come è stato accertato**: `python scripts/applica_correzioni.py --dry-run` → `FileNotFoundError: [Errno 2] No such file or directory: '/home/user/cantiere/data/correzioni_dichiarate.csv'`; `python scripts/applica_squad_value_tm.py --dry-run` → stesso errore su `/home/user/cantiere/data/squad_value_2526_transfermarkt.csv`. I file veri esistono in `data/correzioni_dichiarate.csv` e `data/squad_value_2526_transfermarkt.csv`.
- **Correzione**: `ROOT = parents[1]`, `DATA = ROOT / "data"`, e SNAPSHOTS su `data/{lega}_matches.csv`. Poi eseguire davvero `--dry-run` sulle 27 righe `applicata` per confermare l'idempotenza (il valore-dopo deve già essere in snapshot e lo script fermarsi senza scrivere), come la R3 promette.

**🔴 `F13-03-audit-registro-correzioni-muto` — audit_snapshots.py perde in SILENZIO il registro delle correzioni: le 27 correzioni volute tornerebbero a essere segnalate come errori**  
*bug-codice · alta · *non contro-verificato**

- **Dove**: scripts/audit_snapshots.py:80-89 e 336-347
- **Atteso**: `_righe_corrette(league)` deve leggere `data/correzioni_dichiarate.csv` ed escludere dal confronto B2 (snapshot vs fonte ri-scaricata) le righe corrette di proposito (regola R1: es. Union Berlin-Bochum 14/12/2024, gol del campo 1-1 invece dello 0-2 del tribunale), emettendo l'INFO `B0.correzioni_dichiarate`.
- **Trovato**: `_CORR_PATH = ROOT / "cantiere" / "data" / "correzioni_dichiarate.csv"` (cartella cancellata dall'integrazione 3/3c). La funzione degrada in silenzio: `if not _CORR_PATH.exists(): return set()`. Con l'insieme vuoto la INFO B0 non viene mai emessa e il controllo B2 confronta anche le righe corrette, cioè l'audit dei dati riporterebbe come DIFFERENZE-DALLA-FONTE proprio le correzioni volute e documentate. È un difetto distinto dal ROOT: sopravvive anche dopo aver corretto parents[2], perché il segmento «cantiere/data» resta sbagliato.
- **Come è stato accertato**: Lettura del codice: riga 80 (percorso) e righe 85-86 (`if not ... .exists(): return set()`, nessun warning). Il file vero c'è: `data/correzioni_dichiarate.csv`, 31 righe, di cui 27 con `stato == 'applicata'` (verificato con pandas). Il messaggio della riga 342 cita ancora il percorso morto: «registro cantiere/data/correzioni_dichiarate.csv».
- **Correzione**: `_CORR_PATH = ROOT / "data" / "correzioni_dichiarate.csv"` e trasformare il ramo «file assente» da `return set()` silenzioso in un FAIL/WARN esplicito del report — un registro delle correzioni introvabile deve essere rumoroso, non trasparente. Aggiornare anche il testo della riga 342.

**🔴 `F13-04-build-database-ignora-league` — build_database.py ignora --league: legge e SOVRASCRIVE sempre lo snapshot Serie A (rischio di distruzione di uno snapshot congelato con --refresh)**  
*bug-codice · alta · *non contro-verificato**

- **Dove**: scripts/build_database.py:62-128 (tutti i rami usano `database.SNAPSHOT_PATH`), src/data/database.py:33 e 48, src/data/loader.py:280-297
- **Atteso**: Con 5 leghe in produzione (CLAUDE.md §7: «aggiungere una lega = aggiungere una voce in LEAGUE_CONFIGS, non toccare il codice») e un argomento `--league` esposto, `python scripts/build_database.py --league <lega>` deve leggere/scrivere `data/<lega>_matches.csv` (esiste già `database.snapshot_path(league_key)`).
- **Trovato**: `--league` è onorato solo dentro `loader.load_league(args.league, ...)` e in `sources.LEAGUES[args.league]`; ogni lettura e ogni scrittura passa da `database.read_snapshot()` / `database.write_snapshot()` che usano il default `SNAPSHOT_PATH = data/serie_a_matches.csv`. Conseguenze: (a) offline, `--league premier_league` costruisce il DB dalla Serie A dichiarando un'altra lega; (b) `--refresh --league bundesliga` scaricherebbe la Bundesliga e la scriverebbe SOPRA `data/serie_a_matches.csv`, cioè sopra uno snapshot congelato versionato. In più `loader.enrich()` (loader.py:280-297) non passa `league_key` a `understat.add_xg` / `transfermarkt.add_squad_values` / `add_absences`, che defaultano tutti a `"serie_a"`, e la guardia `leagues <= set(sources.UNDERSTAT_LEAGUES)` non protegge più nulla ora che UNDERSTAT_LEAGUES contiene tutte e 5 le leghe (sources.py:401-407): un `--refresh` su Premier aggancerebbe l'xG della Serie A dopo aver fatto `drop` delle colonne xG esistenti (understat.py:252).
- **Come è stato accertato**: Esecuzione reale: `python scripts/build_database.py --league premier_league` stampa «Uso lo snapshot congelato: /home/user/Polymarket-oracle/data/serie_a_matches.csv» e «partite: 3420 … impronta: 8483944342fc8b15» (i numeri della Serie A). Lettura del codice per il ramo `--refresh` (righe 62-79): `path = database.write_snapshot(matches)` senza argomento di lega.
- **Correzione**: Calcolare una volta `snap = database.snapshot_path(args.league)` e passarlo a ogni `read_snapshot`/`write_snapshot` del file; propagare `league_key` in `loader.enrich()` (e da lì a add_xg/add_squad_values/add_absences); aggiungere un test che verifichi che con `--league premier_league` il percorso scritto sia `data/premier_league_matches.csv`.

**🟠 `F13-05-PISTE-non-aggiornate-fase100` — docs/PISTE.md non è stato toccato dalla Fase 100: la pista GG/NG e la pista O/U 2017-19 dicono ancora il contrario di quello che il progetto ha misurato**  
*incoerenza-doc · media · *non contro-verificato**

- **Dove**: docs/PISTE.md:407-413 (pista 16), docs/PISTE.md:442-461 (pista 19); confronto con CLAUDE.md:48-59 e docs/CACCIA_OU_2017_19.md:1-45
- **Atteso**: CLAUDE.md §2 impone di aggiornare PISTE.md «quando una pista si apre/prova/chiude». La Fase 100 ha (a) trovato le quote di chiusura GG/NG reali (1xBet via footiqo, 3.652 partite) e misurato che il mercato GG/NG è informativo, (b) trovato il dato vero della chiusura O/U 2017-19 e deciso deliberatamente di NON inserirlo.
- **Trovato**: Pista 16 dice ancora: «**Dato**: NON esiste in nessun archivio (verificato)» e «il GG/NG è l'unico mercato senza tetto di efficienza dimostrato (principio §1.8)» — entrambe smentite: CLAUDE.md:48-52 dichiara la premessa CADUTA e il mercato GG/NG informativo (log-loss 0.6840 vs 0.6921 di baseline, CI conclusivo). Pista 19 non menziona affatto il ritrovamento 1xBet né la decisione di non inserirlo, e chiude invitando a «ri-tentare la Fase A periodicamente»: una sessione futura che legge PISTE riparte esattamente dalla caccia già conclusa, che è il rischio che il fronte doveva escludere. `git log -- docs/PISTE.md` conferma che l'ultimo commit sul file è 81e174b (Fase 99), prima di tutta l'integrazione.
- **Come è stato accertato**: grep -n su docs/PISTE.md (righe 408 e 410 per il testo citato); `git log --oneline -- docs/PISTE.md` → ultimo commit 81e174b «Fase 99…», nessuno dei 5 commit di integrazione (03d5bec…6c9b377); `grep -i 'fase 100|1xbet|footiqo|bundesliga|ligue' docs/PISTE.md` → 0 occorrenze.
- **Correzione**: Riscrivere la pista 16 (il dato ORA esiste per il 2017-19; resta aperta solo la raccolta prospettica sulle stagioni recenti, che il book non quota) e la pista 19 (marcarla CHIUSA con il ritrovamento e, soprattutto, con il MOTIVO del non-inserimento: book singolo contro colonna multi-book, MAE 0.0156 contro ~0.012 della stima, rottura di regime a metà colonna). Aggiungere in PISTE le 6 domande ancora aperte del report 10 §14, che oggi non vivono in nessun registro canonico.

**🟠 `F13-06-CACCIA-fase-D-non-aggiornata` — L'aggiornamento della caccia O/U dichiarato «da fare» non è stato fatto: la Fase D (OddsPortal) è ancora consigliata benché esclusa dal robots.txt**  
*incompiuto · media · *non contro-verificato**

- **Dove**: docs/CACCIA_OU_2017_19.md:77-80, docs/PISTE.md:456-458; richiesta in docs/audit_5_leghe/02_stime.md:170-181; vincolo in docs/MANUALE_SOPRAVVIVENZA.md:21-23
- **Atteso**: Il report 02 §5 elenca esplicitamente gli «Aggiornamenti da fare a docs/CACCIA_OU_2017_19.md», fra cui: «Fase D (OddsPortal): da 'pista con la probabilità più alta di successo' a **pista esclusa dal robots.txt** del sito».
- **Trovato**: Il documento è stato riscritto in testa (banner «CHIUSA: il dato è stato trovato») ma il corpo non è stato toccato: alla riga 77 si legge ancora «**Fase D**: OddsPortal headless con login resta la pista con la probabilità più alta di successo, mai tentata per il costo/rischio — riconsiderarla se emerge un account 'usa e getta' a basso rischio». Lo stesso invito sopravvive in docs/PISTE.md:456-458. Nel frattempo MANUALE_SOPRAVVIVENZA.md:21-23 dichiara che «oddsportal.com **vieta le pagine storiche** nel suo robots.txt (Disallow: *-2017*, *-2018*): non si scrapano, e non si aggira il divieto». Due documenti canonici dicono cose opposte, e quello sbagliato è quello operativo che una sessione futura leggerebbe per decidere cosa fare.
- **Come è stato accertato**: sed su docs/CACCIA_OU_2017_19.md righe 60-85 e su docs/audit_5_leghe/02_stime.md righe 168-181; grep 'OddsPortal' in docs/MANUALE_SOPRAVVIVENZA.md. Collaterale: la stessa sezione parla ancora di «2.280 celle» (3 leghe) mentre la stima pubblicata copre ora 3.638 righe su 5 leghe (`data/estimates/ou_close_2017_19.csv`, 3638 righe verificate).
- **Correzione**: Applicare i 4 punti del report 02 §5 dentro CACCIA_OU_2017_19.md (Fase A ri-confermata negativa per verifica diretta sulla fonte-madre; Fase B negativa perché il sito ha ritirato il dato, non per blocco geo; Fase D ESCLUSA dal robots.txt; rete dell'ambiente cambiata) e allineare la coda della pista 19 di PISTE.md. Aggiornare «2.280 celle» a 3.638/5 leghe.

**🟠 `F13-07-fase92bis-non-documentata` — La Fase 92-bis ha cambiato il codice di produzione ma non esiste in nessun documento: niente voce nel DIARIO, niente riga nel README**  
*omissione · media · *non contro-verificato**

- **Dove**: commit 1ad6c30 «Fase 92-bis — Chiusura dei fix dell'audit»; src/config.py:104-148 (MARKET_ENGINE); scripts/predict.py:124-160; docs/DIARIO.md (nessuna sezione); README.md (nessuna riga)
- **Atteso**: CLAUDE.md §2 impone, per ogni fase significativa: voce nel DIARIO con blocco 📐, riga nel «Registro completo dei risultati» del README, stato in PANCHINA. Le fasi «-bis» del progetto sono documentate (83-bis, 86-bis, 89-bis, 95-bis hanno tutte sezione e riga).
- **Trovato**: Il commit 1ad6c30 introduce `MARKET_ENGINE` per-lega in src/config.py (motore LISCIO per Premier e Liga, con l'impatto misurato: 1X2 Premier 0.9665 col router contro 0.9640 liscio), il consumo in predict.py, un fix a `_SUB_SUFFIXES` di fetch_polymarket_open.py, due guardie sui dati e tre test verificati per mutazione. Nel DIARIO non c'è nessuna sezione «Fase 92-bis» e la sezione «Fase 92» (righe 9723-9877) non nomina mai `MARKET_ENGINE`, `predict.py`, «LISCIO», `value_bet` né `squad_value` (conteggi 0 su tutti). Nel README la tabella passa da `| **92** |` a `| **93** |`. La stringa «92-bis» compare zero volte in tutti i .md del repo.
- **Come è stato accertato**: `git log --oneline -S MARKET_ENGINE -- src/config.py` → 1ad6c30; `git show --stat 1ad6c30`; conteggio per parola chiave sulle righe 9723-9877 del DIARIO (tutti 0); `grep -rn '92-bis' --include='*.md' .` → nessun risultato; estrazione delle etichette della tabella README → 83-bis, 86-bis, 89-bis, 95-bis presenti, 92-bis assente.
- **Correzione**: Aggiungere la sezione «Fase 92-bis» al DIARIO col blocco 📐 (la matematica non cambia: è `price_markets` con θ/φ0/κ presi da `market_engine(lega)` invece che dalle costanti Serie A; motivare i valori per-lega con Fasi 79/81) e la riga corrispondente nella tabella del README.

**🟠 `F13-08-M2-dichiarato-aperto-ma-chiuso` — Il residuo «M2: θ del router per-lega» è dichiarato ancora aperto in tre documenti, ma è stato chiuso dalla Fase 92-bis**  
*incoerenza-doc · media · *non contro-verificato**

- **Dove**: CLAUDE.md:507-508, README.md:237 (riga 83-bis), experiments/prospettico_2026_27.md:36-39 e 72-76; chiuso da src/config.py:124-148 + scripts/predict.py:124-160
- **Atteso**: Chiuso il lavoro, i documenti di stato devono dirlo (CLAUDE.md §2). Il «passo 2» del test prospettico riguardava sia il Modello 1 (chiuso in Fase 83-bis) sia il θ del router nel path market-implied (Modello 2).
- **Trovato**: CLAUDE.md §6 «Prossimi passi» scrive ancora: «resta da rendere per-lega il θ del router nel path market-implied (M2 Premier con θ neutro)». Ma `MARKET_ENGINE` in src/config.py è per-lega dalla Fase 92-bis (Serie A θ=1.225/1.138, φ0=0.30, κ=1.5, sharpen_1x2=True; Premier e Liga tutto None/0/False = motore LISCIO) e `predict.py` lo consuma su entrambi i path (`eng = market_engine(args.league)`, righe 124-126 e 143-145), stampando pure la nota «motore LISCIO per …». Stessa affermazione superata in README.md:237 e in experiments/prospettico_2026_27.md, dove il protocollo del test prospettico istruisce ancora l'operatore a produrre «il M2 Premier con dp_theta neutro» come se fosse un passo manuale.
- **Come è stato accertato**: sed su CLAUDE.md righe 500-515; lettura di src/config.py righe 104-148 e scripts/predict.py righe 118-160; `git log --oneline -S market_engine -- scripts/predict.py` → 1ad6c30.
- **Correzione**: Sostituire il bullet di CLAUDE.md §6 con «chiuso alla Fase 92-bis (MARKET_ENGINE per-lega)», aggiornare la coda della riga 83-bis del README e riscrivere §2/§3 di prospettico_2026_27.md: il tool ora fa da solo la cosa giusta, basta passare `--league`. Nota collaterale: MARKET_ENGINE ha 3 voci su 5 leghe; Bundesliga e Ligue 1 cadono sul fallback LISCIO — che è la scelta giusta (router θ 0/25 mercati) ma andrebbe reso esplicito con due voci e la fase che le motiva, come il commento del file stesso prescrive.

**🟠 `F13-09-tier2-tier3-dichiarati-futuri` — CLAUDE.md dice due cose opposte su Tier 2 e Tier 3 nello stesso file: «in futuro» / «mai coperti» contro «coperti e validati»**  
*incoerenza-doc · media · *non contro-verificato**

- **Dove**: CLAUDE.md:66-67 (§1.8) e CLAUDE.md:514 (§6 Prossimi passi) contro CLAUDE.md:473-477 (§6); docs/audit_5_leghe/10_modelli_nuove_leghe.md:952-953
- **Atteso**: Il protocollo è il documento che una sessione nuova legge per prima: non deve indicare come «da fare in futuro» mercati già coperti e validati.
- **Trovato**: §1.8 chiude con «Tier 2 (handicap asiatico) e Tier 3 (HT/FT, tempi → fondazione live) in futuro» e §6 «Prossimi passi» elenca «mercati non ancora coperti (Tier 2 handicap asiatico, Tier 3 HT/FT e tempi)». Ma lo stesso §6, 40 righe sopra (473-477), racconta che i mercati Tier 3 «battono la baseline con IC conclusivo» (Fase 98: Halftime +0.0537, Second Half +0.0578, risultato esatto +0.1940) e che «il Tier 2 (handicap asiatico) è l'unico mercato del listino validato contro una quota esterna e indipendente: Brier 0.2044 vs 0.2044» (Fase 88). Lo stesso errore è nel report 10 §14 punto 7: «Tier 2 e Tier 3 …: mercati mai coperti, su nessuna lega». La versione corretta è quella di lavoro_aperto.md §5, che marca Tier 2 ✅ coperto e Tier 3 🟡 tre mercati coperti.
- **Come è stato accertato**: grep -n 'Tier 2|Tier 3' CLAUDE.md → righe 63,66,67,70,297,473,477,514; lettura delle due sezioni; docs/audit_5_leghe/10_modelli_nuove_leghe.md riga 952.
- **Correzione**: In §1.8 scrivere «Tier 2 coperto (F88/F98), Tier 3 coperto per Halftime/Second Half/risultato esatto (F98) — mancano HT/FT congiunto e le combinazioni; Tier 3+ (live) scoperto»; in §6 «Prossimi passi» sostituire il bullet con ciò che manca davvero (HT/FT congiunto e il modello a due stadi per il 2T).

**🟠 `F13-10-DATI-catalogo-incompleto` — docs/DATI.md non è stato completato dopo l'import a 5 leghe: mancano 2 calendari di club su 5, l'intera cartella data/ricerca_esterna/ e 2 file di stima su 5**  
*omissione · media · *non contro-verificato**

- **Dove**: docs/DATI.md:145-158 (§3 Calendari di club), docs/DATI.md:226-233 (Stime attualmente pubblicate); file reali: data/club_fixtures_bundesliga.csv, data/club_fixtures_ligue_1.csv, data/ricerca_esterna/ (50 CSV + footiqo + manifest_fonti_audit.json), data/estimates/ou_open_corrotte_2017_19.csv, data/estimates/celle_residue.csv
- **Atteso**: CLAUDE.md §5 (e §4 della mappa) definiscono docs/DATI.md il «catalogo completo di TUTTI i dati (reali e stimati) — da aggiornare a ogni modifica dei dati».
- **Trovato**: (a) La tabella §3 elenca 3 file di calendario (Serie A 11657, Premier 11994, Liga 12102) mentre in data/ ce ne sono 5: mancano `club_fixtures_bundesliga.csv` (10.375 righe) e `club_fixtures_ligue_1.csv` (10.701 righe). (b) `data/ricerca_esterna/` — 50 CSV di calendari di coppa da Wikipedia per 3.045 righe esatte, più i dump footiqo (1xBet) e il `manifest_fonti_audit.json` con gli SHA256 delle fonti — non compare mai in DATI.md: `grep -rn 'ricerca_esterna' --include='*.md'` la trova solo in docs/audit_5_leghe/00_indice.md, cioè nella tabella di traslazione dei percorsi. (c) La tabella «Stime attualmente pubblicate» elenca 3 file mentre in data/estimates/ ce ne sono 5: `ou_open_corrotte_2017_19.csv` (9 righe) e `celle_residue.csv` (32 righe) sono documentati in data/estimates/README.md (§ righe 126 e 145) ma non nel catalogo canonico.
- **Come è stato accertato**: Conteggi eseguiti: `for f in data/club_fixtures*.csv` → 5 file, 11657/10375/12102/10701/11994 righe; `ls data/ricerca_esterna/fixtures_*.csv | wc -l` → 50 e somma righe pandas = 3045 (esattamente il numero dichiarato in docs/audit_5_leghe/09_chiusura_buchi.md:262); `for f in data/estimates/*.csv` → 5 file; grep su docs/DATI.md per «bundesliga|ligue» → nessuna riga nel §3.
- **Correzione**: Aggiungere le due righe di calendario alla tabella §3; aggiungere una voce §4 per `data/ricerca_esterna/` (cosa contiene, provenienza Wikipedia/footiqo, stato «dato esterno reale, NON ancora integrato negli snapshot», rimando al manifest SHA256); aggiungere le due righe mancanti alla tabella delle stime, riportando gli errori attesi già calcolati (MAE 0.0143 per le 9 linee O/U corrotte).

**🟠 `F13-11-celle-residue-caso-A-non-eseguito` — Sei celle con verdetto «USARE IL DATO REALE» non sono state né inserite né dichiarate: la decisione è scritta solo dentro un CSV**  
*incompiuto · media · *non contro-verificato**

- **Dove**: data/estimates/celle_residue.csv righe 1-6 (caso A); data/bundesliga_matches.csv (Bayern Munich-Hannover 2019-05-04) e data/la_liga_matches.csv (Alaves-Sociedad 2017-10-14); docs/DATI.md:65
- **Atteso**: O il dato reale entra nello snapshot (con riga nel registro correzioni, regola R3), o si dichiara perché non entra. Il verdetto stesso della riga lo chiede: «USARE IL DATO REALE (2,8 volte più preciso della stima, CI conclusivo); provider diverso dal resto della colonna: **da dichiarare in docs/DATI.md**».
- **Trovato**: Le 6 celle (le due terne 1X2 di chiusura di Bayern-Hannover e Alaves-Sociedad) hanno `valore_attuale` vuoto e `valore_proposto` valorizzato (1.03/18.43/43.88 e 3.40/3.34/2.15) da una fonte esterna reale (`github.com/iredchuk/soccer-bookmaker-odds`). Negli snapshot restano NaN (verificato). In docs/DATI.md:65 le due partite compaiono ancora nella sola tabella dei buchi («colonne PSC* vuote nel grezzo»), senza traccia del fatto che un dato reale è stato trovato, valutato migliore della stima e raccomandato. La fonte `iredchuk` è nominata solo in docs/audit_5_leghe/numeri/caccia_quote_singole.md, un appunto di lavoro, e non nel DIARIO: la sezione Fase 100 non menziona né il file celle_residue né i suoi verdetti.
- **Come è stato accertato**: pandas su data/estimates/celle_residue.csv (6 righe caso A, tutte con quel verdetto); lettura degli snapshot: Bundesliga riga 586 (2019-05-04 Bayern Munich-Hannover) odds_home/draw/away = NaN, La Liga riga 71 (2017-10-14 Alaves-Sociedad) idem; `grep -rn iredchuk --include='*.md' .` → solo docs/audit_5_leghe/numeri/*.md; scansione della sezione Fase 100 del DIARIO (righe 10949-11135) per «cell|residu|NaN» → nessuna menzione del caso A.
- **Correzione**: Prendere la decisione e scriverla: se si inserisce, farlo via `applica_correzioni.py` (dopo il fix F13-02) con le 6 righe nel registro e la provenienza dichiarata in DATI.md §4 (provider diverso dal resto della colonna); se non si inserisce, aggiungere in DATI.md la riga «dato reale disponibile ma NON inserito, motivo: …», come già fatto in modo esemplare per il 1xBet della caccia O/U.

**🟠 `F13-12-lavoro-aperto-conteggi-stantii` — L'indice del lavoro aperto sottostima di 5,75× le caselle vuote della rosa: dice 24, sono 138 dopo l'ingresso di Bundesliga e Ligue 1**  
*numero-errato · media · *non contro-verificato**

- **Dove**: lavoro_aperto.md:103 (§3), lavoro_aperto.md:54 (§2), CLAUDE.md:296-297; fonte vera: docs/PANCHINA.md, matrice righe 57-103
- **Atteso**: lavoro_aperto.md dichiara «Conteggio verificato il 26/07/2026»; la matrice di PANCHINA è passata da 4 a 6 colonne (3 leghe + generale → 5 leghe + generale) nello stesso giorno, con l'integrazione della Fase 100.
- **Trovato**: §3 titola «docs/PANCHINA.md — **24 caselle ⬜** (mai testato lì)» e ripete «La matrice ha 24 celle ⬜»: il conteggio reale è **138** su 48 righe × 6 colonne. Il numero stantio è stato ricopiato anche nella mappa del repo del protocollo (CLAUDE.md:297: «le 24 caselle vuote della PANCHINA»). Nello stesso file, §2 titola «docs/PISTE.md — 21 voci» mentre la sua stessa tabella ne elenca 23 (e PISTE.md ha 23 voci numerate: 1,2,3,4,4-bis,4-ter,4-quater,5,6,7,7-bis,8,9,10,11,12,13,14,15,16,17,18,19).
- **Come è stato accertato**: Parsing della matrice di docs/PANCHINA.md (riga d'intestazione «| modello | Serie A | …»): 48 righe di dati, 138 occorrenze di ⬜ nelle 6 colonne di stato (il file ne contiene 138 in totale, tutte lì). Parsing della tabella §2 di lavoro_aperto.md: 23 righe-pista.
- **Correzione**: Ricontare e riscrivere le due intestazioni di lavoro_aperto.md (§2 «23 voci», §3 «138 caselle ⬜») e la riga 297 di CLAUDE.md; aggiungere una nota che il salto è dovuto alle due colonne nuove, così il numero non sembra un peggioramento del lavoro fatto.

**🟠 `F13-13-newseason-superato-da-fase100` — newseason.md e lavoro_aperto.md consigliano ancora cose che la Fase 100 ha già fatto o smentito (aggiungere le leghe nuove, sondare football-data.co.uk)**  
*incoerenza-doc · media · *non contro-verificato**

- **Dove**: newseason.md:149-154 (§7), newseason.md:177 (§8.1), lavoro_aperto.md:196 (§6.1); smentiti da CLAUDE.md §7 e docs/MANUALE_SOPRAVVIVENZA.md:3-15
- **Atteso**: Sono i due documenti che una sessione legge per decidere cosa fare nelle 3 settimane prima del via della stagione: se indicano lavoro già svolto, fanno perdere proprio il tempo che dicono di proteggere.
- **Trovato**: (a) newseason.md §7 «Cosa NON farei adesso»: «**Aggiungere le leghe nuove** (Ligue 1 e Bundesliga come leghe *modellate*) … **Dopo settembre.**» — fatto lo stesso giorno dalla Fase 100: le due leghe sono in LEAGUE_CONFIGS, hanno snapshot congelati (2.754 e 3.097 partite) e config δ 0.28/0.19. (b) newseason.md §8.1 e lavoro_aperto.md §6.1 elencano `football-data.co.uk` come «403 → da provare dal runner Actions» e scrivono «oggi viviamo di bundle caricati a mano», mentre MANUALE_SOPRAVVIVENZA.md in testa dichiara «football-data.co.uk | 403 → **200** — 45 stagioni ri-scaricate» e la Fase 100 ha usato proprio quella riacquisizione per l'audit riga-per-riga.
- **Come è stato accertato**: Lettura di newseason.md righe 149-154 e 170-180, lavoro_aperto.md righe 190-200; docs/MANUALE_SOPRAVVIVENZA.md righe 3-15; `git log --oneline -- lavoro_aperto.md newseason.md` → ultimi commit 81e174b/6c2e0f7, tutti precedenti ai 5 commit di integrazione.
- **Correzione**: Aggiungere in testa a entrambi i file una riga «superato dalla Fase 100 su questi punti» e correggere le due tabelle di sondaggio (football-data.co.uk e Transfermarkt ora 200; il punto §6.1/§8.1 resta valido solo per Betfair/SofaScore). In newseason.md §7 sostituire il divieto con lo stato reale (5 leghe in produzione) e con ciò che resta escluso (Serie B/Championship).

**🟠 `F13-14-registro-run-mancanti` — Cinque fasi recenti non hanno né un run in runs.jsonl né la dichiarazione «nessun run», contro la checklist §2**  
*omissione · media · *non contro-verificato**

- **Dove**: experiments/runs.jsonl (725 righe committate); docs/DIARIO.md sezioni Fase 89-bis (9348), Fase 90 (9465), Fase 93 (9878), Fase 96 (10278), Fase 100 (10949)
- **Atteso**: CLAUDE.md §2: «verifica che il run sia finito in experiments/runs.jsonl … Se hai fatto un esperimento a mano, registralo comunque via experiment_log.append_run». Le fasi che non registrano nulla devono almeno dichiararlo, come fanno correttamente 85, 86, 86-bis, 87, 88, 95, 95-bis, 97, 98, 99 («Diagnostico: nessun run in runs.jsonl»).
- **Trovato**: Mappando il campo `config.source`/`config.phase` di tutte le 725 righe committate, i run si fermano alla Fase 82 per la serie `faseNN_*`, più tre run espliciti con `phase` 89/91/94 e i `build_estimates_*` della Fase 100. Non c'è alcun run per 83, 84, 85, 86, 86-bis, 87, 88, 89-bis, 90, 92, 92-bis, 93, 95, 95-bis, 96, 97, 98, 99. Di queste, le fasi **89-bis, 90, 93, 96 e 100** non contengono nemmeno la frase che dichiara l'assenza (grep di «runs.jsonl»/«registro» dentro ciascuna sezione → nessuna occorrenza). La Fase 93 è il caso più netto: ha prodotto artefatti versionati (`experiments/fase93_discrimination.csv`, 5.083 righe, e il .json) ma nessuna riga di registro e nessuna dichiarazione.
- **Come è stato accertato**: Script su `git show HEAD:experiments/runs.jsonl`: estrazione di `faseNN` dal campo source → ultimo 82; dump delle righe 703-724 (backtest generici, phase 89/91/94, build_estimates_* di Fase 100). `git log --oneline -- experiments/runs.jsonl` → dopo 70ba37e (F91) solo 9b313ae (F94), 03d5bec ed ec85314 (F100). Grep per sezione del DIARIO su «runs.jsonl|registro» → 89-bis, 90, 93, 96, 100 senza occorrenze.
- **Correzione**: Per 89-bis/90/93/96/100 scegliere: registrare a posteriori un run sintetico con `experiment_log.append_run` (metriche già calcolate e presenti negli artefatti) oppure aggiungere in coda alla sezione la frase standard «Diagnostico: nessun run in runs.jsonl», con il perché. Il punto non è la riga in sé: è che oggi non si distingue «non registrato per scelta» da «dimenticato».

**🟡 `F13-15-script-calendari-non-migrati` — Due script citati dalla mappa dell'integrazione non sono stati spostati: le 3.045 righe di calendario coppe non sono rigenerabili da script**  
*incompiuto · bassa · *non contro-verificato**

- **Dove**: docs/audit_5_leghe/00_indice.md:22 (mappatura `cantiere/scripts/*.py -> scripts/`), docs/audit_5_leghe/numeri/caccia_calendari.md:473, 480, 1138
- **Atteso**: L'indice dichiara che tutti gli script del cantiere vivono ora in scripts/. Il principio §1.5 (riproducibilità) chiede che ogni numero sia rifacibile.
- **Trovato**: Risolvendo con la tabella di mappatura tutti i 44 riferimenti `cantiere/...` presenti in docs/, restano 2 script che non esistono in nessun punto della repo: `scripts/caccia_calendari.py` e `scripts/wiki.py` (il fetcher/parser del wikitext che ha prodotto i 50 CSV e le 3.045 righe di data/ricerca_esterna/). Il codice non è perso — è ricopiato per intero nelle Appendici A e B di docs/audit_5_leghe/numeri/caccia_calendari.md — ma non è eseguibile e la mappatura dell'indice è, per questi due file, falsa.
- **Come è stato accertato**: Script di risoluzione dei riferimenti (44 distinti) → 2 script non risolti; `find . -name caccia_calendari.py -o -name wiki.py` → nessun risultato; `ls scripts/ | grep -iE 'caccia|wiki|calendar'` → vuoto; presenza del sorgente come appendice verificata alle righe 480 e 1138 del report.
- **Correzione**: Estrarre le due appendici in `scripts/caccia_calendari.py` e `scripts/wiki.py` (già con `ROOT = parents[1]` e output su `data/ricerca_esterna/`), oppure correggere l'indice dichiarando che quei due vivono solo come appendice. La prima opzione costa dieci minuti e restituisce la rigenerabilità del dato esterno più grande entrato con la Fase 100.

**🟡 `F13-16-prospettico-3-leghe-e-note-stantie` — Il test prospettico (unica fase formalmente APERTA, scadenza a ~3 settimane) copre 3 leghe su 5 e porta note già superate**  
*incompiuto · bassa · *non contro-verificato**

- **Dove**: experiments/prospettico_2026_27.md:1-20, 36-39, 72-76, 137-152; experiments/prospettico_2026_27_dc.csv (7 righe, solo Premier); newseason.md:22-30
- **Atteso**: newseason.md §5 A1 chiede «calendario delle prime 3-5 giornate delle **5 leghe**» e previsioni DC congelate su tutti i mercati Tier 1; il progetto è a 5 leghe dalla Fase 100.
- **Trovato**: Il file è ancora impostato su 3 leghe («Serie A, Premier, La Liga» nel titolo e nel protocollo §3), l'anteprima congelata contiene 7 partite di sola Premier (`prospettico_2026_27_dc.csv`: 7 righe, tutte `premier_league`), Serie A e Liga sono «slot vuoti», e Bundesliga/Ligue 1 non sono nemmeno nominate. In più §2 e §3 istruiscono ancora l'operatore a produrre «il M2 Premier con dp_theta neutro» come passo manuale residuo, superato dalla Fase 92-bis (vedi F13-08). Le date di riferimento divergono da newseason.md §1: qui «Liga ~15/8, PL ~21/8, SA ~23/8», là «Liga 16 agosto, PL 21, SA 22».
- **Come è stato accertato**: Lettura integrale di experiments/prospettico_2026_27.md; `wc -l` e `cut` su prospettico_2026_27_dc.csv → 7 righe di dati, colonna league sempre premier_league; confronto con newseason.md righe 22-30. La scadenza dichiarata (16 agosto) è a 21 giorni dalla data corrente (26/07/2026): il file è coerente nel dichiarare l'urgenza, incoerente nel perimetro.
- **Correzione**: Estendere il perimetro a 5 leghe (o dichiarare esplicitamente perché resta a 3), rigenerare l'anteprima DC con `predict.py --league <lega>` ora che è per-lega, rimuovere le note sul θ manuale, e allineare le date di inizio a un'unica tabella (quella di newseason.md §1, che le ricava dagli `start_date` di Smarkets).

**🟡 `F13-17-manuale-data-aggiornamento` — Il manuale di sopravvivenza dichiara «Ultimo aggiornamento: Fase 70» pur avendo in testa un banner della Fase 100**  
*incoerenza-doc · bassa · *non contro-verificato**

- **Dove**: docs/MANUALE_SOPRAVVIVENZA.md:51, contro docs/MANUALE_SOPRAVVIVENZA.md:3-40
- **Atteso**: Il file dice di sé «Va aggiornato ogni volta che si scopre un fatto operativo nuovo»: la data di ultimo aggiornamento è il primo indicatore di affidabilità che un lettore usa.
- **Trovato**: La riga 51 recita «Ultimo aggiornamento: Fase 70 (luglio 2026)», mentre le righe 3-40 contengono il banner «⚠️ AGGIORNAMENTO — la rete è tornata raggiungibile (integrazione delle 5 leghe)» con la tabella dei domini ri-sondati, footiqo, la trappola FotMob e i vincoli robots.txt. Un lettore che si fermi alla riga 51 conclude che il file è vecchio di 30 fasi.
- **Come è stato accertato**: sed -n 1,70p docs/MANUALE_SOPRAVVIVENZA.md; `git log --oneline -- docs/MANUALE_SOPRAVVIVENZA.md` mostra il tocco nel commit di integrazione 46bf0fc.
- **Correzione**: Portare la riga 51 a «Ultimo aggiornamento: Fase 100 (integrazione delle 5 leghe)» e, già che si è lì, riportare nella tabella §1 «Host BLOCCATI» lo stato nuovo di football-data.co.uk e understat.com invece di lasciarli elencati come bloccati con un banner che li smentisce 40 righe sopra.

**🟡 `F13-18-workflow-3-leghe-caccia-chiusa` — I workflow GitHub Actions servono una caccia ormai chiusa e conoscono solo 3 leghe su 5**  
*incoerenza-doc · bassa · *non contro-verificato**

- **Dove**: .github/workflows/betexplorer-scrape.yml:8-18, .github/betexplorer-scrape-trigger, .github/workflows/kaggle-ou-probe.yml:3-7
- **Atteso**: Dopo la chiusura della caccia O/U 2017-19 (docs/CACCIA_OU_2017_19.md: «CHIUSA: il dato è stato trovato») e l'ingresso di Bundesliga e Ligue 1, l'automazione dovrebbe riflettere lo stato del progetto o essere marcata come dormiente.
- **Trovato**: Il menu `league_season` di betexplorer-scrape.yml offre solo serie-a/premier-league/laliga 2017-18 e 2018-19; il file-segnale committato contiene ancora «probe-7 laliga-2017-2018 stesso-check-tab»; kaggle-ou-probe.yml si descrive come «Fase A del piano CACCIA_OU_2017_19.md». Tutte e tre le automazioni puntano a un obiettivo che il progetto ha dichiarato concluso, e nessuna nomina le due leghe nuove. Non c'è danno operativo (i trigger sono manuali o legati al push del file-segnale, e gli script referenziati esistono tutti: scrape_betexplorer.py, check_acceptance.py, probe_kaggle_ou_datasets.py), ma è residuo da smaltire.
- **Come è stato accertato**: Lettura integrale dei tre file .yml e dei tre file-segnale; verifica dell'esistenza dei tre script referenziati (tutti presenti in scripts/). Nota positiva verificata nello stesso giro: il cron mensile di import_dataset.yml è correttamente disattivato con la motivazione dell'audit Fase 92 scritta nel file.
- **Correzione**: Aggiungere in testa ai due workflow della caccia una riga «pista CHIUSA alla Fase 100 — workflow conservato per riferimento, non lanciarlo senza rileggere docs/CACCIA_OU_2017_19.md», oppure rimuoverli; se si conservano, estendere il menu alle 5 leghe per non lasciare un'automazione tarata su un perimetro che non esiste più.

<details><summary>Verifiche con esito OK su questo fronte</summary>

- Blocco 📐 «Il modello in dettaglio» presente in TUTTE le 27 sezioni del DIARIO dalla Fase 78 alla Fase 100 (script di split su '## Fase' + conteggio del carattere 📐: nessuna sezione priva; Fase 84 ne ha 2, Fase 86 ne ha 3). Nessuna violazione di CLAUDE.md §2-bis nelle ultime 20 fasi.
- Suite di test verde: `python -m pytest -q` → 194 passed in 52s, nessun fallimento e nessun warning bloccante, con la repo nello stato attuale (post-integrazione).
- Le 3.045 righe di calendario coppe dichiarate dal commit 3/3c esistono davvero e il numero è esatto: 50 file `data/ricerca_esterna/fixtures_*.csv`, somma righe = 3045 (coincide con docs/audit_5_leghe/09_chiusura_buchi.md:262). Il manifest SHA256 delle fonti (`data/ricerca_esterna/manifest_fonti_audit.json`) esiste.
- Il totale di 16.111 partite dichiarato in CLAUDE.md §6 si ricompone dagli snapshot: 3.420 × 3 (Serie A, Premier, Liga) + 2.754 (Bundesliga) + 3.097 (Ligue 1) = 16.111, con copertura squad_value al 100% su tutte e 5 le leghe.
- Il censimento dei falsi zero di `midweek_europe` è internamente coerente: le cinque righe caso D di `data/estimates/celle_residue.csv` dichiarano 236+251+454+180+482 = **1.603** celle, esattamente il numero citato in CLAUDE.md §5-bis R6 e in docs/DATI.md §1.
- La decisione di NON inserire il dato 1xBet trovato è registrata in modo esemplare nel documento giusto (docs/CACCIA_OU_2017_19.md, banner «ESITO FINALE» con il motivo tecnico: book singolo contro colonna multi-book, MAE 0.0156 vs ~0.012, rottura di regime a metà colonna) — è PISTE.md a non averla recepita (F13-05), non la decisione a mancare.
- La scadenza operativa della Fase 78 è dichiarata e coerente in due punti: newseason.md §1 («La scadenza vera è il 16 agosto», con la tabella delle 5 date di inizio) e lavoro_aperto.md §1 («⏰ Ha una scadenza vera: 16 agosto»). A oggi 26/07/2026 sono 21 giorni.
- Il residuo aperto dalla Fase 96/98 sul secondo tempo (game-state → modello a due stadi) è propagato correttamente in tutti e quattro i registri: docs/PISTE.md §6 (righe 238-240) e §18 (righe 437-439), docs/PANCHINA.md riga 100, lavoro_aperto.md righe 75 e 98, CLAUDE.md §6 riga 484.
- L'affermazione di newseason.md §6 B4 «8 fasi fondative senza riga nel registro del README» è esatta e ancora aperta: confronto automatico fra le 111 intestazioni «## Fase» del DIARIO e le etichette della tabella del README → mancano esattamente 8 fasi (0, 1, 2a, 4a, 5, 4e, 9, 13-bis).
- Gli script referenziati dai tre workflow GitHub Actions esistono tutti (`scripts/scrape_betexplorer.py`, `scripts/check_acceptance.py`, `scripts/probe_kaggle_ou_datasets.py`) e la cartella `files/player_scores/` con i 4 .csv.gz è al suo posto; il cron mensile di import_dataset.yml è disattivato con la motivazione dell'audit Fase 92 scritta nel file.
- La cartella `cantiere/` è effettivamente vuota (2 directory, 0 file, 0 file tracciati da git): lo smantellamento dichiarato dal commit 6c9b377 è reale sul lato dati — i problemi residui sono nei percorsi dentro il codice e nei documenti, non in file rimasti indietro.
- La rosa dei modelli è stata correttamente estesa a 5 leghe: la matrice di docs/PANCHINA.md ha 48 righe × 6 colonne (5 leghe + fronte generale) con le celle di Bundesliga e Ligue 1 popolate (es. router θ ❌ 0/25 mercati su entrambe, φ35 ❌).
- Nessuna stima `squad_value` è attiva e la documentazione lo dice correttamente: `data/estimates/squad_value_2017_26.csv` ha 0 righe e i due run `build_estimates_squad_value` della Fase 100 registrano `n_estimates: 0`, coerentemente con docs/DATI.md riga 231.
- I riferimenti `cantiere/...` rimasti nei report di docs/audit_5_leghe/ non sono orfani: docs/audit_5_leghe/00_indice.md righe 13-24 fornisce la tabella di traslazione completa dei percorsi, e 42 riferimenti su 44 si risolvono su file esistenti (le 2 eccezioni sono il finding F13-15).

</details>
