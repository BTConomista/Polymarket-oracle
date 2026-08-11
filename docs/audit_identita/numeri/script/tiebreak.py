import sys; sys.path.insert(0,'.')
from tool import *
import re, unicodedata, json, pandas as pd
from src.data.club_matching import _TRADUZIONE

def crudo(nome):
    """Nome 'piatto' che CONSERVA sigle e cifre: serve solo come spareggio."""
    s = str(nome).translate(_TRADUZIONE)
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r'[^a-z0-9]+',' ', s)
    return ' '.join(sorted(s.split()))   # ordine dei token irrilevante

CRUDO = {int(c): crudo(n) for c,n in zip(CN.club_id, CN.name)}

def candidati_tb(nome):
    c = A.candidati(nome)
    if len(c) <= 1: return c
    q = crudo(nome)
    ex = [i for i in c if CRUDO.get(i)==q]
    return ex if len(ex)==1 else c
