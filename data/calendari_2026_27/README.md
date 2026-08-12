# Calendari 2026-27 — i cinque campionati modellati

**Consegna diretta dell'utente**, 11/08/2026. Originali in `originali/`, come
consegnati (regola §5-ter: si conserva l'originale, non solo la versione di
lavoro). Impronte e conteggi in `manifesto.json`.

## Cosa c'è

**1.752 partite**, e il numero è **verificato per identità**, non accettato:

| lega | partite | squadre | giornate | round-robin completo |
|---|---|---|---|---|
| Serie A | 380 | 20 | 38 | ✅ 20×19 = 380 |
| Premier League | 380 | 20 | 38 | ✅ |
| La Liga | 380 | 20 | 38 | ✅ |
| Bundesliga | 306 | 18 | 34 | ✅ 18×17 = 306 |
| Ligue 1 | 306 | 18 | 34 | ✅ |

Nessuna partita mancante, nessun doppione, ogni squadra incontra ogni altra
esattamente due volte. **Struttura perfetta.**

Colonne: `campionato, paese, stagione, giornata, data, giorno, ora_italiana,
ora_locale, squadra_casa, squadra_trasferta, data_ora_provvisoria,
casa_nome_ufficiale, trasferta_nome_ufficiale, kickoff_utc`.

---

## ⚠️ 1. Le DATE sono provvisorie al 93,8% — le squadre no

`data_ora_provvisoria = sì` su **1.643 righe su 1.752**. E si vede nel dato:
tutte e 10 le partite della giornata 1 di La Liga portano lo stesso orario
segnaposto, `2026-08-16T15:00Z`.

Il confronto col listino Smarkets (dato di mercato reale, raccolto il 04/08)
lo conferma — la giornata 1 di Liga è in realtà **spalmata su cinque giorni**:

| partita | calendario | Smarkets |
|---|---|---|
| Alavés – Getafe | 16/08 15:00Z | **15/08 17:30Z** |
| Sevilla – Rayo Vallecano | 16/08 15:00Z | 15/08 19:30Z |
| Celta Vigo – Osasuna | 16/08 15:00Z | 16/08 19:30Z |
| Deportivo La Coruña – Elche | 16/08 15:00Z | 17/08 19:00Z |
| Atlético Madrid – Málaga | 16/08 15:00Z | **19/08 19:00Z** |

> **Regola d'uso che ne discende.** Di questi file si usano gli
> **accoppiamenti** e la **numerazione delle giornate**, che sono affidabili e
> completi. **Le date e gli orari NO**: per quelli la fonte è il listino
> Smarkets, che è il mercato e quindi la verità operativa. Il calendario serve
> a sapere *quali* partite e *in che ordine*; Smarkets a sapere *quando*.

Conseguenza pratica: il calendario **non sposta** la scadenza del
congelamento. La prima partita resta Alavés–Getafe il **15/08**, come già
rettificato alla Fase 127.

---

## ⚠️ 2. I nomi sono in italiano — vanno agganciati

I file usano esonimi italiani (`Barcellona`, `Siviglia`, `Bayern Monaco`,
`Lione`, `Marsiglia`, `Amburgo`, `Stoccarda`…), mentre gli snapshot usano i
nomi di football-data. Stato dell'aggancio contro le squadre viste nelle 9
stagioni di ciascuno snapshot:

| lega | risolvibili con alias | da verificare a mano |
|---|---|---|
| **Serie A** | **0 — combaciano tutte e 20** | **nessuna** |
| Ligue 1 | 6 | 1 (`Le Mans`) |
| Bundesliga | 10 | 2 (`Colonia`, `Elversberg`) |
| Premier League | 0 | 5 (`Manchester City`, `Manchester United`, `Nottingham Forest`, `Coventry`, `Hull City`) |
| La Liga | 4 | 8 (`Athletic Bilbao`, `Atlético Madrid`, `Celta Vigo`, `Espanyol`, `Rayo Vallecano`, `Real Sociedad`, `Deportivo La Coruña`, `Racing Santander`) |

⚠️ **La distinzione che conta, e sbagliarla è un bug silenzioso**: fra i nomi
«da verificare» convivono due cose diverse —

- **stessa squadra, stringa diversa** (`Manchester City` → `Man City`,
  `Rayo Vallecano` → `Vallecano`, `Colonia` → `FC Koln`): serve un **alias** in
  `src/data/sources.py`;
- **squadra davvero nuova** (`Racing Santander`, `Coventry`, `Hull City`,
  `Elversberg`, `Le Mans`): **neopromossa**, senza storia, e va nel prior δ.

Trattare la prima come la seconda darebbe a Manchester City il prior delle
neopromosse. È esattamente il caso che ha generato `TEAM_ALIASES` («Hellas
Verona» → «Verona»), e va istruito squadra per squadra — mai con un
riconoscitore automatico.

⚠️ Le neopromosse **si dichiarano, non si deducono**: `promoted_teams()` sulla
stagione precedente restituisce le promosse del **2025-26**, non del 2026-27
(Fase 128).

**La Serie A è l'unica lega con zero lavoro di aggancio.** È una ragione in più
per partirci.

---

## 3. Le colonne `casa_nome_ufficiale` / `trasferta_nome_ufficiale`

Contengono la denominazione estesa (`Deportivo Alavés`, `Club Atlético de
Madrid`, `Getafe CF`). Non servono all'aggancio — che va fatto sugli alias del
progetto — ma sono **conservate**: sono il modo per disambiguare un nome corto
ambiguo, e non si ri-scaricano.

## 4. Stato d'uso

**RACCOLTO, NON ANCORA USATO.** Nessuno script del progetto legge questi file.
Il consumatore previsto è l'harness delle previsioni prospettiche
(`docs/REGISTRO_VARIANTI.md` §0.6, P4), che non esiste ancora.
