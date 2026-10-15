"""Language-pure rendering boundary. Canonical validated data is never translated in place."""
import base64
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import pandas as pd
import streamlit as native
import streamlit.components.v1 as components
from .i18n import Translator, LABELS, REVERSE, LATIN, TAMIL, label

COLUMN_ALIASES = {'crop_nm':'crop','crop_name':'crop','qty_avail':'available_kg','est_demand':'estimated_demand_kg',
 'mkt_prc':'market_price_per_kg','harvest_age':'harvest_age_days','required_qty':'required_kg',
 'offer_price':'offer_price_per_kg','Check / சோதனை':'Check','Count / எண்ணிக்கை':'Count'}
SCHEMA_EXTRA = {
 'buyer_gross_revenue':'Buyer gross revenue (₹)', 'buyer_transport_cost':'Buyer transport charged (₹)',
 'market_gross_reference':'Market gross reference (₹)', 'difference_vs_market_gross_reference':'Difference versus gross reference (₹)',
 'calculation':'Calculation', 'opportunity_origin':'Origin', 'order_status':'Order status',
 'allocation_rule':'Allocation order', 'view_crop':'Crop', 'filename':'File', 'kind':'Dataset type',
 'origin':'Origin','sha256':'Source identifier','validated_at_utc':'Validated at','rows':'Records',
 'mapping':'Column mapping','quality':'Quality summary','demand_source':'Demand source',
 'input_rows':'Input records','valid_rows':'Valid records','invalid_rows':'Invalid records',
 'not_assessed_rows':'Unassessed records','duplicate_rows':'Duplicate records','missing_cells':'Missing cells',
 'high_surplus_ratio':'Large surplus threshold (%)','age_review_days':'Harvest age review threshold (days)',
 'policy_high_surplus_ratio':'Large surplus threshold (%)','policy_age_review_days':'Harvest age review threshold (days)',
 'policy_scope':'Planning scope','ranking_scope':'Ranking scope', 'scope':'Scope', 'totals':'Totals',
 'market_transport':'Market transport','market_transport_scenario':'Optional market transport scenario',
 'assumed_market_transport_quote':'Assumed total market transport (₹)','applied_market_transport':'Applied market transport',
 'market_return_after_assumed_transport':'Market return after assumed transport (₹)',
 'difference_vs_market_after_assumed_transport':'Buyer difference versus market scenario (₹)',
 'profit':'Profit availability','unmatched_reference':'Unmatched reference status','currency':'Currency',
 'rounding':'Currency rounding','agriculture_metadata':'Agriculture source','buyer_metadata':'Buyer source',
 'agriculture':'Agriculture','buyers':'Buyers','confirmation':'Order status','buyer_order_status':'Order status',
 'allocation_rule':'Allocation order', 'sources':'Calculation sources','question':'Question','answer':'Answer',
 'intent':'Question type','evidence':'Evidence from active calculations'}
