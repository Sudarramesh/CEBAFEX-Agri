"""Durable operational ledger. Suggestions never reserve or consume physical stock."""
from contextlib import contextmanager
from datetime import date,datetime,timezone
from decimal import Decimal
import hashlib,json,math,sqlite3,uuid
import pandas as pd
from .storage import connect
from .money import gross_return,money,sum_money

class OperationError(ValueError):pass

def number(value,positive=False):
    try:value=float(value)
    except (TypeError,ValueError):raise OperationError('Invalid numeric value')
    if not math.isfinite(value) or value<0 or value>1e12 or (positive and value<=0):raise OperationError('Invalid numeric value')
    return value

def text(value):
    value=str(value).strip()
    if not value or len(value)>200:raise OperationError('Required text missing')
    return value

def day(value):
    try:
        if isinstance(value,datetime):return value.date()
        if isinstance(value,date):return value
        raw=str(value).strip()
        return date.fromisoformat(raw) if len(raw)==10 else datetime.fromisoformat(raw.replace('Z','+00:00')).date()
    except (ValueError,TypeError):raise OperationError('Invalid date')

def now():return datetime.now(timezone.utc).isoformat()

def setup(con):
    con.executescript('''
    CREATE TABLE IF NOT EXISTS ops_markets(id INTEGER PRIMARY KEY,name TEXT NOT NULL,location TEXT NOT NULL,latitude REAL,longitude REAL);
    CREATE TABLE IF NOT EXISTS ops_suppliers(id INTEGER PRIMARY KEY,name TEXT NOT NULL,role TEXT NOT NULL,market_id INTEGER NOT NULL REFERENCES ops_markets(id));
    CREATE TABLE IF NOT EXISTS ops_buyers(id INTEGER PRIMARY KEY,name TEXT NOT NULL,buyer_type TEXT NOT NULL,market_id INTEGER NOT NULL REFERENCES ops_markets(id));
    CREATE TABLE IF NOT EXISTS ops_lots(id INTEGER PRIMARY KEY,supplier_id INTEGER NOT NULL REFERENCES ops_suppliers(id),crop TEXT NOT NULL,grade TEXT NOT NULL,received REAL NOT NULL,local_demand REAL NOT NULL,market_price REAL NOT NULL,harvest_date TEXT NOT NULL,ready_date TEXT NOT NULL,freshness TEXT NOT NULL,storage_notes TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS ops_requests(id INTEGER PRIMARY KEY,buyer_id INTEGER NOT NULL REFERENCES ops_buyers(id),crop TEXT NOT NULL,min_grade TEXT NOT NULL,required REAL NOT NULL,offer_price REAL NOT NULL,transport_quote REAL NOT NULL,delivery_by TEXT NOT NULL,max_distance REAL,inspection_required INTEGER NOT NULL,closed INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS ops_orders(id INTEGER PRIMARY KEY,token TEXT NOT NULL UNIQUE,lot_id INTEGER NOT NULL REFERENCES ops_lots(id),request_id INTEGER NOT NULL REFERENCES ops_requests(id),quantity REAL NOT NULL,estimated_price REAL NOT NULL,estimated_transport REAL NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL,response_date TEXT,response_note TEXT NOT NULL DEFAULT '',accepted_at TEXT);
    CREATE TABLE IF NOT EXISTS ops_movements(id INTEGER PRIMARY KEY,token TEXT NOT NULL UNIQUE,lot_id INTEGER NOT NULL REFERENCES ops_lots(id),order_id INTEGER REFERENCES ops_orders(id),event_date TEXT NOT NULL,event_type TEXT NOT NULL,quantity REAL NOT NULL,unit_price REAL NOT NULL,transport REAL NOT NULL,other_costs REAL NOT NULL,notes TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS ops_audit(id INTEGER PRIMARY KEY,created_at TEXT NOT NULL,action TEXT NOT NULL,record_id INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS ops_history(id INTEGER PRIMARY KEY,market_id INTEGER NOT NULL REFERENCES ops_markets(id),crop TEXT NOT NULL,event_date TEXT NOT NULL,demand REAL NOT NULL,stockout INTEGER NOT NULL,basis TEXT NOT NULL,source TEXT NOT NULL,UNIQUE(market_id,crop,event_date));
    CREATE TABLE IF NOT EXISTS ops_models(id INTEGER PRIMARY KEY,market_id INTEGER NOT NULL,crop TEXT NOT NULL,created_at TEXT NOT NULL,cutoff TEXT NOT NULL,payload TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS ops_forecasts(id INTEGER PRIMARY KEY,model_id INTEGER NOT NULL REFERENCES ops_models(id),event_date TEXT NOT NULL,predicted REAL NOT NULL,UNIQUE(model_id,event_date));
    ''')
    con.execute('PRAGMA foreign_keys=ON')

