import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Let's inspect blitzwing_robot.fbx:
# Compare each bone's head position vs the centroid of vertices weighted to that bone!
import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r'E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\blitzwing_robot.fbx'
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
arm = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE'][0]

print(f"Comparing bone head vs vertex centroid in blitzwing_robot.fbx:")
for bname in ['Head', 'Hips', 'LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase', 'RightUpLeg', 'RightLeg', 'RightFoot', 'RightToeBase', 'LeftArm', 'LeftForeArm', 'LeftHand']:
    bone = arm.data.bones.get(bname)
    vg = mesh.vertex_groups.get(bname)
    if bone and vg:
        vs = [v.co for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.3 for g in v.groups)]
        if vs:
            c = sum(vs, Vector()) / len(vs)
            diff = c - bone.head
            print(f"  {bname:14s}: BoneHead={bone.head} | VertCentroid={c} | Diff={diff} (len={diff.length:.3f})")
        else:
            print(f"  {bname:14s}: BoneHead={bone.head} | NO VERTICES!")
    else:
        print(f"  {bname:14s}: MISSING bone={bone is not None}, vg={vg is not None}")
