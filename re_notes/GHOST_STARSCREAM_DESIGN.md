# 鬼魂红蜘蛛（Ghost Starscream）完整美术与技术制作方案

> **角色代号**：`starscream_ghost_gs`  
> **阵营/职业**：霸天虎（Decepticon）· 战术系（Tactician）或 科技系（Tech）· 5星卡牌  
> **核心特征**：全身幽灵灵体自发光、呼吸脉冲残魂微光、暗能量紫光眼眸、小腿半透明消隐虚化、全时悬浮飞行与脚底幽冥磷火推进。

---

## 1. 角色背景与设计概念 (Concept & Lore)

在《变形金刚G1》经典剧情《红蜘蛛的鬼魂》（Ghost in the Machine / Starscream's Ghost）中，红蜘蛛被惊破天的粒子加农炮轰碎身躯后，其不灭的火种化为怨念鬼魂游荡在赛博坦与宇宙之间。

本方案旨在通过 TFTF 原生 Unity 引擎特性，不依赖外部不可控魔改，纯粹利用 **PBR 着色器自发光（Emissive）、材质透明混合（Alpha Blending）、动画状态机覆盖（AnimatorOverrideController）与招式粒子重定向（Moveset Particle Binding）**，100% 还原出晶莹剔透、飘在空中的“幽灵红蜘蛛”。

---

## 2. 基础机体模具选择 (Base Mold & Assets)

在 TFTF 资产体系中，经典的 G1 飞机小队（Seekers）共享中等人形（Medium Biped）骨骼架构：
* **机体母本**：选用 `thundercracker_gs_leader2015.assetbundle`（或 `skywarp_gs_leader2015.assetbundle`）。
  * 理由：该 AssetBundle 与红蜘蛛为 100% 同模机体，自带红蜘蛛的原版 S2 踩踏动作（`starscream_gs_attackSpecial_02_stomp`）与战机变形网格，骨骼层级完全一致。
* **悬浮动作源**：提取自 `dirge_gs_deluxe2008.assetbundle` / `ramjet_gs_deluxe2008.assetbundle`。
  * 包含 `Ramjet_G1_CombatIdle`（浮空待机）与 `Ramjet_locorun`（飞行滑行）。

---

## 3. 幽灵全息自发光涂装 (Ghost / Hologram Emissive Shader)

依据 `.agents/skills/tftf_revival/SKILL.md` 第 6 节解析的 `EB/Character/PBR` 着色器规范实现：

### 3.1 漫反射贴图 (`_base_tex` Albedo) 处理
* **基调色**：将红蜘蛛原本高饱和的红、白、蓝、灰机甲，通过色彩矩阵转化为**冷灰青色谱（Ghostly Spectral Cyan）**（主色调 `#A8E6F0` 至 `#C2F5FF`，金属部分调为暗青灰 `#3A5258`）。
* **残痕保留**：保留胸口座舱透明罩、机翼霸天虎标志、进气道等经典细节，但整体赋予一种“半能量晶体化”的虚幻质感。

### 3.2 自发光复合贴图 (`_pbr_composite_tex` RAOE Alpha) 调配
TFTF 的 PBR 复合贴图采用 4 通道设计：
* **R 通道 (Roughness)**：降至 `30 ~ 60`（整体润泽光滑，提升表面微弱的高光流光效果）。
* **G 通道 (Metallic)**：维持在 `80 ~ 120`（保留淡淡的金属外壳反光）。
* **B 通道 (Cavity)**：保持细节凹陷遮挡。
* **A 通道 (Emissive Mask)**：
  * **机身整体**：涂抹为中等灰度 `120 ~ 160`（实现全身 $50\% \sim 65\%$ 强度的灵体柔和自发光，在阴暗场地无视阴影，泛出幽幽冷光）。
  * **装甲边缘与接缝**：通过边缘检测增强至 `200 ~ 220`，形成灵体外轮廓光（Rim Light）。

