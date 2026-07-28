# listCurrentOrders

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687504>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687504`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## Operation

listCurrentOrders

#FFFFFF#C8D0E4listCurrentOrders **CurrentOrderSummaryReport**   **(** Set<String>betIds,Set<String>marketIds, OrderProjection orderProjection, [TimeRange](https://api.developer.betfair.com/services/webapps/docs/display/1smk3cen4v3lu3yomq5qye0ni/Betting+Type+Definitions#BettingTypeDefinitions-TimeRange) placedDateRange, [TimeRange](https://api.developer.betfair.com/services/webapps/docs/display/1smk3cen4v3lu3yomq5qye0ni/Betting+Type+Definitions#BettingTypeDefinitions-TimeRange) dateRange, OrderBy orderBy, SortDir sortDir,intfromRecord,intrecordCount **)**  **throws APINGException** 

Returns a list of your current orders. Optionally you can filter and sort your current orders using the various parameters, setting none of the parameters will return all of your current orders up to a maximum of 1000 bets, ordered BY\_BET and sorted EARLIEST\_TO\_LATEST. To retrieve more than 1000 orders, you need to make use of the fromRecord and recordCount parameters.

Best Practice

To efficiently track new bet matches from a specific time, customers should use a combination of the **dateRange**, **orderBy "BY\_MATCH\_TIME"** and **orderProjection “ALL”** to filter fully/partially matched orders from the list of returned bets. The response will then filter out any bet records that have no matched date and provide a list of betIds in the order which they are fully/partially matched from the date and time specified in the dateRange field.

| Parameter name | Type | Required | Description |
| --- | --- | --- | --- |
| betIds | Set<String> |  | Optionally restricts the results to the specified bet IDs. A maximum of 250 betId's, or a combination of 250 betId's & marketId's are permitted. |
| marketIds | Set<String> |  | Optionally restricts the results to the specified market IDs. A maximum of 250 marketId's, or a combination of 250 marketId's & betId's are permitted. |
| orderProjection | OrderProjection |  | Optionally restricts the results to the specified order status. |
| customerOrderRefs | Set<CustomerOrderRef> |  | Optionally restricts the results to the specified customer order references. |
| customerStrategyRefs | Set<CustomerStrategyRef> |  | Optionally restricts the results to the specified customer strategy references. |
| dateRange | [TimeRange](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Betting+Type+Definitions#BettingTypeDefinitions-TimeRange) |  | Optionally restricts the results to be from/to the specified date, these dates are contextual to the orders being returned and therefore the dates used to filter on will change to placed, matched, voided or settled dates depending on the orderBy. This date is inclusive, i.e. if an order was placed on exactly this date (to the millisecond) then it will be included in the results. If the from is later than the to, no results will be returned. |
| orderBy | OrderBy |  | Specifies how the results will be ordered. If no value is passed in, it defaults to BY\_BET.  Also acts as a filter such that only orders with a valid value in the field being ordered by will be returned (i.e. BY\_VOID\_TIME returns only voided orders, BY\_SETTLED\_TIME (applies to partially settled markets) returns only settled orders and BY\_MATCH\_TIME returns only orders with a matched date (voided, settled, matched orders)). Note that specifying an orderBy parameter defines the context of the date filter applied by the dateRange parameter (placed, matched, voided or settled date) - see the dateRange parameter description (above) for more information. See also the OrderBy type definition. |
| sortDir | SortDir |  | Specifies the direction the results will be sorted in. If no value is passed in, it defaults to EARLIEST\_TO\_LATEST. |
| fromRecord | int |  | Specifies the first record that will be returned. Records start at index zero, not at index one. |
| recordCount | int |  | Specifies how many records will be returned from the index position 'fromRecord'. Note that there is a page size limit of 1000. A value of zero indicates that you would like all records (including and from 'fromRecord') up to the limit. |
| includeItemDescription | boolean |  | If true then extra description parameters are included in the CurrentOrderSummaryReport. |
| includeSourceId | boolean |  | Specifies if sourceIdKey and sourceIdDescription should be returned (if they are available within orders).  Defaults to false. |

| Return type | Description |
| --- | --- |
| CurrentOrderSummaryReport |  |

| Throws | Description |
| --- | --- |
| APINGException | Generic exception that is thrown if this operation fails for any reason. |

**Since 1.0.0**
