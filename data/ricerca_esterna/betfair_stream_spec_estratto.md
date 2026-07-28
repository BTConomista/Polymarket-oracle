# Specifica Exchange Stream API — estratto di riferimento (Fase 109-bis)

**Fonte**: documentazione ufficiale Betfair, spazio *Betfair Exchange API
Documentation*, pagina **"Exchange Stream API"** (id Confluence `2687396`).
URL: <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/overview>

**Perche' questo file esiste.** I file del servizio *Historical Data*
(`historicdata.betfair.com`) sono **registrazioni dello stream** descritto qui:
stessa struttura di messaggi. Il parser di `scripts/fetch_betfair_historic.py`
va quindi verificato contro QUESTA specifica, non contro assunzioni ricavate
guardando i file. Alla Fase 109-bis la lettura ha trovato un bug reale (vedi
sotto, `img`).

⚠️ **Limite dichiarato**: la specifica descrive lo stream **live**. Che i file
storici la seguano in ogni dettaglio e' un'inferenza ragionevole (sono
registrazioni), **non un fatto verificato**: la verifica vera sara' il
confronto dell'estrazione 2024-25 contro la colonna `BFEC>2.5` di
football-data (protocollo dentro lo script).

## I quattro campi su cui poggia il parser (citazioni testuali)

**`img` / Image** — il campo che ha rivelato il bug:
> img / Image - replace existing prices/data with the data supplied: it is not a delta (or null if delta) tv - The total amount matched across

**`rc` / RunnerChange** e **`con` / Conflated**:
> rc / RunnerChange - this is sent to supply the details of a runner (namely prices) con / Conflated = true - if this is sent then more than one change is combined in this message Values -  Please note:

**`ltp`**:
> ltp - Last Traded Price on this runner. spn - Starting Price Near spf - Starting Price Far

**`inPlay`** (il marcatore che definisce la chiusura):
> inPlay True if the market is currently in play boolean crossMatching True if cross-matching is enabled for thi

**`marketDefinition`**:
> marketDefinition / MarketDefinition - this is sent in full (but only if it has changed) rc / RunnerChange - this is sent

## Conseguenze sul codice

| campo | semantica da specifica | come lo tratta il parser |
|---|---|---|
| `img` | **sostituisce**, non e' un delta | `last.clear()` prima di applicare `rc` (fix Fase 109-bis) |
| `rc` senza `img` | delta | merge sulla cache |
| `ltp` | ultimo prezzo scambiato | e' il prezzo che estraiamo |
| `inPlay` | mercato in gioco | congela la chiusura all'istante in cui diventa `true` |
| `con` | piu' cambi accorpati | irrilevante: teniamo comunque l'ultimo stato |

Il fix su `img` e' coperto da `tests/test_betfair_historic.py`
(`test_img_sostituisce_la_cache_non_la_fonde`), **verificato per mutazione**:
rimuovendo `last.clear()` il test fallisce.
