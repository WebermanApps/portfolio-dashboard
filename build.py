import json,html,datetime,re,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); os.chdir(os.path.dirname(os.path.abspath(__file__)))
import subdash
state=subdash.build()  # 'published' | 'existing' | 'setup'
live=state in('published','existing')
d=json.load(open('data.json'))
d['updated']=datetime.datetime.now().strftime('%b %-d, %Y, %-I:%M %p ICT')
json.dump(d,open('data.json','w'),indent=1)
e=html.escape
V=datetime.datetime.now().strftime('%Y%m%d%H%M%S')  # cache-busting build id
I={'chart':'<path d="M3 20h18M6 16l4-5 3 3 5-7"/>','receipt':'<path d="M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6"/>','card':'<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M3 10h18"/>','doc':'<path d="M7 3h7l4 4v14H7zM14 3v4h4M10 12h5M10 16h5"/>','house':'<path d="M4 11l8-7 8 7v9H4zM10 20v-5h4v5"/>','check':'<circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-6"/>','clock':'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>','lock':'<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/>','share':'<path d="M12 3v12M7 8l5-5 5 5M5 14v6h14v-6"/>'}
ic=lambda k:f'<svg class="ic" viewBox="0 0 24 24" aria-hidden="true">{I[k]}</svg>'
cls=lambda s:{'Done':'done','In Progress':'prog','Waiting on Max':'wait'}[s]
pill=lambda s:f'<span class="pill {cls(s)}">{e(s)}</span>'
def tile(l):
    live_t=live and l['slug'] in subdash.LIVE
    inner=f'{ic(l["icon"])}<div class="tb"><h3>{e(l["name"])}</h3><p>{e(l["note"])}</p><div class="tf">{pill(l["status"])}<span class="lk">{ic("lock")}{"Private, Tap To Open" if live_t else "Locked, Setting Up"}</span></div></div>'
    return f'<a class="card tile mw-hover" href="s/{l["slug"]}.html?v={V}">{inner}</a>' if live_t else f'<div class="card tile off" aria-disabled="true">{inner}</div>'
lanes=''.join(tile(l) for l in d['lanes'])
h=datetime.datetime.now().hour
rt=d.get('report',{}).get('title') or ('Morning Report' if h<12 else 'Evening Report')
RI=d.get('report',{}).get('morning' if h<12 else 'evening',[])
rep=f'<details class="alerts report"><summary><span class="eyebrow">{rt}</span> <span class="tag">{len(RI)} Updates</span></summary><div class="ai"><ul>'+''.join(f'<li>{e(x)}</li>' for x in RI)+'</ul></div></details>'
opn=''.join(f'<li><span>{e(o["t"])}</span>{pill(o["s"])}</li>' for o in d['open'])
dec=''.join(f'<li><span>{e(x)}</span>{pill("Waiting on Max")}</li>' for x in d['decisions'])
rec=''.join(f'<li>{e(x)}</li>' for x in d['recent'])
rou=''.join(f'<li>{ic("clock")}<span><b>{e(r["n"])}</b><br><small>{e(r["w"])}</small></span></li>' for r in d['routines'])
lnk=''.join(f'<a class="link mw-hover" href="{e(l["u"])}" target="_blank" rel="noopener">{ic("lock")}<span><b>{e(l["n"])}</b><br><small>{e(l["l"])}</small></span></a>' for l in d['links'])
page=open('template.html').read()
for k,v in dict(REPORT=rep,STATUS=e(d['status']),UPDATED=e(d['updated']),LANES=lanes,OPEN=opn,DEC=dec,REC=rec,ROU=rou,LNK=lnk,SHARE=ic('share'),BUILD=V).items(): page=page.replace('{{'+k+'}}',v)
# privacy guard: no money figures or account-like numbers
if re.search(r'\$\s?\d|\d[\d,]*\.\d{2}\b|\b(?!20[0-9]{2}\b)\d{4,}\b|\d+(\.\d+)?\s?%|\d+k\b',re.sub(r'<[^>]+>','',re.sub(r'(?s)<(style|script|svg).*?</\1>','',page))):
    sys.exit('PRIVACY GUARD: possible figure found; not publishing')
open('index.html','w').write(page)
if os.environ.get('PORTFOLIO_DASH_PREVIEW_PASSWORD'):  # local-only preview with live tiles
    live=True; lanes=''.join(tile(l) for l in d['lanes']); p=open('template.html').read()
    for k,v in dict(REPORT=rep,STATUS=e(d['status']),UPDATED=e(d['updated']),LANES=lanes,OPEN=opn,DEC=dec,REC=rec,ROU=rou,LNK=lnk,SHARE=ic('share')).items(): p=p.replace('{{'+k+'}}',v)
    import shutil; open(subdash.PRIV+'/preview/index.html','w').write(p); shutil.copy('brand-tokens.css',subdash.PRIV+'/preview/')
print('built',d['updated'],'| sub-dashboards:',state)
