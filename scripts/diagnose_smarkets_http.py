"""Verifica in sola lettura il client Smarkets dal runner, senza salvare prezzi."""
from fetch_smarkets_outrights import _get, OUTRIGHT_NODE

def main():
    first = None
    for label, path in (
        ("pre-partita", "/events/?type=football_match&state=upcoming&limit=1"),
        ("live", "/events/?type=football_match&state=live&limit=1"),
        ("outright", f"/events/?parent_id={OUTRIGHT_NODE}&limit=1"),
    ):
        data = _get(path)
        assert isinstance(data.get("events"), list), f"{label}: risposta senza events"
        print(f"{label}: OK, {len(data['events'])} eventi nella pagina", flush=True)
        if label == "pre-partita" and data["events"]:
            first = data["events"][0]
    if first:
        markets = _get(f"/events/{first['id']}/markets/")["markets"]
        assert markets, "evento senza mercati: prezzi non verificati"
        market_id = markets[0]["id"]
        assert "contracts" in _get(f"/markets/{market_id}/contracts/")
        assert isinstance(_get(f"/markets/{market_id}/quotes/"), dict)
        print("mercati, contratti e libro quote: OK", flush=True)

if __name__ == "__main__":
    main()
