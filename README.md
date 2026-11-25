# HostMT5 MCP server

[![HostMT5 MCP server MCP server – quality and maintenance score on Glama](https://glama.ai/mcp/servers/jayadevrana/hostmt5-mcp/badges/score.svg)](https://glama.ai/mcp/servers/jayadevrana/hostmt5-mcp)

An MCP server for **MetaTrader 5**. It lets Claude, ChatGPT desktop, Cursor and other MCP clients work with your MT5 accounts hosted on [HostMT5](https://hostmt5.com): read balances, positions and price history, place and manage orders, upload and attach Expert Advisors, and set up copy trading between accounts.

HostMT5 runs a real MT5 terminal for each account in the cloud, so your EAs keep trading 24/7 and the assistant reaches the terminal over HTTPS. It works with any broker that offers MT5, demo or live. **HostMT5 is free during launch** (up to 3 MT5 accounts, no card).

> ⚠️ Orders placed on a live account are real. The trading tools say so in their descriptions. Start on a demo account.

## Setup

1. Create a free account at [hostmt5.com](https://hostmt5.com) and add an MT5 account.
2. In the dashboard, open **API keys** and create a key.
3. Add the server to your MCP client. It needs [uv](https://docs.astral.sh/uv/); nothing else to install.

**Claude Desktop, Cursor and other JSON configs**

```json
{
  "mcpServers": {
    "hostmt5": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/jayadevrana/hostmt5-mcp", "hostmt5-mcp"],
      "env": { "HOSTMT5_KEY": "mc_your_key_here" }
    }
  }
}
```

**Claude Code**

```
claude mcp add hostmt5 -e HOSTMT5_KEY=mc_your_key_here -- uvx --from git+https://github.com/jayadevrana/hostmt5-mcp hostmt5-mcp
```

**Without uv**

```
pip install "mcp<2" httpx
python hostmt5_mcp.py      # with HOSTMT5_KEY set in the environment
```

| Variable | Required | Default |
|---|---|---|
| `HOSTMT5_KEY` | yes | none (dashboard > API keys) |
| `HOSTMT5_URL` | no | `https://hostmt5.com` |

## Tools

| Area | Tools |
|---|---|
| Overview | `overview`: your accounts, their status, and your copy-trading links and recent copy activity |
| Market data | `account_state`, `price_history` (M1 to MN1), `trade_history` (last 30 days), `find_symbols`, `watch_symbol` |
| Trading (real on live accounts) | `market_order`, `pending_order` (buy/sell limit and stop), `close_position` (full or partial), `cancel_order`, `modify_position` |
| Expert Advisors | `list_eas`, `upload_ea` (.ex5, or .mq5 compiled on the server), `ea_inputs`, `attach_ea`, `set_ea_inputs`, `remove_ea` |
| Copy trading | `start_copying` (multiplier or fixed lot, max lot, reverse), `pause_copying`, `stop_copying` |
| Terminals | `account_power` (start or stop a hosted terminal) |

## Things to ask your assistant

- "What's open on my demo account, and what's the floating P&L?"
- "Show me the last 200 H1 bars of XAUUSD and summarise the trend."
- "Upload ~/EAs/MyGrid.ex5, show me its inputs, then attach it to EURUSD M15 with Lots = 0.02."
- "Copy every trade from account 12 to account 15 at half the lot size, capped at 0.5 lots."

## How it works

The server is a thin client for the HostMT5 REST API. Each tool sends one authenticated HTTPS request, and HostMT5 applies the same checks as the website. Your broker password is never sent to this server or to the assistant.

More: [Let an AI assistant work with your MT5 account](https://hostmt5.com/learn/mt5-ai-assistant-mcp) · [Run an MT5 EA 24/7 without your PC](https://hostmt5.com/learn/run-mt5-ea-24-7) · [Free MT5 VPS](https://hostmt5.com/learn/free-mt5-vps)

## Licence

MIT. MetaTrader is a trademark of MetaQuotes, which does not endorse HostMT5. HostMT5 provides no investment advice.
