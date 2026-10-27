"""Alignement global des images d'un niveau (rotation 360).

Calcule H[k] : homographie qui envoie les coordonnees de l'image 0 vers l'image k,
pour le plan des murs. Independant du nombre / de la forme des polygones : seule
la zone du batiment (enveloppe des polygones) sert de masque.

usage: python align2.py <dossier_images> <polygones.json> <sortie.json> [puissance=2]
(la sortie 'H' = alignement retenu : chaine d'images + fermeture repartie sur le dernier tiers)
"""
import os, sys, json, glob
import numpy as np, cv2
from scipy.optimize import least_squares

FR, POLY, OUT = sys.argv[1:4]
POW = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0
S = 0.5
files = sorted(glob.glob(os.path.join(FR, '*.jpg')) + glob.glob(os.path.join(FR, '*.png')))
N = len(files)
raw = [cv2.imread(f, cv2.IMREAD_GRAYSCALE) for f in files]
H0_, W0_ = raw[0].shape
imgs = [cv2.resize(r, None, fx=S, fy=S, interpolation=cv2.INTER_AREA) for r in raw]
fimgs = [cv2.GaussianBlur(im, (0, 0), 1.2).astype(np.float32) for im in imgs]
sift = cv2.SIFT_create(nfeatures=10000, contrastThreshold=0.02)
feats = [sift.detectAndCompute(im, None) for im in imgs]
bf = cv2.BFMatcher(cv2.NORM_L2)
Sm = np.diag([S, S, 1.0]); Sinv = np.linalg.inv(Sm)

user = json.load(open(POLY, encoding='utf8'))
lots = user['lots']
allpts = np.vstack([np.array(v['points'], np.float32) for v in lots.values()])
hull = cv2.convexHull(allpts).reshape(-1, 2)          # zone du batiment dans l'image 0


def tp(p, H):
    return cv2.perspectiveTransform(np.asarray(p, np.float64).reshape(-1, 1, 2), H).reshape(-1, 2)


def region_mask(hull_k, shape, pad):
    m = np.zeros(shape, np.uint8)
    cv2.fillPoly(m, [(hull_k * S).astype(np.int32)], 255)
    return cv2.dilate(m, np.ones((pad, pad), np.uint8))


def sift_h(a, b, mask):
    ka, da = feats[a]; kb, db = feats[b]
    idx = [i for i, k in enumerate(ka) if mask[int(k.pt[1]), int(k.pt[0])] > 0]
    if len(idx) < 12:
        return None
    raw_m = bf.knnMatch(da[idx], db, k=2)
    good = [(idx[x.queryIdx], x.trainIdx) for x, y in [r for r in raw_m if len(r) == 2] if x.distance < 0.8 * y.distance]
    if len(good) < 8:
        return None
    pa = np.float32([ka[i].pt for i, _ in good]); pb = np.float32([kb[j].pt for _, j in good])
    Hm, inl = cv2.findHomography(pa, pb, cv2.RANSAC, 3.0)
    return (Hm, int(inl.sum())) if Hm is not None else None


crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6)


def measure(a, b, hull_a, init=None):
    """homographie image a -> image b (coordonnees pleine resolution) + score de correlation"""
    m = region_mask(hull_a, imgs[a].shape, 24)
    inl = 0
    if init is None:
        r = sift_h(a, b, m)
        init_half = r[0] if r is not None else np.eye(3)
        inl = r[1] if r is not None else 0
    else:
        init_half = Sm @ init @ Sinv
    W = init_half.astype(np.float32).copy()
    try:
        cc, W = cv2.findTransformECC(fimgs[a], fimgs[b], W, cv2.MOTION_HOMOGRAPHY, crit, m, 5)
    except cv2.error:
        cc = 0.0
    shift = float(np.abs(tp(hull_a * S, W.astype(np.float64)) - tp(hull_a * S, init_half)).max())
    return Sinv @ W.astype(np.float64) @ Sm, float(cc), inl, shift


from scipy.linalg import logm, expm
step = []
cur_hull = hull.copy()
Hchain = [np.eye(3)]
for k in range(N):
    j = (k + 1) % N
    Hk, cc, inl, shift = measure(k, j, cur_hull)
    step.append((Hk, cc, inl, shift))
    print('pas', k, '->', j, 'cc', round(cc, 3), 'inliers', inl, 'decalage ECC', round(shift, 1), flush=True)
    if k < N - 1:
        Hchain.append(Hk @ Hchain[-1])
        cur_hull = tp(cur_hull, Hk)
Mloop = step[N - 1][0] @ Hchain[N - 1]
Mloop = Mloop / np.cbrt(np.linalg.det(Mloop))
L = logm(Mloop).real
w = np.array([1.0 / max(s[2], 4) ** POW for s in step])
c = np.concatenate([[0], np.cumsum(w)]) / w.sum()
# la derive se concentre sur les derniers pas (peu de points de correspondance, pas de fermeture) :
# on repartit l'erreur de fermeture sur le dernier tiers du tour (lissage progressif), pas sur tout le tour
K0 = int(round(N * 2 / 3))
sm = lambda t: (lambda u: u * u * (3 - 2 * u))(min(max(t, 0.0), 1.0))
Hs = [Hchain[k] @ expm(-sm((k - K0) / (N - K0)) * L).real for k in range(N)]
Hw = [Hchain[k] @ expm(-c[k] * L).real for k in range(N)]
err = np.abs(tp(hull, Mloop) - hull).max()
print('fermeture de boucle (px):', round(float(err), 1), '| poids cumules', [round(float(x), 2) for x in c[:N]])
json.dump({'N': N, 'H': [h.tolist() for h in Hs], 'H_weighted': [h.tolist() for h in Hw], 'H_chain': [h.tolist() for h in Hchain], 'weights': w.tolist(),
           'inliers': [s[2] for s in step], 'cc': [s[1] for s in step]}, open(OUT, 'w'))
print('ecrit', OUT)
