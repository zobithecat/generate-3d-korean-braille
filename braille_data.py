# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 zobithecat
# Derivative of https://github.com/benjaminaigner/braillegenerator
#   Copyright (C) Benjamin Aigner (GPL-3.0)
"""Braille character mappings, Hangul decomposition, and text-to-cells conversion.

Cell representation: a list of dot numbers using the standard 6-dot layout:
    1 4
    2 5
    3 6
An empty list [] represents a blank cell (space).
"""

# ---------------------------------------------------------------------------
# Geometric constants (match braille.jscad defaults)
# ---------------------------------------------------------------------------
DOT_DIAMETER = 1.44          # mm
DOT_RADIUS = DOT_DIAMETER / 2
PLATE_THICKNESS = 2.0        # mm
DOT_SPACING = 2.5            # distance between adjacent dot centers within a cell
CHAR_WIDTH = 6.0             # horizontal distance between cell starts
LINE_HEIGHT = 10.8           # vertical distance between line starts
MARGIN = 2.0                 # plate margin around dots

# Offsets (dx, dy) within a cell for each standard dot number.
DOT_OFFSETS = {
    1: (0.0, 0.0),
    2: (0.0, DOT_SPACING),
    3: (0.0, 2 * DOT_SPACING),
    4: (DOT_SPACING, 0.0),
    5: (DOT_SPACING, DOT_SPACING),
    6: (DOT_SPACING, 2 * DOT_SPACING),
}

# ---------------------------------------------------------------------------
# English Braille (Grade 1)
# ---------------------------------------------------------------------------
ENGLISH_BRAILLE = {
    'a': [1],          'b': [1, 2],       'c': [1, 4],
    'd': [1, 4, 5],    'e': [1, 5],       'f': [1, 2, 4],
    'g': [1, 2, 4, 5], 'h': [1, 2, 5],    'i': [2, 4],
    'j': [2, 4, 5],    'k': [1, 3],       'l': [1, 2, 3],
    'm': [1, 3, 4],    'n': [1, 3, 4, 5], 'o': [1, 3, 5],
    'p': [1, 2, 3, 4], 'q': [1, 2, 3, 4, 5], 'r': [1, 2, 3, 5],
    's': [2, 3, 4],    't': [2, 3, 4, 5], 'u': [1, 3, 6],
    'v': [1, 2, 3, 6], 'w': [2, 4, 5, 6], 'x': [1, 3, 4, 6],
    'y': [1, 3, 4, 5, 6], 'z': [1, 3, 5, 6],
}

ENGLISH_PUNCT = {
    ',': [2], '.': [2, 5, 6], '?': [2, 3, 6], '!': [2, 3, 5],
    ';': [2, 3], ':': [2, 5], "'": [3], '-': [3, 6],
    '(': [1, 2, 3, 5, 6], ')': [2, 3, 4, 5, 6], '"': [2, 3, 6],
}

NUMBER_SIGN = [3, 4, 5, 6]
CAPITAL_SIGN = [6]
LETTER_SIGN = [5, 6]

NUMBER_BRAILLE = {
    '1': [1], '2': [1, 2], '3': [1, 4], '4': [1, 4, 5], '5': [1, 5],
    '6': [1, 2, 4], '7': [1, 2, 4, 5], '8': [1, 2, 5],
    '9': [2, 4], '0': [2, 4, 5],
}

# ---------------------------------------------------------------------------
# Korean Braille (한국 점자) - based on 국립국어원 2017 개정 한국 점자 규정
# Each jamo maps to one or more cells.
# ---------------------------------------------------------------------------
KOREAN_INITIAL = {
    'ㄱ': [[4]],
    'ㄲ': [[6], [4]],
    'ㄴ': [[1, 4]],
    'ㄷ': [[2, 4]],
    'ㄸ': [[6], [2, 4]],
    'ㄹ': [[5]],
    'ㅁ': [[1, 5]],
    'ㅂ': [[4, 5]],
    'ㅃ': [[6], [4, 5]],
    'ㅅ': [[6]],
    'ㅆ': [[6], [6]],
    'ㅇ': [],                 # null initial - omitted in Korean braille
    'ㅈ': [[4, 6]],
    'ㅉ': [[6], [4, 6]],
    'ㅊ': [[5, 6]],
    'ㅋ': [[1, 2, 4]],
    'ㅌ': [[1, 2, 5]],
    'ㅍ': [[1, 4, 5]],
    'ㅎ': [[2, 4, 5]],
}

KOREAN_VOWEL = {
    'ㅏ': [[1, 2, 6]],
    'ㅐ': [[1, 2, 3, 5]],
    'ㅑ': [[3, 4, 5]],
    'ㅒ': [[3, 4, 5], [1, 2, 3, 5]],
    'ㅓ': [[2, 3, 4]],
    'ㅔ': [[1, 3, 4, 5]],
    'ㅕ': [[1, 5, 6]],
    'ㅖ': [[3, 4]],
    'ㅗ': [[1, 3, 6]],
    'ㅘ': [[1, 2, 3, 6]],
    'ㅙ': [[1, 2, 3, 6], [1, 2, 3, 5]],
    'ㅚ': [[1, 3, 4, 5, 6]],
    'ㅛ': [[3, 4, 6]],
    'ㅜ': [[1, 3, 4]],
    'ㅝ': [[1, 3, 4], [2, 3, 4]],
    'ㅞ': [[1, 3, 4], [1, 3, 4, 5]],
    'ㅟ': [[1, 3, 4], [1, 3, 5]],
    'ㅠ': [[1, 4, 6]],
    'ㅡ': [[2, 4, 6]],
    'ㅢ': [[2, 4, 6], [1, 3, 5]],
    'ㅣ': [[1, 3, 5]],
}

