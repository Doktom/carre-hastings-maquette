import os, re, json, base64, io, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PV = os.path.join(HERE)
t = open(os.path.join(PV, 'editor_template.html'), encoding='utf8').read()


def rep(a, b, cnt=1):
    global t
    assert a in t, a[:90]
    t = t.replace(a, b, cnt)


# --- donnees embarquees
rep('const DEFAULT_IMG="__IMG__";\nconst DEFAULT_LOTS=__LOTS__;',
    'const FRAME_URIS=__FRAMEURIS__;\nconst PROP=__PROP__;\nconst TYPO=__TYPO__;\nconst NF=FRAME_URIS.length;')
rep('let S={w:2560,h:1440,lots:JSON.parse(JSON.stringify(DEFAULT_LOTS)),sel:null,mode:"edit",draft:null,selV:null};',
    '''let S={w:2560,h:1440,lots:{},sel:null,mode:"edit",draft:null,selV:null,f:0};
const F=PROP.map(fr=>JSON.parse(JSON.stringify(fr)));
const K=new Set([0]);
function lotsOf(f){const o={};for(const id in F[f])o[id]={typo:TYPO[id],pts:F[f][id]};return o}
S.lots=lotsOf(0);''')
rep('function save(){try{localStorage.setItem(KEY,JSON.stringify({lots:S.lots,level:$("#level").value}))}catch(e){}}\nfunction load(){try{const d=JSON.parse(localStorage.getItem(KEY)||"null");if(d&&d.lots&&Object.keys(d.lots).length){S.lots=d.lots;if(d.level)$("#level").value=d.level}}catch(e){}}',
    '''function sync(){for(const id in S.lots)F[S.f][id]=S.lots[id].pts;for(const id in TYPO)if(S.lots[id])TYPO[id]=S.lots[id].typo}
function save(){sync();try{localStorage.setItem(KEY,JSON.stringify({F,K:[...K],TYPO,level:$("#level").value}))}catch(e){}}
function load(){try{const d=JSON.parse(localStorage.getItem(KEY)||"null");if(d&&d.F&&d.F.length===NF){d.F.forEach((fr,i)=>{F[i]=fr});K.clear();(d.K||[0]).forEach(k=>K.add(k));Object.assign(TYPO,d.TYPO||{});if(d.level)$("#level").value=d.level;S.lots=lotsOf(0)}}catch(e){}}''')
rep('const KEY="editeur-polygones-v2";', 'const KEY="controle-polygones-r1-v1";')
rep('function snapshot(){hist.push(JSON.stringify(S.lots));if(hist.length>200)hist.shift();redo=[]}\nfunction undo(){if(!hist.length)return;redo.push(JSON.stringify(S.lots));S.lots=JSON.parse(hist.pop());S.selV=null;render()}\nfunction redoF(){if(!redo.length)return;hist.push(JSON.stringify(S.lots));S.lots=JSON.parse(redo.pop());S.selV=null;render()}',
    '''function snapshot(){hist.push(JSON.stringify({f:S.f,lots:S.lots}));if(hist.length>300)hist.shift();redo=[]}
function restore(js){const d=JSON.parse(js);if(d.f!==S.f){sync();S.f=d.f;setImg()}S.lots=d.lots;sync();S.selV=null;render();updBar()}
function undo(){if(!hist.length)return;redo.push(JSON.stringify({f:S.f,lots:S.lots}));restore(hist.pop());save()}
function redoF(){if(!redo.length)return;hist.push(JSON.stringify({f:S.f,lots:S.lots}));restore(redo.pop());save()}''')
rep('<button class="btn" id="redo" aria-label="Rétablir">↷</button>\n  </div>',
    '''<button class="btn" id="redo" aria-label="Rétablir">↷</button>
   <span style="width:1px;height:20px;background:#d5dae0"></span>
   <button class="btn" id="fprev" aria-label="Image précédente">◀</button>
   <input type="range" id="fslide" min="0" max="29" value="0" style="width:170px" aria-label="Image">
   <button class="btn" id="fnext" aria-label="Image suivante">▶</button>
   <b id="flabel" style="min-width:170px;font-variant-numeric:tabular-nums"></b>
   <button class="btn" id="fnextk" title="Aller à la prochaine image non corrigée">Image suivante à contrôler</button>
  </div>''')
