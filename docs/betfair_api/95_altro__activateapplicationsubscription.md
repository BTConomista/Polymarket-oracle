# activateApplicationSubscription

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687883>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687883`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## Operation

activateApplicationSubscription

#FFFFFF#C8D0E4activateApplicationSubscription **Status**   **(** **String subscriptionToken** **)**  **throws AccountAPINGException** 

Activates the customers subscription token for an application. **Please note:**  The request is made by the customers account using their session token (X-Authentication header) only.

* The activation of a new subscription token can take up to 2 minutes, therefore, you should ensure that this delay is handled within your application.
* **Please note:** A maximum number of **15,000** subscription **UNACTIVATED** subscriptions tokens can be created at any one time. Attempts to create more subscription tokens will return the error **TOO\_MANY\_REQUESTS** error which will restrict creation of further tokens until existing **UNACTIVATED** subscription tokens have been **ACTIVATED** or **CANCELLED.**

| Parameter name | Type | Required | Description |
| --- | --- | --- | --- |
| subscriptionToken | String |  | Subscription token for activation. |

| Return type | Description |
| --- | --- |
| Status |  |

| Throws | Description |
| --- | --- |
| AccountAPINGException | Generic exception that is thrown if this operation fails for any reason. |

**Since 1.0.0**
