# Playbook — come si producono le previsioni prospettiche

> **Cos'è questo file.** La **procedura**, scritta una volta e riusabile: come si
> producono previsioni su partite non ancora giocate, in modo che il confronto
> fra modelli diversi voglia dire qualcosa e che nessuno possa barare — nemmeno
> per distrazione.
>
> **A cosa serve oltre all'oggi.** È scritto per essere riusato **così com'è**
> per la Fase 2 (quando arriveranno i modelli con i dati per giocatore), per
> **altri campionati** e per **altre competizioni** (coppe nazionali, UEFA).
> Cambia cosa si mette dentro; la procedura no.
>
> **Da dove nasce.** Richiesta dell'utente (12/08/2026), nella sessione in cui
> ha consegnato i calendari 2026-27 e proposto l'orizzonte mobile e
> l'automazione. Il piano che lo inquadra è
> [`docs/CHIUSURA_FASE_1.md`](CHIUSURA_FASE_1.md); l'elenco di cosa prevedere è
> [`docs/REGISTRO_VARIANTI.md`](REGISTRO_VARIANTI.md).
>
> **Stato**: procedura DEFINITA, **produttore non ancora scritto**.

---

## 1 · Le quattro parole che servono

Tutto il resto del file usa queste, e solo queste.

| parola | significato |
|---|---|
| **il produttore** | l'unico programma che produce previsioni. Prende una *variante*, un elenco di partite e una data-limite, e scrive righe in un registro |
| **variante** | una configurazione: quale modello e con quali costanti (es. «Dixon-Coles con emivita 180»). Le ~300 varianti stanno in `REGISTRO_VARIANTI.md` |
| **orizzonte** | quante giornate avanti si prevede. Orizzonte 3 = questa partita è prevista quando mancano 3 giornate |
| **congelamento** | il momento in cui una previsione viene scritta e committata. Dopo, non si tocca più |

### Perché UN produttore e non uno per variante

È il punto che regge tutto il resto.

> Se ogni variante ha il suo script, e lo script numero 47 ha per distrazione un
> taglio dei dati diverso di un giorno, la variante 47 produrrà numeri diversi
> dalle altre. E a fine stagione, davanti alla classifica, **non sarà possibile
> dire se ha vinto perché il modello è migliore o perché il suo script era
> sbagliato**.

Un solo produttore significa: stessi dati, stesso taglio, stessa derivazione
dei mercati, stesso formato. Una differenza in uscita può venire da una cosa
sola — la variante. **Non è una questione di comodità: è la condizione perché
il confronto esista.**

---

## 2 · Le tre regole che non si negoziano

### R-P1 · Non si prevede ciò che è già successo

Il produttore **rifiuta di scrivere** una previsione per una partita il cui
calcio d'inizio è già passato, e rifiuta di usare nei dati di addestramento
partite successive alla data-limite dichiarata.

⚠️ Non è una precauzione teorica: è l'errore che rende belli i numeri e muto il
difetto. Un modello che ha visto il risultato sembra bravissimo, e a stagione
finita non è più ricostruibile che cosa avesse visto. La protezione va **nel
codice**, non nella disciplina di chi esegue: chi esegue è distratto alle 2 di
notte, il codice no.

### R-P2 · Ogni riga dice da dove viene

Ogni previsione porta con sé: **variante**, **commit git** che l'ha prodotta,
**impronta della configurazione**, **data-limite dei dati** (`as_of`),
**orizzonte**, e — per le leghe diverse dalla Serie A — **origine della
costante** (fittata qui, pooled, o copiata dalla Serie A).

Senza, fra otto mesi una riga di numeri è un numero e basta.

### R-P3 · Il commit è la prova

Una previsione vale **solo** se il commit che la scrive precede il calcio
d'inizio. Il registro non è credibile perché lo diciamo noi: è credibile perché
la data del commit è verificabile da chiunque.

Corollario: **si committa subito**, non a fine giornata. Una previsione giusta
ma committata dopo il fischio è carta straccia.

---

## 3 · L'orizzonte mobile

### Come funziona

Con orizzonte **K = 5**:

| momento | si prevedono |
|---|---|
| prima dell'inizio | giornate 1 … 5 |
| giocata la 1 | si **ri**-prevedono 2 … 5 (ora coi dati della 1) e si aggiunge la 6 |
| giocata la 2 | si ri-prevedono 3 … 6 e si aggiunge la 7 |
| … | la finestra scorre fino a fine stagione |

Ogni partita riceve così **fino a K previsioni**, a distanze diverse dal
fischio.

### Il regalo: la curva dell'orizzonte

