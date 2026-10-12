#!/usr/bin/env python3
"""Emit year_over_year.html from already-computed data files."""
import csv
import json

HERE = "/home/chandra/birth-dashboard"

# national births + crude rate (from native WONDER + FRED populations, computed+verified earlier
NAS = [
    [2007, 4316233, 14.29], [2008, 4247694, 13.94],
    [2009, 4130665,  #####13.44], [2010,  #####, ], ,
].  # placeholder replaced below

NAS = [
    [2007, 4316233,  #####14.29], [2008,  #####, ], ,
    [2009,  #####, ], ,
].  # placeholder replaced below