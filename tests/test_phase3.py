from dataclasses import replace
import json
from pathlib import Path
import sqlite3
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from harvest.risk import RiskPolicy, analyse_risk, prioritise_crop
from harvest.storage import save_workspace, load_workspace

ROOT = Path(__file__).resolve().parents[1]
APP = str(ROOT / 'app.py')


def test_demo_rules_and_priority(agriculture):
    report = analyse_risk(agriculture).set_index('crop')
    assert report.loc['Tomatoes', 'potential_surplus_kg'] == 200
    assert report.loc['Tomatoes', 'surplus_ratio'] == pytest.approx(0.4)
    assert report.loc['Tomatoes', 'high_surplus_flag']
    assert not report.loc['Tomatoes', 'age_review_flag']
    assert report.loc['Tomatoes', 'review_score'] == 1
    assert report.loc['Onions', 'review_score'] == 1
    assert report.loc['Onions', 'age_review_flag']
    assert report.loc['Carrots', 'shortage_kg'] == 50
    assert report.loc['Carrots', 'review_level'] == 'No surplus'
    assert pd.isna(report.loc['Carrots', 'priority_rank'])
    assert report.loc['Carrots', 'age_review_flag']
    assert report.potential_surplus_kg.sum() == 250 and report.shortage_kg.sum() == 50
    top = prioritise_crop(agriculture)
    assert top['crop'] == 'Tomatoes' and top['potential_surplus_kg'] == 200
    assert '200 kg' in top['reason'] and '300 kg' in top['reason']


def test_threshold_changes_review_not_balances_or_rank(agriculture):
    original = agriculture.copy(deep=True)
    report = analyse_risk(agriculture, RiskPolicy(0.1, 2)).set_index('crop')
    assert report.loc['Tomatoes', 'review_level'] == 'High'
    assert report.loc['Onions', 'review_level'] == 'High'
    assert report.loc['Carrots', 'review_score'] == 0
    assert prioritise_crop(agriculture, RiskPolicy(1, 100))['crop'] == 'Tomatoes'
    pd.testing.assert_frame_equal(agriculture, original)


def test_zero_stock_and_balanced_rows(agriculture):
    agriculture.loc[0, ['available_kg', 'estimated_demand_kg', 'harvest_age_days']] = [0, 100, 100]
    agriculture.loc[1, 'estimated_demand_kg'] = agriculture.loc[1, 'available_kg']
    report = analyse_risk(agriculture)
    assert report.iloc[0].surplus_ratio == 0
    assert not report.iloc[0].age_review_flag
    assert report.iloc[0].shortage_kg == 100
    assert report.iloc[1].balance_status == 'Balanced'
    assert prioritise_crop(agriculture) is None


def test_no_demand_surplus_ratio_and_inclusive_thresholds(agriculture):
    agriculture.loc[0, 'estimated_demand_kg'] = 375  # 125 / 500 = exact 25% boundary
    agriculture.loc[0, 'harvest_age_days'] = 3
    agriculture.loc[1, 'estimated_demand_kg'] = 0
    report = analyse_risk(agriculture)
    assert report.iloc[0].review_score == 2
    assert report.iloc[1].surplus_ratio == 1
    assert prioritise_crop(agriculture)['crop'] == 'Onions'


def test_surplus_without_flags_is_low(agriculture):
    agriculture.loc[0, 'estimated_demand_kg'] = 499
    report = analyse_risk(agriculture, RiskPolicy(0.25, 100))
    assert report.iloc[0].review_level == 'Low'


def test_priority_ties_are_deterministic(agriculture):
    agriculture['available_kg'] = 200
    agriculture['estimated_demand_kg'] = 100
    agriculture['harvest_age_days'] = [1, 2, 2]
    first = prioritise_crop(agriculture)
    assert first['crop'] == 'Carrots'  # ties by age, then casefold name
    shuffled = agriculture.sample(frac=1, random_state=2)
    assert prioritise_crop(shuffled)['crop'] == first['crop']


@pytest.mark.parametrize('ratio,days', [(0,3),(-1,3),(1.1,3),(float('nan'),3),
    (float('inf'),3),(0.25,0),(0.25,-1),(0.25,float('nan')),(True,3),('0.25',3)])
def test_invalid_policy_rejected(ratio, days):
    with pytest.raises(ValueError):
        RiskPolicy(ratio, days)


