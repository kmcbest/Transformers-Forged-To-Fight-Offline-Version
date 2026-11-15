import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import re
from pathlib import Path

scene_path = r'E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Scenes\Blitzwing_Inspection.unity'
txt = Path(scene_path).read_text(encoding='utf-8')

match = re.search(r'&535011246\s+SkinnedMeshRenderer:.*?(m_Bones:.*?)(?:\n  m_|\Z)', txt, re.DOTALL)
if match:
    bones_block = match.group(1)
    file_ids = re.findall(r'fileID:\s*(\d+)', bones_block)
    print(f"Total bones in SMR 535011246: {len(file_ids)}")
    
    # Map transform fileID to GameObject fileID
    tr_to_go = {}
    for m in re.finditer(r'--- !u!4 &(\d+)\s+Transform:.*?m_GameObject:\s*\{fileID:\s*(\d+)\}', txt, re.DOTALL):
        tr_to_go[m.group(1)] = m.group(2)
        
    go_to_name = {}
    for m in re.finditer(r'--- !u!1 &(\d+)\s+GameObject:.*?m_Name:\s*([^\r\n]+)', txt, re.DOTALL):
        go_to_name[m.group(1)] = m.group(2)
        
    for i, fid in enumerate(file_ids):
        goid = tr_to_go.get(fid)
        bname = go_to_name.get(goid, "Unknown")
        print(f"  [{i:02d}] Transform {fid} -> {bname}")
