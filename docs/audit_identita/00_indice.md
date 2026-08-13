# Audit dell'identità del database — fotografia di un lavoro INTERROTTO

**Data**: 11 agosto 2026 · **Workflow**: `wf_93f8ba67-2b8` · **Stato**: ⛔ interrotto a metà

Questo non è un rapporto: è una **fotografia**, scattata su richiesta dell'utente
prima di passare ad altro. Un audit a 62 agenti è stato lanciato, ha completato la
diagnosi, e si è fermato in mezzo alla verifica per esaurimento del limite di
sessione. Tutto quello che ha prodotto è qui dentro, **per intero e senza tagli**,
così che chi riprenderà non debba rifarlo.

Il workflow verrà ripreso in futuro. Questo indice serve a chi lo riprende.

---

## 1 · Fin dove è arrivato

| fase | previsti | completati | esito |
|---|--:|--:|---|
| **Diagnosi** (un agente per dominio) | 6 | **6** | ✅ completa |
| **Verifica** (un agente per reperto) | 54 | **11** | ⛔ interrotta |
| **Applica** (un agente per file) | ~5 | 0 (1 uccisa a metà) | ⛔ mai completata |
| **Guardia** (test + suite + rapporto) | 1 | 0 | ⛔ mai partita |
| | **62** | **17** | 45 morti sul limite |

Costo del lavoro qui fotografato: **2.466.633 token**, 690 chiamate a strumenti,
**2h09m37s** di esecuzione.

I 10 reperti con `riparabile_ora = false` non erano nemmeno stati mandati in
verifica (54 = 64 − 10): per quelli non esiste né conferma né smentita.

---

## 2 · ⚠️ Come vanno letti questi numeri

**Nessun reperto di questo audit è stato verificato, tranne 11.** È la cosa più
importante di questa pagina e va detta prima dei contenuti.

Le 11 verifiche che hanno girato hanno confermato tutte il proprio reperto
(`07_verifiche_eseguite.md`), ma **erano tutte del dominio club**: il tasso di
conferma di quel campione non si estende agli altri cinque domini. Gli altri 53
reperti sono **misure fatte da un agente e mai attaccate da nessuno**.

Questo importa perché la fase di verifica non è decorazione. Nel disegno del
workflow era l'unica che avesse il compito di *demolire*, e il progetto ha già
pagato più volte il prezzo di una misura non contraddetta:

- un `xG = 0.00` con un gol segnato sembrava impossibile: il dato tiro-per-tiro
  mostrava un autogol. Era il **controllo** a essere cieco, non il dato (R5.1);
- il gap col mercato è stato letto al contrario **per 80 fasi**, perché
  `P(12) = 1 − P(X)` non era mai stato messo in formule (Fase 92).

Quindi: **trattare ogni reperto come un'ipotesi con un numero accanto**, non come
un difetto accertato. Il numero è ri-calcolabile (ogni reperto porta il suo
comando, e gli script stanno in `numeri/script/`); la *conclusione* no.

---

## 3 · I sei domini

| # | dominio | reperti | file |
|---|---|--:|---|
| 1 | Il normalizzatore dei nomi di club | 7 | [`01_normalizzatore_club.md`](01_normalizzatore_club.md) |
| 2 | Gli alias dei nomi di club | 12 | [`02_alias_club.md`](02_alias_club.md) |
| 3 | I casi ambigui dei nomi di club | 9 | [`03_ambigui_club.md`](03_ambigui_club.md) |
| 4 | L'identità dei giocatori | 8 | [`04_giocatori.md`](04_giocatori.md) |
| 5 | Allenatori, traghettatori, vice | 11 | [`05_allenatori.md`](05_allenatori.md) |
| 6 | Le carriere | 17 | [`06_carriere.md`](06_carriere.md) |
| | **totale** | **64** | |

Per categoria: `bug-codice` 14 · `documentazione` 13 · `finto-pieno` 11 ·
`alias-mancante` 11 · `assenza-a-monte` 8 · `ambiguità-da-decidere` 5 ·
`look-ahead` 2.

I file più chiamati in causa: `src/data/club_matching.py` (25 reperti),
`docs/DATI.md` (24), `files/sofascore_coppe_europee_2526/README.md` (13),
`tests/test_careers.py` (10).

---

## 4 · Il reperto che vale da solo il lavoro

Uno solo è stato **ri-verificato a mano dalla sessione principale**, perché tocca
il dato su cui girano i modelli:

```
Agganciatore.aggancia('Espanol') → club_id 25462 = Jove Español San Vicente
                    il club vero → club_id   714 = RCD Espanyol Barcelona
partite di La Liga con 'Espanol' nello snapshot: 266
```

È un **aggancio univoco e falso**: non ambiguo, non mancante — sicuro di sé e
sbagliato. È la categoria peggiore, perché è esattamente quella che nessun
conteggio vede: contare *quanti nomi si risolvono* dà 100%, e il 100% è vero.

Ne esiste un secondo della stessa classe segnalato dall'audit e **non ancora
verificato**: `Red Star FC` che aggancia la Stella Rossa di Belgrado, perché la
guardia `NON_AGGANCIARE` confronta la stringa grezza e le basta un suffisso «FC»
per essere aggirata.

