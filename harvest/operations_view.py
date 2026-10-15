"""Operational UI. All stock, matching and outcome calculations live in pure/SQL modules."""
from datetime import date,timedelta
import sqlite3,uuid
import pandas as pd
from .locale_ui import st
from .i18n import LABELS,LATIN,TAMIL
from . import operations as op
from .views import number

COLUMNS={
'id':'Identifier','name':'Name','location':'Location','latitude':'Latitude','longitude':'Longitude','role':'Participant role','market_id':'Market identifier','supplier_id':'Supplier identifier','buyer_id':'Buyer identifier',
'crop':'Crop','grade':'Grade','received':'Received quantity (kg)','local_demand':'Local demand estimate (kg)','market_price':'Market price (₹/kg)','harvest_date':'Harvest date','ready_date':'Ready date','freshness':'Reported freshness','storage_notes':'Storage notes',
'physical_kg':'Physical stock (kg)','reserved_kg':'Reserved stock (kg)','free_kg':'Free stock (kg)','surplus_kg':'Allocatable surplus (kg)',
'supplier_name':'Supplier','market_name':'Market','buyer_name':'Buyer','buyer_type':'Buyer type','min_grade':'Minimum grade','required':'Required quantity (kg)','offer_price':'Offer price (₹/kg)','transport_quote':'Transport cost (₹)','delivery_by':'Delivery deadline','max_distance':'Maximum straight-line distance (km)','inspection_required':'Acceptable inspection required','remaining_kg':'Remaining buyer requirement (kg)',
'lot_id':'Lot','request_id':'Request','order_id':'Order','quantity':'Actual quantity (kg)','event_date':'Date','event_type':'Outcome type','unit_price':'Actual unit price (₹/kg)','transport':'Actual transport (₹)','other_costs':'Other recorded costs (₹)','status':'Order status','created_at':'Saved at','response_date':'Response date','response_note':'Response notes','accepted_at':'Confirmation recorded at',
'age_days':'Harvest age (days)','review_reasons':'Reasons','score':'Score','eligible':'Eligible','distance_km':'Distance (km)','potential_kg':'Potential quantity (kg)','estimated_return':'Estimated return (₹)','reasons':'Reasons','sold_kg':'Sold quantity (kg)','confirmed_kg':'Confirmed quantity (kg)',
'estimated_full_return':'Estimated full-order return (₹)','estimated_sold_return':'Estimated sold-share return (₹)','actual_gross':'Actual gross (₹)','actual_transport':'Actual transport (₹)','actual_other':'Other recorded costs (₹)','actual_after_transport':'Actual after transport (₹)','actual_after_recorded_costs':'Actual after recorded costs (₹)','difference':'Actual minus sold-share estimate (₹)',
}


def show_table(frame,t,columns=None):
    if isinstance(frame,list):frame=pd.DataFrame(frame)
    if frame.empty:return
    columns=columns or list(frame.columns)
    result={}
    for field in columns:
        if field not in frame:continue
        values=[]
        for i,value in enumerate(frame[field]):
            if isinstance(value,list):value='; '.join(t(v) for v in value)
            if pd.isna(value):value=t('Not available')
            elif isinstance(value,str):
                if field in ['created_at','accepted_at']:value=value.replace('T',' ').split('+')[0]
                elif value in LABELS:value=t(value)
                else:value=t.entity(value,'Crop' if field=='crop' else 'Text',i+1)
            elif isinstance(value,bool):value=t('Yes' if value else 'No')
            values.append(value)
        result[t(COLUMNS.get(field,field))]=values
    st.dataframe(pd.DataFrame(result),hide_index=True,width='stretch')


def choose(t,label,frame,key,name='name'):
    if frame.empty:return None
    lookup=frame.set_index('id')
    return st.selectbox(t(label),list(map(int,frame.id)),format_func=lambda i:str(i)+' · '+t.entity(lookup.loc[i,name],'Crop' if name=='crop' else 'Text',i),key=key)


def qty(t,label,key,value=0):return st.number_input(t(label),min_value=0.0,max_value=1e12,value=float(value),step=1.0,key=key)


