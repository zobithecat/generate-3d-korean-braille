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


def dome(center, radius, embed_depth, flat_top_depth=0.05,
         lat_segs=4, lon_segs=10):
    """Cylinder + upper hemisphere joined at z = cz, optionally with a
    small flat cap at the apex.

    center = (cx, cy, cz): cz is the plate surface (hemisphere equator).
    The cylinder extends downward to cz - embed_depth (anchored inside
    the plate); the hemisphere (radius ``radius``) sits on top.

    ``flat_top_depth`` > 0 truncates the hemisphere apex at
    z = cz + radius - flat_top_depth, replacing the single-point apex
    with a small flat disc of radius sqrt(2 R d - d²). This gives the
    FDM nozzle a proper landing surface instead of finishing on a
    geometric point, eliminating the pointed-blob artifact at each dot.

    Outward-facing triangles.
    """
    cx, cy, cz = center

    # Clamp flat_top_depth to at most 50% of hemisphere radius.
    flat_top_depth = max(0.0, min(flat_top_depth, radius * 0.5))
    use_flat_top = flat_top_depth > 0.0

    vertices = []
    if use_flat_top:
        z_cap = cz + radius - flat_top_depth
        cap_r = float(np.sqrt(radius ** 2 - (radius - flat_top_depth) ** 2))
        top_center_idx = len(vertices)
        vertices.append([cx, cy, z_cap])
        cap_ring_start = len(vertices)
        for lon in range(lon_segs):
            theta = 2 * np.pi * lon / lon_segs
            vertices.append([
                cx + cap_r * np.cos(theta),
                cy + cap_r * np.sin(theta),
                z_cap,
            ])
    else:
        z_cap = None
        vertices.append([cx, cy, cz + radius])     # pointed apex at idx 0

    ring_indices = []
    for lat in range(1, lat_segs + 1):
        phi = (np.pi / 2) * lat / lat_segs
        ring_r = radius * np.sin(phi)
        ring_z = cz + radius * np.cos(phi)
        # Drop rings that would sit above the flat cap.
        if use_flat_top and ring_z >= z_cap - 1e-6:
            continue
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
    if use_flat_top:
        # Flat cap fan (normal +Z).
        for lon in range(lon_segs):
            nxt = (lon + 1) % lon_segs
            faces.append([top_center_idx,
                          cap_ring_start + lon,
                          cap_ring_start + nxt])
        # Band: cap ring -> first hemisphere ring below it.
        if ring_indices:
            rs0 = cap_ring_start
            rs1 = ring_indices[0]
            for lon in range(lon_segs):
                nxt = (lon + 1) % lon_segs
                a = rs0 + lon
                b = rs0 + nxt
                c = rs1 + nxt
                d = rs1 + lon
                faces.append([a, d, c])
                faces.append([a, c, b])
    else:
        # Pointed apex fan.
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

    if ring_indices:
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
def plate_dimensions(lines_cells, margin=MARGIN):
    max_cells = max((len(c) for c in lines_cells), default=0)
    num_lines = max(len(lines_cells), 1)

    content_w = max(max_cells, 1) * CHAR_WIDTH
    content_h = num_lines * LINE_HEIGHT

    plate_w = content_w + 2 * margin
    plate_h = content_h + 2 * margin
    return plate_w, plate_h


DEFAULT_DOT_STYLE = 'dome'
DEFAULT_DOT_RADIUS = 1.0
DEFAULT_DOT_EMBED = 0.15
DEFAULT_DOT_FLAT = 0.05          # apex truncation for FDM-friendly cap (mm)

DEFAULT_ENGRAVING = True
DEFAULT_ENGRAVING_SIZE = 4.0     # triangle side length (mm)
DEFAULT_ENGRAVING_DEPTH = 0.2    # pocket depth into plate (mm)


def _triangular_prism(cx, cy, z_bottom, z_top, size, pointing_up=True):
    """Watertight equilateral triangular prism for boolean subtraction.

    The prism is axis-aligned with its triangle cross section in the XY
    plane, extruded between z_bottom and z_top (z_top > z_bottom).
    ``pointing_up`` places the triangle's apex at larger Y.
    Returns (vertices, faces) with outward-facing normals.
    """
    h = size * np.sqrt(3) / 2
    if pointing_up:
        tri_xy = [
            (cx,            cy + h * 2 / 3),   # apex
            (cx - size / 2, cy - h / 3),       # bottom-left
            (cx + size / 2, cy - h / 3),       # bottom-right
        ]
    else:
        tri_xy = [
            (cx,            cy - h * 2 / 3),
            (cx + size / 2, cy + h / 3),
            (cx - size / 2, cy + h / 3),
        ]

    # Vertices: 0..2 = bottom triangle, 3..5 = top triangle (same XY)
    v = np.array(
        [[x, y, z_bottom] for (x, y) in tri_xy]
        + [[x, y, z_top] for (x, y) in tri_xy],
        dtype=np.float64,
    )
    # Faces with outward normals.
    # Bottom face (z_bottom), normal -Z: CW when viewed from +Z → [0,2,1]
    # Top face (z_top), normal +Z: CCW viewed from +Z → [3,4,5]
    # Side i → (i+1): outward side with CCW from outside
    f = np.array([
        [0, 2, 1],
        [3, 4, 5],
        [0, 1, 4], [0, 4, 3],
        [1, 2, 5], [1, 5, 4],
        [2, 0, 3], [2, 3, 5],
    ], dtype=np.int64)
    return v, f


