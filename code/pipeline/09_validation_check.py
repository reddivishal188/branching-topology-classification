"""
09_validation_check.py — Quick manual graph extraction validation.

Generates side-by-side comparison images for 5 random samples per system.
You look at each and check whether the graph accurately follows the structure.

Usage:
    python pipeline/09_validation_check.py

Output:
    results/validation/validation_*.png
"""

import cv2, numpy as np, os, sys, pickle, glob, random, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from utils.graph_utils import skeleton_to_graph, skeletonize_mask

BASE = r"C:\Users\User\Claude\Projects\Retinnal_Fractal_Analysis"
OUT = os.path.join(BASE, "results", "validation")
os.makedirs(OUT, exist_ok=True)

COLORS = {'retinal': '#E74C3C', 'leaf': '#27AE60', 'crack': '#2C3E50', 'dla': '#8E44AD'}

def make_validation_image(original_img, skeleton, G, title, savepath):
    """Create a side-by-side: original | skeleton | graph overlay."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    axes[0].imshow(original_img, cmap='gray')
    axes[0].set_title('Original')
    axes[0].axis('off')

    axes[1].imshow(skeleton, cmap='gray')
    axes[1].set_title(f'Skeleton ({skeleton.sum()} px)')
    axes[1].axis('off')

    axes[2].imshow(original_img, cmap='gray', alpha=0.5)
    # Draw edges
    for u, v, data in G.edges(data=True):
        path = data.get('path', [])
        if path:
            path = np.array(path)
            axes[2].plot(path[:,1], path[:,0], '-', color=COLORS.get('retinal','orange'),
                        linewidth=0.5, alpha=0.8)
    # Draw nodes
    for n, data in G.nodes(data=True):
        y, x = data.get('pos', n)
        ntype = data.get('type', '')
        if ntype == 'junction':
            axes[2].plot(x, y, 'o', color='red', markersize=3)
        elif ntype == 'endpoint':
            axes[2].plot(x, y, 's', color='blue', markersize=2)
    axes[2].set_title(f'Graph ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)')
    axes[2].axis('off')

    plt.suptitle(title, fontsize=12)
    plt.tight_layout()
    fig.savefig(savepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {savepath}")

print("=" * 60)
print("GRAPH EXTRACTION VALIDATION")
print("Generating 5 validation images for manual inspection")
print("=" * 60)

# --- Retina ---
ret_mask_dir = os.path.join(BASE, "Retinal data", "Retina Vessel Segmentation", "Training", "Masks")
ret_masks = sorted(glob.glob(os.path.join(ret_mask_dir, "*.tif")))[:5]
print(f"\nRetina: {len(ret_masks)} images")
for i, f in enumerate(ret_masks):
    img = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
    if img is None: continue
    h, w = img.shape
    s = 1024 / max(h, w)
    if s < 1:
        img = cv2.resize(img, (int(w*s), int(h*s)), interpolation=cv2.INTER_LINEAR)
    mask = (img > 0).astype(bool)
    if mask.sum() < 100: continue
    skel = skeletonize_mask(mask, method='zhang')
    G = skeleton_to_graph(skel)
    fname = f"validation_retina_{i+1}.png"
    make_validation_image(mask.astype(np.uint8)*255, skel.astype(np.uint8)*255, G,
                         f"Retina sample {i+1}", os.path.join(OUT, fname))

# --- Leaf ---
leaf_dir = os.path.join(BASE, "data", "leaf", "images")
leaf_masks = sorted(glob.glob(os.path.join(leaf_dir, "*_mask.png")))[:5]
print(f"\nLeaf: {len(leaf_masks)} images")
for i, f in enumerate(leaf_masks):
    img = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
    if img is None: continue
    mask = (img > 0).astype(bool)
    if mask.sum() < 100: continue
    skel = skeletonize_mask(mask, method='zhang')
    G = skeleton_to_graph(skel)
    fname = f"validation_leaf_{i+1}.png"
    make_validation_image(mask.astype(np.uint8)*255, skel.astype(np.uint8)*255, G,
                         f"Leaf sample {i+1}", os.path.join(OUT, fname))

# --- Crack ---
crack_dir = os.path.join(BASE, "data", "crack", "images")
crack_files = sorted(glob.glob(os.path.join(crack_dir, "*")))[:5]
print(f"\nCrack: {len(crack_files)} images")
for i, f in enumerate(crack_files):
    img = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
    if img is None: continue
    mask = (img > 0).astype(bool)
    if mask.sum() < 100: continue
    skel = skeletonize_mask(mask, method='zhang')
    G = skeleton_to_graph(skel)
    fname = f"validation_crack_{i+1}.png"
    make_validation_image(mask.astype(np.uint8)*255, skel.astype(np.uint8)*255, G,
                         f"Crack sample {i+1}", os.path.join(OUT, fname))

# --- DLA ---
dla_dir = os.path.join(BASE, "data", "dla", "images")
dla_files = sorted(glob.glob(os.path.join(dla_dir, "*.png")))[:5]
print(f"\nDLA: {len(dla_files)} images")
for i, f in enumerate(dla_files):
    img = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
    if img is None: continue
    mask = (img > 0).astype(bool)
    if mask.sum() < 100: continue
    skel = skeletonize_mask(mask, method='zhang')
    G = skeleton_to_graph(skel)
    fname = f"validation_dla_{i+1}.png"
    make_validation_image(mask.astype(np.uint8)*255, skel.astype(np.uint8)*255, G,
                         f"DLA sample {i+1}", os.path.join(OUT, fname))

print(f"\nAll validation images in: {OUT}")
print("Open each one and check: does the graph follow the structure correctly?")