def commit(call,key=None):
    try:
        result=call()
        if key:st.session_state[key]=str(uuid.uuid4())
        st.session_state['_ops_flash']=True;st.rerun()
    except (op.OperationError,ValueError) as exc:st.error(str(exc))
    except sqlite3.Error:st.error('Could not access workspace storage. Check the configured folder permissions.')


def network_view(t,path):
    data=op.snapshot(path)
    if st.session_state.pop('_ops_flash',False):st.success(t('Record saved to the ledger.'))
    st.info(t('Ledger records are durable immediately and are separate from planning snapshot history.'))
    st.caption(t('Freshness and locations are user-reported, not independently verified.'))
    labels=['Markets','Participants','Stock lots','Buyer requests','Orders and outcomes','Ledger backup']
    tabs=st.tabs([t(v) for v in labels],key='ops_tabs_'+t.language,on_change='rerun')
    with tabs[0]:
        with st.form('ops_market_form'):
            name=st.text_input(t('Market name'),key='ops_market_name',max_chars=200)
            location=st.text_input(t('Location'),key='ops_market_location',max_chars=200)
            coordinates=st.checkbox(t('Coordinates available'),key='ops_coordinates')
            lat=st.number_input(t('Latitude'),min_value=-90.0,max_value=90.0,value=0.0,key='ops_lat')
            lon=st.number_input(t('Longitude'),min_value=-180.0,max_value=180.0,value=0.0,key='ops_lon')
            if st.form_submit_button(t('Create market'),key='ops_add_market'):
                commit(lambda:op.registry(path,'markets',{'name':name,'location':location,'latitude':lat if coordinates else None,'longitude':lon if coordinates else None}))
        show_table(data['markets'],t)
    with tabs[1]:
        if data['markets'].empty:st.info(t('Create markets and participants before adding stock or requests.'))
        else:
            participant=st.selectbox(t('Add participant'),['Supplier','Buyer'],format_func=t,key='ops_participant_kind')
            with st.form('ops_participant_form'):
                name=st.text_input(t('Participant name'),key='ops_participant_name',max_chars=200)
                role=st.selectbox(t('Participant role'),(['Farmer','Vendor','Cooperative','Distributor'] if participant=='Supplier' else ['Restaurant','Hostel','Retailer','Wholesaler','Other']),format_func=t,key='ops_participant_role')
                market=choose(t,'Market',data['markets'],'ops_participant_market')
                if st.form_submit_button(t('Create participant'),key='ops_add_participant'):
                    commit(lambda:op.registry(path,'suppliers' if participant=='Supplier' else 'buyers',{'name':name,'role':role,'market_id':market}))
        show_table(data['suppliers'],t);show_table(data['buyers'],t)
    with tabs[2]:
        if data['suppliers'].empty:st.info(t('Create markets and participants before adding stock or requests.'))
        else:
            with st.form('ops_lot_form'):
                supplier=choose(t,'Supplier',data['suppliers'],'ops_lot_supplier')
                crop=st.text_input(t('Crop'),key='ops_lot_crop',max_chars=200)
                grade=st.selectbox(t('Grade'),['A','B','C'],format_func=t,key='ops_lot_grade')
                received=qty(t,'Received quantity (kg)','ops_received')
                demand=qty(t,'Local demand estimate (kg)','ops_demand')
                price=qty(t,'Market price (₹/kg)','ops_market_price')
                harvest=st.date_input(t('Harvest date'),value=date.today(),key='ops_harvest')
                ready=st.date_input(t('Ready date'),value=date.today(),key='ops_ready')
                freshness=st.selectbox(t('Reported freshness'),['Not assessed','Acceptable','Needs inspection','Unsuitable'],format_func=t,key='ops_freshness')
                notes=st.text_input(t('Storage notes'),key='ops_storage_notes',max_chars=1000)
                if st.form_submit_button(t('Create stock lot'),key='ops_add_lot'):
                    commit(lambda:op.add_lot(path,{'supplier_id':supplier,'crop':crop,'grade':grade,'received':received,'local_demand':demand,'market_price':price,'harvest_date':harvest,'ready_date':ready,'freshness':freshness,'storage_notes':notes}))
        show_table(data['lots'],t,['id','supplier_name','market_name','crop','grade','physical_kg','reserved_kg','free_kg','surplus_kg','harvest_date','ready_date','freshness','storage_notes'])
        if not data['lots'].empty:
            with st.expander(t('Review stock assumptions')):
                lot=choose(t,'Lot',data['lots'],'ops_review_lot','crop');selected=data['lots'].set_index('id').loc[lot]
                with st.form('ops_review_lot_form_'+str(lot)):
                    local=qty(t,'Local demand estimate (kg)','ops_review_demand_'+str(lot),selected.local_demand)
                    price=qty(t,'Market price (₹/kg)','ops_review_price_'+str(lot),selected.market_price)
                    fresh=st.selectbox(t('Reported freshness'),['Not assessed','Acceptable','Needs inspection','Unsuitable'],index=['Not assessed','Acceptable','Needs inspection','Unsuitable'].index(selected.freshness),format_func=t,key='ops_review_fresh_'+str(lot))
                    notes=st.text_input(t('Storage notes'),key='ops_review_notes_'+str(lot),max_chars=1000)
                    if st.form_submit_button(t('Save review'),key='ops_save_review'):commit(lambda:op.revise_lot(path,lot,local,price,fresh,notes))
    with tabs[3]:
        if data['buyers'].empty:st.info(t('Create markets and participants before adding stock or requests.'))
        else:
            with st.form('ops_request_form'):
                buyer=choose(t,'Buyer',data['buyers'],'ops_request_buyer')
                crop=st.text_input(t('Crop'),key='ops_request_crop',max_chars=200)
                grade=st.selectbox(t('Minimum grade'),['A','B','C'],format_func=t,key='ops_request_grade')
                quantity=qty(t,'Required quantity (kg)','ops_request_quantity')
                offer=qty(t,'Offer price (₹/kg)','ops_offer')
                transport=qty(t,'Transport cost (₹)','ops_quote')
                deadline=st.date_input(t('Delivery deadline'),value=date.today()+timedelta(days=3),key='ops_deadline')
                limit=st.checkbox(t('Distance limit applies'),key='ops_distance_applies')
                distance=qty(t,'Maximum straight-line distance (km)','ops_distance')
                inspect=st.checkbox(t('Acceptable inspection required'),key='ops_inspection')
                if st.form_submit_button(t('Create buyer request'),key='ops_add_request'):
                    commit(lambda:op.add_request(path,{'buyer_id':buyer,'crop':crop,'min_grade':grade,'required':quantity,'offer_price':offer,'transport_quote':transport,'delivery_by':deadline,'max_distance':distance if limit else None,'inspection_required':inspect}))
            st.caption(t('Quoted transport is per lot-request trip, not a live route estimate.'))
        show_table(data['requests'],t,['id','buyer_name','market_name','crop','min_grade','required','remaining_kg','offer_price','transport_quote','delivery_by','max_distance'])
        if not data['requests'].empty:
            with st.expander(t('Close request')):
                request=choose(t,'Request',data['requests'],'ops_close_request','crop')
                if st.button(t('Close request'),key='ops_close_request_button'):commit(lambda:op.close_request(path,request))
    with tabs[4]:orders_view(t,path,data)
    with tabs[5]:
        st.caption(t('Complete backup includes planning versions, stock ledger, movements, history and saved forecasts.'))
        st.download_button(t('Download complete database backup'),op.database_backup(path),file_name='cebafex_complete.sqlite3',mime='application/octet-stream',key='ops_database_backup')


