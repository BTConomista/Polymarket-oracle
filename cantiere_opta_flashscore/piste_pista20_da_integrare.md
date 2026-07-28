### 20. flashscore.com / diretta.it (formazioni + corner/cartellini a 5 leghe) — ❌ **CHIUSA (28/07/2026)**
**Dato**: mai estratto, nessuna riga in repo.
**Ipotesi**: diretta.it (versione italiana di Flashscore, stessa piattaforma
Livesport s.r.o.) mostra per (quasi) ogni lega/stagione le **formazioni
ufficiali pre-partita** (pista 10) e le **statistiche di partita**
corner/cartellini per Bundesliga e Ligue 1 (il buco a 5 leghe della pista 7),
che oggi mancano perché `data/football_data_raw/` copre solo la Serie A.
Sarebbe stata una fonte unica per colmare due piste aperte insieme.
**ESITO — chiusa, per due motivi indipendenti, nessuno dei due aggirabile:**
1. **Il sito non ha un'API pubblica.** I dati che il browser mostra arrivano
   da una chiamata interna non documentata verso l'infrastruttura Flashscore,
   protetta da un **meccanismo anti-bot attivo** (oltre a un token applicativo,
   richiede che il client presenti il fingerprint TLS di un browser reale).
   Non è un caso di "nessuno l'ha mai documentata": è una contromisura
   *deliberata* contro client non-browser. Il `robots.txt` di per sé non
   vieta le pagine di risultati (a differenza di understat/oddsportal), ma
   accedere all'endpoint richiederebbe di impersonare un browser a livello di
   handshake TLS — non un semplice user-agent. È la stessa categoria del
   "nessun aggiramento" già scritto in `docs/MANUALE_SOPRAVVIVENZA.md` §4-bis
   (niente user-agent camuffati, niente VPN), solo più profonda: qui sarebbe
   il livello TLS, non l'header. **Non perseguita per scelta di metodo**, a
   prescindere da fattibilità tecnica.
2. **Un browser reale (non necessario per il punto 1, ma verificato per
   completezza) non è comunque un'alternativa pulita in questa sessione**:
   Playwright/Chromium (pre-installato nell'ambiente) non riesce a raggiungere
   la rete pubblica in HTTPS — fallisce con `ERR_CONNECTION_RESET` anche su un
   sito banale come `example.com`, con o senza il proxy dell'agente,
   indipendentemente da diretta.it. È un limite dell'ambiente di questa
   sessione, non del sito.
**Via legittima alternativa, non ancora tentata**: cercare un **dataset già
raccolto e ridistribuito apertamente da terzi** (stesso pattern di
`davidcariboo/player-scores` per Transfermarkt, pista 10/11) — misurato
contro una fonte primaria dove possibile, invece di scrapare noi la fonte
viva. Non riproporre lo scraping diretto senza un cambio di condizioni (es.
un'autorizzazione esplicita del sito, o un accesso browser reale disponibile
in una sessione futura).
