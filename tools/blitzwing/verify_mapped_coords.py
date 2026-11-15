import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import bpy
from mathutils import Vector

# Verify the math of DetectAxisSpec on blitzwing_robot.fbx
bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r'E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\blitzwing_robot.fbx'
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]

def centroid_of(bname):
    vgs = [vg.index for vg in mesh.vertex_groups if vg.name == bname]
    if not vgs: return Vector((0,0,0))
    vs = [v.co for v in mesh.data.vertices if any(g.group == vgs[0] and g.weight > 0.3 for g in v.groups)]
    return sum(vs, Vector((0,0,0))) / len(vs) if vs else Vector((0,0,0))

cLH = centroid_of("LeftHand")
cRH = centroid_of("RightHand")
cToe = centroid_of("LeftToeBase")
cFoot = centroid_of("LeftFoot")

zIsHeight = True
sx = 1.0 if cLH.x <= 0 else -1.0
sz = 1.0 if (cToe != Vector() and cFoot != Vector() and cToe.y > cFoot.y) else -1.0
det = -1.0 * sx * sz

print(f"cLH={cLH}")
print(f"cRH={cRH}")
print(f"cToe={cToe}")
print(f"cFoot={cFoot}")
print(f"Detected: zIsHeight={zIsHeight}, sx={sx}, sz={sz}, det={det}")

# Test hand positions after mapping:
# nv = Vector((sx * v.x, v.z, sz * v.y))
mapped_lh = Vector((sx * cLH.x, cLH.z, sz * cLH.y))
mapped_rh = Vector((sx * cRH.x, cRH.z, sz * cRH.y))
mapped_toe = Vector((sx * cToe.x, cToe.z, sz * cToe.y))
mapped_foot = Vector((sx * cFoot.x, cFoot.z, sz * cFoot.y))

print(f"\nMapped LeftHand in Unity space:  {mapped_lh}")
print(f"Mapped RightHand in Unity space: {mapped_rh}")
print(f"Mapped LeftFoot in Unity space:  {mapped_foot}")
print(f"Mapped LeftToeBase in Unity space: {mapped_toe}")

# Compare with Megatron authoritative coordinates
ROOT = Path(r"E:\Agent\TFTF-blender")
MEG_51_JSON = ROOT / "tools" / "blitzwing" / "megatron_51_authoritative_bindposes.json"
meg_data = json.loads(MEG_51_JSON.read_text(encoding="utf-8"))

print("\nOfficial Megatron Reference coordinates:")
for b in ["LeftHand", "RightHand", "LeftFoot", "LeftToeBase"]:
    u_pos = meg_data["bones"][b]["unity_world_pos"]
    print(f"  {b:12s}: [{u_pos[0]:.4f}, {u_pos[1]:.4f}, {u_pos[2]:.4f}]")
