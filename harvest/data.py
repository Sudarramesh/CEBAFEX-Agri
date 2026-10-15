"""Explicit CSV mapping and strict validation. No silent imputation or row drops."""
from dataclasses import dataclass, field
import pandas as pd
import numpy as np

ALIASES = {
    "crop": ("crop", "crop_nm", "crop_name"),
    "available_kg": ("available_kg", "qty_avail", "available_quantity"),
    "estimated_demand_kg": ("estimated_demand_kg", "est_demand", "estimated_demand"),
    "market_price_per_kg": ("market_price_per_kg", "mkt_prc", "market_price"),
    "harvest_age_days": ("harvest_age_days", "harvest_age"),
}
BUYER_MAPPING = {"buyer_name": "buyer_name", "buyer_type": "buyer_type",
                 "crop": "crop_nm", "required_kg": "required_qty",
                 "offer_price_per_kg": "offer_price", "transport_cost": "transport_cost"}

@dataclass
class ValidationResult:
    data: pd.DataFrame | None
    errors: list[str]
    warnings: list[str]
    summary: dict
    issues: list[dict] = field(default_factory=list)


BUYER_ALIASES = {
    "buyer_name": ("buyer_name", "buyer", "name"),
    "buyer_type": ("buyer_type", "type"),
    "crop": ("crop", "crop_nm", "crop_name"),
    "required_kg": ("required_kg", "required_qty", "required_quantity"),
    "offer_price_per_kg": ("offer_price_per_kg", "offer_price"),
    "transport_cost": ("transport_cost", "transportation_cost"),
}


def suggest_mapping(columns, kind="agriculture"):
    if kind not in ("agriculture", "buyers"):
        raise ValueError("Unknown dataset kind")
    aliases = ALIASES if kind == "agriculture" else BUYER_ALIASES
    # More than one candidate is ambiguous: require an explicit choice.
    result = {}
    for target, names in aliases.items():
        candidates = [c for c in columns if str(c).strip().casefold() in names]
        result[target] = candidates[0] if len(candidates) == 1 else None
    return result


def validate_frame(raw, mapping, kind="agriculture"):
    if kind not in ("agriculture", "buyers"):
        raise ValueError("Unknown dataset kind")
    fields = list(ALIASES) if kind == "agriculture" else list(BUYER_MAPPING)
    summary = {"input_rows": len(raw), "valid_rows": 0, "invalid_rows": 0,
               "duplicate_rows": 0, "not_assessed_rows": 0, "missing_cells": int(raw.apply(lambda col: col.isna() | col.astype("string").str.strip().eq("").fillna(False)).sum().sum())}
    raw = raw.reset_index(drop=True)
    errors, warnings, issues = [], [], []
    if raw.empty:
        errors.append("Dataset has no records.")
    if raw.columns.duplicated().any():
        errors.append("Duplicate source column names are not allowed.")
    sources = [mapping.get(f) for f in fields]
    if any(s is None or s not in raw.columns for s in sources):
        errors.append("Map every required field to an existing source column.")
    if len(set(sources)) != len(sources):
        errors.append("Each source column can map to only one field.")
    if errors:
        summary["not_assessed_rows"] = len(raw)
        return ValidationResult(None, errors, warnings, summary)
    def add_issues(mask, column, message):
        for index in raw.index[mask]:
            issues.append({"record": int(index) + 1, "column": column,
                           "value": str(raw.loc[index, mapping.get(column, sources[0])]),
                           "issue": message})

    data = raw[sources].copy()
    data.columns = fields
    text_fields = ["crop"] if kind == "agriculture" else ["crop", "buyer_name", "buyer_type"]
    bad = pd.Series(False, index=data.index)
    for f in text_fields:
        data[f] = data[f].astype("string").str.strip()
        missing = data[f].isna() | data[f].eq("")
        if missing.any():
            errors.append(f"{f}: {int(missing.sum())} blank value(s).")
        add_issues(missing, f, "Blank required text / தேவையான உரை இல்லை")
        bad |= missing
    for f in [f for f in fields if f not in text_fields]:
        data[f] = pd.to_numeric(data[f], errors="coerce")
        invalid = data[f].isna() | ~np.isfinite(data[f]) | data[f].lt(0)
        if invalid.any():
            errors.append(f"{f}: {int(invalid.sum())} value(s) must be finite, numeric and non-negative.")
        add_issues(invalid, f, "Finite non-negative number required / பூஜ்ஜியம் அல்லது நேர்மறை எண் தேவை")
        bad |= invalid
    # One record per crop for Phase 1; batch-level aggregation is a future feature.
    identities = ["crop"] if kind == "agriculture" else ["buyer_name", "crop"]
    keys = data[identities].apply(lambda s: s.str.casefold())
    duplicate = keys.duplicated(keep=False)
    summary["duplicate_rows"] = int(duplicate.sum())
    if duplicate.any():
        errors.append("Duplicate crop or buyer/crop identities: merge or remove duplicates explicitly.")
        add_issues(duplicate, "crop", "Duplicate identity / நகல் அடையாளம்")
        bad |= duplicate
    summary["invalid_rows"] = int(bad.sum())
    summary["valid_rows"] = int((~bad).sum())
    if len(raw.columns) > len(fields):
        warnings.append("Unmapped extra columns are excluded from calculations.")
    return ValidationResult(None if errors else data.reset_index(drop=True), errors, warnings, summary, issues)


def require_valid(frame, kind="agriculture"):
    fields = list(ALIASES) if kind == "agriculture" else list(BUYER_MAPPING)
    result = validate_frame(frame, {f: f for f in fields}, kind)
    if result.errors:
        raise ValueError(" ".join(result.errors))
    return result.data


# Localized report headers are also accepted as explicit input aliases.
from .i18n import LABELS as _TRANSLATIONS
for _field,_names in list(ALIASES.items()):
    if _field in _TRANSLATIONS: ALIASES[_field] = (*_names,_TRANSLATIONS[_field])
for _field,_names in list(BUYER_ALIASES.items()):
    if _field in _TRANSLATIONS: BUYER_ALIASES[_field] = (*_names,_TRANSLATIONS[_field])
