# 2. Bundesliga 2025-26 — la seconda divisione che ha l'Opta

Consegna 18/08/2026, due zip (la raccolta + `Eventi_Opta` a parte per il peso).
**310 partite, 18 squadre**: 34 giornate da 9 (306) più i **4 spareggi**
promozione/retrocessione. Fonti **due**: SofaScore e WhoScored — ma qui,
a differenza di LaLiga2, **l'Opta c'è**.

```python
from src.data import tre_fonti as tf
tf.squadre("bundesliga2", periodo="Totale")                  # 612 squadra-partita
tf.squadre("bundesliga2", periodo="Totale", spareggio=True)  # 620, con gli spareggi
tf.eventi_opta("bundesliga2")                                # 460.190 eventi con X/Y
```

| blocco | righe | note |
|---|--:|---|
| `squadre` | 1.918 | 1.864 di partita + 54 di classifica |
| `giocatori` | 12.857 | 12.358 di partita + 499 di rosa, **due fonti** |
| `eventi` | 93.886 | **sette** categorie, `Cronaca` compresa |
| `eventi_opta` | 460.190 | 306 partite, 39 tipi, coordinate e qualificatori |
| `heatmap` | 461.520 | 310 partite |
| `legenda` | 479 | documenta **450 colonne su 450** |

⭐ **È la raccolta più piena delle sedici**: 450 colonne e **sei** vuote in
tutto. Il contrasto con LaLiga2 (38 vuote) ha una causa sola — lì WhoScored
non copriva e le sue colonne restavano previste-e-vuote, qui copre davvero.

---

## Il confronto con LaLiga2, che è la cosa più utile da leggere

Le due consegne sono arrivate lo stesso giorno, sono entrambe seconde divisioni,
e si comportano in modo opposto su quasi tutto. Da qui la regola generale:
**niente si eredita fra raccolte, nemmeno fra raccolte gemelle.**

| | LaLiga2 | 2. Bundesliga |
|---|---|---|
| Understat | assente (non copre) | assente (non copre) |
| Opta di WhoScored | **assente** | **presente, 306/310** |
| `Cronaca` | assente (404 su 468/468) | **presente** (306/310) |
| categorie di `eventi` | 6 | 7 |
| colonne vuote | 38 | **6** |
| `Evento` da due fonti | sì (gol raddoppiati) | no (61 righe WhoScored, solo spareggi) |
| turni fuori-giornata | playoff **interno** alla lega | spareggi con **squadre estranee** |
| squadre con / senza | 22 / 22 | **20 / 18** |
| supplementari giocati | nessuno | **1 partita** |

**Understat non copre nemmeno questa**, e la verifica è la stessa a tre vie:
menu del sito con sei sole leghe di prima divisione, sei varianti di URL tutte
a 404, e le pagine squadra che per il 2025 servono un altro anno — o
addirittura **un'altra competizione**: Hamburger SV risponde 2025/26 ma di
*Bundesliga*, dove nel frattempo è stato promosso. È la stessa trappola R6
vista in Spagna, con un grado di insidia in più.

**Le 4 partite senza Opta sono gli spareggi**, e la spiegazione è quella già
misurata in LaLiga2: le loro pagine WhoScored pesano **~100 KB contro ~1 MB**
delle altre, cioè non hanno match centre. Due consegne diverse, stesso criterio,
stesso numero — è così che un controllo positivo diventa una regola invece che
un aneddoto. Su quelle 4 resta `initialMatchDataForScrappers`: **61 righe** di
evento dentro `eventi`, così anche gli spareggi hanno una seconda fonte sui
fatti contabili.

---

## ⚠️⚠️ `eventi_opta.Squadra`: 14 nomi su 18, il caso peggiore mai visto

La colonna `Squadra` di `eventi_opta` usa la forma corta di WhoScored mentre
`Casa`/`Trasferta` dello stesso file usano quella lunga. Non è una novità — è la
**quinta** occorrenza — ma la progressione dice che va misurata sempre:

| raccolta | squadre colpite |
|---|---|
| La Liga | 1 su 20 (5%) |
| Bundesliga | 1 su 18 (6%) |
| Supercoppa UEFA | 2 su 2 (100%) |
| **2. Bundesliga** | **14 su 18 (78%)** |

L'aggancio per **partita** resta perfetto anche senza riparazione, ed è per
questo che il difetto non si rivela da solo.

⭐ **La mappa non è stata costruita per somiglianza.** `eventi_opta` porta sulla
stessa riga il nome corto (`Squadra`), il lato (`Campo`) e i nomi lunghi
(`Casa`/`Trasferta`): l'accoppiamento è **letto dal dato**, e verificato che
ogni nome corto corrisponda a **uno e un solo** nome lungo su tutte e 460.190
le righe.

⚠️ E qui la somiglianza avrebbe fallito per davvero, non per ipotesi: la
traslitterazione tedesca dell'umlaut **espande** la vocale invece di toglierla —
`Fürth`→`Fuerth`, `Düsseldorf`→`Duesseldorf`, `Nürnberg`→`Nuernberg`,
`Münster`→`Muenster`. Uno script che *toglie* gli accenti produce `Furth` da un
lato e lascia `Fuerth` dall'altro: le due forme **si allontanano** invece di
avvicinarsi. È lo stesso errore del `Deportivo de A Coruña`→`La Coruna` di
LaLiga2 (galiziano contro castigliano), trovato lo stesso giorno in un'altra
lingua — due occorrenze indipendenti, che è il minimo per chiamarla una regola.

