# Protocollo di studio del match prima del fischio — v0 (BOZZA, da rifinire insieme)

> Questo file istruisce **come si studia una partita prima del calcio d'inizio** con i
> nostri modelli. È una **bozza v0**: le parti fondate sui risultati (Fasi 0-41) sono
> marcate con la fase; le decisioni ancora aperte sono marcate **🔲 DA DECIDERE
> INSIEME**. Non è un invito a scommettere: allo stato attuale i modelli **non hanno
> un edge dimostrato** sui mercati efficienti (ROI value-betting 1X2 −15%, Fase 15).

---

## 0. Principio guida (non negoziabile)

Il valore **non** è "la mia probabilità > quella del book". È **sapere quando fidarsi
di quel divario**. Nella stragrande maggioranza dei casi la risposta disciplinata è
**"passa"**. Il protocollo serve a filtrare i pochissimi casi in cui c'è motivo di
agire — e a impedirci di inseguire i nostri stessi errori (adverse selection, Fase 20:
dove dissentiamo di più dal mercato, sbagliamo di più).

---

## 1. Dati da raccogliere prima del match (input)

| dato | a cosa serve | fase |
|---|---|---|
| **Quote 1X2 + Over/Under 2.5** (di apertura e/o correnti) | invertirle nei λ,μ del mercato → market-implied (il nostro miglior modello per ~tutti i mercati) | 26/41 |
| Quote dei mercati **Tier 1** che il book offre (GG/NG, risultato esatto, multigol, total-squadra, clean sheet, handicap…) | check di **incoerenza interna** del book vs le sue 1X2+O/U | 41 + demo Roma-Fiorentina |
| **Squadre** (nomi canonici) | fit del DC (fallback senza quote) | 1 |
| **Classifica pre-partita + giornate rimaste** | stato `stakes` (decisa/in corsa) → mismatch motivazione | 31/32 |
| Note su **formazioni/infortuni** dell'ultimo minuto (se disponibili) | informazione NUOVA che il modello storico non ha | 4c/20 |

**Nota onesta:** le quote di **chiusura** sono lo stimatore più efficiente; se
studiamo il match ore prima, lavoriamo su quote più morbide (apertura) — è lì che un
edge, se esiste, è più probabile (Fase 14: ma il modello non batteva nemmeno
l'apertura sull'1X2).

---

## 2. Quali modelli, per quali mercati (esito Fase 41)

- **Con le quote 1X2+O/U → market-implied per TUTTI i mercati Tier 1** (vince su
  19/20, Fase 41), **+ φ(|λ−μ|) della Fase 35/39 sulla famiglia-pareggio** (1X2 draw,
  risultato esatto in diagonale, doppie chance con pari).
- **Senza quote → Dixon-Coles gol+xG** (config ufficiale `src/config.py`), come stima
  indipendente. Meno affidabile del mercato sull'1X2 (gap +0.0165), ma è tutto ciò che
  abbiamo a priori.
- **NON serve un modello bespoke per ogni mercato** (Fase 41: converge tutto sul
  market-implied). L'unica variante utile è la φ35 sui pareggi.

Comando pratico: `python scripts/predict.py <casa> <ospite> --odds H D A OVER UNDER`
→ mostra Modello 1 (DC) e Modello 2 (market-implied) su tutti i mercati.

---

## 3. Regole di selezione — quando (eventualmente) agire

Ogni regola nasce da un risultato; nessuna è un edge dimostrato. **Default: non
scommettere.** Si considera un mercato SOLO se supera il filtro relativo.

### 3.1 Pareggio nelle partite equilibrate (il lead più promettente, Fase 40)
- **Condizione:** `|λ − μ| < 0.5` (partita equilibrata) **E** la nostra P(pari) (con
  φ35) **> P(pari) del mercato**.
- **Perché:** il mercato sotto-prezza i pari equilibrati (Fase 35: 0.296 vs reale
  0.332); su quelle partite battiamo la sua calibrazione, e il ROI storico è **+4.7%**
  (Fase 40). **MA non concluso** (CI [−4.9%, +14.4%], alta varianza).
- **Anti-regola (fondamentale):** se `|λ − μ| ≥ 0.5` **NON** scommettere il pari anche
  se sembra "valore" — su match sbilanciati il nostro eccesso-pari è il nostro errore
  (Fase 40; visto su Roma-Fiorentina: pari 25.8% vs 22.6% del book = trappola).

