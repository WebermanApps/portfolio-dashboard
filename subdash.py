#!/usr/bin/env python3
"""Build the six private sub-dashboards. Plaintext goes ONLY to ../dashboard-private (outside the repo).
Encrypted pages (AES-256-GCM, PBKDF2-SHA256 600k) are written to s/ only when PORTFOLIO_DASH_PASSWORD is set."""
import csv,json,glob,re,base64,os,hashlib,datetime as dt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
HERE=os.path.dirname(os.path.abspath(__file__)); F='/workspace/ops/folio'; PRIV=F+'/dashboard-private'
PAGES=[('portfolio','Portfolio'),('spending','Spending'),('bills','Cards And Bills'),('taxes','Taxes'),('rentals','Rentals Finance'),('upkeep','Smart UpKeep Model')]
ITER=600000
LIVE=('portfolio','spending')  # only these are published; the rest stay Locked, Setting Up
j=lambda p:json.load(open(p))
def merch(d):
    d=re.sub(r'^(SQ \*|TST\* |PY \*|SP |PAYPAL \*|GOOGLE \*)','',d.strip(),flags=re.I)
    d=re.split(r'\s{2,}|\s\d{3,}|\s#|\*|\.COM',d)[0]
    d=re.split(r'\(|\s-|-[a-z]',d,flags=re.I)[0]; d=re.sub(r'\b(chiang\s?mai|los|pclhong)\b','',d,flags=re.I); d=re.sub(r'(?i)www\.','',d)
    w=' '.join(x.capitalize() for x in d.split()[:3]).strip(' -—,')
    for k in ('Rimping','Wise','Venmo','Grab','7-11','Amextravel','Amex Hotel'):
        if w.lower().startswith(k.lower()): return {'Wise':'Wise Transfer','Venmo':'Venmo','Amextravel':'Amex Travel'}.get(k,k)
    return w or 'Unknown'
