# 《百炼为战》（TFTF）角色展厅待机动作与手部握姿（Idle & Grip Pose）定制指南

本指南总结了在《百炼为战》（Transformers: Forged to Fight）中为重涂与自制角色（如回春手 Lifeline）定制展示厅待机动画（Living Idle）与武器握持手型的完整技术规范，涵盖 **Python 二进制肌肉通道微创移植（跨角色借姿势 / 单手镜像到双手）** 与 **Unity 3D 可视化手调 + `HumanPoseHandler` 导出** 两条已验证走通的工程路径，并记录了历史排障中必须规避的两大底层死胡同。

---

## 一、 核心真值：编译后 Humanoid `AnimationClip` 的通道映射表（`+42` 偏移铁律）

Unity 引擎在将 Humanoid（人形骨骼，`typeID = 95`, `path = 0`）动画编译进 AssetBundle 的 `m_ClipBindingConstant.genericBindings` 时，**`attribute` 编号并不是直接从 `0` 开始对应 95 块人体肌肉（`HumanPose.muscles[0..94]`）**！

在 `genericBindings` 中，前 **42 个通道（`attribute = 0..41`）** 固定分配给 6 组 Root 与手脚 IK 目标（每组含 `T.x, T.y, T.z, Q.x, Q.y, Q.z, Q.w` 共 7 个浮点数，$6 \times 7 = 42$）。真正的 95 块人体肌肉从 **`attribute = 42`** 才开始（即 $\text{attribute} = 42 + \text{muscle\_index}$，范围 `42..136`）：

| 编译后 `attribute` 范围 | 对应 `HumanPose.muscles` 下标 | 真实控制部位 | 说明与修改禁忌 |
| :--- | :--- | :--- | :--- |
| **`0 .. 6`** | — | `MotionT.x..z`, `MotionQ.x..w` | 根运动位移与旋转（无 Root Motion 的待机动画通常不包含这 7 项） |
| **`7 .. 13`** | — | `RootT.x..z`, `RootQ.x..w` | 身体重心（Center of Mass）坐标与朝向，决定角色站立高度与重心起伏 |
| **`14 .. 27`** | — | `LeftFootT/Q` (`14..20`), `RightFootT/Q` (`21..27`) | 左右脚 IK 锁定目标，确保双脚稳固踩地不滑步 |
| **`28 .. 41`** | — | `LeftHandT/Q` (`28..34`), `RightHandT/Q` (`35..41`) | 左右手 IK 目标 |
| **`42 .. 62`** | **`0 .. 20`** | 脊椎、胸腔、上胸、颈部、头部、眼球、下巴 | 负责待机呼吸胸腔起伏与头部微动，**严禁在调手型时触碰** |
| **`63 .. 78`** | **`21 .. 36`** | 左大腿/小腿/脚踝/脚趾 (`63..70`)、右腿 (`71..78`) | 负责双腿站姿，**误改会导致角色深蹲、劈叉或踮脚** |
| **`79 .. 96`** | **`37 .. 54`** | 左肩/上臂/前臂/手腕 (`79..87`)、右臂 (`88..96`) | 负责双臂持武器的自然姿态与呼吸摆动，**误改会导致双臂高举或乱拧** |
| **`97 .. 116`** | **`55 .. 74`** | **左手 20 个手指关节**（拇指、食指、中指、无名指、小指） | **左手握持手型的唯一真值通道** |
| **`117 .. 136`** | **`75 .. 94`** | **右手 20 个手指关节**（拇指、食指、中指、无名指、小指） | **右手握持手型的唯一真值通道** |

### 手指通道内部顺序与正负号规范
每只手固定 20 个通道，按 **`Thumb`（拇指）、`Index`（食指）、`Middle`（中指）、`Ring`（无名指）、`Little`（小指）** 顺序排列，每根手指包含 4 个自由度（DOF）：
1. `1 Stretched`（近节指骨弯曲/伸展）
2. `Spread`（手指左右张合）
3. `2 Stretched`（中节指骨弯曲/伸展）
4. `3 Stretched`（远节指尖弯曲/伸展）

