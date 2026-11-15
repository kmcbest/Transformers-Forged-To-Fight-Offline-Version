import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

blend_path = r'E:\Agent\TFTF-blender\3rd-party-models\blitzwing_extracted\rar\Blitzwing.blend'
bpy.ops.wm.open_mainfile(filepath=blend_path)

bw = bpy.data.objects['Blitzwing']
head_vg = bw.vertex_groups.get('bip_head')
if head_vg:
    head_v_indices = {v.index for v in bw.data.vertices if any(g.group == head_vg.index and g.weight > 0.5 for g in v.groups)}
    print(f"Found {len(head_v_indices)} vertices in bip_head")
    uv_layer = bw.data.uv_layers.active
    head_uvs = []
    for poly in bw.data.polygons:
        for li in poly.loop_indices:
            vi = bw.data.loops[li].vertex_index
            if vi in head_v_indices:
                u, v = uv_layer.data[li].uv
                head_uvs.append((u, v))
    if head_uvs:
        u_vals = [uv[0] for uv in head_uvs]
        v_vals = [uv[1] for uv in head_uvs]
        print(f"Head UV Range:")
        print(f"U: [{min(u_vals):.4f}, {max(u_vals):.4f}]")
        print(f"V: [{min(v_vals):.4f}, {max(v_vals):.4f}]")
