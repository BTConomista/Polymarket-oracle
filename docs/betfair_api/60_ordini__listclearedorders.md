# listClearedOrders

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687749>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687749`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## Operation

#FFFFFF#C8D0E4listClearedOrders

**ClearedOrderSummaryReport** [**listClearedOrders**](/wiki/pages/resumedraft.action?draftId=2687749#listClearedOrders-listClearedOrders) **(** **BetStatus****betStatus**, Set<EventTypeId> eventTypeIds, Set<EventId> eventIds, Set<MarketId> marketIds, Set<RunnerId> runnerIds, Set<BetId> betIds, Side side, TimeRange settledDateRange, GroupBy groupBy, boolean includeItemDescription, String locale, int fromRecord, int recordCount **)** **throws****APINGException**

Returns a list of settled bets based on the bet status, ordered by settled date. To retrieve more than 1000 records, you need to make use of the fromRecord and recordCount parameters.

By default the service will return all available data for the **last 90 days** (see Best Practice note below).  The fields available at each roll-up are available here

### Best Practice

 You should specify a **settledDateRange "from"** date when making requests for data. This reduces the amount of data that requires downloading & improves the speed of the response. Specifying a "from" date of the last call will ensure that only new data is returned.

| **Parameter name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| betStatus | BetStatus |  | Restricts the results to the specified status. |
| eventTypeIds | Set<EventTypeId> |  | Optionally restricts the results to the specified Event Type IDs. |
| eventIds | Set<EventId> |  | Optionally restricts the results to the specified Event IDs. |
| marketIds | Set<Market Id> |  | Optionally restricts the results to the specified market IDs. |
| runnerIds | Set<RunnerId> |  | Optionally restricts the results to the specified Runners. |
| betIds | Set<BetId> |  | Optionally restricts the results to the specified bet IDs. A maximum of 1000 betId's are allowed in a single request. |
| customerOrderRefs | Set<[CustomerOrderRef](http://Betting Type Definitions#MatchId)> |  | Optionally restricts the results to the specified customer order references. |
| customerStrategyRefs | Set<CustomerStrategyRef> |  | Optionally restricts the results to the specified customer strategy references. |
| side | Side |  | Optionally restricts the results to the specified side. |
| settledDateRange | TimeRange |  | Optionally restricts the results to be from/to the specified settled date. This date is inclusive, i.e. if an order was cleared on exactly this date (to the millisecond) then it will be included in the results. If the from is later than the to, no results will be returned.  **Please Note:** if you have a longer running market that is settled at multiple different times then there is no way to get the returned market rollup to only include bets settled in a certain date range, it will always return the overall position from the market including all settlements. |
| groupBy | GroupBy |  | How to aggregate the lines, if not supplied then the lowest level is returned, i.e. bet by bet This is only applicable to SETTLED BetStatus.  **Please note:** Only BET returns details of LAPSED or CANCELLED bets. |
| includeItemDescription | boolean |  | If true then an ItemDescription object is included in the response. |
| locale | String |  | The language used for the itemDescription. If not specified, the customer account default is returned. |
| fromRecord | int |  | Specifies the first record that will be returned. Records start at index zero. |
| recordCount | int |  | Specifies how many records will be returned, from the index position 'fromRecord'. Note that there is a page size limit of 1000. A value of zero indicates that you would like all records (including and from 'fromRecord') up to the limit. |
| includeSourceId | boolean |  | Specifies if sourceIdKey and sourceIdDescription should be returned (if they are available within orders). Defaults to false. |

| **Return type** | **Description** |
| --- | --- |
| ClearedOrderSummaryReport |  |

| **Throws** | **Description** |
| --- | --- |
| APINGException | Generic exception that is thrown if this operation fails for any reason. |

**Since 1.0.0**
