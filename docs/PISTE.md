# Piste aperte — dati disponibili, ipotesi di miglioramento e perché

Questo file è per le **revisioni future**: ogni voce è una pista
*dato/architettura → ipotesi di modello*, con lo stato del dato (già in
snapshot / nei grezzi non estratto / da procurare / da raccogliere nel
tempo) e la fase del diario che la motiva. L'obiettivo: chi apre questo
file deve trovare non "cosa manca" ma **"cosa potrei provare dopo, con che
cosa, e perché potrebbe funzionare"**. La parte operativa (rete, strumenti,
Actions) sta nel [MANUALE_SOPRAVVIVENZA.md](MANUALE_SOPRAVVIVENZA.md).
**Va aggiornato quando una pista si apre, si prova o si chiude** (anche
l'esito negativo si scrive, principio §1.4). Ultimo aggiornamento: Fase 79.

## 1 · Piste che non richiedono nuovi dati (feature engineering / architettura)

Le più economiche: nessuna rete, nessun import — solo codice sugli snapshot
già in repo. Da provare per prime (principio §1.3, "versione economica").

### 1. Scontri diretti (head-to-head) tra le due squadre
**Dato**: già nello snapshot — è una query sullo storico delle partite tra
le stesse due squadre (ultimi 5-10 precedenti), zero dati nuovi.
**Ipotesi**: nessuna fase del diario la menziona (verificato: zero
occorrenze di "scontri diretti"/"head-to-head"/"H2H" in 68 fasi) — un
vuoto sorprendente. È concettualmente diverso dalla "forma" già bocciata
(Fase 13: punti/gara recenti, ridondante col fit pesato nel tempo): cattura
un **match-up specifico** (es. una squadra soffre sistematicamente un certo
avversario/stile), non il momento di forma generale. Non è coperto dalle
bocciature esistenti.
**Rischio onesto**: piccoli campioni per coppia (poche stagioni comuni,
specie cross-serie A/B per neopromosse), possibile overfitting; da testare
con shrinkage forte verso zero, come ogni covariata debole (Fase 13/33).

### 2. Covariate anche nel sotto-modello xG, non solo nei gol
**Dato**: nessuno nuovo — è un cambio di architettura.
**Ipotesi**: l'audit Fase 34 nota di passaggio che "le covariate entrano
SOLO nel sotto-modello dei gol, non in quello del segnale (xG): con
α=0.75 il loro effetto sul tasso *blendato* è diluito" — mai seguita.
Potrebbe far riemergere covariate borderline già in panchina (`rest_full`,
`midweek_europe`, Δ≈−0.0004, PANCHINA.md #9/#12) che erano deboli forse
*per la diluizione*, non perché nulle.

### 3. Denoising cross-partita dei λ,μ impliciti (market-implied)
**Dato**: nessuno nuovo — architettura del motore.
**Ipotesi**: Fase 34: "il market-implied inverte ogni partita in modo
indipendente: nessun denoising cross-partita (es. shrinkage stagionale dei
λ,μ impliciti per squadra), mai tentato". Diverso dal denoising
cross-*stagione* già chiuso (Fase 38, bias sistematici): qui si
aggregano/shrinkano i tassi impliciti della stessa squadra su partite
ravvicinate per ridurre il rumore della singola inversione. Candidato sui
mercati "ricchi" (risultato esatto, multigol) dove la Fase 26 mostra i
guadagni maggiori — senza toccare la φ35 già ottimizzata.

### 4. Motore market-implied multi-mercato su Premier/Liga
**Dato**: già negli snapshot (quote 1X2+O/U Premier/Liga esistono).
**Ipotesi**: PANCHINA.md nota ✱1 lo segnala esplicitamente come **primo
candidato del fronte per-lega**: "la struttura è la stessa, le costanti
(ρ, θ, φ) vanno riviste per lega" — mai backtestato multi-mercato fuori
Serie A (solo il tracer 1X2 della Fase 53). È il motore **più forte** del
progetto (batte 13/14 mercati in Serie A, Fase 26): portarlo altrove è
lavoro di ri-taratura, non di raccolta dati.
**CHIUSA, positiva (Fase 76).** Sul 2017-19 dall'apertura (Fase 75) 17/20
mercati; e ora sul **2019-26 dalla CHIUSURA** (Fase 76) il motore batte il
DC-da-gol su **13/14 mercati su tutte e 3 le leghe** (Serie A/Premier/Liga),
identico alla Serie A della Fase 26, **senza ritarare ρ**. La struttura è
universale (solo gli input sono per-lega). Unica eccezione trans-lega: il
pari/dispari (quasi-casuale). Il θ del router NON si trasferisce (per-contesto,
lega × epoca). Resta da testare per-lega solo la **φ35** sulla famiglia-pareggio
(PANCHINA ✱2).

## 2 · Piste nei dati grezzi già scaricati, mai estratte

Nessuna rete: le colonne sono nei CSV football-data congelati in
`data/football_data_raw/`, serve solo estenderne l'estrazione in
`loader.py`.

### 5. Handicap asiatico → terzo vincolo per l'inversione market-implied
**Dato**: colonne AH (linea + prezzi, apertura E chiusura), **7/9
stagioni** (2019-20+).
**Ipotesi**: la Fase 27 chiuse la taratura della forma dicendo
esplicitamente che "per spingere oltre servirebbero PIÙ input di mercato
(altre linee O/U, handicap)"; ripreso in Fase 44. L'handicap è un vincolo
su **λ−μ** (asimmetria) che 1X2+O/U (livello+somma) non fissa bene: terzo
vincolo → inversione più precisa → migliora il motore attivo su tutto il
listino. Tier 2 dichiarato (principio §1.8). **L'unica pista di questa
sezione che può migliorare direttamente il titolare**: priorità massima
tra le "grezzo non estratto".

### 6. Primo tempo (HTHG/HTAG/HTR) → mercati Tier 3 e fondazione live
**Dato**: **9/9 stagioni**, mai estratto.
**Ipotesi**: mercati HT/FT e per-tempo (Tier 3, principio §1.8) con lo
stesso motore market-implied riscalato sul tempo; propedeutico alla pista
18 (in-play).

### 7. Statistiche partita (corner, tiri totali, falli, cartellini)
**Dato**: 9/9 stagioni, mai estratte (solo i tiri in porta furono testati
e bocciati, Fase 2/3 — quelli sono un segnale diverso e già chiuso).
**Ipotesi**: i corner come proxy di pressione offensiva mai testato; i
mercati corner/cartellini sono un listino a sé che il motore non copre.
Aspettativa onesta: bassa sul migliorare 1X2/O/U (tetto informativo, Fasi
20-22), più sensata come **nuovi mercati** da prezzare.

### 8. Quota massima (MaxC*/Max*) → ROI realistico
**Dato**: 7/9 stagioni.
**Ipotesi**: ogni ROI finora usa la quota media → sottostima quanto un
utente reale otterrebbe col best-price. Rifare le simulazioni chiave
(Fasi 14/40/51) al best-price è un test economico che può cambiare le
conclusioni operative (in meglio: il margine effettivo si riduce).

### 9. Pinnacle puro (PS*/PSC*) come benchmark singolo-book
**Dato**: 8/9 stagioni piene (2025-26 ~52%).
**Ipotesi**: il book più efficiente come bersaglio invece della media
multi-book — avversario più duro e pulito (niente rumore da book
ricreativi). Utile per ri-testare il beat-the-close (Fase 52) contro un
avversario più serio. (Betfair Exchange BFE*: solo 2/9 stagioni, futuro.)

## 3 · Piste che richiedono una fonte esterna nuova

### 10. Formazioni ufficiali (`game_lineups.csv`) → assenze VERE
**Dato**: l'upstream player-scores che già importiamo contiene anche
`game_lineups.csv` (~349 MB), `game_events.csv` — mai importati (il
workflow scarica solo i 4 file dei valori). A portata di una riga in più
in `WANTED`.
**Ipotesi**: sono la voce "dati davvero nuovi" della roadmap (README #27).
Le assenze della Fase 4 erano stimate da fonte terza e non aiutavano; con
le formazioni vere si calcola la **forza della formazione schierata**
(valore/minuti dei titolari effettivi vs rosa piena). Attenzione al
timing: le formazioni escono ~1h prima del fischio → utilizzabili solo
contro le quote di **chiusura**.

### 11. `transfers.csv` → shock di gennaio
**Dato**: nello stesso upstream player-scores (pista 10).
**Ipotesi**: il mercato invernale cambia le rose infra-stagione; il nostro
`squad_value` è una foto al 1° settembre. Mai modellato. Da incrociare con
la Fase 31 (motivazione): gennaio ridistribuisce anche gli obiettivi.

### 12. Risultati di seconda serie → prior neopromosse individualizzato
**Dato**: la Fase 68 ha già scaricato le seconde serie (Serie B,
Championship, Segunda, 1617→2425 via openfootball) ma **solo per il
calendario/riposo**, non per i punteggi — che sono nello stesso file.
**Ipotesi**: oggi il prior δ (Fase 7) è un numero fisso uguale per ogni
neopromossa; la Fase 7 stessa nota il limite: "il 2023-24 peggiora perché
quel trio di promosse (Genoa/Cagliari/Frosinone) era più vicino alla
media — il prior le sotto-stima". Stimare una forza di partenza per
neopromossa dal suo rendimento reale (punti/gara, differenza reti)
nell'ultima stagione di B/Championship/Segunda userebbe un dato già in
casa, nello stesso formato dei file coppa già parsati.

### 13. Meteo pre-partita
**Dato**: da procurare (mai cercata una fonte).
**Ipotesi**: nel chiudere il capitolo "dati interni esauriti" la Fase 4c
lascia il layer covariate "riutilizzabile per dati futuri davvero
indipendenti (es. formazioni ufficiali last-minute, **meteo**,
motivazione)" — formazioni e motivazione sono state poi effettivamente
attaccate (piste 10, Fase 31); il meteo no, mai. È l'unico segnale
esplicitamente indicato come "davvero indipendente" (non ricavabile da
gol/xG storici) mai perseguito.

### 14. Bundle Understat Premier/Liga → port completo del DC
**Dato**: bundle utente in `files/` (Fase 53), xG cross-lega.
**Ipotesi**: la Fase 53-bis è dichiarata aperta nel CLAUDE.md — completare
il port del DC con blend xG su Premier/Liga e ri-validare il two-front
(principio §1.9).
**CHIUSA, positiva (Fasi 54-57)**: snapshot congelati con xG al 100%,
config per-lega in `LEAGUE_CONFIGS` (δ 0.33/0.22), DC+xG batte la baseline
su entrambe; la ri-taratura degli altri iperparametri è piatta. Lo studio
dedicato delle due leghe continua in `docs/STUDIO_PREMIER_LIGA.md`.

### 15. Altre linee O/U (multi-linea) per vincolare meglio λ,μ
**Dato**: da procurare — **verificato che football-data.co.uk NON le
fornisce** (solo 2.5), a differenza dell'handicap (pista 5, quello sì
presente). Serve una fonte esterna nuova (es. storico Pinnacle/Betfair
multi-linea), mai identificata nel diario.
**Ipotesi**: Fase 27 e Fase 44 dichiarano il bisogno due volte ("più
input di mercato — altre linee O/U, handicap — che lo snapshot non ha")
per vincolare meglio l'inversione. Meno "pronta" delle altre: nessuna
fonte candidata nota, va cercata da zero.

## 4 · Piste di raccolta prospettica (richiedono mesi, non giorni)

### 16. GG/NG quotato + aperture vere
**Dato**: NON esiste in nessun archivio (verificato); solo raccolta da
oggi in avanti (foto periodiche delle quote).
**Ipotesi**: il GG/NG è l'unico mercato senza tetto di efficienza
dimostrato (principio §1.8) e le "aperture vere" (prima quota pubblicata,
non il venerdì di football-data) sono l'unico test rimasto della Fase 14.
Canale già pronto (cron Actions).

### 17. Paper-trading della strategia draw-bias
**Dato**: nessuno nuovo — modello e storia già esistono; manca il
campione **fuori-sample futuro**.
**Ipotesi**: Fase 40, testuale: "merita raccolta prospettica (tracciare
stake reali su questa sola strategia, con soglia pre-registrata, per 1-2
stagioni) prima di qualsiasi conclusione. È l'unico posto dove il mercato
mostra una crepa e noi abbiamo lo strumento per vederla." È l'unica
strategia a ROI positivo mai trovata (+4.7% Serie A P83%, +3.6% Liga P81%)
ma non conclusiva per varianza campionaria — diversa dalla pista 16 perché
qui serve solo tempo, non un nuovo tipo di dato.

### 18. Dati in-play (quote minuto per minuto)
**Dato**: da raccogliere — progetto di raccolta dati, non backtest.
**Ipotesi**: Fase 0 (design): "per il live basterà condizionare la stessa
distribuzione al minuto e al punteggio" — mai realizzata. Fase 44: "l'
in-play è l'avversario più morbido — ma nessuno dei due è nei dati". Il
modello è già scritto per generalizzarci (matrice condizionabile); manca
solo il dato. Indicato come l'avversario meno efficiente più credibile,
mai nemmeno abbozzato.

### 19. Quote O/U 2017-19 — CHIUSURA vera (non solo stima)
**Dato**: da procurare — piano dedicato: [CACCIA_OU_2017_19.md](CACCIA_OU_2017_19.md).
**Stato (Fase 73)**: il buco si è **dimezzato**. L'**apertura** O/U 2017-19 NON
mancava: l'unica linea (`BbAv`) è un'apertura reale, prima mal etichettata come
chiusura, ora nella colonna giusta (`odds_over25_open`, dato reale). Resta da
procurare solo la **chiusura** O/U (2.280 celle). Fase A (dataset già pronti su
Kaggle/GitHub/HF) e Fase B (scraping BetExplorer) **chiuse negative** —
confermato per ispezione diretta. La stima di chiusura (E3 pooled, Fase 62-bis)
è stata spremuta al massimo con 4 leve (Fase 72) + la dispersione max-vs-media
sbloccata dalla correzione (Fase 73): **8 leve ortogonali respinte**, E3 resta
il tetto pratico. **Non è un buco chiuso per sempre**: solo le vie economiche
note oggi sono esaurite.
**Da riprovare in futuro** (promemoria esplicito, richiesta utente):
ri-tentare la Fase A periodicamente (nuovi dataset compaiono nel tempo su
Kaggle/GitHub/HF — non ripartire dai 6 già controllati, cercarne con fonte
diversa da football-data.co.uk); valutare la Fase D (OddsPortal headless con
login) se emerge un modo a basso rischio di gestire le credenziali; valutare
fonti a pagamento se il progetto passa a un uso più operativo. Dettagli
completi (numeri, candidati testati, criteri di accettazione) in
`CACCIA_OU_2017_19.md` e nel diario (Fasi 71-72).

## 5 · Fatti misurati che condizionano il modeling futuro

- **Cambio di livello della fonte squad_value (+3-5%)**: sulle 456 celle
  in comune, rapporto nuovo/vecchio mediano SA 1.043, PL 1.027, Liga
  1.055 (rose leggermente più ampie via appearances + vintage più
  recente). Se si ri-testa `squad_value` come covariata, il livello non è
  confrontabile col passato: usare solo la nuova fonte, mai mischiare.
- **Regime d'errore dello stimatore F66** (esempio Lazio, stima→reale,
  M€): 1718 200→177, 1819 185→**337**, 1920 390→285, 2021 330→368, 2122
  305→325, 2223 275→271, 2324 271→275, 2425 418→**239**, 2526 284→270.
  Mediana ~15% ma code ±45-75%: il regime dichiarato (~29% mediano, p90
  75%) è reale — le stime valgono per analisi aggregate, MAI per feature
  per-partita.
- **Le 13 celle squad_value 2025-26 — CHIUSE (Fase 70)**: coperture player-
  scores insufficienti al 18/7/2026 (Bologna 79%, Como 82%, Cremonese 70%,
  Parma 64%, **Pisa 33%**, Udinese 80% · Leeds 72%, Sunderland 80% · Celta
  78%, Elche 56%, Espanol 59%, Levante 45%, **Oviedo 34%**; soglia 85%), ma
  recuperate con dato REALE preso direttamente da Transfermarkt (pagine di
  competizione per stagione, non il profilo-club che mostra il valore live)
  prima che il backfill a monte le chiudesse da sole. Scarto vs la stima
  Fase 66 mediano 22.5% (range −43%…+77%, coerente col regime d'errore
  dichiarato: conferma che la stima era onesta, non che fosse precisa
  cella-per-cella).
- **Alaves-Sociedad 14/10/2017 — chiusura 1X2 mancante (aggiornato Fase 73).**
  Nel grezzo PSH/PSD/PSA (Pinnacle pre-match) = 3.52/3.55/2.20 sono presenti,
  ma PSCH/PSCD/PSCA (Pinnacle chiusura) sono vuote — l'unico caso su 2.280
  partite (2017-19, 3 leghe). **Prima della Fase 73**: la chiusura ripiegava sul
  fallback `BbAvH` (media, ~5.3% margine vs Pinnacle ~2.0% — book diversi, non
  un movimento) e l'apertura era oscurata → la riga sembrava "senza apertura".
  **Dalla Fase 73** (chiusura = solo colonne `*C*` genuine, niente fallback):
  la chiusura 1X2 è onestamente **NaN** e l'apertura reale `PSH` è valorizzata.
  Quindi non è più "senza apertura" (la stima Fase 69 è stata ritirata); le
  manca la **chiusura** 1X2 (1 riga, non stimata: movimento 1X2 quasi tutto
  rumore, Fase 69). Torino-Fiorentina 10/01/2022 (recupero COVID) resta senza
  NESSUNA colonna pre-match → apertura 1X2+O/U stimata (Fase 69).
  Tentativo di ricerca esterna (sessione utente, luglio 2026): BetExplorer
  e OddsPortal da IP italiano reindirizzano a edizioni ADM-compliant
  (`/it/`, `centroquote.it`) che non pubblicano Pinnacle e nascondono lo
  storico apertura/chiusura dietro login — nessun dato recuperato.

## 6 · Come procurarsi i dati

Canale unico per tutto ciò che il proxy blocca: **workflow GitHub
Actions** che scarica e committa (pattern Fase 67, dettagli operativi nel
[MANUALE_SOPRAVVIVENZA.md](MANUALE_SOPRAVVIVENZA.md)). Per le piste 5-9 i
dati sono **già nei CSV grezzi in repo**: serve solo estenderne
l'estrazione in `loader.py` (nessuna rete). Per le piste 10-11: una riga
in più nel `WANTED` del workflow. Per la 13/15: fonte esterna da
identificare. Per le piste 16-18: un nuovo workflow cron di raccolta.

---

*Regola d'oro ereditata dalle Fasi 20-33: il tetto è INFORMATIVO, non
architetturale. Ogni pista qui sopra porta INFORMAZIONE nuova (o
un'architettura non ancora provata su informazione già in casa), mai solo
un rifacimento di ciò che l'audit ha già chiuso.*
