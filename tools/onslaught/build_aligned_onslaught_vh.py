import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import math
from pathlib import Path
import bpy
import mathutils

print("=== BUILDING ALIGNED ONSLAUGHT VEHICLE (MISSILE TRUCK) ===")

bpy.ops.wm.read_factory_settings(use_empty=True)

ROOT = Path(r"E:\Agent\TFTF-blender")
BONES_JSON = ROOT / "tools" / "demolishor" / "ironhide_47_vh_bones.json"
VH_BLEND = ROOT / "3rd-party-models" / "onslaught" / "vehicle" / "onslaught_vehicle.blend"
UNITY_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Onslaught"
UNITY_DIR.mkdir(parents=True, exist_ok=True)

with open(BONES_JSON, "r", encoding="utf-8") as f:
    bones_data = json.load(f)
bone_order = bones_data["bone_order"]
bones_dict = bones_data["bones"]


def unity_pos_to_blender(u_vec):
    return mathutils.Vector((u_vec[0], u_vec[2], u_vec[1]))


arm_data = bpy.data.armatures.new("character_vehicle_model")
arm_obj = bpy.data.objects.new("character_vehicle_model", arm_data)
bpy.context.scene.collection.objects.link(arm_obj)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='EDIT')

for name in bone_order:
    mat = mathutils.Matrix(bones_dict[name]["matrix"])
    b_head = unity_pos_to_blender(mat.to_translation())
    eb = arm_data.edit_bones.new(name)
    eb.head = b_head
    eb.tail = b_head + mathutils.Vector((0, 0, 0.1))

bpy.ops.object.mode_set(mode='OBJECT')

with bpy.data.libraries.load(str(VH_BLEND), link=False) as (data_from, data_to):
    data_to.objects = ["VH.dmx"]

vh_mesh = data_to.objects[0]
bpy.context.scene.collection.objects.link(vh_mesh)
bpy.context.view_layer.objects.active = vh_mesh
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
vh_mesh.modifiers.clear()

# Remove any pulled-in armatures or extras so ONLY character_vehicle_model + vh_mesh exist
for o in list(bpy.data.objects):
    if o not in (arm_obj, vh_mesh):
        bpy.data.objects.remove(o, do_unlink=True)

# Remap 4 material slots of VH.dmx to 2048x2048 Vehicle Atlas:
# - vh_body:     U[0.0, 0.5], V[0.5, 1.0]
# - vh_interior: U[0.0, 0.5], V[0.0, 0.5] (2x2 tiled!)
# - wheel:       U[0.5, 1.0], V[0.5, 1.0]
# - logo:        U[0.5, 1.0], V[0.0, 0.5]
uv_layer = vh_mesh.data.uv_layers.active
slot_names = [s.material.name.lower() if s.material else "" for s in vh_mesh.material_slots]
for poly in vh_mesh.data.polygons:
    mname = slot_names[poly.material_index] if poly.material_index < len(slot_names) else ""
    for li in poly.loop_indices:
        u, v = uv_layer.data[li].uv
        if "interior" in mname:
            # Map wrapped [-0.5..1.99] into 2x2 tiled [0.0..0.5] x [0.0..0.5]
            u_t = ((u % 2.0) + 2.0) % 2.0
            v_t = ((v % 2.0) + 2.0) % 2.0
            u_new = max(0.003, min(0.497, u_t * 0.25))
            v_new = max(0.003, min(0.497, v_t * 0.25))
        elif "wheel" in mname:
            u_new = max(0.004, min(0.996, u)) * 0.5 + 0.5
            v_new = max(0.004, min(0.996, v)) * 0.5 + 0.5
        elif "logo" in mname:
            u_new = max(0.004, min(0.996, u)) * 0.5 + 0.5
            v_new = max(0.004, min(0.996, v)) * 0.5 + 0.0
        else:
            # Main truck hull
            u_new = max(0.004, min(0.996, u)) * 0.5 + 0.0
            v_new = max(0.004, min(0.996, v)) * 0.5 + 0.5
        uv_layer.data[li].uv = (u_new, v_new)
vh_mesh.data.update()

# Single unified vehicle material
vh_mat = bpy.data.materials.new("M_Onslaught_Vh")
vh_mat.use_nodes = True
vh_tex = UNITY_DIR / "cha_onslaught_vh_a.png"
if vh_tex.exists():
    ti = vh_mat.node_tree.nodes.new("ShaderNodeTexImage")
    ti.image = bpy.data.images.load(str(vh_tex))
    vh_mat.node_tree.links.new(ti.outputs["Color"], vh_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
vh_mesh.data.materials.clear()
vh_mesh.data.materials.append(vh_mat)

# Orient front (+X in raw) -> +Y in Blender (+Z forward in Unity), scale 1.55x (~8.0m length matching Ironhide Topkick!)
bpy.ops.object.select_all(action='DESELECT')
vh_mesh.select_set(True)
bpy.context.view_layer.objects.active = vh_mesh
vh_mesh.rotation_euler = (0.0, 0.0, math.radians(90.0))
bpy.ops.object.transform_apply(rotation=True)

scale_val = 1.55
vh_mesh.scale = (scale_val, scale_val, scale_val)
bpy.ops.object.transform_apply(scale=True)

xs = [v.co.x for v in vh_mesh.data.vertices]
ys = [v.co.y for v in vh_mesh.data.vertices]
zs = [v.co.z for v in vh_mesh.data.vertices]
vh_mesh.location.x -= (min(xs) + max(xs)) * 0.5
vh_mesh.location.y -= (min(ys) + max(ys)) * 0.5
vh_mesh.location.z -= min(zs)
bpy.ops.object.transform_apply(location=True)

print(f"[✓] Vehicle bounds: X[{min(v.co.x for v in vh_mesh.data.vertices):.2f}, {max(v.co.x for v in vh_mesh.data.vertices):.2f}] "
      f"Y[{min(v.co.y for v in vh_mesh.data.vertices):.2f}, {max(v.co.y for v in vh_mesh.data.vertices):.2f}] "
      f"Z[{min(v.co.z for v in vh_mesh.data.vertices):.2f}, {max(v.co.z for v in vh_mesh.data.vertices):.2f}]")

vh_mesh.vertex_groups.clear()
for bname in bone_order:
    vh_mesh.vertex_groups.new(name=bname)
vh_mesh.vertex_groups["BodyBase"].add(list(range(len(vh_mesh.data.vertices))), 1.0, 'REPLACE')

vh_mesh.name = "cha_onslaught_gs_01"
vh_mesh.parent = arm_obj
mod = vh_mesh.modifiers.new(name="Armature", type='ARMATURE')
mod.object = arm_obj
mod.use_vertex_groups = True

out_fbx = UNITY_DIR / "onslaught_vh_prepared.fbx"
bpy.ops.object.select_all(action='DESELECT')
arm_obj.select_set(True)
vh_mesh.select_set(True)
bpy.context.view_layer.objects.active = arm_obj

bpy.ops.export_scene.fbx(
    filepath=str(out_fbx),
    use_selection=True,
    bake_anim=False,
    add_leaf_bones=False,
    apply_scale_options='FBX_SCALE_ALL',
    axis_forward='-Z',
    axis_up='Y',
)
print(f"[✓] Exported clean vehicle FBX: {out_fbx} ({out_fbx.stat().st_size} bytes)")
