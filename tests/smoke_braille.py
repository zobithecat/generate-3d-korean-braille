#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 zobithecat
"""Round-trip smoke test for Korean braille conversion.

Reference: https://t.hi098123.com/braille (한글 점자 규정 2017 + 2024 개정 반영)

The reference site's converter is heavily obfuscated and gates conversion
behind trusted browser events, so live scraping isn't reliable. Instead this
file holds a curated set of (text, expected braille) pairs that have been
**cross-checked against that site by hand**, organised by rule category.

Run from the project root:

    python3 tests/smoke_braille.py

Exit code 0 = all pass, 1 = any failure.
"""
import os
import sys
import time

# Allow running from anywhere
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from braille_data import text_to_cells, cells_to_unicode  # noqa: E402


# ---------------------------------------------------------------------------
# Test corpus. Each tuple = (label, text, expected_braille).
# Sources marked:
#   [USER]  = printed and verified by the project user
#   [REF]   = cross-checked against t.hi098123.com/braille
#   [RULE]  = derived from 한국 점자 규정 제29항 directly
# ---------------------------------------------------------------------------

CASES = [
    # ── User-verified ground truth ──────────────────────────────────────
    ('신분증',     '⠠⠟⠘⠛⠨⠪⠶',     'USER'),
    ('카드입구',   '⠋⠊⠪⠕⠃⠈⠍',     'USER'),
    ('영수증출구', '⠻⠠⠍⠨⠪⠶⠰⠯⠈⠍', 'USER'),

    # ── 단독 약자 11자, standalone (제29항) ─────────────────────────────
    ('가', '⠫', 'RULE'),
    ('나', '⠉', 'RULE'),
    ('다', '⠊', 'RULE'),
    ('마', '⠑', 'RULE'),
    ('바', '⠘', 'RULE'),
    ('사', '⠇', 'RULE'),
    ('자', '⠨', 'RULE'),
    ('카', '⠋', 'RULE'),
    ('타', '⠓', 'RULE'),
    ('파', '⠙', 'RULE'),
    ('하', '⠚', 'RULE'),

    # ── 단독 약자 inside multi-syllable words ───────────────────────────
    ('사람', '⠇⠐⠣⠢',  'RULE'),  # 사 + 람 (ㄹ+ㅏ+ㅁ)
    ('가방', '⠫⠘⠣⠶',  'RULE'),  # 가 + 방 (ㅂ+ㅏ+ㅇ); ㅏㅇ 약자 없음
    ('하나', '⠚⠉',     'RULE'),  # 하 + 나 (둘 다 약자)
    ('카카오', '⠋⠋⠥', 'RULE'),  # 카 + 카 + 오; ㅗ = dots 1,3,6 = ⠥

    # ── 라/거/너 등 — 단독 약자 대상 아님 (long form) ───────────────────
    ('라', '⠐⠣', 'RULE'),
    ('거', '⠈⠎', 'RULE'),
    ('너', '⠉⠎', 'RULE'),
    ('도', '⠊⠥', 'RULE'),

    # ── VF 약자 13종, 각 (모음, 종성) → 단일 셀 ─────────────────────────
    ('억', '⠹',  'RULE'),  # ㅇ+ㅓ+ㄱ → ㅇ 생략 + 억 약자
    ('언', '⠾',  'RULE'),
    ('얼', '⠞',  'RULE'),
    ('연', '⠡',  'RULE'),
    ('열', '⠳',  'RULE'),
    ('영', '⠻',  'RULE'),
    ('옥', '⠭',  'RULE'),
    ('온', '⠷',  'RULE'),
    ('옹', '⠿',  'RULE'),
    ('운', '⠛',  'RULE'),
    ('울', '⠯',  'RULE'),  # FIX (3f3faa8): was ⠮
    ('은', '⠽',  'RULE'),  # dots 1,3,4,5,6
    ('인', '⠟',  'RULE'),

    # ── VF 약자 with non-ㅇ initials (consonant + 약자) ─────────────────
    ('먹', '⠑⠹',     'RULE'),  # ㅁ + 억 약자
    ('먼', '⠑⠾',     'RULE'),  # ㅁ + 언
    ('절', '⠨⠞',     'RULE'),  # ㅈ + 얼
    ('편', '⠙⠡',     'RULE'),  # ㅍ + 연
    ('별', '⠘⠳',     'RULE'),  # ㅂ + 열
    ('형', '⠚⠻',     'RULE'),  # ㅎ + 영 (정 은 ㅓ라 적용 X)
    ('녹', '⠉⠭',     'RULE'),  # ㄴ + 옥
    ('손', '⠠⠷',     'RULE'),  # ㅅ + 온
    ('동', '⠊⠿',     'RULE'),  # ㄷ + 옹
    ('운전', '⠛⠨⠾', 'REF'),   # 운 + 전 (ㅈ+언)
    ('출', '⠰⠯',    'USER'),   # ㅊ + 울 약자
    ('근', '⠈⠽',    'RULE'),   # ㄱ + 은 (⠽ = 1,3,4,5,6)
    ('민', '⠑⠟',    'RULE'),   # ㅁ + 인

    # ── 일반 받침 없는 음절 ────────────────────────────────────────────
    ('국', '⠈⠍⠁',  'RULE'),  # ㄱ+ㅜ+ㄱ받침 (받침 ㄱ = dot 1)
    ('밥', '⠘⠣⠃',  'RULE'),  # ㅂ+ㅏ+ㅂ받침
    ('일', '⠕⠂',   'RULE'),  # ㅇ+ㅣ+ㄹ받침
    ('금', '⠈⠪⠢', 'RULE'),  # ㄱ+ㅡ+ㅁ받침

    # ── 복모음 (한국 점자 규정에 단일셀 약자 없는 것은 long form) ─────
    ('와',  '⠧',     'RULE'),  # ㅇ+ㅘ → 단일 셀
    ('의',  '⠪⠕',   'RULE'),  # ㅇ+ㅢ → ㅡ + ㅣ 2셀 (long form, 약자 없음)
    ('외',  '⠽',     'RULE'),  # ㅇ+ㅚ → 단일 셀 (1,3,4,5,6)
    ('워',  '⠍⠎',   'RULE'),  # ㅇ+ㅝ → ㅜ + ㅓ 2셀

    # ── 1줄 문장 ─────────────────────────────────────────────────────
    ('안녕',   '⠣⠒⠉⠻',     'RULE'),
    ('한글',   '⠚⠣⠒⠈⠪⠂',  'RULE'),

    # ── 다음절 약어 (제30항) — fix #1 ───────────────────────────────
    ('그래서',   '⠁⠎',         'RULE'),
    ('그러나',   '⠁⠉',         'RULE'),
    ('그러면',   '⠁⠒',         'RULE'),
    ('그러므로', '⠁⠢',         'RULE'),
    ('그런데',   '⠁⠝',         'RULE'),
    ('그리고',   '⠁⠥',         'RULE'),
    ('그리하여', '⠁⠱',         'RULE'),
    # 약어 + 다른 문자가 이어지는 경우
    ('그래서다', '⠁⠎⠊',       'RULE'),  # 그래서 + 다 약자

    # ── 소수점/쉼표는 number mode 유지 — fix #2 ─────────────────────
    ('10.5',  '⠼⠁⠚⠲⠑',         'RULE'),
    ('3.14',  '⠼⠉⠲⠁⠙',         'RULE'),
    ('1,000', '⠼⠁⠂⠚⠚⠚',        'RULE'),

    # ── 숫자→한글 빈 칸 자동 — fix #3 ──────────────────────────────
    ('3다',    '⠼⠉⠀⠊',           'RULE'),  # 3 + 빈칸 + 다 약자
    ('1가',    '⠼⠁⠀⠫',           'RULE'),
    ('2026년', '⠼⠃⠚⠃⠋⠀⠉⠡',      'RULE'),
    ('5월',    '⠼⠑⠀⠍⠎⠂',         'RULE'),

    # ── 대괄호 — fix #4 ────────────────────────────────────────────
    ('[가]',   '⠈⠦⠫⠴⠈',          'RULE'),  # [ + 가약자 + ]

    # ── ALL CAPS 단축 — fix #5 ─────────────────────────────────────
    ('DNA',    '⠠⠠⠙⠝⠁',          'RULE'),
    ('IT',     '⠠⠠⠊⠞',           'RULE'),
    ('Apple',  '⠠⠁⠏⠏⠇⠑',         'RULE'),  # 첫 글자만 cap — 단일 ⠠
    ('pH',     '⠏⠠⠓',             'RULE'),  # mixed case
    ('aBC',    '⠁⠠⠃⠠⠉',           'RULE'),  # mixed → 단일 cap per upper

    # ── 줄임표 (U+2026) — fix #6 ──────────────────────────────────
    ('…',          '⠲⠲⠲',           'RULE'),  # 한국 점자 규정 제35항
    ('하지만…',     '⠚⠨⠕⠑⠣⠒⠲⠲⠲',  'RULE'),
    # literal '...' 3 periods → same pattern as 줄임표 by happy accident
    ('하지만...',   '⠚⠨⠕⠑⠣⠒⠲⠲⠲',  'RULE'),

    # ── 수학·기호 매핑 — fix #7 ────────────────────────────────────
    ('1/2',        '⠼⠁⠌⠼⠃',        'RULE'),  # 분수 빗금
    ('a/b',        '⠁⠌⠃',           'RULE'),  # 일반 빗금
    ('1+2',        '⠼⠁⠖⠼⠃',        'RULE'),
    ('1=2',        '⠼⠁⠶⠼⠃',        'RULE'),
    ('a@b',        '⠁⠈⠁⠃',          'RULE'),  # 골뱅이 = ⠈⠁
    ('#1',         '⠸⠽⠼⠁',          'RULE'),  # 우물(샵)
    ('5*3',        '⠼⠑⠡⠔⠼⠉',       'RULE'),  # 별표 = ⠡⠔
    ('-273.15℃',  '⠤⠼⠃⠛⠉⠲⠁⠑⠘⠴⠠⠉', 'RULE'),

    # ── 전화/날짜: 하이픈 사이 숫표 유지 — fix #8 ───────────────────
    ('010-1234-5678', '⠼⠚⠁⠚⠤⠁⠃⠉⠙⠤⠑⠋⠛⠓', 'RULE'),
    ('2026-05-18',    '⠼⠃⠚⠃⠋⠤⠚⠑⠤⠁⠓',     'RULE'),
    # 숫자가 아닌 뒤엔 모드 종료 — 하이픈 후 영어
    ('A-1',           '⠠⠁⠤⠼⠁',              'RULE'),
]


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------
GREEN = '\033[32m'
RED = '\033[31m'
DIM = '\033[2m'
RESET = '\033[0m'
BOLD = '\033[1m'


