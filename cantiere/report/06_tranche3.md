# Report 6 — Tranche 3: il playbook sulle leghe nuove (passi 2-5)

Dati pronti e verificati (report 1 e 3), correzioni applicate (report 5): qui si
mette alla prova il modello. Tutto con il protocollo di sempre — walk-forward,
metriche dalla fonte unica, bootstrap appaiato B=10.000, **aspettativa dichiarata
prima** di guardare i numeri.

---

## Passo 2 · Tracer bullet: il Dixon-Coles **così com'è** sulle leghe nuove

Config Serie A senza ritoccare nulla (emivita 365g, shrinkage 1.5, blend xG
α=0.75, δ=0.23), walk-forward settimanale, 6 stagioni di test (2020-21 →
2025-26). Le **cinque** leghe girate con la stessa finestra e lo stesso codice,
così il confronto è pulito.

**Aspettative dichiarate prima:** il DC batte la baseline; **non** batte il
mercato, con gap atteso +0.015…+0.021.

| lega | partite | 1X2 modello | baseline | mercato | **gap vs mercato** | CI95 |
|---|--:|--:|--:|--:|--:|---|
| serie_a | 2.280 | 0.9797 | 1.0849 | 0.9632 | **+0.0165** | [+0.0107, +0.0225] |
| premier_league | 2.280 | 0.9831 | 1.0695 | 0.9623 | **+0.0207** | [+0.0138, +0.0275] |
| la_liga | 2.280 | 0.9843 | 1.0689 | 0.9681 | **+0.0162** | [+0.0103, +0.0225] |
| **bundesliga** | 1.836 | 0.9919 | 1.0722 | 0.9738 | **+0.0181** | [+0.0109, +0.0253] |
| **ligue_1** | 2.058 | 1.0041 | 1.0750 | 0.9851 | **+0.0190** | [+0.0121, +0.0258] |

**Controllo che vale più di tutto il resto:** il gap che misuro in Serie A è
**+0.0165**, identico alla quarta cifra a quello pubblicato dal progetto
(CLAUDE.md §6: «gap 1X2 +0.0165 in Serie A»). Non l'ho preso da lì: esce dalla
mia pipeline, con i miei snapshot e il mio codice di valutazione. È la prova che
l'intero apparato — dati, percorsi, metriche — riproduce i numeri noti.

**Esito.** Entrambe le aspettative si avverano su entrambe le leghe nuove:

- il DC **batte la baseline** in modo conclusivo (guadagno +0.0803 Bundesliga,
  +0.0709 Ligue 1; CI95 lontani da zero);
- il DC **non batte il mercato**, e il gap cade **dentro la forchetta prevista**
  (+0.0181 e +0.0190 contro +0.015…+0.021 attesi). Nessuna sorpresa: il modello
  trasferisce, il tetto informativo pure.

Sull'Over/Under lo stesso quadro (Bundesliga 0.6553 modello vs 0.6459 mercato;
Ligue 1 0.6863 vs 0.6730).

---

## Passo 2b · Tracer market-side: le costanti del mercato, lega per lega

Non serve il modello: bastano chiusura e risultati. Sette stagioni per lega
(2019-20 → 2025-26, tutte quelle con chiusura O/U reale), ogni parametro
fittato **leave-one-season-out**.

| lega | margine book | θ (sotto-disp.) | tilt λ | tilt μ | φ0 | ROI pari-equilibrio |
|---|--:|--:|--:|--:|--:|--:|
| serie_a | 4.87% | 1.232 | −0.028 | +0.026 | 0.2433 | +3.15% |
| premier_league | 4.27% | 1.085 | −0.024 | +0.009 | 0.0341 | −3.82% |
| la_liga | 4.75% | 1.242 | −0.002 | −0.007 | 0.2461 | +1.90% |
| **bundesliga** | 4.76% | **1.080** | +0.019 | +0.022 | **0.1827** | +5.04% |
| **ligue_1** | 5.02% | **1.103** | −0.010 | +0.022 | **0.0000** | −7.82% |

*(tilt: correzione log dei livelli, 0 = mercato centrato; ROI: pareggio dove
|λ−μ| < 0.5, soglia fissa)*

### Tre esiti

**1. La previsione dichiarata prima si avvera.** Dall'EDA (report 3 §6) avevo
scritto, prima di qualunque fit: *«in Ligue 1 aspettarsi φ0 ≈ 0; in Bundesliga un
φ0 piccolo e positivo»*. Misurato: **Ligue 1 φ0 = 0.0000** (la lega si comporta
da «inglese»: nessun deficit-pareggio), **Bundesliga φ0 = 0.183** (positivo,
a metà tra il mondo latino e quello inglese). È una predizione registrata in
anticipo e verificata, non una lettura a posteriori.

