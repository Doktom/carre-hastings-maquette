"""Exporte les images d'un niveau (360 etage) en JPG 1920x1080 pour le web.

usage: python export_frames.py <dossier_images_source> <dossier_sortie> [prefixe=r1] [largeur=1920]
Ex.:   python export_frames.py "<...>/360GOOD+/R+1" final/frames r1
"""
import os, sys
from PIL import Image

src, dst = sys.argv[1:3]
prefix = sys.argv[3] if len(sys.argv) > 3 else 'r1'
W = int(sys.argv[4]) if len(sys.argv) > 4 else 1920
os.makedirs(dst, exist_ok=True)
files = sorted(f for f in os.listdir(src) if f.lower().endswith(('.jpg', '.jpeg', '.png')))
for i, f in enumerate(files):
    im = Image.open(os.path.join(src, f)).convert('RGB')
    im = im.resize((W, round(im.height * W / im.width)), Image.LANCZOS)
    im.save(os.path.join(dst, f'{prefix}_{i:02d}.jpg'), quality=82)
print(len(files), 'images ->', dst)
