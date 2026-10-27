"""Report des polygones par modele de camera en orbite, ajuste sur les images cles tracees a la main.

Principe : les sommets des polygones sont dans un plan horizontal (dessus des murs). La camera tourne
autour d'un axe vertical, a hauteur et distance constantes, d'un pas d'azimut constant par image.
Parametres de camera (4) : focale, elevation, centre optique (ox, oy) ; le pas d'azimut vaut exactement 360/N degres (tour complet) ; positions des
sommets dans le plan (2 par sommet). On les ajuste (moindres carres) sur tous les tracés cles :
sur le R+1 (4 images, 44 sommets) l'ajustement a un rms de 1,4 px et predit une image retiree a 2-3 px.
Entre images cles, la difference modele - trace est interpolee lineairement (le trace est donc
reproduit exactement sur les images cles).

usage (bibliotheque) : frames, info = project_frames(keys, N=30)
   keys = {image: {lot: [[x, y], ...]}} (doit contenir 0), memes sommets dans toutes les images
"""
import numpy as np
from scipy.optimize import least_squares

D = 10.0                      # distance de la camera (unite arbitraire ; l'echelle du plan l'absorbe)


def camera(q, f_idx):
    logf, phi, ox, oy = q[:4]
    th = q[4] * f_idx
    P = D * np.array([np.cos(phi) * np.cos(th), np.cos(phi) * np.sin(th), np.sin(phi)])
    w = -P / np.linalg.norm(P)
    r = np.cross(w, [0, 0, 1.0]); r /= np.linalg.norm(r)
    u = np.cross(r, w)
    return P, r, u, w, np.exp(logf), ox, oy


def project(X, f_idx, q):
    P, r, u, w, F, ox, oy = camera(q, f_idx)
    Xw = np.c_[X, np.zeros(len(X))] - P
    z = Xw @ w
    return np.c_[ox + F * (Xw @ r) / z, oy - F * (Xw @ u) / z]


def unproject(px, f_idx, q):
    """pixel -> point du plan z=0"""
    P, r, u, w, F, ox, oy = camera(q, f_idx)
    px = np.asarray(px, float)
    d = ((px[:, 0] - ox) / F)[:, None] * r + (-(px[:, 1] - oy) / F)[:, None] * u + w
    s = -P[2] / d[:, 2]
    return (P + s[:, None] * d)[:, :2]


def _fit_once(obs, q0):
    """obs : liste de (image, indice_sommet, x, y). Retourne (q, X, rms). q0[4] = pas d'azimut, fixe."""
    delta = q0[4]
    m = 1 + max(o[1] for o in obs)
    first = {}
    for f, j, x, y in obs:
        first.setdefault(j, (f, x, y))
    X0 = np.zeros((m, 2))
    for j, (f, x, y) in first.items():
        X0[j] = unproject([[x, y]], f, q0)[0]
    fr = np.array([o[0] for o in obs]); jj = np.array([o[1] for o in obs]); xy = np.array([[o[2], o[3]] for o in obs])

    def res(p):
        q = np.append(p[:4], delta); X = p[4:].reshape(-1, 2)
        out = np.empty((len(obs), 2))
        for f in np.unique(fr):
            s = fr == f
            out[s] = project(X[jj[s]], f, q)
        return (out - xy).ravel()

    # structure creuse : chaque observation depend de q (5) et de son sommet (2)
    from scipy.sparse import lil_matrix
    S = lil_matrix((2 * len(obs), 4 + 2 * m), dtype=int)
    for k, j in enumerate(jj):
        S[2 * k:2 * k + 2, :4] = 1
        S[2 * k:2 * k + 2, 4 + 2 * j:6 + 2 * j] = 1
    r = least_squares(res, np.concatenate([q0[:4], X0.ravel()]), jac_sparsity=S, method='trf', x_scale='jac', max_nfev=300)
    return np.append(r.x[:4], delta), r.x[4:].reshape(-1, 2), float(np.sqrt(np.mean(r.fun ** 2)))


def fit_orbit(keys, lots, N=30):
    obs, index = [], {}
    for l in lots:
        for f, kp in keys.items():
            if l in kp:
                for j, (x, y) in enumerate(kp[l]):
                    index.setdefault((l, j), len(index))
                    obs.append((f, index[(l, j)], x, y))
    best = None
    for delta in (2 * np.pi / N, -2 * np.pi / N):
        for phi in (0.6, 1.0):
            for fl in (2000, 4000):
                try:
                    q, X, rms = _fit_once(obs, np.array([np.log(fl), phi, 1280.0, 720.0, delta]))
                except Exception:
                    continue
                if best is None or rms < best[2]:
                    best = (q, X, rms)
    return best[0], best[1], best[2], index


def project_frames(keys, N=30):
    lots = [l for l in keys[0] if len(keys[0][l]) >= 3]
    q, X, rms, index = fit_orbit(keys, lots, N)
    ks = sorted(keys) + [N]
    out = {f: {} for f in range(N)}
    corr = np.zeros(N)
    for l in lots:
        idx = [index[(l, j)] for j in range(len(keys[0][l]))]
        Xl = X[idx]
        model = {f: project(Xl, f, q) for f in range(N + 1)}      # image N = image 0 (azimut + 360 deg)
        lk = [k for k in ks[:-1] if l in keys[k]] + [N]
        res = {k: np.array(keys[k % N][l], float) - model[k] for k in lk}
        for a, b in zip(lk[:-1], lk[1:]):
            for f in range(a, b):
                t = (f - a) / (b - a)
                c = (1 - t) * res[a] + t * res[b]
                out[f][l] = (model[f] + c).round(1).tolist()
                corr[f] = max(corr[f], np.linalg.norm(c, axis=1).max())
    info = dict(rms=rms, focale=float(np.exp(q[0])), elevation_deg=float(np.degrees(q[1])),
                pas_azimut_deg=float(np.degrees(q[4])), q=q.tolist(), correction=corr.round(1).tolist())
    return out, info
