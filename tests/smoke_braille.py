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
    ('가방', '⠫⠘⠶',    'RULE'),  # 가 + 방 — 제13항: 방 = 바약자(⠘) + ㅇ받침
    ('하나', '⠚⠉',     'RULE'),  # 하 + 나 (둘 다 약자)
    ('카카오', '⠋⠋⠣⠥', 'RULE'),  # 제17항: 두 번째 카는 ㅏ 살림 (오가 ㅇ초성)

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
    ('은', '⠵',  'RULE'),  # 점 1,3,5,6 — PDF 해설서 line 1006 '은빛 z^o2' 확정
    ('을', '⠮',  'RULE'),  # 14번째 VF 약자 (제15항) — 신규
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
    ('근', '⠈⠵',    'RULE'),   # ㄱ + 은 (⠵ = 1,3,5,6) — PDF 정정
    ('글', '⠈⠮',    'RULE'),   # ㄱ + 을 — 신규
    ('민', '⠑⠟',    'RULE'),   # ㅁ + 인

    # ── 일반 받침 없는 음절 ────────────────────────────────────────────
    ('국', '⠈⠍⠁',  'RULE'),  # ㄱ+ㅜ+ㄱ받침 (받침 ㄱ = dot 1)
    ('밥', '⠘⠃',    'RULE'),  # 제13항: 바약자(⠘) + ㅂ받침
    ('일', '⠕⠂',   'RULE'),  # ㅇ+ㅣ+ㄹ받침
    ('금', '⠈⠪⠢', 'RULE'),  # ㄱ+ㅡ+ㅁ받침

    # ── 복모음 (한국 점자 규정에 단일셀 약자 없는 것은 long form) ─────
    ('와',  '⠧',     'RULE'),  # ㅇ+ㅘ → 단일 셀
    ('의',  '⠪⠕',   'RULE'),  # ㅇ+ㅢ → ㅡ + ㅣ 2셀 (long form, 약자 없음)
    ('외',  '⠽',     'RULE'),  # ㅇ+ㅚ → 단일 셀 (1,3,4,5,6)
    ('워',  '⠍⠎',   'RULE'),  # ㅇ+ㅝ → ㅜ + ㅓ 2셀

    # ── 1줄 문장 ─────────────────────────────────────────────────────
    ('안녕',   '⠣⠒⠉⠻',     'RULE'),
    ('한글',   '⠚⠒⠈⠮',      'RULE'),   # 제13항: 한 = 하약자+ㄴ받침 / 글 = ㄱ+을약자

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
    ('[가]',   '⠦⠆⠫⠰⠴',          'RULE'),  # [ + 가약자 + ] (제56항)

    # ── ALL CAPS 단축 — fix #5 ─────────────────────────────────────
    ('DNA',    '⠠⠠⠙⠝⠁',          'RULE'),
    ('IT',     '⠠⠠⠊⠞',           'RULE'),
    ('Apple',  '⠠⠁⠏⠏⠇⠑',         'RULE'),  # 첫 글자만 cap — 단일 ⠠
    ('pH',     '⠏⠠⠓',             'RULE'),  # mixed case
    ('aBC',    '⠁⠠⠃⠠⠉',           'RULE'),  # mixed → 단일 cap per upper

    # ── 줄임표 (U+2026) — fix #6 ──────────────────────────────────
    ('…',          '⠲⠲⠲',           'RULE'),  # 한국 점자 규정 제35항
    ('하지만…',     '⠚⠨⠕⠑⠒⠲⠲⠲',    'RULE'),  # 만 = 마약자+ㄴ받침 (제13항)
    # literal '...' 3 periods → same pattern as 줄임표 by happy accident
    ('하지만...',   '⠚⠨⠕⠑⠒⠲⠲⠲',    'RULE'),

    # ── 수학·기호 매핑 — PDF 직접 검증 ────────────────────────────
    # `/` 빗금: 한글 본문 = ⠸⠌ (제51항), 로마자 사이 UEB = ⠌
    ('1/2',        '⠼⠁⠸⠌⠼⠃',      'RULE'),  # 숫자 사이 → 한글 본문 룰
    ('a/b',        '⠁⠌⠃',           'RULE'),  # 로마자 사이 → UEB
    # `+`, `=`: 한글 컨텍스트 = 제73항 수학 기호
    ('1+2',        '⠼⠁⠢⠼⠃',        'RULE'),  # 덧셈 = ⠢ (점 2,6)
    ('1=2',        '⠼⠁⠒⠒⠼⠃',      'RULE'),  # 등호 = ⠒⠒ (2 cells)
    ('a@b',        '⠁⠈⠁⠃',          'RULE'),  # 골뱅이 = ⠈⠁
    ('#1',         '⠸⠹⠼⠁',          'RULE'),  # 우물 ⠸⠹ (그 밖의 기호)
    ('5*3',        '⠼⠑⠔⠔⠼⠉',       'RULE'),  # 별표 = ⠔⠔ (제68항)
    ('-273.15℃',  '⠤⠼⠃⠛⠉⠲⠁⠑⠴⠙⠠⠉', 'RULE'),  # ℃ = ⠴⠙⠠⠉

    # ── 전화/날짜: 하이픈 사이 숫표 유지 — fix #8 ───────────────────
    ('010-1234-5678', '⠼⠚⠁⠚⠤⠁⠃⠉⠙⠤⠑⠋⠛⠓', 'RULE'),
    ('2026-05-18',    '⠼⠃⠚⠃⠋⠤⠚⠑⠤⠁⠓',     'RULE'),
    # 숫자가 아닌 뒤엔 모드 종료 — 하이픈 후 영어
    ('A-1',           '⠠⠁⠤⠼⠁',              'RULE'),

    # ── Stage 1: 국립국어원 한국 점자 규정 PDF 직접 검증 케이스 ─────
    # 제15항 — 14번째 약자 '을' (ㅡ,ㄹ) + 겹받침 첫 자음 매칭 룰
    ('은빛',   '⠵⠘⠕⠆',       'RULE'),    # 해설서 line 1006
    ('가을',   '⠫⠮',           'RULE'),    # 해설서 line 1006
    ('긁다',   '⠈⠮⠁⠊',       'RULE'),    # 해설서 line 1185 (ㄺ 겹받침)
    ('늙다',   '⠉⠮⠁⠊',       'RULE'),    # 해설서 line 1185
    ('읊다',   '⠮⠲⠊',         'RULE'),    # 해설서 line 1185 (ㄿ 겹받침)
    ('끊다',   '⠠⠈⠵⠴⠊',     'RULE'),    # 해설서 line 1185 (ㄶ 겹받침 + 은)
    ('큰언니', '⠋⠵⠾⠉⠕',     'RULE'),    # 해설서 line 1185
    # 제16항 — 성/정/청 특례 (ㅅㅈㅊ + ㅓ + ㅇ → 영 약자)
    ('성가',   '⠠⠻⠫',         'RULE'),    # 해설서 line 1240
    ('정성',   '⠨⠻⠠⠻',       'RULE'),    # 해설서 line 1240
    ('청년',   '⠰⠻⠉⠡',       'RULE'),    # 해설서 line 1240
    ('말썽',   '⠑⠂⠠⠠⠻',    'RULE'),    # 해설서 line 1240 (말=마약자+ㄹ받침)
    # 제16항 반례 — ㅅㅈㅊ + ㅕ + ㅇ → 풀어쓰기 (영 약자 차단)
    ('셩',     '⠠⠱⠶',         'RULE'),    # 해설서 line 1268 (외래어)
    # 제16항 반례 — 다른 초성 + ㅓㅇ → 풀어쓰기 (영 약자 적용 X)
    ('덩',     '⠊⠎⠶',         'RULE'),    # 해설서 line 1273
    ('컹',     '⠋⠎⠶',         'RULE'),    # 해설서 line 1273
    # 제16항 정방향 — 다른 초성 + ㅕㅇ → 영 약자 정상 적용
    ('뎡',     '⠊⠻',           'RULE'),    # 해설서 line 1273

    # ── 제13항 — 단독 약자 + 받침 (ㅏ 생략 + 약자 점형 + 받침) ────────
    ('맞',     '⠑⠅',           'RULE'),    # 마약자 + ㅈ받침 (사용자 친구 친절 정정)
    ('갈',     '⠫⠂',           'RULE'),    # 가약자 + ㄹ받침
    ('박',     '⠘⠁',           'RULE'),    # 바약자 + ㄱ받침
    ('답',     '⠊⠃',           'RULE'),    # 다약자 + ㅂ받침
    ('한',     '⠚⠒',           'RULE'),    # 하약자 + ㄴ받침
    ('강',     '⠫⠶',           'RULE'),    # 가약자 + ㅇ받침
    ('살',     '⠇⠂',           'RULE'),    # 사약자 + ㄹ받침
    ('잡',     '⠨⠃',           'RULE'),    # 자약자 + ㅂ받침
    ('맞게',   '⠑⠅⠈⠝',         'RULE'),    # 맞 약자 + 게
    ('마당',   '⠑⠊⠶',           'RULE'),    # 해설서 line 935 (마 + 다약자 + ㅇ받침)

    # ── 제14항 — 된소리 단독 약자 (까/싸/깟) ───────────────────────
    ('까',     '⠠⠫',           'RULE'),    # 된소리표 + 가약자
    ('싸',     '⠠⠇',           'RULE'),    # 된소리표 + 사약자
    ('깟',     '⠠⠫⠄',          'RULE'),    # 된소리 가약자 + ㅅ받침
    ('쌌',     '⠠⠇⠌',          'RULE'),    # 된소리 사약자 + ㅆ받침

    # ── 제17항 — 단독 약자 + 다음 음절 ㅇ초성 → ㅏ 살림 ────────────
    ('다음',   '⠊⠣⠪⠢',         'RULE'),    # 해설서 line 1118
    ('마음',   '⠑⠣⠪⠢',         'RULE'),    # 해설서 line 1118
    ('하얀',   '⠚⠣⠜⠒',         'RULE'),    # 해설서 line 1118
    # 가/사는 제17항 예외 없음 — 다음 음절 ㅇ초성이어도 약자 사용
    ('사이',   '⠇⠕',           'RULE'),
    # 사용자 친구 정정 케이스 (full sentence)
    ('신분증을 홈에 맞게 올려주세요',
     '⠠⠟⠘⠛⠨⠪⠶⠮⠀⠚⠥⠢⠝⠀⠑⠅⠈⠝⠀⠥⠂⠐⠱⠨⠍⠠⠝⠬',
     'USER'),

    # ── Stage 2: 한글 점자 문장 부호 컨텍스트 의존 (제32항/44~67항) ──
    # 한글 본문 컨텍스트 (default) — Korean 매핑
    ('가,나',   '⠫⠐⠉',         'RULE'),    # 쉼표 한글본문 = ⠐
    ('가:나',   '⠫⠐⠂⠉',       'RULE'),    # 쌍점 = ⠐⠂ (2셀)
    ('가;나',   '⠫⠰⠆⠉',       'RULE'),    # 쌍반점 = ⠰⠆ (2셀)
    ('(가)',    '⠦⠄⠫⠠⠴',     'RULE'),    # 소괄호 (제54항)
    ('{가}',    '⠦⠂⠫⠐⠴',     'RULE'),    # 중괄호 (제55항)
    ('가·나',   '⠫⠐⠆⠉',       'RULE'),    # 가운뎃점 (제48항)
    ('가~나',   '⠫⠤⠤⠉',       'RULE'),    # 물결표 (제61항)
    ('*가',     '⠔⠔⠫',         'RULE'),    # 별표 (제68항)
    ('5%',      '⠼⠑⠴⠏',       'RULE'),    # 백분율 (제31항)
    ('5°',      '⠼⠑⠴⠙',       'RULE'),    # 도 (제31항)

    # 로마자 컨텍스트 — UEB 매핑 (제32항 [붙임])
    ('a,b',     '⠁⠂⠃',         'RULE'),    # UEB 쉼표 = ⠂
    ('a:b',     '⠁⠒⠃',         'RULE'),    # UEB 쌍점 = ⠒ (1셀)
    ('a;b',     '⠁⠆⠃',         'RULE'),    # UEB 쌍반점 = ⠆ (1셀)
    # ※ (a) 같이 한 단어 안에서 컨텍스트가 한글→로마자로 전환되는 케이스는
    #    여는/닫는 괄호의 점형이 비대칭이 됨 (`⠦⠄` + `⠾`). 한국 점자 규정도
    #    이런 혼합 케이스의 처리를 명시하지 않음 — 페어 매칭 로직은 별도 이슈.

    # ── Stage 3: 화폐·외래 부호 (제72항 등) ────────────────────────
    ('₩1000',  '⠈⠺⠼⠁⠚⠚⠚',    'RULE'),    # 원 = ⠈⠺
    ('$50',    '⠈⠙⠼⠑⠚',        'RULE'),    # 달러 = ⠈⠙
    ('€100',   '⠈⠑⠼⠁⠚⠚',       'RULE'),    # 유로 = ⠈⠑
    ('a&b',    '⠁⠈⠯⠃',          'RULE'),    # 앰퍼샌드 = ⠈⠯
    ('※주의',  '⠸⠔⠨⠍⠪⠕',       'RULE'),    # 참고표 = ⠸⠔ ; 주의 = ㅈ+ㅜ + ㅇ+ㅢ(ㅡ+ㅣ)
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
