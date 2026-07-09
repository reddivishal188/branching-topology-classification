"""
graph_utils.py — Graph extraction from binary skeleton images.

Converts a binary vessel/crack mask into a NetworkX graph object.
Pipeline: binary mask → skeletonize → detect junction/endpoint nodes
          → trace edges between nodes → build graph.

Algorithm
---------
1. Skeletonize the binary mask to single-pixel width.
2. Detect junction pixels (>=3 neighbours) and endpoint pixels (==1 neighbour)
   using a 3x3 convolution kernel.
3. Starting from each node, walk in each available direction along the skeleton,
   recording the pixel path, until hitting another node.
4. Build a NetworkX graph: nodes = junction/endpoint pixels,
   edges = traced paths between nodes.

Author: PI Claude
Date: 2026-07-08
"""

import numpy as np
import networkx as nx
from skimage.morphology import skeletonize, thin
from scipy.ndimage import convolve
import warnings


# ──────────────────────────────────────────────────────────────────────
# SKELETONIZATION
# ──────────────────────────────────────────────────────────────────────

def skeletonize_mask(mask, method='zhang'):
    """
    Thin a binary mask to single-pixel width skeleton.

    Parameters
    ----------
    mask : np.ndarray, shape (H, W), dtype bool or uint8
        Binary segmentation mask (1 = vessel/crack, 0 = background).
    method : str
        'zhang' (default, fast, 2D), 'lee' (3D), or 'thin' (iterative morphological).

    Returns
    -------
    skeleton : np.ndarray, shape (H, W), dtype bool
        Single-pixel-wide skeleton.
    """
    if mask.dtype != bool:
        mask = mask > 0

    if method == 'zhang':
        skel = skeletonize(mask, method='zhang')
    elif method == 'lee':
        skel = skeletonize(mask, method='lee')
    else:
        skel = thin(mask)

    return skel


# ──────────────────────────────────────────────────────────────────────
# NODE DETECTION
# ──────────────────────────────────────────────────────────────────────

def detect_junction_points(skeleton):
    """
    Detect junction and endpoint nodes in a skeleton.

    Uses a 3x3 convolution to count neighbours for each skeleton pixel.

    Parameters
    ----------
    skeleton : np.ndarray, shape (H, W), dtype bool

    Returns
    -------
    junction_mask : np.ndarray, shape (H, W), dtype bool
        True where junction points (>=3 neighbours).
    endpoint_mask : np.ndarray, shape (H, W), dtype bool
        True where end points (exactly 1 neighbour).
    """
    skel_uint8 = skeleton.astype(np.uint8)

    # 3x3 neighbour sum (excluding centre)
    kernel = np.array([[1, 1, 1],
                       [1, 0, 1],
                       [1, 1, 1]], dtype=np.uint8)

    neighbour_count = convolve(skel_uint8, kernel, mode='constant', cval=0)

    # Only consider skeleton pixels
    n_on_skel = neighbour_count * skel_uint8

    junction_mask = (n_on_skel >= 3).astype(bool)
    endpoint_mask = (n_on_skel == 1).astype(bool)

    return junction_mask, endpoint_mask


# ──────────────────────────────────────────────────────────────────────
# EDGE TRACING
# ──────────────────────────────────────────────────────────────────────

def _neighbours(y, x, shape):
    """Return 8-connected neighbour coordinates within image bounds."""
    h, w = shape
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w:
                yield ny, nx