rep('function setImage(src,name){\n  const im=new Image();im.onload=()=>{S.w=im.naturalWidth;S.h=im.naturalHeight;img.src=src;img.width=S.w;img.height=S.h;$("#imgInfo").textContent=`${name||"image"} · ${S.w}×${S.h}`;fit()};im.src=src;\n}',
    '''function setImg(){img.src=FRAME_URIS[S.f];img.width=S.w;img.height=S.h}
function updBar(){
  $("#fslide").value=S.f;
  $("#flabel").innerHTML=`Image ${S.f} / ${NF-1}`+(S.f===0?" · <span style='color:#2f80ed'>référence</span>":K.has(S.f)?" · <span style='color:#2bb673'>corrigée ✓</span>":" · <span style='color:#6b7683'>calculée</span>");
  $("#imgInfo").textContent=`${K.size-1} image(s) corrigée(s) sur ${NF-1}`;
}
function gotoFrame(n){
  n=((n%NF)+NF)%NF;S.draft=null;if(S.mode==="draw")S.mode="edit";sync();S.f=n;S.lots=lotsOf(n);S.selV=null;
  if(S.sel&&!S.lots[S.sel])S.sel=null;setImg();updBar();render();
}''')
rep('<button class="btn" id="openImg">Ouvrir une image…</button>\n    <input type="file" id="fileImg" accept="image/*" hidden>\n    ', '')
rep('$("#openImg").onclick=()=>$("#fileImg").click();\n$("#fileImg").onchange=e=>{const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=()=>setImage(r.result,f.name);r.readAsDataURL(f)};\n', '')
rep('$("#mDraw").onclick=()=>{if(!S.sel){toast("Sélectionnez ou ajoutez un lot d\'abord");return}startDraw(S.sel)};',
    '$("#mDraw").onclick=()=>{if(S.f!==0){toast("Le tracé se fait sur l\'image 0 (référence)");return}if(!S.sel){toast("Sélectionnez ou ajoutez un lot d\'abord");return}startDraw(S.sel)};')
rep('$("#addLot").onclick=()=>{\n', '$("#addLot").onclick=()=>{\n  if(S.f!==0){toast("Ajout de lot possible sur l\'image 0 uniquement");return}\n')
rep('if(t.dataset&&t.dataset.edge){const[id,i]=t.dataset.edge.split(":");snapshot();',
    'if(t.dataset&&t.dataset.edge){if(S.f!==0){toast("Sur cette image, on ne fait que déplacer les sommets");return}const[id,i]=t.dataset.edge.split(":");snapshot();')
rep('function deleteVertex(id,i){const l=S.lots[id];',
    'function deleteVertex(id,i){if(S.f!==0){toast("Suppression de sommet possible sur l\'image 0 uniquement");return}const l=S.lots[id];')
rep('d.querySelector(".x").onclick=e=>{e.stopPropagation();snapshot();',
    'd.querySelector(".x").onclick=e=>{e.stopPropagation();if(S.f!==0){toast("Suppression de lot possible sur l\'image 0 uniquement");return}snapshot();')
rep('view.addEventListener("pointerup",()=>{if(drag){if(!drag.whole||drag.moved){save()}drag=null}pan=null});',
    'view.addEventListener("pointerup",()=>{if(drag){if(!drag.whole||drag.moved){markK();save()}drag=null}pan=null});')
rep('if(m){e.preventDefault();snapshot();l.pts[i]=[r1(l.pts[i][0]+m[0]),r1(l.pts[i][1]+m[1])];save();render()}',
    'if(m){e.preventDefault();snapshot();l.pts[i]=[r1(l.pts[i][0]+m[0]),r1(l.pts[i][1]+m[1])];markK();save();render()}')
