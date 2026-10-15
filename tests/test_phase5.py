from pathlib import Path
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from harvest.financials import analyse_financials, financial_totals, market_transport_scenario
from harvest.matching import matching_preview, estimated_return
from harvest.money import gross_return

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


def tomato_totals(agriculture, buyers):
    report = analyse_financials(agriculture, buyers)
    return financial_totals(report.crops.loc[report.crops.crop == 'Tomatoes'])


def test_mandatory_tomato_financials(agriculture, buyers):
    report = analyse_financials(agriculture, buyers)
    rows = report.buyers.set_index('buyer_name')
    assert rows.loc['Green Leaf Restaurant', 'buyer_gross_revenue'] == 2800
    assert rows.loc['Green Leaf Restaurant', 'buyer_transport_cost'] == 200
    assert rows.loc['Green Leaf Restaurant', 'estimated_return_after_transport'] == 2600
    assert rows.loc['City Hostel', 'estimated_return_after_transport'] == 1830
    totals = tomato_totals(agriculture, buyers)
    assert totals['matched_kg'] == 180
    assert totals['buyer_gross_revenue'] == 4880
    assert totals['buyer_transport_cost'] == 450
    assert totals['estimated_return_after_transport'] == 4430
    assert totals['market_gross_reference'] == 4500  # same 180 kg, not full 200 kg
    assert totals['difference_vs_market_gross_reference'] == -70
    assert totals['unmatched_kg'] == 20 and totals['unmatched_market_reference'] == 500
    assert 'profit' not in report.totals


def test_all_crop_totals_no_double_transport_or_unmatched_revenue(agriculture, buyers):
    totals = analyse_financials(agriculture, buyers).totals
    assert totals['matched_kg'] == 230
    assert totals['buyer_gross_revenue'] == 6480
    assert totals['buyer_transport_cost'] == 630
    assert totals['estimated_return_after_transport'] == 5850
    assert totals['market_gross_reference'] == 6000
    assert totals['difference_vs_market_gross_reference'] == -150


def test_partial_onion_quote_charged_once(agriculture, buyers):
    detail = analyse_financials(agriculture, buyers).buyers.set_index('buyer_name')
    row = detail.loc['Fresh Basket Market']
    assert row.matched_kg == 50 and row.buyer_transport_cost == 180
    assert row.buyer_gross_revenue == 1600 and row.estimated_return_after_transport == 1420
    assert row.market_gross_reference == 1500


def test_explicit_market_scenario(agriculture, buyers):
    totals = tomato_totals(agriculture, buyers)
    scenario = market_transport_scenario(totals, 100)
    assert scenario['market_return_after_assumed_transport'] == 4400
    assert scenario['difference_vs_market_after_assumed_transport'] == 30
    assert market_transport_scenario(totals, 0)['difference_vs_market_after_assumed_transport'] == -70
    assert totals['market_gross_reference'] == 4500  # unchanged source reference


@pytest.mark.parametrize('value', [-1, float('nan'), float('inf'), 'bad'])
def test_invalid_market_transport_rejected(agriculture, buyers, value):
    with pytest.raises(ValueError):
        market_transport_scenario(tomato_totals(agriculture, buyers), value)


def test_no_match_no_trip_and_reference_zero(agriculture, buyers):
    agriculture['estimated_demand_kg'] = agriculture.available_kg
    report = analyse_financials(agriculture, buyers)
    assert report.buyers.empty
    assert report.totals['estimated_return_after_transport'] == 0
    assert report.totals['buyer_transport_cost'] == 0
    assert market_transport_scenario(report.totals, 100)['applied_market_transport'] == 0


def test_unknown_buyer_crops_not_sold_or_costed(agriculture, buyers):
    buyers['crop'] = ['Peas', 'Beans', 'Corn']
    report = analyse_financials(agriculture, buyers)
    assert report.buyers.empty and report.totals['buyer_transport_cost'] == 0
    assert report.totals['market_gross_reference'] == 0
    assert report.totals['unmatched_market_reference'] == 6500


def test_negative_return_and_zero_market_reference(agriculture, buyers):
    agriculture.loc[0, 'estimated_demand_kg'] = 499
    agriculture.loc[0, 'market_price_per_kg'] = 0
    report = analyse_financials(agriculture, buyers)
    row = report.buyers.iloc[0]
    assert row.estimated_return_after_transport == -172
    assert row.market_gross_reference == 0
    assert row.difference_vs_market_gross_reference == -172


