# Betting Type Definitions

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687465`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## Type Definitions

MarketCatalogue

#FFFFFF#FFCC33MarketFilter

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| textQuery | String |  | Restrict markets by any text associated with the Event name. You can include a wildcard (\*) character as long as it is not the first character.  **Please note -** the textQuery field doesn't evaluate market or selection names. |
| exchangeIds | Set<String> |  | **DEPRECATED** |
| eventTypeIds | Set<String> |  | Restrict markets by event type associated with the market. (i.e., Football, Hockey, etc) |
| eventIds | Set<String> |  | Restrict markets by the event id associated with the market. |
| competitionIds | Set<String> |  | Restrict markets by the competitions associated with the market. |
| marketIds | Set<String> |  | Restrict markets by the market id associated with the market. |
| venues | Set<String> |  | Restrict markets by the venue associated with the market. Currently, only Horse & Greyhound racing markets have venues. |
| bspOnly | boolean |  | Restrict to bsp markets only, if True or non-bsp markets if False. If not specified then returns both BSP and non-BSP markets |
| turnInPlayEnabled | boolean |  | Restrict to markets that will turn in play if True or will not turn in play if false. If not specified, returns both. |
| inPlayOnly | boolean |  | Restrict to markets that are currently in play if True or are not currently in play if false. If not specified, returns both. |
| marketBettingTypes | Set< MarketBettingType > |  | Restrict to markets that match the betting type of the market (i.e. Odds, Asian Handicap Singles, Asian Handicap Doubles or Line) |
| marketCountries | Set<String> |  | Restrict to markets that are in the specified country or countries.  **Please note: the** default value is 'GB' when the correct country code cannot be determined. |
| marketTypeCodes | Set<String> |  | Restrict to markets that match the type of the market (i.e., MATCH\_ODDS, HALF\_TIME\_SCORE). You should use this instead of relying on the market name as the market type codes are the same in all locales. **Please note:** All market types are available via the **listMarketTypes** operations. |
| marketStartTime | [TimeRange](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#TimeRange) |  | Restrict to markets with a market start time before or after the specified date |
| withOrders | Set< OrderStatus > |  | Restrict to markets where I have one or more orders in these states. |
| raceTypes | Set<String> |  | Restrict to markets of a specific raceType. Valid values are -Harness, Flat, Hurdle, Chase, Bumper, NH Flat, Steeple (AUS/NZ races), and NO\_VALUE (when no valid race type has been mapped).   For AUS/NZ races, the following definitions apply:   * **Flat**’ – Used for standard ANZ thoroughbred races * ‘**Harness**’ – Self-explanatory – used for Aus/NZ harness racing events. * ‘**Steeple**’ – Used for Aus/NZ steeple chase races. * ‘**Hurdle**’ - Used for Aus/NZ hurdle races. |
| betDelayModels | Set<String> |  | Restrict to markets specific betDelayModels. e.g. **PASSIVE, DYNAMIC** |

#FFFFFF#FFCC33MarketCatalogue

Information about a market

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| marketId | String |  | The unique identifier for the market. MarketId's are prefixed with '1.' |
| marketName | String |  | The name of the market |
| marketStartTime | Date |  | The time this market starts at, only returned when the MARKET\_START\_TIME enum is passed in the marketProjections |
| description | [MarketDescription](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#MarketDescription) |  | Details about the market |
| totalMatched | Double |  | The total amount of money matched on the market.  **Please note:** The returned value is cached.  For the live total matched value please use listMarketBook. |
| runners | List <[RunnerCatalog](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#RunnerCatalog)> |  | The runners (selections) contained in the market |
| eventType | [EventType](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#EventType) |  | The Event Type the market is contained within |
| competition | [Competition](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#Competition) |  | The competition the market is contained within. Usually only applies to Football competitions |
| event | [Event](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#Event) |  | The event the market is contained within |

MarketBook

#FFFFFF#FFCC33MarketBook

The dynamic data in a market

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| marketId | String |  | The unique identifier for the market. MarketId's are prefixed with '1.' |
| isMarketDataDelayed | boolean |  | True if the data returned by listMarketBook will be delayed. The data may be delayed because you are not logged in with a funded account or you are using an Application Key that does not allow up to date data. |
| status | MarketStatus |  | The status of the market, for example OPEN, SUSPENDED, CLOSED (settled), etc. |
| suspendReason | String |  | Currently returned only for Soccer markets, when status = SUSPENDED. Possible values are *Goal, Third Party Unavailable, Penalty, Red Card, Non In Play Market*, |
| betDelay | int |  | The number of seconds an order is held until it is submitted into the market. Orders are usually delayed when the market is in-play |
| bspReconciled | boolean |  | True if the market starting price has been reconciled |
| complete | boolean |  | If false, runners may be added to the market |
| inplay | boolean |  | True if the market is currently in play |
| numberOfWinners | int |  | The number of selections that could be settled as winners |
| numberOfRunners | int |  | The number of runners in the market |
| numberOfActiveRunners | int |  | The number of runners that are currently active. An active runner is a selection available for betting |
| lastMatchTime | Date |  | The most recent time an order was executed |
| totalMatched | double |  | The total amount matched |
| totalAvailable | double |  | The total amount of orders that remain unmatched |
| crossMatching | boolean |  | True if cross matching is enabled for this market. |
| runnersVoidable | boolean |  | True if runners in the market can be voided. **Please note** - this doesn't include horse racing markets under which bets are voided on non-runners with any applicable reduction factor applied/ |
| version | long |  | The version of the market. The version increments whenever the market status changes, for example, turning in-play, or suspended when a goal is scored. |
| runners | List <[Runner](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#Runner)> |  | Information about the runners (selections) in the market. |
| keyLineDescription | [KeyLineDescription](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Betting+Type+Definitions#BettingTypeDefinitions-#KeyLineDescription) |  | Description of a markets key line for valid market types |
| betDelayModels | List <BetDelayModel> |  | Indicates which bet delay models are applied to a market if applicable. i.e. PASSIVE, DYNAMIC or both. |

RunnerCatalog

#FFFFFF#FFCC33RunnerCatalog

Information about the Runners (selections) in a market

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| selectionId | long |  | The unique id for the selection. The same **selectionId** and **runnerName** pairs are used accross all Betfair markets which contain them. **Please note:** The selectionId can be mapped to the runner name using the output from [**listMarketCatalogue**](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Getting+Started#GettingStarted-RequesttheMarketInformationforanEventinformation) |
| runnerName | String |  | The name of the runner. |
| handicap | double |  | The handicap applies to market with the [MarketBettingType](http://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Betting+Enums#BettingEnums-MarketBettingType) ASIAN\_HANDICAP\_SINGLE\_LINE & ASIAN\_HANDICAP\_DOUBLE\_LINE only otherwise '0' |
| sortPriority | int |  | The sort priority of this runner. Indicates the order in which the runners are displayed on the Betfair Exchange website. |
| metadata | Map<String,String> |  | Metadata associated with the runner.  For a description of this data for Horse Racing, please see Runner Metadata Description |

Runner

#FFFFFF#FFCC33Runner

The dynamic data about runners in a market

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| selectionId | long |  | The unique id of the runner (selection). **Please note -** the same **selectionId** and **runnerName** pairs are used accross all Betfair markets which contain them. |
| handicap | double |  | The handicap.  Enter the specific handicap value (returned by RUNNER in listMaketBook) if the market is an Asian handicap market. |
| status | RunnerStatus |  | The status of the selection (i.e., ACTIVE, REMOVED, WINNER, PLACED, LOSER, HIDDEN) Runner status information is available for 90 days following market settlement. |
| adjustmentFactor | double |  | The adjustment factor applied if the selection is removed |
| lastPriceTraded | double |  | The price of the most recent bet matched on this selection |
| totalMatched | double |  | The total amount matched on this runner |
| removalDate | Date |  | If date and time the runner was removed |
| sp | [StartingPrices](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#StartingPrices) |  | The BSP related prices for this runner |
| ex | [ExchangePrices](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#ExchangePrices) |  | The Exchange prices available for this runner |
| orders | List< [Order](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#Order) > |  | List of orders in the market |
| matches | List< [Match](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#Match) > |  | List of matches (i.e, orders that have been fully or partially executed) |
| matchesByStrategy | Map<String,[Matches](/wiki/pages/resumedraft.action?draftId=2687465)> |  | List of matches for each strategy, ordered by matched data |

StartingPrices

#FFFFFF#FFCC33StartingPrices

Information about the Betfair Starting Price. Only available in BSP markets

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| nearPrice | double |  | What the starting price would be if the market was reconciled now taking into account the SP bets as well as unmatched exchange bets on the same selection in the exchange. This data is cached and update every 60 seconds. **Please note:** Type Double may contain numbers, INF, -INF, and NaN. |
| farPrice | double |  | What the starting price would be if the market was reconciled now taking into account only the currently place SP bets. The Far Price is not as complicated but not as accurate and only accounts for money on the exchange at SP. This data is cached and updated every 60 seconds. **Please note:** Type Double may contain numbers, INF, -INF, and NaN. |
| backStakeTaken | List<#[PriceSize](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#PriceSize) > |  | The total amount of back bets matched at the actual Betfair Starting Price. Pre-reconciliation, this field is zero for all prices except 1.01 (for Market on Close bets) and at the limit price for any Limit on Close bets. |
| layLiabilityTaken | List< [PriceSize](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#PriceSize) > |  | The lay amount matched at the actual Betfair Starting Price. Pre-reconciliation, this field is zero for all prices except 1000 (for Market on Close bets) and at the limit price for any Limit on Close bets. |
| actualSP | double |  | The final BSP price for this runner. Only available for a BSP market that has been reconciled.  **Please note:** for REMOVED runners the actualSP will be returned as 'NaN. Value may be returned as 'Infinity' if no BSP can be calculated. |

ExchangePrices

#FFFFFF#FFCC33ExchangePrices

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| availableToBack | List< [PriceSize](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#PriceSize) > |  |  |
| availableToLay | List< [PriceSize](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#PriceSize) > |  |  |
| tradedVolume | List< [PriceSize](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#PriceSize) > |  |  |

Event

#FFFFFF#FFCC33Event

Event

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| id | String |  | The unique id for the event |
| name | String |  | The name of the event |
| countryCode | String |  | The ISO-2 code for the event.  A list of ISO-2 codes is available via <http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>  **Please note:** default value is 'GB' when the correct country code cannot be determined. |
| timezone | String |  | This is timezone in which the event is taking place. |
| venue | String |  | venue |
| openDate | Date |  | The scheduled start date and time of the event. This is Europe/London (GMT) by default |

EventResult

#FFFFFF#FFCC33EventResult

Event Result

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| event | [Event](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#Event) |  | Event |
| marketCount | int |  | Count of markets associated with this event |

Competition

#FFFFFF#FFCC33Competition

Competition

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| id | String |  | id |
| name | String |  | name |

CompetitionResult

#FFFFFF#FFCC33CompetitionResult

Competition Result

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| competition | [Competition](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#Competition) |  | Competition |
| marketCount | int |  | Count of markets associated with this competition |
| competitionRegion | String |  | Region in which this competition is happening |

EventType

#FFFFFF#FFCC33EventType

EventType

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| id | String |  | id |
| name | String |  | name |

EventTypeResult

#FFFFFF#FFCC33EventTypeResult

EventType Result

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| eventType | [EventType](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#EventType) |  | The ID identifying the Event Type |
| marketCount | int |  | Count of markets associated with this eventType |

MarketTypeResult

#FFFFFF#FFCC33MarketTypeResult

MarketType Result

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| marketType | String |  | Market Type |
| marketCount | int |  | Count of markets associated with this marketType |

CountryCodeResult

#FFFFFF#FFCC33CountryCodeResult

CountryCode Result

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| countryCode | String |  | The ISO-2 code for the event.  A list of ISO-2 codes is available via <http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2> |
| marketCount | int |  | Count of markets associated with this Country Code |

VenueResult

#FFFFFF#FFCC33VenueResult

Venue Result

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| venue | String |  | Venue |
| marketCount | int |  | Count of markets associated with this Venue |

TimeRange

#FFFFFF#FFCC33TimeRange

TimeRange

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| from | Date |  | from |
| to | Date |  | to |

TimeRangeResult

#FFFFFF#FFCC33TimeRangeResult

TimeRange Result

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| timeRange | [TimeRange](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#TimeRange) |  | TimeRange |
| marketCount | int |  | Count of markets associated with this TimeRange |

#FFFFFF#FFCC33Order

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| betId | String |  |  |
| orderType | OrderType |  | BSP Order type. |
| status | OrderStatus |  | Either EXECUTABLE (an unmatched amount remains) or EXECUTION\_COMPLETE (no unmatched amount remains). |
| persistenceType | PersistenceType |  | What to do with the order at turn-in-play |
| side | Side |  | Indicates if the bet is a Back or a LAY.  For LINE markets customers either Buy a line (LAY bet, winning if outcome is greater than the taken line (price)) or Sell a line (BACK bet, winning if outcome is less than the taken line (price)) |
| price | double |  | The price of the bet. **Please note**: LINE markets operate at even-money odds of 2.0. However, price for these markets refers to the line positions available as defined by the markets min-max range and interval steps |
| size | double |  | The size of the bet. |
| bspLiability | double |  | Not to be confused with size. This is the liability of a given BSP bet. |
| placedDate | Date |  | The date, to the second, the bet was placed. |
| avgPriceMatched | double |  | The average price matched at. Voided match fragments are removed from this average calculation. For MARKET\_ON\_CLOSE BSP bets this reports the matched SP price following the SP reconciliation process. This value is not meaningful for activity on LINE markets and is not guaranteed to be returned or maintained for these markets. |
| sizeMatched | double |  | The current amount of this bet that was matched. |
| sizeRemaining | double |  | The current amount of this bet that is unmatched. |
| sizeLapsed | double |  | The current amount of this bet that was lapsed. |
| sizeCancelled | double |  | The current amount of this bet that was cancelled. |
| sizeVoided | double |  | The current amount of this bet that was voided. |
| customerOrderRef | [CustomerOrderRef](/wiki/pages/resumedraft.action?draftId=2687465#BettingTypeDefinitions-MatchId) |  | The customer order reference sent for this bet |
| customerStrategyRef | [CustomerStrategyRef](/wiki/pages/resumedraft.action?draftId=2687465#BettingTypeDefinitions-MatchId) |  | The customer strategy reference sent for this bet |

Match

#FFFFFF#FFCC33Match

An individual bet Match, or rollup by price or avg price. Rollup depends on the requested MatchProjection

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| betId | String |  | Only present if no rollup |
| matchId | String |  | Only present if no rollup |
| side | Side |  | Indicates if the bet is a Back or a LAY |
| price | double |  | Either actual match price or avg match price depending on rollup. This value is not meaningful for activity on LINE markets and is not guaranteed to be returned or maintained for these markets. |
| size | double |  | Size matched at in this fragment, or at this price or avg price depending on rollup |
| matchDate | Date |  | Only present if no rollup |

MarketVersion

#FFFFFF#FFCC33MarketVersion

Market version

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| version | long |  | A non-monotonically increasing number indicating market changes |

MarketDescription

#FFFFFF#FFCC33MarketDescription

Market Definition

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| persistenceEnabled | boolean |  | If 'true' the market supports 'Keep' bets if the market is to be turned in-play |
| bspMarket | boolean |  | If 'true' the market supports Betfair SP betting |
| marketTime | Date |  | The market start time. This is the scheduled start time of the market e.g. horse race or football match etc. |
| suspendTime | Date |  | The market suspend time. This is the next time the market will be suspended for betting and is normally the same as the marketTime. |
| settleTime | Date |  | settled time |
| bettingType | MarketBettingType |  | See MarketBettingType |
| turnInPlayEnabled | boolean |  | If 'true' the market is set to turn in-play |
| marketType | String |  | Market base type |
| regulator | String |  | The market regulator. Value include “GIBRALTAR REGULATOR" (.com), MR\_ESP (Betfair.es markets), MR\_IT (Betfair.it). GIBRALTAR REGULATOR = MR\_INT in the Stream API |
| marketBaseRate | double |  | The commission rate applicable to the market |
| discountAllowed | boolean |  | Indicates whether or not the user's discount rate is taken into account on this market. If ‘false’ all users will be charged the same commission rate, regardless of discount rate. |
| wallet | String |  | The wallet to which the market belongs. |
| rules | String |  | The market rules. |
| rulesHasDate | boolean |  | Indicates whether rules have a date included. |
| eachWayDivisor | double |  | The divisor is returned for the marketType EACH\_WAY only and refers to the fraction of the win odds at which the place portion of an each way bet is settled |
| clarifications | String |  | Any additional information regarding the market |
| lineRangeInfo | [MarketLineRangeInfo](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#MarketLineRangeInfo) |  | Line range info for line markets |
| raceType | String |  | An external identifier of a race type |
| priceLadderDescription | [PriceLadderDescription](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#PriceLadderDescription) |  | Details about the price ladder in use for this market. |
| betDelayModels | Set<String>. |  | Indicates which bet delay models are applied to a market if applicable. i.e. **PASSIVE, DYNAMIC** or both |

MarketRates

#FFFFFF#FFCC33MarketRates

Market Rates

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| marketBaseRate | double |  | marketBaseRate |
| discountAllowed | boolean |  | discountAllowed |

MarketLicence

#FFFFFF#FFCC33MarketLicence

Market Licence

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| wallet | String |  | The wallet from which funds will be taken when betting on this market |
| rules | String |  | The rules for this market |
| rulesHasDate | boolean |  | The market's start date and time are relevant to the rules. |
| clarifications | String |  | Clarifications to the rules for the market |

MarketLineRangeInfo

#FFFFFF#FFCC33MarketLineRangeInfo

Market Line and Range Info

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| maxUnitValue | double |  | maxPrice - Maximum value for the outcome, in market units for this market (eg 100 runs) |
| minUnitValue | double |  | minPrice - Minimum value for the outcome, in market units for this market (eg 0 runs) |
| interval | double |  | interval - The odds ladder on this market will be between the range of minUnitValue and maxUnitValue, in increments of the inverval value.e.g. If minUnitValue=10 runs, maxUnitValue=20 runs, interval=0.5 runs, then valid odds include 10, 10.5, 11, 11.5 up to 20 runs. |
| marketUnit | String |  | unit - The type of unit the lines are incremented in by the interval (e.g: runs, goals or seconds. |

PriceSize

#FFFFFF#FFCC33PriceSize

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| price | double |  | The price available |
| size | double |  | The stake available |

ClearedOrderSummary

#FFFFFF#FFCC33ClearedOrderSummary

 Summary of a cleared order.

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| eventTypeId | [EventTypeId](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#EventTypeId) |  | The id of the event type bet on. Available at EVENT\_TYPE groupBy level or lower. |
| eventId | [EventId](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#EventId) |  | The id of the event bet on. Available at EVENT groupBy level or lower. |
| marketId | [MarketId](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#MarketId) |  | The id of the market bet on. Available at MARKET groupBy level or lower. |
| selectionId | [SelectionId](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#SelectionId) |  | The id of the selection bet on. Available at RUNNER groupBy level or lower. |
| handicap | [Handicap](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#Handicap) |  | The handicap.  Enter the specific handicap value (returned by RUNNER in listMaketBook) if the market is an Asian handicap market. Available at MARKET groupBy level or lower. |
| betId | [BetId](/wiki/pages/resumedraft.action?draftId=2687465#BettingTypeDefinitions-Bet) |  | The id of the bet. Available at BET groupBy level. |
| placedDate | Date |  | The date the bet order was placed by the customer. Only available at BET groupBy level. |
| persistenceType | PersistenceType |  | The turn in play persistence state of the order at bet placement time. This field will be empty or omitted on true SP bets. Only available at BET groupBy level. |
| orderType | OrderType |  | The type of bet (e.g standard limited-liability Exchange bet (LIMIT), a standard BSP bet (MARKET\_ON\_CLOSE), or a minimum-accepted-price BSP bet (LIMIT\_ON\_CLOSE)). If the bet has a OrderType of MARKET\_ON\_CLOSE and a persistenceType of MARKET\_ON\_CLOSE then it is a bet which has transitioned from LIMIT to MARKET\_ON\_CLOSE. Only available at BET groupBy level. |
| side | Side |  | Whether the bet was a back or lay bet. Available at SIDE groupBy level or lower. |
| itemDescription | [ItemDescription](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#ItemDescription) |  | A container for all the ancillary data and localised text valid for this Item |
| betOutcome | String |  | The settlement outcome of the bet. Tri-state (WIN/LOSE/PLACE) to account for Each Way bets where the place portion of the bet won but the win portion lost. The profit/loss amount in this case could be positive or negative depending on the price matched at. Only available at BET groupBy level. |
| priceRequested | [Price](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#Price) |  | The average requested price across all settled bet orders under this Item. Available at SIDE groupBy level or lower. For LINE markets this is the line position requested. For LINE markets this is the line position requested. |
| settledDate | Date |  | The date and time the bet order was settled by Betfair. Available at SIDE groupBy level or lower. |
| lastMatchedDate | Date |  | The date and time the last bet order was matched by Betfair. Available on Settled orders only. |
| betCount | int |  | The number of actual bets within this grouping (will be 1 for BET groupBy) |
| commission | [Size](/wiki/pages/resumedraft.action?draftId=2687465#BettingTypeDefinitions-S) |  | The cumulative amount of commission paid by the customer across all bets under this Item, in the account currency. Available at EXCHANGE, EVENT\_TYPE, EVENT and MARKET level groupings only. |
| priceMatched | [Price](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#Price) |  | The average matched price across all settled bets or bet fragments under this Item. Available at SIDE groupBy level or lower. For LINE markets this is the line position matched at. |
| priceReduced | boolean |  | If true, then the matched price was affected by a reduction factor due to of a runner removal from this Horse Racing market. |
| sizeSettled | [Size](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#Size) |  | The cumulative bet size that was settled as matched or voided under this Item, in the account currency. Available at SIDE groupBy level or lower. |
| profit | [Size](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#Size) |  | The profit or loss (negative profit) gained on this line, in the account currency |
| sizeCancelled | [Size](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#Size) |  | The amount of the bet that was available to be matched, before cancellation or lapsing, in the account currency |
| customerOrderRef | String |  | The order reference defined by the customer for the bet order |
| customerStrategyRef | String |  | The strategy reference defined by the customer for the bet order |
| sourceIdKey | String |  | App Key used to place order |
| sourceIdDescription | String |  | Description associated with sourceIdKey e.g. Desktop, Mobile, API |

ClearedOrderSummaryReport

#FFFFFF#FFCC33ClearedOrderSummaryReport

A container representing search results.

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| clearedOrders | List<[ClearedOrderSummary](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#ClearedOrderSummary)> |  | The list of cleared orders returned by your query. This will be a valid list (i.e. empty or non-empty but never 'null'). |
| moreAvailable | boolean |  | Indicates whether there are further result items beyond this page. Note that underlying data is highly time-dependent and the subsequent search orders query might return an empty result. |

ItemDescription

#FFFFFF#FFCC33 ItemDescription

This object contains some text which may be useful to render a betting history view. It offers no long-term warranty as to the correctness of the text.

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| eventTypeDesc | String |  | The event type name, translated into the requested locale. Available at EVENT\_TYPE groupBy or lower. |
| eventDesc | String |  | The eventName, or openDate + venue, translated into the requested locale. Available at EVENT groupBy or lower. |
| marketDesc | String |  | The market name or racing market type ("Win", "To Be Placed (2 places)", "To Be Placed (5 places)" etc) translated into the requested locale. Available at MARKET groupBy or lower. |
| marketType | String |  | The market type e.g. MATCH\_ODDS, PLACE, WIN etc. |
| marketStartTime | Date |  | The start time of the market (in ISO-8601 format, not translated). Available at MARKET groupBy or lower. |
| runnerDesc | String |  | The runner name, maybe including the handicap, translated into the requested locale. Available at BET groupBy. |
| numberOfWinners | int |  | The number of winners on a market. Available at BET groupBy. |
| eachWayDivisor | double |  | The divisor is returned for the marketType EACH\_WAY only and refers to the fraction of the win odds at which the place portion of an each way bet is settled |

CurrentItemDescription

#FFFFFF#FFCC33CurrentItemDescription

**CurrentItemDescription**

This object contains ancillary information about the item

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| marketVersion | [MarketVersion](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#MarketVersion) |  | The relevant version of the market for this item |

RunnerId

#FFFFFF#FFCC33RunnerId

This object contains the unique identifier for a runner

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| marketId | [MarketId](https://confluence.app.betfair/pages/viewpage.action?title=SportsAPING+BSIDL&spaceKey=APING#SportsAPINGBSIDL-MarketId) |  | The id of the market bet on |
| selectionId | [SelectionId](https://confluence.app.betfair/pages/viewpage.action?title=SportsAPING+BSIDL&spaceKey=APING#SportsAPINGBSIDL-SelectionId) |  | The id of the selection bet on |
| handicap | [Handicap](##Handicap) |  | The handicap associated with the runner in case of asian handicap markets, otherwise returns '0.0'. |

CurrentOrderSummaryReport

#FFFFFF#FFCC33CurrentOrderSummaryReport

A container representing search results.

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| currentOrders | List< [CurrentOrderSummary](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#CurrentOrderSummary) > |  | The list of current orders returned by your query. This will be a valid list (i.e. empty or non-empty but never 'null'). |
| moreAvailable | boolean |  | Indicates whether there are further result items beyond this page. Note that underlying data is highly time-dependent and the subsequent search orders query might return an empty result. |

CurrentOrderSummary

#FFFFFF#FFCC33CurrentOrderSummary

Summary of a current order.

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| betId | String |  | The bet ID of the original place order. |
| marketId | String |  | The market id the order is for. |
| selectionId | long |  | The selection id the order is for. |
| handicap | double |  | The handicap associated with the runner in case of Asian handicap markets, null otherwise. |
| priceSize | [PriceSize](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#PriceSize) |  | The price and size of the bet. |
| bspLiability | double |  | Not to be confused with size. This is the liability of a given BSP bet. |
| side | Side |  | BACK/LAY |
| status | OrderStatus |  | Either EXECUTABLE (an unmatched amount remains) or EXECUTION\_COMPLETE (no unmatched amount remains). |
| persistenceType | PersistenceType |  | What to do with the order at turn-in-play. |
| orderType | OrderType |  | BSP Order type. |
| placedDate | Date |  | The date, to the second, the bet was placed. |
| matchedDate | Date |  | The date, to the second, of the last matched bet fragment (where applicable) |
| averagePriceMatched | double |  | The average price matched at. Voided match fragments are removed from this average calculation. The price is automatically adjusted in the event of non runners being declared with applicable reduction factors. **Please note:** This value is not meaningful for activity on LINE markets and is not guaranteed to be returned or maintained for these markets. |
| sizeMatched | double |  | The current amount of this bet that was matched. |
| sizeRemaining | double |  | The current amount of this bet that is unmatched. |
| sizeLapsed | double |  | The current amount of this bet that was lapsed. |
| sizeCancelled | double |  | The current amount of this bet that was cancelled. |
| sizeVoided | double |  | The current amount of this bet that was voided. |
| regulatorAuthCode | String |  | The regulator authorisation code. |
| regulatorCode | String |  | The regulator Code. |
| customerOrderRef | String |  | The order reference defined by the customer for this bet |
| customerStrategyRef | String |  | The strategy reference defined by the customer for this bet |
| currentItemDescription | [CurrentItemDescription](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#CurrentItemDescription) |  | A container for all the ancillary data for this Item |
| sourceIdKey | String |  | App Key used to place order |
| sourceIdDescription | String |  | Description associated with sourceIdKey e.g. Desktop, Mobile, API |

PlaceInstruction

#FFFFFF#FFCC33PlaceInstruction

Instruction to place a new order

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| orderType | OrderType |  |  |
| selectionId | long |  | The selection\_id. |
| handicap | double |  | The handicap associated with the runner in case of Asian handicap markets (e.g. marketTypes ASIAN\_HANDICAP\_DOUBLE\_LINE, ASIAN\_HANDICAP\_SINGLE\_LINE) null otherwise. |
| side | Side |  | Back or Lay |
| limitOrder | [LimitOrder](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#LimitOrder) |  | A simple exchange bet for immediate execution |
| limitOnCloseOrder | [LimitOnCloseOrder](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#LimitOnCloseOrder) |  | Bets are matched if, and only if, the returned starting price is better than a specified price. In the case of back bets, LOC bets are matched if the calculated starting price is greater than the specified price. In the case of lay bets, LOC bets are matched if the starting price is less than the specified price. If the specified limit is equal to the starting price, then it may be matched, partially matched, or may not be matched at all, depending on how much is needed to balance all bets against each other (MOC, LOC and normal exchange bets) |
| marketOnCloseOrder | [MarketOnCloseOrder](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#MarketOnCloseOrder) |  | Bets remain unmatched until the market is reconciled. They are matched and settled at a price that is representative of the market at the point the market is turned in-play. The market is reconciled to find a starting price and MOC bets are settled at whatever starting price is returned. MOC bets are always matched and settled, unless a starting price is not available for the selection. Market on Close bets can only be placed before the starting price is determined |
| customerOrderRef | String |  | An optional reference customers can set to identify instructions.. No validation will be done on uniqueness and the string is limited  to 32 characters. If an empty string is provided it will be treated as null. |

PlaceExecutionReport

#FFFFFF#FFCC33PlaceExecutionReport

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| customerRef | String |  | Echo of the customerRef if passed. |
| status | ExecutionReportStatus |  |  |
| errorCode | ExecutionReportErrorCode |  |  |
| marketId | String |  | Echo of marketId passed |
| instructionReports | List< [PlaceInstructionReport](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#PlaceInstructionReport) > |  |  |

LimitOrder

#FFFFFF#FFCC33LimitOrder

Place a new LIMIT order (simple exchange bet for immediate execution)

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| size | double |  | The size of the bet. **Please note**: For market type EACH\_WAY. The total stake = size x 2 |
| price | double |  | The limit price. For LINE markets, the price at which the bet is settled and struck will always be 2.0 (Evens). On these bets, the Price field is used to indicate the line value which is being bought or sold |
| persistenceType | PersistenceType |  | What to do with the order at turn-in-play |
| timeInForce | TimeInForce |  | The type of TimeInForce value to use. This value takes precedence over any PersistenceType value chosen.  If this attribute is populated along with the PersistenceType field, then the PersistenceType will be  ignored. When using FILL\_OR\_KILL for a Line market the Volume Weighted Average Price (VWAP) functionality is disabled |
| minFillSize | Size |  | An optional field used if the TimeInForce attribute is populated.  If specified without TimeInForce then this field is ignored.  If no minFillSize is specified, the order is killed unless the entire size can be matched.  If minFillSize is specified, the order is killed unless at least the minFillSize can be matched.  The minFillSize cannot be greater than the order's size.  If specified for a BetTargetType and FILL\_OR\_KILL order, then this value will be ignored |
| betTargetType | BetTargetType |  | An optional field to allow betting to a targeted PAYOUT or BACKERS\_PROFIT.  It's invalid to specify both a Size and BetTargetType  Matching provides best execution at the requested price or better up to the payout or profit.  If the bet is not matched completely and immediately, the remaining portion enters the unmatched pool of bets on the exchange  BetTargetType bets are invalid for LINE markets |
| betTargetSize | Size |  | An optional field which must be specified if BetTargetType is specified for this order  The requested outcome size of either the payout or profit.  This is named from the backer's perspective. For Lay bets the profit represents the bet's liability |

LimitOnCloseOrder

#FFFFFF#FFCC33LimitOnCloseOrder

Place a new LIMIT\_ON\_CLOSE bet

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| liability | double |  | The size of the bet. See [Min BSP Liability](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Additional+Information#AdditionalInformation-CurrencyParameters) |
| price | double |  | The limit price of the bet if LOC |

MarketOnCloseOrder

#FFFFFF#FFCC33MarketOnCloseOrder

Place a new MARKET\_ON\_CLOSE bet

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| liability | double |  | The size of the bet. |

PlaceInstructionReport

#FFFFFF#FFCC33PlaceInstructionReport

Response to a PlaceInstruction

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| status | InstructionReportStatus |  | Whether the command succeeded or failed |
| errorCode | InstructionReportErrorCode |  | Cause of failure, or null if the command succeeds |
| orderStatus | OrderStatus |  | The status of the order, if the instruction succeeded. If the instruction is unsuccessful, no value is provided.   **Please note:**  by default, this field is not returned for **MARKET\_ON\_CLOSE** and **LIMIT\_ON\_CLOSE** orders. |
| instruction | [PlaceInstruction](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#PlaceInstruction) |  | The instruction that was requested |
| betId | String |  | The bet ID of the new bet. Will be null on failure or if the order was placed asynchronously. |
| placedDate | Date |  | Will be null if the order was placed asynchronously |
| averagePriceMatched | [Price](https://confluence.app.betfair/display/APING/SportsAPING+BSIDL#SportsAPINGBSIDL-Price) |  | Will be null if the order was placed asynchronously. This value is not meaningful for activity on LINE markets and is not guaranteed to be returned or maintained for these markets. |
| sizeMatched | [Size](https://confluence.app.betfair/display/APING/SportsAPING+BSIDL#SportsAPINGBSIDL-Size) |  | Will be null if the order was placed asynchronously |

CancelInstruction

#FFFFFF#FFCC33CancelInstruction

Instruction to fully or partially cancel an order (only applies to LIMIT orders). **Please note:** the CancelInstruction report won't be returned for account level cancel instructions.

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| betId | String |  | The betId |
| sizeReduction | double |  | If supplied then this is a partial cancel.  Should be set to 'null' if no size reduction is required. |

CancelExecutionReport

#FFFFFF#FFCC33CancelExecutionReport

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| customerRef | String |  | Echo of the customerRef if passed. |
| status | ExecutionReportStatus |  |  |
| errorCode | ExecutionReportErrorCode |  |  |
| marketId | String |  | Echo of marketId passed |
| instructionReports | List< [CancelInstructionReport](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#CancelInstructionReport) > |  |  |

ReplaceInstruction

#FFFFFF#FFCC33ReplaceInstruction

Instruction to replace a LIMIT or LIMIT\_ON\_CLOSE order at a new price. Original order will be cancelled and a new order placed at the new price for the remaining stake.

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| betId | String |  | Unique identifier for the bet |
| newPrice | double |  | The price to replace the bet at |

ReplaceExecutionReport

#FFFFFF#FFCC33ReplaceExecutionReport

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| customerRef | String |  | Echo of the customerRef if passed. |
| status | ExecutionReportStatus |  |  |
| errorCode | ExecutionReportErrorCode |  |  |
| marketId | String |  | Echo of marketId passed |
| instructionReports | List< [ReplaceInstructionReport](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#ReplaceInstructionReport) > |  |  |

ReplaceInstructionReport

#FFFFFF#FFCC33ReplaceInstructionReport

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| status | InstructionReportStatus |  | whether the command succeeded or failed |
| errorCode | InstructionReportErrorCode |  | cause of failure, or null if command succeeds |
| cancelInstructionReport | [CancelInstructionReport](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#CancelInstructionReport) |  | Cancellation report for the original order |
| placeInstructionReport | [PlaceInstructionReport](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#PlaceInstructionReport) |  | Placement report for the new order |

CancelInstructionReport

#FFFFFF#FFCC33CancelInstructionReport

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| status | InstructionReportStatus |  | whether the command succeeded or failed |
| errorCode | InstructionReportErrorCode |  | cause of failure, or null if command succeeds |
| instruction | [CancelInstruction](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#CancelInstruction) |  | The instruction that was requested |
| sizeCancelled | double |  |  |
| cancelledDate | Date |  |  |

UpdateInstruction

#FFFFFF#FFCC33UpdateInstruction

Instruction to update LIMIT bet's persistence of an order that do not affect exposure

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| betId | String |  | Unique identifier for the bet |
| newPersistenceType | PersistenceType |  | The new persistence type to update this bet to |

UpdateExecutionReport

#FFFFFF#FFCC33UpdateExecutionReport

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| customerRef | String |  | Echo of the customerRef if passed. |
| status | ExecutionReportStatus |  |  |
| errorCode | ExecutionReportErrorCode |  |  |
| marketId | String |  | Echo of marketId passed |
| instructionReports | List< [UpdateInstructionReport](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#UpdateInstructionReport) > |  |  |

UpdateInstructionReport

#FFFFFF#FFCC33UpdateInstructionReport

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| status | InstructionReportStatus |  | whether the command succeeded or failed |
| errorCode | InstructionReportErrorCode |  | cause of failure, or null if command succeeds |
| instruction | [UpdateInstruction](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#UpdateInstruction) |  | The instruction that was requested |

| **Type** | **Required** | **Description** |
| --- | --- | --- |

PriceProjection

#FFFFFF#FFCC33PriceProjection

Selection criteria of the returning price data

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| priceData | Set< PriceData > |  | The basic price data you want to receive in the response. |
| exBestOffersOverrides | [OffersOverrides](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#OffersOverrides) |  | Options to alter the default representation of best offer prices Applicable to EX\_BEST\_OFFERS priceData selection |
| virtualise | boolean |  | Indicates if the returned prices should include virtual prices. Applicable to EX\_BEST\_OFFERS and EX\_ALL\_OFFERS priceData selections, default value is false. **Please note:** This must be set to 'true' replicate the display of prices on the [Betfair Exchange](http://www.betfair.com/exchange/plus/) website. |
| rolloverStakes | boolean |  | Indicates if the volume returned at each price point should be the absolute value or a cumulative sum of volumes available at the price and all better prices. If unspecified defaults to false. Applicable to EX\_BEST\_OFFERS and EX\_ALL\_OFFERS price projections. Not supported as yet. |

ExBestOffersOverrides

#FFFFFF#FFCC33ExBestOffersOverrides

Options to alter the default representation of best offer prices

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| bestPricesDepth | int |  | The maximum number of prices to return on each side for each runner. If unspecified defaults to 3. The maximum returned price depth returned is 10. |
| rollupModel | RollupModel |  | The model to use when rolling up available sizes. If unspecified defaults to STAKE rollup model with rollupLimit of minimum stake in the specified currency. |
| rollupLimit | int |  | The volume limit to use when rolling up returned sizes. The exact definition of the limit depends on the rollupModel. If no limit is provided it will use minimum stake as default the value. Ignored if no rollup model is specified. |
| rollupLiabilityThreshold | double |  | Only applicable when rollupModel is MANAGED\_LIABILITY. The rollup model switches from being stake-based to liability-based at the smallest lay price which is >= rollupLiabilityThreshold.service level default (TBD). Not supported as yet. |
| rollupLiabilityFactor | int |  | Only applicable when rollupModel is MANAGED\_LIABILITY. (rollupLiabilityFactor \* rollupLimit) is the minimum liability the user is deemed to be comfortable with. After the rollupLiabilityThreshold price subsequent volumes will be rolled up to minimum value such that the liability >= the minimum liability.service level default (5). Not supported as yet. |

MarketProfitAndLoss

#FFFFFF#FFCC33MarketProfitAndLoss

Profit and loss in a market

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| marketId | String |  | The unique identifier for the market |
| commissionApplied | double |  | The commission rate applied to P&L values. Only returned if netOfCommision option is requested |
| profitAndLosses | List<[RunnerProfitAndLoss](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#RunnerProfitAndLoss)> |  | Calculated profit and loss data. |

RunnerProfitAndLoss

#FFFFFF#FFCC33RunnerProfitAndLoss

Profit and loss if selection is wins or loses

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| selectionId | [Selection](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#Selection) |  | The unique identifier for the selection |
| ifWin | double |  | Profit or loss for the market if this selection is the winner. |
| ifLose | double |  | Profit or loss for the market if this selection is the loser. Only returned for multi-winner odds markets. |
| ifPlace | double |  | Profit or loss for the market if this selection is placed. Applies to marketType EACH\_WAY only. |

PriceLadderDescription**PriceLadderDescription**

Description of the price ladder type and any related data.

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| type | PriceLadderType |  | The type of price ladder. |

KeyLineSelection**KeyLineSelection**

Description of a markets key line selection, comprising the selectionId and handicap of the team it is applied to.

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| selectionId | [SelectionId](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#SelectionId) |  | Selection ID of the runner in the key line handicap. |
| handicap | [Handicap](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#Handicap) |  | Handicap value of the key line. |

#KeyLineDescription

**KeyLineDescription**

A list of KeyLineSelection objects describing the key line for the market

| **Field name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| keyLine | List<[KeyLineSelection](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687465/Betting+Type+Definitions#KeyLineSelection)> |  | A list of KeyLineSelection objects |

TypeAliases

#FFFFFF#FFCC33Type AliasesType aliases

| **Alias** | **Type** |
| --- | --- |
| MarketType  MarketType | String |
| Venue  Venue | String |
| MarketId  MarketId | String |
| SelectionId  SelectionId | long |
| Handicap  Handicap | double |
| EventId  EventId | String |
| EventTypeId  EventTypeId | String |
| CountryCode  CountryCode | String |
| ExchangeId  ExchangeId | String |
| CompetitionId  CompetitionId | String |
| Price  Price | double |
| Size  Size | double |
| BetId  BetId | String |
| MatchId  MatchId | String |
| CustomerOrderRef | String |
| CustomerStrategyRef | String |
