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

---

## 四、 标准方案三：从 Mixamo 等第三方 Pose 库跨骨骼重定向全身展厅待机（实机踩坑与血泪总结）

当需要给机甲角色套用全新全身待机姿势（例如从 Mixamo 下载的人体 FBX Pose）而非仅微调手指时，必须修改全部 130 个 Humanoid 通道。以下是在阿尔茜（`arcee_gs_deluxe2014` / `TeamSelect_Female_idle`）实机验证中用多次返工换来的 **6 条核心教训与标准流水线**，后续扩展到其他角色必须严格遵循。

### 核心踩坑清单（严禁重蹈覆辙）

1. **大坑 #3：严禁用 `BuildPipeline.BuildAssetBundles` 打包新建 `.anim` 替换原版 Clip —— 会丢失 Foot IK 导致“下半身折叠消失”**
   - **实机症状**：在独立渲染预览看似正常，打进 APK 上真机后角色只有上半身飘在半空、双腿完全折叠塞进骨盆内部。
   - **根因**：真机展厅使用的是 `characters.assetbundle` 中的公共状态机 `animator_char_lw`（`PathID=6875678843721788313`），其中 `FE_Idle` 状态默认开启了 **`iKOnFeet = True`**。
   - 用 `AnimationClip.SetCurve` + `BuildPipeline.BuildAssetBundles` 新建的 Clip 只包含肌肉曲线或裸动画属性，**完全缺失 `attr 14..27`（`LeftFootT/Q`、`RightFootT/Q`）与 `m_LeftFootStartX` / `m_RightFootStartX` 等 Foot IK 目标通道**；而且通过 `HumanTrait.MuscleName` 绑定手指曲线时，Unity 编译出的手指名（如 `"Left Thumb 1 Stretched"`）与内部 `Animator` 索引不匹配，会被编成 `customType = 0`（无法驱动引擎骨骼）。
   - `iKOnFeet = True` 读不到合法 `LeftFootT/RightFootT` 目标时，会把双脚 IK 目标拉向零点/骨盆高度（实测曾导致 `LeftFootY = 5.9157, RightFootY = 5.7814` 倒挂进 `HipsY = 5.5022`），直接把两条腿折进胯里。
   - **唯一正解**：与标准方案一相同，**永远不要整包替换原版 Clip 的 TypeTree**，而是在原版 `TeamSelect_Female_idle`（130 个 `typeID=95, customType=8` 通道）基础上，用 Python 脚本做**全通道原位数值替换**。

2. **大坑 #4：实机 Prefab 与编辑器原型 Prefab 的 `HumanPoseHandler` 根节点不一致**
   - **对比差异**：独立搭建的 `Lifeline_Showroom` 顶层节点直接挂骨架；但真机 AssetBundle（如 `Arcee_GS_Deluxe2014_lw`）中，`Animator` 挂在最外层 Prefab 根节点，而 `Avatar`（`cha_arcee_gs_deluxe2014_00Avatar`）的 `m_TOS` 路径却挂在子物体 **`character_model/`** 之下（以 `"Reference/Hips/..."` 开头）。
   - **后果**：若误传最外层 `inst.transform` 给 `new HumanPoseHandler(avatar, root)`，Unity 不会报错，但会**静默采样/回写全默认站姿**（实测 `Hips` 停留在 `(0.0023, 1.0, 0.0061)`）。
   - **规则**：对游戏原生 AssetBundle Prefab 调用 `HumanPoseHandler` 前，先检查是否存在 `inst.transform.Find("character_model")`，存在则必须传入 `character_model` 节点作为根节点。

