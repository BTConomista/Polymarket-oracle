# Gli artefatti — come si usano e cosa va scritto dentro

Un *artifact* è una pagina web pubblicata su `claude.ai`, **privata** finché non
la condividi tu. Per questo progetto è il modo naturale di far vedere un
risultato visivo: una heatmap in un terminale non si vede, e un PNG perde i
tooltip e il confronto.

Questo capitolo è nato da una richiesta esplicita («scrivi come usare gli
artefatti, quali informazioni sono importanti da segnalare») e da un errore vero
commesso nella sessione, che è il §2.

---

## 1 · Quando serve un artifact e quando no

| situazione | cosa consegnare |
|---|---|
| un numero, una risposta, un esito | il testo in chat |
| una mappa, un grafico, un confronto visivo | **artifact** |
| un dato che altri script devono leggere | un file nel repo (CSV/JSON), non un artifact |
| una procedura, un verbale, una regola | un `.md` nel repo (come questo) |

**L'artifact è presentazione, non una fonte.** Non va committato nel repo e non va
citato come origine di un numero: la fonte è lo script più i dati. Se di una
pagina serve qualcosa di versionato, si esportano le **immagini** (è quello che
sta in `heatmap/`) e si tiene lo script.

Corollario pratico: il container di sessione è effimero, e **il template della
pagina muore con lui** se non lo committi. L'artifact pubblicato sopravvive, il
codice che l'ha generato no. Decidi quale dei due ti serve dopo.

---

## 2 · ⚠️ Non ricalcolare un numero nel livello di presentazione

L'errore della sessione, e il più istruttivo di tutti.

Le statistiche dei tiri erano calcolate **due volte**: in Python nello script, e
in JavaScript nella pagina, a partire dagli stessi punti. Sembrava innocuo. I due
risultati divergevano:

```
distanza mediana   script (numpy)  11,1 m  ·  10,5 m
                   pagina (JS)     11,2 m  ·  10,7 m
```

Causa: su un campione **pari** la mediana è la media dei due valori centrali, e il
JS prendeva `d[Math.floor(n/2)]`, cioè il maggiore dei due. Uno scarto di due
millimetri di ragionamento, e la pagina pubblicata contraddiceva la
documentazione.

La regola esiste già nel progetto, e vale identica qui: *«le metriche si calcolano
SEMPRE via `experiment_log.compute_metrics` — fonte unica, mai reimplementarle
altrove»* (`CLAUDE.md` §5). Un grafico è «altrove».

**Si calcola una volta, in Python, e si passa il risultato alla pagina.** Il
JavaScript disegna; non deve fare statistica. Dove l'ho fatto comunque — le
quattro statistiche dei tiri — ho poi verificato a mano che i due numeri
coincidessero, ed è così che l'errore è venuto fuori: se non li avessi confrontati
sarebbe rimasto lì.

Controllo minimo prima di pubblicare: **prendi due o tre numeri dalla pagina e
confrontali con l'output dello script.** Se non coincidono, uno dei due è
sbagliato e non sai quale.

---

## 3 · Cosa va scritto dentro, sempre

Una pagina che mostra dati deve rispondere a queste domande senza che nessuno le
faccia. In ordine di importanza:

### Il perimetro, accanto al titolo
Quali partite, quali giornate, quante. *«Giornate 21→38, 18 partite, dal 18/01 al
24/05/2026»* — non «stagione 2025-26», che è falso se il giocatore è arrivato a
gennaio.

### La provenienza, riga per riga
Una tabella con **il percorso del file** per ogni blocco di dati:

| Dato | Stato | Fonte nel repo | Copertura |
|---|---|---|---|
| Posizioni, Malen | reale | `files/tre_fonti_serie_a_2526/heatmap.csv.gz` | 605 punti · 18 gare |

