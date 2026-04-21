# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 zobithecat
# Derivative of https://github.com/benjaminaigner/braillegenerator
#   Copyright (C) Benjamin Aigner (GPL-3.0)
"""STL mesh construction for a braille plate.

Coordinate system:
    x: horizontal (character direction, left -> right)
    y: vertical   (line direction, top -> bottom)
    z: out of the plate (dots rise above z = 0)
"""

import numpy as np

from braille_data import (
    DOT_RADIUS, PLATE_THICKNESS, DOT_SPACING, CHAR_WIDTH, LINE_HEIGHT,
    MARGIN, DOT_OFFSETS, text_to_cells,
)


# ---------------------------------------------------------------------------
# Primitive meshes
# ---------------------------------------------------------------------------
def uv_sphere(center, radius, lat_segs=6, lon_segs=10):
    """UV sphere with outward-facing triangles."""
    cx, cy, cz = center
    vertices = [[cx, cy, cz + radius]]
    ring_starts = []

    for lat in range(1, lat_segs):
        phi = np.pi * lat / lat_segs
        z = cz + radius * np.cos(phi)
        r = radius * np.sin(phi)
        ring_starts.append(len(vertices))
        for lon in range(lon_segs):
            theta = 2 * np.pi * lon / lon_segs
            vertices.append([
                cx + r * np.cos(theta),
                cy + r * np.sin(theta),
                z,
            ])

    south_idx = len(vertices)
    vertices.append([cx, cy, cz - radius])

    faces = []

    first_ring = ring_starts[0]
    for lon in range(lon_segs):
        nxt = (lon + 1) % lon_segs
        faces.append([0, first_ring + lon, first_ring + nxt])

    for i in range(len(ring_starts) - 1):
        rs0 = ring_starts[i]
        rs1 = ring_starts[i + 1]
        for lon in range(lon_segs):
            nxt = (lon + 1) % lon_segs
            a = rs0 + lon
            b = rs0 + nxt
            c = rs1 + nxt
            d = rs1 + lon
            faces.append([a, d, c])
            faces.append([a, c, b])

    last_ring = ring_starts[-1]
    for lon in range(lon_segs):
        nxt = (lon + 1) % lon_segs
        faces.append([south_idx, last_ring + nxt, last_ring + lon])

    return (np.asarray(vertices, dtype=np.float64),
            np.asarray(faces, dtype=np.int64))


def dome(center, radius, embed_depth, lat_segs=4, lon_segs=10):
    """Cylinder + upper hemisphere joined at z = cz.

    center = (cx, cy, cz): cz is the plate surface (hemisphere equator).
    The cylinder extends downward to cz - embed_depth (anchored inside
    the plate); the upper hemisphere (radius ``radius``) sits on top.
    Outward-facing triangles.
    """
    cx, cy, cz = center

    vertices = [[cx, cy, cz + radius]]     # apex = idx 0
    ring_indices = []
    for lat in range(1, lat_segs + 1):
        phi = (np.pi / 2) * lat / lat_segs
        ring_r = radius * np.sin(phi)
        ring_z = cz + radius * np.cos(phi)
        ring_indices.append(len(vertices))
        for lon in range(lon_segs):
            theta = 2 * np.pi * lon / lon_segs
            vertices.append([
                cx + ring_r * np.cos(theta),
                cy + ring_r * np.sin(theta),
                ring_z,
            ])

    cyl_bot_start = len(vertices)
    for lon in range(lon_segs):
        theta = 2 * np.pi * lon / lon_segs
        vertices.append([
            cx + radius * np.cos(theta),
            cy + radius * np.sin(theta),
            cz - embed_depth,
        ])
    cyl_bot_center = len(vertices)
    vertices.append([cx, cy, cz - embed_depth])

    faces = []
    first_ring = ring_indices[0]
    for lon in range(lon_segs):
        nxt = (lon + 1) % lon_segs
        faces.append([0, first_ring + lon, first_ring + nxt])

    for i in range(len(ring_indices) - 1):
        rs0 = ring_indices[i]
        rs1 = ring_indices[i + 1]
        for lon in range(lon_segs):
            nxt = (lon + 1) % lon_segs
            a = rs0 + lon
            b = rs0 + nxt
            c = rs1 + nxt
            d = rs1 + lon
            faces.append([a, d, c])
            faces.append([a, c, b])

    eq = ring_indices[-1]
    for lon in range(lon_segs):
        nxt = (lon + 1) % lon_segs
        a = eq + lon
        b = eq + nxt
        c = cyl_bot_start + nxt
        d = cyl_bot_start + lon
        faces.append([a, d, c])
        faces.append([a, c, b])

    for lon in range(lon_segs):
        nxt = (lon + 1) % lon_segs
        faces.append([cyl_bot_center,
                      cyl_bot_start + nxt,
                      cyl_bot_start + lon])

    return (np.asarray(vertices, dtype=np.float64),
            np.asarray(faces, dtype=np.int64))


