"""
01_extract_graphs.py — Extract graphs from retinal and crack binary masks.

Pipeline:
1. Load ground truth segmentation masks
2. Skeletonize to single-pixel width
3. Detect junction and endpoint nodes
4. Trace and link edge segments between nodes
5. Build NetworkX graph objects
6. Save graphs as gpickle for downstream analysis
7. Generate quality control plots

Usage:
    python 01_extract_graphs.py

Output:
    data/retinal/graphs/     — Retinal graph objects (.gpickle)
    data/crack/graphs/       — Crack graph objects (.gpickle)
    results/figures/qc/      — Quality control overlays (PNG)

Author: PI Claude
Date: 2026-07-08
"""

import numpy as np
import networkx as nx
import cv2
import os
import sys
import pickle
import argparse
from datetime import datetime
import warnings
import glob
from skimage.filters import threshold_otsu

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from utils.graph_utils import skeletonize_mask, detect_junction_points, skeleton_to_graph, summarise_graph


# ──────────────────────────────────────────────────────────────────────
# CONFIGURATION — EDIT THESE PATHS TO MATCH YOUR SYSTEM
# ──────────────────────────────────────────────────────────────────────

# Base path: change this to your actual project folder
BASE_DIR = r"C:\Users\User\Claude\Projects\Retinnal_Fractal_Analysis"

# Retinal dataset paths
RETINAL_DIR = os.path.join(BASE_DIR, "Retinal data", "Retina Vessel Segmentation")

# Crack dataset (TLCrack) paths — dense, interconnected crack networks
# Downloaded from https://zenodo.org/records/17033872
CRACK_DIR = r"C:\Fractal Research\Concrete Cracks\TLCrack"

# Output paths
OUTPUT_DIR = os.path.join(BASE_DIR, "data")
RETINAL_GRAPH_DIR = os.path.join(OUTPUT_DIR, "retinal", "graphs")
CRACK_GRAPH_DIR = os.path.join(OUTPUT_DIR, "crack", "graphs")
LEAF_GRAPH_DIR = os.path.join(OUTPUT_DIR, "leaf", "graphs")
QC_DIR = os.path.join(BASE_DIR, "results", "figures", "qc")

# Parameters
SKELETON_METHOD = 'zhang'               # 'zhang', 'lee', or 'thin'
MAX_IMAGE_SIZE = 1024                 # Balance speed and topological detail


# ──────────────────────────────────────────────────────────────────────
# RETINAL DATA LOADING
# ──────────────────────────────────────────────────────────────────────

def load_retinal_data():
    """
    Load retinal images and their ground truth vessel masks.

    The Kaggle combined dataset has structure:
        Training/Images/   — training fundus images (JPG)
        Training/Masks/    — training vessel masks (TIF)
        Test/Images/       — test fundus images (JPG)
        Test/Masks/        — test vessel masks (TIF)

    Returns
    -------
    samples : list of dict
        Each dict: {'image_path': str, 'mask_path': str, 'name': str}
    """
    samples = []

    # Training set
    train_img_dir = os.path.join(RETINAL_DIR, "Training", "Images")
    train_mask_dir = os.path.join(RETINAL_DIR, "Training", "Masks")
    if os.path.isdir(train_img_dir) and os.path.isdir(train_mask_dir):
        _match_samples(train_img_dir, train_mask_dir, samples, prefix='Training')

    # Test set
    test_img_dir = os.path.join(RETINAL_DIR, "Test", "Images")
    test_mask_dir = os.path.join(RETINAL_DIR, "Test", "Masks")
    if os.path.isdir(test_img_dir) and os.path.isdir(test_mask_dir):
        _match_samples(test_img_dir, test_mask_dir, samples, prefix='Test')

    return samples


