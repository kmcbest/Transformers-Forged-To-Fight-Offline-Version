import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import os

pipeline_path = r"e:\Agent\TFTF-blender\re_notes\THIRD_PARTY_3D_MODEL_PIPELINE.md"

sec11_18 = """

### 11.18 飞标（Swoop）与飞行动物/鸟兽模具：Blender FBX 非单位 BindPose 缩放剥离大爆炸破局、原生 58 帧拍翅循环解构与胸口翼龙嘴火球重击
* **详见独立专题工程指南**：[`re_notes/BIRD_BEAST_TRANSFORMATION_PIPELINE.md`](file:///e:/Agent/TFTF-blender/re_notes/BIRD_BEAST_TRANSFORMATION_PIPELINE.md)
* **适用模具**：飞标（Swoop，`swoop_gs_deluxe2008`，科技系 `tech`）等借用喷气机/空军骨架的鸟形、飞龙形野兽金刚。
* **三大核心攻坚复盘与沉淀**：
  1. **Blender FBX 导入剥离 `Lcl Scaling != 1.0` 触发断头断喙大爆炸根治（FK 绝对矩阵重算）**：
     * 3ds Max 制作的模型常在 `bird_neck` (0.3366)、`bird_Head` (0.6236)、`beak` (0.4659) 等骨骼带有非单位缩放；
     * Blender `io_scene_fbx` 会将 EditBone 缩放强制置 1，但在应用动画或读取骨骼姿态时导致 BindMatrix 与局部变换脱节，子部件（如鸟嘴、长颈、翅膀）沿轴向飞脱数米之外；
     * **根本解法**：在 `tools/swoop/build_aligned_swoop_vh.py` 中直接解析 FBX 文本的 `Properties70["Lcl Scaling"]`，在纯 Python 中按正向运动学递归重算 $\\mathbf{W}_{\\text{rest}}$ 与 $\\mathbf{W}_{\\text{pose}}$，并进行局部线性混合蒙皮（LBS）顶点烘焙，彻底杜绝几何撕脱断裂，误差 $< 0.0001\\text{mm}$。
  2. **翼龙原生 58 帧拍翅循环（`vehicle_idle01`）解构与喷气机 10 骨平滑映射**：
     * 将源模型自带的 58 帧双周波扑翼（内翼 $22.4^\\circ$、外翼 $34.3^\\circ$、下喙 $3.8^\\circ$、爪子 $13.9^\\circ$）精准映射到 Ramjet 喷气机的 10 根主要骨骼；
     * 翼膜连接处采用 50/50 线性渐变权重，消除折叠锐角；
     * 通过 Unity `BuildSwoopWingFlapClip()` 烘焙为标准 `AnimationClip` 注入 Car AOC，使载具悬停飞行充满生物扑翼生机感。
  3. **胸口翼龙嘴吐火重击（借用钢锁 `projectile_grimlock_fireball`）与跨包克隆序列化安全矩阵**：
     * 在飞标胸口上喙与下喙交汇处（Beak Tip）设立发射定位器 `joint_Torso/loc_mouth_flame`，在 `moves.assetbundle` 中将重击发射节点与事件重定向；
     * 跨包克隆 Prefab 严格遵循 `ORIGINAL_CHARACTER_CREATION_GUIDE.md` 铁律：`script_types` 必须按 `(FileID, PathID)` 严格升序排列并同步回写所有 `script_type_index`，全量更新 `m_PreloadTable` 与 `m_Container` 切片，动作总数强制断言 $\\ge 945$。
"""

with open(pipeline_path, "r", encoding="utf-8") as f:
    content = f.read()

if "11.18 飞标（Swoop）" not in content:
    content += sec11_18
    with open(pipeline_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Successfully appended Section 11.18 to THIRD_PARTY_3D_MODEL_PIPELINE.md")
else:
    print("Section 11.18 already exists.")
