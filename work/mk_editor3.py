"""Outil de controle des polygones - version images cles (report bidirectionnel).

usage: python mk_editor3.py <dossier_sortie> [align.json] [polys_frames.json] [user.json] [dossier_images]
Genere <dossier_sortie>/controle-polygones.html : 30 images, 4 images cles recommandees
(0, 8, 15, 23 = tous les ~90 degres). Ce qui est corrige a la main sur une image cle ancre le
trace ; les images intermediaires sont recalculees (report avant + report arriere fusionnes).
"""
import os, json, base64, io, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
ALIGN = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'align_R1.json')
PF = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, 'polys_frames.json')
USER = sys.argv[4] if len(sys.argv) > 4 else os.path.join(HERE, 'user_R1.json')
FRAMES = sys.argv[5] if len(sys.argv) > 5 else os.path.join(HERE, 'final', 'frames')
REC = [0, 8, 15, 23]
t = open(os.path.join(HERE, 'editor_template.html'), encoding='utf8').read()


def rep(a, b):
    global t
    assert a in t, a[:90]
    t = t.replace(a, b, 1)


# ---------------------------------------------------------------- donnees + modele
rep('const DEFAULT_IMG="__IMG__";\nconst DEFAULT_LOTS=__LOTS__;',
    '''const FRAME_URIS=__FRAMEURIS__;
const PROP=__PROP__;
const TYPO=__TYPO__;
const HC=__HC__;
const REC=__REC__;
const NF=FRAME_URIS.length;''')
rep('let S={w:2560,h:1440,lots:JSON.parse(JSON.stringify(DEFAULT_LOTS)),sel:null,mode:"edit",draft:null,selV:null};',
    '''let S={w:2560,h:1440,lots:{},sel:null,mode:"edit",draft:null,selV:null,f:0};
const deep=o=>JSON.parse(JSON.stringify(o));
const F=PROP.map(deep);                 // polygones calcules de chaque image
let KP={0:deep(PROP[0])};               // images cles : {image:{lot:[[x,y]..]}} (tracees / corrigees a la main)
const GAP=new Array(NF).fill(0);        // ecart (px) entre report avant et report arriere
/* matrices 3x3 (ligne par ligne) : image 0 -> image k, k=0..NF (NF = image 0 revue apres un tour) */
const mul=(A,B)=>{const C=new Array(9).fill(0);for(let i=0;i<3;i++)for(let j=0;j<3;j++)for(let k=0;k<3;k++)C[i*3+j]+=A[i*3+k]*B[k*3+j];return C};
function inv3(M){const[a,b,c,d,e,f,g,h,i]=M;const A=e*i-f*h,B=-(d*i-f*g),C=d*h-e*g,det=a*A+b*B+c*C;
  return[A/det,-(b*i-c*h)/det,(b*f-c*e)/det,B/det,(a*i-c*g)/det,-(a*f-c*d)/det,C/det,-(a*h-b*g)/det,(a*e-b*d)/det]}
const HCI=HC.map(inv3);
const tr=(a,b)=>mul(HC[b],HCI[a]);
function ap(H,p){const w=H[6]*p[0]+H[7]*p[1]+H[8];return[(H[0]*p[0]+H[1]*p[1]+H[2])/w,(H[3]*p[0]+H[4]*p[1]+H[5])/w]}
function recomputeChain(){
  GAP.fill(0);
  for(const l of Object.keys(KP[0])){
    const n=KP[0][l].length;
    if(n<3){for(let f=0;f<NF;f++)F[f][l]=[];continue}
    const ks=Object.keys(KP).map(Number).filter(k=>KP[k][l]&&KP[k][l].length===n).sort((a,b)=>a-b);
    const ext=[...ks,NF];
    for(let i=0;i<ks.length;i++){
      const a=ext[i],b=ext[i+1],pa=KP[a][l],pb=KP[b%NF][l];
      for(let f=a;f<b;f++){
        if(f===a){F[f][l]=pa.map(p=>[p[0],p[1]]);continue}
        const t=(f-a)/(b-a),Ta=tr(a,f),Tb=tr(b,f);
        F[f][l]=pa.map((p,j)=>{const u=ap(Ta,p),v=ap(Tb,pb[j]);GAP[f]=Math.max(GAP[f],Math.hypot(u[0]-v[0],u[1]-v[1]));
          return[r1((1-t)*u[0]+t*v[0]),r1((1-t)*u[1]+t*v[1])]});
      }
    }
  }
}
/* ---- modele de camera en orbite (meme maths que orbit.py) : camera a distance/hauteur constantes autour d'un axe
   vertical, pas d'azimut = 360/NF ; sommets dans un plan horizontal. Ajuste sur les tracés cles (4 images -> rms ~2 px). */
const MODEL={mode:"chain",rms:0,focale:0,elev:0,perKey:{},q:null,fail:null};
const DIST=10;let DEL=2*Math.PI/NF;
function cam(q,fi){
  const th=DEL*fi,cp=Math.cos(q[1]),sp=Math.sin(q[1]);
  const P=[DIST*cp*Math.cos(th),DIST*cp*Math.sin(th),DIST*sp],n=Math.hypot(P[0],P[1],P[2]);
  const w=[-P[0]/n,-P[1]/n,-P[2]/n];let r=[w[1],-w[0],0];const rn=Math.hypot(r[0],r[1]);r=[r[0]/rn,r[1]/rn,0];
  const u=[r[1]*w[2]-r[2]*w[1],r[2]*w[0]-r[0]*w[2],r[0]*w[1]-r[1]*w[0]];
  return{P,r,u,w,F:Math.exp(q[0]),ox:q[2],oy:q[3]};
}
function proj(c,X){const a=X[0]-c.P[0],b=X[1]-c.P[1],e=-c.P[2];const z=a*c.w[0]+b*c.w[1]+e*c.w[2];
  return[c.ox+c.F*(a*c.r[0]+b*c.r[1])/z,c.oy-c.F*(a*c.u[0]+b*c.u[1]+e*c.u[2])/z]}
function unproj(c,p){const a=(p[0]-c.ox)/c.F,b=-(p[1]-c.oy)/c.F;
  const d=[a*c.r[0]+b*c.u[0]+c.w[0],a*c.r[1]+b*c.u[1]+c.w[1],a*c.r[2]+b*c.u[2]+c.w[2]],s=-c.P[2]/d[2];
  return[c.P[0]+s*d[0],c.P[1]+s*d[1]]}
function solveLin(A,b){const n=b.length,M=A.map((r,i)=>[...r,b[i]]);
  for(let i=0;i<n;i++){let p=i;for(let k=i+1;k<n;k++)if(Math.abs(M[k][i])>Math.abs(M[p][i]))p=k;
    if(Math.abs(M[p][i])<1e-18)return null;[M[i],M[p]]=[M[p],M[i]];
    for(let k=i+1;k<n;k++){const f=M[k][i]/M[i][i];for(let j=i;j<=n;j++)M[k][j]-=f*M[i][j]}}
  const x=new Array(n);for(let i=n-1;i>=0;i--){let s=M[i][n];for(let j=i+1;j<n;j++)s-=M[i][j]*x[j];x[i]=s/M[i][i]}return x}
/* moindres carres (Levenberg-Marquardt, complement de Schur) : q=[log f, elevation, ox, oy] + position plane de chaque sommet */
function fitOnce(obs,m,q0,delta){
  DEL=delta;let q=q0.slice();let X=new Array(m).fill(null);
  for(const o of obs)if(!X[o.j])X[o.j]=unproj(cam(q,o.f),[o.x,o.y]);
  const cost=(q,X)=>{const cs={};let s=0;for(const o of obs){const c=cs[o.f]||(cs[o.f]=cam(q,o.f));const p=proj(c,X[o.j]);s+=(p[0]-o.x)**2+(p[1]-o.y)**2}return s};
  let c0=cost(q,X),lam=1e-3;const eq=[1e-5,1e-6,1e-2,1e-2],ex=1e-5;
  for(let it=0;it<80;it++){
    const U=[0,1,2,3].map(()=>[0,0,0,0]),gq=[0,0,0,0];
    const W=Array.from({length:m},()=>[[0,0],[0,0],[0,0],[0,0]]),V=Array.from({length:m},()=>[[0,0],[0,0]]),gx=Array.from({length:m},()=>[0,0]);
    const cs={};
    for(const o of obs){
      const c=cs[o.f]||(cs[o.f]=cam(q,o.f)),Xj=X[o.j],p0=proj(c,Xj),r=[p0[0]-o.x,p0[1]-o.y];
      const Jq=[[0,0,0,0],[0,0,0,0]],Jx=[[0,0],[0,0]];
      for(let k=0;k<4;k++){const q2=q.slice();q2[k]+=eq[k];const p=proj(cam(q2,o.f),Xj);Jq[0][k]=(p[0]-p0[0])/eq[k];Jq[1][k]=(p[1]-p0[1])/eq[k]}
      for(let k=0;k<2;k++){const X2=Xj.slice();X2[k]+=ex;const p=proj(c,X2);Jx[0][k]=(p[0]-p0[0])/ex;Jx[1][k]=(p[1]-p0[1])/ex}
      for(let a=0;a<4;a++){for(let b=0;b<4;b++)U[a][b]+=Jq[0][a]*Jq[0][b]+Jq[1][a]*Jq[1][b];gq[a]+=Jq[0][a]*r[0]+Jq[1][a]*r[1];
        for(let b=0;b<2;b++)W[o.j][a][b]+=Jq[0][a]*Jx[0][b]+Jq[1][a]*Jx[1][b]}
      for(let a=0;a<2;a++){for(let b=0;b<2;b++)V[o.j][a][b]+=Jx[0][a]*Jx[0][b]+Jx[1][a]*Jx[1][b];gx[o.j][a]+=Jx[0][a]*r[0]+Jx[1][a]*r[1]}
    }
    let ok=false,done=false;
    for(let tries=0;tries<12&&!ok;tries++){
      const S=U.map((row,a)=>row.map((v,b)=>a===b?v*(1+lam)+1e-9:v)),rhs=gq.map(v=>-v),Vi=[];
      for(let j=0;j<m;j++){
        const v00=V[j][0][0]*(1+lam)+1e-12,v11=V[j][1][1]*(1+lam)+1e-12,v01=V[j][0][1],det=v00*v11-v01*v01;
        const vi=[[v11/det,-v01/det],[-v01/det,v00/det]];Vi.push(vi);
        const WV=W[j].map(row=>[row[0]*vi[0][0]+row[1]*vi[1][0],row[0]*vi[0][1]+row[1]*vi[1][1]]);
        for(let a=0;a<4;a++){for(let b=0;b<4;b++)S[a][b]-=WV[a][0]*W[j][b][0]+WV[a][1]*W[j][b][1];rhs[a]+=WV[a][0]*gx[j][0]+WV[a][1]*gx[j][1]}
      }
      const dq=solveLin(S,rhs);if(!dq){lam*=4;continue}
      const q2=q.map((v,k)=>v+dq[k]);
      const X2=X.map((x,j)=>{const t0=-gx[j][0]-(W[j][0][0]*dq[0]+W[j][1][0]*dq[1]+W[j][2][0]*dq[2]+W[j][3][0]*dq[3]),
        t1=-gx[j][1]-(W[j][0][1]*dq[0]+W[j][1][1]*dq[1]+W[j][2][1]*dq[2]+W[j][3][1]*dq[3]);
        return[x[0]+Vi[j][0][0]*t0+Vi[j][0][1]*t1,x[1]+Vi[j][1][0]*t0+Vi[j][1][1]*t1]});
      const c1=cost(q2,X2);
      if(c1<c0){const gain=c0-c1;q=q2;X=X2;c0=c1;lam=Math.max(lam/3,1e-9);ok=true;if(gain<1e-7*c0+1e-9)done=true}else lam*=4;
    }
    if(!ok||done)break;
  }
  return{q,X,rms:Math.sqrt(c0/(2*obs.length)),delta};
}
function recomputeOrbit(){
  const lots=Object.keys(KP[0]).filter(l=>KP[0][l].length>=3),idx={},obs=[],frames=new Set();let m=0;
  for(const l of lots)for(const f of Object.keys(KP).map(Number)){const kp=KP[f][l];if(!kp||kp.length!==KP[0][l].length)continue;frames.add(f);
    kp.forEach((p,j)=>{const key=l+":"+j;if(!(key in idx))idx[key]=m++;obs.push({f,j:idx[key],x:p[0],y:p[1]})})}
  if(frames.size<3){MODEL.mode="chain";MODEL.fail=null;return false}
  let best=null;
  const starts=[];
  if(MODEL.q)starts.push([MODEL.q,MODEL.delta]);
  for(const d of[1,-1])for(const ph of[0.6,1.0])for(const fl of[2000,4000])starts.push([[Math.log(fl),ph,S.w/2,S.h/2],d*2*Math.PI/NF]);
  for(let i=0;i<starts.length;i++){
    let r;try{r=fitOnce(obs,m,starts[i][0],starts[i][1])}catch(e){continue}
    if(!isFinite(r.rms))continue;if(!best||r.rms<best.rms)best=r;
    if(i===0&&MODEL.q&&r.rms<3)break;               // depart a chaud : l'ajustement precedent convient encore
  }
  if(!best||!(best.rms<8)){MODEL.mode="chain";MODEL.fail=best?best.rms:null;MODEL.q=null;return false}
  DEL=best.delta;const snapK=$("#snapKey").checked;
  GAP.fill(0);const perKey={},cnt={};
  for(const l of lots){
    const n=KP[0][l].length,Xl=[];for(let j=0;j<n;j++)Xl.push(best.X[idx[l+":"+j]]);
    const mod=[];for(let f=0;f<=NF;f++){const c=cam(best.q,f);mod.push(Xl.map(x=>proj(c,x)))}
    const lk=Object.keys(KP).map(Number).filter(k=>KP[k][l]&&KP[k][l].length===n).sort((a,b)=>a-b);
    const res={};for(const k of lk){res[k]=KP[k][l].map((p,j)=>[p[0]-mod[k][j][0],p[1]-mod[k][j][1]]);
      perKey[k]=(perKey[k]||0)+res[k].reduce((s,e)=>s+Math.hypot(e[0],e[1]),0);cnt[k]=(cnt[k]||0)+n}
    res[NF]=res[0];const ext=[...lk,NF];
    for(let i=0;i<lk.length;i++){const a=ext[i],b=ext[i+1];
      for(let f=a;f<b;f++){const t=(f-a)/(b-a);
        F[f][l]=mod[f].map((p,j)=>{const cx=(1-t)*res[a][j][0]+t*res[b][j][0],cy=(1-t)*res[a][j][1]+t*res[b][j][1];
          GAP[f]=Math.max(GAP[f],Math.hypot(cx,cy));return snapK?[r1(p[0]+cx),r1(p[1]+cy)]:[r1(p[0]),r1(p[1])]})}}
  }
  for(const k in perKey)perKey[k]/=cnt[k];
  for(const l of Object.keys(KP[0]))if(KP[0][l].length<3)for(let f=0;f<NF;f++)F[f][l]=[];
  Object.assign(MODEL,{mode:"orbit",rms:best.rms,focale:Math.exp(best.q[0]),elev:best.q[1]*180/Math.PI,q:best.q,delta:best.delta,perKey,fail:null});
  return true;
}
function recompute(){if(!recomputeOrbit())recomputeChain()}
function lotsOf(f){const o={};for(const id in F[f])o[id]={typo:TYPO[id],pts:F[f][id]};return o}
function nLots(){return Object.keys(KP[0]).filter(l=>KP[0][l].length>=3).length}
function doneCount(f){return Object.keys(KP[f]||{}).filter(l=>KP[0][l]&&KP[0][l].length>=3).length}
const isDone=f=>doneCount(f)>=nLots();
/* enregistre l'etat courant comme trace ancre (ids = lots touches, sinon tous) */
function commitKey(ids){
  const cur=KP[S.f]||{};
  for(const id of (ids||Object.keys(S.lots)))if(S.lots[id])cur[id]=S.lots[id].pts.map(p=>[p[0],p[1]]);
  KP[S.f]=cur;
  if(S.f===0){let lost=false;
    for(const k of Object.keys(KP)){if(+k===0)continue;
      for(const id of Object.keys(KP[k]))if(!cur[id]||cur[id].length!==KP[k][id].length){delete KP[k][id];lost=true}
      if(!Object.keys(KP[k]).length)delete KP[k]}
    if(lost)toast("Le nombre de sommets a changé sur l'image 0 : les corrections des autres images pour ces lots ont été retirées")}
  recompute();updBar();
}
S.lots=lotsOf(0);''')

