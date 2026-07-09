"""
05_cco_experiment.py — Controlled synthetic transport networks.
Minimizes total edge length (Steiner-like) under varying source-sink geometry.
"""
import numpy as np, networkx as nx, pickle, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_DIR = r"C:\Users\User\Claude\Projects\Retinnal_Fractal_Analysis"
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "cco")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def gen_tree(source, terminals, n_trials=5, seed=42):
    """Grow a tree by sequentially attaching terminals at minimal added length."""
    rng = np.random.RandomState(seed)
    G = nx.Graph()
    src = 0
    G.add_node(src, pos=source)
    pos = {src: source}
    nid = 1
    for tpos in terminals:
        tn = nid; nid += 1
        G.add_node(tn, pos=tpos)
        pos[tn] = tpos
        best = float('inf')
        best_attach = None
        # Try attaching to every existing node
        for n in list(G.nodes()):
            if n == tn: continue
            d = np.linalg.norm(np.array(pos[n]) - np.array(tpos))
            # Also try inserting along edges (Steiner points)
            # For simplicity, just connect to nearest node
            if d < best:
                best = d
                best_attach = n
        if best_attach is not None:
            G.add_edge(tn, best_attach, length=best)
    return G, src

def features(G):
    if G.number_of_nodes() == 0: return {}
    n, e = G.number_of_nodes(), G.number_of_edges()
    c = len(list(nx.connected_components(G))) if not nx.is_empty(G) else n
    try: ass = nx.degree_assortativity_coefficient(G)
    except: ass = 0
    degs = [d for _, d in G.degree()]
    dc = {}
    for d in degs: dc[d] = dc.get(d, 0) + 1
    tot = sum(dc.values()) or 1
    return {'n_nodes': n, 'n_edges': e,
            'cyclo_norm': (e - n + c) / max(e, 1),
            'assortativity': ass,
            'p_deg3': dc.get(3, 0)/max(tot, 1),
            'avg_degree': np.mean(degs) if degs else 0}

def run():
    import pandas as pd
    rng = np.random.RandomState(42)
    N = 60; R = 30; D = 100
    results = []
    for rep in range(30):
        se = rep
        # CENTRIFUGAL
        s = (D/2, D/2)
        ts = [(D/2 + 40*np.cos(a), D/2 + 40*np.sin(a)) for a in np.linspace(0, 2*np.pi, N+1)[:N]]
        G, _ = gen_tree(s, ts, seed=se)
        f = features(G); f['condition']='centrifugal'; f['rep']=rep; results.append(f)
        # CENTRIPETAL
        s = (5, D/2)
        ts = [(rng.uniform(30, 95), rng.uniform(5, 95)) for _ in range(N)]
        G, _ = gen_tree(s, ts, seed=se+100)
        f = features(G); f['condition']='centripetal'; f['rep']=rep; results.append(f)
        # UNIFORM
        s = (rng.uniform(20,80), rng.uniform(20,80))
        ts = [(rng.uniform(5,95), rng.uniform(5,95)) for _ in range(N)]
        G, _ = gen_tree(s, ts, seed=se+200)
        f = features(G); f['condition']='uniform'; f['rep']=rep; results.append(f)
    df = pd.DataFrame(results)
    df.to_csv(os.path.join(OUTPUT_DIR, "cco_experiment.csv"), index=False)
    for cond in ['centrifugal','centripetal','uniform']:
        sub = df[df['condition']==cond]
        print(f"{cond:15s} assort={sub['assortativity'].mean():.4f}±{sub['assortativity'].std():.4f}  "
              f"p_deg3={sub['p_deg3'].mean():.4f}  nodes={sub['n_nodes'].mean():.0f}")
    c1 = df[df['condition']=='centrifugal']['assortativity']
    c2 = df[df['condition']=='centripetal']['assortativity']
    d = c1.mean() - c2.mean()
    print(f"\nPREDICTION: centrifugal({c1.mean():.3f}) > centripetal({c2.mean():.3f})? diff={d:.3f} {'YES ✓' if d>0 else 'NO ✗'}")

if __name__ == '__main__':
    run()
