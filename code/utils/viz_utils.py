"""
viz_utils.py — Visualization utilities for branching network analysis.

Functions for overlaying graphs on images, plotting degree distributions,
persistence diagrams, and creating publication-quality figures.

Author: PI Claude
Date: 2026-07-08
"""

import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import Circle
import warnings

# Colour palette for the project
RETINA_COLOR = '#E74C3C'     # red for retinal
CRACK_COLOR = '#2C3E50'      # dark blue-grey for cracks
SYNTHETIC_COLOR = '#27AE60'  # green for synthetic
NULL_COLOR = '#95A5A6'       # grey for null models
ACCENT_COLOR = '#F39C12'     # orange for highlights


def plot_graph_overlay(image, skeleton, G, ax=None, title=None):
    """
    Overlay extracted graph on the original image.

    Parameters
    ----------
    image : np.ndarray (H, W) or (H, W, 3)
        Original image (or None to use skeleton as background).
    skeleton : np.ndarray (H, W), dtype bool
        The skeleton used for extraction.
    G : networkx.Graph
        Extracted graph.
    ax : matplotlib.axes.Axes, optional
    title : str, optional
    """
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    # Show original image or skeleton
    if image is not None:
        if image.ndim == 2:
            ax.imshow(image, cmap='gray')
        else:
            ax.imshow(image)
    else:
        ax.imshow(skeleton, cmap='gray', alpha=0.3)

    # Draw edges
    for u, v, data in G.edges(data=True):
        path = data.get('path', [])
        if path:
            path = np.array(path)
            ax.plot(path[:, 1], path[:, 0], '-', color=ACCENT_COLOR,
                    linewidth=0.5, alpha=0.8)
        else:
            # Fallback: draw line between nodes
            uy, ux = G.nodes[u]['pos']
            vy, vx = G.nodes[v]['pos']
            ax.plot([ux, vx], [uy, vy], '-', color=ACCENT_COLOR,
                    linewidth=0.5, alpha=0.8)

    # Draw nodes
    for n, data in G.nodes(data=True):
        y, x = data['pos']
        ntype = data.get('type', 'unknown')
        if ntype == 'junction':
            ax.plot(x, y, 'o', color=RETINA_COLOR, markersize=4, zorder=5)
        elif ntype == 'endpoint':
            ax.plot(x, y, 's', color='blue', markersize=3, zorder=5)
        else:
            ax.plot(x, y, '.', color='gray', markersize=2, zorder=5)

    ax.set_xlim(0, image.shape[1] if image is not None else skeleton.shape[1])
    ax.set_ylim(image.shape[0] if image is not None else skeleton.shape[0], 0)
    ax.set_aspect('equal')
    ax.axis('off')

    if title:
        ax.set_title(title)

    return ax


def plot_degree_distribution(graphs, labels, ax=None, title=None):
    """
    Plot degree distributions for one or more groups of graphs.

    Parameters
    ----------
    graphs : list of list of networkx.Graph
        Outer list: groups. Inner list: graphs in each group.
    labels : list of str
        Labels for each group.
    ax : matplotlib.axes.Axes, optional
    title : str, optional
    """
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(8, 5))

    colors = [RETINA_COLOR, CRACK_COLOR, SYNTHETIC_COLOR, NULL_COLOR]

    for i, (group, label) in enumerate(zip(graphs, labels)):
        all_degrees = []
        for G in group:
            if G.number_of_nodes() > 0:
                all_degrees.extend([d for n, d in G.degree()])

        if all_degrees:
            max_deg = max(max(all_degrees), 5)
            bins = np.arange(0.5, max_deg + 1.5, 1)
            ax.hist(all_degrees, bins=bins, alpha=0.5, color=colors[i % len(colors)],
                    label=f'{label} (n={len(all_degrees)})', density=True)

    ax.set_xlabel('Degree')
    ax.set_ylabel('Probability')
    ax.set_xticks(range(0, int(ax.get_xlim()[1]) + 1))
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    if title:
        ax.set_title(title)

    return ax


