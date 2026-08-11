import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad')
from prova import *
import pandas as pd
P = pd.read_excel('/home/user/Polymarket-oracle/files/sofascore_coppe_europee_2526/originale_sofascore.xlsx', sheet_name='Partite')
P['d'] = pd.to_datetime(P['Data'], dayfirst=True)

PROPOSTA = {
 'AC Sparta Praha':197,'AIK':272,'Araz Naxçıvan':44360,'Aris Thessaloniki':605,
 'Beşiktaş JK':114,'ETO FC Győr':6055,'FC Bayern München':27,'FC København':190,
 'FCI Levadia Tallinn':5771,'FK Austria Wien':14,'FK Crvena Zvezda':159,
 'Ferencváros TC':279,"Hapoel Be'er Sheva":2976,'KF Ballkani':28082,
 'KF Shkëndija':1167,'Klaksvíkar Ítróttarfelag':6170,'Nõmme Kalju':22783,
 'Oleksandria':18303,'Olympique Lyonnais':1041,'Royale Union Saint-Gilloise':3948,
 'SK Rapid Wien':170,'SK Slavia Praha':62,'Sporting Braga':1075,'Zirə FK':46710,
 'Ħamrun Spartans FC':17149,
}
def agg(n):
    return PROPOSTA.get(n, A.aggancia(n))

def prova(nome, cid):
    m = P[(P.Casa==nome)|(P.Trasferta==nome)]
    tot=conf=gol_ok=paesi=[]
    conf=0; gol_ok=0; usabili=0; paesi=set()
    for _,r in m.iterrows():
        casa = r.Casa==nome
        avv = r.Trasferta if casa else r.Casa
        avvid = agg(avv)
        if avvid is None: continue
        usabili+=1
        g = G25[(abs((G25.date-r.d).dt.days)<=1)]
        g = g[((g.home_club_id==cid)&(g.away_club_id==avvid)) | ((g.home_club_id==avvid)&(g.away_club_id==cid))]
        if len(g)==0: continue
        conf+=1
        gg=g.iloc[0]
        # lato + punteggio (90'+suppl. escl. rigori: games.csv riporta il finale)
        sc_sofa = (r['Gol casa'], r['Gol trasferta']) if casa else (r['Gol trasferta'], r['Gol casa'])
        sc_ps  = (gg.home_club_goals, gg.away_club_goals) if gg.home_club_id==cid else (gg.away_club_goals, gg.home_club_goals)
        if tuple(sc_sofa)==tuple(sc_ps): gol_ok+=1
        if casa: paesi.add(r['Paese'])
    return dict(partite=len(m), usabili=usabili, data_avv=conf, punteggio=gol_ok, paesi_casa=sorted(paesi))
