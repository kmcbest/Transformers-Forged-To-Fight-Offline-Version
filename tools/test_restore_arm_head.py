import bpy
import mathutils
import math
from pathlib import Path

# Test script:
# 1. Lower head back to neck socket (-0.36m Z, -0.24m Y)
# 2. Import CP_DemolishorArm from FBX, transform and attach to Right Forearm!

BLEND_PATH = "tools/demolishor/demolishor_phase2_inspect.blend"
bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)

mesh = bpy.data.objects.get("cha_demolishor_gs_01")
arm = bpy.data.objects.get("Ironhide_Reference_Armature")

head_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name.lower() for k in ["head", "face", "jaw"])]
print(f"Head VGs: {head_vgs}")

# Lower head vertices by -0.32 Z, -0.15 Y so it sits snugly in the neck cavity
head_verts = [v for v in mesh.data.vertices if any(g.group in head_vgs for g in v.groups)]
print(f"Lowering {len(head_verts)} head vertices back to neck cavity...")
for v in head_verts:
    v.co.z -= 0.34
    v.co.y -= 0.18

mesh.data.update()

# Now import CP_DemolishorArm from original FBX
fbx_path = Path("3rd-party-models/transformers-fall-of-cybertron-demolishor/source/transformers fall of cybertron Demolishor.fbx").resolve()
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

cp_mesh = bpy.data.objects.get("CP_DemolishorArm_SKEL.mo.dmx")
if cp_mesh:
    print(f"Successfully imported CP_DemolishorArm with {len(cp_mesh.data.vertices)} vertices!")

# Clean extra imported objects (Demolishor_ARM, Demolishor_VH_ARM, VH_Demolishor_SKEL, RB_Demolishor)
for obj in list(bpy.data.objects):
    if obj not in [mesh, arm, cp_mesh]:
        if obj.type in ['ARMATURE', 'MESH'] and obj.name != "Ironhide_Ghost_Reference":
            bpy.data.objects.remove(obj, do_unlink=True)

print("Objects in scene now:", [o.name for o in bpy.data.objects])
