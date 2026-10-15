"""CEBAFEX visual system and escaped, localized presentation components."""
from base64 import b64encode
from html import escape
from pathlib import Path
from .locale_ui import st
from .analytics import calculate_kpis
from .risk import prioritise_crop
from .business import fingerprint
from .views import number

ROOT=Path(__file__).resolve().parents[1]


def apply_brand():
    st.markdown((ROOT/'static/brand/business.css').read_text(),unsafe_allow_html=True)


def sidebar_brand(t):
    if t.language=='English':
        logo=b64encode((ROOT/'static/brand/cebafex-logo.png').read_bytes()).decode()
        st.sidebar.markdown(f'<div class="brand-logo"><img src="data:image/png;base64,{logo}" alt="{escape(t("Company logo"))}" /></div>',unsafe_allow_html=True)
    st.sidebar.markdown(f'<div class="brand-name">{escape(t("CEBAFEX"))}<span>{escape(t("Agricultural intelligence"))}</span></div>',unsafe_allow_html=True)


def workspace_status(t):
    has_data=st.session_state.get('active_data') is not None or st.session_state.get('active_buyers') is not None
    saved=st.session_state.get('_saved_fingerprint')
    has_data=has_data or st.session_state.get('_records_changed',False)
    dirty=has_data and (not saved or fingerprint(st.session_state)!=saved)
    if st.session_state.get('planning_source')=='ledger':
        has_data=False;saved=True;dirty=False
    status='Unsaved changes' if dirty else ('Saved workspace' if saved else 'Session workspace')
    tone='pending' if dirty else 'ready'
    st.markdown(f'<div class="workspace-bar"><span class="workspace-label">{escape(t("Business workspace"))}</span><span class="workspace-status {tone}"><i aria-hidden="true"></i>{escape(t(status))}</span></div>',unsafe_allow_html=True)


def navigate(page):
    language=st.session_state.get('language','English')
    st.session_state['navigation']=page
    st.session_state[f'navigation__ui_{language}']=page


def home_view(t):
    st.markdown(f'''<section class="business-hero"><div><p class="eyebrow">{escape(t('Agricultural intelligence'))}</p><h2>{escape(t('Your crop operations, in one clear workspace.'))}</h2><p class="hero-copy">{escape(t('Manage stock, review surplus and compare buyer opportunities using your own validated records.'))}</p></div><div class="hero-symbol" aria-hidden="true"><svg viewBox="0 0 200 200" fill="none"><circle cx="100" cy="100" r="81" stroke="currentColor" stroke-opacity=".22"/><circle cx="100" cy="100" r="57" stroke="currentColor" stroke-opacity=".22"/><path d="M100 155V72M100 106C66 108 48 86 49 60c33-1 52 17 51 46ZM101 88c-1-33 19-50 49-48 1 31-17 49-49 48Z" stroke="currentColor" stroke-width="5" stroke-linejoin="round"/><path d="m151 124 9 9 19-22" stroke="currentColor" stroke-width="4" stroke-linecap="round"/></svg></div></section>''',unsafe_allow_html=True)
    primary,secondary=st.columns([1,1])
    primary.button(t('Get Started'),key='get_started',on_click=navigate,args=('Upload Data',),type='primary',width='stretch')
    secondary.button(t('Manage records'),key='home_manage',on_click=navigate,args=('Workspace',),width='stretch')
    active=st.session_state.get('active_data')
    if active is not None:
        st.subheader(t('Current workspace'))
        kpis=calculate_kpis(active)
        for col,(label,key) in zip(st.columns(4),[('Uploaded records','records'),('Available (kg)','available_kg'),('Potential surplus (kg)','positive_surplus_kg'),('Shortage (kg)','shortage_kg')]):
            col.metric(t(label),number(kpis[key]))
        priority=prioritise_crop(active)
        if priority:
            crop=priority['crop'] if isinstance(priority,dict) else priority.crop
            surplus=priority['potential_surplus_kg'] if isinstance(priority,dict) else priority.potential_surplus_kg
            st.markdown(f'<div class="decision-card"><div><p class="eyebrow">{escape(t("Decision focus"))}</p><h3>{escape(t.entity(crop,"Crop"))}</h3><p>{escape(t("Potential surplus to review"))} · <strong>{number(surplus)} {escape(t("kg"))}</strong></p></div><span class="decision-mark" aria-hidden="true">↗</span></div>',unsafe_allow_html=True)
            st.button(t('View risk review'),key='home_risk',on_click=navigate,args=('Surplus and Risk',))
        else:st.info(t('No positive surplus in the active records.'))
        left,right=st.columns(2)
        left.button(t('Open dashboard'),key='home_dashboard',on_click=navigate,args=('Dashboard',),width='stretch')
        right.button(t('Review opportunities'),key='home_buyers',on_click=navigate,args=('Buyer Matching',),width='stretch')
    else:
        st.markdown(f'<div class="onboarding-card"><span class="step-number">01</span><div><h3>{escape(t("Ready for your first dataset"))}</h3><p>{escape(t("Import a spreadsheet or enter crop and buyer records directly. Calculations update across every screen."))}</p></div></div>',unsafe_allow_html=True)
    st.subheader(t('Workspace guide'))
    cards=[('01','Import and validate','Upload files or maintain records in the workspace.'),('02','Understand your stock','See demand gaps and review crops with potential surplus.'),('03','Compare selling options','Preview capped allocations and returns after transport.'),('04','Keep a saved version','Save your datasets and planning rules together with version history.')]
    html=''.join(f'<article class="guide-card"><span>{n}</span><h3>{escape(t(title))}</h3><p>{escape(t(body))}</p></article>' for n,title,body in cards)
    st.markdown('<div class="guide-grid">'+html+'</div>',unsafe_allow_html=True)
    with st.expander(t('Use your own data')):
        st.caption(t('Demand remains an uploaded estimate. No live market feed or model forecast is generated. / தேவை பதிவேற்றிய மதிப்பீடு; நேரடிச் சந்தைத் தரவு அல்லது மாதிரி முன்னறிவிப்பு இல்லை.'))
        for filename,title in [('agriculture_demo.csv','Download agriculture sample'),('buyers_demo.csv','Download buyers sample'),('agriculture_messy_demo.csv','Download quality-check sample')]:
            st.download_button(t(title),(ROOT/'data'/filename).read_bytes(),file_name=filename,mime='text/csv')
        st.warning(t('Sample opportunities only; not confirmed orders'))
