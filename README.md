# Polymarket Oracle

Motore di stima delle **probabilità reali di eventi sportivi** (calcio),
**indipendente dalle piattaforme** di scommessa.

Il valore del progetto è il **modello di previsione**, non l'integrazione con una
piattaforma specifica. Il motore stima la distribuzione dei gol di una partita; da
quella distribuzione si derivano in modo coerente tutti i mercati (1X2,
Over/Under, ecc.). Solo in un secondo momento il motore potrà essere collegato a
Polymarket, bookmaker, exchange o altri mercati di previsione.

> 📖 **[Diario di bordo](docs/DIARIO.md)** — il resoconto passo-passo di tutte le
> fasi, con il ragionamento e le scelte dietro ogni decisione. Se vuoi capire
> *perché* il progetto è fatto così, parti da lì.
>
> 🛠️ **[Protocollo di lavoro](CLAUDE.md)** — come si contribuisce e **cosa
> aggiornare ogni volta** (registro esperimenti, diario, test). Da leggere prima
> di modificare il progetto; una sessione AI lo carica in automatico.

## Stato attuale

Prima pipeline **end-to-end** funzionante su **Serie A**:

`dati storici → modello Dixon-Coles → probabilità 1X2 e Over/Under 2.5 → validazione`

- **Modello**: Dixon-Coles (1997) con decadimento temporale, implementato da zero
  (`src/models/dixon_coles.py`). Stima forza d'attacco/difesa di ogni squadra +
  vantaggio-casa + correzione sui punteggi bassi.
- **Dati**: 9 stagioni di Serie A (2017-18 → 2025-26) in formato football-data.co.uk.
- **Validazione**: backtest walk-forward sulla stagione 2025-26 (riallenamento
  settimanale, **senza look-ahead**), con Brier score e log-loss, confronto contro
  le quote di chiusura dei bookmaker e contro una baseline banale.

### Risultati del backtest (media su 6 stagioni, 2020-21 → 2025-26)

Metrica principale: **log-loss medio** su 6 stagioni di test (walk-forward, senza
look-ahead). Usiamo la media di 6 stagioni — non una sola — perché una singola
stagione è rumorosa (è il nostro principio: mai concludere da una stagione).

| Mercato | Modello | Baseline | Mercato (chiusura) |
|---|---:|---:|---:|
| **1X2** log-loss | 0.9807 | ~1.085 | **0.9632** |
| **O/U 2.5** log-loss | 0.6884 | ~0.690 | **0.6816** |

_Configurazione ufficiale: **blend gol/xG con α = 0.75**, shrinkage = 1.5, emivita
= 365g, **prior neopromosse δ = 0.23** (vedi Fasi 4b, 4d e 7). Il modello batte
nettamente la baseline e si avvicina al mercato (gap 1X2 ~+0.018), ma **non lo
batte**. Su una singola stagione i numeri oscillano (es. la 2025-26 ha 1X2 ≈
0.993): per questo si giudica sulla media. (Il prior neopromosse migliora la
media a ~0.9796; la tabella sopra riporta la config pre-Fase 7 per continuità.)_

**Come leggerli** (più bassi = meglio):

- Sull'**1X2** il modello **batte nettamente la baseline** (impara qualcosa di
  reale) e si avvicina al mercato, ma **non lo batte**. È il risultato atteso e
  sano per un primo modello semplice: le quote di chiusura sono lo stimatore più
  efficiente che esista.
- Sull'**Over/Under 2.5** il modello è vicino al mercato ma **non aggiunge valore**
  rispetto a "scommetti sulla frequenza media" (baseline). L'O/U è un mercato
  quasi 50/50, difficile da battere senza feature più ricche.
- La simulazione di *value betting* dà **ROI ≈ -8.5%**: un modello che non batte
  la linea di chiusura **perde soldi** contro il margine del bookmaker. Onesto e
  prevedibile a questo stadio.

**Conclusione**: la pipeline funziona e il modello è valido *come modello*, ma non
ha ancora un vantaggio sul mercato. **Non usare questo modello per scommettere
soldi veri.**

### Analisi degli errori — Fase 2a (`scripts/analyze.py`)

