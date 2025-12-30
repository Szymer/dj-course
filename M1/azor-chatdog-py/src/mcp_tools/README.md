# MCP Tools (AZOR)

This folder contains lightweight MCP-compatible tools for AZOR sessions.

Available helpers:
- `mcp_tools/file_helpers.py` - file helpers for listing, reading and deleting session logs.
- `mcp_tools/mcp_cli.py` - CLI for quick manual testing (`list`, `get`, `delete`).
- `mcp_tools/mcp_server.py` - a shim that supports two modes:
  - CLI mode: `python -m mcp_tools.mcp_server --method tools/list --params '{}'` (prints JSON and exits).
  - HTTP mode (Flask): `python -m mcp_tools.mcp_server` exposes `/tools/list`, `/tools/get`, `/tools/delete`.

Manual testing (CLI shim):

```powershell
# activate venv
& 'C:\djc\dj-course\.venv\Scripts\Activate.ps1'
Set-Location 'C:\djc\dj-course\M1\azor-chatdog-py\src'
# list sessions via CLI shim
python -m mcp_tools.mcp_server --method tools/list --params '{}'

# get session
python -m mcp_tools.mcp_server --method tools/get --params '{"session_id":"<id>","format":"text"}'

# delete dry-run
python -m mcp_tools.mcp_server --method tools/delete --params '{"older_than":1, "dry_run":true}'
```

Notes about `npx @modelcontextprotocol/inspector`:
- The inspector expects a running MCP server using stdio JSON-RPC semantics. The CLI shim prints a JSON response and exits, which is sufficient for many quick tests but not a full stdio MCP server.
- To test with inspector you can either implement a full stdio MCP server (see next steps in the project), or use the `--cli` mode of inspector to run our CLI command. If inspector fails to connect, prefer running the `python -m mcp_tools.mcp_server --method ...` commands directly.

HTTP mode (useful for curl/Postman):
```powershell
python -m mcp_tools.mcp_server
Invoke-WebRequest 'http://127.0.0.1:8000/tools/list' -UseBasicParsing
```

Security:
- `delete` defaults to `dry_run=True` and requires `confirm=True` for real deletion.
- Backups are stored under `~/.azor/mcp_backups/` before deletion.

Running tests:
- From project root with `.venv` active:
```powershell
pip install pytest
Set-Location 'C:\djc\dj-course\M1\azor-chatdog-py\src'
pytest -q
```
