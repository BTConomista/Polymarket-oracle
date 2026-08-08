# Dove deve girare la raccolta — ragionamento aperto

> **Stato: NESSUNA DECISIONE PRESA** (08/08/2026). L'utente ha chiesto di
> ragionarci bene prima di decidere, e questo file è il ragionamento. Va
> aggiornato quando arrivano i numeri che oggi mancano (§5).

## 1. La domanda, posta bene

Non è «GitHub Actions va bene o no?». È:

> **quale parte della raccolta ha requisiti che Actions non soddisfa, e quanto
> ci costa davvero non soddisfarli?**

Posta così, la risposta non è per forza la stessa per tutto. Le tre famiglie
di dati che raccogliamo hanno requisiti molto diversi.

## 2. I requisiti, per famiglia

| famiglia | cadenza | cosa succede se il giro slitta di 40 min | cosa succede se salta del tutto |
|---|---|---|---|
| **lungo raggio** (1×/giorno, tutte le esposte) | giornaliera | **niente**: le stesse partite ci sono anche fra un'ora | si perde un giorno di traiettoria su partite che restano esposte per 15-22 giorni → **recuperabile** |
| **chiusura** (oraria, entro 2h dal via) | oraria | la finestra effettiva diventa T-1h20/T-0h20 | **il prezzo di chiusura di quelle partite non esiste più** |
| **in-play** | 2 min, per ore | buco di 40 min nella serie | l'intera partita senza dati |

**Conclusione parziale, che restringe molto il problema:** per il lungo raggio
Actions è più che adeguato e non c'è alcuna ragione di spostarlo. Il problema
è tutto sulle altre due, e soprattutto sull'in-play.

## 3. I limiti di Actions, misurati (non temuti)

Tutti dell'08/08/2026, su questo repo:

| limite | evidenza |
|---|---|
| il cron slitta di **30-40 min** | i giri delle `:07` partiti alle 08:54, 09:49, 10:45, 11:37 |
| il cron può **non partire** | `smarkets-live.yml` a zero run per mezz'ora con 25 partite in corso |
| i run in coda si **cancellano** | run 31258806209, `cancelled` |
| un job dura al massimo **6 ore** | limite documentato |
| il runner è **3,5× più lento** verso Smarkets | una chiamata costa 0,54 s da questo ambiente, **~1,8 s dal runner** |

E il rovescio, che è consistente:

- **gratis e illimitato** sui repo pubblici (è ciò che rende praticabile un job
  acceso 5 ore);
- **zero manutenzione**, nessuna macchina, nessun segreto oltre a quelli che
  GitHub dà da solo;
- codice e dati nello stesso posto, con la storia in git;
- **le mail dei run falliti arrivano davvero** — è così che è cominciata la
  sessione dell'08/08.

### 3-bis. La lentezza del runner, che non è un dettaglio

Scoperta il 08/08 misurando il primo run in-play vero: **un solo giro pieno su
25 partite ha impiegato 9 minuti e 50 secondi**, contro i ~3 minuti stimati.
Conseguenza diretta: zero giri di nucleo, cadenza dichiarata mai realizzata.

La causa non è l'API, è il collegamento del runner:

```
costo di una chiamata:  0,54 s da questo ambiente  |  ~1,8 s dal runner
di cui throttle nostro: 0,35 s                     |   0,35 s
=> ritmo effettivo:     ~2,9 richieste/s (al tetto)|  ~0,55 richieste/s (1/5 del tetto)
```

Qui siamo **limitati dall'API**, sul runner siamo **limitati dalla latenza**.
Rimedio applicato (Fase 144-ter): chiamate in parallelo con un limitatore di
ritmo condiviso — si sovrappongono le *attese*, non si aumentano le richieste.
Guadagno atteso sul runner ~5×; **da questo ambiente il guadagno è 1,1×, cioè
nullo**, perché qui non c'era niente da recuperare. La verifica va fatta sul
runner, ed è in corso.

⚠️ Questo peggiora il conto del §4: se un giro pieno costa minuti, la
sessione da 5 ore ne contiene molti meno di quanti sembrasse, e il tempo speso
a ri-leggere il listino pieno è tempo sottratto alla cadenza fine.

## 4. Il vincolo che decide: 6 ore contro 10,5

Misurato sul calendario vero del perimetro:

