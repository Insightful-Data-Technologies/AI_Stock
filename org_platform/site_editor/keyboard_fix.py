"""Hebrew ↔ English keyboard layout fix (migrated from legacy Streamlit tool)."""
from __future__ import annotations

import re
from typing import Dict, Tuple

HE_TO_EN: Dict[str, str] = {
    "׳": "'",
    "״": '"',
    "־": "-",
    " ": " ",
    "ק": "q",
    "ר": "w",
    "א": "e",
    "ט": "r",
    "ו": "t",
    "ן": "y",
    "ם": "u",
    "פ": "i",
    "ש": "a",
    "ד": "s",
    "ג": "d",
    "כ": "f",
    "ע": "g",
    "י": "h",
    "ח": "j",
    "ל": "k",
    "ך": "l",
    "ף": ";",
    "ז": "z",
    "ס": "x",
    "ב": "c",
    "ה": "v",
    "נ": "b",
    "מ": "n",
    "צ": "m",
    "ת": ",",
    "0": "0",
    "1": "1",
    "2": "2",
    "3": "3",
    "4": "4",
    "5": "5",
    "6": "6",
    "7": "7",
    "8": "8",
    "9": "9",
    ".": ".",
    ",": ",",
    "/": ".",
    ";": "p",
    "'": "[",
    "[": "]",
    "]": "\\",
    "-": "-",
    "=": "=",
}

EN_TO_HE: Dict[str, str] = {v: k for k, v in HE_TO_EN.items()}
for en_char, he_char in list(EN_TO_HE.items()):
    if en_char.isalpha():
        EN_TO_HE[en_char.upper()] = he_char

for k, v in {
    " ": " ",
    "־": "-",
    "–": "-",
    "—": "-",
    "“": '"',
    "”": '"',
    "‘": "'",
    "’": "'",
    "…": "...",
}.items():
    HE_TO_EN.setdefault(k, v)

for k, v in {
    " ": " ",
    "-": "־",
    '"': "״",
    "'": "׳",
    ".": ".",
    ",": ",",
    "?": "/",
    ";": "ף",
    ":": ".",
    "[": "'",
    "]": "]",
    "\\": "\\",
    "/": ".",
    "<": ",",
    ">": ".",
}.items():
    EN_TO_HE.setdefault(k, v)

HEBREW_LETTERS_RE = re.compile(r"[\u0590-\u05FF]")
ENGLISH_LETTERS_RE = re.compile(r"[A-Za-z]")


def detect_layout(text: str) -> Tuple[str, float, float]:
    if not text:
        return ("unknown", 0.0, 0.0)
    hebrew_count = float(len(HEBREW_LETTERS_RE.findall(text)))
    english_count = float(len(ENGLISH_LETTERS_RE.findall(text)))
    if hebrew_count > 0 and english_count == 0:
        return ("hebrew", hebrew_count, english_count)
    if english_count > 0 and hebrew_count == 0:
        return ("english", hebrew_count, english_count)
    if hebrew_count > 0 and english_count > 0:
        return ("mixed", hebrew_count, english_count)
    return ("unknown", hebrew_count, english_count)


def translate_with_map(text: str, mapping: Dict[str, str]) -> str:
    out = []
    for ch in text:
        if ch in mapping:
            out.append(mapping[ch])
            continue
        lower = ch.lower()
        if lower in mapping:
            mapped = mapping[lower]
            out.append(mapped.upper() if ch.isupper() and mapped.isalpha() else mapped)
        else:
            out.append(ch)
    return "".join(out)


def auto_fix_text(original: str) -> Tuple[str, str]:
    detected, _, _ = detect_layout(original)
    if detected == "hebrew":
        return translate_with_map(original, HE_TO_EN), "Detected Hebrew layout → mapped to English keys."
    if detected == "english":
        return translate_with_map(original, EN_TO_HE), "Detected English layout → mapped to Hebrew keys."
    if detected == "mixed":
        candidate_en = translate_with_map(original, HE_TO_EN)
        candidate_he = translate_with_map(original, EN_TO_HE)
        score_en = len(ENGLISH_LETTERS_RE.findall(candidate_en))
        score_he = len(HEBREW_LETTERS_RE.findall(candidate_he))
        if score_en > score_he:
            return candidate_en, "Mixed text → preferred English mapping."
        return candidate_he, "Mixed text → preferred Hebrew mapping."
    return original, "No clear alphabet detected — left unchanged."


def fix_keyboard(text: str, mode: str = "auto") -> Dict[str, object]:
    from typing import Dict  # noqa: F401 — keep annotation local-safe

    original = text or ""
    detected, he_n, en_n = detect_layout(original)
    mode_l = (mode or "auto").lower()
    if mode_l in {"he_to_en", "he→en", "hebrew_to_english"}:
        fixed = translate_with_map(original, HE_TO_EN)
        explanation = "Manual Hebrew → English key map."
    elif mode_l in {"en_to_he", "en→he", "english_to_hebrew"}:
        fixed = translate_with_map(original, EN_TO_HE)
        explanation = "Manual English → Hebrew key map."
    else:
        fixed, explanation = auto_fix_text(original)
    return {
        "ok": True,
        "original": original,
        "fixed": fixed,
        "detected": detected,
        "hebrew_chars": he_n,
        "english_chars": en_n,
        "mode": mode_l,
        "explanation": explanation,
        "alt_he": translate_with_map(original, EN_TO_HE),
        "alt_en": translate_with_map(original, HE_TO_EN),
    }
