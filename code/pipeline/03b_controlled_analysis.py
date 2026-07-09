"""
03b_controlled_analysis.py — Controlled analysis accounting for network size.

The primary analysis (03_analyze.py) showed suspiciously perfect results because
persistent homology features were dominated by graph size differences (retinal ~1382
nodes vs crack ~23 nodes). This script controls for size to isolate genuine
topological differences.

Approach:
1. Use ONLY size-normalized features (ratios, densities, proportions)
2. For PH: subsample EVERY graph to exactly N points before computing
3. Compare: do normalized features alone separate the groups?
4. Use permutation tests to validate separation significance

Author: PI Claude
Date: 2026-07-09
"""

import numpy as np
import pandas as pd
import os
import sys
import warnings
warnings.filterwarnings('ignore')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

BASE_DIR = r"C:\Users\User\Claude\Projects\Retinnal_Fractal_Analysis"
DATA_DIR = os.path.join(BASE_DIR, "data")
FIGURES_DIR = os.path.join(BASE_DIR, "results", "figures")
TABLES_DIR = os.path.join(BASE_DIR, "results", "tables")
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(TABLES_DIR, exist_ok=True)

plt.rcParams.update({'figure.dpi': 150, 'savefig.dpi': 300})
RETINA_COLOR = '#E74C3C'
CRACK_COLOR = '#2C3E50'


# ──────────────────────────────────────────────────────────────────────
# 1. SIZE-NORMALIZED FEATURES ONLY
# ──────────────────────────────────────────────────────────────────────

def run_normalized_analysis(df):
    """
    Run classification using ONLY size-normalized features.
    No raw node/edge counts, no PH features (which are size-biased).
    """
    from sklearn.model_selection import StratifiedKFold, cross_validate
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.svm import SVC
    from sklearn.feature_selection import SelectKBest, f_classif

    # Size-normalized features only
    norm_features = [
        'cyclomatic_normalized', 'junction_ratio', 'graph_density',
        'avg_degree', 'degree_entropy', 'p_deg2', 'p_deg3', 'p_deg4',
        'assortativity', 'avg_clustering', 'mean_edge_length',
        'mean_euclidean_ratio', 'largest_component_ratio'
    ]

    # Filter to existing features
    available = [f for f in norm_features if f in df.columns]
    print(f"\nSize-normalized features ({len(available)}):")
    for f in available:
        print(f"  {f}")

    # Prepare data
    mask = df[available].notna().all(axis=1)
    X = df.loc[mask, available].values
    y = (df.loc[mask, 'label'] == 'retinal').astype(int).values
    print(f"\n  Samples: {len(X)} (retinal={y.sum()}, crack={(1-y).sum()})")

    # Descriptive statistics
    print(f"\n  Feature means by group:")
    retinal_mask = y == 1
    for i, feat in enumerate(available):
        r_mean = X[retinal_mask, i].mean()
        c_mean = X[~retinal_mask, i].mean()
        delta = abs(r_mean - c_mean) / max(np.std(X[:, i]), 1e-10)
        print(f"    {feat:30s} retinal={r_mean:.4f}  crack={c_mean:.4f}  effect={delta:.2f}")

    # Feature selection: top 5 features by ANOVA
    selector = SelectKBest(f_classif, k=min(5, len(available)))
    selector.fit(X, y)
    top_idx = np.argsort(selector.scores_)[-5:][::-1]
    print(f"\n  Top features by ANOVA:")
    for i in top_idx:
        print(f"    {available[i]}: F={selector.scores_[i]:.1f}")

    # Classification
    classifiers = {
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    print(f"\n  Classification results (5-fold CV):")
    for name, clf in classifiers.items():
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', clf)
        ])
        scores = cross_validate(pipeline, X, y, cv=cv,
                               scoring=['balanced_accuracy', 'roc_auc'])
        print(f"    {name:25s} Acc={scores['test_balanced_accuracy'].mean():.3f}±"
              f"{scores['test_balanced_accuracy'].std():.3f}  "
              f"AUC={scores['test_roc_auc'].mean():.3f}±"
              f"{scores['test_roc_auc'].std():.3f}")

    return available


# ──────────────────────────────────────────────────────────────────────
# 2. CONTROLLED PH: MATCHED SUBSAMPLING
# ──────────────────────────────────────────────────────────────────────

def compute_controlled_ph(graph_dir, label, n_points=100, n_graphs=None):
    """
    Compute PH features with controlled subsampling.
    Every graph is subsampled to exactly n_points for a fair comparison.
    """
    import pickle
    import glob
    import ripser

    files = sorted(glob.glob(os.path.join(graph_dir, "*.gpickle")))
    if n_graphs:
        files = files[:n_graphs]

    results = []
    rng = np.random.RandomState(42)

    for fpath in files:
        try:
            with open(fpath, 'rb') as f:
                G = pickle.load(f)
        except:
            continue

        # Extract node positions
        pos = []
        for n, data in G.nodes(data=True):
            p = data.get('pos', None)
            if p is not None:
                pos.append([float(p[1]), float(p[0])])
        pos = np.array(pos)

        if len(pos) < n_points:
            # Not enough points — skip or use all
            continue

        # Subsample to exactly n_points
        idx = rng.choice(len(pos), n_points, replace=False)
        pos = pos[idx]

        # Compute PH
        try:
            result = ripser.ripser(pos, maxdim=1, coeff=2)
            h1 = result['dgms'][1]
            finite_h1 = h1[np.isfinite(h1[:, 1])]
            lifetimes = finite_h1[:, 1] - finite_h1[:, 0] if len(finite_h1) > 0 else np.array([])

            features = {
                'n_h1': len(finite_h1),
                'max_h1': np.max(lifetimes) if len(lifetimes) > 0 else 0,
                'mean_h1': np.mean(lifetimes) if len(lifetimes) > 0 else 0,
                'sum_h1': np.sum(lifetimes) if len(lifetimes) > 0 else 0,
                'h1_entropy': -np.sum((lifetimes/np.sum(lifetimes)) * np.log(lifetimes/np.sum(lifetimes) + 1e-10)) if len(lifetimes) > 0 else 0,
            }
        except:
            continue

        results.append(features)

    df = pd.DataFrame(results)
    df['label'] = label
    return df