3. **大坑 #5：纯骨骼方向向量（`FromToRotation`）会丢失脊柱/骨盆“扭转轴向（Contrapposto Twist）”**
   - Mixamo 站姿的美感往往来自骨盆与胸腔之间的反向拧转（如本次 Pose 1 存在约 `+85.4°` 的水平面拧转），两骨骼连线向量只包含俯仰/侧倾，**会丢失绕骨骼自转轴的 Roll/Yaw 分量**，直接导致摆出来的姿势僵硬或朝向错误。
   - **正解**：从双方模型的 `SkinnedMeshRenderer.sharedMesh.bindposes` 提取精确的世界空间绑定姿势逆矩阵，计算世界旋转增量 `poseRot * Quaternion.Inverse(bindRot)`，并做局部坐标系修正：
     - 处理 Mixamo（标准 T-Pose）与 TFTF 机甲（I-Pose 手臂下垂）的绑定差异：上臂/小臂需施加 `invT2I_L = Quaternion.Euler(0, 0, -90)` 与 `invT2I_R = Quaternion.Euler(0, 0, +90)` 补偿；
     - 映射胸椎链（如 Mixamo `Spine2 -> Arcee Spine1`）；
     - 机甲与真人的肩宽/胯宽/臂长比例差异极易引起叉腰或垂手**穿模（手臂插进腰甲/大腿）**：不能只抄关节旋转角度，必须对双手目标位置结合腰部边界施加外扩偏置（`±Z` 外移），再通过双骨骼解析 IK（`SolveTwoBoneIK`）重算上臂与前臂旋转，保证自然搭胯不穿模。

