from datetime import date,timedelta
from io import BytesIO
import json,math
import pandas as pd
import pytest
from openpyxl import Workbook
from harvest import operations as op
from harvest import forecasting as fc
from harvest.tabular import read_table,interpret_columns,sheets
from harvest.ingestion import prepare_dataset


def history(count=84):
    start=date.today()-timedelta(days=count+8)
    return pd.DataFrame({'date':[str(start+timedelta(days=i)) for i in range(count)],'crop':['Tomatoes']*count,'demand_kg':[120+15*math.sin(2*math.pi*i/7)+i*.1 for i in range(count)],'stockout':[0]*count})


def test_model_temporal_validation_save_and_later_evaluation(tmp_path):
    path=tmp_path/'forecast.db';market=op.registry(path,'markets',{'name':'Market','location':'Town'})
    frame=history();fc.import_history(path,market,frame,source='synthetic_demo')
    run,payload,predictions=fc.train_and_save(path,market,'Tomatoes',7)
    assert payload['heldout_days']>=14 and payload['training_examples']>=21
    assert payload['cutoff']==frame.date.iloc[-1]
    assert all(r['predicted_demand_kg']>=0 for r in predictions)
    assert predictions[0]['date']==str(op.day(payload['cutoff'])+timedelta(days=1))
    saved,rows,mae,count=fc.forecast_report(path,run)
    assert mae is None and count==0
    actual=pd.DataFrame({'date':[p['date'] for p in predictions],'crop':['Tomatoes']*7,'demand_kg':[p['predicted_demand_kg']+5 for p in predictions]})
    fc.import_history(path,market,actual,source='later observations')
    _,_,mae,count=fc.forecast_report(path,run)
    assert count==7 and mae==pytest.approx(5)
    assert fc.forecast_report(path,run)[0]==saved
    copy=path.parent/'full-backup.db';copy.write_bytes(op.database_backup(path))
    copied,_,copied_mae,copied_count=fc.forecast_report(copy,run)
    assert copied==saved and copied_count==7 and copied_mae==pytest.approx(5)
    assert len(fc.historical_series(copy,market,'Tomatoes'))==91
    assert json.dumps(payload,allow_nan=False)


def test_insufficient_gapped_and_censored_history_are_rejected(tmp_path):
    path=tmp_path/'history.db';market=op.registry(path,'markets',{'name':'Market','location':'Town'})
    fc.import_history(path,market,history(20))
    with pytest.raises(op.OperationError):fc.train_and_save(path,market,'Tomatoes')
    frame=history();fc.import_history(path,market,frame,replace=True)
    series=fc.historical_series(path,market,'Tomatoes')
    with pytest.raises(op.OperationError):fc.train_series(series.drop(index=10))
    series['basis']='Sales proxy';series.loc[5,'stockout']=1
    with pytest.raises(op.OperationError):fc.train_series(series)
    bad=frame.iloc[:1].copy();bad['demand_kg']=-1
    with pytest.raises(op.OperationError):fc.import_history(path,market,bad,replace=True)


def test_history_corrections_and_duplicates_are_explicit(tmp_path):
    path=tmp_path/'history.db';market=op.registry(path,'markets',{'name':'Market','location':'Town'})
    frame=history();fc.import_history(path,market,frame)
    changed=frame.iloc[:1].copy();changed['demand_kg']=20
    with pytest.raises(op.OperationError):fc.import_history(path,market,changed)
    assert fc.historical_series(path,market,'Tomatoes').demand.iloc[0]==frame.demand_kg.iloc[0]
    fc.import_history(path,market,changed,replace=True)
    assert fc.historical_series(path,market,'Tomatoes').demand.iloc[0]==20
    with pytest.raises(op.OperationError):fc.import_history(path,market,pd.concat([frame.iloc[:1],frame.iloc[:1]]))


def workbook(rows,extra_sheet=False):
    book=Workbook();sheet=book.active;sheet.title='Stock'
    for row in rows:sheet.append(row)
    if extra_sheet:book.create_sheet('Buyers')
    output=BytesIO();book.save(output);return output.getvalue()


def test_excel_import_same_validated_results_as_csv():
    payload=workbook([['crop_nm','qty_avail','est_demand','mkt_prc','harvest_age'],['Tomatoes',500,300,25,2],['Onions',400,350,30,5],['Carrots',150,200,35,3]],True)
    assert sheets(payload)==['Stock','Buyers']
    result,_=prepare_dataset(payload,'stock.xlsx',sheet='Stock')
    assert not result.errors and len(result.data)==3
    from harvest.analytics import calculate_kpis
    assert calculate_kpis(result.data)['positive_surplus_kg']==250


def test_excel_rejects_formulas_duplicate_headers_and_bad_files():
    for rows in [[['crop','qty'],['Tomatoes','=100+5']],[['crop',' CROP '],['Tomatoes',10]]]:
        with pytest.raises(ValueError):read_table(workbook(rows),'stock.xlsx')
    with pytest.raises(ValueError):read_table(b'not a zip','stock.xlsx')


def test_heuristic_mapping_review_and_forecast_separation():
    frame=pd.DataFrame(columns=['commodity','quantity in stock','expected demand kg','market rate','days since harvest'])
    mapping,notes=interpret_columns(frame,'agriculture')
    assert mapping['crop']=='commodity' and mapping['available_kg']=='quantity in stock'
    assert all(row['confidence']=='Review required' for row in notes)
    _,notes=interpret_columns(pd.DataFrame(columns=['crop','crop_nm','forecast_demand','available_kg']),'agriculture')
    assert next(n for n in notes if n['target']=='crop')['source'] is None
    assert next(n for n in notes if n['target']=='estimated_demand_kg')['source'] is None


def test_corrupt_excel_xml_is_reported_as_validation_error():
    import zipfile
    payload=workbook([['crop','quantity'],['Tomatoes',10]])
    output=BytesIO()
    with zipfile.ZipFile(BytesIO(payload)) as original,zipfile.ZipFile(output,'w') as corrupted:
        for item in original.infolist():
            corrupted.writestr(item,b'<broken' if item.filename=='xl/worksheets/sheet1.xml' else original.read(item.filename))
    with pytest.raises(ValueError,match='Invalid Excel workbook'):read_table(output.getvalue(),'bad.xlsx')
