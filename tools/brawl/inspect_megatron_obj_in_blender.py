import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)

obj_path = r"E:\Agent\TFTF-blender\3rd-party-models\Brawl\00_donor_reference\cha_megatron_cin_rotf_00_robot.obj"
bpy.ops.wm.obj_import(filepath=obj_path)

meg_obj = bpy.context.selected_objects[0]
print(f"Imported Megatron OBJ: {meg_obj.name}")
print(f"Dimensions: {meg_obj.dimensions}")
min_v = [min(v.co[i] for v in meg_obj.data.vertices) for i in range(3)]
max_v = [max(v.co[i] for v in meg_obj.data.vertices) for i in range(3)]
print(f"Bounds in Blender: X=[{min_v[0]:.4f}, {max_v[0]:.4f}], Y=[{min_v[1]:.4f}, {max_v[1]:.4f}], Z=[{min_v[2]:.4f}, {max_v[2]:.4f}]")
