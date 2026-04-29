# EAT — Pipeline Map

End-to-end flow from SAAPPR's CSV export to executed trades at E*TRADE.

```mermaid
flowchart TD
    A[SAAPPR Rebalance Export] -->|writes| B["_local/Trades.csv"]
    B --> C[run_trades.py]
    C --> D[csv_reader.py<br/>parse + validate]
    D --> E[TradeInstruction objects<br/>SELLs sorted first]
    E --> F{Token valid?}
    F -->|yes| H[oauth_etrade.py<br/>OAuth 1.0a signing]
    F -->|no| G[Refresh tokens<br/>Windows Keyring creds]
    G --> H
    H --> I[E*TRADE Preview API]
    I --> J{Preview OK?}
    J -->|yes| K[User confirms in terminal]
    J -->|no| L[Abort + report error]
    K --> M[E*TRADE Place API]
    M --> N[Response logged]
    N --> O{More trades?}
    O -->|yes| F
    O -->|no| P[Done]

    subgraph Credentials
      Q[Windows Keyring<br/>etrade_prod / etrade_sandbox]
      R["~/.etrade/tokens.*.json"]
    end
    Q -.-> G
    R -.-> F
```

## Key Nodes

| Node | File | Purpose |
|---|---|---|
| `csv_reader.py` | `utils/csv_reader.py` | Parses CSV → `TradeInstruction`; enforces SELLs-before-BUYs |
| `oauth_etrade.py` | `auth/oauth_etrade.py` | Custom OAuth 1.0a (pyetrade's built-in flow doesn't work with E*TRADE) |
| `run_trades.py` | root | Entry point; orchestrates preview → confirm → place per trade |
| Token cache | `~/.etrade/tokens.{sandbox,prod}.json` | Auto-refreshed; expires midnight US Eastern |
| Credentials | Windows Keyring (`etrade_prod` / `etrade_sandbox`) | Never hardcoded |

## Upstream / Downstream

- **Upstream:** SAAPPR's Rebalance Export (Excel macro) writes to `Forge/EAT/_local/Trades.csv`
- **Downstream:** E*TRADE API — production at `api.etrade.com`, sandbox data at `apisb.etrade.com` (token endpoints always prod host)

## Alternate Path — Fidelity

For Fidelity trades, the TamperMonkey userscript at `_local/userscripts/fidelity-trade-modal/fidelity-trade-modal.user.js` replaces the API path: CSV → paste into panel → script drives Fidelity's web modal → manual confirm → place.
