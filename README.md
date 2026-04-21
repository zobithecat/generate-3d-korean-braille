# 점자 플레이트 STL 생성기 (Braille Plate STL Generator)

한글, 영문, 숫자 텍스트를 입력하면 3D 프린터로 출력 가능한 **점자 플레이트 STL** 파일을 생성하는 Python GUI 앱입니다.

![원본 demo](braille1.png)

## 주요 기능

- **한글 · 영문 · 숫자** 입력 → 자동 점자 변환
- **필렛된 백플레이트** — 윗면/옆 모서리는 라운드, 바닥면은 평면 유지 (프린터 배드 접착)
- **프린팅 지지대** 토글 (얇은 플레이트가 프린팅 중 휘지 않도록)
- **Tkinter GUI** + Unicode 점자 (U+2800 ~ U+28FF) 실시간 미리보기
- **trimesh 3D 뷰어** 로 저장 전 STL 미리보기 (별도 프로세스, GUI 안 멈춤)
- **바이너리 STL** 출력 (numpy-stl)

## 설치

Python 3.10+ 권장.

```bash
pip install -r requirements.txt
```

`requirements.txt` 내용:
- `numpy`, `numpy-stl` — 메시 연산 & STL 직렬화
- `trimesh[easy]` + `pyglet<2` — 3D 미리보기 뷰어
  - (trimesh 4.x 내장 뷰어가 아직 pyglet 2.x 미지원이라 1.5 계열로 핀)

## 실행

```bash
python3 app.py
```

1. 텍스트 입력란에 원하는 문구 입력 (Enter 로 줄바꿈)
2. 옵션 조정 — 플레이트 두께 (기본 2.0 mm), 필렛 반경 (기본 1.0 mm)
3. **3D 미리보기** 로 모양 확인 → **STL 파일로 저장**

---

## 개발 배경

