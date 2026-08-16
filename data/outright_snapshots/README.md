# `data/outright_snapshots/` — archivio storico dei mercati di STAGIONE

**Cosa sono.** Istantanee **congelate e versionate** dei prezzi dei mercati
outright delle 5 leghe seguite dal progetto. Le scrive
`scripts/archive_outrights.py`.

**Due fonti, entrambe borse (non bookmaker):** **Polymarket** (Gamma API) e
**Smarkets** (API v3 pubblica). Non si sovrappongono quasi mai — è metà del
valore dell'archivio:

| mercato | Polymarket | Smarkets |
|---|---|---|
| campione di stagione | ✅ 5 leghe | ✅ 5 leghe (le **uniche** righe confrontabili fra le due fonti) |
| qualificazione europea (UCL/UEL/UECL) | ✅ | — |
| **retrocessione** | — | ✅ (solo Premier) |
| **Top 2/3/4/5/6, top-half** | — | ✅ |
| capocannoniere | — | — (**mai quotato finora**: il tipo di mercato è supportato dall'archiviatore, ma non è ancora comparso) |

**Stato dell'archivio** (conteggio `pandas` su `history.csv`, 16/08/2026):
**4 istantanee** per **2.347 righe**.

| data | Polymarket | Smarkets | come è stata presa |
|---|---|---|---|
| 2026-07-25 | 211 | 254 | a mano (Fase 97) |
| 2026-07-26 | 211 | 254 | a mano |
| 2026-08-12 | 211 | 552 | a mano (Fase 153, trovando l'archivio fermo da 18 giorni) |
| 2026-08-16 | 211 | 443 | a mano (Fase 156, trovando il workflow morto da 4 giorni) |

⚠️ **NESSUNA di queste è stata presa dall'automazione**, e i due buchi non si
recuperano: **26/07 → 12/08** (18 giorni: il collettore non aveva un workflow,
Fase 153) e **12/08 → 16/08** (4 giorni: il workflow c'era e falliva **4 run su
4** su `ModuleNotFoundError: requests`, Fase 156). Il secondo buco è il più
caro dei due in proporzione: cade sui **primi giorni di campionato**, quando il
prezzo outright si muove di più. Dal 16/08 il workflow installa la dipendenza e
il guardiano (soglia 48 h) non muore più mentre ripara — ma la prova che
funzioni è **il primo file scritto da lui**, non il fatto che sia verde.

È un archivio appena nato: cresce solo in avanti (vedi sotto).

## ⚠️ La trappola che si apre il giorno del calcio d'inizio (Fase 156-bis)

Quando una lega **comincia**, Smarkets porta il suo evento outright e i suoi
mercati da `upcoming`/`open` a **`live`**. Fino al 16/08/2026 l'archiviatore
teneva solo `state == "open"` (mercati **e** contratti, due filtri in AND):
risultato, **l'archivio di una lega si spegneva il giorno della prima
giornata**. Misurato: La Liga, partita il 15 agosto, aveva **109 righe il 12/08
e zero il 16/08**, mentre le altre quattro leghe — non ancora cominciate — erano
tutte presenti.

Adesso si accettano `open` **e** `live`; restano fuori `settled` e `closed`,
dove un prezzo non esiste più. Se un giorno una lega sparisce di nuovo
dall'archivio, il primo sospetto è questo: **guardare lo `state`**, non la rete.

## Perché esistono (il motivo è tutto qui)

Il limite più duro del simulatore di stagione (Fase 89) è che **non esistono
quote outright storiche** raggiungibili: possiamo dimostrare «battiamo le
baseline», **non** «battiamo il mercato» — che è l'unico confronto che conta
(principio §1.6: onestà sui limiti).

Quel limite **non si può rimuovere all'indietro**. Ma si può smettere di
subirlo in avanti: se congeliamo i prezzi **ogni volta che li guardiamo**, fra
qualche stagione lo storico ce l'avremo — e sarà nostro, con la data di
osservazione certificata dal commit git.

Da qui la scelta di **versionare** questa cartella, al contrario del dump
grezzo di `fetch_polymarket_open.py` (che sta in `data/polymarket/`, in
`.gitignore`): uno snapshot che vive solo in un container effimero non
costruisce nessuno storico.

## Formato

| file | contenuto |
|---|---|
| `YYYY-MM-DD.json` | istantanea completa di quella data (tutti i campi, incluso `event_slug`, volumi, liquidità) |
| `history.csv` | **formato lungo** — una riga per `data × fonte × lega × mercato × squadra`. È il file da leggere per le analisi. ⚠️ `source` fa parte della chiave: senza, il campione di stagione compare **due volte** (Polymarket e Smarkets) e ogni conteggio raddoppia |

Colonne di `history.csv` (26 in tutto; qui le portanti):

| colonna | significato |
|---|---|
| `snapshot_date`, `source`, `league`, `market`, `team` | la **chiave**: nessuna delle cinque è ridondante |
| `price` | prezzo grezzo del contratto «Yes» (= probabilità implicita **non** devigata) |
| `prob` | probabilità devigata **solo se `exclusive`**, altrimenti = `price`. **Vuota** quando `price_side = ask_only` (vedi trappola 4) |
| `exclusive` | `True` per i mercati a vincitore unico (campione, capocannoniere): gli esiti sono mutuamente esclusivi, la somma è l'overround e si può rinormalizzare a 1. `False` per qualificazioni, retrocessione e Top-N: sono binari **indipendenti**, la somma vale legittimamente 2-4 e rinormalizzarla sarebbe un errore concettuale |
| `overround` | somma dei prezzi, solo per i mercati esclusivi (visto: 1.0051 Smarkets Premier → 1.0715 Polymarket Serie A) |
| `price_sum` | somma dei prezzi anche quando il mercato non è esclusivo (dove l'`overround` non ha senso) |
| `settled_share` | quota di esiti già a 0 o 1. **≥ 0.9 = non è una previsione**, è la coda di una stagione già conclusa (vedi trappola 1). Vuota sui mercati Top-N |
| `n_entries`, `n_priced` | esiti quotati nell'evento / di cui con un prezzo utilizzabile |
| `best_bid`, `best_ask`, `spread`, `price_side`, `book` | **solo Smarkets** (Polymarket li lascia vuoti): stato del libro. `book ∈ {two_sided, partial}`, `price_side ∈ {mid, ask_only, bid_only, empty}` |
| `volume`, `liquidity`, `event_volume`, `event_liquidity` | **solo Polymarket** |
| `event_title`, `event_slug`, `market_name`, `market_id` | identificativi grezzi della fonte, utili per risalire all'originale |

## ⚠️ Quattro trappole già incontrate (leggere prima di usare i dati)

1. **`settled_share ≥ 0.9` non è una previsione.** Il 25/07/2026 tutti i mercati
   «qualify for UEFA …» si riferivano alla stagione **appena finita**: La Liga,
   Premier e Serie A hanno `settled_share = 0.950` (19 esiti su 20 già a zero) e
   il favorito è prezzato 0.9275 (Premier) e 0.9655 (Serie A). Filtrare sempre.
2. **Non rinormalizzare i mercati non esclusivi.** Vedi `exclusive` sopra: la
   somma 0.81 o 2.5 su una qualificazione, su una retrocessione o su un Top-N è
   corretta, non un bug.
3. **I segnaposto**: Polymarket pubblica righe «Team A/B/C/Other» senza mercato
   vero dietro. Sono già escluse dall'archiviatore (`PLACEHOLDERS`), ma se una
   somma esce assurda controllare lì per prima cosa.
4. **Su Smarkets il libro ha spesso un lato solo.** Al 25/07/2026: **158 righe
   su 254** hanno `book = "partial"` e **139** hanno `price_side = "ask_only"`
   (2 sono `empty`). Un `best_ask` senza `best_bid` è un **tetto** al valore
   equo, non un prezzo, e per quelle righe `prob` è **vuota**. Anche dove il mid
   esiste (113 righe), lo `spread` va da 0.0009 a **0.1703** (mediana 0.0039).
   Due esempi concreti di mid da buttare: *PSG — campione Ligue 1* (`best_bid`
   0.6993, `best_ask` 0.8696 → «mid 78,4%» con 17 punti di spread) e
   *Nottingham Forest — retrocessione Premier* (`best_bid` 0.0010, `best_ask`
   0.100 → «mid 5,05%» con 9,9 punti di spread). **Filtrare sullo spread prima
   di usare il mid in un'analisi.**

## Copertura al primo censimento (25/07/2026, verificata su `history.csv`)

| mercato | Polymarket | Smarkets |
|---|---|---|
| campione di stagione | tutte e 5 *(`settled_share` 0.611 Ligue 1 → 0.857 La Liga: sono ancora code della stagione conclusa)* | tutte e 5 |
| qualificazione UECL | **4**: Serie A, Premier, La Liga, Ligue 1 — **non** Bundesliga *(code della stagione conclusa)* | — |
| qualificazione UCL / UEL | solo Ligue 1 *(idem)* | — |
| **retrocessione** | **non quotata in nessuna lega** | ✅ **solo Premier** — ed è l'unico mercato dell'archivio con `settled_share = 0.000`, cioè l'unico che guarda davvero avanti |
| Top 2 / 3 / 4 / 5 / 6 / top-half | — | Premier (2, 4, 5, 6, top-half), La Liga (4), Ligue 1 (3) |
| capocannoniere | nessuna | nessuna |

> ⚠️ **Aggiornata rispetto alla prima stesura.** Questa tabella diceva
> «qualificazione UECL: tutte e 5» (sono **4**: manca la Bundesliga) ed elencava
> solo Polymarket, con la nota «la retrocessione è l'unico dei tre che Polymarket
> non prezza». Resta vero che *Polymarket* non la prezza — ma **Smarkets sì**,
> sulla Premier, ed è la riga più interessante dell'intero archivio: la
> retrocessione è il mercato dove abbiamo il modello meglio tarato (Fase 94,
> deriva di forza adottata) ed è l'unico prezzo che non sia la coda di una
> stagione già finita.

Se un mercato oggi assente comparisse, l'archiviatore lo prende da solo: il
filtro è per *tipo* di mercato, non per elenco chiuso.

## Uso

```bash
python scripts/archive_outrights.py            # scarica da entrambe le fonti e archivia oggi
python scripts/archive_outrights.py --show     # mostra l'archivio esistente
python scripts/archive_outrights.py --only smarkets    # una fonte sola (anche `polymarket`)
python scripts/archive_outrights.py --from-dump F --date 2026-07-25   # riusa un dump
```

Rieseguire nello stesso giorno **sovrascrive** la riga di quella data
(idempotente), non duplica.

**Nomi squadra: NON normalizzati** — l'archivio conserva i nomi grezzi di
ciascuna fonte («Inter Milan» su Polymarket, «Inter Milano» su Smarkets, «Inter»
da noi). È deliberato: una normalizzazione non validata produrrebbe join
silenziosamente sbagliati. L'unica mappa esistente e verificata a mano è
`SMARKETS_TO_OURS` in `scripts/_run_fase97_relegation_market.py` (Premier, 20 su
20); **chi aggiunge una lega deve costruire la sua**. Vedi `docs/DATI.md` §5-bis.

> **Cadenza consigliata**: una istantanea **prima di ogni inizio stagione**
> (metà agosto) e una **a stagione conclusa**, più quelle spontanee. Il
> promemoria operativo vive in `docs/PISTE.md` §4-bis.
