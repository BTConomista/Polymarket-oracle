"""Scansione ESAUSTIVA: ogni stringa di ogni CSV/JSON di data/ e files/ il cui
   canonico cade nella blocklist. Sono esattamente i nomi il cui esito cambia."""
import sys, os, glob, json, re, unicodedata, collections
sys.path.insert(0,'/home/user/Polymarket-oracle')
import pandas as pd
import src.data.club_matching as cm

def canonico(nome):
    s=str(nome).translate(cm._TRADUZIONE)
    s=unicodedata.normalize('NFKD',s)
    s=''.join(c for c in s if not unicodedata.combining(c)).lower()
    s=re.sub(r'\b(saint|sankt)\b','st',s)
    s=re.sub(r'[^a-z0-9 ]',' ',s)
    return ' '.join(t for t in s.split() if t and t not in cm._STOPWORD and not t.isdigit())
BLOCCO={canonico(x) for x in cm.NON_AGGANCIARE}

trovati=collections.defaultdict(set)
files=[]
for base in ('data','files'):
    for ext in ('*.csv','*.csv.gz','*.json','*.json.gz'):
        files += glob.glob(f'/home/user/Polymarket-oracle/{base}/**/{ext}', recursive=True)
print('file scansionati:', len(files))
for f in files:
    if os.path.getsize(f) > 60_000_000: continue
    try:
        if f.endswith(('.json','.json.gz')):
            import gzip
            op = gzip.open if f.endswith('.gz') else open
            with op(f,'rt',encoding='utf-8',errors='replace') as fh: obj=json.load(fh)
            pila=[obj]; vals=[]
            while pila:
                o=pila.pop()
                if isinstance(o,dict): pila+=list(o.values())+list(o.keys())
                elif isinstance(o,list): pila+=o
                elif isinstance(o,str): vals.append(o)
            for v in set(vals):
                if canonico(v) in BLOCCO: trovati[v].add(os.path.relpath(f,'/home/user/Polymarket-oracle'))
        else:
            d=pd.read_csv(f, low_memory=False)
            for c in d.columns:
                if d[c].dtype!=object: continue
                u=d[c].dropna().unique()
                if len(u)>20000: continue
                for v in u:
                    if isinstance(v,str) and 3<len(v)<60 and canonico(v) in BLOCCO:
                        trovati[v].add(os.path.relpath(f,'/home/user/Polymarket-oracle')+':'+c)
    except Exception as e:
        pass

A=cm.Agganciatore()
print('\nnomi il cui esito CAMBIA con la guardia canonica:')
for n in sorted(trovati):
    c=A.candidati(n)
    print(f'  {n!r:30} candidati ORA {c}   fonti: {sorted(trovati[n])[:4]}')