def test_invalid_or_duplicate_data_rejected(agriculture):
    with pytest.raises(ValueError):
        analyse_risk(pd.concat([agriculture, agriculture.iloc[[0]]]))
    agriculture.loc[0, 'harvest_age_days'] = -1
    with pytest.raises(ValueError):
        analyse_risk(agriculture)


def test_policy_persist_and_invalid_write_preserves_previous(agriculture, tmp_path):
    path = tmp_path / 'snapshot.sqlite3'
    state = {'active_data': agriculture, 'risk_policy': RiskPolicy(0.5, 7).to_dict()}
    save_workspace(state, path)
    assert load_workspace(path)['risk_policy'] == RiskPolicy(0.5, 7).to_dict()
    state['risk_policy'] = {'high_surplus_ratio': 0}
    with pytest.raises(ValueError):
        save_workspace(state, path)
    assert load_workspace(path)['risk_policy']['age_review_days'] == 7


def test_phase2_snapshot_gets_explicit_defaults(agriculture, tmp_path):
    path = tmp_path / 'legacy.sqlite3'
    save_workspace({'active_data': agriculture}, path)
    with sqlite3.connect(path) as con:
        payload = json.loads(con.execute('SELECT payload FROM workspace_snapshot').fetchone()[0])
        payload.pop('risk_policy')
        con.execute('UPDATE workspace_snapshot SET payload=?', (json.dumps(payload),))
    assert load_workspace(path)['risk_policy'] == RiskPolicy().to_dict()


def test_empty_risk_screen_and_no_surplus_message(agriculture):
    app = AppTest.from_file(APP).run()
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Surplus and Risk').run()
    assert not app.exception and len(app.metric) == 0
    agriculture['estimated_demand_kg'] = agriculture.available_kg
    app.session_state['active_data'] = agriculture
    app.run()
    assert not app.exception
    assert any('No positive surplus' in element.value for element in app.info)


def test_rule_form_navigation_filter_tamil_and_restore(tmp_path, monkeypatch):
    monkeypatch.setenv('HARVEST_DB_PATH', str(tmp_path / 'risk.sqlite3'))
    app = AppTest.from_file(APP).run()
    app.button(key='load_demo').click().run()
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Surplus and Risk').run()
    assert not app.exception
    assert [m.value for m in app.metric] == ['250', '50', '0']
    assert any('Tomatoes' in message.value and '200' in message.value for message in app.success)
    app.number_input(key='risk_threshold_pct').set_value(10.0)
    app.number_input(key='risk_age_days').set_value(2.0)
    app.button(key='apply_risk_policy').click().run()
    assert not app.exception
    assert [m.value for m in app.metric] == ['250', '50', '2']
    app.button(key='save_snapshot').click().run()
    next(w for w in app.multiselect if w.key.split('__ui_')[0]=='risk_level_filter').set_value([]).run()
    assert any('No records match' in message.value for message in app.info)
    assert len(app.session_state['active_data']) == 3
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Dashboard').run()
    assert [m.value for m in app.metric] == ['3', '1,050', '850', '250', '50']
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Surplus and Risk').run()
    assert app.number_input(key='risk_age_days').value == 2
    next(w for w in app.selectbox if w.key.startswith('language_')).set_value('தமிழ்').run()
    assert not app.exception and 'உபரி' in app.header[0].value
    second = AppTest.from_file(APP).run()
    second.button(key='restore_snapshot').click().run()
    next(w for w in second.radio if w.key.split('__ui_')[0]=='navigation').set_value('Surplus and Risk').run()
    assert not second.exception
    assert second.number_input(key='risk_threshold_pct').value == 10
    assert second.number_input(key='risk_age_days').value == 2


def test_invalid_rule_form_preserves_applied_policy():
    app = AppTest.from_file(APP).run()
    app.button(key='load_demo').click().run()
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Surplus and Risk').run()
    app.number_input(key='risk_threshold_pct').set_value(0.0)
    app.button(key='apply_risk_policy').click().run()
    assert not app.exception and app.error
    assert app.session_state['risk_policy'] == RiskPolicy().to_dict()
    assert [m.value for m in app.metric] == ['250', '50', '0']


def test_new_dataset_recomputes_priority(agriculture):
    app = AppTest.from_file(APP).run()
    app.session_state['active_data'] = agriculture
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Surplus and Risk').run()
    assert any('Tomatoes' in message.value for message in app.success)
    updated = agriculture.copy()
    updated.loc[1, 'available_kg'] = 1000
    app.session_state['active_data'] = updated
    app.run()
    assert not app.exception
    assert any('Onions' in message.value and '650' in message.value for message in app.success)
