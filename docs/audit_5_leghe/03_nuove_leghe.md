# Report 3 — Import di Bundesliga e Ligue 1

> **Che cos'è questo documento.** Il terzo degli **11 report integrali dell'audit
> a 5 leghe (Fase 100)** — verbale esteso di ciò che `docs/DIARIO.md` riassume
> nella voce «Cinque leghe». Indice: [`00_indice.md`](00_indice.md). Documento
> **storico**: le checklist del §7 sono state **eseguite** all'integrazione (vedi
> il riquadro là).

**Domanda posta:** *«importiamo i dati di bundesliga e ligue 1, segui sempre i
dati che abbiamo importato fino ad ora»* — cioè **stesso schema, stesse fonti,
stessa semantica** delle tre leghe già in repo.

**Verdetto:** fatto. Due snapshot congelati, **38 colonne identiche (nomi e
ordine) a `data/serie_a_matches.csv`**, 9 stagioni (2017-18 → 2025-26):

| file | partite | stagioni | squadre | colonne |
|---|--:|--:|--:|--:|
| `data/bundesliga_matches.csv` | **2.754** | 9 | 29 | 38 |
| `data/ligue_1_matches.csv` | **3.097** | 9 | 30 | 38 |
| `data/club_fixtures_bundesliga.csv` | 10.375 righe squadra-partita | | | |
| `data/club_fixtures_ligue_1.csv` | 10.701 righe squadra-partita | | | |

Entrambi passano l'intero audit (Report 1): **0 differenze** rispetto alle fonti
su gol, date, tiri, 10 colonne quota e 8 colonne xG.

---

## 1 · Fonti (tutte scaricate, con provenienza registrata)

| dato | fonte | come |
|---|---|---|
| risultati + quote | football-data.co.uk, `D1` (Bundesliga) e `F1` (Ligue 1) | 18 CSV, scaricati oggi |
| xG/npxG/PPDA/deep + rose | Understat, `Bundesliga` e `Ligue_1` | 18 JSON via `getLeagueData/` |
| valore rosa | player-scores (`L1`, `FR1`) | `files/player_scores/*.csv.gz` già in repo |
| assenze stimate | Transfermarkt (mirror salimt) + rose Understat | rete |
| calendario di club | openfootball: `deutschland/{stagione}/1-bundesliga.txt`, `2-bundesliga2.txt`, `cup.txt`; `france/france/{stagione}_fr{1,2}.txt`, `_frcup.txt`; coppe UEFA condivise | rete |

`data/ricerca_esterna/manifest_fonti_audit.json`: URL, timestamp UTC, byte e
**SHA256** dei grezzi football-data e Understat-lega — **36 dei 141** file usati
qui; restano fuori gli 84 `.txt` openfootball, i 16 `.html` Transfermarkt e i 4
`.json` `understat_match` (vedi la tabella in testa a
[`00_indice.md`](00_indice.md)).

> ⚠️ **Rettifica della Fase 101.** Le fonti delle due leghe nuove *erano*
> **versionate** nel cantiere (≈11 MB) e gli snapshot si rigeneravano
> **offline**, come per Premier/Liga dai bundle di `files/`. All'integrazione
> sono state **rimosse** (`data/fonti/` è ora in `.gitignore`), quindi oggi la
> rigenerazione richiede prima `python scripts/fetch_sources.py`, che vuole la
> rete.

> ⚠️ La Francia ha uno schema di percorsi openfootball **diverso** da tutte le
> altre leghe: il repo `openfootball/france` è in realtà il mono-repo «Europe» e
> i file sono `france/{stagione}_fr1.txt` (stagione nel **nome del file**, non
> in una cartella). La costante `OPENFOOTBALL_DOMESTIC_URL` di `sources.py` non
> la esprime: serve un builder per lega (`nuove_leghe.openfootball_url`).

## 2 · Metodo: zero codice di modello toccato

Riuso integrale del codice di produzione — `loader._normalize` (risultati + le
10 colonne quota con la politica Fase 73), `understat.parse_season_xg`,
`player_scores.add_squad_values`, `transfermarkt.add_absences`, `fixtures.*` —
con le due leghe **registrate a runtime** (`scripts/nuove_leghe.registra()`).
All'integrazione, quelle voci si spostano in `src/data/sources.py` e
`src/config.py`: **nessuna riga di modello cambia** (CLAUDE.md §7).

