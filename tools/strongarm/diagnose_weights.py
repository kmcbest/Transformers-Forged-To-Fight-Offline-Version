import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
import mathutils

fbx_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm\strongarm_prepared.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

mesh = bpy.data.objects["cha_prowl_gs_deluxe2016_00"]
arm = bpy.data.objects["character_model"]

print(f"Mesh: {mesh.name}, Vertices: {len(mesh.data.vertices)}")
print(f"Armature: {arm.name}, Bones: {len(arm.data.bones)}")

# Check vertex groups in mesh
vg_names = [vg.name for vg in mesh.vertex_groups]
print(f"Vertex groups count: {len(vg_names)}")

# Check for vertices with NO groups
unassigned = [v.index for v in mesh.data.vertices if not v.groups]
print(f"Unassigned vertices: {len(unassigned)}")

# In Unity, the FBX imported coordinates:
# Notice in Blender, after FBX import, arm bones and mesh:
# Let's check where each bone is in world space:
bone_world = {}
for b in arm.data.bones:
    bone_world[b.name] = arm.matrix_world @ b.head_local

# For each vertex, check its assigned bone and distance to that bone
# If the distance is > 2.0m, print summary
stray_counts = {}
for v in mesh.data.vertices:
    for g in v.groups:
        if g.weight > 0.5:
            vg_name = mesh.vertex_groups[g.group].name
            if vg_name in bone_world:
                b_pos = bone_world[vg_name]
                # Distance in (X, Y, Z)
                # But wait! In Blender after FBX import:
                # Mesh coordinates: let's check mesh world pos
                v_world = mesh.matrix_world @ v.co
                dist = (v_world - b_pos).length
                if dist > 2.5:
                    stray_counts[vg_name] = stray_counts.get(vg_name, 0) + 1

print("\nVertex groups with stray vertices (>2.5m from bone):")
for bname, cnt in sorted(stray_counts.items(), key=lambda x: -x[1]):
    print(f"  {bname:25s}: {cnt:5d} stray verts")
