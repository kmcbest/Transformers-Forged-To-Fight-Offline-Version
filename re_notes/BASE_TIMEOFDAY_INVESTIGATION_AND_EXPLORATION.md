# 基地不同时刻光照系统（Time of Day, TOD）调研与技术探索总结

## 1. 探索背景与目标

- **用户诉求**：原版 TFTF 中，玩家基地始终固定在冷月夜晚的场景与光照效果。玩家注意到战斗关卡（如 Primordial / 始源竞技场）具备不同时刻（Day, Sunset, Bluemoon, Dark Energon 等），提出基地是否能支持不同时刻的光照，并希望能实现启动游戏时随机抽取一种时刻（或手动指定），以获得全新的视觉氛围体验。
- **目标效果**：呈现逼真的白昼（阳光明媚、蓝天薄雾）、黄昏（暖金夕阳、晚霞暮色）或特殊异象，同时**必须 100% 保持基地地表岩石原本的细节、凹凸纹理、法线高光与真实材质质感**。

---

## 2. TFTF 光照与渲染底层架构解析

通过反编译 C# 代码、il2cpp 内存布局及 UnityFS AssetBundle 分析，游戏的时刻管理与渲染系统由以下核心组件构成：

1. **`EBTimeOfDayManager`（全局时间时刻管理器）**：
   - 单例地址：GOT `0x2BDB680`，静态字段 `_this` 位于 `static_fields + 0x0`。
   - 管理数组：`TimeOfDays` (`0x18`)，当前激活项 `ActiveTimeOfDay` (`0x20`)。
   - 负责调用 `EBTimeOfDay.Apply` 和 `EBReflectionProbe.Apply`，将主光源参数、环境球谐参数（SH）、反射探针、天空盒与烘焙光照贴图推送到全局 GPU Shader 变量。

2. **`EBTimeOfDay`（具体时刻数据容器）**：
   - `KeyLight` (`0x48`)：场景主光源 GameObject（基地为 `Moon`）。
   - `RenderSettings` (`0x20`)：关联的 `BaseRenderSettings` / `EBRenderSettingsBase`。
   - `ReflectionProbe` (`0x38`)：关联的 `EBReflectionProbe`，提供间接照明与球谐系数（`SH` @ `0x50`）。
   - `SkyBox` (`0x30`)：天空网格与材质（基地为 `skybox_0_baked`，挂载 `qb_primordial_sky_night_01` 贴图）。
   - `Lightmaps` (`0x70`)：烘焙光照贴图数组（基地使用 `partition0_0_Forward_Environment`，绑定到 Shader 全局变量 `_lm`）。

3. **竞技场（Primordial） vs 基地（Base）的资产结构异同**：
   - **`primordial_merged.assetbundle`**：包含 6 套完整时刻 Prefab：
     - `primordial_timeofday_0_forward` (Day 晴天)
     - `primordial_timeofday_1_forward` (Sunset 黄昏)
     - `primordial_timeofday_2_forward` (Bluemoon 蓝月)
     - `primordial_timeofday_3_forward` (Dark Energon 暗黑超能)
     - `primordial_timeofday_4_forward` (Toxic 瘴气)
     - `primordial_timeofday_5_forward` (Eclipse 日蚀)
     - 其天空材质绑定了 `qb_primordial_sky_mist`（白天青雾天幕）和 `qb_primordial_sky_red`（晚霞暮色天幕）。
     - **Lightmap 数量为 0**：全实时光照，依靠极高光强与微小光圈。
   - **`base_merged.assetbundle`**：仅有单一预制体 `base_timeofday_0_baked`：
     - 天空材质为 `skybox_0_baked`（夜晚星空）。
     - **拥有专门的地表烘焙光照贴图 `partition0_0_Forward_Environment`**，负责基地地表复杂岩石凹凸暗调的阴影与环境遮挡。

---

## 3. 已尝试的技术路线与失效复盘

### 路线 1：资产路径重定向（TFormAssetManager.Path / hook_186）

- **实施方案**：
  在 `tools/nativehook/hook.c` 的 `TFormAssetManager.Path`（RVA `0x00B05438`）挂钩，当加载 `base_merged/base_timeofday_0_baked` 时，直接重定向到 `primordial_merged/primordial_timeofday_*`。
- **测试结果（见用户反馈截图 `media_1790692802554.png`, `media_1790692857870.png`）**：
  地表和悬崖完全变成单一的纯白或纯青色，所有岩石凹凸与细节全部消失，如同被刷上了一层均匀纯色油漆。
