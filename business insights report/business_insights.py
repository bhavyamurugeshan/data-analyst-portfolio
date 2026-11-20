"""
PROJECT: Business Insights Report - BharatBazaar (fictional Indian FMCG company)
================================================================================
You are a data analyst at BharatBazaar, a fictional Indian consumer goods
company selling snacks, beverages, personal care and home care products
across India. The founders have asked for the annual business insights
report: not just numbers, but WHAT the numbers mean and WHAT to do next.

What this script does:
  1. Loads one year-pair of line-item sales data (Nov 2024 - Oct 2026)
  2. Computes the headline KPIs (revenue, orders, AOV, margin, growth)
  3. Surfaces 5 concrete INSIGHTS, each with a "so what" recommendation
  4. Ends with the Top 3 priorities for next quarter
  5. Writes a polished, self-contained HTML report (bharatbazaar_report.html)

How to run:
  python business_insights.py
(make sure bharatbazaar_sales.csv sits in the same folder)

Needs only: pandas, plotly   (pip install pandas plotly)
All data is fictional, generated for portfolio practice.
"""

import os
from collections import Counter
from itertools import combinations

import pandas as pd
import plotly.graph_objects as go

# ---------------------------------------------------------------- constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, "bharatbazaar_sales.csv")
HTML_PATH = os.path.join(SCRIPT_DIR, "bharatbazaar_report.html")

YEAR2_START = pd.Timestamp("2025-11-01")   # "this year"  = Nov 2025 - Oct 2026
COMPANY = "BharatBazaar"

PALETTE = {
    "saffron": "#E8821E",
    "maroon": "#7B2D26",
    "teal": "#0E7C7B",
    "gold": "#D4A017",
    "cream": "#FFF8EE",
    "ink": "#3B2F2F",
    "slate": "#6B5E58",
    "green": "#2E7D32",
    "red": "#B03A2E",
}


# ---------------------------------------------------------------- helpers
def inr(amount, symbol="Rs"):
    """Format rupee amounts the Indian way: Rs 850, Rs 4.2 lakh, Rs 1.3 crore."""
    a = abs(amount)
    if a >= 1_00_00_000:
        return f"{symbol} {amount / 1_00_00_000:.2f} crore"
    if a >= 1_00_000:
        return f"{symbol} {amount / 1_00_000:.1f} lakh"
    return f"{symbol} {amount:,.0f}"


def pct(part, whole, digits=1):
    return round(100 * part / whole, digits) if whole else 0.0


def line(char="=", width=66):
    print(char * width)


# ---------------------------------------------------------------- load data
df = pd.read_csv(CSV_PATH, parse_dates=["order_date"])
df["revenue"] = df["quantity"] * df["unit_price"] * (1 - df["discount_pct"] / 100)
df["profit"] = df["revenue"] - df["quantity"] * df["unit_cost"]
df["year"] = df["order_date"].apply(lambda d: "Y2" if d >= YEAR2_START else "Y1")
df["month"] = df["order_date"].dt.to_period("M").dt.to_timestamp()
df["is_weekend"] = df["order_date"].dt.weekday >= 5

y1 = df[df["year"] == "Y1"]
y2 = df[df["year"] == "Y2"]

# ---------------------------------------------------------------- headline KPIs
def kpis(d):
    orders = d["order_id"].nunique()
    rev = d["revenue"].sum()
    return {
        "revenue": rev,
        "orders": orders,
        "aov": rev / orders,
        "profit": d["profit"].sum(),
        "margin": 100 * d["profit"].sum() / rev,
    }

k1, k2 = kpis(y1), kpis(y2)
rev_growth = 100 * (k2["revenue"] - k1["revenue"]) / k1["revenue"]
order_growth = 100 * (k2["orders"] - k1["orders"]) / k1["orders"]

# ---------------------------------------------------------------- insight 1
# Which category is growing fast while its margin quietly shrinks?
cat = df.groupby(["year", "category"]).agg(
    revenue=("revenue", "sum"), profit=("profit", "sum")).reset_index()
