from datetime import date,timedelta
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import pandas as pd
import pytest
from harvest import operations as op
from harvest.business import save_version,load_version

@pytest.fixture
def ledger(tmp_path):
    path=tmp_path/'ledger.db'
    market=op.registry(path,'markets',{'name':'Market','location':'Nagercoil','latitude':8.2,'longitude':77.4})
    supplier=op.registry(path,'suppliers',{'name':'Farmer','role':'Farmer','market_id':market})
    buyer=op.registry(path,'buyers',{'name':'Green Leaf Restaurant','role':'Restaurant','market_id':market})
    lot=op.add_lot(path,{'supplier_id':supplier,'crop':'Tomatoes','grade':'A','received':500,'local_demand':300,'market_price':25,'harvest_date':date.today()-timedelta(days=2),'ready_date':date.today(),'freshness':'Acceptable'})
    request=op.add_request(path,{'buyer_id':buyer,'crop':'Tomatoes','min_grade':'A','required':100,'offer_price':28,'transport_quote':200,'delivery_by':date.today()+timedelta(days=2),'max_distance':20,'inspection_required':True})
    return path,market,supplier,buyer,lot,request


def test_full_actual_workflow_and_transport(ledger):
    path,market,supplier,buyer,lot,request=ledger
    second=op.registry(path,'buyers',{'name':'City Hostel','role':'Hostel','market_id':market})
    other=op.add_request(path,{'buyer_id':second,'crop':'Tomatoes','min_grade':'A','required':80,'offer_price':26,'transport_quote':250,'delivery_by':date.today()+timedelta(days=2)})
    initial=op.snapshot(path);pairs=op.ranked_matches(initial['lots'],initial['requests'])
    assert sum(p['potential_kg'] for p in pairs)==180
    assert sum(p['estimated_return'] for p in pairs)==4430
    first_order=op.propose(path,lot,request,100,'first')
    second_order=op.propose(path,lot,other,80,'second')
    assert op.propose(path,lot,request,100,'first')==first_order
    assert op.snapshot(path)['lots'].iloc[0].physical_kg==500
    assert op.snapshot(path)['lots'].iloc[0].reserved_kg==0
    op.respond(path,first_order,'Accepted');op.respond(path,second_order,'Accepted')
    reserved=op.snapshot(path)['lots'].iloc[0]
    assert reserved.physical_kg==500 and reserved.reserved_kg==180 and reserved.surplus_kg==20
    sale=op.movement(path,lot,'Sale',100,date.today(),28,200,50,first_order,token='sale')
    assert op.movement(path,lot,'Sale',100,date.today(),28,200,50,first_order,token='sale')==sale
    op.movement(path,lot,'Sale',80,date.today(),26,250,0,second_order)
    report=op.evaluation(op.snapshot(path))
    assert report['sold_kg']==180 and report['physical_kg']==320 and report['reserved_kg']==0
    assert report['conversion']==1
    assert sum(r['actual_after_transport'] for r in report['orders'])==4430
    assert sum(r['actual_after_recorded_costs'] for r in report['orders'])==4380
    assert sum(r['difference'] for r in report['orders'])==0
    projection=op.planning_projection(op.snapshot(path))
    assert projection.iloc[0].available_kg==320
    assert projection.iloc[0].estimated_demand_kg==300


def test_declines_and_cancellations_do_not_consume_stock(ledger):
    path,_,_,_,lot,request=ledger
    proposal=op.propose(path,lot,request,100)
    op.respond(path,proposal,'Declined')
    assert op.snapshot(path)['lots'].iloc[0].physical_kg==500
    next_order=op.propose(path,lot,request,100)
    op.respond(path,next_order,'Accepted')
    op.movement(path,lot,'Sale',40,date.today(),28,90,0,next_order)
    op.respond(path,next_order,'Cancelled')
    data=op.snapshot(path)
    assert data['lots'].iloc[0].physical_kg==460 and data['lots'].iloc[0].reserved_kg==0
    assert data['requests'].iloc[0].remaining_kg==60
    with pytest.raises(op.OperationError):op.respond(path,proposal,'Accepted')


def test_concurrent_confirmation_cannot_overreserve(ledger):
    path,market,_,buyer,lot,_=ledger
    requests=[op.add_request(path,{'buyer_id':buyer,'crop':'Tomatoes','min_grade':'A','required':150,'offer_price':28,'transport_quote':200,'delivery_by':date.today()+timedelta(days=2)}) for _ in range(2)]
    orders=[op.propose(path,lot,request,150) for request in requests]
    def accept(order):
        try:op.respond(path,order,'Accepted');return True
        except op.OperationError:return False
    with ThreadPoolExecutor(max_workers=2) as pool:assert sum(pool.map(accept,orders))==1
    assert op.snapshot(path)['lots'].iloc[0].reserved_kg==150