def trace_edges_between_nodes(skeleton, node_mask):
    """
    Trace skeleton paths between all node pixels.

    For each node pixel, look in each of the 8 directions for a neighbour
    skeleton pixel. Walk along that branch until hitting another node.

    Parameters
    ----------
    skeleton : np.ndarray, shape (H, W), dtype bool
    node_mask : np.ndarray, shape (H, W), dtype bool
        Pixels that are either junctions or endpoints.

    Returns
    -------
    edges : list of tuples
        Each: (y1, x1, y2, x2, length, [list of (y,x) path pixels])
    """
    h, w = skeleton.shape
    visited_nodes = set()  # track node -> direction pairs already traced
    edges = []

    node_coords = list(zip(*np.where(node_mask)))

    for y, x in node_coords:
        # Look in each of the 8 directions
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue

                # Avoid double-tracing: same direction from this node
                direction_id = (y, x, dy, dx)
                if direction_id in visited_nodes:
                    continue
                visited_nodes.add(direction_id)

                ny, nx = y + dy, x + dx
                if ny < 0 or ny >= h or nx < 0 or nx >= w:
                    continue
                if not skeleton[ny, nx]:
                    continue
                # If the neighbour is also a node, it's a direct connection
                if node_mask[ny, nx]:
                    # Direct node-to-node connection (length 1)
                    other_id = (ny, nx, -dy, -dx)
                    visited_nodes.add(other_id)
                    edges.append((y, x, ny, nx, 1, [(y, x), (ny, nx)]))
                    continue

                # Walk forward along the branch
                path = [(y, x), (ny, nx)]
                cy, cx = ny, nx
                py, px = y, x

                while True:
                    # Find next step: skeleton neighbour that's not where we came from
                    next_steps = []
                    for nny, nnx in _neighbours(cy, cx, (h, w)):
                        if (nny, nnx) == (py, px):
                            continue
                        if skeleton[nny, nnx]:
                            next_steps.append((nny, nnx))

                    if len(next_steps) == 0:
                        # Dead end — this pixel should have been an endpoint
                        break
                    elif len(next_steps) == 1:
                        # Keep walking
                        py, px = cy, cx
                        cy, cx = next_steps[0]
                        path.append((cy, cx))

                        # Check if we hit a node
                        if node_mask[cy, cx]:
                            break
                    else:
                        # Multiple branches — this is a junction we didn't mark
                        # (can happen at branch points that have 3 neighbours
                        #  where one path enters and 2 leave, but convolution
                        #  might miscount)
                        break

                # Record edge if we reached a node
                if node_mask[cy, cx]:
                    edge_length = len(path)
                    edges.append((y, x, cy, cx, edge_length, path))

                    # Mark the reverse direction as visited for the target node
                    reverse_dy = y - cy
                    reverse_dx = x - cx
                    # Normalize to -1, 0, 1
                    if reverse_dy != 0:
                        reverse_dy = reverse_dy // abs(reverse_dy)
                    if reverse_dx != 0:
                        reverse_dx = reverse_dx // abs(reverse_dx)
                    visited_nodes.add((cy, cx, reverse_dy, reverse_dx))

    return edges


# ──────────────────────────────────────────────────────────────────────
# GRAPH CONSTRUCTION
# ──────────────────────────────────────────────────────────────────────

