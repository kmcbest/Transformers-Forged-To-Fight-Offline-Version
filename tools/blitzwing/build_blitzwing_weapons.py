import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import math
from pathlib import Path
import shutil
import bpy
from mathutils import Vector, Matrix, Euler

ROOT = Path(r"E:\Agent\TFTF-blender")
EW_FBX = ROOT / "3rd-party-models" / "Blitzwing_EW" / "01_source" / "H_shandian_G1_M_LOD.fbx"
ROBOT_FBX = ROOT / "3rd-party-models" / "Blitzwing_EW" / "03_fbx_exports" / "cha_blitzwing_gs_00_robot.fbx"
TEX_ROBOT_DIFF = ROOT / "tools" / "blitzwing" / "atlased_textures" / "cha_blitzwing_main_Diffuse.png"
TEX_WPNS_DIFF = ROOT / "tools" / "blitzwing" / "atlased_textures" / "cha_blitzwing_wpns_Diffuse.png"
OUT_EXPORT_DIR = ROOT / "3rd-party-models" / "Blitzwing_EW" / "03_fbx_exports"
UNITY_BW_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Blitzwing"
RENDER_DIR = ROOT / "tools" / "blitzwing" / "renders"
OUT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
UNITY_BW_DIR.mkdir(parents=True, exist_ok=True)
RENDER_DIR.mkdir(parents=True, exist_ok=True)

SCALE_SWORD = 142.0
SCALE_GUN   = 108.0

# Exact Unity Hand Placement Offsets (in UNITY RightHand / LeftHand space)
POS_SWORD_RH = Vector((-0.72, +0.34, +0.08))
POS_GUN_LH   = Vector((-0.70, -0.38, -0.02))

# 1. Load EW source and extract W1 (Sword) and W2 (Gun)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(EW_FBX))
bpy.context.view_layer.update()

w1_src = bpy.data.objects["H_shandian_G1_W1_Lod"]
w2_src = bpy.data.objects["H_shandian_G1_W2_Lod"]


def isolate_and_scale(obj, scale_val):
    bpy.context.view_layer.objects.active = obj
    mw = obj.matrix_world.copy()
    obj.parent = None
    obj.modifiers.clear()
    obj.matrix_world = Matrix.Identity(4)
    obj.data.transform(Matrix.Scale(scale_val, 4) @ mw)
    obj.data.update()


isolate_and_scale(w1_src, SCALE_SWORD)
isolate_and_scale(w2_src, SCALE_GUN)

# Orient W1 (Sword) into UNITY RightHand orientation centered at hilt grip (0,0,0):
# - Edge along +X_rh / -X_rh (matches Windblade & Bludgeon canonical Sword basis!)
# - Flat faces along Y_rh
# - Tip along +Z_rh
w1_pts = [v.co.copy() for v in w1_src.data.vertices]
hilt_pts = [p for p in w1_pts if p.z < 1.38]
hilt_cx = sum(p.x for p in hilt_pts) / len(hilt_pts)
hilt_cy = sum(p.y for p in hilt_pts) / len(hilt_pts)
cross_pts = [p for p in w1_pts if abs(p.x) > 0.24 and p.z < 2.4]
sword_grip_z = max(0.88, min(p.z for p in cross_pts) - 0.52) if cross_pts else 0.96
w1_src.data.transform(Matrix.Translation(Vector((-hilt_cx, -hilt_cy, -sword_grip_z))))
w1_src.data.update()

# Orient W2 (Gun) into UNITY LeftHand orientation centered at pistol grip (0,0,0):
# - Barrel forward along -X_lh (matches Motormaster LeftHand muzzle vector!)
# - Top rail/sight along +Z_lh (thumb/index side)
# - Width along Y_lh
w2_pts = [v.co.copy() for v in w2_src.data.vertices]
# Pistol grip bottom Z in scaled W2 sits at min_z .. upper receiver ~1.40
min_z_g = min(p.z for p in w2_pts)
grip_pts = [p for p in w2_pts if p.z < min_z_g + 0.15 and -1.2 < p.x < 0.2]
grip_cx = sum(p.x for p in grip_pts) / len(grip_pts)
# Grip shaft runs up ~0.65m above bottom cap; place grip center ~0.35m above bottom cap so curled fingers fit below receiver!
grip_cz = min_z_g + 0.36
w2_rot = Matrix.Rotation(math.pi, 4, 'Z')  # (+x, +y, +z) -> (-x, -y, +z)
w2_src.data.transform(w2_rot @ Matrix.Translation(Vector((-grip_cx, 0.0, -grip_cz))))
w2_src.data.update()

