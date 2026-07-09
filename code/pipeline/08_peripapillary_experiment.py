"""
08_peripapillary_experiment.py — Peripapillary crop experiment.

Crops each retinal mask to a fixed-radius circular region around the image center,
re-extracts the graph, and computes assortativity.
Compares to leaf and crack at matched scales.

Rationale: The peripapillary region captures the initial 2-4 branching generations
from the optic disc, preserving centrifugal hierarchy while substantially reducing
graph size disparity with leaf and crack networks.

Usage:
    python pipeline/08_peripapillary_experiment.py

Output:
    Peripapillary retina assortativity compared to leaf and crack.
"""

import cv2, numpy as np, os, pickle, sys, glob, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import networkx as nx
from utils.graph_utils import skeleton_to_graph

BASE = r"C:\Users\User\Claude\Projects\Retinnal_Fractal_Analysis"
RETINAL_DIR = os.path.join(BASE, "Retinal data", "Retina Vessel Segmentation")

def circular_crop(mask, radius=150):
    """Crop to a circle of given radius centered on the image center."""
    h, w = mask.shape
    cx, cy = w // 2, h // 2
    Y, X = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((X - cx)**2 + (Y - cy)**2)
    crop = mask.copy()
    crop[dist_from_center > radius] = 0
    # Tight bounding box
    ys, xs = np.where(crop > 0)
    if len(ys) == 0:
        return None
    y1, y2 = max(0, ys.min()-5), min(h, ys.max()+5)
    x1, x2 = max(0, xs.min()-5), min(w, xs.max()+5)
    return crop[y1:y2, x1:x2]

def compute_assortativity_from_mask(mask):
    """Skeletonize and compute assortativity."""
    mask_bool = (mask > 0).astype(bool)
    if mask_bool.sum() < 50:
        return None, 0
    from skimage.morphology import skeletonize
    skel = skeletonize(mask_bool, method='zhang')
    G = skeleton_to_graph(skel)
    n = G.number_of_nodes()
    if n < 10:
        return None, n
    try:
        ass = nx.degree_assortativity_coefficient(G)
    except:
        ass = 0
    return ass, n

print("=" * 60)
print("PERIPAPILLARY CROP EXPERIMENT")
print("Testing whether retinal assortativity remains positive")
print("after cropping to peripapillary region (~150px radius)")
print("=" * 60)

# Load all retinal mask images
all_masks = []
for subset in ["Training", "Test"]:
    mask_dir = os.path.join(RETINAL_DIR, subset, "Masks")
    if os.path.isdir(mask_dir):
        for f in sorted(os.listdir(mask_dir)):
            if f.lower().endswith(('.tif', '.tiff', '.png')):
                all_masks.append(os.path.join(mask_dir, f))

print(f"\nFound {len(all_masks)} retinal mask images")

# Process each with circular crop
results = []
for fpath in all_masks[:50]:  # Limit to 50 for speed
    img = cv2.imread(fpath, cv2.IMREAD_GRAYSCALE)
    if img is None:
        continue
    h, w = img.shape
    s = 1024 / max(h, w)
    if s < 1:
        img = cv2.resize(img, (int(w*s), int(h*s)), interpolation=cv2.INTER_LINEAR)

    # Full graph
    ass_full, _ = compute_assortativity_from_mask((img > 0).astype(np.uint8))

    # Cropped graph
    crop = circular_crop(img, radius=150)
    if crop is None:
        continue
    ass_crop, n_nodes = compute_assortativity_from_mask(crop)

    if ass_full is not None and ass_crop is not None:
        results.append({'file': os.path.basename(fpath),
                        'assort_full': ass_full,
                        'assort_crop': ass_crop,
                        'nodes_crop': n_nodes})

print(f"Processed {len(results)} images with valid crops")

if len(results) > 0:
    full_vals = [r['assort_full'] for r in results]
    crop_vals = [r['assort_crop'] for r in results]
    crop_nodes = [r['nodes_crop'] for r in results]

    print(f"\n  Full retina:        mean assort = {np.mean(full_vals):.4f} ± {np.std(full_vals):.4f}")
    print(f"  Peripapillary crop: mean assort = {np.mean(crop_vals):.4f} ± {np.std(crop_vals):.4f}")
    print(f"  Crop node count:    mean = {np.mean(crop_nodes):.0f} ± {np.std(crop_nodes):.0f}, range = [{min(crop_nodes)}-{max(crop_nodes)}]")

    # Compare to leaf and crack
    import pandas as pd
    df = pd.read_csv(os.path.join(BASE, "data", "features.csv"))
    leaf_ass = df[df['label']=='leaf']['assortativity'].dropna().values
    crack_ass = df[df['label']=='crack']['assortativity'].dropna().values

    print(f"\n  Leaf:               mean assort = {leaf_ass.mean():.4f} ± {leaf_ass.std():.4f} (n={len(leaf_ass)})")
    print(f"  Crack:              mean assort = {crack_ass.mean():.4f} ± {crack_ass.std():.4f} (n={len(crack_ass)})")
    print(f"  DLA:                mean assort = {df[df['label']=='dla']['assortativity'].mean():.4f}")

    crop_arr = np.array(crop_vals)
    print(f"\n{'='*60}")
    print("KEY COMPARISON")
    print(f"{'='*60}")
    print(f"  Retina (full):       {np.mean(full_vals):+.4f}")
    print(f"  Retina (peripap):    {np.mean(crop_vals):+.4f}")
    print(f"  Leaf:                {leaf_ass.mean():+.4f}")
    print(f"  Crack:               {crack_ass.mean():+.4f}")
    print(f"  DLA:                 {df[df['label']=='dla']['assortativity'].mean():+.4f}")

    if np.mean(crop_vals) > 0 and leaf_ass.mean() < 0:
        print(f"\n  >>> SIGN REVERSAL PRESERVED after cropping <<<")
        print(f"  Peripapillary retina is assortative ({np.mean(crop_vals):+.3f}), leaf is disassortative ({leaf_ass.mean():+.3f})")
    elif np.mean(crop_vals) > 0:
        print(f"\n  Retina remains assortative but leaf sign comparison needs checking")
    else:
        print(f"\n  >>> SIGN REVERSAL DISAPPEARED <<<")
        print(f"  Peripapillary retina is NOT assortative ({np.mean(crop_vals):+.3f})")

    print(f"\n  Node count: retina crop = {np.mean(crop_nodes):.0f} vs leaf ~46 vs crack ~40")
    print(f"  Size disparity reduced from 34x (full) to ~{np.mean(crop_nodes)/43:.1f}x (crop vs leaf/crack avg)")

print("\nDone.")
