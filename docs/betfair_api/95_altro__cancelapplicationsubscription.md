# cancelApplicationSubscription

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2699920>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2699920`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## Operation

cancelApplicationSubscription

#FFFFFF#C8D0E4cancelApplicationSubscription **Status**   **(** **String subscriptionToken** **)**  **throws AccountAPINGException** 

Cancel the subscription token. The customers subscription will no longer be active once cancelled.

| Parameter name | Type | Required | Description |
| --- | --- | --- | --- |
| subscriptionToken | String |  | Subscription token to cancel |

| Return type | Description |
| --- | --- |
| Status |  |

| Throws | Description |
| --- | --- |
| AccountAPINGException | Generic exception that is thrown if this operation fails for any reason. |

**Since 1.0.0**
