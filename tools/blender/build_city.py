import json
import math
import random

import bpy

ROOT = "/workspace/zombie-survival-3d"
OUT_GLB = f"{ROOT}/assets/models/environment/city_district_01.glb"
OUT_BLEND = f"{ROOT}/assets/models/environment/city_district_01.blend"

random.seed(7)

STREET_W = 8.0
BLOCK = 36.0
PITCH = BLOCK + STREET_W
GRID = 5
WALL_T = 0.25
BASE_Z = 0.12

bpy_mesh_stats = {"objects": 0}


def mat(name, color, rough=0.9, metal=0.0, emissive=None, strength=1.5):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emissive:
        b.inputs["Emission Color"].default_value = (*emissive, 1.0)
        b.inputs["Emission Strength"].default_value = strength
    return m


M = {}


def init_materials():
    global M
    M = {
    "asphalt": mat("asphalt", (0.045, 0.045, 0.05), 0.96),
    "sidewalk": mat("sidewalk", (0.34, 0.34, 0.35), 0.95),
    "marking": mat("marking", (0.80, 0.80, 0.75), 0.8),
    "brick": mat("brick", (0.42, 0.23, 0.16), 0.92),
    "concrete": mat("concrete", (0.52, 0.51, 0.49), 0.93),
    "tan": mat("tan", (0.62, 0.52, 0.40), 0.92),
    "pastel": mat("pastel", (0.42, 0.52, 0.58), 0.92),
    "sage": mat("sage", (0.47, 0.54, 0.44), 0.92),
    "roof": mat("roof", (0.10, 0.10, 0.11), 0.95),
    "glass": mat("glass", (0.06, 0.10, 0.13), 0.25, 0.6),
    "door_wood": mat("door_wood", (0.30, 0.19, 0.10), 0.85),
    "door_metal": mat("door_metal", (0.25, 0.28, 0.30), 0.6, 0.7),
    "metal": mat("metal", (0.28, 0.30, 0.32), 0.5, 0.8),
    "fence": mat("fence", (0.33, 0.35, 0.38), 0.55, 0.7),
    "wood": mat("wood", (0.33, 0.21, 0.10), 0.9),
    "foliage": mat("foliage", (0.11, 0.22, 0.10), 0.95),
    "trunk": mat("trunk", (0.23, 0.15, 0.09), 0.95),
    "water": mat("water", (0.13, 0.28, 0.36), 0.15),
    "cone": mat("cone", (0.85, 0.28, 0.04), 0.8),
    "dumpster": mat("dumpster", (0.13, 0.27, 0.16), 0.85),
    "sandbag": mat("sandbag", (0.55, 0.47, 0.31), 0.95),
    "car_red": mat("car_red", (0.35, 0.08, 0.07), 0.5, 0.6),
    "car_gray": mat("car_gray", (0.28, 0.29, 0.30), 0.5, 0.6),
    "car_blue": mat("car_blue", (0.07, 0.12, 0.24), 0.5, 0.6),
    "car_white": mat("car_white", (0.62, 0.62, 0.60), 0.5, 0.6),
    "car_taxi": mat("car_taxi", (0.65, 0.45, 0.05), 0.5, 0.6),
    "tire": mat("tire", (0.03, 0.03, 0.03), 0.95),
    "sign_cinema": mat("sign_cinema", (0.85, 0.15, 0.40), 0.4, emissive=(0.95, 0.10, 0.35), strength=2.2),
    "sign_hospital": mat("sign_hospital", (0.80, 0.04, 0.04), 0.4, emissive=(0.85, 0.02, 0.02), strength=2.2),
    "sign_gas": mat("sign_gas", (0.85, 0.4, 0.04), 0.4, emissive=(0.9, 0.35, 0.02), strength=1.8),
    "lamp_on": mat("lamp_on", (0.9, 0.8, 0.6), 0.4, emissive=(1.0, 0.85, 0.6), strength=2.0),
    "antenna_red": mat("antenna_red", (0.7, 0.05, 0.05), 0.4, emissive=(0.9, 0.05, 0.05), strength=2.5),
}


