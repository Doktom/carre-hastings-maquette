import os, sys, json, glob
import numpy as np, cv2

FR = r'C:\Users\tom\OneDrive\Documents\ATJ\ATJ GRAPHICS\PROJETS CLIENTS\2026\INOVA CARRE HASTING\360 ETAGES\360GOOD+\R+1'
files = sorted(glob.glob(os.path.join(FR, '*.jpg')))
M = {'chain': ('polys_chain.json', (0, 0, 255)), 'late20': ('polys_late20.json', (0, 200, 0)), 'zlate14': ('polys_late14.json', (0, 200, 255))}
data = {k: json.load(open(v[0])) for k, v in M.items() if os.path.exists(v[0])}
lot, vi = sys.argv[1], int(sys.argv[2])
frames = [int(x) for x in sys.argv[3].split(',')]
R = 70
tiles = []
for k in frames:
    im = cv2.imread(files[k])
    c = None
    for name, d in data.items():
        p = d[str(k)][lot][vi]
        if c is None:
            c = p
    x, y = int(c[0]), int(c[1])
    crop = im[max(0, y - R):y + R, max(0, x - R):x + R].copy()
    crop = cv2.resize(crop, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    for name, d in data.items():
        p = d[str(k)][lot][vi]
        px = int((p[0] - max(0, x - R)) * 4); py = int((p[1] - max(0, y - R)) * 4)
        cv2.circle(crop, (px, py), 7, M[name][1], 2)
        cv2.putText(crop, name[0].upper(), (px + 9, py - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.7, M[name][1], 2)
    cv2.putText(crop, f'img {k}', (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    tiles.append(cv2.resize(crop, (420, 420)))
rows = [np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles) - len(tiles) % 4, 4)]
cv2.imwrite(sys.argv[4], np.vstack(rows))
