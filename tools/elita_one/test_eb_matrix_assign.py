import bpy
import mathutils

bpy.ops.wm.read_factory_settings(use_empty=True)
arm = bpy.data.armatures.new("TestArm")
obj = bpy.data.objects.new("TestArm", arm)
bpy.context.scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode='EDIT')

eb = arm.edit_bones.new("Bone1")
mat = mathutils.Matrix.Rotation(1.57, 4, 'X')
mat.translation = mathutils.Vector((1, 2, 3))

eb.matrix = mat
print("After setting eb.matrix:")
print("  head:", eb.head)
print("  tail:", eb.tail)
print("  matrix:", eb.matrix)
print("  length:", eb.length)