def box(cx, cy, cz, dx, dy, dz, mkey, rot_z=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz))
    obj = bpy.context.active_object
    obj.scale = (dx, dy, dz)
    obj.rotation_euler = (0, 0, rot_z)
    obj.data.materials.append(M[mkey])
    bpy_mesh_stats["objects"] += 1
    return obj


def cyl(cx, cy, cz, r, depth, mkey, verts=12, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=(cx, cy, cz))
    obj = bpy.context.active_object
    obj.rotation_euler = rot
    obj.data.materials.append(M[mkey])
    bpy_mesh_stats["objects"] += 1
    return obj


def ground():
    box(0, 0, -0.05, 300, 300, 0.1, "asphalt")


def sidewalk_plates():
    for gx in range(GRID):
        for gy in range(GRID):
            box((gx - 2) * PITCH, (gy - 2) * PITCH, 0.06, BLOCK, BLOCK, 0.12, "sidewalk")


def road_markings():
    for k in range(GRID - 1):
        s = (k - 1.5) * PITCH
        for t in range(GRID):
            c = (t - 2) * PITCH
            for seg in range(9):
                p = c - BLOCK / 2 + 3.0 + seg * 4.0
                if abs(p - s) < 5:
                    continue
                box(s, p, 0.006, 0.14, 2.0, 0.04, "marking")
                box(p, s, 0.006, 2.0, 0.14, 0.04, "marking")


def crosswalks():
    for i in range(5):
        for j in range(5):
            ix, iy = (i - 2) * PITCH, (j - 2) * PITCH
            for k in range(5):
                off = -STREET_W / 2 + 1.0 + k * 1.5
                box(ix + off, iy - BLOCK / 2 - STREET_W / 2 + 1.3, 0.006, 0.7, 2.4, 0.04, "marking")
                box(ix + off, iy + BLOCK / 2 + STREET_W / 2 - 1.3, 0.006, 0.7, 2.4, 0.04, "marking")
                box(ix - BLOCK / 2 - STREET_W / 2 + 1.3, iy + off, 0.006, 2.4, 0.7, 0.04, "marking")
                box(ix + BLOCK / 2 + STREET_W / 2 - 1.3, iy + off, 0.006, 2.4, 0.7, 0.04, "marking")


def wall_nc(x, y, z, length, along_x, mkey):
    if along_x:
        return box(x, y, z, length, WALL_T, 1.0 * 1 if False else 0)
    return box(x, y, z, WALL_T, length, 0)


def wall_at(x, y, z, dx, dy, mkey):
    return box(x, y, z, dx, dy, 1.0, mkey)


def facade_plain(cx, cy, w, d, wall_h, mkey, skip=None):
    walls = {
        "-X": box(cx - w / 2, cy, BASE_Z + wall_h / 2, WALL_T, d, wall_h, mkey),
        "+X": box(cx + w / 2, cy, BASE_Z + wall_h / 2, WALL_T, d, wall_h, mkey),
        "-Y": box(cx, cy - d / 2, BASE_Z + wall_h / 2, w, WALL_T, wall_h, mkey),
        "+Y": box(cx, cy + d / 2, BASE_Z + wall_h / 2, w, WALL_T, wall_h, mkey),
    }
    return [v for k, v in walls.items() if k != skip]