def axis_box(x0, y0, z0, x1, y1, z1):
    v = np.array([
        [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
        [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1],
    ], dtype=np.float64)
    f = np.array([
        [0, 2, 1], [0, 3, 2],
        [4, 5, 6], [4, 6, 7],
        [0, 1, 5], [0, 5, 4],
        [3, 7, 6], [3, 6, 2],
        [0, 4, 7], [0, 7, 3],
        [1, 2, 6], [1, 6, 5],
    ], dtype=np.int64)
    return v, f


def combine(meshes):
    if not meshes:
        return (np.zeros((0, 3), dtype=np.float64),
                np.zeros((0, 3), dtype=np.int64))
    vs, fs, offset = [], [], 0
    for v, f in meshes:
        vs.append(v)
        fs.append(f + offset)
        offset += len(v)
    return np.concatenate(vs), np.concatenate(fs)


# ---------------------------------------------------------------------------
# Filleted plate
# ---------------------------------------------------------------------------
def _rounded_outline(W, H, r_skeleton, d, n_corner):
    """Return (M, 3) points walking CCW (viewed from +Z) around a rounded
    rectangle.

    The skeleton is the inner rectangle [r, W-r] x [r, H-r] offset outward by
    ``d`` in the XY plane, with corner arcs of radius ``d``. The z coordinate
    is filled in by the caller.
    """
    pts = []
    corners = [
        (W - r_skeleton, r_skeleton,     -np.pi / 2, 0.0),
        (W - r_skeleton, H - r_skeleton,  0.0,       np.pi / 2),
        (r_skeleton,     H - r_skeleton,  np.pi / 2, np.pi),
        (r_skeleton,     r_skeleton,      np.pi,     3 * np.pi / 2),
    ]
    for cx, cy, a0, a1 in corners:
        for i in range(n_corner + 1):
            ang = a0 + (a1 - a0) * (i / n_corner)
            pts.append([cx + d * np.cos(ang), cy + d * np.sin(ang), 0.0])
    return np.asarray(pts, dtype=np.float64)


def filleted_plate(W, H, t, r, n_corner=6, n_fillet=6, eps=1e-4):
    """Build a plate occupying z in [-t, 0] with:

    - 4 top edges (top face perimeter)    filleted with radius r
    - 4 vertical corner edges             filleted with radius r
    - 4 bottom edges                      kept sharp (flat bottom)

    Falls back to a plain axis-aligned box when r <= eps.
    Returns (vertices, faces).
    """
    r = min(r, W / 2 - eps, H / 2 - eps, t - eps)
    if r <= eps:
        return axis_box(0.0, 0.0, -t, W, H, 0.0)

    samples = [(-t, r)]
    for j in range(n_fillet + 1):
        phi = (np.pi / 2) * (j / n_fillet)
        if j == n_fillet:
            z_j = 0.0
            d_j = eps
        else:
            z_j = -r + r * np.sin(phi)
            d_j = r * np.cos(phi)
        samples.append((z_j, d_j))

    rings = []
    for z, d in samples:
        ring = _rounded_outline(W, H, r, d, n_corner)
        ring[:, 2] = z
        rings.append(ring)

    ring_size = 4 * (n_corner + 1)
    ring_verts = np.concatenate(rings, axis=0)

    bottom_center_idx = len(ring_verts)
    top_center_idx = bottom_center_idx + 1
    centers = np.array(
        [[W / 2, H / 2, -t], [W / 2, H / 2, 0.0]],
        dtype=np.float64,
    )
    all_verts = np.vstack([ring_verts, centers])

    faces = []

    for ring_i in range(len(rings) - 1):
        base0 = ring_i * ring_size
        base1 = (ring_i + 1) * ring_size
        for k in range(ring_size):
            k_next = (k + 1) % ring_size
            a = base0 + k
            b = base0 + k_next
            c = base1 + k_next
            d_idx = base1 + k
            faces.append([a, b, c])
            faces.append([a, c, d_idx])

    bottom_base = 0
    for k in range(ring_size):
        k_next = (k + 1) % ring_size
        faces.append([bottom_center_idx,
                      bottom_base + k_next,
                      bottom_base + k])

    top_base = (len(rings) - 1) * ring_size
    for k in range(ring_size):
        k_next = (k + 1) % ring_size
        faces.append([top_center_idx,
                      top_base + k,
                      top_base + k_next])

    return all_verts, np.asarray(faces, dtype=np.int64)


# ---------------------------------------------------------------------------
# Braille plate assembly
# ---------------------------------------------------------------------------
def plate_dimensions(lines_cells):
    max_cells = max((len(c) for c in lines_cells), default=0)
    num_lines = max(len(lines_cells), 1)

    content_w = max(max_cells, 1) * CHAR_WIDTH
    content_h = num_lines * LINE_HEIGHT

    plate_w = content_w + 2 * MARGIN
    plate_h = content_h + 2 * MARGIN
    return plate_w, plate_h


DEFAULT_DOT_STYLE = 'dome'
DEFAULT_DOT_RADIUS = 0.8
DEFAULT_DOT_EMBED = 0.15


def build_braille_mesh(text, plate_thickness=PLATE_THICKNESS,
                       with_backplate=True, with_supports=True,
                       fillet_radius=0.0,
                       dot_style=DEFAULT_DOT_STYLE,
                       dot_radius=DEFAULT_DOT_RADIUS,
                       dot_embed=DEFAULT_DOT_EMBED,
                       n_corner=6, n_fillet=6):
    lines_cells = text_to_cells(text)
    plate_w, plate_h = plate_dimensions(lines_cells)

    meshes = []
    y_pad_in_cell = (LINE_HEIGHT - 2 * DOT_SPACING) / 2

    for line_idx, cells in enumerate(lines_cells):
        for cell_idx, dots in enumerate(cells):
            cell_x = MARGIN + cell_idx * CHAR_WIDTH + DOT_SPACING / 2
            cell_y = MARGIN + line_idx * LINE_HEIGHT + y_pad_in_cell
            for dot in dots:
                if dot not in DOT_OFFSETS:
                    continue
                dx, dy = DOT_OFFSETS[dot]
                dot_center = (cell_x + dx, cell_y + dy, 0.0)
                if dot_style == 'dome':
                    meshes.append(dome(dot_center, dot_radius, dot_embed))
                else:
                    meshes.append(uv_sphere(dot_center, dot_radius))

    if with_backplate:
        if fillet_radius > 0:
            meshes.append(filleted_plate(
                plate_w, plate_h, plate_thickness, fillet_radius,
                n_corner=n_corner, n_fillet=n_fillet,
            ))
        else:
            meshes.append(axis_box(0.0, 0.0, -plate_thickness,
                                   plate_w, plate_h, 0.0))

        if with_supports:
            sup_z_top = 0.0
            sup_z_bot = -plate_thickness - 18.0
            for sx in (3.0, plate_w - 3.0):
                meshes.append(axis_box(
                    sx - 2.5, plate_h - 2.0, sup_z_bot,
                    sx + 2.5, plate_h,       sup_z_top,
                ))

    v, f = combine(meshes)
    return v, f, (plate_w, plate_h, plate_thickness)


# ---------------------------------------------------------------------------
# STL output
# ---------------------------------------------------------------------------
def save_stl(vertices, faces, filename):
    """Write a binary STL. Requires the numpy-stl package."""
    try:
        from stl import mesh as stl_mesh
    except ImportError as exc:
        raise ImportError(
            "numpy-stl 패키지가 필요합니다. 설치: pip install numpy-stl"
        ) from exc

    if len(faces) == 0:
        raise ValueError("생성할 지오메트리가 없습니다 (빈 텍스트).")

    data = np.zeros(len(faces), dtype=stl_mesh.Mesh.dtype)
    data['vectors'] = vertices[faces]
    m = stl_mesh.Mesh(data)
    m.save(filename)


def build_and_save(text, filename, plate_thickness=PLATE_THICKNESS,
                   with_backplate=True, with_supports=True,
                   fillet_radius=0.0,
                   dot_style=DEFAULT_DOT_STYLE,
                   dot_radius=DEFAULT_DOT_RADIUS,
                   dot_embed=DEFAULT_DOT_EMBED):
    v, f, dims = build_braille_mesh(
        text,
        plate_thickness=plate_thickness,
        with_backplate=with_backplate,
        with_supports=with_supports,
        fillet_radius=fillet_radius,
        dot_style=dot_style,
        dot_radius=dot_radius,
        dot_embed=dot_embed,
    )
    save_stl(v, f, filename)
    return len(f), dims
