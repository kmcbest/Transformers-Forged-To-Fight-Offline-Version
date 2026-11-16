import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

print("=== [Brawl] Remapping UVs and Exporting Clean Atlased FBX Meshes ===")

ROBOT_BLEND = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Brawl\01_aligned_mesh\brawl_robot_aligned.blend")
TANK_BLEND = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Brawl\01_aligned_mesh\brawl_tank_aligned.blend")
TEX_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Brawl\02_textures")

UNITY_BRAWL_DIR = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Brawl")
UNITY_BRAWL_DIR.mkdir(parents=True, exist_ok=True)
OUT_FBX_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Brawl\03_fbx_exports")
OUT_FBX_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------
# 1. PROCESS ROBOT MESH
# ----------------------------------------------------
bpy.ops.wm.open_mainfile(filepath=str(ROBOT_BLEND))

# Remove donor ref if present
if "Megatron_Donor_Ref" in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects["Megatron_Donor_Ref"], do_unlink=True)

robot = bpy.data.objects.get("Brawl_Robot_Raw")
assert robot is not None, "Missing Brawl_Robot_Raw!"
robot.name = "cha_brawl_gs_00"

# UV Remapping per polygon material
robot_uv_map = {
    # mat_name: (u_scale, u_off, v_scale, v_off)
    'RB_Brawl_Chest_Mat_INST_B': (0.5, 0.0, 0.5, 0.5),
    'TR_FactionLogo_Mat_INST':   (0.5, 0.0, 0.5, 0.5),
    'VH_Brawl_Cust_MatINST':     (0.5, 0.5, 0.5, 0.5),
    'RB_Brawl_Legs_Mat_INST_B':  (0.5, 0.0, 0.5, 0.0),
    'RB_Brawl_Head_Mat_INST_B':  (0.25, 0.5, 0.25, 0.25),
    'RB_Brawl_ArmLo_Mat_INST_B': (0.25, 0.75, 0.25, 0.25),
    'RB_Brawl_ArmUp_Mat_INST_B': (0.25, 0.5, 0.25, 0.0),
    'VH_BrawInterior_Cust_MatINST': (0.25, 0.75, 0.25, 0.0),
}

# Ensure active UV layer
uv_layer = robot.data.uv_layers.active
assert uv_layer is not None, "Robot mesh missing active UV layer!"

mat_slots = [slot.material.name if slot.material else '' for slot in robot.material_slots]
print("Robot material slots:", mat_slots)

# Remap UV loop coordinates based on polygon material
for poly in robot.data.polygons:
    mname = mat_slots[poly.material_index] if poly.material_index < len(mat_slots) else ''
    u_sc, u_off, v_sc, v_off = robot_uv_map.get(mname, (1.0, 0.0, 1.0, 0.0))
    for loop_idx in poly.loop_indices:
        uv = uv_layer.data[loop_idx].uv
        # Wrap into [0, 1] if needed
        u_base = uv.x % 1.0
        v_base = uv.y % 1.0
        uv_layer.data[loop_idx].uv = (u_base * u_sc + u_off, v_base * v_sc + v_off)

robot.data.update()
print("[✓] Remapped Robot UV coordinates to 4K/2K Atlas layout.")

# Create single unified material
mat_robot = bpy.data.materials.new("M_Brawl_Main")
mat_robot.use_nodes = True
bsdf = mat_robot.node_tree.nodes.get("Principled BSDF")
tex_diff = mat_robot.node_tree.nodes.new("ShaderNodeTexImage")
tex_diff.image = bpy.data.images.load(str(TEX_DIR / "cha_brawl_main_Diffuse.png"))
mat_robot.node_tree.links.new(tex_diff.outputs["Color"], bsdf.inputs["Base Color"])

robot.data.materials.clear()
robot.data.materials.append(mat_robot)

# Export Robot OBJ and FBX
bpy.ops.object.select_all(action='DESELECT')
robot.select_set(True)
bpy.context.view_layer.objects.active = robot

