import argparse
import json
from mcp_tools.file_helpers import list_sessions_filtered, get_session_formatted, delete_sessions, find_candidates_older_than


def cmd_list(args):
    data = list_sessions_filtered(limit=args.limit)
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_get(args):
    fmt = args.format or 'raw'
    truncate = args.truncate
    data = get_session_formatted(args.session_id, fmt=fmt, truncate=truncate)
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_delete(args):
    session_ids = args.session_ids or []
    older_than = args.older_than
    dry_run = args.dry_run
    backup = args.backup
    confirm = args.confirm

    report = delete_sessions(session_ids=session_ids, older_than_days=older_than, dry_run=dry_run, backup=backup, confirm=confirm)
    print(json.dumps(report, indent=2, default=str, ensure_ascii=False))


parser = argparse.ArgumentParser(prog='mcp_cli')
sub = parser.add_subparsers()

p_list = sub.add_parser('list')
p_list.add_argument('--limit', type=int)
p_list.set_defaults(func=cmd_list)

p_get = sub.add_parser('get')
p_get.add_argument('session_id')
p_get.add_argument('--format', choices=['raw', 'universal', 'text'])
p_get.add_argument('--truncate', type=int)
p_get.set_defaults(func=cmd_get)

p_delete = sub.add_parser('delete')
p_delete.add_argument('--session-ids', nargs='*')
p_delete.add_argument('--older-than', type=int, help='days')
p_delete.add_argument('--dry-run', action='store_true', default=False)
p_delete.add_argument('--backup', action='store_true', default=True)
p_delete.add_argument('--confirm', action='store_true', default=False)

p_delete.set_defaults(func=cmd_delete)

if __name__ == '__main__':
    args = parser.parse_args()
    if not hasattr(args, 'func'):
        parser.print_help()
    else:
        args.func(args)
