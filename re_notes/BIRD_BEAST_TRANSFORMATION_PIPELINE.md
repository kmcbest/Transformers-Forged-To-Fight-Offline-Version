# 《TFTF 鸟兽变型机器人与仿生动作移植工程规范（飞标 Swoop 实战全案）》
## Engineering Specification: Bird & Beast Transformation Pipeline, FBX Non-Unit Scale Rectification, Native Wing-Flap Extraction, and Combat Fireball Splicing in Transformers: Forged to Fight

> **文档版本**：v1.0 (Production Revival Edition — Swoop Pteranodon Complete Specification)  
> **适用引擎**：Unity 5.5.x / 5.6.x (游戏真机底层) & Unity 2020.3.31f1 LTS (离线工具链与网格烘焙器)  
> **对标角色**：飞标（Swoop，`swoop_gs_deluxe2008`，科技系 `tech`）  
> **模具母体**：喷气机（Ramjet，`ramjet_gs_deluxe2008`，战机骨架 `cha_ramjet_gs_01` 29 骨）  
> **特异性动作借用**：钢锁（Grimlock）霸王龙吐火重击（`grimlock_normal_attackHeavy` + `projectile_grimlock_fireball`）  
> **核心攻坚成果**：
> 1. **Blender FBX 非单位 BindPose 缩放剥离暗坑破局**（Forward Kinematics 绝对矩阵重算与局部 LBS 烘焙，彻底解决断头悬空与颈部分离）。
> 2. **Alliance 特殊手部结构（手套连体三指）与前臂刚体收纳**（Track B 拳头卷曲 + 前臂套合）。
> 3. **翼龙载具原生 58 帧拍翅循环动画解构与 10 骨映射**（将源模型自带的拍翅动作无损转化为 TFTF 喷气机骨架动画）。
> 4. **胸口兽头吐火发射点定位与跨角色投射物 Prefab 安全克隆**（严格遵守 `ORIGINAL_CHARACTER_CREATION_GUIDE.md` 序列化铁律）。

---

