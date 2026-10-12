#!/usr/bin/env python3
import csv
import json

HERE = "/home/chandra/birth-dashboard"

rows = []
with open(HERE + "/state_birth_rate_econ.csv", newline="") as f:
    for r in csv.DictReader(f):
        rows.append(r)


nas = []
with open(HERE + "/nat_trend.csv", newline="") as f:
    for r in csv.DictReader(f):
        nas.append(r)


corr = {}
with open(HERE + "/corr.json") as f:
    corr = json.load(f)


table_tr = ""
for r in rows:
    name = r["state"]
    rate = r["rate_2024"]
    colv = r["col_index"]
    incv = r["median_income"]
    table_tr = table_tr + "<tr>"
    table_tr = table_tr + "<td>" + name + "</td>"
    table_tr = table_tr + "<td>" + rate + "</td>"
    table_tr = table_tr + "<td>" + colv + "</td>"
    table_tr = table_tr + "<td>" + incv + "</td>"
    table_tr = table_tr + "</tr>"


label_yr = ""
drate_yr = ""
for r in nas:
    label_yr = label_yr + "'" + r["year"] + "',"
    drate_yr = drate_yr + r["rate"] + ","


html = open(HERE + "/yoy_template.html").read()
html = html.replace("__TABLE__", table_tr)
html = html.replace("__YEARS__", label_yr)
html = html.replace("__RATES__", drate_yr)
html = html.replace("__COLK__", str(corr["r_col_all"]))
html = html.replace("__COLK2__", str(corr["r_col_noDC"]))
html = html.replace("__INCK__", str(corr["r_inc_all"]))
html = html.replace("__INCK2__", str(corr["r_inc_noDC"]))

with open(HERE + "/year_over_year.html", "w")as f:
    f.write(html)

print("wrote year_over_year.html")