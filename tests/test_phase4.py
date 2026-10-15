from pathlib import Path
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from harvest.matching import matching_preview
from harvest.storage import save_workspace, load_workspace

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


def test_demo_full_audit_and_capped_partial(agriculture, buyers):
    allocations, balances, audit = matching_preview(agriculture, buyers)
    assert list(audit.source_record) == [1, 2, 3]
    assert list(audit.status) == ['Potential full match', 'Potential full match', 'Potential partial match']
    assert list(audit.matched_kg) == [100, 80, 50]
    assert list(audit.unfilled_request_kg) == [0, 0, 50]
    assert list(audit.surplus_before_kg) == [200, 100, 50]
    assert list(audit.surplus_after_kg) == [100, 20, 0]
    assert audit.iloc[0].estimated_return_after_transport == 2600
    assert audit.iloc[1].estimated_return_after_transport == 1830
    assert balances.matched_kg.sum() == 230
    assert balances.unmatched_kg.sum() == 20
    assert audit.estimated_return_after_transport.sum() == 5850
    assert len(allocations) == 3


def test_exhausted_surplus_keeps_skipped_buyer_in_audit(agriculture, buyers):
    buyers.loc[0, 'required_kg'] = 200
    allocations, balances, audit = matching_preview(agriculture, buyers)
    row = audit.iloc[1]
    assert row.status == 'Surplus exhausted'
    assert row.matched_kg == 0 and row.unfilled_request_kg == 80
    assert row.charged_transport_cost == 0 and row.estimated_return_after_transport == 0
    assert len(allocations) == 2


def test_case_insensitive_matching_and_canonical_balances(agriculture, buyers):
    buyers.loc[0, 'crop'] = ' tomatoes '
    _, balances, audit = matching_preview(agriculture, buyers)
    assert audit.iloc[0].matched_kg == 100
    assert balances.loc[balances.crop == 'Tomatoes', 'unmatched_kg'].item() == 20


@pytest.mark.parametrize('case,status', [('unknown','Crop unavailable'), ('zero','Zero request'), ('shortage','No surplus')])
def test_skipped_request_reasons(agriculture, buyers, case, status):
    if case == 'unknown':
        buyers.loc[0, 'crop'] = 'Peas'
    elif case == 'zero':
        buyers.loc[0, 'required_kg'] = 0
    else:
        buyers.loc[0, 'crop'] = 'Carrots'
    _, _, audit = matching_preview(agriculture, buyers)
    assert audit.iloc[0].status == status
    assert audit.iloc[0].reason
    assert audit.iloc[0].charged_transport_cost == 0
    assert audit.iloc[0].unfilled_request_kg == buyers.iloc[0].required_kg


def test_partial_transport_and_negative_return_visible(agriculture, buyers):
    agriculture.loc[0, 'estimated_demand_kg'] = 499
    _, _, audit = matching_preview(agriculture, buyers)
    assert audit.iloc[0].matched_kg == 1
    assert audit.iloc[0].charged_transport_cost == 200
    assert audit.iloc[0].estimated_return_after_transport == -172
    assert audit.iloc[0].status == 'Potential partial match'


def test_csv_order_not_offer_price_determines_first_allocation(agriculture, buyers):
    agriculture.loc[0, 'estimated_demand_kg'] = 400
    buyers.loc[1, 'offer_price_per_kg'] = 999
    _, _, first = matching_preview(agriculture, buyers)
    assert list(first.matched_kg[:2]) == [100, 0]
    reversed_buyers = buyers.iloc[[1, 0, 2]].reset_index(drop=True)
    _, _, second = matching_preview(agriculture, reversed_buyers)
    assert list(second.matched_kg[:2]) == [80, 20]


def test_duplicate_identity_case_space_rejected(agriculture, buyers):
    duplicate = buyers.iloc[[0]].copy()
    duplicate['buyer_name'] = ' green leaf restaurant '
    duplicate['crop'] = ' tomatoes '
    with pytest.raises(ValueError, match='Duplicate'):
        matching_preview(agriculture, pd.concat([buyers, duplicate]))


def test_same_buyer_different_crops_distinct_quoted_trips(agriculture, buyers):
    buyers.loc[2, 'buyer_name'] = buyers.loc[0, 'buyer_name']
    _, _, audit = matching_preview(agriculture, buyers)
    assert len(audit) == 3 and audit.charged_transport_cost.sum() == 630


def test_fractional_allocations_and_conservation(agriculture, buyers):
    agriculture['available_kg'] = agriculture.available_kg.astype(float)
    buyers['required_kg'] = buyers.required_kg.astype(float)
    agriculture.loc[0, 'available_kg'] = 300.3
    buyers.loc[0, 'required_kg'] = 0.1
    _, balances, audit = matching_preview(agriculture, buyers)
    assert audit.iloc[0].matched_kg == pytest.approx(0.1)
    assert audit.iloc[1].matched_kg == pytest.approx(0.2)
    assert (audit.matched_kg <= audit.required_kg).all()
    assert (audit.surplus_after_kg >= 0).all()
    assert balances.matched_kg.sum() + balances.unmatched_kg.sum() == pytest.approx(balances.potential_surplus_kg.sum())


