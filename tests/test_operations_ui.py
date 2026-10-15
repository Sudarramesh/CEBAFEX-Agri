from pathlib import Path
from datetime import date,timedelta
import base64
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from harvest import operations as op
from harvest import forecasting as fc
from harvest.i18n import LATIN,TAMIL,Translator
from test_phase6 import rendered_strings
from test_operations import ledger
from test_forecast_excel import history,workbook

APP=str(Path(__file__).resolve().parents[1]/'app.py')

def select(app,kind,key):return next(w for w in getattr(app,kind) if w.key.split('__ui_')[0]==key)

@pytest.mark.parametrize('language',['English','தமிழ்'])
def test_all_operational_screens_with_data_follow_language(ledger,monkeypatch,language):
    path,market,_,_,_,_=ledger
    monkeypatch.setenv('HARVEST_DB_PATH',str(path))
    fc.import_history(path,market,history(),source='synthetic_demo');fc.train_and_save(path,market,'Tomatoes',7)
    app=AppTest.from_file(APP).run(timeout=30)
    next(w for w in app.selectbox if w.key.startswith('language_')).set_value(language).run()
    select(app,'selectbox','planning_source').set_value('ledger').run()
    forbidden=TAMIL if language=='English' else LATIN
    for page in ['Home','Dashboard','Surplus and Risk','Buyer Matching','Profit Analysis','AI Assistant','Supply Network','History and Forecasts','Outcome Evaluation','Upload Data','Workspace']:
        select(app,'radio','navigation').set_value(page).run(timeout=30)
        assert not app.exception,(page,[e.message for e in app.exception])
        assert all(not forbidden.search(text) for text in rendered_strings(app)),page
    assert op.snapshot(path)['lots'].iloc[0].physical_kg==500


def test_planning_source_preserves_original_upload_and_refreshes_ledger(ledger,monkeypatch):
    path,_,_,_,lot,request=ledger;monkeypatch.setenv('HARVEST_DB_PATH',str(path))
    app=AppTest.from_file(APP).run();app.button(key='load_demo').click().run()
    select(app,'selectbox','planning_source').set_value('ledger').run()
    select(app,'radio','navigation').set_value('Dashboard').run()
    assert [m.value for m in app.metric]==['1','500','300','200','0']
    order=op.propose(path,lot,request,100);op.respond(path,order,'Accepted');app.run()
    assert [m.value for m in app.metric]==['1','400','300','100','0']
    op.movement(path,lot,'Sale',100,date.today(),28,200,0,order)
    select(app,'radio','navigation').set_value('Outcome Evaluation').run()
    assert [m.value for m in app.metric][:5]==['400','0','100','0','0']
    select(app,'selectbox','planning_source').set_value('planning').run()
    select(app,'radio','navigation').set_value('Dashboard').run()
    assert [m.value for m in app.metric]==['3','1,050','850','250','50']


@pytest.mark.parametrize('language',['English','தமிழ்'])
def test_excel_upload_in_each_language(monkeypatch,language):
    import harvest.locale_ui as ui
    uploads={}
    if language=='தமிழ்':monkeypatch.setattr(ui,'_tamil_upload',lambda **kwargs:uploads.get(kwargs['key']))
    payload=workbook([['crop_nm','qty_avail','est_demand','mkt_prc','harvest_age'],['Tomatoes',500,300,25,2]])
    app=AppTest.from_file(APP).run()
    next(w for w in app.selectbox if w.key.startswith('language_')).set_value(language).run()
    select(app,'radio','navigation').set_value('Upload Data').run()
    if language=='English':app.file_uploader(key='upload_agriculture').upload('stock.xlsx',payload,'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet').run()
    else:
        uploads['upload_agriculture']={'name':'stock.xlsx','content':base64.b64encode(payload).decode()};app.run()
    assert not app.exception
    app.button(key='validate_agriculture').click().run()
    assert not app.exception and len(app.session_state['active_data'])==1


def test_operational_forms_record_proposal_confirm_and_sale(ledger,monkeypatch):
    path,_,_,_,_,_=ledger;monkeypatch.setenv('HARVEST_DB_PATH',str(path))
    app=AppTest.from_file(APP).run()
    select(app,'selectbox','planning_source').set_value('ledger').run()
    select(app,'radio','navigation').set_value('Buyer Matching').run()
    app.button(key='ops_propose').click().run()
    assert not app.exception and len(op.snapshot(path)['orders'])==1
    select(app,'radio','navigation').set_value('Supply Network').run()
    app.button(key='ops_save_response').click().run()
    assert not app.exception
    assert op.snapshot(path)['lots'].iloc[0].reserved_kg==100
    app.number_input(key='ops_outcome_quantity_Sale').set_value(100)
    app.number_input(key='ops_actual_price_Sale').set_value(28)
    app.number_input(key='ops_actual_transport_Sale').set_value(200)
    app.button(key='ops_save_outcome').click().run()
    assert not app.exception
    assert op.snapshot(path)['lots'].iloc[0].physical_kg==400


@pytest.mark.parametrize('language',['English','தமிழ்'])
def test_empty_operational_workspace_can_create_all_source_records(language):
    app=AppTest.from_file(APP).run()
    next(w for w in app.selectbox if w.key.startswith('language_')).set_value(language).run()
    select(app,'selectbox','planning_source').set_value('ledger').run()
    for page in ['Home','Dashboard','Surplus and Risk','Buyer Matching','Profit Analysis','AI Assistant','History and Forecasts','Outcome Evaluation']:
        select(app,'radio','navigation').set_value(page).run()
        assert not app.exception,page
    select(app,'radio','navigation').set_value('Supply Network').run()
    for key,value in [('ops_market_name','Local market' if language=='English' else 'உள்ளூர் சந்தை'),('ops_market_location','Town' if language=='English' else 'நகரம்')]:app.text_input(key=key).set_value(value)
    app.button(key='ops_add_market').click().run()
    app.text_input(key='ops_participant_name').set_value('Farmer' if language=='English' else 'விவசாயி')
    app.button(key='ops_add_participant').click().run()
    select(app,'selectbox','ops_participant_kind').set_value('Buyer').run()
    app.text_input(key='ops_participant_name').set_value('Customer' if language=='English' else 'வாங்குபவர்')
    app.button(key='ops_add_participant').click().run()
    app.text_input(key='ops_lot_crop').set_value('Tomatoes' if language=='English' else 'தக்காளி')
    app.number_input(key='ops_received').set_value(500)
    app.number_input(key='ops_demand').set_value(300)
    app.button(key='ops_add_lot').click().run()
    app.text_input(key='ops_request_crop').set_value('Tomatoes' if language=='English' else 'தக்காளி')
    app.number_input(key='ops_request_quantity').set_value(100)
    app.button(key='ops_add_request').click().run()
    assert not app.exception
    select(app,'radio','navigation').set_value('Dashboard').run()
    assert [m.value for m in app.metric]==['1','500','300','200','0']


def test_invalid_tamil_response_date_cannot_be_saved(ledger,monkeypatch):
    path,_,_,_,lot,request=ledger;monkeypatch.setenv('HARVEST_DB_PATH',str(path))
    op.propose(path,lot,request,100)
    app=AppTest.from_file(APP).run()
    next(w for w in app.selectbox if w.key.startswith('language_')).set_value('தமிழ்').run()
    select(app,'radio','navigation').set_value('Supply Network').run()
    app.text_input(key='ops_response_date__date_ta').set_value('bad-date')
    app.button(key='ops_save_response').click().run()
    assert not app.exception
    assert op.snapshot(path)['orders'].iloc[0].status=='Proposed'