### Riconciliazione nomi (il bug classico) — verificata per identità

103 alias nuovi (Bundesliga 53, Ligue 1 50), ognuno verificato contro l'elenco
canonico football-data; **92 sono effettivamente esercitati** dalle fonti
attuali, gli altri 11 sono varianti difensive (stessa pratica di
`sources.TEAM_ALIASES`). La verifica **non è a occhio**: il builder fallisce
rumorosamente se, per una qualsiasi stagione, l'insieme delle squadre
football-data ≠ l'insieme Understat. Risultato: **zero orfane, zero club non
agganciati** in tutte e 4 le fonti, tutte le 9 stagioni.

Due alias sono stati trovati **da un controllo indiretto**, non da un elenco:
- `player_scores` fallisce rumorosamente sui club non agganciati → 5 nomi
  formali tedeschi (`1.FC Köln`, `1.FSV Mainz 05`, …);
- `Havre AC` (nome usato nei file Ligue 2) è emerso perché **Le Havre risultava
  senza alcuna partita precedente al suo esordio**: senza quell'alias mancava
  tutto lo storico di seconda serie e il riposo della prima gara era NaN.
  Controllo ora sistematico su tutte e 5 le leghe: **ogni squadra ha partite
  precedenti al proprio esordio** (0 eccezioni).

## 3 · Copertura ottenuta

| gruppo di colonne | Bundesliga | Ligue 1 |
|---|--:|--:|
| partita/esito | 100.00% | 100.00% |
| tiri in porta | 99.96% | 100.00% |
| quote chiusura 1X2 | 99.96% | 100.00% |
| **quote chiusura O/U** | **77.78%** | **75.46%** |
| quote apertura 1X2 | 100.00% | 100.00% |
| quote apertura O/U | 99.96% | 100.00% |
| xG / npxG | 100.00% | 99.97% |
| stile (PPDA, deep) | 99.96% | 99.97% |
| valore rosa | 100.00% | 100.00% |
| assenze stimate | 100.00% | 100.00% |
| congestione | 100.00% | 100.00% |

La chiusura O/U al ~76-78% è **lo stesso identico buco delle altre tre leghe**
(assente nel 2017-19 a monte: Report 2 §2), non un difetto dell'import.

## 4 · Particolarità strutturali (da conoscere prima di modellare)

1. **La Bundesliga ha 18 squadre**: 306 gare/stagione, non 380. Ogni conteggio
   che assume 380 va parametrizzato.
2. **La Ligue 1 è passata da 20 a 18 squadre nel 2023-24**: 380 gare fino al
   2022-23, 306 dal 2023-24. È l'unica lega del progetto che **cambia
   dimensione** dentro la finestra dati.
3. **La Ligue 1 2019-20 fu CANCELLATA per COVID** (30/04/2020): 279 gare su 380,
   ultima l'8 marzo; PSG e Strasburgo ne giocarono 27 invece di 28. Unico grande
   campionato a non riprendere. La stagione è usabile ma **strutturalmente
   corta**.
4. **Union Berlin-Bochum 14/12/2024** (Bundesliga): risultato assegnato a
   tavolino 0-2 mentre il campo diceva 1-1 (Report 1 §4.3). Partita **giocata
   per intero** (interruzione al 92′, poi ripresa e conclusa): per decisione
   dell'utente lo snapshot porta il **risultato del campo, 1-1** (regola R1),
   con la correzione tracciata in `data/correzioni_dichiarate.csv`. Resta
   l'unica riga senza statistiche tiri (NaN dichiarato).
5. **Bielefeld-Leverkusen 21/11/2020**: xG = 0 per una squadra che ha segnato —
   sembra un buco, **non lo è**: il gol è un autogol avversario e il Bielefeld
   non ha tirato (Report 7 §1). Utile saperlo: è il tipo di riga che fa scattare
   i controlli automatici a vuoto.

## 5 · Lacune dichiarate (mai numeri inventati)

