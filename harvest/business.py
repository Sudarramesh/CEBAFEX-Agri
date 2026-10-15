"""Validated record management, revisioned SQLite workspaces and portable backups."""
from datetime import datetime, timezone
from io import BytesIO
import hashlib
import json
import sqlite3
import zipfile
from pathlib import Path
import pandas as pd
from .data import ALIASES, BUYER_ALIASES, require_valid
from .risk import RiskPolicy
from .storage import connect

KEYS={'agriculture':'active_data','buyers':'active_buyers'}

class RevisionConflict(ValueError):
    """The saved workspace changed after this session read it."""


def bundle(state):
    result={'schema_version':1,'risk_policy':RiskPolicy.from_dict(state.get('risk_policy')).to_dict(),
            'source':state.get('source','Business records')}
    for kind,key in KEYS.items():
        frame=state.get(key)
        result[key]=json.loads(require_valid(frame,kind).to_json(orient='records')) if frame is not None else None
        result[kind+'_metadata']=state.get(kind+'_metadata')
    return result


def fingerprint(state):
    payload=bundle(state)
    return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def initialise(con):
    con.execute('CREATE TABLE IF NOT EXISTS business_versions (revision INTEGER PRIMARY KEY, created_at TEXT NOT NULL, label TEXT NOT NULL, payload TEXT NOT NULL, digest TEXT NOT NULL)')


def current_revision(path):
    con=connect(path)
    try:
        initialise(con)
        return con.execute('SELECT COALESCE(MAX(revision),0) FROM business_versions').fetchone()[0]
    finally:con.close()


def save_version(state,path,label,expected_revision):
    """One transaction: version history and legacy-compatible latest snapshot."""
    payload=bundle(state)
    label=str(label).strip()
    if not label or len(label)>100:raise ValueError('Invalid version label')
    encoded=json.dumps(payload,ensure_ascii=False,allow_nan=False)
    digest=fingerprint(state)
    con=connect(path)
    try:
        initialise(con)
        con.execute('BEGIN IMMEDIATE')
        revision=con.execute('SELECT COALESCE(MAX(revision),0) FROM business_versions').fetchone()[0]
        if expected_revision!=revision:raise RevisionConflict('Workspace changed in another session')
        revision+=1
        con.execute('INSERT INTO business_versions VALUES (?,?,?,?,?)',
                    (revision,datetime.now(timezone.utc).isoformat(),label,encoded,digest))
        con.execute('CREATE TABLE IF NOT EXISTS workspace_snapshot (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)')
        con.execute('INSERT OR REPLACE INTO workspace_snapshot VALUES (1,?)',(encoded,))
        if payload['active_data'] is not None:
            con.execute('INSERT OR REPLACE INTO active_dataset VALUES (1,?,?)',
                        (json.dumps(payload['active_data']),payload['source']))
        else:con.execute('DELETE FROM active_dataset WHERE id=1')
        con.commit()
        return revision
    except Exception:
        con.rollback();raise
    finally:con.close()


def list_versions(path,limit=100):
    con=connect(path)
    try:
        initialise(con)
        return [{'revision':r,'created_at':created,'label':label} for r,created,label in con.execute(
            'SELECT revision,created_at,label FROM business_versions ORDER BY revision DESC LIMIT ?',
            (max(1,min(int(limit),1000)),)).fetchall()]
    finally:con.close()


def load_version(path,revision):
    con=connect(path)
    try:
        initialise(con)
        row=con.execute('SELECT payload FROM business_versions WHERE revision=?',(int(revision),)).fetchone()
    finally:con.close()
    if not row:raise ValueError('Version not found')
    result=json.loads(row[0])
    result['risk_policy']=RiskPolicy.from_dict(result.get('risk_policy')).to_dict()
    for kind,key in KEYS.items():
        if result[key] is not None:result[key]=require_valid(pd.DataFrame(result[key]),kind)
    return result


def change_record(frame,kind,values=None,index=None,delete=False):
    """Return a new validated dataset; never mutate the active input on failure."""
    if kind not in KEYS:raise ValueError('Unknown dataset kind')
    columns=list(ALIASES if kind=='agriculture' else BUYER_ALIASES)
    current=frame.copy(deep=True).reset_index(drop=True) if frame is not None else pd.DataFrame(columns=columns)
    if index is not None and (not isinstance(index,int) or index<0 or index>=len(current)):
        raise ValueError('Record not found')
    if delete:
        if index is None:raise ValueError('Choose a record')
        current=current.drop(index).reset_index(drop=True)
        return require_valid(current,kind) if len(current) else None
    if values is None or set(values)!=set(columns):raise ValueError('Required fields missing')
    if index is None:
        current=pd.DataFrame([values],columns=columns) if current.empty else pd.concat([current,pd.DataFrame([values])],ignore_index=True)
    else:
        for field in columns:current.loc[index,field]=values[field]
    return require_valid(current,kind)


def apply_records(state,frame,kind):
    key=KEYS[kind]
    state[key]=frame.copy(deep=True) if frame is not None else None
    original=state.get(kind+'_metadata') or {}
    if frame is None:state[kind+'_metadata']=None
    else:
        data=frame.to_csv(index=False).encode('utf-8')
        state[kind+'_metadata']={'kind':kind,'filename':'business_records.csv','origin':'manual',
            'sha256':hashlib.sha256(data).hexdigest(),'rows':len(frame),
            'validated_at_utc':datetime.now(timezone.utc).isoformat(),'mapping':{c:c for c in frame.columns},
            'demand_source':'uploaded_estimate' if kind=='agriculture' else None,
            'previous_sha256':original.get('sha256')}
    if kind=='agriculture':state['source']='Business records'
    state.pop('report_'+kind,None)
    state['_records_changed']=True


def workspace_backup(state):
    payload=bundle(state)
    output=BytesIO()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('workspace.json',json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False))
        for kind,key in KEYS.items():
            if payload[key] is not None:
                archive.writestr(kind+'.csv',pd.DataFrame(payload[key]).to_csv(index=False).encode('utf-8-sig'))
    return output.getvalue()
