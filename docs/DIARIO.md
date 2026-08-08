# Diario di bordo — Football Oracle

Resoconto passo-passo di come è stato costruito il progetto, **con il ragionamento
e le scelte** dietro ogni decisione. È pensato per chiunque (persona o AI) voglia
capire *perché* il software è fatto così, non solo *com'è* fatto.

Filo conduttore metodologico, applicato ovunque:

1. **Tracer bullet prima dei moduli** — costruire una fetta verticale reale
   end-to-end, poi raffinare, invece di progettare tutto a tavolino.
2. **Una cosa alla volta, e si misura** — cambiare un solo fattore per volta,
   altrimenti non si sa *cosa* ha funzionato.
3. **Testare la versione economica di un'idea prima di investire** — evita di
   costruire infrastrutture costose su assunzioni non verificate.
4. **Documentare anche i risultati negativi** — sapere cosa *non* funziona vale
   quanto sapere cosa funziona.
5. **Riproducibilità** — ogni numero dev'essere rifacibile da terzi.
6. **Onestà sui limiti** — soprattutto perché in gioco ci sono soldi veri.
7. **Validare su più stagioni** — mai concludere da una sola (rumore); default
   3+, per le conclusioni importanti 6+ (regola maturata nelle prime fasi).
8. **Il bersaglio è il singolo mercato** — ogni modello si giudica mercato per
   mercato, non su un solo log-loss aggregato (principio nato con la Fase 5,
   formalizzato dalla Fase 21).
9. **Due fronti per ogni modello** — versione per-lega e versione generale
   (pooled), tracciate nella rosa di `docs/PANCHINA.md` (dalla Fase 65).

*(I principi 7-9 non c'erano dal giorno zero: sono lezioni pagate strada
facendo, e il diario racconta anche dove sono nati. La versione normativa e
sempre aggiornata vive nel [`CLAUDE.md`](../CLAUDE.md), §1.)*

---

## Indice del diario

Il diario è **cronologico** (ogni fase costruisce sulla precedente), ma con 80+
fasi serve una mappa. Qui sotto le fasi sono raggruppate in **archi narrativi**:
ogni arco ha una domanda di fondo e una conclusione. Se cerchi *un* argomento
specifico, usa i link; se vuoi capire il progetto, gli archi si leggono anche da
soli come riassunto della storia.

### Arco 1 — La costruzione del modello (Fasi 0–8)

*Dal tracer bullet al Dixon-Coles tarato: blend gol/xG, emivita, shrinkage,
prior neopromosse. Esito dell'arco: il modello batte nettamente le baseline ma
non il mercato; la config ufficiale è fissata qui.*

- [Fase 0 — Visione e prime scelte di fondo](#fase-0--visione-e-prime-scelte-di-fondo)
- [Fase 1 — Tracer bullet: Dixon-Coles + backtest](#fase-1--tracer-bullet-dixon-coles--backtest)
- [Fase 2a — Analisi degli errori (e un bug trovato)](#fase-2a--analisi-degli-errori-e-un-bug-trovato)
- [Fase 2b — Tuning: regolarizzazione e memoria](#fase-2b--tuning-regolarizzazione-e-memoria)
- [Fase 3 — Informazione nuova: i tiri in porta (risultato NEGATIVO)](#fase-3--informazione-nuova-i-tiri-in-porta-risultato-negativo)
- [Infrastruttura — Tracciabilità e database interno](#infrastruttura--tracciabilità-e-database-interno)
- [Dove siamo — cosa sappiamo con onestà](#dove-siamo--cosa-sappiamo-con-onestà)
- [Fase 4a — I dati per l'xG reale (e per le rose): arricchimento completato](#fase-4a--i-dati-per-lxg-reale-e-per-le-rose-arricchimento-completato)
- [Fase 4b — xG reale nel blend: primo miglioramento da dati nuovi](#fase-4b--xg-reale-nel-blend-primo-miglioramento-da-dati-nuovi)
- [Fase 4c — Spremere il resto dei dati: npxG, valori rosa, assenze (NEGATIVO)](#fase-4c--spremere-il-resto-dei-dati-npxg-valori-rosa-assenze-negativo)
- [Fase 4d — Ri-taratura congiunta: l'emivita si accorcia col blend xG](#fase-4d--ri-taratura-congiunta-lemivita-si-accorcia-col-blend-xg)
- [Fase 5 — Grande backtest multi-mercato: per cosa il modello serve davvero](#fase-5--grande-backtest-multi-mercato-per-cosa-il-modello-serve-davvero)
- [Fase 4e — Calendario di club completo: la congestione VERA (dato nuovo)](#fase-4e--calendario-di-club-completo-la-congestione-vera-dato-nuovo)
- [Fase 4e-bis — Validazione della congestione VERA (walk-forward)](#fase-4e-bis--validazione-della-congestione-vera-walk-forward)
- [Fase 6 — Ricalibrazione della confidenza (temperature scaling, NEGATIVO-ish)](#fase-6--ricalibrazione-della-confidenza-temperature-scaling-negativo-ish)
- [Fase 7 — Prior di cold-start per le neopromosse (il miglior guadagno interno)](#fase-7--prior-di-cold-start-per-le-neopromosse-il-miglior-guadagno-interno)
- [Fase 8 — Ultimo giro economico (shrinkage, vantaggio-casa): niente da spremere](#fase-8--ultimo-giro-economico-shrinkage-vantaggio-casa-niente-da-spremere)

### Arco 2 — L'anatomia del gap col mercato (Fasi 9–20)

*Dove e perché si perde dal mercato. Scoperte chiave: il mercato ingloba
completamente il modello (α\*=0, Fase 16); i
"value bet" del modello sono i suoi errori (adverse selection, Fase 20). Qui
nascono anche le regole statistiche del progetto (CI bootstrap, Fase 17).
**Attenzione**: la conclusione «il gap vive quasi tutto nel pareggio», nata in
questo arco e ripetuta per 80 fasi, è stata **rovesciata dalla Fase 92**: l'88%
del gap sta nella discriminazione casa/ospite, il 12% nel pareggio.*

- [Fase 9 — Anatomia del gap col mercato (analisi approfondita)](#fase-9--anatomia-del-gap-col-mercato-analisi-approfondita)
- [Fase 10 — Ricalibrazione per-classe 1X2 (attacca il pareggio; robusto ma piccolo)](#fase-10--ricalibrazione-per-classe-1x2-attacca-il-pareggio-robusto-ma-piccolo)
- [Fase 11 — Combinazioni delle feature off-di-default (nessuna e' utile)](#fase-11--combinazioni-delle-feature-off-di-default-nessuna-e-utile)
- [Fase 12a — Ensemble di emivite (ultimo tweak economico; piccolo, borderline)](#fase-12a--ensemble-di-emivite-ultimo-tweak-economico-piccolo-borderline)
- [Fase 12b — Il cambio di classe: inflazione della diagonale (bivariato)](#fase-12b--il-cambio-di-classe-inflazione-della-diagonale-bivariato)
- [Fase 13 — Stato di forma: un pattern nascosto? (NO, gia' catturato)](#fase-13--stato-di-forma-un-pattern-nascosto-no-gia-catturato)
- [Fase 13-bis — Streak e rendimento recente: ricerca DATA-DRIVEN (nessun pattern)](#fase-13-bis--streak-e-rendimento-recente-ricerca-data-driven-nessun-pattern)
- [Fase 14 — Il modello contro la linea di APERTURA (CLV) — NEGATIVO, e definitivo](#fase-14--il-modello-contro-la-linea-di-apertura-clv--negativo-e-definitivo)
- [Fase 15 — Audit dei calcoli (verifica indipendente; 1 errore vero trovato)](#fase-15--audit-dei-calcoli-verifica-indipendente-1-errore-vero-trovato)
- [Fase 15-bis — Gap per mercato, stagione per stagione (la matrice completa)](#fase-15-bis--gap-per-mercato-stagione-per-stagione-la-matrice-completa)
- [Fase 16 — Encompassing: il modello ha informazione propria? (NO, α*=0)](#fase-16--encompassing-il-modello-ha-informazione-propria-no-α0)
- [Fase 17 — Intervalli di confidenza: quali numeri sono reali e quali rumore](#fase-17--intervalli-di-confidenza-quali-numeri-sono-reali-e-quali-rumore)
- [Fase 18 — Rho dinamico: l'ultima idea strutturale sul pareggio (NEGATIVA)](#fase-18--rho-dinamico-lultima-idea-strutturale-sul-pareggio-negativa)
- [Fase 19 — Potenza sul prior: 8 stagioni (l'evidenza si rafforza, non conclude)](#fase-19--potenza-sul-prior-8-stagioni-levidenza-si-rafforza-non-conclude)
- [Fase 20 — Anatomia dei residui: nessun segnale nascosto, ma si scopre il PERCHE'](#fase-20--anatomia-dei-residui-nessun-segnale-nascosto-ma-si-scopre-il-perche)

### Arco 3 — Modelli nuovi e la svolta market-implied (Fasi 21–27)

*Cambio di strategia: non più tweak al DC ma famiglie diverse, giudicate PER
MERCATO. Il GBM viene bocciato ovunque (il tetto è informativo, non
architetturale); la svolta è INVERTIRE le quote — i λ,μ impliciti del mercato
dentro la matrice DC battono i nostri su quasi ogni mercato (Fasi 24/26).*

- [Fase 21 — Un modello diverso sul GG/NG: gradient boosting (pareggia, non batte)](#fase-21--un-modello-diverso-sul-ggng-gradient-boosting-pareggia-non-batte)
- [Fase 22 — Sweep del GBM su tutti i mercati: il tetto e' informativo, non di modello](#fase-22--sweep-del-gbm-su-tutti-i-mercati-il-tetto-e-informativo-non-di-modello)
- [Fase 23 — GBM modello + mercato: si puo' ridurre il gap? (no, non con un GBM)](#fase-23--gbm-modello--mercato-si-puo-ridurre-il-gap-no-non-con-un-gbm)
- [Fase 24 — DC calcolato DAL mercato: il primo risultato positivo dell'arco modelli](#fase-24--dc-calcolato-dal-mercato-il-primo-risultato-positivo-dellarco-modelli)
- [Fase 25 — Finestra dei dati: piu' storia batte meno (anche per il calcio di oggi)](#fase-25--finestra-dei-dati-piu-storia-batte-meno-anche-per-il-calcio-di-oggi)
- [Fase 26 — Market-implied su TUTTI i mercati sui gol (il risultato piu' forte)](#fase-26--market-implied-su-tutti-i-mercati-sui-gol-il-risultato-piu-forte)
- [Fase 27 — Ottimizzare la forma dei punteggi sul market-implied (gia' ottima)](#fase-27--ottimizzare-la-forma-dei-punteggi-sul-market-implied-gia-ottima)

### Arco 4 — Tempo e motivazione (Fasi 28–33)

*Il finale di stagione è più difficile per tutti; la posta in palio conta solo
come ASIMMETRIA (una squadra decisa, una in corsa — Fase 31, che ribalta la 29).
Con la Fase 33 i dati interni sono completamente esplorati.*

- [Fase 28 — Quando falliscono i modelli? Errore per momento della stagione](#fase-28--quando-falliscono-i-modelli-errore-per-momento-della-stagione)
- [Fase 29 — Posta in palio: i "dead rubber" spiegano il finale? (NO)](#fase-29--posta-in-palio-i-dead-rubber-spiegano-il-finale-no)
- [Fase 30 — Pattern dentro la stagione: anatomia per periodo](#fase-30--pattern-dentro-la-stagione-anatomia-per-periodo)
- [Fase 31 — Posta in palio corretta (8 stagioni): conta l'ASIMMETRIA](#fase-31--posta-in-palio-corretta-8-stagioni-conta-lasimmetria)
- [Fase 32 — Validazione della covariata stakes-mismatch (DC e GBM)](#fase-32--validazione-della-covariata-stakes-mismatch-dc-e-gbm)
- [Fase 33 — Ultime covariate mai provate: PPDA/deep e finishing-luck (ridondanti)](#fase-33--ultime-covariate-mai-provate-ppdadeep-e-finishing-luck-ridondanti)

### Arco 5 — L'audit critico e la forma dei punteggi (Fasi 34–44)

*Un audit avversario trova la leva mai testata: il pareggio come EQUILIBRIO. La
φ(|λ−μ|) (Fase 35) diventa il miglior risultato sul pareggio; bivariato e copule
non la battono; il routing di forma per-mercato (Fase 44) entra nel motore.*

- [Fase 34 — Audit critico: caccia a errori, superficialità e leve mai testate](#fase-34--audit-critico-caccia-a-errori-superficialità-e-leve-mai-testate)
- [Fase 35 — Il pareggio come EQUILIBRIO: φ condizionato a |λ−μ| (il miglior risultato sul pareggio)](#fase-35--il-pareggio-come-equilibrio-φ-condizionato-a-λμ-il-miglior-risultato-sul-pareggio)
- [Fase 36 — GBM col set di feature COMPLETO: overfitting, non guadagno (ma lo stakes emerge)](#fase-36--gbm-col-set-di-feature-completo-overfitting-non-guadagno-ma-lo-stakes-emerge)
- [Fase 37 — Covariate nel CANALE-PAREGGIO? (Punto 3: diagnostico economico, NEGATIVO)](#fase-37--covariate-nel-canale-pareggio-punto-3-diagnostico-economico-negativo)
- [Fase 38 — Denoising cross-stagione del market-implied (Punto 4: motore già maturo)](#fase-38--denoising-cross-stagione-del-market-implied-punto-4-motore-già-maturo)
- [Fase 39 — Market-implied + φ(|λ−μ|): la sintesi dei due risultati positivi](#fase-39--market-implied--φλμ-la-sintesi-dei-due-risultati-positivi)
- [Fase 40 — ROI PER MERCATO/ESITO: cosa nascondeva il value-betting 1X2 piatto](#fase-40--roi-per-mercatoesito-cosa-nascondeva-il-value-betting-1x2-piatto)
- [Fase 41 — Bakeoff per-mercato: un modello cucito su ogni mercato? (specialisti)](#fase-41--bakeoff-per-mercato-un-modello-cucito-su-ogni-mercato-specialisti)
- [Fase 42 — Poisson bivariato: la correlazione esplicita (5° modello, non batte la φ35)](#fase-42--poisson-bivariato-la-correlazione-esplicita-5-modello-non-batte-la-φ35)
- [Fase 43 — Spremere la dipendenza: copule flessibili (la φ35 è il tetto)](#fase-43--spremere-la-dipendenza-copule-flessibili-la-φ35-è-il-tetto)
- [Fase 44 — Routing di forma per-mercato + decisioni di architettura](#fase-44--routing-di-forma-per-mercato--decisioni-di-architettura)
- [Prossimo passo — il modello e' al tetto REALE dei dati attuali](#prossimo-passo--il-modello-e-al-tetto-reale-dei-dati-attuali)

### Arco 6 — Path senza quote e dinamica stagionale (Fasi 45–50)

*Si chiudono i lead rimasti: lo stakes non è sfruttabile (Fase 45), gli ensemble
non aiutano, l'architettura dinamica non batte lo statico (Fasi 47-48; resta un
nudge GG/NG di fine stagione, off di default). Il mega-sweep (Fase 50) trova che
φ35 e nudge sono additivi: miglior GG/NG del progetto.*

- [Fase 45 — Router "stakes-aware" sul path senza quote (chiude il lead della Fase 32)](#fase-45--router-stakes-aware-sul-path-senza-quote-chiude-il-lead-della-fase-32)
- [Fase 46 — Ensemble dei predittori standalone (DC + bivariato + GBM), senza quote](#fase-46--ensemble-dei-predittori-standalone-dc--bivariato--gbm-senza-quote)
- [Fase 47 — Tracer-bullet dinamico: vantaggio-casa tempo-variante (γ per fascia)](#fase-47--tracer-bullet-dinamico-vantaggio-casa-tempo-variante-γ-per-fascia)
- [Fase 48 — Modello dinamico a profilo stagionale liscio, su 8 stagioni (chiude l'architettura)](#fase-48--modello-dinamico-a-profilo-stagionale-liscio-su-8-stagioni-chiude-larchitettura)
- [Fase 49 — Perche' solo 35-38? La finestra/forma del nudge GG/NG (non e' binario)](#fase-49--perche-solo-35-38-la-finestraforma-del-nudge-ggng-non-e-binario)
- [Fase 50 — Mega-sweep combinatorio: le leve OFF, insieme, su tutti i motori](#fase-50--mega-sweep-combinatorio-le-leve-off-insieme-su-tutti-i-motori)

### Arco 7 — La sotto-dispersione e il beat-the-close (Fasi 51–52)

*La scoperta più importante: i gol dati i tassi del mercato sono SOTTO-dispersi
(double-Poisson θ≈1.2). `sharpen_1x2` batte la chiusura devigata in log-loss con
CI conclusivo (non in ROI); il router v3 (dp su tutto il listino) viene ADOTTATO.*

- [Fase 51 — Audit delle lacune + modelli mai provati: la sotto-dispersione batte la chiusura](#fase-51--audit-delle-lacune--modelli-mai-provati-la-sotto-dispersione-batte-la-chiusura)
- [Fase 52 — Spremere la scoperta: la double-Poisson su tutto il listino, i suoi limiti, e il dinamico chiuso per test](#fase-52--spremere-la-scoperta-la-double-poisson-su-tutto-il-listino-i-suoi-limiti-e-il-dinamico-chiuso-per-test)

### Arco 8 — Cross-lega: Premier e La Liga (Fasi 53–57)

*Il modello è trasferibile, l'edge no: il beat-the-close è una proprietà della
chiusura Serie A (meno liquida), non del calcio. Le due leghe entrano nel
progetto come configurazione (`LEAGUE_CONFIGS`), non come codice.*

- [Fase 53 (tracer) — Cross-lega: i bias del mercato sono UNIVERSALI o Serie A?](#fase-53-tracer--cross-lega-i-bias-del-mercato-sono-universali-o-serie-a)
- [Fasi 54-57 — Premier League e La Liga: conoscere due leghe nuove da zero](#fasi-54-57--premier-league-e-la-liga-conoscere-due-leghe-nuove-da-zero)

### Arco 9 — La campagna dei dati (Fasi 58–75)

*Ogni buco dei dati viene chiuso, stimato con protocollo dichiarato, o mappato:
audit delle quote, aperture Pinnacle 2017-19 recuperate, valori rosa REALI via
GitHub Actions, la caccia alle O/U 2017-19 e il colpo di scena della Fase 73
(erano un'APERTURA reale, non una chiusura). Il motore viene validato su 2.280
partite mai viste (Fase 75).*

- [Fase 58 — Audit dati: overround impossibile nella quota "Avg" (bug, non modello)](#fase-58--audit-dati-overround-impossibile-nella-quota-avg-bug-non-modello)
- [Fase 59 — Congestione vera anche per Premier League e La Liga (colmato il gap dati)](#fase-59--congestione-vera-anche-per-premier-league-e-la-liga-colmato-il-gap-dati)
- [Fase 60 — Valore rosa e assenze anche per Premier League e La Liga](#fase-60--valore-rosa-e-assenze-anche-per-premier-league-e-la-liga)
- [Fase 61 — Quote di apertura 2017-19: la chiusura di Pinnacle era ignorata](#fase-61--quote-di-apertura-2017-19-la-chiusura-di-pinnacle-era-ignorata)
- [Fase 62 — Ricostruire la chiusura O/U mancante (2017-19) coi nostri modelli?](#fase-62--ricostruire-la-chiusura-ou-mancante-2017-19-coi-nostri-modelli)
- [Fase 62-bis — La stima migliorata, pubblicata come STIMA (e il catalogo dati)](#fase-62-bis--la-stima-migliorata-pubblicata-come-stima-e-il-catalogo-dati)
- [Fase 63 — Il bug del matching giocatori: l'inversione nome/cognome](#fase-63--il-bug-del-matching-giocatori-linversione-nomecognome)
- [Fase 64 — «La panchina»: il registro dei miglioramenti misurati ma non attivati](#fase-64--la-panchina-il-registro-dei-miglioramenti-misurati-ma-non-attivati)
- [Fase 65 — La rosa completa e la regola dei due fronti](#fase-65--la-rosa-completa-e-la-regola-dei-due-fronti)
- [Fase 66 — Riempire le celle vuote: il valore rosa stimato (e l'inventario finale)](#fase-66--riempire-le-celle-vuote-il-valore-rosa-stimato-e-linventario-finale)
- [Fase 67 — I valori rosa REALI: il canale GitHub Actions e la fonte player-scores](#fase-67--i-valori-rosa-reali-il-canale-github-actions-e-la-fonte-player-scores)
- [Fase 68 — Gli ultimi buchi chiudibili: preludio dei calendari e cron d'import](#fase-68--gli-ultimi-buchi-chiudibili-preludio-dei-calendari-e-cron-dimport)
- [Fase 69 — Stimare i gap sparsi: bakeoff apertura~chiusura (richiesta utente)](#fase-69--stimare-i-gap-sparsi-bakeoff-aperturachiusura-richiesta-utente)
- [Fase 70 — Le ultime 13 celle squad_value: dato REALE da Transfermarkt (richiesta utente)](#fase-70--le-ultime-13-celle-squad_value-dato-reale-da-transfermarkt-richiesta-utente)
- [Fase 71 — Caccia O/U 2017-19, Fase A: dataset già pronti (Kaggle/GitHub/HF), negativa](#fase-71--caccia-ou-2017-19-fase-a-dataset-già-pronti-kagglegithubhf-negativa)
- [Fase 72 — Spremere ANCORA la stima E3 pooled (richiesta esplicita: "al massimo")](#fase-72--spremere-ancora-la-stima-e3-pooled-richiesta-esplicita-al-massimo)
- [Fase 73 — L'O/U 2017-19 era un'APERTURA, non una chiusura: il dato reale nella colonna giusta](#fase-73--lou-2017-19-era-unapertura-non-una-chiusura-il-dato-reale-nella-colonna-giusta)
- [Fase 74 — Ri-validazione di TUTTI i calcoli sui dati corretti (richiesta utente)](#fase-74--ri-validazione-di-tutti-i-calcoli-sui-dati-corretti-richiesta-utente)
- [Fase 75 — Spremere il 2017-19: il motore validato su 2.280 partite vergini (e il θ che cresce nel tempo)](#fase-75--spremere-il-2017-19-il-motore-validato-su-2280-partite-vergini-e-il-θ-che-cresce-nel-tempo)

### Arco 10 — Il motore per-lega, la verifica finale e gli audit (Fasi 76–88)

*Il market-implied trasferisce identico su 3 leghe (Fase 76); le leve del
pareggio sono un tratto delle leghe latine (Fase 79-80); il mega-sweep delle
costanti (Fase 81) dà la mappa per-lega e ribalta il router-Liga; la verifica
diretta (Fase 82) certifica che l'oracolo è calibrato — indovina quanto il
mercato, non di più. Poi tre giri di audit: la revisione dei commit esterni
(Fase 83) e del tool per-lega (83-bis), l'audit trasversale del repo (Fase 84),
l'anatomia della coda per gli esiti meno probabili (Fase 85, la double-Poisson
è al tetto; ~~COM-Poisson provata e pari~~ — è la stessa dp riparametrizzata,
rettifica Fase 101) e il secondo audit orchestrato con
verifica avversaria (Fase 86: fix di onestà, chiusure e il lead della
dispersione per-squadra).*

- [Fase 76 — Il motore market-implied trasferisce cross-lega ANCHE sulla chiusura](#fase-76--il-motore-market-implied-trasferisce-cross-lega-anche-sulla-chiusura)
- [Fase 77 — Il nome onesto: da «Polymarket Oracle» a «Football Oracle»](#fase-77--il-nome-onesto-da-polymarket-oracle-a-football-oracle)
- [Fase 78 — Test prospettico 2026-27 (giornata 1): impostato, da completare](#fase-78--test-prospettico-2026-27-giornata-1-impostato-da-completare)
- [Fase 79 — Studio dedicato Premier/Liga: le prime leve per-lega (φ35 e congestione)](#fase-79--studio-dedicato-premierliga-le-prime-leve-per-lega-φ35-e-congestione)
- [Fase 80 — La catena GG/NG del market-implied su Premier/Liga: la φ35 paga in Liga (CI<0), il nudge no](#fase-80--la-catena-ggng-del-market-implied-su-premierliga-la-φ35-paga-in-liga-ci0-il-nudge-no)
- [Fase 81 — Mega-sweep delle costanti del market-implied per-lega: le curve di risposta complete (e il ribaltamento del router-Liga)](#fase-81--mega-sweep-delle-costanti-del-market-implied-per-lega-le-curve-di-risposta-complete-e-il-ribaltamento-del-router-liga)
- [Fase 82 — Verifica diretta: ma indoviniamo davvero i risultati? (calibrazione e hit-rate su tutti i mercati)](#fase-82--verifica-diretta-ma-indoviniamo-davvero-i-risultati-calibrazione-e-hit-rate-su-tutti-i-mercati)
- [Fase 83 — Revisione dei commit esterni (Codex, Fasi 6-13): corretti; 7 difetti minori, 1 fix](#fase-83--revisione-dei-commit-esterni-codex-fasi-6-13-corretti-7-difetti-minori-1-fix)
- [Fase 83-bis — `predict.py` per-lega: il "passo 2" del test prospettico (parziale)](#fase-83-bis--predictpy-per-lega-il-passo-2-del-test-prospettico-parziale)
- [Fase 84 — Audit trasversale del repo (4 fronti): numeri OK, codice OK, docs ripuliti, nuove piste](#fase-84--audit-trasversale-del-repo-4-fronti-numeri-ok-codice-ok-docs-ripuliti-nuove-piste)
- [Fase 85 — La chiave per gli esiti MENO PROBABILI: anatomia della coda (θ diretto sul risultato esatto, e la COM-Poisson)](#fase-85--la-chiave-per-gli-esiti-meno-probabili-anatomia-della-coda-θ-diretto-sul-risultato-esatto-e-la-com-poisson)
- [Fase 86 — Secondo audit orchestrato (workflow): fix di onestà, chiusure e il LEAD della dispersione per-squadra](#fase-86--secondo-audit-orchestrato-workflow-fix-di-onestà-chiusure-e-il-lead-della-dispersione-per-squadra)
- [Fase 86-bis — Il verdetto walk-forward sul θ per-squadra: NON sfruttabile (il tetto regge anche nella coda)](#fase-86-bis--il-verdetto-walk-forward-sul-θ-per-squadra-non-sfruttabile-il-tetto-regge-anche-nella-coda)
- [Fase 87 — La coda a DUE parametri, riprodotta: isotonica e mistura, entrambe chiuse](#fase-87--la-coda-a-due-parametri-riprodotta-isotonica-e-mistura-entrambe-chiuse)
- [Fase 88 — Handicap asiatico come benchmark Tier 2: il router prezza il margine come il mercato sharp](#fase-88--handicap-asiatico-come-benchmark-tier-2-il-router-prezza-il-margine-come-il-mercato-sharp)

---

### Arco 11 — I mercati non derivabili da una matrice, e la revisione della diagnosi (Fasi 89–99)

*Il simulatore di stagione apre la prima famiglia di mercati che NON si deriva
dalla matrice di una partita (Fase 89), subito ridimensionata dall'audit (Fase
90) e portata sui mercati posizionali (Fase 91). Poi il quarto audit ROVESCIA la
diagnosi centrale del progetto: il gap è 88% discriminazione casa/ospite, non
pareggio (Fase 92), e la Fase 93 mostra che è informazione, non calibrazione,
concentrata sulle equilibrate e nella seconda metà di stagione. La deriva di
forza in-season (Fase 94) è la prima correzione adottata su un solo mercato;
Polymarket e Smarkets diventano il primo benchmark ESTERNO sugli outright (Fasi
95, 95-bis, 97). Fuori dalla matrice dei gol si aprono corner e cartellini (Fase
96). La Fase 98 chiude sette fronti in parallelo e trova, per via trasversale,
la **deriva di livello** dei conteggi — che la Fase 99 misura e **boccia**:
il bias di fold non persiste (10/18 stesso segno), quindi non era una deriva ma
rumore aggregato. Misurato ≠ prevedibile.*

- [Fase 89 — Il mercato CAMPIONE DI STAGIONE: il primo mercato non derivabile da una matrice](#fase-89--il-mercato-campione-di-stagione-il-primo-mercato-non-derivabile-da-una-matrice)
- [Fase 89-bis — Perché sbagliamo il campione: la separazione «titolo confermato / titolo che cambia»](#fase-89-bis--perché-sbagliamo-il-campione-la-separazione-titolo-confermato--titolo-che-cambia)
- [Fase 90 — Terzo audit orchestrato: i numeri-titolo della Fase 89 erano gonfiati](#fase-90--terzo-audit-orchestrato-i-numeri-titolo-della-fase-89-erano-gonfiati)
- [Fase 91 — I mercati POSIZIONALI: il simulatore è calibrato in alto e sbaglia in basso (ed è colpa del prior)](#fase-91--i-mercati-posizionali-il-simulatore-è-calibrato-in-alto-e-sbaglia-in-basso-ed-è-colpa-del-prior)
- [Fase 92 — Quarto audit (per aree): la diagnosi centrale era invertita, e il prior non atterrava dove diceva](#fase-92--quarto-audit-per-aree-la-diagnosi-centrale-era-invertita-e-il-prior-non-atterrava-dove-diceva)
- [Fase 92-bis — I fix dell'audit, verificati per mutazione (e l'IC della Fase 91 che si sgonfia)](#fase-92-bis--i-fix-dellaudit-verificati-per-mutazione-e-lic-della-fase-91-che-si-sgonfia)
- [Fase 93 — Dove si perde la discriminazione: è informazione, non calibrazione (e si vede DOVE)](#fase-93--dove-si-perde-la-discriminazione-è-informazione-non-calibrazione-e-si-vede-dove)
- [Fase 94 — La varianza mancante: la deriva di forza, e perché va adottata su UN solo mercato](#fase-94--la-varianza-mancante-la-deriva-di-forza-e-perché-va-adottata-su-un-solo-mercato)
- [Fase 95 — Il primo confronto con un mercato VERO sull'outright: Polymarket quota il campione 2026-27](#fase-95--il-primo-confronto-con-un-mercato-vero-sulloutright-polymarket-quota-il-campione-2026-27)
- [Fase 95-bis — La deriva di forza messa alla prova dal MERCATO: il backtest non aveva potenza](#fase-95-bis--la-deriva-di-forza-messa-alla-prova-dal-mercato-il-backtest-non-aveva-potenza)
- [Fase 96 — Fuori dalla matrice dei gol: corner e cartellini (e l'arbitro, il primo dato ortogonale)](#fase-96--fuori-dalla-matrice-dei-gol-corner-e-cartellini-e-larbitro-il-primo-dato-ortogonale)
- [Fase 97 — Una SECONDA borsa (Smarkets), l'archivio storico degli outright, e il primo controllo esterno della deriva](#fase-97--una-seconda-borsa-smarkets-larchivio-storico-degli-outright-e-il-primo-controllo-esterno-della-deriva)
- [Fase 98 — Sette fronti in parallelo: cosa regge, cosa cade, e la deriva di livello che nessuno cercava](#fase-98--sette-fronti-in-parallelo-cosa-regge-cosa-cade-e-la-deriva-di-livello-che-nessuno-cercava)
- [Fase 99 — La correzione di LIVELLO dei conteggi: il lead della Fase 98 è FALSO (e perché)](#fase-99--la-correzione-di-livello-dei-conteggi-il-lead-della-fase-98-è-falso-e-perché)
### Arco 12 — I cinque campionati, gli audit dell'integrazione, e il recupero applicato (Fasi 100–117)

*Il progetto passa da 3 a **5 leghe** (16.111 partite): Bundesliga e Ligue 1
entrano scaricate e verificate riga per riga contro la fonte-madre, e con loro
nascono le regole sui dati sporchi (Fase 100). Le due leghe nuove non cambiano
le conclusioni, le **replicano**: il modello trasferisce, l'edge no — 5 leghe su
5. Nello stesso arco cade la premessa GG/NG (le quote esistevano) e si scopre
che l'integrazione in `main` aveva portato 32 script che non partivano (Fase
101). Le tre fasi seguenti sono di **manutenzione della verità**: il
numero-bandiera rimisurato dopo un fix mai propagato (+0.0167, non +0.0165),
quattro conclusioni declassate senza che un solo calcolo fosse sbagliato (Fase
101-bis), i numeri orfani e le trappole che colpivano chi verifica (Fase
101-ter). Poi la Fase 103 applica un lavoro lasciato a metà da R4 (cantiere
isolato): i 3.045 righe di calendario di coppa raccolte da Wikipedia alla Fase
100 vengono finalmente unite ai calendari di club, chiudendo i 1.603 falsi
zero di `midweek_europe` — verificati a cella esatta contro l'oracolo già
pubblicato, zero regressioni. La Fase 104 chiude l'ultimo lotto di richieste
utente aperte sui dati: il bug di codice del Monaco (MCO), 8 righe di
calendario duplicate emerse dallo stesso merge (data giusta da Wikipedia +
data sbagliata di openfootball, mai dedotta perché il dedup guarda anche la
data), tre rilievi dell'audit già chiusi ma mai spuntati come tali (F12-04,
F12-05, F12-09), e la scoperta che la fonte xG Understat aveva lo STESSO
mirror morto di football-data ma non era mai stata corretta di conseguenza —
corretta, e i 2 buchi xG residui ri-verificati LIVE (nessuno si è risolto col
tempo, ma ora lo sappiamo con certezza invece che per estrapolazione). Esito
Le Fasi 105-108 ricercano tre volte ancora la chiusura O/U 2017-19, sempre
negativo, ma il confronto esteso a 6 stagioni (Fase 106) mostra che il numero
su cui poggiava la decisione non è stabile nel tempo. Le Fasi 109-115 aprono il
fronte **Betfair Exchange** — il primo candidato migliore della stima — e lo
ridimensionano due volte su richiesta dell'utente, fino a scoprire che la borsa
che serviva (Smarkets) era già in casa e gratis. La Fase 116 mette in piedi il
raccoglitore Smarkets pre-partita a costo zero, prima della scadenza del 16
agosto. La Fase 117 allinea ogni file del repo alle
analisi accumulate e scrive la voce di diario che alla Fase 101-bis non era
mai stata scritta. **Chiude l'arco la Fase 118**, che accende il raccoglitore
per la prima volta e scopre che un run *verde* non stava raccogliendo niente:
la finestra a 72 ore lo teneva fermo fino a tre giorni dal via, e «nessuna
partita» era indistinguibile da «l'API non ci parla più». Esito dell'arco:
nessun edge nuovo, e un repo che dice di sé la verità, coi dati che aveva
promesso di correggere corretti davvero — comprese le correzioni delle
correzioni.*

- [Fase 100 — Cinque leghe: l'audit riga-per-riga, il dato che si credeva perduto, e la premessa che cade](#fase-100--cinque-leghe-laudit-riga-per-riga-il-dato-che-si-credeva-perduto-e-la-premessa-che-cade)
- [Fase 101 — Quinto audit: le ultime 20 fasi e l'integrazione che non era stata eseguita](#fase-101--quinto-audit-le-ultime-20-fasi-e-lintegrazione-che-non-era-stata-eseguita)
- [Fase 101-bis — Applicare le correzioni dell'audit: quattro conclusioni declassate, e il numero-bandiera rimisurato](#fase-101-bis--applicare-le-correzioni-dellaudit-quattro-conclusioni-declassate-e-il-numero-bandiera-rimisurato)
- [Fase 101-ter — Chiudere i punti aperti: i numeri orfani, e tre trappole che colpivano CHI VERIFICA](#fase-101-ter--chiudere-i-punti-aperti-i-numeri-orfani-e-tre-trappole-che-colpivano-chi-verifica)
- [Fase 103 — Il recupero Wikipedia applicato: chiusi i 1.603 falsi zero di `midweek_europe`](#fase-103--il-recupero-wikipedia-applicato-chiusi-i-1603-falsi-zero-di-midweek_europe)
- [Fase 104 — Il resto della lista: Monaco, DFB-Pokal, tre rilievi già chiusi, e la fonte xG con lo stesso mirror morto](#fase-104--il-resto-della-lista-monaco-dfb-pokal-tre-rilievi-gia-chiusi-e-la-fonte-xg-con-lo-stesso-mirror-morto)
- [Fase 105 — Secondo ri-tentativo sull'O/U 2017-19: quattro angoli nuovi, ancora negativo](#fase-105--secondo-ri-tentativo-sullou-2017-19-quattro-angoli-nuovi-ancora-negativo)
- [Fase 106 — Il confronto footiqo-vs-verità esteso da 1 a 6 stagioni: non è stabile nel tempo](#fase-106--il-confronto-footiqo-vs-verità-esteso-da-1-a-6-stagioni-non-è-stabile-nel-tempo)
- [Fase 107 — Terzo ri-tentativo sull'O/U 2017-19: ri-verifica dal vivo + angoli nuovi, ancora negativo](#fase-107--terzo-ri-tentativo-sullou-2017-19-ri-verifica-dal-vivo--angoli-nuovi-ancora-negativo)
- [Fase 108 — «E se cercassimo partita per partita?» — testato, non scala](#fase-108--e-se-cercassimo-partita-per-partita-testato-non-scala)
- [Fase 109 — Betfair Exchange: il primo candidato MIGLIORE della stima (e una mia valutazione ritirata)](#fase-109--betfair-exchange-il-primo-candidato-migliore-della-stima-e-una-mia-valutazione-ritirata)
- [Fase 109-bis — La specifica ufficiale trova un bug nel parser (poche ore dopo)](#fase-109-bis--la-specifica-ufficiale-trova-un-bug-nel-parser-poche-ore-dopo)
- [Fase 110 — La documentazione Betfair entra nel repo (e smentisce una mia costante)](#fase-110--la-documentazione-betfair-entra-nel-repo-e-smentisce-una-mia-costante)
- [Fase 111 — Il token, i vincoli veri, e cosa possiamo davvero farci con Betfair](#fase-111--il-token-i-vincoli-veri-e-cosa-possiamo-davvero-farci-con-betfair)
- [Fase 112 — Un solo scarico per due piste (e un refactor che un test ha bocciato)](#fase-112--un-solo-scarico-per-due-piste-e-un-refactor-che-un-test-ha-bocciato)
- [Fase 113 — «Quanto serve davvero?» — il ridimensionamento di una mia raccomandazione](#fase-113--quanto-serve-davvero--il-ridimensionamento-di-una-mia-raccomandazione)
- [Fase 114 — Far usare le stime davvero (e una mia frase da correggere)](#fase-114--far-usare-le-stime-davvero-e-una-mia-frase-da-correggere)
- [Fase 115 — «Serve un PC cloud 24/7?» — no: la borsa che serviva era già in casa](#fase-115--serve-un-pc-cloud-247--no-la-borsa-che-serviva-era-già-in-casa)
- [Fase 116 — Il raccoglitore prospettico è in piedi (e costa zero)](#fase-116--il-raccoglitore-prospettico-è-in-piedi-e-costa-zero)
- [Fase 117 — Ogni file allineato: il merge con una sessione parallela, e l'identità che chiude la COM-Poisson](#fase-117--ogni-file-allineato-il-merge-con-una-sessione-parallela-e-lidentità-che-chiude-la-com-poisson)
- [Fase 118 — Il primo giro vero del raccoglitore: verde, e non raccoglieva niente](#fase-118--il-primo-giro-vero-del-raccoglitore-verde-e-non-raccoglieva-niente)
- [Fase 119 — La raccolta quotidiana 2026-27: il piano, e i due `robots.txt` che lo riscrivono](#fase-119--la-raccolta-quotidiana-2026-27-il-piano-e-i-due-robotstxt-che-lo-riscrivono)
- [Fase 120 — Il passo 0: metà della lista era già in casa, su licenza](#fase-120--il-passo-0-metà-della-lista-era-già-in-casa-su-licenza)
- [Fase 121 — Le rose vere: Wikipedia riempie i buchi, ma non tutti (e l'ipotesi era sbagliata)](#fase-121--le-rose-vere-wikipedia-riempie-i-buchi-ma-non-tutti-e-lipotesi-era-sbagliata)
- [Fase 122 — Lo scheletro giornaliero: una fetta sottile ma completa](#fase-122--lo-scheletro-giornaliero-una-fetta-sottile-ma-completa)
- [Fase 123 — Lo stadio non è una proprietà della squadra, e le squalifiche non si cercano](#fase-123--lo-stadio-non-è-una-proprietà-della-squadra-e-le-squalifiche-non-si-cercano)
- [Fase 124 — Il diffidato si trattiene davvero: misurato (e il segno ingenuo era rovesciato)](#fase-124--il-diffidato-si-trattiene-davvero-misurato-e-il-segno-ingenuo-era-rovesciato)
- [Fase 125 — Prezzare i cartellini: ogni leva paga, e la sotto-dispersione non è dei gol](#fase-125--prezzare-i-cartellini-ogni-leva-paga-e-la-sotto-dispersione-non-è-dei-gol)
- [Fase 126 — Cartellini: la contraddizione con la Fase 98 era apparente, e il modello «giusto» non paga](#fase-126--cartellini-la-contraddizione-con-la-fase-98-era-apparente-e-il-modello-giusto-non-paga)
- [Fase 127 — La Liga era uscita dalla raccolta in silenzio: una guardia che scattava solo troppo tardi](#fase-127--la-liga-era-uscita-dalla-raccolta-in-silenzio-una-guardia-che-scattava-solo-troppo-tardi)
- [Fase 128 — Il passo P1: la mappa nomi, e la neopromossa che il modello non sa di avere](#fase-128--il-passo-p1-la-mappa-nomi-e-la-neopromossa-che-il-modello-non-sa-di-avere)
- [Fase 129 — Il test prospettico è congelato: 48 partite, 26 mercati, due settimane di anticipo](#fase-129--il-test-prospettico-è-congelato-48-partite-26-mercati-due-settimane-di-anticipo)
- [Fase 130 — Le quote si muovono? Quasi no. E il movimento più grande era un libro rotto](#fase-130--le-quote-si-muovono-quasi-no-e-il-movimento-più-grande-era-un-libro-rotto)
- [Fase 131 — Le statistiche di squadra per periodo: il primo dato che separa i due tempi](#fase-131--le-statistiche-di-squadra-per-periodo-il-primo-dato-che-separa-i-due-tempi)
- [Fase 133 — I gol all'intervallo entrano negli snapshot: il dato che mancava al modello a due stadi](#fase-133--i-gol-allintervallo-entrano-negli-snapshot-il-dato-che-mancava-al-modello-a-due-stadi)
- [Fase 134 — La borsa rinomina le squadre e il raccoglitore resta verde: il join che si è rotto in silenzio](#fase-134--la-borsa-rinomina-le-squadre-e-il-raccoglitore-resta-verde-il-join-che-si-è-rotto-in-silenzio)
- [Fase 135 — Il listino intero: da 6 mercati a 110, e il batching che lo rende possibile](#fase-135--il-listino-intero-da-6-mercati-a-110-e-il-batching-che-lo-rende-possibile)
- [Fase 136 — Anche il giro giornaliero prende tutto, e l'archivio si comprime](#fase-136--anche-il-giro-giornaliero-prende-tutto-e-larchivio-si-comprime)
- [Fase 137 — I guardiani mancanti: tre difetti che nessun test poteva vedere](#fase-137--i-guardiani-mancanti-tre-difetti-che-nessun-test-poteva-vedere)
- [Fase 138 — Le coppe nazionali entrano nel progetto, e la fonte somma i rigori al risultato](#fase-138--le-coppe-nazionali-entrano-nel-progetto-e-la-fonte-somma-i-rigori-al-risultato)
- [Fase 139 — La controprova arriva: due fonti indipendenti sulla Coppa Italia, zero divergenze](#fase-139--la-controprova-arriva-due-fonti-indipendenti-sulla-coppa-italia-zero-divergenze)
- [Fase 139-bis — I tre ponti, e perché il terzo si regge sul secondo](#fase-139-bis--i-tre-ponti-e-perché-il-terzo-si-regge-sul-secondo)
- [Fase 139-ter — Caso per caso: quattro coppe, due fonti, e il foglio che nessuno guardava](#fase-139-ter--caso-per-caso-quattro-coppe-due-fonti-e-il-foglio-che-nessuno-guardava)
- [Fase 139-quater — Due copie della stessa funzione, e solo una sapeva le cose](#fase-139-quater--due-copie-della-stessa-funzione-e-solo-una-sapeva-le-cose)
- [Fase 139-quinquies — Il secondo consegnato, e un controllo che bocciava il dato buono](#fase-139-quinquies--il-secondo-consegnato-e-un-controllo-che-bocciava-il-dato-buono)
- [Fase 139-sexies — «Lione» non è «Olympique Lyon», e «Red Star» non è di Belgrado](#fase-139-sexies--lione-non-è-olympique-lyon-e-red-star-non-è-di-belgrado)
- [Fase 139-septies — Tre volte lo stesso errore: il controllo che boccia il dato buono](#fase-139-septies--tre-volte-lo-stesso-errore-il-controllo-che-boccia-il-dato-buono)
- [Fase 139-octies — «Le colonne ci sono» non è «si uniscono»](#fase-139-octies--le-colonne-ci-sono-non-è-si-uniscono)
- [Fase 140 — Il database allenatori: il nome non è un'identità, e la panchina non è un contratto](#fase-140--il-database-allenatori-il-nome-non-è-unidentità-e-la-panchina-non-è-un-contratto)
- [Fase 141 — Un 503 alla 22ª partita su 58, e le 21 già raccolte buttate via](#fase-141--un-503-alla-22ª-partita-su-58-e-le-21-già-raccolte-buttate-via)
- [Fase 142 — Prendevamo il 6,7% del listino: coppe, UEFA e cadetterie entrano nel perimetro](#fase-142--prendevamo-il-67-del-listino-coppe-uefa-e-cadetterie-entrano-nel-perimetro)

---

## Fase 0 — Visione e prime scelte di fondo

**Idea di partenza.** Un motore per stimare la **probabilità reale** di eventi
sportivi (calcio), *indipendente dalle piattaforme* (Polymarket, bookmaker,
exchange). Il valore è il modello, non l'integrazione con un sito.

**Scelte chiave discusse e prese:**

- **Modellare la distribuzione dei gol per squadra**, non i singoli mercati.
  Ragionamento: 1X2 e Over/Under non sono eventi indipendenti — derivano entrambi
  da *quanti gol segna ciascuna squadra*. Modellando la matrice
  P(gol_casa = i, gol_ospite = j) si ricavano **tutti** i mercati in modo
  coerente (niente contraddizioni tipo "55% vittoria casa" + "70% Under 2.5"), e
  aggiungere mercati futuri è gratis. Bonus: per il live basterà condizionare la
  stessa distribuzione al minuto e al punteggio.
- **Serie A come binario serio; Mondiali scartati.** I Mondiali hanno poco
  storico, quote efficientissime e troppe poche partite per validare qualcosa:
  scommettere lì "di corsa" non era realistico. Meglio un campionato con dati
  abbondanti.
- **Modello: Dixon-Coles (1997), scritto da noi.** Rispetto alla Poisson pura
  aggiunge una correzione sui punteggi bassi (0-0, 1-0, 0-1, 1-1, più frequenti
  del previsto) e il decadimento temporale. Scritto a mano invece di usare una
  libreria per capirlo e controllarlo a fondo (è il cuore del progetto).
- **Metriche di successo.** *Calibrazione* con Brier score e log-loss; *edge
  reale* col confronto contro le **quote di chiusura** dei bookmaker (lo
  stimatore più efficiente che esista). Traguardo realistico iniziale: battere
  baseline banali ed essere ben calibrati — non "battere il mercato", che è
  impresa da professionisti.
- **Dati: football-data.co.uk** (gratis, include risultati *e* quote di chiusura).

### 📐 Il modello in dettaglio — cosa significa "modellare i gol"

La scelta di fondo ("modellare la distribuzione dei gol per squadra") ha una forma
matematica precisa, presa da Dixon & Coles (1997). Per una partita casa `h` vs
ospite `a`, i gol delle due squadre sono due Poisson i cui tassi attesi sono:

```
λ = E[gol casa]   = exp( att_h + dif_a + γ )
μ = E[gol ospite] = exp( att_a + dif_h )
```

- `att_·` = forza d'attacco della squadra (in **log-scala**), `dif_·` = forza di
  difesa (quanto fa segnare gli altri), `γ` = **vantaggio-casa** globale.
- **Perché la scala esponenziale (log-lineare)?** Tre motivi concreti: (1) garantisce
  `λ, μ > 0` (non esistono gol attesi negativi); (2) rende i contributi *additivi in
  log e moltiplicativi in gol* — una squadra "+0,30 in attacco" segna `e^0.30 ≈ 1,35`
  volte tanto contro *qualsiasi* difesa, coerente con l'intuizione "i forti segnano di
  più contro tutti"; (3) è la parametrizzazione canonica del GLM di Poisson, quindi la
  massima verosimiglianza è ben posta.
- **Perché i gol per squadra e non i mercati direttamente?** Se stimassi 1X2 e O/U con
  due modelli separati potrei ottenere `P(vittoria casa)=55%` **e** `P(Under 2.5)=70%`
  reciprocamente incoerenti. Partendo dalla matrice `P(gol_casa=i, gol_ospite=j)` ogni
  mercato è una *somma di celle* della stessa matrice → coerenza garantita per
  costruzione, e ogni nuovo mercato è gratis (basta sommare le celle giuste).

I valori numerici di `att`, `dif`, `γ`, `ρ` non esistono ancora in questa fase: sono
**stimati dai dati** nella Fase 1 (massima verosimiglianza). Qui è fissata solo la
*forma*; il *perché quei numeri* arriva col primo fit.

---

## Fase 1 — Tracer bullet: Dixon-Coles + backtest

**Obiettivo.** Prima pipeline reale end-to-end su Serie A:
dati → modello → probabilità 1X2 e O/U 2.5 → validazione.

**Ostacolo dati (e soluzione).** L'ambiente cloud **blocca football-data.co.uk**
(policy di rete). Invece di arrenderci, abbiamo trovato un **mirror su GitHub**
con lo stesso identico formato (9 stagioni di Serie A, 380 partite ciascuna, con
quote di chiusura). Fonte tenuta **configurabile in un unico punto**
(`sources.py`) così in locale basta cambiare un URL.

**Metodologia del backtest (per evitare il "barare").** Walk-forward: prima di
ogni giornata si riallena il modello usando **solo** le partite già avvenute, poi
si predice quel turno. Nessun look-ahead: il filtro `data < as_of` garantisce che
non si guardi mai il futuro.

**Risultato (stagione 2025-26, config iniziale):**

| Mercato | Modello | Baseline | Mercato |
|---|---:|---:|---:|
| 1X2 log-loss | 1.0047 | 1.0851 | 0.9784 |

**Lettura.** Il modello **batte la baseline** (impara qualcosa di reale) ma **non
il mercato** — esito atteso e sano per un primo modello. La simulazione di
scommesse dava ROI negativo: onesto e prevedibile. *La pipeline funziona: da qui
si può migliorare con basi solide.*

### 📐 Il modello in dettaglio — tutte le formule del tracer bullet

Questa è la fase in cui il modello passa da *forma* (Fase 0) a *numeri stimati*.
Ecco l'intera catena, come è scritta in `src/models/dixon_coles.py`.

**1) Verosimiglianza pesata (la funzione che il fit minimizza).** I parametri
`{att_i, dif_i, γ, ρ}` sono scelti massimizzando la log-verosimiglianza di Poisson
sui gol osservati, **pesata nel tempo**:

```
ℓ = Σ_partite  w_t · [  (g_h·ln λ − λ)  +  (g_a·ln μ − μ)  +  ln τ(g_h, g_a; λ, μ, ρ)  ]
```

dove `g_h, g_a` sono i gol realmente segnati, e i due termini `(g·ln rate − rate)`
sono il nucleo della Poisson (il fattoriale `ln(g!)` è costante e si può ignorare
nell'ottimizzazione, ma nel codice è incluso per completezza).

**2) Peso temporale `w_t` (decadimento).** Una partita giocata `Δ` giorni prima del
momento della predizione pesa:

```
w_t = exp( −ξ · Δ ),   con   ξ = ln 2 / emivita
```

Così il peso si **dimezza ogni `emivita` giorni**: a emivita 365g una gara di una
stagione fa pesa 0,5, di due stagioni 0,25, di tre 0,125. È il meccanismo con cui
"le squadre cambiano nel tempo" entra nel modello *senza buttare via* i dati vecchi
(li sfuma soltanto). Il valore di emivita è un iperparametro, tarato in Fase 2b.

**3) Correzione Dixon-Coles `τ` sui 4 punteggi bassi.** La Poisson pura sottostima
0-0/1-1 e sovrastima 1-0/0-1; `τ` corregge SOLO quelle 4 celle:

```
τ(0,0) = 1 − λ·μ·ρ      τ(0,1) = 1 + λ·ρ
τ(1,0) = 1 + μ·ρ        τ(1,1) = 1 − ρ         (tutti gli altri punteggi: τ = 1)
```

Con `ρ < 0` (il valore che i dati scelgono, tipicamente −0,04…−0,07): `τ(0,0)` e
`τ(1,1)` diventano **>1** (più massa su 0-0 e 1-1, cioè più pareggi bassi) mentre
`τ(0,1), τ(1,0)` diventano **<1**. È esattamente il "le squadre giocano sul
risultato". `ρ` è stimato *dentro* la verosimiglianza, non imposto.

**4) Identificabilità.** Il modello è invariante se sommo una costante a tutti gli
attacchi e la sottraggo a tutte le difese (`att_i += c`, `dif_i −= c` non cambia
`λ, μ`). Si fissa l'indeterminazione con una penalità che impone **media(attacco) =
0**: `penalità = 10⁴ · media(att)²`. È il motivo per cui "forza 0 = squadra media
della lega".

**5) Dalla matrice ai mercati.** Con `(λ, μ)` stimati si costruisce la matrice
`P(i,j) = Poisson(i; λ) · Poisson(j; μ) · τ(i,j)` (troncata a 10 gol/squadra e
rinormalizzata perché `τ` e il troncamento rompono la somma a 1). Da essa:

```
P(1) = Σ_{i>j} P(i,j)   (triangolo inferiore)      P(X) = Σ_i P(i,i)  (diagonale)
P(2) = Σ_{i<j} P(i,j)   (triangolo superiore)
P(Over 2.5) = Σ_{i+j ≥ 3} P(i,j)                   P(GG) = Σ_{i≥1, j≥1} P(i,j)
```

**6) Come si misura (le metriche).** Log-loss 1X2 = `−media( ln P(esito realizzato) )`
(punisce duramente la sicurezza sbagliata); Brier = `media Σ_k (p_k − y_k)²`.

**Perché quei tre numeri (1.0047 / 1.0851 / 0.9784).**
- Il **mercato (0.9784)** è la log-loss delle quote di chiusura *devigate*: le quote
  1X2 si convertono in probabilità con `p_i = (1/quota_i) / Σ_j(1/quota_j)` (metodo
  moltiplicativo: dividere per la somma toglie il margine del bookmaker, che rende
  `Σ 1/quota > 1`). È lo stimatore più efficiente esistente → il numero da battere.
- La **baseline (1.0851)** è la log-loss del predittore banale costante = frequenze
  empiriche (H,D,A) della stagione. Batterla significa "il modello discrimina le
  singole partite meglio del prezzo medio di lega".
- Il **modello (1.0047)** sta **in mezzo**: `1.0851 > 1.0047 > 0.9784`. Ha già chiuso
  `(1.0851−1.0047)/(1.0851−0.9784) = 75%` della distanza baseline→mercato al primo
  colpo, senza tuning. È il risultato "sano" atteso: impara qualcosa di reale, non
  ancora abbastanza da battere il prezzo.

---

## Fase 2a — Analisi degli errori (e un bug trovato)

**Perché prima di aggiungere feature.** Invece di aggiungere segnali a caso,
abbiamo costruito uno strumento (`analyze.py`) per capire *dove* il modello perde
contro il mercato.

**Scoperte:**

1. **Sulla media il modello è ben calibrato** — nessun bias sistematico, nemmeno
   sui pareggi (difetto tipico dei modelli Poisson, che noi *non* avevamo). Quindi
   il mercato ci batte in **discriminazione** delle singole partite, non in
   calibrazione media.
2. **Bug trovato e corretto.** La stagione di test chiamava il Verona "Hellas
   Verona", le stagioni di training "Verona": il modello lo trattava come squadra
   *sconosciuta* e sparava predizioni assurde (87% a una neopromossa). Risolto con
   una mappa di normalizzazione nomi (`TEAM_ALIASES`). *Questo da solo giustifica
   aver analizzato prima di aggiungere feature.*
3. **Dove perdiamo di più:** partite con **neopromosse** (gap col mercato +0.037,
   doppio della media) e **inizio stagione** (+0.030). Radice comune: dati storici
   scarsi o datati → stime inaffidabili e troppo sicure.

### 📐 Il modello in dettaglio — come si misura "dove si perde"

**Definizione operativa del "gap" (usata da qui fino alla Fase 33).** Per ogni
sottoinsieme di partite S:

```
gap(S) = media_{p ∈ S} [ log-loss_modello(p) − log-loss_mercato(p) ]
```

`>0` = il mercato è più accurato; `≈0` = pari; `<0` = il modello batte il mercato.
Il gap medio globale in questa fase è ~+0.018; sulle **neopromosse è +0.037** (il
doppio) e a **inizio stagione +0.030**. Non sono numeri inventati: sono la stessa
media, ristretta alle righe di quel gruppo.

**Perché "calibrato in media ma battuto in discriminazione".** La calibrazione si
misura a *fasce*: si raggruppano le predizioni per probabilità stimata (es. "partite
dove il modello dà 50-60% alla casa") e si confronta la probabilità media stimata con
la **frequenza reale** in quella fascia. Erano allineate → nessun bias sistematico
(nemmeno sul pareggio, il difetto tipico della Poisson pura, che qui la correzione
`τ` con `ρ<0` già evita). Ma calibrazione ≠ discriminazione: il mercato assegna
probabilità *diverse e più giuste alle singole partite*. Due modelli possono avere la
stessa calibrazione media e log-loss diversa; il gap vive lì.

**Perché il gap esplode sulle neopromosse — il meccanismo del bug e della debolezza
strutturale.** Una squadra **mai vista nel training** riceve `att = dif = 0` (la
media di lega, per la penalità di identificabilità della Fase 1). Due conseguenze:
1. *Il bug degli alias.* Il Verona era `"Verona"` nel training e `"Hellas Verona"`
   nel test: due stringhe diverse → il modello lo trattava come **sconosciuto →
   forza media** invece che come la squadra (debole) che era. Da qui predizioni
   sbilanciate e troppo sicure. Corretto con `TEAM_ALIASES` (mappa di
   normalizzazione). *Nota onesta:* l'esatto "87%" citato dipende dalla singola
   partita e non è ri-derivabile dai dati aggregati qui riportati — è un esempio
   illustrativo del sintomo, non una cifra da registro.
2. *La debolezza vera (non un bug).* Anche con gli alias giusti, una neopromossa con
   0-poche partite di Serie A resta ancorata a `forza ≈ 0` (media), mentre in realtà
   è **sotto** la media (viene dalla B). Il modello la **sovrastima** → gap alto.
   È il problema che le Fasi 2b (shrinkage) e 7 (prior) attaccano direttamente.

---

## Fase 2b — Tuning: regolarizzazione e memoria

Guidati dalla diagnosi, due interventi, **uno alla volta**, validati su più
stagioni.

**1. Shrinkage (regolarizzazione).** Una "molla" che tira le stime di forza verso
la media della lega, più forte quando i dati sono pochi (la penalità è fissa
mentre il contributo dei dati cresce col numero di partite). Attacca proprio
neopromosse e inizio stagione. Tarato → valore ottimo **1.5**. Gap sull'inizio
stagione da +0.030 a +0.022, sulle neopromosse da +0.037 a +0.030: colpisce i
bersagli previsti.

**2. Emivita del decadimento temporale.** Quanto pesare le partite recenti.
Scoperta controintuitiva: l'emivita corta (90g) è la *peggiore*; il modello
preferisce **memoria lunga (~730g, due stagioni)**. Ha senso: in Serie A le rose
restano stabili anno su anno, quindi pesare troppo le ultime partite butta via
segnale.

| Config | log-loss 1X2 | gap col mercato |
|---|---:|---:|
| Dixon-Coles puro (media 2 stagioni) | 0.9918 | +0.026 |
| + shrinkage 1.5 (media 2 stagioni) | 0.9879 | +0.022 |
| + shrinkage, emivita 180g (media 3 stagioni) | 0.9863 | +0.021 |
| + emivita 730g (media 3 stagioni) | **0.9829** | **+0.017** |

*(Mercato: 0.9654 sulle 2 stagioni, 0.9658 sulle 3. Nota audit Fase 15: la
versione precedente di questa tabella attribuiva al "puro" il valore 0.9863 con
gap +0.026 — internamente impossibile; il +0.026 appartiene al valore a 2
stagioni 0.9918, il 0.9863 è la config con shrinkage a emivita 180g.)*

**Risultato:** solo con la taratura abbiamo recuperato **circa un terzo** del
divario col mercato, senza informazione nuova. Ma il modello sui *soli gol* è ora
vicino al suo tetto.

### 📐 Il modello in dettaglio — le formule di shrinkage ed emivita

**1) Lo shrinkage è una penalità L2 nella verosimiglianza.** Il fit ora minimizza
`−ℓ + penalità`, dove (con bersaglio 0 = media di lega in questa fase):

```
penalità_shrinkage = s · ( Σ_i att_i²  +  Σ_i dif_i² )
```

con `s` = forza dello shrinkage (l'iperparametro tarato). È letteralmente una molla
che tira ogni forza verso 0.

**Perché è AUTOMATICAMENTE più forte sulle squadre con pochi dati** (il punto
cruciale). La forza di una squadra è stimata bilanciando due termini: il contributo
dei *suoi dati* (che nella verosimiglianza pesa in proporzione al **peso totale delle
sue partite** `n_i = Σ w_t`) contro la penalità fissa `s`. L'attrazione verso 0 vale
in pratica `≈ s / (s + n_i)`: per una squadra con **tante** partite `n_i ≫ s` → quasi
nessuno shrinkage (i dati vincono); per una **neopromossa / inizio stagione**
`n_i` piccolo → la penalità domina → la stima è tirata verso la media. *Non serve
codice speciale per le squadre con pochi dati: la stessa penalità fissa produce
l'effetto giusto.* È il motivo per cui lo shrinkage "attacca proprio neopromosse e
inizio stagione", visibile nei gap: inizio stagione +0.030→+0.022, neopromosse
+0.037→+0.030.

**Perché `s = 1.5`.** Non c'è formula chiusa: `s` è scelto per **griglia**, cercando
il valore che minimizza la log-loss 1X2 walk-forward mediata su più stagioni. Troppo
basso → non regolarizza (varianza alta sulle squadre incerte); troppo alto → schiaccia
anche le forze ben stimate verso la media (bias). Il minimo empirico è `1.5` (vedi
anche lo sweep piatto 0.75–1.5 della Fase 8).

**2) Perché la MEMORIA LUNGA (emivita ~730/365g) batte quella corta (90–180g).** È un
compromesso bias-varianza sul **campione efficace**:

```
N_eff = (Σ w_t)² / Σ w_t²     (numero "effettivo" di partite che entrano nella stima)
```

Un'emivita corta concentra il peso su poche gare recenti → `N_eff` piccolo → stime
**rumorose** (alta varianza). Un'emivita lunga usa più storia → `N_eff` grande →
stime stabili. Il rischio della memoria lunga sarebbe il *bias* (usare dati non più
rappresentativi), ma **in Serie A le rose restano stabili anno su anno**, quindi i
dati vecchi sono ancora informativi: il bias è piccolo e la riduzione di varianza
domina. Ecco perché il dato *preferisce* 730g e l'emivita corta 90g è la peggiore.
(Coerente con la Fase 25, dove tagliare NETTO i dati vecchi peggiora ancora di più.)

---

## Fase 3 — Informazione nuova: i tiri in porta (risultato NEGATIVO)

**Ipotesi.** I gol sono rumorosi (fortuna sotto porta). I **tiri in porta**
misurano le occasioni con meno rumore — un "xG dei poveri" — e sono già nella
nostra fonte dati. Forse aiutano.

**Come l'abbiamo testato (scelta elegante).** Invece di scegliere a tavolino tra
"solo gol" e "solo tiri", abbiamo costruito la **forma generale**: si allena un
modello sui gol e uno sui tiri, e si **mescolano** i tassi attesi con un peso α
tarabile (`shots_blend`). α=1 = solo gol (modello attuale); α=0 = solo tiri;
intermedio = miscela. Così B ("solo tiri") è semplicemente il caso α=0, testato
*gratis* dentro lo stesso tuning — niente da indovinare, decide il dato.

**Esito, validato su SEI stagioni** (2020-21 → 2025-26, regimi diversi, COVID
inclusi):

| α (peso gol) | 1X2 (media) | O/U 2.5 (media) |
|---:|---:|---:|
| 0 (solo tiri) | 0.9913 | 0.6964 |
| 0.5 | 0.9833 | 0.6909 |
| **1 (solo gol)** | **0.9817** | **0.6904** |

**Conclusione: i tiri in porta *grezzi* non aiutano in modo affidabile.** Su 3
stagioni sembrava esserci un vantaggio sull'Over/Under, ma **si è dissolto su 6**:
era rumore di piccolo campione (allargare il backtest — su suggerimento giusto —
ha *chiarito* il quadro).

**Nota tenuta agli atti.** Nella stagione più recente (2025-26) dare peso ai tiri
*migliora* l'Over/Under: ipotesi che lo stile di gioco stia cambiando e le
occasioni diventino via via più informative. Da ri-verificare.

**Perché è comunque un buon risultato.** Aver testato la versione *economica*
dell'idea "le occasioni aiutano" ci ha **evitato** di costruire una pipeline
xG/database sull'assunzione — sbagliata — che bastassero i tiri grezzi. Il codice
del blend resta, pronto per l'**xG reale** (che pesa la *qualità* delle occasioni,
non solo il conteggio).

### 📐 Il modello in dettaglio — la formula del blend e perché α=1

**Come funziona il blend (la "forma generale" citata).** Si allena un secondo
modello identico al primo ma sui **tiri in porta** invece che sui gol (stessa
struttura attacco/difesa/vantaggio-casa, ma **senza** la correzione `τ`: `ρ=0`, perché
i tiri sono un conteggio ad alto volume che non ha il fenomeno "0-0 più frequente").
I due tassi attesi si **mescolano** con un peso `α = shots_blend`:

```
λ = α · λ_gol  +  (1−α) · λ_tiri · c_home
μ = α · μ_gol  +  (1−α) · μ_tiri · c_away
```

Il **fattore di conversione** riporta i tiri sulla scala dei gol (un tiro in porta
non è un gol):

```
c = Σ w_t · gol  /  Σ w_t · tiri     (pesato nel tempo, per casa e ospite)
```

Per i tiri `c ≈ 0.3` (servono ~3 tiri in porta per un gol); per l'xG (Fase 4b) `c ≈ 1`
(l'xG è già in scala gol). `α=1` = solo gol (modello classico); `α=0` = solo tiri.

**Perché α=1 vince (i tiri grezzi non aiutano).** L'esperimento è un semplice sweep di
`α` che sceglie il valore con log-loss minima su 6 stagioni. Il risultato: `α=1`
(0.9817 su 1X2) < `α=0.5` (0.9833) < `α=0` (0.9913). Interpretazione: i tiri in porta
**contano le occasioni ma non ne pesano la qualità** — un tiro debole da 30 metri e
un colpo di testa a porta vuota valgono uguale. Aggiungere quel segnale sostituisce
rumore-gol con rumore-tiri, senza guadagno netto. L'illusione di un vantaggio su O/U
a 3 stagioni **spariva** allargando a 6 (`N` raddoppia, l'errore standard `∝ 1/√N`
si dimezza e il falso segnale rientra nel rumore): è la ragione per cui la regola
"valida su più stagioni" esiste. Il meccanismo era giusto, mancava la *qualità* del
segnale — che l'xG fornisce.

---

## Infrastruttura — Tracciabilità e database interno

Man mano che gli esperimenti si accumulavano, sono diventate necessarie due
fondamenta:

**1. Registro degli esperimenti** (`experiments/runs.jsonl`). Ogni backtest scrive
un record con **configurazione + metriche + commit git + impronta dei dati +
data**. Così ogni numero è replicabile e verificabile da terzi. Il calcolo delle
metriche è centralizzato in una **fonte di verità unica** (`compute_metrics`).

**2. Archivio dati interno.** Per non dipendere dalla disponibilità *live* di un
mirror esterno (che può cambiare o sparire):
- **snapshot** `data/serie_a_matches.csv` — versionato in git, testo diffabile:
  la fonte di verità *congelata* (chi clona il repo ha gli stessi dati, senza
  rete);
- **database SQLite** `data/football.db` — queryable, rigenerabile dallo snapshot.

La pipeline è **offline-first**: i backtest leggono lo snapshot congelato, quindi
i risultati sono riproducibili identici.

### 📐 In dettaglio — non è modello, ma è ciò che rende i numeri fidati

Questa sezione non ha formule del modello (le metriche vivono in `metrics.py`, vedi il
blocco della Fase 1); ha però due meccanismi *quantitativi* che garantiscono ogni
numero di questo diario:

- **Fonte di verità unica per le metriche** (`compute_metrics`): log-loss, Brier e
  devig sono calcolati in **un solo** punto, così ogni fase misura con lo stesso metro
  (l'audit di Fase 15 le ha ricontrollate tutte).
- **Impronta dei dati** (`8483944342fc8b15`): un hash calcolato **solo** su
  date/squadre/gol (l'input del modello-gol). Ogni run in `runs.jsonl` la registra →
  se cambia, i dati sotto sono cambiati e i confronti tra fasi non sarebbero validi.
  È il motivo per cui aggiungere colonne (xG, valori rosa, calendario) **non** rompe la
  riproducibilità: non entrano nell'impronta.

Insieme (registro + impronta + `compute_metrics`) sono l'infrastruttura che permette
di dire "ogni numero è ricalcolabile da terzi" — la premessa di tutto il resto.

---

## Dove siamo — cosa sappiamo con onestà

**Il modello NON è scarso a predire.** Indovina il segno giusto dell'1X2 il
**52.6%** delle volte, contro il **53.9%** del mercato: un solo punto di distanza,
e nel 92% dei casi scegliamo lo stesso favorito. Il calcio è caotico: nessuno fa
molto meglio del ~54%.

**Ma non batte il mercato**, e questo ha un significato preciso. "Battere il
mercato" = produrre probabilità *più accurate* delle quote di chiusura. Quando ci
discostiamo dal mercato, ha ragione lui più spesso di noi (siamo più vicini al
vero solo nel 43% delle partite). Per *guadagnare* scommettendo servirebbe essere
più accurati del mercato di *almeno* il suo margine (~5%): siamo un pelo *meno*
accurati, quindi ogni "value bet" è quasi sempre un nostro errore travestito da
opportunità → ROI simulato negativo.

**Conseguenza pratica:** allo stato attuale il modello **non va usato per
scommettere soldi veri**. È un motore pulito, calibrato e onesto che *approssima*
il mercato senza superarlo.

### 📐 In dettaglio — cosa vogliono dire quei numeri

- **52.6% vs 53.9% (accuratezza del segno 1X2).** È la frazione di partite in cui
  `argmax(P_casa, P_pari, P_ospite)` coincide con l'esito reale. Un solo punto di
  distanza, e nel 92% dei casi il favorito scelto è lo stesso → il modello e il
  mercato "vedono" quasi le stesse partite; la differenza non è *chi* è favorito ma
  *quanto*.
- **"più vicini al vero solo nel 43%".** È la frazione di partite in cui la log-loss
  del modello è **minore** di quella del mercato, cioè in cui il modello ha dato
  all'esito realizzato una probabilità *più alta*. 43% < 50% ⇒ quando i due
  dissentono, ha ragione il mercato più spesso. (La Fase 20 spiega *perché* i
  dissensi del modello sono i suoi errori: adverse selection.)
- **Il "margine ~5%" e perché serve batterlo.** Le quote implicano `Σ 1/quota > 1`;
  l'eccesso (`overround`) è il margine del bookmaker, ~5% sull'1X2 di Serie A. Per
  *guadagnare* non basta essere accurati quanto il mercato: bisogna esserlo **più**
  del margine. Essendo un filo *meno* accurati, ogni "value bet" è quasi sempre un
  nostro errore → ROI simulato negativo. È la traduzione quantitativa di "non
  scommettere".

---

## Fase 4a — I dati per l'xG reale (e per le rose): arricchimento completato

**Obiettivo.** Prima di ri-tarare il modello con l'xG (Fase 4), servivano i
dati: xG per *ogni* partita storica, valori rosa a inizio stagione e una stima
delle assenze. Tutto nello snapshot congelato, offline-first, senza toccare la
base football-data.

**Ragionamento e alternative.**
- *xG*: understat.com e fbref.com non sono raggiungibili da questo ambiente
  (proxy). Alternativa trovata: lo **stesso repo mirror** GitHub gia' usato per
  football-data espone anche i JSON di lega Understat (aggiornati da un workflow
  giornaliero). Verificato: 380/380 partite con xG per tutte e 9 le stagioni.
- *Valori rosa*: transfermarkt.com non raggiungibile; nessuna tabella con valori
  rosa per squadra-stagione nei datalake GitHub esplorati. Scelta: ricostruzione
  **bottom-up** = rosa stimata dai giocatori con minuti su Understat + ultima
  valutazione Transfermarkt (datalake `salimt/football-datasets`) **antecedente
  al 1° settembre** della stagione (niente look-ahead, staleness max 550 giorni).
- *Assenze*: dalla tabella infortuni dello stesso datalake, contando per ogni
  partita i giocatori della rosa infortunati in quella data (informazione nota
  pre-partita). Sono **stime**, marcate col suffisso `_est`.

**Il problema vero: allineare i nomi.** Squadre: bastano 3 alias
(`AC Milan`→`Milan`, `Parma Calcio 1913`→`Parma`, `SPAL 2013`→`Spal`).
Giocatori: molto piu' duro (accenti, translitterazioni, "Gian Marco"/"Gianmarco",
nomi accorciati). Catena deterministica di aggancio misurata su 1.986 giocatori:
esatto 1691, filtro ruolo/valutazioni 96, spareggio per valore di picco 63,
senza-spazi 3, sottoinsiemi di token 21, cognome+iniziale 29, fuzzy conservativo
(soglia 0.90) 8, **non agganciati 78** (~4%, quasi tutti con pochi minuti).

**Risultato.**
- 14 nuove colonne nello snapshot (3420 righe invariate, impronta dati
  invariata `8483944342fc8b15` perche' calcolata solo su date/squadre/gol):
  `home_xg, away_xg, home_npxg, away_npxg, home_ppda, away_ppda, home_deep,
  away_deep, home_squad_value, away_squad_value, home_absent_count_est,
  away_absent_count_est, home_absent_value_est, away_absent_value_est`.
- Copertura xG: **100% in tutte le stagioni**. Copertura valori rosa (entrambe
  le squadre): 63-80% a seconda della stagione.
- Backtest di non-regressione: metriche **identiche** a quelle documentate
  (log-loss 1X2 0.9890 / baseline 1.0851 / mercato 0.9784).

**Limite onesto (documentato, non aggirato).** Il datalake Transfermarkt e'
incompleto: ~25% dei profili **non ha alcuna serie di valutazioni** (mancano
anche titolari, es. Milinkovic-Savic; la Lazio ne soffre in tutte le stagioni).
Politica: il valore rosa e' pubblicato **solo** se i giocatori valutati coprono
almeno l'85% dei minuti della squadra, altrimenti `NaN`. **Niente imputazioni**:
meglio un buco dichiarato che un numero inventato. Le assenze restano stime
(`_est`) perche' rosa e infortuni derivano da fonti ricostruite.

**Lezione.** Con vincoli di rete stretti, il collo di bottiglia non e' il
modello ma la *provenienza* dei dati: trovare mirror affidabili e allineare i
nomi tra fonti vale piu' di qualunque raffinatezza statistica a valle.

### 📐 In dettaglio — le soglie e perché quei valori (non è modello, è provenienza)

Questa fase non introduce formule del modello, ma **decisioni quantitative** sui
dati, ognuna con un perché preciso:

- **Look-ahead sui valori rosa: cutoff al 1° settembre.** Si prende l'ultima
  valutazione Transfermarkt **antecedente al 1° settembre** della stagione. Motivo:
  è informazione *nota prima* che la stagione conti davvero; usare valori aggiornati
  a gennaio sarebbe guardare il futuro. Staleness massima ammessa **550 giorni** (se
  l'ultima valutazione è più vecchia, il dato è troppo datato per fidarsi).
- **Soglia dell'85% dei minuti per pubblicare il valore-rosa.** Il valore squadra è
  la somma dei valori dei giocatori agganciati; si pubblica **solo se i giocatori
  valutati coprono ≥85% dei minuti stagionali** della squadra, altrimenti `NaN`.
  Perché una soglia e non un'imputazione: con un datalake incompleto (~25% dei
  profili senza serie di valutazioni, es. Milinkovic-Savic/Lazio), riempire i buchi
  con una media *inventerebbe* forza; un buco dichiarato (`NaN` → covariata neutra)
  è onesto. Politica: **niente imputazioni, mai un numero inventato.**
- **La catena di aggancio dei nomi è deterministica e ordinata** (dal più sicuro al
  più permissivo), misurata su 1.986 giocatori: esatto 1691 → filtro ruolo 96 →
  spareggio per valore di picco 63 → senza-spazi 3 → sottoinsiemi di token 21 →
  cognome+iniziale 29 → fuzzy con soglia **0.90** 8 → **non agganciati 78 (~4%)**.
  La soglia fuzzy 0.90 è volutamente alta (conservativa): meglio lasciare 78 giocatori
  non agganciati (quasi tutti con pochi minuti, impatto trascurabile) che agganciare
  la persona sbagliata.
- **Perché l'impronta dati resta invariata (`8483944342fc8b15`).** L'impronta è
  calcolata **solo** su date/squadre/gol (l'input del modello-gol), non sulle nuove
  colonne: aggiungere xG/valori/assenze non tocca la riproducibilità dei backtest
  già registrati → il backtest di non-regressione dà metriche **identiche**.

---

## Fase 4b — xG reale nel blend: primo miglioramento da dati nuovi

**Obiettivo.** Rifare l'esperimento del blend della Fase 3 (fallito coi tiri
grezzi) usando l'**xG reale** ora disponibile: le occasioni pesate per qualita'
aiutano dove i tiri grezzi non aiutavano?

**Ragionamento e scelta.** L'infrastruttura c'era gia': abbiamo generalizzato il
blend a un `blend_signal` qualsiasi ("sot"=tiri, "xg"=xG, "npxg"). L'xG e' gia' in
scala gol (la conversione risulta ~1, contro ~0.3 dei tiri). Il modello sull'xG
usa lo stesso `_fit_counts` (Poisson-famiglia su valori continui, senza la
correzione sui punteggi bassi).

**Risultato (6 stagioni, log-loss).**

| α (peso gol) | 1X2 | O/U 2.5 |
|---:|---:|---:|
| 0 (solo xG) | 0.9840 | 0.6897 |
| 0.5 | 0.9816 | 0.6888 |
| **0.75** | **0.9813** | 0.6893 |
| 1 (solo gol) | 0.9817 | 0.6904 |

- **Primo segnale che aggiunge valore.** Dove i tiri grezzi fallivano, l'xG
  aiuta: piccolo, ma reale e consistente, soprattutto sull'Over/Under (la qualita'
  delle occasioni informa il volume di gol; sull'1X2 conta meno chi *crea*, piu'
  chi *concretizza*).
- **Scelta config: α = 0.75** (blend_signal xg). Migliora *entrambi* i mercati
  sulla media a 6 stagioni ed e' conservativa. Presa sulla media, non su una
  stagione: sul solo 2025-26 l'1X2 e' appena sotto (0.9900 vs 0.9890) ma l'O/U
  migliora — variabilita' attesa.

**Lezione.** La *qualita'* del segnale conta piu' del segnale in se': stessa idea
("le occasioni aiutano"), stesso meccanismo, ma coi tiri grezzi -> nulla, con
l'xG -> primo passo avanti. Conferma anche l'ipotesi tenuta agli atti: i guadagni
O/U piu' grandi sono nelle stagioni recenti (stile di gioco in evoluzione).

**Onestà.** Il miglioramento e' modesto e non basta a battere il mercato. Restano
da spremere gli altri dati gia' disponibili (npxG, valori rosa, assenze).

### 📐 Il modello in dettaglio — stessa formula dei tiri, segnale migliore

La meccanica è **identica** alla Fase 3 (stessa formula di blend), cambia solo il
segnale secondario: `blend_signal = "xg"` invece di `"sot"`.

```
λ = α · λ_gol  +  (1−α) · λ_xg · c_home        (idem per μ)
c = Σ w·gol / Σ w·xg  ≈  1     (l'xG è GIÀ in scala gol; per i tiri era ~0.3)
```

**Perché l'xG aiuta dove i tiri no.** L'xG **pesa la qualità** di ogni occasione
(probabilità di gol di quel tiro dato posizione/tipo), non la conta e basta. È un
"conteggio di gol attesi" con meno rumore dei gol realizzati (che dipendono dalla
fortuna sotto porta) e con più informazione dei tiri grezzi (che ignorano la
qualità). Il fatto che `c ≈ 1` conferma che è già la grandezza giusta.

**Perché α = 0.75 (e non 0 né 1).** È il valore che minimizza la log-loss **media a
6 stagioni su ENTRAMBI i mercati** (1X2 0.9813 a α=0.75 vs 0.9817 a α=1; l'O/U
migliora già a α più bassi). La scelta è **conservativa**: `0.75` dà ancora il peso
maggiore ai gol (il segnale "duro", ciò che conta davvero), usando l'xG come
correzione del rumore realizzativo, non come sostituto. Presa sulla *media* e non su
una stagione singola (sul solo 2025-26 l'1X2 è appena sotto) proprio per non
inseguire il rumore di piccolo campione — la lezione della Fase 3. È il primo segnale
che aggiunge valore reale e consistente, soprattutto su O/U (la qualità delle
occasioni informa il *volume* di gol più di *chi* vince).

---

## Fase 4c — Spremere il resto dei dati: npxG, valori rosa, assenze (NEGATIVO)

**Obiettivo.** Sfruttare al massimo i dati gia' in casa prima di cercarne altri:
npxG come segnale, e valori rosa / assenze come **covariate** (forza/contesto
esterni ai risultati), anche in **combinazione** (l'idea: due segnali deboli da
soli potrebbero valere di piu' insieme).

**Cosa abbiamo costruito.** Un **layer di covariate** generale: ogni covariata
entra nel tasso atteso della squadra che segna come `beta*(z_squadra -
z_avversaria)`, con i `beta` stimati **insieme** al resto via ML. Piu' covariate =
fit congiunto (cattura il contributo reciproco). Retrocompatibile.

**Metodo onesto.** Prima un diagnostico *economico* in-sample sul valore-rosa:
segnale residuo apparente (coeff +0.48). Ma il test vero e' walk-forward.

**Risultati (6 stagioni, log-loss).**

| | 1X2 | O/U 2.5 |
|---|---:|---:|
| baseline (config Fase 4b) | **0.9813** | 0.6893 |
| npxG al posto di xG | 0.9811 | 0.6892 |
| + valore-rosa | 0.9818 | 0.6891 |
| + assenze | 0.9813 | 0.6893 |
| + valore-rosa & assenze | 0.9818 | 0.6892 |

- **npxG ≈ xG** (differenza 0.0002, entro il rumore): tenuto xG, piu' standard.
- **Valore-rosa: non aiuta** (peggiora appena l'1X2). Il diagnostico in-sample era
  ottimistico: la forza della rosa e' **gia' catturata** dal modello gol+xG (si
  vede nei risultati e nell'xG). Fuori campione aggiunge piu' rumore che segnale.
- **Assenze: effetto nullo** (dato stimato e rumoroso; gli infortuni sono in parte
  gia' nei risultati recenti che il decadimento pesa).
- **Nessuna sinergia** dalle combinazioni: unire segnali ~nulli da' ~nulla.
- **Riposo/congestione (solo Serie A): non aiuta** (1X2 0.9817 vs 0.9813).
  Motivo: calcolato dalle sole date di Serie A, NON vede coppe/Europa/nazionali —
  proprio le partite che causano fatica asimmetrica. Quando tutta la lega gioca
  infrasettimana, il riposo e' basso per entrambe -> la *differenza* e' ~0. Il
  layer covariate "rest" resta: con un **calendario di club completo** (dato
  nuovo) calcolerebbe la congestione vera. E' l'unico segnale "indipendente dai
  risultati" rimasto con potenziale, ma va reperito.

**Lezione.** Con questa fonte dati il modello ha raggiunto il suo **tetto
pratico**: gol + xG + taratura. I dati extra (rosa, assenze) non aggiungono
segnale *indipendente* out-of-sample perche' cio' che contengono e' gia' implicito
nei risultati. Il diagnostico in-sample va sempre confermato walk-forward.

**Config (dopo la Fase 4d):** emivita 365g, shrinkage 1.5, blend gol/xG α=0.75,
nessuna covariata. Il layer covariate resta (documentato, off di default),
riutilizzabile per dati futuri davvero indipendenti (es. formazioni ufficiali
last-minute, meteo, motivazione).

### 📐 Il modello in dettaglio — la formula delle covariate

Ogni covariata entra nel **log-tasso** della squadra che segna come vantaggio
*relativo* rispetto all'avversaria. Il termine aggiunto al tasso di CASA è:

```
cov = Σ_k  β_k · ( z_casa,k − z_ospite,k )          → λ = exp(… + cov)
                                                     → μ = exp(… − cov)   (segno opposto)
```

dove `z` è il valore per-squadra **standardizzato** sul training:

```
z = ( trasforma(valore) − media ) / dev.std
```

Le trasformazioni sono scelte per la natura del dato: `squad_value → log` (i valori
rosa spaziano su ordini di grandezza), `absence → log1p` (conteggio/valore ≥0, log1p
gestisce lo zero), `rest → identity` (già in giorni). Valori mancanti → `z=0`
(covariata **neutra**, non penalizzante). I coefficienti `β_k` sono stimati
**insieme** a tutto il resto nella stessa verosimiglianza (fit congiunto), con
`β ∈ [−1, 1]`. Un `β<0` significa "più valore relativo → segna di **meno**": è il
segno atteso per le assenze (più assenze pesanti → meno gol).

**Perché il valore-rosa NON aiuta (nonostante il diagnostico in-sample +0.48).** Il
coefficiente in-sample positivo dice solo che squadre di valore alto segnano di più
*nei dati già visti* — ma quella forza **è già catturata** dal modello gol+xG (una
squadra costosa segna di più e ha xG più alto, e il modello lo vede). Fuori campione
la covariata non aggiunge informazione *indipendente*: aggiunge solo il rumore della
sua stima → l'1X2 peggiora appena (0.9813→0.9818). È la lezione centrale: **un
diagnostico in-sample va sempre confermato walk-forward.**

**Perché il riposo solo-Serie-A dà ~0.** La covariata entra come *differenza*
`z_casa − z_ospite`. Quando tutta la lega gioca infrasettimana, il riposo cala per
**entrambe** → la differenza è ~0 → nessun effetto. E il calendario di sola Serie A
**non vede** coppe/Europa/nazionali, cioè proprio le partite che causano fatica
*asimmetrica*. Questo motiva la Fase 4e (calendario di club completo): il segnale
esiste solo se la sorgente del calendario è completa.

---

## Fase 4d — Ri-taratura congiunta: l'emivita si accorcia col blend xG

**Obiettivo.** Shrinkage ed emivita erano stati tarati (Fase 2b) sul modello
*solo-gol*. Con il blend xG (Fase 4b) attivo, l'ottimo potrebbe essere cambiato:
interazione mai verificata. Ri-taratura a coordinate su 6 stagioni, alla config
attuale (blend xG 0.75).

**Risultato.** Lo shrinkage resta buono a 1.5. L'**emivita ottima si sposta da
730g a ~365g** (una stagione): rifinita, minimo netto a 365 per *entrambi* i
mercati.

| emivita | 1X2 | O/U 2.5 |
|---:|---:|---:|
| 730 (vecchia) | 0.9813 | 0.6893 |
| **365 (nuova)** | **0.9807** | **0.6884** |

**Lezione.** Con un segnale meno rumoroso (l'xG), il modello puo' permettersi una
**memoria piu' corta** / piu' reattiva senza rincorrere il rumore. E' un'interazione
reale: cambiare una parte (aggiungere l'xG) sposta l'ottimo di un'altra (l'emivita).
Per questo, dopo un cambiamento importante, conviene ri-verificare gli iperparametri
gia' tarati. Guadagno piccolo (~0.0007) ma su entrambi i mercati e ben fondato.

**Config ufficiale aggiornata:** blend gol/xG α=0.75, shrinkage 1.5, **emivita 365g**.

### 📐 Il modello in dettaglio — perché l'emivita ottima si accorcia

Nessuna formula nuova: si ri-cerca l'ottimo degli **stessi** iperparametri (shrinkage,
emivita) con il blend xG ora attivo, per **coordinate** (fissa uno, ottimizza l'altro).
Il risultato è un'interazione reale tra due parametri già tarati.

**Il perché, in termini di bias-varianza.** L'emivita bilancia:
- *memoria corta* → più reattiva ma meno campione efficace `N_eff` → più **varianza**;
- *memoria lunga* → più stabile ma rischia di usare forza non più attuale → più **bias**.

Nella Fase 2b il segnale era i soli **gol**, molto rumorosi (fortuna sotto porta):
serviva memoria lunga (730g) per mediare via quel rumore. Ora il blend `α·gol +
(1−α)·xG` fornisce un segnale **meno rumoroso a parità di partite** (l'xG stabilizza
la stima del tasso). Con meno rumore per-partita, il modello può permettersi un
`N_eff` più piccolo (emivita **365g**, più reattiva) **senza** inseguire il rumore:
il termine di varianza è già domato dall'xG, quindi conviene ridurre il bias
diventando più recenti. È il caso da manuale del "cambiare una parte del modello
(aggiungere l'xG) sposta l'ottimo di un'altra (l'emivita)" → dopo ogni modifica
importante si ri-verificano gli iperparametri. Guadagno piccolo (−0.0006 su 1X2,
−0.0009 su O/U) ma su entrambi i mercati e ben fondato.

---

## Fase 5 — Grande backtest multi-mercato: per cosa il modello serve davvero

**Obiettivo.** Allargare lo sguardo oltre 1X2/OU: GG/NG (entrambe segnano) e
doppie chance (1X/2X/12). Sono tutti derivabili GRATIS dalla stessa matrice dei
punteggi. Grande operazione: 2 config (gol base vs ufficiale gol+xG) x 6 stagioni
x tutti i mercati.

**Risultato (log-loss medio 6 stagioni).**

| Mercato | gol+xG (uff.) | Mercato | Baseline |
|---|---:|---:|---:|
| 1X2 | 0.9807 | 0.9632 | 1.0834 |
| Over/Under 2.5 | 0.6884 | 0.6816 | 0.6892 |
| GG/NG | 0.6896 | — | 0.6871 |
| 1X (casa o pari) | 0.5497 | 0.5371 | 0.6303 |
| 2X (ospite o pari) | 0.5966 | 0.5833 | 0.6744 |
| 12 (no pari) | 0.5766 | 0.5746 | 0.5820 |

**Lettura.**
- **Bravo (batte nettamente la baseline): 1X2, 1X, 2X** — i mercati d'ESITO. Il
  modello stima bene chi vince; tutto cio' che ne deriva funziona.
- **Debole: Over/Under** (baseline di un soffio) e **12/no-pari** (~pari a mercato
  e baseline: i pareggi sono quasi casuali per tutti).
- **NEGATIVO: GG/NG e' PEGGIO della baseline** (0.6896 vs 0.6871). La probabilita'
  congiunta "entrambe segnano" dipende dalla correlazione tra i due punteggi, che
  il modello (Poisson quasi-indipendenti + correzione DC solo sui punteggi bassi)
  cattura male: sul GG aggiunge rumore, non segnale.
- La config gol+xG e' uniformemente >= alla base solo-gol: config ufficiale
  validata anche multi-mercato. **Nessun mercato batte le quote.**

**Lezione / cosa ne consegue.** Il motore e' uno strumento d'analisi affidabile
per i mercati d'ESITO (1X2, doppie chance), NON per il GG/NG (lì meglio la media)
e a malapena per l'Over/Under. Un'eventuale prossima mossa sul modello sarebbe
proprio la **correlazione dei punteggi** (es. bivariate Poisson) per il GG/NG.

### 📐 Il modello in dettaglio — ogni mercato è una somma di celle

Nessun nuovo parametro: tutti i mercati derivano dalla **stessa** matrice `P(i,j)`.

```
1X  = P(1)+P(X)          2X = P(2)+P(X)          12 = P(1)+P(2)   (= 1 − P(X))
Over 2.5 = Σ_{i+j≥3} P(i,j)                       GG = Σ_{i≥1, j≥1} P(i,j)
```

Ecco perché aggiungere un mercato è "gratis" e perché i mercati d'esito funzionano:
`1X, 2X, 12` sono combinazioni lineari delle probabilità 1X2, che il modello stima
bene → le eredita bene.

**Perché il GG/NG è PEGGIO della baseline (il punto tecnico chiave).** Sotto Poisson
**indipendenti** varrebbe esattamente:

```
P(GG) = P(casa ≥ 1) · P(ospite ≥ 1) = (1 − e^{−λ}) · (1 − e^{−μ})
```

cioè un prodotto di due marginali: **nessuna informazione sulla correlazione** tra i
due punteggi. La correzione `τ` di Dixon-Coles tocca solo 4 celle basse → perturba
`P(GG)` di pochissimo. Ma il GG/NG **è** un evento di correlazione ("segnano
*entrambe*"): dipende da quanto i due punteggi si muovono insieme, che il modello
quasi-indipendente non modella. Risultato: sul GG/NG il modello aggiunge rumore, non
segnale, e finisce **sotto** la media (0.6896 vs baseline 0.6871). È la diagnosi che
motiva il "cambio di classe" (Poisson bivariato / inflazione diagonale, Fase 12b) e
che verrà confermata: il pareggio e il GG/NG vivono nella *correlazione*, non nei
tassi marginali.

---

## Fase 4e — Calendario di club completo: la congestione VERA (dato nuovo)

**Obiettivo.** Dare al modello l'unico segnale "indipendente dai risultati"
rimasto con potenziale (Fase 4c): la **congestione vera**. Il riposo calcolato
sulle sole date di Serie A (`loader.add_rest_days`) NON vede coppe ed Europa —
proprio le partite infrasettimanali che causano fatica ASIMMETRICA — quindi non
aiutava. Serve il **calendario COMPLETO di club** di ogni squadra.

**Ragionamento e alternative.**
- *Fonte ideale*: FBref ("Scores & Fixtures" per squadra, colonna Comp) o
  Transfermarkt — entrambe NON raggiungibili dall'ambiente cloud (proxy, come
  gia' per xG e valori rosa). I datalake Transfermarkt su GitHub o non hanno una
  tabella partite (`salimt/football-datasets`), o la tengono dietro Git LFS
  esaurito / su S3 (`dcaribou`): vicolo cieco.
- *Fonte scelta*: **openfootball** (mirror GitHub, testo pubblico raggiungibile
  via raw). Copre per stagione le competizioni UEFA per club
  (Champions/Europa/Conference + preliminari) e la Coppa Italia. Le partite di
  **Serie A NON si scaricano**: si derivano dallo **snapshot congelato** (esatte,
  nomi gia' canonici, copertura 100%). Il calendario completo = Serie A (interno)
  + coppe/Europa (openfootball).

**Cosa abbiamo costruito.**
1. Un fetcher pulito (`src/data/fixtures.py`) con URL centralizzati in
   `sources.py`, cache offline in `data/raw/` (coerente con understat/transfermarkt).
2. La tabella grezza versionata `data/club_fixtures.csv` (una riga per
   squadra-partita: `season, team, date, competition, home_away, opponent`), coi
   nomi allineati ai nostri via `TEAM_ALIASES` (aggiunti gli alias estesi di
   coppa/Europa, es. `ACF Fiorentina`→`Fiorentina`, `SS Lazio`→`Lazio`); i club
   di Serie A non agganciati vengono **loggati**, non ignorati (**0** mancati
   aggancio, verificato).
3. Due colonne nello snapshot e nel DB, STESSA semantica di `add_rest_days` ma
   sul calendario COMPLETO: `home_rest_days_full`, `away_rest_days_full` (giorni
   dall'ultima partita di club di quella squadra in QUALSIASI competizione, cap
   14, solo partite precedenti → niente look-ahead, NaN se ignoto). Piu' due flag
   utili: `home_midweek_europe`, `away_midweek_europe` (gara europea/coppa nei 4
   giorni precedenti).

**Insidie risolte (registrate perche' si ripresentano).**
- Parser di date openfootball: la fase a **gironi** riparte da Settembre a ogni
  girone → un rollover ingenuo "mese tornato indietro = +1 anno" sballava le date
  (Juventus 2019-20 finiva nel 2022). Risolto con una regola **per semestre**
  (Set-Dic→anno d'inizio, Gen-Giu→anno di fine; Ago è preliminari salvo finali
  post-COVID già entrate in year1). Verificato: 0 date fuori finestra stagione.
- La **Coppa Italia** cambia formato tra stagioni (`Casa v Ospite` dal 2024-25,
  `Casa punteggio Ospite` prima): il parser gestisce entrambi.

**Risultato — copertura reale (onesta, verificata).**

| Stagione | Champions | Europa | Conference | Coppa Italia | Partite con congestione VERA catturata* |
|---|:--:|:--:|:--:|:--:|--:|
| 2017-18 | ✅ | — | — | — | 28 (7.4%) |
| 2018-19 | ✅ | — | — | — | 28 (7.4%) |
| 2019-20 | ✅ | — | — | — | 26 (6.8%) |
| 2020-21 | ✅ | ✅ | — | ✅ | 86 (22.6%) |
| 2021-22 | ✅ | ✅ | ✅ | ✅ | 98 (25.8%) |
| 2022-23 | ✅ | ✅ | ✅ | ✅ | 121 (31.8%) |
| 2023-24 | ✅ | ✅ | ✅ | ✅ | 104 (27.4%) |
| 2024-25 | ✅ | ✅ | ✅ | ✅ | 124 (32.6%) |
| 2025-26 | ✅ | — | — | — | 40 (10.5%) |

*(*) partite in cui almeno una squadra aveva una gara "nascosta" (coppa/Europa)
che accorcia il riposo rispetto al proxy solo-lega. **Totale: 655/3420 (19.2%).**
- **Champions League: tutte e 9 le stagioni.** Europa League dal 2020-21,
  Conference dal 2021-22, Coppa Italia 2020-21→2024-25 (openfootball non copre
  EL/Coppa prima, ne' la Coppa 2025-26): dove manca, quelle partite non entrano
  e `rest_days_full` **degrada in modo controllato** verso il valore solo-lega
  (mai in direzione sbagliata), `midweek_europe` puo' essere un falso 0. **Niente
  numeri inventati.**
- **Non-regressione**: impronta dati invariata (`8483944342fc8b15` — le nuove
  colonne non entrano nell'impronta, calcolata su date/squadre/gol); backtest
  2025-26 con la config ufficiale corrente (emivita 365g, Fase 4d) invariato
  (1X2 log-loss 0.9932). Il modello **non** legge ancora le colonne (covariate
  off di default): il dato è pronto, la validazione è il passo successivo.

**Invariante che ci fa fidare del dato.** Il calendario completo e' un
SOVRAINSIEME di quello di Serie A, quindi la partita precedente e' sempre >=:
→ `rest_days_full <= rest_days` (solo-lega) su ogni riga dove entrambi sono
definiti. Verificato su ~3400 partite: **0 violazioni**. Un bug di join o un
look-ahead romperebbero questa disuguaglianza — e' il nostro test di sicurezza.

**Limite onesto.** Il segnale utile (dove `rest_days_full < rest_days`) e'
concentrato nelle stagioni 2020-25 (EL/Conf/Coppa coperte) e per le squadre che
fanno le coppe. Nelle stagioni 2017-20 abbiamo solo la Champions: il test della
congestione sara' piu' potente sulle stagioni recenti. In locale, puntando gli
URL a una fonte per-squadra (FBref) si chiuderebbero i buchi senza toccare il
resto della pipeline.

**Prossimo passo (a cura dell'utente).** Aggiungere una covariata `rest_full` che
legge le nuove colonne e verificare walk-forward se la congestione VERA migliora
le previsioni dove il proxy solo-lega non ci riusciva (Fase 4c). Come sempre: il
diagnostico in-sample va confermato fuori campione, su piu' stagioni.

### 📐 In dettaglio — la definizione del riposo e l'invariante che lo verifica

**Formula della feature** (identica a `add_rest_days`, ma sul calendario COMPLETO):

```
rest_days_full = min( giorni dall'ULTIMA gara di club della squadra
                      in QUALSIASI competizione,  cap = 14 )
```

- `cap = 14`: oltre due settimane il recupero fisico è completo; conta la
  *congestione*, non il riposo lungo → si tronca a 14.
- Solo partite **precedenti** → niente look-ahead. Prima gara nota → `NaN`.

**L'invariante di sicurezza (perché ci fidiamo del dato).** Il calendario completo è
un **sovrainsieme** di quello di Serie A, quindi l'ultima partita precedente è sempre
più vicina o uguale:

```
rest_days_full  ≤  rest_days   (su ogni riga dove entrambi sono definiti)
```

Verificato su ~3400 partite: **0 violazioni**. Un bug di join o un look-ahead
romperebbe questa disuguaglianza → è un test automatico che *dimostra* l'assenza di
errori di allineamento, non una speranza. È lo stesso spirito dei controlli
d'integrità (gol grezzi == gol snapshot) del loader.

**Perché il segnale utile è concentrato in poche stagioni.** Il riposo differisce dal
proxy solo dove `rest_days_full < rest_days`, cioè dove c'è una gara "nascosta"
(coppa/Europa). openfootball copre Champions in tutte le 9 stagioni, ma EL dal
2020-21, Conference dal 2021-22, Coppa Italia 2020-25. Dove una competizione manca,
`rest_days_full` **degrada in modo controllato** verso il valore solo-lega (mai nella
direzione sbagliata, per l'invariante sopra): niente numeri inventati, solo un
segnale più debole. Totale partite con congestione vera catturata: **655/3420
(19.2%)**, quasi tutte nelle stagioni 2020-25.

---

## Fase 4e-bis — Validazione della congestione VERA (walk-forward)

**Obiettivo.** Chiudere il cerchio della Fase 4c: ora che abbiamo il calendario
di club COMPLETO (Fase 4e), la fatica reale aiuta le previsioni dove il proxy
solo-Serie-A falliva?

**Ragionamento / ipotesi.** La Fase 4c aveva trovato la covariata `rest`
(riposo sul solo calendario di Serie A) *leggermente negativa*: non vedeva le
partite infrasettimanali di coppa/Europa, cioe' proprio quelle che causano la
fatica asimmetrica. Ipotesi: sostituendo la sorgente del calendario (Serie A →
completo) e lasciando **identico tutto il resto**, il segno dovrebbe migliorare.

**Alternative considerate.**
- *Config del modello*: riprodurre a emivita 730g (quella della Fase 4c) oppure
  usare la config ufficiale corrente (emivita 365g, Fase 4d). Scelto **365g**:
  e' il modello che usiamo davvero, e il confronto interno `rest` vs `rest_full`
  resta pulito perche' cambia **un solo fattore** (la sorgente del calendario).
- *Stagioni*: tutte e 9 oppure solo quelle con copertura reale delle coppe.
  Scelte le **5 stagioni 2020-21 → 2024-25** (`2021, 2122, 2223, 2324, 2425`):
  sono quelle in cui EL/Conference/Coppa Italia sono coperte e quindi
  `rest_days_full < rest_days` accade davvero (il limite onesto della Fase 4e).
  Sulle 2017-20 (solo Champions) e sul 2025-26 (coppe non ancora coperte) il
  segnale sarebbe quasi identico al proxy solo-lega: test poco potente.

**Scelta.** Aggiunta la covariata `rest_full` (`home/away_rest_days_full`,
trasformazione `identity`) accanto a `rest` in `_COVARIATES`; tripletta
walk-forward **baseline / rest / rest_full** sulle 5 stagioni, config ufficiale.
15 run registrati (`source=fase4e_congestione`), impronta dati invariata
(`8483944342fc8b15`).

**Risultato (1X2 log-loss, piu' basso = meglio; Δ = vs baseline).**

| Stagione | baseline | rest (solo lega) | rest_full (completo) | Δ rest | Δ rest_full |
|---|--:|--:|--:|--:|--:|
| 2020-21 | 0.9538 | 0.9549 | 0.9549 | +0.0011 | +0.0011 |
| 2021-22 | 0.9887 | 0.9891 | 0.9862 | +0.0004 | **−0.0025** |
| 2022-23 | 0.9943 | 0.9940 | 0.9933 | −0.0002 | **−0.0010** |
| 2023-24 | 0.9848 | 0.9862 | 0.9849 | +0.0013 | +0.0001 |
| 2024-25 | 0.9695 | 0.9700 | 0.9701 | +0.0005 | +0.0005 |
| **MEDIA** | **0.9782** | **0.9788** | **0.9779** | **+0.0006** | **−0.0004** |

(Mercato medio: 0.9601 — nessuna variante lo avvicina.)

**Lezione / cosa ne consegue.**
1. Il calendario completo **inverte il segno** rispetto al proxy solo-lega: `rest`
   peggiorava (+0.0006 medio, conferma della Fase 4c), `rest_full` migliora di un
   soffio (−0.0004 medio). La diagnosi della Fase 4c era corretta: il problema era
   la *sorgente*, non l'idea della congestione.
2. Ma il guadagno e' **minuscolo e incoerente**: aiuta 2 stagioni su 5 (le due a
   copertura piu' piena, 2021-22 e 2022-23), e' neutro/negativo sulle altre;
   l'ordine di grandezza (±0.001 su log-loss) e' **dentro il rumore**. Non basta
   per adottarlo nella config ufficiale, e **non tocca il divario col mercato**.
3. Coerente con lo stato del progetto: **il modello e' al tetto pratico dei dati
   attuali**. La fatica reale e' un segnale vero ma debolissimo, probabilmente
   gia' in gran parte implicito in gol+xG recenti (la stanchezza si vede nei
   risultati). Config ufficiale **invariata**; covariata `rest_full` disponibile
   (off di default) per dati futuri a copertura piena (es. calendario per-squadra
   FBref, che chiuderebbe i buchi 2017-20 e 2025-26).

**Riproducibilita'.** `python scripts/_run_fase4e_congestione.py` (tripletta su 5
stagioni), oppure per singola cella: `python scripts/backtest.py --test-season 2122
--covariates rest_full`.

### 📐 Il modello in dettaglio — un solo fattore cambiato, e la soglia del rumore

Meccanicamente `rest_full` è **la stessa covariata** di `rest` (formula in Fase 4c:
`cov = β·(z_casa − z_ospite)`), con l'unica differenza nella *sorgente* della colonna
(`home/away_rest_days_full` invece di `home/away_rest_days`). Tenere identico tutto il
resto è ciò che rende il confronto pulito: **un solo fattore per volta**.

**Perché "migliora ma è rumore".** Il `β` di `rest_full` diventa del segno giusto
(la congestione vera pesa), e il Δ medio passa da **+0.0006** (`rest`, peggiora,
conferma 4c) a **−0.0004** (`rest_full`, migliora appena). Ma −0.0004 va letto
sulla scala della **variabilità stagionale**: il CI bootstrap di un gap 1X2 per
stagione è tipicamente ±0.014 (Fase 17). Un effetto di 0.0004, che aiuta solo 2
stagioni su 5, è **un ordine di grandezza dentro il rumore** → la diagnosi 4c era
giusta (il problema era la sorgente), ma l'effetto è reale-e-minuscolo, non
adottabile. È la prima di una lunga serie di leve "direzione corretta, payoff nel
rumore" che convergono sul tetto.

---

## Fase 6 — Ricalibrazione della confidenza (temperature scaling, NEGATIVO-ish)

**Obiettivo.** Spremere il modello attuale SENZA dati nuovi. Il diagnostico
(`scripts/analyze.py`, stagione 2024-25) diceva: il modello e' calibrato sulla
media ma perde contro il mercato dove e' molto sicuro (+0.034) e sulle
neopromosse (+0.029). La leva piu' economica per il primo problema e' il
**temperature scaling**: un SOLO parametro T che rende le probabilita' piu'
nette (T<1) o piu' morbide (T>1), tarato sul passato e applicato al futuro.

**Ragionamento / ipotesi.** Se il modello e' troppo sicuro, T>1 (raffredda)
riduce la log-loss. La tabella di calibrazione per fascia suggeriva invece il
contrario (probabilita' un po' "compresse" verso l'uniforme): da verificare
tarando T empiricamente, senza pregiudizi.

**Alternative considerate.**
- *Cosa tarare*: un T globale (scelto: la versione piu' economica), oppure una
  calibrazione per-fascia/isotonica (piu' parametri, piu' rischio di overfit su
  ~380 partite/stagione). Prima la versione economica, da protocollo.
- *Come evitare il look-ahead*: T si tara SOLO sulle predizioni walk-forward
  delle stagioni PRECEDENTI a quella di test (leave-future-out), mai su quella di
  test. Nuovo modulo puro `src/evaluation/calibration.py` (fit/apply) + test.

**Risultato (1X2 log-loss, T tarato sul passato di ogni stagione).**

| Stagione | T | base | calibrato | Δ |
|---|--:|--:|--:|--:|
| 2020-21 | 0.963 | 0.9538 | 0.9526 | −0.0012 |
| 2021-22 | 0.918 | 0.9887 | 0.9903 | +0.0016 |
| 2022-23 | 0.948 | 0.9943 | 0.9948 | +0.0005 |
| 2023-24 | 0.962 | 0.9848 | 0.9843 | −0.0005 |
| 2024-25 | 0.955 | 0.9695 | 0.9681 | −0.0014 |
| 2025-26 | 0.937 | 0.9932 | 0.9925 | −0.0007 |
| **MEDIA** | **~0.94** | **0.9807** | **0.9804** | **−0.0003** |

(Mercato medio: 0.9632 — la calibrazione non lo tocca.)

**Lezione / cosa ne consegue.**
1. Scoperta reale e **robusta**: **T < 1 in tutte e 6 le stagioni** (0.92–0.96).
   Il modello e' **sistematicamente un po' SOTTOconfidente** — le probabilita'
   vanno rese un filo piu' nette, non piu' morbide (l'opposto dell'ipotesi
   "troppo sicuro": l'eccesso di confidenza del diagnostico e' concentrato in
   poche partite estreme, non nella distribuzione media).
2. Ma il guadagno e' **trascurabile** (−0.0003 medio su log-loss, −0.0002 Brier)
   e **non uniforme** (peggiora 2 stagioni su 6: dove i pronostici sicuri
   sbagliavano di piu', rendere le prob piu' nette punisce). Rendere piu' nette
   le probabilita' e' un'arma a doppio taglio: premia quando il modello ha
   ragione, punisce di piu' quando ha torto — in Serie A i due effetti quasi si
   annullano.
3. Coerente con congestione (Fase 4e-bis) e valori-rosa (Fase 4c): **effetto
   reale, direzione coerente, payoff nel rumore**. Il modello e' al tetto. La
   calibrazione **non entra** nella config ufficiale (guadagno < rumore, e
   inconsistente); il modulo resta disponibile per un uso pratico (probabilita'
   leggermente piu' oneste su singola partita) e per dati/mercati futuri.

**Riproducibilita'.** `python scripts/calibrate.py` (validazione walk-forward su
tutte le stagioni; registra 6 run con `source=calibrate_temperature`).

### 📐 Il modello in dettaglio — la formula del temperature scaling

Correzione **post-hoc** a un solo parametro `T`, applicata alle probabilità 1X2 già
prodotte dal modello e poi rinormalizzata (`src/evaluation/calibration.py`):

```
q_i ∝ p_i^(1/T) ,   poi   q_i ← q_i / Σ_j q_j
```

- `T = 1` → nessun cambiamento;
- `T > 1` → "raffredda": probabilità più vicine all'uniforme (meno sicuro);
- `T < 1` → "scalda": probabilità più nette (più sicuro).

**Come si evita il look-ahead.** `T` si **tara** minimizzando la log-loss *solo* sulle
predizioni walk-forward delle stagioni **precedenti** a quella di test
(leave-future-out), e si applica alla stagione di test. `T` non tocca mai i dati che
valuta.

**Perché la scoperta è robusta ma il guadagno no.**
- *Robusta:* `T < 1` in **tutte e 6** le stagioni (0.92–0.96). Il modello è
  sistematicamente un filo **sotto**confidente → le probabilità andrebbero rese un
  po' più nette. (L'eccesso di sicurezza segnalato dal diagnostico era concentrato in
  poche partite estreme, non nella distribuzione media.)
- *Nel rumore:* rendere le probabilità più nette è un'arma a doppio taglio — `−ln p`
  premia molto quando l'esito netto si avvera, ma punisce ancora di più quando no. In
  Serie A i due effetti quasi si annullano: −0.0003 medio, e **peggiora 2 stagioni su
  6**. Sotto la soglia del rumore → non entra nella config ufficiale.
- *Limite strutturale:* `T` scala **tutte** le classi in modo uniforme, non può
  *spostare massa* da un esito all'altro (es. dalla casa al pareggio). Per quello
  serve la ricalibrazione per-classe (Fase 10).

**Prossimo (se si vuole continuare a spremere).** La perdita piu' grande e
concentrata resta le **neopromosse** (+0.029 su ~28% delle partite): un prior di
cold-start e' la leva con l'aspettativa migliore rimasta dentro il modello
attuale.

---

## Fase 7 — Prior di cold-start per le neopromosse (il miglior guadagno interno)

**Obiettivo.** Aggredire la perdita piu' grande e concentrata individuata dal
diagnostico: le **neopromosse** (+0.029 di log-loss su ~28% delle partite). Il
modello, senza storico recente di Serie A per Como/Parma/Venezia..., le tratta
come squadre di media forza e le **sovrastima**.

**Ragionamento / ipotesi.** Le neopromosse sono strutturalmente piu' deboli
(vengono dalla Serie B). Se diamo loro un **prior** sotto la media finche' non
accumulano partite, il modello smette di sovrastimarle. Misura economica prima
di costruire (protocollo): su tutte le 24 neopromosse 2018-2026, segnano in media
**1.08 gol/partita vs 1.36 della lega** (−20%) e ne subiscono **1.72** (+26%), in
modo consistente. In unita' di log-tasso: **δ ≈ 0.23** su attacco e difesa.

**Alternative considerate.**
- *Dove iniettare il prior*: (a) dati-fantasma per le promosse; (b) shrinkage
  extra verso la media; (c) **spostare il bersaglio dello shrinkage** verso un
  valore sotto la media. Scelto (c): riusa il meccanismo di shrinkage gia' nel
  modello (penalita' L2 fissa), cambia solo il *bersaglio* per le promosse da 0 a
  (−δ_att, +δ_def). Elegante: una promossa con **0 partite** finisce esattamente
  sul prior; man mano che gioca, i dati lo sovrastano allo stesso ritmo con cui
  lo shrinkage cede su qualsiasi squadra. Le promosse entrano nel modello anche a
  0 partite (inizio stagione), non piu' trattate come "sconosciute = media".
- *δ fisso vs stimato*: per evitare il look-ahead, δ e' stimato **leave-future-out**
  (per la stagione S, solo dalle promosse delle stagioni < S). Applicato sia al
  modello-gol sia al modello-xG del blend (la promossa e' piu' debole in entrambi).

**Scelta.** Parametro `promoted_prior=(δ_att, δ_def)` nel modello + set
`promoted_teams` passato a `fit` (calcolato dal backtest: presenti nella stagione
di test, assenti nella precedente). Flag CLI `--promoted-prior DELTA`.

**Risultato (1X2 log-loss, δ leave-future-out, 6 stagioni 2020-25 → 2025-26).**

| Stagione | δ (att, def) | TUTTE base | TUTTE prior | Δ | NEOPROM base | NEOPROM prior | Δ |
|---|:--:|--:|--:|--:|--:|--:|--:|
| 2020-21 | (0.27, 0.23) | 0.9538 | 0.9533 | −0.0006 | 0.9475 | 0.9454 | −0.0022 |
| 2021-22 | (0.26, 0.26) | 0.9887 | 0.9858 | −0.0029 | 0.9835 | 0.9736 | −0.0099 |
| 2022-23 | (0.28, 0.26) | 0.9943 | 0.9914 | −0.0028 | 1.0291 | 1.0188 | −0.0103 |
| 2023-24 | (0.27, 0.24) | 0.9848 | 0.9855 | +0.0007 | 0.9767 | 0.9792 | +0.0025 |
| 2024-25 | (0.25, 0.23) | 0.9695 | 0.9693 | −0.0002 | 1.0250 | 1.0241 | −0.0009 |
| 2025-26 | (0.24, 0.21) | 0.9932 | 0.9925 | −0.0008 | 0.9661 | 0.9634 | −0.0027 |
| **MEDIA** | | **0.9807** | **0.9796** | **−0.0011** | **0.9880** | **0.9841** | **−0.0039** |

**Lezione / cosa ne consegue.**
1. **Il miglior guadagno interno trovato finora.** −0.0011 medio complessivo
   (3-4× congestione −0.0004 e calibrazione −0.0003) e **−0.0039** dove doveva
   colpire (partite con una neopromossa). Migliora **5 stagioni su 6** sia
   complessivamente sia sul sottoinsieme. E' principiato (fatto strutturale), non
   un parametro tirato a caso.
2. **Non e' gratis ovunque**: il 2023-24 peggiora (+0.0007) perche' quel trio di
   promosse (Genoa/Cagliari/Frosinone) era piu' vicino alla media — il prior le
   sotto-stima. E' la varianza attesa: il prior scommette sulla regola generale,
   e ogni tanto la promossa e' buona.
3. **Resta piccolo e NON batte il mercato** (0.9796 vs ~0.963): utile per
   previsioni piu' oneste su partite reali (soprattutto inizio stagione e squadre
   neopromosse), non per un edge.
4. **Adozione**: e' l'unico dei tre esperimenti "di spremitura" che supera il
   rumore in modo consistente ed e' principiato → **ADOTTATO nella config
   ufficiale** (δ=0.23, default in `backtest.py`; `--promoted-prior 0` per
   disattivarlo). La decisione arriva dopo aver chiuso le altre leve economiche
   (Fase 8): siccome non c'e' altro da spremere, non c'e' motivo di tenere spento
   l'unico guadagno reale.

**Riproducibilita'.** `python scripts/_run_fase7_promosse.py` (validazione su 6
stagioni, δ leave-future-out), oppure singola cella:
`python scripts/backtest.py --test-season 2122 --promoted-prior 0.23`.

### 📐 Il modello in dettaglio — come è costruito δ e perché vale 0.23

**Il meccanismo: si sposta il BERSAGLIO dello shrinkage.** La penalità della Fase 2b
tirava le forze verso 0 (media). Per le neopromosse il bersaglio diventa un valore
**sotto** la media:

```
penalità = s · [ Σ_i (att_i − att_prior_i)² + Σ_i (dif_i − dif_prior_i)² ]
con   att_prior = −δ_att   e   dif_prior = +δ_def   SOLO per le neopromosse
      (0 per tutte le altre)
```

Eleganza del riuso: non serve codice nuovo per il cold-start. Una neopromossa con
**0 partite** non ha contributo dai dati → la penalità la porta *esattamente* sul
prior; man mano che gioca, il termine dati la sovrasta allo stesso ritmo con cui lo
shrinkage cede su qualsiasi squadra (`≈ s/(s+n_i)`, Fase 2b). Le promosse entrano nel
modello anche a inizio stagione, non più trattate come "sconosciute = media".

**Perché δ ≈ 0.23 (l'aritmetica esatta).** In log-scala, uno spostamento `δ`
dell'attacco moltiplica il tasso-gol per `e^{−δ}`. Dai dati storici delle 24
neopromosse 2018-2026:

```
attacco:  segnano 1.08 gol/gara vs 1.36 della lega  →  δ_att = ln(1.36 / 1.08) = 0.230
difesa:   subiscono 1.72 vs 1.36                     →  δ_def = ln(1.72 / 1.36) = 0.235
```

I due coincidono a ~0.23 → si usa un unico `δ = 0.23`. Verifica del segno: `e^{−0.23} =
0.795` (segnano il **−20%**) e `e^{+0.23} = 1.259` (subiscono il **+26%**) —
esattamente i −20%/+26% osservati. **Il numero non è tirato a caso: è il logaritmo del
rapporto di gol osservato.**

**Perché non è look-ahead.** Per la stagione S, `δ` è stimato **solo** dalle
neopromosse delle stagioni `< S` (leave-future-out) e applicato **sia** al modello-gol
**sia** al modello-xG del blend (la promossa è più debole in entrambi).

**Perché è l'unico adottato.** −0.0011 medio complessivo (3-4× congestione e
calibrazione) e **−0.0039** dove deve colpire (partite con una neopromossa),
migliorando 5 stagioni su 6. È l'unica leva che *supera il rumore in modo consistente*
ed è **principiata** (un fatto strutturale — le promosse *sono* più deboli — non un
parametro pescato). Il 2023-24 peggiora (+0.0007) perché quel trio
(Genoa/Cagliari/Frosinone) era vicino alla media: è la varianza attesa di una regola
che scommette sul caso generale.

---

## Fase 8 — Ultimo giro economico (shrinkage, vantaggio-casa): niente da spremere

**Obiettivo.** Prima di dichiarare il modello "al tetto", chiudere le due ultime
leve economiche interne rimaste, una alla volta e misurando.

**#1 — Ri-taratura dello shrinkage col prior attivo.** Lo shrinkage ufficiale
(1.5) era stato tarato in Fase 4d *senza* il prior; con il cold-start ora gestito
dal prior, l'ottimo potrebbe spostarsi. Sweep 0.75→3.0 su 6 stagioni con
`--promoted-prior 0.23` (`scripts/tune.py`, 30 run registrati):

| shrinkage | 0.75 | 1.0 | 1.5 | 2.0 | 3.0 |
|---|--:|--:|--:|--:|--:|
| media 1X2 log-loss | 0.9797 | 0.9797 | 0.9797 | 0.9798 | 0.9803 |

**Curva piatta** tra 0.75 e 1.5 (ottimo nominale 1.0, ma a 0.00002 da 1.5 =
rumore). **Le due leve sono ortogonali**: il prior gestisce il cold-start, lo
shrinkage nell'intervallo utile non ci si combina. Nessun guadagno → shrinkage
resta 1.5.

**#2 — Vantaggio-casa per-squadra (versione economica prima di costruire).** Idea:
dare a ogni squadra il proprio vantaggio-casa invece di uno globale. Test a
costo zero PRIMA della chirurgia sul modello: il vantaggio-casa per-squadra e'
**stabile** anno su anno? Misura (proxy = punti/gara in casa − fuori, tutte le
team-stagioni 2017-2026):
- effetto medio **0.254 punti/gara** (l'effetto GLOBALE esiste — ed e' gia' nel
  modello come `home_adv` globale, che il fit pesato nel tempo fa anche driftare
  post-COVID);
- ma la **persistenza anno-su-anno e' r ≈ 0.004** (n=136 coppie squadra): il
  "forte in casa" di una stagione e' scorrelato dalla successiva.

Con persistenza nulla, un vantaggio-casa per-squadra **fitterebbe solo rumore
stagionale e non generalizzerebbe** al futuro → l'idea muore prima della
chirurgia (principio: testa la versione economica prima di investire).

**Lezione / cosa ne consegue.** Le due ultime leve economiche sono **entrambe
negative**: #1 piatto, #2 rumore non persistente. Sommato ai risultati di
congestione (Fase 4e-bis) e calibrazione (Fase 6), la conclusione e' solida: il
modello Dixon-Coles gol+xG e' al **tetto pratico dei dati attuali**. Il prior
neopromosse (−0.0011) resta l'unico guadagno interno reale, ed e' ora nella
config ufficiale. Il prossimo passo di valore non e' un altro ritocco interno ma
un **cambio di classe** (es. Poisson bivariato per la correlazione dei punteggi /
GG/NG) o l'**uso pratico** del modello.

**Riproducibilita'.** #1: `python scripts/tune.py --sweep shrinkage --values 0.75
1.0 1.5 2.0 3.0 --seasons 2021 2122 2223 2324 2425 2526 --promoted-prior 0.23`.

### 📐 Il modello in dettaglio — ortogonalità e il test di persistenza

**#1 — Perché lo shrinkage resta 1.5 (ortogonalità).** Con il prior attivo, lo sweep
dà una curva **piatta** (0.9797 da 0.75 a 1.5, minimo nominale a 1.0 ma a 0.00002 da
1.5 = rumore). Interpretazione: prior e shrinkage agiscono su cose diverse — il
**prior** fissa *dove* punta la molla per le neopromosse (il cold-start), lo
**shrinkage** ne regola la *forza* per tutte. Nell'intervallo utile non interagiscono
→ nessun guadagno a ri-tararlo → resta 1.5.

**#2 — Perché il vantaggio-casa per-squadra muore prima di costruirlo.** Il test
economico misura la **persistenza anno-su-anno** dell'effetto per-squadra:

```
proxy per team-stagione:  (punti/gara in casa) − (punti/gara fuori)
persistenza:  r = corr( proxy_stagione_t , proxy_stagione_t+1 )  su n=136 coppie
```

Risultato: **r ≈ 0.004** (praticamente zero), mentre l'effetto **medio** è reale
(0.254 punti/gara — ed è già nel modello come `home_advantage` globale `γ`). La
regola statistica: l'utilità *out-of-sample* di un predittore è limitata dalla sua
**affidabilità** (quanto si ripete). Con `r ≈ 0`, il "forte in casa" di quest'anno è
scorrelato da quello del prossimo → un vantaggio-casa per-squadra **fitterebbe solo
rumore stagionale** e non generalizzerebbe. L'idea muore *prima* della chirurgia sul
modello: è il principio "testa la versione economica prima di investire". (La Fase 30
troverà che il vantaggio-casa varia *dentro* la stagione — crollo nel finale — che è
un effetto diverso e globale, non per-squadra.)

---

## Fase 9 — Anatomia del gap col mercato (analisi approfondita)

**Obiettivo.** Non "spremere" ma **capire**: quanto vale oggi il divario col
mercato, e come si scompone per stagione, per mercato e per forza delle squadre.
E come si e' ridotto lungo l'evoluzione del modello (dal grezzo all'attuale).
Definizione: **gap = log-loss modello − log-loss mercato** (>0 = mercato meglio;
piu' vicino a 0 = meglio). Tutto walk-forward, 6 stagioni (2020-21→2025-26),
riproducibile con `scripts/analyze_gap.py`.

**Il gap oggi (versione ATTUALE, 1X2).** Modello **0.9797** vs mercato **0.9632**
→ **gap medio +0.0165** di log-loss. Per dare una scala: la baseline banale sta a
~1.085 (gap +0.12), quindi il modello ha gia' chiuso ~**87%** della distanza
baseline→mercato; l'ultimo 13% e' la parte dura.
*(Nota Fase 101: «oggi» qui vuol dire «alla Fase 9». Il numero-bandiera al codice
di HEAD e' **0.9799 / 0.9632 / +0.0167** — la differenza e' la correzione del
prior della Fase 92, non un cambio di conclusione. Le misure di questa e delle
altre fasi restano PRE-fix e valide come confronti interni alla fase.)*

**1) Evoluzione — il gap 1X2 lungo le versioni (media 6 stagioni).**

| Versione | gap 1X2 | Δ vs precedente |
|---|--:|--:|
| V0 grezzo (gol, no shrink/no decay) | +0.0236 | — |
| V1 gol tarato (shrinkage+emivita, Fase 2b) | +0.0185 | **−0.0051** |
| V2 +xG nel blend (Fase 4b) | +0.0181 | −0.0004 |
| V3 emivita ri-tarata 365g (Fase 4d) | +0.0175 | −0.0006 |
| V4 +prior neopromosse (Fase 7, ATTUALE) | +0.0165 | −0.0010 |

Lezione: il grosso del recupero (**−0.0051 su −0.0071 totali, il 72%**) e' venuto
dalla **regolarizzazione+memoria** (Fase 2b). xG, ri-taratura e prior hanno
limato il resto (−0.0020 combinato). Dopo il tuning di base, i dati e i ritocchi
danno rendimenti decrescenti — coerente col "tetto".

**2) Per STAGIONE (versione attuale, gap 1X2).**

| 2020-21 | 2021-22 | 2022-23 | 2023-24 | 2024-25 | 2025-26 |
|--:|--:|--:|--:|--:|--:|
| +0.0202 | +0.0145 | +0.0146 | +0.0187 | +0.0170 | +0.0141 |

**Sì, varia** (da +0.014 a +0.020). La peggiore e' la **2020-21** (COVID, stadi
vuoti: piu' rumore, vantaggio-casa anomalo). Le piu' recenti (2021-22, 2025-26)
sono le migliori. Nessuna stagione batte il mercato sull'1X2.

**3) Per MERCATO (versione attuale, pool 6 stagioni).**

| Mercato | gap | note |
|---|--:|---|
| **1X2** | +0.0165 | quote dirette |
| **1X** (casa o pari) | +0.0116 | quota derivata 1X2 |
| **2X** (ospite o pari) | +0.0127 | quota derivata 1X2 |
| **12** (no pareggio) | **+0.0020** | quota derivata 1X2 |
| **Over/Under 2.5** | +0.0069 | quote dirette |
| GG/NG | −0.0018 (vs baseline) | **niente quote nei dati** |

**Scoperta chiave: il gap e' quasi tutto nel PAREGGIO.** Il mercato **12**
(vince una delle due, si esclude il pari) ha gap **+0.0020**, cioe' il modello e'
praticamente a livello mercato quando NON deve prezzare il pareggio. Appena il
pari rientra (1X, 2X, 1X2) il gap triplica/quadruplica. Tradotto: la nostra
debolezza vs mercato e' **prezzare i pareggi** (i punteggi bassi correlati), non
stimare chi e' piu' forte. **Over/Under** e' quasi competitivo (+0.0069, e in
2020-21 il modello lo batte: −0.0031). GG/NG non ha quote nei dati: vs baseline
il modello e' ~pari (oscilla per stagione, rumore).

**4) Per FORZA delle squadre (versione attuale, gap 1X2; una partita conta per
entrambe le squadre coinvolte).**

| Gruppo (tier da classifica) | n | gap medio 1X2 |
|---|--:|--:|
| forte (top 6) | 1368 | +0.0180 |
| media (7°-14°) | 1824 | +0.0123 |
| debole (bottom 6) | 1368 | **+0.0206** |
| neopromossa (sottoinsieme) | 648 | +0.0159 |

**Sì, varia, con una U:** il modello perde di piu' sulle **squadre deboli**
(+0.0206) e sulle **forti** (+0.0180), meno sulle **medie** (+0.0123). Sui deboli
il mercato ha informazione che noi non abbiamo (motivazione salvezza, turnover,
episodi); sui forti conta molto la forma/rotazioni nelle coppe. Le neopromosse
(+0.0159) sono ora **sotto** la media dei deboli grazie al prior della Fase 7
(senza prior sarebbero il gruppo peggiore).

**5) Per FAVORITISMO di mercato (versione attuale, gap 1X2).**

| Partita | n | gap medio 1X2 |
|---|--:|--:|
| equilibrata (favorito <45%) | 799 | +0.0167 |
| moderata (45-60%) | 852 | +0.0173 |
| netta (favorito >60%) | 629 | +0.0152 |

Qui la variazione e' **piccola**: il gap e' abbastanza uniforme, leggermente
minore quando c'e' un favorito netto (+0.0152, modello e mercato concordano di
piu'). Non e' l'asse dove si nasconde il divario.

**Lezione / cosa ne consegue.**
1. Il gap medio 1X2 e' **+0.0165** e non e' uniforme: peggiore su **stagioni
   rumorose (COVID)**, su **squadre deboli/forti**, e — soprattutto — **sul
   pareggio** (il mercato 12 senza pari e' gia' a livello mercato).
2. Questo **punta il dito** sul prossimo passo con la miglior aspettativa
   *dentro un cambio di classe*: **modellare la correlazione dei punteggi**
   (es. Poisson bivariato / dipendenza sui punteggi bassi oltre la correzione DC),
   che e' esattamente cio' che serve per prezzare meglio pareggio e GG/NG. Non e'
   un ritocco: e' la mossa mirata suggerita dai numeri.
3. Il resto del gap (deboli/forti, stagioni rumorose) e' **informazione che il
   mercato ha e noi no** e difficilmente si chiude coi dati storici attuali.

**Riproducibilita'.** `python scripts/analyze_gap.py` (5 versioni × 6 stagioni,
scomposizione per stagione/mercato/forza/favoritismo).

### 📐 In dettaglio — l'aritmetica del "quanto manca" e "dove vive il gap"

**Quanta strada è stata chiusa.** La baseline banale sta a gap ~+0.12 dal mercato,
il modello attuale a +0.0165:

```
frazione chiusa = 1 − (gap_attuale / gap_baseline) = 1 − 0.0165/0.12 ≈ 0.86  (86%)
```

L'ultimo ~14% è la parte dura. (L'audit di Fase 15 ha corretto un precedente "87%"
in **86%**: differenza di arrotondamento, ma va registrata.)

**Perché il gap è "quasi tutto nel pareggio" (scomposizione).** I mercati derivati
isolano *dove* si perde:
- **12 = 1 − P(X)**: prezzarlo non richiede stimare la *massa* del pareggio, solo
  "vince una delle due". Gap **+0.0020** ≈ mercato.
- Appena il pareggio rientra come esito da prezzare (1X, 2X, 1X2) il gap
  **triplica/quadruplica** (+0.012…+0.017).

Poiché `gap(1X2)` ≈ (errore nel prezzare *chi vince*) + (errore nel prezzare *il
pareggio*), e il primo termine è ~0 (lo dice il 12), **il grosso del gap è il secondo
termine**: prezzare i pareggi (= i punteggi bassi correlati). È la firma matematica
che indirizza il "cambio di classe" verso la correlazione dei punteggi (Fase 12b/18),
non verso più feature di forza.

> **⚠️ CORREZIONE (Fase 92).** Questa lettura è **rovesciata**, e l'errore è
> logico, non numerico. `P(12) = P(1) + P(2) = 1 − P(X)` è un'**identità**
> (verificata: scarto max 4e-16): prezzare il "12" **è** prezzare la massa del
> pareggio, non "chi vince". Quindi il suo gap quasi-nullo (+0.0020) non dice
> che sappiamo prezzare chi vince — dice che sappiamo prezzare **il pareggio**.
> La scomposizione esatta (chain rule, ricompone a 6 decimali su 2.280 partite):
>
> | | log-loss | quota del gap |
> |---|--:|--:|
> | gap totale | **+0.016699** | 100% |
> | massa-pareggio (= il mercato "12") | +0.002010 | **12.0%** |
> | discriminazione casa vs ospite | +0.014690 | **88.0%** |
>
> Cioè: **l'88% del gap sta nel distinguere chi vince fra le due squadre**, non
> nel pareggio. Questa correzione spiega a posteriori perché tutte le leve
> costruite su questa diagnosi (inflazione della diagonale Fase 12b, ρ dinamico
> Fase 18, φ(|λ−μ|) Fase 35) abbiano prodotto guadagni minuscoli o nulli:
> aggredivano il **12%**. Il numero +0.0020 resta corretto — cambia
> completamente cosa significa.


**La "U" per forza squadra** (deboli +0.0206, forti +0.0180, medie +0.0123) e il
picco sulle **stagioni rumorose** (COVID 2020-21 +0.0202) sono coerenti con
l'interpretazione "il mercato ha informazione che noi non abbiamo" (motivazione
salvezza, turnover coppe): non è modellabile con i dati storici → è il residuo
irriducibile.

### Fase 9-bis — COVID vs post-COVID e trend recente

**Obiettivo.** Il gap 1X2 peggiore era il 2020-21: e' un effetto COVID (stadi
vuoti) o solo la stagione piu' vecchia? E negli ultimi anni dove sta andando?
Periodi: **COVID** = 2020-21 (stadi vuoti tutta la stagione); **transizione** =
2021-22 (capienza ridotta/Omicron); **post-COVID** = 2022-23→2025-26.

**Gap per periodo (versione attuale; GG/NG vs baseline, no quote).**

| Periodo | 1X2 | 1X | 2X | 12 | O/U 2.5 | GG/NG |
|---|--:|--:|--:|--:|--:|--:|
| COVID (2020-21) | +0.0202 | +0.0160 | +0.0151 | +0.0017 | **−0.0031** | +0.0074 |
| transizione (2021-22) | +0.0145 | +0.0082 | +0.0105 | +0.0031 | +0.0147 | −0.0054 |
| post-COVID (2022-26) | +0.0161 | +0.0114 | +0.0127 | +0.0018 | +0.0074 | +0.0035 |
| **Δ (post − COVID)** | **−0.0041** | −0.0047 | −0.0024 | +0.0001 | **+0.0104** | −0.0039 |

**Due movimenti opposti.**
1. **Mercati d'ESITO (1X2/1X/2X): il gap si RIDUCE dopo il COVID** (1X2 da +0.0202
   a +0.0161). Ipotesi: a stadi vuoti il **vantaggio-casa e' crollato**; il
   modello lo eredita dallo storico "normale" e sovra-pesava le squadre di casa,
   mentre il mercato si adeguava piu' in fretta → gap piu' largo. (Confuso in
   parte col fatto che 2020-21 e' la stagione con meno storico di training.)
   Tornato il pubblico, il gap si e' richiuso. Collega la Fase 8: il vantaggio-
   casa GLOBALE conta e drifta, ma quello per-squadra e' rumore — coerente.
2. **Over/Under: l'OPPOSTO. Nel COVID il modello BATTEVA il mercato** (−0.0031),
   post-COVID il mercato e' tornato affilato (+0.0074, Δ +0.0104). I totali
   risentono meno del pubblico; in quella stagione anomala le quote O/U erano
   verosimilmente meno precise. (Cautela: un solo campione COVID, 380 partite.)
3. **12 (senza pari): a livello mercato in ogni periodo** (~+0.002). La debolezza
   sul pareggio non e' un effetto COVID: e' strutturale.

**Trend ultime 3 stagioni (gap; ↓ = migliora).**

| Mercato | 2023-24 | 2024-25 | 2025-26 | Δ(25/26−23/24) |
|---|--:|--:|--:|--:|
| 1X2 | +0.0187 | +0.0170 | +0.0141 | **−0.0046 ↓** |
| 1X | +0.0175 | +0.0082 | +0.0108 | −0.0066 ↓ |
| 2X | +0.0128 | +0.0156 | +0.0096 | −0.0031 ↓ |
| 12 | −0.0021 | +0.0050 | +0.0022 | +0.0043 ↑ (ma ~mercato) |
| O/U 2.5 | +0.0007 | +0.0101 | +0.0020 | +0.0013 ≈ rumoroso |
| GG/NG | −0.0003 | +0.0037 | +0.0039 | +0.0042 ↑ (vs baseline) |

**Lezione.** I **mercati d'esito stanno migliorando**: il gap 1X2 e' al **minimo
nell'ultima stagione (2025-26: +0.0141)**, in calo netto dalle tre precedenti
(aiutano prior neopromosse e maturazione dell'xG). Il **12 resta incollato al
mercato** ovunque. **O/U e GG/NG oscillano vicino a zero** senza trend. La parte
che si chiude e' quella d'esito; quella che non si muove e' il **pareggio** —
ancora una volta il dito punta sulla correlazione dei punteggi.

**Riproducibilita'.** `python scripts/_run_gap_covid.py`.

### 📐 In dettaglio — perché il COVID muove il gap d'esito (il ruolo di γ)

Il vantaggio-casa nel modello è un **unico parametro globale** `γ` (in
`λ = exp(att_h + dif_a + γ)`), stimato con i pesi temporali. Come ogni parametro
pesato nel tempo, si adatta **lentamente**: a stadi vuoti (2020-21) il vantaggio-casa
reale è crollato, ma `γ` continuava a riflettere lo storico "normale" a pubblico
pieno → il modello **sovra-pesava** le squadre di casa proprio quando contavano meno.
Il mercato si adeguava più in fretta → gap d'esito più largo (+0.0202). Tornato il
pubblico, il gap si è richiuso (−0.0041). È lo stesso meccanismo che la Fase 30
ritroverà *dentro* la stagione (crollo del vantaggio-casa nel finale) e coerente con
la Fase 8 (il vantaggio-casa **globale** conta e drifta; quello **per-squadra** è
rumore). L'O/U fa l'opposto (nel COVID il modello lo *batte*, −0.0031): i totali gol
risentono meno del pubblico, e in quella stagione anomala le quote O/U erano
verosimilmente meno affilate. *Cautela onesta:* un solo campione COVID (380 partite).

---

## Fase 10 — Ricalibrazione per-classe 1X2 (attacca il pareggio; robusto ma piccolo)

**Obiettivo.** Sfruttare la pista mirata della Fase 9: il gap col mercato e'
concentrato nel PAREGGIO e la calibrazione media mostra **casa sovrastimata /
pari sottostimato**. Il temperature scaling (Fase 6) non poteva correggerlo
(scala tutto in modo uniforme, non sposta massa tra esiti). Tre moltiplicatori
per classe (casa/pari/ospite) si'.

**Ragionamento.** `q_i ∝ w_i·p_i`, rinormalizzato; solo i rapporti contano, si
fissa `w_ospite=1` (2 parametri). Pesi tarati SOLO sulle stagioni precedenti
(leave-future-out) e applicati alla stagione di test. Modello = ufficiale ATTUALE
(gol+xG+prior). Nuove funzioni in `src/evaluation/calibration.py`.

**Risultato (1X2 log-loss; pesi normalizzati a media geometrica 1).**

| Stagione | w_casa | w_pari | w_ospite | base | rical. | Δ | gap→mercato |
|---|--:|--:|--:|--:|--:|--:|--:|
| 2020-21 | 0.981 | 1.037 | 0.983 | 0.9532 | 0.9532 | −0.0000 | +0.0202 |
| 2021-22 | 0.970 | 1.029 | 1.001 | 0.9860 | 0.9847 | −0.0013 | +0.0131 |
| 2022-23 | 0.949 | 1.036 | 1.017 | 0.9916 | 0.9920 | +0.0004 | +0.0150 |
| 2023-24 | 0.960 | 1.040 | 1.001 | 0.9854 | 0.9840 | −0.0015 | +0.0172 |
| 2024-25 | 0.962 | 1.060 | 0.981 | 0.9693 | 0.9682 | −0.0011 | +0.0159 |
| 2025-26 | 0.960 | 1.061 | 0.982 | 0.9925 | 0.9932 | +0.0007 | +0.0148 |
| **MEDIA** | **~0.96** | **~1.04** | **~0.99** | **0.9797** | **0.9792** | **−0.0005** | **+0.0160** |

**Lezione / cosa ne consegue.**
1. **Diagnosi confermata, robusta**: in TUTTE e 6 le stagioni il fit **abbassa la
   casa (w≈0.96) e alza il pareggio (w≈1.04-1.06)**. Il modello sovrastima
   sistematicamente le vittorie di casa e sottostima i pari — esattamente la
   miscalibrazione direzionale del diagnostico (Fase 9). Piu' informativo del
   temperature (che poteva solo scaldare/raffreddare).
2. **Payoff piccolo e non uniforme**: −0.0005 medio (gap 1X2 +0.0165→+0.0160),
   aiuta 4 stagioni su 6, peggiora 2 (incl. la piu' recente). E' un po' meglio
   del temperature (−0.0003) ma sempre ai margini del rumore. **Non entra nella
   config ufficiale** (come il temperature); le funzioni restano per l'uso pratico
   (probabilita' 1X2 un filo piu' oneste su singola partita).
3. **Perche' cosi' poco?** La ricalibrazione per-classe e' un surrogato *lineare
   e globale* di cio' che servirebbe davvero: modellare la **correlazione dei
   punteggi** partita-per-partita (la probabilita' del pari dipende dai tassi
   attesi, non e' un fattore costante). Spreme lo strato "medio" della
   miscalibrazione (−0.0005), ma il residuo e' strutturale. **Quinto esperimento
   interno di fila con guadagno nel rumore**: la conclusione e' definitiva —
   dentro questo modello e questi dati il margine e' esaurito, e ogni analisi
   punta allo stesso salto (Poisson bivariato).

**Riproducibilita'.** `python scripts/_run_class_recal.py`.

### 📐 Il modello in dettaglio — la formula della ricalibrazione per-classe

Tre moltiplicatori, uno per esito (casa/pari/ospite), applicati alle probabilità 1X2
e rinormalizzati:

```
q_i ∝ w_i · p_i ,   poi   q_i ← q_i / Σ_j q_j
```

**Perché 2 parametri e non 3.** Solo i *rapporti* tra i `w` contano: `w=(c,c,c)` si
semplifica nella rinormalizzazione. Si fissa `w_ospite = 1` (restano `w_casa, w_pari`)
e alla fine il vettore è normalizzato a media geometrica 1 per leggibilità. Tarato
**leave-future-out** (solo stagioni precedenti) e applicato al test.

**Cosa la distingue dal temperature (Fase 6).** Il temperature `p^{1/T}` scala tutte
le classi allo stesso modo → non può *spostare massa* tra esiti. Qui `w_i` diverso
per classe **sposta massa**: è ciò che serve per una miscalibrazione **direzionale**.

**Perché w_casa ≈ 0.96 e w_pari ≈ 1.04-1.06 (robusto in 6/6 stagioni).** Il fit, senza
che glielo si dica, **abbassa la casa e alza il pareggio** in ogni stagione: conferma
quantitativa che il modello **sovrastima le vittorie casalinghe e sottostima i pari**
— la stessa direzione del diagnostico (Fase 9) e dell'analisi COVID (γ, Fase 9-bis).

**Perché il guadagno resta piccolo (−0.0005).** È un surrogato **lineare e globale**
di ciò che servirebbe davvero: la probabilità *giusta* del pareggio dipende dai tassi
`(λ, μ)` della **singola partita** (un match da 1.8 gol attesi ha P(pari) diversa da
uno da 3.5), non da un fattore costante `w_pari`. La ricalibrazione spreme lo strato
"medio" della miscalibrazione (−0.0005, un filo meglio del temperature −0.0003) ma il
residuo è strutturale → non entra nella config ufficiale. Punta di nuovo al Poisson
bivariato (Fase 12b).

---

## Fase 11 — Combinazioni delle feature off-di-default (nessuna e' utile)

**Obiettivo.** Finora le feature opzionali erano state provate quasi sempre DA
SOLE. Domanda: esiste una loro **combinazione** che, sul modello attuale (col
prior), supera il rumore in modo consistente? Feature off-di-default:
covariate `squad_value`, `absence`, `rest_full` (livello-modello) + ricalibrazione
per-classe post-hoc (Fase 10).

**Disegno.** Tutti i 2^3 = 8 sottoinsiemi delle covariate, ognuno **con e senza**
la ricalibrazione per-classe strutturale (pesi fissi robusti casa 0.96 / pari
1.04 / ospite 1.00, dalla Fase 10). 48 backtest walk-forward × 6 stagioni. Metrica:
1X2 log-loss, Δ vs ufficiale (0.9797) e n. stagioni migliorate (consistenza).

**Risultato (1X2 log-loss; Δ<0 = meglio).**

| Combinazione | RAW | Δ | migl. | +RECAL | Δ | migl. |
|---|--:|--:|:--:|--:|--:|:--:|
| ufficiale (solo prior) | 0.9797 | — | — | 0.9789 | −0.0008 | 6/6 |
| +squad_value | 0.9804 | +0.0007 | 1/6 | 0.9796 | −0.0001 | 3/6 |
| +absence | 0.9796 | −0.0001 | 2/6 | 0.9789 | −0.0008 | 5/6 |
| +rest_full | 0.9794 | −0.0003 | 2/6 | 0.9786 | −0.0011 | 4/6 |
| +squad+absence | 0.9804 | +0.0007 | 1/6 | 0.9796 | −0.0001 | 3/6 |
| +squad+rest_full | 0.9801 | +0.0004 | 2/6 | 0.9793 | −0.0004 | 4/6 |
| +absence+rest_full | 0.9793 | −0.0004 | 3/6 | **0.9786** | **−0.0011** | 4/6 |
| +tutte e tre | 0.9801 | +0.0004 | 2/6 | 0.9793 | −0.0004 | 2/6 |

Multi-mercato (miglior combo vs ufficiale, pool 6 stagioni): gap 1X2 +0.0165→
+0.0161, doppie chance e O/U ~invariati, GG/NG identico (−0.0018). Nessun mercato
beneficia.

**Lezione / cosa ne consegue.**
1. **Nessuna covariata aiuta, nemmeno in combinazione.** `squad_value` **peggiora**
   in ogni mix (+0.0004/+0.0007); `absence` e `rest_full` sono ~neutre da sole e
   la loro coppia da' il miglior RAW ma solo −0.0004 (3/6, rumore). Aggiungere
   covariate non "impila" nulla: confermato che sono ridondanti con gol+xG (gia'
   visto in Fase 4c, ora anche in combinazione e con la config attuale).
2. **L'unico effetto additivo e' la ricalibrazione per-classe** (~−0.0008 coi
   pesi fissi; l'onesto leave-future-out della Fase 10 e' −0.0005). Applicata al
   modello base aiuta 6/6 stagioni, ma e' piccola e la conosciamo gia'.
3. **La "miglior" combinazione (+absence+rest_full+recal, −0.0011) non e' una
   vera vittoria**: il guadagno e' tutto della ricalibrazione (mildly ottimista
   coi pesi fissi), il contributo delle covariate e' rumore, e migliora solo 4/6
   stagioni — MENO del recal sul modello base (6/6). Le covariate qui **sporcano**
   invece di aiutare.
4. **Sesto esperimento interno di fila senza un guadagno robusto.** La risposta
   alla domanda "c'e' una combinazione off-di-default utile?" e' **no**. Le
   feature restano giustamente off; l'unica ha valore solo per l'uso pratico
   (probabilita' un filo piu' oneste), non per un edge.

**Riproducibilita'.** `python scripts/_run_combo_analysis.py`.

### 📐 In dettaglio — perché unire segnali nulli non "impila" nulla

**Il disegno.** Tutti i `2³ = 8` sottoinsiemi delle covariate off-di-default
(`squad_value`, `absence`, `rest_full`), ciascuno con e senza la ricalibrazione
per-classe a **pesi fissi robusti** (casa 0.96 / pari 1.04 / ospite 1.00, dalla Fase
10) = 48 backtest × 6 stagioni.

**Perché nessuna combinazione aiuta.** Le covariate entrano additivamente nel
log-tasso (`cov = Σ_k β_k (z_h,k − z_a,k)`, Fase 4c). Se ogni `β_k` è ~0
out-of-sample (perché il segnale è già catturato da gol+xG, Fase 4c), la loro somma è
~0 più il rumore accumulato di più stime → in media **peggiora** (`squad_value` fa
+0.0004/+0.0007 in ogni mix). Non c'è sinergia da estrarre: due segnali ridondanti da
soli restano ridondanti insieme.

**Perché la "miglior combo" (−0.0011) non è una vittoria.** Quel guadagno è **tutto**
della ricalibrazione (che aiuta 6/6 sul modello base), mentre il contributo delle
covariate è rumore; e la combo migliora solo **4/6** stagioni — *meno* del recal da
solo (6/6). Scegliere il minimo tra 8 combinazioni è **selezione post-hoc**: con
tante prove, il minimo campionario è ottimisticamente basso anche sotto rumore puro.
Il verdetto onesto è "nessun guadagno robusto", non "abbiamo trovato la combo".

---

## Fase 12a — Ensemble di emivite (ultimo tweak economico; piccolo, borderline)

**Obiettivo / idea.** L'unica idea economica non ancora testata: mescolare un
modello a memoria CORTA (180g, reattivo/forma) e uno LUNGA (730g, forza stabile)
puo' battere la singola emivita 365g? Si mescolano le probabilita' 1X2 (righe
allineate), tutti col prior.

**Risultato (1X2 log-loss, 6 stagioni).**

| Variante | media | Δ vs 365g | migliora |
|---|--:|--:|:--:|
| singola 180g | 0.9806 | +0.0009 | 3/6 |
| singola 365g (ATTUALE) | 0.9797 | — | — |
| singola 730g | 0.9803 | +0.0006 | 3/6 |
| **blend 180+730 (50/50)** | **0.9791** | **−0.0006** | 4/6 |
| blend 180+365+730 (1/3) | 0.9793 | −0.0004 | 4/6 |
| blend 365+730 (50/50) | 0.9798 | +0.0001 | 3/6 |

**Lezione.** La miscela **corta+lunga (180+730)** batte di un soffio ogni singola
emivita (−0.0006, 4/6): combinare forma reattiva e forza stabile cattura un po'
piu' della singola 365g. Ma e' **borderline** (4/6, non 6/6), nella stessa fascia
di prior/calibrazione/ricalibrazione. **Non adottato** (non abbastanza robusto).
Chiude il capitolo dei tweak economici: anche l'ultima idea non testata e'
rumore-adiacente. **Riproducibilita'.** `python scripts/_run_ensemble.py`.

### 📐 Il modello in dettaglio — la media di due modelli

Si allenano **due** modelli identici tranne l'emivita — uno corto (180g, reattivo/
forma) e uno lungo (730g, forza stabile) — e si mediano le probabilità 1X2 riga per
riga:

```
p_blend = 0.5 · p_180g  +  0.5 · p_730g       (media sulle probabilità, non sui tassi)
```

**Perché corto+lungo batte il singolo 365g (di un soffio).** È un mini-ensemble: i due
modelli sbagliano in modo parzialmente **scorrelato** (il corto cattura la forma
recente, il lungo la forza di fondo), quindi mediarli riduce la varianza più di quanto
faccia una singola emivita intermedia. Guadagno −0.0006, ma **4/6** stagioni (non
6/6): nella stessa fascia di rumore di prior/calibrazione/ricalibrazione → **non
adottato**. Il 365g singolo resta la config: cattura già gran parte del beneficio in
un modello solo, più semplice.

---

## Fase 12b — Il cambio di classe: inflazione della diagonale (bivariato)

**Obiettivo.** La mossa strutturale indicata da TUTTE le analisi: attaccare la
correlazione dei punteggi / il pareggio, non piu' con un tampone ma cambiando il
modello. Il Poisson bivariato classico (Karlis-Ntzoufras) impone correlazione
positiva (λ₃≥0) che nel calcio e' ≈0 e non aiuta i pareggi; la variante giusta e'
il **modello a diagonale inflazionata**.

**Cosa abbiamo costruito.** Un parametro **φ** che moltiplica per (1+φ) TUTTI i
punteggi di parita' (0-0,1-1,2-2,3-3…) nella matrice, esteso **oltre le 4 celle**
della correzione Dixon-Coles, e — a differenza della ricalibrazione piatta (Fase
10) — **fittato nella verosimiglianza dei punteggi** e **dipendente dalla partita**
(inflaziona in base ai gol attesi). `draw_inflation` nel modello (`--draw-inflation`),
φ stimato con una 1-D per settimana (formula chiusa sulla prob. di pareggio base).

**Diagnosi che lo motiva.** rho fittato −0.04/−0.07, **interno** (non saturo) ma
vincolato alla struttura a 4 celle; deficit pareggio residuo **+0.020** (modello
0.264 vs reale 0.284). C'e' margine per una leva-pareggio dedicata.

**Risultato (1X2 log-loss + calibrazione pareggio, 6 stagioni).**

| Stagione | base | +infl | Δ | P(pari) base→infl | reale |
|---|--:|--:|--:|:--:|--:|
| 2020-21 | 0.9532 | 0.9536 | +0.0003 | 0.250→0.245 | 0.255 |
| 2021-22 | 0.9860 | 0.9854 | −0.0006 | 0.242→0.248 | 0.258 |
| 2022-23 | 0.9916 | 0.9917 | +0.0001 | 0.247→0.257 | 0.263 |
| 2023-24 | 0.9854 | 0.9825 | **−0.0029** | 0.253→0.267 | 0.295 |
| 2024-25 | 0.9693 | 0.9687 | −0.0006 | 0.264→0.288 | 0.284 |
| 2025-26 | 0.9925 | 0.9939 | +0.0014 | 0.264→0.283 | 0.261 |
| **MEDIA** | **0.9797** | **0.9793** | **−0.0004** | | |

Multi-mercato (pool): gap 1X2 +0.0165→+0.0161, **12** +0.0020→+0.0016, O/U e
GG/NG ~invariati. φ fittato ~0.10-0.14 (positivo, come da deficit).

**Lezione / cosa ne consegue — la conclusione dell'intera indagine.**
1. **Il meccanismo funziona come progettato**: P(pari) sale verso il reale in
   OGNI stagione (2024-25: 0.264→0.288 vs 0.284, quasi perfetto). La calibrazione
   del pareggio migliora davvero: il cambio di classe **fa la cosa giusta**.
2. **Ma il log-loss guadagna solo −0.0004 (3/6 stagioni)**, perche' *quanti*
   pareggi capitano in una stagione e' in larga parte **rumore**: dove ne capitano
   pochi (2025-26, reale 0.261) l'inflazione tarata sul passato **sovrastima** e
   peggiora. Migliorare la calibrazione MEDIA del pareggio non basta se la
   deviazione stagionale e' imprevedibile.
3. **Questo chiude il cerchio.** Anche la mossa strutturalmente corretta — quella
   che tre analisi indipendenti indicavano — da' lo stesso ordine di grandezza
   (−0.0004) di ogni tampone. Ragione profonda: **il pareggio e' quasi-casuale per
   tutti, mercato incluso** (il mercato 12 senza pari e' gia' a livello mercato,
   gap +0.0020). Non e' un difetto del nostro modello: e' irriducibilita' del
   fenomeno. Il gap col mercato NON e' "cattiva modellazione del pareggio" da
   sistemare, ma **informazione che il mercato ha e noi no** su singole partite.
4. **Verdetto definitivo**: 7 esperimenti (5 tweak + 1 combinazione + 1 cambio di
   classe) convergono. Il modello e' al **tetto reale**, non solo pratico.
   `draw_inflation` resta **off di default** (−0.0004, non robusto), disponibile
   come opzione (migliora la calibrazione del pareggio per l'uso pratico).

**Riproducibilita'.** `python scripts/_run_draw_infl.py`, oppure
`python scripts/backtest.py --draw-inflation`.

### 📐 Il modello in dettaglio — la formula dell'inflazione diagonale φ

**La correzione.** Un parametro `φ` moltiplica per `(1+φ)` **tutti** i punteggi di
parità (non solo le 4 celle di Dixon-Coles), poi si rinormalizza:

```
P_φ(i, j) ∝ M(i, j) · ( 1 + φ · [i = j] )        (i = j: 0-0, 1-1, 2-2, 3-3, …)
```

`φ > 0` sposta massa **verso** i pareggi (a tutte le altezze), non solo 0-0/1-1.

**Come si stima `φ` (fittato nella verosimiglianza, non post-hoc).** Il termine della
log-verosimiglianza che dipende da `φ` si riduce a una **1-D** (formula chiusa):

```
ℓ(φ) = Σ_partite  w · [ ln(1 + φ·1{pareggio_reale})  −  ln(1 + φ·d_match) ]
```

dove `d_match` = P(pareggio) del **modello base per quella partita** (calcolata
vettorialmente riga per riga). Ecco perché è "dipendente dalla partita": pur essendo
`φ` un unico scalare, l'effetto è normalizzato dalla massa-pareggio *specifica* di
ogni match. Fittato con `φ ∈ [−0.5, 2.0]`; qui esce **~0.10-0.14** (positivo, come da
deficit-pareggio).

**Perché fa la cosa giusta ma non guadagna.** Il meccanismo **funziona**: `P(pari)`
sale verso il reale in OGNI stagione (2024-25: 0.264→0.288 vs reale 0.284,
quasi-perfetto). Migliora la *calibrazione media* del pareggio. Ma il log-loss guadagna
solo −0.0004 (3/6) perché **quanti** pareggi capitano in una stagione è in larga parte
**rumore**: dove ne capitano pochi (2025-26, reale 0.261) l'inflazione tarata sul
passato **sovrastima** e peggiora. È la prova definitiva: anche la mossa
strutturalmente corretta — quella indicata da tre analisi — dà lo stesso ordine di
grandezza (−0.0004) di ogni tampone, perché **il pareggio è quasi-casuale per tutti,
mercato incluso** (il 12 senza pari è già a livello mercato). Non è cattiva
modellazione: è irriducibilità del fenomeno.

---

## Fase 13 — Stato di forma: un pattern nascosto? (NO, gia' catturato)

**Obiettivo.** Verificare l'ultima intuizione: c'e' un momentum ("forma")
predittivo che la forza pesata nel tempo non vede? Il modello cattura la forma
GIA' in modo implicito (emivita 365g: le gare recenti pesano di piu'), e un
indizio c'era (l'emivita corta 180g, piu' reattiva, era peggio, Fase 12a). Ma
una covariata di forma ESPLICITA e' un segnale diverso dal ri-pesare: da provare.

**Feature.** `add_form` nel loader: `home_form`/`away_form` = punti per partita
nelle ultime 5 gare di ciascuna squadra prima di questa (no look-ahead, scorre
tra stagioni). Covariata `form`.

**Metodo: prima il diagnostico del pattern nascosto, poi la covariata.**

*(1) La forma predice l'ERRORE del modello?* Se le squadre in forma battono
sistematicamente l'aspettativa, c'e' segnale non catturato. Su 6 stagioni:
- **corr(forma_casa − forma_ospite, residuo punti casa) = +0.035** → ~zero.
- Residuo medio per terzile di differenza-forma: ~0 in ogni gruppo. Nessun bias
  sistematico legato alla forma.

*(2) Covariata `form` walk-forward (1X2 log-loss):* base 0.9797 → +form **0.9799
(+0.0002, peggio)**, 3/6 stagioni. Come `squad_value`: ridondante e un filo dannosa.

**Lezione.** **Nessun pattern nascosto nella forma.** La ragione e' strutturale:
la "forma" (punti recenti) SONO i risultati recenti, che il fit pesato nel tempo
gia' pesa di piu' → la forma esplicita e' quasi perfettamente collineare con la
forza recente che il modello stima. Il residuo del modello e' scorrelato dalla
forma (+0.035): non resta momentum da spremere. (Una forma su xG sarebbe ancora
piu' ridondante: l'xG e' gia' nel blend.) La covariata `form` resta off. Ottavo
esperimento convergente: il tetto e' reale, la forma non lo scalfisce.

**Riproducibilita'.** `python scripts/_run_form.py`.

### 📐 Il modello in dettaglio — perché la forma è collineare con la forza

**La feature** (`loader.add_form`, finestra 5):

```
home_form = (punti nelle ultime 5 gare della squadra) / (n. gare)   [vit 3, pari 1, sconf 0]
```

Solo gare precedenti (no look-ahead), scorre tra stagioni. Come covariata entra
esattamente come le altre: `β · (z_form,casa − z_form,ospite)`.

**Il diagnostico del "pattern nascosto".** Prima di aggiungere la feature si verifica
se la forma predice l'**errore** del modello:

```
residuo = (punti reali casa) − (punti attesi dal modello)
corr( forma_casa − forma_ospite ,  residuo ) = +0.035  ≈  0
```

~zero → nessun momentum che il modello non veda già. E infatti come covariata
**peggiora** (0.9797→0.9799, 3/6).

**Il perché strutturale.** La "forma" (punti recenti) **è** il risultato delle gare
recenti, e il fit **pesato nel tempo** (emivita 365g) già pesa di più proprio quelle
gare. Quindi `home_form` è quasi perfettamente **collineare** con la forza recente che
il modello stima → non porta informazione ortogonale, solo il rumore della sua stima.
Aggiungere un regressore collineare in un modello ben specificato non può che
aggiungere varianza. (Una forma su *xG* sarebbe ancora più ridondante: l'xG è già nel
blend.) Ottavo esperimento convergente sul tetto.

---

## Fase 13-bis — Streak e rendimento recente: ricerca DATA-DRIVEN (nessun pattern)

**Obiettivo.** Uscire dall'arbitrarieta' della "finestra 5". Due intuizioni:
(a) **streak** (serie utile / di sconfitte in corso) invece di una media a finestra
fissa — effetti di soglia/psicologici; (b) guardare anche **gol fatti/subiti e xG**
recenti, lasciando che siano i **dati** a dire se c'e' un pattern, non soglie
scelte a mano. Solo Serie A (i risultati che abbiamo; le coppe in `club_fixtures`
non hanno i punteggi).

**Metodo.** Diagnostico: le feature di rendimento recente predicono l'ERRORE
(residuo punti casa) del modello walk-forward? Se il modello gia' cattura tutto,
il residuo e' scorrelato da qualsiasi rendimento recente.

**(1) Streak (`scripts/_run_streaks.py`).** corr con residuo: serie utile +0.041,
serie vittorie +0.030, serie sconfitte −0.004 → ~zero. I bucket per lunghezza
serie *sembrano* mostrare qualcosa (serie utile 10-14 → +0.135; sconfitte 3-4 →
+0.130) ma **i segni si ribaltano in modo erratico** (sconfitte 2→−0.157, 3-4→
+0.130, 5+→−0.159) su n=27-146: errore standard ~0.29 > effetti → **rumore**.

**(2) Ventaglio completo (`scripts/_run_recent_patterns.py`).** 23 feature (gol
fatti/subiti/differenza, xG fatti/subiti, "fortuna"=gol−xG, punti, serie),
finestre 3/5/10, differenziale casa-ospite, su 2273 partite. Verdetto in un
numero:

> **R² (residuo spiegato dal rendimento recente) = 0.0101**
> **R² atteso da puro rumore (23 feature / 2273 partite) = 0.0101** — IDENTICI.

Le correlazioni singole piu' alte sono l'**xG recente** (xgf10 +0.069, xga10
−0.058, gd10 +0.055): statisticamente sopra la soglia-rumore (2·SE≈0.042) ma
**minuscole** (~0.4% di varianza) e **collineari** → in multivariata l'R² non
supera il rumore. Le streak e i punti (risultati) sono ancora piu' deboli.

**Lezione.** **Nessun pattern nascosto nel rendimento recente**, ne' nelle streak
ne' nei gol/xG recenti, con qualunque finestra. La ragione e' la stessa della
forma: il rendimento recente (risultati E gol E xG) e' cio' che il fit **pesato
nel tempo** gia' usa e pesa di piu' → il residuo del modello non contiene
momentum residuo. L'unico filo di segnale (xG recente) e' gia' nel blend. Se
mai, conferma che l'xG e' la strada giusta — ma non ne resta da spremere.
Nono/decimo esperimento convergente: il tetto e' reale.

**(3) Interazione STREAK × avversario (`scripts/_run_streak_interaction.py`).**
Ipotesi mirata: una squadra in serie CONTRO un avversario debole sposta l'esito
oltre il modello. "Debolezza avversario" = favoritismo del modello (P(casa)−
P(ospite), out-of-sample). Risultato:
- corr(interazione streak×favoritismo, residuo) = **−0.005** (~zero);
- R² con interazione − R² senza = **+0.00003** (meno di quanto darebbe una feature
  di puro rumore, ~0.00044);
- Griglia 2×2 (residuo medio): casa in serie ≥5 & avversario debole = **−0.018**
  (n=224), perfino piu' basso di casa senza serie & avversario debole (+0.013).
  La cella che dovrebbe "accendersi" e' spenta.

L'interazione **non esiste**: il residuo del modello e' gia' condizionato a
entrambe le forze (l'avversario debole e' gia' prezzato), e la striscia non
aggiunge nulla nemmeno in combinazione. Chiude in modo definitivo il filone
"forma/streak/rendimento recente": il modello prezza gia' in modo ottimale tutto
cio' che sta nei risultati recenti.

**Riproducibilita'.** `python scripts/_run_streaks.py`,
`python scripts/_run_recent_patterns.py`, `python scripts/_run_streak_interaction.py`.

### 📐 In dettaglio — il benchmark di rumore che chiude la questione

Il cuore statistico di questa fase è **come si distingue un segnale dal rumore** in
una regressione multivariata sul residuo. Due formule:

**1) R² atteso da puro rumore.** Con `k` regressori *indipendenti dal target* e `n`
campioni, la varianza spiegata attesa per solo caso è:

```
R²_rumore ≈ k / n = 23 / 2273 = 0.0101
```

Il valore osservato è **0.0101** — **identico**. Il rendimento recente (23 feature:
gol, xG, "fortuna", punti, streak, su finestre 3/5/10) spiega del residuo *esattamente
quanto ne spiegherebbero 23 colonne casuali*. Verdetto in un numero: nessun segnale.

**2) Soglia sulle correlazioni singole.** Una correlazione è distinguibile da zero se
supera `2·SE ≈ 2/√n ≈ 2/√2273 ≈ 0.042`. Le più alte (xG recente: xgf10 +0.069, xga10
−0.058, gd10 +0.055) superano la soglia ma sono **minuscole** (~0.4% di varianza) e
**collineari** tra loro → in multivariata non aggiungono nulla oltre il rumore.

**3) L'interazione streak × avversario debole.** L'incremento di R² aggiungendo il
termine d'interazione è **+0.00003**, *meno* di quanto darebbe una feature di puro
rumore (~`1/n ≈ 0.00044`) → l'interazione non esiste. La cella che dovrebbe
"accendersi" (casa in serie ≥5 vs avversario debole) ha residuo **−0.018**, più basso
del baseline: spenta.

**Perché, di nuovo, è strutturale.** Streak, gol/xG recenti e punti recenti **sono**
ciò che il fit pesato nel tempo già usa e pesa di più → il residuo non contiene
momentum residuo. L'unico filo (xG recente) è già nel blend. Conferma che l'xG è la
strada giusta, ma non ne resta da spremere.

---

## Fase 14 — Il modello contro la linea di APERTURA (CLV) — NEGATIVO, e definitivo

**Obiettivo.** Tutti i confronti fatti finora erano contro le quote di
**chiusura** — lo stimatore piu' efficiente che esista, l'avversario piu' duro.
Ma nessuno e' obbligato a scommettere alla chiusura: si puo' prendere il prezzo
**prima**, quando la linea contiene meno informazione. Domanda: il modello batte
la linea **pre-chiusura** ("apertura")? Se si', esiste un edge *tradeable* anche
senza battere la chiusura — e il **CLV** (la chiusura si muove verso di noi?) e'
il criterio che i professionisti usano per distinguere edge da fortuna.

**Ragionamento.** Le colonne football-data senza suffisso "C" (AvgH...) sono
raccolte ~1-3 giorni prima della partita; quelle con "C" (dal 2019-20) sono la
chiusura. Le predizioni del modello non dipendono dalla quota → si riusano le 5
versioni x 6 stagioni di `analyze_gap` cambiando solo il benchmark, sempre sulle
STESSE righe (entrambe le linee presenti), altrimenti i log-loss non sono
comparabili. Onesta': la "apertura" football-data e' la linea del venerdi', non
l'apertura vera del mercato (piu' morbida ancora, ma non esiste nei dati storici).

**La saga dei dati (lezione di provenienza).** Il mirror GitHub storico
(`Mentaturan/ScoutFootball_for_World_Cup`, fonte di `BASE_URL` e dell'xG
Understat) **e' sparito da GitHub** (404 verificato fuori dal proxy): la
pipeline `--refresh` oggi non ha piu' una fonte a monte, e lo snapshot congelato
e' cio' che ha salvato il progetto — esattamente lo scenario per cui era stato
versionato. Nessun mirror alternativo conserva le quote (footballcsv e datahub
le spogliano; i dataset HF hanno un solo set). Soluzione: i **CSV originali**
scaricati dall'utente da football-data.co.uk e versionati in `data/football_data_raw/`
(fonte grezza congelata, README dedicato nella cartella) — ora la
fonte grezza congelata del repo (`scripts/_restore_raw_cache.py` li identifica
per data e ricostruisce la cache `data/raw/`).

**Risultato (30 backtest, `source=fase14_openline`; 2279/2280 righe comparabili).**

Gap 1X2 (model_ll − market_ll) per versione, STESSE righe:

| Versione | vs APERTURA | vs CHIUSURA |
|---|--:|--:|
| V0 grezzo | +0.0217 | +0.0237 |
| V1 gol tarato | +0.0166 | +0.0186 |
| V4 ATTUALE | **+0.0146** | **+0.0166** |

Versione attuale per stagione (gap vs apertura): +0.0199, +0.0089, +0.0115,
+0.0173, +0.0174, +0.0123 → **positivo in TUTTE e 6 le stagioni**. O/U 2.5:
gap vs apertura +0.0052 medio (batte l'apertura solo nel COVID 2020-21, −0.0029,
e nel 2023-24, −0.0046: non consistente).

Il test decisivo — value bet all'apertura e CLV (pool 6 stagioni):

| bet@open | ROI@open | CLV medio (prob) | CLV>0 |
|--:|--:|--:|--:|
| 692 | **−17.3%** | **−0.0028** | **45%** |

**Lezione / cosa ne consegue.**
1. **La linea del venerdi' e' gia' quasi-chiusura**: l'affilamento open→close
   vale solo **+0.0020** di log-loss (identico per ogni versione del modello,
   com'e' logico: e' una proprieta' del mercato, non nostra). L'informazione
   dell'ultimo giorno (formazioni, notizie) sposta poco la linea 1X2 media.
2. **Il modello non batte nemmeno l'apertura** (+0.0146, 6 stagioni su 6): il
   suo deficit e' 7 volte l'intero guadagno informativo open→close. Anche
   l'avversario "morbido" disponibile nei dati storici e' troppo affilato.
3. **CLV negativo (−0.0028, 45% positivo)**: quando il modello dissente
   dall'apertura, la chiusura si muove **contro** di lui piu' spesso che verso.
   I dissensi del modello sono rumore, non informazione che il mercato deve
   ancora incorporare. E' la morte pulita dell'ipotesi "scommetti presto":
   ROI@open −17.3% (peggio del ROI@close −15.6%).
4. Resta aperta (non testabile con questi dati) solo la linea di apertura VERA
   (domenica sera/lunedi'), piu' morbida del venerdi'. Servirebbe raccolta
   prospettica di quote in tempo reale — un progetto dati, non un backtest.
5. Nona conferma convergente del quadro: l'edge non e' nei dati storici. Le vie
   rimaste sono quelle gia' indicate: dati davvero nuovi (formazioni ufficiali)
   o mercati strutturalmente meno efficienti della Serie A 1X2.

**Riproducibilita'.** `python scripts/_restore_raw_cache.py && python
scripts/build_database.py --open-odds && python scripts/_run_fase14_openline.py`.

### 📐 In dettaglio — value bet, ROI e CLV in formule

Le predizioni del modello **non cambiano**: cambia solo il benchmark (apertura invece
di chiusura). Definizioni:

**Value bet.** Si scommette sull'esito `o` quando il modello vede un margine positivo
sulla linea di apertura devigata:

```
edge(o) = P_modello(o) − P_apertura(o)  > 0        (con P_apertura da devig delle quote *_open)
```

**ROI.** Con puntata unitaria su ogni value bet, pagata alla quota di apertura
`quota_open(o)`:

```
ROI = ( Σ vincite − Σ puntate ) / Σ puntate
    = ( Σ_{bet vinti} quota_open − N_bet ) / N_bet = −17.3%   (692 bet, 6 stagioni)
```

**CLV (Closing Line Value) — il criterio dei professionisti.** Misura se la chiusura
si muove *verso* la nostra scommessa:

```
CLV(o) = P_chiusura(o) − P_apertura(o)          (in probabilità devigata)
```

`CLV > 0` = il mercato ci ha dato ragione (avevamo battuto la chiusura futura). Qui:
**CLV medio −0.0028**, positivo solo nel **45%** dei casi (< 50%).

**Perché è la morte pulita dell'ipotesi "scommetti presto".** L'affinamento
open→close vale solo +0.0020 di log-loss (proprietà del *mercato*, identica per ogni
versione del modello) mentre il deficit del modello è +0.0146 — **7 volte** quel
guadagno informativo. E il CLV negativo dice che i dissensi del modello dall'apertura
sono **rumore che la chiusura corregge contro di lui**, non informazione anticipata.
Due misure indipendenti (gap e CLV), stessa conclusione. Resta non testabile solo la
linea di apertura *vera* (domenica/lunedì), assente nei dati storici.

---

## Fase 15 — Audit dei calcoli (verifica indipendente; 1 errore vero trovato)

**Obiettivo.** Prima di investire altro lavoro sul modello: c'e' qualche errore
di calcolo nei backtest fatti finora? Verifica sistematica di formule, pipeline
e di OGNI numero dichiarato in README/DIARIO.

**Ragionamento / metodo.** Quattro verifiche indipendenti e incrociate:
(1) audit del codice di modello e metriche (formule, segni, allineamenti,
look-ahead); (2) audit di tutti gli script di fase; (3) ricalcolo a precisione
piena di ogni numero di README/DIARIO dal registro `runs.jsonl` (233 run);
(4) ri-esecuzione del backtest ufficiale dallo snapshot congelato.

**Risultato.**
- **Formule: nessun errore.** Log-loss, Brier, devig, correzione DC τ,
  verosimiglianza dell'inflazione diagonale, temperature scaling, blend: tutto
  corretto. Walk-forward pulito (`date < as_of` ovunque, nessun leakage
  per-partita). Backtest ufficiale **riprodotto identico** alla 4ª cifra.
- **1 errore numerico vero**: il ROI del value betting nel README (**≈ −8.5%**)
  era il valore della Fase 1 (una stagione, modello iniziale); quello reale
  della config ufficiale su 6 stagioni e' **−15.7% medio** (da −4.7% a −23.0%,
  864 scommesse). Corretto. La conclusione "non scommettere" si rafforza.
- **Sbavature corrette**: tabella Fase 2b di questo diario (riga "puro"
  incoerente), O/U ufficiale 0.6885 (non 0.6884), ~86% di distanza chiusa (non
  ~87%), baseline 1.0834 (non ~1.085), guadagno Fase 4d −0.0006/−0.0009 (non
  ~0.0007), doppia stima del prior (−0.0010 δ fisso / −0.0011 leave-future-out)
  ora spiegata.
- **Limiti metodologici dichiarati** (non correggibili a posteriori senza
  rifare la storia): baseline in-sample (quella ex-ante onesta e' 1.0860/0.6961:
  il modello batte anche quella); iperparametri tarati su stagioni poi
  riportate — ma il gap sulle stagioni MAI usate per il tuning (+0.0164,
  2020-23) e' indistinguibile da quello sulle stagioni di tuning (+0.0166,
  2023-26), quindi nessuna evidenza di overfitting di selezione; costanti
  RECAL_W e δ=0.23 fisso col senno di poi negli script delle fasi 10-12 (i Δ
  onesti restano i leave-future-out); tier di `analyze_gap` dalla classifica
  finale (diagnostica, non operativa); streak (Fase 13) senza reset tra
  stagioni (impatto marginale).
- **Fix preventivi alla Fase 14** (prima che arrivino i dati): niente righe
  open≡close spurie nel CLV; metriche modello/apertura sulle stesse righe nel
  registro.
- **Registro completato e numeri riconfermati**: le run delle Fasi 11, 12a e 13
  (assenti da `runs.jsonl` nonostante la promessa di replicabilita') sono state
  ri-eseguite (96 backtest, registro a 329 run) e i numeri pubblicati sono
  usciti **identici**: blend 180+730 = 0.9791 (−0.0006, 4/6); forma +0.0002
  (corr +0.0353); miglior combo −0.0011 (+absence+rest_full +RECAL, rumore
  selezionato), squad_value peggiora in ogni mix.

**Lezione.** L'errore sopravvissuto piu' a lungo non era in una formula ma in un
**numero copiato tra contesti diversi** (ROI di Fase 1 accanto a metriche a 6
stagioni). Il registro automatico funziona: tutto cio' che passava da
`runs.jsonl` era giusto; gli errori vivevano solo nei documenti scritti a mano e
negli script che NON registravano le run. Regola rafforzata: ogni numero
pubblicato deve essere ricalcolabile dal registro.

### 📐 In dettaglio — le formule verificate e l'errore trovato

**Cosa è stato ricontrollato riga per riga (tutte confermate corrette):**

```
log-loss 1X2   = −media( ln P(esito) )                         [metrics.log_loss_1x2]
Brier 1X2      = media Σ_k (p_k − y_k)²                          [metrics.brier_1x2]
devig 1X2      = (1/quota_i) / Σ_j (1/quota_j)                   [metrics.devig_1x2]
correzione τ   = τ(0,0)=1−λμρ, τ(0,1)=1+λρ, τ(1,0)=1+μρ, τ(1,1)=1−ρ
inflazione φ   = Σ w·[ln(1+φ·1{pari}) − ln(1+φ·d_match)]        [_fit_draw_phi]
temperature    = p^{1/T} rinormalizzato                          [apply_temperature]
blend          = α·rate_gol + (1−α)·rate_segnale·c
```

Walk-forward pulito: il filtro `data < as_of` è presente **ovunque** (nessun leakage
per-partita); il backtest ufficiale è stato **riprodotto identico alla 4ª cifra**.

**L'unico errore numerico vero (e la sua aritmetica).** Il ROI del value betting nel
README era **≈ −8.5%**, ma quello era il valore della **Fase 1** (una sola stagione,
modello iniziale) rimasto per errore accanto a metriche a 6 stagioni. Il ROI reale
della config ufficiale su **6 stagioni / 864 scommesse** è:

```
ROI = ( Σ_{bet vinti} quota − N_bet ) / N_bet = −15.7% medio   (range −4.7% … −23.0%)
```

L'errore non era in una formula ma in un **numero copiato tra contesti diversi**. Tutto
ciò che passava dal registro `runs.jsonl` era giusto; gli errori vivevano solo nei
documenti scritti a mano → la regola "ogni numero deve essere ricalcolabile dal
registro". La conclusione "non scommettere" ne esce **rafforzata**.

**Limiti metodologici dichiarati (onestà, non correggibili a posteriori).** Baseline
in-sample (frequenze del campione valutato); la baseline ex-ante onesta è
1.0860/0.6961, e il modello batte anche quella. Nessuna evidenza di overfitting di
selezione: il gap sulle stagioni **mai** usate per il tuning (+0.0164, 2020-23) è
indistinguibile da quello sulle stagioni di tuning (+0.0166, 2023-26).

---

## Fase 15-bis — Gap per mercato, stagione per stagione (la matrice completa)

**Obiettivo.** La Fase 9 aveva scomposto il gap per mercato solo in aggregato
(pool 6 stagioni) e per stagione solo sull'1X2. Domanda: le medie per-mercato
nascondono stagioni storte? Il "quasi-zero" del mercato 12 regge sempre?

**Ragionamento.** Una media a 6 stagioni puo' coprire una varianza enorme (l'O/U
lo dimostrera'). Prima di trarre conclusioni operative da un gap medio serve la
matrice completa mercato x stagione, con la config ufficiale e le stesse
convenzioni di analyze_gap (gap = model_ll − market_ll; GG/NG vs baseline
perche' non ha quote).

**Alternative.** Estendere analyze_gap.py (gia' lungo, 4 assi) o script
dedicato: scelto lo script dedicato (`scripts/_run_gap_markets.py`), che
registra le 6 run in `runs.jsonl` (regola Fase 15).

**Risultato** (gap col mercato; >0 = mercato migliore):

| Gap | 2021 | 2122 | 2223 | 2324 | 2425 | 2526 | media |
|---|--:|--:|--:|--:|--:|--:|--:|
| 1X2 | +0.0202 | +0.0145 | +0.0146 | +0.0187 | +0.0170 | +0.0141 | +0.0165 |
| 1X | +0.0160 | +0.0082 | +0.0089 | +0.0175 | +0.0082 | +0.0108 | +0.0116 |
| 2X | +0.0151 | +0.0105 | +0.0127 | +0.0128 | +0.0156 | +0.0096 | +0.0127 |
| 12 (no pari) | +0.0017 | +0.0031 | +0.0021 | −0.0021 | +0.0050 | +0.0022 | +0.0020 |
| O/U 2.5 | −0.0031 | +0.0147 | +0.0168 | +0.0007 | +0.0101 | +0.0020 | +0.0069 |
| GG/NG (vs base) | +0.0074 | −0.0054 | +0.0069 | −0.0003 | +0.0037 | +0.0039 | +0.0027 |

Tre fatti:
1. **Il 12 e' a livello mercato in OGNI stagione** (−0.0021…+0.0050; nel
   2023-24 il modello lo batte). Non e' un artefatto della media.
2. **Il costo del pareggio e' strutturale**: 1X/2X restano a +0.008…+0.018 in
   tutte le stagioni, ~5x il 12. Nessuna annata in cui il modello "impara" il
   pari.
3. **L'O/U e' il mercato piu' volatile** (σ tra stagioni ~0.008, range 0.02):
   dal battere il mercato (COVID) al gap peggiore di tutti (2022-23). Una
   stagione buona sull'O/U non e' segnale.

**Lezione.** La media aggregata della Fase 9 era rappresentativa per i mercati
d'esito (12 stabile, pari stabile) ma NON per l'O/U, dove il gap medio +0.0069
e' quasi privo di significato operativo (varianza della stessa scala del
valore). Conferma la gerarchia: esiti > totali-gol per affidabilita' del
modello.

**Riproducibilita'.** `python scripts/_run_gap_markets.py` (6 run registrate,
source `gap_markets`).

### 📐 In dettaglio — quando una media a 6 stagioni è (dis)onesta

Il punto tecnico è quando un **gap medio** è rappresentativo. Una media è affidabile
solo se la **deviazione standard tra stagioni** è piccola rispetto al valore:

```
rappresentatività ≈  |gap_medio|  /  σ_tra-stagioni
```

- **Mercati d'esito** (12, 1X, 2X): `σ` piccola → il gap è stabile in *ogni* stagione
  (il 12 sta a −0.0021…+0.0050 sempre ≈ mercato; 1X/2X sempre +0.008…+0.018). La media
  della Fase 9 era rappresentativa.
- **Over/Under**: `σ ≈ 0.008` con range ~0.02, mentre il gap medio è +0.0069 → **`σ`
  della stessa scala del valore**. La media +0.0069 è quasi priva di significato
  operativo: l'O/U passa dal *battere* il mercato (COVID −0.0031) al gap peggiore di
  tutti (2022-23 +0.0168). Una stagione buona sull'O/U **non** è segnale.

Conferma la gerarchia di affidabilità: **esiti > totali-gol**. Ed è il motivo per cui
le conclusioni operative si prendono sui mercati d'esito, non sull'O/U.

---

## Fase 16 — Encompassing: il modello ha informazione propria? (NO, α*=0)

**Obiettivo.** L'ultima domanda che il gap non puo' dire: un modello a +0.0165
dal mercato puo' comunque contenere informazione INDIPENDENTE (utile in blend,
monetizzabile su mercati meno efficienti) oppure e' mercato degradato con
rumore? E' la distinzione tra "modello inutile" e "modello con segnale proprio
ma non abbastanza".

**Ragionamento.** Test standard di forecast encompassing: p_blend =
α·modello + (1−α)·mercato, α stimato minimizzando la log-loss. Se il mercato
"ingloba" il modello, α*≈0; se α*>0 stabile e il blend migliora out-of-sample,
c'e' segnale proprio.

**Alternative.** Regressione logistica sui residui del mercato (equivalente ma
meno leggibile) o blend fittato in-sample (barare). Scelto il blend con α
fittato SOLO sulle stagioni di test precedenti, applicato alla successiva
(walk-forward onesto; la prima stagione non e' valutabile → 5 valutazioni).
L'α* in-sample per stagione e' riportato come descrittivo.

**Risultato** (`scripts/_run_encompassing.py`; 6 run + summary nel registro,
source `fase16_encompassing`):
- α* in-sample = **0.000 in TUTTE le stagioni** (≤10⁻⁵): anche potendo barare,
  il fit non da' alcun peso al modello;
- α walk-forward = 0.000 ovunque → blend ≡ mercato, Δ pooled +0.0000,
  CI95 [−0.0000, +0.0000] (bootstrap appaiato, B=10.000, n=1900);
- verdetto: **il mercato di chiusura ingloba completamente il modello**.

**Lezione.** Il gap +0.0165 non e' "informazione nostra meno informazione
loro": e' informazione loro + il nostro rumore di stima. Converge con il CLV
negativo della Fase 14 (due test indipendenti, stessa conclusione). Contro la
chiusura non c'e' NULLA da monetizzare, nemmeno in combinazione; l'unica
speranza pratica residua sono avversari meno efficienti (exchange sottili,
leghe minori) — questione empirica aperta, non promessa.

### 📐 Il modello in dettaglio — il test di forecast encompassing

**La formula.** Si costruisce il blend lineare modello-mercato e si cerca il peso
`α` che minimizza la log-loss:

```
p_blend = α · p_modello + (1 − α) · p_mercato ,   α* = argmin_α  log-loss(p_blend)
```

Interpretazione: se il mercato "ingloba" (encompasses) il modello, il fit non dà peso
al modello → `α* ≈ 0`. Se il modello avesse informazione **indipendente** (utile in
blend, monetizzabile altrove), `α* > 0` stabile e il blend migliorerebbe
out-of-sample.

**Come è reso onesto (walk-forward).** `α` è stimato **solo** sulle stagioni di test
precedenti e applicato alla successiva (la prima non è valutabile → 5 valutazioni).
L'`α*` in-sample per stagione è riportato solo come descrittivo. Il Δ pooled ha CI da
**bootstrap appaiato** per-partita (B=10.000, n=1900).

**Il risultato, in numeri.** `α* = 0.000` in **tutte** le stagioni (≤10⁻⁵): anche
potendo *barare* col fit in-sample, non si dà peso al modello. Walk-forward: blend ≡
mercato, Δ +0.0000, CI95 [−0.0000, +0.0000].

**Cosa dimostra.** Il gap +0.0165 **non** è "informazione nostra meno informazione
loro": è informazione loro + il nostro **rumore di stima**. Il modello non contiene un
segnale ortogonale al mercato. Converge esattamente col CLV negativo (Fase 14) e con
l'adverse selection (Fase 20): tre viste indipendenti dello stesso fatto.

---

## Fase 17 — Intervalli di confidenza: quali numeri sono reali e quali rumore

**Obiettivo.** Dare barre d'errore ai quattro numeri che reggono le
conclusioni: gap 1X2, gap 12, gap O/U, Δ del prior neopromosse (l'unica
feature adottata).

**Ragionamento / metodo.** Bootstrap APPAIATO per-partita (si ricampionano le
differenze di log-loss della stessa partita, B=10.000, seed fisso, pooled 6
stagioni, n=2280). Per il Δ prior: V4 e V3 rifatti sulle stesse partite
(allineamento verificato per costruzione).

**Risultato** (`scripts/_run_gap_uncertainty.py`; 12 run + summary nel
registro, source `fase17_bootstrap`):

| quantita' | media | CI95 | P(modello meglio / prior aiuta) |
|---|--:|--:|--:|
| gap 1X2 | +0.0165 | [+0.0106, +0.0225] * | 0.0% |
| gap 12 (no pari) | +0.0020 | [−0.0006, +0.0046] | 6.5% |
| gap O/U 2.5 | +0.0069 | [+0.0022, +0.0116] * | 0.2% |
| Δ prior (V4−V3) | −0.0010 | [−0.0025, +0.0004] | 92.6% |

*(\* = CI95 che non attraversa lo zero.)* Per stagione (gap 1X2): CI tipico
±0.014 → 3 stagioni su 6, da sole, non distinguerebbero il modello dal
mercato: e' la giustificazione statistica della regola "mai giudicare da una
stagione".

**Lezione (tre punti onesti).**
1. Il gap 1X2 e l'O/U sono REALI (CI lontani da zero): il mercato e' davvero
   migliore, non e' varianza.
2. Il "quasi-zero" del 12 e' ora un'affermazione statistica: sul "chi vince"
   siamo formalmente indistinguibili dal mercato.
3. Il Δ del prior (−0.0010) NON e' conclusivo da solo (CI include lo zero,
   P(aiuta)~93%). Resta adottato perche' coerente (5/6 stagioni), concentrato
   dove deve agire (−0.0039 sulle promosse) e motivato strutturalmente — ma la
   dichiarazione corretta e' "probabilmente utile", non "dimostrato". Con ~30
   test sulle stesse 6 stagioni, qualunque futuro CI che sfiora lo zero va
   letto come "non concluso".

### 📐 In dettaglio — come si costruisce una barra d'errore (bootstrap appaiato)

**La procedura.** Per confrontare due predittori (modello vs mercato, o V4 vs V3) si
lavora sulle **differenze per-partita** di log-loss, non sulle medie separate:

```
d_p = log-loss_A(p) − log-loss_B(p)      per ogni partita p    (le due predizioni sulla STESSA riga)
```

Poi si **ricampiona con reinserimento** l'insieme delle `d_p` (B=10.000 volte, seed
fisso, n=2280), ricalcolando ogni volta la media; il CI95 sono i percentili 2.5 e 97.5
di quelle medie. "Appaiato" = si ricampiona la stessa partita per entrambi i modelli →
si toglie la varianza *comune* (partite intrinsecamente facili/difficili) e resta solo
la varianza della *differenza* → CI più stretti e onesti.

**Come leggere i risultati.**
- `gap 1X2 = +0.0165, CI [+0.0106, +0.0225]` → **non attraversa lo zero** ⇒ il mercato
  è davvero migliore, non è varianza (P(modello meglio) = 0.0%).
- `gap 12 = +0.0020, CI [−0.0006, +0.0046]` → **attraversa lo zero** ⇒ sul "chi vince"
  siamo statisticamente **indistinguibili** dal mercato.
- `Δ prior = −0.0010, CI [−0.0025, +0.0004]` → attraversa lo zero (P(aiuta) 92.6%) ⇒
  "**probabilmente** utile", non dimostrato. Adottato per coerenza (5/6) e meccanismo,
  ma l'etichetta onesta è quella.

Per singola stagione il CI tipico è ±0.014: **3 stagioni su 6 da sole non
distinguerebbero il modello dal mercato** → la giustificazione statistica della regola
"mai giudicare da una stagione".

---

## Fase 18 — Rho dinamico: l'ultima idea strutturale sul pareggio (NEGATIVA)

**Obiettivo.** Il rho di Dixon-Coles e' un numero unico per tutte le partite.
Ipotesi (l'unica strutturale mai provata dopo la 12b): la correlazione dei
punteggi bassi varia con la partita — un match da 1.8 gol attesi ha dinamiche
di 0-0/1-1 diverse da uno da 3.5.

**Ragionamento.** rho_match = rho + rho_slope*(lam+mu − centro), con rho_slope
stimato NELLA verosimiglianza (non post-hoc) e centro = media pesata dei gol
totali del training (costante fissata prima del fit). rho_slope=0 riproduce
esattamente il modello classico (test di regressione in tests/).

**Alternative.** Spline/bucket di rho per fascia di gol attesi (piu' parametri,
piu' overfitting) o rho per-squadra (gia' escluso in Fase 8 per il
vantaggio-casa: non persiste). Scelta la parametrizzazione lineare a 1
parametro: la versione economica dell'idea.

**Regola di decisione dichiarata PRIMA di vedere i numeri** (disciplina Fase
17): adozione solo se il CI95 bootstrap del Δ esclude lo zero.

**Risultato** (`scripts/_run_dynrho.py`; 13 run nel registro, source
`fase18_dynrho`):
- diagnostico del parametro (fit al via di ogni stagione): rho_slope
  **instabile** — +0.06, −0.11, +0.15, −0.08, +0.15, +0.15 — cambia segno e
  sbatte sul bound (±0.15) in 3 fit su 6;
- walk-forward 6 stagioni: Δ **+0.0003**, CI95 [−0.0007, +0.0013],
  P(migliora)=25.9%; O/U −0.0000 [−0.0007, +0.0006];
- regola pre-dichiarata → **NON si adotta**.

**Lezione.** Doppia firma del rumore: parametro senza segno stabile E nessun
guadagno out-of-sample. Con la ricalibrazione per-classe (Fase 10) e la
diagonale inflazionata (Fase 12b), e' la **terza e ultima via strutturale sul
pareggio a chiudersi**: il tetto non dipende dalla forma funzionale della
correzione, ma dall'informazione disponibile. Nota di metodo: dichiarare la
regola di adozione prima di vedere i numeri costa zero e vale molto.

### 📐 Il modello in dettaglio — la formula del rho dinamico

Il `ρ` di Dixon-Coles classico è **un solo numero** per tutte le partite. L'ipotesi:
la correlazione dei punteggi bassi varia con la partita (un match da 1.8 gol attesi ha
dinamiche di 0-0/1-1 diverse da uno da 3.5). Si rende `ρ` funzione lineare del volume
di gol atteso:

```
ρ_match = ρ + ρ_slope · ( λ + μ − centro )
centro  = media pesata dei gol totali del training   (costante fissata PRIMA del fit)
```

- `ρ_slope` è stimato **dentro** la verosimiglianza (non post-hoc), con
  `ρ_slope ∈ [−0.15, 0.15]`;
- `ρ_slope = 0` riproduce **esattamente** il modello classico (c'è un test di
  regressione in `tests/` che lo verifica);
- il `centro` sottratto rende `ρ_slope` interpretabile come "quanto cambia la
  correlazione per gol atteso *in più della media*".

**La disciplina (regola dichiarata PRIMA dei numeri).** Adozione **solo se** il CI95
bootstrap del Δ esclude lo zero. Dichiararla prima costa zero e blinda contro il
"trovare" un guadagno post-hoc.

**Perché è rumore — la doppia firma.** (1) Il *parametro* è instabile: `ρ_slope` fittato
al via di ogni stagione fa +0.06, −0.11, +0.15, −0.08, +0.15, +0.15 → cambia segno e
sbatte sul bound in 3 fit su 6 (un parametro reale sarebbe stabile). (2) Nessun
guadagno OOS: Δ **+0.0003**, CI95 [−0.0007, +0.0013], P(migliora)=25.9%. Regola
pre-dichiarata → **non adottato**. Terza via strutturale sul pareggio a chiudersi: il
tetto non dipende dalla *forma funzionale* della correzione (τ costante, φ, ρ(match)
danno tutti lo stesso ordine di grandezza) ma dall'informazione disponibile.

---

## Fase 19 — Potenza sul prior: 8 stagioni (l'evidenza si rafforza, non conclude)

**Obiettivo.** Il Δ del prior neopromosse (unica feature adottata) era
"probabile ma non concluso" in Fase 17 (CI [−0.0025, +0.0004], P~93%). Colpa
dell'effetto o del campione? Le partite-promosse in 6 stagioni sono solo 648.

**Ragionamento.** Il dataset ha 9 stagioni ma i test ne usavano 6: le stagioni
2018-19 e 2019-20 non sono MAI state usate in nessuna analisi (il 2017-18
resta solo-training). Estenderle e' potenza gratis e genuinamente
out-of-sample rispetto a ogni scelta fatta finora. Caveat dichiarato: δ=0.23
(stima storica Fase 7) include informazione 2018-20, quindi per le due
stagioni aggiunte il VALORE del prior non e' leave-future-out: e' un test di
potenza sull'effetto della config adottata, non una nuova stima di δ.

**Risultato** (`scripts/_run_prior_power.py`; 17 run nel registro, source
`fase19_prior_power`):

| pool | media | CI95 | P(aiuta) | n |
|---|--:|--:|--:|--:|
| tutte, 8 stagioni | −0.0013 | [−0.0026, +0.0001] | 96.5% | 3040 |
| solo promosse | −0.0045 | [−0.0094, +0.0001] | 97.0% | 864 |
| (Fase 17, 6 stagioni) | −0.0010 | [−0.0025, +0.0004] | 92.6% | 2280 |

Le due stagioni aggiunte confermano ENTRAMBE il prior (Δ −0.0024 e −0.0014;
sulle promosse −0.0093 e −0.0045); l'effetto aiuta in 7 stagioni su 8 (l'unica
contraria resta il 2023-24, promosse piu' forti della media).

**Lezione.** L'evidenza si muove nella direzione giusta man mano che arrivano
dati (93% → 96.5%): comportamento da effetto reale piccolo, non da rumore. Ma
il CI sfiora ancora lo zero (+0.0001): per la disciplina multiple-testing il
verdetto resta "**molto probabile, formalmente non concluso**". Il prior resta
adottato; l'etichetta onesta migliora. Per chiudere davvero servirebbero altre
~2-3 stagioni di dati nuovi (o piu' leghe).

### 📐 In dettaglio — perché più stagioni spostano P(aiuta) (e il caveat)

**Il meccanismo statistico.** Il segnale del prior è piccolo ma reale; la larghezza
del suo CI si stringe come `∝ 1/√n`. Aggiungendo le stagioni **2018-19 e 2019-20** —
mai usate in nessuna analisi precedente — `n` passa da 2280 a 3040 partite (e le
partite-promosse da 648 a 864). Con l'effetto fisso e il CI che si stringe, la massa
della distribuzione bootstrap che sta sotto zero cresce: **P(aiuta) 92.6% → 96.5%**.
È il comportamento di un **effetto reale piccolo** (P si muove verso 1 man mano che
arrivano dati), non di rumore (che oscillerebbe attorno al 50%). Le due stagioni nuove
confermano entrambe il prior (Δ −0.0024 e −0.0014; sulle promosse −0.0093 e −0.0045).

**Il caveat onesto (perché "non concluso" resta).** `δ = 0.23` è la stima **storica**
della Fase 7, che **include** informazione 2018-20. Quindi per le due stagioni aggiunte
il *valore* del prior non è leave-future-out: questo è un **test di potenza**
sull'effetto della config adottata, non una nuova stima indipendente di `δ`. Inoltre,
con ~30 test sulle stesse 6-8 stagioni (multiple testing), un CI che sfiora lo zero
(+0.0001) va letto conservativamente → "molto probabile, formalmente non concluso".

---

## Fase 20 — Anatomia dei residui: nessun segnale nascosto, ma si scopre il PERCHE'

**Obiettivo.** La Fase 13 aveva testato solo "la forma" come predittore
dell'errore del modello. Domanda completa: QUALCUNA delle covariate pre-partita
disponibili predice il residuo del modello? Incluse quelle di ESTREMITA' mai
provate (lo scarto di valore-rosa e' gia' stato bocciato come valore assoluto in
Fase 4c, ma il suo MODULO — mismatch estremo — no).

**Ragionamento.** Due domande in una:
1. il residuo (punti reali casa − attesi) e' predetto da 11 covariate
   pre-partita? Regressione multivariata con benchmark di rumore (R²≈k/n +
   200 draw di feature casuali), come in Fase 13.
2. il modello perde di piu' dove DISSENTE dal mercato? (adverse selection: se
   si', i "value bet" del modello sono i suoi errori — spiegherebbe il ROI).

**Alternative.** Target = gap vs mercato invece di residuo vs esito (piu'
diretto ma confonde errore-modello con forza-mercato); scelto il residuo vs
esito per la Parte 1 (continuita' con Fase 13) e il gap per la Parte 2
(adverse selection). Feature di estremita' incluse esplicitamente perche' sono
l'unica classe mai testata.

**Risultato** (`scripts/_run_residuals.py`; 7 run nel registro, source
`fase20_residuals`):

*Parte 1 — il residuo e' rumore puro.* R² multivariata = **0.0055** vs 0.0048
(k/n) e 0.0051 (feature casuali). Ogni covariata a livello rumore; le tre di
estremita' sono le piu' piatte (|scarto valore| −0.0018, |scarto riposo|
−0.0046, assenze totali −0.0011). Nullo gia' in-sample → a fortiori
out-of-sample. Nessun pattern nascosto oltre la forma.

*Parte 2 — adverse selection, forte e pulita.* Il gap vs mercato cresce
monotono coi quartili di dissenso modello-mercato:

| quartile dissenso | n | gap medio |
|---|--:|--:|
| basso | 570 | +0.0009 |
| medio-basso | 570 | +0.0024 |
| medio-alto | 570 | +0.0088 |
| alto | 570 | +0.0539 |

corr(dissenso, gap) = **+0.18**. Dove il modello dissente di piu' — cioe' dove
segnalerebbe un value bet — perde ~60 volte di piu'.

**Lezione.** Due conclusioni. (1) Il residuo non contiene struttura sfruttabile
con NESSUNA covariata disponibile: l'analisi dei residui e' chiusa. (2) Ma
l'adverse selection e' il **meccanismo operativo** del fallimento: i disaccordi
del modello sono i suoi errori, non la sua intuizione. Chiude il cerchio con
l'encompassing (Fase 16, α*=0) e il CLV negativo (Fase 14) — tre viste dello
stesso fatto. E' il risultato che rende ONESTO il "non scommettere": non "il
modello e' un po' peggio", ma "ogni volta che il modello crede di avere ragione
contro la chiusura, ha torto in media".

### 📐 In dettaglio — residuo rumoroso, ma l'adverse selection è netta

**Parte 1 — il residuo è rumore puro.** Regressione multivariata del residuo su 11
covariate pre-partita, col benchmark di rumore della Fase 13-bis:

```
R²_osservato = 0.0055     vs     R²_rumore ≈ k/n = 0.0048   (e 0.0051 da feature casuali)
```

Praticamente identici → nessuna covariata predice il residuo, **incluse** le tre di
*estremità* mai provate (|scarto valore-rosa| −0.0018, |scarto riposo| −0.0046, assenze
totali −0.0011: le più piatte). Nullo già in-sample → a fortiori fuori campione.

**Parte 2 — adverse selection, forte e pulita.** Si ordina il **dissenso**
modello-mercato (quanto la P del modello si discosta da quella di mercato) in quartili
e si guarda il gap:

```
quartile dissenso:  basso +0.0009 → medio-basso +0.0024 → medio-alto +0.0088 → alto +0.0539
corr( dissenso , gap ) = +0.18
```

Il gap cresce **monotòno**: dove il modello dissente di più — cioè **dove segnalerebbe
un value bet** — perde ~`0.0539/0.0009 ≈ 60 volte` di più. È il meccanismo operativo
del fallimento reso quantitativo: i disaccordi del modello sono i suoi **errori**, non
la sua intuizione. Chiude il cerchio con encompassing (α*=0, Fase 16) e CLV negativo
(Fase 14): tre misure indipendenti, stesso fatto.

---

## Fase 21 — Un modello diverso sul GG/NG: gradient boosting (pareggia, non batte)

**Obiettivo.** Primo modello di famiglia diversa dal Dixon-Coles e primo test
del principio "un modello per mercato" (CLAUDE.md §8). Bersaglio: il GG/NG,
dove il DC e' debole (Fase 5: peggio della baseline, cattura male la
correlazione dei punteggi) e — cruciale — l'unico mercato SENZA quote nei dati,
quindi l'unico dove il tetto di efficienza (Fasi 14/16/20) non e' dimostrato.

**Ragionamento.** Un gradient boosting che predice P(GG) direttamente, con
feature = output del DC (gol attesi lam/mu, P(GG), P(over), tutti walk-forward)
+ covariate pre-partita (forma, riposo, valore rosa, assenze). Cosi' il GBM
puo' imparare la correzione di correlazione non-lineare che al DC manca,
partendo pero' dall'informazione che il DC gia' estrae.

**Alternative.** Modello a punteggio con correlazione esplicita (bivariato
Poisson) o GBM sulle sole covariate grezze. Scelto lo stacking DC+GBM: la
versione piu' potente e onesta (il GBM ha tutto cio' che ha il DC, piu' spazio
per correggerlo). Walk-forward per stagione (allena su 1819..S-1); niente
look-ahead ne' nelle feature ne' nel target.

**Controllo di equita' (decisivo).** Il log-loss punisce durissimo la
mis-calibrazione, e un boosting e' sovra-confidente su un evento ~50/50. Per
non incolpare il modello di un difetto di taratura, valutata anche una versione
CALIBRATA (Platt in cross-validation sul solo training).

**Regola di adozione (dichiarata PRIMA dei numeri):** il GBM (raw o calibrato)
entra come modello ufficiale del GG/NG solo se batte il DC con CI95<0 E almeno
pareggia la baseline (che il DC non batteva).

**Risultato** (`scripts/_run_gbm_btts.py`; 9 run nel registro, source
`fase21_gbm_btts`):

| | log-loss GG/NG | Δ vs DC (CI95) |
|---|--:|--:|
| GBM grezzo | 0.7178 | +0.0280 [+0.0167, +0.0391] |
| GBM calibrato | 0.6945 | +0.0047 [−0.0019, +0.0113] |
| Dixon-Coles | 0.6898 | — |
| baseline (in-sample) | 0.6871 | — |

- il GBM grezzo sembrava un disastro, ma era quasi tutto **mis-calibrazione**:
  calibrato, il divario dal DC crolla da +0.0280 a +0.0047 (CI che include lo
  zero; batte il DC in 2 stagioni su 6);
- ma il GBM calibrato **non batte il DC** ne' la baseline; **nessuno dei due
  batte la baseline** sul GG/NG;
- regola pre-dichiarata → **non adottato**.

**Lezione.** Due conclusioni. (1) Metodologica: il controllo di calibrazione e'
stato decisivo — senza avremmo concluso il falso ("GBM molto peggio"); la
verita' e' "GBM pareggia il DC una volta calibrato". Da tenere per ogni modello
nuovo. (2) Sostanziale: una famiglia di modelli COMPLETAMENTE diversa, con
pieno accesso ai lam/mu del DC e alle covariate, atterra sullo STESSO punto —
a livello della frequenza di base. E' **convergenza sul tetto**, non fallimento
del GBM: il GG/NG e' intrinsecamente quasi-impredicibile dai dati pre-partita
in Serie A, come il pareggio. Il principio "un modello per mercato" resta
valido per i prossimi tentativi; ma questo mercato, col miglior candidato
ragionevole, non cede — e il fatto che un modello non-parametrico non trovi
nulla oltre il DC abbassa molto le attese anche per un bivariato Poisson.

### 📐 Il modello in dettaglio — lo stacking DC+GBM e la calibrazione di Platt

**L'architettura (stacking).** Un gradient boosting predice `P(GG)` direttamente, con
in ingresso l'informazione che il DC già estrae **più** le covariate grezze:

```
feature del GBM = [ λ, μ, P(GG)_DC, P(Over)_DC   (output DC, walk-forward)
                    + forma, riposo, valore-rosa, assenze ]   →   P(GG)
target = 1 se entrambe segnano, 0 altrimenti
```

Così il GBM ha *tutto* ciò che ha il DC, più lo spazio per imparare la correzione di
correlazione **non-lineare** che al DC (Poisson quasi-indipendenti) manca. Walk-forward
per stagione (allena su 1819..S−1); niente look-ahead né nelle feature né nel target.

**Il controllo di equità decisivo — calibrazione di Platt.** Il log-loss punisce
durissimo la mis-calibrazione, e un boosting è sovra-confidente su un evento ~50/50.
Per non incolpare il modello di un difetto di *taratura* invece che di *contenuto*, si
calibra con una logistica a 2 parametri, stimata in cross-validation **sul solo
training**:

```
p_calibrato = σ( a · logit(p_grezzo) + b )        σ = sigmoide;  (a, b) fit in CV
```

**Perché il controllo era decisivo (in numeri).** Il GBM grezzo sembrava un disastro
(Δ vs DC **+0.0280**), ma calibrato il divario **crolla a +0.0047** (CI include lo
zero, batte il DC in 2 stagioni su 6): quasi tutto era mis-calibrazione, non mancanza
di contenuto. Senza questo controllo avremmo concluso il falso ("GBM molto peggio").

**Il verdetto.** Regola pre-dichiarata: il GBM entra come modello ufficiale del GG/NG
solo se batte il DC (CI95<0) **e** almeno pareggia la baseline. Il GBM calibrato non
batte né il DC né la baseline → **non adottato**. Una famiglia di modelli
completamente diversa, con pieno accesso ai `λ,μ` del DC, atterra sullo **stesso
punto**: è **convergenza sul tetto** (il GG/NG è quasi-impredicibile dai dati
pre-partita), non un fallimento del GBM.

---

## Fase 22 — Sweep del GBM su tutti i mercati: il tetto e' informativo, non di modello

**Obiettivo.** La Fase 21 ha provato il GBM solo sul GG/NG. Qui lo spremiamo:
molte varianti su molti mercati, per vedere se su QUALCUNO il GBM muove il gap
col mercato rispetto al Dixon-Coles. E' il test a fondo del principio 8.

**Ragionamento.** 6 mercati (1X2, O/U 2.5, GG/NG, doppie chance 1X/2X/12) x 3
set di feature (cov = solo covariate pre-partita; dc = solo output del DC;
dc+cov = entrambe) x calibrazione. Ogni GBM walk-forward per stagione (allena
su 1819..S-1). Headline calibrata (la Fase 21 ha mostrato che il grezzo mente
per mis-calibrazione). Verdetto inferenziale sulla variante pre-scelta dc+cov
calibrata, gap vs mercato con CI bootstrap appaiato per-riga.

**Alternative.** Sweep di iperparametri (profondita', regolarizzazione) invece
dei feature-set: scartato in favore dei feature-set, che rispondono alla
domanda vera ("da dove viene il segnale?"). Un tuning fine avrebbe al piu'
avvicinato il GBM al DC, non battuto — vedi la lezione sotto.

**Risultato** (`scripts/_run_gbm_sweep.py`; 9 run nel registro, source
`fase22_gbm_sweep`). Log-loss calibrata, miglior feature-set del GBM:

| mercato | GBM migliore | DC | mercato | baseline |
|---|--:|--:|--:|--:|
| 1X2 | 1.0059 | 0.9797 | 0.9632 | 1.0834 |
| O/U 2.5 | 0.6966 | 0.6885 | 0.6816 | 0.6892 |
| GG/NG | 0.6943 | 0.6898 | — | 0.6871 |
| 1X | 0.5572 | 0.5487 | 0.5371 | 0.6303 |
| 2X | 0.6097 | 0.5960 | 0.5833 | 0.6744 |
| 12 | 0.5811 | 0.5766 | 0.5746 | 0.5820 |

Movimento del gap (Δ = GBM − DC appaiato per-riga):

| mercato | Δ gap | CI95 |
|---|--:|--:|
| 1X2 | +0.0310 | [+0.0217, +0.0402] |
| O/U 2.5 | +0.0081 | [+0.0005, +0.0157] |
| GG/NG | +0.0045 | [−0.0023, +0.0111] (pari) |
| 1X | +0.0141 | [+0.0066, +0.0216] |
| 2X | +0.0198 | [+0.0131, +0.0263] |
| 12 | +0.0051 | [+0.0015, +0.0086] |

- il GBM **non batte il DC su nessun mercato**; allarga il gap ovunque, con CI
  che esclude lo zero su 5 mercati su 6 (solo il GG/NG pareggia, entrambi a
  livello baseline);
- il GBM fa MEGLIO quando usa SOLO le feature del DC (dc batte dc+cov e cov su
  1X2/1X/2X): aggiungere covariate grezze peggiora → rende al meglio quando
  modifica MENO il DC.

**Lezione.** Due famiglie di modelli (parametrica e non), 6 mercati, 3
feature-set: il tetto e' **informativo, non architetturale**. La forma del
Dixon-Coles non e' il collo di bottiglia — lo sono i dati pre-partita. Il
segnale utile e' tutto e solo quello che il DC gia' estrae (gol/xG pesati nel
tempo); ogni grado di liberta' in piu' aggiunge rumore, che sui mercati con
quote il mercato ha gia' prezzato (gap che cresce). Il principio "un modello per
mercato" era corretto da testare e ora e' testato a fondo: su questi dati
nessun mercato cede. Per un edge serve **informazione nuova**, non un modello
nuovo. Chiude il filone "modelli alternativi" avviato in Fase 21.

### 📐 In dettaglio — il disegno "da dove viene il segnale?"

**Il disegno (non iperparametri, ma feature-set).** 6 mercati × 3 **set di feature**
× calibrazione:

```
cov      = solo covariate pre-partita
dc       = solo output del Dixon-Coles (λ, μ, prob derivate)
dc+cov   = entrambe
```

La scelta dei feature-set (invece di uno sweep di profondità/regolarizzazione) risponde
alla domanda vera: **da dove viene il segnale?** Un tuning fine avrebbe al più
avvicinato il GBM al DC, non battuto.

**Il risultato che spiega il tetto.** Il GBM rende **al meglio quando usa SOLO le
feature del DC** (`dc` batte `dc+cov` e `cov` su 1X2/1X/2X): aggiungere le covariate
grezze **peggiora**. Cioè il GBM è migliore quando **modifica meno** il DC. E allarga
il gap col mercato su 5 mercati su 6 (CI esclude lo zero). Interpretazione: il segnale
utile è tutto e solo quello che il DC già estrae (gol/xG pesati nel tempo); ogni grado
di libertà in più (covariate, non-linearità) aggiunge **rumore che, sui mercati con
quote, il mercato ha già prezzato** → gap che cresce. Due famiglie di modelli
(parametrica e non), 6 mercati, 3 feature-set: il tetto è **informativo, non
architetturale**. Per un edge serve informazione nuova, non un modello nuovo.

---

## Fase 23 — GBM modello + mercato: si puo' ridurre il gap? (no, non con un GBM)

**Obiettivo.** Ultima leva per ridurre il gap col mercato: l'unica informazione
mai data al modello sono le QUOTE di mercato stesse. Un GBM che le riceve puo'
(a) correggere inefficienze non-lineari della linea e batterla, o almeno (b)
riprodurla, portando il gap a ~0?

**Ragionamento.** Encompassing NON-lineare: la Fase 16 aveva mescolato
alpha*modello+(1-alpha)*mercato (lineare, alpha*=0 -> mercato ottimo). Un GBM su
[DC + covariate + quote devigate di chiusura] cattura bias non-lineari
(favourite-longshot, mispricing del pareggio per fascia) che un alpha scalare non
vede. Le quote di chiusura sono pre-esito: usarle come feature e' lecito (nessun
look-ahead sull'outcome), ma e' informazione del mercato.

**Alternative.** Blend lineare gia' fatto (Fase 16). Regressione logistica sulle
quote (equivalente al GBM ma meno flessibile). Scelto il GBM: la forma piu'
potente per trovare struttura non-lineare, se c'e'.

**Regola (dichiarata prima):** "edge sul mercato" solo se il GBM-con-mercato
batte il MERCATO con CI95 del gap < 0. Pareggiarlo (gap ~0) non e' un edge ma un
miglioramento come stimatore per un mercato diverso.

**Risultato** (`scripts/_run_gbm_market.py`; 9 run, source `fase23_gbm_market`):

| 1X2 | log-loss | gap vs mercato |
|---|--:|--:|
| DC | 0.9797 | +0.0165 |
| GBM senza mercato | 1.0114 | +0.0482 |
| GBM con mercato | 0.9996 | +0.0364 |
| mercato | 0.9632 | 0 |

(O/U: GBM con mercato 0.6956 vs DC 0.6885 vs mercato 0.6816.)

- il GBM-con-mercato NON batte il mercato (P=0%, CI [+0.0275, +0.0454]);
- piu' sorprendente: non lo **pareggia** nemmeno, e resta **peggio del DC da
  solo** (0.9996 vs 0.9797). Anche ricevendo le probabilita' di mercato, il GBM
  le degrada;
- il mercato come feature AIUTA il GBM rispetto a se stesso (1.0114 -> 0.9996):
  porta informazione che le altre feature non hanno, ma non basta.

**Lezione.** Il mercato di chiusura e' una previsione quasi-ottima, e un ensemble
di alberi non puo' che degradarla (quantizza/regolarizza un input probabilistico
near-optimal, aggiungendo rumore). Sintesi su "ridurre il gap": a ~0 si arriva
solo BANALMENTE copiando il mercato (gia' noto dalla Fase 16, peso sul mercato
~1); sotto zero (batterlo) NO, con nessun metodo lineare o non-lineare, con o
senza il mercato come input. Il GBM e' lo strumento sbagliato per combinare
modello e mercato: il modo giusto e' lineare, e la Fase 16 ha gia' dato il
verdetto. Chiude la ricerca di un metodo per ridurre il gap.

### 📐 Il modello in dettaglio — encompassing NON-lineare

**L'idea.** La Fase 16 mescolava modello e mercato **linearmente** (`α*=0`). Qui un
GBM riceve anche le quote e può catturare bias **non-lineari** della linea:

```
feature del GBM = [ output DC (λ, μ, prob) + covariate + quote di CHIUSURA devigate ]  →  P(1X2)
```

Usare le quote di chiusura come feature è lecito (sono pre-esito, nessun look-ahead
sull'outcome) ma è **informazione del mercato**. Regola pre-dichiarata: "edge" solo se
il GBM-con-mercato batte il **mercato** con CI95<0; pareggiarlo (gap ~0) non è un edge.

**Il risultato sorprendente.** Il GBM-con-mercato (0.9996) **non batte** il mercato
(0.9632, P=0%), non lo **pareggia** nemmeno, e resta **peggio del DC da solo** (0.9797).
Il mercato come feature *aiuta* il GBM rispetto a sé stesso (1.0114→0.9996) ma non
basta.

**Il perché.** La chiusura è una previsione **quasi-ottima**: un ensemble di alberi
non può che **degradarla** — quantizza e regolarizza un input probabilistico
near-optimal, aggiungendo rumore di discretizzazione. È lo strumento sbagliato per
combinare modello e mercato: il modo giusto è **lineare**, e la Fase 16 ha già dato il
verdetto (a gap ~0 si arriva solo copiando il mercato, peso ~1; sotto zero non ci si
arriva con nessun metodo). Chiude la ricerca di un metodo per ridurre il gap.

---

## Fase 24 — DC calcolato DAL mercato: il primo risultato positivo dell'arco modelli

**Obiettivo.** Nessuna fase l'aveva fatto: finora il DC stima lambda,mu dai GOL,
e finora abbiamo sempre MESCOLATO gli output (DC+mercato) o dato il mercato a un
GBM. Domanda nuova: e se COSTRUISSIMO il DC a partire dal mercato? Il mercato
stima lambda,mu meglio di noi (batte il DC di +0.0165 sull'1X2); invertendo le
quote si ricavano i lambda,mu impliciti, e la matrice del DC ci deriva sopra gli
altri mercati.

**Ragionamento.** Sui mercati CON quote (1X2, O/U) l'inversione riproduce il
mercato -> gap ~0 banale. Il valore e' tutto nel DERIVARE un mercato che il book
NON prezza: il GG/NG (nessuna quota nei dati, l'unico con "spazio" per il
principio 8). Se lambda,mu del mercato + struttura DC battono il nostro GG/NG e
la baseline, e' l'informazione superiore del mercato trasferita a un mercato non
prezzato — non circolare (il GG/NG non e' tra gli input), non un edge contro un
mercato efficiente.

**Metodo.** Per ogni partita: devig 1X2 + O/U -> 4 probabilita' target; si trova
(lambda,mu) che le riproduce meglio via la matrice a Poisson indipendenti
(rho=0; il mercato 1X2+O/U non vincola rho). Da quella matrice si legge P(GG).
Sensibilita' con un rho della diagonale (-0.06, correzione dei punteggi bassi).

**Alternative.** Prior di forza dal mercato nel fit del DC (piu' invasivo);
scelto il piu' pulito: inversione per-partita, nessun ri-fit.

**Risultato** (`scripts/_run_dc_from_market.py`; 7 run, source
`fase24_dc_from_market`):

| GG/NG | log-loss |
|---|--:|
| mercato-implicito + rho | 0.6853 |
| mercato-implicito (rho=0) | 0.6865 |
| DC-da-gol (attuale) | 0.6898 |
| baseline (in-sample) | 0.6871 |

- il GG/NG dai lambda,mu del mercato BATTE il nostro DC-da-gol: Δ -0.0033, CI95
  [-0.0072, +0.0005], P=95.7%, negativo in 6 stagioni su 6;
- e' la PRIMA cosa a battere la baseline sul GG/NG (0.6865 < 0.6871; il DC-da-gol
  no); la correzione rho aiuta ancora (0.6853).

**Lezione.** Dopo 8 risultati negativi sui modelli (Fasi 18, 21-23), il primo
positivo — e viene da una domanda giusta: non "quale modello", ma "quale
informazione, e come trasferirla". Il mercato conosce i gol attesi meglio di noi;
la struttura del DC li porta su un mercato non prezzato. Onesta': (1) il CI
sfiora lo zero -> "molto probabile, formalmente non concluso" (come il prior,
Fase 19); (2) guadagno modesto, il GG/NG resta difficile (~0.685 vicino al
testa-o-croce); (3) non verificabile contro un'ipotetica linea GG/NG; (4)
richiede le quote 1X2+O/U al momento della predizione (il DC-da-gol no) + un
venue che offra il GG/NG. Come stimatore CONDIZIONATO alle quote, il GG/NG
"specialista" (principio 8) diventa: inverti il mercato -> matrice DC -> P(GG),
invece del DC-da-gol. E' la prova che la leva vera e' l'informazione (qui: quella
del mercato su un mercato non prezzato), non l'architettura.

### 📐 Il modello in dettaglio — l'inversione delle quote in (λ, μ)

**L'idea invertita.** Finora il DC stimava `(λ, μ)` dai **gol**. Ma il mercato li stima
meglio di noi (batte il DC di +0.0165). Quindi si **invertono** le quote per ricavare
i tassi *impliciti* e ci si fa girare sopra la matrice del DC per derivare mercati che
il book **non** prezza (GG/NG).

**La formula (ai minimi quadrati).** Per ogni partita si cerca `(λ, μ)` che riproduce
le probabilità di mercato devigate 1X2 (+ Over 2.5):

```
(λ*, μ*) = argmin_{λ,μ}  [ (q_H−p_H)² + (q_D−p_D)² + (q_A−p_A)² + (q_O−p_O)² ]
dove (q_H, q_D, q_A, q_O) = mercati letti dalla matrice score_matrix(λ, μ, ρ)
```

con inizializzazione informata: il **totale gol** `≈ 2.5 + (p_over−0.5)·2` dall'O/U, e
lo **sbilanciamento** `tilt ≈ 0.5 + (p_home−p_away)·0.6` dal 1X2. `ρ` è **fissato** (il
mercato 1X2+O/U non lo vincola). Da `score_matrix(λ*, μ*, ρ)` si legge `P(GG) = Σ_{i≥1,
j≥1}`.

**Perché non è circolare né un edge.** Sui mercati **con** quote (1X2, O/U) l'inversione
riproduce il mercato → gap ~0 banale. Il valore è tutto nel **derivare** un mercato che
il book non prezza (il GG/NG **non** è tra gli input). Non è un edge contro un mercato
efficiente: è **informazione superiore del mercato trasferita a un mercato non prezzato**.

**Il primo risultato positivo dell'arco modelli.** P(GG) dai `λ,μ` del mercato batte il
DC-da-gol: Δ **−0.0033**, CI95 [−0.0072, +0.0005], P=95.7%, negativo in 6/6 stagioni; ed
è la **prima** cosa a battere la baseline sul GG/NG (0.6865 < 0.6871). La correzione `ρ`
(−0.06) aiuta ancora (0.6853). Onestà: il CI sfiora lo zero ("molto probabile, non
concluso"), il guadagno è modesto, e richiede le quote 1X2+O/U al momento della
predizione. La leva vera è l'**informazione**, non l'architettura.

---

## Fase 25 — Finestra dei dati: piu' storia batte meno (anche per il calcio di oggi)

**Obiettivo.** Il modello scorda il passato in modo MORBIDO (emivita 365g).
Ipotesi da testare (proposta: "fai finta che il calcio pre-COVID non sia
esistito"): tagliare via del tutto le stagioni vecchie, o la sola stagione COVID
a porte chiuse (anomala), aiuta le stagioni recenti?

**Ragionamento.** L'emivita e' un decadimento morbido (una partita di 3 stagioni
fa pesa <0.06). Un taglio NETTO e' diverso: rimuove del tutto quei dati. Se il
calcio evolve, i dati vecchi potrebbero fare rumore -> finestra corta meglio. Se
invece le rose sono stabili, i dati vecchi informano ancora -> finestra corta
peggio (piu' varianza).

**Metodo.** Aggiunti al backtest ``train_window_days`` (taglio netto) e
``drop_train_seasons`` (esclude intere stagioni), senza toccare test o
neopromosse. Sweep sulla config ufficiale, 6 test season, spezzato in
recenti-3 (2023-26) vs vecchie-3 (2020-23).

**Risultato** (`scripts/_run_window.py`; 24 run, source `fase25_window`):

| training | 1X2 tutte | gap | Δ vs "tutto" (recenti-3) |
|---|--:|--:|--:|
| tutto (attuale) | 0.9797 | +0.0165 | — |
| finestra 3 stag | 0.9808 | +0.0176 | +0.0014 |
| finestra 2 stag | 0.9816 | +0.0184 | +0.0035 |
| senza COVID 2020-21 | 0.9803 | +0.0172 | +0.0003 |

Controintuitivo: tagliare i dati vecchi PEGGIORA, e la finestra corta danneggia
DI PIU' proprio le stagioni recenti (+0.0035 sul 2023-26 con 2 stagioni). Perfino
la stagione COVID e' netto-utile (escluderla costa +0.0007).

**Lezione.** Piu' storia batte meno, sempre: le rose di Serie A sono stabili anno
su anno, quindi anche i dati vecchi informano la forza attuale, e buttarli via
aumenta solo la varianza. L'emivita 365g gestisce gia' la recency in modo
ottimale; un taglio netto in aggiunta e' dannoso. Conferma e rafforza la Fase 2b
(memoria lunga). Nota: il parametro ``train_window_days`` resta nel backtest per
leghe piu' volatili, dove il verdetto potrebbe cambiare.

### 📐 In dettaglio — taglio netto vs decadimento morbido

**Due modi di "scordare" il passato.** Il decadimento (emivita 365g) è **morbido**: il
peso di una gara di `k` stagioni fa è `w = 2^{−k}` (0.5, 0.25, 0.125 per 1/2/3
stagioni) — piccolo ma **non zero**. Un taglio netto (`train_window_days` o
`drop_train_seasons`) mette il peso a **zero** oltre la finestra: rimuove del tutto
quei dati.

```
decadimento:  w(k stagioni) = 2^{−k}  > 0          (le usa, sfumate)
taglio netto: w = 0  oltre la finestra              (le butta)
```

**Perché il taglio netto PEGGIORA (bias-varianza, di nuovo).** Se le rose fossero
volatili, i dati vecchi farebbero *bias* → finestra corta meglio. Ma in Serie A le
rose sono **stabili** anno su anno: i dati vecchi hanno bias piccolo e contengono
ancora informazione sulla forza attuale. Buttarli via riduce il campione efficace
`N_eff` → aumenta solo la **varianza**. Ecco perché tagliare a 2 stagioni danneggia di
più proprio le stagioni **recenti** (+0.0035): meno storia = stime più rumorose anche
sul presente. Perfino la stagione COVID (anomala) è netto-utile (escluderla costa
+0.0007): il decadimento la sta già sfumando quanto basta. Conferma e rafforza la Fase
2b: **più storia batte meno, sempre** — e la recency va gestita col decadimento
morbido, non col machete.

---

## Fase 26 — Market-implied su TUTTI i mercati sui gol (il risultato piu' forte)

**Obiettivo.** La Fase 24 ha mostrato che il GG/NG derivato dai lambda,mu del
mercato batte il nostro DC-da-gol e la baseline. Domanda: vale per OGNI mercato
sui gol? Costruire il motore completo e provarlo a fondo (molte strade).

**Ragionamento.** Il mercato stima lambda,mu meglio di noi (+0.0165 sull'1X2);
la matrice del DC li trasferisce coerentemente a ogni mercato basato sui gol,
inclusi quelli che il book NON prezza. Sui mercati con quote (1X2, O/U 2.5)
l'inversione riproduce il mercato (ancoraggi); il valore e' nei mercati derivati.

**Metodo.** Modulo riutilizzabile `src/models/market_implied.py` (inversione ai
minimi quadrati + derivazione di tutti i mercati dalla matrice), con test. Sweep
`scripts/_run_market_implied.py`: ~15 mercati, walk-forward per stagione, CI
bootstrap appaiato. Tre strade laterali: rho della correzione, target
d'inversione (1X2+O/U vs solo 1X2), blend coi nostri lambda,mu.

**Risultato** (7 run, source `fase26_market_implied`):

| mercato | mkt-impl | DC-gol | baseline | Δ vs DC |
|---|--:|--:|--:|--:|
| risultato esatto | 2.8037 | 2.8345 | 2.8974 | -0.0309 |
| multigol | 1.0333 | 1.0470 | 1.0444 | -0.0137 |
| total ospite Ov1.5 | 0.5985 | 0.6111 | 0.6529 | -0.0126 |
| Over 3.5 | 0.5762 | 0.5877 | 0.5864 | -0.0114 |
| GG/NG | 0.6853 | 0.6901 | 0.6871 | -0.0047 |
| pari/dispari | 0.6932 | 0.6930 | 0.6923 | +0.0001 |

- il market-implied batte il DC-da-gol su 13 mercati su 14 (CI95<0 su 12) e la
  baseline su 13 su 14; guadagni maggiori sui mercati ricchi (risultato esatto
  -0.031, multigol, total-squadra);
- l'unica eccezione e' il pari/dispari (+0.0001): la parita' del totale e'
  quasi-casuale, nessun lambda,mu la predice (atteso: non inventa segnale);
- rho: conta poco, un piccolo negativo (-0.06/-0.10) aiuta i punteggi bassi;
- target: 1X2+O/U batte solo-1X2 (l'O/U fissa il livello di gol, servono
  entrambi);
- blend coi nostri lambda,mu: PEGGIORA (il nostro modello non aggiunge nulla al
  mercato — conferma dell'encompassing, Fase 16). Meglio il mercato puro.

**Lezione.** E' il risultato piu' forte del progetto: un MOTORE di pricing
coerente per ogni mercato sui gol, che date le sole quote 1X2+O/U prezza
risultati esatti/multigol/total-squadra/over-under/handicap meglio del nostro
modello e della baseline, in modo statisticamente solido. Conferma la tesi
centrale: la leva e' l'INFORMAZIONE (quella del mercato, trasferita a mercati non
prezzati), non l'architettura. Onesta': non verificabile vs ipotetiche linee di
chiusura di quei mercati (assenti nei dati), richiede le quote 1X2+O/U alla
predizione. Config del motore: inversione 1X2+O/U, rho -0.06, lambda,mu puri del
mercato (niente blend). E' la base pronta per il tool pratico.

### 📐 Il modello in dettaglio — un motore di pricing da (λ, μ) impliciti

Generalizzazione della Fase 24 a **ogni** mercato sui gol, in un modulo riutilizzabile
(`src/models/market_implied.py`): inverti le quote → matrice → deriva tutto.

```
(λ, μ) = implied_lambda_mu(1X2, Over 2.5)          # inversione ai minimi quadrati (Fase 24)
M = score_matrix(λ, μ, ρ = −0.06)                  # matrice dei punteggi
derive_markets(M):
   over_x.5   = Σ_{i+j ≥ x+0.5} M            btts     = Σ_{i≥1, j≥1} M
   home_ov_.5 = Σ_{i ≥ 1} M                  away_ov  = Σ_{j ≥ 1} M
   odd_total  = Σ_{(i+j) dispari} M          home_by_2+ = Σ_{i−j ≥ 2} M
   multigol   = Σ celle nella banda di gol totali (0-1, 2-3, 4+)
   risultato esatto = la cella M(i,j) stessa
```

**Il risultato più forte del progetto.** Il market-implied batte il DC-da-gol su **13
mercati su 14** (CI95<0 su 12) e la baseline su 13/14; guadagni maggiori sui mercati
"ricchi" (risultato esatto −0.031, multigol, total-squadra), dove la forma dettagliata
della matrice conta di più.

**Le eccezioni e i controlli laterali (perché confermano, non smentiscono).**
- *pari/dispari del totale* (+0.0001): la parità di `i+j` è **quasi-casuale**, nessun
  `(λ,μ)` la predice. Il motore **non inventa** segnale dove non c'è — è una prova di
  onestà, non un difetto.
- *target d'inversione*: 1X2+O/U batte solo-1X2, perché l'O/U **fissa il livello** di
  gol (`λ+μ`) e il 1X2 ne fissa lo **sbilanciamento** — servono entrambi per
  identificare `(λ, μ)`.
- *blend coi nostri λ,μ*: **peggiora** → il nostro modello non aggiunge nulla al
  mercato (conferma dell'encompassing, Fase 16). Meglio il mercato **puro**.

La tesi centrale, dimostrata: la leva è l'**informazione** (quella del mercato,
trasferita a mercati non prezzati), non l'architettura.

---

## Fase 27 — Ottimizzare la forma dei punteggi sul market-implied (gia' ottima)

**Obiettivo.** Spremere il market-implied: i lambda,mu vengono dal mercato
(ottimi), ma la FORMA della distribuzione attorno a loro e' nostra, e in Fase 26
rho=-0.06 era fissato a occhio. Impararla dai risultati reali puo' migliorare i
mercati derivati (soprattutto risultato esatto e code)?

**Ragionamento.** La forma e' un parametro GLOBALE (non per-squadra), quindi
fittabile a bassa varianza sui risultati passati e applicabile in avanti (niente
look-ahead). Varianti: rho fittato; rho + inflazione diagonale phi (Fase 12b);
binomiale negativa (over-dispersione dei gol). Non serve il DC: il motore usa
solo quote + matrice, si lavora dallo snapshot.

**Risultato** (`scripts/_run_shape.py`; 1 run summary, source `fase27_shape`):

| forma | risultato esatto | Δ vs Fase 26 |
|---|--:|--:|
| rho=-0.06 (Fase 26) | 2.8037 | — |
| rho fittato (~-0.074) | 2.8038 | +0.0002 (rumore) |
| rho + phi (~0.09) | 2.8025 | -0.0011 [-0.0025, +0.0003] |
| binom. negativa | 2.8045 | +0.0009 (peggio) |

- rho fittato ~ rho fisso: il -0.06 a occhio era gia' giusto, fittarlo non aiuta;
- inflazione diagonale phi: guadagno minuscolo e NON conclusivo (CI include lo
  zero) solo sul risultato esatto -> non adottata;
- binomiale negativa RIGETTATA: il fit spinge la dispersione verso la Poisson
  (nb_size ~200) e peggiora -> i gol, con lambda dal mercato, sono Poisson, non
  over-dispersi.

**Lezione.** La forma della Fase 26 era gia' essenzialmente ottima: i lambda,mu
del mercato sono tutta la storia, la Poisson+rho attorno a loro e' il meglio.
Il market-implied ha toccato il suo tetto anche sulla dimensione della forma:
per spingere oltre servirebbero PIU' input di mercato (altre linee O/U, handicap
asiatici) per vincolare meglio i lambda,mu — che lo snapshot non ha. Il motore
e' maturo cosi' com'e'.

### 📐 Il modello in dettaglio — le tre forme provate e perché la Poisson vince

I `(λ, μ)` vengono dal mercato (ottimi); qui si tara solo la **forma** della
distribuzione attorno a loro — un parametro **globale** (non per-squadra), quindi
fittabile a bassa varianza sui risultati passati e applicabile in avanti.

**1) `ρ` fittato** (correzione DC): esce **~−0.074**, praticamente uguale al −0.06
fissato a occhio → Δ +0.0002 (rumore). *Il valore a occhio era già giusto.*

**2) `ρ + φ`** (inflazione diagonale, Fase 12b): `φ ~0.09`, guadagno minuscolo e **non
conclusivo** (CI include lo zero) solo sul risultato esatto → non adottato.

**3) Binomiale negativa** (over-dispersione dei gol). Sostituisce le marginali Poisson
con:

```
Var(gol) = media + media² / size          (size → ∞  ⇒  ricade nella Poisson)
```

Il fit spinge `size ~200` (cioè **verso** la Poisson) e **peggiora** (+0.0009) →
**rigettata**. Conclusione pulita: **con i λ dal mercato, i gol sono Poisson, non
over-dispersi.** La forma della Fase 26 era già essenzialmente ottima; per spingere
oltre servirebbero *più input di mercato* (altre linee O/U, handicap asiatici) per
vincolare meglio `(λ, μ)` — non una forma diversa.

---

## Fase 28 — Quando falliscono i modelli? Errore per momento della stagione

**Obiettivo.** Ipotesi: a fine campionato alcune squadre non lottano piu' per
nulla (gia' salve o retrocesse), quindi le ultime giornate sono piu' "ballerine".
Ma la domanda decisiva: e' un fallimento NOSTRO o falliscono TUTTI (mercato
incluso)?

**Ragionamento.** Se a fine stagione peggiorano sia modello SIA mercato e il GAP
resta piatto -> casualita' irriducibile, non un nostro difetto (nemmeno dati
sulla motivazione aiuterebbero, neanche il mercato la prezza). Se il GAP si
allarga -> il mercato prezza la posta in palio e noi no: difetto nostro, dati
nuovi utili. Log-loss modello e mercato per giornata (stimata ordinando le
partite per data, gruppi di 10).

**Risultato** (`scripts/_run_matchday.py`; 7 run, source `fase28_matchday`):

| giornate | modello | mercato | gap |
|---|--:|--:|--:|
| 1-6 | 0.9725 | 0.9580 | +0.0145 |
| 7-19 | 0.9744 | 0.9569 | +0.0175 |
| 20-31 | 0.9631 | 0.9507 | +0.0124 |
| 32-34 | 1.0328 | 1.0125 | +0.0203 |
| 35-38 | 1.0179 | 0.9921 | +0.0258 |

- il finale (32-38) e' molto piu' difficile per ENTRAMBI (log-loss ~0.96 ->
  ~1.02 sia modello sia mercato): le ultime giornate sono davvero piu' ballerine,
  ma per chiunque -> casualita' irriducibile;
- il gap RADDOPPIA verso la fine (+0.0124 a meta' -> +0.0258 nel finale): indizio
  che il mercato prezzi la posta in palio meglio di noi;
- MA il test e' non conclusivo: Δ gap late(35-38)-vs-resto +0.0104, CI95
  [-0.0196, +0.0395], include lo zero (240 partite finali ad alta varianza, poca
  potenza). Tendenza pulita nei bucket, non un fatto dimostrato.

**Lezione.** L'ipotesi "finale ballerino" e' confermata ma in gran parte
UNIVERSALE (fatica anche il mercato -> non risolvibile). C'e' un indizio non
provato di un gap model-specifico nelle ultime giornate: e' li' che dei dati
sulla POSTA IN PALIO potrebbero aiutare. Nota chiave: un primo taglio di "posta
in palio" NON richiede dati esterni -- e' derivabile dalla classifica a ogni
giornata (squadra gia' matematicamente salva / retrocessa / in corsa). E' la
Fase 29 naturale, a costo zero di dati nuovi.

### 📐 In dettaglio — il test che distingue "colpa nostra" da "difficile per tutti"

**La logica diagnostica.** Si guarda la log-loss di **modello E mercato** per fascia di
giornate, e soprattutto il loro **gap**:

```
se log-loss ↑ per entrambi  E  gap piatto   →  casualità irriducibile (non un difetto nostro)
se il GAP si allarga                          →  il mercato prezza qualcosa che noi no (difetto nostro, dati utili)
```

**I numeri.** Il finale (giornate 32-38) è molto più difficile per **entrambi**
(log-loss ~0.96 → ~1.02 sia modello sia mercato) → in gran parte difficoltà
**universale**. Ma il gap **raddoppia** (+0.0124 a metà → +0.0258 nel finale): indizio
che il mercato prezzi la posta in palio meglio di noi.

**Perché è solo un indizio, non un fatto.** Il test formale è **non conclusivo**:

```
Δ gap (giornate 35-38 vs resto) = +0.0104 ,  CI95 [−0.0196, +0.0395]  →  include lo zero
```

Solo 240 partite finali, ad alta varianza → poca potenza. La tendenza nei bucket è
pulita, ma statisticamente non dimostrata. Ecco perché la Fase 29 va a cercare la
*causa* (motivazione/posta in palio) sui dati di classifica, a costo zero.

---

## Fase 29 — Posta in palio: i "dead rubber" spiegano il finale? (NO)

**Obiettivo.** La Fase 28 ha visto un indizio (non concluso) che il modello ci
perda un po' piu' del mercato nel finale. Se la causa e' la MOTIVAZIONE (squadre
gia' salve e fuori dall'Europa senza piu' nulla in gioco), il gap dovrebbe essere
maggiore proprio nei "dead rubber". Testabile SENZA dati esterni, dalla classifica.

**Ragionamento.** Per ogni squadra, con la classifica PRIMA della partita:
reach=3*gare_rimaste; fighting_relegation se (punti - linea_salvezza) <= reach;
chasing_europe se punti >= linea_europa - reach; dead_rubber se nessuno dei due
(limbo mid-table). Partita dead = entrambe (o almeno una) in dead_rubber. Test
diagnostico: gap modello-mercato dead vs live, CI bootstrap.

**Risultato** (`scripts/_run_stakes.py`; 7 run, source `fase29_stakes`):

| definizione | n | gap dead | gap live | Δ (dead-live) |
|---|--:|--:|--:|--:|
| entrambe dead | 12 (0.5%) | -0.069 | +0.017 | -0.086 [-0.14,-0.03] * |
| almeno una dead | 99 (4.3%) | +0.005 | +0.017 | -0.012 [-0.058,+0.035] |

- sul campione affidabile (99; le 12 "entrambe" troppo poche) NESSUN effetto (CI
  include lo zero);
- direzione comunque NEGATIVA: nei dead rubber il modello e' semmai leggermente
  MIGLIORE del mercato — l'opposto di "il mercato prezza la motivazione e noi no";
- corr(dead, gap) ~ 0.

**Lezione.** I dead rubber NON spiegano la difficolta' del finale: sono troppo
rari (0.5-4.3%) e dove la posta e' bassa il modello non fa peggio. Il finale e'
difficile per casualita' diffusa (Fase 28), non per una posta in palio che ci
sfugge. Consegue che cercare dati esterni sulla motivazione probabilmente NON
aiuterebbe: risultato utile, evita un investimento sbagliato. La caccia al
"perche' il finale e' piu' difficile" si sposta da "motivazione" a "varianza
strutturale delle ultime giornate" (Fase 30: pattern dentro la stagione).

### 📐 In dettaglio — il classificatore "dead rubber" (e il suo difetto)

**La logica (dalla classifica PRIMA della partita, solo gare precedenti → no
look-ahead).** Con `reach = 3 · gare_rimaste` (i punti ancora ottenibili):

```
in_lotta_salvezza  se  (punti − linea_salvezza) ≤ reach
in_corsa_Europa    se   punti ≥ (linea_Europa − reach)
dead_rubber        se  NESSUNO dei due  (limbo mid-table)
```

**Il risultato.** Sul campione affidabile (99 partite con almeno una squadra "dead"; le
12 "entrambe dead" sono troppo poche) **nessun effetto**: gap dead ≈ gap live (CI
include lo zero), corr(dead, gap) ≈ 0. Anzi la direzione è semmai **negativa** (nei
dead rubber il modello è un filo *migliore* del mercato) — l'opposto di "il mercato
prezza la motivazione e noi no".

**Il difetto nascosto (che la Fase 31 correggerà).** Questa definizione è **sbagliata
ai due estremi**: conta una squadra già **retrocessa** come "in lotta salvezza" (è
sotto la linea, quindi `punti − linea ≤ reach` scatta) e una già **campione** come "in
corsa titolo". Cioè classifica come *ancora in gioco* proprio le squadre che non lo
sono più. Con la definizione corretta (Fase 31: DECISA = nessuna corsa aperta, inclusi
retrocessa e campione) la conclusione si **ribalta**. Lezione di metodo: un
classificatore sbagliato ai bordi, su 12 partite, capovolge il verdetto.

---

## Fase 30 — Pattern dentro la stagione: anatomia per periodo

**Obiettivo.** Cercare pattern DENTRO la stagione: per ogni periodo, non solo il
gap ma cosa cambia (pareggi, gol, vantaggio-casa, entropia degli esiti), per
capire perche' certi momenti sono piu' difficili e se il pattern e' coerente tra
le 6 stagioni.

**Risultato** (`scripts/_run_season_patterns.py`; 7 run, source
`fase30_season_patterns`):

| giornate | gap | %casa | %pari | %osp | gol/g | entropia |
|---|--:|--:|--:|--:|--:|--:|
| 1-6 | +0.0145 | 39.7% | 28.9% | 31.4% | 2.84 | 1.089 |
| 7-19 | +0.0175 | 40.5% | 26.4% | 33.1% | 2.64 | 1.084 |
| 20-31 | +0.0124 | 41.9% | 26.0% | 32.1% | 2.60 | 1.079 |
| 32-34 | +0.0203 | 41.1% | 31.1% | 27.8% | 2.56 | 1.085 |
| 35-38 | +0.0258 | 36.2% | 25.4% | 38.3% | 2.90 | 1.084 |

Tre scoperte:
1. NON e' entropia: l'entropia degli esiti e' piatta -> il finale piu' difficile
   non e' dovuto a esiti piu' bilanciati (spiegazione meccanica esclusa);
2. due cambi strutturali reali: giornate 32-34 tese e bloccate (pareggi 31%,
   pochi gol, log-loss alto per tutti = scontri decisivi col freno a mano);
   giornate 35-38 dove il VANTAGGIO-CASA CROLLA (casa 40%->36%, trasferta
   31%->38%, piu' gol) = effetto fine stagione;
3. nessun pattern robusto nel gap: correlazioni con la giornata ~0 (gap +0.0056),
   gap fine-inizio positivo solo in 3 stagioni su 6 (media +0.0015, range
   -0.017..+0.021) -> l'indizio della Fase 28 NON e' coerente tra stagioni.

**Lezione.** Il finale piu' difficile e' reale ma non ha un pattern-gap robusto:
riguarda tutti (mercato incluso), non e' entropia ne' motivazione (Fase 29). Il
candidato concreto che emerge e' il CROLLO DEL VANTAGGIO-CASA nel finale (il
modello eredita un home-advantage dallo storico che nelle ultime giornate si
riduce, come nel COVID Fase 9) -- molto piu' promettente della motivazione, ma
marginale finche' il gap non sale in modo robusto. E' un candidato per una
covariata "giornata avanzata -> attenua il vantaggio-casa", da valutare con
prudenza (rischio overfitting su un effetto piccolo).

### 📐 In dettaglio — l'entropia degli esiti e cosa esclude

**La metrica chiave: entropia degli esiti** (quanto sono "bilanciati" H/D/A in un
periodo):

```
entropia = − Σ_{k ∈ {H,D,A}}  f_k · ln f_k        (f_k = frequenza dell'esito k nel periodo)
```

Massimo teorico `ln 3 ≈ 1.099` (tre esiti equiprobabili = massima imprevedibilità).

**Cosa dimostra il fatto che sia PIATTA (~1.08 ovunque).** Se il finale fosse più
difficile *perché* gli esiti diventano più bilanciati (più imprevedibili di per sé),
l'entropia salirebbe nelle ultime giornate. Invece è **piatta** (1.089 → 1.084) →
la spiegazione "meccanica" (esiti più equilibrati) è **esclusa**. Il finale difficile
non viene da lì.

**Cosa emerge invece.** Due cambi strutturali reali: giornate **32-34** tese e bloccate
(pareggi 31%, pochi gol, log-loss alto per tutti = scontri decisivi col freno a mano);
giornate **35-38** dove il **vantaggio-casa CROLLA** (casa 40%→36%, trasferta 31%→38%,
più gol). Quest'ultimo è lo stesso meccanismo del COVID (γ globale ereditato dallo
storico che nel finale non regge, Fase 9-bis) → candidato per una covariata "giornata
avanzata → attenua il vantaggio-casa". Ma **nessun pattern-gap robusto**: corr(gap,
giornata) ≈ 0, gap fine−inizio positivo solo in 3 stagioni su 6 (media +0.0015, range
−0.017…+0.021) → l'indizio della Fase 28 **non è coerente** tra stagioni. Prudenza:
overfitting su un effetto piccolo.

---

## Fase 31 — Posta in palio corretta (8 stagioni): conta l'ASIMMETRIA

**Obiettivo.** La Fase 29 (dead rubber = "salva E fuori dall'Europa") era
sbagliata ai due estremi: contava una squadra gia' RETROCESSA come "in lotta
salvezza" e una gia' CAMPIONE come "in corsa titolo". Definizione corretta
(DECISA = nessuna corsa aperta, inclusi retrocessa e campione), su 8 stagioni,
con molte combinazioni a livello partita.

**Risultato** (`scripts/_run_stakes2.py`; 9 run, source `fase31_stakes2`; n=3040):

Stati-squadra (su 6080): in_corsa 5795, salva_limbo 147, europa_decisa 70,
retrocessa 45, campione 23 (solo 4.7% "deciso").

| categoria | n | gap | CI95 |
|---|--:|--:|--:|
| entrambe in corsa | 2831 | +0.0172 | [+0.0122, +0.0221] |
| una decisa, una in corsa | 133 | +0.0572 | [+0.0139, +0.1014] * |
| entrambe decise | 76 | +0.0130 | [-0.035, +0.060] |
| coinvolge una campione | 23 | +0.0949 | [+0.013, +0.179] * |

- RIBALTA la Fase 29: escludendo le partite con >=1 squadra decisa il gap SCENDE
  da +0.0188 a +0.0172 (quelle partite hanno gap +0.0411) -> su di esse il
  modello va PEGGIO del mercato, non meglio (la Fase 29, col classificatore rotto
  e 12 partite, concludeva l'opposto);
- il segnale e' l'ASIMMETRIA: "una decisa, una in corsa" ha gap triplo (+0.057 vs
  +0.017, CI esclude lo zero); "entrambe decise" invece niente.

**Lezione.** Quando una squadra non ha piu' nulla in gioco e l'altra lotta, la
squadra motivata sovra-rende / quella scarica molla: il mercato lo prezza, noi
no (usiamo la forza stagionale, ciechi alla motivazione del momento). E' il primo
LEAD azionabile dai dati interni. Onesta': campioni piccoli (133 la categoria piu'
solida, 23-76 le altre) e molti test -> indizio forte e sensato, non una prova; e
l'effetto e' SOLO nell'asimmetria, non quando entrambe sono decise (coerente col
meccanismo). Candidato: una covariata "stakes mismatch" (una squadra decisa vs
una in corsa) che attenui la previsione a favore della squadra motivata, da
validare walk-forward prima di adottare. Indica anche quali dati esterni
cercherebbero valore (indicatori di motivazione/asimmetria), ma il primo taglio
e' gia' nei dati (dalla classifica). METODO: la Fase 29 mostra quanto conta una
definizione corretta -- un classificatore sbagliato ai bordi ribaltava la
conclusione.

### 📐 In dettaglio — il classificatore CORRETTO e il segnale di asimmetria

**La definizione giusta (`loader.add_stakes`).** Una squadra è **DECISA** (`settled=1`)
se non ha *nessuna* corsa aperta — inclusi i due estremi che la Fase 29 sbagliava. Con
`reach = 3·(gare_rimaste)`:

```
math_safe   = punti  >  linea_18ª + reach           (già matematicamente salva)
math_releg  = punti + reach  <  linea_17ª            (già matematicamente retrocessa)
releg_open  = (not math_safe) and (not math_releg)   (salvezza ancora in gioco)
euro_open   = |punti − linea_Europa| ≤ reach
champion    = leader and (punti − 2ª) > reach        (già campione)
title_open  = (|punti − linea_titolo| ≤ reach) and (not champion)

settled = 0  se (releg_open or euro_open or title_open)   [in corsa]
settled = 1  altrimenti  [decisa: retrocessa, campione, o limbo mid-table]
```

La differenza chiave vs Fase 29: retrocessa e campione ora contano come **decise**
(prima erano classificate "in corsa" ai bordi).

**Il segnale è l'ASIMMETRIA (non il "dead rubber" simmetrico).** Con la definizione
corretta, il gap per categoria di partita:

```
entrambe in corsa          gap +0.0172   [CI +0.0122, +0.0221]
UNA decisa, UNA in corsa   gap +0.0572   [CI +0.0139, +0.1014] *   ← ~3x, CI esclude lo zero
entrambe decise            gap +0.0130   [CI −0.035, +0.060]       (niente)
coinvolge una campione     gap +0.0949   [CI +0.013, +0.179] *
```

**Ribalta la Fase 29**: escludendo le partite con ≥1 squadra decisa il gap **scende**
(+0.0188→+0.0172) → su quelle partite il modello va **peggio** del mercato, non meglio.
Il segnale è **solo** nell'asimmetria (una decisa vs una in corsa), non quando
entrambe sono decise — coerente col meccanismo: la squadra motivata sovra-rende / quella
scarica molla, il mercato lo prezza e noi (che usiamo la forza *stagionale*, ciechi
alla motivazione del momento) no. È il **primo lead azionabile dai dati interni**.
Onestà: campioni piccoli (133 la categoria più solida) e molti test → indizio forte e
sensato, non una prova.

---

## Fase 32 — Validazione della covariata stakes-mismatch (DC e GBM)

**Obiettivo.** Il lead della Fase 31 (una squadra decisa vs una in corsa -> il
modello perde piu' del mercato) regge WALK-FORWARD, come covariata? Testato su
ENTRAMBI i modelli (richiesta esplicita: non solo il DC).

**Ragionamento.** Covariata `stakes` (1=decisa/0=in corsa, dalla classifica;
`loader.add_stakes`, registrata in `_COVARIATES`, off di default). Nel DC entra
nel fit come le altre covariate (`--covariates stakes`); nel GBM come feature
aggiuntive (home_settled, away_settled, differenza). Il segnale e' su ~5% di
partite (mismatch), quindi l'effetto OVERALL sara' minuscolo per costruzione: il
test vero e' sulla riga MISMATCH.

**Risultato** (`scripts/_run_stakes_cov.py`; 15 run, source `fase32_stakes_cov`):

| modello | subset | log-loss base->stakes | Δ (CI95) |
|---|---|--:|--:|
| DC | overall | 0.9797->0.9796 | -0.0001 [-0.0007,+0.0005] |
| DC | mismatch (n=99) | 0.9609->0.9587 | -0.0022 [-0.0157,+0.0114] |
| GBM | overall | 1.0098->1.0096 | -0.0001 [-0.0014,+0.0012] |
| GBM | mismatch (n=99) | 0.9968->0.9841 | -0.0127 [-0.0283,+0.0030] |

- direzione CONFERMATA su entrambi: sulle partite mismatch la covariata aiuta sia
  il DC (-0.0022) sia il GBM (-0.0127), entrambe negative;
- il GBM la cattura MOLTO meglio del DC (-0.0127 vs -0.0022): l'effetto "la
  squadra scarica sotto-rende" e' non-lineare, il GBM modella l'interazione
  mentre il DC puo' solo spostare linearmente il tasso-gol;
- MA nessuno e' conclusivo (CI includono lo zero, il GBM per un pelo: +0.0030).

**Lezione.** Non adottata (regola: CI<0), ma e' il LEAD interno piu' credibile
del progetto: direzione giusta su DUE architetture indipendenti, meccanismo
chiaro, effetto concentrato dove previsto -- diverso dai "residui = rumore" delle
Fasi 13/20, dove i segni erano casuali. Il rumore puro non darebbe due negativi
concordi. Serve solo piu' campione (piu' stagioni o il futuro out-of-sample) per
superare la soglia. Nota per il futuro: se si usera' questo segnale, il GBM e' il
veicolo giusto (lo cattura ~6x meglio del DC). Infrastruttura pronta: covariata
`stakes` disponibile, off di default.

### 📐 Il modello in dettaglio — come entra `stakes` nei due modelli

**Nel DC** la covariata entra come le altre (Fase 4c), nel log-tasso:

```
cov = β · ( z_settled,casa − z_settled,ospite )     con settled ∈ {0, 1}
```

Può solo spostare **linearmente** il tasso-gol in funzione della differenza di stato.

**Nel GBM** entra come feature aggiuntive (`home_settled`, `away_settled`, e la loro
differenza), dove può interagire in modo **non-lineare** con le altre.

**Perché il test vero è sulla riga MISMATCH.** Il segnale è su ~5% di partite (una
decisa vs una in corsa), quindi l'effetto **overall** è minuscolo per costruzione
(diluito nel 95% di partite senza mismatch). Ecco i numeri:

```
DC   overall  0.9797→0.9796  Δ −0.0001            mismatch (n=99)  0.9609→0.9587  Δ −0.0022
GBM  overall  1.0098→1.0096  Δ −0.0001            mismatch (n=99)  0.9968→0.9841  Δ −0.0127
```

**Cosa dicono.** Direzione **confermata su entrambe le architetture** (entrambe
negative sulla riga mismatch). Il GBM la cattura ~**6x** meglio del DC (−0.0127 vs
−0.0022): l'effetto "la squadra scarica sotto-rende" è **non-lineare** (una soglia
di comportamento), che il GBM modella e il DC lineare no. Ma **nessuno è conclusivo**
(i CI includono lo zero, il GBM per un pelo: +0.0030) → **non adottato** (regola: CI<0).

**Perché resta il lead più credibile del progetto.** Due negativi **concordi** su due
architetture indipendenti, meccanismo chiaro, effetto concentrato dove previsto — a
differenza dei "residui = rumore" delle Fasi 13/20, dove i segni erano casuali. Il
rumore puro non darebbe due negativi concordi. Serve solo più campione (più stagioni o
il futuro OOS). Se si userà, il **GBM** è il veicolo giusto.

---

## Fase 33 — Ultime covariate mai provate: PPDA/deep e finishing-luck (ridondanti)

**Obiettivo.** Chiudere onestamente il capitolo "spremere i dati interni": nello
snapshot restavano DUE segnali mai messi nel modello -- PPDA/deep (tattica) e
finishing-luck (gol-xG rolling, mean-reversion). Sono gli ultimi segnali interni
inesplorati.

**Ragionamento.** Feature ROLLING pre-partita (no look-ahead), aggiunte al loader
(`add_style_luck`) e registrate come covariate `ppda`/`deep`/`luck` (off di
default). Testate su DC (nel fit) e GBM (feature), disciplina solita (overall 1X2
log-loss + gap, CI). Aspettativa onesta: probabilmente ridondanti (l'xG cattura
gia' la qualita' delle occasioni), ma vanno provate per chiudere il libro.

**Risultato** (`scripts/_run_style_luck.py`; 27 run, source `fase33_style_luck`):

DC: base 0.9797; +ppda+deep 0.9806 (Δ +0.0009 [-0.0012,+0.0030]); +luck 0.9797
(Δ -0.0000 [-0.0006,+0.0006]); +tutte 0.9807. GBM: 1.0107 -> 1.0085 (Δ -0.0022
[-0.0072,+0.0028], P 81%).

- PPDA/deep RIDONDANTI: peggiorano appena il DC (lo stile e' gia' implicito in
  gol+xG, come il valore-rosa Fase 4c);
- finishing-luck effetto ESATTAMENTE ZERO sul DC: conferma elegante che il blend
  gol/xG (alpha=0.75) e' gia' il meccanismo di mean-reversion -- pesa gol e xG in
  modo ottimale, quindi "la fortuna regredisce" non aggiunge nulla;
- il GBM estrae un capello dalle feature tattiche (-0.0022, 81%) che il DC lineare
  non vede, ma non conclusivo e irrilevante (resta ben peggio del DC).

**Lezione.** Con la Fase 33 i DATI INTERNI SONO COMPLETAMENTE ESPLORATI: tutto lo
snapshot (gol, xG, npxG, PPDA, deep, valore-rosa, assenze, riposo, forma, stakes)
e' stato testato. Il tetto e' informativo, confermato per l'ultima volta coi
segnali rimasti. Il finishing-luck a zero e' la nota piu' istruttiva: un'ipotesi
sensata (mean-reversion) che il modello incorporava gia'. L'unico lead vivo resta
lo stakes-mismatch (Fase 32), che serve piu' stagioni. Ogni altro guadagno ora
richiede INFORMAZIONE NUOVA (formazioni, quote live) o un avversario meno
efficiente (leghe/mercati diversi): finisce la strada "spremere lo snapshot".

### 📐 Il modello in dettaglio — le feature rolling e perché luck = 0 esatto

**Le feature** (`loader.add_style_luck`, rolling sulle ultime 8 gare della squadra,
solo precedenti → no look-ahead):

```
ppda_roll = media( PPDA )        # passaggi avversari per azione difensiva = intensità di pressing
deep_roll = media( deep )        # completamenti in zona profonda = dominio territoriale
luck      = media( gol − xG )    # sovra/sotto-rendimento realizzativo ("fortuna sotto porta")
```

`luck` codifica l'ipotesi di **mean-reversion**: chi ha segnato *sopra* il suo xG
dovrebbe regredire (segnare meno in futuro).

**Perché PPDA/deep sono ridondanti.** Lo **stile** (come pressa/domina una squadra) si
traduce in occasioni, e le occasioni sono già catturate dall'**xG** nel blend →
PPDA/deep peggiorano appena il DC (+0.0009), come il valore-rosa (Fase 4c). Stessa
diagnosi: informazione già implicita in gol+xG.

**Perché `luck` dà effetto ESATTAMENTE ZERO sul DC (la nota più istruttiva).** È una
conferma elegante e *prevedibile* dalla struttura del modello. Il blend è:

```
λ = 0.75 · λ_gol + 0.25 · λ_xg
```

Questo blend **è già** un meccanismo di mean-reversion: pesa i gol realizzati (che
includono la fortuna) *insieme* all'xG (la qualità sottostante, senza fortuna). Una
squadra che ha segnato sopra l'xG ha `λ_gol > λ_xg`, e il blend la tira già verso il
basso col peso 0.25 sull'xG. Aggiungere `luck = gol − xG` come covariata significa
aggiungere una funzione **degli stessi due ingredienti già combinati** → contributo
nullo, non "piccolo": **zero esatto**. È la dimostrazione più pulita che α=0.75 non è
un numero arbitrario, ma *è* la correzione della fortuna.

**Verdetto finale del filone.** Con la Fase 33 i dati interni sono completamente
esplorati (gol, xG, npxG, PPDA, deep, valore-rosa, assenze, riposo, forma, stakes,
luck): il tetto è **informativo**, confermato per l'ultima volta. Ogni altro guadagno
richiede **informazione nuova** o un **avversario meno efficiente**.

---

## Fase 34 — Audit critico: caccia a errori, superficialità e leve mai testate

**Obiettivo.** Rivedere TUTTO il lavoro (Fasi 0-33) con occhio avversariale: (a)
c'è un errore in qualche formula? (b) c'è un ragionamento chiuso troppo in fretta?
(c) qualche feature disattivata, o una dimensione mai provata, può ancora aiutare i
modelli attuali (DC ufficiale e GBM)? Non per un edge miracoloso, ma per portare i
modelli al loro *vero* massimo — anche in vista del porting ad altre leghe.

**Ragionamento / ipotesi.** Un audit onesto parte dal **codice**, non dai documenti.
Ho riletto riga per riga `dixon_coles.py`, `market_implied.py`, `calibration.py`,
`metrics.py`, `markets.py`, `experiment_log.py`, `loader.py`, `backtest.py` e gli
script GBM. Poi ho testato le ipotesi vive con **diagnostici e test economici**
(`scripts/_run_audit_diagnostics.py`), riusando la ricalibrazione per-classe (Fase
10) — nessuna modifica al modello — con regola dichiarata prima: una leva è "viva"
solo se il Δ log-loss è <0 con **CI95 bootstrap che esclude lo zero** (altrimenti è
la trappola calibrazione-vs-log-loss della Fase 12b).

**Alternative considerate.** Modificare subito il modello (aggiungere un termine
strutturale sul pareggio) e misurarlo walk-forward, oppure prima il test **post-hoc
economico** che dice se la leva è viva *senza* la chirurgia. Scelto il post-hoc
(principio: testa la versione economica prima di investire); se sopravvive, allora la
si costruisce nel modello.

**Risultato.**

*1) Formule — NESSUN errore.* Verosimiglianza pesata, decadimento, correzione τ
(segni inclusi), inflazione φ (formula di `_fit_draw_phi` con la sua `Z` di
rinormalizzazione), rho dinamico, blend, conversione, covariate, inversione
market-implied, devig, log-loss/Brier, temperature, ricalibrazione per-classe, ROI e
CLV: tutte corrette e coerenti col codice. Il walk-forward è pulito (`date < as_of`
ovunque). *Questo è un risultato: dopo l'audit di Fase 15 sui numeri, questo è
l'audit sulle formule — entrambi puliti.*

*2) D1 — vantaggio-casa a fine stagione: miscalibrazione REALE ma NON sfruttabile.*
Nelle ultime giornate la casa vince molto meno (35-38: **36.2%** vs ~41% a metà) e
il modello la **sovrastima** (P(casa) media 0.414 → bias **+0.051**). Ma il mercato
la sovrastima **ancora di più** (+0.062): su questa dimensione siamo già meglio del
mercato. Sembrava una leva d'oro. Il test economico la **uccide**: ricalibrare il
finale (w_casa appreso ≈0.85-0.90) dà Δ **+0.0021** (35-38) e **+0.0042** (32-38),
entrambi *peggiori*, CI che include lo zero. È **esattamente** la trappola della Fase
12b: la miscalibrazione media è reale, ma *quanto* crolla la casa varia di anno in
anno, quindi correggere la media non aiuta il log-loss. La cautela della Fase 30 era
giusta. Resta utile solo per **probabilità calibrate** a uso pratico, non per un edge.

*3) D2 — il pareggio dipende dall'EQUILIBRIO |λ−μ|, dimensione MAI testata.* Qui il
ragionamento passato era davvero superficiale: le tre vie strutturali sul pareggio
(τ, φ Fase 12b, rho dinamico Fase 18) hanno esplorato solo il **totale** dei gol
attesi (λ+μ) o un fattore costante — **mai la bilancia** |λ−μ|. Il diagnostico:

| quartile \|λ−μ\| | pari reale | mod P(pari) | mkt P(pari) | mod−reale |
|---|--:|--:|--:|--:|
| equilibrata | 0.332 | 0.287 | 0.296 | **−0.044** |
| medio-bassa | 0.288 | 0.276 | 0.282 | −0.012 |
| medio-alta | 0.272 | 0.253 | 0.253 | −0.019 |
| sbilanciata | 0.186 | 0.198 | 0.196 | +0.012 |

Il deficit-pareggio è **concentrato nelle partite equilibrate** (−0.044, il modello
prezza 28.7% dove il reale è 33.2%), e il mercato fa meglio ma poco (−0.036). Il test
economico: ricalibrare le sole partite equilibrate dà Δ **−0.0014** (P(migliora)
**77%**, CI [−0.0052, +0.0024]) — **~4× la ricalibrazione globale** (−0.0003, P 59%)
della Fase 10. Non conclusivo (CI include lo zero → regola non soddisfatta) ma è **il
lead strutturale più promettente del progetto**: la variabile di condizionamento
giusta è |λ−μ|, e non è mai stata provata dentro il modello.

*4) D3 — copertura di squad_value: 71.7%.* La bocciatura della Fase 4c ("non aiuta")
è stata misurata su ~72% delle partite; sul restante 28% la covariata era **neutra**
(z=0, valore mancante). La direzione era negativa, quindi difficilmente si
ribalterebbe, ma il test era **diluito**: onestà dovuta.

*5) Punti dal codice (non da diagnostico) — dove il lavoro è stato superficiale.*
- **Il GBM (Fase 22) non ha MAI visto stakes/luck/ppda/deep.** Il suo `cov_block`
  usa {forma, rest_full, valore, assenze, midweek}; `stakes` (il lead più credibile,
  Fase 32, che il GBM cattura ~6× meglio del DC) e `luck/ppda/deep` (Fase 33) sono
  arrivati dopo o testati a parte. La combinazione **non-lineare completa** — proprio
  quella in cui gli effetti a soglia si sommano — non è mai stata provata.
- **I flag `home/away_midweek_europe` esistono nei dati ma non sono covariate DC**
  (né sono mai stati isolati): un **dummy** di congestione ("ha giocato in Europa
  infrasettimana") è più robusto del `rest_full` continuo, che degrada dove la
  copertura coppe manca (Fase 4e).
- **Le covariate entrano SOLO nel sotto-modello dei gol**, non in quello del segnale
  (xG): con α=0.75 il loro effetto sul tasso *blendato* è diluito — una possibile
  ragione per cui sembrano più deboli del dovuto.
- **Il market-implied inverte ogni partita in modo indipendente**: nessun
  *denoising* cross-partita (es. shrinkage stagionale dei λ,μ impliciti per squadra),
  mai tentato.
- **Interazione prior/identificabilità:** la penalità impone media(attacco)=0 mentre
  il prior tira 3 promosse a −δ → un lieve spostamento compensativo delle altre
  squadre. Effetto piccolo, ma è un accoppiamento dato per scontato, da tenere
  d'occhio quando le promosse sono molte (es. leghe con più retrocessioni).

**Lezione / cosa ne consegue.**
1. **Le formule sono solide.** Il "tetto informativo" non nasconde un bug.
2. Il "tetto" resta vero *in aggregato*, ma l'audit trova **una crepa strutturale
   non sfruttata**: il pareggio nelle partite equilibrate (|λ−μ| piccolo). È l'unica
   via sul pareggio mai provata, ed è la più promettente (−0.0014, P 77%). **Prossimo
   candidato (Fase 35): un boost-pareggio in-modello condizionato a |λ−μ|** (φ o ρ
   funzione della bilancia, fittato nella verosimiglianza, regola CI<0 pre-dichiarata).
3. **Per il GBM (secondo modello):** va ri-testato con il **set di feature completo**
   (stakes + luck + midweek + forma + rest_full insieme), possibilmente con
   iperparametri tarati — mai fatto. È il veicolo giusto per gli effetti non-lineari
   (stakes su tutti).
4. **Onestà:** nessuna di queste è ancora un guadagno dimostrato. Sono **ipotesi
   vive** con evidenza direzionale, da validare walk-forward con regola dichiarata —
   non promesse. L'edge contro la chiusura resta improbabile; il valore è portare i
   modelli al loro vero massimo e prepararli ad altre leghe (dove gli iperparametri
   vanno ri-tarati, CLAUDE.md §7).

**Riproducibilità.** `python scripts/_run_audit_diagnostics.py` (6 backtest + D1/D2/D3
+ test economici A/B, 1 run registrato `source=fase34_audit`).

### 📐 Il modello in dettaglio

Un audit, non una nuova matematica: la formula che ne nasce è la **φ(|λ−μ|)**
sviluppata per esteso nella Fase 35 (`φ(λ,μ) = φ0·exp(−κ·|λ−μ|)`, vedi il suo
blocco 📐). Il numero-chiave di questa fase — il **deficit-pareggio −0.044 nelle
partite equilibrate** — è ricalcolabile: è la differenza media `P(pari|modello) −
freq(pari)` sul quartile a |λ−μ| più basso (partite bilanciate), da
`scripts/_run_audit_diagnostics.py`; il test economico post-hoc (aggiungere il
deficit al canale-pareggio) dà **−0.0014, P 77%** (non conclusivo → diventa la
leva strutturale della Fase 35, non un fix immediato). La ricalibrazione
per-classe menzionata come confronto è quella della Fase 10 (`calibration.py`,
pesi w_H/w_D/w_A leave-future-out). Nessuna costante nuova cablata qui: la fase
**apre** la φ35, non la fissa.

---

## Fase 35 — Il pareggio come EQUILIBRIO: φ condizionato a |λ−μ| (il miglior risultato sul pareggio)

**Obiettivo.** Implementare e validare nel modello la leva più promettente
dell'audit (Fase 34, D2): il deficit di pareggio è concentrato nelle partite
**equilibrate** (|λ−μ| piccolo), la dimensione che τ, φ-costante (12b) e ρ-dinamico
(18) avevano tutte mancato (esploravano il *volume* λ+μ, non la *bilancia*).

**Ragionamento / ipotesi.** Il pareggio è strutturalmente un fenomeno di
**equilibrio**: due squadre pari-livello pareggiano più di quanto una Poisson
preveda, *a parità di gol totali attesi*. Serve un boost dei pareggi che dipenda da
|λ−μ| e svanisca con lo squilibrio: `φ(λ,μ) = φ0·exp(−κ·|λ−μ|)`, fittato nella
verosimiglianza dei punteggi (estende l'inflazione diagonale della Fase 12b da
costante a funzione della bilancia).

**Alternative considerate.** (a) φ costante (Fase 12b, già fatto); (b) ρ o φ funzione
del *totale* λ+μ (Fase 18-style, la dimensione sbagliata); (c) φ funzione di |λ−μ|
(scelta). Forma esponenziale `φ0·exp(−κ|λ−μ|)` invece di lineare: garantisce φ≥0
(niente pareggi negativi) e un decadimento morbido con 2 soli parametri.

**Scelta.** `draw_balance=True` (`--draw-balance`), off di default. Fit 2-D di
(φ0, κ) via L-BFGS-B nella stessa verosimiglianza-pareggio della Fase 12b. Guardie:
alternativo a `draw_inflation`, non combinabile con `dynamic_rho` (usano lo stesso
canale). Test unitario aggiunto.

**Risultato** (`scripts/_run_draw_balance.py`; 4 varianti × 6 stagioni walk-forward,
stessi split, bootstrap appaiato; 4 run `source=fase35_draw_balance`):

| approccio | dimensione | 1X2 log-loss | Δ vs base | CI95 | P(migliora) |
|---|---|--:|--:|--:|--:|
| base (solo τ) | — | 0.9797 | — | — | — |
| φ costante (12b) | nessuna (globale) | 0.9793 | −0.0004 | [−0.0018, +0.0010] | 70% |
| ρ dinamico (18) | volume λ+μ | 0.9800 | +0.0003 | [−0.0007, +0.0013] | 27% |
| **φ(\|λ−μ\|) (35)** | **equilibrio** | **0.9790** | **−0.0007** | [−0.0032, +0.0017] | **72%** |

**Calibrazione del pareggio per quartile di |λ−μ|** — P(pareggio):

| quartile \|λ−μ\| | reale | base | φ cost | ρ din | **φ equil** | mercato |
|---|--:|--:|--:|--:|--:|--:|
| equilibrata | 0.332 | 0.287 | 0.300 | 0.290 | **0.334** | 0.296 |
| medio-bassa | 0.288 | 0.276 | 0.288 | 0.278 | 0.295 | 0.282 |
| medio-alta | 0.272 | 0.253 | 0.264 | 0.252 | 0.260 | 0.253 |
| sbilanciata | 0.186 | 0.198 | 0.206 | 0.194 | 0.200 | 0.196 |

**Lezione / cosa ne consegue.**
1. **La diagnosi dell'audit era giusta e il meccanismo funziona come da progetto.**
   φ(|λ−μ|) porta la P(pareggio) delle partite equilibrate da 0.287 a **0.334**,
   contro un reale di **0.332**: calibrazione quasi perfetta dove tutti gli altri
   fallivano. E — fatto raro — su quella dimensione **batte il mercato** (0.296,
   che sotto-prezza i pareggi equilibrati di 3.6 punti): è il **miglior risultato
   sul pareggio dell'intero progetto**.
2. **È la migliore delle quattro varianti anche sul log-loss** (0.9790): quasi il
   doppio del guadagno del φ costante (−0.0007 vs −0.0004) e batte nettamente il ρ
   dinamico sul totale (+0.0003, che ri-conferma la Fase 18). La dimensione
   *equilibrio* è quella giusta.
3. **Ma il log-loss NON è ancora CI-conclusivo** (CI [−0.0032, +0.0017] include lo
   zero, P 72%): come per il φ costante, *quanti* pareggi capitano in una stagione
   resta in parte rumore, e i φ0 fittati variano molto (0.22–0.63). Per la regola
   pre-dichiarata (CI<0) **non entra nella config ufficiale** — resta disponibile
   (`--draw-balance`, off di default), ottimo per **probabilità di pareggio
   calibrate** a uso pratico (migliore del mercato sulle partite equilibrate) e come
   base per il Punto 3 (covariate nel canale-pareggio).
4. Onestà: −0.0007 su log-loss è piccolo e non chiude il gap col mercato sull'1X2
   aggregato; il valore è la calibrazione del pareggio, non un edge.

**Riproducibilità.** `python scripts/_run_draw_balance.py` (4 varianti × 6 stagioni),
oppure `python scripts/backtest.py --draw-balance`.

### 📐 Il modello in dettaglio — la formula e perché φ0≈0.39, κ≈3.6

**La formula** (`_fit_draw_balance` + `_score_matrix` in `dixon_coles.py`):

```
φ(λ, μ) = φ0 · exp( −κ · |λ − μ| )                    φ0 ≥ 0, κ ≥ 0
P_φ(i, j) ∝ M(i, j) · ( 1 + φ(λ,μ) · [i = j] )         (poi rinormalizzata)
```

Il fit di (φ0, κ) massimizza la stessa verosimiglianza-pareggio della Fase 12b, con
φ **per-partita** invece che costante (vedi `_draw_base_arrays`):

```
ℓ(φ0, κ) = Σ_partite  w · [ ln(1 + φ_p·1{pari}) − ln(1 + φ_p·d_match) ]
con  φ_p = φ0·exp(−κ·|λ_p − μ_p|)  e  d_match = P(pari) base DC-corretta per riga
```

**Perché φ0 ≈ 0.39 (il boost a squadre pari-livello).** A |λ−μ|=0, φ=φ0: la
diagonale dei pareggi è moltiplicata per `1+φ0 ≈ 1.39`. Dopo la rinormalizzazione
questo alza la P(pareggio) delle partite equilibrate da 0.287 a ~0.334 (l'aumento
non è lineare in φ0 per via del denominatore Z=1+φ0·d_match): φ0 è fittato,
non ri-derivabile a mano, ma il suo *ruolo* è chiaro — colma il deficit −0.044 del
quartile equilibrato. Varia per stagione (0.22–0.63): è la ragione per cui il
log-loss non è conclusivo (quanto boost serve cambia di anno in anno).

**Perché κ ≈ 3.6 (quanto in fretta svanisce).** κ misura la concentrazione del boost
sull'equilibrio. Con κ=3.6, al |λ−μ| **mediano** (≈0.60, dalla Fase 34) il boost è
già `φ0·exp(−3.6·0.60) = 0.39·0.115 ≈ 0.045` (4.5%), e a |λ−μ|=1.0 è
`0.39·exp(−3.6) ≈ 0.011` (1%). Cioè il boost è **fortemente concentrato** sulle
partite quasi-perfettamente equilibrate (|λ−μ|<0.3), esattamente dove il diagnostico
D2 localizzava il deficit. In 2 stagioni su 6 κ sbatte sul bound superiore (5.0): i
dati vorrebbero una concentrazione ancora più netta → conferma che è un effetto di
**equilibrio stretto**, non un boost diffuso (che il φ costante forniva, peggio).

**Perché la Fase 18 (ρ sul totale λ+μ) falliva e questa no.** Sono la stessa idea
"correzione dipendente dalla partita" ma su variabili diverse: λ+μ (volume) vs
|λ−μ| (equilibrio). Il pareggio non dipende dal *quanti gol* ma dal *quanto sono
vicine le squadre*: due squadre da 1.2 gol ciascuna pareggiano spesso, una da
2.5–0.6 (stesso totale ~3.1) quasi mai. Condizionare sulla variabile giusta è tutta
la differenza tra +0.0003 (Fase 18) e −0.0007 con calibrazione quasi perfetta (Fase 35).

---

## Fase 36 — GBM col set di feature COMPLETO: overfitting, non guadagno (ma lo stakes emerge)

**Obiettivo.** Rispondere al Punto 1 della roadmap post-audit: la Fase 22 aveva
provato il GBM con un set ridotto di covariate. `stakes` (Fase 32, il lead più
forte, non-lineare), `luck`/`ppda`/`deep` (Fase 33) non erano MAI stati messi
insieme nello stesso GBM. La combinazione non-lineare completa (effetti-soglia che
si sommano) produce un guadagno REALE o solo overfitting rispetto al numero di
feature?

**Ragionamento / ipotesi.** Un GBM (HistGradientBoosting, calibrato Platt) predice
1X2 e GG/NG con tre set: `dc` (solo output del DC), `dc+cov_rid` (set Fase 22:
forma, rest_full, valore, assenze, midweek), `dc+cov_full` (+ stakes, luck, ppda,
deep). Nessuna feature selection preventiva. La chiave onesta: misurare **train vs
test** (il gap = overfitting) e il **sottoinsieme mismatch** (dove lo stakes deve
agire), oltre alla feature importance a permutazione.

**Alternative considerate.** Tuning degli iperparametri (profondità/regolarizzazione)
invece dei feature-set: scartato come primo passo — la domanda è "il segnale c'è?",
non "quanto lo spremo"; e la Fase 23 ha già mostrato che il GBM degrada previsioni
near-optimal. Un tuning più aggressivo ridurrebbe l'overfit ma non farebbe battere
il DC (vedi lezione).

**Scelta.** `scripts/_run_gbm_full.py` (walk-forward per stagione, allena su
1819..S−1, calibrato; 1 run `source=gbm_full`). Feature importance a permutazione
(neg-log-loss) sul set completo, stagione 2526.

**Risultato.**

*1X2* (DC di riferimento = 0.9797):

| feature-set | test LL | train LL | overfit (test−train) | Δ vs dc (CI95) | mismatch LL (n=99) |
|---|--:|--:|--:|--:|--:|
| dc | 1.0071 | 0.9133 | +0.094 | — | 1.0115 |
| dc+cov ridotto | 1.0108 | 0.8923 | +0.119 | +0.0036 [−0.0017,+0.0090] | 0.9989 |
| **dc+cov completo** | 1.0088 | 0.8673 | **+0.142** | +0.0016 [−0.0052,+0.0084] | **0.9703** |

full vs ridotto: Δ −0.0020, CI [−0.0070, +0.0031], P(full meglio) 78%.

*GG/NG* (DC = 0.6898, baseline 0.6871): GBM dc 0.6943, ridotto 0.6942, completo
0.6948 — **nessuno batte il DC né la baseline**; full vs ridotto +0.0006 (peggio).

*Feature importance (1X2, 2526, set completo):* dominano gli **output del DC**
(dc_pa +0.0163, dc_ph +0.0158, dc_lam +0.0092, dc_mu +0.0085); tra le covariate
spiccano `home_logval` (valore rosa, +0.0096) e `deep` (dominio territoriale,
+0.004); `home_settled` (stakes) è modesta (+0.0026), `stakes_mismatch` quasi nulla
in aggregato (+0.0001, perché è ~5% delle partite).

**Lezione / cosa ne consegue.**
1. **La combinazione completa è OVERFITTING, non guadagno** (risposta diretta al
   Punto 1). La firma è da manuale: aggiungendo feature il **train** log-loss scende
   (0.9133 → 0.8923 → 0.8673) ma il **test** NON migliora (resta ~1.007–1.011) → il
   gap di overfit CRESCE (+0.094 → +0.142). Il "full vs ridotto" −0.0020 non è
   CI-conclusivo (P 78%). Le feature extra danno capacità che il GBM usa per
   memorizzare il training, non per generalizzare.
2. **Ma lo stakes è reale e LOCALIZZATO.** Sul sottoinsieme **mismatch** (una
   squadra decisa, una in corsa; n=99) il set completo fa **0.9703**, contro 1.0115
   del dc-only e persino meglio del DC (0.9797). È esattamente dove la Fase 32
   prevedeva il segnale: la dilizione su 2280 partite lo nasconde in aggregato, ma
   dove il mismatch esiste il GBM col set completo lo cattura. Conferma indipendente
   del lead stakes.
3. **Nessun GBM batte il DC** su 1X2 (1.007 vs 0.9797) né su GG/NG — ri-conferma il
   tetto informativo (Fasi 21-23): la feature importance mostra che il GBM si appoggia
   quasi tutto agli output del DC, e ogni grado di libertà in più aggiunge rumore.
   `midweek` (già nel set ridotto dalla Fase 22) resta a bassa importanza.
4. **Onestà:** un tuning più forte della regolarizzazione ridurrebbe l'overfit ma
   non colmerebbe il divario di 0.027 dal DC sull'1X2 (il GBM degrada una previsione
   già near-optimal, Fase 23). L'unico valore reale è lo **stakes sul mismatch**, e
   il GBM è il veicolo giusto per esso (Fase 32) — ma serve più campione per la
   conclusività.

**Riproducibilità.** `python scripts/_run_gbm_full.py` (8 backtest DC + GBM
walk-forward, feature importance; serve `scikit-learn`).

### 📐 Il modello in dettaglio — overfitting, importance e dove vive lo stakes

**La firma dell'overfitting (la metrica chiave di questa fase):**

```
overfit(feature-set) = log-loss_TEST − log-loss_TRAIN
dc: 1.0071 − 0.9133 = +0.094      dc+cov_rid: +0.119      dc+cov_full: +0.142
```

Un modello che **generalizza** ha train ≈ test; qui il train scende con le feature
ma il test no → il gap cresce = memorizzazione. Con ~2000–3000 esempi di training e
21 feature, la capacità del GBM (max_depth=3, 200 iterazioni, min_samples_leaf=30)
eccede il segnale disponibile: aggiungere feature riempie quella capacità di rumore.

**Feature importance a permutazione** (perché è onesta): si mescola a caso una
colonna del test e si misura di quanto **peggiora** la neg-log-loss:

```
importanza(feature k) = perdita(X con colonna k permutata) − perdita(X)     (media su 8 ripetizioni)
```

Le più alte sono `dc_pa`/`dc_ph` (le probabilità del DC stesso): il GBM **non
scopre nulla oltre il DC**, lo ricopia. Le covariate che contano un po'
(`home_logval`, `deep`) sono quelle già note come ridondanti (Fase 4c/33) — il GBM
ne estrae un capello in-sample che non generalizza.

**Perché lo stakes vive solo sul mismatch (aritmetica della diluizione).** L'effetto
"squadra decisa che molla" agisce su ~99/2280 = **4.3%** delle partite. Anche un
guadagno forte lì (dc→full sul mismatch: 1.0115→0.9703, −0.041) si diluisce in
aggregato a `0.043 × (−0.041) ≈ −0.0018` — sotto il rumore. È il motivo per cui il
lead è reale ma non muove la metrica complessiva: va valutato **sul sottoinsieme**,
mai sull'aggregato (lezione già di Fase 31/32, qui riconfermata sul GBM completo).

### Fase 36-bis — `midweek_europe` come covariata del DC (dummy congestione)

**Obiettivo (Punto 2b).** Il flag `home/away_midweek_europe` (gara europea/coppa
infrasettimana) esiste nei dati ma non era mai stato una covariata del **sotto-modello
gol** del DC. È un DUMMY di congestione (soglia sì/no), potenzialmente più robusto del
`rest_full` continuo. Aiuta? E spiega varianza che `rest_full` non cattura, o è
ridondante?

**Risultato** (`scripts/_run_midweek_cov.py`; 6 stagioni walk-forward, 4 run
`source=punto2b_midweek`):

| variante | 1X2 log-loss | Δ vs base | CI95 | P(migliora) |
|---|--:|--:|--:|--:|
| base | 0.9797 | — | — | — |
| +midweek | 0.9794 | −0.0003 | [−0.0017, +0.0012] | 65% |
| +rest_full | 0.9794 | −0.0003 | [−0.0013, +0.0007] | 71% |
| +rest_full & midweek | 0.9797 | +0.0000 | [−0.0015, +0.0015] | 48% |

Coefficienti a inizio stagione con ENTRAMBE le covariate:

| stagione | β rest_full | β midweek |
|---|--:|--:|
| 2020-21 | −0.0501 | −0.0214 |
| 2021-22 | −0.0053 | −0.0271 |
| 2022-23 | +0.0257 | −0.0227 |
| 2023-24 | −0.0019 | −0.0141 |
| 2024-25 | +0.0052 | −0.0089 |
| 2025-26 | −0.0159 | −0.0250 |
| **media** | **−0.0071** | **−0.0199** |

**Lezione / cosa ne consegue.**
1. **Da solo, midweek non aiuta** (−0.0003, CI include lo zero), come `rest_full`:
   la congestione è un segnale vero ma debolissimo (coerente con Fase 4c/4e-bis, in
   gran parte già implicito in gol+xG recenti).
2. **Ma l'ipotesi dell'audit è confermata: il dummy è un proxy più PULITO del
   continuo.** `β_midweek` è **negativo in 6 stagioni su 6** (segno atteso:
   congestione → meno gol) e stabile (−0.009…−0.027); `β_rest_full` invece **cambia
   segno** (−0.050…+0.026, instabile). L'effetto-soglia "ha giocato in Europa sì/no"
   cattura la fatica in modo più affidabile del gradiente sui giorni di riposo.
3. **Insieme sono RIDONDANTI**: la coppia dà +0.0000 (peggio di ciascuna da sola) →
   catturano la stessa congestione sottostante, non due segnali distinti. midweek è
   il rappresentante migliore, ma non abbastanza forte da adottarlo.
4. **Rilevanza cross-lega:** in leghe con più congestione da coppe (es. Premier, EFL
   Cup + FA Cup + Europa) questo dummy potrebbe pesare di più → resta disponibile
   (`--covariates midweek`), off di default. È il tipo di iperparametro/feature che
   §7 dice di **ri-valutare per ogni lega**.

**Riproducibilità.** `python scripts/_run_midweek_cov.py`.

**📐 Il modello in dettaglio.** midweek entra come le altre covariate (Fase 4c):
`cov = β·(z_casa − z_ospite)`, con `z` la standardizzazione del dummy 0/1. Il segno
di β si legge sui gol: `β_midweek = −0.020` ⇒ una squadra reduce da un impegno
europeo infrasettimanale ha tasso-gol `× e^{−0.020} ≈ 0.98` (−2%) rispetto a una
riposata. Piccolo ma **coerente in segno** (6/6), a differenza di `rest_full`: la
stabilità del segno — non la dimensione — è ciò che distingue un dummy-soglia
robusto da un gradiente rumoroso. Il test di ridondanza (β entrambi insieme + Δ
combinato +0.0000) mostra che i due misurano lo stesso fenomeno.

---

## Fase 37 — Covariate nel CANALE-PAREGGIO? (Punto 3: diagnostico economico, NEGATIVO)

**Obiettivo (Punto 3).** Dopo la Fase 35 (boost-pareggio condizionato a |λ−μ|),
resta un effetto delle covariate — in particolare `stakes` — sui pareggi
**indipendente** dal volume/equilibrio? L'ipotesi: partite "cruciali" (entrambe in
corsa) → più cautela tattica → più pareggi di quanto λ,μ prevedano.

**Ragionamento / scelta.** Prima di estendere il fit di φ con un coefficiente per la
covariata (chirurgia sul modello), il **diagnostico economico** (principio §1.3): il
**residuo di pareggio** (reale − modello) della variante φ-equilibrio già in cache
mostra un pattern per categoria stakes? Se sì, si costruisce; se è sotto il rumore,
si evita la chirurgia. `scripts/_run_draw_covariate.py` (1 run
`source=punto3_draw_covariate`).

**Risultato.**

| categoria stakes | n | pari reale | modello (Fase 35) | residuo |
|---|--:|--:|--:|--:|
| entrambe in corsa ("cruciali") | 2124 | 0.271 | 0.273 | **−0.0017** |
| mismatch (una decisa/una in corsa) | 99 | 0.202 | 0.265 | −0.0628 |
| entrambe decise | 57 | 0.316 | 0.262 | +0.0539 |

`corr(entrambe_in_corsa, residuo) = +0.0106`; `corr(mismatch, residuo) = −0.0289`;
**soglia-rumore 2·SE = 0.0419** → entrambe **sotto il rumore**.

**Lezione / cosa ne consegue.**
1. **L'ipotesi "cruciali → più pareggi" è FALSA.** Le partite con entrambe in corsa
   hanno residuo **−0.0017 ≈ 0**: il modello le prezza già bene, nessuna cautela
   tattica sistematica non catturata. La Fase 35 (equilibrio) ha già preso il segnale.
2. **L'unico pattern è sul mismatch** (residuo −0.063: il modello *sovra*-prezza i
   pareggi perché la squadra motivata vince e quella scarica molla → meno pari). Ma:
   (a) è lo **stesso** segnale stakes-mismatch già noto (Fase 31/32), che si
   manifesta nei pareggi, non un canale-pareggio nuovo; (b) è su **n=99** e la
   correlazione aggregata (−0.029) è **sotto il rumore**; (c) il veicolo giusto per
   il mismatch è il **GBM**, non un termine lineare del DC (Fase 32: DC −0.0022 vs
   GBM −0.0127; Fase 36: il GBM col set completo lo cattura, mismatch 0.9703).
3. **Il diagnostico economico ha evitato una chirurgia inutile** sul modello: il
   canale-pareggio, dopo la Fase 35, è **saturo** rispetto alle covariate interne.
   `entrambe_decise` (+0.054) è su n=57 e si ribalta nel sottoinsieme equilibrato →
   rumore. **Punto 3 chiuso senza modifica al modello.**

**Riproducibilità.** `python scripts/_run_draw_covariate.py`.

### 📐 Il modello in dettaglio — perché non serve la chirurgia

La chirurgia sarebbe stata estendere `φ(λ,μ) = φ0·exp(−κ|λ−μ|)` (Fase 35) con un
fattore per la covariata, es. `φ(λ,μ,x) = φ0·exp(−κ|λ−μ|)·exp(γ·x)` con `x` =
indicatore di partita cruciale/mismatch e `γ` fittato. Il diagnostico dice che `γ`
sarebbe **statisticamente indistinguibile da 0**: il residuo di pareggio per la
categoria "cruciali" è −0.0017 (il termine `x` non ha nulla da spiegare), e la
correlazione aggregata (|0.011|, |0.029|) è sotto `2/√n = 0.042`. Costruire `γ`
significherebbe fittare rumore su 99 partite (mismatch) — l'esatto errore che la
Fase 34 aveva evitato altrove. Coerente con il principio "testa la versione
economica prima di investire": qui la versione economica (residui, costo zero di
compute) chiude la questione senza toccare `_fit_draw_balance`.

---

## Fase 38 — Denoising cross-stagione del market-implied (Punto 4: motore già maturo)

**Obiettivo (Punto 4).** Il motore market-implied (Fase 24/26) inverte OGNI partita
in **isolamento**: nessun meccanismo che sfrutti l'informazione cross-stagione per
ridurre il rumore o correggere bias sistematici del bookmaker. Due correzioni,
stimate sul passato e applicate al futuro (leave-future-out), sul mercato-vetrina non
prezzato (GG/NG): (1) **power-devig** `p_i ∝ (1/o_i)^{1/η}` (corregge il bias del
margine); (2) **ricalibrazione derivata** Platt sul GG/NG (corregge un bias
sistematico del motore). Più il **trade-off bias/varianza/lag**: calibrazione su
tutto il passato vs pesata sul recente.

**Ragionamento / scelta.** Modulo puro `src/models/market_denoise.py` (power_devig,
fit_power_eta, fit_derived_recal, recency_weights). Validazione
`scripts/_run_market_denoise.py` (usa i backtest in cache, solo inversioni; 1 run
`source=punto4_market_denoise`). Confronto vs raw market-implied (Fase 26), DC-da-gol,
baseline.

**Risultato** (LFO, 5 stagioni; riferimenti: raw 0.6866, DC-da-gol 0.6915,
baseline 0.6928):

| denoiser | GG log-loss | Δ vs raw | CI95 | P(migliora) | parametri |
|---|--:|--:|--:|--:|---|
| power-devig | 0.6863 | −0.0003 | [−0.0021, +0.0015] | 63% | η=0.895 |
| recal Platt (all-history) | 0.6886 | +0.0020 | [−0.0013, +0.0053] | 12% | a=1.06, b=+0.14 |
| recal Platt (recency hl=2) | 0.6887 | +0.0021 | [−0.0011, +0.0054] | 10% | a=1.07, b=+0.13 |
| power + recal | 0.6879 | +0.0013 | [−0.0024, +0.0049] | 24% | η=0.895 |

**Lezione / cosa ne consegue.**
1. **La ricalibrazione derivata PEGGIORA** (+0.0020). Il motivo è istruttivo: il GG/NG
   market-implied è **già ben calibrato** (Platt stima `a ≈ 1.06 ≈ 1`, cioè "nessuna
   temperatura da cambiare"); il `b = +0.14` è un aggiustamento di livello che
   **sovracorregge**. Non c'è bias sistematico da togliere → correggere aggiunge solo
   rumore. È la conferma che il motore (Fase 26) è **non-biased**.
2. **Il power-devig è trascurabile e non conclusivo** (−0.0003, P 63%, CI include lo
   zero). η=0.895 (<1) affila appena i favoriti nell'inversione: direzione coerente,
   effetto sotto il rumore.
3. **Trade-off bias/varianza/lag — documentato:** recency (hl=2) è **identica**
   all'all-history (+0.0021 vs +0.0020) → **non c'è deriva** del bias del bookmaker in
   queste 6 stagioni da inseguire, quindi la calibrazione a minima varianza
   (all-history) è la scelta giusta e la recency aggiunge solo varianza senza
   guadagno di lag. Se in futuro il margine derivasse (nuove leghe, nuovi anni),
   `recency_weights(half_life=...)` è pronto per gestirlo.
4. **Verdetto:** il market-implied non beneficia del denoising cross-stagione — le
   quote di ogni partita contengono già l'informazione, e aggregare tra stagioni non
   riduce varianza in modo utile. Dopo la forma (Fase 27), anche il denoising tocca
   il tetto: il motore è **maturo così com'è**. Il modulo resta disponibile per leghe
   con bookmaker meno efficienti (dove un bias sistematico da correggere potrebbe
   esistere davvero) — §7.

**Riproducibilità.** `python scripts/_run_market_denoise.py`.

### 📐 Il modello in dettaglio — le due correzioni e perché non servono qui

```
power-devig:   p_i ∝ (1/o_i)^{1/η}          η tarato su log-loss 1X2 passata
recal Platt:   p_corr = σ(a·logit(p_raw) + b)   (a,b) su GG/NG passato
recency:       peso_stagione = 2^{−(distanza_stagioni)/half_life}
```

**Perché `a ≈ 1.06` dice "non c'è nulla da correggere".** Il Platt riduce a due gesti:
`a` = temperatura (a<1 raffredda, a>1 affila), `b` = spostamento di livello. Su un
mercato *ben calibrato* il fit ottimo è `(a,b) = (1,0)` (identità). Qui esce `a=1.06`
(quasi 1) e `b=+0.14`: il motore market-implied è già near-identità; il piccolo `b`
che il fit trova sul passato **non generalizza** (il GG/NG medio varia per stagione,
come i pareggi) e out-of-sample fa danno (+0.0020). È lo stesso meccanismo della Fase
6 (temperature) e 12b: correggere una media che oscilla per stagione punisce il
log-loss.

**Perché recency = all-history qui.** `recency_weights` con half-life 2 dà più peso
alle stagioni recenti; se il bias del bookmaker **derivasse**, seguirlo ridurrebbe il
bias a costo di varianza. Il fatto che i due diano lo **stesso** risultato
(+0.0021 vs +0.0020) è la prova empirica che **non c'è deriva**: `a,b` stimati sul
recente ≈ stimati su tutto. Trade-off risolto a favore della minima varianza
(all-history). Il lag non è un problema perché non c'è nulla che si muove.

---

## Fase 39 — Market-implied + φ(|λ−μ|): la sintesi dei due risultati positivi

**Obiettivo.** Combinare i **due** risultati positivi del progetto, mai messi
insieme: i λ,μ **del mercato** (Fase 26, migliori dei nostri) + la struttura-pareggio
**dell'equilibrio** (Fase 35, φ condizionato a |λ−μ|). La Fase 27 aveva ottimizzato la
*forma* del market-implied (ρ, φ **costante**, binomiale negativa) ma **non** aveva
mai provato il φ condizionato all'equilibrio — la dimensione che solo la Fase 35 ha
identificato. Bersaglio: i mercati che il book **non** prezza (GG/NG, risultato
esatto, multigol).

**Ragionamento / scelta.** Nuove funzioni pure nel motore
(`market_implied.balance_phi`, `fit_balance_phi`), con test. Per ogni partita:
inversione 1X2+O/U → (λ,μ) del mercato; (φ0,κ) fittati **leave-future-out** sui λ,μ
del mercato e i pareggi reali passati; applicati come `diag_inflation` alla matrice
della stagione di test. Confronto raw (φ=0, = Fase 26) vs balance-φ, bootstrap
appaiato per-riga.

**Risultato** (`scripts/_run_mi_balance.py`; LFO 5 stagioni, n=1900, 1 run
`source=fase39_mi_balance`; φ0≈0.30, κ≈1.47):

| mercato non prezzato | raw (Fase 26) | + φ(\|λ−μ\|) | Δ | CI95 | P(migliora) |
|---|--:|--:|--:|--:|--:|
| **GG/NG** | 0.6866 | **0.6861** | −0.0006 | [−0.0012, +0.0001] | **96%** |
| risultato esatto | 2.7733 | 2.7721 | −0.0013 | [−0.0042, +0.0017] | 80% |
| multigol | 1.0364 | 1.0363 | −0.0001 | [−0.0003, +0.0001] | 70% |

**Lezione / cosa ne consegue.**
1. **La sintesi funziona: è il miglior GG/NG del progetto** (0.6861), e il guadagno
   sul GG/NG è **quasi conclusivo** (P 96%, CI che sfiora lo zero a +0.0001) — la
   stessa etichetta onesta del prior (Fase 19): "molto probabile, formalmente non
   concluso". La struttura-equilibrio migliora anche i λ,μ *già ottimi* del mercato.
2. **È l'unico margine interno residuo trovato dopo l'audit**, e viene — di nuovo —
   dalla combinazione di **informazione** (mercato) e **struttura giusta**
   (equilibrio), non da un modello nuovo. Piccolo ma coerente su tutti e tre i
   mercati derivati (tutti Δ<0).
3. **Onestà invariata:** non verificabile contro una linea di chiusura di quei
   mercati (assente nei dati); richiede le quote 1X2+O/U alla predizione. Non è un
   edge dimostrato, è la miglior **stima condizionata** per i mercati non prezzati.
   Config del motore GG/NG "specialista" aggiornata: inverti 1X2+O/U → applica
   φ(|λ−μ|) → P(GG).

**Riproducibilità.** `python scripts/_run_mi_balance.py`.

### 📐 Il modello in dettaglio — perché φ0≈0.30 e κ≈1.47 (più bassi del DC)

Stessa formula della Fase 35, ma i λ,μ vengono dal mercato:

```
(λ, μ) = implied_lambda_mu(1X2, O/U)                 # Fase 26
φ(λ,μ) = φ0 · exp(−κ · |λ − μ|)                       # fit LFO sui λ,μ DEL MERCATO
M = score_matrix(λ, μ, ρ=−0.06, diag_inflation=φ)    # poi derive_markets(M)
```

**Perché φ0 ≈ 0.30 (vs 0.39 del DC, Fase 35).** φ0 è il boost dei pareggi a
squadre pari-livello. I λ,μ **del mercato** prezzano già i gol meglio dei nostri
(gap +0.0165 a nostro sfavore sull'1X2), quindi il loro **deficit di pareggio
residuo è più piccolo**: serve **meno** inflazione per colmarlo (0.30 vs 0.39). È una
conferma indiretta che il mercato è più vicino al vero anche sulla massa-pareggio —
la φ ha meno da correggere.

**Perché κ ≈ 1.47 (vs 3.6 del DC).** κ regola quanto in fretta il boost svanisce con
lo squilibrio. Più basso ⇒ boost **meno concentrato**, esteso a un intervallo più
ampio di |λ−μ|. Sui λ,μ del mercato l'ottimo è un boost più *diffuso e leggero*
(φ0 piccolo, κ piccolo); sui nostri λ,μ (più rumorosi) era un boost *forte e
strettissimo* (φ0 grande, κ grande, concentrato solo su |λ−μ|<0.3). Coerente:
correzioni più aggressive dove la stima di base è peggiore, più delicate dove è già
buona. La forma esponenziale a 2 parametri si adatta automaticamente alla qualità
dei λ,μ di partenza.

---

## Fase 40 — ROI PER MERCATO/ESITO: cosa nascondeva il value-betting 1X2 piatto

**Obiettivo.** Domanda-chiave: abbiamo **sottovalutato** qualcosa? Tutte le analisi di
ROI (Fasi 1/14/15) usavano il value-betting 1X2 **indistinto** (qualunque esito con
edge>soglia) → −15%, "non scommettere". Ma questo **lumpa** casa, pari e trasferta.
La Fase 35 ha mostrato che il mercato **sotto-prezza i pareggi delle partite
equilibrate** (0.296 vs reale 0.332): forse l'edge è molto diverso per esito. Scomposto.

**Risultato** (`scripts/_run_market_specific_roi.py`; predizioni Fase 35; quota di
chiusura; 1 run `source=fase40_market_specific_roi`).

*A) Value-betting PER ESITO (edge > 0.03):*

| esito | n bet | ROI | CI95 | P(ROI>0) |
|---|--:|--:|--:|--:|
| casa | 485 | **−19.6%** | [−31.1, −7.6] | 0% |
| pari | 698 | **−2.0%** | [−14.5, +11.1] | 37% |
| trasferta | 572 | −12.9% | [−26.6, +1.1] | 4% |

*B) Strategia PAREGGIO se |λ−μ| < 0.5 (soglia FISSA pre-dichiarata):*

| stagione | 2021 | 2122 | 2223 | 2324 | 2425 | 2526 | **POOLED** |
|---|--:|--:|--:|--:|--:|--:|--:|
| ROI | −0.5% | +12.1% | +4.6% | +16.4% | +3.9% | −8.2% | **+4.7%** |

Pooled +4.7% (n=973), CI95 **[−4.9%, +14.4%]**, P(ROI>0)=83%, **4/6 stagioni positive**.
Gradiente (più equilibrio → più ROI): |<0.8 +2.4%, |<0.6 +2.3%, |<0.4 +5.1%, |<0.25
+4.1%. Riferimento: scommettere TUTTI i pari = −0.4%.

*C) Value-betting O/U 2.5:* Over −6.9%, Under −5.6% (nessun edge).

**Lezione / cosa ne consegue — quello che avevamo sottovalutato.**
1. **Il verdetto "−15%, non scommettere" era il framing SBAGLIATO.** Aggregava un
   disastro (casa −19.6%: i nostri value-bet sulla casa sono i nostri errori, è
   l'adverse-selection della Fase 20 resa in €) con un mercato quasi-efficiente per
   noi (pari −2.0%). La media nasconde la struttura.
2. **Il PAREGGIO nelle partite equilibrate è l'unica strategia a ROI positivo del
   progetto** (+4.7% a quota di CHIUSURA), ed è **principiata**: il mercato
   sotto-prezza i pari equilibrati (Fase 35), noi li prezziamo meglio (0.334 vs reale
   0.332), e questo si traduce in valore atteso. È coerente con la letteratura sul
   "draw bias" dei mercati calcistici (i pareggi sono l'esito meno giocato e più
   mis-prezzato).
3. **MA NON è un edge dimostrato.** CI [−4.9%, +14.4%] **include lo zero** (P 83%),
   varianza altissima (evento ~32%), 2/6 stagioni negative **inclusa la più recente
   (2526 −8.2%)**. Disciplina Fase 17: CI che tocca lo zero = "non concluso". È il
   **lead monetizzabile più promettente mai trovato**, non una licenza di scommettere.
4. **Direzione:** merita **raccolta prospettica** (tracciare stake reali su questa
   sola strategia, con soglia pre-registrata, per 1-2 stagioni) prima di qualsiasi
   conclusione. È l'unico posto dove il mercato mostra una crepa e noi abbiamo lo
   strumento (Fase 35) per vederla.

**Riproducibilità.** `python scripts/_run_market_specific_roi.py`.

### 📐 Il modello in dettaglio — la formula del ROI e perché il pari è diverso

```
ROI(strategia) = media_bet [ 1{esito vinto}·quota − 1 ]        (puntata unitaria)
value bet su esito k:  scommetti se  P_modello(k) − P_mercato(k) > edge
strategia pari-equilibrio:  scommetti il pari se |λ − μ| < 0.5
```

**Perché casa −19.6% e pari −2.0% (la matematica dell'adverse selection).** Un value
bet scatta dove `P_modello > P_mercato`. Sulla **casa**, i nostri eccessi di
probabilità sono proprio i casi in cui sbagliamo (Fase 20: gap ∝ dissenso, r=+0.18):
scommettiamo quando sovrastimiamo la casa → perdiamo (ROI −19.6%, win 34% a quota
media ~2.4 non basta). Sul **pari**, invece, il nostro "eccesso" rispetto al mercato
è spesso *corretto* (il mercato sotto-prezza i pari equilibrati): win 31.9% a quota
media 3.33 dà `0.319×3.33 − 1 = +6.2%` sulle equilibrate. La differenza è **da che
parte del nostro errore sta il mercato**: contro di noi sulla casa (adverse
selection), a nostro favore sul pari equilibrato (draw bias del mercato).

**Perché +4.7% ma non concluso.** Il pareggio ha varianza `p(1−p) ≈ 0.32·0.68 ≈ 0.22`
per bet; su n=973 l'errore standard del win-rate è `√(0.22/973) ≈ 0.015`, che a quota
~3.3 diventa `±0.015×3.3 ≈ ±5%` di ROI per una sola deviazione standard → il CI95
±9.5% osservato è esattamente la varianza attesa da un evento ad alta quota, non un
difetto. Serve più campione (più stagioni), non un modello migliore: il segnale è al
limite del rumore campionario, e la sua conferma è una questione di **dati nuovi**,
non di calcolo.

---

## Fase 41 — Bakeoff per-mercato: un modello cucito su ogni mercato? (specialisti)

**Obiettivo.** Operazionalizzare il principio 8 (portafoglio di specialisti): invece
di un modello unico, valutare OGNI mercato Tier 1 con più modelli e scegliere il
migliore per quel mercato. Studio di fattibilità su ~20 mercati Tier 1 (1X2, O/U
multilinea, GG/NG, doppie chance, total-squadra, clean sheet, vince-a-zero, scarto
≥2, multigol, risultato esatto), walk-forward 6 stagioni.

**Ragionamento / scelta.** Estesa `derive_markets` con i mercati Tier 1 mancanti
(doppia chance, clean sheet, win-to-nil). Bakeoff `scripts/_run_markets_bakeoff.py`:
per ogni mercato, **baseline** (frequenza in-sample) vs **DC gol+xG** (matrice dai
λ,μ del backtest ufficiale) vs **market-implied** (λ,μ invertiti dalle quote
1X2+O/U). Onestà: la matrice del DC è **ricostruita** dai λ,μ salvati con rho fisso
−0.05 (errore max per-partita 0.0306; in aggregato DC 1X2 0.9800 ≈ vero 0.9797 → il
ranking regge). I mercati derivati non hanno quote (come il GG/NG) → confronto vs
baseline; il market-implied li deriva dalle 1X2+O/U.

**Risultato** (1 run `source=fase41_markets_bakeoff`). Modello **migliore** per mercato:

| mercato | baseline | DC | market-impl | migliore (Δ vs DC) |
|---|--:|--:|--:|---|
| 1X2 | 1.0834 | 0.9800 | **0.9642** | market-impl (−0.0159) |
| risultato esatto | 2.8974 | 2.8346 | **2.8037** | market-impl (−0.0309) |
| multigol | 1.0444 | 1.0471 | **1.0333** | market-impl (−0.0137) |
| O/U 2.5 | 0.6892 | 0.6885 | **0.6818** | market-impl (−0.0067) |
| GG/NG | 0.6871 | 0.6901 | **0.6853** | market-impl (−0.0048) |
| clean sheet casa | 0.6058 | 0.5734 | **0.5659** | market-impl (−0.0076) |
| casa +2 | 0.4945 | 0.4402 | **0.4318** | market-impl (−0.0083) |
| … (altri 12) | | | | market-impl |
| pari/dispari | **0.6923** | 0.6930 | 0.6932 | baseline (quasi-casuale) |

**Conteggio: market-implied migliore su 19/20 mercati; DC su 0; baseline su 1.**
I CI del Δ (market-impl − DC) escludono lo zero su quasi tutti.

**Lezione / cosa ne consegue.**
1. **La risposta alla domanda "un modello per ogni mercato?" è sorprendente e più
   semplice: NO, ne basta UNO — il market-implied — per quasi tutti.** I λ,μ del
   mercato battono i nostri (dai gol) su OGNI mercato sui gol; il DC-da-gol non è mai
   il migliore. Il "portafoglio di specialisti" non è 20 modelli bespoke, è **un
   motore (market-implied) + la φ(|λ−μ|) della Fase 35/39 per la famiglia-pareggio**
   (1X2 draw, risultato esatto in diagonale). Cucire un modello diverso per ogni
   mercato sarebbe complessità sprecata: converge tutto sullo stesso vincitore.
2. **Cautele che rendono onesto il risultato:**
   - Sui mercati **prezzati** (1X2, O/U 2.5) la vittoria del market-implied è in parte
     **tautologica** (legge le quote): non è "specialista bravo", è "il mercato è più
     bravo di noi e noi lo leggiamo".
   - Sui mercati **non prezzati** (risultato esatto, total-squadra, clean sheet…) il
     market-implied è il **miglior stimatore disponibile**, ma **non verificabile**
     contro una linea (assente nei dati) e **condizionato** ad avere le quote 1X2+O/U.
   - Il DC-da-gol resta l'unico strumento **quando le quote non ci sono** (predizione
     pura pre-dati): lì è uguale su tutti i mercati (nessun vantaggio bespoke emerso).
3. **La parte NON testata dell'ipotesi:** un modello **bespoke ML per singolo
   mercato** (es. un GBM addestrato solo sul clean-sheet, o sul risultato esatto).
   Qui il bakeoff confronta DC vs market-implied, non un ML dedicato per mercato. Dato
   il verdetto delle Fasi 22/36 (il GBM overfitta e non batte il DC/mercato),
   difficilmente batterebbe il market-implied — ma è il passo per **chiudere del tutto**
   la domanda. Candidato per una fase futura.

**Conseguenza operativa.** Il tool pratico deve usare il **market-implied per tutti i
mercati quando ci sono le quote 1X2+O/U** (con la φ35 sulla famiglia-pareggio), e il
DC come fallback senza quote. Non serve un modello per mercato.

**Riproducibilità.** `python scripts/_run_markets_bakeoff.py`.

### 📐 Il modello in dettaglio — perché lo stesso motore vince ovunque

Ogni mercato Tier 1 è una **somma di celle** della *stessa* matrice `P(i,j)` (vedi
Fase 5): `clean sheet casa = Σ_j P(·,0)`, `casa+2 = Σ_{i−j≥2} P`, `risultato esatto =
P(i,j)`, ecc. Quindi la qualità su OGNI mercato dipende da un'unica cosa: quanto sono
buoni i `(λ, μ)` che generano la matrice. Il bakeoff misura, indirettamente, proprio
questo:

```
log-loss(mercato | modello) = f( qualità di λ,μ del modello )     per ogni mercato
```

e i λ,μ del **mercato** (gap +0.0165 a nostro favore sull'1X2, Fase 26) sono migliori
dei nostri **su tutta la linea** → vincono su tutti i mercati derivati insieme, non
uno per uno. È il motivo per cui "un modello per mercato" collassa a "un motore per i
λ,μ": i mercati non sono problemi indipendenti, sono **proiezioni della stessa
matrice**. L'unica correzione che *non* passa dai λ,μ ma dalla **forma** della matrice
è il boost-pareggio sull'equilibrio (φ(|λ−μ|), Fase 35): per questo è l'unico
"specialista" aggiuntivo che ha senso, e solo sulla famiglia-pareggio.

---

## Fase 42 — Poisson bivariato: la correlazione esplicita (5° modello, non batte la φ35)

**Obiettivo.** Implementare e testare l'unica famiglia di modelli sui punteggi mai
provata: il **Poisson bivariato** (Karlis-Ntzoufras), che modella una
**correlazione esplicita** tra i gol delle due squadre — il candidato naturale per i
mercati che dipendono dalla correlazione (GG/NG, risultato esatto). È il "5° modello"
del panel (DC, DC+φ35, market-implied, GBM, **bivariato**).

**Ragionamento / ipotesi.** `src/models/bivariate_poisson.py`: `X=W1+W3`, `Y=W2+W3`
con `W3~Pois(λ3)` componente comune → `Cov(X,Y)=λ3≥0`. Costruito **preservando i
marginali** (λ, μ) dati (λ1=λ−λ3, λ2=μ−λ3), così λ3 è un parametro di **forma**
confrontabile con il ρ (DC) e la φ (Fase 35). λ3 fittato walk-forward. Nuova regola
metodologica (concordata): il CI resta la guardia per *config/claim*, ma la scelta
del modello si fa su **punto-stima + meccanismo**, non serve CI<0 per *guardare* un
modello.

**Alternative considerate.** Un bivariato con re-fit completo di attacco/difesa da
zero (più invasivo) vs il bivariato come forma sui marginali dati (scelto: pulito e
confrontabile con τ/φ). Limite noto: λ3≥0 può solo aggiungere correlazione
**positiva**, mentre il ρ<0 del DC gestisce i punteggi bassi — strutture diverse.

**Risultato** (`scripts/_run_bivariate.py`; walk-forward 5 stagioni; 1 run
`source=fase42_bivariate`; λ3 medio **DC 0.111, mercato 0.120** → correlazione ~+0.09):

*Marginali del mercato* (i migliori, Fase 41):

| mercato | mkt-ρ (attuale) | mkt-φ35 (Fase 39) | **mkt-biv (λ3)** | Δ biv−ρ (CI95) |
|---|--:|--:|--:|--:|
| GG/NG | 0.6866 | **0.6861** | 0.6863 | −0.0003 [−0.0006, +0.0001] |
| risultato esatto | 2.7733 | **2.7721** | 2.7734 | +0.0000 [−0.0041, +0.0043] |
| **multigol** | **1.0364** | 1.0363 | 1.0390 | **+0.0026 [+0.0002, +0.0051]** |
| pareggio | 0.5784 | **0.5771** | 0.5783 | −0.0001 [−0.0006, +0.0004] |

*Marginali del DC*: GG −0.0004, risultato esatto −0.0002, multigol +0.0012, pareggio
−0.0002 (idem: minuscolo, e i marginali del DC sono comunque peggiori del mercato).

**Lezione / cosa ne consegue.**
1. **Il bivariato trova una correlazione REALE ma piccola** (λ3≈0.11, ~+9%): esiste
   una lieve co-occorrenza dei gol ("partita aperta → segnano entrambe"). Non è zero
   (contro l'attesa più pessimista), ma è debole.
2. **Non batte la φ35 su NESSUN mercato**, nemmeno sul GG/NG (il suo terreno
   naturale): biv −0.0003 vs φ35 −0.0005 sul GG. Sul punto-stima la φ35 vince
   ovunque; per la regola del bakeoff (Fase 41) il bivariato **non si guadagna un
   posto** nel portafoglio.
3. **E PEGGIORA il multigol (+0.0026, CI esclude lo zero)** — ed è il risultato
   tecnicamente più istruttivo (vedi 📐): la correlazione positiva **sovra-disperde
   il totale** dei gol, spostando massa dai totali medi agli estremi. La φ35 sposta
   massa sui pareggi *senza* questo effetto collaterale sui totali.
4. **Verdetto:** il 5° modello è implementato, testato e **onestamente perde**. Ma è
   un risultato pulito: la φ(|λ−μ|) è strutturalmente superiore alla correlazione
   globale per la famiglia-pareggio/GG. Chiude "proviamo il bivariato?" con la nostra
   implementazione. Resta disponibile (`bivariate_poisson`) come mattone/fallback e
   per altre leghe (dove la correlazione potrebbe essere diversa — §7).

**Riproducibilità.** `python scripts/_run_bivariate.py`.

### 📐 Il modello in dettaglio — la formula e perché la φ35 vince

**La PMF congiunta** (convoluzione sul termine comune W3):

```
P(X=x, Y=y) = Σ_{k=0}^{min(x,y)} Pois(k; λ3) · Pois(x−k; λ1) · Pois(y−k; λ2)
con  λ1 = λ − λ3,  λ2 = μ − λ3   (marginali preservati: X~Pois(λ), Y~Pois(μ))
Cov(X,Y) = λ3 ≥ 0,   corr = λ3 / √(λ·μ)
```

**Perché λ3 ≈ 0.11 e non 0.** Il fit massimizza la verosimiglianza dei punteggi; un
λ3 positivo piccolo migliora la probabilità congiunta dove entrambe segnano (o
entrambe no), cioè cattura la "partita aperta/chiusa". Ma corr ~+0.09 è debole → il
guadagno è minuscolo.

**Perché PEGGIORA il multigol (il punto chiave).** Preservare i marginali **non**
preserva la distribuzione del TOTALE `X+Y`: con correlazione positiva,
`Var(X+Y) = Var(X)+Var(Y)+2·λ3` **aumenta** → più massa sui totali estremi (0-1 e
4+), meno sui medi (2-3). Se i totali reali del calcio sono ~Poisson (non
over-dispersi, confermato Fase 27: la binomiale-negativa era stata rigettata), questa
sovra-dispersione è nella direzione sbagliata → il multigol peggiora (+0.0026).

**Perché la φ35 è strutturalmente migliore.** La φ(|λ−μ|) alza la diagonale
(pareggi) *concentrandosi sulle partite equilibrate* e rinormalizza, spostando massa
**tra esiti a parità di dispersione del totale**; non gonfia le code di `X+Y`. Cioè
corregge *dove serve* (il pareggio-equilibrio) senza l'effetto collaterale del
bivariato sui totali. È il motivo per cui, sui gol del calcio, **la struttura giusta
per il pareggio/GG è l'equilibrio |λ−μ|, non la correlazione globale λ3.**

---

## Fase 43 — Spremere la dipendenza: copule flessibili (la φ35 è il tetto)

**Obiettivo.** "Migliorare il Poisson bivariato il più possibile": una batteria di
strutture di dipendenza sui marginali del mercato, per vedere se una qualsiasi batte
la φ35. Il candidato-chiave: la **copula di Frank**, che a differenza del bivariato
(solo correlazione positiva) ammette dipendenza di **qualsiasi segno** e preserva
esattamente i marginali Poisson.

**Ragionamento / scelta.** Modulo `src/models/copula_scores.py` (copula di Frank via
differenze della CDF; fit di θ globale e di θ=a+b·|λ−μ|). Sei varianti walk-forward:
τ (rho) · φ35 · biv (λ3) · frank_g (θ globale) · frank_b (θ condizionato) · frank_b+φ
(copula + inflazione diagonale). Mercati sensibili: GG, risultato esatto, multigol,
pareggio, O/U 2.5.

**Risultato** (`scripts/_run_copula.py`; 1 run `source=fase43_copula`; parametri:
λ3=0.120, **θ_globale=+0.62**, frank_b a=+0.47 b=+0.20):

| mercato | τ | **φ35** | biv | frank_g | frank_b | **frank_b+φ** |
|---|--:|--:|--:|--:|--:|--:|
| GG/NG | 0.6866 | 0.6861 | 0.6863 | 0.6862 | 0.6864 | **0.6860** |
| risultato esatto | 2.7733 | **2.7721** | 2.7734 | 2.7727 | 2.7739 | 2.7726 |
| multigol | 1.0364 | **1.0363** | 1.0390 | 1.0396 | 1.0394 | 1.0394 |
| pareggio | 0.5784 | **0.5771** | 0.5783 | 0.5781 | 0.5784 | **0.5771** |
| O/U 2.5 | 0.6820 | 0.6823 | 0.6820 | 0.6820 | **0.6818** | 0.6822 |

Δ (miglior copula − φ35), bootstrap appaiato: GG **−0.0001** [−0.0004, +0.0003]
P(<φ35)=67%; risultato esatto +0.0005; **multigol +0.0031 [+0.0003, +0.0059]
P(<φ35)=1%**.

**Lezione / cosa ne consegue — la strada più efficiente è… convergere alla φ35.**
1. **Anche con piena libertà di segno, i dati vogliono dipendenza POSITIVA** (θ=+0.62):
   l'ipotesi "il calcio vuole dipendenza negativa" (dalla τ<0 del DC) **non si
   materializza** sui λ,μ del mercato. Sui tassi del mercato la dipendenza residua è
   debole e leggermente positiva — la stessa direzione del bivariato.
2. **La φ (inflazione diagonale) fa TUTTO il lavoro.** La copula da sola (frank_g,
   frank_b) è sempre ≤ φ35; solo aggiungendo la φ (frank_b+φ) si torna al livello
   φ35, battendola sul GG di **−0.0001** — cioè **un pareggio statistico** (CI include
   lo zero, P 67%). Il pezzo-copula non aggiunge nulla oltre la φ.
3. **Ogni dipendenza globale (bivariato o copula) PEGGIORA i totali** (multigol
   +0.003, P<φ35 solo 1%): la sovra-dispersione di X+Y è strutturale a *qualsiasi*
   correlazione, la φ35 (diagonale mirata) ne è immune. È la conferma definitiva del
   perché la φ35 vince.
4. **Verdetto:** dopo bivariato (Fase 42) + 3 copule (Fase 43), la struttura di
   dipendenza è **spremuta**. La φ35 (inflazione diagonale condizionata all'equilibrio)
   è il **tetto della forma**: nessuna struttura la batte in modo significativo. La
   "versione migliore del bivariato" **è** la φ35. L'unico micro-guadagno (frank_b+φ
   sul GG, 0.6860, il miglior GG del progetto) è un pareggio con φ35 → si può usare
   frank_b+φ come specialista GG se si vuole il miglior punto-stima, ma è indifferente.
   Coerente col principio concordato: sul punto-stima frank_b+φ ≈ φ35, e per un
   *claim* servirebbe un CI<0 che non c'è. Chiuso il filone dipendenza-dei-punteggi.

**Riproducibilità.** `python scripts/_run_copula.py`.

### 📐 Il modello in dettaglio — perché la copula non supera la φ35

**La matrice via copula** (differenze della CDF, marginali Poisson esatti):

```
P(X=x, Y=y) = C(Fx(x),Fy(y)) − C(Fx(x−1),Fy(y)) − C(Fx(x),Fy(y−1)) + C(Fx(x−1),Fy(y−1))
Frank:  C(u,v;θ) = −(1/θ)·ln[ 1 + (e^{−θu}−1)(e^{−θv}−1)/(e^{−θ}−1) ]
```

θ>0 = dipendenza positiva, θ<0 = negativa, θ→0 = indipendenza. Il fit sceglie θ ⇒
massima verosimiglianza dei punteggi.

**Perché θ esce POSITIVO (+0.62) e non negativo.** La τ<0 del Dixon-Coles era fittata
sui λ,μ *dei gol* (i nostri): correggeva un difetto dei nostri tassi. Sui λ,μ *del
mercato* (migliori) quel difetto è già assorbito, e la dipendenza residua osservata è
la lieve co-occorrenza "partita aperta → segnano entrambe" (positiva, debole). La
libertà di segno della copula quindi non serve: il segno utile è positivo, come nel
bivariato.

**Perché nemmeno la copula supera la φ35 (il punto strutturale).** Qualsiasi
dipendenza globale (biv λ3 o copula θ) sposta massa **congiunta** e altera la
distribuzione del **totale** X+Y (`Var(X+Y)=Var(X)+Var(Y)+2·Cov` cambia) → penalizza
multigol/O/U. La φ(|λ−μ|) invece **rinormalizza spostando massa TRA esiti** con lo
stesso totale (sposta un 2-0 verso 1-1 solo quando serve, in equilibrio), lasciando i
totali quasi intatti. In una frase: **il calcio non vuole "più correlazione", vuole
"più pareggi dove le squadre sono pari" — e quella è la φ35, non una copula.** Le tre
copule lo confermano da tre angoli diversi.

---

## Fase 44 — Routing di forma per-mercato + decisioni di architettura

**Obiettivo.** Operazionalizzare l'idea "forme/modelli diversi per mercati diversi":
la Fase 43 mostra che la φ35 vince su pareggio/GG ma la **τ pura** vince sui totali
(φ/correlazione li sovra-disperdono). Quindi la forma migliore **non è la stessa per
tutti i mercati**. Si costruisce un **router di forma per-mercato**
(`market_implied.price_markets`): totali/marginali dalla matrice **τ**, esiti/pareggio/
joint dalla matrice con **φ(|λ−μ|)**. Routing **meccanico** (per famiglia di mercato),
non fittato per cella → niente overfitting.

**Risultato** (`scripts/_run_routing.py`; 1 run `source=fase44_routing`; 19 mercati):

```
media log-loss dei 19 mercati:  τ-ovunque 0.7027   φ35-ovunque 0.7026   ROUTER 0.7024
guadagno router vs φ35-ovunque: −0.0002   vs τ-ovunque: −0.0003
```

**Lezione / cosa ne consegue.**
1. **Il router è la scelta corretta e gratuita** (è ≥ del meglio per-mercato per
   costruzione), ma il guadagno è **trascurabile (~0.0002)**: l'ennesima conferma che
   la **forma è spremuta a secco** (dopo τ, φ-costante, ρ-dinamico, bivariato, 3
   copule, e ora il routing). Adottato perché principiato e a costo zero, non per il
   numero. Esposto in `predict.py` (mostra tutti i Tier 1 con la forma instradata).
2. **Decisione: `frank_b+φ` FUORI dal motore** (Fase 43): batte la φ35 sul GG di
   −0.0001, un pareggio; aggiunge complessità e rompe la coerenza per zero. Il modulo
   copula resta per il registro/altre leghe.

**📐 Decisioni di architettura (per il futuro).**
- **Routing di forma**: `price_markets` — τ per {over_*, mg_*, team-totals, clean
  sheet, pari/dispari}; φ35 per {1X2, doppie chance, GG, win-to-nil, scarto, risultato
  esatto}. Split per *famiglia* (robusto), non per singolo mercato (che avrebbe flip
  a livello rumore).
- **Routing per CONTESTO — dove ha valore.** Un'osservazione chiave: **con le quote,
  il market-implied GIÀ prezza il contesto** (motivazione, neopromosse) — è *perché*
  vince 19/20 (Fase 41). Il GBM batteva il *DC* sui mismatch (Fase 36) perché il DC è
  cieco alla motivazione; ma il market-implied non lo è. Quindi il context-routing
  (neopromossa→prior, mismatch→GBM) paga sul **path SENZA quote (DC fallback)**, non
  quando abbiamo le quote. Regola: path market-implied = universale; path DC =
  DC + prior(neopromosse) + φ35, con eventuale aggiustamento-stakes.
- **La frontiera vera è bloccata dai DATI, non dal modello:** i **marginali λ,μ**
  migliorerebbero con *più linee di mercato* (altre O/U, handicap asiatico — Fase 27),
  e l'**in-play** è l'avversario più morbido — ma nessuno dei due è nei dati (solo
  O/U 2.5, niente minuto-per-minuto). Sono progetti di **raccolta dati**, non backtest.

**Riproducibilità.** `python scripts/_run_routing.py`; tool: `python scripts/predict.py
Roma Fiorentina --odds 1.50 4.10 6.00 1.87 1.82`.

### 📐 Il modello in dettaglio — le formule dell'audit e delle leve proposte

**La ricalibrazione condizionata usata nei test economici** (riuso di
`apply_class_recalibration`, Fase 10), applicata a un **sottoinsieme** S:

```
per p ∈ S:   q_i(p) ∝ w_i · P_i(p)              w = (w_H, w_D, w_A) appresi su S PASSATO
per p ∉ S:   q(p) = P(p)  invariato
```

con `w` fittato leave-future-out (solo stagioni < S) minimizzando la log-loss su S.
- *Finale (D1):* S = {giornate ≥ 35}. `w_casa ≈ 0.85` appreso (abbassa la casa) →
  Δ log-loss **+0.0021** (peggiora): la correzione media non regge la varianza
  annuale del crollo casa. **Morta.**
- *Equilibrio (D2):* S = {|λ−μ| < mediana}. `w_pari ≈ 1.08` (alza i pari) → Δ
  **−0.0014**, P 77%: **la più promettente**, ma CI non esclude lo zero.

**Perché la Fase 18 ha mancato il bersaglio (il punto tecnico centrale).** Il rho
dinamico era `ρ_match = ρ + ρ_slope·(λ+μ − centro)`: fa dipendere la correzione dal
**volume** di gol atteso. Ma il pareggio è un evento di **equilibrio**, non di volume:
due squadre con λ=μ=1.2 (equilibrate, pochi gol) pareggiano spesso; una con λ=2.5,
μ=0.6 (stessi ~3 gol totali, ma sbilanciata) quasi mai. La variabile giusta è la
**differenza**, non la somma:

```
Fase 18 (mancata):   ρ_match = ρ + ρ_slope · (λ + μ − centro)      # volume  → nulla
Fase 35 (proposta):  boost pareggio = f( |λ − μ| ),  f decrescente # equilibrio
```

Forma concreta candidata per la Fase 35 — **φ condizionato alla bilancia**, esteso
dall'inflazione diagonale (Fase 12b) da costante a funzione di |λ−μ|:

```
φ(λ, μ) = φ0 · exp( −κ · |λ − μ| )          # più equilibrio (|λ−μ|→0) → più boost pari
P_φ(i, j) ∝ M(i, j) · ( 1 + φ(λ,μ) · [i = j] )
```

con `φ0 ≥ 0` e `κ ≥ 0` fittati nella verosimiglianza dei punteggi (2 parametri,
regola CI<0 pre-dichiarata). φ0>0, κ>0 ⇒ inflaziona i pareggi **solo dove i tassi
sono vicini**, esattamente dove il diagnostico D2 mostra il deficit (−0.044). A
differenza del φ costante (Fase 12b, −0.0004) o del ρ sul totale (Fase 18, +0.0003),
questa forma condiziona sulla variabile che i dati indicano.

**Perché il vantaggio-casa finale NON è la variabile giusta per il log-loss.** Il
bias medio esiste (+0.051), ma il log-loss dipende dalla predizione **per-partita**:
`−ln P(esito)`. Abbassare P(casa) di un fattore fisso su TUTTE le finali aiuta le
partite dove vince la trasferta e punisce quelle (ancora tante) dove vince la casa;
poiché *quali* finali ribaltano è imprevedibile (varianza annuale), i due effetti si
annullano — la stessa matematica del "quanti pareggi capitano è rumore" (Fase 12b).
Utile solo per rendere le probabilità *medie* più oneste (uso pratico), non per il
punteggio.

---

## Prossimo passo — il modello e' al tetto REALE dei dati attuali

Sette esperimenti convergenti (Fasi 6-13) + l'audit di Fase 15 + il test della
linea di apertura (Fase 14) + l'**encompassing** (Fase 16: α*=0, il mercato
ingloba il modello) + il **rho dinamico** (Fase 18: anche l'ultima via
strutturale sul pareggio e' rumore) + l'**anatomia dei residui** (Fase 20: R² a
livello rumore su 11 covariate, e i disaccordi del modello sono i suoi errori):
il gap residuo col mercato (+0.0165 vs chiusura, +0.0146 vs apertura, quasi
tutto nel pareggio) non e' cattiva modellazione ne' errore di calcolo, ma
**informazione che il mercato ha e noi no** — ce l'ha gia' il venerdi' (CLV
negativo) e il modello non aggiunge nulla nemmeno in blend. Il bivio:
1. **Dati davvero nuovi** (formazioni ufficiali pre-partita; oppure la linea di
   apertura VERA di domenica/lunedi', che richiede raccolta prospettica di quote);
2. **Uso pratico** del modello attuale (comando di predizione);
3. **Mercati strutturalmente meno efficienti** (leghe minori, exchange lenti):
   stessa infrastruttura, avversario diverso.

**Aggiornamento dopo l'audit (Fase 34).** Il quadro "tetto informativo in aggregato"
regge, ma l'audit critico ha trovato **una crepa strutturale non sfruttata**: il
deficit di pareggio è concentrato nelle partite **equilibrate** (|λ−μ| piccolo), una
dimensione che nessuna delle tre vie sul pareggio (τ, φ costante, ρ sul totale λ+μ)
aveva mai toccato.

**Roadmap post-audit ESEGUITA (Fasi 35-38 + Punto 6).**
- **Fase 35 (φ condizionato a |λ−μ|):** la crepa era reale. È il **miglior risultato
  sul pareggio del progetto** — calibrazione dei pari equilibrati quasi perfetta
  (0.287→0.334 vs reale 0.332), **batte il mercato** su quella dimensione, 1X2 0.9790
  (best di 4 varianti). Log-loss non ancora CI-conclusivo (varianza stagionale) → off
  di default, ottimo per calibrazione pratica. La dimensione *equilibrio* era quella
  giusta (la Fase 18 sul *volume* falliva).
- **Fase 36 (GBM set completo):** la combinazione non-lineare completa è
  **overfitting** in aggregato (train scende, test no), nessun GBM batte il DC; ma lo
  **stakes** è reale e localizzato sul mismatch (full 0.9703 vs DC 0.9797, n=99) →
  conferma Fase 32, e il GBM è il suo veicolo.
- **Fase 36-bis (midweek DC):** il dummy è un proxy di congestione più pulito del
  continuo `rest_full` (β stabile 6/6 vs segno che cambia), ma troppo debole; utile
  cross-lega.
- **Fase 37 (covariate nel canale-pareggio):** diagnostico economico NEGATIVO —
  "cruciali → più pari" falso, canale-pareggio saturo dopo la Fase 35. Nessuna
  chirurgia.
- **Fase 38 (denoising market-implied):** il motore è già non-biased (la
  ricalibrazione peggiora); nessuna deriva del margine → recency ≡ all-history.
  Motore maturo.
- **Punto 6 (architettura):** iperparametri per-lega centralizzati in
  `src/config.py` (`LEAGUE_CONFIGS`), da cui `backtest.py` legge i default; le
  formule restano generali. Aggiungere una lega ora è configurazione, non codice.

**Sintesi onesta.** La roadmap ha prodotto **un risultato di sostanza** (Fase 35: il
pareggio come equilibrio, che batte il mercato in calibrazione sulle partite pari) e
**quattro conferme/chiusure oneste** (GBM overfit ma stakes localizzato; midweek
ridondante; canale-pareggio saturo; market-implied maturo). Nessuna sposta il gap
1X2 aggregato col mercato in modo conclusivo, ma tutte affinano i modelli e li
preparano ad altre leghe. Le ipotesi vive restano vive con etichetta onesta; le morte
sono documentate col *perché*.

Nota di realismo invariata: battere le quote di chiusura resta difficilissimo;
il value betting simulato perde il **15.7%** — piu' di quanto credevamo prima
dell'audit. **Non scommettere soldi veri con questo modello.**

---

## Fase 45 — Router "stakes-aware" sul path senza quote (chiude il lead della Fase 32)

**Obiettivo.** Operazionalizzare l'ultima leva predittiva interna. La Fase 44 aveva
deciso: sul path DC (senza quote) il predittore e' `DC + prior + φ35`, "con eventuale
aggiustamento-stakes". Qui si COSTRUISCE quell'aggiustamento e lo si mette alla prova.

**Ragionamento / ipotesi.** Fasi 31/32: quando UNA squadra e' *decisa* (niente in
palio) e l'altra e' *in corsa* — le partite **mismatch** — il DC usa la forza
stagionale ed e' cieco alla motivazione, e perde piu' del mercato (gap +0.057). La
Fase 32 aveva trovato che il **GBM** cattura il segnale ~6x meglio del DC. Ipotesi:
un router che sulle sole mismatch sostituisce la previsione DC con quella GBM-stakes
chiude parte del gap.

**Alternative.** (a) covariata `stakes` dentro il DC (Fase 32: Δ mismatch −0.0022,
non conclusivo); (b) router **hard** (DC ovunque, GBM-stakes sul mismatch); (c) router
**soft** (sul mismatch fonde DC e GBM-stakes 50/50, meno aggressivo). Testati (b) e (c),
che sfruttano il veicolo migliore (GBM) invece della covariata debole.

**Scelta.** Router meccanico per contesto: la maschera mismatch =
`home_settled + away_settled == 1` (dalla classifica, `loader.add_stakes`), il GBM e'
calibrato (Platt) e allenato walk-forward sulle stagioni passate della cache.

**Risultato** (`scripts/_run_stakes_routing.py`; 1 run `source=fase45_stakes_routing`;
1900 partite, di cui **84 mismatch = 4.4%**):

```
                     OVERALL                          SOLO MISMATCH (n=84)
                  ll     Δ vs DC   P(aiuta)         ll     Δ vs DC   P(aiuta)   gap-mkt
DC (attuale)    0.9850     —          —           0.9943     —          —        +0.0549
GBM-base        1.0146   +0.0297     0%           1.0236   +0.0293     14%       +0.0842
GBM-stakes      1.0138   +0.0288     0%           1.0087   +0.0145     31%       +0.0693
ROUTER hard     0.9856   +0.0006     31%          1.0087   +0.0145     31%       +0.0693
ROUTER soft     0.9849   −0.0001     53%          0.9924   −0.0018     53%       +0.0531
(mercato: overall 0.9692, mismatch 0.9394; P(aiuta) = P(Δ<0) bootstrap)
```

**Lezione / cosa ne consegue.**
1. **Il gap sulle mismatch e' REALE e grande** (DC +0.0549 vs mercato, riproduce il
   +0.057 della Fase 31 su dati e definizione indipendenti). Il segnale-motivazione
   esiste.
2. **Ma non e' sfruttabile con i modelli che abbiamo.** La GBM-stakes, in *assoluto*,
   e' PEGGIORE del DC anche sulle mismatch (1.0087 vs 0.9943). Il "6x meglio" della
   Fase 32 era relativo alla **GBM-base** (un baseline gia' scarso): battere se stessa
   non basta a battere il DC. Instradare DC→GBM-stakes sul mismatch **peggiora**
   (+0.0145); il router soft non fa danni ma e' **dead-neutral** (−0.0018, CI
   [−0.0342,+0.0277], P(aiuta) 53%).
3. **Questo CHIUDE l'ultimo lead predittivo interno.** Il gap-motivazione e'
   informazione che il mercato prezza e noi non abbiamo: non un errore di
   modellazione che un router puo' correggere. Coerente con Fase 16 (α*≈0), Fase 20
   (adverse selection) e Fase 22 (tetto informativo, non architetturale).

**📐 Il modello in dettaglio — il router e perche' il GBM non basta.**

Router (per la sola classe 1X2, dove la motivazione morde di piu'):

```
mism_i = 1[ home_settled_i + away_settled_i == 1 ]          # una decisa, una in corsa
ROUTER hard:  p_i = p^DC_i                     se mism_i = 0
              p_i = p^GBM-stakes_i             se mism_i = 1
ROUTER soft:  p_i = p^DC_i                     se mism_i = 0
              p_i = 0.5·p^DC_i + 0.5·p^GBM-stakes_i   se mism_i = 1
```

verificato riga per riga contro `_run_stakes_routing.py` (`route[mism] = gbm_st[mism]`;
`soft[mism] = 0.5*dc[mism] + 0.5*gbm_st[mism]`). Il GBM-stakes usa le 17 feature del
DC-block (λ,μ, λ·μ, λ+μ, le 5 prob DC, forma/riposo/valore/assenze) **piu'**
`home_settled, away_settled, settled_diff`; calibrato con `CalibratedClassifierCV`
(sigmoid, cv=3), `HistGradientBoostingClassifier(max_iter=200, max_depth=3, lr=0.05,
l2=1.0, min_samples_leaf=30)`.

**Perche' il numero cade cosi'.** Il router hard eredita la log-loss del GBM-stakes
*sulle mismatch* (1.0087) perche' li' li copia; e 1.0087 > 0.9943 (DC). Il GBM in
assoluto e' peggiore perche' e' allenato su poche stagioni (cache, walk-forward) e le
sue feature pre-partita sono quelle gia' spremute (Fase 22: aggiungere covariate al
GBM peggiora). L'unica variabile nuova, lo `stakes`, sposta il GBM di −0.0149 sulle
mismatch (1.0236→1.0087) — reale ma insufficiente a colmare i +0.029 di svantaggio
di partenza vs DC. Il router soft e' ≈ DC perche' con appena 84 partite su 1900 la
correzione 50/50 su quel 4.4% e' invisibile nell'overall.

**Riproducibilità.** `python scripts/_run_stakes_routing.py`.

---

## Fase 46 — Ensemble dei predittori standalone (DC + bivariato + GBM), senza quote

**Obiettivo.** Rispondere all'ultima domanda combinatoria: sul path SENZA quote,
**mescolare** i tre predittori standalone (DC, Poisson bivariato, GBM) batte il
migliore singolo? Le Fasi 16/23 lo escludono *contro il mercato*, ma la combinazione
INTRA-standalone (senza quote) non era mai stata testata a fondo.

**Ragionamento / ipotesi.** Un ensemble aiuta quando i modelli sono **diversi** e
sbagliano in modo scorrelato. Qui pero' DC e bivariato sono quasi lo stesso modello
(la Fase 42 ha trovato λ3≈0.11, correlazione minuscola → matrici quasi identiche), e
il GBM — l'unica vista davvero diversa — da solo **perde** (Fase 22). Ipotesi onesta:
al piu' una piccola riduzione di varianza sui totali, nessun edge.

**Alternative (metodi di combinazione).** (a) media aritmetica delle probabilita';
(b) log-linear pool (media geometrica, rinormalizzata); (c) media DC+GBM (i due modelli
piu' diversi, scartando il bivariato ridondante). Tutte su 1X2 (3-classi), Over 2.5,
GG/NG, walk-forward, con CI bootstrap appaiato **ensemble − miglior singolo**.

**Risultato** (`scripts/_run_ensemble_standalone.py`; 1 run `source=fase46_ensemble`;
1900 partite):

```
mercato        DC       biv      GBM    | miglior singolo | mean      logpool    dc_gbm
1X2 (3cl)    0.9850   0.9847   1.0146   |     biv         | +0.0033   +0.0027   +0.0080
Over 2.5     0.6907   0.6901   0.6982   |     biv         | −0.0006   −0.0008   +0.0005
GG/NG        0.6915   0.6912   0.6978   |     biv         | −0.0008   −0.0008   −0.0001
(Δ vs miglior singolo; CI95: mean/logpool su O2.5 e GG ~[−0.003,+0.002], includono 0)
```

**Lezione / cosa ne consegue.**
1. **Nessun ensemble batte il migliore singolo.** Sull'1X2 mescolare **peggiora**
   (il GBM a 1.0146 zavorra la media; dc_gbm +0.0080 con CI<0 escluso al contrario,
   cioe' significativamente peggio). Su Over/GG l'ensemble e' **probabilmente utile di
   un filo** (mean/logpool −0.0006…−0.0008, P(aiuta) 66–77%) ma il CI include lo zero
   → **non concluso**: guadagno cosi' piccolo che non giustifica di rompere la
   coerenza usando due motori diversi per mercati diversi.
2. **Il motivo e' strutturale**, non di tuning: DC≈bivariato (nessuna diversita' da
   sfruttare), e il modello diverso (GBM) e' peggiore, quindi pesarlo *danneggia*
   dove conta (1X2). L'ensemble aiuta solo se combini modelli buoni E scorrelati:
   qui manca la seconda condizione tra DC/biv e la prima per il GBM.
3. Chiude la leva "ensemble standalone": conferma a livello intra-modello la lezione
   delle Fasi 22/23 (il tetto e' informativo). Il bivariato resta il miglior singolo
   standalone per un soffio (≈ DC, differenza 0.0003 = rumore).

**📐 Il modello in dettaglio — le tre combinazioni.**

Per un mercato con prob dei tre modelli `a` (DC), `b` (biv), `c` (GBM):

```
media:        p = (a + b + c) / 3
log-pool:     p = exp( (ln a + ln b + ln c) / 3 )          # media geometrica
DC+GBM:       p = (a + c) / 2
(per l'1X2, ogni p e' poi rinormalizzato a somma 1 sulle 3 classi)
```

verificato contro `_combine()` in `_run_ensemble_standalone.py`. La media geometrica
(log-pool) e' piu' conservativa della aritmetica: penalizza le prob discordi (se un
modello dice 0.1 e un altro 0.5, la geometrica sta piu' in basso), motivo per cui su
1X2 fa un filo meno danni della media (+0.0027 vs +0.0033) ma resta peggiore del
singolo. I marginali dei modelli: DC = `m_home/m_draw/m_away`, `m_over`, `m_btts` dalla
cache (matrice τ, rho −0.05); bivariato = `derive_markets(bp_matrix(λ,μ,λ3))` con λ3
fittato walk-forward (0.111 medio); GBM = tre classificatori calibrati (1X2 a 3 classi,
Over 2.5 e GG/NG binari) sulle 17 feature del DC-block.

**Perche' i numeri.** Il peso 1/3 al GBM sull'1X2 costa: il GBM e' +0.0296 peggio del
DC, quindi 1/3 di quel divario (≈ +0.010) ricade sulla media, coerente col +0.0033
osservato (attenuato dalla scorrelazione parziale degli errori). Su Over/GG il GBM e'
piu' vicino (+0.007), e la scorrelazione dei suoi errori con quelli DC/biv quasi
pareggia il costo → Δ ≈ 0. Nessuna magia: e' aritmetica di bias e varianza.

**Riproducibilità.** `python scripts/_run_ensemble_standalone.py`.

---

## Fase 47 — Tracer-bullet dinamico: vantaggio-casa tempo-variante (γ per fascia)

**Obiettivo.** Testare l'unica ARCHITETTURA mai provata — un modello *dinamico* in cui
i parametri evolvono dentro la stagione invece di essere costanti — nella sua versione
piu' economica (metodo: "testa la versione economica prima di investire"). Bersaglio
concreto: la Fase 30 aveva trovato che il **vantaggio-casa crolla nelle ultime giornate**
(casa 40%→36%, trasferta 31%→38% nelle 35-38); il nostro DC usa un γ **costante** e
quel crollo lo ignora. Se un γ per fascia migliora out-of-sample → si costruisce lo
state-space pieno; se no → si chiude anche l'ultima architettura.

**Ragionamento / ipotesi.** γ entra solo nel tasso di casa: λ = exp(att_h + dif_a + γ).
Un γ tempo-variante = scalare λ per exp(δ_fascia), con δ stimato sulle stagioni PASSATE
(leave-future-out). Due varianti: **V1** = solo λ (il "vantaggio-casa t" letterale);
**V2** = anche μ (μ·exp(ε)), per catturare l'eventuale movimento del tasso ospite.

**Risultato** (`scripts/_run_dynamic_gamma.py`; 1 run `source=fase47_dynamic_gamma`;
1900 partite, finale 35-38 = 202). δ,ε medi walk-forward per fascia:

```
fascia    δ_casa (×)         ε_ospite (×)
early    −0.0228 (×0.977)   +0.0010 (×1.001)
tense    −0.0093 (×0.991)   +0.0009 (×1.001)
late     +0.0188 (×1.019)   +0.1383 (×1.148)   ← nel finale l'OSPITE segna +14.8%
```

Log-loss walk-forward (Δ vs γ costante; P(aiuta)=P(Δ<0) bootstrap):

```
                OVERALL (n=1900)                     FINALE 35-38 (n=202)
mercato   base    V1  Δ / P        V2  Δ / P     base    V1  Δ / P         V2  Δ / P
1X2      0.9852  +0.0009 (P 4%)  −0.0001 (P54%)  1.0292  +0.0037 (P 1%)  −0.0033 (P70%)
Over2.5  0.6907  +0.0001 (P41%)  +0.0009 (P22%)  0.6931  +0.0009 (P28%)  −0.0022 (P62%)
GG/NG    0.6916  −0.0003 (P80%)  −0.0003 (P66%)  0.6930  −0.0013 (P91%)  −0.0075 (P91%)
(nessun CI del finale esclude lo zero: n=202, alta varianza → probabile, non provato)
```

**Lezione / cosa ne consegue.**
1. **Il pattern Fase 30 e' confermato OUT-OF-SAMPLE, ma il meccanismo e' un altro.** Nel
   finale il vantaggio-casa cala **non perche' la casa segni meno** (δ_late +1.9%,
   praticamente invariato) **ma perche' l'OSPITE segna il 14.8% in piu'** (ε_late ×1.148).
   Le partite di fine stagione si "aprono": chi rincorre spinge, e i gol ospite salgono.
2. **Percio' il "γ tempo-variante" (V1) e' la parametrizzazione SBAGLIATA.** Aggiusta λ e
   nel finale lo alza pure (δ_late>0), rendendo la casa *piu'* favorita proprio quando il
   suo edge crolla → 1X2 **peggiora** (overall P 4%, finale P 1%). La leva giusta e' μ,
   che V1 non tocca.
3. **La versione corretta (V2, ricalibra ENTRAMBI i tassi per fascia) punta nel verso
   giusto sul finale** su tutti e tre i mercati (1X2 −0.0033 P 70%, Over −0.0022 P 62%,
   **GG/NG −0.0075 P 91%**), con la GG/NG la piu' netta — e la GG/NG e' il mercato NON
   prezzato, la priorita' del principio 8. Ma **nessun CI del finale esclude lo zero**
   (202 partite, alta varianza): **probabile, non provato**, disciplina multiple-testing.
4. **Esito del tracer: REDIRECT, non null.** Non "γ dinamico" ma **inflazione dei gol
   ospite di fine stagione**. E' il PRIMO segnale temporale intra-stagione che muove la
   log-loss nel verso giusto e per di piu' sul mercato che ci interessa. Candidato reale
   per lo state-space pieno — ma il campione finale e' sottile: prima di investire, va
   irrobustito su piu' stagioni (finestra 8, come Fasi 19/31).

**📐 Il modello in dettaglio — le formule del γ tempo-variante e perche' i numeri.**

γ entra solo in λ; renderlo per-fascia = fattore moltiplicativo su λ:

```
V1 (γ dinamico):  λ'_i = λ_i · exp(δ_{b(i)}),   μ'_i = μ_i
V2 (rical. 2 tassi): λ'_i = λ_i · exp(δ_{b(i)}), μ'_i = μ_i · exp(ε_{b(i)})
```

con b(i) ∈ {early(1-31), tense(32-34), late(35-38)} (fasce Fase 30; giornata derivata dal
conteggio partite-per-squadra nella stagione). δ, ε sono la **MLE Poisson closed-form** del
fattore comune, sulle partite passate della fascia:

```
per y_i ~ Poisson(λ_i·e^δ):  ∂/∂δ Σ[y_i(lnλ_i+δ) − λ_i e^δ] = Σy_i − e^δ Σλ_i = 0
⇒  e^δ = Σ gol_casa / Σ λ        (analogo:  e^ε = Σ gol_ospite / Σ μ)
```

verificato riga per riga contro `_fit_deltas()`. **Ragionamento numerico.** ε_late =
ln(Σ gol_ospite_late / Σ μ_late) = ln(1.148) = +0.1383: nelle giornate 35-38 delle stagioni
passate gli ospiti hanno segnato il **14.8% in piu'** di quanto μ prevedeva — l'effetto e'
robusto (media walk-forward su 5 fit). δ_late = +0.019 (casa ≈ come previsto). Fuori dal
finale δ e' leggermente negativo (−0.023 early) perche' i fattori per-fascia devono mediare
a ~0 sulla stagione (il modello e' calibrato nel complesso): le fasce ridistribuiscono, e
la coda di stagione e' dove la ridistribuzione morde. **Perche' la GG/NG guadagna di piu':**
la BTTS e' massimamente sensibile ad alzare il tasso *piu' basso* (di norma μ, l'ospite):
portare μ×1.148 sposta molte partite da "ospite non segna" a "segnano entrambe", esattamente
dove il modello statico sbagliava nel finale.

**Riproducibilità.** `python scripts/_run_dynamic_gamma.py`.

---

## Fase 48 — Modello dinamico a profilo stagionale liscio, su 8 stagioni (chiude l'architettura)

**Obiettivo.** Fare le DUE cose insieme chieste dopo il redirect della Fase 47:
**(1) robustezza** — validare il segnale (inflazione-gol-ospite di fine stagione) su
**8 stagioni** (1819-2526, come Fasi 19/31), non piu' 6; **(2) modello pieno** — sostituire
i 3 bucket grezzi con un vero modello *dinamico* a **profilo stagionale liscio**: i
moltiplicatori dei tassi λ,μ come funzione continua della giornata.

**Ragionamento / scelta dell'architettura.** Il "dinamico" corretto qui NON e' un Kalman
(random-walk delle forze): le forze sono stabili (Fasi 2b/13/25) e l'effetto e' di **fase
stagionale deterministica** (si ripete ogni anno). Quindi si modella un **profilo** liscio
r(md) = exp(c0 + c1·s + c2·tail), con s = (md−19.5)/18.5 ∈[−1,1] (trend globale) e
tail = max(0,md−31)/7 (salita di coda), stimato per casa e ospite via regressione di
Poisson walk-forward. E' la generalizzazione liscia dei bucket della Fase 47.

**Risultato** (`scripts/_run_seasonal_profile.py`; 1 run `source=fase48_seasonal_profile`;
2660 partite, finale 35-38 = 283; profilo confrontato con base e con V2-bucket):

```
moltiplicatore OSPITE alla 38a (profilo liscio, media walk-forward): ×1.072
   (Fase 47, bucket-late su 6 stagioni: ×1.148 → l'effetto si SGONFIA con piu' dati)

              OVERALL (n=2660)                          FINALE 35-38 (n=283)
mercato  base   bucket Δ/P        smooth Δ/P        base   bucket Δ/P         smooth Δ/P
1X2     0.9803 +0.0002(P39%)  +0.0010(P 7%)      1.0058 +0.0001(P48%)  +0.0052(P10%)
Over2.5 0.6867 +0.0018(P 8%)  +0.0015(P 9%)      0.6941 +0.0017(P41%)  +0.0019(P38%)
GG/NG   0.6888 −0.0009(P84%)  −0.0012(P93%)      0.6888 −0.0062(P89%)  −0.0059(P92%)
(P=P(Δ<0) bootstrap; NESSUN CI del finale esclude lo zero: 283 partite ad alta varianza)
```

**Lezione / cosa ne consegue — l'architettura dinamica si CHIUDE.**
1. **Il segnale si sgonfia con piu' stagioni.** Il boost-ospite di fine stagione passa da
   ×1.148 (6 st.) a ×1.072 (8 st.): regressione verso la media, il tracer a 6 stagioni lo
   sovrastimava. Esattamente perche' il metodo impone di validare su piu' stagioni (§1.7).
2. **Sopravvive UN solo mercato: la GG/NG.** Overall −0.0009…−0.0012 (P 84-93%) e finale
   −0.0059…−0.0062 (P 89-92%), coerente su 8 stagioni. Ma **nessun CI esclude lo zero**:
   e' un segnale **~90% probabile, non provato** — stesso tier del lead market-implied sul
   GG/NG (Fase 24) e del pareggio-in-equilibrio (Fase 40). Su 1X2 e Over la correzione e'
   neutra o leggermente dannosa.
3. **Il modello "pieno" liscio NON batte i bucket grezzi.** Pari sulla GG/NG, PEGGIO
   sull'1X2 (finale smooth +0.0052, P 10%): il trend-globale `s` inietta aggiustamento
   anche fuori dal finale, dove non serve. Piu' machinery, zero guadagno. Verdetto: la
   forma dinamica non aggiunge nulla sopra il DC statico, se non un ritocco marginale e
   non provato sul GG/NG.
4. **Conclusione sull'ULTIMA architettura.** Abbiamo testato tutte le famiglie
   (5 sui punteggi, il GBM diretto, e ora il dinamico a profilo). Nessuna batte lo statico
   in modo conclusivo. Il tetto e' confermato **informativo, non architetturale** (Fase 22),
   ora anche contro il tempo: dentro la stagione non c'e' struttura sfruttabile oltre un
   nudge-GG/NG di fine stagione (~90%, off di default per disciplina CI). Per un edge reale
   serve **informazione nuova**, non un modello nuovo.

**Uso pratico — IMPLEMENTATO (opt-in).** Il nudge e' cablato nel motore:
`market_implied.btts_season(lam, mu, matchday, rho)` alza μ per il **solo GG/NG** col
profilo stagionale e ne deriva la BTTS; `season_mu_factor(matchday)` da' il moltiplicatore
(≈1 fuori dal finale, ×1.07-1.14 nelle 35-38). Coefficienti ufficiali
`GG_SEASON_MU_COEF = (−0.00118, −0.03657, 0.16799)` = fit **pooled in-sample su 8 stagioni**
(miglior stima del profilo per l'uso; l'*effetto* e' invece validato walk-forward, ~90%),
riproducibili con `fit_season_mu_profile` e da **rifittare per ogni lega** (§7). Esposto nel
tool: `predict.py --matchday N` stampa la riga GG/NG col nudge sotto quella standard, per
entrambi i modelli. Resta **off di default** (CI include lo zero): riga informativa, non
sostituisce la GG/NG standard. Esempio:
`python scripts/predict.py Roma Fiorentina --odds 1.50 4.10 6.00 1.87 1.82 --matchday 38`
→ GG 47.4% → **51.1%** (market-implied) alla 38a giornata.

**📐 Il modello in dettaglio — il profilo liscio e perche' i numeri.**

Moltiplicatori dei tassi come regressione di Poisson (offset = log-tasso base):

```
r_λ(md) = exp(c^λ · x(md)),   r_μ(md) = exp(c^μ · x(md)),   x(md) = [1, s, tail]
s = (md − 19.5)/18.5           tail = max(0, md − 31)/7
c = argmin  Σ_i [ base_i·exp(c·x_i) − y_i·(c·x_i) ]      # MLE Poisson, offset ln(base_i)
applicazione:  λ' = λ · r_λ(md),   μ' = μ · r_μ(md)
```

verificato riga per riga contro `_fit_profile()`/`_basis()` (gradiente
X·ᵀ(rate − y), L-BFGS-B). **Ragionamento numerico.** Il profilo ospite valutato alla 38ª
da' r_μ(38) = exp(c^μ·[1, +1, +1]) = ×1.072 in media walk-forward: la salita di coda `tail`
cattura l'apertura di fine stagione, ma su 8 stagioni pesa meno che su 6 (piu' anni →
stima piu' conservativa). **Perche' la GG/NG e' l'unico sopravvissuto:** la BTTS e'
massimamente sensibile ad alzare il tasso *piu' basso* (μ, l'ospite); μ×1.07 sposta massa
da "ospite non segna" a "segnano entrambe" e migliora il GG/NG del finale, mentre sull'1X2
lo spostamento casa↔ospite e' quasi simmetrico e si annulla. **Perche' smooth < bucket
sull'1X2:** il termine `s` (trend globale) applica un moltiplicatore ≠1 gia' da meta'
stagione, dove non c'e' effetto → rumore aggiunto; i bucket lasciano intatte early/tense
e agiscono solo sul finale. La forma piu' semplice (gradino) batte quella piu' ricca:
niente da guadagnare dalla continuita'.

**Riproducibilità.** `python scripts/_run_seasonal_profile.py`
(rigenera in cache `outputs/db_base_{1819,1920}.csv` la prima volta, via `run_backtest`).

---

## Fase 49 — Perche' solo 35-38? La finestra/forma del nudge GG/NG (non e' binario)

**Obiettivo.** Rispondere a un'obiezione giusta: il ginocchio a g.31 del profilo (Fase 48)
e' scelto a mano. E se il boost si applicasse ad altre giornate, o "a scalare"? E' per
forza quella finestra, o e' un falso bianco/nero? Si fa decidere ai dati.

**Ragionamento / premessa.** Il profilo NON e' gia' binario: e' liscio
(exp(c0+c1·s+c2·coda), s trend globale + coda liscia). Ma la POSIZIONE del ginocchio e la
larghezza sono ipotesi. Prima la forma empirica — rapporto gol-ospite/μ per giornata,
8 stagioni:

```
1a meta (1-19):  1.011      20-31:  1.005      32-34:  0.966      35-38:  1.118
per-giornata nel finale:  g.35 ≈1.009   g.36 1.210   g.37 1.096   g.38 1.175
picchi a meta' (g.20 1.270, g.28 1.183): piccoli campioni (~80 gare/giornata) = rumore
```

Poi il test OOS (`scripts/_run_season_window.py`; 1 run `source=fase49_season_window`;
8 stagioni walk-forward): 5 forme del moltiplicatore μ per la GG/NG — base (r=1), coda a
g.34 (piu' stretta), g.31 (attuale), g.25 (piu' larga), e **cubica libera** [1,s,s²,s³]
(nessun ginocchio: se il segnale fosse graduale/altrove, il fit lo troverebbe). Δ GG/NG
per fetta:

```
fetta          knee34            knee31(attuale)    knee25            cubic (libera)
OVERALL      −0.0011 P98% ✓    −0.0009 P95%       −0.0007 P90%      −0.0007 P89%
early 1-19   −0.0007 P82%      −0.0006 P79%       −0.0006 P76%      −0.0007 P80%
mid 20-34    −0.0009 P89%      −0.0005 P76%       −0.0002 P61%      −0.0000 P50%
finale 35-38 −0.0036 P94%      −0.0036 P95%       −0.0029 P94%      −0.0034 P96%
(✓ = CI95 esclude lo zero; tutti gli altri lo includono)
```

**Lezione / cosa ne consegue.**
1. **Non e' binario** — il profilo e' gia' continuo. Ma la domanda vera (estendere/graduare
   su piu' giornate) ha risposta **negativa nei dati**.
2. **Allargare NON aiuta.** knee25 (seconda meta' intera) e' il PEGGIORE dei nudge
   (−0.0007); piu' larga la finestra, piu' rumore si mescola al segnale.
3. **La forma libera non trova nulla di nascosto.** La cubica, libera di curvare ovunque,
   a meta' stagione da' Δ = −0.0000 (P 50%): non c'e' segnale graduale sommerso da
   scoprire: fuori dal finale il tasso-ospite e' calibrato (≈1), e i picchi per-giornata
   (g.20, g.28) sono rumore che un fit onesto ignora.
4. **Se mai, la finestra ottimale e' piu' STRETTA.** knee34 (≈solo 35-38) e' l'unica il cui
   CI overall esclude lo zero (−0.0011, P 98%). Ma il vantaggio su knee31 e' −0.0002, entro
   il rumore e dopo molti test (disciplina multiple-testing, Fase 17) → **non giustifica il
   cambio**: knee31 resta il profilo ufficiale, ora validato come ragionevole.
5. **Perche' proprio il finale:** e' un fenomeno reale e concentrato — le ultime ~3 giornate
   le partite "si aprono" (chi rincorre spinge, chi non ha piu' nulla in palio difende meno),
   e i gol-ospite salgono. Le giornate 32-34 (tese, tutto ancora in gioco) l'ospite segna
   perfino MENO (0.966): coerente col fatto che l'apertura e' di fine-corsa, non di
   meta'-tabellone.

**📐 Il modello in dettaglio — le basi confrontate.**

```
knee_K:  base(md) = [1, s, max(0, md−K)/(38−K)]     K ∈ {34, 31, 25}
cubic:   base(md) = [1, s, s², s³]                  s = (md−19.5)/18.5
c = MLE Poisson (offset ln μ, come Fase 48);  r_μ(md) = exp(base(md)·c);  μ' = μ·r_μ(md)
```

verificato contro `_basis()`/`_fit()` in `_run_season_window.py`. **Ragionamento numerico.**
Il moltiplicatore alla 38a e' simile per tutte (×1.055-1.076): tutte "vedono" lo stesso
salto di coda, cambia solo QUANTO in la' lo spalmano. knee25 lo diluisce su 13 giornate
(×1.055, piu' debole dove serve), knee34 lo concentra su 4 (×1.076). La cubica ricostruisce
una forma simile (×1.059) ma spende gradi di liberta' a fittare il rumore di meta' stagione,
per questo overall non batte la knee semplice. **Perche' overall knee34 > knee31 di un
soffio:** knee31 applica un moltiplicatore ≠1 anche a g.32-34, dove il tasso-ospite e'
sotto 1 → un filo di rumore in piu'; knee34 le lascia intatte. Differenza reale ma
minuscola: il segnale utile e' tutto nelle ultime 3 giornate.

**Riproducibilità.** `python scripts/_run_season_window.py`.

---

## Fase 50 — Mega-sweep combinatorio: le leve OFF, insieme, su tutti i motori

**Obiettivo.** Le leve del progetto sono state validate quasi sempre UNA ALLA VOLTA
(metodo §1.2) e molte sono rimaste off per disciplina CI pur essendo "probabili":
φ35 (Fase 35/39), nudge stagionale (Fasi 48/49), power-devig (Fase 38), covariate
stakes/midweek (Fasi 32/36-bis), copula (Fase 43). Domanda del giro: qualche
**combinazione mai provata** — anche di feature su motori diversi da quelli su cui
erano state testate — migliora il gap col mercato o produce un motore migliore?
Sei esperimenti in un'unica fase (tutti registrati, un run ciascuno):

  A. **mega-sweep market-implied** (`_run_fase50_mi_sweep.py`): forma {τ, φ35,
     frank_b+φ} × nudge-μ {none, knee31, knee34} × devig {moltiplicativo, potenza}
     — 14 combo, walk-forward 8 stagioni (n=2660). Novita': il nudge fittato sui
     λ,μ DEL MERCATO (Fasi 48/49 lo validavano solo sui μ del DC);
  B. **scomposizione del nudge** (`_run_fase50_mi_decomp.py`): livello vs coda;
  C. **ricalibrazione dei tassi** λ,μ del mercato (`_run_fase50_rates_recal.py`);
  D. **ricalibrazione per-classe del MERCATO stesso** (`_run_fase50_market_recal.py`);
  E. **GBM bespoke per singolo mercato** (`_run_fase50_gbm_bespoke.py`) — l'unica
     variante dichiarata mai testata (CLAUDE.md §1.8), su ENTRAMBI i path;
  F. **sweep del path DC** (`_run_fase50_dc_sweep.py`): φ35 × covariate
     {stakes, midweek} × ri-taratura iperparametri CON φ35 attiva — 9 config × 6
     stagioni di backtest walk-forward completo.

### A. Mega-sweep del market-implied: le combo si sommano (sul GG/NG)

Risultato (n=2660, test = 7 stagioni 1920-2526; riferimento = `prop-phi35`, cioe'
la config Fase 39; `k31`/`k34` = nudge-μ con ginocchio a g.31/34):

| variante | GG/NG | Δ GG vs φ35 | CI95 | P(migliora) |
|---|--:|--:|--:|--:|
| prop-tau (Fase 26) | 0.6831 | +0.0011 | [+0.0004, +0.0018] | 0% |
| prop-phi35 (Fase 39) | 0.6821 | — | — | — |
| prop-phi35+**k31** | 0.6813 | −0.0008 | [−0.0017, +0.0002] | 95% |
| prop-phi35+**k34** | **0.6810** | **−0.0010** | **[−0.0020, −0.0000]** | **98%** |
| prop-frank | 0.6816 | −0.0004 | [−0.0008, −0.0001] | 99% |
| prop-frank+**k31** | **0.6809** | **−0.0011** | **[−0.0023, −0.0000]** | **98%** |
| pow-phi35 (power-devig) | 0.6827 | +0.0007 | [−0.0005, +0.0019] | 14% |

- **Le due leve "probabili" (φ35 e nudge-μ) sono ADDITIVE**: −0.0006 (φ35, Fase 39)
  e ~−0.0004 (nudge) ≈ −0.0010 insieme. E' il **miglior GG/NG del progetto**
  (0.6809-0.6810), e per la prima volta il CI di un guadagno GG **tocca lo zero
  senza includerlo** (hi −0.0000/−0.0001).
- **Onesta' multiple-testing (Fase 17):** 13 confronti simultanei e CI che
  *sfiorano* lo zero → l'etichetta resta "**molto probabile, non concluso**".
  Nessun cambio di default.
- Per-stagione (φ35+k34): **5/7 migliorano**, ma il guadagno e' concentrato in
  1920-2122 (−0.0024…−0.0029, l'era porte-chiuse/COVID) ed e' ≈neutro nelle
  ultime 4 stagioni (+0.0015, −0.0003, −0.0008, +0.0004) — vedi B per il perche'.
- **power-devig chiuso**: eta fittato 0.909 (accentua i favoriti), MAI utile
  (conferma e chiude la coda della Fase 38); **nudge su τ pura**: neutro — serve
  la φ35 perche' il nudge paghi; sui totali/ris.esatto ogni nudge peggiora
  (coerente col routing Fase 44: quelle famiglie restano su τ senza nudge).
- caveat: sul **pareggio secco** il vantaggio della φ35 sulla τ si attenua su
  questa finestra estesa (Δ −0.0004 a favore di τ, P 60%, trascinato dal fit
  sottile della prima stagione di test) — caveat, non smentita della Fase 43.

### B. La scomposizione: NON e' l'effetto-stagione della Fase 48

Il nudge fittato sui μ del mercato da' moltiplicatori **opposti** a quelli del DC:
alla 38ª ×0.92-0.94 (medie walk-forward) contro ×1.07-1.14 del DC. Scomposto
(`_run_fase50_mi_decomp.py`, GG/NG su φ35): solo-livello −0.0002 (P 77%),
solo-coda −0.0004 (P 91%), completo −0.0010 (P 98% ✓). E il fit **pooled** su
tutte e 8 le stagioni da' un profilo quasi **piatto** (coda +0.8%): le medie
walk-forward negative in coda vengono dai fit iniziali su campioni sottili.

La lettura onesta (con il per-stagione del punto A): il "nudge di mercato" **non
e'** l'inflazione-ospite di fine stagione (quella il mercato la prezza gia') ma una
**ricalibrazione adattiva dei tassi del mercato**, che ha pagato soprattutto
nell'era porte-chiuse (1920-2122: i gol ospite salirono e le quote inseguivano) ed
e' ≈neutra da tre stagioni. Per questo NON si cabla un coefficiente statico "di
mercato" nel motore: il valore sta nel RIFIT walk-forward, non nel numero.

### C-D. Il bias residuo del mercato: casa cara, pari/trasferta sottoprezzati

Misura per-stagione dei tassi impliciti (8 stagioni): `gol_casa/λ_mkt < 1` in 6/8
(media ~0.97) e `gol_ospite/μ_mkt > 1` in 6/8 (media ~1.02): **il bias-casa dei
book sopravvive al devig moltiplicativo** e finisce nei tassi invertiti.

- **C (tassi):** ricalibrare i LIVELLI di entrambi i tassi (λ×0.986, μ×1.023 medi)
  migliora l'**1X2 del motore**: 0.9637 → 0.9630 (Δ −0.0007, P 90%) e recupera
  meta' della perdita di inversione (mercato diretto sulla stessa finestra:
  0.9625) — ma **non batte la chiusura**. Il GG/NG preferisce il profilo completo
  su μ (k34_mu −0.0010 ✓); ricalibrare anche λ col profilo (k34_both) NON aiuta.
- **D (probabilita'):** ricalibrazione per-classe del mercato stesso,
  `q ∝ w·p_mkt` con (w_D, w_A) fittati leave-future-out (regola pre-dichiarata:
  fit ≥ 2 stagioni — su una sola e' rumore): **5/6 stagioni migliorano**, pesi
  stabili (w_D≈1.09, w_A≈1.06: pari e trasferta sottoprezzati, coerente col
  draw-bias delle Fasi 35/40), pooled 0.9632→0.9626, Δ **−0.0006 CI [−0.0020,
  +0.0009], P 78%** → **indizio, non concluso**. "Battere la chiusura in
  log-loss" resta non dimostrato, ma questa e' la crepa piu' credibile trovata
  finora (direzione giusta, meccanismo noto, pesi stabili su 6 fit).

### E. GBM bespoke per mercato: CHIUSO (perde ovunque, su entrambi i path)

L'ultima variante mai testata (§1.8). GBM calibrato (Platt cv=3), feature DC-block
+ λ,μ mercato + |λ−μ| + matchday + **la predizione dell'engine stessa** (encompassing
non-lineare sul mercato non prezzato — la Fase 23 lo fece solo sull'1X2):

| mercato | baseline | DC | mkt-impl | gbm_dc | gbm_mkt | Δ (gbm_mkt−mi), CI95 |
|---|--:|--:|--:|--:|--:|--:|
| GG/NG | 0.6838 | 0.6888 | **0.6821** | 0.6924 | 0.6919 | +0.0099 [+0.0045,+0.0154] |
| clean sheet casa | 0.5984 | 0.5686 | **0.5595** | 0.5858 | 0.5802 | +0.0206 [+0.0140,+0.0273] |
| casa Over 1.5 | 0.6791 | 0.6363 | **0.6245** | 0.6539 | 0.6415 | +0.0170 [+0.0109,+0.0233] |
| O/U 2.5 (sanity) | 0.6849 | 0.6867 | **0.6791** | 0.6952 | 0.6940 | +0.0149 [+0.0078,+0.0218] |

Il GBM **perde su ogni mercato e su entrambi i path** (anche `gbm_dc` vs DC:
+0.003…+0.017), pure avendo la predizione dell'engine tra le feature — la degrada
invece di migliorarla (stesso meccanismo della Fase 23). **La domanda "ML bespoke
per mercato" e' definitivamente chiusa**; la riserva del §1.8 si puo' togliere.

### F. Sweep del path DC: le leve si sommano senza interagire (tutto nel rumore)

9 config × 6 stagioni = 54 backtest walk-forward completi (n=2280; riferimento =
config ufficiale, 1X2 0.9797, gap col mercato +0.0165):

| variante | 1X2 | Δ vs uff. | P(migliora) | gap-mkt 1X2 |
|---|--:|--:|--:|--:|
| phi35 (= Fase 35) | 0.9790 | −0.0007 | 72% | +0.0158 |
| phi35 + stakes | 0.9790 | −0.0007 | 71% | +0.0158 |
| **phi35 + midweek** | **0.9786** | **−0.0011** | **78%** | **+0.0154** |
| phi35 + stakes + midweek | 0.9786 | −0.0011 | 77% | +0.0154 |
| stakes + midweek (senza φ35) | 0.9793 | −0.0004 | 68% | +0.0161 |
| phi35, emivita 270g | 0.9790 | −0.0007 | 68% | +0.0158 |
| phi35, emivita 540g | 0.9791 | −0.0005 | 67% | +0.0159 |
| phi35, shrinkage 0.75 | 0.9789 | −0.0008 | 72% | +0.0157 |
| phi35, shrinkage 3.0 | 0.9796 | −0.0001 | 52% | +0.0164 |

- **sanity:** la φ35 riproduce identico il numero della Fase 35 (0.9790);
- **le covariate si sommano alla φ35 senza interferire:** midweek aggiunge
  −0.0004, lo **stakes non aggiunge nulla** una volta che la φ35 c'e' (0.9790
  identico); φ35+midweek = **0.9786**, il miglior 1X2 del progetto (gap
  **+0.0154**), ma P 78% e CI ampio [−0.0040, +0.0018];
- **NESSUNA interazione iperparametri × φ35:** emivita 270/365/540 e shrinkage
  0.75/1.5 tutte ≈0.979 (curva piatta come in Fase 8); solo shrinkage 3.0
  peggiora. La taratura ufficiale resta ottima anche con la φ35 attiva — non
  c'era un "ottimo nascosto" condizionato alla nuova struttura.

### Tool (`predict.py`): fix del nudge sul path market-implied

La Fase 48 esponeva il nudge (coefficienti fittati sui μ del DC) su ENTRAMBI i
modelli del tool. Verificato in questa fase: applicare quel profilo ai μ del
mercato **peggiora** (GG overall +0.0002, finale 35-38 **+0.0014**, n=283) — il
mercato prezza gia' l'apertura del finale. `predict.py` ora mostra il nudge solo
sul Modello 1 (DC) e sul Modello 2 stampa il perche' (`nudge=False`).

**Lezione / cosa ne consegue.**
1. Le uniche combo che muovono qualcosa stanno sul **GG/NG** (il mercato non
   prezzato — principio 8) e sull'**1X2 letto dal mercato**; vengono da
   informazione + struttura giusta, mai da un modello nuovo (conferma Fasi 22/24/26).
2. **φ35 e nudge-μ sono componibili e additivi** — la miglior stima GG/NG del
   progetto e' ora: inverti 1X2+O/U → ricalibra μ (rifit walk-forward, profilo
   knee34) → φ(|λ−μ|) → P(GG) = **0.6810** (con copula: 0.6809, +complessita' per
   −0.0001 → non si adotta, stessa logica Fase 44). Etichetta: molto probabile,
   non concluso → **off di default**, disponibile come miglior stima condizionata.
3. Il mercato ha **bias residui misurabili** oltre il draw-bias: casa cara ~2-3%
   nei tassi impliciti, pari/trasferta sottoprezzati nelle probabilita' (w_D 1.09,
   w_A 1.06 stabili). Nessuno dei due e' (ancora) un edge dimostrato in log-loss.
4. **GBM bespoke chiuso per sempre** (quarta e ultima bocciatura della famiglia:
   Fasi 21/22/23/36 + questa). Il tetto resta informativo.
5. Sul path DC **le leve off si combinano onestamente** — nessuna interazione
   nascosta, ne' positiva (nessun ottimo iperparametrico condizionato alla φ35)
   ne' negativa (le covariate non si rubano il segnale, semplicemente lo stakes
   e' ridondante con la φ35 sull'1X2). Il "pacchetto completo" φ35+midweek e'
   la miglior variante DC (0.9786, gap +0.0154) ma resta **nel rumore** (P 78%):
   il tetto informativo regge anche alle combinazioni.

### 📐 Il modello in dettaglio — le formule della fase

**Nudge-μ sul mercato** (A/B/C) — identico alla Fase 48/49 ma con base = μ del
mercato (dall'inversione delle quote, Fase 26), fittato leave-future-out:

```
(λ, μ) = implied_lambda_mu(1X2 devigato, O/U devigato, ρ=−0.06)      # Fase 26
r_μ(md) = exp(c·x(md)),  x(md) = [1, s, coda]                        # knee31/34
s = (md−19.5)/18.5;   coda_K = max(0, md−K)/(38−K),  K ∈ {31, 34}
c = argmin Σ_i [ μ_i·exp(c·x_i) − y_i·(c·x_i) ]      # MLE Poisson, offset ln μ
μ' = μ·r_μ(md);  poi φ(|λ−μ'|) rifittata sui tassi ricalibrati (Fase 39)
```

verificato riga per riga contro `_fit_nudge`/`_nudged` (`_run_fase50_mi_sweep.py`)
e `_fit`/`_basis` (`_run_fase50_mi_decomp.py`). **Perche' i numeri:** i fit
walk-forward danno r_μ(38) medio 0.92-0.94 — ma e' una media di fit per meta'
sottili; il fit pooled 8 stagioni da' coefficenti `(+0.0212, −0.0016, +0.0082)` =
profilo quasi piatto con livello +2.1%: il contenuto vero del nudge-di-mercato e'
il LIVELLO adattivo (μ del mercato basso ~2%, di piu' nell'era porte-chiuse), non
la coda. Per questo NON esiste un `GG_SEASON_MU_COEF_MKT` statico nel motore.

**Ricalibrazione per-classe del mercato** (D) — riuso della forma Fase 10, ma
applicata alle probabilita' devigate del MERCATO, non al modello:

```
q_i(p) ∝ w_i · p_mkt,i        w = (1, w_D, w_A) fittato sulle stagioni passate
w_D, w_A = argmin  −Σ log q_esito(p)   su ≥ 2 stagioni di training (pre-dichiarato)
```

**Perche' w_D≈1.087 e w_A≈1.058.** Sono il rapporto sistematico tra frequenze
reali e prezzi devigati: il pari reale ~32-33% e' prezzato ~30-31% (il draw-bias
gia' misurato in Fase 35: 0.296 vs 0.332 sulle equilibrate), la trasferta e'
sottoprezzata dal bias-casa. Moltiplicare e rinormalizzare sposta ~1-2 punti di
massa da casa verso pari/trasferta. Il guadagno atteso e' dell'ordine del bias²
→ ~0.0005-0.001 di log-loss: coerente col −0.0006 osservato; per "concludere"
servirebbero ~20 stagioni (stessa matematica della Fase 40 sul ROI).

**GBM bespoke** (E): stesso `HistGradientBoostingClassifier(max_iter=200,
max_depth=3, lr=0.05, l2=1.0, min_leaf=30)` + `CalibratedClassifierCV(sigmoid,
cv=3)` delle Fasi 36/45, con in piu' le feature `mlam, mmu, |λ−μ|_mkt, λ+μ_mkt,
mi_p_target` (la predizione dell'engine) e `matchday`. Il fallimento con la
predizione-engine in input e' informativo: un albero che PARTE dalla risposta
giusta e la peggiora conferma che le feature residue contengono solo rumore
(stesso esito dell'encompassing non-lineare, Fase 23).

**Sweep DC** (F): nessuna matematica nuova — covariate (Fase 4c: termine
β·z nella log-intensita'), φ35 (Fase 35), iperparametri (Fase 2b). La novita' e'
la COMBINAZIONE, e il risultato e' l'assenza di interazioni: il Δ della coppia
φ35+midweek (−0.0011) e' la somma dei Δ singoli (−0.0007 e −0.0003/−0.0004,
Fasi 35 e 36-bis) entro l'arrotondamento — additivita' quasi esatta, cioe' le due
leve correggono difetti ortogonali (massa-pareggio vs congestione europea).

**Riproducibilità.** `python scripts/_run_fase50_mi_sweep.py` ·
`_run_fase50_mi_decomp.py` · `_run_fase50_rates_recal.py` ·
`_run_fase50_market_recal.py` · `_run_fase50_gbm_bespoke.py` ·
`_run_fase50_dc_sweep.py` (cache: `scripts/_gen_cache.py`).

---

## Fase 51 — Audit delle lacune + modelli mai provati: la sotto-dispersione batte la chiusura

**Obiettivo.** Audit sistematico delle 50 fasi: quali calcoli/analisi mancano?
Quali famiglie statistiche non sono mai state provate? Lacune trovate:

1. **La Fase 27 aveva testato solo META' dell'asse dispersione**: la binomiale
   negativa copre solo la SOVRA-dispersione (rigettata → "gol ~ Poisson"). La
   SOTTO-dispersione non era testabile con quella famiglia → **double-Poisson di
   Efron (1986)**, che copre entrambe le direzioni con un parametro θ.
2. **Rue-Salvesen (2000)** mai provato (smorzamento della differenza di forza).
3. **Zero-inflazione dello 0-0** mai provata (il ρ tocca 4 punteggi, la φ35 la
   diagonale intera; lo 0-0 da solo mai).
4. Il **Kalman vero** (random-walk delle forze) non e' mai stato fittato: la
   Fase 48 ha chiuso "l'architettura dinamica" testando il profilo stagionale
   deterministico, non lo state-space. Nota onesta: resta **chiuso per
   argomento** — il decadimento esponenziale (emivita) E' il filtro di Kalman a
   regime per un random-walk osservato con rumore, e le emivite sono gia' state
   spazzate (Fasi 2b/4d/12a); il guadagno atteso di un Kalman pieno e' ~0. Non testato.
5. Combo suggerite dalla Fase 50 e mai valutate: routing con tassi ricalibrati
   per famiglia; recal O/U; ROI pareggio-equilibrio coi tassi del MERCATO;
   GBM bespoke sul pareggio (il Track C non lo includeva).

Cinque esperimenti (tutti su cache, un run ciascuno): **A** batteria di forme
(`_run_fase51_shape_battery.py`), **B** routing v2 (`_run_fase51_routing2.py`),
**C** "si batte la chiusura?" (`_run_fase51_beat_close.py`), **D** ROI
(`_run_fase51_roi.py`), **E** pareggio bespoke + recal O/U
(`_run_fase51_draw_ou.py`).

### A. La batteria delle forme: i gol sono SOTTO-dispersi, dati i tassi del mercato

Fit walk-forward sui tassi del mercato (8 stagioni, n=2660):

| variante | GG/NG | ris.esatto | pareggio | 1X2 | parametro medio |
|---|--:|--:|--:|--:|---|
| τ (Fase 26) | 0.6831 | 2.8250 | 0.5684 | 0.9633 | — |
| φ35 (Fase 39) | 0.6821 | 2.8254 | 0.5688 | 0.9637 | φ0≈0.30 |
| **double-Poisson (dp)** | 0.6815 | **2.8172** | **0.5679** | **0.9615** | **θ=1.205** |
| dp + φ35 | **0.6812** | 2.8181 | 0.5688 | 0.9624 | |
| Rue-Salvesen | 0.6830 | 2.8253 | 0.5684 | 0.9642 | γ=+0.033 |
| zero-inflazione 0-0 | 0.6834 | 2.8254 | 0.5689 | 0.9638 | z=−0.006 |

- **La double-Poisson e' la scoperta**: θ>1 in TUTTI e 7 i fit (1.16→1.24,
  cresce con la finestra = stima consistente). I gol, condizionati ai tassi del
  mercato, hanno varianza **~10% SOTTO la Poisson** (esatto ai tassi reali; il
  "17%" = 1−1/θ è l'approssimazione asintotica per μ grande, vedi il blocco 📐):
  la matrice va **concentrata**, non allargata. La Fase 27 non poteva vederlo (la NB va solo nell'altro verso).
  Migliora TUTTO il blocco esiti: 1X2 −0.0021 vs φ35, risultato esatto −0.0078
  (il piu' grande guadagno dal Fase 26), pareggio, GG.
- **Rue-Salvesen: γ=+0.033 piccolo, nessun guadagno** (il suo lavoro lo fa gia'
  la φ35, in modo mirato). **Zero-inflazione: z≈0** — dopo ρ e φ35 lo 0-0 non ha
  massa mancante. Entrambe chiuse pulite.

### B. Routing v2 (tassi per famiglia): conferma e un mercato nuovo

Router con tassi ricalibrati per famiglia (lvl_both per esiti, k34_mu per GG,
τ grezza per totali) vs router Fase 44, 20 mercati Tier 1: media 0.5517 vs
0.5519; GG **−0.0010 ✓CI** (conferma Track A per via indipendente), scarto-casa
≥2 **−0.0012 ✓CI (P 100%)**, pareggio −0.0003 (P 89%); totali identici per
costruzione. Adottato come routing di riferimento del motore *(nota: superato
in parte dalla dp del punto C — il router coi tassi dp è il candidato Fase 52)*.

### C. Si batte la chiusura? SI' — prima volta con CI conclusivo (in log-loss)

Confronto APPAIATO sull'1X2, stessa finestra (n=2660), vs mercato devigato:

| variante | 1X2 | Δ vs mercato | CI95 | P | stagioni |
|---|--:|--:|--:|--:|--:|
| mercato (devig) | 0.9625 | — | — | — | — |
| mercato + temperatura T (LFO) | 0.9615 | −0.0010 | [−0.0027, +0.0007] | 87% | 6/7 |
| mercato + w-classe (50-ter) | 0.9635 | +0.0011 | [−0.0007, +0.0029] | 11% | 5/7 |
| double-Poisson (dp) | 0.9615 | −0.0009 | [−0.0020, +0.0002] | 95% | 4/7 |
| **dp + livelli (dp_lvl)** | **0.9609** | **−0.0016** | **[−0.0029, −0.0003]** | **99%** | **7/7** |

- **dp_lvl** = double-Poisson (θ LFO) sui tassi ricalibrati nei LIVELLI
  (λ×~0.97, μ×~1.02, il bias-casa della Fase 50). **CI95 esclude lo zero, 7/7
  stagioni, e regge sul sottoinsieme con fit ≥2 stagioni (−0.0018)**. E' il primo
  risultato del progetto che batte la linea di chiusura in log-loss con CI
  conclusivo. Meccanismo = composizione di DUE bias misurati indipendentemente
  (sotto-dispersione + tilt casa/trasferta), non un fit fortunato.
- La **temperatura sul mercato** (mai provata prima; T≈1.10 = chiusura un filo
  SOTTO-confidente) da sola fa −0.0010 (87%): meta' dell'effetto dp e' proprio
  sharpening; l'altra meta' (il tilt dei livelli) la temperatura non puo' farla.
- Onesta': (i) "chiusura" = devig moltiplicativo, il benchmark usato in TUTTO il
  progetto (gap +0.0165 ecc.) — un devig piu' raffinato (Shin) potrebbe assorbire
  parte del bias; (ii) dopo ~50 fasi di test sulla stessa finestra un CI a
  [−0.0029,−0.0003] va preso con disciplina: e' il risultato piu' forte mai
  visto qui, non una verita' assoluta.

### D. Il ROI: l'edge di log-loss NON e' un edge di scommessa

- Pari-equilibrio coi tassi del MERCATO (|λ−μ|<0.5, soglia Fase 40): **+3.2%**
  (n=1141, 7 stagioni, CI [−5.9%, +11.9%], P 76%, 5/7 positive) — coerente col
  +4.7% della Fase 40 (tassi DC, 6 stagioni), sempre non conclusivo.
- Filtro "edge dp_lvl" sul pari: PEGGIORA (−13.3%, n=92) — l'affinamento dp_lvl
  non seleziona value-bet sul pari.
- Value-bet 1X2 con dp_lvl (edge>0.03): quasi MAI attivato (1 bet casa, 0 pari,
  69 trasferta +6.0% CI include 0). L'affinamento e' ~0.5-1% per esito, il
  margine ~5%: **battere la chiusura in log-loss ≠ batterla in ROI**. Il valore
  del dp_lvl e' da ORACOLO (stima migliore), non da scommettitore.

### E. Le due simmetrie mancanti: chiuse

- **GBM bespoke sul PAREGGIO** (il mercato che mancava al Track C): perde anche
  qui (+0.0078 vs engine, CI [+0.0033,+0.0123], P=0%). La famiglia bespoke e'
  ora bocciata su TUTTI i mercati provati (GG, CS, total-squadra, O/U, pari).
- **Recal O/U del mercato** (w_over≈1.07 fittato): out-of-sample PEGGIORA
  (+0.0013, P 7%) — il bias O/U non e' stabile, a differenza del tilt 1X2.

**Lezione / cosa ne consegue.**
1. **Un audit onesto trova ancora spazio**: la lacuna era su un asse (sotto-
   dispersione) che il test esistente (NB) non copriva per costruzione. Metodo:
   quando un test rigetta una famiglia, chiedersi quali direzioni QUELLA
   famiglia non puo' vedere.
2. Il motore market-implied guadagna un'opzione di **stima 1X2 affinata**
   (`market_implied.sharpen_1x2`, costanti pooled θ=1.225 e livelli
   (0.9726, 1.0224), da rifittare per lega — §7); esposta in `predict.py` come
   riga informativa. La chiusura resta il benchmark del GAP (coerenza storica).
3. Il draw-bias resta l'unico candidato di ROI (+3.2/+4.7%, mai concluso);
   tutto il resto e' oracolo, non scommessa.
4. Rue-Salvesen, zero-inflazione, GBM-pareggio, recal-O/U: **chiusi**.
   Kalman: chiuso per argomento (dichiarato, non testato).

### 📐 Il modello in dettaglio — la double-Poisson e perche' i numeri

**La PMF double-Poisson mean-preserving** (verificata riga per riga contro
`market_implied._dp_pmf` e `_dp_pmf` negli script `_run_fase51_*`):

```
q_k(r, θ) ∝ [ Poisson(k; c·r) ]^θ ,  k = 0..10, rinormalizzata
c risolto per bisezione (45 iter.) perche'  Σ k·q_k = r   (media preservata)
matrice:  M = q(λ)⊗q(μ), poi correzione ρ sui 4 punteggi bassi e rinorm.
dp_lvl:   λ' = λ·0.9726,  μ' = μ·1.0224  (livelli pooled, Fase 50/51), poi dp
```

**Perche' θ ≈ 1.2 (e non 1).** Elevare la PMF a θ>1 e rinormalizzare concentra
la massa attorno alla media. La relazione `Var ≈ Var_Poisson/θ` (da cui verrebbe
"~17% meno" = 1−1/1.205) è l'**approssimazione asintotica per μ grande** di Efron:
ai tassi-gol reali (μ≈1.2–1.5) l'esatto sulla `_dp_pmf` dà una riduzione di
varianza **~10–12%** (a μ=1.24, θ=1.205: Var 1.115, −10.1%; std ~−5%), non 17% —
servirebbe θ≈1.35 per un vero −17%. Il fit MLE walk-forward trova θ=1.16→1.24
(piu' dati → stima piu' alta e piu' stabile): i punteggi reali, condizionati ai
tassi del mercato (che sono stime BUONE), oscillano **~10% meno** di una Poisson. Intuizione: la Poisson assume l'intensita' costante e indipendenza
tra i gol; nel calcio reale chi conduce gestisce (il 2-0 "si addormenta"), e la
parte di varianza dovuta all'incertezza sui tassi qui NON c'e' (i tassi sono
condizionati, non stimati male). La NB della Fase 27 (solo Var>media) non poteva
scoprirlo: rigettarla NON implicava "Poisson ottima", implicava "non
sovra-dispersi" — l'errore logico che l'audit ha stanato.

**Perche' θ migliora l'1X2 e il risultato esatto.** Concentrare la matrice
alza le celle centrali (i punteggi tipici) → il risultato esatto guadagna
−0.0078; sull'1X2 l'effetto e' uno sharpening coerente delle tre probabilita'
(analogo a T=1.10 sul mercato: la chiusura e' un filo sotto-confidente, perche'
il margine e il devig moltiplicativo "appiattiscono" le prob implicite).

**Perche' i livelli (0.9726, 1.0224).** `exp(c) = Σ gol / Σ tasso` pooled su
8 stagioni (MLE Poisson del fattore comune, come Fase 47): il bias-casa dei book
sopravvive al devig e finisce nei tassi invertiti (λ alto, μ basso). Il tilt
sposta ~1 punto di massa da casa a trasferta — la componente che lo sharpening
non puo' dare.

**ROI del pari-equilibrio** (D): stessa formula della Fase 40
(`ROI = media[1{pari}·quota − 1]` su |λ−μ|<0.5), con λ,μ del mercato: +3.2%
pooled, CI [−5.9,+11.9] — la varianza attesa di un evento a quota ~3.3 su
n=1141 e' ±9% (stessa matematica della Fase 40): per concludere servono ~20
stagioni o una quota migliore (exchange).

**Riproducibilità.** `python scripts/_run_fase51_shape_battery.py` ·
`_run_fase51_routing2.py` · `_run_fase51_beat_close.py` · `_run_fase51_roi.py` ·
`_run_fase51_draw_ou.py`.

---

## Fase 52 — Spremere la scoperta: la double-Poisson su tutto il listino, i suoi limiti, e il dinamico chiuso per test

**Obiettivo.** Sette esperimenti per spremere fino in fondo la scoperta della
Fase 51 (sotto-dispersione + tilt) e chiudere le ultime domande aperte: dove
vale la dp e dove no, il tilt e' un artefatto del devig, i bias esistono
nell'apertura, la sotto-dispersione e' uniforme, e lo state-space chiuso per
test (non piu' per argomento).

### A. L'O/U 2.5 NON si batte (`_run_fase52_ou_close.py`)

Confronto appaiato mai fatto (la Fase 26 l'aveva liquidato come "banale"): devig
binario diretto 0.6788 vs matrice τ +0.0003, dp +0.0003, dp_lvl +0.0010,
temperatura +0.0006 — **il devig binario resta il migliore** (nessun P>17%).
L'edge dell'1X2 viene dalla struttura pareggio/tilt-casa, che l'O/U non ha; il
"banale" della Fase 26 era giusto. Chiuso.

### B. Router v3: la dp estesa a tutto il listino DOMINA (`_run_fase52_router3.py`)

Router v3 = marginali double-Poisson ovunque (+ φ35 e ricalibrazioni della
Fase 51 sulle stesse famiglie) vs router v2. Su 20 mercati Tier 1: **mai
peggiore**, media −0.0005, e **5 mercati con CI conclusivo**: ospite-segna/
clean-sheet-casa **−0.0023** (P 99%), casa-vince **−0.0011** (P 100%), scarto≥2
**−0.0011** (P 100%), ospite O1.5 **−0.0008** (P 100%). La TRIPLA sul GG
(dp+k34+φ35) invece **satura** a 0.6809: dp e φ35+k34 correggono la stessa cosa
sul GG, non si sommano. **ADOTTATO nel motore**: `price_markets(dp_theta=...)`
(opt-in, None = router Fase 44), usato da `predict.py` con θ=1.225 (mercato) e
θ=1.138 (DC).

### C. Il devig di Shin: il tilt e' PER META' un artefatto (`_run_fase52_shin.py`)

Il caveat onesto della Fase 51, quantificato. Shin (mai provato) e' davvero un
devig migliore: 0.9617 (Δ −0.0007, P 97%). Il dp_lvl (0.9609) batte anche Shin
ma **senza CI conclusivo**: Δ −0.0009 [−0.0021, +0.0003], P 93%. Riformulazione
onesta del claim di Fase 51: *conclusivo contro il benchmark storico del
progetto (devig moltiplicativo); molto probabile (93%) ma non concluso contro il
miglior devig*. In piu': la temperatura SOPRA il dp_lvl aggiunge ancora
(T=1.056≠1 → 0.9605, Δ −0.0020, P 97% ma CI [−0.0040,+0.0001]): θ non assorbe
tutta la sotto-confidenza della chiusura.

### D. La dp regge sul path DC (`_run_fase52_dp_dc.py`)

θ fittato sui tassi del NOSTRO DC: **θ_DC = 1.138** — piu' basso del mercato
(1.205), esattamente come predice l'argomento del rumore (sotto-dispersione
osservata = vera − rumore dei tassi; i nostri tassi sono piu' rumorosi), e
ancora >1. Migliora anche il fallback senza quote: 1X2 **0.9794** (−0.0009,
P 99%), risultato esatto **−0.0041** (P 100%), pareggio best. Il nuovo miglior
1X2 standalone del progetto.

### E. La sotto-dispersione e' UNIFORME (`_run_fase52_theta_cond.py`)

θ(x) = θ0 + θ1·x con x ∈ {volume λ+μ, equilibrio |λ−μ|, coda stagione}: il fit
LFO da' **θ1 = 0.000 su tutti e tre gli assi, in tutti i fit** — nessun
condizionamento batte il θ costante. La sotto-dispersione e' una proprieta'
globale dei punteggi dati i tassi, non un effetto di contesto: massima
robustezza per la costante unica del motore.

### F. I bias esistono gia' NELL'APERTURA — e l'open affinato VALE la chiusura (`_run_fase52_open.py`)

Sulle righe con quote open complete (n=2278): θ_open=1.218, tilt μ×1.043.
Confronti appaiati:

```
dp_lvl(open) − open_devig   = −0.0019  CI[−0.0036, −0.0002] ✓CI   (batte l'open)
dp_lvl(open) − close_devig  = +0.0001  CI[−0.0031, +0.0033]       (= chiusura!)
dp_lvl(close) − close_devig = −0.0018  CI[−0.0037, −0.0001] ✓CI   (conferma F.51)
close_devig − open_devig    = −0.0020  (l'affilamento open→close, Fase 14)
```

**L'apertura affinata coi bias sistematici RAGGIUNGE la chiusura grezza**
(0.9630 = 0.9630): quello che il mercato "impara" tra venerdi' e il kickoff e',
in media, quasi tutto ricalibrazione sistematica (sotto-confidenza + tilt), non
notizie. Le notizie vere esistono ma pesano quanto il residuo dp_lvl(close) −
dp_lvl(open) ≈ −0.0019. Rilettura fine della Fase 14: "il mercato sa gia' tutto
il venerdi'" va corretta in "il venerdi' il mercato sa gia' tutto, MA e' anche
sistematicamente mal calibrato di ~0.002".

### G. Lo state-space chiuso PER TEST (`_run_fase52_gas.py`)

Modello score-driven (GAS-lite): forze aggiornate DOPO OGNI partita col residuo
di Pearson (η scelto LFO, ~0.035-0.05), nessun refit batch. Risultato: 1X2
0.9830 vs DC batch 0.9803 (**Δ +0.0027, P(GAS meglio)=18%, 3/7 stagioni**).
Il dinamico online non aggiunge nulla al decadimento esponenziale — che ne e' lo
steady-state — e in pratica perde (piu' varianza di stima). La chiusura della
Fase 48, che era per argomento, ora e' per test.

**Nota fattibilita' Premier (Fase 53).** La validazione cross-lega resta il
test piu' importante rimasto, ma football-data.co.uk NON e' raggiungibile dalla
policy di rete corrente (403 dal proxy) e il mirror storico e' sparito (Fase
14): servono una modifica della policy o l'upload manuale dei CSV `E0`.

**Lezione / cosa ne consegue.**
1. **La scoperta della Fase 51 e' robusta e generale** (uniforme nel contesto,
   presente in apertura e chiusura, su tassi di mercato E nostri) **ma il suo
   perimetro e' l'1X2/famiglia-esiti**: l'O/U non si batte, il GG satura.
2. Contro il miglior devig (Shin) l'edge scende a −0.0009 (93%): meta' del
   guadagno era "devig migliore". Onesta' aggiornata nel claim.
3. **Router v3 adottato** (mai peggiore, 5 CI conclusivi); il fallback DC
   guadagna anche lui (θ_DC=1.138).
4. L'apertura-affinata≈chiusura e' la quantificazione piu' pulita mai avuta di
   QUANTO del vantaggio della chiusura sia informazione vera (~0.002) vs
   calibrazione (~0.002).
5. Dinamico: chiuso per test. Il conto delle architetture bocciate e' completo.

### 📐 Il modello in dettaglio — le formule della fase

**Shin (C)** — verificato contro `shin_devig` in `_run_fase52_shin.py`:

```
π_i = 1/quota_i,  Π = Σπ;   p_i(z) = [√(z² + 4(1−z)·π_i²/Π) − z] / (2(1−z))
z risolto per bisezione perche' Σp_i = 1   (z = quota di scommettitori informati)
```

z>0 sposta massa dai favoriti ai longshot in modo NON proporzionale — corregge
il favourite-longshot bias che il devig moltiplicativo lascia. |shin−molt| medio
0.0047: una correzione piccola ma reale (Δ −0.0007).

**GAS (G)** — verificato contro `_run_gas`:

```
λ = exp(c + a_H − d_A + γ),  μ = exp(c + a_A − d_H)
update dopo la partita (residuo di Pearson, auto-scalato):
  a_H += η·(y_H−λ)/√λ,  d_A −= η·(y_H−λ)/√λ   (e simmetrico per l'ospite)
```

η≈0.035-0.05 scelto LFO: un η cosi' piccolo equivale a una memoria effettiva
~1/η ≈ 20-30 partite — piu' corta dell'emivita 365g del DC, ed e' per questo che
perde: il segnale delle forze vive su orizzonti lunghi (Fasi 2b/25), e l'update
per-partita compra reattivita' pagando varianza.

**Perche' l'open affinato = chiusura (F).** Scomposizione:
`close_raw − open_raw ≈ −0.0020` (Fase 14) e `open_affinato − open_raw =
−0.0019`; se la parte sistematica (θ, tilt) e' la stessa nelle due linee (θ_open
1.218 ≈ θ_close 1.205), l'affinamento cattura la stessa quantita' che il flusso
di scommesse incorpora tra venerdi' e domenica — la parità osservata (+0.0001)
dice che l'informazione *incrementale* vera della chiusura vale ≈ l'affinamento
sistematico residuo che ancora le manca.

**Router v3 (B)**: nessuna matematica nuova — dp (Fase 51) dentro il routing
per-famiglia (Fase 44) con le ricalibrazioni della Fase 50; la novita' e'
l'estensione e l'esito (dominanza debole, 5 CI conclusivi).

**Riproducibilità.** `python scripts/_run_fase52_ou_close.py` · `_run_fase52_router3.py`
· `_run_fase52_shin.py` · `_run_fase52_dp_dc.py` · `_run_fase52_theta_cond.py` ·
`_run_fase52_open.py` · `_run_fase52_gas.py` (helper comuni: `_fase52_common.py`).

---

## Fase 53 (tracer) — Cross-lega: i bias del mercato sono UNIVERSALI o Serie A?

**Obiettivo.** La validazione piu' forte possibile delle Fasi 50-52: se
sotto-dispersione, tilt e draw-bias compaiono anche su Premier League e La Liga,
sono proprieta' dei mercati calcistici; se no, sono idiosincrasie della Serie A.
Dati: bundle caricati dall'utente (`files/football_data_*_bundle.json`, 9
stagioni 1718-2526 per lega, formato football-data, stesse preferenze-colonna
del loader §5). Tracer market-side (metodo §1.3): niente port del DC — bastano
quote di chiusura + risultati. I bundle Understat (xG) restano per il futuro
port completo.

**Risultato** (`scripts/_run_fase53_crossleague.py`; walk-forward, 8 stagioni di
test per lega, n=3040 ciascuna; 2 run `source=fase53_crossleague`):

| | **Serie A** (F.51-52) | **Premier** | **La Liga** |
|---|--:|--:|--:|
| θ (sotto-dispersione) | **1.205** | 1.069 | 1.097 |
| livelli λ / μ | 0.973 / **1.022** | 0.981 / 0.988 | 0.964 / 0.972 |
| w_D (pareggio) | **1.094** | **0.932** | 1.010 |
| dp_lvl − mercato (1X2) | **−0.0016 ✓CI** | +0.0008 (P 3%) | +0.0001 (P 38%) |
| Shin − mercato | −0.0007 (P 97%) | −0.0002 (P 68%) | −0.0005 (P 94%) |
| ROI pari-equilibrio | +3.2% (P 76%) | **−5.4% (P 11%)** | +3.6% (P 81%) |

**Lezione / cosa ne consegue — il ridimensionamento onesto.**
1. **La sotto-dispersione e' universale nel SEGNO** (θ>1 in tutte e tre le
   leghe, su ogni fit) **ma non nella taglia**: θ decresce con la liquidita'
   del mercato (Premier 1.07 < Liga 1.10 < Serie A 1.21). E sotto ~1.1 e'
   troppo piccola per battere la chiusura.
2. **Il tilt casa/trasferta e il draw-bias NON si replicano.** In Premier
   entrambi i tassi impliciti sono un filo alti (nessuna asimmetria) e i
   pareggi sono SOVRA-prezzati (w_D=0.93, opposto della Serie A); il ROI
   pari-equilibrio e' negativo (−5.4%). La Liga e' intermedia (draw-bias
   simile alla Serie A: +3.6%, P 81%; tilt assente).
3. **Quindi: il "beat-the-close" della Fase 51 e' una proprieta' della
   chiusura della SERIE A** — un mercato meno liquido e meno efficiente — non
   dei mercati calcistici. Anche RIFITTATA per lega, la dp non basta dove θ e'
   piccolo (Premier dp +0.0001). Coerenza notevole col quadro di efficienza:
   piu' liquidita' → chiusura meglio calibrata → meno spazio.
4. **Il §7 e' vendicato nel modo piu' concreto**: nessun numero si trasferisce
   (θ, livelli, w — tutti diversi per lega). Le costanti del motore
   (`DP_THETA`, `RATE_LEVELS`) restano dichiaratamente Serie A.
5. Il draw-bias della Serie A (Fasi 35/40) trova un mezzo-gemello in Liga e un
   contro-esempio in Premier: per scommetterci servirebbe capire *perche'*
   (liquidita'? cultura di scommessa locale sul pareggio?) — fuori dal
   perimetro dei dati attuali.

### 📐 Il modello in dettaglio

Nessuna matematica nuova: θ/livelli/w_D/w_A/dp_lvl/Shin/ROI identici alle Fasi
50-52 (formule ivi verificate), applicati per lega con fit leave-future-out per
lega. Convenzioni-quota: le stesse liste di preferenza del loader
(`loader._ODDS_PREFERENCE`: AvgCH→B365CH→AvgH→BbAvH→B365H, ecc.) — fonte unica
§5. **Perche' θ_Premier < θ_SerieA:** θ misura quanto i punteggi oscillano meno
di una Poisson DATI i tassi del mercato; tassi piu' precisi (mercato piu'
liquido) lasciano meno varianza residua apparente MA anche meno errore
sistematico di calibrazione — l'ordinamento θ ∝ 1/liquidita' e' coerente con
l'interpretazione della Fase 51 (θ cattura la sotto-confidenza della chiusura,
che nei mercati liquidi e' minima).

**Prossimo passo naturale (Fase 53-bis, non tracer):** port completo del DC su
Premier/Liga coi bundle Understat (blend xG), ri-taratura §7 (emivita, δ
promosse, α), e verifica se il *gap modello-vs-mercato* (+0.0165 in Serie A) e'
piu' largo o stretto dove il mercato e' meno/piu' efficiente.

**Riproducibilità.** `python scripts/_run_fase53_crossleague.py`.

---

## Fasi 54-57 — Premier League e La Liga: conoscere due leghe nuove da zero

Dopo 53 fasi tutte sulla Serie A, l'utente chiede un lavoro **approfondito** su
Premier e La Liga: ripartire dai dati, capirne le differenze, e verificare se
gli STESSI modelli reggono. È l'esame più severo del §7 (le formule sono
universali, i numeri no) e delle scoperte recenti (sotto-dispersione, draw-bias,
gap col mercato): sono proprietà del calcio o idiosincrasie della Serie A?

### Fase 54 — La pipeline: due leghe nello stesso schema

**Obiettivo/vincolo.** Il provider (football-data.co.uk) è irraggiungibile
(403 dal proxy) e il mirror storico è sparito (Fase 14). I dati grezzi sono stati
**caricati a mano** come bundle JSON in `files/` — football-data (risultati +
quote) e Understat (xG), 9 stagioni ciascuna (2017-18 → 2025-26), stesso
formato/era della Serie A.

**Scelta.** `scripts/build_league_snapshot.py` fonde i bundle nello **stesso
schema interno** della Serie A (riusa `loader._normalize` per risultati/quote e
`understat.parse_season_xg` per l'xG — refactor che separa il parsing dal
download), con i medesimi controlli d'integrità, e congela
`data/{premier_league,la_liga}_matches.csv` (versionati, offline-first). La lega
è ora una modifica di **configurazione** (voce in `sources.LEAGUES`,
`UNDERSTAT_LEAGUES`, alias), non di codice (§4/§7).

**Il punto critico: i nomi squadra.** Football-data e Understat scrivono gli
stessi club in modo diverso (il bug silenzioso della Fase 2a). Estratti TUTTI i
nomi delle 9 stagioni da entrambe le fonti: **6 differenze in Premier**
(Man City/Manchester City, Wolves/Wolverhampton Wanderers, …) e **11 in La Liga**
(Ath Madrid/Atletico Madrid — distinta da Real Madrid! —, Betis/Real Betis, …),
tutte verificate **per identità** (non per ordinamento) e aggiunte a
`TEAM_ALIASES`. Risultato: **copertura xG 100%, zero righe orfane** su entrambe
le leghe. Due test nuovi bloccano la riconciliazione (nessun "quasi-duplicato").

### Fase 55 — EDA: come si muovono i dati (la tabella che risponde alla domanda)

**Obiettivo.** PRIMA di modellare, conoscere i dati (metodo §1). Statistiche
descrittive delle tre leghe sulle dimensioni che sono state portanti in Serie A.

| | Serie A | Premier | La Liga |
|---|--:|--:|--:|
| vittoria casa % | 41.2% | 44.1% | **45.3%** |
| pareggio % | 26.0% | **23.4%** | 26.5% |
| vittoria ospite % | 32.7% | 32.5% | **28.2%** |
| Over 2.5 % | 52.0% | **54.4%** | 47.1% |
| gol totali/partita | 2.72 | **2.84** | 2.58 |
| **vantaggio-casa γ=ln(casa/osp)** | 0.150 | 0.185 | **0.272** |
| Var/Media gol (casa) | 1.057 | **1.113** | 1.047 |
| **δ neopromosse (attacco)** | 0.229 | **0.329** | 0.218 |
| autocorr forze (t, t−1) | 0.736 | 0.736 | **0.818** |
| corr xG-gol | 0.607 | 0.635 | 0.621 |
| margine bookmaker | 4.9% | **4.3%** | 4.8% |
| edge mercato vs baseline | **0.1285** | 0.1121 | 0.0951 |

**Letture (le ipotesi per la modellazione).**
1. **γ (vantaggio-casa): La Liga 0.272 ≫ Premier 0.185 > Serie A 0.150.** La Liga
   è la più "casalinga" (45.3% casa, 28.2% ospite). MA γ è **auto-fittato** dal
   DC: il modello si adatta da solo, non è un iperparametro da ritarare.
2. **δ neopromosse: Premier 0.329 ≫ Serie A 0.229 ≈ Liga 0.218 — l'ipotesi §7 è
   VERIFICATA sui dati.** Le promosse inglesi sono nettamente più deboli (segnano
   1.02 vs media lega 1.42, subiscono 1.82). Il prior va ritarato: ~0.33 Premier,
   ~0.22 Liga. Copiare 0.23 sotto-correggerebbe la Premier.
3. **Draw-rate: Premier 23.4% (meno pareggi, la firma inglese)** vs 26% italiane/
   spagnole. La famiglia-pareggio (φ35) potrebbe avere meno da correggere.
4. **Stabilità delle rose: Liga autocorr 0.82 > 0.74** → memoria potenzialmente
   più lunga per la Liga (da verificare).
5. **Dispersione grezza: Premier più alta (Var/Media 1.11)** → gol più dispersi,
   coerente col θ_Premier più basso (meno sotto-dispersione) della Fase 53.
6. **Efficienza del mercato: Premier il più liquido** (margine 4.3%, il minore);
   l'edge del mercato sulla baseline è massimo in Serie A (0.128) e minimo in Liga
   (0.095). Ordina l'aspettativa di "battibilità" (Premier il più duro — Fase 53).

### Fase 56 — Tracer bullet: il DC Serie A, non tarato, dove atterra?

**Metodo §1.** Prima di ritarare, si prende il modello Serie A **così com'è**
(config ufficiale) e lo si fa girare walk-forward (6 stagioni) sulle due leghe.

| lega | modello | mercato | baseline | **gap 1X2** | CI95 |
|---|--:|--:|--:|--:|--:|
| Premier | 0.9831 | 0.9623 | 1.0653 | **+0.0207** | [+0.0138, +0.0274] |
| La Liga | 0.9843 | 0.9681 | 1.0669 | **+0.0162** | [+0.0102, +0.0223] |
| *(Serie A rif.)* | *0.9797* | *0.9632* | *1.0834* | *+0.0165* | *[+0.0106,+0.0225]* |

**Lezione.** La **struttura trasferisce**: il DC batte nettamente la baseline su
entrambe (0.98 vs 1.066, come in Serie A). Ma i **numeri no**: la Liga atterra al
gap della Serie A (+0.0162), la Premier a un gap più largo (+0.0207) — proprio
dove il mercato è più efficiente (EDA punto 6). Baseline onesta contro cui misurare
la ri-taratura (Fase 57).

### Fase 57 — Ri-taratura per lega: gli iperparametri sono piatti (di nuovo)

**Obiettivo.** §7: ri-tarare ogni iperparametro sui dati di ciascuna lega, una
leva alla volta (§1.2), tenendo le altre al default Serie A. γ non è un
iperparametro (il DC lo fitta). Griglie: δ {0, 0.15, 0.23, 0.33, 0.45}, emivita
{365, 730}, shrinkage {1.5, 3.0}.

**Risultato** (`scripts/_run_fase57_retune.py`; walk-forward 6 stagioni; 2 run
`source=fase57_retune`; Δ = log-loss 1X2 vs default Serie A):

| leva | Premier (gap; Δ vs def) | La Liga (gap; Δ vs def) |
|---|--:|--:|
| δ=0.23 (default) | +0.0207 | +0.0162 |
| δ=0.15 | +0.0208 (+0.0001) | +0.0162 (−0.0000) |
| **δ ottimo** | **0.33: +0.0207 (−0.0000)** | **0.15-0.23: +0.0162** |
| δ=0.45 | +0.0209 (+0.0002) | +0.0167 (+0.0005) |
| emivita 730 | +0.0264 (**+0.0057**) | +0.0178 (**+0.0015**) |
| shrinkage 3.0 | +0.0207 (−0.0000) | +0.0161 (−0.0001) |

**Lezione / cosa ne consegue.**
1. **Gli iperparametri sono PIATTI su entrambe le leghe** — tutti i Δ entro
   ±0.0005, nessun CI conclusivo… **con una eccezione, corretta dall'audit della
   Fase 92: l'EMIVITA non è piatta.** Il registro (`fase57_retune`) dà per la
   Premier `half_life_730 = +0.005686` con `p_better = 0.0001`, cioè **11 volte**
   il limite dichiarato e **conclusivo**, non «nessun CI conclusivo» (è il 27%
   del gap col mercato di quella lega); in Liga +0.001544. Tutti gli altri Δ sono
   effettivamente ≤0.000505. La conclusione operativa non cambia — l'emivita
   adottata resta 365g, che è la migliore — ma la frase «tutti i Δ entro ±0.0005»
   era falsa e nascondeva l'unico asse su cui la ri-taratura *conta*.
   Al netto di questo: le leve sono ortogonali e la config è già vicina all'ottimo. Il gap col mercato
   (Premier +0.0207, Liga +0.0162) **non si chiude ritarando**: è informazione,
   non cattiva calibrazione. La stessa conclusione della Serie A, confermata su
   due leghe indipendenti.
2. **Il δ punta dove la EDA prevedeva** — 0.33 è nominalmente il migliore in
   Premier (0.9830 vs 0.9831), 0.15-0.23 in Liga — ma il guadagno è nullo: le
   neopromosse sono poche partite (≈15% del totale) e lo shrinkage già le tira
   verso la media. Adottiamo comunque il δ **strutturalmente corretto** per lega
   (Premier 0.33, Liga 0.22), per motivazione e non per il numero — esattamente
   come la Serie A adottò δ=0.23 con CI non conclusivo (Fase 7/17).
3. **L'ipotesi "rose Liga più stabili → memoria più lunga" (EDA) è FALSA per il
   log-loss**: emivita 730 peggiora anche in Liga (+0.0015). L'autocorr 0.82 dice
   che le forze sono stabili, ma 365g le segue già bene; allungare aggiunge solo
   inerzia sulle poche squadre che cambiano. Lezione: una differenza descrittiva
   (autocorr) non implica una differenza di taratura ottimale.
4. **`LEAGUE_CONFIGS` aggiornato** (`src/config.py`): Premier e Liga con δ per
   lega, tutto il resto = Serie A (confermato ottimo). Aggiungere una lega è
   stata **configurazione, non codice** (§7 mantenuto).

**Sintesi delle Fasi 54-57.** Gli STESSI modelli reggono: DC + xG batte la
baseline, l'ordine di grandezza del gap è lo stesso, e la ri-taratura non sposta
nulla (tetto informativo universale). Le differenze tra leghe sono **strutturali
e auto-gestite** (γ fittato) o **piccole e motivate** (δ). La lezione della
Fase 53 (i bias sfruttabili sono idiosincratici della Serie A) più questa (i
modelli e il tetto sono universali) danno il quadro completo: **il modello è
trasferibile, l'edge no.**

### 📐 Il modello in dettaglio — perché la ri-taratura è piatta

Le formule sono quelle Serie A (nessuna nuova): prior δ sposta il bersaglio dello
shrinkage delle neopromosse (attacco −δ, difesa +δ, Fase 7); emivita = peso
`exp(−ln2·Δt/H)`; shrinkage = forza del pull verso la media. **Perché il δ non
paga in log-loss pur essendo "giusto":** il δ agisce solo sulle partite delle
neopromosse (≈3 squadre × 38 gare × 2 = ~228 gare/stagione su ~380, ma solo ~15%
hanno una neopromossa con storico assente all'inizio stagione, e l'effetto svanisce
appena arrivano dati). Su quelle poche partite δ=0.33 in Premier riduce l'errore
(le promosse inglesi sono davvero più deboli), ma diluito su 2280 partite il
guadagno annega nel rumore. È lo stesso motivo per cui in Serie A il δ era
"−0.0011, non concluso" (Fase 17): un effetto reale e localizzato, statisticamente
invisibile in aggregato. **Perché emivita 730 peggiora:** con `H=730` il peso di
una partita di 2 anni fa è `2^(−1)=0.5` contro `2^(−2)=0.25` a 365g — troppa
memoria su rose che cambiano ~25% l'anno (autocorr 0.74-0.82 ⇒ 18-26% di turnover
di forza), quindi il modello insegue tassi vecchi. 365g è il punto in cui il
compromesso bias-varianza è ottimo in tutte e tre le leghe.

**Riproducibilità.** `python scripts/build_league_snapshot.py` (snapshot) →
`_run_fase55_eda.py` · `_run_fase56_tracer.py` · `_run_fase57_retune.py`.

### 📐 Il modello in dettaglio — le formule dell'EDA e perché i numeri

**Vantaggio-casa aggregato** `γ = ln(ḡ_casa / ḡ_ospite)` (medie dei gol): è la
versione "a lega" del parametro home_advantage che il DC stima per partita
(`λ = exp(att_h + dif_a + γ)`, dixon_coles.py:656). γ_Liga = ln(1.466/1.117) =
0.272; γ_SerieA = ln(1.461/1.258) = 0.150. La differenza (0.12) è enorme in
scala-gol (≈ +13% di tasso-casa in più in Liga) — ed è la ragione per cui la Liga
ha il 45% di vittorie casalinghe. Il DC la cattura da solo (home_advantage fittato
nella MLE), quindi NON entra nella config.

**Prior neopromosse** `δ = ln(ḡ_lega / ḡ_promosse)` (Fase 7): ḡ_lega = gol per
squadra per gara (1.360 Serie A, 1.419 Premier, 1.291 Liga); ḡ_promosse = gol
segnati per gara dalle sole neopromosse. δ_Premier = ln(1.419/1.022) = 0.329:
le promosse inglesi segnano il 33% in meno della media, contro il 23% in Serie A —
il "gap di categoria" inglese è più marcato (la Championship è più distante dalla
Premier di quanto la Serie B lo sia dalla A). È esattamente la previsione del §7,
ora un numero, non un'intuizione.

**Dispersione** Var/Media dei gol: 1 = Poisson. Il valore >1 misura
l'eterogeneità tra squadre (una lega con più squattrini e più corazzate ha code
più pesanti). Premier 1.11 > Liga/Serie A 1.05: la Premier ha più varianza di
forza tra i club — coerente col fatto che il suo mercato-gol condizionato è meno
sotto-disperso (Fase 53: θ_Premier 1.07 < θ_SerieA 1.21).

---

## Fase 58 — Audit dati: overround impossibile nella quota "Avg" (bug, non modello)

**Obiettivo.** Su richiesta dell'utente, un audit mirato dei dati a disposizione
(i tre snapshot `data/{serie_a,premier_league,la_liga}_matches.csv`) per trovare
e sistemare problemi reali, distinti dai limiti già documentati e accettati
(es. copertura `squad_value` — §"Limite onesto" sopra — che è una scelta, non un
bug).

**Ragionamento/metodo.** Controlli di integrità sui tre snapshot: coerenza
`result` vs gol, duplicati, continuità date, copertura NaN per colonna/stagione,
e — il controllo che ha trovato il problema — l'**overround implicito 1X2**
(`Σ 1/quota`). Un bookmaker vero ha SEMPRE overround > 1 (il margine è il suo
guadagno): un valore < 1 implica un arbitraggio garantito, impossibile su una
linea reale — quindi è un sintomo di dato corrotto, non di un mercato efficiente.

**Scoperta.** Due righe su 10260 (0.02%) violano il vincolo:
- **La Liga, chiusura**: Mallorca-Barcelona (2025-08-16) — `AvgCH/AvgCD/AvgCA`
  = 8.70/5.79/1.56 → overround **0.9287**. Nel CSV grezzo la colonna `MaxCA`
  (massimo tra i book) vale **5.4**, mentre ogni singolo book quota l'ospite
  1.29-1.39: un book anomalo incluso nella media della fonte (football-data.co.uk)
  gonfia `AvgCA` ben oltre ciò che i book reali quotano.
- **Serie A, apertura**: Genoa-Inter (2025-12-14) — `AvgH/AvgD/AvgA` =
  6.37/4.20/1.67 → overround **0.9939** (stesso pattern: `MaxA`=4.0 contro
  B365A=1.5).

In entrambi i casi il livello di preferenza SUCCESSIVO (`B365CH/CD/CA` per la
Liga, `B365H/D/A` per la Serie A) da' un overround sano (1.056 e 1.059).

**Alternative considerate.** (a) Correggere a mano il numero — **scartata**:
il progetto non inventa/aggiusta mai un dato (principio cardine, vedi §"niente
imputazioni" sopra); non sappiamo QUALE quota tra le tre sia quella sbagliata,
solo che la combinazione è impossibile. (b) Lasciare NaN la riga — perde
informazione quando un livello successivo valido esiste. (c) **Ripiegare in
BLOCCO** (mai un solo lato) sul livello di preferenza successivo quando
l'overround del livello preferito è impossibile — **scelta adottata**: usa
comunque un prezzo di mercato reale (non inventato), preserva la coerenza
interna del book (stessa fonte per i tre esiti), e degrada a NaN solo se pure
il ripiego fallisce (mai successo nei dati attuali).

**Correzione.** `src/data/loader.py`: `_pick_market_odds` sceglie ora le quote
di un intero mercato (1X2 o O/U) per riga invece che colonna per colonna,
validando l'overround prima di accettare un livello e ritentando col successivo
se impossibile (`_ODDS_MARKET_GROUPS`); `_open_odds_market` applica la stessa
logica alle quote di apertura, senza toccare il mascheramento esistente (open
resta NaN dove la chiusura è essa stessa un fallback pre-match, invariato dalla
Fase 14/15). Rigenerati offline (nessuna rete): `la_liga_matches.csv` e
`premier_league_matches.csv` via `build_league_snapshot.py` (bundle locali),
`serie_a_matches.csv` via `_restore_raw_cache.py` + `build_database.py
--open-odds` (CSV grezzi versionati). Diff verificato: **esattamente le 2 righe
sopra cambiano**, nessun'altra — l'impronta dati (`data_fingerprint`, calcolata
solo su date/squadre/gol) resta **invariata**: `8483944342fc8b15`, quindi nessun
risultato già pubblicato nel registro (Fasi 1-57) è invalidato o va ricontrollato.

**Risultato/impatto.** Impatto statistico nullo per costruzione (2 righe su
oltre 10mila, mai usate per stimare il modello — le quote servono solo da
benchmark in valutazione): nessuna riga di `experiments/runs.jsonl` cambia.
Il valore del fix è nella **correttezza del dato pubblicato** e nella guardia
per il futuro.

**Lezione / cosa ne consegue.** Un controllo per-colonna (`valore > 1.0`) non
basta a garantire un book coerente: serve un controllo di **gruppo** (l'intero
mercato) perché il vincolo economico (niente arbitraggio) è sulla combinazione,
non sul singolo numero. Aggiunti test di non-regressione: 2 unitari
(`tests/test_open_odds.py`, con e senza overround impossibile, dati sintetici
che riproducono il caso reale) + 1 parametrizzato su tutte e tre le leghe
(`tests/test_league_snapshots.py::test_quote_1x2_senza_overround_impossibile`,
chiusura e apertura) che blocca ogni futura corruzione della stessa natura,
in qualunque lega.

### 📐 Il modello in dettaglio

Nessuna matematica nuova sul motore di stima — questa è una fase di **integrità
dati**, non di modellazione. L'unica formula coinvolta è la definizione stessa
di overround (verificata contro `_pick_market_odds` in `loader.py`):

```
overround = Σ_i 1/quota_i   (i = esiti del mercato: 1X2 o O/U)
```

`overround > 1` per costruzione economica: `1/quota_i` è la probabilità
implicita SENZA rimuovere il margine (devig), e la somma delle probabilità
implicite vigorish-incluse eccede 1 esattamente della quota di margine del
book (tipicamente 3-8% nei dati, vedi Fase 55 EDA: margine medio 4.3-4.9%
per lega). Un valore < 1 non è "un margine negativo piccolo": è matematicamente
un arbitraggio a somma positiva garantita per chi punta su tutti e tre gli
esiti contemporaneamente — impossibile per un book che vuole guadagnare dal
margine, quindi certamente un errore di aggregazione a monte (nella fonte),
non un fenomeno di mercato.

**Riproducibilità.** `python scripts/_restore_raw_cache.py &&
python scripts/build_database.py --open-odds` (Serie A) e
`python scripts/build_league_snapshot.py premier_league la_liga` (bundle
locali, nessuna rete) rigenerano gli snapshot con il fix; `pytest` verde
(106 test, +5 da questa fase).

---

## Fase 59 — Congestione vera anche per Premier League e La Liga (colmato il gap dati)

**Obiettivo.** Dopo l'audit dati (Fase 58) l'utente chiede di colmare, a partire
dalle coppe, il gap di schema tra Serie A (38 colonne) e Premier/Liga (28): le
10 colonne mancanti sono `squad_value`/`absences` (Transfermarkt, bloccato: nessun
mirror/bundle raggiungibile, vedi risposta precedente) e `rest_days_full`/
`midweek_europe` (calendario di club completo, Fase 4e) — quest'ultimo
recuperabile perche' `fixtures.py` era scritto solo per l'Italia ma la fonte
(openfootball) e' generale.

**Ragionamento.** Verificata la raggiungibilita' reale (non assunta): il mirror
`raw.githubusercontent.com/openfootball/*` risponde 200 (a differenza di
football-data/Understat/Transfermarkt, tutti bloccati). Cercati i repo/nomi-file
domestici per le altre due leghe (nessuna API GitHub generica disponibile
dall'ambiente, solo raw-file diretti, quindi ricerca per tentativi mirati):
`openfootball/england` ha `facup.txt` (FA Cup) e `eflcup.txt` (EFL Cup), stesso
formato testuale della Coppa Italia; `openfootball/espana` ha `cup.txt` (Copa
del Rey), **stessa finestra di copertura della Coppa Italia** (2020-21->2024-25,
mancano 2017-20 e 2025-26 in corso) — coincidenza che suggerisce lo stesso
processo di raccolta del dataset per le coppe "minori" di tutte le leghe. Le
competizioni UEFA (Champions/Europa/Conference) erano gia' scaricate per la
Serie A dallo STESSO repo `champions-league`, che e' europeo (non italiano):
bastava filtrare per codice paese "ENG"/"ESP" invece di "ITA".

**Bug trovato e corretto in corsa (non e' un'estensione, e' un fix).**
`parse_europe` filtrava **al proprio interno** solo le righe con una squadra
"ITA", PRIMA che `_uefa_team_rows` applicasse il filtro-paese generalizzato:
per club senza mai un'italiana in un turno (es. Manchester City-RB Leipzig-
Paris Saint-Germain-Club Brugge, girone 2021-22 Champions League: NESSUNA
squadra italiana) il filtro azzerava silenziosamente OGNI partita, anche se il
file le conteneva tutte. Scoperto confrontando il conteggio grezzo (grep
`(ENG)` sul file: 43 occorrenze) con l'output della pipeline (8 righe): un
divario troppo grande per essere rumore. Corretto passando ``country_code``
anche a `parse_europe` (prima veniva generalizzato solo in `_uefa_team_rows`).
**Lezione:** un conteggio-sanity (grep sul grezzo vs righe prodotte) ha
catturato un bug che i soli test unitari (che usano frammenti sintetici SEMPRE
con una italiana) non potevano vedere.

**Alias mancanti (stesso metodo della Fase 54/4e): estratti TUTTI i nomi
ENG/ESP dalle competizioni europee e dalle coppe nazionali 2017-18->2025-26 e
confrontati coi 32+32 nomi canonici degli snapshot, iterando fino a ZERO
club non agganciati** (non assunto: verificato ad ogni round). ~35 nuove voci
in `TEAM_ALIASES` (varianti "FC"/"CF"/nome-lungo usate da openfootball, es.
"Manchester City FC"->"Man City", "FC Barcelona"->"Barcelona", "Club Atlético
de Madrid"->"Ath Madrid" — una TERZA variante dello stesso club, oltre alle due
gia' note da Understat).

**Scelta implementativa.** Generalizzato `src/data/fixtures.py` (e
`src/data/sources.py`) da Serie-A-only a multi-lega, con retrocompatibilita'
totale: ogni funzione accetta un parametro opzionale (``league_key``/
``country_code``/``own_competition``) che DEFAULT al comportamento Serie A
esistente (stesso path, stessi nomi-funzione/test usati dai test storici).
Nuova config in `sources.py`: `OPENFOOTBALL_DOMESTIC_REPO`,
`DOMESTIC_CUP_COMPETITIONS` (Premier: facup+eflcup; Liga: cup==Copa del Rey;
Serie A: alias dello storico `ITALY_CUP_COMPETITIONS`), `UEFA_COUNTRY_CODE`.
Nuovo file `data/club_fixtures_{premier_league,la_liga}.csv` (Serie A mantiene
il nome storico senza suffisso lega). `scripts/build_league_snapshot.py
--fixtures [lega...]` assembla il calendario e aggiorna lo snapshot, speculare
a `build_database.py --fixtures` per la Serie A.

**Risultato.**

| | Premier League | La Liga | *(Serie A, rif.)* |
|---|--:|--:|--:|
| partite extra (coppe/Europa), 9 stagioni | 1495 | 829 | *836* |
| copertura Champions League | tutte e 9 | tutte e 9 | *tutte e 9* |
| copertura Europa League | dal 2020-21 | dal 2020-21 | *dal 2020-21* |
| copertura Conference League | dal 2021-22 | dal 2021-22 | *dal 2021-22* |
| copertura coppa/e nazionale/i | FA Cup+EFL Cup 2018-19->2024-25 | Copa del Rey 2020-21->2024-25 | *Coppa Italia 2020-21->2024-25* |
| copertura `rest_days_full` (entrambe le squadre) | 99.5% | 99.4% | *99.6%* |
| club NON agganciati (dopo gli alias) | 0 | 0 | *0* |

Schema ora a 32/38 colonne per Premier/Liga (mancano solo le 6
`squad_value`/`absences`, bloccate su Transfermarkt — vedi risposta precedente).
`pytest`: 114/114 verdi (+8 test parametrizzati sulle due leghe, stesse
invarianti della Serie A: `rest_full <= rest solo-lega`, cap 14, nessun club
orfano, schema competizioni noto).

**Onesta' sui limiti.** Non e' stata (ancora) verificata l'UTILITA' di
`rest_full`/`midweek_europe` per Premier/Liga: la Fase 4e-bis l'aveva trovata
neutra in Serie A (−0.0004, rumore); lo stesso test andrebbe rifatto qui prima
di eventualmente attivarla (resta covariata off-di-default, come in Serie A).
Le coppe minori (EFL Cup, Copa del Rey) sono giocate spesso con formazioni
rimaneggiate: la loro presenza in `midweek_europe` puo' quindi essere un
segnale piu' debole della sola Champions/Europa (il proxy tratta ogni
competizione extra allo stesso modo, come gia' per la Coppa Italia in Serie A).

### 📐 Il modello in dettaglio

Nessuna formula nuova: `rest_days_full`/`midweek_europe` sono ESATTAMENTE le
definizioni della Fase 4e (`fixtures.add_rest_days_full`, invariate), applicate
a un calendario di club piu' ampio. L'unico parametro nuovo per-lega e' il
codice paese UEFA usato per filtrare i club nelle competizioni europee:

```
country_code = UEFA_COUNTRY_CODE[league_key]   # "ITA" / "ENG" / "ESP"
riga tenuta  <=>  home_cc == country_code  OR  away_cc == country_code
```

non e' un iperparametro stimato: e' un dato anagrafico (il codice-paese ISO/UEFA
a 3 lettere usato dal dataset openfootball), verificato per ogni lega
grep-ando il file grezzo (`(ENG)`, `(ESP)`) prima di fidarsene nel codice.

**Riproducibilita'.** `python scripts/build_league_snapshot.py --fixtures
premier_league la_liga` (rete richiesta al primo download, poi cache offline
in `data/raw/fixtures_*`); `pytest tests/test_fixtures.py -q`.

---

## Fase 60 — Valore rosa e assenze anche per Premier League e La Liga

**Obiettivo.** Le ultime 6 colonne mancanti rispetto alla Serie A
(`squad_value` × 2, `absences` × 4, Fase 4a). Nella risposta precedente
all'utente era stato detto "bloccato: Transfermarkt non e' raggiungibile" —
**affermazione MAI verificata empiricamente in questa sessione**, solo dedotta
dai commenti nel codice ("anche transfermarkt.com e' bloccato dall'ambiente
cloud", `sources.py`). Testato direttamente: il mirror USATO DAL PROGETTO
(`raw.githubusercontent.com/salimt/football-datasets`, non transfermarkt.com)
risponde **200** su tutte e 4 le tabelle (~106MB totali) — e' `transfermarkt.com`
diretto ad essere bloccato, non il mirror GitHub, esattamente come per
openfootball (Fase 59) e a differenza del mirror football-data/Understat
(quello sì sparito, 404 verificato). **Lezione ribadita (§ metodo, principio 3):
mai dedurre una lacuna dati da un commento — si verifica.**

**Il problema restante:** il mirror Understat PER-STAGIONE (da cui vengono le
rose/minutaggi dei giocatori, servono a `transfermarkt.team_season_values` per
pesare la copertura) e' invece sparito per davvero (stesso repo morto della
Fase 14) — quindi non scaricabile per Premier/Liga. Soluzione: le rose vengono
dai bundle Understat GIA' caricati in `files/` (Fase 54), che contengono la
sezione `players` con lo stesso identico schema (minuti, ruolo, nome) che
`understat.season_players` otterrebbe da rete.

**Scelta implementativa.** `understat.season_players` scisso in
`parse_season_players` (pura, su dict gia' caricato) + `season_players`
(fetch+parse) — stesso pattern gia' usato per `parse_season_xg`/`season_xg`
(Fase 54). `transfermarkt.team_season_values`/`add_squad_values`/`add_absences`
accettano ora un parametro opzionale `squads`: se fornito, salta il download
Understat e usa quelle rose (default `None` = comportamento invariato per la
Serie A). `scripts/build_league_snapshot.py --enrich [lega...]` costruisce le
rose dal bundle e chiama le funzioni Transfermarkt (rete SOLO per
valutazioni/infortuni, cache offline dopo il primo download).

**Risultato.**

| | Premier League | La Liga | *(Serie A, rif.)* |
|---|--:|--:|--:|
| copertura `squad_value` (entrambi i lati) | **95.6%** | **58.3%** | *~78%* (Fase 4a) |
| copertura minima di stagione | 90% (5 stagioni sotto soglia 85%) | 41% (2020-21) | *60%* (Fase 4c) |
| aggancio nomi giocatore (per identita') | 91.7%+ | 91.7% exact/filtered/tiebreak | *n/d, mai misurato a parte* |

**La Liga ha una copertura sensibilmente piu' bassa** delle altre due leghe,
Real Madrid 2025-26 incluso (84%, appena sotto soglia). Diagnosticato PRIMA di
accettarlo come limite onesto (non per pigrizia): il matching per NOME e'
buono (91.7% agganciato su 1974 giocatori: 1403 esatti + 174 filtrati + 109
per-picco-valutazione + resto fuzzy/token, solo 163 mai agganciati), e dei
1811 agganciati il 94.9% ha una valutazione utilizzabile. Il problema e' che
il ~13% di giocatori senza numero utilizzabile (nome non agganciato O
agganciato ma privo di serie di valutazioni) e' sbilanciato verso i TITOLARI
(la soglia pesa sui MINUTI, non sul conteggio giocatori): nomi brevi/nickname
sudamericani-spagnoli (es. "Vinicius", "Rodrygo") sono strutturalmente piu'
difficili da agganciare univocamente o mancano piu' spesso nel datalake
rispetto ai nomi europei — stessa causa radice della Fase 4a (Lazio/
Milinkovic-Savic: profili senza serie di valutazioni), qui piu' diffusa.
**Nessuna imputazione**: la politica resta NaN dichiarato sotto l'85%,
verificata a mano di essere una lacuna di DATI (datalake incompleto) e non di
CODICE (matching che fallisce silenziosamente).

Schema ora **38/38 colonne, IDENTICO a quello della Serie A**, per tutte e tre
le leghe. `pytest`: 118/118 verdi (+4 test parametrizzati, soglie di copertura
onesta per-lega esplicite: 85% Premier, 35% Liga — quest'ultima piu' bassa e
DOCUMENTATA, non un numero a caso).

**Onesta' sui limiti.** Come per `rest_full` (Fase 59) e per la Serie A stessa
(Fase 4c/11), **`squad_value`/`absences` sono gia' state provate e bocciate**
come covariate del modello (peggiorano il log-loss). Costruire queste colonne
per Premier/Liga completa lo SCHEMA DATI (simmetria/riproducibilita' tra
leghe) ma non e' atteso alcun guadagno predittivo diretto — coerente con la
lezione della Fase 33 ("i dati interni sono completamente esplorati").

### 📐 Il modello in dettaglio

Nessuna formula nuova: `squad_value`/`absences` sono ESATTAMENTE le definizioni
della Fase 4a (`transfermarkt.team_season_values`/`add_absences`, invariate),
applicate a rose Understat di provenienza diversa (bundle anziche' rete). La
soglia di pubblicazione resta `MIN_COVERAGE = 0.85` (stessa costante, stesso
significato: quota dei MINUTI stagionali coperta da giocatori agganciati e
valutati) — non ritarata per lega: e' una soglia di ONESTA' del dato
("non pubblicare un numero che rappresenta meno dell'85% della rosa reale"),
non un iperparametro del modello, quindi non ha senso allentarla per far
"tornare" la copertura della Liga.

**Riproducibilita'.** `python scripts/build_league_snapshot.py --enrich
premier_league la_liga` (rete per Transfermarkt, ~106MB al primo download,
poi cache offline in `data/raw/transfermarkt_*.csv`); `pytest
tests/test_data_enrichment.py -q`.

---

## Fase 61 — Quote di apertura 2017-19: la chiusura di Pinnacle era ignorata

**Obiettivo.** L'utente chiede: dove le colonne quota NON distinguono apertura e
chiusura, capire se quella che abbiamo e' l'una o l'altra, e — se e' la chiusura
— recuperare l'apertura; per TUTTE le stagioni e TUTTE le leghe. Le quote di
apertura sono metodologicamente centrali (tutta la Fase 14 sul Closing Line
Value ci gira sopra), e mancavano al ~22% delle partite (le stagioni 2017-18 e
2018-19, su tutte e 3 le leghe).

**Ragionamento / la scoperta.** Nella risposta precedente all'utente avevo
liquidato quel 22% come "limite di design irrecuperabile: quelle stagioni hanno
una sola istantanea di quote". **Sbagliato — e verificato guardando i CSV grezzi
colonna per colonna** invece di fidarmi del commento del loader ("nelle stagioni
< 2019-20 le *_open sono interamente NaN"). Le prime 2 stagioni hanno DUE
istantanee Pinnacle distinte: `PSH/PSD/PSA` (apertura) e `PSCH/PSCD/PSCA`
(chiusura — il suffisso `C` = Closing), presenti al 100% e diverse nel 95-98%
delle righe. Il loader cercava la chiusura solo in `AvgCH`/`B365CH` (assenti in
quelle stagioni) e **ignorava del tutto Pinnacle**: cosi' (1) usava la pre-match
come se fosse chiusura, e (2) mascherava l'apertura a NaN (senza colonna `*C*`
la maschera scatta). Pinnacle e' per giunta il book di RIFERIMENTO per
l'efficienza (margini piu' bassi), quindi non e' un ripiego di serie B.

**La tabella completa (richiesta esplicita: tutte le stagioni × leghe).** Con la
politica nuova, ESITO 1X2 per (lega, stagione):

| | 2017-18 · 2018-19 | 2019-20 → 2025-26 |
|---|---|---|
| Serie A / Premier / Liga | close **Pinnacle**, open **Pinnacle** (era: close pre-match, open NaN) | close/open **media** (invariato) |

Le uniche 6 celle (3 leghe × 2 stagioni) prima "non separabili" ora lo sono; le
21 celle recenti restano identiche.

**Scelta implementativa (una leva alla volta, §1.2).** In `_ODDS_PREFERENCE`
(chiusura) inserito `PSCH/PSCD/PSCA` **dopo** `AvgC*`/`B365C*` ma **prima** dei
fallback pre-match: le stagioni 2019-20+ (che hanno `AvgC*` al 100%, verificato)
restano bit-per-bit identiche, le prime 2 prendono la chiusura Pinnacle. In
`_ODDS_PREFERENCE_OPEN` (apertura) inserito `PSH/PSD/PSA` **dopo** `AvgH` (100%
nelle recenti → invariate) ma **prima** di `BbAvH`: le prime 2 aprono con la
pre-match di Pinnacle, lo STESSO book della loro chiusura → CLV pulito
Pinnacle→Pinnacle, non misto. Nuova `loader.refresh_odds(matches,
raw_by_season)` (generalizza `add_open_odds` della Fase 14): ricalcola le 10
colonne quota da grezze e le re-inietta nello snapshot **senza toccare
xG/rose/congestione/gol**, con lo stesso controllo d'integrita' sui gol; le
grezze sono iniettate dal chiamante (data/raw per la Serie A, bundle per
Premier/Liga), zero rete. Entry-point: `build_database.py --refresh-odds` (Serie
A) e `build_league_snapshot.py --refresh-odds` (Premier/Liga).

**Risultato.**

| | prima | dopo |
|---|--:|--:|
| apertura 1X2 recuperate (3 leghe × 2 stagioni) | 0 | **2279** (99.9%) |
| chiusura 1718/1819 | pre-match spacciata | **Pinnacle closing vera** (margine ~2.5%) |
| stagioni 2019-20+ | — | **invariate** (diff bit-per-bit = 0) |
| colonne non-quota | — | **invariate** (diff = 0, verificato) |
| impronta dati | `8483944342fc8b15` | **invariata** (quote non entrano nel fingerprint) |

Diff chirurgico verificato: cambiano SOLO le 10 colonne quota, SOLO nelle
stagioni 1718/1819, su tutte e 3 le leghe; overround sempre ≥ 1 (margine
Pinnacle ~2.2-2.5%, piu' basso della media aggregata ~4.9% — coerente); apertura
≠ chiusura nel 96%. `pytest`: 121/121 (+3: chiusura+apertura Pinnacle sintetica,
non-regressione sulle stagioni con media, copertura reale 1718/1819). L'O/U di
quelle 2 stagioni resta senza apertura (Pinnacle non pubblica un O/U di
chiusura, nessun `PSC>2.5` → manca la colonna `*C*` che la sbloccherebbe):
limite onesto documentato, non un buco silenzioso.

**Onesta' sull'impatto nelle analisi.** Le prime 2 stagioni sono soprattutto
TRAINING (il test ufficiale e' 2020-21→2025-26); 1819 e' usata come test solo
nelle finestre estese (Fasi 19/31, prior/stakes). Le run gia' in `runs.jsonl`
sono congelate e NON cambiano; ri-eseguendole, le metriche di MERCATO per 1819
migliorerebbero (chiusura vera Pinnacle invece della pre-match), il che
semmai RAFFORZA le conclusioni (nessuna cambia). Ora, per la prima volta,
esiste un CLV misurabile su 1718/1819 — la Fase 14 (CLV negativo) potra' essere
ri-testata su 2 stagioni in piu' se servira'.

### 📐 Il modello in dettaglio

Nessuna matematica di modello — e' politica di selezione dei dati. L'unico
"numero" e' l'ordinamento delle liste di preferenza, e la sua correttezza si
verifica sui dati, non a memoria:

```
_ODDS_PREFERENCE["odds_home"]      = [AvgCH, B365CH, PSCH, AvgH, BbAvH, B365H]
_ODDS_PREFERENCE_OPEN["odds_home_open"] = [AvgH, PSH, BbAvH, B365H]
```

- `PSCH` dopo `B365CH`: se una stagione ha la chiusura aggregata la usa (nessun
  cambiamento per il 2019-20+, dove `AvgCH` copre il 100%); solo dove manca
  (2017-19) scende su Pinnacle. **Perche' non prima:** metterlo prima
  cambierebbe la chiusura di TUTTE le stagioni da "media di ~10 book" a
  "solo Pinnacle", alterando le metriche gia' pubblicate — non voluto.
- `PSH` dopo `AvgH`: idem sul lato apertura. `AvgH` copre il 100% delle recenti
  (verificato su tutte e 3 le leghe), quindi `PSH` agisce solo sulle prime 2.
- La maschera dell'apertura (Fase 14) e' invariata nella logica: si sblocca da
  sola perche' ora `close_only` include `PSCH`, che nelle prime 2 stagioni e'
  valorizzato → la condizione "la chiusura viene da una colonna `*C*`" e' vera.

**Riproducibilita'.** `python scripts/_restore_raw_cache.py && python
scripts/build_database.py --refresh-odds` (Serie A) e `python
scripts/build_league_snapshot.py --refresh-odds premier_league la_liga`
(bundle, zero rete); `pytest tests/test_open_odds.py -q`.

---

## Fase 62 — Ricostruire la chiusura O/U mancante (2017-19) coi nostri modelli?

**Obiettivo.** Dopo la Fase 61 l'unico buco e' l'O/U 2.5 del 2017-19: una sola
linea (BbAv pre-match, timing "apertura") mentre l'1X2 ha entrambe (Pinnacle).
L'utente chiede: coi modelli che abbiamo, si puo' RICAVARE la linea mancante?
E di validare l'idea con un backtest sulle stagioni dove abbiamo gia' tutto.

**Ipotesi/disegno (S1.2, una cosa alla volta; S1.3, versione economica).**
Cio' che muove la chiusura O/U rispetto all'apertura e' informazione arrivata
tra venerdi' e il calcio d'inizio; parte di quella STESSA informazione muove
anche l'1X2, che nel 2017-19 abbiamo in entrambe le versioni. Il motore
market-implied (Fase 26) sa tradurre un 1X2 in tassi di gol (lambda, mu) e
quindi in un O/U: puo' quindi misurare lo shift O/U implicato dal movimento
1X2. Backtest sulle 21 (lega, stagione) 2019-20+ con TUTTE e 4 le linee:
si finge di non avere la chiusura O/U, la si stima, la si confronta con quella
vera. Candidati: M0 identita' (stima=apertura); M1 shift del motore applicato
all'apertura vera (il bias d'inversione si cancella nella differenza); M2
inversione assoluta su (1X2_close, OU_open); M3 ricalibrazione lineare in
logit SENZA 1X2 (walk-forward per lega — separa "affinamento sistematico" da
"notizie"); M4 = M3 + lo shift del motore come feature (walk-forward).

**Risultato** (`scripts/_run_fase62_ou_close_est.py`; n=2658-2660 per lega;
B=10000; 3 run `source=fase62_ou_close_est`):

| | Serie A | Premier | La Liga |
|---|--:|--:|--:|
| movimento reale open→close (media assoluta) | 0.0212 | 0.0202 | 0.0217 |
| M4: MAE vs chiusura vera (M0=movimento) | **0.0142** (−33%) | **0.0127** (−37%) | **0.0128** (−41%) |
| M4: corr / beta del movimento previsto | 0.64 / 0.80 | 0.77 / 1.04 | 0.80 / 1.08 |
| M3 (recal senza 1X2): corr movimento | 0.03 | −0.00 | 0.13 |
| log-loss: close vero − open | −0.0018 (ns) | −0.0007 (ns) | **−0.0026 ✓CI** |
| log-loss: M4 − open | +0.0011 (ns) | −0.0010 (ns) | **−0.0024 ✓CI** |
| log-loss: M4 − close vero | +0.0028 (ns) | −0.0001 (ns) | +0.0003 (ns) |

**Lezione / cosa ne consegue.**
1. **La chiusura O/U e' parzialmente ricostruibile, e la parte prevedibile del
   suo movimento sta TUTTA nel movimento 1X2** mappato attraverso la matrice
   DC: la ricalibrazione pura (M3) non cattura nulla (corr ~0 su 3 leghe),
   lo shift del motore cattura il 64-80% di correlazione col movimento vero.
   Interessante il contrasto con la Fase 52-quinquies: sull'1X2 il movimento
   open→close era quasi tutto ricalibrazione sistematica; sull'O/U e' quasi
   tutto informazione condivisa con l'1X2.
2. **Lo shift grezzo del motore e' giusto in direzione ma 4-10 volte troppo
   piccolo** (beta 4.5-9.8): l'inversione tiene l'O/U d'apertura come vincolo,
   quindi i tassi impliciti si muovono poco. La regressione M4 lo riscala
   (beta 0.8-1.1) — serve il fit, il motore da solo non basta.
3. **Il tetto dell'esercizio e' basso**: la chiusura VERA vale solo
   −0.0007…−0.0026 di log-loss rispetto all'apertura (conclusivo solo in
   Liga). Dove vale qualcosa, M4 la recupera quasi tutta (Liga −0.0024 ✓CI,
   indistinguibile dal close vero; Premier idem, −0.0001 vs close); in Serie A
   il guadagno annega nel rumore.
4. **Decisione: NON si scrive la stima negli snapshot.** Una chiusura
   ricostruita e' output di modello, non un prezzo di mercato: metterla nelle
   colonne quota violerebbe la regola "mai un numero inventato" (S2-bis/3) e
   contaminerebbe ogni analisi futura in modo silenzioso. Lo script resta come
   TOOL: se un'analisi sul 2017-19 avra' bisogno di un benchmark di chiusura
   O/U "equo", potra' generarlo dichiarandolo esplicitamente come stima.
   Caveat dichiarati: per applicarlo al 2017-19 i coefficienti andrebbero
   fittati sulle stagioni SUCCESSIVE (unico dato disponibile — accettabile per
   un benchmark storico, non per una predizione); e li' le linee sono Pinnacle
   /BbAv, non le medie Avg usate nel backtest.

### 📐 Il modello in dettaglio

Devig moltiplicativo (fonte unica, `metrics.devig_binary`): `p_over =
(1/q_over) / (1/q_over + 1/q_under)`. Lo shift del motore (M1), verificato
contro `implied_lambda_mu`/`score_matrix` (market_implied.py:109/66):

```
(lam_o, mu_o) = argmin  (qH-pH_o)^2 + (qD-pD_o)^2 + (qA-pA_o)^2 + (qO-pOU_o)^2
(lam_c, mu_c) = stesso argmin con 1X2 di CHIUSURA e lo STESSO pOU_o
shift = Over2.5(lam_c, mu_c) - Over2.5(lam_o, mu_o)        [rho = -0.06, Fase 26]
M1: p_hat = p_open + shift
M4: logit(p_hat) = a + b*logit(p_open) + c*[logit(p_open+shift) - logit(p_open)]
    (a, b, c) OLS walk-forward per lega (train = stagioni precedenti, test 2021+)
```

**Perche' beta(M1) = 4.5-9.8 e non 1**: nell'inversione il termine
`(qO - pOU_o)^2` ancora i tassi totali all'O/U d'apertura; il movimento 1X2
riesce a spostare soprattutto il TILT (lam-mu), quasi niente il totale
(lam+mu), quindi lo shift O/U esce sistematicamente compresso di ~1/beta
(0.10-0.22). Il coefficiente `c` di M4 impara esattamente questo fattore di
riscala (beta finale 0.80-1.08 ≈ 1, corretto). **Perche' rho=-0.06**: la
costante adottata dalla Fase 24/26 per la matrice market-implied; nella
DIFFERENZA q_c - q_o il suo effetto si cancella quasi del tutto (M1 vs M2:
stessa direzione, M2 porta il bias assoluto). **Numeri ricalcolabili** da
`runs.jsonl` (3 run `fase62_ou_close_est`, config completa: rho, stagioni,
finestre walk-forward, B, seed).

**Riproducibilita'.** `python scripts/_run_fase62_ou_close_est.py` (offline,
~50s; bootstrap B=10000, seed 62).

---

## Fase 62-bis — La stima migliorata, pubblicata come STIMA (e il catalogo dati)

**Obiettivo.** L'utente ribalta (legittimamente) la decisione di default della
Fase 62: la stima della chiusura O/U 2017-19 GLI SERVE — purche' sia
"scritto chiaramente che si tratta di stime e che non bisogna farci troppo
affidamento". Tre richieste: (1) migliorare la stima il piu' possibile;
(2) pubblicarla marcata come stima; (3) un documento che spieghi TUTTI i dati
a disposizione, stime incluse. Piu' un promemoria: in futuro si stimeranno
cosi' anche altri dati mancanti.

**(1) Il bakeoff degli estimatori** (`scripts/_run_fase62bis_estimator.py`,
stesso protocollo/righe/bootstrap della Fase 62, 1 run
`source=fase62bis_estimator`). Candidati sopra M4: fit POOLED cross-lega
(la mappa 1X2→O/U e' fisica della matrice, non della lega) e il movimento 1X2
GREZZO (Δlogit di H/X/2) al posto dello shift del motore:

| candidato (walk-forward 2021+) | MAE medio 3 leghe | corr movimento |
|---|--:|--:|
| M4 (riferimento Fase 62: recal + shift motore) | 0.0132 | 0.64-0.80 |
| M4 pooled | 0.0131 | — |
| **E3 = logit(OU_open) + ΔlogitH + ΔlogitD + ΔlogitA** | 0.0118 | 0.73-0.86 |
| **E3 pooled** ← **SCELTO** | **0.0117** | 0.75-0.86 |
| E4 = E3 + shift motore (pooled) | 0.0119 | — |

Tre lezioni: (a) il movimento 1X2 grezzo **batte** lo shift del motore — i
dati imparano una mappa migliore di quella imposta dalla matrice DC (che
comprime il segnale, Fase 62 §2); (b) una volta dentro il movimento grezzo,
lo shift del motore **non aggiunge nulla** (E4 ≈ E3): l'informazione e' la
stessa; (c) il pooling non guasta e triplica il train → per la disciplina
multiple-testing (candidati vicini → si sceglie il PIU' SEMPLICE e generale)
si adotta **E3 pooled**: 5 coefficienti, niente inversioni, un solo set
cross-lega. MAE 0.0117 = **riduzione del 44%** rispetto a non stimare
(movimento medio |.| ≈ 0.021).

**(2) La pubblicazione** (`scripts/build_estimates.py` →
`data/estimates/ou_close_2017_19.csv`, 2279 stime; 1 run
`source=build_estimates_ou_close` coi coefficienti registrati). Scelte di
design per NON farla scambiare per un dato:
- vive in **`data/estimates/`**, mai negli snapshot (test-guardia:
  `tests/test_estimates.py::test_snapshot_non_contaminati`);
- e' una **probabilita'** (`p_over25_close_est`), mai una quota: senza
  margine, non puo' essere presa per un prezzo di book;
- README della cartella con le regole d'uso (niente ROI simulati; ogni
  analisi che la usa lo dichiara) e l'errore atteso in chiaro;
- accesso da codice con warning nel docstring:
  `loader.read_ou_close_estimates()`.
I coefficienti finali (fit pooled su 7978 partite 2019-20+):
`[0.0209, 0.9788, +1.2453, −0.8113, +1.2457]` per
`[1, logit(OU_open), ΔlogitH, ΔlogitD, ΔlogitA]` — vedi 📐.

**(3) Il catalogo dati**: nuovo **`docs/DATI.md`** — per ogni gruppo di
colonne: fonte, copertura, semantica (inclusa la tabella apertura/chiusura
per stagione, che e' il punto piu' insidioso), i limiti dichiarati dei dati
reali, la sezione **Stime** e i **candidati futuri a stima** (promemoria
esplicito richiesto dall'utente: `squad_value` Liga/Lazio — prerequisito:
sistemare il sospetto bug del matching giocatori; aperture O/U sparse; ecc.).
Convenzione fissata anche nel CLAUDE.md §5 (vale per ogni stima futura).

**Onesta'.** La stima cattura solo la parte di movimento CONDIVISA con l'1X2
(corr 0.75-0.86 → ~55-75% della varianza del movimento): le notizie
puro-totali (turnover d'attacco annunciato, meteo) restano fuori. In log-loss
vs esiti reali la stima resta indistinguibile dalla chiusura vera in
Premier/Liga ma un filo peggiore in Serie A (+0.0022 [+0.0001,+0.0053]): per
un benchmark va bene, per qualsiasi uso "operativo" no — ed e' scritto
ovunque.

### 📐 Il modello in dettaglio

Verificato riga per riga contro `scripts/build_estimates.py::_X`:

```
logit(p̂_close_OU) = a + b·logit(p_OU_linea) + cH·Δlogit(pH) + cD·Δlogit(pD) + cA·Δlogit(pA)
Δlogit(pX) = logit(pX_close) − logit(pX_open)        [1X2 devigato, molt.]
fit: OLS pooled, 7978 partite (3 leghe × 7 stagioni 2019-20+)
a=0.0209  b=0.9788  cH=+1.2453  cD=−0.8113  cA=+1.2457
```

**Perche' quei valori.** `b≈0.98` ≈ 1: la linea pre-match e' gia' quasi la
chiusura (il grosso dell'informazione c'e' gia'; b<1 = leggerissima
regressione verso la media). `cH ≈ cA ≈ +1.245` — la SIMMETRIA e' la parte
interessante: l'accorciarsi di UNA delle due squadre (casa O trasferta) alza
l'Over della stessa quantita'; e' la componente "gol totali attesi" del
movimento 1X2, che e' simmetrica per costruzione. `cD = −0.81` negativo: il
pareggio che si accorcia segnala partita bloccata → Under. Il contenuto
informativo del movimento 1X2 sull'O/U e' quindi (cH+cA)·(componente
simmetrica) + cD·(componente pareggio) — la matrice DC codifica la stessa
struttura, ma con pesi fissi sbagliati (lo shift del motore usciva compresso
4-10x, Fase 62); la regressione li impara dai dati. **MAE atteso 0.012**: dal
walk-forward della Fase 62-bis (mai dal fit in-sample, che per coincidenza e'
simile: 0.0122). Tutti i numeri ricalcolabili dai 2 run registrati.

**Riproducibilita'.** `python scripts/_run_fase62bis_estimator.py` (bakeoff,
~35s) → `python scripts/build_estimates.py` (pubblicazione, ~1s) →
`pytest tests/test_estimates.py -q`.

---

## Fase 63 — Il bug del matching giocatori: l'inversione nome/cognome

**Obiettivo.** Sistemare il "sospetto bug" del matching Understat↔Transfermarkt
segnalato nella Fase 60 e messo in cima ai prerequisiti in DATI.md: titolari
con migliaia di minuti (Djené 25.960', Gerard Moreno 17.974', …) senza valore
di mercato, che abbassano la copertura `squad_value` (Liga 58.3%).

**Diagnosi (prima di toccare il codice).** I casi sospetti si dividono in DUE
categorie, e solo una e' un bug:
1. **Inversione nome/cognome tra le fonti** — Understat scrive "Djené Dakonam",
   Transfermarkt "Dakonam Djené" (id 221150, VALUTATO): stesso insieme di
   token, ordine diverso. Nessuno dei 7 stadi del matching lo copriva (l'indice
   per cognome usa l'ULTIMO token, che nelle due fonti e' diverso). Quantificato
   sui dati reali: **27 giocatori / 115.488 minuti recuperabili in Liga, 12 /
   23.069 in Premier**. Questo E' il bug.
2. **Buchi del datalake** — Gerard Moreno, Theo Hernández, Álex Baena: il loro
   record VALUTATO non esiste proprio in `player_profiles` (compaiono solo
   nella tabella "compagni di squadra", con id privi di valutazioni). Nessun
   algoritmo puo' trovare cio' che non c'e': NON e' un bug, e' il limite gia'
   documentato del datalake (lo stesso di Lazio/Milinkovic-Savic, Fase 4a).
   Idem "Morales" (Levante): nome a token unico con MOLTI omonimi valutati →
   ambiguo → giustamente non agganciato (mai un omonimo a caso).

**Fix (una cosa alla volta: solo la categoria 1).** Nuovo stadio **4-bis
`token_sort`** in `map_players`: match sull'insieme ORDINATO dei token
("dakonam djene" == sorted("djene dakonam")), accettato solo con candidato
valutato unico e ruolo compatibile — ambiguita' → nessun match (2 test
unitari sintetici, incluso il caso ambiguo a 3 token). La categoria 2 resta
dichiarata in DATI.md; l'unico rimedio vero sarebbe una fonte valutazioni
migliore.

**Risultato** (ri-arricchimento Premier/Liga; la Serie A NON e'
ri-arricchibile: le sue rose Understat non hanno ne' bundle ne' mirror — 
limite aggiunto a DATI.md §4):

| copertura `squad_value` (entrambi i lati) | prima | dopo |
|---|--:|--:|
| La Liga | 58.3% | **60.2%** (Getafe 22%→44%) |
| Premier League | 95.6% | 95.6% (invariata) |

Guadagno reale ma modesto, e ASIMMETRICO in modo istruttivo: in Liga i
ripescati fanno superare la soglia dell'85% a nuove (squadra, stagione); in
Premier i 12 ripescati (23k minuti) NON spostano nessuna coppia sopra soglia —
pero' i VALORI pubblicati si aggiornano comunque (247 righe per lega ora
sommano anche i ripescati, +52/16 righe di assenze), quindi il dato e' piu'
accurato anche dove la copertura non sale. Il resto del gap Liga e' di
categoria 2 (buchi del datalake): non e' estraibile dal matching, serve una
fonte valutazioni migliore.

### 📐 Il modello in dettaglio

Nessuna matematica: e' un algoritmo di riconciliazione. La regola nuova,
verificata contro `transfermarkt.py::map_players` (stadio 4-bis):

```
chiave(nome) = " ".join(sorted(token_normalizzati(nome)))
match se: |{id : chiave(nome_TM) == chiave(nome_Understat), id valutato,
            ruolo compatibile}| == 1
```

Perche' DOPO squashed (4) e PRIMA di token_subset (5): e' piu' precisa di
subset/cognome/fuzzy (usa TUTTI i token, solo riordinati) ma meno del match
esatto/senza-spazi (che preserva l'ordine). Il vincolo "candidato UNICO"
e' lo stesso di tutti gli stadi di ripiego: su 3 token la stessa chiave puo'
coprire persone diverse ("ana bruno carlos" vs "bruno ana carlos") → in caso
di collisione non si aggancia (test dedicato).

**Riproducibilita'.** `python scripts/build_league_snapshot.py --enrich
premier_league la_liga` (rete per Transfermarkt, cache dopo il primo giro);
`pytest tests/test_data_enrichment.py -q`.

---

## Fase 64 — «La panchina»: il registro dei miglioramenti misurati ma non attivati

**Obiettivo (richiesta utente).** Un file, da tenere SEMPRE aggiornato (regola
scritta nel protocollo), con l'elenco dei modelli/leve che nei backtest
migliorano la config attiva ma NON sono stati adottati — perche' il CI
contiene lo zero, per rumore, o per altre mancanze di robustezza.

**Perche' serve (e perche' non bastava cio' che c'era).** `runs.jsonl` ha
tutte le run (grezzo), il diario ha le decisioni (narrazione), il README ha
l'esito di ogni analisi (sintesi) — ma NESSUNO dei tre risponde a colpo
d'occhio alla domanda operativa: *"cosa abbiamo gia' misurato che potrebbe
diventare ufficiale se arrivasse piu' potenza statistica?"*. Con ~64 fasi,
quella lista viveva solo nella memoria di chi ha letto tutto il diario.

**Scelta.** Nuovo **`docs/PANCHINA.md`**: 11 voci ordinate per credibilita' ×
grandezza (da GG/NG φ35+knee34 della Fase 50, P 98%, a temperature scaling,
−0.0003), ciascuna con: numeri + CI/P, motivo della panchina, come si attiva
(flag/API gia' esistenti), condizioni di promozione. Piu' una sezione "lead
operativi" (draw-bias Serie A, stakes-mismatch) e un archivio per le voci
promosse/smentite. In testa, il contro-esempio che DEFINISCE i criteri: il
prior δ fu adottato NONOSTANTE il CI non conclusivo per motivazione
strutturale (Fasi 7/17/19) — la panchina non e' un "mai", e' un "non finche'".
**Regola fissata nel CLAUDE.md §2** (checklist obbligatoria): ogni esperimento
"migliorativo ma non adottato" aggiunge/aggiorna una voce; promozioni e
smentite si spostano nell'archivio con data e motivo.

### 📐 Il modello in dettaglio

Nessuna matematica nuova: e' un artefatto di PROCESSO. Ogni numero citato nel
file proviene dalle fasi gia' documentate (50, 50-ter, 52-ter, 35, 48, 12a,
10, 12b, 4e-bis, 6, 33, 40, 45) ed e' ricalcolabile dalle run corrispondenti
in `runs.jsonl` — il file non introduce ne' potra' mai introdurre numeri
propri (regola 3 del file stesso).

---

## Fase 65 — La rosa completa e la regola dei due fronti

**Obiettivo (richiesta utente).** Estendere il registro della Fase 64 da
"sola panchina" a **rosa completa** — titolari, panchina E bocciati — e
fissare una nuova regola di lavoro: d'ora in poi ogni modello si sviluppa su
**due fronti**, la versione **per-lega** (es. il DC della Serie A) e la
versione **generale** (es. il DC con iperparametri comuni), entrambe
tracciate nello stesso file.

**Scelta.** `docs/PANCHINA.md` (nome invariato: e' gia' linkato da regole e
README) diventa **«La rosa dei modelli»** con:
1. la **matrice modello × fronte** (Serie A / Premier / Liga / generale-pooled,
   ~28 righe): ogni cella e' ⚽ titolare, 🪑 panchina, ❌ bocciato o ⬜ mai
   testato — e il ⬜ e' dichiarato "lavoro potenziale, non un'assoluzione";
2. le tre sezioni (titolari coi fronti di ciascuno; panchina con le 11 voci
   della Fase 64 ora annotate per-fronte; **bocciati** — 20 voci coi numeri
   del verdetto, da F3 a F57);
3. regole aggiornate nel CLAUDE.md: nuovo **principio 9** (i due fronti) e
   checklist §2 riscritta (ogni esperimento aggiorna la cella della matrice).

**Cosa emerge gia' dalla matrice (il valore del colpo d'occhio).**
- Il **fronte per-lega piu' urgente**: il motore market-implied multi-mercato
  non e' MAI stato backtestato su Premier/Liga (solo il tracer F53); le
  costanti θ/φ/ρ sono tutte Serie A.
- Il **fronte generale gia' vinto senza saperlo**: gli iperparametri del DC
  (ri-taratura piatta, F57) e lo stimatore E3 pooled (F62-bis, batte i
  per-lega) sono le due prove documentate che la versione generale a volte e'
  la migliore.
- Il **contro-esempio che vieta di generalizzare alla cieca**: la
  ricalibrazione per-classe del mercato ha segno OPPOSTO in Premier (w_D=0.93
  vs 1.09, F53) — una versione generale e' bocciata in partenza, il fronte
  per-lega resta aperto.
- Il candidato **piu' vicino alla promozione sul fronte generale**: il devig
  di Shin — unica voce di panchina con direzione confermata su 3/3 leghe.

### 📐 Il modello in dettaglio

Nessuna matematica nuova: artefatto di processo (come la Fase 64). Ogni cella
della matrice rimanda alla fase che l'ha misurata e ogni numero resta
ricalcolabile da `runs.jsonl`; il file non introduce numeri propri. La regola
nuova (principio 9) e' prospettica: ogni esperimento futuro dichiara su quale
fronte sta lavorando e aggiorna la matrice.

**Verifica di completezza (richiesta utente, stessa fase).** Ripassate TUTTE
le fasi del registro README contro la rosa: mancavano 5 voci, aggiunte —
vantaggio-casa per-squadra (F8, bocciato), covariata `midweek_europe`
(F36-bis: −0.0003 ma β stabile 6/6 → PANCHINA, non bocciata), covariate del
canale-pareggio (F37, bocciate), ricalibrazione O/U del mercato (F51-quater,
bocciata), temperatura sopra dp_lvl (F52-ter, panchina). Completate anche le
etichette (GBM include F36; GAS include il Kalman chiuso-per-argomento;
covariate includono ppda/deep; stakes unifica F32/36/45). Totale rosa: 34
righe di matrice, 13 voci di panchina, 23 bocciati.

---

## Fase 66 — Riempire le celle vuote: il valore rosa stimato (e l'inventario finale)

**Obiettivo (richiesta utente).** "Riempire le celle vuote delle colonne che
gia' abbiamo". Inventario post-Fasi 58-63 dei NaN residui negli snapshot:

| gruppo di celle vuote | entita' | esito |
|---|---|---|
| `squad_value` | **73 celle (stagione, squadra)/540** (SA 29, Liga 40, PL 4) | **STIMATE in questa fase** |
| O/U apertura 2017-19 | 760×2 per lega | resta NaN **per design** (il dato reale non esiste; la stima della CHIUSURA e' gia' pubblicata, F62-bis; riempire l'apertura violerebbe la maschera anti-contaminazione) |
| `rest_days_full` prime partite | ~14/lega (0.4%) | resta NaN (fisiologico: nessuna partita precedente nota; riempirlo col cap=14 sarebbe un'assunzione fuori dai dati) |
| 2 partite senza 1X2 apertura | 1 SA (Torino-Fiorentina 2122, recupero COVID: il grezzo non ha NESSUNA quota pre-match) + 1 Liga (Alaves-Sociedad 1718: pre-match Pinnacle presente ma chiusura Pinnacle assente → maschera corretta) | restano NaN, onesti |

**Il lavoro: stimare le 73 celle `squad_value`** (protocollo stime, CLAUDE.md
§5: backtest di fedelta' PRIMA di pubblicare). Sulle 467 celle note,
leave-one-out E leave-TEAM-out (il caso Lazio: squadra senza NESSUNA stagione
nota), candidati dal piu' economico, entrambi i fronti (principio 9):

| candidato | LOO err mediano | leave-TEAM-out |
|---|--:|--:|
| A0 mediana di lega | 52.0% | 52.0% |
| A1 ancora adiacente (dove esiste, 87%) | 16.3% | — (copertura 0) |
| A2 regressione rendimento, per-lega | 27.8% | **28.5%** |
| A2 pooled | 30.6% | 31.4% |
| **A3 = A2+ancora, pooled** | **16.6%** | 38.1% |

**Scelta: ibrido dichiarato riga per riga.** `anchored` (A3 pooled) per le 37
celle con almeno una stagione adiacente nota (err ~17%); `regression` (A2
per-lega) per le 36 senza ancore (err ~29%, p90 75%). Il leave-team-out mostra
il perche' dell'ibrido: A3, fittato CON l'ancora tra le feature, degrada
(38%) quando l'ancora manca per tutta la squadra — meglio il modello che non
l'ha mai vista. **Nota per il principio 9**: il fronte vincente DIPENDE DAL
REGIME (pooled con ancora, per-lega senza) — nessuno dei due domina.

**Pubblicazione**: `data/estimates/squad_value_2017_26.csv` (73 stime, EUR
arrotondati ai 100k, metodo + errore atteso per riga); 2 run registrati
(`fase66_squad_value_est`, `build_estimates_squad_value`); 3 test nuovi (lo
"esattamente i buchi": le stime coprono le celle NaN degli snapshot, ne' una
di piu' ne' una di meno; non-contaminazione).

**Onesta' (piu' severa del solito).** L'errore e' GRANDE (17-29% mediano) e
con CODE PESANTI: la regressione deduce il valore dal rendimento, quindi una
squadra che rende piu' di quanto vale viene sovrastimata per costruzione (es.
Getafe 2018-19, quinto in Liga con una rosa modesta: stima ~254M contro un
valore reale plausibile di ~80M — errore >100%, oltre il p90). Sono ordini di
grandezza, non valori puntuali — scritto nel README della cartella, nel file
(colonna `expected_median_err_pct`) e qui. E la feature resta BOCCIATA come
covariata (F4c/11): queste stime completano il DATO, non promettono
predizione.

### 📐 Il modello in dettaglio

Verificato contro `scripts/_run_fase66_squad_value_est.py` /
`build_estimates.py::build_squad_value`:

```
bersaglio:  y = log(v) − log(mediana_lega_stagione)     [errore = relativo]
A2:  y ≈ a + b·pts_pg + c·gd_pg + d·xgd_pg + e·promossa      (OLS, per-lega)
A3:  y ≈ ... + f·ancora_riempita + g·flag_ancora             (OLS, pooled)
ancora = media dei y NOTI della stessa squadra in (t−1, t+1)
stima finale:  v̂ = exp(ŷ + log(mediana_lega_stagione))
```

**Perche' il log-rapporto col mediano**: i valori spaziano 30M-1.3B e ogni
lega-stagione ha la sua inflazione; il rapporto rende l'errore RELATIVO e
toglie il trend di mercato senza stimarlo. **Perche' il rendimento della
stagione stessa** (e non della precedente): e' un completamento STORICO, non
una predizione — l'informazione in-season e' lecita e dichiarata; per meta'
delle celle (promosse, prime stagioni) la stagione precedente non esiste nei
nostri dati. **Perche' l'OLS e non altro**: 467 osservazioni, 5-7 parametri,
e il confronto e' con candidati piu' semplici (A0/A1) — la versione economica
prima (§1.3); un modello piu' ricco andrebbe ri-validato da zero. I numeri
17/29% vengono dal backtest (run `fase66_squad_value_est`), non dal fit
in-sample.

**Riproducibilita'.** `python scripts/_run_fase66_squad_value_est.py`
(backtest, ~6s) → `python scripts/build_estimates.py` (pubblica entrambe le
stime) → `pytest tests/test_estimates.py -q`.

---

## Fase 67 — I valori rosa REALI: il canale GitHub Actions e la fonte player-scores

**Obiettivo (richiesta utente).** Dopo le stime della Fase 66, l'utente chiede
di cercare su internet i dati REALI. E ha un'intuizione operativa decisiva:
un **workflow GitHub Actions** come "braccio" con rete libera — l'ambiente
cloud e' dietro un proxy che blocca Kaggle/HuggingFace/transfermarkt, ma i
runner Actions no.

**La ricerca della fonte.** Transfermarkt diretto, download HF, CDN R2,
Datasets-Server: tutti bloccati (verificati uno a uno). La fonte giusta e'
`davidcariboo/player-scores` (progetto dcaribou/transfermarkt-datasets, CC0,
aggiornato settimanalmente): ~508k valutazioni per 31.5k giocatori — TUTTI i
giocatori che al datalake salimt mancavano (Milinkovic-Savic 31 valutazioni,
Gerard Moreno 33, Morales 30…) — e le tabelle `appearances` (presenze con
minuti = rose reali per id interno) e `clubs`.

**Il workflow (debug di quello dell'utente).** Tre problemi: (1) file in
`files/.github/workflows/` — GitHub lo legge solo dalla radice; (2) contenuto
corrotto da un incolla duplicato; (3) `workflow_dispatch` compare nella tab
Actions solo se il file sta sul branch di DEFAULT (main, vuoto). Riscritto in
`.github/workflows/import_dataset.yml` con trigger aggiuntivo su push del
file-segnale `.github/import-dataset-trigger` (il trigger push legge il
workflow dal branch pushato → azionabile da questo branch senza toccare main)
e CSV compressi (`files/player_scores/*.csv.gz`: appearances 148MB→42MB,
niente split sotto il limite GitHub dei 100MB). Primo run: successo, 4 file
committati dal bot sul branch.

**La pipeline (`src/data/player_scores.py` + `scripts/build_squad_values.py`).**
Definizione INVARIATA dalla Fase 4a (somma ultima valutazione ≤ 1 settembre,
cap 550 giorni, soglia 85% dei minuti) ma: rose dalle `appearances` della lega
domestica (id interni: **zero matching giocatori per nome** — l'unico aggancio
e' quello dei ~110 club, +34 alias formali in TEAM_ALIASES, zero orfani);
stagioni assegnate per **finestra di date dello snapshot** — la regola "mese
≥ 7" avrebbe fatto traboccare la coda COVID della 2019-20 (chiusa il 2 agosto
2020) nella stagione successiva: scoperto perche' il conteggio celle dava 549
invece di 540, le 9 extra erano TUTTE retrocesse-2020 (test di regressione
dedicato).

**Risultato.**

| copertura `squad_value` (entrambi i lati) | prima (salimt) | **dopo (player-scores)** |
|---|--:|--:|
| Serie A | 69.8% (Lazio mai) | **94.2%** — stagioni concluse **100%** |
| Premier League | 95.6% | **97.8%** — concluse 100% |
| La Liga | 60.2% | **95.0%** — concluse 100% |

I buchi residui: **13 celle, tutte 2025-26** (valutazioni di inizio stagione
ancora incomplete a monte per alcune neopromosse). Le stime della Fase 66
scendono da 73 a 13 (60 SOSTITUITE da dati reali — la Lazio vera: 177-368M
contro stime 185-418M, dentro l'errore dichiarato ~29% con code). Cross-check
sulle 456 celle che avevano gia' un valore: scarto mediano 3-6% (stessa
grandezza, stessa fonte a monte; differenze di vintage e di rosa), p90 12-19%.

**Lezione.** (1) Il canale Actions e' un pattern RIUSABILE per ogni futura
fonte bloccata dal proxy (bundle senza upload manuale dell'utente); (2) la
via maestra contro i buchi era la FONTE, non il modeling (le Fasi 63/66
restano utili: il fix del matching per il path salimt/assenze, lo stimatore
per i 13 residui); (3) di nuovo il conteggio-sanity (549≠540) ha catturato un
bug che i test non vedevano (la coda COVID).

### 📐 Il modello in dettaglio

Nessuna matematica nuova: la formula del valore rosa e' quella della Fase 4a
(verificata contro `player_scores.py::team_season_values`):

```
V(team, s) = Σ_{p ∈ rosa(team, s)} v_p(asof = 1 settembre anno(s))
v_p(asof)  = ultima valutazione ≤ asof, scartata se piu' vecchia di 550 giorni
pubblicato ⇔ Σ minuti dei giocatori valutati / Σ minuti totali ≥ 0.85
rosa(team, s) = {p : ≥1 presenza in campionato per team con data ∈ finestra(s)}
finestra(s)   = [min data, max data] della stagione s NELLO SNAPSHOT
```

L'unica novita' e' `finestra(s)`: derivata dai dati stessi (non da una regola
di calendario), gestisce esattamente la coda COVID. Le costanti 550/0.85 NON
sono state ritoccate (fonte unica: `transfermarkt.py`, da cui sono importate).

**Riproducibilita'.** Import: push di `.github/import-dataset-trigger` (o
Run workflow quando il file sara' su main) → `python scripts/build_squad_values.py`
→ `python scripts/build_estimates.py` (stime residue) → `pytest -q`
(136 test, +5). Run registrati: `build_squad_values_player_scores`,
`build_estimates_squad_value`.

---

## Fase 68 — Gli ultimi buchi chiudibili: preludio dei calendari e cron d'import

**Obiettivo (richiesta utente).** I due passi finali del completamento dati:
(1) re-import periodico del dataset player-scores (per le 13 celle squad_value
2025-26); (2) radicare con date REALI il riposo delle prime partite (82 celle
`rest_days_full` NaN — artefatto della finestra, non buchi del mondo).

**Passo 2 — i calendari "preludio"** (`fixtures._prelude_rows`): massima serie
2016-17 + SECONDE serie 1617→2425 (Serie B, Championship, Segunda — tutte su
openfootball, verificate 200) entrano nel calendario di club con etichette
proprie. Cosi' OGNI squadra della finestra ha una partita precedente reale al
suo esordio: **0 NaN residui su 3 leghe** (82 → 0; +4 alias dal file spagnolo
1617: CD Alavés, RC Celta, Espanyol Barcelona, Deportivo La Coruña).
**Bonus retroattivo scoperto nel diff**: 36 (PL) + 71 (Liga) righe di riposo
GIA' note sono ora piu' accurate — gli alias formali della Fase 67 ("Levante
UD", "Cádiz CF", …) agganciano partite di Copa del Rey/FA Cup che le build
delle Fasi 59-63 scartavano in silenzio (club senza alias → riga persa senza
errore). Il diff e' stato ispezionato riga per riga prima di accettarlo: ogni
cambio risale a una partita di coppa reale ora contata.

**Passo 1 — cron mensile + test immediato.** Aggiunto `schedule` (1° del mese)
al workflow d'import — con l'onesta' dovuta: come il dispatch manuale, lo
schedule parte SOLO dal branch di default, quindi si attivera' quando il file
sara' su main (documentato nel workflow). Il re-trigger immediato (run-2) ha
dato l'informazione che serviva: fonte **Kaggle ufficiale** (dato del 18
luglio 2026, non il mirror di giugno) e coperture IDENTICHE → **le 13 celle
2025-26 mancano davvero a monte oggi**, non per staleness; si chiuderanno se/
quando il backfill arrivera' (il cron le raccogliera' da solo). Sistemato in
corsa un dettaglio visto nel log: gzip reso DETERMINISTICO (mtime=0), cosi' i
run senza dati nuovi non producono commit-rumore.

**Stato finale del completamento** (inventario Fase 66 aggiornato):

| gruppo | prima | dopo |
|---|--:|--:|
| `rest_days_full` | 82 NaN | **0** |
| `squad_value` | 494 NaN (13 celle, stima F66) | invariato (buco A MONTE, cron in attesa) |
| O/U apertura 2017-19 | 4.564 NaN | invariato (unico blocco residuo; chiusura coperta da stima) |
| quote sparse | 6 NaN | invariato (irriducibili: nessuna quota nel grezzo / maschera corretta) |

Completamento celle: **98.68% → 98.70% reale**; ogni cella mancante ha causa
scritta e, dove sensato, una stima dichiarata.

### 📐 Il modello in dettaglio

Nessuna matematica: `rest_days_full` e' la definizione della Fase 4e,
invariata — cambia solo l'INSIEME delle partite note (piu' ampio). L'unica
scelta con contenuto: le partite di preludio/seconda serie contano nel riposo
(sono partite di club a tutti gli effetti) e, per il flag `midweek_europe`,
ricadono nella classe "non-campionato" — irrilevante in pratica (mai a <4
giorni da una partita di massima serie della stessa squadra, stagioni
diverse). Verificata l'invariante di sempre: `rest_full ≤ rest solo-lega`
(il calendario piu' ampio puo' solo accorciare il riposo).

**Riproducibilita'.** `python scripts/build_database.py --fixtures` (Serie A)
e `python scripts/build_league_snapshot.py --fixtures premier_league la_liga`
(rete openfootball al primo giro, poi cache); re-import: push di
`.github/import-dataset-trigger`.

---

## Fase 69 — Stimare i gap sparsi: bakeoff apertura~chiusura (richiesta utente)

**Obiettivo.** Chiudere i "6 NaN" residui delle quote sparse (Fase 68) senza
raccolta dati: l'utente chiede esplicitamente di provare **più metodi di
stima**, fare un bakeoff, e scegliere il migliore (o un mix). Prima, però, un
tentativo di ricerca esterna diretta (BetExplorer/OddsPortal da IP italiano,
sessione utente): fallito per un blocco strutturale nuovo — redirect
geo/ADM (`/it/` senza tabella quote, `oddsportal.com`→`centroquote.it` senza
Pinnacle, storico dietro login) — documentato in MANUALE_SOPRAVVIVENZA.md.

**Scoperta preliminare (correzione di rotta).** Riesaminando il grezzo per
rispondere alla ricerca esterna, il pattern "PS presente, PSC assente" che
spiega Alaves-Sociedad risulta **unico su 2.280 partite 2017-19** (non
sistemico): l'ipotesi dell'AI esterna che 3.52/3.55/2.20 e 3.37/3.39/2.17
fossero "lo stesso momento di mercato" era già gestita correttamente dalla
maschera anti-contaminazione (`_open_odds_market`, Fase 58/61) — nessun bug,
solo NaN dichiarato. Nell'inventariare i gap sparsi con precisione emerge
anche un **terzo buco mai catalogato**: Verona-Genoa 19/10/2020 (Serie A,
stagione 2020-21) ha l'O/U di apertura mancante pur avendo il 1X2 completo —
il conteggio "6 NaN" di Fase 68 copriva solo le 2 partite 1X2, non questa.

**Ragionamento/ipotesi.** Se l'apertura è correlata alla chiusura (che per
tutte e 3 le partite conosciamo per certo), un modello chiusura→apertura può
riempire il buco con un errore MISURABILE — stesso principio già usato per
`ou_close_2017_19.csv` (Fase 62, ma in direzione opposta: lì si stima la
chiusura dall'apertura + movimento 1X2; qui si stima l'apertura dalla sola
chiusura, un problema più povero di segnale ma con **enormemente più dati di
validazione** — 10.258 coppie 1X2 e 7.978 O/U reali contro le 7.978 usate
per l'altro estimatore).

**Alternative considerate (bakeoff, 5-fold CV su tutte le coppie reali).**

| metodo | MAE 1X2 | MAE O/U |
|---|--:|--:|
| A — identità (apertura≈chiusura) | 0.02051 | 0.02105 |
| B — regressione lineare pooled | 0.02013 | 0.01956 |
| **C — regressione LOGIT pooled** | **0.02011** | **0.01956** |
| D — regressione lineare per-lega | 0.02007 | 0.01938 |
| E — blend identità+logit (media) | 0.02022 (**peggio di A e C**) | — |

**Scelta e perché.** **C (logit pooled)**, sempre: sul 1X2 nessun metodo
batte davvero l'identità (curva piatta, come Fase 8/57 — il movimento di
linea 1X2 è quasi tutto rumore piccolo, r=0.99 tra apertura e chiusura
devigate); sull'O/U la regressione aiuta per davvero (~7% in meno). Il
per-lega (D) è sempre marginalmente il migliore ma il margine (~0.0002, 5-10
partite per lega-stagione) non giustifica 3× i parametri per stimare 3
partite. Il blend (E) è **peggiore** di entrambi i singoli metodi — la media
tira l'identità (debole) verso il basso invece di migliorarla: nessun mix,
come sospettava l'utente poteva servire ma i dati dicono di no. Scelto lo
spazio **logit** (non lineare) per coerenza con l'unico altro estimatore del
progetto (Fase 62) e perché resta in [0,1] per costruzione.

**Risultato.** 3 partite stimate in `data/estimates/open_sparse_1x2_ou.csv`
(mai dentro gli snapshot): Alaves-Sociedad (1X2: 0.2871/0.2758/0.4371),
Verona-Genoa (O/U: Over 0.5452), Torino-Fiorentina (1X2: 0.3205/0.2849/0.3947,
O/U: Over 0.4938). MAE atteso dichiarato: **~0.016** (1X2, 3 esiti insieme) e
**~0.020** (O/U) — molto più stretto della stima squad_value (17-29%),
perché qui il rapporto sotto stima è quasi un'identità (β≈0.93-0.97).
Conferma indiretta: per Alaves-Sociedad la stima (`p_home≈0.287`) è vicina al
valore Pinnacle grezzo mai validato (`p_home≈0.278`, scartato dalla maschera)
— coerenza, non prova, ma un segnale che il metodo non produce numeri assurdi.

**Lezione/cosa ne consegue.** (1) Un bakeoff onesto a volte conferma che il
modello più semplice basta (identità sul 1X2) e a volte no (regressione
sull'O/U) — **si misura, non si assume**, anche su un problema piccolissimo
(3 partite). (2) Il blend non è un'assicurazione contro l'errore: mescolare
un metodo debole con uno forte può peggiorare entrambi — va validato come
gli altri, non applicato per prudenza. (3) Il completamento dati "98.70%
reale" della Fase 68 nascondeva un buco non censito (Verona-Genoa): ogni
volta che si tocca l'inventario dei NaN conviene un controllo programmatico
completo, non fidarsi del conteggio della fase precedente.

### 📐 Il modello in dettaglio

```
p_close = devig(quota_chiusura)                 # metrics.devig_1x2 / devig_binary
logit(p_open_est) = alpha + beta * logit(p_close)
p_open_est = sigmoid(alpha + beta * logit(p_close))
```

Fit pooled (minimi quadrati su tutte le coppie reali, 3 leghe insieme):

- **1X2** (home e draw fittati direttamente, away per differenza +
  rinormalizzazione — sempre somma 1 per costruzione):
  `home: alpha=-0.0012, beta=0.9715` · `draw: alpha=-0.0899, beta=0.9281`.
  beta≈1 e alpha≈0 per l'home conferma numericamente il "quasi-identità":
  il coefficiente angolare è a 3 punti percentuali da 1, l'intercetta
  trascurabile. Il draw ha un'intercetta negativa più marcata (-0.09 in
  spazio logit): i pareggi tendono a diventare leggermente MENO probabili
  tra apertura e chiusura (draw-bias noto, Fase 40/50-ter, letto qui dal
  lato opposto della chiusura).
- **O/U**: `alpha=0.0126, beta=0.8912`. beta più lontano da 1 (11% di
  "compressione" verso il centro) spiega perché qui la regressione batte
  l'identità: la chiusura O/U si muove via via più decisa quanto più la
  linea di apertura è già estrema, un pattern che l'identità non cattura.
- **MAE 5-fold**: stesso split (seed fisso 42, riproducibile) per tutti i
  metodi del bakeoff, cosi' il confronto è ad armi pari; il numero
  dichiarato per il 1X2 (0.0156 nel file finale) è il MAE **congiunto sui 3
  esiti** (home+draw dal fit, away rinormalizzato) — più onesto della media
  dei soli due MAE fittati direttamente (che sarebbe stato 0.0143,
  sottostimando l'errore reale perché ignora l'esito away).

**Riproducibilità.** `python scripts/build_estimates.py` (rigenera tutte e 3
le stime, incluso questo file); lettura da codice:
`loader.read_open_sparse_estimates()`; run registrato in
`experiments/runs.jsonl` (`source: build_estimates_open_sparse`).

---

## Fase 70 — Le ultime 13 celle squad_value: dato REALE da Transfermarkt (richiesta utente)

**Obiettivo.** Chiudere il gap 2 (13 celle `squad_value` 2025-26 sotto la
soglia di copertura player-scores, Fase 68/PISTE §5) con dato vero invece
che con la sola stima, visto che il numero è pubblico e potenzialmente
"molto semplice" da recuperare (richiesta utente).

**Ragionamento/ipotesi.** Il valore rosa di un club è mostrato pubblicamente
su Transfermarkt — ma `transfermarkt.com`/`.it`/`.us`/`.co.uk` sono bloccati
dal proxy di QUESTA sessione (confermato: anche `WebFetch` su `example.com`
dava 403, un problema del tool in quel momento, non un blocco mirato). Serve
un canale diverso: un'AI con browser reale (Claude Cowork + estensione
Chrome dell'utente), stesso principio del canale GitHub Actions (Fase 67) ma
per un recupero manuale una tantum, non automatizzabile.

**Alternative considerate (e un errore corretto in corsa).** Primo giro di
link forniti: pagina PROFILO club (`startseite`/`kader` senza `saison_id`).
L'utente ha chiesto "sicuro che puntino all'anno giusto?" — giustamente:
quella pagina mostra sempre il valore **LIVE di oggi** (luglio 2026, quasi
un anno dopo l'inizio della stagione 2025-26 che ci serve), non lo storico.
Corretto aggiungendo `saison_id/2025` alla pagina squadra — ma la sessione
Cowork ha scoperto che nemmeno quello basta: il dato storico per-stagione
vive nella pagina di **competizione filtrata per stagione**
(`.../{lega}/startseite/wettbewerb/{codice}/saison_id/{anno}`), non nella
pagina squadra. Verifica di sanità della sessione Cowork: club poi
retrocessi (Cremonese, Pisa, Oviedo) mostrano nella pagina-competizione un
valore ben diverso (più alto) di quello attuale — se i due numeri
coincidessero, sarebbe la pagina live sbagliata.

**Scelta e perché.** Accettare i 13 valori con provenienza dichiarata (fonte
+ URL + data di recupero, mai verificati in prima persona da questa
sessione per via del blocco di rete) DOPO un controllo di plausibilità: li
confronto con la stima Fase 66 già pubblicata, che ha un errore atteso
dichiarato (17% anchored / 29% regression) — se il nuovo dato cadesse
sistematicamente fuori da quel range, sarebbe un segnale di errore nella
raccolta, non solo nella stima.

**Risultato.**

| team | lega | stima F66 (M€) | reale F70 (M€) | scarto |
|---|---|--:|--:|--:|
| Bologna | serie_a | 479.4 | 274.70 | −42.7% |
| Como | serie_a | 276.2 | 405.20 | +46.7% |
| Cremonese | serie_a | 107.3 | 69.03 | −35.7% |
| Parma | serie_a | 136.4 | 189.00 | +38.6% |
| Pisa | serie_a | 92.8 | 98.30 | +5.9% |
| Udinese | serie_a | 255.6 | 200.00 | −21.8% |
| Leeds | premier_league | 414.0 | 373.30 | −9.8% |
| Sunderland | premier_league | 413.7 | 424.93 | +2.7% |
| Celta | la_liga | 108.6 | 192.20 | +77.0% |
| Elche | la_liga | 81.8 | 100.20 | +22.5% |
| Espanol | la_liga | 96.2 | 127.85 | +32.9% |
| Levante | la_liga | 100.1 | 109.90 | +9.8% |
| Oviedo | la_liga | 55.4 | 56.40 | +1.8% |

Scarto assoluto **mediano 22.5%**, medio 26.8% — dentro il range dichiarato
per la Fase 66 (17-29%), anche se alcune righe singole (Celta +77%, Bologna
−43%) sono nella coda: coerente col limite già scritto allora ("code
pesanti... l'errore può superare il 100%"), non un segnale che il nuovo dato
sia sbagliato. I 13 valori sono entrati negli snapshot
(`home/away_squad_value`), le 13 righe sono state rimosse da
`squad_value_2017_26.csv` (ora vuoto, stesso schema di sempre, rigenerabile:
0 buchi → 0 righe). **`squad_value` è ora reale al 100% su TUTTE le 9
stagioni, 3 leghe, zero NaN residui.**

**Lezione/cosa ne consegue.** (1) Un dato "pubblico e semplice" può comunque
avere una trappola di **timing** non ovvia (pagina live vs storica): la
domanda scettica dell'utente ("sicuro che l'anno sia giusto?") ha evitato di
scrivere nello snapshot un numero sbagliato di quasi un anno. (2) Quando un
dato reale arriva a sostituire una stima, il confronto tra i due è di per sé
un piccolo esperimento: qui conferma che l'errore dichiarato della Fase 66
era onesto (mediana vicina al dichiarato), non che fosse preciso riga per
riga — a riprova del proprio avviso "usare come ordine di grandezza". (3) Un
canale "browser reale una tantum" (Cowork) è un terzo modo di aggirare i
blocchi di rete, distinto sia dal proxy-bypass di GitHub Actions (Fase 67,
automatizzabile) sia dal blocco geo/ADM incontrato per BetExplorer (Fase
69, bloccato anche da browser reale se l'IP è italiano) — utile quando il
dato è troppo piccolo/puntuale per giustificare un intero workflow.

### 📐 Il modello in dettaglio

Nessuna nuova matematica: sostituzione diretta di 13 valori NaN con numeri
reali (EUR), stesso schema delle colonne `home/away_squad_value` già
esistenti. L'unico calcolo è il confronto con la stima pre-esistente:

```
scarto_% = (valore_reale - valore_stimato_F66) / valore_stimato_F66 * 100
```

usato per decidere se il dato raccolto è plausibile (confrontato contro
l'errore atteso già dichiarato alla Fase 66), non per calibrare nulla.

**Riproducibilità.** L'iniezione è un'operazione MANUALE una tantum (non
rigenerabile da una fonte automatica), fatta con
`scripts/_apply_fase70_squad_value_real.py` (i 13 valori sono scritti nel
codice, con la fonte in testa al file); da rilanciare `build_estimates.py`
dopo per confermare che `squad_value_2017_26.csv` resti vuoto (corretto un
bug di bordo: con 0 buchi il costruttore andava in errore su
`sort_values` — ora gestito).

---

## Fase 71 — Caccia O/U 2017-19, Fase A: dataset già pronti (Kaggle/GitHub/HF), negativa

**Obiettivo.** Riprendere il piano di `docs/CACCIA_OU_2017_19.md` (Fase B,
scraping BetExplorer, era già chiusa negativa) partendo dal passo più
economico non ancora tentato: la Fase A, ricognizione di dataset già
scrappati che coprano O/U 2.5 apertura+chiusura per Serie A/Premier/La Liga
2017-18/2018-19, prima di investire in scraping diretto (Fase D, OddsPortal,
richiede login).

**Ragionamento/ipotesi.** Se qualcuno ha già raccolto e ripubblicato lo
storico giusto (Kaggle, un repo GitHub con CSV committati, un dataset
accademico su Zenodo/Hugging Face), è molto più economico di ri-scrappare.
Ipotesi da verificare: la maggior parte dei dataset di quote calcio in giro
ripubblica football-data.co.uk — se quella fonte non ha mai avuto l'apertura
O/U per il 2017-19 (sospetto già in `docs/DATI.md` §2), ogni suo derivato
eredita lo stesso buco, indipendentemente da quanti se ne trovano.

**Alternative considerate.** (1) Cercare a mano su Kaggle/GitHub via
`WebSearch` (funzionante in sessione) e fidarsi delle descrizioni — troppo
debole: le descrizioni Kaggle non dichiarano quasi mai lo schema colonne
esatto. (2) Leggere le pagine dataset con `WebFetch` — tentato, ma il tool
rispondeva 403 anche su `example.com` (bug noto, non un blocco dei siti,
vedi `docs/MANUALE_SOPRAVVIVENZA.md`): scartato per quel giro. (3) **Scelta
fatta**: `WebSearch` per la ricognizione + un probe via runner GitHub Actions
(stesso canale-bypass della Fase 67) che scarica i candidati con `kagglehub`
e ne ispeziona le colonne davvero, senza fidarsi di nulla di non verificato.

**Cosa abbiamo fatto.**
1. `WebSearch` mirato (query su oddsportal/football-data/Kaggle/Zenodo/
   OddsPortal opening-odds history). Trovata conferma indipendente dai nostri
   dati: football-data.co.uk raccoglie due istantanee apertura/chiusura
   **solo dalla stagione 2019/20** (prima, un'unica media Betbrain) — combacia
   esattamente col buco già documentato. Nessun repo GitHub con CSV pronti
   (solo scraper), niente su Hugging Face (`hub_repo_search`, più query),
   un dataset accademico Zenodo (Whelan & Hegarty 2024) copre 1X2 e Asian
   handicap, non O/U — scartato.
2. Probe diagnostico via Actions (`scripts/probe_kaggle_ou_datasets.py`,
   workflow `kaggle-ou-probe.yml`) su 6 dataset Kaggle candidati (i più
   citati nei risultati di ricerca per "storico quote calcio"): scarica con
   `kagglehub` (senza credenziali, stesso pattern Fase 67) e stampa colonne +
   range date nel log — **nessun dato committato**, solo diagnostica (run
   [29881936699](https://github.com/BTConomista/Polymarket-oracle/actions/runs/29881936699)).

**Risultato.** Negativo su tutti e 6. I dataset con colonne quote
(`mexwell/historical-football-resultsbetting-odds-data` — mirror completo
football-data, centinaia di file stagione×lega; `louischen7/football-
results-and-betting-odds-data-of-epl`; `thedevastator/uncovering-betting-
patterns-in-the-premier-leagu`) sono ricostruzioni dirette di
football-data.co.uk: **ogni singolo file** che copre 2017-18/2018-19 per le
3 leghe (`E0`/`I1`/`SP1`) ha esattamente `PSH/PSD/PSA` + `PSCH/PSCD/PSCA`
(Pinnacle 1X2 apertura/chiusura, già nostri dalla Fase 61) e **una sola**
istantanea O/U — `BbOU, BbMx>2.5, BbAv>2.5, BbMx<2.5, BbAv<2.5` — zero
colonne apertura/chiusura O/U distinte. Gli altri 3 (`eladsil`,
`ahmadasadi00`, `rayenjlassi`) non hanno proprio colonne O/U. Non è
un'inferenza dalla sola ricerca web: è l'ispezione diretta delle colonne di
ogni file 2017-19 dei 6 candidati, che conferma il meccanismo sospettato —
il buco è nella fonte a monte (football-data.co.uk non ha mai raccolto
l'apertura O/U per quelle stagioni), quindi ogni dataset che la ripubblica
eredita lo stesso buco, per quanti se ne trovino.

**Lezione/cosa ne consegue.** (1) Una ricerca web che "conferma" un'ipotesi
sulla fonte a monte non basta da sola: senza l'ispezione diretta delle
colonne (qui via Actions, perché Kaggle è irraggiungibile dalla sessione
cloud) si rischiava di scartare un dataset valido per pigrizia o, peggio,
accettarne uno cattivo fidandosi della descrizione. (2) Fase A e Fase B sono
ora **entrambe chiuse negative**: i due canali "economici" del piano
(dataset già pronti, scraping diretto d'archivio) sono esauriti. Resta solo
la Fase D (OddsPortal headless con login, rischio/complessità più alta) o
accettare le stime attuali (Fase 62-bis, MAE atteso ~0.012 chiusura /
Fase 69 ~0.016-0.020 le poche righe sparse) come tetto dei dati per l'O/U
2017-19 — decisione da prendere con l'utente, non un default silenzioso.

### 📐 Il modello in dettaglio

Nessuna nuova matematica: fase di ricognizione dati, non di modellazione. I
controlli applicati sono quelli già definiti in `docs/CACCIA_OU_2017_19.md`
§1 (criteri di accettazione: linea 2.5 esatta, quote decimali >1.0, apertura
≠ chiusura in ≥90% delle righe, overround `1/over + 1/under > 1` su ogni
riga, copertura ≥95%, provenienza dichiarata) — nessuno dei 6 candidati è
arrivato al punto di doverli applicare, perché nessuno ha nemmeno la coppia
di colonne apertura/chiusura O/U richiesta dallo schema §1. Il probe
(`scripts/probe_kaggle_ou_datasets.py`) si limita a un pattern-match sui nomi
colonna (`OU_HINTS`, `OPEN_CLOSE_HINTS`) e a un parse di `pandas.to_datetime`
sulla colonna data per il range stagionale — diagnostica, non stima.

**Riproducibilità.** `python scripts/probe_kaggle_ou_datasets.py` (richiede
`kagglehub`, rete verso Kaggle — non disponibile dalla sessione cloud, va
lanciato dal runner Actions via il trigger `.github/kaggle-ou-probe-trigger`
o `workflow_dispatch` su `kaggle-ou-probe.yml`); nessun dato scritto negli
snapshot, nessuna riga in `runs.jsonl` (fase di ricognizione, non un
backtest/tuning — stesso trattamento della Fase B).

---

## Fase 72 — Spremere ANCORA la stima E3 pooled (richiesta esplicita: "al massimo")

**Obiettivo.** Con Fase A e Fase B chiuse negative, l'utente sceglie di NON
rincorrere Fase D (OddsPortal headless, login) e chiede invece di migliorare
il più possibile la stima già pubblicata (E3 pooled, Fase 62-bis, MAE
walk-forward 0.0117) prima di accettarla come tetto dei dati per il 2017-19,
più un promemoria esplicito per il futuro (vedi PISTE.md e
CACCIA_OU_2017_19.md).

**Ragionamento/ipotesi.** E3 pooled è lineare in 4 feature (O/U apertura +
movimento 1X2 nei 3 esiti). Quattro leve ortogonali, mai provate, potrebbero
catturare segnale che il modello lineare lascia sul tavolo: (1) curvatura —
un'interazione tra i movimenti home/away; (2) un effetto di calendario reale
già trovato altrove (Fase 30: il vantaggio-casa crolla a fine stagione); (3)
regolarizzazione — controllo di robustezza, anche se con 5 parametri su
~8000 righe l'overfitting è già improbabile; (4) non-linearità generica via
gradient boosting sulle stesse 4 feature — le Fasi 21-23 hanno già trovato
che il GBM non batte modelli lineari su mercato/esiti, ma qui il compito è
diverso (mimare un prezzo di chiusura, non predire un esito), quindi vale il
test invece di assumere lo stesso risultato per analogia.

**Alternative considerate.** Scartata la regressione L1/MAE-diretta (via
programmazione lineare): l'obiettivo di valutazione è già MAE ma il fit OLS
in logit minimizza L2 — un mismatch reale — ma il costo (LP con ~16.000
vincoli per fold, ripetuto su più fold/candidati) supera il guadagno atteso
(i residui in spazio logit non hanno code pesanti evidenti, Fase 62-bis).
Scartato un lag/rolling della linea O/U stessa: nel 2017-19 non esiste una
seconda lettura O/U pre-match da cui derivarlo.

**Cosa abbiamo fatto.** Stesso protocollo esatto di Fase 62-bis (stesse
righe 2019-20+/3 leghe, stesso walk-forward `WF_TEST`, stesso pooling
cross-lega, stesso bootstrap B=10000) — numeri confrontabili 1:1 —
(`scripts/_run_fase72_ou_close_est2.py`, 1 run `source=fase72_ou_close_est2`):

| candidato | MAE medio 3 leghe |
|---|--:|
| **E3 pooled** (riferimento, Fase 62-bis) | **0.0117** |
| E5 = E3 + dH·dA (interazione) | 0.0117 |
| E6 = E3 + season_frac (calendario) | 0.0117 |
| E7 = E3 ridge, α=0.3 | 0.0119 |
| E7 = E3 ridge, α=1.0 | 0.0124 |
| E7 = E3 ridge, α=3.0 | 0.0135 |
| E7 = E3 ridge, α=10.0 | 0.0155 |
| E8 = GBM(feature di E3), pooled | 0.0160 |

**Risultato.** **E3 pooled resta imbattuto.** L'interazione (E5) e il
calendario (E6) non cambiano il MAE alla quarta cifra: il movimento 1X2 già
cattura tutto ciò che quelle due leve avrebbero potuto aggiungere — nessuna
curvatura o effetto di stagione residuo. Il ridge (E7) **peggiora
monotonicamente** con α: conferma diretta che il problema non è overfitting
(la regolarizzazione toglie segnale vero, non rumore) — atteso, dato il
rapporto righe/parametri (~1600:1), ma verificato invece che assunto. Il GBM
(E8) è nettamente peggiore (+37% di MAE): stessa conclusione delle Fasi
21-23 (il tetto è informativo, non di forma funzionale), ora confermata
anche su questo compito specifico (mimare un prezzo, non predire un esito).

**Lezione/cosa ne consegue.** (1) E3 pooled non è solo "il migliore provato
finora": è stato messo sotto pressione con 4 leve ortogonali indipendenti e
nessuna lo sposta — è un tetto **informativo** più solido di quanto fosse
prima di questa fase (che aveva un solo confronto, M4, nella Fase 62-bis
originale). (2) La stima pubblicata (`data/estimates/ou_close_2017_19.csv`)
**non cambia**: stessi coefficienti, stesso MAE atteso 0.012, nessuna
rigenerazione necessaria. (3) Come richiesto dall'utente, il canale "cerca
meglio i dati reali" resta esplicitamente APERTO per il futuro (non chiuso
per sempre): la Fase A/B hanno esaurito le vie economiche/sicure disponibili
OGGI, non tutte le vie possibili — nuovi dataset possono comparire su
Kaggle/GitHub/HF nel tempo, e la Fase D (OddsPortal login) resta una
candidata non tentata. Promemoria scritto in `docs/PISTE.md` e in testa a
`docs/CACCIA_OU_2017_19.md`.

### 📐 Il modello in dettaglio

Nessuna formula nuova per E3 (vedi Fase 62-bis). Le leve nuove:

```
E5:  logit(p_close) = a + b·logit(p_open) + cH·ΔH + cD·ΔD + cA·ΔA + cHA·(ΔH·ΔA)
E6:  logit(p_close) = a + b·logit(p_open) + cH·ΔH + cD·ΔD + cA·ΔA + cS·season_frac
     season_frac = (rank(data) - 1) / (n_partite_lega_stagione - 1)   in [0,1]
E7:  stesso disegno di E3; coef = (AᵀA + αP)⁻¹ Aᵀy,  P = diag(0,1,1,1,1)
     (intercetta non penalizzata, standard per la ridge)
E8:  GradientBoostingRegressor(n_estimators=100, max_depth=2, lr=0.05,
     subsample=0.8) su [logit(p_open), ΔH, ΔD, ΔA] → logit(p_close)
```

**Perché quei valori.** `season_frac` è un rank normalizzato (non la data
grezza) per essere confrontabile tra leghe con calendari diversi. Gli α della
ridge sono una grid coarse (0.3→10, decadi mezze) attorno a 1 — sufficiente
per vedere la direzione (monotona, nessun minimo interno da cercare più
fine). Il GBM usa alberi shallow (`max_depth=2`) e `subsample=0.8` proprio
per limitare l'overfitting che ci si aspetterebbe di più da lui che da un
modello lineare a 5 parametri — anche così, perde nettamente. **MAE
0.0117 di E3 pooled è identico, alla quarta cifra, al valore già registrato
nella Fase 62-bis**: conferma che l'implementazione qui è la stessa esatta
pipeline (stesso fingerprint dati, stesso protocollo), non solo un numero
simile per caso.

**Riproducibilità.** `python scripts/_run_fase72_ou_close_est2.py` (offline,
~20s; richiede `scikit-learn` solo per E8 — se assente, lo salta e prosegue
con gli altri candidati). Registrato in `runs.jsonl`
(`source=fase72_ou_close_est2`).

---

## Fase 73 — L'O/U 2017-19 era un'APERTURA, non una chiusura: il dato reale nella colonna giusta

**Obiettivo.** L'utente chiede di capire dov'è DAVVERO il buco O/U 2017-19:
riguarda l'apertura, la chiusura, o entrambe? E, se il dato che abbiamo è
un'apertura, spostarlo nella colonna giusta e poi cercare il miglior metodo
per stimare la chiusura mancante.

**La scoperta.** Fino alla Fase 72 la narrazione era: "nel 2017-19 abbiamo
una sola linea O/U, di timing ambiguo, tenuta nello slot *chiusura*
(`odds_over25`) con un ⚠️; l'apertura O/U è un buco (4.564 celle NaN)". La
verifica ha ribaltato la diagnosi: **quella linea è un'APERTURA reale, e il
buco vero è sulla CHIUSURA.** Quattro evidenze indipendenti convergono:
1. **Metodologia documentata**: il `notes.txt` di football-data (recuperato da
   3 mirror GitHub indipendenti; il sito diretto è irraggiungibile) dichiara le
   colonne `Bb*` (Betbrain, tra cui `BbAv>2.5`) raccolte "Friday afternoons /
   Tuesday afternoons" = pre-match = **apertura**.
2. **Struttura delle colonne**: nel grezzo 2017-19 (verificato su tutte e 3 le
   leghe, entrambe le stagioni) il suffisso `C` (closing) esiste **solo per
   l'1X2** (`PSC*` Pinnacle), **mai per l'O/U** (nessun `PSC>2.5`, `AvgC>2.5`,
   `P>2.5`): non c'è alcuna colonna di chiusura O/U, quindi `BbAv` non *può*
   essere una chiusura.
3. **Coerenza di timing**: `BbAv` condivide la raccolta del venerdì con `PS*`,
   che il progetto già usa come **apertura 1X2** (Fase 61) — stesso timing.
4. **Margine (overround)**: `BbAv` O/U ~1.055 ≈ apertura `Avg` ~1.053 delle
   stagioni recenti, leggermente più largo della chiusura `AvgC` ~1.052
   (coerente con una linea di apertura, meno affilata).

**Cosa abbiamo fatto (la correzione).** Semplificata la politica quote in
`src/data/loader.py` (una sola regola generale, non un hack per-stagione):
- **CHIUSURA** = solo colonne di chiusura genuine (`AvgC*/B365C*/PSC*`), NaN se
  non esistono. Rimossi i fallback pre-match (`Avg*/BbAv*/B365*`) dalle liste di
  chiusura: erano loro a far passare la pre-match `BbAv` per una chiusura.
- **APERTURA** = solo colonne pre-match. Insieme **disgiunto** dalla chiusura →
  apertura e chiusura non coincidono mai per costruzione → **rimosso il masking**
  (`_open_odds_market`), che prima oscurava l'apertura quando non c'era una
  chiusura genuina (l'esatto meccanismo che nascondeva l'apertura O/U 2017-19).

Snapshot rigenerati (`build_database.py --refresh-odds`,
`build_league_snapshot.py --refresh-odds`) e **diff cella-per-cella** contro i
precedenti per dimostrare il raggio d'impatto:
- **O/U 2017-19** (3 leghe, 2.280 righe): chiusura (`odds_over25/under25`) →
  NaN; apertura (`odds_over25_open/under25_open`) → `BbAv` reale. La correzione.
- **2019-20+**: **bit-identico** ovunque (la chiusura genuina `AvgC` esiste, la
  politica non cambia nulla).
- **1 riga 1X2** (La Liga, Alaves-Sociedad 14/10/2017): chiusura → NaN,
  apertura → `PSH` reale. È l'unico caso su 2.280 con `PSC*` vuote (già
  segnalato in PISTE.md): prima la chiusura era un *falso* (fallback `BbAvH`) e
  l'apertura NaN; ora la chiusura è onestamente NaN e l'apertura reale c'è. La
  stima di apertura 1X2 della Fase 69 per questa riga è stata **ritirata**
  (`open_sparse` scende da 3 a 2 righe, auto-rilevata dal builder).

**Il metodo per la chiusura (invariato + una leva nuova).** L'estimatore E3
pooled (Fase 62-bis) leggeva la linea pre-match da `odds_over25` (ora NaN):
spostato su `odds_over25_open` (stessi numeri, solo la colonna giusta). La
stima pubblicata `ou_close_2017_19.csv` è risultata **byte-identica** a prima
(2.279 righe, stessi valori): la correzione è di *etichettatura*, non cambia
cosa stimiamo. Il reframing sblocca però un input mai usato — la **dispersione
max-vs-media** dell'O/U all'apertura (`BbMx` vs `BbAv`, disponibile nel
2017-19; analogo `Max`/`Avg` nel fit 2019-20+): misura il disaccordo tra book,
un possibile predittore del movimento verso la chiusura. Bakeoff dedicato
(`_run_fase73_ou_close_disp.py`, stesso protocollo walk-forward di Fase
62-bis/72):

| candidato (walk-forward pooled) | MAE medio 3 leghe |
|---|--:|
| **E3** (riferimento) | **0.0117** |
| E9 = E3 + dispersione | 0.0117 |
| E10 = E3 + dispersione×logit(apertura) | 0.0117 |
| E11 = E3 + entrambe | 0.0117 |

La dispersione **non aiuta** (Δ ±0.0001, trascurabile): E3 pooled resta il
metodo migliore, ora confermato anche contro l'unico input nuovo che la
correzione rendeva disponibile. Sommato alla Fase 72 (interazione 1X2,
calendario, ridge, GBM — tutti falliti), E3 ha ora resistito a **8 leve
ortogonali**: tetto informativo molto solido.

**Lezione/cosa ne consegue.** (1) Una colonna "sospetta ma usata da mesi"
(l'O/U 2017-19 nello slot chiusura, con un ⚠️ che diceva *che* era strana ma
non *perché*) andava verificata alla fonte, non tramandata: il `notes.txt` +
la struttura delle colonne dicono in modo inequivocabile che è un'apertura.
(2) Il buco 2017-19 è **metà di quanto si credeva**: l'apertura O/U è un dato
REALE (era solo mal etichettato), solo la chiusura è mancante — la caccia
esterna (CACCIA_OU_2017_19.md) ha ora un bersaglio più stretto e onesto.
(3) La correzione ha reso la politica quote **più semplice** (niente masking,
insiemi disgiunti) oltre che più corretta: un raro caso in cui il fix riduce
il codice. (4) Impatto a valle (auditato): la chiusura O/U del 2017-19 è ora
NaN negli snapshot — ogni analisi che ne ha bisogno usa l'apertura reale
(`odds_over25_open`) o la stima (`data/estimates/`), mai più una pre-match
scambiata per chiusura.

**Audit dell'impatto a valle (fatto, non solo dichiarato).** 14 script storici
(Fasi 50/51/52: `_fase52_common`, `_run_fase50_mi_*`, `_run_fase51_*`,
`_run_gbm_*`, `_run_season_window`, `_run_seasonal_profile`) includono il 1819
nel loro range e usano l'O/U: prima leggevano `odds_over25` per il 1819 (di
fatto un'apertura `BbAv` mal etichettata), ora NaN. Verificato che la
degradazione è **graziosa**: caricano l'O/U con `dropna`/`isfinite` (es.
`_fase52_common.load_with_rates` filtra `ok = isfinite(...odds_over/under)`),
quindi le righe 1819 senza chiusura O/U vengono **escluse**, non usate sbagliate
né causano crash. La cache che alimenta quegli script (`outputs/db_base_*.csv`)
**non è versionata** ed è rigenerata da `_gen_cache.py` (che legge lo snapshot
vivo): nessun dato vecchio mal etichettato persiste su disco. I run già
registrati in `runs.jsonl` sono **record storici immutati** (non si ri-scrivono).
Le conclusioni ADOTTATE non dipendono dall'etichetta O/U del solo 1819 (1/8
delle stagioni; e per l'O/U la conclusione era "non si batte la chiusura" —
conservativa proprio sotto la mis-etichettatura, che rendeva la linea 1819 meno
affilata e quindi più facile da battere: non battuta lo stesso). Un'eventuale
ri-validazione completa dei sotto-risultati O/U delle Fasi 50-52 escludendo il
1819 è disponibile su richiesta, ma non cambia le adozioni.

### 📐 Il modello in dettaglio

Nessuna nuova matematica per la stima (E3 invariato, vedi Fase 62-bis). Le
formule toccate:

**Politica di scelta quote** (`loader._pick_market_odds`, invariata; cambiano
solo le liste di preferenza):
```
CHIUSURA:  odds_over25   <- prima colonna valida tra [AvgC>2.5, B365C>2.5]
           (nessun fallback pre-match; NaN se nessuna presente)
APERTURA:  odds_over25_open <- prima valida tra [Avg>2.5, BbAv>2.5, B365>2.5]
           (sempre popolata dove esiste; insieme disgiunto dalla chiusura)
overround < 1 -> ripiego in blocco al livello successivo (Fase 58, invariato)
```
Prima della Fase 73 la lista chiusura O/U era `[AvgC>2.5, B365C>2.5, Avg>2.5,
BbAv>2.5, B365>2.5]` (i 3 pre-match in coda): per il 2017-19, prive di `AvgC`,
la chiusura cadeva su `BbAv` (apertura) e il masking azzerava l'apertura.

**Dispersione** (`_run_fase73_ou_close_disp._dispersion`):
```
disp = 0.5 * [ (max_over/avg_over − 1) + (max_under/avg_under − 1) ]
       (2017-19: max=BbMx, avg=BbAv;  2019-20+: max=Max, avg=Avg)
E9:  logit(p_close) = E3 + c·disp
E10: logit(p_close) = E3 + c·(disp · logit(p_open))
```
`disp` è una magnitudine (≥0, premio best-vs-media): l'ipotesi era che
modulasse *quanto* si muove la linea, non la direzione (quella la dà il 1X2,
già in E3). Distribuzioni confrontabili tra le due ere (premio medio ~0.042
Betbrain vs ~0.038 panel recente): il fit cross-era è legittimo. Esito: `c`≈0
utile (Δ MAE ±0.0001), coerente col fatto che una feature non-segnata aggiunge
poco a una predizione segnata già al tetto.

**Riproducibilità.** `python scripts/_restore_raw_cache.py` →
`python scripts/build_database.py --refresh-odds` →
`python scripts/build_league_snapshot.py --refresh-odds premier_league la_liga`
→ `python scripts/build_estimates.py` (stima byte-identica) →
`python scripts/_run_fase73_ou_close_disp.py` (bakeoff dispersione) →
`pytest -q`. Run registrato: `source=fase73_ou_close_disp`.

---

## Fase 74 — Ri-validazione di TUTTI i calcoli sui dati corretti (richiesta utente)

**Obiettivo.** Dopo la correzione dei dati (Fase 73: O/U 2017-19 spostato da
chiusura ad apertura, chiusura ora NaN), ri-controllare che nessun risultato
pubblicato/adottato cambi in modo da invalidarne le conclusioni.

**Il diff dei dati bounda tutto il lavoro.** Confronto cella-per-cella dello
snapshot pre/post-Fase 73 (backup congelato): cambiano **SOLO** le stagioni
1718/1819, **SOLO** le colonne O/U (over25/under25 + `_open`), più **1 riga**
1X2 in La Liga (Alaves-Sociedad). **I gol sono identici in tutte le leghe.**
Due conseguenze dirette, che riducono la ri-validazione a un perimetro
piccolissimo:
1. **Il Dixon-Coles fitta sui GOL** → tutte le sue predizioni sono **identiche**
   ovunque. Ogni numero puramente di modello (log-loss DC, Brier, calibrazione,
   prior, shrinkage, emivita, xG-blend, ecc.) è **invariato per costruzione**.
2. **Il 2019-20+ è bit-identico** → ogni analisi la cui finestra parte da
   2020-21 è **invariata per costruzione**.

**Mappa degli script (70 script `_run_*`/analyze/backtest).**
- **43 non usano l'O/U** → immutati (dipendono da gol/1X2 non-1819).
- **~22 usano l'O/U ma partono da 2020-21** — verificato il range: `gap_uncertainty`
  (Fase 17, gap+CI headline), `market_implied` (26), `markets_bakeoff` (41, il
  portafoglio adottato), `market_denoise`, `routing`, `shape`, `matchday`,
  `dc_from_market`, `market_specific_roi` hanno tutti `SEASONS=[2021..2526]` →
  **invariati** (dati bit-identici). Spot-check: `market_implied` carica
  `load_league` e filtra 2021+ → risultato identico per costruzione.
- **13 includono il 1819** (Fasi 50/51/52 + `gbm_*` + `season_window`/
  `seasonal_profile`): gli unici potenzialmente toccati.

**Ri-eseguito l'unico ADOTTATO tra questi: il router dp (Fase 52).**
`_run_fase52_router3.py` sulla cache Serie A rigenerata. Con la chiusura O/U
1819 ora NaN, `load_with_rates` (che richiede tutte e 5 le quote finite) scarta
l'intero 1819; il walk-forward, perdendo il 1819 come training, sposta l'inizio
del confronto da 1920 a 2021 (n 2660→2280). Esito confronto vecchio→nuovo:

| | vecchio (incl. 1819 nel training) | nuovo (dati corretti) |
|---|---|---|
| media 20 mercati (dp v3) | — | 0.5531 vs devig 0.5534, Δ −0.0003 |
| mercati dove **dp è CONCLUSIVAMENTE PEGGIORE** | **0** | **0** |
| delta dp-vs-devig per mercato | — | stabili (es. over_2.5 +0.0001→+0.0005; away_ov_1.5 −0.0008→−0.0010) |

**La conclusione adottata REGGE**: dp non è mai conclusivamente peggiore del
devig su nessuno dei 20 mercati (né prima né dopo), i delta sono stabili. Il
1819 esce **correttamente** da un'analisi basata sulla CHIUSURA (non ha una
chiusura O/U); i livelli assoluti si spostano solo perché la finestra si
restringe, non perché un giudizio cambi.

**I 12 script esplorativi restanti** (Fasi 50/51 dp-discovery/beat-close/ML
bespoke, `gbm_*`, window/profile) sono **risultati CHIUSI negativi** (ML
bespoke perde, GBM perde, beat-the-close è idiosincratico della chiusura Serie
A): togliere 1 stagione di O/U su 8 a un risultato negativo lo lascia negativo
(nessun campione borderline dipendeva dal solo 1819). Non ri-eseguiti uno per
uno (archiviati, non adottati); la loro validità è indiretta — il dp che
scoprirono è confermato dal router adottato qui sopra. Ri-esecuzione completa
disponibile su richiesta.

**Onestà.** I run storici in `runs.jsonl` restano **record immutati** (non si
riscrivono col senno di poi); la Fase 52 originale era corretta sui dati di
allora. Questa fase aggiunge un run nuovo (`fase52_router3`, dati corretti) e
la conclusione che l'adozione non cambia.

**Lezione/cosa ne consegue.** Un errore di etichettatura su una colonna, una
volta corretto, non si propaga "a caso": qui il diff dei dati (gol invariati +
2019-20+ bit-identico) **dimostra** che l'80%+ delle analisi è immutato senza
bisogno di rilanciarle, e restringe la ri-validazione a un solo risultato
adottato (il router), che regge. Il valore di uno snapshot congelato +
fingerprint: si può *provare* cosa NON è cambiato, non solo sperarlo.

### 📐 Il modello in dettaglio

Nessuna matematica nuova: ri-esecuzione. Il criterio di invarianza è la
**bit-identità dei dati** per (stagione ∉ {1718,1819}) e per la colonna gol
ovunque, verificata con `numpy.isclose` cella-per-cella sullo snapshot pre/post
(gestendo i NaN: `NaN==NaN` conta come "uguale"). Router: metriche e formula
del dp (θ mean-preserving) invariate dalla Fase 51/52; qui cambia solo il
campione (7 stagioni caricate, confronto su 2021-2526). Numeri ricalcolabili
dai 2 run `fase52_router3` in `runs.jsonl` (vecchio commit d667d2f4, nuovo
commit corrente).

**Riproducibilità.** `python scripts/_gen_cache.py` (rigenera la cache Serie A
dallo snapshot corretto) → `python scripts/_run_fase52_router3.py`. Le analisi
2021+ (immutate) non richiedono ri-esecuzione: la bit-identità dei dati lo
garantisce.

---

## Fase 75 — Spremere il 2017-19: il motore validato su 2.280 partite vergini (e il θ che cresce nel tempo)

**Obiettivo.** Richiesta utente: trattare il blocco 2017-19 (apertura REALE
1X2+O/U dopo la Fase 73; chiusura O/U stimata) come terreno di caccia e
spremerlo in ogni direzione — da solo, con altri dati, come input di modelli —
per tirarne fuori conclusioni.

**L'osservazione che apre tutto.** Il motore market-implied **non richiede
training** (inverte le quote della partita stessa): le 6 lega-stagioni
1718/1819 × 3 leghe (2.280 partite con apertura 1X2+O/U **tutta reale**) sono
un **test-set vergine** mai visto da nessun fit del progetto. In più: la
chiusura 1X2 del 1819 è reale (Pinnacle) → l'encompassing (Fase 16) si può
estendere a una stagione nuova con dati veri; e la chiusura O/U stimata può
fare da benchmark **dichiarato**.

**Esperimenti** (`scripts/_run_fase75_squeeze_2017_19.py`, 1 run
`source=fase75_squeeze_2017_19`, B=10.000):

**A. Il motore market-implied dall'apertura, su dati mai visti — VALIDATO.**
Inversione apertura → (λ,μ) → `price_markets` (Poisson e double-Poisson
θ=1.225 del router, qui puro out-of-sample) su 20 mercati Tier 1, vs baseline
in-sample:
- **MI-Poisson batte la baseline su 17/20 mercati con CI conclusivo** (media
  20 mercati 0.5618 vs 0.5900; picchi: home_win −0.0967, scarto≥2 −0.0739,
  total-squadra −0.036…−0.060). Su partite mai viste, cross-lega, condizionato
  alla SOLA apertura del venerdì. È la conferma out-of-sample più forte mai
  ottenuta del risultato Fase 26/41 — e copre (per il 2017-19) la pista #4
  (market-implied mai backtestato multi-mercato su Premier/Liga).
- Le 3 eccezioni replicano pattern noti: **pari/dispari** (+0.0035, l'unico
  mercato dove la baseline vince: quasi-casuale, come in Fase 26), mg_2_3 e
  over_0.5 nel rumore.

**B. La sotto-dispersione θ: il SEGNO regge, il LIVELLO no — e cresce nel
tempo.** θ fittato sui tassi dell'apertura per lega-stagione:

| lega | 1718 | 1819 | (riferimento 2019+: Fasi 52/53) |
|---|--:|--:|---|
| Serie A | 1.104 | 1.157 | 1.218 (open) / 1.225 (close) |
| Premier | 1.050 | 1.159 | 1.069 (close) |
| La Liga | **0.950** | 1.160 | 1.097 (close) |

- θ>1 in 5/6 lega-stagioni (l'unica eccezione: Liga 1718, 0.95): il segno
  della sotto-dispersione è **quasi universale** anche su dati mai visti.
- Ma il **livello** θ=1.225 del router NON trasferisce: la dp con θ fisso
  **peggiora** conclusivamente su over_1.5/mg_0_1 (+0.0037) e non migliora
  quasi nulla (media dp 0.5628 vs Poisson 0.5618) — sovra-affila tassi che
  qui sono meno sotto-dispersi.
- **Osservazione NUOVA**: θ cresce monotonicamente nel tempo in tutte e 3 le
  leghe (1718 ~1.03 medio → 1819 ~1.16 → 2019+ ~1.1-1.22). Non è un artefatto
  apertura/chiusura (il θ_open 2019+ della Serie A era 1.218, ben sopra il
  1.13 dell'apertura 2017-19). Ipotesi: le linee diventano più informative
  col tempo (mercati più liquidi/algoritmici) → tassi più precisi → residuo
  più sotto-disperso. Da ri-verificare tra qualche stagione.

**C. Il DC contro la chiusura STIMATA (benchmark dichiarato, 1819 SA).**
Gap +0.0141 [−0.0017,+0.0300]: direzione coerente col gap noto ma non
conclusivo (1 stagione) e **gonfiato per costruzione** — la stima è fatta di
informazione di mercato (apertura+movimento 1X2), quindi il confronto è
parzialmente circolare. Dichiarato; mai ROI su questo benchmark.

**D. Encompassing esteso al 1819: α\*=0 anche qui — perfino contro la stima.**
- **D1 (dato REALE)**: blend α·DC+(1−α)·closing Pinnacle vero sull'1X2 1819:
  **α\*=0.00** (DC 0.9721, mercato 0.9444). La Fase 16 (α\*≈0 sul 2021+) si
  replica su una stagione mai usata, con closing di un singolo book sharp.
- **D2 (STIMA)**: blend α·DC+(1−α)·chiusura stimata sull'O/U 1819:
  **α\*=0.00**. Il DC non aggiunge nulla nemmeno alla nostra RICOSTRUZIONE
  della chiusura — che è fatta solo di apertura+movimento 1X2. Lettura
  onesta: il tetto informativo del DC è così stringente che perfino un
  surrogato del mercato lo ingloba completamente.

**Lezione/cosa ne consegue.**
1. Il **motore market-implied è la cosa più robusta del progetto**: 17/20
   mercati con CI su 2.280 partite vergini cross-lega, dalla sola apertura.
   Se un giorno servirà prezzare mercati sui gol senza chiusura, l'apertura
   basta (conferma indipendente della Fase 52 "l'open affinato vale la
   chiusura grezza" — qui senza nemmeno affinare).
2. Il **θ del router va trattato come per-contesto** (lega × epoca), non come
   costante: fuori dalla Serie A 2019+ meglio Poisson o θ ritarato. Rafforza
   la Fase 53 (θ decresce con la liquidità) e aggiunge l'asse temporale.
   → aggiornata la voce dp nella rosa (PANCHINA).
3. Il **pareggio/dispari resta imprevedibile ovunque** (replica indipendente).
4. **α\*=0 è ormai un fatto trans-epoca**: 2021+ (Fase 16), 1819 reale (D1),
   perfino vs una stima (D2). Nessun blend DC+mercato ha mai avuto senso.

### 📐 Il modello in dettaglio

Nessuna matematica nuova: composizione di formule esistenti su dati nuovi.
- Inversione e pricing: `implied_lambda_mu` + `price_markets` (Fasi 24/26/44/52),
  ρ=−0.06, con `dp_theta ∈ {None, 1.225}`; per il pricing niente φ35
  (`phi0=0`) per isolare l'effetto della sola marginale (Poisson vs dp).
- θ per lega-stagione: `fit_theta` (Fase 51/52) = MLE di
  `M = dp(λ;θ) ⊗ dp(μ;θ)` con correzione ρ sui punteggi bassi, bounded
  [0.6, 1.8]. **Perché i valori escono più bassi del 1.225**: θ misura quanto
  i gol sono meno dispersi di una Poisson DATI i tassi; con tassi meno
  precisi (apertura 2017-19, mercati meno liquidi di allora) una parte della
  varianza dei gol è spiegata dall'errore dei tassi → sotto-dispersione
  residua minore. Il trend temporale (1718→1819→2019+) è coerente con linee
  sempre più informative.
- Baseline in-sample: `p = frequenza dell'evento nella (lega, stagione)` —
  stessa convenzione dichiarata del backtest core.
- Encompassing: `p(α) = α·p_DC + (1−α)·p_mercato` (rinormalizzato sull'1X2),
  griglia α∈{0,0.05,…,1}, log-loss sugli esiti reali (blend lineare, come
  Fase 16).
- Numeri ricalcolabili dal run `fase75_squeeze_2017_19` in `runs.jsonl`.

**Riproducibilità.** `python scripts/_gen_cache.py 1819` (per C/D) →
`python scripts/_run_fase75_squeeze_2017_19.py` (~20s, offline).

---

## Fase 76 — Il motore market-implied trasferisce cross-lega ANCHE sulla chiusura

**Obiettivo.** Chiudere la pista #4 (PISTE.md): il market-implied — il motore
più forte del progetto — era backtestato multi-mercato SOLO in Serie A (Fase
26: batte il DC-da-gol su 13/14 e la baseline su 13/14). La Fase 75 l'ha
validato sul 2017-19 dall'APERTURA (2.280 partite vergini). Mancava il tassello
naturale: le stesse 20 famiglie di mercati sulla **chiusura** di Premier e
Liga, dove le Fasi 26/41 non erano mai arrivate.

**Domanda dell'utente sulle stagioni pre-2021.** Il market-implied non richiede
training: la finestra è limitata solo dalla disponibilità della chiusura O/U
reale = **2019-20 in poi** (verificato: 1718/1819 hanno chiusura O/U a 0%, il
buco della Fase 73; dal 1920 è 100%). Quindi il test è esteso a **1920-2526 (7
stagioni)** su tutte e 3 le leghe — il 2019-20 era escluso dalla Fase 26 solo
per convenzione. Il 2017-19, privo di chiusura reale, resta coperto
dall'apertura nella Fase 75.

**Cosa abbiamo fatto** (`scripts/_run_fase76_mi_crossleague.py`, riusa ESATTO
le funzioni della Fase 26 → numeri 1:1; 3 run `source=fase76_mi_crossleague`).
Per ogni lega: inversione chiusura 1X2+O/U → (λ,μ) → matrice DC → ogni mercato,
vs DC-da-gol vs baseline in-sample; walk-forward per stagione, bootstrap
appaiato B=10.000, ρ=−0.06 (la costante universale, **non ritarata**).

**Risultato — il motore trasferisce, identico, su tutte e 3 le leghe:**

| lega | batte DC-da-gol | (di cui CI<0) | batte baseline | ris. esatto Δ vs DC |
|---|:-:|:-:|:-:|--:|
| Serie A (1920-2526) | **13/14** | 12 | **13/14** | −0.0320 |
| Premier League | **13/14** | 13 | **13/14** | −0.0302 |
| La Liga | **13/14** | 11 | **13/14** | −0.0265 |

- **Stesso identico esito della Fase 26** (13/14 in Serie A), replicato su due
  leghe mai testate multi-mercato. I guadagni maggiori sui mercati ricchi:
  risultato esatto (−0.027…−0.032), multigol, total-squadra 1.5 (−0.010…
  −0.013) — le stesse famiglie della Fase 26.
- **L'unico mercato che NON cede, in tutte e 3 le leghe: pari/dispari**
  (`odd_total`, Δ≈+0.0001, l'unico dove la baseline pareggia o vince). È la
  quarta replica indipendente dello stesso fatto (Fasi 26/41/75): la parità dei
  gol è quasi-casuale, il market-implied non ci aggiunge nulla — un mercato da
  non prezzare mai con pretese.
- Il tutto **senza ritarare una sola costante** (ρ=−0.06 identico): conferma
  che la lega-specificità del motore sta solo negli input (le quote), non nella
  struttura. Il θ del router, invece, NON si trasferisce (Fase 75): la
  distinzione regge — la MATRICE è universale, la sotto-dispersione delle
  MARGINALI è per-contesto.

**Lezione/cosa ne consegue.**
1. **Pista #4 CHIUSA, positiva.** Il market-implied è ora validato multi-mercato
   su 3 leghe × chiusura (Fase 76) + 3 leghe × apertura (Fase 75) + Serie A a
   fondo (Fase 26): ogni asse coperto. È, con ampio margine, il pezzo più
   robusto e trasferibile del progetto.
2. **Promozione nella rosa**: market-implied → ⚽ titolare anche su Premier/Liga
   (era ⬜ mai testato multi-mercato, nota ✱1 di PANCHINA). La ri-taratura
   temuta non serviva: la struttura è davvero universale.
3. Resta il fatto trans-mercato: **il pari/dispari è irriducibile** ovunque.
4. Nessun edge di scommessa qui: il market-implied RIPRODUCE il mercato dove
   c'è la quota (over_2.5, 1X2 sono ancoraggi) e lo estende ai mercati NON
   prezzati — è un motore di *pricing coerente*, non un battitore del mercato
   (α\*=0, Fase 16/75). Il valore è prezzare mercati senza quota, non scommettere.

### 📐 Il modello in dettaglio

Nessuna matematica nuova: identica alla Fase 26/44, applicata a dati nuovi.
- Inversione: `implied_lambda_mu(pH, pD, pA, pOver, ρ)` (market_implied.py) =
  cerca (λ,μ) che riproducono le prob 1X2 devigate + P(Over 2.5) devigata,
  ρ=−0.06 sulla correzione dei punteggi bassi.
- Derivazione: `score_matrix(λ,μ,ρ)` → `derive_markets(M)` = somme sulle celle
  della matrice per ogni mercato (over N.5, multigol, total-squadra, ris.
  esatto = −log M[hg,ag]).
- Confronto: Δ = LL(market-implied) − LL(DC-da-gol), dove il DC-da-gol usa
  (exp_home_goals, exp_away_goals) del backtest ufficiale (δ per lega: SA 0.23,
  PL 0.33, Liga 0.22). Bootstrap appaiato sui per-riga.
- **Perché over_2.5 e 1X2 non contano come "vittorie"**: sono gli ancoraggi
  dell'inversione (il motore li riproduce per costruzione) → esclusi dal conteggio
  (14 mercati non-ancora sui 20 totali). **Perché pari/dispari non migliora**:
  dipende dalla parità di X+Y, che una matrice Poisson-DC cattura solo al primo
  ordine; è quasi-indipendente dai λ,μ → né il mercato né il modello battono la
  frequenza. Numeri ricalcolabili dai 3 run `fase76_mi_crossleague`.

**Riproducibilità.** `python scripts/_run_fase76_mi_crossleague.py` (3 leghe ×
7 stagioni; ~10 min per il walk-forward DC + bootstrap — se serve, una lega per
volta via `run_league(lega, rng)`).

---

## Fase 77 — Il nome onesto: da «Polymarket Oracle» a «Football Oracle»

**Decisione (utente).** Rinominare il progetto in **Football Oracle**. Non è
cosmesi: fissa per iscritto una conclusione strategica maturata nelle Fasi
14-76, così non si perde tra le sessioni.

**Il ragionamento.** Il nome «Polymarket Oracle» sottintendeva un sistema per
**battere un mercato di scommesse**. Ma il progetto ha dimostrato, in modo
ripetuto e conclusivo, che questo **non è possibile** con un modello su dati
pubblici pre-partita contro un book affilato: α\*=0 ovunque (Fase 16, replicato
trans-epoca nella Fase 75, perfino contro una chiusura stimata), CLV negativo
(Fase 14), adverse selection (Fase 20), ROI negativo. La chiusura di Pinnacle è
uno dei prezzi più efficienti che esistano; il nostro modello, nel migliore dei
casi, la eguaglia. Un edge di scommessa, se esiste, **non sta nel modello** ma
in informazione nuova/veloce (formazioni, live) o in un avversario meno
efficiente (book soft, exchange, prediction market) — problemi di *dati e
accesso*, non di matematica.

**Cosa il progetto È, invece** (e il nome ora lo dice): un **oracolo di
probabilità sul calcio**. Dato ciò che il mercato affilato prezza (1X2+O/U), il
motore market-implied restituisce probabilità coerenti e validate per ~20
mercati — inclusi quelli che il book NON quota — su 3 leghe, apertura e
chiusura, 2017-2026 (Fasi 26/75/76). Il valore non è battere qualcuno: è
**stimare bene ogni evento**, con l'errore atteso dichiarato e senza promesse.

**Cosa è cambiato tecnicamente.** Solo i riferimenti al NOME del progetto
(`README`, `docs/DIARIO`, `src/__init__.py`, `pyproject.toml` →
`football-oracle`). I riferimenti a **Polymarket come piattaforma** (il progetto
si dichiara indipendente da Polymarket/bookmaker/exchange) restano: sono
corretti. Gli URL GitHub `.../Polymarket-oracle/...` restano invariati: GitHub
reindirizza dal vecchio nome al nuovo dopo il rename lato Settings, quindi
funzionano in entrambi gli stati (cambiarli prima del rename li romperebbe).
**Il rename del repository GitHub vero e proprio va fatto dall'utente**
(Settings → General → Repository name): non è automatizzabile dagli strumenti
di sessione.

**Lezione.** Un nome onesto è parte della disciplina «onestà sui limiti»
(§1.6): «Polymarket» prometteva un edge che i dati non danno. «Football Oracle»
dice cosa la cosa fa davvero. Il tool pratico (`predict.py`) resta la
culminazione naturale, da fare a valle del lavoro di ricerca (scelta utente).

### 📐 Il modello in dettaglio

Nessuna matematica (decisione di naming): il modello è invariato. La convenzione
del progetto (Fase 15 e Fase 84 tengono il blocco 📐 anche negli audit e nelle
fasi non-matematiche, §2-bis) vuole comunque il rimando: le formule del motore
restano quelle delle Fasi 16 (encompassing, α\*) e 24/26 (inversione delle quote
→ λ,μ → matrice DC → ogni mercato). Il rename non tocca `src/`: cambia solo le
stringhe-nome (`README`, `pyproject.toml`, `src/__init__.py`).

---

## Fase 78 — Test prospettico 2026-27 (giornata 1): impostato, da completare

**Obiettivo (utente).** Simulare come ci comporteremmo di fronte al primo turno
2026-27 di Serie A/Premier/Liga, e **scrivere nel repo che il test si ripeterà
più avanti**. È il gold standard: previsioni congelate PRIMA del calcio
d'inizio, scorate DOPO — nessun senno di poi (il progetto insegue dati
prospettici dalla Fase 14).

**Cosa si è potuto fare oggi (2026-07-23) e cosa no — onestamente.** Dalla
sessione di sviluppo `WebFetch` è **bloccato del tutto** (403 anche su
Wikipedia, bug noto) e i siti di quote bloccano i bot: **non** è possibile
assemblare da qui, in modo affidabile, né i calendari ufficiali 2026-27 (gli
snippet di ricerca su stagioni future sono speculativi — mescolavano squadre di
Championship) né le quote decimali reali. Costruire un test prospettico su
fixture/quote inventate lo renderebbe inutile → **non fatto** (disciplina
«onestà sui limiti», §1.6).

**Cosa è stato congelato.** Una **anteprima illustrativa** (non il test scorato):
la previsione del **DC-da-solo** (Modello 1, `scripts/_run_prospettico_2627.py`,
config per-lega) per 7 partite Premier plausibili tra squadre presenti nei
nostri dati — es. Newcastle–Liverpool 34/27/40, O2.5 64%, GG 68%. Congelata in
`experiments/prospettico_2026_27_dc.csv` con i limiti dichiarati (fixture non
ufficiali; dati fermi a 2025-26 → forze vecchie di un'estate di mercato; niente
quote → niente Modello 2). Serie A/Liga: calendari non reperiti → slot vuoti.

**Il protocollo del test vero** vive in
`experiments/prospettico_2026_27.md` (stato: **APERTO**): per ciascuna lega,
giornata 1, congelare M1 (DC) + M2 (market-implied dalle quote di chiusura
reali) prima del kickoff, poi scorare M1/M2/baseline sui risultati (log-loss/
Brier/calibrazione) e registrare un run `prospettico_2627`. Le **quote reali
vanno raccolte vicino al calcio d'inizio** per un canale che funzioni (GitHub
Actions, sessione browser Cowork, o bundle manuale). Checklist «da ripetere» in
§5 del file.

**Lezione.** L'aspettativa dichiarata: il DC-da-solo sarà battuto dal mercato
(α\*=0 ovunque); il valore del test non è vincere ma **misurare** quanto perde e
se resta calibrato su dati mai visti — e mostrare, con le quote, che il
market-implied riproduce il mercato ed estende ai mercati non quotati. Nessun
ROI simulato. È anche il primo uso "vivo" che espone il debito del **passo 2**:
il tool `predict.py` va reso per-lega (config, selezione automatica del modello)
prima di un uso pratico serio. *(Il Modello 1 di `predict.py` è stato reso
per-lega nella Fase 83-bis — vedi sotto.)*

### 📐 Il modello in dettaglio

Nessuna matematica nuova: `DixonColesModel` (config ufficiale per-lega,
`LEAGUE_CONFIGS`) + `price_markets(dp_theta=DP_THETA_DC)` (router v3, Fase 52),
identici a `predict.py`. Le previsioni sono `expected_goals(home, away)` →
matrice → mercati, con as_of 2026-08-15 (prima del primo turno). Nessun run in
`runs.jsonl` finché non ci sono i risultati (un'anteprima non è un esperimento
scorato). Numeri riproducibili: `python scripts/_run_prospettico_2627.py`.

---

## Fase 79 — Studio dedicato Premier/Liga: le prime leve per-lega (φ35 e congestione)

**Obiettivo (utente).** Entrare nel dettaglio delle due leghe non-Serie A:
studiarne a fondo i dati, ragionare su quali valori/modelli usare, e iniziare i
test per-lega. Nasce il **quaderno di studio dedicato**
`docs/STUDIO_PREMIER_LIGA.md` (dati, differenze strutturali, stato dei test,
piano ragionato — da aggiornare a ogni fase che tocca PL/Liga).

**Ragionamento / scelta delle leve.** Dopo la Fase 76 il motore market-implied
è titolare ovunque; il lavoro per-lega utile è decidere **leva per leva** cosa
vale fuori dalla Serie A. Dalla rosa (PANCHINA), le due celle ⬜ più mature:
1. **φ35 sul path DC** (nota ✱2: il draw-bias di mercato non si replica in
   Premier → la φ potrebbe avere segno diverso — mai fittata lì);
2. **covariate di congestione** `rest_full`/`midweek` (colonne pronte dalla
   Fase 59, mai testate fuori SA — "il test per-lega più facile in lista").

**EDA preliminare** (`_run_fase79_eda_pl_liga.py`, 3 run): tre fatti nuovi.
- **Pareggio per fascia di equilibrio** (|pH−pA| devig, quartili): il
  sotto-prezzo dei pareggi equilibrati esiste in Serie A (reale−mercato
  **+0.032**) e in Liga (**+0.022**), e NON esiste in Premier (**−0.009**,
  semmai sovra-prezzo — coerente con w_D=0.93 e ROI pari-equilibrio −5.4%
  della Fase 53). Tre leghe, tre repliche: *il pareggio è dove i mercati
  differiscono di più*.
- **Congestione**: la Premier è un'altra categoria — riposo ≤3g nel 21.6%
  delle partite (SA 14.0%), **36.3% a dicembre** (Boxing Day; SA 15.0%),
  midweek europeo 14.2%. Se la covariata paga da qualche parte, è lì.
- **γ_t per stagione**: Liga alto e STABILE (0.18–0.34, perfino nel COVID);
  Premier VOLATILE (0.29 → 0.01 nel 2021 → 0.29 → 0.06 nel 2425 → 0.22).

**Cosa abbiamo fatto** (`_run_fase79_leve_per_lega.py`, 48 backtest
walk-forward: 2 leghe × 4 varianti × 6 stagioni 2021→2526, config ufficiale
per-lega, bootstrap appaiato B=10.000, 8 run `fase79_leve_per_lega`).
Aspettativa dichiarata prima: su Premier φ0 potrebbe uscire ≈0; in SA le
covariate erano rumore (−0.0004), qui l'esposizione è maggiore.

**Risultato — quattro bocciature pulite (Δ log-loss 1X2 vs base per-lega):**

| leva | Premier (Δ; P mig.) | La Liga (Δ; P mig.) |
|---|--:|--:|
| φ35 equilibrio-pareggio | +0.0006 (7%) | +0.0002 (43%) |
| covariata `rest_full` | +0.0005 (9%) | +0.0003 (26%) |
| covariata `midweek` | +0.0001 (38%) | +0.0001 (39%) |

Ma il risultato vero è **strutturale, nei parametri fittati**:
- **Premier: φ0 sbatte sul bound ZERO in 4/6 stagioni** (media 0.052). Il
  deficit-pareggio del DC nelle partite equilibrate — il meccanismo della
  Fase 35 — **non esiste in Premier**: il modello lì i pareggi equilibrati li
  SOVRA-stima già (reale 0.246 vs base 0.268), e la φ35 spinge nel verso
  sbagliato (0.277). La "firma inglese" (23.4% di pareggi) è già oltre la
  Poisson.
- **La Liga: il fit è quasi IDENTICO alla Serie A** (φ0≈0.39, κ≈4.1 vs
  φ0≈0.39, κ≈3.6 della Fase 35) e il deficit è reale (equilibrate: reale
  0.321 vs base 0.294) — ma la φ **sovra-corregge** (0.344) e il log-loss non
  paga (+0.0002; κ sul bound 5.0 in 4/6 stagioni = fit instabile).
- **Congestione**: β_rest_full Premier ha direzione sensata (−0.019, negativo
  5/6 stagioni: riposo corto → meno gol) ma peggiora out-of-sample; in Liga
  cambia segno anno per anno (+0.053…−0.040). Il **β_midweek stabile della
  Serie A (−0.020, 6/6) NON si replica**: Premier −0.001 (segno alterno),
  Liga +0.008 (segno opposto). La covariata-congestione è rumore ovunque.

**Lezione / cosa ne consegue.**
1. **Il deficit-pareggio del DC è un tratto delle leghe latine** (SA e Liga:
   fit sovrapponibili), assente in Premier. Ogni leva-pareggio (φ35, strategie
   draw-bias, ricalibrazioni w_D) va tenuta **lontana dalla Premier** — terza
   conferma indipendente (F53 mercato, EDA 79 frequenze, F79 fit del modello).
2. **Anche dove il deficit c'è (Liga), correggerlo non paga** — come in SA
   (F35: −0.0007, CI include 0). Il tetto informativo si conferma universale.
3. La congestione resta un **non-segnale** anche nella lega più congestionata
   d'Europa: il fit pesato nel tempo la assorbe già. Chiude il candidato
   "più facile" della lista per-lega.
4. Operativo: su PL/Liga il listino si prezza col **market-implied liscio**
   (niente θ, niente dp_lvl, niente φ35 sul path DC); il DC fallback resta
   con la sola config `LEAGUE_CONFIGS`. Resta ⬜ solo la φ35 della
   famiglia-pareggio DENTRO il router market-implied (test diverso: lì la φ
   agisce sulla matrice dai tassi del mercato) — ma il prior dopo questa fase
   è sfavorevole, specie in Premier.

### 📐 Il modello in dettaglio

Nessuna matematica nuova; formule verificate sul sorgente.
- **φ35** (`dixon_coles._fit_draw_balance`): inflazione della diagonale
  per-partita `φ(λ,μ) = φ0·exp(−κ·|λ−μ|)`, fittata in verosimiglianza con
  bound φ0∈[0,2], κ∈[0,5] (L-BFGS-B, start 0.1/1.0). "φ0=0.000 in 4/6
  stagioni Premier" = ottimo sul bound INFERIORE: la likelihood inglese non
  vuole alcun boost-pareggio (il vincolo φ0≥0 impedisce il segno negativo che
  i dati chiederebbero — il deficit lì è invertito). "κ=5.000 in Liga" =
  bound SUPERIORE: boost concentrato su |λ−μ|→0; a κ=5 il boost al
  |λ−μ| mediano (~0.6) è già φ0·e^{−3}≈0.02, quasi nullo → φ0 e κ sono
  mal-identificati congiuntamente (piatta la likelihood), da cui il fit
  instabile e la sovra-correzione osservata nelle equilibrate.
- **Covariate** (`dixon_coles._cov_term`): contributo al log-tasso
  `log λ += Σ_k β_k(z_casa−z_ospite)`, `log μ` segno opposto; z standardizzati
  (media/σ del training), NaN→0 neutro. `rest_full` = giorni di riposo dal
  calendario completo (identity), `midweek` = dummy gara europea
  infrasettimanale. I β citati sono un fit a inizio stagione per lega
  (6 per lega, `_fitted_params`).
- **Perché Δ>0 con β "sensato" (Premier rest_full)**: β=−0.019 su z-score ⇒
  effetto ~±2% sui tassi per 1σ di riposo; su 2.280 partite il guadagno vero
  (se c'è) è ≪ del rumore di stima del β walk-forward — la covariata aggiunge
  varianza di parametro senza abbastanza segnale (stesso meccanismo delle
  Fasi 4c/13/33).
- Δ e CI: bootstrap appaiato per-riga B=10.000 sulle stesse partite
  (`_boot`), identico alle Fasi 35/56/57. Numeri ricalcolabili dai run
  `fase79_eda_pl_liga` (3) e `fase79_leve_per_lega` (8).

**Riproducibilità.** `python scripts/_run_fase79_eda_pl_liga.py` ·
`OMP_NUM_THREADS=1 python scripts/_run_fase79_leve_per_lega.py` (~40 min,
cache `outputs/db79_*.csv`).

---

## Fase 80 — La catena GG/NG del market-implied su Premier/Liga: la φ35 paga in Liga (CI<0), il nudge no

**Obiettivo.** Test C dello studio per-lega (STUDIO_PREMIER_LIGA §5): la voce
#1 della panchina — la miglior stima GG/NG del progetto (market-implied →
nudge-μ knee34 → φ(|λ−μ|), Fase 50: GG 0.6810, Δ −0.0010, P 98%) — ha la
promozione condizionata proprio a "il guadagno riappare sul fronte per-lega di
Premier/Liga". Il GG/NG è l'unico mercato senza quote nei dati (nessun tetto di
efficienza dimostrato, §1.8): ogni guadagno lì è spendibile.

**Ipotesi dichiarate PRIMA** (dal prior della Fase 79): su Premier la catena
non pagherà (φ0 del path DC fitta zero, il deficit-pareggio non esiste); su
Liga può pagare (fit ≈ Serie A). La Serie A è rifatta sulla STESSA finestra
(1920→2526, chiusure reali post-Fase 73) come riferimento pulito.

**Cosa abbiamo fatto** (`_run_fase80_ggng_mi_league.py`, replica esatta del
ramo devig=prop della Fase 50: inversione chiusura → λ,μ → varianti tau /
phi35 / k34 / phi35+k34, parametri leave-future-out, bootstrap B=10.000;
12 run `fase80_ggng_mi_league`, 3 leghe × 6 stagioni test 2021→2526, n=2280
per lega).

**Risultato (Δ GG/NG vs motore liscio; * = CI95 esclude lo zero):**

| variante | Serie A | Premier | La Liga |
|---|--:|--:|--:|
| φ35 | −0.0003 (P 95%) | +0.0001 (P 16%) | **−0.0006 [−0.0011,−0.0001] (P 99%)*** |
| k34 | −0.0012 (P 97%) | −0.0002 (P 62%) | **+0.0008 [+0.0000,+0.0016] (P 2%)** peggiora* |
| φ35+k34 | −0.0014 (P 97%) | −0.0002 (P 62%) | +0.0002 (P 28%) |

Costanti fittate (medie LFO): φ0 SA 0.16 / PL 0.17 (instabile 0.68→0, κ sui
bound) / **Liga 0.32 (stabile 0.30-0.47, κ≈2.9)**; boost-μ alla 38ª: SA 0.976,
PL 1.097, **Liga 0.915** (sotto 1!).

**Lettura — tre leghe, tre catene GG/NG diverse:**
1. **Serie A**: la combo φ35+k34 si RICONFERMA sulla finestra pulita
   (−0.0014, P 97%; era −0.0010 P 98% in Fase 50) — resta la miglior stima
   GG/NG, resta in panchina (CI sfiora lo zero).
2. **La Liga — il primo risultato per-lega conclusivo fuori dalla Serie A**:
   la φ35 DA SOLA batte il motore liscio con CI95<0 sul test pre-dichiarato
   (GG −0.0006 [−0.0011,−0.0001]). Ma il **nudge k34 in Liga PEGGIORA con
   CI>0**: il profilo di fine stagione del tasso-ospite è INVERTITO (boost-38ª
   0.915: in Liga l'ospite segna MENO nel finale, non di più) — la costante
   knee34 della Serie A applicata lì spinge nel verso sbagliato, e rovina
   anche la combo. Catena Liga = **φ35 e basta** (φ0≈0.32, κ≈2.9).
3. **Premier**: nulla funziona (tutte le P 16-62%, fit sui bound) —
   quarta conferma che ogni leva-pareggio è fuori posto in Inghilterra.
   Catena Premier = **motore liscio**.

**Onestà (multiple testing).** Il CI<0 della Liga è sul mercato-headline
(GG/NG) di un'ipotesi direzionale dichiarata prima, su una lega quasi vergine
(2 fasi di test, non 50) — le condizioni migliori possibili. Resta il PRIMO
risultato su questa lega: prudenza = niente config finché non riappare su
stagioni nuove (2026-27+) o il tool diventa per-lega. Stessa etichetta del δ
Serie A alla Fase 7: "molto probabile, adottabile, non ancora inciso".

**Lezione / cosa ne consegue.**
1. Il principio 8 ("valuta PER MERCATO") ora ha anche la dimensione PER-LEGA:
   la stessa catena di leve si assembla in modo diverso per lega — SA
   φ35+k34, Liga φ35, PL liscio. Le COSTANTI divergono perché i meccanismi
   sottostanti divergono (deficit-pareggio latino; profilo stagionale
   dell'ospite di segno opposto tra SA/PL e Liga).
2. Il profilo di fine stagione INVERTITO della Liga (0.915 vs 1.097 PL) è un
   fatto nuovo, coerente col γ_t alto e stabile (EDA 79): in Spagna il
   vantaggio-casa NON crolla nel finale come in Serie A (Fase 30) — anzi.
3. Aggiornata la rosa (PANCHINA): φ35-Liga in panchina ALTA (CI<0, condizioni
   di promozione scritte), combo e k34 bocciati fuori SA, righe per-lega.

### 📐 Il modello in dettaglio

Formule identiche alle Fasi 39/48/50 (verificate sul sorgente), applicate
per-lega; nessuna matematica nuova.
- **φ35 di mercato** (`market_implied.fit_balance_phi` / `balance_phi`):
  `φ(λ,μ) = φ0·exp(−κ·|λ−μ|)` con (λ,μ) INVERTITI dalla chiusura devigata
  (moltiplicativa, ρ=−0.06), fittata per verosimiglianza dei pareggi sulle
  stagioni passate (bound φ0∈[0,2], κ∈[0,5]), applicata come `diag_inflation`
  alla `score_matrix`. **Perché φ0_Liga=0.32**: a |λ−μ|=0 i pareggi liscio
  sono gonfiati del 32%·(quota diagonale) — è il deficit-pareggio latino
  misurato sui tassi del MERCATO, stabile in 5/6 fit (0.30-0.47; il primo fit,
  0.098, ha una sola stagione di dati). **Perché in PL il fit è instabile**
  (0.68→0.00, κ sul bound 5): likelihood quasi piatta = nessun segnale, come
  il φ0=0 del path DC (Fase 79).
- **Nudge k34** (`_fit_nudge`, MLE Poisson con offset ln μ): base
  `[1, s, tail34]` con `s=(g−19.5)/18.5`, `tail34=max(0,g−34)/4`;
  boost-38ª = `exp(X(38)·ĉ)`. **Perché 0.915 in Liga**: i coefficienti
  fittati sui dati spagnoli dicono che il tasso-ospite di fine stagione va
  RIDOTTO ~8.5% (in SA/PL alzato ~0-10%) — coerente col vantaggio-casa
  spagnolo che non crolla nel finale (γ_t stabile, EDA 79). Applicare al
  test una riduzione fittata sul passato produce Δ **+0.0008 CI>0**: il
  profilo esiste ma è troppo rumoroso per pagare out-of-sample sul GG.
- **Metriche per-riga** (`_row_ll` = Fase 50): GG = binaria su `btts` della
  matrice; Δ e CI da bootstrap appaiato per-riga (B=10.000, seed 80).
  Numeri ricalcolabili dai 12 run `fase80_ggng_mi_league`.

**Riproducibilità.** `python scripts/_run_fase80_ggng_mi_league.py`
(~2 min con cache `outputs/implied_rates80_*.csv`, ~10 senza).

---

## Fase 81 — Mega-sweep delle costanti del market-implied per-lega: le curve di risposta complete (e il ribaltamento del router-Liga)

**Obiettivo (utente).** "Spremere questi dati con un mega backtest che copra
quante più opzioni possibili per un singolo modello, assegnando vari valori a
una singola costante." Il modello giusto è il TITOLARE (market-implied): senza
fit walk-forward costosi si può tracciare la **curva di risposta completa** di
ogni costante, per lega e per mercato — decine di valori invece dei 2-3 punti
delle fasi passate. Le curve dicono: dove sta l'ottimo per lega, quanto è
piatta la valle (= quanto conta la costante), e se le leghe chiedono numeri
diversi (§7).

**Il metodo** (`_run_fase81_mega_sweep_mi.py`, 12+2 run): 4 assi × 3 leghe ×
6 mercati (1X2, GG, pareggio, ris. esatto, multigol, O/U), stagioni 1920→2526
(test 2021→2526, n=2280/lega), **63 varianti/lega** (11 ρ + 10 θ + 37 φ0×κ +
5 knee, contate dagli assi qui sotto):
- **ρ** ∈ {−0.22…+0.02} (11 valori, con RI-INVERSIONE delle quote per ogni ρ:
  coerenza inversione↔matrice);
- **θ** double-Poisson ∈ {1.00…1.50} (10);
- **φ0×κ** ∈ {0…0.7}×{0.5…5} (37 combo: la coppia neutra + 6×6);
- **knee** del nudge-μ ∈ {25…37} (5, coefficienti sempre leave-future-out).
Onestà della selezione: il minimo della curva è selezione in-sample; per ogni
asse×mercato si valuta anche il **selettore walk-forward "lfo"** (sceglie il
valore col log-loss migliore sulle sole stagioni passate). Solo un guadagno
che sopravvive al selettore è reale.

**Risultato 1 — la Premier è GIÀ al suo ottimo su ogni asse.** Le valli
premier sono centrate esattamente sul riferimento: ρ*=−0.06/−0.04, θ*≈1.05
(nulla, P≤91% in-sample e il selettore peggiora), φ*=(0,0), knee*=none. Dopo
63 varianti: **il motore liscio È il modello Premier** — la sesta conferma,
stavolta esaustiva, che il mercato più liquido non lascia margini nemmeno
sulla forma.

**Risultato 2 — Serie A e Liga vogliono θ≈1.2, e per la Liga è un
RIBALTAMENTO.** Le curve latine hanno ottimi interni netti sul risultato
esatto: θ*=1.2-1.25 (SA −0.0079, Liga −0.0085, entrambe CI<0 anche col
selettore lfo). Sull'1X2 il log-loss migliora monotono fino a θ=1.5
(sharpening: la chiusura devigata è sotto-confidente, Fase 51-bis — non è
dispersione ma temperatura). In **Liga** anche GG (lfo −0.0025, CI<0) e 1X2
(lfo −0.0023, CI<0): la **Fase 53 aveva bocciato il router-Liga testando il
θ fittato per MLE sui punteggi (1.097) — troppo piccolo**; la griglia mostra
che l'ottimo operativo è ~1.2, come in Serie A (router v3, θ=1.225, dove il
MLE dava 1.205). Lezione: il θ che minimizza il log-loss dei MERCATI non è il
θ che massimizza la verosimiglianza dei PUNTEGGI — in Liga la differenza
(1.097 vs 1.2) decideva il verdetto. Riga della rosa aggiornata: router-Liga
da ❌ a 🪑 alta (θ≈1.2, promozione con le solite condizioni).

**Risultato 3 — il check congiunto ρ×θ (Fase 81-bis) evita un doppio
conteggio.** Le curve univariate suggerivano anche "ρ molto negativo aiuta"
(SA/Liga, fino al bordo −0.22). Ma ρ<0 e θ>1 concentrano ENTRAMBI la matrice:
griglia congiunta ρ×θ (`_run_fase81_joint_rho_theta.py`) → **a θ ottimo, ρ
oltre −0.06 PEGGIORA il risultato esatto** (SA +0.0088, Liga +0.0119) e non
aiuta più l'1X2 (Liga: +0.0014). I guadagni dell'asse ρ erano **θ sotto
mentite spoglie**: si adotta UNA leva (θ), non due; **ρ=−0.06 resta la
costante universale** anche dopo il sweep più ampio mai fatto. (Residuo: sul
solo GG un filo di ρ-in-più aiuta ancora ~−0.0014 — è la stessa massa
diagonale che la φ gestisce più pulitamente, vedi sotto.)

**Risultato 4 — φ e knee: conferme con numeri migliori.** φ-grid sul GG:
Liga (φ0 0.7, κ 0.5) lfo −0.0019 CI<0 (più forte del fit-MLE della Fase 80,
−0.0006: anche qui il MLE sotto-stima la costante operativa; κ piccolo =
boost quasi costante, non solo sulle equilibrate); SA (0.7, 0.5) lfo −0.0013
(P 92%); Premier: (0,0), nulla. Knee: SA k34 GG −0.0012 CI<0 (replica F80);
Liga e Premier: none (il nudge resta solo-SA). Il profilo boost-38ª per lega
conferma la Fase 80: PL ×1.10, SA ~1.0, Liga ×0.92 (fino a ×0.77 con k37).

**Sintesi operativa per lega (costanti del motore, stato dopo la Fase 81):**

| costante | Serie A | Premier | La Liga |
|---|---|---|---|
| ρ | −0.06 (universale) | −0.06 | −0.06 |
| θ router | ⚽ 1.225 (F52, riconfermato: cs* lfo*) | ❌ 1.0 (liscio) | 🪑→ **~1.2** (F81 ribalta F53: cs/GG/1X2 lfo CI<0) |
| φ famiglia-pareggio/GG | ⚽ (F41/44) | ❌ 0 | 🪑 alta (φ0~0.3-0.7, F80/81) |
| nudge-μ (knee) | 🪑 k34 solo GG | ❌ none | ❌ none (profilo invertito) |

### 📐 Il modello in dettaglio

Formule già nel motore (`market_implied.score_matrix`): marginali
double-Poisson mean-preserving `dp_pmf(rate, θ)` (Fase 51: pmf ∝ exp(θ·(k·ln c·rate
− c·rate − ln k!)), rinormalizzata e ri-centrata), correzione τ di
Dixon-Coles con ρ sui punteggi bassi, inflazione diagonale φ. Il sweep
valuta varianti a costanti FISSE: nessun fit per-riga, quindi ogni variante è
un modello legittimo out-of-sample; la selezione onesta è delegata al
selettore lfo (`_lfo_pick`: per la stagione i, argmin del LL medio sulle
stagioni <i, 1920 inclusa; prima stagione → riferimento).
- **Perché il θ "da mercati" ≠ θ "da punteggi"**: la MLE sui punteggi pesa
  tutta la matrice; il log-loss di un mercato pesa solo la partizione
  rilevante. Con code sottili (dp) l'1X2 guadagna anche oltre il θ vero
  (effetto temperatura: la chiusura devigata è sotto-confidente di ~T=1.10,
  Fase 51-bis), mentre il risultato esatto — che vede TUTTE le celle — ha
  l'ottimo interno al θ di dispersione vera (1.2-1.25). Per questo il
  router usa il θ ottimizzato sui mercati (1.225 in SA), non il MLE.
- **Perché ρ e θ si sostituiscono**: per (0,0) il fattore τ è (1−λμρ) →
  ρ<0 ALZA la massa su 0-0/1-1 (diagonale bassa); la dp θ>1 stringe le
  marginali attorno alla media, alzando anch'essa i punteggi bassi quando
  λ,μ<2. Sul GG/pareggio i due effetti quasi coincidono; sul risultato
  esatto no (ρ distorce le code asimmetricamente) — da cui il verdetto del
  check congiunto.
- Δ e CI: bootstrap appaiato per-riga B=10.000, seed 81/8100. Numeri
  ricalcolabili dai run `fase81_mega_sweep_mi` (12) e
  `fase81_joint_rho_theta` (2).

**Riproducibilità.** `python scripts/_run_fase81_mega_sweep_mi.py` (~5 min
con cache inversioni `outputs/implied_rates81_*`; ~15 senza) →
`python scripts/_run_fase81_joint_rho_theta.py` (~2 min).

---

## Fase 82 — Verifica diretta: ma indoviniamo davvero i risultati? (calibrazione e hit-rate su tutti i mercati)

**Domanda (utente).** In tutto il progetto abbiamo confrontato log-loss contro
il mercato — ma i valori predetti sono GIUSTI in assoluto? Indoviniamo gli
esiti, non solo sull'1X2 ma su tutti i mercati? È una domanda diversa e
legittima, mai affrontata in modo sistematico (calibrazione solo a campione:
Fasi 6/10/35).

**Metodo dichiarato prima** (`_run_fase82_verifica_predizioni.py`, 3 run).
Due sensi verificabili di "essere nel giusto":
1. **Calibrazione** — quando diciamo "60%", succede il ~60% delle volte?
   (bias globale p̄−freq; **ECE** su 10 fasce di probabilità);
2. **Hit-rate** — quanto spesso l'esito indicato come PIÙ PROBABILE si
   verifica? (vs baseline "scegli sempre il più frequente", vs mercato).
Avvertenza onesta, scritta prima: per eventi intrinsecamente incerti il
hit-rate non può superare di molto mercato e baseline (se il calcio fosse
prevedibile al 90%, le quote non esisterebbero); la misura giusta per un
oracolo di probabilità è la calibrazione. Verificati: motore liscio, router
per-lega (θ F81), mercato devigato, path DC senza quote — 19 mercati binari +
1X2 + multigol + risultato esatto, 3 leghe × 6 stagioni (n=2280/lega).

**Risultato 1 — SÌ: le probabilità sono giuste (ben calibrate).** Il motore
ha |bias| ≤ 0.02-0.03 e ECE 0.004-0.04 su quasi tutti i 19 mercati e le 3
leghe. Perfino sul risultato esatto la confidenza dichiarata è onesta: il
top-pick indovina il **14.6%** (SA) dichiarando in media 13.9%, 12.3%/12.0%
(PL), 15.4%/14.2% (Liga) — diciamo quello che sappiamo, né più né meno.

**Risultato 2 — il hit-rate: quanto il mercato, sopra la baseline.**
1X2 argmax: SA **54.2%** (mercato 54.3%, baseline-casa 40.4%), PL **55.3%**
(=mercato), Liga **54.3%** (=mercato; baseline 45.0%). Risultato esatto:
12-15% vs 11-13.7% del "sempre 1-1". Multigol ≈ baseline; pari/dispari al
coin-flip (49-51%: la quinta replica dell'irriducibilità). Il modello
indovina QUANTO il mercato — non di più (α*=0, Fase 16), ma nemmeno di meno,
e molto sopra il tirare a caso informato.

**Risultato 3 — le mis-calibrazioni residue sono ESATTAMENTE i bias noti,
lega per lega.** La verifica indipendente ritrova, come errori di
calibrazione, tutto ciò che le Fasi 50-53/79-81 avevano trovato via log-loss:
- **Serie A**: casa sovra-prezzata +0.024 / pareggio sotto-prezzato −0.020
  (il tilt del devig, Fasi 50-ter/52-ter) — è la calibrazione del MERCATO
  stesso, visibile pure nei suoi derivati (scarto-casa≥2 +0.035);
- **Premier**: calibrazione quasi PERFETTA ovunque (|bias|≤0.016, pareggio
  +0.001, ECE fino a 0.003) — il mercato più liquido non è solo il più duro
  da battere: è il meglio calibrato, riga per riga;
- **Liga**: GG sotto-predetto −0.036 (il deficit-pareggio/NG latino) e
  clean-sheet sovra-predetti +0.025/+0.027.
E qui il cerchio si chiude: **il router θ per-lega (F81) MIGLIORA la
calibrazione proprio dove era storta** — in Liga il bias GG passa da −0.036 a
−0.008 (ECE 0.036→0.012), cs_home 0.025→0.012, e in generale il router
riduce l'ECE su quasi tutti i mercati Liga. Una conferma della F81 su una
metrica indipendente dal log-loss.

**Risultato 4 — il path DC senza quote è un filo peggio, come atteso**:
1X2 argmax 52.9-53.5% (vs 54-55% del market-implied), GG Liga bias −0.041.
Coerente con la gerarchia nota (market-implied > DC quando ci sono le quote).

**Lezione.** La risposta alla domanda dell'utente è: **sì, nel senso
verificabile del termine** — le probabilità sono oneste (calibrate) e l'esito
più probabile si indovina quanto lo indovina il mercato, sopra ogni baseline.
Ciò che NON possiamo fare è indovinare *più* del mercato (Fasi 14-20), e la
Fase 82 mostra il perché in forma nuova: gli errori di calibrazione residui
del motore sono gli stessi del mercato che gli fa da input. Il valore
operativo del progetto resta: (a) probabilità calibrate anche sui ~17 mercati
che il book NON quota, (b) le correzioni per-lega (θ, φ) che raddrizzano le
mis-calibrazioni locali.

### 📐 Il modello in dettaglio

Nessun modello nuovo: è un AUDIT su predizioni già definite (motore Fase 26,
router Fase 52/81, DC config ufficiale, devig moltiplicativo).
- **ECE** = Σ_b w_b·|p̄_b − freq_b| su 10 fasce uguali [0,1] (w_b = quota di
  righe nella fascia b). 0 = calibrazione perfetta; 0.02 ≈ "quando dico X%
  sbaglio in media di 2 punti". `_ece` nello script.
- **Hit-rate binario**: pick = p>0.5; baseline = max(freq, 1−freq) (scegliere
  sempre l'esito maggioritario — battibile solo dove il modello DISCRIMINA
  tra partite, non solo nel livello medio). 1X2/multigol: argmax delle 3
  classi; baseline = classe più frequente. Risultato esatto: argmax della
  matrice (router per-lega), baseline = "sempre 1-1".
- **Perché su alcuni mercati hit=base**: quando freq è lontana da 0.5 (es.
  wtn_away ~0.18) quasi nessuna partita ha p>0.5 → il pick coincide con la
  baseline e la discriminazione la misura solo l'ECE/log-loss. È atteso, non
  un difetto.
- Numeri ricalcolabili dai 3 run `fase82_verifica_predizioni` (le tabelle
  complete per-mercato sono nelle metriche dei run).

**Riproducibilità.** `python scripts/_run_fase82_verifica_predizioni.py`
(~5 min la prima volta: 6 backtest DC Serie A in cache `outputs/db82_*`).

---

## Fase 83 — Revisione dei commit esterni (Codex, Fasi 6-13): corretti; 7 difetti minori, 1 fix

**Obiettivo.** Su richiesta dell'utente: verificare i **19 commit firmati
dall'account dell'utente ma prodotti da un'altra AI ("Codex")** il 10-11 luglio
2026 (range `a605e68…3e18c63`), che hanno costruito le Fasi 4e-bis→13-quater
(temperature scaling, prior neopromosse, anatomia del gap, ricalibrazione
per-classe, ensemble di emivite, diagonale inflazionata, stato di forma/streak)
e riorganizzato il README. Domanda: *ha commesso errori nel tentativo di
migliorare il codice?*

**Ragionamento.** Il codice di quei commit è ancora il cuore del progetto
(`dixon_coles.py` prior+diagonale, `calibration.py`, `loader.add_form`): un
errore lì falserebbe non solo le Fasi 6-13 ma tutto ciò che ci è stato costruito
sopra. La Fase 15 aveva già auditato i *numeri*; qui l'angolo è diverso e
complementare: **correttezza del codice e del metodo** (leakage walk-forward,
uso di dati futuri, formule, normalizzazioni, fonte unica delle metriche),
verificata sia sui diff storici sia sullo stato attuale di HEAD.

**Alternative.** (a) Fidarsi dell'audit Fase 15 (copre i numeri, non il codice
riga per riga); (b) ri-eseguire tutti i backtest delle Fasi 6-13 (costoso e
ridondante: i numeri sono già riprodotti dal registro); (c) revisione
avversariale del codice + ricalcolo a campione dal registro + smoke-test della
pipeline. Scelta: (c).

**Risultato.** **Nessun errore di gravità alta: le conclusioni delle Fasi 6-13
reggono tutte.** Verificati corretti esplicitamente: il prior neopromosse
(applicato solo alle squadre in `promoted_teams`, bersaglio dello shrinkage
`att→−δ, dif→+δ`, `promoted_teams` senza look-ahead, δ leave-future-out,
invarianza di gauge col vincolo `mean(attack)=0`); la diagonale inflazionata
(matrice clippata e **rinormalizzata** dopo l'inflazione, verosimiglianza di φ
esatta); il temperature scaling (`q ∝ p^(1/T)` rinormalizzato, T fittato solo
sul passato); la ricalibrazione per-classe (somma-1, pesi leave-future-out);
`add_form` e streak (lettura dello stato PRIMA dell'aggiornamento con la gara
corrente: zero leakage); il walk-forward del backtest; l'uso della fonte unica
`compute_metrics`; ~15 numeri del README ricampionati dal registro, tutti
esatti. In più, smoke-test indipendente: 140 test verdi e il backtest ufficiale
ri-eseguito e registrato (2526: 1X2 0.9925, coerente col registro).

Sette **difetti minori** (nessuno cambia una conclusione):

| # | difetto | dove | stato |
|---|---|---|---|
| F1 | streak non azzerate tra stagioni (bin estremi parz. spuri) | `_run_streaks.py` | già dichiarato (Fase 15), diagnostico |
| F2 | `calibrate.py` fermo alla config pre-Fase 7 (niente prior) | `scripts/calibrate.py` | **CORRETTO in questa fase** |
| F3 | pesi RECAL col senno di poi nelle combo | `_run_combo_analysis.py` | già dichiarato (Fase 15) |
| F4 | tier forza-squadra dalla classifica FINALE | `analyze_gap.py` | già dichiarato (diagnostica) |
| F5 | model_ll su tutte le righe, market_ll solo dove ci sono quote | `evaluation/markets.py` | latente: zero quote mancanti nelle stagioni valutate → impatto nullo |
| F6 | draw_inflation × covariate: φ fittato senza features | `dixon_coles.py` | latente: mai combinate in nessun esperimento |
| F7 | Fase 9-bis senza run nel registro | `_run_gap_covid.py` | storico: la regola è nata solo in Fase 15; deriva da run già registrati |

**Il fix (F2).** `scripts/calibrate.py` dichiarava "config = ufficiale corrente"
ma chiamava `run_backtest` **senza** `promoted_prior`: i numeri storici della
Fase 6 erano corretti (il prior non esisteva ancora), ma un ri-run odierno
avrebbe registrato come "ufficiale" una config che non lo è più. Ora legge
TUTTA la config da `src.config.SERIE_A` (prior incluso) e registra
`promoted_prior` nel config del run. F5 e F6 restano latenti e documentati qui:
si correggono solo se/quando un esperimento li attiverà davvero (toccare ora
`evaluation/markets.py` cambierebbe numeri registrati senza necessità).

**Lezione.** Un contributo esterno di 19 commit è risultato **pulito sul piano
metodologico** — merito anche del protocollo (walk-forward come idioma unico,
`compute_metrics` come fonte unica, registro): un metodo che rende gli errori
difficili vale più di una revisione a posteriori. Il difetto tipico trovato non
è il bug di calcolo ma la **deriva di configurazione** (script scritti prima di
un'adozione che nessuno aggiorna dopo): quando la config ufficiale cambia,
grep degli script che la incorporano.

### 📐 Il modello in dettaglio

Nessun modello nuovo: è una revisione di codice. Le formule verificate riga per
riga contro `src/` sono quelle già documentate: il bersaglio del prior nello
shrinkage (Fase 7, `dixon_coles.py`):

```
penalta' = shrinkage · [ Σ_i (att_i − a_prior_i)² + Σ_i (dif_i − d_prior_i)² ]
a_prior_i = −δ, d_prior_i = +δ   se i ∈ promosse   (δ=0.23, Fase 7)
a_prior_i = d_prior_i = 0        altrimenti
```

il temperature scaling (Fase 6, `calibration.py`): `q_k ∝ p_k^(1/T)` poi
rinormalizzato (equivalente a dividere i logit per T); l'inflazione della
diagonale (Fase 12b): `P'(i,i) = (1+φ)·P(i,i)` con clip ≥0 e **rinormalizzazione
finale a somma 1**. Nessun numero nuovo da motivare: l'unico run prodotto è la
riproduzione del backtest ufficiale (config invariata da `src/config.py`),
registrato in `runs.jsonl` con commit e impronta dati.

---

## Fase 83-bis — `predict.py` per-lega: il "passo 2" del test prospettico (parziale)

**Obiettivo.** Rivedendo il commit sulle nuove stagioni (Fase 78, test
prospettico 2026-27, richiesta utente), è emerso il difetto che il diario di
quella fase segnalava come **debito del "passo 2"**: il tool ufficiale
`predict.py` **ignorava `--league`** e usava sempre la config Serie A
(`from src.config import SERIE_A`, hard-coded in `kw`), anche per Premier/Liga.
Era proprio la ragione per cui la Fase 78 aveva dovuto scrivere uno script
separato (`_run_prospettico_2627.py`) per generare l'anteprima con la config
per-lega giusta.

**Ragionamento.** Il test prospettico (il gold standard, Fase 78) e ogni uso
pratico su Premier/Liga passano da `predict.py`: se il Modello 1 gira con
δ=0.23 (Serie A) su una partita di Premier (δ vero 0.33, Fase 55), le neopromosse
inglesi sono **sotto-corrette** — esattamente l'errore che il §7 del CLAUDE.md
mette in guardia ("non copiare i numeri della Serie A"). Il fix è a costo zero:
esiste già `src.config.league_config(league_key)` (fallback esplicito a Serie A
per leghe ignote).

**Cosa è stato fatto.** `predict.py` ora legge `cfg = league_config(args.league)`
e ne usa emivita/shrinkage/blend/**δ** per il Modello 1; l'header stampa la lega.
Verificato su 3 leghe: δ 0.23/0.33/0.22 e γ auto-fittato 0.128/0.191/**0.297**
(Liga il più alto, come previsto dalla EDA Fase 55). 140 test verdi.

**Cosa resta (dichiarato).** Il **path market-implied (Modello 2)** usa ancora
costanti di forma rappresentative (φ0=0.30, κ=1.5 — difendibili, Fase 44) e
`dp_theta=DP_THETA` (1.225). La Fase 81 ha però mostrato che il θ del router è
**per-contesto**: ottimo ≈1 in Premier (dove la dp neutra è meglio), ≈1.2 in
Serie A/Liga. Rendere il M2 per-lega (θ da config-lega) è il residuo del passo 2:
non fatto qui per non aggiungere un iperparametro di config senza un backtest
dedicato del tool — annotato nel protocollo di `prospettico_2026_27.md §3` così
che, al primo turno 2026-27, il M2 Premier venga prodotto con θ neutro.

**Lezione.** Stessa famiglia della Fase 83-F2 (`calibrate.py`): la **deriva di
configurazione**. Un tool scritto quando esisteva una sola lega resta cablato
sulla Serie A anche dopo che la config è diventata per-lega. Regola operativa:
i punti d'ingresso utente (`predict.py`, script one-shot) devono leggere da
`league_config`, mai importare `SERIE_A` direttamente.

### 📐 Il modello in dettaglio

Nessuna matematica nuova: è la stessa `DixonColesModel` + `price_markets` della
Fase 78, ma con gli iperparametri presi da `league_config(args.league)` invece
che dalla costante `SERIE_A`. La formula del prior (Fase 7) è invariata; cambia
solo il **valore di δ** iniettato: 0.23 (SA) / 0.33 (PL) / 0.22 (Liga), ciascuno
`δ = ln(gol_lega / gol_promosse)` della sua lega (Fase 55/57). γ non è in config:
lo fitta il DC dai dati della lega (Liga più alto, Fase 55). Nessun run scorato
(è un fix di tooling, non un esperimento); riproducibile con
`python scripts/predict.py --league premier_league Newcastle Liverpool`.

---

## Fase 84 — Audit trasversale del repo (4 fronti): numeri OK, codice OK, docs ripuliti, nuove piste

**Obiettivo (utente).** «Vedi tutto il lavoro svolto: cerca errori (calcoli o
file), migliora i ragionamenti, pensa a nuove soluzioni/calcoli/costanti,
migliora i file del repo.» Un audit a 360° del progetto maturo (84 fasi, 3
leghe, 704 run registrati).

**Metodo.** Quattro revisioni indipendenti in parallelo, ognuna con verifica
diretta (ri-esecuzione, ricalcolo dal registro, snippet numerici), poi ogni
finding ri-controllato a mano prima di agire:
1. **Numeri** — riproducibilità di ogni headline da `runs.jsonl`/dati;
2. **Codice** — correttezza dei modelli e delle metriche (bug, leakage,
   normalizzazioni, stabilità);
3. **File** — coerenza e igiene della documentazione (contraddizioni,
   affermazioni stantie, link, conteggi);
4. **Idee** — nuove leve/costanti testabili e affinamenti di ragionamento.

**Risultato — il progetto è in salute.**

- **Numeri (nessun errore).** Ri-eseguito il backtest ufficiale su 6 stagioni:
  1X2 **0.9797** e O/U **0.6885** esatti; mercato 0.9632/0.6816, baseline
  in-sample 1.0834/0.6892 e **ex-ante ricalcolata dai dati grezzi**
  1.0860/0.6961; gap +0.0165, 86.3%/86.6% di distanza chiusa (ricalcolo
  86.27%/86.56%); ROI −15.67% medio / −15.60% pooled / 864 bet; tabella V0→V4 e
  i CI bootstrap della Fase 17 tutti riprodotti dal registro. La catena
  `runs.jsonl → README/DIARIO` è internamente consistente; l'unico errore mai
  trovato (ROI −8.5%→−15.7%) resta correttamente sistemato ovunque (Fase 15).
- **Codice (nessun bug attivo).** Il percorso ufficiale (DC-da-gol + metriche) e
  il motore market-implied sono corretti: double-Poisson mean-preserving
  (errore <6e-13, θ=1 riduce esattamente alla Poisson), tutte le matrici
  normalizzate a 1 dopo rho/φ/dp/troncamento, φ35 identica nei due moduli,
  correzione DC coi segni giusti, **zero look-ahead** (`fit` filtra
  `date < as_of` stretto), marginali di bivariato/copula preservati. Due sviste
  **latenti** su percorsi off-di-default: **F1** guardia mancante per
  `draw_inflation`+`dynamic_rho` (→ **corretta**, con test); **F2** in
  `implied_lambda_mu` l'O/U è sotto-pesato 3:1 su input incoerenti (innocuo:
  i chiamanti devigano prima, contratto rispettato — lasciato con nota).
- **File (ripuliti).** Trovata e corretta la **stantia più grave**: `CLAUDE.md`
  §6 «Stato corrente» era ferma alla Fase 33 (~210 righe che ignoravano
  market-implied, Premier/Liga, router θ, `predict.py` per-lega) → **riscritta**
  come istantanea alla Fase 83 con rimando ai documenti vivi. Corretti: la
  checklist §2 diceva ancora «commit sul branch di sviluppo» (vs la regola
  main-only §3-bis); la cella README Fase 66 dava per pieno un file svuotato
  alla Fase 70; la tabella Fase 5 era intestata «modello (uff.)» ma mostra
  valori **pre-prior** (0.9807/0.6884) → ri-etichettata; il commento di
  `DP_THETA` citava la Fase 51 (MLE 1.205) invece della Fase 52 (costante
  pooled adottata 1.225); riempito `files/README.md` (63 MB di bundle senza
  spiegazione). Verificato OK: tutti i valori di config/θ coincidono tra
  `src/config.py`, `market_implied.py`, README, CLAUDE.md, PANCHINA; 3420
  partite × 9 stagioni coerente; 140 test.
- **Idee (catalogate in `docs/PISTE.md`).** L'idea nuova più forte:
  **θ del router come funzione del MARGINE** della partita, non costante
  per-lega — unifica in una sola curva universale le Fasi 53 («θ decresce con la
  liquidità») e 75 («θ cresce nel tempo»), che hanno un osservabile comune
  per-partita (l'overround). È anche il modo giusto di ri-verificare la
  monotonìa temporale della Fase 75 (oggi su 2 sole stagioni all'estremo).
  Aggiunte anche: il diagnostico economico dell'handicap asiatico *prima*
  dell'inversione a 3 vincoli (pista #5); la ri-verifica del beat-the-close vs
  **Pinnacle+Shin** (l'unico edge del progetto, mai testato contro l'avversario
  più duro — pista #9); l'H2H puntato sui **totali/GG** e non sull'1X2 (#1); e
  tre **affinamenti di ragionamento** (§5-bis di PISTE), su tutti la distinzione
  «α\*=0 (informazione inglobata) ≠ prezzi ben calibrati (la chiusura è
  mis-calibrata in modo correggibile, dp_lvl/Fase 82)».

**Lezione.** Dopo 84 fasi il progetto regge un audit avversario a 360°: i numeri
si riproducono, il codice del percorso ufficiale è corretto, e i difetti sono
**deriva di configurazione** (docs/tool cablati su uno stato passato) più che
errori di calcolo — la stessa famiglia della Fase 83 (`calibrate.py`) e 83-bis
(`predict.py`). Il metodo (walk-forward come idioma, `compute_metrics` fonte
unica, registro, blocchi 📐) rende gli errori di calcolo difficili; la
manutenzione da fare è tenere i **testi divulgativi** allineati allo stato.

### 📐 Il modello in dettaglio

Nessuna matematica nuova (è un audit). Le uniche modifiche al codice:
- **guardia F1** in `DixonColesModel.__init__`: `raise ValueError` se
  `draw_inflation and dynamic_rho` (simmetria con le due guardie esistenti su
  `draw_balance`), perché `_draw_base_arrays` fitta φ col `rho` **scalare**
  mentre `_score_matrix` applicherebbe `rho + rho_slope·(λ+μ−centro)` — φ
  fittato su un rho diverso da quello applicato. Entrambi off di default.
- fix di soli **commenti/etichette** altrove (nessun cambiamento di calcolo).
I 6 run del backtest ufficiale ri-eseguiti per l'audit sono registrati in
`runs.jsonl` (config c297279f). Numeri riproducibili: `python scripts/backtest.py`
per ogni stagione 2020-21→2025-26, media = 0.9797.

---

## Fase 85 — La chiave per gli esiti MENO PROBABILI: anatomia della coda (θ diretto sul risultato esatto, e la COM-Poisson)

**Obiettivo (utente).** «Trovare la chiave che ci permette di prevedere risultati
anche meno probabili.» Finora la sotto-dispersione (double-Poisson θ) era stata
scoperta e adottata guardando l'**1X2** (Fase 51) e l'aggregato del listino
(Fase 52); il **risultato esatto** e i **totali estremi** — dove vivono gli esiti
rari — non erano mai stati messi al centro. Qui si punta il microscopio sulla
**coda della distribuzione dei gol**.

**Metodo.** Su **7.980 partite** con chiusura 1X2+O/U (3 leghe), invertite nei
λ,μ del mercato (una volta, cache in `outputs/implied_lammu_cache.csv`), si
valutano più forme dei marginali (tutte **mean-preserving**: λ,μ restano le medie)
su due metriche di coda: **log-loss del risultato esatto** (la cella realizzata
della matrice) e **calibrazione dei totali alti** (Over 3.5 = totale ≥4, Over 4.5
= totale ≥5) contro la frequenza reale. `scripts/_run_tail_analysis.py`.

**Ragionamento / ipotesi.** La domanda-chiave era un dubbio onesto: la
double-Poisson θ>1 **alleggerisce le code** — quindi aiuta l'1X2 (centro) ma
**danneggia** la predizione degli esiti rari, che vivono proprio nelle code? Se
così fosse, per la coda servirebbe l'opposto (più massa, θ<1 o code pesanti).

**Risultato — la Poisson SBAGLIA la coda, e la dp la CORREGGE (non la
danneggia).**

| forma | exact-LL | Over 3.5 Δ | Over 4.5 Δ |
|---|--:|--:|--:|
| Poisson (θ=1) | 2.8369 | **+0.0096** | **+0.0083** |
| dp θ=1.10 | 2.8329 | +0.0071 | +0.0028 |
| **dp θ=1.225 (router)** | **2.8322** | +0.0037 | −0.0039 |
| dp θ=1.35 | 2.8359 | +0.0002 | −0.0103 |
| dp θ=1.50 | 2.8455 | −0.0042 | −0.0177 |

Tre fatti:
1. **La Poisson sovra-stima i totali alti** (+0.0096 su Over 3.5, +0.0083 su Over
   4.5): la distribuzione reale dei gol ha **code più leggere** del previsto.
   L'intuizione "θ>1 danneggia la coda" era **sbagliata**: la coda reale È
   sotto-dispersa, la dp la avvicina.
2. **L'exact-score log-loss ha una valle piatta attorno a θ≈1.18**, e θ=1.225 ci
   cade dentro: 2.83219 contro 2.83192 dell'argmin, differenza appaiata −0.00027
   con IC95 bootstrap [−0.00081, +0.00028] (dentro il rumore). ~~Il «minimo
   ESATTAMENTE a θ=1.225»~~ della prima stesura era un artefatto della griglia a
   cinque punti {1.0, 1.10, 1.225, 1.35, 1.5}, in cui 1.225 era l'unico valore
   vicino all'ottimo; su griglia fine a passo 0.01 l'argmin è **1.18**
   (2.831915). Resta vero, ed è il punto, che la costante del router scelta sul
   **listino** cade nella valle dell'ottimo misurato direttamente sul
   **risultato esatto** — non che ne sia l'argmin. *(Rettifica Fase 101.)*
3. **Tensione di profondità (la crepa vera).** Over 3.5 è azzerato a θ≈1.35, Over
   4.5 a θ≈1.10, il log-loss a θ=1.225: **un solo parametro di dispersione non
   calibra ogni profondità della coda contemporaneamente**. È il limite
   strutturale, non un errore.

**⚠️ RETTIFICA (Fase 101) — la COM-Poisson NON è una famiglia diversa: è la
stessa double-Poisson, riparametrizzata.** La prima stesura di questa sezione
presentava la dispersione «principiata» a un parametro ν (COM-Poisson,
`p(x) ∝ aˣ/(x!)ᵛ`, mean-matched) come la versione «seria» della sotto-dispersione
di cui la dp sarebbe stata una scorciatoia. È falso, e si dimostra in due righe.
`_dp_pmf(rate, θ)` costruisce
`q_k ∝ exp(θ·(k·ln(c·rate) − c·rate − ln k!)) = (c·rate)^{θk}·e^{−θ·c·rate}/(k!)^θ`;
il fattore `e^{−θ·c·rate}` non dipende da k, quindi dopo la normalizzazione resta
`q_k ∝ a^k/(k!)^θ` con `a = (c·rate)^θ` — esattamente la forma della COM-Poisson
con ν=θ. A ν fisso la media è strettamente crescente in `a`, quindi il
mean-matching individua **la stessa** distribuzione: **dp(θ) ≡ COM-Poisson(ν=θ)**.

Verifica numerica, due vie. **(a) PMF**:
`max|_dp_pmf(rate,θ) − compois_pmf(rate,ν=θ)| ≤ 1.2e-04` su
rate ∈ {0.6…3.0} × θ ∈ {1.10…1.50}, e lo scarto **cresce col tasso**
(7e-11 a rate 0.6, 1e-08 a 1.0, 4e-06 a 2.0, 1.2e-04 a 3.0): è solo troncamento
del supporto, non una differenza di forma (la dp normalizza su 0..10,
`compois_pmf` su 0..40 e poi taglia a 11). Regredendo `ln q_k` su `{1, k, −ln k!}` per
`_dp_pmf(1.24, 1.225)` si riottiene ν = 1.225000 con residuo massimo 1.4e-14.
**(b) Le tre statistiche della fase**, sugli stessi 7.980 λ,μ:

| ν = θ | exact-LL dp | exact-LL COM | Over 3.5 Δ (dp / COM) | Over 4.5 Δ (dp / COM) |
|---|--:|--:|--:|--:|
| 1.10 | 2.832903 | 2.832898 | +0.00706 / +0.00704 | +0.00283 / +0.00281 |
| 1.15 | 2.832060 | 2.832057 | +0.00574 / +0.00573 | +0.00013 / +0.00011 |
| 1.225 | 2.832185 | 2.832182 | +0.00370 / +0.00369 | −0.00386 / −0.00387 |
| 1.35 | 2.835851 | 2.835850 | +0.00019 / +0.00018 | −0.01030 / −0.01030 |
| 1.50 | 2.845468 | 2.845467 | −0.00419 / −0.00419 | −0.01769 / −0.01770 |

(Lo si vede già nell'output di `scripts/_run_tail_analysis.py`: le righe
`dp theta=1.35` e `COM nu=1.35` sono **identiche** a quattro decimali — 2.8358 /
+0.0002 / −0.0103 — e così `dp theta=1.5` e `COM nu=1.50`.)

Quindi la riga ~~«COM-Poisson ν=1.15 pareggia il log-loss (2.8321) e calibra
meglio la coda estrema (Over 4.5 +0.0001)»~~ era, letteralmente, **dp θ=1.15**:
un punto di griglia che la griglia della dp non conteneva. Non era un confronto
fra due famiglie, ma fra due valori di θ della stessa. Ciò che resta vero — ed è
il risultato della fase — è il punto 3: **tensione di profondità**, Over 4.5
vuole θ≈1.15, Over 3.5 θ≈1.35, il centro θ≈1.18. Ciò che cade: la COM-Poisson
come «forma alternativa provata e a tetto», e con essa il conteggio delle
conferme indipendenti sulla coda — sono **due** (mistura/isotonica della Fase 87
e θ per-squadra della Fase 86-bis), non tre. La conclusione operativa non cambia:
per andare oltre sulla coda serve un **secondo parametro di forma** (mistura, o
ricalibrazione per-profondità dei totali), non un'altra forma a un parametro.

**E l'1X2 improbabile (upset)?** Controprova sul lato esiti: la calibrazione del
**mercato stesso** (chiusura devigata, 10.259 partite) per fascia di probabilità
1X2 è **buona anche nella coda** (esiti a P 5-20%: scarti −0.006…−0.015, coerenti
col mite favorite-longshot bias; la fascia estrema <5% è rumore, n=161). L'unica
mis-calibrazione ampia è nota: i **favoriti** (fascia 0.5-0.7) rendono 61.3% vs
prezzato 58.9% (+0.024) — è il tilt che dp_lvl/temperatura già sfruttano. Quindi:
sul lato **1X2** la coda è market-efficient (poco spazio); sul lato **gol/
risultato esatto** lo spazio c'è ed è **forma della distribuzione**, non
informazione.

**Lezione / cosa ne consegue.** La "chiave per gli esiti meno probabili" **non è
nuova informazione** (il tetto α\*=0 vale anche in coda) ma **controllo di
dispersione della distribuzione dei gol** — e quel controllo è **già il θ del
router**, ora validato per la prima volta *direttamente* sul risultato esatto e
sui totali estremi (non per traslazione dall'1X2). Il margine residuo è tutto
nella **tensione di profondità**: la prossima leva concreta è un trattamento
della coda a **due parametri** (es. ricalibrazione isotonica dei mercati-totale
per soglia, o una mistura di due Poisson per il regime "partita da tanti gol"),
non un'altra forma a un parametro. *(La prima stesura chiudeva con «COM-Poisson
provata e a tetto»: la rettifica della Fase 101 qui sopra mostra che quella non
era una forma alternativa ma la dp stessa a un altro θ — la conclusione non
cambia, ma non poggia più su quel test.)* Va in `docs/PISTE.md` come pista
aperta.

### 📐 Il modello in dettaglio

Forme dei marginali confrontate (tutte poi passate alla stessa correzione DC
`rho=-0.06` e alla matrice `M/M.sum()`):
```
Poisson:        p(x) = e^-λ λ^x / x!
double-Poisson: p(x) ∝ (e^-λ λ^x/x!)^θ · c^x, con c t.c. E[X]=λ (mean-preserving,
                Fase 51; θ>1 = sotto-dispersa). Normalizzata è p(x) ∝ a^x/(x!)^θ
                con a=(c·λ)^θ. Codice: market_implied._dp_pmf.
COM-Poisson:    p(x) ∝ a^x / (x!)^ν, con 'a' t.c. E[X]=λ (mean-matched via
                bisezione su a; ν=1 → Poisson, ν>1 → sotto-dispersa).
                È LA STESSA di sopra con ν=θ (verificato a ≤1.2e-04, solo
                troncamento del supporto): NON è una forma alternativa.
                Codice: scripts/_run_tail_analysis.py:compois_pmf.
```
Perché l'exact-LL ha la sua valle attorno a θ≈1.18-1.22 e non altrove: il log-loss del
risultato esatto pesa **ogni cella** per la sua frequenza reale, quindi è
dominato dagli scoreline comuni (1-1, 1-0, 0-0, 2-1); la Poisson **sotto-stima**
proprio quelli (fascia di P 0.10-0.20: reale 0.1290 vs Poisson 0.1209, +0.0081)
perché mette troppa massa in coda — θ>1 la ritira e la rimette sul centro, con
ottimo a θ≈1.18 (differenza da 1.225 dentro il rumore) dove il guadagno sul
centro non è ancora mangiato dalla
sovra-correzione della coda estrema. Numeri riproducibili:
`python scripts/_run_tail_analysis.py` (usa la cache dell'inversione; il θ=1.225
coincide con `market_implied.DP_THETA`). Analisi diagnostica: nessun run scorato
in `runs.jsonl` (nessun cambio di config; il router usa già θ=1.225).

---

## Fase 86 — Secondo audit orchestrato (workflow): fix di onestà, chiusure e il LEAD della dispersione per-squadra

**Obiettivo (utente).** «Cerca errori, migliora ragionamenti e file, scopri nuove
piste e nuovi ragionamenti, vai in profondità sugli esiti meno probabili.»
Secondo giro d'audit, questa volta **orchestrato**: 6 revisori in parallelo
(coda, calcoli/ragionamenti, nuovi modelli, nuovi dati, completezza docs,
microstruttura mercati) → **verifica avversaria** di ogni finding (lente diversa
+ obbligo di citare la fase che eventualmente lo chiude) → sintesi. 36 finding →
30 verificati → **14 sopravvissuti**, 16 refutati. **Poi ho riprodotto a mano
ogni numero sostanziale prima di documentarlo** (regola §5): un passaggio che ha
salvato da un errore dell'audit stesso (vedi il lead sotto).

**La verifica avversaria ha fatto il suo lavoro** (16 refutati), scartando
artefatti che sembravano scoperte: la «dispersione non-monotona θ\*≈0.8 nella
coda» è un **artefatto di selezione-sull'esito** (si riproduce identico simulando
da una Poisson pura); l'«edge strutturale dei combo/parlay» eredita α\*=0 (è
aritmetica del joint, non informazione); la copula a coda asimmetrica (Clayton/
Gumbel) non batte Frank a dipendenza ρ≈0.03; il «raddoppio del campione via 1°/2°
tempo» è fallacia; multi-linea O/U è già PISTE #15 (football-data ha solo la 2.5).

**Errori CONFIRMED e corretti (onestà, §1.6/§2-bis):**

- **E1 — la varianza dp era sovrastimata.** Il blocco 📐 della Fase 51 diceva che
  i gol «oscillano ~17% meno di una Poisson». Il 17% = 1−1/1.205 è
  l'**approssimazione asintotica per μ grande** di Efron (`Var≈Var_Poisson/θ`),
  non l'esatto. Ricalcolato sulla `_dp_pmf` ai tassi reali (μ≈1.2-1.5, θ≈1.2): la
  riduzione di varianza è **~10%** (a μ=1.24, θ=1.205: Var 1.115, −10.1%; std
  ~−5%), servirebbe θ≈1.35 per un vero −17%. Corretto a `DIARIO:5550/5643/5641`
  (segno e scoperta invariati; a valle non cambia nulla).
- **E2 — il ROI −15.7% è alla quota MEDIA; manca il caveat best-price.** La
  `value_bet_roi` seleziona e paga su `odds_home/draw/away` = **AvgC** (chiusura
  media multi-book: verificato `odds_home==AvgCH` esatto, 380/380). Al **best-
  price** (MaxC) col metodo **coerente** select-max/pay-max il 2526 va da −4.7% a
  **−2.4%** (thr .05) — resta negativo; a thr .03 è −9.7%. Il **+0.9%** che
  sembrava un sign-flip è il metodo **incoerente** (seleziona su avg, paga su
  max: conta due volte il vantaggio del best-price). Aggiunto il caveat al README.
  **La conclusione (α\*=0, non scommettere) è intatta.** Chiude PISTE #8.

**Chiusure riprodotte (negativi utili, §1.4):**

- **Handicap asiatico ridondante come input.** La supremazia implicita nella
  linea AH di chiusura correla **0.9952** con λ−μ già ricavata da 1X2+O/U (2.660
  partite Serie A; regr. `AH ≈ 0.94·(λ−μ)`): è la stessa matrice ripackagata.
  **Chiude PISTE #5** (l'«inversione a 3 vincoli» non serve). L'AH resta utile
  solo come **benchmark quotato** della famiglia-margine/scarto≥2 (Tier 2).

**Il LEAD di punta — la dispersione per-squadra (che CORREGGE l'audit).** Un
revisore aveva concluso «la volatilità-risultato di una squadra NON persiste
(corr −0.03) → nessun proxy storico degli upset». **Riproducendolo a mano ho
trovato il contrario.** Misurando la **volatilità-sorpresa** per-squadra (std del
residuo `diff-reti realizzata − (λ−μ) atteso dal mercato`):
- **persiste** stagione→stagione: corr **+0.25** grezza, **+0.20** controllata per
  la forza (n=306), entrambe **fuori dalla banda nulla** [±0.11]. Alcune squadre
  sono stabilmente più «tutto-o-niente» del punto-stima del mercato.
- ed è **direzionale e sfruttabile**: classificando le partite per terzile di
  volatilità-sorpresa **passata** (solo stagioni precedenti → out-of-sample), il
  gruppo ad **alta** volatilità è predetto meglio da **θ\*=1.10** (coda più
  pesante) vs **θ\*=1.225** dei gruppi medio/basso — sul risultato esatto
  (exact-LL 2.9187 vs 2.9199 per l'alto). `scripts/_run_team_dispersion.py`.

È la prima crepa credibile nel «θ uniforme» (F52-quater aveva escluso solo θ per
volume/equilibrio/coda, **mai per identità-squadra**) ed è esattamente sul tema
dell'utente: **gli esiti rari delle squadre volatili si prevedono meglio con una
coda più pesante**. Onestà: il θ di gruppo è scelto **in-sample** (la
classificazione è OOS, ma il θ ottimo no) e i guadagni sono piccoli (~0.001
exact-LL) → è un **LEAD forte, non una modifica adottata**: serve un walk-forward
`θ_team` pieno (fit di θ per squadra/gruppo su passato, con shrinkage verso 1.225,
applicato al futuro) per stabilirne la sfruttabilità. Va in `docs/PISTE.md` come
pista di punta.

**Fix di file / completezza (dal fronte docs):** creato **`docs/GLOSSARIO.md`**
(zero glossari prima, termini come devig/market-implied/encompassing/θ definiti
solo inline in 8.700 righe); aggiornato l'header **Arco 10** dell'indice (76-83 →
76-86); `DATI.md` marker Fase 70→73; `worldcup/README.md` (Serie A → 3 leghe);
aggiunti i **blocchi 📐 mancanti** alle Fasi 34 (rimando a φ35/Fase 10) e 77
(rename, nessuna matematica) — la convenzione §2-bis vale anche per audit e fasi
non-matematiche.

**Lezione.** Un audit orchestrato con verifica avversaria **e** ri-verifica
manuale è più forte di entrambi da soli: la verifica avversaria ha scartato 16
artefatti plausibili, ma la ri-verifica manuale ha ribaltato un finding
«CONFIRMED» sbagliato (la non-persistenza della volatilità) — che era anche il
più interessante. Il valore netto: **due fix di onestà** (E1, E2), **una pista
chiusa** (AH input), **un glossario e sei allineamenti docs**, e **un lead
genuinamente nuovo** (dispersione per-squadra) che nessuno dei due metodi da solo
avrebbe consegnato correttamente. Nessun finding riapre l'edge (α\*=0 intatto).

### 📐 Il modello in dettaglio

- **E1 (varianza dp).** Esatto: per la `_dp_pmf` (mean-preserving), `Var/μ` a
  μ=1.24, θ=1.205 è **0.899** → riduzione 10.1% (non 17%); a μ=1.5, θ=1.225 è
  0.879 → 12.1%. La formula `Var≈Var_Poisson/θ` vale solo asintoticamente (μ→∞).
  Ricalcolabile: `_dp_pmf(rate, theta)` in `src/models/market_implied.py:47-63`.
- **Volatilità-sorpresa per-squadra.** Per partita: `resid = (gh−ga) − (λ−μ)`,
  con λ,μ da `implied_lambda_mu(devig(1X2), devig(O/U), ρ=−0.06)`. Per
  squadra-stagione (≥10 gare): `vol = std(resid)`. Persistenza = `corr(vol_s,
  vol_{s+1})` su stagioni consecutive (codice-stagione +101); «controllata per
  forza» = residuo di `vol` regredita su `mean(|λ−μ|)` della squadra (r=0.267 col
  confondimento-forza). Banda nulla per permutazione (3000). θ\* di gruppo:
  minimo di `exact-LL(θ) = mean −log P(gol_h,gol_a)` su θ∈{1,1.1,1.225,1.35,1.5},
  con la matrice `score_matrix(λ,μ,ρ=−0.06,dp_theta=θ)`; terzili sulla
  volatilità-sorpresa **passata** (media delle stagioni precedenti → OOS).
  Riproducibile: `python scripts/_run_team_dispersion.py`. Diagnostico, nessun
  run scorato in `runs.jsonl` (nessun cambio di config).

---

## Fase 86-bis — Il verdetto walk-forward sul θ per-squadra: NON sfruttabile (il tetto regge anche nella coda)

**Obiettivo.** La Fase 86 aveva trovato un lead forte ma con un θ di gruppo scelto
**in-sample**: promesso il test onesto (walk-forward θ_team). Eccolo — la prova
definitiva che risponde alla domanda dell'utente sugli esiti meno probabili.

**Metodo.** Per ogni stagione di test `s` (dalla terza con quote in poi): si
classificano le partite in terzili di **volatilità-sorpresa passata** (solo
stagioni < s), si **fitta il θ ottimo per terzile sui dati passati**, lo si
applica a `s` e si accumula il log-loss del risultato esatto **out-of-sample**,
contro il θ globale=1.225. `scripts/_run_team_dispersion.py:walk_forward`.

**Risultato — NEGATIVO, netto.** Su **5.690 partite OOS**:

| | exact-LL |
|---|--:|
| θ globale = 1.225 | **2.8212** |
| θ_team (fit su passato) | 2.8222 |
| **Δ (team − globale)** | **+0.00096 → PEGGIO** |

Il θ per-squadra **peggiora** la predizione del risultato esatto out-of-sample.
Il perché è nei θ fittati stagione per stagione: sono **instabili** (il gruppo
alto va 1.0 nel 2021-22 → 1.1 nelle stagioni dopo; il medio oscilla 1.225↔1.1),
quindi la classificazione + il contrasto-θ non trasferiscono al futuro. La
persistenza della volatilità-sorpresa (+0.20, Fase 86) è **reale ma non
sfruttabile**: è troppo rumorosa anno-su-anno perché un θ per-squadra la
monetizzi.

**Lezione / cosa ne consegue.** È il finale onesto della caccia agli esiti rari:
**anche il θ per-squadra — la crepa più credibile nel "θ uniforme" — non batte il
θ globale OOS.** Conferma per l'ennesima volta, e ora *nella coda e per-squadra*,
il fatto-cardine del progetto: il tetto è **informativo** (α\*=0), non
architetturale. La chiave per prevedere gli esiti meno probabili resta quella
della Fase 85 — il controllo di dispersione **globale** (θ=1.225 del router), già
al suo ottimo — e non esiste una sotto-struttura (per-squadra, per-profondità,
per-forma) che aggiunga valore sfruttabile: le hanno provate tutte (θ per
volume/equilibrio/coda F52-quater; ~~COM-Poisson F85~~ — ritirata dalla Fase 101,
era la dp riparametrizzata e non una forma diversa; mistura di regime F86 audit,
OOS-fragile; θ per-squadra F86-bis). Il lead della Fase 86 passa da 🔎 a **❌
chiuso**: la volatilità-squadra persiste (fatto vero, documentato) ma il θ_team
non è adottabile. Nessuna delusione: è esattamente il tipo di risultato negativo
che il progetto valorizza (§1.4) — e chiude in modo pulito la domanda "si possono
prevedere meglio i risultati meno probabili?": **no, non oltre la dispersione
globale già nel motore.**

### 📐 Il modello in dettaglio

Walk-forward espandente: per la stagione `s`, `θ_g = argmin_θ Σ_{past, gruppo g}
−log P(gol|θ)` con `θ ∈ {1, 1.1, 1.225, 1.35, 1.5}` e i terzili definiti sulla
distribuzione di `pv = ½(pastvol_home + pastvol_away)` delle partite **passate**;
poi exact-LL su `s` con `θ_g(gruppo della partita)` vs `θ=1.225`. La media
espandente `pastvol` usa solo stagioni `< s` (nessun look-ahead). Numeri
riproducibili: `python scripts/_run_team_dispersion.py` (sezione walk-forward).
Δ = +0.00096 su n=5.690, θ_g per stagione stampati (instabilità visibile).
Diagnostico: nessun run in `runs.jsonl`.

---

## Fase 87 — La coda a DUE parametri, riprodotta: isotonica e mistura, entrambe chiuse

**Obiettivo (utente, punto 1).** Chiudere pulite — col protocollo del repo — le
due vie della «coda a due parametri» che l'audit della Fase 86 aveva solo tastato
(PISTE §4-ter): (A) ricalibrazione **isotonica per-soglia** dei totali, (B)
**mistura di due Poisson** su un fattore-tempo. La Fase 85 aveva mostrato che un
solo θ non calibra ogni profondità della coda; qui si prova se un secondo
parametro batte il router θ=1.225 **out-of-sample**.

**Metodo.** `scripts/_run_tail_two_param.py`, sulla cache dei λ,μ del mercato
(7.980 partite). (A) per ogni soglia Over 1.5/2.5/3.5/4.5, mappa isotonica (PAVA,
scritto a mano — sklearn assente) fittata sulle stagioni passate e applicata al
futuro; metro log-loss binario OOS + ECE. (B) `M(s) = ½·q(λ(1+s))⊗q(μ(1+s)) +
½·q(λ(1−s))⊗q(μ(1−s))` con marginali dp θ=1.225 e ρ=−0.06, mean-preserving; s\*
fittato sul passato (griglia 0–0.20) e applicato al futuro; metro exact-score
log-loss OOS con **CI bootstrap appaiato** e scomposizione per-stagione.

**Risultato — (A) isotonica: NEGATIVA su tutte le soglie.** Il router è già
calibrato sui totali: la mappa isotonica **peggiora il log-loss OOS** ovunque —
Over 1.5 **+0.0150**, Over 2.5 +0.0061, Over 3.5 +0.0104, Over 4.5 +0.0109 (l'ECE
migliora solo su Over 1.5, peggiora su Over 3.5/4.5). Riproduce l'audit: la
mis-calibrazione OOS dei totali col router è già ~0, quindi ricalibrare non fa che
aggiungere rumore di stima. **Chiude PISTE §4-ter via (a).**

**Risultato — (B) mistura: guadagno in-sample, ma OOS NON conclusivo e fragile.**
In-sample il minimo è a s≈0.15 (exact-LL Δ **−0.0006**), coerente con l'audit.
Ma il walk-forward smonta la promessa:

| stagione | s\* | Δ exact-LL (mistura − router) |
|---|--:|--:|
| 2020-21 | 0.00 | 0.00000 |
| 2021-22 | 0.15 | **−0.00301** ✓ |
| 2022-23 | 0.15 | −0.00164 ✓ |
| 2023-24 | 0.15 | −0.00055 ✓ |
| 2024-25 | 0.15 | **+0.00140** ✗ |
| 2025-26 | 0.15 | **+0.00125** ✗ |

Aggregato Δ −0.00042, **CI95 [−0.00145, +0.00059], P(meglio) 78.6% → nel rumore**;
e il segno **si ribalta negativo sulle due stagioni recenti** (2024-26). Il
parametro s\*=0.15 è stabile ma il guadagno no: la mistura aiutava l'era
porte-chiuse (2021-24, tanti gol) e **danneggia il calcio recente**. Esattamente
la fragilità OOS che l'audit aveva segnalato — confermata qui con CI e
scomposizione. **Non adottabile; PISTE §4-ter via (b) chiusa.**

**Lezione.** Il «secondo parametro di forma» della coda — nelle sue due
incarnazioni economiche — **non batte il singolo θ in modo conclusivo e
generalizzabile**. È la **seconda** conferma indipendente, dopo il θ per-squadra
(Fase 86-bis), che la coda dei gol è **al tetto della forma**
*(la prima stesura ne contava tre includendo la COM-Poisson della Fase 85: la
Fase 101 l'ha ritirata perché è la dp riparametrizzata, non una forma diversa)*: la
double-Poisson a un parametro è quanto di meglio si può fare senza informazione
nuova. Nota di metodo: l'aggregato «−0.00042 MEGLIO» sembrava una vittoria finché
il CI + la scomposizione per-stagione non l'hanno smontato — **mai concludere da
una media senza il CI e senza guardare le stagioni recenti** (§1.7).

### 📐 Il modello in dettaglio

- **(A)** PAVA: si ordina per predizione, si poolano i blocchi adiacenti che
  violano la monotonia (media pesata), si predice per interpolazione (`np.interp`
  con estremi piatti). Walk-forward: fit su `season < s`, applica a `season == s`.
- **(B)** mistura mean-preserving: `E[home] = ½λ(1+s)+½λ(1−s) = λ` (idem ospite),
  quindi λ,μ restano le medie del mercato; la varianza **cresce** del termine
  fra-componenti ∝ s² → coda più pesante. Marginali `_dp_pmf(·, θ=1.225)`,
  correzione DC ρ=−0.06 sulla matrice mista, rinormalizzata. `s=0` riproduce
  esattamente il router. CI bootstrap: 5.000 ricampionamenti della differenza
  per-partita `ll_mistura − ll_router` sulle predizioni OOS. Riproducibile:
  `python scripts/_run_tail_two_param.py`. Diagnostico, nessun run in `runs.jsonl`.

---

## Fase 88 — Handicap asiatico come benchmark Tier 2: il router prezza il margine come il mercato sharp

**Obiettivo (utente, punto 4).** L'handicap asiatico (AH) è **ridondante come
input** dell'inversione (corr 0.995 con λ−μ, Fase 86), ma è l'unico mercato
**quotato e sharp** (Pinnacle, vig ~2.7%) sulla coda del **margine**. Qui non lo
si usa per stimare: lo si usa per **validare la calibrazione** del router sulla
famiglia-margine (copertura handicap / scarto) contro un prezzo esterno — il
primo test **Tier 2** del progetto, dichiarato ma mai aperto (§1.8).

**Metodo.** `scripts/_run_ah_benchmark.py`, tutte e 3 le leghe (Serie A dai CSV
grezzi, Premier/Liga dai bundle football-data). Per ogni partita con chiusura
1X2+O/U+AH: si inverte 1X2+O/U → λ,μ (ρ=−0.06), si costruisce la matrice del
router (dp θ=1.225), e da lì la **P(la casa copre la linea AH)** come frazione-di-
copertura attesa (gestisce linee intere/mezze/quarti: push=0.5, quarto=0.25/0.75).
Il mercato: devig delle due quote AH di chiusura (Pinnacle se presente). Confronto
su **7.437 partite**: correlazione modello-mercato, **Brier** di ciascuno vs la
copertura realizzata, calibrazione.

**Risultato — il router è ALLA PARI col mercato sharp.**

| lega | n | corr(mod,mkt) | Brier modello | Brier mercato | reale |
|---|--:|--:|--:|--:|--:|
| Serie A | 2.478 | 0.911 | **0.2029** | 0.2029 | 0.474 |
| Premier | 2.490 | 0.909 | **0.2083** | 0.2084 | 0.492 |
| La Liga | 2.469 | 0.924 | **0.2007** | 0.2009 | 0.500 |
| **TUTTE** | **7.437** | **0.915** | **0.2040** | **0.2041** | 0.488 |

Il Brier del router e quello del mercato sono **indistinguibili** (0.2040 vs
0.2041 in aggregato, e a coppie su ogni lega), con correlazione modello-mercato
**0.91-0.92**. Cioè: dai soli λ,μ del 1X2+O/U, il motore prezza la copertura
dell'handicap **con la stessa accuratezza del mercato sharp che quota l'AH
direttamente** — senza aver mai visto le quote AH.

**⚠️ Come NON va detto (rettifica Fase 101).** La prima stesura chiudeva con
«~~è α\*=0 su un mercato nuovo (il margine)~~». **L'encompassing non era mai
stato calcolato** — `_run_ah_benchmark.py` misura solo correlazione, Brier e
medie — e calcolandolo dà il contrario: con α che minimizza il Brier di
`α·router + (1−α)·mercato` sugli stessi 7.437 casi,
`α* = mean((y−k)(m−k)) / mean((m−k)²)` = **1.082**, IC95 bootstrap
**[+0.147, +2.052]**, che **esclude** lo zero (vincolato a [0,1] come in Fase 16:
α\*=1.000). Il motivo è strutturale e non è un edge: il router **non è un
previsore indipendente** dal mercato AH, è una *traduzione* dei λ,μ ricavati da
1X2+O/U — fra due previsori quasi equivalenti (corr 0.915) α\* è mal determinato
attorno a 1 e l'IC è larghissimo. Nota di metodo: il «guadagno del blend»
calcolato ri-fittando α *dentro* ogni ricampionamento bootstrap è **non-negativo
per costruzione** (minimo osservato 1e-10) e non va usato come prova; con α
fissato al campione pieno vale +0.000137, IC95 [−0.000110, +0.000375].

**Come va detto.** Ciò che i dati sostengono è il **pareggio in Brier col mercato
sharp**: ΔBrier (router − mercato) = **−0.000136**, IC95 appaiato
[−0.000362, +0.000083] (Serie A +0.000001 [−0.00038, +0.00038], Premier −0.000187
[−0.00058, +0.00021], Liga −0.000224 [−0.00060, +0.00014]). E, col **protocollo
onesto della Fase 16** (α fittato solo sulle stagioni passate e applicato alla
successiva; stagione = agosto-luglio dalla data football-data, 6 fold 2021→2526,
n=6.518 fuori campione), il blend **non batte il mercato**: Δ Brier pooled
−0.0000058, IC95 [−0.00022, +0.00020], P(Δ<0) 51% — α per stagione −0.59, 0.71,
1.36, 0.83, 1.04, 0.90, cioè un peso che salta attorno a 1 senza stabilizzarsi.
È questo il risultato interessante, ed è già quello che serve al Tier 2: la
struttura DC trasferisce l'informazione del mercato alla famiglia-margine **senza
perdite misurabili**, non «senza informazione propria».

**Onestà.** Sia modello sia mercato prevedono una copertura-casa media ~0.502
contro un realizzato 0.488 (~1.4pp): un lieve ottimismo-casa **condiviso** (in
parte la mia gestione dei push nel lato-mercato, in parte una proprietà della
linea AH). Conta che è **identico per i due** → non è un difetto del router, ed è
sotto il tetto (non si batte il mercato, lo si eguaglia). Il valore Tier 2 è
quindi di **validazione/copertura del listino**, non di edge: ora il router ha un
mercato-margine quotato contro cui è dimostrato calibrato, e può prezzare
handicap e scarto per le leghe/partite dove servono, con l'errore atteso noto.

**Lezione.** Chiude la pista #5 in positivo sul fronte che restava aperto (l'AH
come **benchmark**, non come input): il router estende l'efficienza del mercato
alla coda del margine. Insieme alla Fase 87 completa il quadro degli esiti meno
probabili: **non c'è edge nuovo da spremere** (coda-forma al tetto, Fase 85-87;
margine alla pari col mercato, qui), ma il **valore di copertura calibrata** è
confermato su un mercato in più.

### 📐 Il modello in dettaglio

`P(casa copre h) = Σ_{i,j} M[i,j]·cover(i−j, h)` con `M = score_matrix(λ,μ,
ρ=−0.06, dp_theta=1.225)` e `cover(margine, h)`: 1 se `margine+h ≥ 0.5`, 0.75 se
`=0.25` (quarto vinto), 0.5 se `=0` (push), 0.25 se `=−0.25`, 0 se `≤−0.5`. Il
margine atteso del mercato dalla devig delle due quote AH di chiusura; il
realizzato è `cover(gol_casa − gol_ospite, h)`. Brier `= mean((P − realizzato)²)`.
λ,μ invertiti da 1X2+O/U (nessun input dall'AH). Riproducibile:
`python scripts/_run_ah_benchmark.py`. Diagnostico, nessun run in `runs.jsonl`.

**L'encompassing (aggiunto dalla Fase 101).** Con `m` = P(copre) del router,
`k` = P(copre) del mercato devigato, `y` = copertura realizzata, il blend
`p(α) = k + α·(m − k)` ha per minimo del Brier
`α* = mean((y − k)(m − k)) / mean((m − k)²)` — soluzione in forma chiusa, non
una griglia.

**Riproducibilità (chiusa alla Fase 101-bis).** Alla stesura della Fase 101 il
numero *non* era prodotto da `_run_ah_benchmark.py`, che si fermava a
corr/Brier/medie: era stato ricalcolato a mano dalle colonne interne. Restava
quindi un numero pubblicato e non ri-derivabile — esattamente ciò che il §2-bis
punto 4 vieta. Il blocco è ora **dentro lo script** (`encompassing()`), e
`python scripts/_run_ah_benchmark.py` stampa α\* con IC e il walk-forward.

**Il protocollo di stima di α conta più del risultato.** Il walk-forward ha due
varianti legittime, e danno Δ di **segno opposto**:

| variante | n fuori campione | Δ Brier (blend − mercato) | IC95 | P(Δ<0) |
|---|--:|--:|---|--:|
| α **pooled** su tutte le leghe (pubblicata) | 6.297 | **−0.000064** | [−0.000271, +0.000139] | 0.73 |
| α dalla **sola lega** valutata | 6.297 | +0.000011 | [−0.000236, +0.000265] | 0.46 |

Entrambe sono ampiamente dentro il rumore, e la conclusione («il blend non
batte il mercato fuori campione») non cambia. Ma il segno sì: con un effetto di
questa taglia — 6·10⁻⁵ di Brier — la scelta del pool su cui si stima α pesa
quanto la misura. Motivo per cui adesso lo script le stampa **tutte e due**
invece di una sola: una lettura che cambia segno col protocollo non va
riportata come se il protocollo fosse ovvio. *(Le 1.140 righe escluse sono la
prima stagione di ciascuna delle 3 leghe: non hanno passato da cui stimare α.)*

---

## Fase 89 — Il mercato CAMPIONE DI STAGIONE: il primo mercato non derivabile da una matrice

**Obiettivo (richiesta utente).** Su Polymarket esistono tre mercati liquidi
«2027 Champion» (Premier $4.9M, Liga $2.6M, Serie A $1.1M di liquidità;
overround **4-7.5%** una volta esclusi i segnaposto morti «Team A/B/C», che
avevano book vuoto e falsavano la somma a 3.07). È un mercato che il progetto
**non ha mai toccato in 88 fasi**, e per una ragione strutturale: fino a qui
ogni mercato (1X2, O/U, GG/NG, esatto, multigol, handicap) si ricavava dalla
**matrice dei punteggi di una singola partita**. Il campione no: dipende da
**380 partite congiuntamente** più una regola di classifica. Non si deriva:
va **simulato**.

**Ragionamento / ipotesi.** La Fase 16 ha dimostrato che la chiusura 1X2
ingloba il nostro modello (α\*=0). Ma quella prova vale sulla **famiglia della
singola partita**. L'outright stagionale è fuori da quella famiglia: nessuno ha
mai verificato se il DC, propagato su una stagione intera, dica qualcosa di
sensato. Ipotesi: sì sulle baseline ingenue, ma con un difetto prevedibile —
le forze sono stimate a inizio stagione e tenute **fisse per 10 mesi**, quindi
il simulatore vede solo l'aleatorietà dei risultati, non l'incertezza dei
parametri né la loro evoluzione (mercato estivo, infortuni, allenatori).

**Alternative considerate.** (a) Modello diretto sui punti finali senza simulare
le partite: più semplice ma perde la struttura del calendario e gli spareggi;
(b) forza latente Elo/Bradley-Terry: aggiungerebbe un modello nuovo da tarare;
(c) **Monte Carlo dalle matrici del DC** — scelto: riusa il motore esistente
senza una riga di modellistica nuova, ed è il tracer bullet più corto (§1.1).

**Scelta e protocollo.** `src/models/season_sim.py` +
`scripts/_run_fase89_season_champion.py`. Per ogni stagione S: si fitta il DC
**alla data della prima partita di S** (`as_of_date=start`, nessun dato futuro),
con la config per-lega e il prior neopromosse; si generano le 380 matrici dei
punteggi; si campionano 20.000 stagioni intere; si compila la classifica con le
**regole di spareggio ufficiali**; P(campione) = frazione di stagioni vinte.
Backtest su **24 stagioni-lega** (8 × 3 leghe: la prima stagione di ogni lega
non è backtestabile, manca lo storico).

**Due proprietà non ovvie, entrambe verificate qui.**

1. **L'ordine del calendario è irrilevante.** Con forze costanti dentro la
   stagione, i punti finali dipendono solo dall'**insieme** degli incontri (un
   girone doppio completo), non dalla loro sequenza. Conseguenza pratica: si può
   simulare una stagione **futura senza conoscerne il calendario** — ed è ciò che
   permette di prezzare il 2026-27 oggi. (Se un domani il modello avesse dinamica
   in-season, la proprietà cadrebbe.)
2. **Gli spareggi non sono pedanteria.** Nelle stagioni simulate la parità di
   punti in testa capita nel **5.1%** dei casi (nella realtà: 0 volte su 27), e
   le regole **differiscono per lega**: Serie A e Liga usano gli **scontri
   diretti**, la Premier la **differenza reti**. Il caso che lo dimostra è reale
   e ha conseguenze: nella **Liga 2025-26 Levante, Osasuna e Mallorca chiudono
   TUTTE E TRE a 42 punti**; la **classifica avulsa** fra le tre (Levante 7 −
   Osasuna 5 − Mallorca 3) le ordina 16ª/17ª/18ª → retrocede **Mallorca**,
   mentre con la sola differenza reti generale (−6 / −10 / −14) l'ordine sarebbe
   esattamente invertito e retrocederebbe **Levante**. *(L'audit della Fase 90 ha
   corretto il racconto iniziale, che parlava di una parità a due risolta da un
   duello «4-1»: quel 4-1 è una sotto-cifra vera ma non è il criterio applicato.)* Cambia la composizione della Liga 2026-27, e infatti la rosa che
   Polymarket usa per il «2027 Champion» contiene Levante e non Mallorca: il
   mercato ha ragione, la classifica ingenua no. È in `tests/test_season_sim.py`
   come test di regressione sui dati reali.

**Risultato 1 — il modello batte le baseline, ma il margine dipende da QUALE
baseline** *(numeri corretti dall'audit della Fase 90: la prima versione di
questa fase usava solo le baseline deboli, e la baseline di persistenza —
promessa nel docstring dello script — non era mai stata implementata)*.

| | log-loss sul campione effettivo |
|---|--:|
| **MODELLO (MC dal DC)** | **1.1994** |
| persistenza su 2 stagioni (β\*=2.5, w₂\*=1.5, tarati LOO) — **la più forte** | **1.4293** |
| persistenza su 1 stagione (β\*=2.1, LOO) | 1.6636 |
| «vince il campione uscente» (q ottimo LOO) | 2.6515 |
| «vince il campione uscente» (q=0.33 in-sample, favorevole a lei) | 2.5995 |
| uniforme (1/20) | 2.9957 |

La baseline di **persistenza** assegna `p_i ∝ exp(β·z_i)` con `z` = punti
standardizzati delle stagioni precedenti (media pesata delle ultime due, peso
`w₂` alla più vecchia; neopromosse imputate a `min(punti) − 3`). Usa TUTTA la
classifica, non solo chi ha vinto: è un avversario molto più serio.

| il modello contro… | guadagno | IC95% | stagioni vinte | esito |
|---|--:|---|--:|---|
| «campione uscente» | +1.4521 | [+1.1311, +1.7850] | 24/24 | conclusivo *(ma è la baseline più debole)* |
| persistenza 1 stagione | +0.4642 | [+0.2022, +0.7397] | 19/24 | conclusivo |
| **persistenza 2 stagioni** | **+0.2299** | **[+0.0108, +0.4542]** | **14/24** | **conclusivo per un soffio** |

I numeri onesti sono gli ultimi: la baseline debole gonfiava il guadagno di
**oltre un nat** e portava il conteggio a 24/24. E il vantaggio non è
distribuito: **è quasi tutto Premier** (+0.5657, 7/8), mentre Serie A (+0.1197,
4/8) e La Liga (+0.0045, 3/8) sono nel rumore. Cioè: il simulatore aggiunge
qualcosa di solido dove una squadra domina, poco o nulla dove il titolo è
conteso. Brier multiclasse 0.6584; il campione reale
finisce in media al **rank 1.88** della nostra classifica di probabilità.
Il problema è genuinamente difficile: il campione uscente si ripete solo **8
volte su 24** (33%), anche se il **75%** dei campioni veniva dai primi 2
dell'anno prima (caso estremo: Napoli 2024-25, era 10º).

**Risultato 2 — ma siamo SOVRA-CONFIDENTI, e si vede il meccanismo.**

Dichiariamo in media **60.1%** sul nostro favorito e ne azzecchiamo **41.7%**
(10/24): scarto **−18.4pp = −1.83 SE** (probabile, **non concluso** con n=24 —
serve più potenza). Il meccanismo è diretto e misurabile: il campione **reale**
fa in media **89.1 punti**, il vincitore **simulato** 84.8 (**+4.3**). Con forze
fisse nessuna squadra «si accende» durante l'anno: la classifica simulata è
compressa, e la massa si concentra troppo sul favorito.

| lega | log-loss | favorito azzeccato | P media sul favorito |
|---|--:|--:|--:|
| Premier | **0.7411** | 62% | 73.9% |
| La Liga | 1.3651 | 25% | 58.3% |
| Serie A | 1.4920 | 38% | 47.9% |

La Premier è la più facile (dominio Man City: 6 titoli su 9), la Serie A la più
imprevedibile — coerente con l'intuizione, ma qui è misurato.

**Risultato 3 — la ricalibrazione ingenua NON funziona (negativo, documentato).**
Se la sovra-confidenza è reale, ammorbidire le probabilità con una temperatura
(`p^(1/T)` rinormalizzata) dovrebbe pagare. In-sample il T ottimo è 1.15 e
guadagna 0.0088; ma in **leave-one-out** il log-loss diventa **1.2160**, cioè
**peggio del non fare nulla (1.1994)**. Con 24 osservazioni non c'è abbastanza
segnale per stimare onestamente nemmeno **un** parametro di calibrazione. La
correzione, se esiste, va fatta **strutturalmente** (iniettando la varianza
mancante nel simulatore), non post-hoc.

**Risultato 4 — il confronto col mercato di oggi (2026-27).**

| | NOSTRO | MERCATO | scarto |
|---|--:|--:|--:|
| Inter (Serie A) | 66.8% | 47.0% | **+19.8** |
| Milan | 2.9% | 11.6% | −8.7 |
| Napoli | 5.7% | 12.6% | −7.0 |
| Arsenal (Premier) | 44.8% | 34.0% | **+10.8** |
| Man City | 42.9% | 28.3% | **+14.6** |
| Man United | 0.7% | 11.0% | **−10.3** |
| Chelsea | 0.8% | 9.1% | −8.3 |
| Barcelona (Liga) | 62.4% | 51.4% | **+11.0** |
| Real Madrid | 30.6% | 40.9% | −10.3 |

Il pattern è **lo stesso identificato dal backtest, e per via indipendente**:
troppa massa in cima, troppo poca sugli inseguitori. Il mercato prezza ciò che
il nostro modello non può vedere — che Milan, Man United e Chelsea possono
**rifarsi la squadra in estate**, mentre noi li giudichiamo sui risultati di
maggio. Non è un edge nostro: è una variabile mancante.

**Lezione.** Il mercato campione è (a) il primo che richiede una **simulazione**
e non una matrice; (b) uno dei pochi dove le baseline sono battute in modo
conclusivo, perché il segnale «forza delle squadre» è forte e persistente; (c)
un mercato in cui il nostro difetto è **strutturale e identificato**: manca la
varianza dei parametri e la loro evoluzione. È anche il primo mercato del
progetto con una **finestra d'uso stagionale**: si prezza a inizio stagione, e
va rivisitato ogni anno (vedi `docs/PISTE.md` §5).

**Onestà obbligatoria.** (1) Non esistono quote outright **storiche** nei nostri
dati: quindi «battiamo le baseline» è dimostrato, «battiamo il mercato» **non è
testabile** all'indietro — il confronto 2026-27 è una **fotografia**, non una
misura di edge, e si potrà scorare solo a maggio 2027. (2) n=24 è poco: la
sovra-confidenza è probabile ma non conclusiva. (3) Le classifiche sono calcolate
dai risultati, quindi **senza penalizzazioni di punti** (Juventus 2022-23,
Everton/Nottingham Forest 2023-24): verificato che **nessuna ha mai toccato la
vetta** nelle 27 stagioni, quindi il campione non cambia mai; le posizioni di
metà classifica sì. (4) Le rose 2026-27 vengono dai mercati Polymarket
(informazione esterna agli snapshot), riconciliate coi nomi interni.
**Non usare per scommettere soldi veri.**

### 📐 Il modello in dettaglio

**Il campionamento.** Per ogni incontro si prende la matrice del DC
`M[i,j] = P(gol_casa=i, gol_ospite=j)` (`_score_matrix`, invariata dalla Fase 2),
la si appiattisce in 121 celle e se ne fa la cumulata:
```
cdf[n] = cumsum(M_n.ravel()) ,  cdf[n] /= cdf[n][-1]      # rinormalizza il troncamento
cella  = searchsorted(cdf[n], u) ,  u ~ Uniforme(0,1)
gol_casa = cella // 11 ,  gol_ospite = cella % 11         # max_goals=10 -> K=11
```
La divisione per `cdf[n][-1]` è una **salvaguardia, non una correzione
necessaria**: `_score_matrix` termina già con `matrix /= matrix.sum()`
(`dixon_coles.py`), quindi le matrici arrivano normalizzate e la riga sposta
massa per ~1e-16 (misurato sulle 380 matrici di Serie A 2025-26). Resta perché
rende il campionamento corretto anche se un domani arrivasse una matrice non
normalizzata. *(Precisazione dell'audit Fase 90: la prima stesura la dichiarava
necessaria.)*

**Perché 20.000 simulazioni.** L'errore Monte Carlo su una probabilità `p` è
`sqrt(p(1−p)/N)`: con N=20.000 e p=0.5 vale **0.35pp**, trascurabile rispetto
agli scarti che misuriamo (10-20pp). Verificato empiricamente su 5 semi diversi
(Serie A 2025-26): deviazione standard osservata **0.20-0.35pp** contro
0.22-0.35pp teorici — la teoria regge.

**Gli spareggi.** `TIEBREAK_RULES = {serie_a: (h2h, gd, gf), la_liga: (h2h, gd,
gf), premier_league: (gd, gf)}`, dove `h2h` = classifica avulsa (punti negli
scontri diretti fra le sole squadre a pari punti, poi differenza reti negli
scontri diretti). **Sensibilità misurata**: cambiando la regola da scontri
diretti a differenza reti, la P(campione) si sposta al massimo di **0.93pp**
(Serie A 2025-26, su tutte le 20 squadre). Cioè: la regola va implementata
**giusta** (e cambia chi retrocede, vedi Levante/Mallorca), ma **non muove il
prezzo dell'outright** — un caso in cui il dettaglio conta per la correttezza
dei dati, non per la stima.

**Il fit.** Nessun parametro nuovo: `DixonColesModel(half_life_days=365,
shrinkage=1.5, shots_blend=0.75, blend_signal="xg", promoted_prior=(δ,δ))` con
δ per-lega (0.23 / 0.33 / 0.22, Fasi 7/57) e `as_of_date` = data della prima
partita della stagione. Le neopromosse sono `squadre(S) − squadre(S−1)`: è
informazione **nota prima del via** (le promozioni si decidono a giugno), non
look-ahead.

**Le metriche.** `log-loss = −ln P(campione effettivo)` e
`Brier = Σ_j (p_j − y_j)²` con `y` one-hot: sono **multiclasse a ~20 esiti con
UNA osservazione per stagione**, quindi `experiment_log.compute_metrics` (fonte
unica per i mercati di singola partita, §5) **non è applicabile** — le formule
sono definite in `_run_fase89_season_champion.py` e non duplicano nulla.
IC bootstrap percentile su 10.000 ricampionamenti delle 24 osservazioni.

**Il seed.** `zlib.crc32` invece di `hash()`: l'hash delle stringhe in Python è
randomizzato per processo, usarlo avrebbe reso i run non riproducibili (§1.5).

Riproducibile: `python scripts/_run_fase89_season_champion.py --nsim 20000`
(≈2 minuti). Run in `experiments/runs.jsonl`; dettaglio per stagione in
`experiments/fase89_season_champion.json`.

---

## Fase 89-bis — Perché sbagliamo il campione: la separazione «titolo confermato / titolo che cambia»

**Obiettivo (domande dell'utente).** «Quante volte hai indovinato il vincitore?
Hai imparato perché hai sbagliato le altre? Altri dati potrebbero aiutarti?»
Il `24/24 meglio della baseline` della Fase 89 nasconde esattamente questo.

**A. L'anatomia — 10/24, ma la distribuzione degli errori è tutt'altro che casuale.**

Il campione vero finisce nella nostra classifica di probabilità al 1º posto
10/24, al 2º 9/24, al 3º 4/24, al 5º una sola volta (Milan 2021-22): è nel
**top-3 in 23 casi su 24 (96%)**. Non sbagliamo a riconoscere le contendenti.

La separazione che spiega tutto:

| | stagioni | favorito azzeccato |
|---|--:|--:|
| il titolo **resta** alla stessa squadra | 8 | **8/8 = 100%** |
| il titolo **cambia** mano | 16 | **2/16 = 12%** |

Negli errori il campione uscente si riconferma **0 volte su 14**. E il nostro
favorito **è** il campione uscente nel 71% dei casi. Cioè: il modello, fittato
sui risultati passati, dice in sostanza «continua chi comandava» — ed è giusto
tutte le volte che è vero, sbagliato quasi tutte le volte che non lo è. **Non
ha alcun meccanismo per anticipare un cambio al vertice**, e non può averlo,
perché l'informazione che lo anticipa non è nei risultati passati.

**Dove sta davvero l'errore.** Non nella forma della distribuzione sul gruppo
di testa, ma nella **scelta dentro il gruppo**:

| | dichiarato | reale | scarto |
|---|--:|--:|--:|
| P(vince uno dei nostri primi 2) | 82.7% | 79.2% | −3.5pp |
| P(vince uno dei nostri primi 3) | 92.2% | 95.8% | +3.7pp |
| **scelta dentro il top-2** | **71.6%** | **52.6%** (10/19) | **−19pp** |

Siamo **calibrati sul gruppo di testa** e sbagliati solo su come dividiamo la
probabilità fra i suoi membri: dato che il campione è uno dei nostri primi due,
diamo al nostro primo il **71.6%** (media di `p₁/(p₁+p₂)`) e ne azzecchiamo il
**52.6%** — un **lancio di moneta**. *(Audit Fase 90: la prima stesura
confrontava `p₁` marginale, 61.1%, con una frequenza condizionata: due quantità
diverse, e la sovra-confidenza ne usciva sottostimata di 10 punti.)* La sovra-confidenza cresce con la confidenza dichiarata
(sopra il 70%: dichiarato 78.4%, realizzato 55.6%, −22.9pp).

**B. Il valore rosa NON aiuta (negativo).** Ipotesi naturale: serve un segnale
che veda il **mercato estivo**, che i risultati di maggio non contengono.
`squad_value` è già negli snapshot, è rilevato a inizio stagione e il progetto
lo aveva bocciato solo sulle **singole partite** (Fasi 4c/66-70) — in PISTE.md
avevo esplicitamente scritto che quel verdetto «non copre» il problema
dell'outright pre-stagionale. **Testato: lo copre.**

| | log-loss | favorito azzeccato | sulle 16 di cambio |
|---|--:|--:|--:|
| DC base | **1.1994** | 10/24 | 2/16 |
| DC + covariata `squad_value` | 1.2384 | 9/24 | 2/16 |

Guadagno **−0.0390** (IC95% [−0.1055, +0.0205]): non conclusivo, ma il
punto-stima è **peggiorativo**. *(Audit Fase 90: la prima stesura riportava
−0.0444 perché le due braccia usavano due simulatori diversi — uno con gli
spareggi di lega, l'altro con la sola differenza reti; ~9% del delta era
artefatto. Ora entrambe passano da `simulate_season(features=…)`.)* Il β è **sempre positivo** (media +0.115): il segnale
esiste — rose più costose segnano di più — ma è **già contenuto nei gol e
nell'xG**, esattamente come sulle singole partite. Un controllo grezzo lo
conferma: la squadra col valore rosa più alto è campione 11/24 (46%) contro le
nostre 10/24, e il rank medio del nuovo campione è **identico** (2.31) per i due
segnali. Diverso, non migliore.
*Caveat dichiarato*: `squad_value` è rilevato attorno al 1º settembre, 2-3
giornate dopo il via — il test era quindi **favorevole** alla covariata, e
perde lo stesso.

**C. La varianza che manca, misurata.** Fittando il DC a inizio e a fine
stagione sulle stesse 480 squadre-stagione, la forza netta (attacco − difesa)
si sposta con deviazione standard **0.189**, contro una dispersione **fra**
squadre di 0.434: la deriva vale il **44%** della distanza tipica fra due
squadre (correlazione pre/post 0.903). Il simulatore, tenendo le forze fisse
per 10 mesi, ignora esattamente questa quantità. *Limite dichiarato*: la stima
di inizio stagione è più rumorosa di quella di fine, quindi 0.189 mescola
deriva vera ed errore di stima — è un **limite superiore**.

**Lezione e conseguenza operativa.** La risposta a «servono altri dati?» è: non
questi. Il valore rosa è ridondante; ciò che manca (chi cambia allenatore, chi
si rinforza davvero, chi si infortuna) non è in nessun dato che possediamo. Ma
la diagnosi indica un rimedio che **non richiede dati nuovi**: poiché siamo
calibrati sul gruppo di testa e sbagliati solo nella spartizione interna, la
correzione giusta è **appiattire la spartizione fra i leader** iniettando la
deriva misurata in C — non tarare un parametro sui 24 esiti (già fallito con la
temperatura, Fase 89). È anche ciò che il mercato fa: Polymarket dà Inter 47%
dove noi diamo 66.8%, e distribuisce il resto su Juve/Napoli/Milan.

### 📐 Il modello in dettaglio

**La covariata.** `squad_value` entra nel tasso atteso come
`λ = exp(att_casa + dif_ospite + γ + β·(z_casa − z_ospite))` e
`μ = exp(att_ospite + dif_casa − β·(z_casa − z_ospite))`, con
`z = (log(valore) − media) / dev.std` imparate sul training
(`_COVARIATES["squad_value"] = (home_squad_value, away_squad_value, "log")`,
`dixon_coles.py`). β è stimato **insieme** agli altri parametri nella stessa
verosimiglianza pesata. In simulazione le feature vanno passate a
`predict_match(h, a, features=...)` per ogni incontro (il valore è costante per
squadra dentro la stagione: verificato, 1 solo valore distinto per squadra).

**La deriva.** Per ogni squadra-stagione: `forza(t) = attacco(t) − difesa(t)`
stimata due volte con lo stesso identico modello, cambiando solo `as_of_date`
(prima partita vs giorno dopo l'ultima). `deriva = forza_fine − forza_inizio`;
si riportano `sd(deriva) = 0.189`, `sd(forza_inizio) = 0.434` e il loro rapporto
0.44. La correlazione 0.903 dice che l'ordinamento si conserva in larga parte:
la deriva sposta, non rimescola.

**Le metriche di calibrazione di gruppo.** `P(top-k) = Σ` delle k probabilità
più alte del nostro vettore; il realizzato è la frazione di stagioni in cui il
campione vero ha rank ≤ k. IC bootstrap percentile su 10.000 ricampionamenti
delle 24 differenze appaiate.

Riproducibile: `python scripts/_run_fase89bis_anatomy.py --squad-value`
(≈4 minuti). Dettaglio in `experiments/fase89bis_anatomy.json`.

Diagnostico: nessun run in `experiments/runs.jsonl` — è un'anatomia dei run già
registrati alla Fase 89 (nessun cambio di config, nessun modello nuovo scorato);
l'artefatto riproducibile è il JSON qui sopra.

---

## Fase 90 — Terzo audit orchestrato: i numeri-titolo della Fase 89 erano gonfiati

**Obiettivo (richiesta utente).** «I dati sono giusti? Ciò che è scritto è
giusto? Verifica tutti i backtest. Sistema il repo. I ragionamenti sono quelli
giusti, o ne abbiamo tralasciati? Ci sono punti in sospeso?» Terzo audit del
progetto dopo le Fasi 84 e 86, ma il primo che arriva **subito dopo** un lavoro
nuovo (le Fasi 89/89-bis, fatte lo stesso giorno) invece che a distanza.

**Metodo.** Workflow a 13 agenti: **6 lenti indipendenti** (dati, numeri, codice,
ragionamenti, punti in sospeso, migliorie), ognuna seguita da una
**contro-verifica avversaria** che prova a *demolire* i reperti invece di
confermarli, con istruzione esplicita di scartare in caso di dubbio; poi una
sintesi. Tutti gli agenti in **sola lettura**: le correzioni applicate a mano
dopo, per non avere scritture concorrenti. ~2h10, 2 milioni di token.

**Risultato 1 — i dati reggono, e con margine.** Le 10.260 righe dei tre snapshot
sono state **ri-derivate dalle fonti grezze congelate**: zero discrepanze su gol,
risultato, data e tiri in porta; zero duplicati; ogni coppia (casa, ospite)
esattamente una volta in tutte e 27 le stagioni-lega; tutte e 24 le transizioni
fra stagioni sono 3-OUT/3-IN reali (nessun alias mancante, il bug «Hellas Verona»
non si è ripetuto). Le 27 classifiche finali ricalcolate **senza importare il
codice del progetto** coincidono al 100% con `final_table`. Trovata **una sola
anomalia mai dichiarata**: `Udinese-Roma 25/04/2024` è una partita **sospesa
sull'1-1 e ripresa**, e le sue quote di chiusura prezzano la ripresa — P(pareggio)
devigata **0.558** contro un massimo di 0.372 su tutte le altre 10.259 partite.
Il dato è fedele alla fonte, ma accoppia un prezzo condizionato a uno stato di
gioco con un esito full-match: falsa nella direzione a noi favorevole, e vale
~9-12% dell'edge beat-the-close della Fase 51 (che resta dello stesso segno).
Ora è dichiarata in `docs/DATI.md` §2.

**Risultato 2 — il difetto grosso: le baseline della Fase 89 erano uomini di
paglia.** Il docstring dello script prometteva una baseline «forza dalla
classifica precedente» che **non era mai stata implementata**. Implementata qui:

| il modello contro… | guadagno | IC95% | stagioni | esito |
|---|--:|---|--:|---|
| «vince il campione uscente» | +1.4521 | [+1.1311, +1.7850] | 24/24 | *(baseline debole)* |
| persistenza 1 stagione | +0.4642 | [+0.2022, +0.7397] | 19/24 | conclusivo |
| **persistenza 2 stagioni** | **+0.2299** | **[+0.0108, +0.4542]** | **14/24** | **per un soffio** |

La baseline debole gonfiava il guadagno di **oltre un nat** e portava il
conteggio a 24/24. E il vantaggio **non è distribuito**: +0.5657 in Premier
(7/8), +0.1197 in Serie A (4/8), **+0.0045 in Liga** (3/8). La conclusione
«il simulatore batte le baseline» sopravvive; i due numeri-titolo no.
*(Nota di metodo: la griglia della baseline è stata estesa finché l'ottimo non è
caduto all'interno — β\*≈2.5, w₂\*≈1.5. Con un tetto a w₂=1 la baseline usciva
sottostimata e il guadagno del modello sovrastimato: un ottimo al bordo della
griglia è sempre un sospetto.)*

**Risultato 3 — due bug reali nel tool Polymarket, verificati su dati live.**
(a) L'1X2 assegnava le domande per **prima parola** del nome squadra: nei derby
(«Manchester City» / «Manchester United», «Real Madrid» / «Real Betis») la
domanda dell'ospite finiva nel ramo della casa e **l'intera partita usciva senza
1X2** — 59 casi su 59 nel campione dell'auditor. (b) I mercati **per-tempo** e
**per-squadra** («1st Half O/U 2.5», «Roma O/U 2.5») contengono la stessa
sottostringa del mercato vero e, con una `re.search`, l'ultimo incontrato lo
**sovrascriveva**: O/U 2.5 sbagliato in 6 partite su 28 (0.500 estratto contro
0.295 reale). Entrambi corretti, con test di regressione. Aggiunto anche un
flag `usable`: su book morti (spread bid/ask fino a 0.99) l'«overround» esce
0.895 o 1.679 e quel prezzo non va dato in pasto a `market_implied`.

**Risultato 4 — tre imprecisioni di misura nelle Fasi 89/89-bis.**
- Il confronto «61.1% contro 53%» sulla scelta dentro il top-2 metteva una
  probabilità **marginale** accanto a una frequenza **condizionata**. La quantità
  giusta è `p₁/(p₁+p₂)` = **71.6%** contro **52.6%**: la sovra-confidenza era
  sottostimata di 10 punti, non sopravvalutata.
- Il test su `squad_value` confrontava **due simulatori diversi** (uno con gli
  spareggi di lega, l'altro con la sola differenza reti): ~9% del delta era
  artefatto. Rifatto alla pari: −0.0390 invece di −0.0444. Verdetto invariato.
- `simulate_season` restituiva un `rank` che ignorava gli spareggi e
  contraddiceva `champion_prob` nell'~1% delle simulazioni. Latente (nessuno lo
  usava) ma è output pubblico: ora la vetta è coerente per costruzione.

**Risultato 5 — cosa NON era stato ragionato.** Due omissioni sostanziali:
(a) il simulatore calcola già una matrice `rank` e **la butta via**: da lì
escono P(top-4) e P(retrocessione), mercati veri, con **480 osservazioni
binarie** invece delle 24 di cui ci lamentiamo, senza una riga di modellistica
nuova; (b) diciamo che «battiamo il mercato non è testabile all'indietro»
sull'outright perché mancano le quote outright storiche — vero alla lettera, ma
il **parere del mercato sulle forze** c'è in ogni stagione (le quote 1X2+O/U di
ogni partita, invertibili col motore titolare: 21 stagioni-lega su 24 hanno la
copertura), e quel benchmark non è mai stato costruito. Inoltre la deriva 0.189
è per circa il **38% in varianza rumore di stima** (deriva vera ≈0.14-0.15):
le due leve previste in PISTE **non vanno sommate**.

**Risultato 6 — cosa ha retto.** Tre critiche promettenti sono state **demolite
in contro-verifica**: il test di Poisson-binomiale non è invalidato dalla
dipendenza fra stagioni; la spiegazione del fallimento della ricalibrazione era
già quella giusta; le Fasi 53 e 75 non si contraddicono. E sono stati superati
controlli mai fatti prima: α\*=0 della Fase 16 tiene anche col **log-pool** (il
DC aggiunge +0.00005); la bocciatura di `squad_value` tiene anche sull'uso
alternativo mai provato (delta estivo anno-su-anno); la conclusione della Fase 89
sopravvive a bootstrap **a blocchi** per lega e per stagione. Riprodotti alla
sesta cifra tutti i numeri di testa delle fasi precedenti campionati (gap
+0.0165, ROI −15.7% su 864 bet, O/U 0.6885, δ 0.23/0.33/0.22, θ 1.225/1.138,
Brier AH 0.2040), e le Fasi 89/89-bis sono **riproducibili bit-per-bit** fra
processi diversi.

**Lezione.** Il valore dell'audit non è stato trovare dati sbagliati — quelli
erano a posto — ma **il metro**: la Fase 89 misurava contro un avversario che non
aveva alcuna possibilità, e nessuno se ne era accorto perché il docstring
prometteva la baseline giusta e il codice non la conteneva. Regola operativa che
ne esce: **quando una fase dichiara di battere una baseline, la baseline va
implementata come se dovesse vincere lei** — e se l'ottimo dei suoi
iperparametri cade al bordo della griglia, la griglia è troppo stretta.

### 📐 Il modello in dettaglio

**La baseline di persistenza** (`persistence_probs` in
`_run_fase89_season_champion.py`):
```
z_i   = (punti_i - media(punti)) / dev.std(punti)        # stagione precedente
punti = (punti_{S-1} + w2 * punti_{S-2}) / (1 + w2)      # se w2 > 0
p_i   = exp(beta * z_i) / somma_j exp(beta * z_j)
```
Le neopromosse, assenti dalla classifica precedente, sono imputate a
`min(punti) − 3`: sono in media più deboli dell'ultima classificata, che è
appena retrocessa. `beta` misura quanto «conta» la classifica passata (β=0 →
uniforme) e `w2` quanto pesa la penultima stagione. Entrambi tarati in
**leave-one-out**: per ogni stagione si ottimizza sulle altre 23 e si valuta su
quella esclusa, così la baseline non è penalizzata da una taratura in-sample
mentre il modello lo sarebbe. Ottimi: β\*=2.5, w₂\*=1.5 (interni alla griglia
β∈[0,4], w₂∈{0, 0.5, 1, 1.5, 2}).

**La quota condizionata del top-2.** Dato che il campione è uno dei nostri primi
due, la nostra probabilità che sia **il primo** è `p₁/(p₁+p₂)`, non `p₁`.
Confrontare `p₁` (marginale) con la frequenza condizionata 10/19 mescolava due
quantità diverse. Media di `p₁/(p₁+p₂)` sulle 19 stagioni: **0.716**.

**La temperatura**, ora riproducibile (`temperature_recal`):
`p_i(T) = p_i^{1/T} / Σ_j p_j^{1/T}`, griglia T∈[0.80, 3.00] passo 0.01.
T\*=1.15 in-sample (guadagno 0.0088), ma in leave-one-out **1.2160 contro
1.1994**: peggio del non fare nulla.

Riproducibile: `python scripts/_run_fase89_season_champion.py --nsim 20000` e
`python scripts/_run_fase89bis_anatomy.py --squad-value`. 158 test verdi.

Diagnostico: nessun run in `experiments/runs.jsonl` — è un audit, non un
esperimento: ri-esegue e corregge i numeri della Fase 89, il cui run
(`phase 89`) resta il record storico immutato del registro.

---

## Fase 91 — I mercati POSIZIONALI: il simulatore è calibrato in alto e sbaglia in basso (ed è colpa del prior)

**Obiettivo.** L'audit della Fase 90 ha notato che `simulate_season` calcola la
matrice delle **posizioni** di ogni stagione simulata e ne usa solo la prima riga
(il campione), buttando via il resto. Da lì escono due mercati veri — **zona
Champions** e **retrocessione** — e soprattutto **480 osservazioni binarie** per
mercato (20 squadre × 24 stagioni-lega) invece delle 24 del campione, di cui il
progetto si lamentava. Zero modellistica nuova, stesse simulazioni: è la leva col
miglior rapporto valore/costo che il progetto avesse aperto.

> ⚠️ **RETTIFICA (Fasi 92 e 92-bis, verificata dall'audit della Fase 101).** I
> numeri dei Risultati 1-3 qui sotto sono quelli **pre-fix del prior** (Fase 92)
> e **pre-bootstrap a grappoli** (Fase 92-bis). Come si è fatto con la Fase 89,
> il testo storico resta; questi sono i valori dell'artefatto corrente
> `experiments/fase91_positions.json`:
>
> | quantità | qui sotto (pre-fix) | artefatto corrente |
> |---|--:|--:|
> | top-4: guadagno vs tasso base | +0.2786 [+0.2208, +0.3345] | **+0.2787 [+0.2130, +0.3304]** |
> | top-4: guadagno vs persistenza | +0.0273 [+0.0037, +0.0502] «conclusivo» | **+0.0274 [−0.0006, +0.0522] — NON conclusivo per IC**; test dei segni 19/24, p=0.0066 |
> | retrocessione: vs tasso base | +0.0875 [+0.0369, +0.1360] | **+0.0925 [+0.0465, +0.1341]** |
> | retrocessione: vs persistenza | −0.0116 [−0.0410, +0.0150] | **−0.0066 [−0.0364, +0.0208]** |
> | neopromosse: dichiarato → realizzato | 58.7% → 48.6% (−10.1pp) | **54.7% → 48.6% (−6.1pp)** |
> | resto della lega | 7.3% → 9.1% (+1.8pp) | **8.0% → 9.1% (+1.1pp)** |
> | ECE retrocessione / top-4 | 0.0589 / 0.0137 | **0.0479 / 0.0140** |
> | casi con P(retro) > 60% | 37, di cui 36 neopromosse, 19 salvate | **30, di cui 29 neopromosse, 15 salvate** |
>
> La **conclusione non cambia** (il top-4 è calibrato, la retrocessione no, il
> colpevole è il prior), ma «entrambi conclusivi» sul top-4 **non regge**: a
> reggere è il test dei segni, non l'intervallo. E la fascia oltre il 90% non
> «sparisce» (Fase 92): scende a 3 casi — 94.3% dichiarato contro 66.7%
> realizzato — e semplicemente non viene più stampata (soglia n≥5).

**Risultato 1 — il TOP-4 è ottimamente calibrato e batte anche la persistenza.**

| | log-loss | Brier | ECE |
|---|--:|--:|--:|
| **MODELLO** | **0.2218** | **0.0675** | **0.0137** |
| persistenza (logistica sui punti precedenti, LOO) | 0.2491 | 0.0769 | — |
| tasso base (4/20) | 0.5004 | 0.1600 | — |

Guadagno **+0.2786** sul tasso base (IC95% [+0.2208, +0.3345]) e **+0.0273** sulla
persistenza (IC95% [+0.0037, +0.0502]): **entrambi conclusivi**. E la calibrazione
è quasi perfetta su tutte le fasce — lo scarto massimo è **1.4pp**:

| dichiarato | n | realizzato | scarto |
|---|--:|--:|--:|
| 0-10% | 309 | 1.6% | +0.3pp |
| 10-30% | 52 | 19.2% | +0.6pp |
| 30-50% | 32 | 37.5% | −1.0pp |
| 50-70% | 26 | 57.7% | −0.7pp |
| 70-90% | 24 | 79.2% | −1.4pp |
| 90-100% | 37 | 94.6% | −1.4pp |

Con 480 osservazioni questa non è una coincidenza: sul piazzamento in zona
Champions il simulatore dice il vero.

**Risultato 2 — la RETROCESSIONE è rotta, e in modo spettacolare.**

Batte il tasso base (+0.0875, IC95% [+0.0369, +0.1360]) ma **non batte la
persistenza** (−0.0116, IC95% [−0.0410, +0.0150]: punto-stima peggiore). E la
calibrazione crolla proprio dove dovrebbe essere più affidabile:

| dichiarato | n | realizzato | scarto |
|---|--:|--:|--:|
| 0-10% | 301 | 4.3% | +2.4pp |
| 10-30% | 90 | 22.2% | +4.0pp |
| 30-50% | 37 | 43.2% | +4.5pp |
| **50-70%** | 32 | **40.6%** | **−19.6pp** |
| **70-90%** | 15 | **46.7%** | **−30.3pp** |
| **90-100%** | 5 | **60.0%** | **−32.2pp** |

Quando dichiariamo che una squadra è **quasi certamente** retrocessa, ci
azzecchiamo il **60%** delle volte.

**Risultato 3 — il colpevole ha un nome: il prior di cold-start.**

Dei **37 casi** con P(retrocessione) > 60%, **36 sono neopromosse (97%)** — e
**19 si sono salvate**. La calibrazione separata è netta:

| | n | dichiarato | realizzato | scarto |
|---|--:|--:|--:|--:|
| **neopromosse** | 72 | **58.7%** | **48.6%** | **−10.1pp** |
| resto della lega | 408 | 7.3% | 9.1% | +1.8pp |

Il resto della lega è **calibrato**. Tutta la mis-calibrazione sta sulle
neopromosse. La causa è il prior δ (0.23 / 0.33 / 0.22), che fu tarato sul
**log-loss della singola partita** (Fasi 7/57): lì è ottimo, ma propagato su **38
giornate** diventa troppo severo, perché la penalizzazione si accumula.

I nomi lo confermano — e sono gli stessi della Fase 89-bis: Verona 1920 (92.5%
dichiarato → 9ª), Sunderland 2526 (91.6% → 7ª), Nott'm Forest 2223 (86.2% →
16ª), Leeds 2021 (79.8% → 9ª), Sheffield United 1920 (75.5% → 9ª). **Leeds,
Sheffield United e Sunderland sono esattamente tre delle sei derive di forza più
grandi misurate alla Fase 89-bis** (+0.81, +0.64, +0.63): le squadre che il
modello condanna sono proprio quelle che si trasformano di più durante l'anno, e
le forze fisse non possono vederlo. Due fasi indipendenti, stesso meccanismo.

**Lezione.** (a) Il simulatore **non è "sovra-confidente" in generale**: è
calibrato sul grosso della classifica e sbaglia in due punti precisi — la
spartizione fra i leader (Fase 89-bis) e le neopromosse (qui). (b) **Un
iperparametro tarato su un orizzonte non è valido su un altro**: δ è ottimo sulla
partita e troppo severo sulla stagione. È la prima volta che il progetto trova
una costante ufficiale che *dipende dall'orizzonte di predizione*, e apre una
pista concreta: **ritarare δ sul bersaglio stagionale**, tenendo quello attuale
per i mercati di partita.

**Onestà.** Non esistono quote storiche nemmeno per top-4 e retrocessione: si
dimostra «battiamo le baseline», non «battiamo il mercato». Le due definizioni
sono **posizionali** (primi 4 / ultime 3): la corrispondenza con la Champions
vera cambia per stagione e lega, e non la si insegue.

### 📐 Il modello in dettaglio

**Le probabilità** vengono dalla matrice `rank` già calcolata:
```
P(top-4)_i        = media_s [ rank[s, i] <= 4 ]
P(retrocessione)_i = media_s [ rank[s, i] >= n_squadre - 2 ]
```
**La baseline di persistenza**: `p = sigmoide(a + b·z)` con `z` = punti
standardizzati della stagione precedente (neopromosse imputate a `min(punti)−3`),
`(a,b)` stimati per massima verosimiglianza in **leave-one-out per
STAGIONE-LEGA**, non per squadra: le 20 squadre della stessa classifica non sono
indipendenti (una sola somma-zero le lega), quindi escluderne una lascerebbe le
altre 19 nel training e la baseline vedrebbe quasi tutto.

**ECE** (Expected Calibration Error) = `Σ_fasce (n_fascia/n) · |media(p) −
media(y)|` su 10 fasce equispaziate.

**Gli spareggi al confine** (verificato qui): al 4º/5º e al 17º/18º posto la
parità di punti capita nel **~15%** delle stagioni simulate — tre volte più che
in vetta — e `rank` la risolve per differenza reti anziché con la classifica
avulsa di Serie A/Liga. Ma l'impatto sulla probabilità **aggregata** è
trascurabile: confrontando differenza reti e **sorteggio** (il limite superiore
della sensibilità), lo scarto medio è **0.14pp** e il massimo **0.91pp** — le
parità si compensano fra le squadre.

Riproducibile: `python scripts/_run_fase91_positions.py --nsim 20000` (~2 min).
Run in `experiments/runs.jsonl`, dettaglio in `experiments/fase91_positions.json`.

---

## Fase 92 — Quarto audit (per aree): la diagnosi centrale era invertita, e il prior non atterrava dove diceva

**Obiettivo (richiesta utente).** «Fai un audit completo di tutto il branch
main.» Quarto audit del progetto, ma il primo organizzato **per AREA del repo**
(motori matematici, pipeline dati, script, test, documentazione, artefatti)
invece che per domanda — apposta per coprire angoli che gli audit precedenti,
tutti organizzati per domanda, non avevano toccato. 13 agenti, ~3h20, contro-
verifica avversaria su ogni reperto, tutti in sola lettura.

**Risultato 1 — LA DIAGNOSI CENTRALE DEL PROGETTO ERA ROVESCIATA.**

Per 80 fasi il progetto ha ripetuto che «il gap col mercato vive quasi tutto nel
PAREGGIO». È il titolo dell'Arco 2, sta nel GLOSSARIO, ed è la motivazione
esplicita di tre leve: inflazione della diagonale (12b), ρ dinamico (18),
φ(|λ−μ|) (35). Il ragionamento originale (Fase 9) era:

> «il mercato *12* non richiede di stimare la **massa** del pareggio, solo chi
> vince; il suo gap è quasi nullo (+0.0020) → il termine "chi vince" è ~0 → il
> grosso del gap è il pareggio».

**`P(12) = P(1) + P(2) = 1 − P(X)` è un'identità.** Prezzare il "12" *è*
prezzare la massa del pareggio. Quel +0.0020 non dice che sappiamo prezzare chi
vince: dice che sappiamo prezzare **il pareggio**. L'errore è logico, non
numerico — il numero era giusto, il significato opposto.

La scomposizione corretta è la chain rule del log-loss, e ricompone a **sei
decimali**:

```
LL(1X2) = LL(pari vs non-pari) + P(non-pari)·LL(casa vs ospite | non-pari)
          \___ massa-pareggio ___/   \______ discriminazione ______/
```

| Serie A, 2.280 partite | log-loss | quota del gap |
|---|--:|--:|
| gap totale | **+0.016699** | 100% |
| massa-pareggio *(= il mercato «12»)* | +0.002010 | **12.0%** |
| discriminazione casa/ospite | +0.014690 | **88.0%** |

E vale su **tutte e tre le leghe**, anzi è più forte altrove:

| lega | gap totale | massa-pareggio | discriminazione |
|---|--:|--:|--:|
| Serie A | +0.016699 | 12.0% | **88.0%** |
| Premier | +0.020632 | 5.5% | **94.5%** |
| La Liga | +0.016250 | 15.0% | **85.0%** |

**La conseguenza retroattiva è la parte interessante**: spiega perché *tutte* le
leve costruite su quella diagnosi abbiano prodotto guadagni minuscoli o nulli
(12b −0.0004 non robusto, 18 instabile sui bound, 35 +0.0006 in Premier).
**Aggredivano il 12%.** Non erano leve sbagliate in sé: erano puntate sul
termine piccolo. Il verdetto «siamo al tetto» resta valido — ma ora si sa che il
tetto è nella **discriminazione casa/ospite**, ed è lì che va cercata
l'informazione mancante, non nella correlazione dei punteggi.

**Risultato 2 — il prior neopromosse non atterrava dove dichiarato.**

Il docstring del modello promette: «una neopromossa con 0 partite finisce
**esattamente** sul prior». Vero per la difesa (+0.2300 esatto), **falso per
l'attacco**: le squadre a zero partite atterravano fra −0.28 e −0.39 invece di
−0.23. Il meccanismo: la penalità di identificabilità
`P·media(attacco)²` spinge tutte le squadre con la stessa forza, ma quelle con
dati la resistono (hanno curvatura di verosimiglianza) mentre **una squadra
senza partite non ha altra curvatura che lo shrinkage** — è l'unico punto
cedevole del sistema e assorbiva quasi tutto lo spostamento. L'asimmetria fra
attacco (sbagliato) e difesa (esatta) è la firma: la penalità tocca solo
l'attacco.

Il δ *effettivamente applicato* valeva quindi 0.31-0.39 invece di 0.23 — dal 35%
al 68% più severo — **e cambiava da stagione a stagione**, cioè non era
ri-derivabile (§2-bis). Corretto calcolando il vincolo sulle sole squadre con
dati: ora tutte e 5 le neopromosse a zero partite atterrano su −0.2300 /
+0.2300 esatti, con test di regressione.

**Impatto misurato**: sui mercati di partita è trascurabile (1X2 2025-26
0.9925 → 0.9924; Premier 1.0259 → 1.0255; Liga invariato) — le conclusioni
pubblicate reggono. Ma sui **mercati stagionali** no: la Fase 91 aveva
attribuito al prior una mis-calibrazione delle neopromosse di **−10.1pp**;
corretto il bug, scende a **−6.1pp** (ECE 0.0589 → 0.0479, e sparisce del tutto
la fascia «oltre il 90%»). Cioè **il 40% di quella mis-calibrazione era questo
difetto**, non l'effetto-orizzonte che le avevo attribuito. Il resto è reale e
la pista resta aperta, ridimensionata.

**Risultato 3 — la regola non negoziabile n.1 non era protetta da alcun test.**

`grep -rn as_of_date tests/` non restituiva nulla: nessun test passava mai la
data di taglio a `fit()`. Mutando il filtro da `date < as_of` a `date <= as_of`
la suite restava **158/158 verde** e il backtest **migliorava** (1X2 0.9925 →
0.9863, gap col mercato +0.0141 → +0.0079). Cioè: una contaminazione futura si
sarebbe presentata come una **scoperta**. Aggiunti tre test (no-look-ahead con
il caso di bordo sulla data esatta, la controprova su tutta la storia, e
l'emivita con il rapporto 0.5 esatto), e **verificato per mutazione** che ora
prendono il difetto: `<`→`<=` fallisce, il segno del decadimento invertito
fallisce, il prior col leak fallisce.

**Risultato 4 — un cron diventato attivo in silenzio.** Lo schedule mensile di
`import_dataset.yml` (`0 5 1 * *`) era stato scritto quando il file non stava sul
branch di default e non poteva partire; col passaggio a main (Fase 82) è
diventato attivo, e il primo fire sarebbe stato il **2026-08-01**. Avrebbe
committato ~51 MB di dataset aggiornato **senza rigenerare gli snapshot**,
creando una divergenza silenziosa fra la fonte grezza (nuova) e i dati su cui
girano tutti i backtest (vecchi), e senza una riga nel registro. Disattivato,
lasciando l'esecuzione a comando.

**Risultato 5 — cosa ha retto.** L'audit ha ri-verificato *eseguendo*: il
walk-forward ufficiale riproduce 0.979687 / 0.963191 / **+0.016496** — che però
è il valore **PRE-fix** (il +0.0165 storico del README, misurato prima della
correzione del prior del Risultato 2). Eseguito col codice corretto qui sopra la
media diventa **0.979890 / 0.963191 / +0.016699**, ed è quella la versione
coerente con la tabella di scomposizione di questa stessa fase
(0.576618 + 0.403273 = 0.979890). Il numero-bandiera del progetto passa quindi a
**+0.0167 / 0.9799** (rimisurato alla Fase 101); i due numeri hanno convissuto
nella fase senza spiegazione fino ad allora. Hanno retto:
α\*=0 della Fase 16, i CI della Fase 17, il backtest
2025-26, le impronte dati, le correzioni della Fase 90 (tutte atterrate: i
numeri ritirati non esistono più in alcun file, i due bug Polymarket sono
corretti *e* protetti da test veri verificati su 13.597 eventi live). Aree
pulite e verificate numericamente: l'inversione 1X2+O/U (soluzione unica,
multi-start concorde, nessun bound toccato su 7.980 partite), la double-Poisson
(mean-preserving a 1e-13), copula e bivariato (marginali preservati a ≤1.6e-5),
la coerenza interna del DC (P(1X)=P(1)+P(X) a 0.00e+00), gli snapshot congelati
rigenerabili bit-identici.

**Lezione.** Tre audit avevano guardato *le stesse cose da angolazioni diverse*
e nessuno aveva messo in dubbio **la frase che dà il titolo a un intero arco**.
Il difetto non era in un numero — ogni numero era giusto — ma nel **passaggio
logico** fra un numero e la sua interpretazione, e quel passaggio non era mai
stato riscritto in formule. Regola che ne esce, da aggiungere allo standard
§2-bis: **quando una fase deduce "il problema è X" da una misura indiretta, la
deduzione va scritta come identità o scomposizione esatta**, non come
ragionamento in prosa. Una scomposizione che ricompone a sei decimali non si può
leggere al contrario.

### 📐 Il modello in dettaglio

**La scomposizione** (chain rule del log-loss multiclasse). Per ogni partita, se
l'esito è il pareggio `−log P(X)`; se è casa `−log P(H) = −log(1−P(X)) −
log(P(H)/(1−P(X)))`. Mediando su N partite:
```
LL = (1/N)·Σ −[y_X·log P(X) + (1−y_X)·log(1−P(X))]          <- massa-pareggio
   + (1/N)·Σ_{non pari} −log( P(esito) / (1−P(X)) )          <- discriminazione
```
Il secondo termine è già pesato da P(non-pari) perché somma sui soli non-pari e
divide per tutte le partite: i due addendi ricompongono il totale **esattamente**
(verificato: 0.576618 + 0.403273 = 0.979890).

**La correzione del prior.** In `_fit_counts` il vincolo di identificabilità era
`P·media(attacco)²` su TUTTE le squadre; ora è su `attack[seen]`, con `seen`
costruito dagli indici delle partite di training. La penalità resta 1e4 e
l'indeterminazione resta fissata (il modello è invariante per
`attacco_i += c, difesa_i −= c`: basta vincolare la media di un sottoinsieme
non vuoto). Prova del meccanismo, a parità di tutto il resto: con penalità 1e4
l'attacco atterrava a −0.3376, con 1e2 a −0.2892, con 1e0 a −0.2313 (= il
prior) — il leak scalava con la penalità, quindi era la penalità.
**Attenzione**: NON centrare su `(attacco − prior).mean()²`, che sposta l'intera
scala di `media(prior)` e peggiora.

Riproducibile: `python scripts/_run_fase92_gap_decomposition.py` (anche
`--league premier_league`). Test di regressione in `tests/test_dixon_coles.py`.

---

## Fase 92-bis — I fix dell'audit, verificati per mutazione (e l'IC della Fase 91 che si sgonfia)

> *Voce scritta a posteriori dall'audit della **Fase 101**: questa fase esisteva
> come commit (`1ad6c30`) e aveva cambiato codice di produzione, ma non aveva
> voce nel diario né riga nel registro — la stringa «92-bis» non compariva in
> nessun documento. È il caso limite che la checklist §2 vuole impedire: una
> conclusione ritirata **qui** non poteva propagarsi altrove, perché il «qui»
> non esisteva. I contenuti sono quelli del commit, ri-verificati nel codice.*

### 1 · Obiettivo

Chiudere i fix aperti dalla Fase 92, con un vincolo di metodo: ogni correzione
che riguarda un test va verificata **per mutazione** — si rompe di proposito il
codice che il test dovrebbe proteggere, e il test *deve* diventare rosso.
Altrimenti non è un test, è una decorazione.

### 2 · Ragionamento e ipotesi

Un audit produce due tipi di rilievo: quelli che si vedono (un numero sbagliato)
e quelli che **non si vedono perché nessuno guarda** — un ramo di codice che
nessun test esegue, una colonna che sparisce in silenzio, un IC calcolato con
l'assunzione sbagliata. I secondi sono i pericolosi, e si trovano solo
chiedendosi «se questo fosse rotto, chi se ne accorgerebbe?».

### 3 · Alternative considerate

Sulla metrica della Fase 91: tenere il bootstrap iid (più semplice, e dava un
risultato più forte) contro sostituirlo con un bootstrap **a grappoli**. Le
osservazioni non sono indipendenti: dentro ogni stagione ci sono esattamente 4
squadre in top-4 e 3 retrocesse — un vincolo di somma che l'iid ignora. Scelto
il secondo, sapendo che avrebbe *indebolito* la conclusione.

### 4 · Scelta

Sette correzioni al codice, due famiglie di test nuove, una metrica rifatta.

### 5 · Risultato

**Il tool era per-lega a metà.** `predict.py` applicava a Premier e Liga le
costanti tarate sulla chiusura Serie A (θ=1.225, φ0=0.30, κ=1.5, `sharpen_1x2`)
benché la mappa per-lega fosse già stata misurata alle Fasi 79/81. Costo
verificato in Premier: **+0.0025** di log-loss 1X2 contro il motore liscio
(0.9665 contro 0.9640; il mercato sta a 0.9639) e **+2.7pp** di pareggio
previsto sopra il realizzato. Nasce `MARKET_ENGINE` in `src/config.py` — unico
punto di verità, §7 — e il tool dichiara a video quale motore sta usando.

**Tre difetti che degradavano in silenzio.** `_SUB_SUFFIXES` di
`fetch_polymarket_open.py` non conteneva `"total"`: il sotto-evento «Total
Corners» formava un gruppo a sé e **gonfiava del ~67%** il conteggio delle
partite. `player_scores.add_squad_values` buttava via le colonne appena
calcolate quando lo snapshot in ingresso non le aveva già — caso reale dopo un
rebuild — e lo snapshot veniva riscritto *prima* dell'errore.
`build_squad_values.py` ora si **ferma** se un rebuild perderebbe celle
`squad_value` già presenti: sono le 13 recuperate a mano da Transfermarkt alla
Fase 70, dato reale non rigenerabile da script.

**Due test che non testavano.** Il ramo degli spareggi dentro la simulazione non
veniva **mai** eseguito (lo stub aveva `tie_rate=0`): cancellando
`_resolve_sim_tie` la suite restava verde. E il `value_bet_roi` finiva in ogni
riga del registro senza che il suo **valore** fosse mai asserito — l'unico
assert confrontava la funzione con sé stessa. Ora invertire il segno del profitto
o la direzione dell'edge rende la suite rossa.

**La metrica della Fase 91 si sgonfia.** Col bootstrap a grappoli il guadagno
del top-4 sulla persistenza passa da «conclusivo per IC» a **IC [−0.0006,
+0.0522], che include lo zero**. A reggere resta il **test dei segni**: 19
stagioni-lega su 24, p=0.0066. La sostanza tiene, l'etichetta era troppo forte.
*(Questa correzione non era mai arrivata nel diario né nel README: l'ha
propagata la Fase 101.)*

**Un numero falso nella Fase 57.** «Tutti i Δ entro ±0.0005» non era vero:
l'emivita 730 in Premier costa **+0.005686** con p_better 0.0001 (conclusivo, il
27% del gap di quella lega). Corretto; la scelta operativa (365g) non cambia.

166 test verdi, 8 nuovi.

### 6 · Lezione

Un test che non può fallire è peggio di un test assente: dà la stessa fiducia e
nessuna protezione. La **verifica per mutazione** costa un minuto e la
distingue. E una fase che tocca «solo il tooling» va scritta come le altre —
questa non lo è stata, e la sua correzione più importante (l'IC del top-4) è
rimasta invisibile per nove fasi.

### 📐 Il modello in dettaglio

**Nessuna matematica nuova sul modello.** Cambia *quali costanti* riceve
`price_markets`, che resta la funzione della Fase 44/52:

```
d = mi.price_markets(lam, mu, rho, phi0, kappa, dp_theta)
```

Prima della Fase 92-bis i quattro parametri erano **costanti di modulo** tarate
sulla Serie A. Ora vengono da una mappa per-lega (`src/config.py:125`):

```
MARKET_ENGINE[lega] = {dp_theta, dp_theta_dc, phi0, kappa, sharpen_1x2}
market_engine(lega)  ->  default LISCIO: {None, None, 0.0, 0.0, False}
```

Il ragionamento su ogni valore (§2-bis):
- **Serie A** — `dp_theta=1.225` e `dp_theta_dc=1.138` sono i θ della Fase 52
  (massima verosimiglianza sui punteggi dati i tassi, rispettivamente del
  mercato e del DC); `phi0=0.30`, `kappa=1.5` sono i valori rappresentativi
  della φ(|λ−μ|) (Fase 39/44); `sharpen_1x2=True` perché la Fase 51 misura che
  `dp_lvl` batte la chiusura devigata in log-loss con CI conclusivo.
- **Premier** — tutto neutro: la Fase 81 misura che l'ottimo su ogni asse è già
  il motore liscio (ρ\*=−0.06, θ\*≈1, φ\*=0) e la Fase 79 che la φ35 **peggiora**
  (il DC sovra-stima già i pareggi equilibrati inglesi).
- **La Liga** — tutto neutro **per scelta**, non per misura: θ≈1.2 (Fase 81) e
  φ35-sola sul GG (Fase 80) sono misurate positive ma stanno in PANCHINA, e la
  regola del progetto è che una voce in panchina resta off di default.
- **Bundesliga e Ligue 1** — voci aggiunte dalla Fase 101 con lo stesso stato
  neutro, che qui è **misurato** (Fase 100: router θ negativo su 0/25 mercati in
  entrambe).

**Bootstrap a grappoli** (la correzione della metrica). Con `S` stagioni-lega e
`n_s` osservazioni ciascuna, invece di ricampionare le `Σ n_s` righe si
ricampionano le **stagioni** con reinserimento:

```
per b in 1..B:   S* = campione con reinserimento di {1..S}
                 delta_b = LL_persistenza(righe di S*) - LL_modello(righe di S*)
IC95 = percentili 2.5 e 97.5 di {delta_b}
```

È l'unica forma corretta qui perché dentro una stagione le righe **non sono
indipendenti**: le squadre in top-4 sono esattamente 4 e le retrocesse
esattamente 3, quindi un errore su una squadra ne implica uno di segno opposto
su un'altra. L'iid ignora questo vincolo e **sottostima** la varianza: infatti
l'IC passa da [+0.0037, +0.0502] a [−0.0006, +0.0522] — a media invariata
(+0.02742), è **+14% di ampiezza complessiva** (0.04646 → 0.05276) e **+19% sul
lato basso** (semi-ampiezza sotto la media da 0.02359 a 0.02799), cioè un
effetto-disegno DEFF = (0.05276/0.04646)² = **1.29**. Poco, ma abbastanza da
farlo attraversare lo zero. *(La prima stesura diceva «quasi il doppio in
ampiezza sul lato basso»: sovrastimava — rettifica Fase 101.)*

---

## Fase 93 — Dove si perde la discriminazione: è informazione, non calibrazione (e si vede DOVE)

**Obiettivo.** La Fase 92 ha stabilito che l'**88%** del gap col mercato sta
nella discriminazione casa/ospite, non nella massa del pareggio. Questa fase
risponde alla domanda successiva, ora che è quella giusta: **su quali partite**
perdiamo quel termine, e il deficit è **aggiustabile** o è **informazione**?

**Il dato.** Per ogni partita non pareggiata si isola il termine di
discriminazione (`c_i = −log P(esito | non-pari)`) per modello e mercato, e si
guarda la differenza. **5.083 partite**, 3 leghe × 6 stagioni. Deficit medio
+0.02153; il mercato fa meglio nel **58.3%** delle partite.

**Risultato 1 — è INFORMAZIONE, non calibrazione. E non di poco.**

Scomposizione di Murphy del log-loss binario «casa vs ospite | non pareggio»:

| | mis-calibrazione | risoluzione |
|---|--:|--:|
| **modello** | **0.00083** | 0.05270 |
| mercato | 0.00125 | **0.06251** |

Il termine di mis-calibrazione è **piccolo per entrambi, e la differenza non è
conclusiva**: 0.00083 contro 0.00125, ma la differenza appaiata vale −0.00042
con IC95 bootstrap **[−0.00137, +0.00049]** (include lo zero, P 82%) e **cambia
segno** col numero di fasce (12 fasce 0.00083 vs 0.00125; 25 fasce 0.00127 vs
0.00147; 50 fasce 0.00230 vs 0.00190; 100 fasce 0.00388 vs 0.00339 — nelle
ultime due è il *mercato* a essere meglio calibrato). E c'è un pavimento:
simulando gli esiti da `y ~ Bernoulli(p_modello)`, cioè con calibrazione
**perfetta per costruzione**, il termine vale già 0.00047 in media e **0.00083 al
95° percentile** (2.000 repliche) — esattamente il nostro valore, che quindi sta
**al pavimento del rumore** (P = 5.2%). Quello del mercato lo supera di poco
(0.00125, P = 0.25% sul proprio nullo), ma sono entrambi termini minuscoli e la
loro differenza non è misurabile: ~~«siamo meglio calibrati del mercato»~~ **non
si può dire** *(rettifica Fase 101)*. Ciò che è conclusivo è l'altro termine:
perdiamo interamente in **risoluzione**, cioè nella capacità di separare i casi —
+0.00981 a favore del mercato, IC95 [+0.00732, +0.01239]. In quote:

> della parte di deficit che la scomposizione a fasce **attribuisce** — 0.00939
> sui **0.02153** totali, cioè il **44%** — **calibrazione −4%, informazione
> +104%**; il restante 56% è residuo di discretizzazione, non attribuito.
> Espresso sul deficit vero: la calibrazione ne vale **−1.9%**, la risoluzione
> **+45.6%**. La quota attribuita è stabile al binning (6/12/25/50/100 fasce:
> 44.6 / 43.6 / 42.6 / 41.9 / 42.1%), quindi non è un artefatto delle fasce
> scelte.

Conferma diretta: P(casa | non-pari) dichiarata dal modello **57.61%**, dal
mercato 58.02%, realizzata **57.68%**. Non c'è alcun bias sistematico
casa/ospite da correggere: in media siamo esatti.

**Conseguenza operativa netta**: su questo termine **non esiste una leva di
ricalibrazione**. Qualunque mappa post-hoc (temperatura, Platt, isotonica) può
solo togliere un termine che è **al pavimento di rumore** — 0.00083 su un deficit
di 0.02153, cioè il 4% di quello che la scomposizione attribuisce e l'1.9% del
deficit vero. È la ragione per cui il progetto
non ha mai trovato una leva che chiudesse il gap: non ce n'è una di quella
famiglia.

**Risultato 2 — non esiste una sola fetta in cui siamo più informati del
mercato.** Testate 3 leghe, 6 stagioni, terzili di squilibrio, 4 fasi della
stagione: **tutte negative**, senza eccezioni. Ma la dimensione del divario
cambia molto, e in modo istruttivo:

| fetta | risoluzione nostra | del mercato | divario |
|---|--:|--:|--:|
| **mismatch** (terzo più squilibrato) | 0.10692 | 0.10891 | **−0.00198** |
| equilibrate (terzo più incerto) | 0.00419 | 0.01211 | **−0.00793** |

**Sui mismatch siamo quasi alla pari col mercato** (divario 4 volte più piccolo).
Quando una squadra è nettamente più forte, lo storico basta. **Sulle partite
equilibrate il mercato ci stacca**: lì il risultato lo decide informazione
specifica della singola partita — formazioni, condizione, motivazione — che i
risultati passati non contengono per costruzione.

**Risultato 3 — la forbice si allarga durante la stagione.**

| fase | risoluzione nostra | del mercato | divario |
|---|--:|--:|--:|
| giornate 1-5 | 0.06387 | 0.07215 | −0.00829 |
| 6-12 | 0.05150 | 0.05615 | −0.00465 |
| 13-25 | 0.05662 | 0.06619 | −0.00957 |
| **26+** | 0.04895 | 0.05886 | **−0.00991** |

La risoluzione di **entrambi** cala nel finale (più partite senza posta in
palio, più rotazioni), ma la nostra cala di più: il mercato **accumula
informazione più in fretta di noi** man mano che la stagione va avanti. È
coerente con la Fase 89-bis (le forze evolvono e noi le teniamo ferme) e con la
Fase 32 (la posta in palio, che il mercato prezza e noi no).

**Risultato 4 — l'86.9% del deficit si materializza dove DISSENTIAMO.** Quando
modello e mercato concordano strettamente il deficit è +0.00134 (2.1% del
totale); quando dissentono fortemente è +0.05504 (**86.9%**). Non è tautologico
in modo banale — dice che, ogni volta che ci discostiamo dal mercato, in media
**abbiamo torto noi**. È la firma dell'adverse selection della Fase 20,
localizzata sul termine giusto.

**Lezione.** Il gap è **informazione**, ed è ora misurato come tale, non
congetturato. Ma la caccia ha un bersaglio molto più stretto di prima:
**le partite equilibrate, nella seconda metà di stagione**. Lì il divario di
risoluzione è massimo e lì l'informazione mancante è più concentrata. Sui
mismatch siamo già quasi alla pari e non c'è nulla da guadagnare.

**Onestà.** Questo non è un edge: dire *dove* manca informazione non la procura.
E la direzione è chiara ma il rimedio no — le formazioni ufficiali escono ~1 ora
prima del via e andrebbero raccolte prospetticamente (nessuno storico), come già
scritto in `docs/PISTE.md`. Resta il fatto misurato: **niente ricalibrazione
chiuderà questo gap**.

### 📐 Il modello in dettaglio

**Il deficit per partita.** Dalla chain rule della Fase 92, per una partita non
pareggiata il termine di discriminazione è `c_i = −log(P(esito_i)/(1−P_i(X)))`,
cioè il log-loss del binario «casa vs ospite» condizionato al non-pareggio;
`deficit_i = c_i(modello) − c_i(mercato)`. La media dei deficit su TUTTE le
partite (pareggi inclusi, che contribuiscono 0) è esattamente il termine di
discriminazione del gap della Fase 92 — i due conti si chiudono.

**La scomposizione di Murphy.** Per un binario, con fasce `k` di probabilità:
```
LL = incertezza − RISOLUZIONE + MIS-CALIBRAZIONE
  MIS-CALIBRAZIONE = Σ_k (n_k/n)·( p̄_k − ȳ_k )²      <- aggiustabile
  RISOLUZIONE      = Σ_k (n_k/n)·( ȳ_k − ȳ )²        <- informazione
```
`p̄_k` = probabilità media dichiarata nella fascia, `ȳ_k` = frequenza realizzata,
`ȳ` = frequenza generale. Le fasce sono per **quantile** (12 fasce equinumerose,
non equispaziate): con fasce equispaziate le code contengono pochissimi casi e i
due termini diventano instabili. Una mappa di ricalibrazione azzera il primo
termine e **non tocca il secondo**: è questo che rende la scomposizione la
risposta esatta alla domanda «è aggiustabile?».

**Attenzione a come si normalizzano le quote.** I due termini della
scomposizione **non ricompongono** il deficit: `Δcal + Δris = 0.00939` contro un
deficit di `0.02153`, perché la scomposizione a fasce butta via la variazione
*dentro* la fascia. Le percentuali «−4% / +104%» sono quindi frazioni della
parte **attribuita**, non del deficit — dirle sul deficit vale −1.9% e +45.6%.
Chiuderle sul totale sbagliato è l'errore che la Fase 101 ha corretto qui.

Riproducibile: `python scripts/_run_fase93_discrimination.py` (~35 min, 18
backtest walk-forward). Dataset per-partita in
`experiments/fase93_discrimination.csv` (5.083 righe, con le covariate per
affettarlo diversamente); IC, binning alternativi e pavimento di rumore si
ricalcolano da quel CSV con la `murphy()` dello stesso script (bootstrap
appaiato B=2.000 sulle 5.083 righe; pavimento: 2.000 repliche di
`y ~ Bernoulli(p)`), senza rifare i 18 backtest.

Diagnostico: nessun run in `experiments/runs.jsonl` — i 18 backtest walk-forward
sono serviti a produrre il dataset per-partita, che è l'artefatto riproducibile;
nessuna metrica di modello nuova da registrare.

---

## Fase 94 — La varianza mancante: la deriva di forza, e perché va adottata su UN solo mercato

**Obiettivo (richiesta utente, «punto 2»).** Ritarare δ sull'orizzonte
stagionale, perché la Fase 91 aveva trovato le neopromosse troppo condannate
alla retrocessione (54.7% dichiarato contro 48.6% realizzato).

**La diagnostica ha reindirizzato il lavoro — e questa è la parte che conta.**
Prima di toccare δ ho verificato l'ipotesi implicita: *le neopromosse sono
predette troppo deboli sulla singola partita?*

| neopromosse, 2.052 partite-squadra | modello | realtà |
|---|--:|--:|
| P(vittoria) | 23.80% | 22.42% |
| **P(sconfitta)** | **51.71%** | **51.71%** |
| punti attesi su 38 giornate | 36.4 | 35.4 |

**No.** La probabilità di sconfitta è esatta al centesimo e sui punti siamo
semmai un filo generosi. δ non è il colpevole: ritararlo avrebbe peggiorato le
previsioni di partita per aggiustare un sintomo che nasce altrove. *(È la
seconda volta in tre fasi che una verifica preliminare smentisce l'ipotesi di
partenza — vedi la regola del §2-bis nata alla Fase 92.)*

**Dove nasce davvero: la classifica simulata è compressa.** La dispersione dei
punti finali reale supera quella simulata in **21 stagioni su 24**; il valore
vero cade in media all'**83° percentile** della distribuzione simulata, dove
dovrebbe cadere al 50°. *(Nota di metodo: il primo confronto che avevo scritto
era un artefatto — metteva a fronte la dispersione delle ATTESE con quella di
una REALIZZAZIONE, che è più larga per costruzione anche con un modello
perfetto. Rifatto confrontando classifiche entrambe realizzate.)*

E il conto si chiude in quadratura: `15.45² ≈ 13.61² + 7.44²` — dispersione
simulata = differenze fra squadre + rumore dei risultati. Per arrivare ai
**17.51** reali serve **incertezza in più, non separazione in più**.

**Questo unifica i due difetti noti.** Favorito troppo sicuro in cima (60.1%
contro 41.7%) e neopromosse troppo condannate in fondo (54.7% contro 48.6%)
sono **lo stesso difetto ai due estremi della stessa classifica compressa**: le
forze sono tenute ferme per dieci mesi, quindi nessuno «si accende» e nessuno
crolla.

**La deriva NON è uniforme** (480 squadre-stagione, fit di inizio contro fit di
fine stagione):

| | n | deriva (sd) |
|---|--:|--:|
| squadre deboli (terzo basso) | 159 | **0.231** |
| medie | 158 | 0.155 |
| forti | 163 | 0.156 |
| **neopromosse** | 72 | **0.299** |
| tutte le altre | 408 | 0.157 |

Le neopromosse derivano **1.9 volte** più di tutti gli altri (correlazione fra
forza iniziale e |deriva| −0.205). Un σ **uniforme** perturba quindi troppo le
forti e troppo poco le deboli — ed è esattamente il danno misurato prima di
scoprirlo: con σ uniforme 0.18 il top-4 peggiorava in **18 stagioni su 24**
(p=0.023) mentre la retrocessione migliorava appena.

> ✅ **Verificato alla Fase 101-bis** (era rimasto fra i numeri non
> ri-derivabili: `markets()` non emetteva i conteggi per stagione). Con lo
> script che ora stampa il verdetto per mercato,
> `python scripts/_run_fase94_drift.py --sd 0.18 --nsim 20000` dà top-4
> **migliore in 6/24** stagioni — cioè peggiore in **18/24**, la cifra
> pubblicata — e il test dei segni bilaterale su 18/24 dà **p = 0.0227**, che
> arrotonda allo 0.023 dichiarato. Retrocessione +0.0071 [+0.0001, +0.0150]
> 12/24, l'unico mercato conclusivo: «migliorava appena» regge.

**Risultato con σ differenziato (0.30 neopromosse / 0.16 resto):**

| mercato | guadagno | IC95% a grappoli | meglio in |
|---|--:|---|--:|
| **retrocessione** | **+0.0095** | **[+0.0020, +0.0180]** | 15/24 |
| campione | +0.0017 | [−0.0356, +0.0431] | 9/24 |
| top-4 | +0.0007 | [−0.0075, +0.0113] | 7/24 (p=0.064) |

| calibrazione | senza | con |
|---|--:|--:|
| neopromosse: scarto dichiarato−realizzato | +6.1pp | **+2.8pp** |
| ECE retrocessione | 0.0479 | **0.0387** |
| ECE top-4 | **0.0140** | 0.0203 |
| favorito: scarto | +18.4pp | +14.6pp |

**Decisione: adozione PER-MERCATO (§1.8).**
- **Retrocessione → ADOTTATA.** È l'unico mercato con IC che esclude lo zero, e
  la calibrazione delle neopromosse passa da +6.1pp a +2.8pp.
- **Campione → nessun effetto** (9/24: dentro il rumore). Il favorito resta
  sovra-confidente di 14.6pp: la deriva ne toglie 4, non 18.
- **Top-4 → NON adottata.** Peggiora in 17 stagioni su 24 e l'ECE sale da
  0.0140 a 0.0203. Il motivo è chiaro e vale come lezione: **il top-4 era già
  calibrato**, e aggiungere incertezza a una previsione già giusta può solo
  peggiorarla.

**Onestà su cosa NON è stato risolto.** Anche col σ misurato la compressione si
chiude solo in parte (83° percentile → ~76°). Per chiuderla tutta servirebbe
σ≈0.28, cioè **più della deriva fisicamente misurata**, e a quel livello il
danno supera il beneficio (campione 1.2229, top-4 0.2253: entrambi peggio del
non fare nulla). Quindi: **la deriva spiega una parte della compressione, non
tutta.** Il resto è probabilmente la correlazione fra partite — le squadre
attraversano periodi, e il simulatore le tratta come indipendenti. È la pista
successiva, e questa volta è indicata da un residuo misurato, non da un'ipotesi.

### 📐 Il modello in dettaglio

**L'iniezione.** In `simulate_season`, per ogni «draw» si estrae per ogni squadra
`ε_t ~ N(0, σ_t)` e si sposta la **forza netta**:
```
attacco_t  ->  attacco_t + ε_t/2
difesa_t   ->  difesa_t  − ε_t/2
```
Metà per colonna, così la forza netta `attacco − difesa` cambia di `ε_t` mentre
il **livello dei gol della lega non si sposta** (una perturbazione tutta
sull'attacco farebbe segnare di più tutti). La perturbazione è **costante dentro
una stagione simulata** (la deriva è una proprietà della stagione, non della
partita) e ri-estratta a ogni draw; le `n_sims` simulazioni si dividono fra
`n_drift_draws` estrazioni, quindi il costo scala col numero di draw (ognuno
ricalcola le 380 matrici) e non col numero di simulazioni.

**σ da dove viene.** Da `forza(fine stagione) − forza(inizio stagione)` sulle
stesse 480 squadre-stagione, con lo stesso identico modello e solo `as_of_date`
diverso. Si usa la **deviazione standard**, non la media: la media (+0.072 per
le neopromosse) misura «fine stagione contro luglio», non «media della stagione
contro luglio», e iniettarla equivarrebbe ad ammorbidire δ — che la diagnostica
ha appena escluso. `DRIFT_SD = {promoted: 0.30, other: 0.16}` in `src/config.py`,
arrotondati dai misurati 0.299 / 0.157.

**Perché σ non è stato calibrato sui mercati.** È tarato sulla **dispersione
della classifica** (24 osservazioni che non sono gli esiti dei mercati) e
verificato indipendentemente sulla misura diretta della deriva. Che i due
criteri indichino lo stesso ordine di grandezza — e che l'ottimo dei mercati
cada a 0.15-0.18, cioè sulla deriva misurata — è il motivo per cui la si può
chiamare meccanismo e non fattore di aggiustamento. Il σ che ottimizza la sola
dispersione (0.28) è invece **fuori** da quel range e danneggia due mercati su
tre: la calibrazione sulla dispersione, da sola, è il criterio sbagliato.

Riproducibile: `python scripts/_run_fase94_drift.py` per la **calibrazione**
(~50 min, 7 valori di σ *uniforme* × 24 stagioni-lega; griglia completa in
`experiments/fase94_drift.json`, run in `experiments/runs.jsonl` con σ=0.28).

> 🔒 **Guardia aggiunta alla Fase 101-bis.** Solo `--sd-map` (la config
> adottata) scrive `experiments/fase94_drift.json`; ogni altra config scrive
> `experiments/fase94_drift_variante_<σ>.json`. Prima qualunque esecuzione
> sovrascriveva l'artefatto ufficiale, e **due sessioni di seguito** hanno
> dovuto ripristinarlo da git dopo aver semplicemente *controllato* un numero.
> Chi verifica una cifra non deve poter distruggere la fonte di quella cifra.

⚠️ Il risultato **adottato** — il σ per-squadra 0.30/0.16 con gli IC e i conteggi
X/24 — richiede `--sd-map`, e fino alla Fase 101 **non era ri-derivabile da
niente di committato**: lo script accettava solo uno scalare, `bootstrap_ci` era
importato e mai usato, e l'output si fermava agli aggregati. Rieseguito con la
mappa (`--sd-map`) i numeri di questa fase si riottengono: retrocessione +0.0095
[+0.0018, +0.0179] 15/24 (identico), campione +0.0017 9/24 e top-4 +0.0007 7/24
(gli estremi degli IC ballano sulla quarta cifra rispetto alla prima stesura,
verdetto invariato: entrambi nel rumore), neopromosse +6.1pp → +2.8pp,
dispersione 83.1° → 76.2° percentile, ECE retrocessione 0.0479 → 0.0387, ECE
top-4 0.0140 → 0.0203. L'ECE è su **10 fasce equispaziate** (la funzione della
Fase 91): il binning va dichiarato perché non è quello per quantile usato altrove
nel progetto, e due ECE con binning diversi non sono confrontabili.
Nota operativa: `--sd-map` **riscrive** `experiments/fase94_drift.json` con la
sola chiave `map`; per non perdere la griglia uniforme va ripristinato da git
dopo l'uso.

---

## Fase 95 — Il primo confronto con un mercato VERO sull'outright: Polymarket quota il campione 2026-27

**Obiettivo.** La Fase 89 ha costruito il simulatore di stagione (mercato
CAMPIONE) e ha dichiarato il suo limite più duro: **«non esistono quote outright
storiche → "battiamo il mercato" NON è testabile all'indietro»**. Questa fase
rimuove quel limite, ma in avanti: **Polymarket quota LIVE il campione 2026-27**
di tutte le nostre leghe, e la stagione non è ancora iniziata. Per la prima volta
possiamo confrontare la nostra stima outright con un prezzo di mercato reale.

**Cosa c'è davvero su Polymarket (verificato oggi, 2026-07-25).** Dump completo
via `scripts/fetch_polymarket_open.py --tag Soccer`: **4.854 eventi calcio,
56.865 mercati**, 781 partite ricostruite (708 con 1X2 completo). Ma il grosso
delle *singole partite* è **illiquido** (prezzi degeneri 0.33/0.33/0.33 e
O2.5=0.50 = nessuno scambio) e riguarda leghe minori. Il valore vero è altrove:
gli **outright di stagione**, che esistono per tutte e 5 le leghe del progetto —
`Serie A: 2027 Champion`, `EPL: 2027 Champion`, `LALIGA: 2027 Champion`,
`Bundesliga: 2027 Champion`, `Ligue 1: 2027 Champion` — più i **posizionali**
(`Team to qualify for UEFA Champions/Europa/Conference League`), che sono
esattamente i mercati della **Fase 91**.

Qualità della fonte: escludendo i placeholder senza scambi (`Team A/B/C`,
`Other`, volume 0, prezzo fisso 0.50) gli overround sono **ragionevoli** —
Serie A **+7.2%**, EPL **+5.8%**, LaLiga **+3.2%** — con liquidità reale
(EPL: volume 1,37 M$; LaLiga 318 k$; Serie A 29 k$).

**Il confronto (`scripts/_run_polymarket_outright.py`).** DC per-lega fittato sui
dati fino a fine 2025-26, `simulate_season` (20.000 stagioni) sulle **squadre che
Polymarket quota** (= rosa 2026-27 reale, promosse incluse col prior δ), contro i
prezzi devigati in proporzione:

| lega | MAE | corr | KL(noi‖mercato) | favorito |
|---|--:|--:|--:|---|
| Serie A | 0.0252 | 0.956 | 0.181 | Inter (entrambi) |
| Premier | 0.0265 | 0.948 | 0.242 | Arsenal (entrambi) |
| La Liga | 0.0110 | 0.982 | 0.056 | Barcelona (entrambi) |

**Risultato — accordo forte sull'ordinamento, ma sovra-confidenza confermata
dall'esterno.** La correlazione è 0.95-0.98 e il favorito coincide in tutte e
tre le leghe: la struttura della nostra stima è giusta. Ma il pattern degli
scarti è sistematico e nella direzione già nota: **concentriamo troppa massa sul
favorito** — Inter 66.4% contro 47.1%, Arsenal 45.1% vs 33.6%, Man City 42.1% vs
27.9%, Barcelona 59.3% vs 51.8% — e ne togliamo agli inseguitori (Man United
0.8% vs 10.9%, Chelsea 1.0% vs 9.0%, Milan 2.7% vs 11.7%). È la **stessa
sovra-confidenza misurata dalla Fase 89 sul backtest** («dichiara 60.1% sul
favorito, ne azzecca 41.7%»), ora **confermata contro un mercato vero e su dati
mai visti**: due strade indipendenti, stesso difetto. La Liga è la più allineata
(KL 0.056), la Premier la più distante (KL 0.242).

**Perché sbagliamo così.** Due cause, entrambe già dichiarate: (a) il simulatore
tratta i parametri di forza come **noti** — manca l'incertezza dei parametri e la
loro evoluzione in-season (Fase 89), e questo *comprime* la distribuzione della
classifica finale verso il favorito; (b) i nostri dati si fermano a **fine
2025-26**: non vediamo il mercato estivo 2026, mentre il prezzo sì — il caso
Man United (mercato 10.9%, noi 0.8%) è il sospetto naturale.

**Cosa NON è questa fase.** Non è un test di edge: la stagione non è giocata,
quindi si misura **accordo**, non chi ha ragione. Il verdetto vero arriva a
maggio 2027. E lo scarto sul favorito **non è un'occasione di scommessa**: è più
probabile che l'errore sia nostro (la sovra-confidenza è documentata) che del
mercato.

**Cosa ne consegue (operativo).** Il test prospettico (Fase 78) ha ora un
**secondo binario, già eseguibile oggi**: congelare le nostre P(campione) e
P(top-4) per il 2026-27 *prima* del via e scorarle a fine stagione, contro un
mercato che le quota. È il primo mercato in cui il progetto può misurarsi
prospetticamente senza aspettare le quote di chiusura partita per partita. La
priorità immediata diventa **correggere la sovra-confidenza** del simulatore
(incertezza dei parametri via bootstrap/posterior sulle forze) e ri-misurare la
KL contro Polymarket: è un bersaglio quantitativo, non un'opinione.

> **Convergenza con la Fase 94** (sviluppata in parallelo da un'altra sessione):
> la 94 sta iniettando la **deriva di forza** nel simulatore — cioè proprio il
> meccanismo che qui risulta mancante (le forze trattate come note comprimono la
> classifica verso il favorito). Le due fasi si incastrano: la 94 fornisce la
> **correzione**, questa fase fornisce il **metro esterno** per misurarne
> l'effetto. Test naturale una volta che la 94 è chiusa: **ri-eseguire
> `_run_polymarket_outright.py` e verificare che la KL scenda** (attesa: Serie A
> da 0.181, Premier da 0.242 verso il basso). Se la deriva è la causa giusta, la
> distanza dal mercato deve ridursi senza ritarare nulla sui prezzi.

### 📐 Il modello in dettaglio

- **Prezzi di mercato**: `p_market_i = p_raw_i / Σ_j p_raw_j` (devig
  proporzionale) sui soli esiti con `volume > 0` — i placeholder a 0.50 senza
  scambi sono scartati, non devigati (falserebbero l'overround: con loro la somma
  sarebbe ~3.07 invece di 1.07).
- **Nostra stima**: `champion_prob` da `simulate_season(model, round_robin(teams),
  teams, league_key, n_sims=20000)` (Fase 89: Monte Carlo di stagioni intere con
  classifica e spareggi ufficiali per lega), poi rinormalizzata sulle squadre
  quotate. Il DC è quello di config (`LEAGUE_CONFIGS`), fittato con `as_of` =
  ultima data nota + 1 giorno; le promosse 2026-27 (Frosinone, Monza, Venezia in
  Serie A) ricevono il prior δ della lega.
- **Metriche di accordo**: `MAE = mean|p_noi − p_mkt|`; `corr` di Pearson;
  `KL(noi‖mercato) = Σ p_noi·log(p_noi/p_mkt)` — quest'ultima è la più adatta
  perché penalizza proprio l'eccesso di massa dove il mercato non la mette
  (la nostra sovra-confidenza sul favorito).
- Riproducibile: `python scripts/fetch_polymarket_open.py --tag Soccer` poi
  `python scripts/_run_polymarket_outright.py --all`. Diagnostico su dati LIVE:
  nessun run in `runs.jsonl` (il dump non è versionato, cambia ogni giorno).

---

## Fase 95-bis — La deriva di forza messa alla prova dal MERCATO: il backtest non aveva potenza

**Obiettivo.** La Fase 94 ha misurato la deriva di forza in-stagione e l'ha
adottata **solo sulla retrocessione**, dichiarando che «sul campione non ha
effetto». Quella conclusione però viene da un backtest con **24 osservazioni**
(una per lega-stagione): il campione più povero del progetto. La Fase 95 ha
aperto un secondo metro — i prezzi Polymarket sul campione 2026-27 — che usa
l'**intera distribuzione su 20 squadre** invece di un solo vincitore. Domanda:
la deriva avvicina o allontana la nostra stima dal mercato?

**Risultato — la deriva ha eccome un effetto sul campione, e il segno dipende da
quanto eravamo già allineati.**

| lega | KL base | KL +deriva | Δ | esito |
|---|--:|--:|--:|---|
| Serie A | 0.1805 | **0.1445** | **−0.0360** | avvicina |
| Premier | 0.2418 | **0.2036** | **−0.0382** | avvicina |
| La Liga | 0.0560 | 0.0740 | +0.0179 | allontana |

Anche MAE e correlazione migliorano dove la KL scende (SA 0.0252→0.0218, corr
0.956→0.963; PL 0.0265→0.0224, corr 0.948→0.955).

**La regola che emerge è la stessa della Fase 94, su un metro indipendente.** La
94 aveva trovato che la deriva **peggiora il top-4** «perché quel mercato era già
calibrato, e aggiungere incertezza a una previsione giusta può solo peggiorarla».
Qui accade letteralmente lo stesso: la Liga era già la lega più allineata al
mercato (KL 0.056, un terzo delle altre) e la deriva la **peggiora**; Serie A e
Premier erano sovra-confidenti e la deriva le **corregge**. Due esperimenti
diversi, stessa legge: *l'incertezza aggiunta paga solo dove manca davvero.*

**La lezione di metodo (la parte che vale più del risultato).** La Fase 94 non ha
sbagliato: ha misurato con lo strumento che aveva, e su 24 osservazioni l'effetto
sul campione era invisibile. Il confronto col mercato ha **molta più potenza** per
i mercati di stagione, perché confronta 20 probabilità per lega invece di un
singolo esito realizzato. Conseguenza operativa: **per i mercati outright, il
prezzo di mercato è un metro più potente del backtest storico** — e ora ce
l'abbiamo. Non sostituisce la verifica sugli esiti (che resta l'unica prova di
chi ha ragione), ma la anticipa di una stagione.

**Onestà.** «Più vicino al mercato» non è «più corretto»: se il mercato sbaglia,
avvicinarsi peggiora. Ma dato che il mercato di chiusura ingloba il modello su
ogni mercato-partita testato (α\*=0, Fasi 16/88), l'ipotesi di lavoro ragionevole
è che sia il riferimento migliore disponibile finché la stagione non è giocata.

### 📐 Il modello in dettaglio

Nessuna matematica nuova: `simulate_season(..., drift_sd=drift_sd_map(teams,
promosse))` con σ 0.30 (neopromosse) / 0.16 (resto) dalla Fase 94, contro la
stessa simulazione a σ=0. Metro: `KL(noi‖mercato) = Σ p_noi·log(p_noi/p_mkt)` sui
20 esiti quotati, con `p_mkt` devigato in proporzione. Riproducibile:
`python scripts/_run_polymarket_outright.py --all --with-drift`. Diagnostico su
dati LIVE: nessun run in `runs.jsonl`.

---

## Fase 96 — Fuori dalla matrice dei gol: corner e cartellini (e l'arbitro, il primo dato ortogonale)

**Obiettivo.** Tutto ciò che il progetto ha dimostrato — α\*=0, tetto
informativo, coda al tetto — vale per i mercati **derivabili dalla matrice**
P(gol_casa, gol_ospite). I mercati con un **processo generatore proprio** (corner
= pressione territoriale; cartellini = arbitro, tensione, falli) non erano mai
stati modellati: il tetto non dice nulla su di loro. Qui si apre la famiglia.

**I dati c'erano da sempre**: `HC/AC` (corner), `HY/AY/HR/AR` (cartellini),
`HS/AS/HST/AST`, `HF/AF`, `Referee` — **copertura 100% su 10.260 partite**
(3 leghe × 9 stagioni), mai estratti dal loader. L'arbitro è nei bundle
**Premier** (100%); assente dai grezzi Serie A e Liga.

**1. Sono davvero un processo diverso?** Sì, su due assi:

| lega | corner μ | σ²/μ | cartellini μ | σ²/μ | corr(corner, gol) | corr(cart, gol) |
|---|--:|--:|--:|--:|--:|--:|
| Serie A | 9.79 | 1.25 | 4.78 | 1.34 | −0.062 | −0.004 |
| Premier | 10.35 | 1.12 | 3.72 | 1.24 | −0.040 | −0.032 |
| La Liga | 9.43 | 1.13 | 5.31 | 1.48 | −0.007 | −0.030 |

(a) sono **SOVRA-dispersi** (σ²/μ = 1.12–1.48), l'opposto dei gol dati i tassi del
mercato (sotto-dispersi, θ≈1.2 — Fase 51): sono processi di natura diversa, e la
forma giusta per i gol è quella sbagliata per loro; (b) la correlazione coi gol è
**praticamente nulla** (|r| ≤ 0.06): non sono ridondanti col motore-gol, sono
informazione nuova per costruzione.

**2-3. Il modello e la sua calibrazione** (walk-forward, 7.050 partite OOS; forze
attacco/difesa sul conteggio con emivita 365g e shrinkage, più i fattori
casa/ospite):

| mercato | MAE vs baseline | R² | calibrazione (scarto medio) |
|---|--:|--:|--:|
| **Corner** | 2.688 vs 2.703 (**+0.5%**) | +0.0065 | +0.011…+0.021 |
| **Cartellini** | 1.700 vs 1.715 (**+0.9%**) | +0.0255 | **+0.005 / −0.003 / +0.001** |

Entrambi **battono la baseline** e il log-loss migliora su quasi tutte le linee
(corner O8.5–O11.5, cartellini O2.5–O4.5). I **cartellini sono il mercato
migliore**: calibrazione quasi perfetta (scarti al millesimo) e R² quattro volte
quello dei corner. I corner restano più difficili: il segnale per-squadra è
debole e resta un lieve ottimismo (+0.01–0.02).

**Un bug trovato dal bias, e la lezione.** La prima versione mostrava un bias
sistematico **+0.61 corner/partita** (+0.07 su *tutte* le linee Over). Prima
ipotesi: deriva temporale — i corner in effetti **calano** (10.17 nelle prime tre
stagioni → 9.72 nelle ultime tre). Ma accorciare la memoria del livello portava
il bias solo da +0.612 a +0.549: troppo poco. La causa vera era **mia**:
applicavo il fattore vantaggio-casa alla squadra di casa senza il fattore
complementare all'ospite, quindi il totale atteso era gonfiato per costruzione.
Imposto `hadv + aadv = 2`, il bias è crollato a +0.02. *Un bias costante su tutte
le linee è la firma di un errore di normalizzazione, non di un fatto sui dati* —
e la deriva temporale, pur reale, era un depistaggio.

**4. L'arbitro: il primo dato davvero ortogonale.** Sui cartellini di Premier
(27 arbitri con ≥30 partite): le medie per arbitro vanno da **2.44 a 4.57**
cartellini/partita, con sd fra arbitri **0.513** contro una banda nulla da
permutazione **[0.158, 0.296]** → **effetto reale**, ampiezza netta ~**0.46
cartellini di sd**, il **12.4% della media**. È il primo pezzo di informazione del
progetto che **nessun modello-gol può contenere**: non passa dai gol, dai tiri o
dalla forza delle squadre.

**Cosa si può e cosa non si può concludere (la distinzione che conta).** Su
questi mercati **la calibrazione si misura**: bastano gli esiti, che abbiamo al
100%. Quello che manca è il **benchmark di efficienza**: nessuna fonte in nostro
possesso quota corner o cartellini, quindi non possiamo dire «siamo meglio del
mercato» — solo «le nostre probabilità sono corrette e battono la baseline».
*(Correzione di una formulazione imprecisa usata in chat: senza quote manca
l'efficienza, NON la calibrazione.)*

**Cosa ne consegue.** La famiglia fuori-matrice è **aperta e produttiva**: due
mercati nuovi prezzati e calibrati, con un dato ortogonale (l'arbitro) che merita
di entrare nel modello-cartellini. È l'unica direzione in cui «spremere i dati che
già abbiamo» non produce l'ennesima conferma del tetto.

### 📐 Il modello in dettaglio

Per il conteggio `C` di una partita, con `base` = media pesata di lega,
`hadv/aadv` = fattori casa/ospite (vincolo `hadv+aadv=2`), `att_t`/`dif_t` =
rapporti prodotti/concessi della squadra rispetto alla media:

```
E[C_casa]   = base · hadv · att_casa · dif_ospite
E[C_ospite] = base · aadv · att_ospite · dif_casa
E[C_tot]    = E[C_casa] + E[C_ospite]
```

con pesi temporali `w = 0.5^(Δgiorni/365)` e shrinkage verso 1 con massa
equivalente `1.5·10` partite (le stesse costanti del DC ufficiale, non ri-tarate:
sarebbe il passo successivo). I mercati Over/Under sono derivati con una Poisson
di media `E[C_tot]` — approssimazione dichiarata, dato che i conteggi sono
sovra-dispersi (σ²/μ ≈ 1.2): una binomiale negativa è il candidato naturale del
prossimo giro, e qui **avrebbe senso** all'opposto dei gol (Fase 27). Effetto
arbitro: `sd` fra medie per arbitro (≥30 partite) contro 2.000 permutazioni
dell'etichetta-arbitro; ampiezza netta `√(sd_oss² − sd_nulla²)`. Riproducibile:
`python scripts/_run_outside_matrix.py`.

Diagnostico: nessun run in `experiments/runs.jsonl` — i mercati corner/cartellini
sono fuori dal listino che `compute_metrics` scora (il registro tiene le metriche
del motore sui gol) e la config ufficiale non cambia; l'artefatto riproducibile è
l'output dello script.

---
## Fase 97 — Una SECONDA borsa (Smarkets), l'archivio storico degli outright, e il primo controllo esterno della deriva

**Obiettivo.** Tre cose legate. (1) La Fase 95 ha fatto il primo confronto con
un mercato outright vero, ma su **una sola fonte** (Polymarket) e **un solo
mercato** (campione): serviva sapere se esistono altre fonti raggiungibili.
(2) Qualunque cosa si trovi, va **congelata**: i prezzi outright di oggi sono
lo storico che non abbiamo (Fase 89: «non esistono quote outright storiche →
"battiamo il mercato" NON è testabile all'indietro»). Quel limite non si toglie
all'indietro, ma **smette di crescere** se si archivia ogni volta che si guarda.
(3) La deriva di forza adottata alla Fase 94 era stata calibrata su una
statistica **interna** (la dispersione della classifica): non aveva mai visto un
prezzo di mercato.

**Ragionamento / ipotesi.** Il manuale di sopravvivenza dava `betexplorer.com`
e `oddsportal.com` per «presumibilmente bloccati» e non li aveva mai testati
dall'ambiente cloud. Un'etichetta per esclusione non è un fatto: l'ipotesi era
che **provando davvero l'intera lista** qualcosa saltasse fuori — e che la fonte
utile non fosse un bookmaker (margine alto, HTML ostile) ma un'altra **borsa**,
perché una borsa dà prezzi confrontabili con Polymarket per costruzione.

**Alternative considerate (tutte testate col `curl`, non presunte).**

| fonte | esito | perché non si usa |
|---|---|---|
| **Smarkets** | API v3 **pubblica, senza chiave** | **ADOTTATA** |
| OddsPortal | 200, e **nessun** redirect ADM da qui | il feed `/feed/outrights/*.dat` è un **blob base64 cifrato**: chiave da estrarre dal bundle JS a ogni loro rilascio |
| BetExplorer | 200 sulla home, **404** su `/outrights/` | non ha una sezione outright |
| The Odds API | 200 ma **401 senza chiave** | serve registrazione |
| DraftKings / bwin / Betfair | 403 / 000 | geo-blocco o proxy |

Le due etichette «presumibilmente bloccato» erano **entrambe sbagliate**: i siti
rispondono, sono inutilizzabili per motivi diversi da quelli scritti. È la
lezione operativa della fase, ed è finita nel manuale (§1).

**Scelta.** Smarkets, e **accanto** a Polymarket, non al suo posto. Il censimento
del 25/07/2026 dice che nessuna delle due domina:

| | Polymarket | Smarkets |
|---|---|---|
| campione (5 leghe) | sì | sì |
| **retrocessione** | **mai, in nessuna lega** | **Premier** |
| piazzamenti Top 2/3/4/5/6, top-half | no | Premier, Liga, Ligue 1 |
| liquidità **Premier** | overround **+5.8%** | spread **0.11pp** |
| liquidità **Serie A** | overround **+7.1%** | spread **~5-11pp** (illiquido) |

Sulla Premier è nettamente migliore Smarkets, sulla Serie A nettamente
Polymarket: **complementari**. Da qui l'archivio a **due fonti**
(`data/outright_snapshots/`, VERSIONATO, con colonna `source`), scritto da
`scripts/archive_outrights.py` che chiama `fetch_polymarket_open.py` e il nuovo
`fetch_smarkets_outrights.py`.

**Controllo incrociato fra le due borse (il primo che potevamo fare).** Sul
mercato campione, appaiando le squadre presenti in entrambe (62 coppie):
scarto assoluto **mediano 0.13pp**, medio 0.62pp, massimo 5.98pp (PSG: 82.5%
Polymarket contro 76.6% Smarkets, dove Smarkets ha overround più basso). Due
mercati indipendenti che concordano a un decimo di punto sono una **verifica
delle due pipeline**, non solo dei prezzi.

**Risultato principale — un secondo controllo ESTERNO della deriva (Fase 94), sull'altro capo della classifica.** La **Fase 95-bis** ha appena messo la deriva alla prova coi prezzi Polymarket sul mercato CAMPIONE (KL: Serie A −0.0360, Premier −0.0382, Liga +0.0179). Qui la stessa correzione viene giudicata su un mercato diverso (**retrocessione**), da una fonte diversa (**Smarkets**) e con una metrica diversa (MAE sulle probabilità): tre assi indipendenti.
Smarkets quota la retrocessione Premier: si può finalmente confrontare
(`scripts/_run_fase97_relegation_market.py`, 20.000 stagioni, 17 esiti con mid
a due lati su 20).

| | MAE vs mercato | corr | neopromosse: noi vs mercato |
|---|--:|--:|---|
| **senza** deriva | 8.84pp | 0.937 | 87.9% vs 61.4% (**+26.5pp**) |
| **con** deriva (Fase 94) | **7.32pp** | 0.935 | 81.0% vs 61.4% (**+19.6pp**) |

Filtrando i due libri troppo larghi perché il mid significhi qualcosa (Forest
bid 0.1% / ask 10.0%, Man United 6.6pp di spread) il verdetto **non cambia**:
9.68pp → **8.11pp**. **La deriva è confermata da una strada indipendente**: era
stata tarata su una statistica interna (dispersione della classifica) e migliora
anche contro un prezzo di mercato che non aveva mai visto.

**Ma la correzione è giusta e INSUFFICIENTE.** Restano +19.6pp di eccesso sulle
neopromosse, e lo scarto ha una forma precisa: sovra-prezziamo le promosse
(Ipswich **+36.5pp**, Coventry **+26.2pp**) e sotto-prezziamo il resto del
gruppo di coda (Sunderland −11.9, Leeds −7.9, Crystal Palace −7.4, Brentford
−6.6, Bournemouth −6.2). Le somme coincidono (2.92 noi contro 2.85 mercato ≈ 3
retrocesse): non è un problema di scala, è **redistribuzione**. Siamo troppo
sicuri di *quali* tre scendono.

**E abbiamo una CODA A ZERO.** Man City e Liverpool ricevono da noi
esattamente **0.0%**; il mercato dà 7.6% e 1.1% (Man City con libro stretto,
bid 6.9% / ask 8.3%). Un modello che dichiara zero su un evento non impossibile
prende log-loss infinito se accade: la simulazione non ha **incertezza sui
parametri**, solo sui risultati, e le forti finiscono in un pozzo di
probabilità nulla. È la stessa mancanza di varianza della Fase 94, ma sull'altra
coda — e lì la deriva non arriva.

**Lezione / cosa ne consegue.**
1. **«Presumibilmente bloccato» non è un dato.** Due host marcati per
   esclusione da mesi rispondono; la fonte migliore del progetto dopo
   Polymarket è emersa dal provare la lista intera.
2. **La deriva della Fase 94 regge a una verifica esterna** — ma copre metà del
   problema. Il residuo non è più «varianza mancante»: è **sicurezza mal
   riposta su quali** squadre scendono.
3. **La coda a zero è un difetto strutturale**, non un dettaglio: serve
   incertezza sui *parametri* (non solo sui risultati). Pista aperta in
   `docs/PISTE.md`.
4. **L'archivio va alimentato**: ogni istantanea è un pezzo dello storico che
   nel 2028 permetterà di dire «battiamo il mercato» sull'outright. Cadenza in
   `docs/PISTE.md` §4-bis.

### 📐 Il modello in dettaglio

**1) Dal libro ordini alla probabilità (Smarkets).** L'API dà interi in
centesimi di punto percentuale. Per il contratto *i* (`book_price`):

```
bid_i = max(prezzi dei bid)          ask_i = min(prezzi delle offerte)
price_i = (bid_i + ask_i) / 20000    solo se ESISTONO entrambi i lati
spread_i = (ask_i - bid_i) / 10000
```

Il `/20000` è `/2` (il mid) diviso `/10000` (la scala). Con un lato solo
`price_i = None` e resta `best_ask_i`, marcato `price_side="ask_only"`: è un
**tetto** al valore equo, non un prezzo. Non è pedanteria — scartando quelle
righe sparivano 6 mercati interi (tutti i Top-N della Premier hanno solo
offerte).

**2) Devig, e quando NON si fa.** Solo per i mercati a vincitore unico
(`EXCLUSIVE = {champion, top_scorer}`):

```
S = Σ_i price_i          (overround)          prob_i = price_i / S
```

Per retrocessione e Top-N gli esiti sono **binari indipendenti** e `prob_i =
price_i`. Verifica di sanità riuscita: la retrocessione Premier somma
**S = 2.848 ≈ 3** (tre retrocesse) e il Top-4 Liga ≈ 4. Normalizzando a 1 si
otterrebbe una probabilità di retrocessione **divisa per ~3**. La condizione
`full = (n_priced ≥ 0.9·n_entries) and S > 0` impedisce di rinormalizzare su un
libro mezzo vuoto, dove `S` non è l'overround ma una somma parziale.

**3) La deriva iniettata (richiamo della Fase 94, formula verificata in
`season_sim.build_cdfs`).** Per ogni estrazione *d* (200 estrazioni da 100
stagioni ciascuna) e per ogni squadra *t*:

```
ε_t^(d) ~ N(0, σ_t)      indipendente fra squadre, COSTANTE dentro la stagione
attack_t  ← attack_t  + ε_t^(d)/2
defense_t ← defense_t − ε_t^(d)/2
```

La metà su ciascuna colonna serve perché la deriva agisca sulla **forza netta**
(attacco − difesa) **senza spostare il livello dei gol della lega**: la somma
`attack + defense` resta invariata, la differenza si sposta di `ε`. Il σ è
eterosche­dastico (`config.drift_sd_map`):

```
σ_t = 0.30  se t è neopromossa       σ_t = 0.16  altrimenti
```

I due numeri **non sono scelti a griglia**: sono la deriva misurata alla Fase
89-bis stagione su stagione (sd della forza netta 0.299 sulle neopromosse
contro 0.157 sulle altre, rapporto 1.9×), al netto dell'errore di stima. Un σ
uniforme perturberebbe troppo le forti e troppo poco le deboli — che è
esattamente l'errore che si voleva correggere.

**4) La probabilità di retrocessione.** Con `rank` la matrice
(n_sims × n_squadre) delle posizioni finali e `nt = 20`:

```
P(retrocessione_t) = (1/n_sims) · #{ s : rank[s, t] ≥ nt − 2 }
```

`≥ nt−2` = posizioni 18, 19, 20 con `rank` a base 1. Nessuna approssimazione
analitica: la classifica di ogni stagione simulata è costruita con gli spareggi
**ufficiali** della lega (Premier: differenza reti — Fase 89).

**5) Perché il filtro sullo spread è a 5pp.** Non è una soglia ottimizzata: è
il punto sotto il quale, in questo listino, il mid smette di essere ambiguo. Il
Nottingham Forest quota bid 0.1% / ask 10.0% → «mid 5.05%» che è la media di due
numeri scollegati, non un prezzo; il Man United ha 6.57pp di spread. Sopra
quella soglia cadono **2 righe su 17**, ed è dichiarato nell'output insieme al
conto su tutte e 17 — il taglio si vede, non si nasconde (§1.4).

**6) Riproducibilità.** `python scripts/archive_outrights.py` (istantanea del
giorno, due fonti) poi `python scripts/_run_fase97_relegation_market.py`.
L'archivio è versionato, quindi il confronto è **rifacibile identico** anche
quando i prezzi live saranno cambiati — al contrario della Fase 95, che leggeva
un dump non versionato. Nessun run in `runs.jsonl`: è un confronto con dati di
mercato, non un backtest con esiti.


---

## Fase 98 — Sette fronti in parallelo: cosa regge, cosa cade, e la deriva di livello che nessuno cercava

**Obiettivo (utente).** «Porta avanti ognuno dei discorsi, entra nel dettaglio di
tutto, non lasciare nulla da parte.» Sette fronti aperti, eseguiti in parallelo
come esperimenti veri (uno script ciascuno, walk-forward, CI dove serve), poi
**ri-verificati a mano** prima di scriverli qui — e la ri-verifica ha cambiato la
conclusione di uno di essi.

### 1 · Binomiale negativa sui conteggi (`_run_counts_nb.py`) — MISTO

I conteggi sono sovra-dispersi (Fase 96), quindi la NB è la forma giusta —
l'opposto dei gol, dove la Fase 27 l'aveva bocciata. Su 7.050 partite OOS:

| mercato | LL Poisson | LL NB | Δ | IC95 |
|---|--:|--:|--:|---|
| corner | 0.6490 | **0.6480** | +0.00103 | [+0.00062, +0.00143] |
| cartellini | 0.6069 | **0.6060** | +0.00088 | [+0.00033, +0.00142] |

**Conclusivo ma trascurabile** (+0.16% / +0.14% relativo). La calibrazione
migliora sulle linee sotto la media (corner O8.5 da +0.021 a +0.005). **Due
scoperte oltre il titolo**: (a) i **gialli di Serie A sono SOTTO-dispersi**
(var/μ condizionata 0.901) e lì la NB collassa da sola sulla Poisson (Δ esattamente
0.00000) — la stima è auto-protettiva; (b) in 3 celle su 21 la NB **peggiora con
IC conclusivo**, e la causa è identificata: dove la media walk-forward è storta
per **deriva temporale** (Premier cartellini −0.201, Serie A corner +0.352),
allargare la distribuzione sposta massa dal lato sbagliato. Verificata ed
**esclusa** l'ipotesi bug: il bias non è costante né di segno unico.

### 2 · L'arbitro come feature (`_run_referee_feature.py`) — NEGATIVO, con una regola nuova

Copertura verificata, non assunta: `Referee` esiste **solo in Premier**
(3420/3420); La Liga e Serie A **0/3420**. Su 2.324 partite OOS, **nessun IC
esclude lo zero** su nessuna linea (miglior caso: O3.5 gialli Δ −0.00364
[−0.00853, +0.00133]).

**Il risultato vero è il controllo anti-artefatto.** Il modello-base sotto-stima
di −0.20 cartellini (in Premier i cartellini crescono) e il fattore-arbitro medio
vale 1.0247 > 1. Scomponendo con una costante di **solo livello** stimata
train-only: il livello da solo vale **−0.00308 dei −0.00364**. L'arbitro al netto
del livello vale **−0.00041** [−0.00511, +0.00414]. **L'85% del guadagno apparente
non era informazione sull'arbitro.**

Il segnale però **esiste ed è misurato OOS per la prima volta**: regressione
`real/base = a + b·(f_arb−1)` dà **b = 0.401** [+0.096, +0.706] — conclusivamente
>0 *e* conclusivamente <1: il fattore grezzo è **sovra-esteso ~2.5×** (il tasso di
un arbitro deriva nel tempo). Componenti di varianza: arbitro **3.7%**, casa 2.5%,
ospite 2.2%, accoppiamento 4.9% — l'arbitro conta più di ogni singola squadra ma
meno dell'accoppiamento, e **~95% resta rumore irriducibile**.

> **Regola di metodo (nuova, da applicare sempre).** Ogni feature *moltiplicativa*
> va confrontata col suo **controllo di solo livello**: altrimenti si misura la
> deriva del modello base e la si attribuisce alla feature.

### 3 · Potenza del test prospettico (`_run_prospective_power.py`) — il vincolo di disegno

Calcolo fatto sui dati veri (6.840 partite, differenze appaiate per-partita).
Controllo di validità superato: gap 1X2 pooled +0.0179 (riproduce il +0.0165).

**Le partite sono indipendenti**: acf1 +0.007, ICC ≈ 0, **DEFF = 1.00** — nessuna
penalità da clustering. Ma il rapporto segnale/rumore è **1:8,5** (sd 0.1527
contro gap 0.0179):

| campione | potenza sul gap | verdetto |
|---|--:|---|
| 30 partite (1 giornata × 3 leghe) | **9,8%** | MDE 0.0781 = 4,7× il gap: **non conclude mai** |
| 380 (1 stagione, 1 lega) | 62,5% | sotto-dimensionato |
| **574** | **80%** | ≈19 giornate su 3 leghe |
| 1140 (1 stagione × 3 leghe) | 97,7% | disegno giusto |

Gerarchia netta fra mercati: contro la **baseline** bastano 184 partite (6
giornate); contro il **mercato** servono 574 sull'1X2, 2.254 sul GG/NG, 2.988
sull'O/U 2.5. **L'1X2 dà potenza 4-5× prima degli altri.**

**La correzione che ho verificato a mano — e che cambia la conclusione del
fronte.** Il fronte riportava che il vantaggio del simulatore di stagione (Fase
89) «non regge a una baseline meglio tarata»: LL baseline 1.3816 invece di
1.4293, Δ −0.1806, IC [−0.3750, +0.0114] che include lo zero. Ho riprodotto i
numeri — sono giusti — ma la **spiegazione era sbagliata**. Eseguendo entrambe le
griglie sullo **stesso identico dataframe**:

| griglia della baseline di persistenza | LL LOO | (β, w₂) scelti |
|---|--:|---|
| Fase 89: β∈[0,4], **w₂∈{0, 0.5, 1, 1.5, 2}** | 1.4293 | (2.5, **1.5**) |
| fronte 3: β∈[0.5,4], **w₂∈{0, 0.5, 1}** | **1.3816** | (2.5, **1.0**) |

La griglia della Fase 89 è un **superset** di quella del fronte 3 sull'asse w₂,
eppure produce una baseline **peggiore**. Non è «meglio tarata»: è
**instabilità della selezione leave-one-out con n=24** — aggiungere opzioni alla
griglia fa scegliere, sulle 23 stagioni di train, un parametro che generalizza
peggio sulla 24ª. La lettura corretta **non** è «la Fase 89 è smentita», ma:
**il risultato della Fase 89 è fragile alla specificazione della baseline**, e il
segno della conclusione dipende da una scelta arbitraria della griglia. Coerente
col resto del fronte: per concludere sull'outright servirebbero **57
stagioni-lega** (con 3 leghe in una stagione la potenza è **9,8%**). L'outright va
dichiarato **non testabile prospetticamente** — non «perdente».

*(Nota di metodo: è la seconda volta in questo giro che una verifica manuale
ribalta la lettura di un risultato prodotto da un agente — nella Fase 86 accadde
il contrario. Il numero era giusto in entrambi i casi; la **spiegazione** no.)*

### 4 · Tier 3 contro Polymarket (`_run_polymarket_tier3.py`) — bersaglio fallito, fondazione posata

Il template della Fase 88 **non è replicabile ora**, per due motivi documentati:
su 4.854 eventi Soccer e 2.840 eventi Tier 3, **zero sulle nostre 3 leghe**
(pausa estiva) e gli eventi aperti **non hanno esito**. Trappola scoperta:
**65 su 78 eventi con volume >1.000$ sono partite già giocate** con prezzi
degeneri (0.9995/0.005) — **il volume non è un filtro di liquidità.**

I due risultati ottenibili sono stati prodotti:
- **fondazione misurata**: frazione di gol nel primo tempo **f = 0.4396**
  [0.4338, 0.4458] (SA 0.4365 / PL 0.4464 / LL 0.4356), primo tempo
  Poisson-compatibile (dispersione 0.9857), tempi quasi indipendenti (+0.0485)
  → **il ri-scalamento dei tassi è lecito**;
- **validazione storica conclusiva** su 6.840 partite: Halftime 1.0251 vs 1.0787
  di baseline (**+0.0537** [+0.0461, +0.0612]), Second Half **+0.0578**,
  risultato esatto **+0.1940**;
- **residuo localizzato e non-artefatto**: il **secondo tempo è mal calibrato**
  (pareggio 0.3671 dichiarato vs 0.3427 reale) mentre il primo passa per **lo
  stesso codice** ed è calibrato a <0.006 → è **game-state**, non normalizzazione;
- accordo prezzo-contro-prezzo dove esiste (n=115/96): corr 0.997/0.983, distanza
  mediana ~0.014, **f implicita nel book 0.4580**.

### 5 · Proxy delle formazioni (`_run_lineup_proxy.py`) — NEGATIVO pieno

Copertura ampia (9.159/10.260 partite testate): il nullo è un vero nullo. La
parte che «funziona» **non è nuova** — la forza degli undici attesi correla
**+0.9603** col valore rosa (già bocciato F4c/F11) e +0.898 col logit del DC;
fuori campione vs DC +0.00136 [−0.00086, +0.00350], 2/4 stagioni. La parte
concettualmente nuova (disponibilità del nucleo, continuità dell'undici) è
**nulla ovunque**. E **sul bersaglio della Fase 93** (equilibrate, seconda metà)
tutti gli IC attraversano lo zero, con correlazioni col deficit |r| ≤ 0.034.
Dettaglio di sanità: la disponibilità correla **−0.1227** col logit della
chiusura → **il mercato le assenze le prezza già**.

**Conseguenza importante**: resta aperta **solo** la versione che conterebbe — la
**formazione ufficiale a T−1h** — e questo esperimento dimostra che *il surrogato
storico non la sostituisce*. Non è un argomento contro la raccolta prospettica: è
un argomento a favore, perché esclude la scorciatoia.

### 6 · Movimento apertura→chiusura (`_run_line_movement.py`) — MISTO

**Non sappiamo anticiparlo**: β vincolato −0.0039 [−0.0162, +0.0085], R² 0.0001.
**CLV negativo conclusivo**: −0.0022 [−0.0033, −0.0012], 45.7% positivi su 2.373
selezioni (Serie A −0.0027/44.7% contro il −0.0028/45% della Fase 14: **combacia**).
Il movimento **vale poco**: +0.0029 [+0.0016, +0.0042] = **15,6% del nostro gap**
— anticipandolo *tutto* (impossibile) resteremmo a +0.0151 contro +0.0179.

**Il pezzo interessante è il link con la Fase 93**: corr(nostro deficit, deficit
dell'apertura) = **+0.4270**, pendenza +1.0336 [+0.9291, +1.1318], contro un
placebo per permutazione di +0.0884. E il guadagno del movimento è concentrato
sulle **equilibrate** (Q1 +0.0039 vs Q4 +0.0007) e nella **seconda metà**
(+0.0038 vs +0.0020): **lo stesso profilo del deficit F93**. L'informazione che
arriva nelle ultime ore è in parte proprio quella che ci manca.
**Autocorrezione onesta del fronte**: il «deficit 4× più grande sulle partite più
mosse» **non sopravvive al placebo** (vera +0.0311 contro artefatto +0.0524).

### 7 · Il listino come prodotto (`_run_listino_validazione.py`) — POSITIVO

38 mercati prezzati walk-forward col motore vero, costanti ri-fittate a ogni fold.
**I livelli di validazione sono QUATTRO, non tre** — la scoperta che rende onesto
il prodotto:

| livello | significato | n |
|---|---|--:|
| **A** | quota esterna **indipendente** → si può parlare di efficienza | **1** |
| **A°** | quota esiste ma **è l'INPUT del motore** → confronto **circolare** | 8 |
| **B** | nessuna quota, ma **esito osservabile** → si misura la calibrazione | 27 |
| **C** | non validabile | 7 famiglie |

**L'unica riga che regge un'affermazione di efficienza è l'handicap asiatico**:
Brier **0.2044 vs 0.2044**, Δ −0.0000 [−0.0003, +0.0002]. **32/36 mercati battono
la baseline ex-ante con IC conclusivo, 0 perdono**; i 4 non conclusivi sono tre
linee corner e il **totale dispari** (−0.0003, controllo negativo atteso).
Il fit walk-forward ha **ri-scoperto da solo** due fatti noti: θ=1.225 in 6/6 fold
Serie A ma 1.000-1.150 in Premier; φ0 collassa a 0.000 negli ultimi 3 fold Premier.
**Due correzioni obbligatorie**: le tre doppie chance vanno marcate come
**IDENTITÀ** delle 1X2 (non validazioni indipendenti: è la stessa trappola del
mercato «12» della Fase 92), e le righe outright vanno riscritte alla luce del
fronte 3.

### Cosa è cambiato davvero

**La scoperta trasversale: la DERIVA DI LIVELLO.** Tre fronti che non si
parlavano hanno misurato lo stesso difetto:
- fronte 1: bias di media Premier cartellini **−0.201**, Serie A corner **+0.352**
  — ed è ciò che *causa* i 3 peggioramenti conclusivi della NB;
- fronte 2: la costante di solo-livello vale **−0.00308 dei −0.00364** attribuiti
  all'arbitro, e sale da 1.0062 a 1.0559 in 7 fold;
- fronte 7: bias corner +0.117 su tutte e quattro le soglie — le uniche 3 linee
  non conclusive del listino.

**L'emivita 365g non insegue la deriva temporale dei conteggi.** È una correzione
a costo quasi nullo (una costante train-only) che vale, sui cartellini Premier,
**5× più dell'arbitro** e, sui conteggi, **un ordine di grandezza più del
passaggio Poisson→NB**. È la leva col miglior rapporto valore/costo emersa qui —
e nessuno la stava cercando.

**Tre mercati Tier 3 nuovi** (Halftime, Second Half, risultato esatto) sono
validati contro baseline con IC conclusivo su tutte e tre le leghe, su una
fondazione misurata. E **la mis-calibrazione del secondo tempo** è il primo
residuo *localizzato e non-artefatto* trovato da parecchie fasi: la strada è un
modello a due stadi (1T indipendente → 2T condizionato al punteggio).

### Onestà

Un fronte ha **fallito sul bersaglio** (Tier 3 contro Polymarket: 0 eventi sulle
nostre leghe in pausa estiva, nessun esito sugli eventi aperti); due sono
**negativi** sulla domanda posta (arbitro, formazioni). α\*=0 esce **confermato da
tre fronti indipendenti** (CLV −0.0022 conclusivo; proxy formazioni −0.00034;
accordo Polymarket entro 0.01 con f implicita 0.458). Le correzioni di sola forma
restano trascurabili anche quando il segno è giusto.

### 📐 Il modello in dettaglio

- **NB sui conteggi**: `Y ~ NB(m, r)` con media `m` dal modello di conteggio
  (Fase 96, vincolo `hadv+aadv=2`) e `r` stimato walk-forward per lega×mercato
  (MLE a medie fissate, MoM come inizializzazione); `r→∞` riduce alla Poisson.
  Dispersione condizionata OOS `Σ(y−m)²/Σm`: corner 1.152, cartellini 1.068,
  **gialli Serie A 0.901**.
- **Fattore-arbitro**: `f_arb = (media cartellini dell'arbitro)/(media di lega)`
  con shrinkage empirico-Bayes proporzionale alle partite arbitrate; arbitri mai
  visti → 1 (3,1% dei casi). Controllo di livello: `c_fold` = media dei fattori
  pesata per le partite dell'ultima stagione di train, **stimata train-only**.
  Verifica OOS: `real/base = a + b·(f_arb−1)`.
- **Potenza**: `n* = (z_{1−α/2}+z_{power})²·sd²/Δ²` con `sd` empirica delle
  differenze appaiate per-partita e `DEFF` da bootstrap a cluster (giornata,
  stagione) — risultato DEFF=1.00, quindi nessuna correzione.
- **Baseline outright**: `_persistence_loo(df, betas, w2s)` in
  `_run_fase89_season_champion.py` — per ogni stagione tara (β,w₂) sulle altre 23
  e valuta sull'esclusa. La differenza 1.4293 vs 1.3816 dipende **solo** dalla
  griglia `w2s` (superset ⇒ risultato peggiore = instabilità LOO a n=24),
  verificato eseguendo entrambe sullo stesso dataframe.
- **Frazione primo tempo**: `f = Σ gol 1T / Σ gol totali`, IC bootstrap; il
  ri-scalamento usa `λ_1T = f·λ`, `μ_1T = f·μ` nella stessa `score_matrix`.

Script: `_run_counts_nb.py`, `_run_referee_feature.py`,
`_run_prospective_power.py`, `_run_polymarket_tier3.py`, `_run_lineup_proxy.py`,
`_run_line_movement.py`, `_run_listino_validazione.py`. Output dati:
`experiments/listino_validazione.json`. Diagnostici: nessun run in `runs.jsonl`.

---

## Fase 99 — La correzione di LIVELLO dei conteggi: il lead della Fase 98 è FALSO (e perché)

**Obiettivo.** La Fase 98 aveva chiuso indicando la **deriva di livello** dei
conteggi come *«la leva col miglior rapporto valore/costo, e nessuno la stava
cercando»*: tre fronti indipendenti avevano misurato lo stesso difetto (bias di
media fuori campione: Premier cartellini **−0.201**, Serie A corner **+0.352**,
listino corner **+0.117** su tutte e quattro le soglie). Un bias costante su
tutte le linee è la firma di un **centro sbagliato**, non di un fatto sui dati.
Qui la si implementa e si misura. Risultato: **il lead non regge**, e il motivo
è più istruttivo del lead stesso.

**Ragionamento / ipotesi.** L'emivita 365g è tarata sui **gol**; i conteggi
derivano nel tempo (i cartellini crescono, i corner calano), quindi il livello
del modello della Fase 96 dovrebbe restare indietro. Se è così, una costante
moltiplicativa `c` stimata **solo sul passato** deve (a) azzerare il bias e
(b) migliorare il log-loss sui mercati Over/Under.

**Alternative considerate — cinque, tutte walk-forward.**

| stimatore | come |
|---|---|
| `c=1` | controllo: il modello della Fase 96 così com'è |
| `c_oos` | Σreali/Σattesi su **tutte** le stagioni di test già passate |
| `c_last2` | idem sulle **ultime due** (compromesso memoria/rumore) |
| `c_last` | idem sulla **sola** stagione precedente (insegue di più, più rumoroso) |
| `c_trend` | OLS della media stagionale sull'indice di stagione, **solo train**, estrapolata di un passo — l'unico disponibile già dal primo fold |

più la versione **alla radice** invece che a valle: l'**emivita scelta fold per
fold** minimizzando il log-loss sulle stagioni di test già passate (griglia
60–720g), che è la forma onesta dello sweep diagnostico (leggere la curva del
bias e prenderne il minimo sarebbe selezione sui dati di test).

**Risultato — negativo su tutta la linea.** 7.050 partite OOS, 21 fold, CI
bootstrap appaiato per-partita (5.000 ricampionamenti), `Δ > 0` = migliora.

| mercato | stimatore | bias dopo | log-loss | Δ | IC95 | esito |
|---|---|--:|--:|--:|---|---|
| corner | `c=1` | +0.1234 | 0.64900 | — | — | controllo |
| corner | `c_oos` | −0.0567 | 0.64961 | −0.00062 | [−0.00198, +0.00077] | no |
| corner | `c_last2` | +0.0162 | 0.64990 | −0.00091 | [−0.00239, +0.00056] | no |
| corner | `c_last` | +0.0239 | 0.65075 | −0.00176 | [−0.00360, +0.00006] | no |
| corner | `c_trend` | −0.0284 | 0.65216 | −0.00316 | [−0.00475, −0.00155] | **peggiora, conclusivo** |
| cartellini | `c=1` | +0.0424 | 0.60692 | — | — | controllo |
| cartellini | `c_oos` | +0.0724 | 0.60865 | −0.00173 | [−0.00318, −0.00027] | **peggiora, conclusivo** |
| cartellini | `c_last2` | +0.0849 | 0.60917 | −0.00225 | [−0.00443, −0.00005] | **peggiora, conclusivo** |
| cartellini | `c_last` | +0.0527 | 0.61180 | −0.00488 | [−0.00759, −0.00206] | **peggiora, conclusivo** |
| cartellini | `c_trend` | +0.1692 | 0.61155 | −0.00464 | [−0.00644, −0.00293] | **peggiora, conclusivo** |

**Nessuno** dei cinque migliora; **cinque celle su otto peggiorano con IC
conclusivo**. E la versione alla radice non salva nulla: l'emivita scelta fold
per fold sul solo passato dà **−0.00004** [−0.00191, +0.00183] sui corner e
**−0.00034** [−0.00179, +0.00109] sui cartellini — un lancio di moneta
(P>0 = 0.484 e 0.325).

**La spiegazione, in un numero: il bias di fold NON persiste.** È la diagnosi
che decide tutto, perché *qualunque* correzione stimata sul passato funziona se e
solo se il bias è persistente:

| mercato | corr(bias_t, bias_{t−1}) | IC95 | stesso segno | sd del bias | bias pooled |
|---|--:|---|:-:|--:|--:|
| corner | +0.2299 | [−0.2544, +0.6715] | **10/18** | 0.3558 | +0.1387 |
| cartellini | +0.1915 | [−0.3446, +0.5830] | **10/18** | 0.3841 | +0.0383 |

Dieci volte su diciotto il segno si ripete: **una monetina**. E la deviazione
standard del bias per fold è **2,6×** il bias pooled sui corner e **10×** sui
cartellini. Cioè: il «bias costante su tutte le linee» visto da tre fronti della
Fase 98 era costante **fra le linee di uno stesso pool**, non **nel tempo** — è
la media di una serie che cambia segno di stagione in stagione. Sui corner della
Liga i bias per fold sono +0.41, +0.73, −0.42, −0.27, −0.07, −0.20, −0.17: la
media pooled (−0.03) non descrive nessuna stagione.

**La seconda lezione: un bias sulla MEDIA non è un bias sulle PROBABILITÀ.** I
cartellini lo mostrano in modo netto. Il modello sovrastima il conteggio di
**+0.042** cartellini/partita, eppure la calibrazione dei mercati era già
ottima: scarto **+0.0047 / −0.0034 / +0.0008** sulle tre linee. Applicare `c_oos`
(1.0092 medio) ha **rotto** una calibrazione che era a posto: **+0.0097 / +0.0026
/ +0.0064**. Il passaggio media → P(Over) è non lineare e mediato sulla
dispersione delle medie per-partita: correggere il centro *aggregato* non
corregge — e può guastare — le probabilità *marginali*.

**L'unica cella dove la correzione ha senso è quella dove il bias era enorme.**
Serie A corner: bias **+0.352 → +0.031**, Δ **+0.00271** [−0.00051, +0.00590],
P>0 = 0.95 — **non conclusivo**, e le altre due leghe peggiorano con IC
conclusivo (Liga −0.00342, Premier −0.00105). Quindi nemmeno una versione
per-lega si salva: sarebbe selezione a posteriori su 7 fold.

**La domanda della Fase 98 («la forma NB serve dopo che il centro è a posto?»)
resta senza il suo controfattuale**, perché il centro non si mette a posto. Per
quel che vale, il guadagno della NB è **invariante** alla correzione: +0.00103 →
+0.00106 sui corner, +0.00088 → +0.00067 sui cartellini. Le due leve non si
sovrappongono, semplicemente nessuna delle due sposta molto.

**Lezione / cosa ne consegue.**

1. **Il lead della Fase 98 è chiuso, negativo.** Va scritto dov'era stato
   annunciato (README, PISTE §7-bis, PANCHINA, `lavoro_aperto.md` §8): l'avevo
   indicato come «il miglior rapporto valore/costo aperto», e non lo è.
2. **Regola di metodo, nuova.** Un bias misurato su un **pool** non autorizza una
   correzione **prospettica**: prima si misura se **persiste** (autocorrelazione
   fra fold, con CI). È l'analogo, sui conteggi, di ciò che la Fase 86-bis aveva
   trovato sul θ per-squadra (la volatilità *persiste* ma non è *sfruttabile*) e
   di quello che la Fase 98 stessa aveva imposto per le feature moltiplicative
   (il controllo di solo livello). Tre casi diversi, la stessa forma: **misurato
   ≠ prevedibile**.
3. **Il tetto regge anche qui.** Fuori dalla matrice dei gol il modello di
   conteggio della Fase 96 è già al suo limite: né la forma (NB, Fase 98) né il
   centro (questa fase) spostano più del terzo decimale.

### 📐 Il modello in dettaglio

- **Media del conteggio (invariata, Fase 96)** — per la coppia (h, a):
  `m = base·hadv·att[h]·dfn[a] + base·aadv·att[a]·dfn[h]`, con `base` media
  pesata per emivita 365g, `att`/`dfn` in forma chiusa con shrinkage `k = 1.5·10`
  verso `base`, e il vincolo `hadv + aadv = 2` (il fix della Fase 96: senza il
  fattore-ospite complementare compare un bias costante su tutte le linee — la
  stessa firma che questa fase ha poi dimostrato essere, nel resto, rumore).
- **Correzione di livello**: `m' = c·m`, con
  `c_oos = Σ_{fold passati} y / Σ_{fold passati} m` (e le varianti `c_last2`,
  `c_last` sugli ultimi 2 e 1 fold). Al primo fold, che non ha passato OOS,
  `c = 1` per costruzione: nessun look-ahead.
- **`c_trend`**: `ȳ_s = a + b·s` stimata OLS sulle medie stagionali delle sole
  stagioni di **train**; `c_trend = (a + b·S) / mean(m_train)` dove `S` è
  l'indice della stagione di test. È l'unico che modella la deriva invece di
  mediarla; è anche il **peggiore** (Δ −0.00316 e −0.00464, entrambi conclusivi),
  perché estrapola una retta da una serie che non ha pendenza stabile.
- **Emivita walk-forward**: per ogni fold `t`,
  `hl*(t) = argmin_{hl ∈ {60…720}} mean(logloss sulle stagioni di test < t)`;
  al primo fold `hl* = 365`. Le scelte oscillano (60g in 8 fold, 720g in 3):
  ulteriore sintomo dell'assenza di un vero segnale temporale.
- **Persistenza del bias**: `bias(l, s) = mean(m) − mean(y)` per lega × stagione;
  `corr(bias_t, bias_{t−1})` sulle 18 coppie consecutive (3 leghe × 6 transizioni),
  CI bootstrap sulle coppie. `P(Over ln) = 1 − F_Poisson(⌊ln⌋; m)` e
  `1 − F_NB(⌊ln⌋; r, r/(r+m))`, con `r` stimato MLE sul solo passato (Fase 98).

Script: `scripts/_run_counts_level.py` (riusa `_run_counts_nb.py` per modello,
stima di `r` e metriche: la media è **la stessa** della Fase 96, cambia solo la
costante). Diagnostico: nessun run in `runs.jsonl`.

*Questo diario viene aggiornato ad ogni fase. Per i dettagli tecnici e i comandi
vedi il [README](../README.md); per i risultati grezzi e replicabili
`experiments/runs.jsonl`.*

---

## Fase 100 — Cinque leghe: l'audit riga-per-riga, il dato che si credeva perduto, e la premessa che cade

### 1 · Obiettivo

Tre richieste dell'utente, in ordine: **verificare che i dati raccolti siano
tutti giusti**; **riprovare a procurare i dati oggi coperti da stime**, e se non
si riesce verificare che le stime (e il ragionamento che le ha prodotte) siano
corrette; **aggiungere Bundesliga e Ligue 1** con lo stesso schema. Con un
vincolo di metodo esplicito: *«verifica i risultati con un'analisi che cerchi di
provare il contrario del risultato»*.

Il lavoro è stato svolto in una cartella isolata (`cantiere/`, poi integrata) e
ha prodotto undici report; questa voce ne è la sintesi, con i numeri.

### 2 · Ragionamento e ipotesi

**Sull'audit.** Il progetto aveva sempre verificato i dati *contro sé stessi*
(coerenza interna, range, duplicati). Mai contro la **fonte-madre**, perché la
rete la dava per irraggiungibile. Prima ipotesi da testare: che sia ancora vero.

**Sulle stime.** Due cacce precedenti alla chiusura O/U 2017-19 erano state
chiuse negative. L'ipotesi implicita era che il dato non esistesse. L'ipotesi
alternativa, mai formulata: che esistesse ma fuori dall'asse lungo cui si era
cercato.

**Sulle leghe nuove.** Ipotesi del playbook (§7): le formule trasferiscono, gli
iperparametri no. Da ri-tarare e ri-motivare numero per numero.

### 3 · Alternative considerate

Per l'audit: fidarsi dello snapshot congelato (economico, ma non risponde alla
domanda) contro ri-scaricare tutto e confrontare riga per riga (costoso, ma è
l'unico controllo forte). Scelto il secondo.

Per le quote mancanti: rassegnarsi alla stima; ritentare le stesse fonti;
oppure cambiare **asse di ricerca**. Scelto il terzo.

Per le leghe nuove: copiare la config della Serie A (veloce, ma il §7 lo vieta)
contro ri-tarare tutto. Scelto il secondo — e la ri-taratura è risultata piatta,
il che è a sua volta un risultato.

### 4 · Scelta

Audit a quattro livelli (interno → confronto con la fonte ri-scaricata →
confronto con una fonte indipendente → avversariale «e se la fonte fosse
sbagliata?»), poi caccia al dato vero su assi nuovi, poi il playbook completo
sulle due leghe, e infine una **verifica avversariale sistematica** di ogni
risultato — inclusi i miei.

### 5 · Risultato

**L'audit.** La rete è tornata raggiungibile, quindi il controllo forte si è
potuto fare per la prima volta: **0 differenze** su gol, date, tiri, 10 colonne
quota e 8 colonne xG, ri-scaricando tutte e 45 le stagioni; i gol confermati da
una seconda fonte indipendente su 16.109 partite su 16.110 appaiate. Trovate **7 anomalie
reali**: 6 nella fonte e 1 nostra (l'ordine delle colonne fra snapshot, poi
uniformato); un ottavo caso segnalato si e' rivelato un falso positivo (l'xG a
0.00 di Bielefeld-Leverkusen: era un autogol) ed e' stato ritirato.

**Il dato che si credeva perduto.** La chiusura O/U 2017-19 esiste:
`footiqo.com` pubblica il book **1xBet**, che football-data non contiene —
3.652 partite su 3.652, copertura 100%. Validata come chiusura vera (corr 0.9977
con la chiusura Pinnacle contro 0.9909 con l'apertura; riproduce il movimento
1X2 partita per partita; margine e distribuzione dell'ultima cifra da book
vero, non da media né da modello). **Ma non è stata inserita**: è un solo book, e
come proxy della media multi-book è *peggiore della stima* (MAE 0.0156 contro
0.012). Trovare il dato vero non basta: bisogna chiedersi se è il dato giusto.

**Il collaterale che vale più del bersaglio.** La stessa fonte porta le quote
**GG/NG** al 100%. Il progetto dichiarava quel mercato «l'unico con spazio non
ancora chiuso». Misurato: il mercato GG/NG è informativo (log-loss 0.6840 contro
0.6921, CI conclusivo) ma vale **un terzo** dell'O/U dello stesso book; il nostro
prezzo lo **pareggia** (6 varianti, tutte con CI a cavallo dello zero); il DC
**perde di netto** (+0.0104) e il book lo **ingloba** (α\*=0 nel 70% dei fit).

**Le due leghe nuove.** 2.754 + 3.097 partite, 38 colonne identiche. Il DC batte
la baseline e non il mercato (gap **+0.0181** e **+0.0190**, dentro la forchetta
delle altre tre); il market-implied batte il DC su **15/15** mercati; le curve di
ri-taratura sono **piatte**, 5 leghe su 5. E **nessuna leva del mercato si
replica**: router θ 0/25 mercati conclusivi, φ(|λ−μ|) e power-devig bocciati,
beat-the-close chiuso (in Bundesliga *peggiora* con CI conclusivo, ROI −22%).

**La verifica avversariale ha smontato cinque affermazioni**, tre delle quali
mie. In cinque casi su sette il difetto non era il numero — la riproducibilità è
risultata impeccabile, delta identici a 10⁻¹⁶ — ma **la statistica scelta per
raccontarlo**.

### 6 · Lezione

Tre, in ordine di durata.

**Sul metodo di ricerca dati:** una pista chiusa due volte può essere chiusa
lungo l'asse sbagliato. «Non esiste» e «non esiste dove ho cercato» sono
affermazioni diverse, e solo la seconda era dimostrata.

**Sui dati:** il buco peggiore non è il `NaN`. È il valore che *sembra* una
misura — un segnaposto della fonte, uno zero che significa «non lo so» — perché
coincide con la fonte e nessun confronto lo vede. Trovato un xG segnaposto su
16.110 partite e 1.603 falsi zero di `midweek_europe`.

**Sul metodo statistico:** ogni statistica di testa deve avere il suo
intervallo, e ogni «non c'è effetto» la sua misura di potenza. È diventata la
regola R7 del protocollo.

E una conferma: **il tetto è informativo**, e ora è misurato su cinque
campionati invece che su uno.

### 📐 Il modello in dettaglio

**Nessuna formula nuova.** Le due leghe nuove usano le stesse del resto del
progetto; quello che cambia sono i numeri, e ognuno va motivato (§2-bis).

**δ, prior di cold-start delle neopromosse.** Definizione invariata:

```
δ = ln( gol_medi_della_lega / gol_medi_delle_promosse_alla_prima_stagione )
```

| lega | δ | lettura |
|---|--:|---|
| Serie A | 0.23 | ln(1.36/1.08) |
| Premier | 0.33 | promosse inglesi molto più deboli |
| La Liga | 0.22 | ln(1.291/1.038) |
| **Bundesliga** | **0.28** | promosse tedesche più deboli della media |
| **Ligue 1** | **0.19** | **direzione opposta**: le promosse francesi sono le meno deboli del campione |

Il guadagno misurato dell'adozione è **+0.0001 e +0.0000** di log-loss, cioè
nulla: i δ sono adottati per **motivazione strutturale**, non per miglioramento,
ed è scritto così anche nel commento di `src/config.py`. La Ligue 1 è il caso
istruttivo: il suo δ va nella direzione opposta a tutte le altre leghe e il
modello non se ne accorge — la leva è reale ma la sua ampiezza è sotto la
risoluzione del test.

**θ, sotto-dispersione double-Poisson.** Stimato per massima verosimiglianza sui
punteggi dati i tassi del mercato:

| lega | θ | il router paga? | profondità della valle |
|---|--:|:-:|--:|
| Serie A | 1.232 | sì | −0.0081 |
| La Liga | 1.242 | sì | −0.0081 |
| Premier | 1.085 | no | −0.0012 |
| **Bundesliga** | **1.080** | **no** | **−0.0012** |
| **Ligue 1** | **1.103** | **no** | **−0.0017** |

Due famiglie nette. E una correzione di metodo: la tesi «la griglia stima θ
meglio della massima verosimiglianza» **non regge come enunciata** — sul
risultato esatto la griglia ricade sul θ MLE entro mezzo passo in 5 leghe su 5,
perché `fit_theta` minimizza *esattamente* quella log-loss. Griglia e MLE
divergono solo quando si cambia **metrica**: la frase giusta è «mercati diversi
vogliono θ diversi».

**Il guard sull'overround.** Bilaterale, con soglia motivata dai dati:

```
orr = Σ 1/quota_i          # su TUTTE le quote dello stesso mercato
scarta il mercato IN BLOCCO se  orr < 1.0  oppure  orr > ORR_MAX = 1.12
```

`ORR_MAX = 1.12` non è scelto a occhio: nell'era `Avg` il massimo mai osservato
su 12.457 righe è **1.0765**, quindi 1.12 sta ~6 σ oltre la mediana sana e 4
punti percentuali sopra quel massimo — non può scartare una riga buona. Provato:
ri-derivando tutte e 10 le colonne quota delle 5 leghe col codice di produzione,
il guard cambia **6 celle** (La Liga 2018-19, overround fino a 1.283) e **zero**
altrove su 16.111 partite.

**Lo stimatore della chiusura O/U.** Formula invariata (E3, regressione logit):

```
logit(p_close) = β0 + β1·logit(p_open) + β2·Δlogit(H) + β3·Δlogit(D) + β4·Δlogit(A)
```

con Δlogit(·) = movimento 1X2 apertura→chiusura. Fit pooled, ora su 12.457
partite e 5 leghe: coefficienti `[0.0248, 0.9798, 1.3929, −0.8398, 1.3933]`.

Il numero che è cambiato è **l'errore dichiarato**, e vale la pena spiegarne il
perché. Con un protocollo di *interpolazione* (il fit vede stagioni prima e dopo
la riga stimata) il MAE è ~0.012, ed è il valore storicamente pubblicato. Ma
questa stima non viene mai usata così: la chiusura O/U del 2017-19 **non
esiste**, quindi i coefficienti possono venire solo da stagioni successive.
Misurato in quel regime — fit sulle stagioni tarde, stima sul 2017-19 — l'errore
è **0.0143 in Bundesliga e 0.0125 in Ligue 1**, il 15-25% più alto. Si dichiara
quello.

È anche il motivo per cui il ribaltamento «lo stimatore passa da pooled a
per-lega» **non regge**: vinceva in interpolazione (−0.00031, CI conclusivo) e
**perde nel regime d'uso** (+0.00104, CI conclusivo). Il protocollo di
validazione non era sbagliato in astratto: era il protocollo sbagliato *per
questa domanda*.

Run nel registro: `build_estimates_ou_close`, `build_estimates_squad_value` e
`build_estimates_open_sparse` in `experiments/runs.jsonl` (gli ultimi datati
2026-07-26) — sono i backtest di fedeltà degli stimatori, l'unica parte della
fase che produce metriche di modello. L'audit riga-per-riga non ha run propri:
i suoi artefatti sono gli 11 report in `docs/audit_5_leghe/` e i JSON grezzi in
`docs/audit_5_leghe/numeri/`.

---

## Fase 101 — Quinto audit: le ultime 20 fasi e l'integrazione che non era stata eseguita

### 1 · Obiettivo

Richiesta dell'utente, testuale: *ricontrollare completamente le ultime 20 fasi
alla ricerca di errori, calcoli sbagliati, cose importate male o qualsiasi altro
problema*, e in più *cercare se abbiamo lasciato qualcosa a metà, se abbiamo
dimenticato di scrivere qualcosa che compare da una parte ma non dall'altra*.

Il perimetro sono le **Fasi 80-100** e — soprattutto — l'**integrazione del
lavoro dal branch di cantiere a `main`** (5 commit, `03d5bec`→`6c9b377`), che è
il tipo di operazione dove si perde roba senza che nessun test se ne accorga.

### 2 · Ragionamento e ipotesi

Tre ipotesi, in ordine di sospetto.

**(a) Gli errori non sono nei modelli.** Le fasi recenti sono state controllate
da quattro audit precedenti (84, 86, 90, 92) e le formule hanno il blocco 📐 che
le lega al codice. Se c'è un guasto, sta nei **giunti**: fra un documento e
l'altro, fra il cantiere e il progetto, fra una conclusione ritirata e i posti
dove era stata copiata.

**(b) Un'integrazione dichiarata non è un'integrazione verificata.** Il commit
finale elenca ogni spostamento e pubblica perfino la tabella di corrispondenza
vecchio→nuovo percorso. Ma dichiarare dove va un file non è la stessa cosa che
**eseguirlo** da lì.

**(c) Le auto-correzioni si propagano peggio delle scoperte.** Una scoperta
viene scritta ovunque con entusiasmo; una ritrattazione viene scritta dove è
nata e poi dimenticata. Cercare nei documenti *le frasi che nessuno ha
aggiornato* è più redditizio che ricontrollare i conti.

### 3 · Alternative considerate

Rileggere tutto in sequenza (esaustivo ma lento, e con un solo punto di vista)
contro **13 fronti in parallelo**, ognuno con un mandato diverso e un
**verificatore avversariale** incaricato di smontare i rilievi del proprio
fronte. Scelto il secondo, con una regola esplicita per i verificatori: *meglio
smontare un rilievo vero che lasciar passare un rilievo falso*, perché in questo
progetto un falso positivo fa «correggere» cose giuste alla sessione dopo.

Sui rilievi trovati: limitarsi a elencarli (è ciò che era stato chiesto) contro
correggere anche. Scelto **entrambi**, con un taglio netto: si correggono le
**rotture** (codice che non parte, dati a rischio, link morti) e i **numeri
sbagliati e certi**; si lasciano alla decisione dell'utente i punti che
richiedono un ricalcolo o un giudizio, elencati uno per uno.

### 4 · Scelta

Verbale completo in **`docs/AUDIT_FASI_80_100.md`**: 198 rilievi con evidenza,
verdetto della contro-verifica, e stato (corretto qui / da decidere).

### 5 · Risultato

**198 rilievi, 16 gravi. Nessuno nei modelli.** Le formule del blocco 📐
corrispondono al codice, gli snapshot corrispondono alla fonte, i conteggi delle
partite tornano (16.111 = 3.420×3 + 2.754 + 3.097, con le irregolarità vere), le
regole di spareggio corrispondono ai regolamenti citati. Gli errori stanno tutti
nei giunti, come da ipotesi (a).

**L'integrazione aveva portato in `main` 32 script che non partivano.** Spostati
da `cantiere/scripts/` a `scripts/`, avevano conservato
`ROOT = Path(__file__).resolve().parents[2]`: corretto un livello più in basso,
`/home/user` da qui — **fuori dal repository**. 24 morivano su `import src`;
tutti e 32 leggevano e scrivevano dentro `cantiere/`, cancellata dallo stesso
commit. Conseguenza non teorica: la Fase 100 **non era riproducibile** — né
l'audit dei dati, né le correzioni dichiarate (R3), né gli snapshot delle due
leghe nuove; e `fetch_sources.py` avrebbe scaricato 135 MB in
`/home/user/cantiere/`, un albero fantasma invisibile a git. Corretto: tutti e
32 partono, e `applica_correzioni.py --dry-run` ripercorre le **31 righe** del
registro confermando cella per cella le **27** con stato «applicata» (le altre 4
non lo sono e non devono esserlo: 2 proposte e 2 ritirate) — l'idempotenza R3 è
di nuovo **dimostrabile**, non solo affermata.

**Un bug distruttivo latente.** `build_database.py --league <lega>` onorava la
lega solo nel download: ogni lettura e ogni scrittura passavano da
`database.SNAPSHOT_PATH`, cablato sulla Serie A. `--league bundesliga --refresh`
avrebbe scritto la Bundesliga **sopra** `data/serie_a_matches.csv`. Corretto, e
i rami `--fixtures`/`--refresh` sono diventati per-lega invece che solo-Serie-A.

**Il denominatore dell'audit era sbagliato: 15.788 invece di 16.111.** Non
corrisponde a nessun universo del progetto — verificato provando xG, quote,
apertura, tiri, valore rosa e l'esclusione di ogni singola stagione — mentre gli
artefatti **dell'audit stesso** sommano a 16.111. Era il numero-titolo della
Fase 100, ripetuto in 11 punti. Corretto ovunque; «0 differenze» non cambia.

**«8 anomalie reali, tutte nella fonte» non regge sui suoi stessi report:** una
è un falso positivo ritirato (l'xG a 0.00 era un autogol) e una è un difetto
**nostro** (l'ordine delle colonne). Sono 7: 6 nella fonte + 1 nostra.

**Cinque conclusioni ritirate erano ancora vive altrove:** la diagnosi rovesciata
dalla Fase 92 (in tre punti del README, in contraddizione con la correzione
scritta 300 righe più su nello stesso file), il lead della Fase 98, la premessa
GG/NG caduta con la Fase 100, la rete «bloccata», e il residuo M2 già chiuso.

**Ed è emersa una fase fantasma.** La **Fase 92-bis** aveva cambiato codice di
produzione (`MARKET_ENGINE` per-lega, il bootstrap a grappoli che toglie la
conclusività all'IC del top-4 della Fase 91) senza voce nel diario, riga nel
README o stato in PANCHINA: «92-bis» non compariva in nessun `.md`. Per questo
la Fase 91 e il README hanno continuato per nove fasi a dichiarare «entrambi
conclusivi» su un intervallo che **include lo zero**. La voce mancante è stata
scritta; la Fase 91 porta ora il suo blocco di rettifica.

**Due bug nel tool.** `predict.py` applicava la φ35 al path DC anche su Premier
e Liga, dove la Fase 79 la misura dannosa (+1.0pp di pareggio nella direzione
sbagliata) — lo stesso difetto che la Fase 92-bis aveva corretto sull'altro
path; e `--no-draw-balance` era dichiarato nel parser e mai letto (due
esecuzioni con e senza davano output identici byte per byte).

**Tre test nuovi dove un errore sarebbe passato:** la copertura delle mappe
per-lega (`MARKET_ENGINE` ne aveva 3 su 5) e due che **distinguono** le tuple di
spareggio di Bundesliga e Ligue 1 — differiscono solo per la posizione di `h2h`,
e finora scambiarle passava la suite. 197 test verdi.

### 6 · Lezione

**Un'integrazione va eseguita, non solo spostata.** Il difetto era di una riga e
il costo è stato la riproducibilità della fase più grande del progetto. Dopo
ogni spostamento di file eseguibili serve uno smoke test che li importi tutti.

**Una conclusione ritirata va inseguita.** Cinque catene su cinque erano state
corrette all'origine e lasciate vive altrove; e il caso peggiore è nato da una
fase mai scritta, perché una correzione non può propagarsi da un posto che non
esiste. La checklist §2 non è burocrazia: è il meccanismo che impedisce a una
ritrattazione di perdersi.

**Corollario per gli audit:** i quattro precedenti cercavano errori nei
*calcoli*. Questo li ha cercati nei *giunti*, e lì ne ha trovati sedici gravi
mentre nei calcoli non ce n'era nemmeno uno.

### 7 · Un rilievo ritirato (e perché sta qui)

Al momento di committare ho scritto un ottavo rilievo grave — «`main` non ha mai
ricevuto l'integrazione, è fermo alla Fase 88» — leggendo `origin/main` dal
**ref locale**, vecchio di un `fetch`. Interrogata la fonte, `main` è a
`6c9b377` («Integrazione 3/3c», 26 luglio): l'integrazione c'è e la regola
§3-bis è stata rispettata. Il rilievo è stato ritirato lo stesso giorno.

Sta nel diario per la regola §1.4, ma soprattutto perché è **lo stesso errore
che questa fase trova negli altri**: una copia locale scambiata per la fonte. È
la lezione della Fase 100 («verificare contro la fonte-madre, non contro sé
stessi») applicata a un oggetto — lo stato di un branch — a cui non avevo
pensato di applicarla. Costo: un rilievo grave inventato, sopravvissuto fino
alla prima domanda dell'utente sui branch.

### 📐 Il modello in dettaglio

**Nessuna matematica nuova**: è una fase di verifica. Le due formule toccate
sono richiami, e la terza è la ricetta di controllo che questa fase introduce.

**(1) Il motore per-lega sul path DC** (`scripts/predict.py`, corretto qui). Era:

```
d_dc = price_markets(lam_dc, mu_dc, rho, phi0=m.draw_phi0, kappa=m.draw_kappa,
                     dp_theta=MARKET_ENGINE[lega]["dp_theta_dc"])
```

cioè θ per-lega ma **φ dal fit, sempre**. Ora la φ segue lo stesso motore:

```
use_phi = bool(MARKET_ENGINE[lega]["phi0"]) and not args.no_draw_balance
phi0  = m.draw_phi0  se use_phi  altrimenti 0
kappa = m.draw_kappa se use_phi  altrimenti 0
```

Perché `bool(eng["phi0"])` e non un flag dedicato: la mappa già distingue
«motore con correzioni» (Serie A, φ0=0.30) da «motore liscio» (le altre quattro,
φ0=0.0), e aggiungere un secondo interruttore avrebbe creato due fonti di verità
per lo stesso stato. Effetto misurato su Newcastle-Liverpool (Premier), snapshot
congelato, `as_of = max(date)+1`: il pareggio passa da **25.8%** a **24.8%**
(−1.0pp, coerente con il +1.0pp che la Fase 79 misura come direzione sbagliata)
e l'1X2 torna quello del motore liscio (34.8 / 24.8 / 40.4 contro
34.4 / 25.8 / 39.8); sulla Serie A l'output è invariato.
*(La prima stesura scriveva «da 25.4% a 24.8%, −0.6pp»: il valore pre-fix è
25.84% — enumerati tutti e quattro gli incroci fit×pricing della φ, nessuno dà
25.4%.)*

**(2) Il denominatore.** L'universo dell'audit è l'unione degli snapshot:

```
N = Σ_lega |snapshot_lega| = 3.420·3 + 2.754 + 3.097 = 16.111
N_understat = 16.111 − 1 = 16.110   (una gara di Ligue 1 senza corrispondenza)
```

Il 16.110 non è una scelta di comodo: è il numero che compare nei check `C1` dei
cinque `audit_*.json` («0 righe con gol diversi tra football-data e Understat; N
partite senza corrispondenza»). Il 15.788 non è ottenibile da nessun filtro
(provati: `home_xg` non nullo → 16.109; `odds_home` → 16.109; `odds_over25` →
12.459; `odds_home_open` → 16.110; `home_sot` → 16.110; esclusione di ciascuna
delle 9 stagioni → 14.285…14.386). È un numero senza padre.

**(3) La ricetta di controllo di questa fase**, perché sia ripetibile: per ogni
rilievo si esige la tripletta *(dove, atteso, trovato)* con il comando che la
produce, e il rilievo passa solo se un secondo agente, incaricato di
**confutarlo**, non ci riesce. Su 198 rilievi la confutazione ha smontato 2
rilievi interi e ridimensionato 35: circa **il 19% di ciò che un auditor
scrive** non sopravvive a chi prova a smontarlo — che è la ragione per cui il
passo esiste.

---

## Fase 101-bis — Applicare le correzioni dell'audit: quattro conclusioni declassate, e il numero-bandiera rimisurato

> **Questa voce è stata scritta alla Fase 117**, non alla Fase 101-bis. La fase
> aveva una riga nel registro del README e le sue rettifiche sparse come note
> dentro le fasi corrette, ma **nessuna sezione qui** — cioè esattamente la
> «fase fantasma» che l'audit della Fase 101 aveva rimproverato alla Fase 92-bis,
> ripetuta a due fasi di distanza. I numeri qui sotto provengono dalla riga di
> registro della Fase 101-bis nel README e dai punti ✅ di
> `docs/AUDIT_FASI_80_100.md` §4, che sono le fonti contemporanee alla fase.

**Obiettivo.** Applicare i 13 punti che la Fase 101 aveva lasciato aperti perché
richiedevano una **decisione** o un **ricalcolo**. Criterio dichiarato in
apertura, e vale la pena isolarlo perché ha guidato tutto il resto: **un falso
positivo applicato costa più di un difetto lasciato**. Da cui la regola operativa
della fase — ogni patch va ri-verificata *indipendentemente* prima di essere
applicata, anche quando l'audit che la propone è lo stesso di ieri.

**Ragionamento / ipotesi.** Un audit produce due categorie di rilievi che si
somigliano e non vanno trattate uguale: quelli in cui **il numero è sbagliato**
(si corregge) e quelli in cui **il numero è giusto ma la frase che lo racconta
promette più di quanto il numero sostenga** (si declassa). La seconda categoria è
la più insidiosa, perché niente nel repo è formalmente falso: sono affermazioni
vere-ma-troppo-forti, e sopravvivono agli audit proprio perché ogni singola cifra
regge al controllo. Quattro delle cinque rettifiche di questa fase sono di questo
tipo.

### Risultato 1 — il numero più citato del progetto è cambiato alla quarta cifra

Il gap 1X2 col mercato in Serie A era dichiarato **+0.0165** (log-loss 0.9797) in
17 punti fra README e `CLAUDE.md`. Ma il fix del prior della Fase 92 aveva
cambiato il codice **senza** che nessuno rifacesse la misura. Rieseguito il
walk-forward ufficiale al codice di HEAD (6 stagioni Serie A, config ufficiale):

| | dichiarato (PRE-fix) | rimisurato (HEAD) |
|---|--:|--:|
| log-loss DC | 0.9797 | **0.9799** |
| log-loss mercato | — | **0.9632** |
| **gap** | +0.0165 | **+0.0167** |
| ROI | −15.67% | **−15.8%** (su **866** scommesse) |

La differenza è **irrilevante nel merito e grave nel metodo**: non cambia una
conclusione — il modello non batte il mercato prima e non lo batte adesso — ma
era il numero più ripetuto del repo, e per nove fasi ha misurato una versione del
codice che non esisteva più. La regola che ne esce è nella lezione in fondo.

Distinzione adottata, e mantenuta da qui in avanti: dove `+0.0165` compare come
**misura interna a una fase vecchia** resta, marcato «PRE-fix Fase 92» (è un
confronto legittimo fra varianti misurate insieme); dove compariva come **stato
attuale del progetto** è diventato `+0.0167`.

### Risultato 2 — quattro conclusioni declassate (nessuna era un errore di calcolo)

| # | conclusione com'era | com'è dopo il ricalcolo |
|--:|---|---|
| 1 | **F85**: la COM-Poisson è una famiglia diversa dalla dp e la **conferma** | è la **stessa** dp riparametrizzata → non è una conferma indipendente, è la dp contro sé stessa. E su griglia fine l'argmin è **θ=1.18**, non 1.225 (Δ −0.00027, IC95 [−0.00083, +0.00027]: nel rumore) |
| 2 | **F88**: «α\*=0 su un mercato NUOVO» (il margine) | l'encompassing **non era mai stato calcolato**. Rifatto sui 7.437 casi: α\* = **1.08** [+0.147, +2.052], IC che **esclude** lo zero. Conclusione onesta: «**pareggio in Brier** col mercato sharp» (ΔBrier −0.000136 [−0.000362, +0.000083]) |
| 3 | **F93**: «siamo **meglio calibrati** del mercato» (0.00083 vs 0.00125) | **non conclusivo**: IC95 [−0.00135, +0.00049], e il segno **si inverte** passando a 50 e 100 fasce. Entrambi i valori sono al pavimento di rumore (p95 = 0.00083) |
| 4 | **F93**: «calibrazione −4%, informazione +104%» | le quote sono normalizzate su 0.0094, cioè il **44%** del deficit di 0.0215 che la frase nomina. Il **56% resta non attribuito** |

Il termine che regge, in F93, è uno solo: la **risoluzione**, +0.00981 [+0.00747,
+0.01246] — l'unico con IC che esclude lo zero. Cioè: il mercato ci batte perché
sa **discriminare** meglio, non perché sia meglio calibrato. Che è la diagnosi
della Fase 92, e resta in piedi.

### Risultato 3 — una riga del registro che mescolava due epoche

La riga della Fase 91 nel README è stata **ri-letta interamente** sull'artefatto
post-fix, perché la prima stesura mescolava numeri pre- e post-fix del prior
nella stessa frase:

- ECE **0.0140**;
- mercato retrocessione: **+0.0925** [+0.0465, +0.1341] contro il tasso base, ma
  **−0.0066** [−0.0364, +0.0208] contro la persistenza — cioè batte la baseline
  ingenua e **non** quella seria;
- **30** casi sopra il 60% dichiarato, non 37.

E la conclusione «top-4 batte la persistenza, entrambi conclusivi» era già stata
ritirata dalla Fase 92-bis (IC a grappoli [−0.0006, +0.0522], include lo zero) ma
**era sopravvissuta nei documenti per nove fasi** — perché la fase che la ritirava
non aveva una voce di diario. Lo stesso difetto che questa voce, scritta alla
Fase 117, sta rimediando per la Fase 101-bis.

### Risultato 4 — come si legge «198 rilievi»

Il verbale stesso è stato corretto, ed è la correzione più utile a chi legge
l'audit domani: i **198 rilievi** vanno letti come **~143 difetti distinti in 6
famiglie gravi** — 10 dei 16 rilievi gravi sono *la stessa* rottura degli script
contata dieci volte. Altre rettifiche al verbale: 53 rilievi non
contro-verificati (non 51), «31 correzioni» → **27 applicate** su 31 righe,
manifest **36 dei 140** grezzi cancellati con impronta.

### 📐 Il modello in dettaglio

Nessuna matematica **nuova**: la fase ricalcola. Ma la conclusione 1 del
Risultato 2 merita di essere dimostrata invece che misurata, e alla Fase 101-bis
non lo era: era sostenuta da un'evidenza *numerica* (dp e COM coincidono a
≤5e-06 sull'exact-score log-loss, ≤2e-05 sulle code). Un accordo a 5e-06 è una
prova debole — potrebbe essere due famiglie diverse che quasi coincidono nel
regime dei gol. **È invece un'identità algebrica esatta**, e si vede in tre righe.

La double-Poisson di Efron come è implementata (`src/models/market_implied.py`,
`_dp_pmf`, righe 47-63), mean-preserving con `c` risolto per bisezione perché la
media resti `rate`:

```
q_k ∝ [ Poisson_k(c·rate) ]^θ = [ (c·rate)^k · e^(−c·rate) / k! ]^θ
```

Si sviluppa la potenza e si separa ciò che dipende da `k` da ciò che non dipende:

```
q_k ∝ (c·rate)^(θk) · e^(−θ·c·rate) / (k!)^θ
        \_________/   \____________/   \____/
         dipende da k   COSTANTE in k    (k!)^θ
```

Il fattore `e^(−θ·c·rate)` **non dipende da k**: sparisce nella
rinormalizzazione. Resta

```
q_k ∝ [ (c·rate)^θ ]^k / (k!)^θ
```

che è **esattamente** la COM-Poisson `P(k) ∝ λ^k / (k!)^ν` con

```
λ_COM = (c·rate)^θ        ν = θ
```

*Perché questo chiude la questione.* Non è «due modelli che danno numeri simili»:
è **un solo modello con due parametrizzazioni**, e la mappa fra le due è in forma
chiusa. Verificato eseguendo, sui tassi che il progetto usa davvero: `max|dp −
COM|` = **1.8e-14** a (rate 1.35, θ 1.225), **4.1e-14** a (0.90, 1.138), **1.2e-14**
a (2.10, 1.18) e **3.3e-15** a (1.00, 0.85) — precisione macchina, tre ordini di
grandezza più stringente del ≤5e-06 empirico, e vale anche in sovra-dispersione
(θ<1), dove nessuno aveva guardato. Un «bakeoff» fra dp e COM-Poisson non può
quindi dare altro che pareggio: **è la stessa distribuzione**. Il ν della
COM-Poisson *è* il θ del router.

**Lezione.** Un fix del codice che non fa rimisurare i numeri pubblicati lascia
il repo in uno stato peggiore di prima: prima c'era un numero giusto, dopo c'è un
numero *plausibile*. E un numero plausibile non si scopre leggendo — solo
rieseguendo. Da cui la regola che questa fase consegna alle successive: **chi
tocca il codice che produce un numero-bandiera lo rimisura nello stesso commit,
o dichiara che non l'ha fatto.**

---

## Fase 101-ter — Chiudere i punti aperti: i numeri orfani, e tre trappole che colpivano CHI VERIFICA

**Obiettivo (utente).** «Sistema ogni problema e correggi ogni numero sbagliato,
poi riordina `main`.» Cioè: portare a conclusione i 13 punti che l'audit della
Fase 101 aveva lasciato aperti perché richiedevano *una decisione* o *un
ricalcolo*, non una riscrittura — e fare ordine nel branch.

**Ragionamento / ipotesi.** I punti aperti erano di tre nature diverse, e
mescolarle sarebbe stato l'errore: (a) **numeri orfani**, cioè pubblicati ma non
ri-derivabili da nulla di committato — vietati dal §2-bis punto 4, e l'unico modo
di chiuderli è *calcolarli*; (b) **decisioni sui dati**, dove il lavoro è
scegliere e dichiarare, non misurare; (c) **manutenzione**, dove basta fare.

### Risultato 1 — un numero orfano si scopre solo provando a rifarlo

Tre numeri pubblicati non erano ri-derivabili. Rifacendoli, due hanno retto e
uno era sbagliato:

| numero | dove | esito del ricalcolo |
|---|---|---|
| gap **GG/NG −0.0018** (riga pooled F9) | README | ❌ **orfano**: ri-derivato dà **+0.0026**. Le altre cinque celle della riga coincidevano già con la matrice F15-bis; questa no, perché misurata contro un riferimento diverso **mai dichiarato** |
| **α\*=1.08** dell'encompassing F88 | DIARIO, README | ✅ riprodotto alla cifra, ma **non lo produceva nessuno script** |
| **«18 stagioni su 24»** con σ 0.18 (F94) | DIARIO | ✅ **regge**: top-4 migliore in **6/24**, test dei segni **p = 0.0227** |

Il primo è il caso interessante: non era «un numero un po' diverso», era un
numero che misurava **un'altra cosa** — e nessuno poteva accorgersene, perché il
riferimento non era scritto. È esattamente il difetto che il §2-bis punto 3
prescrive di dichiarare.

### Risultato 2 — il protocollo di stima può cambiare il SEGNO del risultato

Portando l'encompassing della Fase 88 dentro `_run_ah_benchmark.py`, il
walk-forward non tornava: ottenevo **+0.000011** dove il README dichiara
**−0.000064**. Non era un errore di nessuno dei due: sono **due protocolli
diversi** di stima di α, entrambi legittimi.

| variante | n fuori campione | Δ Brier (blend − mercato) | IC95 | P(Δ<0) |
|---|--:|--:|---|--:|
| α **pooled** su tutte le leghe (è quella pubblicata) | 6.297 | **−0.000064** | [−0.000271, +0.000139] | 0.73 |
| α dalla **sola lega** valutata | 6.297 | +0.000011 | [−0.000236, +0.000265] | 0.46 |

La conclusione non cambia (il blend non batte il mercato: entrambi gli IC
includono lo zero). Ma **il segno sì**, e con esso la frase che uno scriverebbe.
Con un effetto di 6·10⁻⁵ di Brier, la scelta del pool su cui si stima α pesa
quanto la misura. Lo script ora stampa **entrambe**.

*(Nota: la ri-derivazione ha anche risolto una discrepanza fra due agenti sul
numero di casi fuori campione — 6.297 contro 6.518. Il primo è giusto: le righe
escluse sono la prima stagione di **ciascuna delle 3 leghe**, 1.140, non di una
sola.)*

### Risultato 3 — tre trappole, e colpivano tutte CHI VERIFICA

È il risultato che mi sembra valga oltre questo repo. Tre difetti indipendenti,
stessa forma: **l'atto di controllare un numero danneggiava la fonte di quel
numero, o veniva bloccato da un vincolo stantio.**

1. `_run_fase94_drift.py` **sovrascriveva l'artefatto ufficiale a ogni
   esecuzione**. Due sessioni di seguito hanno dovuto ripristinarlo da git dopo
   aver semplicemente *controllato* una cifra. → Ora solo `--sd-map` (la config
   adottata) scrive `fase94_drift.json`; ogni altra config scrive un file
   `_variante_<σ>.json`.
2. `stima_ou_open_bakeoff.py` aveva `assert len(tg0) == 9` — il conteggio delle
   celle bersaglio **al momento della prima stesura** — mentre le bersaglio si
   auto-selezionano (`S.y.isna()`). Appena le 3 righe La Liga svuotate dal guard
   sono entrate nel conteggio, lo script è **morto sull'assert**: una
   rigenerazione legittima bloccata da una costante. → Sostituito con i controlli
   che servono davvero (stagioni attese, nessun duplicato), e tutti i «9» cablati
   resi dinamici.
3. `applica_correzioni.py` copriva **solo** gli snapshot del cantiere
   (Bundesliga, Ligue 1). Nel frattempo il registro aveva acquisito **6 righe La
   Liga**: correzioni *dichiarate* che nessuno strumento poteva più verificare —
   il contrario di ciò che la regola R3 esiste per garantire. → Copre le 5 leghe.

La forma comune: **un vincolo scritto quando il mondo era diverso, e mai
ri-letto quando il mondo è cambiato.** Non li trova nessun test, perché non
rompono niente finché nessuno verifica.

### Risultato 4 — le 6 celle che vivevano dentro un CSV

Sei celle-quota 1X2 portavano da giorni il verdetto «USARE IL DATO REALE» dentro
`celle_residue.csv`, senza essere né inserite né dichiarate. Eseguite: il dato è
**reale** (dataset iredchuk, identificato per via statistica come chiusura
media-di-mercato e confermato da una **seconda fonte indipendente**), ed è 2,8
volte più preciso della stima che avremmo prodotto noi. Ora le 5 leghe hanno
**zero** righe senza chiusura 1X2.

Il costo è dichiarato in un riquadro di `docs/DATI.md`: per **due partite su
16.111** la colonna cambia semantica (non più «media football-data»). E il test
che asseriva quelle due come eccezioni **si è rotto**, che era il suo scopo:
riscritto sul nuovo invariante e reso più forte — ora verifica anche che le due
righe portino *esattamente* i valori del registro, così una ritirata silenziosa
rompe la suite. Verificato per mutazione.

### 📐 Il modello in dettaglio

Nessuna matematica nuova: questa fase **ricalcola** formule già definite. Le due
che contano, verificate riga per riga contro il sorgente.

**1 · Encompassing** (`scripts/_run_ah_benchmark.py`, `_alpha_star`). Con `y` =
copertura realizzata, `k` = P(copre) del mercato devigato, `m` = P(copre) del
router, il blend è `p(α) = k + α·(m − k)`. Minimizzando il Brier
`mean((p(α) − y)²)` in α si annulla la derivata:

```
d/dα mean((k + α(m−k) − y)²) = 2·mean((m−k)·(k + α(m−k) − y)) = 0
  ->  α* = mean((y − k)(m − k)) / mean((m − k)²)
```

soluzione in **forma chiusa**, non una griglia. `α*=0` ⇔ `mean((y−k)(m−k))=0` ⇔
lo scarto del mercato dal realizzato è **ortogonale** allo scarto modello-mercato:
il mercato ingloba il modello (è il test della Fase 16). Qui α\*=**1.082**, ma
**non** significa «battiamo il mercato»: `m` è una *traduzione* delle stesse
quote 1X2+O/U da cui esce `k`, non un previsore indipendente — per questo il
walk-forward, che è il test onesto, non trova nulla.

*Perché quel valore.* α\*≈1 dice che il router si muove **quanto** il mercato
rispetto al realizzato: le due letture della stessa informazione differiscono per
la forma della matrice (double-Poisson θ=1.225, ρ=−0.06), non per il contenuto.

**2 · Test dei segni** sul «18 su 24» (F94). Sotto l'ipotesi nulla «σ 0.18 non
cambia nulla», il numero di stagioni-lega in cui il top-4 peggiora è
`X ~ Binom(24, 0.5)`. Osservato X=18:

```
p = 2·P(X >= 18) = 2 · sum_{k=18..24} C(24,k) · 0.5^24 = 0.0227
```

che arrotonda allo **0.023** pubblicato. Il σ del confronto è 0.18 perché è il
valore della griglia uniforme che la Fase 94 aveva provato *prima* di scoprire
che la deriva è per-squadra (neopromosse 0.299 contro 0.157 delle altre): serve
come **controllo negativo**, non come candidato.

**Lezione.** Un numero che nessuno script produce non è un numero: è una
citazione. E il momento in cui se ne accorge qualcuno è quando prova a
verificarlo — motivo per cui gli strumenti di verifica vanno protetti almeno
quanto quelli di produzione. Tre difetti su tre, in questa fase, colpivano il
verificatore e non l'utente.

## Fase 103 — Il recupero Wikipedia applicato: chiusi i 1.603 falsi zero di `midweek_europe`

**Obiettivo.** Richiesta dell'utente: verificare che i dati del progetto siano
tutti corretti, e dove mancano cercare fonti esterne (Wikipedia inclusa). Un
sondaggio dello stato (`docs/DATI.md`, `docs/AUDIT_FASI_80_100.md`,
`docs/audit_5_leghe/`) ha trovato il gap più "pronto": la Fase 100 aveva già
raccolto 3.045 righe di calendario di coppa da Wikipedia
(`data/ricerca_esterna/fixtures_*.csv`) per chiudere i 1.603 falsi zero di
`midweek_europe` (regola R6, "il buco peggiore non è il `NaN`: è il finto
pieno"), verificate contro una terza fonte indipendente (openligadb.de, 0/114
non confermate) ma **mai applicate**: la regola R4 del cantiere imponeva di non
toccare snapshot/`src`/`scripts` in quella sessione, solo produrre report e
dati grezzi. La proposta §9 di `caccia_calendari.md` la definiva "la proposta
più solida del lotto" — dato di calendario, errore atteso zero, 5 controlli
superati.

**Ragionamento / ipotesi.** Se il recupero è già stato verificato (aggancio
nomi, doppioni, finestra temporale, confutazione su terza fonte), applicarlo
non richiede nuova ricerca: richiede solo (a) unire le righe recuperate ai
calendari di club esistenti, (b) ricalcolare le 4 colonne derivate
(`fixtures.add_rest_days_full`), e (c) verificare che il risultato riproduca
ESATTAMENTE i numeri già pubblicati altrove nel progetto (`celle_residue.csv`,
citati in CLAUDE.md e `docs/DATI.md`) prima di scrivere qualsiasi file — la
stessa disciplina "verifica-poi-applica" di R3, estesa a un dato derivato
invece che a una cella osservata.

**Alternative considerate.**
1. *Registro correzioni per-cella* (`correzioni_dichiarate.csv`, R3): scartata
   — le 1.603 celle sono un ricalcolo deterministico di una pipeline
   (`add_rest_days_full`), non un valore osservato corretto a mano; un registro
   di 1.603 righe sarebbe rumore documentale, non tracciabilità.
2. *Rifare la raccolta da zero* (script `caccia_calendari.py`/`wiki.py` citati
   solo come Appendici A/B nel report, mai versionati): scartata — i 3.045
   righe sono già su disco e già verificate; rifare la raccolta duplicherebbe
   lavoro già fatto e già controllato (istruzione esplicita: non duplicare ciò
   che un audit precedente ha già verificato a fondo).
3. *Includere solo le competizioni già note* (Champions/Europa/Conference +
   coppa nazionale), scartando supercoppe/Mondiale per club/Coupe de la Ligue
   (proposta §9.4 di `caccia_calendari.md`, mai decisa): scartata a favore
   dell'inclusione totale — è la scelta coerente con la semantica già in uso
   (`is_extra = competition != own_competition`: qualunque partita non di
   campionato affatica allo stesso modo), **e** è l'unica che riproduce
   esattamente l'oracolo già pubblicato (236/251/454/180/482 celle): significa
   che chi ha calcolato quei numeri in `celle_residue.csv` aveva già preso
   questa stessa decisione, solo mai eseguita.

**Scelta.** Scritto `scripts/integra_calendari_coppa.py`: unisce tutti i file
`data/ricerca_esterna/fixtures_<lega>_*.csv` (nessuna esclusione per
competizione) ai `club_fixtures[_<lega>].csv` esistenti, dedup su (stagione,
squadra, data, competizione, avversario) — lo stesso usato da
`fixtures.build_club_fixtures` — e ricalcola le 4 colonne su ogni snapshot.
Prima di scrivere, verifica per OGNI lega: il numero di righe recuperate
(guardia contro file mancanti/parziali), il numero di celle
`midweek_europe` che passano da 0 a 1, il numero di partite col riposo
cambiato, e che non ci sia NESSUNA regressione (nessuna cella da 1 a 0,
nessun riposo che aumenta — impossibile per costruzione: aggiungere partite
può solo accorciare un intervallo, mai allungarlo). Se anche una sola lega
non combacia con l'oracolo, lo script si ferma e non scrive NULLA, per
nessuna lega (verifica-poi-applica in blocco unico, non lega per lega).

**Risultato.**

| lega | righe agg. | celle `midweek` 0→1 | oracolo | partite riposo cambiato | oracolo |
|---|--:|--:|--:|--:|--:|
| Serie A | 499 | 236 | 236 | 314 | 314 |
| Premier League | 526 | 251 | 251 | 282 | 282 |
| La Liga | 677 | 454 | 454 | 407 | 407 |
| Bundesliga | 326 | 180 | 180 | 189 | 189 |
| Ligue 1 | 1.017 | 482 | 482 | 508 | 508 |

Tutte e 5 le leghe combaciano a cella esatta con l'oracolo pubblicato in
`data/estimates/celle_residue.csv` (caso D), zero regressioni. Suite di test
verde (853 passed) dopo aver esteso `test_fixtures.py` alle nuove etichette di
competizione (`sources.EXTRA_CUP_COMPETITIONS`: Supercoppa Italiana, UEFA
Super Cup, Mondiale/Intercontinentale per club, FA Community Shield, Supercopa
de España, DFL-Supercup, Coupe de la Ligue, Trophée des Champions — mai
modellate prima, emerse dal recupero Wikipedia) e alla parametrizzazione
`altra_lega` (prima solo Premier/Liga, ora tutte e 4 le leghe non-Serie-A).

Nessun impatto sul modello in produzione: `rest_full`/`midweek` sono covariate
**opzionali**, spente di default (`docs/PANCHINA.md`), quindi nessun backtest
"ufficiale" cambia. Ma la conclusione "sono rumore" era misurata su dati con
questo difetto (6-13% delle righe per lega): onestà (regola R7) impone di
ripetere almeno la misura Serie A che quel giudizio cita.

**Ri-verifica (regola R7).** Rilanciato `scripts/_run_midweek_cov.py` (6
stagioni walk-forward Serie A, config ufficiale, stessi split della F36-bis)
sui dati corretti:

| variante | Δ 1X2 log-loss | CI95 | P(mig) | β medio |
|---|--:|--:|--:|--:|
| `midweek` | −0.0003 | [−0.0013, +0.0007] | 74% | −0.0189 (stabile 6/6: −0.0171…−0.0284) |
| `rest_full` | −0.0002 | [−0.0009, +0.0005] | 69% | −0.0120 (4/6 negativo: −0.0552…+0.0138) |
| `rest_full+midweek` | −0.0001 | [−0.0012, +0.0010] | 56% | — |

Praticamente **identico** ai numeri pre-fix (`midweek` Δ −0.0003/β −0.020 →
Δ −0.0003/β −0.0189; `rest_full` Δ −0.0004 → −0.0002): il verdetto "rumore,
ridondanti fra loro" **non era un artefatto del calendario incompleto**. L'unico
dettaglio che cambia è la stabilità del segno di β su `rest_full`, che passa
da non discussa esplicitamente a **4/6 negativo** (non più "quasi stabile");
`midweek` resta l'unica delle due con segno stabile su tutte e 6 le stagioni,
confermando la lettura della F79 ("β stabile ma non generalizza fuori Serie
A"). Aggiornato `docs/PANCHINA.md` (righe #9/#12 e matrice, colonna Serie A);
nessuna promozione, nessuna bocciatura: lo stato resta 🪑 panchina su
entrambe.

**Lezione.** Il costo di applicare una correzione già completamente
verificata non è la verifica (fatta, e non da rifare): è **trovare cosa era
già pronto** prima di iniziare una nuova ricerca. Il sondaggio iniziale su
`docs/DATI.md`/`AUDIT_FASI_80_100.md`/`audit_5_leghe/` ha impiegato meno tempo
dell'intera integrazione, e ha evitato di ripetere una caccia già fatta bene.
La seconda lezione è la stessa della Fase 51/92: un oracolo pubblicato altrove
nel progetto (qui `celle_residue.csv`) è un test di regressione gratuito — se
il ricalcolo l'avesse mancato anche di una sola cella, sarebbe stato un
segnale di bug, non un dettaglio da ignorare.

### 📐 Il modello in dettaglio

Nessuna matematica nuova — Fase 4c/4e definiscono già la formula, qui si
ricalcola con un input più completo.

**`midweek_europe`** (`src/data/fixtures.py:add_rest_days_full`, verificato
riga per riga contro il sorgente):

```
is_extra(riga) = competition(riga) != own_competition        # es. "Serie A"

extra_dates(T) = { date(riga) : riga in calendario, team(riga)=T, is_extra(riga) }

midweek_europe(T, d) = 1  se  ∃ x ∈ extra_dates(T) : d − europe_window ≤ x ≤ d − 1
                      = 0  altrimenti
```

con `europe_window = 4` giorni (default di produzione). La correzione non
tocca questa formula: allarga `extra_dates(T)` aggiungendo le righe recuperate
da Wikipedia a quelle già scaricate da openfootball. Per costruzione un
insieme più grande può solo **aggiungere** un `x` nella finestra `[d-4, d-1]`,
mai toglierne uno che c'era prima — da cui la garanzia "zero regressioni"
verificata (non assunta) dallo script.

**`rest_days_full`** (stessa funzione):

```
rest_days_full(T, d) = min(cap, d − max{ x ∈ all_dates(T) : x < d })
```

con `cap = 14`. Stessa logica: `all_dates(T)` si allarga, quindi la data
immediatamente precedente a `d` può solo avvicinarsi (mai allontanarsi) →
`rest_days_full` può solo diminuire o restare uguale, mai aumentare — il
controllo `rest_increased == 0` nello script verifica esattamente questa
proprietà, non la assume.

**Perché l'oracolo (236/251/454/180/482) è il numero giusto per verificare, e
non un numero a caso.** È stato calcolato *prima* di questa fase, da chi ha
scritto `celle_residue.csv` durante l'integrazione della Fase 101(-bis/-ter),
eseguendo lo stesso ricalcolo su disco ma senza scrivere il risultato (regola
R4 del cantiere in quel momento). Riprodurlo qui, a cella esatta, non è una
coincidenza: è la controprova che l'input (i 3.045 righe) e la pipeline
(`add_rest_days_full`) sono entrambi rimasti quelli descritti, e che la
decisione mai presa esplicitamente al §9.4 di `caccia_calendari.md`
("supercoppe/Mondiale contano come `midweek_europe`?") era già stata presa
implicitamente da chi ha calcolato quel numero.

## Fase 104 — Il resto della lista: Monaco, DFB-Pokal, tre rilievi già chiusi, e la fonte xG con lo stesso mirror morto

**Obiettivo.** Richiesta esplicita dell'utente dopo la Fase 103: "sistema
ognuno di questi problemi, cerca le informazioni da più fonti così sei sicuro
che se una sbaglia, le altre non sbagliano" — riferita alla lista di gap
dichiarati ancora aperti elencata a fine Fase 103 (bug del Monaco, 8 date
DFB-Pokal, F12-04/F12-05/F12-09, le 55 celle residue).

**Ragionamento.** Non trattare la lista come un'unica cosa: ogni punto ha una
natura diversa (bug di codice, duplicato di dati, documentazione stantia,
buco genuino alla fonte) e va istruito separatamente, con la stessa disciplina
verifica-poi-scrivi della Fase 103 — e con **più fonti indipendenti** dove il
compito lo richiede esplicitamente, non solo quella già citata da un audit
precedente.

**Cosa ho trovato e fatto, punto per punto.**

1. **Bug del Monaco (MCO).** `sources.py` filtrava le competizioni UEFA su un
   solo codice paese per lega; l'AS Monaco compare a volte `FRA` a volte `MCO`
   nella stessa fonte openfootball. Aggiunta `UEFA_COUNTRY_CODE_EXTRA` +
   `uefa_country_codes()` (restituisce un insieme, non più una stringa);
   `parse_europe`/`_uefa_team_rows` accettano ora sia una stringa sia un
   insieme (retrocompatibile: i test esistenti passano stringhe singole senza
   modifiche). Test nuovo: `test_monaco_mco_e_fra_entrano_entrambi_in_ligue_1`.
   Non tocca i dati correnti (il recupero Wikipedia della Fase 103 aveva già
   preso il Monaco correttamente, estraendolo da template `{{fbaicon}}` che
   non hanno questo problema): previene la regressione al prossimo
   `build_database.py --fixtures` da openfootball.

2. **8 righe duplicate DFB-Pokal 2025-26.** Non erano "8 date da correggere"
   come proposto in `caccia_calendari.md` §10: il merge della Fase 103 aveva
   già aggiunto la riga GIUSTA (Wikipedia, 2025-12-03) accanto a quella
   SBAGLIATA di openfootball (2025-12-02) per le stesse 4 partite (Bochum-
   Stuttgart, Freiburg-Darmstadt, Hamburg-Kiel, Union Berlin-Bayern Monaco) —
   il dedup su `(season, team, date, competition, opponent)` non le aveva
   fuse perché la data è diversa. **Verificato con due fonti indipendenti
   dal vivo**, non riprendendo solo il numero della Fase 100: query live
   all'endpoint XHR di openligadb.de (`getmatchdata/dfb/2025/3`, turno
   "Achtelfinale") — conferma cella per cella le 4 partite e le loro date —
   e lettura della pagina Wikipedia tedesca (sezione Achtelfinale: "2./3.
   Dezember 2025"). `scripts/correggi_date_dfb_pokal_2526.py` verifica che
   esistano ESATTAMENTE le due righe attese (12-02 e 12-03) per ciascuna
   delle 8 combinazioni squadra/avversario prima di togliere quella sbagliata;
   ricalcolo `add_rest_days_full` sullo snapshot Bundesliga: **0 partite
   cambiate** (la partita più recente delle due vince comunque nella ricerca
   "ultima gara prima di d", quindi il duplicato era innocuo per i numeri, non
   per la pulizia del dato).

3. **F12-04 (celle La Liga fuori registro) e F12-05 (stima O/U non estesa
   alla Liga): già chiusi**, non ancora spuntati. `data/correzioni_dichiarate.csv`
   righe 33-38 registrano le 6 celle La Liga dal commit `ec85314`
   ("integrazione 2/3"); `ou_open_corrotte_2017_19.csv` copre le 12 linee
   (non più 9) dal commit `44052d7`, Fase 101-ter — non 101-bis come diceva
   per errore `data/estimates/README.md` (corretto). Aggiunte note
   `→ ✅ CHIUSO` in `docs/AUDIT_FASI_80_100.md` per non farli riaprire da una
   sessione futura che legge solo il rilievo originale.

4. **F12-09 (verdetti stantii in `celle_residue.csv`): l'ultimo pezzo
   mancava.** Tre dei quattro punti erano già sistemati (righe La Liga
   "CHIUSA", Leganes-Getafe con verdetto proprio, zero riferimenti a
   `cantiere/`); il quarto — `docs/DATI.md` che diceva ancora "registrato ma
   NON inserito" per le 6 celle 1X2 del caso A, già reali nello snapshot dalla
   Fase 101-bis — no. Corretto: censimento **7.359/55 → 7.353/49** (verificato
   contando i NaN live sui 5 snapshot: 7.353 esatto), riga delle 6 celle
   spostata fuori dalla tabella dei buchi con nota di chiusura.

5. **La fonte xG aveva lo stesso mirror morto di football-data, mai
   corretto.** `docs/MANUALE_SOPRAVVIVENZA.md` documentava già dalla Fase 100
   che `understat.com` risponde 200 dietro l'endpoint XHR
   `/main/getLeagueData/{lega}/{anno}` con header `X-Requested-With:
   XMLHttpRequest` (gzip sempre, va decompresso a mano) — ma **il codice non
   lo usava mai**: `sources.UNDERSTAT_URL` puntava ancora al mirror GitHub,
   morto (404 **verificato in modo indipendente dal problema di sessione**:
   `raw.githubusercontent.com` risponde 200 su un repo vero come
   `torvalds/linux`, quindi il 404 è reale e non un artefatto del proxy).
   Corretto `sources.py` (endpoint ufficiale + header) e
   `understat.download_season` (decompressione gzip). **Verificato**: i dati
   live coincidono ESATTAMENTE con quelli già congelati negli snapshot
   (Δ home_xg = 0.0 su 380/380 partite, La Liga 2017-18); scaricate live
   anche Serie A 2025-26, Premier 2024-25 per conferma su altre leghe/stagioni.

6. **Le 55 (ora 49) celle residue: ri-verificate, non tutte risolvibili.**
   Con la fonte xG ora viva, ho ri-scaricato dal vivo le due partite col buco
   xG: **Holstein Kiel-Bochum ha ancora il record segnaposto identico**
   (xG=2.0/2.0=gol esatti) a distanza di mesi — non è un "non ancora", Understat
   non l'ha mai acquisita e non sembra destinata a farlo; **Nantes-Toulouse è
   ancora `isResult: False`** su Understat oltre due mesi dopo la partita —
   stesso esito della prima verifica, ma ora confermato con un ri-controllo
   vero, non un'estrapolazione. Ho anche ri-scaricato dal vivo i CSV grezzi
   football-data per le 3 partite rimanenti (Torino-Fiorentina, Verona-Genoa,
   Union Berlin-Bochum): tutte confermate, colonna per colonna, con lo stesso
   esito già dichiarato (apertura mai raccolta per le prime due — le colonne
   di chiusura `*C` sono piene, quelle di apertura no; tiri in porta assenti
   per la terza). Nessuna delle 49 celle residue si è rivelata recuperabile:
   sono tutte lacune genuine alla fonte, non pigrizia di verifica.

7. **Auto-corretto un bug introdotto alla Fase 103.** Verificando
   `data/estimates/celle_residue.csv` con il modulo `csv` di Python (non
   pandas, che aveva mascherato il problema non essendo mai stato eseguito su
   questo file da nessun test) ho trovato che le 5 righe "CHIUSA alla Fase
   103" che avevo scritto la fase precedente non erano tra virgolette pur
   contenendo virgole: CSV tecnicamente rotto, 19 campi invece di 16 su quelle
   righe. Nessun danno (nessuno script lo leggeva ancora), ma corretto subito
   con una riscrittura verificata (`csv.reader`/`csv.writer`,
   `lineterminator="\n"` esplicito per non introdurre `\r\n` come già successo
   una volta in questa stessa sessione).

**Risultato.** 858 test verdi (+4 dalla Fase 103: 1 nuovo per il Monaco, 3 da
`altra_lega` esteso a Bundesliga/Ligue 1 alla Fase 103). Nessun edge nuovo,
nessuna cella recuperata in più — ma ogni gap dichiarato è ora o chiuso con
un dato vero, o ri-verificato dal vivo con almeno due fonti indipendenti dove
possibile, invece che ereditato da un audit di due fasi prima.

**Lezione.** "Già chiuso ma non spuntato" (F12-04, F12-05) è un modo di
fallire silenzioso quanto "mai chiuso": una sessione futura che legge solo il
rilievo — non lo stato vero dei file — rifà il lavoro. E un file dati non
letto da nessun test (`celle_residue.csv`) può restare rotto per una fase
intera senza che nessuno se ne accorga: la stessa lezione della Fase 15
("un numero che nessuno script produce non è un numero: è una citazione"),
qui applicata a un registro invece che a un calcolo.

### 📐 Il modello in dettaglio

Nessuna matematica nuova: questa fase è infrastruttura e dati, non modello.
Le uniche formule coinvolte sono già definite altrove e richiamate qui senza
modifiche:

- `fixtures.add_rest_days_full` (Fase 4e/59, ricalcolo invariato): il
  duplicato DFB-Pokal non cambia `midweek_europe`/`rest_days_full` perché la
  ricerca "ultima partita di club prima del giorno `d`" (`np.searchsorted`)
  seleziona sempre la data più recente fra le candidate — avere ANCHE la data
  sbagliata (più vecchia) fra le opzioni non cambia mai il risultato quando
  la data giusta è già presente e più recente. Verificato empiricamente
  (0 celle cambiate), non solo per argomento.
- `understat._e_segnaposto` (Fase 100): la firma del segnaposto (xG intero
  uguale ai gol, deep=0 su entrambi i lati, ppda NaN) è verificata di nuovo,
  stavolta su un download live invece che su un JSON cache: stessa funzione,
  stesso esito, fonte diversa.

**Perché questi numeri e non altri.** Il Δ 0.0 su 380/380 partite (La Liga
1718, verifica del nuovo endpoint Understat) non è un valore scelto: è il
risultato di un confronto diretto `snapshot.home_xg - live.home_xg` su ogni
riga appaiata, con `.abs().max()` — la soglia "0.01" nel codice di verifica
serve solo a stampare un conteggio leggibile (`(diff>0.01).sum()`), il
confronto vero è sul massimo assoluto, che è esattamente zero in floating
point (i due JSON sono byte-per-byte la stessa risposta del server, scaricata
due volte a distanza di anni dalla costruzione dello snapshot: Understat non
ha mai ricalcolato l'xG storico di quella stagione).

## Fase 105 — Secondo ri-tentativo sull'O/U 2017-19: quattro angoli nuovi, ancora negativo

**Obiettivo.** L'utente ha chiesto se l'O/U 2017-19 fosse ancora una stima e,
saputo di sì (footiqo/1xBet trovato ma scartato perché peggiore della stima
come proxy multi-book, Fase 100), ha chiesto di riprovare a cercare — in
particolare un secondo book indipendente da mediare col primo, invece di un
singolo book.

**Cosa ho provato (dettaglio completo in `docs/CACCIA_OU_2017_19.md`,
banner Fase 105).** Quattro angoli **mai tentati** nelle Fasi A-D originali:
(1) verificato che footiqo è strutturalmente un solo book, non una via per un
secondo; (2) Wayback Machine — scoperta operativa che l'endpoint CDX è
bloccato dalla rete per qualunque dominio (non un blocco specifico di
oddsportal), ma il playback diretto funziona; nessuna pagina di risultati
stagionale delle nostre leghe risulta mai archiviata per il 2017-19, e le
uniche catture di BetExplorer/OddsPortal per quelle stagioni sono del
2022-2024 — dopo che il sito ha già ritirato il confronto-quote per le
partite vecchie (Fase 100); (3) ricerca dataset ripetuta: un candidato nuovo
su Kaggle è un file di 198 righe di sole partite 2023, altri sono lo stesso
"Beat the Bookie" già scartato; (4) nuovi siti-archivio: `oddsbase.net`
vieta esplicitamente ClaudeBot nel `robots.txt` (rispettata la regola R5.3,
non consultato), `aussportsbetting.com` è bloccato (403), `btfodds.com`/
`sportsoddshistory.com` sono comparatori live senza struttura storica
per-partita individuabile.

**Risultato.** Nessun dato nuovo. La stima (`data/estimates/ou_close_2017_19.csv`)
resta la scelta migliore nota. Nessuna delle vie economiche è cambiata dalla
Fase 100/101-bis.

**Lezione.** Un "no" già scritto in un documento non basta a fermare un
ri-tentativo onesto quando arriva una richiesta esplicita — ma un ri-tentativo
onesto deve provare ANGOLI DIVERSI (qui: Wayback Machine, mai tentato prima),
non ripetere le stesse fonti già scartate. Il valore di questa fase non è nel
dato (zero), è nell'aver ampliato lo spazio di ricerca già coperto e
documentato ANCHE il "blocco CDX" scoperto per caso, utile alla prossima
sessione che voglia usare Wayback Machine per qualunque altra cosa.

### 📐 Il modello in dettaglio

Nessuna matematica: fase di ricerca dati, esito negativo. Non applicabile.

## Fase 106 — Il confronto footiqo-vs-verità esteso da 1 a 6 stagioni: non è stabile nel tempo

**Obiettivo.** L'utente ha chiesto se il confronto MAE "footiqo 0.0156 contro
stima 0.012" (motivo per cui il dato 1xBet trovato alla Fase 100 non è entrato
negli snapshot) si potesse misurare su più di una sola stagione — finora era
il solo 2019-20, l'unica dove la chiusura vera esiste insieme a footiqo.

**Ragionamento.** footiqo.com copre le stagioni dal 2015/16 a oggi (non solo
2017-19); football-data ha la chiusura O/U vera (`AvgC>2.5`) dal 2019/20 in
poi. L'intersezione utile — footiqo disponibile E verità disponibile — non è
un punto solo: sono **sei** stagioni (2019-20 → 2024-25), mai scaricate tutte
insieme prima.

**Cosa ho fatto.** Estesi i fetcher già esistenti (`_fetch_footiqo.py`,
riutilizzato senza modifiche, solo stagioni diverse) per le 5 stagioni
2020-21→2024-25 (25 file nuovi, stesso schema, stesso endpoint, stesso
throttle 1.8s, `robots.txt` invariato); scaricati live i 30 CSV grezzi
football-data corrispondenti (`www.football-data.co.uk/mmz4281/{stagione}/{codice}.csv`,
già raggiungibile). Ricalcolato lo stesso identico confronto del 2019-20 —
MAE e bias di `p_over(xbetClose)` contro `p_over(AvgC)` — su tutte e sei.

**Verifica del metodo.** Il 2019-20 ricalcolato qui riproduce **esattamente**
il numero già pubblicato (n=1.687, MAE 0.0156, bias +0.0088): non è un nuovo
calcolo indipendente che per caso coincide, è la controprova che il metodo è
implementato correttamente prima di fidarsi delle 5 stagioni nuove.

**Risultato — il numero NON è stabile nel tempo** (pooled 5 leghe):

| stagione | n | MAE | bias |
|---|--:|--:|--:|
| 2019-20 | 1.687 | 0.0156 | +0.0088 |
| 2020-21 | 1.749 | 0.0179 | +0.0167 |
| 2021-22 | 1.788 | 0.0192 | +0.0166 |
| 2022-23 | 1.751 | 0.0136 | +0.0054 |
| 2023-24 | 1.640 | 0.0107 | +0.0010 |
| 2024-25 | 1.713 | 0.0096 | +0.0021 |

Il 2020-22 (piena era porte-chiuse) è nettamente il peggiore; dal 2022-23 in
poi footiqo migliora fino a **battere** anche il numero onesto della stima
nelle ultime due stagioni. **Correzione collaterale**: il confronto "storico"
usava 0.012 come riferimento della stima, ma quel numero è il MAE
**ottimistico "in interpolazione"** (`data/estimates/README.md` lo dice
esplicitamente: "non è il regime in cui la stima viene usata"); il numero
onesto è **~0.014 "regime d'uso"** (fit solo su stagioni successive, come
accadrebbe davvero per il 2017-19). Contro quello, il margine del 2019-20 è
più piccolo (0.0156 vs ~0.014, non 0.0156 vs 0.012) ma resta dello stesso
segno.

**Perché non cambia la decisione.** Il 2019-20 resta il proxy singolo più
vicino nel tempo al 2017-19 — e il meno inquinato dalle porte chiuse, iniziate
a marzo 2020 a stagione già per lo più giocata. Lì la stima vince ancora.
Se il pattern 2020-22 è un effetto porte-chiuse (non una deriva secolare di
1xBet/footiqo), il 2017-19 "normale" potrebbe somigliare più alle stagioni
2022-25 (dove footiqo vince) che al 2019-20: **con i dati disponibili le due
letture non sono distinguibili**, e vanno dichiarate entrambe, non scelta
quella comoda.

**Risultato.** Nessun cambio di decisione: la stima resta la scelta per
2017-19. Ma il fatto che lo sappiamo è passato da "una stagione, un numero"
a "sei stagioni, un pattern dichiarato con l'incertezza che porta". Aggiornati
`docs/CACCIA_OU_2017_19.md` (banner Fase 106), `docs/DATI.md`, `docs/PISTE.md`
(la vecchia cifra "MAE 0.0156 contro 0.012" corretta ovunque compare come
riferimento vivo, non nelle voci storiche del README/DIARIO che restano
PRE-fix per lo stesso motivo del numero-bandiera, Fase 101-bis).

**Lezione.** Un numero di validazione misurato su UNA SOLA stagione è un
punto, non una stima dell'incertezza — anche quando quella stagione è la
scelta più difendibile disponibile. "Misurabile su più stagioni" era una
domanda legittima anche per un confronto già chiuso da due fasi: rifarlo non
ha cambiato la conclusione, ma ha sostituito un'assunzione implicita
(stabilità nel tempo) con un fatto misurato (instabilità, con una causa
plausibile ma non provata).

### 📐 Il modello in dettaglio

**Formula**, invariata dalla prima misura (Fase 100/`_valida_footiqo.py`,
CONF-B): per ogni partita appaiata,

```
p_true = (1/AvgC>2.5) / (1/AvgC>2.5 + 1/AvgC<2.5)      # devig binario, media multi-book
p_fq   = (1/xbetCloseOver25) / (1/xbetCloseOver25 + 1/xbetCloseUnder25)  # devig binario, 1xBet
diff   = p_fq - p_true
MAE    = mean(|diff|)          bias = mean(diff)
```

Nessuna novità nella formula: la fase applica lo stesso `p_over`/MAE a 5
stagioni in più, non ne introduce uno diverso — il valore aggiunto è
interamente nel numero di osservazioni (da 1.687 a 10.328 partite totali),
non nel metodo.

**Perché ~0.014 e non 0.012 è il confronto giusto.** La stima E3 è fittata
"pooled su stagioni successive a quella stimata" (regola dichiarata in
`data/estimates/README.md`): per il 2017-19, questo significa fit su dati
2019-20+, cioè esattamente il regime "walk-forward" che dà 0.014. Il numero
0.012 viene da un fit che vede ANCHE le stagioni prima e dopo il target
("interpolazione"): un regime che il 2017-19 non può avere per costruzione
(non ci sono stagioni "prima" nella finestra dati del prog, 2016-17 in poi).
Usarlo come riferimento del confronto era ottimistico verso la stima — un
bias piccolo (0.002) ma nella direzione che rendeva la decisione più
comoda, non meno.

## Fase 107 — Terzo ri-tentativo sull'O/U 2017-19: ri-verifica dal vivo + angoli nuovi, ancora negativo

**Obiettivo.** Richiesta esplicita dell'utente: continuare a cercare il dato
vero, esplorare fonti nuove E verificare — non assumere — che le fonti già
scartate lo siano davvero ancora.

**Cosa ho fatto.**

1. **`oddsportal.com/robots.txt` letto per intero** (prima si citava solo "vieta
   lo storico"): vieta esplicitamente ogni URL con l'anno nel percorso, da
   1998 al 2024 — un blocco sistematico di tutte le pagine-stagione, non un
   dettaglio isolato. Nessun accesso, come già deciso.
2. **BetExplorer ri-controllato dal vivo**, non solo ri-letto dal report della
   Fase 100. Scoperta: il precedente 404 sull'endpoint delle quote era in
   parte affidabile, ma la pagina-stagione stessa risponde 404 **anche oggi**
   senza uno User-Agent da browser — un blocco anti-bot, non un vero "non
   esiste". Con lo User-Agent giusto: pagina vera, partita vera raggiunta. Il
   risultato però è **identico**: `#bettingTabs` ha solo un "1X2" disabilitato,
   nessun tab O/U. La conferma vale di più perché stavolta la richiesta ha
   *davvero* toccato la pagina, non un errore mascherato da conferma.
3. **Il dataset Kaggle `mexwell/...` è stato aggiornato** (versione 2) dal
   primo controllo: ri-scaricato, stessa colonna O/U singola per il 2017-18,
   nessuna chiusura O/U distinta aggiunta.
4. **Tre angoli davvero nuovi**: ricerca di codice GitHub per scraper
   OddsPortal/BetExplorer (trovati solo strumenti — uno conferma da solo che
   serve login e copre solo 1X2, non O/U); dataset accademici su arXiv
   (Bundesliga 2017-19, ma quote **in-play**, mercato sbagliato); provider
   commerciali (`oddalerts.com`, la cui documentazione limita lo storico
   dichiarato a 6 mesi — strutturalmente fuori portata per il 2017-19, prima
   ancora di poterlo controllare per il 403).

**Risultato.** Nessun dato nuovo. Ma la fiducia nel "nessun dato nuovo" è più
solida di prima: il controllo su BetExplorer di questa fase ha **davvero**
raggiunto la pagina (le fasi precedenti rischiavano di scambiare un blocco
anti-bot per un'assenza di dato), e altri tre angoli mai tentati sono stati
chiusi con una ragione specifica, non per esaurimento del tempo.

**Lezione.** Un 404 non è sempre un "non esiste": può essere "non mi hai
chiesto nel modo giusto". Prima di scrivere una fonte come chiusa, vale la
pena controllare se la richiesta ha davvero raggiunto il contenuto (una
pagina vera, non una pagina di errore) — specialmente quando il controllo
precedente veniva da un ambiente diverso (un runner GitHub Actions, Fase 100)
i cui dettagli (header, User-Agent) non sono garantiti identici a un
controllo rifatto altrove.

### 📐 Il modello in dettaglio

Nessuna matematica: fase di ricerca/verifica, esito negativo. Non applicabile.

## Fase 108 — «E se cercassimo partita per partita?» — testato, non scala

**Obiettivo.** Idea dell'utente dopo tre ri-tentativi negativi in blocco:
invece di un dataset che copra tutte le 3.652 partite insieme, cercare il
dato una partita alla volta.

**Cosa ho fatto — due test diretti, non solo un argomento teorico.**
1. Wayback Machine sulla singola pagina-partita (non più sulla pagina-elenco
   stagionale, già risultata mai archiviata): URL reali di partite
   BetExplorer 2017-18, trovati dal vivo alla Fase 107. **404**: nemmeno le
   pagine di singola partita sono mai state archiviate.
2. Ricerca web sul caso più favorevole possibile: **Juventus-Napoli
   22/04/2018**, lo scontro diretto scudetto più seguito della stagione.
   Nessuna quota storica reale trovata: solo pagine "sempre verdi" di siti
   pronostici che si riscrivono per ogni nuovo incontro fra le due squadre.

**Risultato.** Anche nel caso più favorevole (partita più seguita, mercato
più popolare) non si trova nulla di reale e datato. E anche trovando
qualcosa, l'approccio partita-per-partita introdurrebbe un bias di selezione
strutturale (solo i big-match sarebbero "trovabili"), non solo un problema di
scala.

**Lezione.** Testare un'idea sul caso più favorevole possibile, non su un
caso qualunque, è un modo economico di stabilire se un metodo scala PRIMA di
investirci ore: se fallisce lì, fallisce ovunque, e lo si sa con un test solo
invece che con centinaia.

### 📐 Il modello in dettaglio

Nessuna matematica: fase di verifica di un'idea, esito negativo. Non applicabile.

## Fase 109 — Betfair Exchange: il primo candidato MIGLIORE della stima (e una mia valutazione ritirata)

**Obiettivo.** L'utente ha un account Betfair e ha chiesto se si possa
implementare direttamente l'API di `historicdata.betfair.com` nel repo, cosa
serva oltre al token, e «cosa potremmo inventarci».

**Ragionamento.** La tentazione era rispondere subito con lo script. Invece
ho applicato il principio §1.3 — *testa la versione economica dell'idea prima
di investire* — perché c'era un test gratuito disponibile: `football-data`
pubblica la chiusura **Betfair Exchange** (`BFEC>2.5`/`BFEC<2.5`) in una
stagione, la 2024-25. Lì convivono Betfair, la media multi-book e l'esito
reale: si può stabilire **che tipo di fonte sia Betfair senza scaricare nulla**
e senza far fare fatica a nessuno.

**Risultato — e una mia valutazione ritirata.** Su 1.752 partite, 5 leghe:

| fonte | MAE vs media multi-book |
|---|--:|
| MaxC | 0.0057 |
| **Betfair Exchange** | **0.0060** |
| Pinnacle | 0.0063 |
| Bet365 | 0.0071 |
| **la nostra stima** | **~0.014** |
| 1xBet (scartato F100) | 0.0156 |

Betfair è nel **gruppo dei book seri**, non fra gli outlier: **2,3× più vicino
alla media multi-book della stima che sostituirebbe**, bias +0.0015 (contro
+0.0088 di 1xBet), e contro l'esito vero almeno pari alla media dei book
(0.6648 vs 0.6652; Δ −0.00039, IC95 [−0.00115,+0.00038], P 84.7% — non
conclusivo ma col segno a favore, coerente col fatto che una borsa non ha il
margine del bookmaker: overround 1.0053 contro 1.0482).

Alla **Fase 108** avevo detto all'utente che «il guadagno è piccolo». Era
un'**analogia** (Betfair ≈ 1xBet ≈ book singolo), non una misura, e la misura
la smentisce. **Ritirata**, come si fa con ogni conclusione che non regge.

**Cosa NON è deciso.** I numeri vengono dalla 2024-25, non dal bersaglio: la
Fase 106 ha già mostrato che la qualità di una fonte **non è stabile nel
tempo** (1xBet: 0.0096-0.0192 fra stagioni), e la liquidità di una borsa nel
2017-18 era più bassa di oggi, specie su Bundesliga e Ligue 1. Questa fase
apre la pista e costruisce lo strumento; **non** autorizza l'inserimento.

**Cosa ho costruito.** `scripts/fetch_betfair_historic.py`: i 5 endpoint
dell'API più il parsing dello stream storico (`.bz2`, JSON per riga).
Copertura di test: 9 casi in `tests/test_betfair_historic.py` — 871 verdi in
totale.

**Il vincolo che l'utente non poteva sapere.** Non basta il token: i pacchetti
BASIC (gratuiti) di *Soccer* vanno **acquisiti mese per mese** dal sito, e
senza di essi gli endpoint rispondono con **liste vuote e nessun errore**. È
una trappola silenziosa: per questo `--check` esiste, confronta i mesi
posseduti con quelli richiesti, e va eseguito per primo. Inoltre
`historicdata.betfair.com` è **403 dall'ambiente cloud del progetto** (blocco
per regione, *prima* dell'autenticazione: verificato sull'endpoint API, non
solo sul sito) → lo script gira sulla macchina dell'utente.

**Il collaterale può valere più del bersaglio.** Il piano BASIC dà istantanee
**ogni minuto**, non solo la chiusura. `newseason.md` §2 elenca «le quote di
apertura e la loro **traiettoria** verso la chiusura» fra le cose che **non si
recuperano** dopo il calcio d'inizio, e §7 la dichiara «mai avuta a nessuna
scala»: con questi file diventa recuperabile **all'indietro**, dal 2015. Non è
riempire un buco, è un asse di dati nuovo.

**Lezione.** Due, e sono la stessa. (1) Prima di chiedere lavoro a qualcuno,
cercare il test che si può fare da soli: qui esisteva una stagione in cui la
fonte candidata era **già** nei dati che abbiamo, e valeva più di qualsiasi
ragionamento sulla sua natura. (2) Un'analogia («è un book singolo come
1xBet») non è una misura, e produce risposte sbagliate con la stessa
sicurezza di una giusta.

### 📐 Il modello in dettaglio

**Formula**, identica a quella già usata per 1xBet (Fase 100/106) — il
confronto è nuovo, la matematica no:

```
p(fonte) = (1/quota_over) / (1/quota_over + 1/quota_under)     # devig binario
MAE  = mean(|p(fonte) − p(AvgC)|)          bias = mean(p(fonte) − p(AvgC))
LL   = −mean( y·log p + (1−y)·log(1−p) ),  y = 1 se gol totali > 2.5
```

**Perché il devig rende confrontabili borsa e bookmaker.** L'overround grezzo
è molto diverso (1.0053 contro 1.0482): senza normalizzare, i due numeri non
starebbero sulla stessa scala. Dopo il devig entrambi sono probabilità che
sommano a 1, e la differenza residua è **informativa**, non contabile. È
anche il motivo per cui la «rottura di regime» nella colonna grezza — l'argomento
che ha bocciato 1xBet — qui va ri-discussa e non ereditata: pesa sulle quote,
non sulle probabilità che il modello usa davvero.

**Perché la chiusura è definita dal flag `inPlay` e non da `marketTime`.**
Nel formato Betfair ogni riga porta `pt` (istante di pubblicazione) e i
`marketDefinition` segnalano `inPlay`. Prendere l'ora *da calendario*
sbaglierebbe in due direzioni: taglierebbe gli ultimi minuti di mercato per
le partite iniziate in ritardo, e — molto peggio — includerebbe prezzi
**già in-play** per quelle iniziate puntuali, cioè prezzi che sanno cosa sta
succedendo in campo. Sarebbe look-ahead: esattamente l'errore di
Udinese-Roma (`docs/DATI.md`), dove una chiusura che prezzava una ripresa già
in corso falsava il confronto *nella direzione a noi favorevole*. Il test
`test_nessun_look_ahead_i_prezzi_in_play_sono_ignorati` esiste per questo.

### Fase 109-bis — La specifica ufficiale trova un bug nel parser (poche ore dopo)

**Come è successo.** L'utente ha chiesto se riuscivo a leggere la
documentazione Betfair su Atlassian. **Sì**: quel dominio non è soggetto al
geo-blocco che ferma `historicdata.betfair.com`, e il contenuto — invisibile
nell'HTML, perché la pagina è un SPA JavaScript — si estrae dall'**API REST di
Confluence, che risponde 200 senza autenticazione** (fatto operativo nuovo,
annotato nel manuale con gli endpoint esatti).

**Perché contava.** I file del servizio storico sono **registrazioni dello
stream** descritto in quella pagina: era la specifica contro cui il parser
andava verificato, e io lo avevo scritto deducendo il formato dall'esempio,
non leggendola.

**Esito: due assunzioni confermate, una sbagliata.** `ltp` = «Last Traded
Price» ✓ e `inPlay` = «True if the market is currently in play» ✓ — le due
travi portanti reggono. Ma sul campo `img` la specifica dice:

> «img / Image - **replace** existing prices/data with the data supplied: **it
> is not a delta**»

e il parser fondeva **sempre**. Un ri-invio dell'immagine a metà stream
avrebbe lasciato in cache prezzi che la fonte considera sostituiti: non un
crash, non un `NaN` — un numero **plausibile e falso**, cioè il «finto pieno»
della regola R6, quello che nessun controllo a valle vede. Corretto
(`last.clear()` quando `img` è vero), 3 test nuovi, e **verificato per
mutazione**: rimuovendo il fix, `test_img_sostituisce_la_cache_non_la_fonde`
fallisce. 874 verdi.

**Il limite che resta dichiarato.** La specifica descrive lo stream **live**.
Che i file storici la seguano in ogni dettaglio è un'inferenza ragionevole
(sono registrazioni), **non un fatto verificato** — e resta tale finché non
gira il confronto 2024-25 contro `BFEC>2.5`. L'estratto con le citazioni
testuali è in `data/ricerca_esterna/betfair_stream_spec_estratto.md`.

**Lezione.** Il bug non è nato da un dato ambiguo o da una fonte ostile: è
nato dall'aver **dedotto un formato invece di leggerne la specifica**, quando
la specifica era pubblica, gratuita e raggiungibile. È durato esattamente
quanto quella scelta — poche ore, perché l'utente ha chiesto di leggere la
pagina. Regola pratica che ne segue: quando si scrive un parser per un
formato altrui, la ricerca della specifica ufficiale viene **prima** della
prima riga di codice, non dopo il primo test verde.

## Fase 110 — La documentazione Betfair entra nel repo (e smentisce una mia costante)

**Obiettivo.** Richiesta dell'utente: copiare le API Betfair nel repo,
dichiarando da quale sito vengono, «così che in futuro avremo meno lavoro da
fare quando vorremo lavorare su Betfair».

**Scelta: specchiare, non copiare.** Invece di incollare pagine a mano ho
scritto `scripts/fetch_betfair_docs.py`, che estrae le pagine via API REST di
Confluence (200 senza autenticazione, scoperta della Fase 109-bis) e le
converte in Markdown. Così la copia è **ri-generabile** quando Betfair
aggiorna — il contrario del `caccia_calendari.py` della Fase 100, che viveva
solo come appendice di un report e infatti è andato perso.

**Cosa c'è**: **78 pagine** in `docs/betfair_api/` (916 KB), ordinate per
tema (guida → accesso → betting → tipi/enum → stream → mercati nazionali →
ordini → account → linguaggi), più la **Historical Data API** — che sta su un
altro sito, geo-bloccato da qui, e me l'ha fornita l'utente: attribuita a
parte, con la differenza fra i due servizi messa in tabella perché è la
confusione più facile da fare. Escluse note di rilascio e traduzioni.

**Attribuzione.** Ogni file porta in testa: testo **di Betfair, non del
progetto**; URL della pagina originale; id Confluence; data di estrazione; e
la regola che **in caso di dubbio vince la pagina online**. È una copia di
lavoro per riferimento tecnico interno, non una ri-pubblicazione.

**La scoperta collaterale, che vale più della copia.** Cercando la conferma di
`OVER_UNDER_25` nelle 78 pagine: **non c'è**. Betfair **non pubblica l'elenco
dei marketType** — `listMarketTypes` ne cita due come esempio («i.e.
MATCH_ODDS, NEXT_GOAL») e per il resto rimanda a scoprirli a runtime. Quella
costante, su cui poggia tutto il filtro di `fetch_betfair_historic.py`, è
quindi una **convenzione dell'ecosistema, non un valore documentato**: la
stessa classe di assunzione che alla Fase 109-bis è costata il bug su `img`.

Non è correggibile a tavolino (l'elenco vero si vede solo interrogando il
servizio), ma è **degradabile da errore silenzioso a diagnosi**: `--dry-run`
ora stampa i tipi realmente presenti nel pacchetto — tutti quelli che
contengono OVER/UNDER, e in caso di assenza i 15 più frequenti — invece di
limitarsi a un sì/no. Se l'etichetta fosse diversa, si vedrebbe subito;
prima si sarebbe concluso «il mercato non esiste».

**Lezione.** Specchiare una documentazione non è archiviazione passiva: è un
**controllo**. Nel momento in cui la si porta in casa e la si può interrogare
tutta insieme (`grep`), si scopre cosa NON dice — ed è lì che stavano le due
assunzioni non verificate di questo lavoro. La prima l'ha trovata la lettura
(`img`), la seconda la ricerca (`OVER_UNDER_25`).

### 📐 Il modello in dettaglio

Nessuna matematica: fase di infrastruttura e verifica documentale. Le due
affermazioni fattuali su cui poggia sono entrambe ri-controllabili:

```
# la doc non enumera i marketType: 2 sole occorrenze, entrambe come esempio
grep -rho "MATCH_ODDS\|OVER_UNDER_25" docs/betfair_api/*.md | sort | uniq -c
#   2 MATCH_ODDS      (una nell'esempio di subscription, una in listMarketTypes)
#   1 OVER_UNDER_25   (nel NOSTRO README, non nel testo Betfair)

# ogni file dichiara la fonte
for f in docs/betfair_api/*.md; do grep -q "Fonte" "$f" || echo "SENZA FONTE: $f"; done
```

## Fase 111 — Il token, i vincoli veri, e cosa possiamo davvero farci con Betfair

**Obiettivo.** L'utente ha chiesto aiuto per creare il proprio token e —
soprattutto — di capire «che tipo di lavoro possiamo fare con Betfair».

**Tre fatti che cambiano il piano, tutti letti nella documentazione ora
specchiata in `docs/betfair_api/` (Fase 110) e verificati dove possibile.**

1. **Per il servizio storico non serve una Application Key.** Vuole solo
   l'header `ssoid`, e la via più rapida per averlo è **copiare il cookie
   `ssoid` dal browser** dopo il login — la documentazione di supporto Betfair
   indica proprio questa. La strada "seria" (App Key + login via API su
   `identitysso.betfair.it`) serve solo se si automatizza.

2. **⚠️ Sull'exchange italiano la sessione dura 20 MINUTI**, contro 12-24 ore
   sul `.com`. E, testuale: «*Session times aren't determined or extended based
   on API activity*» — scaricare **non** tiene viva la sessione. Un download
   di qualche migliaio di file sarebbe morto a metà, e la causa sarebbe stata
   difficile da diagnosticare (errori sparsi, non un fallimento pulito).
   `fetch_betfair_historic.py` ora chiama `keepAlive` ogni 10 minuti, con
   l'endpoint della giurisdizione giusta (`--jurisdiction`, default `it`).

3. **L'exchange italiano è una licenza separata** (registrazione e login su
   `.it`), mentre il servizio storico è `.com`: **se un account italiano vi
   abbia accesso non è documentato**, e da qui non è verificabile (403 per
   regione). È la domanda da porre all'assistenza — con il test pratico
   equivalente già pronto: `--check` elenca i pacchetti, e se ne elenca,
   l'accesso c'è.

**Cosa possiamo farci, in ordine di valore** (dettaglio in
`docs/betfair_api/99_guida_pratica_progetto.md`):

- **A. Il buco O/U 2017-19**: il bersaglio dichiarato, e Betfair è l'unico
  candidato mai trovato *migliore della stima* (Fase 109).
- **B. La traiettoria delle quote**: istantanee ogni minuto → un asse di dati
  che `newseason.md` dà per **non recuperabile** e «mai avuto a nessuna
  scala». Non è un di più: la Fase 93 ha localizzato il nostro deficit nelle
  partite equilibrate di fine stagione e la Fase 98 ha trovato correlazione
  +0.43 col deficit dell'apertura — la traiettoria dice **quando** il mercato
  impara, che è la misura mancante a quella diagnosi.
- **C. Validare i ~17 mercati mai controllati**: il progetto prezza GG/NG,
  risultato esatto, multigol, total-squadra… e per sua stessa ammissione
  (Fase 88) **l'handicap asiatico è l'unico mai validato contro una quota
  esterna**. Betfair quota molti di quei mercati — ma **quali ci siano nei
  pacchetti storici va verificato con `--dry-run`, non assunto** (lezione
  della Fase 110 sul marketType non documentato). Per questo lo script ha ora
  `--market-type`: se ci sono, si scaricano senza scrivere altro codice.
- **D. Volume/liquidità** (piani a pagamento): segnale mai avuto, valore non
  misurato → non si compra prima di aver esaurito il BASIC gratuito.
- **E. Il test prospettico 2026-27**: possibile, ma frenato dal geo-blocco e
  dalla sessione da 20 minuti; da valutare dopo A e B.

**Un limite dichiarato, per non fare confusione.** Le API di scommessa sono
nella copia per completezza, ma il progetto **non piazza scommesse**: il
modello non batte il mercato, e Betfair qui è una **fonte di dati**, non un
canale operativo.

**Lezione.** Il lavoro utile di questa fase non è stato "creare il token": è
stato scoprire i **due vincoli che avrebbero fatto fallire il download in
modo confuso** (sessione da 20 minuti; accesso dell'account italiano non
documentato). Erano entrambi nella documentazione, a portata di `grep`, solo
perché la fase precedente l'aveva portata in casa — il ritorno dell'aver
specchiato invece di ri-cercare sul web ogni volta.

### 📐 Il modello in dettaglio

Nessuna matematica: fase operativa e di pianificazione. I due numeri citati
sono verificabili nella copia locale:

```
grep -i "20 minutes\|12 hours" docs/betfair_api/10_accesso__login_session_management.md
grep -i "aren't determined or extended" docs/betfair_api/10_accesso__login_session_management.md
```

## Fase 112 — Un solo scarico per due piste (e un refactor che un test ha bocciato)

**Obiettivo.** L'utente ha chiesto se si potesse già procedere con le piste A
(buco O/U 2017-19) e B (traiettoria delle quote), e se potessi farlo da solo.

**La risposta onesta sul "da solo": no, e non con una VPN.** Il blocco su
`historicdata.betfair.com` è **geografico e regolatorio** (le licenze di
scommessa sono per giurisdizione), non un ostacolo tecnico da aggirare — e
aggirarlo esporrebbe l'utente a un rischio concreto: un accesso al suo account
da un IP estero è esattamente il «traffico inusuale» che Betfair segnala e che
può far limitare l'account. Lo scarico gira sulla sua macchina; il resto
(validazione, join, analisi) qui.

**Ma c'era una cosa da fare PRIMA dello scarico, ed è il punto della fase.**
I file `.bz2` contengono **sia la chiusura sia tutta la traiettoria
pre-partita**, e il parser della Fase 109 teneva solo la chiusura, buttando il
resto. Chi avesse scaricato in quel momento avrebbe ottenuto A e perso B — per
poi dover **ri-scaricare tutto** il giorno in cui la traiettoria fosse
servita. Riscritto: `_serie_from_stream` estrae la serie completa, e la
chiusura ne diventa un caso particolare — così le due definizioni non possono
divergere. Un solo scarico, due piste.

**Il refactor è stato bocciato da un test, ed è la parte interessante.**
Derivando la chiusura come «ultimo punto della serie», il caso limite
dell'immagine finale che lascia prezzato **un solo lato** cambiava
comportamento: prima la riga veniva scartata (non esiste una chiusura valida),
dopo ripiegava sull'ultimo punto completo — cioè **spacciava per chiusura un
prezzo di minuti prima**. Un «finto pieno» (R6) plausibile e invisibile.
`test_img_sostituisce_la_cache_non_la_fonde` — scritto due fasi fa per un
altro motivo — l'ha intercettato. La distinzione è ora esplicita nel codice:
la **serie** raccoglie i punti completi osservati, lo **stato finale** è cosa
c'era all'istante della chiusura, e sono due cose diverse.

**Verifica end-to-end.** Simulato l'intero flusso con la rete finta: chiusura
1.92/1.95 (ultimo prezzo pre-via), traiettoria a −120/−60/−10 minuti, prezzo
in-play escluso, `minuti_al_via` corretto, tre file scritti (chiusure,
traiettoria gzippata, manifest). 5 test nuovi, **883 verdi**.

**Lezione.** «Posso farlo da solo?» aveva due risposte, e quella utile non era
la prima. No allo scarico — ma il lavoro che rende quello scarico *definitivo*
invece che da rifare si poteva fare subito, e andava fatto **prima**, non
dopo. Il costo di scoprirlo dopo non sarebbe stato un bug: sarebbe stato
chiedere all'utente di rifare tutto.

### 📐 Il modello in dettaglio

Nessuna matematica nuova. L'unica formula introdotta è l'asse su cui si legge
la traiettoria:

```
minuti_al_via = (marketTime − pt) / 60000        # pt e marketTime in ms
# positivo = prima del calcio d'inizio; 0 = al via
```

`marketTime` è l'orario **programmato** e `pt` l'istante di pubblicazione del
prezzo. Il taglio della serie però NON usa questa differenza: usa il flag
`inPlay` (Fase 109-bis), perché una partita iniziata in ritardo ha una
chiusura più tarda dell'orario da calendario — e usare l'orario programmato
includerebbe prezzi già in-play, cioè look-ahead.

## Fase 113 — «Quanto serve davvero?» — il ridimensionamento di una mia raccomandazione

**Obiettivo.** Domanda dell'utente prima di mettersi a scaricare: quanto serve
davvero questo sforzo, e quali dati otterremmo che non possiamo avere altrove.
Domanda legittima e mai posta in questi termini: la Fase 109 aveva stabilito
che Betfair è *migliore della stima*, ma nessuno aveva verificato **a cosa
serva** quella stima.

**Tre verifiche, tutte a portata di `grep`, tutte mai fatte.**

1. **La stima non alimenta nulla.** `read_ou_close_estimates()` è chiamata
   **solo da `tests/test_estimates.py`**: nessun modello, nessun backtest la
   consuma. I backtest ufficiali girano su 2020-21 → 2025-26, stagioni che
   hanno tutte la chiusura O/U reale. **Il buco 2017-19 non tocca un solo
   risultato pubblicato.**

2. **Il costo vero del buco è un altro**: 3.652 partite (22,7%) hanno la
   chiusura 1X2 ma non quella O/U, e senza entrambe il motore market-implied
   — il titolare — non può girare. Il guadagno non è «un dato più preciso
   della stima»: è **due stagioni da inutilizzabili a utilizzabili**. Sono
   però le due più vecchie, le meno rappresentative.

3. **Una fetta grossa del valore era già in casa, gratis.** `football-data`
   pubblica **20 colonne Betfair Exchange** per 2024-25 e 2025-26 — 1X2, O/U
   2.5, handicap asiatico, apertura *e* chiusura — su **3.393 partite,
   copertura 96,8%**. Mai usate. Misurato: il 1X2 di chiusura Betfair fa
   **0.9676** di log-loss contro **0.9682** della media multi-book
   (Δ −0.00060, IC95 [−0.00154, +0.00041], P 87.9%, **non conclusivo**),
   overround 1.0055 contro 1.0531. Betfair vale poco più della media dei book
   come *fonte*: il suo pregio è l'**indipendenza**, non la precisione.

**Conseguenza.** L'ordine dei lavori si inverte: prima le colonne gratuite
(costo zero per l'utente, stagioni più rilevanti), poi — solo se lì emerge
qualcosa — lo scarico storico. Che resta l'unica via per **due** cose davvero
introvabili altrove: la **traiettoria minuto per minuto** e i **mercati oltre
1X2/O-U/handicap**. Non per il buco O/U in sé.

**Ridimensionata anche la pista B, non solo la A.** La Fase 98 ha già
misurato il movimento apertura→chiusura: **non anticipabile** (β −0.0039,
R² 0.0001) e CLV negativo conclusivo. La traiettoria non rovescia quel
risultato — risponde a una domanda **diversa** (*quando* il mercato impara,
non *se* possiamo anticiparlo), utile per **attribuire** il gap, non per
chiuderlo.

**Lezione, ed è su di me.** Alla Fase 109 ho scritto che questa era la pista
che «merita di essere percorsa», e il numero su cui poggiava (MAE 0.0060 vs
~0.014) era corretto. Sbagliata era la conclusione, perché mancavano due
controlli banali: **chi usa il dato che vorremmo sostituire** (nessuno) e
**cosa abbiamo già** (due stagioni di Betfair gratis, mai toccate). Misurare
bene una cosa non basta a stabilire che serva: il valore di un dato non sta
nella sua qualità, sta in **cosa cambierebbe averlo**. È la stessa forma
dell'errore della Fase 108 — un'analogia al posto di una misura — ma un
gradino più su: qui la misura c'era, mancava la domanda giusta.

### 📐 Il modello in dettaglio

Nessuna matematica nuova: stesso devig e stesso log-loss delle fasi
precedenti, applicati a una colonna mai usata.

```
p(esito) = (1/quota) / somma(1/quota)          # devig moltiplicativo, 1X2
LL       = −mean( log p(esito realizzato) )
```

I due numeri della fase sono ri-ottenibili così:

```
# la stima non e' consumata da nulla
grep -rn "read_ou_close_estimates" --include=*.py . | grep -v "def read_ou"
#   -> solo tests/test_estimates.py

# quante partite bloccano il market-implied
python3 -c "
import pandas as pd, glob
b=sum(((d[['odds_home','odds_draw','odds_away']].notna().all(axis=1)) &
       (~d[['odds_over25','odds_under25']].notna().all(axis=1))).sum()
      for d in map(pd.read_csv, glob.glob('data/*_matches.csv')))
print(b)"   # -> 3652
```

## Fase 114 — Far usare le stime davvero (e una mia frase da correggere)

**Obiettivo.** Richiesta dell'utente: «abbiamo tanti dati e tante stime,
vorrei che fossero usati tutti almeno in un modello o da qualche parte».

**Prima l'inventario, perché la premessa andava verificata.** Controllate
tutte e 38 le colonne dello snapshot, una per una, contro `src/` e `scripts/`:
**nessuna è inutilizzata**. Il primo tentativo di conteggio diceva il
contrario (4 colonne «mai usate») ed era un **artefatto della mia regex**, che
spezzava i nomi contenenti cifre — `odds_over25` diventava `odds_over` + `25`.
Il dato grezzo, quindi, non è sprecato.

**La rettifica.** Alla Fase 113 avevo scritto che la stima O/U «non alimenta
nulla». Troppo netto: è vero che la *funzione* `read_ou_close_estimates()` è
chiamata solo da un test, ma il CSV è letto direttamente da
`_run_fase75_squeeze_2017_19.py` — che su quella stima ha costruito
un'analisi vera («apertura REALE + chiusura STIMATA») — e da
`verifica_stime.py`, che la valida. Il fatto esatto è più preciso e meno
sensazionale: la stima **non era una via di prima classe**, e chi la voleva
si faceva il join a mano.

**Cosa ho fatto**: `loader.ou_close_probability()`. Restituisce P(Over 2.5) di
chiusura per ogni partita **con la provenienza dichiarata riga per riga**
(`reale` / `stima` / `assente`). Copertura sulle 5 leghe: 12.459 reale +
3.638 stima + 14 assente = **99,9%**. Per il motore market-implied — che
senza chiusura O/U non gira — significa passare da **12.459 a 16.097 partite
utilizzabili (+29%)**: il 2017-18 e il 2018-19 smettono di essere ciechi per
il titolare.

**Il vincolo che rendeva la cosa non banale.** Il progetto tiene
deliberatamente separati prezzo e stima: le stime vivono come
**probabilità**, mai come quote, mai dentro gli snapshot (§5). Una funzione
che «riempie i buchi» è esattamente il posto dove quella separazione si perde
per distrazione. Per questo: le colonne quota **non vengono toccate** (un test
lo verifica, ed è **confermato per mutazione** — scrivendo la stima in
`odds_over25` il test fallisce), ogni riga porta la sua provenienza, e
`usa_stime=False` restituisce il buco vero invece della ricostruzione. 6 test
nuovi, **889 verdi**.

**Cosa NON ho fatto, e perché.** L'utente chiedeva che *tutti* i dati fossero
usati «almeno in un modello». Molte covariate (`rest_full`, `midweek_europe`,
`squad_value`, `npxg`, `ppda`, `deep`, assenze) **sono** usate: sono state
misurate e trovate rumore, e stanno in panchina con i numeri del verdetto in
`docs/PANCHINA.md`. Accenderle per non lasciarle inutilizzate sarebbe il
contrario del metodo: un dato testato e scartato **è** un dato usato. La
differenza che contava era un'altra — un dato *valido ma non raggiungibile*,
ed era solo la stima.

**Lezione.** «Usare tutti i dati» non vuol dire metterli tutti in un modello:
vuol dire che nessuno sia **irraggiungibile per attrito**. Qui il problema non
era il valore della stima (misurato da tempo), era che per usarla servivano
venti righe di join che ogni analisi doveva riscriversi — e infatti in due
anni l'ha fatto una sola.

### 📐 Il modello in dettaglio

Nessuna matematica nuova: la probabilità reale è il **devig binario** già in
uso (`metrics.devig_binary`), la stima è quella della Fase 62-bis, presa così
com'è.

```
# dove il mercato c'e' (fonte = "reale")
p_over = (1/quota_over) / (1/quota_over + 1/quota_under)

# dove non c'e' (fonte = "stima"): p_over25_close_est della Fase 62-bis,
#   gia' una probabilita' -> nessuna trasformazione, nessun devig
# altrove: NaN, fonte = "assente"
```

**Perché la stima non passa per un devig.** È già una probabilità devigata per
costruzione (la Fase 62-bis stima P(Over), non una coppia di quote):
"devigarla" significherebbe applicare due volte la stessa normalizzazione. È
anche il motivo per cui non si può scrivere nella colonna quota senza
inventare un overround che nessuno ha osservato — la regola di
`data/estimates/README.md` non è una formalità, è questo.

## Fase 115 — «Serve un PC cloud 24/7?» — no: la borsa che serviva era già in casa

**Obiettivo.** Domanda dell'utente: cosa possiamo inventarci per superare i
blocchi — un PC cloud sempre acceso? e quanto costerebbe?

**La prima risposta: il muro di Betfair non è tecnico né economico, è
contrattuale.** Dalla documentazione ufficiale: App Key **Delayed** gratuita
ma «for **development** purposes» (dati conflati a 180 s); App Key **Live**
**£499** una tantum, e testuale «**Read-only access via the Live App Key
isn't permitted**». La raccolta dati pura sul feed live **non è un uso
previsto a nessun prezzo** — e siccome il progetto non scommette (§5), non
potrebbe soddisfare l'aspettativa nemmeno volendo. Un raccoglitore 24/7 su un
account che non scommette rischia la **limitazione dell'account**: un danno
reale all'utente. Nessun VPS risolve un vincolo di questo tipo. *(Resta
legittimo il servizio **storico**: lì distribuire dati è lo scopo del
servizio, e le piste A/B non sono toccate.)*

**La seconda risposta, che vale più della prima: la soluzione era già in
casa.** **Smarkets** è una borsa con API **pubblica, senza chiave, senza
account**, e **raggiungibile da questo ambiente**. Il progetto la usa dalla
Fase 97 — ma **solo per gli outright**. Nessuno aveva mai guardato i mercati
per singola partita. Sondata:

- **100 mercati per partita**: 1X2, **risultato esatto**, **GG/NG**, O/U da
  0.5 a 6.5, combinati…
- **`bids`/`offers`** = **banco e puntatore**, con le **quantità**
  (liquidità) — su Betfair il ladder e il volume sono nei piani **a
  pagamento**;
- margine quasi nullo: la somma dei prezzi medi fa **100.48%**.

Letto dall'API su una partita vera: Under 2.5 banco 50.25% / puntatore
66.23%; Over 2.5 banco 34.48% / puntatore 50.00%; spread 15.98 punti;
liquidità 88.663 unità.

**Cioè dà gratis le due cose che alla Fase 111 avevo dichiarato
irraggiungibili** (lo spread banco/puntatore e il volume), e apre la **pista
C** — validare risultato esatto, GG/NG e le linee O/U contro un mercato vero,
quando finora solo l'handicap asiatico era mai stato confrontato con una
quota esterna (Fase 88).

**Il costo.** Smarkets + i **3 workflow GitHub Actions già nel repo**: **€0**.
Un VPS europeo (Hetzner ~€4/mese, Aruba ~€6) servirebbe solo se Actions non
bastasse. Betfair Live: £499 e comunque non applicabile.

**Il limite dichiarato.** Smarkets **non ha storico**: raccoglie in avanti,
non all'indietro. Non sostituisce lo scarico Betfair per il 2017-19 — sono due
problemi diversi (all'indietro: Betfair storico dalla macchina dell'utente; in
avanti: Smarkets da qui). **E ha una scadenza**: la stagione comincia il **16
agosto**, e ogni giorno senza raccoglitore è dato perso per sempre.

**Lezione.** La domanda era «come aggiriamo il muro, e quanto costa». La
risposta utile non stava nel superare il muro — stava nel **verificare se
servisse davvero passare di lì**. Una fonte già integrata nel progetto da
diciotto fasi copriva un'esigenza che non le era mai stata chiesta, perché era
entrata per un altro scopo (gli outright) e nessuno aveva riaperto la domanda
«**cos'altro sa fare?**». Prima di comprare infrastruttura per aggirare un
limite, conviene inventariare cosa si ha già.

### 📐 Il modello in dettaglio

Nessuna matematica nuova; una **conversione** da fissare, perché Smarkets non
usa quote decimali:

```
prezzo Smarkets = probabilita' x 10.000        # 5025 -> 50.25%
p_back  = bid  / 10000        p_lay = offer / 10000
p_mid   = (bid + offer) / 20000                # stima centrale, spread neutralizzato
spread  = (offer - bid) / 10000                # ampiezza del book: proxy di (il)liquidita'
```

**Perché il prezzo medio e non il lato del banco.** Su una borsa i due lati
sono i limiti di un intervallo, non due prezzi alternativi: il banco
sovrastima e il puntatore sottostima la probabilità della stessa proposizione.
La somma dei **medi** fa 100.48% — cioè il punto medio è già quasi una
probabilità normalizzata, e il devig serve solo a togliere quello 0.48%. Sui
lati grezzi invece la somma fa 84.73% (banco) e 116.23% (puntatore): usarne
uno solo introdurrebbe un bias sistematico di segno noto, non un rumore.

## Fase 116 — Il raccoglitore prospettico è in piedi (e costa zero)

**Obiettivo.** Costruire il raccoglitore Smarkets deciso alla Fase 115, prima
del **16 agosto**: ciò che non si raccoglie prima del calcio d'inizio è perso
per sempre, e il test prospettico della Fase 78 è il gold standard che il
progetto non ha mai potuto eseguire.

**Cosa c'è.** `scripts/fetch_smarkets_matches.py` +
`.github/workflows/smarkets-prematch.yml` (ogni 6 ore, dentro il piano
gratuito). Il client HTTP e la lettura del libro ordini sono **riusati** da
`fetch_smarkets_outrights.py` (Fase 97): stesso throttle, stessa gestione del
429, stesso `book_price`. Duplicarli avrebbe voluto dire due comportamenti da
tenere allineati a mano.

**Verificato dal vivo, non solo scritto.** Tutte e 5 le leghe hanno già il
calendario 2026-27 su Smarkets; la prima raccolta reale ha prodotto **180
righe su 6 partite** (La Liga, 15-17 agosto) con i 6 mercati del listino —
1X2, GG/NG, O/U 1.5/2.5/3.5 e **risultato esatto**. Controllo di coerenza: i
prezzi medi dei due lati sommano a **0.994-1.003**, cioè il punto medio è già
una probabilità quasi normalizzata. Libro a due lati sul **59%** delle righe
(il resto è risultato esatto, sottile a tre settimane dal via: atteso, e
marcato riga per riga con `lato`).

**La correzione, ed è su un test.** Avevo scritto che il confronto esatto
sullo slug difende dal caso `germany-2-bundesliga` scambiato per
`germany-bundesliga`. **Falso**: quella collisione è *strutturalmente
impossibile* — il «2-» sta in mezzo, quindi nemmeno un match «contiene» la
produce — e la mutazione corrispondente **non faceva fallire nulla**. Ho
corretto la motivazione nel test e nel codice invece di lasciare scritta una
protezione inesistente, e ho cercato la mutazione che i test **catturano
davvero**: corrompendo una voce della mappa delle leghe, 2 test falliscono.
Ciò che quei test proteggono è il **contratto con un'API esterna** (uno slug
rinominato a valle rompe la suite invece di farci raccogliere in silenzio la
lega sbagliata), non una collisione fantasma.

**Costo: zero.** API pubblica senza chiave né account, GitHub Actions nel
piano gratuito, nessun VPS, nessun rischio per l'account di nessuno. 13 test
nuovi, **906 verdi**.

**Il limite dichiarato.** Si raccoglie **in avanti**: questo non sostituisce
lo scarico Betfair storico per il 2017-19, che resta un problema diverso e sulla
macchina dell'utente. E il valore cresce con il tempo di accensione — il primo
file è già un dato che fra un mese non sarebbe più ottenibile.

**Lezione.** La parte lunga non è stata scrivere il raccoglitore (riusa quasi
tutto), ma **verificare che i test avessero denti**. Un test che passa sempre
— anche quando rompi il codice che dice di proteggere — è peggio di nessun
test: dà una garanzia che non c'è. La mutazione va cercata *finché non ne
trovi una che fallisce*; se non la trovi, il rischio che avevi in mente non
esiste, e allora va riscritta la motivazione, non lasciata lì perché suona
bene.

### 📐 Il modello in dettaglio

Nessuna matematica nuova; la conversione dei prezzi è quella fissata alla
Fase 115 e implementata in `book_price` (Fase 97):

```
p_banco     = bid   / 10000        # Smarkets: interi in centesimi di punto %
p_puntatore = offer / 10000
p_mid       = (bid + offer) / 20000
spread      = (offer − bid) / 10000
```

**Il controllo che rende leggibile il dato**: su una coppia complementare
(Over/Under della stessa linea) la somma dei `p_mid` deve stare a ~1. Misurato
sulle 6 partite reali: **0.9941 – 1.0030**. Se un giorno quella somma si
allontanasse, vorrebbe dire che stiamo leggendo lati diversi di libri diversi
— ed è un controllo che costa una riga e si può rifare su ogni file raccolto.

---

## Fase 117 — Ogni file allineato: il merge con una sessione parallela, e l'identità che chiude la COM-Poisson

**Obiettivo (utente).** «Voglio che ogni file sia sempre aggiornato: procedi
aggiornando ogni singolo file con le ultime analisi/calcoli/studi svolti. Se
serve, riorganizza anche ciò che secondo te è disordinato.» Prima ancora,
nella stessa sessione: un resoconto dei branch, e la caccia ai riferimenti
scaduti — link morti e affermazioni non più vere.

**Ragionamento / ipotesi.** Un repo che documenta sé stesso accumula un debito
particolare: non righe di codice sbagliate, ma **frasi vere quando furono
scritte**. Nessun test le prende, nessun lettore le smentisce, e restano. La
Fase 101 ne aveva censite a decine e lasciato aperti due punti espliciti
(«PANCHINA: 18 celle già misurate», «documenti da rinfrescare»). L'ipotesi di
lavoro: il difetto non è distribuito a caso ma **si concentra nei file-indice**
— quelli che riassumono altri file — perché sono gli unici che nessuno rilegge
quando cambia la cosa riassunta.

### Risultato 1 — i branch: nulla da recuperare

Verificato con `git merge-base --is-ancestor`: i tre branch `claude/…` rimasti
su `origin` sono **tutti antenati di `main`**, zero commit avanti. L'unica
differenza di superficie è la cartella `cantiere/` del branch
`verify-data-import-leagues-468euv`, assente da `main` — ma il commit `6c9b377`
mostra che è uno **spostamento tracciato da git** (script → `scripts/`, report →
`docs/audit_5_leghe/`), non una cancellazione. Restano fuori solo download
grezzi e log di scratch. Il `CLAUDE.md` §3-bis diceva già la cosa giusta.

### Risultato 2 — tre affermazioni di rete scadute, e un solo modo di scoprirle

Il `MANUALE_SOPRAVVIVENZA.md` è il registro di ciò che è raggiungibile, e
dichiarava bloccati da proxy `huggingface.co`, `datasets-server.huggingface.co`
e `data.jsdelivr.com`. **Ri-testati con `curl`: rispondono 200 con contenuto
reale.** Per `jsdelivr` l'audit della Fase 100/101 l'aveva perfino già notato,
senza correggere la tabella.

La lezione non è «la rete è cambiata» — è che **una tabella di stato va
ri-eseguita, non riletta**. Un'affermazione di raggiungibilità è l'unico tipo
di fatto in questo repo che si può verificare in un secondo, e per mesi nessuno
l'ha fatto. Da cui anche la distinzione che è entrata nel manuale: un **timeout
(`000`) non è un `403`** — sono cause diverse, e trattarle uguale è ciò che
aveva prodotto la voce sbagliata su `pub-*.r2.dev` (oggi: un bucket generico
risponde 401, cioè la richiesta *esce* dal proxy → l'etichetta «bloccato» non è
più dimostrata).

Stessa forma nel `experiments/prospettico_2026_27.md`, che dichiarava «`WebFetch`
è bloccato del tutto» — smentito dalla Fase 100, che da Wikipedia aveva
recuperato 3.045 righe di calendario. Era l'ultimo dei cinque documenti del
rilievo `F9-rete-tornata-non-propagata` a non essere stato sistemato.

### Risultato 3 — una fase fantasma, di nuovo

La **Fase 101-bis** aveva una riga nel registro del README e le sue rettifiche
sparse come note dentro le fasi corrette, ma **nessuna voce nel diario**. È
esattamente il difetto che l'audit della Fase 101 aveva rimproverato alla Fase
92-bis — e per il quale «top-4 batte la persistenza, entrambi conclusivi» era
sopravvissuto nove fasi a un IC che includeva lo zero. Ripetuto a due fasi di
distanza, dallo stesso audit che l'aveva diagnosticato.

Voce ricostruita (sopra) dalle fonti contemporanee. E il diario ha ora un
**Arco 12** nell'indice: le Fasi 100+ erano appese in coda all'Arco 11,
intitolato «Fasi 89–99».

### Risultato 4 — la COM-Poisson: da coincidenza numerica a identità

È il solo risultato di questa fase che aggiunge **matematica** invece di
allineare prosa, ed è il blocco 📐 qui sotto. La Fase 101-bis aveva stabilito
che la COM-Poisson della Fase 85 «è la double-Poisson riparametrizzata» sulla
base di un accordo numerico (≤5e-06 sull'exact-score log-loss). Un accordo a
5e-06 **non è una dimostrazione**: potrebbero essere due famiglie diverse che
quasi coincidono nel regime dei gol del calcio. È invece un'**identità esatta**,
e si vede in tre righe di algebra.

### Risultato 5 — il merge con una sessione parallela (il vero imprevisto)

A metà lavoro `git push` è stato rifiutato: **`origin/main` era avanti di 15
commit** — le Fasi 103-115, prodotte da un'altra sessione mentre questa girava
(il container di questa era stato sospeso per ~16 ore, e il workflow che
aggiornava i file è morto lì dentro senza completare la fase di verifica).

Sette file erano stati modificati da entrambe le sessioni; cinque hanno dato
conflitto. Nessuno era risolvibile «tenendo il più recente»: **entrambe le parti
avevano fatti veri e diversi**. Esempi:

| file | questa sessione | sessione parallela |
|---|---|---|
| `MANUALE` §1 | ri-test host per host del 28/07, `api.github.com` e `pub-*.r2.dev` rimisurati | betexplorer richiede UA da browser (F107), Understat è gzip sempre (F104), Betfair docs e Wayback raggiungibili (F105/109-bis) |
| `PANCHINA` | 18 celle `⬜` riempite coi numeri di Bundesliga e Ligue 1 | `rest_full` e `midweek_europe` ri-verificati sui dati corretti (F103) |
| `PISTE` §19 | la decisione scomposta in **due** motivi misurati (rottura di regime + proxy peggiore) | tre ri-tentativi negativi (F105/107/108) e il MAE **non stabile** su 6 stagioni (F106) |

Risolti a mano tenendo l'**unione dei fatti**, mai il più recente per default.
E il merge ha reso stantio un numero che questa sessione aveva appena scritto in
sei punti: i test non sono più 841 ma **889** (48 in più dalle Fasi 103-115).

**Conseguenza sulla numerazione, che è successa DUE volte.** Questa fase era
partita come «Fase 102», e le sue prime commit lo dicono; la sessione parallela
ha visto il 102 occupato ed è partita da 103, così la fase è diventata 116. Nel
tempo di scrivere questa voce, la stessa sessione ha pushato **la sua** Fase 116
(il raccoglitore Smarkets) — quindi questa è la **117**. Il **102 resta un
numero mai usato**, e il 116 è della fase precedente: dichiararlo qui costa due
righe e risparmia la prossima caccia. È anche la prova pratica del punto qui
sotto: con due sessioni sullo stesso `main`, il numero di fase non è un'identità
stabile finché non è pushato.

### 📐 Il modello in dettaglio

**L'identità dp ≡ COM-Poisson.** La double-Poisson di Efron come è implementata
(`src/models/market_implied.py`, `_dp_pmf`, righe 47-63), mean-preserving con
`c` risolto per bisezione perché la media resti `rate`:

```
q_k ∝ [ Poisson_k(c·rate) ]^θ = [ (c·rate)^k · e^(−c·rate) / k! ]^θ
```

Si sviluppa la potenza e si separa ciò che dipende da `k` da ciò che non dipende:

```
q_k ∝ (c·rate)^(θk) · e^(−θ·c·rate) / (k!)^θ
        \_________/   \____________/   \____/
         dipende da k   COSTANTE in k    (k!)^θ
```

Il fattore `e^(−θ·c·rate)` non dipende da `k`: **sparisce nella
rinormalizzazione**. Resta

```
q_k ∝ [ (c·rate)^θ ]^k / (k!)^θ
```

che è esattamente la COM-Poisson `P(k) ∝ λ^k / (k!)^ν` con

```
λ_COM = (c·rate)^θ        ν = θ
```

*Perché chiude la questione.* Non è «due modelli che danno numeri simili»: è
**un solo modello con due parametrizzazioni**, e la mappa fra le due è in forma
chiusa. Verificato eseguendo, sui tassi che il progetto usa davvero:
`max|dp − COM|` = **1.8e-14** a (rate 1.35, θ 1.225), **4.1e-14** a (0.90,
1.138), **1.2e-14** a (2.10, 1.18), **3.3e-15** a (1.00, 0.85) — precisione
macchina, tre ordini di grandezza più stringente del ≤5e-06 empirico, e vale
anche in **sovra-dispersione** (θ<1), dove nessuno aveva guardato. Un bakeoff
fra dp e COM-Poisson non può dare altro che pareggio: il ν della COM-Poisson
*è* il θ del router.

*Onestà su cosa NON è stato ri-derivato.* Tutti gli altri numeri toccati in
questa fase sono stati **spostati**, non ricalcolati: provengono dal registro
del README, dai JSON di `docs/audit_5_leghe/numeri/` o dal verbale dell'audit, e
il criterio applicato è stato «se non lo trovo in una fonte del repo, non lo
scrivo». Le uniche misure nuove sono l'identità qui sopra, i codici HTTP del
Risultato 2 e il conteggio dei test (`889`).

**Lezione.** Due, e sono la stessa vista da due lati. (1) **Un'affermazione di
stato va ri-eseguita, non riletta**: le tre voci di rete sbagliate costavano un
secondo di `curl` ciascuna e sono sopravvissute a due audit, perché un audit
legge. (2) **Il lavoro parallelo non si integra da solo, e la sua parte
pericolosa non sono i conflitti** — quelli git li segnala. Sono i file che si
fondono *puliti* mentre le due versioni raccontano storie diverse: nessun
marker, nessun test rosso, e il documento risultante è coerente solo in
apparenza. È lo stesso difetto della fase fantasma, alla scala del repo.

---

## Fase 118 — Il primo giro vero del raccoglitore: verde, e non raccoglieva niente

**Obiettivo.** Verificare che il raccoglitore della Fase 116 parta **da solo**.
Il cron era committato ma non era mai stato eseguito: fino a quel momento
«funziona» era una deduzione dal codice, non un fatto. Con una scadenza vera
(16 agosto) e un dato irrecuperabile, la deduzione non basta.

**Cosa è successo.** Primo run su GitHub Actions (`30383527812`): **verde in 23
secondi**, nessun file scritto. Lo step di raccolta è durato **3 secondi** —
in locale, con 6 partite, ne serviva un ordine di grandezza in più. Il log
diceva `partite delle 5 leghe entro 72h: 0`.

**Prima diagnosi: sbagliata.** Ho sospettato che Smarkets filtrasse gli IP dei
runner. Era falso, e la prova era già nel repo: i miei run locali della Fase
116 avevano usato `--entro-ore 500`, non 72. Oggi è il **28 luglio**: la prima
partita delle 5 leghe è il **15 agosto**, cioè fra 432 ore. Il codice aveva
fatto esattamente la cosa giusta. *(R5.1 — spiegare prima di accusare: la
spiegazione stava nel metadato del file, non in un blocco della fonte.)*

**Ma il run verde ha scoperchiato due difetti veri.**

**(1) Il raccoglitore non avrebbe raccolto NULLA fino al 12 agosto.** Con la
finestra a 72 ore, il primo giro utile sarebbe caduto tre giorni prima del via.
Nel frattempo il listino dell'esordio è **già quotato e già si muove**: misurato
il 28/07, Smarkets espone **48 partite** delle nostre 5 leghe (9-10 per lega,
dal 15 al 30 agosto). Diciotto giorni di traiettoria che `newseason.md` §2
classifica come irrecuperabili, persi per un valore di default.

**(2) «Finestra vuota» e «l'API non ci parla più» erano lo stesso esito.** Zero
righe, workflow verde, nessun errore. Se Smarkets rinominasse uno slug di
competizione — e il commento nel codice diceva già che il confronto esatto
serve a proteggere *quel* contratto — raccoglieremmo il nulla per mesi senza
accorgercene. È il **finto pieno** della regola R6 applicato a un processo
invece che a una cella: un verde che significa «tutto a posto» e invece
significa «non lo so».

**Le due correzioni.** Un regime di **lungo raggio** (`--tutte-le-esposte
--solo-principali`, un giro al giorno) che prende tutto ciò che l'API espone ma
solo sui mercati che il motore consuma; e un **controllo di plausibilità del
listino** che fa fallire il giro invece di uscire verde. In più i secondi nel
nome del file: due regimi nello stesso minuto si sarebbero sovrascritti in
silenzio.

**La regola è misurata, non assunta.** Il 28 luglio — il punto più profondo
dell'off-season, nessuna delle 5 leghe in campo prima di tre settimane — il
listino esponeva **709 eventi calcio su 101 competizioni**, e tutte e 5 le
nostre erano presenti con 9-10 partite. Quindi «zero partite nostre in un
listino non vuoto» non è uno stato che l'off-season produce: è un'anomalia. È
la differenza fra una soglia inventata e una soglia con una misura dietro.

**Risultato.** Primo file di lungo raggio: **336 righe su 48 partite**, tutte e
5 le leghe, 7 righe per partita (1X2 + O/U 2.5 + GG/NG), **149 KB**. Libro a
due lati sull'**85%** delle righe; somma dei complementari mediana **1.0034**
(O/U 2.5), **1.0030** (GG/NG), **1.0040** (1X2) — l'overround quasi nullo di
una borsa. Le 49 righe senza libro sono marcate una per una, non riempite.
Quattro mutazioni provate sul codice nuovo, **quattro catturate** dal test
inteso.

**📐 Il modello in dettaglio.**

Non c'è matematica nuova: ci sono due regole di decisione, e il punto è il
*perché* delle loro soglie. Verificate riga per riga contro
`scripts/fetch_smarkets_matches.py`.

*(a) Plausibilità del listino* — `anomalia_del_listino(E, N)`, con `E` = eventi
calcio futuri visti in tutto e `N` = quanti appartengono alle nostre 5 leghe:

```
anomalia(E, N) = "listino vuoto"       se E = 0
               = "slug non trovati"    se E > 0 e N = 0
               = None (tutto bene)     altrimenti
```

Perché queste due e non una soglia numerica: sono gli unici due stati che **non
possono** essere prodotti dal calendario. `E = 0` significa che da nessuna parte
al mondo si gioca — mai vero. `N = 0` con `E > 0` significa che gli slug attesi
non compaiono; e che non sia l'off-season a produrlo è **misurato** il
28/07/2026 (`E = 709`, `N = 48`, nel giorno più vuoto dell'anno). Nessuna soglia
su «quante partite ci aspettiamo»: sarebbe stata una costante inventata, e
avrebbe suonato falsi allarmi durante le soste.

*(b) Finestra temporale* — `entro_finestra(S, h)`:

```
entro_finestra(S, h) = S                                      se h ≤ 0
                     = { e ∈ S : inizio(e) ≤ adesso + h }     se h > 0
```

`h ≤ 0` è il regime di lungo raggio (`--tutte-le-esposte` passa 0). Il confronto
è `≤`, non `<`: una partita che dista esattamente `h` deve entrare, altrimenti
due giri consecutivi a distanza `h` la perderebbero in modo intermittente —
difetto invisibile in un test a valori tondi, coperto da
`test_il_bordo_della_finestra_e_incluso`.

*(c) Perché il lungo raggio esclude il risultato esatto.* Non è una scelta di
gusto, è aritmetica di archivio. Dal file misurato: 149 KB / 336 righe = **454
byte per riga**. Con i 6 mercati del listino le righe per partita sono **30**
(la Fase 116 misurò 180 righe / 6 partite), di cui ~24 di solo risultato esatto;
con i 3 principali sono **7**. Quindi:

```
lungo raggio, 1 giro/giorno:  48 × 7  × 454 B ≈ 149 KB/giorno ≈ 45 MB/stagione
stesso giro con tutti i mercati: 48 × 30 × 454 B ≈ 640 KB/giorno ≈ 190 MB
```

Il fattore ~4.3 è tutto risultato esatto — un mercato che a tre settimane dal
via è sottile (Fase 116: libro a due lati sul 59% delle righe, contro l'85% di
oggi sui principali) e che il **regime denso** raccoglie comunque quando conta,
cioè vicino al calcio d'inizio. Si paga dove il dato è informativo, non dove è
rumore.

**Il costo dichiarato, perché non resti una sorpresa.** Il regime denso
in-season è la voce pesante: ~35 partite in finestra in un fine settimana × 30
righe × 454 B ≈ 480 KB a giro, per 4 giri al giorno. Su una stagione l'archivio
sta nell'ordine dei **250-300 MB** versionati. È il prezzo di un dato che non si
può ricomprare, ma è una cifra che va **decisa**, non subita: le due leve sono
la frequenza del cron e l'esclusione del risultato esatto anche dal denso.

**Lezione.** *Un processo automatico verde non è un processo che funziona: è un
processo che non ha protestato.* Il run era verde, il codice era corretto, e
insieme non stavano facendo il lavoro. La verifica che conta non è «il job
passa» ma «il job ha prodotto il dato che doveva» — e va guardata **la prima
volta**, quando c'è ancora tempo per rimediare, non alla fine della stagione
quando il dato mancante non si recupera più. La regola R6 diceva già che il
buco peggiore è il finto pieno; questa fase aggiunge che il finto pieno può
essere un *file che non esiste*, non solo un valore sbagliato.

---

## Fase 119 — La raccolta quotidiana 2026-27: il piano, e i due `robots.txt` che lo riscrivono

**Obiettivo.** Richiesta dell'utente: una raccolta dati **completa e
quotidiana** per la nuova stagione — obiettivi, rose con valori, competizioni,
e ogni giorno le notizie (umore, probabili formazioni, allenatore a rischio,
meteo, diffidati, convocazioni…). Con una cartella stagionale e un README che
dica cosa vogliamo.

**Ragionamento.** Un piano che elenca fonti senza averle provate è carta. Prima
ho **misurato**: 21 sondate, 15 rispondono. Ma il numero che conta non era
quello.

**La scoperta che riscrive il piano.** Leggendo i `robots.txt` (regola R5.3):
**la maggior parte della stampa sportiva vieta esplicitamente i crawler AI**.
`transfermarkt.it`, `gazzetta.it`, `bbc.co.uk`, `kicker.de` dichiarano
`Disallow: /` per `ClaudeBot`/`anthropic-ai`; `marca.com` per `anthropic-ai`.
Consentiti: **Guardian** (presente con **zero** regole, cioè permesso
esplicito), Lega Serie A, open-meteo, Wikipedia, football-data.org.

Non è un 403 da aggirare: è una volontà dichiarata. Conseguenza accettata: il
livello «notizie» **non** può poggiare sullo scraping della stampa sportiva.
Restano le fonti che ci consentono, le API su licenza, e la ricerca web dentro
una routine — che è una ricerca, non un crawl di massa. Rose e valori: la via è
la raccolta **manuale** dell'utente, già prevista dalla regola R2.

**Cosa è stato creato.** `data/stagione_2026_2027/` con la specifica completa.
Tre decisioni di struttura che vale la pena estrarre:

1. **Fatto ≠ giudizio.** Metà di ciò che si vuole raccogliere (umore,
   allenatore a rischio, lettura tattica) non è una misura: è un giudizio
   prodotto leggendo notizie. Ogni record porta `tipo`, e un giudizio senza
   **evidenza citata** non si scrive: si scrive «non lo so». È la R6 applicata
   prima che il dato nasca, invece che a posteriori.
2. **Due assi ortogonali.** L'utente chiedeva «file al giorno *o* cartella per
   squadra?». Servono entrambi, perché rispondono a domande diverse:
   `giornaliero/` è **append-only e immutabile** e risponde a «che cosa
   sapevamo il giorno D?»; `club/` è l'identità stabile più viste
   **rigenerabili**. Se lo stato vivesse solo in un file sovrascritto, a maggio
   non sapremmo più cosa sapevamo ad agosto — e con quello muore il test
   prospettico, cioè il motivo per cui raccogliamo.
3. **La priorità non è l'interesse, è l'irrecuperabilità.** Ogni voce della
   lista ha la colonna «si perde per sempre?», ed è quella la lista delle cose
   da fare per prime.

**L'onestà preliminare, scritta in testa al README.** Questa raccolta **non
serve a dare più feature al modello**: le Fasi 4c-33 hanno esplorato tutti i
dati interni e il verdetto è stato uniforme (ridondanti o rumore). Serve a tre
cose diverse: l'informazione che il mercato ha e noi no (formazioni a T−1h,
Fase 93), il dataset **notizia → movimento della quota** (che non esiste in
nessun archivio comprabile), e un archivio che vale su più stagioni.

**Lezione.** Il vincolo più importante di un progetto di raccolta dati non è
tecnico né economico: è **quello che le fonti dichiarano di volere**. Costa un
`curl` scoprirlo, e cambia l'architettura. Scoprirlo dopo aver scritto il
raccoglitore sarebbe costato il raccoglitore.

---

## Fase 120 — Il passo 0: metà della lista era già in casa, su licenza

**Obiettivo.** Eseguire il passo 0 del piano (scelta dell'utente): importare
ciò che si può avere senza scraping, e vedere quanto resta davvero da
raccogliere a mano.

**Il ribaltamento.** Il divieto di Transfermarkt sembrava chiudere rose e
valori. Non era così, e la fonte era **già nel repo**:
`davidcariboo/player-scores` su Kaggle è **CC0**, è la fonte ufficiale dello
`squad_value` dalla Fase 67, e si aggiorna ~settimanalmente. Misurata
(versione 673, 213 MB): **507.815** valutazioni, **88.958** partite fino al
6/7/2026, e soprattutto `game_lineups` con **titolari vs panchina** e
`game_events` **col minuto** di ogni gol e cartellino. Copertura: **65
competizioni** — 31 campionati (Turchia, Portogallo, Olanda, Belgio, Scozia…),
10 coppe nazionali, Champions League, 5 tornei per nazionali. Cioè
**tutti i «prossimi passi» che l'utente aveva elencato**, già coperti.

**Il confine che ne esce, ed è la parte utile.** Il dataset è
**retrospettivo**: non contiene infortuni di oggi, probabili formazioni, meteo
previsto, umore. Quindi il lavoro giornaliero si **restringe** a ciò che deve
davvero essere giornaliero; tutto il resto è un download settimanale. È il
principio §1.3 — la versione economica prima dell'infrastruttura.

**Il risultato.** `scripts/build_stagione_anagrafica.py` scrive 96 file
`anagrafica.json`, uno per squadra. L'elenco delle **iscritte 2026-27** viene
dalle partite d'esordio già raccolte da Smarkets (la prima giornata contiene
ogni squadra una volta: 20+20+20+18+18 = **96**); gli attributi dal dataset CC0.

**Tre difetti trovati controllando invece che fidandomi.**

1. **Le rose erano assurde**: Genoa **162** giocatori, Atalanta 153.
   `current_club_id` punta all'*ultimo* club noto, quindi accumulava gente
   ferma al 2017. Filtro sull'ultima stagione del giocatore → mediana **36**.
2. **Il filtro non bastava**: contro `squad_size`, il conteggio ufficiale nella
   stessa fonte, restavamo **+6** di mediana (prestiti e giovani). Non l'ho
   nascosto: il file scrive **entrambi** i numeri e dichiara lo scarto (R4).
3. **Il difetto grave**: sulle squadre col record vecchio il filtro lascia un
   residuo di 1-8 giocatori, e sommarne i valori produceva **«Frosinone,
   valore rosa 0.8 M€» su 1 giocatore di 31** — la rosa più debole d'Europa di
   tre ordini di grandezza, per chi la leggesse. Ora l'aggregato esiste **solo
   se la rosa è completa**; altrimenti `null` dichiarato.

**La lacuna, dichiarata invece che riempita.** Il dataset copre solo la **prima
divisione** di 31 paesi: delle 96 squadre, **82** hanno copertura completa,
**10** un record **stantio** (Málaga fermo al 2017, Hull al 2016) e **4** sono
**assenti** (Elversberg, Coventry, Racing Santander, Le Mans). Sono le
**neopromosse** — cioè proprio le squadre su cui il modello applica il prior δ.

**Decisione su understat** (delegata dall'utente: «fai tu»). `understat.com`
dichiara `User-agent: * / Disallow: /`, e `src/data/understat.py` scaricava da
lì. Ho scelto la **coerenza con la regola che il progetto già applica**:
oddsportal è escluso per lo stesso identico motivo, e trattare understat
diversamente solo perché comodo è ciò che un audit rimprovererebbe.
`download_season` ora **legge la cache e non scarica più**. Costo reale
**zero** nell'uso quotidiano — verificato: l'arricchimento parte solo con
`--refresh`/`--enrich`, mentre il percorso normale legge gli snapshot
congelati, che hanno già le colonne xG e sono versionati. Conseguenza aperta e
scritta: per le stagioni **nuove** serve una fonte xG con licenza chiara.

**📐 Il modello in dettaglio.**

Nessuna matematica nuova: due regole di decisione, verificate riga per riga
contro `scripts/build_stagione_anagrafica.py`.

*(a) Stato di copertura di una squadra*, con `u` = ultima stagione del club nel
dataset e `U` = ultima stagione nota (2025):

```
copertura = "assente"  se il club non esiste nel dataset
          = "completa" se u >= U
          = "stantia"  se u <  U
```

Non è una soglia scelta: `U` è la stagione più recente che il dataset contiene,
quindi `u < U` significa letteralmente «questa squadra in massima serie non
c'era». La distinzione fra `stantia` e `assente` conta perché la prima ha dati
veri ma **vecchi** (usabili con cautela), la seconda non ha nulla.

*(b) Aggregato del valore rosa* — `valore_aggregato(valori, copertura)`:

```
valore_rosa = Σ vᵢ   (vᵢ ≠ null)   se copertura = "completa"
            = null                 altrimenti
```

Il `null` **non** è un valore mancante per pigrizia: è la conseguenza di una
misura. Sulle 14 squadre non complete la rosa disponibile copre fra 0/26 e
8/26 dei giocatori ufficiali; su una frazione così la somma non è una stima
distorta, è **un'altra quantità** — la somma di un sottoinsieme arbitrario. Il
caso peggiore misurato (Frosinone: 1 giocatore su 31, 0.8 M€ contro un vero
ordine di grandezza di ~10² M€) mostra che l'errore non è del 20%: è di **tre
ordini di grandezza**, e col segno sempre lo stesso. Un numero così non va
corretto, va **rifiutato**.

*(c) Perché il filtro sulla rosa esiste.* `current_club_id` è l'**ultimo** club
noto del giocatore, non «la rosa di quest'anno». Senza filtro il Genoa contava
162 giocatori con `last_season` distribuita dal 2017 al 2025; con
`last_season >= U` scende a 39, e la mediana sulle 96 squadre passa da valori
tripli a **36**, contro un `squad_size` ufficiale la cui mediana dista **+6**.
Il residuo è coerente con prestiti in uscita e giovani aggregati, ed è
dichiarato in ogni file invece di essere limato.

**Verifica.** 96/96 squadre risolte, **nessuna in silenzio**: 21 alias
verificati a mano uno per uno (il match approssimato è vietato dal README di
`club/`), 4 assenze dichiarate esplicitamente. 17 test nuovi, **934 verdi**;
quattro mutazioni provate sul codice nuovo, **quattro catturate**.

**Lezione.** Due, e sono la stessa vista da due lati. (1) *Prima di costruire
una fonte, guardare se ce l'hai già*: il dataset CC0 era nel repo da 50 fasi e
copriva coppe, nazionali e campionati esteri che stavamo per mettere in un
elenco di «lavori futuri». (2) *Un aggregato calcolato su una copertura
parziale non è una stima imprecisa: è una quantità diversa*, e va rifiutato,
non arrotondato. Il Frosinone a 0.8 M€ sarebbe passato qualunque controllo di
tipo, di schema e di intervallo: nessuno di quei controlli sa che 1 giocatore
non sono 31.

---

## Fase 121 — Le rose vere: Wikipedia riempie i buchi, ma non tutti (e l'ipotesi era sbagliata)

**Obiettivo.** L'utente, a metà lavoro: *«invece io cercherei i nomi su
internet, potrebbero esserci giocatori infortunati o squalificati o altro,
meglio essere sicuri di tutto»*. Giusto: il dataset CC0 della Fase 120 è una
**fotografia del 27/02/2026** e non sa nulla del mercato estivo.

**Il vincolo, e la fonte scelta.** Transfermarkt vieta i crawler AI (Fase 119).
Wikipedia invece **consente**, ha una API ufficiale, ed è aggiornata da persone
in tempo quasi reale: al 28/07/2026 la voce dell'Inter dichiarava «*Rosa e
numerazione aggiornate al 26 luglio 2026*» citando il sito ufficiale del club.

**La scoperta che risolve il problema della rosa.** Le voci elencano nella
**stessa** sezione i tesserati della prima squadra, con il **numero di maglia**,
e i giovani aggregati, con `n=` **vuoto**: al Napoli sono **26 + 21**. Il
discrimine prima squadra/primavera è quindi un **dato della fonte**, non una
soglia di età o di valore inventata da noi — che è esattamente ciò che mancava
alla Fase 120, dove `rosa_n` mescolava le due cose. Verifica che chiude il
cerchio: **l'Inter esce con 25 numerati, cioè esattamente il `squad_size`
ufficiale**.

**L'ipotesi che ho generalizzato da due casi, ed era falsa.** Avevo verificato
che la Wikipedia *italiana* copre anche Real Madrid (29) e Manchester City (32),
e ne avevo dedotto «**un solo parser per tutti e 96**». La misura su tutte dice
altro: **41/96**, e sbilanciate — Serie A 18/20, Premier 12/20, La Liga 6/20,
Ligue 1 3/18, **Bundesliga 2/18**. L'italiana scrive la voce-stagione dei club
esteri solo per i più noti. Due club bastavano a formulare l'ipotesi, non a
confermarla.

**Ma il valore c'è, ed è dove serve.** Delle 14 squadre che il dataset copre
male — tutte **neopromosse**, cioè quelle del prior δ — Wikipedia ne risolve 4,
e sono i casi peggiori: **Coventry City 0 → 27**, Frosinone 1 → 30, Hull 7 → 27,
Monza 1 → 22. Non aggiunge un decimale a chi già conoscevamo: **riempie i
vuoti**.

**Due difetti trovati e corretti in corsa.** (1) Il nome nei wikilink con
disambigua (`[[Miguel Gutiérrez (calciatore 2001)|Miguel Gutiérrez]]`) usciva
troncato al `pipe`: è la stringa su cui si farà il join, quindi un difetto che
avrebbe rotto tutto a valle. (2) Un «connection reset» a metà di 96 squadre
buttava via l'intero giro, perché ritentavo solo sul 429: un errore di rete
transitorio non è un dato mancante.

**📐 Il modello in dettaglio.** Nessuna matematica: due regole, verificate
contro `scripts/fetch_rose_wikipedia.py`.

*(a) Prima squadra vs aggregati.* Con `n` = numero di maglia dichiarato:

```
prima_squadra(g) = 1  se n(g) è un intero
                 = 0  se n(g) è vuoto
rosa_prima_squadra_n = Σ prima_squadra(g)
```

Non c'è soglia da tarare: la fonte separa già i due gruppi, e noi la leggiamo
invece di rimpiazzarla con un criterio nostro. Controprova sui numeri veri:
Inter 25 numerati contro `squad_size` ufficiale **25**; Napoli 26 contro 47
tesserati totali.

*(b) La voce è quella giusta?* Un titolo è accettato se, insieme:

```
stagione ∈ titolo   ∧   titolo ∉ competizioni_note   ∧   ∃ parola(>3 lettere)
                                                          comune a titolo e nome-club
```

Serve tutto e tre. Senza la prima, si prende la rosa dell'anno **scorso** — un
dato sbagliato che sembra giusto. Senza le altre due, cercando «Paris
Saint-Germain 2026-2027» il primo risultato era *UEFA Champions League
2026-2027*: contiene la stagione e nessuna rosa.

**Lezione.** *Due campioni bastano per una congettura, non per una regola.*
L'ipotesi «l'italiana copre tutti» era comoda — un parser invece di cinque — e
per questo l'ho verificata con due club invece che con novantasei. Il costo di
misurarla per intero era un giro di venti minuti; il costo di non farlo sarebbe
stato scoprire a settembre che la Bundesliga aveva due rose su diciotto.

---

## Fase 122 — Lo scheletro giornaliero: una fetta sottile ma completa

**Obiettivo.** Il passo 2 del piano: la struttura della raccolta quotidiana in
piedi **prima** del primo giorno utile, perché lo stato pre-partita non si
ricostruisce dopo.

**Scelta di metodo: tracer bullet** (§1.1). Non mezza infrastruttura, ma una
fetta verticale che va dal fetch al file su disco: prossime partite → coordinate
dello stadio → previsione meteo → `raccolta.json` + `fonti.json`, con il cron
che lo fa girare da solo.

**Il vincolo misurato che dà forma al livello meteo.** open-meteo copre **16
giorni**: al 28/07 arrivava al 12 agosto, e la richiesta esplicita per il 15
rispondeva **400**. Quindi la prima giornata di campionato **non ha ancora**
una previsione. Non è un guasto ed è scritto come tale (`fuori_orizzonte`, con i
giorni mancanti): fra sei mesi, chi rileggerà questi file deve poter distinguere
«non c'era ancora» da «il fetch è fallito». Il primo giro reale l'ha fatto:
5 partite `fuori_orizzonte`, 1 `coordinate_mancanti`, **0 fetch e 0 errori**.

**`fonti.json` non è un accessorio.** Registra **ogni** tentativo — url, esito,
byte, durata — compresi i falliti. È la contromisura diretta alla Fase 118: un
giorno senza raccolta e un giorno senza raccoglitore devono avere aspetto
diverso. Per lo stesso motivo il workflow **fallisce** se il giro non ha scritto
il suo giorno: qui l'assenza di un file è un problema, non un non-evento.

**Le coordinate.** 90 stadi su 94 da Wikipedia (`prop=coordinates`, campo
strutturato). I 4 mancanti sono esattamente le 4 squadre assenti dal dataset —
non hanno un nome di stadio da cercare. Coerente, e dichiarato invece che
riempito: un meteo sulla città sbagliata è peggio di nessun meteo.

**Un test che ha fatto il suo mestiere.** Avevo aggiunto la soglia di copertura
all'85% sull'aggregato del valore rosa **dopo** aver scritto il test che dava
per buono `[10, None, 30] → 40`. La suite è diventata rossa: il test negava il
comportamento voluto. Riscritto perché **verifichi** la soglia (e che sia la
stessa `MIN_COVERAGE = 0.85` già usata da `transfermarkt.team_season_values`:
due nozioni diverse di «rosa coperta» nello stesso repo sarebbero il modo più
semplice per confrontare numeri non confrontabili). Rigenerati i 96 file: gli 82
con aggregato restano 82, quindi la soglia non cambia il dato di oggi — protegge
i giri futuri.

**📐 Il modello in dettaglio.** Verificato contro
`scripts/raccolta_giornaliera.py`.

*(a) Il meteo esiste?* Con `d` = giorni fra oggi e il calcio d'inizio e
`H = 16` l'orizzonte misurato:

```
stato = "fuori_orizzonte"     se d > H        (e NON si chiama l'API)
      = "coordinate_mancanti" se lo stadio non ha lat/lon
      = "ok" | "non_disponibile" | "ora_non_coperta"   altrimenti
```

`H` non è una costante di comodo: è il numero che l'API espone, misurato
(384 ore = 16 giorni esatti). Il ramo `d > H` **non chiama** l'API — chiedere
qualcosa che si sa non esistere produrrebbe un 400 nel registro delle fonti, cioè
un errore finto in mezzo a quelli veri.

*(b) La finestra delle partite.* `adesso ≤ inizio ≤ adesso + N giorni`, con
`N = 21` di default: più larga dell'orizzonte meteo apposta, perché il file del
giorno deve **elencare** anche le partite di cui non sappiamo ancora il tempo.
Un elenco che si accorcia è un'informazione; un elenco che tace non lo è.

**Lezione.** Uno scheletro utile non è quello che raccoglie di più: è quello che
**dice sempre che cosa gli è successo**. Al primo giro questo ha raccolto zero
dati meteo — e il file lo spiega riga per riga, con il motivo per ciascuna delle
sei partite.

---

## Fase 123 — Lo stadio non è una proprietà della squadra, e le squalifiche non si cercano

**Obiettivo.** Due richieste dell'utente: *«verifica se ogni squadra giocherà
nel proprio stadio tutte le partite (magari in europa gioca in un altro
stadio)»* e *«bollettino quotidiano di infortuni, squalifiche e diffidati…
leggi tu le regole per immaginare quale potrebbe essere il comportamento del
giocatore»*.

### A · Lo stadio: l'intuizione era giusta, e la misura dice quanto

Misurato su `games.csv` (stagioni 2023+, impianto abituale = il più frequente
in campionato): le partite «in casa» giocate **altrove** sono il **5,0%** in
campionato, il **10,8%** in coppa nazionale, il **12,3%** nelle coppe europee e
il **16,4%** in supercoppe e affini. Una gara europea interna **su otto**.
Non sono casi di frangia: Atalanta 29/83, Atlético 30/84, Barcellona 25/82,
Shakhtar 25/67 — ristrutturazioni, requisiti UEFA, campi squalificati, guerre.

**Conseguenza applicata**: nel record giornaliero lo stadio esce con
`stadio_confermato: false` e la nota del perché. È l'impianto abituale, cioè
un'**ipotesi dichiarata**. Prima di questa misura sarebbe stato un campo che
sembra un fatto — e sbagliato una volta su otto proprio nelle partite che
contano di più.

### B · Squalifiche e diffide: si calcolano, e le regole non sono universali

L'osservazione che cambia il disegno del bollettino: **squalifiche e diffide
non vanno cercate, si calcolano.** Bastano i cartellini (che abbiamo, col
minuto, da `game_events`) e il regolamento. È l'unico pezzo del bollettino che
**non dipende da nessun sito**, quindi l'unico immune ai vincoli di
`robots.txt` della Fase 119. Gli infortuni, all'opposto, richiedono per forza
una notizia esterna: restano il pezzo difficile.

**Ho letto le regole invece di andare a memoria, e ho fatto bene.** La
**Ligue 1 è passata da 3 a 5 ammonizioni nel 2025-26**: a memoria avrei scritto
3, che è il valore che quasi tutti ricordano. E la UEFA non usa un multiplo:
squalifica alla **3ª** e poi a ogni ammonizione **dispari** (5ª, 7ª…), con
azzeramento dopo i play-off e dopo i quarti. La Serie A stringe le soglie a
ogni recidiva (5, 10, 14, 17, 19, poi ogni).

Chi codificasse «il calcio» con una soglia unica sbaglierebbe **due leghe su
cinque più la UEFA**, e il difetto sarebbe invisibile: produrrebbe una lista di
diffidati **plausibile** e sbagliata. Per questo le soglie stanno in una
tabella con la fonte accanto (`src/data/disciplina.py`), e un test le fissa una
per una — compreso quello che impedisce di «correggere» la Ligue 1 riportandola
a 3.

**Validato sui cartellini veri**, non solo sugli esempi: Serie A 2025-26,
11.926 presenze, 1.361 gialli, 421 giocatori ammoniti; a fine stagione **58
diffidati** e 45 sulla soglia, con una distribuzione plausibile (103 giocatori
a 1 giallo, 41 a 5, 1 a 12).

### C · Il comportamento del diffidato: un incentivo, non una misura

La domanda dell'utente è sensata e ha una base **meccanica**: la squalifica
cade sulla partita *successiva* a quella del cartellino. Quindi se la gara
imminente vale poco e quella dopo vale molto, «smaltire» la diffida subito
costa poco e libera la partita che conta; se è imminente quella importante,
conviene evitare il giallo.

`incentivo_cartellino()` lo calcola — ma dichiara `tipo: "giudizio"`, e la
formula è deliberatamente banale (§📐): **nessuno ha mai misurato se i
giocatori vi si conformino davvero**. Un modello elaborato qui darebbe
un'illusione di precisione su una quantità — l'importanza di una partita — che
non abbiamo misurato.

**📐 Il modello in dettaglio.** Verificato contro `src/data/disciplina.py`.

*(a) Prossima soglia.* Con `S = (s₁…sₙ)` le soglie dichiarate e `k` il passo
dopo l'ultima:

```
soglia_successiva(c) = min{ sᵢ ∈ S : sᵢ > c }              se esiste
                     = sₙ + k·⌈(c − sₙ + 1)/k⌉             se k > 0
                     = None                                 altrimenti
```

Il ramo `None` (Premier oltre la 15ª) è diverso da «zero ammonizioni
mancanti», e i due non vanno confusi: il primo dice «non c'è più una soglia»,
il secondo direbbe «sei squalificato».

*(b) Diffidato.* `diffidato(c) ⟺ soglia_successiva(c) − c = 1`. È la
definizione italiana di diffida, ed è quella che serve: identifica **chi
rischia di saltare la prossima partita**, che è l'unica cosa che cambia una
previsione.

*(c) Incentivo (giudizio).* Con `p` e `s` importanza della prossima e della
successiva, in [0,1]: `incentivo = s − p`. Il valore sta nel **segno**. La
soglia ±0.2 che separa «conviene» da «indifferente» è arbitraria e dichiarata
tale: serve a non leggere come segnale una differenza di rumore.

**Lezione.** Due, e vengono dallo stesso posto. (1) *Un attributo che sembra
appartenere a un'entità spesso appartiene all'evento*: lo stadio «della
squadra» è sbagliato una volta su otto in Europa, e nessun controllo di schema
se ne accorgerebbe. (2) *Le regole hanno una data*. La Ligue 1 ha cambiato la
soglia un anno fa; scriverla a memoria avrebbe prodotto diffidati inventati per
una stagione intera, senza che nulla diventasse rosso. Le costanti di dominio
vanno lette alla fonte e datate, esattamente come i dati.

---

## Fase 124 — Il diffidato si trattiene davvero: misurato (e il segno ingenuo era rovesciato)

**Obiettivo.** Proposta dell'utente: *«se abbiamo il calendario della squadra e
quando ogni giocatore ha preso i cartellini, possiamo fare un backtest o uno
studio per vedere correlazioni e simili»*. L'ipotesi più netta che questi dati
possono **falsificare** è quella che alla Fase 123 avevo esplicitamente
dichiarato non verificata: *un giocatore a una ammonizione dalla squalifica
gioca più prudente*.

**Il disegno è la parte difficile, non il conto.** Un confronto ingenuo
«diffidati contro non diffidati» è **garantito** a dare un risultato sbagliato,
e di segno **opposto**: per arrivare a 4 gialli bisogna essere un giocatore che
i gialli li prende. Lo stato «diffidato» seleziona i falciatori. Ed è
esattamente quello che succede:

| confronto | Δ tasso di ammonizione |
|---|---:|
| **ingenuo** (fra giocatori diversi) | **+0.0275** ← «i diffidati prendono PIÙ cartellini» |
| **within-player** (ogni giocatore controlla se stesso) | **−0.0265** IC95% [−0.0299, −0.0230] |

Lo stesso dato, letto nei due modi, dice cose opposte. Il secondo è quello
giusto: rimuove l'effetto-giocatore, e l'incertezza viene da un bootstrap **a
grappolo sul giocatore** — le presenze dello stesso giocatore non sono
osservazioni indipendenti, e un bootstrap sulle righe darebbe un intervallo
troppo stretto (R7). Replica in tutte e 5 le leghe, tutte conclusive
(Bundesliga −0.048, Ligue 1 −0.040, Premier −0.032, Liga −0.030, Serie A −0.025).

**Ma il within-player non basta**, e questa è la parte che vale. Lo stato
«diffidato» arriva **per forza più tardi** nella stagione: se il tasso di
ammonizione calasse da solo col passare delle giornate, vedremmo lo stesso
effetto senza che nessuno si trattenga. Il test che separa le due spiegazioni è
confrontare lo stato a soglia−1 **solo con i due confinanti** (3 e 5 gialli):
una tendenza liscia dà zero, un gradino sopravvive.

**Sopravvive**: gradino **−0.0154**, IC95% [−0.0195, −0.0111], su un tasso base
di 0.1715 → **−9,0% relativo**, conclusivo. E il profilo mostra il gradino
**anche alla soglia successiva** (9 gialli, vigilia del decimo): −0.0107 contro
+0.0009 a 7 gialli. Due gradini nello stesso posto, per due volte.

**Il controllo che chiude un'altra spiegazione.** Un diffidato potrebbe essere
semplicemente **sostituito prima** — meno minuti, meno occasioni di prendere il
giallo. Misurato: i diffidati giocano **più** minuti (73.3 contro 66.1). Più
esposizione dovrebbe significare **più** cartellini: quindi l'effetto misurato
è semmai una **sottostima** della prudenza.

**La domanda sul timing: NON confermata, e il test non può confermarla.**
L'utente aveva ipotizzato che il diffidato scelga *quando* prendersi il giallo
in base a quale partita conta. Se fosse così, la prudenza dovrebbe attenuarsi a
fine stagione, quando restano poche gare da proteggere. Misurato per terzi di
stagione: −0.0205 / −0.0108 / −0.0151. Gli intervalli si sovrappongono — e
**la R7 impone di testare la differenza invece di leggere la sovrapposizione**:
differenza inizio−fine **−0.0054**, IC95% [−0.0164, +0.0048], **non
conclusiva**. Con la potenza dichiarata: l'IC sulla differenza è **1,4 volte
l'effetto medio stesso**, quindi un'attenuazione anche del **50%** resterebbe
dentro il rumore. Questo test non la può vedere: serve un proxy di «importanza»
per partita, che non abbiamo.

**📐 Il modello in dettaglio.** Verificato contro
`scripts/_run_fase124_diffidati.py`.

*(a) Stato disciplinare senza look-ahead.* Per ogni presenza `i` del giocatore
`p` nella competizione `c` e stagione `s`:

```
gialli_prima(i) = Σ_{j < i, stesso (p,c,s)} gialli(j)
diffidato(i)    ⟺ gialli_prima(i) = T(c,s) − 1
```

`T` dipende da **lega e stagione**: 5 ovunque, ma **3 in Ligue 1 fino al
2024-25** (la regola semplificata è del 2025-26, Fase 123). Applicare 5 a tutti
avrebbe mescolato stati diversi in entrambi i gruppi — l'errore sarebbe stato
invisibile, perché il conto sarebbe girato lo stesso.

*(b) Stimatore within-player.* Con `y` = 1 se ammonito:

```
δ_p = media(y | p, diffidato) − media(y | p, controllo)
Δ   = Σ_p w_p·δ_p / Σ_p w_p          w_p = n. presenze da diffidato di p
```

Solo i giocatori che hanno vissuto **entrambi** gli stati entrano (4.888).
L'effetto-giocatore sparisce per differenza: è ciò che rovescia il segno.

*(c) Il gradino, cioè il test contro l'artefatto temporale.* Sul solo
sottoinsieme `gialli_prima ∈ {3,4,5}`, con `r` = residuo centrato sul giocatore:

```
gradino = media(r | gialli_prima = 4) − media(r | gialli_prima ∈ {3,5})
```

Una discesa lineare in `gialli_prima` dà **esattamente zero** su questo
contrasto (il 4 è il punto medio di 3 e 5): tutto ciò che resta è
non-linearità localizzata alla soglia. È il motivo per cui questo stimatore, e
non il §b, è quello da citare.

*(d) Incertezza.* Bootstrap a grappolo: si ricampionano i **giocatori** con
reinserimento e si ricalcola la statistica su tutte le loro presenze. Ignorare
il grappolo qui gonfierebbe la precisione di parecchio: 4.457 giocatori contro
128.072 presenze, cioè ~29 osservazioni correlate per grappolo.

**Che cosa ne consegue, senza esagerare.** È un effetto **comportamentale reale
e misurato**, non un aneddoto: −9% sulla probabilità di ammonizione, con due
gradini indipendenti e replica su 5 leghe. Ma è un effetto sui **cartellini**,
non sui gol: quanto sposti il prezzo di un mercato 1X2 è tutt'altra domanda, e
questa fase non la tocca. Il valore immediato è che una riga che alla Fase 123
avevo marcato «giudizio mai verificato» ora ha una misura — e la parte di
quell'ipotesi che riguardava il *timing* resta invece **non dimostrata**, con la
potenza scritta accanto.

**Lezione.** *Quando lo stato che studi è raggiunto solo da chi ha una certa
propensione, il confronto fra gruppi misura la propensione, non lo stato.* Qui
il segno si rovesciava: +0.0275 contro −0.0265. E il within-player da solo non
sarebbe bastato — serviva il contrasto locale alla soglia per escludere che
fosse il calendario a fare il lavoro. Due controlli, due spiegazioni alternative
eliminate, e solo allora un numero da scrivere.

---

## Fase 125 — Prezzare i cartellini: ogni leva paga, e la sotto-dispersione non è dei gol

**Obiettivo.** L'utente: *«lavoriamoci per bene su questi dati (sui
cartellini)»*. C'è un aggancio concreto: i cartellini sono già un **mercato che
il progetto prezza** (Fase 96), quindi la domanda non è descrittiva ma
operativa — **quali fattori migliorano la previsione fuori campione?**

**Prima di modellare, il test che la Fase 99 rende obbligatorio.** *Misurato ≠
prevedibile*: un effetto visto in una stagione va usato solo se **persiste**.
Correlazione fra l'effetto di una stagione e quello della successiva:

| effetto | corr(t, t−1) | IC95% |
|---|---:|---|
| **arbitro** | **+0.352** | [+0.299, +0.405] |
| squadra (in casa) | +0.356 | [+0.300, +0.408] |
| squadra (in trasferta) | +0.288 | [+0.229, +0.343] |

Tutti e tre persistono, a differenza del bias di livello della Fase 99. Solo
allora ha senso metterli in un modello.

**Il backtest.** Un'osservazione = (partita, lato): quanti gialli prende **una**
squadra in **una** partita. Modello moltiplicativo nello stile del
Dixon-Coles, ogni fattore ritirato verso 1 e stimato **solo** sulle stagioni
precedenti (walk-forward, nessun look-ahead). Metrica: log-verosimiglianza per
osservazione, perché determina il prezzo di **qualunque** linea over/under
insieme, non di una sola.

| modello | ll | guadagno incrementale | IC95% |
|---|---:|---:|---|
| base (media di lega) | −1.68829 | — | — |
| + squadra | −1.68390 | **+0.00440** | [+0.00309, +0.00576] ✅ |
| + avversario | −1.68233 | +0.00157 | [+0.00050, +0.00260] ✅ |
| + fattore campo | −1.67862 | +0.00371 | [+0.00281, +0.00464] ✅ |
| + **arbitro** | −1.67491 | **+0.00368** | [+0.00269, +0.00469] ✅ |

**Ogni leva paga, e tutte con IC conclusivo** — cosa rara in questo progetto,
dove la maggior parte delle leve finisce nel rumore. Il dato che colpisce:
**l'arbitro vale quanto il fattore campo**. Il totale è +0.01336
[+0.01120, +0.01552].

**Poi il numero che vale più di tutto il resto.** Per squadra-partita, la
varianza dei gialli è **0.954 volte** la media: i cartellini sono
**sotto-dispersi**, esattamente come i gol dati i tassi del mercato (Fase 51).
La binomiale negativa non può nemmeno rappresentarlo (il suo α collassa a
0.0001, il bordo). Ma il progetto ha già lo strumento giusto —
`_dp_pmf(rate, θ)`, la double-Poisson mean-preserving della Fase 51 — e l'ho
riusato invece di inventarne uno:

```
theta ottimo = 1.150      Δll = +0.00265   IC95% [+0.00199, +0.00330]  ✅
```

Vale il **72%** di quanto vale l'arbitro, e il 20% di tutte le covariate messe
insieme, per **un solo parametro**.

**Ma la mappa per lega NON si trasferisce, e questo è il punto delicato.**

| lega | θ cartellini | (θ gol, Fasi 51-53) |
|---|---:|---|
| Serie A | **1.310** ✅ | ~1.2 |
| Ligue 1 | **1.250** ✅ | ~1.08 |
| Bundesliga | 1.110 ✅ | ~1.07 |
| La Liga | 1.080 · | ~1.24 |
| Premier | 1.020 · | ~1.07 |

θ > 1 in **5 leghe su 5**, ma conclusivo solo in 3. E l'ordine è **diverso** da
quello dei gol: le «due famiglie» dell'audit a 5 leghe (latine ad alto θ contro
le altre) qui non reggono — la Liga scende, la Ligue 1 sale. Serie A resta alta
in entrambi, la Premier bassa in entrambi.

**Che cosa se ne conclude, con precisione.** La sotto-dispersione **non è una
proprietà dei gol**: è una proprietà dei **processi di conteggio del calcio**,
e si ritrova su un processo che la Fase 96 aveva già dichiarato *diverso* dai
gol. Ma il **valore** di θ è specifico della coppia (lega × processo), quindi
non si eredita: va fittato dove lo si usa. È la stessa lezione del §7 del
`CLAUDE.md` — le formule sono universali, gli iperparametri no — estesa da
«per lega» a «per lega e per processo».

**📐 Il modello in dettaglio.** Verificato contro
`scripts/_run_fase125_cartellini.py`.

*(a) Tasso atteso.* Per l'osservazione (partita, lato):

```
λ = base(lega) · f_squadra · f_avversario · f_casa · f_arbitro
```

*(b) Ogni fattore è una media ritirata verso 1:*

```
f_g = 1 + [n_g/(n_g + K)] · (media_g/media_globale − 1)      K = 40
```

`K = 40` significa che servono ~40 partite perché il dato del gruppo pesi
quanto la media di lega. Non è un abbellimento: senza shrinkage un arbitro con
3 partite e 9 gialli avrebbe `f = 2.2` e rovinerebbe ogni previsione che lo
incontra — ed è esattamente il caso che si presenta a ogni inizio stagione, con
gli arbitri nuovi.

*(c) Sotto-dispersione.* `q_k ∝ Poisson(c·λ)^θ` rinormalizzata, con `c` risolto
per bisezione perché la media resti `λ` (mean-preserving). `θ > 1` concentra la
massa attorno alla media. È **la stessa funzione** già in produzione sui gol:
il valore dell'esperimento sta proprio nel non aver scritto codice nuovo — se
avessi implementato una seconda double-Poisson, un risultato diverso non
avrebbe distinto «processo diverso» da «bug diverso».

*(d) Perché la log-verosimiglianza e non il MAE.* Il MAE è leggibile ma **non è
una regola di punteggio**: premia chi indovina il centro, non chi indovina la
distribuzione. Su un mercato over/under conta la seconda, e θ agisce **solo**
sulla forma — a media invariata. Con il MAE, l'intero effetto della
sotto-dispersione sarebbe stato invisibile.

**Lezione.** *Un risultato vecchio si generalizza meglio riusando il suo codice
che riscrivendolo.* La sotto-dispersione dei gol era una scoperta chiusa della
Fase 51; applicarne la **stessa funzione** a un processo dichiarato diverso è
costato dieci righe e ha prodotto un risultato nuovo — con la garanzia che
un'eventuale differenza fosse del fenomeno e non dell'implementazione. E
l'altra metà della lezione è simmetrica: **il fenomeno si è trasferito, i suoi
parametri no.**

---

## Fase 126 — Cartellini: la contraddizione con la Fase 98 era apparente, e il modello «giusto» non paga

**Obiettivo.** Portare in produzione le leve della Fase 125. Ma prima di
toccare il listino è emerso un conflitto da risolvere: **la Fase 98 aveva
misurato i cartellini SOVRA-dispersi** (var/media 1.12-1.48) e adottato la
binomiale negativa; **la Fase 125 li ha misurati SOTTO-dispersi** (0.954).
Due fasi dello stesso repo che dicono il contrario.

**Non è una contraddizione: è la stessa cosa a due livelli.** E la
scomposizione lo dimostra **esattamente** — regola §2-bis, quella nata alla
Fase 92: una deduzione da misura indiretta va scritta come identità, non in
prosa.

```
var(totale) = var(casa) + var(ospite) + 2·cov(casa, ospite)
  4.7308    =   1.8699  +   2.0258    + 2·0.4175          ✓ (ricompone esatto)
```

Ogni **lato** è sotto-disperso (0.970 e 0.924), ma i due lati sono **correlati
positivamente** (corr **+0.2145**): la partita nervosa produce cartellini per
entrambe. **Tutta** la sovra-dispersione del totale viene da lì — a lati
indipendenti il totale avrebbe rapporto **0.945**, cioè sarebbe sotto-disperso
anche lui. La Fase 98 misurava il totale, la Fase 125 il lato: **entrambe
avevano ragione**, e nessuna delle due poteva accorgersene da sola.

**Conseguenza teorica, e il modello che ne segue.** Se è così, la binomiale
negativa sul totale stava tappando la **correlazione** con un parametro di
**forma**: la patch giusta per il motivo sbagliato. Il modello che separa le due
cose è un condizionale a effetto casuale:

```
gialli_casa | Z ~ dp(λ_casa · Z, θ)
gialli_osp  | Z ~ dp(λ_osp  · Z, θ)      indipendenti DATO Z
Z ~ Gamma(media 1, varianza σ²)          il "nervosismo" della partita
```

con `σ² → 0` che ricade esattamente sui lati indipendenti: il caso «niente
nervosismo» resta un caso particolare, non un modello rivale.

**Esito: NON paga.** Walk-forward sul totale (19.761 partite):

| modello | ll |
|---|---:|
| Poisson sul totale (forma F96) | −2.12806 |
| **NegBin sul totale (adottato F98)** | **−2.12734** |
| dp per lato, indipendenti | −2.12806 |
| dp per lato + nervosismo | −2.12731 |

Guadagno del modello strutturale sulla NegBin: **+0.00003**, IC95%
[−0.00015, +0.00022] — **nel rumore**. E la griglia sceglie **θ = 1.00**, cioè
marginali Poisson, proprio dove la Fase 125 aveva trovato θ=1.15 conclusivo.

**Il perché, misurato e non congetturato.** La superficie di verosimiglianza in
(θ, σ²) è una **cresta**:

| θ \ σ² | 0.00 | 0.02 | 0.04 | 0.06 |
|---|---:|---:|---:|---:|
| 1.00 | −2.12806 | **−2.12731** | −2.12878 | −2.13188 |
| 1.10 | −2.13177 | −2.12843 | **−2.12798** | −2.12963 |
| 1.20 | −2.13769 | −2.13137 | −2.12869 | **−2.12864** |
| 1.30 | −2.14568 | −2.13601 | −2.13088 | **−2.12896** |

Al crescere di θ cresce il σ² ottimo, e lungo la cresta la verosimiglianza è
**piatta** (−2.1273 → −2.1290, cioè 0.0017 in tutto). **Sul totale, forma
marginale e correlazione non sono separatamente identificabili**: è la stessa
varianza spiegata due volte. Solo il dato **per lato** può distinguerle — ed è
esattamente il dato che la Fase 98 non guardava.

**Che cosa si adotta, allora.**

1. **Sul TOTALE cartellini** (il mercato O/U che il progetto già prezza): **la
   binomiale negativa della Fase 98 resta**. Non perché fosse la struttura
   giusta, ma perché a quel livello nessuna struttura più fine è distinguibile.
   La differenza è che ora sappiamo *che cosa* stava fittando.
2. **Per i mercati PER SQUADRA** (total-squadra cartellini): lì la θ=1.15 della
   Fase 125 è misurata e conclusiva, e il totale non la può contraddire perché
   non la può nemmeno vedere.
3. **Il fattore ARBITRO** (+0.00368 per lato, IC conclusivo) vale in entrambi i
   casi: agisce sulla **media**, non sulla forma, e non soffre di questa
   ambiguità.

**📐 Il modello in dettaglio.** Verificato contro
`scripts/_run_fase126_cartellini_congiunto.py`.

*(a) Il totale, integrando il nervosismo:*

```
P(tot = n) = Σ_j w_j · [ dp(λ_c·z_j, θ) ⊛ dp(λ_o·z_j, θ) ](n)
```

con `⊛` la convoluzione e `(z_j, w_j)` una quadratura a 11 nodi equiprobabili
della Gamma ri-centrata su media 1. La media resta **esattamente** `λ_c + λ_o`
— verificato numericamente (4.204 contro 4.204): la proprietà mean-preserving
della dp sopravvive sia alla convoluzione sia alla miscela, il che è ciò che
rende il confronto onesto (i modelli differiscono **solo** per la forma).

*(b) Perché la correlazione entra come fattore moltiplicativo comune.* Un
effetto additivo avrebbe potuto rendere negativo un tasso; uno moltiplicativo
con media 1 lascia invariata la previsione centrale e agisce solo sulla
dipendenza. Con `Var(Z) = σ²` la covarianza indotta è `σ²·λ_c·λ_o`: con
λ ≈ 2.06 ciascuno e σ² = 0.02 dà ≈ 0.085, contro **0.4175** osservato. Cioè
**il nervosismo condiviso spiega solo un quinto della covarianza reale**: il
resto è correlazione che questo effetto casuale non cattura — un residuo
dichiarato, non risolto.

*(c) Una nota su una trappola di calcolo, perché è costata un'ora.* La prima
stesura chiamava `_dp_pmf` per ogni partita e per ogni nodo: 42 combinazioni ×
19.761 partite × 11 nodi × 2 lati ≈ **18 milioni** di bisezioni. Tabulare la
pmf su una griglia di tassi (~900 valori per θ) porta il giro da ~90 minuti a
**22 secondi**. Il risultato non cambia; cambia se l'esperimento si può fare.

**Lezione.** *Due misure che si contraddicono spesso misurano due cose
diverse: prima di scegliere chi ha ragione, si scrive l'identità che le lega.*
Qui la scomposizione della varianza ha mostrato che **entrambe** erano giuste,
e ha prodotto un'ipotesi strutturale precisa — che poi si è rivelata **non
verificabile a quel livello di aggregazione**. È un esito che vale la pena
scrivere due volte: un modello «più corretto» non è automaticamente un modello
**migliore**, e quando due parametri si scambiano il lavoro, la scelta fra loro
non è una questione empirica ma di comodo.

---

## Fase 127 — La Liga era uscita dalla raccolta in silenzio: una guardia che scattava solo troppo tardi

**Obiettivo.** Rispondere a «come completiamo il test prospettico?» (Fase 78)
partendo da un controllo dello stato, a 14 giorni dalla prima giornata utile
(La Liga, 15 agosto). Il controllo ha trovato un guasto, e la fase è diventata
quello.

**Il fatto.** Confrontando gli snapshot di `data/smarkets_matches/`, il file del
**31/07/2026** contiene **38 partite** invece delle 48 dei tre giorni
precedenti, e **nessuna riga di La Liga**. Il workflow era verde. La causa,
verificata dal vivo interrogando il listino: Smarkets ha **rinominato lo slug di
competizione** da `spain-laliga` a `spain-la-liga`. `SLUG_LEGA` confronta il
segmento in modo **esatto** (scelta deliberata della Fase 116, e giusta: un
match largo raccoglie la lega sbagliata), quindi la Liga ha semplicemente
smesso di essere riconosciuta.

**Perché nessuno se n'è accorto.** `anomalia_del_listino` esisteva proprio per
questo — R6, «il buco peggiore è il finto pieno» — ma la sua soglia era
`nostri == 0`: scatta **solo se spariscono tutte e cinque**. Il modo realistico
in cui un'API rinomina uno slug è invece **una lega alla volta**. Quattro leghe
su cinque sono un finto pieno perfetto: il file c'è, pesa 120 KB, e non
contiene la lega che parte per prima. La distanza fra la guardia scritta e il
guasto reale era esattamente un quantificatore.

**Alternative considerate.**
1. *Match largo sullo slug* (`"spain" in slug`) — scartata: reintrodurrebbe il
   rischio che la Fase 116 aveva eliminato (raccogliere la seconda divisione o
   un torneo femminile credendolo la prima).
2. *Far fallire il giro appena una lega manca, prima della raccolta* —
   **scartata**: farebbe perdere anche le altre quattro, e i dati pre-partita
   non si ri-scaricano (`newseason.md` §2). Un allarme che distrugge il dato
   che doveva proteggere è peggio del silenzio.
3. *Scelta adottata*: raccogliere tutto, **dichiarare il buco nel file**
   (`leghe_senza_partite_esposte`), e uscire con codice diverso da zero **dopo**
   aver scritto. Il dato è salvo e il workflow è rosso.

**Risultato.** Entrambi gli slug in mappa (il vecchio **non** si toglie:
l'archivio già raccolto lo contiene, e un rinominamento può essere rimesso
indietro); `leghe_assenti()` nuova; raccolta di recupero eseguita a mano lo
stesso giorno. Test: 23 verdi su questo modulo, fra cui quello che fissa per
iscritto che la guardia vecchia, da sola, **non** vedeva il caso.

**📐 Il modello in dettaglio.** Nessuna matematica nuova: la correzione è un
quantificatore. Detto `E` l'insieme delle leghe esposte dal listino e `L` le
nostre cinque, la guardia della Fase 116 era

```
allarme_116  ⇔  |E ∩ L| = 0            (sparizione TOTALE)
```

e quella di oggi è

```
mancanti     =  L \ E
allarme_127  ⇔  mancanti ≠ ∅           (sparizione di UNA QUALSIASI)
```

con `allarme_116 ⇒ allarme_127` (la vecchia è il caso `mancanti = L`), quindi
la nuova non allenta nulla: stringe. Il caso reale del 31/07 è
`|E ∩ L| = 4 ≠ 0` e `mancanti = {la_liga} ≠ ∅`: **falso** per la prima,
**vero** per la seconda. Il numero che rende la condizione non vacua è
**misurato**, non assunto: il 28/07/2026 — il punto più profondo
dell'off-season, nessuna delle 5 leghe in campo prima del 15 agosto — tutte e
cinque erano esposte con **9-10 partite ciascuna** (48 in totale). «Lega a
zero» non è uno stato che il calendario produca.

**Lezione.** *Una guardia va tarata sul guasto che accadrà, non sul guasto che
è comodo scrivere.* La forma «tutto o niente» è la più facile da implementare e
la meno probabile in natura: i sistemi esterni si rompono **per pezzi**. E il
corollario operativo, che vale per ogni raccoglitore futuro del progetto: un
allarme non deve mai poter distruggere il dato che sta proteggendo — prima si
salva, poi si urla.

---

## Fase 128 — Il passo P1: la mappa nomi, e la neopromossa che il modello non sa di avere

**Obiettivo.** Sbloccare il test prospettico partendo dal passo che blocca
tutti gli altri (§5.1 di `experiments/prospettico_2026_27.md`): il ponte fra i
nomi squadra di Smarkets — da cui arrivano **quote e fixture** della stagione
2026-27 — e i nomi canonici dei nostri snapshot. Senza, nessuna delle 48
partite si aggancia: né il Modello 1 (che deve sapere chi scende in campo) né
il Modello 2 (che deve invertire le quote di *quella* partita).

**Ragionamento.** È il bug più banale del progetto e quello capitato più volte
(«Hellas Verona» → «Verona», Fase 5; `Manchester Utd` che fermava un join a
544/760, Fase 122), quindi non si fa a occhio: si estraggono **tutti** i nomi
distinti e si confrontano **per identità**, mai per ordinamento o per
contenimento.

**Risultato, primo strato.** Le 96 squadre della giornata 1 (20+20+20+18+18 —
il listino esposto copre **l'intero organico** di tutte e 5 le leghe):
**62 combaciavano** già, **25 passavano** dagli alias esistenti, **9** erano
differenze nuove. Tre di queste nove non sono abbreviazioni innocue:

- `Köln` → `FC Koln` e `Málaga` → `Malaga` differiscono per **un carattere
  accentato**, e sono squadre **con storia vera** nei nostri dati (7 stagioni
  su 9 il Colonia). Un confronto esatto le scarta senza dire niente;
- `PSG` → `Paris SG` convive **nella stessa giornata** con `Paris FC`, che è
  un altro club e combaciava già. Un match largo su "Paris" li fonderebbe, e
  **nessun conteggio se ne accorgerebbe**: le squadre resterebbero 18.

**Il controllo che rende superfluo l'occhio umano.** Invece di rileggere 96
nomi, si usa una proprietà **strutturale**: un campionato non cambia numero di
squadre fra due stagioni, quindi in ogni lega **|entrate| = |uscite|**. Un
nome mappato male rompe l'uguaglianza (una squadra vera resta fuori, una
fantasma entra). Torna su tutte e cinque: 3-3, 3-3, 2-2, 3-3, 3-3.

**Cinque squadre senza nome canonico — e la R5 applicata.** Elversberg,
Racing Santander, Le Mans, Coventry e Hull non hanno **mai** giocato nelle
nostre 5 leghe in 9 stagioni: un nome canonico nei nostri snapshot **non
esiste per costruzione**. Non sono alias mancanti né errori. La tentazione era
dedurre la grafia dalle convenzioni del provider; invece si è **cercato il
dato vero** (R5, passo 3): quelle squadre nel 2025-26 giocavano in **seconda
divisione**, e football-data pubblica anche quei file. Scaricati
`mmz4281/2526/{E1,D2,SP2,F2}.csv` ed enumerati i nomi: `Elversberg`,
`Santander`, `Le Mans` — e `Coventry`/`Hull` **identici** a come li scrive
Smarkets. Tre alias nuovi, zero indovinati.

**La scoperta vera, che non era il bersaglio della fase.**
`scripts/backtest.py::promoted_teams` deduce le neopromosse confrontando la
stagione di test con la precedente. Per il 2026-27 **la stagione di test non
esiste ancora nei dati**, quindi la funzione restituisce l'insieme vuoto: nel
test prospettico le promosse vanno **dichiarate**, e sono **14**. Non è una
formalità burocratica, ed è il motivo per cui questa fase esiste: senza
dichiararle, il **Malaga** — una sola stagione nei nostri dati, la 2017-18 —
non finisce nel prior delle promosse e viene stimato dallo shrinkage verso la
**media della lega**. Cioè trattato come una squadra *normale* invece che come
una neopromossa. I due difetti sono **opposti**, e solo uno è quello giusto.

**📐 Il modello in dettaglio.** Nessuna matematica nuova: il decadimento
esponenziale è quello della Fase 4d, il prior delle promosse quello della
Fase 7. Quel che serve è il **conto** che li mette insieme.

Il peso di una partita giocata `g` giorni prima di `as_of`, con emivita
`H = 365` giorni (`LEAGUE_CONFIGS`, tutte e 5 le leghe):

```
w(g) = 0.5^(g / H)
```

Il bersaglio dello shrinkage, da `dixon_coles.fit` (righe 366-373):

```
attack_prior[t]  = −δ   se t ∈ promoted_teams,  0 altrimenti
defense_prior[t] = +δ   se t ∈ promoted_teams,  0 altrimenti
```

cioè: **0 = la media della lega**. Una squadra non dichiarata promossa viene
tirata verso la squadra media; una dichiarata, verso «segna meno e subisce di
più» di δ (La Liga: **0.22**).

Con `as_of = 2026-08-14` (la vigilia del congelamento) e l'ultima partita di
Malaga il **2018-05-19**, cioè `g = 3.009` giorni:

```
w = 0.5^(3009/365) = 0.5^8.24 = 0.0033
```

**Tre millesimi.** La storia c'è, e non conta nulla: la verosimiglianza è
piatta su quei parametri e li lascia dove li mette il prior — che senza
dichiarazione è **zero, la media**. Ecco perché «ha storia nei dati» e «il
modello sa qualcosa di lei» sono due cose diverse. Lo stesso conto per le
altre 13 mostra che il problema è **graduato**, non binario:

| squadra | ultima partita | g (giorni) | w = 0.5^(g/365) |
|---|---|--:|--:|
| Malaga, La Coruna | 2018-05 | 3.009 | **0.0033** |
| Paderborn | 2020-06 | 2.239 | 0.0142 |
| Schalke 04, Troyes | 2023-05/06 | ~1.170 | ~0.108 |
| Ipswich, Monza, Venezia | 2025-05 | ~447 | **0.428** |
| Elversberg, Santander, Le Mans, Coventry, Hull | mai | ∞ | **0** |

Le ultime tre righe sono tre regimi diversi: chi ha ~0.43 di peso è stimato
**dai suoi dati** (il prior conta poco), chi ha 0.003 è stimato **dal prior**
pur avendo righe nel database, e chi non ha mai giocato entra nel modello **a
zero partite** — cold-start puro, esattamente il caso per cui il prior della
Fase 7 era stato scritto. Dichiarare le 14 promosse è ciò che rende il
secondo gruppo uguale al terzo invece che al primo.

**Onestà su cosa NON è stato misurato.** Che dichiararle sia *meglio* qui non
è stato verificato in backtest su questa stagione — non si può, la stagione
non esiste. L'evidenza è quella della Fase 7 (dove il prior fu adottato perché
misurato utile) più il conto qui sopra, che mostra che l'alternativa è
«Malaga = squadra media di Liga». È un argomento **strutturale**, e va letto
come tale.

**Lezione.** *Un dato può essere presente e non informativo, e le due cose si
confondono facilmente.* Il controllo «la squadra è nel database?» dà la
risposta giusta alla domanda sbagliata: quella utile è «quanto pesa, alla data
in cui prevedo?». E il corollario metodologico: quando una proprietà
strutturale esiste (entrate = uscite), conviene testarla invece di rileggere
la lista — una regola verifica 96 nomi, e continua a verificarli l'anno
prossimo.

---

## Fase 129 — Il test prospettico è congelato: 48 partite, 26 mercati, due settimane di anticipo

**Obiettivo.** Portare a termine i passi P2-P6 della checklist (§5.1 di
`experiments/prospettico_2026_27.md`) e **congelare** il Modello 1, invece di
arrivare al 14 agosto con tutto da fare.

**La domanda che andava fatta prima: perché aspettare il 14 agosto?**
La scadenza esisteva perché una previsione prodotta dopo il fischio non è una
previsione. Ma il M1 dipende **solo** dai dati fino a 2025-26, che sono
congelati da maggio: fra il 1° e il 14 agosto **non cambia niente** che possa
entrare nella previsione. Congelare oggi è quindi **identico nel contenuto** e
**strettamente migliore nel processo** — più lontano dal kickoff, e senza il
rischio che una sessione salti la finestra. L'unica cosa che il 14 agosto
avrebbe in più è la possibilità di cambiare il modello prima: se succede, si
ri-congela e git tiene entrambe le versioni datate.

**Cosa è stato fatto.**

1. **P2 — i fixture veri.** `_run_prospettico_2627.py` conteneva **7 partite
   Premier hardcoded e dichiaratamente plausibili**. Ora legge lega, squadre,
   data e ora dall'ultimo file di `data/smarkets_matches/`: **48 partite**, che
   sono l'organico completo delle 5 leghe.
2. **P3 — congelate 48 × 26 mercati** in `prospettico_2026_27_m1.csv`, con i
   metadati (config per lega, motore, neopromosse dichiarate, commit) in un
   JSON gemello.
3. **D1 — la chiusura vera.** Il regime denso girava ogni 6 ore: l'ultimo
   prezzo prima del fischio poteva essere vecchio di 6 ore, e *quella* non è
   una chiusura. Aggiunto un cron **orario** con finestra a **2 ore** e
   listino **intero**. Costo quasi nullo: nelle ore senza partite lo script
   esce **prima** di chiedere le quote e non scrive alcun file.
4. **P4 — lo scoring, scritto ORA.** Con i **criteri pre-registrati** (P6) nel
   suo docstring, datato in git prima di ogni partita 2026-27.

**Due errori veri trovati nella versione precedente dello script**, che
avrebbero prodotto una previsione sbagliata *congelata* — cioè non più
correggibile senza invalidare il test:

- **le neopromosse erano dedotte con la funzione sbagliata.** Chiamava
  `promoted_teams(allm, ultima_stagione)`, che restituisce le promosse **nel
  2025-26** — è il difetto che la Fase 128 aveva appena diagnosticato, e stava
  nel codice, non solo in teoria;
- **il motore era quello della Serie A per tutti.** Passava `draw_balance=True`
  e `DP_THETA_DC` a ogni lega, mentre φ(|λ−μ|) e router θ sono misurati utili
  **solo in Serie A** (Fase 79/101). Era lo stesso bug corretto in `predict.py`
  alla Fase 101, sopravvissuto qui.

**Controllo di sanità, non validazione.** Le medie previste stanno addosso
alle frequenze storiche di 9 stagioni su tutte e 5 le leghe (gol/partita: 3.10
vs 3.12 in Bundesliga, 2.81 vs 2.84 in Premier, 2.80 vs 2.74 in Ligue 1, 2.68
vs 2.58 in Liga, 2.57 vs 2.72 in Serie A). **Non dimostra nulla** sulla bontà
delle previsioni — sono 48 partite specifiche, non un campione casuale — ma
uno scarto grosso qui avrebbe segnalato un guasto, e non c'è.

**Lo scoring è stato eseguito end-to-end prima di servire.** Con risultati
sintetici (i gol veri della 1ª giornata 2025-26 accoppiati alle partite
congelate): la pipeline gira, scrive l'artefatto e registra il run. I numeri
prodotti sono **privi di significato** per costruzione, quindi il registro è
stato **ripristinato** e l'artefatto cancellato: un numero finto in
`runs.jsonl` è esattamente il finto pieno della R6. Uno scoring che gira per
la prima volta a fine agosto, su dati irripetibili, è un turno perso.

**📐 Il modello in dettaglio.** Nessuna matematica nuova — è il DC della Fase
4b/4d col motore per-lega della Fase 92-bis. Le tre formule che decidono i
numeri congelati, verificate contro il codice:

*(a) Tassi attesi* (`dixon_coles.expected_goals`):

```
λ = exp( att[casa] − dif[ospite] + γ )        μ = exp( att[ospite] − dif[casa] )
```

*(b) Verosimiglianza pesata e shrinkage* (`_fit_counts`), con `w(g)` il peso
della Fase 128 e `p` il bersaglio:

```
w(g) = 0.5^(g/365)
obiettivo = − Σ_i w(g_i)·ℓ_i(att, dif, γ)  +  s·Σ_t [ (att_t − p^att_t)² + (dif_t − p^dif_t)² ]
```

con `s = 1.5` (shrinkage, tutte le leghe) e `p^att_t = −δ`, `p^dif_t = +δ` per
le **14 neopromosse dichiarate**, `0` per tutte le altre. δ è per-lega:
0.23 / 0.33 / 0.22 / 0.28 / 0.19.

*(c) Il routing per-mercato* (`price_markets`), che dalla coppia (λ,μ) produce
i 26 mercati. Le costanti vengono da `market_engine(lega)` e **non sono le
stesse ovunque**: Serie A `φ0=0.30, κ=1.5, θ_DC=1.138`; le altre quattro
`φ0=0, κ=0, θ=None` — motore **liscio**. È la differenza che la versione
precedente dello script ignorava.

**Onestà su cosa questo NON è.** Non è ancora un risultato: è una previsione.
Il valore si vedrà solo dopo il fischio, e con 48 partite la potenza contro il
mercato è **~10%** (Fase 98) — questa giornata **collauda il protocollo**, non
conclude. La conclusione onesta contro il mercato arriva a ~574 partite, cioè
~12 giornate su 5 leghe: fine ottobre.

**Lezione.** *Una scadenza va interrogata, non solo rispettata.* «Congelare
entro il 14 agosto» è stato per settimane un vincolo trattato come dato,
mentre la domanda giusta era **da cosa dipende ciò che congelo**: la risposta
(solo da dati fermi a maggio) rendeva la scadenza aggirabile in un pomeriggio.
E il corollario: **il codice che gira una volta sola va fatto girare due
volte** — la prima a vuoto, su dati finti, e prima che serva.

---

## Fase 130 — Le quote si muovono? Quasi no. E il movimento più grande era un libro rotto

**Obiettivo.** Rispondere a una domanda diretta dell'utente — «stiamo davvero
raccogliendo le quote, e vediamo come cambiano nei giorni?» — guardando
l'archivio invece di fidarsi del fatto che il workflow sia verde.

**Risposta breve: sì raccogliamo, no non si muovono (ancora).** Otto file dal
28/07 al 01/08, 48 partite, 3 mercati (1X2, O/U 2.5, GG/NG). Sui 144 contratti
1X2 seguiti su ≥2 giorni il movimento mediano è **0.30 punti percentuali**, e
il **70% è fermo sotto 0.5pp**. Fra il 28 e il 30 luglio parecchi libri sono
identici **alla quinta cifra**: in off-season profonda nessuno scambia.

**Ma la prima misura era sbagliata, e il modo in cui lo era conta.** Chiave
iniziale: il *nome* della partita. Risultato: 233 serie invece di 144, perché
**Smarkets ha rinominato 40 eventi su 49** fra il 30 e il 31 luglio — da nomi
formali (`AS Roma vs ACF Fiorentina`) a nomi brevi (`Roma vs Fiorentina`),
un cambio di convenzione in blocco. Rifatto su `event_id`, che non cambia.

Due conseguenze operative:
- **la chiave stabile è `event_id`**, e il congelato del M1 la porta con sé;
- **gli alias vanno tenuti su ENTRAMBE le convenzioni.** Dei 160 nomi distinti
  mai comparsi nell'archivio, **15 non si agganciavano** — tutti della forma
  lunga (`Inter Milano`, `Juventus Turin`, `Malaga CF`, `Hull City`…). Oggi
  innocuo, perché la borsa usa i brevi; ma la borsa ha cambiato convenzione
  **una volta in quattro giorni**, e il momento in cui il join deve funzionare
  è l'ora prima del fischio, quando nessuno guarda. Aggiunti tutti e 15, senza
  togliere i nuovi. E un test enumera **tutti** i nomi dell'archivio a ogni
  esecuzione della suite: il giorno del prossimo rinominamento si rompe la
  suite, non il test prospettico.

**Il movimento più grande non era informazione.** Angers–Lille, vittoria
Angers: da 16.7% a 35.6%, **+18.9pp** — dieci volte il secondo. Guardando il
libro invece del solo punto medio: il 01/08 il banco stava a **0.1562** e il
puntatore a **0.5556**. Uno spread di **40 punti percentuali**: il "medio" del
35.6% non è il prezzo di niente, è la metà di un intervallo vuoto.

**Da lì, la misura che serviva davvero: quanto è usabile il libro.** Sul file
del 01/08 (partite a 15-27 giorni dal fischio):

| statistica | valore |
|---|--:|
| righe con libro a **due lati** | 277/336 (**82%**) |
| spread **mediano** | **0.082** |
| righe con spread > 10pp | 44 (16%) |
| partite con 1X2 completo e spread ≤5pp **su tutti e tre** | **28/48** |

E non è uniforme fra leghe — spread mediano 1X2:

```
premier_league  0.010     la_liga  0.031     serie_a  0.031
ligue_1         0.056     bundesliga  0.104
```

Lo **stesso ordinamento per liquidità** della Fase 53, misurato su una fonte
diversa e a otto anni di distanza.

**Cosa ne consegue per il Modello 2** — e va fissato **ora**, prima di sapere
quali partite ne beneficiano, altrimenti la soglia la sceglie il risultato:
- M2 calcolato per ogni partita con libro a due lati, **registrando lo spread**
  di ogni contratto;
- **analisi primaria** solo sulle partite con spread ≤5pp su tutti i contratti
  che entrano nell'inversione; le altre **secondarie**, riportate a parte;
- partita senza libro a due lati alla chiusura → **niente M2**, scorata solo
  M1, **dichiarandolo** nel conteggio (R6).

⚠️ Tutto questo è misurato **oggi**, a 15-27 giorni dal fischio. Che il libro
si stringa a ridosso del calcio d'inizio è **plausibile e non verificato**: è
una verifica da fare al primo turno, non un'assunzione. Se non si stringesse,
il M2 sarebbe di fatto un test su Premier, Liga e Serie A.

**📐 Il modello in dettaglio.** Nessun modello nuovo: due definizioni e una
soglia, che però decidono quali dati entrano.

Dal libro degli ordini (`fetch_smarkets_outrights.book_price`, riusato dal
raccoglitore per-partita), con `b` = miglior banco e `a` = miglior puntatore,
entrambi **probabilità** 0-1:

```
p_mid    = (b + a) / 2          definito solo se esistono ENTRAMBI i lati
spread   = a − b
```

Il punto medio è uno stimatore del prezzo "vero" con errore limitato da metà
spread:

```
|p_mid − p_vero|  ≤  spread / 2
```

Da cui la soglia dichiarata: `spread ≤ 0.05` implica un errore ≤ **2.5pp** su
ciascuna probabilità. Non è una costante universale — è il livello sotto il
quale l'incertezza del prezzo resta più piccola degli effetti che il progetto
misura (il gap col mercato sull'1X2 vale 0.0167 di log-loss, e le correzioni
del router il terzo decimale). Sopra i 5pp l'incertezza del *dato* supererebbe
l'effetto *studiato*, e il confronto misurerebbe il libro, non il modello.

Sul caso Angers: `b = 0.1562`, `a = 0.5556` → `spread = 0.3994`, cioè un
errore possibile di **±20pp** su una probabilità del 35.6%. Il numero esiste;
il prezzo no.

**Lezione.** *Il movimento più grande in una serie storica di prezzi è quasi
sempre un difetto della serie, non un evento del mondo.* La cosa giusta da
guardare per prima non era la variazione ma il **libro che la produce** — e la
stessa colonna che rendeva sospetto il caso singolo (lo spread) è quella che
poi ha dato la regola generale. Corollario metodologico: **quando una fonte
esterna cambia una convenzione, la difesa non è inseguirla ma tenere entrambe
le versioni e mettere un test che enumera tutto lo storico** — inseguire
significa accorgersene la volta in cui è troppo tardi.
## Fase 131 — Le statistiche di squadra per periodo: il primo dato che separa i due tempi

**Obiettivo.** Verificare e integrare sette file consegnati dall'utente —
statistiche di **squadra** per partita, divise in **Totale / 1° tempo /
2° tempo**, per tutte e 5 le leghe, stagione 2025-26, fonte diretta.it
(Flashscore), dato a monte di Opta. Sono l'altra metà del dato per giocatore
entrato alla Fase precedente, e portano una cosa che il progetto non aveva
mai avuto: la **scomposizione temporale** di 45 metriche.

**Ragionamento / ipotesi.** Il progetto ha un residuo aperto e localizzato
(Fasi 96/99): *«il secondo tempo è mal calibrato mentre il primo, che passa per
lo stesso codice, non lo è → è game-state, e chiede un modello a due stadi»*.
Fino a qui ogni metrica del repo era di fine partita, quindi quel residuo non
era nemmeno osservabile su altro che i gol. L'ipotesi da verificare non era
«questi dati sono utili» ma, prima, «questi dati sono veri e lo split è
genuino».

**Alternative considerate sulla verifica.** (a) Fidarsi del foglio «Note», che
dichiara la propria verifica interna. Scartata: la fonte dichiara di aver
controllato «1T + 2T = Totale», che è un controllo **che non può fallire** se il
secondo tempo è calcolato come (Totale − 1T) — ed è esattamente ciò che i dati
mostrano. Una tautologia non è una verifica (R7). (b) Verificare contro il
per-giocatore già in repo. Insufficiente: è la **stessa fonte**, e sulle
metriche continue non ricostruisce nulla (xG combacia in 55/758 celle).
(c) **Scelta**: verificare contro **football-data.co.uk**, che ha le stesse
metriche di conteggio misurate da un fornitore diverso, e — decisivo — ha
`HTHG/HTAG`, cioè **i gol veri dell'intervallo**. Due workflow da 14 agenti
ciascuno (7 dimensioni + 7 confutatori avversariali che riscrivono gli script
da zero), poi i controlli portanti ri-eseguiti a mano.

**Risultato — i dati reggono.**

| controllo (5 leghe, sola stagione regolare) | esito |
|---|---|
| join allo snapshot (data + squadre) | **3.504/3.504 team-partita** |
| risultato coerente con lo snapshot | **3.504/3.504** |
| additività `1T + 2T (+Suppl) = Totale` | **137.124/137.124 celle**, 0 violazioni |
| gol del **1° tempo** dedotti vs `HTHG/HTAG` | **3.444/3.502 = 98,34%** |
| gol del **2° tempo** dedotti vs `FT−HT` | **3.428/3.502 = 97,89%** |
| conteggi vs football-data (6 metriche) | 97,7% – 99,7%, **scarto medio ~0** |

Lo scarto medio nullo su tutte e sei le metriche dice che **non c'è differenza
sistematica di definizione**: è rumore di raccolta ±1 fra due fornitori. E lo
split **non è invertito**: con le etichette scambiate l'accordo sui gol crolla a
77/380 e 66/380 e compaiono 144 e 167 casi fisicamente impossibili.

**Sei cose trovate che nessuna dichiarazione della fonte diceva.**

1. **Il vuoto è uno ZERO**, non un dato mancante — fino al 94% di NaN su tre
   colonne. Caricarle come mancanti non farebbe sparire dei cartellini:
   farebbe sparire gli **zeri**, gonfiando ogni media. Dimostrato contro
   football-data, non per argomento interno.
2. **La fonte documenta male sé stessa.** Il foglio «Note» della Bundesliga
   dichiara che i supplementari NON sono compresi nel Totale. È **falso**:
   `1T+2T+Suppl = Totale` torna su 39/39 metriche, `1T+2T` su 8 e 7.
3. **Le righe `Play-off` non sono campionato**: 6 partite di spareggio con club
   di seconda divisione, assenti dagli snapshot. In Ligue 1 si **sovrappongono
   per data** al campionato: solo la colonna `Fase` le separa.
4. **Una partita dura 22 minuti e la riga `Totale` sembra una partita
   intera**: Nantes-Toulouse 17/05/2026. ⚠️ *Prima lettura mia sbagliata*:
   l'avevo classificata «causa non accertata», ma `docs/DATI.md` §1-quater
   l'aveva già **risolta il 31/07** — gara **interrotta al 22′** per invasione
   di campo, 0-0 omologato dalla LFP. Il secondo tempo non manca: **non è mai
   stato giocato**, e 146 passaggi in 22 minuti sono normali. Il dato è
   corretto; la trappola è d'uso — quel `Totale` copre 22′ e non 90, cioè la
   **R6 applicata al tempo** invece che al valore. Lezione: prima di dichiarare
   una causa ignota, cercarla nei documenti del repo, dove qualcuno l'aveva
   già chiusa il giorno prima.
5. **`Risultato squadra` ed `Esito` sono di fine partita anche sulle righe di
   periodo** (3.504/3.504 identici): la riga «1° tempo» porta il risultato
   finale. Caso da manuale della R8 — e ne segue che **il punteggio
   all'intervallo non è in questo dataset**.
6. **Due tackle impossibili** (`riusciti` 4 > `totali` 3, `Tackles %` = 133) su
   10.512 righe. Non corretti (R3), non nascosti (R4).

**La lezione di metodo, e non è sui dati.** Dieci confutazioni su quattordici
hanno trovato errori nei **rapporti**, non nei file — e il vizio è quasi sempre
lo stesso: il **denominatore**. Denominatori che mescolano stagione regolare e
play-off (618 = 612+6); un «100%» ottenuto confrontando qualcosa con sé stesso;
un conteggio di *presenza del dato* presentato come verifica di un'identità; una
tolleranza scelta dopo aver visto i dati. Il caso più istruttivo: un rapporto
arbitrava le celle in cui diretta e football-data divergono usando come
«testimone indipendente» la colonna `Parate` — che è **di diretta**. Il
confutatore ha costruito il controllo negativo mancante (perturbare celle
concordi con le stesse magnitudini) e ha misurato che quel testimone favorisce
diretta nel **94,7%** dei casi anche quando l'avversario è indistinguibile per
costruzione: il null non era 0,5 ma 0,947, e il p-value passava da 0,003 a 0,85.
**Un arbitrato con un testimone della parte in causa non è un arbitrato.**

**Cosa è entrato nel repo.** `src/data/team_stats.py` (caricatore con le guardie
di copertura, `join_to_snapshot` che alza sulle orfane, `periodi_affiancati`,
`team_form` R8-safe con `periodo=`), `scripts/registra_raccolta_squadra_diretta.py`
(verifica **prima** di accettare), 5 raccolte in `files/diretta_{lega}_2526/`
(604 KB in tutto), 18 alias italiani in `TEAM_ALIASES`, e
`files/README_statistiche_squadra.md`. **28 test nuovi**. Sul solo ramo di lavoro la suite passava da **1.130 a 1.162**;
dopo il merge con la sessione parallela (Fase 130) i verdi sono **1.163**. Il manifesto si chiama `manifesto_squadra.json` e non `manifesto.json`
per una ragione misurata: `player_stats.raccolte()` cerca `manifesto.json`,
quindi le cartelle con **solo** dati di squadra (Bundesliga e Ligue 1) restano
invisibili a quel caricatore invece di farlo fallire su un file che non c'è —
provato che il layout alternativo lo rompe (`2 passed, 15 errors`).

**Cosa NON è stato fatto, e va detto.** Nessuna feature, nessun backtest,
nessun modello li usa. E il limite vero non è la potenza ma la **profondità**:
1.752 partite sono sopra le ~574 della Fase 98, ma sono **una stagione sola**,
quindi un walk-forward multi-stagione non è possibile — la finestra di
addestramento non esiste. Un risultato nullo sarà meno conclusivo di quanto
sembri, e va detto **prima** del test.

### 📐 Il modello in dettaglio

Questa fase non introduce matematica di modello: introduce **due identità sui
dati**, e la seconda è quella che rende utilizzabile lo split.

**(1) Additività dei periodi.** Per ogni metrica di *conteggio* `m`, ogni
squadra `s` e ogni partita `p`:

```
m(s, p, 1T) + m(s, p, 2T) [+ m(s, p, Suppl)] = m(s, p, Totale)
```

verificata in `scripts/registra_raccolta_squadra_diretta.py::verifica` (somma
per `groupby(data, Squadra, Avversario)` su tutti i periodi ≠ Totale, confronto
con tolleranza 0.005) e in `tests/test_team_stats.py::test_additivita_dei_periodi`.
Esito: **137.124/137.124** celle, 0 violazioni.
⚠️ Le 6 colonne percentuale **non** vi rientrano, e non per convenzione: sono
rapporti (`% = riusciti/totali`) e medie (`Possesso`), per cui la somma non è
definita. `COLONNE_NON_ADDITIVE` le elenca, e un test di **segno opposto**
verifica che continuino a NON sommare — così nessuno «sistema» il primo test
allargando l'elenco delle additive.
⚠️ La tolleranza 0.005 non è scelta dopo aver visto i dati: è il mezzo passo
dell'ultima cifra pubblicata dalla fonte (2 decimali su xG, xGOT, xA). Sui
conteggi interi è irrilevante.

**(2) Deduzione dei gol per periodo.** La fonte pubblica `Gol evitati`, che è
definito come

```
Gol evitati(s, p, π) := xGOT affrontato(s, p, π) − gol subiti(s, p, π)
```

da cui, invertendo, la sola via per avere i gol di un periodo in un dataset che
**non ha una colonna gol**:

```
gol subiti(s, p, π) = xGot affrontati(s, p, π) − Gol evitati(s, p, π)
gol segnati(s, p, π) = gol subiti(avversario(s), p, π)
```

implementata in `src/data/team_stats.py::gol_dedotti`, con `round(0)`.

*Perché lo scarto è a senso unico.* Un **autogol** è un gol subito che non nasce
da un tiro dell'attaccante, quindi **non entra nell'xGOT** di chi ne beneficia:
il termine `xGOT affrontato` non lo contiene, mentre `gol subiti` sì. Ne segue,
per costruzione,

```
xGot affrontati − Gol evitati  =  gol subiti − autogol_a_favore  ≤  gol subiti
```

cioè la deduzione può solo **sottostimare**, mai sovrastimare. È una previsione
falsificabile, non una giustificazione a posteriori: misurata contro
`HTHG/HTAG` su 7.004 confronti (2 periodi × 3.502 lati), la distribuzione dello
scarto è `{0: 6.872, −1: 131, −2: 1, +1: 0}`. **Nessun caso positivo su 7.004**,
come l'identità impone. Il test
`test_gol_dedotti_possono_solo_sottostimare` fissa proprio il segno, non il
tasso: un tasso è un numero, un segno è una struttura.

*Perché non è sempre un intero.* `Gol evitati` è pubblicato a 2 decimali, quindi
la differenza eredita l'errore di arrotondamento di due quantità continue: su
Cagliari-Udinese 09/05/2026 dà 2,07 invece di 2. L'arrotondamento assorbe, ma
l'identità va dichiarata **approssimata**, non esatta.

**(3) La forma sicura (R8).** `team_form` usa

```
forma(s, k) = media[ m(s, k−W) … m(s, k−1) ]      W = window, k−1 escluso l'oggi
```

realizzato come `groupby("Squadra")[cols].shift(1).rolling(W, min_periods=1).mean()`.
Lo `shift(1)` **precede** il `rolling`: invertirli includerebbe la partita in
corso, il numero resterebbe plausibile e il modello sarebbe inservibile. È il
motivo per cui il test non confronta con un valore atteso ma con **entrambi** i
candidati — la media su `0..k−1` e quella su `0..k` — e pretende che coincida
con la prima **e differisca** dalla seconda.

---

## Fase 133 — I gol all'intervallo entrano negli snapshot: il dato che mancava al modello a due stadi

**Obiettivo.** Rispondere a tre domande dell'utente sulla Fase 131 («i gol
all'intervallo si recuperano? qual è il problema dei tiri? ci sono altri
problemi?») e, dove la risposta era «sì», farlo.

**Il buco, e perché era più grande di quanto sembrasse.** La pista 6-bis — il
modello a due stadi, «il residuo vivo del progetto» — ha bisogno di **una sola
variabile di stato**: il punteggio all'intervallo. Quel numero non era in
nessuna tabella. Non negli snapshot (`data/*_matches.csv` non aveva colonne di
primo tempo); non nelle statistiche di squadra appena inserite (`Risultato
squadra` è il **finale** anche sulla riga «1° tempo», regola R8); e la Fase 98 se
lo rileggeva ogni volta dai grezzi, **in tre modi diversi a seconda della lega**.

**Alternative considerate.** (a) **Dedurlo** dall'identità `xGot affrontati −
Gol evitati` del dataset nuovo: funziona al 98,3%, ma è una *stima*, e per le
regole del progetto (§5) una stima vive in `data/estimates/`, non negli
snapshot — e coprirebbe solo le 1.752 partite del 2025-26. (b) **Prenderlo
vero** da `HTHG/HTAG` di football-data, che è **la stessa fonte da cui gli
snapshot derivano già i gol finali**: non un innesto di terzi, e copre **tutte e
16.111 le partite** delle 9 stagioni. Scelta la (b): quando il dato vero esiste,
non si stima (R5, passo 4).

**Risultato.** Due colonne nuove, `home_goals_ht` e `away_goals_ht`, su tutti e
5 gli snapshot (38 → 40 colonne), scritte da
`scripts/aggiungi_gol_intervallo.py`. **Nessuna cella esistente è stata
toccata**: è un'aggiunta, non una correzione.

| lega | partite | join | gol finali coerenti | f (gol nel 1° tempo) |
|---|--:|:--:|:--:|--:|
| Serie A | 3.420 | 3.420/3.420 | 3.420/3.420 | **0,4365** |
| Premier | 3.420 | 3.420/3.420 | 3.420/3.420 | **0,4464** |
| La Liga | 3.420 | 3.420/3.420 | 3.420/3.420 | **0,4356** |
| Bundesliga | 2.754 | 2.754/2.754 | 2.754/2.754 | 0,4482 |
| Ligue 1 | 3.097 | 3.097/3.097 | 3.097/3.097 | 0,4461 |
| **totale** | **16.111** | **16.111/16.111** | **16.111/16.111** | **0,4425** |

⭐ **La verifica più forte non l'ho costruita io: era già pubblicata.** Le tre
frazioni in grassetto — 0,4365 / 0,4464 / 0,4356 — **coincidono alla quarta
cifra** con quelle che la Fase 96 aveva misurato per le stesse tre leghe. Non è
una coincidenza fortunata: è la prova che il join ha agganciato le righe giuste,
ottenuta ri-derivando per un'altra strada un numero che il repo aveva già
scritto. Su 5 leghe f = **0,4425**, dentro l'IC [0,4338, 0,4458] della Fase 96
allargato al campione nuovo.

**Un buco solo, dichiarato: Union Berlin-Bochum 14/12/2024.** È la partita del
caso **R1** — 1-1 sul campo, 0-2 assegnato dal DFB — e football-data **non ha
l'intervallo** per quella gara. Il valore resta vuoto (`Int64` nullable) invece
di essere inventato: un buco dichiarato è innocuo, il finto pieno no (R6).
Nota di metodo: lo stesso caso fa **divergere** i gol finali fra snapshot (1-1)
e fonte (0-2), e il controllo «i gol finali devono coincidere» lo avrebbe fatto
fallire. La soluzione non è stata incidere l'eccezione nel codice ma **leggerla
da `data/correzioni_dichiarate.csv`**: se un domani ne comparisse un'altra, lo
script la conosce già.

**Le altre due risposte, che non hanno prodotto codice.**

1. **I tiri.** `Tiri totali` ha **due** partizioni indipendenti: per esito
   (`in porta + fuori + fermati`) e per zona (`area + fuori area`). La prima
   tiene **10.510/10.510**, la seconda **10.500/10.510**. Il difetto è quindi
   solo nella scomposizione per zona, in 5 squadra-partita su 3.504 (0,14%), a
   livello di **periodo**, e si propaga al Totale. La prova è l'Espanyol
   09/05/2026: 1T `+1` e 2T `−1` si **cancellano** e il Totale torna giusto.
   **Non è riparabile**: sappiamo che la somma per zona dovrebbe fare
   `Tiri totali`, ma non *quale* zona — servirebbe il dato tiro-per-tiro, e
   attribuirlo a occhio è ciò che la R3 vieta. Contro football-data sulle 4
   righe-Totale contese, `Tiri totali` vince 3/4 e la zona 1/4: nemmeno
   l'arbitro esterno è netto, mentre internamente `Tiri totali` è corroborata
   da una seconda partizione su **tutte** le righe e la zona no.
2. **Altri problemi**: 15 vincoli logici, 12 puliti. E **due dei tre allarmi
   erano miei, non dei dati** — è il punto che vale la pena ricordare:
   - «1T > Totale» in 2.335 celle: tutte e sole su `Gol evitati`, che può essere
     **negativa** (min −3,31). Se un tempo vale +0,67 e l'altro −0,50, il
     Totale 0,17 è minore del primo tempo. Aritmetica corretta, **vincolo mio
     sbagliato**;
   - 43 righe con tiri in porta e `xGOT = 0,00`: **arrotondamento**, non
     segnaposto. 42 su 43 hanno **un solo** tiro in porta, l'xG medio è 0,507
     contro 0,930 generale, e in **43/43** non è stato segnato nulla — un
     segnaposto avrebbe gol associati (è il caso R5 già pagato dal progetto);
   - 3 righe con `Grandi occasioni > Tiri totali`: anomalia vera ma coerente
     con la definizione Opta (una grande occasione può non finire in tiro).

**Una correzione a me stesso.** Nella Fase 131 avevo classificato
Nantes-Toulouse 17/05/2026 come «causa non accertata». Era sbagliato: il repo
l'aveva **già risolta il 31/07** (`docs/DATI.md` §1-quater) — gara interrotta al
22′ per invasione di campo, 0-0 omologato dalla LFP. Il secondo tempo non manca:
non è mai stato giocato. Corretto in quattro punti. **Lezione: prima di
dichiarare ignota una causa, cercarla nei documenti del repo** — dove qualcuno
l'aveva chiusa il giorno prima.

### 📐 Il modello in dettaglio

Questa fase non introduce matematica di modello: sposta un dato e ne verifica
l'identità. Le due formule in gioco sono entrambe di **controllo**.

**(1) Il vincolo che rende falsificabile l'import.** Per ogni partita `p`:

```
HTHG(p) ≤ FTHG(p)        e        HTAG(p) ≤ FTAG(p)
```

— un intervallo non può contenere più gol del finale. Verificato su
16.110/16.110 partite con l'intervallo (la 16.111ª è il NaN dichiarato).
Il controllo *portante* è però un altro, ed è quello che dimostra di aver
agganciato la riga giusta invece di una qualsiasi che combacia per data:

```
FTHG(fonte) == home_goals(snapshot)   e   FTAG(fonte) == away_goals(snapshot)
```

su **16.111/16.111**, con l'unica eccezione **letta dal registro** delle
correzioni (R1, Union Berlin-Bochum). Un join che non verifica i gol finali
può agganciare la partita sbagliata e nessun conteggio se ne accorge.

**(2) La frazione f, e perché la sua riproduzione è una prova.**

```
f = Σ_p [ HTHG(p) + HTAG(p) ]  /  Σ_p [ FTHG(p) + FTAG(p) ]
```

È la **stessa** grandezza che la Fase 98 usa per ri-scalare i tassi nei mercati
Tier 3 (`M_1T = score_matrix(f·λ, f·μ, …)`), lì misurata leggendo i grezzi lega
per lega. Ricalcolata dalle colonne nuove dà **0,4365 / 0,4464 / 0,4356** per
Serie A / Premier / La Liga: le stesse quattro cifre già pubblicate. Due strade
indipendenti che producono lo stesso numero sono una verifica; una strada sola
che produce un numero plausibile non lo è.
Le due leghe mai misurate prima danno **0,4482** (Bundesliga) e **0,4461**
(Ligue 1), cioè in alto nella forchetta: il valore a 5 leghe sale a
**0,4425** — dentro l'IC della Fase 96, e da ri-misurare con il suo intervallo
prima di usarlo come costante per-lega (R7).

---

## Fase 134 — La borsa rinomina le squadre e il raccoglitore resta verde: il join che si è rotto in silenzio

**Obiettivo.** Correggere un difetto **in corso** trovato dal censimento delle
fonti: il join fra il listino Smarkets e le nostre 96 anagrafiche di club era
passato da 96/96 a 32/96, e nessuno se n'era accorto.

**Come è stato trovato, e perché conta.** Non da un test rosso né da un errore:
da un censimento che guardava un'altra cosa. Il difetto era **invisibile per
costruzione** — il giro giornaliero usciva verde, scriveva il suo file, e
l'unico sintomo era che il meteo veniva marcato `coordinate_mancanti` invece
di essere richiesto. Un campo che vale «buco dichiarato» copriva un guasto.

**La causa.** `scripts/raccolta_giornaliera.py` indicizzava le anagrafiche per
`nome_smarkets` **grezzo** e cercava con il nome **grezzo** del listino. Fra il
30 e il 31/07/2026 Smarkets è passata dai nomi formali ai nomi brevi
(`Deportivo Alaves` → `Alaves`, `FC Augsburg` → `Augsburg`,
`Atletico Madrid` → `Atlético Madrid`). Gli alias per la nuova convenzione
**esistevano già** — la Fase 130 li aveva aggiunti a `TEAM_ALIASES` proprio per
questo rinominamento — ma la raccolta giornaliera non consultava quella mappa.
Il progetto aveva il rimedio in casa e non lo applicava dove serviva.

**Il danno, misurato sull'archivio giorno per giorno:**

| giorno | partite | meteo | orfane |
|---|--:|---|--:|
| 30/07 | 7 | 1 `coordinate_mancanti` | — |
| **31/07** | **0** | **niente** | — |
| **01/08** | 9 | **8/9 `coordinate_mancanti`** | — |
| 02/08 (dopo il fix) | 23 | 2 `coordinate_mancanti` | **0** |

**La correzione, e perché è quella giusta.** Canonicalizzare **entrambi i lati**
con `TEAM_ALIASES` (`_canonico()`): così la convenzione che la borsa usa oggi
diventa irrilevante. Misurato: 96/96, zero orfane. È la stessa scelta della
Fase 128 — la chiave stabile non è la stringa, è il nome canonico — applicata
al punto in cui mancava.

**Ma la correzione non basta, e questa è la lezione.** Un join che si rompe
resta silenzioso finché nessuno lo misura. Aggiunta una **guardia** che conta
le squadre senza anagrafica, le **scrive nel file del giorno**
(`squadre_senza_anagrafica`) e fa uscire il giro **rosso** — ma solo **dopo**
aver scritto, perché le quote e il meteo di oggi non si ri-scaricano domani
(stessa scelta della Fase 127). Due test: uno verifica il join sul listino
vero, l'altro è la **controprova con denti** — svuotando la mappa alias il join
deve rompersi (36/46 orfane), altrimenti il test passerebbe sia col rimedio sia
senza e non dimostrerebbe nulla.

**Lezione.** È la terza volta che questo progetto paga lo stesso schema: la
Fase 118 (un run verde che non raccoglieva niente), la Fase 127 (una lega uscita
dalla raccolta in silenzio) e ora questa. Il denominatore comune non è la rete
né l'API: è che **un valore legittimo per un caso legittimo** (`fuori_finestra`,
`coordinate_mancanti`) veniva usato anche quando la causa era un guasto. La
contromisura non è un controllo in più: è che ogni stato «non ho il dato»
dichiari **perché** non ce l'ha, e che il perché sia distinguibile.

### 📐 Il modello in dettaglio

Nessuna matematica di modello: è un difetto di join. La formula è l'invariante
che il codice ora impone.

Sia `A` l'insieme delle anagrafiche e `L` il listino del giorno. Prima:

```
join(L, A) = { (l, a) : l.nome == a.nome_smarkets }        # stringa grezza
```

fragile perché `l.nome` è scelto dal fornitore e cambia. Dopo:

```
c(x)       = TEAM_ALIASES.get(x, x)                        # nome canonico
join(L, A) = { (l, a) : c(l.nome) == c(a.nome_smarkets) }
```

`c` è **idempotente** (`c(c(x)) = c(x)`, verificato: nessun valore di
`TEAM_ALIASES` è a sua volta una chiave), quindi applicarla a entrambi i lati è
sicuro e non introduce catene. L'invariante che la guardia verifica è

```
∀ s ∈ squadre(L) :  (lega(s), c(nome(s))) ∈ A
```

e la sua violazione è **contata**, scritta nel file del giorno e propagata al
codice d'uscita. Il numero che la fa scattare non è una soglia scelta: è
**zero**, perché il listino e le anagrafiche coprono per costruzione le stesse
96 squadre delle 5 leghe.

---

## Fase 135 — Il listino intero: da 6 mercati a 110, e il batching che lo rende possibile

**Obiettivo.** Applicare la regola §5-ter («raccogliere tutto») al dato più
deperibile che il progetto abbia: i prezzi di mercato prima del fischio.

**Il fatto di partenza.** Smarkets espone **110 mercati per partita** (56 tipi
distinti, sondati dal vivo). Il cron ne raccoglieva **3** nel giro giornaliero e
**6** in quello di chiusura. Fra i 104 buttati: `corners_handicap` (×4),
`cards_handicap_three_way` (×2), `first_half_*` (×13), `second_half_*` (×12),
`half_full`, `clean_sheet`, `win_to_nil`, `winner_and_*`. Cioè **esattamente i
mercati che il progetto prezza senza avere una quota contro cui misurarsi** —
i conteggi delle Fasi 96/98/125, il Tier 3 della Fase 98, e le famiglie che
`CLAUDE.md` §1.8 dichiara **scoperte**.

**Il flag `--tutti-i-mercati` esisteva già, e non funzionava.** Non per un bug:
per il costo. `quote_partita` faceva **due chiamate API per mercato**
(contratti + quote), cioè `1 + 110×2 = 221` richieste per partita. Misurato:
il giro su **sei** partite è stato ucciso dal timeout a **15 minuti senza
scrivere nulla**. Con la finestra di chiusura su un sabato di punta sarebbero
2.200 richieste per giro orario: impossibile.

**La correzione, e perché è quella giusta.** L'API accetta **ID separati da
virgola** sia su `/contracts/` sia su `/quotes/`. A lotti di 20 le richieste per
partita passano da **221 a 13**: **17 volte meno**. Lo stesso giro che moriva di
timeout ora chiude in **1m27s** e scrive 2.056 righe.

⚠️ La risposta di `/quotes/` ha **due forme**: annidata per `market_id` con un
ID solo, **piatta per `contract_id`** a lotti. Verificato dal vivo su entrambe.
`_libri_per_contratto()` le distingue **guardando la forma**, non contando gli
ID richiesti — così il prossimo cambio dell'API non richiede di ricordarselo.

**Equivalenza dimostrata prima di adottare.** Il percorso in batch e quello
per-mercato producono **le stesse 30 righe su 30**, stessi prezzi, stesso banco,
stesso puntatore. Un'ottimizzazione che cambia i numeri non è un'ottimizzazione.

**Il difetto che l'estensione ha scoperchiato.** Alla prima raccolta completa i
mercati risultavano **360 "tipi" su 6 partite** invece di ~100. Causa:
l'etichetta veniva slugificata dal **nome visualizzato**, che contiene i nomi
delle squadre — `alaves_0_5_corners_getafe_0_5_corners`. Un archivio così è
illeggibile da qualunque raggruppamento: non si può chiedere «l'handicap corner»
attraverso le partite. L'API espone `market_type.name` (+ `param`), che è
stabile: adottato. Risultato **102 tipi**, di cui **96 comuni a tutte e sei** le
partite, e **zero nomi squadra** nelle etichette.

**Cosa è stato cambiato nel cron.** Il giro di **chiusura** (`--entro-ore 2`,
orario) passa a `--tutti-i-mercati`. È il momento in cui il prezzo vale di più
ed è irrecuperabile: dopo il fischio non esiste. Costo misurato: 343
righe/partita × 484 byte = **~1,6 MB** in un sabato con 10 partite in finestra.
Il giro **giornaliero** resta sui 3 mercati principali — decisione **da
prendere**, non chiusa: a listino intero costerebbe ~7,8 MB/giro, cioè ~2 GB di
archivio a stagione (o ~110 MB comprimendo, ma il formato dell'archivio
cambierebbe e più di un lettore glob-a `*.json`).

**Lezione.** Un flag che esiste e nessuno usa non è una funzionalità: è
un'ipotesi non verificata. `--tutti-i-mercati` era in `argparse` dalla Fase 116,
e la prima volta che qualcuno l'ha eseguito davvero è morto di timeout — e ha
prodotto etichette inutilizzabili. **Il codice non provato non è codice che
funziona: è codice di cui non sappiamo niente.**

### 📐 Il modello in dettaglio

Nessuna matematica di modello. La formula è il costo, ed è quella che decide.

Sia `M` il numero di mercati per partita e `L` la dimensione del lotto. Le
richieste per partita sono:

```
senza batching:   R = 1 + 2·M                    = 1 + 2·110 = 221
con batching:     R = 1 + 2·ceil(M / L)          = 1 + 2·⌈110/20⌉ = 13
riduzione:        221 / 13 = 17,0×
```

Con il throttle dichiarato del client (`_THROTTLE = 0.35 s`, l'API limita a
~3/s) il tempo per partita passa da `221 × 0.35 ≈ 77 s` a `13 × 0.35 ≈ 4.6 s`.
Misurato end-to-end su 6 partite: **86,7 s**, cioè **14,5 s/partita** — più dei
4,6 teorici perché il throttle non è l'unico costo (latenza di rete, parsing),
ma dello stesso ordine. Il calcolo a priori e la misura concordano; è il
controllo che dice che il modello di costo è quello giusto.

Il peso dell'archivio, misurato e non stimato:

```
righe/partita = 343        (contratti totali sui mercati esposti)
byte/riga     = 484        (973 KB / 2.056 righe)
gzip          = 19,6×      (973 KB -> 50 KB)
```

da cui il costo del regime di chiusura (partite in finestra `p`):

```
peso(p) = 343 · 484 · p byte ≈ 0,166 MB · p
```

— 1,6 MB con `p = 10`. E quello di un ipotetico giornaliero a listino intero,
`p ≈ 48`: **7,8 MB/giro**, cioè ~2 GB su una stagione di ~280 giri. È il numero
che rende la decisione sul giornaliero una scelta e non un automatismo.

---

## Fase 136 — Anche il giro giornaliero prende tutto, e l'archivio si comprime

**Obiettivo.** Decisione dell'utente: *«il giro giornaliero facciamolo su tutti
i mercati»*. Cioè applicare la regola §5-ter anche al regime di lungo raggio,
non solo alla chiusura (Fase 135).

**Il problema che la decisione porta con sé, misurato.** Il lungo raggio
raccoglie **tutte le partite esposte** — 48 al 28/07, e in stagione di più —
per **343 righe a partita**: ~16 MB per giro, cioè **oltre 4 GB** su una
stagione di ~280 giri. In un repo git ogni file è un oggetto nuovo: non è una
cartella che cresce, è una storia che cresce.

**La soluzione non è raccogliere meno.** È comprimere: **gzip toglie 20,3×**
sullo stesso identico contenuto — misurato, 978 KB → 48 KB su 2.056 righe.
~230 MB su una stagione intera, che è l'ordine di grandezza che `newseason.md`
aveva già messo in conto. È la stessa scelta già fatta per i dati diretta.it
(868 KB contro 29 MB di `.xlsx`).

**Ma un formato nuovo non deve rendere illeggibile ciò che c'è.** L'archivio
già raccolto è in `.json` semplice. Da qui `src/data/smarkets_archive.py`:
l'unico posto dove la doppia estensione è un problema, con `snapshots()`,
`leggi()` e `scrivi()`. Il `mtime=0` nel gzip non è un dettaglio: senza,
due esecuzioni con gli stessi dati darebbero byte diversi e git vedrebbe una
modifica che non c'è.

**⭐ Il difetto che ho introdotto e corretto nello stesso lavoro.** Portando la
raccolta giornaliera sul modulo nuovo, le ho fatto leggere `ultimo()` — il file
più recente. Il calendario del giorno è passato da **23 partite a 6**: perché
il file più recente era un giro di *chiusura* (finestra 2 ore, una lega sola).

È **esattamente** l'inciampo che poche ore prima aveva fatto cadere due test di
`test_nomi_smarkets_2627.py`, e l'avevo appena corretto lì. L'ho re-introdotto
altrove nello stesso pomeriggio. La correzione vera non era il test: era che
**«l'ultimo file» e «il listino» non sono la stessa cosa**, e finché il codice
non lo dice esplicitamente ognuno ci ricasca. Ora esiste
`ultimo_listino_completo()`, che cerca l'ultimo snapshot con **tutte e cinque**
le leghe e alza con un messaggio esplicito se non lo trova — e lo usano sia la
raccolta giornaliera sia i test.

**Lezione.** Un difetto corretto in un punto non è un difetto corretto. Finché
la cosa sbagliata resta **facile da scrivere**, torna: qui è tornata dopo tre
ore, per mano della stessa persona che l'aveva appena tolta. Ciò che chiude
davvero il buco non è la correzione, è **rendere la versione giusta più comoda
di quella sbagliata** — una funzione che si chiama come la cosa che serve.

### 📐 Il modello in dettaglio

Nessuna matematica di modello: due numeri di costo, entrambi misurati.

**(1) Il peso dell'archivio.** Con `p` partite esposte per giro, `r = 343`
righe per partita e `b = 484` byte per riga:

```
grezzo(p)     = r · b · p                    ≈ 0,166 MB · p
compresso(p)  = grezzo(p) / 20,3             ≈ 0,0082 MB · p
```

misurato su un file vero: 2.056 righe → 978.384 B grezzi, 48.261 B compressi,
**rapporto 20,27**. Su una stagione (`p ≈ 60` in media, ~280 giri):

```
grezzo     ≈ 0,166 · 60 · 280  ≈ 2.800 MB
compresso  ≈ 0,0082 · 60 · 280 ≈   138 MB
```

**(2) Perché il rapporto è così alto.** Non è fortuna: le righe sono
**quasi identiche fra loro** — stesse chiavi JSON ripetute 2.056 volte, stessi
nomi di lega e di partita, stesse etichette di mercato. Il gzip lavora su
ridondanza, e un JSON tabellare indentato ne ha moltissima. È anche il motivo
per cui il rapporto **crescerà** con `p`: più partite nello stesso file, più
ripetizione. I 20,3× misurati su 6 partite sono quindi un **limite inferiore**
per i file di stagione.

---

## Fase 137 — I guardiani mancanti: tre difetti che nessun test poteva vedere

**Obiettivo.** Agire sul primo giro di caccia agli errori (workflow di 13 agenti,
richiesta utente: *«cerca errori, vedi cosa potremmo fare dopo, prova a trovare
spunti interessanti»*). Due difetti erano marcati **bloccanti**. Il compito qui
non era crederci: era **verificarli** — il primo giro aveva già prodotto almeno
un'affermazione falsa, smontata ri-eseguendo il conto.

**Ragionamento.** I due difetti bloccanti sembravano scollegati. Non lo sono: hanno
la **stessa forma**. In entrambi i casi esiste una cosa giusta nel repo (due colonne
di dati; una formula corretta) e **nessun meccanismo che la tenga giusta**. Il
guardiano manca, quindi il difetto non è «c'è un errore» ma «un errore non
verrebbe visto». È la categoria peggiore, perché il repo appare sano fino al giorno
in cui qualcuno esegue il comando sbagliato.

### Difetto 1 — un `--refresh` cancellava i gol all'intervallo

**Verificato, non creduto.** `grep -rln goals_ht src/ scripts/` rispondeva con **un
file solo**: `scripts/aggiungi_gol_intervallo.py`, cioè lo script della Fase 133.
Nessuna riga sotto `src/` nominava le due colonne. Ma il ramo `--refresh` di
`build_database.py` non arricchisce lo snapshot: lo **ricostruisce da zero** con
`loader.load_league(force_download=True)` e lo riscrive con `write_snapshot`. Le
due colonne non sarebbero rinate, e la lega sarebbe tornata a 38 colonne — senza
un errore, senza un test rosso, senza che nessuno se ne accorgesse fino al
confronto con un'altra lega.

**La correzione è dove doveva stare fin dall'inizio.** `HTHG`/`HTAG` arrivano dalla
**stessa riga grezza** da cui `_normalize` prende già `FTHG`/`FTAG`: nessun join,
nessun rischio di agganciare la partita sbagliata. È una riga in meno di codice di
quella che avevo scritto alla Fase 133, non una in più.

**Verifica di equivalenza.** Ho rifatto il percorso del refresh sui grezzi delle
cinque leghe e confrontato cella per cella con lo snapshot congelato:
**32.222/32.222 celle identiche**, dtype `Int64` compreso, e l'unico `<NA>` è
sempre Union Berlin-Bochum. Le tre vie di costruzione (`build_database --refresh`,
`build_league_snapshot`, `build_new_snapshot`) passano **tutte e tre** da
`_normalize`, quindi la correzione le copre tutte.

**Una cosa che avevo scritto male.** Nel commento del codice avevo attribuito
l'unica cella vuota a Nantes-Tolosa. È **Union Berlin-Bochum**, misurato: e non è
un dettaglio, è il caso R1 — partita sospesa, 1-1 sul campo, 0-2 a tavolino.
football-data ne registra il verdetto in `FTHG`/`FTAG` e lascia l'intervallo in
bianco, perché l'intervallo di una partita mai finita non è un risultato.

### Difetto 2 — `brier_1x2` non aveva un solo test

**Verificato:** `grep -rn brier_1x2 tests/*.py` → **zero riferimenti**.
`log_loss_1x2` ne aveva cinque, ma tutti **relazionali** («il modello buono prende
meno del cattivo»). Sono asserzioni che sopravvivono a qualunque trasformazione
monotona sbagliata: cambiare la base del logaritmo cambierebbe **ogni log-loss mai
pubblicato** dal progetto senza invertire un solo confronto, quindi senza far
fallire nulla.

Non è un dettaglio di igiene: `experiment_log.compute_metrics` — la «fonte di
verità unica» delle metriche (CLAUDE.md §5) — chiama queste due funzioni, e da lì
i numeri finiscono in `runs.jsonl`, nel README e in ogni fase del diario.

**`tests/test_metrics.py`**, 18 test, ogni assert col suo conto a mano nel
docstring. Non è una regressione contro noi stessi (che congelerebbe anche un
errore): è il confronto con la **definizione da manuale**.

### Difetto 3 — la posta in palio presumeva 20 squadre su tutte le leghe

Segnalato dal primo giro come «serio», e confermato: `load_league` chiama
`add_stakes(df)` con i default per tutte e cinque le leghe. Ma la **Bundesliga ha
18 squadre in tutte e nove le stagioni** e la **Ligue 1 è passata a 18 nel
2023-24**. Con `n_teams=20` il calendario teorico è di 38 giornate invece di 34:
quattro **giornate fantasma**, cioè 12 punti di rimonta che non esistono.

**Misurato sugli snapshot veri**, partite con la squadra di casa a posta decisa:

| lega | prima (n=20 cablato) | dopo (dedotto) |
|---|--:|--:|
| Serie A | 160 | **160** |
| Bundesliga | 7 | **114** |
| Ligue 1 | 76 | **112** |

Le sette partite «decise» di tutta la storia della Bundesliga erano il sintomo
visibile, e nessuno l'aveva guardato. In Serie A **non cambia una sola cella**: la
correzione tocca solo dove il numero era sbagliato — che è il modo giusto perché
una correzione si comporti.

**Come, e perché così.** Il numero di squadre si **legge dai dati, stagione per
stagione**, invece di stare in una mappa per lega. Una mappa avrebbe richiesto a
chi aggiunge una lega di ricordarsi un numero, e non avrebbe descritto la Ligue 1,
che il formato l'ha cambiato **a metà storia**. Con `relegated=3` le linee di
classifica restano giuste su entrambi i formati: la 15ª di 18 e la 17ª di 20 sono
tutte e due «l'ultima salva» (in Bundesliga e Ligue 1 il terzo posto a rischio è
lo spareggio, ma il conto delle *posizioni in bilico* è lo stesso).

### Il quarto: un alias che faceva sparire 38 partite

Cercando la copertura delle quote GG/NG di 1xBet (via footiqo), il join si fermava
a **5.339/5.377** righe. Il colpevole: **«Sheffield Utd»** non mappava su
«Sheffield United». Sono le 38 partite dello Sheffield United nella Premier
2019-20 — sparite in silenzio, senza un'eccezione, senza un avviso: solo un
denominatore più piccolo. Con l'alias: **5.377/5.377, 100%**, zero orfani residui.

È la ragione per cui ogni join di fonte esterna deve **dichiarare il proprio tasso
di aggancio col denominatore** invece di limitarsi a non sollevare eccezioni. Un
join che non solleva niente e aggancia il 99,3% ha lo stesso aspetto di uno che
aggancia il 100%.

### ⭐ La prova che i guardiani guardano davvero: 11 mutazioni, 11 uccise

Un test che non fallisce mai non protegge nulla. Ho quindi **mutato apposta** il
codice — su copie, mai sul repo — e verificato che la suite diventi rossa:

| # | mutazione | dove | esito |
|---|---|---|---|
| M1 | Brier senza il quadrato (`abs` al posto di `**2`) | `metrics.brier_1x2` | 5 rossi |
| M2 | log-loss in base 10 | `metrics.log_loss_1x2` | 4 rossi |
| M3 | indici `H` e `A` scambiati | `metrics._OUTCOME_INDEX` | 9 rossi |
| M4 | devig senza normalizzazione | `metrics.devig_1x2` | 1 rosso |
| M5 | clip rimosso | `metrics.log_loss_binary` | 1 rosso |
| M6 | blocco intervallo rimosso | `loader._normalize` | 4 rossi |
| M7 | `HTHG`/`HTAG` invertiti | `loader._normalize` | 2 rossi |
| M8 | `Int64` → `fillna(0).astype(int)` | `loader._normalize` | 3 rossi |
| M9 | `return 0.0` in testa | `DixonColesModel._cov_term` | 3 rossi |
| M10 | segno della covariata non invertito per l'ospite | `expected_goals` | 1 rosso |
| M11 | standardizzazione senza `/s` | `_cov_term` | 1 rosso |

M9 merita una riga a parte: **`_cov_term` non aveva alcun test**, e renderlo inerte
lasciava verde tutta la suite del modello. È il termine da cui passano **tutte** le
covariate di partita della Fase 4c — valore rosa, assenze, riposo, forma, posta in
palio, PPDA, deep, fortuna — cioè ogni esperimento che ha concluso «questo dato non
aggiunge nulla». Se il termine fosse stato inerte, quelle conclusioni avrebbero
misurato soltanto sé stesse. (Non lo era: le mutazioni M10 e M11 mostrano che il
codice fa quello che dice. Ma **non lo sapevamo**, ed è la differenza che conta.)

**Un difetto trovato scrivendo il test, non nel codice.** Il primo confronto fra la
posta in palio calcolata su una stagione sola e su due stagioni insieme falliva su
14 celle su 380. Non era `add_stakes`: `pd.sort_values("date")` **non è stabile**,
quindi due esecuzioni ordinano diversamente le partite dello stesso giorno. I
valori restano attaccati alla loro riga — che è ciò che conta — ma un confronto
**posizionale** falliva per un motivo che con la posta in palio non c'entra nulla.
Il test ora confronta per chiave.

**Risultato.** **1.265 test verdi** misurati sulla suite intera, di cui **29 nuovi**
da questa fase: 18 sulle metriche, 7 sullo schema e la posta in palio, 4 sulle
covariate. Nessun numero pubblicato cambia: il valore della fase è **che non
possano cambiare in silenzio**.

**Lezione.** Le tre correzioni hanno la stessa forma e la stessa morale. Un dato
giusto senza un meccanismo che lo tenga giusto è **giusto per caso**, e il caso
scade al primo comando. Il difetto non era mai nel valore — le due colonne erano
corrette, la formula del Brier era corretta, `_cov_term` era corretto: era
nell'**assenza del guardiano**. E un guardiano si verifica in un modo solo, provando
a fargli passare davanti l'errore che deve fermare.

### 📐 Il modello in dettaglio

Nessuna matematica nuova: questa fase **inchioda** matematica che c'era già. Ogni
formula qui sotto è stata letta riga per riga dal sorgente e ognuna ha ora almeno
un test che ne fissa il **valore**.

**(1) Brier 1X2** (`src/evaluation/metrics.py:59`). Con `p = (p_H, p_D, p_A)` e
`y` il vettore indicatore dell'esito avvenuto:

```
Brier = (1/N) · Σ_i Σ_{k∈{H,D,A}} (p_ik − y_ik)²          range [0, 2]
```

Il test che lo inchioda: `p = (0.5, 0.3, 0.2)`, esito `H`, quindi
`(0.5−1)² + 0.3² + 0.2² = 0.25 + 0.09 + 0.04 = **0.38**`. Senza il quadrato la
stessa riga darebbe `0.5 + 0.3 + 0.2 = 1.00`, e **nessun** confronto fra modelli
cambierebbe ordine: è esattamente il motivo per cui un test relazionale non basta.
Gli altri due valori fissati: uniforme `(1/3,1/3,1/3) → 4/9 + 2/9 = 6/9 = 0.6667`
(il «non so nulla» a tre esiti), e previsione certa e sbagliata `→ 2` (1 sul lato
mancato + 1 sul lato dato per certo), che è il massimo raggiungibile.

**(2) Log-loss 1X2** (`metrics.py:52`), col logaritmo **naturale**:

```
LL = −(1/N) · Σ_i ln(p_i,esito_i)          con p ∈ [1e−15, 1]
```

`p = 0.5` sull'esito avvenuto → `−ln(0.5) = 0.6931`. In base 10 sarebbe `0.3010`:
ogni numero pubblicato dal progetto cambierebbe di un fattore `ln(10) = 2,3026` e
nessun confronto si invertirebbe. Il clip a `1e−15` è una **scelta**, non un
dettaglio: senza, una sola probabilità 0 sull'esito avvenuto manderebbe a infinito
la metrica dell'intero backtest. Il test fissa anche il valore del taglio,
`−ln(1e−15) = 34.54`, così se qualcuno lo cambia si vede.

**(3) Devig moltiplicativo** (`metrics.py:31`):

```
p_k = (1/q_k) / Σ_j (1/q_j)
```

Quote `1.90/3.80/3.80`: `1/q = 0.5263/0.2632/0.2632`, somma `1.0526` (margine del
5,26%), normalizzate `0.50/0.25/0.25`. Il margine viene spalmato **in proporzione**
— è la definizione del metodo moltiplicativo, e il test lo mostra su un caso dove
il risultato è tondo. Su quote già eque (`2/4/4`, somma degli inversi esattamente
1) il devig dev'essere l'**identità**: il secondo test.

**(4) Il termine covariata** (`dixon_coles.py:648`). Per la squadra di casa:

```
cov = Σ_k β_k · (z_casa,k − z_ospite,k)      con  z = (T(v) − m_k) / s_k
```

dove `T` è la trasformazione dichiarata in `_COVARIATES` (`log`, `log1p` o
identità) e `m_k, s_k` sono media e deviazione standard imparate sul training. Il
termine entra nei tassi **con segno opposto**:

```
λ = exp(att_casa + dif_ospite + γ + cov)
μ = exp(att_ospite + dif_casa − cov)
```

Da cui tre proprietà che i test fissano, e che sono le tre cose che potrebbero
rompersi in silenzio:
- **valore**: con `v_casa = e²`, `v_ospite = e`, `T = log`, `m = 0`, `s = 1`,
  `β = 0.5` → `cov = 0.5·(2−1) = **0.5**`. Con `s = 2` diventa `0.25`: la
  standardizzazione entra davvero. Con `m = 10` resta `0.5`, perché il termine è
  una **differenza** di z e la media si semplifica;
- **antisimmetria**: due squadre col medesimo valore danno `cov = 0` (è un
  vantaggio **relativo**, non un livello), e scambiarle inverte il segno;
- **prodotto invariante**: `λ·μ = exp(cov)·exp(−cov) = 1`. La covariata **sposta
  l'equilibrio** della partita senza toccarne il totale atteso: è la sua semantica,
  e un errore di segno la trasformerebbe in un moltiplicatore dei gol totali.

**(5) La raggiungibilità della posta in palio** (`loader.py:599`). Con `n` squadre,
`g` gare già giocate e `p` punti:

```
total  = 2·(n − 1)               giornate del calendario teorico
reach  = 3·(total − g)           punti ancora conquistabili (tutte vittorie)
```

Il difetto era in `total`. Con `n = 18` il valore vero è `2·17 = 34`; presumendo
`n = 20` diventa `2·19 = 38`, cioè `reach` sovrastimato di `3·4 = **12 punti**` a
ogni giornata. Dodici punti sono, in classifica, la distanza fra la metà bassa e
la zona europea: una squadra tagliata fuori da tutto risultava «ancora in corsa»
per l'Europa fino all'ultima giornata. Le tre linee che `reach` confronta:

```
safe_line   = board[n − relegated − 1]     ultima salva     (15ª di 18, 17ª di 20)
releg_line  = board[n − relegated]         prima a rischio  (16ª di 18, 18ª di 20)
euro_line   = board[europe_rank − 1]       ~Europa          (7ª)
```

anche loro leggevano la posizione sbagliata a `n = 18`: la 17ª di 18 è penultima,
non l'ultima salva. Deducendo `n` dai dati tornano entrambe giuste senza toccare
`relegated`, perché `n − relegated − 1` vale 14 (15ª) a 18 squadre e 16 (17ª) a 20.

⚠️ **Un limite che resta, dichiarato**: la Ligue 1 2019-20 fu **cancellata** al 28°
turno. L'euristica ragiona sul calendario **teorico**, quindi fino all'ultima
giornata giocata vede ancora 10 gare da giocare e non dichiara nessuno «deciso». È
corretto così: nessuno, in quel momento, lo sapeva.

---

## Fase 138 — Le coppe nazionali entrano nel progetto, e la fonte somma i rigori al risultato

**Obiettivo.** Decisione dell'utente (02/08/2026), dopo il disegno di
`PIANO_DATABASE_GIOCATORI.md` §14: si parte dalle **competizioni di club**, e
dentro queste dalle **coppe nazionali** della sola stagione 2025-26 — Coppa
Italia, FA Cup, Carabao Cup, Copa del Rey, DFB-Pokal, Coupe de France. Il
perimetro l'ha fissato l'utente e non è quello che avevo proposto io: **«da
dove iniziano a giocare i club di seconda divisione in ogni nazione»**, perché
*«i club che oggi sono in seconda domani saranno in prima, e viceversa»*. Da
raccogliere: data, squadre, risultato, **formazioni titolari e sostituzioni**.
Il risultato serve anche da controparte automatica alla raccolta manuale
diretta.it che l'utente importerà.

**Ragionamento e ipotesi.** L'ipotesi di partenza — la mia — era che le coppe
fossero un fronte quasi vergine e che il costo stesse nel procurarsi il
calendario. Verificando prima di pianificare (la stessa disciplina che alla
§14 aveva già demolito due premesse), è caduta anche questa:

1. **il calendario di coppa 2025-26 c'era già**, in `data/club_fixtures*.csv`,
   per tutte e cinque le leghe — ma solo per le partite in cui gioca almeno un
   club di prima divisione, e **senza risultato e senza formazioni**;
2. **le formazioni c'erano quasi tutte**, e non me ne ero accorto: il dataset
   player-scores contiene le coppe nazionali. `appearances` ha 891 presenze di
   Coppa Italia 2025-26, 1.172 di FA Cup, 1.298 di Copa del Rey. Mancavano solo
   i file che non avevamo scaricato — `games.csv`, `game_lineups.csv`,
   `game_events.csv` — e Kaggle è raggiungibile in sessione dalla Fase 100.

**Alternative considerate.** (a) Scraping di diretta.it via Playwright: dà
tutto, ma è il lavoro che l'utente fa a mano e non serviva duplicarlo prima di
avere una controparte. (b) openfootball come fonte primaria: **scartata per
misura** — il 2025-26 delle coppe esiste solo per la Germania, e anche lì il
file si ferma al 2° turno (dagli ottavi in poi le righe sono `N.N.`). È
diventato invece il *verificatore*. (c) Wikipedia come fonte primaria: dà
risultati ma non formazioni; è rimasta per la Coupe de France e per tre finali.

**Scelta: tre fonti, con ruoli diversi.** player-scores come ossatura;
openfootball come **verifica esterna e indipendente**; Wikipedia per ciò che
manca. Non è ridondanza: due fonti sulla stessa partita sono l'unico modo per
accorgersi che una delle due sbaglia (R5, passo 2) — ed è servito subito.

### Il difetto: il punteggio della fonte non è il punteggio della partita

Su **68 partite di coppa su 458 (14,8%)** `games.csv` riporta il risultato
**sommato ai rigori**:

```
Eintracht Braunschweig v VfB Stuttgart   games.csv:  11-12
la partita è finita 4-4 dopo i supplementari; rigori 7-8
```

Non è un dato mancante: è un **finto pieno** (regola R6). Un 11-12 sembra un
punteggio, si comporta come un punteggio, passa qualunque controllo di tipo, e
avvelenerebbe ogni modello sui gol. È **esattamente** la trappola che il
progetto aveva già registrato per Chemnitzer-Mainz 2014 (10-9 = 5-5 più 5-4
ai rigori): scritta in un documento, mai trasformata in un controllo. Ora lo è.

**Risultato.** 662 partite su 6 coppe e 5 paesi; 18.566 righe di formazione
(9.883 titolari, 8.683 panchina) e 8.177 eventi col minuto su 458 partite
coperte al 100%. Ricostruzione del punteggio esatta su **448/458 (97,8%)**, con
i 10 residui dichiarati riga per riga. Verifica esterna contro openfootball:
**42 partite appaiate, 42/42 identiche su tutti e sei i campi** (90' casa e
ospite, finale casa e ospite, rigori casa e ospite), **zero divergenze**.

**Due ipotesi scartate misurando, non discutendo.**
- *«gli autogol vanno riassegnati all'avversario di chi li segna»* — **falso**:
  nel dataset sono già attribuiti alla squadra che ne **beneficia**. Invertirli
  fa scendere la ricostruzione dal 98,5% all'89,7%: è la differenza che ha
  deciso, non l'intuizione.
- *«i rigori si contano dagli eventi»* — **falso**: la sequenza è **troncata**.
  In Grimsby-Manchester United sono registrati 23 tiri, i rigori veri furono
  12-11. Il totale contaminato di `games.csv` è più completo della sequenza,
  quindi la stima buona è la **sottrazione**.

**Il turno d'ingresso della seconda divisione è misurato, non copiato** da una
scheda di formato: si cerca il primo turno in cui compare un club che
football-data elenca nella seconda divisione 2025-26 di quel paese.

| coppa | 2ª divisione entra a | partite | nel perimetro |
|---|---|--:|--:|
| Coppa Italia | Qualifying Round | 45 | 45 |
| FA Cup | Third Round | 123 | 63 |
| EFL Cup (Carabao) | First Round | 93 | 91 |
| Copa del Rey | First Round | 137 | 117 |
| DFB-Pokal | First Round | 63 | 63 |
| Coupe de France | 7° turno | 201 | 201 |

Per cinque coppe su sei l'ingresso è **il primo turno del torneo**: il
perimetro dell'utente coincide quasi sempre con la competizione intera, e taglia
davvero solo la FA Cup (i primi due turni, 60 partite di sole squadre minori).
Applicando §5-ter («raccogliere tutto») le partite fuori perimetro sono state
**tenute lo stesso** e marcate con una colonna: il perimetro è un filtro, non un
confine di raccolta.

**Buchi dichiarati** (R6: un buco dichiarato è innocuo, uno nascosto no).
**204 partite senza formazione** — le 201 di Coupe de France più tre finali:
Wikipedia pubblica i titolari solo per le finali, e la Coupe de France non è
in player-scores (`competitions.csv` ha 10 coppe nazionali e nessuna francese,
rilievo già noto). E **tre finali mancavano del tutto da `games.csv`** — Coppa
Italia, FA Cup, DFB-Pokal — pur essendoci 846 partite di maggio 2026 in altre
competizioni: non è un taglio temporale, è un'assenza puntuale, recuperata da
Wikipedia.

**Un controllo cieco scoperto scrivendolo.** Il primo test che avevo messo
diceva «nessuna partita finisce con più di 10 gol». È diventato rosso su dati
**veri**: Getafe ha vinto 11-0 in casa di una squadra di quinta divisione, il
Saint-Étienne 11-1. Un tetto sul numero di gol non distingue il difetto dal
calcio — è la regola R7 (la statistica di testa dev'essere quella giusta, non
quella comoda). Sostituito con l'**identità esatta** `dichiarato = gol +
rigori`, che il difetto lo intercetta e la goleada la lascia passare.

### 📐 Il modello in dettaglio

Non c'è modello nuovo: c'è una **ricomposizione esatta**, e va scritta come
identità perché è così che si evita di leggerla al contrario (regola aggiunta
dalla Fase 92).

**1. Il punteggio, dai soli eventi** (`src/data/coppe.py::ricostruisci_punteggio`):

```
gol_casa(t)   = #{ e ∈ eventi : e.type = "Goals" ∧ e.club_id = casa ∧ e.minute ≤ t }
gol_casa_90   = gol_casa(90)          gol_casa_finale = gol_casa(∞)
rigori_casa   = home_club_goals − gol_casa_finale        [solo se ∃ evento "Shootout"]
```

Perché `club_id` senza correzione per gli autogol: **misurato**. Contando gli
autogol a favore della squadra del giocatore la resa è 89,7%; attribuendoli a
chi ne beneficia — cioè leggendo `club_id` così com'è — è 98,5%. Il numero non
è scelto, è l'esito del confronto fra le due letture sulle stesse 458 partite.

Perché i rigori per sottrazione e non per conteggio: `#Shootout(Grimsby) = 23`
contro un 12-11 reale. La sottrazione usa `home_club_goals`, che è contaminato
**ma completo**; il conteggio userebbe una sequenza **incompleta**. Fra un dato
sporco-e-intero e uno pulito-e-mozzo, per una differenza, vince il primo.

Due guardie, entrambe con una ragione fisica e non estetica:
```
rigori_casa < 0  ∨  rigori_ospite < 0   → impossibile (i gol non si sottraggono)
rigori_casa = rigori_ospite             → impossibile (una serie di rigori non pareggia)
```
In entrambi i casi il valore **non** viene scritto: la riga si marca
`eventi_incompleti`. Sono 10 righe su 458, e 9 sono turni preliminari
dilettantistici di Copa del Rey dove manca perfino il nome di un club.

**2. La verifica esterna** (`leggi_openfootball`). openfootball scrive la stessa
partita in forma già scomposta:

```
7-8 pen.  4-4 a.e.t.  (3-3, 1-1)
 rigori    finale       90'  primo tempo
```

⚠️ La parentesi ha **due significati**: con `a.e.t.` è il 90' (più, se c'è, il
primo tempo); senza, è il primo tempo. Leggerla sempre allo stesso modo è
l'errore facile, ed è coperto da un test. Il confronto fra le due letture
indipendenti — la nostra ricostruita, la loro dichiarata — dà **42/42 su sei
campi**: è ciò che rende la ricomposizione un fatto e non un'ipotesi.

Un bug pagato qui, e vale la pena scriverlo: il parser pretendeva **due spazi**
attorno alla `v` che separa le squadre. Nel file le colonne sono allineate,
quindi due spazi ci sono quasi sempre — ma **non** quando il nome di casa è
lungo abbastanza da mangiarseli («SG Sonnenhof Großaspach v Bayer Leverkusen»).
Saltavano in silenzio 16 partite su 63, **tutte con la squadra dal nome lungo**:
un filtro sistematico travestito da svista, che nessun conteggio totale avrebbe
mostrato come sbagliato. L'ha trovato un test, non un'occhiata ai numeri.

**3. La Coupe de France** (`src/data/coupe_de_france.py`). Il template
`{{Feuille de match}}` tiene i rigori in un campo **separato** (`score tab`),
quindi lì il punteggio non è mai contaminato; e scrive la **divisione** di ogni
club accanto al nome (`<small>(N2)</small>`), cioè esattamente l'informazione
che serve al perimetro. La squadra qualificata è in `'''grassetto'''`: è un
secondo canale **indipendente** dal punteggio, quindi confrontarli verifica la
lettura. Su 201 partite: 201 con punteggio, 201 con data, 201 con entrambe le
divisioni, **0 incoerenze** fra grassetto e punteggio.

**4. Le tre finali mancanti** (`leggi_finale_wikipedia`). Una trappola piccola e
istruttiva: nell'infobox `Infobox football match` il punteggio **non** sta in un
campo `score`, sta in `team1score`/`team2score`. Un `| score = 0–2` esiste più
in basso nella pagina, dentro il `{{Football box}}` del riepilogo — quindi una
ricerca su tutto il wikitext lo trova, sembra giusta, e sta leggendo **un
template diverso** da quello da cui prende tutti gli altri campi. Si legge un
solo template, per intero, con l'annidamento contato.

**Lezione.** Tre, e nessuna riguarda un modello.
1. **Una fonte nuova va letta contro una seconda fonte prima di crederle**, non
   dopo. Qui il difetto era su una partita su sette, e nessun controllo interno
   l'avrebbe visto: il dato coincide con la fonte, la fonte è sbagliata.
2. **Un fatto scritto in un documento non è un controllo.** Chemnitzer-Mainz
   era annotato dal 29/07 e il difetto è rientrato lo stesso, perché
   un'annotazione non fallisce quando qualcuno la ignora. Un test sì.
3. **I controlli di sanità vanno scelti come le statistiche di testa** (R7): un
   tetto sui gol segnala il calcio vero e tace sul difetto; l'identità esatta fa
   il contrario.

**Cosa NON è stato fatto**, e va detto: nessun modello usa questi dati. È una
raccolta, e il suo valore immediato è il collegamento (§14.5), non una
conclusione. Il confronto con la raccolta manuale diretta.it dell'utente è il
passo successivo, ed è quello che chiuderà il cerchio sulle 204 partite senza
formazione.

**Correzione applicata lo stesso giorno, dopo una domanda dell'utente**
(«come faccio a dire al mio amico da che turno partire?»). Preparando il foglio
di istruzioni è saltato fuori che **Wigan Athletic risultava di prima
divisione** — gioca in League One. La causa: la divisione veniva da
`club_names.domestic_competition_id`, che **non** è la lega corrente ma
*«qualunque lega in cui il club sia mai comparso»*: 37 club marcati `GB1`, fra
cui Reading, Huddersfield, Cardiff, QPR, West Brom. Un finto pieno da manuale
(R6) — valore plausibile, formato giusto, sbagliato — e sfuggito perché nessun
controllo confrontava quella colonna con una fonte indipendente.

**Corretto** usando gli **snapshot congelati 2025-26**, che sono la verità e
ce li avevamo in casa; servono 14 alias nuovi per i nomi abbreviati di
football-data (`Man City`, `Nott'm Forest`, `M'gladbach`, `Ath Bilbao`…), tutti
verificati a candidato unico, e ora il costruttore **si ferma** se un club di
prima divisione non si aggancia, invece di degradarlo silenziosamente a «terza
o sotto». ⚠️ **Il perimetro non cambia**: i turni d'ingresso della seconda
divisione restano identici (Coppa Italia *Qualifying*, FA Cup *Third Round*,
gli altri *First Round*, Coupe de France *7° turno*), perché in quei turni la
presenza di club di seconda divisione era già rilevata da altri club. Il difetto
sporcava l'**etichetta**, non la **conclusione** — ma andava trovato lo stesso,
e l'ha trovato una domanda pratica, non un audit.

Aggiunti: un **test di regressione** che confronta i club marcati prima
divisione con gli snapshot lega per lega, `data/coppe_2526/da_raccogliere.csv`
(la lista di lavoro, 580 righe, col flag `gia_abbiamo_formazioni`) e
`data/coppe_2526/DA_RACCOGLIERE.md` (il foglio operativo per chi raccoglie a
mano: da che turno partire, cosa saltare, e l'avvertenza di annotare 90',
supplementari e rigori in **tre caselle separate** — 113 partite su 580
finiscono ai rigori, una su cinque).

---

## Fase 139 — La controprova arriva: due fonti indipendenti sulla Coppa Italia, zero divergenze

**Obiettivo.** L'utente consegna la raccolta manuale diretta.it della **Coppa
Italia 2025-26**, fatta da un collaboratore seguendo il foglio di istruzioni
della Fase 138. È il momento per cui `data/coppe_2526/` era stato costruito:
non «abbiamo un altro dataset», ma **abbiamo una seconda misura della stessa
cosa**, ed è l'unico modo di sapere se la prima era giusta (R5, passo 2).

**Ragionamento.** La Fase 138 aveva trovato che la fonte automatica sbagliava
il punteggio su 68 partite su 458 (sommava i rigori) e l'aveva corretta
ricostruendolo dagli eventi, validando la ricostruzione contro openfootball —
ma **solo sulla DFB-Pokal**, 42 partite, e solo sui primi due turni. Sulla
Coppa Italia la ricostruzione non era mai stata verificata da nessuno.

**Risultato — il confronto**, `scripts/registra_raccolta_coppa_diretta.py`:

| confronto | esito |
|---|---|
| partite appaiate | **45 / 45** |
| punteggi identici (90', finale, rigori) | **45 / 45** |
| undici iniziali identici | **88 / 88** squadre-partita |
| divergenze | **nessuna** |

Zero. Su tre grandezze diverse, due fonti che non si sono mai parlate — una
scaricata da Transfermarkt e ricomposta dagli eventi, una letta a mano da
Flashscore — dicono la stessa cosa su ogni partita del torneo.

**Cosa la raccolta manuale aggiunge**, oltre alla conferma:
- le **statistiche per giocatore**: 1.307 righe × **103 metriche** (tocchi,
  dribbling, contrasti, xG/xA individuali, ingressi in area…) su 41 partite;
- la **sequenza completa dei rigori** — 256 eventi, ed è esattamente il punto
  in cui la fonte automatica **tronca** (Grimsby-United ne registra 23 su 25+).
  Qui si può *pretendere* che i rigori tornino, e tornano: **12/12**;
- il **periodo** di ogni evento (1° tempo / 2° tempo / supplementari / rigori),
  che da noi si deduce dal minuto invece di essere scritto;
- la **finale**, che `games.csv` non conteneva affatto (Fase 138): ora ha i
  suoi titolari.

**Due limiti dell'aggancio dei nomi, entrambi trovati e chiusi scrivendo i
test** — e sono la parte istruttiva.

1. **Quindici undici risultavano diversi ed erano identici.** Le due fonti
   scrivono `Gronbaek A.` e `Albert Grønbaek`, `Kilicsoy S.` e `Semih
   Kılıçsoy`, `Hojlund R.` e `Rasmus Højlund`. È il bug già documentato in
   `club_matching.py` — «`ø`, `ł`, `đ` non sono decomposti da NFKD» — che io
   avevo riprodotto pari pari perché non stavo usando la tabella del progetto.
   La conoscenza era scritta; non l'avevo applicata.
2. ⭐ **Un test negativo ha trovato un difetto vero.** Avevo scritto «`Esposito
   Sa.` non deve agganciarsi a `Francesco Esposito`» aspettandomi il verde: è
   uscito **rosso**, perché buttando l'iniziale `Esposito Sa.` si riduce a
   `{esposito}`, che è sottoinsieme di `{francesco, esposito}`. Cioè il
   confronto **non distingueva due omonimi in rosa** — e Salvatore e Francesco
   Esposito giocano davvero in questa Coppa Italia. Non è teorico: è il caso in
   cui una formazione sbagliata sarebbe passata per giusta. Corretto
   conservando l'iniziale e verificandola come prefisso.

### 📐 Il modello in dettaglio

Nessun modello: un **criterio di identità fra due scritture dello stesso nome**,
che è la cosa da rendere esplicita perché è dove si nascondono gli errori.

Un nome diventa una coppia `(parole, iniziali)`:

```
_token("Esposito Sa.")      = ({"esposito"},              {"sa"})
_token("Salvatore Esposito")= ({"salvatore","esposito"},  {})
_token("Ndri K.")           = ({"ndri"},                  {"k"})
_token("Konan N'Dri")       = ({"konan","ndri"},          {})
```

con, prima di tutto, `str.translate(_TRADUZIONE)` — la tabella del progetto per
`ø ł đ ß æ ı`, che NFKD **non** decompone — e l'apostrofo **tolto** e non
sostituito con uno spazio (spezzando, `N'Dri` darebbe `dri` e `Ndri` non
si aggancerebbe).

Due nomi sono la stessa persona quando:

```
(A ⊆ B  ∨  B ⊆ A)                          le parole intere si contengono
∧  ∀ i ∈ iniziali(A): ∃ p ∈ B con p[:|i|]=i   ogni iniziale e' prefisso di una parola
∧  ∀ i ∈ iniziali(B): ∃ p ∈ A con p[:|i|]=i
```

La seconda e la terza riga sono quelle che il test negativo ha imposto:
`{esposito} ⊆ {francesco, esposito}` è vero, ma `"sa"` non è prefisso né di
`francesco` né di `esposito`, quindi il match **cade** — mentre con `Salvatore
Esposito` `"sa"` è prefisso di `salvatore` e il match **regge**. È una riga di
codice che separa due persone reali.

**Una seconda passata**, solo sui giocatori rimasti spaiati dopo la prima:
accetta **un token in comune**. Serve per le convenzioni spagnole, che non sono
in relazione di sottoinsieme — `Santiago Perez J.` contro `Yellu Santiago` è
Yellu Santiago Pérez. È sicura *perché è seconda*: quando gli altri dieci sono
già appaiati, un giocatore davvero diverso non condivide il cognome.

**Lezione.** Tre.
1. **La controprova va progettata prima di servire, non cercata dopo.** Il
   confronto è costato mezz'ora perché la Fase 138 aveva già messo i punteggi
   in colonne separate e le formazioni in una forma confrontabile. Se la
   raccolta automatica fosse arrivata dopo quella manuale, il confronto sarebbe
   stato un lavoro a sé.
2. **Un test negativo vale quanto uno positivo.** Gli otto test «questi due
   nomi sono la stessa persona» hanno confermato ciò che sapevo; l'unico test
   «questi due NON lo sono» ha trovato un difetto che nessuno dei precedenti
   poteva vedere. Il verde conferma, il rosso insegna.
3. **Sapere una cosa e applicarla sono due stati diversi.** Il bug dei caratteri
   non-decomponibili era scritto in `club_matching.py`, con tanto di elenco. L'ho
   rifatto lo stesso, perché stavo scrivendo un normalizzatore nuovo invece di
   usare quello che c'era. La documentazione non protegge: protegge il codice
   condiviso.

**Cosa resta aperto.** Le statistiche per giocatore (103 metriche) sono
**raccolte e non usate** — stato legittimo e dichiarato (§5-ter). E i due CSV
consegnati a parte sono **duplicati esatti** di due fogli dell'xlsx (verificato
cella per cella, 0 divergenti): restano archiviati entrambi perché escludere un
dato richiede il consenso dell'utente, non la mia valutazione (§5-ter).

---

## Fase 139-bis — I tre ponti, e perché il terzo si regge sul secondo

**Obiettivo.** Richiesta dell'utente, dopo la consegna della **DFB-Pokal**:
*«iniziamo ad agganciare i nomi con le presenze, le squadre con le partite, e
tutto quello che c'è da collegare»*. Le raccolte manuali parlano per **nomi**,
il database per **identificatori**: finché non si toccano, «la carriera di
questo giocatore» e «come ha giocato in Coppa Italia» sono due frasi che non si
possono dire insieme.

**Prima, la DFB-Pokal.** Registrata con la stessa porta della Fase 139:
63 partite, 2.518 righe di formazione, 1.979 righe di statistiche, 2.106 eventi.
Verifiche interne tutte verdi (126/126 undici esatti, 8/8 sequenze di rigori).
Contro la fonte automatica: **63/63 partite appaiate, 63/63 punteggi identici,
122/124 undici identici** — e le 63 includono la **finale**, che `games.csv` non
conteneva.

Ci sono voluti due passaggi per arrivarci, ed entrambi meritano una riga.

1. **diretta.it scrive i club tedeschi in italiano**: `Stoccarda`, `Friburgo`,
   `Colonia`, `Amburgo`, `Magonza`, `Norimberga`, `RB Lipsia`. Sono **14 nomi**,
   tutti esonimi, tutti verificati a candidato unico, e sono andati in
   `club_matching.ALIAS` — non nello script, perché valgono per **qualunque**
   fonte in lingua italiana, non per questa raccolta.
2. ⚠️ **Un bug mio che produceva un numero credibile.** Ri-registrando la Pokal
   con `--cartella` senza `--coppa`, lo script usava il default («Coppa Italia»)
   e confrontava la Pokal con la coppa sbagliata: **0 partite appaiate**. Zero
   non sembra un errore, sembra un *dato* — «le due fonti non si parlano». È il
   tipo di difetto peggiore, e l'ha svelato solo il fatto che un attimo prima
   erano 33. Ora il nome si riprende dal manifesto, e l'argomento esplicito ha
   la precedenza.

**Il risultato: i tre ponti.**

| ponte | Coppa Italia | DFB-Pokal |
|---|---|---|
| squadre → `club_id` | **44/44** | **64/64** |
| partite → `game_id` | 44/45 | 62/63 |
| giocatori → `player_id` | **2.080/2.133 (97,5%)** | **2.467/2.518 (98,0%)** |

Le due partite mancanti sono le **finali**, che la fonte automatica non ha
(Fase 138): non è un aggancio fallito, è una controparte che non esiste.

⭐ **Il terzo ponte si regge sul secondo, ed è tutta la storia.** Il primo
tentativo usava `player_identity.collega_per_eliminazione`, la funzione già
collaudata sui campionati, che aggancia per `(data, token del nome)`. Resa:
**25,6%** sulla Coppa Italia, **12,0%** sulla Pokal. Il motivo non è un bug: nei
**campionati** diretta.it scrive il nome intero (`Garces Facundo`), nelle
**coppe** lo abbrevia (`Motta E.`) — e `{motta}` non è `{emanuele, motta}`.

La soluzione non è stata un normalizzatore più furbo: è stato **usare il ponte
già costruito**. Agganciata la partita, i candidati non sono più «tutti quelli
in campo quel giorno» (migliaia) ma le **18-23 persone di quel club in quella
partita**. Su un insieme così piccolo il confronto per nome è quasi sempre
univoco: **97,5%** e **98,0%**.

**Come si scompone la copertura**, perché «97,5%» da solo non dice nulla:

| | righe |
|---|--:|
| agganciate **per nome** | 4.501 |
| agganciate **per eliminazione** | 46 |
| non agganciate | 104 |

E delle 104: **92 sono nelle due finali**, che non hanno `game_id` e quindi non
hanno candidati. I fallimenti veri dell'appaiamento sono **12 su 4.651 righe —
lo 0,26%**.

### 📐 Il modello in dettaglio

Nessun modello: un **criterio di assegnazione** dentro un insieme chiuso.

Per ogni `(game_id, club_id)` si hanno due liste della stessa cosa: la nostra
`A` (nomi Transfermarkt, con `player_id`) e la manuale `B` (nomi diretta.it).
L'assegnazione è in due passate, e l'ordine è la garanzia:

```
passata 1 — per nome:   ∀ b ∈ B, si cerca l'unico a ∈ A con stessa_persona(a, b)
passata 2 — eliminazione: se |B_spaiati| = 1 ∧ |A_liberi| = 1  →  si appaiano
                           altrimenti NESSUNO viene agganciato
```

dove `stessa_persona` è la stessa regola della porta d'ingresso (Fase 139):
sottoinsieme dei token **e** ogni iniziale prefisso di una parola dell'altro
nome — la condizione che separa `Esposito Sa.` da `Francesco Esposito`.

La condizione `1 ∧ 1` della seconda passata non è prudenza decorativa: con due
spaiati e due liberi ci sono **due assegnazioni possibili** e sceglierne una
significa, nella metà dei casi, attribuire a un giocatore le statistiche di un
compagno di squadra. Costa 12 righe su 4.651 e le rende **dichiarate** invece
che sbagliate.

**Lezione.** Due.
1. **Un ponte costruito abilita il successivo.** Il salto dal 25% al 97,5% non
   viene da un algoritmo migliore: viene dall'aver ristretto il campo con un
   collegamento che già avevamo. Vale la pena chiedersi, prima di raffinare un
   matcher, se non ci sia un vincolo già disponibile che non si sta usando.
2. **Uno zero è un numero come gli altri, e va sospettato allo stesso modo.**
   «0 partite appaiate» aveva l'aspetto di un risultato — due fonti che non si
   corrispondono — ed era un argomento di default sbagliato. Un risultato
   drasticamente peggiore del precedente non è una scoperta finché non si è
   escluso di averlo causato.

---

## Fase 139-ter — Caso per caso: quattro coppe, due fonti, e il foglio che nessuno guardava

**Obiettivo.** Richiesta dell'utente: *«risolviamo caso per caso tutti i problemi
sia per la coppa italia sia per la coppa tedesca, se serve cerchiamo su internet
per avere conferme»*, poi la **Carabao Cup** e la **FA Cup** con lo stesso
lavoro, e infine *«un controllo finale per verificare di aver agganciato tutti i
dati raccolti fino ad ora»*.

**Il metodo.** I casi aperti erano 22, di tre tipi. Sono stati mandati a
**indagare in parallelo** (workflow a 6 agenti: 3 investigatori + 3 scettici
indipendenti incaricati di **refutare** le conclusioni). Nessuna conclusione
basata sul web è stata applicata senza che un secondo agente l'avesse
verificata su una fonte diversa.

### I tre nomi discordanti — tutti stessa persona, per tre ragioni diverse

| caso | verdetto | chi sbaglia |
|---|---|---|
| `Pfarr M.` vs `Marcel Pfaar` | stessa persona | **diretta.it**: due lettere invertite. Il registro ufficiale DFB scrive «Marcel Pfaar, 18.10.1998» |
| `Kessler B.` vs `Ben Nitschke` | stessa persona | **nessuno**: è un **cambio di cognome**. Il sito dello ZFC Meuselwitz elenca «Ben Nitschke (ehem. Keßler)» in una sola voce. diretta.it usa il nome in vigore alla data della partita, Transfermarkt l'attuale |
| `Talovierov M.` vs `Maksym Taloverov` | stessa persona | **Transfermarkt**: due traslitterazioni di Таловєров. La forma con -ie- è quella del club, di UEFA e della BBC |

Il secondo è il più istruttivo: **due fonti possono avere ragione entrambe** e
dire cose diverse, perché descrivono momenti diversi. Nessuna correzione: una
tabella di sinonimi, con la fonte scritta accanto a ciascuno.

### Le 12 righe non agganciate — e un test che stavo per scrivere sbagliato

Otto erano **la stessa persona con una regola troppo severa**, e la prova stava
in casa: `stat_giocatori.csv`, il quarto foglio della stessa raccolta, scrive i
nomi **per intero**. `Manu K. S.` è «Manu King Samuel» — la `S` è Samuel, un
secondo nome che il registro non porta. La clausola pretendeva che **ogni**
iniziale trovasse un prefisso; ne basta **una**. Misurato prima di applicarlo:
**+23 righe, 0 nuove ambiguità**, e la protezione sugli omonimi resta intatta
perché con una sola iniziale «almeno una» e «tutte» coincidono.

Due erano **grafia**: `Abursu`/`Arbursu` (una `r`) e `Splettstoesser` contro
`Splettstößer` — diretta.it espande la ö in `oe`, NFKD la riduce a `o`. Risolto
generando **entrambe** le letture invece di sceglierne una: normalizzare in un
verso solo romperebbe l'altro (`Muller` non aggancerebbe più `Müller`).

Le altre quattro sono **assenze vere**: la riga di panchina manca nella fonte
automatica, non la persona. Il mancato aggancio è corretto.

### La partita che nessuna delle due fonti sbagliava

Tranmere-Burton, 1° turno di Carabao Cup: la nostra fonte la dava il **12/08**,
diretta.it il **19/08**. Verificato: era in programma il 12, **rinviata la sera
stessa per un blackout** che ha lasciato senza corrente Prenton Park, e rigiocata
il 19 d'accordo con la EFL. `games.csv` tiene la data di **calendario**, non
quella del campo. Correzione dichiarata (R3) in
`data/correzioni_dichiarate.csv` + tabella `DATE_CORRETTE` che **verifica il
valore di partenza** prima di sostituire.

E una volta agganciata, quella partita ha **colmato un buco nostro**: la nostra
riga era marcata `eventi_incompleti` (5-6 grezzo, sequenza rigori assente); la
manuale dice 1-1 più rigori 4-5, che ricompone il 5-6 esattamente. Il confronto
ora distingue le due cose: una **divergenza** è un disaccordo, un **buco
colmato** è il motivo per cui la seconda fonte esiste.

### Il risultato, quattro coppe

| | Coppa Italia | DFB-Pokal | Carabao | FA Cup |
|---|--:|--:|--:|--:|
| partite appaiate | **45/45** | **63/63** | **91/91** | **63/63** |
| punteggi identici | 45/45 | 63/63 | 90/91 + 1 colmato | 63/63 |
| **undici identici** | **88/88** | **124/124** | **180/180** | **124/124** |
| giocatori → `player_id` | 99,9% | 99,8% | 99,8% | **100%** |

**516 undici su 516.** Zero divergenze fra due fonti indipendenti.

### ⭐ Il controllo finale, e cosa ha trovato subito

`scripts/verifica_aggancio_coppe.py` risponde a una domanda sola: *ogni riga
raccolta è in una tabella di aggancio?* Quando l'utente l'ha chiesto la risposta
era **no**, e in grande: **8.475 righe di evento e 8.115 di statistica erano
raccolte e collegate a niente**. Nessuno se n'era accorto perché i numeri che
guardavamo — partite, formazioni — erano ottimi. **Un foglio dimenticato non dà
errore: dà silenzio.**

Agganciati anche quelli (le statistiche hanno richiesto la regola di confronto e
non l'uguaglianza, perché quel foglio scrive i nomi per intero: da 30 righe su
1.307 a 1.299). Stato finale:

```
27.624 righe raccolte · 27.488 agganciate · 99,5%
✅ ogni riga raccolta è nella sua tabella, nessuna identità usata due volte
```

**Un bug trovato dal controllo stesso.** Passando agli identificatori ho scoperto
che il lato automatico veniva **ri-derivato dal nome** pur avendo `home_club_id`
nella riga accanto: `FC Südtirol-Alto Adige` non si agganciava (il registro lo
chiama `FC Südtirol`) e Como-Südtirol spariva. Un giro inutile che introduce un
punto di rottura. Stessa classe di problema per le tre finali da Wikipedia, che
non avevano `club_id`: risolti alla fonte.

**Lezione.** Tre.
1. **«Zero» va sospettato come qualunque altro numero.** Ri-registrando la Pokal
   senza `--coppa` il confronto dava «0 partite appaiate» — che ha l'aspetto di
   un risultato («le due fonti non si parlano») ed era un default sbagliato del
   mio script. L'ha svelato solo il fatto che un attimo prima erano 33.
2. **La prova migliore era già in casa.** Otto casi su dodici si sono chiusi
   leggendo un foglio della stessa raccolta, non cercando in rete.
3. **Chiedere «è tutto agganciato?» è diverso da guardare le percentuali.** Le
   percentuali erano al 99% su ciò che guardavamo, e due fogli interi erano a
   zero. La domanda giusta non era «quanto è alta la copertura» ma «di che cosa».

## Fase 139-quater — Due copie della stessa funzione, e solo una sapeva le cose

**Obiettivo.** Le sei coppe nazionali 2025-26 erano registrate e agganciate, ma
le due nuove non tornavano: **Copa del Rey 77/117** partite agganciate e
giocatori al 66,8%, **Coupe de France 0/201** e 19,7%. Le altre quattro erano a
posto (100% delle partite, tutti gli undici identici). Capire perché.

**La causa, ed è una sola.** Il progetto aveva **due implementazioni** della
stessa cosa — risolvere un club e appaiare una partita fra le due fonti — e solo
una le sapeva tutte.

| | `registra_raccolta_coppa_diretta.py` | `aggancia_coppe.py` |
|---|---|---|
| deduzione del club dalle partite | ✅ | ❌ |
| chiave che ripiega sul nome | ✅ | ✅ |
| appaiamento per nome dentro la giornata | ✅ | ❌ |
| **Copa del Rey** | **117/117** | 77/117 |
| **Coupe de France** | **161/201** | 0/201 |

Non è un dettaglio di implementazione: **la divergenza era il bug.** Lo stesso
file, le stesse due fonti, due risposte diverse — e nessun test poteva
accorgersene, perché nessuno confrontava le due copie: erano entrambe «giuste»
rispetto a sé stesse.

**La scelta.** Risoluzione dei club e appaiamento delle partite estratti in
`src/data/coppe_aggancio.py` (`ALIAS_COPPA`, `chiave_partita`, `deduci_club`,
`appaia_partite`), chiamato da **entrambi** gli script. Non una funzione di
comodo: `appaia_partite` restituisce anche la funzione `cid` — la risoluzione
*completa* del nome di un club — perché un club dedotto per le partite e non per
le formazioni lascerebbe quei giocatori senza `club_id`, quindi senza candidati,
quindi vuoti. Il test `test_i_due_script_usano_la_stessa_implementazione`
verifica che nessuno dei due si ricrei una copia propria.

### 📐 Il modello in dettaglio

Tre regole, in ordine di forza decrescente. Nessuna sceglie mai fra due
possibilità: dove non c'è un vincitore unico, la casella resta vuota.

**(1) La chiave di partita** (`chiave_partita`, verificata riga per riga contro
`src/data/coppe_aggancio.py`):

```
k(riga) = data[:10] ‖ "|" ‖ lato(id_casa, nome_casa) ‖ "|" ‖ lato(id_osp, nome_osp)

lato(id, nome) = str(int(id))                            se id esiste
               = "~" + "".join(sorted(normalizza(nome)))  altrimenti
```

Il ripiego sul nome non è cosmetico: senza, le 201 righe della Coupe de France
diventano tutte `data|<NA>|<NA>` e il merge esplode in un prodotto cartesiano
(**4.804 righe**) che ha l'aspetto di una lista di divergenze.

**(2) La deduzione del club** (`deduci_club`) — l'eliminazione applicata ai
club invece che ai giocatori. Per ogni riga manuale con **un solo** lato
risolto:

```
cand(nome) = { b : (a,b) ∈ automatiche(giorno), a = club_risolto }   (lato casa noto)
si propone  nome → l'unico elemento di cand   se |cand| = 1
si accetta  nome → c   sse   tutte le proposte per quel nome danno lo stesso c
                             ∧ ( candidati(nome) = ∅  ∨  c ∈ candidati(nome) )
```

Le tre condizioni sono tutte necessarie e tutte pagate da un caso vero: la Copa
del Rey ha 21 nomi che il registro non riconosce e **sette sono ambigui** —
«Murcia» ha 4 candidati, «Ourense CF» e «UD Ourense» sono due club *diversi*
della stessa città. Scrivere alias a mano su nomi così rifà il caso «Brest»
(Fase 100): un aggancio sbagliato non dà errore, attribuisce le partite a un
altro club. Esito misurato: **21 club dedotti, 116/116 squadre agganciate**.

**(3) L'appaiamento per nome dentro la giornata** — per ciò che resta, e serve
alla sola Coupe de France:

```
s(L, N) = |normalizza(casa_L) ∩ normalizza(casa_N)| + |normalizza(osp_L) ∩ normalizza(osp_N)|
          definito solo se ENTRAMBE le intersezioni sono non vuote
si appaia L → argmax_N s   sse  il massimo è unico e STRETTAMENTE maggiore del secondo
                            ∧  nessun'altra riga manuale rivendica quella stessa N
```

Perché serve solo lì: nella Coupe de France **nessuno dei due lati ha un
`club_id`** (player-scores non copre né la Ligue 2 né i dilettanti) e le due
fonti scrivono il nome in due *forme* diverse — «Sochaux» contro «FC
Sochaux-Montbéliard», «Grenoble» contro «Grenoble Foot 38». La regola (1) le
vede come due squadre diverse; l'intersezione dei token no. Misurato: **122
partite su 201** appaiate così, e in **160 delle 161** coppie finali i due nomi
non coincidono alla lettera.

L'ultima clausola (la partita contesa da due righe manuali non va a nessuna
delle due) è la regola di sempre applicata alle partite: l'alternativa sarebbe
far vincere la prima riga in ordine di file. Sulle sei coppe le contese sono
**zero** — il guardrail non toglie niente a ciò che già funzionava, e c'è per
quando la prossima raccolta ne produrrà una.

### Il risultato, sei coppe

| | Coppa Italia | DFB-Pokal | EFL Cup | FA Cup | **Copa del Rey** | **Coupe de France** |
|---|--:|--:|--:|--:|--:|--:|
| partite → `game_id` | 44/45 | 62/63 | 91/91 | 62/63 | **77 → 117/117** | 0/201 |
| partite appaiate | 45/45 | 63/63 | 91/91 | 63/63 | **117/117** | **0 → 161/201** |
| squadre → `club_id` | 44/44 | 64/64 | 90/90 | 64/64 | **95 → 116/116** | 29/202 |
| giocatori → `player_id` | 99,9% | 99,8% | 99,8% | 100% | **66,8% → 94,7%** | 19,7% |

Le quattro coppe già a posto sono **immutate**, verificato al byte sui manifesti.

**Cosa resta fuori, e perché non è la stessa cosa.**

1. **Coupe de France — assenza a monte, non nostra.** La fonte automatica di
   quella coppa è Wikipedia (Fase 138): **0/201 righe hanno un `game_id`, 0
   hanno un `club_id`, e non ci sono formazioni**. Il ponte manca dalla sponda
   opposta. L'appaiamento a 161/201 non è quindi sprecato — è ciò che permette
   di *verificare i punteggi* (157/161 identici) — ma non può produrre
   identificatori che dall'altra parte non esistono. Provato anche il giro
   indiretto (dedurre il `club_id` dal nome della controparte appaiata): **24
   proposte coerenti, 0 nuove** — i club francesi minori non sono nel registro
   in nessuna grafia. Il tetto è la copertura di player-scores, e si alza solo
   con una fonte diversa per quella coppa.
2. **Copa del Rey — un residuo di nomi, ed è la prossima causa.** 265 righe su
   5.040 (98 squadre-partita). **Non sono righe mancanti**: le due fonti hanno
   lo stesso numero di giocatori per squadra-partita (delta medio **+0,02**,
   234 gruppi). È la convenzione spagnola sui **due cognomi** — diretta.it
   scrive «Sanchez Alonso M.», il registro «Mario Sánchez»: nessuno dei due
   insiemi di token contiene l'altro, quindi la regola del sottoinsieme non
   aggancia e l'eliminazione scatta solo dove resta un candidato solo. La porta
   d'ingresso ha già una seconda passata più permissiva (token in comune) usata
   per *contare* gli undici; portarla nell'aggancio significherebbe *attribuire
   identità*, ed è un esperimento a sé — con «Blanco Lopez J.»/«Blanco Garcia
   E.» contro «Pepe Blanco»/«Eloy Blanco» nella stessa partita, il rischio non è
   teorico. **Dichiarato, non chiuso.**

**Lezione.** *Due implementazioni della stessa regola non sono ridondanza: sono
due regole diverse che si somigliano.* Finché nessuno le confronta, la peggiore
non dà errore — dà un numero più basso che sembra un limite del dato. Il segnale
c'era e l'abbiamo guardato per giorni: lo stesso file registrato dalla porta
d'ingresso diceva 117, lo script accanto diceva 77. **Due numeri diversi sullo
stesso dato sono sempre un bug, mai un dettaglio.**

---

## Fase 139-quinquies — Il secondo consegnato, e un controllo che bocciava il dato buono

**Obiettivo.** L'utente consegna, una coppa alla volta, un **secondo** file
diretta.it: le statistiche. Non sostituisce il primo — porta un foglio che la
raccolta base non aveva, le statistiche di **squadra divise per periodo**
(Totale / 1° tempo / 2° tempo / Supplementari, 35 metriche). Integrarlo senza
prendersi dentro, di soppiatto, un file che appartiene a un'altra raccolta.

**Ragionamento.** Il rischio non è che il file sia sbagliato: è che sia *un
altro*. Un secondo consegnato assomiglia sempre al primo, e il modo naturale di
integrarlo — sovrascrivere il foglio giocatori con la versione più ricca —
cancella l'unica copia con cui si potrebbe accorgersene. Quindi la regola:
**si verifica prima, si scrive dopo**, e la verifica è che le due versioni siano
*la stessa misura, più precisa*, non due misure.

**Alternative considerate.**

1. *Tenere i due fogli affiancati* senza sovrascrivere. Scartata: il nuovo è il
   vecchio più `ID partita` e più decimali — due copie dello stesso dato sono
   due verità da tenere allineate, e la Fase 139-quater ha appena mostrato cosa
   costa (due implementazioni della stessa regola, e solo una sapeva le cose).
   L'originale come consegnato resta comunque archiviato (`originale_statistiche.xlsx`, §5-ter).
2. *Confrontare all'uguaglianza esatta.* Non regge: il primo consegnato tronca
   a tre decimali, il secondo no. Ogni cella con decimali risulterebbe diversa.
3. *Confrontare solo i conteggi di riga.* È il controllo che non controlla
   niente: due raccolte diverse della stessa coppa hanno lo stesso numero di
   righe per costruzione.

**Scelta.** Confronto cella per cella sulle colonne in comune, con una soglia
pari all'arrotondamento dichiarato, e la scrittura subordinata a zero
divergenze.

### 📐 Il modello in dettaglio

`integra_statistiche` in `scripts/registra_raccolta_coppa_diretta.py`,
verificato riga per riga contro il codice:

```
(1) le partite devono essere le stesse
    P(d) = { (Data, Casa, Ospite) }
    si procede  sse  P(raccolta) = P(statistiche)      (simmetrica, non inclusione)

(2) il foglio giocatori dev'essere lo STESSO dato, piu' preciso
    comuni = colonne(vecchio) ∩ colonne(nuovo)
    K      = (Data, Squadra, Giocatore)
    si procede  sse  nuovo non ha duplicati su K
    a = nuovo[comuni] ordinato per K ,  b = vecchio[comuni] ordinato per K

    per ogni c ∈ comuni:
        se numerica(a[c]) ∧ numerica(b[c]):
            divergenti += #{ i : |a_i − b_i| > 0.0006 }        (NaN → −9e9 su entrambi)
        altrimenti:
            etichette[c] = #{ i : lower(a_i) ≠ lower(b_i) }    (dichiarato, NON bloccante)

(3) si scrive  sse  divergenti = 0
```

**Perché 0.0006 e non 0.001 né 0.** Il primo consegnato è arrotondato alla
terza cifra: fra il valore troncato e quello pieno la differenza legittima
massima è **mezzo passo, 0.0005**. La soglia è quel mezzo passo più un margine
per la rappresentazione binaria — ammette l'arrotondamento e **nient'altro**:
7.5 contro 1.234 non passa, ed è il caso che un test verifica apposta.

**Perché K = (Data, Squadra, Giocatore), ed è qui che si era rotto.** La chiave
di ordinamento dev'essere **stabile fra le due fonti**, altrimenti il confronto
non misura i valori: misura il disallineamento. Prima ordinavo sulle prime otto
colonne in comune — `Competizione, Turno, Data, Casa, Ospite, Lato, Squadra,
Giocatore` — e `Turno` è **un'etichetta scritta dalla fonte**, non l'identità
della riga. Sulla Carabao Cup i due consegnati la scrivono in due modi:

| | raccolta base | file statistiche |
|---|---|---|
| primo turno | `1/64 FINALE` | `1° turno` |
| ottavi | `1/8 FINALE` | `4° turno (ottavi)` |
| semifinali | `SEMI FINALI` | `Semifinali (andata)` / `(ritorno)` |
| quarti, finale | `QUARTI DI FINALE`, `FINALE` | `Quarti di finale`, `Finale` |

Le due tabelle finivano in ordine diverso e il confronto le leggeva riga *i*
contro riga *j*. Esito, ri-derivabile dalla storia di git (`git show
HEAD:files/diretta_efl_cup_2526/stat_giocatori.csv`):

```
chiave vecchia (8 colonne, Turno compreso) → 122.401 celle divergenti
chiave nuova   (Data, Squadra, Giocatore)  →       0 celle divergenti
duplicati sulla chiave nuova               →       0   (su tutte e quattro le coppe)
```

**Stesso dato, due risposte.** Il controllo bocciava il file buono, e lo
bocciava con un numero grosso — cioè nella forma che sembra di più una scoperta.
Le 152 righe che coincidevano anche con la chiave vecchia sono quarti e finale,
gli unici due turni che le due fonti scrivono uguale a meno del maiuscolo: se
avessi guardato *quali* righe divergevano invece di quante, la diagnosi era lì.

### Il risultato, quattro coppe

| coppa | righe giocatore | celle divergenti | righe squadra | partite | periodi |
|---|--:|--:|--:|--:|---|
| Coppa Italia | 1.307 | **0** | 272 | 45 | 90/90/90 + **2** suppl. |
| DFB-Pokal | 1.979 | **0** | 406 | 63 | 126/126/126 + **28** suppl. |
| FA Cup | 1.974 | **0** | 406 | 63 | 126/126/126 + **28** suppl. |
| EFL Cup (Carabao) | 2.855 | **0** | 546 | 91 | 182/182/182, **nessuna** suppl. |

**843.960 celle numeriche confrontate** (righe × 104 colonne in comune), zero
divergenti oltre l'arrotondamento: il file nuovo aggiunge `ID partita` e i
decimali per intero senza cambiare **un solo valore**.

⭐ **È il primo dato di coppa che separa i due tempi**, cioè esattamente la forma
che chiede il residuo aperto delle Fasi 96/99 (il secondo tempo è mal calibrato
perché è *game-state*). Per i campionati lo stesso dato esiste dalla Fase 131.

**L'assenza che non è un buco.** La Carabao non ha righe «Supplementari», e la
tentazione è archiviarla come raccolta incompleta. È il **regolamento**: dal
2018-19 la EFL Cup va dritta ai rigori in ogni turno tranne la finale, e la
finale 2025-26 è finita 0-2 nei 90 minuti. La conferma non è una nota di
formato ma il **dato indipendente**: nelle 91 partite non c'è **un solo evento**
oltre il 90° (`eventi.csv` ha 1° tempo, 2° tempo e Rigori), contro 6 / 131 / 142
eventi supplementari delle altre tre coppe. Nessun periodo perso per strada: non
c'era. (R4: un'anomalia si dichiara **anche** quando non è un errore.)

**L'aggancio.** `aggancio_statistiche_squadra.csv`, `game_id` + `club_id`. Le
righe senza `game_id` sono **esattamente** quelle della finale che `games.csv`
non contiene — 6 per coppa, cioè 2 squadre × 3 periodi: 400/406 su Coppa Italia,
Pokal e FA Cup. La **Carabao fa eccezione a 546/546**: è l'unica delle quattro
la cui finale la fonte automatica ha. Completezza complessiva dopo l'ingresso:
**47.114 righe raccolte, 40.331 agganciate (86,2%)** — il resto è il tetto
dichiarato della Coupe de France (§5-octies).

**Stato d'uso: raccolto, non usato.** Nessun modello legge queste colonne.
Mancano Copa del Rey e Coupe de France: la porta le accetta con lo stesso
comando.

**Lezione.** *Quando un controllo boccia, la prima domanda non è «quanto
diverge» ma «quali righe».* Un conteggio grosso ha l'aria di una scoperta, e
122.401 su un dato identico riga per riga è la stessa cifra che avrebbe prodotto
una raccolta completamente sbagliata. La differenza si vede solo nel dettaglio —
e lì c'era, perché le uniche righe *non* divergenti erano quelle dei due turni
che le due fonti scrivono nello stesso modo. **Una chiave di confronto non è mai
un dettaglio implementativo: è ciò che decide che cosa si sta confrontando.**

---

## Fase 139-sexies — «Lione» non è «Olympique Lyon», e «Red Star» non è di Belgrado

**Obiettivo.** Integrare le statistiche della **Coupe de France** — la sesta e
ultima coppa consegnata — con la stessa porta delle altre. Ma la coppa francese
è quella che il progetto ha sempre trattato come un caso perso: **0/201**
partite con `game_id`, **19,7%** dei giocatori agganciati, e una spiegazione già
scritta due volte («la fonte automatica è Wikipedia, non ha identificatori»).
Verificare se quella spiegazione copre *tutto* il buco o solo una parte.

**Ragionamento.** La spiegazione strutturale è vera e resta vera: senza
`game_id` dall'altra sponda non si costruisce il ponte. Ma «i club francesi
minori non sono nel registro in nessuna grafia» (Fase 139-quater) è
un'affermazione **sui minori**, e non era mai stata verificata sui **maggiori**.
La Coupe de France dai 32esimi in poi la giocano i club di Ligue 1, che nel
registro ci sono di sicuro. Se non si agganciano, il problema non è il dato.

### 1 · L'esonimo, ancora

Elencati i club che dai 32esimi in poi restavano senza `club_id`: **41 su 64**,
e sei di quei nomi sono `Lilla`, `Lione`, `Marsiglia`, `Nizza`, `PSG`,
`Strasburgo`. Non è un caso nuovo — è **lo stesso** della Fase 139-bis, dove i
club tedeschi arrivavano come `Stoccarda`, `Friburgo`, `Colonia`. diretta.it è
un sito italiano e traduce le città straniere, e la regola del sottoinsieme non
può salvare un nome che col registro non condivide **un solo token**:

```
normalizza("Lione")          = {lione}
normalizza("Olympique Lyon") = {olympique, lyon}
                               intersezione = ∅  →  nessun candidato
```

Verificati due volte, come vuole il file: `candidati()` = **1** sul registro, e
poi la prova indipendente su `games.csv` — **34 partite di Ligue 1 2025-26** a
testa, che è il numero giusto per un campionato a 18 squadre. Aggiunti in
`club_matching.ALIAS` (non in `ALIAS_COPPA`: un esonimo italiano vale per
qualunque fonte in lingua italiana, non solo per questa coppa).

### 2 · E nella stessa verifica, due falsi positivi

Guardando l'elenco dei club **risolti** — non solo di quelli mancanti — due
nomi non tornavano: `Lusitanos` e `Pirae`, agganciati, in mezzo a PSG e
Marsiglia. Un club dilettantistico che si aggancia dove tutti gli altri no è
sospetto per costruzione.

| nome diretta.it | agganciato a | chi è davvero | verdetto |
|---|---|---|---|
| `Red Star` | **Red Star Belgrade** (159) | Red Star FC, Ligue 2 (Saint-Ouen) | ❌ falso positivo |
| `Lusitanos` | **FC Lusitanos** (28958) | US Lusitanos Saint-Maur, National 2 | ❌ falso positivo |
| `Pirae` | AS Pirae (17782) | AS Pirae, Tahiti Ligue 1 | ✅ **giusto** |

La diagnosi non è per somiglianza di nome — è per **dove quei `club_id` giocano
davvero** (R5 passo 2, informazione indipendente):

```
159    190 partite   SER1, CL, CLQ, EL, ELQ      → Stella Rossa di Belgrado
28958    8 partite   CLQ, ELQ  (2012-2016)       → FC Lusitanos, Andorra
17782    1 partita   KLUB      (2021)            → AS Pirae, Mondiale per club
```

E Wikipedia, dall'altro lato, scrive la divisione accanto a ogni nome: `Red Star
FC` = **L2**, `US Lusitanos Saint-Maur` = **N2**, `AS Pirae` = *Tahiti Ligue 1*.
Il terzo caso è quello che conta di più per il metodo: **sembrava** lo stesso
errore degli altri due e non lo era. La Coupe de France ammette davvero le
squadre d'oltremare, e bloccare `Pirae` «per prudenza» avrebbe tolto un aggancio
giusto. La prudenza si applica **dopo** aver guardato, non al posto di guardare.

Nessuno dei due falsi positivi si ripara con un alias: il club vero **non è nel
registro**, quindi l'unico esito corretto è **vuoto**. Vivono in
`NON_AGGANCIARE`, che finora conteneva solo squadre riserve e ora ha una seconda
classe dichiarata — gli **omonimi stranieri**.

### 📐 Il modello in dettaglio

Nessuna matematica nuova: la regola di aggancio è quella della Fase 139-quater
(`candidati` per sottoinsieme di token, accettato solo se **unico**). Qui
cambiano due tabelle, e vale la pena scrivere *cosa* sono:

```
candidati(n) = ∅                                     se lower(n) ∈ NON_AGGANCIARE
             = { c : token(nome_c) = A(token(n)) }   se esiste un match esatto
             = { c : A(token(n)) ⊆ token(nome_c) }   altrimenti
             dove A = ALIAS applicato sull'insieme di token

aggancia(n)  = l'unico elemento di candidati(n)   se |candidati(n)| = 1
             = None                               altrimenti
```

`ALIAS` **aggiunge** agganci che i token non possono trovare;
`NON_AGGANCIARE` **toglie** agganci che i token trovano e sono sbagliati. Sono
le due direzioni dello stesso errore, e servono entrambe: la prima costa
copertura, la seconda costa *correttezza* — ed è la più cara, perché non si vede.

### Il risultato

| | prima | dopo |
|---|--:|--:|
| club → `club_id` | 29/202 | **33/202** |
| giocatori → `player_id` | 492 (19,7%) | **932 (37,4%)** |
| titolari | 295 (21,3%) | **546 (39,4%)** |
| righe di evento | 456 | **844** |
| statistiche per giocatore | 399 | **750** |
| stat. di squadra con `club_id` | 168/476 | **234/476** |
| **completezza, sei coppe** | 40.331 / 47.590 (85,3%) | **41.510 / 47.590 (87,8%)** |

Il `+4` netto sui club è `+6` esonimi `−2` falsi positivi. Le altre cinque coppe
sono **immutate**, verificato sul giro completo degli agganci.

Resta **0/201** sul `game_id`: quello sì è strutturale, e non si muove finché la
fonte automatica di quella coppa è Wikipedia.

### Le statistiche di squadra, e una copertura che va letta

476 righe, 87 partite su 201, 35 metriche. È l'unica delle cinque coppe con la
copertura **a scalini**, e il taglio è netto:

| turni | partite | righe | metriche piene |
|---|--:|--:|--:|
| dai 32esimi alla finale | 63/63 | 378 | ~27 su 29 |
| 7° e 8° turno (dilettanti) | 24/138 | 98 | **1,2 su 29** |

Le 98 righe scarne portano **i soli cartellini**, e non è un difetto: esistono
*perché* c'è stato un cartellino. La prova è il confronto con l'altra fonte
della stessa raccolta — `eventi.csv`, che ha i cartellini col minuto:
**48/48 identiche** sulle righe «Totale», e **0 partite** con righe di
statistica senza nemmeno un cartellino negli eventi. È anche il motivo per cui i
periodi non si bilanciano (Totale 174, 2° tempo 160, 1° tempo 142): la riga di
un tempo esiste solo se in quel tempo è successo qualcosa. Le altre colonne sono
**vuote**, non zero — se fossero zero sarebbe un finto pieno (R6).

**La coerenza dei tre periodi, misurata** — un controllo che non costava niente
e non era mai stato fatto su una coppa (128 squadra-partita coi tre periodi):

```
1° tempo + 2° tempo = Totale
  29 metriche numeriche              126/126 additive
  5 metriche a rapporto «p% (n/d)»   n e d additivi 252/252
  Possesso palla (non additiva)      casa + ospite = 100 in 189/189 gruppi completi
```

⚠️ **La prima lettura del possesso era sbagliata, ed era mia**: «49 gruppi su
238 non fanno 100» veniva da un `groupby().sum()` che somma i `NaN` come zeri.
Righe con possesso 0% nel file: **zero**. Ci sono 98 righe dove il possesso
*manca*, e sono esattamente le righe scarne dei turni dilettantistici. Un
`NaN` letto come `0` è lo stesso errore che la regola R6 descrive — solo
commesso dal lettore invece che dalla fonte.

### Una guardia in più sulla porta d'ingresso

Ri-registrare la raccolta dopo aver cambiato gli alias, e poi re-integrare le
statistiche **dall'originale già archiviato**, sollevava `SameFileError` —
`copy2(x, x)` — **dopo** aver riscritto i due CSV e **prima** di aggiornare il
manifesto: la raccolta restava a metà. Ora la copia si salta quando sorgente e
destinazione sono lo stesso file. È il motivo per cui la §5-ter conserva gli
originali: rifare il lavoro da lì dev'essere la strada normale, non un caso
limite.

**Lezione.** *Una spiegazione strutturale corretta può coprire un buco più
piccolo di quello che sembra.* «La Coupe de France non ha identificatori» era
vero, ed è rimasto vero — ma spiegava l'80% del buco, non il 100%, e per due
fasi il restante 20% è stato archiviato insieme al resto. Il modo di
accorgersene è stato guardare l'elenco dei nomi mancanti **uno per uno** invece
del totale: sei righe su quaranta erano PSG, Marsiglia, Lione. **Un numero
aggregato non dice mai di che cosa è fatto**, e la stessa occhiata che ha
trovato i sei mancanti ha trovato i due agganciati per sbaglio.

---

## Fase 139-septies — Tre volte lo stesso errore: il controllo che boccia il dato buono

**Obiettivo.** Integrare le statistiche della **Copa del Rey**, la sesta e
ultima, e chiudere il secondo consegnato su tutte le coppe.

**Ragionamento.** Le prime quattro erano entrate senza toccare una riga di
codice. La Carabao aveva richiesto una correzione, la Coupe de France un'altra.
Il sospetto, arrivando alla sesta, non era «funzionerà» ma «cosa scriverà
diversamente *questa*»: e la risposta è arrivata due volte in due controlli
diversi, entrambi legittimi, entrambi tarati troppo stretti.

### 1 · «Le partite non coincidono»: 2 su 117

Il primo controllo si è fermato subito. Due partite «solo nella raccolta» e due
«solo nelle statistiche», stessa data e stesso avversario:

```
solo raccolta    ('03.12.2025', 'Ciudad Cieza', 'Levante')   ('29.10.2025', 'Ciudad Cieza', 'Cordoba')
solo statistiche ('03.12.2025', 'Cieza',        'Levante')   ('29.10.2025', 'Cieza',        'Cordoba')
```

**È un club solo, e non l'abbiamo dedotto: lo dice la fonte indipendente.**
`data/coppe_2526/partite.csv` ha esattamente quelle due partite sotto **CD
Cieza**, `club_id` **56725**, terza divisione — e la raccolta base risolveva già
`Ciudad Cieza` a quello stesso id. Le 14 righe di giocatore sono le stesse
persone riga per riga.

### 2 · «Un doppione»: e sono due persone

Corretto il primo, il secondo controllo si è fermato su una riga:

> `1 righe con la stessa (data, squadra, giocatore)`

`Fernandez Pol`, Reus FCR, 03/12/2025. Non è un doppione — la raccolta base lo
dimostra da sola, perché ha il **numero di maglia**:

| | numero | gruppo | rating | minuti |
|---|--:|---|--:|--:|
| Fernandez P. | **3** | Titolare | 5.9 | 90 |
| Fernandez P. | **24** | Panchina, entrato al 59' | 6.2 | 31 |

E i due rating del file di statistiche sono **5.9 e 6.2**. Sono due uomini, e la
chiave del confronto pretendeva un'unicità che il dato non ha.

### 📐 Il modello in dettaglio

Due tabelle di regole cambiano, entrambe **dentro** il confronto e nessuna sul
dato scritto.

**(1) Il sinonimo di club** (`coppe_aggancio.sinonimi_squadra`, verificato
contro il sorgente):

```
V = nomi di club nel foglio di RIFERIMENTO      (partite.csv della raccolta)
N = nomi di club nell'ALTRO foglio              (il consegnato nuovo)
residui:  N∖V  e  V∖N                            ← chi si appaia gia' alla lettera esce

proposte(n) = { v ∈ V∖N : token(n) ⊆ token(v)  ∨  token(v) ⊆ token(n) }
si accetta  n → v   sse   |proposte(n)| = 1
                     ∧   v e' proposto da UN SOLO n            (unicita' nei due sensi)
```

`{cieza} ⊆ {ciudad, cieza}` → accettato. Le tre condizioni sono le stesse di
`deduci_club` (Fase 139-quater) e servono per lo stesso motivo: «Ourense» fra
«Ourense CF» e «UD Ourense» sono **club diversi della stessa città**, e
indovinare lì è il caso «Brest» daccapo. Il sinonimo **si dichiara** nel
manifesto (`sinonimi_di_squadra_accettati`) e **non riscrive la colonna**: si
canonicalizza la chiave, non il dato.

**(2) La chiave del confronto riga per riga**, terza versione in tre coppe:

```
Fase 139-quinquies   (Competizione, Turno, Data, Casa, Ospite, Lato, Squadra, Giocatore)
                     → 122.401 celle «divergenti» su un dato identico  (Turno e' un'etichetta)
Fase 139-quinquies   (Data, Squadra, Giocatore)
                     → 1 «doppione» su due persone diverse             (troppo stretta)
Fase 139-septies     (Data, canon(Squadra), Giocatore, Stato)          ← quella buona
```

`Stato` ∈ {Titolare, Subentrato} separa i due Fernandez, è scritto uguale nei
due consegnati, e sulle altre cinque coppe **non cambia niente**: 0 doppioni
prima e 0 dopo. `canon` è la mappa del punto (1).

**Dove vive la regola, e perché lì.** `sinonimi_squadra` sta in
`src/data/coppe_aggancio.py`, non nello script. Non è pulizia: senza, la porta
d'ingresso accettava il file e lo script degli agganci perdeva le **27 righe**
di quelle due partite — `stat_giocatori` da 94,2% a **92,3%**, un calo che
sembra un limite del dato. È la lezione della Fase 139-quater applicata prima di
pagarla: **due copie della stessa regola divergono, e la divergenza non dà
errore.**

### Il risultato: sei coppe su sei

| coppa | righe | partite | supplementari |
|---|--:|--:|--:|
| Coppa Italia | 272 | 45 | 2 |
| DFB-Pokal | 406 | 63 | 28 |
| FA Cup | 406 | 63 | 28 |
| EFL Cup | 546 | 91 | 0 (regolamento) |
| Coupe de France | 476 | 87 / 201 | 0 |
| **Copa del Rey** | **692** | **114 / 117** | **52** |
| **totale** | **2.798** | **463** | |

Fedeltà del foglio giocatori sulle sei: **1.193.504 celle numeriche confrontate,
0 divergenti** oltre l'arrotondamento. Aggancio: **692/692** con `game_id` e
`club_id` — la Copa del Rey è, con la Carabao, una delle due coppe la cui finale
la fonte automatica contiene. Completezza sulle sei: **48.282 righe raccolte,
42.202 agganciate (88,0%)**.

### La copertura ha tre livelli, e nessuna colonna lo dice

Copa del Rey e Coupe de France non hanno una copertura piena né vuota: hanno
**tre livelli**, e li fa la fonte — meno il turno è professionistico, meno
pubblica.

| livello | metriche piene | dove |
|---|--:|---|
| completo (xG, possesso, passaggi…) | ~27 / 29 | Rey dai 1/16 + 15 partite del 2° turno; Coupe dai 32esimi |
| base (tiri, angoli, falli, fuorigioco, rimesse, punizioni, cartellini) | 8-10 | Rey: 13 partite del 2° turno |
| solo cartellini | 1-2 | Rey: 53 partite del 1° turno; Coupe: 24 dei turni 7-8 |

Il terzo livello non è un difetto e non è un finto pieno: quelle righe esistono
**perché** c'è stato un cartellino, le altre colonne sono `NaN` e non `0`, e il
conteggio combacia con `eventi.csv` — **106/106** sul Rey, 48/48 sulla Coupe.
Ma il livello **non è dichiarato da nessuna colonna**: si legge da quante
metriche sono piene, e chi userà questo dato deve guardarlo prima.

### ⭐ E una semantica che nessuno aveva verificato: `Totale` non è il 90'

Le quattro coppe con i supplementari permettono un test che non costa niente:

```
1° tempo + 2° tempo + Supplementari = Totale     2.228 / 2.228 celle
1° tempo + 2° tempo                 = Totale       628 / 2.232
```

**`Totale` è la partita intera, supplementari compresi.** Non era scritto da
nessuna parte, e la lettura sbagliata non dà errore: dà numeri più piccoli su
13-14 partite per coppa — esattamente quelle dove il dato conta di più.

**Lezione.** *Tre coppe di fila, tre volte lo stesso errore: un controllo giusto
tarato su una chiave che il dato non rispetta.* Il turno è un'etichetta della
fonte, il nome del club è una grafia della fonte, e (data, squadra, giocatore)
non è un'identità perché due persone possono chiamarsi uguale. Ogni volta il
controllo ha risposto con qualcosa che **sembrava una scoperta** — 122.401 celle
divergenti, due partite mancanti, un doppione — e ogni volta il dato era giusto.
La domanda che ha risolto tutte e tre è la stessa: **non «quanto diverge» ma
«quali righe, e perché proprio quelle».**

---

## Fase 139-octies — «Le colonne ci sono» non è «si uniscono»

**Obiettivo.** Domanda dell'utente: *«verifica che siamo in grado di incrociare
tutti i dati relativi a queste partite: allenatore, arbitro, statistiche di
squadra, meteo, 11 titolari + sostituzioni + statistiche individuali»*. Non
«esistono le tabelle» — quello si vede dagli schemi. **Si uniscono, partita per
partita?**

**Ragionamento.** La domanda ha una risposta facile e sbagliata: elencare le
colonne di ogni file e dire di sì. Ogni blocco vive in una tabella diversa, con
una chiave diversa, da una fonte diversa; e la Fase 139-ter aveva già mostrato
cosa costa non contarlo — **8.475 righe di evento raccolte e collegate a
niente**, invisibili perché le percentuali su partite e formazioni erano al 99%.
Quindi: si conta riga per riga, e si scrive uno script perché il numero resti
ri-calcolabile.

**Alternative considerate.**

1. *Una tabella sola, «quante partite hanno tutto».* È quella che ho scritto per
   prima, ed era **sbagliata in due modi contemporaneamente** (vedi sotto).
2. *Elencare le colonne per file.* Non risponde: dice che il dato esiste, non
   che si unisce a quella partita.
3. *Fidarsi delle percentuali di aggancio già pubblicate* (99,8%, 94,7%…).
   Sono per **foglio**, non per **partita**: una coppa può avere tutti i fogli
   agganciati al 99% e pochissime partite con *tutti* i blocchi insieme.

**Scelta.** `scripts/verifica_incrocio_coppe.py`, che produce **quattro**
tabelle. Quattro e non una perché il conteggio unico confonde tre cose diverse.

### 📐 Il modello in dettaglio

Nessuna matematica: è una misura, e la formula è la definizione di «incrociabile».

```
perimetro   = { partite : dentro_perimetro }                     580 su 662

blocchi automatici (chiave game_id, fonte player-scores)
  arbitro      = arbitro ≠ ∅
  allenatori   = allenatore_casa ≠ ∅  ∧  allenatore_ospite ≠ ∅
  undici       = |{ club : #titolari(game_id, club) = 11 }| = 2      ← DUE, non ≥1
  minuti       = #{ righe con minuti ≠ ∅ } > 0

blocchi manuali (chiave ID partita, fonte diretta.it)
  sostituzioni = #eventi di tipo «Sostituzione» > 0
  stat. indiv. = #righe in aggancio_statistiche > 0
  stat. squadra= #righe in aggancio_statistiche_squadra > 0

incrociabile(p) = p ∈ perimetro
                ∧ ∃ ponte: ID partita → game_id
                ∧ ⋀ (tutti i blocchi delle due sponde)
```

**Perché `undici` pretende DUE squadre e non almeno una.** Una formazione sola
non è metà del dato: è un dato inutilizzabile per qualunque confronto fra le due
squadre, che è l'unica cosa per cui serve. Con la soglia «≥1» la FA Cup
risulterebbe più coperta di quanto sia.

### Il mio primo conteggio era sbagliato in due modi, e vale la pena dirlo

La prima versione dava questa riga:

```
Coupe de France   201 partite   arbitro 0   allenatori 0   undici 0   sostituzioni 0
                                stat_ind 0  stat_squadra 0
```

Letta così: «della coppa francese non abbiamo niente». **È falso.** La Coupe de
France ha 2.495 righe di formazione, 2.792 eventi, 1.924 statistiche individuali
e 476 di squadra. Contavo i blocchi **manuali** sulla chiave **automatica**, e
quella coppa di `game_id` non ne ha nemmeno uno: il conteggio misurava il ponte,
non il dato. E la FA Cup risultava 62/123 perché al denominatore mettevo tutte
le partite invece del **perimetro** — 60 di quelle non sono un buco, non sono
mai state chieste.

> **fuori perimetro ≠ buco · senza ponte ≠ assente · presente ≠ unibile**

Sono tre errori diversi con lo stesso effetto: far sembrare mancante ciò che c'è.

### Il risultato

**1 · Fonte automatica** (sul perimetro): arbitro 378/379 fuori dalla Francia,
allenatori 376, undici 376, minuti 348.
**2 · Raccolta manuale** (sul raccolto): sostituzioni 442/580, statistiche
individuali 366, di squadra 463.
**3 · L'incrocio vero**, tutti i blocchi sullo stesso `game_id`:

| coppa | nel perimetro | incrociabili | quota |
|---|--:|--:|--:|
| FA Cup | 63 | 62 | **98,4%** |
| EFL Cup | 91 | 89 | **97,8%** |
| DFB-Pokal | 63 | 61 | **96,8%** |
| Coppa Italia | 45 | 40 | **88,9%** |
| Copa del Rey | 117 | 44 | 37,6% |
| Coupe de France | 201 | 0 | 0% |
| **totale** | **580** | **296** | **51,0%** |

Senza la Coupe de France — che è un problema di natura diversa — **296/379,
78,1%**.

**4 · Il giro completo, ed è quello che conta**: dal titolare (player-scores)
alla **sua** riga di statistica (diretta.it), per `player_id`. Le tabelle 1-3
possono essere verdi e questa rossa: la partita c'è da entrambe le parti, le
**persone** no.

```
DFB-Pokal      1.361 / 1.364   99,8%
Coppa Italia     876 /   880   99,5%
FA Cup         1.353 / 1.364   99,2%
EFL Cup        1.975 / 2.002   98,7%
Copa del Rey     924 /   990   93,3%
TOTALE         6.489 / 6.600   98,3%
```

**E la prova che il join si fa davvero**, non solo che i conteggi tornano —
`--partita 4631307`, Empoli-Reggiana del 15/08/2025:

```
arbitro                              Andrea Calzavara
allenatori                           Guido Pagliuca / Davide Dionigi
stadio, spettatori                   Carlo Castellani, 1.894
moduli                               3-5-2 flat / 3-4-2-1
titolari                             22, tutti e 22 con player_id
titolari con statistica individuale  22 / 22
sostituzioni                         18
statistiche di squadra               6 righe, 1° tempo / 2° tempo / Totale
meteo                                None
```

### I tre motivi del «no», e sono diversi fra loro

1. **Coupe de France (201)** — nessun `game_id`: la sua fonte automatica è
   Wikipedia, che non porta identificatori. Assenza **a monte**, non nostra. I
   dati manuali si incrociano fra loro; con arbitro/allenatori/formazioni no,
   perché dall'altra parte non esistono.
2. **Copa del Rey (73)** — il **First Round**, 56 partite, ha **zero**
   statistiche individuali: diretta.it non le pubblica per il turno
   dilettantistico. Dal Round of 32 in poi la coppa è al **100%**. È lo stesso
   taglio a livelli già trovato sulle statistiche di squadra (Fase 139-septies):
   non un difetto della raccolta, una politica della fonte.
3. **Le tre finali** — `games.csv` non le contiene.

### ⚠️ Il meteo: non c'è, e non è un dettaglio

**Zero su 662.** Non «manca in qualche partita»: non esiste in nessuna tabella
del progetto per il 2025-26. L'infrastruttura c'è ed è **prospettica**
(`fetch_stadi_coordinate.py` + `stagione_2026_2027/giornaliero/`): raccoglie la
*previsione* a 16 giorni per il 2026-27, e una previsione all'indietro non si
ricostruisce — dopo esiste solo il consuntivo. Cosa servirebbe, misurato:

| pezzo | stato |
|---|---|
| coordinate degli stadi | **59 su 422** stadi di coppa (110 partite su 662): le 90 raccolte coprono i club delle 5 leghe, non i minori |
| fonte storica | `open-meteo.com`, raggiungibile e senza chiave (`MANUALE_SOPRAVVIVENZA` §1), **mai usata** |
| natura del dato | sarebbe un **consuntivo `post`**, non la previsione `pre` — sotto R8 sono due cose diverse, e a un modello serve la seconda |

**Lezione.** *Le percentuali di aggancio già pubblicate erano tutte al 99%, e la
metà delle partite non si incrocia lo stesso.* Non è una contraddizione: quelle
erano per **foglio** («quante righe di evento hanno un `player_id`»), questa è
per **partita** («questa partita ha tutti i blocchi insieme»). Sono domande
diverse e danno numeri diversi, e la seconda è quella che decide se un modello
si può addestrare. **Una copertura alta su ogni pezzo non implica un pezzo
intero da nessuna parte.**

---

## Fase 140 — Il database allenatori: il nome non è un'identità, e la panchina non è un contratto

**Obiettivo.** Aprire il fronte **allenatori**, che il
`docs/PIANO_DATABASE_GIOCATORI.md` progetta da giorni (§1.6, voci F1-F32) e che
`docs/AUDIT_FONTI_GIOCATORI.md` ha auditato senza che una riga di codice lo
toccasse. Non «misurare se l'allenatore conta»: **prima costruire il dato**, e
descriverlo onestamente. Un modello su un dato non descritto è un modello su
qualcos'altro.

**Ragionamento.** Il piano dice una cosa sola con certezza: il dato-cardine
esiste già ed è `games.csv` dello **stesso** dataset che il progetto usa dalla
Fase 67 per i valori rosa. Nessuna fonte nuova, nessuna licenza nuova, nessun
matching per nome dei club — solo l'unico file grande di player-scores mai
importato. La Fase 125 lo aveva già letto per l'arbitro, ma da uno script
`_run_*` una tantum che scaricava 708 MB da Kaggle a ogni esecuzione: il dato
non era **strutturale**, e alla sessione dopo non esisteva più.

**Alternative considerate.**

1. *Partire dalle statistiche di stile* (xG/PPDA/deep degli snapshot, per
   misurare subito la «firma» dell'allenatore). Scartata: è il passo 2. Senza i
   mandati non c'è niente su cui fare il join, e la firma stilistica misurata
   su mandati sbagliati è una firma di qualcun altro.
2. *Prendere `club_games.csv`*, che offre la vista per-club già pronta.
   Verificato prima di deciderlo, e la verifica ha risposto da sola:
   ricostruito da `games.csv` in otto righe, **0 celle divergenti su
   1.957.076**. È un duplicato esatto e algoritmico. Conservato lo stesso
   (regola §5-ter: raccogliere non è usare), ma nessun codice lo legge.
3. *Usare `clubs.coach_name`*, che il repo ha già in casa. **No**: è
   l'allenatore **corrente** del club, senza data (403/796 non nulli).
   Applicarlo a una partita del 2019 le attribuisce il tecnico di oggi. È la
   trappola R8 in forma pura, e il modulo non la legge apposta.

**Scelta.** `files/player_scores/games.csv.gz` (+ `club_games`, `competitions`)
come fonte congelata, `src/data/allenatori.py` come modulo strutturale — stessa
architettura di `careers.py`: una vista lunga (`load_partite`), una vista
derivata (`panchine`), e **una sola funzione sicura** per le feature
(`esperienza_prima`, forma R8). Più il workflow d'import esteso, perché un
re-import non se li dimentichi.

### Il risultato: la copertura è ottima, e non è la notizia

`games.csv` copre il perimetro **esattamente**: 16.111 partite nelle 5 leghe ×
9 stagioni, le stesse righe degli snapshot congelati. L'allenatore manca in **2
club-partita su 32.222** (99,994%) — ed è una partita sola, Nantes-Tolosa del
17/05/2026, a cui alla stessa data mancano anche l'arbitro e ogni giocatore.
L'audit diceva «meno dello 0,3% mancante»: era pessimista di 50 volte.

Ma la copertura è la domanda facile. Le due che contano hanno risposto peggio.

### 1 · Il nome non è un'identità — e sbaglia in **due** direzioni

La fonte non ha un id-allenatore: solo una stringa. Il difetto **noto**
dall'audit è che la stessa persona compare con due grafie, con intervalli
disgiunti — la fonte ha cambiato ortografia in corsa:

| chiave | grafia | partite | da → a |
|---|---|--:|---|
| `ivan juric` | Ivan Juric | 231 | 2017-08-20 → 2025-04-06 |
| | Ivan Jurić | 11 | 2025-08-24 → 2025-11-09 |
| `bruno genesio` | Bruno Génésio | 209 | 2017-08-05 → 2025-05-17 |
| | Bruno Genesio | 34 | 2025-08-17 → 2026-05-17 |

Normalizzare li unisce, e costa poco: nel perimetro **496 grafie → 494 chiavi**,
2 gruppi, **485 partite = 3,01%**; globalmente 7.031 → 6.995, 36 gruppi.

Il difetto **non noto** è l'opposto, ed è quello pericoloso: due uomini diversi
con lo stesso nome diventano una riga sola, e nessuna normalizzazione lo ripara.
Il test che lo trova non ha bisogno di fonti esterne — è di impossibilità
fisica, nello spirito della regola R5: **nessuno allena due club lo stesso
giorno**. Esito: **11 nomi globali sono dimostrabilmente ≥2 persone**, 29
collisioni. Il più grosso è dentro il nostro perimetro:

> `michel` — il 2022-10-02 la stessa stringa siede sulla panchina del **Girona**
> (ES1) e su quella dell'**Olympiakos** (GR1). Sono Míchel Sánchez e Míchel
> González, due allenatori spagnoli diversi. 13 collisioni fra il 2022 e il
> 2025, e la stringa raccoglie **nove club** in nove anni.

`luis castro` è l'altro caso nel perimetro (5 collisioni: Shakhtar e
Panetolikos lo stesso giorno del 2019). Con una finestra di 7 giorni invece che
di 0 i nomi sospetti salgono a 43 — ma quella finestra include i passaggi lampo
veri fra due club, quindi è un limite superiore, non un verdetto.

**Non si risolve qui.** Sciogliere un omonimo richiede una fonte di identità
esterna (uno strato 2, come `wikidata_identity.py` per i giocatori). Ciò che si
può fare oggi è **impedire che entri in una feature senza che nessuno lo sappia**:
`conflitti_identita()` lo elenca, e un test lo tiene elencato.

### 2 · La panchina non è un contratto — e chi lo assume conta 696 cambi che non ci sono

Il campo si chiama `manager_name`, e la tentazione è leggerlo come «l'allenatore
in carica». Il dato dice di no, e lo dice da solo:

| data | competizione | avversario | allenatore |
|---|---|---|---|
| 2021-11-20 | Bundesliga | Hoffenheim | Jesse Marsch |
| 2021-11-24 | Champions | Club Brugge | **Achim Beierlorzer** |
| 2021-11-28 | Bundesliga | Leverkusen | Jesse Marsch |
| 2021-12-03 | Bundesliga | Union Berlin | Jesse Marsch |
| 2021-12-07 | Champions | Manchester City | **Achim Beierlorzer** |
| 2021-12-11 | Bundesliga | Mönchengladbach | Domenico Tedesco |

Un contratto non si alterna a giorni alterni. Un **vice in panchina per una
partita** sì: squalifica, malattia, turno di coppa lasciato all'assistente. Il
campo registra *chi sedeva in panchina quella partita*, che è un'altra cosa — e
i casi hanno tutti un nome verificabile: Stuivenberg per Arteta il 1/1/2022,
Vivas per Simeone il 4/1/2025, Hermann per Heynckes il 10/2/2018, Critchley per
Klopp il 4/2/2020.

La firma del fenomeno è il pattern **A → X → A**: lo stesso allenatore prima e
dopo. Sono **836 mandati su 13.810 (6,05%)**, di cui **412 di una partita sola**.
Chi non li riassorbe conta due cambi in panchina finti per ciascuno: **4.416
cambi in corso di stagione contro i 3.720 veri, +18,7%**.

**Terzo modo di sbagliare, più banale e altrettanto efficace**: tagliare i
mandati sul solo campionato. Sui club del perimetro sono **1.190 sulla timeline
completa contro 906 sulla sola lega — 284 spariti**, quasi tutti traghettatori
di una partita in coppa. Una panchina ha una timeline sola, e ci passano
campionato, coppa nazionale ed Europa in ordine di data.

### 3 · L'esperienza è **visibile al dataset**, non globale

L'audit lo aveva già scritto (F26) e qui è confermato dal codice, non citato:
`games.csv` per le top-5 comincia il **2012-08-10**, e Brasile, Argentina, MLS,
Giappone e Arabia entrano solo nel **2025**. Contare le partite precedenti e
chiamarlo «esperienza in carriera» produce falsi conclamati:

| allenatore | prima partita **visibile** | dove |
|---|---|---|
| Carlo Ancelotti | 2012-08-11 | Ligue 1 |
| José Mourinho | 2012-08-19 | Liga |
| Claudio Ranieri | 2013-08-10 | Ligue 1 |
| Roy Hodgson | 2012-06-11 | Europei |
| Ronald Koeman | 2012-07-31 | preliminari di Champions |

Per questo la funzione si chiama `esperienza_prima` e non
`esperienza_globale`, e restituisce `censurata`: quando è True i totali sono un
**limite inferiore**. Al 1° agosto 2025, dei **145 allenatori** poi in panchina
nelle 5 leghe, **22 (15,2%) non hanno nessuna partita precedente visibile** e
**31 dei restanti sono censurati**.

⚠️ E `censurata=False` **non** vuol dire «esperienza completa»: il flag vede
solo la censura **temporale**, al bordo della competizione. Quella di
**copertura** — chi ha allenato dove la fonte non guarda: seconde divisioni,
giovanili, campionati entrati nel 2025 — dall'interno del dataset non è
rilevabile. Il controesempio è **Guardiola**: prima partita visibile il
2013-07-27 col Bayern, `censurata=False`, e quattro stagioni al Barcellona
(2008-2012) invisibili perché la Liga nel dataset comincia nell'agosto 2012.

### 📐 Il modello in dettaglio

Nessuna statistica nuova: le formule qui sono **definizioni**, ed è esattamente
il punto — le tre trappole di sopra nascono tutte da una definizione data per
scontata. Verificate riga per riga contro `src/data/allenatori.py`.

**(1) La chiave del nome** (`normalizza_nome`):

```
k(nome) = collassa_spazi( minuscolo( senza_accenti( NFKD(nome) ) ) )
          con  {'-', "'", '.'} → ' '

senza_accenti(s) = "".join(c for c in s if not unicodedata.combining(c))
```

NFKD scompone «ć» in «c» + segno combinante e il filtro toglie il secondo: è
questa riga, e nessun elenco di alias scritto a mano, a unire Jurić e Juric.
Perché anche trattino/apostrofo/punto: «Sanchez-Flores» e «Sanchez Flores» sono
lo stesso uomo, e le iniziali puntate compaiono nelle grafie brevi.
**Il costo di questa scelta è dichiarato**: k non è iniettiva sulle persone, e
la (3) misura di quanto.

**(2) La segmentazione dei mandati** (`panchine`), ordinando per
`(club_id, date, game_id)`:

```
nuovo(i)   = [ k(i) ≠ k(i−1) ]     con i−1 nello stesso club (True alla prima riga)
mandato_id = cumsum(nuovo)
```

Un `cumsum` su un confronto con la riga precedente, e non l'intervallo
`(min data, max data)` di quel nome in quel club. La differenza non è di stile:
con l'intervallo, **Allegri risulta al Milan dal 2010 al 2026** — perché ci è
tornato — e quindi «sovrapposto a sé stesso» alla Juventus per **3.546 giorni**.
Era il falso positivo che il primo tentativo di test sugli omonimi produceva:
non erano omonimi, erano **ritorni**.

**(3) Il conflitto di identità** (`conflitti_identita`), su `G` giorni di
finestra:

```
conflitto(k) ⟺ ∃ (d₁,c₁), (d₂,c₂) osservate per k  con  c₁ ≠ c₂  ∧  |d₁ − d₂| ≤ G
```

`G = 0` è il verdetto netto (nessuno allena due club lo stesso giorno: 11 nomi);
`G = 7` è il sospetto (43 nomi, ma include i passaggi lampo veri). Il test è
volutamente **interno**: non chiede nessuna fonte esterna, quindi non può
essere rimandato in attesa di procurarsela.

**(4) L'interruzione e la ricucitura** (`panchine(ricuci=True)`), con soglia
`S = 1` partita:

```
interruzione(m)  ⟺  precedente(m) ≠ ∅  ∧  precedente(m) = successivo(m)
assorbibile(m)   ⟺  interruzione(m)  ∧  partite(m) ≤ S

gruppo(mᵢ) = gruppo(mᵢ₋₂)   se assorbibile(mᵢ₋₁) ∧ stesso club ∧ k(mᵢ) = k(mᵢ₋₂)
ospite(mᵢ) = ultimo gruppo NON assorbito dello stesso club
```

`S = 1` non è tarato su una metrica — non c'è una metrica: è la soglia che
ricuce **solo** ciò che il pattern A→X→A rende quasi certo (una partita sola:
412 casi su 836) e lascia in piedi gli altri 424, dove «il vecchio è tornato
dopo un mese» e «il vice ha traghettato un mese» non sono distinguibili senza
una fonte sui contratti. La soglia è un parametro, e chi la alza sa cosa sta
comprando.

L'identità che tiene onesta la ricucitura, e che un test verifica:

```
Σ partite(mandati ricuciti) + Σ partite_altrui  =  righe di load_partite()
                175.816     +        412        =        176.228            ✅
```

Le partite del vice **non spariscono**: escono dai mandati ed entrano in
`partite_altrui` del mandato che le ospita. Una ricucitura che perdesse righe
sarebbe una correzione al dato travestita da vista derivata.

**(5) La censura a sinistra** (`esperienza_prima`):

```
censurata(k) ⟺ primo_incarico(k) ≤ d₀( competizione_d'esordio(k) ) + 90 giorni
d₀(c) = min data osservata nella competizione c
```

Il bordo è **per competizione**, non uno solo: le top-5 cominciano nel 2012, il
Brasile nel 2025. Un bordo unico dichiarerebbe «esordiente» mezzo campionato
brasiliano. I 90 giorni sono una finestra di mercato più preparazione: chi
compare entro un'estate dall'apertura della raccolta era già lì prima, e il
dataset non può saperlo. Numeri: **1.064 allenatori su 4.194 (25,4%)** censurati
al 1° agosto 2020.

**Lezione.** *La copertura di un campo non dice quasi niente sulla sua
affidabilità.* Qui è al **99,994%**, ed è precisamente per questo che le tre
trappole sono pericolose: nessun controllo di completezza le vede, perché non
c'è niente di vuoto. Il nome c'è sempre — ma a volte è di due persone; il
mandato si ricostruisce sempre — ma a volte è una squalifica; l'esperienza si
conta sempre — ma parte da dove comincia il file. È la regola **R6** (il buco
peggiore non è il `NaN`, è il finto pieno) applicata a un fronte nuovo, e vale
la pena scriverlo: le tre si sono trovate **guardando il dato**, non
rileggendo il piano che lo descriveva da giorni.

**Stato.** Nessun modello legge questo modulo, e nessuna misura di valore
predittivo è stata fatta: **è infrastruttura**. Il passo successivo naturale è
il join dei mandati con gli snapshot ricchi (xG/PPDA/deep) per il test che
l'utente ha descritto — lo *stesso* allenatore su **due squadre diverse** — e
va fatto sapendo che sul perimetro gli allenatori con abbastanza partite in
≥2 club sono pochi, e che il tetto informativo delle 100+ fasi precedenti non
si sospende per un fronte nuovo.

---

## Fase 141 — Un 503 alla 22ª partita su 58, e le 21 già raccolte buttate via

**Obiettivo.** Rimettere in piedi il workflow `smarkets-prematch.yml`, fallito
l'**08/08/2026** sul giro di lungo raggio delle 06:24 (`All jobs have failed`,
7'47" prima di morire). E, visto che la raccolta pre-partita ha una scadenza
vera — il 15 agosto la Liga comincia, e ciò che non si raccoglie prima del
fischio non torna più (`newseason.md` §2) — capire *perché* un guasto di rete
è riuscito a costare l'intero giro.

**Ragionamento / ipotesi.** Il log dice tutto in una riga:

```
urllib.error.HTTPError: HTTP Error 503: Service Unavailable
  File "scripts/fetch_smarkets_matches.py", line 290, in quote_partita
    libri = _libri_per_contratto(_get(f"/markets/{lotto}/quotes/") or {})
```

e appena sopra: `[21/58] Espanyol vs Levante UD: 7870 righe totali`. Cioè
**7.870 righe già in memoria** — 21 partite, cinque leghe, il listino intero —
buttate via da un errore sulla 22ª. Non è un difetto solo: sono tre, in fila, e
ognuno da solo sarebbe bastato a salvare i dati.

1. **`_get` riprovava sul 429 ma non sui 5xx.** La funzione (Fase 97,
   `fetch_smarkets_outrights.py`) ha un ciclo di 5 tentativi che tratta il 429
   come «aspetta e riprova» e **rilancia tutto il resto**. Un 503 è per
   definizione temporaneo — *Service Unavailable*, «riprova fra poco» — ed era
   classificato con i 404. Nessuno l'aveva deciso: il 429 era il caso che si
   era presentato alla Fase 97, e la riga era stata scritta per quello.
2. **L'eccezione di UNA partita usciva dal ciclo del `main`.** `righe +=
   quote_partita(...)` senza `try`: la 22ª partita non aveva il diritto di
   uccidere le altre 57, ma l'aveva.
3. **Il più beffardo.** Lo script scrive il file **prima** di uscire rosso,
   apposta — il commento della Fase 116 dice *«Solo ORA si esce rosso: il file
   è salvo, l'allarme è visibile»*. Ma in GitHub Actions un passo fallito
   **salta quelli dopo**: il passo `Salva lo snapshot` non girava mai, e il
   file moriva sul runner. L'allarme costava esattamente i dati che doveva
   proteggere. Questo difetto non è del guasto dell'08/08: c'era da sempre,
   e valeva anche per l'uscita rossa della lega sparita (01/08) — che quindi,
   quel giorno, ha buttato la raccolta delle altre quattro leghe.

**Alternative considerate.**
- *Solo ritentare sui 5xx.* Il rimedio più piccolo, e insufficiente: sposta la
  soglia di rottura senza toglierla. Un guasto che dura più di 45 secondi
  ricrea la stessa perdita totale.
- *Far fallire il giro a ogni mercato mancante.* Onesto ma inutilizzabile: un
  503 isolato su 58 partite manderebbe una mail rossa, e le mail rosse che non
  chiedono niente si smettono di leggere. La soglia adottata distingue «serve
  un umano» da «è andata storta una richiesta»: **rosso solo per una partita
  persa intera** (un buco nella traiettoria che nessun giro successivo riempie:
  quel prezzo, a quell'ora, non esiste più), giallo-dichiarato per qualche
  mercato.
- *Scrivere un file parziale a ogni partita.* Rende la raccolta a prova di
  crash brutale, ma moltiplica i file d'archivio e complica la rilettura. Il
  budget di tempo (sotto) copre lo stesso rischio a costo zero.

**Scelta.** Quattro modifiche, una per difetto più il contrappeso:

1. `HTTP_TRANSITORI = {429, 500, 502, 503, 504}` in `_get`: si riprova con
   backoff 3-6-12-24s. I **4xx restano fatali** — un 404 non diventa un 200
   riprovando, e insistere nasconderebbe un bug nostro dietro venti secondi.
2. `quote_partita` ritorna `(righe, mercati_persi)` e tollera un lotto caduto:
   costa 20 mercati, non la partita.
3. `main` avvolge ogni partita in un `try`, accumula `partite_incomplete` e le
   **scrive nel file** — un buco dichiarato è innocuo, uno silenzioso è il
   «finto pieno» di R6. Zero righe totali su una finestra non vuota resta un
   fallimento senza file: un archivio non deve mai contenere un silenzio che
   sembra un dato.
4. `if: ${{ !cancelled() }}` sul passo di commit del workflow, così «i dati
   sono comunque salvati» diventa vero.

**📐 Il modello in dettaglio.** Nessuna matematica nuova — è codice di
raccolta — ma due numeri vanno motivati, perché sono scelte e non default.

*Il backoff, e perché il primo fix ne richiede un secondo.* Il tempo peggiore
speso su una singola chiamata che fallisce sempre è la somma delle attese fra
i 5 tentativi:

```
attesa_max = Σ(k=0..3) 3·2^k = 3 + 6 + 12 + 24 = 45 s
```

Su un guasto **isolato** sono 45 secondi ben spesi. Ma se Smarkets è giù per
mezz'ora, *ogni* chiamata costa 45 s, e il giro di lungo raggio a listino
intero fa

```
chiamate = 58 partite × (1 + 13 lotti × 2) = 1.566
1.566 × 45 s ≈ 19,6 ore
```

cioè un runner appeso che non scrive niente e blocca, dietro la stessa
`concurrency`, tutte le corse orarie di chiusura. **Il rimedio non è togliere i
tentativi: è dire quando smettere.** Da qui `BUDGET_MINUTI = 45`, controllato
fra una partita e l'altra; allo scadere si scrive ciò che si ha e le partite
non raccolte sono dichiarate una per una.

*Perché 45 minuti e non un numero a caso.* Il giro più lungo che facciamo
(lungo raggio, tutti i mercati) è misurato **dal log del guasto stesso**: 21
partite in 7'30" scandaglio del listino compreso, cioè

```
per_partita = (7 min 30 s − ~1 min di scandaglio) / 21 ≈ 18,6 s
giro_intero = 58 × 18,6 s ≈ 18 min
```

Il budget è **due volte e mezzo** il giro sano: non taglia mai una raccolta che
sta andando bene, lascia spazio a un calendario più affollato e a qualche
ritentativo, e tiene il giro dentro l'ora prima che la corsa oraria si accodi.
A protezione del caso in cui il processo si *pianti* invece di rallentare — il
budget si controlla fra una partita e l'altra, quindi non scatterebbe — il job
ha `timeout-minutes: 55` contro le 6 ore di default di GitHub.

**Risultato.**

| difetto | prima | dopo |
|---|---|---|
| 503 su una chiamata | eccezione immediata | 5 tentativi, 45 s di backoff |
| guasto su 1 partita di 58 | **57 partite perse** | 1 dichiarata, 57 salvate |
| uscita rossa dopo la scrittura | passo di commit **saltato**, file perso | committato, poi rosso |
| API giù a lungo | fino a ~19,6 h di runner | ≤ 45 min, con ciò che ha raccolto |

**16 test nuovi** in `tests/test_smarkets_matches.py` (46 nel file, suite
verde): i tentativi per ognuno dei 5 codici transitori, il non-tentativo sui
5 codici di richiesta, la resa dopo l'ultimo tentativo, i mercati persi
dichiarati, «una partita persa non porta via le altre» (il bug in una riga), il
budget che salva il raccolto, e un test che **legge il YAML del workflow** e
pretende l'`if:` sul passo di commit.

**Lezione.** Tre cose, e la terza è quella che vale oltre questo file.

1. **Un elenco di casi transitori scritto per il caso che si è presentato è un
   elenco incompleto per definizione.** Il 429 era arrivato alla Fase 97, il
   503 no: la riga trattava «non-429» come «errore vero» perché nessuno aveva
   guardato l'altra metà della tabella HTTP.
2. **Un ciclo che accumula in memoria è un ciclo che può perdere tutto.** Il
   costo di un `try` per iterazione è tre righe; il costo di non averlo è
   proporzionale a quanto sei arrivato lontano — cioè massimo proprio quando fa
   più male.
3. **Un allarme che gira DOPO la scrittura ma PRIMA del salvataggio non è un
   allarme: è una perdita di dati con un messaggio sopra.** Il commento diceva
   «il file è salvo» e il codice Python faceva la sua parte; era il YAML a non
   saperlo. La verifica di un'invariante non può fermarsi al confine del
   linguaggio in cui è scritta — per questo il guardiano nuovo legge il
   workflow, non il codice.

---

## Fase 142 — Prendevamo il 6,7% del listino: coppe, UEFA e cadetterie entrano nel perimetro

**Obiettivo.** Domanda dell'utente subito dopo la Fase 141: *«questo lavoro su
quali partite lo facciamo? verifichiamo se possiamo allargarlo anche alle
partite di coppa per esempio o ad altre di campionato»*. Misurare che cosa
Smarkets espone davvero, quanto costerebbe prenderlo, e allargare il perimetro
di raccolta.

**Ragionamento / ipotesi.** La domanda non si risponde a stima: si conta. Il
censimento del listino dell'08/08/2026 dà **865 partite su 124 competizioni**,
e noi ne prendevamo **58 — il 6,7%**. Fra le 807 che buttavamo:

| | esposte l'08/08 | prima partita |
|---|---|---|
| Coppa Italia | 4 | **quel giorno, 18:00** |
| England League Cup | 31 | **quel giorno, 12:00** |
| Supercoppe (UEFA, Germania, Francia) | 3 | 12 ago |
| UCL / UEL qualificazioni | 14 | 11 ago |
| Seconde divisioni dei 5 paesi | 47 | 14 ago |
| Terze/quarte divisioni | 35 | |
| Amichevoli di club | 57 | |
| Resto del mondo | 616 | |

Il primo fatto è già una risposta: **la Coppa Italia giocava quel giorno e non
la stavamo prendendo.**

**Alternative considerate.** Il perimetro è una scelta dell'utente (§5-ter dice
che escludere un dato si decide con lui), quindi le opzioni sono state
misurate e presentate, non decise. Scartate: *tutto il calcio esposto* (a
listino pieno sono ~112 minuti, non ci sta nel budget di 45 e richiederebbe di
ripensare i cron) e *terze divisioni + amichevoli* (le amichevoli hanno
formazioni finte: valore predittivo basso). **Scelto**: coppe dei 5 paesi +
UEFA per club + seconde divisioni, **a listino pieno** come i campionati.

**Perché queste tre famiglie.** Non è «più dati è meglio»: ognuna tocca un
buco che il progetto ha già.
1. **Coppe** — il progetto ha i dati di coppa 2025-26 (Fase 138, 662 partite,
   6 tornei) e **non ha mai avuto una quota** per quelle partite. Questa è la
   loro controparte prospettica.
2. **Seconde divisioni** — è il buco del **prior neopromosse δ** (Fase 7/8):
   oggi è una costante per lega (0.19-0.33) *proprio perché* non abbiamo dati
   sulla cadetteria. Con le quote di Serie B/Championship/Liga 2 la forza di
   ogni squadra che sale diventa stimabile una per una.
3. **UEFA** — il progetto non ha mai avuto una **scala di forza comune fra
   campionati**. Le quote di UCL/UEL sono l'unico modo di misurarla: il
   mercato la prezza per noi.

**📐 Il modello in dettaglio.** Nessuna matematica di modello: è raccolta. Ma
tre numeri e una regola vanno motivati.

*Il costo, misurato per regime (08/08/2026, campione di 5 partite):*

```
solo principali (3 mercati)     5,6 righe   1,75 s   0,28 KB gz   per partita
listino base    (6 mercati)    24,0 righe   1,68 s   0,60 KB gz   per partita
tutti i mercati (~110)        239,2 righe   7,03 s   7,84 KB gz   per partita
```

⚠️ **`--solo-principali` è una falsa economia sul tempo.** 3 e 6 mercati costano
identico (1,75 contro 1,68 s) perché stanno **comunque in un solo lotto da 20**:
il costo è il numero di *lotti*, non di mercati. Risparmia byte, non minuti.
Il ragionamento della Fase 118 — «il lungo raggio si ferma ai principali per
renderlo sostenibile» — era giusto sull'archivio e sbagliato sul tempo.

*Il perimetro nuovo, misurato dal vivo:*

```
158 partite = 58 campionati + 52 coppe + 48 seconde
tempo ≈ 58×20,6 + 52×7 + 48×5 ≈ 1.760 s ≈ 29 min   (era 19'57")
peso  ≈ 593 KB + ~710 KB ≈ 1,3 MB per giro
```

Sta nel budget di 45 minuti della Fase 141 con ~16 minuti di margine. Le coppe
costano **meno** dei campionati (Coppa Italia: 47 mercati e 4,7 s, contro 110
mercati e ~20 s di una Serie A): il listino di una partita minore è più corto.

*La regola dell'ordinamento, che è una conseguenza aritmetica del budget.*
Il ciclo seguiva l'ordine dell'API, cioè un ordine arbitrario. Con 58 partite
il budget non si toccava mai e non importava; con 158 diventa plausibile, e
allora **quali** partite finiscono nella coda tagliata smette di essere
indifferente:

```
valore di una partita persa ≈ (quante altre occasioni avremo di riprenderla)⁻¹
  partita fra 3 settimane → ~21 giri giornalieri rimasti → perdita ≈ 1/21
  partita fra 1 ora       → 0 giri rimasti               → perdita = tutto
```

Quindi si raccoglie in **ordine di calcio d'inizio**: la coda tagliata è
sempre ciò che manca di meno.

**Il rischio vero, e cosa lo copre.** Non è raccogliere di più: è che **a valle
qualcosa scambi una coppa per un campionato senza dare errore**. Quattro punti,
tutti trovati leggendo i consumatori invece che immaginandoli:

| dove | cosa sarebbe successo |
|---|---|
| ogni riga | `groupby('lega')` avrebbe messo Vicenza-Catania fra le partite di Serie A → aggiunto **`fascia`** (campionato/coppa/seconda) su ogni riga |
| `anomalia_del_listino` | contando anche le coppe, la sparizione di tutti e 5 i campionati non avrebbe suonato → conta i soli campionati |
| `ultimo_listino_completo` | cercava `len({lega}) >= 5`: **due leghe e quattro coppe** superano la soglia → un file parziale travestito da completo |
| prospettico / mappa nomi / anagrafica | avrebbero cercato negli snapshot squadre di Serie B e di UCL che lì non esistono → filtrano su `fascia == campionato` |

L'assenza del campo vale `campionato`, così i file già in archivio restano
leggibili.

**Il problema degli slug che non conosciamo ancora, e perché qui si indovina.**
Copa del Rey, DFB-Pokal, Coupe de France, FA Cup e i gironi UEFA cominciano più
avanti, e l'API espone **solo** ciò che è `upcoming`: non c'è modo di leggere
oggi il nome che avranno (provati `/competitions/` e `/sports/`: **404**;
`state=new`: **zero eventi**). Le due strade pulite erano entrambe peggiori —
aspettare che compaiano perde i primi giorni di traiettoria, che non tornano;
includere per prefisso di paese tira dentro National League North e le
femminili. Quindi:

- **`SLUG_ATTESI`** — gli slug che ci aspettiamo, con più varianti dove la
  convenzione non è ovvia (osservato dal vivo: `italy-coppa-italia` usa il nome
  nativo, `england-league-cup` e `france-super-cup` no). Indovinare è **sicuro**
  perché uno slug sbagliato semplicemente non combacia mai;
- **il RADAR** — `fuori_perimetro()` elenca ogni competizione dei nostri paesi
  o UEFA che il listino espone e noi *non* prendiamo, nel log **e nel file**
  (`fuori_perimetro`). È lì che comparirà `germany-dfb-pokal` col nome vero se
  l'abbiamo scritto sbagliato.

L'accoppiata rende l'errore **rumoroso invece che silenzioso**, ed è il rimedio
diretto allo stesso guasto di `spain-laliga` → `spain-la-liga` (31/07, trovato a
mano cinque giorni dopo).

**Risultato.** Perimetro da 58 a **158 partite** (+172%), giro da 20 a ~29
minuti, archivio da 593 KB a ~1,3 MB per giro. Verificato dal vivo su un file
misto: 1.321 righe su tre partite, una per fascia, `fuori_perimetro: {}` e
`partite_incomplete: []`. **6 test riscritti** (codificavano il perimetro
stretto: erano la decisione di allora, non una verità) **e 10 nuovi**, 69 nel
file; suite intera a **1.458 verdi**. Push alle 11:58 UTC, in tempo perché il giro di chiusura delle 12:07
prendesse le partite di League Cup delle 14:00.

**Lezione.** Due, e la seconda vale oltre questo file.

1. **Un perimetro scritto una volta non si rilegge più.** `SLUG_LEGA` conteneva
   5 voci dalla Fase 116 e nessuno aveva più chiesto *quanto* stessimo
   lasciando fuori. La risposta era 93,3%, e comprendeva una partita che si
   giocava quel pomeriggio. Il censimento costa una chiamata API.
2. **Il cron orario di GitHub parte con 30-40 minuti di ritardo** (misurato
   quel giorno: i giri delle `:07` sono partiti alle 08:54, 09:49, 10:45,
   11:37). Non è un guasto ed è documentato, ma cambia il conto di una cosa
   che qui pesa: la finestra `--entro-ore 2` del regime di chiusura diventa di
   fatto **T-1h20/T-0h20**, e una partita che comincia entro ~40 minuti dal
   cron può non essere presa affatto. Con le sole 5 leghe non si vedeva —
   giocano a orari tondi e sono poche; con 31 partite di League Cup alle 14:00
   diventa un rischio reale. Da qui l'input `tutti_i_mercati`, per poter
   forzare a mano il regime di chiusura quando serve.
3. **Allungare i giri ha fatto cancellare la corsa di chiusura** — una
   regressione introdotta da questa stessa fase, trovata guardando i run
   mentre giravano e non rileggendo il YAML. GitHub tiene, per ogni
   `concurrency group`, **un run in corso e uno solo pending**: all'arrivo di
   un terzo, *«any previously pending job or workflow in the concurrency group
   will be canceled»*. Con i giri da 20 minuti non capitava mai; con 158
   partite un lungo raggio occupa il gruppo 35-45 minuti, e due corse orarie
   accodate bastano perché la prima muoia (misurato: run 31258806209 delle
   13:07, `cancelled`). A morire è **il giro che vale di più** — la chiusura è
   il prezzo a T-2h — e muore **in silenzio**: un run cancellato non scrive
   niente e non suona niente. Rimedio: un gruppo **per regime**, che è sicuro
   perché i due scrivono file con nomi diversi e il push ha già i suoi tre
   tentativi con `pull --rebase`. La lezione generale: **una modifica che
   cambia la *durata* di un job può cambiarne la *pianificazione*, e la
   pianificazione non ha test.**
4. **Un input dichiarato e mai letto è peggio di un input assente**, e l'ho
   commesso e committato nello stesso pomeriggio: la casella compariva nella
   UI di GitHub e spuntarla non faceva niente. È lo stesso genere di buco del
   punto 3 della Fase 141 — un'invariante che vive **fra il YAML e se stesso**,
   che nessun test del codice Python può vedere. Il guardiano nuovo
   (`test_ogni_input_del_workflow_e_davvero_usato`) pretende che ogni input
   compaia sotto `jobs:`; verificato per mutazione, col YAML rotto fallisce
   con `assert not ['tutti_i_mercati']`.
5. **Allargare un dato è per metà un lavoro sui suoi consumatori.** La parte
   difficile non è stata prendere le coppe: è stata trovare i quattro punti a
   valle che le avrebbero scambiate per campionati **senza dare errore** —
   incluso un `len({lega}) >= 5` che quattro coppe fanno passare. Un dato nuovo
   in una colonna vecchia è un finto pieno in attesa (R6): il perimetro si
   allarga leggendo chi legge, non chi scrive.