| lacuna | dettaglio | effetto |
|---|---|---|
| chiusura O/U 2017-19 | assente a monte (5 leghe su 5) | come le altre leghe; la stima E3 può essere estesa qui |
| ~~valore rosa 2025-26~~ | **CHIUSA**: le 16 celle (5 Bundesliga, 11 Ligue 1) sotto la soglia di copertura player-scores sono state riempite col dato **reale Transfermarkt** (regola R2), provenienza riga per riga in `data/squad_value_2526_transfermarkt.csv` | copertura valore rosa ora **100%**; la colonna 2025-26 mescola due misure (rapporto misurato per lega, vedi REGOLE.md R2) |
| Coppa di Germania | openfootball non ha `cup.txt` per 2016-17 e 2017-18 | `midweek_europe` falso 0 in quelle stagioni per chi giocò la Pokal |
| Coppa di Francia | openfootball ha **solo** `2024-25_frcup.txt` | idem, su tutte le altre stagioni |
| Europa/Conference 2025-26 | file assenti in openfootball — **vale per tutte e 5 le leghe** | falso 0 nella stagione in corso |
| xG Nantes-Toulouse 17/05/2026 | Understat marca `isResult=false` | NaN dichiarato (1 riga) |

Le lacune di coppa nazionale sono **dello stesso tipo** già presenti nelle altre
leghe (Coppa Italia e Copa del Rey solo dal 2020-21) e degradano `rest_days_full`
sempre nella direzione conservativa (mai verso un riposo inventato).

## 6 · EDA: le 5 leghe a confronto (passo 1 del playbook)

| lega | gare | gol/gara | casa% | pari% | ospite% | over2.5% | γ | Var/Media | δ promosse | corr(xG,gol) | margine 1X2 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| serie_a | 3420 | 2.719 | 41.2% | 26.0% | 32.7% | 52.0% | 0.150 | 0.978 | 0.229 | 0.607 | 4.35% |
| premier_league | 3420 | 2.839 | 44.1% | 23.4% | 32.5% | 54.4% | 0.185 | 0.963 | 0.329 | 0.635 | 3.82% |
| la_liga | 3420 | 2.582 | 45.3% | 26.5% | 28.2% | 47.1% | 0.272 | 1.038 | 0.218 | 0.621 | 4.26% |
| **bundesliga** | 2754 | **3.122** | 43.7% | 24.9% | 31.4% | **60.3%** | 0.216 | 0.962 | **0.277** | 0.644 | 4.27% |
| **ligue_1** | 3097 | 2.742 | 43.3% | 25.3% | 31.4% | 52.2% | 0.202 | 1.006 | **0.188** | 0.631 | 4.41% |

**Validazione del metodo:** la mia formula per δ **riproduce i valori ufficiali
già in `src/config.py`** — Premier ln(1.419/1.022) = 0.3286 (config: 0.33), La
Liga ln(1.291/1.038) = 0.2179 (config: 0.22), Serie A ln(1.360/1.081) = 0.2292
(config: 0.23). Gli stessi identici numeri citati nei commenti del file. Quindi
i δ delle due leghe nuove sono calcolati con un metodo verificato.

### 📐 Il δ delle due leghe nuove

```
δ = ln( gol_medi_per_squadra_gara_della_lega / gol_medi_per_gara_delle_NEOPROMOSSE )

Bundesliga: δ = ln(1.5608 / 1.1834) = 0.2768     (17 neopromosse, 578 gare-squadra)
Ligue 1:    δ = ln(1.3710 / 1.1358) = 0.1882     (19 neopromosse, 670 gare-squadra)
```
Neopromossa = squadra presente in una stagione e assente in quella precedente
(la prima stagione dei dati non ha un «prima»: esclusa). Lettura: le promosse
**francesi sono le meno deboli** del campione (δ 0.19, contro 0.33 inglese) —
coerente con una Ligue 1 dal vertice concentrato e dal centro-classifica
compresso; le tedesche stanno in mezzo (0.28), come l'alta quota di gol della
lega lascia prevedere.

⚠️ Questi δ sono **calcolati, non ancora adottati**: l'adozione richiede il
passo 3 del playbook (ri-taratura per-lega con backtest walk-forward). Qui c'è
solo il numero e la sua derivazione.

> **Adottati poi**, dopo il passo 3 ([`06_tranche3.md`](06_tranche3.md)):
> `src/config.py` porta oggi `promoted_prior` **0.28** (Bundesliga) e **0.19**
> (Ligue 1), cioè i due valori qui calcolati arrotondati a due decimali come per
> le altre leghe. Adozione **per motivazione strutturale**: il guadagno misurato
> è nel rumore (report 6, passo 3), e va detto così.

