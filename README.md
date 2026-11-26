# HostMT5 MCP server

[![HostMT5 MCP server MCP server – quality and maintenance score on Glama](https://glama.ai/mcp/servers/jayadevrana/hostmt5-mcp/badges/score.svg)](https://glama.ai/mcp/servers/jayadevrana/hostmt5-mcp)

An MCP server for **MetaTrader 5**. It lets Claude, ChatGPT, Cursor, VS Code and other MCP clients work with your MT5 accounts hosted on [HostMT5](https://hostmt5.com): read accounts, prices and history, trade, write MQL5 Expert Advisors and compile, run and tune them, read their logs, stop and resume trading, and set up copy trading, TradingView webhooks and alerts.

HostMT5 runs a real MT5 terminal for each account in the cloud, so your EAs keep trading 24/7 without your PC. It works with any broker that offers MT5, demo or live. **HostMT5 is free during launch** (up to 3 MT5 accounts, no card).

> ⚠️ Orders placed on a live account are real. The trading tools say so in their descriptions. Start on a demo account, or use a read-only key.

## Get a key

1. Create a free account at [hostmt5.com](https://hostmt5.com) and add an MT5 account.
2. In the dashboard, open **AI & API** and create an API key (`mc_...`).

A **read-only key** gives the assistant only the read tools: use one when you want analysis without any chance of a trade.

## Connect: remote URL (recommended)

HostMT5 hosts the MCP server itself. Nothing to install.

| | |
|---|---|
| URL | `https://hostmt5.com/mcp` with header `Authorization: Bearer mc_your_key` (Streamable HTTP) |
| URL-only apps | `https://hostmt5.com/mcp/mc_your_key`. The URL then is the password, so keep it private. |

**Claude Code**

```
claude mcp add --transport http hostmt5 https://hostmt5.com/mcp --header "Authorization: Bearer mc_your_key"
```

**Claude.ai and ChatGPT**

```
Claude.ai: Settings → Connectors → Add custom connector
ChatGPT:   Settings → Connectors → Advanced → Developer mode → Create

Server URL:  https://hostmt5.com/mcp/mc_your_key
```

**Cursor** (`~/.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "hostmt5": {
      "url": "https://hostmt5.com/mcp",
      "headers": { "Authorization": "Bearer mc_your_key" }
    }
  }
}
```

**VS Code** (`.vscode/mcp.json`)

```json
{
  "servers": {
    "hostmt5": {
      "type": "http",
      "url": "https://hostmt5.com/mcp",
      "headers": { "Authorization": "Bearer mc_your_key" }
    }
  }
}
```

## Connect: local stdio bridge (for apps that only run local servers)

Some apps, such as Claude Desktop with a JSON config, only start MCP servers as local commands. This repo is a small stdio bridge for them: it forwards every message to `https://hostmt5.com/mcp`, so you always get the current tools. Python 3.8+, no dependencies.

**With [uv](https://docs.astral.sh/uv/)** (Claude Desktop: Settings → Developer → Edit config)

```json
{
  "mcpServers": {
    "hostmt5": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/jayadevrana/hostmt5-mcp", "hostmt5-mcp"],
      "env": { "HOSTMT5_KEY": "mc_your_key" }
    }
  }
}
```

**Without uv**: download [`hostmt5_mcp.py`](hostmt5_mcp.py) (or the same bridge from the HostMT5 docs, [`mcp_server.py`](https://hostmt5.com/sdk/mcp_server.py)) and run it with Python:

```json
{
  "mcpServers": {
    "hostmt5": {
      "command": "python",
      "args": ["C:/Users/you/Downloads/hostmt5_mcp.py"],
      "env": { "HOSTMT5_KEY": "mc_your_key" }
    }
  }
}
```

| Variable | Required | Default |
|---|---|---|
| `HOSTMT5_KEY` | yes | none (Dashboard → AI & API) |
| `HOSTMT5_URL` | no | `https://hostmt5.com` |

Without a valid key the bridge still answers `initialize` and `tools/list`, so clients and directories can inspect it; every tool call then returns the key error.

## Tools (39)

Every tool takes the `account_id` from `get_overview` where it acts on one account.

| Area | Tools |
|---|---|
| Account and plan | `get_overview` (start here: plan, accounts, copy links), `get_account`, `add_account`, `relogin_account`, `power_account` (start or stop a hosted terminal), `remove_account`, `get_stats` (profit, win rate, profit factor, drawdown) |
| Trading control | `stop_trading` (kill switch: Algo Trading off, webhook and copy paused, optionally close everything), `resume_trading` |
| Market data | `find_symbols`, `symbol_info`, `get_quotes`, `get_bars` (M1 to MN1), `get_ticks` |
| Positions, orders, history | `get_positions`, `get_orders`, `get_history`, `place_order` (market, limit, stop; real on live accounts), `modify_position`, `close_position` (full or partial), `close_positions`, `cancel_order` |
| Expert Advisors | `list_eas`, `upload_ea` (MQL5 source compiled on the server, errors with line numbers; or a .ex5), `get_ea_source`, `ea_inputs`, `attach_ea`, `set_ea_inputs`, `remove_ea`, `get_logs` (Experts and Journal) |
| Copy trading | `start_copying` (multiplier, fixed, balance, equity, risk and more; max lot, reverse), `update_copying` (change, pause, resume), `stop_copying` |
| TradingView webhooks | `get_webhooks`, `create_webhook`, `webhook_settings`, `send_signal` |
| Alerts | `get_alerts`, `set_alerts` (email, Telegram, auto-restart, drawdown and margin level) |

The live list with descriptions: [hostmt5.com/docs#mcp](https://hostmt5.com/docs#mcp).

## Things to ask your assistant

- "Show my open positions on every account, and the floating P&L."
- "Show me the last 200 H1 bars of XAUUSD and summarise the trend."
- "Write an EA that buys XAUUSD on an H1 RSI cross under 30, compile it and attach it to my demo with 0.01 lots."
- "Stop all trading on my real account and close everything."
- "Copy account 1 to account 3 at half size."

## How it works

Every tool is one call to the HostMT5 API with your key, so the assistant gets exactly the checks, limits and key scope the dashboard has. If you add an MT5 account through `add_account`, the assistant sees the password you give it; add accounts in the dashboard instead to keep the password out of the chat.

More: [Let an AI assistant work with your MT5 account](https://hostmt5.com/learn/mt5-ai-assistant-mcp) · [Run an MT5 EA 24/7 without your PC](https://hostmt5.com/learn/run-mt5-ea-24-7) · [Free MT5 VPS](https://hostmt5.com/learn/free-mt5-vps) · [API docs](https://hostmt5.com/docs)

## Licence

MIT. MetaTrader is a trademark of MetaQuotes, which does not endorse HostMT5. HostMT5 provides no investment advice.
