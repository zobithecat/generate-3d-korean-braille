#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Diagnostic dump for the user-supplied 40-case edge corpus.

Runs each input through the current parser and prints (label, output).
No expected values — this is a *probe*, not a pass/fail test.

After review against https://t.hi098123.com/braille these get promoted to
tests/smoke_braille.py with the verified expected outputs.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from braille_data import text_to_cells, cells_to_unicode  # noqa: E402

CATEGORIES = [
    ("1. 약자 예외 / 자음 결합", [
        '성경책과 정원',
        '청렴결백',
        '쏭아지',
        '벽면과 편지',
        '령역과 명령',
        '션샤인',
        '쩍 갈라지다',
        '깟씨와 짠맛',
        '영영 오지 않았다',
        '엉덩이',
    ]),
    ("2. 숫자-한글 모드 / 숫표 효력 범위", [
        '제3세대',
        '17년 동안',
        '1가 2나 3다',
        '12시간 34분 56초',
        '-273.15℃',
        '3.141592...',
        '1/2 + 2/3 = 7/6',
        '010-1234-5678',
    ]),
    ("3. 로마자 대소문자 / 하이브리드", [
        'GitHub Repository',
        'OpenAI의 ChatGPT-4o',
        'https://vendit.co.kr',
        'test@example.com',
        'Windows 11 Pro',
        '5G 네트워크',
        'USB-C 타입',
        'IoT 플랫폼인 SmartMesh',
    ]),
    ("4. 부호 중첩 / 이중 구조", [
        '"그가 말했다. \'절대 안 돼!\'라고."',
        '[필독] (주의) 강조',
        '무궁화꽃이 피었습니다...!?',
        '1등, 2등, 3등...',
        '@운영자, #해시태그',
        '(단글/영어)',
    ]),
    ("5. 희귀 음절 / 극한 겹받침", [
        '붸붸 고인 선',
        '똠양꿍과 뜀틀',
        '쀍 기차',
        '휑한 들판',
        '듸뎌 도달했다',
        '읊고 읊는 시',
        '값지다',
        '가나다라1234abcd',
    ]),
]


def main():
    total = 0
    for cat, items in CATEGORIES:
        print(f"\n=== {cat} ===")
        for s in items:
            total += 1
            try:
                cells = text_to_cells(s)[0]
                out = cells_to_unicode(cells)
                nc = len(cells)
                print(f"  [{total:02d}] {s!r:<40} → {out}   ({nc} cells)")
            except Exception as e:
                print(f"  [{total:02d}] {s!r:<40} → !! ERROR: {type(e).__name__}: {e}")


if __name__ == '__main__':
    main()
