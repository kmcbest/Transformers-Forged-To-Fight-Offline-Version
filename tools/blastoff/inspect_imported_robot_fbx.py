import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

FBX_PATH = r"E:\Agent\TFTF-blender\3rd-party-models\BlastOff\03_fbx_exports\blastoff_robot_prepared.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']

print(f"Meshes: {[m.name for m in meshes]}")
print(f"Armatures: {[a.name for a in arms]}")

m = meshes[0]
arm = arms[0]

vg_map = {vg.name: vg.index for vg in m.vertex_groups}

for bname in ["LeftArm", "RightArm", "LeftHand", "RightHand", "LeftShoulder", "RightShoulder"]:
    if bname in vg_map:
        idx = vg_map[bname]
        pts = [m.matrix_world @ v.co for v in m.data.vertices if any(g.group == idx and g.weight > 0.4 for g in v.groups)]
        if pts:
            mx = sum(p.x for p in pts) / len(pts)
            my = sum(p.y for p in pts) / len(pts)
            mz = sum(p.z for p in pts) / len(pts)
            print(f"Vertex Group [{bname:15s}]: count={len(pts):4d}, mean=({mx:7.2f}, {my:7.2f}, {mz:7.2f})")
    if bname in arm.pose.bones:
        pb = arm.pose.bones[bname]
        wpos = arm.matrix_world @ pb.head
        print(f"Pose Bone    [{bname:15s}]: head=({wpos.x:7.2f}, {wpos.y:7.2f}, {wpos.z:7.2f})")
