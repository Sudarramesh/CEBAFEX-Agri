from pathlib import Path
import base64
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from harvest.analytics import calculate_kpis
from harvest.financials import analyse_financials
from harvest.i18n import LATIN,TAMIL
from test_phase6 import rendered_strings

ROOT=Path(__file__).resolve().parents[1]
APP=str(ROOT/'app.py')

@pytest.mark.parametrize('language',['English','தமிழ்'])
def test_full_judging_workflow_from_uploads(language,monkeypatch,tmp_path):
    import harvest.locale_ui as ui
    monkeypatch.setenv('HARVEST_DB_PATH',str(tmp_path/'judging.sqlite3'))
    files={}
    if language=='தமிழ்':
        monkeypatch.setattr(ui,'_tamil_upload',lambda **kwargs:files.get(kwargs.get('key')))
    app=AppTest.from_file(APP).run(timeout=30)
    next(w for w in app.selectbox if w.key.startswith('language_')).set_value(language).run()
    app.button(key='get_started').click().run()
    assert app.session_state['navigation']=='Upload Data'
    def upload(kind,name):
        payload=(ROOT/'data'/name).read_bytes()
        if language=='English':
            app.file_uploader(key=f'upload_{kind}').upload(name,payload,'text/csv').run()
        else:
            files[f'upload_{kind}']={'name':name,'content':base64.b64encode(payload).decode()}
            app.run()
        assert not app.exception
    upload('agriculture','agriculture_messy_demo.csv')
    app.button(key='validate_agriculture').click().run()
    assert app.session_state['active_data'] is None
    result=app.session_state['report_agriculture']['result']
    assert result.summary['missing_cells']==1 and result.summary['invalid_rows']==1
    assert result.issues[0]['record']==3 and result.issues[0]['column']=='market_price_per_kg'
    upload('agriculture','agriculture_demo.csv')
    app.button(key='validate_agriculture').click().run()
    assert app.session_state['agriculture_metadata']['origin']=='uploaded'
    next(w for w in app.radio if w.key.split('__ui_')[0]=='dataset_kind').set_value('buyers').run()
    upload('buyers','buyers_demo.csv')
    app.button(key='validate_buyers').click().run()
    assert app.session_state['buyers_metadata']['origin']=='uploaded'
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Dashboard').run()
    assert [m.value for m in app.metric]==['3','1,050','850','250','50']
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Surplus and Risk').run()
    assert [m.value for m in app.metric]==['250','50','0']
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Buyer Matching').run()
    next(w for w in app.selectbox if w.key.startswith('matching_crop_')).set_value('tomatoes').run()
    assert [m.value for m in app.metric]==['200','180','20']
    report=analyse_financials(app.session_state['active_data'],app.session_state['active_buyers'])
    assert list(report.buyers.estimated_return_after_transport[:2])==[2600,1830]
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Profit Analysis').run()
    next(w for w in app.selectbox if w.key.startswith('financial_crop_')).set_value('tomatoes').run()
    assert [m.value for m in app.metric][:6]==['180','₹4,880.00','₹450.00','₹4,430.00','₹4,500.00','₹-70.00']
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('AI Assistant').run()
    app.button(key='ask_suggestion').click().run()
    assert not app.exception
    pattern=TAMIL if language=='English' else LATIN
    text=list(rendered_strings(app))
    assert all(not pattern.search(value) for value in text)
    assert any('200' in value for value in text)
    assert any('180' in value and '20' in value for value in text)
    assert any('4,430.00' in value for value in text)
    app.button(key='save_snapshot').click().run()
    restored=AppTest.from_file(APP).run()
    restored.button(key='restore_snapshot').click().run()
    assert calculate_kpis(restored.session_state['active_data'])=={'records':3,'available_kg':1050,'estimated_demand_kg':850,'positive_surplus_kg':250,'shortage_kg':50}
    assert len(restored.session_state['active_buyers'])==3


def test_tamil_large_table_is_paged_without_changing_active_data(agriculture):
    rows=pd.concat([agriculture.iloc[[0]].assign(crop=f'Crop {n}') for n in range(60)],ignore_index=True)
    app=AppTest.from_file(APP).run()
    app.session_state['active_data']=rows
    next(w for w in app.selectbox if w.key.startswith('language_')).set_value('தமிழ்').run()
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Dashboard').run()
    assert not app.exception
    selector=next(w for w in app.selectbox if w.key.startswith('locale_table_'))
    assert selector.options==['பக்கம் 1, மொத்தம் 2','பக்கம் 2, மொத்தம் 2']
    assert len(app.table[0].value)==50
    selector.set_value(2).run()
    assert not app.exception and len(app.table[0].value)==10
    assert len(app.session_state['active_data'])==60


def test_language_round_trip_keeps_canonical_selections():
    app=AppTest.from_file(APP).run()
    app.button(key='load_demo').click().run()
    def widget(kind,key):
        return next(w for w in getattr(app,kind) if w.key.split('__ui_')[0]==key)
    widget('radio','navigation').set_value('Buyer Matching').run()
    crop=next(w for w in app.selectbox if w.key.startswith('matching_crop_'))
    crop_key=crop.key.split('__ui_')[0]
    crop.set_value('tomatoes').run()
    for language in ['தமிழ்','English','தமிழ்']:
        next(w for w in app.selectbox if w.key.startswith('language_')).set_value(language).run()
        assert not app.exception
        assert app.session_state[crop_key]=='tomatoes'
        assert [m.value for m in app.metric]==['200','180','20']
    widget('selectbox',crop_key).set_value('onions').run()
    next(w for w in app.selectbox if w.key.startswith('language_')).set_value('English').run()
    assert app.session_state[crop_key]=='onions'
    assert [m.value for m in app.metric]==['50','50','0']
    widget('radio','navigation').set_value('Upload Data').run()
    assert app.session_state['dataset_kind']=='agriculture'
    widget('radio','dataset_kind').set_value('buyers').run()
    next(w for w in app.selectbox if w.key.startswith('language_')).set_value('English').run()
    assert app.session_state['dataset_kind']=='buyers'


@pytest.mark.parametrize('language',['English','தமிழ்'])
def test_financial_hover_uses_currency_unit(language):
    import json
    app=AppTest.from_file(APP).run()
    app.button(key='load_demo').click().run()
    next(w for w in app.selectbox if w.key.startswith('language_')).set_value(language).run()
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Profit Analysis').run()
    spec=json.loads(app.get('plotly_chart')[0].proto.spec)
    assert all('₹: %{y}' in trace['hovertemplate'] for trace in spec['data'])
