# TFTF 第三方 3D 角色移植防错与自纠偏执行协议 (Self-Check & Self-Correction Protocol)

> **定位**：[THIRD_PARTY_3D_MODEL_PIPELINE.md](file:///e:/Agent/TFTF-blender/re_notes/THIRD_PARTY_3D_MODEL_PIPELINE.md) 的**强约束执行层与防呆门禁**。
> **适用对象**：所有执行第三方向游戏移植新角色模型（Blender 对齐 → Unity 导出 → AssetBundle 嫁接 → APK 打包）的模型/智能体。

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
  - **每多边形 UV 解算与刚性权重截断**：`[0.004, 0.996]` 钳制防止跨图块撕裂；非变形装甲块 `w >= 0.65 -> 1.0` 截断消除果冻拉伸。
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
  - 所有使用中的材质球 `_Color`、`_emissive_intensity_col` 与 `_MainTex` UV Scale/Offset 保持正常基模尺度；载具保留原始有效骨骼哈希数组。
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
| **Gate 4 (bundle)** | `TEX_DATA_LEN` / `MAT_UV_SCALE` / `MAT_DARK_COLOR` | `Texture2D` 字节为空、UV 缩放未重置或有效材质 `_Color` 过黑 | 确保图集贴图写入 `image data`，重置 `_MainTex` Scale `(1,1)` 与有效颜色亮度 |

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
