#!/usr/bin/env python3
"""
Birth Seasonality Dashboard — Maricopa County (Phoenix) vs major US cities.

Data: CDC WONDER Natality 2016-2024 (county x month x year), and 1991-2020
NOAA climate normals (monthly mean temperature) via Open-Meteo.

Usage:
    python3 build_dashboard.py            # writes birth_dashboard.html
    python3 build_dashboard.py --serve    # also serves it on localhost:8090

Output: birth_dashboard.html — a fully self-contained interactive dashboard
(Plotly via CDN; no Python dependencies beyond the standard library).
"""
import argparse, calendar, csv, json, math, os, sys
from statistics import mean

HERE = os.path.dirname(os.path.abspath(__file__))
BIRTHS_CSV = os.path.join(HERE, "births_county_month_year.csv")
TEMPS_CSV = os.path.join(HERE, "temps_cities.csv")
OUT_HTML = os.path.join(HERE, "birth_dashboard.html")

CITY_COUNTY = {
    "Phoenix, AZ": "Maricopa County, AZ",
    "Los Angeles, CA": "Los Angeles County, CA",
    "Chicago, IL": "Cook County, IL",
    "Houston, TX": "Harris County, TX",
    "Seattle, WA": "King County, WA",
    "Miami, FL": "Miami-Dade County, FL",
    "Atlanta, GA": "Fulton County, GA",
    "Denver, CO": "Denver County, CO",
    "Minneapolis, MN": "Hennepin County, MN",
    "Boston, MA": "Suffolk County, MA",
    "New York City, NY": "New York County, NY",
    "Dallas, TX": "Dallas County, TX",
    "Philadelphia, PA": "Philadelphia County, PA",
}
MONTH_NAMES = ["January","February","March","April","May","June",
               "July","August","September","October","November","December"]
MONTH_DAYS = {m: calendar.monthrange(2020, m)[1] for m in range(1, 13)}

# Federal holidays count per calendar month (typical US federal holidays)
FED_HOLIDAYS = {1: 2, 2: 1, 3: 0, 4: 0, 5: 1, 6: 0, 7: 1, 8: 0, 9: 1, 10: 1, 11: 1, 12: 1}
# Major "family/holiday" season anchors for annotations
HOLIDAY_ANCHORS = [("New Year's", 1), ("Valentine's", 2), ("Memorial Day", 5),
                   ("July 4th", 7), ("Labor Day", 9), ("Halloween", 10),
                   ("Thanksgiving", 11), ("Christmas", 12)]


def load_births():
    rows = []
    with open(BIRTHS_CSV, newline="") as f:
        for r in csv.DictReader(f):
            rows.append({"county": r["county"], "month": int(r["month_code"]),
                         "year": int(r["year"]), "births": int(r["births"])})
    return rows


def load_temps():
    temps = {}
    with open(TEMPS_CSV, newline="") as f:
        for r in csv.DictReader(f):
            temps[r["city"]] = [float(r[f"M{m}"]) for m in range(1, 13)]
    return temps


def pearson(x, y):
    mx, my = mean(x), mean(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den = math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))
    return num / den if den else 0.0


def county_series(births, county):
    """Return {year: {month: births}} and monthly aggregates."""
    yearly_month = {}
    monthly_total = {m: 0 for m in range(1, 13)}
    yearly_total = {}
    for b in births:
        if b["county"] != county:
            continue
        yearly_month.setdefault(b["year"], {})[b["month"]] = b["births"]
        monthly_total[b["month"]] += b["births"]
        yearly_total[b["year"]] = yearly_total.get(b["year"], 0) + b["births"]
    return yearly_month, monthly_total, yearly_total


def compute_city(births, temps, city, county):
    _, monthly, yearly_total = county_series(births, county)
    # day-length adjusted monthly share (% of annual)
    adj = {m: monthly[m] / MONTH_DAYS[m] for m in monthly}
    tot = sum(adj.values())
    share = {m: round(adj[m] / tot * 100, 2) for m in range(1, 13)}
    peak = max(range(1, 13), key=lambda m: share[m])
    trough = min(range(1, 13), key=lambda m: share[m])
    t = temps[city]
    shares = [share[m] for m in range(1, 13)]
    same_t = [t[m - 1] for m in range(1, 13)]

    def conc_month(m):  # conception month = 9 months before birth month
        return (m - 10) % 12 + 1

    conc_t = [t[conc_month(m) - 1] for m in range(1, 13)]
    conc_h = [FED_HOLIDAYS[conc_month(m)] for m in range(1, 13)]
    return {
        "city": city, "county": county,
        "total_births": sum(monthly.values()),
        "years": sorted(yearly_total.keys()),
        "yearly": yearly_total,
        "monthly_raw": monthly,
        "share": share,
        "peak_month": peak, "trough_month": trough,
        "temps": t,
        "r_same_temp": round(pearson(shares, same_t), 3),
        "r_conception_temp": round(pearson(shares, conc_t), 3),
        "r_conception_holidays": round(pearson(shares, conc_h), 3),
    }


