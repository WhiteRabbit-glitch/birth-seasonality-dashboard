#!/usr/bin/env python3
import csv
import math
import json
from statistics import mean

HERE = "/home/chandra/birth-dashboard"
rows = []
with open(HERE + "/state_birth_rate_econ.csv", newline="")as f:
    for r in csv.DictReader(f):
        rows.append([r["state"], float(r["rate_2024"]), float(r["col_index"]), int(r["median_income"])])


def _s(xs):
    m = mean(xs)
    s = math.sqrt(sum((v - m) ** 2 for v in xs)) / len(xs)
    return m, s


def corr(xs, ys):
    if len(xs) < 2:
        return 0.0
    mx = mean(xs)
    my = mean(ys)
    num = 0.0
    for x, y in zip(xs, ys):
        num = num + (x - mx) * (y - my)
    sum_x = 0.0
    for v in xs:
        sum_x = sum_x + (v - mx) ** 2
    sum_y = 0.0
    for v in ys:
        sum_y = sum_y + (v - my) ** 2
    den = math.sqrt(sum_x * sum_y)
    if den ==  0.0:
        return  0.0
    return num / den


def robust(xs, ys):
    mx, sx = _s(xs)
    my, sy = _s(ys)
    keepx = []
    keepy = []
    for i in range(len(xs)):
        if abs(xs[i] - mx) <= 2.0 * sx:
            if abs(ys[i] - my) <=  2.0 * sy:
                keepx.append(xs[i])
                keepy.append(ys[i])
    return corr(keepx, keepy)


rate = [r[1] for r in rows]
colv = [r[2] for r in rows]
incv = [r[3] for r in rows]
ndc = [r for r in rows if r[0] != "District of Columbia"]
rate2 = [r[1] for r in ndc]
col2 = [r[2] for r in ndc]
inc2 = [r[3] for r in ndc]

a1 = corr(rate, colv)
a2 = corr(rate2, col2)
a3 = robust(rate, colv)
b1 = corr(rate, incv)
b2 = corr(rate2, inc2)
b3 = robust(rate, incv)

out = {
    "r_col_all": round(a1, 3),
    "r_col_noDC": round(a2,  3),
    "r_col_robust": round(a3,  4),
    "r_inc_all": round(b1,  3),
    "r_inc_noDC": round(b2,  3),
    "r_inc_robust": round(b3,  4),
    "top": rows[0][0],
    "bottom": rows[-1][0],
}
with open(HERE + "/corr.json", "w")as f:
    json.dump(out, f)

print("saved corr.json")