# ---------------------------------------------------------------- persistance / historique
rep('function save(){try{localStorage.setItem(KEY,JSON.stringify({lots:S.lots,level:$("#level").value}))}catch(e){}}\nfunction load(){try{const d=JSON.parse(localStorage.getItem(KEY)||"null");if(d&&d.lots&&Object.keys(d.lots).length){S.lots=d.lots;if(d.level)$("#level").value=d.level}}catch(e){}}',
    '''function sync(){for(const id in S.lots)TYPO[id]=S.lots[id].typo}
function save(){sync();if(S.f===0)commitKey();try{localStorage.setItem(KEY,JSON.stringify({KP,TYPO,level:$("#level").value}))}catch(e){}}
function load(){try{const d=JSON.parse(localStorage.getItem(KEY)||"null");if(d&&d.KP&&d.KP[0]){KP=d.KP;Object.assign(TYPO,d.TYPO||{});if(d.level)$("#level").value=d.level;recompute();S.lots=lotsOf(0)}}catch(e){}}''')
rep('const KEY="editeur-polygones-v2";', 'const KEY="controle-polygones-r1-v2";')
rep('function snapshot(){hist.push(JSON.stringify(S.lots));if(hist.length>200)hist.shift();redo=[]}\nfunction undo(){if(!hist.length)return;redo.push(JSON.stringify(S.lots));S.lots=JSON.parse(hist.pop());S.selV=null;render()}\nfunction redoF(){if(!redo.length)return;hist.push(JSON.stringify(S.lots));S.lots=JSON.parse(redo.pop());S.selV=null;render()}',
    '''const state=()=>JSON.stringify({f:S.f,KP,lots:S.lots});
function snapshot(){hist.push(state());if(hist.length>300)hist.shift();redo=[]}
function restore(js){const d=JSON.parse(js);KP=d.KP;S.f=d.f;recompute();S.lots=d.lots;S.selV=null;setImg();updBar();render();save()}
function undo(){if(!hist.length)return;redo.push(state());restore(hist.pop())}
function redoF(){if(!redo.length)return;hist.push(state());restore(redo.pop())}''')