def _match_samples(img_dir, mask_dir, samples, prefix=''):
    """Match images with their corresponding masks by filename."""
    # Get image files
    img_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff')
    img_files = sorted([f for f in os.listdir(img_dir)
                       if f.lower().endswith(img_extensions)])

    # Get mask files
    mask_extensions = ('.tif', '.tiff', '.png', '.jpg', '.jpeg', '.bmp')
    mask_files = sorted([f for f in os.listdir(mask_dir)
                        if f.lower().endswith(mask_extensions)])

    # Match by filename stem (ignoring extensions)
    img_stems = {}
    for f in img_files:
        stem = os.path.splitext(f)[0]
        img_stems[stem] = f

    mask_stems = {}
    for f in mask_files:
        stem = os.path.splitext(f)[0]
        mask_stems[stem] = f

    matched = 0
    for stem, img_name in img_stems.items():
        if stem in mask_stems:
            samples.append({
                'image_path': os.path.join(img_dir, img_name),
                'mask_path': os.path.join(mask_dir, mask_stems[stem]),
                'name': f"{prefix}_{stem}"
            })
            matched += 1

    print(f"  {prefix}: matched {matched} image-mask pairs")
    return matched


# ──────────────────────────────────────────────────────────────────────
# CRACK DATA LOADING (TLCrack)
# ──────────────────────────────────────────────────────────────────────

def load_crack_data():
    """
    Load TLCrack images and ground truth binary masks.

    TLCrack structure:
        images/       — RGB crack images (PNG)
        annotations/  — binary masks (PNG, 0=background, 255=crack)

    These are dense, interconnected crack networks with rich topology.
    """
    samples = []

    img_dir = os.path.join(CRACK_DIR, "images")
    mask_dir = os.path.join(CRACK_DIR, "annotations")

    if not os.path.isdir(img_dir):
        print(f"  WARNING: TLCrack image directory not found: {img_dir}")
        return samples
    if not os.path.isdir(mask_dir):
        print(f"  WARNING: TLCrack annotation directory not found: {mask_dir}")
        return samples

    # List all PNG files in images
    all_images = sorted([f for f in os.listdir(img_dir) if f.lower().endswith('.png')])
    matched = 0

    for img_name in all_images:
        mask_path = os.path.join(mask_dir, img_name)
        if os.path.isfile(mask_path):
            samples.append({
                'image_path': os.path.join(img_dir, img_name),
                'mask_path': mask_path,
                'name': f"TLCrack_{os.path.splitext(img_name)[0]}",
            })
            matched += 1

    print(f"  TLCrack: matched {matched} image-mask pairs")
    return samples


# ──────────────────────────────────────────────────────────────────────
# LEAF DATA LOADING (CHAMBASA)
# ──────────────────────────────────────────────────────────────────────

def load_leaf_data():
    """
    Load CHAMBASA leaf images and pre-converted binary vein masks.

    Raw files are at C:\Fractal Research\LEAF\*TRACED.png (RGB masks).
    Binary conversions are at data/leaf/images/*_mask.png (binary grayscale).

    This loader reads from data/leaf/images/ where 00_prepare_leaf.py
    saved the converted binary masks.
    """
    samples = []
    leaf_dir = os.path.join(BASE_DIR, "data", "leaf", "images")

    if not os.path.isdir(leaf_dir):
        print(f"  WARNING: Leaf image directory not found: {leaf_dir}")
        print(f"  Run 00_prepare_leaf.py first to convert CHAMBASA masks.")
        return samples

    mask_files = sorted([f for f in os.listdir(leaf_dir) if f.lower().endswith('_mask.png')])
    matched = 0

    for mask_name in mask_files:
        mask_path = os.path.join(leaf_dir, mask_name)
        samples.append({
            'image_path': mask_path,  # no original image needed; mask is sufficient
            'mask_path': mask_path,
            'name': f"Leaf_{os.path.splitext(mask_name)[0].replace('_mask', '')}",
        })
        matched += 1

    print(f"  Leaf (CHAMBASA): matched {matched} binary masks")
    return samples


# ──────────────────────────────────────────────────────────────────────
# MASK LOADING FROM .MAT FILES
# ──────────────────────────────────────────────────────────────────────

