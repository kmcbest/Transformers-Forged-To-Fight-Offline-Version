# TFTF 战斗场景动态模型嫁接与背景演绎技术指南
# (Battle Stage Dynamic Model Integration & Background Animation Specification)

本文档系统性总结了《变形金刚：百炼为战》（Transformers: Forged to Fight）离线重构版本中，**在既有战斗场景（Stage / Arena）中添加全新外部 3D 动态模型、绑定背景循环动画、调教动态 PBR 着色器以及规避 AssetBundle 底层陷阱的全套端到端工业化流程**。涵盖“生锈荒海（Rust Sea）6车合体大力神”与“卡纳克沙漠（Karnak Desert）修罗王 vs 凯旋女神双巨像对峙”两套经典实战案例。

---

## 一、 核心架构与技术挑战

在 TFTF 场景中植入外部高复杂度动态资产（如 6 车合体大力神 Devastator、修罗王 Volcanicus、凯旋女神 Victorion），存在跨引擎与底层打包层面的数个致命技术壁垒：

```
[外部 3D 模具与动作 FBX] ──▶ [Unity 2020.3.31f1 独立舞台工程]
                                            │ (导出舞台临时 AssetBundle)
                                            ▼
[原版 Stage assetbundle] ◀─── [merge_and_patch_*.py] (TypeTree & 层次合并)
 (rust_merged / karnak_merged)              │
                                            ▼
                               ┌────────────┴────────────┐
                               ▼                         ▼
                  [动态角色 PBR 着色器注入]       [resS 纹理流单轨归一化]
                  [材质光照与粉红超新星防御]       [Mecanim 纯净循环防畸变]
                  [战斗围栏避让与沙丘贴地标定]     [双机视线聚焦与等高配比]
                               │
                               ▼
            [assets_redeco/*_merged.assetbundle]
                               │
                               ▼
        [Server/build_phone_apk.py] (TOC CRC=0 & 文件大小动态重写)
                               │
                               ▼
                 [Android 离线 APK 100% 稳定运行]
```

---

## 二、 场景工程搭建与资产规范

### 1. 物理隔离的独立 Unity 舞台工程
* **严禁污染角色主工程**：场景环境与 3D 角色存在完全不同的渲染管线、Layer 层级与光照探针体系。必须在独立目录（如 `stage_project/`）搭建 Unity 2020.3.31f1 工程。
* **工程忽略规范**：
  在 `.gitignore` 中必须严格忽略 Unity 生成的临时和构建缓存目录，避免数百兆冗余文件入库：
  ```gitignore
  stage_project/[Ll]ibrary/
  stage_project/[Tt]emp/
  stage_project/[Oo]bj/
  stage_project/[Bb]uild/
  stage_project/[Bb]uilds/
  stage_project/[Ll]ogs/
  stage_project/[Uu]ser[Ss]ettings/
  stage_project/AssetBundles/
  stage_project/*.log
  stage_project_assets/
  ```

### 2. 外部模型导入与层级分配规范
* **场景背景图层（Layer 11）**：
  * TFTF 的场景相机视锥体划分极严。战斗双方英雄位于 Layer 8/9，场景背景几何体必须分配在 **Layer 11 (`Stage Background Geometry`)**。
  * 导入的根节点及其所有子物体（包括骨骼 Transform、Mesh、Collider 等 100+ 节点）必须递归设置为 Layer 11，否则会被场景主摄像机 CullingMask 过滤剔除。
* **蒙皮网格离屏更新保护（`updateWhenOffscreen = True`）**：
  * 大力神这类超大体量模型在合体动画中，部分工程车会在摄像机视锥体外围展开并飞入中心。
  * Unity 默认 `SkinnedMeshRenderer.updateWhenOffscreen = False`，会导致边界盒（Bounds）暂时离开屏幕时骨骼动画暂停、网格突然瞬移闪烁。必须将所有 SMR 的 `m_UpdateWhenOffscreen` 强制写入 `True`。
* **冗余 Mono 代码清洗**：
  * 导出自 Unity 的 Prefab 若包含自定义 C# 脚本，在注入原版 Bundle 时会因缺少 DLL 产生 Missing MonoBehaviour 报错。必须在合并时清洗这些悬空组件。

---

## 三、 Mecanim 动画循环陷阱与『正向合体 ➔ 定格瞻仰 ➔ 倒放解体 ➔ 归位重组』无缝 Ping-Pong 架构

