# getApplicationSubscriptionHistory

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687103>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687103`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

**getApplicationSubscriptionHistory**

**List<[SubscriptionHistory](http://docs.developer.betfair.com/docs/display/1smk3cen4v3lu3yomq5qye0ni/Accounts+TypeDefinitions#AccountsTypeDefinitions-SubscriptionHistory)>** [**getApplicationSubscriptionHistory**](https://confluence.app.betfair/display/APING/AccountsAPING+BSIDL#AccountsAPINGBSIDL-getApplicationSubscriptionHistory) **(** **String vendorClientId** **)** **throws AccountAPINGException**

Returns a list of subscriptions tokens that have been associated with the customers account.  This allows a vendor to identify if a customer has a previous subscription to their application and the status of each subscription.

| Parameter name | Type | Required | Description |
| --- | --- | --- | --- |
| vendorClientId  applicationKey | String  String |  | The unique customer identifier  The unique application identifier |

| Return type | Description |
| --- | --- |
| List<SubscriptionHistory> | List of subscription tokens associated with the account |

| Throws | Description |
| --- | --- |
| [AccountAPINGException](https://confluence.app.betfair/display/APING/AccountsAPING+BSIDL#AccountsAPINGBSIDL-AccountAPINGException) | Generic exception that is thrown if this operation fails for any reason. |

\*Since \*
