import copy
from io import BytesIO
import json
from pathlib import Path
import zipfile
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from harvest.business import (change_record,apply_records,save_version,load_version,list_versions,
                              current_revision,workspace_backup,fingerprint,RevisionConflict)
from harvest.storage import load_workspace,load_snapshot
from harvest.risk import RiskPolicy
from harvest.i18n import LATIN,TAMIL
from test_phase6 import rendered_strings

APP=str(Path(__file__).resolve().parents[1]/'app.py')


def test_record_add_edit_delete_preserves_input(agriculture):
    original=agriculture.copy(deep=True)
    values={'crop':'Beans','available_kg':90,'estimated_demand_kg':50,'market_price_per_kg':12,'harvest_age_days':1}
    added=change_record(agriculture,'agriculture',values)
    assert len(added)==4 and len(agriculture)==3
    changed=change_record(added,'agriculture',{**values,'available_kg':110},index=3)
    assert changed.iloc[3].available_kg==110
    pd.testing.assert_frame_equal(agriculture,original)
    assert len(change_record(changed,'agriculture',index=3,delete=True))==3
    assert change_record(agriculture.iloc[:1],'agriculture',index=0,delete=True) is None


@pytest.mark.parametrize('mutation',[{'available_kg':-1},{'estimated_demand_kg':float('nan')},{'crop':''},{'crop':' TOMATOES '}])
def test_invalid_record_edit_is_atomic(agriculture,mutation):
    original=agriculture.copy(deep=True)
    row=agriculture.iloc[1].to_dict();row.update(mutation)
    with pytest.raises(ValueError):change_record(agriculture,'agriculture',row,index=1)
    pd.testing.assert_frame_equal(agriculture,original)


def test_buyer_duplicates_and_source_order(buyers):
    with pytest.raises(ValueError):change_record(buyers,'buyers',buyers.iloc[0].to_dict())
    row=buyers.iloc[1].to_dict();row['required_kg']=60
    changed=change_record(buyers,'buyers',row,index=1)
    assert changed.buyer_name.tolist()==buyers.buyer_name.tolist()
    assert changed.iloc[1].required_kg==60 and buyers.iloc[1].required_kg==80
    with pytest.raises(ValueError):change_record(buyers,'buyers',row,index=99)


def state_for(agriculture,buyers):
    state={'risk_policy':RiskPolicy().to_dict()}
    apply_records(state,agriculture,'agriculture');apply_records(state,buyers,'buyers')
    return state


def test_versions_are_atomic_and_restore_both_datasets(agriculture,buyers,tmp_path):
    state=state_for(agriculture,buyers);path=tmp_path/'workspace.db'
    assert current_revision(path)==0
    assert save_version(state,path,'Before',0)==1
    state['active_data'].loc[0,'available_kg']=700
    assert save_version(state,path,'After',1)==2
    assert [v['revision'] for v in list_versions(path)]==[2,1]
    first=load_version(path,1)
    assert first['active_data'].iloc[0].available_kg==500
    assert len(first['active_buyers'])==3
    assert load_workspace(path)['active_data'].iloc[0].available_kg==700
    with pytest.raises(RevisionConflict):save_version(first,path,'Stale session',1)
    assert current_revision(path)==2 and len(list_versions(path))==2
    state['active_data'].loc[0,'available_kg']=-1
    with pytest.raises(ValueError):save_version(state,path,'Invalid',2)
    assert current_revision(path)==2


def test_empty_saved_version_does_not_resurrect_deleted_stock(agriculture,buyers,tmp_path):
    state=state_for(agriculture,buyers);path=tmp_path/'workspace.db'
    save_version(state,path,'Original',0)
    apply_records(state,None,'agriculture');apply_records(state,None,'buyers')
    save_version(state,path,'Cleared',1)
    assert load_workspace(path)['active_data'] is None
    assert load_workspace(path)['active_buyers'] is None
    assert load_snapshot(path) is None
    assert len(load_version(path,1)['active_data'])==3


def test_backup_is_lossless_and_does_not_mutate(agriculture,buyers):
    state=state_for(agriculture,buyers);before=fingerprint(state)
    with zipfile.ZipFile(BytesIO(workspace_backup(state))) as archive:
        assert set(archive.namelist())=={'workspace.json','agriculture.csv','buyers.csv'}
        data=json.loads(archive.read('workspace.json'))
        assert data['active_data'][0]['crop']=='Tomatoes'
        assert data['active_buyers'][0]['transport_cost']==200
    assert fingerprint(state)==before