def matching_view(t,path):
    data=op.snapshot(path);pairs=op.ranked_matches(data['lots'],data['requests'])
    st.warning(t('Sample opportunities only; not confirmed orders') if not len(data['lots']) else t('Confirmation is recorded by the operator; no buyer is contacted or verified automatically.'))
    st.caption(t('Distance is straight-line geography, not driving distance or a delivery guarantee.'))
    with st.expander(t('Ranking rules')):
        st.write(t('Score = grade fit up to 30 + reported freshness up to 20 + straight-line distance up to 20 + quantity coverage up to 30.'))
        st.write(t('Equal grade earns 30; better grade earns 25. Acceptable freshness earns 20, unassessed 10, inspection-needed 0. Distance points are max(0, 20 − km/10), or 0 if unknown.'))
        st.write(t('Quantity coverage earns 30 × min(free surplus/request remainder, 1). Ties use estimated return, then lot and request identifiers.'))
        st.caption(t('Ranking is a planning rule, not a learned probability. Quantities are capped across all preview pairs.'))
    show_table(pairs,t,['lot_id','request_id','crop','supplier_name','buyer_name','eligible','score','distance_km','potential_kg','estimated_return','reasons'])
    eligible=[p for p in pairs if p['eligible'] and p['potential_kg']>0]
    if not eligible:st.info(t('No suitable free surplus pairs.'));return
    options={str(r['lot_id'])+':'+str(r['request_id']):r for r in eligible}
    selected=st.selectbox(t('Record proposal'),list(options),format_func=lambda key:t('Lot')+' '+key.split(':')[0]+' · '+t('Request')+' '+key.split(':')[1],key='ops_proposal_pair')
    row=options[selected];st.session_state.setdefault('ops_proposal_token',str(uuid.uuid4()))
    with st.form('ops_proposal_form_'+selected):
        quantity=qty(t,'Proposal quantity (kg)','ops_proposal_qty_'+selected,row['potential_kg'])
        if st.form_submit_button(t('Create proposal'),key='ops_propose'):
            commit(lambda:op.propose(path,row['lot_id'],row['request_id'],quantity,st.session_state['ops_proposal_token']),'ops_proposal_token')
    st.caption(t('Only actual outcomes consume physical stock. Proposals do not reserve it; accepted orders reserve it.'))


