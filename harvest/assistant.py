"""Deterministic question routing and calculation-grounded answers. No network/model calls."""
from dataclasses import dataclass, field
import re
import pandas as pd
from .analytics import calculate_kpis, crop_balances
from .risk import RiskPolicy, analyse_risk, prioritise_crop
from .matching import matching_preview
from .financials import analyse_financials, financial_totals

@dataclass
class AssistantAnswer:
    intent: str
    parts: list = field(default_factory=list)   # (translation key, numeric/identity arguments)
    evidence: pd.DataFrame = field(default_factory=pd.DataFrame)
    sources: list[str] = field(default_factory=list)
    crop: str | None = None


PROMPTS = {'priority':'Which crop should I prioritise?', 'overview':'Show surplus and shortages',
           'matching':'Explain the buyer matches', 'financial':'Explain the returns after transport',
           'risk':'Explain the risk rules', 'unsupported':'Ask a question about the active data'}


def route_question(question):
    q = question.strip().casefold()
    if any(term in q for term in ['real-time','real time','live price','weather','forecast','today','confirmed order',
                                  'இன்றைய','நேரடி','வானிலை','முன்னறிவிப்பு','உறுதியான ஆர்டர்']):
        return 'unsupported'
    for intent,terms in [('priority',['prioritis','prioritiz','priority','first crop','which crop should','sell first','முன்னுரிமை','முதலில்']),
                         ('risk',['risk','review rule','threshold','spoil','அபாய','வரம்பு','அழுக']),
                         ('financial',['return','profit','transport','revenue','financial','compare','earn','வருவாய்','லாப','போக்குவரத்து','ஒப்பிட']),
                         ('matching',['buyer','who can buy','will buy','sell to','match','unmatched','வாங்குபவர்','பொருத்த']),
                         ('overview',['surplus','shortage','available','demand','summary','உபரி','பற்றாக்குறை','இருப்பு','தேவை','சுருக்க'])]:
        if any(term in q for term in terms):return intent
    return 'unsupported'


def resolve_crop(question,data,scope=None):
    aliases={'tomatoes':['tomato','tomatoes','தக்காளி'], 'onions':['onion','onions','வெங்காயம்'], 'carrots':['carrot','carrots','கேரட்']}
    q=question.casefold()
    found=[]
    for crop in data.crop:
        names=[crop.casefold()]
        for group in aliases.values():
            if crop.casefold() in group:names=group;break
        if any(re.search(r'(?<!\w)'+re.escape(name)+r'(?!\w)',q) for name in names):found.append(crop)
    if len(found)==1:return found[0]
    if len(found)>1:return None
    unknown = re.search(r'\b(?:for|about)\s+([a-z]+)\b',q)
    if unknown and unknown.group(1) not in ['the','my','all','crop','active','surplus','transport','buyer','returns']:
        return unknown.group(1)
    if scope is not None:
        return next((crop for crop in data.crop if crop.casefold()==scope.casefold()),scope)
    return None


