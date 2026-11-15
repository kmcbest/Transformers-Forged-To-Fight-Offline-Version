import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy, struct

donor_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(donor_path))
obj_map = {o.path_id: o for o in env.objects}

mesh = obj_map[-6391917038499381755].read_typetree()
vd = mesh["m_VertexData"]
vcount = vd["m_VertexCount"]
data = bytes(vd["m_DataSize"])
print(f"Donor Cannon verts={vcount}, DataSize={len(data)}")
print("Skin weights info:")
print("  m_Skin:", mesh.get("m_Skin"))
print("  m_VariableBoneCountWeights:", mesh.get("m_VariableBoneCountWeights"))