for label, obj in [("SWORD (RightHand_unity)", w1_src), ("GUN (LeftHand_unity)", w2_src)]:
    pts = [v.co for v in obj.data.vertices]
    print(f"=== {label} (origin = grip center) ===")
    print(f"  X=[{min(p.x for p in pts):.3f}, {max(p.x for p in pts):.3f}]")
    print(f"  Y=[{min(p.y for p in pts):.3f}, {max(p.y for p in pts):.3f}]")
    print(f"  Z=[{min(p.z for p in pts):.3f}, {max(p.z for p in pts):.3f}]")


# 2. Export 1-bone COG FBXs (and verify Unity axis mapping in PackBlitzwingBundle.cs!)
# NOTE: Wait! What FBX export axes match Unity's Vector3(x,y,z) cleanly?
# With Blender object coordinates (x, y, z) and export_scene.fbx(axis_forward='-Z', axis_up='Y'),
# Unity imports (x, y, z)_blender -> (x, z, -y) OR (-x, y, z) depending on bake_space_transform.
# Instead of relying on export axis guessing, we export with axis_forward='Y', axis_up='Z' (identity transform in FBX!)
# AND in PackBlitzwingBundle.cs we convert Blender (x_b, y_b, z_b) -> Unity (-x_b, z_b, -y_b) OR let's check what PackBlitzwingBundle.cs gets from Blender FBX!
def export_single_bone_wpn_fbx(mesh_obj, mesh_name, arm_name, out_fbx: Path, unity_fbx: Path):
    bpy.ops.object.select_all(action='DESELECT')
    # Duplicate cleanly into an isolated export rig
    mcopy = mesh_obj.copy()
    mcopy.data = mesh_obj.data.copy()
    mcopy.name = mesh_name
    mcopy.data.name = mesh_name
    mcopy.matrix_world = Matrix.Identity(4)
    bpy.context.collection.objects.link(mcopy)

    # Clear materials -> 1 clean material cha_blitzwing_wpns
    mcopy.data.materials.clear()
    mat = bpy.data.materials.new(name="cha_blitzwing_wpns")
    mcopy.data.materials.append(mat)

    arm_data = bpy.data.armatures.new(name=arm_name + "_Data")
    arm_obj = bpy.data.objects.new(name=arm_name, object_data=arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj

    bpy.ops.object.mode_set(mode='EDIT')
    bone = arm_data.edit_bones.new(name="COG")
    bone.head = Vector((0.0, 0.0, 0.0))
    bone.tail = Vector((0.0, 0.0, 1.0))
    bpy.ops.object.mode_set(mode='OBJECT')

    mcopy.vertex_groups.clear()
    vg = mcopy.vertex_groups.new(name="COG")
    vg.add(list(range(len(mcopy.data.vertices))), 1.0, 'REPLACE')
    mod = mcopy.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj
    mcopy.parent = arm_obj

    bpy.ops.object.select_all(action='DESELECT')
    mcopy.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

    bpy.ops.export_scene.fbx(
        filepath=str(out_fbx),
        use_selection=True,
        add_leaf_bones=False,
        bake_anim=False,
        axis_forward='Y',
        axis_up='Z',
    )
    shutil.copy2(out_fbx, unity_fbx)
    print(f"[EXPORT] {out_fbx.name} ({out_fbx.stat().st_size} bytes) -> copied to {unity_fbx.name}")

    # Remove temp export rig so scene stays clean for renders
    bpy.data.objects.remove(mcopy, do_unlink=True)
    bpy.data.objects.remove(arm_obj, do_unlink=True)


# WAIT: Notice in UNITY we want mesh coordinates = UNITY_HAND space (x_u, y_u, z_u).
# Because Unity imports Blender's Y-up conversion (`v_unity = (-v_b.x, v_b.z, -v_b.y)` if using default FBX or check `PackBlitzwingBundle.cs`),
# let's keep Blender FBX vertices in exact UNITY_HAND space `(x, y, z)` and verify in PackBlitzwingBundle.cs log!
# Keep W2 barrel along +X in Blender FBX so Unity FBX Importer's X-axis handedness flip
# natively places barrel along LeftHand -X_unity ([-2.660, +1.855]) with clean outward winding!
w2_unity_fbx_copy = w2_src.copy()
w2_unity_fbx_copy.data = w2_src.data.copy()
w2_unity_fbx_copy.data.transform(Matrix.Rotation(math.pi, 4, 'Z'))  # flip X & Y -> barrel +X in Blender -> -X in Unity!
w2_unity_fbx_copy.data.update()

export_single_bone_wpn_fbx(
    w1_src, "cha_blitzwing_wpns_sword", "cha_blitzwing_sword_rig",
    OUT_EXPORT_DIR / "cha_blitzwing_wpns_sword.fbx",
    UNITY_BW_DIR / "cha_blitzwing_wpns_sword.fbx",
)
export_single_bone_wpn_fbx(
    w2_unity_fbx_copy, "cha_blitzwing_wpns_gun", "cha_blitzwing_gun_rig",
    OUT_EXPORT_DIR / "cha_blitzwing_wpns_gun.fbx",
    UNITY_BW_DIR / "cha_blitzwing_wpns_gun.fbx",
)
bpy.data.objects.remove(w2_unity_fbx_copy, do_unlink=True)


# 3. Render Blender Verification Previews on Blitzwing Robot (Rest + LeftArm Raised Aiming Pose!)
def make_tex_mat(name, tex_path):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(tex_path))
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if "Roughness" in bsdf.inputs:
        bsdf.inputs["Roughness"].default_value = 0.45
    return mat


