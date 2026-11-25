"""HostMT5 MCP server: lets an AI assistant (Claude, ChatGPT desktop, Cursor, ...) work with your MetaTrader 5
accounts hosted on https://hostmt5.com.

Run:     uvx --from git+https://github.com/jayadevrana/hostmt5-mcp hostmt5-mcp
Env:     HOSTMT5_KEY  (required, from the HostMT5 dashboard > API keys)
         HOSTMT5_URL  (optional, default https://hostmt5.com)
Everything the assistant does goes through the same checks as the website; orders are real on live accounts,
so the tools that trade say so. Start on a demo account."""
import base64, os
from pathlib import Path
import httpx
from mcp.server.fastmcp import FastMCP

URL = os.environ.get('HOSTMT5_URL', 'https://hostmt5.com').rstrip('/')
KEY = os.environ.get('HOSTMT5_KEY', '')
mcp = FastMCP("hostmt5")


def _api(method, path, body=None):
    if not KEY: raise RuntimeError('Set HOSTMT5_KEY (Dashboard > API keys)')
    r = httpx.request(method, URL + path, json=body, headers={'Authorization': f'Bearer {KEY}'}, timeout=300)
    try: j = r.json()
    except Exception: j = {'detail': r.text[:300]}
    if r.status_code >= 400: raise RuntimeError(j.get('detail') if isinstance(j, dict) else str(j))
    return j


def _call(account_id, op, **kw):
    r = _api('POST', f'/api/accounts/{account_id}/call', dict(op=op, **kw))
    if r.get('ok') is False: raise RuntimeError(r.get('error') or f'{op} refused')
    return r


# ---------------------------------------------------------------- overview
@mcp.tool()
def overview() -> dict:
    """Plan (slots, paid until), every hosted MT5 account (id, label, login, server, status), copy-trading links and recent copy activity."""
    me = _api('GET', '/api/me')
    return {k: me[k] for k in ('plan', 'accounts', 'links', 'copylog', 'methods')}


@mcp.tool()
def account_state(account_id: int) -> dict:
    """Balance, equity, margin, open positions, pending orders and live Market Watch quotes of one account."""
    return _api('GET', f'/api/accounts/{account_id}/state')


@mcp.tool()
def price_history(account_id: int, symbol: str, timeframe: str = 'H1', count: int = 200) -> dict:
    """OHLC bars. timeframe: M1 M5 M15 M30 H1 H4 D1 W1 MN1. Each bar has time (unix), open, high, low, close, tick_volume, spread."""
    return _call(account_id, 'bars', symbol=symbol, tf=timeframe, count=min(int(count), 5000))


@mcp.tool()
def trade_history(account_id: int) -> dict:
    """Closed deals of the last 30 days (deposits, opens, closes with profit)."""
    return _call(account_id, 'deals')


@mcp.tool()
def find_symbols(account_id: int, text: str) -> list:
    """Search the broker's symbol list (name or description contains text). Use watch_symbol to get quotes for one."""
    t = text.lower(); syms = _call(account_id, 'symbols').get('symbols', [])
    return [s for s in syms if t in ' '.join(map(str, s if isinstance(s, list) else [s])).lower()][:50]


@mcp.tool()
def watch_symbol(account_id: int, symbol: str, show: bool = True) -> dict:
    """Add (show=True) or remove a symbol from the account's Market Watch, so its quotes stream."""
    return _call(account_id, 'show_symbol' if show else 'hide_symbol', symbol=symbol)


# ---------------------------------------------------------------- trading (REAL orders on live accounts)
@mcp.tool()
def market_order(account_id: int, symbol: str, side: str, volume: float, sl: float = 0, tp: float = 0, comment: str = '') -> dict:
    """Open a position at market. side: buy or sell. sl/tp are prices (0 = none). REAL order on a live account."""
    return _call(account_id, 'market', symbol=symbol, side=side.lower(), volume=volume, sl=sl, tp=tp, comment=comment)


@mcp.tool()
def pending_order(account_id: int, symbol: str, kind: str, volume: float, price: float, sl: float = 0, tp: float = 0) -> dict:
    """Place a pending order. kind: 'buy limit', 'sell limit', 'buy stop' or 'sell stop'. REAL order on a live account."""
    return _call(account_id, 'pending', symbol=symbol, kind=kind.lower(), volume=volume, price=price, sl=sl, tp=tp)


