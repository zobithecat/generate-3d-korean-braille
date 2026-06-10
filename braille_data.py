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

# UEB (통일 영어 점자) punctuation — 로마자 사이에 나타나는 부호에 한해 적용.
# 출처: 한국 점자 규정 제32항 [붙임] 표.
UEB_PUNCT = {
    ',': [2], '.': [2, 5, 6], '?': [2, 3, 6], '!': [2, 3, 5],
    ';': [2, 3], ':': [2, 5], "'": [3], '-': [3, 6],
    '(': [1, 2, 3, 5, 6], ')': [2, 3, 4, 5, 6], '"': [2, 3, 6],
    # ASCII math/symbol — Roman context uses NABU single-cell forms.
    '/': [3, 4],          # ⠌
    '+': [3, 4, 6],       # ⠬  (NABU `+`)
    '=': [1, 2, 3, 4, 5, 6],  # ⠿  (NABU `=`)
    '*': [1, 6],          # ⠡  (NABU `*`)
}

# 한글 점자 문장 부호 (제44~67항) — 한글 본문 컨텍스트에서 우선 적용.
# PDF 해설서 line 2520 비교 표 + 본문 항 직접 검증.
KOREAN_PUNCT = {
    ',': [5],                   # ⠐  쉼표 (제47항). 자릿점 쉼표는 별도 처리.
    '.': [2, 5, 6],             # ⠲  마침표 (제44항). 소수점도 동일.
    '?': [2, 3, 6],             # ⠦  물음표 (제45항)
    '!': [2, 3, 5],             # ⠖  느낌표 (제46항)
    "'": [3],                   # ⠄  아포스트로피 / 여는 작은따옴표
                                #     (닫는 작은따옴표는 별도 2셀, MULTI)
    '-': [3, 6],                # ⠤  붙임표 (제59항)
}

# 한글 점자 다중 셀 문장 부호.
KOREAN_PUNCT_MULTI = {
    ':':  [[5], [2]],                       # ⠐⠂  쌍점 (제49항)
    ';':  [[5, 6], [2, 3]],                 # ⠰⠆  쌍반점 (제50항)
    '(':  [[2, 3, 6], [3]],                 # ⠦⠄  여는 소괄호 (제54항)
    ')':  [[6], [3, 5, 6]],                 # ⠠⠴  닫는 소괄호
    '{':  [[2, 3, 6], [2]],                 # ⠦⠂  여는 중괄호 (제55항)
    '}':  [[5], [3, 5, 6]],                 # ⠐⠴  닫는 중괄호
    '[':  [[2, 3, 6], [2, 3]],              # ⠦⠆  여는 대괄호 (제56항)
    ']':  [[5, 6], [3, 5, 6]],              # ⠰⠴  닫는 대괄호
    '·':  [[5], [2, 3]],                    # ⠐⠆  가운뎃점 (제48항)
    '~':  [[3, 6], [3, 6]],                 # ⠤⠤  물결표 (제61항) — 줄표와 동형
    '*':  [[3, 5], [3, 5]],                 # ⠔⠔  별표 (제68항)
    '/':  [[4, 5, 6], [3, 4]],              # ⠸⠌  빗금 (제51항)
    '…':  [[2, 5, 6]] * 3,                  # ⠲⠲⠲  줄임표 — 마침표 3개 (제67항)
    # 따옴표 — 한국 점자 규정은 여는/닫는 구분
    '"':  [[2, 3, 6]],                      # 큰따옴표는 단일 셀이지만 처리 통일 위해 multi
    # 골뱅이/우물/도/℃ — 한국 점자 규정 부호 (외래 부호 처리)
    '@':  [[4], [1]],                       # ⠈⠁  골뱅이 ('그 밖의 기호')
    '#':  [[4, 5, 6], [1, 4, 5, 6]],        # ⠸⠹  우물(샵)
    '°':  [[3, 5, 6], [1, 4, 5]],           # ⠴⠙  도 — 로마자 표 + d
    '℃':  [[3, 5, 6], [1, 4, 5], [6], [1, 4]],     # ⠴⠙⠠⠉  °+ Cap+ C
    '℉':  [[3, 5, 6], [1, 4, 5], [6], [1, 2, 4]],  # ⠴⠙⠠⠋  °+ Cap+ F
    '%':  [[3, 5, 6], [1, 2, 3, 4]],        # ⠴⠏  백분율 — 로마자 표 + p (제31항)
    # 수학 기호 (제73항) — 한글 본문 컨텍스트 기본값
    '+':  [[2, 6]],                         # ⠢  덧셈
    '−':  [[3, 5]],                         # ⠔  뺄셈/음수 (U+2212, ASCII '-' 와 구분)
    '=':  [[2, 5], [2, 5]],                 # ⠒⠒  등호
    '×':  [[1, 6]],                         # ⠡  곱셈
    '÷':  [[3, 4], [3, 4]],                 # ⠌⠌  나눗셈
    # 화폐 기호 (제72항) — 모두 `@` + 영문자 형식
    '₩':  [[4], [2, 4, 5, 6]],              # ⠈⠺  원
    '$':  [[4], [1, 4, 5]],                 # ⠈⠙  달러
    '€':  [[4], [1, 5]],                    # ⠈⠑  유로
    '¥':  [[4], [1, 3, 4, 5, 6]],           # ⠈⠽  엔
    '£':  [[4], [1, 2, 3]],                 # ⠈⠇  파운드
    '¢':  [[4], [1, 4]],                    # ⠈⠉  센트
    # 음수 부호 — Unicode minus sign (ASCII '-' 은 붙임표/하이픈로 별도 유지)
    '−':  [[3, 5]],                         # ⠔  뺄셈/음수 (제73항)
    # 글머리 (참고: 점역 지침)
    '•':  [[2, 3, 5, 6]],                   # ⠶  1단계 글머리
    # 그 외 외래 부호
    '^':  [[4], [2, 6]],                    # ⠈⠢  캐럿
    '&':  [[4], [1, 2, 3, 4, 6]],           # ⠈⠯  앰퍼샌드
    '※':  [[4, 5, 6], [3, 5]],              # ⠸⠔  참고표
}

