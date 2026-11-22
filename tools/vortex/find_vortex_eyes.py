import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np

env = UnityPy.load('assets_redeco/vortex_gs.assetbundle')
for obj in env.objects:
    if obj.path_id == 5703189533076905359: # cha_grindor_cin_rotf_00
        m = obj.read()
        vd = m.m_VertexData
        vc = vd.m_VertexCount
        raw = vd.m_DataSize
        pos = np.ndarray((vc, 3), dtype=np.float32, buffer=raw[:vc*40], strides=(40, 4), offset=0)
        uv = np.ndarray((vc, 2), dtype=np.float32, buffer=raw[vc*40:vc*48], strides=(8, 4), offset=0)
        ib = np.frombuffer(bytes(m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)
        
        diff = None
        raoe = None
        for o in env.objects:
            if o.path_id == -527106191474585865: # cha_grindor_cin_rotf_main_a
                diff = np.array(o.read().image.convert("RGBA"))
            if o.path_id == -2574972184015167263: # main_tform_misc_RAOE
                raoe = np.array(o.read().image.convert("RGB"))
                
        h, w = diff.shape[:2]
        tri_uvs = uv[ib].mean(axis=1)
        tri_pos = pos[ib].mean(axis=1)
        
        px = np.clip((tri_uvs[:, 0] * w).astype(int), 0, w - 1)
        py = np.clip(((1.0 - tri_uvs[:, 1]) * h).astype(int), 0, h - 1)
        sampled_diff = diff[py, px, :3]
        sampled_raoe = raoe[py, px, 2]
        
        print("Vortex robot pos bounds:", pos.min(axis=0), pos.max(axis=0))
        # Head is top Y
        head_mask = (tri_pos[:, 1] > 9.5)
        print(f"Total head triangles (Y > 9.5): {head_mask.sum()}")
        
        # Check glowing triangles on head
        glowing_head = np.where(head_mask & (sampled_raoe > 50))[0]
        print(f"Glowing head triangles (RAOE.B > 50): {len(glowing_head)}")
        for idx in glowing_head:
            tp = tri_pos[idx]
            tu = tri_uvs[idx]
            rgb = sampled_diff[idx]
            em = sampled_raoe[idx]
            print(f"  Vortex Head Glow Tri {idx}: Pos=({tp[0]:.2f}, {tp[1]:.2f}, {tp[2]:.2f}), UV=({tu[0]:.3f}, {tu[1]:.3f}), RGB={rgb}, RAOE.B={em}")
