# Accounts Exceptions

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687902>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687902`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## ExceptionsAccountAPINGException

#FFFFFF#E4B8D6AccountAPINGException

This exception is thrown when an operation fails

| **Error code** | **Description** |
| --- | --- |
| INVALID\_INPUT\_DATA | Invalid input data. Please check the format of your request.  **Please note:** if the number of **placeOrders, updateOrders, replaceOrders**, or **cancelOrders** instructions exceeds the documented limit you will also receive this error. |
| INVALID\_SESSION\_INFORMATION | The session token hasn't been provided, is invalid or has expired. You must login again to creata a new session token. |
| UNEXPECTED\_ERROR | An unexpected internal error occurred that prevented successful request processing. |
| INVALID\_APP\_KEY | The application key passed is invalid or is not present. |
| SERVICE\_BUSY | The service is currently too busy to service this request. |
| TIMEOUT\_ERROR | nThe internal call to downstream service timed out |
| DUPLICATE\_APP\_NAME | Duplicate application name. |
| APP\_KEY\_CREATION\_FAILED | Creating application key version has failed. Please check that your application name is unique and doesn't contain your Betfair username. |
| APP\_CREATION\_FAILED | Application creation has been failed |
| NO\_SESSION | A session token header ('X-Authentication') has not been provided in the request.  **Please note:** The same error is returned by the Keep Alive operation if the X-Authentication header is provided but the session value is invalid or if the session has expired. |
| NO\_APP\_KEY | An application key header ('X-Application') has not been provided in the request |
| SUBSCRIPTION\_EXPIRED | An application key is required for this operation |
| INVALID\_SUBSCRIPTION\_TOKEN | The subscription token provided doesn't exist |
| TOO\_MANY\_REQUESTS | Too many requests.  For more details relating to this error please see [**FAQ's**](https://support.developer.betfair.com/hc/en-us/articles/360000406111-Why-am-I-receiving-the-TOO-MANY-REQUESTS-error-) |
| INVALID\_CLIENT\_REF | Invalid length for the client reference |
| WALLET\_TRANSFER\_ERROR | There was a problem transferring funds between your wallets |
| INVALID\_VENDOR\_CLIENT\_ID | The vendor client ID is not subscribed to this Application Key. |
| USER\_NOT\_SUBSCRIBED | The user making the request is not subscribed to the Application Key. they are trying to perform the action on (e.g. creating an Authorisation Code). |
| INVALID\_SECRET | The vendor making the request has provided a vendor secret that does not match our records. |
| INVALID\_AUTH\_CODE | The vendor making the request has not provided a valid authorisation cod |
| INVALID\_GRANT\_TYPE | The vendor making the request has not provided a valid grant\_type, or the grant\_type they have passed does not match the parameters (authCode/refreshToken) |
| CUSTOMER\_ACCOUNT\_CLOSED | A token could not be created because the customer's account is CLOSED. |
| SESSION\_LIMIT\_EXCEEDED | A token could not be refreshed because the end user's session limit has expired. |

| **Other parameters** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| errorDetails | String |  | the stack trace of the error |
| requestUUID | String |  |  |
