import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

blend_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_aligned_mesh\sideswipe_robot_aligned.blend")
bpy.ops.wm.open_mainfile(filepath=str(blend_path))

mesh_obj = next(o for o in bpy.data.objects if o.type == "MESH")
mesh = mesh_obj.data
uv_layer = mesh.uv_layers.active.data

raoe_img = bpy.data.images.load(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\02_textures\cha_sideswipe_main_RAOE.png")
diff_img = bpy.data.images.load(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\02_textures\cha_sideswipe_main_Diffuse.png")

w, h = raoe_img.size
raoe_pixels = list(raoe_img.pixels) # RGBA floats 0..1
diff_pixels = list(diff_img.pixels) # RGBA floats 0..1

def sample_px(pixels, w, h, u, v):
    x = int(max(0, min(w - 1, u * w)))
    y = int(max(0, min(h - 1, v * h)))
    idx = (y * w + x) * 4
    return pixels[idx], pixels[idx+1], pixels[idx+2], pixels[idx+3], x, y

emissive_polys = []
for p in mesh.polygons:
    p_uvs = [uv_layer[li].uv for li in p.loop_indices]
    u_mean = sum(uv[0] for uv in p_uvs) / len(p_uvs)
    v_mean = sum(uv[1] for uv in p_uvs) / len(p_uvs)
    
    r_r, r_g, r_b, r_a, px, py = sample_px(raoe_pixels, w, h, u_mean, v_mean)
    d_r, d_g, d_b, d_a, _, _ = sample_px(diff_pixels, w, h, u_mean, v_mean)
    
    if r_b > 0.2: # Emissive > ~50/255
        p_xs = [mesh.vertices[vi].co.x for vi in p.vertices]
        p_ys = [mesh.vertices[vi].co.y for vi in p.vertices]
        p_zs = [mesh.vertices[vi].co.z for vi in p.vertices]
        emissive_polys.append((
            sum(p_xs)/len(p_xs), sum(p_ys)/len(p_ys), sum(p_zs)/len(p_zs),
            px, py, int(r_b*255),
            (int(d_r*255), int(d_g*255), int(d_b*255)),
            p.index, u_mean, v_mean
        ))

print(f"Total polygons sampling emissive pixels (> 50): {len(emissive_polys)}")
for p in emissive_polys:
    print(f"  poly {p[7]}: 3D=({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f}), UV=({p[8]:.3f}, {p[9]:.3f}), Pixel=({p[3]}, {p[4]}), E={p[5]}, Diffuse RGB={p[6]}")
