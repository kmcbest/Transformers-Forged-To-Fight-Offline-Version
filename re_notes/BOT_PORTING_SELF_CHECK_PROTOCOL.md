# TFTF 第三方 3D 角色移植防错与自纠偏执行协议 (Self-Check & Self-Correction Protocol)

> **定位**：[THIRD_PARTY_3D_MODEL_PIPELINE.md](file:///e:/Agent/TFTF-blender/re_notes/THIRD_PARTY_3D_MODEL_PIPELINE.md) 的**强约束执行层与防呆门禁**。
> **适用对象**：所有执行第三方向游戏移植新角色模型（Blender 对齐 → Unity 导出 → AssetBundle 嫁接 → APK 打包）的模型/智能体。
> **⚠️ Alliance 模具专属前置入口**：若源模型来自 ***Transformers: Alliance***（如 Star Saber、Swoop 等三指拓扑/自带变形动画/鸟兽模具），**请务必最先阅读 [`ALLIANCE_MODEL_PORTING_GUIDE.md`](file:///e:/Agent/TFTF-blender/re_notes/ALLIANCE_MODEL_PORTING_GUIDE.md)** 并使用 `tools/starsaber/` 或 `tools/swoop/` 黄金模板。

---

## 0. 四条铁律（违反任意一条立即失败）

1. **禁止从零重写核心脚本**：必须直接克隆“黄金模板”，仅修改角色路径/骨骼映射/图集列表：
   - 贴图烘焙：`tools/brawl/build_brawl_atlased_textures.py`
   - Blender 人形/载具对齐：`tools/brawl/build_aligned_brawl_robot.py`、`tools/brawl/build_aligned_brawl_tank.py`（或 `tools/tarn/build_aligned_tarn.py`）
   - Unity 场景与渲染对比：`toolchain/unity_build_project/Assets/Editor/BuildBrawlInspectionScene.cs`（或 `BuildTarnInspectionScene.cs`）
   - Bundle 嫁接：`tools/brawl/generate_brawl_bundle.py`（或 `tools/tarn/generate_tarn_bundle.py`）
2. **禁止跳过机器校验器 (`tools/validate_port_gates.py`)**：每一阶段结束后必须立刻运行对应 Gate；只要返回码 `!= 0`，**严禁进入下一步**，必须根据 `[SELF-FIX]` 就地修复并重跑至 `[PASS]`。
3. **禁止盲目掩盖缺陷**：严禁通过“将手指全部焊死到 `LeftHand`”、“清空 `Stream 2` 数据”、“强行调亮 `_Color`”等方式绕过告警。
4. **Gate 3 视觉放行前禁止出包**：必须把 Unity 侧并排对比图与左手手指 Open/Curled 图用 `read_file` 查看并交给用户确认后，才允许运行 `generate_*_bundle.py` 和 `build_apk.py`。

---

## 1. 四阶段硬门禁流水线 (Fail-Fast Pipeline)

### Stage 1：PBR 贴图与法线金属性通道 (`tex`)
- **必须满足**：
  - 所有散图拼入 `2048x2048` 图集，UV 边界留白 `[0.004, 0.996]`。
  - 法线执行 DirectX → OpenGL Y 轴翻转；`_Normal.png`（游戏用）把 Metallic 写入 **B 通道**（Kabam `NM.B` 规范），`_Normal_unity.png`（Unity 预览用）保留标准 Z 蓝通道 `255`。
  - `_RAOE.png` 严格保存为 **RGB 三通道**（禁用 RGBA，避免黑化/透明溢出）；`_Emission.png` 单独保存且仅保留自发光掩码（非黑像素占比不过爆）。
  - **FOC 共享 `*_e.jpg` 验真铁律**：多角色合包中的通用命名发光图（`head_e`、`chest_e`、`armup_e`、`legs_e`、`armlo_e`、`vh`）严禁直接盲信套用；必须先核对 UV 与自身 Diffuse 对位，必要时基于 FBX 骨骼权重+UV 分区掩码从自身 `*_cust_matinst.jpg` 提取发光区并剔除哑光紫涂装（如 `bip_pelvis`、衣领、头顶），且将 `RAOE.B` 控在 `105~155` 防白化。
- **门禁命令**：
  ```powershell
  python tools\validate_port_gates.py tex --tex-dir "<textures_dir>" --prefixes <cha_main> [<cha_misc>]
  ```
- **视觉检查**：在 Blender 中渲染 `gate1_blender_preview.png` 并用 `read_file` 检查反光/自发光/标志是否清晰。

### Stage 2：Blender 坐标对齐、拆指与权重导出 (`fbx`)
- **必须满足**：
  - **严格 `det=+1` 旋转对齐**：`R_z(-90°)` 使 Blender 空间满足 `+X = Left, -Y = Forward, +Z = Up`（严禁负缩放或单轴硬镜像导致 `X` 左右反转和法线内翻）。
  - **地面优先顺序 (Ground-First)**：必须先对齐 `LeftFoot/RightFoot` 使脚底严格踩在 `Z=0` 并缩放至匹配基模身高，**之后再**做手腕与 15 根手指骨头对齐（否则拉直腿部会连带拖偏手指）。
  - **UE3/FOC 2-Shell → 3-Phalanx 左手拆指**：2 节原始手指网格必须按投影比例（如 `[28, 19]`）切分为基/中/末 3 节，分别绑到 `Finger*1 / Finger*2 / Finger*3`。
  - **跨周期镜像/平铺 UV（`U < 0` / `U > 1`）必须每多边形整数平移归位**：对称载具或胸甲广泛将镜像半边 UV 落在 `[-1, 0)` 象限。**严禁直接全局 `min(max(uv, 0), 1)` 硬截断**（会把整侧车身拍扁在 `U=0` 边缘一列像素上拉丝花屏）；必须按**每多边形均值计算整数偏移 (`shift_u = math.floor(mean_u)`, `shift_v = math.floor(mean_v)`)** 还原进 `[0, 1]` 后再映射进图集象限，并钳制在 `[0.004, 0.996]`。
  - **手臂缩放隔离与轨道 B 世界轴心握拳防反折**：
    * 对上臂/前臂做 `pose_segment_world` 拉伸对位腕关节时，必须立即对 `Hand` 执行**世界矩阵正交归一化 (`Scale = (1, 1, 1)`)**，阻断父骨非等比缩放沿层级污染手掌与手指；
    * 当第三方指骨节距与宿主差 $>25\%$ 或采用轨道 B 预烘焙握拳时，**严禁仅凭经验填写 `Biped` 局部欧拉正负号**（左右手局部轴对称反转极易把四指反折向手背！），必须通过实时世界坐标构造从食指到小指的**确定性世界铰链轴**（如 `(f4_pos - f1_pos).normalized()`）向掌心内侧曲指，并同步前向环扣大拇指，在 Blender 中多角度渲染掌心/正面实拍图确认后再合并回 `LeftHand` / `RightHand`。
  - **非变形装甲刚性权重截断**：非变形装甲块 `w >= 0.65 -> 1.0` 截断消除果冻拉伸。
- **门禁命令**：
  ```powershell
  python tools\validate_port_gates.py fbx --fbx "<robot_prepared.fbx>" --tank-fbx "<veh_prepared.fbx>"
  ```
- **视觉检查**：在 Blender 中渲染人形与基模并排对比图（如 `gate2_blender_robot_sbs.png`）并 `read_file` 核对左右手方向与身形比例。

### Stage 3：Unity Batchmode 导入、C# 矩阵对齐与动作帧验收 (`mesh`)
- **必须满足**：
  - C# 导入脚本必须复用 `DetectAxisSpec`、`NormalGuard`（法线外向性检测）、`VerifyLeftFingerJointAlignment`（校验 15 根手指与基模 BindPose `maxPosDelta`）。
  - 载具必须运行 `AuditVehicleBonesAndClips` 找出真实驱动车体的骨骼（如 `COG`）并保持水平放置。
- **门禁命令**：
  ```powershell
  python tools\validate_port_gates.py mesh --mesh-bundle "<mesh_ab>" --donor "<donor_ab>" --robot-mesh <cha_bot_00> --veh-mesh <cha_bot_01>
  ```
- **强制 9+ 张图核验 (`read_file`)**：Rest / Combat Idle / TeamSelect / Back / Light Punch / Heavy / High Kick / Victory / Vehicle Side-by-Side / Left Hand Open & Curled。全部无误后**暂停并汇报截图请用户拍板**。

### Stage 4：Unity 5.6 AssetBundle 嫁接与 APK 校验 (`bundle`)
- **必须满足**：
  - 使用 `UnityPy` 嫁接网格/贴图/材质时，保留原有 `m_VertexData.m_Channels` 结构；**严禁直接把 Stream 2 整段清零**（否则导致 Unity `SkinMesh` 运行时崩溃或隐身）。
  - **多材质白名单隔离与防白光过曝**：做材质自发光兜底中和时，**严禁将人形主贴图指针无差别覆盖到载具材质（必须用 `neutralize_emissive_only` 豁免 `m_TexEnvs`）**；浅色/沙色载具漆面务必维持 `_metallic_range = 0.0`（交由 `NM.B` 局部控金属度）、`_clearcoat_reflectance_range <= 0.03`、`_Color >= 0.72` 与 `_base_col <= 0.56`，避免强光环境泛白失真。
  - 所有使用中的材质球 `_Color`、`_emissive_intensity_col` 与 `_MainTex` UV Scale/Offset 保持正常基模尺度；载具保留原始有效骨骼哈希数组。
  - **多 SubMesh 热修、Stream 对齐与 `.resS` 隔离（双/多色发光必检）**：
    * **共用贴图隔离**：严禁向被多材质共用的 `RAOE`（如 `wpns_RAOE`）直写局部发光；需要独立色相或独立区域时，拆出独立 `SubMesh` 并深拷贝同形态宿主材质 `m_Shader`（Robot→`MAT_ROBOT_PID`，Vehicle→`MAT_VEHICLE_PID`），保留原模平铺内构材质（如 `TR_Test_Mat_INST`）走第 3 `SubMesh`。
    * **UV 16 字节对齐**：原地读写 `m_VertexData` UV 时，Stream 1 偏移必须用 `s1_off = (vc * stride0 + 15) & ~15`（奇数顶点数直接 `vc * 40` 会错位 8B 导致花屏）。
    * **复用 `Texture2D` 槽位清理**：替换贴图前必须在 `t.save()` 前清零 `t.m_StreamData`（`offset=0, size=0, path=""`），显式设 `m_WrapU/V`（图集标用 `Clamp=1`，内构平铺用 `Repeat=0`）并调用 `t.set_image(..., TextureFormat.RGB24, mipmap_count=1)`。
    * **双 SMR + `m_PreloadTable` + 基线幂等**：同时绑定 `*.prefab` 与 `*_lw.prefab` 两份 SMR 的 `m_Materials` 并重建两份容器 `m_PreloadTable`；`m_IndexBuffer` 重排与法线外抬脚本必须从 `git show HEAD:...` 干净基线全量重算，严禁原地二次叠加执行。
  - **母体共存四重隔离 & `character_model` 等比缩放 & 纯紫防白化**：
    * 保存前必须对 **`env.file.files` 字典键名**、`m_StreamData.path`、双根 GameObject（`<Bot>_GS`/`_lw`）与 `cha_<bot>_00/01` 及 `AssetBundle.m_Container`/`m_PreloadTable` 执行 100% 独立重映射（防止与供体同场双隐形）；
    * 需要缩小或放大身高体格时，**Blender 网格必须坚持 `1.0x` 对齐母骨**，仅在双 Prefab 的 **`character_model.m_LocalScale`** 施加等比缩放（防侏儒畸变与手指缩入前臂）；
    * 紫色发光需强设 `_emissive_range=1.0`、`_emissive_overbright_range=15.0` 且压低 `_emissive_intensity_col.g <= 0.03`（如 `(0.62, 0.02, 1.0)`），防止紫眼/紫标泛白。
  - 重新打包 AssetBundle 必须传 `packer="lz4"`，禁止不压缩保存。
- **门禁命令**：
  ```powershell
  python tools\validate_port_gates.py bundle --bundle "assets_redeco\<bot>.assetbundle" --donor "<donor_ab>" --bot <bot_id>
  ```

---

## 2. 报错代码自纠偏手册 (`[FAIL:*] -> [SELF-FIX]`)

| 门禁阶段 | 报错代码 | 根因定位 | 标准自纠偏动作 |
| :--- | :--- | :--- | :--- |
| **Gate 1 (tex)** | `TEX_DIR` / `TEX_MISSING` | 贴图目录不存在或 `_Diffuse`/`_Normal`/`_RAOE` 命名缺失 | 核对 `--tex-dir` 与 `--prefixes`，确保由图集脚本完整输出 |
| **Gate 1 (tex)** | `RAOE_NOT_RGB` | `_RAOE.png` 含 Alpha (`RGBA`) 或单通道 | 用 `img.convert("RGB")` 重新保存，彻底剥离 Alpha |
| **Gate 1 (tex)** | `RAOE_ROUGH_RANGE` / `RAOE_EM_PCT` | Roughness 均值过暗/过亮，或自发光像素占比过高 | 核对 RAOE R/G/B 通道映射，确保自发光掩码不溢出到全身装甲 |
| **Gate 1 (tex)** | `NM_BLUE_MISSING` / `NM_UNITY_BAD` | `_Normal.png` 缺 `NM.B` 金属性数据或 `_Normal_unity.png` B 通道不对 | 游戏法线将 Metallic 写入 B 通道；Unity 预览法线设 B=255 |
| **Gate 2 (fbx)** | `FBX_CHECK` (`FAIL_UV_RANGE` / `FAIL_UV_TEAR`) | 存在未合并图集的大跨度 UV（如 `65504.0`）或跨 tile 撕裂 | 在 Blender 按多边形 (`loop`) 重映射 UV 到对应图集小块并钳制在 `[0.004, 0.996]` |
| **Gate 2 (fbx)** | `FBX_CHECK` (`FAIL_ZERO_WEIGHT`) | 存在没有任何骨骼权重的孤立顶点 | 检查顶点组命名匹配与漏绑碎片，补绑至最近父骨骼或躯干 `COG` |
| **Gate 2 (fbx)** | `FBX_CHECK` (`FAIL_GROUND` / `FAIL_BLENDER_AXIS`) | 脚底未落地 (`min_z != 0`) 或朝向/比例不符 Blender 规范 | 先执行 `R_z(-90°)`，按脚底先落地+缩放，最后对齐手臂与手指 |
| **Gate 3 (mesh)** | `ROBOT_HEIGHT` / `TANK_VERTICAL` | 人形缩放后高度严重偏离基模，或载具竖直立起/尺寸错误 | 核对 `DetectAxisSpec` 的 `axisSwap` 与高度缩放比；载具必须水平对齐车体长轴 |
| **Gate 3 (mesh)** | `X_AXIS_INVERTED` / `LIMB_OFFSET_TOO_LARGE` | **左右手 X 轴反转**（最致命炸裂/拧麻花根因）或四肢偏移过大 | 检查 Blender→Unity 的 `R_z(-90°)` 与 C# `sx` 符号，禁止双重/三重取反 |
| **Gate 3 (mesh)** | `BONE_COUNT` / `ROBOT_UV_RANGE` / `ROBOT_WEIGHTS` / `VEH_*` | 导出骨骼数丢失、UV 溢出或顶点权重损坏 | 核对 FBX 导出设置与 `BuildGraftedMesh` 骨骼绑定顺序 |
| **Gate 4 (bundle)** | `AB_NAME` / `CONTAINER_KEY` | `AssetBundle.m_Name` 或 `m_Container` 路径仍指向基模未替换 | 将 AssetBundle 名称与 `m_Container` Key 全部重写为新 `<bot_id>` |
| **Gate 4 (bundle)** | `FINAL_MESH_WEIGHTS` / `FINAL_BONE_HASH` | `m_VertexData`（尤其 Stream 2）被错误覆盖/清零，或骨骼哈希缺失 | 保留基模有效 Stream 通道布局与完整骨骼哈希列表，仅替换对应几何流 |
| **Gate 4 (bundle)** | `TEX_DATA_LEN` / `MAT_UV_SCALE` / `MAT_DARK_COLOR` | `Texture2D` 字节为空、UV 缩放未重置或有效材质 `_Color` 过黑 | 确保图集贴图写入 `image data`，重置 `_MainTex` Scale `(1,1)` 与有效颜色亮度（`_Color >= 0.72`） |
| **真机视觉故障** | 半边车身花白条纹/沿中缝劈开 | 源模使用了 `U < 0`（`[-1, 0)`）对称平铺 UV，脚本执行全局 `clamp(0,1)` 把负侧压死在 `U=0` | 用每多边形均值 `math.floor` 整数偏移归位进 `[0, 1]`（参考 `remap_polygon_uv_to_tile`），禁止硬截断 |
| **真机视觉故障** | 载具误贴人形贴图 / 浅色装甲泛白光 | 材质兜底循环误覆盖 `MAT_VEHICLE_PID`，或 `_metallic_range=0.65` + 高清漆过曝 | 使用仅改自发光的 `neutralize_emissive_only`，设 `_metallic_range=0.0, _clearcoat<=0.03, _base_col<=0.56` |
| **真机视觉故障** | 手指往手背反折 / 大拇指缺失 | 混淆 `Biped` 左右镜像局部欧拉正负号，且未正交隔离 `Forearm` 缩放传给 `Hand` | 正交归一化 `Hand (scale=1)`，用实时世界位置构造 `Finger1->4` 世界铰链轴向掌心曲指并环扣拇指 |
| **真机视觉故障** | 下蹲/站姿脚踝悬浮脱离脚窝 | 源模外八字脚掌（如 `X=±2.20`）偏离宿主垂直脚骨轴心过远，且小腿末端插头仅浅插 15cm | 先垂直对位 `Thigh/Calf/Foot` 至宿主脚轴附近，机械整靴归并 `LeftFoot/RightFoot`，将小腿末端接头下延深扎入脚窝底槽并在关节区赋予 `LeftLeg↔LeftFoot` 线性渐变权重 |
| **真机视觉故障** | 载具机身/机炮大面积泛粉亮 | 载具/武器共用 `wpns_RAOE`，直接往该贴图写入局部自发光导致跨部件污染 | 还原 `wpns_RAOE` 为零自发光；拆出独立 `SubMesh` 并绑定独占空闲贴图槽（先审计全包材质 `_pbr_composite_tex` 引用） |
| **真机视觉故障** | 热改 UV 后贴图花屏/标志破碎/推进器错贴主迷彩 | 奇数顶点数 `vc` 未按 `align16(vc*40)` 读取 Stream 1 偏移（差 8B）；复用武器槽未清 `m_StreamData`；或合并掉了第 3 内构材质（如 `TR_Test_Mat_INST`） | 用 `(vc*stride0+15)&~15` 读写 UV；`m_StreamData` 清零再 `set_image(..., RGB24, 1)`；拆第 3 `SubMesh` 还原原生平铺内构并设 `Clamp=1`/`Repeat=0` |
| **真机视觉故障** | 阵营标过曝糊白/目镜竖条连亮/二次跑脚本 SubMesh 错乱 | `RAOE.B=220+` 经 $(\text{RAOE.B})^2$ 平方放大糊白；相邻部位未清零；或反复原地执行 `m_IndexBuffer` 重排冲散序号 | 精细黑缝标志压至 `RAOE.B=85~90`（黑缝置 `0`）、用背部 Raycast 融底并外抬 `+0.008m`；显式抹零邻区 `RAOE.B`；热修脚本强制从 `git show HEAD:...` 全量重算并重建双 Prefab `m_PreloadTable` |
| **真机视觉故障** | 与母体同场双方同时隐形 | 改了代码里的 CAB 变量，但保存前漏重映射 `env.file.files` 字典键名及 `m_StreamData.path` / `m_Container` | 四重物理隔离：分配独立 `NEW_CAB`、保存前 100% 重映射 `env.file.files` 与流路径、独立重命名 `<Bot>_GS/_lw` 根节点与 `cha_<bot>_00/01`、重建双 `m_Container` & `m_PreloadTable` |
| **真机视觉故障** | 缩小体格后变“蹲姿侏儒”且手指缩进前臂 | 在 Blender 中预缩网格/BindPose（如 `0.80x`），而宿主 Prefab 骨长仍为 `1.0x`，运行时骨链强行拉拽手腕与膝盖 | Blender 网格与 BindPose **严格保持 `1.0x` 与宿主骨头 1:1 吻合**；仅在 `generate_*_bundle.py` 修改双 Prefab 内 **`character_model` 的 `m_LocalScale`**（如 `0.82`）实现全层级真·等比例缩放 |
| **真机视觉故障** | FOC 角色头顶误亮/肩胸腿灯熄灭/紫眼紫标泛白 | 误用他人的通用 `*_e.jpg`；以及 `RAOE.B=255` + `_emissive_intensity_col.g=0.15` + 缺 `_emissive_range=1` 导致三通道过曝变白 | 基于 FBX 骨骼+UV 分区从自身漫反射图精准提取胸格栅/下胸月牙/肩弧/小腿条/腕槽，跳过裤衩/衣领/头顶；设 `RAOE.B=105~155`、`_emissive_range=1.0`、`_emissive_overbright_range=15.0`、`_emissive_intensity_col=(0.62, 0.02, 1.0)` |

---

## 3. 给后续 AI 智能体的标准执行提示词（可直接复制使用）

```markdown
请基于 `e:\Agent\TFTF-blender` 将新角色【<角色英文名/中文名>】（源模型：`<源目录路径>`，基模：`<基模ID，如 megatron_cin_rotf>`，目标 ID：`<bot_id>`）完整移植进离线版。

强制执行以下铁律，不得违规：
1. **必读协议与黄金模板**：先阅读 `re_notes/BOT_PORTING_SELF_CHECK_PROTOCOL.md` 与 `re_notes/THIRD_PARTY_3D_MODEL_PIPELINE.md`。贴图、Blender 对齐、Unity 检查、AssetBundle 嫁接必须分别复制并适配以下现有黄金脚本，**严禁从零重写**：
   - `tools/brawl/build_brawl_atlased_textures.py`
   - `tools/brawl/build_aligned_brawl_robot.py` 与 `tools/brawl/build_aligned_brawl_tank.py`
   - `toolchain/unity_build_project/Assets/Editor/BuildBrawlInspectionScene.cs`
   - `tools/brawl/generate_brawl_bundle.py`
2. **四阶段门禁硬拦截（Fail-Fast）**：每个阶段完成后，必须立即运行 `tools/validate_port_gates.py` 对应子命令：
   - 阶段 1 后运行：`python tools\validate_port_gates.py tex ...`
   - 阶段 2 后运行：`python tools\validate_port_gates.py fbx ...`
   - 阶段 3 后运行：`python tools\validate_port_gates.py mesh ...`
   - 阶段 4 后运行：`python tools\validate_port_gates.py bundle ...`
   只要任一阶段返回码非 0，**必须按 `[SELF-FIX]` 提示修复到 `[PASS]` 才能继续下一阶段**。
3. **强制视觉自查与用户拍板**：
   - Gate 1（Blender 贴图预览）、Gate 2（Blender 并排对比）、Gate 3（Unity 9+ 张动作与手部 Open/Curled 对比图）必须全部生成，并用 `read_file` 亲自看图核验（确认无炸裂、左右手 X 轴无反转、载具水平、手指随拳头开合）。
   - **Gate 3 全部通过并把对比图汇报给我确认通过前，严禁生成最终 AssetBundle 和打包 APK**。
```