### 3.2 Incoerenza interna del book (Tier 1 soft)
- **Condizione:** su un mercato esotico (risultato esatto, multigol, total-squadra,
  GG/NG…), la **linea del book** diverge dalla probabilità **implicita nelle sue
  stesse 1X2+O/U** (market-implied) oltre una soglia, **E** l'EV al netto del margine
  è positivo.
- **Perché:** i book prezzano i mercati soft con meno cura; l'incoerenza è valore che
  non richiede di battere la "verità", solo la loro stessa linea principale.
- **Stato:** meccanismo dimostrato (demo Roma-Fiorentina, GG −1.6% ma sotto il
  margine). Serve il **tool di scansione incoerenza** (da costruire) per sistematizzarlo.

### 3.3 Mismatch di motivazione (fine stagione, Fase 31/32)
- **Condizione:** una squadra **decisa** (già salva/retrocessa/campione) contro una
  **in corsa**, nelle ultime giornate.
- **Stato:** segnale reale ma non concluso (n piccolo); il GBM lo cattura meglio del
  DC. Da usare al più come **filtro di cautela** (non fidarsi della nostra linea su
  quei match), non come bet attivo.

### 3.4 Cosa NON fare mai (imparato a caro prezzo)
- **Value bet sulla vittoria casa/trasferta** (ROI −19.6% / −12.9%, Fase 40): sono i
  nostri errori. Il mercato ci batte sull'1X2 d'esito.
- Scommettere dove **dissentiamo molto** dal mercato senza una delle regole sopra
  (adverse selection, Fase 20: gap ∝ dissenso).

---

## 4. Gestione del rischio e staking 🔲 DA DECIDERE INSIEME

Domande aperte su cui serve la tua decisione:
- **Bankroll** e frazione massima per singola scommessa (flat? Kelly frazionato?).
  *Raccomandazione tecnica:* flat o Kelly molto frazionato (¼), vista l'incertezza
  (nessun edge provato).
- **Soglia di edge minima** per agire (es. EV netto > X%).
- **Soglia di incoerenza** per §3.2.
- **Numero massimo di bet per giornata / esposizione totale.**
- **Stop-loss / criteri di revisione** (dopo quante giornate rivalutiamo?).
- **Quali mercati Tier 1** vogliamo davvero giocare all'inizio (io suggerirei: solo
  §3.1 pareggio-equilibrio, in prova, a stake minimo, per raccogliere dati reali).

---

## 5. Workflow operativo (checklist per ogni match)

1. Raccogli gli input (§1): quote 1X2+O/U, quote Tier 1 offerte, classifica.
2. `python scripts/predict.py casa ospite --odds …` → market-implied + DC su tutti i
   mercati.
3. Calcola `|λ − μ|` (equilibrio) e lo stato `stakes` delle due squadre.
4. Applica i filtri §3 **in ordine**; per default **nessun bet**.
5. Se un filtro scatta: calcola l'**EV al netto del margine** alla quota offerta; se
   positivo e sopra soglia (§4), è un candidato.
6. **Registra tutto** (match, quote, decisione, motivazione, esito) — anche i "no bet":
   è l'unico modo per validare prospetticamente i lead non conclusi (Fase 40).
7. Post-match: aggiorna il registro con l'esito e il P&L teorico.

---

## 6. Cosa manca (per rendere questo protocollo operativo davvero)

- [ ] **Tool di scansione incoerenza** book vs market-implied su tutti i Tier 1 (§3.2).
- [ ] **Registro prospettico** delle selezioni (§5.6) per validare §3.1 su dati nuovi.
- [ ] **Raccolta quote** (apertura + Tier 1) — non è nei dati storici; serve una fonte
  live/prospettica.
- [ ] Decisioni di §4 (staking, soglie, bankroll).
- [ ] (Futuro) modello di **timing gol** → mercati sui tempi + fondazione in-play
  (Tier 3), l'avversario più morbido.

---

*Bozza v0 — aggiornare insieme. Ogni regola operativa deve restare ancorata a una fase
del [DIARIO](DIARIO.md) e, quando possibile, a un ROI/CI reale, non a un'intuizione.*
