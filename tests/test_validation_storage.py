import pandas as pd
import pytest
from harvest.data import suggest_mapping, validate_frame
from harvest.storage import save_snapshot, load_snapshot


def test_automatic_suggestions(raw):
    mapping = suggest_mapping(raw.columns)
    assert mapping['crop'] == 'crop_nm'
    assert mapping['estimated_demand_kg'] == 'est_demand'
    assert not validate_frame(raw, mapping).errors


@pytest.mark.parametrize('value', [None, '', 'bad', -1, float('inf'), float('nan')])
def test_bad_quantity_rejected(raw, value):
    raw['qty_avail'] = raw.qty_avail.astype(object)
    raw.loc[0, 'qty_avail'] = value
    result = validate_frame(raw, suggest_mapping(raw.columns))
    assert result.errors and result.data is None
    assert result.summary['invalid_rows'] == 1


def test_blank_crop_and_duplicate_identity(raw):
    raw.loc[0, 'crop_nm'] = ' '
    assert validate_frame(raw, suggest_mapping(raw.columns)).errors
    raw.loc[0, 'crop_nm'] = ' onions '
    assert validate_frame(raw, suggest_mapping(raw.columns)).summary['duplicate_rows'] == 2


def test_empty_missing_or_reused_mapping(raw):
    mapping = suggest_mapping(raw.columns)
    assert validate_frame(raw.iloc[:0], mapping).errors
    assert validate_frame(raw, {}).errors
    mapping['estimated_demand_kg'] = mapping['available_kg']
    assert validate_frame(raw, mapping).errors


def test_zero_is_valid_and_missing_price_not_imputed(raw):
    raw.loc[0, 'qty_avail'] = 0
    assert not validate_frame(raw, suggest_mapping(raw.columns)).errors
    raw.loc[2, 'mkt_prc'] = None
    result = validate_frame(raw, suggest_mapping(raw.columns))
    assert result.data is None
    assert result.summary['missing_cells'] == 1


def test_explicit_mapping_and_extra_column(raw):
    raw = raw.rename(columns={'crop_nm': 'produce'})
    raw['note'] = 'example'
    mapping = suggest_mapping(raw.columns)
    assert mapping['crop'] is None
    mapping['crop'] = 'produce'
    result = validate_frame(raw, mapping)
    assert result.warnings and not result.errors
    assert 'note' not in result.data


def test_sqlite_roundtrip_and_atomic_rejection(agriculture, tmp_path):
    path = tmp_path / 'snapshot.sqlite3'
    assert load_snapshot(path) is None
    save_snapshot(agriculture, 'Uploaded sample', path)
    restored, source = load_snapshot(path)
    pd.testing.assert_frame_equal(restored, agriculture, check_dtype=False)
    assert source == 'Uploaded sample'
    invalid = agriculture.copy()
    invalid.loc[0, 'available_kg'] = -1
    with pytest.raises(ValueError):
        save_snapshot(invalid, 'bad', path)
    assert load_snapshot(path)[1] == 'Uploaded sample'