def skeleton_to_graph(skeleton):
    """
    Convert a binary skeleton to a NetworkX graph.

    Parameters
    ----------
    skeleton : np.ndarray, shape (H, W), dtype bool
        Single-pixel-wide skeleton.

    Returns
    -------
    G : networkx.Graph
        Graph where:
        - Node key: (y, x) tuple
        - Node attributes: 'pos' (y, x), 'type' ('junction', 'endpoint')
        - Edge attributes: 'length' (pixels), 'path' (list of (y,x) tuples)

    Notes
    -----
    - Isolated skeleton loops (no junctions or endpoints) are not captured.
    - Self-edges (loops of length 0) are removed.
    - The graph is undirected.
    """
    if skeleton.sum() == 0:
        return nx.Graph()

    # Detect nodes
    junction_mask, endpoint_mask = detect_junction_points(skeleton)
    node_mask = junction_mask | endpoint_mask

    # If no nodes found, something is wrong — could be a closed loop
    # without any endpoints. In that case, add all skeleton pixels as nodes.
    if node_mask.sum() == 0:
        coords = list(zip(*np.where(skeleton)))
        G = nx.Graph()
        for y, x in coords:
            G.add_node((y, x), pos=(float(y), float(x)), type='isolated')
        return G

    # Trace edges
    edges = trace_edges_between_nodes(skeleton, node_mask)

    # Build graph
    G = nx.Graph()

    for y1, x1, y2, x2, length, path in edges:
        node1 = (y1, x1)
        node2 = (y2, x2)

        if node1 == node2:
            continue  # skip self-loops

        # Determine node types
        type1 = ('junction' if junction_mask[y1, x1] else
                 'endpoint' if endpoint_mask[y1, x1] else
                 'path')
        type2 = ('junction' if junction_mask[y2, x2] else
                 'endpoint' if endpoint_mask[y2, x2] else
                 'path')

        # Compute Euclidean distance
        euclidean = np.sqrt((y2 - y1)**2 + (x2 - x1)**2)

        G.add_node(node1, pos=(float(y1), float(x1)), type=type1)
        G.add_node(node2, pos=(float(y2), float(x2)), type=type2)
        G.add_edge(node1, node2,
                   length=length,
                   euclidean_dist=euclidean,
                   path=path)

    # Add any unconnected node pixels as isolated nodes
    for y in range(skeleton.shape[0]):
        for x in range(skeleton.shape[1]):
            if node_mask[y, x] and (y, x) not in G:
                ntype = ('junction' if junction_mask[y, x] else 'endpoint')
                G.add_node((y, x), pos=(float(y), float(x)), type=ntype)

    return G


# ──────────────────────────────────────────────────────────────────────
# SUMMARY
# ──────────────────────────────────────────────────────────────────────

def summarise_graph(G):
    """
    Print a summary of graph properties and return statistics dict.

    Parameters
    ----------
    G : networkx.Graph

    Returns
    -------
    stats : dict
        Key graph statistics.
    """
    if G.number_of_nodes() == 0:
        print("Graph Summary:\n  Empty graph (0 nodes, 0 edges)")
        return {'n_nodes': 0, 'n_edges': 0, 'n_components': 0,
                'n_junctions': 0, 'n_endpoints': 0, 'cyclomatic': 0,
                'mean_edge_length': 0, 'std_edge_length': 0}

    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()

    if nx.is_empty(G):
        n_components = n_nodes
    else:
        n_components = nx.number_connected_components(G)

    # Count node types
    type_counts = {'junction': 0, 'endpoint': 0, 'path': 0, 'isolated': 0}
    for n, data in G.nodes(data=True):
        t = data.get('type', 'unknown')
        if t in type_counts:
            type_counts[t] += 1
        else:
            type_counts['isolated'] += 1

    # Edge length stats
    if n_edges > 0:
        lengths = [d.get('length', 0) for _, _, d in G.edges(data=True)]
        mean_len = float(np.mean(lengths))
        std_len = float(np.std(lengths))
        min_len = int(np.min(lengths))
        max_len = int(np.max(lengths))
    else:
        lengths = []
        mean_len = std_len = min_len = max_len = 0

    cyclomatic = n_edges - n_nodes + n_components

    print(f"Graph Summary:")
    print(f"  Nodes: {n_nodes} "
          f"(junctions={type_counts['junction']}, "
          f"endpoints={type_counts['endpoint']}, "
          f"path={type_counts['path']}, "
          f"isolated={type_counts['isolated']})")
    print(f"  Edges: {n_edges}")
    print(f"  Connected components: {n_components}")
    if n_edges > 0:
        print(f"  Edge length (pixels): mean={mean_len:.1f} "
              f"± {std_len:.1f}, range=[{min_len}, {max_len}]")
    print(f"  Cyclomatic number (μ = E - V + C): {cyclomatic}")

    return {
        'n_nodes': n_nodes,
        'n_edges': n_edges,
        'n_components': n_components,
        'n_junctions': type_counts['junction'],
        'n_endpoints': type_counts['endpoint'],
        'cyclomatic': cyclomatic,
        'mean_edge_length': mean_len,
        'std_edge_length': std_len,
    }
