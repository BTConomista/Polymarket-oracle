# placeOrders

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687496>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687496`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

2flatpipe

## Operation

placeOrders

#FFFFFF#C8D0E4placeOrders **PlaceExecutionReport**   **(** **StringmarketId** ,  **List< PlaceInstruction >instructions, String customerRef, MarketVersion marketVersion, String customerStrategyRef, boolean async **)****  **throws APINGException** 

Place new orders into market. Please note that additional [bet sizing rules](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687808/Betting+On+Italian+Exchange) apply to bets placed into the Italian Exchange.

In normal circumstances the placeOrders is an atomic operation.  PLEASE NOTE: if the ['Best Execution'](http://en-betfair.custhelp.com/app/answers/detail/a_id/404/~/exchange%3A-what-is-best-price-execution%3F) features is switched off, placeOrders can return ‘PROCESSED\_WITH\_ERRORS’ meaning that some bets can be rejected and other placed when submitted in the same [PlaceInstruction](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Betting+Type+Definitions#BettingTypeDefinitions-PlaceInstruction)

| Parameter name | Type | Required | Description |
| --- | --- | --- | --- |
| marketId | String |  | The market id these orders are to be placed on |
| instructions | List< PlaceInstruction > |  | The number of place instructions.  The limit of place instructions per request is 200 for the Global Exchange and 50 for the Italian Exchange. |
| customerRef | String |  | Optional parameter allowing the client to pass a unique string (up to 32 chars) that is used to de-dupe mistaken re-submissions.   customerRef can contain: upper/lower chars, digits, chars : - . \_ + \* : ; ~ only.  **Please note:** There is a time window associated with the de-duplication of duplicate submissions which is 60 seconds.  **NB:** This field does not persist into the placeOrders response/Order Stream API and should not be confused with **customerOrderRef**, which is separate field that can be sent in the PlaceInstruction. |
| marketVersion | MarketVersion |  | Optional parameter allowing the client to specify which version of the market the  orders should be placed on. If the current market version is higher than that sent on an order,  the bet will be lapsed. |
| customerStrategyRef | String |  | An optional reference customers can use to specify which strategy has sent the order.  The reference will be returned on order change messages through the stream API. The string is  limited to 15 characters. If an empty string is provided it will be treated as null. |
| async | boolean |  | An optional flag (not setting equates to false) which specifies if the orders should be placed asynchronously.  Orders can be tracked via the Exchange Stream API or or the API-NG by providing a customerOrderRef for each place order.  An order's status will be PENDING and no bet ID will be returned.  This functionality is available for all bet types - including Market on Close and Limit on Close |

| Return type | Description |
| --- | --- |
| PlaceExecutionReport |  |

| Throws | Description |
| --- | --- |
| APINGException | Generic exception that is thrown if this operation fails for any reason. |

**Since 1.0.0**

### Placing a Bet

To place a bet you require the marketId and selectionId parameters from the  API call. The below parameters will place a normal Exchange bet at odds of 3.0 for a stake of £2.0.

If the bet is placed successfully, a betId is returned in the placeOrders response

****placeOrders Request****

[
{
"jsonrpc": "2.0",
"method": "SportsAPING/v1.0/placeOrders",
"params": {
"marketId": "1.109850906",
"instructions": [
{
"selectionId": "237486",
"handicap": "0",
"side": "LAY",
"orderType": "LIMIT",
"limitOrder": {
"size": "2",
"price": "3",
"persistenceType": "LAPSE"
}
}
]
},
"id": 1
}
]

****placeOrders Response****

[
{
"jsonrpc": "2.0",
"result": {
"marketId": "1.109850906",
"instructionReports": [
{
"instruction": {
"selectionId": 237486,
"handicap": 0,
"limitOrder": {
"size": 2,
"price": 3,
"persistenceType": "LAPSE"
},
"orderType": "LIMIT",
"side": "LAY"
},
"betId": "31242604945",
"placedDate": "2013-10-30T14:22:47.000Z",
"averagePriceMatched": 0,
"sizeMatched": 0,
"status": "SUCCESS"
}
],
"status": "SUCCESS"
},
"id": 1
}
]

### Placing a Betfair SP Bet - MARKET\_ON\_CLOSE

To place a bet on a selection at Betfair SP (MARKET\_ON\_CLOSE) you need to specify the parameters below in the placeOrders request. The below example would place a Betfair SP back bet on the required selection for a stake of £2.00.

****placeOrders Request****

[
{
"jsonrpc": "2.0",
"method": "SportsAPING/v1.0/placeOrders",
"params": {
"marketId": "1.111836557",
"instructions": [
{
"selectionId": "5404312",
"handicap": "0",
"side": "BACK",
"orderType": "MARKET\_ON\_CLOSE",
"marketOnCloseOrder": {
"liability": "2"
}
}
]
},
"id": 1
}
]

****placeOrders Response****

[
{
"jsonrpc": "2.0",
"result": {
"marketId": "1.111836557",
"instructionReports": [
{
"instruction": {
"selectionId": 5404312,
"handicap": 0,
"marketOnCloseOrder": {
"liability": 2
},
"orderType": "MARKET\_ON\_CLOSE",
"side": "BACK"
},
"betId": "31645233727",
"placedDate": "2013-11-12T12:07:29.000Z",
"status": "SUCCESS"
}
],
"status": "SUCCESS"
},
"id": 1
}
]

### Placing a Betfair SP Bet - LIMIT\_ON\_CLOSE

Below is an example of a Betfair SP Bet - using the orderType LIMIT\_ON\_CLOSE.  Please refer to [Additional Information#CurrencyParameters](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Additional+Information#AdditionalInformation-CurrencyParameters) for **Min BSP liability for LAY bets**.  The below example show a LIMIT\_ON\_CLOSE BACK order for a minimum price of 5.0 and a stake of £2.

**placeOrders Request**

[{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", "params": {"marketId":"1.185101721","instructions":[{"selectionId":"35701728","handicap":"0","side":"BACK","orderType":"LIMIT\_ON\_CLOSE","limitOnCloseOrder":{"price":"5.0","liability":"2"}}]}, "id": 1}]

**placeOrders Response**

[{"jsonrpc":"2.0","result":{"status":"SUCCESS","marketId":"1.185101721","instructionReports":[{"status":"SUCCESS","instruction":{"selectionId":35701728,"handicap":0.0,"limitOnCloseOrder":{"liability":2.0,"price":5.0},"orderType":"LIMIT\_ON\_CLOSE","side":"BACK"},"betId":"237695599651","placedDate":"2021-07-08T08:45:54.000Z"}]},"id":1}]

**Placing a 'Keep' Bet**

To place a bet that will be kept once a market turns in-play (if unmatched), you must include the below parameters i.e. "persistenceType": "PERSIST"

The bet will then be placed automatically into the in-play market at the start of the event.

**placeOrders Request**

[
{
"jsonrpc": "2.0",
"method": "SportsAPING/v1.0/placeOrders",
"params": {
"marketId": "1.109850906",
"instructions": [
{
"selectionId": "237486",
"handicap": "0",
"side": "LAY",
"orderType": "LIMIT",
"limitOrder": {
"size": "2",
"price": "3",
"persistenceType": "PERSIST"
}
}
]
},
"id": 1
}
]

**placeOrders Response**

[
{
"jsonrpc": "2.0",
"result": {
"marketId": "1.109850906",
"instructionReports": [
{
"instruction": {
"selectionId": 237486,
"handicap": 0,
"limitOrder": {
"size": 2,
"price": 3,
"persistenceType": "PERSIST"
},
"orderType": "LIMIT",
"side": "LAY"
},
"betId": "31242604945",
"placedDate": "2013-10-30T14:22:47.000Z",
"averagePriceMatched": 0,
"sizeMatched": 0,
"status": "SUCCESS"
}
],
"status": "SUCCESS"
},
"id": 1
}
]

## **Betting Enhancements**

### **Fill or Kill bets**

By setting the optional parameter ‘**TimeInForce**’ on a**limitOrder** submission to the value ‘FILL\_OR\_KILL’ and optionally passing a **minFillSize**value, the Exchange will only match the order if at  least the specified **minFillSize** can be matched (if passed) or the whole order matched (if not).  Any order which cannot be so matched, and any remaining unmatched part of the order (if minFillSize is specified) will be immediately cancelled.

**Please note:**  the matching algorithm for Fill or Kill orders behaves slightly differently to that for standard limit orders.  Whereas the price on a limit order represents the lowest price at which any fragment should be matched, the price on a Fill or Kill order represents the lower limit of the Volume Weighted Average Price (“VWAP”) for the entire volume matched.  So, for instance, a Fill or Kill order with price = 5.4 and size = 10 might be matched as £2 @ 5.5, £6 @ 5.4 and £2 @ 5.3.

#### Examples

**FILL\_OR\_KILL order which was lapsed:**

Request[{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", "params": {"marketId":"1.126124422","instructions":[{"selectionId":"10590221","handicap":"0","side":"BACK","orderType":"LIMIT","limitOrder":{"size":"5","price":"21","persistenceType":"LAPSE","timeInForce":"FILL\_OR\_KILL","minFillSize":"5"}}]}, "id": 1}]Response[{"jsonrpc":"2.0","result":{"status":"SUCCESS","marketId":"1.126124422","instructionReports":[{"status":"SUCCESS","instruction":{"selectionId":10590221,"handicap":0.0,"limitOrder":{"size":5.0,"price":21.0,"minFillSize":5.0,"timeInForce":"FILL\_OR\_KILL"},"orderType":"LIMIT","side":"BACK"},"betId":"72666364933","placedDate":"2016-08-12T10:45:15.000Z","averagePriceMatched":0.0,"sizeMatched":0.0}]},"id":1}]

**FILL\_OR KILL requesting a minimum fill size of 3.00:**

Request[{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", "params": {"marketId":"1.126124422","instructions":[{"selectionId":"10590221","handicap":"0","side":"BACK","orderType":"LIMIT","limitOrder":{"size":"5","price":"21","persistenceType":"LAPSE","timeInForce":"FILL\_OR\_KILL","minFillSize":"3"}}]}, "id": 1}]Response[{"jsonrpc":"2.0","result":{"status":"SUCCESS","marketId":"1.126124422","instructionReports":[{"status":"SUCCESS","instruction":{"selectionId":10590221,"handicap":0.0,"limitOrder":{"size":5.0,"price":21.0,"minFillSize":3.0,"timeInForce":"FILL\_OR\_KILL"},"orderType":"LIMIT","side":"BACK"},"betId":"72666433304","placedDate":"2016-08-12T10:47:42.000Z","averagePriceMatched":21.32267441860465,"sizeMatched":3.4400000000000004}]},"id":1}]

### **Market version parameter**

We have added an additional optional parameter ‘**marketVersion**’ to the ‘[**placeOrders**’](http://docs.developer.betfair.com/docs/display/1smk3cen4v3lu3yomq5qye0ni/placeOrders) and ‘[**replaceOrders**’](http://docs.developer.betfair.com/docs/display/1smk3cen4v3lu3yomq5qye0ni/replaceOrders) operations.  The MarketBook data item, which contains the dynamic data on a market, including its prices, has always returned an integer market ‘version’.  This ‘version’ is incremented when significant events – runner removal, turn in-play etc. – occur.  Now, by passing that version as ‘marketVersion’ with your orders, you can specify that if the market version has been incremented beyond that value, your orders should lapse and not be submitted for matching.

This functionality should be of use to those who want to bet right up to the actual ‘off’ of a horse race or sporting event but be confident that you’re not inadvertently bet into the first seconds of in-play after the off.  Similarly, in managed football markets, you can avoid your bets reaching the Exchange after the market has reformed following a goal being scored etc.

**Notes on 'version'****behavior**

The ‘market version’ value (on listMarketBook and on ESA) is incremented for any and all changes to the market.

However, to prevent falsely blocking bets we keep track of the last material change (which we define as one performed under suspension\*\*) and will only accept bets placed with that version or later.

|  | Market Version | Minimum version to not be rejected | Expected behaviour |
| --- | --- | --- | --- |
| Market Activated | 1234 | 1234 |  |
| Start time updated (market not suspended) | 1235 | 1234 | Non-material change, bets placed before change but received after will be processed normally |
| Runner removed (under suspension) | 1236 | 1236 | Material change, bets placed before change but received after will be rejected. |
| Market turned in-play | 1237 | 1237 | As above |

\*\* this includes:

**-          Runner removal and addition**

**-          Turn in-play**

**-          Lapsing or voiding bets (eg on goals being scored in managed Football** market)

But not (e.g.) updating Tennis court times or Golf tee times as they become more accurately known on the day.

Example of a request including market version:

[{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", "params": {"marketId":"1.126086207","instructions":[{"selectionId":"63908","handicap":"0","side":"BACK","orderType":"LIMIT","limitOrder":{"size":"2","price":"30"}}],"marketVersion":{"version":"123456789"}}, "id": 1}]

Example of request and response were market version is rejected due to a material change

**Request**

[{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", "params": {"marketId":"1.192357130","instructions":[{"selectionId":"3531817","handicap":"0","side":"BACK","orderType":"LIMIT","limitOrder":{"size":"2","price":"1000"}}],"marketVersion":{"version":"4249587130"}}, "id": 1}]

**Response**

[{"jsonrpc":"2.0","result":{"status":"FAILURE","errorCode":"BET\_ACTION\_ERROR","marketId":"1.192357130","instructionReports":[{"status":"FAILURE","errorCode":"BET\_TAKEN\_OR\_LAPSED","instruction":{"selectionId":3531817,"handicap":0.0,"limitOrder":{"size":2.0,"price":1000.0,"persistenceType":"LAPSE"},"orderType":"LIMIT","side":"BACK"},"betId":"253638292039","placedDate":"2021-12-15T11:05:58.000Z","averagePriceMatched":0.0,"sizeMatched":0.0,"orderStatus":"EXECUTION\_COMPLETE"}]},"id":1}]

### **Bet to Payout or Profit/Liability**

Place a bet specifying your target payout, profit or liability, instead of the backers stake ('size').

Currently, [best execution](http://en-betfair.custhelp.com/app/answers/detail/a_id/404/~/exchange%3A-what-is-best-execution%3F), which guarantees that you’ll receive the best possible price, means that you receive a greater potential payout to the same stakes (or risk a smaller potential payout to the same backer’s stakes, for layers).

If you  wish to benefit by receiving the same potential payout as you originally requested, but to smaller stakes, you can now specify on a LimitOrder ([placeOrders](http://docs.developer.betfair.com/docs/display/1smk3cen4v3lu3yomq5qye0ni/placeOrders)) an optional ‘betTargetType’ of ‘PAYOUT’ or ‘BACKERS\_PROFIT’ (the latter being identical to layers’ liability) and a ‘betTargetSize’ representing the value of that payout or profit, together with the usual ‘price’ parameter to represent their limit price.  Your bet will then be matched to achieve that payout or profit at the specified price or better.

Should all or any of the order be unmatched after first reaching the Exchange, the unmatched portion will be expressed in standard price and backers’ stake terms (by dividing the remaining unmatched payout by the price, or unmatched profit by the price – 1, and placed on the unmatched queue), after this point the bet behaves like any other.

**Please note: This function is only enabled for UK & International customers and not .it, .es, .dk and .se jurisdictions.**

#### **Examples**

**Placing a back bet targeting a £2 profit**

Request[{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", "params": {"marketId":"1.126124417","instructions":[{"selectionId":"11166583","handicap":"0","side":"BACK","orderType":"LIMIT","limitOrder":{"price":"2","betTargetType":"BACKERS\_PROFIT","betTargetSize":"2"}}]}, "id": 1}]Response

 [{"jsonrpc":"2.0","result":{"status":"SUCCESS","marketId":"1.126124417","instructionReports":[{"status":"SUCCESS","instruction":{"selectionId":11166583,"handicap":0.0,"limitOrder":{"price":2.0,"betTargetSize":2.0,"persistenceType":"LAPSE","betTargetType":"BACKERS\_PROFIT"},"orderType":"LIMIT","side":"BACK"},"betId":"72671225671","placedDate":"2016-08-12T13:00:23.000Z","averagePriceMatched":6.3999999999999995,"sizeMatched":0.37}]},"id":1}]

**Placing a lay bet targeting a £10 Payout**

Request[{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", "params": {"marketId":"1.126122473","instructions":[{"selectionId":"11576316","handicap":"0","side":"LAY","orderType":"LIMIT","limitOrder":{"price":"10","betTargetType":"PAYOUT","betTargetSize":"10"}}]}, "id": 1}]Response[{"jsonrpc":"2.0","result":{"status":"SUCCESS","marketId":"1.126122473","instructionReports":[{"status":"SUCCESS","instruction":{"selectionId":11576316,"handicap":0.0,"limitOrder":{"price":10.0,"betTargetSize":10.0,"persistenceType":"LAPSE","betTargetType":"PAYOUT"},"orderType":"LIMIT","side":"LAY"},"betId":"72671531256","placedDate":"2016-08-12T13:05:45.000Z","averagePriceMatched":4.2,"sizeMatched":2.38}]},"id":1}]

### **Ability to place lower minimum stakes at larger prices**

In order to allow customers to bet to smaller stakes on longer-priced selections, an extra property has been added to our Currency Parameters – “Min Bet Payout”.

As currently LIMIT bets where the backer’s stake is at and above the ‘Min Bet Size’ for the currency concerned (£1 for GBP) are valid.   In addition, bets below this value are valid if the payout of the bet would be equal to or greater than the value of ‘**Min Bet Payout’** - £10 for GBP.  For example, a bet of £1 @ 10, or 10p @ 100 or 1p @ 1000 are all valid as they all target a payout of £10 or more.

This functionality is available to "orderType: LIMIT" bets only.

**Please note: This function is only enabled for UK & International customers and not .it, .es, .dk and **.se jurisdictions**.**

### Each Way Betting

Each Way betting is available via the API.  Each Way markets can be identified as marketType EACH\_WAY using listMarketCatalogue.

**Please note:** your potential liability for an each way bet is 'size' x 2, so for a 10 size bet your available to bet balance will be reduced by 20, for example.

The divisor that applies to the EACH\_WAY market is returned by listMarketCatalogue via the MARKET\_DESCRIPTION MarketProjection.

Please see table a table that indicates how the “Each-Way divisor" is determined for specific race types:

|  |  |  |  |
| --- | --- | --- | --- |
| Race Type | Number of Runners(1) | Number of Places | Fraction of Win Odds “Each-Way divisor" |
| Handicap | 16 or more | 4 | 1/4 |
| Handicap | 12 to 15 | 3 | 1/4 |
| Handicap | 8 to 11 | 3 | 1/5 |
| Handicap | 5 to 7 | 2 | 1/4 |
| Non-Handicap | 8 or more | 3 | 1/5 |
| Non-Handicap | 5 to 7 | 2 | 1/4 |

**(1)**   Number of Runners at Market creation time; place terms are fixed for the life of the market (like Betfair Place market) not dependent on number of runners at the off (like Fixed Odds EW markets)

We will not offer EW markets if the number of runners at market creation time is 4 or fewer

### Betfair Price Increments

Below is a list of price increments per price 'group'.  Placing a bet outside of these increments will result in an **INVALID\_ODDS** error

**Odds Markets**

| Price | Increment |
| --- | --- |
| 1.01 → 2 | 0.01 |
| 2→ 3 | 0.02 |
| 3 → 4 | 0.05 |
| 4 → 6 | 0.1 |
| 6 → 10 | 0.2 |
| 10 → 20 | 0.5 |
| 20 → 30 | 1 |
| 30 → 50 | 2 |
| 50 → 100 | 5 |
| 100 → 1000 | 10 |

**Asian Handicap & Total Goal Markets**

| Price | Increment |
| --- | --- |
| 1.01 → 1000 | 0.01 |

### Currency Parameters currency

Guide to **[available currencies and minimum bet sizes](http://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Additional+Information#AdditionalInformation-CurrencyParameters)****.**
