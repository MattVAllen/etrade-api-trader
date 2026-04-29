## Minimal Format

For simple trades, only 3 columns are required:

```csv
Symbol,Action,Quantity
POWL,SELL,8
DY,BUY,5
NEM,BUY,18
```

This will use E*TRADE defaults:
- **Price Type:** MARKET (execute at market price)
- **Order Term:** GOOD_FOR_DAY (cancel if not filled by end of day)
- **Market Session:** REGULAR (9:30 AM - 4:00 PM ET)

---

## Full Format (All Optional Columns)

For fine-grained control, use all columns:

```csv
Symbol,Action,Quantity,PriceType,LimitPrice,StopPrice,OrderTerm,MarketSession,AllOrNone,RoutingDestination
AAPL,BUY,10,LIMIT,185.50,,GOOD_UNTIL_CANCEL,REGULAR,,
DY,BUY,5,MARKET,,,GOOD_FOR_DAY,REGULAR,,
NEM,SELL,18,STOP,,,GOOD_FOR_DAY,REGULAR,,75.00
```

---

## Column Definitions

### Symbol (required)
- Stock ticker symbol (e.g., AAPL, MSFT, DY)
- Case-insensitive

### Action (required)
Valid values:
- `BUY` — Buy shares
- `SELL` — Sell shares from holdings
- `BUY_TO_COVER` — Buy to cover short sale
- `SELL_SHORT` — Short sell (requires margin account)

### Quantity (required)
- Number of shares (integer)
- Must be positive

### PriceType (optional)
Valid values:
- `MARKET` — Execute at current market price (default)
- `LIMIT` — Execute only at specified price or better (requires LimitPrice)
- `STOP` — Execute when price hits stop level (requires StopPrice)
- `STOP_LIMIT` — Combine stop and limit (requires both prices)
- `MARKET_ON_CLOSE` — Execute at market close price

### LimitPrice (optional)
- Decimal price (e.g., 185.50)
- Required if PriceType is LIMIT or STOP_LIMIT
- Leave empty otherwise

### StopPrice (optional)
- Decimal price (e.g., 75.00)
- Required if PriceType is STOP or STOP_LIMIT
- Leave empty otherwise

### OrderTerm (optional)
Valid values:
- `GOOD_FOR_DAY` — Cancel if not filled by end of trading day (default)
- `GOOD_UNTIL_CANCEL` — Order remains open until manually canceled
- `IMMEDIATE_OR_CANCEL` — Fill entire order immediately or cancel all
- `FILL_OR_KILL` — Fill entire order immediately or cancel all (stricter than IOC)

### MarketSession (optional)
Valid values:
- `REGULAR` — Normal trading hours: 9:30 AM - 4:00 PM ET (default)
- `EXTENDED` — Extended hours: 7:00 AM - 8:00 PM ET (pre-market + after-hours)

### AllOrNone (optional)
Valid values:
- Leave empty for default (fill allowed)
- `true` or `1` — Entire order must be filled at once
- `false` or `0` — Partial fills allowed (default)

### RoutingDestination (optional)
Valid values:
- `AUTO` — Let E*TRADE choose best route (default)
- `ARCA` — Direct to ARCA exchange
- `NSDQ` — Direct to NASDAQ
- `NYSE` — Direct to NYSE

Most trades should use `AUTO` and let E*TRADE optimize routing.

---

## Example Trades

### Simple Buy (Market Order)
```csv
Symbol,Action,Quantity
MSFT,BUY,10
```
→ Buy 10 shares of MSFT at market price, day order, regular hours

### Sell with Limit Price
```csv
Symbol,Action,Quantity,PriceType,LimitPrice
TSLA,SELL,5,LIMIT,250.00
```
→ Sell 5 TSLA only if price reaches $250 or higher

### Buy with Extended Hours
```csv
Symbol,Action,Quantity,MarketSession
AMD,BUY,20,EXTENDED
```
→ Buy 20 AMD shares during extended hours (7 AM - 8 PM ET)

### Day Trade with Stop-Limit
```csv
Symbol,Action,Quantity,PriceType,LimitPrice,StopPrice,OrderTerm
NVDA,BUY,5,STOP_LIMIT,480.00,475.00,GOOD_FOR_DAY
```
→ Buy 5 NVDA when price drops to $475, but only fill if ≤$480, cancel at market close if not filled

### Good-Until-Cancel (Swing Trade)
```csv
Symbol,Action,Quantity,PriceType,LimitPrice,OrderTerm
AIBM,SELL,100,LIMIT,150.00,GOOD_UNTIL_CANCEL
```
→ Sell 100 AIBM shares at $150 or higher, remain open until manually canceled

---

## Processing Rules

**SELL orders execute BEFORE BUY orders** — this ensures cash availability for buys. Automatic sorting by `run_trades.py`.

**Example CSV:**
```csv
Symbol,Action,Quantity
TSLA,BUY,5
POWL,SELL,8
DY,BUY,10
```

**Execution order:**
1. POWL SELL 8 (first, frees up cash)
2. TSLA BUY 5 (uses freed cash)
3. DY BUY 10 (uses remaining cash)

Why? Prevents insufficient cash errors when trading with tight margins.

---

## Validation & Errors

**CSV must be valid:**
- First row is header (Symbol, Action, Quantity, ...)
- All subsequent rows are trades
- No blank rows in middle
- No trailing commas

**Symbol validation:** Checked against E*TRADE when trade is previewed. Invalid symbol = trade is rejected with error.

**Quantity validation:** Must be positive integer. Fractional shares not supported (E*TRADE limitation).

**Price validation:** Limit and stop prices must be positive decimals. Range checked by E*TRADE API.

**Action validation:** Must be one of: BUY, SELL, BUY_TO_COVER, SELL_SHORT. Case-insensitive.

If validation fails, `run_trades.py` shows error and exits before any trades execute.
