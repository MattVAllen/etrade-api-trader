"""
E*TRADE Trade Executor
Reads trades from CSV, authenticates, previews, and executes.

Usage:
    python run_trades.py trades.csv              (sandbox, default)
    python run_trades.py trades.csv --env prod   (production)
"""

import sys
import uuid
from auth.oauth_etrade import load_config_from_keyring, authenticate
from utils.csv_reader import read_trades, TradeInstruction
from pyetrade import ETradeAccounts, ETradeOrder


def normalize(obj):
    """If pyetrade returns a list instead of a dict, unwrap it."""
    if isinstance(obj, list):
        return obj[0] if obj else {}
    return obj


def safe_get(obj, *keys):
    """
    Traverse nested keys safely, unwrapping any lists along the way.
    e.g. safe_get(resp, "PreviewOrderResponse", "PreviewIds", "previewId")
    """
    for key in keys:
        if obj is None:
            return None
        obj = normalize(obj)
        obj = obj.get(key)
    return normalize(obj) if isinstance(obj, (list, dict)) else obj


def get_account(cfg, access_token, access_secret):
    """Get account list and let user pick one."""
    accounts = ETradeAccounts(
        client_key=cfg.consumer_key,
        client_secret=cfg.consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_secret,
        dev=(cfg.env == "sandbox"),
    )
    account_list = accounts.list_accounts()
    accts = account_list["AccountListResponse"]["Accounts"]["Account"]

    # Filter to active accounts
    active = [a for a in accts if a.get("accountStatus") == "ACTIVE"]

    if len(active) == 1:
        acct = active[0]
        print(f"Using account: {acct['accountDesc']} ({acct['accountId']})")
        return acct["accountIdKey"]

    print("\nAvailable accounts:")
    for i, a in enumerate(active, 1):
        print(f"  {i}. {a['accountDesc']} - {a['accountId']} ({a['accountMode']})")

    while True:
        raw = input("Select account (enter number 1-{}, or account ID): ".format(len(active))).strip()
        if raw.isdigit() and 1 <= int(raw) <= len(active):
            acct = active[int(raw) - 1]
            break
        match = [a for a in active if a["accountId"] == raw]
        if match:
            acct = match[0]
            break
        print(f"  Invalid selection. Try again.")

    print(f"Using account: {acct['accountDesc']} ({acct['accountId']})")
    return acct["accountIdKey"]


def preview_and_place(orders_client, account_id_key, trade):
    """Preview and place a single trade. Returns order ID or None on failure."""
    client_order_id = uuid.uuid4().hex[:20]
    params = trade.to_order_params(account_id_key, client_order_id)

    # Preview
    try:
        preview = normalize(orders_client.preview_equity_order(**params))
        preview_id = safe_get(preview, "PreviewOrderResponse", "PreviewIds", "previewId")
        commission = safe_get(preview, "PreviewOrderResponse", "Order", "estimatedCommission")
        if preview_id is None:
            raise ValueError(f"Could not extract previewId from response: {preview}")
    except Exception as e:
        print(f"  PREVIEW FAILED: {e}")
        return None

    # Place
    try:
        result = normalize(orders_client.place_equity_order(**params, previewId=preview_id))
        order_id = safe_get(result, "PlaceOrderResponse", "OrderIds", "orderId")
        msg = safe_get(result, "PlaceOrderResponse", "Order", "messages", "Message", "description")
        if order_id is None:
            raise ValueError(f"Could not extract orderId from response: {result}")
        print(f"  Order #{order_id} - {msg} (commission: ${commission})")
        return order_id
    except Exception as e:
        print(f"  PLACE FAILED: {e}")
        return None


def main():
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python run_trades.py <csv_file> [--env sandbox|prod]")
        sys.exit(1)

    csv_path = sys.argv[1]
    env = "sandbox"
    if "--env" in sys.argv:
        env_idx = sys.argv.index("--env") + 1
        if env_idx < len(sys.argv):
            env = sys.argv[env_idx]

    is_prod = (env == "prod")

    print("=" * 60)
    if is_prod:
        print("  *** PRODUCTION MODE - REAL MONEY ***")
    print(f"E*TRADE Trade Executor ({env.upper()})")
    print("=" * 60)

    # Read trades
    print(f"\nReading trades from: {csv_path}")
    trades = read_trades(csv_path)

    # Show summary counts
    sells = [t for t in trades if t.action in ("SELL", "SELL_SHORT")]
    buys = [t for t in trades if t.action in ("BUY", "BUY_TO_COVER")]
    print(f"\nLoaded {len(trades)} trades: {len(sells)} SELL(s), {len(buys)} BUY(s)")
    if sells:
        print("  SELLs will execute first")

    # Show trade summary
    print(f"\nTrade Summary:")
    print("-" * 60)
    print(f"{'Symbol':<10} {'Action':<12} {'Qty':>6} {'Type':<14} {'Term'}")
    print("-" * 60)
    for t in trades:
        price_info = t.price_type
        if t.limit_price:
            price_info += f" @{t.limit_price}"
        if t.stop_price:
            price_info += f" stop@{t.stop_price}"
        print(f"{t.symbol:<10} {t.action:<12} {t.quantity:>6} {price_info:<14} {t.order_term}")
    print("-" * 60)

    # Confirmation
    if is_prod:
        print(f"\n{'!' * 60}")
        print(f"  WARNING: You are about to place {len(trades)} REAL trades")
        print(f"  This will use REAL MONEY in your REAL account")
        print(f"{'!' * 60}")
        confirm = input(f"\n  Type CONFIRM to proceed: ").strip()
        if confirm != "CONFIRM":
            print("Cancelled. (Must type CONFIRM exactly)")
            sys.exit(0)
    else:
        confirm = input(f"\nProceed with {len(trades)} trades in SANDBOX? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Cancelled.")
            sys.exit(0)

    # Authenticate
    print(f"\nAuthenticating ({env})...")
    cfg = load_config_from_keyring(env=env)
    access_token, access_secret = authenticate(cfg)

    # Get account
    account_id_key = get_account(cfg, access_token, access_secret)

    # Second confirmation for production
    if is_prod:
        confirm2 = input(f"\n  Final check - execute trades on this account? (CONFIRM/no): ").strip()
        if confirm2 != "CONFIRM":
            print("Cancelled.")
            sys.exit(0)

    # Create order client
    orders_client = ETradeOrder(
        client_key=cfg.consumer_key,
        client_secret=cfg.consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_secret,
        dev=(cfg.env == "sandbox"),
    )

    # Execute trades — SELLs first, then BUYs
    results = {"success": 0, "failed": 0}

    if sells:
        print(f"\n--- EXECUTING {len(sells)} SELL ORDER(S) ---")
        for t in sells:
            print(f"\n  {t.action} {t.quantity} {t.symbol}...")
            order_id = preview_and_place(orders_client, account_id_key, t)
            if order_id:
                results["success"] += 1
            else:
                results["failed"] += 1

    if buys:
        print(f"\n--- EXECUTING {len(buys)} BUY ORDER(S) ---")
        for t in buys:
            print(f"\n  {t.action} {t.quantity} {t.symbol}...")
            order_id = preview_and_place(orders_client, account_id_key, t)
            if order_id:
                results["success"] += 1
            else:
                results["failed"] += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"COMPLETE: {results['success']} succeeded, {results['failed']} failed")
    print("=" * 60)


if __name__ == "__main__":
    main()