```
giorno        partite   primo   ultimo   arco    copertura live necessaria (arco + 2h)
2026-08-09         6    11:30   19:00    7.5h    ->  9.5h
2026-08-15        15    11:00   19:30    8.5h    -> 10.5h
```

**Una giornata piena chiede fino a 10,5 ore continue. Un job ne dura 6.**
Non è aggirabile allungando la sessione: serve per forza una staffetta, e ogni
passaggio di consegne dipende da un cron che slitta di 30-40 minuti.

Con sessioni da 5 ore e sentinella ogni 30 minuti, il conto atteso è:

```
passaggi per una giornata da 10,5h ≈ 2
buco atteso per passaggio          ≈ ritardo medio del cron ≈ 20 min (0-40)
buco atteso per giornata            ≈ 40 min su 10,5h  ≈  6% della giornata
```

Il 6% non è catastrofico, ma **non è distribuito a caso**: cade sempre a
cinque ore dall'accensione, cioè a un'ora del pomeriggio prevedibile. Se
capita durante il blocco delle 15:00 si perdono venti partite insieme.

### 4-bis. Una via d'uscita dentro Actions, da valutare

Il tetto delle 6 ore si aggira **senza cambiare piattaforma**: due workflow
gemelli (`live-A` e `live-B`) con gruppi di concorrenza distinti e cron
sfalsati di ~4,5 ore, ciascuno con sessione da 5 ore. Le due catene si
**sovrappongono per costruzione**, quindi:

- non c'è nessun passaggio di consegne scoperto: quando A finisce, B sta già
  raccogliendo da mezz'ora;
- il cron torna a essere un accendino, e ce ne sono **due indipendenti**: perché
  si apra un buco devono fallire entrambi.

Costo: raccolta doppia nelle ore di sovrapposizione (file distinti, istanti
distinti — la deduplica a valle è banale) e un secondo workflow da tenere
allineato al primo. **Non è ancora stato provato.**

### 3-ter. Il parallelismo ha reso 1,56×, non 5× — e ha scoperto il limite vero

Misurato sul runner (run 31262917393, 25 partite, listino pieno):

```
prima: 590 s (9'50")   dopo: 378,6 s (6'19")   ->  1,56x, non il 5x previsto
giri di nucleo:  0     ->  1                    (meglio, ma la cadenza di 2' resta lontana)
⚠️ 151 mercati persi per HTTP 429 in un solo giro
```

I 429 sono la spiegazione del guadagno mancato: **fra rifiuti e attese si
mangia gran parte del teorico**. E il fatto che conta è questo:

| ambiente | ritmo nominale | esito |
|---|---|---|
| questo container | 2,9 req/s | **24 su 24 accettate, zero 429** |
| runner GitHub | 2,9 req/s | **151 mercati persi per 429** |

Stesso ritmo, esito opposto. Le ragioni plausibili sono due e non sappiamo
distinguerle — l'IP di un runner è **condiviso fra molti utenti di Actions**, e
il volume sostenuto è diverso (~1.000 chiamate contro 24). Il punto però non è
quale delle due: **un numero fisso non può essere giusto in entrambi i posti.**

Rimedio (Fase 144-quater): l'intervallo **si tara da solo** — cresce di 1,6×
a ogni 429, decade dello 0,99 a ogni successo, fra un minimo e un massimo
dichiarati. Asimmetrico apposta: un 429 è un fatto, un successo è solo
l'assenza di un rifiuto. Il ritmo raggiunto finisce **scritto nel file**, così
una sessione con pochi giri non resta un mistero.

⚠️ Nota su come è nato l'equivoco: il valore 0,35 s viene dalla Fase 97 ma
**non era mai stato provato al suo ritmo nominale**. In sequenza la latenza
aggiungeva spaziatura da sola (0,55 req/s effettive sul runner contro le 2,9
nominali): il limite vero dell'API non l'avevamo mai toccato. L'abbiamo
toccato solo parallelizzando.

**Conseguenza per la decisione infrastrutturale:** il runner non è solo più
lento, è anche **più rifiutato**. Sono due svantaggi distinti e si sommano.

## 4-ter. La proposta dell'utente: gemelli + staging + compattazione

Proposta (08/08): *«due o anche più workflow gemelli, salvare tutto in una
cartella provvisoria da svuotare periodicamente per eliminare i doppioni e
aggiungere al database solo i dati puliti»*.