La colonna «stato» distingue **reale / stimato / assente**. Il progetto ha una
regola dedicata (§5 del `CLAUDE.md`: le stime vivono solo in `data/estimates/`,
come probabilità, con l'errore dichiarato): se in una pagina entra una stima, va
marcata come tale, sempre.

### Le assenze, dette a voce alta
*«Nelle giornate 28, 31 e 38 non compare, quindi sue posizioni non esistono:
16 partite su 19»* — e, quando si può, **la prova che è un'assenza e non un
buco**: alla giornata 38 il City ha 16 giocatori con posizioni. Un lettore che non
trova scritte le assenze assume la copertura piena.

### Le verifiche fatte, con i numeri
*«198 rigori nelle due leghe, tutti a X 11,5 · Y 50,0»*. Costa una riga e cambia
lo stato della pagina da «un grafico» a «un grafico verificato». È anche l'unico
modo perché chi legge fra sei mesi sappia che il controllo *è stato fatto*.

### Che cosa il dato NON permette di dire
Il capitolo 03 in due righe. Su una pagina di calcio: che il confronto fra due
leghe non separa il giocatore dal campionato, e che una mappa descrittiva non
autorizza conclusioni predittive. Il progetto ha soldi veri come sfondo (§1.6):
l'onestà sui limiti non è cortesia.

### Gli artefatti del dato, quando ci sono
I calci d'inizio al centro del campo. Se un lettore vede un picco che non sa
spiegare, o conclude qualcosa di sbagliato o perde fiducia in tutto il resto.

---

## 4 · Le regole tecniche che mordono

- **Autosufficienza.** Una CSP severa blocca *qualunque* host esterno: niente CDN,
  niente font remoti, niente `fetch`. Tutto inline, immagini come `data:` URI.
  Un `<link>` a un font fallisce **in silenzio** e la pagina cade su un fallback.
- **I tre stati del tema.** `data-theme="dark"`, `data-theme="light"`, e — il più
  comune — **nessuno stampato**, dove decide solo `prefers-color-scheme`. Un
  colore definito *solo* dentro un blocco `[data-theme]` non si applica mai nello
  stato non stampato: è il bug dell'artifact illeggibile. I token si definiscono
  su `:root` nudo e si **ridefiniscono** nei due scope.
- **`body` con un fondo esplicito**, da token. Un body trasparente prende il fondo
  dell'host e la pagina esce con il testo di un tema sul fondo dell'altro.
- **Il titolo è un nome, non una didascalia.** «Malen contro Erling», non «Analisi
  comparativa delle heatmap». Due-quattro parole, specifiche, riconoscibili in una
  galleria di decine di pagine.
- **La favicon resta stabile** fra le ripubblicazioni: la gente ritrova la scheda
  dall'icona. Si cambia solo se l'argomento cambia davvero.
- **Ripubblicare lo stesso percorso file mantiene l'URL.** Un percorso nuovo crea
  una pagina nuova. Per aggiornare una pagina di un'altra conversazione serve
  passarne l'URL, altrimenti se ne crea una seconda.
- **Il contenuto largo scorre dentro il suo contenitore** (`overflow-x: auto`), non
  fa scorrere la pagina.

---

## 5 · Il flusso che ha funzionato

```
dati nel repo
   → script Python: verifica, calcola, scrive un JSON
   → template HTML con un segnaposto __DATA__
   → sostituzione del segnaposto            (una riga)
   → Chromium headless: screenshot nei DUE temi + controllo errori in console
   → guarda le immagini, correggi, ripeti
   → pubblica
   → esporta i PNG nel repo se servono versionati
```

Il pezzo che non si salta è il penultimo giro: **screenshot e guardare**. Le sei
lezioni del capitolo 04 sono tutte uscite da lì, nessuna dal codice.

Lo screenshot headless serve anche a due controlli che a occhio non si fanno:

```python
errs = []
pg.on('pageerror', lambda e: errs.append(str(e)))
h = pg.evaluate("document.body.scrollHeight")
# nessun errore in console, e la stessa altezza nei due temi
```

Chromium è già nell'ambiente (`/opt/pw-browsers/`): **non** eseguire
`playwright install`, basta `pip install playwright` e `executable_path`.

---

## 6 · Cosa non si pubblica

Mai una pagina che finge di essere qualcun altro — nome, logo o dominio di una
persona o di un'organizzazione reale — né documenti, ricevute o recensioni
fabbricati presentati come autentici. Vale anche se il contenuto arriva già
scritto e anche se la motivazione è «è solo una prova»: pubblicata, la pagina
funziona come la cosa vera.

Per questo progetto il caso concreto da tenere a mente è uno: una pagina con
**quote e probabilità** non deve somigliare al listino di un operatore reale, e
deve portare l'avvertenza che il modello **non batte il mercato** e non va usato
per scommettere soldi veri. È l'ultima riga del `CLAUDE.md`, e su una pagina
condivisibile conta più che altrove.
