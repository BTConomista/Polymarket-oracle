# Login & Session Management

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687869>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687869`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

Home | API Status | Historical Data | Vendor Program | Developer Forum Login & Session Management{"id":"EJyr1dNQxAJdJguiodbJA","name":"page","children":[{"id":"iOCUkGtPzoYzSRQ\_IZAXO","params":{"background":{"light":"#ffffff99","dark":"#1d212599"},"padding":20,"gap":10,"backgroundSize":"contain","image":{"value":"att19398657","target":"\_blank","type":"attachment"}},"children":[],"name":"section"},{"params":{"padding":0,"gap":0,"image":{"value":"https://images.unsplash.com/photo-1554034483-04fda0d3507b?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3wzMzg3MzF8MHwxfHNlYXJjaHw2fHxncmFkaWVudHxlbnwwfDB8fHwxNzAyMzkyMDI1fDA&ixlib=rb-4.0.3&q=80&w=1080","target":"\_self","type":"link"},"background":{"type":"solid","dark":"#1D2125","light":"#000000"}},"children":[{"name":"row","children":[{"name":"column","children":[{"name":"text","params":{"templateId":"headline 2","value":[{"type":"paragraph","children":[{"type":"paragraph","children":[{"text":"","fontSize":18},{"type":"link","link":{"value":"https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/overview","target":"\_blank","type":"link"},"children":[{"text":"Home","letterSpacing":0,"fontFamily":"Poppins, sans-serif","backgroundColor":{"type":"solid","light":"#000000"},"color":{"type":"solid","light":"#ffffff"},"fontSize":18}]},{"letterSpacing":0,"fontFamily":"Poppins, sans-serif","text":" | ","backgroundColor":{"type":"solid","light":"#000000"},"color":{"type":"solid","light":"#ffffff"},"fontSize":18},{"type":"link","link":{"value":"https://status.developer.betfair.com/","target":"\_blank","type":"link"},"children":[{"letterSpacing":0,"fontFamily":"Poppins, sans-serif","text":"API Status ","backgroundColor":{"type":"solid","light":"#000000"},"color":{"type":"solid","light":"#ffffff"},"fontSize":18}]},{"letterSpacing":0,"fontFamily":"Poppins, sans-serif","text":"| ","backgroundColor":{"type":"solid","light":"#000000"},"color":{"type":"solid","light":"#ffffff"},"fontSize":18},{"type":"link","link":{"value":"https://historicdata.betfair.com/","target":"\_blank","type":"link"},"children":[{"letterSpacing":0,"fontFamily":"Poppins, sans-serif","backgroundColor":{"type":"solid","light":"#000000"},"text":"Historical Data","color":{"type":"solid","light":"#ffffff"},"fontSize":18}]},{"letterSpacing":0,"fontFamily":"Poppins, sans-serif","backgroundColor":{"type":"solid","light":"#000000"},"text":" | ","color":{"type":"solid","light":"#ffffff"},"fontSize":18},{"type":"link","link":{"value":"https://developer.betfair.com/en/vendor-program/the-process/","target":"\_blank","type":"link"},"children":[{"letterSpacing":0,"fontFamily":"Poppins, sans-serif","backgroundColor":{"type":"solid","light":"#000000"},"text":"Vendor Program","color":{"type":"solid","light":"#ffffff"},"fontSize":18}]},{"letterSpacing":0,"fontFamily":"Poppins, sans-serif","backgroundColor":{"type":"solid","light":"#000000"},"text":" | ","color":{"type":"solid","light":"#ffffff"},"fontSize":18},{"type":"link","link":{"value":"https://forum.developer.betfair.com/","target":"\_blank","type":"link"},"children":[{"letterSpacing":0,"fontFamily":"Poppins, sans-serif","text":"Developer Forum","backgroundColor":{"type":"solid","light":"#000000"},"color":{"type":"solid","light":"#ffffff"},"fontSize":18}]},{"text":""}],"align":"center"}]}]},"children":[],"id":"CO2FLq4NeFdddoCtq1lBg"}],"params":{"borderRadius":{"all":0,"btl":0,"bbl":0,"btr":0,"bbr":0,"isIndividualCorners":false},"padding":0,"gap":20,"verticalAlignment":"top"},"id":"rJ16aA1aMkr8JRkTqLleH"},{"name":"column","children":[],"params":{"borderRadius":{"all":0,"btl":0,"bbl":0,"btr":0,"bbr":0,"isIndividualCorners":false},"padding":0,"gap":20,"verticalAlignment":"top"},"id":"7fUpJjIL2DsfQknnq-wa0"},{"name":"column","children":[],"params":{"borderRadius":{"all":0,"btl":0,"bbl":0,"btr":0,"bbr":0,"isIndividualCorners":false},"padding":0,"gap":20,"verticalAlignment":"top"},"id":"PIPX4pcmcW98Txau\_w0mN"},{"name":"column","children":[],"params":{"borderRadius":{"all":0,"btl":0,"bbl":0,"btr":0,"bbr":0,"isIndividualCorners":false},"padding":0,"gap":20,"verticalAlignment":"top"},"id":"cCTICr9-WCCKgM1zihI3a"},{"name":"column","children":[],"params":{"borderRadius":{"all":0,"btl":0,"bbl":0,"btr":0,"bbr":0,"isIndividualCorners":false},"padding":0,"gap":20,"verticalAlignment":"top"},"id":"7tcYt28H6ZBQHonx-iXCM"},{"name":"column","children":[],"params":{"borderRadius":{"all":0,"btl":0,"bbl":0,"btr":0,"bbr":0,"isIndividualCorners":false},"padding":0,"gap":20,"verticalAlignment":"top"},"id":"uu1DjQWXgO\_NO5oXOAHWf"}],"params":{"layout":[1],"gap":10,"minHeight":10,"padding":25,"borderRadius":0,"backgroundColor":{"light":"#000000","dark":"#1C2124"},"size":"full"},"id":"w72\_YQeLVmnO\_3H7W5tTY"}],"name":"section","id":"x\_1tr1IPoFQQqIJn\_2Jii"},{"id":"xq8go2x2nzRB53Gl6mcmu","params":{"background":{"light":"#ffc40099","dark":"#1d21259999"},"padding":0,"gap":10,"image":{"value":"att21397505","target":"\_blank","type":"attachment"}},"children":[{"id":"SwCvX77I8YzeID8el1Ux2","name":"row","children":[{"id":"dZPbWKV2EsN6n\_Qs5Y85N","name":"column","children":[{"name":"text","params":{"templateId":"headline and paragraph","value":[{"type":"paragraph","children":[{"type":"paragraph","children":[{"text":"Login & Session Management","fontWeight":700,"letterSpacing":-3,"lineHeight":"64px","color":{"light":"#000000","dark":"#ffffff"},"fontFamily":"unset","fontSize":48}],"align":"center"}]}]},"children":[],"id":"0TtmjnO-f4xz9ArW2UWHv"}],"params":{"borderRadius":{"all":0,"btl":0,"bbl":0,"btr":0,"bbr":0,"isIndividualCorners":false},"padding":0,"gap":40,"verticalAlignment":"top"}},{"id":"5gTC-wLx6Abt7H\_z-FUDj","name":"column","children":[{"name":"image","params":{"templateId":"full-width","alignment":"center","position":"center center","borderRadius":{"all":10,"bbl":0,"bbr":0,"btl":0,"btr":0,"isIndividualCorners":false},"image":{"value":"https://images.unsplash.com/photo-1524758631624-e2822e304c36?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3wzMzg3MzF8MHwxfHNlYXJjaHw4fHxPZmZpY2V8ZW58MHx8fHwxNjkzNTYzNzQ1fDA&ixlib=rb-4.0.3&q=80&w=1080","target":"\_self","type":"link"}},"children":[],"id":"I9mL3DVNDAKTji5vQM2F7"}],"params":{"borderRadius":{"all":0,"btl":0,"bbl":0,"btr":0,"bbr":0,"isIndividualCorners":false},"padding":0,"gap":40,"verticalAlignment":"top"}},{"id":"sJ\_W6Nh8Xt4FguMmSMhQR","name":"column","children":[],"params":{"borderRadius":{"all":0,"btl":0,"bbl":0,"btr":0,"bbr":0,"isIndividualCorners":false},"padding":0,"gap":40,"verticalAlignment":"top"}},{"id":"YrSohHBn4-xI7LMUQezzu","name":"column","children":[],"params":{"borderRadius":{"all":0,"btl":0,"bbl":0,"btr":0,"bbr":0,"isIndividualCorners":false},"padding":0,"gap":40,"verticalAlignment":"top"}},{"id":"3pjGIxBYtledL6ItUdDL8","name":"column","children":[],"params":{"borderRadius":{"all":0,"btl":0,"bbl":0,"btr":0,"bbr":0,"isIndividualCorners":false},"padding":0,"gap":40,"verticalAlignment":"top"}},{"id":"m8F56VGx\_TDGDmXAo3-XI","name":"column","children":[],"params":{"borderRadius":{"all":0,"btl":0,"bbl":0,"btr":0,"bbr":0,"isIndividualCorners":false},"padding":0,"gap":40,"verticalAlignment":"top"}}],"params":{"layout":[1],"gap":100,"minHeight":100,"padding":10,"borderRadius":0}}],"name":"section"}]}11flatpipe

# Login

The Betfair API offers three login flows for developers, depending on the use case for your application.

:info:atlassian-info#B3D4FF

All API requests should be sent as **POST**.

## **Non-Interactive login**

If you are building an application that will run autonomously, there is a separate login flow to follow to ensure your account remains secure.

## **Interactive login**

If you are building an application that will be used interactively, then this is the flow for you. This flow has two variants:

#### **Interactive login - Desktop Application**

This login flow makes use of Betfair's login pages and allows your app to gracefully handle all errors and redirections in the same way as the Betfair website.

#### **Interactive login - API method**

This flow makes use of a JSON API endpoint and is the simplest way to get started if you are looking to create your own login form.

:info:atlassian-info#B3D4FF

If you're looking for the quickest way to get started, try the curl example in the Interactive login - API Method.

## Login Request Limits

Successful login requests are restricted to **100 requests per minute**.  In the event of a breach of the log in limit, the account will be prevented from creating a new login session for 20 minutes. The error **TEMPORARY\_BAN\_TOO\_MANY\_REQUESTS** will be returned in these circumstances. All existing sessions will continue to be valid.

# Login Method Summary

| **Login Type** | **Use Case** | **Method** | **Pros** | **Cons** | **Recommendation** |
| --- | --- | --- | --- | --- | --- |
| **Non-interactive Login** | Applications running **autonomously** (e.g., bots). | Non-interactive endpoint with **SSL certificate**. | Secure for automation. Recommended for bots. | Requires certificate setup. | ✅ Use if your app runs without user interaction (e.g., bots, scheduled tasks). |
| **Interactive Login – API Login** | Applications needing a **simple integration** with minimal development time. | API login endpoint (username + password, or username + password + 2FA if enabled). | Easiest to implement. Good for most apps. | Less flexible for handling edge cases compared to the embedded login page. | ✅ Use if you want quick setup and don’t need T&Cs or jurisdiction workflows. |
| **Interactive Login – Desktop App** | Applications used **interactively** by a wide range of users. | Embedded **Betfair login pages**. | Handles workflows like T&Cs updates and jurisdiction checks. More flexible for 3rd party apps. | Requires embedding Betfair’s login page. More development effort compared to API login. | ✅ Use if your app is for many users and must handle extra workflows securely. |

# Keep Alive

You can use **Keep-Alive** to extend the session timeout period.

* On the international (.com) Exchange the current session expiry time is 12 hours for all customers (excluding UK & Ireland) and 24 hours for UK & Ireland customers.
* The session expiry time is currently 20 minutes on the Italian & Spanish Exchange.
* You should request Keep Alive within this time to prevent session expiry. If you don't call Keep Alive within the specified timeout period, the session will expire.
* Session times aren't determined or extended based on API activity.

**Please note:** You can configure the timeout via [**My Account**](https://myaccount.betfair.com/accountdetails/mysecurity?showAPI=1) **> Logout Preferences** if required

## Headers

| **Name** | **Description** | **Sample** |
| --- | --- | --- |
| **Accept** (mandatory) | Header that signals that the response should be returned as JSON | application/json |
| **X-Authentication** (mandatory) | Header that represents the session token that needs to be keep alive | Session Token |
| **X-Application** (optional) | Header the Application Key used by the customer to identify the product. | App Key |

 The presence of the "Accept: application/json" header will signal that the service should respond with JSON and not an HTML page

## URL Definition (Global)

|  |
| --- |
| `https://identitysso.betfair.com/api/keepAlive` |

