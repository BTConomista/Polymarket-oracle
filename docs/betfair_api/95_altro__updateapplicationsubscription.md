# updateApplicationSubscription

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687031>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687031`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## **Operation**

#FFFFFF#C8D0E4updateApplicationSubscription

**String** [**updateApplicationSubscription**](https://confluence.app.betfair/display/APING/AccountsAPING+BSIDL#AccountsAPINGBSIDL-updateApplicationSubscription) **(** **String vendorClientId**, **int subscriptionLength** **)** **throws AccountAPINGException**

Update an application subscription with a new expiry date. **Please note**: A new subscription token will be created and existing tokens will be cancelled automatically

**Please note:** A subscription token created by this operation \***doesn't\*** need to be activated via **activateApplicationSubscription** as the token is automatically associated with the customers vendorClientId when the request is made.

| Parameter name | Type | Required | Description |
| --- | --- | --- | --- |
| vendorClientId | String |  | The vendor client id for which to update the subscription for |
| subscriptionLength | int |  | How many days the subscription should last. Expiry time will be rounded up to midnight on the date of expiry. Any change to the subscription length will override the customers existing subscription. |

| Return type | Description |
| --- | --- |
| String | Subscription token |

| Throws | Description |
| --- | --- |
| AccountAPINGException | Generic exception that is thrown if this operation fails for any reason |

\*Since \*
