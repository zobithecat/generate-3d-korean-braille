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
PLATE_THICKNESS = 1.5        # mm
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
    # Math / symbol additions (한국 점자 규정 부호 + UEB 관습)
    '/': [3, 4],               # ⠌  빗금 / 분수선
    '+': [2, 3, 5],            # ⠖  덧셈표 (note: shares shape with `!`)
    '=': [2, 3, 5, 6],         # ⠶  등호  (shares shape with ㅇ받침; ctx)
}

# Multi-cell punctuation. Checked before ENGLISH_PUNCT in the loop.
ENGLISH_PUNCT_MULTI = {
    '[': [[4], [2, 3, 6]],         # ⠈⠦  (한국 점자 규정 제33항)
    ']': [[3, 5, 6], [4]],         # ⠴⠈
    '*': [[1, 6], [3, 5]],         # ⠡⠔  별표
    '@': [[4], [1]],               # ⠈⠁  골뱅이 (2017 신설)
    '#': [[4, 5, 6], [1, 3, 4, 5, 6]],  # ⠸⠽  우물(샵)
    '…': [[2, 5, 6], [2, 5, 6], [2, 5, 6]],  # ⠲⠲⠲  줄임표 (제35항)
    '℃': [[4, 5], [3, 5, 6], [6], [1, 4]],   # ⠘⠴⠠⠉  °+ Cap+ C
    '℉': [[4, 5], [3, 5, 6], [6], [1, 2, 4]], # ⠘⠴⠠⠋  °+ Cap+ F
    '°': [[4, 5], [3, 5, 6]],      # ⠘⠴  도 기호
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

# ---------------------------------------------------------------------------
# 단독 약자 (한 글자 약자) - 한국 점자 규정 제29항
# '자음 + ㅏ (받침 없음)' 형태의 11개 음절은 단일 셀 약자로 적는다.
# ㅏ 중성(⠣)을 생략한다. 대부분의 약자는 초성 점형과 점 패턴이 같다
# (예: 카 약자 ⠋ == ㅋ 초성 ⠋). 가·사는 고유한 점형.
#   예) 카드 = 카(⠋) + 드(⠊⠪) = ⠋⠊⠪      (3 cells)
#       사람 = 사(⠇) + 람(⠐⠣⠢) = ⠇⠐⠣⠢   (4 cells)
# ---------------------------------------------------------------------------
KOREAN_SYLLABLE_ABBREV = {
    '가': [1, 2, 4, 6],   # ⠫
    '나': [1, 4],         # ⠉  (== ㄴ 초성)
    '다': [2, 4],         # ⠊  (== ㄷ 초성)
    '마': [1, 5],         # ⠑  (== ㅁ 초성)
    '바': [4, 5],         # ⠘  (== ㅂ 초성)
    '사': [1, 2, 3],      # ⠇
    '자': [4, 6],         # ⠨  (== ㅈ 초성)
    '카': [1, 2, 4],      # ⠋  (== ㅋ 초성)
    '타': [1, 2, 5],      # ⠓  (== ㅌ 초성)
    '파': [1, 4, 5],      # ⠙  (== ㅍ 초성)
    '하': [2, 4, 5],      # ⠚  (== ㅎ 초성)
}


# ---------------------------------------------------------------------------
# 약자 (abbreviations) - 국립국어원 2017 한국 점자 규정 제29항
# (vowel, final) 패턴이 단일 셀로 축약되며, 초성과 무관하게 적용됨.
#   예) 신 = ㅅ + (ㅣ+ㄴ → 인 약자 ⠟) = ⠠⠟  (2 cells, 3 cells가 아님)
#       분 = ㅂ + (ㅜ+ㄴ → 운 약자 ⠛) = ⠘⠛
#       인 = (ㅇ 생략) + (ㅣ+ㄴ → 인 약자 ⠟) = ⠟
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 다음절 약어 (multi-syllable contractions) - 한국 점자 규정 제30항
# These multi-syllable Korean words are written as a 2-cell abbreviation
# starting with ⠁ (dot 1) plus a distinguishing second cell.
# Matched longest-first in text_to_cells via _MULTI_ABBREV_DESC.
# ---------------------------------------------------------------------------
KOREAN_MULTI_ABBREV = {
    '그래서':   [[1], [2, 3, 4]],     # ⠁⠎
    '그러나':   [[1], [1, 4]],         # ⠁⠉
    '그러면':   [[1], [2, 5]],         # ⠁⠒
    '그러므로': [[1], [2, 6]],         # ⠁⠢
    '그런데':   [[1], [1, 3, 4, 5]],   # ⠁⠝
    '그리고':   [[1], [1, 3, 6]],      # ⠁⠥
    '그리하여': [[1], [1, 5, 6]],      # ⠁⠱
}

# Sorted longest-first so 그러므로 wins over 그러나, etc.
_MULTI_ABBREV_DESC = tuple(sorted(KOREAN_MULTI_ABBREV.keys(),
                                   key=len, reverse=True))


KOREAN_VF_ABBREV = {
    ('ㅓ', 'ㄱ'): [1, 4, 5, 6],        # 억 ⠹
    ('ㅓ', 'ㄴ'): [2, 3, 4, 5, 6],     # 언 ⠾
    ('ㅓ', 'ㄹ'): [2, 3, 4, 5],        # 얼 ⠞
    ('ㅕ', 'ㄴ'): [1, 6],              # 연 ⠡
    ('ㅕ', 'ㄹ'): [1, 2, 5, 6],        # 열 ⠳
    ('ㅕ', 'ㅇ'): [1, 2, 4, 5, 6],     # 영 ⠻
    ('ㅗ', 'ㄱ'): [1, 3, 4, 6],        # 옥 ⠭
    ('ㅗ', 'ㄴ'): [1, 2, 3, 5, 6],     # 온 ⠷
    ('ㅗ', 'ㅇ'): [1, 2, 3, 4, 5, 6],  # 옹 ⠿
    ('ㅜ', 'ㄴ'): [1, 2, 4, 5],        # 운 ⠛
    ('ㅜ', 'ㄹ'): [1, 2, 3, 4, 6],     # 울 ⠯
    ('ㅡ', 'ㄴ'): [1, 3, 4, 5, 6],     # 은 ⠵
    ('ㅣ', 'ㄴ'): [1, 2, 3, 4, 5],     # 인 ⠟
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
    """Convert free-form text into a list of lines; each line is a list of cells.

    Implements 한국 점자 규정 2017 + 2024 개정:
      - 단독 약자 11자  (제29항)
      - VF 약자 13종    (제29항)
      - 다음절 약어 7종 (제30항) — 그래서/그러나/그러면/그러므로/
                                       그런데/그리고/그리하여
      - 숫자 다음 한글 사이 빈 칸 자동 삽입 (제30항)
      - 소수점·쉼표는 number mode 유지 (⠼ 재삽입 X)
      - 연속 대문자 ≥ 2 글자는 ⠠⠠ + 평문자 (단축)
      - 대괄호 [, ] 2셀 매핑
    """
    output_lines = []
    for raw_line in text.split('\n'):
        cells = []
        prev_is_digit = False
        i = 0
        n = len(raw_line)

        while i < n:
            ch = raw_line[i]

            # 1) 다음절 약어 (longest-first)
            matched = False
            for pattern in _MULTI_ABBREV_DESC:
                if raw_line.startswith(pattern, i):
                    if prev_is_digit:
                        cells.append([])  # 숫자→한글 사이 분리
                    for c in KOREAN_MULTI_ABBREV[pattern]:
                        cells.append(list(c))
                    i += len(pattern)
                    prev_is_digit = False
                    matched = True
                    break
            if matched:
                continue

            # 2) Hangul composed syllable
            if is_hangul_syllable(ch):
                if prev_is_digit:
                    cells.append([])  # 숫자→한글 사이 분리
                prev_is_digit = False
                if ch in KOREAN_SYLLABLE_ABBREV:
                    cells.append(list(KOREAN_SYLLABLE_ABBREV[ch]))
                else:
                    initial, vowel, final = decompose_hangul(ch)
                    cells.extend(KOREAN_INITIAL.get(initial, []))
                    if (vowel, final) in KOREAN_VF_ABBREV:
                        cells.append(list(KOREAN_VF_ABBREV[(vowel, final)]))
                    else:
                        cells.extend(KOREAN_VOWEL.get(vowel, []))
                        cells.extend(KOREAN_FINAL.get(final, []))
                i += 1
                continue

            # 3) Standalone jamo (compatibility block)
            if ch in KOREAN_INITIAL:
                if prev_is_digit:
                    cells.append([])
                prev_is_digit = False
                cells.extend(KOREAN_INITIAL[ch])
                i += 1
                continue
            if ch in KOREAN_VOWEL:
                if prev_is_digit:
                    cells.append([])
                prev_is_digit = False
                cells.extend(KOREAN_VOWEL[ch])
                i += 1
                continue

            # 4) Decimal point / thousands-comma inside a number
            #    (keep number mode active so ⠼ isn't re-emitted)
            if prev_is_digit and ch in '.,':
                if ch == '.':
                    cells.append([2, 5, 6])    # ⠲
                else:
                    cells.append([2])           # ⠂
                # prev_is_digit stays True
                i += 1
                continue

            # 4b) Hyphen between digits keeps number mode active
            #     so ⠼ isn't re-emitted (e.g. phone "010-1234-5678",
            #     date "2026-05-18").
            if (
                prev_is_digit and ch == '-'
                and i + 1 < n and raw_line[i + 1] in NUMBER_BRAILLE
            ):
                cells.append(list(ENGLISH_PUNCT['-']))  # ⠤
                # prev_is_digit stays True — next digit will NOT re-emit ⠼
                i += 1
                continue

            # 5) Digit
            if ch in NUMBER_BRAILLE:
                if not prev_is_digit:
                    cells.append(list(NUMBER_SIGN))
                cells.append(list(NUMBER_BRAILLE[ch]))
                prev_is_digit = True
                i += 1
                continue

            # 6) Whitespace
            if ch == ' ':
                cells.append([])
                prev_is_digit = False
                i += 1
                continue
            if ch == '\t':
                cells.append([])
                prev_is_digit = False
                i += 1
                continue

            # 7) Run of ≥ 2 consecutive uppercase ASCII letters → double-cap
            #    prefix. Restrict to ASCII so Korean chars don't get pulled
            #    into the "alphabetic run" (Python's str.isalpha() is True
            #    for Hangul too).
            def _is_ascii_alpha(c):
                return c.isascii() and c.isalpha()

            if _is_ascii_alpha(ch) and ch.isupper():
                is_run_start = (i == 0) or not _is_ascii_alpha(raw_line[i - 1])
                if is_run_start:
                    j = i
                    while j < n and _is_ascii_alpha(raw_line[j]):
                        j += 1
                    run = raw_line[i:j]
                    if len(run) >= 2 and run.isupper():
                        cells.append(list(CAPITAL_SIGN))
                        cells.append(list(CAPITAL_SIGN))
                        for k in range(i, j):
                            cells.append(list(ENGLISH_BRAILLE[raw_line[k].lower()]))
                        prev_is_digit = False
                        i = j
                        continue

            # 8) English letter (single or mixed-case)
            lower = ch.lower()
            if lower in ENGLISH_BRAILLE:
                if prev_is_digit and lower in 'abcdefghij':
                    cells.append(list(LETTER_SIGN))
                if ch.isupper():
                    cells.append(list(CAPITAL_SIGN))
                cells.append(list(ENGLISH_BRAILLE[lower]))
                prev_is_digit = False
                i += 1
                continue

            # 9) Multi-cell punctuation (대괄호 등)
            if ch in ENGLISH_PUNCT_MULTI:
                for c in ENGLISH_PUNCT_MULTI[ch]:
                    cells.append(list(c))
                prev_is_digit = False
                i += 1
                continue

            # 10) Single-cell punctuation
            if ch in ENGLISH_PUNCT:
                cells.append(list(ENGLISH_PUNCT[ch]))
                prev_is_digit = False
                i += 1
                continue

            # 11) Unknown → blank cell
            cells.append([])
            prev_is_digit = False
            i += 1

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