# Legacy aliases for backward compatibility within this module.
ENGLISH_PUNCT = UEB_PUNCT
ENGLISH_PUNCT_MULTI = KOREAN_PUNCT_MULTI

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


# VF 약자 14종 — 국립국어원 한국 점자 규정 제15항.
# 점형은 PDF 해설서 (ASCII Braille NABU 디코딩) 직접 검증.
#   은 약자 점형: PDF 해설서 line 1006 '은빛 z~o2'에서 z=⠵(1-3-5-6)로 확정.
#                (1-3-4-5-6=⠽가 아님 — 이전 구현 버그 수정)
#   을 약자 신규: PDF 제15항 14번째 약자, line 1185 '긁다 @!ai'에서 !=⠮로 확정.
KOREAN_VF_ABBREV = {
    ('ㅓ', 'ㄱ'): [1, 4, 5, 6],        # 억 ⠹  (NABU `?`)
    ('ㅓ', 'ㄴ'): [2, 3, 4, 5, 6],     # 언 ⠾  (NABU `)`)
    ('ㅓ', 'ㄹ'): [2, 3, 4, 5],        # 얼 ⠞  (NABU `T`)
    ('ㅕ', 'ㄴ'): [1, 6],              # 연 ⠡  (NABU `*`)
    ('ㅕ', 'ㄹ'): [1, 2, 5, 6],        # 열 ⠳  (NABU `|`)
    ('ㅕ', 'ㅇ'): [1, 2, 4, 5, 6],     # 영 ⠻  (NABU `}`)
    ('ㅗ', 'ㄱ'): [1, 3, 4, 6],        # 옥 ⠭  (NABU `x`)
    ('ㅗ', 'ㄴ'): [1, 2, 3, 5, 6],     # 온 ⠷  (NABU `(`)
    ('ㅗ', 'ㅇ'): [1, 2, 3, 4, 5, 6],  # 옹 ⠿  (NABU `=`)
    ('ㅜ', 'ㄴ'): [1, 2, 4, 5],        # 운 ⠛  (NABU `g`)
    ('ㅜ', 'ㄹ'): [1, 2, 3, 4, 6],     # 울 ⠯  (NABU `&`)
    ('ㅡ', 'ㄴ'): [1, 3, 5, 6],        # 은 ⠵  (NABU `z`) ← 정정
    ('ㅡ', 'ㄹ'): [2, 3, 4, 6],        # 을 ⠮  (NABU `!`) ← 신규
    ('ㅣ', 'ㄴ'): [1, 2, 3, 4, 5],     # 인 ⠟  (NABU `q`)
}