cat["margin"] = 100 * cat["profit"] / cat["revenue"]
c1 = cat[cat["year"] == "Y1"].set_index("category")
c2 = cat[cat["year"] == "Y2"].set_index("category")
cat_story = None
for c in c2.index:
    growth = 100 * (c2.loc[c, "revenue"] - c1.loc[c, "revenue"]) / c1.loc[c, "revenue"]
    margin_drop = c1.loc[c, "margin"] - c2.loc[c, "margin"]
    if growth > 15 and margin_drop > 3:
        cat_story = {
            "category": c,
            "growth": growth,
            "rev_y2": c2.loc[c, "revenue"],
            "margin_y1": c1.loc[c, "margin"],
            "margin_y2": c2.loc[c, "margin"],
            "margin_drop": margin_drop,
            "avg_disc_y1": y1[y1["category"] == c]["discount_pct"].mean(),
            "avg_disc_y2": y2[y2["category"] == c]["discount_pct"].mean(),
        }
        break

# ---------------------------------------------------------------- insight 2
# Which region drops the ball on weekends?
reg = y2.groupby(["region", "is_weekend"])["revenue"].sum().unstack()
reg["weekend_share"] = 100 * reg[True] / (reg[True] + reg[False])
weak_region = reg["weekend_share"].idxmin()
weak_share = reg.loc[weak_region, "weekend_share"]
other_share = reg.drop(index=weak_region)["weekend_share"].mean()

# ---------------------------------------------------------------- insight 3
# Which channel brings many small orders (high volume, low AOV)?
ch = df.groupby(["year", "channel"]).agg(
    orders=("order_id", "nunique"), revenue=("revenue", "sum")).reset_index()
ch["aov"] = ch["revenue"] / ch["orders"]
h1 = ch[ch["year"] == "Y1"].set_index("channel")
h2 = ch[ch["year"] == "Y2"].set_index("channel")
ch_growth = (h2["orders"] - h1["orders"]) / h1["orders"] * 100
hot_channel = ch_growth.idxmax()
hot_growth = ch_growth.max()
hot_aov = h2.loc[hot_channel, "aov"]
hot_share = pct(h2.loc[hot_channel, "orders"], k2["orders"])

# ---------------------------------------------------------------- insight 4
# Market-basket: which products are bought together?
baskets = df.groupby("order_id")["product"].apply(lambda s: sorted(set(s)))
pair_counts = Counter()
for items in baskets:
    for pair in combinations(items, 2):
        pair_counts[pair] += 1
top_pairs = pair_counts.most_common(5)
best_pair, best_count = top_pairs[0]
with_a = sum(1 for items in baskets if best_pair[0] in items)
pair_rate = pct(best_count, with_a)

# ---------------------------------------------------------------- insight 5
# How much of the year's revenue is squeezed into the festive window?
daily2 = y2.groupby("order_date")["revenue"].sum()
FESTIVE_START, FESTIVE_END = "2026-10-10", "2026-10-31"   # Diwali build-up, Year 2
festive_mask = (daily2.index >= FESTIVE_START) & (daily2.index <= FESTIVE_END)
festive_rev = daily2[festive_mask].sum()
festive_share = pct(festive_rev, k2["revenue"])
festive_days = int(festive_mask.sum())
top10_share = pct(daily2.nlargest(10).sum(), k2["revenue"])

# ---------------------------------------------------------------- terminal output
line()
print(f"  {COMPANY.upper()} - BUSINESS INSIGHTS REPORT")
print("  Fictional data  |  Y1: Nov 2024-Oct 2025  |  Y2: Nov 2025-Oct 2026")
line()
print("\nKEY NUMBERS (Year 2)")
print(f"  Revenue        : {inr(k2['revenue'])}  (up {rev_growth:.1f}% vs last year)")
print(f"  Orders         : {k2['orders']:,}  (up {order_growth:.1f}%)")
print(f"  Avg order value: {inr(k2['aov'])}")
print(f"  Gross profit   : {inr(k2['profit'])}  ({k2['margin']:.1f}% margin)")

line("-")
print("INSIGHT 1 - Growth that eats its own margin")
line("-")
print(f"  {cat_story['category']} revenue grew {cat_story['growth']:.0f}% to "
      f"{inr(cat_story['rev_y2'])} - the fastest of any category.")
print(f"  But its margin fell from {cat_story['margin_y1']:.0f}% to "
      f"{cat_story['margin_y2']:.0f}% in the same year.")
print(f"  Reason: average discount jumped from {cat_story['avg_disc_y1']:.0f}% "
      f"to {cat_story['avg_disc_y2']:.0f}%.")
print("  SO WHAT: We are buying growth with discounts. Cap beverage discounts")
print("  at 15% and test bundle pricing before the next festive season.")

