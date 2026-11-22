import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

OBJ_PATH = r"E:\Agent\TFTF-blender\3rd-party-models\BlastOff\00_donor_reference\cha_megatronus_gs_kabam_01_jet.obj"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=OBJ_PATH)

obj = bpy.context.selected_objects[0]
mw = obj.matrix_world
verts = [mw @ v.co for v in obj.data.vertices]

max_y = max(verts, key=lambda v: v.y)
min_y = min(verts, key=lambda v: v.y)
max_z = max(verts, key=lambda v: v.z)
min_z = min(verts, key=lambda v: v.z)

print(f"Imported Megatronus Jet:")
print(f"  Max Y: {max_y}")
print(f"  Min Y: {min_y}")
print(f"  Max Z: {max_z}")
print(f"  Min Z: {min_z}")

# Check which Y end has narrow width (nose) vs wide width (wings):
high_y_verts = [v for v in verts if v.y > 2.0]
low_y_verts = [v for v in verts if v.y < -2.0]

print(f"X span at High Y (> +2.0): {max(v.x for v in high_y_verts) - min(v.x for v in high_y_verts):.3f}")
print(f"X span at Low Y (< -2.0):  {max(v.x for v in low_y_verts) - min(v.x for v in low_y_verts):.3f}")
