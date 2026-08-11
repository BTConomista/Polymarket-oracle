import sys, pickle, importlib
sys.path.insert(0, "/home/user/Polymarket-oracle")
sys.path.insert(0, "/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad")
import pandas as pd
import src.data.club_matching as CM
importlib.reload(CM)
from V3_patch import normalizza_patched          # riparazione PROPOSTA
from VA_corretta import normalizza2, _deconfondi2  # riparazione CORRETTA

S = "/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/"
cn = pd.read_csv("/home/user/Polymarket-oracle/files/player_scores/club_names.csv.gz")

reali = ['FС Taganrog (-2015)', 'FС Vologda (-2014)', 'Cherkashchyna Сherkasy',
         'Οlympiacos Ζacharo', 'BRW-ВІК Volodymyr-Volynskyi',
         'Сокол Обручище', 'Футбольный клуб "Локомотив" Москва']
print("=== i 5 casi reali + i 2 non-latini ===")
for n in reali:
    print(f"  {n!r}\n     base     {sorted(CM.normalizza(n))}\n"
          f"     proposta {sorted(normalizza_patched(n))}\n"
          f"     corretta {sorted(normalizza2(n))}")

sint = ["ΠΑΟΚ FC", "ΠΑΣ Giannina", "ΑΕΚ Athens", "Динамо Kyiv", "Спартак Moscow",
        "Ολυμπιακός Piraeus FC", "Шахтар Donetsk", "ПАОК FC"]
A0 = CM.Agganciatore(cn)
base = {n: tuple(A0.candidati(n)) for n in sint}
CM.normalizza = normalizza_patched; Ap = CM.Agganciatore(cn)
prop = {n: tuple(Ap.candidati(n)) for n in sint}
CM.normalizza = normalizza2; Ac = CM.Agganciatore(cn)
corr = {n: tuple(Ac.candidati(n)) for n in sint}
def nome(i): return str(cn.loc[cn.club_id == i, "name"].iloc[0])
print("\n=== nomi misti SINTETICI (cirillico/greco VERO) ===")
for n in sint:
    print(f"  {n!r:26s} base={base[n]}{[nome(i) for i in base[n][:2]]}  "
          f"proposta={prop[n]}{[nome(i) for i in prop[n][:2]]}  "
          f"corretta={corr[n]}{[nome(i) for i in corr[n][:2]]}")

# diff completo sulle 74.637 stringhe reali
nomi = sorted(pickle.load(open(S + "NOMI.pkl", "rb")))
importlib.reload(CM); A0 = CM.Agganciatore(cn)
b = {n: tuple(A0.candidati(n)) for n in nomi}
CM.normalizza = normalizza2; Ac = CM.Agganciatore(cn)
c = {n: tuple(Ac.candidati(n)) for n in nomi}
cambi = [(n, b[n], c[n]) for n in nomi if b[n] != c[n]]
print(f"\n=== diff CORRETTA su {len(nomi)} nomi reali: {len(cambi)} cambiati")
for n, x, y in cambi: print(f"   {n!r}: {x} -> {y}")

from collections import defaultdict
def coll(fn):
    m = defaultdict(list)
    for cid, nm in zip(cn.club_id, cn.name):
        t = fn(nm)
        if t: m[t].append(int(cid))
    return {k: v for k, v in m.items() if len(v) > 1}
importlib.reload(CM)
print("collisioni registro base:", len(coll(CM.normalizza)),
      " corretta:", len(coll(normalizza2)))
