"""All quantities are kg; uploaded estimated demand is never called a forecast."""
from .data import require_valid


def crop_balances(data):
    result = require_valid(data).copy()
    gap = result["available_kg"] - result["estimated_demand_kg"]
    result["potential_surplus_kg"] = gap.clip(lower=0)
    result["shortage_kg"] = (-gap).clip(lower=0)
    return result


def calculate_kpis(data):
    balances = crop_balances(data)
    return {"records": len(balances),
            "available_kg": float(balances.available_kg.sum()),
            "estimated_demand_kg": float(balances.estimated_demand_kg.sum()),
            "positive_surplus_kg": float(balances.potential_surplus_kg.sum()),
            "shortage_kg": float(balances.shortage_kg.sum())}
