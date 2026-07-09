"""
02_compute_features.py — Compute topological and graph-theoretic features.

Loads extracted graphs (from 01_extract_graphs.py), computes invariants,
and saves results as CSV and a combined feature DataFrame.

Features computed:
    GRAPH-LEVEL:
        n_nodes, n_edges, n_components
        cyclomatic_number, cyclomatic_normalized
        n_junctions, n_endpoints, junction_ratio
        graph_density, avg_degree, degree_entropy
        p_deg2, p_deg3, p_deg4 (proportion of nodes by degree)
        assortativity, avg_clustering
        mean_edge_length, std_edge_length, max_edge_length
        mean_euclidean_ratio (tortuosity proxy)
        largest_component_ratio

    PERSISTENT HOMOLOGY (if ripser available):
        n_h0_features, n_h1_features
        max_h1_persistence, mean_h1_persistence, total_h1_persistence
        h1_persistence_entropy

Usage:
    python 02_compute_features.py

Output:
    data/features.csv          — All features, one row per graph
    data/feature_metadata.json — Feature descriptions

Author: PI Claude
Date: 2026-07-08
"""

import numpy as np
import networkx as nx
import pandas as pd
import pickle
import os
import sys
import json
import glob
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

BASE_DIR = r"C:\Users\User\Claude\Projects\Retinnal_Fractal_Analysis"
RETINAL_GRAPH_DIR = os.path.join(BASE_DIR, "data", "retinal", "graphs")
CRACK_GRAPH_DIR = os.path.join(BASE_DIR, "data", "crack", "graphs")
LEAF_GRAPH_DIR = os.path.join(BASE_DIR, "data", "leaf", "graphs")
DLA_GRAPH_DIR = os.path.join(BASE_DIR, "data", "dla", "graphs")
OUTPUT_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ──────────────────────────────────────────────────────────────────────
# FEATURE DEFINITIONS
# ──────────────────────────────────────────────────────────────────────

def compute_graph_features(G):
    """
    Compute all topological and graph-theoretic features for a single graph.

    Parameters
    ----------
    G : networkx.Graph

    Returns
    -------
    features : dict
        Feature name -> value mapping.
    """
    features = {}

    # Basic counts
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    features['n_nodes'] = n_nodes
    features['n_edges'] = n_edges

    if n_nodes == 0:
        # Empty graph — fill with zeros
        zeros = ['n_components', 'cyclomatic_number', 'cyclomatic_normalized',
                 'n_junctions', 'n_endpoints', 'junction_ratio', 'graph_density',
                 'avg_degree', 'degree_entropy', 'p_deg2', 'p_deg3', 'p_deg4',
                 'assortativity', 'avg_clustering', 'mean_edge_length',
                 'std_edge_length', 'max_edge_length', 'mean_euclidean_ratio',
                 'largest_component_ratio']
        for z in zeros:
            features[z] = 0.0
        return features

    # Connected components
    if nx.is_empty(G):
        n_components = n_nodes
    else:
        n_components = nx.number_connected_components(G)
    features['n_components'] = n_components

    # Cyclomatic number (loops measure)
    cyclomatic = n_edges - n_nodes + n_components
    features['cyclomatic_number'] = cyclomatic
    features['cyclomatic_normalized'] = cyclomatic / max(n_edges, 1)

    # Node type counts
    node_types = Counter([d.get('type', '') for _, d in G.nodes(data=True)])
    features['n_junctions'] = node_types.get('junction', 0)
    features['n_endpoints'] = node_types.get('endpoint', 0)
    total_labeled = features['n_junctions'] + features['n_endpoints']
    features['junction_ratio'] = features['n_junctions'] / max(total_labeled, 1)

    # Graph density
    features['graph_density'] = nx.density(G)

    # Degree distribution
    if n_nodes > 1:
        degrees = [d for _, d in G.degree()]
        features['avg_degree'] = np.mean(degrees)

        # Degree distribution entropy
        deg_counts = Counter(degrees)
        total = sum(deg_counts.values())
        probs = [c / total for c in deg_counts.values()]
        features['degree_entropy'] = -sum(p * np.log(p) for p in probs if p > 0)

        # Proportion of nodes with specific degrees
        features['p_deg2'] = deg_counts.get(2, 0) / total
        features['p_deg3'] = deg_counts.get(3, 0) / total
        features['p_deg4'] = deg_counts.get(4, 0) / total
    else:
        features['avg_degree'] = 0.0
        features['degree_entropy'] = 0.0
        features['p_deg2'] = 0.0
        features['p_deg3'] = 0.0
        features['p_deg4'] = 0.0

    # Assortativity (degree correlation)
    try:
        features['assortativity'] = nx.degree_assortativity_coefficient(G)
    except (nx.NetworkXError, ZeroDivisionError):
        features['assortativity'] = 0.0

    # Clustering coefficient
    try:
        features['avg_clustering'] = nx.average_clustering(G)
    except ZeroDivisionError:
        features['avg_clustering'] = 0.0

    # Edge length statistics
    if n_edges > 0:
        lengths = [d.get('length', 1) for _, _, d in G.edges(data=True)]
        euclidean_dists = [d.get('euclidean_dist', d.get('length', 1))
                          for _, _, d in G.edges(data=True)]

        features['mean_edge_length'] = float(np.mean(lengths))
        features['std_edge_length'] = float(np.std(lengths))
        features['max_edge_length'] = int(np.max(lengths))

        # Tortuosity proxy: ratio of path length to euclidean distance
        ratios = [p / max(e, 1) for p, e in zip(lengths, euclidean_dists)]
        features['mean_euclidean_ratio'] = float(np.mean(ratios))
    else:
        features['mean_edge_length'] = 0.0
        features['std_edge_length'] = 0.0
        features['max_edge_length'] = 0
        features['mean_euclidean_ratio'] = 0.0

    # Largest connected component size ratio
    if n_nodes > 0 and not nx.is_empty(G):
        components = sorted(nx.connected_components(G), key=len, reverse=True)
        features['largest_component_ratio'] = len(components[0]) / n_nodes
    else:
        features['largest_component_ratio'] = 1.0 / max(n_nodes, 1)

    return features


