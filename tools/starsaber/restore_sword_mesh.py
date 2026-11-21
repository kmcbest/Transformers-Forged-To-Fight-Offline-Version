import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
import UnityPy
from pathlib import Path

MESH_BUNDLE = Path(r"E:\Agent\TFTF-blender\3rd-party-models\StarSaber\04_unity_bundles\starsaber_mesh.assetbundle")

# 1. Load git commit 6f315e6 version of starsaber_mesh.assetbundle
cmd = ["git", "show", "6f315e6:3rd-party-models/StarSaber/04_unity_bundles/starsaber_mesh.assetbundle"]
res = subprocess.run(cmd, cwd=r"E:\Agent\TFTF-blender", stdout=subprocess.PIPE, check=True)
env_git = UnityPy.load(res.stdout)

# Extract 00 mesh typetree from git
git_00_tt = None
for o in env_git.objects:
    if o.type.name == "Mesh" and "00" in o.read_typetree().get("m_Name", ""):
        git_00_tt = o.read_typetree()
        break
assert git_00_tt is not None, "Failed to find 00 mesh in git 6f315e6!"

# 2. Load current starsaber_mesh.assetbundle
env_cur = UnityPy.load(str(MESH_BUNDLE))
updated = False
for o in env_cur.objects:
    if o.type.name == "Mesh" and "00" in o.read_typetree().get("m_Name", ""):
        print(f"Replacing Mesh 00 in starsaber_mesh.assetbundle with git 6f315e6 version...")
        o.save_typetree(git_00_tt)
        updated = True
        break
assert updated, "Failed to find Mesh 00 in current starsaber_mesh.assetbundle!"

# 3. Save starsaber_mesh.assetbundle
with open(MESH_BUNDLE, "wb") as f:
    f.write(env_cur.file.save(packer="lz4"))
print(f"[✓] Saved restored starsaber_mesh.assetbundle ({MESH_BUNDLE.stat().st_size} bytes, packer='lz4')")
