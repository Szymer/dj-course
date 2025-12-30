from flask import Flask, request, jsonify
from mcp_tools.file_helpers import list_sessions_detailed, read_session_raw, backup_files, delete_session_files, find_candidates_older_than

app = Flask(__name__)

@app.route('/list', methods=['GET'])
def list_endpoint():
    limit = request.args.get('limit', type=int)
    sessions = list_sessions_detailed()
    if limit:
        sessions = sessions[:limit]
    return jsonify({'count': len(sessions), 'sessions': sessions})

@app.route('/get', methods=['GET'])
def get_endpoint():
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'error':'session_id required'}), 400
    data, err = read_session_raw(session_id)
    if err:
        return jsonify({'error': err}), 404
    return jsonify(data)

@app.route('/delete', methods=['POST'])
def delete_endpoint():
    body = request.get_json() or {}
    session_ids = body.get('session_ids', [])
    older_than = body.get('older_than')
    dry_run = body.get('dry_run', True)

    to_delete = set(session_ids or [])
    if older_than:
        candidates = find_candidates_older_than(int(older_than))
        to_delete.update([c['id'] for c in candidates])

    to_delete = list(to_delete)

    if not to_delete:
        return jsonify({'candidates': [], 'deleted': [], 'skipped': []})

    if dry_run:
        return jsonify({'candidates': to_delete, 'deleted': [], 'skipped': []})

    backup_path, backup_results = backup_files(to_delete)
    deleted_results = delete_session_files(to_delete)

    return jsonify({'backup_path': backup_path, 'backup_results': backup_results, 'deleted_results': deleted_results})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)