LABELS.update({
 'Order status':'ஆர்டர் நிலை','Allocation order':'ஒதுக்கீட்டு வரிசை','Source identifier':'மூல அடையாள எண்',
 'Demand source':'தேவையின் மூலம்','Planning scope':'திட்டமிடும் வரம்பு','Ranking scope':'முன்னுரிமை வரம்பு',
 'Scope':'வரம்பு','Totals':'மொத்தக் கணக்குகள்','Market transport':'சந்தைப் போக்குவரத்து',
 'Applied market transport':'கணக்கிட்ட சந்தைப் போக்குவரத்து','Profit availability':'லாபக் கணக்கீடு கிடைக்குமா',
 'Unmatched reference status':'பொருந்தாத உபரிக் குறிப்பு நிலை','Currency':'பண அலகு','Currency rounding':'பண மதிப்பு முழுமையாக்கம்',
 'Question type':'கேள்வி வகை', 'not_confirmed':'உறுதிப்படுத்தப்படவில்லை', 'csv_source_order':'மூலக் கோப்பின் வரிசை',
 'unknown':'தெரியவில்லை','uploaded':'பதிவேற்றப்பட்டது','sample':'மாதிரி','all_crops':'அனைத்துப் பயிர்கள்',
 'uploaded_estimate':'பதிவேற்றிய மதிப்பீடு','none':'இல்லை','INR':'ரூபாய்',
 'planning_only_not_spoilage_prediction':'திட்டமிடல் மட்டும்; அழுகல் முன்னறிவிப்பு அல்ல',
 'full_active_agriculture_dataset':'முழு நடப்பு வேளாண் தரவு',
 'all_active_buyers_before_view_filter':'காட்சி வடிகட்டிக்கு முன் அனைத்து நடப்பு வாங்குபவர்கள்',
 'user_assumption':'பயனர் அனுமானம்', 'not_calculable_production_and_other_costs_unknown':'உற்பத்தி மற்றும் பிற செலவுகள் தெரியாததால் கணக்கிட முடியாது',
 'separate_not_revenue':'தனிக் குறிப்பு; வருவாய் அல்ல',
 'gross lines and charged costs to paise using decimal ROUND_HALF_UP, then subtract; totals sum rounded lines':'மொத்த வருவாய் மற்றும் செலவை பைசாவிற்கு முழுமையாக்கிக் கழிக்கவும்; பின்னர் கூட்டவும்',
 'Select a value':'ஒரு மதிப்பைத் தேர்ந்தெடுக்கவும்','Choose options':'விருப்பங்களைத் தேர்ந்தெடுக்கவும்',
 'Money inputs must be finite, numeric and non-negative.':'பண உள்ளீடுகள் வரையறுக்கப்பட்ட பூஜ்ஜியம் அல்லது நேர்மறை எண்களாக இருக்க வேண்டும்.',
})
# Correct the inherited mixed unit caption in both languages.
_UNIT='kg · ₹/kg · days / நாட்கள். Transport is ₹ per buyer trip / போக்குவரத்து ₹ ஒரு பயணத்திற்கு.'
LABELS[_UNIT]='கிலோ · ₹/கிலோ · நாட்கள். போக்குவரத்து: ஒரு பயணத்திற்கான ரூபாய்.'
from .i18n import PAIRED
PAIRED[_UNIT]=('kg · ₹/kg · days. Transport is ₹ per buyer trip.',LABELS[_UNIT])


def current():
    return Translator(native.session_state.get('language','English')).configure(native.session_state.get('active_data'),native.session_state.get('active_buyers'))


def error_text(error,t):
    text=str(error)
    if t.language=='English':
        return re.split(r' / [\u0b80-\u0bff]',text)[0]
    if 'finite range' in text: return t('Calculated currency exceeds the supported finite range.')
    if 'snapshot' in text.lower() or 'restore' in text.lower() or 'save' in text.lower(): return t('Unable to save or restore the local snapshot.')
    if 'threshold' in text or 'policy' in text or 'percentage' in text: return t('Invalid planning thresholds; use a positive age and a percentage above zero and at most 100.')
    if 'Duplicate crop' in text: return t('Duplicate crop or buyer/crop identities are not allowed.')
    if 'Map every' in text or 'Each source' in text: return t('Select every required field using distinct source columns.')
    match=re.match(r'(\w+): (\d+) value',text)
    if match:
        return f'{t(match[1])}: {match[2]}. '+t('Values must be finite, numeric and non-negative.')
    if text in LABELS: return t(text)
    return t('Input error; check the file structure and selected columns.')


def clean_text(text,t):
    text=str(text)
    if t.language=='English':
        if not TAMIL.search(text):return text
        return label(text,'English')
    if not LATIN.search(text):return text
    if text in LABELS:return t(text)
    raise KeyError(f'Missing Tamil UI translation: {text}')


def canonical_column(name):
    text=str(name)
    for key,value in LABELS.items():
        if text==value and (key in set(COLUMN_ALIASES.values())|set(SCHEMA_EXTRA)|{'crop','buyer_name','buyer_type','reason','status','value','column','issue'} or re.fullmatch(r'[a-z][a-z_0-9]+',key)):
            return key
    for key,value in SCHEMA_EXTRA.items():
        if text==value:return key
    return COLUMN_ALIASES.get(text,text)


