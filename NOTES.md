# pyetrade Notes & Workarounds

This file documents the differences between pyetrade's actual behavior and what you might expect from the E\*TRADE API documentation, along with the fixes applied in this project. Kept here for reference and as a basis for a future contribution back to the pyetrade library.

---

## Parameter Naming Mismatch

pyetrade uses different parameter names than the E\*TRADE API documentation. If you initialize `ETradeAccounts` or `ETradeOrder` using the names from the E\*TRADE docs, it will silently fail.

| E\*TRADE Docs | pyetrade Actual |
|---|---|
| `consumer_key` | `client_key` |
| `consumer_secret` | `client_secret` |
| `oauth_token` | `resource_owner_key` |
| `oauth_token_secret` | `resource_owner_secret` |

**Correct usage:**
```python
accounts = ETradeAccounts(
    client_key=cfg.consumer_key,
    client_secret=cfg.consumer_secret,
    resource_owner_key=access_token,
    resource_owner_secret=access_secret,
    dev=True,   # True = sandbox, False = production
)
```

---

## OAuth Endpoint Behavior

pyetrade's built-in OAuth flow does not handle E\*TRADE's specific requirements correctly, which is why this project uses a custom `oauth_etrade.py` module instead. The issues:

- **Callback URI** — E\*TRADE requires `callback_uri="oob"` to be passed in the OAuth header as part of the signature. pyetrade passes it as a query parameter, which E\*TRADE rejects.
- **Sandbox OAuth URLs** — pyetrade incorrectly routes OAuth token endpoints to the sandbox URL (`apisb.etrade.com`) when `dev=True`. E\*TRADE requires all three token endpoints (`request_token`, `access_token`, `renew`) to always use `https://api.etrade.com` regardless of environment. Only data API calls use the sandbox URL.
- **URL-encoded tokens** — E\*TRADE returns OAuth tokens with URL encoding (`%2F`, `%2B`, `%3D`, etc.). pyetrade does not decode these, which causes signature failures on subsequent calls. Fix: decode all tokens with `urllib.parse.unquote()` immediately after receiving them.

---

## Token Renewal

pyetrade's renewal method works correctly once tokens are properly decoded (see above). No structural changes were needed — just ensure tokens are unquoted before being passed in.

---

## Environment Switching (`dev` flag)

pyetrade uses `dev=True` for sandbox and `dev=False` for production. This controls which base URL is used for data API calls only. The OAuth token endpoints are unaffected by this flag (they always use production URLs regardless — see above).

---

## Future Contribution

These findings could be contributed back to [jessecooper/pyetrade](https://github.com/jessecooper/pyetrade) as either:
- A pull request fixing the OAuth callback and URL encoding handling
- A documentation update clarifying the correct parameter names and endpoint behavior

Note: pyetrade is currently in maintenance-only status as of early 2026.
