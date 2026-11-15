import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Let's inspect the mesh after pose_segment_world in build_aligned_blitzwing.py
# Does the hand look normal in Blender or is it already distorted?
import bpy
from mathutils import Vector, Matrix

ROOT = bpy.path.abspath("//")
# Let's import the exported blitzwing_robot.fbx into Blender and inspect the vertices of the hand
bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r'E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\blitzwing_robot.fbx'
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]

# Check bounding box of Left Hand finger vertices in blitzwing_robot.fbx
for side in ['Left', 'Right']:
    vgs = [vg.index for vg in mesh.vertex_groups if side in vg.name and ('Finger' in vg.name or 'Thumb' in vg.name or 'Middle' in vg.name or 'Index' in vg.name or 'Ring' in vg.name or 'Pinky' in vg.name)]
    fvs = [v.co for v in mesh.data.vertices if any(g.group in vgs and g.weight > 0.1 for g in v.groups)]
    print(f"\n{side} Fingers in FBX: {len(fvs)} vertices")
    for axis, i in [('X', 0), ('Y', 1), ('Z', 2)]:
        vals = [v[i] for v in fvs]
        print(f"  {axis}: [{min(vals):.3f}, {max(vals):.3f}] (span={max(vals)-min(vals):.3f})")
