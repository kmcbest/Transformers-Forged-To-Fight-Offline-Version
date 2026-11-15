import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(r"E:\Agent\TFTF-blender")
MEG_51_JSON = ROOT / "tools" / "blitzwing" / "megatron_51_authoritative_bindposes.json"
meg_data = json.loads(MEG_51_JSON.read_text(encoding="utf-8"))

def u_to_b(pos):
    return Vector((-float(pos[0]), -float(pos[2]), float(pos[1])))

bpy.ops.wm.read_factory_settings(use_empty=True)
arm_data = bpy.data.armatures.new("character_model")
arm_obj = bpy.data.objects.new("character_model", arm_data)
bpy.context.scene.collection.objects.link(arm_obj)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='EDIT')

edit_bones = {}
for bname in meg_data["bone_names"]:
    b_info = meg_data["bones"][bname]
    head_pos = u_to_b(b_info["unity_world_pos"])
    eb = arm_data.edit_bones.new(bname)
    eb.head = head_pos
    eb.tail = head_pos + Vector((0, -0.08, 0))
    edit_bones[bname] = eb

for bname in meg_data["bone_names"]:
    b_info = meg_data["bones"][bname]
    parent_name = b_info.get("parent")
    if parent_name and parent_name in edit_bones and parent_name != bname:
        eb = edit_bones[bname]
        eb.parent = edit_bones[parent_name]

print("Armature edit bones in Blender:")
for bname in ['Head', 'Hips', 'LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase', 'LeftArm', 'LeftForeArm', 'LeftHand']:
    eb = edit_bones.get(bname)
    if eb:
        print(f"  {bname:14s}: head={eb.head}, tail={eb.tail}")
