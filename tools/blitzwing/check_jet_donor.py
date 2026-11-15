import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy, struct

p_wb = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\windblade_gs_odr\windblade_gs.assetbundle")
if p_wb.exists():
    env = UnityPy.load(str(p_wb))
    for o in env.objects:
        if o.type.name == "Mesh":
            tt = o.read_typetree()
            if "01" in tt["m_Name"] or "jet" in tt["m_Name"].lower() or "trans" in tt["m_Name"].lower():
                print(f"Windblade vehicle mesh: {tt['m_Name']}")
                vd = tt["m_VertexData"]
                data = bytes(vd["m_DataSize"])
                vcount = vd["m_VertexCount"]
                stride = 40
                xs, ys, zs = [], [], []
                for i in range(vcount):
                    x, y, z = struct.unpack_from("<fff", data, i * stride)
                    xs.append(x); ys.append(y); zs.append(z)
                print(f"  X: [{min(xs):.3f}, {max(xs):.3f}]")
                print(f"  Y: [{min(ys):.3f}, {max(ys):.3f}]")
                print(f"  Z: [{min(zs):.3f}, {max(zs):.3f}]")
                print(f"  bones: {len(tt.get('m_BoneNameHashes', []))}")
