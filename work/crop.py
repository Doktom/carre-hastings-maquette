import sys, os
from PIL import Image, ImageDraw, ImageFont
SRC = r'C:\Users\tom\OneDrive\Documents\ATJ\ATJ GRAPHICS\PROJETS CLIENTS\2026\INOVA CARRE HASTING\360 ETAGES\360GOOD+\R+1\MONPLAISIR_360 Coupe Etage R+1 (2k30)_00000.jpg'
x0, y0, x1, y1, z = [int(v) for v in sys.argv[1:6]]
out = sys.argv[6]
im = Image.open(SRC).convert('RGB').crop((x0, y0, x1, y1))
im = im.resize(((x1 - x0) * z, (y1 - y0) * z), Image.LANCZOS)
d = ImageDraw.Draw(im)
f = ImageFont.truetype('arial.ttf', 16)
step = 25
for x in range((x0 // step + 1) * step, x1, step):
    major = x % 100 == 0
    d.line([((x - x0) * z, 0), ((x - x0) * z, im.size[1])], fill=(255, 0, 0) if major else (255, 200, 0), width=1)
    if x % 50 == 0:
        d.text(((x - x0) * z + 3, 3), str(x), fill=(255, 0, 0), font=f)
for y in range((y0 // step + 1) * step, y1, step):
    major = y % 100 == 0
    d.line([(0, (y - y0) * z), (im.size[0], (y - y0) * z)], fill=(255, 0, 0) if major else (255, 200, 0), width=1)
    if y % 50 == 0:
        d.text((3, (y - y0) * z + 3), str(y), fill=(255, 0, 0), font=f)
im.save(out)
print(im.size)
