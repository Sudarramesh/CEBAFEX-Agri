"""Streamlit presentation only; calculations and validation live in separate modules."""
import hashlib
import pandas as pd
import plotly.express as px
from .locale_ui import st
from .analytics import calculate_kpis, crop_balances
from .data import suggest_mapping
from .tabular import read_table,interpret_columns,sheets
from .ingestion import read_csv_bytes, prepare_dataset, activate_dataset, buyer_coverage


def number(value):
    return f"{value:,.3f}".rstrip('0').rstrip('.') if float(value) != int(value) else f"{value:,.0f}"


def provenance(metadata, t):
    if metadata and metadata.get('origin')=='operations':
        st.caption(t('Derived from stock lots, recorded movements and reservations. See Supply Network for source identities.'));return
    if metadata:
        with st.expander(t('Data provenance')):
            info = pd.DataFrame([{'Check':t('File'),'value':t.entity(metadata.get('filename',''),'Source file')},
                {'Check':t('Origin'),'value':t(metadata.get('origin','unknown'))},
                {'Check':t('Records'),'value':str(metadata.get('rows',0))},
                {'Check':t('Validated at'),'value':str(metadata.get('validated_at_utc','')).replace('T',' ').replace('Z','')}])
            st.dataframe(info, hide_index=True, width='stretch')


def upload_view(t):
    st.caption(t('CSV and Excel workbooks are supported. Export formulas as values before uploading.'))
    kind = st.radio(t('Dataset type'), ['agriculture', 'buyers'],
                    format_func=lambda v: t('Agriculture' if v == 'agriculture' else 'Buyers'),
                    key='dataset_kind', horizontal=True)
    st.caption(t('kg · ₹/kg · days / நாட்கள். Transport is ₹ per buyer trip / போக்குவரத்து ₹ ஒரு பயணத்திற்கு.'))
    if kind == 'buyers':
        st.warning(t('Uploaded opportunities; not confirmed orders'))
    uploaded = st.file_uploader(t('Upload agriculture CSV' if kind == 'agriculture' else 'Upload buyers CSV'),
                                type=['csv','xlsx'], key=f'upload_{kind}')
    if uploaded is not None:
        payload = uploaded.getvalue()
        digest = hashlib.sha256(payload).hexdigest()
        try:
            sheet=None
            if uploaded.name.lower().endswith('.xlsx'):
                choices=sheets(payload)
                sheet=st.selectbox(t('Workbook sheet'),choices,key=f'sheet_{kind}_{digest}')
            raw = read_table(payload,uploaded.name,sheet)
            st.subheader(t('Preview'))
            st.dataframe(raw.head(20), hide_index=True, width='stretch')
            suggestions,interpretation = interpret_columns(raw,kind)
            with st.expander(t('Column interpretation notes')):
                for item in interpretation:
                    st.write(t(item['target'])+' · '+t(item['method'])+' · '+t(item['confidence']))
                st.caption(t('Heuristic suggestions require your review; meanings are not verified by a language model.'))
            st.subheader(t('Column mapping'))
            st.caption(t('Choose each source column once. Ambiguous suggestions are left blank / குழப்பமான பொருத்தங்களைத் தேர்ந்தெடுக்கவும்.'))
            mapping = {}
            with st.form(f'map_{kind}_{digest}'):
                for target, suggestion in suggestions.items():
                    options = [None] + list(raw.columns)
                    mapping[target] = st.selectbox(t(target), options, index=options.index(suggestion),
                        format_func=lambda v: t('Select column') if v is None else str(v),
                        key=f'map_{kind}_{digest}_{target}')
                submitted = st.form_submit_button(t('Validate and activate'), key=f'validate_{kind}')
            if submitted:
                result, meta = prepare_dataset(payload, uploaded.name, kind, mapping,sheet=sheet)
                success = activate_dataset(st.session_state, result, meta)
                st.session_state[f'report_{kind}'] = {'result': result, 'digest': digest, 'name': uploaded.name, 'success': success}
                # Rerun updates sidebar provenance and every screen from the newly committed state.
                st.rerun()
            report = st.session_state.get(f'report_{kind}')
            if report and report['digest'] == digest:
                show_report(report, t, kind)
        except ValueError as exc:
            st.error(f'CSV / கோப்புப் பிழை: {exc}')
    key = 'active_data' if kind == 'agriculture' else 'active_buyers'
    current = st.session_state.get(key)
    if current is not None:
        st.subheader(t('Active validated data'))
        st.dataframe(current.rename(columns=t), hide_index=True, width='stretch')
        provenance(st.session_state.get(f'{kind}_metadata'), t)
        st.download_button(t('Download validated CSV'), current.to_csv(index=False).encode('utf-8-sig'),
                           file_name=f'{kind}_validated.csv', mime='text/csv', key=f'export_{kind}')
        if kind == 'buyers':
            st.subheader(t('Match compatibility'))
            st.caption(t('Coverage checks crop names only; allocations are not calculated here / பயிர்ப் பெயர்கள் மட்டும் ஒப்பிடப்படுகின்றன.'))
            coverage = buyer_coverage(st.session_state.get('active_data'), current)
            st.dataframe(coverage[['buyer_name', 'crop', 'crop_in_active_agriculture']], hide_index=True, width='stretch')