Prima di aggiungere feature, abbiamo analizzato *dove* il modello perde contro il
mercato. Risultati principali:

- **Sulla media il modello è ben calibrato** (nessun bias sistematico, nemmeno sui
  pareggi): il vantaggio del mercato è nella **discriminazione** delle singole
  partite, non nella calibrazione media.
- **Bug trovato e corretto**: la stagione di test chiamava il Verona "Hellas
  Verona" mentre le stagioni di training usavano "Verona" → il modello lo trattava
  come squadra sconosciuta, producendo predizioni assurde. Risolto con una mappa
  di normalizzazione nomi (`TEAM_ALIASES` in `sources.py`).
- **Dove il modello perde di più** (log-loss, gap col mercato): partite con
  **neopromosse** (gap +0.037, doppio della media) e **inizio stagione**
  (+0.030). Radice comune: dati storici scarsi o datati → stime inaffidabili.
  Questi sono i bersagli prioritari del feature engineering (Fase 2b).

### Feature engineering — Fase 2b (in corso)

Primo intervento: **shrinkage** (regolarizzazione verso la media della lega),
tarato con `scripts/tune.py` su due stagioni. Poiché la penalità è
fissa mentre il contributo dei dati cresce col numero di partite, l'effetto è
**automaticamente più forte sulle squadre con pochi dati** — proprio i punti
deboli individuati.

Risultato (log-loss 1X2, media 2024-25 + 2025-26; più basso = meglio):

| shrinkage | media | gap col mercato |
|---:|---:|---:|
| 0.0 (base) | 0.9918 | +0.026 |
| **1.5** (scelto) | **0.9879** | **+0.022** |
| Mercato | 0.9654 | — |

Migliora **entrambe** le stagioni e riduce il divario col mercato di ~15%. In
particolare il gap sull'**inizio stagione** scende da +0.030 a +0.022 e quello
sulle **neopromosse** da +0.037 a +0.030: l'intervento colpisce i bersagli
previsti.

Secondo intervento: **taratura dell'emivita** del decadimento temporale (quanto
peso dare alle partite recenti), su tre stagioni. Risultato (log-loss 1X2 medio):

| emivita | media | note |
|---:|---:|---|
| 90g | 0.9935 | troppo reattiva, rumorosa |
| 180g (prima) | 0.9863 | |
| 365g | 0.9834 | |
| **730g** (scelta) | **0.9829** | memoria ~2 stagioni |
| Mercato | 0.9658 | |

Lezione: in Serie A le rose restano stabili anno su anno, quindi una **memoria
lunga** (~2 stagioni) batte il peso aggressivo sulle ultime partite. Con la
configurazione finale (emivita 730g, shrinkage 1.5) il divario medio col mercato
scende da +0.026 (Dixon-Coles puro) a **+0.017**: circa un terzo del divario
recuperato solo con la taratura, senza informazione nuova.

Qui il modello basato sui **soli gol** è vicino al suo tetto: per avvicinarsi
ancora al mercato serve informazione nuova (forma, xG, indisponibili), non altro
tuning.

### Informazione nuova: tiri in porta — Fase 3 (risultato NEGATIVO)

Terzo intervento, primo con informazione *nuova*: i **tiri in porta** (già
presenti nella fonte dati) misurano le occasioni create con meno rumore dei gol
(la "fortuna sotto porta"). Il modello è stato esteso per allenare, oltre a
quello sui gol, un modello sui tiri in porta e **mescolare** i due tassi attesi
con un peso α tarabile (`shots_blend`: α=1 solo gol, α=0 solo tiri).

Esito, tarato su **sei** stagioni di test (2020-21 → 2025-26, regimi diversi,
COVID inclusi):

| α (peso gol) | 1X2 (media) | O/U 2.5 (media) |
|---:|---:|---:|
| 0 (solo tiri) | 0.9913 | 0.6964 |
| 0.5 | 0.9833 | 0.6909 |
| **1 (solo gol)** | **0.9817** | **0.6904** |
| Mercato | 0.9632 | 0.6816 |

