import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\assets_netflix\character_anim_procedural.assetbundle"
env = UnityPy.load(bundle_path)
obj_map = {o.path_id: o for o in env.objects}

override_pids = [8156662034948264509, 3658090888164254241, 1661097116018184003, -131870695485524161, -8977399132283187477, 6003597289559234958, 2235498278053343569, 7862591952412139551, -3119635653397265966, 7218399588967537672, -4633680087473212482, -2236987077198429143]

for pid in override_pids:
    clip = obj_map.get(pid)
    if clip:
        d = clip.read()
        print(f"PathID={pid}: {getattr(d, 'm_Name', '')} duration={getattr(d, 'm_StopTime', 0):.2f}s")
