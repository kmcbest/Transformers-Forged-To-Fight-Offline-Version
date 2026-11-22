import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, r"E:\Agent\TFTF-blender")
import json
from pathlib import Path
import numpy as np

DONOR_JSON = Path(r"E:\Agent\TFTF-blender\3rd-party-models\BlastOff\00_donor_reference\donor_summary.json")
donor = json.loads(DONOR_JSON.read_text(encoding="utf-8"))
mesh_00 = donor["meshes"]["cha_megatronus_gs_kabam_00"]
avatar_tos = donor["avatars"]["cha_megatronus_gs_kabam_00Avatar"]["tos"]

print("--- Megatronus Bone Positions (Unity coords: Y=Up, Z=Fwd, X=Right) ---")
for idx, (h, bp) in enumerate(zip(mesh_00["boneHashes"], mesh_00["bindposes"])):
    mat = np.array([
        [bp["e00"], bp["e01"], bp["e02"], bp["e03"]],
        [bp["e10"], bp["e11"], bp["e12"], bp["e13"]],
        [bp["e20"], bp["e21"], bp["e22"], bp["e23"]],
        [bp["e30"], bp["e31"], bp["e32"], bp["e33"]],
    ])
    inv = np.linalg.inv(mat)
    upos = inv[:3, 3]
    bname = avatar_tos.get(str(h), f"bone_{idx}").split("/")[-1]
    if any(k in bname.lower() for k in ("spine", "neck", "head", "hip", "clav", "shoulder")):
        print(f"  {bname:20s}: X={upos[0]:6.3f}, Y={upos[1]:6.3f}, Z={upos[2]:6.3f}")
