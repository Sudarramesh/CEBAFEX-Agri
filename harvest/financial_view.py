"""Financial comparison UI with explicit missing-cost boundaries and optional user scenario."""
import hashlib
import json
import pandas as pd
import plotly.express as px
from .locale_ui import st
from .financials import analyse_financials, financial_totals, market_transport_scenario
from .views import number, provenance


def rupees(value):
    return f'₹{value:,.2f}'


def financial_view(t):
    data, buyers = st.session_state.get('active_data'), st.session_state.get('active_buyers')
    if data is None:
        st.info(t('Load agriculture data before financial analysis'))
        return
    if buyers is None:
        st.info(t('Load buyer opportunities in Upload Data or use Load demo data'))
        return
    meta = st.session_state.get('buyers_metadata') or {}
    st.warning(t('Sample opportunities only; not confirmed orders' if meta.get('origin') == 'sample' else 'Uploaded opportunities; not confirmed orders'))
    st.info(t('Estimated returns after transport, not profit; production and other costs are unknown'))
    st.caption(t('The page is named Profit Analysis for navigation; profit cannot be calculated from the supplied fields'))
    try:
        report = analyse_financials(data, buyers)
    except ValueError as exc:
        st.error(str(exc))
        return
    fingerprint = hashlib.sha256((data.to_json() + buyers.to_json()).encode()).hexdigest()[:12]
    crops = {crop.casefold(): crop for crop in data.crop}
    choice = st.selectbox(t('Financial crop filter'), [None] + list(crops),
                          format_func=lambda value: t('All crops') if value is None else crops[value],
                          key=f'financial_crop_{fingerprint}')
    scope = 'all_crops' if choice is None else choice
    crop_rows = report.crops if choice is None else report.crops.loc[report.crops.crop.str.casefold() == choice]
    detail = report.buyers if choice is None else report.buyers.loc[report.buyers.crop.str.casefold() == choice]
    totals = financial_totals(crop_rows)
    st.caption(t('Financial totals use the selected matched quantities; allocation order is unchanged'))
    metrics = [('Potentially matched (kg)', 'matched_kg'), ('Buyer gross revenue (₹)', 'buyer_gross_revenue'),
               ('Buyer transport charged (₹)', 'buyer_transport_cost'), ('Buyer return after transport (₹)', 'estimated_return_after_transport')]
    for start in (0, 2):
        for col, (name, field) in zip(st.columns(2), metrics[start:start+2]):
            col.metric(t(name), number(totals[field]) if field == 'matched_kg' else rupees(totals[field]))
    if totals['matched_kg'] == 0:
        st.info(t('No matched quantity in this view; no buyer revenue or transport is assumed'))
    if (detail.estimated_return_after_transport < 0).any():
        st.warning(t('Some allocated opportunities have negative returns after transport; review before acting'))
    st.subheader(t('Buyer calculation breakdown'))
    st.write(t('Buyer gross = matched kg × offer price; return after transport subtracts the full quoted trip cost once'))
    labels = {field: t(label) for field, label in {
        'buyer_gross_revenue': 'Buyer gross revenue (₹)', 'buyer_transport_cost': 'Buyer transport charged (₹)',
        'market_gross_reference': 'Market gross reference (₹)',
        'difference_vs_market_gross_reference': 'Difference versus gross reference (₹)',
        'calculation': 'Calculation'}.items()}
    st.dataframe(detail.rename(columns=lambda col: labels.get(col, t(col))), hide_index=True, width='stretch')
    st.caption(t('Currency: gross lines and charged trip costs are rounded to paise (decimal half-up), then subtracted; totals sum those lines. / பண மதிப்புகள் பைசாவிற்கு முழுமையாக்கப்படும்.'))
    st.caption(t('Partial allocations incur the full buyer transport quote; zero allocation incurs no trip'))
    st.subheader(t('Compare the same matched quantities'))
    st.write(t('Market reference = matched kg × uploaded market price, before market transport and other costs'))
    st.warning(t('Market transport is unknown by default; the gross reference is not a net return or a confirmed sale'))
    st.metric(t('Market gross reference (₹)'), rupees(totals['market_gross_reference']))
    st.metric(t('Difference versus gross reference (₹)'), rupees(totals['difference_vs_market_gross_reference']))
    st.caption(t('Difference = buyer return after transport minus market gross reference; it is not a net advantage or profit'))
    comparison = pd.DataFrame({'option': [t('Buyer return after transport (₹)'), t('Market gross reference (₹)')],
                               'INR': [totals['estimated_return_after_transport'], totals['market_gross_reference']]})
    fig = px.bar(comparison, x='option', y='INR', color='option', pattern_shape='option',
                 color_discrete_sequence=['#087F8C', '#075C86'], labels={'option': t('Reference type'), 'INR': '₹'})
    fig.update_layout(showlegend=False, margin={'t':20, 'b':30})
    st.plotly_chart(fig, width='stretch')
    scenario = None
    with st.expander(t('Optional market transport scenario')):
        st.caption(t('Enter one total market transport assumption for only the selected matched quantity'))
        enabled = st.checkbox(t('I want to supply a market transport assumption'), key=f'market_scenario_{fingerprint}_{scope}')
        if enabled:
            cost = st.number_input(t('Assumed total market transport (₹)'), min_value=0.0, value=0.0, step=10.0,
                                    key=f'market_cost_{fingerprint}_{scope}')
            scenario = market_transport_scenario(totals, cost)
            st.metric(t('Market return after assumed transport (₹)'), rupees(scenario['market_return_after_assumed_transport']))
            st.metric(t('Buyer difference versus market scenario (₹)'), rupees(scenario['difference_vs_market_after_assumed_transport']))
            st.caption(t('User assumption only; an entered zero explicitly assumes zero transport. Other costs remain unknown'))
            st.caption(t('This scenario is session-only and is not included in workspace snapshots'))
    st.subheader(t('Unmatched surplus stays separate'))
    st.write(t('{quantity} kg · ₹{amount} — unmatched reference before costs, not revenue.',quantity=number(totals['unmatched_kg']),amount=f"{totals['unmatched_market_reference']:,.2f}"))
    st.dataframe(crop_rows.rename(columns=lambda col: labels.get(col, t(col))), hide_index=True, width='stretch')
    st.caption(t('Never add unmatched reference value to buyer revenue; no buyer allocation exists for it'))
    assumptions = {'scope': scope, 'allocation_rule': 'csv_source_order', 'buyer_order_status': 'not_confirmed',
                   'market_transport': 'unknown' if scenario is None else 'user_assumption',
                   'market_transport_scenario': scenario, 'totals': totals,
                   'profit': 'not_calculable_production_and_other_costs_unknown',
                   'unmatched_reference': 'separate_not_revenue', 'currency': 'INR',
                   'rounding': 'gross lines and charged costs to paise using decimal ROUND_HALF_UP, then subtract; totals sum rounded lines',
                   'agriculture_metadata': st.session_state.get('agriculture_metadata'), 'buyer_metadata': meta}
    st.download_button(t('Download buyer financial report'), detail.assign(opportunity_origin=meta.get('origin','unknown'),
                       order_status='not_confirmed').to_csv(index=False).encode('utf-8-sig'),
                       file_name='buyer_financial_report.csv', mime='text/csv')
    st.download_button(t('Download crop financial summary'), crop_rows.to_csv(index=False).encode('utf-8-sig'),
                       file_name='crop_financial_summary.csv', mime='text/csv')
    st.download_button(t('Download financial assumptions and totals'), json.dumps(assumptions, indent=2).encode(),
                       file_name='financial_assumptions.json', mime='application/json')
    st.subheader(t('Agriculture source'))
    provenance(st.session_state.get('agriculture_metadata'), t)
    st.subheader(t('Buyer source'))
    provenance(meta, t)
