import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy
from io_scene_fbx import parse_fbx
from mathutils import Vector

FBX_SRC = Path(r"e:\Agent\TFTF-blender\3rd-party-models\swoop\01_master\Swoop_pbr.fbx")

elem, _ = parse_fbx.parse(str(FBX_SRC))
objects = next(e for e in elem.elems if e.id == b'Objects')
connections = next(e for e in elem.elems if e.id == b'Connections')

models = {}
clusters = {}
for e in objects.elems:
    if e.id == b'Model':
        models[e.props[0]] = e.props[1].split(b'\x00')[0].decode('utf-8', errors='replace')
    elif e.id == b'Deformer' and len(e.props) >= 3 and e.props[2] == b'Cluster':
        for sub in e.elems:
            if sub.id == b'TransformLink':
                clusters[e.props[0]] = sub.props[0]

c_to_m = {}
tl_scales = {}
for c in connections.elems:
    if c.id == b'C':
        src, dst = c.props[1], c.props[2]
        if src in models and dst in clusters:
            bname = models[src]
            tl = clusters[dst]
            c_to_m[bname] = tl
            tl_scales[bname] = (tl[0] ** 2 + tl[1] ** 2 + tl[2] ** 2) ** 0.5

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))
arm = bpy.data.objects.get("Bip001")
mesh = bpy.data.objects.get("Swoop.001")

# Print parent chain and TransformLink for bird_neck, bird_Head, beak, beak_the bottom, bird_Head_02
head_bones = ["Bone_Spine1", "bird_chest", "bird_neck", "bird_Head", "bird_Head_02", "beak", "beak_the bottom", "Bone_Head"]
print("=== Rest Pose EditBones & TransformLink ===")
for bname in head_bones:
    b = arm.data.bones.get(bname)
    tl = c_to_m.get(bname)
    s = tl_scales.get(bname, 1.0)
    pname = b.parent.name if b and b.parent else "None"
    th = Vector((tl[12], tl[13], tl[14])) if tl else Vector()
    print(f"  {bname:<18} (parent={pname:<14}) tl_scale={s:.4f} tl_pos=({th.x:+.4f},{th.y:+.4f},{th.z:+.4f}) b.head_local=({b.head_local.x:+.4f},{b.head_local.y:+.4f},{b.head_local.z:+.4f})")

# Check vertex bounding boxes in Raw Static Pose vs vehicle_idle01 Frame 1
vg_map = {vg.name: vg.index for vg in mesh.vertex_groups}
print("\n=== Raw Static Pose Vertex Bounds (Mesh Local Space) ===")
for vgn in head_bones:
    if vgn not in vg_map:
        continue
    vgi = vg_map[vgn]
    pts = [v.co for v in mesh.data.vertices if any(g.group == vgi and g.weight > 0.5 for g in v.groups)]
    if pts:
        print(f"  {vgn:<18} ({len(pts):3d}v): X=[{min(p.x for p in pts):+.3f},{max(p.x for p in pts):+.3f}] Y=[{min(p.y for p in pts):+.3f},{max(p.y for p in pts):+.3f}] Z=[{min(p.z for p in pts):+.3f},{max(p.z for p in pts):+.3f}]")

act = bpy.data.actions.get("Bip001|vehicle_idle01|Base Layer")
arm.animation_data.action = act
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()

print("\n=== Pose Bones at vehicle_idle01 Frame 1 (Unmodified Blender Import) ===")
for bname in head_bones:
    pb = arm.pose.bones.get(bname)
    if pb:
        print(f"  {bname:<18} loc=({pb.location.x:+.4f},{pb.location.y:+.4f},{pb.location.z:+.4f}) quat=({pb.rotation_quaternion.w:+.3f},{pb.rotation_quaternion.x:+.3f},{pb.rotation_quaternion.y:+.3f},{pb.rotation_quaternion.z:+.3f}) scale=({pb.scale.x:.3f},{pb.scale.y:.3f},{pb.scale.z:.3f})")
