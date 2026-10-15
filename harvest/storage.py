"""SQLite foundation. One atomic active snapshot, no uploaded file SQL interpolation."""
import json
import sqlite3
from pathlib import Path
import pandas as pd
from .data import require_valid
from .risk import RiskPolicy


def connect(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE IF NOT EXISTS active_dataset "
                "(id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL, source TEXT NOT NULL)")
    return con


def save_snapshot(data, source, path):
    data = require_valid(data)
    con = connect(path)
    try:
        with con:
            con.execute("INSERT OR REPLACE INTO active_dataset VALUES (1, ?, ?)",
                        (data.to_json(orient="records"), source))
    finally:
        con.close()


def load_snapshot(path):
    con = connect(path)
    try:
        row = con.execute("SELECT payload, source FROM active_dataset WHERE id=1").fetchone()
        return (require_valid(pd.DataFrame(json.loads(row[0]))), row[1]) if row else None
    finally:
        con.close()



def save_workspace(state, path):
    """Atomically persist both validated datasets and provenance; preserve legacy snapshot API."""
    bundle = {"risk_policy": RiskPolicy.from_dict(state.get("risk_policy")).to_dict()}
    for kind, key in (("agriculture", "active_data"), ("buyers", "active_buyers")):
        frame = state.get(key)
        bundle[key] = json.loads(require_valid(frame, kind).to_json(orient="records")) if frame is not None else None
        bundle[f"{kind}_metadata"] = state.get(f"{kind}_metadata")
    bundle["source"] = state.get("source", "Saved agriculture dataset")
    con = connect(path)
    try:
        with con:
            con.execute("CREATE TABLE IF NOT EXISTS workspace_snapshot (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)")
            con.execute("INSERT OR REPLACE INTO workspace_snapshot VALUES (1, ?)", (json.dumps(bundle, allow_nan=False),))
            if bundle["active_data"] is not None:
                con.execute("INSERT OR REPLACE INTO active_dataset VALUES (1, ?, ?)",
                            (json.dumps(bundle["active_data"]), bundle["source"]))
    finally:
        con.close()


def load_workspace(path):
    con = connect(path)
    try:
        exists = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workspace_snapshot'").fetchone()
        row = con.execute("SELECT payload FROM workspace_snapshot WHERE id=1").fetchone() if exists else None
    finally:
        con.close()
    if row:
        state = json.loads(row[0])
        state["risk_policy"] = RiskPolicy.from_dict(state.get("risk_policy")).to_dict()
        for kind, key in (("agriculture", "active_data"), ("buyers", "active_buyers")):
            if state.get(key) is not None:
                state[key] = require_valid(pd.DataFrame(state[key]), kind)
        return state
    legacy = load_snapshot(path)
    if legacy:
        return {"active_data": legacy[0], "source": legacy[1], "active_buyers": None,
                "agriculture_metadata": None, "buyers_metadata": None, "risk_policy": RiskPolicy().to_dict()}
    return None
