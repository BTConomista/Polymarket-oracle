"""Passo 0.3 del playbook: riconciliazione dei nomi squadra per le leghe nuove.

Il bug classico (CLAUDE.md §5, PLAYBOOK passo 0.3): la stessa squadra scritta in
due modi diversi da due fonti diventa due squadre diverse, in silenzio. Qui si
estraggono TUTTI i nomi distinti da OGNI fonte e si confrontano **per identita'**,
mai per ordinamento.

Fonti confrontate, per Bundesliga e Ligue 1:
  1. football-data.co.uk  (nomi CANONICI del progetto, per costruzione)
  2. Understat            (xG)
  3. openfootball         (calendari: campionato, seconda serie, coppa naz.)
  4. player-scores        (valori rosa, tabella clubs)

Uscita: la lista degli alias da aggiungere, e le squadre non agganciate.
Uso: python cantiere/scripts/riconcilia_nomi.py
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.data import sources  # noqa: E402

FONTI = ROOT / "cantiere" / "data" / "fonti"
OUT = ROOT / "cantiere" / "out"
SEASONS = sources.SEASONS

NUOVE = {
    "bundesliga": {"fd_code": "D1", "understat": "Bundesliga"},
    "ligue_1": {"fd_code": "F1", "understat": "Ligue_1"},
}

# openfootball: percorsi VERIFICATI (probe 2026-07-24).
#   Germania -> repo `deutschland`, cartella per stagione;
#   Francia  -> repo `france` (in realta' il mono-repo "Europe"), file
#               france/{stagione}_fr{1,2}.txt  (schema DIVERSO: la stagione e'
#               nel NOME del file, non in una cartella) -> serve un builder
#               di URL dedicato, non basta la costante di sources.py.
OF_URLS = {
    "bundesliga": {
        "top": "https://raw.githubusercontent.com/openfootball/deutschland/master/{lbl}/1-bundesliga.txt",
        "second": "https://raw.githubusercontent.com/openfootball/deutschland/master/{lbl}/2-bundesliga2.txt",
        "cup": "https://raw.githubusercontent.com/openfootball/deutschland/master/{lbl}/cup.txt",
    },
    "ligue_1": {
        "top": "https://raw.githubusercontent.com/openfootball/france/master/france/{lbl}_fr1.txt",
        "second": "https://raw.githubusercontent.com/openfootball/france/master/france/{lbl}_fr2.txt",
        "cup": "https://raw.githubusercontent.com/openfootball/france/master/france/{lbl}_frcup.txt",
    },
}
# player-scores: id competizione del dataset per le due leghe nuove.
PS_COMPETITIONS = {"bundesliga": "L1", "ligue_1": "FR1"}


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def key(s: str) -> str:
    """Chiave di confronto 'morbida' usata SOLO per proporre accostamenti;
    la decisione finale resta per identita' (occhio umano sulla lista)."""
    s = strip_accents(str(s)).lower()
    s = re.sub(r"\b(fc|sc|ac|as|sv|vfl|vfb|tsg|tsv|bv|rb|sg|ss|us|ud|cd|rc|rcd|"
               r"ogc|osc|estac|fco|stade|club|calcio|1846|1848|1899|1900|1904|"
               r"1907|1909|1913|05|04|09|96|1846)\b", " ", s)
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


def fd_names(league: str) -> set[str]:
    names = set()
    for s in SEASONS:
        raw = pd.read_csv(FONTI / "football_data" / f"{league}_{s}.csv",
                          encoding="latin-1")
        raw = raw.dropna(subset=["HomeTeam", "AwayTeam"])
        names |= set(raw.HomeTeam.astype(str).str.strip())
        names |= set(raw.AwayTeam.astype(str).str.strip())
    return names


def ud_names(league: str) -> set[str]:
    names = set()
    for s in SEASONS:
        year = 2000 + int(s[:2])
        data = json.loads((FONTI / "understat" / f"{league}_{year}.json").read_text())
        for m in data["dates"]:
            names.add(str(m["h"]["title"]).strip())
            names.add(str(m["a"]["title"]).strip())
    return names


