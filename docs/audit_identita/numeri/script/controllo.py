import sys; sys.path.insert(0,'.')
from prova import *
from guadagno import ALIAS_NUOVI
import pandas as pd
_o = A.aggancia
A.aggancia = lambda n: ALIAS_NUOVI.get(n, _o(n))   # 2° passata: piu' avversari noti
nomi = sorted(set(PART.Squadra)|set(PART.Avversario))
righe=[]
for n in nomi:
    v,u,t = deduci(n)
    dichiarato = _o(n)
    proposto   = ALIAS_NUOVI.get(n, dichiarato)
    voto = v.most_common(1)[0] if v else (None,0)
    concorde = (voto[0]==proposto) if proposto and voto[0] else None
    righe.append(dict(nome=n, agganciato=dichiarato, proposto=proposto,
                      fixture_top=voto[0], voti=voto[1], usate=u, tot=t,
                      alternativi=len(v)-1 if v else 0, concorde=concorde))
D = pd.DataFrame(righe)
