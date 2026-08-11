import sys
sys.path.insert(0,"/home/user/Polymarket-oracle")
sys.path.insert(0,"/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad")
import pandas as pd, importlib
import src.data.club_matching as CM
from V3_patch import normalizza_patched
R="/home/user/Polymarket-oracle/"
cn = pd.read_csv(R+"files/player_scores/club_names.csv.gz")

casi = ['FС Taganrog (-2015)','FС Vologda (-2014)','Cherkashchyna Сherkasy',
        'Οlympiacos Ζacharo','BRW-ВІК Volodymyr-Volynskyi',
        'Футбольный клуб "Локомотив" Москва','Сокол Обручище',
        'Juventus Next Gen [ α ]']
print("=== token PRIMA / DOPO ===")
for n in casi:
    print(f"  {n!r}\n     prima {sorted(CM.normalizza(n))}\n     dopo  {sorted(normalizza_patched(n))}")

# --- collisioni nel registro (due club_id con lo STESSO insieme di token)
from collections import defaultdict
def collisioni(fn):
    m=defaultdict(list)
    for cid,nome in zip(cn.club_id,cn.name):
        ts=fn(nome)
        if ts: m[ts].append(int(cid))
    return {k:v for k,v in m.items() if len(v)>1}
c0=collisioni(CM.normalizza); c1=collisioni(normalizza_patched)
print(f"\n=== collisioni registro: prima {len(c0)}  dopo {len(c1)}")
nuove=set(c1)-set(c0); perse=set(c0)-set(c1)
print("  nuove:",[(sorted(k),c1[k]) for k in nuove])
print("  sparite:",[(sorted(k),c0[k]) for k in perse])

# --- indice: token totali
def idx(fn):
    from collections import defaultdict
    inv=defaultdict(set); per={}
    for cid,nome in zip(cn.club_id,cn.name):
        ts=fn(nome)
        if not ts: continue
        per[int(cid)]=ts
        for t in ts: inv[t].add(int(cid))
    return per,inv
p0,i0=idx(CM.normalizza); p1,i1=idx(normalizza_patched)
print(f"\ntoken distinti indice: prima {len(i0)} dopo {len(i1)}")
print(" token spariti:",sorted(set(i0)-set(i1)))
print(" token nuovi  :",sorted(set(i1)-set(i0)))
