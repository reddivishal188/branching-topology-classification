"""
03_analyze.py — Statistical analysis, classification, and figure generation.

Pipeline:
1. Load features CSV
2. Statistical tests (Mann-Whitney U, effect sizes, multiple comparison correction)
3. ML classification (Logistic Regression, Random Forest, SVM)
4. Feature importance analysis
5. PCA visualization
6. Summary figures

Usage:
    python 03_analyze.py

Output:
    results/tables/statistical_results.csv
    results/tables/classification_results.csv
    results/figures/feature_comparison.png
    results/figures/pca_phase_space.png
    results/figures/feature_importance.png
    results/figures/confusion_matrix.png

Author: PI Claude
Date: 2026-07-08
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
import seaborn as sns

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

BASE_DIR = r"C:\Users\User\Claude\Projects\Retinnal_Fractal_Analysis"
DATA_DIR = os.path.join(BASE_DIR, "data")
FIGURES_DIR = os.path.join(BASE_DIR, "results", "figures")
TABLES_DIR = os.path.join(BASE_DIR, "results", "tables")

os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(TABLES_DIR, exist_ok=True)

# ── Plotting style ──
plt.rcParams.update({
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.labelsize': 11,
    'legend.fontsize': 9,
    'figure.figsize': (8, 5),
})
RETINA_COLOR = '#E74C3C'
CRACK_COLOR = '#2C3E50'
COLORS = [RETINA_COLOR, CRACK_COLOR]
LABEL_MAP = {'retinal': 'Retinal Vasculature', 'crack': 'Concrete Cracks'}


# ──────────────────────────────────────────────────────────────────────
# 1. DATA LOADING AND PREPARATION
# ──────────────────────────────────────────────────────────────────────

def load_features():
    """Load feature CSV and prepare for analysis."""
    csv_path = os.path.join(DATA_DIR, "features.csv")
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} samples with {len(df.columns)} columns")

    # Define which features to use for analysis (exclude size-dependent raw counts)
    # Size-dependent (use with caution — differ due to image resolution)
    size_features = ['n_nodes', 'n_edges', 'n_components',
                     'cyclomatic_number', 'max_edge_length',
                     'std_edge_length', 'n_junctions', 'n_endpoints']

    # Size-normalized features (robust to image resolution)
    normalized_features = [
        'cyclomatic_normalized',     # loops per edge
        'junction_ratio',            # junctions / all nodes
        'graph_density',             # edges / possible edges
        'avg_degree',                # mean degree
        'degree_entropy',            # entropy of degree distribution
        'p_deg2',                    # proportion of degree-2 nodes
        'p_deg3',                    # proportion of degree-3 nodes
        'p_deg4',                    # proportion of degree-4 nodes
        'assortativity',             # degree correlation
        'avg_clustering',            # clustering coefficient
        'mean_edge_length',          # average segment length
        'mean_euclidean_ratio',      # tortuosity proxy
        'largest_component_ratio',   # fraction of nodes in largest component
    ]

    # Persistent homology features (if available)
    ph_features = [
        'n_h1_features', 'max_h1_persistence',
        'mean_h1_persistence', 'total_h1_persistence',
        'h1_persistence_entropy', 'n_h1_significant'
    ]

    # Determine which PH features exist
    existing_ph = [c for c in ph_features if c in df.columns]

    # Primary analysis uses normalized features + PH
    analysis_features = normalized_features + existing_ph

    # Print dataset info
    print(f"  Retinal: {(df['label']=='retinal').sum()}")
    print(f"  Cracks:  {(df['label']=='crack').sum()}")
    print(f"  Analysis features: {len(analysis_features)}")

    return df, analysis_features


# ──────────────────────────────────────────────────────────────────────
# 2. STATISTICAL ANALYSIS
# ──────────────────────────────────────────────────────────────────────

def run_statistical_tests(df, features):
    """Run Mann-Whitney U tests and compute effect sizes."""
    from scipy.stats import mannwhitneyu

    retinal = df[df['label'] == 'retinal']
    crack = df[df['label'] == 'crack']

    results = []
    for feat in features:
        if feat not in df.columns:
            continue
        r_vals = retinal[feat].dropna()
        c_vals = crack[feat].dropna()

        if len(r_vals) < 5 or len(c_vals) < 5:
            continue

        # Mann-Whitney U test
        try:
            stat, pval = mannwhitneyu(r_vals, c_vals, alternative='two-sided')
        except ValueError:
            continue

        # Effect size: Cliff's delta
        n1, n2 = len(r_vals), len(c_vals)
        cliff_delta = (2 * stat) / (n1 * n2) - 1

        # Cohen's d (approximate from means and pooled std)
        mean_diff = r_vals.mean() - c_vals.mean()
        pooled_std = np.sqrt((r_vals.std()**2 + c_vals.std()**2) / 2)
        cohens_d = mean_diff / max(pooled_std, 1e-10)

        results.append({
            'feature': feat,
            'retinal_mean': r_vals.mean(),
            'retinal_std': r_vals.std(),
            'crack_mean': c_vals.mean(),
            'crack_std': c_vals.std(),
            'mannwhitney_U': stat,
            'p_value': pval,
            'cliffs_delta': cliff_delta,
            'cohens_d': cohens_d,
            'n_retinal': n1,
            'n_crack': n2,
        })

    results_df = pd.DataFrame(results)

    # Bonferroni correction
    n_tests = len(results_df)
    results_df['p_corrected'] = np.minimum(results_df['p_value'] * n_tests, 1.0)
    results_df['significant'] = results_df['p_corrected'] < 0.05

    # Sort by absolute Cohen's d
    results_df['abs_cohens_d'] = results_df['cohens_d'].abs()
    results_df = results_df.sort_values('abs_cohens_d', ascending=False)

    return results_df


# ──────────────────────────────────────────────────────────────────────
# 3. ML CLASSIFICATION
# ──────────────────────────────────────────────────────────────────────

def run_classification(df, features):
    """Run ML classification with nested cross-validation."""
    from sklearn.model_selection import StratifiedKFold, cross_val_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.svm import SVC
    from sklearn.metrics import balanced_accuracy_score, roc_auc_score
    from sklearn.model_selection import cross_validate

    # Prepare data
    X = df[features].dropna().values
    y = (df['label'].dropna() == 'retinal').astype(int).values

    # Use only rows where all features are non-NaN
    mask = df[features].notna().all(axis=1)
    X = df.loc[mask, features].values
    y = (df.loc[mask, 'label'] == 'retinal').astype(int).values

    print(f"\n  Classification samples: {len(X)} "
          f"(retinal={y.sum()}, crack={(1-y).sum()})")

    if len(X) < 20:
        print("  WARNING: Too few samples for reliable classification")
        return None

    # Define classifiers
    classifiers = {
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'SVM (RBF)': SVC(kernel='rbf', probability=True, random_state=42),
    }

    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scaler = StandardScaler()

    results = []
    for name, clf in classifiers.items():
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', clf)
        ])

        scores = cross_validate(pipeline, X, y, cv=cv,
                                scoring=['balanced_accuracy', 'roc_auc'],
                                return_train_score=False)

        results.append({
            'classifier': name,
            'balanced_accuracy_mean': scores['test_balanced_accuracy'].mean(),
            'balanced_accuracy_std': scores['test_balanced_accuracy'].std(),
            'roc_auc_mean': scores['test_roc_auc'].mean(),
            'roc_auc_std': scores['test_roc_auc'].std(),
        })

    return pd.DataFrame(results)


# ──────────────────────────────────────────────────────────────────────
# 4. FIGURES
# ──────────────────────────────────────────────────────────────────────

def plot_feature_comparison(df, features, filename='feature_comparison.png'):
    """Box plots comparing key features between groups."""
    selected = features[:9]  # First 9 features

    fig, axes = plt.subplots(3, 3, figsize=(14, 12))
    axes = axes.flatten()

    for i, feat in enumerate(selected[:9]):
        ax = axes[i]
        data = df[[feat, 'label']].dropna()

        for j, (label, color) in enumerate(zip(['retinal', 'crack'], COLORS)):
            vals = data[data['label'] == label][feat].values
            pos = j
            bp = ax.boxplot(vals, positions=[pos], widths=0.6,
                           patch_artist=True,
                           boxprops=dict(facecolor=color, alpha=0.6),
                           medianprops=dict(color='black', linewidth=1.5),
                           whiskerprops=dict(color=color),
                           capprops=dict(color=color))
            # Strip plot
            np.random.seed(42)
            jitter = np.random.normal(pos, 0.04, size=len(vals))
            ax.scatter(jitter, vals, alpha=0.3, s=8, color=color, edgecolors='none')

        ax.set_xticks([0, 1])
        ax.set_xticklabels(['Retinal', 'Crack'], fontsize=8)
        ax.set_ylabel(feat.replace('_', ' '), fontsize=9)
        ax.tick_params(axis='y', labelsize=8)
        ax.grid(alpha=0.2, axis='y')

    plt.tight_layout()
    path = os.path.join(FIGURES_DIR, filename)
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {path}")


def plot_pca_phase_space(df, features, filename='pca_phase_space.png'):
    """2D PCA projection of the feature space."""
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    mask = df[features].notna().all(axis=1)
    X = df.loc[mask, features].values
    y = df.loc[mask, 'label'].values

    if len(X) < 10:
        print("  WARNING: Too few samples for PCA")
        return

    # Standardize and PCA
    X_scaled = StandardScaler().fit_transform(X)
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)

    explained = pca.explained_variance_ratio_

    fig, ax = plt.subplots(1, 1, figsize=(8, 6))

    for label, color, marker in zip(['retinal', 'crack'], COLORS, ['o', 's']):
        mask_label = y == label
        ax.scatter(X_pca[mask_label, 0], X_pca[mask_label, 1],
                   c=color, marker=marker, label=LABEL_MAP.get(label, label),
                   s=50, alpha=0.7, edgecolors='w', linewidth=0.5)

    ax.set_xlabel(f'PC1 ({explained[0]:.1%} variance)', fontsize=11)
    ax.set_ylabel(f'PC2 ({explained[1]:.1%} variance)', fontsize=11)
    ax.set_title('Topological Phase Space', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)

    # Add text explaining cluster separation
    from scipy.spatial.distance import pdist
    retinal_pts = X_pca[y == 'retinal']
    crack_pts = X_pca[y == 'crack']
    if len(retinal_pts) > 0 and len(crack_pts) > 0:
        centroid_r = retinal_pts.mean(axis=0)
        centroid_c = crack_pts.mean(axis=0)
        distance = np.linalg.norm(centroid_r - centroid_c)
        ax.plot([centroid_r[0], centroid_c[0]],
                [centroid_r[1], centroid_c[1]], 'k--', alpha=0.3, linewidth=1)
        ax.text(0.05, 0.95, f'Cluster separation: {distance:.2f}',
                transform=ax.transAxes, fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    path = os.path.join(FIGURES_DIR, filename)
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {path}")

    return pca


def plot_feature_importance(df, features, filename='feature_importance.png'):
    """Random Forest feature importance."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler

    mask = df[features].notna().all(axis=1)
    X = df.loc[mask, features].values
    y = (df.loc[mask, 'label'] == 'retinal').astype(int).values

    if len(X) < 20:
        return

    X_scaled = StandardScaler().fit_transform(X)

    rf = RandomForestClassifier(n_estimators=200, random_state=42)
    rf.fit(X_scaled, y)

    importances = pd.DataFrame({
        'feature': features,
        'importance': rf.feature_importances_
    }).sort_values('importance', ascending=False)

    fig, ax = plt.subplots(1, 1, figsize=(9, 6))
    top_n = min(15, len(importances))
    ax.barh(range(top_n), importances['importance'].values[:top_n][::-1],
            color='#3498DB', edgecolor='white')
    ax.set_yticks(range(top_n))
    ax.set_yticklabels(importances['feature'].values[:top_n][::-1], fontsize=9)
    ax.set_xlabel('Feature Importance', fontsize=11)
    ax.set_title('Topological Features Ranked by Discriminative Power', fontsize=12)
    ax.invert_yaxis()
    ax.grid(alpha=0.3, axis='x')

    plt.tight_layout()
    path = os.path.join(FIGURES_DIR, filename)
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {path}")

    return importances


