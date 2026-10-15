from pathlib import Path
import pandas as pd
import pytest
from harvest.data import suggest_mapping, validate_frame
from harvest.ingestion import read_csv_bytes, prepare_dataset, activate_dataset, buyer_coverage
from harvest.storage import save_workspace, load_workspace, save_snapshot
from harvest.analytics import calculate_kpis
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = (ROOT / 'data/agriculture_demo.csv').read_bytes()
BUYERS = (ROOT / 'data/buyers_demo.csv').read_bytes()
APP = str(ROOT / 'app.py')

def test_metadata_and_invalid_activation():
    state = {}
    result, meta = prepare_dataset(PAYLOAD, 'farm.csv')
    assert activate_dataset(state, result, meta)
    assert meta['origin'] == 'uploaded' and meta['demand_source'] == 'uploaded_estimate'
    assert len(meta['sha256']) == 64
    original = state['active_data'].copy()
    bad, bad_meta = prepare_dataset(PAYLOAD.replace(b'Carrots,150,200,35,3', b'Carrots,150,200,,3'), 'bad.csv')
    assert not activate_dataset(state, bad, bad_meta)
    pd.testing.assert_frame_equal(state['active_data'], original)
    assert state['agriculture_metadata']['filename'] == 'farm.csv'
    assert bad.summary['missing_cells'] == 1
    assert bad.issues[0]['record'] == 3 and bad.issues[0]['column'] == 'market_price_per_kg'
    result, meta = prepare_dataset(BUYERS, 'buyers.csv', 'buyers', origin='sample')
    activate_dataset(state, result, meta)
    assert len(state['active_buyers']) == 3 and len(state['active_data']) == 3
    assert state['buyers_metadata']['origin'] == 'sample'

@pytest.mark.parametrize('payload', [b'', b'crop,crop\na,b\n', b'crop, CROP \na,b\n',
    b',qty\na,1\n', b'a,b\n1\n', b'a,b\n1,2,3\n', b'a,b\n\n',
    b'a,b\n"unfinished,1', b'\xff,qty\na,1', b'x' * (10 * 1024 * 1024 + 1)])
def test_strict_csv_structure(payload):
    with pytest.raises(ValueError):
        read_csv_bytes(payload)

def test_utf8_bom_and_quoted_crop():
    payload = PAYLOAD.replace(b'Tomatoes', '"தக்காளி, Tomato"'.encode('utf-8'))
    result, _ = prepare_dataset(b'\xef\xbb\xbf' + payload, 'tamil.csv')
    assert not result.errors and result.data.iloc[0].crop == 'தக்காளி, Tomato'

def test_ambiguous_mapping_requires_manual_selection():
    raw = read_csv_bytes(PAYLOAD)
    raw['crop'] = raw.crop_nm
    mapping = suggest_mapping(raw.columns)
    assert mapping['crop'] is None and validate_frame(raw, mapping).errors
    mapping['crop'] = 'crop_nm'
    assert not validate_frame(raw, mapping).errors

def test_buyer_mapping_and_missing_transport():
    raw = read_csv_bytes(BUYERS)
    mapping = suggest_mapping(raw.columns, 'buyers')
    assert mapping['required_kg'] == 'required_qty'
    raw.loc[1, 'transport_cost'] = ''
    result = validate_frame(raw, mapping, 'buyers')
    assert result.summary['invalid_rows'] == 1 and result.issues[0]['record'] == 2

def test_coverage_no_allocations(agriculture, buyers):
    buyers.loc[0, 'crop'] = 'Other'
    coverage = buyer_coverage(agriculture, buyers)
    assert list(coverage.crop_in_active_agriculture) == [False, True, True]
    assert not buyer_coverage(None, buyers).crop_in_active_agriculture.any()
    assert 'matched_kg' not in coverage