line("-")
print("INSIGHT 2 - The West region sleeps on weekends")
line("-")
print(f"  Weekends bring only {weak_share:.0f}% of {weak_region}'s revenue,")
print(f"  vs {other_share:.0f}% for the rest of India. Saturday-Sunday demand")
print(f"  exists everywhere else - {weak_region} is simply not showing up.")
print(f"  SO WHAT: Check weekend staffing and delivery coverage in Mumbai,")
print(f"  Pune and Ahmedabad, and run a weekend-only promo there.")

line("-")
print(f"INSIGHT 3 - {hot_channel}: many orders, tiny baskets")
line("-")
print(f"  {hot_channel} orders grew {hot_growth:.0f}% (the fastest channel) and")
print(f"  now make {hot_share:.0f}% of all orders - but AOV is just "
      f"{inr(hot_aov)},")
print(f"  roughly a fourth of the company average ({inr(k2['aov'])}).")
print("  SO WHAT: Nudge bigger baskets - 'add Rs 50 more for free delivery'")
print("  and 2-pack combos built for this channel.")

line("-")
print("INSIGHT 4 - A ready-made combo is hiding in the cart data")
line("-")
print(f"  {pair_rate:.0f}% of orders that include {best_pair[0]} also include")
print(f"  {best_pair[1]}. That is {best_count:,} orders - our strongest")
print("  product pair by far.")
print("  SO WHAT: Sell them as a named festive combo box and place them")
print("  together on every channel shelf.")

line("-")
print("INSIGHT 5 - The festive window carries the year")
line("-")
print(f"  Just {festive_days} festive-season days (10-31 Oct) brought {inr(festive_rev)},")
print(f"  which is {festive_share:.0f}% of the whole year's revenue. The top 10")
print(f"  days alone hold {top10_share:.0f}%.")
print("  SO WHAT: Lock festive stock and ad budgets 6 weeks early; a stockout")
print("  in late October costs more than a slow quarter.")

line()
print("TOP 3 PRIORITIES FOR NEXT QUARTER")
line()
print(f"  1. Fix {cat_story['category']} margins - discount cap + bundle pricing.")
print(f"  2. Win back {weak_region} weekends - coverage check + weekend promo.")
print(f"  3. Grow {hot_channel} basket size - free-delivery threshold + combos.")
line()

print(f"\nReport saved as: {os.path.basename(HTML_PATH)}")
print("Open it by double-clicking the file. No internet needed.")
print('\nINTERVIEW HOOK: "I turned raw line-item sales into a business')
print('insights report - KPIs, margin diagnostics, channel mix and market-')
print('basket analysis - and shipped it as a one-file HTML report."')
line()

# ---------------------------------------------------------------- charts
BASE_LAYOUT = dict(
    font=dict(family="Segoe UI, Arial", color=PALETTE["ink"], size=13),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=50, r=30, t=55, b=45),
    height=360,
)

def fig_monthly():
    m = df.groupby(["year", "month"])["revenue"].sum().reset_index()
    fig = go.Figure()
    for yr, color, name in [("Y1", "#C9B8A8", "Nov 2024 - Oct 2025"),
                            ("Y2", PALETTE["saffron"], "Nov 2025 - Oct 2026")]:
        d = m[m["year"] == yr]
        fig.add_trace(go.Scatter(x=d["month"], y=d["revenue"], mode="lines+markers",
                                 name=name, line=dict(color=color, width=3)))
    fig.update_layout(title="Monthly revenue - the festive spike repeats",
                      yaxis_title="Revenue (Rs)", legend=dict(orientation="h", y=1.12),
                      **BASE_LAYOUT)
    return fig

def fig_category():
    cats = c2.index.tolist()
    growth = [100 * (c2.loc[c, "revenue"] - c1.loc[c, "revenue"]) / c1.loc[c, "revenue"] for c in cats]
    fig = go.Figure(go.Bar(
        x=cats, y=growth,
        marker_color=[PALETTE["saffron"] if c == cat_story["category"] else "#C9B8A8" for c in cats],
        text=[f"+{g:.0f}%" for g in growth], textposition="outside"))
    fig.update_layout(title="Revenue growth by category (Year 2 vs Year 1)",
                      yaxis_title="Growth %", **BASE_LAYOUT)
    return fig

def fig_margin():
    cats = c2.index.tolist()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=cats, y=[c1.loc[c, "margin"] for c in cats],
                         name="Year 1", marker_color="#C9B8A8"))
    fig.add_trace(go.Bar(x=cats, y=[c2.loc[c, "margin"] for c in cats],
                         name="Year 2", marker_color=PALETTE["maroon"]))
    fig.update_layout(title="Gross margin % by category - beverages slipped",
                      yaxis_title="Margin %", barmode="group",
                      legend=dict(orientation="h", y=1.12), **BASE_LAYOUT)
    return fig

