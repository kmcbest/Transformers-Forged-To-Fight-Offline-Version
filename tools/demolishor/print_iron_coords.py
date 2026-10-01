# -*- coding: utf-8 -*-
import json
import mathutils

with open('tools/demolishor/ironhide_80_bones.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

bones = ['LeftShoulder', 'LeftArm', 'LeftForeArm', 'LeftHand', 
         'RightShoulder', 'RightArm', 'RightForeArm', 'RightHand', 
         'LeftUpLeg', 'LeftLeg', 'LeftFoot', 
         'RightUpLeg', 'RightLeg', 'RightFoot']

print("=== Ironhide Armature Coordinates in Blender Space ===")
for name in bones:
    m = mathutils.Matrix(d['bones'][name]['matrix'])
    t = m.to_translation()
    # Unity (X, Y, Z) -> Blender (X, Z, Y)
    bx, by, bz = t.x, t.z, t.y
    print(f"{name:16s}: (X={bx:6.2f}, Y={by:6.2f}, Z={bz:6.2f})")
