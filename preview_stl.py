# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 zobithecat
# Derivative of https://github.com/benjaminaigner/braillegenerator
#   Copyright (C) Benjamin Aigner (GPL-3.0)
"""Standalone trimesh viewer. Launched as a subprocess from app.py.

Usage: python preview_stl.py <path.stl> [window_title]

Viewer keyboard shortcuts (pyglet-based):
    mouse drag   rotate
    mouse wheel  zoom
    w            toggle wireframe
    c            toggle back-face culling
    g            toggle grid
    a            toggle axes
    f            fullscreen
    q            quit
"""
import sys


def main():
    if len(sys.argv) < 2:
        print("usage: preview_stl.py <path.stl> [window_title]",
              file=sys.stderr)
        sys.exit(2)

    stl_path = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else '점자 플레이트 미리보기'

    try:
        import trimesh
    except ImportError:
        print("trimesh 패키지가 필요합니다. 설치: pip install 'trimesh[easy]'",
              file=sys.stderr)
        sys.exit(3)

    mesh = trimesh.load(stl_path, force='mesh')
    if mesh is None or len(mesh.faces) == 0:
        print(f"빈 메시입니다: {stl_path}", file=sys.stderr)
        sys.exit(1)

    # Beige/gold color so the braille dots are clearly visible.
    mesh.visual.face_colors = [217, 184, 89, 255]

    scene = trimesh.Scene(mesh)

    try:
        scene.show(
            caption=title,
            resolution=(960, 720),
            flags={'cull': False, 'axis': True, 'grid': True},
        )
    except Exception as e:
        print(f"viewer error: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(4)


if __name__ == '__main__':
    main()
