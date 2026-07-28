# listMarketProfitAndLoss

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687667>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687667`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

**listMarketProfitAndLoss**

**List<MarketProfitAndLoss>** **listMarketProfitAndLoss** **(** **Set<MarketId> marketIds**, boolean includeSettledBets, boolean includeBspBets, boolean netOfCommission **)** **throws APINGException**

Retrieve profit and loss for a given list of OPEN markets. The values are calculated using matched bets and optionally settled bets. **Only odds (**MarketBettingType** = ODDS) markets are implemented; markets of other types are silently ignored.**

To retrieve your profit and loss for CLOSED markets, please use the  request.

****Please note**:   apply to requests made to**listMarketProfitAndLoss****

| Parameter name | Type | Required | Description |
| --- | --- | --- | --- |
| marketIds | Set<MarketId> |  | List of markets to calculate profit and loss |
| includeSettledBets | boolean |  | Option to include settled bets (partially settled markets only). Defaults to false if not specified. |
| includeBspBets | boolean |  | Option to include BSP bets. Defaults to false if not specified. |
| netOfCommission | boolean |  | Option to return profit and loss net of users current commission rate for this market including any special tariffs. Defaults to false if not specified. |

| Return type | Description |
| --- | --- |
| List<MarketProfitAndLoss> |  |

| Throws | Description |
| --- | --- |
| APINGException | Generic exception that is thrown if this operation fails for any reason. |

**Since 1.0.0**