- Sull'**1X2** i tiri **peggiorano** in modo netto e monotòno (α=1 è il migliore).
- Sull'**Over/Under** α=1 è il migliore anche in media. Su 3 stagioni sembrava
  esserci un lieve vantaggio dei tiri, ma **si dissolve su 6 stagioni**: era
  rumore di piccolo campione (allargare il backtest ha chiarito il quadro).

> **Da tenere d'occhio (ipotesi aperta).** Nella stagione più recente (2025-26),
> e in modo più sfumato nel 2024-25, dare peso ai tiri in porta **migliora
> l'Over/Under** (2025-26: α=0 → 0.7000 vs α=1 → 0.7056), anche se non aiuta
> l'1X2 e non aiuta nella media a 6 stagioni. Possibile ipotesi: da un paio di
> stagioni il modo di affrontarsi in campionato sta cambiando e le occasioni
> create potrebbero diventare via via più informative. **Da ri-verificare** man
> mano che arrivano nuove stagioni: se il segnale si rafforza, il blend (o l'xG
> reale) tornerà utile, almeno sull'Over/Under.

**Conclusione: i tiri in porta grezzi non danno un miglioramento affidabile** (su
6 stagioni, α=1 è il migliore per entrambi i mercati). Il
default resta α=1 (solo gol); il codice del blend è mantenuto (esperimento
documentato, riutilizzabile con l'xG *reale*, che pesa la qualità delle occasioni
e non solo il conteggio). È un risultato prezioso: aver testato la versione
*economica* dell'idea "le occasioni aiutano" ci ha evitato di costruire una
pipeline xG/database sull'assunzione sbagliata che bastasse.

### xG reale nel blend — Fase 4b (primo miglioramento da dati nuovi)

Con l'xG reale integrato (Fase 4a), abbiamo rifatto lo *stesso* esperimento del
blend, ma con l'**xG** al posto dei tiri grezzi. Il meccanismo è identico (peso α
gol vs segnale), cambia solo la qualità del segnale.

Esito su **6 stagioni** (log-loss, più basso = meglio):

| α (peso gol) | 1X2 | O/U 2.5 |
|---:|---:|---:|
| 0 (solo xG) | 0.9840 | 0.6897 |
| 0.5 | 0.9816 | **0.6888** |
| **0.75** (scelto) | **0.9813** | 0.6893 |
| 1 (solo gol) | 0.9817 | 0.6904 |
| Mercato | 0.9632 | 0.6816 |

- È il **primo segnale che aggiunge valore** dopo il tuning: dove i tiri *grezzi*
  fallivano (Fase 3), l'**xG aiuta** — piccolo ma reale, soprattutto
  sull'Over/Under (la *qualità* delle occasioni informa il volume di gol).
- α=0.75 (config scelta) migliora **entrambi** i mercati sulla media a 6 stagioni.
- I guadagni O/U più grandi sono nelle stagioni **recenti** (2024-25, 2025-26),
  coerente con l'ipotesi che lo stile di gioco stia evolvendo.

**Onestà:** il miglioramento è *modesto* e non ci fa battere il mercato. Ma è il
primo passo avanti ottenuto con informazione nuova.

## Struttura

```
src/
  data/         raccolta e normalizzazione dati (schema interno pulito)
    sources.py    UNICO punto con URL e stagioni (cambiare fonte = 1 riga)
    loader.py     download + parsing + normalizzazione
  models/
    dixon_coles.py   il modello (stima + predizione)
  evaluation/
    metrics.py    Brier, log-loss, devigging quote, baseline
scripts/
  download_data.py   scarica i CSV (cache in data/raw/)
  backtest.py        esegue il backtest walk-forward e stampa il report
tests/              test unitari del modello e delle metriche
worldcup/           esperimento parallelo a bassa priorità (Mondiali)
```

## Come si usa

```bash
pip install -e .            # oppure: pip install numpy pandas scipy pytest

python scripts/download_data.py     # scarica i dati storici (una volta)
python scripts/backtest.py          # esegue il backtest sulla stagione 2025-26
python scripts/analyze.py           # analizza gli errori del backtest
python scripts/tune.py --sweep shrinkage          # tara un iperparametro su piu' stagioni
python scripts/markets.py           # grande backtest su TUTTI i mercati (1X2, O/U, GG/NG, doppie chance)
python -m pytest                    # esegue i test
```

