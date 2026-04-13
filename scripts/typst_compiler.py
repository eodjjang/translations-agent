"""
Typst CLI 실행 및 stderr/exit code 반환. 설계서 Step 5 스크립트 담당.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def find_typst() -> str | None:
    return shutil.which("typst")


def compile_typst(
    src: Path,
    out_pdf: Path,
    *,
    root: Path | None = None,
) -> tuple[int, str, str]:
    """
    typst compile [root] src out
    root가 있으면 프로젝트 루트로 작업 디렉터리를 둔다 (에셋·폰트 상대 경로용).
    반환: (exit_code, stdout, stderr)
    """
    exe = find_typst()
    if not exe:
        return (127, "", "typst CLI not found. Install: winget install typst (Windows)")

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    cmd = [exe, "compile"]
    if root:
        cmd.extend(["--root", str(root.resolve())])
    cmd.extend([str(src.resolve()), str(out_pdf.resolve())])
    cwd = str(root) if root else None
    r = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return (r.returncode, r.stdout or "", r.stderr or "")


def main() -> int:
    p = argparse.ArgumentParser(description="Compile Typst source to PDF.")
    p.add_argument("src", type=Path, help="Path to .typ file (e.g. output/src/main.typ)")
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output PDF path",
    )
    p.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Working directory for typst (for relative includes/assets)",
    )
    args = p.parse_args()

    output_path = args.output or args.src.parent.parent / "final_translated.pdf"
    code, out, err = compile_typst(args.src, output_path, root=args.root)
    if out:
        print(out, file=sys.stdout)
    if err:
        print(err, file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
