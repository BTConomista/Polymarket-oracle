# Playbook — come si aggiunge (e si studia) una lega nuova

Questo file è la **procedura operativa** per portare il progetto su un
campionato nuovo (Bundesliga, Ligue 1, Eredivisie…). Distilla il metodo
effettivamente seguito per Premier League e La Liga (Fasi 53-57 dati/tracer/
ri-taratura; Fasi 79-80 studio dedicato e leve per-lega) e le regole date
dall'utente: *studiare a fondo i dati prima di modellare, provare gli STESSI
modelli su ogni lega, farsi dire dai backtest quali costanti divergono, e
tenere sempre aggiornati diario/registri/rose*. Chi apre questo file davanti a
una lega nuova deve poter procedere senza reinventare nulla.

Regola madre (CLAUDE.md §7): **le formule sono universali, i numeri no.**
Una lega nuova è una modifica di *configurazione* (voce in `LEAGUE_CONFIGS`,
`sources.LEAGUES`, alias), mai di codice del modello.

---

## Passo 0 — Procurare e congelare i dati

1. **Fonti**: risultati+quote in formato football-data.co.uk e xG Understat,
   stesse stagioni delle leghe esistenti (oggi 2017-18 → 2025-26). Se il
   proxy blocca le fonti: bundle JSON caricati dall'utente in `files/`
   (pattern Fase 53) o workflow GitHub Actions d'import (pattern Fase 67,
   dettagli nel MANUALE_SOPRAVVIVENZA).
2. **Snapshot congelato**: `scripts/build_league_snapshot.py` → 
   `data/<lega>_matches.csv` versionato, stesso schema 38-colonne delle altre
   leghe (offline-first, §5 del CLAUDE.md).
3. **Riconciliazione nomi (il bug classico)**: estrarre TUTTI i nomi squadra
   da ENTRAMBE le fonti e verificarli **per identità** (mai per ordinamento);
   alias in `sources.TEAM_ALIASES`. Attenzione ai club omonimi (Ath/Atletico/
   Real Madrid). Obiettivo: **copertura xG 100%, zero righe orfane**; i test
   anti quasi-duplicato devono passare.
4. **Dati ausiliari** (pattern Fasi 59-60): calendario completo di club
   (coppe+Europa → `rest_days_full`, `midweek_europe`), `squad_value`
   (player-scores), assenze. Semantica quote apertura/chiusura: SOLO colonne
   `*C*` genuine come chiusura (regola Fase 73).
5. **Aggiornare `docs/DATI.md`** (catalogo dati) con coperture e semantica; i
   buchi noti (es. chiusura O/U 2017-19) valgono anche per la lega nuova.

## Passo 1 — Conoscere la lega PRIMA di modellare (EDA)

Due batterie standard, entrambe già scriptate (adattare la lista `LEAGUES`):

- **EDA base** (pattern Fase 55, `_run_fase55_eda.py`): esiti H/D/A, gol,
  Over%, γ=ln(casa/ospite), Var/Media, δ=ln(gol_lega/gol_promosse), autocorr
  delle forze, corr xG-gol, margine book, edge mercato vs baseline.
- **EDA struttura** (pattern Fase 79, `_run_fase79_eda_pl_liga.py`):
  1. **pareggio per fascia di equilibrio** (reale−mercato per quartile di
     |pH−pA| devig) → dice subito se la lega è "latina" (deficit-pareggio,
     come SA/Liga) o "inglese" (assente/invertito);
  2. **congestione** (riposo ≤3g, dicembre, midweek europeo);
  3. **γ_t per stagione** (stabilità del vantaggio-casa, crollo COVID).

**Output obbligatorio**: la sezione della lega nel quaderno di studio (oggi
`docs/STUDIO_PREMIER_LIGA.md`; con 4+ leghe valutare un file per lega) e la
**riga nella tabella «differenze in un colpo d'occhio»** (§3-bis dello
studio), con la colonna "universale?" compilata. Run EDA in `runs.jsonl`.

## Passo 2 — Tracer bullet (il modello COSÌ COM'È)

Prima di ritarare qualsiasi cosa (§1.1 e §1.3 del CLAUDE.md):

- **DC config Serie A** (o della lega più simile) walk-forward sulla lega
  nuova (pattern Fase 56): deve battere la baseline; misurare il gap col
  mercato (aspettativa: +0.015…+0.021, più largo dove il book è più liquido).
- **Tracer market-side** (pattern Fase 53, niente port del DC): θ
  (sotto-dispersione), tilt λ/μ, draw-bias w_D/w_A, ROI pari-equilibrio.
  Aspettativa: θ>1 ma decrescente con la liquidità; i bias sfruttabili
  probabilmente NON si replicano (finora mai successo).

## Passo 3 — Ri-taratura per-lega degli iperparametri DC

Una leva alla volta (§1.2), le altre ferme al default (pattern Fase 57):

- **δ neopromosse**: SEMPRE ricalcolato, `δ = ln(ḡ_lega/ḡ_promosse)` — è
  l'unico iperparametro finora davvero per-lega (SA 0.23, PL 0.33, Liga
  0.22). Si adotta per motivazione strutturale anche con CI non conclusivo
  (precedente: Fasi 7/17/57).
- **emivita / shrinkage / α blend**: griglia minima {365,730} × {1.5,3} ×
  {0.75}. Aspettativa: **curve piatte** (successo su 3/3 leghe: il tetto è
  informativo). Se una lega desse curve NON piatte sarebbe una scoperta: 
  documentarla a fondo prima di adottare.
