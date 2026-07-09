# Topological Signatures of Network Formation Mechanisms — Pipeline

## Quick Start — Do These Steps in Order

### Step 1: Generate synthetic test data
```bash
cd C:\Users\User\Claude\Projects\Retinnal_Fractal_Analysis\code
python tests\generate_synthetic.py
```
This creates synthetic tree, mesh, and DLA patterns in `data/synthetic/`.

### Step 2: Run synthetic pipeline test
```bash
python tests\run_synthetic_test.py
```
This validates the graph extraction pipeline on known ground truth.  
**All tests should pass before proceeding to real data.**

### Step 3: Dry-run on real data (scan only, no processing)
```bash
python pipeline\01_extract_graphs.py --dry-run
```
This scans your retinal and crack datasets and reports how many samples will be processed.

### Step 4: Process all images
```bash
python pipeline\01_extract_graphs.py
```
This extracts graphs from all retinal and crack images. QC overlays are saved to `results/figures/qc/`.

### Step 5: Quick quality check
Open `results/figures/qc/` and inspect a few overlay images.  
The graph (orange lines) should follow the vessel/crack paths accurately.  
Junctions are red circles, endpoints are blue squares.

---

## Pipeline Modules

| Module | File | Purpose |
|--------|------|---------|
| Graph extraction | `utils/graph_utils.py` | Skeletonize → detect junctions → trace edges → build graph |
| Visualization | `utils/viz_utils.py` | Overlays, degree distributions, persistence diagrams, phase space |
| Extract graphs | `pipeline/01_extract_graphs.py` | Run full extraction on both datasets |
| Synthetic data | `tests/generate_synthetic.py` | Generate known-topology test patterns |
| Pipeline test | `tests/run_synthetic_test.py` | Validate pipeline on synthetic data |

---

## Expected Processing Time

| Step | Time |
|------|------|
| Synthetic data generation | ~10 seconds |
| Pipeline tests | ~30 seconds |
| Dry run | ~5 seconds |
| Full extraction (93 retinal + 118 crack) | ~5-15 minutes |

---

## Directory Structure After Pipeline

```
Retinnal_Fractal_Analysis/
├── data/
│   ├── retinal/
│   │   └── graphs/        ← .gpickle files for retinal images
│   ├── crack/
│   │   └── graphs/         ← .gpickle files for crack images
│   └── synthetic/          ← synthetic test patterns
├── results/
│   └── figures/
│       └── qc/             ← quality control overlay images
├── code/
│   ├── pipeline/
│   ├── utils/
│   └── tests/
└── notebooks/              ← coming soon
```

---

## Troubleshooting

**"Could not load mask"** — Check that the mask file path exists. Some Kaggle datasets use different folder structures.

**Empty graph** — The mask may be all-black (no vessels/cracks in this image). This is normal for some samples.

**Very small graph** — Try different skeletonization method by editing `SKELETON_METHOD = 'thin'` in `01_extract_graphs.py`.

**Import errors** — Run from the `code/` directory. Ensure all packages are installed (`pip install -r requirements.txt`).
