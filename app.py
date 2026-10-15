"""CEBAFEX Agri business workspace. Run: python -m streamlit run app.py."""
import os
import sqlite3
from pathlib import Path
from harvest.locale_ui import st,setup_locale
from harvest.ingestion import prepare_dataset,activate_dataset
from harvest.i18n import Translator
from harvest.storage import load_workspace
from harvest.business import current_revision,RevisionConflict
from harvest.business_view import business_view,persist,restore_into_session
from harvest.brand import apply_brand,sidebar_brand,workspace_status,home_view
from harvest.views import upload_view,dashboard_view
from harvest.risk import RiskPolicy
from harvest.risk_view import risk_view
from harvest.matching_view import matching_view
from harvest.financial_view import financial_view
from harvest.assistant_view import assistant_view
from harvest import operations as op
from harvest import operations_view as ov
from harvest.forecast_view import history_view

ROOT=Path(__file__).resolve().parent
DB=Path(os.environ.get('HARVEST_DB_PATH',str(ROOT/'data/cebafex.sqlite3')))
PAGES=['Home','Upload Data','Dashboard','Surplus and Risk','Buyer Matching','Profit Analysis','AI Assistant','Workspace','Supply Network','History and Forecasts','Outcome Evaluation']
previous_language=st.session_state.get('language','English')
st.set_page_config(page_title=Translator(previous_language)('CEBAFEX Agri'),page_icon=str(ROOT/'static/brand/cebafex-logo.png'),layout='wide')
setup_locale();apply_brand()
language_widget_key='language_'+previous_language

def change_language():
    st.session_state.language=st.session_state[language_widget_key]

language=st.sidebar.selectbox(Translator(previous_language)('Language'),['English','தமிழ்'],
    index=0 if previous_language=='English' else 1,key=language_widget_key,on_change=change_language)
st.session_state.language=language
t=Translator(language)
for key,default in [('active_data',None),('active_buyers',None),('source','No active dataset'),
    ('agriculture_metadata',None),('buyers_metadata',None),('risk_policy',RiskPolicy().to_dict())]:
    st.session_state.setdefault(key,default)
if '_base_revision' not in st.session_state:
    try:st.session_state['_base_revision']=current_revision(DB)
    except (OSError,sqlite3.Error):st.session_state['_base_revision']=0

source_mode=st.sidebar.selectbox(t('Planning source'),['planning','ledger'],format_func=lambda v:t('Uploaded workspace' if v=='planning' else 'Operational ledger'),key='planning_source')
last_mode=st.session_state.get('_last_planning_source','planning')
projection_keys=['active_data','active_buyers','agriculture_metadata','buyers_metadata','source']
if source_mode=='ledger':
    if last_mode=='planning':st.session_state['_planning_cache']={key:st.session_state.get(key) for key in projection_keys}
    operational=op.snapshot(DB)
    projection=op.planning_projection(operational)
    st.session_state['active_data']=projection
    st.session_state['active_buyers']=None
    st.session_state['agriculture_metadata']={'origin':'operations','rows':len(projection) if projection is not None else 0}
    st.session_state['buyers_metadata']=None
    st.session_state['source']='Operational ledger'
elif last_mode=='ledger':
    st.session_state.update(st.session_state.get('_planning_cache',{}))
st.session_state['_last_planning_source']=source_mode
sidebar_brand(t)
page=st.sidebar.radio(t('Navigation'),PAGES,format_func=t,key='navigation')
st.sidebar.divider()
if source_mode=='planning':
    with st.sidebar.expander(t('Data and reports')):
        if st.button(t('Load demo data'),key='load_demo',width='stretch'):
            prepared=[prepare_dataset((ROOT/'data'/filename).read_bytes(),filename,kind,origin='sample')
                      for kind,filename in [('agriculture','agriculture_demo.csv'),('buyers','buyers_demo.csv')]]
            if any(result.errors for result,_ in prepared):st.error(t('Demo validation failed'))
            else:
                for result,meta in prepared:activate_dataset(st.session_state,result,meta)
                for key in ['report_agriculture','report_buyers']:st.session_state.pop(key,None)
        if st.button(t('Restore local snapshot'),key='restore_snapshot',width='stretch'):
            try:
                restored=load_workspace(DB)
                if restored:
                    restore_into_session(st.session_state,restored,DB)
                    st.success(t('Restored'))
                else:st.info(t('No saved snapshot'))
            except (OSError,ValueError,TypeError,sqlite3.Error):
                st.error(t('Could not access workspace storage. Check the configured folder permissions.'))
        if st.session_state.active_data is not None or st.session_state.active_buyers is not None or st.session_state.get('_records_changed'):
            if st.button(t('Save local snapshot'),key='save_snapshot',width='stretch'):
                try:
                    persist(st.session_state,DB,t('Saved version {n}',n=st.session_state['_base_revision']+1))
                    st.success(t('Saved'))
                except RevisionConflict:st.error(t('Another session saved a newer version. Restore the latest saved workspace before saving again.'))
                except (OSError,ValueError,TypeError,sqlite3.Error):
                    st.error(t('Could not access workspace storage. Check the configured folder permissions.'))
t.configure(st.session_state.get('active_data'),st.session_state.get('active_buyers'))
st.sidebar.caption(t('Source: {origin}',origin=t((st.session_state.get('agriculture_metadata') or {}).get('origin','unknown'))))
st.sidebar.caption(t('Private local workspace'))
workspace_status(t)
st.title(t('CEBAFEX Agri'))
st.header(t(page))
if source_mode=='ledger':st.caption(t('Operational balances are calculated from recorded movements and reservations. Demand remains a separate entered estimate.'))
if page=='Home':
    if source_mode=='ledger':ov.overview_view(t,DB,home=True)
    else:home_view(t)
elif page=='Upload Data':
    if source_mode=='ledger':st.info(t('Use Supply Network to manage ledger records; switch to Uploaded workspace to edit or upload planning snapshots.'))
    else:upload_view(t)
elif page=='Dashboard':
    if source_mode=='ledger':ov.overview_view(t,DB)
    else:dashboard_view(t)
elif page=='Surplus and Risk':
    if source_mode=='ledger':ov.overview_view(t,DB,risk=True)
    else:risk_view(t)
elif page=='Buyer Matching':
    if source_mode=='ledger':ov.matching_view(t,DB)
    else:matching_view(t)
elif page=='Profit Analysis':
    if source_mode=='ledger':ov.evaluation_view(t,DB)
    else:financial_view(t)
elif page=='AI Assistant':
    if source_mode=='ledger':ov.assistant_view(t,DB)
    else:assistant_view(t)
elif page=='Workspace':
    if source_mode=='ledger':st.info(t('Use Supply Network to manage ledger records; switch to Uploaded workspace to edit or upload planning snapshots.'))
    else:business_view(t,DB)
elif page=='Supply Network':ov.network_view(t,DB)
elif page=='History and Forecasts':history_view(t,DB)
elif page=='Outcome Evaluation':ov.evaluation_view(t,DB)
