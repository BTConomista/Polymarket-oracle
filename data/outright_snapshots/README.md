# `data/outright_snapshots/` — archivio storico dei mercati di STAGIONE

**Cosa sono.** Istantanee **congelate e versionate** dei prezzi dei mercati
outright (campione, qualificazione europea, retrocessione, capocannoniere) delle
5 leghe seguite dal progetto. Le scrive `scripts/archive_outrights.py`.

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
| `history.csv` | **formato lungo** — una riga per `data × lega × mercato × squadra`. È il file da leggere per le analisi |

Colonne di `history.csv`:

| colonna | significato |
|---|---|
| `price` | prezzo grezzo del contratto «Yes» (= probabilità implicita **non** devigata) |
| `prob` | probabilità devigata **solo se `exclusive`**, altrimenti = `price` |
| `exclusive` | `True` per i mercati a vincitore unico (campione, capocannoniere): gli esiti sono mutuamente esclusivi, la somma è l'overround e si può rinormalizzare a 1. `False` per le qualificazioni: sono binari **indipendenti** (si qualificano in 4-5), la somma vale legittimamente 2-4 e rinormalizzarla sarebbe un errore concettuale |
| `overround` | somma dei prezzi, solo per i mercati esclusivi |
| `settled_share` | quota di esiti già a 0 o 1. **≥ 0.9 = non è una previsione**, è la coda di una stagione già conclusa (vedi sotto) |
| `n_entries` | numero di esiti quotati nell'evento |

## ⚠️ Tre trappole già incontrate (leggere prima di usare i dati)

1. **`settled_share ≥ 0.9` non è una previsione.** Il 25/07/2026 tutti i mercati
   «qualify for UEFA …» si riferivano alla stagione **appena finita** (19 esiti
   su 20 già a zero, favorito al 100%), non al 2026-27. Filtrare sempre.
2. **Non rinormalizzare i mercati non esclusivi.** Vedi `exclusive` sopra: la
   somma 0.81 o 2.5 su una qualificazione è corretta, non un bug.
3. **I segnaposto**: Polymarket pubblica righe «Team A/B/C/Other» senza mercato
   vero dietro. Sono già escluse dall'archiviatore (`PLACEHOLDERS`), ma se una
   somma esce assurda controllare lì per prima cosa.

## Copertura al primo censimento (25/07/2026)

| mercato | leghe quotate |
|---|---|
| campione di stagione | Serie A, Premier, La Liga, Bundesliga, Ligue 1 |
| qualificazione UECL | tutte e 5 *(ma erano code della stagione conclusa)* |
| qualificazione UCL/UEL | solo Ligue 1 *(idem)* |
| **retrocessione** | **NON QUOTATA da Polymarket in nessuna lega** |
| capocannoniere | nessuna |

La retrocessione è il mercato dove abbiamo il modello meglio tarato (Fase 94,
deriva di forza adottata) ed è **l'unico dei tre che Polymarket non prezza**:
se comparisse, l'archiviatore lo prende da solo (il filtro è per *tipo* di
mercato, non per elenco chiuso).

## Uso

```bash
python scripts/archive_outrights.py            # scarica e archivia la data di oggi
python scripts/archive_outrights.py --show     # mostra l'archivio esistente
python scripts/archive_outrights.py --from-dump F --date 2026-07-25   # riusa un dump
```

Rieseguire nello stesso giorno **sovrascrive** la riga di quella data
(idempotente), non duplica.

> **Cadenza consigliata**: una istantanea **prima di ogni inizio stagione**
> (metà agosto) e una **a stagione conclusa**, più quelle spontanee. Il
> promemoria operativo vive in `docs/PISTE.md` §4-bis.