def test_repeated_preview_inputs_unchanged_and_snapshot_recreates_plan(agriculture, buyers, tmp_path):
    before = buyers.copy(deep=True)
    first = matching_preview(agriculture, buyers)
    second = matching_preview(agriculture, buyers)
    for a, b in zip(first, second):
        pd.testing.assert_frame_equal(a, b)
    pd.testing.assert_frame_equal(before, buyers)
    path = tmp_path / 'preview.sqlite3'
    save_workspace({'active_data': agriculture, 'active_buyers': buyers}, path)
    saved = load_workspace(path)
    third = matching_preview(saved['active_data'], saved['active_buyers'])
    pd.testing.assert_frame_equal(first[2], third[2], check_dtype=False)


def test_no_surplus_all_audited(agriculture, buyers):
    agriculture['estimated_demand_kg'] = agriculture.available_kg
    allocations, balances, audit = matching_preview(agriculture, buyers)
    assert allocations.empty and len(audit) == 3
    assert (audit.status == 'No surplus').all()
    assert audit.charged_transport_cost.sum() == 0
    assert balances.unmatched_kg.sum() == 0


def test_missing_dataset_screen_messages(agriculture):
    app = AppTest.from_file(APP).run()
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Buyer Matching').run()
    assert not app.exception and app.info and len(app.metric) == 0
    app.session_state['active_data'] = agriculture
    app.run()
    assert not app.exception and any('Load buyer opportunities' in info.value for info in app.info)


def test_demo_crop_filter_financial_rows_tamil_and_navigation():
    app = AppTest.from_file(APP).run()
    app.button(key='load_demo').click().run()
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Buyer Matching').run()
    assert not app.exception
    assert [m.value for m in app.metric] == ['250', '230', '20']
    next(w for w in app.selectbox if w.key.startswith('matching_crop_')).set_value('tomatoes').run()
    assert not app.exception
    assert [m.value for m in app.metric] == ['200', '180', '20']
    allocation_table = app.dataframe[1].value
    assert list(allocation_table.matched_kg) == [100, 80]
    assert list(allocation_table.estimated_return_after_transport) == [2600, 1830]
    assert any('Sample opportunities' in msg.value for msg in app.warning)
    before = app.session_state['active_buyers'].copy(deep=True)
    app.run()
    assert [m.value for m in app.metric] == ['200', '180', '20']
    pd.testing.assert_frame_equal(before, app.session_state['active_buyers'])
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Dashboard').run()
    assert [m.value for m in app.metric] == ['3', '1,050', '850', '250', '50']
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Buyer Matching').run()
    next(w for w in app.selectbox if w.key.startswith('language_')).set_value('தமிழ்').run()
    assert not app.exception and 'வாங்குபவர்' in app.header[0].value


def test_unknown_crop_view_and_uploaded_labels(agriculture, buyers):
    buyers.loc[0, 'crop'] = 'Peas'
    app = AppTest.from_file(APP).run()
    app.session_state['active_data'] = agriculture
    app.session_state['active_buyers'] = buyers
    app.session_state['buyers_metadata'] = {'origin': 'uploaded', 'filename': 'mybuyers.csv'}
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Buyer Matching').run()
    next(w for w in app.selectbox if w.key.startswith('matching_crop_')).set_value('peas').run()
    assert not app.exception
    assert [m.value for m in app.metric] == ['0', '0', '0']
    assert any('Uploaded opportunities' in msg.value for msg in app.warning)
    assert any('no agriculture record' in msg.value for msg in app.info)


def test_negative_return_screen_warning(agriculture, buyers):
    agriculture.loc[0, 'estimated_demand_kg'] = 499
    app = AppTest.from_file(APP).run()
    app.session_state['active_data'] = agriculture
    app.session_state['active_buyers'] = buyers
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Buyer Matching').run()
    assert not app.exception
    assert any('negative returns' in msg.value for msg in app.warning)


def test_active_data_change_recomputes_and_resets_crop_filter(agriculture, buyers):
    app = AppTest.from_file(APP).run()
    app.session_state['active_data'] = agriculture
    app.session_state['active_buyers'] = buyers
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Buyer Matching').run()
    next(w for w in app.selectbox if w.key.startswith('matching_crop_')).set_value('tomatoes').run()
    changed = agriculture.copy()
    changed.loc[0, 'estimated_demand_kg'] = 490
    app.session_state['active_data'] = changed
    app.run()
    assert not app.exception
    assert [m.value for m in app.metric] == ['60', '60', '0']
    assert next(w for w in app.selectbox if w.key.startswith('matching_crop_')).value is None
