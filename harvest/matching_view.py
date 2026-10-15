"""Buyer Matching screen: transparent preview over active validated inputs."""
import hashlib
import json
import pandas as pd
import plotly.express as px
from .locale_ui import st
from .matching import matching_preview
from .views import number, provenance


def matching_view(t):
    agriculture = st.session_state.get('active_data')
    buyers = st.session_state.get('active_buyers')
    if agriculture is None:
        st.info(t('Load agriculture data before buyer matching'))
        return
    if buyers is None:
        st.info(t('Load buyer opportunities in Upload Data or use Load demo data'))
        return
    meta = st.session_state.get('buyers_metadata') or {}
    st.warning(t('Sample opportunities only; not confirmed orders' if meta.get('origin') == 'sample'
                 else 'Uploaded opportunities; not confirmed orders'))
    st.caption(t('Preview only: no stock reserved, no buyer contacted, no order created'))
    st.subheader(t('Allocation rules'))
    st.write(t('Buyer rows are processed once in CSV source order; earlier rows get surplus first'))
    st.write(t('Each allocation is capped at the buyer request and remaining positive crop surplus'))
    st.caption(t('Crop names match ignoring case/outer whitespace. Duplicate buyer/crop identities are rejected on upload. / பயிர்ப் பெயர்கள் பொருத்தப்படுகின்றன; நகல் வாங்குபவர்/பயிர் பதிவுகள் நிராகரிக்கப்படும்.'))
    st.caption(t('This is a deterministic preview, not an optimal-profit allocation'))
    try:
        allocations, balances, audit = matching_preview(agriculture, buyers)
    except ValueError as exc:
        st.error(str(exc))
        return
    fingerprint = hashlib.sha256((agriculture.to_json() + buyers.to_json()).encode()).hexdigest()[:12]
    # A view filter only: allocations are always computed against ALL active buyers.
    names = {}
    for name in list(agriculture.crop) + list(buyers.crop):
        names.setdefault(name.casefold(), name)
    crop = st.selectbox(t('Matching crop filter'), [None] + list(names),
                        format_func=lambda key: t('All crops') if key is None else names[key],
                        key=f'matching_crop_{fingerprint}')
    st.caption(t('Filters change the view only; allocation source order and full-dataset calculations stay unchanged'))
    if crop is None:
        shown_balances, shown_audit, shown_allocations = balances, audit, allocations
    else:
        shown_balances = balances.loc[balances.crop.str.casefold() == crop]
        shown_audit = audit.loc[audit.crop.str.casefold() == crop]
        shown_allocations = allocations.loc[allocations.crop.str.casefold() == crop]
    cols = st.columns(3)
    for col, name, field in zip(cols, ['Potential surplus (kg)', 'Potentially matched (kg)', 'Still unmatched (kg)'],
                               ['potential_surplus_kg', 'matched_kg', 'unmatched_kg']):
        col.metric(t(name), number(shown_balances[field].sum()))
    st.caption(t('Matching totals reflect the selected crop; All crops shows full-dataset totals'))
    st.subheader(t('Crop allocation summary'))
    columns = ['crop', 'potential_surplus_kg', 'matched_kg', 'unmatched_kg', 'shortage_kg']
    if shown_balances.empty:
        st.info(t('Selected crop has no agriculture record and no allocatable surplus'))
    else:
        st.dataframe(shown_balances[columns].rename(columns=t), hide_index=True, width='stretch')
        chart = shown_balances.melt(id_vars='crop', value_vars=['matched_kg', 'unmatched_kg'], var_name='measure', value_name='kg')
        chart['measure'] = chart.measure.map(t)
        fig = px.bar(chart, x='crop', y='kg', color='measure', pattern_shape='measure', barmode='stack',
                     labels={'crop': t('Crop'), 'kg': t('Quantity (kg)'), 'measure': t('Measure')},
                     color_discrete_sequence=['#166534', '#1E40AF'])
        fig.update_layout(legend={'orientation': 'h', 'y': -0.3}, margin={'t': 20, 'b': 90})
        st.plotly_chart(fig, width='stretch')
    st.subheader(t('Potential buyer allocations'))
    if shown_allocations.empty:
        st.info(t('No potential allocations for this view; see the audit for reasons'))
    else:
        st.dataframe(shown_allocations.rename(columns=t), hide_index=True, width='stretch')
    st.caption(t('Estimated return after transport = matched kg × offer ₹/kg − full quoted transport. No allocation means no trip/cost. / போக்குவரத்துக்குப் பிந்தைய வருவாய் = ஒதுக்கிய கிலோ × விலை − போக்குவரத்து.'))
    st.caption(t('Returns after transport are estimates, not profit; production and other costs are unknown'))
    if (shown_allocations.estimated_return_after_transport < 0).any():
        st.warning(t('Some allocated opportunities have negative returns after transport; review before acting'))
    st.subheader(t('Buyer allocation audit'))
    st.caption(t('Audit includes unmatched requests and source record numbers, in allocation order'))
    shown_audit = shown_audit.copy()
    display = shown_audit.copy()
    display['status'] = display.status.map(t)
    st.dataframe(display.rename(columns=t), hide_index=True, width='stretch')
    st.caption(t('Unfilled buyer requests are separate from crop shortages and unmatched crop surplus'))
    # CSVs retain stable schema identifiers; include scope and order in every preview row.
    export = shown_audit.assign(opportunity_origin=meta.get('origin', 'unknown'),
                               order_status='not_confirmed', allocation_rule='csv_source_order',
                               view_crop=crop if crop is not None else 'all_crops')
    st.download_button(t('Download allocation audit'), export.to_csv(index=False).encode('utf-8-sig'),
                       file_name='buyer_allocation_audit.csv', mime='text/csv', key='download_matching_audit')
    st.download_button(t('Download crop matching summary'), shown_balances[columns].to_csv(index=False).encode('utf-8-sig'),
                       file_name='crop_matching_summary.csv', mime='text/csv', key='download_matching_summary')
    provenance_report = {'allocation_rule': 'csv_source_order', 'scope': 'all_active_buyers_before_view_filter',
                         'confirmation': 'none', 'agriculture': st.session_state.get('agriculture_metadata'),
                         'buyers': meta}
    st.download_button(t('Download matching provenance'), json.dumps(provenance_report, indent=2).encode(),
                       file_name='matching_provenance.json', mime='application/json')
    st.subheader(t('Agriculture source'))
    provenance(st.session_state.get('agriculture_metadata'), t)
    st.subheader(t('Buyer source'))
    provenance(meta, t)
