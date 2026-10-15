import pandas as pd
import pytest
from harvest.analytics import calculate_kpis, crop_balances
from harvest.matching import match_surplus, estimated_return


def test_mandatory_sample_totals(agriculture):
    assert calculate_kpis(agriculture) == {
        'records': 3, 'available_kg': 1050, 'estimated_demand_kg': 850,
        'positive_surplus_kg': 250, 'shortage_kg': 50}


def test_mandatory_crop_balances(agriculture):
    rows = crop_balances(agriculture).set_index('crop')
    assert rows.loc['Tomatoes', 'potential_surplus_kg'] == 200
    assert rows.loc['Onions', 'potential_surplus_kg'] == 50
    assert rows.loc['Carrots', 'shortage_kg'] == 50


def test_mandatory_buyer_returns(agriculture, buyers):
    allocations, balances = match_surplus(agriculture, buyers)
    tomatoes = balances.set_index('crop').loc['Tomatoes']
    assert tomatoes.matched_kg == 180
    assert tomatoes.unmatched_kg == 20
    rows = allocations.set_index('buyer_name')
    assert rows.loc['Green Leaf Restaurant', 'estimated_return_after_transport'] == 2600
    assert rows.loc['City Hostel', 'estimated_return_after_transport'] == 1830
    assert allocations.loc[allocations.crop == 'Tomatoes', 'estimated_return_after_transport'].sum() == 4430
    # Onion request is larger than surplus: charge full transport once on 50 kg.
    assert rows.loc['Fresh Basket Market', 'matched_kg'] == 50
    assert rows.loc['Fresh Basket Market', 'estimated_return_after_transport'] == 1420


def test_repeat_run_does_not_accumulate_or_mutate(agriculture, buyers):
    original = agriculture.copy(deep=True)
    first, _ = match_surplus(agriculture, buyers)
    second, _ = match_surplus(agriculture, buyers)
    pd.testing.assert_frame_equal(first, second)
    pd.testing.assert_frame_equal(original, agriculture)


def test_surplus_cap_across_buyers(agriculture, buyers):
    buyers.loc[0, 'required_kg'] = 190
    allocations, balances = match_surplus(agriculture, buyers)
    assert allocations.loc[allocations.crop == 'Tomatoes', 'matched_kg'].sum() == 200
    assert (balances.unmatched_kg >= 0).all()
    assert allocations.set_index('buyer_name').loc['City Hostel', 'matched_kg'] == 10


def test_no_surplus_or_unknown_crop(agriculture, buyers):
    agriculture['estimated_demand_kg'] = agriculture.available_kg + 1
    allocations, _ = match_surplus(agriculture, buyers)
    assert allocations.empty
    buyers['crop'] = ['Unknown A', 'Unknown B', 'Unknown C']
    assert match_surplus(agriculture, buyers)[0].empty


def test_duplicate_buyer_rejected(agriculture, buyers):
    with pytest.raises(ValueError, match='Duplicate'):
        match_surplus(agriculture, pd.concat([buyers, buyers.iloc[[0]]]))


@pytest.mark.parametrize('quantity,price,transport,expected', [(100,28,200,2600), (80,26,250,1830),
    (0,28,200,0), (1,2,20,-18), (0.5,25,1,11.5)])
def test_transport_rules(quantity, price, transport, expected):
    assert estimated_return(quantity, price, transport) == expected


@pytest.mark.parametrize('value', [-1, float('inf'), float('nan')])
def test_invalid_financial_values(value):
    with pytest.raises(ValueError):
        estimated_return(value, 28, 200)


def test_demand_is_not_a_forecast(agriculture):
    assert 'estimated_demand_kg' in crop_balances(agriculture)
    assert not any('forecast' in c for c in crop_balances(agriculture).columns)