### 3.3 材质参数配置 (Material Emissive Settings)
在角色主材质（`cha_starscream_ghost_main`）中注入以下原生 PBR 控制参数：
```json
{
  "_emissive_intensity_col": { "r": 0.15, "g": 0.85, "b": 1.0, "a": 0.0 },
  "_emissive_overbright_range": 35.0,
  "_emissive_pulse_intensity_range": 0.35,
  "_emissive_pulse_time_range": 1.8
}
```
* **效果**：
  * 发光呈现极度纯净的**幽灵青蓝色光芒**；
  * `_emissive_overbright_range = 35.0` 会在战斗 HDR/Bloom 镜头下产生轻微的眩目光晕；
  * `_emissive_pulse_...` 会让整具机体以 **1.8秒为周期一明一暗地呼吸脉动**，仿佛游离的怨念火种核心在胸腔跳动！

---

## 4. 眼睛暗能量紫光实现 (Dark Energon Purple Glow Eyes)

红蜘蛛即便化为鬼魂，眼中依然充满对霸天虎权力的狂热与暗能量的邪恶：

### 4.1 贴图局部精准遮罩定位
1. **2D UV 坐标定位**：
   在 `thundercracker_gs_leader2015_main_a` 贴图中，定位红蜘蛛面部双眼对应的 UV 选区区块；
2. **Albedo 颜色填充**：
   在 `_base_tex` 上将眼球 UV 区域填涂为高饱和度的**暗能量品紫色**（`#E020FF` 或 `#FF00D0`）；
3. **RAOE Emissive 通道压满**：
   在 `_pbr_composite_tex` 的 Alpha 通道中，将眼睛区域完全刷成 **纯白（255）**。

### 4.2 光学对比效果
* 全身躯干为柔和的青蓝幽光（Alpha 120~160，泛光倍率 35）；
* 双眼为纯白 Alpha 255 的暗能量紫光，在 Bloom 作用下会刺破幽灵青光溢出眼眶，形成极具威慑力的**穿透性紫芒眼眸**！

---

## 5. 小腿至脚板半透明消隐虚化 (Translucent Lower Legs & Feet)

要让红蜘蛛看起来像真正的幽灵，机甲必须从膝盖以下逐渐“消散成烟”：

### 5.1 材质渲染模式切换
在主网格材质（Material）中开启透明混合：
* **`_Mode`**：由 `0.0` (Opaque) 改为 **`3.0` (Transparent)** 或 **`2.0` (Fade)**。
* **`_CustomRenderQueue`**：设为 **`3000`**（放入 Transparent 渲染队列，后于背景和场景绘制）。
* **混合模式**：
  * `_SrcBlend = 1.0` (`One`)
  * `_DstBlend = 10.0` (`OneMinusSrcAlpha`)
  * `_ZWrite = 0.0`（半透明物体关闭深度写入，防止遮挡背景产生黑边）。

### 5.2 垂直高度 Alpha 渐变绘制 (Vertical Fade Gradient)
利用 Python 脚本配合 3D 顶点高度（$Y$ 轴坐标）与 UV 映射：
1. **高度区间判断**：
   * 膝盖骨骼（`LeftLeg` / `RightLeg`）高度以上：Alpha = 1.0（100% 不透明实心灵体）；
   * 膝盖至脚踝：Alpha 呈余弦平滑过渡（$1.0 \to 0.35$）；
   * 脚底板边缘：Alpha 衰减至 $0.15 \sim 0.20$（极度半透明）。
2. **烘焙进 `_base_tex` 的 Alpha 通道**：
   着色器在渲染腿部时，下半截机体将直接透出战斗背景的地面与光影，呈现出腿部虚无缥缈、如同鬼火凝结而成的视觉效果。

---

## 6. 全时悬浮飞行与动作模组改造 (Hovering Locomotion & Moveset)

### 6.1 动画切片替换 (`AnimatorOverrideController`)
在鬼魂红蜘蛛的角色 AssetBundle 中配置 `override_Starscream_Ghost_fight`：
* **待机动画覆盖**：
  * `CombatIdle` $\longrightarrow$ **`Ramjet_G1_CombatIdle`**
  * *效果*：红蜘蛛双脚悬空抬离地面，双腿微曲前后轻微漂浮摇曳，不再落地。
