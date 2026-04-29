## Critical OAuth Rules (E*TRADE Specific)

**Callback URI:**
- `callback_uri="oob"` must be in OAuth header
- NOT as a query parameter

**Token Endpoints:**
- All three token endpoints always use `https://api.etrade.com`
- This is true even in sandbox environment
- Only data calls use `https://apisb.etrade.com` for sandbox

**Token Encoding:**
- E*TRADE returns URL-encoded tokens
- Always decode with `urllib.parse.unquote()`
- Failure to decode causes OAuth failures

**Token Expiration:**
- Tokens expire at midnight US Eastern time
- Auto-renewal is cheap and reliable
- No need to re-authenticate unless cache is cleared

---

## pyetrade Parameter Names

pyetrade uses different parameter names than E*TRADE docs. This is a common source of confusion.

| pyetrade | E*TRADE Docs | Used In |
|---|---|---|
| `client_key` | `consumer_key` | OAuth initialization |
| `client_secret` | `consumer_secret` | OAuth initialization |
| `resource_owner_key` | `oauth_token` | API calls |
| `resource_owner_secret` | `oauth_token_secret` | API calls |
| `dev=True` | Sandbox | Quote/order endpoints |
| `dev=False` | Production | Quote/order endpoints |

---

## pyetrade Known Issues

**Built-in OAuth flow doesn't work:**
- E*TRADE's OAuth requirements are specific enough that pyetrade's default flow fails
- Solution: Use custom `oauth_etrade.py` module instead

**Price quote reliability:**
- `detail_flag=None` (defaults to "all") is most reliable
- Other values sometimes return incomplete data

**Maintenance status:**
- As of early 2026, pyetrade is maintenance-only
- No active development; only critical bug fixes
- Still works reliably for trade execution and quote retrieval

---

## Keyring Storage Pattern

Both projects use Windows Keyring to store OAuth credentials securely.

**Sandbox Entry:**
```python
import keyring, json
creds = {"consumer_key": "YOUR_KEY", "consumer_secret": "YOUR_SECRET"}
keyring.set_password("etrade_sandbox", "credentials", json.dumps(creds))
```

**Production Entry:**
```python
import keyring, json
creds = {"consumer_key": "YOUR_KEY", "consumer_secret": "YOUR_SECRET"}
keyring.set_password("etrade_prod", "credentials", json.dumps(creds))
```

**Retrieval:**
```python
import keyring, json
creds = json.loads(keyring.get_password("etrade_prod", "credentials"))
consumer_key = creds["consumer_key"]
consumer_secret = creds["consumer_secret"]
```

---

## PIN Entry Flow

First run of the day (or cache cleared):
1. User runs `python run_trades.py trades.csv --env prod`
2. OAuth handler loads cached tokens from keyring
3. Tokens are expired (or missing)
4. System opens browser to E*TRADE OAuth consent page
5. User logs in and approves access
6. E*TRADE returns a PIN (~6 characters)
7. User pastes PIN into terminal prompt
8. Tokens are fetched and cached
9. Script continues to trade execution

**Time:** ~30 seconds one-time per day

Subsequent runs same day:
- Tokens are valid and cached
- No browser/PIN entry required
- Tokens are auto-renewed
- Script runs to completion immediately
