"""Business record forms and revision history; pure operations live in business.py."""
import sqlite3
import pandas as pd
from .locale_ui import st
from .business import (KEYS,change_record,apply_records,list_versions,load_version,
                       current_revision,save_version,fingerprint,workspace_backup,RevisionConflict)
from .views import number


FORM_LABELS={'crop':'Crop','buyer_name':'Buyer name','buyer_type':'Buyer type','available_kg':'Available (kg)',
 'estimated_demand_kg':'Estimated demand (kg)','market_price_per_kg':'Market price (₹/kg)',
 'harvest_age_days':'Harvest age (days)','required_kg':'Required quantity (kg)',
 'offer_price_per_kg':'Offer price (₹/kg)','transport_cost':'Transport cost (₹)'}

def restore_into_session(state,restored,path):
    for key in ['report_agriculture','report_buyers','risk_threshold_pct','risk_age_days']:
        state.pop(key,None)
    state.update(restored)
    state['_base_revision']=current_revision(path)
    state['_saved_fingerprint']=fingerprint(state)
    state['_records_changed']=False


def persist(state,path,label):
    revision=save_version(state,path,label,state.get('_base_revision',0))
    state['_base_revision']=revision
    state['_saved_fingerprint']=fingerprint(state)
    state['_records_changed']=False
    return revision


def record_editor(t,kind):
    frame=st.session_state.get(KEYS[kind])
    actions=['Add record','Edit record','Delete record']
    action=st.selectbox(t('Record action'),actions,format_func=t,key='record_action_'+kind)
    selected=None
    if action!='Add record':
        if frame is None or frame.empty:
            st.info(t('No records to edit or remove. Add a record first.'));return
        def name(i):
            row=frame.iloc[i]
            crop=t.entity(row['crop'],'Crop',i+1)
            return crop if kind=='agriculture' else t.entity(row['buyer_name'],'Buyer',i+1)+' · '+crop
        selected=st.selectbox(t('Select record'),list(range(len(frame))),format_func=name,key='record_selected_'+kind)
    row=frame.iloc[selected].to_dict() if selected is not None else {}
    if action=='Delete record':
        st.warning(t('Only the selected record is changed. Buyer rows retain their allocation order.'))
        confirmed=st.checkbox(t('I understand this removes the selected active record.'),key='record_delete_confirm_'+kind)
        if st.button(t('Remove selected record'),key='delete_record_'+kind,disabled=not confirmed):
            apply_records(st.session_state,change_record(frame,kind,index=int(selected),delete=True),kind)
            st.session_state['_business_flash']=True;st.rerun()
        return
    edit=selected is not None
    if edit:
        st.caption(t('Names identify records and cannot be changed in the edit form.'))
    form_key=f'record_form_{kind}_{action}_{selected}_{len(frame) if frame is not None else 0}'
    values={}
    with st.form(form_key):
        if kind=='agriculture':
            values['crop']=row['crop'] if edit else st.text_input(t('Crop'),key=form_key+'_crop',max_chars=100)
            fields=['available_kg','estimated_demand_kg','market_price_per_kg','harvest_age_days']
        else:
            values['buyer_name']=row['buyer_name'] if edit else st.text_input(t('Buyer name'),key=form_key+'_buyer',max_chars=150)
            values['buyer_type']=row['buyer_type'] if edit else st.selectbox(t('Buyer type'),['Retailer','Restaurant','Hostel','Other'],format_func=t,key=form_key+'_type')
            if edit:values['crop']=row['crop']
            else:
                agriculture=st.session_state.get('active_data')
                crops=list(agriculture.crop) if agriculture is not None else []
                if crops:
                    values['crop']=st.selectbox(t('Buyer crop'),crops,key=form_key+'_crop')
                else:values['crop']=st.text_input(t('Crop'),key=form_key+'_crop',max_chars=100)
            fields=['required_kg','offer_price_per_kg','transport_cost']
        for offset in range(0,len(fields),2):
            for col,field in zip(st.columns(2),fields[offset:offset+2]):
                values[field]=col.number_input(t(FORM_LABELS[field]),min_value=0.0,value=float(row.get(field,0)),step=1.0,key=form_key+'_'+field)
        submitted=st.form_submit_button(t('Save record'),key='save_record_'+kind,type='primary')
    if submitted:
        try:
            if not edit and frame is not None and len(frame)>=50000:
                st.error(t('Record limit reached. Use a smaller dataset.'));return
            changed=change_record(frame,kind,values,index=int(selected) if edit else None)
            apply_records(st.session_state,changed,kind)
            st.session_state['_business_flash']=True;st.rerun()
        except ValueError:
            st.error(t('Check required names and non-negative numeric values. Duplicate crop or buyer-crop records are not allowed.'))
    if frame is not None:
        query=st.text_input(t('Find crop or buyer'),key='record_search_'+kind,max_chars=100).strip().casefold()
        shown=frame.copy()
        if query:
            names=[t.entity(row['crop'],'Crop',i+1)+((' '+t.entity(row['buyer_name'],'Buyer',i+1)) if kind=='buyers' else '') for i,(_,row) in enumerate(frame.iterrows())]
            shown=frame.loc[[query in value.casefold() for value in names]]
        if shown.empty:st.info(t('No matching records'))
        else:st.dataframe(shown.rename(columns=lambda name:t(FORM_LABELS.get(name,name))),hide_index=True,width='stretch')


