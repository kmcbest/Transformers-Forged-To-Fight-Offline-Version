import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

target_names = [
    "VH_Blastoff_SKEL.mo.dmx",
    "VH_BlastoffWing_STAT.mo.001.dmx",
    "VH_BlastoffWing_STAT.mo.dmx",
]

print("=== Raw Blast Off Vehicle Meshes ===")
for name in target_names:
    o = bpy.data.objects.get(name)
    if not o:
        print(f"NOT FOUND: {name}")
        continue
    # World matrix transform vertices
    mw = o.matrix_world
    world_co = [mw @ v.co for v in o.data.vertices]
    xs = [v.x for v in world_co]
    ys = [v.y for v in world_co]
    zs = [v.z for v in world_co]
    print(f"\nObject: {name}")
    print(f"  Parent: {o.parent.name if o.parent else None}")
    print(f"  Matrix World: loc={mw.to_translation()}, rot_euler={[round(r, 2) for r in mw.to_euler()]}")
    print(f"  Vertex Count: {len(world_co)}")
    print(f"  X: [{min(xs):.3f}, {max(xs):.3f}] (size={max(xs)-min(xs):.3f})")
    print(f"  Y: [{min(ys):.3f}, {max(ys):.3f}] (size={max(ys)-min(ys):.3f})")
    print(f"  Z: [{min(zs):.3f}, {max(zs):.3f}] (size={max(zs)-min(zs):.3f})")
    print(f"  Materials: {[s.name for s in o.material_slots]}")

# Also check overall combined bounding box:
all_co = []
for name in target_names:
    o = bpy.data.objects.get(name)
    if o:
        mw = o.matrix_world
        all_co.extend([mw @ v.co for v in o.data.vertices])

print("\n=== Combined Vehicle Bounding Box (Raw World Coords) ===")
xs = [v.x for v in all_co]
ys = [v.y for v in all_co]
zs = [v.z for v in all_co]
print(f"X: [{min(xs):.3f}, {max(xs):.3f}] (size={max(xs)-min(xs):.3f})")
print(f"Y: [{min(ys):.3f}, {max(ys):.3f}] (size={max(ys)-min(ys):.3f})")
print(f"Z: [{min(zs):.3f}, {max(zs):.3f}] (size={max(zs)-min(zs):.3f})")
