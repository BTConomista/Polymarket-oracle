# Guida pratica: Betfair per QUESTO progetto

> **Questo file è del progetto, non di Betfair** (a differenza di tutti gli
> altri di questa cartella). Distilla dalla documentazione ufficiale solo ciò
> che serve qui, con i vincoli reali già verificati. Scritto alla Fase 111.

## 1 · Il token: due strade, e per noi la prima basta

### Strada A — il cookie del browser (la più semplice, e ci basta)

Il servizio **Historical Data** vuole **solo** l'header `ssoid`. Nessuna
Application Key, nessun certificato. La documentazione di supporto Betfair
indica proprio questa via per lavorare subito:

1. accedi a Betfair nel browser (per un account italiano: `betfair.it`);
2. apri gli strumenti sviluppatore (Chrome: `Ctrl+Shift+J`);
3. **Application → Cookies →** il dominio Betfair;
4. copia il valore del cookie chiamato **`ssoid`**.

Poi, nel terminale dove girerà lo script:

```bash
export BETFAIR_SSOID='il-valore-copiato'
```

Mai come argomento da riga di comando (finirebbe nella history), mai dentro
un file del repo.

### Strada B — login via API (serve se si automatizza)

Richiede **prima** una Application Key. Le due cose insieme:

```bash
# 1. Application Key: si crea UNA SOLA VOLTA, dal tool ufficiale
#    https://apps.betfair.com/visualisers/api-ng-account-operations/
#    operazione createDeveloperAppKeys
#    -> ne escono DUE chiavi: "Live" (nasce INATTIVA) e "Delayed"
#       (la Delayed funziona sull'exchange vero, con dati ritardati)

# 2. Login (endpoint per giurisdizione: .it per un account italiano)
curl -k -i \
  -H "Accept: application/json" \
  -H "X-Application: <AppKey>" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -X POST -d 'username=<utente>&password=<password>' \
  https://identitysso.betfair.it/api/login
# risposta: {"token":"SESSION_TOKEN","product":"APP_KEY","status":"SUCCESS","error":""}
```

Il campo `token` **è** l'`ssoid`.

Limite: **100 login riusciti al minuto**; sforandolo, l'account non può
aprire nuove sessioni per 20 minuti (`TEMPORARY_BAN_TOO_MANY_REQUESTS`).

## 2 · ⚠️ Il vincolo che rompe i download lunghi: 20 minuti

| giurisdizione | durata sessione |
|---|---|
| `.com` internazionale | 12 ore (24h per UK/Irlanda) |
| **Italia e Spagna** | **20 minuti** |

E — testuale dalla documentazione — «*Session times aren't determined or
extended based on API activity*»: **scaricare non tiene viva la sessione**.
Un download di qualche migliaio di file muore a metà.

Per questo `scripts/fetch_betfair_historic.py` chiama da sé
`https://identitysso.betfair.it/api/keepAlive` **ogni 10 minuti** (metà
finestra, con margine). Se il tuo account non fosse italiano:
`--jurisdiction com`.

## 3 · ❓ La domanda aperta da fare all'assistenza

**Un account dell'exchange *italiano* ha accesso a
`historicdata.betfair.com`?**

Non è una pignoleria: l'exchange italiano è una licenza separata (registrazione
su `register.betfair.it`, login su endpoint `.it` dedicati), mentre il servizio
storico è `.com`. La documentazione **non lo dice** né in un senso né
nell'altro, e noi non possiamo verificarlo: quel dominio risponde **403 da
questo ambiente** per blocco geografico.

Testo pronto:

> I have an Italian Exchange account (betfair.it). Can I use it to access the
> Historical Data service at historicdata.betfair.com — specifically, to
> acquire the free BASIC monthly packages for Soccer and download data via the
> API? If not, what account type is required?

**Il test più rapido resta però pratico**: prendi il token e lancia
`python scripts/fetch_betfair_historic.py --check`. Se elenca dei pacchetti,
l'accesso c'è.

## 3-bis · ⚠️ RIDIMENSIONAMENTO (Fase 113) — leggere PRIMA di scaricare

Domanda dell'utente: «quanto serve davvero questo sforzo? quali dati
scarichiamo che non possiamo avere da altre parti?». Verificato, e la risposta
ridimensiona quanto scritto sotto. Tre fatti:

**1. La stima che il dato sostituirebbe alimenta pochissimo.**
`read_ou_close_estimates()` è chiamata **solo da un test**: nessun modello,
nessun backtest la consuma. ⚠️ *Rettifica della Fase 114*: dire «non alimenta
nulla» era **troppo netto** — il CSV è letto direttamente da
`_run_fase75_squeeze_2017_19.py`, che su quella stima ha costruito
un'analisi vera («apertura REALE + chiusura STIMATA»), e da
`verifica_stime.py` che la valida. Il fatto esatto è: la stima **non era una
via di prima classe**, e chi la voleva se ne faceva il join a mano. Dalla
Fase 114 c'è `loader.ou_close_probability()`. E i backtest ufficiali girano su **2020-21 →
2025-26**, stagioni che hanno tutte la chiusura O/U reale. Il buco 2017-19
**non tocca nessun risultato pubblicato**.

**2. Il costo vero del buco è un altro, ed è misurabile**: 3.652 partite
(**22,7%**) hanno la chiusura 1X2 ma non quella O/U, e senza entrambe il
motore **market-implied** — il titolare — non può girare. Il guadagno reale
non è «un dato più preciso della stima»: è **due stagioni che passano da
inutilizzabili a utilizzabili**. Sono però le due *più vecchie*, cioè le meno
rappresentative del calcio di oggi.

