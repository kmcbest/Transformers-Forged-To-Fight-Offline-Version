import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\BlastOff\03_fbx_exports\blastoff_robot_prepared.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

o = bpy.data.objects['cha_blastoff_robot']
vs = o.data.vertices
high_v = [v for v in vs if v.co.z > 11.0]
print(f"Total verts > 11.0m: {len(high_v)} / {len(vs)}")

# Check Y (depth) and X (width) of these high vertices
ys = [v.co.y for v in high_v]
xs = [v.co.x for v in high_v]
zs = [v.co.z for v in high_v]
print(f"High verts X: [{min(xs):.2f}, {max(xs):.2f}]")
print(f"High verts Y (Fwd=-Y, Back=+Y): [{min(ys):.2f}, {max(ys):.2f}]")
vg_names = {vg.index: vg.name for vg in o.vertex_groups}
for target_bone in ["Head", "Neck", "Spine1", "Spine", "Hips", "LeftShoulderPad", "RightShoulderPad", "LeftUpLeg", "LeftLeg", "LeftFoot"]:
    bone_zs = []
    for v in vs:
        for g in v.groups:
            if vg_names.get(g.group) == target_bone and g.weight > 0.4:
                bone_zs.append(v.co.z)
    if bone_zs:
        print(f"Bone '{target_bone:16s}': Z=[{min(bone_zs):.2f}, {max(bone_zs):.2f}] (mean={sum(bone_zs)/len(bone_zs):.2f})")

