# -*- coding: utf-8 -*-
"""Locate the XML elements that still carry a non-Times font."""
import re
import zipfile
from pathlib import Path

DECK = Path(r"C:\Users\user\Desktop\Overall_Data Visual Assignment"
            r"\4_Final_whole_result\CA6002_Group30_Final_Presentation.pptx")
z = zipfile.ZipFile(DECK)
for x in sorted(y for y in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", y)):
    s = z.read(x).decode("utf8")
    hits = {}
    for m in re.finditer(r'<a:(\w+)[^>]*typeface="([^"]+)"', s):
        if m.group(2) != "Times New Roman":
            hits[(m.group(1), m.group(2))] = hits.get((m.group(1), m.group(2)), 0) + 1
    if hits:
        print(x, hits)
