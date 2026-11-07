import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_paths = [
    Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ironhide_gs_kabam_odr\ironhide_gs_kabam.assetbundle"),
    Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\ironhide_cin_rotf_odr\ironhide_cin_rotf.assetbundle")
]

for bp in bundle_paths:
    print(f"\n=======================================================")
    print(f"Inspecting: {bp.name}")
    print(f"Exists: {bp.exists()}")
    if not bp.exists():
        continue
    
    env = UnityPy.load(str(bp))
    print(f"Total objects in env: {len(env.objects)}")
    
    # Collect GameObjects, SMRs, MeshRenderers, Meshes
    game_objects = {}
    smrs = []
    mrs = []
    anim_clips = []
    
    for obj in env.objects:
        if obj.type.name == "GameObject":
            data = obj.read()
            game_objects[obj.path_id] = getattr(data, 'm_Name', getattr(data, 'name', ''))
        elif obj.type.name == "SkinnedMeshRenderer":
            smrs.append(obj)
        elif obj.type.name == "MeshRenderer":
            mrs.append(obj)
        elif obj.type.name == "AnimationClip":
            data = obj.read()
            anim_clips.append(getattr(data, 'm_Name', getattr(data, 'name', '')))
            
    print(f"Total GameObjects: {len(game_objects)}")
    print(f"Total SkinnedMeshRenderers: {len(smrs)}")
    print(f"Total MeshRenderers: {len(mrs)}")
    print(f"AnimationClips ({len(anim_clips)}): {anim_clips[:10]}")
    
    print("\n--- SMRs ---")
    for smr_obj in smrs:
        data = smr_obj.read()
        go_name = game_objects.get(data.m_GameObject.path_id, f"PID_{data.m_GameObject.path_id}")
        mesh_data = data.m_Mesh.read() if data.m_Mesh else None
        mesh_name = getattr(mesh_data, 'm_Name', getattr(mesh_data, 'name', 'None')) if mesh_data else "None"
        bones_count = len(data.m_Bones)
        print(f"SMR on GO: '{go_name}' | Mesh: '{mesh_name}' | Bones: {bones_count}")
        
    print("\n--- MeshRenderers ---")
    for mr_obj in mrs:
        data = mr_obj.read()
        go_name = game_objects.get(data.m_GameObject.path_id, f"PID_{data.m_GameObject.path_id}")
        print(f"MeshRenderer on GO: '{go_name}'")
        
    # Check for weapon-related GameObjects
    print("\n--- Weapon / Prop GameObjects ---")
    for pid, name in game_objects.items():
        n_low = name.lower()
        if any(w in n_low for w in ["wpn", "weapon", "gun", "cannon", "blaster", "pistol", "rifle"]):
            print(f"  GO [{pid}]: {name}")
