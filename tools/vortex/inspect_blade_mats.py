import bpy
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

blade = bpy.data.objects.get("WEP_IonBlade_SKEL.mo_L.dmx")
if blade:
    mat_poly_counts = {}
    for p in blade.data.polygons:
        idx = p.material_index
        mname = blade.data.materials[idx].name if idx < len(blade.data.materials) else "None"
        mat_poly_counts[mname] = mat_poly_counts.get(mname, 0) + 1
    print("Blade polygon counts per material:")
    for m, c in mat_poly_counts.items():
        print(f"  {m:30s}: {c} polygons")
