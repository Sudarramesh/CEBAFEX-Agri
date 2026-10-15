"""Historical import, explicit target basis, training and later-observation evaluation."""
from datetime import date,timedelta
import hashlib,sqlite3
import pandas as pd
from .locale_ui import st
from .operations import connection,snapshot,OperationError
from .forecasting import import_history,historical_series,train_and_save,forecast_report
from .operations_view import choose
from .tabular import read_table,sheets
from .views import number


def history_view(t,path):
    data=snapshot(path)
    st.info(t('Forecast dates follow the last recorded date, not necessarily today. Forecasts do not overwrite entered demand estimates.'))
    st.caption(t('At least 56 consecutive daily observations are required for each crop and market. Missing dates are not silently filled.'))
    st.download_button(t('Download synthetic history sample'),(__import__('pathlib').Path(__file__).resolve().parents[1]/'data/history_synthetic.csv').read_bytes(),file_name='history_synthetic.csv',mime='text/csv',key='history_example')
    st.warning(t('Synthetic demonstration data, not observed business demand.'))
    if data['markets'].empty:
        st.info(t('Create markets and participants before adding stock or requests.'));return
    market=choose(t,'Market',data['markets'],'history_market')
    with st.expander(t('Import daily history')):
        uploaded=st.file_uploader(t('History file'),type=['csv','xlsx'],key='history_upload')
        basis=st.selectbox(t('Historical target basis'),['Observed demand','Sales proxy'],format_func=t,key='history_basis')
        st.caption(t('Stockout-marked sales are censored and cannot be treated as observed demand.'))
        if uploaded:
            try:
                payload=uploaded.getvalue();digest=hashlib.sha256(payload).hexdigest()[:12];sheet=None
                if uploaded.name.lower().endswith('.xlsx'):sheet=st.selectbox(t('Workbook sheet'),sheets(payload),key='history_sheet_'+digest)
                frame=read_table(payload,uploaded.name,sheet);columns=list(frame.columns)
                st.dataframe(frame.head(10),hide_index=True,width='stretch')
                with st.form('history_mapping_'+digest):
                    mapping={}
                    for canonical,label in [('date','History date column'),('crop','History crop column'),('demand_kg','History quantity column')]:
                        match=next((c for c in columns if c.casefold()==canonical),None)
                        mapping[canonical]=st.selectbox(t(label),[None]+columns,index=columns.index(match)+1 if match else 0,format_func=lambda v:t('Select column') if v is None else v,key='history_map_'+canonical+'_'+digest)
                    flag=st.selectbox(t('Stockout column'),[None]+columns,index=columns.index('stockout')+1 if 'stockout' in columns else 0,format_func=lambda v:t('No stockout column') if v is None else v,key='history_flag_'+digest)
                    replace=st.checkbox(t('Allow explicit corrections to existing observations'),key='history_correct_'+digest)
                    submit=st.form_submit_button(t('Import validated history'),key='history_import')
                if submit:
                    if None in mapping.values() or len(set(mapping.values()))<3:raise OperationError('History columns or size invalid')
                    canonical=frame[list(mapping.values())].copy();canonical.columns=list(mapping)
                    canonical['stockout']=frame[flag] if flag else 0
                    origin='synthetic_demo' if 'source' in frame and frame.source.astype(str).eq('synthetic_demo').all() else uploaded.name
                    import_history(path,market,canonical,basis,origin,replace)
                    st.success(t('Historical records imported.'))
            except (ValueError,OperationError) as exc:st.error(str(exc))
    with connection(path) as con:
        crops=pd.read_sql_query('SELECT DISTINCT crop FROM ops_history WHERE market_id=? ORDER BY crop',con,params=(market,)).crop.tolist()
    if not crops:st.info(t('No ledger records yet.'));return
    crop=st.selectbox(t('Crop'),crops,key='history_crop')
    records=historical_series(path,market,crop)
    # Show normalized target, dates and user-declared provenance in the selected language.
    table=records[['event_date','demand','stockout']].rename(columns={'event_date':t('Date'),'demand':t('Demand (kg)'),'stockout':t('Stockout')})
    st.dataframe(table,hide_index=True,width='stretch')
    st.write(t('Historical target basis')+': '+t(records.basis.iloc[0]))
    if records.source.astype(str).str.contains('synthetic',case=False).any():st.warning(t('Synthetic demonstration data, not observed business demand.'))
    st.subheader(t('Train and compare'))
    st.caption(t('The model uses lag 1, lag 7, seven-day mean, weekday and annual cycles. Older dates train it; the latest at least 14 targets validate it.'))
    st.caption(t('Validation is rolling one-day-ahead; future multi-day forecasts are recursive. The comparison selects the better method and is not an independent final test.'))
    horizon=st.number_input(t('Forecast horizon (days)'),min_value=1,max_value=30,value=7,key='forecast_horizon')
    if st.button(t('Train forecast'),key='train_forecast',type='primary'):
        try:
            run,_,_=train_and_save(path,market,crop,horizon)
            st.session_state['forecast_run']=run
            st.session_state[f'forecast_run__ui_{t.language}']=run
            st.success(t('Forecast trained and saved.'))
        except (ValueError,OperationError) as exc:st.error(str(exc))
    with connection(path) as con:runs=[r[0] for r in con.execute('SELECT id FROM ops_models WHERE market_id=? AND crop=? ORDER BY id DESC',(market,crop))]
    if not runs:return
    run=st.selectbox(t('Saved forecast run'),runs,format_func=lambda v:t('Version {n}',n=v),key='forecast_run')
    payload,rows,mae,count=forecast_report(path,run)
    st.write(t('Model method')+': '+t(payload['method']))
    st.write(t('Forecast cutoff')+': '+payload['cutoff'])
    a,b=st.columns(2);a.metric(t('Ridge validation MAE (kg)'),number(payload['ridge_mae']));b.metric(t('Baseline validation MAE (kg)'),number(payload['baseline_mae']))
    st.subheader(t('Model-generated forecasts'))
    display=rows[['event_date','predicted','actual']].rename(columns={'event_date':t('Forecast date'),'predicted':t('Predicted demand (kg)' if payload['basis']=='Observed demand' else 'Predicted sales proxy (kg)'),'actual':t('Observed quantity (kg)')})
    st.dataframe(display,hide_index=True,width='stretch')
    a,b=st.columns(2);a.metric(t('Evaluated forecast days'),str(count));b.metric(t('Later-observation MAE (kg)'),number(mae) if mae is not None else '—')
    if mae is None:st.info(t('No later observations are available for these forecast dates.'))
    st.download_button(t('Download forecast report'),display.to_csv(index=False).encode('utf-8-sig'),file_name='forecast_report.csv',mime='text/csv',key='download_forecast')
