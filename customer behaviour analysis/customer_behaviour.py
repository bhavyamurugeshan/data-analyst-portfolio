#!/usr/bin/env python3
"""
customer_behaviour.py - Customer behaviour analysis for "Dukaan24",
a FICTIONAL Indian online store (practice data, not real customers).

What it does:
  1. Loads dukaan24_orders.csv with pandas
  2. Runs RFM segmentation (Recency, Frequency, Monetary) - a classic
     customer-analysis technique used by real e-commerce teams
  3. Finds shopping-time patterns, festive spikes and discount behaviour
  4. Prints a summary to the terminal
  5. Builds dukaan24_report.html - an animated, self-contained dashboard

Needs: pandas  (pip install pandas)
Run:   python customer_behaviour.py
"""

import pandas as pd

CSV_FILE = "dukaan24_orders.csv"
OUT_HTML = "dukaan24_report.html"

# ---------------------------------------------------------------- load
df = pd.read_csv(CSV_FILE, parse_dates=["order_date"])

n_orders = len(df)
n_customers = df["customer_id"].nunique()
date_min = df["order_date"].min()
date_max = df["order_date"].max()
total_rev = df["amount"].sum()
aov = df["amount"].mean()

# repeat vs one-time
orders_per_cust = df.groupby("customer_id").size()
one_timers = int((orders_per_cust == 1).sum())
repeaters = n_customers - one_timers
rev_one = df[df["customer_id"].isin(orders_per_cust[orders_per_cust == 1].index)]["amount"].sum()
one_rev_share = rev_one / total_rev * 100

