import sys
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
MEG_JSON = ROOT / "tools" / "blitzwing" / "megatron_51_authoritative_bindposes.json"
data = json.loads(MEG_JSON.read_text(encoding="utf-8"))

head = data["bones"]["Head"]["unity_world_pos"]
pelvis = data["bones"]["Hips"]["unity_world_pos"]
lfoot = data["bones"]["LeftFoot"]["unity_world_pos"]
ltoe = data["bones"]["LeftToeBase"]["unity_world_pos"]

print(f"Megatron Unity World Pos:")
print(f"  Head:     {head}")
print(f"  Hips:     {pelvis}")
print(f"  LeftFoot: {lfoot}")
print(f"  LeftToe:  {ltoe}")

# Unity (ux, uy, uz) -> Blender (-ux, -uz, uy)
# In Blender Z is Up, so Unity uy corresponds to Blender Z!
print(f"Megatron Blender Z (Height):")
print(f"  Head Z:     {head[1]:.3f}m")
print(f"  Hips Z:     {pelvis[1]:.3f}m")
print(f"  LeftFoot Z: {lfoot[1]:.3f}m")
print(f"  LeftToe Z:  {ltoe[1]:.3f}m")
