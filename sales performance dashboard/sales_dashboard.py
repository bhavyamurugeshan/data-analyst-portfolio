"""Sales Performance Dashboard

Reads sales_data.csv, prints a summary of the headline numbers,
and writes sales_dashboard.html - a visual dashboard you open
in your browser by double-clicking it.

Needs only pandas. Run with:  python sales_dashboard.py
"""

import html

import pandas as pd

# ---------------------------------------------------------------- load data
df = pd.read_csv("sales_data.csv", parse_dates=["order_date"])
df["month"] = df["order_date"].dt.to_period("M")

# ------------------------------------------------------- headline numbers
total_revenue = df["revenue_inr"].sum()
total_orders = len(df)
avg_order_value = total_revenue / total_orders
total_qty = df["quantity"].sum()

monthly = df.groupby("month")["revenue_inr"].sum().sort_index()
best_month = monthly.idxmax()
best_month_revenue = monthly.max()
last_month, prev_month = monthly.iloc[-1], monthly.iloc[-2]
mom_growth = (last_month / prev_month - 1) * 100

by_region = df.groupby("region")["revenue_inr"].sum().sort_values(ascending=False)
by_category = df.groupby("category")["revenue_inr"].sum().sort_values(ascending=False)
top_products = df.groupby("product")["revenue_inr"].sum().nlargest(5)
top_people = df.groupby("salesperson")["revenue_inr"].sum().nlargest(5)

# ------------------------------------------------------ number formatting
def inr(n):
    """Format a number in the Indian style: 12,34,567."""
    n = int(round(n))
    s = str(abs(n))
    if len(s) > 3:
        last3 = s[-3:]
        rest = s[:-3]
        groups = []
        while rest:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        s = ",".join(groups) + "," + last3
    return ("-" if n < 0 else "") + s


# ------------------------------------------------------------- SVG charts
PALETTE = ["#2563eb", "#16a34a", "#d97706", "#dc2626", "#7c3aed", "#0891b2"]


def bar_chart(series, width=640, bar_h=30, gap=12):
    """Horizontal bar chart as inline SVG."""
    label_w, value_w, top = 170, 130, 10
    height = top * 2 + len(series) * (bar_h + gap)
    maxv = series.max()
    parts = [f'<svg width="{width}" height="{height}" '
             f'xmlns="http://www.w3.org/2000/svg" font-family="Segoe UI, Arial" font-size="13">']
    for i, (label, value) in enumerate(series.items()):
        y = top + i * (bar_h + gap)
        bar_w = max(2, int((width - label_w - value_w - 20) * value / maxv))
        color = PALETTE[i % len(PALETTE)]
        parts.append(f'<text x="{label_w - 8}" y="{y + bar_h * 0.7:.0f}" text-anchor="end" fill="#111">{html.escape(str(label))}</text>')
        parts.append(f'<rect x="{label_w}" y="{y}" width="{bar_w}" height="{bar_h}" rx="4" fill="{color}"/>')
        parts.append(f'<text x="{label_w + bar_w + 8}" y="{y + bar_h * 0.7:.0f}" fill="#111">INR {inr(value)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def line_chart(series, width=640, height=260):
    """Monthly revenue line chart as inline SVG."""
    pad_l, pad_r, pad_t, pad_b = 70, 30, 26, 40
    n = len(series)
    maxv, minv = series.max(), series.min()
    xs = [pad_l + i * (width - pad_l - pad_r) / (n - 1) for i in range(n)]
    scale = (height - pad_t - pad_b) / (maxv - minv if maxv > minv else 1)
    ys = [height - pad_b - (v - minv) * scale for v in series]
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    parts = [f'<svg width="{width}" height="{height}" '
             f'xmlns="http://www.w3.org/2000/svg" font-family="Segoe UI, Arial" font-size="11">']
    # gridlines + y labels (4 lines)
    for g in range(5):
        v = minv + (maxv - minv) * g / 4
        y = height - pad_b - (v - minv) * scale
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width - pad_r}" y2="{y:.1f}" stroke="#e5e7eb"/>')
        parts.append(f'<text x="{pad_l - 6}" y="{y + 4:.1f}" text-anchor="end" fill="#6b7280">{inr(v / 1000)}k</text>')
    parts.append(f'<polyline points="{pts}" fill="none" stroke="#2563eb" stroke-width="2.5"/>')
    for i, (x, y) in enumerate(zip(xs, ys)):
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#2563eb"/>')
        label = str(series.index[i])
        if (i % 2 == 0 and i <= n - 3) or i == n - 1:  # every second month, always the last
            parts.append(f'<text x="{x:.1f}" y="{height - pad_b + 16}" text-anchor="middle" fill="#6b7280">{label}</text>')
    # mark the best month
    bi = list(series.index).index(series.idxmax())
    anchor = "end" if xs[bi] > width - 80 else "middle"
    parts.append(f'<circle cx="{xs[bi]:.1f}" cy="{ys[bi]:.1f}" r="6" fill="none" stroke="#dc2626" stroke-width="2"/>')
    parts.append(f'<text x="{xs[bi]:.1f}" y="{ys[bi] - 12:.1f}" text-anchor="{anchor}" fill="#dc2626" font-size="12">Best month</text>')
    parts.append("</svg>")
    return "".join(parts)


