# listRunnerBook

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687847>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687847`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

**List<MarketBook>** **listRunnerBook** **(** **MarketId marketId**, **SelectionId selectionId**, double handicap, [PriceProjection](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Betting+Type+Definitions#BettingTypeDefinitions-PriceProjection) priceProjection, [OrderProjection](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Betting+Enums#BettingEnums-OrderProjection) orderProjection, [MatchProjection](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Betting+Enums#BettingEnums-MatchProjection) matchProjection, boolean includeOverallPosition, boolean partitionMatchedByStrategyRef, Set<String> customerStrategyRefs, StringcurrencyCode,Stringlocale, Date matchedSince, Set<[BetId](http://docs.developer.betfair.com/docs/display/1smk3cen4v3lu3yomq5qye0ni/Betting+Type+Definitions)> betIds**)****throws [APINGException](http://docs.developer.betfair.com/docs/display/1smk3cen4v3lu3yomq5qye0ni/Betting+Exceptions#BettingExceptions-APINGException)**

Returns a list of dynamic data about **a market** and a **specified runner**. Dynamic data includes prices, the status of the market, the status of selections, the traded volume, and the status of any orders you have placed in the market..

listRunnerBook behaviourYou can only pass in one marketId and one selectionId in that market per request. If the selectionId being passed in is not a valid one / doesn’t belong in that market then the call will still work but only the market data is returned

runnerBook

| Parameter name | Type | Required | Description |
| --- | --- | --- | --- |
| marketId | MarketId |  | The unique id for the market.. |
| selectionId | SelectionId |  | The unique id for the selection in the market. |
| handicap | double |  | The handicap associated with the runner in case of Asian handicap market |
| priceProjection | [PriceProjection](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Betting+Type+Definitions#BettingTypeDefinitions-PriceProjection) |  | The projection of price data you want to receive in the response. |
| orderProjection | [OrderProjection](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Betting+Enums#BettingEnums-OrderProjection) |  | The orders you want to receive in the response. |
| matchProjection | [MatchProjection](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Betting+Enums#BettingEnums-MatchProjection) |  | If you ask for orders, specifies the representation of matches. |
| includeOverallPosition | boolean |  | If you ask for orders, returns matches for each selection. Defaults to true if unspecified. |
| partitionMatchedByStrategyRef | boolean |  | If you ask for orders, returns the breakdown of matches by strategy for each selection. Defaults to false if unspecified. |
| customerStrategyRefs | Set<String> |  | If you ask for orders, restricts the results to orders matching any of the specified set of customer defined strategies.  Also filters which matches by strategy for selections are returned, if partitionMatchedByStrategyRef is true.  An empty set will be treated as if the parameter has been omitted (or null passed). |
| currencyCode | String |  | A Betfair standard currency code. If not specified, the default currency code is used. |
| locale | String |  | The language used for the response. If not specified, the default is returned. |
| matchedSince | Date |  | If you ask for orders, restricts the results to orders that have at least one fragment matched since  the specified date (all matched fragments of such an order will be returned even if some were matched before the specified date).  All EXECUTABLE orders will be returned regardless of matched date. |
| betIds | Set<[BetId](http://docs.developer.betfair.com/docs/display/1smk3cen4v3lu3yomq5qye0ni/Betting+Type+Definitions#BettingTypeDefinitions-BettId)> |  | If you ask for orders, restricts the results to orders with the specified bet IDs. Omitting this parameter means that all bets will be included in the response. **Please note:** A maximum of 250 betId's can be provided at a time. |

| Return type | Description |
| --- | --- |
| List< MarketBook > | output data |

| Throws | Description |
| --- | --- |
| [APINGException](http://docs.developer.betfair.com/docs/display/1smk3cen4v3lu3yomq5qye0ni/Betting+Exceptions#BettingExceptions-APINGException) | Generic exception that is thrown if this operation fails for any reason. |

**Since 1.0.0**
