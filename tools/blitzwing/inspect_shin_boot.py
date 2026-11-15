import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

blend_path = r'E:\Agent\TFTF-blender\3rd-party-models\blitzwing_extracted\rar\Blitzwing.blend'
bpy.ops.wm.open_mainfile(filepath=blend_path)
mesh = bpy.data.objects['Blitzwing']

min_z = min(v.co.z for v in mesh.data.vertices)
SCALE = 1.4803

# Check submesh 1 (Legs material) vs others
# In Blender, polygons have material_index
# Material 0: Hands, 1: Legs, 2: Body
leg_verts = set()
for poly in mesh.data.polygons:
    if poly.material_index == 1: # Legs
        for vi in poly.vertices:
            leg_verts.add(vi)

leg_zs = [(mesh.data.vertices[vi].co.z - min_z) * SCALE for vi in leg_verts]
print(f"Legs material verts: {len(leg_verts)}")
print(f"Legs material scaled Z: min={min(leg_zs):.3f}, max={max(leg_zs):.3f}")

# Check vertices in bip_toe_L vs bip_foot_L vs bip_knee_L
for vg_name in ['bip_knee_L', 'bip_foot_L', 'bip_toe_L']:
    vg = mesh.vertex_groups.get(vg_name)
    if vg:
        vs = [vi for vi in leg_verts if any(g.group == vg.index and g.weight > 0.1 for g in mesh.data.vertices[vi].groups)]
        zs = [(mesh.data.vertices[vi].co.z - min_z) * SCALE for vi in vs]
        ys = [mesh.data.vertices[vi].co.y for vi in vs]
        print(f"{vg_name:12s}: {len(vs)} verts, Z=[{min(zs):.3f}, {max(zs):.3f}], Y=[{min(ys):.3f}, {max(ys):.3f}]")