def of_names(league: str) -> dict[str, set[str]]:
    """Nomi squadra nei file openfootball (campionato/seconda serie/coppa)."""
    out: dict[str, set[str]] = {}
    line_re = re.compile(r"^\s*(?:\d{1,2}[:.]\d{2}\s+)?(.+?)\s{2,}"
                         r"(?:\d{1,2}-\d{1,2}|v)\s")
    for kind, tmpl in OF_URLS[league].items():
        got: set[str] = set()
        for s in ["1617"] + SEASONS:
            lbl = sources.openfootball_season_label(s)
            url = tmpl.format(lbl=lbl)
            cache = FONTI / "openfootball" / f"{league}_{kind}_{s}.txt"
            cache.parent.mkdir(parents=True, exist_ok=True)
            if not cache.exists():
                try:
                    with urllib.request.urlopen(url, timeout=60) as r:
                        cache.write_bytes(r.read())
                except Exception:
                    cache.write_text("")     # 404 = lacuna dichiarata
            text = cache.read_text(encoding="utf-8", errors="replace")
            for line in text.splitlines():
                m = line_re.match(line.rstrip())
                if m:
                    got.add(m.group(1).strip())
                    tail = re.split(r"\s{2,}", line.rstrip())
                    if tail:
                        cand = tail[-1].strip()
                        if cand and not re.match(r"^[\d\s\-()apen.dcr]+$", cand):
                            got.add(cand)
        out[kind] = {g for g in got if g and len(g) > 2}
    return out


def ps_names(league: str) -> set[str]:
    clubs = pd.read_csv(ROOT / "files" / "player_scores" / "clubs.csv.gz",
                        usecols=["name", "domestic_competition_id"])
    return set(clubs.loc[clubs.domestic_competition_id == PS_COMPETITIONS[league],
                         "name"].astype(str))


def propose(canon: set[str], other: set[str], label: str) -> tuple[dict, list]:
    """Per ogni nome 'other' non gia' canonico, propone il canonico con la
    stessa chiave morbida. Ritorna (alias proposti, nomi non agganciati)."""
    by_key: dict[str, list[str]] = {}
    for c in canon:
        by_key.setdefault(key(c), []).append(c)
    alias, orphans = {}, []
    for name in sorted(other):
        if name in canon:
            continue
        cands = by_key.get(key(name), [])
        if len(cands) == 1:
            alias[name] = cands[0]
        else:
            orphans.append({"nome": name, "candidati": cands, "fonte": label})
    return alias, orphans


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    for league in NUOVE:
        print(f"\n=== {league} ===")
        canon = fd_names(league)
        print(f"  football-data (canonici): {len(canon)} squadre distinte")
        srcs = {"understat": ud_names(league), "player_scores": ps_names(league)}
        for kind, names in of_names(league).items():
            srcs[f"openfootball_{kind}"] = names
        all_alias, all_orph = {}, []
        for label, names in srcs.items():
            alias, orph = propose(canon, names, label)
            # openfootball/player-scores contengono anche club di ALTRE leghe o
            # serie inferiori: le orfane li' sono attese, non un errore.
            expected_orphans = label != "understat"
            print(f"  {label:24s} {len(names):4d} nomi -> {len(alias):3d} alias, "
                  f"{len(orph):3d} non agganciati"
                  f"{' (attesi: altre serie/club)' if expected_orphans else ''}")
            for k, v in alias.items():
                if k in all_alias and all_alias[k] != v:
                    print(f"    !! CONFLITTO alias {k}: {all_alias[k]} vs {v}")
                all_alias[k] = v
            all_orph += orph
        print(f"\n  --- alias proposti ({len(all_alias)}) ---")
        for k, v in sorted(all_alias.items()):
            print(f'    "{k}": "{v}",')
        ud_orph = [o for o in all_orph if o["fonte"] == "understat"]
        if ud_orph:
            print(f"\n  !! Understat NON agganciati ({len(ud_orph)}) — vanno risolti a mano:")
            for o in ud_orph:
                print(f"     {o}")
        report[league] = {"canonici": sorted(canon), "alias": all_alias,
                          "orfani": all_orph,
                          "orfani_understat": ud_orph}
    (OUT / "riconciliazione_nomi.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n-> {(OUT / 'riconciliazione_nomi.json').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
