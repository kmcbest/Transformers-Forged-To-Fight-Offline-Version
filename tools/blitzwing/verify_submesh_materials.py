import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Check raw blitzwing_robot.fbx submesh materials in Unity via script
from pathlib import Path
import re

# Read blitzwing_robot.fbx.meta or check Unity asset database
# Actually in blitzwing_robot.fbx:
# In cha_blitzwing_gs_00.asset lines 12-41:
# Submesh 0: indexCount=6996 (which is 6996/3 = 2332 triangles = Slot 2: Hands!)
# Submesh 1: indexCount=13524 (which is 13524/3 = 4508 triangles = Slot 1: Legs!)
# Submesh 2: indexCount=21672 (which is 21672/3 = 7224 triangles = Slot 0: Body!)

print(f"SubMesh 0 triangles: 6996 / 3 = {6996//3} -> corresponds to Hands (2332 tris)!")
print(f"SubMesh 1 triangles: 13524 / 3 = {13524//3} -> corresponds to Legs (4508 tris)!")
print(f"SubMesh 2 triangles: 21672 / 3 = {21672//3} -> corresponds to Body (7224 tris)!")
