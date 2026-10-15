from pathlib import Path
import pandas as pd
import pytest
from harvest.data import BUYER_MAPPING, suggest_mapping, validate_frame

ROOT = Path(__file__).resolve().parents[1]
@pytest.fixture
def raw():
    return pd.read_csv(ROOT / 'data/agriculture_demo.csv')

@pytest.fixture
def agriculture(raw):
    return validate_frame(raw, suggest_mapping(raw.columns)).data

@pytest.fixture
def buyers():
    raw = pd.read_csv(ROOT / 'data/buyers_demo.csv')
    return validate_frame(raw, BUYER_MAPPING, 'buyers').data


@pytest.fixture(autouse=True)
def isolated_workspace_db(tmp_path,monkeypatch):
    monkeypatch.setenv('HARVEST_DB_PATH',str(tmp_path/'test-workspace.sqlite3'))
