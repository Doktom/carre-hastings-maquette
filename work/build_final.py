import os, re, json, io, base64, shutil, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PV = os.path.join(HERE)
WD = sys.argv[1]
OUT = os.path.join(WD, 'maquette-r1')
if os.path.exists(OUT):
    shutil.rmtree(OUT)
shutil.copytree(os.path.join(PV, 'site', 'img'), os.path.join(OUT, 'img'))
shutil.copytree(os.path.join(PV, 'site', 'pdf'), os.path.join(OUT, 'pdf'))
shutil.copytree(os.path.join(PV, 'final', 'frames'), os.path.join(OUT, 'frames'))
os.remove(os.path.join(OUT, 'img', 'r1_000.jpg'))

lots = json.load(open(os.path.join(PV, 'site', 'lots.json'), encoding='utf8'))
for l in lots.values():
    l['table'] = [[re.sub(r'^(\w+) \1$', r'\1', r[0]), r[1]] for r in l['table']]
pf = json.load(open(os.path.join(PV, 'polys_frames.json')))
frames = [pf[str(k)] for k in range(30)]

tpl = open(os.path.join(PV, 'final_template2.html'), encoding='utf8').read()
html = tpl.replace('__LOTS__', json.dumps(lots, ensure_ascii=False)).replace('__POLYS__', json.dumps(frames))
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf8').write(html)

# version autonome : tout est embarque (fonctionne sans serveur ni dossiers)
def data_uri(path, mime, maxw=None, q=76):
    if mime == 'image/jpeg' and maxw:
        im = Image.open(path).convert('RGB')
        if im.width > maxw:
            im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
        b = io.BytesIO(); im.save(b, 'JPEG', quality=q, optimize=True); raw = b.getvalue()
    else:
        raw = open(path, 'rb').read()
    return f'data:{mime};base64,' + base64.b64encode(raw).decode()

asset = {}
for i in range(30):
    asset[f'frames/r1_{i:02d}.jpg'] = data_uri(os.path.join(OUT, 'frames', f'r1_{i:02d}.jpg'), 'image/jpeg', 1600, 76)
for f in sorted(os.listdir(os.path.join(OUT, 'img'))):
    big = f.startswith('plan-lot')
    asset['img/' + f] = data_uri(os.path.join(OUT, 'img', f), 'image/jpeg', 1900 if big else 1280, 80 if big else 72)
for f in sorted(os.listdir(os.path.join(OUT, 'pdf'))):
    asset['pdf/' + f] = data_uri(os.path.join(OUT, 'pdf', f), 'application/pdf')
js = '<script>window.ASSET=' + json.dumps(asset) + ';</script>\n'
auto = html.replace('<script>\nconst A=', js + '<script>\nconst A=', 1)
assert js in auto
open(os.path.join(WD, 'maquette-r1-autonome.html'), 'w', encoding='utf8').write(auto)
print('folder', sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(OUT) for f in fs) // 1024, 'KB')
print('autonome', os.path.getsize(os.path.join(WD, 'maquette-r1-autonome.html')) // 1024, 'KB')