**2. L'aspettativa del playbook «θ decresce con la liquidità» NON regge.** Era
scritta come lezione acquisita (*«più il book è liquido, meno c'è da spremere»*).
Le due leghe nuove la contraddicono:

- la **Ligue 1** ha il margine **più alto** del campione (5.02%, il book meno
  competitivo) e θ **basso** (1.103);
- la **Bundesliga** ha un margine da Serie A (4.76% vs 4.87%) e θ da Premier
  (1.080 vs 1.085).

Correlazioni sulle 5 leghe: corr(θ, margine) = **+0.299** — il segno è *opposto*
a quello previsto, e con n=5 nessuna delle due è conclusiva. Ma l'ipotesi
«liquidità» non spiega i dati: quello che li spiega è un'altra cosa (punto 3).

**3. θ e φ0 viaggiano insieme: sono due descrizioni dello stesso fenomeno.**
corr(θ, φ0) = **+0.755** sulle 5 leghe. Ha senso: un θ > 1 (gol sotto-dispersi
rispetto alla Poisson) produce *più pareggi e meno punteggi estremi* di quanto
la matrice del mercato preveda — esattamente ciò che φ(|λ−μ|) corregge in modo
mirato. Le due leghe «latine» hanno entrambi alti (θ ≈ 1.24, φ0 ≈ 0.245); le due
«inglesi» entrambi bassi. La Bundesliga è l'unico caso intermedio (θ basso, φ0
medio) — ed è il posto giusto dove indagare se si vorrà separare i due effetti.