def test_workspace_atomicity_and_legacy(agriculture, tmp_path):
    path = tmp_path / 'workspace.sqlite3'
    assert load_workspace(path) is None
    save_snapshot(agriculture, 'Phase 1 snapshot', path)
    assert load_workspace(path)['source'] == 'Phase 1 snapshot'
    state = {}
    for kind, data in [('agriculture', PAYLOAD), ('buyers', BUYERS)]:
        result, meta = prepare_dataset(data, kind + '.csv', kind)
        activate_dataset(state, result, meta)
    save_workspace(state, path)
    loaded = load_workspace(path)
    pd.testing.assert_frame_equal(loaded['active_buyers'], state['active_buyers'], check_dtype=False)
    assert loaded['agriculture_metadata'] == state['agriculture_metadata']
    state['active_buyers'].loc[0, 'required_kg'] = -1
    with pytest.raises(ValueError):
        save_workspace(state, path)
    assert load_workspace(path)['active_buyers'].iloc[0].required_kg == 100

def test_dashboard_filters_view_only():
    app = AppTest.from_file(APP).run()
    app.button(key='load_demo').click().run()
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Dashboard').run()
    app.multiselect[0].set_value(['Tomatoes']).run()
    assert not app.exception
    assert [m.value for m in app.metric] == ['1', '500', '300', '200', '0']
    assert calculate_kpis(app.session_state['active_data'])['available_kg'] == 1050
    app.multiselect[0].set_value([]).run()
    assert not app.exception and len(app.metric) == 0

def test_actual_upload_and_invalid_replacement():
    app = AppTest.from_file(APP).run()
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Upload Data').run()
    app.file_uploader(key='upload_agriculture').upload('farm.csv', PAYLOAD, 'text/csv').run()
    app.button(key='validate_agriculture').click().run()
    assert not app.exception
    assert app.session_state['agriculture_metadata']['filename'] == 'farm.csv'
    bad = PAYLOAD.replace(b'Carrots,150,200,35,3', b'Carrots,150,200,,3')
    app.file_uploader(key='upload_agriculture').upload('missing.csv', bad, 'text/csv').run()
    app.button(key='validate_agriculture').click().run()
    assert not app.exception
    assert app.session_state['agriculture_metadata']['filename'] == 'farm.csv'
    assert app.session_state['report_agriculture']['result'].issues[0]['record'] == 3
    next(w for w in app.radio if w.key.split('__ui_')[0]=='dataset_kind').set_value('buyers').run()
    app.file_uploader(key='upload_buyers').upload('opportunities.csv', BUYERS, 'text/csv').run()
    app.button(key='validate_buyers').click().run()
    assert not app.exception and len(app.session_state['active_buyers']) == 3
    assert app.session_state['buyers_metadata']['origin'] == 'uploaded'
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Dashboard').run()
    assert [m.value for m in app.metric] == ['3', '1,050', '850', '250', '50']
    assert any('not confirmed orders' in w.value for w in app.warning)

def test_custom_mapping_in_app():
    app = AppTest.from_file(APP).run()
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Upload Data').run()
    app.file_uploader(key='upload_agriculture').upload('custom.csv', PAYLOAD.replace(b'crop_nm', b'produce'), 'text/csv').run()
    next(w for w in app.selectbox if w.label == 'crop').set_value('produce')
    app.button(key='validate_agriculture').click().run()
    assert not app.exception
    assert app.session_state['agriculture_metadata']['mapping']['crop'] == 'produce'

def test_save_restore_complete_workspace_in_app(tmp_path, monkeypatch):
    monkeypatch.setenv('HARVEST_DB_PATH', str(tmp_path / 'roundtrip.sqlite3'))
    first = AppTest.from_file(APP).run()
    first.button(key='load_demo').click().run()
    first.button(key='save_snapshot').click().run()
    assert not first.exception
    second = AppTest.from_file(APP).run()
    assert second.session_state['active_buyers'] is None
    second.button(key='restore_snapshot').click().run()
    assert not second.exception
    assert len(second.session_state['active_data']) == 3 and len(second.session_state['active_buyers']) == 3
    assert second.session_state['buyers_metadata']['origin'] == 'sample'
