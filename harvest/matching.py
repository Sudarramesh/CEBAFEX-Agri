"""Deterministic, stateless source-order allocation previews; no orders or reservations."""
import pandas as pd
from .analytics import crop_balances
from .data import require_valid
from .money import return_after_transport, money

ALLOCATION_COLUMNS = ['buyer_name', 'buyer_type', 'crop', 'matched_kg',
                      'offer_price_per_kg', 'transport_cost', 'estimated_return_after_transport']
AUDIT_COLUMNS = ['source_record', 'buyer_name', 'buyer_type', 'crop', 'required_kg',
                 'surplus_before_kg', 'matched_kg', 'unfilled_request_kg', 'surplus_after_kg',
                 'status', 'offer_price_per_kg', 'transport_cost', 'charged_transport_cost',
                 'estimated_return_after_transport', 'reason']


def estimated_return(quantity, price, transport):
    return return_after_transport(quantity, price, transport)


def matching_preview(data, buyers):
    """One preview, one pass over validated buyer identities; full audit including skips.

    Validation rejects repeated (buyer_name, crop) identities ignoring case/space.
    Full quoted transport is charged per positively allocated buyer/crop row, even
    on partial fills. Multiple crops for one buyer are separate quoted trips.
    """
    balances = crop_balances(data)
    buyers = require_valid(buyers, 'buyers')
    initial = {row.crop.casefold(): float(row.potential_surplus_kg) for row in balances.itertuples()}
    remaining = dict(initial)
    records, audit = [], []
    for source_record, buyer in enumerate(buyers.itertuples(), 1):
        key = buyer.crop.casefold()
        before = remaining.get(key, 0.0)
        requested = float(buyer.required_kg)
        quantity = min(before, requested)
        after = before - quantity
        if key in remaining:
            remaining[key] = after
        net_return = estimated_return(quantity, buyer.offer_price_per_kg, buyer.transport_cost)
        if quantity > 0:
            status = 'Potential full match' if quantity == requested else 'Potential partial match'
            reason = f'min(remaining surplus {before:g} kg, request {requested:g} kg) = {quantity:g} kg; remaining {after:g} kg.'
            records.append({'buyer_name': buyer.buyer_name, 'buyer_type': buyer.buyer_type, 'crop': buyer.crop,
                            'matched_kg': quantity, 'offer_price_per_kg': buyer.offer_price_per_kg,
                            'transport_cost': money(buyer.transport_cost), 'estimated_return_after_transport': net_return})
        elif key not in initial:
            status, reason = 'Crop unavailable', 'Crop is absent from active agriculture; no surplus can be allocated.'
        elif requested == 0:
            status, reason = 'Zero request', 'Buyer requested zero kg; no trip or allocation is assumed.'
        elif initial[key] == 0:
            status, reason = 'No surplus', 'Active crop has no positive surplus after uploaded estimated demand.'
        else:
            status, reason = 'Surplus exhausted', 'Earlier buyer rows consumed the available surplus in this preview.'
        audit.append({'source_record': source_record, 'buyer_name': buyer.buyer_name,
                      'buyer_type': buyer.buyer_type, 'crop': buyer.crop, 'required_kg': requested,
                      'surplus_before_kg': before, 'matched_kg': quantity,
                      'unfilled_request_kg': requested - quantity, 'surplus_after_kg': after,
                      'status': status, 'offer_price_per_kg': buyer.offer_price_per_kg,
                      'transport_cost': buyer.transport_cost,
                      'charged_transport_cost': money(buyer.transport_cost) if quantity > 0 else 0.0,
                      'estimated_return_after_transport': net_return, 'reason': reason})
    balances['unmatched_kg'] = balances.crop.str.casefold().map(remaining)
    balances['matched_kg'] = balances.potential_surplus_kg - balances.unmatched_kg
    return (pd.DataFrame(records, columns=ALLOCATION_COLUMNS), balances,
            pd.DataFrame(audit, columns=AUDIT_COLUMNS))


def match_surplus(data, buyers):
    """Preserved Phase 1–3 public two-table API."""
    allocations, balances, _ = matching_preview(data, buyers)
    return allocations, balances
