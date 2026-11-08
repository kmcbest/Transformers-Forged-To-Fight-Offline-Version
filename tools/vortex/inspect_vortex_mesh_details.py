import bpy
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh_names = [
    "RB_Vortex_CHARSKEL_ArmLoL.mo.dmx",
    "RB_Vortex_CHARSKEL_ArmLoR.mo.dmx",
    "RB_Vortex_CHARSKEL_Head.mo.dmx",
    "VH_Vortex_SKEL.001.dmx",
    "WEP_IonBlade_SKEL.mo_L.dmx",
    "WEP_IonBlade_SKEL.mo_R.dmx"
]

print("--- Vortex Meshes Details ---")
for name in mesh_names:
    obj = bpy.data.objects.get(name)
    if not obj:
        print(f"Mesh {name} NOT FOUND!")
        continue
    
    verts = len(obj.data.vertices)
    faces = len(obj.data.polygons)
    vgs = [vg.name for vg in obj.vertex_groups]
    mats = [m.name for m in obj.data.materials if m]
    bbox = [list(c) for c in obj.bound_box]
    min_z = min(c[2] for c in bbox)
    max_z = max(c[2] for c in bbox)
    height = max_z - min_z
    
    print(f"Object: {name}")
    print(f"  Verts: {verts}, Polygons: {faces}")
    print(f"  Materials ({len(mats)}): {mats}")
    print(f"  Vertex Groups count: {len(vgs)}")
    print(f"  Sample VGs: {vgs[:8]}")
    print(f"  Local Bounding Box Z: min={min_z:.2f}, max={max_z:.2f}, height={height:.2f}")
    print(f"  World Location: ({obj.location.x:.2f}, {obj.location.y:.2f}, {obj.location.z:.2f})")
    print(f"  Parent: {obj.parent.name if obj.parent else 'None'}")
    print(f"  Armature modifier: {[m.object.name for m in obj.modifiers if m.type == 'ARMATURE' and m.object]}")
    print("-" * 50)