# ---------------------------------------------------------------- barre : navigation entre images
rep('<button class="btn" id="redo" aria-label="Rétablir">↷</button>\n  </div>',
    '''<button class="btn" id="redo" aria-label="Rétablir">↷</button>
   <span style="width:1px;height:20px;background:#d5dae0"></span>
   <button class="btn" id="fprev" aria-label="Image précédente">◀</button>
   <input type="range" id="fslide" min="0" max="29" value="0" style="width:150px" aria-label="Image">
   <button class="btn" id="fnext" aria-label="Image suivante">▶</button>
   <button class="btn dark" id="fnextk" title="Aller à la prochaine image à préciser">Prochaine image à préciser ▸</button>
   <button class="btn" id="fok" title="Le tracé est juste sur cette image : le valider tel quel">✓ Valider cette image</button>
   <div id="flabel"></div>
   <div id="strip" role="group" aria-label="Les 30 images"></div>
  </div>''')
rep('@media (max-width:820px)',
    '''#flabel{flex-basis:100%;font-variant-numeric:tabular-nums}
#strip{flex-basis:100%;display:grid;grid-template-columns:repeat(30,1fr);gap:2px}
#strip button{appearance:none;border:2px solid transparent;background:#e9ecf0;color:#4a5560;border-radius:4px;padding:3px 0 2px;font:600 10px inherit;cursor:pointer;line-height:1.1}
#strip button.rec{border-color:#f2994a}
#strip button.done{background:#2bb673;color:#fff}
#strip button.part{background:#a8e0c6}
#strip button.cur{outline:2px solid #1d232b;outline-offset:1px}
#strip button.g1{box-shadow:inset 0 -4px 0 #f2c94c}#strip button.g2{box-shadow:inset 0 -4px 0 #e5484d}
#plan{display:flex;flex-direction:column;gap:6px}
.step{display:grid;grid-template-columns:1fr auto;gap:2px 8px;border:1px solid var(--line);border-radius:10px;padding:7px 9px;cursor:pointer;align-items:center}
.step.cur{border-color:var(--ink);box-shadow:0 0 0 1px var(--ink)}
.step small{color:var(--mute);grid-column:1/-1}
.ok{color:#1f8f5f;font-weight:700}.todo{color:#c26a1b;font-weight:700}
@media (max-width:820px)''')
rep('<div>\n   <h2>Appartements</h2>',
    '''<div>
   <h2>Images à préciser</h2>
   <div id="plan"></div>
   <div class="hint" style="margin-top:6px">Sur chacune, ne retouchez que les sommets qui s'écartent de la face intérieure du mur (ou validez l'image si tout est juste). Les 26 autres images se recalculent toutes seules entre vos images.</div>
  </div>

  <div>
   <h2>Appartements</h2>''')