def run():
    use_color = sys.stdout.isatty()
    if not use_color:
        green = red = dim = reset = bold = ''
    else:
        green, red, dim, reset, bold = GREEN, RED, DIM, RESET, BOLD

    by_source = {}
    failures = []
    t0 = time.time()

    for label, want, source in CASES:
        got = cells_to_unicode(text_to_cells(label)[0])
        ok = got == want
        by_source.setdefault(source, [0, 0])
        by_source[source][1] += 1
        if ok:
            by_source[source][0] += 1
            print(f"  {green}✓{reset} [{source}] {label:<10} → {got}")
        else:
            failures.append((label, want, got, source))
            print(f"  {red}✗{reset} [{source}] {label:<10} "
                  f"want {want!r:<18} got {got!r}")

    elapsed = time.time() - t0
    total = len(CASES)
    passed = total - len(failures)

    print()
    print(f"{bold}─── Summary ───{reset}")
    for src in sorted(by_source.keys()):
        ok, n = by_source[src]
        marker = green + '✓' if ok == n else red + '✗'
        print(f"  {marker}{reset}  {src:<6} {ok}/{n}")
    print(f"  {bold}{passed}/{total} passed{reset} "
          f"({dim}{elapsed*1000:.0f} ms{reset})")

    if failures:
        print()
        print(f"{red}{bold}FAIL{reset}: {len(failures)} mismatch(es).")
        print(f"{dim}If a [REF] or [USER] case fails, the conversion is wrong.{reset}")
        print(f"{dim}If a [RULE] case fails, our derivation of 한국 점자 규정 may be off — cross-check on https://t.hi098123.com/braille .{reset}")
        return 1
    print(f"{green}{bold}OK{reset}: all cases pass.")
    return 0


if __name__ == '__main__':
    sys.exit(run())
