"""Surplus and Risk screen; a presentation layer over shared pure functions."""
import json
import pandas as pd
import plotly.express as px
from .locale_ui import st
from .risk import RiskPolicy, analyse_risk, prioritise_crop
from .views import number, provenance
from .locale_ui import risk_reason


def risk_view(t):
    active = st.session_state.get('active_data')
    if active is None:
        st.info(t('Load demo data or validate an agriculture CSV first / முதலில் வேளாண் தரவை ஏற்றவும்'))
        return
    st.warning(t('Planning signals only; not measured spoilage or shelf life'))
    policy = RiskPolicy.from_dict(st.session_state.get('risk_policy'))
    with st.expander(t('Planning assumptions'), expanded=True):
        st.caption(t('Demo defaults are adjustable planning choices, not crop-specific science. / மாதிரி வரம்புகள் திட்டமிடும் தேர்வுகள்; பயிரின் ஆயுள் குறித்த அறிவியல் முடிவுகள் அல்ல.'))
        with st.form('risk_policy_form'):
            ratio = st.number_input(t('Large surplus threshold (%)'), min_value=0.0, max_value=100.0,
                                     value=policy.high_surplus_ratio * 100, step=1.0, key='risk_threshold_pct')
            days = st.number_input(t('Harvest age review threshold (days)'), min_value=0.0,
                                    value=policy.age_review_days, step=1.0, key='risk_age_days')
            apply = st.form_submit_button(t('Apply planning rules'), key='apply_risk_policy')
        if apply:
            try:
                policy = RiskPolicy(ratio / 100, days)
                st.session_state.risk_policy = policy.to_dict()
                st.success(t('Planning rules applied'))
            except ValueError as exc:
                st.error(str(exc))
        st.write(t('Large-surplus threshold: {ratio}%; harvest-age review threshold: {days} days.',ratio=f'{policy.high_surplus_ratio*100:g}',days=f'{policy.age_review_days:g}'))
        st.write(t('For surplus crops: review score = large-surplus flag + age-review flag. 0 = Low; 1 = Moderate; 2 = High. Crops without surplus show No surplus, with age review shown independently.'))
        st.caption(t('These are review categories, not probabilities. No temperature, storage condition or crop shelf-life data is available. / இவை பரிசீலனைப் பிரிவுகள்; அழுகும் நிகழ்தகவு அல்ல.'))
    report = analyse_risk(active, policy)
    # All-data recommendation is stable regardless of this screen or Dashboard filters.
    recommendation = prioritise_crop(active, policy)
    st.subheader(t('First crop to review for surplus selling'))
    st.caption(t('Priority uses the full active dataset; filters below only change the report view'))
    if recommendation is None:
        st.info(t('No positive surplus; no crop prioritised for surplus selling'))
    else:
        st.success(t('Potential surplus: {crop}, {quantity} kg.',crop=t.entity(recommendation['crop'],'Crop'),quantity=number(recommendation['potential_surplus_kg'])))
        st.write(t('Selling priority: largest positive surplus, then older harvest, then crop name'))
        st.write(risk_reason(report.loc[report.crop == recommendation['crop']].iloc[0].to_dict(),t))
    st.subheader(t('Surplus and shortage overview'))
    columns = st.columns(3)
    columns[0].metric(t('Potential surplus (kg)'), number(report.potential_surplus_kg.sum()))
    columns[1].metric(t('Shortage (kg)'), number(report.shortage_kg.sum()))
    columns[2].metric(t('High review crops'), str(int((report.review_level == 'High').sum())))
    st.caption(t('Overview totals use all active crops'))
    selected = st.multiselect(t('Review category filter'), ['High', 'Moderate', 'Low', 'No surplus'],
                              default=['High', 'Moderate', 'Low', 'No surplus'], format_func=t, key='risk_level_filter')
    filtered = report.loc[report.review_level.isin(selected)].sort_values('priority_rank', na_position='last')
    if filtered.empty:
        st.info(t('No records match this filter'))
        return
    chart = filtered.melt(id_vars='crop', value_vars=['potential_surplus_kg', 'shortage_kg'], var_name='measure', value_name='kg')
    chart['measure'] = chart.measure.map(t)
    fig = px.bar(chart, x='crop', y='kg', color='measure', barmode='group', pattern_shape='measure',
                 labels={'crop': t('Crop'), 'kg': t('Quantity (kg)'), 'measure': t('Measure')},
                 color_discrete_sequence=['#087F8C', '#075C86'])
    fig.update_layout(legend={'orientation': 'h', 'y': -0.3}, margin={'t': 20, 'b': 90})
    st.plotly_chart(fig, width='stretch')
    display = filtered.copy()
    display['surplus_ratio'] = display.surplus_ratio.map(lambda value: f'{value:.2%}')
    for col in ['balance_status', 'review_level']:
        display[col] = display[col].map(t)
    for col in ['high_surplus_flag', 'age_review_flag']:
        display[col] = display[col].map(lambda value: t('Yes' if value else 'No'))
    st.dataframe(display.rename(columns=t), hide_index=True, width='stretch')
    for row in filtered.itertuples():
        with st.expander(f'{t.entity(row.crop,"Crop")} · {t(row.review_level)}'):
            st.write(risk_reason(row,t))
            if row.shortage_kg > 0:
                st.info(t('Review shortage separately; this crop has no surplus to allocate'))
            if row.age_review_flag:
                st.caption(t('Inspect stock condition; age alone does not prove spoilage'))
    export = filtered.assign(policy_high_surplus_ratio=policy.high_surplus_ratio,
                             policy_age_review_days=policy.age_review_days,
                             policy_scope='planning_only_not_spoilage_prediction',
                             ranking_scope='full_active_agriculture_dataset')
    st.download_button(t('Download risk report'), export.to_csv(index=False).encode('utf-8-sig'),
                       file_name='surplus_risk_report.csv', mime='text/csv', key='download_risk')
    st.download_button(t('Download planning policy'), json.dumps(policy.to_dict(), indent=2).encode(),
                       file_name='planning_policy.json', mime='application/json')
    provenance(st.session_state.get('agriculture_metadata'), t)