@pytest.mark.parametrize('language',['English','தமிழ்'])
def test_workspace_forms_and_language(language,tmp_path,monkeypatch):
    monkeypatch.setenv('HARVEST_DB_PATH',str(tmp_path/'ui.db'))
    app=AppTest.from_file(APP).run()
    def widget(kind,prefix):return next(w for w in getattr(app,kind) if w.key.split('__ui_')[0]==prefix)
    next(w for w in app.selectbox if w.key.startswith('language_')).set_value(language).run()
    widget('radio','navigation').set_value('Workspace').run()
    name=next(w for w in app.text_input if w.key.endswith('_crop'))
    name.set_value('Beans' if language=='English' else 'பீன்ஸ்')
    next(w for w in app.number_input if w.key.endswith('_available_kg')).set_value(90)
    next(w for w in app.number_input if w.key.endswith('_estimated_demand_kg')).set_value(50)
    app.button(key='save_record_agriculture').click().run()
    assert not app.exception and len(app.session_state['active_data'])==1
    assert app.session_state['active_data'].iloc[0].available_kg==90
    app.text_input(key='version_name').set_value('First' if language=='English' else 'முதல்')
    app.button(key='save_workspace_version').click().run()
    assert not app.exception and app.session_state['_base_revision']==1
    pattern=TAMIL if language=='English' else LATIN
    assert all(not pattern.search(text) for text in rendered_strings(app))
    # Editing the row updates current calculations, without replacing its identity.
    widget('selectbox','record_action_agriculture').set_value('Edit record').run()
    next(w for w in app.number_input if w.key.endswith('_available_kg')).set_value(120)
    app.button(key='save_record_agriculture').click().run()
    assert not app.exception and app.session_state['active_data'].iloc[0].available_kg==120
    widget('radio','navigation').set_value('Dashboard').run()
    assert [m.value for m in app.metric]==['1','120','50','70','0']


def test_backup_cli_round_trip_and_invalid_backup(agriculture,buyers,tmp_path):
    import subprocess,sys
    root=Path(APP).parent
    original=tmp_path/'source.db';recovered=tmp_path/'restored.db';archive=tmp_path/'backup.zip'
    state=state_for(agriculture,buyers);save_version(state,original,'Original',0)
    def run(*args):
        return subprocess.run([sys.executable,str(root/'manage.py'),*map(str,args)],capture_output=True,text=True)
    result=run('--database',original,'backup',archive)
    assert result.returncode==0,result.stderr
    assert run('--database',original,'backup',archive).returncode!=0
    result=run('--database',recovered,'restore',archive,'--replace-current')
    assert result.returncode==0,result.stderr
    restored=load_workspace(recovered)
    pd.testing.assert_frame_equal(restored['active_data'],agriculture,check_dtype=False)
    assert len(restored['active_buyers'])==3
    invalid=tmp_path/'invalid.zip'
    with zipfile.ZipFile(invalid,'w') as z:z.writestr('workspace.json','{"schema_version":1,"active_data":[{"crop":"Beans"}]}')
    assert run('--database',recovered,'restore',invalid,'--replace-current').returncode!=0
    assert current_revision(recovered)==1


def test_empty_dataset_can_be_saved_after_confirmed_ui_removal(tmp_path,monkeypatch):
    monkeypatch.setenv('HARVEST_DB_PATH',str(tmp_path/'delete.db'))
    app=AppTest.from_file(APP).run()
    app.session_state['active_data']=pd.DataFrame([{'crop':'Beans','available_kg':90,'estimated_demand_kg':50,'market_price_per_kg':12,'harvest_age_days':1}])
    def widget(kind,key):return next(w for w in getattr(app,kind) if w.key.split('__ui_')[0]==key)
    widget('radio','navigation').set_value('Workspace').run()
    widget('selectbox','record_action_agriculture').set_value('Delete record').run()
    assert app.button(key='delete_record_agriculture').disabled
    app.checkbox(key='record_delete_confirm_agriculture').check().run()
    app.button(key='delete_record_agriculture').click().run()
    assert app.session_state['active_data'] is None
    app.text_input(key='version_name').set_value('Cleared')
    assert not app.button(key='save_workspace_version').disabled
    app.button(key='save_workspace_version').click().run()
    assert not app.exception and app.session_state['_base_revision']==1
    assert load_workspace(tmp_path/'delete.db')['active_data'] is None