def data():
    roth=j(F+'/roth/roth-slide-data.json'); kr=j(F+'/crypto/kraken/kraken-slide-data.json'); PH=j(F+'/reports/roth/history/price-history.json'); ph=PH['symbols']
    alias=lambda t:t if t in ph else t.replace('.','/')
    pos=[];hist={}
    for src,d in (('Roth IRA',roth),('Kraken',kr)):
        for r in d['rows']:
            if r['value']<1: continue
            t=r['ticker']; pos.append(dict(acct=src,t=t,qty=r['qty'],price=r['price'],value=r['value'],cost=r.get('cost_basis'),gl=r.get('gl_dlt'),glp=r.get('gl_pct'),d7=r.get('pct_7d'),d30=r.get('pct_30d')))
            o=ph.get(alias(t),{}).get('ohlcv')
            if o: hist[t]=[[x[0]]+[round(v,6) for v in x[1:5]] for x in o]
    # live Kraken refresh (public ticker); equities stay at the latest completed US session close
    kr_live=None
    try:
        import urllib.request
        tk=json.load(urllib.request.urlopen('https://api.kraken.com/0/public/Ticker?pair=XBTUSD',timeout=10))['result']['XXBTZUSD']
        last,op=float(tk['c'][0]),float(tk['o'])
        for p in pos:
            if p['acct']=='Kraken' and p['t']=='BTC':
                old=p['value']; p['price']=last; p['value']=round(p['qty']*last,2)
                if p['cost']: p['gl']=round(p['value']-p['cost'],2); p['glp']=round(p['gl']/p['cost']*100,2)
                kr['total']=round(kr['total']-old+p['value'],2); kr_live=dict(dlt=round(p['qty']*(last-op),2),pct=round((last/op-1)*100,2),asof=dt.datetime.now().strftime('%Y-%m-%d %H:%M ICT'))
    except Exception as ex: kr_live=None
    for r in roth['rows']:
        for p in pos:
            if p['acct']=='Roth IRA' and p['t']==r['ticker']: p['dpct']=r.get('pct'); p['ddlt']=r.get('dlt')
    for r in kr['rows']:
        for p in pos:
            if p['acct']=='Kraken' and p['t']==r['ticker'] and 'dpct' not in p: p['dpct']=r.get('pct'); p['ddlt']=r.get('dlt')
    if kr_live:
        for p in pos:
            if p['t']=='BTC' and p['acct']=='Kraken': p['dpct']=kr_live['pct']; p['ddlt']=kr_live['dlt']
    # target mix from the draft (bucket -> tickers, target %)
    BK={'Index':['SPY','EEMA','BRK.B','BRK/B'],'Bitcoin':['BTC','IBIT'],'TSLA':['TSLA'],'Other Single Stocks':['AAPL','META','NFLX','NDAQ'],'Space':['SPCX','NASA','RKLB'],'Thematic':['BATT','THD','QTUM'],'Cash / SGOV':['SGOV','CASH']}
    md=open(F+'/roth/TARGET-MIX-DRAFT.md').read(); tg=[float(x) for x in re.findall(r'\|\s*(?:at most )?(\d+)%\s*\|\s*$',md,re.M)]
    mix=[dict(k=k,tickers=v,target=tg[i] if i<len(tg) else None,cap='at most' in md.split('\n|')[i+3] if i<len(tg) else False) for i,(k,v) in enumerate(BK.items())]
    news=j(PRIV+'/inputs/news.json') if os.path.exists(PRIV+'/inputs/news.json') else None
    port=dict(mix=mix,news=news,roth_day=roth.get('day_dlt'),roth_day_pct=roth.get('day_pct'),roth_session=roth.get('equity_session'),kr_day=(kr_live or {}).get('dlt',kr.get('day_dlt')),kr_day_pct=(kr_live or {}).get('pct',kr.get('day_pct')),kr_live=(kr_live or {}).get('asof'),roth_total=roth['book'],roth_cash=roth['cash'],kr_total=kr['total'],asof=roth['asof'][:10],kr_asof=kr['asof'][:10],roth_week=roth.get('week_pct'),kr_week=kr.get('week_pct'))
    lines=[r for r in csv.DictReader(open(F+'/spending/personal/monthly-may-sep-2026-lines.csv')) if r['status']=='included']
    sp=[dict(d=r['date'],m=r['month'],a=round(float(r['amount']),2),c=r['category'],acct=r['account'],desc=re.sub(r'\s+',' ',r['description'])[:60],mer=merch(r['description'])) for r in lines]
    work={}
    for f in ('amex-business-platinum-ytd.csv','capone-business-ytd.csv'):
        for r in csv.DictReader(open(F+'/spending/'+f)):
            m=r['date_iso'][:7]
            if r['section'] in('charge','txn') and r['lean']=='work' and '2026-05'<=m<='2026-09': work[m]=round(work.get(m,0)+float(r['amount']),2)
    allp=list(csv.DictReader(open(F+'/spending/personal/monthly-may-sep-2026-lines.csv')))
    for r in allp:
        if r['status']=='excluded_work': work[r['month']]=round(work.get(r['month'],0)+float(r['amount']),2)
    unsure=round(sum(float(r['amount']) for r in allp if r['status'].startswith('caveat')),2)
    bills=[]
    for p in glob.glob(F+'/credit-cards/*/account-profile.json'):
        d=j(p); l4=re.sub(r'\D','',str(d.get('last4') or ''))[-4:]
        bills.append(dict(card=(d.get('product','') if d.get('product','') in d.get('issuer','') else f"{d.get('issuer','')} {d.get('product','')}").split('|')[0].strip(),l4=l4,due=d.get('payment_due'),bal=d.get('new_balance'),mn=d.get('minimum_due'),auto=d.get('autopay')))
    bills.sort(key=lambda b:b['due'] or '9999')
    for b in bills:  # last 4 only: scrub any long digit runs from free text
        b['auto']=b['auto'] and re.sub(r'\b\d{5,}\b','',b['auto'])
    tax=j(PRIV+'/inputs/tax-status.json')['items']
    for x in tax:
        assert not re.search(r'\d{3}-?\d{2}-?\d{4}|\d{2}-\d{7}|\b(CP|LT)\s?\d+|Letter\s?\d+',x['t']+x['n'],re.I),'tax item has an ID or letter number'
    # Rent: property names only, never payer/tenant names
    now=dt.date.today().strftime('%Y-%m'); ms=[f'2026-{m:02d}' for m in range(1,13) if f'2026-{m:02d}'<=now]
    RE=j(PRIV+'/inputs/rent-expected.json'); exp={p:{m:v['monthly'] for m in ms if m>=v['from']} for p,v in RE.items()}
    got={'Wickfield':{},'Mellow Wood':{}}
    for r in csv.DictReader(open(F+'/income/rent-deposits-2026.csv')):
        if r['ledger_category']!='rental_income': continue
        p='Wickfield' if 'Wickfield' in r['property'] else 'Mellow Wood'; got[p][r['period']]=got[p].get(r['period'],0)+float(r['amount'])
    rent=dict(months=ms,exp=exp,got=got,note='Wickfield expected monthly all year; Mellow Wood rented from Sep 19, so its expected rent starts in October (September signing money is not counted as rent). A missing month means no deposit is in the file yet.')
    # Smart UpKeep
    import openpyxl
    ws=openpyxl.load_workbook('/workspace/smart-visa/financial_model/SmartKeep_HomeRecord_3yr_Model.xlsx',data_only=True,read_only=True)['Scenarios']
    rows=[r[:4] for r in ws.iter_rows(values_only=True) if r and r[0]]
    sec=None;M={}
    for r in rows:
        if r[1] is None: sec=r[0] if r[0].startswith('FY') else None
        elif r[1] is not None and isinstance(r[1],(int,float)): M[(sec,r[0])]=r[1:4]
    g=lambda s,k:list(M.get((s,k)) or [None]*3)
    review=open('/workspace/smart-visa/financial_model/FOLIO-REVIEW.md').read()
    errs=[re.sub(r'\*\*','',m) for m in re.findall(r'^\d+\.\s+\*\*(.+?)\*\*',review,re.M)]
    flags=[re.sub(r'\*\*','',m).rstrip(':.') for m in re.findall(r'^- \*\*(.+?)\*\*',review.split('## Assumption flags')[1],re.M)]
    us=g(None,'US Operator Cash Need'); th=g(None,'Thai Licensor Cash Need (USD)')
    up=dict(reviewed=(re.search(r'Reviewed ([A-Z][a-z]+ \d+, \d{4})',review) or [None,''])[1],
       ltvcac=g(None,'LTV / CAC'),mem29=g('FY2029','Members, End of Year'),
       ebitda=[[x for x in g(f'FY{y}','Group EBITDA')] for y in (2027,2028,2029)],
       need=[a+b for a,b in zip(us,th)],
       rows=[['US Revenue FY2029']+g('FY2029','US Operator Revenue'),['Group EBITDA FY2029']+g('FY2029','Group EBITDA'),['US Cash Need']+us,['Thai Cash Need']+th,['Group Cash Need (Netted)']+g(None,'Group Cash Need'),['Standalone Cash Need']+[a+b for a,b in zip(us,th)],['LTV / CAC']+[f'{v:.1f}x' for v in g(None,'LTV / CAC')]],
       errs=errs,flags=flags)
    return dict(port=port,pos=pos,hist=hist,sp=sp,work=work,unsure=unsure,bills=bills,tax=tax,rent=rent,up=up)