obj_robot_out = OUT_FBX_DIR / "cha_brawl_gs_00_robot.obj"
bpy.ops.wm.obj_export(filepath=str(obj_robot_out), export_selected_objects=True)

fbx_robot_out = UNITY_BRAWL_DIR / "brawl_robot.fbx"
fbx_robot_backup = OUT_FBX_DIR / "brawl_robot.fbx"
for p in (fbx_robot_out, fbx_robot_backup):
    bpy.ops.export_scene.fbx(
        filepath=str(p),
        use_selection=True,
        object_types={'MESH'},
        axis_forward='Z',
        axis_up='Y',
        apply_unit_scale=True,
        bake_anim=False
    )
print(f"[✓] Exported Robot FBX: {fbx_robot_out}")


# ----------------------------------------------------
# 2. PROCESS TANK MESH
# ----------------------------------------------------
bpy.ops.wm.open_mainfile(filepath=str(TANK_BLEND))

tank = bpy.data.objects.get("VH_BrawlCINE_SKEL.001.dmx")
assert tank is not None, "Missing tank object!"
tank.name = "cha_brawl_gs_01"

tank_uv_map = {
    'VH_Brawl_Cust_MatINST':        (0.5, 0.0, 0.5, 0.5),
    'VH_BrawLegsl_Cust_MatINST':    (0.5, 0.5, 0.5, 0.5),
    'VH_BrawInterior_Cust_MatINST': (0.5, 0.0, 0.5, 0.0),
    'TR_FactionLogo_Mat_INST':      (0.5, 0.5, 0.5, 0.0),
}

tank_uv_layer = tank.data.uv_layers.active
t_mat_slots = [slot.material.name if slot.material else '' for slot in tank.material_slots]
print("Tank material slots:", t_mat_slots)

for poly in tank.data.polygons:
    mname = t_mat_slots[poly.material_index] if poly.material_index < len(t_mat_slots) else ''
    u_sc, u_off, v_sc, v_off = tank_uv_map.get(mname, (1.0, 0.0, 1.0, 0.0))
    for loop_idx in poly.loop_indices:
        uv = tank_uv_layer.data[loop_idx].uv
        u_base = uv.x % 1.0
        v_base = uv.y % 1.0
        tank_uv_layer.data[loop_idx].uv = (u_base * u_sc + u_off, v_base * v_sc + v_off)

tank.data.update()
print("[✓] Remapped Tank UV coordinates to 4K/2K Atlas layout.")

mat_tank = bpy.data.materials.new("M_Brawl_Vehicle")
mat_tank.use_nodes = True
t_bsdf = mat_tank.node_tree.nodes.get("Principled BSDF")
t_tex_diff = mat_tank.node_tree.nodes.new("ShaderNodeTexImage")
t_tex_diff.image = bpy.data.images.load(str(TEX_DIR / "cha_brawl_tform_misc_Diffuse.png"))
mat_tank.node_tree.links.new(t_tex_diff.outputs["Color"], t_bsdf.inputs["Base Color"])

tank.data.materials.clear()
tank.data.materials.append(mat_tank)

bpy.ops.object.select_all(action='DESELECT')
tank.select_set(True)
bpy.context.view_layer.objects.active = tank

obj_tank_out = OUT_FBX_DIR / "cha_brawl_gs_01_tank.obj"
bpy.ops.wm.obj_export(filepath=str(obj_tank_out), export_selected_objects=True)

fbx_tank_out = UNITY_BRAWL_DIR / "brawl_tank.fbx"
fbx_tank_backup = OUT_FBX_DIR / "brawl_tank.fbx"
for p in (fbx_tank_out, fbx_tank_backup):
    bpy.ops.export_scene.fbx(
        filepath=str(p),
        use_selection=True,
        object_types={'MESH'},
        axis_forward='Z',
        axis_up='Y',
        apply_unit_scale=True,
        bake_anim=False
    )
print(f"[✓] Exported Tank FBX: {fbx_tank_out}")
print("=== All Brawl FBX and OBJ assets built successfully! ===")
