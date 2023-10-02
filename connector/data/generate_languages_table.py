#!/usr/bin/python3


import sys
from csv import DictWriter


writer = DictWriter(sys.stdout, fieldnames=["name", "type"])
writer.writeheader()
for line in sys.stdin:
    if '(' not in line:
        continue
    writer.writerow({
        "name": line.split('(')[0].strip(),
        "type": "GPL"})
