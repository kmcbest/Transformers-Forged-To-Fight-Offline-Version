import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
import UnityPy
import numpy as np

# 1. Inspect vortex_mesh.assetbundle!
vm_path = r"e:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\vortex_mesh.assetbundle"
env_vm = UnityPy.load(vm_path)
for o in env_vm.objects:
    if o.type.name == "Mesh":
        m = o.read()
        tt = o.read_typetree()
        print(f"vortex_mesh.assetbundle Mesh '{m.m_Name}': vc={m.m_VertexData.m_VertexCount}, tris={len(bytes(m.m_IndexBuffer))//6}, submeshes={len(tt['m_SubMeshes'])}")
        for i, ch in enumerate(tt["m_VertexData"]["m_Channels"]):
            if ch["dimension"] > 0:
                print(f"  ch[{i}]: {ch}")

# 2. Inspect HEAD vortex_gs.assetbundle Mesh cha_grindor_cin_rotf_01 vertex buffer size & channels!
raw_head = subprocess.check_output(["git", "show", "HEAD:assets_redeco/vortex_gs.assetbundle"], cwd=r"e:\Agent\TFTF-blender")
env_h = UnityPy.load(raw_head)
for o in env_h.objects:
    if o.path_id == -2766188856892899435:
        m = o.read()
        tt = o.read_typetree()
        vd = tt["m_VertexData"]
        vc = vd["m_VertexCount"]
        raw = bytes(vd["m_DataSize"])
        print(f"\nHEAD cha_grindor_cin_rotf_01: vc={vc}, len(m_DataSize)={len(raw)}, expected 40+8+32={vc*80}, 40+8+0={vc*48}")
        for i, ch in enumerate(vd["m_Channels"]):
            if ch["dimension"] > 0:
                print(f"  ch[{i}]: {ch}")
        # Print first 5 verts UV from raw at vc*40 vs check if raw has 16-byte alignment padding!
        pos = np.ndarray((vc, 3), dtype=np.float32, buffer=raw, strides=(40, 4), offset=0)
        uv = np.ndarray((vc, 2), dtype=np.float32, buffer=raw, strides=(8, 4), offset=vc*40)
        ib = np.frombuffer(bytes(m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)
        print("HEAD first 10 tris pos_mean & uv:")
        for i in range(10):
            print(f"  Tri {i}: pos_mean={pos[ib[i]].mean(axis=0).round(2)}, uvs={uv[ib[i]].round(3).tolist()}")