def version_panel(t,path):
    st.caption(t('Saved versions preserve both datasets and the applied planning rules.'))
    active=st.session_state.get('active_data') is not None or st.session_state.get('active_buyers') is not None
    with st.form('save_workspace_version_form'):
        name=st.text_input(t('Version name'),max_chars=100,key='version_name')
        saved=st.form_submit_button(t('Save workspace version'),key='save_workspace_version',disabled=not (active or st.session_state.get('_records_changed')),type='primary')
    if saved:
        if not name.strip():st.error(t('Enter a version name of 1 to 100 characters.'))
        else:
            try:
                revision=persist(st.session_state,path,name)
                st.session_state['saved_version']=revision
                st.session_state[f'saved_version__ui_{t.language}']=revision
                st.session_state['_version_saved_flash']=True
                st.rerun()
            except RevisionConflict:st.error(t('Another session saved a newer version. Restore the latest saved workspace before saving again.'))
            except (OSError,sqlite3.Error,ValueError):st.error(t('Could not access workspace storage. Check the configured folder permissions.'))
    try:versions=list_versions(path)
    except (OSError,sqlite3.Error):
        st.error(t('Could not access workspace storage. Check the configured folder permissions.'));return
    if versions:
        labels={v['revision']:t('Version {n}',n=v['revision'])+' · '+t.entity(v['label'],'Text',v['revision']) for v in versions}
        selected=st.selectbox(t('Choose a saved version'),list(labels),format_func=labels.get,key='saved_version')
        st.warning(t('Restore replaces the active datasets and planning rules. Unsaved changes will be lost.'))
        confirm=st.checkbox(t('I want to replace the active workspace with this saved version.'),key='restore_version_confirm')
        if st.button(t('Restore selected version'),key='restore_version',disabled=not confirm):
            try:
                restore_into_session(st.session_state,load_version(path,selected),path)
                st.rerun()
            except (OSError,ValueError,sqlite3.Error):st.error(t('Could not access workspace storage. Check the configured folder permissions.'))
        history=pd.DataFrame([{t('Revision'):v['revision'],t('Saved at'):v['created_at'].replace('T',' ').split('+')[0],t('Name'):t.entity(v['label'],'Text',v['revision'])} for v in versions])
        st.dataframe(history,hide_index=True,width='stretch')
    else:st.info(t('No saved versions yet.'))
    if active:
        st.subheader(t('Portable backup'))
        st.caption(t('Backup contains original identifiers and schemas for lossless recovery. Display reports follow the selected language.'))
        st.download_button(t('Download original data backup'),workspace_backup(st.session_state),file_name='cebafex_workspace.zip',mime='application/zip',key='download_backup')


def business_view(t,path):
    st.caption(t('All calculations use your active validated data.'))
    if st.session_state.pop('_version_saved_flash',False):st.success(t('Workspace version saved.'))
    if st.session_state.pop('_business_flash',False):st.success(t('Records updated. Save the workspace to keep these changes.'))
    agriculture,buyers=st.session_state.get('active_data'),st.session_state.get('active_buyers')
    a,b=st.columns(2)
    a.metric(t('Crop records'),number(len(agriculture) if agriculture is not None else 0))
    b.metric(t('Buyer opportunities'),number(len(buyers) if buyers is not None else 0))
    crops_tab,buyers_tab,versions_tab=st.tabs([t('Crop records'),t('Buyer opportunities'),t('Version history')],key='workspace_tabs_'+t.language,on_change='rerun')
    with crops_tab:
        st.caption(t('Crop quantities and demand are entered estimates, not live measurements.'))
        record_editor(t,'agriculture')
    with buyers_tab:
        st.warning(t('Uploaded opportunities; not confirmed orders'))
        record_editor(t,'buyers')
    with versions_tab:version_panel(t,path)
