"""Date-based demand learning with chronological tests and immutable JSON model runs."""
from datetime import date,timedelta
import hashlib,json,math
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from .operations import connection,number,text,day,now,audit,OperationError,_exists

MIN_DAYS=56
FEATURES=['lag_1','lag_7','mean_7','weekday_sin','weekday_cos','annual_sin','annual_cos']

def import_history(path,market_id,frame,basis='Observed demand',source='uploaded',replace=False):
    if basis not in ['Observed demand','Sales proxy']:raise OperationError('Invalid historical target')
    required={'date','crop','demand_kg'}
    if not required.issubset(frame.columns) or frame.empty or len(frame)>50000:raise OperationError('History columns or size invalid')
    records=[];seen=set()
    for row in frame.to_dict('records'):
        when=day(row['date']);crop=text(row['crop']).casefold()
        if when>date.today():raise OperationError('Actual observations cannot be in the future')
        value=number(row['demand_kg'])
        flag=row.get('stockout',0)
        if str(flag).strip().lower() not in ['0','1','false','true','0.0','1.0']:raise OperationError('Stockout must be zero or one')
        flag=int(str(flag).strip().lower() in ['1','true','1.0'])
        identity=(crop,str(when))
        if identity in seen:raise OperationError('Duplicate historical date and crop')
        seen.add(identity);records.append((int(market_id),crop,str(when),value,flag,basis,text(source)))
    with connection(path,True) as con:
        _exists(con,'ops_markets',market_id)
        for record in records:
            old=con.execute('SELECT demand,stockout,basis FROM ops_history WHERE market_id=? AND crop=? AND event_date=?',record[:3]).fetchone()
            if old and old!=record[3:6] and not replace:raise OperationError('Existing observation differs; explicit correction required')
            con.execute('INSERT INTO ops_history(market_id,crop,event_date,demand,stockout,basis,source) VALUES (?,?,?,?,?,?,?) ON CONFLICT(market_id,crop,event_date) DO UPDATE SET demand=excluded.demand,stockout=excluded.stockout,basis=excluded.basis,source=excluded.source',record)
        audit(con,'Imported history',len(records))
    return len(records)


def historical_series(path,market_id,crop):
    with connection(path) as con:return pd.read_sql_query('SELECT event_date,demand,stockout,basis,source FROM ops_history WHERE market_id=? AND crop=? ORDER BY event_date',con,params=(int(market_id),str(crop).strip().casefold()))


def features(values,when):
    return [values[-1],values[-7],float(np.mean(values[-7:])),math.sin(2*math.pi*when.weekday()/7),math.cos(2*math.pi*when.weekday()/7),math.sin(2*math.pi*when.timetuple().tm_yday/365.25),math.cos(2*math.pi*when.timetuple().tm_yday/365.25)]


def train_series(frame):
    frame=frame.sort_values('event_date').reset_index(drop=True).copy()
    if len(frame)<MIN_DAYS:raise OperationError('At least 56 consecutive daily observations required')
    dates=[day(v) for v in frame.event_date]
    if len(set(dates))!=len(dates) or any((b-a).days!=1 for a,b in zip(dates,dates[1:])):raise OperationError('History must contain consecutive daily dates')
    if len(set(frame.basis))!=1:raise OperationError('Do not mix observed demand and sales proxy targets')
    if frame.basis.iloc[0]=='Sales proxy' and frame.stockout.astype(bool).any():raise OperationError('Stockout sales are censored; provide observed demand or an uncensored consecutive period')
    y=[number(v) for v in frame.demand]
    x=np.array([features(y[:i],dates[i]) for i in range(7,len(y))]);target=np.array(y[7:])
    # Fit using older observations; hold out the most recent >=14 one-day targets.
    holdout=max(14,int(len(x)*.2));split=len(x)-holdout
    if split<21:raise OperationError('Not enough chronological training examples')
    mean=x[:split].mean(axis=0);scale=x[:split].std(axis=0);scale[scale==0]=1
    model=Ridge(alpha=10.0).fit((x[:split]-mean)/scale,target[:split])
    predicted=np.maximum(0,model.predict((x[split:]-mean)/scale))
    baseline=x[split:,1]  # previous week's observed quantity, available at each one-day origin
    mae=float(np.mean(abs(predicted-target[split:])));base_mae=float(np.mean(abs(baseline-target[split:])))
    selected='Ridge regression' if mae<base_mae else 'Seasonal baseline'
    # Refit final weights on all available lagged rows only after the held-out comparison.
    mean=x.mean(axis=0);scale=x.std(axis=0);scale[scale==0]=1
    final=Ridge(alpha=10.0).fit((x-mean)/scale,target)
    payload={'method':selected,'features':FEATURES,'mean':mean.tolist(),'scale':scale.tolist(),'coef':final.coef_.tolist(),'intercept':float(final.intercept_),
             'ridge_mae':mae,'baseline_mae':base_mae,'heldout_days':holdout,'training_examples':split,'total_days':len(y),
             'holdout_start':str(dates[7+split]),'holdout_end':str(dates[-1]),'cutoff':str(dates[-1]),'basis':frame.basis.iloc[0],
             'source_labels':sorted(set(frame.source)), 'history_digest':hashlib.sha256(frame.to_json(orient='records',double_precision=15).encode()).hexdigest(),
             'tail':y[-7:],'code_version':'ridge_lags_v1',
             'backtest':[{'date':str(dates[7+split+i]),'actual':float(actual),'model_prediction':float(predicted[i]),'baseline_prediction':float(baseline[i])} for i,actual in enumerate(target[split:])]}
    if not all(math.isfinite(v) for v in [mae,base_mae,payload['intercept'],*payload['coef']]):raise OperationError('Numerical training failure')
    return payload


