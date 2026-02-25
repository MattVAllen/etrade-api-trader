"""
Test OAuth authentication before integrating with bot
"""

from auth.oauth_etrade import load_config_from_keyring, authenticate
from pyetrade import ETradeAccounts


def test_authentication():
    print("E*TRADE OAuth Test")
    print("=" * 50)

    # Load config
    cfg = load_config_from_keyring(env="sandbox")
    print(f"Environment: {cfg.env}")
    print(f"Base URL: {cfg.base_url}")

    # Authenticate
    access_token, access_secret = authenticate(cfg)

    # Test API call - list accounts
    print("\nTesting API call: List Accounts")
    print("-" * 50)

    accounts = ETradeAccounts(
        client_key=cfg.consumer_key,
        client_secret=cfg.consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_secret,
        dev=True
    )

    account_list = accounts.list_accounts()
    print(f"Successfully retrieved accounts")
    print(account_list)

    print("\n" + "=" * 50)
    print("OAuth authentication test PASSED")


if __name__ == "__main__":
    test_authentication()