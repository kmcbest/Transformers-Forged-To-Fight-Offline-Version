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

print("=== BUILDING ALIGNED VORTEX VEHICLE (CYBERTRONIAN ATTACK HELICOPTER) ===")

bpy.ops.wm.read_factory_settings(use_empty=True)

ROOT = Path(r"E:\Agent\TFTF-blender")
BONES_JSON = ROOT / "tools" / "vortex" / "grindor_45_vh_bones.json"
AUTH_BP_JSON = ROOT / "tools" / "vortex" / "grindor_45_vh_authoritative_bindposes.json"
HIER_JSON = ROOT / "tools" / "vortex" / "grindor_45_vh_hierarchy.json"
VH_BLEND = ROOT / "3rd-party-models" / "vortex" / "vehicle" / "vortex_vehicle.blend"
UNITY_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Vortex"
UNITY_DIR.mkdir(parents=True, exist_ok=True)

with open(BONES_JSON, "r", encoding="utf-8") as f:
    bone_order = json.load(f)

bp_data = json.loads(AUTH_BP_JSON.read_text(encoding="utf-8"))
hier_data = json.loads(HIER_JSON.read_text(encoding="utf-8"))
parents_map = hier_data.get("parents", {})

# Convert Unity (ux, uy, uz) -> Blender (ux, uz, uy)
g_vh_pos = {}
for bname, info in bp_data.items():
    p = info["world_pos"]
    g_vh_pos[bname] = mathutils.Vector((p["x"], p["z"], p["y"]))

arm_data = bpy.data.armatures.new("character_vehicle_model")
arm_obj = bpy.data.objects.new("character_vehicle_model", arm_data)
bpy.context.scene.collection.objects.link(arm_obj)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='EDIT')

edit_bones = {}
for name in bone_order:
    b_head = g_vh_pos[name].copy()
    eb = arm_data.edit_bones.new(name)
    eb.head = b_head
    eb.tail = b_head + mathutils.Vector((0, 0, 0.15))
    edit_bones[name] = eb

for name in bone_order:
    p_name = parents_map.get(name)
    if p_name and p_name in edit_bones and p_name != name:
        edit_bones[name].parent = edit_bones[p_name]

bpy.ops.object.mode_set(mode='OBJECT')
print(f"[✓] Created official Grindor 45-bone vehicle armature!")

# Load VH mesh from vortex_vehicle.blend
with bpy.data.libraries.load(str(VH_BLEND), link=False) as (data_from, data_to):
    data_to.objects = ["VH_Vortex_SKEL.001.dmx"]

vh_mesh = data_to.objects[0]
bpy.context.scene.collection.objects.link(vh_mesh)
bpy.context.view_layer.objects.active = vh_mesh
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
vh_mesh.modifiers.clear()

# Remove pulled-in extras so only arm_obj + vh_mesh exist
for o in list(bpy.data.objects):
    if o not in (arm_obj, vh_mesh):
        bpy.data.objects.remove(o, do_unlink=True)

