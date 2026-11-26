"""
Procedural Blender 5.3 builder for the Strawberry Hollow Lantern ("StrawberryLamp").
Builds clean, game-ready stylized geometry, procedural botanical vein & leaf textures,
PBR/Cycles translucent frosted-glass shaders, magical interior floating light motes,
and renders a 6-view turnaround sheet + twilight hero beauty shot.
"""

import math
import os
import random
import numpy as np
import bpy
import bmesh
from mathutils import Vector, Matrix, Euler

# ---------------------------------------------------------------------------
# Paths & Configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT = r"c:\Users\count\Documents\Unreal Projects\Parkour"
OUT_DIR = os.path.join(PROJECT_ROOT, "SourceArt", "StrawberryLamp")
TEX_DIR = os.path.join(OUT_DIR, "Textures")
RENDER_DIR = os.path.join(OUT_DIR, "Renders")
os.makedirs(TEX_DIR, exist_ok=True)
os.makedirs(RENDER_DIR, exist_ok=True)

BLEND_PATH = os.path.join(OUT_DIR, "StrawberryLamp.blend")

# Real-world scale: normalized unit 1.0 = 0.18 m (body diameter ~0.36 m, total height ~0.45 m)
SCALE = 0.18
H_BODY = 1.64
NUM_LOBES = 8


def srgb_to_linear_channel(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def srgb(r: float, g: float, b: float, a: float = 1.0):
    return (
        srgb_to_linear_channel(r),
        srgb_to_linear_channel(g),
        srgb_to_linear_channel(b),
        a,
    )


def srgb3(r: float, g: float, b: float):
    return (
        srgb_to_linear_channel(r),
        srgb_to_linear_channel(g),
        srgb_to_linear_channel(b),
    )


# ---------------------------------------------------------------------------
# Math helpers: plump strawberry-lantern silhouette profile
# ---------------------------------------------------------------------------
def _catmull_rom(p0, p1, p2, p3, u):
    u2 = u * u
    u3 = u2 * u
    return 0.5 * (
        (2.0 * p1)
        + (-p0 + p2) * u
        + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * u2
        + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * u3
    )


# Plump, balanced strawberry-lantern profile matching concept art FRONT/RIGHT/BACK:
# Cute ogival bottom tip -> full rounded lower belly -> widest at ~58% -> plump shoulder under calyx.
PROFILE_PTS = [
    (-0.04, -0.06),
    (0.00, 0.00),
    (0.04, 0.115),
    (0.11, 0.345),
    (0.21, 0.61),
    (0.34, 0.835),
    (0.48, 0.968),
    (0.60, 1.00),
    (0.73, 0.962),
    (0.84, 0.845),
    (0.92, 0.64),
    (0.97, 0.36),
    (1.00, 0.00),
    (1.04, -0.25),
]


def sample_profile_radius(t: float) -> float:
    if t <= 0.0 or t >= 1.0:
        return 0.0
    pts = PROFILE_PTS
    for i in range(1, len(pts) - 2):
        t1, r1 = pts[i]
        t2, r2 = pts[i + 1]
        if t1 <= t <= t2:
            u = (t - t1) / max(1e-8, (t2 - t1))
            r = _catmull_rom(pts[i - 1][1], r1, r2, pts[i + 2][1], u)
            return max(0.0, r)
    return 0.0


def lobe_bulge(theta: float) -> float:
    s = abs(math.sin(0.5 * NUM_LOBES * theta))
    eps = 0.004
    p = 0.27
    v0 = eps ** p
    v1 = (1.0 + eps) ** p
    return (((s * s + eps) ** p) - v0) / (v1 - v0)


def lobe_vertical_envelope(t: float) -> float:
    lo = min(1.0, max(0.0, t / 0.08))
    lo = lo * lo * (3.0 - 2.0 * lo)
    hi = min(1.0, max(0.0, (1.0 - t) / 0.08))
    hi = hi * hi * (3.0 - 2.0 * hi)
    return lo * hi


def body_radius(t: float, theta: float) -> float:
    rb = sample_profile_radius(t)
    env = lobe_vertical_envelope(t)
    b = lobe_bulge(theta)
    r_valley = rb * 0.905
    r_crest = rb * 1.05
    return r_valley + (r_crest - r_valley) * b * env


def valley_radius(t: float) -> float:
    return sample_profile_radius(t) * 0.905


def body_z(t: float) -> float:
    return t * H_BODY


def find_shoulder_z_for_radius(r_target: float) -> float:
    best_t = 0.85
    for i in range(400):
        t = 1.0 - (i / 399.0) * 0.42
        r = sample_profile_radius(t) * 0.955
        if r >= r_target:
            best_t = t
            break
    return body_z(best_t)


# ---------------------------------------------------------------------------
# Procedural Texture Generation (NumPy -> PNG -> Packed Blender Images)
# ---------------------------------------------------------------------------
def _fbm_2d(h: int, w: int, octaves=5, base_freq=4, seed=101) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), dtype=np.float32)
    amp = 0.5
    norm = 0.0
    for o in range(octaves):
        freq_y = max(2, int(base_freq * (2 ** o)))
        freq_x = max(2, int(base_freq * (w / h) * (2 ** o)))
        grid = rng.random((freq_y, freq_x), dtype=np.float32)
        ys = np.linspace(0, freq_y, h, endpoint=False)
        xs = np.linspace(0, freq_x, w, endpoint=False)
        y0 = np.floor(ys).astype(np.int32)
        x0 = np.floor(xs).astype(np.int32)
        y1 = (y0 + 1) % freq_y
        x1 = (x0 + 1) % freq_x
        fy = (ys - y0).astype(np.float32)
        fx = (xs - x0).astype(np.float32)
        fy = fy * fy * (3.0 - 2.0 * fy)
        fx = fx * fx * (3.0 - 2.0 * fx)

        c00 = grid[y0[:, None], x0[None, :]]
        c10 = grid[y0[:, None], x1[None, :]]
        c01 = grid[y1[:, None], x0[None, :]]
        c11 = grid[y1[:, None], x1[None, :]]
        top = c00 * (1.0 - fx[None, :]) + c10 * fx[None, :]
        bot = c01 * (1.0 - fx[None, :]) + c11 * fx[None, :]
        layer = top * (1.0 - fy[:, None]) + bot * fy[:, None]
        out += layer * amp
        norm += amp
        amp *= 0.52
    return out / max(1e-6, norm)


def _draw_segment(canvas: np.ndarray, x0, y0, x1, y1, radius_px, intensity):
    h, w = canvas.shape
    pad = int(math.ceil(radius_px * 2.5)) + 2
    min_x = max(0, int(min(x0, x1)) - pad)
    max_x = min(w - 1, int(max(x0, x1)) + pad)
    min_y = max(0, int(min(y0, y1)) - pad)
    max_y = min(h - 1, int(max(y0, y1)) + pad)
    if max_x < min_x or max_y < min_y:
        return

    yy, xx = np.mgrid[min_y:max_y + 1, min_x:max_x + 1]
    dx = x1 - x0
    dy = y1 - y0
    seg_len2 = dx * dx + dy * dy + 1e-8
    t = np.clip(((xx - x0) * dx + (yy - y0) * dy) / seg_len2, 0.0, 1.0)
    px = x0 + t * dx
    py = y0 + t * dy
    dist = np.sqrt((xx - px) ** 2 + (yy - py) ** 2)
    val = intensity * np.exp(-0.5 * (dist / max(0.45, radius_px)) ** 2)
    np.maximum(canvas[min_y:max_y + 1, min_x:max_x + 1], val, out=canvas[min_y:max_y + 1, min_x:max_x + 1])


