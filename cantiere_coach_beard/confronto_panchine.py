"""Confronto panchine: Serie A 2025-26 (nostro dato) vs Guida Asta 2026-27.
Ri-eseguibile: python3 confronto_panchine.py  (dalla radice del repo)"""
import sys, unicodedata; sys.path.insert(0, '.')
import pandas as pd
from src.data import allenatori as al

GUIDA = 'cantiere_coach_beard/coach-beard-starter/Dati/Dati Su Giocatori, Allenatori e Squadre/Guida_Asta_202627.xlsx'

# I nomi club di games.csv (player-scores) NON sono quelli dello snapshot ne' della guida:
# la mappa e' scritta a mano e verificata a occhio, non stimata per somiglianza (CLAUDE.md).
ALIAS = {
    'AC Milan': 'Milan', 'ACF Fiorentina': 'Fiorentina', 'Associazione Sportiva Roma': 'Roma',
    'Atalanta BC': 'Atalanta', 'Bologna Football Club 1909': 'Bologna', 'Cagliari Calcio': 'Cagliari',
    'Como 1907': 'Como', 'Genoa CFC': 'Genoa', 'Hellas Verona': 'Verona', 'Inter Milan': 'Inter',
    'Juventus FC': 'Juventus', 'Parma Calcio 1913': 'Parma', 'Pisa Sporting Club': 'Pisa',
    'SSC Napoli': 'Napoli', 'Società Sportiva Lazio S.p.A.': 'Lazio', 'Torino FC': 'Torino',
    'US Cremonese': 'Cremonese', 'US Lecce': 'Lecce', 'US Sassuolo': 'Sassuolo', 'Udinese Calcio': 'Udinese',
}

def cognome(nome):
    """'M. Sarri' e 'Maurizio Sarri' -> 'sarri'. Confronto sul COGNOME: l'iniziale
    puntata della guida rende impossibile il confronto sul nome completo."""
    s = unicodedata.normalize('NFKD', str(nome)).encode('ascii', 'ignore').decode().lower()
    return s.replace('.', ' ').split()[-1] if s.strip() else ''

p = al.load_partite()
sa = p[(p['competition_id'] == 'IT1') & (p['season'] == 2025)].copy()
sa['squadra'] = sa['club_name'].map(ALIAS)
assert sa['squadra'].notna().all(), 'alias mancante: ' + str(set(sa.loc[sa['squadra'].isna(), 'club_name']))

# titolare = chi ha fatto piu' panchine nella stagione
nostro = (sa.groupby(['squadra', 'allenatore']).size().reset_index(name='n')
            .sort_values('n', ascending=False).groupby('squadra').first())

g = pd.read_excel(GUIDA, sheet_name='Squadre', header=2).dropna(subset=['Squadra'])
g = g.set_index('Squadra')

righe, uguali = [], 0
for sq in sorted(set(nostro.index) | set(g.index)):
    a25 = nostro.loc[sq, 'allenatore'] if sq in nostro.index else '—  (non in Serie A 25-26)'
    n25 = f" ({nostro.loc[sq,'n']}/38)" if sq in nostro.index else ''
    a26 = g.loc[sq, 'Allenatore'] if sq in g.index else '—  (retrocessa)'
    stessa = sq in nostro.index and sq in g.index and cognome(a25) == cognome(a26)
    uguali += stessa
    righe.append((sq, f'{a25}{n25}', a26, 'stesso' if stessa else ('cambio' if sq in nostro.index and sq in g.index else '')))

print(f"{'SQUADRA':12s} {'ALLENATORE 2025-26 (nostro dato)':38s} {'ALLENATORE 2026-27 (guida)':22s} ESITO")
for r in righe:
    print(f'{r[0]:12s} {r[1]:38s} {r[2]:22s} {r[3]}')
comuni = set(nostro.index) & set(g.index)
print(f'\nSquadre in comune: {len(comuni)}/20 | panchina confermata: {uguali} | cambiata: {len(comuni)-uguali}')