def fig_region_weekend():
    regions = reg.index.tolist()
    wk = [100 * reg.loc[r, False] / (reg.loc[r, True] + reg.loc[r, False]) for r in regions]
    we = [reg.loc[r, "weekend_share"] for r in regions]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=regions, y=wk, name="Weekday", marker_color="#C9B8A8"))
    fig.add_trace(go.Bar(x=regions, y=we, name="Weekend",
                         marker_color=[PALETTE["red"] if r == weak_region else PALETTE["teal"]
                                       for r in regions]))
    fig.update_layout(title=f"Where the weekend revenue comes from (Year 2) - {weak_region} lags",
                      yaxis_title="Share of region revenue %", barmode="stack",
                      legend=dict(orientation="h", y=1.12), **BASE_LAYOUT)
    return fig

def fig_channel():
    channels = h2.sort_values("orders", ascending=False).index.tolist()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=channels, y=[h2.loc[c, "orders"] for c in channels],
                         name="Orders (Year 2)", marker_color=PALETTE["teal"]))
    fig.add_trace(go.Scatter(x=channels, y=[h2.loc[c, "aov"] for c in channels],
                             name="Avg order value (Rs)", mode="lines+markers",
                             line=dict(color=PALETTE["gold"], width=3), yaxis="y2"))
    layout = dict(BASE_LAYOUT)
    layout["margin"] = dict(l=50, r=30, t=90, b=45)
    fig.update_layout(title="Channel mix - volume vs basket size (Year 2)",
                      yaxis=dict(title="Orders"),
                      yaxis2=dict(title="AOV (Rs)", overlaying="y", side="right"),
                      legend=dict(orientation="h", y=1.14), **layout)
    return fig

def fig_pairs():
    labels = [f"{a} + {b}" for (a, b), _ in top_pairs][::-1]
    values = [n for _, n in top_pairs][::-1]
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h",
                           marker_color=PALETTE["saffron"], text=values,
                           textposition="outside"))
    fig.update_layout(title="Top product pairs in the same order (market basket)",
                      xaxis_title="Orders containing both", **BASE_LAYOUT)
    return fig

def fig_festive():
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily2.index, y=daily2.values, mode="lines",
                             line=dict(color=PALETTE["saffron"], width=1.5),
                             name="Daily revenue"))
    fig.add_vrect(x0=FESTIVE_START, x1=FESTIVE_END, fillcolor=PALETTE["gold"],
                  opacity=0.25, line_width=0,
                  annotation_text="festive window", annotation_position="top left")
    fig.update_layout(title=f"Daily revenue (Year 2) - {festive_share:.0f}% of the year in {festive_days} days",
                      yaxis_title="Revenue (Rs)", **BASE_LAYOUT)
    return fig

figures = [fig_monthly(), fig_category(), fig_margin(),
           fig_region_weekend(), fig_channel(), fig_pairs(), fig_festive()]

# ---------------------------------------------------------------- HTML report
chart_html = []
for i, fig in enumerate(figures):
    chart_html.append(fig.to_html(full_html=False, include_plotlyjs=(i == 0)))

def rs(amount):
    return inr(amount, symbol="&#8377;")  # rupee sign for the web page

