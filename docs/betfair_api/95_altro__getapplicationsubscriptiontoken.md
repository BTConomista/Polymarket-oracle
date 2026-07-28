# getApplicationSubscriptionToken

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2699921>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2699921`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## Operation

getApplicationSubscriptionToken

#FFFFFF#C8D0E4getApplicationSubscriptionToken**String**  **(** int subscriptionLength **)**  **throws AccountAPINGException** 

Used to create new subscription tokens for an application. Returns the newly generated subscription token which can be provided to the end user.

**Please note:** A maximum number of **15,000** subscription **UNACTIVATED** subscriptions tokens can be created at any one time. Attempts to create more subscription tokens will return the error **TOO\_MANY\_REQUESTS** error which will restrict creation of further tokens until existing **UNACTIVATED** subscription tokens have been **ACTIVATED** or **CANCELLED**

| Parameter name | Type | Required | Description |
| --- | --- | --- | --- |
| subscriptionLength | int |  | How many days the subscription should last. Open ended if value not supplied. Expiry time will be rounded up to midnight on the date of expiry. |
| clientReference | String |  | Any client reference for this subscription token request. |

| Return type | Description |
| --- | --- |
| String | Subscription token |

| Throws | Description |
| --- | --- |
| AccountAPINGException | Generic exception that is thrown if this operation fails for any reason. |

**Since 1.0.0**
