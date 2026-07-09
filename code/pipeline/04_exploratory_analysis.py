"""
04_exploratory_analysis.py — Phase 1 exploratory analysis (full graphs, no subsampling).
"""
import numpy as np, pandas as pd, pickle, os, sys, glob, warnings
warnings.filterwarnings('ignore')
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
import networkx as nx

BASE_DIR = r"C:\Users\User\Claude\Projects\Retinnal_Fractal_Analysis"
FIGURES_DIR = os.path.join(BASE_DIR, "results", "figures")
TABLES_DIR = os.path.join(BASE_DIR, "results", "tables")
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(TABLES_DIR, exist_ok=True)
COLORS = {'retinal': '#E74C3C', 'crack': '#2C3E50', 'dla': '#27AE60'}
LABELS = {'retinal': 'Retina', 'crack': 'Concrete', 'dla': 'DLA'}

def load_graphs(path, label, min_nodes=10):
    files = sorted(glob.glob(os.path.join(path, "*.gpickle")))
    graphs = []
    for f in files:
        G = pickle.load(open(f, 'rb'))
        if G.number_of_nodes() >= min_nodes:
            graphs.append({'G': G, 'label': label})
    return graphs

def compute_features(G):
    n, e = G.number_of_nodes(), G.number_of_edges()
    if n == 0 or e == 0:
        return {}
    comps = len(list(nx.connected_components(G)))
    cyclo = e - n + comps
    degs = [d for _, d in G.degree()]
    deg_counts = {d: degs.count(d) for d in set(degs)}
    total = sum(deg_counts.values())
    try:
        ass = nx.degree_assortativity_coefficient(G)
    except:
        ass = 0
    try:
        clust = nx.average_clustering(G)
    except:
        clust = 0
    return {
        'n_nodes': n, 'n_edges': e,
        'cyclo_norm': cyclo / max(e, 1),
        'assortativity': ass,
        'clustering': clust,
        'p_deg3': deg_counts.get(3,0)/max(total,1),
        'p_deg4': deg_counts.get(4,0)/max(total,1),
        'avg_degree': np.mean(degs),
        'density': nx.density(G),
    }

print("="*60)
print("PHASE 1 EXPLORATORY (full graphs)")
print("="*60)

# Load
ret = load_graphs(os.path.join(BASE_DIR,"data","retinal","graphs"), 'retinal', 30)
cra = load_graphs(os.path.join(BASE_DIR,"data","crack","graphs"), 'crack', 15)
dla = load_graphs(os.path.join(BASE_DIR,"data","dla","graphs"), 'dla', 20)
print(f"\nRetina: {len(ret)}, Crack: {len(cra)}, DLA: {len(dla)}")

# Compute features on FULL graphs
rows = []
for item in ret + cra + dla:
    f = compute_features(item['G'])
    if f:
        f['label'] = item['label']
        rows.append(f)
df = pd.DataFrame(rows)

# Quick size correlation check
print(f"\n{'='*60}")
print("SIZE CORRELATION CHECK")
print("Are normalized features correlated with graph size?")
for feat in ['cyclo_norm', 'assortativity', 'clustering', 'p_deg3', 'p_deg4', 'avg_degree', 'density']:
    r_corr = df[df['label']=='retinal']['n_nodes'].corr(df[df['label']=='retinal'][feat])
    c_corr = df[df['label']=='crack']['n_nodes'].corr(df[df['label']=='crack'][feat])
    d_corr = df[df['label']=='dla']['n_nodes'].corr(df[df['label']=='dla'][feat]) if len(df[df['label']=='dla']) > 5 else 0
    print(f"  {feat:15s}: retina r={r_corr:.3f}, crack r={c_corr:.3f}, dla r={d_corr:.3f}")

# Feature means by group
print(f"\nFEATURE MEANS BY GROUP")
print("-"*76)
feats = ['cyclo_norm','assortativity','clustering','p_deg3','p_deg4','avg_degree','density']
for feat in feats:
    print(f"\n  {feat}:")
    for label in ['retinal','crack','dla']:
        m = df[df['label']==label][feat].mean()
        s = df[df['label']==label][feat].std()
        print(f"    {label:10s} = {m:.4f} ± {s:.4f}")
    means = {label: df[df['label']==label][feat].mean() for label in ['retinal','crack','dla']}
    order = sorted(['retinal','crack','dla'], key=lambda x: means[x], reverse=True)
    print(f"    Order: {' > '.join(order)}")

# Plot key features
fig, axes = plt.subplots(1, 3, figsize=(13, 4))
for idx, feat in enumerate(['assortativity', 'cyclo_norm', 'p_deg4']):
    ax = axes[idx]
    for j, (label, color) in enumerate(zip(['retinal','crack','dla'],
        [COLORS['retinal'],COLORS['crack'],COLORS['dla']])):
        vals = df[df['label']==label][feat].dropna()
        ax.boxplot(vals, positions=[j], widths=0.5, patch_artist=True,
                   boxprops=dict(facecolor=color, alpha=0.6),
                   medianprops=dict(color='black'))
        ax.scatter(np.random.RandomState(42).normal(j,0.05,size=len(vals)),
                  vals, alpha=0.3, s=6, color=color)
    ax.set_xticks([0,1,2]); ax.set_xticklabels(['Retina','Crack','DLA'])
    ax.set_title(feat); ax.grid(alpha=0.2)
plt.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR,"exploratory_full.png"), dpi=300)
plt.close(fig)
print(f"\nFigure saved to results/figures/exploratory_full.png")

print(f"\n{'='*60}")
print("BOTTOM LINE")
# Check if assortativity separates retina from crack
r_ass = df[df['label']=='retinal']['assortativity'].dropna()
c_ass = df[df['label']=='crack']['assortativity'].dropna()
d_ass = df[df['label']=='dla']['assortativity'].dropna()
print(f"  Retina assortativity: {r_ass.mean():.3f} ± {r_ass.std():.3f}")
print(f"  Crack assortativity:  {c_ass.mean():.3f} ± {c_ass.std():.3f}")
print(f"  DLA assortativity:    {d_ass.mean():.3f} ± {d_ass.std():.3f}")
print(f"  Retina vs Crack overlap: {(abs(r_ass.mean()-c_ass.mean()))/(r_ass.std()+c_ass.std()):.2f} sigma")
