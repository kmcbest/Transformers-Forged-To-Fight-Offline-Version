# 《Transformers: Alliance》第三方模具移植必读指南（TFTF Porting Playbook）

> **文档定位**：所有来自 ***Transformers: Alliance*** 游戏的第三方模具（含常规战士、持械剑枪角色、飞机载具及鸟兽/机器恐龙变体）向《变形金刚：百炼为战》（TFTF）移植的**第一顺位必读入口总纲**。  
> **阅读顺序**：凡移植 *Alliance* 模具，**必须先完整通读本指南**并严格按黄金脚本模板推进；仅在需要深究某个底层算法、非 Alliance 通用规范或完整门禁命令行时，再按索引跳转阅读三份深度参考文档。

---

## 0. 角色类型路由与参考文档地图

### 0.1 黄金脚本模板选型（严禁从零重写）

| 目标模具特征 | 黄金参考角色 | 必须复制适配的脚本目录 / 文件 |
| :--- | :--- | :--- |
| **近战持械 + 副手枪械 + 战机** | **史达（Star Saber）** | [`tools/starsaber/`](file:///e:/Agent/TFTF-blender/tools/starsaber/)（贴图 [`build_starsaber_textures.py`](file:///e:/Agent/TFTF-blender/tools/starsaber/build_starsaber_textures.py)、人形 [`build_aligned_starsaber_robot.py`](file:///e:/Agent/TFTF-blender/tools/starsaber/build_aligned_starsaber_robot.py)、载具 [`build_aligned_starsaber_veh.py`](file:///e:/Agent/TFTF-blender/tools/starsaber/build_aligned_starsaber_veh.py)、HITL [`build_hitl_starsaber_assets.py`](file:///e:/Agent/TFTF-blender/tools/starsaber/build_hitl_starsaber_assets.py) & [`BuildStarSaberHITLScene.cs`](file:///e:/Agent/TFTF-blender/tools/starsaber/unity_scripts/BuildStarSaberHITLScene.cs)、打包 [`generate_starsaber_bundle.py`](file:///e:/Agent/TFTF-blender/tools/starsaber/generate_starsaber_bundle.py)） |
| **鸟兽 / 机器恐龙 + 原生变形动作** | **飞标（Swoop）** | [`tools/swoop/`](file:///e:/Agent/TFTF-blender/tools/swoop/)（贴图 [`build_swoop_atlased_textures.py`](file:///e:/Agent/TFTF-blender/tools/swoop/build_swoop_atlased_textures.py)、人形 [`build_aligned_swoop_robot.py`](file:///e:/Agent/TFTF-blender/tools/swoop/build_aligned_swoop_robot.py)、载具与拍翅提取 [`build_aligned_swoop_vh.py`](file:///e:/Agent/TFTF-blender/tools/swoop/build_aligned_swoop_vh.py)、注包 [`generate_swoop_bundle.py`](file:///e:/Agent/TFTF-blender/tools/swoop/generate_swoop_bundle.py)、重击火球补丁 [`patch_swoop_heavy_move.py`](file:///e:/Agent/TFTF-blender/tools/swoop/patch_swoop_heavy_move.py)、自检 [`validate_swoop_bundle.py`](file:///e:/Agent/TFTF-blender/tools/swoop/validate_swoop_bundle.py)、Unity [`BuildSwoopInspectionScene.cs`](file:///e:/Agent/TFTF-blender/toolchain/unity_build_project/Assets/Editor/BuildSwoopInspectionScene.cs)） |
| **双色发光拆分与金属漆校色** | **横炮 / 飞标** | [`tools/sideswipe/generate_sideswipe_bundle.py`](file:///e:/Agent/TFTF-blender/tools/sideswipe/generate_sideswipe_bundle.py) + [`tools/swoop/build_swoop_atlased_textures.py`](file:///e:/Agent/TFTF-blender/tools/swoop/build_swoop_atlased_textures.py) |

### 0.2 四份核心前置/深度参考文档

* **强制门禁执行层**：[`BOT_PORTING_SELF_CHECK_PROTOCOL.md`](file:///e:/Agent/TFTF-blender/re_notes/BOT_PORTING_SELF_CHECK_PROTOCOL.md)（[`validate_port_gates.py`](file:///e:/Agent/TFTF-blender/tools/validate_port_gates.py) 四阶段 Fail-Fast 拦截与 `[SELF-FIX]` 修复矩阵）。
* **全管线技术百科**：[`THIRD_PARTY_3D_MODEL_PIPELINE.md`](file:///e:/Agent/TFTF-blender/re_notes/THIRD_PARTY_3D_MODEL_PIPELINE.md)（特别是 **`§11.16` 史达 HITL 握剑、`§11.17` Alliance 六大核心范式、`§11.18` 飞标专题、`§11.19.6` 双 SubMesh 双色自发光拆分与腔体防遮挡**）。
* **鸟兽非单位缩放专项**：[`BIRD_BEAST_TRANSFORMATION_PIPELINE.md`](file:///e:/Agent/TFTF-blender/re_notes/BIRD_BEAST_TRANSFORMATION_PIPELINE.md)（重点参阅 **`§3` FBX `Lcl Scaling` 剥离与纯 Python 递归 FK+LBS 烘焙公式**；注意其早期章节对重击与发射点的描述已在后期被 `tools/swoop/patch_swoop_heavy_move.py` 的实际方案取代，**代码以 `tools/swoop/` 为准**）。
* **新角色入包防崩铁律**：[`ORIGINAL_CHARACTER_CREATION_GUIDE.md`](file:///e:/Agent/TFTF-blender/re_notes/ORIGINAL_CHARACTER_CREATION_GUIDE.md)（防卡 LOGO、防进战 `SIGTRAP` 闪退：`script_types` 严格升序、`m_PreloadTable` 闭环覆盖、`moves.assetbundle >= 945`）。

---

## 1. Alliance 源 FBX 导入前的四大固有陷阱

相比 FOC（旋风/袭击/吵闹）模具，*Alliance* 游戏的 FBX 普遍存在以下四类工程特性，**导入阶段不处理就会全盘错位或爆炸**：

1. **默认激活载具轨道（假 Rest Pose 陷阱）**
   * Alliance 模型导出时往往默认激活 `Bip001|vehicle_idle01` 动作轨道，一导入 Blender 就会显示为半折叠载具或扭曲站姿。
   * **铁律**：提取人形 Rest Pose 前，必须先对骨架执行 `animation_data_clear()` 并遍历所有 `PoseBone` 复位 `rotation_quaternion / location / scale` 为单位矩阵。
2. **`0.01x` `*_pbr` 外壳容器与正反面校验**
   * Alliance 源网格常带有 `0.01` 全局缩放的 `*_pbr` 父容器，而骨架坐标位于 Armature 空间。读取骨骼关节世界坐标转入网格局部空间时，必须显式使用 `mesh.matrix_local.inverted() @ b.head_local`。
   * **正反面铁律**：导入并转轴落地后，必须第一时间确认**胸甲/面罩朝向 `+Z`（正面）、翅膀/背包位于 `-Z`（背面）**，严禁把人形正反面装反！
3. **3ds Max 非单位骨骼 `Lcl Scaling != 1.0` 剥离大爆炸（鸟兽/细长件高危）**
   * Alliance 鸟兽、长颈、鸟喙或尾翼骨骼常被 3ds Max 使用非等比缩放调整长度（如 `bird_neck = 0.3366`、`bird_Head = 0.6236`、`beak = 0.4659`）。Blender 的 `EditBone` 结构会强制丢弃 Rest Scale（归 `1.0`），但顶点 `BindPose` 仍按旧缩放计算，导致直接按 Pose 变形时**头部、鸟喙飞出数米发生断头爆炸**。
   * **标准解法**：使用 `io_scene_fbx.parse_fbx` 直接读取原始 FBX `Properties70` 中的 `Lcl Scaling`，在纯 Python 内存中按递推全局 Rest/Pose 矩阵完成 Forward Kinematics 与局部 Linear Blend Skinning（LBS）顶点烘焙，彻底绕开 Blender `EditBone` 缩放剥离（公式详见 [`BIRD_BEAST_TRANSFORMATION_PIPELINE.md §3`](file:///e:/Agent/TFTF-blender/re_notes/BIRD_BEAST_TRANSFORMATION_PIPELINE.md#L93-L140)，源码样板见 [`build_aligned_swoop_vh.py`](file:///e:/Agent/TFTF-blender/tools/swoop/build_aligned_swoop_vh.py)）。
4. **杂件清理与 `det = -1` Y/Z 轴交换绕序守卫**
   * 清理源包自带废对象（如 `Symbol_DC`、`Shadow`、`*_Weapon` 占位壳等）。
   * Blender `(x, y, z)` 映射 Unity `(x, z, y)` 时矩阵行列式 $\det = -1$，在 Unity 导入后必须同步翻转三角形索引并取反切线 `.w`，校验 $\sum \text{Cross}(p_1 - p_0, p_2 - p_0) \cdot n_0 > 0$，确保实测 `fn · vn > +0.85`（[`THIRD_PARTY_3D_MODEL_PIPELINE.md §11.12`](file:///e:/Agent/TFTF-blender/re_notes/THIRD_PARTY_3D_MODEL_PIPELINE.md#L1098-L1106)）。

---

## 2. 三指拓扑手部标准化处理（9 骨 `Hand_L/R_1..9` + `Dummy_hand`）

Alliance 角色手部绝非 TFTF 标准的 5 指 30 骨，而是 **`Dummy_hand` + 每侧 9 根骨骼组成的三分支拓扑**（`Hand_*_1..9`：独立拇指、独立食指、中/无名/小指连体铸造的三指套）。**严禁强行按 Y 坐标切分连体指套并套用 30 指骨**，否则进战斗一握拳就会撕裂成飞刺。按角色是否持械分为两条标准轨道：

### 2.1 轨道 B：徒手握拳系（如 Swoop 飞标 —— 收敛合入 `LeftHand` / `RightHand`）

* **权重策略**：先用原模型自有手部指骨烘焙出自然的握拳静止姿态，再将所有 `Hand_L/R_1..9` 顶点权重 **100% 并入母体 `LeftHand` / `RightHand`**，母体 30 根灵动指骨权重全部清零；同时按腕部轴向微调手掌收纳深度防止陷进小臂或悬空。
* **🚨 右拳大拇指对称镜像铁律（Swoop 实战血训）**：
  * **严禁凭直觉手猜右拳拇指四元数旋转轴！**（手猜旋转轴曾导致 Swoop 左手完美握拳，右手大拇指却向外撇直刺向大腿）。
  * **标准公式**：先调好并肉眼确认左拳拇指四元数 `LEFT_FIST_QUATS`，再通过 **Mesh 空间 `X=0` 平面严格轴镜像**推导右拳 `Bone_R_Finger0/01/02` 姿态——保持旋转轴 `Y/Z` 分量不变、反转 `axis.x` 并取反旋转角 `-angle`（实现见 [`build_aligned_swoop_robot.py`](file:///e:/Agent/TFTF-blender/tools/swoop/build_aligned_swoop_robot.py)）。
  * **必查画面**：Unity 检查图中必须产出左、右拳同框微距图，确认双侧拇指均向掌心扣合。

### 2.2 轨道 A / Unity HITL：持近战武器系（如 Star Saber 史达 —— 握柄入掌心 + `+90°` 刃向校正 + 网格焊接）

* **HITL 可视化对位**：提取 `Hand_R_1->4->5`（拇指）、`Hand_R_2->6->7`（食指）、`Hand_R_3->8->9`（连体三指）在 Unity 中搭建可交互微调台（[`BuildStarSaberHITLScene.cs`](file:///e:/Agent/TFTF-blender/tools/starsaber/unity_scripts/BuildStarSaberHITLScene.cs)），驱动拇指/指节包络剑柄时**统一使用 `Quaternion.FromToRotation` 计算目标朝向差，严禁手算 `Vector3.Cross`**。
* **放准手心与刃向校正（Star Saber 踩坑总结）**：
  1. 先把剑柄中心锚定嵌入 `RightHand` 掌心袋区（防止剑悬浮在指尖外或穿破手背）；
  2. 通过 `swordMesh.bounds.size` 自动识别剑身最长轴，在 `swordLocalRotationEuler.z` 施加 **`+90°`** 等轴向修正，确保剑刃平面与护手朝向完全贴合母体持剑动作（严禁“竖刃变横刃”或刀背砍人）；
  3. 对位定稿后在 Unity 中调用 `BakeMesh()` 冻结手指与剑体位置，焊接融合至母体 54 骨的 `RightHand`。
* **🚨 Unity `.asset` 网格写盘生死线**：
  * **严禁对运行时 `new Mesh()` 调用 `EditorUtility.CopySerialized(built, existing)`**（Unity 2020 Editor 下会静默丢失 C++ `m_VertexData` 与索引更新，导致旧顶点+新索引撕裂甚至游戏隐形）。
  * 必须使用 **`existing.Clear(false)` 后逐属性写回**，或直接 **`AssetDatabase.DeleteAsset` + `AssetDatabase.CreateAsset` 全量重建**。

---

## 3. 副手借用/外挂远程武器规范（`PropsController` + 对象池 + 图集 + 音效）

若需为 Alliance 角色副手配置远程枪炮等外挂 Props（例如给 Star Saber 左手补配 `StarSaberGun`，总结自 [`THIRD_PARTY_3D_MODEL_PIPELINE.md §11.17`](file:///e:/Agent/TFTF-blender/re_notes/THIRD_PARTY_3D_MODEL_PIPELINE.md#L1215-L1283)）：

1. **Main 与 `_lw` 双预制体同步挂载**：武器网格与骨骼节点必须**同时**绑定挂载到主 Prefab 与轻量化 `_lw` Prefab 的对应手腕节点（如 `LeftHand`）下。
2. **同步修正 `PropsController` 初始化配置**：光改 Prefab Transform 无效！必须在角色蓝图/组件所属 `PropsController` 数据（如 `_props["gun"]`）中，精确写入 `InitProps()` 依赖的 **`RootPath`、`PositionOffset`、`RotationOffset`**，并把源枪械模型尺幅缩放到匹配母体尺度（如 `4.0x`）。
3. **发射事件、投射物重命名与双 `PrefabList` 对象池注册**：
   * 远程动作帧中需配置匹配出手节奏的 `PropMoveEvent`；
   * 借用或定制的子弹 Prefab 需与招式配置名严格一致，并在双 `PrefabList` 对象池列表完成注册，否则开火瞬发空包弹或空指针闪退。
4. **共享图集象限与 FSB5 音频追加**：
   * 武器贴图统一合入角色主图集的独立 UV 象限（如 `U ∈ [0.5, 1.0]`），共享同一个 PBR 材质避免额外材质槽溢出；
   * 补充远程开火音效时，将音频按 FSB5 流格式追加至对应 `.resource` 尾部并保持 `AudioClip` 元数据对齐。
5. **母体废旧武器干净屏蔽（`_wpns_` 清零）**：
   * 若借用的母体自带多余默认武器容器（如 `_wpns_`），注入产物时必须三保险彻底关停：`m_IsActive = False`、`SMR.m_Enabled = False`、`m_LocalScale = (0, 0, 0)`。

---

## 4. 贴图、双眼、3D 阵营标与 Grimlock 官方金属质感校准

Alliance 原生贴图与 TFTF Kabam `EB/Character/PBR` 管线存在结构性差异，直接直出必定发黑、灰白过曝或错亮额头：

### 4.1 `Tx_*_D.png` Alpha 缩放黑化死坑 & `Tx_*_S.png` 通道语义

* **致命黑化陷阱**：Alliance 的 `Tx_*_D.png` **机身大半区域 `Alpha = 0`**！若直接调用 `Image.resize(..., Image.LANCZOS)`，PIL 的 RGBA 预乘滤波会把零 Alpha 周边的像素全部乘成 `(0, 0, 0)` 黑碳！
  * **铁律**：缩放贴图前**必须先执行 `.split()` 剥离 `RGB` 与 `A` 通道**，单独缩放 `RGB` 后再分别处理各控制通道。
* **Alliance `Tx_*_S.png` 通道映射**：
  * **`S.R`** = 高光/金属反射提示；**`S.G`** = 光泽/粗糙度参考（映射到 `RAOE.R`）；**`S.B`** = 原模型自带烘焙 AO（应混合至 `RAOE.G` 保住装甲沟壑层次）。
* **`Tx_*_D.png` Alpha 真实身份 = 原生眼睛/光学器件发光遮罩**：原画师已把眼部/护目镜透光掩码埋在漫反射 Alpha 通道里！

### 4.2 双眼精准点亮与严防“误亮额头”

* **血案复盘**：Swoop 早期曾凭经验手写 UV 盒 `[888..965, 648..674]` 点亮发光遮罩，结果游戏内双眼乌黑，**前额头盔眉骨却亮起一大块蓝灯**——实测真正的人形眼缝位于 `[948..992, 638..652]`，翼龙眼位于 `[600..666, 5..34]`！横炮（Sideswipe）真瞳孔更是仅有 `4×5` 像素（`[1748..1753, 744..748]` 与 `[1748..1753, 828..832]`）。
* **标准核验流程**：
  1. 用脚本提取 `Tx_*_D.png` 的 Alpha 非零独立像素连通域（ROI）；
  2. 在 Blender 中直接选取头部眼眶对应三角面，回查真实 UV 坐标区间并交叉核对；
  3. 只对真眼核心像素赋值 `RAOE.B = 200~255`，**面部其余区域 `RAOE.B` 严格清零**。

### 4.3 拒绝灰模过曝：对齐官方钢锁（`grimlock_gs_mp08`）金属质感基线

| 参数项 | ❌ 典型过曝错调 | ✅ 官方 Grimlock 实测标尺 / Swoop 校准值 | 实际观感差异 |
| :--- | :--- | :--- | :--- |
| **`_Color` / `_base_col`** | `0.95` / `1.0` | `_Color ≈ 0.255~0.65`，`_base_col ≈ 0.50~0.56` | 过曝写法把车身洗成发白塑料/灰模；收敛标尺保留重金属反差 |
| **`_roughness_range` / 清漆** | 偏低或无清漆 | `_roughness_range = 1.0`，`_clearcoat_reflectance_range = 0.10` | 恢复装甲清漆光泽与高光边缘锐度 |
| **`NM.B`（金属度）/ `RAOE.R`** | 金属低、粗糙高 | `NM.B ≈ 143~214`（Swoop 取 `~150`），`RAOE.R ≈ 59~69` | 抑制粉质哑光感，体现战损金属冷冽质感 |
| **`RAOE.G`（AO）/ 色彩增强** | 全局无脑线性提亮 | `RAOE.G ≈ 197`（深缝压暗），HSV 饱和度增 `~1.45x` | **严禁拉高暗部缝隙亮度**，确保机械黑缝深沉、彩漆鲜艳饱和 |

### 4.4 单材质单色物理限制、双 SubMesh 拆分与 `Symbol_AB` 胸标四铁律

* **着色器物理限制**：Kabam `EB/Character/PBR` 的自发光公式为：
  $$\text{Emissive} = (\text{RAOE.B})^2 \times (\text{\_emissive\_intensity\_col.rgb})^2 \times \text{Overbright}$$
  `_emissive_intensity_col` 是材质级全局统一变量（Uniform Vector4），**单个 Material 实例在数学上绝对无法同时发出蓝光（眼）和红光（胸口阵营标/车灯）**！
* **双 SubMesh / 双材质槽物理分离架构**（源自 Sideswipe `§11.19.6` & Swoop 实战）：
  1. **网格分槽**：全机身与蓝眼保留在 `SubMesh 0`（绑定主材质 `MAT_ROBOT_PID`，`_emissive_intensity_col = (0.04, 0.52, 1.0, 0.0)`，`Overbright ≈ 18.0`）；单独将胸口 `Symbol_AB` 红标面（或透光车灯/腔体底面）拆为 **`SubMesh 1`**。
  2. **借用闲置同 Shader 材质槽**：从供体包中挑一个同 Shader 的闲置材质（如 `MAT_EMBLEM_PID` 或 `MAT_WEAPON_PID`），写入 `m_Materials[1]`（Main 与 `_lw` 双 Prefab 同步写入），设定**纯深红 `_emissive_intensity_col = (1.0, 0.0, 0.0, 0.0)`** 并**压低 `Overbright ≈ 9.0`**。
     * **🚨 防粉红铁律**：红标若把 `Overbright` 设成 `22~24` 且漫反射泛白，经移动端 ACES HDR 色调映射后会严重发粉变成“粉红标志”！压低至 `9.0` 配合纯红通道即可发透正红！
  3. **🚨 `Symbol_AB` `UVMap` vs `UV0` 合并黑底巨坑**：Blender 给 `Symbol_AB` 新建默认 `"UVMap"` 后若 `join()` 进主网，而主网 UV 层叫 **`"UV0"`**，两组 UV 不会合并，`Symbol_AB` 会落进 UV1（着色器不读），进游戏直接采样 `(0,0)` 黑点！**合并前必须把 `Symbol_AB` 的 UV 层重命名为与主网 100% 同名（如 `"UV0"`）**！
  4. **防 Z-Fighting 抬出**：`Symbol_AB` 红标贴片必须沿胸甲外法线（如 `-Y`）微抬出 **`0.025~0.037m`**，且黑底垫片保留在枪灰主材质槽（`SubMesh 0`），彻底根治凹槽黑色多边形遮挡或闪烁（车灯类腔体同步见 `§11.19.6`）。

---

## 5. 自带变形动画提取、载具尺寸对齐与跨供体引用铁律

### 5.1 提取原生拍翅/载具循环动作与战机骨架映射

* **提取原则**：对于 Swoop 这类自带 `vehicle_idle01` 循环动画（58 帧、双振翅周期）的模具，先用 `§1.3` 的 FBX 原始 `Lcl Scaling` 逆解算法恢复无畸变局部旋转，再按解剖对应关系重映射到借壳战机 `COG` 子骨链（例如内翼/外翼/翼尖导弹分别绑定对称翅膀骨，且内-外翼过渡带使用 **50/50 线性渐变权重**消除向下扑动时的折角黑线）。
* **注入状态机**：导出 Unity `AnimationClip` 覆盖战机 `Jet/Car AOC` 对应飞行槽位（如槽位 `[5, 12, 16]`），所有曲线路径必须保留母体 `ORIGINAL` 骨架路径前缀并匹配 `m_BoneNameHashes`。

### 5.2 载具真实比例对齐（不破 `BindPose` 的安全缩放法）

* **先对参照物再定倍率**：导入后切勿想当然沿用 `1.0x` 载具比例！必须在 Blender/Unity 中对比**同个零部件在人形与载具上的绝对长度**（例如 Swoop 双肩与翼龙双翼挂载的是同一对导弹仓，经实测对比需要 `4.866 / 3.169 ≈ 1.53x` 才匹配，否则翼龙形态整体显小一圈）。
* **安全等比放大技法**：先核查目标 `AOC` 中是否有动画曲线写入 `Reference` 节点的缩放属性；确认无曲线覆盖后，直接在注入阶段修改 Main 与 `_lw` 双 Prefab 下 **`transformed/Reference` Transform 的 `m_LocalScale`**（如 `(1.53, 1.53, 1.53)`）。这样既能让整只载具按理想倍率完美等比放大，又完全不触碰任何骨架 `BindPose` 与 `TransformedStateScaleEvent`！

### 5.3 动作高度借用、实测发射点与 `m_FileID` 跨供体铁律

1. **禁止“只改发射不看动作高度”**：借用钢锁火球（`grimlock_fireball`）绝不等于借用钢锁贴地喷火动作！Swoop 等飞行类重击应借用红蜘蛛空中悬停动作（`StarScream_Normal_attackHeavy`），在战机悬空高度变形为翼龙后吐火球。
2. **禁止凭脑补硬写投射物 `po` 偏移**：如果在游戏内发现火球从身体下方很远窜出而非从嘴巴吐出，根本原因是 `po` 偏移未按实机缩放与动作帧姿态算准。
   * **唯一正解**：在 Unity 无头场景中加载目标 Heavy 动画 Clip，于实际发射帧（如 `f=11/12`）调用 `BakeMesh()` **直接读取变形嘴尖/炮口顶点（`BeakMouth`）的世界/根节点坐标**（例如 Swoop 在 `patch_swoop_heavy_move.py` 中据此把火球 `po` 修正为 **`(0.0, 11.4, 2.8)`**），一针见血锁死发射点！
3. **🚨 `m_FileID` 跨供体逐包核查铁律（重击载具隐形头号元凶）**：
   * **绝对禁止把 A 供体的外部文件 `m_FileID` 硬编码复制到 B 供体脚本中！**
   * **血案实录**：外部共享动画包 `character_anim_procedural.assetbundle` 在 Skywarp / Starscream 的依赖表里是 **`m_FileID = 3`**；但在 **Ramjet** 中，**`m_FileID = 3` 指向的是 `character_fx`**，真正的 `character_anim_procedural` 位于 **`m_FileID = 5`**！把 `FileID=3` 填进 Ramjet 供体包会使重击动作片段静默加载失败，表现为“飞标重击能出火球，但翼龙身体完全消失”！
   * **铁律**：编写 `generate_<bot>_bundle.py` 前，必用脚本打印供体 `env.file.files` 中 `externals` 列表，逐条确认每个 `.assetbundle` 对应的真实 `m_FileID`。
4. **SP3 Matinee 节点命名契约**：若移植角色后续适配自定义/借用 SP3，必须保留供体 Prefab 原生 `cha_<donor>_00` / `cha_<donor>_01` 层级与命名约定以防过场动画脱靶（详见 [`THIRD_PARTY_3D_MODEL_PIPELINE.md §11.17`](file:///e:/Agent/TFTF-blender/re_notes/THIRD_PARTY_3D_MODEL_PIPELINE.md#L1254-L1283) 与 [`SP3_WHITEBOX_NATIVE_MATINEE_ARCHITECTURE.md`](file:///e:/Agent/TFTF-blender/re_notes/SP3_WHITEBOX_NATIVE_MATINEE_ARCHITECTURE.md)）。

---

## 6. 标准作业流程与 Alliance 专属验收红线（Fail-Fast Checklist）

### 6.1 四阶段命令式机械门禁

复制并改造 `tools/starsaber/` 或 `tools/swoop/` 后，每完成一步必须立即运行 [`tools/validate_port_gates.py`](file:///e:/Agent/TFTF-blender/tools/validate_port_gates.py)：

```powershell
$env:PYTHONIOENCODING="utf-8"
python tools\validate_port_gates.py tex    --tex-dir 3rd-party-models\<Bot>\02_textures
python tools\validate_port_gates.py fbx    --fbx-dir 3rd-party-models\<Bot>\03_fbx
python tools\validate_port_gates.py mesh   --bundle toolchain\unity_build_project\AssetBundles\<bot>_mesh.assetbundle
python tools\validate_port_gates.py bundle --bundle assets_redeco\<bot>.assetbundle --bot <bot_id>
```

> 若使用独立强化校验（如 [`validate_swoop_bundle.py`](file:///e:/Agent/TFTF-blender/tools/swoop/validate_swoop_bundle.py)），同步核查 **所有引用 Clip `m_FileID` 有效性**、`m_PreloadTable` 闭合、`script_types` 严格升序、`moves.assetbundle >= 945` 与服务端蓝图/头像资产对齐。

### 6.2 Alliance 专属 6 项视觉红线（Agent 必须用读图工具逐项核验后才能交付）

- [ ] **红线 1（正反朝向）**：人形胸甲、面部确定面向 `+Z` 正前方，翅膀/背包在 `-Z` 背后。
- [ ] **红线 2（三指与武器微距）**：左/右拳同框特写下双侧大拇指均自然向掌心收拢（绝无右手大拇指外翻指向大腿）；若持剑/枪，确认剑柄深入掌心且刃向旋转 `+90°` 正确、枪械 `PropsController` 与 `LeftHand` 无浮空穿模。
- [ ] **红线 3（双眼 ROI 与防误亮额头）**：近景头部确认发光像素精准落在双目眼眶，**额头/眉骨零蓝块误亮**。
- [ ] **红线 4（`Symbol_AB` 双色分层与防粉红）**：胸口 `Symbol_AB` `UV0` 与主网合并正常、无黑底或 Z-Fighting 闪烁；`SubMesh 1` 使用压低后的 `Overbright ≈ 9` 发出纯正红光，未过曝成粉红色。
- [ ] **红线 5（Grimlock 级金属质感）**：与官方 `grimlock_gs_mp08` 并排对比，呈厚重饱和的金属漆光泽，绝无发白灰模过曝感，黑色机械沟壑对比鲜明。
- [ ] **红线 6（载具尺度与发射口实测）**：载具共件（如双侧导弹）比例与人形协调（如 `1.53x` 对齐）；重击演示帧确认载具实体正常显现（`m_FileID` 正确）、空中悬停高度正确、火球/弹道从实测嘴尖/炮口顶点正中喷出。
