"""
generate_synthetic.py — Generate synthetic branching networks for pipeline testing.

Creates three types of branching patterns with known ground truth topology:
1. Tree network (transport-like) — bifurcating tree, no loops
2. Mesh network (crack-like) — intersecting lines forming loops
3. DLA cluster (diffusion-like) — diffusion-limited aggregation

Each pattern is saved as both an image and a ground-truth skeleton,
allowing quantitative validation of the graph extraction pipeline.

Author: PI Claude
Date: 2026-07-08
"""

import sys
import numpy as np
import networkx as nx
import cv2
import os
import pickle
import warnings

# Add project root to path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ──────────────────────────────────────────────────────────────────────
# 1. TREE NETWORK — bifurcating transport-like branching
# ──────────────────────────────────────────────────────────────────────

def generate_tree(size=512, initial_angle=90, branching_angle=30,
                  max_depth=6, length_scale=80, length_decay=0.7):
    """
    Generate a bifurcating tree network (transport-like).

    Parameters
    ----------
    size : int
        Image height/width.
    initial_angle : float
        Angle of the main trunk (degrees from horizontal).
    branching_angle : float
        Maximum deviation at each bifurcation (degrees).
    max_depth : int
        Maximum branching depth.
    length_scale : float
        Length of the first trunk (pixels).
    length_decay : float
        Factor by which branch length shrinks per level.

    Returns
    -------
    image : np.ndarray (size, size), uint8
        Rendered binary image.
    skeleton : np.ndarray (size, size), bool
        Ground truth skeleton.
    G : networkx.Graph
        Ground truth graph.
    """
    image = np.zeros((size, size), dtype=np.uint8)
    G = nx.Graph()  # ground truth graph

    # Start from bottom center
    origin = (size - 10, size // 2)
    current_id = 0

    def branch(start, angle, depth, length):
        nonlocal current_id
        if depth > max_depth or length < 2:
            return

        # Compute endpoint
        rad = np.radians(angle)
        end_y = start[0] - int(length * np.cos(rad))
        end_x = start[1] + int(length * np.sin(rad))

        # Clamp to image bounds
        end_y = max(0, min(size - 1, end_y))
        end_x = max(0, min(size - 1, end_x))

        end_point = (end_y, end_x)

        # Draw line on image
        cv2.line(image, (start[1], start[0]), (end_x, end_y), 255, 1)

        # Add nodes and edge
        node_a = current_id
        current_id += 1
        node_b = current_id
        current_id += 1

        G.add_node(node_a, pos=(float(start[0]), float(start[1])))
        G.add_node(node_b, pos=(float(end_y), float(end_x)))
        G.add_edge(node_a, node_b)

        # Recurse
        new_length = length * length_decay
        branch(end_point, angle - branching_angle, depth + 1, new_length)
        branch(end_point, angle + branching_angle, depth + 1, new_length)

    # Draw root
    G.add_node(current_id, pos=(float(origin[0]), float(origin[1])))
    current_id += 1

    branch(origin, initial_angle, 0, length_scale)

    # Skeleton = image (since we drew single-pixel lines)
    skeleton = image.astype(bool)

    return image, skeleton, G


# ──────────────────────────────────────────────────────────────────────
# 2. MESH NETWORK — crack-like intersecting lines with loops
# ──────────────────────────────────────────────────────────────────────

def generate_mesh(size=512, n_lines=30, line_length=150):
    """
    Generate a mesh-like network (crack-like) with intersecting lines.

    Parameters
    ----------
    size : int
        Image height/width.
    n_lines : int
        Number of random line segments.
    line_length : int
        Maximum length of each line segment.

    Returns
    -------
    image : np.ndarray (size, size), uint8
        Rendered binary image.
    skeleton : np.ndarray (size, size), bool
        Ground truth skeleton.
    G : networkx.Graph
        Ground truth graph.
    """
    image = np.zeros((size, size), dtype=np.uint8)

    np.random.seed(42)
    for _ in range(n_lines):
        x1 = np.random.randint(0, size)
        y1 = np.random.randint(0, size)
        angle = np.random.uniform(0, 180)
        length = np.random.randint(20, line_length)
        rad = np.radians(angle)
        x2 = int(x1 + length * np.cos(rad))
        y2 = int(y1 + length * np.sin(rad))
        x2 = max(0, min(size - 1, x2))
        y2 = max(0, min(size - 1, y2))
        cv2.line(image, (x1, y1), (x2, y2), 255, 1)

    skeleton = image.astype(bool)

    # Build ground truth graph by extracting from skeleton
    # (Lines are drawn at single-pixel width so image = skeleton)
    from utils.graph_utils import skeleton_to_graph
    G = skeleton_to_graph(skeleton)

    return image, skeleton, G


# ──────────────────────────────────────────────────────────────────────
# 3. DLA CLUSTER — diffusion-limited aggregation
# ──────────────────────────────────────────────────────────────────────

def generate_dla(size=256, n_particles=2000):
    """
    Generate a Diffusion-Limited Aggregation cluster.

    Parameters
    ----------
    size : int
        Image height/width (DLA grows from center).
    n_particles : int
        Number of particles to aggregate.

    Returns
    -------
    image : np.ndarray (size, size), uint8
        Rendered binary image.
    skeleton : np.ndarray (size, size), bool
        Ground truth skeleton (after thinning).
    G : networkx.Graph
        Ground truth graph.
    """
    from skimage.morphology import skeletonize

    image = np.zeros((size, size), dtype=np.uint8)
    cx, cy = size // 2, size // 2
    image[cy, cx] = 1

    np.random.seed(42)
    for _ in range(n_particles):
        # Launch random walker from boundary
        angle = np.random.uniform(0, 2 * np.pi)
        radius = size // 2 - 5
        x = int(cx + radius * np.cos(angle))
        y = int(cy + radius * np.sin(angle))
        x = max(0, min(size - 1, x))
        y = max(0, min(size - 1, y))

        # Random walk until hitting cluster
        stuck = False
        for _ in range(5000):
            # Check if adjacent to cluster
            y0 = max(0, y - 1)
            y1 = min(size - 1, y + 1)
            x0 = max(0, x - 1)
            x1 = min(size - 1, x + 1)
            if np.any(image[y0:y1+1, x0:x1+1]):
                image[y, x] = 1
                stuck = True
                break

            # Random step
            dx, dy = np.random.choice([-1, 0, 1], size=2)
            if abs(dx) + abs(dy) != 1:
                continue
            x = max(0, min(size - 1, x + dx))
            y = max(0, min(size - 1, y + dy))

        if not stuck:
            continue  # particle escaped, skip

    # Skeletonize the DLA cluster
    skeleton = skeletonize(image.astype(bool), method='zhang-suen')

    # Build graph
    from utils.graph_utils import skeleton_to_graph
    G = skeleton_to_graph(skeleton)

    return image.astype(np.uint8), skeleton, G


# ──────────────────────────────────────────────────────────────────────
# GENERATE ALL AND SAVE
# ──────────────────────────────────────────────────────────────────────

def generate_all(output_dir, sizes=(256, 256)):
    """Generate one of each synthetic pattern and save to output_dir."""
    os.makedirs(output_dir, exist_ok=True)

    print("Generating synthetic tree...")
    img, skel, G = generate_tree(size=sizes[0])
    cv2.imwrite(os.path.join(output_dir, 'synthetic_tree.png'), img)
    np.save(os.path.join(output_dir, 'synthetic_tree_skeleton.npy'), skel)
    with open(os.path.join(output_dir, 'synthetic_tree_graph.gpickle'), 'wb') as f:
        pickle.dump(G, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"  Tree: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    print("Generating synthetic mesh...")
    img, skel, G = generate_mesh(size=sizes[0])
    cv2.imwrite(os.path.join(output_dir, 'synthetic_mesh.png'), img)
    np.save(os.path.join(output_dir, 'synthetic_mesh_skeleton.npy'), skel)
    with open(os.path.join(output_dir, 'synthetic_mesh_graph.gpickle'), 'wb') as f:
        pickle.dump(G, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"  Mesh: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    print("Generating synthetic DLA...")
    img, skel, G = generate_dla(size=sizes[0])
    cv2.imwrite(os.path.join(output_dir, 'synthetic_dla.png'), img)
    np.save(os.path.join(output_dir, 'synthetic_dla_skeleton.npy'), skel)
    with open(os.path.join(output_dir, 'synthetic_dla_graph.gpickle'), 'wb') as f:
        pickle.dump(G, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"  DLA: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    print(f"\nSynthetic data saved to {output_dir}")
    return output_dir


if __name__ == '__main__':
    import sys
    output_dir = sys.argv[1] if len(sys.argv) > 1 else \
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'synthetic')
    os.makedirs(output_dir, exist_ok=True)
    generate_all(output_dir, sizes=(256, 256))