def js(obj):
    return json.dumps(obj)


def build_html(cities, phx):
    months = MONTH_NAMES
    # ---- Maricopa detail plots data ----
    phx_share = [phx["share"][m] for m in range(1, 13)]
    phx_temps = phx["temps"]
    phx_years = phx["years"]
    phx_yearly = [phx["yearly"][y] for y in phx_years]
    # scatter for conception-temp correlation (all cities)
    scatter = [{"x": c["r_conception_temp"] and None, "y": None} for c in cities]
    sc = []
    for c in cities:
        for m in range(1, 13):
            sc.append({"city": c["city"], "month": m,
                       "share": c["share"][m],
                       "conctemp": c["conc_temps"][str(m)]})
    # comparison table rows
    table = []
    for c in cities:
        table.append({
            "city": c["city"], "county": c["county"],
            "total": c["total_births"],
            "peak": months[c["peak_month"] - 1],
            "trough": months[c["trough_month"] - 1],
            "peak_share": c["share"][c["peak_month"]],
            "trough_share": c["share"][c["trough_month"]],
            "r_conc_temp": c["r_conception_temp"],
            "r_conc_hol": c["r_conception_holidays"],
            "r_same_temp": c["r_same_temp"],
        })
    # multi-city normalized monthly curve
    norm_lines = []
    scatter_pts = []
    for c in cities:
        norm_lines.append({
            "name": c["city"],
            "share": [c["share"][m] for m in range(1, 13)],
            "peak": c["peak_month"] - 1,
        })
        for m in range(1, 13):
            scatter_pts.append({
                "city": c["city"], "month": m,
                "share": c["share"][m],
                "conctemp": c["conc_temps"][str(m)],
            })
    payload = {
        "months": months,
        "phx": {
            "city": phx["city"], "county": phx["county"],
            "total": phx["total_births"],
            "share": phx_share, "temps": phx_temps,
            "years": phx_years, "yearly": phx_yearly,
            "peak": months[phx["peak_month"] - 1],
            "trough": months[phx["trough_month"] - 1],
            "peak_share": phx["share"][phx["peak_month"]],
            "trough_share": phx["share"][phx["trough_month"]],
            "r_same_temp": phx["r_same_temp"],
            "r_conception_temp": phx["r_conception_temp"],
            "r_conception_holidays": phx["r_conception_holidays"],
        },
        "holiday_anchors": HOLIDAY_ANCHORS,
        "comparison": table,
        "norm_lines": norm_lines,
        "scatter_pts": scatter_pts,
    }

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Birth Seasonality Dashboard — Phoenix &amp; Major US Cities</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
<style>
  :root { --ink:#1f2430; --mut:#6b7280; --line:#e5e7eb; --bg:#f7f8fa; --card:#fff;
          --phx:#c2410c; --accent:#2563eb; }
  * { box-sizing:border-box; }
  body { margin:0; font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
         background:var(--bg); color:var(--ink); }
  header { background:linear-gradient(135deg,#7c2d12,#c2410c); color:#fff; padding:28px 24px 22px; }
  header h1 { margin:0 0 6px; font-size:26px; }
  header p { margin:0; opacity:.92; max-width:900px; line-height:1.5; }
  main { max-width:1180px; margin:0 auto; padding:20px 16px 60px; }
  .cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:12px; margin:18px 0; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:14px 16px; }
  .card .k { font-size:12px; text-transform:uppercase; letter-spacing:.04em; color:var(--mut); }
  .card .v { font-size:22px; font-weight:700; margin-top:4px; }
  .card .s { font-size:12px; color:var(--mut); margin-top:2px; }
  .panel { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px; margin:18px 0; }
  .panel h2 { margin:0 0 4px; font-size:18px; }
  .panel .sub { color:var(--mut); font-size:13px; margin-bottom:10px; }
  .plot { width:100%; height:430px; }
  table { border-collapse:collapse; width:100%; font-size:13px; }
  th,td { text-align:right; padding:7px 8px; border-bottom:1px solid var(--line); }
  th:first-child,td:first-child,th:nth-child(2),td:nth-child(2) { text-align:left; }
  th { color:var(--mut); font-weight:600; background:#fafafa; }
  tbody tr:hover { background:#f5f6f8; }
  .pill { display:inline-block; padding:2px 8px; border-radius:999px; font-size:11px; font-weight:600; }
  .pill.pk { background:#dcfce7; color:#166534; }
  .pill.tr { background:#fee2e2; color:#991b1b; }
  footer { text-align:center; color:var(--mut); font-size:12px; padding:20px; }
  @media (max-width:700px){ .plot{height:340px} }
</style>
</head>
<body>
<header>
  <h1>👶 Birth Seasonality — Phoenix / Maricopa County vs Major US Cities</h1>
  <p>Monthly birth counts from <b>CDC WONDER Natality 2016–2024</b> (county of residence × month × year),
     correlated against 1991–2020 monthly mean temperatures and the federal-holiday calendar.
     A birth in month <i>M</i> implies conception ~9 months earlier (<i>M−9</i>), so both same-month and
     conception-lagged temperature correlations are shown.</p>
</header>
<main>
  <div class="cards" id="kpi"></div>
  <div class="panel">
    <h2>Monthly births vs temperature — Maricopa County, AZ (Phoenix)</h2>
    <div class="sub">Bar: births per day (day-length adjusted) · Line: mean monthly temperature. Births peak ~Sept (conception ~Dec, holiday season).</div>
    <div id="plot-phx" class="plot"></div>
  </div>
  <div class="panel">
    <h2>Births by year — Maricopa County</h2>
    <div class="sub">Total live births per calendar year, 2016–2024.</div>
    <div id="plot-yearly" class="plot"></div>
  </div>
  <div class="panel">
    <h2>Conception-month temperature vs birth share (all 13 cities)</h2>
    <div class="sub">Each dot = one city-month. X = mean temp of the conception month (9 months prior); Y = that birth month's share of annual births. Cold conception months (fall/winter holidays) → higher share ~9 months later.</div>
    <div id="plot-scatter" class="plot"></div>
  </div>
  <div class="panel">
    <h2>Normalized seasonal curve — all cities</h2>
    <div class="sub">Monthly share of annual births (day-length adjusted), each city as its own line.</div>
    <div id="plot-norm" class="plot"></div>
  </div>
  <div class="panel">
    <h2>Comparison table</h2>
    <div class="sub">Peak/trough birth months, and Pearson r between monthly birth share and (a) same-month temp, (b) conception-month temp, (c) # federal holidays in conception month.</div>
    <div style="overflow-x:auto"><table id="cmp-table"></table></div>
  </div>
  <footer>Source: CDC WONDER Natality 2016–2024 (births by mother's county of residence) · NOAA 1991–2020 climate normals via Open-Meteo · Dashboard generated by build_dashboard.py</footer>
</main>
<script>
const DATA = __PAYLOAD__;
const M = DATA.months;
const PHX = DATA.phx;

// ---- KPI cards ----
const kpi = [
  {k:'Total births 2016–24', v:PHX.total.toLocaleString(), s:PHX.county},
  {k:'Peak birth month', v:PHX.peak, s:PHX.peak_share+'% of annual births'},
  {k:'Trough birth month', v:PHX.trough, s:PHX.trough_share+'% of annual births'},
  {k:'r with conception-month temp', v:PHX.r_conception_temp, s:'strong negative = cool fall/winter → more births'},
  {k:'r with conception-month holidays', v:PHX.r_conception_holidays, s:'positive = holidays line up with peak'},
];
document.getElementById('kpi').innerHTML = kpi.map(c=>
  `<div class="card"><div class="k">${c.k}</div><div class="v">${c.v}</div><div class="s">${c.s}</div></div>`).join('');

// ---- Phoenix: births vs temp ----
Plotly.newPlot('plot-phx', [
  {type:'bar', x:M, y:PHX.share, name:'Births (% of annual)', marker:{color:'#c2410c'}, yaxis:'y'},
  {type:'scatter', mode:'lines+markers', x:M, y:PHX.temps, name:'Mean temp (°C)',
   line:{color:'#2563eb', width:3}, yaxis:'y2'},
], {
  margin:{t:30,b:40,l:50,r:50},
  xaxis:{title:'Month'},
  yaxis:{title:'% of annual births', ticksuffix:'%'},
  yaxis2:{title:'°C', overlaying:'y', side:'right'},
  legend:{orientation:'h', y:1.12},
  hovermode:'x unified',
}, {responsive:true, displaylogo:false});

// ---- Phoenix: yearly ----
Plotly.newPlot('plot-yearly', [
  {type:'bar', x:PHX.years, y:PHX.yearly, name:'Births', marker:{color:'#9a3412'},
   text:PHX.yearly.map(String), textposition:'outside', cliponaxis:false},
], {
  margin:{t:30,b:40,l:60,r:20},
  xaxis:{title:'Year', dtick:1},
  yaxis:{title:'Live births'},
  hovermode:'x unified',
}, {responsive:true, displaylogo:false});

// ---- Scatter: conception temp vs share ----
const sp = DATA.scatter_pts;
const spCities = [...new Set(sp.map(d=>d.city))];
// color per city
const palette = ['#7c3aed','#2563eb','#0d9488','#ca8a04','#dc2626','#9333ea','#059669','#ea580c','#0284c7','#be123c','#4d7c0f','#7e22ce','#0891b2'];
const cityColor = {}; spCities.forEach((c,i)=>cityColor[c]=palette[i%palette.length]);
const scTrace = {
  type:'scatter', mode:'markers',
  x: sp.map(d=>d.conctemp), y: sp.map(d=>d.share),
  text: sp.map(d=>`${d.city} — ${M[d.month-1]}`),
  marker:{size:7, color: sp.map(d=>cityColor[d.city]), opacity:.6},
  hovertemplate:'%{text}<br>conception temp %{x}°C<br>birth share %{y}%<extra></extra>',
};
// add annotation for Phoenix
Plotly.newPlot('plot-scatter', [scTrace], {
  margin:{t:30,b:40,l:50,r:20},
  xaxis:{title:'Mean temp of conception month (M-9), °C'},
  yaxis:{title:'Share of annual births (%)', ticksuffix:'%'},
  hovermode:'closest',
}, {responsive:true, displaylogo:false});

// ---- Normalized curves ----
const traces = DATA.norm_lines.map(nl=>({
  type:'scatter', mode:'lines+markers', name:nl.name,
  x:M, y:nl.share, line:{width: nl.name==='Phoenix, AZ'?4:1.5,
    color: nl.name==='Phoenix, AZ' ? '#c2410c' : undefined,
    dash: nl.name==='Phoenix, AZ' ? undefined : 'dot'},
  marker:{size: nl.name==='Phoenix, AZ'?7:3},
}));
Plotly.newPlot('plot-norm', traces, {
  margin:{t:30,b:40,l:50,r:20},
  xaxis:{title:'Month'},
  yaxis:{title:'% of annual births', ticksuffix:'%'},
  hovermode:'x unified',
}, {responsive:true, displaylogo:false});

// ---- Comparison table ----
const tbody = DATA.comparison.map(c=>`
  <tr>
    <td><b>${c.city}</b></td>
    <td>${c.county}</td>
    <td>${c.total.toLocaleString()}</td>
    <td><span class="pill pk">${c.peak}</span></td>
    <td><span class="pill tr">${c.trough}</span></td>
    <td>${c.r_conc_temp}</td>
    <td>${c.r_conc_hol}</td>
    <td>${c.r_same_temp}</td>
  </tr>`).join('');
document.getElementById('cmp-table').innerHTML =
  `<thead><tr><th>City</th><th>County</th><th>Total births</th><th>Peak</th><th>Trough</th>
   <th>r conception temp</th><th>r conception holidays</th><th>r same-month temp</th></tr></thead><tbody>${tbody}</tbody>`;
</script>
</body>
</html>"""

    html = html.replace("__PAYLOAD__", js(payload))
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {OUT_HTML} ({os.path.getsize(OUT_HTML):,} bytes)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true", help="serve on localhost:8090 after building")
    args = ap.parse_args()

    births = load_births()
    temps = load_temps()
    cities = []
    for city, county in CITY_COUNTY.items():
        cities.append(compute_city(births, temps, city, county))
    phx = next(c for c in cities if c["city"] == "Phoenix, AZ")
    # attach conception temps per city for the scatter
    for c in cities:
        t = c["temps"]
        c["conc_temps"] = {str(m): round(t[(m - 10) % 12], 1) for m in range(1, 13)}
    build_html(cities, phx)

    if args.serve:
        import http.server, socketserver
        os.chdir(HERE)
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", 8090), handler) as httpd:
            print("Serving at http://localhost:8090/birth_dashboard.html  (Ctrl+C to stop)")
            httpd.serve_forever()


if __name__ == "__main__":
    main()
