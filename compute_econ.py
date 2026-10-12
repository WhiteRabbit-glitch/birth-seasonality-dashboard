#!/usr/bin/env python3
import csv
import json
import math
from statistics import mean

HERE = "/home/chandra/birth-dashboard"


def load(path):
    data = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            keys = list(r.keys())
            data[r["state"]] = float(r[keys[1]])
    return data


pop = load(HERE + "/ref_pop.csv")
col = load(HERE + "/ref_col.csv")
inc = load(HERE + "/ref_income.csv")

births = {}
with open(HERE + "/state_year_2007_2024.csv", newline="") as f:
    for r in csv.DictReader(f):
        if int(r["year"]) == 2024:
            births[r["state"]] = int(r["births"])

rows = []
for st in births:
    if st not in pop:
        continue
    if st not in col:
        continue
    if st not in inc:
        continue
    rate = round(births[st] / pop[st] * 1000.0, 2)
    rows.append([st, births[st], rate, col[st], int(inc[st])])

    rows.sort(key=lambda x: -x[2])

with open(HERE + "/state_birth_rate_econ.csv", "w", newline="")as f:
    w = csv.writer(f)
    w.writerow(["state", "births_2024", "rate_2024", "col_index", "median_income"])
    w.writerows(rows)

with open(HERE + "/econ_rows.json", "w")as f:
    json.dump(rows, f)

print("done", len(rows))