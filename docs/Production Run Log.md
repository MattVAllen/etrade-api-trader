# Production Run Log

Log of live trade execution runs.
Workbook version history is in SAAPPR → Workbook Change Log.md.

---

### Feb 25, 2026 — Run #1 ✅

First successful production run. End-to-end workflow validated.

---

### Feb 27, 2026 — Run #2 ⚠️ Partial failure

- 36 trades attempted: 1 SELL + 35 BUYs
- 21 BUYs succeeded
- Root cause 1: pyetrade response parsing — E*TRADE sometimes returns list instead of dict. Script crashed but orders were executing silently.
- Root cause 2: Excel scaling bug — Target Spend was scaling against Starting Cash instead of Net to Deploy, over-allocating ~15%.

---

### Mar 2, 2026 — Run #3 ⚠️ Partial failure (Realignment)

- Ran realignment to correct over-bought positions from Feb 27
- All 23 SELLs succeeded ✅
- 7 BUYs failed with same list parsing error (fix not yet applied)

---

### Mar 2, 2026 — Run #4 ✅ Bug fix confirmed

- Re-ran with fixed `run_trades.py`
- Fix: added `normalize()` and `safe_get()` helpers to unwrap nested API responses recursively
- Confirmed successful trade execution

---

### Mar 3, 2026 — GitHub Update: API Response Parsing Fix ✅

- Pushed `run_trades.py` fix to public repo (commit fcd2372)
- **Changes:** Added `normalize()` and `safe_get()` helpers to handle pyetrade list/dict variance
- **Impact:** Fixes "list indices must be integers or slices, not str" errors where SELL orders would execute but script couldn't confirm them
- Public repo now has production-ready API parsing robustness

---

### Mar 3, 2026 — pyetrade Upstream Contribution Submitted 📝

- Created PR #122 on jessecooper/pyetrade: "Add E*TRADE OAuth quirks and workarounds documentation"
- Added comprehensive guide: `docs/OAUTH_QUIRKS.md`
- Updated README with link to new guide
- Awaiting maintainer feedback