@contextmanager
def connection(path,write=False):
    con=connect(path);setup(con)
    try:
        con.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
        yield con
        if write:con.commit()
    except Exception:
        if write:con.rollback()
        raise
    finally:con.close()

def audit(con,action,record):con.execute('INSERT INTO ops_audit(created_at,action,record_id) VALUES (?,?,?)',(now(),action,record))

def _exists(con,table,record):
    if not con.execute('SELECT 1 FROM '+table+' WHERE id=?',(int(record),)).fetchone():raise OperationError('Record not found')

def registry(path,kind,values):
    with connection(path,True) as con:
        name=text(values['name'])
        if kind=='markets':
            lat,lon=values.get('latitude'),values.get('longitude')
            if (lat is None)!=(lon is None):raise OperationError('Both coordinates required')
            if lat is not None:
                lat,lon=float(lat),float(lon)
                if not math.isfinite(lat+lon) or not -90<=lat<=90 or not -180<=lon<=180:raise OperationError('Invalid coordinates')
            cursor=con.execute('INSERT INTO ops_markets(name,location,latitude,longitude) VALUES (?,?,?,?)',(name,text(values['location']),lat,lon))
        elif kind in ('suppliers','buyers'):
            _exists(con,'ops_markets',values['market_id'])
            role=text(values['role'])
            allowed=['Farmer','Vendor','Cooperative','Distributor'] if kind=='suppliers' else ['Restaurant','Hostel','Retailer','Wholesaler','Other']
            if role not in allowed:raise OperationError('Invalid participant role')
            column='role' if kind=='suppliers' else 'buyer_type'
            cursor=con.execute('INSERT INTO ops_'+kind+'(name,'+column+',market_id) VALUES (?,?,?)',(name,role,int(values['market_id'])))
        else:raise OperationError('Invalid registry')
        audit(con,'Added '+kind,cursor.lastrowid);return cursor.lastrowid


def add_lot(path,values):
    harvest,ready=day(values['harvest_date']),day(values['ready_date'])
    if harvest>date.today() or ready<harvest:raise OperationError('Invalid stock dates')
    if values['grade'] not in ['A','B','C'] or values['freshness'] not in ['Not assessed','Acceptable','Needs inspection','Unsuitable']:raise OperationError('Invalid stock quality')
    with connection(path,True) as con:
        _exists(con,'ops_suppliers',values['supplier_id'])
        row=(int(values['supplier_id']),text(values['crop']),values['grade'],number(values['received'],True),number(values['local_demand']),number(values['market_price']),str(harvest),str(ready),values['freshness'],str(values.get('storage_notes',''))[:1000])
        cursor=con.execute('INSERT INTO ops_lots(supplier_id,crop,grade,received,local_demand,market_price,harvest_date,ready_date,freshness,storage_notes) VALUES (?,?,?,?,?,?,?,?,?,?)',row)
        audit(con,'Added lot',cursor.lastrowid);return cursor.lastrowid


def add_request(path,values):
    deadline=day(values['delivery_by'])
    if deadline<date.today():raise OperationError('Delivery deadline has passed')
    if values['min_grade'] not in ['A','B','C']:raise OperationError('Invalid grade')
    distance=values.get('max_distance')
    with connection(path,True) as con:
        _exists(con,'ops_buyers',values['buyer_id'])
        row=(int(values['buyer_id']),text(values['crop']),values['min_grade'],number(values['required'],True),number(values['offer_price']),number(values['transport_quote']),str(deadline),number(distance) if distance is not None else None,int(bool(values.get('inspection_required'))))
        cursor=con.execute('INSERT INTO ops_requests(buyer_id,crop,min_grade,required,offer_price,transport_quote,delivery_by,max_distance,inspection_required) VALUES (?,?,?,?,?,?,?,?,?)',row)
        audit(con,'Added request',cursor.lastrowid);return cursor.lastrowid


