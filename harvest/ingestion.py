"""Strict, bounded CSV parsing and validated dataset provenance."""
import csv
import hashlib
import io
from datetime import datetime, timezone
import pandas as pd
from .data import validate_frame, suggest_mapping

MAX_BYTES = 10 * 1024 * 1024
MAX_RECORDS = 50_000


def read_csv_bytes(payload):
    if not payload or len(payload) > MAX_BYTES:
        raise ValueError("CSV must contain data and be at most 10 MB / அதிகபட்சம் 10 MB")
    try:
        text = payload.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        headers = next(reader)
        normalized = [h.strip().casefold() for h in headers]
        if not headers or any(not h for h in normalized) or len(set(normalized)) != len(headers):
            raise ValueError("CSV headers must be nonblank and unique, ignoring case/whitespace.")
        records = []
        for row in reader:
            if len(row) != len(headers):
                raise ValueError(f"Record {len(records)+1}: expected {len(headers)} cells, got {len(row)}. Blank/ragged rows are not dropped.")
            records.append(row)
            if len(records) > MAX_RECORDS:
                raise ValueError("CSV exceeds 50,000 records.")
        return pd.DataFrame(records, columns=headers)
    except (UnicodeError, csv.Error, StopIteration) as exc:
        raise ValueError(f"Use a valid comma-delimited UTF-8 CSV: {exc}") from exc


def prepare_dataset(payload, name, kind="agriculture", mapping=None, origin="uploaded", sheet=None):
    if origin not in ("sample", "uploaded"):
        raise ValueError("Unknown data origin")
    from .tabular import read_table,interpret_columns
    raw = read_table(payload,name,sheet)
    mapping = interpret_columns(raw,kind)[0] if mapping is None else mapping
    result = validate_frame(raw, mapping, kind)
    metadata = {"filename": str(name), "kind": kind, "origin": origin,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "validated_at_utc": datetime.now(timezone.utc).isoformat(),
                "rows": len(raw), "mapping": dict(mapping), "quality": result.summary,
                "demand_source": "uploaded_estimate" if kind == "agriculture" else None}
    return result, metadata


def activate_dataset(state, result, metadata):
    """Invalid input cannot replace either active dataset or its provenance."""
    if result.errors or result.data is None:
        return False
    kind = metadata["kind"]
    key = "active_data" if kind == "agriculture" else "active_buyers"
    state[key] = result.data.copy(deep=True)
    state[f"{kind}_metadata"] = dict(metadata)
    if kind == "agriculture":
        state["source"] = f"{metadata['origin'].title()}: {metadata['filename']}"
    return True


def buyer_coverage(agriculture, buyers):
    """Data compatibility only; no matching, reservations or confirmed orders."""
    crops = set(agriculture.crop.str.casefold()) if agriculture is not None else set()
    result = buyers.copy()
    result["crop_in_active_agriculture"] = result.crop.str.casefold().isin(crops)
    return result
