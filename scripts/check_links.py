"""Fail if a relative Markdown link points to a file that does not exist (offline)."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".venv", ".venv-gpu", ".git", "release_bundle", "runs", "data", "node_modules"}
LINK = re.compile(r"\]\(([^)\s]+)\)")

bad = []
for md in ROOT.rglob("*.md"):
    if SKIP & set(md.relative_to(ROOT).parts):
        continue
    for target in LINK.findall(md.read_text(encoding="utf-8")):
        if re.match(r"[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
            continue  # external URL, mailto or in-page anchor
        if not (md.parent / target.split("#")[0]).exists():
            bad.append(f"{md.relative_to(ROOT)}: {target}")
print("\n".join(bad) or "internal links ok")
sys.exit(1 if bad else 0)
