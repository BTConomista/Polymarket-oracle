#!/usr/bin/env python3
"""Scarica le quote di CHIUSURA 1xBet da footiqo.com (wpDataTables server-side).

Contesto: caccia al dato vero "O/U 2.5 di CHIUSURA 2017-18 / 2018-19" sulle 5
leghe. footiqo.com espone un database pubblico (tab "Odds") con colonne
xbetClose* = quote di CHIUSURA del bookmaker 1xBet, per 1X2, O/U 0.5..4.5 e
BTTS. La tabella e' servita via `admin-ajax.php?action=get_wdtable` (plugin
wpDataTables), esplicitamente permesso da footiqo.com/robots.txt
(`Allow: /wp-admin/admin-ajax.php`). Throttle >= 1.8s tra richieste.

Uso:
    python3 _fetch_footiqo.py                 # 5 leghe x 2017/2018,2018/2019,2019/2020
Output: cantiere/data/ricerca/footiqo_<lega>_<stagione>.json (grezzo, una riga
per partita) + footiqo_manifest.json con URL, timestamp, sha256, conteggi.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")
THROTTLE = 1.8

# colonne della tabella "Odds" (ricavate dal JSON di configurazione della pagina)
COLS = ['id', 'matchDate', 'Country', 'League', 'Season', 'homeTeam', 'awayTeam',
        'xbetClose1FT', 'xbetCloseXFT', 'xbetClose2FT',
        'xbetCloseOver05', 'xbetCloseUnder05',
        'xbetCloseOver15', 'xbetCloseUnder15',
        'xbetCloseOver25', 'xbetCloseUnder25',
        'xbetCloseOver35', 'xbetCloseUnder35',
        'xbetCloseOver45', 'xbetCloseUnder45',
        'xbetCloseBTTSY', 'xbetCloseBTTSN']

LEAGUES = {
    'serie_a': 'italy-serie-a',
    'premier_league': 'england-premier-league',
    'la_liga': 'spain-laliga',
    'bundesliga': 'germany-bundesliga',
    'ligue_1': 'france-ligue-1',
}
SEASONS = ['2017/2018', '2018/2019', '2019/2020']


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read().decode('utf-8', 'replace')


def page_tables(slug: str):
    """Ritorna (html, {table_id: nonce}) e l'id della tabella Odds 'stagioni passate'."""
    html = _get(f'https://footiqo.com/database/leagues/{slug}/')
    nonces = dict(re.findall(
        r'id="wdtNonceFrontendServerSide_(\d+)"\s+name="[^"]+"\s+value="([0-9a-f]+)"', html))
    odds_ids = []
    for tid in nonces:
        i = html.find(f'"tableWpId":{tid}')
        if i > 0 and 'xbetCloseOver25' in html[i:i + 30000]:
            odds_ids.append(int(tid))
    odds_ids.sort()
    # due tabelle Odds: la minore = stagione corrente, la maggiore = stagioni passate
    return nonces, odds_ids


def query(table_id, nonce, season, slug, start=0, length=1000):
    d = [('draw', '1'), ('start', str(start)), ('length', str(length)),
         ('search[value]', ''), ('search[regex]', 'false'), ('wdtNonce', nonce)]
    for i, c in enumerate(COLS):
        d += [(f'columns[{i}][data]', str(i)), (f'columns[{i}][name]', c),
              (f'columns[{i}][searchable]', 'true'), (f'columns[{i}][orderable]', 'true'),
              (f'columns[{i}][search][value]', season if c == 'Season' else ''),
              (f'columns[{i}][search][regex]', 'false')]
    d += [('order[0][column]', '1'), ('order[0][dir]', 'asc')]
    body = urllib.parse.urlencode(d).encode()
    url = (f'https://footiqo.com/wp-admin/admin-ajax.php?action=get_wdtable'
           f'&table_id={table_id}')
    req = urllib.request.Request(url, data=body, headers={
        'User-Agent': UA, 'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': f'https://footiqo.com/database/leagues/{slug}/',
        'Accept': 'application/json, text/javascript, */*; q=0.01'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode('utf-8', 'replace'))


def main():
    manifest = {'fonte': 'footiqo.com', 'endpoint': 'wp-admin/admin-ajax.php?action=get_wdtable',
                'book': '1xBet (colonne xbetClose*)', 'scaricato': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'file': []}
    for lega, slug in LEAGUES.items():
        nonces, odds_ids = page_tables(slug)
        time.sleep(THROTTLE)
        tid = odds_ids[-1]           # tabella "stagioni passate"
        nonce = nonces[str(tid)]
        for season in SEASONS:
            rows, start = [], 0
            while True:
                j = query(tid, nonce, season, slug, start=start, length=1000)
                data = j.get('data') or []
                rows += data
                tot = int(j.get('recordsFiltered', 0))
                start += len(data)
                time.sleep(THROTTLE)
                if not data or start >= tot:
                    break
            recs = [dict(zip(COLS, r)) for r in rows]
            name = f'footiqo_{lega}_{season.replace("/", "-")}.json'
            p = OUT / name
            p.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
            sha = hashlib.sha256(p.read_bytes()).hexdigest()
            manifest['file'].append({'file': name, 'lega': lega, 'stagione': season,
                                     'table_id': tid, 'righe': len(recs), 'sha256': sha})
            print(f'{lega:16s} {season}  righe={len(recs):4d}  -> {name}')
    (OUT / 'footiqo_manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding='utf-8')
    print('manifest scritto')


if __name__ == '__main__':
    main()