Opzioni utili:

```bash
python scripts/backtest.py --test-season 2425          # testa un'altra stagione
python scripts/tune.py --sweep half_life_days --values 0 180 365 730
python scripts/tune.py --sweep shots_blend --values 0 0.5 1
```

## Roadmap (idee, non impegni)

1. ✅ **Fase 1** — tracer bullet: Dixon-Coles + backtest su Serie A.
2. ✅ **Fase 2a** — analisi degli errori: capito dove il modello perde (neopromosse,
   inizio stagione) e corretto il bug dei nomi squadra.
3. ✅ **Fase 2b** — tuning: shrinkage + memoria lunga (emivita 730g). Divario
   medio col mercato da +0.026 a +0.017.
4. ✅ **Fase 3** — tiri in porta come informazione nuova: **risultato negativo**
   (i tiri grezzi non aiutano in modo affidabile). Codice mantenuto per l'xG reale.
5. ✅ **Fase 4a** — arricchimento dati: **xG reale Understat per il 100% delle
   3420 partite**, valori rosa Transfermarkt a inizio stagione (copertura 63-80%
   per stagione) e assenze stimate da infortuni. Snapshot e DB rigenerati, base
   invariata (stessa impronta dati). Vedi `docs/DIARIO.md`, Fase 4a.
