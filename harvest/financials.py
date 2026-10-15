"""Compare identical matched quantities; never invent market transport or production costs."""
from dataclasses import dataclass
import pandas as pd
from .matching import matching_preview
from .money import gross_return, money, sum_money, nonnegative_decimal

DETAIL_COLUMNS = ['source_record', 'buyer_name', 'buyer_type', 'crop', 'matched_kg',
                  'offer_price_per_kg', 'market_price_per_kg', 'buyer_gross_revenue',
                  'buyer_transport_cost', 'estimated_return_after_transport',
                  'market_gross_reference', 'difference_vs_market_gross_reference', 'calculation']

@dataclass
class FinancialReport:
    buyers: pd.DataFrame
    crops: pd.DataFrame
    totals: dict


def analyse_financials(data, buyers):
    _, balances, audit = matching_preview(data, buyers)
    prices = {row.crop.casefold(): row.market_price_per_kg for row in balances.itertuples()}
    records = []
    for row in audit.loc[audit.matched_kg > 0].itertuples():
        price = prices[row.crop.casefold()]
        gross = gross_return(row.matched_kg, row.offer_price_per_kg)
        reference = gross_return(row.matched_kg, price)
        records.append({'source_record': row.source_record, 'buyer_name': row.buyer_name,
                        'buyer_type': row.buyer_type, 'crop': row.crop, 'matched_kg': row.matched_kg,
                        'offer_price_per_kg': row.offer_price_per_kg, 'market_price_per_kg': price,
                        'buyer_gross_revenue': gross, 'buyer_transport_cost': row.charged_transport_cost,
                        'estimated_return_after_transport': row.estimated_return_after_transport,
                        'market_gross_reference': reference,
                        'difference_vs_market_gross_reference': money(row.estimated_return_after_transport - reference),
                        'calculation': f'{row.matched_kg:g} kg × ₹{row.offer_price_per_kg:g}/kg − ₹{row.charged_transport_cost:g} transport = ₹{row.estimated_return_after_transport:,.2f}'})
    detail = pd.DataFrame(records, columns=DETAIL_COLUMNS)
    crops = balances[['crop', 'potential_surplus_kg', 'matched_kg', 'unmatched_kg', 'shortage_kg', 'market_price_per_kg']].copy()
    sums = ['buyer_gross_revenue', 'buyer_transport_cost', 'estimated_return_after_transport',
            'market_gross_reference', 'difference_vs_market_gross_reference']
    for field in sums:
        crops[field] = [sum_money(detail.loc[detail.crop.str.casefold() == crop.casefold(), field]) for crop in crops.crop]
    crops['unmatched_market_reference'] = [gross_return(row.unmatched_kg, row.market_price_per_kg) for row in crops.itertuples()]
    return FinancialReport(detail, crops, financial_totals(crops))


def financial_totals(crops):
    totals = {field: float(crops[field].sum()) for field in ['potential_surplus_kg', 'matched_kg', 'unmatched_kg', 'shortage_kg']}
    for field in ['buyer_gross_revenue', 'buyer_transport_cost', 'estimated_return_after_transport',
                  'market_gross_reference', 'difference_vs_market_gross_reference', 'unmatched_market_reference']:
        totals[field] = sum_money(crops[field])
    return totals


def market_transport_scenario(totals, assumed_market_transport):
    """Explicit user assumption: one TOTAL market transport quote for this matched scope."""
    cost = nonnegative_decimal(money(nonnegative_decimal(assumed_market_transport)))
    if totals['matched_kg'] <= 0:
        return {'assumed_market_transport_quote': float(cost), 'applied_market_transport': 0.0, 'market_return_after_assumed_transport': 0.0,
                'difference_vs_market_after_assumed_transport': 0.0}
    net = money(nonnegative_decimal(totals['market_gross_reference']) - cost)
    return {'assumed_market_transport_quote': float(cost), 'applied_market_transport': float(cost), 'market_return_after_assumed_transport': net,
            'difference_vs_market_after_assumed_transport': money(totals['estimated_return_after_transport'] - net)}