# ---------------------------------------------------------------- navigation
rep('function setImage(src,name){\n  const im=new Image();im.onload=()=>{S.w=im.naturalWidth;S.h=im.naturalHeight;img.src=src;img.width=S.w;img.height=S.h;$("#imgInfo").textContent=`${name||"image"} · ${S.w}×${S.h}`;fit()};im.src=src;\n}',
    '''function setImg(){img.src=FRAME_URIS[S.f];img.width=S.w;img.height=S.h}
function stateLabel(f){
  if(f===0)return `<span style='color:#2f80ed'>référence (tracée)</span>`;
  const n=doneCount(f),N=nLots();
  if(n>=N)return `<span class="ok">précisée ✓</span>`;
  if(n>0)return `<span class="ok">${n}/${N} lots précisés</span>`;
  return REC.includes(f)?`<span class="todo">à préciser</span>`:`<span style='color:#6b7683'>calculée</span>`;
}
function updBar(){
  $("#fslide").value=S.f;
  const g=GAP[S.f],hasKeys=Object.keys(KP).length>1;
  const orb=MODEL.mode==="orbit";
  $("#flabel").innerHTML=`<b>Image ${S.f} / ${NF-1}</b> · ${stateLabel(S.f)}`+(orb&&MODEL.perKey[S.f]!==undefined?` · écart de votre tracé avec le modèle : ${MODEL.perKey[S.f].toFixed(1)} px en moyenne`:(!orb&&hasKeys&&!KP[S.f]?` · écart entre les 2 reports : ${g.toFixed(1)} px`:""));
  $("#modelInfo").innerHTML=orb?`<b>Modèle de caméra ajusté sur vos tracés</b> : erreur moyenne ${MODEL.rms.toFixed(1)} px (focale ${MODEL.focale.toFixed(0)}, élévation ${MODEL.elev.toFixed(0)}°). Un tracé dont l'écart est nettement plus grand que les autres est probablement à reprendre.`:(MODEL.fail!==null?`<span class="todo">Le modèle de caméra ne colle pas à vos tracés (erreur ${MODEL.fail.toFixed(1)} px) : calcul de secours utilisé. Vérifiez que les mêmes sommets sont tracés sur les images précisées.</span>`:"Le modèle de caméra se calcule dès que 2 images sont précisées en plus de l'image 0 ; d'ici là le report automatique simple est utilisé.");
  const todo=REC.filter(f=>!isDone(f)).length;
  $("#imgInfo").textContent=todo?`${todo} image(s) à préciser`:"Les 4 images sont précisées ✓";
  let s="";
  for(let f=0;f<NF;f++){
    const cls=[REC.includes(f)?"rec":"",isDone(f)?"done":(doneCount(f)?"part":""),f===S.f?"cur":"",hasKeys&&!KP[f]?(GAP[f]>(orb?14:8)?"g2":GAP[f]>(orb?8:4)?"g1":""):""].join(" ");
    s+=`<button class="${cls}" data-f="${f}" title="Image ${f}${REC.includes(f)?" · à préciser":""}${hasKeys&&!KP[f]?(orb?` · correction ${GAP[f].toFixed(1)} px`:` · écart ${GAP[f].toFixed(1)} px`):""}">${f}</button>`;
  }
  $("#strip").innerHTML=s;
  $("#plan").innerHTML=REC.map(f=>`<div class="step${f===S.f?" cur":""}" data-f="${f}"><b>Image ${f}</b><span>${stateLabel(f)}</span><small>${f===0?"Votre tracé de départ (rotation 0°)":`Rotation ${(f*12)}°`+(orb&&MODEL.perKey[f]!==undefined?` · écart avec le modèle : ${MODEL.perKey[f].toFixed(1)} px`:(!orb&&hasKeys&&!KP[f]?` · écart des 2 reports : ${GAP[f].toFixed(1)} px`:""))}</small></div>`).join("");
  document.querySelectorAll("#strip button,#plan .step").forEach(b=>b.onclick=()=>gotoFrame(+b.dataset.f));
}
function gotoFrame(n){
  n=((n%NF)+NF)%NF;S.draft=null;if(S.mode==="draw")S.mode="edit";sync();S.f=n;S.lots=lotsOf(n);S.selV=null;
  if(S.sel&&!S.lots[S.sel])S.sel=null;setImg();updBar();render();
}''')
rep('<button class="btn" id="openImg">Ouvrir une image…</button>\n    <input type="file" id="fileImg" accept="image/*" hidden>\n    ', '')
rep('$("#openImg").onclick=()=>$("#fileImg").click();\n$("#fileImg").onchange=e=>{const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=()=>setImage(r.result,f.name);r.readAsDataURL(f)};\n', '')