def orders_view(t,path,data):
    st.caption(t('Only actual outcomes consume physical stock. Proposals do not reserve it; accepted orders reserve it.'))
    orders=data['orders'];lots=data['lots']
    show_table(orders,t,['id','lot_id','request_id','quantity','status','response_date','response_note'])
    available=orders.loc[orders.status.isin(['Proposed','Accepted'])]
    if not available.empty:
        with st.form('ops_response_form'):
            order=choose(t,'Order',available.assign(name=available.id.astype(str)),'ops_response_order')
            response=st.selectbox(t('Buyer response'),['Accepted','Declined','Cancelled'],format_func=t,key='ops_response')
            when=st.date_input(t('Response date'),value=date.today(),key='ops_response_date')
            notes=st.text_input(t('Response notes'),key='ops_response_notes',max_chars=1000)
            if st.form_submit_button(t('Save response'),key='ops_save_response') and when is not None:commit(lambda:op.respond(path,order,response,notes,when))
        st.caption(t('Confirmation is recorded by the operator; no buyer is contacted or verified automatically.'))
    if lots.empty:return
    event=st.selectbox(t('Outcome type'),['Sale','Redistribution','Discard'],format_func=t,key='ops_event_type')
    accepted=orders.loc[orders.status=='Accepted']
    if event=='Sale' and accepted.empty:st.info(t('Choose an accepted order'));return
    st.session_state.setdefault('ops_movement_token',str(uuid.uuid4()))
    with st.form('ops_movement_form_'+event):
        order_id=None
        if event=='Sale':
            order_id=choose(t,'Order',accepted.assign(name=accepted.id.astype(str)),'ops_sale_order');lot=int(accepted.set_index('id').loc[order_id,'lot_id'])
        else:lot=choose(t,'Lot',lots,'ops_outcome_lot','crop')
        quantity=qty(t,'Actual quantity (kg)','ops_outcome_quantity_'+event)
        when=st.date_input(t('Actual event date'),value=date.today(),key='ops_outcome_date_'+event)
        price=qty(t,'Actual unit price (₹/kg)','ops_actual_price_'+event) if event=='Sale' else 0
        transport=qty(t,'Actual transport (₹)','ops_actual_transport_'+event)
        other=qty(t,'Other recorded costs (₹)','ops_actual_other_'+event)
        notes=st.text_input(t('Outcome notes'),key='ops_outcome_notes_'+event,max_chars=1000)
        if st.form_submit_button(t('Save actual outcome'),key='ops_save_outcome'):
            commit(lambda:op.movement(path,lot,event,quantity,when,price,transport,other,order_id,notes,st.session_state['ops_movement_token']),'ops_movement_token')
    show_table(data['movements'],t,['id','lot_id','order_id','event_date','event_type','quantity','unit_price','transport','other_costs'])


