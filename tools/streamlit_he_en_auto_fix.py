# File: C:/AI_Backtest_Dev/streamlit_he_en_auto_fix.py

"""
This module provides a Streamlit app that auto-detects
and fixes Hebrew↔English keyboard layout mistakes.
Created by Chanan Zevin.
"""

from __future__ import annotations

import streamlit as st
import re
from typing import Dict, Tuple

# --------------------------------------------------------------------------------
# Keyboard mappings: Hebrew <-> English
# --------------------------------------------------------------------------------
# NOTE: mappings include unshifted and common shifted characters,
#       punctuation, numbers and brackets as they appear on standard
#       Hebrew/English keyboard layouts.
#       Keep mappings comprehensive to handle punctuation correctly.

HE_TO_EN: Dict[str, str] = {
    "׳": "'", "״": '"', "־": "-", " ":" ",
    # letters
    "ק": "q", "ר": "w", "א": "e", "ט": "r", "ו": "t", "ן": "y", "ם": "u", "פ": "i",
    "ש": "a", "ד": "s", "ג": "d", "כ": "f", "ע": "g", "י": "h", "ח": "j", "ל": "k",
    "ך": "l", "ף": ";", "ז": "z", "ס": "x", "ב": "c", "ה": "v", "נ": "b", "מ": "n",
    "צ": "m", "ת": ",",
    # numbers and shifted numbers (common on keyboard; map to same)
    "0": "0", "1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7",
    "8": "8", "9": "9",
    # punctuation and symbols (unshifted)
    ".": ":", ",": "?", "/": ".", ";": "p", "'": "[", "[": "]", "]": "\\",
    "-": "-", "=": "=",
    # Hebrew punctuation commonly typed with English layout
    ".": ".", ",": ","
}

EN_TO_HE: Dict[str, str] = {v: k for k, v in HE_TO_EN.items()}

# Expand mapping to cover uppercase letters by mapping uppercase to corresponding hebrew
# (we will handle case by preserving case for English letters; Hebrew has no case)
for en_char, he_char in list(EN_TO_HE.items()):
    if en_char.isalpha():
        EN_TO_HE[en_char.upper()] = he_char

# Some characters mapping are ambiguous or different in some layouts.
# We'll add an alternate explicit mapping for common punctuation one-to-one.
ADDITIONAL_HE_TO_EN = {
    " ": " ",
    "־": "-",
    "–": "-",
    "—": "-",
    "“": '"',
    "”": '"',
    "‘": "'",
    "’": "'",
    "…": "..."
}
for k, v in ADDITIONAL_HE_TO_EN.items():
    HE_TO_EN.setdefault(k, v)

# Create a more complete mapping for punctuation the English-to-Hebrew direction
ADDITIONAL_EN_TO_HE = {
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
}
for k, v in ADDITIONAL_EN_TO_HE.items():
    EN_TO_HE.setdefault(k, v)

# --------------------------------------------------------------------------------
# Utility functions
# --------------------------------------------------------------------------------
HEBREW_LETTERS_RE = re.compile(r"[\u0590-\u05FF]")  # Hebrew Unicode block
ENGLISH_LETTERS_RE = re.compile(r"[A-Za-z]")

def detect_layout(text: str) -> Tuple[str, float, float]:
    """
    Detect whether text is typed in Hebrew layout or English layout by mistake.
    Returns a tuple: (detected_layout, hebrew_score, english_score)
    detected_layout is one of: 'hebrew', 'english', 'mixed', 'unknown'
    hebrew_score and english_score are counts of letters found.
    """
    if not text:
        return ("unknown", 0.0, 0.0)
    hebrew_count = len(HEBREW_LETTERS_RE.findall(text))
    english_count = len(ENGLISH_LETTERS_RE.findall(text))
    # consider digits and punctuation as neutral
    if hebrew_count > 0 and english_count == 0:
        return ("hebrew", float(hebrew_count), float(english_count))
    if english_count > 0 and hebrew_count == 0:
        return ("english", float(hebrew_count), float(english_count))
    # mixed: both alphabets present
    if hebrew_count > 0 and english_count > 0:
        return ("mixed", float(hebrew_count), float(english_count))
    return ("unknown", float(hebrew_count), float(english_count))

def translate_with_map(text: str, mapping: Dict[str, str]) -> str:
    """
    Translate text character-by-character using provided mapping.
    Characters not found in mapping are preserved unchanged.
    This preserves whitespace and punctuation if mapping covers them.
    """
    result_chars = []
    for ch in text:
        # preserve combining marks and diacritics if any
        if ch in mapping:
            result_chars.append(mapping[ch])
        else:
            # try lowercase/uppercase fallback for English letters
            lower = ch.lower()
            if lower in mapping:
                mapped = mapping[lower]
                # preserve original case if mapping is alphabetic English
                if ch.isupper():
                    result_chars.append(mapped.upper())
                else:
                    result_chars.append(mapped)
            else:
                result_chars.append(ch)
    return "".join(result_chars)

