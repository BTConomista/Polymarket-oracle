#!/usr/bin/env python3
"""Scarica da footiqo.com la tabella "Scores" (gol) delle stesse stagioni.

Serve al controllo di integrita' richiesto dal protocollo: i gol della FONTE
devono coincidere con i gol dello snapshot su ogni riga. La tabella "Odds" non
espone i gol, ma condivide la chiave `id` con la tabella "Scores".

Stesse regole del fetch quote: endpoint admin-ajax (permesso da robots.txt),
throttle >= 1.8s.
"""
from __future__ import annotations

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
COLS = ['id', 'matchDate', 'Country', 'League', 'Season', 'homeTeam', 'awayTeam',
        'ftHomeTeamGoals', 'ftAwayTeamGoals', 'ftResult',
        'htHomeTeamGoals', 'htAwayTeamGoals', 'htResult',
        'stHomeTeamGoals', 'stAwayTeamGoals', 'stResult']
LEAGUES = {'serie_a': 'italy-serie-a', 'premier_league': 'england-premier-league',
           'la_liga': 'spain-laliga', 'bundesliga': 'germany-bundesliga',
           'ligue_1': 'france-ligue-1'}
SEASONS = ['2017/2018', '2018/2019']


def _get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read().decode('utf-8', 'replace')


def find_scores_table(slug):
    html = _get(f'https://footiqo.com/database/leagues/{slug}/')
    nonces = dict(re.findall(
        r'id="wdtNonceFrontendServerSide_(\d+)"\s+name="[^"]+"\s+value="([0-9a-f]+)"', html))
    ids = []
    for tid in nonces:
        i = html.find(f'"tableWpId":{tid}')
        if i > 0 and 'htHomeTeamGoals' in html[i:i + 30000]:
            ids.append(int(tid))
    ids.sort()
    return ids[-1], nonces[str(ids[-1])]   # tabella "stagioni passate"


def query(table_id, nonce, season, slug, start=0, length=1000):
    d = [('draw', '1'), ('start', str(start)), ('length', str(length)),
         ('search[value]', ''), ('search[regex]', 'false'), ('wdtNonce', nonce)]
    for i, c in enumerate(COLS):
        d += [(f'columns[{i}][data]', str(i)), (f'columns[{i}][name]', c),
              (f'columns[{i}][searchable]', 'true'), (f'columns[{i}][orderable]', 'true'),
              (f'columns[{i}][search][value]', season if c == 'Season' else ''),
              (f'columns[{i}][search][regex]', 'false')]
    d += [('order[0][column]', '1'), ('order[0][dir]', 'asc')]
    url = (f'https://footiqo.com/wp-admin/admin-ajax.php?action=get_wdtable'
           f'&table_id={table_id}')
    req = urllib.request.Request(url, data=urllib.parse.urlencode(d).encode(), headers={
        'User-Agent': UA, 'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': f'https://footiqo.com/database/leagues/{slug}/',
        'Accept': 'application/json, text/javascript, */*; q=0.01'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode('utf-8', 'replace'))


def main():
    for lega, slug in LEAGUES.items():
        tid, nonce = find_scores_table(slug)
        time.sleep(THROTTLE)
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
            name = f'footiqo_gol_{lega}_{season.replace("/", "-")}.json'
            (OUT / name).write_text(json.dumps(recs, ensure_ascii=False, indent=1),
                                    encoding='utf-8')
            print(f'{lega:16s} {season}  righe={len(recs):4d}  -> {name}')


if __name__ == '__main__':
    main()
