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
    inner=f'{ic(l["icon"])}<span><b>{e(l["name"])}</b><small>{"Private, Tap To Unlock" if live_t else "Locked, Setting Up"}</small></span>{pill(l["status"])}<svg class="ic clk" viewBox="0 0 24 24" aria-label="Locked">{I["lock"]}</svg>'
    return f'<a class="trow mw-hover" href="s/{l["slug"]}.html?v={V}">{inner}</a>' if live_t else f'<div class="trow off" aria-disabled="true">{inner}</div>'
lanes=''.join(tile(l) for l in d['lanes'])
h=datetime.datetime.now().hour
rt=d.get('report',{}).get('title') or ('Morning Report' if h<12 else 'Evening Report')
RI=d.get('report',{}).get('morning' if h<12 else 'evening',[])
if not rt.startswith('Fresh Start'): rt=rt.replace('Morning Report','Evening Report') if h>=12 else rt.replace('Evening Report','Morning Report')
TI={'Portfolio':('s/portfolio.html','chart'),'Spending':('s/spending.html','receipt'),'Finance Review':('https://github.com/WebermanApps/finance-review','doc')}
def tileurl(x):
    for k,(u,i) in TI.items():
        if x.split(':',1)[1].strip().lower().startswith(k.lower()+' ') or k.lower() in x.lower()[:40]: return k,(u+'?v='+V if u.startswith('s/') else u),i
    return None
if rt.startswith('Fresh Start'):
    rdy=[x for x in RI if x.lower().startswith('ready:')]; wt=[x.split(':',1)[1].strip() for x in RI if x.lower().startswith('waiting')]
    tl=''
    for x in rdy[:3]:
        m=tileurl(x)
        if m: tl+=f'<a class="fst-tile mw-hover" href="{e(m[1])}">{ic(m[2])}<b>{e(m[0])}</b><span>Ready now</span></a>'
    rep=f'<details class="alerts report fs1"><summary><span class="eyebrow">{e(rt)}</span> <span class="tag g">{len(rdy)} Ready</span> <span class="tag w">{len(wt)} Waiting</span></summary><div class="ai"><div class="fst-tiles">{tl}</div><ul class="wl">'+''.join(f'<li>Waiting on you: {e(x)}</li>' for x in wt)+'</ul></div></details>'
else:
    rep=f'<section class="rep report" aria-label="{e(rt)}"><div class="eyebrow">{len(RI)} Updates</div><h3>{e(rt)}</h3><ol class="ev">'+''.join(f'<li>{e(x)}</li>' for x in RI)+'</ol></section>'
GREET='Good Morning, Max' if h<12 else ('Good Afternoon, Max' if h<17 else 'Good Evening, Max')
row=lambda t,right,det:f'<li><details><summary><span>{t}</span><span class="dt">{right}</span></summary><div class="det">{det}</div></details></li>'
opn=''.join(row(e(o["t"]),pill(o["s"]),f'Status: {e(o["s"])}. Owner: Portfolio.') for o in d['open'])
dec=''.join(row(e(x),pill("Waiting on Max"),'Needs your answer; Portfolio follows up once you reply.') for x in d['decisions'])
rec=''.join(row(e(x),'Oct 13',e(x)) for x in d['recent'])
rou=''.join(row(e(r["n"]),e(r["w"]),f'{e(r["n"])} runs {e(r["w"])}.') for r in d['routines'])
lnk=''.join(f'<a class="link mw-hover" href="{e(l["u"])}" target="_blank" rel="noopener">{ic("lock")}<span><b>{e(l["n"])}</b><br><small>{e(l["l"])}</small></span></a>' for l in d['links'])
MY=[('Portfolio',f's/portfolio.html?v={V}','chart','Private'),('Spending',f's/spending.html?v={V}','receipt','Private'),('Finance Review','https://github.com/WebermanApps/finance-review','doc','Private Repo')]
myapps=''.join(f'<a class="app mw-hover" href="{e(u)}">{ic(i)}<b>{e(n)}</b><small>{e(s)}</small></a>' for n,u,i,s in MY)
# R63: pin unfinished decks at top (newest first). Finished = submitted/done.
DONE={'submitted','done','finished'}
unfin=[x for x in d.get('decks',[]) if str(x.get('status','')).lower() not in DONE]
unfin=list(reversed(unfin))  # data.json append order = oldest→newest
def drow(x):
    prog=f'{int(x.get("answered",0))} of {int(x.get("total",0))}'
    return f'<a class="drow mw-hover" href="{e(x["url"])}"><b>{e(x["name"])}</b><span class="dprog">{e(prog)}</span></a>'
decks=('' if not unfin else
  '<section class="decks-pin" aria-label="Decks To Finish"><h2>Decks To Finish</h2><div class="drows">'
  +''.join(drow(x) for x in unfin)+'</div></section>')
page=open('template.html').read()
for k,v in dict(REPORT=rep,STATUS=e(d['status']),UPDATED=e(d['updated']),LANES=lanes,OPEN=opn,DEC=dec,REC=rec,ROU=rou,LNK=lnk,SHARE=ic('share'),BUILD=V,MYAPPS=myapps,NDEC=str(len(d['decisions'])),GREET=GREET,DECKS=decks).items(): page=page.replace('{{'+k+'}}',v)
# privacy guard: no money figures or account-like numbers
if re.search(r'\$\s?\d|\d[\d,]*\.\d{2}\b|\b(?!20[0-9]{2}\b)\d{4,}\b|\d+(\.\d+)?\s?%|\d+k\b',re.sub(r'<[^>]+>','',re.sub(r'(?s)<(style|script|svg).*?</\1>','',page))):
    sys.exit('PRIVACY GUARD: possible figure found; not publishing')
open('index.html','w').write(page)

# Public report meta (no figures): morning/evening publish + update.sh both land here
_now=datetime.datetime.now()
_rtype=os.environ.get('PORTFOLIO_REPORT_TYPE') or ('Morning Report' if 'Morning' in rt else ('Evening Report' if 'Evening' in rt else ('Morning Report' if _now.hour<12 else 'Evening Report')))
json.dump({'type':_rtype,'posted_at':_now.strftime('%Y-%m-%dT%H:%M:%S+07:00'),'posted_ict':_now.strftime('%b %-d, %Y, %-I:%M %p ICT')},open('report.json','w'),indent=1)

if os.environ.get('PORTFOLIO_DASH_PREVIEW_PASSWORD'):  # local-only preview with live tiles
    live=True; lanes=''.join(tile(l) for l in d['lanes']); p=open('template.html').read()
    for k,v in dict(REPORT=rep,STATUS=e(d['status']),UPDATED=e(d['updated']),LANES=lanes,OPEN=opn,DEC=dec,REC=rec,ROU=rou,LNK=lnk,SHARE=ic('share'),BUILD=V,MYAPPS=myapps,NDEC=str(len(d['decisions'])),GREET=GREET,DECKS=decks).items(): p=p.replace('{{'+k+'}}',v)
    import shutil; open(subdash.PRIV+'/preview/index.html','w').write(p); shutil.copy('brand-tokens.css',subdash.PRIV+'/preview/')
print('built',d['updated'],'| sub-dashboards:',state)
