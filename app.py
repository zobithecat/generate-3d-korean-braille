# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 zobithecat
# Derivative of https://github.com/benjaminaigner/braillegenerator
#   Copyright (C) Benjamin Aigner (GPL-3.0)
"""Tkinter GUI for the 점자 STL 생성기 (Braille Plate Generator)."""
import atexit
import os
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

from braille_data import text_to_cells, cells_to_unicode, PLATE_THICKNESS
from generator import (
    build_and_save, plate_dimensions,
    DEFAULT_DOT_STYLE, DEFAULT_DOT_RADIUS, DEFAULT_DOT_EMBED, DEFAULT_DOT_FLAT,
    DEFAULT_ENGRAVING, DEFAULT_ENGRAVING_SIZE, DEFAULT_ENGRAVING_DEPTH,
)

PREVIEW_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'preview_stl.py')


class BrailleApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("점자 STL 생성기 - Braille Plate Generator")
        root.geometry("680x820")
        root.minsize(560, 720)

        header = ttk.Frame(root)
        header.pack(fill='x', padx=16, pady=(14, 4))
        ttk.Label(header, text="점자 플레이트 STL 생성기",
                  font=('Helvetica', 16, 'bold')).pack(anchor='w')
        ttk.Label(header,
                  text="한글 · 영문 · 숫자를 입력하면 점자 STL 파일을 생성합니다.",
                  foreground='#555').pack(anchor='w')

        in_frame = ttk.LabelFrame(root, text="텍스트 입력 (Enter 로 줄바꿈)",
                                  padding=8)
        in_frame.pack(fill='both', expand=True, padx=16, pady=8)
        self.text_input = scrolledtext.ScrolledText(
            in_frame, height=6, wrap='word', font=('Helvetica', 13),
        )
        self.text_input.pack(fill='both', expand=True)
        self.text_input.insert('1.0', '안녕하세요\nHello 123')
        self.text_input.bind('<KeyRelease>', lambda _e: self.update_preview())

        opt_frame = ttk.LabelFrame(root, text="프린팅 옵션", padding=8)
        opt_frame.pack(fill='x', padx=16, pady=6)

        self.backplate_var = tk.BooleanVar(value=True)
        self.supports_var = tk.BooleanVar(value=False)
        self.thickness_var = tk.StringVar(value=str(PLATE_THICKNESS))
        self.fillet_var = tk.StringVar(value='1.5')
        self.dot_style_var = tk.StringVar(value=DEFAULT_DOT_STYLE)
        self.dot_radius_var = tk.StringVar(value=str(DEFAULT_DOT_RADIUS))
        self.dot_embed_var = tk.StringVar(value=str(DEFAULT_DOT_EMBED))
        self.dot_flat_enable_var = tk.BooleanVar(value=True)
        self.dot_flat_var = tk.StringVar(value=str(DEFAULT_DOT_FLAT))
        self.engrave_var = tk.BooleanVar(value=DEFAULT_ENGRAVING)
        self.engrave_size_var = tk.StringVar(value=str(DEFAULT_ENGRAVING_SIZE))
        self.engrave_depth_var = tk.StringVar(value=str(DEFAULT_ENGRAVING_DEPTH))

        ttk.Checkbutton(
            opt_frame, text="후면 플레이트 포함 (backplate)",
            variable=self.backplate_var,
        ).grid(row=0, column=0, columnspan=3, sticky='w', pady=2)

        ttk.Checkbutton(
            opt_frame, text="프린팅 지지대 추가 (support cubes)",
            variable=self.supports_var,
        ).grid(row=1, column=0, columnspan=3, sticky='w', pady=2)

        ttk.Label(opt_frame, text="플레이트 두께 (mm):").grid(
            row=2, column=0, sticky='w', pady=2, padx=(0, 6))
        ttk.Entry(opt_frame, width=8,
                  textvariable=self.thickness_var).grid(
            row=2, column=1, sticky='w')
        ttk.Label(opt_frame, text="(권장 1.5 ~ 3.0)",
                  foreground='#777').grid(row=2, column=2, sticky='w',
                                          padx=(6, 0))

        ttk.Label(opt_frame, text="필렛 반경 (mm):").grid(
            row=3, column=0, sticky='w', pady=2, padx=(0, 6))
        ttk.Entry(opt_frame, width=8,
                  textvariable=self.fillet_var).grid(
            row=3, column=1, sticky='w')
        ttk.Label(opt_frame, text="(0 = 샤프, 윗면/옆면만 적용)",
                  foreground='#777').grid(row=3, column=2, sticky='w',
                                          padx=(6, 0))

        ttk.Separator(opt_frame, orient='horizontal').grid(
            row=4, column=0, columnspan=3, sticky='we', pady=6)

        ttk.Label(opt_frame, text="점 모양:").grid(
            row=5, column=0, sticky='w', pady=2, padx=(0, 6))
        style_frame = ttk.Frame(opt_frame)
        style_frame.grid(row=5, column=1, columnspan=2, sticky='w')
        ttk.Radiobutton(style_frame, text="Dome (원기둥+반구, 추천)",
                        variable=self.dot_style_var,
                        value='dome').pack(side='left', padx=(0, 10))
        ttk.Radiobutton(style_frame, text="Sphere (구, 레거시)",
                        variable=self.dot_style_var,
                        value='sphere').pack(side='left')

        ttk.Label(opt_frame, text="점 반경 (mm):").grid(
            row=6, column=0, sticky='w', pady=2, padx=(0, 6))
        ttk.Entry(opt_frame, width=8,
                  textvariable=self.dot_radius_var).grid(
            row=6, column=1, sticky='w')
        ttk.Label(opt_frame, text="(= 가시 높이, 기저 = 2×반경)",
                  foreground='#777').grid(row=6, column=2, sticky='w',
                                          padx=(6, 0))

        ttk.Label(opt_frame, text="플레이트 속 박힘 (mm):").grid(
            row=7, column=0, sticky='w', pady=2, padx=(0, 6))
        ttk.Entry(opt_frame, width=8,
                  textvariable=self.dot_embed_var).grid(
            row=7, column=1, sticky='w')
        ttk.Label(opt_frame, text="(Dome 전용 앵커, 보통 0.15 ~ 0.2)",
                  foreground='#777').grid(row=7, column=2, sticky='w',
                                          padx=(6, 0))

        ttk.Checkbutton(
            opt_frame,
            text="점 상단 평평 깎기 (FDM 노즐 안착용, 뾰족 꼭지 방지)",
            variable=self.dot_flat_enable_var,
        ).grid(row=8, column=0, columnspan=3, sticky='w', pady=2)

        ttk.Label(opt_frame, text="깎기 깊이 (mm):").grid(
            row=9, column=0, sticky='w', pady=2, padx=(0, 6))
        ttk.Entry(opt_frame, width=8,
                  textvariable=self.dot_flat_var).grid(
            row=9, column=1, sticky='w')
        ttk.Label(opt_frame, text="(보통 0.03 ~ 0.08, 자동 클램프: 반경의 50%)",
                  foreground='#777').grid(row=9, column=2, sticky='w',
                                          padx=(6, 0))

        ttk.Separator(opt_frame, orient='horizontal').grid(
            row=10, column=0, columnspan=3, sticky='we', pady=6)

        ttk.Checkbutton(
            opt_frame,
            text="뒷면에 음각 삼각형 (설치 방향 표시, apex = 위쪽)",
            variable=self.engrave_var,
        ).grid(row=11, column=0, columnspan=3, sticky='w', pady=2)

        ttk.Label(opt_frame, text="삼각형 변 길이 (mm):").grid(
            row=12, column=0, sticky='w', pady=2, padx=(0, 6))
        ttk.Entry(opt_frame, width=8,
                  textvariable=self.engrave_size_var).grid(
            row=12, column=1, sticky='w')
        ttk.Label(opt_frame, text="(자동 클램프: plate 의 40%/60%)",
                  foreground='#777').grid(row=12, column=2, sticky='w',
                                          padx=(6, 0))

        ttk.Label(opt_frame, text="음각 깊이 (mm):").grid(
            row=13, column=0, sticky='w', pady=2, padx=(0, 6))
        ttk.Entry(opt_frame, width=8,
                  textvariable=self.engrave_depth_var).grid(
            row=13, column=1, sticky='w')
        ttk.Label(opt_frame, text="(자동 클램프: plate 두께의 40%)",
                  foreground='#777').grid(row=13, column=2, sticky='w',
                                          padx=(6, 0))

        preset_frame = ttk.LabelFrame(
            root, text="프리셋 (Plate · Fillet · Dot 일괄 적용)", padding=6)
        preset_frame.pack(fill='x', padx=16, pady=4)
        ttk.Button(preset_frame, text="A  안정형 (일반용)",
                   command=lambda: self._apply_preset('A')
                   ).pack(side='left', padx=4)
        ttk.Button(preset_frame, text="B  박형 (얇음)",
                   command=lambda: self._apply_preset('B')
                   ).pack(side='left', padx=4)
        ttk.Button(preset_frame, text="C  사이니지 (크고 튼튼)",
                   command=lambda: self._apply_preset('C')
                   ).pack(side='left', padx=4)

        pv_frame = ttk.LabelFrame(root, text="점자 미리보기 (Unicode Braille)",
                                  padding=8)
        pv_frame.pack(fill='x', padx=16, pady=6)
        self.preview = tk.Text(pv_frame, height=4, wrap='none',
                               font=('Menlo', 20), bg='#fafafa',
                               relief='flat')
        self.preview.pack(fill='x')
        self.preview.configure(state='disabled')

        self.info_var = tk.StringVar(value='')
        ttk.Label(root, textvariable=self.info_var,
                  foreground='#444').pack(fill='x', padx=18, pady=(0, 4))

        btn_frame = ttk.Frame(root)
        btn_frame.pack(fill='x', padx=16, pady=(4, 8))
        ttk.Button(btn_frame, text="텍스트 미리보기 새로고침",
                   command=self.update_preview).pack(side='left', padx=4)
        ttk.Button(btn_frame, text="3D 미리보기 (trimesh)",
                   command=self.on_preview_3d).pack(side='left', padx=4)
        ttk.Button(btn_frame, text="STL 파일로 저장...",
                   command=self.on_save).pack(side='left', padx=4)
        ttk.Button(btn_frame, text="종료",
                   command=root.destroy).pack(side='right', padx=4)

        self._preview_procs = []
        self._preview_tmp_files = []
        atexit.register(self._cleanup_preview_resources)

        self.status_var = tk.StringVar(value="준비")
        status = ttk.Label(root, textvariable=self.status_var,
                           relief='sunken', anchor='w', padding=(8, 3))
        status.pack(fill='x', side='bottom')

        self.update_preview()

    def _get_text(self) -> str:
        return self.text_input.get('1.0', 'end-1c')

    def _get_thickness(self) -> float:
        try:
            t = float(self.thickness_var.get())
            if t <= 0:
                raise ValueError
            return t
        except ValueError:
            raise ValueError("플레이트 두께는 0보다 큰 숫자여야 합니다.")

    def _get_fillet(self) -> float:
        try:
            r = float(self.fillet_var.get())
            if r < 0:
                raise ValueError
            return r
        except ValueError:
            raise ValueError("필렛 반경은 0 이상의 숫자여야 합니다.")

    def _get_dot_style(self) -> str:
        s = self.dot_style_var.get()
        if s not in ('dome', 'sphere'):
            raise ValueError("점 모양은 dome 또는 sphere 여야 합니다.")
        return s

    def _get_dot_radius(self) -> float:
        try:
            r = float(self.dot_radius_var.get())
            if r <= 0:
                raise ValueError
            return r
        except ValueError:
            raise ValueError("점 반경은 0보다 큰 숫자여야 합니다.")

    def _get_dot_embed(self) -> float:
        try:
            e = float(self.dot_embed_var.get())
            if e < 0:
                raise ValueError
            return e
        except ValueError:
            raise ValueError("점 박힘 깊이는 0 이상의 숫자여야 합니다.")

    def _get_dot_flat(self) -> float:
        """Apex-truncation depth; returns 0 if the checkbox is off."""
        if not self.dot_flat_enable_var.get():
            return 0.0
        try:
            f = float(self.dot_flat_var.get())
            if f < 0:
                raise ValueError
            return f
        except ValueError:
            raise ValueError("깎기 깊이는 0 이상의 숫자여야 합니다.")

    def _get_engrave_size(self) -> float:
        try:
            s = float(self.engrave_size_var.get())
            if s < 0:
                raise ValueError
            return s
        except ValueError:
            raise ValueError("삼각형 변 길이는 0 이상의 숫자여야 합니다.")

    def _get_engrave_depth(self) -> float:
        try:
            d = float(self.engrave_depth_var.get())
            if d < 0:
                raise ValueError
            return d
        except ValueError:
            raise ValueError("음각 깊이는 0 이상의 숫자여야 합니다.")

    PRESETS = {
        'A': {'label': '안정형',   'thickness': 2.0, 'fillet': 1.5,
              'dot_style': 'dome', 'dot_radius': 0.8,  'dot_embed': 0.15,
              'dot_flat_on': True, 'dot_flat': 0.05,
              'engrave': True,  'engrave_size': 8.0,  'engrave_depth': 0.5},
        'B': {'label': '박형',     'thickness': 1.2, 'fillet': 0.6,
              'dot_style': 'dome', 'dot_radius': 0.75, 'dot_embed': 0.20,
              'dot_flat_on': True, 'dot_flat': 0.04,
              'engrave': True,  'engrave_size': 6.0,  'engrave_depth': 0.3},
        'C': {'label': '사이니지', 'thickness': 2.5, 'fillet': 2.0,
              'dot_style': 'dome', 'dot_radius': 1.0,  'dot_embed': 0.20,
              'dot_flat_on': True, 'dot_flat': 0.08,
              'engrave': True,  'engrave_size': 10.0, 'engrave_depth': 0.7},
    }

    def _apply_preset(self, key: str):
        p = self.PRESETS.get(key)
        if p is None:
            return
        self.thickness_var.set(str(p['thickness']))
        self.fillet_var.set(str(p['fillet']))
        self.dot_style_var.set(p['dot_style'])
        self.dot_radius_var.set(str(p['dot_radius']))
        self.dot_embed_var.set(str(p['dot_embed']))
        self.dot_flat_enable_var.set(p['dot_flat_on'])
        self.dot_flat_var.set(str(p['dot_flat']))
        self.engrave_var.set(p['engrave'])
        self.engrave_size_var.set(str(p['engrave_size']))
        self.engrave_depth_var.set(str(p['engrave_depth']))
        self.status_var.set(f"프리셋 {key} · {p['label']} 적용됨")
        self.update_preview()

    def update_preview(self):
        text = self._get_text()
        lines = text_to_cells(text)

        self.preview.configure(state='normal')
        self.preview.delete('1.0', 'end')
        for i, cells in enumerate(lines):
            self.preview.insert('end', cells_to_unicode(cells))
            if i != len(lines) - 1:
                self.preview.insert('end', '\n')
        self.preview.configure(state='disabled')

        total_cells = sum(len(c) for c in lines)
        try:
            thickness = self._get_thickness()
        except ValueError:
            thickness = PLATE_THICKNESS

        plate_w, plate_h = plate_dimensions(lines)
        self.info_var.set(
            f"셀 {total_cells}개 · {len(lines)}줄  "
            f"→  플레이트 약 {plate_w:.1f} × {plate_h:.1f} × {thickness:.1f} mm"
        )
        self.status_var.set(f"{total_cells}개 점자 셀")

    def _cleanup_preview_resources(self):
        for proc in self._preview_procs:
            if proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:
                    pass
        for path in self._preview_tmp_files:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass

    def on_preview_3d(self):
        text = self._get_text()
        if not text.strip():
            messagebox.showwarning("입력 필요", "텍스트를 먼저 입력하세요.")
            return
        try:
            thickness = self._get_thickness()
            fillet_r = self._get_fillet()
            dot_style = self._get_dot_style()
            dot_radius = self._get_dot_radius()
            dot_embed = self._get_dot_embed()
            dot_flat = self._get_dot_flat()
            engrave = self.engrave_var.get()
            engrave_size = self._get_engrave_size()
            engrave_depth = self._get_engrave_depth()
        except ValueError as e:
            messagebox.showerror("입력 오류", str(e))
            return

        if not os.path.exists(PREVIEW_SCRIPT):
            messagebox.showerror(
                "파일 없음",
                f"미리보기 스크립트를 찾을 수 없습니다:\n{PREVIEW_SCRIPT}",
            )
            return

        fd, tmp_path = tempfile.mkstemp(suffix='.stl',
                                        prefix='braille_preview_')
        os.close(fd)
        self._preview_tmp_files.append(tmp_path)

        self.status_var.set("3D 미리보기 생성 중...")
        self.root.update_idletasks()
        try:
            tri_count, (pw, ph, pt) = build_and_save(
                text, tmp_path,
                plate_thickness=thickness,
                with_backplate=self.backplate_var.get(),
                with_supports=self.supports_var.get(),
                fillet_radius=fillet_r,
                dot_style=dot_style,
                dot_radius=dot_radius,
                dot_embed=dot_embed,
                dot_flat=dot_flat,
                with_engraving=engrave,
                engraving_size=engrave_size,
                engraving_depth=engrave_depth,
            )
        except ImportError as e:
            self.status_var.set("의존성 누락")
            messagebox.showerror("의존성 오류", str(e))
            return
        except Exception as e:
            self.status_var.set("오류")
            messagebox.showerror("생성 실패", f"{type(e).__name__}: {e}")
            return

        title = (f'점자 미리보기  {pw:.1f}×{ph:.1f}×{pt:.1f}mm  '
                 f'(△{tri_count:,})')
        try:
            proc = subprocess.Popen(
                [sys.executable, PREVIEW_SCRIPT, tmp_path, title],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError as e:
            self.status_var.set("실행 실패")
            messagebox.showerror("미리보기 실행 실패", str(e))
            return

        self._preview_procs.append(proc)
        self.status_var.set(
            f"3D 미리보기 창이 열렸습니다 · 삼각형 {tri_count:,}개 · PID {proc.pid}"
        )

    def on_save(self):
        text = self._get_text()
        if not text.strip():
            messagebox.showwarning("입력 필요", "텍스트를 먼저 입력하세요.")
            return

        try:
            thickness = self._get_thickness()
            fillet_r = self._get_fillet()
            dot_style = self._get_dot_style()
            dot_radius = self._get_dot_radius()
            dot_embed = self._get_dot_embed()
            dot_flat = self._get_dot_flat()
            engrave = self.engrave_var.get()
            engrave_size = self._get_engrave_size()
            engrave_depth = self._get_engrave_depth()
        except ValueError as e:
            messagebox.showerror("입력 오류", str(e))
            return

        filename = filedialog.asksaveasfilename(
            defaultextension='.stl',
            filetypes=[('STL file', '*.stl'), ('All files', '*.*')],
            initialfile='braille_plate.stl',
            title='STL 저장 위치 선택',
        )
        if not filename:
            return

        self.status_var.set("STL 생성 중...")
        self.root.update_idletasks()
        try:
            tri_count, (pw, ph, pt) = build_and_save(
                text, filename,
                plate_thickness=thickness,
                with_backplate=self.backplate_var.get(),
                with_supports=self.supports_var.get(),
                fillet_radius=fillet_r,
                dot_style=dot_style,
                dot_radius=dot_radius,
                dot_embed=dot_embed,
                dot_flat=dot_flat,
                with_engraving=engrave,
                engraving_size=engrave_size,
                engraving_depth=engrave_depth,
            )
        except ImportError as e:
            self.status_var.set("의존성 누락")
            messagebox.showerror("의존성 오류", str(e))
            return
        except Exception as e:
            self.status_var.set("오류")
            messagebox.showerror("저장 실패",
                                 f"{type(e).__name__}: {e}")
            return

        self.status_var.set(
            f"저장 완료: {filename}  |  삼각형 {tri_count:,}개"
        )
        messagebox.showinfo(
            "STL 저장 완료",
            (f"저장 경로:\n{filename}\n\n"
             f"플레이트: {pw:.1f} × {ph:.1f} × {pt:.1f} mm\n"
             f"삼각형: {tri_count:,} 개"),
        )


def main():
    root = tk.Tk()
    try:
        style = ttk.Style(root)
        themes = style.theme_names()
        for preferred in ('aqua', 'clam', 'vista'):
            if preferred in themes:
                style.theme_use(preferred)
                break
    except tk.TclError:
        pass
    BrailleApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