# --------------------------------------------------------------- HTML page
def card(title, value, sub=""):
    return (f'<div class="card"><div class="card-title">{title}</div>'
            f'<div class="card-value">{value}</div>'
            f'<div class="card-sub">{sub}</div></div>')


cards = "".join([
    card("Total revenue", f"INR {inr(total_revenue)}", f"{len(monthly)} months, {total_qty:,} units"),
    card("Total orders", f"{total_orders:,}", f"Avg order value INR {inr(avg_order_value)}"),
    card("Best month", str(best_month), f"INR {inr(best_month_revenue)}"),
    card("Latest month growth", f"{mom_growth:+.1f}%",
         f"{monthly.index[-1]} vs {monthly.index[-2]}"),
])

page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Sales Performance Dashboard</title>
<style>
  body {{ font-family: "Segoe UI", Arial, sans-serif; background:#f3f4f6; margin:0; padding:24px; color:#111; }}
  h1 {{ font-size:22px; margin:0 0 4px; }}
  .sub {{ color:#6b7280; font-size:13px; margin-bottom:20px; }}
  .cards {{ display:flex; flex-wrap:wrap; gap:14px; margin-bottom:22px; }}
  .card {{ background:#fff; border-radius:10px; padding:14px 18px; min-width:190px;
          box-shadow:0 1px 3px rgba(0,0,0,.08); }}
  .card-title {{ font-size:12px; color:#6b7280; text-transform:uppercase; letter-spacing:.04em; }}
  .card-value {{ font-size:22px; font-weight:600; margin-top:4px; }}
  .card-sub {{ font-size:12px; color:#6b7280; margin-top:2px; }}
  .grid {{ display:flex; flex-wrap:wrap; gap:18px; }}
  .panel {{ background:#fff; border-radius:10px; padding:16px 18px;
           box-shadow:0 1px 3px rgba(0,0,0,.08); }}
  .panel h2 {{ font-size:15px; margin:0 0 10px; }}
  .note {{ color:#6b7280; font-size:12px; margin-top:22px; }}
</style>
</head>
<body>
<h1>Sales Performance Dashboard</h1>
<div class="sub">{df['order_date'].min().date()} to {df['order_date'].max().date()} &middot; {total_orders:,} orders &middot; fictional demo data</div>
<div class="cards">{cards}</div>
<div class="grid">
  <div class="panel"><h2>Monthly revenue</h2>{line_chart(monthly)}</div>
  <div class="panel"><h2>Revenue by region</h2>{bar_chart(by_region)}</div>
  <div class="panel"><h2>Revenue by category</h2>{bar_chart(by_category)}</div>
  <div class="panel"><h2>Top 5 products by revenue</h2>{bar_chart(top_products)}</div>
  <div class="panel"><h2>Top 5 salespeople by revenue</h2>{bar_chart(top_people)}</div>
</div>
<div class="note">Built by sales_dashboard.py from sales_data.csv.</div>
</body>
</html>
"""

with open("sales_dashboard.html", "w", encoding="utf-8") as f:
    f.write(page)

# ------------------------------------------------------------ text summary
print("=" * 52)
print("SALES PERFORMANCE DASHBOARD - SUMMARY")
print("=" * 52)
print(f"Period            : {df['order_date'].min().date()} to {df['order_date'].max().date()}")
print(f"Total orders      : {total_orders:,}")
print(f"Total units sold  : {total_qty:,}")
print(f"Total revenue     : INR {inr(total_revenue)}")
print(f"Avg order value   : INR {inr(avg_order_value)}")
print(f"Best month        : {best_month} (INR {inr(best_month_revenue)})")
print(f"Latest month      : {monthly.index[-1]} (INR {inr(last_month)}, {mom_growth:+.1f}% vs previous)")
print()
print("Revenue by region:")
for name, val in by_region.items():
    print(f"  {name:<8} INR {inr(val)}  ({val / total_revenue * 100:.1f}%)")
print()
print("Top 5 products:")
for name, val in top_products.items():
    print(f"  {name:<22} INR {inr(val)}")
print()
print("Top 5 salespeople:")
for name, val in top_people.items():
    print(f"  {name:<16} INR {inr(val)}")
print()
print("Dashboard written to sales_dashboard.html - double-click it to open in your browser.")
