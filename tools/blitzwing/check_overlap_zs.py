import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy
from mathutils import Matrix

ROOT = Path(r"E:\Agent\TFTF-blender")
BLEND_SRC = ROOT / "3rd-party-models" / "blitzwing_extracted" / "rar" / "Blitzwing.blend"

bpy.ops.wm.open_mainfile(filepath=str(BLEND_SRC))
mesh_obj = bpy.data.objects['Blitzwing']
arm_obj = bpy.data.objects['Blitzwing_Skeleton']

if mesh_obj.data.shape_keys:
    bpy.context.view_layer.objects.active = mesh_obj
    mesh_obj.select_set(True)
    bpy.ops.object.shape_key_remove(all=True)

SCALE = 1.4803
min_z = min(v.co.z for v in mesh_obj.data.vertices)
ground_scale_mat = Matrix.Scale(SCALE, 4) @ Matrix.Translation((0, 0, -min_z))
mesh_obj.data.transform(ground_scale_mat)
mesh_obj.data.update()

# Modifier apply as in script
arm_mod = mesh_obj.modifiers.new("Armature", "ARMATURE")
arm_mod.object = arm_obj
bpy.context.view_layer.objects.active = mesh_obj
mesh_obj.select_set(True)
bpy.ops.object.modifier_apply(modifier="Armature")

old_vg_by_index = {vg.index: vg.name for vg in mesh_obj.vertex_groups}

for vg_name in ['bip_toe_L', 'bip_foot_L', 'bip_knee_L']:
    zs = [v.co.z for v in mesh_obj.data.vertices if any(old_vg_by_index.get(g.group) == vg_name for g in v.groups)]
    print(f"{vg_name:12s}: count={len(zs):4d}, Z range=[{min(zs):.3f}, {max(zs):.3f}]")

# Check vertices that belong to bip_knee_L AND bip_foot_L (the overlap area!)
overlap = [v.co.z for v in mesh_obj.data.vertices if any(old_vg_by_index.get(g.group) == 'bip_knee_L' for g in v.groups) and any(old_vg_by_index.get(g.group) == 'bip_foot_L' for g in v.groups)]
print(f"Overlap knee+foot vertices: count={len(overlap)}, Z range=[{min(overlap):.3f}, {max(overlap):.3f}]")

# Check toe vertices (pure foot/toe)
pure_foot_or_toe = [v.co.z for v in mesh_obj.data.vertices if any(old_vg_by_index.get(g.group) in ['bip_foot_L', 'bip_toe_L'] for g in v.groups) and not any(old_vg_by_index.get(g.group) == 'bip_knee_L' for g in v.groups)]
print(f"Pure foot/toe (no knee): count={len(pure_foot_or_toe)}, Z range=[{min(pure_foot_or_toe):.3f}, {max(pure_foot_or_toe):.3f}]")
