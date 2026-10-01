import bpy
import math
import mathutils
from pathlib import Path

ROOT = Path("tools/demolishor")
BLEND_PATH = ROOT / "demolishor_phase2_inspect.blend"
bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))

# Check location of RightShoulderPad vertices at frame 0, 10, 50:
mesh = bpy.data.objects.get("cha_demolishor_gs_01")
vg = mesh.vertex_groups.get("RightShoulderPad")
arm = bpy.data.objects.get("Ironhide_Reference_Armature")

if vg:
    pad_verts = [v.index for v in mesh.data.vertices for g in v.groups if g.group == vg.index and g.weight > 0.5]
    print(f"RightShoulderPad vertices count: {len(pad_verts)}")
    for f in [0, 10, 30, 50]:
        bpy.context.scene.frame_set(f)
        # In pose, evaluate mesh
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_mesh = mesh.evaluated_get(depsgraph)
        pts = [eval_mesh.matrix_world @ eval_mesh.data.vertices[idx].co for idx in pad_verts[:10]]
        avg_pos = sum(pts, mathutils.Vector()) / len(pts)
        print(f"Frame {f:2d}: RightShoulderPad average pos = X={avg_pos.x:.3f}, Y={avg_pos.y:.3f}, Z={avg_pos.z:.3f}")

# Render Frame 10 with SideFrontCam
bpy.context.scene.frame_current = 10
bpy.context.scene.render.filepath = str(ROOT.resolve() / "preview_shoulder_active_frame10.png")
bpy.ops.render.render(write_still=True)

# Render Frame 50
bpy.context.scene.frame_current = 50
bpy.context.scene.render.filepath = str(ROOT.resolve() / "preview_shoulder_active_frame50.png")
bpy.ops.render.render(write_still=True)

print("[✓] Rendered shoulder active frames!")
