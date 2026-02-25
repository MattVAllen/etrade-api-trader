# E*TRADE API Trader

A lightweight command-line tool for executing stock trades through the E\*TRADE API via a simple CSV file. Authenticate once, review your orders, confirm, and execute — SELLs always run before BUYs.

---

## Features

- ✅ OAuth 1.0a authentication (no browser automation required)
- ✅ Token persistence — PIN entry only required once per trading day
- ✅ CSV-driven trade input — bring your own trade list
- ✅ Order preview before execution
- ✅ Automatic SELL-before-BUY ordering
- ✅ Sandbox and production environment support
- ✅ Multi-account selection

---

## Requirements

- Python 3.10+
- Windows (credential storage uses Windows Credential Manager)
- E\*TRADE developer account — [register here](https://developer.etrade.com)
- Microsoft C++ Build Tools *(required by the `ecos` dependency)*

---

## Installation

```cmd
git clone https://github.com/yourusername/etrade-api-trader.git
cd etrade-api-trader
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Setup

### 1. Get API credentials

Create an application at the [E\*TRADE Developer Portal](https://developer.etrade.com) to receive a `consumer_key` and `consumer_secret`. E\*TRADE provides separate credentials for sandbox and production — store them separately.

### 2. Store your credentials

Run this once in Python (in your activated virtual environment) to save your credentials to Windows Credential Manager.

**Sandbox:**
```python
import keyring, json
creds = {"consumer_key": "YOUR_SANDBOX_KEY", "consumer_secret": "YOUR_SANDBOX_SECRET"}
keyring.set_password("etrade_sandbox", "credentials", json.dumps(creds))
```

**Production:**
```python
import keyring, json
creds = {"consumer_key": "YOUR_PROD_KEY", "consumer_secret": "YOUR_PROD_SECRET"}
keyring.set_password("etrade_prod", "credentials", json.dumps(creds))
```

To update credentials later, run the same snippet with your new values — it overwrites the existing entry.

---

## Usage

### Sandbox (for testing — recommended first)

```cmd
python run_trades.py trades.csv
```

### Production

```cmd
python run_trades.py trades.csv --env prod
```

### What to expect

1. On the first run of each trading day, a URL is printed in the terminal — open it in your browser, log in to E\*TRADE, approve access, and paste the PIN back into the terminal (~30 seconds)
2. Subsequent runs the same day reuse saved tokens automatically — no PIN needed
3. Your accounts are listed — enter the number to select which account to trade in
4. A trade summary table is displayed for review
5. Type `yes` to execute — each order is previewed then placed
6. A final success/failure count is reported

---

## CSV Format

All trades are driven by a CSV file. Only three columns are required — the rest are optional and will fall back to the defaults shown below.

### Required columns

```csv
Symbol,Action,Quantity
AAPL,SELL,10
MSFT,BUY,5
NVDA,BUY,8
```

### Optional columns and their defaults

If a column is omitted or left blank, the following defaults apply:

| Column | Default | Options |
|---|---|---|
| PriceType | `MARKET` | `MARKET`, `LIMIT`, `STOP`, `STOP_LIMIT`, `MARKET_ON_CLOSE` |
| LimitPrice | — | Any decimal (required if PriceType is `LIMIT`) |
| StopPrice | — | Any decimal (required if PriceType is `STOP` or `STOP_LIMIT`) |
| OrderTerm | `GOOD_FOR_DAY` | `GOOD_FOR_DAY`, `GOOD_UNTIL_CANCEL`, `IMMEDIATE_OR_CANCEL`, `FILL_OR_KILL` |
| MarketSession | `REGULAR` | `REGULAR`, `EXTENDED` |
| AllOrNone | `FALSE` | `TRUE`, `FALSE` |
| RoutingDestination | `AUTO` | `AUTO`, `ARCA`, `NSDQ`, `NYSE` |

### Full example

```csv
Symbol,Action,Quantity,PriceType,LimitPrice,StopPrice,OrderTerm,MarketSession,AllOrNone,RoutingDestination
AAPL,SELL,10,LIMIT,185.00,,GOOD_UNTIL_CANCEL,REGULAR,FALSE,AUTO
MSFT,BUY,5,MARKET,,,GOOD_FOR_DAY,REGULAR,FALSE,AUTO
```

**Notes:**
- Column names with or without spaces are both accepted (`Price Type` or `PriceType`)
- The order of rows in the CSV does not matter — SELLs always execute before BUYs regardless

---

## Authentication Details

This tool uses the OAuth 1.0a PIN-based flow required by E\*TRADE.

| Scenario | Behavior |
|---|---|
| First run of the trading day | PIN flow — ~30 seconds |
| Subsequent runs same day | Silent token renewal — no action needed |
| After midnight Eastern time | Tokens expire — PIN flow required again |

Tokens are saved locally at:
- Sandbox: `~/.etrade/tokens.sandbox.json`
- Production: `~/.etrade/tokens.prod.json`

### E\*TRADE OAuth quirks

If you're building on top of this or troubleshooting auth issues, these are the non-obvious implementation details:

- `callback_uri="oob"` must be passed in the OAuth header — **not** as a URL query parameter
- All three token endpoints (`request_token`, `access_token`, `renew`) always use `https://api.etrade.com`, even in sandbox mode
- Only data calls (accounts, orders) use `https://apisb.etrade.com` for sandbox
- E\*TRADE returns URL-encoded tokens — always decode with `urllib.parse.unquote()` before use

---

## Project Structure

```
etrade-api-trader/
├── auth/
│   ├── __init__.py
│   └── oauth_etrade.py      # OAuth 1.0a authentication module
├── tests/
│   ├── test_oauth.py        # Auth test (no trades placed)
│   └── test_trade.py        # Trade execution test (sandbox only)
├── utils/
│   └── csv_reader.py        # CSV trade reader
├── run_trades.py            # Main execution script
├── requirements.txt
└── README.md
```

---

## Dependencies

This project uses [pyetrade](https://github.com/jessecooper/pyetrade) (v2.1.1) as the E\*TRADE API wrapper. Note that pyetrade is currently in maintenance-only status — it is functional but not actively developed.

---

## Disclaimer

This tool places real stock orders. Always test in sandbox before running in production. You are solely responsible for any trades executed. This is not financial advice.