## Other Jurisdictions

Please use the below if your country of residence is in one of the list jurisdictions.

| **Jurisdiction** | **Endpoint** |
| --- | --- |
| Australia & New Zealand | `https://identitysso.betfair.au/api/keepAlive` |
| Italy | `https://identitysso.betfair.it/api/keepAlive` |
| Spain | `https://identitysso.betfair.es/api/keepAlive` |
| Romania | `https://identitysso.betfair.ro/api/keepAlive` |

## Parameters

 The Keep-Alive operation requires no parameters.

## Response structure

|  |
| --- |
| `{`  `"token":"<token_passed_as_header>",`  `"product":"product_passed_as_header",`  `"status":"<status>",`  `"error":"<error>"`  `}` |

## Status values

|  |
| --- |
| `SUCCESS`  `FAIL` |

## Error values

|  |
| --- |
| `INPUT_VALIDATION_ERROR`  `INTERNAL_ERROR`  `NO_SESSION` |

## Call sample

**Request**

|  |
| --- |
| `curl -k -i -H "Accept: application/json"` `-H "X-Application: AppKey"` `-H "X-Authentication: <token>"` `https://`[identitysso.betfair.com/api/keepAlive](http://identitysso.betfair.com/api/keepAlive) |

**Response**

|  |
| --- |
| `curl -k -i -H "Accept: application/json"` `-H "X-Application: AppKey"` `-H "X-Authentication: SESSIONTOKEN"` `https://`[identitysso.betfair.com/api/keepAlive](http://identitysso.betfair.com/api/keepAlive)    `{`  `"token":"SESSIONTOKEN",`  `"product":"AppKey",`  `"status":"SUCCESS",`  `"error":""`  `}` |

# Logout

You can use Logout to terminate your existing session.

## URL Definition

https://identitysso.betfair.com/api/logout

The presence of the "Accept: application/json" header will signal that the service should respond with JSON and not an HTML page

## Headers

| **Name** | **Description** | **Sample** |
| --- | --- | --- |
| **Accept** (mandatory) | Header that signals that the response should be returned as JSON | application/json |
| **X-Authentication** (mandatory) | Header that represents the session token created at login. | Session Token |
| **X-Application** (optional) | Header the Application Key used by the customer to identify the product. | App Key |

## Response structure

|  |
| --- |
| `{`  `"token":"<token_passed_as_header>",`  `"product":"product_passed_as_header",`  `"status":"<status>",`  `"error":"<error>"`  `}` |

## Status values

|  |
| --- |
| `SUCCESS`  `FAIL` |

## Error values

|  |
| --- |
| `INPUT_VALIDATION_ERROR`  `INTERNAL_ERROR`  `NO_SESSION` |

## Call sample

|  |
| --- |
| `# full request`  `curl -k -i -H "Accept: application/json"` `-H "X-Application: AppKey"` `-H "X-Authentication: <token>"` `https://`[identitysso.betfair.com/api/logout](http://identitysso.betfair.com/api/logout) |
