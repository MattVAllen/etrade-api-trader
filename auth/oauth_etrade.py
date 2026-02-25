import json
import keyring
import time
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass
from urllib.parse import unquote

import requests
from requests_oauthlib import OAuth1Session


@dataclass(frozen=True)
class ETradeConfig:
    """E*TRADE API configuration."""
    env: str  # "sandbox" or "prod"
    base_url: str
    consumer_key: str
    consumer_secret: str
    token_path: Path


def load_config_from_keyring(env: str = "sandbox") -> ETradeConfig:
    if env not in ("sandbox", "prod"):
        raise ValueError("env must be 'sandbox' or 'prod'")

    # Separate keyring entries for sandbox vs prod
    if env == "sandbox":
        keyring_service = "etrade_sandbox"
        base_url = "https://apisb.etrade.com"
        token_path = Path.home() / ".etrade" / "tokens.sandbox.json"
    else:
        keyring_service = "etrade_prod"
        base_url = "https://api.etrade.com"
        token_path = Path.home() / ".etrade" / "tokens.prod.json"

    credentials = keyring.get_password(keyring_service, "credentials")
    if not credentials:
        raise ValueError(
            f"No E*TRADE {env} credentials found in keyring "
            f"(service: '{keyring_service}'). "
            f"Store them with: keyring.set_password('{keyring_service}', 'credentials', "
            f"json.dumps({{'consumer_key': '...', 'consumer_secret': '...'}}))"
        )

    creds = json.loads(credentials)
    consumer_key = creds.get("consumer_key")
    consumer_secret = creds.get("consumer_secret")

    if not consumer_key or not consumer_secret:
        raise ValueError(f"Missing consumer_key or consumer_secret in keyring (service: '{keyring_service}')")

    token_path.parent.mkdir(parents=True, exist_ok=True)

    return ETradeConfig(
        env=env,
        base_url=base_url,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        token_path=token_path,
    )


def load_tokens(cfg: ETradeConfig) -> Tuple[Optional[str], Optional[str]]:
    """Load saved OAuth tokens."""
    if not cfg.token_path.exists():
        return None, None
    data = json.loads(cfg.token_path.read_text())
    return data.get("oauth_token"), data.get("oauth_token_secret")


def save_tokens(cfg: ETradeConfig, oauth_token: str, oauth_token_secret: str) -> None:
    """Save OAuth tokens for future use."""
    payload = {
        "oauth_token": oauth_token,
        "oauth_token_secret": oauth_token_secret,
        "saved_at_epoch": int(time.time()),
    }
    cfg.token_path.write_text(json.dumps(payload, indent=2))
    print(f"Tokens saved to {cfg.token_path}")


def oauth_session(
    cfg: ETradeConfig,
    token: Optional[str] = None,
    token_secret: Optional[str] = None,
    verifier: Optional[str] = None,
    callback_uri: Optional[str] = None,
) -> OAuth1Session:
    """Create OAuth1Session for E*TRADE API."""
    return OAuth1Session(
        client_key=cfg.consumer_key,
        client_secret=cfg.consumer_secret,
        resource_owner_key=token,
        resource_owner_secret=token_secret,
        verifier=verifier,
        callback_uri=callback_uri,
    )


def get_request_token(cfg: ETradeConfig) -> Tuple[str, str]:
    """Get request token (Step 1 of OAuth flow)."""
    sess = oauth_session(cfg, callback_uri="oob")
    url = "https://api.etrade.com/oauth/request_token"
    resp = sess.get(url, timeout=30)
    resp.raise_for_status()
    data = dict(x.split("=", 1) for x in resp.text.split("&"))
    return unquote(data["oauth_token"]), unquote(data["oauth_token_secret"])


def get_authorize_url(cfg: ETradeConfig, request_token: str) -> str:
    """Build authorization URL (Step 2 of OAuth flow)."""
    return f"https://us.etrade.com/e/t/etws/authorize?key={cfg.consumer_key}&token={request_token}"


def exchange_access_token(
    cfg: ETradeConfig,
    request_token: str,
    request_secret: str,
    verifier_pin: str,
) -> Tuple[str, str]:
    """Exchange PIN for access token (Step 3 of OAuth flow)."""
    sess = oauth_session(cfg, token=request_token, token_secret=request_secret, verifier=verifier_pin)
    url = "https://api.etrade.com/oauth/access_token"
    resp = sess.get(url, timeout=30)
    resp.raise_for_status()
    data = dict(x.split("=", 1) for x in resp.text.split("&"))
    return unquote(data["oauth_token"]), unquote(data["oauth_token_secret"])


def renew_access_token(cfg: ETradeConfig, access_token: str, access_secret: str) -> None:
    """Renew inactive access token (if within same day)."""
    sess = oauth_session(cfg, token=access_token, token_secret=access_secret)
    url = "https://api.etrade.com/oauth/renew_access_token"
    resp = sess.get(url, timeout=30)
    resp.raise_for_status()


def authenticate(cfg: ETradeConfig, force_new: bool = False) -> Tuple[str, str]:
    """Ensure valid OAuth tokens, authenticating if necessary."""
    if not force_new:
        access_token, access_secret = load_tokens(cfg)

        if access_token and access_secret:
            try:
                renew_access_token(cfg, access_token, access_secret)
                print("Existing tokens renewed successfully")
                return access_token, access_secret
            except Exception:
                print("Token renewal failed (likely expired). Re-authenticating...")

    print("\nStarting OAuth authentication flow...")
    print("=" * 50)

    print("Step 1: Getting request token...")
    req_token, req_secret = get_request_token(cfg)
    print("Request token received")

    print("\nStep 2: User authorization required")
    auth_url = get_authorize_url(cfg, req_token)
    print(f"  1. Open this URL in your browser:")
    print(f"     {auth_url}")
    print(f"  2. Log into E*TRADE and approve access")
    print(f"  3. Copy the verification code (PIN)")
    print()

    verifier = input("Enter the verification code (PIN): ").strip()

    print("\nStep 3: Exchanging PIN for access token...")
    access_token, access_secret = exchange_access_token(cfg, req_token, req_secret, verifier)
    print("Access token received")

    save_tokens(cfg, access_token, access_secret)
    print("Authentication complete!")
    print("=" * 50)

    return access_token, access_secret


def get_oauth_session(env: str = "sandbox") -> OAuth1Session:
    """Get an authenticated OAuth session ready for API calls."""
    cfg = load_config_from_keyring(env)
    access_token, access_secret = authenticate(cfg)
    return oauth_session(cfg, token=access_token, token_secret=access_secret)