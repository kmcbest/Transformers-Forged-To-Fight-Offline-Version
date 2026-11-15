import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Run the exact code of build_aligned_blitzwing.py up to line 305 and check vz of foot vertices!
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

# Modifier apply
arm_mod = mesh_obj.modifiers.new("Armature", "ARMATURE")
arm_mod.object = arm_obj
bpy.context.view_layer.objects.active = mesh_obj
mesh_obj.select_set(True)
bpy.ops.object.modifier_apply(modifier="Armature")

old_vg_by_index = {vg.index: vg.name for vg in mesh_obj.vertex_groups}
foot_zs = [v.co.z for v in mesh_obj.data.vertices if any(old_vg_by_index.get(g.group) == 'bip_foot_L' for g in v.groups)]
print(f"Foot v.co.z right after modifier_apply: min={min(foot_zs):.3f}, max={max(foot_zs):.3f}")
print(f"BOOT_Z_THRESH = {0.35 * SCALE:.3f}")
below = sum(1 for z in foot_zs if z <= 0.35 * SCALE)
print(f"Number of foot vertices <= BOOT_Z_THRESH: {below} / {len(foot_zs)}")