def facade_door_wall(cx, cy, w, d, wall_h, face, door_w, door_h, mkey, door_mkey):
    objs = []
    seg = (w - door_w) / 2
    header_h = wall_h - door_h
    if face == "+Y":
        wy = cy + d / 2
        objs.append(box(cx - w / 2 + seg / 2, wy, BASE_Z + wall_h / 2, seg, WALL_T, wall_h, mkey))
        objs.append(box(cx + w / 2 - seg / 2, wy, BASE_Z + wall_h / 2, seg, WALL_T, wall_h, mkey))
        objs.append(box(cx, wy, BASE_Z + door_h + header_h / 2, door_w, WALL_T, header_h, mkey))
        objs.append(box(cx, wy + WALL_T, BASE_Z + door_h / 2, door_w, 0.06, door_h, door_mkey))
    elif face == "-Y":
        wy = cy - d / 2
        objs.append(box(cx - w / 2 + seg / 2, wy, BASE_Z + wall_h / 2, seg, WALL_T, wall_h, mkey))
        objs.append(box(cx + w / 2 - seg / 2, wy, BASE_Z + wall_h / 2, seg, WALL_T, wall_h, mkey))
        objs.append(box(cx, wy, BASE_Z + door_h + header_h / 2, door_w, WALL_T, header_h, mkey))
        objs.append(box(cx, wy - WALL_T, BASE_Z + door_h / 2, door_w, 0.06, door_h, door_mkey))
    else:
        wx = cx + (w / 2 if face == "+X" else -w / 2)
        sgn = 1 if face == "+X" else -1
        seg_d = (d - door_w) / 2
        objs.append(box(wx, cy - d / 2 + seg_d / 2, BASE_Z + wall_h / 2, WALL_T, seg_d, wall_h, mkey))
        objs.append(box(wx, cy + d / 2 - seg_d / 2, BASE_Z + wall_h / 2, WALL_T, seg_d, wall_h, mkey))
        objs.append(box(wx, cy, BASE_Z + door_h + header_h / 2, WALL_T, door_w, header_h, mkey))
        objs.append(box(wx + WALL_T * sgn, cy, BASE_Z + door_h / 2, 0.06, door_w, door_h, door_mkey))
    return objs


def window_bands(cx, cy, w, d, floors, mkey):
    objs = []
    for fl in range(floors):
        z = BASE_Z + 1.1 + fl * 3.4
        nx = max(2, int(w / 3.2))
        for i in range(nx):
            off = -w / 2 + (i + 0.5) * (w / nx)
            objs.append(box(cx + off, cy + d / 2, z, 1.5, 0.08, 1.1, mkey))
        for i in range(nx):
            off = -w / 2 + (i + 0.5) * (w / nx)
            objs.append(box(cx + off, cy - d / 2, z, 1.5, 0.08, 1.1, mkey))
    return objs


def build_house(cx, cy, w, d, wall_h, mkey, face, enterable):
    objs = []
    if enterable:
        objs += facade_door_wall(cx, cy, w, d, wall_h, face, 1.5, 2.4, mkey, "door_wood")
        objs += facade_plain(cx, cy, w, d, wall_h, mkey, skip=face)
        objs.append(box(cx, cy, BASE_Z + 0.04, w - 0.5, d - 0.5, 0.1, "concrete"))
    else:
        objs += facade_plain(cx, cy, w, d, wall_h, mkey)
    objs.append(box(cx, cy, BASE_Z + wall_h + 0.15, w + 0.5, d + 0.5, 0.3, "roof"))
    objs += window_bands(cx, cy, w, d, 1, "glass")
    return objs


def build_apartment(cx, cy, w, d, floors, mkey):
    wall_h = floors * 3.4
    objs = facade_plain(cx, cy, w, d, wall_h, mkey)
    objs.append(box(cx, cy, BASE_Z + 0.04, w - 0.5, d - 0.5, 0.1, "concrete"))
    objs.append(box(cx, cy, BASE_Z + wall_h + 0.2, w + 0.5, d + 0.5, 0.4, "roof"))
    objs += window_bands(cx, cy, w, d, floors, "glass")
    return objs


