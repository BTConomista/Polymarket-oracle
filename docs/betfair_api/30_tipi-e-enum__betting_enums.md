# Betting Enums

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687455>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687455`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## Enums

MarketProjection

#FFFFFF#99CC66MarketProjection

| **Value** | **Description** |
| --- | --- |
| COMPETITION | If not selected then the competition will not be returned with marketCatalogue |
| EVENT | If not selected then the event will not be returned with marketCatalogue |
| EVENT\_TYPE | If not selected then the eventType will not be returned with marketCatalogue |
| MARKET\_START\_TIME | If not selected then the start time will not be returned with marketCatalogue |
| MARKET\_DESCRIPTION | If not selected then the description will not be returned with marketCatalogue |
| RUNNER\_DESCRIPTION | If not selected then the runners will not be returned with marketCatalogue |
| RUNNER\_METADATA | If not selected then the runner metadata will not be returned with marketCatalogue. If selected then RUNNER\_DESCRIPTION will also be returned regardless of whether it is included as a market projection. |

PriceData

#FFFFFF#99CC66PriceData

| **Value** | **Description** |
| --- | --- |
| SP\_AVAILABLE | Amount available for the BSP auction. |
| SP\_TRADED | Amount traded in the BSP auction. |
| EX\_BEST\_OFFERS | Only the best prices available for each runner, to requested price depth. |
| EX\_ALL\_OFFERS | EX\_ALL\_OFFERS trumps EX\_BEST\_OFFERS if both settings are present |
| EX\_TRADED | Amount traded on the exchange. |

MatchProjection

#FFFFFF#99CC66MatchProjection

| **Value** | **Description** |
| --- | --- |
| NO\_ROLLUP | No rollup, return raw fragments |
| ROLLED\_UP\_BY\_PRICE | Rollup matched amounts by distinct matched prices per side. |
| ROLLED\_UP\_BY\_AVG\_PRICE | Rollup matched amounts by average matched price per side |

OrderProjection

#FFFFFF#99CC66OrderProjection

| **Value** | **Description** |
| --- | --- |
| ALL | EXECUTABLE and EXECUTION\_COMPLETE orders |
| EXECUTABLE | An order that has a remaining unmatched portion. This is either a fully unmatched or partially matched bet (order) |
| EXECUTION\_COMPLETE | An order that does not have any remaining unmatched portion.  This is a fully matched bet (order). |

MarketStatus

#FFFFFF#99CC66MarketStatus

| **Value** | **Description** |
| --- | --- |
| INACTIVE | The market has been created but isn't yet available. |
| OPEN | The market is open for betting. |
| SUSPENDED | The market is suspended and not available for betting. |
| CLOSED | The market has been settled and is no longer available for betting. |

RunnerStatus

#FFFFFF#99CC66RunnerStatus

| **Value** | **Description** |
| --- | --- |
| ACTIVE | ACTIVE |
| WINNER | WINNER |
| LOSER | LOSER |
| PLACED | The runner was placed, applies to EACH\_WAY marketTypes only. |
| REMOVED\_VACANT | REMOVED\_VACANT applies to Greyhounds. Greyhound markets always return a fixed number of runners (traps). If a dog has been removed, the trap is shown as vacant. |
| REMOVED | REMOVED |
| HIDDEN | The selection is hidden from the market.  This occurs in Horse Racing markets were runners is hidden when it is doesn’t hold an official entry following an entry stage. This could be because the horse was never entered or because they have been scratched from a race at a declaration stage. All matched customer bet prices are set to 1.0 even if there are later supplementary stages. Should it appear likely that a specific runner may actually be supplemented into the race this runner will be reinstated with all matched customer bets set back to the original prices. |

TimeGranularity

#FFFFFF#99CC66TimeGranularity

| **Value** | **Description** |
| --- | --- |
| DAYS |  |
| HOURS |  |
| MINUTES |  |

Side

#FFFFFF#99CC66Side

| **Value** | **Description** |
| --- | --- |
| BACK | To back a team, horse or outcome is to bet on the selection to win. For LINE markets a Back bet refers to a SELL line. A SELL line will win if the outcome is LESS THAN the taken line (price) |
| LAY | To lay a team, horse, or outcome is to bet on the selection to lose. For LINE markets a Lay bet refers to a BUY line. A BUY line will win if the outcome is MORE THAN the taken line (price) |

OrderStatus

#FFFFFF#99CC66OrderStatus

| **Value** | **Description** |
| --- | --- |
| PENDING | An asynchronous order is yet to be processed. Once the bet has been processed by the exchange  (including waiting for any in-play delay), the result will be reported and available on the  Exchange Stream API and API NG.  Not a valid search criteria on MarketFilter |
| EXECUTION\_COMPLETE | An order that does not have any remaining unmatched portion. |
| EXECUTABLE | An order that has a remaining unmatched portion. |
| EXPIRED | The order is no longer available for execution due to its time in force constraint.  In the case of FILL\_OR\_KILL orders, this means the order has been killed because it could not be filled to your specifications.  Not a valid search criteria on MarketFilter |

OrderBy

#FFFFFF#99CC66OrderBy

| **Value** | **Description** |
| --- | --- |
| BY\_BET | @Deprecated Use BY\_PLACE\_TIME instead. Order by placed time, then bet id. |
| BY\_MARKET | Order by market id, then placed time, then bet id. |
| BY\_MATCH\_TIME | Order by time of last matched fragment (if any), then placed time, then bet id. Filters out orders which have no matched date. The dateRange filter (if specified) is applied to the matched date. |
| BY\_PLACE\_TIME | Order by placed time, then bet id. This is an alias of to be deprecated BY\_BET. The dateRange filter (if specified) is applied to the placed date. |
| BY\_SETTLED\_TIME | Order by time of last settled fragment (if any due to partial market settlement), then by last match time, then placed time, then bet id. Filters out orders which have not been settled. The dateRange filter (if specified) is applied to the settled date. |
| BY\_VOID\_TIME | Order by time of last voided fragment (if any), then by last match time, then placed time, then bet id. Filters out orders which have not been voided. The dateRange filter (if specified) is applied to the voided date. |

SortDir

#FFFFFF#99CC66SortDir

| **Value** | **Description** |
| --- | --- |
| EARLIEST\_TO\_LATEST | Order from earliest value to latest e.g. lowest betId is first in the results. |
| LATEST\_TO\_EARLIEST | Order from the latest value to the earliest e.g. highest betId is first in the results. |

OrderType

#FFFFFF#99CC66OrderType

| **Value** | **Description** |
| --- | --- |
| LIMIT | A normal exchange limit order for immediate execution |
| LIMIT\_ON\_CLOSE | Limit order for the auction (SP) |
| MARKET\_ON\_CLOSE | Market order for the auction (SP) |

MarketSort

#FFFFFF#99CC66MarketSort

| **Value** | **Description** |
| --- | --- |
| MINIMUM\_TRADED | Minimum traded volume |
| MAXIMUM\_TRADED | Maximum traded volume |
| MINIMUM\_AVAILABLE | Minimum available to match |
| MAXIMUM\_AVAILABLE | Maximum available to match |
| FIRST\_TO\_START | The closest markets based on their expected start time |
| LAST\_TO\_START | The most distant markets based on their expected start time |

MarketBettingType

#FFFFFF#99CC66MarketBettingType

| **Value** | **Description** |
| --- | --- |
| ODDS | Odds Market - Any market that doesn't fit any any of the below categories. |
| LINE | Line Market - LINE markets operate at even-money odds of 2.0. However, price for these markets refers to the line positions available as defined by the markets min-max range and interval steps. Customers either Buy a line (LAY bet, winning if outcome is greater than the taken line (price)) or Sell a line (BACK bet, winning if outcome is less than the taken line (price)). If settled outcome equals the taken line, stake is returned. |
| RANGE | Range Market - **Now Deprecated** |
| ASIAN\_HANDICAP\_DOUBLE\_LINE | Asian Handicap Market - A traditional Asian handicap market. Can be identified by marketType ASIAN\_HANDICAP |
| ASIAN\_HANDICAP\_SINGLE\_LINE | Asian Single Line Market - A market in which there can be 0 or multiple winners. e,.g marketType TOTAL\_GOALS |
| FIXED\_ODDS | Sportsbook Odds Market. This type is deprecated and will be removed in future releases, when Sportsbook markets will be represented as ODDS market but with a different product type |

ExecutionReportStatus

#FFFFFF#99CC66ExecutionReportStatus

| **Value** | **Description** |
| --- | --- |
| SUCCESS | Order processed successfully |
| FAILURE | Order failed. |
| PROCESSED\_WITH\_ERRORS | The order itself has been accepted, but at least one (possibly all) actions have generated errors. This error only occurs for **replaceOrders**, **cancelOrders** and **updateOrders** operations.  In normal circumstances the placeOrders operation will not return PROCESSED\_WITH\_ERRORS status as it is an atomic operation.  PLEASE NOTE: if the ['Best Execution'](http://en-betfair.custhelp.com/app/answers/detail/a_id/404/~/exchange%3A-what-is-best-price-execution%3F) features is switched off, placeOrders can return ‘PROCESSED\_WITH\_ERRORS’ meaning that some bets can be rejected and other placed when submitted in the same [PlaceInstruction](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Betting+Type+Definitions#BettingTypeDefinitions-PlaceInstruction) |
| TIMEOUT | The order timed out & the status of the bet is unknown. If a TIMEOUT error occurs on a **placeOrders/replaceOrders** request, you should check **listCurrentOrders** to verify the status of your bets before placing further orders. **Please Note:** Timeouts will occur after 5 seconds of attempting to process the bet but please allow up to 15 seconds for a timed out order to appear. After this time any unprocessed bets will automatically be Lapsed and no longer be available on the Exchange. |

ExecutionReportErrorCode

#FFFFFF#99CC66ExecutionReportErrorCode

| **Value** | **Description** |
| --- | --- |
| ERROR\_IN\_MATCHER | The matcher is not healthy. **Please note:** The error will also be returned is you attempt concurrent 'cancel all' bets requests using cancelOrders which isn't permitted. |
| PROCESSED\_WITH\_ERRORS | The order itself has been accepted, but at least one (possibly all) actions have generated errors |
| BET\_ACTION\_ERROR | There is an error with an action that has caused the entire order to be rejected. Check the instructionReports errorCode for the reason for the rejection of the order. |
| INVALID\_ACCOUNT\_STATE | Order rejected due to the account's status (suspended, inactive, dup cards) |
| INVALID\_WALLET\_STATUS | Order rejected due to the account's wallet's status |
| INSUFFICIENT\_FUNDS | Account has exceeded its exposure limit or available to bet limit |
| LOSS\_LIMIT\_EXCEEDED | The account has exceed the self imposed loss limit |
| MARKET\_SUSPENDED | Market is suspended |
| MARKET\_NOT\_OPEN\_FOR\_BETTING | Market is not open for betting. It is either not yet active, suspended or closed awaiting settlement. |
| DUPLICATE\_TRANSACTION | Duplicate customer reference data submitted - **Please note**: There is a time window associated with the de-duplication of duplicate submissions which is 60 second |
| INVALID\_ORDER | Order cannot be accepted by the matcher due to the combination of actions. For example, bets being edited are not on the same market, or order includes both edits and placement |
| INVALID\_MARKET\_ID | Market doesn't exist |
| PERMISSION\_DENIED | Business rules do not allow order to be placed. You are either attempting to place the order using a Delayed Application Key or from a restricted jurisdiction (i.e. USA) |
| DUPLICATE\_BETIDS | Duplicate bet ids found. For example, you've included the same betId more than once in a single cancelOrders request. |
| NO\_ACTION\_REQUIRED | Order hasn't been passed to matcher as system detected there will be no state change |
| SERVICE\_UNAVAILABLE | The requested service is unavailable |
| REJECTED\_BY\_REGULATOR | The regulator rejected the order. On the **Italian Exchange** this error will occur if more than 50 bets are sent in a single placeOrders request. |
| NO\_CHASING | A specific error code that relates to Spanish Exchange markets only which indicates that the bet placed contravenes the Spanish regulatory rules relating to loss chasing. |
| REGULATOR\_IS\_NOT\_AVAILABLE | The underlying regulator service is not available. |
| TOO\_MANY\_INSTRUCTIONS | The amount of orders exceeded the maximum amount allowed to be executed |
| INVALID\_MARKET\_VERSION | The supplied market version is invalid. Max length allowed for market version is 12. |
| INVALID\_PROFIT\_RATIO | The order falls outside the permitted price and size combination. |
| NO\_CHANGE | Trying to update the persistence type to the one it already has. |

PersistenceType

#FFFFFF#99CC66PersistenceType

| **Value** | **Description** |
| --- | --- |
| LAPSE | Lapse (cancel) the order automatically when the market is turned in play if the bet is unmatched |
| PERSIST | Persist the unmatched order to in-play. The bet will be placed automatically into the in-play market at the start of the event.  Once in play, the bet won't be cancelled by Betfair if a material event takes place and will be available until matched or cancelled by the user |
| MARKET\_ON\_CLOSE | Put the order into the auction (SP) at turn-in-play |

InstructionReportStatus

#FFFFFF#99CC66InstructionReportStatus

| **Value** | **Description** |
| --- | --- |
| SUCCESS | The instruction was successful. |
| FAILURE | The instruction failed. |
| TIMEOUT | The order timed out & the status of the bet is unknown. If a TIMEOUT error occurs on a **placeOrders/replaceOrders** request, you should check **listCurrentOrders** to verify the status of your bets before placing further orders. **Please Note:** Timeouts will occur after 5 seconds of attempting to process the bet but please allow up to 15 seconds for a timed out order to appear. After this time any unprocessed bets will automatically be Lapsed and no longer be available on the Exchange. |

InstructionReportErrorCode

#FFFFFF#99CC66InstructionReportErrorCode

| **Value** | **Description** |
| --- | --- |
| INVALID\_BET\_SIZE | The bet size is invalid for your currency or your regulator. Please check the bet size conforms to the Min Bet Size for your currency. Please see Currency Parameters for further details. |
| INVALID\_RUNNER | Runner does not exist, includes vacant traps in greyhound racing |
| BET\_TAKEN\_OR\_LAPSED | Bet cannot be cancelled or modified as it has already been taken or has been cancelled/lapsed Includes attempts to cancel/modify market on close BSP bets and cancelling limit on close BSP bets. The error may be returned on placeOrders request if for example a bet is placed at the point when a market admin event takes place (i.e. market is turned in-play).  The error will also be returned if a  market version is submitted and a material change has taken place since the bet was submitted causing the bet to be rejected. |
| BET\_IN\_PROGRESS | No result was received from the matcher in a timeout configured for the system |
| RUNNER\_REMOVED | Runner has been removed from the event |
| MARKET\_NOT\_OPEN\_FOR\_BETTING | Attempt to edit a bet on a market that has closed. |
| LOSS\_LIMIT\_EXCEEDED | The action has caused the account to exceed the self imposed loss limit |
| MARKET\_NOT\_OPEN\_FOR\_BSP\_BETTING | Market now closed to bsp betting. Turned in-play or has been reconciled |
| INVALID\_PRICE\_EDIT | Attempt to edit down the price of a bsp limit on close lay bet, or edit up the price of a limit on close back bet |
| INVALID\_ODDS | Odds not on price ladder - either edit or placement |
| INSUFFICIENT\_FUNDS | Insufficient funds available to cover the bet action. Either the exposure limit or available to bet limit would be exceeded |
| INVALID\_PERSISTENCE\_TYPE | Invalid persistence type for this market, e.g. KEEP for a non in-play market or KEEP for markets with PASSIVE betDelayModels. |
| ERROR\_IN\_MATCHER | A problem with the matcher prevented this action completing successfully |
| INVALID\_BACK\_LAY\_COMBINATION | The order contains a back and a lay for the same runner at overlapping prices. This would guarantee a self match. This also applies to BSP limit on close bets |
| ERROR\_IN\_ORDER | The action failed because the parent order failed |
| INVALID\_BID\_TYPE | Bid type is mandatory |
| INVALID\_BET\_ID | Bet for id supplied has not been found |
| CANCELLED\_NOT\_PLACED | Bet cancelled but replacement bet was not placed |
| RELATED\_ACTION\_FAILED | Action failed due to the failure of a action on which this action is dependent |
| NO\_ACTION\_REQUIRED | the action does not result in any state change. eg changing a persistence to it's current value |
| TIME\_IN\_FORCE\_CONFLICT | You may only specify a time in force on either the place request OR on individual limit order instructions (not both),  since the implied behaviors are incompatible. |
| UNEXPECTED\_PERSISTENCE\_TYPE | You have specified a persistence type for a FILL\_OR\_KILL order, which is nonsensical because no umatched portion  can remain after the order has been placed. |
| INVALID\_ORDER\_TYPE | You have specified a time in force of FILL\_OR\_KILL, but have included a non-LIMIT order type. |
| UNEXPECTED\_MIN\_FILL\_SIZE | You have specified a minFillSize on a limit order, where the limit order's time in force is not FILL\_OR\_KILL.  Using minFillSize is not supported where the time in force of the request (as opposed to an order) is FILL\_OR\_KILL. |
| INVALID\_CUSTOMER\_ORDER\_REF | The supplied customer order reference is too long. |
| INVALID\_MIN\_FILL\_SIZE | The minFillSize must be greater than zero and less than or equal to the order's size.  The minFillSize cannot be less than the minimum bet size for your currency |
| BET\_LAPSED\_PRICE\_IMPROVEMENT\_TOO\_LARGE | Your bet is lapsed. There is better odds than requested available in the market, but your  preferences don't allow the system to match your bet against better odds. Change your betting  preferences to accept better odds if you don't want to receive this error.  **Please see** [**https://support.betfair.com/app/answers/detail/a\_id/404/**](https://support.betfair.com/app/answers/detail/a_id/404/) **for more details regarding Best Execution and how to update your settings.** |

RollupModel

GroupBy

#FFFFFF#99CC66GroupBy

| **Value** | **Description** |
| --- | --- |
| EVENT\_TYPE | A roll up of settled P&L, commission paid and number of bet orders, on a specified event type |
| EVENT | A roll up of settled P&L, commission paid and number of bet orders, on a specified event |
| MARKET | A roll up of settled P&L, commission paid and number of bet orders, on a specified market. Does not include **LAPSED** or **CANCELLED** bets. |
| SIDE | An averaged roll up of settled P&L, and number of bets, on the specified side of a specified selection within a specified market, that are either settled or voided |
| BET | The P&L, side and regulatory information etc, about each individual bet order. Use to retrieve details of **LAPSED** or **CANCELLED** bets |

BetStatus

#FFFFFF#99CC66 BetStatus

| **Value** | **Description** |
| --- | --- |
| SETTLED | A matched bet that was settled normally |
| VOIDED | A matched bet that was subsequently voided by Betfair, before, during or after settlement |
| LAPSED | Unmatched bet that was cancelled by Betfair (for example at turn in play). |
| CANCELLED | Unmatched bet that was cancelled by an explicit customer action. |

legacydata

#FFFFFF#99CC66marketType - Legacy Data

| **Value** | **Description** |
| --- | --- |
| A | Asian Handicap |
| L | Line market |
| O | Odds market |
| R | Range market. |
| NOT\_APPLICABLE | The market does not have an applicable marketType. |

#FFFFFF#99CC66TimeInForce

timeinforce

| **Value** | **Description** |
| --- | --- |
| FILL\_OR\_KILL | Execute the transaction immediately and completely (filled to size or between minFillSize and size) or not at all (cancelled).  For LINE markets Volume Weighted Average Price (VWAP) functionality is disabled |

#FFFFFF#99CC66BetTargetType

| **Value** | **Description** |
| --- | --- |
| BACKERS\_PROFIT | The payout requested minus the calculated size at which this LimitOrder is to be placed. BetTargetType bets are invalid for LINE markets |
| PAYOUT | The total payout requested on a LimitOrder |

PriceLadderType

#FFFFFF#99CC66PriceLadderType

| **Value** | **Description** |
| --- | --- |
| CLASSIC | Price ladder increments traditionally used for Odds Markets. |
| FINEST | Price ladder with the finest available increment, traditionally used for  Asian Handicap markets. |
| LINE\_RANGE | Price ladder used for LINE markets. Refer to MarketLineRangeInfo for more details. |

#FFFFFF#99CC66BetDelayModel

fc4e268c-d306-40ef-9e06-3f3220d620ac

| **Value** | **Description** |
| --- | --- |
| PASSIVE | For in-play markets where betDelay > 0, orders that are guaranteed not to match immediately are accepted straight away, bypassing the bet delay wait.  Order requirements (otherwise bets will be subject to the usual bet delay before being placed).   * Only plain LIMIT orders are supported.  * Allowed persistenceType: LAPSE  * The following attributes are not supported and must be omitted: timeInForce, minFillSize, betTargetType |
| DYNAMIC | Indicates market is subject to dynamic in-play bet delays. This mean that the in-play betDelay will vary while the market is turned in-play.  **Please note:** Currently returned for Tennis markets only. Specifically, every game 3,5,7,9,11 or game which decides a set (potentially 6,8,10,12) the betDelay is reduced to 1 second. |
