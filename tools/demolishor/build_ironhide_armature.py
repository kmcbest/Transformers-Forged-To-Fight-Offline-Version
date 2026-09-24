# -*- coding: utf-8 -*-
import bpy
import json
import mathutils
from pathlib import Path

bpy.ops.wm.read_factory_settings(use_empty=True)

with open("tools/demolishor/ironhide_extracted/ironhide_transforms.json", "r", encoding="utf-8") as f:
    transforms = json.load(f)

# Find root of Ironhide
root_pid = "5877212488468470809" # IronHide_Cin_ROTF

# Compute world transform for each node
world_matrices = {}

def compute_world_matrix(pid, parent_matrix):
    node = transforms.get(str(pid))
    if not node: return
    pos = node["localPosition"]
    rot = node["localRotation"]
    scl = node["localScale"]
    
    # Unity translation: (x, y, z)
    # Unity rotation quaternion: (x, y, z, w)
    # Unity scale: (x, y, z)
    t = mathutils.Vector((pos.get("x", 0), pos.get("y", 0), pos.get("z", 0)))
    q = mathutils.Quaternion((rot.get("w", 1), rot.get("x", 0), rot.get("y", 0), rot.get("z", 0)))
    s = mathutils.Vector((scl.get("x", 1), scl.get("y", 1), scl.get("z", 1)))
    
    # Compose local matrix
    local_mat = mathutils.Matrix.LocRotScale(t, q, s)
    world_mat = parent_matrix @ local_mat
    world_matrices[str(pid)] = world_mat
    
    for c_pid in node["children_pids"]:
        compute_world_matrix(c_pid, world_mat)

compute_world_matrix(root_pid, mathutils.Matrix.Identity(4))

# Create an Armature in Blender
arm_data = bpy.data.armatures.new("Ironhide_ARM")
arm_obj = bpy.data.objects.new("Ironhide_ARM", arm_data)
bpy.context.scene.collection.objects.link(arm_obj)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='EDIT')

edit_bones = {}

def add_bones(pid, parent_bone_name=None):
    node = transforms.get(str(pid))
    if not node: return
    name = node["name"]
    w_mat = world_matrices.get(str(pid))
    
    # Don't add 'transformed' vehicle nodes to combat humanoid armature
    if name == "transformed" or name.startswith("chop"):
        return
        
    b = arm_data.edit_bones.new(name)
    pos = w_mat.to_translation()
    b.head = pos
    # Give it a small default length
    b.tail = pos + mathutils.Vector((0, 0.1, 0))
    if parent_bone_name and parent_bone_name in arm_data.edit_bones:
        b.parent = arm_data.edit_bones[parent_bone_name]
        # Align parent tail to child head if suitable
        p_bone = arm_data.edit_bones[parent_bone_name]
        if (pos - p_bone.head).length > 0.01:
            p_bone.tail = pos
            
    for c_pid in node["children_pids"]:
        add_bones(c_pid, name)

add_bones(root_pid)
bpy.ops.object.mode_set(mode='OBJECT')

print(f"[✓] Created Ironhide Armature with {len(arm_obj.data.bones)} bones!")
for b in arm_obj.data.bones[:20]:
    print(f"  {b.name} (head: {b.head})")