合体动作（`transform_r_Garage`，原始 192 帧，约 6.37 秒）由 6 辆工程车分散在四周推进、空中变形、到最后一帧合体为擎天巨人。在实现沉浸式无限循环演绎时，经历了从解决底层崩溃到构建工业级丝滑动画的完整演进：

### 1. 陷阱 1：单次播放后永久定格（Clamp Forever）
* **成因**：FBX 导入进 Unity 时，`AnimationClip` 的 `m_LoopTime` 默认为 `False`，`wrapMode` 为 `0`（Once）。在 Mecanim 单状态状态机中，动画播放到最后一帧即永久停滞。
* **解决**：在底层 `MuscleClip` 中将 `m_LoopTime` 设为 `True`，`m_WrapMode` 设为 `2`（Loop）。

### 2. 陷阱 2：Loop Pose（闭环姿态平滑融合）引起的肢体支离破碎（最致命！）
* **成因**：
  * 普通循环动作（如走跑待机）首尾姿态相同，Unity 的 `Loop Pose`（底层变量 `m_LoopBlend`）会自动将第 1 帧与最后一帧做加权融合消除跳跃。
  * 但合体动画**起点是“6 辆车分散在地面”，终点是“咬合为人型整体”**！
  * 一旦开启 `m_LoopBlend = True`，Unity 会把终点的完整合体形态向起点的分散车辆强行做姿态插值。导致**合体完毕的一瞬间，各车肢体关节被硬生生向外扯脱臼，车辆悬空断裂，整个模型变得支离破碎**！
* **铁律与修复**：
  * **合体/展开类非对称动作，必须严格禁用 Loop Pose！**
  * 在底层序列化中强制设置：
    ```python
    mc.m_LoopTime = True             # 允许状态机循环播放
    mc.m_LoopBlend = False            # 严格关闭 Loop Pose 闭环拉扯！
    mc.m_LoopBlendOrientation = False
    mc.m_LoopBlendPositionY = False
    mc.m_LoopBlendPositionXZ = False
    ```
  * 此时骨骼运动 100% 忠实还原原版动画曲线，合体锁死严丝合缝。

### 3. 终极体验提升：四阶段无缝对称镜像 Ping-Pong 动画架构
单纯将单向合体动作循环播放，会导致大力神合体完成后**瞬间瞬间跳回（Snap back）** 6 辆小车状态，在激战中视觉冲击极其突兀断裂。
为了实现最真实、震撼且自然的背景互动，我们设计并落地了**四阶段高精度数学逆序 Ping-Pong 动画管线**：

```
[0.00s]                           [6.37s]              [8.03s]                                      [14.40s]         [14.90s]
   │ ──▶ 阶段 1：6车推进合体 ──▶      │ ──▶ 阶段 2：巨人定格 ──▶ │ ──▶ 阶段 3：数学严格逆序倒放解体（倒车归位） ──▶ │ ──▶ 阶段 4：发车待机 ──▶ │
   └───────────────────────────────┴────────────────────┴──────────────────────────────────────────┴─────────────────┘
                                                                                                            ▲
                                                                                                (首尾零瞬移、无限平滑闭环)
```

#### 关键帧四阶段数学映射法则：
设原正向动画帧数为 $N=192$ 帧（$0.0000s \sim 6.3667s$）：
1. **阶段 1：正向推进合体（$0.0000s \sim 6.3667s$，192 帧）**：
   * 原生忠实保留 1220 条骨骼曲线的所有关键帧 $(t_i, v_i)$。
   * 尾帧（$t=6.3667s$）的 `outTangent` 平滑归零，平稳过渡到定格姿态。
2. **阶段 2：合体完成巨人定格（$6.3667s \sim 8.0334s$，持续 1.6667s / 50 帧）**：
   * 在尾帧追加定格关键帧，数值保持为合体完成值 $v_{191}$。
   * 让玩家在激烈对决中有充足时间看清完全体大力神的巨构细节与威严霸气。
3. **阶段 3：数学级严格逆序倒放解体（$8.0334s \sim 14.4000s$，192 帧）**：
   * 倒放时间：$t_{rev} = t_{hold\_end} + (t_{fwd} - t_j) = 14.4000 - t_j$。
   * 倒放数值：$v_{rev} = v_j$。
   * **切线导数微分反转铁律**：根据微积分链式法则 $\frac{d}{dt}[f(C-t)] = -f'(C-t)$，逆序运动的切线必须严格反转对调：
     $$inTangent_{rev} = -outTangent_j, \quad outTangent_{rev} = -inTangent_j$$
   * 该映射使得 6 辆车从大力神躯干上严密反向拆解、原路倒车驶回各自初始落位点，绝无任何漂移或顿挫。
