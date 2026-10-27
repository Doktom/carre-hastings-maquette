"""Construit l'editeur de polygones pour UNE image (tracer l'image 0 d'un niveau).

usage: python mk_editor1.py <image_0.jpg> <sortie.html> [polygones_existants.json]

L'image est embarquee dans la page (fichier autonome). Le JSON exporte par la page a le format :
  {level, image:{width,height}, lots:{"5":{typo, points:[[x,y],...]}}}   (coordonnees de l'image source)
Le fichier existant (meme format) sert de point de depart pour retoucher un trace.
"""
import base64, io, json, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
img, out = sys.argv[1:3]
start = sys.argv[3] if len(sys.argv) > 3 else None

im = Image.open(img).convert('RGB')
b = io.BytesIO(); im.save(b, 'JPEG', quality=90)
uri = 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()
lots = {}
if start:
    d = json.load(open(start, encoding='utf8'))
    lots = {k: {'typo': v['typo'], 'pts': v['points']} for k, v in d['lots'].items()}
t = open(os.path.join(HERE, 'editor_template.html'), encoding='utf8').read()
# la version "30 images" est produite par mk_editor2.py ; ici une seule image
t = t.replace('__IMG__', uri).replace('__LOTS__', json.dumps(lots))
t = t.replace('const KEY="editeur-polygones-v2";', 'const KEY="editeur-polygones-' + os.path.basename(img) + '";')
open(out, 'w', encoding='utf8').write(t)
print('ok', im.size, '->', out)
