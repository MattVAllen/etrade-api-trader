"""
CSV Trade Reader for E*TRADE Bot
Reads trade instructions from CSV and validates them.

Required columns: Symbol, Action, Quantity
Optional columns: PriceType, LimitPrice, StopPrice, OrderTerm, MarketSession,
                  AllOrNone, RoutingDestination

Defaults (if optional columns not provided):
  PriceType: MARKET
  OrderTerm: GOOD_FOR_DAY
  MarketSession: REGULAR
  AllOrNone: False
  RoutingDestination: AUTO
"""

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


VALID_ACTIONS = {"BUY", "SELL", "BUY_TO_COVER", "SELL_SHORT"}
VALID_PRICE_TYPES = {"MARKET", "LIMIT", "STOP", "STOP_LIMIT", "MARKET_ON_CLOSE"}
VALID_ORDER_TERMS = {"GOOD_FOR_DAY", "GOOD_UNTIL_CANCEL", "IMMEDIATE_OR_CANCEL", "FILL_OR_KILL"}
VALID_SESSIONS = {"REGULAR", "EXTENDED"}
VALID_ROUTING = {"AUTO", "ARCA", "NSDQ", "NYSE"}


@dataclass
class TradeInstruction:
    """A single trade instruction parsed from CSV."""
    symbol: str
    action: str  # BUY, SELL, BUY_TO_COVER, SELL_SHORT
    quantity: int
    price_type: str = "MARKET"
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    order_term: str = "GOOD_FOR_DAY"
    market_session: str = "REGULAR"
    all_or_none: bool = False
    routing_destination: str = "AUTO"

    def to_order_params(self, account_id_key: str, client_order_id: str) -> dict:
        """Convert to kwargs for pyetrade preview/place_equity_order."""
        params = dict(
            accountIdKey=account_id_key,
            symbol=self.symbol,
            orderAction=self.action,
            clientOrderId=client_order_id,
            priceType=self.price_type,
            quantity=self.quantity,
            marketSession=self.market_session,
            orderTerm=self.order_term,
        )
        if self.limit_price is not None:
            params["limitPrice"] = self.limit_price
        if self.stop_price is not None:
            params["stopPrice"] = self.stop_price
        if self.all_or_none:
            params["allOrNone"] = True
        if self.routing_destination != "AUTO":
            params["routingDestination"] = self.routing_destination
        return params


def read_trades(csv_path: str) -> List[TradeInstruction]:
    """
    Read trade instructions from CSV file.

    Required columns: Symbol, Action, Quantity
    Optional columns: PriceType, LimitPrice, StopPrice, OrderTerm,
                      MarketSession, AllOrNone, RoutingDestination

    Rows with Action = EVALUATE or HOLD are skipped.
    Empty rows are skipped.

    Args:
        csv_path: Path to CSV file

    Returns:
        List of TradeInstruction objects, SELLs first then BUYs

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If required columns missing or data invalid
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    trades = []
    errors = []

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        # Normalize header names (strip whitespace, capitalize)
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty")
        headers = {h.strip() for h in reader.fieldnames}

        # Check required columns (case-insensitive matching)
        header_map = {h.strip().lower(): h.strip() for h in reader.fieldnames}
        for required in ("symbol", "action", "quantity"):
            if required not in header_map:
                raise ValueError(f"Missing required column: {required}. Found: {headers}")

        for row_num, row in enumerate(reader, start=2):
            # Normalize keys
            row = {k.strip().lower().replace(" ", ""): v.strip() if v else "" for k, v in row.items()}
            
            # Skip empty rows
            if not row.get("symbol"):
                continue

            # Skip non-actionable rows
            action = row["action"].upper()
            if action in ("EVALUATE", "HOLD", ""):
                continue

            # Validate action
            if action not in VALID_ACTIONS:
                errors.append(f"Row {row_num}: Invalid action '{action}' for {row['symbol']}")
                continue

            # Validate quantity
            try:
                quantity = int(float(row["quantity"]))
                if quantity <= 0:
                    errors.append(f"Row {row_num}: Quantity must be positive for {row['symbol']}")
                    continue
            except (ValueError, TypeError):
                errors.append(f"Row {row_num}: Invalid quantity '{row.get('quantity')}' for {row['symbol']}")
                continue

            # Parse optional fields with defaults
            price_type = row.get("pricetype", "MARKET").upper() or "MARKET"
            if price_type not in VALID_PRICE_TYPES:
                errors.append(f"Row {row_num}: Invalid PriceType '{price_type}' for {row['symbol']}")
                continue

            order_term = row.get("orderterm", "GOOD_FOR_DAY").upper() or "GOOD_FOR_DAY"
            if order_term not in VALID_ORDER_TERMS:
                errors.append(f"Row {row_num}: Invalid OrderTerm '{order_term}' for {row['symbol']}")
                continue

            market_session = row.get("marketsession", "REGULAR").upper() or "REGULAR"
            if market_session not in VALID_SESSIONS:
                errors.append(f"Row {row_num}: Invalid MarketSession '{market_session}' for {row['symbol']}")
                continue

            routing = row.get("routingdestination", "AUTO").upper() or "AUTO"
            if routing not in VALID_ROUTING:
                errors.append(f"Row {row_num}: Invalid RoutingDestination '{routing}' for {row['symbol']}")
                continue

            # Parse limit/stop prices
            limit_price = None
            if row.get("limitprice"):
                try:
                    limit_price = float(row["limitprice"])
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid LimitPrice '{row['limitprice']}' for {row['symbol']}")
                    continue

            stop_price = None
            if row.get("stopprice"):
                try:
                    stop_price = float(row["stopprice"])
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid StopPrice '{row['stopprice']}' for {row['symbol']}")
                    continue

            # Validate price type requirements
            if price_type in ("LIMIT", "STOP_LIMIT") and limit_price is None:
                errors.append(f"Row {row_num}: LimitPrice required for {price_type} order ({row['symbol']})")
                continue
            if price_type in ("STOP", "STOP_LIMIT") and stop_price is None:
                errors.append(f"Row {row_num}: StopPrice required for {price_type} order ({row['symbol']})")
                continue

            all_or_none = row.get("allornone", "").upper() in ("TRUE", "YES", "1")

            trades.append(TradeInstruction(
                symbol=row["symbol"].upper(),
                action=action,
                quantity=quantity,
                price_type=price_type,
                limit_price=limit_price,
                stop_price=stop_price,
                order_term=order_term,
                market_session=market_session,
                all_or_none=all_or_none,
                routing_destination=routing,
            ))

    # Report errors
    if errors:
        print(f"\nWarnings ({len(errors)} rows skipped):")
        for err in errors:
            print(f"  {err}")

    if not trades:
        raise ValueError("No valid trades found in CSV")

    # Sort: SELLs and SELL_SHORTs first, then BUYs
    sell_actions = {"SELL", "SELL_SHORT"}
    sells = [t for t in trades if t.action in sell_actions]
    buys = [t for t in trades if t.action not in sell_actions]

    sorted_trades = sells + buys

    print(f"\nLoaded {len(sorted_trades)} trades: {len(sells)} SELL(s), {len(buys)} BUY(s)")
    if sells:
        print("  SELLs will execute first")

    return sorted_trades