- **γ vantaggio-casa NON si tara**: lo fitta il DC dai dati.
- Nuova voce in `LEAGUE_CONFIGS` con blocco 📐 per ogni numero (§2-bis).

## Passo 4 — Il motore market-implied sulla lega

- **Multi-mercato dalla chiusura** (pattern Fase 76): l'inversione
  1X2+O/U → (λ,μ) → matrice → 20 mercati Tier 1, **senza ritarare ρ=−0.06**.
  Aspettativa: batte il DC-da-gol su ~13/14 (la MATRICE è universale, 3/3
  leghe finora). Se non accade, fermarsi e capire (probabile problema dati).
- **MAI copiare le costanti di AFFINAMENTO**: θ del router, dp_lvl, φ35,
  nudge stagionale sono **per-contesto** (lega × epoca — Fasi 53/75/79/80).
  Ognuna va rifittata leave-future-out sulla lega, con **aspettativa
  dichiarata PRIMA** e il FIT stesso trattato come risultato (esempi: φ0=0.00
  in Premier = il deficit-pareggio non esiste; boost-38ª 0.915 in Liga = il
  profilo di fine stagione è invertito).

## Passo 5 — Le leve della rosa, cella per cella

La matrice di `docs/PANCHINA.md` ha una colonna per la lega nuova: ogni cella
`⬜` è un test potenziale. Ordine di priorità:

1. leve **titolari** del motore nelle altre leghe (φ35 famiglia-pareggio,
   router) — decidono la configurazione operativa della lega;
2. leve in **panchina** la cui promozione è condizionata a "riappare su
   un'altra lega" (es. catena GG/NG, voce #1);
3. covariate/ricalibrazioni a costo zero (colonne già nello snapshot).

Per ogni test: config ufficiale per-lega, walk-forward (default 6 stagioni di
test), bootstrap appaiato B=10.000, regola CI95<0, prior dall'EDA dichiarato
prima. **L'esito atteso più comune è la bocciatura** (Fase 79: 4/4 bocciate;
Fase 80: 1 leva su 3 leghe) — va scritta comunque, vale quanto un successo.

## Le finestre di backtest (stagioni): come sceglierle

- **Training**: più storia è meglio, sempre (Fase 25: tagliare peggiora;
  l'emivita 365g gestisce già la recency). Non escludere nemmeno il COVID.
- **Test standard**: 6 stagioni (oggi 2021→2526) — abbastanza potenza, e
  CONFRONTABILE con tutti i numeri storici del progetto.
- **Estendere**: si può risalire fin dove i dati reali reggono (1920 per
  tutto ciò che usa la chiusura O/U — Fase 73; 1718 per la sola apertura/1X2,
  come Fase 75). Più stagioni = più potenza sui CI, MA epoche diverse
  (porte-chiuse, θ che cresce nel tempo): dichiarare sempre la finestra e non
  mischiare confronti a finestre diverse.
- **Ridurre** (solo recenti): lecito per domande "com'è OGGI la lega", ma i
  CI si allargano — non trarre conclusioni forti da <3 stagioni (§1.7).
- Nei confronti CROSS-lega usare **finestre identiche** per tutte le leghe
  (come la Fase 80: 1920→2526 per tutte e tre, Serie A rifatta apposta).

## Cosa aspettarsi (le lezioni già pagate, da non ricomprare)

1. **La struttura trasferisce, l'edge no** (Fasi 53-57): DC e market-implied
   funzionano ovunque; sotto-dispersione sfruttabile, dp_lvl, draw-bias sono
   idiosincrasie della lega (finora: solo Serie A, il mercato meno liquido).
2. **Più il book è liquido, meno c'è da spremere** (margine PL 4.3% → nessun
   bias; SA 4.9% → tutti i bias). Il tracer market-side (Passo 2) anticipa
   quasi tutto.
3. **Il pareggio è la dimensione più per-lega che esista**: deficit latino
   (SA/Liga φ0≈0.39) vs assenza inglese (PL φ0=0). Ogni leva-pareggio va
   ri-fittata, mai copiata.
4. **Il pari/dispari non si predice in nessuna lega** (4 repliche): non
   prezzarlo con pretese.
5. **Le covariate (congestione, forma, rose…) sono rumore ovunque**: il fit
   pesato nel tempo le assorbe. Riprovarle su una lega nuova solo con una
   ragione strutturale forte (es. una lega con calendario estremo).

## Checklist di chiusura (per OGNI esperimento della lega nuova)

- [ ] run in `experiments/runs.jsonl` (nessuna analisi senza run);
- [ ] `docs/DIARIO.md`: fase con blocco 📐 (formule verificate sul sorgente +
      perché di ogni numero);
- [ ] `README.md`: riga nel «Registro completo dei risultati»;
- [ ] `docs/PANCHINA.md`: celle della matrice aggiornate (+ voci di
      dettaglio, condizioni di promozione);
- [ ] quaderno di studio della lega: risultati + tabella differenze;
- [ ] `docs/PISTE.md` / `docs/DATI.md` / questo playbook se cambia il metodo;
- [ ] `pytest` verde; commit + push (container effimero).

---

*Creato alla Fase 80 (luglio 2026), dopo l'onboarding completo di Premier
League e La Liga. Se il metodo cambia (nuove fonti, nuovi passi), aggiornare
QUESTO file oltre al CLAUDE.md: è il punto d'ingresso per ogni lega futura.*