def load_mat_mask(mat_path):
    """
    Load a crack segmentation mask from a .mat file.

    CrackForest .mat files have structure:
        data['groundTruth'] -> shape (1,1), dtype ['Segmentation', 'Boundaries']
        data['groundTruth'][0,0]['Segmentation'] -> 2D uint8 array
        Values are 1 (background) and 2 (crack)

    Falls back to any 2D numeric array if this pattern fails.
    """
    import scipy.io
    try:
        data = scipy.io.loadmat(mat_path)

        # Extract 2D segmentation array
        seg = None

        # CASE 1: CrackForest struct format
        if 'groundTruth' in data:
            gt = data['groundTruth']
            if hasattr(gt, 'dtype') and gt.dtype is not None and gt.dtype.names is not None:
                if 'Segmentation' in gt.dtype.names:
                    seg = gt[0, 0]['Segmentation']
                elif 'segmentation' in gt.dtype.names:
                    seg = gt[0, 0]['segmentation']

        # CASE 2: Direct variable name
        if seg is None:
            for key in ['groundTruth', 'GT', 'gt', 'mask', 'Segmentation']:
                if key in data:
                    candidate = data[key]
                    if hasattr(candidate, 'shape') and len(candidate.shape) == 2:
                        seg = candidate
                        break

        # CASE 3: Any 2D non-metadata array
        if seg is None:
            for key in data:
                if not key.startswith('__') and hasattr(data[key], 'shape') and len(data[key].shape) == 2:
                    seg = data[key]
                    break

        if seg is None:
            print(f"    WARNING: Could not extract 2D mask from {mat_path}")
            return None

        # Convert to binary: if only two unique values, the crack is the smaller count
        # If values are 1 and 2, crack = 2. If 0 and 1, crack = 1.
        unique_vals = np.unique(seg)
        if len(unique_vals) <= 2:
            # Assume the larger value is foreground
            foreground_val = unique_vals.max()
            return (seg == foreground_val).astype(np.uint8) * 255
        else:
            # Multiple values — use Otsu threshold
            from skimage.filters import threshold_otsu
            thresh = threshold_otsu(seg)
            return (seg > thresh).astype(np.uint8) * 255

    except Exception as e:
        print(f"    ERROR loading {mat_path}: {e}")
        return None


# ──────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ──────────────────────────────────────────────────────────────────────

def resize_if_needed(image, max_size=MAX_IMAGE_SIZE):
    """Resize image if both dimensions exceed max_size, preserving aspect ratio."""
    h, w = image.shape[:2]
    if max(h, w) > max_size:
        scale = max_size / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        if image.ndim == 2:
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
        else:
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        print(f"    Resized: {w}x{h} -> {new_w}x{new_h}")
    return image