def compute_persistence_features(G, max_ph_nodes=500):
    """
    Compute persistent homology features using ripser.

    Sub-samples the graph to max_ph_nodes to keep computation tractable.
    Returns None if ripser is not installed or computation fails.
    """
    n_nodes = G.number_of_nodes()
    if n_nodes < 10:
        return None

    try:
        import ripser
    except ImportError:
        return None

    try:
        # Create point cloud from node positions
        pos = []
        for n, data in G.nodes(data=True):
            p = data.get('pos', None)
            if p is not None:
                pos.append([float(p[1]), float(p[0])])  # (x, y)

        if len(pos) < 10:
            return None

        pos = np.array(pos)

        # Subsample if too large (ripser scales quadratically with N)
        if len(pos) > max_ph_nodes:
            rng = np.random.RandomState(42)
            idx = rng.choice(len(pos), max_ph_nodes, replace=False)
            pos = pos[idx]

        # Compute persistent homology (H0 and H1 only)
        result = ripser.ripser(pos, maxdim=1, coeff=2)

        dgms = result['dgms']

        features = {}

        # H1 features (loops)
        h1 = dgms[1] if len(dgms) > 1 else np.array([])
        finite_h1 = h1[np.isfinite(h1[:, 1])] if len(h1) > 0 else np.array([])

        features['n_h1_features'] = len(finite_h1)

        if len(finite_h1) > 0:
            lifetimes = finite_h1[:, 1] - finite_h1[:, 0]
            features['max_h1_persistence'] = float(np.max(lifetimes))
            features['mean_h1_persistence'] = float(np.mean(lifetimes))
            features['total_h1_persistence'] = float(np.sum(lifetimes))

            # Persistence entropy
            total_life = np.sum(lifetimes)
            if total_life > 0:
                probs = lifetimes / total_life
                features['h1_persistence_entropy'] = float(
                    -np.sum(probs * np.log(probs + 1e-10)))
            else:
                features['h1_persistence_entropy'] = 0.0

            # Number of significant loops (persistence > 10% of max)
            significant = lifetimes > 0.1 * np.max(lifetimes)
            features['n_h1_significant'] = int(np.sum(significant))
        else:
            features['max_h1_persistence'] = 0.0
            features['mean_h1_persistence'] = 0.0
            features['total_h1_persistence'] = 0.0
            features['h1_persistence_entropy'] = 0.0
            features['n_h1_significant'] = 0

        return features

    except Exception as e:
        # Silent failure — PH is optional for this analysis
        return None


# ──────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────