**3. Una fetta grossa del valore ce l'abbiamo GIÀ, gratis.** `football-data`
pubblica **20 colonne Betfair Exchange** per 2024-25 **e 2025-26**: 1X2, O/U
2.5 e handicap asiatico, *apertura e chiusura* (`BFEH/BFECH…`, `BFE>2.5`,
`BFEC>2.5`, `BFEAHH`, `BFECAHH`). **3.393 partite, copertura 96,8%**,
scaricabili in trenta secondi — e **mai usate**.

Misurato su quelle: il 1X2 di chiusura Betfair ha log-loss **0.9676** contro
**0.9682** della media multi-book (Δ −0.00060, IC95 [−0.00154, +0.00041],
P 87.9% — **non conclusivo**), con overround 1.0055 contro 1.0531. Cioè:
Betfair come *fonte* vale poco più della media dei book — il suo vantaggio è
di essere **indipendente**, non più preciso.

**Conseguenza sull'ordine dei lavori.** Prima si usano le colonne Betfair
gratuite (costo zero per l'utente, stagioni più rilevanti), e solo se lì
emerge qualcosa si giustifica lo scarico storico. Lo scarico resta l'unica
via per **due** cose che non esistono altrove: la **traiettoria minuto per
minuto** (pista B) e i **mercati oltre 1X2/O-U/handicap** (pista C, tutta da
verificare con `--dry-run`). Non per il buco O/U in sé.

**Onestà su quanto avevo detto.** Alla Fase 109 avevo presentato Betfair come
la pista che «merita di essere percorsa», sulla base di un MAE 0.0060 contro
~0.014 della stima. Il numero è giusto, la conclusione era sbilanciata: non
avevo controllato **chi usa quella stima** (nessuno) né **cosa abbiamo già**
(due stagioni di Betfair gratis). Entrambi i controlli erano a portata di
`grep`.

## 4 · Cosa possiamo farci — in ordine di valore

### A · Chiudere il buco O/U 2017-19 *(il bersaglio dichiarato)*

L'ultimo buco dati vero del progetto, oggi coperto da una stima. Betfair è
**l'unico candidato mai trovato che sia migliore della stima**: MAE 0.0060
dalla media multi-book contro ~0.014 della stima (misurato sulla 2024-25,
Fase 109). Protocollo: prima la 2024-25 per validare l'estrazione contro
`BFEC>2.5`, poi il 2017-18.

### B · La traiettoria delle quote *(un asse di dati nuovo)* — ✅ già nello stesso scarico

Il piano BASIC dà **istantanee ogni minuto**, non solo la chiusura.
`newseason.md` elenca «le quote di apertura e la loro traiettoria» fra le cose
che **non si recuperano** dopo il calcio d'inizio, e la dichiara «mai avuta a
nessuna scala». Con questi file diventa recuperabile **all'indietro, dal
2015** — e tocca una domanda aperta: la Fase 93 ha localizzato il nostro
deficit nelle **partite equilibrate della seconda metà di stagione**, e la
Fase 98 ha visto che il nostro errore correla +0.43 con quello dell'apertura.
La traiettoria dice *quando* il mercato impara le cose: è la misura che
manca a quella diagnosi.

**Dalla Fase 112 A e B escono dallo STESSO scarico**: `_serie_from_stream`
estrae tutta la serie pre-partita e la chiusura ne è l'ultimo punto, così un
solo download serve entrambe le piste. Non è un dettaglio: estrarre solo la
chiusura avrebbe costretto a **ri-scaricare tutto** il giorno in cui si vuole
la traiettoria. Output: `betfair_traiettoria_<mercato>_<stagione>.csv.gz`
(compresso: la serie pesa ~2 ordini di grandezza più delle chiusure), con
`minuti_al_via` come asse.

### C · Validare i ~17 mercati che nessuno ha mai controllato *(forse il più grosso)*

Il progetto prezza GG/NG, risultato esatto, multigol, total-squadra, clean
sheet… e per sua stessa ammissione **l'handicap asiatico è l'unico mercato
del listino mai validato contro una quota esterna indipendente** (Fase 88).
Betfair è una borsa che quota molti di quei mercati.

⚠️ Da verificare, non da assumere: quali mercati ci siano davvero nei
pacchetti storici lo dice `--dry-run`, che ora stampa i nomi reali. È il
primo controllo da fare, perché **decide quanto vale tutta questa pista**.
Se ci sono, `--market-type <NOME>` li scarica senza altro codice.

### D · Volume e liquidità *(a pagamento, valore incerto)*

I piani ADVANCED/PRO aggiungono il volume scambiato: quanto denaro c'era su
ogni lato. È un segnale che il progetto non ha mai avuto — una misura di
"quanta convinzione" c'è dietro un prezzo. Ma costa, e il valore non è
misurato: **da non comprare prima di aver esaurito il BASIC gratuito**.

### E · Il test prospettico 2026-27 *(Fase 78, ha una scadenza)*

Betfair darebbe catture pre-partita datate e indipendenti per il test
prospettico. Due frizioni: gira solo dalla tua macchina (geo-blocco), e la
sessione italiana da 20 minuti complica l'automazione. Da valutare **dopo**
che A e B hanno funzionato — Smarkets e Polymarket, già integrati, coprono
intanto gli outright.

## 5 · Quello che NON faremo

Le API di scommessa (`placeOrders` e affini) sono documentate in
`60_ordini__*` per completezza della copia, ma **il progetto non piazza
scommesse**: il `CLAUDE.md` dice, e resta vero, che il modello **non batte il
mercato** e non va usato per scommettere soldi veri. Betfair qui è una
**fonte di dati**, non un canale operativo.
