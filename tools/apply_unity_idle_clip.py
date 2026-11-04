import sys
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from generate_lifeline_assets import inject_dual_sword_grip_into_clip

FINGER_POSE_JSON = Path("unity_lifeline/Assets/AssetBundles/lifeline_finger_pose.json")
SWORD_OFFSETS_JSON = Path("unity_lifeline/Assets/AssetBundles/sword_offsets.json")
TARGET_BUNDLE = Path("assets_redeco/lifeline_gs_deluxe2014.assetbundle")


def apply_unity_finger_pose() -> bool:
    if not FINGER_POSE_JSON.exists():
        print(f"[-] 未找到 Unity 导出的手指肌肉文件: {FINGER_POSE_JSON}")
        print("    请先在 Unity 中点击菜单【Lifeline 调手型工具 -> 2. 导出双手手指肌肉值 (attr 97..136)】！")
        return False

    with open(FINGER_POSE_JSON, "r", encoding="utf-8", errors="replace") as f:
        raw_map = json.load(f)

    # 严格门禁：仅允许修改编译后 Humanoid 手指通道 attr 97..136 (42 + muscle_index 55..94)
    finger_map = {}
    for k, v in raw_map.items():
        attr = int(k)
        if not (97 <= attr <= 136):
            raise ValueError(f"[SECURITY GATE] 非法通道 attr={attr}！严禁修改 97..136 以外的身体/四肢通道！")
        finger_map[attr] = float(v)

    if len(finger_map) != 40:
        raise ValueError(f"[SECURITY GATE] 期望 40 个手指通道 (97..136)，实际读取到 {len(finger_map)} 个！")

    print(f"[+] 成功加载并通过门禁校验: 40 个手指肌肉通道 (attr 97..136)")

    offsets = {}
    if SWORD_OFFSETS_JSON.exists():
        try:
            with open(SWORD_OFFSETS_JSON, "r", encoding="utf-8", errors="replace") as f:
                offsets = json.load(f)
            print(f"[+] 加载双刀位置微调参数: {offsets}")
        except Exception as e:
            print(f"[!] 读取 sword_offsets.json 失败: {e}")

    print(f"[+] 加载目标回春手 AssetBundle: {TARGET_BUNDLE}...")
    target_env = UnityPy.load(str(TARGET_BUNDLE))

    clips_patched = 0
    for obj in target_env.objects:
        if obj.path_id in [807675994726628539, 7081150187961391002] and obj.type.name == "AnimationClip":
            tree = obj.read_typetree()
            cname = tree.get("m_Name")
            mod_count = inject_dual_sword_grip_into_clip(tree, finger_map)
            obj.save_typetree(tree)
            clips_patched += 1
            print(f"[+] 微创注入 {cname} (PathID={obj.path_id}): 仅更新 {mod_count} 个手指通道 (attr 97..136)，身体/呼吸曲线 100% 保持原样")

    if clips_patched == 0:
        print("[-] 未能在目标 Bundle 中找到待机动画！")
        return False

    if offsets:
        props_updated = 0
        for obj in target_env.objects:
            if obj.path_id in [-8672360083464370100, -468543671400758953] and obj.type.name == "MonoBehaviour":
                tree = obj.read_typetree()
                props = tree.get("_props", {})
                keys = props.get("_serializedKeys", [])
                vals = props.get("_serializedValues", [])
                for k_idx, k_name in enumerate(keys):
                    if k_name in offsets:
                        off = offsets[k_name]
                        p = off.get("pos", [0.0, 0.0, 0.0])
                        r = off.get("rot", [0.0, 0.0, 0.0])
                        vals[k_idx]["PositionOffset"] = {"x": float(p[0]), "y": float(p[1]), "z": float(p[2])}
                        vals[k_idx]["RotationOffset"] = {"x": float(r[0]), "y": float(r[1]), "z": float(r[2])}
                        print(f"    [PropsController {obj.path_id}] 更新 '{k_name}' -> pos={p}, rot={r}")
                props["_serializedValues"] = vals
                tree["_props"] = props
                obj.save_typetree(tree)
                props_updated += 1
        print(f"[+] 已同步更新 {props_updated} 个 PropsController 中的双刀偏移")

    out_data = target_env.file.save(packer="lz4")
    TARGET_BUNDLE.write_bytes(out_data)
    print(f"[SUCCESS] 已使用 LZ4 压缩保存 {TARGET_BUNDLE} ({len(out_data)} bytes)！")
    return True


if __name__ == "__main__":
    apply_unity_finger_pose()
