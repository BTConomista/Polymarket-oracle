# Coefficienti UEFA — federazioni e club

Consegna manuale dell'utente, **13/08/2026**. Non si scarica: il file è
`coefficienti_uefa_2026-08-12.xlsx`, come consegnato (regola 5-ter).

Fonte dichiarata nel foglio `Note`: **uefa.com**, aggiornamento
**12/08/2026 19:55** (ora italiana) —
`uefa.com/nationalassociations/uefarankings/country/` e `.../club/`.

Si legge con `src/data/ranking_uefa.py`, mai con `pd.read_excel` diretto.

```python
from src.data import ranking_uefa as ru
ru.federazioni("2025-26")   # 55 federazioni, finestra chiusa a fine 2025/26
ru.club()                   # 410 club con Paese e Coefficiente UEFA
ru.paese_dei_club()         # club_id -> paese, per i 331 agganci univoci
```

## Perché conta: è il **paese** dei club che il dataset non ha

`docs/CLUB_FUORI_PERIMETRO.md` misura che nel dataset player-scores **nessuna
colonna, in nessun file, dice di che paese è un club**: c'è solo
`domestic_competition_id`, pieno su 796 righe su 3.173 (25,1%).

Il ranking lo dice per 410 club. Agganciati al nostro registro: **331 univoci**,
20 ambigui, 59 assenti — e **168 dei 331 sono club che nel dataset non hanno un
campionato domestico**. Sono esattamente quelli su cui il dataset taceva.

⚠️ I 79 non agganciati sono in gran parte le abbreviazioni UEFA dei club **più
grandi** (`Ajax`, `Atleti`, `B. Dortmund`, `Bayern München`, `Athletic Club`):
proprio quelli per cui il ranking non ci serve, perché sono già nei nostri
campionati. Il valore sta nella coda, non in testa.

## ⚠️ R8 — un coefficiente è una fotografia con una data

Il file contiene **due finestre diverse** per le federazioni, e non sono
intercambiabili:

| foglio | finestra | decide |
|---|---|---|
| `Federazioni 2025-26` | 21/22 → 25/26 | access list **2027/28** |
| `Federazioni 2026-27` | 22/23 → 26/27 (in corso, colonna 26/27 = 0.0) | access list **2028/29** |

L'access list **2026/27**, cioè la stagione in corso, è decisa da coefficienti
chiusi a fine 2024/25 — una finestra che il file **non contiene**.

`federazioni()` non ha un default per `finestra`: sceglierne una di nascosto
sarebbe la trappola R8. Usare il coefficiente di oggi per prevedere una partita
di due anni fa è look-ahead: quel numero incorpora il risultato di quella
partita e di tutte le successive.

## ⚠️ Il coefficiente di club non misura sempre il club

Regola UEFA, dichiarata nel foglio `Note` e **verificata sul file (410/410
righe, 0 scarti)**:

```
Coefficiente UEFA = MAX( somma delle 5 stagioni ; 20% del coefficiente della federazione )
```

Il pavimento **morde su 146 club su 410 (35,6%)**: per loro il numero pubblicato
è una proprietà del **paese**, non della squadra, e mette alla pari tutti i club
della stessa federazione. `ru.pavimento_attivo()` lo dice riga per riga. Chi lo
usa come feature deve saperlo — probabilmente escluderli o trattarli a parte.

## Altri fatti dichiarati nel file

- **Punti**: 2 vittoria / 1 pareggio (1 e 0,5 nei preliminari e playoff). I
  rigori **non contano**. Bonus per la posizione nel league phase, più 1,5 punti
  per turno dagli ottavi in Champions (1 in Europa, 0,5 in Conference).
- **Federazioni**: somma dei punti di tutti i club del paese diviso il numero di
  partecipanti, sommata sulle ultime 5 stagioni. Verificato: la somma delle 5
  colonne riproduce `Punti` su **55/55** righe (il foglio ne ha 57: due sono vuote).
- **EPS** (European Performance Spots): i 2 posti extra in Champions **non**
  vanno alle prime del ranking quinquennale ma alle 2 federazioni col miglior
  coefficiente della **singola stagione precedente**. Per il 2026/27:
  Inghilterra (28,680 nel 2025/26) e Spagna (22,093).
- **Russia**: sospesa dalle competizioni UEFA dal 28/02/2022, coefficiente
  congelato.

## Stato d'uso

**Raccolto e strutturato, non usato da nessun modello.** È uno stato legittimo
(§5-ter): il paese dei club fuori perimetro è disponibile, decidere se e come
usarlo è una domanda separata.
