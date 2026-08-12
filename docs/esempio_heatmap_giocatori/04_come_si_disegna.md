# Come si disegna — sei lezioni, tutte viste a schermo

Nessuna di queste è stata dedotta: ognuna è un difetto che è comparso in uno
screenshot e che è stato corretto. La regola che le genera tutte è una:
**renderizza e guarda**, perché un validatore controlla i colori e non la
geometria.

---

## 1 · La rampa sequenziale si INVERTE col tema ⚠️ la più grave

Prima versione: rampa blu chiaro → blu scuro, uguale nei due temi. In chiaro
funzionava. In scuro **l'encoding era invertito**: la zona più densa diventava un
blu notte che sparisce nel fondo scuro, e le zone vuote — blu chiarissimo —
erano le più luminose e attiravano l'occhio.

Il numero che lo spiega, contrasto contro il campo:

| | campo chiaro `#e6eaf0` | campo scuro `#21262e` |
|---|--:|--:|
| passo più chiaro `#cde2fb` | 1,10:1 | **11,49:1** |
| passo più scuro `#0d366b` | **9,90:1** | 1,27:1 |

La densità massima deve stare sul passo con **più contrasto rispetto al proprio
fondo**. Quindi: chiaro→scuro su fondo chiaro, scuro→chiaro su fondo scuro. Non è
un'inversione cosmetica, è ciò che tiene l'encoding leggibile.

E poiché la direzione dipende dal tema, **il tema che cambia va intercettato** o
la mappa resta girata:

```js
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', render);
new MutationObserver(render).observe(document.documentElement,
  { attributes: true, attributeFilter: ['data-theme'] });
```

## 2 · Interpola la rampa, non fare i gradini

Prima versione: 13 passi discreti, scelti con `Math.floor(t * n)`. Risultato:
**fasce concentriche da carta topografica**, che sembrano curve di livello e
suggeriscono soglie che nei dati non esistono.

La densità è continua, il colore deve esserlo: si interpola linearmente fra due
passi adiacenti.

```js
const x = t * (stops.length - 1), i = Math.floor(x), f = x - i;
return stops[i].map((c, k) => Math.round(c + (stops[i+1][k] - c) * f));
```

## 3 · L'aspetto del `viewBox` deve combaciare col contenitore

Con `preserveAspectRatio="none"` e un `viewBox` verticale (45×60) dentro un
contenitore orizzontale (105:68), i cerchi dei tiri diventavano **ellissi**. Su
una mappa dei tiri l'area del cerchio codifica l'xG: deformarla falsifica la
codifica.

Il controllo, che costa una riga e va automatizzato:

```js
const b = document.querySelector('#box circle').getBoundingClientRect();
b.width / b.height   // deve essere 1
```

## 4 · Ritaglia il campo sui dati

La mappa dei tiri copriva 40 metri di profondità con metà immagine vuota. Il tiro
più lontano dei due insiemi è a **28,6 m**: il frame è stato portato a 30 e i
punti hanno guadagnato metà dello spazio.

E l'orientamento convenzionale di una mappa dei tiri è **verticale con la porta
in alto**, non orizzontale: è come le leggono tutti, e va rispettato.

## 5 · Il tooltip dice il conteggio grezzo, non la cella lisciata

Su una heatmap lisciata il valore della cella è una densità relativa
normalizzata: non è interpretabile e non va mostrata. Il tooltip mostra invece la
zona grossa a **conteggio vero**:

> **13,4%** delle posizioni · trequarti · centro-destra · 81 punti su 605

Ventiquattro zone di hover invisibili sopra la mappa, con `tabindex` perché
funzionino anche da tastiera.

## 6 · Due giocatori = due rampe a una tinta, non una rampa a due tinte

Confrontando due mappe serve un colore per giocatore. La tentazione è una scala
divergente o un arcobaleno; entrambe sbagliate, perché qui non c'è una polarità e
non c'è un punto neutro. Sono **due contesti sequenziali distinti**, ognuno con la
propria tinta unica: blu per Malen, arancio per Erling.

Entrambe le rampe verificate **monotòne in luminanza** — condizione perché una
scala sequenziale sia leggibile come «di più / di meno»:

```
blu     : 0.743 0.633 0.537 0.369 0.239 0.145 0.080 0.056 0.038
arancio : 0.761 0.619 0.490 0.382 0.278 0.220 0.165 0.112 0.065
```

Lo stesso colore identifica poi il giocatore **in tutta la pagina** — barre,
pallini, legende: il colore segue l'entità, mai il suo posto in classifica.

---

## Il campo, in unità reali

Disegnare il campo in metri (105×68) invece che in unità normalizzate rende le
marcature gratuite e giuste:

```
area di rigore   16,5 m di profondità, 40,32 di larghezza  (y 13,84 → 54,16)
area piccola      5,5 × 18,32                             (y 24,84 → 43,16)
dischetto        11 m dalla linea di porta, centrato
cerchio di metà   raggio 9,15
```

E la conversione dai dati, una volta sola, in due funzioni:

```js
const PX = x => x / 100 * 105;   // heatmap: 0 porta propria → 100 avversaria
const PY = y => y / 100 * 68;
```

---

## Le due cose da controllare sempre, prima di consegnare

1. **Apri la pagina e guardala**, nei due temi. Gli errori di questo capitolo
   sono tutti invisibili nel codice e ovvi a schermo.
2. **Verifica che non ci siano errori in console** e che l'altezza della pagina
   sia la stessa nei due temi (se differisce, qualcosa non ha reso).