def test_sale_and_disposal_bounds_are_atomic(ledger):
    path,_,_,_,lot,request=ledger
    order=op.propose(path,lot,request,100);op.respond(path,order,'Accepted')
    for args in [(lot,'Sale',101,date.today(),28,200,0,order),(lot,'Discard',401,date.today()),(lot,'Redistribution',1,date.today()+timedelta(days=1)),(lot,'Sale',1,date.today()-timedelta(days=3),28,0,0,order)]:
        with pytest.raises(op.OperationError):op.movement(path,*args)
    assert op.snapshot(path)['movements'].empty
    op.movement(path,lot,'Discard',20,date.today(),other_costs=10)
    op.movement(path,lot,'Redistribution',30,date.today(),transport=50)
    data=op.snapshot(path);report=op.evaluation(data)
    assert report['physical_kg']==450 and report['reserved_kg']==100
    assert report['discarded_kg']==20 and report['redistributed_kg']==30


@pytest.mark.parametrize('change,reason',[
    ({'freshness':'Unsuitable'},'Stock reported unsuitable'),
    ({'grade':'C'},'Grade below requirement'),
    ({'ready_date':str(date.today()+timedelta(days=9))},'Delivery dates incompatible'),
    ({'latitude':None,'longitude':None},'Distance unknown for limit')])
def test_matching_explains_constraints(ledger,change,reason):
    path,*_=ledger;data=op.snapshot(path)
    lot=data['lots'].iloc[0].to_dict();lot.update(change)
    check=op.suitability(lot,data['requests'].iloc[0])
    assert not check['eligible'] and reason in check['reasons']


def test_multi_supplier_same_crop_and_capped_ranking(ledger):
    path,market,_,buyer,_,_=ledger
    supplier=op.registry(path,'suppliers',{'name':'Other farmer','role':'Vendor','market_id':market})
    op.add_lot(path,{'supplier_id':supplier,'crop':'Tomatoes','grade':'A','received':70,'local_demand':0,'market_price':25,'harvest_date':date.today(),'ready_date':date.today(),'freshness':'Acceptable'})
    data=op.snapshot(path);pairs=op.ranked_matches(data['lots'],data['requests'])
    assert sum(p['potential_kg'] for p in pairs)<=100
    assert op.planning_projection(data).iloc[0].available_kg==570
    assert len(data['lots'])==2
    assert op.snapshot(path)['orders'].empty


def test_planning_restore_cannot_reverse_actual_sales(ledger,agriculture,buyers):
    path,_,_,_,lot,request=ledger
    state={'active_data':agriculture,'active_buyers':buyers}
    save_version(state,path,'Planning',0)
    order=op.propose(path,lot,request,100);op.respond(path,order,'Accepted')
    op.movement(path,lot,'Sale',100,date.today(),28,200,0,order)
    restored=load_version(path,1)
    assert restored['active_data'].iloc[0].available_kg==500
    assert op.snapshot(path)['lots'].iloc[0].physical_kg==400
    binary=op.database_backup(path)
    copy=path.parent/'copy.db';copy.write_bytes(binary)
    assert op.snapshot(copy)['lots'].iloc[0].physical_kg==400


def test_retry_tokens_reject_different_payload_and_total_costs_include_disposal(ledger):
    path,_,_,_,lot,request=ledger
    order=op.propose(path,lot,request,100,'same')
    with pytest.raises(op.OperationError,match='Retry token'):op.propose(path,lot,request,90,'same')
    op.respond(path,order,'Accepted')
    op.movement(path,lot,'Sale',100,date.today(),28,200,40,order,token='sale')
    with pytest.raises(op.OperationError,match='Retry token'):op.movement(path,lot,'Sale',99,date.today(),28,200,40,order,token='sale')
    op.movement(path,lot,'Discard',10,date.today(),transport=20,other_costs=30)
    report=op.evaluation(op.snapshot(path))
    assert report['actual_gross']==2800
    assert report['all_transport']==220 and report['all_other']==70
    assert report['after_all_recorded_costs']==2510


def test_lot_surplus_and_shortage_do_not_cancel_between_suppliers(ledger):
    path,_,supplier,_,_,request=ledger
    op.add_lot(path,{'supplier_id':supplier,'crop':'Tomatoes','grade':'A','received':50,'local_demand':100,'market_price':25,'harvest_date':date.today(),'ready_date':date.today(),'freshness':'Acceptable'})
    totals=op.operational_totals(op.snapshot(path))
    assert totals['positive_surplus_kg']==200 and totals['shortage_kg']==50
    op.close_request(path,request)
    assert not any(p['eligible'] for p in op.ranked_matches(op.snapshot(path)['lots'],op.snapshot(path)['requests']))