* **移动奔跑覆盖**：
  * `locorun` $\longrightarrow$ **`Ramjet_locorun`**
  * *效果*：推杆移动时，红蜘蛛身体前倾、双脚悬空在地面上方平滑滑行飞行，彻底告别普通步兵的跑步动作！
* **招式覆盖保持**：
  * 基础轻重攻击保留红蜘蛛原版拳脚与零射线扫射；
  * 必杀技保留经典三绝招（S1 空中优势组合、S2 狡猾的背叛踩踏、S3 战机轰炸）。

### 6.2 招式表与脚底幽冥磷火挂载 (`moves.assetbundle`)
利用 `moves.assetbundle` 的事件系统，创建或绑定 `move_starscream_ghost_idle` 与 `move_starscream_ghost_run`：
* **挂载骨骼节点**：
  * 左腿推进器：`character_model/Reference/Hips/LeftUpLeg/LeftLeg`
  * 右腿推进器：`character_model/Reference/Hips/RightUpLeg/RightLeg`
* **粒子特效调配**：
  * 将原本喷气机的橙黄尾焰（`jet_left_leg` / `jet_right_leg`）通过材质调色替换为**幽绿/冷紫色幽冥鬼火**（借用 `fx_m_skywarp_tele_a` 或惊破天的反物质粒子），在两脚下方不断向下喷涌出淡淡的磷火微光粒子与青烟。

---

## 7. 角色卡牌、数值与服务器接入 (Game Data & Integration)

### 7.1 图鉴与数值定义 (`Server/gamedata.py`)
```python
ROSTER["starscream_ghost_gs"] = ("decepticon", "tact", 5)  # 5星 霸天虎 战术系

# 专属特色属性微调（高闪避、高暴击率、特技虚化免伤）
_BASE_STATS_OVERRIDE["starscream_ghost_gs"] = {
    "health_mult": 0.95,       # 鬼魂身躯生命略微脆弱
    "attack_mult": 1.25,       # 零射线与暗能量加持的高额攻击力
    "crit_chance": 0.65,       # 天生高暴击率
    "crit_damage": 1.65,       # 165% 暴击伤害倍率
}
```

### 7.2 UI 头像与战斗立绘资源
在 `assets_redeco/` 下生成配对的高清 UI 资源：
* `portraits/portrait_starscream_ghost_large.png`（五星卡牌大立绘：半透明悬浮、全身散发冷青荧光、双眼泛紫）
* `portraits/portrait_starscream_ghost_small.png`（队伍选择小方头像）
* `questboard/portrait_starscream_ghost_quest.png`（副本据点 Boss 战立绘）

---

## 8. 制作执行阶段划分 (Roadmap)

| 阶段 | 任务目标 | 产出物 |
| :--- | :--- | :--- |
| **Phase 1: 贴图重绘与发光烘焙** | 基于 Leader 级飞机机体制作幽灵灰青 Albedo，烘焙全身发光 RAOE 与眼部纯白 Alpha | `cha_starscream_ghost_main_a.png`, `main_tform_misc_RAOE.png` |
| **Phase 2: 半透明与材质打包** | 编写脚本注入 `_Mode=3.0`, `Queue=3000`, 配置紫光/青光发光向量，打包 AssetBundle | `assets_redeco/starscream_ghost_gs_leader2015.assetbundle` |
| **Phase 3: 悬浮动画与招式绑定** | 移植 `Ramjet_G1_CombatIdle` / `Ramjet_locorun`，重定向 AOC 并挂载磷火粒子事件 | `moves.assetbundle` (含鬼魂待机/移动) |
| **Phase 4: 卡牌图鉴与全包编译** | 注册 `gamedata.py`，导出 payload，重构 APK 并推送真机验证 | 完整独立 5 星鬼魂红蜘蛛角色上架 |
