"""Build the claude.ai artifact copy of index.html.
usage: python3 tools/build_artifact.py tools/artifact_files.json /abs/path/out/index.html
The artifact already holds 512 files (its cap): artifact_files.json lists them. Any image the page uses that is not in that list is inlined as base64; GBI/HSI helper images too; downloads point to the live site."""
# Build the artifact copy of index.html: inline every referenced image the artifact lacks (512-file cap),
# point downloads at the live GitHub site.
import base64,json,re,sys,glob,os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
have=set(json.load(open(sys.argv[1])))
s=open('index.html').read()
LIVE='https://tigrestudiodesign.github.io/'
mime={'webp':'image/webp','png':'image/png','jpg':'image/jpeg','svg':'image/svg+xml'}
n=0;sz=0
# static paths
for f in sorted(set(re.findall(r"img/[\w\-]+\.(?:webp|png|jpg|svg)",s))):
    if f in have or not os.path.exists(f): continue
    if f=='img/og-card.jpg' or f.startswith('img/bm__') or f.startswith('img/kh__') or f.startswith('img/ff__') or f.startswith('img/cn__') or f.startswith('img/ml') or f=='img/henry-portrait.webp': continue
    b='data:%s;base64,%s'%(mime[f.rsplit('.',1)[1]],base64.b64encode(open(f,'rb').read()).decode())
    s=s.replace("'%s'"%f,"'%s'"%b).replace('"%s"'%f,'"%s"'%b); n+=1; sz+=len(b)
# dynamic helpers like GBI('02') -> 'img/gb__'+f+'.webp': provide a lookup map for missing files of that prefix
for pre,helper in (('gb','GBI'),('hs','HSI')):
    miss=[f for f in glob.glob('img/%s__*.webp'%pre) if f not in have]
    if miss:
        m={os.path.basename(f)[len(pre)+2:-5]:'data:image/webp;base64,'+base64.b64encode(open(f,'rb').read()).decode() for f in miss}
        a="const %s=(f,w,h,c)=>['img/%s__'+f+'.webp',"%(helper,pre)
        assert a in s,helper
        s=s.replace(a,"const %sM=%s;\nconst %s=(f,w,h,c)=>[%sM[f]||'img/%s__'+f+'.webp',"%(helper,json.dumps(m),helper,helper,pre),1); n+=len(m); sz+=sum(map(len,m.values()))
# Kinetic Hexagon page builds paths as R('kh__name') -> 'img/kh__name.webp': embed the ones the artifact lacks
khm=[f for f in sorted(glob.glob('img/kh__*.webp')) if f not in have]
if khm:
    from PIL import Image
    import io
    def small(f):  # artifact-only copy: the index.html cap is 16 MiB, so embed lighter versions
        im=Image.open(f).convert('RGB');mx=1200 if 'timelapse' in f else 900 if 'gh_steps' in f else 1050
        if im.width>mx: im=im.resize((mx,round(im.height*mx/im.width)),Image.LANCZOS)
        bb=io.BytesIO();im.save(bb,'WEBP',quality=62,method=6);return bb.getvalue()
    m={os.path.basename(f)[:-5]:'data:image/webp;base64,'+base64.b64encode(small(f)).decode() for f in khm}
    a="const R=(f,w=1920,h=1080)=>['img/'+f+'.webp',w,h];"
    assert a in s,'KH R()'
    s=s.replace(a,"const KHM=%s;const R=(f,w=1920,h=1080)=>[KHM[f]||'img/'+f+'.webp',w,h];"%json.dumps(m),1); n+=len(m); sz+=sum(map(len,m.values()))
    # full-size canvas links open on the live site
    s=s.replace('<a href="img/kh__gh_sun.webp"','<a href="'+LIVE+'img/kh__gh_sun.webp"').replace('<a href="img/kh__gh_steps.webp"','<a href="'+LIVE+'img/kh__gh_steps.webp"')
    for k,v in m.items(): s=s.replace("'img/%s.webp'"%k,"'%s'"%v)
# BASECAMP manual pages: BMP(n) -> 'img/bm__pNN.webp' (lighter copies, artifact only)
bmm=[f for f in sorted(glob.glob('img/bm__p*.webp')) if f not in have]
if bmm:
    from PIL import Image
    import io
    def bsmall(f):
        im=Image.open(f).convert('RGB');mx=1300 if '_2x' in f else 1100
        if im.width>mx: im=im.resize((mx,round(im.height*mx/im.width)),Image.LANCZOS)
        bb=io.BytesIO();im.save(bb,'WEBP',quality=66,method=6);return 'data:image/webp;base64,'+base64.b64encode(bb.getvalue()).decode()
    m={os.path.basename(f)[5:-5]:bsmall(f) for f in bmm if '_2x' not in f}
    a="const BMP=n=>['img/bm__p'+String(n).padStart(2,'0')+'.webp',1600,1000];"
    assert a in s,'BMP'
    s=s.replace(a,"const BMPM=%s;const BMP=n=>[BMPM[String(n).padStart(2,'0')]||'img/bm__p'+String(n).padStart(2,'0')+'.webp',1600,1000];"%json.dumps(m),1)
    if 'img/bm__p05_2x.webp' in bmm: s=s.replace("'img/bm__p05_2x.webp'","'%s'"%bsmall('img/bm__p05_2x.webp'))
    n+=len(bmm); sz+=sum(map(len,m.values()))