- **深层根因分析**：
  1. **14,000 倍光学曝光断崖**：
     - 竞技场战斗相机为了景深清晰，光圈极小（**f/20.0**, ISO 193, 1/300s 快门）。Kabam 为了在 f/20.0 下照亮角色，将日光光强（`_UnitIntensity`）拉到惊人的 **35,000.0**，天空亮度达到 **26,000.0 ~ 40,000.0**。
     - 基地相机则是为静谧夜景设计的大光圈广角相机（**f/2.1**, ISO 1200），感光能力高出上百倍！原生的月光直射光强只有 **2.5**，天空亮度仅 **3.0**。
     - 将竞技场 35,000 级光照引入 f/2.1 的基地相机中，光子信号瞬间把 RGB 通道彻底打满截断（clamped to white），产生极度过曝。
  2. **地表 Lightmap 丢失**：
     - 竞技场无 Lightmap，而基地地表着色器极度依赖 `partition0_0_Forward_Environment`。丢失后地表无法计算暗部与环境遮挡。

---

### 路线 2：原生 BaseRenderSettings + EBLight + ReflectionProbe 动态参数注入

- **实施方案**：
  保留原生 `base_merged/base_timeofday_0_baked` 载入，以确保 Lightmap 和材质完整。在 `hook_80`（`BaseRenderSettings.ApplyBaseSettings`）中每帧动态注入：
  - `BaseFogColorAmbient`、`BaseFogColor`、`BaseZoomFogColor`
  - 雾效范围 `BaseFogDistStart`（25m）和 `BaseFogDistEnd`（350m）
  - `SkyClearColor` 与 `SkyLuminousScale`
  - `EBLight._UnitIntensity`（2.5 ~ 3.8 物理安全区间）与 `_Color`
  - `EBReflectionProbe` 球谐环境光（SH）DC 项
- **测试结果（见用户反馈截图 `media_1790694659118.png`, `media_1790694659133.png`, `media_1790694659139.png`）**：
  地表未过曝，但整个基地被一层厚重的有色浓雾覆盖（蓝雾、灰白雾、紫雾），用户反馈：“**感觉不是调了光照，是不同颜色的毒气笼罩了基地**”。
- **深层根因分析**：
  1. **基地地形 Shader 对直射光的响应机制**：
     - 基地地表使用的 Shader（`Hidden/PBR_..._EB_COMPOSITE_RMEAO_`）漫反射项几乎完全由烘焙贴图 `_lm` 驱动，直射光（`EBLight` / Moon）无法直接将暗色地表提升为明亮白昼。
  2. **Fog 机制误用成了“光照伪造器”**：
     - Unity 的屏幕空间距离/高度雾（Fog）是在画面像素上做颜色插值（Blend）。当为了营造白昼蓝天或晚霞而将 Fog Color 改为亮蓝、橙黄或紫红并拉大距离时，摄像机前方 25m~350m 的全部建筑物和地面都被蒙上了一层浓重的纯色薄膜，视觉呈现即为“毒气弥漫 / 严重沙尘暴”。
  3. **背景天空盒（Skybox）依旧是夜晚**：
     - 远端天幕依然挂着 `qb_primordial_sky_night_01` 深黑星空贴图。黑夜天幕与前景的浓厚彩色大雾产生严重冲突，更加剧了“夜间毒气突袭”的违和感。

---

## 4. 给后续接手 Agent 的建议与突破口

若后续需要继续推进基地真实多时刻（TOD）系统，建议沿以下路线实施：

### 建议方向 A：天空盒贴图动态替换（最立竿见影的氛围感提升）
- **核心逻辑**：
  夜晚感的核心来源是天上的 `qb_primordial_sky_night_01` 贴图。
  在 `primordial_merged.assetbundle` 中存在高精度的 `qb_primordial_sky_mist`（白昼晴云薄雾）与 `qb_primordial_sky_red`（晚霞夕阳）。
  通过 `Material.SetTexture`（RVA `0x1B5682C`），在基地载入完成后将天空材质 `skybox_0_baked` 的 `_base_tex` 动态绑定为 `qb_primordial_sky_mist` 或 `qb_primordial_sky_red`。天幕换成白昼/夕阳后，自然呈现真实天空，无需依赖任何厚雾。

### 建议方向 B：彻底压低或禁用 Fog，严禁用亮色 Fog 模拟光照
- 无论切换到任何时刻，`BaseFogColor` 的透明度/强度都必须保持极低，甚至可以将 FogDistEnd 推到 2000m 以上或关闭雾效，确保视野清澈透明，坚决避免“毒气笼罩”感。

### 建议方向 C：在 AssetBundle 层制作/克隆多套 base_timeofday
- 基地地表最真实的光照是预烘焙好的 `_lm` Lightmap。
- 使用 `UnityPy` 对 `base_merged.assetbundle` 进行增量扩充，生成 `base_timeofday_1_day`，将其中的烘焙贴图亮度曲线调成白天调色，并配合 `qb_primordial_sky_mist` 天空盒。在代码端加载不同 Prefab，即可实现与原版夜景质感完全一致的电影级白昼基地。