4. **大坑 #6：千万不要只拍正面单视角 —— 必须用真机 `characters.assetbundle` 状态机 + 360° 多视角联合验收**
   - 仅在正面单相机下看“大概像”，极易掩盖右手/刀鞘穿入侧腰、脚尖悬空或脚后跟陷入地板等问题。
   - 本工程已沉淀专用真机级验证器 [`VerifyRealGameAnimator.cs`](file:///d:/Agent/tftf/unity_lifeline/Assets/Editor/VerifyRealGameAnimator.cs)：同时加载 `characters.assetbundle`（真实 `animator_char_lw` 的 `FE_Idle` 状态，开启 `iKOnFeet = True`）与待测角色 Bundle，运行帧步进更新后打印 `HipsY / LeftFootY / RightFootY / LeftToeY / RightToeY / minMeshY` 接地数据与整周期位移平滑度，并固定输出 **`180°`、`130°`、`060°`、`300°` 四方向环绕截图**。
   - **Unity 命令行卡死提醒**：在本机 Windows 环境下运行上述验证/导出 Batchmode 时，**不要附加 `-nographics`**（该参数易触发 Unity 包管理或域重载卡死），保持标准 `-batchmode -quit -executeMethod ...` 即可快速退出。

5. **大坑 #7：改写 `m_StreamedClip` 时漏清 `kp + 3`（一次项斜率 $c_2$）会导致角色手脚疯狂锯齿抖动**
   - **数据结构**：Unity `m_StreamedClip` 中每个关键帧占 5 个 `uint32`：`[curveIdx, c0(dt³), c1(dt²), c2(dt¹), c3(const)]`（`kp+0` 到 `kp+4`），插值公式为 $y(dt) = c_0 dt^3 + c_1 dt^2 + c_2 dt + c_3$。
   - **常见误区**：误把 `kp+1 / kp+2` 当作 `inSlope / outSlope` 清零而**漏清 `kp+3`（`c2`）**！原版 `TeamSelect_Female_idle` 的手臂/前臂等 51 条曲线全部存在 `StreamedClip` 中，残留的 `c2` 会让手臂在每两个关键帧之间按原版挥手速度线性漂移、到下一帧瞬间弹回，肉眼表现为**整只手高频抽搐跳动**。
   - **正解**：
     - 静止通道必须将 `kp+1`、`kp+2`、**`kp+3`** 全部置 `0`，仅写入 `kp+4 = val`；
     - 叠加呼吸微动的 `StreamedClip` 通道（如 `attr 45` `Chest Front-Back`）必须按相邻关键帧间隔 $dx = t_1 - t_0$ 解析计算精确三次 Hermite 系数 `(c0, c1, c2, c3)`；
     - 同步核查支撑脚脚踝内/外翻肌肉（如 `muscles[27]` `Left Foot Twist In-Out`、`muscles[25]` `Left Lower Leg Twist In-Out`），避免人类软体网格的轻微崴脚角度在机甲硬质脚踝护甲上被放大为明显“外撇”，且支撑脚 Foot IK Goal（`LeftFootT`）应正对脚踝正下方地面 `(lf.x, 0, lf.z)`。

### 跨骨骼重定向标准流水线（以阿尔茜为例）

已固化的完整工具链位于 [`tools/run_arcee_pose1_pipeline.py`](file:///d:/Agent/tftf/tools/run_arcee_pose1_pipeline.py)：

1. **阶段 A（Unity C# 求解与通道导出）**：[`ExportArceePose1Data.cs`](file:///d:/Agent/tftf/unity_lifeline/Assets/Editor/ExportArceePose1Data.cs)
   - 加载 Mixamo FBX 与目标角色 Bundle，按 `sharedMesh.bindposes`、`T <-> I` 补偿、`Spine2 -> Spine1`、`SolveTwoBoneIK` 防穿模外扩及手指弯曲（`muscles[55..94]`）求解出目标世界姿态；
   - 通过 `HumanPoseHandler(avatar, character_model)` 读出精确 `bodyPosition`、`bodyRotation` 与 95 维 `muscles`；
   - **按游戏原生偏移反算 Foot/Hand IK Goal**：
     - Foot/HandGoal 局部坐标公式：`inv(bodyRot) * ((TargetWorldPos - bodyWorldPos) / humanScale)`、`inv(bodyRot) * (BoneRot * Offset)`（阿尔茜实测 `Offset_Foot = Quaternion(0.2421f, 0.6641f, -0.6647f, 0.2419f)`）；
   - 将所有 130 个通道参数导出至中间 JSON（如 `build/arcee_pose1_export.json`）。
2. **阶段 B（Python 130 通道原位注入 + 微动呼吸）**：[`inject_arcee_showroom_pose1.py`](file:///d:/Agent/tftf/tools/inject_arcee_showroom_pose1.py)
   - 从原版备份（`backup/arcee_gs_deluxe2014.assetbundle.orig`）读取 `TeamSelect_Female_idle`（`PathID=807675994726628539`）；
   - 原位重写全部 `customType = 8` 通道的 `m_ValueArrayDelta`、`m_StreamedClip`、`m_DenseClip`（77 帧采样）、`m_ConstantClip`，并同步更新 Clip 根端的 `m_StartX`、`m_StopX`、`m_LeftFootStartX`、`m_RightFootStartX`；
   - 在 `Spine / Chest / Head / Shoulders` 相关肌肉通道（`attrs 42, 45, 48, 79, 88`）叠加周期余弦呼吸微动 $0.5 \times (1 - \cos(2\pi t / T))$，确保静止站姿具备自然呼吸起伏而不改变首尾衔接；
   - 使用 `packer="lz4"` 写回 `assets_redeco/arcee_gs_deluxe2014.assetbundle`。
3. **阶段 C（真机状态机与四视角门禁校验）**：[`VerifyRealGameAnimator.cs`](file:///d:/Agent/tftf/unity_lifeline/Assets/Editor/VerifyRealGameAnimator.cs)
   - 验证通过标准：`LeftToeY / RightToeY` 贴近 `0.00~0.04`、`minMeshY >= -0.1`（无腿部折叠、无悬浮或深陷），且 `180°/130°/060°/300°` 四视角截图人工确认双肩与手指无穿模后，方可进入 APK 打包。

---

## 五、 标准方案四：完整长周期多帧动态动画替换（从静态姿势到几十秒连续动态演出）

当静态单帧 Pose 显得单薄，需要将第三方（如 Mixamo、外部动捕资产）长达十余秒甚至几十秒的**完整长动作（如双手叉腰 -> 侧身环视 -> 缓缓抱胸 -> 细腻微动循环）** 整体替换进游戏展厅待机（`TeamSelect_Female_idle`）时，必须解决多帧重定向、流式曲线组织、首尾无缝循环与 Foot IK 动态贴地等工程挑战。

以下是在克劳莉娅（`chromia_gs_kabam`，19.167 秒、576 帧全量动态待机）实机交付中沉淀的最佳工程实践。

### 核心技术突破与工程铁律

#### 1. Mixamo FBX 导入规范：声明为 Humanoid (`ModelImporterAnimationType.Human`) 启用引擎级自动重定向
- **原理解耦**：在之前的静态单帧方案中，为了修正机甲 I-Pose 与人体 T-Pose 的差异，曾花费大量精力在 C# 中手动反算 `bindposes`、局部欧拉角与双骨骼 IK。
- **正解**：导入外部 FBX 动捕资产时，直接通过 `ModelImporter` 将动画类型设为 **`ModelImporterAnimationType.Human`**：
  ```csharp
  ModelImporter mi = AssetImporter.GetAtPath(fbxPath) as ModelImporter;
  if (mi.animationType != ModelImporterAnimationType.Human) {
      mi.animationType = ModelImporterAnimationType.Human;
      mi.SaveAndReimport();
  }
  ```
- Unity 引擎底层的 Mecanim Humanoid 系统拥有顶级的工业级骨骼重定向算法。只需通过两个 `HumanPoseHandler`：
  ```csharp
  HumanPoseHandler hphSource = new HumanPoseHandler(sourceAnim.avatar, sourceInst.transform);
  HumanPoseHandler hphTarget = new HumanPoseHandler(targetAnim.avatar, targetModelTransform);
  ```
  在每一帧对源模型调用 `clip.SampleAnimation(sourceInst, t)` 并通过 `hphSource.GetHumanPose(ref hp)` 获取肌肉数据，再直接传入 `hphTarget.SetHumanPose(ref hp)`，**全身体态、手腕手指与腰肢扭转即由引擎 100% 自动精确映射至机甲，彻底告别繁琐易错的骨骼轴向手工补偿**！

#### 2. 底层曲线架构重构：将 130 通道全部提升为纯密集阵列（`DenseClip`）
- **旧架构瓶颈**：原版游戏待机动作受限于官方压包策略，被拆分为 `StreamedClip`（51 条）、`DenseClip`（24 条）与 `ConstantClip`（55 条）。若强行在旧架构上注入多帧动画，原本存放在 `ConstantClip` 中的关节（如手指、头部、小腿）会被硬编码锁死，而 `StreamedClip` 的 Hermite 样条由于关键帧稀疏，极易引发前文大坑 #7 的斜率抽搐。
- **最佳重构方案**：**彻底抛弃混合架构，将 `genericBindings` 的全部 130 个通道统一纳入 `m_DenseClip`**：
  - **`m_StreamedClip`**：清空曲线，仅保留正无穷哨兵标记：
    ```python
    streamed["curveCount"] = 0
    streamed["data"] = [2139095040, 0]  # 0x7f800000 (+inf), keyCount = 0
    ```
  - **`m_ConstantClip`**：清空常数阵列：
    ```python
    constant["data"] = []
    ```
  - **`m_DenseClip`**：接管全部 130 通道与 $N$ 帧数据（形状为 `(N, 130)`）：
    ```python
    dense["m_CurveCount"] = 130
    dense["m_FrameCount"] = frame_count  # 如 576
    dense["m_SampleRate"] = 30.0
    dense["m_SampleArray"] = d_samples.flatten().tolist()
    ```
  - **`m_MuscleClip`**：同步更新总时长与首尾姿态：
    ```python
    mc["m_StartTime"] = 0.0
    mc["m_StopTime"] = duration  # 19.166667
    for b_idx in range(130):
        deltas[b_idx]["m_Start"] = float(d_samples[0, b_idx])
        deltas[b_idx]["m_Stop"]  = float(d_samples[-1, b_idx])
    mc["m_ValueArrayDelta"] = deltas
    ```
- **验证结论**：该结构与游戏原生大招动画（如 `chromia_gs_attackspecial_03`、`frontend_Arcee_levelup_exit`）底层规范 100% 一致，引擎原生深度支持，且 576 帧经 LZ4 压缩后体积仅增大约 220 KB，对加载和运行内存零压力。

#### 3. 首尾循环（Seamless Looping）双重防跳帧机制
- **展厅机制**：角色展示界面的待机动作以 `WrapMode.Loop` 方式无限循环。若最后一帧与第一帧存在肢体姿态断层，在每次循环重置时均会出现瞬移跳帧。
- **校验原则**：
  - 优质动捕资产（如 Mixamo 的标准 Idle 动作）往往天然首尾相连。在采样前需提取 $t=0.0s$ 与 $t=T$ 的 `bodyPosition`、`bodyRotation` 与手脚通道比对。
  - 若外部动画非首尾循环，**必须在最后 0.8 秒（约 24 帧）施加余弦缓动平滑混合（Cosine Blend）**：
    $$\alpha = 0.5 \times \left(1 - \cos\left(\frac{\pi (t - t_{\text{blend}})}{T - t_{\text{blend}}}\right)\right)$$
    将姿态逐帧向第 0 帧平滑插值（四元数采用 `Quaternion.Slerp`，标量肌肉采用 `Mathf.Lerp`），实现无感衔接。

#### 4. 逐帧动态接地与 Foot IK 矩阵反算
- **动态沉降消除**：真实动捕演员在呼吸晃动或交叉双臂时，膝盖微屈常引起骨盆下沉 5~15 cm。在逐帧循环中，通过 `GetMinMeshY(clean)` 实时探测脚底网格与地板的相对高度，每帧动态补偿 `hp.bodyPosition.y -= curMinY / scaleEst`，确保两脚脚底无论动作如何起伏，始终严密贴合 $Y=0$ 地面。
- **Foot IK Goal 逐帧生成**：
  根据每帧角色的实时重心世界坐标与旋转逆矩阵，动态反算 `LeftFootT/Q` 与 `RightFootT/Q`：
  ```csharp
  Vector3 bodyWorldPos = hp.bodyPosition * actualHs;
  Quaternion invBodyRot = Quaternion.Inverse(hp.bodyRotation);

  Vector3 lfSoleWorld = new Vector3(lf.position.x, 0f, lf.position.z);
  Vector3 rfSoleWorld = new Vector3(rf.position.x, 0f, rf.position.z);

  Vector3 lfT = invBodyRot * ((lfSoleWorld - bodyWorldPos) / actualHs);
  Quaternion lfQ = invBodyRot * (lf.rotation * offsetFoot);
  Vector3 rfT = invBodyRot * ((rfSoleWorld - bodyWorldPos) / actualHs);
  Quaternion rfQ = invBodyRot * (rf.rotation * offsetFoot);
  ```
  配合脚踝外撇修正（`muscles[27] = 0.0f, muscles[35] = 0.0f, muscles[25] = -0.05f, muscles[33] = +0.05f`），确保游戏原生状态机 `animator_char_lw` 在开启 `iKOnFeet = True` 时，不仅不会引起下半身折叠，反而能让双脚稳如磐石。

### 固化的完整长动画工具链

1. **Unity 批量采样导出**：[`unity_lifeline/Assets/Editor/ExportChromiaAngryAnimation.cs`](file:///d:/Agent/tftf/unity_lifeline/Assets/Editor/ExportChromiaAngryAnimation.cs)
   - 自动导入 FBX 为 Humanoid，逐帧重定向、动态接地并反算 IK 目标，导出包含全部 576 帧数据的 JSON（`build/chromia_anim_angry_export.json`）。
2. **Python 纯 DenseClip 注入**：[`tools/inject_chromia_angry_animation.py`](file:///d:/Agent/tftf/tools/inject_chromia_angry_animation.py)
   - 重构 `TeamSelect_Female_idle` 的 `m_DenseClip`、`m_StreamedClip` 与 `m_ConstantClip`，按 LZ4 高效压缩写入 `assets_redeco/chromia_gs_kabam.assetbundle`。
3. **原生状态机回放检验**：[`unity_lifeline/Assets/Editor/VerifyPatchedAnimationPlayback.cs`](file:///d:/Agent/tftf/unity_lifeline/Assets/Editor/VerifyPatchedAnimationPlayback.cs)
   - 加载真实 `characters.assetbundle` 控制器与打好的 Bundle，分段推进回放整套 19 秒动作，门禁验证无 NaN、无破面、接地高度浮动收敛在安全范围内。

---

## 六、 滑流（Slipstream）与风刃（Windblade）实机交付规范与持械解耦

在滑流（Slipstream，看左手指甲 4.433 秒待机）与风刃（Windblade，叉腰持刀待机）的开发中，进一步完善了共享切片解耦、持械角色手指融合与双脚平踏接地的规范：

### 1. 共享外部 Procedural 待机切片的独立解耦铁律
- **风险背景**：原版风刃在 `override_WindBlade_GS_lw` 中的 `FE_Idle` 条目默认引用外部 `character_anim_procedural.assetbundle` 中的通用持刀待机 `Frontend_Sword_idle`（`PathID = 4726225886941715276`）。该切片被漂移（Drift）与钢锁（Grimlock）等多名持剑角色共享。若直接修改外部切片，将导致其他全部持刀角色动作同步被改。
- **解耦规范**：
  1. 在风刃自身 Bundle（`windblade_gs.assetbundle`）内克隆创建一个全新的独立内部 `AnimationClip`（分配唯一 PathID 如 `8888777766665555`）。
  2. 修改 `override_WindBlade_GS_lw` 中 `FE_Idle` 的重定向指针：从 `{'m_FileID': 3, 'm_PathID': 4726225886941715276}` 修改为 `{'m_FileID': 0, 'm_PathID': 8888777766665555}`。
  3. 实现风刃展厅动作彻底私有化，不影响任何其他角色。

### 2. 单手持武器角色的“真实握姿 + 动捕姿态”精准融合
- 当为持武器角色（如右手握刀的风刃）定制展示动作时，身体四肢与左手来自外部动捕 FBX，而**右手及手指 20 通道肌肉（`muscles[75..94]`）必须完整继承官方持刀动作（`Frontend_Sword_idle`）的真实握姿**。
- 这避免了外部动捕中右手五指张开穿透武器刀柄的硬伤，实现刀柄与五指的严密贴合。

### 3. Humanoid 肌肉核心索引速查（排查肢体错位的真理基线）
在编写 Unity 脚本调节肢体姿态时，必须严格遵守引擎底层 `HumanTrait.MuscleName` 的真实下标：
- **下肢与双脚**：
  - `Left Upper Leg`: 21 (FB), 22 (IO), 23 (Twist) | `Right Upper Leg`: 29 (FB), 30 (IO), 31 (Twist)
  - `Left Lower Leg`: 24 (Stretch), 25 (Twist) | `Right Lower Leg`: 32 (Stretch), 33 (Twist)
  - `Left Foot`: 26 (Up-Down), 27 (Twist) | `Right Foot`: 34 (Up-Down), 35 (Twist)
  - `Left Toes`: 28 (Up-Down) | `Right Toes`: 36 (Up-Down)
- **左上肢与手腕**：
  - `37`: Left Shoulder Down-Up, `38`: Left Shoulder Front-Back
  - `39`: Left Arm Down-Up, `40`: Left Arm Front-Back, `41`: Left Arm Twist In-Out
  - `42`: Left Forearm Stretch（前臂弯曲伸展，负数为折肘，正数为伸直）, `43`: Left Forearm Twist
  - `44`: Left Hand Down-Up, `45`: Left Hand In-Out
- **左手手指（`55..74`）**：
  - `55..58`: Left Thumb (T1, Spread, T2, T3)
  - `59..62`: Left Index (I1, Spread, I2, I3)
  - `63..66`: Left Middle | `67..70`: Left Ring | `71..74`: Left Little
- **右手手指（`75..94`）**：
  - `75..78`: Right Thumb | `79..82`: Right Index | `83..86`: Right Middle | `87..90`: Right Ring | `91..94`: Right Little

### 4. 动捕踮脚浮空与叉腰悬空修正
- **踮脚浮空（High-Heel Float）根治**：外部女性站姿动捕中，常有单腿下扣踮脚动作（如 `Left Foot UD = 0.736`）。在开启游戏 `iKOnFeet = True` 的状态机下，此参数会导致该腿脚后跟浮空无法踩实地面。修正时必须将双脚统一设为水平平踏（`FootUD ≈ 0.04`，`CalfStretch ≈ 0.82`），确保脚底网格严密贴合地面。
- **叉腰贴合度与大拇指朝向**：机甲角色的腰部结构与人体不同（外侧通常有突出的髋部护甲）。叉腰时需将大臂稍下放（`ArmDU ≈ -0.28`）并后拉（`ArmFB ≈ 0.35`），使手腕落在髋骨护甲边缘；将大拇指展开度设为负向紧收（`ThumbSpread ≈ -0.85`），使其顺着护甲上沿自然水平贴合，防止反向翻翘。

---

## 七、 跨游戏借用战斗动作（MCOC → TFTF）与粒子特效缝合/本地视频预览流水线

在拓展特殊技（SP1/SP2）动作借用与跨角色特效缝合的实战中，沉淀出以下从 **MCOC 借动作**、**TFTF 粒子特效魔改** 到 **本地 Unity 免打包视频验收** 的标准方法论：

### 1. MCOC 跨游戏借用战斗动作（SP1/SP2）核心原理
- **底层肌肉通道 100% 通用**：MCOC（即便为 Unity `6000.3.10f1` 构建）与《百炼为战》（Unity `2020.3.31f1`）同源，其 Humanoid `AnimationClip` 的 `typeID = 95` 通道定义完全一致（`7..9` = `RootT`，`10..13` = `RootQ`，`14..41` = IK Goals，`42..136` = 95 块肌肉）。因此可以直接提取 MCOC 角色包中 `m_DenseClip` / `m_ConstantClip` / `m_StreamedClip` 的纯数值曲线用于 TFTF 动作移植。
- **真身模型直接 Humanoid 重定向**：TFTF 角色本体（如 Swoop `cha_ramjet_gs_deluxe2008_00Avatar` `scale = 6.836`、Shockwave `cha_shockwave_gs_mp29_00Avatar` `scale = 7.412`、Rodimus `cha_rodimusprime_gs_mp09_00Avatar` `scale = 7.052`）自带标准 Humanoid Avatar。通过 `HumanPoseHandler` 驱动时，Unity 会按 `animator.humanScale` 自动完成位移比例缩放。
- **连击数（Hits）与倒地（Knockdown）完全由 `moves.assetbundle` 控制**：
  - 动画本身不锁定 Hits 数量与击倒逻辑；实际判定完全取决于招式 JSON `events` 中挂载了多少个 `HitMoveEvent`（近战）或 `ProjectileMoveEvent`（弹道）（例如 MCOC 猎鹰 SP1 原版 `nhe: 8`，含 1 击近身翼刃 `dam=0.2` + 7 发速射各 `0.1/0.2`，总权重 = `1.0`）。
  - 前段连击配置 `db: false` + 轻/中受击硬直（`hr`，如 `HitReactionLightBackHigh`），保证对手保持站立硬直而不飞出射程；最后一击配置 **`db: true`** + **`hr: "HitReactionHeavyBack"`** + 高 `kb`，即可实现“连续挨打后摇 → 末击击倒”的标准手感。

### 2. 原生粒子特效跨角色缝合与参数魔改（以“震荡波 SP2 + 满屏喷火”为例）
- **特效来源原则（严禁硬搬 MCOC 粒子）**：MCOC 的粒子 Prefab 依赖 Unity 6000 Shader 与脚本，直接搬入 TFTF 极易粉屏报错。特效与弹道应统一从 **TFTF 自身供体底包或公共库** 取材（如喷气机底包继承的 `fx_p_jetfire_large`、`fx_p_gatling_muzzle_flash`、野牛的 `fx_p_tantrum_flame_thrower`、公共弹道 `projectile_special_bullet` 等）。
- **射程、密度与颜色魔改方法**：
  - 以野牛短程喷火 `fx_p_tantrum_flame_thrower`（原参数 `startSpeed=26`, `startLifetime=0.80`, `rateOverTime=40`, `limitVelocity=True`）缝合到震荡波 SP2（第 44 帧起喷、持续 `d=18` 帧）为例：
  - 将粒子系统的 **`startSpeed` 提升至 `72`**、**`startLifetime` 延至 `0.95s`**、**关闭 `limitVelocityOverLifetime` 阻力限制**，并把 **`rateOverTime` 提至 `95`**，即可将原本近距离喷火拉长为贯穿全屏的高压烈焰；同时可在 `colorOverLifetime` / 材质色调中直接修改火焰颜色。
  - 在招式 JSON 的 `ParticleMoveEvent` 中，通过 `ref` 绑定到新角色的手部/炮口骨骼（如 `LeftHand`、`LeftProp`），再配合 `po`（偏移坐标）与 `ro`（喷射朝向）即可精准对齐枪口或胸口。

### 3. 本地 Unity 免打包视频预览流水线（20 秒快速验收）
无需每次调整喷火距离、颜色或偏移都打包进 APK 装机验证，直接在本地 `unity_lifeline` 中通过 **Batchmode + `ParticleSystem.Simulate` + `ffmpeg`** 即可生成 30fps MP4 与 GIF：
1. **AssetBundle 直加载与桌面端贴图修复**：通过 `UnityPy` 预先将角色及粒子用到的贴图解出为 `.png`；Unity 脚本用 `AssetBundle.LoadFromFile` 加载 Android 角色包实例化角色后，将角色材质替换为桌面端 `Standard`、将粒子材质替换为 `Legacy Shaders/Particles/Additive`（保留原贴图与 `6x6` UV 序列帧设置）以防粉屏。
2. **逐帧推进与广角格斗机位铁律**：
   - 在帧循环中逐帧调用 `HumanPoseHandler.SetHumanPose` 推进骨骼动作，并在攻击窗口调用 `ps.Simulate(1f/30f, false, false)` 精确模拟粒子飞行；
   - **摄像机机位铁律**：必须放置在格斗正面侧翼（`+X` 侧）且保持**固定宽景或极低比例平滑追踪**（如 `Mathf.Lerp(stageCenter, rz, 0.25f)`），配合网格地面与对手靶机受击反馈。**严禁 100% 死锁追踪 `rz`/`ry`**，否则角色前冲与腾空位移会被摄像机完全抵消，产生“人偶僵在空中原地旋转”的视觉错觉。
3. **参考脚本链**：
   - 动作曲线提取：[`tools/export_falcon_sp1_frames.py`](file:///d:/Agent/tftf/tools/export_falcon_sp1_frames.py)、[`tools/prepare_shockwave_flame_preview.py`](file:///d:/Agent/tftf/tools/prepare_shockwave_flame_preview.py)
   - Unity 本地视频渲染：[`unity_lifeline/Assets/Editor/RenderSwoopFalconSP1Video.cs`](file:///d:/Agent/tftf/unity_lifeline/Assets/Editor/RenderSwoopFalconSP1Video.cs)、[`unity_lifeline/Assets/Editor/RenderShockwaveFlameSP2Video.cs`](file:///d:/Agent/tftf/unity_lifeline/Assets/Editor/RenderShockwaveFlameSP2Video.cs)、[`unity_lifeline/Assets/Editor/RenderRodimusFlameSP2Video.cs`](file:///d:/Agent/tftf/unity_lifeline/Assets/Editor/RenderRodimusFlameSP2Video.cs)
   - 视频/动图合成：[`tools/encode_swoop_sp1_video.py`](file:///d:/Agent/tftf/tools/encode_swoop_sp1_video.py)、[`tools/encode_shockwave_flame_video.py`](file:///d:/Agent/tftf/tools/encode_shockwave_flame_video.py)、[`tools/encode_rodimus_flame_video.py`](file:///d:/Agent/tftf/tools/encode_rodimus_flame_video.py)