def build_hospital(cx, cy):
    w, d, wall_h = 22, 14, 12
    objs = facade_plain(cx, cy, w, d, wall_h, "concrete")
    objs.append(box(cx, cy, BASE_Z + 0.04, w - 0.5, d - 0.5, 0.1, "concrete"))
    objs.append(box(cx, cy, BASE_Z + wall_h + 0.2, w + 0.5, d + 0.5, 0.4, "roof"))
    objs.append(box(cx - 2.2, cy + d / 2 + 0.1, BASE_Z + wall_h + 1.2, 4.5, 0.2, 1.1, "sign_hospital"))
    objs.append(box(cx, cy + d / 2 + 0.1, BASE_Z + wall_h + 1.2, 1.4, 0.2, 3.5, "sign_hospital"))
    objs += window_bands(cx, cy, w, d, 3, "glass")
    objs.append(box(cx, cy + d / 2, BASE_Z + 1.25, 2.5, WALL_T, 2.5, "door_metal"))
    return objs


def build_cinema(cx, cy):
    w, d, wall_h = 20, 14, 9
    objs = facade_door_wall(cx, cy, w, d, wall_h, "-Y", 3.0, 3.2, "brick", "door_metal")
    objs += facade_plain(cx, cy, w, d, wall_h, "brick", skip="-Y")
    objs.append(box(cx, cy, BASE_Z + 0.04, w - 0.5, d - 0.5, 0.1, "concrete"))
    objs.append(box(cx, cy, BASE_Z + wall_h + 0.2, w + 0.5, d + 0.5, 0.4, "roof"))
    objs.append(box(cx, cy + d / 2 + 0.6, BASE_Z + wall_h + 0.9, 14, 1.0, 2.0, "sign_cinema"))
    objs += window_bands(cx, cy, w, d, 1, "glass")
    return objs


def build_church(cx, cy):
    dz = BASE_Z
    h_body = 7.0
    objs = [
        box(cx - 5, cy, dz + h_body / 2, WALL_T + 0.1, 14, h_body, "concrete"),
        box(cx + 5, cy, dz + h_body / 2, WALL_T + 0.1, 14, h_body, "concrete"),
        box(cx, cy + 7, dz + h_body / 2, 10.35, WALL_T + 0.1, h_body, "concrete"),
        box(cx, cy, dz + 0.05, 10.3, 14, 0.1, "concrete"),
        box(cx, cy, dz + h_body + 0.1, 10.5, 14.3, 0.2, "roof"),
        box(cx, cy - 8.5, dz + 6.0, 4.2, 4.2, 12.0, "concrete"),
        cyl(cx, cy - 8.5, dz + 14.1, 3.5, 4.4, "roof", verts=4),
        box(cx, cy - 10.72, dz + 14.0, 0.14, 0.14, 3.4, "metal"),
        box(cx, cy - 10.72, dz + 14.9, 1.6, 0.14, 0.28, "metal"),
        box(cx, cy - 10.75, dz + 1.6, 1.7, 0.3, 3.2, "door_wood"),
    ]
    return objs


def build_gas_station(cx, cy):
    objs = [
        box(cx, cy - 6, BASE_Z + 2.1, 10, 8, 4.2, "pastel"),
        box(cx, cy - 6, BASE_Z + 4.3, 10.4, 8.4, 0.25, "roof"),
        box(cx, cy - 6 - 4.1, BASE_Z + 1.15, 1.8, 0.1, 2.3, "door_metal"),
        box(cx, cy + 4, BASE_Z + 5.6, 16, 10, 0.4, "concrete"),
        box(cx - 6.5, cy + 2, BASE_Z + 2.8, 0.6, 0.6, 5.4, "metal"),
        box(cx + 6.5, cy + 2, BASE_Z + 2.8, 0.6, 0.6, 5.4, "metal"),
        box(cx, cy + 10, BASE_Z + 5.4, 5.0, 0.25, 1.3, "sign_gas"),
        box(cx - 2.5, cy + 2, BASE_Z + 0.78, 1.2, 1.2, 1.35, "metal"),
        box(cx + 2.5, cy + 2, BASE_Z + 0.78, 1.2, 1.2, 1.35, "metal"),
    ]
    return objs


