import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import shutil
from pathlib import Path

# Paths
SOURCE_FBX = Path(r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx")
SOURCE_TEX_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\textures")

TARGET_ROOT = Path(r"E:\Agent\TFTF-blender\3rd-party-models\vortex")
TARGET_TEX_DIR = TARGET_ROOT / "textures"
TARGET_ROBOT_DIR = TARGET_ROOT / "robot"
TARGET_WEAPONS_DIR = TARGET_ROOT / "weapons"
TARGET_VEHICLE_DIR = TARGET_ROOT / "vehicle"

for d in [TARGET_ROOT, TARGET_TEX_DIR, TARGET_ROBOT_DIR, TARGET_WEAPONS_DIR, TARGET_VEHICLE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 1. Required textures list for Vortex
REQUIRED_TEXTURES = [
    # Robot
    "rb_vortex_head_mat.jpg",
    "rb_vortex_head_n.jpg",
    "rb_vortex_chest_mat.jpg",
    "rb_vortex_chest_n.jpg",
    "rb_vortex_armup_mat.jpg",
    "rb_vortex_armup_n.jpg",
    "rb_vortex_armlo_mat.jpg",
    "rb_vortex_armlo_n.jpg",
    "rb_vortex_legs_mat.jpg",
    "rb_vortex_legs_n.jpg",
    "rb_vortex_backpack_mat.jpg",
    "rb_vortex_backpack_n.jpg",
    # Vehicle
    "vh_vortexbase_mat.jpg",
    "vh_vortexbase_n.jpg",
    # Weapons
    "wep_bladeaut_mat.jpg",
    "wep.jpg",
    "wep_e.jpg",
    # Logo
    "DecepticonLogo.png"
]

print("=== STEP 1: COPYING VORTEX TEXTURES ===")
for tname in REQUIRED_TEXTURES:
    src_f = SOURCE_TEX_DIR / tname
    dst_f = TARGET_TEX_DIR / tname
    if src_f.exists():
        shutil.copy2(src_f, dst_f)
        print(f"  [OK] Copied {tname}")
    else:
        print(f"  [WARN] Source texture not found: {tname}")

# Material mapping definitions for Vortex
MAT_TEXTURE_DEFS = {
    "RB_Vortex_Head_MAT": {
        "diffuse": "rb_vortex_head_mat.jpg",
        "normal": "rb_vortex_head_n.jpg",
        "emission": None
    },
    "RB_Vortex_Chest_MAT": {
        "diffuse": "rb_vortex_chest_mat.jpg",
        "normal": "rb_vortex_chest_n.jpg",
        "emission": None
    },
    "RB_Vortex_ArmUp_MAT": {
        "diffuse": "rb_vortex_armup_mat.jpg",
        "normal": "rb_vortex_armup_n.jpg",
        "emission": None
    },
    "RB_Vortex_ArmLo_MAT": {
        "diffuse": "rb_vortex_armlo_mat.jpg",
        "normal": "rb_vortex_armlo_n.jpg",
        "emission": None
    },
    "RB_Vortex_Legs_MAT": {
        "diffuse": "rb_vortex_legs_mat.jpg",
        "normal": "rb_vortex_legs_n.jpg",
        "emission": None
    },
    "RB_Vortex_BackPack_MAT": {
        "diffuse": "rb_vortex_backpack_mat.jpg",
        "normal": "rb_vortex_backpack_n.jpg",
        "emission": None
    },
    "VH_VortexBase_MAT": {
        "diffuse": "vh_vortexbase_mat.jpg",
        "normal": "vh_vortexbase_n.jpg",
        "emission": None
    },
    "WEP_BLadeAut_MAT": {
        "diffuse": "wep_bladeaut_mat.jpg",
        "normal": None,
        "emission": None
    },
    "WEP_IonBlade_MATINST": {
        "diffuse": "wep.jpg",
        "normal": None,
        "emission": "wep_e.jpg"
    },
    "TR_FactionLogo_Mat_INST": {
        "diffuse": "DecepticonLogo.png",
        "normal": None,
        "emission": None
    }
}

def setup_mat_nodes(mat, tex_info, relative_dir=TARGET_TEX_DIR):
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = (400, 0)
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    links.new(bsdf.outputs['BSDF'], output_node.inputs['Surface'])
    
    if tex_info.get("diffuse"):
        d_path = relative_dir / tex_info["diffuse"]
        if d_path.exists():
            tex_img = nodes.new(type='ShaderNodeTexImage')
            tex_img.image = bpy.data.images.load(str(d_path))
            tex_img.location = (-400, 200)
            links.new(tex_img.outputs['Color'], bsdf.inputs['Base Color'])
            if tex_info["diffuse"].endswith(".png"):
                links.new(tex_img.outputs['Alpha'], bsdf.inputs['Alpha'])
                mat.blend_method = 'CLIP'
    
    if tex_info.get("normal"):
        n_path = relative_dir / tex_info["normal"]
        if n_path.exists():
            norm_img = nodes.new(type='ShaderNodeTexImage')
            norm_img.image = bpy.data.images.load(str(n_path))
            norm_img.image.colorspace_settings.name = 'Non-Color'
            norm_img.location = (-600, -200)
            
            norm_map = nodes.new(type='ShaderNodeNormalMap')
            norm_map.location = (-300, -200)
            links.new(norm_img.outputs['Color'], norm_map.inputs['Color'])
            links.new(norm_map.outputs['Normal'], bsdf.inputs['Normal'])
            
    if tex_info.get("emission"):
        e_path = relative_dir / tex_info["emission"]
        if e_path.exists():
            emis_img = nodes.new(type='ShaderNodeTexImage')
            emis_img.image = bpy.data.images.load(str(e_path))
            emis_img.location = (-400, -500)
            if 'Emission Color' in bsdf.inputs:
                links.new(emis_img.outputs['Color'], bsdf.inputs['Emission Color'])
            elif 'Emission' in bsdf.inputs:
                links.new(emis_img.outputs['Color'], bsdf.inputs['Emission'])
            if 'Emission Strength' in bsdf.inputs:
                bsdf.inputs['Emission Strength'].default_value = 1.0

def configure_all_materials(relative_dir=TARGET_TEX_DIR):
    for mat in bpy.data.materials:
        for pattern, defs in MAT_TEXTURE_DEFS.items():
            if pattern.lower() in mat.name.lower():
                setup_mat_nodes(mat, defs, relative_dir)
                break

# List of Vortex objects
ROBOT_MESH_NAMES = [
    "RB_Vortex_CHARSKEL_ArmLoL.mo.dmx",
    "RB_Vortex_CHARSKEL_ArmLoR.mo.dmx",
    "RB_Vortex_CHARSKEL_Head.mo.dmx",
]
ROBOT_ARM_NAME = "Vortex_ARM"

WEAPON_NAMES = [
    "WEP_IonBlade_SKEL.mo_L.dmx",
    "WEP_IonBlade_SKEL.mo_R.dmx"
]

VEHICLE_MESH_NAME = "VH_Vortex_SKEL.001.dmx"
VEHICLE_ARM_NAME = "Vortex_VH_ARM"

ALL_VORTEX_OBJ_NAMES = set(ROBOT_MESH_NAMES + [ROBOT_ARM_NAME] + WEAPON_NAMES + [VEHICLE_MESH_NAME, VEHICLE_ARM_NAME])

print("\n=== STEP 2: IMPORTING FULL COMBATICONS FBX ===")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SOURCE_FBX))