# Single unified vehicle material
vh_mat = bpy.data.materials.new("M_Vortex_Vh")
vh_mat.use_nodes = True
vh_tex = UNITY_DIR / "cha_vortex_vh_a.png"
if vh_tex.exists():
    ti = vh_mat.node_tree.nodes.new("ShaderNodeTexImage")
    ti.image = bpy.data.images.load(str(vh_tex))
    vh_mat.node_tree.links.new(ti.outputs["Color"], vh_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
vh_mesh.data.materials.clear()
vh_mesh.data.materials.append(vh_mat)

# Orient front (+X in raw) -> +Y in Blender (+Z forward in Unity)
bpy.ops.object.select_all(action='DESELECT')
vh_mesh.select_set(True)
bpy.context.view_layer.objects.active = vh_mesh
vh_mesh.rotation_euler = (0.0, 0.0, math.radians(90.0))
bpy.ops.object.transform_apply(rotation=True)

# Scale by 1.50 to match Grindor's helicopter length (~15m)
scale_val = 1.50
vh_mesh.scale = (scale_val, scale_val, scale_val)
bpy.ops.object.transform_apply(scale=True)

# Align position to Grindor's helicopter center
xs = [v.co.x for v in vh_mesh.data.vertices]
ys = [v.co.y for v in vh_mesh.data.vertices]
zs = [v.co.z for v in vh_mesh.data.vertices]

# Grindor's RotorMain is at (X=0.0, Y=0.16, Z=4.02)
# Align Vortex's main rotor center to Grindor's RotorMain
rotor_vgs = ["C_PropRobo18_XT", "C_PropRobo19_XT", "C_PropRobo20_XT", "C_PropRobo21_XT"]
rotor_indices = [v.index for v in vh_mesh.data.vertices if any(vh_mesh.vertex_groups.get(rn) and any(g.group == vh_mesh.vertex_groups[rn].index for g in v.groups) for rn in rotor_vgs)]
if rotor_indices:
    r_cx = sum(vh_mesh.data.vertices[i].co.x for i in rotor_indices) / len(rotor_indices)
    r_cy = sum(vh_mesh.data.vertices[i].co.y for i in rotor_indices) / len(rotor_indices)
    r_cz = sum(vh_mesh.data.vertices[i].co.z for i in rotor_indices) / len(rotor_indices)
else:
    r_cx, r_cy, r_cz = (min(xs) + max(xs)) * 0.5, (min(ys) + max(ys)) * 0.5, max(zs)

target_rotor = g_vh_pos["RotorMain"]
vh_mesh.location.x += (target_rotor.x - r_cx)
vh_mesh.location.y += (target_rotor.y - r_cy)
vh_mesh.location.z += (target_rotor.z - r_cz)
bpy.ops.object.transform_apply(location=True)

print(f"[✓] Vehicle bounds after alignment: "
      f"X[{min(v.co.x for v in vh_mesh.data.vertices):.2f}, {max(v.co.x for v in vh_mesh.data.vertices):.2f}] "
      f"Y[{min(v.co.y for v in vh_mesh.data.vertices):.2f}, {max(v.co.y for v in vh_mesh.data.vertices):.2f}] "
      f"Z[{min(v.co.z for v in vh_mesh.data.vertices):.2f}, {max(v.co.z for v in vh_mesh.data.vertices):.2f}]")

# Map vertex groups cleanly to Grindor's 45 vehicle bones
vh_bone_order_set = set(bone_order)
orig_vgs = {vg.name: vg.index for vg in vh_mesh.vertex_groups}

ROTOR_EXACT_VGS = {
    "C_BodyRobo06_XT",
    "C_BodyRobo16_XT",
    "C_BodyRobo17_XT",
    "C_BodyRobo18_XT",
    "C_PropRobo18_XT",
    "C_BodyRobo19_XT",
    "C_PropRobo19_XT",
    "C_BodyRobo20_XT",
    "C_PropRobo20_XT",
    "C_BodyRobo21_XT",
    "C_PropRobo21_XT",
}

def resolve_vh_bone(vg_name, v_co):
    if vg_name in ROTOR_EXACT_VGS:
        return "RotorMain"
    vgn = vg_name.lower()
    if "tail" in vgn or "fin" in vgn: return "Tail"
    if "wing" in vgn: return "WingLeft" if v_co.x < 0 else "WingRight"
    if "head" in vgn or "nose" in vgn: return "BodyHeadLeft" if v_co.x < 0 else "BodyHeadRight"
    if v_co.y < -5.0: return "Tail"
    if v_co.y > 2.0: return "BodyHeadLeft" if v_co.x < 0 else "BodyHeadRight"
    if abs(v_co.x) > 1.8: return "WingLeft" if v_co.x < 0 else "WingRight"
    return "BodyMainCenterTopLeft" if v_co.x < 0 else "BodyMainCenterTopRight"

vh_weights = [{} for _ in range(len(vh_mesh.data.vertices))]
for v in vh_mesh.data.vertices:
    w_acc = {}
    for g in v.groups:
        vg_name = list(orig_vgs.keys())[list(orig_vgs.values()).index(g.group)]
        tb = resolve_vh_bone(vg_name, v.co)
        w_acc[tb] = w_acc.get(tb, 0.0) + g.weight
    if not w_acc:
        tb = resolve_vh_bone("", v.co)
        w_acc[tb] = 1.0
    tot = sum(w_acc.values())
    vh_weights[v.index] = {b: w / tot for b, w in w_acc.items()}

vh_mesh.vertex_groups.clear()
for bname in bone_order:
    vh_mesh.vertex_groups.new(name=bname)

for vi, wd in enumerate(vh_weights):
    for bname, w in wd.items():
        vh_mesh.vertex_groups[bname].add([vi], w, 'REPLACE')

rotor_indices = [vi for vi, wd in enumerate(vh_weights) if wd.get("RotorMain", 0.0) > 0.5]
print(f"[✓] Identified {len(rotor_indices)} vertices belonging to RotorMain!")
rotor_json = ROOT / "tools" / "vortex" / "vortex_vh_rotor_indices.json"
rotor_json.write_text(json.dumps(rotor_indices, indent=2), encoding="utf-8")
(UNITY_DIR / "vortex_vh_rotor_indices.json").write_text(json.dumps(rotor_indices, indent=2), encoding="utf-8")

vh_mesh.name = "cha_vortex_gs_01"
vh_mesh.parent = arm_obj
mod = vh_mesh.modifiers.new(name="Armature", type='ARMATURE')
mod.object = arm_obj
mod.use_vertex_groups = True

out_fbx = UNITY_DIR / "vortex_vh_prepared.fbx"
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