KOREAN_FINAL = {
    '':   [],                 # no final
    'ㄱ': [[1]],
    'ㄲ': [[1], [1]],
    'ㄳ': [[1], [3]],
    'ㄴ': [[2, 5]],
    'ㄵ': [[2, 5], [1, 3]],
    'ㄶ': [[2, 5], [3, 5, 6]],
    'ㄷ': [[3, 5]],
    'ㄹ': [[2]],
    'ㄺ': [[2], [1]],
    'ㄻ': [[2], [2, 6]],
    'ㄼ': [[2], [1, 2]],
    'ㄽ': [[2], [3]],
    'ㄾ': [[2], [2, 3, 6]],
    'ㄿ': [[2], [2, 5, 6]],
    'ㅀ': [[2], [3, 5, 6]],
    'ㅁ': [[2, 6]],
    'ㅂ': [[1, 2]],
    'ㅄ': [[1, 2], [3]],
    'ㅅ': [[3]],
    'ㅆ': [[3, 4]],
    'ㅇ': [[2, 3, 5, 6]],
    'ㅈ': [[1, 3]],
    'ㅊ': [[2, 3]],
    'ㅋ': [[2, 3, 5]],
    'ㅌ': [[2, 3, 6]],
    'ㅍ': [[2, 5, 6]],
    'ㅎ': [[3, 5, 6]],
}

# ---------------------------------------------------------------------------
# Hangul syllable decomposition (U+AC00 .. U+D7A3)
# ---------------------------------------------------------------------------
_INITIAL_LIST = [
    'ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ',
    'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ',
]
_VOWEL_LIST = [
    'ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ',
    'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ',
]
_FINAL_LIST = [
    '', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ',
    'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ',
    'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ',
]

_HANGUL_BASE = 0xAC00
_HANGUL_LAST = 0xD7A3


def is_hangul_syllable(ch: str) -> bool:
    return len(ch) == 1 and _HANGUL_BASE <= ord(ch) <= _HANGUL_LAST


def decompose_hangul(ch: str):
    """Return (initial, vowel, final) for a Hangul syllable, or None."""
    if not is_hangul_syllable(ch):
        return None
    code = ord(ch) - _HANGUL_BASE
    initial = _INITIAL_LIST[code // 588]
    vowel = _VOWEL_LIST[(code % 588) // 28]
    final = _FINAL_LIST[code % 28]
    return initial, vowel, final


# ---------------------------------------------------------------------------
# Text -> cells
# ---------------------------------------------------------------------------
def text_to_cells(text: str):
    """Convert free-form text into a list of lines; each line is a list of cells."""
    output_lines = []
    for raw_line in text.split('\n'):
        cells = []
        prev_is_digit = False

        for ch in raw_line:
            if is_hangul_syllable(ch):
                prev_is_digit = False
                initial, vowel, final = decompose_hangul(ch)
                cells.extend(KOREAN_INITIAL.get(initial, []))
                cells.extend(KOREAN_VOWEL.get(vowel, []))
                cells.extend(KOREAN_FINAL.get(final, []))
                continue

            if ch in KOREAN_INITIAL:
                prev_is_digit = False
                cells.extend(KOREAN_INITIAL[ch])
                continue
            if ch in KOREAN_VOWEL:
                prev_is_digit = False
                cells.extend(KOREAN_VOWEL[ch])
                continue

            if ch in NUMBER_BRAILLE:
                if not prev_is_digit:
                    cells.append(list(NUMBER_SIGN))
                cells.append(list(NUMBER_BRAILLE[ch]))
                prev_is_digit = True
                continue

            if ch == ' ':
                cells.append([])
                prev_is_digit = False
                continue

            lower = ch.lower()
            if lower in ENGLISH_BRAILLE:
                if prev_is_digit and lower in 'abcdefghij':
                    cells.append(list(LETTER_SIGN))
                if ch.isupper():
                    cells.append(list(CAPITAL_SIGN))
                cells.append(list(ENGLISH_BRAILLE[lower]))
                prev_is_digit = False
                continue

            if ch in ENGLISH_PUNCT:
                cells.append(list(ENGLISH_PUNCT[ch]))
                prev_is_digit = False
                continue

            if ch == '\t':
                cells.append([])
                prev_is_digit = False
                continue

            cells.append([])
            prev_is_digit = False

        output_lines.append(cells)

    return output_lines


def cells_to_unicode(cells) -> str:
    """Render cells using Unicode Braille (U+2800..U+28FF) for preview."""
    out = []
    for dots in cells:
        value = 0
        for d in dots:
            if 1 <= d <= 6:
                value |= 1 << (d - 1)
        out.append(chr(0x2800 + value))
    return ''.join(out)
