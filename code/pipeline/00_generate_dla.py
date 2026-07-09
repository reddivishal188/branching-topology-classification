"""Fast DLA generator for branching network analysis."""
import numpy as np, cv2, os, pickle, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.graph_utils import skeleton_to_graph
from skimage.morphology import skeletonize

BASE = r"C:\Users\User\Claude\Projects\Retinnal_Fractal_Analysis\data\dla"
os.makedirs(BASE + "/images", exist_ok=True)
os.makedirs(BASE + "/graphs", exist_ok=True)

for i in range(200):
    start = time.time()
    S = 128
    img = np.zeros((S, S), dtype=np.uint8)
    cx, cy = S//2, S//2
    img[cy, cx] = 1
    rng = np.random.RandomState(100 + i)
    agg = 0
    max_r = 1

    for n in range(3000):
        a = rng.uniform(0, 2*np.pi)
        r = max_r + 2
        x = int(cx + r * np.cos(a))
        y = int(cy + r * np.sin(a))
        if x < 1 or x >= S-1 or y < 1 or y >= S-1:
            continue

        for _ in range(2000):
            if img[y-1, x] or img[y+1, x] or img[y, x-1] or img[y, x+1]:
                img[y, x] = 1
                agg += 1
                dy = y - cy
                dx = x - cx
                mr = dx*dx + dy*dy
                if mr > max_r*max_r:
                    max_r = int(np.sqrt(mr)) + 1
                break

            d = rng.randint(0, 4)
            if d == 0: y -= 1
            elif d == 1: y += 1
            elif d == 2: x -= 1
            else: x += 1

            if x < 1 or x >= S-1 or y < 1 or y >= S-1:
                break

    img = (img * 255).astype(np.uint8)
    cv2.imwrite(f"{BASE}/images/dla_{i:03d}.png", img)
    skel = skeletonize(img > 0, method="zhang")
    G = skeleton_to_graph(skel)
    with open(f"{BASE}/graphs/dla_{i:03d}.gpickle", "wb") as f:
        pickle.dump(G, f)
    n = G.number_of_nodes()
    elapsed = time.time() - start
    print(f"DLA {i+1}/200: {n} nodes ({agg} agg) in {elapsed:.1f}s")

print("Done")