⚠️ **`Darmstadt` è mappato al contrario di proposito.** Le altre tredici vanno
corto→lungo perché il lungo poi passa da `TEAM_ALIASES` e arriva alla forma
dello snapshot (`VfL Bochum 1848`→`Bochum`). Per Darmstadt quel secondo
passaggio non esiste, quindi si mappa il **lungo** verso il canonico
(`Darmstadt 98`→`Darmstadt`, il nome con cui il club sta nello snapshot
Bundesliga, dove ha giocato nel 2023-24). Non si possono avere entrambe le
direzioni: `_normalizza_squadre` applica la mappa **una volta sola**, non fino a
punto fisso, e i due lati si scambierebbero di posto.

---

## ⭐ La partita che ha fatto scattare il tripwire sul punteggio

`SC Paderborn 07 – VfL Wolfsburg`, 25/05/2026, spareggio di ritorno: **2-1, di
cui 1-0 ai supplementari**. È la **prima partita di un campionato**, in tutte le
raccolte, ad andare oltre il 90'.

La guardia `gol_sono_regolamentari()` verificava `Gol = 1T + 2T`, e la sua
docstring prevedeva per iscritto esattamente questo caso: *«se una consegna
futura contenesse i tempi supplementari … l'identità salterebbe pur essendo il
dato giusto»*. La previsione era esatta — ma il caso **era già arrivato** e
nessuno se n'era accorto, perché il test che copriva la Champions (l'unica coppa
coi supplementari giocati) **si era riscritto l'identità a tre addendi per conto
proprio** invece di chiamare la funzione. Risultato: la guardia dichiarava
«punteggio sporco» su **10 righe di Champions e 32 di Europa League** di dati
sani, e il test accanto passava verde.

Ora l'identità è a tre addendi (`Gol = 1T + 2T + suppl.`) e vale **310/310** qui,
562/562 in Champions, e continua a saltare dove deve: sulle 6 partite di
Conference il cui `Gol` contiene davvero la lotteria dei rigori.

**La lezione, che vale oltre questa funzione: un test che ri-scrive la regola
invece di chiamarla non testa la regola.** Verifica i dati e lascia il codice
scoperto — e siccome passa, sembra che copra entrambi.

---

## Le altre cose da sapere

**Niente snapshot.** `data/bundesliga2_matches.csv` non esiste e la 2.
Bundesliga non è in `LEAGUE_CONFIGS`. Al posto dell'aggancio valgono i controlli
interni: i gol degli eventi ricostruiscono il punteggio su **620 squadra-partita
su 620** (903 gol, 26 autogol, 74 rigori) e l'identità dei tempi regge 310/310.

**Gli spareggi tirano dentro due squadre estranee** — Rot-Weiss Essen (3. Liga)
e VfL Wolfsburg (Bundesliga) — quindi **18 squadre nel campionato e 20 con gli
spareggi**. È il caso *opposto* a LaLiga2, dove il playoff è interno alla lega e
le squadre restano 22 in entrambi i casi. Stessa etichetta, ragioni diverse:
qui escluderli per default è la ragione storica di `E_CAMPIONATO`, non una
convenzione.

**`Periodo` ha due valori nuovi**: `1° supplementare` e `2° supplementare`, 2
righe ciascuno — solo quella partita. Chi cicla sui periodi assumendo i tre
soliti li trova.

**Le due fonti concordano quasi sempre**: 19 righe di squadra su 1.836
confrontabili (1%) e 110 di giocatore su 12.198 (1%). Squadre: passaggi 12,
tiri 7, corner 5, falli 1. ⭐ E **non c'è il falso positivo sul possesso**: la
colonna `possession % (normalizzato) (WhoScored)`, introdotta a monte con la
consegna della Bundesliga, è presente anche qui — zero token `possesso` nella
colonna `Discordanze`, contro 760 righe su 760 nelle prime tre leghe.

**Il rating lo pubblicano entrambe le fonti** (9.335 righe confrontabili,
r=0,80, scarto medio 0,36 punti): concordano sull'ordine, **non** sul livello.
Riferimento SofaScore, WhoScored come controllo — **non mediare**. L'xG invece
lo pubblica solo SofaScore, quindi non c'è nulla da confrontare.

**`Meteo (WhoScored)` è quasi vuota**: 12 righe su 1.918 (0,63%). È il quarto
stato misurato di quella colonna — 0,0% Serie A, 0,3% Liga, 98,4% Premier — e il
motivo per cui `copertura()` torna uno stato invece di un booleano.

**Da SofaScore i dati fisici** (km percorsi, alta intensità, sprint, velocità
massima), **da WhoScored** altezza, peso ed età dei giocatori: le due fonti
portano cose diverse, non le stesse due volte.

**La sfida antibot di SofaScore (2026)**: senza l'header `X-Captcha` la
paginazione **si tronca in silenzio**. Fatto operativo, non un difetto dei dati.
