import os
import shutil
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from files.session_files import list_sessions, load_session_history
from files import config
import logging

BACKUP_DIR_NAME = "mcp_backups"


def get_log_path(session_id: str) -> str:
    return os.path.join(config.LOG_DIR, f"{session_id}-log.json")


def read_session_raw(session_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    path = get_log_path(session_id)
    if not os.path.exists(path):
        return None, f"Session file not found: {path}"
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data, None
    except Exception as e:
        return None, f"Error reading session file {path}: {e}"


def list_sessions_detailed() -> List[Dict]:
    raw = list_sessions()
    detailed = []
    for item in raw:
        sid = item.get('id')
        path = get_log_path(sid)
        preview = None
        err = item.get('error')
        err_read = None
        if not err:
            data, err_read = read_session_raw(sid)
            if data and 'history' in data and data['history']:
                preview = data['history'][-1].get('text', '')[:200]
        detailed.append({
            'id': sid,
            'path': path,
            'messages_count': item.get('messages_count'),
            'last_activity': item.get('last_activity'),
            'preview': preview,
            'error': err_read if err is None else err
        })
    return detailed


def find_candidates_older_than(days: int) -> List[Dict]:
    cutoff = datetime.now() - timedelta(days=days)
    candidates = []
    for s in list_sessions_detailed():
        last = s.get('last_activity')
        if not last or last == 'Brak aktywności':
            continue
        try:
            try:
                dt = datetime.fromisoformat(last)
            except ValueError:
                dt = datetime.strptime(last, '%Y-%m-%d %H:%M')
            if dt < cutoff:
                candidates.append(s)
        except ValueError:
            continue
    return candidates


def _parse_last_activity(last: Optional[str]) -> Optional[datetime]:
    if not last or last == 'Brak aktywności':
        return None
    try:
        return datetime.fromisoformat(last)
    except Exception:
        try:
            return datetime.strptime(last, '%Y-%m-%d %H:%M')
        except Exception:
            return None


def list_sessions_filtered(since: Optional[str] = None, before: Optional[str] = None,
                           limit: Optional[int] = None, title_contains: Optional[str] = None,
                           sort: str = 'updated_at_desc') -> Dict:
    """Return filtered sessions with metadata.

    since/before: ISO datetime strings
    sort: 'updated_at_desc' or 'updated_at_asc'
    """
    sessions = list_sessions_detailed()

    since_dt = datetime.fromisoformat(since) if since else None
    before_dt = datetime.fromisoformat(before) if before else None

    filtered = []
    for s in sessions:
        last = _parse_last_activity(s.get('last_activity'))

        if since_dt and (not last or last <= since_dt):
            continue
        if before_dt and (not last or last >= before_dt):
            continue

        if title_contains:
            preview = s.get('preview') or ''
            if title_contains.lower() not in preview.lower():
                continue

        filtered.append(s)

    reverse = sort == 'updated_at_desc'
    filtered.sort(key=lambda x: _parse_last_activity(x.get('last_activity')) or datetime.min, reverse=reverse)

    total = len(filtered)
    if limit:
        filtered = filtered[:limit]

    return {'count': len(filtered), 'matched': total, 'sessions': filtered}


def get_session_formatted(session_id: str, fmt: str = 'raw', truncate: Optional[int] = None) -> Dict:
    data, err = read_session_raw(session_id)
    if err:
        return {'session_id': session_id, 'error': err}

    result = {'session_id': session_id, 'path': get_log_path(session_id), 'messages_count': len(data.get('history', []))}

    if fmt == 'raw':
        result['raw'] = data
    elif fmt == 'universal':
        # reuse load_session_history to convert
        history, err2 = load_session_history(session_id)
        if err2:
            result['error'] = err2
        else:
            result['universal'] = history
    elif fmt == 'text':
        parts = []
        for entry in data.get('history', []):
            role = entry.get('role', '')
            text = entry.get('text', '')
            parts.append(f"[{role}] {text}")
        joined = '\n\n'.join(parts)
        if truncate:
            joined = joined[:truncate]
        result['text'] = joined
    else:
        result['error'] = f'Unknown format: {fmt}'

    return result


def delete_sessions(session_ids: Optional[List[str]] = None, older_than_days: Optional[int] = None,
                    dry_run: bool = True, backup: bool = True, confirm: bool = False) -> Dict:
    """Delete sessions safely. Returns a report dict."""
    logger = logging.getLogger('mcp_tools.delete')
    logger.setLevel(logging.DEBUG)
    logpath = os.path.join(config.LOG_DIR, 'mcp_delete.log')
    if not logger.handlers:
        fh = logging.FileHandler(logpath)
        fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        logger.addHandler(fh)

    to_delete = set(session_ids or [])
    if older_than_days is not None:
        candidates = find_candidates_older_than(older_than_days)
        to_delete.update([c['id'] for c in candidates])

    candidates = list(to_delete)
    report = {'candidates': candidates, 'deleted': [], 'skipped': [], 'backup_path': None}

    if not candidates:
        return report

    if dry_run:
        logger.info('Dry run delete requested for %s', candidates)
        return report

    if not confirm:
        logger.warning('Delete called without confirm=True; operation cancelled')
        report['skipped'] = [{'reason': 'no_confirm'}]
        return report

    if backup:
        backup_path, backup_results = backup_files(candidates)
        report['backup_path'] = backup_path
        report['backup_results'] = backup_results
        logger.info('Backup created at %s', backup_path)

    deleted_results = delete_session_files(candidates)
    for sid, ok, err in deleted_results:
        if ok:
            report['deleted'].append(sid)
            logger.info('Deleted %s', sid)
        else:
            report['skipped'].append({'id': sid, 'reason': err})
            logger.error('Failed to delete %s: %s', sid, err)

    return report


def ensure_backup_dir() -> str:
    backup_root = os.path.join(config.LOG_DIR, BACKUP_DIR_NAME)
    os.makedirs(backup_root, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%dT%H%M%S')
    path = os.path.join(backup_root, ts)
    os.makedirs(path, exist_ok=True)
    return path


def backup_files(session_ids: List[str]) -> Tuple[str, List[Tuple[str, bool, Optional[str]]]]:
    backup_path = ensure_backup_dir()
    results = []
    for sid in session_ids:
        src = get_log_path(sid)
        if not os.path.exists(src):
            results.append((sid, False, 'not_found'))
            continue
        dst = os.path.join(backup_path, os.path.basename(src))
        try:
            shutil.copy2(src, dst)
            results.append((sid, True, None))
        except Exception as e:
            results.append((sid, False, str(e)))
    return backup_path, results


def delete_session_files(session_ids: List[str]) -> List[Tuple[str, bool, Optional[str]]]:
    results = []
    for sid in session_ids:
        path = get_log_path(sid)
        if not os.path.exists(path):
            results.append((sid, False, 'not_found'))
            continue
        try:
            os.remove(path)
            results.append((sid, True, None))
        except Exception as e:
            results.append((sid, False, str(e)))
    return results