# ff__/cn__/ml__/mlr__ images are NOT inlined: publish them as separate artifact files (see tools/artifact_extra_files.txt); cross-site images are blocked in the artifact viewer
# brand-book spreads built as TSP(n)
tsm=[f for f in sorted(glob.glob('img/ts__p*.webp')) if f not in have]
if tsm:
    m={str(int(os.path.basename(f)[5:7])):'data:image/webp;base64,'+base64.b64encode(open(f,'rb').read()).decode() for f in tsm}
    a="const TSP=n=>['img/ts__p'+String(n).padStart(2,'0')+'.webp',1600,900];"
    assert a in s
    s=s.replace(a,"const TSPM=%s;\nconst TSP=n=>[TSPM[n]||'img/ts__p'+String(n).padStart(2,'0')+'.webp',1600,900];"%json.dumps(m),1); n+=len(m); sz+=sum(map(len,m.values()))
# fonts the artifact lacks -> data URIs
for f in sorted(set(re.findall(r'url\((fonts/[^)]+\.woff2)\)',s))):
    if f not in have and os.path.exists(f):
        s=s.replace('url(%s)'%f,'url(data:font/woff2;base64,%s)'%base64.b64encode(open(f,'rb').read()).decode())
s=re.sub(r'href="(downloads/[^"]+\.pdf)" download',lambda m:'href="'+LIVE+m.group(1)+'" target="_blank" rel="noopener"',s)
# Tuned Air films: the artifact viewer may block video from another site, so show the poster and open the film on the live site
s=s.replace('<video class="ta-v" src="${f}" poster="${po}" width="${w}" height="${h}" muted loop playsinline autoplay preload="auto" aria-label="${esc(c)}"></video>',
 '<a class="ta-pl" href="'+LIVE+'#p11" target="_blank" rel="noopener"><img src="${po}" width="${w}" height="${h}" alt="${esc(c)}"><span>▶ Play film</span></a>')
s=s.replace('.ta-films video{','.ta-pl{position:relative;display:block}.ta-pl img{display:block;width:100%;height:100%;object-fit:cover}.ta-pl span{position:absolute;left:12px;bottom:12px;background:#FF5A1F;color:#0B0B0C;font:700 12px var(--mono);padding:6px 10px;letter-spacing:.06em}.ta-films video{')
# videos -> live site (not inlined)
s=re.sub(r'"(img/[^"]+\.mp4)"',lambda m:'"'+LIVE+m.group(1)+'"',s)
# downloads -> live site, opened in a new tab (the artifact viewer blocks downloads)
s=re.sub(r"'(downloads/[^']+\.pdf)'",lambda m:"'"+LIVE+m.group(1)+"'",s)
s=re.sub(r'(href="\$\{[A-Za-z_.]+\}") download',r'\1 target="_blank" rel="noopener"',s)
# any remaining download attribute (the viewer ignores it): open the file from the live site in a new tab instead
s=re.sub(r'(<a\b[^>]*?)\sdownload(?=[\s>])(?![^>]*target=)',r'\1 target="_blank" rel="noopener"',s)
s=re.sub(r'(<a\b[^>]*?)\sdownload(?=[\s>])',r'\1',s)
out=sys.argv[2] if len(sys.argv)>2 else 'artifact-index.html'
# Media pack: the artifact holds at most 512 files, so photo/CMF/material-library images ship in ONE json
# (data/media_pack.json, path -> data URI) that im() fills in on demand. Cross-site images are blocked in the viewer.
import glob as _g
PK_RE=r'^img\/(ff__|cn__|ml__|mlr__|henry-portrait)'
pack={}
for f in sorted(_g.glob('img/ff__*.webp')+_g.glob('img/cn__*.webp')+_g.glob('img/ml__*.webp')+_g.glob('img/mlr__*.webp')+['img/henry-portrait.webp']):
    pack[f]='data:image/webp;base64,'+base64.b64encode(open(f,'rb').read()).decode()
_od=os.path.join(os.path.dirname(os.path.abspath(out)),'data'); os.makedirs(_od,exist_ok=True)
json.dump(pack,open(os.path.join(_od,'media_pack.json'),'w'),separators=(',',':'))
_im_old="const im=(r,alt,cls='')=>`<img src=\"${r[0]}\""
assert _im_old in s, 'im() signature changed'
_pk="const PKR=/"+PK_RE+"/;let PKM=null,PKP=null;const pkLoad=()=>PKP||(PKP=fetch('data/media_pack.json').then(r=>r.json()).then(j=>{PKM=j;document.querySelectorAll('img[data-pk]').forEach(e=>{const v=PKM[e.dataset.pk];if(v){e.src=v;e.removeAttribute('data-pk')}})}).catch(()=>{}));new MutationObserver(()=>{if(document.querySelector('img[data-pk]')){if(PKM)document.querySelectorAll('img[data-pk]').forEach(e=>{const v=PKM[e.dataset.pk];if(v){e.src=v;e.removeAttribute('data-pk')}});else pkLoad()}}).observe(document.documentElement,{childList:true,subtree:true});\n"
s=s.replace(_im_old,_pk+"const im=(r,alt,cls='')=>`<img ${PKR.test(r[0])?(PKM&&PKM[r[0]]?'src=\"'+PKM[r[0]]+'\"':'data-pk=\"'+r[0]+'\" src=\"data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==\"'):'src=\"'+r[0]+'\"'}",1)
os.makedirs(os.path.dirname(os.path.abspath(out)),exist_ok=True); open(out,'w').write(s)
print('inlined',n,'bytes',sz,'total',len(s))