def answer_question(question,data=None,buyers=None,policy=None,crop=None):
    """All numbers come from existing functions and the current validated dataset."""
    intent=route_question(str(question)[:2000])
    result=AssistantAnswer(intent)
    if data is None:
        result.parts=[('Load validated agriculture data before asking the assistant.',{})]
        return result
    if intent=='unsupported':
        result.parts=[('I can explain priorities, surplus, shortages, review rules, buyer matches and estimated returns from active data.',{}),
                      ('No live prices, weather, automatic orders or actual profit are available in this planning view. Open History and Forecasts for recorded model forecasts.',{})]
        return result
    try:
        policy=RiskPolicy() if policy is None else policy
        balances=crop_balances(data)
        selected=resolve_crop(str(question),data,crop)
        if selected is not None and selected not in list(balances.crop):
            result.parts=[('This crop is not in the active agriculture dataset.',{})];return result
        result.crop=selected
        if intent=='priority':
            recommended=prioritise_crop(data,policy)
            result.sources=['Priority and risk calculations']
            result.evidence=analyse_risk(data,policy)
            if recommended is None:
                result.parts=[('No positive surplus; no crop prioritised for surplus selling',{})];return result
            selected=recommended['crop']; result.crop=selected
            row=balances.loc[balances.crop==selected].iloc[0]
            result.parts=[('Prioritise {crop} for surplus-selling review: {surplus} kg potential surplus.',{'crop':selected,'surplus':row.potential_surplus_kg}),
                          ('Available {available} kg − estimated demand {demand} kg gives {surplus} kg potential surplus and {shortage} kg shortage.',
                           {'available':row.available_kg,'demand':row.estimated_demand_kg,'surplus':row.potential_surplus_kg,'shortage':row.shortage_kg}),
                          ('Rank uses largest positive surplus, then older harvest, then crop name; it is not a perishability or profit forecast.',{})]
        elif intent=='risk':
            report=analyse_risk(data,policy)
            result.evidence=report if selected is None else report.loc[report.crop==selected]
            result.sources=['Priority and risk calculations']
            result.parts=[('Large-surplus threshold: {ratio}%; harvest-age review threshold: {days} days.',{'ratio':policy.high_surplus_ratio*100,'days':policy.age_review_days}),
                          ('Planning signals only; not measured spoilage or shelf life',{}),
                          ('For surplus crops: review score = large-surplus flag + age-review flag. 0 = Low; 1 = Moderate; 2 = High. Crops without surplus show No surplus, with age review shown independently.',{})]
            return result
        elif intent=='overview':
            selected_data=data if selected is None else data.loc[data.crop==selected]
            kpis=calculate_kpis(selected_data)
            result.evidence=crop_balances(selected_data);result.sources=['Overview calculations']
            result.parts=[('Surplus {surplus} kg and shortages {shortage} kg are summed separately.',{'surplus':kpis['positive_surplus_kg'],'shortage':kpis['shortage_kg']})]
            return result
        if buyers is None:
            result.parts.append(('Buyer data is not active; load buyer opportunities to calculate matches and returns.',{}));return result
        if intent in ('priority','matching'):
            _,matched,audit=matching_preview(data,buyers)
            selected_rows=matched if selected is None else matched.loc[matched.crop==selected]
            for row in selected_rows.itertuples():
                result.parts.append(('{crop}: {matched} kg potentially matched; {unmatched} kg still unmatched.',
                                     {'crop':row.crop,'matched':row.matched_kg,'unmatched':row.unmatched_kg}))
            result.sources.append('Buyer allocation calculations')
            if intent=='matching':
                result.evidence=audit if selected is None else audit.loc[audit.crop.str.casefold()==selected.casefold()]
                result.parts.append(('Buyer rows are processed once in CSV source order; earlier rows get surplus first',{}))
        report=analyse_financials(data,buyers)
        selected_finance=report.crops if selected is None else report.crops.loc[report.crops.crop==selected]
        totals=financial_totals(selected_finance)
        result.sources.append('Financial calculations')
        result.parts.append(('Combined estimated return after buyer transport: ₹{amount}.',{'amount':totals['estimated_return_after_transport']}))
        if intent=='financial':
            result.evidence=report.buyers if selected is None else report.buyers.loc[report.buyers.crop.str.casefold()==selected.casefold()]
            result.parts += [('Buyer gross ₹{gross} − transport ₹{transport} = estimated return ₹{result}.',
                              {'gross':totals['buyer_gross_revenue'],'transport':totals['buyer_transport_cost'],'result':totals['estimated_return_after_transport']}),
                            ('Same matched quantity market reference: ₹{reference}, before unknown market transport and other costs.',{'reference':totals['market_gross_reference']})]
        result.parts += [('Returns after transport are estimates, not profit; production and other costs are unknown',{}),
                         ('Preview only: no stock reserved, no buyer contacted, no order created',{})]
        return result
    except ValueError:
        result.parts.append(('Input error; check the file structure and selected columns.',{}))
        return result


def render_parts(answer,t):
    lines=[]
    money_keys={'amount','gross','transport','result','reference'}
    for key,values in answer.parts:
        display={}
        for field,value in values.items():
            if field=='crop':display[field]=t.entity(value,'Crop')
            elif isinstance(value,(int,float)) or hasattr(value,'item'):
                display[field]=f'{value:,.2f}' if field in money_keys else f'{value:g}'
            else:display[field]=value
        lines.append(t(key,**display))
    return lines