# ---------------------------------------------------------------- restrictions : topologie sur l'image 0 seulement
rep('$("#mDraw").onclick=()=>{if(!S.sel){toast("Sélectionnez ou ajoutez un lot d\'abord");return}startDraw(S.sel)};',
    '$("#mDraw").onclick=()=>{if(S.f!==0){toast("Le tracé se fait sur l\'image 0 (référence)");return}if(!S.sel){toast("Sélectionnez ou ajoutez un lot d\'abord");return}startDraw(S.sel)};')
rep('$("#addLot").onclick=()=>{\n', '$("#addLot").onclick=()=>{\n  if(S.f!==0){toast("Ajout de lot possible sur l\'image 0 uniquement");return}\n')
rep('if(t.dataset&&t.dataset.edge){const[id,i]=t.dataset.edge.split(":");snapshot();',
    'if(t.dataset&&t.dataset.edge){if(S.f!==0){toast("Sur cette image, on ne fait que déplacer les sommets");return}const[id,i]=t.dataset.edge.split(":");snapshot();')
rep('function deleteVertex(id,i){const l=S.lots[id];',
    'function deleteVertex(id,i){if(S.f!==0){toast("Suppression de sommet possible sur l\'image 0 uniquement");return}const l=S.lots[id];')
rep('d.querySelector(".x").onclick=e=>{e.stopPropagation();snapshot();',
    'd.querySelector(".x").onclick=e=>{e.stopPropagation();if(S.f!==0){toast("Suppression de lot possible sur l\'image 0 uniquement");return}snapshot();')

