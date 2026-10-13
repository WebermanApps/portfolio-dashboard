#!/usr/bin/env python3
"""Build the six private sub-dashboards. Plaintext goes ONLY to ../dashboard-private (outside the repo).
Encrypted pages (AES-256-GCM, PBKDF2-SHA256 600k) are written to s/ only when PORTFOLIO_DASH_PASSWORD is set."""
import csv,json,glob,re,base64,os,hashlib,datetime as dt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
HERE=os.path.dirname(os.path.abspath(__file__)); F='/workspace/ops/folio'; PRIV=F+'/dashboard-private'
PAGES=[('portfolio','Portfolio'),('spending','Spending'),('bills','Cards And Bills'),('taxes','Taxes'),('rentals','Rentals Finance'),('upkeep','Smart UpKeep Model')]
ITER=600000
j=lambda p:json.load(open(p))
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
    port=dict(roth_total=roth['book'],roth_cash=roth['cash'],kr_total=kr['total'],asof=roth['asof'][:10],kr_asof=kr['asof'][:10],roth_week=roth.get('week_pct'),kr_week=kr.get('week_pct'))
    lines=[r for r in csv.DictReader(open(F+'/spending/personal/monthly-may-sep-2026-lines.csv')) if r['status']=='included']
    sp=[dict(d=r['date'],m=r['month'],a=round(float(r['amount']),2),c=r['category'],acct=r['account'],desc=re.sub(r'\s+',' ',r['description'])[:60]) for r in lines]
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
    exp={'Wickfield':{m:4300 for m in ms},'Mellow Wood':{m:3500 for m in ms if m>='2026-10'}}
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
    return dict(port=port,pos=pos,hist=hist,sp=sp,bills=bills,tax=tax,rent=rent,up=up)
PICK={'portfolio':['port','pos','hist'],'spending':['sp'],'bills':['bills'],'taxes':['tax'],'rentals':['rent'],'upkeep':['up']}
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
def encrypt_all(pages,pw,dest):
    s=salt(); key=hashlib.pbkdf2_hmac('sha256',pw.encode(),base64.b64decode(s),ITER,32); lock=open(HERE+'/lock_template.html').read()
    os.makedirs(dest,exist_ok=True)
    for slug,title in PAGES:
        iv=os.urandom(12); ct=base64.b64encode(iv+AESGCM(key).encrypt(iv,pages[slug].encode(),None)).decode()
        open(f'{dest}/{slug}.html','w').write(lock.replace('{{TITLE}}',title).replace('{{SALT}}',s).replace('{{CT}}',ct))
def build():
    pages=render(); os.makedirs(PRIV+'/plain',exist_ok=True)
    for k,v in pages.items(): open(f'{PRIV}/plain/{k}.html','w').write(v)
    pw=os.environ.get('PORTFOLIO_DASH_PASSWORD')
    prev=os.environ.get('PORTFOLIO_DASH_PREVIEW_PASSWORD')  # local test only, never published
    if prev: encrypt_all(pages,prev,PRIV+'/preview/s')
    if pw: encrypt_all(pages,pw,HERE+'/s'); return 'published'
    return 'existing' if all(os.path.exists(f'{HERE}/s/{k}.html') for k,_ in PAGES) else 'setup'
if __name__=='__main__': print(build())