def _save_rgba_png(rgba: np.ndarray, filepath: str, name: str, colorspace="sRGB"):
    h, w, _ = rgba.shape
    if name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[name])
    img = bpy.data.images.new(name=name, width=w, height=h, alpha=True, float_buffer=False)
    img.pixels.foreach_set(np.clip(rgba, 0.0, 1.0).ravel())
    img.filepath_raw = filepath
    img.file_format = "PNG"
    img.save()
    img.colorspace_settings.name = colorspace
    img.pack()
    return img


def generate_glass_vein_texture():
    """
    2048x1024 delicate, airy botanical capillary veins & soft cloudy rose-quartz frost
    across all 8 lobes (refined so veins feel ethereal & delicate, not dense/fibrous).
    """
    w, h = 2048, 1024
    lobe_w = w // NUM_LOBES
    vein_map = np.zeros((h, w), dtype=np.float32)

    rng = random.Random(2026)

    def draw_branch(cx, cy, angle, length, thickness, intensity, depth, lobe_x0, lobe_x1):
        if depth <= 0 or length < 14.0 or intensity < 0.08:
            return
        steps = max(5, int(length / 14.0))
        x, y = cx, cy
        ang = angle
        for s in range(steps):
            frac = s / float(steps)
            ang += rng.uniform(-0.11, 0.11)
            ang = ang * 0.90 + (math.pi * 0.5) * 0.10
            step_len = length / float(steps)
            nx = x + math.cos(ang) * step_len
            ny = y + math.sin(ang) * step_len
            margin = 8.0
            nx = max(lobe_x0 + margin, min(lobe_x1 - margin, nx))
            ny = max(12.0, min(h - 14.0, ny))
            rad = thickness * (1.0 - 0.52 * frac)
            _draw_segment(vein_map, x, y, nx, ny, rad, intensity * (1.0 - 0.24 * frac))

            if depth >= 2 and s > 0 and s % 3 == 1 and rng.random() < 0.72:
                if depth == 3:
                    for sd in (-1.0, 1.0):
                        b_ang = ang + sd * rng.uniform(0.42, 0.78)
                        draw_branch(
                            nx, ny, b_ang,
                            length * rng.uniform(0.20, 0.34),
                            rad * 0.72,
                            intensity * rng.uniform(0.60, 0.78),
                            depth - 1,
                            lobe_x0, lobe_x1,
                        )
                else:
                    side = 1.0 if ((s + depth) % 2 == 0) else -1.0
                    b_ang = ang + side * rng.uniform(0.32, 0.68)
                    draw_branch(
                        nx, ny, b_ang,
                        length * rng.uniform(0.32, 0.50),
                        rad * 0.68,
                        intensity * rng.uniform(0.55, 0.72),
                        depth - 1,
                        lobe_x0, lobe_x1,
                    )
            x, y = nx, ny

    for k in range(NUM_LOBES):
        lx0 = k * lobe_w
        lx1 = (k + 1) * lobe_w
        lmid = 0.5 * (lx0 + lx1)

        # Single graceful central branching botanical vein per lobe
        draw_branch(
            lmid + rng.uniform(-6, 6),
            h * 0.06,
            math.pi * 0.5 + rng.uniform(-0.04, 0.04),
            h * 0.86,
            2.1,
            0.92,
            depth=3,
            lobe_x0=lx0,
            lobe_x1=lx1,
        )
        # Subtle delicate side capillary
        for side in (-1.0, 1.0):
            draw_branch(
                lmid + side * (lobe_w * rng.uniform(0.24, 0.32)),
                h * rng.uniform(0.20, 0.34),
                math.pi * 0.5 - side * rng.uniform(0.06, 0.16),
                h * rng.uniform(0.45, 0.58),
                1.4,
                0.62,
                depth=2,
                lobe_x0=lx0,
                lobe_x1=lx1,
            )

    marble = _fbm_2d(h, w, octaves=5, base_freq=4, seed=77)
    fine_grain = _fbm_2d(h, w, octaves=4, base_freq=18, seed=99)

    vein_soft = np.clip(vein_map, 0.0, 1.0)
    combined = np.clip(vein_soft * 0.70 + marble * 0.35 + fine_grain * 0.10, 0.0, 1.0)

    rgba = np.stack([vein_soft, marble, fine_grain, combined], axis=-1).astype(np.float32)
    path = os.path.join(TEX_DIR, "T_StrawberryLamp_GlassVein.png")
    return _save_rgba_png(rgba, path, "T_StrawberryLamp_GlassVein", colorspace="Non-Color")


def generate_leaf_textures():
    """Clean, velvety muted sage-olive calyx leaf BaseColor & Bump textures (1024x1024)."""
    size = 1024
    yy, xx = np.mgrid[0:size, 0:size]
    u = xx / float(size - 1)
    v = yy / float(size - 1)
    du = np.abs(u - 0.5) * 2.0

    midrib_groove = np.exp(-((du / 0.046) ** 2)) * (1.0 - 0.28 * v)
    midrib_ridge = np.exp(-((du / 0.015) ** 2)) * (1.0 - 0.55 * v)

    lat_veins = np.zeros_like(u, dtype=np.float32)
    for k in range(4):
        v0 = 0.16 + k * 0.175
        v_curve = v0 + 0.25 * (du ** 1.28)
        dist = np.abs(v - v_curve)
        mask = np.clip(1.0 - du * 0.90, 0.0, 1.0) * np.clip((du - 0.025) / 0.06, 0.0, 1.0)
        lat_veins = np.maximum(lat_veins, np.exp(-((dist / 0.013) ** 2)) * mask * (1.0 - 0.25 * v))

    fbm = _fbm_2d(size, size, octaves=4, base_freq=5, seed=314)

    # Concept art warm olive-sage leaf color
    base_r = 0.56 + 0.06 * (du ** 0.9) + 0.07 * v + 0.02 * (fbm - 0.5)
    base_g = 0.58 + 0.05 * (du ** 0.9) + 0.06 * v + 0.02 * (fbm - 0.5)
    base_b = 0.26 + 0.03 * du + 0.03 * v + 0.012 * (fbm - 0.5)

    base_ao = 0.12 * np.exp(-((v / 0.16) ** 2))
    darken = 0.12 * midrib_groove + 0.09 * lat_veins + base_ao
    r = np.clip(base_r * (1.0 - darken) + 0.02 * midrib_ridge, 0.0, 1.0)
    g = np.clip(base_g * (1.0 - darken) + 0.025 * midrib_ridge, 0.0, 1.0)
    b = np.clip(base_b * (1.0 - darken * 1.08), 0.0, 1.0)

    rgba_col = np.stack([r, g, b, np.ones_like(r)], axis=-1).astype(np.float32)
    col_img = _save_rgba_png(
        rgba_col,
        os.path.join(TEX_DIR, "T_StrawberryLamp_Leaf_BaseColor.png"),
        "T_StrawberryLamp_Leaf_BaseColor",
        colorspace="sRGB",
    )

    height = 0.55 - 0.22 * midrib_groove + 0.08 * midrib_ridge - 0.16 * lat_veins + 0.03 * (fbm - 0.5)
    height = np.clip(height, 0.0, 1.0)
    rgba_bump = np.stack([height, height, height, np.ones_like(height)], axis=-1).astype(np.float32)
    bump_img = _save_rgba_png(
        rgba_bump,
        os.path.join(TEX_DIR, "T_StrawberryLamp_Leaf_Bump.png"),
        "T_StrawberryLamp_Leaf_Bump",
        colorspace="Non-Color",
    )
    return col_img, bump_img


# ---------------------------------------------------------------------------
# Geometry Builders
# ---------------------------------------------------------------------------
def _set_smooth(mesh):
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.update()


