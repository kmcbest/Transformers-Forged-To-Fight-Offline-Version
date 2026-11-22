import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, r"E:\Agent\TFTF-blender")
import UnityPy
import numpy as np
from pathlib import Path
from tools.validate_port_gates import parse_unity_mesh_streams

mb_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blastoff_mesh.assetbundle")
env = UnityPy.load(str(mb_path))

for o in env.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        if tt["m_Name"] == "cha_blastoff_gs_00":
            pts, uvs, ws, bi = parse_unity_mesh_streams(tt)
            print(f"Mesh {tt['m_Name']}: {len(pts)} vertices")
            
            # Find vertices with high Y (head is at Y > 10.5m)
            head_idx = np.where(pts[:, 1] > 10.5)[0]
            print(f"Head vertices (Y > 10.5m): {len(head_idx)}")
            head_pts = pts[head_idx]
            head_uvs = uvs[head_idx]
            
            print(f"Head Y range: [{head_pts[:,1].min():.3f}, {head_pts[:,1].max():.3f}]")
            print(f"Head UV U range: [{head_uvs[:,0].min():.4f}, {head_uvs[:,0].max():.4f}]")
            print(f"Head UV V range: [{head_uvs[:,1].min():.4f}, {head_uvs[:,1].max():.4f}]")
            
            # In image space (U*2048, (1-V)*2048)
            img_x = head_uvs[:, 0] * 2048
            img_y = (1.0 - head_uvs[:, 1]) * 2048
            print(f"Head pixel X: [{img_x.min():.1f}, {img_x.max():.1f}], Y: [{img_y.min():.1f}, {img_y.max():.1f}]")
            
            # Eye level is at Y ~ 11.0 to 11.4, Z > 0.0 (front facing)
            eye_idx = np.where((pts[:, 1] > 11.0) & (pts[:, 1] < 11.4) & (pts[:, 2] > 0.1))[0]
            print(f"Eye candidate vertices: {len(eye_idx)}")
            if len(eye_idx) > 0:
                eye_uvs = uvs[eye_idx]
                e_x = eye_uvs[:, 0] * 2048
                e_y = (1.0 - eye_uvs[:, 1]) * 2048
                print(f"Eye pixel X: [{e_x.min():.1f}, {e_x.max():.1f}], Y: [{e_y.min():.1f}, {e_y.max():.1f}]")
