import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import bpy
from pathlib import Path

OUT_FBX = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(OUT_FBX))

arm = None
mesh_obj = None
for o in bpy.context.scene.objects:
    if o.type == 'ARMATURE': arm = o
    if o.type == 'MESH': mesh_obj = o

print("Armature bones in elita_one_prepared.fbx:", len(arm.data.bones) if arm else None)
if arm:
    finger_bones = [b.name for b in arm.data.bones if any(k in b.name.lower() for k in ['finger', 'index', 'middle', 'ring', 'pinky', 'thumb'])]
    print("Finger bones in armature:", finger_bones)

print("Mesh vertex groups in elita_one_prepared.fbx:", len(mesh_obj.vertex_groups) if mesh_obj else None)
if mesh_obj:
    finger_vgs = [vg.name for vg in mesh_obj.vertex_groups if any(k in vg.name.lower() for k in ['finger', 'index', 'middle', 'ring', 'pinky', 'thumb'])]
    print("Finger vertex groups in mesh:", finger_vgs)
    # Check if they have vertices
    for vg_name in finger_vgs:
        vg = mesh_obj.vertex_groups.get(vg_name)
        cnt = sum(1 for v in mesh_obj.data.vertices for g in v.groups if g.group == vg.index and g.weight > 0.05)
        print(f"  {vg_name}: {cnt} verts")
