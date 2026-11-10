import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm\strongarm_prepared.fbx")
mesh = bpy.data.objects["cha_prowl_gs_deluxe2016_00"]

unassigned = [v for v in mesh.data.vertices if not v.groups]
print(f"Number of unassigned vertices: {len(unassigned)}")
if unassigned:
    co_sample = [v.co for v in unassigned[:10]]
    print(f"Sample unassigned vertex coords: {co_sample}")
    # Check bounding box of unassigned vertices
    min_x = min(v.co.x for v in unassigned)
    max_x = max(v.co.x for v in unassigned)
    min_y = min(v.co.y for v in unassigned)
    max_y = max(v.co.y for v in unassigned)
    min_z = min(v.co.z for v in unassigned)
    max_z = max(v.co.z for v in unassigned)
    print(f"Unassigned bounds: X=[{min_x:.3f}, {max_x:.3f}], Y=[{min_y:.3f}, {max_y:.3f}], Z=[{min_z:.3f}, {max_z:.3f}]")