def evaluation_view(t,path):
    report=op.evaluation(op.snapshot(path))
    metrics=[('Physical stock (kg)','physical_kg'),('Reserved stock (kg)','reserved_kg'),('Sold quantity (kg)','sold_kg'),('Redistributed quantity (kg)','redistributed_kg'),('Discarded quantity (kg)','discarded_kg')]
    for start in range(0,len(metrics),3):
        for col,(label,key) in zip(st.columns(min(3,len(metrics)-start)),metrics[start:start+3]):col.metric(t(label),number(report[key]))
    a,b,c=st.columns(3);a.metric(t('Recorded proposals'),str(report['proposals']));b.metric(t('Proposals with recorded sales'),str(report['purchases']));c.metric(t('Purchase conversion (%)'),f"{100*report['conversion']:.1f}" if report['conversion'] is not None else '—')
    for col,(label,key) in zip(st.columns(4),[('Actual gross (₹)','actual_gross'),('All outcome transport (₹)','all_transport'),('All outcome other costs (₹)','all_other'),('After all recorded costs (₹)','after_all_recorded_costs')]):
        col.metric(t(label),f"₹{report[key]:,.2f}")
    st.caption(t('Cost totals include sales, redistribution and discard events.'))
    show_table(report['orders'],t)
    st.caption(t('For partial sales, the quoted transport is allocated in proportion to sold quantity for comparison only. Actual trips use their recorded costs.'))
    st.warning(t('After recorded costs is not profit unless all relevant business costs have been captured.'))
    st.info(t('Recorded sales or redistribution do not prove how much waste would otherwise have occurred. Waste avoided is not measured.'))


def assistant_view(t,path):
    st.info(t('Rule-based assistant; no external model or live information is used.'))
    topic=st.selectbox(t('Suggested question'),['Ledger overview','Buyer suitability','Actual outcomes','Forecast evidence'],format_func=t,key='ops_assistant_topic')
    data=op.snapshot(path);report=op.evaluation(data);pairs=op.ranked_matches(data['lots'],data['requests'])
    if topic=='Ledger overview':
        st.write(t('Physical {physical} kg; reserved {reserved} kg; recorded sales {sold} kg.',physical=number(report['physical_kg']),reserved=number(report['reserved_kg']),sold=number(report['sold_kg'])))
        projection=op.planning_projection(data)
        if projection is not None:
            from .analytics import crop_balances
            balances=data['lots'].groupby('crop',as_index=False).surplus_kg.sum().rename(columns={'surplus_kg':'potential_surplus_kg'}).sort_values(['potential_surplus_kg','crop'],ascending=[False,True])
            if balances.iloc[0].potential_surplus_kg>0:
                row=balances.iloc[0];st.write(t('Largest free surplus: {crop}, {quantity} kg.',crop=t.entity(row.crop,'Crop'),quantity=number(row.potential_surplus_kg)))
            show_table(data['lots'],t,['id','crop','physical_kg','reserved_kg','surplus_kg','freshness'])
    elif topic=='Buyer suitability':
        active=[p for p in pairs if p['eligible'] and p['potential_kg']>0]
        st.write(t('Eligible preview pairs: {count}; potential quantity {quantity} kg.',count=len(active),quantity=number(sum(p['potential_kg'] for p in active))))
        show_table(active,t,['lot_id','request_id','score','distance_km','potential_kg','estimated_return'])
        st.caption(t('Ranking is a planning rule, not a learned probability. Quantities are capped across all preview pairs.'))
    elif topic=='Actual outcomes':
        st.write(t('Proposals {proposals}; proposals with sales {purchases}.',proposals=report['proposals'],purchases=report['purchases']))
        show_table(report['orders'],t)
    else:
        from .operations import connection
        from .forecasting import forecast_report
        with connection(path) as con:runs=pd.read_sql_query('SELECT id,crop,cutoff FROM ops_models ORDER BY id DESC LIMIT 5',con)
        if runs.empty:st.info(t('No saved forecast runs yet.'))
        for run in runs.itertuples():
            payload,_,mae,count=forecast_report(path,run.id)
            st.write(t.entity(run.crop,'Crop')+' · '+t(payload['method'])+' · '+str(run.cutoff))
            st.write(t('Evaluated forecast days')+': '+str(count)+' · '+t('Later-observation MAE (kg)')+': '+(number(mae) if mae is not None else t('Not available')))
    st.caption(t('Entered data is not independently verified. No live routes, orders or market feeds are fabricated.'))


