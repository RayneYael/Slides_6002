# -*- coding: utf-8 -*-
"""Compare the WPS storyline docx with its markdown conversions."""
import re
import zipfile
from pathlib import Path

ROOT = Path(r"C:\Users\user\Desktop\Overall_Data Visual Assignment")
DOCS = ROOT / "0_docs_必看"
DOCX = DOCS / "Storytelling草稿.docx"
ORIGIN = DOCS / "Storytelling草稿MD格式" / "a363d6f3-07cf-4e67-a13c-468818b87ee0_origin.docx"
FULL = DOCS / "Storytelling草稿MD格式" / "full.md"
CHAIN = DOCS / "完整故事链_最新版.md"


def docx_text(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf8")
    xml = re.sub(r"</w:p>", "\n", xml)
    return re.sub(r"<[^>]+>", "", xml)


def norm(t):
    return re.sub(r"\s+", "", t)


a, b = docx_text(DOCX), docx_text(ORIGIN)
md = FULL.read_text(encoding="utf8")
chain = CHAIN.read_text(encoding="utf8")
print("docx == origin.docx:", norm(a) == norm(b), len(norm(a)), len(norm(b)))

md_plain = re.sub(r"<[^>]+>", "", md)
md_plain = re.sub(r"[#*`>|\-]", "", md_plain)
sent = [s for s in re.split(r"[。\n]", re.sub(r"[#*`>|]", "", a)) if len(s.strip()) > 12]
missing = [s.strip() for s in sent if norm(s) not in norm(md_plain)]
print(f"docx sentences not found in full.md: {len(missing)} of {len(sent)}")
for s in missing[:12]:
    print("   -", s[:90])

for key in ["92.2", "193", "24", "169", "K=2", "边界国家", "monitoring"]:
    print(f"  '{key}': docx={a.count(key)}  full.md={md.count(key)}  chain={chain.count(key)}")
