"""Quick sanity check that the exported HTML matches the current deck."""
import io
from pathlib import Path

HTML = Path(__file__).resolve().parents[1] / "CA6002_Group30_Final_Presentation.html"
h = io.open(HTML, encoding="utf-8").read()

print("slides:", h.count('class="slide"'))
print("puff divs:", h.count("obj shape puff"))
print("smoke keyframes:", "keyframes rise" in h)
print("arrow-key capture fix:", "}, true);" in h)
print("tables:", h.count('<table class="tbl"'))
print("credit lines:", h.count("Responsible:"))
print("mixed-case credit leak:", "Responsible: Shen Ruiting" in h)
for kw in ("required by the brief", "assignment template", "20 body slides", "20-slide"):
    print(f"meta text {kw!r}:", kw in h)