4. **阶段 4：归位短暂停顿（$14.4000s \sim 14.9000s$，持续 0.5000s / 15 帧）**：
   * 车辆回归初始点后驻车微歇 0.5 秒，尾帧关键帧数值 $v_{end} = v_0$。
   * 尾帧的属性与位置与 $t=0.0s$ 起始帧 **100% 严格一致**。
   * 当 Mecanim 触发循环时，从 14.90s 到 0.00s 的过渡误差为 0，实现了没有任何抽搐和突变的无限丝滑连贯循环！

### 4. 陷阱 3：动作位移引发模型倒地翻覆与多机拼装肢体脱节（卡纳克双巨像实战教训）
在卡纳克沙漠引入凯旋女神（Victorion，由 6 台载具拼装而成）时，踩中了动作选择与肢体绑定的严重陷阱：
* **动作位移翻滚陷阱**：
  * 若误选了包含大幅多段下劈、前滚翻位移的攻击动画（如 `attack_3`），在未搭载 Root Motion 物理约束的场景背景中，末段位移会导致模型重力朝向翻覆，甚至整尊人物“躺倒卧地”。
  * **法则**：背景观战模型必须选用**重心稳定、动作刚劲、在原地起手与收招的专属动作剪辑**（如稳定的 `Victorion_Attack_1`，时长 2.83 秒，挥舞巨剑霸气挥砍后自然回正）。
* **多部件拼装关节脱节与散架**：
  * 组合金刚（Combiner）由多机拼接。如果开启了 `m_LoopBlend`，首尾帧强制融合会硬生生拉断关节约束，导致直升机双臂悬空断裂、跑车双腿脱节飞离躯干。
  * **必须坚决贯彻 `m_LoopBlend = False`**，严格关闭姿态闭环平滑，让每台机体的骨骼曲线按照原生关键帧精确贴合咬合。

---

## 四、 PBR 着色器与光照调色避坑指南

### 1. 全黑剪影（Black Silhouette）根因分析
* **光照贴图脱节**：
  * 场景原生物体挂载静态建筑 Shader：`Hidden/PBR_LIGHTMAP_ON...__STATIC`。
  * 大力神是动态骨骼蒙皮模型（`SkinnedMeshRenderer`），其光照贴图索引为 `lightmapIndex = 65535`（无 Lightmap）。
  * 移动端渲染时，着色器采样缺失的光照贴图返回全黑 `(0, 0, 0)`，与漫反射贴图相乘后导致整个模型变成纯黑剪影。
* **解决方案：注入原生角色动态 PBR Shader**：
  * 从 `character_mergecharacters_procedural.assetbundle` 提取游戏角色专用的动态 PBR 着色器 `Hidden/PBR_EB_SECOND_DIRECTIONAL_LIGHT_ON...`（PID `-7396015257959012681`）。
  * 将该 Shader 的 TypeTree 与二进制数据注入到场景包中，并赋予大力神所有材质。该 Shader 原生支持场景实时双向平行光，彻底摆脱 Lightmap 依赖。

### 2. 渲染偏暗与明艳度重塑
在背光环境下，动态模型容易显得发暗、脏污。必须针对性调整材质 PBR 属性：
1. **消除错误 AO 腰斩**：
   * 场景复合贴图（`_pbr_composite_tex`）的 Green 通道为环境光遮蔽（AO），均值仅 0.54。
   * 若材质保留 `_OcclusionStrength = 1.0`，漫反射会被直接压暗 50%。
   * **修改**：将 `_OcclusionStrength` 强制置为 `0.0`。
2. **漫反射色彩增益（Albedo Tint）**：
   * 原版工程绿贴图在暗处色度偏低（RGB 均值约 0.25）。
   * 将 `_Color` 提升至 `(1.65, 1.65, 1.65, 1.0)`，增益 65%，使霸天虎经典的明艳工程绿在日光下极具冲击力。
3. **环境暗面发光补偿**：
   * 由于生锈荒海太阳光从左上方斜后方照射，大力神正面处于自然阴影中。
   * 注入 `_EmissionColor = (0.15, 0.15, 0.15, 1.0)` 与环境基底色 `_base_col = 0.75`，给暗面提供均匀的散射漫射光，杜绝死黑。
