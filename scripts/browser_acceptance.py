"""Optional real-browser acceptance check. Runtime app does not require Playwright."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import os
import tempfile
import zipfile
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from harvest.i18n import Translator


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8510)
    parser.add_argument('--browser-config',help='Optional JSON containing custom browser path and args')
    parser.add_argument('--axe-script',help='Optional path to a local axe.min.js for accessibility checks')
    parser.add_argument('--artifacts',help='Optional local screenshot directory')
    parser.add_argument('--report',help='Optional JSON result path')
    args=parser.parse_args()
    from playwright.sync_api import sync_playwright,expect,TimeoutError as PlaywrightTimeout
    url=f'http://127.0.0.1:{args.port}'
    temporary=tempfile.TemporaryDirectory(prefix='cebafex-browser-')
    server=subprocess.Popen([sys.executable,'-m','streamlit','run','app.py','--server.headless','true',
                             '--server.address','127.0.0.1','--server.port',str(args.port)],cwd=ROOT,
                             stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                             env={**os.environ,'HARVEST_DB_PATH':str(Path(temporary.name)/'browser.sqlite3')})
    result={'languages':[],'screens':[],'accessibility':[],'external_requests':[],'browser_errors':[]}
    artifacts=Path(args.artifacts) if args.artifacts else None
    if artifacts:artifacts.mkdir(parents=True,exist_ok=True)
    try:
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _ in range(60):
            try:
                with opener.open(url+'/_stcore/health',timeout=1) as response:assert response.status==200
                break
            except OSError:time.sleep(.25)
        else:raise RuntimeError('Local server failed to start')
        config=json.loads(Path(args.browser_config).read_text()) if args.browser_config else {}
        with sync_playwright() as p:
            kwargs={'headless':True}
            if config:kwargs.update(executable_path=config['path'],args=config.get('args',[]))
            for language in ['English','தமிழ்']:
                browser=p.chromium.launch(**kwargs)
                result['browser']=browser.version
                code='en' if language=='English' else 'ta'; t=Translator(language)
                context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce')
                page=context.new_page()
                page.on('pageerror',lambda error:result['browser_errors'].append(str(error)))
                def route(request):
                    if request.request.url.startswith(url) or request.request.url.startswith(('data:','blob:')):request.continue_()
                    else:result['external_requests'].append(request.request.url);request.abort()
                page.route('**/*',route)
                def settled():
                    page.wait_for_function("document.querySelector('[data-testid=stApp]')?.getAttribute('data-test-script-state')==='notRunning'")
                    page.wait_for_function('(lang)=>document.documentElement.lang===lang',arg=code)
                    page.wait_for_timeout(250)
                    page.wait_for_function("document.querySelector('[data-testid=stApp]')?.getAttribute('data-test-script-state')==='notRunning'")
                def choose(label,value):
                    print(code+': choosing '+label,flush=True)
                    control=page.get_by_role('combobox',name=t(label),exact=True)
                    for attempt in range(3):
                        control.click()
                        try:
                            page.get_by_role('option',name=value,exact=True).click(timeout=4000)
                            settled()
                            expect(control).to_have_value(value)
                            return
                        except PlaywrightTimeout:
                            if attempt==2:
                                if artifacts:
                                    page.screenshot(path=str(artifacts/'selection-failure.png'),full_page=True)
                                    (artifacts/'selection-failure.txt').write_text(page.locator('body').inner_text())
                                raise
                            page.keyboard.press('Escape');settled()
                def go(name):
                    page.set_viewport_size({'width':1440,'height':1000})
                    expand=page.get_by_role('button',name=re.compile('Expand sidebar|Open sidebar|பக்கப் பட்டையை விரிக்கவும்|பக்கப் பட்டையைத் திறக்கவும்'))
                    if expand.count() and expand.first.is_visible():
                        try:expand.first.click(timeout=1500)
                        except PlaywrightTimeout:pass  # Desktop resize may already have expanded it.

                    page.get_by_role('radio',name=t(name),exact=True).locator('xpath=ancestor::label').click()
                    page.get_by_role('heading',name=t(name),exact=True).wait_for()
                    settled()
                def metrics(values):
                    expect(page.get_by_test_id('stMetricValue')).to_have_text(values)
                def upload(kind,filename):
                    source=ROOT/'data'/filename
                    if language=='English':page.locator('input[type=file]').set_input_files(source)
                    else:page.frame_locator('iframe[src*=tamil_csv_upload]').locator('#file').set_input_files(source)
                    fingerprint=hashlib.sha256(source.read_bytes()).hexdigest()
                    page.locator(f'[class*="st-key-map_{kind}_{fingerprint}"]').first.wait_for()
                    settled()
                page.goto(url)
                page.get_by_role('button',name='Get Started',exact=True).wait_for()
                if language=='தமிழ்':
                    page.get_by_role('combobox').first.click()
                    page.get_by_role('option',name='Tamil',exact=True).click()
                    expect(page.get_by_role('combobox').first).to_have_value('தமிழ்')
                settled()
                page.get_by_role('button',name=t('Get Started'),exact=True).click()
                page.get_by_role('heading',name=t('Upload Data'),exact=True).wait_for()
                upload('agriculture','agriculture_messy_demo.csv')
                page.get_by_role('button',name=t('Validate and activate'),exact=True).click()
                page.get_by_role('heading',name=t('Quality summary'),exact=True).wait_for()
                expect(page.get_by_test_id('stAlert').filter(has_text=t('market_price_per_kg'))).to_be_visible()
                assert not page.get_by_role('heading',name=t('Active validated data'),exact=True).count()
                upload('agriculture','agriculture_demo.csv')
                page.get_by_role('button',name=t('Validate and activate'),exact=True).click()
                page.get_by_text(t('Validated and active'),exact=True).wait_for()
                page.get_by_role('radio',name=t('Buyers'),exact=True).locator('xpath=ancestor::label').click()
                page.get_by_text(t('Upload buyers CSV'),exact=True).wait_for()
                upload('buyers','buyers_demo.csv')
                page.get_by_role('button',name=t('Validate and activate'),exact=True).click()
                page.get_by_text(t('Validated and active'),exact=True).wait_for()
                go('Dashboard');metrics(['3','1,050','850','250','50'])
                go('Surplus and Risk');metrics(['250','50','0'])
                go('Buyer Matching');choose('Matching crop filter',t('Tomatoes'));metrics(['200','180','20'])
                go('Profit Analysis');choose('Financial crop filter',t('Tomatoes'))
                metrics(['180','₹4,880.00','₹450.00','₹4,430.00','₹4,500.00','₹-70.00'])
                go('AI Assistant')
                page.get_by_role('button',name=t('Use suggested question'),exact=True).click()
                page.get_by_role('heading',name=t('Question {n}',n=1),exact=True).wait_for()
                expect(page.get_by_role('main')).to_contain_text('4,430.00')
                settled()
                if language=='தமிழ்':
                    assert page.evaluate("document.fonts.check('16px HarvestTamil','தக்காளி')")
                    input_frame=page.frame_locator('iframe[src*=locale_chrome]')
                    assert page.locator('html').get_attribute('lang')=='ta'
                # Real business CRUD, persistence, backup download and version recovery.
                go('Workspace')
                crop_name='Beans' if code=='en' else 'பீன்ஸ்'
                form=page.get_by_test_id('stForm').filter(has=page.get_by_role('textbox',name=t('Crop'),exact=True))
                form.get_by_role('textbox',name=t('Crop'),exact=True).fill(crop_name)
                for label,value in [('Available (kg)','90'),('Estimated demand (kg)','50'),('Market price (₹/kg)','12'),('Harvest age (days)','1')]:
                    form.get_by_role('spinbutton',name=t(label),exact=True).fill(value)
                form.get_by_role('button',name=t('Save record'),exact=True).click()
                metrics(['4','3']);settled()
                page.get_by_role('tab',name=t('Version history'),exact=True).click();settled()
                page.get_by_role('textbox',name=t('Version name'),exact=True).fill('Browser version' if code=='en' else 'உலாவிப் பதிப்பு')
                page.get_by_role('button',name=t('Save workspace version'),exact=True).click()
                page.get_by_text(t('Workspace version saved.'),exact=True).wait_for();settled()
                with page.expect_download() as download_event:
                    page.get_by_role('button',name=t('Download original data backup'),exact=True).click()
                download=download_event.value
                with zipfile.ZipFile(download.path()) as backup:
                    assert len(json.loads(backup.read('workspace.json'))['active_data'])==4
                page.get_by_role('tab',name=t('Crop records'),exact=True).click();settled()
                choose('Record action',t('Edit record'))
                choose('Select record',crop_name)
                edit=page.get_by_test_id('stForm').filter(has=page.get_by_role('spinbutton',name=t('Available (kg)'),exact=True))
                edit.get_by_role('spinbutton',name=t('Available (kg)'),exact=True).fill('120')
                edit.get_by_role('button',name=t('Save record'),exact=True).click();settled()
                page.get_by_role('tab',name=t('Version history'),exact=True).click();settled()
                page.get_by_role('checkbox',name=t('I want to replace the active workspace with this saved version.'),exact=True).locator('xpath=ancestor::label').click()
                page.get_by_role('button',name=t('Restore selected version'),exact=True).click();settled()
                go('Dashboard');metrics(['4','1,140','900','290','50'])
                result['languages'].append({'language':code,'judging_workflow':'passed','required_values':'passed','business_records_versions_backup_recovery':'passed'})
                print(code+': upload → validation → dashboard → risk → matching → financials → assistant PASSED',flush=True)
                for screen in ['Home','Upload Data','Dashboard','Surplus and Risk','Buyer Matching','Profit Analysis','AI Assistant','Workspace']:
                    go(screen)
                    if screen=='Home':
                        skip=page.get_by_role('link',name=t('Skip to main content'),exact=True)
                        skip.focus();page.keyboard.press('Enter')
                        page.wait_for_function("document.activeElement.id==='main-content'")
                    # Material-icon ligatures are glyphs, not English interface words.
                    text=page.evaluate('''()=>{const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n,out=[];while(n=walker.nextNode()){const e=n.parentElement;if(!e||e.closest('script,style,[data-testid=stIconMaterial]'))continue;if(!e.checkVisibility({checkVisibilityCSS:true,checkOpacity:true}))continue;if(/Material/i.test(getComputedStyle(e).fontFamily))continue;out.push(n.textContent);}return out.join(' ');}''')
                    forbidden=re.compile(r'[\u0b80-\u0bff]' if code=='en' else r'[A-Za-z]')
                    assert not forbidden.search(text),(code,screen,'language leakage',forbidden.search(text).group())
                    attributes=page.locator('[aria-label],[title],[placeholder]').evaluate_all("els=>els.filter(e=>e.checkVisibility({checkVisibilityCSS:true,checkOpacity:true})).flatMap(e=>['aria-label','title','placeholder'].map(a=>e.getAttribute(a)||''))")
                    assert all(not forbidden.search(value) for value in attributes),(code,screen,'accessible label leakage',[value for value in attributes if forbidden.search(value)])
                    # Verify selected strings as well as text nodes, because combobox values are properties.
                    for value in page.get_by_role('combobox').evaluate_all('(els)=>els.map(e=>e.value)'):
                        assert not forbidden.search(value),(code,screen,'selected value',value)
                    if artifacts and screen in ['Home','Dashboard','AI Assistant','Workspace']:
                        page.screenshot(path=str(artifacts/f'{code}-{screen.replace(" ","-")}-desktop.png'),full_page=True)
                    if args.axe_script:
                        page.add_script_tag(path=args.axe_script)
                        audit=page.evaluate("async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}});return r.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary})).slice(0,4)}));}")
                        result['accessibility'].append({'language':code,'screen':screen,'violations':audit})
                    page.set_viewport_size({'width':375,'height':812})
                    collapse=page.get_by_role('button',name=re.compile('Collapse sidebar|பக்கப் பட்டையைச் சுருக்கவும்'))
                    if collapse.count() and collapse.first.is_visible():
                        try:collapse.first.click(timeout=1500)
                        except PlaywrightTimeout:pass  # Phone resize may already have collapsed it.
                    page.wait_for_timeout(100)
                    dimensions=page.evaluate('({viewport:innerWidth,document:document.documentElement.scrollWidth,main:document.querySelector("[data-testid=stMain]")?.scrollWidth})')
                    assert dimensions['document']<=dimensions['viewport']+1,(code,screen,'page overflow',dimensions)
                    if screen=='Home':
                        # The phone menu must open and navigate, not merely fit the viewport.
                        expand=page.get_by_role('button',name=re.compile('Expand sidebar|Open sidebar|பக்கப் பட்டையை விரிக்கவும்|பக்கப் பட்டையைத் திறக்கவும்'))
                        expect(expand.first).to_be_visible();expand.first.click()
                        page.get_by_role('radio',name=t('Dashboard'),exact=True).locator('xpath=ancestor::label').click()
                        page.get_by_role('heading',name=t('Dashboard'),exact=True).wait_for();settled()
                        page.get_by_role('radio',name=t('Home'),exact=True).locator('xpath=ancestor::label').click()
                        page.get_by_role('heading',name=t('Home'),exact=True).wait_for();settled()
                        page.get_by_role('button',name=re.compile('Collapse sidebar|பக்கப் பட்டையைச் சுருக்கவும்')).first.click()
                    if artifacts and screen in ['Dashboard','Buyer Matching','Profit Analysis','AI Assistant','Workspace']:
                        page.screenshot(path=str(artifacts/f'{code}-{screen.replace(" ","-")}-phone.png'),full_page=True)
                    if screen in ['Dashboard','Workspace']:
                        for width,height in [(768,1024),(812,375)]:
                            page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(100)
                            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(code,screen,width,'page overflow')
                    result['screens'].append({'language':code,'screen':screen,'desktop_language':'passed','phone_width':375,'horizontal_page_overflow':False})
                    print(code+': '+screen+' desktop + phone checked',flush=True)
                # The real native control must survive a round-trip language change.
                page.set_viewport_size({'width':1440,'height':1000})
                expand=page.get_by_role('button',name=re.compile('Expand sidebar|Open sidebar|பக்கப் பட்டையை விரிக்கவும்|பக்கப் பட்டையைத் திறக்கவும்'))
                if expand.count() and expand.first.is_visible():
                    try:expand.first.click(timeout=1500)
                    except PlaywrightTimeout:pass  # Desktop resize may already have expanded it.

                settled()
                for attempt in range(3):
                    page.get_by_role('combobox',name=t('Language'),exact=True).click()
                    try:
                        page.get_by_role('option',name='ஆங்கிலம்' if code=='ta' else 'Tamil',exact=True).click(timeout=4000)
                        break
                    except PlaywrightTimeout:
                        print('Language menu options: '+str(page.get_by_role('option').all_text_contents()),flush=True)
                        if artifacts:page.screenshot(path=str(artifacts/'language-menu.png'),full_page=True)
                        page.keyboard.press('Escape');page.wait_for_timeout(500)
                        if attempt==2:raise
                expect(page.get_by_role('combobox').first).to_have_value('English' if code=='ta' else 'தமிழ்')
                context.close()
                browser.close()
        assert not result['browser_errors'],result['browser_errors']
        assert not result['external_requests'],result['external_requests']
        assert not any(item['violations'] for item in result['accessibility']),result['accessibility']
        result['status']='passed'
        if args.report:Path(args.report).write_text(json.dumps(result,ensure_ascii=False,indent=2))
        print(json.dumps({'status':'passed','languages':len(result['languages']),'screen_checks':len(result['screens']),
                          'axe_violations':sum(len(item['violations']) for item in result['accessibility'])}),flush=True)
    except Exception as exc:
        result['failure']=str(exc)
        try:
            if artifacts:
                page.screenshot(path=str(artifacts/'failure.png'),full_page=True)
                (artifacts/'failure.txt').write_text(page.locator('body').inner_text())
        except Exception:pass
        raise
    finally:
        if args.report and 'status' not in result:
            result['status']='failed';Path(args.report).write_text(json.dumps(result,ensure_ascii=False,indent=2))
        server.terminate()
        try:server.wait(timeout=10)
        except subprocess.TimeoutExpired:server.kill();server.wait()
        temporary.cleanup()

if __name__=='__main__':main()
