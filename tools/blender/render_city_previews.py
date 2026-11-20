import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from PIL import Image

ROOT = "/workspace/zombie-survival-3d"
BLEND = f"{ROOT}/assets/models/environment/city_district_01.blend"
OUT = f"{ROOT}/previews/city"
os.makedirs(OUT, exist_ok=True)

SHOT_LIST = [
    ("aerial_34", (-150, -165, 135), (0, 0, 6), 40, 260, 72, 760),
    ("plaza_fog", (26, -44, 1.9), (0, 0, 2.5), 6, 90, 48, 640),
    ("street_barricade", (23, -16, 1.7), (25, 10, 0.8), 4, 70, 48, 640),
    ("cinema_front", (12, -126, 2.2), (0, -98, 4.0), 12, 110, 48, 640),
    ("hospital_front", (26, 52, 2.4), (0, 78, 6.0), 12, 110, 48, 640),
    ("church_34", (-24, -92, 2.4), (-4, -90, 9.0), 12, 100, 48, 640),
    ("gas_station", (-90, 22, 2.2), (-90, 2, 4.5), 6, 60, 48, 640),
    ("radio_tower", (62, 26, 2.0), (44, 44, 12.0), 6, 60, 48, 640),
]

SENSOR_W = 36.0


def aim(cam_obj, target):
    d = Vector(target) - Vector(cam_obj.location)
    cam_obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def build_bvh():
    depsgraph = bpy.context.evaluated_depsgraph_get()
    trees = []
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH' or obj.hide_render:
            continue
        trees.append(BVHTree.FromObject(obj.evaluated_get(depsgraph), depsgraph))
    print("BVH trees:", len(trees))
    return trees


def depth_map(trees, cam_obj, W, H):
    mw = cam_obj.matrix_world
    right = Vector(mw.col[0][:3]).normalized()
    up = Vector(mw.col[1][:3]).normalized()
    fwd = -Vector(mw.col[2][:3]).normalized()
    tan_h = (SENSOR_W * 0.5) / 35.0
    origin = Vector(mw.translation)
    dist = np.full((H, W), 1e9, dtype=np.float32)
    for row in range(H):
        vy = 1.0 - 2.0 * (row + 0.5) / H
        for col in range(W):
            u = 2.0 * (col + 0.5) / W - 1.0
            d = (fwd + right * (u * tan_h) + up * (vy * tan_h)).normalized()
            best = 1e9
            for t in trees:
                hit = t.ray_cast(origin, d)
                if hit[0] is not None and hit[3] < best:
                    best = hit[3]
            dist[row, col] = best
    return dist


def mist_factor(dist, start, depth):
    f = (dist - start) / float(depth)
    f = np.clip(f, 0.0, 1.0)
    return f * f


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.use_denoising = True
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.6

    world = bpy.data.worlds.new("CityWorld")
    world.use_nodes = True
    scene.world = world
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.62, 0.66, 0.72, 1.0)
    bg.inputs[1].default_value = 1.6

    sun = bpy.data.lights.new("CitySun", type='SUN')
    sun.energy = 5.0
    sun.angle = 0.5
    sun.color = (0.88, 0.9, 0.95)
    sun_obj = bpy.data.objects.new("CitySun", sun)
    bpy.context.collection.objects.link(sun_obj)
    sun_obj.rotation_euler = (math.radians(-48), 0, math.radians(35))

    hemi = bpy.data.lights.new("Hemi", type='AREA')
    hemi.energy = 3000
    hemi.size = 140
    hemi.color = (0.7, 0.75, 0.85)
    hemi_obj = bpy.data.objects.new("Hemi", hemi)
    bpy.context.collection.objects.link(hemi_obj)
    hemi_obj.location = (0, 0, 80)
    hemi_obj.rotation_euler = (0, 0, 0)

    cam = bpy.data.cameras.new("CityCam")
    cam.lens = 35
    cam_obj = bpy.data.objects.new("CityCam", cam)
    bpy.context.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    trees = build_bvh()
    FOGB = np.array([0.72, 0.76, 0.82], dtype=np.float32)

    only = set(a for a in sys.argv[sys.argv.index("--") + 1:] if not a.startswith("-") and a != "") if "--" in sys.argv else None
    for name, pos, target, start, depth, samples, res in SHOT_LIST:
        if only and name not in only:
            continue
        scene.cycles.samples = samples
        scene.render.resolution_x = res
        scene.render.resolution_y = res
        cam_obj.location = pos
        cam.lens = 50 if name == "aerial_34" else 35
        aim(cam_obj, target)
        scene.render.filepath = "/tmp/_fog_base.png"
        bpy.ops.render.render(write_still=True)
        img = np.asarray(Image.open("/tmp/_fog_base.png").convert("RGB"), dtype=np.float32) / 255.0
        H, W = img.shape[0], img.shape[1]
        dist = depth_map(trees, cam_obj, W, H)
        f = mist_factor(dist, start, depth)[..., None]
        out = img * (1.0 - f) + FOGB * f
        out = np.clip(out * 255.0, 0, 255).astype(np.uint8)
        Image.fromarray(out).save(os.path.join(OUT, f"{name}.png"))
        print("RENDERED:", name, "fog_mean_f:", round(float(f.mean()), 3))


main()