def run_controlled_ph():
    """Compare retinal and crack using matched PH subsampling."""
    print(f"\n{'='*60}")
    print("CONTROLLED PH (matched subsampling)")
    print(f"{'='*60}")

    # Find minimum graph size across both groups
    import pickle, glob
    crack_files = sorted(glob.glob(os.path.join(CRACK_GRAPH_DIR, "*.gpickle")))
    min_nodes_crack = 9999
    for f in crack_files:
        with open(f, 'rb') as fp:
            G = pickle.load(fp)
        n = G.number_of_nodes()
        if n > 10:
            min_nodes_crack = min(min_nodes_crack, n)

    n_sample = min(100, min_nodes_crack)
    print(f"  Using {n_sample} points per graph (minimum found: {min_nodes_crack})")

    if n_sample < 10:
        print("  WARNING: Too few nodes for meaningful PH comparison")
        return None

    # Compute controlled PH
    retinal_ph = compute_controlled_ph(RETINAL_GRAPH_DIR, 'retinal', n_points=n_sample)
    crack_ph = compute_controlled_ph(CRACK_GRAPH_DIR, 'crack', n_points=n_sample)

    if retinal_ph is None or crack_ph is None:
        return None

    combined = pd.concat([retinal_ph, crack_ph], ignore_index=True)
    print(f"  Retinal: {len(retinal_ph)} samples, Crack: {len(crack_ph)} samples")

    # Statistical comparison
    from scipy.stats import mannwhitneyu
    print(f"\n  Comparison (Mann-Whitney U, matched n={n_sample}):")
    for col in ['n_h1', 'max_h1', 'mean_h1', 'sum_h1', 'h1_entropy']:
        r_vals = combined[combined['label']=='retinal'][col]
        c_vals = combined[combined['label']=='crack'][col]
        if len(r_vals) > 0 and len(c_vals) > 0:
            stat, p = mannwhitneyu(r_vals, c_vals)
            print(f"    {col:15s} retinal={r_vals.mean():.2f}±{r_vals.std():.2f}  "
                  f"crack={c_vals.mean():.2f}±{c_vals.std():.2f}  p={p:.4f}")

    # Plot comparison
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for i, col in enumerate(['n_h1', 'mean_h1', 'max_h1']):
        ax = axes[i]
        for j, (label, color) in enumerate(zip(['retinal', 'crack'], [RETINA_COLOR, CRACK_COLOR])):
            vals = combined[combined['label']==label][col].dropna().values
            ax.boxplot(vals, positions=[j], widths=0.5, patch_artist=True,
                       boxprops=dict(facecolor=color, alpha=0.6),
                       medianprops=dict(color='black'))
            np.random.seed(42)
            ax.scatter(np.random.normal(j, 0.05, size=len(vals)), vals,
                      alpha=0.3, s=6, color=color)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(['Retinal', 'Crack'], fontsize=8)
        ax.set_title(col, fontsize=10)
        ax.grid(alpha=0.2)

    plt.tight_layout()
    path = os.path.join(FIGURES_DIR, 'controlled_ph_comparison.png')
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"\n  Saved: {path}")

    return combined


# ──────────────────────────────────────────────────────────────────────
# 3. MAIN
# ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("CONTROLLED ANALYSIS (size-normalized)")
    print("=" * 60)

    # Load features
    csv_path = os.path.join(DATA_DIR, "features.csv")
    df = pd.read_csv(csv_path)

    # Part 1: Normalized features only
    print("\n[1/2] Normalized features analysis...")
    norm_features = run_normalized_analysis(df)

    # Part 2: Controlled PH
    print("\n[2/2] Controlled persistent homology...")
    ph_df = run_controlled_ph()

    # Summary assessment
    print(f"\n{'='*60}")
    print("ASSESSMENT")
    print(f"{'='*60}")
    print("""
    The primary analysis showed 100% classification accuracy, but this was
    driven by graph size differences (retinal ~1382 nodes vs crack ~23 nodes)
    rather than genuine topological differences.

    The controlled analysis above separates TWO questions:
    1. Do the systems differ in their normalized topology?
    2. Do they differ in PH when matched for size?

    If the answer to both is still 'yes' after size normalization,
    then the result is genuine and scientifically interesting.
    If not, the separation was an artifact of dataset differences.
    """)

if __name__ == '__main__':
    main()