def build_radio_tower(cx, cy):
    side, h = 3.4, 26
    objs = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            objs.append(box(cx + sx * side / 2, cy + sy * side / 2, BASE_Z + h / 2, 0.35, 0.35, h, "metal"))
    for lvl in range(1, 7):
        z = BASE_Z + lvl * 3.8
        s = side * (1 - lvl * 0.10)
        objs.append(box(cx, cy, z, s, 0.10, 0.12, "metal"))
        objs.append(box(cx, cy, z, 0.10, s, 0.12, "metal"))
    objs.append(cyl(cx, cy, BASE_Z + h + 2.2, 0.12, 4.2, "metal", verts=8))
    objs.append(box(cx, cy, BASE_Z + h + 4.5, 0.4, 0.4, 0.4, "antenna_red"))
    objs.append(cyl(cx, cy, BASE_Z + 0.30, side * 0.8, 0.16, "concrete", verts=14))
    return objs


def build_plaza(cx, cy):
    objs = [
        box(cx, cy, 0.20, 24, 24, 0.16, "sidewalk"),
        cyl(cx, cy, 0.50, 3.6, 0.7, "concrete", verts=16),
        cyl(cx, cy, 0.90, 3.0, 0.20, "water", verts=16),
        cyl(cx, cy, 1.25, 0.8, 1.2, "concrete", verts=12),
        cyl(cx, cy, 2.15, 0.4, 0.6, "concrete", verts=10),
        cyl(cx, cy, 2.75, 0.65, 0.25, "water", verts=12),
    ]
    for ang in range(0, 360, 60):
        a = math.radians(ang)
        tx, ty = cx + 9.0 * math.cos(a), cy + 9.0 * math.sin(a)
        objs.append(cyl(tx, ty, 1.7, 0.18, 2.8, "trunk", verts=8))
        objs.append(cyl(tx, ty, 3.55, 2.1, 2.4, "foliage", verts=8))
        objs.append(cyl(tx, ty, 4.4, 1.3, 1.2, "foliage", verts=8))
        if ang % 120 == 0:
            objs.append(box(tx, ty, 0.66, 0.5, 1.9, 0.10, "wood"))
            objs.append(box(tx, ty - 0.9, 0.88, 0.4, 0.18, 0.38, "wood"))
            objs.append(box(tx, ty + 0.9, 0.88, 0.4, 0.18, 0.38, "wood"))
    return objs


def fence_ring(cx, cy, half, h):
    objs = []
    length = half * 2
    n = int(length / 2.2)
    for i in range(n + 1):
        t = i / max(n, 1)
        for (x, y) in ((cx - half + length * t, cy - half), (cx - half + length * t, cy + half),
                       (cx - half, cy - half + length * t), (cx + half, cy - half + length * t)):
            objs.append(box(x, y, 0.12 + h / 2, 0.08, 0.08, h, "fence"))
    for (x, y) in ((cx, cy - half), (cx, cy + half)):
        objs.append(box(x, y, 0.12 + h - 0.22, length, 0.05, 0.08, "fence"))
        objs.append(box(x, y, 0.12 + h * 0.45, length, 0.05, 0.08, "fence"))
    for (x, y) in ((cx - half, cy), (cx + half, cy)):
        objs.append(box(x, y, 0.12 + h - 0.22, 0.05, length, 0.08, "fence"))
        objs.append(box(x, y, 0.12 + h * 0.45, 0.05, length, 0.08, "fence"))
    return objs


