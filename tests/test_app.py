from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / 'app.py')

def test_entry_demo_dashboard_and_shared_state(tmp_path, monkeypatch):
    monkeypatch.setenv('HARVEST_DB_PATH', str(tmp_path / 'app.sqlite3'))
    app = AppTest.from_file(APP).run(timeout=30)
    assert not app.exception
    assert app.session_state['active_data'] is None
    app.button(key='load_demo').click().run()
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Dashboard').run()
    assert not app.exception
    assert [m.value for m in app.metric] == ['3', '1,050', '850', '250', '50']
    for page in ['Upload Data', 'Surplus and Risk', 'Buyer Matching', 'Profit Analysis', 'AI Assistant', 'Home']:
        next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value(page).run()
        assert not app.exception
        assert len(app.session_state['active_data']) == 3
    next(w for w in app.selectbox if w.key.startswith('language_')).set_value('தமிழ்').run()
    assert not app.exception
    assert 'முகப்பு' in app.header[0].value


def test_dashboard_empty_state():
    app = AppTest.from_file(APP).run()
    next(w for w in app.radio if w.key.split('__ui_')[0]=='navigation').set_value('Dashboard').run()
    assert not app.exception
    assert len(app.metric) == 0
    assert app.info