mat_wpn = make_tex_mat("Mat_Wpn", TEX_WPNS_DIFF)
w1_src.data.materials.clear()
w1_src.data.materials.append(mat_wpn)
w2_src.data.materials.clear()
w2_src.data.materials.append(mat_wpn)

bpy.ops.import_scene.fbx(filepath=str(ROBOT_FBX))
bw_arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
bw_mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and o not in (w1_src, w2_src))
mat_bot = make_tex_mat("Mat_Bot", TEX_ROBOT_DIFF)
bw_mesh.data.materials.clear()
bw_mesh.data.materials.append(mat_bot)

M_rh_to_bl = Matrix((
    (0.0, 1.0, 0.0, -2.4734 + POS_SWORD_RH.y),
    (0.0, 0.0, -1.0, 0.0470 - POS_SWORD_RH.z),
    (1.0, 0.0, 0.0, 5.5272 + POS_SWORD_RH.x),
    (0.0, 0.0, 0.0, 1.0),
))
M_lh_to_bl = Matrix((
    (0.0, 1.0, 0.0, 2.4734 + POS_GUN_LH.y),
    (0.0, 0.0, -1.0, 0.0470 - POS_GUN_LH.z),
    (1.0, 0.0, 0.0, 5.5272 + POS_GUN_LH.x),
    (0.0, 0.0, 0.0, 1.0),
))

w1_prev = w1_src.copy()
w1_prev.data = w1_src.data.copy()
w1_prev.data.transform(M_rh_to_bl)
bpy.context.collection.objects.link(w1_prev)

w2_prev = w2_src.copy()
w2_prev.data = w2_src.data.copy()
w2_prev.data.transform(M_lh_to_bl)
bpy.context.collection.objects.link(w2_prev)

w1_src.hide_render = True
w2_src.hide_render = True
w1_src.hide_viewport = True
w2_src.hide_viewport = True

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1280
scene.render.resolution_y = 960
world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.14, 0.16, 0.20, 1.0)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.2

for name, rot_deg, energy in [("Key", (45, 0, 35), 2.8), ("Fill", (65, 0, -135), 1.4)]:
    ld = bpy.data.lights.new(name, type='SUN')
    ld.energy = energy
    lo = bpy.data.objects.new(name, ld)
    lo.rotation_euler = Euler([math.radians(a) for a in rot_deg])
    bpy.context.collection.objects.link(lo)

cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
bpy.context.collection.objects.link(cam)
scene.camera = cam


def look_at(eye, target, lens=45.0):
    cam.data.lens = lens
    cam.location = Vector(eye)
    cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()


# Render A: Hero Dual-Weapon Rest
look_at((9.5, -16.0, 9.5), (0.0, -1.0, 6.2), lens=40.0)
scene.render.filepath = str(RENDER_DIR / "10_dual_weapons_hero.png")
bpy.ops.render.render(write_still=True)

# Render B: RightHand + Sword Palm Grip Closeup
look_at((-4.2, -4.8, 3.2), (-2.13, -0.5, 4.85), lens=50.0)
scene.render.filepath = str(RENDER_DIR / "11_righthand_sword_closeup.png")
bpy.ops.render.render(write_still=True)

# Render C: LeftHand + Gun Aiming Forward (+90 deg LeftArm forward raise!)
pb_lh = bw_arm.pose.bones["LeftHand"]
M_lh_rest = (bw_arm.matrix_world @ pb_lh.matrix).copy()

# Pose LeftArm raised 85 deg forward to simulate Motormaster shooting pose
pb_la = bw_arm.pose.bones["LeftArm"]
pb_la.rotation_mode = 'XYZ'
pb_la.rotation_euler = Euler((math.radians(-85), 0.0, 0.0))
bpy.context.view_layer.update()

M_lh_posed = (bw_arm.matrix_world @ pb_lh.matrix).copy()
w2_aim = w2_prev.copy()
w2_aim.data = w2_prev.data.copy()
w2_aim.data.transform(M_lh_posed @ M_lh_rest.inverted())
bpy.context.collection.objects.link(w2_aim)
w2_prev.hide_render = True

look_at((7.5, -12.0, 10.0), (1.0, -3.5, 7.8), lens=42.0)
scene.render.filepath = str(RENDER_DIR / "12_lefthand_gun_aiming_closeup.png")
bpy.ops.render.render(write_still=True)

print("[✓] Exported FBXs & rendered updated weapon verification shots!")