def show_report(report, t, kind):
    result = report['result']
    st.subheader(t('Quality summary'))
    st.caption(t.entity(report['name'],'Source file'))
    names = [('Input records', 'input_rows'), ('Valid records', 'valid_rows'),
             ('Invalid records', 'invalid_rows'), ('Unassessed records', 'not_assessed_rows'), ('Duplicate records', 'duplicate_rows'), ('Missing cells', 'missing_cells')]
    st.dataframe(pd.DataFrame([{'Check / சோதனை': t(name), 'Count / எண்ணிக்கை': result.summary[key]}
                              for name, key in names]), hide_index=True, width='stretch')
    for warning in result.warnings:
        st.warning(warning)
    for error in result.errors:
        st.error(error)
    if result.issues:
        st.subheader(t('Row issues'))
        issues = pd.DataFrame(result.issues)
        st.caption(t('Record numbers start at 1 after the header / தலைப்புக்குப் பின் பதிவு எண் 1 இல் தொடங்கும்.'))
        st.dataframe(issues, hide_index=True, width='stretch')
        st.download_button(t('Download issue report'), issues.to_csv(index=False).encode('utf-8-sig'),
                           file_name=f'{kind}_issues.csv', mime='text/csv', key=f'issues_{kind}')
    if result.errors:
        st.info(t('Fix errors and validate again; previous active data is preserved'))
    else:
        st.success(t('Validated and active'))


def dashboard_view(t):
    active = st.session_state.get('active_data')
    if active is None:
        st.info(t('Load demo data or validate an agriculture CSV first / முதலில் வேளாண் தரவை ஏற்றவும்'))
        return
    st.caption(t('KPIs and charts below reflect selected crops only / கீழுள்ள கணக்குகள் தேர்ந்தெடுத்த பயிர்களுக்கு மட்டும்.'))
    # Dataset changes reset the selection; edits to only buyer data do not.
    fingerprint = hashlib.sha256(active.to_json().encode()).hexdigest()[:12]
    selected = st.multiselect(t('Crop filter'), list(active.crop), default=list(active.crop), key=f'crops_{fingerprint}')
    if not selected:
        st.info(t('No crops selected'))
        return
    filtered = active.loc[active.crop.isin(selected)].copy()
    kpis = calculate_kpis(filtered)
    names = [('Uploaded records', 'records'), ('Available (kg)', 'available_kg'),
             ('Estimated demand (kg)', 'estimated_demand_kg'), ('Potential surplus (kg)', 'positive_surplus_kg'),
             ('Shortage (kg)', 'shortage_kg')]
    for start in range(0, len(names), 3):
        for col, (name, key) in zip(st.columns(min(3, len(names)-start)), names[start:start+3]):
            col.metric(t(name), number(kpis[key]))
    balances = crop_balances(filtered)
    chart = balances.melt(id_vars='crop', value_vars=['available_kg', 'estimated_demand_kg'],
                          var_name='measure', value_name='kg')
    chart['measure'] = chart['measure'].map(t)
    fig = px.bar(chart, x='crop', y='kg', color='measure', barmode='group',
                 labels={'crop': t('Crop'), 'kg': t('Quantity (kg)'), 'measure': t('Measure')},
                 color_discrete_sequence=['#087F8C', '#075C86'], pattern_shape='measure')
    fig.update_layout(legend={'orientation': 'h', 'y': -0.3}, margin={'t': 20, 'b': 90})
    st.plotly_chart(fig, width='stretch')
    st.subheader(t('Active validated data'))
    st.dataframe(balances.rename(columns=t), hide_index=True, width='stretch')
    st.download_button(t('Download filtered balances'), balances.to_csv(index=False).encode('utf-8-sig'),
                       file_name='filtered_crop_balances.csv', mime='text/csv')
    st.caption(t('Surplus = max(available − uploaded estimated demand, 0). Shortage = max(demand − available, 0). Summed separately / உபரி மற்றும் பற்றாக்குறை தனித்தனியாகக் கணக்கிடப்படுகின்றன.'))
    st.info(t('No model-generated forecast'))
    provenance(st.session_state.get('agriculture_metadata'), t)
    buyers = st.session_state.get('active_buyers')
    if buyers is not None:
        st.subheader(t('Active buyers'))
        meta = st.session_state.get('buyers_metadata') or {}
        st.warning(t('Sample opportunities only; not confirmed orders' if meta.get('origin') == 'sample'
                     else 'Uploaded opportunities; not confirmed orders'))
        st.caption(t('Buyer records: {n}. Count covers the full buyer dataset.',n=len(buyers)))
        provenance(meta, t)
