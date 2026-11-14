# TFTF 战斗场景动态模型嫁接与背景演绎技术指南
# (Battle Stage Dynamic Model Integration & Background Animation Specification)

本文档系统性总结了《变形金刚：百炼为战》（Transformers: Forged to Fight）离线重构版本中，**在既有战斗场景（Stage / Arena）中添加全新外部 3D 动态模型、绑定背景循环动画、调教动态 PBR 着色器以及规避 AssetBundle 底层陷阱的全套端到端工业化流程**。

---

## 一、 核心架构与技术挑战

在 TFTF 场景中植入如“6车合体大力神（Devastator）”这类高复杂度动态资产，存在数个跨引擎与底层打包层面的致命技术壁垒：

```
[外部 3D 模具与动作 FBX] ──▶ [Unity 2020.3.31f1 独立舞台工程]
                                            │ (导出舞台临时 AssetBundle)
                                            ▼
[原版 Stage rust_merged.assetbundle] ◀── [merge_devastator_rust_stage.py] (TypeTree & 层次合并)
                                            │
                                            ▼
                               [patch_rust_merged_devastator.py]
                               ┌────────────┴────────────┐
                               ▼                         ▼
                  [动态角色 PBR 着色器注入]       [resS 纹理流单轨归一化]
                  [材质光照与暗面补偿调色]       [Mecanim 纯净循环防畸变]
                               │
                               ▼
            [assets_redeco/rust_merged.assetbundle]
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

---

## 五、 UnityFS 单轨 resS 纹理流归一化

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

## 六、 ODR 目录与 TOC CRC 校验绕过

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
  ```
  同时在 `packs.txt` 中防止 `rust_merged_odr` 污染，确保游戏 100% 稳定读取自定义生锈荒海地图。

---

## 七、 维护与自动化工具链

整个工作流已高度收敛并固化至工具集中，后续任何场景模型追加均可一键复用：

| 脚本路径 | 功能职责 |
| :--- | :--- |
| [`stage_project/Assets/Editor/GeneratePingPongAnimation.cs`](file:///E:/Agent/TFTF-blender/stage_project/Assets/Editor/GeneratePingPongAnimation.cs) | 自动化解析 1220 条骨骼曲线，生成微积分镜像逆序与定格的无缝 Ping-Pong 动画资产 |
| [`stage_project/Assets/Editor/ExportDevastatorBundle.cs`](file:///E:/Agent/TFTF-blender/stage_project/Assets/Editor/ExportDevastatorBundle.cs) | Unity Headless 批量构建 Android 舞台 AssetBundle |
| [`tools/merge_devastator_rust_stage.py`](file:///E:/Agent/TFTF-blender/tools/merge_devastator_rust_stage.py) | 提取 TypeTree，将模型层级与骨骼树注入生锈荒海主场景 |
| [`tools/patch_rust_merged_devastator.py`](file:///E:/Agent/TFTF-blender/tools/patch_rust_merged_devastator.py) | 动态角色 PBR 着色器注入、单轨 resS 合并、光照提亮与纯净循环修正 |
| [`Server/build_phone_apk.py`](file:///E:/Agent/TFTF-blender/Server/build_phone_apk.py) | 拦截 TOC CRC 并注入准确文件大小，防止场景回退 |
