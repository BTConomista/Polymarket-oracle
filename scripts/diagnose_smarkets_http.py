"""Diagnosi in sola lettura dell'accesso pubblico Smarkets dal runner."""
import json
import subprocess
import time
import urllib.error
import urllib.request

URL = "https://api.smarkets.com/v3/events/?type=football_match&state=upcoming&limit=1"

def probe(label, headers):
    request = urllib.request.Request(URL, headers=headers)
    try:
        response = urllib.request.urlopen(request, timeout=30)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        body = response.read(1200).decode("utf-8", errors="replace")
        print(json.dumps({"client": label, "status": response.status,
                          "headers": {k: v for k, v in response.headers.items()
                                      if k.lower() in {"server", "content-type", "cf-mitigated", "retry-after"}},
                          "body": body}, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    probe("urllib default", {})
    time.sleep(2)
    probe("urllib JSON", {"Accept": "application/json",
                         "User-Agent": "Polymarket-Oracle/1.0 (+https://github.com/BTConomista/Polymarket-oracle)"})
    time.sleep(2)
    subprocess.run(["curl", "--silent", "--show-error", "--max-time", "30",
                    "--include", URL], check=False)
