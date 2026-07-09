"""
00_prepare_leaf.py — Convert CHAMBASA TRACED masks to binary and organize.

The CHAMBASA TRACED masks are RGB images where:
- Red pixels (R > 100) = veins
- White/Black pixels = background

This script converts them to standard binary masks (0/255)
and organizes them for the extraction pipeline.

CHAMBASA raw files location: C:\Fractal Research\LEAF\
Output location: data\leaf\images\ and data\leaf\graphs\

Usage:
    python 00_prepare_leaf.py
"""

import cv2
import numpy as np
import os
import sys
import glob

BASE_DIR = r"C:\Users\User\Claude\Projects\Retinnal_Fractal_Analysis"
RAW_DIR = r"C:\Fractal Research\LEAF"
OUTPUT_IMAGES = os.path.join(BASE_DIR, "data", "leaf", "images")
OUTPUT_GRAPHS = os.path.join(BASE_DIR, "data", "leaf", "graphs")
os.makedirs(OUTPUT_IMAGES, exist_ok=True)
os.makedirs(OUTPUT_GRAPHS, exist_ok=True)

print("Converting CHAMBASA masks to binary format...")
traced_files = sorted(glob.glob(os.path.join(RAW_DIR, "*TRACED*")))

converted = 0
errors = 0
for t in traced_files:
    try:
        img = cv2.imread(t, cv2.IMREAD_COLOR)
        if img is None:
            errors += 1
            continue
        # Extract red channel as vein mask (R > 100 captures red veins)
        vein_mask = (img[:,:,2] > 100).astype(np.uint8) * 255
        # Save as PNG
        base = os.path.basename(t).replace("_TRACED.png", "")
        out_path = os.path.join(OUTPUT_IMAGES, f"{base}_mask.png")
        cv2.imwrite(out_path, vein_mask)
        converted += 1
    except Exception as e:
        print(f"  Error: {t}: {e}")
        errors += 1

print(f"Converted {converted} masks, {errors} errors")
print(f"Binary masks saved to: {OUTPUT_IMAGES}")
print(f"\nNext step: python pipeline\\01_extract_graphs.py")