# Configure materials with clean textures
configure_all_materials(TARGET_TEX_DIR)

# Fix offsets and relations
arm_robot = bpy.data.objects.get(ROBOT_ARM_NAME)
arm_vh = bpy.data.objects.get(VEHICLE_ARM_NAME)
vh_mesh = bpy.data.objects.get(VEHICLE_MESH_NAME)

# Center robot armature and meshes
if arm_robot:
    arm_robot.location = (0, 0, 0)

for mname in ROBOT_MESH_NAMES:
    m = bpy.data.objects.get(mname)
    if m:
        m.location = (0, 0, 0)
        m.parent = arm_robot
        if not any(mod.type == 'ARMATURE' for mod in m.modifiers):
            mod = m.modifiers.new(name=ROBOT_ARM_NAME, type='ARMATURE')
            mod.object = arm_robot

# Center weapons and parent to robot armature
for wname in WEAPON_NAMES:
    w = bpy.data.objects.get(wname)
    if w:
        w.location = (0, 0, 0)
        w.parent = arm_robot
        if not any(mod.type == 'ARMATURE' for mod in w.modifiers):
            mod = w.modifiers.new(name=ROBOT_ARM_NAME, type='ARMATURE')
            mod.object = arm_robot

# Center vehicle armature and mesh
if arm_vh:
    arm_vh.location = (0, 0, 0)
if vh_mesh:
    vh_mesh.location = (0, 0, 0)
    vh_mesh.parent = arm_vh
    if not any(mod.type == 'ARMATURE' for mod in vh_mesh.modifiers):
        mod = vh_mesh.modifiers.new(name=VEHICLE_ARM_NAME, type='ARMATURE')
        mod.object = arm_vh

