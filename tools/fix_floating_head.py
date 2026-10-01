import bpy
from pathlib import Path

ROOT = Path("tools/demolishor")
BLEND_PATH = ROOT / "demolishor_phase2_inspect.blend"

bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))

mesh = bpy.data.objects.get("cha_demolishor_gs_01")
head_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name.lower() for k in ["head", "face", "jaw"])]
head_verts = [v for v in mesh.data.vertices if any(g.group in head_vgs for g in v.groups)]

print(f"Lowering {len(head_verts)} head vertices back into neck socket...")
# In v5, it shifted +0.36 Z and +0.24 Y
# Lower back by -0.34 Z and -0.18 Y so visor remains visible but neck is snugly enclosed in collar
for v in head_verts:
    v.co.z -= 0.34
    v.co.y -= 0.18

mesh.data.update()

bpy.context.scene.frame_current = 0
bpy.ops.wm.save_mainfile(filepath=str(BLEND_PATH))
print(f"[✓] Successfully restored head to natural socket!")
