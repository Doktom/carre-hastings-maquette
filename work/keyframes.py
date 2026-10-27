"""Report bidirectionnel des polygones depuis des images cles tracees a la main.

Hc[k] : homographie image 0 -> image k (alignement retenu de align_level.py : chaine d'ECC, fermeture
repartie sur le dernier tiers du tour), Hc[N] = identite (l'image 0 revue apres un tour).
Sans autre image cle que 0, on retrouve exactement l'ancien report.
Entre deux images cles a < b (b = N pour boucler sur l'image 0), l'image f est obtenue par
 - report avant  : polygones de a transportes par Hc[f] Hc[a]^-1
 - report arriere: polygones de b transportes par Hc[f] Hc[b]^-1
 - fusion lineaire (poids 1 sur a en a, 1 sur b en b) : l'erreur est nulle sur les images cles.
L'ecart entre les deux reports mesure la confiance de l'automatisme sur cette image.
"""
import json
import numpy as np, cv2


def chain_matrices(align):
    """N+1 matrices 3x3 : H[k] de l'alignement retenu (fermeture deja repartie), puis l'identite pour
    'image N' = image 0 revue apres un tour"""
    Hc = [np.array(h, float) for h in align['H']] + [np.eye(3)]
    return [h / h[2, 2] for h in Hc]


def tp(p, H):
    return cv2.perspectiveTransform(np.asarray(p, np.float64).reshape(-1, 1, 2), H).reshape(-1, 2)


def propagate(keys, Hc, N=30):
    """keys : {frame: {lot: [[x,y]..]}} (doit contenir 0). Retourne (frames, ecart) :
    frames[f][lot] = points, ecart[f] = ecart max (px) entre report avant et arriere."""
    ks = sorted(keys)
    assert ks[0] == 0
    ext = ks + [N]
    lots = list(keys[0])
    out, gap = {}, {}
    for a, b in zip(ext[:-1], ext[1:]):
        kb = keys[b % N]
        for f in range(a, b):
            t = (f - a) / (b - a)
            res, g = {}, 0.0
            for l in lots:
                Ta = Hc[f] @ np.linalg.inv(Hc[a]); Tb = Hc[f] @ np.linalg.inv(Hc[b])
                pa = tp(keys[a][l], Ta); pb = tp(kb[l], Tb)
                res[l] = ((1 - t) * pa + t * pb)
                g = max(g, float(np.linalg.norm(pa - pb, axis=1).max()))
            out[f] = res; gap[f] = g
    return out, gap
