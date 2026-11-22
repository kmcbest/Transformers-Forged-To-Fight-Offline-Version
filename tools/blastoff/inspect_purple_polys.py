import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

SRC = r"O:\agent\transformers-fall-of-cybertron-combaticons\textures"
head_diff = bpy.data.images.load(f"{SRC}/rb_blastoff_head_cust_matinst.jpg")
w, h = head_diff.size
pixels = list(head_diff.pixels)

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\BlastOff\03_fbx_exports\blastoff_robot_prepared.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh_obj = next(o for o in bpy.data.objects if o.type == "MESH")
uv_layer = mesh_obj.data.uv_layers.active.data

def get_pixel(x, y):
    idx = (y * w + x) * 4
    return pixels[idx], pixels[idx+1], pixels[idx+2]

purple_polys = []
for p in mesh_obj.data.polygons:
    p_vs = [mesh_obj.data.vertices[v_idx].co for v_idx in p.vertices]
    z_mean = sum(v.z for v in p_vs) / len(p_vs)
    if z_mean < 10.5:
        continue
    
    # Calculate poly UV center
    uvs = [uv_layer[li].uv for li in p.loop_indices]
    uc = sum(u.x for u in uvs) / len(uvs)
    vc = sum(u.y for u in uvs) / len(uvs)
    
    # Map back to tile (512x512)
    u_tile = (uc - 0.5) / 0.25
    v_tile = (vc - 0.75) / 0.25
    x_px = int(min(max(u_tile * w, 0), w - 1))
    # In Blender image pixels, Y=0 is bottom
    y_px = int(min(max(v_tile * h, 0), h - 1))
    
    r, g, b = get_pixel(x_px, y_px)
    # Check if purple: b > 0.45, b > g + 0.1, r > 0.25
    if b > r and b > g + 0.1:
        y_mean = sum(v.y for v in p_vs) / len(p_vs)
        x_mean = sum(v.x for v in p_vs) / len(p_vs)
        purple_polys.append((p, x_mean, y_mean, z_mean, x_px, y_px, (round(r, 2), round(g, 2), round(b, 2))))

print(f"Total purple polygons on head: {len(purple_polys)}")
for p, xm, ym, zm, xp, yp, col in purple_polys:
    print(f"  Poly at (x={xm:+.3f}, y={ym:+.3f}, z={zm:+.3f}): px=({xp}, {yp}), color={col}")
