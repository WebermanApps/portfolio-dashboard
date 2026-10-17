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
def tile(l):  # agent-dashboards-01 pick A: Icon Row (each linked dashboard as a small icon tile)
    live_t=live and l['slug'] in subdash.LIVE
    sub="Private, Tap To Unlock" if live_t else "Locked, Setting Up"
    inner=f'<span class="ib">{ic(l["icon"])}</span><b>{e(l["name"])}</b>{pill(l["status"])}<svg class="ic clk" viewBox="0 0 24 24" aria-hidden="true">{I["lock"]}</svg>'
    return f'<a class="itile mw-hover" href="s/{l["slug"]}.html?v={V}" title="{e(l["name"])}: {sub}" aria-label="{e(l["name"])}, {e(l["status"])}, {sub}">{inner}</a>' if live_t else f'<div class="itile off" aria-disabled="true" title="{e(l["name"])}: {sub}">{inner}</div>'
lanes=''.join(tile(l) for l in d['lanes'])
h=datetime.datetime.now().hour
# Morning Report only (Evening Report retired Oct 14 2026). Never auto-relabel to Evening.
rt=d.get('report',{}).get('title') or 'Morning Report'
if not rt.startswith('Fresh Start'):
    rt=rt.replace('Evening Report','Morning Report')
    if 'Morning Report' not in rt and not rt.startswith('Fresh Start'): rt='Morning Report'
RI=d.get('report',{}).get('morning',[])
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
# R106 audit (Oct 17 2026): the Decisions Waiting On Max block was merged into the To-Do (data.json todo) and removed.
rec=''.join(row(e(x),'Oct 13',e(x)) for x in d['recent'])
# R106 (Max Oct 17 2026): To-Do List fold-down, closed by default, directly under the Morning Report. Names + statuses only (no figures).
# Exactly one block carries data-mw-slot="todo"; the shared kit (mw-layout.js) moves it into the branded header. Source: data.json "todo".
TD=d.get('todo',[])
todo=(f'<details class="alerts todo" id="todos" data-mw-slot="todo" data-mw-todo-title="To-Do List" data-mw-todo-count="{len(TD)}"><summary><span class="eyebrow">To-Do List</span> <span class="tag w">{len(TD)} Open</span></summary><div class="ai"><ul class="rows">'
      +''.join(row(e(x["t"]),pill(x["s"]),(e(x["det"])+' ' if x.get("det") else '')+f'Status: {e(x["s"])}. Owner: Portfolio.') for x in TD)+'</ul></div></details>') if TD else ''
rou=''  # R65: Routines now render from routines.json via the shared kit component
# R65 routines.json (names, groups, ICT schedules only; no figures, no secrets)
json.dump({'updated':datetime.datetime.now().strftime('%Y-%m-%d %H:%M ICT'),'routines':[{k:r[k] for k in ('name','group','schedule_plain','status','last_run') if r.get(k)} for r in d['routines']]},open('routines.json','w'),indent=1)
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
decks=''  # R66: unfinished decks render inside the Ready To Swipe shelf (shelf.json pinned), not as a separate pin
# R66 Ready To Swipe: sync unfinished (newest first) into shelf.json pinned so the 5-cap counts them
try: SH=json.load(open('shelf.json'))
except Exception: SH={'agent':'portfolio','decks':[],'pinned':[],'done':[]}
SH.setdefault('agent','portfolio'); SH.setdefault('decks',[]); SH.setdefault('done',[])
SH['pinned']=[{'name':x['name'],'url':x['url'],'answered':int(x.get('answered',0))} for x in unfin]
SH['updated']=datetime.datetime.now().astimezone().isoformat(timespec='seconds')
json.dump(SH,open('shelf.json','w'),indent=1)

# Bills Calendar (names + due dates only; every date sourced from a file, est = projected)
import calendar
BL=d.get('bills',[]); _t=datetime.date.today()
_ms=[(_t.year,_t.month),((_t.year+(_t.month==12)),(_t.month%12)+1)]
def _bm(y,m):
    cells=''.join('<div class="bc x"></div>' for _ in range(calendar.monthrange(y,m)[0]))
    for dd in range(1,calendar.monthrange(y,m)[1]+1):
        ds=f'{y:04d}-{m:02d}-{dd:02d}'; it=[x for x in BL if x['date']==ds]
        tod=' today' if datetime.date(y,m,dd)==_t else ''
        cells+=f'<div class="bc{tod}"><span class="bd">{dd}</span>'+''.join(f'<span class="bi k-{e(x["kind"])}{" est" if x["est"] else ""}" title="{e(x["name"])}{" (Estimated)" if x["est"] else ""}">{e(x["name"])}{"<i>Est.</i>" if x["est"] else ""}</span>' for x in it)+'</div>'
    hd=''.join(f'<div class="bh">{w}</div>' for w in ('Mon','Tue','Wed','Thu','Fri','Sat','Sun'))
    return f'<div class="bmon"><h3>{calendar.month_name[m]} {y}</h3><div class="bgrid">{hd}{cells}</div></div>'
