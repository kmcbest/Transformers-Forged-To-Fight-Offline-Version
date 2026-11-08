import bpy
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROBOT_BLEND = r"E:\Agent\TFTF-blender\3rd-party-models\vortex\robot\vortex_robot.blend"
bpy.ops.wm.open_mainfile(filepath=ROBOT_BLEND)

for obj in bpy.data.objects:
    if obj.type != 'MESH': continue
    print(f"\nObject: {obj.name}")
    uv_layer = obj.data.uv_layers.active
    if not uv_layer: continue
    
    mat_uvs = {}
    for poly in obj.data.polygons:
        midx = poly.material_index
        mname = obj.data.materials[midx].name if midx < len(obj.data.materials) else "None"
        if mname not in mat_uvs:
            mat_uvs[mname] = []
        for loop_idx in poly.loop_indices:
            mat_uvs[mname].append(uv_layer.data[loop_idx].uv)
            
    for mname, uvs in mat_uvs.items():
        min_u = min(u[0] for u in uvs)
        max_u = max(u[0] for u in uvs)
        min_v = min(u[1] for u in uvs)
        max_v = max(u[1] for u in uvs)
        print(f"  Material {mname:30s} (polys={len(uvs)//3}): U=[{min_u:.3f}, {max_u:.3f}], V=[{min_v:.3f}, {max_v:.3f}]")
