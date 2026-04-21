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
from generator import build_and_save, plate_dimensions

PREVIEW_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'preview_stl.py')


class BrailleApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("점자 STL 생성기 - Braille Plate Generator")
        root.geometry("660x680")
        root.minsize(540, 600)

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
        self.supports_var = tk.BooleanVar(value=True)
        self.thickness_var = tk.StringVar(value=str(PLATE_THICKNESS))
        self.fillet_var = tk.StringVar(value='1.0')

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
