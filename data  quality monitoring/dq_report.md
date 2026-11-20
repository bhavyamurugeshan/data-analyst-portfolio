# Data Quality Report

File checked : messy_retail_sales.csv
Rows         : 318
Columns      : 8  (order_id, order_date, product, category, price, quantity, customer_id, region)

## 1. Missing values
- category: 3 missing (0.9%)
- customer_id: 3 missing (0.9%)
- region: 2 missing (0.6%)

## 2. Duplicates
- Exact duplicate rows: 6
- Rows reusing an order_id: 8
  Example IDs: ORD-1230, ORD-1080, ORD-1132, ORD-1010, ORD-1111

## 3. Impossible values (price / quantity)
- Negative prices: 3
- Zero prices: 2
- Negative quantities: 2
  Example IDs: ORD-3005, ORD-3003, ORD-3002, ORD-3004, ORD-3001

## 4. Dates
- Dates that could not be parsed: 2
  - "unknown"
  - "2026-02-30"
- Dates not in the standard YYYY-MM-DD format: 7
  - "Feb 26, 2026"
  - "19/03/2026"
  - "unknown"
  - "Mar 30, 2026"
  - "Mar 13, 2026"

## 5. Inconsistent text (region names)
- Region values with odd spacing or casing: 5
  - " North "  should be  "North"
  - "SOUTH "  should be  "South"
  - "north"  should be  "North"
  - "east"  should be  "East"
  - "WEST"  should be  "West"

## 6. Outliers (unusually large values)
- price: 1 row(s) above 3,020 (normal upper limit)
  - ORD-3015: price = 99,999
- quantity: 1 row(s) above 7 (normal upper limit)
  - ORD-3016: quantity = 500

## Summary

| Check | Result |
| --- | --- |
| Missing values | 8 issue(s) found |
| Duplicates | 14 issue(s) found |
| Impossible values | 7 issue(s) found |
| Date problems | 9 issue(s) found |
| Inconsistent text | 5 issue(s) found |
| Outliers | 2 issue(s) found |

Next step: fix these issues in a cleaning script, then re-run this
file - every check should say PASS on the clean data.
