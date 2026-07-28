# listApplicationSubscriptionTokens

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2699922>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2699922`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## Operation

listApplicationSubscriptionTokens

#FFFFFF#C8D0E4listApplicationSubscriptionTokens **List< ApplicationSubscription >**   **(** SubscriptionStatus subscriptionStatus **)**  **throws AccountAPINGException** 

Returns a list of subscription tokens for an application based on the subscription status passed in the request. Returns all subscription token details, including the client reference and vendor client Id associated with the subscription token.

| Parameter name | Type | Required | Description |
| --- | --- | --- | --- |
| subscriptionStatus | SubscriptionStatus |  | Optionally filter response by Subscription status of the token |

| Return type | Description |
| --- | --- |
| List< ApplicationSubscription > | List of subscription tokens for an application |

| Throws | Description |
| --- | --- |
| AccountAPINGException | Generic exception that is thrown if this operation fails for any reason. |

**Since 1.0.0**
