import bpy
import mathutils
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BLEND_FILE = ROOT / "tools" / "elita_one" / "elita_one_arcee_setup.blend"

bpy.ops.wm.open_mainfile(filepath=str(BLEND_FILE))

elita_arm = bpy.data.objects.get("Elita_One_Armature")
elita_mesh = bpy.data.objects.get("Elita_One_Mesh")
arcee = bpy.data.objects.get("Arcee_Ghost_Reference")

# Check bone head positions for Spine and Clavicles in Elita One
for bname in ['pelvis_skin', 'head_skin', 'l_upperarm_skin', 'r_upperarm_skin', 'l_foot_skin', 'r_foot_skin']:
    b = elita_arm.data.bones.get(bname)
    if b:
        print(f"Elita bone '{bname}': head = ({b.head_local.x:.2f}, {b.head_local.y:.2f}, {b.head_local.z:.2f})")

# Look at l_upperarm_skin vs r_upperarm_skin
l_arm = elita_arm.data.bones.get('l_upperarm_skin')
r_arm = elita_arm.data.bones.get('r_upperarm_skin')
if l_arm and r_arm:
    print(f"Vector from R_Arm to L_Arm (Shoulder Axis): {l_arm.head_local - r_arm.head_local}")
