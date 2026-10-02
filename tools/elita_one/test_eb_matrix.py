import bpy
import mathutils
import numpy as np
import json

bpy.ops.wm.read_factory_settings(use_empty=True)

bindposes_raw = json.loads(open("tools/elita_one/arcee_extracted/arcee_bindposes.json").read())
bone_names = json.loads(open("tools/elita_one/arcee_63_bones.json").read())

arm_data = bpy.data.armatures.new("TestArm")
arm_obj = bpy.data.objects.new("TestArm", arm_data)
bpy.context.scene.collection.objects.link(arm_obj)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='EDIT')

# Test setting matrix on first bone
bp = bindposes_raw[0]
M_inv = np.array([
    [bp["e00"], bp["e01"], bp["e02"], bp["e03"]],
    [bp["e10"], bp["e11"], bp["e12"], bp["e13"]],
    [bp["e20"], bp["e21"], bp["e22"], bp["e23"]],
    [bp["e30"], bp["e31"], bp["e32"], bp["e33"]],
])
M_bone = np.linalg.inv(M_inv)

# In Unity to Blender conversion:
# Unity: X right, Y up, Z forward (left-handed)
# Blender: X right, Y forward, Z up (right-handed)
print("Testing bone matrix assignment in Blender...")
eb = arm_data.edit_bones.new(bone_names[0])
eb.head = (0, 0, 0)
eb.tail = (0, 1, 0)
print("Default eb.matrix:\n", eb.matrix)
