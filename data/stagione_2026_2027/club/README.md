# `club/` — una cartella per squadra, per sempre

Struttura: `club/<PAESE-ISO3>/<slug>/`, dove **PAESE è quello del club**, non
della competizione. Esempi: `club/ITA/inter/`, `club/ENG/manchester-city/`,
`club/POR/benfica/` (il Portogallo non è fra le leghe che modelliamo, ma il
Benfica lo incontriamo nelle coppe).

**Un club sta in una sola cartella per tutta la sua vita**, anche se retrocede,
cambia nome, cambia proprietà o cambia competizione. La cartella è la sua
**identità**; categoria e classifica sono attributi che cambiano nel tempo e
vivono nei file, non nel percorso.

## Lo slug

Minuscolo, ASCII, trattini. È una **chiave tecnica**: si sceglie una volta e non
si tocca più, anche se il club cambia nome ufficiale (in quel caso si aggiorna
`nome_ufficiale` dentro `anagrafica.json` e si registra il cambio, non si
rinomina la cartella — rinominarla spezzerebbe tutto lo storico).

## ⚠️ I nomi squadra sono il posto dove si rompono i join

Questo repo ha già pagato il bug: «Hellas Verona» contro «Verona»
(`TEAM_ALIASES` in `src/data/sources.py`). Ora le fonti da allineare sono
almeno quattro — i nostri snapshot, Smarkets, la fonte delle rose, il calendario
— e ognuna scrive i nomi a modo suo («Inter», «Inter Milan», «Inter Milano»,
«FC Internazionale Milano»).

Regole:

1. `anagrafica.json` contiene **tutti** gli alias conosciuti, uno per fonte,
   con il nome della fonte accanto. È lì che si guarda per fare un join.
2. Un alias si aggiunge **solo dopo averlo verificato a mano** su una partita
   reale. Mai un match approssimato, mai una distanza di stringa: produrrebbe
   join sbagliati che nessun test vede (**R6**, il finto pieno).
3. Due club diversi possono avere nomi quasi identici in paesi diversi. Il
   paese fa parte della chiave, sempre.

## File attesi in ogni cartella

| file | che cos'è | si modifica a mano? |
|---|---|:--:|
| `anagrafica.json` | identità, alias, rosa, obiettivi, competizioni, allenatore, stadio | sì, ma con registro |
| `rosa_storico.jsonl` | una riga per **variazione** (mercato, valore, infortunio lungo) | append-only |
| `vista_corrente.md` | riassunto leggibile, **rigenerato** dai file giornalieri | ❌ **mai** |

`vista_corrente.md` porta in testa la riga «⚙️ GENERATO — non modificare» e la
data di rigenerazione. Se qualcuno lo modifica a mano, la prima rigenerazione
cancella la modifica: è il comportamento voluto, non un difetto.
