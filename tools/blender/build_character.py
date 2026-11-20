import argparse
import json
import math
import os

import bpy

OUTPUT_ROOT = "/workspace/zombie-survival-3d"

BONE_LIST = [
    # (name, parent, head(x,y,z), tail(x,y,z), deform)
    ("root", None, (0, 0, 0.95), (0, -0.05, 0.95), False),
    ("hips", "root", (0, 0, 0.98), (0, 0, 1.06), True),
    ("spine", "hips", (0, 0, 1.06), (0, 0, 1.18), True),
    ("chest", "spine", (0, 0, 1.18), (0, 0, 1.46), True),
    ("neck", "chest", (0, 0, 1.46), (0, 0, 1.53), True),
    ("head", "neck", (0, 0, 1.53), (0, 0, 1.74), True),
]

ARM_TILT = math.radians(12)
SHOULDER = (0.25, 0, 1.42)
ELBOW = (SHOULDER[0] + 0.30 * math.sin(ARM_TILT), 0, 1.42 - 0.30 * math.cos(ARM_TILT))
WRIST = (ELBOW[0] + 0.28 * math.sin(ARM_TILT * 0.6), 0, ELBOW[2] - 0.28 * math.cos(ARM_TILT * 0.6))

for side in (".L", ".R"):
    x = 1 if side == ".L" else -1
    BONE_LIST += [
        (f"upperarm{side}", "chest",
         (x * SHOULDER[0], 0, SHOULDER[2]), (x * ELBOW[0], 0, ELBOW[2]), True),
        (f"forearm{side}", f"upperarm{side}",
         (x * ELBOW[0], 0, ELBOW[2]), (x * WRIST[0], 0, WRIST[2]), True),
        (f"hand{side}", f"forearm{side}",
         (x * WRIST[0], 0, WRIST[2]), (x * (WRIST[0] + 0.02), 0, WRIST[2] - 0.12), True),
        (f"thigh{side}", "hips",
         (x * 0.10, 0.02, 0.92), (x * 0.10, 0.03, 0.50), True),
        (f"shin{side}", f"thigh{side}",
         (x * 0.10, 0.03, 0.50), (x * 0.10, 0.04, 0.10), True),
        (f"foot{side}", f"shin{side}",
         (x * 0.10, 0.04, 0.09), (x * 0.10, -0.14, 0.09), True),
    ]