def localized_frame(frame,t):
    result=frame.copy()
    original=list(result.columns)
    canonical=[canonical_column(c) for c in original]
    for pos,col in enumerate(original):
        key=canonical[pos]
        converted=[]
        for i,value in enumerate(result[col]):
            if pd.isna(value):converted.append('—');continue
            if isinstance(value,(bool,)) or str(type(value)).find('bool')>=0:
                converted.append(t('Yes' if value else 'No'));continue
            if not isinstance(value,str):converted.append(value);continue
            if key=='reason':
                row={canonical[j]:frame.iloc[i,j] for j in range(len(original))}
                if 'surplus_before_kg' in row:
                    converted.append(audit_reason(row,t));continue
                if 'available_kg' in row:
                    converted.append(risk_reason(row,t));continue
            if key=='calculation':
                text=value.replace(' kg',' கிலோ').replace('/kg','/கிலோ').replace(' transport',' போக்குவரத்து') if t.language=='தமிழ்' else value
                converted.append(text);continue
            if key in ('crop','buyer_name'):
                converted.append(t.entity(value,'Crop' if key=='crop' else 'Buyer',i+1));continue
            if key=='column':
                try:converted.append(t(COLUMN_ALIASES.get(value,value)))
                except KeyError:converted.append(t('Source column {n}',n=i+1))
                continue
            if key in ('issue','reason'):
                value=value.split(' / ')[0]
                if 'Finite non-negative' in value:value='Values must be finite, numeric and non-negative.'
            if t.language=='English':
                converted.append(clean_text(value,t) if TAMIL.search(value) and value in LABELS else t.entity(value,'Text',i+1))
            elif value in LABELS:converted.append(t(value))
            elif re.fullmatch(r'[0-9.,+−%₹:/\s-]*',value):converted.append(value)
            else:converted.append(t.entity(value,'Text',i+1))
        result[col]=converted
    if t.language=='தமிழ்':
        names=[]
        for i,col in enumerate(canonical):
            key=SCHEMA_EXTRA.get(col,col)
            try:names.append(t(key))
            except KeyError:names.append(t('Source column {n}',n=i+1))
        result.columns=names
    elif any(TAMIL.search(str(col)) for col in original):
        result.columns=[canonical[i] if not TAMIL.search(canonical[i]) else f'Column {i+1}' for i in range(len(original))]
    return result


def risk_reason(row,t):
    if hasattr(row,'_asdict'):row=row._asdict()
    base=t('Available {available} kg − estimated demand {demand} kg gives {surplus} kg potential surplus and {shortage} kg shortage.',
           available=f"{row['available_kg']:g}",demand=f"{row['estimated_demand_kg']:g}",surplus=f"{row['potential_surplus_kg']:g}",shortage=f"{row['shortage_kg']:g}")
    if 'review_score' in row:
        level=str(row['review_level'])
        if level in REVERSE:level=REVERSE[level]
        base+=' '+t('Surplus share {ratio}%; review score {score}/2; level {level}.',ratio=f"{float(str(row['surplus_ratio']).rstrip('%')) if isinstance(row['surplus_ratio'],str) else row['surplus_ratio']*100:.2f}",score=row['review_score'],level=t(level))
    return base


def audit_reason(row,t):
    status=row['status']
    if status in REVERSE:status=REVERSE[status]
    if row['matched_kg']>0:
        return t('Remaining surplus {before} kg; request {request} kg; potential match {matched} kg; remaining {after} kg.',before=f"{row['surplus_before_kg']:g}",request=f"{row['required_kg']:g}",matched=f"{row['matched_kg']:g}",after=f"{row['surplus_after_kg']:g}")
    return t({'Crop unavailable':'Unknown crop; no surplus can be allocated.','Zero request':'Buyer request is zero; no allocation or trip is assumed.','No surplus':'No positive crop surplus is available.','Surplus exhausted':'Earlier buyer rows consumed this crop surplus.'}.get(status,'No allocations'))


def local_json(value,t,key=''):
    if isinstance(value,dict):
        if key=='mapping':
            out={}
            for n,(target,source) in enumerate(value.items(),1):
                try: name=t(target)
                except KeyError: name=t('Source column {n}',n=n)
                source=COLUMN_ALIASES.get(str(source),str(source))
                out[name]=t(source) if source in LABELS else t.entity(source,'Source column',n)
            return out
        out={}
        for n,(k,v) in enumerate(value.items(),1):
            try: name=t(SCHEMA_EXTRA.get(k,k))
            except KeyError:name=t('Source column {n}',n=n)
            out[name]=local_json(v,t,k)
        return out
    if isinstance(value,list):return [local_json(v,t,key) for v in value]
    if isinstance(value,str):
        if key=='sha256':return str(int(value,16))
        if key=='validated_at_utc':return value.replace('T',' ').replace('Z','')
        if key=='filename':return t.entity(value,'Source file')
        kind = 'Crop' if key in ('scope','view_crop','crop') else 'Text'
        return t.entity(value,kind) if value not in LABELS else t(value)
    return value