def _frames(con):
    lots=pd.read_sql_query('''SELECT l.*,s.name supplier_name,s.role supplier_role,s.market_id,m.name market_name,m.location,m.latitude,m.longitude FROM ops_lots l JOIN ops_suppliers s ON s.id=l.supplier_id JOIN ops_markets m ON m.id=s.market_id''',con)
    requests=pd.read_sql_query('''SELECT r.*,b.name buyer_name,b.buyer_type,b.market_id,m.name market_name,m.latitude,m.longitude FROM ops_requests r JOIN ops_buyers b ON b.id=r.buyer_id JOIN ops_markets m ON m.id=b.market_id''',con)
    movements=pd.read_sql_query('SELECT * FROM ops_movements',con)
    orders=pd.read_sql_query('SELECT * FROM ops_orders',con)
    for col in ['physical_kg','reserved_kg','free_kg','surplus_kg']:lots[col]=0.0
    for i,row in lots.iterrows():
        moved=float(movements.loc[movements.lot_id==row.id,'quantity'].sum())
        reserved=0.0
        for order in orders.loc[(orders.lot_id==row.id)&(orders.status=='Accepted')].itertuples():
            sold=float(movements.loc[(movements.order_id==order.id)&(movements.event_type=='Sale'),'quantity'].sum())
            reserved+=max(float(order.quantity)-sold,0)
        physical=max(float(row.received)-moved,0)
        lots.loc[i,['physical_kg','reserved_kg','free_kg','surplus_kg']]=[physical,reserved,max(physical-reserved,0),max(physical-reserved-float(row.local_demand),0)]
    requests['remaining_kg']=0.0
    for i,row in requests.iterrows():
        used=0.0
        for order in orders.loc[orders.request_id==row.id].itertuples():
            sold=float(movements.loc[(movements.order_id==order.id)&(movements.event_type=='Sale'),'quantity'].sum())
            used+=float(order.quantity) if order.status in ['Accepted','Completed'] else sold
        requests.loc[i,'remaining_kg']=max(float(row.required)-used,0)
    return lots,requests,orders,movements


def snapshot(path):
    with connection(path) as con:
        lots,requests,orders,movements=_frames(con)
        return {'lots':lots,'requests':requests,'orders':orders,'movements':movements,
                'markets':pd.read_sql_query('SELECT * FROM ops_markets',con),
                'suppliers':pd.read_sql_query('SELECT * FROM ops_suppliers',con),
                'buyers':pd.read_sql_query('SELECT * FROM ops_buyers',con)}


def haversine(a,b,c,d):
    if any(pd.isna(v) for v in [a,b,c,d]):return None
    a,b,c,d=map(math.radians,[a,b,c,d]);h=math.sin((c-a)/2)**2+math.cos(a)*math.cos(c)*math.sin((d-b)/2)**2
    return 6371*2*math.asin(min(1,math.sqrt(h)))


def suitability(lot,request,as_of=None):
    as_of=as_of or date.today();reasons=[]
    if str(lot['crop']).casefold().strip()!=str(request['crop']).casefold().strip():reasons.append('Crop mismatch')
    if {'A':3,'B':2,'C':1}[lot['grade']]<{'A':3,'B':2,'C':1}[request['min_grade']]:reasons.append('Grade below requirement')
    if lot['freshness']=='Unsuitable':reasons.append('Stock reported unsuitable')
    if request['inspection_required'] and lot['freshness']!='Acceptable':reasons.append('Inspection requirement unmet')
    if day(request['delivery_by'])<as_of or day(lot['ready_date'])>day(request['delivery_by']):reasons.append('Delivery dates incompatible')
    distance=haversine(lot['latitude'],lot['longitude'],request['latitude'],request['longitude'])
    limit=request['max_distance']
    if pd.notna(limit):
        if distance is None:reasons.append('Distance unknown for limit')
        elif distance>float(limit):reasons.append('Distance exceeds limit')
    if request['closed']:reasons.append('Request closed')
    if lot['surplus_kg']<=0 or request['remaining_kg']<=0:reasons.append('No free surplus or request')
    # Explicit planning score, not a learned probability or verified delivery promise.
    grade=30 if lot['grade']==request['min_grade'] else 25
    freshness=20 if lot['freshness']=='Acceptable' else (0 if lot['freshness']=='Needs inspection' else 10)
    distance_points=0 if distance is None else max(0,20-distance/10)
    coverage=30*min(float(lot['surplus_kg'])/max(float(request['remaining_kg']),1e-9),1)
    return {'eligible':not reasons,'score':round(grade+freshness+distance_points+coverage,2),
            'distance_km':distance,'reasons':reasons,'grade_points':grade,'freshness_points':freshness,
            'distance_points':distance_points,'coverage_points':coverage}