# ---------------------------------------------------------------- validation des modifications
rep('view.addEventListener("pointerup",()=>{if(drag){if(!drag.whole||drag.moved){save()}drag=null}pan=null});',
    'view.addEventListener("pointerup",()=>{if(drag){if(!drag.whole||drag.moved){commitKey(drag.whole?drag.ids:[drag.id]);save()}drag=null}pan=null});')
rep('if(m){e.preventDefault();snapshot();l.pts[i]=[r1(l.pts[i][0]+m[0]),r1(l.pts[i][1]+m[1])];save();render()}',
    'if(m){e.preventDefault();snapshot();l.pts[i]=[r1(l.pts[i][0]+m[0]),r1(l.pts[i][1]+m[1])];commitKey([id]);save();render()}')
rep('/* ---------- boutons ---------- */',
    '''/* ---------- boutons ---------- */
$("#fprev").onclick=()=>gotoFrame(S.f-1);$("#fnext").onclick=()=>gotoFrame(S.f+1);
$("#fslide").oninput=e=>gotoFrame(+e.target.value);
$("#fnextk").onclick=()=>{const n=REC.filter(f=>!isDone(f));
  if(!n.length){toast("Les 4 images sont précisées ✓");return}
  gotoFrame(n.find(f=>f>S.f)??n[0])};
$("#snapKey").onchange=()=>{recompute();gotoFrame(S.f)};
$("#fok").onclick=()=>{if(S.f===0){toast("L'image 0 est votre tracé de référence");return}snapshot();commitKey();save();render();toast(`Image ${S.f} validée`)};''')
rep('if(e.key==="0"){fit();return}',
    'if(e.key==="0"){fit();return}\n  if(e.key==="PageDown"||e.key==="."){gotoFrame(S.f+1);return}\n  if(e.key==="PageUp"||e.key===","){gotoFrame(S.f-1);return}')

