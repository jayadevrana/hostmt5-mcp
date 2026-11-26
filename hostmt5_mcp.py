"""HostMT5 MCP bridge: lets AI apps that run MCP servers locally over stdio (Claude Desktop, Cursor, Windsurf, Cline,
LM Studio...) use the HostMT5 remote MCP server at https://hostmt5.com/mcp.

Every message is forwarded to the remote server, so the tools are always HostMT5's current full set: accounts, live data
and history, orders, Expert Advisors (write / upload / compile / attach / inputs / logs), stop and resume trading, copy
trading, TradingView webhooks, alerts, statistics. Python 3.8+, standard library only.

Apps that take a URL do not need this: use https://hostmt5.com/mcp with header  Authorization: Bearer mc_...

Run:  uvx --from git+https://github.com/jayadevrana/hostmt5-mcp hostmt5-mcp
      or  python hostmt5_mcp.py
Env:  HOSTMT5_KEY  (required for tools: Dashboard > AI & API > New API key; a read-only key shows only the read tools)
      HOSTMT5_URL  (optional, default https://hostmt5.com)

Without a valid key the bridge still answers initialize and tools/list (from the public tool list at GET /mcp), so MCP
clients and directories can inspect it; tool calls then return the key error."""
import json, os, sys, urllib.error, urllib.request

__version__ = '2.0.0'
BASE = os.environ.get('HOSTMT5_URL', 'https://hostmt5.com').rstrip('/')
URL = BASE + '/mcp'
KEY = os.environ.get('HOSTMT5_KEY', '').strip()
UA = 'hostmt5-mcp-bridge/' + __version__
VERSIONS = ('2025-06-18', '2025-03-26', '2024-11-05')
KEY_HELP = 'HostMT5 API key missing or invalid: set HOSTMT5_KEY (Dashboard > AI & API > New API key)'
INSTRUCTIONS = ("HostMT5 hosts the user's real MetaTrader 5 terminals in the cloud. Call get_overview first: it lists the "
                "accounts (use their id in every other tool). Orders on a live (real) account move real money: confirm size "
                "and symbol with the user before trading unless they told you to act on your own.")


class NoKey(Exception):
    pass


def forward(raw):
    """POST one JSON-RPC message to the remote server. Returns (status, body text). Raises NoKey on 401."""
    if not KEY: raise NoKey()
    req = urllib.request.Request(URL, data=raw.encode(), method='POST', headers={
        'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream', 'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            status, ctype, body = r.status, r.headers.get('Content-Type', ''), r.read().decode()
    except urllib.error.HTTPError as e:
        if e.code == 401: raise NoKey()
        status, ctype, body = e.code, e.headers.get('Content-Type', ''), e.read().decode()
    if 'text/event-stream' in ctype:                              # the server answers JSON today; accept SSE too
        body = '\n'.join(l[5:].strip() for l in body.splitlines() if l.startswith('data:'))
    return status, body


def public_tools():
    """Tool names and descriptions from the public catalogue (GET /mcp), for clients without a valid key yet."""
    req = urllib.request.Request(URL, headers={'Accept': 'application/json', 'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as r: cat = json.loads(r.read().decode())
    return [dict(name=t['name'], description=t['description'], inputSchema={'type': 'object'},
                 annotations=dict(readOnlyHint=not t.get('trading'), openWorldHint=True)) for t in cat.get('tools', [])]


def offline(msg):
    """Answer a request locally because there is no usable key. None = nothing to send (a notification)."""
    mid, method, p = msg.get('id'), msg.get('method'), msg.get('params') or {}
    if mid is None: return None
    if method == 'initialize':
        v = p.get('protocolVersion') if p.get('protocolVersion') in VERSIONS else VERSIONS[0]
        res = dict(protocolVersion=v, capabilities=dict(tools=dict(listChanged=False)),
                   serverInfo=dict(name='hostmt5', title='HostMT5', version=__version__), instructions=INSTRUCTIONS)
    elif method == 'ping': res = {}
    elif method == 'tools/list':
        try: res = dict(tools=public_tools())
        except Exception: res = dict(tools=[])
    elif method == 'tools/call': res = dict(content=[dict(type='text', text=KEY_HELP)], isError=True)
    elif method in ('resources/list', 'prompts/list'): res = {method.split('/')[0]: []}
    else: return dict(jsonrpc='2.0', id=mid, error=dict(code=-32001, message=KEY_HELP))
    return dict(jsonrpc='2.0', id=mid, result=res)


def handle(line):
    """One line from stdin -> the text to write back, or None."""
    try: msg = json.loads(line)
    except ValueError: return json.dumps(dict(jsonrpc='2.0', id=None, error=dict(code=-32700, message='Parse error')))
    try:
        status, body = forward(line)
        return body.strip() if status != 202 and body.strip() else None   # 202 / empty = a notification was accepted
    except NoKey:
        if isinstance(msg, list):
            out = [r for r in (offline(m) for m in msg if isinstance(m, dict)) if r is not None]
            return json.dumps(out) if out else None
        r = offline(msg) if isinstance(msg, dict) else None
        return json.dumps(r) if r is not None else None
    except Exception as e:
        if not isinstance(msg, dict) or msg.get('id') is None: return None
        return json.dumps(dict(jsonrpc='2.0', id=msg['id'], error=dict(code=-32000, message='HostMT5: %s' % e)))


def main():
    for s in (sys.stdin, sys.stdout):                             # MCP stdio is UTF-8 with \n, also on Windows
        try: s.reconfigure(encoding='utf-8', newline='\n')
        except (AttributeError, ValueError): pass
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        out = handle(line)
        if out: sys.stdout.write(out + '\n'); sys.stdout.flush()


if __name__ == '__main__':
    main()
