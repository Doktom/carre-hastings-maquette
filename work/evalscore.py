"""Score d'alignement : les contours doivent suivre des bords nets de l'image.

usage: python evalscore.py <dossier_images> <polys_frames.json> [autre.json ...]
Affiche, par fichier, le score moyen et les 5 plus mauvaises images (plus haut = mieux).
"""
import os, sys, glob, json
import numpy as np, cv2

FR = sys.argv[1]
files = sorted(glob.glob(os.path.join(FR, '*.jpg')) + glob.glob(os.path.join(FR, '*.png')))
grads = []
for f in files:
    g = cv2.GaussianBlur(cv2.imread(f, cv2.IMREAD_GRAYSCALE).astype(np.float32), (0, 0), 1.5)
    m = cv2.magnitude(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
    grads.append(cv2.dilate(m, np.ones((5, 5), np.uint8)))


def score(frames):
    sc = []
    for k, G in enumerate(grads):
        vals = []
        for lot, pts in frames[str(k)].items():
            p = np.array(pts)
            for a, b in zip(p, np.roll(p, -1, axis=0)):
                n = max(2, int(np.hypot(*(b - a)) / 3))
                xs = np.linspace(a[0], b[0], n).astype(int).clip(0, G.shape[1] - 1)
                ys = np.linspace(a[1], b[1], n).astype(int).clip(0, G.shape[0] - 1)
                vals.append(G[ys, xs])
        sc.append(float(np.mean(np.concatenate(vals))))
    return sc


for path in sys.argv[2:]:
    sc = score(json.load(open(path)))
    worst = sorted(range(len(sc)), key=lambda i: sc[i])[:5]
    print(os.path.basename(path), 'moyenne', round(float(np.mean(sc)), 1), '| minimum', round(min(sc), 1),
          '| pires images', [(i, round(sc[i], 1)) for i in worst])
