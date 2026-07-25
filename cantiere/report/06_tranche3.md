# Report 6 — Tranche 3: il playbook sulle leghe nuove (passi 2-5)

Dati pronti e verificati (report 1 e 3), correzioni applicate (report 5): qui si
mette alla prova il modello. Tutto con il protocollo di sempre — walk-forward,
metriche dalla fonte unica, bootstrap appaiato B=10.000, **aspettativa dichiarata
prima** di guardare i numeri.

*(Le sezioni contrassegnate ⏳ sono in corso e verranno completate.)*

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

| | Bundesliga | Ligue 1 |
|---|--:|--:|
| partite | 1.836 | 2.058 |
| market-implied batte il **DC-da-gol** | **15/15** | **15/15** |
| market-implied batte la **baseline** | 14/15 | 14/15 |
| guadagno più grande (risultato esatto) | +0.0283 | +0.0364 |
| guadagno più piccolo (pari/dispari) | +0.0002 | +0.0000 |

L'unico mercato dove la baseline vince è, in entrambe le leghe, il
**pari/dispari** — quinta replica consecutiva della lezione «il pari/dispari non
si predice in nessuna lega». Non prezzarlo con pretese.

---

## Passo 5 · La leva φ(|λ−μ|) sulla famiglia-pareggio

Riprezzatura con `price_markets(phi0, kappa)`, parametri fittati
**leave-one-season-out** (mai in-sample).

**Aspettativa dichiarata prima:** Ligue 1 φ0 = 0 → nessun guadagno; Bundesliga
φ0 ≈ 0.18 → guadagno possibile ma piccolo.

| lega | φ0 LOSO | 1X2 senza φ | 1X2 con φ | guadagno | verdetto |
|---|---|--:|--:|--:|---|
| bundesliga | 0.175 – 0.334 | 0.9747 | 0.9735 | +0.00122 [−0.0016, +0.0040] | nel rumore |
| ligue_1 | 0.000 – 0.130 | 0.9850 | 0.9854 | −0.00036 [−0.0008, +0.0001] | nel rumore |

Stesso esito su `draw`, `dc_1x`, `dc_2x`: nessun CI conclusivo.

**Lettura.** In **Ligue 1** l'esito è quello previsto e va scritto come chiusura:
φ35 **non serve** (φ0 fittato ≈ 0, guadagno nullo o leggermente negativo). In
**Bundesliga** il segno è giusto e la grandezza plausibile, ma con 1.836 partite
il CI non conclude: la leva resta **in panchina**, promuovibile solo con più
dati (o con la finestra a 7 stagioni). Nessuna delle due entra nella
configurazione operativa.

---

## Passo 2 · Tracer bullet del Dixon-Coles ⏳

## Passo 3 · Ri-taratura per-lega ⏳