**È l'architettura giusta**, e per una ragione strutturale: disaccoppia
l'*affidabilità della raccolta* dalla *pulizia dei dati*. Se i doppioni non
fanno danno, la ridondanza diventa gratis, e ogni gemello in più è un
miglioramento che non può peggiorare niente — mentre con workflow che si
coordinano fra loro ogni gemello in più è un rischio in più. E mette la parte
fragile dove un errore non costa: se la compattazione fallisce il grezzo c'è
ancora; se fallisce un gemello, gli altri hanno il dato.

Due correzioni, entrambe misurate.

### (a) Lo staging NON può stare in git

`git` non dimentica: committare e poi cancellare lascia la storia. Misurato
sui file veri dell'08/08 (un giro pieno su 25 partite = **1,1 MB compressi**):

```
una giornata piena, 1 gemello: 40 giri pieni + 120 di nucleo ≈  19 MB
                   3 gemelli:                                ≈  57 MB
       x ~150 giornate di calcio in una stagione:            ≈ 8,4 GB
```

Contro un limite consigliato di **1 GB** per repo (duro: 5 GB). Lo svuotamento
periodico **non svuoterebbe niente**.

Il posto giusto sono gli **artefatti di Actions**: gratis sui repo pubblici,
scadenza configurabile, fuori dalla storia di git. La compattazione li scarica,
fonde e committa solo il risultato; il grezzo scade da solo.

### (b) Il «doppione» non è quello che sembra

Misurato su una sessione vera (28.147 letture, 10 giri, 25 partite):

```
letture in cui il libro E' CAMBIATO:  21.351  (75,9%)
letture identiche alla precedente:     6.796  (24,1%)
```