class Proxy:
    def __init__(self,target):self.target=target
    @property
    def sidebar(self):return Proxy(self.target.sidebar)
    def __getattr__(self,name):
        original=getattr(self.target,name)
        if name in ('title','header','subheader','caption','write','info','warning','error','success','expander','button','form_submit_button','checkbox','number_input','text_input','text_area','chat_input'):
            def render(*args,**kwargs):
                t=current()
                if args and isinstance(args[0],str):
                    text=error_text(args[0],t) if name=='error' else clean_text(args[0],t)
                    args=(text,*args[1:])
                if 'placeholder' in kwargs:kwargs['placeholder']=clean_text(kwargs['placeholder'],t)
                return original(*args,**kwargs)
            return render
        if name=='date_input':
            def date_field(label,*args,**kwargs):
                from datetime import date
                t=current();base=kwargs.pop('key','date_field')
                value=kwargs.pop('value',args[0] if args else date.today())
                if t.language=='தமிழ்':
                    raw=native.text_input(clean_text(label,t),value=str(value),key=base+'__date_ta',placeholder='2026-10-15')
                    try:parsed=date.fromisoformat(raw)
                    except (TypeError,ValueError):
                        native.error(t('Enter a valid date in year-month-day format.'));return None
                else:parsed=original(clean_text(label,t),value=value,key=base+'__date_en',**kwargs)
                return parsed
            return date_field
        if name in ('selectbox','multiselect','radio'):
            def select(*args,**kwargs):
                t=current()
                if args:args=(clean_text(args[0],t),*args[1:])
                fmt=kwargs.pop('format_func',str)
                options=list(args[1]) if len(args)>1 else list(kwargs['options'])
                def display(value):
                    result=fmt(value)
                    if str(kwargs.get('key','')).startswith('map_') and result in COLUMN_ALIASES and t.language=='தமிழ்':
                        return t(COLUMN_ALIASES[result])
                    if result in LABELS or (t.language=='தமிழ்' and not LATIN.search(str(result))) or (t.language=='English' and not TAMIL.search(str(result))):return clean_text(result,t)
                    return t.entity(result,'Source column' if str(kwargs.get('key','')).startswith('map_') else 'Crop', options.index(value)+1)
                kwargs['format_func']=display
                base_key=kwargs.get('key')
                bridge=bool(base_key and not str(base_key).startswith('language_'))
                if bridge:
                    # Streamlit serializes formatted strings. Remount per locale, while
                    # keeping canonical selection state separate from widget state.
                    kwargs['key']=f'{base_key}__ui_{t.language}'
                    saved=native.session_state.get(base_key)
                    locale_key=f'{base_key}__display_locale'
                    if native.session_state.get(locale_key)!=t.language:
                        if base_key in native.session_state and (isinstance(saved,list) if name=='multiselect' else saved in options):
                            native.session_state[kwargs['key']]=saved
                        native.session_state[locale_key]=t.language
                    if name=='multiselect':
                        if isinstance(saved,list):kwargs['default']=[v for v in saved if v in options]
                    elif base_key in native.session_state and saved in options:
                        kwargs['index']=options.index(saved)
                if name in ('multiselect','selectbox'):
                    kwargs.setdefault('placeholder',t('Choose options' if name=='multiselect' else 'Select a value'))
                value=original(*args,**kwargs)
                if bridge:native.session_state[base_key]=value
                return value
            return select
        if name=='dataframe':
            def table(data,*args,**kwargs):
                t=current()
                if t.language=='தமிழ்' and len(data)>50:
                    number=native.session_state.get('_locale_table_counter',0)
                    native.session_state['_locale_table_counter']=number+1
                    fingerprint=hashlib.sha256((str(list(data.columns))+str(len(data))+data.head(1).to_json()).encode()).hexdigest()[:12]
                    pages=(len(data)+49)//50
                    page=native.selectbox(t('Table page'),list(range(1,pages+1)),format_func=lambda n:t('Page {n} of {pages}',n=n,pages=pages),key=f'locale_table_{fingerprint}_{number}')
                    start=(page-1)*50
                    native.caption(t('Showing records {first}–{last} of {total}.',first=start+1,last=min(start+50,len(data)),total=len(data)))
                    data=data.iloc[start:start+50]
                frame=localized_frame(data,t)
                if t.language=='தமிழ்':return native.table(frame.astype(str))
                return original(frame,*args,**kwargs)
            return table
        if name=='plotly_chart':
            def chart(fig,*args,**kwargs):
                t=current()
                for trace in fig.data:
                    if trace.x is not None:
                        trace.x=[t.entity(x,'Crop',i+1) if isinstance(x,str) else x for i,x in enumerate(trace.x)]
                    if trace.name:trace.name=clean_text(trace.name,t)
                    unit='₹' if fig.layout.yaxis.title.text=='₹' else t('Quantity (kg)')
                    trace.hovertemplate='%{x}<br>'+unit+': %{y}<extra></extra>'
                    trace.customdata=None
                fig.update_layout(paper_bgcolor='#FFFFFF',plot_bgcolor='#FFFFFF',font={'color':'#152D43'},
                                  legend={'font':{'color':'#52677A'}},hoverlabel={'bgcolor':'#0B2540','font_color':'#FFFFFF'})
                fig.update_yaxes(gridcolor='#E4EBF2',zerolinecolor='#DCE5ED')
                kwargs['config']={'displayModeBar':False,'responsive':True}
                return original(fig,*args,**kwargs)
            return chart
        if name=='download_button':
            def download(*args,**kwargs):
                t=current(); args=list(args)
                if args:args[0]=clean_text(args[0],t)
                data=args[1] if len(args)>1 else kwargs.get('data')
                filename=kwargs.get('file_name','report.txt')
                if isinstance(data,bytes):
                    if filename.endswith('.csv'):
                        try:data=localized_frame(pd.read_csv(BytesIO(data)),t).to_csv(index=False).encode('utf-8-sig')
                        except pd.errors.EmptyDataError:pass
                    elif filename.endswith('.json'):
                        data=json.dumps(local_json(json.loads(data),t),ensure_ascii=False,indent=2).encode()
                if len(args)>1:args[1]=data
                else:kwargs['data']=data
                if t.language=='தமிழ்':kwargs['file_name']='அறிக்கை.'+filename.rsplit('.',1)[-1]
                return original(*args,**kwargs)
            return download
        if name=='file_uploader':
            def upload(*args,**kwargs):
                t=current()
                if t.language=='English':return original(clean_text(args[0],t),*args[1:],**kwargs)
                native.write(clean_text(args[0],t))
                result=_tamil_upload(key=kwargs.get('key','upload'),default=None,accept=','.join('.'+v for v in kwargs.get('type',['csv'])))
                if not result:return None
                try:
                    content=base64.b64decode(result['content'],validate=True)
                    if len(content)>10*1024*1024:raise ValueError('size')
                except Exception:
                    native.error(t('Input error; check the file structure and selected columns.'));return None
                return Uploaded(result.get('name','source.csv'),content)
            return upload
        return original

