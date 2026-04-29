# Credentials & Configuration

OAuth credentials and environment setup for EAT (E-Trade API).
SAP Replicator directory layout is in SAAPPR → Excel Workbook Reference.md.

---

## Windows Keyring Setup

OAuth credentials are stored in Windows Keyring, encrypted via Windows DPAPI.

### First-Time Setup

**Sandbox Environment:**
```python
import keyring
import json

creds = {
    "consumer_key": "YOUR_SANDBOX_KEY_HERE",
    "consumer_secret": "YOUR_SANDBOX_SECRET_HERE"
}

keyring.set_password("etrade_sandbox", "credentials", json.dumps(creds))
print("Sandbox credentials stored in keyring")
```

**Production Environment:**
```python
import keyring
import json

creds = {
    "consumer_key": "YOUR_PROD_KEY_HERE",
    "consumer_secret": "YOUR_PROD_SECRET_HERE"
}

keyring.set_password("etrade_prod", "credentials", json.dumps(creds))
print("Production credentials stored in keyring")
```

---

## Token Storage

OAuth tokens are cached locally in encrypted JSON files.

**Sandbox tokens:**
```
~/.etrade/tokens.sandbox.json
```

**Production tokens:**
```
~/.etrade/tokens.prod.json
```

**Token file format:**
```json
{
  "oauth_token": "abc123...",
  "oauth_token_secret": "xyz789...",
  "oauth_token_expires_in": "86400",
  "timestamp": "2026-03-01T10:00:00"
}
```

**Expiration:**
- Tokens expire at midnight US Eastern time
- Auto-renewal happens automatically on next run
- Manual refresh only needed if tokens are deleted

---

## Environment Variables (Optional)

Set to avoid `--env` flag on every run:
```shell
set ETRADE_ENV=prod
```

Then run without `--env`:
```bash
python run_trades.py Trades.csv
```

Default is sandbox if not set.

---

## Python Virtual Environment

**Activate:**
```bash
cd EAT
venv\Scripts\activate
```

**Deactivate:**
```bash
deactivate
```

**Re-create venv (if broken):**
```bash
cd EAT
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Keyring Troubleshooting

### "keyring.errors.InitError"

**Cause:** Keyring not initialized or Windows Credential Manager issue
**Fix:**
```python
import keyring
from keyring.backends import windows
keyring.set_keyring(windows.WinVaultKeyring())
```
Then retry your operation.

### "No password provided"

**Cause:** Credentials not stored or wrong key name
**Fix:**
```python
import keyring
print(keyring.backends.windows.WinVaultKeyring().get_credential("etrade_prod", "credentials"))
```
Re-store if missing.

### Clear credentials (for testing)

```python
import keyring
keyring.delete_password("etrade_prod", "credentials")
keyring.delete_password("etrade_sandbox", "credentials")
```
Then re-store with new credentials.
