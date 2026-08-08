# Quote IN-PLAY di Smarkets (Fase 143)

Prezzi raccolti **a partita in corso**, a cadenza fissa. Cartella **separata**
da `data/smarkets_matches/`: non è un dettaglio organizzativo.

## Perché è separata

Un prezzo in-play **conosce il punteggio**, uno pre-partita no. Non sono lo
stesso dato e non sono confrontabili riga per riga. Se stessero insieme, ogni
lettore dell'archivio pre-partita — `ultimo_listino_completo()` per primo — li
leggerebbe come se fossero la stessa cosa, **senza dare errore**: il modo
peggiore di sbagliare (R6).

## Formato

Un file per **sessione** (non per giro), `YYYY-MM-DDTHH-MM-SS.json.gz`,
riscritto sul disco del runner ogni 5 giri e committato alla fine. Una
sessione dura ~40 minuti e contiene decine di giri.

| campo di riga | |
|---|---|
| `istante_utc` | **il momento di QUESTO giro**. Il file è una serie temporale, non uno scatto: senza questo campo le righe sono indistinguibili |
| `giro` | `nucleo` (1X2, O/U 2.5, GG/NG, risultato esatto — ogni 2 min) o `pieno` (tutti i ~103 mercati — ogni 15 min) |
| `stato_mercato` | `live` / `settled` / `halted` — vedi sotto, è il campo che porta lo stato della partita |
| tutto il resto | come `data/smarkets_matches/`: `p_banco`, `p_puntatore`, `p_mid`, `spread`, volumi, `fascia` |

## Il punteggio non è un campo, ma c'è

Smarkets **non espone un tabellone** (provati `/events/{id}/scores/` e
`/state/`: 404). Lo stato della partita si legge da *cosa è ancora quotato*:

- **`stato_mercato == "settled"`** marca i mercati già decisi. A 3 gol fatti,
  O/U 0.5/1.5/2.5 sono `settled` e la 3.5 è `live`: i gol sono la linea più
  alta regolata, arrotondata per eccesso;
- il **risultato esatto** tiene solo i punteggi ancora raggiungibili, e il
  **minimo componentwise** è il punteggio corrente.

Verificato dal vivo su Cambridge-Barnet (08/08/2026, 13:42): sopravvivevano
2-1, 2-2, 2-3, 3-1, 3-2, 3-3 → minimo **2-1**; e O/U 2.5 `settled` con 3.5
`live` → **3 gol**. Due segnali indipendenti, stessa risposta. La stessa
logica vale per **corner** e **cartellini**, che hanno le loro linee O/U.

⚠️ **Qui il punteggio NON è dedotto.** Il file contiene ciò che l'API ha detto,
non ciò che ne ricaviamo: la ricostruzione è una regola da validare su partite
a risultato noto, e finché non lo è non entra nei dati (§5, stime dichiarate).

C'è un terzo stato: **`halted`**, il mercato sospeso. È il momento in cui *sta
succedendo qualcosa* (un gol in verifica, un VAR) e in sé è informazione.

## Cadenza

Nucleo ogni **2 minuti**, listino pieno ogni **15**. Scelta dell'utente
l'08/08/2026 come punto di partenza prudente («partiamo più leggeri e
vediamo»): si alza misurando quanto pesa e quanto serve, non a sentimento.
Le leve sono in `scripts/fetch_smarkets_live.py` e negli input del workflow.

## Buchi, e perché ce ne sono

`giri_incompleti` elenca le partite perse o raccolte a metà in un dato giro
(stessa politica della Fase 141). Ma esistono anche buchi **fra** le sessioni:
la sentinella è un cron di GitHub e parte con **30-40 minuti di ritardo**. Le
sessioni durano più del periodo della sentinella apposta, così si sovrappongono
e il ritardo viene assorbito — ma una copertura continua non è garantita, e un
file non c'è **anche** quando semplicemente non giocava nessuno del perimetro.
