"""translate_priority/ko_pXX.txt → src/pages/pXX.txt (Typst 이스케이프)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "entropy_typst_build", root / "scripts" / "entropy_typst_build.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

tp = root / "output" / "entropy" / "translate_priority"
dst = root / "output" / "entropy" / "src" / "pages"
lo, hi = 1, 18
if len(sys.argv) >= 3:
    lo, hi = int(sys.argv[1]), int(sys.argv[2])

for pg in range(lo, hi + 1):
    src = tp / f"ko_p{pg:02d}.txt"
    if not src.is_file():
        print("skip missing", src)
        continue
    raw = src.read_text(encoding="utf-8")
    (dst / f"p{pg:02d}.txt").write_text(mod.escape_typst_text(raw), encoding="utf-8")
    print("ok", pg)