def plot_feature_comparison(df, feature_cols, group_col, ax=None, title=None):
    """
    Side-by-side box plots comparing features between groups.

    Parameters
    ----------
    df : pandas.DataFrame
        Must contain feature_cols and group_col.
    feature_cols : list of str
        Feature column names to plot.
    group_col : str
        Column name for group labels.
    """
    import seaborn as sns

    n_features = len(feature_cols)
    fig, axes = plt.subplots(1, n_features, figsize=(5 * n_features, 4))
    if n_features == 1:
        axes = [axes]

    for ax, feat in zip(axes, feature_cols):
        sns.boxplot(data=df, x=group_col, y=feat, ax=ax,
                    palette=[RETINA_COLOR, CRACK_COLOR])
        sns.stripplot(data=df, x=group_col, y=feat, ax=ax,
                      color='black', alpha=0.3, size=3)
        ax.set_title(feat)
        ax.set_xlabel('')

    if title:
        fig.suptitle(title)

    plt.tight_layout()
    return fig, axes


def plot_persistence_diagram(dgms, ax=None, title=None):
    """
    Plot a persistence diagram from ripser output.

    Parameters
    ----------
    dgms : list of np.ndarray
        Output from ripser. dgms[0] = H0, dgms[1] = H1, etc.
        Each array has shape (N, 2) with columns [birth, death].
    ax : matplotlib.axes.Axes, optional
    title : str, optional
    """
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(6, 6))

    colors = ['#3498DB', '#E74C3C', '#27AE60', '#F39C12']
    labels = ['H0 (components)', 'H1 (loops)', 'H2 (voids)', 'H3']

    max_val = 0
    for i, dgm in enumerate(dgms):
        if len(dgm) > 0:
            finite = dgm[np.isfinite(dgm[:, 1])]
            if len(finite) > 0:
                max_val = max(max_val, np.max(finite))

    max_val = max(max_val, 1.0)

    # Diagonal line
    ax.plot([0, max_val], [0, max_val], 'k--', alpha=0.3, linewidth=0.5)

    for i, dgm in enumerate(dgms):
        if i >= len(labels):
            break
        if len(dgm) > 0:
            finite = dgm[np.isfinite(dgm[:, 1])]
            if len(finite) > 0:
                ax.scatter(finite[:, 0], finite[:, 1],
                          c=colors[i % len(colors)],
                          label=labels[i], s=10, alpha=0.7, edgecolors='none')

    ax.set_xlabel('Birth')
    ax.set_ylabel('Death')
    ax.set_aspect('equal')
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    if title:
        ax.set_title(title)

    return ax


def plot_topological_phase_space(features_df, x_col, y_col, label_col, ax=None, title=None):
    """
    2D scatter plot of topological phase space.

    Parameters
    ----------
    features_df : pandas.DataFrame
    x_col, y_col : str
        Column names for x and y axes.
    label_col : str
        Column name for group labels.
    """
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))

    groups = features_df[label_col].unique()
    colors = [RETINA_COLOR, CRACK_COLOR, SYNTHETIC_COLOR, NULL_COLOR]
    markers = ['o', 's', '^', 'D']

    for i, group in enumerate(groups):
        mask = features_df[label_col] == group
        ax.scatter(features_df.loc[mask, x_col],
                  features_df.loc[mask, y_col],
                  c=colors[i % len(colors)],
                  marker=markers[i % len(markers)],
                  label=group, s=40, alpha=0.7, edgecolors='w', linewidth=0.5)

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.legend()
    ax.grid(alpha=0.3)

    if title:
        ax.set_title(title)

    return ax


def save_figure(fig, filename, dpi=300):
    """Save figure to results/figures/ directory."""
    import os
    save_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           'results', 'figures')
    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, filename)
    fig.savefig(path, dpi=dpi, bbox_inches='tight')
    print(f"Saved: {path}")
    return path
