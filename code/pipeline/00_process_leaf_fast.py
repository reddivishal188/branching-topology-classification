"""Fast leaf graph extraction — 512px resize, skips sparse masks."""
import cv2, numpy as np, os, pickle, sys, glob, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from utils.graph_utils import skeleton_to_graph
from skimage.morphology import skeletonize

SRC = r"C:\Users\User\Claude\Projects\Retinnal_Fractal_Analysis\data\leaf\images"
DST = r"C:\Users\User\Claude\Projects\Retinnal_Fractal_Analysis\data\leaf\graphs"
os.makedirs(DST, exist_ok=True)

files = sorted(glob.glob(os.path.join(SRC, "*_mask.png")))[:120]  # 120 is enough for stats
t0 = time.time()
ok = skip = 0

for i, f in enumerate(files):
    m = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
    if m is None: continue
    h, w = m.shape
    # Aggressive resize to 512px max
    s = 512 / max(h, w)
    if s < 1:
        m = cv2.resize(m, (int(w * s), int(h * s)), interpolation=cv2.INTER_NEAREST)
    m = (m > 0).astype(bool)
    if m.sum() < 50:
        skip += 1
        continue
    sk = skeletonize(m, method="zhang")
    G = skeleton_to_graph(sk)
    nm = os.path.splitext(os.path.basename(f))[0].replace("_mask", "")
    with open(os.path.join(DST, f"leaf_{nm}.gpickle"), "wb") as fp:
        pickle.dump(G, fp)
    ok += 1
    if (i + 1) % 100 == 0:
        print(f"[{i+1}/{len(files)}] ok={ok} skip={skip} time={time.time()-t0:.0f}s")

print(f"\nDONE: {ok} graphs in {time.time()-t0:.0f}s ({skip} sparse skipped)")
