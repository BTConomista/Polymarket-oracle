# La procedura, in sette passi

Vale per qualunque giocatore delle due leghe con la raccolta a tre fonti. I passi
1-3 non si saltano: sono i controlli che rendono il resto affidabile.

---

## 1 · Verifica le convenzioni PRIMA di calcolare

Due controlli indipendenti, entrambi in `verifica_convenzioni()`:

```python
# scala: il dischetto del rigore e' sempre a X 11,5 · Y 50,0
rig = tiri[tiri.Situazione == "penalty"]
assert abs(rig.X.mean() - 11.5) < 0.2 and abs(rig.Y.mean() - 50.0) < 0.2

# verso: la X media deve CRESCERE da portiere ad attaccante
medie = hm.assign(Ruolo=hm.Giocatore.map(ruoli)).groupby("Ruolo")["X"].mean()
assert medie.reindex(["G", "D", "M", "F"]).is_monotonic_increasing
```

Lo script **esce con errore** invece di produrre numeri, se uno dei due fallisce.
È deliberato: un'analisi che si ferma costa cinque minuti, una che gira sbagliata
costa la conclusione.

## 2 · Seleziona per ID, non per nome

```python
sel = df[df["ID giocatore"] == 839956]        # ✅
sel = df[df.Giocatore.str.contains("Haaland")] # ❌ due giocatori diversi
```

Se parti dal nome, controlla che porti a un ID unico e **fermati se non lo fa**.

## 3 · Filtra la fonte dei tiri

```python
tiri = ev[(ev.Categoria == "Tiro") & (ev.Fonte == "SofaScore")]
```

Senza il secondo filtro i tiri sono il doppio. SofaScore perché è la fonte che
produce anche la heatmap: posizioni e tiri restano nella stessa convenzione.

## 4 · Definisci la finestra, e dichiara le assenze

La giornata si estrae dal `Turno`:

```python
hm["gio"] = hm.Turno.str.extract(r"(\d+)")[0].astype(int)
hm = hm[hm.gio >= 20]        # seconda meta'
```

Poi **conta i buchi dentro la finestra**, perché non tutti sono uguali:

```
ID [839956]   463 posizioni su 16 partite
giornate: 20-37 (16 presenze)
  ⚠️ senza posizioni dentro la finestra: giornate [28, 31]
```

⚠️ Nota come si legge: lo script segnala i buchi **dentro** l'intervallo che ha
osservato, cioè 20-37. La giornata **38 non compare affatto**, e per questo non è
elencata: le assenze in coda a una finestra sono invisibili a un controllo di
questo tipo. Il conto vero è 16 presenze su 19 giornate possibili — 28, 31 e 38 —
e per accorgersi della terza bisogna confrontare con il **calendario**, non con i
dati del giocatore.

Un buco può essere il giocatore che non è entrato oppure la raccolta che manca.
Si distinguono guardando **se gli altri ci sono**: alla giornata 38 il
Manchester City ha 16 giocatori con posizioni e Haaland no → è un'assenza sua,
non un difetto del dato. Questo controllo va fatto, non assunto.

## 5 · Densità: liscia per la forma, conta grezza per i numeri

Due griglie, due scopi diversi, e **non** si confondono:

```python
# forma: istogramma fine + lisciamento gaussiano, normalizzato sul PROPRIO massimo
H, _, _ = np.histogram2d(X, Y, bins=[120, 80], range=[[0, 100], [0, 100]])
G = gaussian_filter(H, sigma=(4.5, 4.5), mode="constant"); G = G / G.max()

# numeri: zone grosse a conteggio GREZZO — sono queste che si citano
C, _, _ = np.histogram2d(X, Y, bins=[6, 4], range=[[0, 100], [0, 100]])
```

`sigma=4.5` su una griglia 120×80 significa un raggio di lisciamento di circa
**4 metri**: abbastanza per non vedere il singolo punto, poco per non spostare i
picchi. `mode="constant"` evita che la densità rimbalzi sui bordi e gonfi
artificialmente le fasce laterali.

⚠️ **Il valore di una cella lisciata non è una quantità interpretabile.** Non si
mette in un tooltip e non si cita: è una densità relativa, normalizzata su un
massimo arbitrario. I numeri che si dicono a voce alta escono da `C`.

## 6 · Normalizza per il tempo, separatamente

Le due mappe sono ognuna normalizzata sul proprio massimo: confrontano le
**forme**, non le intensità. Per l'intensità serve un numero a parte:

```
Malen  605 punti / 1.478' = 36,8 posizioni per 90'
Erling 463 punti / 1.312' = 31,8 posizioni per 90'
```

Senza questo, due mappe affiancate suggeriscono che i due giocatori tocchino il
pallone la stessa quantità di volte, che non è mai vero.

## 7 · Salva i parametri, non le immagini

Lo script scrive un JSON con la griglia, le zone grezze, le zone derivate e i
tiri. Da lì si ridisegna qualunque cosa. È lo stesso criterio del
`PLAYBOOK_PREVISIONI` (§ *si salvano i parametri, non i 26 mercati*): il
contenuto informativo sta nei numeri, non nel PNG.

---

## Il perimetro dove questo vale

| lega | posizioni | note |
|---|---|---|
| Serie A 2025-26 | ✅ 556.996 | `files/tre_fonti_serie_a_2526/` |
| Premier League 2025-26 | ✅ 573.203 | `files/tre_fonti_premier_league_2526/` |
| La Liga 2025-26 | ✅ 570.768 | `files/tre_fonti_la_liga_2526/` |
| Bundesliga · Ligue 1 | ❌ | statistiche per partita sì, coordinate no |
| coppe nazionali | ❌ | formazioni ed eventi sì, coordinate no |
| coppe UEFA | ⚠️ solo tiri | `files/sofascore_coppe_europee_2526/tiri.csv.gz`, senza heatmap |

⚠️ **Questa tabella invecchia.** È stata riscritta due volte in un'ora mentre il
quaderno veniva scritto — la Premier è entrata, poi La Liga. Prima di fidartene,
guarda quali cartelle `files/tre_fonti_*_2526/` esistono davvero:

```bash
ls -d files/tre_fonti_*_2526/
```

Lo script funziona su qualunque lega abbia quella cartella, **senza modifiche**:
verificato su La Liga al primo colpo, compreso il caso di un difensore centrale
(Pau Cubarsí, 3,1% nel terzo offensivo e 0,7% in area — che è la controprova che
la pipeline non è tarata sugli attaccanti).

Sulle coppe europee esistono i **tiri** con coordinate ma non le posizioni: un
confronto lì è una mappa dei tiri, che è un'altra cosa e va chiamata col suo
nome.