rep('/* ---------- boutons ---------- */',
    '''function markK(){if(S.f!==0&&!K.has(S.f)){K.add(S.f);updBar()}}
/* ---------- boutons ---------- */
$("#fprev").onclick=()=>gotoFrame(S.f-1);$("#fnext").onclick=()=>gotoFrame(S.f+1);
$("#fslide").oninput=e=>gotoFrame(+e.target.value);
$("#fnextk").onclick=()=>{for(let i=1;i<=NF;i++){const n=(S.f+i)%NF;if(n!==0&&!K.has(n)){gotoFrame(n);return}}toast("Toutes les images sont corrigées")};''')
rep('if(e.key==="0"){fit();return}',
    'if(e.key==="0"){fit();return}\n  if(e.key==="PageDown"||e.key==="."){gotoFrame(S.f+1);return}\n  if(e.key==="PageUp"||e.key===","){gotoFrame(S.f-1);return}')

old = t[t.index('function payload(){'):t.index('$("#exp").onclick')]
t = t.replace(old, '''function payload(){
  sync();
  const out={level:$("#level").value,image:{width:S.w,height:S.h},lots:{},frames:{},keyframes:[...K].sort((a,b)=>a-b)};
  for(const id of Object.keys(F[0]).sort((a,b)=>a-b)){out.lots[id]={typo:TYPO[id],points:F[0][id]}}
  for(let k=0;k<NF;k++)out.frames[k]=F[k];
  return out;
}
''')
old = t[t.index('$("#fileJson").onchange'):t.index('window.addEventListener("resize"')]
t = t.replace(old, '''$("#fileJson").onchange=e=>{const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=()=>{try{const d=JSON.parse(r.result);
  if(!d.frames){toast("Ce fichier ne contient pas les 30 images");return}
  for(let k=0;k<NF;k++)if(d.frames[k])F[k]=d.frames[k];K.clear();(d.keyframes||[0]).forEach(k=>K.add(k));
  for(const id in d.lots)TYPO[id]=d.lots[id].typo;if(d.level)$("#level").value=d.level;
  S.sel=null;gotoFrame(S.f);save();toast("Tracé importé")}catch(err){toast("Fichier invalide")}};r.readAsText(f)};
''')
rep('load();setImage(DEFAULT_IMG,"R+1 · image 0");', 'load();setImg();updBar();fit();')
rep('<h1>Éditeur de polygones</h1><div class="hint">Tracez les appartements une seule fois sur l\'image 0 : le tracé est ensuite reporté sur toutes les autres images.</div>',
    '<h1>Contrôle des polygones</h1><div class="hint">Parcourez les 30 images (curseur ou ◀ ▶). Quand un contour s\'écarte d\'un mur, glissez les sommets : l\'image passe en « corrigée » et les images voisines sont ajustées automatiquement.</div>')
rep('<h2>Niveau / image</h2>', '<h2>Niveau</h2>')
t = t.replace('<title>Éditeur de polygones</title>', '<title>Contrôle des polygones</title>')

# --- injection des donnees
pf = json.load(open(os.path.join(PV, 'polys_frames.json')))
prop = [pf[str(k)] for k in range(30)]
user = json.load(open(os.path.join(PV, 'user_R1.json'), encoding='utf8'))
typo = {k: v['typo'] for k, v in user['lots'].items()}
uris = []
D = os.path.join(PV, 'final', 'frames')
for k in range(30):
    im = Image.open(os.path.join(D, f'r1_{k:02d}.jpg')).convert('RGB').resize((1600, 900), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, 'JPEG', quality=78)
    uris.append('data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode())
t = t.replace('__FRAMEURIS__', json.dumps(uris)).replace('__PROP__', json.dumps(prop)).replace('__TYPO__', json.dumps(typo))
wd = sys.argv[1]
open(os.path.join(wd, 'controle-polygones.html'), 'w', encoding='utf8').write(t)
json.dump(prop, open(os.path.join(PV, 'prop_embedded.json'), 'w'))
print('ok', len(t) // 1024, 'KB')
