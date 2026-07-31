# Carriere da Wikipedia — strato 2 del database giocatori

## Licenza

Questi dati vengono dall'infobox delle voci di `en.wikipedia.org` e sono
**CC BY-SA 4.0** — attribuzione a *Wikipedia contributors*, con l'URL della
voce su ogni riga (`source_url`), e share-alike su chi li ridistribuisce.
Scelta consapevole del titolare del repo.

---

## Cosa c'è

| file | cos'è |
|---|---|
| `esiti.jsonl` | una riga JSON per giocatore **tentato** — anche i falliti. Campi: `player_id`, `nome`, `nostro`, `censurato`, `stato`, `url`, `tappe[]` |

Gli **esiti negativi sono registrati come i positivi** (principio §1.4 del
`CLAUDE.md`): senza, la sessione dopo ritenta gli stessi fallimenti.

Stati possibili: `ok` · `nessuna_pagina` (404) · `nessun_infobox` (pagina di
disambigua) · `nessun_blocco` (voce senza tabella carriera) · `errore`.

### Struttura di una tappa

| campo | significato |
|---|---|
| `ordine` | posizione nell'infobox, dall'alto |
| `club` | nome come compare su Wikipedia (⚠️ **non** normalizzato sui nostri `club_id`) |
| `anno_da`, `anno_a` | `2006–2008` → 2006, 2008. Una tappa di un anno solo ha `anno_da == anno_a` |
| `aperta` | `true` per `2026–` senza fine: tappa **in corso** |
| `presenze`, `gol` | dalle colonne `Apps` e `(Gls)` |
| `prestito` | dal marcatore `→` che Wikipedia usa per i prestiti |
| `giovanili` | `true` se la tappa sta nel blocco *Youth career*, non *Senior career* |
| `source_url`, `fonte`, `licenza` | provenienza per riga (regola R2) |

---

## Come è stato raccolto (conformità)

- **solo** pagine `/wiki/<Nome>`, verificate permesse dal `robots.txt` di ogni
  dominio usato il 31/07/2026. `/w/`, `/api/` e `/wiki/Special:` sono **vietati**
  e non vengono toccati;
- **1 richiesta al secondo**, e una **cache su disco** (`data/wikipedia_cache/`,
  non versionata) perché ogni pagina si scarichi **una volta sola** — che è la
  forma più concreta di rispetto per il server;
- User-Agent onesto e identificabile, con contatto;
- nessuna protezione aggirata, nessun captcha, nessun rate-limit forzato.

⚠️ **Trappola registrata**: `urllib.robotparser` di Python **non implementa RFC
9309** (applica *first-match-wins* invece di longest-match) e su Wikipedia
dichiara vietati percorsi che sono leciti. Le regole sono state verificate a
mano.

---

## Limiti misurati (primo lotto di 60, i censurati con più presenze)

| | |
|---|---|
| pagine risolte | **57/60 = 95%** |
| tappe estratte | 531 (9,3 a testa): **401 senior**, 130 giovanili, 67 prestiti |
| tappe senior **con presenze** | 400/401 = **99,8%** |
| tappe senior **con anno di fine** | 360/401 = **89,8%** |
| **guadagno vero**: tappe che finiscono entro il 2012, cioè **invisibili allo strato 1** | **123**, per **4.405 presenze**, su **48 dei 57 giocatori (84%)** |

**I 3 falliti sono tutti mononimi** — Koke, Pedro, Ederson: il nome nudo porta a
una pagina di disambigua. È il limite noto della risoluzione per nome, ed è
dichiarato invece che nascosto.

### Cosa NON è risolto

1. **I nomi dei club non sono normalizzati** sui nostri `club_id`. «Lech Poznań»
   qui e `club_id=124` nello strato 1 sono la stessa squadra e il codice non lo
   sa. Serve una tabella di alias — lavoro non ancora fatto.
2. **Le presenze di Wikipedia non sono confrontabili con le nostre**: contano
   solo il campionato nazionale, mentre `appearances.csv` conta tutte le 48
   competizioni. **Non vanno sommate fra loro.**
3. **La grana è l'anno, non la data**: una tappa `2008–2010` non dice il giorno.
   Per la regola **R8** questo significa che il taglio a una certa data è
   **approssimato all'anno** — e va usato come tale, non come una data esatta.
4. **Mononimi e omonimi**: la risoluzione è per nome, quindi un omonimo può
   essere agganciato al giocatore sbagliato. Non è stato ancora quantificato.

---

## Un bug trovato dai test, e vale la pena raccontarlo (31/07/2026)

Il primo lotto aveva **7 tappe con `anno_da = 0`**. Non era un errore di lettura:
il template dell'infobox di Wikipedia usa **`0000` come segnaposto quando
l'anno di inizio è ignoto**, e lo rende letteralmente così:

```
['0000 –2000', 'TPK']        ← Lukas Hradecky, settore giovanile
```

È un **finto pieno da manuale (regola R6)**: uno zero che *sembra* una misura e
significa «non lo so». Lasciarlo passare avrebbe prodotto carriere iniziate
nell'anno zero e lunghe due millenni — e **nessun controllo di completezza lo
avrebbe visto**, perché la cella è piena e il numero è un intero valido.

Casi trovati: Hradecky, Handanovic, Schöne, Insigne, Joe Hart, Papastathopoulos,
Sansone — tutte tappe giovanili.

**Corretto**: `0000` → `None`. E un test lo presidia (`anno_da == 0` non deve
esistere), perché è il tipo di difetto che rientra in silenzio.

> **Come è saltato fuori**: non da un'ispezione, ma da un test che chiedeva
> `anno_da >= 1900`. È l'argomento a favore dei test sui **range fisici** dei
> dati, non solo sulla loro forma: il tipo era giusto, il valore no.