INSIGHT_CARDS = f"""
<div class="insight">
  <h3><span class="num">1</span> Growth that eats its own margin</h3>
  <p><b>{cat_story['category']}</b> revenue grew <b>{cat_story['growth']:.0f}%</b> to
  {rs(cat_story['rev_y2'])} - the fastest of any category. But its gross margin fell from
  {cat_story['margin_y1']:.0f}% to {cat_story['margin_y2']:.0f}%, because the average discount
  jumped from {cat_story['avg_disc_y1']:.0f}% to {cat_story['avg_disc_y2']:.0f}%.</p>
  <p class="sowhat"><b>So what:</b> we are buying growth with discounts. Cap beverage
  discounts at 15% and test bundle pricing before the next festive season.</p>
</div>
<div class="insight">
  <h3><span class="num">2</span> The West region sleeps on weekends</h3>
  <p>Weekends bring only <b>{weak_share:.0f}%</b> of {weak_region}'s revenue, vs
  <b>{other_share:.0f}%</b> for the rest of India. Weekend demand exists everywhere else -
  {weak_region} is simply not showing up.</p>
  <p class="sowhat"><b>So what:</b> check weekend staffing and delivery coverage in Mumbai,
  Pune and Ahmedabad, and run a weekend-only promo there.</p>
</div>
<div class="insight">
  <h3><span class="num">3</span> {hot_channel}: many orders, tiny baskets</h3>
  <p>{hot_channel} orders grew <b>{hot_growth:.0f}%</b> - the fastest of any channel - and now
  make <b>{hot_share:.0f}%</b> of all orders. But average order value is just
  <b>{rs(hot_aov)}</b>, roughly a fourth of the company average ({rs(k2['aov'])}).</p>
  <p class="sowhat"><b>So what:</b> nudge bigger baskets with a free-delivery threshold and
  2-pack combos built for this channel.</p>
</div>
<div class="insight">
  <h3><span class="num">4</span> A ready-made combo is hiding in the cart data</h3>
  <p><b>{pair_rate:.0f}%</b> of orders that include <b>{best_pair[0]}</b> also include
  <b>{best_pair[1]}</b> - {best_count:,} orders, our strongest product pair by far.</p>
  <p class="sowhat"><b>So what:</b> sell them as a named festive combo box and place them
  together on every channel shelf.</p>
</div>
<div class="insight">
  <h3><span class="num">5</span> The festive window carries the year</h3>
  <p>Just <b>{festive_days} festive-season days</b> (10-31 October) brought {rs(festive_rev)} -
  <b>{festive_share:.0f}%</b> of the whole year's revenue. The top 10 days alone hold
  <b>{top10_share:.0f}%</b>.</p>
  <p class="sowhat"><b>So what:</b> lock festive stock and ad budgets 6 weeks early; a
  stockout in late October costs more than a slow quarter.</p>
</div>
"""

chart_sections = ""
chart_titles = ["The year in revenue", "Category growth", "Margin watch",
                "Weekend gap by region", "Channel mix", "Market basket", "Festive concentration"]