> [!IMPORTANT] 肌肉值正负号与左右手对称性铁律
> 1. **负数为握拳（Closed），正数为张开（Stretched）**：在 Unity Mecanim 肌肉空间中，`Stretched` 字面意思是“伸展张开”，因此手指紧握刀柄时，`1 Stretched` 与 `2 Stretched` 均为**负数**（通常在 `-0.56` ~ `-1.68` 之间）。
> 2. **左右手天然镜像对称，复制时无需取反**：Unity 的 `HumanTrait` 肌肉空间已在引擎底层完成了左右手镜像归一化——无论 `Stretched` 还是 `Spread`，**左手 `97..116` 与右手 `117..136` 的正负号和数值含义完全一致**。将单手握刀姿势（如风刃右手 `117..136`）复制到另一只手（左手 `97..116`）时，**直接 1:1 原样复制 20 个浮点数即可，严禁将 `Spread` 取反**！

---

## 二、 历史踩坑警示：必须规避的两大死胡同

### ❌ 死胡同 1：漏算 `+42` 偏移，误把 `attribute 55..94`（或 `46..94`）当成手指通道修改
- **错误做法**：以为 Unity 有 95 块肌肉（`0..94`），就直接去改 `genericBindings` 里 `attribute = 55..94` 的数值，甚至自己编造 `+0.50 ~ +0.85` 的正数写入。
- **灾难后果**：由于漏算了前 42 个 IK/Root 通道，`attribute 55..94` 实际上是 `muscle_index 13..52`（脖子、双腿 `63..78`、双臂 `79..94`）！修改它们会导致角色的腿和手臂发生各种离奇扭曲（劈叉、举手、胸前架刀），给人一种“每次修改都有变化”的错觉，而真正控制手指的 **`attribute 97..136` 从头到尾纹丝不动**，手指永远停留在原版张开状态。
- **同时注意**：Unity 并不会因为只改 `attr 97..136` 而触发任何所谓的“IK 逆向暴走”。手指关节位于运动学链最末端，且在待机动画（如 `TeamSelect_Female_idle` 和 `Prefight_Female_idle`）中，全部 40 个手指通道均独立存放在 `ConstantClip` 尾部（`b_idx = 90..129`，即 `c_data[15..54]`），与 `StreamedClip`（51 条）和 `DenseClip`（24 条）中的身体呼吸曲线完全解耦。

### ❌ 死胡同 2：在 Unity Editor 中将 `Animator.avatar = null` 并烘焙为 Generic `Transform` 曲线替换原动画
- **错误做法**：在 Unity Editor 中为了绕过 Humanoid 骨骼无法直接用 Animation 窗口 K 帧的限制，把 `instanceAnim.avatar = null` 清空，将动画烘焙成基于骨骼路径的 Generic `Transform.localRotation` / `localPosition` 曲线（`typeID = 4`），然后整包替换游戏 AssetBundle 中的 `AnimationClip`。
- **灾难后果**：
  1. 游戏内角色使用的是 **Humanoid `Animator`**，它只读取 `typeID = 95` 的肌肉通道，**100% 忽略手指与四肢上的 Generic `Transform.localRotation` 曲线**！
  2. 原版 `typeID = 95` 的肌肉数据被洗掉后，全身肌肉回退到 Avatar 默认的 **T-Pose / Bind Pose**（双臂僵直交叉成“十字刀”，手指恢复张开）。
  3. 无 Avatar 状态下烘焙出的 `Hips.localPosition`（如 `Y = -7.73`）会直接覆盖游戏内重心高度，导致角色“半截身子陷入地下”。

---

## 二、 标准方案一：纯 Python 跨角色借用握姿 / 单手镜像到双手（最快、零失真）

