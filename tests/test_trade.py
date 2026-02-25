"""
Test trade execution in sandbox - BUY and SELL
"""

import uuid
from auth.oauth_etrade import load_config_from_keyring, authenticate
from pyetrade import ETradeAccounts, ETradeOrder


def place_order(orders, account_id_key, symbol, action, quantity):
    """Preview and place a single order."""
    client_order_id = uuid.uuid4().hex[:20]
    order_params = dict(
        accountIdKey=account_id_key,
        symbol=symbol,
        orderAction=action,
        clientOrderId=client_order_id,
        priceType="MARKET",
        quantity=quantity,
        marketSession="REGULAR",
        orderTerm="GOOD_FOR_DAY",
    )

    print(f"\nPreviewing: {action} {quantity} {symbol} @ MARKET")
    preview = orders.preview_equity_order(**order_params)
    preview_id = preview["PreviewOrderResponse"]["PreviewIds"]["previewId"]
    print(f"  Preview ID: {preview_id}")

    print(f"  Placing order...")
    result = orders.place_equity_order(**order_params, previewId=preview_id)
    order_id = result["PlaceOrderResponse"]["OrderIds"]["orderId"]
    msg = result["PlaceOrderResponse"]["Order"]["messages"]["Message"]["description"]
    print(f"  Order ID: {order_id} - {msg}")
    return order_id


def test_trade():
    print("E*TRADE Sandbox Trade Test - SELL and BUY")
    print("=" * 50)

    cfg = load_config_from_keyring(env="sandbox")
    access_token, access_secret = authenticate(cfg)

    accounts = ETradeAccounts(
        client_key=cfg.consumer_key,
        client_secret=cfg.consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_secret,
        dev=True,
    )
    account_list = accounts.list_accounts()
    acct = account_list["AccountListResponse"]["Accounts"]["Account"][0]
    account_id_key = acct["accountIdKey"]
    print(f"Using account: {acct['accountDesc']} ({acct['accountId']})")

    orders = ETradeOrder(
        client_key=cfg.consumer_key,
        client_secret=cfg.consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_secret,
        dev=True,
    )

    # Execute SELLs first, then BUYs
    print("\n--- SELL ORDERS ---")
    place_order(orders, account_id_key, "POWL", "SELL", 8)

    print("\n--- BUY ORDERS ---")
    place_order(orders, account_id_key, "DY", "BUY", 5)
    place_order(orders, account_id_key, "NEM", "BUY", 18)

    print("\n" + "=" * 50)
    print("All orders placed successfully!")


if __name__ == "__main__":
    test_trade()