# 제16항 — 성/정/청 특례.
# 'ㅅ/ㅆ/ㅈ/ㅉ/ㅊ' + 'ㅓ' + 'ㅇ받침' 음절은 영 약자(⠻)를 적용.
# 반대로 같은 초성에 'ㅕ' + 'ㅇ받침'(셩/졍/쳥)이 오면 풀어쓰기.
SEONG_INITIALS = frozenset(['ㅅ', 'ㅆ', 'ㅈ', 'ㅉ', 'ㅊ'])
YEONG_ABBREV = [1, 2, 4, 5, 6]   # ⠻ — 영 약자 (제16항에서 재사용)

# 제13항 — 단독 약자 + 받침.
# 가/나/다/마/바/사/자/카/타/파/하 음절에 받침이 추가되면, 약자 점형
# (ㅏ 생략된 형태)에 받침을 이어 적는다.
#   예) 맞 = 마 약자(⠑) + ㅈ받침(⠅) = ⠑⠅
#       갈 = 가 약자(⠫) + ㄹ받침(⠂) = ⠫⠂
#       당 = 다 약자(⠊) + ㅇ받침(⠶) = ⠊⠶  (PDF 마당 = ei7 = ⠑⠊⠶)
# None = 약자 점형이 초성과 동일 (ㅏ만 생략하면 됨).
# 명시값 = 가/사처럼 별도 점형 사용.
SINGLE_ABBREV_BY_INITIAL = {
    'ㄱ': [1, 2, 4, 6],   # 가 약자 ⠫ (ㄱ초성 ⠈와 다름)
    'ㄴ': None,            # 나 약자 = ㄴ초성 동형 ⠉
    'ㄷ': None,            # 다 = ⠊
    'ㅁ': None,            # 마 = ⠑
    'ㅂ': None,            # 바 = ⠘
    'ㅅ': [1, 2, 3],       # 사 약자 ⠇ (ㅅ초성 ⠠와 다름)
    'ㅈ': None,            # 자 = ⠨
    'ㅋ': None,            # 카 = ⠋
    'ㅌ': None,            # 타 = ⠓
    'ㅍ': None,            # 파 = ⠙
    'ㅎ': None,            # 하 = ⠚
}

# 제14항 — 된소리 단독 약자.
# 까/싸/껏은 된소리표(⠠, dot 6) + 가/사/것 약자 형태로 적는다.
#   까 = 된소리표(⠠) + 가 약자(⠫) = ⠠⠫
#   싸 = 된소리표(⠠) + 사 약자(⠇) = ⠠⠇
#   깟/쌌 등도 동일하게 된소리표 + 약자 + 받침
TENSED_PREFIX = [6]   # ⠠ — 된소리 표지
TENSED_ABBREV_BY_INITIAL = {
    'ㄲ': [1, 2, 4, 6],   # 까 → ⠠⠫
    'ㅆ': [1, 2, 3],       # 싸 → ⠠⠇
}

# 제17항 — 단독 약자 받침 없고 다음 음절이 모음으로 시작하면 ㅏ 살림.
# 'ㄴ/ㄷ/ㅁ/ㅂ/ㅈ/ㅋ/ㅌ/ㅍ/ㅎ'에 적용 ('ㄱ'/'ㅅ'은 예외 없이 항상 약자).
#   예) 다음 = ⠊⠣⠪⠢  (다 약자 안 쓰고 long form)
#       카카오 = ⠋⠋⠣⠥  (두 번째 카는 long form, '오'가 ㅇ초성)
#       마음 = ⠑⠣⠪⠢
JEH_17_INITIALS = frozenset(['ㄴ', 'ㄷ', 'ㅁ', 'ㅂ', 'ㅈ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'])

