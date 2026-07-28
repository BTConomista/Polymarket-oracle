# getVendorDetails

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687719>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687719`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

#FFFFFF#C8D0E4getVendorDetails

**VendorDetails**  **(** **String vendorId** **)** **throws AccountAPINGException**

Return details about a vendor from its identifier. Response includes Vendor Name and URL.

| Parameter name | Type | Required | Description |
| --- | --- | --- | --- |
| vendorId | String |  | The vendor's public identifier |

| Return type | Description |
| --- | --- |
| VendorDetails | Response object containing the vendor and the redirect url |

| Throws | Description |
| --- | --- |
| AccountAPINGException |  |

**Since 1.0.0**
