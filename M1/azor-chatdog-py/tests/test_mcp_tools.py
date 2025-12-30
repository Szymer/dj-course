import os
import json
import tempfile
from mcp_tools import file_helpers
from files import config


def setup_tmp_log_dir(tmp_path, monkeypatch):
    # create tmp log dir
    tmp_log = tmp_path / 'logs'
    tmp_log.mkdir()
    # create a couple of session files
    now = '2025-12-30T12:00:00'
    s1 = tmp_log / 's1-log.json'
    s1.write_text(json.dumps({'session_id':'s1','history':[{'role':'user','timestamp':now,'text':'hello'}]}))
    s2 = tmp_log / 's2-log.json'
    s2.write_text(json.dumps({'session_id':'s2','history':[{'role':'user','timestamp':now,'text':'bye'}]}))
    # monkeypatch LOG_DIR
    monkeypatch.setattr(config, 'LOG_DIR', str(tmp_log))
    return str(tmp_log)


def test_list_sessions_filtered(tmp_path, monkeypatch):
    setup_tmp_log_dir(tmp_path, monkeypatch)
    res = file_helpers.list_sessions_filtered()
    assert res['count'] == 2
    ids = [s['id'] for s in res['sessions']]
    assert 's1' in ids and 's2' in ids


def test_get_session_formatted(tmp_path, monkeypatch):
    setup_tmp_log_dir(tmp_path, monkeypatch)
    res = file_helpers.get_session_formatted('s1', fmt='text')
    assert 'text' in res


def test_delete_sessions_dry_run(tmp_path, monkeypatch):
    setup_tmp_log_dir(tmp_path, monkeypatch)
    report = file_helpers.delete_sessions(session_ids=['s1'], dry_run=True, confirm=False)
    assert 's1' in report['candidates']
    assert report['deleted'] == []