def overview_view(t,path,home=False,risk=False):
    data=op.snapshot(path);totals=op.operational_totals(data)
    if home:
        st.subheader(t('Your crop operations, in one clear workspace.'))
        st.caption(t('Only actual outcomes consume physical stock. Proposals do not reserve it; accepted orders reserve it.'))
    labels=[('Stock lots','records'),('Available (kg)','available_kg'),('Estimated demand (kg)','estimated_demand_kg'),('Potential surplus (kg)','positive_surplus_kg'),('Shortage (kg)','shortage_kg')]
    for start in range(0,len(labels),3):
        for col,(label,key) in zip(st.columns(min(3,len(labels)-start)),labels[start:start+3]):col.metric(t(label),number(totals[key]))
    st.caption(t('Ledger surplus and shortages are summed separately for each stock lot; one market shortage does not cancel another supplier surplus.'))
    if data['lots'].empty:st.info(t('No ledger records yet.'));return
    if risk:
        from .risk import RiskPolicy
        current=RiskPolicy.from_dict(st.session_state.get('risk_policy'))
        with st.form('ops_policy_form'):
            ratio=st.number_input(t('Large surplus threshold (%)'),min_value=.01,max_value=100.0,value=float(current.high_surplus_ratio*100),key='ops_policy_ratio')
            age=st.number_input(t('Harvest age review threshold (days)'),min_value=1.0,value=float(current.age_review_days),key='ops_policy_age')
            if st.form_submit_button(t('Apply planning rules'),key='ops_apply_policy'):
                st.session_state['risk_policy']=RiskPolicy(ratio/100,age).to_dict();st.rerun()
        rows=op.risk_reviews(data,current)
        for row in rows:row['review_reasons']='; '.join(t(reason) for reason in row['review_reasons'])
        show_table(rows,t,['id','supplier_name','market_name','crop','surplus_kg','age_days','freshness','review_reasons'])
        st.caption(t('Inspection urgency comes first, then free surplus, older harvest and lot identifier. These are planning rules, not spoilage predictions.'))
    else:
        show_table(data['lots'],t,['id','supplier_name','market_name','crop','physical_kg','reserved_kg','free_kg','local_demand','surplus_kg','freshness'])
        import plotly.express as px
        chart=data['lots'][['id','crop','free_kg','local_demand']].copy()
        chart['crop']=[t.entity(v,'Crop',i+1)+' · '+str(k) for i,(v,k) in enumerate(zip(chart.crop,chart.id))]
        chart=chart.melt(id_vars='crop',value_vars=['free_kg','local_demand'],var_name='measure',value_name='kg')
        chart['measure']=chart['measure'].map({'free_kg':t('Free stock (kg)'),'local_demand':t('Local demand estimate (kg)')})
        figure=px.bar(chart,x='crop',y='kg',color='measure',pattern_shape='measure',barmode='group',labels={'crop':t('Crop'),'kg':t('Quantity (kg)'),'measure':t('Measure')},color_discrete_sequence=['#087F8C','#075C86'])
        st.plotly_chart(figure,width='stretch')