def forecast(payload,horizon=7):
    horizon=int(horizon)
    if not 1<=horizon<=30:raise OperationError('Forecast horizon must be 1 to 30 days')
    values=list(payload['tail']);result=[];cutoff=day(payload['cutoff'])
    for step in range(1,horizon+1):
        when=cutoff+timedelta(days=step)
        x=np.array(features(values,when))
        predicted=float(values[-7]) if payload['method']=='Seasonal baseline' else float(np.dot((x-np.array(payload['mean']))/np.array(payload['scale']),np.array(payload['coef']))+payload['intercept'])
        predicted=max(0,predicted)
        if not math.isfinite(predicted) or predicted>1e12:raise OperationError('Forecast exceeds numeric limits')
        values.append(predicted);result.append({'date':str(when),'predicted_demand_kg':predicted})
    return result


def train_and_save(path,market_id,crop,horizon=7):
    frame=historical_series(path,market_id,crop);payload=train_series(frame);predictions=forecast(payload,horizon)
    with connection(path,True) as con:
        # Recheck the exact input snapshot to reject a concurrent historical correction.
        latest=pd.read_sql_query('SELECT event_date,demand,stockout,basis,source FROM ops_history WHERE market_id=? AND crop=? ORDER BY event_date',con,params=(int(market_id),str(crop).strip().casefold()))
        if latest.to_json(orient='records',double_precision=15)!=frame.to_json(orient='records',double_precision=15):raise OperationError('History changed while fitting; train again')
        cursor=con.execute('INSERT INTO ops_models(market_id,crop,created_at,cutoff,payload) VALUES (?,?,?,?,?)',(int(market_id),str(crop).strip().casefold(),now(),payload['cutoff'],json.dumps(payload,allow_nan=False)))
        model_id=cursor.lastrowid
        con.executemany('INSERT INTO ops_forecasts(model_id,event_date,predicted) VALUES (?,?,?)',[(model_id,r['date'],r['predicted_demand_kg']) for r in predictions])
        audit(con,'Trained forecast',model_id)
        return model_id,payload,predictions


def forecast_report(path,model_id):
    with connection(path) as con:
        row=con.execute('SELECT market_id,crop,payload FROM ops_models WHERE id=?',(int(model_id),)).fetchone()
        if not row:raise OperationError('Model run not found')
        payload=json.loads(row[2]);rows=pd.read_sql_query('''SELECT f.event_date,f.predicted,h.demand actual,h.basis,h.stockout FROM ops_forecasts f LEFT JOIN ops_history h ON h.event_date=f.event_date AND h.market_id=? AND h.crop=? WHERE f.model_id=? ORDER BY f.event_date''',con,params=(row[0],row[1],int(model_id)))
    eligible=rows.actual.notna()&(rows.basis==payload['basis'])
    if payload['basis']=='Sales proxy':eligible&=rows.stockout.eq(0)
    error=float((rows.loc[eligible,'actual']-rows.loc[eligible,'predicted']).abs().mean()) if eligible.any() else None
    return payload,rows,error,int(eligible.sum())