当游戏内已有现成持剑/持武器角色的待机动作（例如 `character_anim_procedural.assetbundle` 中的风刃持剑待机 `Frontend_Sword_idle`，其右手握剑，左手张开），只需提取其右手握剑的 20 个通道（`attr 117..136`），同时写入目标角色待机动画的左手（`attr 97..116`）与右手（`attr 117..136`），即可在 **100% 保留目标角色原版呼吸起伏、站姿与手臂角度** 的前提下，让双手稳稳握住武器。

### 完整实现与参考数据（以回春手 `tools/generate_lifeline_assets.py` 为例）

从 `Frontend_Sword_idle` 提取的右手握剑 20 通道真值，对称映射到双手 `97..136`：

```python
# Authentic sword-holding grip extracted from Frontend_Sword_idle (Right Hand attr 117..136)
# Applied symmetrically to Left Hand (attr 97..116) and Right Hand (attr 117..136).
LIFELINE_DUAL_SWORD_GRIP = {
    # Left Hand Fingers (attr 97..116 = muscle 55..74)
    97:  -1.5541633,  # Left Hand.Thumb.1 Stretched
    98:  -2.1583767,  # Left Hand.Thumb.Spread
    99:  -0.2255878,  # Left Hand.Thumb.2 Stretched
    100: -0.4691082,  # Left Hand.Thumb.3 Stretched
    101: -0.5655559,  # Left Hand.Index.1 Stretched
    102: -0.7321508,  # Left Hand.Index.Spread
    103: -1.2284926,  # Left Hand.Index.2 Stretched
    104:  0.8108447,  # Left Hand.Index.3 Stretched
    105: -0.5706741,  # Left Hand.Middle.1 Stretched
    106: -0.9387131,  # Left Hand.Middle.Spread
    107: -1.2096846,  # Left Hand.Middle.2 Stretched
    108:  0.8109050,  # Left Hand.Middle.3 Stretched
    109: -0.8122700,  # Left Hand.Ring.1 Stretched
    110: -1.1390761,  # Left Hand.Ring.Spread
    111: -1.6857924,  # Left Hand.Ring.2 Stretched
    112:  0.8109150,  # Left Hand.Ring.3 Stretched
    113: -0.6678960,  # Left Hand.Little.1 Stretched
    114: -0.7445285,  # Left Hand.Little.Spread
    115: -1.2094172,  # Left Hand.Little.2 Stretched
    116:  0.8109943,  # Left Hand.Little.3 Stretched

    # Right Hand Fingers (attr 117..136 = muscle 75..94)
    117: -1.5541633,  # Right Hand.Thumb.1 Stretched
    118: -2.1583767,  # Right Hand.Thumb.Spread
    119: -0.2255878,  # Right Hand.Thumb.2 Stretched
    120: -0.4691082,  # Right Hand.Thumb.3 Stretched
    121: -0.5655559,  # Right Hand.Index.1 Stretched
    122: -0.7321508,  # Right Hand.Index.Spread
    123: -1.2284926,  # Right Hand.Index.2 Stretched
    124:  0.8108447,  # Right Hand.Index.3 Stretched
    125: -0.5706741,  # Right Hand.Middle.1 Stretched
    126: -0.9387131,  # Right Hand.Middle.Spread
    127: -1.2096846,  # Right Hand.Middle.2 Stretched
    128:  0.8109050,  # Right Hand.Middle.3 Stretched
    129: -0.8122700,  # Right Hand.Ring.1 Stretched
    130: -1.1390761,  # Right Hand.Ring.Spread
    131: -1.6857924,  # Right Hand.Ring.2 Stretched
    132:  0.8109150,  # Right Hand.Ring.3 Stretched
    133: -0.6678960,  # Right Hand.Little.1 Stretched
    134: -0.7445285,  # Right Hand.Little.Spread
    135: -1.2094172,  # Right Hand.Little.2 Stretched
    136:  0.8109943,  # Right Hand.Little.3 Stretched
}
```

