# ⚠️ DATI DI PROVA — non sono dati del progetto

Quote in-play di **campionati che il progetto NON modella**: Brasile, MLS,
Argentina, Messico, seconde divisioni estere, qualunque cosa Smarkets stesse
quotando in quel momento.

## Perché esistono

Per un motivo **tecnico**, non modellistico: provare l'infrastruttura di
raccolta **anche nelle ore in cui il nostro perimetro non gioca**.

Misurato il 09/08/2026: il nostro perimetro (5 campionati + coppe + UEFA +
seconde divisioni) copre **3-7 ore al giorno**; tutto il calcio ne copre
**5-14**. Senza queste partite, metà delle ore del giorno non le proveremmo
mai — e i guasti che capitano di notte li scopriremmo la prima notte in cui
contano davvero.

## Come sono raccolte

- **riempiono, non aggiungono**: si prendono solo fino al tetto di 25 partite
  in contemporanea, che è il carico misurato di una nostra giornata piena. Se
  il nostro perimetro gioca già, qui non finisce niente;
- stesso raccoglitore, stessa cadenza, stesso formato di
  `data/smarkets_live/` — è il punto: se fossero raccolte diversamente non
  proverebbero la stessa cosa;
- `fascia` vale sempre **`prova`**, e `lega` è lo **slug grezzo** di Smarkets
  (`brazil-serie-a`, `us-major-league-soccer`…): non hanno una chiave nostra
  perché non sono nel nostro perimetro.

## Cosa NON fare con questi dati

**Non usarli per addestrare o valutare un modello**, e non unirli a
`data/smarkets_live/`. Non perché siano sporchi — sono dati di mercato veri,
raccolti nello stesso modo — ma perché:

1. sono un **campione di comodo**, scelto in base a *quando l'infrastruttura
   aveva bisogno di lavorare*, non in base a una domanda. Chi li usasse
   starebbe selezionando le partite in un modo che non sa descrivere;
2. non abbiamo per queste squadre **niente** di ciò che serve: né snapshot
   storici, né risultati, né anagrafica dei nomi;
3. il tetto di 25 li rende **incompleti per costruzione** — in un'ora con
   quaranta partite ne prendiamo venticinque, e quali dipende dall'ordine
   dell'API.

## Perché allora si conservano

Regola §5-ter del progetto: *«quando una fonte offre un dato, lo si prende,
anche se oggi non serve»*. Sono prezzi in-play veri di partite vere, e non si
ri-scaricano dopo. Un giorno potrebbero servire — per esempio a chiedersi se
la sotto-dispersione dei gol (θ, Fase 51) si comporta allo stesso modo fuori
dai cinque campionati. Fino ad allora sono **raccolti e non usati**, che è uno
stato legittimo e dichiarato (`docs/DATI.md`).
