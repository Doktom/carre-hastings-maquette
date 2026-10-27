"""Applique les corrections manuelles (images cles) aux polygones calcules.

usage: python apply_corrections.py export.json [sortie.json]
Pour chaque sommet, l'ecart (corrige - calcule) est connu aux images corrigees ;
il est interpole lineairement entre ces images (circulaire) puis ajoute au calcul.
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PV = os.path.join(HERE)
exp = json.load(open(sys.argv[1], encoding='utf8'))
out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(PV, 'polys_frames.json')
prop = json.load(open(os.path.join(PV, 'prop_embedded.json')))      # liste de 30 {lot: points}
N = len(prop)
keys = sorted(exp['keyframes'])
if 0 not in keys:
    keys = [0] + keys
lots = list(prop[0].keys())

off = {}   # off[k][lot] = ecarts (n,2)
for k in keys:
    user = exp['frames'][str(k)] if str(k) in exp['frames'] else exp['frames'][k]
    off[k] = {l: np.array(user[l], float) - np.array(prop[k][l], float) for l in lots}

final = {}
for f in range(N):
    # images cles encadrantes (circulaire)
    prev = max([k for k in keys if k <= f])
    nxt = min([k for k in keys if k > f] or [keys[0] + N])
    nk = nxt % N
    t = (f - prev) / (nxt - prev) if nxt != prev else 0.0
    res = {}
    for l in lots:
        o = (1 - t) * off[prev][l] + t * off[nk][l]
        res[l] = (np.array(prop[f][l], float) + o).round(1).tolist()
    final[str(f)] = res

json.dump(final, open(out_path, 'w'))
mx = max(np.abs(np.array(final[str(f)][l]) - np.array(prop[f][l])).max() for f in range(N) for l in lots)
print('images cles:', keys, '| ecart max applique (px):', round(float(mx), 1), '->', out_path)