for title, ch_html in zip(chart_titles, chart_html):
    chart_sections += f'<div class="card chart"><h2>{title}</h2>{ch_html}</div>\n'

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{COMPANY} - Business Insights Report</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; font-family: "Segoe UI", Arial, sans-serif; color: {PALETTE['ink']};
    background: linear-gradient(160deg, #FFF4E0 0%, #FBE8D0 45%, #F3D9C2 100%);
    background-attachment: fixed;
  }}
  .wrap {{ max-width: 1020px; margin: 0 auto; padding: 24px 18px 60px; }}
  header {{
    text-align: center; padding: 46px 20px 34px; border-radius: 22px;
    background: linear-gradient(135deg, {PALETTE['maroon']} 0%, #A0522D 55%, {PALETTE['saffron']} 100%);
    color: #FFF6EA; box-shadow: 0 12px 30px rgba(123,45,38,.28);
    animation: rise .8s ease both;
  }}
  header h1 {{ margin: 0 0 8px; font-size: 2.1rem; letter-spacing: .5px; }}
  header p {{ margin: 4px 0; opacity: .92; }}
  .badge {{
    display: inline-block; margin-top: 12px; padding: 5px 14px; border-radius: 999px;
    background: rgba(255,255,255,.16); font-size: .85rem; letter-spacing: .4px;
  }}
  .kpis {{ display: flex; flex-wrap: wrap; gap: 14px; margin: 22px 0; }}
  .kpi {{
    flex: 1 1 160px; background: #FFFDF8; border-radius: 16px; padding: 18px 16px;
    box-shadow: 0 6px 18px rgba(123,45,38,.10); border-top: 4px solid {PALETTE['saffron']};
    animation: rise .8s ease both;
  }}
  .kpi:nth-child(2) {{ animation-delay: .08s; border-top-color: {PALETTE['teal']}; }}
  .kpi:nth-child(3) {{ animation-delay: .16s; border-top-color: {PALETTE['gold']}; }}
  .kpi:nth-child(4) {{ animation-delay: .24s; border-top-color: {PALETTE['maroon']}; }}
  .kpi:nth-child(5) {{ animation-delay: .32s; border-top-color: {PALETTE['green']}; }}
  .kpi .v {{ font-size: 1.35rem; font-weight: 700; }}
  .kpi .l {{ font-size: .82rem; color: {PALETTE['slate']}; margin-top: 4px; }}
  .kpi .d {{ font-size: .8rem; margin-top: 6px; color: {PALETTE['green']}; font-weight: 600; }}
  h2.section {{ margin: 34px 4px 14px; font-size: 1.25rem; color: {PALETTE['maroon']};
                letter-spacing: .3px; }}
  .insight {{
    background: #FFFDF8; border-left: 6px solid {PALETTE['saffron']}; border-radius: 14px;
    padding: 18px 22px; margin: 14px 0; box-shadow: 0 6px 18px rgba(123,45,38,.10);
    animation: rise .8s ease both;
  }}
  .insight h3 {{ margin: 0 0 8px; color: {PALETTE['maroon']}; font-size: 1.08rem; }}
  .insight .num {{
    display: inline-block; width: 26px; height: 26px; line-height: 26px; text-align: center;
    background: {PALETTE['saffron']}; color: #fff; border-radius: 50%; margin-right: 8px;
    font-size: .9rem;
  }}
  .insight p {{ margin: 6px 0; line-height: 1.55; }}
  .sowhat {{ background: #FDF1DC; border-radius: 10px; padding: 10px 14px; }}
  .card {{
    background: #FFFDF8; border-radius: 16px; padding: 14px 10px 6px; margin: 16px 0;
    box-shadow: 0 6px 18px rgba(123,45,38,.10); animation: rise .8s ease both;
  }}
  .card h2 {{ font-size: 1.02rem; color: {PALETTE['slate']}; margin: 6px 12px 0; }}
  .priorities {{
    margin-top: 30px; padding: 24px 26px; border-radius: 18px; color: #FFF6EA;
    background: linear-gradient(135deg, {PALETTE['teal']} 0%, #0A5F5E 100%);
    box-shadow: 0 12px 26px rgba(14,124,123,.30); animation: rise .8s ease both;
  }}
  .priorities h2 {{ margin: 0 0 12px; }}
  .priorities ol {{ margin: 0; padding-left: 22px; line-height: 1.9; font-size: 1.02rem; }}
  footer {{ text-align: center; margin-top: 34px; color: {PALETTE['slate']}; font-size: .9rem; }}
  footer .hook {{
    background: #FFFDF8; border-radius: 14px; padding: 16px 20px; margin-bottom: 14px;
    box-shadow: 0 6px 18px rgba(123,45,38,.10); font-style: italic;
  }}
  @keyframes rise {{ from {{ opacity: 0; transform: translateY(18px); }}
                     to {{ opacity: 1; transform: translateY(0); }} }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>{COMPANY} - Business Insights Report</h1>
    <p>Annual review: November 2025 - October 2026, compared with the previous year</p>
    <p>Prepared by the Data Analyst desk</p>
    <span class="badge">Fictional company &amp; data - portfolio project</span>
  </header>

  <div class="kpis">
    <div class="kpi"><div class="v">{rs(k2['revenue'])}</div><div class="l">Revenue (Year 2)</div>
      <div class="d">up {rev_growth:.1f}% vs last year</div></div>
    <div class="kpi"><div class="v">{k2['orders']:,}</div><div class="l">Orders</div>
      <div class="d">up {order_growth:.1f}% vs last year</div></div>
    <div class="kpi"><div class="v">{rs(k2['aov'])}</div><div class="l">Avg order value</div></div>
    <div class="kpi"><div class="v">{rs(k2['profit'])}</div><div class="l">Gross profit</div></div>
    <div class="kpi"><div class="v">{k2['margin']:.1f}%</div><div class="l">Gross margin</div></div>
  </div>

  <h2 class="section">What the numbers are telling us</h2>
  {INSIGHT_CARDS}

  <h2 class="section">The charts behind the story</h2>
  {chart_sections}

  <div class="priorities">
    <h2>Top 3 priorities for next quarter</h2>
    <ol>
      <li>Fix {cat_story['category']} margins - cap discounts, test bundle pricing.</li>
      <li>Win back {weak_region} weekends - coverage check plus a weekend promo.</li>
      <li>Grow {hot_channel} basket size - free-delivery threshold and 2-pack combos.</li>
    </ol>
  </div>

  <footer>
    <div class="hook">Interview hook: "I turned raw line-item sales into a business insights
    report - KPIs, margin diagnostics, channel mix and market-basket analysis - and shipped it
    as a one-file HTML report that opens with a double-click."</div>
    Built with Python (pandas + Plotly) &middot; {COMPANY} is a fictional company
  </footer>
</div>
</body>
</html>
"""

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)