def build_glass_body(collection):
    """Build the 8-lobed translucent strawberry lantern shell with clean non-overlapping UVs."""
    n_z = 96
    n_theta = NUM_LOBES * 24

    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    t_vals = [0.5 * (1.0 - math.cos(math.pi * i / (n_z - 1))) for i in range(n_z)]
    v_bot = bm.verts.new(Vector((0.0, 0.0, body_z(0.0))) * SCALE)
    v_top = bm.verts.new(Vector((0.0, 0.0, body_z(1.0))) * SCALE)

    rings = []
    for iz in range(1, n_z - 1):
        t = t_vals[iz]
        z = body_z(t)
        ring = []
        for it in range(n_theta):
            theta = (2.0 * math.pi * it) / n_theta
            r = body_radius(t, theta)
            ring.append(bm.verts.new(Vector((r * math.cos(theta), r * math.sin(theta), z)) * SCALE))
        rings.append((t, ring))

    t0, r0 = rings[0]
    for it in range(n_theta):
        it_next = (it + 1) % n_theta
        f = bm.faces.new((v_bot, r0[it_next], r0[it]))
        u0 = it / float(n_theta)
        u1 = (it + 1) / float(n_theta)
        f.loops[0][uv_layer].uv = (0.5 * (u0 + u1), 0.0)
        f.loops[1][uv_layer].uv = (u1, t0)
        f.loops[2][uv_layer].uv = (u0, t0)

    for iz in range(len(rings) - 1):
        ta, ra = rings[iz]
        tb, rb = rings[iz + 1]
        for it in range(n_theta):
            it_next = (it + 1) % n_theta
            f = bm.faces.new((ra[it], ra[it_next], rb[it_next], rb[it]))
            u0 = it / float(n_theta)
            u1 = (it + 1) / float(n_theta)
            f.loops[0][uv_layer].uv = (u0, ta)
            f.loops[1][uv_layer].uv = (u1, ta)
            f.loops[2][uv_layer].uv = (u1, tb)
            f.loops[3][uv_layer].uv = (u0, tb)

    t_last, r_last = rings[-1]
    for it in range(n_theta):
        it_next = (it + 1) % n_theta
        f = bm.faces.new((r_last[it], r_last[it_next], v_top))
        u0 = it / float(n_theta)
        u1 = (it + 1) / float(n_theta)
        f.loops[0][uv_layer].uv = (u0, t_last)
        f.loops[1][uv_layer].uv = (u1, t_last)
        f.loops[2][uv_layer].uv = (0.5 * (u0 + u1), 1.0)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("StrawberryLamp_GlassBody_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    _set_smooth(mesh)

    obj = bpy.data.objects.new("StrawberryLamp_GlassBody", mesh)
    collection.objects.link(obj)
    return obj


def build_golden_ribs_and_finial(collection):
    """Build the 8 sleek golden wire ribs nestled cleanly in the valleys + bottom finial bead."""
    bm = bmesh.new()
    rib_radius = 0.0155
    n_steps = 64
    n_sides = 14

    for k in range(NUM_LOBES):
        theta = k * (2.0 * math.pi / NUM_LOBES)
        radial_dir = Vector((math.cos(theta), math.sin(theta), 0.0))
        tangent_lat = Vector((-math.sin(theta), math.cos(theta), 0.0))

        pts = []
        for i in range(n_steps):
            frac = i / float(n_steps - 1)
            t = 0.008 + 0.955 * (0.5 * (1.0 - math.cos(math.pi * frac)))
            r = valley_radius(t) + 0.004
            z = body_z(t)
            pts.append(Vector((r * radial_dir.x, r * radial_dir.y, z)) * SCALE)

        rings = []
        for i, p in enumerate(pts):
            if i == 0:
                tang = (pts[1] - pts[0]).normalized()
            elif i == len(pts) - 1:
                tang = (pts[-1] - pts[-2]).normalized()
            else:
                tang = (pts[i + 1] - pts[i - 1]).normalized()
            out_n = tangent_lat.cross(tang).normalized()
            if out_n.dot(radial_dir) < 0:
                out_n = -out_n

            ring = []
            for s in range(n_sides):
                ang = (2.0 * math.pi * s) / n_sides
                offset = (out_n * math.cos(ang) + tangent_lat * math.sin(ang)) * (rib_radius * SCALE)
                ring.append(bm.verts.new(p + offset))
            rings.append(ring)

        for i in range(len(rings) - 1):
            ra, rb = rings[i], rings[i + 1]
            for s in range(n_sides):
                sn = (s + 1) % n_sides
                bm.faces.new((ra[s], ra[sn], rb[sn], rb[s]))

        bm.faces.new(rings[0][::-1])
        bm.faces.new(rings[-1])

    finial_mat = Matrix.Translation(Vector((0.0, 0.0, -0.003 * SCALE))) @ Matrix.Diagonal((1.0, 1.0, 0.86, 1.0))
    bmesh.ops.create_uvsphere(
        bm,
        u_segments=28,
        v_segments=16,
        radius=0.052 * SCALE,
        matrix=finial_mat,
    )

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("StrawberryLamp_GoldRibs_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    _set_smooth(mesh)

    obj = bpy.data.objects.new("StrawberryLamp_GoldRibs", mesh)
    collection.objects.link(obj)
    return obj


def _leaf_width(u: float) -> float:
    """
    Almond/petal-shaped leaf silhouette matching concept art TOP view:
    clean deeper V-separation between adjacent leaves starting around u=0.25,
    plump rounded oval belly around u=0.52, tapering gracefully to a soft point!
    """
    if u <= 0.0:
        return 0.075
    if u >= 1.0:
        return 0.004
    # Classic almond/ovate petal: narrower near base so the 8 petals separate crisply,
    # swelling gently to a full rounded oval belly around u = 0.50!
    s = math.sin(math.pi * (u ** 0.90))
    w_main = 0.275 * (max(0.0, s) ** 0.72)
    # Tight overlap only right under the gold collar (u < 0.16)
    w_base = 0.065 * ((1.0 - min(1.0, u / 0.18)) ** 1.5)
    return max(0.004, w_main + w_base)


def _leaf_spine_rz(u: float):
    """
    Graceful strawberry-hull drape: hugs down nicely over the upper shoulder
    with a soft organic outward flare at the tip!
    """
    r_start = 0.13
    r_end = 0.93
    r = r_start + (r_end - r_start) * u

    z_top = H_BODY + 0.032
    drape = -0.315 * (math.sin(u * math.pi * 0.58) ** 1.22)
    soft_flare = 0.052 * (u ** 2.65) * (1.0 - 0.12 * u)
    z = z_top + drape + soft_flare

    if r < 0.88:
        z_glass = find_shoulder_z_for_radius(r)
        target = z_glass + 0.022
        if target > z:
            z = z + (target - z) * 0.90

    return r, z


def build_calyx_leaves(collection):
    """Build 8 plump, sculpted olive-green calyx leaves with almond petal separation."""
    n_u = 30
    n_v = 16

    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    raw_spine = []
    for iu in range(n_u):
        u = iu / float(n_u - 1)
        r, z = _leaf_spine_rz(u)
        raw_spine.append([u, r, z])
    for _ in range(4):
        smoothed = [raw_spine[0][:]]
        for iu in range(1, n_u - 1):
            sr = 0.25 * raw_spine[iu - 1][1] + 0.5 * raw_spine[iu][1] + 0.25 * raw_spine[iu + 1][1]
            sz = 0.25 * raw_spine[iu - 1][2] + 0.5 * raw_spine[iu][2] + 0.25 * raw_spine[iu + 1][2]
            smoothed.append([raw_spine[iu][0], sr, sz])
        smoothed.append(raw_spine[-1][:])
        raw_spine = smoothed

    for k in range(NUM_LOBES):
        theta = k * (2.0 * math.pi / NUM_LOBES)
        dir_r = Vector((math.cos(theta), math.sin(theta), 0.0))
        dir_t = Vector((-math.sin(theta), math.cos(theta), 0.0))

        top_grid = []
        bot_grid = []

        for iu in range(n_u):
            u, r_s, z_s = raw_spine[iu]
            if iu == 0:
                dr = raw_spine[1][1] - raw_spine[0][1]
                dz = raw_spine[1][2] - raw_spine[0][2]
            elif iu == n_u - 1:
                dr = raw_spine[-1][1] - raw_spine[-2][1]
                dz = raw_spine[-1][2] - raw_spine[-2][2]
            else:
                dr = raw_spine[iu + 1][1] - raw_spine[iu - 1][1]
                dz = raw_spine[iu + 1][2] - raw_spine[iu - 1][2]
            ln = math.hypot(dr, dz) + 1e-8
            nr, nz = -dz / ln, dr / ln
            if nz < 0:
                nr, nz = -nr, -nz

            half_w = _leaf_width(u)
            thick_center = 0.068 * (1.0 - 0.55 * (u ** 1.15))

            top_row = []
            bot_row = []
            for iv in range(n_v):
                v_norm = -1.0 + 2.0 * (iv / float(n_v - 1))
                av = abs(v_norm)
                lat_offset = v_norm * half_w

                midrib_dip = -0.017 * math.exp(-((av / 0.14) ** 2)) * (1.0 - 0.45 * u)
                side_dome = 0.025 * math.sin(av * math.pi) * (1.0 - 0.30 * u)

                vein_relief = 0.0
                for vk in range(4):
                    vu0 = 0.16 + vk * 0.175
                    v_curve = vu0 + 0.24 * (av ** 1.28)
                    vein_relief -= (
                        0.0055
                        * math.exp(-(((u - v_curve) / 0.026) ** 2))
                        * (1.0 - av * 0.85)
                        * min(1.0, av / 0.12)
                    )

                shoulder_wrap = -0.036 * (av * av) * (1.0 - 0.45 * u)
                edge_profile = math.sqrt(max(0.05, 1.0 - 0.90 * (av * av)))
                half_th = 0.5 * thick_center * edge_profile

                r_local = r_s - 0.030 * (av * av) * (1.0 - 0.4 * u)
                z_mid = z_s + shoulder_wrap

                p_base = dir_r * r_local + dir_t * lat_offset + Vector((0.0, 0.0, z_mid))
                n_vec = dir_r * nr + Vector((0.0, 0.0, nz))

                p_top = p_base + n_vec * (half_th + midrib_dip + side_dome + vein_relief)
                p_bot = p_base - n_vec * (half_th * 0.85)

                top_row.append(bm.verts.new(p_top * SCALE))
                bot_row.append(bm.verts.new(p_bot * SCALE))
            top_grid.append(top_row)
            bot_grid.append(bot_row)

        for iu in range(n_u - 1):
            v0 = iu / float(n_u - 1)
            v1 = (iu + 1) / float(n_u - 1)
            for iv in range(n_v - 1):
                u0 = iv / float(n_v - 1)
                u1 = (iv + 1) / float(n_v - 1)
                f = bm.faces.new((
                    top_grid[iu][iv],
                    top_grid[iu + 1][iv],
                    top_grid[iu + 1][iv + 1],
                    top_grid[iu][iv + 1],
                ))
                f.loops[0][uv_layer].uv = (u0, v0)
                f.loops[1][uv_layer].uv = (u0, v1)
                f.loops[2][uv_layer].uv = (u1, v1)
                f.loops[3][uv_layer].uv = (u1, v0)

                fb = bm.faces.new((
                    bot_grid[iu][iv],
                    bot_grid[iu][iv + 1],
                    bot_grid[iu + 1][iv + 1],
                    bot_grid[iu + 1][iv],
                ))
                fb.loops[0][uv_layer].uv = (u0, v0)
                fb.loops[1][uv_layer].uv = (u1, v0)
                fb.loops[2][uv_layer].uv = (u1, v1)
                fb.loops[3][uv_layer].uv = (u0, v1)

        for iu in range(n_u - 1):
            v0 = iu / float(n_u - 1)
            v1 = (iu + 1) / float(n_u - 1)
            fl = bm.faces.new((top_grid[iu][0], bot_grid[iu][0], bot_grid[iu + 1][0], top_grid[iu + 1][0]))
            for lp in fl.loops:
                lp[uv_layer].uv = (0.0, 0.5 * (v0 + v1))
            fr = bm.faces.new((top_grid[iu][-1], top_grid[iu + 1][-1], bot_grid[iu + 1][-1], bot_grid[iu][-1]))
            for lp in fr.loops:
                lp[uv_layer].uv = (1.0, 0.5 * (v0 + v1))

        for iv in range(n_v - 1):
            u_mid = (iv + 0.5) / float(n_v - 1)
            fb_cap = bm.faces.new((top_grid[0][iv], top_grid[0][iv + 1], bot_grid[0][iv + 1], bot_grid[0][iv]))
            for lp in fb_cap.loops:
                lp[uv_layer].uv = (u_mid, 0.0)
            ft_cap = bm.faces.new((top_grid[-1][iv], bot_grid[-1][iv], bot_grid[-1][iv + 1], top_grid[-1][iv + 1]))
            for lp in ft_cap.loops:
                lp[uv_layer].uv = (u_mid, 1.0)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("StrawberryLamp_Calyx_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    _set_smooth(mesh)

    obj = bpy.data.objects.new("StrawberryLamp_Calyx", mesh)
    collection.objects.link(obj)

    sub = obj.modifiers.new("Subsurf", "SUBSURF")
    sub.levels = 1
    sub.render_levels = 2
    return obj


def _add_lathe(bm, profile_rz, n_seg=64):
    rings = []
    for r, z in profile_rz:
        if r <= 1e-6:
            rings.append([bm.verts.new(Vector((0.0, 0.0, z)) * SCALE)])
        else:
            ring = []
            for i in range(n_seg):
                a = (2.0 * math.pi * i) / n_seg
                ring.append(bm.verts.new(Vector((r * math.cos(a), r * math.sin(a), z)) * SCALE))
            rings.append(ring)

    for i in range(len(rings) - 1):
        ra, rb = rings[i], rings[i + 1]
        if len(ra) == 1 and len(rb) > 1:
            for s in range(n_seg):
                sn = (s + 1) % n_seg
                bm.faces.new((ra[0], rb[sn], rb[s]))
        elif len(ra) > 1 and len(rb) == 1:
            for s in range(n_seg):
                sn = (s + 1) % n_seg
                bm.faces.new((ra[s], ra[sn], rb[0]))
        elif len(ra) > 1 and len(rb) > 1:
            for s in range(n_seg):
                sn = (s + 1) % n_seg
                bm.faces.new((ra[s], ra[sn], rb[sn], rb[s]))


def build_top_collar_and_ring(collection):
    """Two-tier antique gold collar + compact bail clasp + chunky hanging ring in XZ plane."""
    bm = bmesh.new()

    z0 = H_BODY + 0.016
    collar_profile = [
        (0.000, z0 - 0.05),
        (0.245, z0 - 0.05),
        (0.268, z0 - 0.025),
        (0.272, z0 + 0.052),
        (0.264, z0 + 0.078),
        (0.240, z0 + 0.092),
        (0.180, z0 + 0.096),
        (0.172, z0 + 0.106),
        (0.170, z0 + 0.162),
        (0.156, z0 + 0.178),
        (0.115, z0 + 0.185),
        (0.000, z0 + 0.188),
    ]
    _add_lathe(bm, collar_profile, n_seg=64)

    z_ring_bot = z0 + 0.176
    r_major = 0.278
    r_tube = 0.068
    z_ring_center = z_ring_bot + r_major - 0.015

    n_maj = 64
    n_min = 28
    torus_rings = []
    for i in range(n_maj):
        u = (2.0 * math.pi * i) / n_maj
        cu, su = math.cos(u), math.sin(u)
        center = Vector((r_major * cu, 0.0, z_ring_center + r_major * su))
        rad_out = Vector((cu, 0.0, su))
        side_y = Vector((0.0, 1.0, 0.0))
        ring = []
        for j in range(n_min):
            v = (2.0 * math.pi * j) / n_min
            p = center + (rad_out * math.cos(v) + side_y * math.sin(v)) * r_tube
            ring.append(bm.verts.new(p * SCALE))
        torus_rings.append(ring)

    for i in range(n_maj):
        ra = torus_rings[i]
        rb = torus_rings[(i + 1) % n_maj]
        for j in range(n_min):
            jn = (j + 1) % n_min
            bm.faces.new((ra[j], rb[j], rb[jn], ra[jn]))

    ferrule_mat = (
        Matrix.Translation(Vector((0.0, 0.0, (z_ring_bot - 0.008) * SCALE)))
        @ Matrix.Rotation(math.pi * 0.5, 4, "Y")
        @ Matrix.Diagonal((0.92, 1.04, 1.0, 1.0))
    )
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=32,
        radius1=0.084 * SCALE,
        radius2=0.084 * SCALE,
        depth=0.16 * SCALE,
        matrix=ferrule_mat,
    )

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("StrawberryLamp_GoldCapRing_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    _set_smooth(mesh)

    obj = bpy.data.objects.new("StrawberryLamp_GoldCapRing", mesh)
    collection.objects.link(obj)
    return obj


def build_magic_motes(collection):
    """
    Create ~195 magical floating glowing golden firefly/fairy motes suspended inside the
    hollow glass chamber: rich shimmering golden cluster in the lower-central heart,
    tapering gracefully into drifting fairy stardust up through the rosy pink lobes.
    """
    rng = random.Random(20261125)
    tiers = [
        ("StrawberryLamp_MagicMotes_Bright", 32, (0.018, 0.030)),
        ("StrawberryLamp_MagicMotes_Gold", 75, (0.012, 0.022)),
        ("StrawberryLamp_MagicMotes_Dust", 90, (0.007, 0.013)),
    ]

    created = []
    for name, count, (r_min, r_max) in tiers:
        bm = bmesh.new()
        placed = 0
        attempts = 0
        while placed < count and attempts < count * 25:
            attempts += 1
            if rng.random() < 0.78:
                # Dense golden fairy cluster in lower half (t ~ 0.04..0.54)
                t = rng.betavariate(1.5, 3.1) * 0.56 + 0.04
            else:
                # Delicate rising stardust drifting up to t ~ 0.80
                t = rng.uniform(0.42, 0.80)

            theta = rng.uniform(0.0, 2.0 * math.pi)
            r_wall = valley_radius(t) * 0.84
            if r_wall < 0.04:
                continue

            # Slightly denser toward inner-mid heart in lower third, spreading out gracefully
            frac_r = rng.random() ** 0.62
            r = max(0.0, frac_r * (r_wall - r_max * 1.4))

            x = r * math.cos(theta)
            y = r * math.sin(theta)
            z = body_z(t)
            rad = rng.uniform(r_min, r_max)

            bmesh.ops.create_icosphere(
                bm,
                subdivisions=2,
                radius=rad * SCALE,
                matrix=Matrix.Translation(Vector((x, y, z)) * SCALE),
            )
            placed += 1

        mesh = bpy.data.meshes.new(name + "_Mesh")
        bm.to_mesh(mesh)
        bm.free()
        _set_smooth(mesh)
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        created.append(obj)

    return created


# ---------------------------------------------------------------------------
# Materials (physically calibrated linear colors for Blender 5.3 + AgX)
# ---------------------------------------------------------------------------
def create_gold_material():
    mat = bpy.data.materials.new("M_StrawberryLamp_AntiqueGold")
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 42.0
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Roughness"].default_value = 0.55

    ramp_col = nt.nodes.new("ShaderNodeValToRGB")
    ramp_col.color_ramp.elements[0].position = 0.25
    ramp_col.color_ramp.elements[0].color = srgb(0.76, 0.55, 0.21)
    ramp_col.color_ramp.elements[1].position = 0.78
    ramp_col.color_ramp.elements[1].color = srgb(0.92, 0.73, 0.35)

    ramp_rgh = nt.nodes.new("ShaderNodeMapRange")
    ramp_rgh.inputs["From Min"].default_value = 0.2
    ramp_rgh.inputs["From Max"].default_value = 0.8
    ramp_rgh.inputs["To Min"].default_value = 0.22
    ramp_rgh.inputs["To Max"].default_value = 0.33

    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.025
    bump.inputs["Distance"].default_value = 0.002

    bsdf.inputs["Metallic"].default_value = 0.94
    bsdf.inputs["Coat Weight"].default_value = 0.08
    bsdf.inputs["Coat Roughness"].default_value = 0.20

    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp_col.inputs["Fac"])
    nt.links.new(ramp_col.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(noise.outputs["Fac"], ramp_rgh.inputs["Value"])
    nt.links.new(ramp_rgh.outputs["Result"], bsdf.inputs["Roughness"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def create_leaf_material(col_img, bump_img):
    mat = bpy.data.materials.new("M_StrawberryLamp_CalyxLeaf")
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")

    uv = nt.nodes.new("ShaderNodeTexCoord")

    tex_col = nt.nodes.new("ShaderNodeTexImage")
    tex_col.image = col_img

    tex_bump = nt.nodes.new("ShaderNodeTexImage")
    tex_bump.image = bump_img

    ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
    ao.samples = 16
    ao.inputs["Distance"].default_value = 0.045

    ao_mix = nt.nodes.new("ShaderNodeMix")
    ao_mix.data_type = "RGBA"
    ao_mix.blend_type = "MULTIPLY"
    ao_mix.inputs["Factor"].default_value = 0.48

    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.24
    bump.inputs["Distance"].default_value = 0.003

    bsdf.inputs["Roughness"].default_value = 0.56
    bsdf.inputs["Specular IOR Level"].default_value = 0.28
    bsdf.inputs["Subsurface Weight"].default_value = 0.06
    bsdf.inputs["Subsurface Scale"].default_value = 0.008
    bsdf.inputs["Subsurface Radius"].default_value = (0.35, 0.55, 0.14)
    bsdf.inputs["Sheen Weight"].default_value = 0.16
    bsdf.inputs["Sheen Roughness"].default_value = 0.65

    nt.links.new(uv.outputs["UV"], tex_col.inputs["Vector"])
    nt.links.new(uv.outputs["UV"], tex_bump.inputs["Vector"])
    nt.links.new(tex_col.outputs["Color"], ao_mix.inputs[6])
    nt.links.new(ao.outputs["Color"], ao_mix.inputs[7])
    nt.links.new(ao_mix.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(tex_bump.outputs["Color"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def create_glass_material(vein_img):
    """
    Dreamy frosted translucent strawberry-pink-to-creamy-gold botanical glass shader.
    Roughness ~0.24-0.34 gives soft alabaster/petal-glass diffusion so the glowing
    floating motes read as luminous fairy sparkles while hiding stark back-wire clutter.
    """
    mat = bpy.data.materials.new("M_StrawberryLamp_PetalGlass")
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    translucent = nt.nodes.new("ShaderNodeBsdfTranslucent")
    mix_sh = nt.nodes.new("ShaderNodeMixShader")

    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep_xyz = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep_xyz.inputs["Vector"])

    tex_vein = nt.nodes.new("ShaderNodeTexImage")
    tex_vein.image = vein_img
    sep_vein = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(tc.outputs["UV"], tex_vein.inputs["Vector"])
    nt.links.new(tex_vein.outputs["Color"], sep_vein.inputs["Color"])

    # Creamy-gold bottom -> warm apricot-peach mid -> soft pastel strawberry-rose top
    grad_ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = grad_ramp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = srgb(1.00, 0.88, 0.50)
    e1 = cr.elements.new(0.26)
    e1.color = srgb(1.00, 0.70, 0.48)
    e2 = cr.elements.new(0.56)
    e2.color = srgb(0.98, 0.58, 0.52)
    cr.elements[1].position = 1.0
    cr.elements[1].color = srgb(0.96, 0.53, 0.54)
    nt.links.new(sep_xyz.outputs["Z"], grad_ramp.inputs["Fac"])

    # Subtle thicker-glass rim enrichment at grazing angles
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.34

    rim_tint = nt.nodes.new("ShaderNodeMix")
    rim_tint.data_type = "RGBA"
    rim_tint.blend_type = "MULTIPLY"
    rim_tint.inputs[7].default_value = srgb(0.96, 0.68, 0.63)
    nt.links.new(lw.outputs["Facing"], rim_tint.inputs["Factor"])
    nt.links.new(grad_ramp.outputs["Color"], rim_tint.inputs[6])

    # Delicate ethereal pale-cream botanical veins
    vein_mix = nt.nodes.new("ShaderNodeMix")
    vein_mix.data_type = "RGBA"
    vein_mix.blend_type = "MIX"
    vein_mix.inputs[7].default_value = srgb(1.00, 0.90, 0.86)

    vein_fac = nt.nodes.new("ShaderNodeMath")
    vein_fac.operation = "MULTIPLY"
    vein_fac.inputs[1].default_value = 0.36
    nt.links.new(sep_vein.outputs["Red"], vein_fac.inputs[0])
    nt.links.new(vein_fac.outputs["Value"], vein_mix.inputs["Factor"])
    nt.links.new(rim_tint.outputs[2], vein_mix.inputs[6])

    # Soft misty alabaster marbling
    marble_mix = nt.nodes.new("ShaderNodeMix")
    marble_mix.data_type = "RGBA"
    marble_mix.blend_type = "OVERLAY"
    marble_mix.inputs["Factor"].default_value = 0.12
    nt.links.new(vein_mix.outputs[2], marble_mix.inputs[6])
    nt.links.new(sep_vein.outputs["Green"], marble_mix.inputs[7])

    # Frosted glass roughness (soft dreamy diffusion for interior lights & veins!)
    rgh_base = nt.nodes.new("ShaderNodeMapRange")
    rgh_base.inputs["From Min"].default_value = 0.0
    rgh_base.inputs["From Max"].default_value = 1.0
    rgh_base.inputs["To Min"].default_value = 0.23
    rgh_base.inputs["To Max"].default_value = 0.31
    nt.links.new(sep_vein.outputs["Green"], rgh_base.inputs["Value"])

    rgh_vein_add = nt.nodes.new("ShaderNodeMath")
    rgh_vein_add.operation = "MULTIPLY"
    rgh_vein_add.inputs[1].default_value = 0.12
    nt.links.new(sep_vein.outputs["Red"], rgh_vein_add.inputs[0])

    rgh_final = nt.nodes.new("ShaderNodeMath")
    rgh_final.operation = "ADD"
    rgh_final.use_clamp = True
    nt.links.new(rgh_base.outputs["Result"], rgh_final.inputs[0])
    nt.links.new(rgh_vein_add.outputs["Value"], rgh_final.inputs[1])

    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.045
    bump.inputs["Distance"].default_value = 0.002
    nt.links.new(sep_vein.outputs["Red"], bump.inputs["Height"])

    # Warm creamy-gold lower heart glow fading into rosy pink upper body
    emit_ramp = nt.nodes.new("ShaderNodeValToRGB")
    ec = emit_ramp.color_ramp
    ec.elements[0].position = 0.0
    ec.elements[0].color = srgb(1.00, 0.91, 0.46)
    em1 = ec.elements.new(0.28)
    em1.color = srgb(1.00, 0.68, 0.34)
    ec.elements[1].position = 0.72
    ec.elements[1].color = srgb(0.68, 0.28, 0.24)
    nt.links.new(sep_xyz.outputs["Z"], emit_ramp.inputs["Fac"])

    facing_inv = nt.nodes.new("ShaderNodeMath")
    facing_inv.operation = "SUBTRACT"
    facing_inv.inputs[0].default_value = 1.0
    nt.links.new(lw.outputs["Facing"], facing_inv.inputs[1])

    facing_pow = nt.nodes.new("ShaderNodeMath")
    facing_pow.operation = "POWER"
    facing_pow.inputs[1].default_value = 1.15
    nt.links.new(facing_inv.outputs["Value"], facing_pow.inputs[0])

    z_emit = nt.nodes.new("ShaderNodeMapRange")
    z_emit.clamp = True
    z_emit.inputs["From Min"].default_value = 0.0
    z_emit.inputs["From Max"].default_value = 0.62
    z_emit.inputs["To Min"].default_value = 1.25
    z_emit.inputs["To Max"].default_value = 0.06
    nt.links.new(sep_xyz.outputs["Z"], z_emit.inputs["Value"])

    emit_mul = nt.nodes.new("ShaderNodeMath")
    emit_mul.operation = "MULTIPLY"
    nt.links.new(z_emit.outputs["Result"], emit_mul.inputs[0])
    nt.links.new(facing_pow.outputs["Value"], emit_mul.inputs[1])

    bsdf.inputs["IOR"].default_value = 1.04
    if "Thin Wall" in bsdf.inputs:
        bsdf.inputs["Thin Wall"].default_value = True
    bsdf.inputs["Transmission Weight"].default_value = 0.64
    bsdf.inputs["Subsurface Weight"].default_value = 0.20
    bsdf.inputs["Subsurface Scale"].default_value = 0.014
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.38, 0.26)
    bsdf.inputs["Coat Weight"].default_value = 0.58
    bsdf.inputs["Coat Roughness"].default_value = 0.09

    nt.links.new(marble_mix.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(rgh_final.outputs["Value"], bsdf.inputs["Roughness"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(emit_ramp.outputs["Color"], bsdf.inputs["Emission Color"])
    nt.links.new(emit_mul.outputs["Value"], bsdf.inputs["Emission Strength"])

    nt.links.new(marble_mix.outputs[2], translucent.inputs["Color"])
    nt.links.new(bump.outputs["Normal"], translucent.inputs["Normal"])

    # 15% soft translucent petal-glass scatter so internal warm lights illuminate the lobes evenly
    mix_sh.inputs["Fac"].default_value = 0.15
    nt.links.new(bsdf.outputs["BSDF"], mix_sh.inputs[1])
    nt.links.new(translucent.outputs["BSDF"], mix_sh.inputs[2])
    nt.links.new(mix_sh.outputs["Shader"], out.inputs["Surface"])
    return mat


def create_mote_material(name, color_srgb, strength):
    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = srgb(*color_srgb)
    emit.inputs["Strength"].default_value = strength
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return mat


# ---------------------------------------------------------------------------
# Scene, Lighting & Rendering Setup
# ---------------------------------------------------------------------------
def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def configure_cycles(samples=112):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.refresh_devices()
    for d in prefs.devices:
        d.use = (d.type == "OPTIX")
    scene.cycles.device = "GPU"
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.012
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPTIX"
    scene.cycles.max_bounces = 10
    scene.cycles.diffuse_bounces = 5
    scene.cycles.glossy_bounces = 5
    scene.cycles.transmission_bounces = 10
    scene.cycles.transparent_max_bounces = 10

    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 0.05
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"


def setup_world_and_lights(studio_mode=True):
    scene = bpy.context.scene
    world = bpy.data.worlds.new("World")
    scene.world = world
    nt = world.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg_cam = nt.nodes.new("ShaderNodeBackground")
    bg_env = nt.nodes.new("ShaderNodeBackground")
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix_bg = nt.nodes.new("ShaderNodeMixShader")

    if studio_mode:
        # Bright airy cool-gray studio sheet matching concept art background (#D8DCE2 under AgX)
        bg_cam.inputs["Color"].default_value = srgb(0.84, 0.86, 0.89)
        bg_cam.inputs["Strength"].default_value = 1.48
        bg_env.inputs["Color"].default_value = srgb(0.90, 0.92, 0.96)
        bg_env.inputs["Strength"].default_value = 0.50
    else:
        # Deep cozy Strawberry Hollow twilight forest-night sky
        bg_cam.inputs["Color"].default_value = srgb(0.11, 0.13, 0.22)
        bg_cam.inputs["Strength"].default_value = 1.0
        bg_env.inputs["Color"].default_value = srgb(0.24, 0.30, 0.50)
        bg_env.inputs["Strength"].default_value = 0.28

    nt.links.new(lp.outputs["Is Camera Ray"], mix_bg.inputs["Fac"])
    nt.links.new(bg_env.outputs["Background"], mix_bg.inputs[1])
    nt.links.new(bg_cam.outputs["Background"], mix_bg.inputs[2])
    nt.links.new(mix_bg.outputs["Shader"], out.inputs["Surface"])

    for obj in list(bpy.data.objects):
        if obj.name.startswith("StudioLight_"):
            bpy.data.objects.remove(obj, do_unlink=True)

    def add_area(name, loc, target, energy, size, color=(1.0, 1.0, 1.0)):
        ldata = bpy.data.lights.new(name, type="AREA")
        ldata.energy = energy
        ldata.size = size
        ldata.color = color
        lobj = bpy.data.objects.new(name, ldata)
        scene.collection.objects.link(lobj)
        lobj.location = Vector(loc)
        direction = Vector(target) - lobj.location
        lobj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        return lobj

    center = Vector((0.0, 0.0, 0.92 * SCALE))
    if studio_mode:
        add_area("StudioLight_Key", (1.2, -1.5, 1.5), center, energy=26.0, size=1.4, color=srgb3(1.0, 0.98, 0.95))
        add_area("StudioLight_Fill", (-1.4, -1.1, 0.9), center, energy=15.0, size=1.6, color=srgb3(0.95, 0.97, 1.0))
        add_area("StudioLight_Rim", (0.2, 1.6, 1.3), center, energy=18.0, size=1.3, color=srgb3(1.0, 0.97, 0.93))
        add_area("StudioLight_BottomFill", (0.0, -0.4, -1.3), center, energy=8.0, size=1.4, color=srgb3(1.0, 0.96, 0.90))
    else:
        add_area("StudioLight_MoonRim", (-1.1, 1.3, 1.4), center, energy=24.0, size=1.1, color=srgb3(0.68, 0.80, 1.0))
        add_area("StudioLight_SoftKey", (1.3, -1.4, 1.3), center, energy=11.0, size=1.4, color=srgb3(1.0, 0.92, 0.82))
        add_area("StudioLight_WarmBounce", (0.0, -0.6, -1.0), center, energy=5.0, size=1.2, color=srgb3(1.0, 0.78, 0.45))


def add_internal_lamp_lights(collection):
    """
    Warm golden interior point lights that illuminate the translucent glass shell from inside
    WITHOUT rendering as visible floating lightbulbs through transmission/glossy rays!
    """
    l1 = bpy.data.lights.new("StrawberryLamp_CoreLight", type="POINT")
    l1.energy = 1.05
    l1.shadow_soft_size = 0.045
    l1.color = srgb3(1.0, 0.88, 0.40)
    o1 = bpy.data.objects.new("StrawberryLamp_CoreLight", l1)
    o1.location = Vector((0.0, 0.0, 0.26 * H_BODY)) * SCALE
    # Hide direct bulb sphere in camera/glossy/transmission rays so only the soft glow & motes appear!
    o1.visible_camera = False
    o1.visible_glossy = False
    o1.visible_transmission = False
    collection.objects.link(o1)

    l2 = bpy.data.lights.new("StrawberryLamp_UpperGlowLight", type="POINT")
    l2.energy = 0.35
    l2.shadow_soft_size = 0.065
    l2.color = srgb3(1.0, 0.65, 0.46)
    o2 = bpy.data.objects.new("StrawberryLamp_UpperGlowLight", l2)
    o2.location = Vector((0.0, 0.0, 0.60 * H_BODY)) * SCALE
    o2.visible_camera = False
    o2.visible_glossy = False
    o2.visible_transmission = False
    collection.objects.link(o2)
    return [o1, o2]


def setup_camera(loc, target, lens=65.0, ortho=False, ortho_scale=0.56):
    scene = bpy.context.scene
    if "RenderCam" in bpy.data.objects:
        cam_obj = bpy.data.objects["RenderCam"]
        cam_data = cam_obj.data
    else:
        cam_data = bpy.data.cameras.new("RenderCam")
        cam_obj = bpy.data.objects.new("RenderCam", cam_data)
        scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    cam_obj.location = Vector(loc)
    direction = Vector(target) - cam_obj.location
    if abs(direction.normalized().z) > 0.999:
        if direction.z < 0:
            cam_obj.rotation_euler = Euler((0.0, 0.0, 0.0), "XYZ")
        else:
            cam_obj.rotation_euler = Euler((math.pi, 0.0, 0.0), "XYZ")
    else:
        cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    cam_data.type = "ORTHO" if ortho else "PERSP"
    cam_data.lens = lens
    cam_data.ortho_scale = ortho_scale
    cam_data.clip_start = 0.01
    cam_data.clip_end = 100.0
    return cam_obj


def add_fog_glow_postprocess(img_np: np.ndarray, threshold=0.86, radius=14, strength=0.38) -> np.ndarray:
    rgb = img_np[..., :3].astype(np.float32)
    lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    mask = np.clip((lum - threshold) / max(1e-4, 1.0 - threshold), 0.0, 1.0)
    bright = rgb * (mask * mask)[..., None]

    k_half = int(radius * 2)
    x = np.arange(-k_half, k_half + 1, dtype=np.float32)
    kern = np.exp(-0.5 * (x / float(radius)) ** 2)
    kern /= kern.sum()

    def blur_1d(arr, axis):
        pad = [(0, 0)] * arr.ndim
        pad[axis] = (k_half, k_half)
        padded = np.pad(arr, pad, mode="edge")
        out = np.zeros_like(arr)
        for i, w in enumerate(kern):
            sl = [slice(None)] * arr.ndim
            sl[axis] = slice(i, i + arr.shape[axis])
            out += padded[tuple(sl)] * w
        return out

    glow = blur_1d(blur_1d(bright, axis=1), axis=0)
    out_rgb = np.clip(rgb + glow * strength, 0.0, 1.0)
    return np.concatenate([out_rgb, img_np[..., 3:4]], axis=-1)


def render_view_to_array(filepath, res_x, res_y, bloom_strength=0.36, bloom_threshold=0.88):
    scene = bpy.context.scene
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.resolution_percentage = 100
    scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)

    img = bpy.data.images.load(filepath, check_existing=False)
    arr = np.empty((res_y, res_x, 4), dtype=np.float32)
    img.pixels.foreach_get(arr.ravel())
    bpy.data.images.remove(img)

    if bloom_strength > 0.0:
        arr = add_fog_glow_postprocess(arr, threshold=bloom_threshold, radius=14, strength=bloom_strength)
        _save_rgba_png(arr, filepath, "TempBloomSave", colorspace="sRGB")
        if "TempBloomSave" in bpy.data.images:
            bpy.data.images.remove(bpy.data.images["TempBloomSave"])
    return arr


def build_turnaround_sheet():
    setup_world_and_lights(studio_mode=True)
    tile_w, tile_h = 640, 640

    z_mid_full = 1.20 * SCALE
    z_mid_body = 0.84 * SCALE
    target_full = Vector((0.0, 0.0, z_mid_full))
    target_body = Vector((0.0, 0.0, z_mid_body))

    views = [
        ("front", Vector((0.0, -1.6, z_mid_full)), target_full, True, 0.56),
        ("right", Vector((1.6, 0.0, z_mid_full)), target_full, True, 0.56),
        ("back", Vector((0.0, 1.6, z_mid_full)), target_full, True, 0.56),
        ("top", Vector((0.0, 0.0, 2.0)), target_body, True, 0.50),
        ("bottom", Vector((0.0, 0.0, -1.6)), target_body, True, 0.50),
        ("three_quarter", Vector((0.66, -0.80, z_mid_full + 0.34)), target_full, False, 0.56),
    ]

    tiles = {}
    for name, loc, tgt, is_ortho, o_scale in views:
        setup_camera(loc, tgt, lens=76.0, ortho=is_ortho, ortho_scale=o_scale)
        p = os.path.join(RENDER_DIR, f"view_{name}.png")
        tiles[name] = render_view_to_array(p, tile_w, tile_h, bloom_strength=0.38, bloom_threshold=0.88)

    sheet = np.zeros((tile_h * 2, tile_w * 3, 4), dtype=np.float32)
    sheet[tile_h:tile_h * 2, 0:tile_w] = tiles["front"]
    sheet[tile_h:tile_h * 2, tile_w:tile_w * 2] = tiles["right"]
    sheet[tile_h:tile_h * 2, tile_w * 2:tile_w * 3] = tiles["back"]
    sheet[0:tile_h, 0:tile_w] = tiles["top"]
    sheet[0:tile_h, tile_w:tile_w * 2] = tiles["bottom"]
    sheet[0:tile_h, tile_w * 2:tile_w * 3] = tiles["three_quarter"]

    line_col = np.array([0.70, 0.73, 0.77, 1.0], dtype=np.float32)
    sheet[tile_h - 1:tile_h + 1, :, :] = line_col
    sheet[:, tile_w - 1:tile_w + 1, :] = line_col
    sheet[:, tile_w * 2 - 1:tile_w * 2 + 1, :] = line_col

    sheet_path = os.path.join(OUT_DIR, "StrawberryLamp_Turnaround.png")
    _save_rgba_png(sheet, sheet_path, "StrawberryLamp_Turnaround", colorspace="sRGB")
    if "StrawberryLamp_Turnaround" in bpy.data.images:
        bpy.data.images.remove(bpy.data.images["StrawberryLamp_Turnaround"])
    return sheet_path


def render_hero_beauty():
    """High-res cozy magical twilight render showing the lamp glowing as a light source."""
    setup_world_and_lights(studio_mode=False)
    if "StrawberryLamp_CoreLight" in bpy.data.objects:
        bpy.data.objects["StrawberryLamp_CoreLight"].data.energy = 1.9
    if "StrawberryLamp_UpperGlowLight" in bpy.data.objects:
        bpy.data.objects["StrawberryLamp_UpperGlowLight"].data.energy = 0.55

    z_mid = 1.18 * SCALE
    setup_camera(
        loc=Vector((0.64, -0.80, z_mid + 0.24)),
        target=Vector((0.0, 0.0, z_mid)),
        lens=72.0,
        ortho=False,
    )
    beauty_path = os.path.join(OUT_DIR, "StrawberryLamp_Beauty_Twilight.png")
    render_view_to_array(beauty_path, 1024, 1024, bloom_strength=0.62, bloom_threshold=0.76)

    # Restore studio lighting & camera before saving .blend
    if "StrawberryLamp_CoreLight" in bpy.data.objects:
        bpy.data.objects["StrawberryLamp_CoreLight"].data.energy = 1.05
    if "StrawberryLamp_UpperGlowLight" in bpy.data.objects:
        bpy.data.objects["StrawberryLamp_UpperGlowLight"].data.energy = 0.35
    setup_world_and_lights(studio_mode=True)
    setup_camera(
        loc=Vector((0.66, -0.82, z_mid + 0.28)),
        target=Vector((0.0, 0.0, z_mid)),
        lens=72.0,
        ortho=False,
    )
    return beauty_path


def main():
    clear_scene()
    configure_cycles(samples=112)

    lamp_col = bpy.data.collections.new("StrawberryLamp")
    bpy.context.scene.collection.children.link(lamp_col)

    root = bpy.data.objects.new("StrawberryLamp_Root", None)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.08
    lamp_col.objects.link(root)

    vein_img = generate_glass_vein_texture()
    leaf_col_img, leaf_bump_img = generate_leaf_textures()

    mat_gold = create_gold_material()
    mat_leaf = create_leaf_material(leaf_col_img, leaf_bump_img)
    mat_glass = create_glass_material(vein_img)
    # Warm golden-cream fairy fireflies (vivid gold halo + luminous core under AgX)
    mat_mote_bright = create_mote_material("M_StrawberryLamp_MoteBright", (1.00, 0.94, 0.50), 28.0)
    mat_mote_gold = create_mote_material("M_StrawberryLamp_MoteGold", (1.00, 0.84, 0.26), 18.0)
    mat_mote_dust = create_mote_material("M_StrawberryLamp_MoteDust", (1.00, 0.74, 0.18), 11.0)

    glass_obj = build_glass_body(lamp_col)
    glass_obj.data.materials.append(mat_glass)

    ribs_obj = build_golden_ribs_and_finial(lamp_col)
    ribs_obj.data.materials.append(mat_gold)

    calyx_obj = build_calyx_leaves(lamp_col)
    calyx_obj.data.materials.append(mat_leaf)

    cap_obj = build_top_collar_and_ring(lamp_col)
    cap_obj.data.materials.append(mat_gold)

    mote_objs = build_magic_motes(lamp_col)
    for obj, m in zip(mote_objs, [mat_mote_bright, mat_mote_gold, mat_mote_dust]):
        obj.data.materials.append(m)

    lights = add_internal_lamp_lights(lamp_col)

    for o in [glass_obj, ribs_obj, calyx_obj, cap_obj] + mote_objs + lights:
        o.parent = root

    sheet_path = build_turnaround_sheet()
    beauty_path = render_hero_beauty()

    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

    # Print clean mesh & material stats
    depsgraph = bpy.context.evaluated_depsgraph_get()
    total_verts = 0
    total_tris = 0
    print("MESH_STATS:")
    for o in [glass_obj, ribs_obj, calyx_obj, cap_obj] + mote_objs:
        ev = o.evaluated_get(depsgraph)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        v_cnt = len(me.vertices)
        t_cnt = len(me.loop_triangles)
        total_verts += v_cnt
        total_tris += t_cnt
        print(f"  {o.name}: {v_cnt} verts, {t_cnt} tris")
        ev.to_mesh_clear()
    print(f"  TOTAL: {total_verts} verts, {total_tris} tris")
    print("SUCCESS:")
    print("  BLEND:", BLEND_PATH)
    print("  TURNAROUND:", sheet_path)
    print("  BEAUTY:", beauty_path)


if __name__ == "__main__":
    main()
