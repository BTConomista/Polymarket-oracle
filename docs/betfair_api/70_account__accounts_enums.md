# Accounts Enums

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687907>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687907`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## EnumsSubscriptionStatus

#FFFFFF#99CC66SubscriptionStatus

| **Value** | **Description** |
| --- | --- |
| ALL | Any subscription status |
| ACTIVATED | Only activated subscriptions |
| UNACTIVATED | Only unactivated subscriptions |
| CANCELLED | Only cancelled subscriptions |
| EXPIRED | Only expired subscriptions |

Status

#FFFFFF#99CC66Status

| **Value** | **Description** |
| --- | --- |
| SUCCESS | Sucess status |

ItemClass

#FFFFFF#99CC66ItemClass

| **Value** | **Description** |
| --- | --- |
| UNKNOWN | Statement item not mapped to a specific class. All values will be concatenated into a single key/value pair. The key will be 'unknownStatementItem' and the value will be a comma separated string. **Please note:**  This is used to represent commission payment items. |

Wallet

#FFFFFF#99CC66Wallet

| **Value** | **Description** |
| --- | --- |
| UK | The Global Exchange wallet |

IncludeItem

#FFFFFF#99CC66IncludeItem

| **Value** | **Description** |
| --- | --- |
| ALL | Include all items |
| DEPOSITS\_WITHDRAWALS | Include payments only |
| EXCHANGE | Include exchange bets only |
| POKER\_ROOM | Include poker transactions only |

winLose

#FFFFFF#99CC66winLose

| **Value** | **Description** |
| --- | --- |
| RESULT\_ERR | Record has been affected by a unsettlement. There is no impact on the balance for these records, this just a label to say that these are to be corrected. |
| RESULT\_FIX | Record is a correction to the balance to reverse the impact of records shown as in error. If commission has been paid on the original settlement then there will be a second FIX record to reverse the commission. |
| RESULT\_LOST | Loss |
| RESULT\_NOT\_APPLICABLE | Amounts relating to commission payments. |
| RESULT\_WON | Won |
| COMMISSION\_REVERSAL | Betfair have restored the funds to your account that it previously received from you in commission. |

#FFFFFF#99CC66GrantType

granttype

| **Value** | **Description** |
| --- | --- |
| AUTHORIZATION\_CODE | Returned via the Vendor Web API token request. The **authorization code** will be valid for a single use for 10 minutes. |
| REFRESH\_TOKEN | A token that can be used to create a new access token when using the Vendor Web API |

#FFFFFF#99CC66TokenType

tokentype

| **Value** | **Description** |
| --- | --- |
| BEARER | Token type used for Vendor Web API interactions for making requests on a customers behalf. |

#FFFFFF#99CC66 AffiliateRelationStatus

affiliaterelationstatus

| **Value** | **Description** |
| --- | --- |
| INVALID\_USER | Provided vendor client ID is not valid |
| AFFILIATED | Vendor client ID valid and affiliated |
| NOT\_AFFILIATED | Vendor client ID valid but not affiliated |