def load_graphs(graph_dir, label):
    """Load all .gpickle files from a directory."""
    graphs = []
    pattern = os.path.join(graph_dir, "*.gpickle")
    files = sorted(glob.glob(pattern))
    print(f"  Loading {len(files)} graphs from {label}...")

    for fpath in files:
        try:
            with open(fpath, 'rb') as f:
                G = pickle.load(f)
            basename = os.path.splitext(os.path.basename(fpath))[0]
            graphs.append({'name': basename, 'G': G, 'label': label})
        except Exception as e:
            print(f"    ERROR loading {fpath}: {e}")

    return graphs


def compute_all_features(graphs, do_persistence=True):
    """Compute all features for a list of graphs."""
    rows = []
    ph_count = 0

    for i, item in enumerate(graphs):
        if (i + 1) % 20 == 0:
            print(f"  [{i+1}/{len(graphs)}] computing features...")

        G = item['G']
        row = {
            'name': item['name'],
            'label': item['label']
        }

        # Graph features
        gf = compute_graph_features(G)
        row.update(gf)

        # Persistence features
        if do_persistence:
            pf = compute_persistence_features(G)
            if pf is not None:
                row.update(pf)
                ph_count += 1
            else:
                # Fill with NaN
                ph_keys = ['n_h1_features', 'max_h1_persistence',
                          'mean_h1_persistence', 'total_h1_persistence',
                          'h1_persistence_entropy', 'n_h1_significant']
                for k in ph_keys:
                    row[k] = np.nan

        rows.append(row)

    df = pd.DataFrame(rows)
    return df, ph_count


def main():
    print("=" * 60)
    print("FEATURE COMPUTATION")
    print("=" * 60)

    # Load graphs
    print("\n[1/3] Loading graphs...")
    all_graphs = []
    all_graphs.extend(load_graphs(RETINAL_GRAPH_DIR, 'retinal'))
    all_graphs.extend(load_graphs(CRACK_GRAPH_DIR, 'crack'))
    all_graphs.extend(load_graphs(LEAF_GRAPH_DIR, 'leaf'))
    all_graphs.extend(load_graphs(DLA_GRAPH_DIR, 'dla'))
    print(f"  Total: {len(all_graphs)} graphs")

    # Compute features
    print("\n[2/3] Computing features...")
    df, ph_count = compute_all_features(all_graphs, do_persistence=True)

    # Save
    print(f"\n[3/3] Saving results...")
    csv_path = os.path.join(OUTPUT_DIR, "features.csv")
    df.to_csv(csv_path, index=False)
    print(f"  Saved: {csv_path}")

    # Also save a pickled version for analysis scripts
    pkl_path = os.path.join(OUTPUT_DIR, "features.pkl")
    df.to_pickle(pkl_path)
    print(f"  Saved: {pkl_path}")

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"  Retinal graphs: {(df['label']=='retinal').sum()}")
    print(f"  Crack graphs:   {(df['label']=='crack').sum()}")
    print(f"  Leaf graphs:    {(df['label']=='leaf').sum()}")
    ph_cols = ['n_h1_features', 'max_h1_persistence', 'mean_h1_persistence',
               'total_h1_persistence', 'h1_persistence_entropy', 'n_h1_significant']
    has_ph = any(c in df.columns for c in ph_cols)
    if has_ph:
        ph_with_data = df[ph_cols[0]].notna().sum() if ph_cols[0] in df.columns else 0
        print(f"  Graph features: {len(df.columns) - 2 - len(ph_cols)}")
        print(f"  PH features:    {ph_with_data} graphs (with persistent homology)")
    else:
        print(f"  Graph features: {len(df.columns) - 2}")

    # Quick comparison: top 5 discriminative features by effect size
    print(f"\n  Quick comparison (retinal vs crack, mean ± std):")
    for feat in ['n_nodes', 'n_edges', 'cyclomatic_number', 'cyclomatic_normalized',
                 'junction_ratio', 'graph_density', 'assortativity', 'avg_clustering']:
        if feat in df.columns:
            r_mean = df[df['label']=='retinal'][feat].mean()
            r_std = df[df['label']=='retinal'][feat].std()
            c_mean = df[df['label']=='crack'][feat].mean()
            c_std = df[df['label']=='crack'][feat].std()
            print(f"    {feat:25s}: retinal={r_mean:8.2f}±{r_std:6.2f}  crack={c_mean:8.2f}±{c_std:6.2f}")


if __name__ == '__main__':
    main()