4. **金属与清漆高光锐化**：
   * 设置 `_reflectance = 0.08` 与 `_clearcoat_reflectance_range = 0.20`，在沙漠阳光下激发出醒目的金属高光边缘轮廓。

### 3. PBR 自发光遮罩与移动端泛光失真（“粉红超新星”强光陷阱，最隐蔽杀手！）
在卡纳克沙漠调优修罗王与凯旋女神材质时，遭遇了模型在实机上通体爆发出极度刺眼的粉红色超新星强光的重大 Bug：
* **TFTF 角色着色器 RAOE 通道真理**：
  * 原生角色 PBR 着色器 `Hidden/PBR_EB_SECOND_DIRECTIONAL_LIGHT_ON...` 采用特殊的 **RAOE 复合通道标准**（`_pbr_composite_tex`）：
    - `R` (Red) = 粗糙度 (Roughness)
    - `G` (Green) = 环境光遮蔽 (Ambient Occlusion, AO)
    - `B` (Blue) = **自发光遮罩 (Emissive Mask)**！
    - `A` (Alpha) = 金属度 / 附加属性 (Metallic / Specular)
  * 着色器中总自发光计算公式如下：
    $$\text{TotalEmissive} = \text{tex2D}(\_pbr\_composite\_tex, uv).b \times \_emissive\_overbright\_range \times \_EmissionColor.rgb$$
* **强光致盲成因剖析**：
  * 此前为了消除全黑剪影，误将复合贴图绑定到特效贴图（如 `fx_t_energy_vortex`），该贴图的 Blue 通道全图恒为 255（1.0）。
  * 角色着色器默认预埋了 `_emissive_overbright_range = 120.0`。
  * 只要材质上赋予哪怕一点微弱的 `_EmissionColor = (0.35, 0.35, 0.35)`，两者相乘便会产生 **$1.0 \times 120.0 \times 0.35 = 42.0$ 的毁灭级自发光强度**！
  * 移动端后处理（Post-Processing）的 HDR 泛光（Bloom）阈值通常为 1.0。高达 42 倍的发光强度直接击穿了 Tone-mapping 映射上限，在暖黄色的卡纳克沙漠中严重色偏溢出为通体发白、边缘泛粉的巨大超新星光球！
* **治本防御铁律**：
  * ① **自发光通道参数物理归零**：将材质浮点属性中的 `_emissive_overbright_range = 0.0`、`_emissive_range = 0.0`，并开启 `_emissive_none = 1.0`；颜色属性 `_EmissionColor = (0, 0, 0, 1)` 与 `_emissive_intensity_col = (0, 0, 0, 0)` 坚决清零。
  * ② **选用纯净 RAOE 复合贴图**：使用 `Victorion_AO`（PID `-890209823152787406`），其 G 通道均值 126.5（min 56，层次丰富绝无死黑），B 通道均值仅 2.99/255 ≈ 0.01（自发光遮罩近乎零）。
  * ③ **解除 AO 强制压暗**：将 `_OcclusionStrength` 强制置为 `0.0`，杜绝暗部被环境遮蔽腰斩成黑块。
  * ④ **沙漠日光漫反射增益**：将基础颜色 `_Color` 设为 `(1.5, 1.5, 1.5, 1.0)`，平行光与环境散射增益 `_base_col`、`_base_r/g/b_col` 统一设为 `1.2`，获得日光下通透鲜活、高对比度的高清金属机甲质感。
  * ⑤ **防法线缺失空指针黑块**：凯旋女神等缺少原装法线贴图的模型，统一绑定场景平整法线（如 `krnk_prop_pillar_01_n`），严禁留空触发 Shader 异常黑块。

---


---

## 五、 战斗场地活动围栏与背景巨像落位避让法则

在格斗游戏中，背景动态演绎角色绝不能干扰或侵入前景英雄的对战体验：

### 1. 致命误区：将视觉装饰地标误当成全部活动空间
* **现象**：初次配置时，若误以为卡纳克中央只有内圈小圆盘（半径约 15 米）是战斗场地，将巨像放置在半径 20~30 米处（如 `(-22, 0, 20)` 与 `(22, 2.06, 20)`）。在实机对战中，战斗英雄一旦闪避后撤或蓄力突进，便会直接穿模移动到巨像脚下甚至踢到巨像小腿。
* **真实架构真相**：
  * 卡纳克沙漠中央的内环小圆盘仅为视觉起点中心；
  * 整个外环刻花金属大圆盘 `krnk_trrn_metal_panel_floor_01`（半径约 35.3 米）**全都是角色可以自由移动的平地**；
  * 真正的战斗活动物理边界是由场景摄像机辅助系统 `HELPERS_CAMERAScale/player_wall` 约束的八角形空气墙，其有效边界半径高达 **45~50 米**！

