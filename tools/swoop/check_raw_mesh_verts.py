import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FBX_PATH = ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

swoop_mesh = bpy.data.objects.get("Swoop.001")
raw_mesh = swoop_mesh.data

# Raw vertices without any modifier
vs = [v.co for v in raw_mesh.vertices]
xs = [v.x for v in vs]
ys = [v.y for v in vs]
zs = [v.z for v in vs]

print(f"RAW MESH DATA VERTICES (len={len(vs)}):")
print(f"  X: [{min(xs):.3f}, {max(xs):.3f}] span={max(xs)-min(xs):.3f}")
print(f"  Y: [{min(ys):.3f}, {max(ys):.3f}] span={max(ys)-min(ys):.3f}")
print(f"  Z: [{min(zs):.3f}, {max(zs):.3f}] span={max(zs)-min(zs):.3f}")

# Check head vertex
vg_head = swoop_mesh.vertex_groups.get("Bone_Head") or swoop_mesh.vertex_groups.get("Bip001 Head")
if vg_head:
    head_verts = [v.co for v in raw_mesh.vertices if any(g.group == vg_head.index and g.weight > 0.5 for g in v.groups)]
    print(f"Head verts (count={len(head_verts)}):")
    h_xs = [v.x for v in head_verts]
    h_ys = [v.y for v in head_verts]
    h_zs = [v.z for v in head_verts]
    print(f"  Head mean: X={sum(h_xs)/len(h_xs):.3f}, Y={sum(h_ys)/len(h_ys):.3f}, Z={sum(h_zs)/len(h_zs):.3f}")

# Check hand vertex
vg_hand = swoop_mesh.vertex_groups.get("Bone_L_Hand") or swoop_mesh.vertex_groups.get("Bip001 L Hand")
if vg_hand:
    hand_verts = [v.co for v in raw_mesh.vertices if any(g.group == vg_hand.index and g.weight > 0.5 for g in v.groups)]
    print(f"Left Hand verts (count={len(hand_verts)}):")
    h_xs = [v.x for v in hand_verts]
    h_ys = [v.y for v in hand_verts]
    h_zs = [v.z for v in hand_verts]
    print(f"  Hand mean: X={sum(h_xs)/len(h_xs):.3f}, Y={sum(h_ys)/len(h_ys):.3f}, Z={sum(h_zs)/len(h_zs):.3f}")

# Check foot vertex
vg_foot = swoop_mesh.vertex_groups.get("Bone_L_Foot") or swoop_mesh.vertex_groups.get("Bip001 L Foot")
if vg_foot:
    foot_verts = [v.co for v in raw_mesh.vertices if any(g.group == vg_foot.index and g.weight > 0.5 for g in v.groups)]
    print(f"Left Foot verts (count={len(foot_verts)}):")
    h_xs = [v.x for v in foot_verts]
    h_ys = [v.y for v in foot_verts]
    h_zs = [v.z for v in foot_verts]
    print(f"  Foot mean: X={sum(h_xs)/len(h_xs):.3f}, Y={sum(h_ys)/len(h_ys):.3f}, Z={sum(h_zs)/len(h_zs):.3f}")