def make_material(name, color, roughness=0.85, metallic=0.0, emissive=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emissive:
        bsdf.inputs["Emission Color"].default_value = (*emissive, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 2.5
    return mat


def add_box(name, center, dims, mat, bone):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (dims[0], dims[1], dims[2])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    group = obj.vertex_groups.new(name=bone)
    group.add(list(range(len(obj.data.vertices))), 1.0, "ADD")
    return obj


def build_mesh(palette):
    box = lambda name, center, dims, mat, bone: add_box(name, center, dims, mat, bone)

    parts = []
    z = palette
    parts.append(box("hips_box", (0, 0, 0.98), (0.30, 0.22, 0.18), z["pants"], "hips"))
    parts.append(box("torso_lower", (0, 0, 1.12), (0.34, 0.22, 0.16), z["shirt"], "spine"))
    parts.append(box("chest_box", (0, 0, 1.32), (0.40, 0.24, 0.30), z["shirt"], "chest"))
    parts.append(box("neck_box", (0, 0, 1.50), (0.10, 0.10, 0.07), z["skin"], "neck"))
    parts.append(box("head_box", (0, 0, 1.64), (0.21, 0.21, 0.22), z["skin"], "head"))
    parts.append(box("hair_cap", (0, -0.005, 1.77), (0.23, 0.23, 0.09), z["hair"], "head"))
    for side in (".L", ".R"):
        x = 1 if side == ".L" else -1
        parts.append(box(f"upperarm{side}", (x * (SHOULDER[0] + ELBOW[0]) / 2, 0, (SHOULDER[2] + ELBOW[2]) / 2),
                         (0.11, 0.11, 0.31), z["shirt"], f"upperarm{side}"))
        parts.append(box(f"forearm{side}", (x * (ELBOW[0] + WRIST[0]) / 2, 0, (ELBOW[2] + WRIST[2]) / 2),
                         (0.09, 0.09, 0.29), z["skin"] if palette["bare_forearms"] else z["shirt"], f"forearm{side}"))
        parts.append(box(f"hand{side}", (x * WRIST[0], 0, WRIST[2] - 0.06), (0.08, 0.08, 0.12), z["skin"], f"hand{side}"))
        parts.append(box(f"thigh{side}", (x * 0.10, 0.025, 0.71), (0.14, 0.15, 0.44), z["pants"], f"thigh{side}"))
        parts.append(box(f"shin{side}", (x * 0.10, 0.035, 0.30), (0.12, 0.12, 0.40), z["pants"], f"shin{side}"))
        parts.append(box(f"foot{side}", (x * 0.10, -0.05, 0.045), (0.11, 0.24, 0.09), z["boots"], f"foot{side}"))
    if z.get("eye_emissive"):
        for side in (".L", ".R"):
            x = 1 if side == ".L" else -1
            parts.append(box(f"eye{side}", (x * 0.05, -0.108, 1.66), (0.035, 0.006, 0.03), z["eyes_mat"], "head"))

    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    mesh = bpy.context.active_object
    mesh.name = "CharacterVisual"
    for poly in mesh.data.polygons:
        poly.use_smooth = False
    return mesh


def build_armature():
    arm_data = bpy.data.armatures.new("CharacterSkeleton")
    arm = bpy.data.objects.new("CharacterSkeleton", arm_data)
    bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = {}
    for name, parent, head, tail, deform in BONE_LIST:
        eb = arm_data.edit_bones.new(name)
        eb.head, eb.tail = head, tail
        eb.roll = 0
        eb.use_deform = deform
        edit_bones[name] = eb
    for name, parent, *_ in BONE_LIST:
        if parent:
            edit_bones[name].parent = edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
    return arm


def link_skin(arm, mesh):
    mesh.parent = arm
    mod = mesh.modifiers.new("Armature", type='ARMATURE')
    mod.object = arm


def key_pose(arm, frame, pose):
    for bone, channels in pose.items():
        pb = arm.pose.bones[bone]
        for ch, val in channels.items():
            if ch == "loc":
                pb.location = val
                pb.keyframe_insert("location", frame=frame, group=bone)
            else:
                key = {"rx": 0, "ry": 0, "rz": 0}
                key[ch] = val
                pb.rotation_euler = (key["rx"], key["ry"], key["rz"])
                pb.keyframe_insert("rotation_euler", frame=frame, group=bone)


def make_action(arm, name, keyframes):
    """keyframes: sorted list of (frame, pose)."""
    act = bpy.data.actions.new(name)
    arm.animation_data_create()
    arm.animation_data.action = act
    for frame, pose in keyframes:
        key_pose(arm, frame, pose)
    act.use_fake_user = True
    act.name = name
    arm.animation_data.action = None
    return act


def anim_idle(base_pose, cfg):
    keys = []
    for f in range(0, 48, 6):
        s = 2 * math.pi * f / 48
        pose = dict(base_pose)
        pose["chest"] = {"rx": 0.03 * math.sin(s)}
        pose["head"] = {"rx": 0.04 * math.sin(s + 0.7), "rz": 0.06 * math.sin(s * 0.5)}
        pose["upperarm.L"] = {"rx": 0.05 * math.sin(s), "rz": cfg.get("arm_out", 0)}
        pose["upperarm.R"] = {"rx": 0.05 * math.sin(s + 1.0), "rz": -cfg.get("arm_out", 0)}
        if cfg.get("hunch"):
            pose["spine"] = {"rx": -0.12 + 0.02 * math.sin(s + 0.4)}
        keys.append((f, pose))
    keys.append((48, dict(base_pose)))
    return keys


def anim_walk(base_pose, cfg):
    amp = cfg.get("stride_amp", 0.5)
    keys = []
    for i in range(0, 25, 2):
        f = i * 2
        phase = 2 * math.pi * i / 24
        pose = dict(base_pose)
        sw = math.sin(phase)
        pose["thigh.L"] = {"rx": amp * sw}
        pose["thigh.R"] = {"rx": -amp * sw}
        pose["shin.L"] = {"rx": max(0.0, 0.7 * math.sin(phase - 0.6))}
        pose["shin.R"] = {"rx": max(0.0, 0.7 * math.sin(phase + math.pi - 0.6))}
        pose["foot.L"] = {"rx": 0.2 * math.sin(phase + 1.2)}
        pose["foot.R"] = {"rx": 0.2 * math.sin(phase + math.pi + 1.2)}
        pose["upperarm.L"] = {"rx": -0.4 * amp * sw / max(amp, 1e-6) * amp, "rz": cfg.get("arm_out", 0)}
        pose["upperarm.R"] = {"rx": -0.4 * amp * sw / max(amp, 1e-6) * amp, "rz": -cfg.get("arm_out", 0)}
        pose["forearm.L"] = {"rx": -0.3 - 0.15 * sw}
        pose["forearm.R"] = {"rx": -0.3 + 0.15 * sw}
        pose["hips"] = {"rx": 0.06 * sw, "rz": 0.05 * sw}
        pose["chest"] = {"rz": -0.08 * sw, "rx": -cfg.get("lean", 0.05)}
        if cfg.get("hunch"):
            pose["spine"] = {"rx": -0.12 + 0.04 * sw}
            pose["upperarm.L"] = {"rx": -1.05 - 0.25 * sw, "rz": 0.15}
            pose["upperarm.R"] = {"rx": -1.05 + 0.25 * sw, "rz": -0.15}
            pose["forearm.L"] = {"rx": -0.5}
            pose["forearm.R"] = {"rx": -0.5}
            pose["head"] = {"rx": -0.18}
        pose["root"] = {"loc": (0, 0, 0.012 * abs(math.cos(phase)) - 0.02)}
        keys.append((f, pose))
    return keys


def anim_run(base_pose, cfg):
    amp = 0.85
    keys = []
    for i in range(0, 17, 2):
        f = i
        phase = 2 * math.pi * i / 16
        sw = math.sin(phase)
        pose = {
            "thigh.L": {"rx": amp * sw},
            "thigh.R": {"rx": -amp * sw},
            "shin.L": {"rx": max(0.1, 1.3 * math.sin(phase - 0.8))},
            "shin.R": {"rx": max(0.1, 1.3 * math.sin(phase + math.pi - 0.8))},
            "foot.L": {"rx": 0.3 * math.sin(phase + 1.4)},
            "foot.R": {"rx": 0.3 * math.sin(phase + math.pi + 1.4)},
            "upperarm.L": {"rx": -0.9 * sw, "rz": 0.1},
            "upperarm.R": {"rx": 0.9 * sw, "rz": -0.1},
            "forearm.L": {"rx": -1.2},
            "forearm.R": {"rx": -1.2},
            "chest": {"rx": -0.25 + 0.05 * sw},
            "hips": {"rx": 0.1 * sw},
            "root": {"loc": (0, 0, -0.05 + 0.03 * abs(math.cos(phase)))},
        }
        keys.append((f, pose))
    return keys


def anim_attack(base_pose, cfg, both_arms=False):
    arms = ["upperarm.R", "forearm.R", "hand.R"]
    if both_arms:
        arms = ["upperarm.L", "forearm.L", "hand.L"] + arms
    keys = [
        (1, {**base_pose, "chest": {"rx": -0.15, "ry": -0.3},
             "upperarm.L": {"rx": -2.2, "rz": 0.25},
             "upperarm.R": {"rx": -2.3, "rz": -0.25},
             "forearm.L": {"rx": -1.6}, "forearm.R": {"rx": -1.6}}),
        (7, {**base_pose, "chest": {"rx": 0.1, "ry": 0.35},
             "upperarm.L": {"rx": -0.5, "rz": 0.1},
             "upperarm.R": {"rx": -0.45, "rz": -0.1},
             "forearm.L": {"rx": -0.2}, "forearm.R": {"rx": -0.2},
             "thigh.L": {"rx": 0.25}, "thigh.R": {"rx": -0.25}}),
        (14, {**base_pose}),
        (20, {**base_pose}),
    ]
    return keys


def anim_hit(base_pose, cfg):
    keys = [
        (1, {**base_pose}),
        (2, {**base_pose, "chest": {"rx": 0.45, "ry": -0.2}, "head": {"rx": 0.3},
             "hips": {"rx": 0.15}, "upperarm.L": {"rx": -0.6, "rz": 0.5},
             "upperarm.R": {"rx": -0.6, "rz": -0.5}}),
        (9, {**base_pose}),
        (14, {**base_pose}),
    ]
    return keys


def anim_death(base_pose, cfg):
    keys = [
        (1, {**base_pose}),
        (5, {**base_pose, "chest": {"rx": 0.3}, "head": {"rx": 0.25},
             "upperarm.L": {"rx": -1.4, "rz": 0.6}, "upperarm.R": {"rx": -1.4, "rz": -0.6}}),
        (16, {"root": {"loc": (0, 0.25, -0.55)}, "hips": {"rx": -0.9},
              "chest": {"rx": 0.35}, "head": {"rx": 0.4},
              "thigh.L": {"rx": -0.55}, "thigh.R": {"rx": -0.35},
              "shin.L": {"rx": 0.7}, "shin.R": {"rx": 0.9},
              "upperarm.L": {"rx": -0.4, "rz": 0.9}, "upperarm.R": {"rx": -0.3, "rz": -0.9},
              "forearm.L": {"rx": -0.4}, "forearm.R": {"rx": -0.3}}),
        (24, {"root": {"loc": (0, 0.32, -0.78)}, "hips": {"rx": -1.35},
              "chest": {"rx": 0.5}, "head": {"rx": 0.5},
              "thigh.L": {"rx": -0.4}, "thigh.R": {"rx": -0.25},
              "shin.L": {"rx": 0.4}, "shin.R": {"rx": 0.55},
              "upperarm.L": {"rz": 1.2}, "upperarm.R": {"rz": -1.2},
              "forearm.L": {"rx": -0.15}, "forearm.R": {"rx": -0.1}}),
    ]
    return keys


def rest_base_pose(cfg):
    base = {}
    if cfg.get("hunch"):
        base["spine"] = {"rx": -0.12}
        base["chest"] = {"rx": -0.08}
        base["head"] = {"rx": -0.12}
        base["upperarm.L"] = {"rx": -1.05, "rz": 0.15}
        base["upperarm.R"] = {"rx": -1.05, "rz": -0.15}
        base["forearm.L"] = {"rx": -0.5}
        base["forearm.R"] = {"rx": -0.5}
    return base


def export(arm, mesh, out_glb):
    bpy.ops.object.select_all(action='DESELECT')
    mesh.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.gltf(
        filepath=out_glb,
        export_format='GLB',
        export_animation_mode='NLA_TRACKS',
        export_anim_slide_to_zero=True,
        use_selection=True,
        export_yup=True,
    )


def measure(arm, mesh):
    world = [mesh.matrix_world @ v.co for v in mesh.data.vertices]
    xs = [v.x for v in world]
    ys = [v.y for v in world]
    zs = [v.z for v in world]
    return {
        "widthX": round(max(xs) - min(xs), 3),
        "depthY": round(max(ys) - min(ys), 3),
        "heightZ": round(max(zs) - min(zs), 3),
        "zMin": round(min(zs), 3),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--char", required=True, choices=["survivor", "zombie"])
    args = parser.parse_args()

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.preferences.addon_enable(module="io_scene_gltf2")

    if args.char == "survivor":
        palette = {
            "skin": (0.87, 0.68, 0.55),
            "shirt": (0.30, 0.36, 0.20),
            "pants": (0.16, 0.17, 0.19),
            "boots": (0.23, 0.13, 0.07),
            "hair": (0.13, 0.09, 0.06),
            "bare_forearms": False,
        }
        cfg = {"stride_amp": 0.5, "lean": 0.05}
        out = "assets/models/characters/survivor_male_01"
        spec_type = "character"
    else:
        palette = {
            "skin": (0.52, 0.60, 0.36),
            "shirt": (0.38, 0.14, 0.10),
            "pants": (0.20, 0.19, 0.16),
            "boots": (0.15, 0.14, 0.12),
            "hair": (0.08, 0.08, 0.09),
            "bare_forearms": True,
            "eye_emissive": True,
        }
        tmp = bpy.data.materials.new("no_basis")
        palette["eyes_mat"] = make_material("zombie_eyes", (1.0, 0.15, 0.05), emissive=(1.0, 0.15, 0.05))
        palette["eyes_mat"].name = "zombie_eyes"
        cfg = {"stride_amp": 0.35, "hunch": True}
        out = "assets/models/enemies/zombie_walker_01"
        spec_type = "enemy"

    materials = {}
    for key in ("skin", "shirt", "pants", "boots", "hair"):
        materials[key] = make_material(f"{args.char}_{key}", palette[key],
                                       roughness={**{"skin": 0.7, "shirt": 0.9, "pants": 0.9, "boots": 0.6, "hair": 0.95}}[key])

    mesh = build_mesh({**palette, **materials})
    arm = build_armature()
    link_skin(arm, mesh)

    base = rest_base_pose(cfg)
    actions = {
        "idle": make_action(arm, f"{args.char}_idle", anim_idle(base, cfg)),
        "walk": make_action(arm, f"{args.char}_walk", anim_walk(base, cfg)),
        "run": make_action(arm, f"{args.char}_run", anim_run(base, cfg)),
        "attack": make_action(arm, f"{args.char}_attack", anim_attack(base, cfg, both_arms=args.char == "zombie")),
        "hit": make_action(arm, f"{args.char}_hit", anim_hit(base, cfg)),
        "death": make_action(arm, f"{args.char}_death", anim_death(base, cfg)),
    }

    arm.animation_data_create()
    for name, act in actions.items():
        track = arm.animation_data.nla_tracks.new()
        track.name = name
        track.strips.new(act.name, int(act.frame_range[0]), act)

    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.wm.save_as_mainfile(filepath=f"/workspace/zombie-survival-3d/{out}.blend")

    glb_path = f"/workspace/zombie-survival-3d/{out}.glb"
    export(arm, mesh, glb_path)
    m = measure(arm, mesh)
    info = {
        "char": args.char,
        "glb": glb_path,
        "blend": f"/workspace/zombie-survival-3d/{out}.blend",
        "meshStats": {
            "verts": len(mesh.data.vertices),
            "tris": sum(len(p.vertices) - 2 for p in mesh.data.polygons),
            "materials": [s.name for s in mesh.material_slots],
        },
        "bones": [b.name for b in arm.data.bones],
        "animations": {n: {"frames": list(a.frame_range), "fcurves": sum(
            len(cb.fcurves) for layer in a.layers for strip in layer.strips for cb in strip.channelbags
        )} for n, a in actions.items()},
        "dimensions": m,
    }
    print("BUILD_RESULT_JSON:" + json.dumps(info))


main()
