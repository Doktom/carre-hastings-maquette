"""Applique l'alignement H[k] aux polygones de l'image 0 -> polys_frames.json

usage: python propagate.py <polygones.json> <align.json> <sortie.json> [cle=H|H_chain]
"""
import sys, json
import numpy as np, cv2

POLY, ALIGN, OUT = sys.argv[1:4]
KEY = sys.argv[4] if len(sys.argv) > 4 else 'H'
user = json.load(open(POLY, encoding='utf8'))
al = json.load(open(ALIGN))
Hs = [np.array(h) for h in al[KEY]]
out = {}
for k, H in enumerate(Hs):
    out[str(k)] = {
        lot: cv2.perspectiveTransform(np.array(v['points'], np.float64).reshape(-1, 1, 2), H).reshape(-1, 2).round(1).tolist()
        for lot, v in user['lots'].items()
    }
json.dump(out, open(OUT, 'w'))
print('ok', len(out), 'images,', len(user['lots']), 'lots ->', OUT)
