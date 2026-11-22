import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, r"E:\Agent\TFTF-blender")
import json
from pathlib import Path

sum_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\BlastOff\00_donor_reference\donor_summary.json")
data = json.loads(sum_path.read_text(encoding="utf-8"))
mesh_00 = data["meshes"]["cha_megatronus_gs_kabam_00"]
avatar_tos = data["avatars"]["cha_megatronus_gs_kabam_00Avatar"]["tos"]
import numpy as np

for idx, (h, bp) in enumerate(zip(mesh_00["boneHashes"], mesh_00["bindposes"])):
    bname = avatar_tos.get(str(h), f"bone_{idx}").split("/")[-1]
    mat = np.array([
        [bp["e00"], bp["e01"], bp["e02"], bp["e03"]],
        [bp["e10"], bp["e11"], bp["e12"], bp["e13"]],
        [bp["e20"], bp["e21"], bp["e22"], bp["e23"]],
        [bp["e30"], bp["e31"], bp["e32"], bp["e33"]],
    ])
    inv_bp = np.linalg.inv(mat)
    u_pos = inv_bp[:3, 3] # Unity coords (X=Right, Y=Up, Z=Fwd)
    b_pos = (-u_pos[0], -u_pos[2], u_pos[1]) # Blender coords (X=Left, Y=Back, Z=Up)
    if any(k in bname.lower() for k in ("hip", "spine", "foot", "toe", "leg", "head")):
        print(f"{bname:20s}: Unity Y(Up)={u_pos[1]:.3f} | Blender Z(Up)={b_pos[2]:.3f}")

