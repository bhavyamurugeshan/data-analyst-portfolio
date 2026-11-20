"""
DATA QUALITY MONITOR
====================
What this script does:
  1. Loads a CSV file of sales data.
  2. Runs six standard data-quality checks on it.
  3. Prints a summary to the screen AND saves the same summary as a
     Markdown report (dq_report.md) that you can put on GitHub.

This is how data teams watch for "bad data" before it breaks a
dashboard or a report. Real tools (Great Expectations, dbt tests) do
the same job - this script teaches you the ideas behind them.

You only need pandas:   python -m pip install pandas
Run it from the folder that contains the CSV:
    python data_quality_check.py
"""

import pandas as pd

FILE_NAME = "messy_retail_sales.csv"   # the data we are checking
REPORT_NAME = "dq_report.md"           # the report we will create

# ------------------------------------------------------------------
# Small helper: everything we "say" goes to the screen AND into the
# report file, so the report always matches what you saw on screen.
# ------------------------------------------------------------------
report_lines = []

def say(text=""):
    print(text)
    report_lines.append(text)

# We collect (check name, number of problems) as we go, so the final
# summary can say PASS or list the issue count for each check.
check_results = []

# ------------------------------------------------------------------
# STEP 1: Load the data
# ------------------------------------------------------------------
df = pd.read_csv(FILE_NAME)

say("# Data Quality Report")
say()
say(f"File checked : {FILE_NAME}")
say(f"Rows         : {len(df)}")
say(f"Columns      : {len(df.columns)}  ({', '.join(df.columns)})")
say()

# ------------------------------------------------------------------
# CHECK 1: Missing values
# Empty cells are the most common data problem. pandas shows them as
# NaN (Not a Number). We count them column by column.
# ------------------------------------------------------------------
say("## 1. Missing values")
missing = df.isna().sum()
missing_cols = missing[missing > 0]
if missing_cols.empty:
    say("No missing values anywhere.")
else:
    for col, n in missing_cols.items():
        pct = n / len(df) * 100
        say(f"- {col}: {n} missing ({pct:.1f}%)")
check_results.append(("Missing values", int(missing_cols.sum())))
say()

# ------------------------------------------------------------------
# CHECK 2: Duplicates
# Two kinds: a whole row copied twice, and two different rows sharing
# the same order_id (an ID should never repeat).
# ------------------------------------------------------------------
say("## 2. Duplicates")
dup_rows = int(df.duplicated().sum())
dup_ids = int(df.duplicated(subset="order_id").sum())
say(f"- Exact duplicate rows: {dup_rows}")
say(f"- Rows reusing an order_id: {dup_ids}")
if dup_ids:
    example_ids = df[df.duplicated(subset="order_id", keep=False)]["order_id"].unique()[:5]
    say(f"  Example IDs: {', '.join(example_ids)}")
check_results.append(("Duplicates", dup_rows + dup_ids))
say()

# ------------------------------------------------------------------
# CHECK 3: Impossible values
# A price or quantity below zero (or a price of exactly zero) is a
# data entry error - no real order looks like that.
# ------------------------------------------------------------------
say("## 3. Impossible values (price / quantity)")
neg_price = int((df["price"] < 0).sum())
zero_price = int((df["price"] == 0).sum())
neg_qty = int((df["quantity"] < 0).sum())
say(f"- Negative prices: {neg_price}")
say(f"- Zero prices: {zero_price}")
say(f"- Negative quantities: {neg_qty}")
if neg_price or zero_price or neg_qty:
    bad_ids = df[(df["price"] <= 0) | (df["quantity"] < 0)]["order_id"].head(5)
    say(f"  Example IDs: {', '.join(bad_ids)}")
check_results.append(("Impossible values", neg_price + zero_price + neg_qty))
say()

# ------------------------------------------------------------------
# CHECK 4: Dates
# Two separate problems:
#   a) dates a computer cannot read at all (errors="coerce" turns
#      unreadable dates into NaT - "Not a Time")
#   b) valid dates written in a different format than the rest
#      (mixing formats breaks sorting and grouping later)
# dayfirst=True tells pandas that 14/03/2026 means 14 March.
# ------------------------------------------------------------------
say("## 4. Dates")
try:
    # pandas 2.0 and later: "mixed" lets each row have its own format
    parsed = pd.to_datetime(df["order_date"], errors="coerce",
                            format="mixed", dayfirst=True)
except Exception:
    parsed = pd.to_datetime(df["order_date"], errors="coerce", dayfirst=True)

bad_dates = df["order_date"][parsed.isna()]
say(f"- Dates that could not be parsed: {len(bad_dates)}")
for v in bad_dates.unique()[:5]:
    say(f'  - "{v}"')

iso_mask = df["order_date"].astype(str).str.match(r"^\d{4}-\d{2}-\d{2}$")
non_iso = df["order_date"][~iso_mask]
say(f"- Dates not in the standard YYYY-MM-DD format: {len(non_iso)}")
for v in non_iso.unique()[:5]:
    say(f'  - "{v}"')
check_results.append(("Date problems", len(bad_dates) + len(non_iso)))
say()

# ------------------------------------------------------------------
# CHECK 5: Inconsistent text
# "North", "north " and " NORTH" look the same to a person but are
# three different values to a computer - they would show up as three
# separate regions in a chart.
# ------------------------------------------------------------------
say("## 5. Inconsistent text (region names)")
regions_raw = df["region"].dropna()
cleaned = regions_raw.str.strip().str.title()
messy = regions_raw[regions_raw != cleaned]
say(f"- Region values with odd spacing or casing: {len(messy)}")
for v in messy.unique():
    say(f'  - "{v}"  should be  "{v.strip().title()}"')
check_results.append(("Inconsistent text", len(messy)))
say()

# ------------------------------------------------------------------
# CHECK 6: Outliers
# The IQR rule: values far above the "normal" range are suspicious.
# Q1 = value at 25%, Q3 = value at 75%, IQR = Q3 - Q1.
# Anything above Q3 + 1.5*IQR is flagged. It is not always wrong -
# but a human should look at it.
# ------------------------------------------------------------------
say("## 6. Outliers (unusually large values)")
total_outliers = 0
for col in ["price", "quantity"]:
    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)
    iqr = q3 - q1
    upper = q3 + 1.5 * iqr
    outs = df[df[col] > upper]
    total_outliers += len(outs)
    say(f"- {col}: {len(outs)} row(s) above {upper:,.0f} (normal upper limit)")
    for _, r in outs.head(3).iterrows():
        say(f'  - {r["order_id"]}: {col} = {r[col]:,}')
check_results.append(("Outliers", total_outliers))
say()

# ------------------------------------------------------------------
# FINAL SUMMARY
# ------------------------------------------------------------------
say("## Summary")
say()
say("| Check | Result |")
say("| --- | --- |")
for name, n in check_results:
    say(f"| {name} | {'PASS' if n == 0 else str(n) + ' issue(s) found'} |")
say()
say("Next step: fix these issues in a cleaning script, then re-run this")
say("file - every check should say PASS on the clean data.")

with open(REPORT_NAME, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines) + "\n")

print()
print(f"Report saved to {REPORT_NAME}")
