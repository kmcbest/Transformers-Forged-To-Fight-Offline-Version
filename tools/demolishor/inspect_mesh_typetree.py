# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = "extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_ironhide_cin_rotf_00":
            print(f"Mesh: {tree.get('m_Name')}")
            print("  Top keys:", list(tree.keys()))
            v_data = tree.get("m_VertexData", {})
            print("  m_VertexData keys:", list(v_data.keys()))
            print("  m_VertexCount:", v_data.get("m_VertexCount"))
            print("  m_Channels:", len(v_data.get("m_Channels", [])))
            for idx, ch in enumerate(v_data.get("m_Channels", [])):
                if ch.get("dimension", 0) > 0:
                    print(f"    Channel {idx}: stream={ch.get('stream')}, offset={ch.get('offset')}, format={ch.get('format')}, dim={ch.get('dimension')}")
            break
