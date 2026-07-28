# token

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687712>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687712`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

token

#FFFFFF#C8D0E4token

**VendorAccessTokenInfo**  **(** **String client\_id**, **GrantType grant\_type**, String code, **String client\_secret**, String refresh\_token **)** **throws AccountAPINGException**

Generate web vendor session based on a standard session identifiable by auth code, vendor secret and app key

| Parameter name | Type | Required | Description |
| --- | --- | --- | --- |
| client\_id | String |  | The vendor's vendorId |
| grant\_type | GrantType |  | Whether the vendor is using an authorisation code or a refresh token to get a session |
| code | String |  | The authorisation code used to lookup the session to be returned |
| client\_secret | String |  | The vendor's private key used to verify their identity |
| refresh\_token | String |  | The vendor's refresh token if the grant\_type is refresh\_token |

| Return type | Description |
| --- | --- |
| VendorAccessTokenInfo | Response object containing VendorAccessToken, RefreshToken and optionally a Subscription Token if one was created |

| Throws | Description |
| --- | --- |
| AccountAPINGException |  |

**Since 1.0.0**