# ---------------------------------------------------------------- export / import
old = t[t.index('function payload(){'):t.index('$("#exp").onclick')]
t = t.replace(old, '''function payload(){
  sync();
  const out={level:$("#level").value,image:{width:S.w,height:S.h},lots:{},keyframes:Object.keys(KP).map(Number).sort((a,b)=>a-b),keys:KP,model:{mode:MODEL.mode,rms:MODEL.rms,focale:MODEL.focale,elevation_deg:MODEL.elev},frames:{}};
  for(const id of Object.keys(KP[0]).sort((a,b)=>a-b)){if(KP[0][id].length>=3)out.lots[id]={typo:TYPO[id],points:KP[0][id]}}
  for(let k=0;k<NF;k++){out.frames[k]={};for(const id in out.lots)out.frames[k][id]=F[k][id]}
  return out;
}
''')
old = t[t.index('$("#fileJson").onchange'):t.index('window.addEventListener("resize"')]
t = t.replace(old, '''$("#fileJson").onchange=e=>{const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=()=>{try{const d=JSON.parse(r.result);
  let kp=d.keys;
  if(!kp&&d.frames&&d.keyframes){kp={};for(const k of d.keyframes)if(d.frames[k])kp[k]=d.frames[k]}
  if(!kp||!kp[0]){toast("Ce fichier ne contient pas les images clés");return}
  snapshot();KP=kp;for(const id in d.lots)TYPO[id]=d.lots[id].typo;if(d.level)$("#level").value=d.level;
  recompute();S.sel=null;gotoFrame(S.f);save();toast("Tracé importé")}catch(err){toast("Fichier invalide")}};r.readAsText(f)};
''')
rep('load();setImage(DEFAULT_IMG,"R+1 · image 0");', 'load();setImg();updBar();fit();')
rep('<h1>Éditeur de polygones</h1><div class="hint">Tracez les appartements une seule fois sur l\'image 0 : le tracé est ensuite reporté sur toutes les autres images.</div>',
    '<h1>Contrôle des polygones</h1><div class="hint">Précisez les polygones sur 4 images (tous les ~90°). Les autres images se calculent entre elles : plus vous êtes précis sur ces 4 images, plus les 26 autres le sont.</div>')