将该字典通过 `inject_dual_sword_grip_into_clip(tree)` 注入目标角色的展示厅待机 `TeamSelect_Female_idle`（PathID `807675994726628539`）与战前待机 `Prefight_Female_idle`（PathID `7081150187961391002`），并确保单元测试验证：
- `m_StreamedClip.data`、`m_DenseClip.m_SampleArray` 与原版 **100% 字节一致**；
- `m_ConstantClip.data` 中非手指项与原版 **100% 一致**，仅 `attr 97..136` 对应的 40 项被更新。

---

## 三、 标准方案二：在 Unity 3D 软件中可视化手调姿势 + `HumanPoseHandler` 导出（所见即所得）

如果需要针对特殊造型的武器在 3D 视口中看着刀柄一根根微调手指角度，**千万不要清空 `Avatar` 去烘焙 `.anim` 文件**，而应直接使用工程中已改造完成的 [`unity_lifeline/Assets/Editor/LifelinePoseWorkbench.cs`](file:///d:/Agent/tftf/unity_lifeline/Assets/Editor/LifelinePoseWorkbench.cs) 与 [`tools/apply_unity_idle_clip.py`](file:///d:/Agent/tftf/tools/apply_unity_idle_clip.py) 流水线。

### 四个必须严格遵守的工程铁律（防 AI 改错门禁）

1. **骨骼层级路径无 `character_model/` 前缀，`HumanPoseHandler` 根节点必须传顶层 `instance.transform`**：
   - 在角色的 `Avatar`（如 `cha_arcee_gs_deluxe2014_00Avatar`）的 `m_TOS` 映射表中，骨骼路径直接以 `"Reference/Hips/Spine/..."` 开头（**不存在** `"character_model/"` 子节点！），且 `Animator` 组件直接挂载在 Prefab 最顶层实例（`Lifeline_Showroom`）上。
   - 因此调用 `new HumanPoseHandler(anim.avatar, root.transform)` 时，第二个参数**必须且只能传挂载了 `Animator` 的最顶层 `root.transform`**；双手双刀的查找路径也必须是 `"Reference/Hips/Spine/Spine1/.../RightHand/swordRight"`。
2. **采样第 0 帧后必须禁用 `Animator`（`enabled = false`），但严禁清空 `Animator.avatar`**：
   - 加载场景时，先在 `instanceAnim.avatar` 完好的状态下调用 `sourceClip.SampleAnimation(instance, 0f)` 将角色定格在官方待机站姿；
   - 随后执行 `instanceAnim.runtimeAnimatorController = null; instanceAnim.enabled = false;` 解除骨骼锁定（否则在 Scene 视图中拖不动手指），**同时必须保留 `instanceAnim.avatar = origAvatar` 不清空**，供导出时 `HumanPoseHandler` 读取。
3. **加载场景时必须手动同步 `PropsController` 的武器掌心偏移**：
   - 独立 Unity 工程不运行游戏脚本 `PropsController.Awake()`，因此刚实例化时 `swordLeft` 和 `swordRight` 的 `localPosition` 会停留在 `(0, 0, 0)`（悬在手背外）。
   - 编辑器加载脚本必须主动设置 `swordRight.localPosition = new Vector3(0f, 0f, 0.38f)` 与 `swordLeft.localPosition = new Vector3(0f, 0f, -0.38f)`，保证 Unity 视口中刀柄与手掌的相对位置和游戏实机 100% 一致。
4. **导出与注入严禁整包替换 `AnimationClip`**：
   - 导出阶段由 [`LifelinePoseWorkbench.cs`](file:///d:/Agent/tftf/unity_lifeline/Assets/Editor/LifelinePoseWorkbench.cs) 将 `pose.muscles[55..94]` 按 `attr = 42 + mIdx`（即 `97..136`）写入 `unity_lifeline/Assets/AssetBundles/lifeline_finger_pose.json`（支持双手独立导出或右手一键镜像到左手）；
   - 注入阶段运行 `python tools/apply_unity_idle_clip.py`，脚本设有安全门禁（仅允许 `97 <= attr <= 136` 共 40 项），只微创更新原版 `TeamSelect_Female_idle` 与 `Prefight_Female_idle` 的手指通道，100% 保护原版身体呼吸曲线与重心高度。
