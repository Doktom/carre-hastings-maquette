"""Calcule les polygones des 30 images a partir des images cles exportees par controle-polygones.html
(modele de camera en orbite, voir orbit.py).

usage: python apply_keys.py <export.json> [sortie.json] [--lisse]
  sortie.json : {image: {lot: points}} (meme format que polys_frames.json) -> par defaut polys_frames.json
  --lisse     : ne colle pas exactement aux traces (le modele lisse les petites irregularites)
"""
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orbit

args = [a for a in sys.argv[1:] if not a.startswith('--')]
exp = json.load(open(args[0], encoding='utf8'))
out_path = args[1] if len(args) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'polys_frames.json')
keys = {int(k): v for k, v in exp['keys'].items()}
frames, info = orbit.project_frames(keys, N=len(exp['frames']))
if '--lisse' in sys.argv:
    # modele seul : on retire la correction interpolee
    q = np.array(info['q'])
    lots = [l for l in keys[0] if len(keys[0][l]) >= 3]
    _, X, _, index = orbit.fit_orbit(keys, lots, len(exp['frames']))
    for l in lots:
        Xl = X[[index[(l, j)] for j in range(len(keys[0][l]))]]
        for f in frames:
            frames[f][l] = orbit.project(Xl, f, q).round(1).tolist()
json.dump({str(f): frames[f] for f in sorted(frames)}, open(out_path, 'w'))
print(f"images cles : {sorted(keys)} | erreur du modele sur vos traces : {info['rms']:.2f} px (rms)"
      f" | focale {info['focale']:.0f}, elevation {info['elevation_deg']:.1f} deg, pas d'azimut {info['pas_azimut_deg']:.2f} deg")
print('->', out_path)