# Remove all non-Vortex objects
print("\n=== STEP 3: PRUNING NON-VORTEX OBJECTS ===")
for obj in list(bpy.data.objects):
    if obj.name not in ALL_VORTEX_OBJ_NAMES:
        bpy.data.objects.remove(obj, do_unlink=True)

# Remove unused data blocks
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
for arm in list(bpy.data.armatures):
    if arm.users == 0:
        bpy.data.armatures.remove(arm)

# Save Master .blend containing all Vortex parts
master_blend = TARGET_ROOT / "vortex_master.blend"
robot_coll = bpy.data.collections.new("01_Vortex_Robot")
weapons_coll = bpy.data.collections.new("02_Vortex_Weapons")
vh_coll = bpy.data.collections.new("03_Vortex_Vehicle")

scene_coll = bpy.context.scene.collection
scene_coll.children.link(robot_coll)
scene_coll.children.link(weapons_coll)
scene_coll.children.link(vh_coll)

for name in ROBOT_MESH_NAMES + [ROBOT_ARM_NAME]:
    o = bpy.data.objects.get(name)
    if o:
        robot_coll.objects.link(o)
        if o.name in scene_coll.objects:
            scene_coll.objects.unlink(o)

for name in WEAPON_NAMES:
    o = bpy.data.objects.get(name)
    if o:
        weapons_coll.objects.link(o)
        if o.name in scene_coll.objects:
            scene_coll.objects.unlink(o)

for name in [VEHICLE_MESH_NAME, VEHICLE_ARM_NAME]:
    o = bpy.data.objects.get(name)
    if o:
        vh_coll.objects.link(o)
        if o.name in scene_coll.objects:
            scene_coll.objects.unlink(o)

bpy.ops.wm.save_as_mainfile(filepath=str(master_blend))
print(f"[OK] Saved master blend: {master_blend}")

# --- STEP 4: EXPORT ROBOT MODE ---
print("\n=== STEP 4: EXPORTING ROBOT MODE ===")
bpy.ops.wm.open_mainfile(filepath=str(master_blend))
for name in [VEHICLE_MESH_NAME, VEHICLE_ARM_NAME]:
    o = bpy.data.objects.get(name)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)

robot_blend = TARGET_ROBOT_DIR / "vortex_robot.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(robot_blend))
robot_fbx = TARGET_ROBOT_DIR / "vortex_robot.fbx"
bpy.ops.export_scene.fbx(filepath=str(robot_fbx), use_selection=False, add_leaf_bones=False)
print(f"[OK] Saved robot blend: {robot_blend}")
print(f"[OK] Saved robot fbx: {robot_fbx}")

# --- STEP 5: EXPORT VEHICLE MODE ---
print("\n=== STEP 5: EXPORTING VEHICLE MODE ===")
bpy.ops.wm.open_mainfile(filepath=str(master_blend))
for obj in list(bpy.data.objects):
    if obj.name not in [VEHICLE_MESH_NAME, VEHICLE_ARM_NAME]:
        bpy.data.objects.remove(obj, do_unlink=True)

vh_blend = TARGET_VEHICLE_DIR / "vortex_vehicle.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(vh_blend))
vh_fbx = TARGET_VEHICLE_DIR / "vortex_vehicle.fbx"
bpy.ops.export_scene.fbx(filepath=str(vh_fbx), use_selection=False, add_leaf_bones=False)
print(f"[OK] Saved vehicle blend: {vh_blend}")
print(f"[OK] Saved vehicle fbx: {vh_fbx}")

# --- STEP 6: EXPORT WEAPONS ---
print("\n=== STEP 6: EXPORTING WEAPONS ===")
bpy.ops.wm.open_mainfile(filepath=str(master_blend))
for obj in list(bpy.data.objects):
    if obj.name not in WEAPON_NAMES:
        bpy.data.objects.remove(obj, do_unlink=True)

wpn_blend = TARGET_WEAPONS_DIR / "vortex_weapons.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(wpn_blend))
wpn_fbx = TARGET_WEAPONS_DIR / "vortex_weapons.fbx"
bpy.ops.export_scene.fbx(filepath=str(wpn_fbx), use_selection=False, add_leaf_bones=False)
print(f"[OK] Saved weapons blend: {wpn_blend}")
print(f"[OK] Saved weapons fbx: {wpn_fbx}")

print("\n[SUCCESS] All Vortex assets successfully extracted, packaged, and verified!")