PICK={'portfolio':['port','pos','hist'],'spending':['sp','work','unsure'],'bills':['bills'],'taxes':['tax'],'rentals':['rent'],'upkeep':['up']}
def render():
    D=data(); b64=lambda p:base64.b64encode(open(p,'rb').read()).decode(); B='/workspace/ops/construction/brand/'
    fonts=f"@font-face{{font-family:Khand;font-weight:700;src:url(data:font/woff2;base64,{b64(B+'Khand-Bold.woff2')})}}@font-face{{font-family:Hind;font-weight:400 600;src:url(data:font/woff2;base64,{b64(B+'Hind-Regular.woff2')})}}"
    tpl=open(HERE+'/sub_template.html').read(); js=open(HERE+'/sub.js').read(); lib=open(F+'/reports/roth/vendor/lightweight-charts.standalone.production.js').read()
    out={}
    for slug,title in PAGES:
        h=tpl.replace('/*TITLE*/',title).replace('/*FONTS*/',fonts).replace('/*TOKENS*/',open(HERE+'/brand-tokens.css').read()).replace('/*PAGE*/',slug)
        h=h.replace('/*LIB*/',lib if slug=='portfolio' else '').replace('/*JS*/',js).replace('/*DATA*/','const D='+json.dumps({k:D[k] for k in PICK[slug]})+';')
        out[slug]=h
    return out
def salt():
    p=PRIV+'/salt.b64'
    if not os.path.exists(p): open(p,'w').write(base64.b64encode(os.urandom(16)).decode())
    return open(p).read().strip()
def encrypt_all(pages,pw,dest,only=None):
    s=salt(); key=hashlib.pbkdf2_hmac('sha256',pw.encode(),base64.b64decode(s),ITER,32); lock=open(HERE+'/lock_template.html').read()
    os.makedirs(dest,exist_ok=True)
    for slug,title in PAGES:
        if only and slug not in only: continue
        iv=os.urandom(12); ct=base64.b64encode(iv+AESGCM(key).encrypt(iv,pages[slug].encode(),None)).decode()
        open(f'{dest}/{slug}.html','w').write(lock.replace('{{TITLE}}',title).replace('{{SALT}}',s).replace('{{CT}}',ct))
def build():
    pages=render(); os.makedirs(PRIV+'/plain',exist_ok=True)
    for k,v in pages.items(): open(f'{PRIV}/plain/{k}.html','w').write(v)
    pw=os.environ.get('PORTFOLIO_DASH_PASSWORD')
    prev=os.environ.get('PORTFOLIO_DASH_PREVIEW_PASSWORD')  # local test only, never published
    if prev: encrypt_all(pages,prev,PRIV+'/preview/s')
    if pw: encrypt_all(pages,pw,HERE+'/s',LIVE); return 'published'
    return 'existing' if all(os.path.exists(f'{HERE}/s/{k}.html') for k in LIVE) else 'setup'
if __name__=='__main__': print(build())
