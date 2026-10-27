import os, re, json, glob, shutil
import fitz
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

BASE = os.environ.get('CARRE_BASE', r'C:\Users\tom\OneDrive\Documents\ATJ\ATJ GRAPHICS\PROJETS CLIENTS\2026\INOVA CARRE HASTING')
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'site')
os.makedirs(os.path.join(OUT, 'img'), exist_ok=True)
os.makedirs(os.path.join(OUT, 'pdf'), exist_ok=True)

# fond R+1 image 0
bg = Image.open(os.path.join(BASE, '360 ETAGES', '360GOOD+', 'R+1', 'MONPLAISIR_360 Coupe Etage R+1 (2k30)_00000.jpg')).convert('RGB')
bg.save(os.path.join(OUT, 'img', 'r1_000.jpg'), quality=88)

# correspondance lot -> dossier vues 3D (hypothese a valider)
FOLDER = {5: 'R+1_T4_3', 6: 'R+1_T4_4', 7: 'R+1_T3_2', 8: 'R+1_T3_1'}
lots = {}
for n in (5, 6, 7, 8):
    src = os.path.join(BASE, 'Plansdeventes_pdf', f'Plans de vente - INOVA RUE MONPLAISIR-{n}.pdf')
    shutil.copy(src, os.path.join(OUT, 'pdf', f'lot-{n:02d}.pdf'))
    page = fitz.open(src)[0]
    words = page.get_text('words')
    # lignes du tableau (colonne droite, sous "Surfaces habitables")
    rows = {}
    for x0, y0, x1, y1, w, *_ in words:
        if x0 > 525 and y0 > 350:
            rows.setdefault(round(y0 / 3), []).append((x0, w))
    table = []
    for k in sorted(rows):
        ws = sorted(rows[k])
        txt = ' '.join(w for _, w in ws)
        m = re.match(r'^(.*?)\s+([\d,]+)\s*m', txt)
        if m:
            table.append((m.group(1).strip(), m.group(2)))
    head = page.get_text()
    typo = re.search(r'Appartement n\S* (\d+) - (T\d(?:/ ?T\d)?)', head)
    etage = 'Rez-de-chaussée' if 'REZ DE' in head else ('Étage 1' if 'ETAGE 1' in head else 'Étage 2')
    lots[n] = dict(num=n, typo=typo.group(2).replace(' ', ''), etage=etage, table=table)

    d = os.path.join(BASE, 'appartements 3d', '004_VUES INTERIEURES', FOLDER[n])
    files = sorted(os.listdir(d))
    views = []
    for f in files:
        low = f.lower()
        stem = os.path.splitext(f)[0]
        if low.endswith('.png') or low.endswith('.jpg') or low.endswith('.jpeg'):
            # evite les doublons (meme nom, extension differente)
            key = re.sub(r'[ _]+', '', stem.lower())
            key = re.sub(r'^.*?(plan3d|chambre\d?|sejour\d?(?:jour|nuit)?|chambreenfant|chambre)', r'\1', key)
            views.append((f, stem))
    seen, final = set(), []
    for f, stem in views:
        name = re.sub(r'^R\+\d_T\d_\d_?', '', stem).replace('_', ' ').strip()
        k = name.lower().replace(' ', '')
        if k in seen:
            continue
        seen.add(k)
        final.append((f, name))
    out_views = []
    for i, (f, name) in enumerate(final):
        im = Image.open(os.path.join(d, f)).convert('RGB')
        big = 'plan' in name.lower()
        im.thumbnail((2200 if big else 1600, 1400))
        fn = f'lot{n:02d}_{i:02d}.jpg'
        im.save(os.path.join(OUT, 'img', fn), quality=82)
        out_views.append(dict(file='img/' + fn, label=name.title().replace('Sejour', 'Séjour').replace('3d','3D').replace('Jour','jour').replace('Nuit','nuit')))
    lots[n]['views'] = out_views
    print(n, lots[n]['typo'], lots[n]['etage'], len(table), [v['label'] for v in out_views])

json.dump(lots, open(os.path.join(OUT, 'lots.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print(json.dumps(lots[5]['table'], ensure_ascii=False))
