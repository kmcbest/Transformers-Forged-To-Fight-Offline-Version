import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Vector

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

armature = bpy.data.objects.get("brawl_ARM")
print("Armature bones count:", len(armature.data.bones))

for o in bpy.data.objects:
    if o.type == 'MESH' and ('Cap' in o.name or 'Arm' in o.name):
        vgs = [vg.name for vg in o.vertex_groups]
        print(f"\nObject: {o.name}")
        print(f"  Vertex groups: {vgs}")

print("\n--- Armature bone hierarchy around arms ---")
for b in armature.data.bones:
    if 'arm' in b.name.lower() or 'collar' in b.name.lower() or 'pad' in b.name.lower() or 'cap' in b.name.lower():
        pname = b.parent.name if b.parent else "None"
        print(f"Bone: {b.name:25s} Head={b.head_local} Parent={pname}")
