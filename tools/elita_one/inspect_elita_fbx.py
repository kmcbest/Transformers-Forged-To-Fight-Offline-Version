import bpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"

print(f"=== Inspecting Elita One FBX: {FBX_PATH.name} ===")
# Clear current scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Import FBX
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

print(f"\nImported {len(bpy.data.objects)} objects:")
armatures = []
meshes = []
for obj in bpy.data.objects:
    print(f"  [{obj.type:8s}] {obj.name:30s} parent: {obj.parent.name if obj.parent else 'None'}")
    if obj.type == 'ARMATURE':
        armatures.append(obj)
    elif obj.type == 'MESH':
        meshes.append(obj)

for arm in armatures:
    print(f"\nArmature '{arm.name}': {len(arm.data.bones)} bones")
    bones = [b.name for b in arm.data.bones]
    print(f"  First 20 bones: {bones[:20]}")
    print(f"  Last 10 bones: {bones[-10:]}")

for m in meshes:
    print(f"\nMesh '{m.name}': {len(m.data.vertices)} verts, {len(m.data.polygons)} polys, {len(m.vertex_groups)} VGs")
    dim = m.dimensions
    print(f"  Dimensions: X={dim.x:.2f}m, Y={dim.y:.2f}m, Z={dim.z:.2f}m")
    bb = m.bound_box
    z_min = min(v[2] for v in bb)
    z_max = max(v[2] for v in bb)
    print(f"  Z range: [{z_min:.2f}m, {z_max:.2f}m]")
    print(f"  Materials: {[mat.name for mat in m.data.materials if mat]}")
    if m.vertex_groups:
        print(f"  Sample VGs: {[vg.name for vg in m.vertex_groups[:15]]}")
