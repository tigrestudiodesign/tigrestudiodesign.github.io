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
    if f=='img/og-card.jpg': continue
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
# downloads -> live site, opened in a new tab (the artifact viewer blocks downloads)
s=re.sub(r"'(downloads/[^']+\.pdf)'",lambda m:"'"+LIVE+m.group(1)+"'",s)
s=re.sub(r'(href="\$\{[A-Za-z_.]+\}") download',r'\1 target="_blank" rel="noopener"',s)
out=sys.argv[2] if len(sys.argv)>2 else 'artifact-index.html'
os.makedirs(os.path.dirname(os.path.abspath(out)),exist_ok=True); open(out,'w').write(s)
print('inlined',n,'bytes',sz,'total',len(s))
