# Documentazione API Betfair — copia di lavoro locale

> **Attribuzione.** Il contenuto di questa cartella è **testo di
> Betfair**, non del progetto. Fonte unica:
> **Betfair Developer Program — *Betfair Exchange API Documentation***
> <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/overview>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`). Estratto il **2026-07-28** con
> `scripts/fetch_betfair_docs.py`, che è ri-eseguibile: **in caso di
> divergenza vince sempre la pagina online**, che può essere più recente.

**Perché esiste.** Alla Fase 109-bis un bug del parser dello stream (il
campo `img`) è costato una correzione che si sarebbe evitata leggendo la
specifica ufficiale *prima* di scrivere il codice. Questa copia serve a
far partire ogni lavoro futuro su Betfair da dentro il repo.

**Cosa NON c'è**: le note di rilascio (una ventina di pagine di
cronologia) e le traduzioni (spagnolo, portoghese, rumeno) — escluse
dallo script perché non servono al lavoro tecnico.

## Le due API di Betfair, da non confondere

| | a cosa serve | dove è documentata |
|---|---|---|
| **Exchange API** (live) | quote in tempo reale, piazzare scommesse, stream dei prezzi | questa cartella, file `00`-`80` |
| **Historical Data** | scaricare i file storici già registrati | `90_historical_data_api.md` (fonte diversa) |

Si toccano in un punto che ci riguarda: **i file storici sono
registrazioni dello stream** descritto in `40_stream__*`, quindi quella
specifica vale anche per il parser di
`scripts/fetch_betfair_historic.py`.

## ⭐ Parti da qui

**[`99_guida_pratica_progetto.md`](99_guida_pratica_progetto.md)** — l'unico
file di questa cartella scritto DAL progetto: come ottenere il token, i
vincoli reali già verificati (sessione da 20 minuti sull'exchange italiano,
geo-blocco), la domanda ancora aperta per l'assistenza, e cosa possiamo
farci in ordine di valore.

## Le pagine che servono per prime

- **`40_stream__exchange_stream_api.md`** — il formato dei messaggi
  (`mcm`, `mc`, `rc`, `ltp`, `img`, `marketDefinition.inPlay`): è la
  specifica contro cui va verificato il parser dei file storici.
- **`30_tipi-e-enum__betting_enums.md`** — i valori ammessi, fra cui i
  tipi di mercato (`MATCH_ODDS`, `OVER_UNDER_25`, …).
- **`10_accesso__*`** — come si ottiene un token di sessione (`ssoid`)
  e a cosa serve l'application key.
- **`50_mercati-nazionali__betting_on_italian_exchange.md`** — regole
  dell'exchange italiano: rilevante perché l'account del progetto è
  italiano e `historicdata.betfair.com` risponde 403 per regione.

## Indice completo


### 00 · guida

- [Additional Information](00_guida__additional_information.md)
- [API Demo Tools](00_guida__api_demo_tools.md)
- [Best Practice](00_guida__best_practice.md)
- [Betfair API Docs](00_guida__betfair_api_docs.md)
- [Developer Support](00_guida__developer_support.md)
- [Getting Started](00_guida__getting_started.md)
- [Interface Definition Documents](00_guida__interface_definition_documents.md)
- [Optimizing API Application Performance](00_guida__optimizing_api_application_performance.md)
- [Reference Guide](00_guida__reference_guide.md)
- [Reference Guide (Offline Copy)](00_guida__reference_guide_offline_copy.md)
- [Sample Code, Client Libraries & Tutorials](00_guida__sample_code_client_libraries_tutorials.md)

### 10 · accesso

- [Application Keys](10_accesso__application_keys.md)
- [Certificate Generation With XCA](10_accesso__certificate_generation_with_xca.md)
- [Interactive Login - API Endpoint](10_accesso__interactive_login_api_endpoint.md)
- [Interactive Login - Desktop Application](10_accesso__interactive_login_desktop_application.md)
- [Login & Session Management](10_accesso__login_session_management.md)
- [Non-Interactive (bot) login](10_accesso__non_interactive_bot_login.md)
- [token](10_accesso__token.md)

### 20 · betting

- [Betfair Starting Price Betting (BSP)](20_betting__betfair_starting_price_betting_bsp.md)
- [Betting API](20_betting__betting_api.md)
- [listCompetitions](20_betting__listcompetitions.md)
- [listCountries](20_betting__listcountries.md)
- [listEvents](20_betting__listevents.md)
- [listEventTypes](20_betting__listeventtypes.md)
- [listMarketBook](20_betting__listmarketbook.md)
- [listMarketCatalogue](20_betting__listmarketcatalogue.md)
- [listMarketProfitAndLoss](20_betting__listmarketprofitandloss.md)
- [listMarketTypes](20_betting__listmarkettypes.md)
- [listRunnerBook](20_betting__listrunnerbook.md)
- [listTimeRanges](20_betting__listtimeranges.md)
- [listVenues](20_betting__listvenues.md)
- [Market Data Request Limits](20_betting__market_data_request_limits.md)
- [Navigation Data For Applications](20_betting__navigation_data_for_applications.md)

### 30 · tipi-e-enum

- [Betting Enums](30_tipi-e-enum__betting_enums.md)
- [Betting Exceptions](30_tipi-e-enum__betting_exceptions.md)
- [Betting Type Definitions](30_tipi-e-enum__betting_type_definitions.md)

### 40 · stream

- [Exchange Stream API](40_stream__exchange_stream_api.md)

### 50 · mercati-nazionali

- [Betting On Italian Exchange](50_mercati-nazionali__betting_on_italian_exchange.md)
- [Betting on Spanish Exchange](50_mercati-nazionali__betting_on_spanish_exchange.md)

### 60 · ordini

- [cancelOrders](60_ordini__cancelorders.md)
- [Heartbeat API](60_ordini__heartbeat_api.md)
- [listClearedOrders](60_ordini__listclearedorders.md)
- [listClearedOrders - Roll-up Fields Available](60_ordini__listclearedorders_roll_up_fields_available.md)
- [listCurrentOrders](60_ordini__listcurrentorders.md)
- [placeOrders](60_ordini__placeorders.md)
- [replaceOrders](60_ordini__replaceorders.md)
- [updateOrders](60_ordini__updateorders.md)

### 70 · account

- [Accounts API](70_account__accounts_api.md)
- [Accounts Enums](70_account__accounts_enums.md)
- [Accounts Exceptions](70_account__accounts_exceptions.md)
- [Accounts TypeDefinitions](70_account__accounts_typedefinitions.md)
- [getAccountDetails](70_account__getaccountdetails.md)
- [getAccountFunds](70_account__getaccountfunds.md)
- [getAccountStatement](70_account__getaccountstatement.md)
- [listCurrencyRates](70_account__listcurrencyrates.md)
- [Race Status API](70_account__race_status_api.md)

### 80 · linguaggi

- [C#](80_linguaggi__c.md)
- [Excel & VBA Sample](80_linguaggi__excel_vba_sample.md)
- [Java](80_linguaggi__java.md)
- [Javascript](80_linguaggi__javascript.md)
- [PHP](80_linguaggi__php.md)
- [Python](80_linguaggi__python.md)

### 95 · altro

- [activateApplicationSubscription](95_altro__activateapplicationsubscription.md)
- [cancelApplicationSubscription](95_altro__cancelapplicationsubscription.md)
- [createDeveloperAppKeys](95_altro__createdeveloperappkeys.md)
- [getAffiliateRelation](95_altro__getaffiliaterelation.md)
- [getApplicationSubscriptionHistory](95_altro__getapplicationsubscriptionhistory.md)
- [getApplicationSubscriptionToken](95_altro__getapplicationsubscriptiontoken.md)
- [getDeveloperAppKeys](95_altro__getdeveloperappkeys.md)
- [getVendorClientId](95_altro__getvendorclientid.md)
- [getVendorDetails](95_altro__getvendordetails.md)
- [isAccountSubscribedToWebApp](95_altro__isaccountsubscribedtowebapp.md)
- [listAccountSubscriptionTokens](95_altro__listaccountsubscriptiontokens.md)
- [listApplicationSubscriptionTokens](95_altro__listapplicationsubscriptiontokens.md)
- [revokeAccessToWebApp](95_altro__revokeaccesstowebapp.md)
- [updateApplicationSubscription](95_altro__updateapplicationsubscription.md)
- [Vendor Services API](95_altro__vendor_services_api.md)
