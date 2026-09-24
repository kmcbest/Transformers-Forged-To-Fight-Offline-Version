# -*- coding: utf-8 -*-
import sys
import numpy as np
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

env_iron = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')
for obj in env_iron.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_ironhide_cin_rotf_00':
            # Extract vertices
            mesh_data = obj.read()
            # print vertices from mesh_data
            verts = mesh_data.m_Vertices
            print(f"Ironhide vertices count: {len(verts)}")
            xs = [v.x for v in verts]
            ys = [v.y for v in verts]
            zs = [v.z for v in verts]
            print(f"Ironhide X range: [{min(xs):.2f}, {max(xs):.2f}] (width: {max(xs)-min(xs):.2f})")
            print(f"Ironhide Y range: [{min(ys):.2f}, {max(ys):.2f}] (height: {max(ys)-min(ys):.2f})")
            print(f"Ironhide Z range: [{min(zs):.2f}, {max(zs):.2f}] (depth: {max(zs)-min(zs):.2f})")
            break