### 2. 背景巨像落位五大黄金法则
为彻底杜绝穿模并营造震撼的观赛构图，提炼出以下五项工程标定法则：

1. **绝对安全避让距离（$R \ge 60$ 米）**：
   * 背景模型摆放半径必须严格大于空气墙外沿 15 米以上。
   * **修罗王（① 号位）**：放置在左上角沙丘废墟后方 `X = -48.0, Y = 1.5, Z = 46.0`（距中心 $R = 66.5$ 米）。
   * **凯旋女神（② 号位）**：放置在右上角狮身人面像前沙丘 `X = 46.0, Y = 4.13, Z = 46.0`（距中心 $R = 65.0$ 米）。
2. **视线绝对聚焦法则（$\text{atan2}$ 朝向计算）**：
   * 模型从坐标 $(X, Z)$ 看向战场中心 $(0, 0)$ 的向量为 $(-X, -Z)$，其航向角应严格设为 $\theta = \text{atan2}(-X, -Z)$：
     - ① 号位：$\text{atan2}(48, -46) \approx 133.78^\circ$，四元数 `{x: 0, y: 0.91976, z: 0, w: 0.39249}`；
     - ② 号位：$\text{atan2}(-46, -46) = -135.0^\circ$，四元数 `{x: 0, y: -0.92388, z: 0, w: 0.38268}`。
   * 双巨像视线 100% 聚焦于圆盘中央的格斗对决。
3. **双巨像对立夹角（Angular Separation）**：
   * 双机夹角保持在 $90^\circ \sim 150^\circ$ 之间（本次为 $91.22^\circ$）。在主对战摄像机广角画幅中左一尊、右一尊遥相呼应，构筑出极富层次感的史诗竞技场纵深。
4. **沙丘斜坡地面贴合度（Terrain Grounding）**：
   * 沙漠边缘沙丘具有自然坡高（卡纳克沙丘地表高度约为 $Y = 1.5$ 米）。
   * 凯旋女神模型因动作中心自带约 2.63 米的局部中心偏移，其 Transform Y 坐标需相应设为 $Y = 1.5 + 2.63 = 4.13$ 米，从而使其双脚紧密服帖地踩在沙丘表面，杜绝漂浮或陷地。
5. **远景等高巨像透视配比（Colossus Equalized Scale）**：
   * 移至 65 米远景后，模型需按视网膜远近透视比放大：
     - 修罗王：`Scale = (600, 600, 600)`（体高约 31.1 米）；
     - 凯旋女神：`Scale = (130, 130, 130)`（体高约 31.2 米）；
   * 二者在远景地平线上呈现等高平齐的巍峨身躯，与前景英雄形成鲜明的巨微对比。

---

## 六、 UnityFS 单轨 resS 纹理流归一化

Unity 在 Android 运行时的 AssetBundle 资源加载器遵循“单归档单流”规则：
* 当主场景包名为 `CAB-8047d50cb53b499f81473861dbf0f211` 时，Android 底层只会打开并持有 `CAB-8047d50cb53b499f81473861dbf0f211.resS`。
* 若直接将外部带有的 `CAB-173392592a09aa74156a2f75549d5a15.resS` 复制进包中，Android 引擎不会为第二 CAB 建立资源流句柄，导致所有外部贴图加载为空。

**单轨合并标准算法**：
```python
# 1. 计算主 resS 字节基准偏移
rust_ress_bytes = bf.files[rust_ress_name].read()
dev_ress_bytes = bf.files[dev_ress_name].read()
base_offset = len(rust_ress_bytes)

# 2. 追加合并数据并更新主流
combined_ress_bytes = rust_ress_bytes + dev_ress_bytes
reader = EndianBinaryReader(combined_ress_bytes)
reader.flags = bf.files[rust_ress_name].flags
bf.files[rust_ress_name] = reader
del bf.files[dev_ress_name] # 彻底移除次级 resS

# 3. 重定向外部贴图 StreamData
for tex in dev_textures:
    tex.m_StreamData.path = f"archive:/{primary_cab}/{primary_cab}.resS"
    tex.m_StreamData.offset = base_offset + orig_offset
    tex.save()
```
合并后，主包仅保留唯一的 `.resS` 流文件，彻底杜绝移动端纹理读取异常。