# 겹받침 → (앞 자음, 뒤 자음) 분해.
# 제15항 해설: VF 약자는 단일 받침뿐 아니라 겹받침의 앞 자음과도 매칭된다.
#   예) 긁 = ㄱ+ㅡ+ㄺ(=ㄹ+ㄱ) → ㄱ + 을 약자(ㅡ,ㄹ) + ㄱ받침
#       끊 = ㄲ+ㅡ+ㄶ(=ㄴ+ㅎ) → ㄲ + 은 약자(ㅡ,ㄴ) + ㅎ받침
KOREAN_COMPOUND_FINAL = {
    'ㄳ': ('ㄱ', 'ㅅ'),
    'ㄵ': ('ㄴ', 'ㅈ'),
    'ㄶ': ('ㄴ', 'ㅎ'),
    'ㄺ': ('ㄹ', 'ㄱ'),
    'ㄻ': ('ㄹ', 'ㅁ'),
    'ㄼ': ('ㄹ', 'ㅂ'),
    'ㄽ': ('ㄹ', 'ㅅ'),
    'ㄾ': ('ㄹ', 'ㅌ'),
    'ㄿ': ('ㄹ', 'ㅍ'),
    'ㅀ': ('ㄹ', 'ㅎ'),
    'ㅄ': ('ㅂ', 'ㅅ'),
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
        # prev_alpha_kind tracks the most recent letter-bearing character
        # for punctuation context disambiguation. 'korean' is the default
        # so that isolated punctuation in pure-Korean text uses 한국 점자
        # 규정 mappings; switches to 'roman' inside ASCII letter runs.
        prev_alpha_kind = 'korean'
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
                    prev_alpha_kind = 'korean'
                    matched = True
                    break
            if matched:
                continue

            # 2) Hangul composed syllable
            if is_hangul_syllable(ch):
                if prev_is_digit:
                    cells.append([])  # 숫자→한글 사이 분리
                prev_is_digit = False
                prev_alpha_kind = 'korean'
                decomp = decompose_hangul(ch)
                # mypy/pyright: is_hangul_syllable guarantees non-None
                initial, vowel, final = decomp  # type: ignore[misc]

                # 제14항 — 된소리 단독 약자 (까/싸/깟/쌌 등)
                # ㄲ/ㅆ + ㅏ → 된소리표 + 가/사 약자 (+ 받침 있으면 이어 적기)
                if vowel == 'ㅏ' and initial in TENSED_ABBREV_BY_INITIAL:
                    cells.append(list(TENSED_PREFIX))
                    cells.append(list(TENSED_ABBREV_BY_INITIAL[initial]))
                    if final:
                        if final in KOREAN_COMPOUND_FINAL:
                            for j in KOREAN_COMPOUND_FINAL[final]:
                                cells.extend(KOREAN_FINAL.get(j, []))
                        else:
                            cells.extend(KOREAN_FINAL.get(final, []))
                    i += 1
                    continue

                # 제12-13항, 제17항 — 단독 약자 11종 + 받침/제17항 예외
                if vowel == 'ㅏ' and initial in SINGLE_ABBREV_BY_INITIAL:
                    if not final:
                        # 받침 없음 — 제17항 체크
                        keep_a = False
                        if initial in JEH_17_INITIALS:
                            nxt = i + 1
                            if nxt < n and is_hangul_syllable(raw_line[nxt]):
                                next_decomp = decompose_hangul(raw_line[nxt])
                                if next_decomp and next_decomp[0] == 'ㅇ':
                                    keep_a = True
                        if keep_a:
                            # long form — ㅏ 살림
                            cells.extend(KOREAN_INITIAL.get(initial, []))
                            cells.extend(KOREAN_VOWEL['ㅏ'])
                        else:
                            # 단독 약자 (ㅏ 생략)
                            abbrev = SINGLE_ABBREV_BY_INITIAL[initial]
                            if abbrev is not None:
                                cells.append(list(abbrev))
                            else:
                                cells.extend(KOREAN_INITIAL.get(initial, []))
                    else:
                        # 받침 있음 — 제13항 (ㅏ 생략 + 약자 점형 + 받침)
                        abbrev = SINGLE_ABBREV_BY_INITIAL[initial]
                        if abbrev is not None:
                            cells.append(list(abbrev))
                        else:
                            cells.extend(KOREAN_INITIAL.get(initial, []))
                        if final in KOREAN_COMPOUND_FINAL:
                            for j in KOREAN_COMPOUND_FINAL[final]:
                                cells.extend(KOREAN_FINAL.get(j, []))
                        else:
                            cells.extend(KOREAN_FINAL.get(final, []))
                    i += 1
                    continue

                # 라/차 등 제17항 외 syllable + 기타 — 기존 로직
                if True:
                    # 제16항 — 성/정/청 특례 (ㅅ/ㅆ/ㅈ/ㅉ/ㅊ + ㅓ + ㅇ → 영 약자;
                    # 반대로 셩/졍/쳥은 풀어쓰기).
                    use_yeong_special = (
                        initial in SEONG_INITIALS
                        and vowel == 'ㅓ' and final == 'ㅇ'
                    )
                    block_yeong_normal = (
                        initial in SEONG_INITIALS
                        and vowel == 'ㅕ' and final == 'ㅇ'
                    )
                    cells.extend(KOREAN_INITIAL.get(initial, []))
                    if use_yeong_special:
                        cells.append(list(YEONG_ABBREV))
                    elif block_yeong_normal:
                        cells.extend(KOREAN_VOWEL.get(vowel, []))
                        cells.extend(KOREAN_FINAL.get(final, []))
                    elif (vowel, final) in KOREAN_VF_ABBREV:
                        cells.append(list(KOREAN_VF_ABBREV[(vowel, final)]))
                    elif (
                        final in KOREAN_COMPOUND_FINAL
                        and (vowel, KOREAN_COMPOUND_FINAL[final][0])
                            in KOREAN_VF_ABBREV
                    ):
                        # 겹받침 앞 자음 + 모음이 VF 약자 매칭 (제15항 해설)
                        first, second = KOREAN_COMPOUND_FINAL[final]
                        cells.append(list(KOREAN_VF_ABBREV[(vowel, first)]))
                        cells.extend(KOREAN_FINAL.get(second, []))
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
                prev_alpha_kind = 'korean'
                cells.extend(KOREAN_INITIAL[ch])
                i += 1
                continue
            if ch in KOREAN_VOWEL:
                if prev_is_digit:
                    cells.append([])
                prev_is_digit = False
                prev_alpha_kind = 'korean'
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
                        prev_alpha_kind = 'roman'
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
                prev_alpha_kind = 'roman'
                i += 1
                continue

            # 9) Punctuation — context-dependent.
            # In Korean context (the default), prefer 한국 점자 규정
            # mappings. In Roman context (just emitted an ASCII letter),
            # fall back to UEB mappings for ASCII punct (per 제32항 [붙임]).
            if prev_alpha_kind == 'korean':
                if ch in KOREAN_PUNCT_MULTI:
                    for c in KOREAN_PUNCT_MULTI[ch]:
                        cells.append(list(c))
                    prev_is_digit = False
                    i += 1
                    continue
                if ch in KOREAN_PUNCT:
                    cells.append(list(KOREAN_PUNCT[ch]))
                    prev_is_digit = False
                    i += 1
                    continue
            # Roman context (or punct not defined in Korean spec) → UEB
            if ch in UEB_PUNCT:
                cells.append(list(UEB_PUNCT[ch]))
                prev_is_digit = False
                i += 1
                continue
            # Fallback: any multi-cell Korean punct still works in Roman
            # context if no UEB single-cell exists.
            if ch in KOREAN_PUNCT_MULTI:
                for c in KOREAN_PUNCT_MULTI[ch]:
                    cells.append(list(c))
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