def build_car(x, y, rot_z, color, flipped=False):
    lr, rr = math.cos(rot_z), math.sin(rot_z)

    def rc(ox, oy):
        return (x + ox * lr - oy * rr, y + ox * rr + oy * lr)

    body_l, body_w = 4.2, 1.9
    along_x = rot_z in (0.0, math.pi)
    cx_, cy_ = rc(0, 0)
    box(cx_, cy_, 0.62 if not flipped else 1.1,
        body_l if along_x else body_w, body_w if along_x else body_l,
        0.75, color, rot_z=rot_z)
    cab_ox, cab_oy = rc(-0.2, 0)
    box(cab_ox, cab_oy, 1.28 if not flipped else 0.6,
        2.1 if along_x else 1.8, 1.8 if along_x else 2.1, 0.65, "glass", rot_z=rot_z)
    for oxx in (-1.35, 1.35):
        for oyy in (-0.95, 0.95):
            wx, wy = rc(oxx, oyy)
            cyl(wx, wy, 0.34, 0.34, 0.22, "tire", verts=10,
                rot=(0, math.pi / 2, 0) if along_x else (math.pi / 2, 0, 0))


def street_props():
    objs = []
    car_colors = ["car_red", "car_gray", "car_blue", "car_white", "car_taxi"]
    spots = []
    for k in range(4):
        s = (k - 1.5) * PITCH
        for t in (-2, -1, 0, 1, 2):
            c = t * PITCH
            for lane in (-2.6, 2.6):
                spots.append((s, c + lane, 0))
                spots.append((c + lane, s, math.pi / 2))
    random.shuffle(spots)
    idx = 0
    for x, y, rz in spots[:16]:
        build_car(x, y, rz, car_colors[idx % len(car_colors)], flipped=idx in (3, 10))
        idx += 1

    for bx, by in [(-PITCH * 0.6, -BLOCK / 2 - 3.6), (PITCH * 0.4, BLOCK / 2 + 3.6),
                   (BLOCK / 2 + 3.8, PITCH * 0.2), (-BLOCK / 2 - 3.8, -PITCH * 0.3)]:
        objs.append(box(bx, by, 0.75, 1.8, 1.0, 1.4, "dumpster"))

    for bx, by in [(2.0, -BLOCK / 2 - 3.2), (-6.0, BLOCK / 2 + 3.2), (8.5, 0.5), (-9.5, -PITCH * 0.7)]:
        objs.append(cyl(bx, by, 0.45, 0.35, 0.9, "cone", verts=8))

    barricades = [
        ((-PITCH + 5, PITCH * 1.5), False), ((PITCH - 5, -PITCH * 1.5), False),
        ((PITCH * 0.5 + 4, 8), True), ((PITCH * 0.5 - 7, -8), True),
    ]
    for (bx, by), along_y in barricades:
        for t in (-2.2, 0, 2.2):
            if along_y:
                objs.append(box(bx, by + t, 0.45, 2.4, 1.8, 0.9, "concrete"))
            else:
                objs.append(box(bx + t, by, 0.45, 1.8, 2.4, 0.9, "concrete"))

    for k in range(26):
        ang = random.uniform(0, 6.283)
        rad = random.uniform(20, 105)
        x, y = math.cos(ang) * rad, math.sin(ang) * rad
        gx, gy = round(x / PITCH), round(y / PITCH)
        if abs(x - gx * PITCH) < BLOCK / 2 - 2 and abs(y - gy * PITCH) < BLOCK / 2 - 2:
            continue
        objs.append(box(x, y, 0.5, 0.7, 0.7, 1.0, "sandbag"))

    for gx in range(5):
        for gy in range(5):
            ix, iy = (gx - 2) * PITCH, (gy - 2) * PITCH
            for sgn in (-1, 1):
                px = ix + sgn * (BLOCK / 2 + 0.8)
                py = iy + (BLOCK / 2 - 1.0) * sgn
                objs.append(cyl(px, py, 0.12 + 2.9, 0.09, 5.8, "metal", verts=8))
                objs.append(box(px, py - sgn * 0.75, 5.55, 1.3, 0.5, 0.1, "metal"))
                objs.append(box(px, py - sgn * 1.0, 5.35, 0.5, 0.22, 0.22, "lamp_on"))

    for k in range(45):
        x, y = random.uniform(-105, 105), random.uniform(-105, 105)
        gx, gy = round(x / PITCH), round(y / PITCH)
        if abs(x - gx * PITCH) < BLOCK / 2 - 2 and abs(y - gy * PITCH) < BLOCK / 2 - 2:
            continue
        objs.append(box(x, y, 0.06, random.uniform(0.3, 1.3), random.uniform(0.3, 1.3),
                        random.uniform(0.1, 0.30), "concrete"))

    for tx, ty in [(-PITCH - 6, BLOCK * 0.3), (PITCH + 6, -BLOCK * 0.4),
                   (BLOCK * 0.4, PITCH + 7), (-BLOCK * 0.5, -PITCH - 7)]:
        objs.append(cyl(tx, ty, 1.6, 0.2, 2.8, "trunk", verts=8))
        objs.append(cyl(tx, ty, 3.4, 2.2, 2.4, "foliage", verts=8))

    return objs


