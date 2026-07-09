"""
06_phase_b_figures.py — Phase B figure generation.

Reads from data/features.csv, generates all publication-quality figures.
Run after 02_compute_features.py.

Usage:
    python pipeline/06_phase_b_figures.py

Output:
    results/figures/fig1_boxplots.png
    results/figures/fig2_pca.png
    results/figures/fig3_corr_matrix.png
    results/figures/fig4_size_correlation.png
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import sys
import warnings
warnings.filterwarnings('ignore')

BASE_DIR = r"C:\Users\User\Claude\Projects\Retinnal_Fractal_Analysis"
FIGURES_DIR = os.path.join(BASE_DIR, "results", "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

COLORS = {'retinal': '#E74C3C', 'leaf': '#27AE60', 'crack': '#2C3E50', 'dla': '#8E44AD'}
LABELS = {'retinal': 'Retina', 'leaf': 'Leaf', 'crack': 'Concrete', 'dla': 'DLA'}
SYSTEMS = ['retinal', 'leaf', 'crack', 'dla']

plt.rcParams.update({'figure.dpi': 150, 'savefig.dpi': 300, 'font.size': 9})

df = pd.read_csv(os.path.join(BASE_DIR, "data", "features.csv"))
print(f"Loaded {len(df)} samples")

# ── FIG 1: Box plots ──────────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(10, 8))
axes = axes.flatten()

descriptors = [
    ('p_deg3', 'Proportion of degree-3 (bifurcations)'),
    ('p_deg4', 'Proportion of degree-4 (crossings)'),
    ('assortativity', 'Assortativity'),
    ('cyclomatic_normalized', 'Cyclomatic ratio'),
]

for idx, (desc, title) in enumerate(descriptors):
    ax = axes[idx]
    for i, sys_name in enumerate(SYSTEMS):
        vals = df[df['label'] == sys_name][desc].dropna()
        if len(vals) == 0:
            continue
        ax.boxplot(vals, positions=[i], widths=0.5, patch_artist=True,
                   boxprops=dict(facecolor=COLORS[sys_name], alpha=0.6),
                   medianprops=dict(color='black', linewidth=1.5),
                   whiskerprops=dict(color=COLORS[sys_name]),
                   capprops=dict(color=COLORS[sys_name]))
        np.random.seed(42)
        ax.scatter(np.random.normal(i, 0.05, size=len(vals)),
                   vals, alpha=0.2, s=4, color=COLORS[sys_name])
    ax.set_xticks(range(4))
    ax.set_xticklabels([LABELS[s] for s in SYSTEMS], fontsize=8)
    ax.set_title(title, fontsize=8)
    ax.grid(alpha=0.2, axis='y')
    if desc == 'assortativity':
        ax.axhline(y=0, color='gray', linestyle='--', linewidth=0.5)

plt.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, 'fig1_boxplots.png'), dpi=300)
plt.close(fig)
print("Fig 1: boxplots")

# ── FIG 2: PCA ────────────────────────────────────────────────────
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

norm_feats = ['cyclomatic_normalized', 'junction_ratio', 'avg_degree',
              'degree_entropy', 'p_deg3', 'p_deg4', 'assortativity',
              'avg_clustering']
available = [f for f in norm_feats if f in df.columns]
mask = df[available].notna().all(axis=1)
X = StandardScaler().fit_transform(df.loc[mask, available].values)
labels = df.loc[mask, 'label'].values
pca = PCA(n_components=2).fit_transform(X)
var = PCA(n_components=2).fit(X).explained_variance_ratio_

fig, ax = plt.subplots(figsize=(8, 6))
for sys_name in SYSTEMS:
    sys_mask = labels == sys_name
    ax.scatter(pca[sys_mask, 0], pca[sys_mask, 1],
               c=COLORS[sys_name], marker='o', label=LABELS[sys_name],
               s=25, alpha=0.5, edgecolors='w', linewidth=0.3)
ax.set_xlabel(f'PC1 ({var[0]:.1%})')
ax.set_ylabel(f'PC2 ({var[1]:.1%})')
ax.legend(fontsize=9)
ax.grid(alpha=0.2)
ax.set_title('PCA of topological feature space')
plt.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, 'fig2_pca.png'), dpi=300)
plt.close(fig)
print("Fig 2: PCA")

# ── FIG 3: Correlation matrix ──────────────────────────────────────
feats_for_corr = ['cyclomatic_normalized', 'junction_ratio', 'avg_degree',
                  'p_deg3', 'p_deg4', 'assortativity', 'avg_clustering',
                  'graph_density', 'mean_euclidean_ratio', 'largest_component_ratio']
available2 = [f for f in feats_for_corr if f in df.columns]
corr = df[available2].corr()

fig, ax = plt.subplots(figsize=(8, 7))
im = ax.imshow(corr, cmap='RdBu_r', vmin=-1, vmax=1)
ax.set_xticks(range(len(available2)))
ax.set_yticks(range(len(available2)))
ax.set_xticklabels([c.replace('_', '\n') for c in available2], fontsize=6, rotation=45, ha='right')
ax.set_yticklabels(available2, fontsize=7)
for i in range(len(available2)):
    for j in range(len(available2)):
        ax.text(j, i, f'{corr.iloc[i, j]:.2f}', ha='center', va='center',
                fontsize=5, color='white' if abs(corr.iloc[i, j]) > 0.5 else 'black')
fig.colorbar(im, ax=ax, shrink=0.8)
ax.set_title('Topological descriptor correlations')
plt.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, 'fig3_corr_matrix.png'), dpi=300)
plt.close(fig)
print("Fig 3: correlation matrix")

# ── FIG 4: Size correlation ────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(10, 8))
axes = axes.flatten()

for idx, feat in enumerate(['cyclomatic_normalized', 'assortativity', 'p_deg3', 'p_deg4']):
    ax = axes[idx]
    for sys_name in SYSTEMS:
        sub = df[df['label'] == sys_name]
        ax.scatter(sub['n_nodes'], sub[feat], c=COLORS[sys_name],
                   label=LABELS[sys_name], s=10, alpha=0.5)
    ax.set_xlabel('Number of nodes')
    ax.set_ylabel(feat.replace('_', ' '))
    ax.set_xscale('log')
    ax.grid(alpha=0.2)
    ax.legend(fontsize=7)

plt.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, 'fig4_size_correlation.png'), dpi=300)
plt.close(fig)
print("Fig 4: size correlations")

print(f"\nAll figures in: {FIGURES_DIR}")