def ranked_matches(lots,requests,as_of=None):
    candidates=[]
    for lot in lots.to_dict('records'):
        for request in requests.to_dict('records'):
            if str(lot['crop']).casefold().strip()!=str(request['crop']).casefold().strip():continue
            detail=suitability(lot,request,as_of)
            q=min(lot['surplus_kg'],request['remaining_kg'])
            estimate=gross_return(q,request['offer_price'])-money(request['transport_quote']) if q>0 else 0
            candidates.append({**detail,'lot_id':int(lot['id']),'request_id':int(request['id']),'crop':lot['crop'],'buyer_name':request['buyer_name'],'supplier_name':lot['supplier_name'],'offer_price':request['offer_price'],'transport_quote':request['transport_quote'],'potential_kg':0.0,'estimated_return':0.0,'ranking_return':estimate})
    candidates.sort(key=lambda r:(not r['eligible'],-r['score'],-r['ranking_return'],r['lot_id'],r['request_id']))
    stock={int(r.id):float(r.surplus_kg) for r in lots.itertuples()};needed={int(r.id):float(r.remaining_kg) for r in requests.itertuples()}
    for row in candidates:
        if not row['eligible']:continue
        q=min(stock[row['lot_id']],needed[row['request_id']]);stock[row['lot_id']]-=q;needed[row['request_id']]-=q
        row['potential_kg']=q
        row['estimated_return']=money(Decimal(str(gross_return(q,row['offer_price'])))-Decimal(str(money(row['transport_quote'])))) if q>0 else 0
        if q<=0:row['reasons']=['Earlier ranked pairs used the capacity']
    return candidates


def propose(path,lot_id,request_id,quantity,token=None):
    token=token or str(uuid.uuid4());quantity=number(quantity,True)
    with connection(path,True) as con:
        existing=con.execute('SELECT id,lot_id,request_id,quantity FROM ops_orders WHERE token=?',(token,)).fetchone()
        if existing:
            if tuple(existing[1:])!=(int(lot_id),int(request_id),quantity):raise OperationError('Retry token belongs to different data')
            return existing[0]
        lots,requests,orders,_=_frames(con)
        if lot_id not in lots.id.values or request_id not in requests.id.values:raise OperationError('Record not found')
        lot=lots.loc[lots.id==lot_id].iloc[0];request=requests.loc[requests.id==request_id].iloc[0]
        check=suitability(lot,request)
        if not check['eligible'] or quantity>min(lot.surplus_kg,request.remaining_kg)+1e-8:raise OperationError('Pair or quantity is no longer eligible')
        if len(orders.loc[(orders.lot_id==lot_id)&(orders.request_id==request_id)&(orders.status=='Proposed')]):raise OperationError('Proposal already exists')
        cursor=con.execute('INSERT INTO ops_orders(token,lot_id,request_id,quantity,estimated_price,estimated_transport,status,created_at) VALUES (?,?,?,?,?,?,?,?)',(token,int(lot_id),int(request_id),quantity,float(request.offer_price),float(request.transport_quote),'Proposed',now()))
        audit(con,'Recorded proposal',cursor.lastrowid);return cursor.lastrowid


def respond(path,order_id,response,notes='',response_date=None):
    if response not in ['Accepted','Declined','Cancelled']:raise OperationError('Invalid buyer response')
    response_date=day(response_date or date.today())
    if response_date>date.today():raise OperationError('Actual response cannot be in the future')
    with connection(path,True) as con:
        lots,requests,orders,_=_frames(con)
        selected=orders.loc[orders.id==order_id]
        if selected.empty:raise OperationError('Record not found')
        order=selected.iloc[0]
        if (response in ['Accepted','Declined'] and order.status!='Proposed') or (response=='Cancelled' and order.status not in ['Proposed','Accepted']):raise OperationError('Invalid order transition')
        if response=='Accepted':
            lot=lots.loc[lots.id==order.lot_id].iloc[0];request=requests.loc[requests.id==order.request_id].iloc[0]
            if response_date<day(lot.harvest_date):raise OperationError('Response predates harvest')
            if not suitability(lot,request)['eligible'] or order.quantity>min(lot.surplus_kg,request.remaining_kg)+1e-8:raise OperationError('Insufficient unreserved capacity')
        con.execute('UPDATE ops_orders SET status=?,response_date=?,response_note=?,accepted_at=CASE WHEN ?=\'Accepted\' THEN ? ELSE accepted_at END WHERE id=?',(response,str(response_date),str(notes)[:1000],response,now(),int(order_id)))
        audit(con,'Recorded '+response,int(order_id))