rep('<label class="row"><input type="checkbox" id="showNum" checked> Afficher les numéros</label>',
    '<label class="row"><input type="checkbox" id="showNum" checked> Afficher les numéros</label>\n   <label class="row" title="Coché : vos tracés sont reproduits exactement sur vos images. Décoché : le modèle de caméra lisse les petites irrégularités de tracé."><input type="checkbox" id="snapKey" checked> Coller à mes tracés</label>')
rep('<div id="plan"></div>', '<div id="plan"></div>\n   <div class="hint" id="modelInfo" style="margin-top:6px"></div>')
rep('<h2>Niveau / image</h2>', '<h2>Niveau</h2>')
t = t.replace('<title>Éditeur de polygones</title>', '<title>Contrôle des polygones</title>')

# ---------------------------------------------------------------- injection
user = json.load(open(USER, encoding='utf8'))
al = json.load(open(ALIGN))
N = al['N']
Hc = [np.array(h, float) for h in al['H']] + [np.eye(3)]
HC = [(h / h[2, 2]).reshape(9).tolist() for h in Hc]
pf = json.load(open(PF))
prop = [pf[str(k)] for k in range(N)]
typo = {k: v['typo'] for k, v in user['lots'].items()}
uris = []
for k in range(N):
    im = Image.open(os.path.join(FRAMES, f'r1_{k:02d}.jpg')).convert('RGB').resize((1600, 900), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, 'JPEG', quality=78)
    uris.append('data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode())
for a, b in (('__FRAMEURIS__', uris), ('__PROP__', prop), ('__TYPO__', typo), ('__HC__', HC), ('__REC__', REC)):
    t = t.replace(a, json.dumps(b))
open(os.path.join(OUT, 'controle-polygones.html'), 'w', encoding='utf8').write(t)
print('ok', len(t) // 1024, 'KB')