**4. L'edge non si replica: 5 leghe su 5.** Il ROI pari-equilibrio non è
conclusivo in nessuna lega (tutti i CI95 attraversano lo zero), Bundesliga
compresa nonostante il +5.04% di stima puntuale. La lezione del progetto
(«la struttura trasferisce, l'edge no») regge anche sulle leghe 4 e 5.

---

## Passo 4 · Il motore market-implied sulle leghe nuove

Inversione della chiusura 1X2+O/U nei tassi (λ, μ) → matrice DC (ρ = −0.06, **non**
ri-tarato) → prezzo di ogni mercato Tier 1. Confronto con il DC-da-gol (gli stessi
(λ, μ) prodotti dal modello walk-forward) e con la baseline in-sample. Finestra:
6 stagioni (2020-21 → 2025-26).

**Aspettativa dichiarata prima:** il market-implied batte il DC-da-gol su ~13/14
mercati (la matrice è universale: 3/3 leghe finora).

**Risultato: 15/15 su entrambe le leghe nuove.** Superata.

| lega | partite | batte il **DC-da-gol** | batte la **baseline** |
|---|--:|--:|--:|
| serie_a | 2.280 | 14/15 | 14/15 |
| premier_league | 2.280 | 14/15 | 14/15 |
| la_liga | 2.280 | 15/15 | 14/15 |
| **bundesliga** | 1.836 | **15/15** | 14/15 |
| **ligue_1** | 2.058 | **15/15** | 14/15 |

Le due leghe nuove sono, se possibile, il caso **migliore** del campione: il
motore le prezza meglio di quanto prezzi Serie A e Premier. Guadagno più grande
sul risultato esatto (+0.0283 Bundesliga, +0.0364 Ligue 1), più piccolo sul
pari/dispari (+0.0002 e +0.0000).

L'unico mercato dove la baseline vince è, in entrambe le leghe, il
**pari/dispari**: coerente con la lezione già registrata dal playbook («il
pari/dispari non si predice in nessuna lega», 4 repliche), che con queste due
leghe arriva a **sei**. Non prezzarlo con pretese.

---

## Passo 5 · La leva φ(|λ−μ|) sulla famiglia-pareggio

Riprezzatura con `price_markets(phi0, kappa)`, parametri fittati
**leave-one-season-out** (mai in-sample).

**Aspettativa dichiarata prima:** Ligue 1 φ0 = 0 → nessun guadagno; Bundesliga
φ0 ≈ 0.18 → guadagno possibile ma piccolo.

| lega | φ0 LOSO | 1X2 senza φ | 1X2 con φ | guadagno | verdetto |
|---|---|--:|--:|--:|---|
| serie_a | 0.235 – 0.370 | 0.9642 | 0.9628 | +0.00135 [−0.0010, +0.0038] | nel rumore |
| premier_league | 0.000 – 0.026 | 0.9622 | 0.9623 | −0.00014 [−0.0003, +0.0000] | nel rumore |
| la_liga | 0.198 – 0.423 | 0.9688 | 0.9685 | +0.00031 [−0.0016, +0.0023] | nel rumore |
| **bundesliga** | 0.175 – 0.334 | 0.9747 | 0.9735 | +0.00122 [−0.0016, +0.0040] | nel rumore |
| **ligue_1** | 0.000 – 0.130 | 0.9850 | 0.9854 | −0.00036 [−0.0008, +0.0001] | nel rumore |

*(I φ0 di questa tabella sono fittati sulle 6 stagioni di questo passo; quelli
del passo 2b — 0.183 e 0.000 — sulle 7 stagioni con chiusura O/U reale. Finestre
diverse, stessa storia: positivo in Bundesliga, nullo in Ligue 1.)*

Stesso esito su `draw`, `dc_1x`, `dc_2x`: nessun CI conclusivo.

**Lettura.** In **Ligue 1** l'esito è quello previsto e va scritto come chiusura:
φ35 **non serve** (φ0 fittato ≈ 0, guadagno nullo o leggermente negativo). In
**Bundesliga** il segno è giusto e la grandezza plausibile, ma con 1.836 partite
il CI non conclude: la leva resta **in panchina**.

**E un risultato scomodo che va detto:** su questo percorso — market-implied,
finestra 6 stagioni, parametri leave-one-season-out — φ35 **non è conclusiva in
nessuna delle cinque leghe**, Serie A compresa (+0.00135, CI [−0.0010, +0.0038]),
dove pure φ0 si fitta stabilmente fra 0.235 e 0.370. Non è una smentita della
leva (nel progetto è documentata su percorsi e finestre diverse, e il **segno**
qui è quello giusto in tutte le leghe «latine»): è la constatazione che, con
~2.000 partite per lega, il guadagno atteso di 1-1.5 millesimi di log-loss è
**sotto la soglia di risoluzione** del test. Chi vorrà promuoverla deve o
allargare la finestra o cambiare metrica, non ri-fittare gli stessi dati.

---

## Passo 3 · Ri-taratura per-lega ⏳ (in corso)

---

## La rosa dei modelli, per le due leghe nuove

Sintesi in stile `docs/PANCHINA.md` — cosa è **titolare**, cosa resta in
**panchina**, cosa è **chiuso**, sulla base dei test di questa tranche.

| leva / modello | Bundesliga | Ligue 1 | perché |
|---|---|---|---|
| **market-implied** (chiusura 1X2+O/U → matrice) | ⚽ **titolare** | ⚽ **titolare** | batte il DC-da-gol su 15/15 mercati Tier 1 |
| **DC gol+xG** (config Serie A) | ⚽ titolare *come fallback* | ⚽ titolare *come fallback* | batte la baseline in modo conclusivo, non il mercato (gap +0.018 / +0.019): esattamente il ruolo che ha nelle altre leghe |
| **φ(\|λ−μ\|)** sulla famiglia-pareggio | 🪑 panchina | ❌ non serve | Bundesliga: segno giusto, CI non conclusivo; Ligue 1: φ0 = 0, la lega non ha deficit-pareggio |
| **dp / θ del router** | 🪑 panchina | 🪑 panchina | θ misurato 1.080 / 1.103: sopra 1 ma molto sotto Serie A e Liga; da testare come leva solo dopo il passo 3 |
| **ROI pari-equilibrio** | ❌ chiuso | ❌ chiuso | non conclusivo, come nelle altre 3 leghe |
| **pari/dispari** | ❌ chiuso | ❌ chiuso | la baseline vince: sesta replica della lezione |

---

## Cosa si porta a casa

1. **Il modello trasferisce, di nuovo.** Cinque leghe, stessa finestra, stesso
   codice: il DC batte sempre la baseline e non batte mai il mercato, con un gap
   in una forchetta stretta (+0.0162…+0.0207). Non c'è nulla di speciale nella
   Serie A, e non c'è nulla di rotto nelle leghe nuove.
2. **Il motore market-implied è ancora più forte fuori dall'Italia** (15/15 in
   Liga, Bundesliga e Ligue 1 contro 14/15 in Serie A e Premier).
3. **Una lezione del playbook va riscritta.** «θ decresce con la liquidità» non
   regge al test su 5 leghe; quello che regge è che **θ e il deficit-pareggio
   sono la stessa cosa vista da due angoli** (corr +0.755).
4. **Una previsione fatta prima si è avverata** (φ0 = 0 in Ligue 1), il che dà
   fiducia al metodo dell'EDA come strumento di *pronostico* e non solo di
   descrizione.
5. **Nessun edge nuovo.** Come sempre: la struttura viaggia, i soldi no.
