from typing import Optional
import json
from flask import Flask, request, jsonify
from mcp_tools.file_helpers import list_sessions_filtered, get_session_formatted, delete_sessions

app = Flask(__name__)


@app.route('/tools/list', methods=['GET'])
def http_list():
    params = dict(request.args)
    data = list_sessions_filtered(since=params.get('since'), before=params.get('before'), limit=int(params.get('limit')) if params.get('limit') else None, title_contains=params.get('title_contains'), sort=params.get('sort','updated_at_desc'))
    return jsonify(data)


@app.route('/tools/get', methods=['GET'])
def http_get():
    session_id = request.args.get('session_id')
    fmt = request.args.get('format','raw')
    truncate = request.args.get('truncate')
    truncate = int(truncate) if truncate else None
    res = get_session_formatted(session_id, fmt=fmt, truncate=truncate)
    return jsonify(res)


@app.route('/tools/delete', methods=['POST'])
def http_delete():
    body = request.get_json() or {}
    report = delete_sessions(session_ids=body.get('session_ids'), older_than_days=body.get('older_than'), dry_run=body.get('dry_run', True), backup=body.get('backup', True), confirm=body.get('confirm', False))
    return jsonify(report)


def cli_run_method(method: str, params_json: str):
    params = json.loads(params_json or '{}')
    if method in ('tools/list','tools/list_sessions'):
        return json.dumps(list_sessions_filtered(**params), ensure_ascii=False)
    if method in ('tools/get','tools/get_session'):
        return json.dumps(get_session_formatted(params.get('session_id'), fmt=params.get('format','raw'), truncate=params.get('truncate')), ensure_ascii=False)
    if method in ('tools/delete','tools/delete_sessions'):
        return json.dumps(delete_sessions(session_ids=params.get('session_ids'), older_than_days=params.get('older_than'), dry_run=params.get('dry_run', True), backup=params.get('backup', True), confirm=params.get('confirm', False)), ensure_ascii=False)
    return json.dumps({'error':'unknown method'})


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--method', type=str, help='Run single tool (for inspector CLI mode)')
    parser.add_argument('--params', type=str, default='{}')
    args = parser.parse_args()

    if args.method:
        print(cli_run_method(args.method, args.params))
    else:
        app.run(host=args.host, port=args.port)