6. ✅ **Fase 4b** — blend gol/**xG reale** (α=0.75): primo miglioramento da dati
   nuovi, soprattutto sull'Over/Under. Config ufficiale aggiornata.
7. ✅ **Fase 4c** — spremuti gli altri dati (npxG, valori rosa, assenze) via un
   **layer di covariate** (anche in combinazione): **risultato negativo** — non
   aggiungono segnale indipendente (già implicito in gol+xG). Modello al **tetto
   pratico** dei dati attuali.
8. ✅ **Fase 4d** — ri-taratura congiunta: col blend xG l'emivita ottima passa a
   **365g** (memoria più corta). Piccolo guadagno su entrambi i mercati.
9. ✅ **Fase 4e** — **calendario di club completo** (Serie A + Coppa Italia +
   coppe europee) per la **congestione vera** + validazione walk-forward della
   covariata `rest_full` sulle 5 stagioni a copertura reale (2020-25). Il
   calendario completo **inverte il segno** del proxy solo-lega della Fase 4c
   (che peggiorava), ma il guadagno è **minuscolo e dentro il rumore** (−0.0004
   medio su 1X2 log-loss, aiuta 2 stagioni su 5) e **non tocca il mercato**:
   config ufficiale **invariata**, covariata off di default. Conferma il **tetto
   pratico** dei dati attuali. Vedi `docs/DIARIO.md`, Fase 4e / 4e-bis.
10. ✅ **Fase 5** — grande backtest **multi-mercato** (`scripts/markets.py`): il
   modello è affidabile sui mercati d'**esito** (1X2, 1X, 2X, batte la baseline),
   **debole** su Over/Under, e **peggio della baseline su GG/NG** (cattura male la
   correlazione dei punteggi). Nessun mercato batte le quote. Vedi `docs/DIARIO.md`.
11. ✅ **Fase 6** — **ricalibrazione della confidenza** (temperature scaling,
    `scripts/calibrate.py`): T tarato walk-forward sul passato. Scoperta reale e
    robusta — il modello è **sistematicamente un po' sottoconfidente** (T≈0.94,
    <1 in tutte e 6 le stagioni) — ma il guadagno è **nel rumore** (−0.0003 medio
    su 1X2 log-loss) e non uniforme: **non entra** nella config ufficiale. Modulo
    `src/evaluation/calibration.py` disponibile per l'uso pratico. Conferma il
    **tetto pratico** dei dati attuali. Vedi `docs/DIARIO.md`, Fase 6.
12. ✅ **Fase 7** — **prior di cold-start per le neopromosse** (`--promoted-prior`):
    sposta il bersaglio dello shrinkage sotto la media per le squadre senza
    storico (δ≈0.23, stimato leave-future-out). È il **miglior guadagno interno**
    trovato: −0.0011 medio complessivo (3-4× congestione/calibrazione) e −0.0039
    sulle partite delle neopromosse, su **5 stagioni su 6**. **Adottato nella
    config ufficiale** (δ=0.23). Vedi `docs/DIARIO.md`, Fase 7.
13. ✅ **Fase 8** — ultimo giro economico, **entrambe negative**: ri-taratura
    shrinkage col prior = curva **piatta** (leve ortogonali, nessun guadagno);
    vantaggio-casa per-squadra = **persistenza anno-su-anno r≈0.00** (solo rumore,
    non generalizza). Nulla più da spremere: modello al **tetto pratico**.
14. ✅ **Fase 9** — **anatomia del gap col mercato** (`scripts/analyze_gap.py`):
    gap 1X2 medio **+0.0165** (modello 0.9797 vs mercato 0.9632). Scomposto: varia
    per stagione (+0.014→+0.020, peggio nel COVID 2020-21), per forza-squadra (a U:
    deboli +0.0206 e forti +0.0180 peggio delle medie +0.0123), e — soprattutto —
    **è quasi tutto nel PAREGGIO** (il mercato 12 senza pari ha gap +0.0020 ≈
    mercato). Punta al prossimo passo mirato: **correlazione dei punteggi**. Vedi
    `docs/DIARIO.md`, Fase 9.
15. ✅ **Fase 10** — **ricalibrazione per-classe 1X2** (casa/pari/ospite): conferma
    robusta che il modello **sovrastima la casa e sottostima il pareggio** (w≈0.96
    / 1.04 in tutte e 6 le stagioni), ma il guadagno è nel rumore (−0.0005 medio,
    4/6 stagioni) → **non entra** nella config (come il temperature); funzioni in
    `src/evaluation/calibration.py` per l'uso pratico. Quinto esperimento interno
    di fila con guadagno nel rumore. Vedi `docs/DIARIO.md`, Fase 10.
16. ✅ **Fase 11** — **combinazioni delle feature off-di-default**
    (`scripts/_run_combo_analysis.py`): griglia 8 combo covariate × con/senza
    ricalibrazione, 6 stagioni. **Nessuna combinazione è utile**: `squad_value`
    peggiora sempre, `absence`/`rest_full` sono rumore anche in coppia; l'unico
    effetto additivo è la ricalibrazione (già nota, −0.0005/−0.0008). Sesto
    esperimento interno di fila senza guadagno robusto. Vedi `docs/DIARIO.md`.
17. **Prossimo bivio** — modello di classe diversa (es. bivariate Poisson per la
    correlazione dei punteggi / GG/NG) / dati davvero nuovi, oppure **uso pratico**.
18. **Estensione** a nuovi campionati (già predisposto in `sources.py`).
19. **Integrazioni** con piattaforme esterne (Polymarket, exchange, …).

## Archivio dati interno (riproducibilità)

Per non dipendere dalla disponibilità *in tempo reale* di una fonte esterna (che
può cambiare o sparire) e permettere a chiunque di rieseguire gli stessi calcoli,
i dati sono **congelati** in un archivio interno con due artefatti:

- **snapshot** `data/serie_a_matches.csv` — **versionato in git**, testo diffabile:
  è la fonte di verità congelata (3420 partite, 9 stagioni). Chi clona il repo ha
  esattamente gli stessi dati, **senza rete**.
- **database** `data/football.db` — SQLite queryable, **rigenerabile** dallo
  snapshot (non versionato).

```bash
python scripts/build_database.py            # ricostruisce il DB dallo snapshot (offline)
python scripts/build_database.py --enrich   # ricalcola xG/rose/assenze sullo snapshot esistente
python scripts/build_database.py --fixtures # assembla il calendario di club completo + congestione vera
python scripts/build_database.py --refresh  # riscarica TUTTO dalle fonti e aggiorna lo snapshot
sqlite3 data/football.db "SELECT season, COUNT(*) FROM matches GROUP BY season"
```

### Colonne di arricchimento (Fase 4a)

Oltre alle 15 colonne base (partita, gol, tiri in porta, quote), lo snapshot
contiene 14 colonne da fonti esterne (`NaN` dove la fonte non copre):

| Colonne | Fonte | Note |
|---|---|---|
| `home_xg`, `away_xg`, `home_npxg`, `away_npxg` | Understat | xG e xG senza rigori; **100% delle partite** |
| `home_ppda`, `away_ppda`, `home_deep`, `away_deep` | Understat | pressing e passaggi profondi |
| `home_squad_value`, `away_squad_value` | Transfermarkt | valore rosa (EUR) all'inizio stagione (valutazioni ≤ 1 settembre, **niente look-ahead**); pubblicato solo con copertura ≥85% dei minuti, altrimenti `NaN` |
| `home_absent_count_est`, `away_absent_count_est`, `home_absent_value_est`, `away_absent_value_est` | Transfermarkt | assenze per infortunio alla data della partita: **stime** (suffisso `_est`), rosa ricostruita dai minutaggi Understat |

Il join usa la chiave `(season, home_team, away_team)` con nomi squadra
canonicalizzati (alias in `sources.TEAM_ALIASES`); la data serve solo da
controllo di coerenza.

### Congestione vera — calendario di club completo (Fase 4e)

Il riposo di `add_rest_days` vede solo le date di Serie A; la **congestione
vera** richiede coppe ed Europa. `src/data/fixtures.py` assembla il **calendario
di club completo** (Serie A dallo snapshot + Champions/Europa/Conference e Coppa
Italia da openfootball, via mirror GitHub) nella tabella grezza versionata
`data/club_fixtures.csv` (`season, team, date, competition, home_away,
opponent`), e aggiunge allo snapshot 4 colonne:

| Colonne | Significato |
|---|---|
| `home_rest_days_full`, `away_rest_days_full` | giorni dall'ultima partita di club in **qualsiasi** competizione, cap 14, solo partite precedenti (no look-ahead), `NaN` se ignoto |
| `home_midweek_europe`, `away_midweek_europe` | 1 se la squadra ha giocato una gara europea/coppa nei ~4 giorni precedenti |

Copertura reale per stagione (onesta, con i buchi documentati) nel
[diario, Fase 4e](docs/DIARIO.md): Champions League tutte e 9 le stagioni,
Europa dal 2020-21, Conference dal 2021-22, Coppa Italia 2020-21→2024-25. Dove
una competizione non è coperta, `rest_days_full` degrada verso il valore
solo-lega (mai in direzione sbagliata) — **nessun numero inventato**. Invariante
verificata su ~3400 partite: `rest_days_full ≤ rest_days` (0 violazioni). La
covariata `rest_full` legge queste colonne ma resta **off di default**: la
validazione walk-forward (Fase 4e-bis) mostra un guadagno dentro il rumore
(−0.0004 medio su 1X2 log-loss, 2020-25), non abbastanza per adottarla —
`python scripts/backtest.py --covariates rest_full --test-season 2122` per
riprovare.

Tutta la pipeline è **offline-first**: `backtest.py`/`tune.py` leggono lo snapshot
congelato (nessun download per run), quindi i risultati sono riproducibili identici.
Ogni backtest è inoltre registrato in `experiments/runs.jsonl` con l'impronta dei
dati usati (vedi `experiments/README.md`).

### Fonti originali

L'ambiente di sviluppo cloud non raggiunge direttamente `football-data.co.uk`,
`understat.com` né `transfermarkt.com` (policy di rete), quindi si usano mirror
su GitHub con **lo stesso formato**:

- **football-data** e **Understat**: stesso repo mirror (aggiornato da un
  workflow giornaliero) — URL in `sources.BASE_URL` / `sources.UNDERSTAT_URL`;
- **Transfermarkt**: datalake `salimt/football-datasets` — URL in
  `sources.TRANSFERMARKT_MIRROR_URL`. Limite noto: ~25% dei profili è privo di
  serie di valutazioni (per questo alcune squadre-stagione hanno `squad_value = NaN`).

Girando il progetto in locale è sufficiente sostituire gli URL in
`src/data/sources.py` con quelli ufficiali (per Understat c'è già
`UNDERSTAT_OFFICIAL_URL`).
