import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import UnityPy, struct

p_tex = Path(r"E:\Agent\TFTF-blender\tools\blitzwing\atlased_textures\cha_blitzwing_tform_misc_Diffuse.png")
if p_tex.exists():
    im = Image.open(p_tex)
    print("tform_misc_Diffuse size:", im.size, im.mode)

p_mesh = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blitzwing_mesh.assetbundle")
env = UnityPy.load(str(p_mesh))

for o in env.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        name = tt["m_Name"]
        if "tank" in name or "jet" in name or "01" in name or "02" in name:
            channels = tt["m_VertexData"]["m_Channels"]
            print(f"\nMesh {name}:")
            # find UV channel
            uv_ch = channels[4] # UV0
            print("  UV0 channel:", uv_ch)
            data = bytes(tt["m_VertexData"]["m_DataSize"])
            stride = 40
            offset = uv_ch["offset"]
            u_vals, v_vals = [], []
            for i in range(tt["m_VertexData"]["m_VertexCount"]):
                u, v = struct.unpack_from("<ff", data, i * stride + offset)
                u_vals.append(u); v_vals.append(v)
            print(f"  U range: [{min(u_vals):.4f}, {max(u_vals):.4f}]")
            print(f"  V range: [{min(v_vals):.4f}, {max(v_vals):.4f}]")
