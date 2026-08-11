import sys; sys.path.insert(0,'.')
from tool import *
from patch import FONTI
import re, unicodedata
import src.data.club_matching as cm

def canonico(nome):
    """Come normalizza, ma CONSERVA l'ordine dei token (serve alla guardia:
    'Bilbao Athletic' e 'Athletic Bilbao' NON devono collassare)."""
    s = str(nome).translate(cm._TRADUZIONE)
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r'\b(saint|sankt)\b','st',s)
    s = re.sub(r'[^a-z0-9 ]',' ', s)
    return ' '.join(t for t in s.split() if t and t not in cm._STOPWORD and not t.isdigit())

BLOCCO = {canonico(x) for x in cm.NON_AGGANCIARE}
def bloccato(n): return canonico(n) in BLOCCO