def movement(path,lot_id,event_type,quantity,event_date,unit_price=0,transport=0,other_costs=0,order_id=None,notes='',token=None):
    quantity=number(quantity,True);event_date=day(event_date)
    if event_type not in ['Sale','Redistribution','Discard'] or event_date>date.today():raise OperationError('Invalid actual outcome')
    unit_price,transport,other_costs=map(number,[unit_price,transport,other_costs]);token=token or str(uuid.uuid4())
    with connection(path,True) as con:
        existing=con.execute('SELECT id,lot_id,order_id,event_date,event_type,quantity,unit_price,transport,other_costs,notes FROM ops_movements WHERE token=?',(token,)).fetchone()
        if existing:
            intended=(int(lot_id),int(order_id) if order_id is not None and event_type=='Sale' else None,str(event_date),event_type,quantity,unit_price,transport,other_costs,str(notes)[:1000])
            if tuple(existing[1:])!=intended:raise OperationError('Retry token belongs to different data')
            return existing[0]
        lots,_,orders,moves=_frames(con)
        selected=lots.loc[lots.id==lot_id]
        if selected.empty:raise OperationError('Record not found')
        lot=selected.iloc[0]
        if event_date<day(lot.harvest_date):raise OperationError('Outcome predates harvest')
        if event_type=='Sale':
            order=orders.loc[orders.id==order_id]
            if order.empty:raise OperationError('Choose an accepted order')
            order=order.iloc[0]
            sold=float(moves.loc[(moves.order_id==order_id)&(moves.event_type=='Sale'),'quantity'].sum())
            if order.status!='Accepted' or order.lot_id!=lot_id or quantity>float(order.quantity)-sold+1e-8:raise OperationError('Sale exceeds accepted remaining quantity')
            if event_date<day(order.response_date):raise OperationError('Sale predates confirmation')
            if quantity>lot.physical_kg+1e-8:raise OperationError('Insufficient physical stock')
        else:
            order_id=None
            if quantity>lot.free_kg+1e-8:raise OperationError('Stock is reserved or unavailable')
            if unit_price:raise OperationError('Non-sale outcome cannot record sale revenue')
        cursor=con.execute('INSERT INTO ops_movements(token,lot_id,order_id,event_date,event_type,quantity,unit_price,transport,other_costs,notes) VALUES (?,?,?,?,?,?,?,?,?,?)',(token,int(lot_id),int(order_id) if order_id is not None else None,str(event_date),event_type,quantity,unit_price,transport,other_costs,str(notes)[:1000]))
        if event_type=='Sale' and sold+quantity>=float(order.quantity)-1e-8:con.execute("UPDATE ops_orders SET status='Completed' WHERE id=?",(int(order_id),))
        audit(con,'Recorded '+event_type,cursor.lastrowid);return cursor.lastrowid


def evaluation(data):
    lots,orders,moves=data['lots'],data['orders'],data['movements'];rows=[]
    for order in orders.itertuples():
        sales=moves.loc[(moves.order_id==order.id)&(moves.event_type=='Sale')]
        sold=float(sales.quantity.sum());gross=sum_money(gross_return(r.quantity,r.unit_price) for r in sales.itertuples())
        transport=sum_money(sales.transport);other=sum_money(sales.other_costs)
        allocated=money(float(order.estimated_transport)*sold/float(order.quantity))
        estimate=money(gross_return(sold,order.estimated_price)-allocated)
        rows.append({'order_id':order.id,'lot_id':order.lot_id,'request_id':order.request_id,'status':order.status,'confirmed_kg':float(order.quantity) if pd.notna(order.accepted_at) else 0,'sold_kg':sold,'estimated_full_return':money(gross_return(order.quantity,order.estimated_price)-order.estimated_transport),'estimated_sold_return':estimate,'actual_gross':gross,'actual_transport':transport,'actual_other':other,'actual_after_transport':money(gross-transport),'actual_after_recorded_costs':money(gross-transport-other),'difference':money(gross-transport-estimate)})
    proposed=len(orders);purchases=sum(r['sold_kg']>0 for r in rows)
    actual_gross=sum_money(r['actual_gross'] for r in rows)
    all_transport=sum_money(moves.transport);all_other=sum_money(moves.other_costs)
    return {'actual_gross':actual_gross,'all_transport':all_transport,'all_other':all_other,'after_all_recorded_costs':money(actual_gross-all_transport-all_other),'orders':rows,'proposals':proposed,'purchases':purchases,'conversion':purchases/proposed if proposed else None,
            'physical_kg':float(lots.physical_kg.sum()),'reserved_kg':float(lots.reserved_kg.sum()),
            'sold_kg':float(moves.loc[moves.event_type=='Sale','quantity'].sum()),
            'redistributed_kg':float(moves.loc[moves.event_type=='Redistribution','quantity'].sum()),
            'discarded_kg':float(moves.loc[moves.event_type=='Discard','quantity'].sum())}


