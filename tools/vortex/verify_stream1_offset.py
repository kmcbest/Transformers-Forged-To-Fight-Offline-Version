import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
import UnityPy
import numpy as np

raw_head = subprocess.check_output(["git", "show", "HEAD:assets_redeco/vortex_gs.assetbundle"], cwd=r"e:\Agent\TFTF-blender")
env_h = UnityPy.load(raw_head)
for o in env_h.objects:
    if o.path_id == -2766188856892899435:
        m = o.read()
        tt = o.read_typetree()
        vd = tt["m_VertexData"]
        vc = vd["m_VertexCount"]
        raw = bytes(vd["m_DataSize"])
        s1_off = (vc * 40 + 15) & ~15
        s2_off = s1_off + ((vc * 8 + 15) & ~15)
        print(f"vc={vc}, s1_off={s1_off}, s2_off={s2_off}, total_with_s2={s2_off + vc*32}, actual={len(raw)}")
        pos = np.ndarray((vc, 3), dtype=np.float32, buffer=raw, strides=(40, 4), offset=0)
        uv  = np.ndarray((vc, 2), dtype=np.float32, buffer=raw, strides=(8, 4),  offset=s1_off)
        ib  = np.frombuffer(bytes(m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)

        print("\nWith s1_off =", s1_off, "Emblem Tris 59..62 UVs:")
        for ti in [59, 60, 61, 62]:
            for vi in ib[ti]:
                print(f"  Tri {ti} v{vi}: pos={pos[vi].round(3)}, uv={uv[vi].round(4)}")
        print("\nWith s1_off =", s1_off, "First 5 tris UVs (no leading [0,0]!):")
        for ti in range(5):
            print(f"  Tri {ti}: pos_mean={pos[ib[ti]].mean(axis=0).round(2)}, uvs={uv[ib[ti]].round(3).tolist()}")
