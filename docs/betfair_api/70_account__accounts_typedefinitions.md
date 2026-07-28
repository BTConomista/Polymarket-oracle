# Accounts TypeDefinitions

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687852>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687852`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## Type definitions

Transfer

#FFFFFF#FFCC33TransferResponse

Transfer operation response

| Field name | Type | Required | Description |
| --- | --- | --- | --- |
| transactionId | String |  | The id of the transfer transaction that will be used in tracking the transfers between the wallets |

ApplicationSubscription

#FFFFFF#FFCC33ApplicationSubscription

Application subscription details

| Field name | Type | Required | Description |
| --- | --- | --- | --- |
| subscriptionToken | String |  | Application key identifier |
| expiryDateTime | Date |  | Subscription Expiry date |
| expiredDateTime | Date |  | Subscription Expired date |
| createdDateTime | Date |  | Subscription Create date |
| activationDateTime | Date |  | Subscription Activation date |
| cancellationDateTime | Date |  | Subscription Cancelled date |
| subscriptionStatus | SubscriptionStatus |  | Subscription status |
| clientReference | String |  | Client reference |
| vendorClientId | String |  | Vendor client Id |

SubscriptionHistory

#FFFFFF#FFCC33Subscription History

Application subscription history details

| Field name | Type | Required | Description |
| --- | --- | --- | --- |
| subscriptionToken | String |  | Application key identifier |
| expiryDateTime | Date |  | Subscription Expiry date |
| expiredDateTime | Date |  | Subscription Expired date |
| createdDateTime | Date |  | Subscription Create date |
| activationDateTime | Date |  | Subscription Activation date |
| cancellationDateTime | Date |  | Subscription Cancelled date |
| subscriptionStatus | SubscriptionStatus |  | Subscription status |
| clientReference | String |  | Client reference |

AccountSubscription

#FFFFFF#FFCC33AccountSubscription

Application subscription details

| Field name | Type | Required | Description |
| --- | --- | --- | --- |
| subscriptionTokens | List<  > |  | Lis t of subscription token details |
| applicationName | String |  | Application name |
| applicationVersionId | String |  | Application version Id |

SubscriptionTokenInfo

#FFFFFF#FFCC33SubscriptionTokenInfo

Subscription token information

| Field name | Type | Required | Description |
| --- | --- | --- | --- |
| subscriptionToken | String |  | Subscription token |
| activatedDateTime | Date |  | Subscription Activated date |
| expiryDateTime | Date |  | Subscription Expiry date |
| expiredDateTime | Date |  | Subscription Expired date |
| cancellationDateTime | Date |  | Subscription Cancelled date |
| subscriptionStatus | SubscriptionStatus |  | Subscription status |

DeveloperApp

#FFFFFF#FFCC33DeveloperApp

Describes developer/vendor specific application

| Field name | Type | Required | Description |
| --- | --- | --- | --- |
| appName | String |  | The unique name of the application |
| appId | long |  | A unique id of this application |
| appVersions | List<  > |  | The application versions (including application keys) |

DeveloperAppVersion

#FFFFFF#FFCC33DeveloperAppVersion

Describes a version of an external application

| Field name | Type | Required | Description |
| --- | --- | --- | --- |
| owner | String |  | The user who owns the specific version of the application |
| versionId | long |  | The unique Id of the application version |
| version | String |  | The version identifier string such as 1.0, 2.0. Unique for a given application. |
| applicationKey | String |  | The unqiue application key associated with this application version |
| delayData | boolean |  | Indicates whether the data exposed by platform services as seen by this application key is delayed or realtime. |
| subscriptionRequired | boolean |  | Indicates whether the application version needs explicit subscription |
| ownerManaged | boolean |  | Indicates whether the application version needs explicit management by the software owner. A value of false indicates, this is a version meant for personal developer use. |
| active | boolean |  | Indicates whether the application version is currently active |
| vendorId | String |  | Public unique string provided to the Vendor that they can use to pass to the Betfair API in order to identify themselves. |
| vendorSecret | String |  | Private unique string provided to the Vendor that they pass with certain calls to confirm their identity.  Linked to a particular App Key. |

AccountFundsResponse

#FFFFFF#FFCC33AccountFundsResponse

Response for retrieving available to bet.

| Field name | Type | Required | Description |
| --- | --- | --- | --- |
| availableToBetBalance | double |  | Amount available to bet. |
| exposure | double |  | Current exposure. |
| retainedCommission | double |  | Sum of retained commission. |
| exposureLimit | double |  | Exposure limit. |
| discountRate | double |  | User Discount Rate.  **Please note:** **Betfair AUS/NZ** customers should not rely on this to determine their discount rates which are now applied at the account level. |
| pointsBalance | int |  | The Betfair points balance. |

AccountDetailsResponse

#FFFFFF#FFCC33AccountDetailsResponse

Response for Account details.

| Field name | Type | Required | Description |
| --- | --- | --- | --- |
| currencyCode | String |  | Default user currency Code. See Currency Parameters for minimum bet sizes relating to each currency. |
| firstName | String |  | First Name. |
| lastName | String |  | Last Name. |
| localeCode | String |  | Locale Code. |
| region | String |  | Region based on users zip/postcode (ISO 3166-1 alpha-3 format). Defaults to GBR if zip/postcode cannot be identified. |
| timezone | String |  | User Time Zone. |
| discountRate | double |  | User Discount Rate.   **Please note:** **Betfair AUS/NZ** customers should not rely on this to determine their discount rates which are now applied at the account level. |
| pointsBalance | int |  | The Betfair points balance. |
| countryCode | String |  | The customer's country of residence (ISO 2 Char format) |

AccountStatementReport

#FFFFFF#FFCC33AccountStatementReport

A container representing search results.

| Field name | Type | Required | Description |
| --- | --- | --- | --- |
| accountStatement | List<> |  | The list of statement items returned by your request. |
| moreAvailable | boolean |  | Indicates whether there are further result items beyond this page. |

StatementItem

#FFFFFF#FFCC33StatementItem

Summary of a cleared order.

| Field name | Type | Required | Description |
| --- | --- | --- | --- |
| refId | String |  | An external reference, eg. equivalent to betId in the case of an exchange bet statement item. |
| itemDate | Date |  | The date and time of the statement item, eg. equivalent to settledData for an exchange bet statement item. (in ISO-8601 format, not translated) |
| amount | double |  | The amount of money the balance is adjusted by |
| balance | double |  | Account balance. |
| itemClass | ItemClass |  | Class of statement item. This value will determine which set of keys will be included in itemClassData |
| itemClassData | Map<String,String> |  | Key value pairs describing the current statement item. The set of keys will be determined by the itemClass |
| legacyData |  |  | Set of fields originally returned from APIv6. Provided to facilitate migration from APIv6 to API-NG, and ultimately onto itemClass and itemClassData |

StatementLegacyData

#FFFFFF#FFCC33StatementLegacyData

Summary of a cleared order.

| Field name | Type | Required | Description |
| --- | --- | --- | --- |
| avgPrice | double |  | The average matched price of the bet (null if no part has been matched) |
| betSize | double |  | The amount of the stake of your bet. (0 for commission payments or deposit/withdrawals) |
| betType | String |  | Back or lay |
| betCategoryType | String |  | Exchange, Market on Close SP bet, or Limit on Close SP bet. |
| commissionRate | String |  | Commission rate on market |
| eventId | long |  | **Please note:** this is the Id of the market without the associated exchangeId |
| eventTypeId | long |  | Event Type |
| fullMarketName | String |  | Full Market Name. For card payment items, this field contains the card name |
| grossBetAmount | double |  | The winning amount to which commission is applied. |
| marketName | String |  | Market Name. For card transactions, this field indicates the type of card transaction (deposit, deposit fee, or withdrawal). |
| marketType | marketType |  | Market type. For account deposits and withdrawals, marketType is set to NOT\_APPLICABLE. |
| placedDate | Date |  | Date and time of bet placement |
| selectionId | long |  | Id of the selection (this will be the same for the same selection across markets) |
| selectionName | String |  | Name of the selection |
| startDate | Date |  | Date and time at the bet portion was settled |
| transactionType | String |  | Debit or credit |
| transactionId | long |  | The unique reference Id assigned to account deposit and withdrawals. |
| winLose | winLose |  | Win or loss |
| deadHeatPriceDivisor | double |  | In the instance of a dead heat, this field will indicate the number of winners involved in the dead heat (null otherwise) |
| avgPriceRaw | double |  | Currently returns same value as avgPrice. Once released will display the average matched price of the bet with no rounding applied |

TimeRange

#FFFFFF#FFCC33TimeRange

TimeRange

| Field name | Type | Required | Description |
| --- | --- | --- | --- |
| from | Date |  | from, format: ISO 8601) |
| to | Date |  | to, format: ISO 8601 |

CurrencyRate

#FFFFFF#FFCC33CurrencyRate

Currency rate

| Field name | Type | Required | Description |
| --- | --- | --- | --- |
| currencyCode | String |  | Three letter ISO 4217 code |
| rate | double |  | Exchange rate for the currency specified in the request |

#FFFFFF#FFCC33AuthorisationResponse

**AuthorisationResponse authorisationresponse**

Wrapper object containing authorisation code and redirect URL for web vendors

| Field name | Type | Required | Description |
| --- | --- | --- | --- |
| authorisationCode | String |  | The authorisation code |
| redirectUrl | String |  | URL to redirect the user to the vendor page |

#FFFFFF#FFCC33SubscriptionOptions

****SubscriptionOptions subscriptionoptions****

Wrapper object containing details of how a subscription should be created

| Field name | Type | Required | Description |
| --- | --- | --- | --- |
| subscription\_length | int |  | How many days should a created subscription last for. Open ended subscription created if value not provided.  Relevant only if createdSubscription is true. |
| subscription\_token | String |  | An existing subscription token that the caller wishes to be activated instead of creating a new one.  Ignored is createSubscription is true. |
| client\_reference | String |  | Any client reference for this subscription token request. |

#FFFFFF#FFCC33VendorAccessTokenInfo

****vendoraccesstokeninfo****

Wrapper object containing UserVendorSessionToken, RefreshToken and optionally a Subscription Token if one was created

| Field name | Type | Required | Description |
| --- | --- | --- | --- |
| access\_token | String |  | Session token used by web vendors |
| token\_type | TokenType |  | Type of the token |
| expires\_in | long |  | How long until the token expires |
| refresh\_token | String |  | Token used to refresh the session token in future |
| application\_subscription | [ApplicationSubscription](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Accounts+TypeDefinitions) |  | Object containing the vendor client id and optionally some subscription information |

#FFFFFF#FFCC33VendorDetails

****vendordetails****

Wrapper object containing vendor name and redirect url

| Field name | Type | Required | Description |
| --- | --- | --- | --- |
| appVersionId | long |  | Internal id of the application |
| vendorName | String |  | Vendor name |
| redirectUrl | String |  | URL to be redirected to |

#FFFFFF#FFCC33AffiliateRelation

affiliaterelationWrapper object containing affiliate relation details

| Field name | Type | Required | Description |
| --- | --- | --- | --- |
| vendorClientId | String |  | ID of user |
| status | AffiliateRelationStatus |  | The affiliate relation status |
