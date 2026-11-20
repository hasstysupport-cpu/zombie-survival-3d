import math
import os
import sys

import bpy
from mathutils import Vector

ROOT = "/workspace/zombie-survival-3d"

SHOTS = [
    ("rest_front", None, 12, 0),
    ("idle_34", "idle", 12, -35),
    ("walk_34", "walk", 24, -35),
    ("walk_side", "walk", 12, -90),
    ("run_34", "run", 8, -35),
    ("attack_34", "attack", 7, -25),
    ("hit_back", "hit", 2, 150),
    ("death_side", "death", 20, -75),
]

SUN_TRANSFORMS = {
    0: (math.radians(-55), 0, math.radians(15)),
    -35: (math.radians(-55), 0, math.radians(-20)),
    -90: (math.radians(-55), 0, math.radians(-70)),
    -75: (math.radians(-55), 0, math.radians(-60)),
    150: (math.radians(-55), 0, math.radians(160)),
    -25: (math.radians(-55), 0, math.radians(5)),
}


def setup_camera(cam_obj, azimuth_deg, dist=3.1, cam_z=1.45):
    a = math.radians(azimuth_deg)
    cam_obj.location = (dist * math.sin(a), -dist * math.cos(a), cam_z)
    target = Vector((0, 0, 0.95))
    direction = target - Vector(cam_obj.location)
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def assert_mod(arm, mesh):
    if not any(m.type == 'ARMATURE' for m in mesh.modifiers):
        mod = mesh.modifiers.new("Armature", type='ARMATURE')
        mod.object = arm


def main():
    blend_path, out_name = sys.argv[-2], sys.argv[-1]
    out_dir = os.path.join(ROOT, "previews", out_name)
    os.makedirs(out_dir, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=blend_path)
    arm = bpy.data.objects["CharacterSkeleton"]
    mesh = bpy.data.objects["CharacterVisual"]
    assert_mod(arm, mesh)

    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 560
    scene.render.resolution_y = 560
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'Standard'

    world = bpy.data.worlds.new("PreviewWorld")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.55, 0.58, 0.62, 1.0)
    bg.inputs[1].default_value = 1.2
    scene.world = world

    sun = bpy.data.lights.new("KeySun", type='SUN')
    sun.energy = 5.0
    sun.angle = 0.35
    sun_obj = bpy.data.objects.new("KeySun", sun)
    bpy.context.collection.objects.link(sun_obj)
    sun_obj.rotation_euler = (math.radians(-55), 0, math.radians(15))

    if not any(o.name == "PreviewGround" for o in bpy.data.objects):
        import bmesh
        ground = bpy.data.meshes.new("PreviewGround")
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=6)
        bm.to_mesh(ground)
        bm.free()
        gobj = bpy.data.objects.new("PreviewGround", ground)
        bpy.context.collection.objects.link(gobj)
        gmat = bpy.data.materials.new("ground_mat")
        gmat.use_nodes = True
        gp = gmat.node_tree.nodes["Principled BSDF"]
        gp.inputs["Base Color"].default_value = (0.55, 0.57, 0.60, 1)
        gp.inputs["Roughness"].default_value = 0.95
        gobj.data.materials.append(gmat)

    cam = bpy.data.cameras.new("PreviewCam")
    cam.lens = 52
    cam_obj = bpy.data.objects.new("PreviewCam", cam)
    bpy.context.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    prefix = "survivor" if "survivor" in os.path.basename(blend_path) else "zombie"

    for shot_name, anim, frame, yaw in SHOTS:
        if anim:
            act = bpy.data.actions.get(f"{prefix}_{anim}")
            if act:
                arm.animation_data_create()
                arm.animation_data.action = act
                scene.frame_set(frame)
            else:
                print("MISSING ACTION", anim)
        else:
            if arm.animation_data:
                arm.animation_data.action = None
            scene.frame_set(1)
        sun_obj.rotation_euler = SUN_TRANSFORMS.get(yaw, (math.radians(-55), 0, math.radians(15)))
        bpy.context.view_layer.update()
        setup_camera(cam_obj, yaw)
        scene.render.filepath = os.path.join(out_dir, f"{shot_name}.png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED:", scene.render.filepath)


main()