# ──────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("STATISTICAL ANALYSIS & CLASSIFICATION")
    print("=" * 60)

    # Load
    print("\n[1/5] Loading features...")
    df, features = load_features()

    # Statistical tests
    print("\n[2/5] Running statistical tests...")
    stats_df = run_statistical_tests(df, features)
    print(f"  Significant after Bonferroni: {stats_df['significant'].sum()}/{len(stats_df)}")

    # Save statistical results
    stats_path = os.path.join(TABLES_DIR, "statistical_results.csv")
    stats_df.to_csv(stats_path, index=False)
    print(f"  Saved: {stats_path}")

    # Print top discriminators
    print(f"\n  Top discriminators (by Cohen's d):")
    for _, row in stats_df.head(8).iterrows():
        sig = '***' if row['p_corrected'] < 0.001 else \
              '**' if row['p_corrected'] < 0.01 else \
              '*' if row['p_corrected'] < 0.05 else 'ns'
        print(f"    {row['feature']:25s}  d={row['cohens_d']:7.3f}  p_corr={row['p_corrected']:.4f} {sig}")

    # ML Classification
    print("\n[3/5] Running classification...")
    cls_df = run_classification(df, features)
    if cls_df is not None:
        cls_path = os.path.join(TABLES_DIR, "classification_results.csv")
        cls_df.to_csv(cls_path, index=False)
        print(f"  Saved: {cls_path}")
        print(f"\n  Classification results:")
        for _, row in cls_df.iterrows():
            print(f"    {row['classifier']:25s}  "
                  f"Bal. Acc. = {row['balanced_accuracy_mean']:.3f} ± {row['balanced_accuracy_std']:.3f}  "
                  f"ROC AUC = {row['roc_auc_mean']:.3f} ± {row['roc_auc_std']:.3f}")

    # Figures
    print("\n[4/5] Generating figures...")
    plot_feature_comparison(df, features)
    pca = plot_pca_phase_space(df, features)
    imp = plot_feature_importance(df, features)

    # Summary
    print(f"\n[5/5] Summary")
    print(f"{'='*60}")
    n_sig = stats_df['significant'].sum()
    n_total = len(stats_df)
    print(f"  Statistical tests: {n_sig}/{n_total} features significant (Bonferroni-corrected)")

    if cls_df is not None:
        best = cls_df.loc[cls_df['balanced_accuracy_mean'].idxmax()]
        print(f"  Best classifier: {best['classifier']} "
              f"(Acc = {best['balanced_accuracy_mean']:.1%} ± {best['balanced_accuracy_std']:.1%})")

    if imp is not None:
        top3 = imp.head(3)
        print(f"  Top features: {', '.join(top3['feature'].values)}")

    print(f"\n  Figures saved to: {FIGURES_DIR}")
    print(f"  Tables saved to: {TABLES_DIR}")


if __name__ == '__main__':
    main()