Le K previsioni della stessa partita misurano **quanto migliora la previsione
avvicinandosi**. È la stessa domanda che il progetto ha studiato sulle quote
(apertura → chiusura, Fasi 14/52-quinquies/98) ma **sul nostro modello**, e non
è mai stata fatta.

### ⚠️ Quale previsione conta per il verdetto: UNA

Per dire se una variante è brava conta **solo l'ultima** previsione di ogni
partita — quella a orizzonte 1.

Se si contassero tutte e K, ogni partita peserebbe K volte, e non sono K
informazioni indipendenti: è la stessa partita guardata K volte. Gli intervalli
di confidenza verrebbero **falsamente stretti** e ogni conclusione sarebbe
sovra-sicura.

Le altre K−1 sono uno studio **separato e dichiarato** (la curva dell'orizzonte).

### Quanto vale K

K=5 è la proposta dell'utente ed è ragionevole: copre circa un mese, che è
l'orizzonte oltre il quale le formazioni e le condizioni cambiano troppo.
**Non è una costante sacra**: se un giorno si volesse misurare la curva più in
là, si alza — e si dichiara da quale giornata.

---

## 4 · Che cosa si salva

### La regola: i parametri, non i prodotti

Tutti i mercati Tier 1 (1X2, Over/Under, GG/NG, doppie chance, total-squadra,
clean sheet, multigol, risultato esatto…) sono **funzioni deterministiche** di
pochi numeri: i gol attesi λ e μ, più ρ e le costanti della variante. Quindi si
salvano quelli, e i mercati si ricostruiscono quando servono.

Il conto che rende la regola necessaria:

```
300 varianti × 1.752 partite × 26 mercati × 5 orizzonti  =  68.328.000 righe
300 varianti × 1.752 partite ×  1 riga    × 5 orizzonti  =   2.628.000 righe
```

Da svariati gigabyte a ~40 MB compressi. In un repo git la prima non ci sta.

### Il controllo che rende la regola sicura

Per il **modello ufficiale** si salva **anche** il listino completo dei 26
mercati. Un test verifica che ricostruirlo dai parametri dia gli stessi numeri.
Se un giorno la ricostruzione divergesse, il test lo dice — invece di lasciarci
scoprire a maggio che tutte le varianti tranne una erano ricostruite male.

⚠️ **Eccezione da dichiarare**: alcune varianti applicano correzioni *dopo* la
matrice (temperature scaling, ricalibrazione per classe). Quelle non sono
riassunte da λ e μ: per loro si salva anche il vettore di correzione, oppure il
listino intero. La regola non è «sempre i parametri»: è «i parametri quando
bastano, e si dichiara quando non bastano».

---

## 5 · La procedura, passo per passo

### Passo 0 — una volta per competizione

1. **Calendario completo** (chi gioca contro chi, in quale giornata). Le date
   possono essere provvisorie: servono gli accoppiamenti.
2. **Fonte degli orari veri.** Le date dei calendari pubblicati si spostano —
   nel 2026-27 il 93,8% era dichiarato provvisorio. La verità operativa è il
   listino del mercato.
3. **Aggancio dei nomi**: ogni squadra del calendario deve risolvere a un nome
   canonico del progetto. ⚠️ Distinguere **alias** (`Manchester City` →
   `Man City`) da **squadra nuova** (`Coventry`): confonderli darebbe al
   Manchester City il prior delle neopromosse.
4. **Neopromosse dichiarate, non dedotte.** `promoted_teams()` sulla stagione
   precedente dà le promosse dell'anno *scorso* (Fase 128).
5. **Elenco delle varianti** da produrre, in `REGISTRO_VARIANTI.md`.

### Passo 1 — a ogni giro

1. Leggi il calendario e trova le giornate nella finestra dei prossimi K turni
   non ancora giocati.
2. Per ognuna, prendi gli **orari veri** dal listino di mercato (non dal
   calendario).
3. Per ogni variante del registro, per ogni giornata della finestra: se la
   previsione a quell'orizzonte **non esiste già**, producila.
4. Data-limite dei dati = il calcio d'inizio della partita (§7, decisione D-P1).
5. Scrivi in coda al registro, con la provenienza di R-P2.
6. **Committa prima del primo fischio** della giornata più vicina.

### Passo 2 — dopo il fischio finale

1. Raccogli i risultati.
2. Calcola le metriche **solo** via `experiment_log.compute_metrics` — mai
   reimplementate (§5 del `CLAUDE.md`).
3. Aggiorna lo stato in `REGISTRO_VARIANTI.md`.
4. A verdetto maturo, aggiorna **`docs/PANCHINA.md`**, che resta la fonte
   canonica dello stato scientifico.

---

## 6 · L'automazione

Il repo ha già workflow di GitHub Actions che girano da soli. Il produttore ne
aggiunge uno.

**Cadenza: una volta al giorno.** Legge il calendario, verifica se qualche
giornata dei campionati seguiti è entrata nella finestra, produce le previsioni
mancanti, committa.

⚠️ **Il controllo anti-look-ahead sta nel produttore, non nel workflow.** Se
stesse nel workflow, un lancio a mano lo salterebbe — ed è proprio a mano che si
lancia quando si va di fretta.

⚠️ **Il workflow non deve mai riscrivere una previsione esistente.** Solo
aggiungere. Se una riga per (variante, partita, orizzonte) c'è già, si salta:
una previsione ri-scritta dopo aver visto qualcosa non è più una previsione.

Fatti già pagati sull'infrastruttura di questo repo, da tenere presenti:
il cron parte con **30-40 minuti di ritardo** rispetto all'orario dichiarato
(Fase 142), e GitHub tiene **un solo** run in coda: il terzo cancella il
pending. Per un giro giornaliero nessuno dei due morde, ma vanno saputi prima
di infittire la cadenza.

---

## 7 · Le decisioni di disegno, e il loro stato

| # | decisione | stato |
|---|---|---|
| **D-P1** | data-limite dei dati: per **partita** o per **lega-giornata**? | ⏳ **aperta**. La Fase 129 scelse per lega-giornata, motivandola sul solo decadimento dei pesi (0.5^(2/365) = 0.996, fattore comune). L'argomento però **non copre le partite mancanti**: con un turno spalmato su più giorni, la partita del lunedì non vedrebbe quelle del sabato. Per la giornata 1 le due scelte coincidono |
| **D-P2** | orizzonte K | proposto **5**, da confermare |
| **D-P3** | cosa conta per il verdetto | **l'ultima previsione**, orizzonte 1 (§3) |
| **D-P4** | cosa si salva | **parametri**, listino intero per il modello ufficiale (§4) |
| **D-P5** | quante varianti a orizzonte pieno | proposta: **tutte** a orizzonte 1; orizzonte pieno solo per il modello ufficiale e le 8 varianti prioritarie di `CHIUSURA_FASE_1.md` §4 |

---

## 8 · Riuso: aggiungere una competizione o una fase nuova

La procedura non cambia. Cambiano tre cose, ed è utile sapere **quali**:

| cosa cambia | come |
|---|---|
| **il calendario** | serve quello della nuova competizione. Per le coppe c'è in più il tabellone a eliminazione: la «giornata» diventa il turno, e chi gioca il turno successivo non si sa in anticipo — l'orizzonte mobile si accorcia da solo |
| **i dati ammessi** | per la Fase 2 entrano giocatori, formazioni, allenatori. ⚠️ Vale identica la regola **R8**: un dato si può usare solo se era noto **prima** del fischio. Le formazioni ufficiali escono un'ora prima — sono ammissibili, ma spostano il momento del congelamento |
| **le costanti** | per una lega nuova **non si copiano** quelle della Serie A. Si producono due varianti, `X_costante_SA` e `X_ritarata`, e si lascia decidere al fuori campione (`docs/PLAYBOOK_NUOVA_LEGA.md`) |

Ciò che **non** cambia mai: le tre regole di §2, l'orizzonte mobile, il fatto
che conti solo l'ultima previsione, e che ci sia **un solo produttore**.

---

## 9 · Errori già pagati, da non ripetere

| errore | dove | costo |
|---|---|---|
| costanti di una lega applicate a un'altra | `predict.py` fino alla Fase 92 | +0.0025 di log-loss 1X2 in Premier, pareggio previsto +2.7pp |
| neopromosse **dedotte** invece che dichiarate | versione precedente del congelamento | il Málaga tirato verso la media di lega invece che verso δ — il difetto opposto a quello giusto (Fase 128) |
| fidarsi che un file esista senza guardarci dentro | 31/07/2026 | il listino esisteva, pesava 120 KB e non conteneva La Liga (Fase 127) |
| date prese da un calendario pubblicato | 11/08/2026 | 93,8% dichiarate provvisorie; la giornata 1 di Liga era spalmata su 5 giorni contro 1 |
| un controllo scritto in fretta fuori dagli strumenti testati | 09-10/08/2026 | due falsi allarmi in un giorno: `max` invece di `min` sulle distanze dal fischio |

---

**Ultimo aggiornamento**: 12/08/2026 · **Stato**: procedura definita, produttore
da scrivere · **Decisioni aperte**: D-P1, D-P2.
