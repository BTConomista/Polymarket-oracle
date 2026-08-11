import pandas as pd
g = pd.read_csv("data/coppe_2526/aggancio_giocatori.csv")
p = pd.read_csv("data/coppe_2526/aggancio_partite.csv")
print("aggancio_partite colonne:", list(p.columns), "| righe:", len(p))
col = [c for c in p.columns if "id" in c.lower()]
print(p[col].head(3).to_string())
ids_p = set(p[[c for c in p.columns if c.lower() in ("id_diretta","id partita","id_partita")][0]]) if any(c.lower() in ("id_diretta","id partita","id_partita") for c in p.columns) else None
print("\nid_diretta distinti in aggancio_giocatori:", g["id_diretta"].nunique())
for c in p.columns:
    s=set(p[c].astype(str)); ov=len(s & set(g["id_diretta"].astype(str)))
    if ov: print(f"  colonna '{c}' di aggancio_partite: {ov} valori in comune (su {g['id_diretta'].nunique()})")
# quante righe di formazione per id_diretta? deve essere ~ una partita
print("\nrighe per id_diretta: mediana", g.groupby("id_diretta").size().median(), "min", g.groupby("id_diretta").size().min(), "max", g.groupby("id_diretta").size().max())
print("squadre distinte per id_diretta: distribuzione")
print(g.groupby("id_diretta")["squadra"].nunique().value_counts().to_string())
# e il game_id? un id_diretta -> quanti game_id
print("\ngame_id distinti per id_diretta:", g.groupby("id_diretta")["game_id"].nunique().value_counts().to_string())
F = pd.read_csv("data/coppe_2526/formazioni.csv")
print("\nformazioni.csv colonne:", list(F.columns))
