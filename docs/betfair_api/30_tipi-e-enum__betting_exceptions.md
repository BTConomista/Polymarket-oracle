# Betting Exceptions

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687450>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687450`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## Exceptions

APINGException

#FFFFFF#E4B8D6APINGException

This exception is thrown when an operation fails

| Error code | Description |
| --- | --- |
| TOO\_MUCH\_DATA | The operation requested too much data, exceeding the Market Data Request Limits. You must adjust your request parameters to stay with the documented limits. |
| INVALID\_INPUT\_DATA | The data input is invalid. A specific description is returned via errorDetails as shown below.  **Please note:** if the number of **placeOrders, updateOrders, replaceOrders**, or **cancelOrders** instructions exceeds the documented limit you will also receive this error. |
| INVALID\_SESSION\_INFORMATION | The session token hasn't been provided, is invalid or has expired. Login again to create a new session |
| NO\_APP\_KEY | An application key header ('X-Application') has not been provided in the request. |
| NO\_SESSION | A session token header ('X-Authentication') has not been provided in the request |
| UNEXPECTED\_ERROR | An unexpected internal error occurred that prevented successful request processing. |
| INVALID\_APP\_KEY | The application key passed is invalid or is not present |
| TOO\_MANY\_REQUESTS | There are too many pending (in-flght) requests e.g. a  with Order/Match projections is limited to 3 concurrent requests. The error also applies to:   * , listMarketProfitAndLoss and  if you have 3 or more requests currently in execution. * , cancelOrders. ,  if the number of transactions (instructions) submitted exceeds 1000 in a single second.   For more details relating to this error please see **[FAQ's](https://support.developer.betfair.com/hc/en-us/articles/360000406111-Why-am-I-receiving-the-TOO-MANY-REQUESTS-error-)** |
| SERVICE\_BUSY | The service is currently too busy to service this request. |
| TIMEOUT\_ERROR | The Internal call to downstream service timed out. **Please note:** If a TIMEOUT error occurs on a placeOrders/replaceOrders request, you should check listCurrentOrders to verify the status of your bets before placing further orders. Please Note: Timeouts will occur after 5 seconds of attempting to process the bet but please allow up to 15 seconds for a timed out order to appear. After this time any unprocessed bets will automatically be Lapsed and no longer be available on the Exchange. |
| REQUEST\_SIZE\_EXCEEDS\_LIMIT | The request exceeds the request size limit. Requests are limited to a total of 250 betId’s/marketId’s (or a combination of both). |
| ACCESS\_DENIED | The calling client is not permitted to perform the specific action e.g. they have an App Key restriction in place or attempting to place a bet from a restricted jurisdiction. |

| **Other parameters** | **Type** | **Required** | **Description** | **Values** |
| --- | --- | --- | --- | --- |
| errorDetailserrodetails | String |  | the stack trace of the error | "market id passed is invalid"  "locale must use valid iso-639 locale names"  "currency must use valid iso2 currency code name"  "country code must use valid iso2 country code name"  "text query has invalid content"  "language must use valid iso language name" |
| requestUUID | String |  |  |  |

#FFFFFF#E4B8D6Generic JSON-RPC Exceptions

| Error Code | Description |
| --- | --- |
| -32700 | Invalid JSON was received by the server. An error occurred on the server while parsing the JSON text. |
| -32601 | Method not found |
| -32602 | Problem parsing the parameters, or a mandatory parameter was not found |
| -32603 | Internal JSON-RPC error |