def auto_fix_text(original: str) -> Tuple[str, str]:
    """
    Auto-detect mistaken layout and return (fixed_text, method_explanation).
    method_explanation is a short Hebrew string explaining what was done.
    """
    detected, heb_count, en_count = detect_layout(original)
    # Heuristic: if text contains only English letters but many characters are
    # where Hebrew letters would usually be (i.e., user typed with wrong layout),
    # we attempt to map EN->HE or HE->EN according to detection.
    # Use lengths and proportion to decide.
    if detected == "hebrew":
        # text appears as Hebrew, so maybe the user intended English but keyboard was HE
        fixed = translate_with_map(original, HE_TO_EN)
        return fixed, "זוהתה הקלדה בעברית. טקסט הומר לאנגלית באמצעות מיפוי מקשים."
    if detected == "english":
        # text appears as English, maybe keyboard was EN but intended Hebrew
        fixed = translate_with_map(original, EN_TO_HE)
        return fixed, "זוהתה הקלדה באנגלית. טקסט הומר לעברית באמצעות מיפוי מקשים."
    if detected == "mixed":
        # Mixed: try both translations and choose the one with more valid words (simple heuristic)
        candidate_en = translate_with_map(original, HE_TO_EN)
        candidate_he = translate_with_map(original, EN_TO_HE)
        # Heuristic scoring: count occurrences of vowels/letters common in each language
        score_en = len(ENGLISH_LETTERS_RE.findall(candidate_en))
        score_he = len(HEBREW_LETTERS_RE.findall(candidate_he))
        # prefer larger increase in alphabet presence
        if score_en > score_he:
            return candidate_en, "טקסט מעורב. המרה ל-EN נבחרה לפי בדיקת תווים."
        else:
            return candidate_he, "טקסט מעורב. המרה ל-HE נבחרה לפי בדיקת תווים."
    # unknown or empty
    return original, "לא זוהתה שפה ברורה. לא בוצעה המרה אוטומטית."

# --------------------------------------------------------------------------------
# Streamlit UI
# --------------------------------------------------------------------------------
st.set_page_config(page_title="תיקון פריסת מקשים HE/EN", layout="centered")

st.title("תיקון פריסת מקשים — עברית ↔ אנגלית")

st.markdown(
    "היישום מתקן טעויות כאשר המשתמש הקליד עם פריסת מקשים לא נכונה."
)

with st.form("keyboard_fix_form"):
    input_text = st.text_area("הקלד טקסט כאן:", value="", height=160)
    col1, col2 = st.columns([1, 1])
    with col1:
        auto_mode = st.checkbox("גילוי אוטומטי של פריסת המקשים", value=True)
    with col2:
        direction_option = st.selectbox(
            "כיוון המרה (יש לבחור אם לא אוטומטי):",
            ("אין - שימוש באוטומטי", "עברית → אנגלית", "אנגלית → עברית")
        )
    st.write("")  # spacer
    submitted = st.form_submit_button("תרגם / תקן")

# Show detection hints upfront for the user before pressing translate
if input_text.strip():
    detected, hc, ec = detect_layout(input_text)
    hint_map = {
        "hebrew": "נראה כי הטקסט מכיל תווים בעברית בלבד.",
        "english": "נראה כי הטקסט מכיל תווים באנגלית בלבד.",
        "mixed": "נראה כי הטקסט מכיל תווים בעברית ובאנגלית.",
        "unknown": "לא נצפו תווים אלפביתיים ברורים."
    }
    st.info(f"זיהוי פריסה: {hint_map.get(detected,'לא ידוע')} (he={int(hc)}, en={int(ec)})")

# On submit, perform translation/fix
if submitted:
    if not input_text.strip():
        st.warning("אנא הכנס טקסט לקליטה לפני לחיצה על תרגם.")
    else:
        # Determine mapping approach
        if auto_mode:
            fixed_text, explanation = auto_fix_text(input_text)
            st.success("בוצע תיקון אוטומטי.")
            st.write(explanation)
        else:
            # Manual direction chosen
            if direction_option == "עברית → אנגלית":
                fixed_text = translate_with_map(input_text, HE_TO_EN)
                st.success("המרה: עברית → אנגלית בוצעה.")
            elif direction_option == "אנגלית → עברית":
                fixed_text = translate_with_map(input_text, EN_TO_HE)
                st.success("המרה: אנגלית → עברית בוצעה.")
            else:
                fixed_text = input_text
                st.info("לא בוצעה המרה - בחר/י כיוון המרה או הפעל/י גילוי אוטומטי.")
        # Display original and fixed side-by-side
        st.subheader("תוצאה")
        col_a, col_b = st.columns(2)
        with col_a:
            st.caption("מקור:")
            st.text_area("מקור", value=input_text, height=180)
        with col_b:
            st.caption("תוקן:")
            st.text_area("תוקן", value=fixed_text, height=180)

        # Additional helper: offer to swap suggestions when ambiguous
        # Provide the alternative (the opposite mapping) so user can choose
        alt_candidate_he = translate_with_map(input_text, EN_TO_HE)
        alt_candidate_en = translate_with_map(input_text, HE_TO_EN)
        st.write("")  # spacer
        st.markdown("**אפשרויות נוספות:**")
        if alt_candidate_en != fixed_text:
            st.write("- המרה נוספת לעיון (עברית→אנגלית):")
            st.code(alt_candidate_en)
        if alt_candidate_he != fixed_text:
            st.write("- המרה נוספת לעיון (אנגלית→עברית):")
            st.code(alt_candidate_he)

        # Provide a small note about limitations
        st.info(
            "הערה: המרה מבוססת על מיפוי תווים."
            " במקרים של שגיאות הקלדה אמיתיות"
            " או מלים משולבות, ייתכן כי התוצאה דורשת בדיקה ידנית."
        )

# Footer / usage hint
st.write("")
st.markdown(
    "מדריך מהיר: אם תקלידו עברית אך המקלדת הוגדרה לאנגלית,"
    " הפעילו גילוי אוטומטי ולחצו על 'תרגם / תקן'."
)

# To run:
# streamlit run C:/AI_Backtest_Dev/streamlit_he_en_auto_fix.py