_inm=[x for x in BL if (int(x['date'][:4]),int(x['date'][5:7])) in _ms]
_li=''.join(f'<li class="{"past" if x["date"]<_t.isoformat() else ""}"><span>{e(x["name"])}{" <i>Est.</i>" if x["est"] else ""}</span><span class="dt">{datetime.date.fromisoformat(x["date"]).strftime("%a %b %-d")}</span></li>' for x in _inm)
_later=[x for x in BL if x['date']>f'{_ms[1][0]:04d}-{_ms[1][1]:02d}-31']
_lt=(' <span class="blater">Later: '+' · '.join(f'{e(x["name"])} {datetime.date.fromisoformat(x["date"]).strftime("%b %-d")}' for x in _later)+'</span>') if _later else ''
bills=f'<section id="bills" aria-label="Bills Calendar"><h2>Bills Calendar</h2><div class="blg"><span class="k-card bi">Card</span><span class="k-loan bi">Loan</span><span class="k-rent bi">Rent In</span><span class="k-ins bi">Insurance / Tax</span><span><i>Est.</i> = projected from last stated date</span></div><div class="bcal">{"".join(_bm(y,m) for y,m in _ms)}</div><ul class="blist">{_li}</ul><p class="bnote">Names and due dates only.{_lt}</p></section>'
page=open('template.html').read()
for k,v in dict(REPORT=rep,STATUS=e(d['status']),UPDATED=e(d['updated']),LANES=lanes,OPEN=opn,REC=rec,ROU=rou,LNK=lnk,SHARE=ic('share'),BUILD=V,MYAPPS=myapps,GREET=GREET,DECKS=decks,BILLS=bills,TODO=todo).items(): page=page.replace('{{'+k+'}}',v)
# privacy guard: no money figures or account-like numbers
if re.search(r'\$\s?\d|\d[\d,]*\.\d{2}\b|\b(?!20[0-9]{2}\b)\d{4,}\b|\d+(\.\d+)?\s?%|\d+k\b',re.sub(r'<[^>]+>','',re.sub(r'(?s)<(style|script|svg).*?</\1>','',page))):
    sys.exit('PRIVACY GUARD: possible figure found; not publishing')
open('index.html','w').write(page)

# Public report meta (no figures): Morning Report publish + update.sh land here (Evening Report retired Oct 14 2026)
_now=datetime.datetime.now()
# Morning Report only — never write Evening Report (retired). Prefer env from morning script; default Morning Report.
_rtype=os.environ.get('PORTFOLIO_REPORT_TYPE') or 'Morning Report'
if 'Evening' in _rtype: _rtype='Morning Report'
if 'Morning' not in _rtype and not _rtype.startswith('Fresh'): _rtype='Morning Report'
json.dump({'type':_rtype,'posted_at':_now.strftime('%Y-%m-%dT%H:%M:%S+07:00'),'posted_ict':_now.strftime('%b %-d, %Y, %-I:%M %p ICT'),'late':(_now.hour,_now.minute)>(5,0)},open('report.json','w'),indent=1)

if os.environ.get('PORTFOLIO_DASH_PREVIEW_PASSWORD'):  # local-only preview with live tiles
    live=True; lanes=''.join(tile(l) for l in d['lanes']); p=open('template.html').read()
    for k,v in dict(REPORT=rep,STATUS=e(d['status']),UPDATED=e(d['updated']),LANES=lanes,OPEN=opn,REC=rec,ROU=rou,LNK=lnk,SHARE=ic('share'),BUILD=V,MYAPPS=myapps,GREET=GREET,DECKS=decks,BILLS=bills,TODO=todo).items(): p=p.replace('{{'+k+'}}',v)
    import shutil; open(subdash.PRIV+'/preview/index.html','w').write(p); shutil.copy('brand-tokens.css',subdash.PRIV+'/preview/')
print('built',d['updated'],'| sub-dashboards:',state)
