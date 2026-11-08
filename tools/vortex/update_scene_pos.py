import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

scene_file = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Scenes\Vortex_Inspection.unity"
with open(scene_file, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace Transform 553386621 (Grindor) m_LocalPosition: {x: 4, y: 0, z: 0} -> {x: 3.3, y: 0, z: 0}
# Replace Transform 980312485 (Vortex) m_LocalPosition: {x: -4, y: 0, z: 0} -> {x: -3.3, y: 0, z: 0}

# Specifically target the transform blocks
import re

def repl_grindor(match):
    block = match.group(0)
    return block.replace('m_LocalPosition: {x: 4, y: 0, z: 0}', 'm_LocalPosition: {x: 3.3, y: 0, z: 0}')

text_new = re.sub(r'--- !u!4 &553386621\nTransform:.*?(?=--- !u!)', repl_grindor, text, flags=re.DOTALL)

def repl_vtx(match):
    block = match.group(0)
    return block.replace('m_LocalPosition: {x: -4, y: 0, z: 0}', 'm_LocalPosition: {x: -3.3, y: 0, z: 0}')

text_new = re.sub(r'--- !u!4 &980312485\nTransform:.*?(?=--- !u!)', repl_vtx, text_new, flags=re.DOTALL)

if text != text_new:
    with open(scene_file, 'w', encoding='utf-8') as f:
        f.write(text_new)
    print("Successfully updated scene root positions to +/-3.3!")
else:
    print("No change made.")