def test_currency_rounding_to_paise_and_shared_matching_result(agriculture, buyers):
    assert gross_return(1, 0.005) == 0.01
    assert estimated_return(1, 0.005, 0) == 0.01
    assert estimated_return(1, 1, 0.005) == 0.99
    buyers['offer_price_per_kg'] = 1.005
    buyers['transport_cost'] = 0.005
    detail = analyse_financials(agriculture, buyers).buyers
    _, _, audit = matching_preview(agriculture, buyers)
    assert list(detail.estimated_return_after_transport) == list(audit.estimated_return_after_transport)
    assert (detail.buyer_transport_cost == 0.01).all()
    assert list(detail.estimated_return_after_transport) == [100.49, 80.39, 50.24]


def test_input_immutability_and_case_insensitive_reference(agriculture, buyers):
    old_data, old_buyers = agriculture.copy(deep=True), buyers.copy(deep=True)
    first = analyse_financials(agriculture, buyers)
    second = analyse_financials(agriculture, buyers)
    pd.testing.assert_frame_equal(first.buyers, second.buyers)
    pd.testing.assert_frame_equal(agriculture, old_data)
    pd.testing.assert_frame_equal(buyers, old_buyers)
    buyers.loc[0, 'crop'] = ' tomatoes '
    assert analyse_financials(agriculture, buyers).buyers.iloc[0].market_price_per_kg == 25


def test_missing_dataset_screen_states(agriculture):
    app = AppTest.from_file(APP).run()
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Profit Analysis').run()
    assert not app.exception and len(app.metric) == 0 and app.info
    app.session_state['active_data'] = agriculture
    app.run()
    assert not app.exception and any('Load buyer opportunities' in element.value for element in app.info)


def test_finance_ui_tomatoes_reference_scenario_and_tamil():
    app = AppTest.from_file(APP).run()
    app.button(key='load_demo').click().run()
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Profit Analysis').run()
    next(w for w in app.selectbox if w.key.startswith('financial_crop_')).set_value('tomatoes').run()
    assert not app.exception
    assert [m.value for m in app.metric] == ['180','₹4,880.00','₹450.00','₹4,430.00','₹4,500.00','₹-70.00']
    assert any('not profit' in element.value for element in app.info)
    assert any('unknown by default' in element.value for element in app.warning)
    next(w for w in app.checkbox if w.key.startswith('market_scenario_')).check().run()
    next(w for w in app.number_input if w.key.startswith('market_cost_')).set_value(100.0).run()
    assert not app.exception
    assert [m.value for m in app.metric][-2:] == ['₹4,400.00', '₹30.00']
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Buyer Matching').run()
    assert [m.value for m in app.metric] == ['250','230','20']
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Profit Analysis').run()
    next(w for w in app.selectbox if w.key.startswith('language_')).set_value('தமிழ்').run()
    assert not app.exception and 'லாப' in app.header[0].value


def test_no_match_financial_ui(agriculture, buyers):
    agriculture['estimated_demand_kg'] = agriculture.available_kg
    app = AppTest.from_file(APP).run()
    app.session_state['active_data'] = agriculture
    app.session_state['active_buyers'] = buyers
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Profit Analysis').run()
    assert not app.exception
    assert [m.value for m in app.metric][:4] == ['0','₹0.00','₹0.00','₹0.00']
    assert any('No matched quantity' in element.value for element in app.info)


def test_changed_inputs_reset_scenario_and_recompute(agriculture, buyers):
    app = AppTest.from_file(APP).run()
    app.session_state['active_data'] = agriculture
    app.session_state['active_buyers'] = buyers
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Profit Analysis').run()
    next(w for w in app.checkbox if w.key.startswith('market_scenario_')).check().run()
    changed = buyers.copy()
    changed.loc[0, 'transport_cost'] = 300
    app.session_state['active_buyers'] = changed
    app.run()
    assert not app.exception
    assert not next(w for w in app.checkbox if w.key.startswith('market_scenario_')).value
    assert [m.value for m in app.metric][:4] == ['230','₹6,480.00','₹730.00','₹5,750.00']


def test_oversized_derived_currency_is_rejected_cleanly():
    with pytest.raises(ValueError, match='finite range'):
        gross_return(1e308, 1e308)


def test_oversized_buyer_return_is_a_clear_ui_error(agriculture, buyers):
    buyers['offer_price_per_kg'] = 1e308
    app = AppTest.from_file(APP).run()
    app.session_state['active_data'] = agriculture
    app.session_state['active_buyers'] = buyers
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Profit Analysis').run()
    assert not app.exception
    assert any('finite range' in element.value for element in app.error)