> ✅ **ENTRAMBI RIPARATI il 13/08/2026 (Fase 154).** `Espanol` con un alias
> (`{espanol}` → `{espanyol, barcelona}`), `Red Star FC` elencando le forme
> lunghe accanto a quella corta. Misura di controllo **indipendente dalla
> stringa**, come chiede il §4: ricomposizione snapshot↔`games.csv` sulla chiave
> (data, `club_id` casa, `club_id` trasferta), **15.839 → 16.105 su 16.111**
> (98,31% → 99,96%), coppie inesistenti **272 → 6** (i 6 residui sono
> slittamenti di ±1 giorno con squadre e punteggio identici, dichiarati R4).
>
> ⚠️ E una lezione per chi riprende: la riparazione «pulita» di `Red Star FC`
> — confrontare il divieto sugli **insiemi di token** invece che sulla stringa
> — è stata provata e **ritirata**, perché su 3.339 nomi rompe due agganci
> giusti (`Athletic Bilbao`, `FC Lusitanos`): `normalizza` perde l'ordine e
> butta le sigle, e le due classi di divieto hanno bisogni opposti. Dettagli e
> test in `docs/DIARIO.md` §Fase 154.

### Perché questo cambia una frase detta lo stesso giorno

Nella stessa sessione, poche ore prima, era stato riferito che gli snapshot dei
cinque campionati erano *«153 nomi su 153, nessun problema»*. Quel 100% misurava
che ogni nome **si risolve**, non che si risolve **al club giusto**. È il terzo
finto pieno del giorno, dopo le assenze 2025-26 (colonna piena e vuota) e
`nome_smarkets` (96 valori su 96, giusto 32 volte).

**La lezione operativa, per chi riprende**: per ogni aggancio, costruire un
controllo *indipendente dalla stringa* — dedurre l'entità dalle partite (data +
avversario già agganciato + punteggio) — e contare gli agganci **sbagliati**, non
solo quelli mancanti. È una colonna che nel progetto non è mai stata contata.

---

## 5 · Cosa c'è in questa cartella

```
00_indice.md                questo file
01..06_*.md                 un file per dominio: OGNI reperto con evidenza,
                            comando che la ricalcola, riparazione proposta,
                            file da toccare e guadagno atteso — testo integrale
                            dell'agente, non riassunto
07_verifiche_eseguite.md    le 11 verifiche che hanno fatto in tempo a girare
numeri/
  diagnosi_completa.json    il payload grezzo dei 17 agenti completati: è la
                            fonte da cui i .md sopra sono GENERATI, non scritti
                            a mano (nessun numero è passato per una tastiera)
  *.json, *.csv             risultati intermedi lasciati dagli agenti
  script/  (97 file .py)    gli script che gli agenti hanno scritto per misurare.
                            Sono ciò che rende ri-calcolabili i numeri dei
                            reperti (regola Fase 15). Vivevano in una cartella
                            temporanea: senza questa copia sarebbero morti col
                            container
```

⚠️ **Cosa NON è stato copiato, e va detto** (regola 5-ter: raccogliere tutto, e
dichiarare le esclusioni): ~25 file `.pkl` e una `__pycache__` di risultati
intermedi. Sono cache rigenerabili dagli script accanto e legate alla versione di
Python, non dati originali. Se servissero, si rifanno lanciando gli script.

---

## 6 · Lo stato del repo al momento dello scatto

- **L'albero di lavoro è pulito.** L'unico agente di applicazione partito aveva
  cominciato a riscrivere `src/data/club_matching.py` (un tie-breaker `crudo()`
  più un flag `ORDINE_ALIAS_PRIMA` che ha tutta l'aria di un esperimento lasciato
  a metà) ed è stato ucciso in corsa. La modifica è **non verificata** e su un
  modulo centrale: è stata messa da parte, non applicata.

  ```bash
  git stash list     # stash@{0}: On main: apply-agent a meta', non verificato
  git stash show -p stash@{0}
  ```

- **Nessun file di dati è stato toccato.** La fase di applicazione non ha mai
  raggiunto i dati, e la regola R3 vietava comunque di modificarli a mano.

- **La suite era verde prima e resta verde**: **1.608 test**, misurati dopo lo
  scatto (`python -m pytest -q`, 6m52s). Il numero comprende i 9 test sulle
  assenze congelate aggiunti lo stesso giorno, prima dell'audit.

---

## 7 · Per chi riprende: l'ordine che consiglierei

Non è un piano approvato, è la lettura di chi ha scattato la fotografia.

1. ~~**Prima i due agganci falsi** (`Espanol`, `Red Star FC`). Sono gli unici
   reperti che sporcano il dato su cui girano i backtest, e uno dei due è già
   verificato. Tutto il resto può aspettare; questi no.~~
   ✅ **FATTO il 13/08/2026** (Fase 154) — vedi il riquadro del §4. Il punto 1
   della lista è quindi chiuso: chi riprende parte dal 2.
2. **Poi la verifica**, non l'applicazione. 53 reperti su 64 non sono mai stati
   contraddetti da nessuno, e applicare una riparazione non verificata è come
   il flag `ORDINE_ALIAS_PRIMA` rimasto nel diff: sembra lavoro fatto, ed è
   lavoro da rifare.
3. **La caccia che l'audit non ha fatto**: il conteggio degli agganci *sbagliati*
   su tutte le fonti, col metodo indipendente dalla stringa del §4. L'audit lo ha
   proposto e non ha avuto il tempo di eseguirlo su tutto.
4. **Il disegno del workflow va cambiato**, e il motivo per cui è morto è
   istruttivo: la verifica apriva **un agente per reperto** (54), e la diagnosi
   ne aveva prodotti più del previsto. Un ventaglio proporzionale a ciò che la
   fase precedente trova non ha un tetto. Verificare **per dominio** (6 agenti
   che attaccano ciascuno i propri reperti) costa un ordine di grandezza in meno
   e non perde nulla di essenziale.