Quindi **due letture ravvicinate di due gemelli NON sono doppioni**: sono due
campioni di una serie temporale, e buttarne una getta informazione vera. Il
doppione è un'altra cosa: una lettura **identica alla precedente dello stesso
contratto**. Toglierla non perde nulla — fra due cambiamenti il prezzo era
quello, ricostruibile esattamente. È **compressione, non selezione**, ed è per
questo che sta in regola con §5-ter («si conserva l'originale»).

E ha una proprietà che rende la proposta migliore di com'è stata formulata:
**più gemelli si aggiungono, più la compattazione rende.** Con 3 gemelli il
campionamento effettivo passa da 2 minuti a ~40 secondi, quindi fra un
campione e l'altro il libro cambia meno spesso, quindi la frazione di letture
identiche sale. La ridondanza costa **meno che linearmente**.

### (b-bis) ⚠️ RETTIFICA: togliere le letture identiche NON è senza perdita

Sopra ho scritto che eliminare una lettura identica alla precedente «non perde
nulla». **È falso, e vale la pena vedere perché.**

```
letture:  t1=A  t2=A  t3=A  t4=A  t5=B
tenendo solo i cambiamenti:  t1=A, t5=B
```

Il valore è ricostruibile, sì — ma la **risoluzione temporale del cambiamento**
no: con tutte le letture so che il libro è cambiato fra t4 e t5, con le sole
due so soltanto che è cambiato fra t1 e t5. Su un dato in-play, dove la
domanda interessante è *quanto in fretta il prezzo reagisce a un gol*, quella
è esattamente l'informazione che conta.

**La forma giusta è la codifica a corse con ENTRAMBI gli estremi**:

```
{ contratto, valore, da: t1, a: t4, n_letture: 4 }   poi   { valore B, da: t5, ... }
```

Così si sa che il valore era A **almeno fino a t4** e che il cambio è avvenuto
in (t4, t5]. Questa è davvero senza perdita, e regge la regola §5-ter.

**Quanto si risparmia, misurato** su 126.004 righe in-play vere:

| chiave usata per «identico» | righe tenute |
|---|---|
| solo il prezzo medio | 34,0% |
| i due lati del libro (banco + puntatore) | 40,9% |
| **libro + volumi** | **43,8%** |

Avevo previsto che includere i volumi azzerasse la compattazione: **misurato,
costa 3 punti**. Quindi non c'è nessun compromesso da fare — si tengono anche
i volumi e si comprime lo stesso di ~2,3×.

### Cosa resta da sorvegliare

1. **Il grezzo scade.** Se la compattazione si ferma più a lungo della
   scadenza degli artefatti, i dati si perdono per davvero. Il cane da guardia
   dovrà controllare anche lei («l'ultimo compattato ha meno di N ore?»).
2. **Contesa su git**: con lo staging fuori dal repo pushano solo la
   compattazione e i giri pre-partita, quindi il problema quasi sparisce — ed
   è una ragione in più per non tenere lo staging in git.

**Stato: valutata e non ancora costruita.**

## 5. Cosa NON sappiamo, ed è il punto

Le misure del §3 sono aneddoti di una giornata sola. Per decidere servono
frequenze, e non le abbiamo:

- **quanto spesso** un cron salta del tutto (visto una volta, su un workflow
  appena creato — caso notoriamente peggiore);
- **quale frazione** delle partite resta senza prezzo di chiusura in una
  settimana vera;
- **quale copertura in-play** otteniamo davvero su una giornata piena.

Sono esattamente le tre cose che `scripts/controlla_raccolta.py` misura a ogni
giro, quattro volte al giorno. **Fra pochi giorni la decisione si prende su
numeri invece che su una giornata storta.** Nel frattempo il costo di
aspettare non è zero — i dati non raccolti non tornano — ma è limitato al
delta fra ciò che perdiamo ora e ciò che perderemmo con l'alternativa, non
all'intera raccolta.

## 6. Le alternative, coi costi veri

| | cosa risolve | cosa costa | reversibile? |
|---|---|---|---|
| **A. Server sempre acceso** (Oracle Always Free, o Hetzner ~4 €/mese) | tutti e cinque i limiti: cron al secondo, nessun tetto di durata, nessuna coda, **e una rete che si può scegliere** (la lentezza del runner verso Smarkets non è una costante dell'universo) | una macchina da mantenere e aggiornare; una chiave di scrittura sul repo da custodire; **un nuovo punto di rottura che nessun sistema sorveglia** — il cane da guardia dovrebbe girare altrove | sì: il codice non cambia, cambia chi lo lancia |
| **B. Cloudflare Workers + Cron Triggers** | cron al minuto, gratis, molto puntuale | tetto strettissimo di CPU per invocazione: un giro su 25 partite non ci sta. Andrebbe riscritto come tante micro-invocazioni con stato esterno, fuori da Python | no: riscrittura |
| **C. Cloud Run + Cloud Scheduler** | cron preciso, job fino a 24h | account cloud con carta; più pezzi da configurare; costo che può comparire fuori dal free tier | sì, ma con lavoro |
| **D. Catena auto-innescata su Actions** | toglie la dipendenza dal cron ripetuto | ⚠️ **da verificare**: GitHub blocca di proposito i workflow che si ri-innescano col token automatico; servirebbe un token personale come segreto — cioè un segreto da custodire e che scade | sì, banalmente |
| **E. Due workflow sfalsati** (§4-bis) | il tetto delle 6 ore e metà del rischio-cron | un secondo workflow da tenere allineato; raccolta doppia nelle sovrapposizioni | sì, banalmente |
| **F. Il tuo computer** | affidabilità piena quando è acceso | dev'essere acceso; e i dati pre-partita si raccolgono di notte | sì |

## 7. Una nota che va tolta di mezzo

Il progetto ha evitato un VPS alla **Fase 115**, e quel precedente **non si
applica qui**. La ragione di allora era contrattuale — il rischio per un
*account Betfair* — non tecnica. Smarkets è un'API pubblica senza chiave e
senza account: non c'è nessun account da mettere a rischio. Se scegliamo di
non prendere un server dev'essere per il costo di manutenzione, non citando
una decisione presa per un motivo diverso (§1.10 del CLAUDE.md: un esito vale
per il perimetro su cui è stato ottenuto).

## 8. Dove siamo

- **Nessuna decisione presa.**
- Il pezzo più economico e più reversibile — **E**, i due workflow sfalsati —
  è quello che toglie il vincolo più duro (le 6 ore contro 10,5) senza
  cambiare niente d'altro. È il candidato naturale da provare per primo,
  **se** i numeri del cane da guardia diranno che il buco esiste davvero.
- **A** resta il salto di qualità vero, e la ragione storica per escluderlo è
  caduta. Ma introduce una macchina che nessuno sorveglia, e va deciso
  sapendolo.
- La prossima cosa che cambia il quadro non è un'idea: sono i **rapporti del
  cane da guardia** dei prossimi giorni.