def merge_all():
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects[0]
    bpy.ops.object.join()
    mesh = bpy.context.active_object
    mesh.name = "CityStatic"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return mesh


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.preferences.addon_enable(module="io_scene_gltf2")
    init_materials()
    ground()
    sidewalk_plates()
    road_markings()
    crosswalks()

    landmarks = {(0, 0): "plaza", (0, 2): "hospital", (0, -2): "cinema",
                 (2, 0): "church", (-2, 0): "gas", (1, 1): "radio"}

    for gx in range(5):
        for gy in range(5):
            cx, cy = (gx - 2) * PITCH, (gy - 2) * PITCH
            kind = landmarks.get((gx, gy))
            if kind == "plaza":
                build_plaza(cx, cy)
                continue
            if kind == "hospital":
                build_hospital(cx, cy - 10)
                build_house(cx - 8, cy + 10, 12, 10, 3.6, "concrete", "-Y", True)
                continue
            if kind == "cinema":
                build_cinema(cx, cy - 10)
                build_house(cx + 8, cy + 10, 12, 10, 3.6, "tan", "-Y", True)
                continue
            if kind == "church":
                build_church(cx - 4, cy - 4)
                build_house(cx + 9, cy + 11, 11, 9, 3.6, "sage", "-Y", True)
                continue
            if kind == "gas":
                build_gas_station(cx - 2, cy + 2)
                build_house(cx - 9, cy - 10, 11, 9, 3.6, "pastel", "+Y", True)
                continue
            if kind == "radio":
                build_radio_tower(cx, cy)
                fence_ring(cx, cy, 16, 2.2)
                continue

            corners = [(1, 1), (-1, -1)] if (gx + gy) % 2 else [(-1, 1), (1, -1)]
            for si, (sx, sy) in enumerate(corners):
                bx, by = cx + sx * 9, cy + sy * 9
                r = random.random()
                if r < 0.42:
                    build_apartment(bx, by, 13, 11, 3, random.choice(["brick", "concrete", "tan", "pastel"]))
                else:
                    h = 3.6 if r < 0.8 else 4.6
                    build_house(bx, by, 11, 9, h, random.choice(["brick", "tan", "pastel", "sage"]),
                                "+Y" if sy > 0 else "-Y", (gx * 5 + gy + si) % 3 == 0)

    street_props()
    mesh = merge_all()

    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format="GLB", use_selection=False, export_yup=True)

    tris = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
    info = {
        "glb": OUT_GLB,
        "blend": OUT_BLEND,
        "tris": tris,
        "objects_built": bpy_mesh_stats["objects"],
        "objs_left": len(bpy.data.objects),
        "materials": sorted({s.name for s in mesh.material_slots}),
        "size_m": [round(mesh.dimensions.x, 1), round(mesh.dimensions.y, 1), round(mesh.dimensions.z, 1)],
        "enterable_buildings": 9,
    }
    print("CITY_RESULT_JSON:" + json.dumps(info))


main()
