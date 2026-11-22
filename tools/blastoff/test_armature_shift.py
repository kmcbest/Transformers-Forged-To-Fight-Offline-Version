import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
# Create a bone and a mesh
bpy.ops.object.armature_add()
arm = bpy.context.active_object
bpy.ops.mesh.primitive_cube_add()
cube = bpy.context.active_object

vg = cube.vertex_groups.new(name="Bone")
vg.add(list(range(len(cube.data.vertices))), 1.0, "REPLACE")

mod = cube.modifiers.new("Armature", "ARMATURE")
mod.object = arm

deps = bpy.context.evaluated_depsgraph_get()
ev0 = cube.evaluated_get(deps)
em0 = ev0.to_mesh()
z0 = min((ev0.matrix_world @ v.co).z for v in em0.vertices)
ev0.to_mesh_clear()
print(f"Initial cube min Z: {z0:.3f}")

# Shift both by -1.0m
arm.location.z -= 1.0
cube.location.z -= 1.0
bpy.context.view_layer.update()

ev1 = cube.evaluated_get(deps)
em1 = ev1.to_mesh()
z1 = min((ev1.matrix_world @ v.co).z for v in em1.vertices)
ev1.to_mesh_clear()
print(f"Shifted both arm and cube by -1.0m: min Z = {z1:.3f} (delta = {z1 - z0:.3f})")

# Shift only arm
arm.location.z += 1.0
cube.location.z += 1.0
bpy.context.view_layer.update()
arm.location.z -= 1.0
bpy.context.view_layer.update()

ev2 = cube.evaluated_get(deps)
em2 = ev2.to_mesh()
z2 = min((ev2.matrix_world @ v.co).z for v in em2.vertices)
ev2.to_mesh_clear()
print(f"Shifted only arm by -1.0m: min Z = {z2:.3f} (delta = {z2 - z0:.3f})")