class Uploaded:
    def __init__(self,name,data):self.name=name;self.data=data
    def getvalue(self):return self.data

_locale_chrome=components.declare_component('locale_chrome',path=str(Path(__file__).parent/'locale_chrome'))
_tamil_upload=components.declare_component('tamil_csv_upload',path=str(Path(__file__).parent/'tamil_upload'))
st=Proxy(native)


def setup_locale():
    native.session_state['_locale_table_counter']=0
    _locale_chrome(language=current().language,key='native_locale_chrome',default=None)
    if current().language=='தமிழ்':
        native.markdown('''<style>
        @font-face {font-family:HarvestTamil;src:url('/app/static/fonts/noto-sans-tamil-tamil-400-normal.woff2');font-weight:400;font-display:swap;unicode-range:U+0B80-0BFF,U+200C-200D,U+20B9,U+25CC;}
        @font-face {font-family:HarvestTamil;src:url('/app/static/fonts/noto-sans-tamil-tamil-700-normal.woff2');font-weight:700;font-display:swap;unicode-range:U+0B80-0BFF,U+200C-200D,U+20B9,U+25CC;}
        @font-face {font-family:HarvestTamil;src:url('/app/static/fonts/noto-sans-tamil-latin-400-normal.woff2');font-weight:400;font-display:swap;unicode-range:U+0000-00FF;}
        @font-face {font-family:HarvestTamil;src:url('/app/static/fonts/noto-sans-tamil-latin-700-normal.woff2');font-weight:700;font-display:swap;unicode-range:U+0000-00FF;}
        [data-testid="stAppViewContainer"] p,[data-testid="stAppViewContainer"] h1,[data-testid="stAppViewContainer"] h2,[data-testid="stAppViewContainer"] h3,[data-testid="stAppViewContainer"] label,[data-testid="stAppViewContainer"] button,[data-testid="stAppViewContainer"] input,[data-testid="stAppViewContainer"] textarea,.stTable {font-family:HarvestTamil,sans-serif !important;}
        .brand-name,.workspace-bar,.guide-card,.business-hero,.onboarding-card,.decision-card,[data-testid="stPlotlyChart"] text, [role="option"], [role="option"] div, [data-testid="stAppViewContainer"] span:not([data-testid="stIconMaterial"]) {font-family:HarvestTamil,sans-serif !important;}
        [data-testid="stElementToolbar"], [role="tooltip"] {display:none !important;}
        </style>''',unsafe_allow_html=True)
    t=current()
    native.markdown(f'<a class="skip-link" href="#main-content">{t("Skip to main content")}</a><span id="main-content" tabindex="-1"></span>',unsafe_allow_html=True)
    native.markdown('''<style>
    [data-testid="stToolbarActions"], [data-testid="stAppDeployButton"], [data-testid="stMainMenu"], [data-testid="stSkipToContent"], footer, [data-testid="InputInstructions"] {display:none !important;}
    :root {scroll-padding-top:4rem;}
    .sidebar-brand {font-size:1.4rem;font-weight:700;}
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {color:#425649 !important;opacity:1 !important;}
    h1,h2,h3 {text-wrap:balance;scroll-margin-top:4rem;overflow-wrap:anywhere;max-width:100%;}
    [data-testid="stHeading"] {min-width:0;max-width:100%;}
    [data-testid="stHeading"] h1 {font-size:clamp(1.8rem,3.5vw,2.75rem);}
    button, a, input, select, textarea {touch-action:manipulation;}
    [tabindex]:focus-visible,button:focus-visible,a:focus-visible,input:focus-visible,textarea:focus-visible {outline:3px solid #1e40af !important;outline-offset:3px;}
    [data-testid="stMetric"] {font-variant-numeric:tabular-nums;min-width:0;}
    [data-testid="stMetricLabel"] {white-space:normal;overflow-wrap:anywhere;}
    [data-testid="stMarkdownContainer"] p {overflow-wrap:anywhere;}
    [data-testid="stFileUploaderDropzoneInstructions"] * {color:#425649 !important;opacity:1 !important;}
    .stTable th,.stTable th p,.stTable th div {color:#425649 !important;opacity:1 !important;}
    .stTable {overflow-x:auto;max-width:100%;} .stTable th,.stTable td {min-width:80px;}
    .skip-link {position:fixed;left:1rem;top:0;transform:translateY(-200%);z-index:10000;background:#fff;padding:1rem;color:#1e40af;}
    .skip-link:focus {top:1rem;transform:translateY(0);}
    @media (max-width:640px) {
       [data-testid="stMainBlockContainer"] {padding:1rem 1rem max(2rem,env(safe-area-inset-bottom));}
       [data-testid="stMetricValue"] {font-size:1.6rem;}
    }
    @media (prefers-reduced-motion:reduce) {* {scroll-behavior:auto !important;animation-duration:0.01ms !important;transition-duration:0.01ms !important;}}
    </style>''',unsafe_allow_html=True)

# Schema identifiers and human labels share the same Tamil translation.
for _field,_english in SCHEMA_EXTRA.items():
    if _english in LABELS:
        LABELS.setdefault(_field,LABELS[_english])