# ---------------------------------------------------------------- RFM
snapshot = date_max + pd.Timedelta(days=1)
rfm = df.groupby("customer_id").agg(
    recency=("order_date", lambda s: (snapshot - s.max()).days),
    frequency=("order_id", "count"),
    monetary=("amount", "sum"),
)
rfm["R"] = pd.qcut(rfm["recency"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
rfm["F"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
rfm["M"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)


def segment(r, f):
    if r >= 4 and f >= 5:
        return "Champions"
    if r >= 3 and f >= 4:
        return "Loyal Customers"
    if r >= 4 and f >= 2:
        return "Potential Loyalists"
    if r >= 4:
        return "New Customers"
    if r == 3 and f <= 2:
        return "Promising"
    if r <= 2 and f >= 3:
        return "At Risk"
    if r <= 2:
        return "Hibernating"
    return "Needs Attention"


rfm["segment"] = [segment(r, f) for r, f in zip(rfm["R"], rfm["F"])]

SEG_ORDER = ["Champions", "Loyal Customers", "Potential Loyalists", "Promising",
             "New Customers", "At Risk", "Hibernating", "Needs Attention"]
SEG_COLORS = {"Champions": "#ffd166", "Loyal Customers": "#06d6a0",
              "Potential Loyalists": "#4cc9f0", "Promising": "#b5179e",
              "New Customers": "#f72585", "At Risk": "#ff9e00",
              "Hibernating": "#8d99ae", "Needs Attention": "#c77dff"}

seg_stats = []
for s in SEG_ORDER:
    sub = rfm[rfm["segment"] == s]
    if len(sub) == 0:
        continue
    seg_stats.append({
        "name": s,
        "customers": int(len(sub)),
        "cust_share": len(sub) / n_customers * 100,
        "revenue": float(sub["monetary"].sum()),
        "rev_share": sub["monetary"].sum() / total_rev * 100,
        "avg_spend": float(sub["monetary"].mean()),
        "aov": float(sub["monetary"].sum() / sub["frequency"].sum()),
        "avg_orders": float(sub["frequency"].mean()),
    })

champ = next(s for s in seg_stats if s["name"] == "Champions")

# ---------------------------------------------------------------- time patterns
df["weekday"] = df["order_date"].dt.weekday  # Mon=0
df["hour"] = df["order_date"].dt.hour
WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
heat = [[0] * 24 for _ in range(7)]
for _, row in df.iterrows():
    heat[int(row["weekday"])][int(row["hour"])] += 1
heat_max = max(max(r) for r in heat)
day_counts = df["weekday"].value_counts()
best_day_i = int(day_counts.idxmax())
best_day_pct = day_counts.max() / n_orders * 100
hour_counts = df["hour"].value_counts()
best_hr = int(hour_counts.idxmax())
best_hr_pct = hour_counts.max() / n_orders * 100
hr_label = f"{(best_hr - 12) if best_hr > 12 else best_hr}-{(best_hr - 11) if best_hr > 12 else best_hr + 1} " + ("PM" if best_hr >= 12 else "AM")
weekend_share = df[df["weekday"] >= 5].shape[0] / n_orders * 100
evening_share = df[(df["hour"] >= 18) & (df["hour"] <= 23)].shape[0] / n_orders * 100

# ---------------------------------------------------------------- monthly + Diwali
df["month"] = df["order_date"].dt.to_period("M").astype(str)
monthly = df.groupby("month")["amount"].sum()
months = list(monthly.index)
month_vals = [float(v) for v in monthly.values]

DIW0, DIW1 = pd.Timestamp("2025-10-06"), pd.Timestamp("2025-10-26 23:59")
fest = df[(df["order_date"] >= DIW0) & (df["order_date"] <= DIW1)]
fest_orders = len(fest)
fest_rev = float(fest["amount"].sum())
fest_rev_share = fest_rev / total_rev * 100
total_weeks = (date_max - date_min).days / 7
normal_week_orders = (n_orders - fest_orders) / (total_weeks - 3)
fest_mult = (fest_orders / 3) / normal_week_orders
fest_peak_month = pd.Period(df.groupby(df["order_date"].dt.to_period("M"))["amount"].sum().idxmax()).strftime("%b %Y")

# ---------------------------------------------------------------- discount behaviour
disc = df.groupby("customer_id")["discount_pct"].mean()
hunters = set(disc[disc >= 15].index)
fans = set(disc[disc <= 5].index)
n_hunt, n_fan = len(hunters), len(fans)
n_mixed = n_customers - n_hunt - n_fan
hunt_aov = df[df["customer_id"].isin(hunters)]["amount"].mean()
fan_aov = df[df["customer_id"].isin(fans)]["amount"].mean()
hunt_avg_disc = disc[disc >= 15].mean()
hunt_fest_share = len(fest[fest["customer_id"].isin(hunters)]) / max(1, len(df[df["customer_id"].isin(hunters)])) * 100

# ---------------------------------------------------------------- categories
cat_rev = df.groupby("category")["amount"].sum().sort_values(ascending=False)
top_cat = cat_rev.index[0]
champ_ids = rfm[rfm["segment"] == "Champions"].index
champ_cat = df[df["customer_id"].isin(champ_ids)].groupby("category")["amount"].sum().sort_values(ascending=False)

# ---------------------------------------------------------------- helpers
def crore(x):
    return f"Rs {x / 1e7:.2f} crore"

def lakh(x):
    return f"Rs {x / 1e5:.2f} lakh"

def money(x):
    return f"Rs {x:,.0f}"

def pct(x):
    return f"{x:.1f}%"

# ---------------------------------------------------------------- terminal summary
print("=" * 60)
print("  DUKAAN24 - CUSTOMER BEHAVIOUR ANALYSIS  (fictional data)")
print("=" * 60)
print(f"Rows loaded: {n_orders}  |  Customers: {n_customers}")
print(f"Period: {date_min:%d %b %Y} - {date_max:%d %b %Y}")
print(f"Total revenue: {crore(total_rev)}  |  Avg order value: {money(aov)}")
print(f"Repeat customers: {repeaters} ({pct(repeaters / n_customers * 100)})  |  "
      f"One-time: {one_timers} ({pct(one_timers / n_customers * 100)})")
print(f"One-timers bring only {pct(one_rev_share)} of revenue")
print()
print("--- RFM SEGMENTS ------------------------------------------")
for s in seg_stats:
    print(f"{s['name']:<20} {s['customers']:>4} customers ({pct(s['cust_share']):>5})  "
          f"revenue share {pct(s['rev_share']):>5}  avg spend {money(s['avg_spend'])}")
print(f"Champions = {pct(champ['cust_share'])} of customers but {pct(champ['rev_share'])} of revenue")
print()
print("--- WHEN INDIA SHOPS --------------------------------------")
print(f"Best day: {WD[best_day_i]} ({pct(best_day_pct)} of orders)")
print(f"Peak hour: {hr_label} ({pct(best_hr_pct)} of orders)")
print(f"Weekend share: {pct(weekend_share)}  |  6 PM-midnight share: {pct(evening_share)}")
print()
print("--- THE DIWALI WAVE ---------------------------------------")
print(f"Festive window (6-26 Oct 2025): {fest_orders} orders, {lakh(fest_rev)} "
      f"= {pct(fest_rev_share)} of all revenue")
print(f"Orders ran {fest_mult:.1f}x a normal week; peak month {fest_peak_month}")
print()
print("--- DISCOUNT HUNTERS vs FULL-PRICE FANS -------------------")
print(f"Hunters: {n_hunt} customers, avg discount {hunt_avg_disc:.1f}%, AOV {money(hunt_aov)}")
print(f"Full-price fans: {n_fan} customers, AOV {money(fan_aov)}")
print(f"{pct(hunt_fest_share)} of hunters' orders land in the Diwali window")
print()
print("--- WHAT THEY BUY -----------------------------------------")
print(f"Top category overall: {top_cat} ({lakh(cat_rev.iloc[0])})")
print("Champions' top 3: " + ", ".join(f"{c} ({lakh(v)})" for c, v in champ_cat.head(3).items()))
print()
print(f"Dashboard written to {OUT_HTML} - double-click it to open the story.")

# ================================================================ dashboard
cr_val = total_rev / 1e7
rep_pct = repeaters / n_customers * 100

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:#0d1b2a;color:#e9ecef;overflow-x:hidden}
#progress{position:fixed;top:0;left:0;height:4px;width:0;background:linear-gradient(90deg,#f72585,#ffd166,#06d6a0);z-index:99;transition:width .1s linear}
.blob{position:fixed;border-radius:50%;filter:blur(90px);opacity:.25;z-index:0;pointer-events:none;animation:drift 18s ease-in-out infinite alternate}
@keyframes drift{from{transform:translate(0,0) scale(1)}to{transform:translate(60px,-50px) scale(1.15)}}
.wrap{position:relative;z-index:1;max-width:1000px;margin:0 auto;padding:0 20px}
.hero{min-height:92vh;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center}
.badge{display:inline-block;background:#f72585;color:#fff;font-size:.72rem;letter-spacing:.18em;padding:6px 16px;border-radius:999px;font-weight:700;animation:pulse 2.4s infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(247,37,133,.5)}50%{box-shadow:0 0 0 14px rgba(247,37,133,0)}}
h1{font-size:clamp(2rem,6vw,3.6rem);margin:22px 0 10px;background:linear-gradient(90deg,#ffd166,#f72585,#4cc9f0);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero p.sub{color:#adb5bd;font-size:1.05rem;max-width:560px}
.cue{margin-top:44px;font-size:1.6rem;animation:bob 1.6s ease-in-out infinite}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(10px)}}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin:-40px 0 70px}
.kpi{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.09);border-radius:18px;padding:22px;text-align:center;backdrop-filter:blur(6px);opacity:0;transform:translateY(26px);transition:all .7s cubic-bezier(.2,.8,.2,1)}
.kpi.in{opacity:1;transform:none}
.kpi .num{font-size:1.9rem;font-weight:800;color:#ffd166}
.kpi .lbl{color:#adb5bd;font-size:.85rem;margin-top:6px}
section{margin:0 0 84px;opacity:0;transform:translateY(34px);transition:all .8s cubic-bezier(.2,.8,.2,1)}
section.in{opacity:1;transform:none}
h2{font-size:1.55rem;margin-bottom:6px}
.lede{color:#adb5bd;margin-bottom:26px;font-size:.95rem;max-width:640px}
.panel{background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:24px}
.bar-row{display:flex;align-items:center;gap:10px;margin:9px 0}
.bar-row .nm{width:140px;font-size:.8rem;text-align:right;color:#ced4da;flex-shrink:0}
.bar-track{flex:1;background:rgba(255,255,255,.06);border-radius:8px;height:22px;overflow:hidden}
.bar{height:100%;width:0;border-radius:8px;transition:width 1.2s cubic-bezier(.2,.8,.2,1)}
.bar-row .val{width:86px;font-size:.78rem;color:#adb5bd;flex-shrink:0}
.two{display:grid;grid-template-columns:1fr 1fr;gap:22px}
@media(max-width:760px){.two{grid-template-columns:1fr}}
.callout{border-left:4px solid #ffd166;background:rgba(255,209,102,.08);padding:14px 18px;border-radius:0 14px 14px 0;margin-top:20px;font-size:.92rem;color:#f1f3f5}
.heat-scroll{overflow-x:auto}
table.heat{border-collapse:separate;border-spacing:3px;margin:0 auto}
table.heat th{font-size:.66rem;color:#8d99ae;font-weight:600;padding:2px}
table.heat td{width:30px;height:26px;border-radius:6px;text-align:center;font-size:.6rem;color:#212529;opacity:0;transform:scale(.4);transition:all .45s cubic-bezier(.34,1.56,.64,1)}
.in table.heat td,section.in td{opacity:1;transform:scale(1)}
td.peak{outline:2px solid #ffd166;outline-offset:1px;font-weight:800}
.legend{display:flex;align-items:center;gap:8px;justify-content:center;margin-top:12px;font-size:.72rem;color:#8d99ae}
.legend .sw{width:22px;height:12px;border-radius:4px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:18px}
.card{background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.09);border-radius:18px;padding:22px;opacity:0;transform:perspective(600px) rotateX(-14deg) translateY(20px);transition:all .7s cubic-bezier(.2,.8,.2,1)}
section.in .card{opacity:1;transform:none}
.card h3{font-size:1rem;margin-bottom:8px}
.card p{font-size:.85rem;color:#adb5bd;line-height:1.5}
.card .big{font-size:1.5rem;font-weight:800;margin:4px 0}
.green .card{border-top:4px solid #06d6a0}
.chip{display:inline-block;background:rgba(76,201,240,.14);border:1px solid rgba(76,201,240,.4);color:#a5e3f5;border-radius:999px;padding:7px 16px;margin:5px;font-size:.84rem;opacity:0;transform:translateY(12px);transition:all .5s ease}
section.in .chip{opacity:1;transform:none}
footer{text-align:center;color:#6c757d;font-size:.78rem;padding:34px 0 50px}
.mono{font-variant-numeric:tabular-nums}
@media (prefers-reduced-motion: reduce){
 *{animation:none!important;transition:none!important}
 section,.kpi,.card,.chip,table.heat td{opacity:1!important;transform:none!important}
 .bar{transition:none!important}
 #trend{stroke-dashoffset:0!important}
 .dot{opacity:1!important}
}
"""

JS = """
const reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
document.querySelectorAll('.fill').forEach(b=>{b.style.width=b.dataset.w+'%';});
if(reduce){
 document.querySelectorAll('section,.kpi,.card,.chip').forEach(e=>e.classList.add('in'));
 document.querySelectorAll('.count').forEach(el=>{el.textContent=el.dataset.final;});
}else{
 const io=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},{threshold:.15});
 document.querySelectorAll('section,.kpi').forEach(e=>io.observe(e));
 function runCount(el){const t=+el.dataset.target,dec=+el.dataset.dec||0,pre=el.dataset.pre||'',suf=el.dataset.suf||'';const t0=performance.now(),D=1600;
  (function tick(now){const p=Math.min(1,(now-t0)/D),e=1-Math.pow(1-p,3);el.textContent=pre+(t*e).toLocaleString('en-IN',{minimumFractionDigits:dec,maximumFractionDigits:dec})+suf;if(p<1)requestAnimationFrame(tick);})(t0);}
 const cio=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){runCount(e.target);cio.unobserve(e.target);}});},{threshold:.4});
 document.querySelectorAll('.count').forEach(e=>cio.observe(e));
 const path=document.getElementById('trend');
 if(path){const pio=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){path.style.strokeDashoffset='0';document.querySelectorAll('.dot').forEach((d,i)=>setTimeout(()=>d.style.opacity='1',i*70));pio.unobserve(path);}});},{threshold:.3});pio.observe(path);}
}
window.addEventListener('scroll',()=>{const h=document.documentElement;document.getElementById('progress').style.width=(h.scrollTop/(h.scrollHeight-h.clientHeight)*100)+'%';});
"""

# ---- segment bar charts
max_c = max(s["cust_share"] for s in seg_stats)
max_r = max(s["rev_share"] for s in seg_stats)
bars_c, bars_r = "", ""
for s in seg_stats:
    col = SEG_COLORS[s["name"]]
    bars_c += (f"<div class='bar-row'><div class='nm'>{s['name']}</div>"
               f"<div class='bar-track'><div class='bar fill' data-w='{s['cust_share'] / max_c * 100:.1f}' style='background:{col}'></div></div>"
               f"<div class='val mono'>{s['customers']} ({s['cust_share']:.1f}%)</div></div>")
    bars_r += (f"<div class='bar-row'><div class='nm'>{s['name']}</div>"
               f"<div class='bar-track'><div class='bar fill' data-w='{s['rev_share'] / max_r * 100:.1f}' style='background:{col}'></div></div>"
               f"<div class='val mono'>{s['rev_share']:.1f}%</div></div>")

# ---- heatmap
HRL = {0: "12a", 3: "3a", 6: "6a", 9: "9a", 12: "12p", 15: "3p", 18: "6p", 21: "9p"}
heat_html = "<table class='heat'><tr><th></th>"
for h in range(24):
    heat_html += f"<th>{HRL.get(h, '')}</th>"
heat_html += "</tr>"
for d in range(7):
    heat_html += f"<tr><th>{WD[d]}</th>"
    for h in range(24):
        v = heat[d][h]
        a = 0.10 + 0.90 * (v / heat_max)
        peak = " class='peak'" if v == heat_max else ""
        delay = (d * 24 + h) * 6
        heat_html += (f"<td{peak} title='{WD[d]} {h:02d}:00 - {v} orders' "
                      f"style='background:rgba(255,159,28,{a:.2f});transition-delay:{delay}ms'>{v if a > 0.55 else ''}</td>")
    heat_html += "</tr>"
heat_html += "</table>"

# ---- monthly trend svg
W, H, PL, PB, PT = 920, 280, 46, 34, 26
iw, ih = W - PL - 20, H - PT - PB
mn, mx = min(month_vals), max(month_vals)
pts = []
for i, v in enumerate(month_vals):
    x = PL + iw * i / (len(month_vals) - 1)
    y = PT + ih * (1 - (v - mn) / (mx - mn))
    pts.append((x, y))
path_d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
area_d = path_d + f" L{pts[-1][0]:.1f} {PT + ih} L{pts[0][0]:.1f} {PT + ih} Z"
grid, dots, labs = "", "", ""
for f in (0, .25, .5, .75, 1):
    y = PT + ih * (1 - f)
    val = mn + (mx - mn) * f
    grid += (f"<line x1='{PL}' y1='{y:.1f}' x2='{W - 20}' y2='{y:.1f}' stroke='rgba(255,255,255,.08)'/>"
             f"<text x='{PL - 6}' y='{y + 3:.1f}' fill='#6c757d' font-size='9' text-anchor='end'>{val / 1e5:.0f}L</text>")
for i, (x, y) in enumerate(pts):
    mon = months[i]
    is_pk = mon == "2025-10"
    dots += (f"<circle class='dot' cx='{x:.1f}' cy='{y:.1f}' r='{5.5 if is_pk else 3}' "
             f"fill='{'#ffd166' if is_pk else '#4cc9f0'}' style='opacity:0;transition:opacity .3s'/>")
    if i % 2 == 0 or is_pk:
        labs += f"<text x='{x:.1f}' y='{PT + ih + 16}' fill='#6c757d' font-size='8.5' text-anchor='middle'>{pd.Period(mon).strftime('%b %y')}</text>"
pk_x, pk_y = pts[months.index("2025-10")]
trend_svg = (f"<svg viewBox='0 0 {W} {H}' style='width:100%;height:auto'>"
             f"<defs><linearGradient id='ag' x1='0' y1='0' x2='0' y2='1'>"
             f"<stop offset='0' stop-color='#f72585' stop-opacity='.35'/><stop offset='1' stop-color='#f72585' stop-opacity='0'/></linearGradient></defs>"
             f"{grid}<path d='{area_d}' fill='url(#ag)'/>"
             f"<path id='trend' d='{path_d}' fill='none' stroke='#f72585' stroke-width='2.5' pathLength='1' "
             f"style='stroke-dasharray:1;stroke-dashoffset:1;transition:stroke-dashoffset 2.2s ease'/>"
             f"{dots}{labs}"
             f"<text x='{pk_x:.1f}' y='{pk_y - 14:.1f}' fill='#ffd166' font-size='11' font-weight='700' text-anchor='middle'>DIWALI</text></svg>")

# ---- discount donut (customer mix)
tot_c = n_hunt + n_mixed + n_fan
segs = [("Discount hunters", n_hunt, "#f72585"), ("A bit of both", n_mixed, "#ffd166"), ("Full-price fans", n_fan, "#06d6a0")]
off, rings, dleg = 25.0, "", ""
for nm, v, col in segs:
    frac = v / tot_c * 100
    rings += (f"<circle r='15.9' cx='21' cy='21' fill='none' stroke='{col}' stroke-width='7' pathLength='100' "
              f"stroke-dasharray='{frac:.2f} {100 - frac:.2f}' stroke-dashoffset='{off:.2f}'/>")
    dleg += f"<div style='margin:7px 0;font-size:.88rem'><span style='display:inline-block;width:11px;height:11px;border-radius:3px;background:{col};margin-right:8px'></span>{nm}: <b>{v}</b> ({v / tot_c * 100:.0f}%)</div>"
    off -= frac
donut = (f"<div class='two'><div style='text-align:center'><svg viewBox='0 0 42 42' style='max-width:230px;width:100%'>{rings}"
         f"<text x='21' y='20' fill='#e9ecef' font-size='5.2' font-weight='700' text-anchor='middle'>{n_customers:,}</text>"
         f"<text x='21' y='26' fill='#8d99ae' font-size='3' text-anchor='middle'>customers</text></svg></div>"
         f"<div>{dleg}<div class='callout' style='margin-top:14px'>Hunters average a <b>{hunt_avg_disc:.0f}%</b> discount and put "
         f"<b>{hunt_fest_share:.0f}%</b> of their orders into the Diwali window - they shop the <i>sale</i>, not the store. "
         f"Full-price fans spend <b>{money(fan_aov)}</b> per order vs hunters' <b>{money(hunt_aov)}</b>.</div></div></div>")

# ---- category bars
max_cv = float(cat_rev.max())
cat_bars = ""
for c, v in cat_rev.items():
    cat_bars += (f"<div class='bar-row'><div class='nm'>{c}</div>"
                 f"<div class='bar-track'><div class='bar fill' data-w='{v / max_cv * 100:.1f}' style='background:linear-gradient(90deg,#4cc9f0,#4361ee)'></div></div>"
                 f"<div class='val mono'>{v / 1e5:.1f}L</div></div>")
champ_chips = "".join(f"<span class='chip' style='transition-delay:{i * 120}ms'>{c} - Rs {v / 1e5:.1f} lakh</span>"
                      for i, (c, v) in enumerate(champ_cat.head(3).items()))

html = f"""<!DOCTYPE html>
<html lang='en'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Dukaan24 - Customer Behaviour Report (fictional data)</title>
<style>{CSS}</style></head>
<body>
<div id='progress'></div>
<div class='blob' style='width:420px;height:420px;background:#f72585;top:-120px;left:-120px'></div>
<div class='blob' style='width:380px;height:380px;background:#4361ee;top:38%;right:-140px;animation-delay:-6s'></div>
<div class='blob' style='width:340px;height:340px;background:#06d6a0;bottom:-100px;left:22%;animation-delay:-12s'></div>
<div class='wrap'>
<div class='hero'>
<span class='badge'>FICTIONAL PRACTICE DATA</span>
<h1>Inside the Cart</h1>
<p class='sub'>What <b class='mono'>{n_orders:,}</b> orders and <b class='mono'>{n_customers:,}</b> customers taught
Dukaan24, a fictional Indian online store, over {date_min:%b %Y} - {date_max:%b %Y}.
A customer behaviour analysis with RFM segmentation.</p>
<div class='cue'>&#9660;</div>
</div>
<div class='kpis'>
<div class='kpi'><div class='num count mono' data-target='{n_customers}' data-final='{n_customers:,}'>0</div><div class='lbl'>customers</div></div>
<div class='kpi'><div class='num count mono' data-target='{n_orders}' data-final='{n_orders:,}'>0</div><div class='lbl'>orders placed</div></div>
<div class='kpi'><div class='num count mono' data-target='{cr_val:.2f}' data-dec='2' data-pre='&#8377;' data-suf=' Cr' data-final='&#8377;{cr_val:.2f} Cr'>0</div><div class='lbl'>total revenue</div></div>
<div class='kpi'><div class='num count mono' data-target='{rep_pct:.1f}' data-dec='1' data-suf='%' data-final='{rep_pct:.1f}%'>0</div><div class='lbl'>came back for more</div></div>
</div>

<section>
<h2>1. Not all customers are equal</h2>
<p class='lede'>We scored every customer on <b>Recency</b> (how lately they shopped), <b>Frequency</b> (how often)
and <b>Monetary</b> value (how much they spent) - the classic <b>RFM</b> method - and grouped them into segments.</p>
<div class='two'>
<div class='panel'><h3 style='font-size:.95rem;margin-bottom:12px;color:#ced4da'>How MANY customers</h3>{bars_c}</div>
<div class='panel'><h3 style='font-size:.95rem;margin-bottom:12px;color:#ced4da'>How much REVENUE they bring</h3>{bars_r}</div>
</div>
<div class='callout'>The <b style='color:#ffd166'>Champions</b> are just <b>{champ['cust_share']:.1f}%</b> of customers but bring
<b>{champ['rev_share']:.1f}%</b> of all revenue, ordering {champ['avg_orders']:.0f} times on average. Losing one Champion
hurts like losing dozens of one-time buyers.</div>
</section>

<section>
<h2>2. When India shops</h2>
<p class='lede'>Every order by day and hour. Brighter = busier. Hover any cell for the exact count.</p>
<div class='panel heat-scroll'>{heat_html}
<div class='legend'>quiet <span class='sw' style='background:rgba(255,159,28,.15)'></span><span class='sw' style='background:rgba(255,159,28,.45)'></span><span class='sw' style='background:rgba(255,159,28,.75)'></span><span class='sw' style='background:rgba(255,159,28,1)'></span> rush hour</div>
</div>
<div class='callout'><b>{WD[best_day_i]}</b> is the biggest day ({best_day_pct:.1f}% of orders) and the rush peaks at
<b>{hr_label}</b>. Weekends carry {weekend_share:.0f}% of all orders and 6 PM-midnight carries {evening_share:.0f}%.
That's exactly when push notifications and flash sales should fire.</div>
</section>

<section>
<h2>3. The Diwali wave</h2>
<p class='lede'>Monthly revenue over 18 months. One month is not like the others.</p>
<div class='panel'>{trend_svg}</div>
<div class='callout'>The 3 festive weeks (6-26 Oct 2025) alone brought <b>{fest_orders:,}</b> orders and
<b>{lakh(fest_rev)}</b> - <b>{fest_rev_share:.1f}%</b> of all revenue in 3 weeks, running <b>{fest_mult:.1f}x</b> a normal week.
Stock, servers and support all need to be Diwali-ready.</div>
</section>

<section>
<h2>4. Sale seekers vs full-price fans</h2>
<p class='lede'>Grouping customers by their average discount tells us <i>why</i> they buy.</p>
<div class='panel'>{donut}</div>
</section>

<section>
<h2>5. What's in the cart</h2>
<p class='lede'>Revenue by category overall - and what the Champions actually fill their carts with.</p>
<div class='panel'>{cat_bars}
<h3 style='font-size:.95rem;margin:18px 0 8px;color:#ced4da'>Champions' top categories</h3>{champ_chips}</div>
<div class='callout'><b>{top_cat}</b> leads overall, but Champions' baskets are anchored by
<b>{champ_cat.index[0]}</b> - the repeat-purchase engine. One-time buyers are {one_timers:,} people who bring only
{one_rev_share:.1f}% of revenue: converting even a slice of them is the cheapest growth there is.</div>
</section>

<section class='green'>
<h2>6. So what does Dukaan24 do now?</h2>
<p class='lede'>Analysis is only half the job. Here is the action list this data points to.</p>
<div class='cards'>
<div class='card' style='transition-delay:0ms'><h3>Guard the Champions</h3><div class='big' style='color:#ffd166'>{champ['customers']} people</div><p>Early access, loyalty perks, a human on support. At {champ['rev_share']:.0f}% of revenue, retention here is the whole game.</p></div>
<div class='card' style='transition-delay:120ms'><h3>Win back the At-Risk</h3><div class='big' style='color:#ff9e00'>{next((s['customers'] for s in seg_stats if s['name'] == 'At Risk'), 0)} people</div><p>They used to shop often and went quiet. A well-timed "we miss you" offer beats acquiring a stranger.</p></div>
<div class='card' style='transition-delay:240ms'><h3>Show up {WD[best_day_i]} evening</h3><div class='big' style='color:#4cc9f0'>{hr_label}</div><p>Run campaigns, pushes and flash sales in the {WD[best_day_i]}-evening rush, not on sleepy weekday mornings.</p></div>
<div class='card' style='transition-delay:360ms'><h3>Plan big for Diwali</h3><div class='big' style='color:#06d6a0'>{fest_mult:.1f}x volume</div><p>Inventory, deals and delivery slots locked in weeks ahead. Hunters will arrive for the sale - give them a reason to stay.</p></div>
</div>
</section>

<footer>Dukaan24 is a fictional store. All customers, orders and amounts are synthetic practice data
generated for a data-analyst portfolio project. Built with pandas - one self-contained HTML file, no internet needed.</footer>
</div>
<script>{JS}</script>
</body></html>"""

with open(OUT_HTML, "w", encoding="utf-8") as fh:
    fh.write(html)
print(f"HTML size: {len(html) / 1024:.0f} KB")
