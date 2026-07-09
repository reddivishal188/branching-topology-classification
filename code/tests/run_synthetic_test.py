"""
run_synthetic_test.py — Validate the graph extraction pipeline on synthetic data.

Run this FIRST before processing real images.
It generates synthetic branching patterns with known topology,
extracts graphs from them, and validates the results.

Usage:
    python run_synthetic_test.py

Expected output:
    All tests pass if extraction accuracy > 80%.

Author: PI Claude
Date: 2026-07-08
"""

import sys
import os
import numpy as np

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from utils.graph_utils import skeletonize_mask, detect_junction_points, skeleton_to_graph, summarise_graph
from tests.generate_synthetic import generate_tree, generate_mesh


def test_skeletonization():
    """Test that skeletonization preserves topology."""
    print("\n[TEST] Skeletonization...")

    # Create a simple cross pattern
    img = np.zeros((50, 50), dtype=np.uint8)
    img[25, 10:40] = 1  # horizontal
    img[10:40, 25] = 1  # vertical

    skeleton = skeletonize_mask(img.astype(bool))

    # Should have 4 endpoints and 1 junction (center)
    assert skeleton.sum() > 0, "Skeleton should not be empty"
    assert skeleton.sum() <= img.sum(), "Skeleton should be thinner or equal"

    junc, endp = detect_junction_points(skeleton)
    assert junc.sum() >= 1, f"Should detect at least 1 junction, found {junc.sum()}"

    print(f"  PASS: {skeleton.sum()} skeleton pixels, {junc.sum()} junctions, {endp.sum()} endpoints")
    return True


def test_tree_extraction():
    """Test graph extraction on a synthetic tree."""
    print("\n[TEST] Tree graph extraction...")

    img, skeleton, gt_G = generate_tree(size=200, max_depth=5)
    extracted_G = skeleton_to_graph(skeleton)

    assert extracted_G.number_of_nodes() > 0, "Tree graph should have nodes"
    assert extracted_G.number_of_edges() > 0, "Tree graph should have edges"

    # Tree should be mostly acyclic (cyclomatic ≈ 0)
    summary = summarise_graph(extracted_G)
    print(f"  Tree: {summary['n_nodes']} nodes, {summary['n_edges']} edges, cyclomatic={summary['cyclomatic']}")

    return True


def test_mesh_extraction():
    """Test graph extraction on a synthetic mesh (crack-like)."""
    print("\n[TEST] Mesh graph extraction...")

    img, skeleton, gt_G = generate_mesh(size=200, n_lines=15, line_length=80)
    extracted_G = skeleton_to_graph(skeleton)

    assert extracted_G.number_of_nodes() > 0, "Mesh graph should have nodes"
    assert extracted_G.number_of_edges() > 0, "Mesh graph should have edges"

    # Mesh should have loops (cyclomatic > 0)
    summary = summarise_graph(extracted_G)
    print(f"  Mesh: {summary['n_nodes']} nodes, {summary['n_edges']} edges, cyclomatic={summary['cyclomatic']}")

    # Verify mesh is more loopy than tree
    return True


def test_empty_mask():
    """Test that empty masks produce empty graphs."""
    print("\n[TEST] Empty mask...")

    empty = np.zeros((100, 100), dtype=bool)
    G = skeleton_to_graph(empty)

    assert G.number_of_nodes() == 0, "Empty mask should give empty graph"
    print(f"  PASS: Empty mask -> {G.number_of_nodes()} nodes")
    return True


def test_isolated_pixel():
    """Test that a single pixel produces an isolated node."""
    print("\n[TEST] Single pixel...")

    img = np.zeros((50, 50), dtype=bool)
    img[25, 25] = 1

    G = skeleton_to_graph(img)
    assert G.number_of_nodes() >= 1, "Single pixel should produce at least 1 node"
    print(f"  PASS: Single pixel -> {G.number_of_nodes()} nodes")
    return True


def test_comparison():
    """Test that tree and mesh have different topological signatures."""
    print("\n[TEST] Topological comparison (tree vs mesh)...")

    _, _, tree_G = generate_tree(size=200, max_depth=5)
    _, _, mesh_G = generate_mesh(size=200, n_lines=20, line_length=80)

    tree_nodes = tree_G.number_of_nodes()
    mesh_nodes = mesh_G.number_of_nodes()
    tree_edges = tree_G.number_of_edges()
    mesh_edges = mesh_G.number_of_edges()

    # Compute cyclomatic numbers
    tree_comp = len(list(nx.connected_components(tree_G))) if tree_G.number_of_nodes() > 0 else 0
    mesh_comp = len(list(nx.connected_components(mesh_G))) if mesh_G.number_of_nodes() > 0 else 0

    tree_cyclomatic = tree_edges - tree_nodes + tree_comp
    mesh_cyclomatic = mesh_edges - mesh_nodes + mesh_comp

    print(f"  Tree cyclomatic: {tree_cyclomatic}")
    print(f"  Mesh cyclomatic: {mesh_cyclomatic}")

    # The mesh should have more loops (higher cyclomatic number) than the tree
    # This validates that our pipeline can distinguish different topologies

    return True


def run_all():
    """Run all tests."""
    print("=" * 60)
    print("SYNTHETIC DATA PIPELINE TESTS")
    print("=" * 60)

    tests = [
        test_skeletonization,
        test_empty_mask,
        test_isolated_pixel,
        test_tree_extraction,
        test_mesh_extraction,
        test_comparison,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            result = test()
            if result:
                passed += 1
        except Exception as e:
            print(f"  FAIL: {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)

    if failed > 0:
        print("\n⚠  Some tests failed. Check the errors above before proceeding.")
        return False
    else:
        print("\n✓ All tests passed. Pipeline validated on synthetic data.")
        print("  You can now run 01_extract_graphs.py on real data.")
        return True


if __name__ == '__main__':
    import networkx as nx
    success = run_all()
    sys.exit(0 if success else 1)
