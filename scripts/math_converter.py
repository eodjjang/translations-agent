"""
유니코드 수학 문자 → Typst 인라인 수식 조각으로의 기본 매핑.
복잡한 식은 에이전트가 문맥으로 교정한다.
"""

from __future__ import annotations

import re
import unicodedata

# 자주 쓰이는 단일 문자 매핑 (확장 가능)
UNICODE_TO_TYPST: dict[str, str] = {
    "α": "alpha",
    "β": "beta",
    "γ": "gamma",
    "δ": "delta",
    "ε": "epsilon",
    "θ": "theta",
    "λ": "lambda",
    "μ": "mu",
    "π": "pi",
    "σ": "sigma",
    "φ": "phi",
    "ω": "omega",
    "Σ": "Sigma",
    "Π": "Pi",
    "∞": "infinity",
    "∑": "sum",
    "∫": "integral",
    "∂": "partial",
    "√": "sqrt",
    "×": "times",
    "±": "plus.minus",
    "≤": "lt.eq",
    "≥": "gt.eq",
    "≠": "eq.not",
    "→": "arrow.r",
    "←": "arrow.l",
    "⇒": "arrow.r.double",
}


def unicode_to_typst_fragment(ch: str) -> str | None:
    """단일 문자를 Typst 식별자 또는 짧은 표현으로 변환. 매핑 없으면 None."""
    if ch in UNICODE_TO_TYPST:
        return UNICODE_TO_TYPST[ch]
    cat = unicodedata.category(ch)
    if cat.startswith("L") or cat == "Nd":
        return None
    return None


def wrap_inline_typst(body: str) -> str:
    """Typst 인라인 수식으로 감싼다."""
    body = body.strip()
    if not body:
        return ""
    return f"$ {body} $" if not body.startswith("$") else body


def convert_line(line: str, aggressive: bool = False) -> str:
    """
    매핑 테이블에 있는 유니코드 수학 문자만 Typst 인라인 조각으로 치환.
    이미 존재하는 $...$ 구간은 aggressive=True일 때만 재처리한다.
    """
    if not aggressive and "$" in line:
        return line

    out: list[str] = []
    for ch in line:
        frag = unicode_to_typst_fragment(ch)
        if frag is not None:
            out.append(f"${frag}$")
        else:
            out.append(ch)
    return "".join(out)


def extract_inline_math_segments(text: str) -> list[tuple[int, int, str]]:
    """$ 로 구분된 인라인 수식 구간 (시작, 끝, 내용) 목록."""
    parts: list[tuple[int, int, str]] = []
    for m in re.finditer(r"\$([^$]+)\$", text):
        parts.append((m.start(), m.end(), m.group(1)))
    return parts


if __name__ == "__main__":
    sample = "Energy $E=mc^2$ and α particle."
    print(convert_line(sample, aggressive=False))