---

## 七、 ODR 目录与 TOC CRC 校验绕过

TFTF 客户端通过 `ODRManager` 动态加载场景。在 `assets/rust/toc.txt` 中预埋了场景包的 CRC 校验码与尺寸：
* 一旦修改了 `rust_merged.assetbundle`，文件哈希改变，`ODRManager.LoadAssetBundle` 会报 CRC 校验失败，并**强制安全回退至 Karnak（卡纳克）沙漠场景**。
* **规避铁律**：
  在 `Server/build_phone_apk.py` 的 APK 打包流中，拦截 `assets/rust/toc.txt`，动态将 `crc` 置为 `0`，并注入修改后 bundle 的真实字节尺寸：
  ```python
  elif info.filename == "assets/rust/toc.txt":
      rpath = Path("assets_redeco/rust_merged.assetbundle")
      if rpath.exists():
          toc_dict = json.loads(data.decode("utf-8"))
          toc_dict["bundles"]["rust_merged"]["crc"] = 0
          toc_dict["bundles"]["rust_merged"]["size"] = rpath.stat().st_size
          data = json.dumps(toc_dict, indent=4).encode("utf-8")
  elif info.filename == "assets/karnak/toc.txt":
      rpath = Path("assets_redeco/karnak_merged.assetbundle")
      if rpath.exists():
          toc_dict = json.loads(data.decode("utf-8"))
          toc_dict["bundles"]["karnak_merged"]["crc"] = 0
          toc_dict["bundles"]["karnak_merged"]["size"] = rpath.stat().st_size
          data = json.dumps(toc_dict, indent=4).encode("utf-8")
  ```
  同时在 `packs.txt` 中防止 `rust_merged_odr` 与 `karnak_merged_odr` 污染，确保游戏 100% 稳定读取自定义生锈荒海与卡纳克沙漠地图。

---

## 八、 维护与自动化工具链

整个工作流已高度收敛并固化至工具集中，后续任何场景模型追加均可一键复用：

| 脚本路径 | 功能职责 |
| :--- | :--- |
| [`stage_project/Assets/Editor/GeneratePingPongAnimation.cs`](file:///E:/Agent/TFTF-blender/stage_project/Assets/Editor/GeneratePingPongAnimation.cs) | 自动化解析 1220 条骨骼曲线，生成微积分镜像逆序与定格的无缝 Ping-Pong 动画资产 |
| [`stage_project/Assets/Editor/ExportDevastatorBundle.cs`](file:///E:/Agent/TFTF-blender/stage_project/Assets/Editor/ExportDevastatorBundle.cs) | Unity 批量构建生锈荒海大力神 AssetBundle |
| [`stage_project/Assets/Editor/ExportKarnakBundle.cs`](file:///E:/Agent/TFTF-blender/stage_project/Assets/Editor/ExportKarnakBundle.cs) | Unity 批量构建卡纳克双巨像 AssetBundle |
| [`tools/merge_devastator_rust_stage.py`](file:///E:/Agent/TFTF-blender/tools/merge_devastator_rust_stage.py) | 生锈荒海：提取 TypeTree，将模型层级与骨骼树注入主场景 |
| [`tools/patch_rust_merged_devastator.py`](file:///E:/Agent/TFTF-blender/tools/patch_rust_merged_devastator.py) | 生锈荒海：动态角色 PBR 着色器注入、单轨 resS 合并与纯净循环修正 |
| [`tools/merge_and_patch_karnak_combiners.py`](file:///E:/Agent/TFTF-blender/tools/merge_and_patch_karnak_combiners.py) | 卡纳克沙漠：一站式合并 TypeTree、流资源单轨合并、PBR 防粉红超新星校准、沙丘落位与动画闭环 |
| [`tools/update_unity_scene_colossi.py`](file:///E:/Agent/TFTF-blender/tools/update_unity_scene_colossi.py) | 卡纳克沙漠：Unity 场景 YAML 批量更新修罗王与凯旋女神位姿与缩放 |
| [`Server/build_phone_apk.py`](file:///E:/Agent/TFTF-blender/Server/build_phone_apk.py) | 拦截 TOC CRC 并注入准确文件大小，防止生锈荒海与卡纳克沙漠回退 |
