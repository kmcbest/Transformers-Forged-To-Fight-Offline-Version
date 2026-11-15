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

arm_mod = mesh_obj.modifiers.new("Armature", "ARMATURE")
arm_mod.object = arm_obj
bpy.context.view_layer.objects.active = mesh_obj
mesh_obj.select_set(True)
bpy.ops.object.modifier_apply(modifier="Armature")

old_vg = {vg.index: vg.name for vg in mesh_obj.vertex_groups}

# Test the rule
leg_count = 0
foot_count = 0
toe_count = 0

for v in mesh_obj.data.vertices:
    vg_names = [old_vg.get(g.group) for g in v.groups]
    if 'bip_knee_L' in vg_names:
        leg_count += 1
    elif 'bip_toe_L' in vg_names:
        toe_count += 1
    elif 'bip_foot_L' in vg_names:
        foot_count += 1

print(f"Rule results for Left Leg/Foot:")
print(f"  LeftLeg (rigid shin including 368 overlap): {leg_count}")
print(f"  LeftFoot (pure foot sole/heel): {foot_count}")
print(f"  LeftToeBase (pure toes): {toe_count}")
print(f"Total: {leg_count + foot_count + toe_count}")