def planning_projection(data,as_of=None):
    as_of=as_of or date.today();rows=[]
    for key,group in data['lots'].groupby(data['lots'].crop.str.casefold().str.strip()):
        physical=float(group.physical_kg.sum());free=float(group.free_kg.sum())
        price=float((group.market_price*group.physical_kg).sum()/physical) if physical else float(group.market_price.mean())
        rows.append({'crop':group.iloc[0].crop,'available_kg':free,'estimated_demand_kg':float(group.local_demand.sum()),'market_price_per_kg':price,'harvest_age_days':max((as_of-day(v)).days for v in group.harvest_date)})
    return pd.DataFrame(rows) if rows else None


def revise_lot(path,lot_id,local_demand,market_price,freshness,notes=''):
    if freshness not in ['Not assessed','Acceptable','Needs inspection','Unsuitable']:raise OperationError('Invalid stock quality')
    with connection(path,True) as con:
        _exists(con,'ops_lots',lot_id)
        con.execute('UPDATE ops_lots SET local_demand=?,market_price=?,freshness=?,storage_notes=? WHERE id=?',(number(local_demand),number(market_price),freshness,str(notes)[:1000],int(lot_id)))
        audit(con,'Reviewed stock lot',int(lot_id))


def close_request(path,request_id):
    with connection(path,True) as con:
        _exists(con,'ops_requests',request_id)
        con.execute('UPDATE ops_requests SET closed=1 WHERE id=?',(int(request_id),));audit(con,'Closed request',int(request_id))


def database_backup(path):
    import tempfile,os
    handle,name=tempfile.mkstemp(suffix='.sqlite3');os.close(handle)
    try:
        source=connect(path);destination=sqlite3.connect(name)
        try:source.backup(destination)
        finally:source.close();destination.close()
        with open(name,'rb') as file:return file.read()
    finally:os.unlink(name)


def operational_totals(data):
    lots=data['lots']
    return {'records':len(lots),'available_kg':float(lots.free_kg.sum()),'physical_kg':float(lots.physical_kg.sum()),
            'reserved_kg':float(lots.reserved_kg.sum()),'estimated_demand_kg':float(lots.local_demand.sum()),
            'positive_surplus_kg':float(lots.surplus_kg.sum()),
            'shortage_kg':float((lots.local_demand-lots.free_kg).clip(lower=0).sum())}


def risk_reviews(data,policy,as_of=None):
    as_of=as_of or date.today();rows=[]
    for row in data['lots'].to_dict('records'):
        age=(as_of-day(row['harvest_date'])).days;share=row['surplus_kg']/row['free_kg'] if row['free_kg'] else 0
        reasons=[]
        if row['freshness']=='Unsuitable':reasons.append('Review unsuitable stock')
        elif row['freshness']=='Needs inspection':reasons.append('Inspection needed')
        if row['physical_kg']>0 and age>=policy.age_review_days:reasons.append('Age review')
        if row['surplus_kg']>0 and share>=policy.high_surplus_ratio:reasons.append('Large surplus')
        urgency=2 if row['freshness']=='Unsuitable' else (1 if row['freshness']=='Needs inspection' else 0)
        rows.append({**row,'age_days':age,'review_reasons':reasons or ['No rule triggered'],'review_urgency':urgency})
    rows.sort(key=lambda r:(-r['review_urgency'],-r['surplus_kg'],r['harvest_date'],r['id']))
    return rows