### Deficit-pareggio per quartile di equilibrio (reale − prezzato dal mercato)

| lega | Q1 equilibrate | Q2 | Q3 | Q4 sbilanciate |
|---|--:|--:|--:|--:|
| serie_a | **+0.0323** | +0.0111 | −0.0031 | −0.0105 |
| la_liga | **+0.0223** | +0.0035 | +0.0079 | −0.0181 |
| premier_league | −0.0092 | +0.0111 | −0.0158 | −0.0132 |
| **bundesliga** | **+0.0108** | +0.0267 | +0.0132 | +0.0014 |
| **ligue_1** | −0.0061 | −0.0032 | +0.0128 | −0.0137 |

Riproduce il fatto noto del progetto (deficit «latino» in SA/Liga, assente in
Premier: φ0 = 0 alla Fase 79) e lo estende: la **Bundesliga** mostra un deficit
positivo ma spalmato (più marcato in Q2 che in Q1), la **Ligue 1** si comporta
da lega «inglese» (nessun deficit nelle equilibrate). Prior dichiarato **prima**
di qualsiasi fit della φ(|λ−μ|): in Ligue 1 aspettarsi φ0 ≈ 0; in Bundesliga un
φ0 piccolo e positivo, con la possibilità che la forma della curva non sia
quella latina.

## 7 · Checklist di integrazione (quando si porta tutto in `main`)

> ⚠️ **Eseguita.** Tutti e otto i punti sono stati fatti all'integrazione: le due
> leghe vivono in `src/data/sources.py` e in `LEAGUE_CONFIGS` (δ 0.28 / 0.19), gli
> snapshot sono in `data/`, `tests/test_league_snapshots.py` copre le 5 leghe
> (compreso `test_schema_identico_tra_leghe`), e la matrice di `docs/PANCHINA.md`
> è passata da 4 a 6 colonne. La lista resta come verbale.

1. `src/data/sources.py`: aggiungere le 2 voci a `LEAGUES`, `UNDERSTAT_LEAGUES`,
   `UEFA_COUNTRY_CODE`, `SECOND_TIER_NAMES`, `DOMESTIC_CUP_COMPETITIONS`,
   `OPENFOOTBALL_DOMESTIC_REPO` + i 103 alias (da `scripts/nuove_leghe.py`),
   e generalizzare l'URL openfootball per lo schema francese;
2. `src/data/player_scores.py`: `COMPETITION_IDS` += `{"L1": "bundesliga", "FR1": "ligue_1"}`;
3. `src/config.py`: 2 voci in `LEAGUE_CONFIGS` — **dopo** la ri-taratura (passo 3
   del playbook), con blocco 📐 per ogni numero; i δ del §6 sono il punto di
   partenza;
4. spostare `data/{bundesliga,ligue_1}_matches.csv` e
   `club_fixtures_*.csv` in `data/`, e le fonti in `files/` (o mantenere il
   download diretto ora che la rete è aperta: aggiornare
   `docs/MANUALE_SOPRAVVIVENZA.md` §1);
5. `tests/`: estendere `test_league_snapshots.py` alle 5 leghe (+ il test
   cross-lega sull'ordine colonne, Report 1 §4.6);
6. `docs/DATI.md`: nuove righe di copertura e le lacune del §5;
   `docs/STUDIO_PREMIER_LIGA.md` → valutare un file per lega (il playbook lo
   prevede da 4 leghe in su);
7. `docs/PANCHINA.md`: 2 colonne nuove nella matrice (tutte le celle `⬜`);
8. `experiments/runs.jsonl` + `README.md` (registro completo) + `docs/DIARIO.md`
   (fase con blocco 📐) secondo la checklist del CLAUDE.md §2.

## 8 · Cosa NON è stato fatto (deliberatamente)

Il passo 2 e seguenti del playbook — **tracer bullet** (DC così com'è sulla lega
nuova), ri-taratura, motore market-implied, leve della rosa — **non** sono stati
eseguiti: la richiesta era importare i dati. I dati sono pronti e verificati per
farlo; `docs/PLAYBOOK_NUOVA_LEGA.md` §2-5 dice esattamente come.

> **Fatti subito dopo**, nello stesso audit: i passi 2-5 stanno in
> [`06_tranche3.md`](06_tranche3.md) e il resto della rosa in
> [`10_modelli_nuove_leghe.md`](10_modelli_nuove_leghe.md).