@mcp.tool()
def close_position(account_id: int, ticket: int, volume: float = 0) -> dict:
    """Close a position (volume 0 = all of it, or a partial volume)."""
    return _call(account_id, 'close', ticket=ticket, **({'volume': volume} if volume else {}))


@mcp.tool()
def cancel_order(account_id: int, ticket: int) -> dict:
    """Delete a pending order."""
    return _call(account_id, 'cancel', ticket=ticket)


@mcp.tool()
def modify_position(account_id: int, ticket: int, sl: float = 0, tp: float = 0) -> dict:
    """Set a position's stop loss and take profit (prices; 0 removes it)."""
    return _call(account_id, 'modify', ticket=ticket, sl=sl, tp=tp)


# ---------------------------------------------------------------- Expert Advisors (run 24/7 inside the account's MT5)
@mcp.tool()
def list_eas(account_id: int) -> dict:
    """Compiled EAs available in the terminal, and the ones attached (with id, chart, default and changed inputs)."""
    return _call(account_id, 'mt5_experts')


@mcp.tool()
def upload_ea(account_id: int, file_path: str) -> dict:
    """Upload an EA from this computer: compiled .ex5, or .mq5 source (compiled on the server; errors come back). Then attach_ea."""
    p = Path(file_path).expanduser()
    return _call(account_id, 'mt5_upload', filename=p.name, data=base64.b64encode(p.read_bytes()).decode())


@mcp.tool()
def ea_inputs(account_id: int, name: str, symbol: str = 'EURUSD') -> dict:
    """An EA's inputs and their defaults BEFORE attaching it (like MT5's Inputs tab). name as list_eas shows it."""
    return _call(account_id, 'mt5_probe', name=name, symbol=symbol)


@mcp.tool()
def attach_ea(account_id: int, name: str, symbol: str, timeframe: str = 'H1', inputs: dict | None = None) -> dict:
    """Attach an EA (name as list_eas shows it, e.g. 'Uploaded\\MyEA') to its own chart; it trades 24/7 and starts in ~1-2 s.
    inputs: values that differ from the defaults, e.g. {"Lots": "0.05"} (names from ea_inputs)."""
    return _call(account_id, 'mt5_attach', name=name, symbol=symbol, period=timeframe,
                 **({'inputs': {k: str(v) for k, v in inputs.items()}} if inputs else {}))


@mcp.tool()
def set_ea_inputs(account_id: int, ea_id: str, inputs: dict) -> dict:
    """Change an attached EA's inputs, e.g. {"Lots": "0.05"}. Names must be the EA's own (see list_eas). Only that EA restarts (~1 s)."""
    return _call(account_id, 'mt5_inputs', eid=ea_id, inputs={k: str(v) for k, v in inputs.items()})


@mcp.tool()
def remove_ea(account_id: int, ea_id: str) -> dict:
    """Detach one EA; the account's other EAs keep running."""
    return _call(account_id, 'mt5_detach', eid=ea_id)


# ---------------------------------------------------------------- copy trading
@mcp.tool()
def start_copying(master_account_id: int, follower_account_id: int, mode: str = 'multiplier', value: float = 1.0,
                  max_lot: float = 0, reverse: bool = False) -> dict:
    """Copy every new trade of the master to the follower. mode 'multiplier' (lot x value) or 'fixed' (value lots); max_lot caps it."""
    return _api('POST', '/api/links', dict(master=master_account_id, follower=follower_account_id, mode=mode, value=value, max_lot=max_lot, reverse=reverse))


@mcp.tool()
def pause_copying(link_id: int, paused: bool = True) -> dict:
    """Pause or resume one copy link (ids are in overview().links)."""
    return _api('POST', f'/api/links/{link_id}', dict(active=not paused))


@mcp.tool()
def stop_copying(link_id: int) -> dict:
    """Remove a copy link. Positions already copied stay open on the follower."""
    return _api('DELETE', f'/api/links/{link_id}')


# ---------------------------------------------------------------- accounts
@mcp.tool()
def account_power(account_id: int, on: bool) -> dict:
    """Start or stop a hosted terminal (stopping pauses its EAs)."""
    return _api('POST', f'/api/accounts/{account_id}/power', dict(on=on))


def main():
    mcp.run()


if __name__ == '__main__':
    main()