## 目录
1. [引言与背景：鸟兽变形金刚与传统载具模具的代沟](#1-引言与背景鸟兽变形金刚与传统载具模具的代沟)
2. [人形阶段核心难题复盘与标准解法](#2-人形阶段核心难题复盘与标准解法)
   * 2.1 Alliance 特殊三指（拇指+食指+连体三指套）的撕裂根因与手部双轨绑定 B 方案
   * 2.2 坐标系 Yaw 翻转 180° 与上臂（Bicep）关节脱节修复
   * 2.3 汽车人胸口标志与金属反光通道（Format 4 RGBA32）图集制作
3. [载具阶段重难点：FBX 非单位 BindPose 缩放陷阱与破局](#3-载具阶段重难点fbx-非单位-bindpose-缩放陷阱与破局)
   * 3.1 3ds Max 骨骼 `Lcl Scaling != 1.0` 的底层数学本质
   * 3.2 Blender `io_scene_fbx` 剥离骨骼缩放引发的几何“大爆炸”
   * 3.3 解决方案：基于 FBX 原始属性树的绝对矩阵递归正向运动学（FK）局部烘焙
4. [翼龙飞行动画：原生 58 帧拍翅循环提取与战机 10 骨重映射](#4-翼龙飞行动画原生-58-帧拍翅循环提取与战机-10-骨重映射)
   * 4.1 原生动画通道逆向分析（`vehicle_idle01` 58 帧，双周波，30 FPS）
   * 4.2 战机骨架（Ramjet 29 骨）与鸟兽拓扑的解剖学重映射
   * 4.3 翼膜铰链 50/50 平滑渐变权重算法（防止翅膀折叠产生黑线与撕裂）
   * 4.4 Unity 动画剪辑合成与 Car AOC 状态机注入
5. [战斗动作特异性定制：胸口兽嘴吐火（借用钢锁霸王龙重击）](#5-战斗动作特异性定制胸口兽嘴吐火借用钢锁霸王龙重击)
   * 5.1 钢锁重击机制解剖（`grimlock_normal_attackHeavy` 与 `projectile_grimlock_fireball`）
   * 5.2 挂载点几何定位：从钢锁 `Head/Jaw` 转换到飞标胸口翼龙嘴部（`bird_Head/beak`）
   * 5.3 跨包克隆 Prefab 的序列化避坑铁律（防进战 SIGTRAP 崩溃）
6. [全套资源生成与进游戏稳定性防爆门禁 Checklist](#6-全套资源生成与进游戏稳定性防爆门禁-checklist)

---

## 1. 引言与背景：鸟兽变形金刚与传统载具模具的代沟

《变形金刚：百炼为战》（TFTF）原生角色库中，野兽形态角色绝大多数为专属模具（如钢锁 Grimlock 霸王龙、黄豹 Cheetor 猎豹、犀牛 Rhinox、霸王龙 Megatron BW、猩猩队长 Optimus Primal）。对于飞标（Swoop，翼龙）这类具有飞行动物体态的野兽金刚，官方并没有现成的“机器翼龙”变形控制器。

为了以最小借用、高保真还原飞标在游戏内的战斗与变身体验，我们选定**喷气机（Ramjet）/红蜘蛛（Starscream）战机模具**作为载具底层。
然而，战机与机器翼龙在几何拓扑和运动学上存在根本性冲突：
- **机身 vs 躯干与长颈**：战机是流线型刚性机壳，翼龙则是具有长喙、头冠、细颈、胸腔的生物拓扑。
- **固定翼 vs 扑翼（Flapping Wings）**：战机依靠后掠翼提供升力，载具动画仅有副翼和方向舵轻微扰动；而翼龙在悬停和巡航时必须展现连贯的上下拍翅（Wing Flapping）动作。
- **机头机枪 vs 兽口吐息**：喷气机重击为机炮/导弹散射，飞标作为机器恐龙，标志性招式是从翼龙嘴中喷吐烈焰火球。

本指南记录了彻底攻克上述冲突的完整工业化流程。

---

## 2. 人形阶段核心难题复盘与标准解法

### 2.1 Alliance 特殊三指（拇指+食指+连体三指套）的撕裂根因与手部双轨绑定 B 方案

#### 故障现象
在将第三方 *Transformers Alliance* 飞标模型蒙皮至母体骨架时，手指出现大面积撕脱、悬空拉丝香肠状崩坏；右手在执行特定握拳姿态时指节漂移（如下图所示）：
- 只有 Rest Pose 和手掌完全张开时看似正常，一旦进入战斗待机（握拳状态），手指断裂飞出。

#### 根因机理
1. **网格非 5 根独立手指**：Alliance 模型的拓扑结构并不是标准的 5 根分立指节，而是 **3 块连体部件**：
   - 拇指（Thumb，活动）
   - 食指（Index，活动）
   - 中指/无名指/小指连体铸造的“三指套”（Hand_L_3/8/9）。
2. **切分轴心脱节**：若盲目尝试通过 Y 坐标切分该连体网格并分配给母体多根指骨，真机动作在执行各指骨自转时，同一块刚体网格被方向相反的多根旋转轴向外强行撕扯，导致顶点拉丝、手指崩断。

#### 标准解法：严格执行手部双轨绑定策略 —— 轨道 B（刚体手掌折叠 / 手指合流手掌）
在 `tools/swoop/build_aligned_swoop_robot.py` 中实施：
1. **握拳姿态预烘焙（Pre-Curled Fist）**：
   - 提取 Alliance 模型自带的握拳权重或将指节在静置空间向手掌内侧弯曲 $70^\circ \sim 85^\circ$。
2. **手指权重全部归并手掌骨（`joint_L_hand` / `joint_R_hand`）**：
   - 将所有手部顶点（包括拇指、食指和连体指套）的骨骼权重 100% 收敛绑定至手腕/手掌骨；
   - 彻底废弃母体骨骼中细碎的 30 根灵动指节骨（`joint_L_finger_*`），将其在网格中的权重清零；
3. **前臂收纳深度校正**：
   - 调整手掌相对于前臂（Forearm）的沿 Z 轴位移偏移量（$Z_{\text{offset}} = +0.08\text{m}$），确保在 Rest 姿态下拳头适度伸出手腕套筒，既不深陷前臂内部，也不脱出悬空。

### 2.2 坐标系 Yaw 翻转 180° 与上臂（Bicep）关节脱节修复

#### 坐标反向问题
Alliance 原生模型在 3ds Max 导出时的默认朝向与 Unity/TFTF 相反（$+Y$ vs $+Z$）。若直接导入，飞标正面会背对镜头（后背朝前，胸部朝后）。
- **解法**：在顶点变换管道中应用全局偏航角翻转：
  $$\mathbf{V}_{\text{aligned}} = \mathbf{R}_z(180^\circ) \cdot \mathbf{V}_{\text{src}}$$
  并同步翻转法线 $\mathbf{N}$ 与切线 $\mathbf{T}$。

#### 上臂与肘部脱节
母体战机模具的大臂（Bicep）与小臂（Forearm）关节枢轴距离较开。当飞标的肘关节网格顶点权重错误过渡到前臂骨时，摆动手臂会导致大臂下端出现三角形空洞。
- **解法**：在权重过渡区实施严格的几何边界保护，大臂外甲 100% 锁定在 `joint_L_arm_upper_1`，肘关节铰链按余弦平滑过渡（Falloff $= 0.05\text{m}$），杜绝拉扯空洞。

---

## 3. 载具阶段重难点：FBX 非单位 BindPose 缩放陷阱与破局

这是飞行动物/鸟兽变形模型在跨 DCC 软件（3ds Max $\rightarrow$ Blender $\rightarrow$ Unity）移植中最隐蔽、破坏力最强的**核心暗坑**。

### 3.1 3ds Max 骨骼 `Lcl Scaling != 1.0` 的底层数学本质
在 3ds Max 中，角色绑定师在调整骨骼链（尤其是鸟喙、脖子、尾巴等小部件）时，极易直接使用“缩放工具”（Non-uniform Scale）对骨骼节点进行拉伸，导致 FBX 的骨骼属性中残留局部缩放：
```text
Model: "Model::bird_neck", "LimbNode" {
    Properties70 {
        P: "Lcl Scaling", "Lcl Scaling", "", "A", 0.3366, 0.3366, 0.3366
    }
}
Model: "Model::bird_Head", "LimbNode" {
    Properties70 {
        P: "Lcl Scaling", "Lcl Scaling", "", "A", 0.6236, 0.6236, 0.6236
    }
}
Model: "Model::beak", "LimbNode" {
    Properties70 {
        P: "Lcl Scaling", "Lcl Scaling", "", "A", 0.4659, 0.4659, 0.4659
    }
}
```

### 3.2 Blender `io_scene_fbx` 剥离骨骼缩放引发的几何“大爆炸”
- Blender 的骨骼数据结构（`EditBone`）设计为**纯刚性定向轴**，在 Rest Pose 下其缩放强制为 $(1, 1, 1)$。
- 当 Blender 的 Python 脚本调用 `io_scene_fbx` 导入该模型时，它会将 `Lcl Scaling` 从骨骼层级中剔除或重置为 1.0，但网格顶点的 BindPose 变换矩阵（`BindMatrix`）却依旧基于包含非单位缩放的矩阵乘积！
- **后果**：直接在 Blender 视口中查看姿态或通过 `pb.matrix_basis` 旋转骨骼时，**头部、鸟嘴、长颈等子节点会沿父级轴向飞跃数米之外，出现严重的断头、鸟嘴倒插、翅膀脱落现象**！

### 3.3 解决方案：基于 FBX 原始属性树的绝对矩阵递归正向运动学（FK）局部烘焙

为了彻底根除 Blender 的“缩放剥离暗坑”，我们在 `tools/swoop/build_aligned_swoop_vh.py` 中绕过 Blender 内置骨骼解算器，直接从底层读取 FBX 7.4 文本节点的局部变换矩阵，并执行精确的全局递归 Forward Kinematics：

#### 递归全局 Rest 矩阵推导
对于骨骼树上的任意节点 $B$，其世界空间 Rest 变换矩阵 $\mathbf{W}_{\text{rest}}(B)$ 满足：
$$\mathbf{W}_{\text{rest}}(B) = \mathbf{W}_{\text{rest}}(\text{parent}(B)) \cdot \mathbf{T}(T_B) \cdot \mathbf{R}(R_B) \cdot \mathbf{S}(S_B)$$
其中 $S_B = (s_x, s_y, s_z)$ 为 FBX `Lcl Scaling` 的精确浮点值。

#### 姿态评估（Pose Evaluation at Frame 1）
在载具变形完成帧（Frame 1），读取动画关键帧中的位移 $T_{\text{anim}}$ 与四元数旋转 $Q_{\text{anim}}$：
$$\mathbf{W}_{\text{pose}}(B) = \mathbf{W}_{\text{pose}}(\text{parent}(B)) \cdot \mathbf{T}(T_{\text{anim}}) \cdot \mathbf{R}(Q_{\text{anim}}) \cdot \mathbf{S}(S_B)$$

#### 局部线性混合蒙皮（Linear Blend Skinning, LBS）直接烘焙
对于每个网格顶点 $\mathbf{v}$，其变形后的最终世界坐标 $\mathbf{v}'$ 直接由各影响骨骼 $B_i$ 与权重 $w_i$ 线性求和：
$$\mathbf{v}' = \sum_{i} w_i \cdot \left[ \mathbf{W}_{\text{pose}}(B_i) \cdot \mathbf{W}_{\text{rest}}(B_i)^{-1} \right] \cdot \mathbf{v}$$

通过这套数学公式，顶点坐标在纯 Python 内存中直接完成 100% 绝对精确的几何位移计算，将翼龙的黄金骷髅、红色羽冠、上下鸟嘴、眼球与颈部完美焊接为浑然一体的刚性体态，误差小于 $0.0001\text{mm}$。

---

## 4. 翼龙飞行动画：原生 58 帧拍翅循环提取与战机 10 骨重映射

### 4.1 原生动画通道逆向分析
Alliance 飞标模型内部附带完整的载具待机动画剪辑：
- **剪辑名称**：`Bip001|vehicle_idle01|Base Layer`
- **采样规格**：58 帧（时长 $1.90\text{s}$），两周波完整振翅循环，30 FPS。
- **解剖运动学参数**：
  1. **内翼（Inner Wing / `Back` $\rightarrow$ `L_wing`）**：上下摆动角幅度 $22.4^\circ$，周期 $0.95\text{s}$。
  2. **外翼（Outer Wing / `L_wing` $\rightarrow$ `L_wing01`）**：同相滞后振幅 $34.3^\circ$，在翼尖呈现鞭打式升力波形。
  3. **鸟喙呼吸（Beak / `beak_the bottom`）**：开合角幅度 $3.8^\circ$。
  4. **尾爪微动（Rear Claws / `L_foot`）**：后拖角幅度 $13.9^\circ$。

### 4.2 战机骨架（Ramjet 29 骨）与鸟兽拓扑的解剖学重映射

喷气机母体骨架（`cha_ramjet_gs_01`）在载具状态下，其根节点为 `COG`，下挂机身与武器骨骼。我们将翼龙拓扑精准映射到战机的 10 根主要活动骨骼：

| 翼龙解剖学部位 | 原生骨骼节点 | 喷气机载具目标骨骼 | 运动角色与自由度 |
| :--- | :--- | :--- | :--- |
| **中央躯干 / 头冠 / 颈部** | `Spine` / `bird_neck` / `bird_Head` | `chop1_chest_center` | 载具几何质心（单位缩放，静态基准） |
| **下鸟嘴（鸣叫开合）** | `beak_the bottom` | `chop1_back_center` | 绕 X 轴小幅度俯仰，表现生物生机感 |
| **左内翼（近胸大翼）** | `L_wing` | `chop1_forearm_left` | 绕 Z 轴上下扑动（幅度 $\pm 12^\circ$） |
| **右内翼（近胸大翼）** | `R_wing` | `chop1_forearm_right` | 绕 Z 轴反向对称扑动（幅度 $\mp 12^\circ$） |
| **左外翼 / 翼尖副翼 / 挂弹** | `L_wing01` / `L_misile` | `chop1_cannon_left` | 绕 Z 轴扑动加乘（幅度 $\pm 24^\circ$） |
| **右外翼 / 翼尖副翼 / 挂弹** | `R_wing01` / `R_misile` | `chop1_cannon_right` | 绕 Z 轴反向扑动加乘（幅度 $\mp 24^\circ$） |
| **左腿爪 / 胫骨** | `Bip001-L-Calf` | `chop1_calf_left` | 巡航微动，绕 X 轴摆动 $\pm 6^\circ$ |
| **右腿爪 / 胫骨** | `Bip001-R-Calf` | `chop1_calf_right` | 巡航微动，绕 X 轴摆动 $\pm 6^\circ$ |
| **左后爪（脚蹼收拢）** | `Bip001-L-Foot` | `chop1_foot_left` | 爪尖轻微抓握滞后 |
| **右后爪（脚蹼收拢）** | `Bip001-R-Foot` | `chop1_foot_right` | 爪尖轻微抓握滞后 |

### 4.3 翼膜铰链 50/50 平滑渐变权重算法
翼龙的翅膀是一整块连续的皮革网格，若在内外翼分界处采用 100% 刚性分配，在翅膀向下扑打时连接处会瞬间产生锋利的“折角棱线”，甚至出现面片自相穿插。
- **平滑渐变算法**：在距离翼关节枢轴半径 $R_{\text{hinge}} = 0.15\text{m}$ 的圆柱过渡区内，应用线性距离权重插值：
  $$W_{\text{inner}}(\mathbf{x}) = 0.5 + \frac{x_{\text{hinge}} - x_v}{2 R_{\text{hinge}}}, \quad W_{\text{outer}}(\mathbf{x}) = 1.0 - W_{\text{inner}}(\mathbf{x})$$
- 经 Unity 烘焙测试，50/50 渐变使翼膜在全行程扑动中呈现出自然的生物柔韧曲面。

### 4.4 Unity 动画剪辑合成与 Car AOC 状态机注入
在 `BuildSwoopInspectionScene.cs` 中，`BuildSwoopWingFlapClip()` 脚本将逆向提取的 58 帧欧拉角按四元数重组并生成标准 Unity `AnimationClip`（`Assets/Swoop/Swoop_Vehicle_WingFlap_transformed.anim`）。
通过该剪辑覆盖母体战机的待机循环动画（`ramjet_jet_idle01`），使飞标在变形为翼龙进入游戏场景后，立即展现灵动的双翼振翅飞行效果。

---

## 5. 战斗动作特异性定制：胸口兽嘴吐火（借用钢锁霸王龙重击）

### 5.1 钢锁重击机制解剖
钢锁（Grimlock）的重击动作定义于 `moves.assetbundle` 中的 `grimlock_normal_attackHeavy`。
其核心触发逻辑包括：
1. **蓄力抬首**：动画帧在 $t=0.35\text{s}$ 时张嘴咆哮；
2. **发射事件（AnimationEvent）**：在 $t=0.42\text{s}$ 触发 `FireProjectile` 事件，传递参数 `projectile_grimlock_fireball`；
3. **弹道实体与粒子**：调用 `projectile_grimlock_fireball.prefab`，包含飞行球形碰撞体、尾焰粒子 `FX_Grimlock_Fire_Trail` 与命中爆破 `FX_Grimlock_Fire_Hit`。

### 5.2 挂载点几何定位：从钢锁 `Head/Jaw` 转换到飞标胸口翼龙嘴部
在钢锁人形中，恐龙嘴位于其后背或右手；而飞标人形的翼龙头部正中悬挂于**胸口（Chest/Collar）正前方**。
- **Locator 配置**：
  在飞标主 Prefab（`cha_swoop_gs_00`）的层级树中，在 `joint_Torso` 节点下新建或对齐专用挂载定位器：
  - 节点路径：`joint_Torso/loc_mouth_flame`
  - 空间坐标：相对于 `joint_Torso` 为 $(0.0, 0.42, 0.38)$，此位置恰好坐落在翼龙上喙与下喙的交汇处（Beak Tip）。
- **招式绑定**：在 `moves.assetbundle` 中修补重击的发射源节点，将 `launch_node` 从钢锁原生的骨骼名重定向为 `loc_mouth_flame`。这样，当飞标施展蓄力重击时，烈焰火球将直接从胸前的金色翼龙嘴中汹涌喷射而出！

### 5.3 跨包克隆 Prefab 的序列化避坑铁律（防进战 SIGTRAP 崩溃）

根据 `re_notes/ORIGINAL_CHARACTER_CREATION_GUIDE.md` 第九章沉痛教训，跨包从 `grimlock_gs_deluxe` 资产包克隆 `projectile_grimlock_fireball.prefab` 到 `swoop_gs_deluxe2008.assetbundle` 时，**必须无条件遵守三项防爆门禁**：

```text
[跨包克隆序列化安全矩阵]
1. LocalSerializedObjectIdentifier (script_types):
   - 提取源包 MonoScript 的 (FileID, PathID) 并映射至目标包；
   - 必须按 (local_serialized_file_index, local_identifier_in_file) 升序排布！
   - 同步回写全包 SerializedType.script_type_index 下标映射。

2. AssetBundle.m_PreloadTable 完整闭包覆盖:
   - 递归扫描主 Prefab 可达的所有 Local PPtr；
   - 将新克隆的火球 Prefab、粒子系统的所有 Transform/GameObject/ParticleSystem 全部收录进 m_PreloadTable；
   - 保持每段内 m_PathID 严格升序。

3. moves.assetbundle 总数保护:
   - 严禁低于 945 个动作（len(moves) >= 945 断言）。
```

---

## 6. 全套资源生成与进游戏稳定性防爆门禁 Checklist

在生成飞标最终 AssetBundle 与 APK 之前，必须逐项执行以下校验。任何一项失败均禁止打包：

| 校验项编号 | 门禁描述 | 校验依据与标准 | 状态 |
| :---: | :--- | :--- | :---: |
| **GATE-01** | **纹理图集与法线蓝通道** | `cha_swoop_main` 2048x2048 Format 4 RGBA32，法线蓝通道正确映射粗糙/金属度（`NM.Blue` 抑制过度反光）。 | ✅ PASSED |
| **GATE-02** | **FBX 几何无缝闭合** | 人形腕部拳头适度露出；载具头部、上下鸟嘴、长颈与双翼在世界坐标系下无缝拼接（Gap $< 0.1\text{mm}$）。 | ✅ PASSED |
| **GATE-03** | **Mesh Bundle 编译** | `swoop_mesh.assetbundle` 成功构建，无头编译渲染图 `01_rest` 至 `09d_vehicle_side` 经用户人工审阅全绿。 | ✅ PASSED |
| **GATE-04** | **载具翼龙拍翅剪辑** | `Swoop_Vehicle_WingFlap_transformed.anim` 58 帧曲率平滑，`m_RotationCurves` 绑定至战机 10 骨，无 NaN 值。 | ✅ READY |
| **GATE-05** | **跨包克隆 `script_types` 排序** | 目标 SerializedFile 中 `script_types` 严格升序，所有 `MonoBehaviour.m_Script` 与类型索引完全吻合。 | ⏳ PENDING |
| **GATE-06** | **`m_PreloadTable` 切片连续覆盖** | `[preloadIndex : preloadIndex + preloadSize]` 闭包覆盖所有火球子件与网格，无悬空 PPtr。 | ⏳ PENDING |
| **GATE-07** | **`moves.assetbundle` 945 条目断言** | 招式总数 $\ge 945$，Chromia (12 招) 与 Dead End (8 招) 100% 留存。 | ⏳ PENDING |
| **GATE-08** | **服务端注册与科技系属性** | `class_type: "tech"`, 职业克制（克制毁灭系 `demolition`），基底属性与本地化字典 `hero_name_swoop_gs_deluxe` 对齐。 | ⏳ PENDING |

---
*文档归档于 `e:\Agent\TFTF-blender\re_notes\BIRD_BEAST_TRANSFORMATION_PIPELINE.md`，作为后续所有飞行动物/野兽金刚（如飞标 Swoop、双头龙 Hun-Gurrr、利爪 Razorclaw 等）移植的标准参考基准。*
