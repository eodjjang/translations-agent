"""
Hook 라우터: postToolUse(Write) 이벤트를 받아 파일 경로 패턴에 따라
적절한 검증기를 호출하고, 결과를 additional_context로 반환한다.

관련 없는 파일이면 빈 JSON을 반환하여 오버헤드를 최소화한다.
"""

from __future__ import annotations

import importlib.util
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

HOOK_DIR = Path(__file__).resolve().parent


def _load_validator(name: str):
    spec = importlib.util.spec_from_file_location(name, HOOK_DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _find_file_path(hook_input: dict) -> str | None:
    """postToolUse stdin JSON에서 기록된 파일 경로를 추출한다."""
    tool_input = hook_input.get("input", {})
    return tool_input.get("path") or tool_input.get("filePath")


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        print("{}")
        return

    try:
        hook_input = json.loads(raw)
    except json.JSONDecodeError:
        print("{}")
        return

    file_path = _find_file_path(hook_input)
    if not file_path:
        print("{}")
        return

    fp = file_path.replace("\\", "/")

    errors: list[str] = []

    # output/*/src/*.typ  ->  translation_validator + typst_validator
    if re.search(r"output/[^/]+/src/.*\.typ$", fp):
        try:
            tv = _load_validator("translation_validator")
            result = tv.validate(file_path, hook_input)
            if result:
                errors.extend(result)
        except Exception as e:
            errors.append(f"[translation_validator 오류] {e}")

        try:
            tyv = _load_validator("typst_validator")
            result = tyv.validate(file_path, hook_input)
            if result:
                errors.extend(result)
        except Exception as e:
            errors.append(f"[typst_validator 오류] {e}")

    # output/*/final_translated.pptx  ->  pptx_validator
    elif re.search(r"output/[^/]+/final_translated\.pptx$", fp):
        try:
            pv = _load_validator("pptx_validator")
            result = pv.validate(file_path, hook_input)
            if result:
                errors.extend(result)
        except Exception as e:
            errors.append(f"[pptx_validator 오류] {e}")

    else:
        print("{}")
        return

    if errors:
        msg = "[자동 검증 실패]\n" + "\n".join(f"- {e}" for e in errors)
        msg += "\n→ 위 항목을 수정한 후 파일을 다시 저장하세요."
        print(json.dumps({"additional_context": msg}, ensure_ascii=False))
    else:
        print("{}")


if __name__ == "__main__":
    main()
