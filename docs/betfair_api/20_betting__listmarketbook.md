# listMarketBook

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687510>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687510`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## Operation

listMarketBook

#FFFFFF#C8D0E4listMarketBook

**List<** **MarketBook** **>**  [**listMarketBook#listMarketBook**](/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687510#listMarketBook-listMarketBook) **(** **List<String>marketIds** , PriceProjection priceProjection, OrderProjection orderProjection, MatchProjection matchProjection, boolean includeOverallPosition, boolean partitionMatchedByStrategyRef, Set<String> customerStrategyRefs, StringcurrencyCode,Stringlocale, Date matchedSince, Set<[BetId](https://confluence.app.betfair/display/APING/SportsAPING+BSIDL#SportsAPINGBSIDL-BetId)> betIds**)**  **throws** **APINGException**

Returns a list of dynamic data about markets. Dynamic data includes prices, the status of the market, the status of selections, the traded volume, and the status of any orders you have placed in the market.

**Please note:** Separate requests should be made for **OPEN & CLOSED** markets. Requests that include both **OPEN & CLOSED** markets will only return those markets that are **OPEN.**

**Please note:** An illustration of the equivalent data as displayed on the Betfair website can be viewed [here](https://support.developer.betfair.com/hc/en-us/articles/6540502258077-What-Betfair-Exchange-market-data-is-available-from-listMarketBook-Stream-API-)

Market Data Request Limits apply to requests made to **listMarketBook** that include price or order projections.

Calls to **listMarketBook** should be made up to a maximum of 5 times per second to a single marketId.

### Best Practice

Customers seeking to use listMarketBook to obtain price, volume, unmatched **(EXECUTABLE)** orders, and matched positions in a single operation should provide an **OrderProjection**of **“EXECUTABLE”** in their listMarketBook request and receive all unmatched **(EXECUTABLE)** orders and the aggregated matched volume from all orders irrespective of whether they are partially or fully matched. The level of matched volume aggregation (**MatchProjection**) requested should be **ROLLED\_UP\_BY\_AVG\_PRICE** or **ROLLED\_UP\_BY\_PRICE**, the former being preferred. This provides a single call in which you can track prices, traded volume, unmatched orders and your evolving matched position with a reasonably fixed, minimally sized response.

| **Parameter name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| marketIds | List<String> |  | One or more market ids. The number of markets returned depends on the amount of data you request via the price projection. |
| priceProjection | PriceProjection |  | The projection of price data you want to receive in the response.  **Please note:** An illustration of the equivalent data priceProjection as displayed on the Betfair website can be viewed [**here**](https://support.developer.betfair.com/hc/en-us/articles/6540502258077-What-Betfair-Exchange-market-data-is-available-from-listMarketBook-Stream-API-) |
| orderProjection | OrderProjection |  | The orders you want to receive in the response. |
| matchProjection | MatchProjection |  | If you ask for orders, specifies the representation of matches. |
| includeOverallPosition | boolean |  | If you ask for orders, returns matches for each selection. Defaults to true if unspecified. |
| partitionMatchedByStrategyRef | boolean |  | If you ask for orders, returns the breakdown of matches by strategy for each selection. Defaults to false if unspecified. |
| customerStrategyRefs | Set<String> |  | If you ask for orders, restricts the results to orders matching any of the specified set of customer defined strategies.  Also, filters which matches by strategy for selections are returned, if partitionMatchedByStrategyRef is true.  An empty set will be treated as if the parameter has been omitted (or null passed). |
| currencyCode | String |  | A Betfair standard currency code. If not specified, the default currency code is used. |
| locale | String |  | The language used for the response. If not specified, the default is returned. |
| matchedSince | Date |  | If you ask for orders, restricts the results to orders that have at least one fragment matched since  the specified date (all matched fragments of such an order will be returned even if some were matched before the specified date).  All EXECUTABLE orders will be returned regardless of matched date. |
| betIds | Set<BetId> |  | If you ask for orders, restricts the results to orders with the specified bet IDs. Omitting this parameter means that all bets will be included in the response. **Please note:** A maximum of 250 betId's can be provided at a time. |

| **Return type** | **Description** |
| --- | --- |
| List< MarketBook > | output data |

| **Throws** | **Description** |
| --- | --- |
| APINGException | Generic exception that is thrown if this operation fails for any reason. |

**Since 1.0.0**