def process_mask(mask, name, output_dir, save_qc=False, qc_dir=None, original_img=None):
    """
    Process a single binary mask through the full pipeline.

    1. Skeletonize
    2. Graph extraction
    3. Save graph and summary
    """
    # Ensure binary
    if mask.dtype != bool:
        mask = mask > 0

    # Skeletonize
    try:
        skeleton = skeletonize_mask(mask, method=SKELETON_METHOD)
    except Exception as e:
        print(f"    ERROR skeletonizing {name}: {e}")
        return None

    skeleton_pixels = skeleton.sum()
    if skeleton_pixels == 0:
        print(f"    WARNING: Empty skeleton for {name}")
        return None

    # Extract graph
    try:
        G = skeleton_to_graph(skeleton)
    except Exception as e:
        print(f"    ERROR extracting graph for {name}: {e}")
        import traceback
        traceback.print_exc()
        return None

    # Save graph
    import pickle
    graph_path = os.path.join(output_dir, f"{name}.gpickle")
    with open(graph_path, 'wb') as f:
        pickle.dump(G, f, protocol=pickle.HIGHEST_PROTOCOL)

    # Summary
    summary = summarise_graph(G)

    # Quality control overlay
    if save_qc and qc_dir:
        try:
            from utils.viz_utils import plot_graph_overlay
            import matplotlib.pyplot as plt

            fig, axes = plt.subplots(1, 3, figsize=(15, 5))

            # Original mask
            axes[0].imshow(mask, cmap='gray')
            axes[0].set_title(f'Original Mask ({mask.shape[0]}x{mask.shape[1]})')
            axes[0].axis('off')

            # Skeleton
            axes[1].imshow(skeleton, cmap='gray')
            axes[1].set_title(f'Skeleton ({skeleton_pixels} px)')
            axes[1].axis('off')

            # Graph overlay
            plot_graph_overlay(original_img if original_img is not None else mask,
                             skeleton, G, ax=axes[2],
                             title=f'Graph ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)')

            plt.tight_layout()
            qc_path = os.path.join(qc_dir, f"qc_{name}.png")
            fig.savefig(qc_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
        except Exception as e:
            print(f"    WARNING: QC plot failed for {name}: {e}")

    return G


def run_pipeline(dry_run=False, max_samples=None):
    """
    Run the full graph extraction pipeline.

    Parameters
    ----------
    dry_run : bool
        If True, only scan and report what will be processed.
    max_samples : int or None
        Limit number of samples per class (for testing).
    """
    print("=" * 60)
    print(f"GRAPH EXTRACTION PIPELINE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Skeleton method: {SKELETON_METHOD}")
    print("=" * 60)

    # Create output directories
    os.makedirs(RETINAL_GRAPH_DIR, exist_ok=True)
    os.makedirs(CRACK_GRAPH_DIR, exist_ok=True)
    if qc_dir:
        os.makedirs(qc_dir, exist_ok=True)

    # ── Load data ──
    print("\n[1/4] Loading retinal data...")
    retinal_samples = load_retinal_data()
    if max_samples:
        retinal_samples = retinal_samples[:max_samples]

    print(f"\n[2/4] Loading crack data...")
    crack_samples = load_crack_data()
    if max_samples:
        crack_samples = crack_samples[:max_samples]

    leaf_samples = load_leaf_data()
    if max_samples:
        leaf_samples = leaf_samples[:max_samples]

    total_samples = len(retinal_samples) + len(crack_samples) + len(leaf_samples)
    print(f"\n  Total samples: {total_samples}")
    print(f"    Retinal: {len(retinal_samples)}")
    print(f"    Cracks:  {len(crack_samples)}")
    print(f"    Leaf:    {len(leaf_samples)}")

    if dry_run:
        print("\nDry run complete. Set dry_run=False to process.")
        return

    # ── Process retinal ──
    print(f"\n[3/4] Processing retinal graphs...")
    retinal_graphs = []
    for i, sample in enumerate(retinal_samples):
        print(f"  [{i+1}/{len(retinal_samples)}] {sample['name']}")

        # Load image
        img = cv2.imread(sample['image_path'])
        if img is None:
            print(f"    WARNING: Could not load image: {sample['image_path']}")
            continue

        # Load mask
        mask = cv2.imread(sample['mask_path'], cv2.IMREAD_GRAYSCALE)
        if mask is None:
            print(f"    WARNING: Could not load mask: {sample['mask_path']}")
            continue

        # Resize if needed
        img = resize_if_needed(img)
        mask = resize_if_needed(mask)

        # Convert image to RGB for QC display
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if img.ndim == 3 else img

        # Process
        G = process_mask(mask, f"retinal_{sample['name']}",
                        RETINAL_GRAPH_DIR, save_qc=bool(qc_dir), qc_dir=qc_dir,
                        original_img=img_rgb)
        if G is not None:
            retinal_graphs.append(G)

    # ── Process cracks ──
    print(f"\n[4/4] Processing crack graphs...")
    crack_graphs = []
    for i, sample in enumerate(crack_samples):
        print(f"  [{i+1}/{len(crack_samples)}] {sample['name']}")

        # Load image
        img = cv2.imread(sample['image_path'])
        if img is None:
            print(f"    WARNING: Could not load image: {sample['image_path']}")
            continue

        # Load mask
        mask = None
        if sample.get('mask_format') == 'mat':
            mask = load_mat_mask(sample['mask_path'])
        else:
            mask = cv2.imread(sample['mask_path'], cv2.IMREAD_GRAYSCALE)

        if mask is None:
            print(f"    WARNING: Could not load mask: {sample['mask_path']}")
            continue

        # Convert to binary
        mask = (mask > 0).astype(np.uint8) * 255

        # Resize if needed
        img = resize_if_needed(img)
        mask = resize_if_needed(mask)

        # Convert image for QC
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if img.ndim == 3 else img

        # Process
        G = process_mask(mask, f"crack_{sample['name']}",
                        CRACK_GRAPH_DIR, save_qc=bool(qc_dir), qc_dir=qc_dir,
                        original_img=img_rgb)
        if G is not None:
            crack_graphs.append(G)

    # ── Process leaf ──
    print(f"\n[5/5] Processing leaf graphs...")
    os.makedirs(LEAF_GRAPH_DIR, exist_ok=True)
    leaf_graphs = []
    for i, sample in enumerate(leaf_samples):
        print(f"  [{i+1}/{len(leaf_samples)}] {sample['name']}")

        # Load mask
        mask = cv2.imread(sample['mask_path'], cv2.IMREAD_GRAYSCALE)
        if mask is None:
            print(f"    WARNING: Could not load: {sample['mask_path']}")
            continue

        mask = (mask > 0).astype(np.uint8) * 255

        # Process
        G = process_mask(mask, f"leaf_{sample['name']}",
                        LEAF_GRAPH_DIR, save_qc=bool(qc_dir), qc_dir=qc_dir)
        if G is not None:
            leaf_graphs.append(G)

    # ── Final summary ──
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"\nRetinal graphs: {len(retinal_graphs)} extracted")
    if retinal_graphs:
        nodes = [G.number_of_nodes() for G in retinal_graphs]
        edges = [G.number_of_edges() for G in retinal_graphs]
        print(f"  Nodes: {np.mean(nodes):.0f} ± {np.std(nodes):.0f}")
        print(f"  Edges: {np.mean(edges):.0f} ± {np.std(edges):.0f}")

    print(f"\nCrack graphs: {len(crack_graphs)} extracted")
    if crack_graphs:
        nodes = [G.number_of_nodes() for G in crack_graphs]
        edges = [G.number_of_edges() for G in crack_graphs]
        print(f"  Nodes: {np.mean(nodes):.0f} ± {np.std(nodes):.0f}")
        print(f"  Edges: {np.mean(edges):.0f} ± {np.std(edges):.0f}")

    print(f"\nLeaf graphs: {len(leaf_graphs)} extracted")
    if leaf_graphs:
        nodes = [G.number_of_nodes() for G in leaf_graphs]
        edges = [G.number_of_edges() for G in leaf_graphs]
        print(f"  Nodes: {np.mean(nodes):.0f} ± {np.std(nodes):.0f}")
        print(f"  Edges: {np.mean(edges):.0f} ± {np.std(edges):.0f}")

    print(f"\nGraphs saved to:")
    print(f"  Retinal: {RETINAL_GRAPH_DIR}")
    print(f"  Cracks:  {CRACK_GRAPH_DIR}")
    print(f"  Leaf:    {LEAF_GRAPH_DIR}")
    print(f"QC images: {qc_dir}")
    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract graphs from binary masks')
    parser.add_argument('--dry-run', action='store_true',
                       help='Scan files without processing')
    parser.add_argument('--max-samples', type=int, default=None,
                       help='Limit number of samples per class')
    parser.add_argument('--no-qc', action='store_true',
                       help='Skip quality control plots')
    args = parser.parse_args()

    # Update QC config
    qc_dir = QC_DIR
    if args.no_qc:
        qc_dir = ''

    run_pipeline(dry_run=args.dry_run, max_samples=args.max_samples)
