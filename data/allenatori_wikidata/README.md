# Verifica esterna degli allenatori — Wikidata (Fase 141)

> **Cos'è.** La controparte indipendente del database allenatori (Fase 141
> verifica ciò che la Fase 140 ha costruito). Il nostro dato dice *chi risulta
> in panchina* a ogni partita secondo Transfermarkt; questa cartella dice cosa
> ne pensa una fonte **diversa e strutturata**.
>
> **Cosa NON è.** Non è una correzione ai dati. Nessun file di questa cartella
> tocca `files/player_scores/games.csv.gz` né gli snapshot: il confronto vive a
> parte, e ogni divergenza resta *dichiarata*, non applicata (regola R3).

Si rigenera con `python scripts/aggancia_allenatori_wikidata.py --passo tutto`.

## Perché Wikidata e non una ricerca web

1. **È strutturata.** `P286` (allenatore) sull'entità del *club* porta i
   qualificatori `P580`/`P582` — inizio e fine mandato come valori tipizzati.
   Non c'è testo da interpretare, quindi non c'è una lettura da sbagliare.
2. **Ogni allenatore è un Q-id, non una stringa.** È l'unica cosa capace di
   sciogliere gli omonimi che la Fase 140 può soltanto dichiarare: due `Míchel`
   sono due Q-id, e la distinzione smette di essere un'opinione.
3. **È CC0** (pubblico dominio), a differenza di Wikipedia che è CC BY-SA e
   porterebbe lo share-alike per contatto (è la ragione per cui le carriere
   Wikipedia dei giocatori vivono in una cartella separata e auto-dichiarata).
4. **Costa una richiesta per club**, non una ricerca per mandato.

## ⚖️ Robots.txt — perché NON si usa SPARQL

`https://query.wikidata.org/robots.txt` contiene `Disallow: /sparql`.
L'endpoint **risponde** — una sola query avrebbe prodotto tutta questa cartella
in un colpo — e non si può usare. Sta scritto qui perché è esattamente il tipo
di scorciatoia che la prossima sessione sarebbe tentata di prendere trovandola
funzionante.

La via permessa è `https://www.wikidata.org/wiki/Special:EntityData/<qid>.json`:

```
Disallow: /wiki/Special:EntityData/
Allow:    /wiki/Special:EntityData/*.
```

Per la regola del **match più lungo** (RFC 9309 §2.2.2) un URL con estensione è
permesso — è l'endpoint che Wikidata pubblica apposta per l'accesso automatico.
Il controllo è già scritto e verificato in `src/data/wikidata_identity.py`
(⚠️ `urllib.robotparser` su questa coppia risponde **sbagliato**: applica
*first-match-wins* invece del match più lungo). Le pagine `/wiki/<Titolo>` di
Wikipedia, usate solo per leggere il `wgWikibaseItemId` incorporato, sono
permesse e passano da `wikipedia_careers.fetch_page` (cache su disco, un
prelievo per pagina, ritmo limitato, User-Agent identificabile).

## I file

| file | cosa contiene |
|---|---|
| `club_qid.csv` | i **153 club** del perimetro → Q-id, con il titolo Wikipedia usato e quanti mandati `P286` porta l'entità |
| `mandati_wikidata.csv` | lato **club**: i mandati `P286` che toccano il 2017-2026, con Q-id, nome e data di nascita dell'allenatore |
| `persone_qid.csv` | i nostri allenatori → Q-id, con lo stato dell'aggancio |
| `mandati_persona.csv` | lato **persona**: `P6087` (allena la squadra) con le sue date |
| `confronto.csv` | un verdetto per ognuno dei **nostri** mandati |
| `residuo.json` | i casi che nessuna regola automatica chiude → verifica caso per caso |

## Le due cose da sapere prima di usarli

**1. Un'assenza in Wikidata non è una smentita.** La copertura di `P286` è
disuguale e non in modo prevedibile: il Genoa ha 20 mandati, il Newcastle 4.
Per questo la verifica ha **due lati** — la storia del club (`P286`) e quella
della persona (`P6087`) — e per questo il verdetto `assente_da_wikidata`
significa «la fonte non lo sa», mai «il nostro dato è sbagliato».

**2. Le date non parlano della stessa cosa.** Le nostre sono la **prima e
l'ultima partita** di quella persona in panchina; quelle di Wikidata sono
**nomina ed esonero**. È normale che la seconda preceda la prima di giorni: la
tolleranza (`TOLLERANZA_GIORNI = 45`) copre una sosta intera senza arrivare a
coprire il mandato breve di qualcun altro. Un confronto senza questa distinzione
produrrebbe centinaia di divergenze inesistenti.

⚠️ **E le date di Wikidata hanno una precisione dichiarata.**
`+1958-00-00T00:00:00Z` significa «1958, mese e giorno non noti», non «il giorno
zero». Le colonne `prec_da`/`prec_a` la conservano (11 = giorno, 10 = mese,
9 = anno): una data annuale non può contare come una data esatta senza che si
veda.

## ⏱️ Disponibilità temporale (R8)

Tutto ciò che sta qui è **`statico`**: è anagrafica di identità e di mandato
(chi è chi, chi era in carica quando), non una misura della partita. Non
diventa per questo utilizzabile in una feature senza pensarci: «chi era in
carica» è noto prima del fischio, ma «quanto è durato il mandato» contiene il
futuro esattamente come le presenze in carriera (§ regola R8, e vedi
`esperienza_prima` in `src/data/allenatori.py`).

## ⚖️ Licenza

I dati Wikidata sono **CC0** (pubblico dominio): nessun obbligo di attribuzione
né share-alike. Le pagine Wikipedia sono toccate **solo** per leggere il Q-id
incorporato nell'HTML — nessun contenuto testuale viene conservato, quindi il
CC BY-SA non si propaga a questa cartella. La cache delle pagine vive in
`data/wikipedia_cache/`, che **non è versionata**.
