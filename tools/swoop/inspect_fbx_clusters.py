import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy
from mathutils import Vector

FBX_SRC = Path("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/Swoop_pbr.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

arm = bpy.data.objects.get("Bip001")
mesh = bpy.data.objects.get("Swoop.001")
act = bpy.data.actions.get("Bip001|vehicle_idle01|Base Layer")
arm.animation_data.action = act
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()

deps = bpy.context.evaluated_depsgraph_get()
ev = mesh.evaluated_get(deps)

# Print every vertex group's bounding box in evaluated vehicle_idle01 frame 1 (in mesh local space!)
print("=== All Vertex Group Bounds in vehicle_idle01 Frame 1 (Mesh Local Space) ===")
for vg in mesh.vertex_groups:
    pts = [ev.data.vertices[v.index].co for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
    if pts:
        print(f"  {vg.name:28s} (n={len(pts):4d}): X=[{min(p.x for p in pts):+6.3f},{max(p.x for p in pts):+6.3f}], Y=[{min(p.y for p in pts):+6.3f},{max(p.y for p in pts):+6.3f}], Z=[{min(p.z for p in pts):+6.3f},{max(p.z for p in pts):+6.3f}]")