def apply_triangular_engraving(plate_v, plate_f, plate_w, plate_h,
                                plate_thickness, size, depth,
                                pointing_up=True, cx=None, cy=None):
    """Boolean-subtract a triangular pocket from the plate back face.

    Uses trimesh + manifold3d. The pocket opens at z = -plate_thickness
    (plate's back face) and extends upward (into the plate) by ``depth``.
    Returns (vertices, faces) of the engraved plate.
    """
    try:
        import trimesh
    except ImportError as exc:
        raise ImportError(
            "trimesh 가 필요합니다. 설치: pip install 'trimesh[easy]' manifold3d"
        ) from exc

    if cx is None:
        cx = plate_w / 2
    if cy is None:
        cy = plate_h / 2

    # Clamp so the engraving is always safely inside the plate.
    size = max(0.0, min(size, plate_w * 0.4, plate_h * 0.6))
    depth = max(0.0, min(depth, plate_thickness * 0.4))
    if size <= 0 or depth <= 0:
        return plate_v, plate_f

    # Prism: bottom slightly BELOW the plate's back face so the boolean
    # cleanly cuts through the back (no coplanar surfaces).
    z_bottom = -plate_thickness - 0.1
    z_top = -plate_thickness + depth

    pv, pf = _triangular_prism(cx, cy, z_bottom, z_top, size, pointing_up)

    plate = trimesh.Trimesh(plate_v, plate_f, process=False)
    prism = trimesh.Trimesh(pv, pf, process=False)
    engraved = trimesh.boolean.difference([plate, prism])
    return (np.asarray(engraved.vertices, dtype=np.float64),
            np.asarray(engraved.faces, dtype=np.int64))


def build_braille_mesh(text, plate_thickness=PLATE_THICKNESS,
                       with_backplate=True, with_supports=True,
                       fillet_radius=0.0,
                       dot_style=DEFAULT_DOT_STYLE,
                       dot_radius=DEFAULT_DOT_RADIUS,
                       dot_embed=DEFAULT_DOT_EMBED,
                       dot_flat=DEFAULT_DOT_FLAT,
                       with_engraving=DEFAULT_ENGRAVING,
                       engraving_size=DEFAULT_ENGRAVING_SIZE,
                       engraving_depth=DEFAULT_ENGRAVING_DEPTH,
                       margin=MARGIN,
                       n_corner=6, n_fillet=6):
    lines_cells = text_to_cells(text)
    plate_w, plate_h = plate_dimensions(lines_cells, margin=margin)
    num_lines = max(len(lines_cells), 1)

    meshes = []
    y_pad_in_cell = (LINE_HEIGHT - 2 * DOT_SPACING) / 2

    # Y-axis mirror for the braille content so that in a Y-up 3D viewer /
    # slicer the braille is visually right-side-up (dot 1 at the top of each
    # cell, line 0 at the top of the plate). The plate itself is Y-symmetric
    # and the supports stay pinned to y = plate_h, so they are unaffected.
    for line_idx, cells in enumerate(lines_cells):
        effective_line = (num_lines - 1) - line_idx
        for cell_idx, dots in enumerate(cells):
            cell_x = margin + cell_idx * CHAR_WIDTH + DOT_SPACING / 2
            cell_y = margin + effective_line * LINE_HEIGHT + y_pad_in_cell
            for dot in dots:
                if dot not in DOT_OFFSETS:
                    continue
                dx, dy = DOT_OFFSETS[dot]
                dy_flipped = 2 * DOT_SPACING - dy
                dot_center = (cell_x + dx, cell_y + dy_flipped, 0.0)
                if dot_style == 'dome':
                    meshes.append(dome(dot_center, dot_radius, dot_embed,
                                       flat_top_depth=dot_flat))
                else:
                    meshes.append(uv_sphere(dot_center, dot_radius))

    if with_backplate:
        if fillet_radius > 0:
            plate_v, plate_f = filleted_plate(
                plate_w, plate_h, plate_thickness, fillet_radius,
                n_corner=n_corner, n_fillet=n_fillet,
            )
        else:
            plate_v, plate_f = axis_box(
                0.0, 0.0, -plate_thickness,
                plate_w, plate_h, 0.0,
            )

        if with_engraving and engraving_size > 0 and engraving_depth > 0:
            plate_v, plate_f = apply_triangular_engraving(
                plate_v, plate_f, plate_w, plate_h, plate_thickness,
                size=engraving_size, depth=engraving_depth,
                pointing_up=True,
            )

        meshes.append((plate_v, plate_f))

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
                   dot_embed=DEFAULT_DOT_EMBED,
                   dot_flat=DEFAULT_DOT_FLAT,
                   with_engraving=DEFAULT_ENGRAVING,
                   engraving_size=DEFAULT_ENGRAVING_SIZE,
                   engraving_depth=DEFAULT_ENGRAVING_DEPTH,
                   margin=MARGIN):
    v, f, dims = build_braille_mesh(
        text,
        plate_thickness=plate_thickness,
        with_backplate=with_backplate,
        with_supports=with_supports,
        fillet_radius=fillet_radius,
        dot_style=dot_style,
        dot_radius=dot_radius,
        dot_embed=dot_embed,
        dot_flat=dot_flat,
        with_engraving=with_engraving,
        engraving_size=engraving_size,
        engraving_depth=engraving_depth,
        margin=margin,
    )
    save_stl(v, f, filename)
    return len(f), dims