이 프로젝트는 [**benjaminaigner/braillegenerator**](https://github.com/benjaminaigner/braillegenerator) 의 `braille.jscad` (OpenJSCAD) 파일을 참조하여 **한글 점자 지원을 추가**하고 **Python + Tkinter GUI 로 포팅**한 파생 저작물입니다.

### 원본에서 계승한 것

- 점자 셀의 기하 상수 (점 지름 1.44 mm, 셀 내 점 간격 2.5 mm, 문자 간격 6 mm, 줄 간격 10.8 mm, 플레이트 두께 2 mm)
- 2 mm 백플레이트 + 인쇄 지지대 구조
- 문자 → 점자 비트맵 매핑의 기본 아이디어

### 새로 구현한 것

#### 1. 한국어 점자 (국립국어원 2017 한국 점자 규정)

`braille_data.py`:

- **초성 19자** (`ㄱ~ㅎ`, 쌍자음 포함) — 쌍자음은 `ㅅ`(dot 6) 프리픽스 + 평자음 2셀
- **중성 21자** — `ㅘ`, `ㅙ`, `ㅝ`, `ㅞ`, `ㅟ`, `ㅢ`, `ㅒ` 등 복모음은 2셀
- **종성 28자** — 겹받침 (`ㄺ`, `ㄻ`, `ㄼ`, `ㄽ`, `ㄾ`, `ㄿ`, `ㅀ`, `ㅄ`, `ㄳ`, `ㄵ`, `ㄶ`) 모두 2셀 분해
- Hangul Syllables (U+AC00 ~ U+D7A3) 자동 **초성+중성+종성** 분해
- `ㅇ` 초성 생략 규칙 적용

#### 2. 영문 / 숫자

- Grade-1 영문 점자 (a-z)
- 숫자 prefix `⠼` (dots 3-4-5-6) + letter sign `⠰` (dots 5-6) 전환
- 대문자 prefix `⠠` (dot 6)
- 기본 문장부호 (`. , ? ! ; : ' - ( ) "`)

#### 3. Python 메시 파이프라인 (`generator.py`)

- 순수 `numpy` 로 UV sphere / axis-aligned box 메시 생성
- CSG 불리언 연산 없이 **구 + 플레이트 단순 결합** → 대부분의 슬라이서가 오버랩 자동 처리
- `numpy-stl` 로 바이너리 STL 직렬화

#### 4. 필렛 백플레이트 (사용자 요청으로 추가)

3D 프린팅에 친화적인 "위·옆은 둥글게, 바닥은 평면" 플레이트:

- **스켈레톤 사각형** `[r, W-r] × [r, H-r]` 을 기준으로 높이별 오프셋
- 수직 영역 `z ∈ [-t, -r]`: 외측 오프셋 `d = r` 고정 → **수직 모서리 4개** 라운드
- 상단 필렛 `z ∈ [-r, 0]`: `d(z) = √(r² - (z+r)²)` 로 수축 → **윗면 모서리 4개** 1/4 원호
- 바닥면 `z = -t`: 라운드 사각형이지만 **측벽과는 90° 샤프** 유지 → 프린터 배드 접착면 보장
- `r` 자동 클램프: `min(r, W/2, H/2, t) − eps`
- 링 기반 스윕 + 팬 트라이앵글레이션 → `trimesh.is_watertight == True` 보장

#### 5. Tkinter GUI (`app.py`)

- 텍스트 입력 + 옵션 위젯 (백플레이트, 지지대, 두께, 필렛 반경)
- 입력 즉시 Unicode 점자 미리보기 갱신
- 플레이트 최종 치수 실시간 표시

#### 6. 3D 뷰어 (`preview_stl.py`)

- **서브프로세스**로 실행 → Tkinter 메인 루프 블로킹 없음 (특히 macOS)
- `trimesh.Scene.show()` + pyglet 뷰어
- 임시 STL 파일 생성 → 프로세스에 경로 전달 → 앱 종료 시 `atexit` 로 정리

---

## 아키텍처

```
app.py                    Tkinter GUI (엔트리 포인트)
 ├── braille_data.py       점자 매핑, Hangul 분해, 텍스트 → 셀
 ├── generator.py          셀 → 3D 메시 → STL 파일
 │     └── numpy-stl
 └── preview_stl.py        trimesh + pyglet 뷰어 (subprocess)
```

## 지오메트리 상수

| 항목 | 기본값 | 출처 |
|---|---|---|
| 점 지름 | 1.44 mm | 점자 표준 |
| 셀 내 점 간격 | 2.5 mm | `braille.jscad` |
| 문자 간격 | 6.0 mm | `braille.jscad` |
| 줄 간격 | 10.8 mm | `braille.jscad` |
| 플레이트 두께 | 2.0 mm | `braille.jscad` |
| 플레이트 여백 | 2.0 mm | (새로 추가) |
| 필렛 반경 | 1.0 mm | (새로 추가) |
| UV sphere 해상도 | lat 6 × lon 10 | (새로 추가) |

## 파일 구조

```
.
├── app.py             # Tkinter GUI
├── braille_data.py    # 점자 매핑 + Hangul 분해
├── generator.py       # 메시 생성 + STL 저장
├── preview_stl.py     # trimesh 뷰어 (subprocess)
├── requirements.txt
├── braille.jscad      # 원본 OpenJSCAD 스크립트 (참조용)
├── braille1.png       # 원본 데모 이미지
├── LICENSE            # GPL-3.0 전문
└── README.md
```

---

## 라이선스 & Attribution

본 프로젝트는 **GPL-3.0-or-later** 로 배포됩니다. 상세는 [LICENSE](LICENSE) 참조.

### 원저작물 (Upstream)

본 프로젝트는 다음 저작물의 **파생 저작물 (derivative work)** 입니다:

| 항목 | 정보 |
|---|---|
| 원본 프로젝트 | [benjaminaigner/braillegenerator](https://github.com/benjaminaigner/braillegenerator) |
| 원저작자 | Benjamin Aigner |
| 원본 라이선스 | GPL-3.0 |
| 참조한 파일 | `braille.jscad`, `braille1.png` |

원본은 `braille.jscad` 만 존재하는 OpenJSCAD 스크립트였으며, 본 포트에서는:
- 독일어 점자 대신 **한글/영문/숫자** 매핑 사용
- OpenJSCAD 대신 **순수 Python + numpy-stl** 파이프라인
- **GUI · 3D 미리보기 · 필렛 플레이트** 추가

GPL-3.0 의 copyleft 조항에 따라 본 파생 저작물도 동일하게 GPL-3.0 으로 배포됩니다. 소스 수정/재배포는 자유이며, 재배포 시 동일 라이선스 유지와 소스 공개 의무가 있습니다.

### Python 파일 저작권 표기

각 `.py` 파일 상단에 SPDX 식별자와 copyright notice 를 포함합니다:

```python
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 zobithecat
# Derivative of https://github.com/benjaminaigner/braillegenerator
#   Copyright (C) Benjamin Aigner (GPL-3.0)
```
