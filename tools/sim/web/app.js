// TFTF Combat Simulator Client Application

let isRunning = false;
let tickTimer = null;
let currentInjectTarget = 0; // 0=P0, 1=P1
let p0Blocking = false;

// DOM Elements
const timerDisplay = document.getElementById("timerDisplay");
const stageTimerDisplay = document.getElementById("stageTimerDisplay");
const btnPlay = document.getElementById("btnPlay");
const btnPause = document.getElementById("btnPause");
const btnStep = document.getElementById("btnStep");
const btnReset = document.getElementById("btnReset");
const btnRecompile = document.getElementById("btnRecompile");
const announcementText = document.getElementById("announcementText");
const stageCenterAnnoText = document.getElementById("stageCenterAnnoText");

const p0BotSelect = document.getElementById("p0BotSelect");
const p1BotSelect = document.getElementById("p1BotSelect");
const p0Name = document.getElementById("p0Name");
const p1Name = document.getElementById("p1Name");
const stageP0Name = document.getElementById("stageP0Name");
const stageP1Name = document.getElementById("stageP1Name");
const p0BotId = document.getElementById("p0BotId");
const p1BotId = document.getElementById("p1BotId");
const p0HpText = document.getElementById("p0HpText");
const p1HpText = document.getElementById("p1HpText");
const stageP0HpText = document.getElementById("stageP0HpText");
const stageP1HpText = document.getElementById("stageP1HpText");
const p0HpFill = document.getElementById("p0HpFill");
const p1HpFill = document.getElementById("p1HpFill");
const stageP0HpFill = document.getElementById("stageP0HpFill");
const stageP1HpFill = document.getElementById("stageP1HpFill");
const p0ManaText = document.getElementById("p0ManaText");
const p1ManaText = document.getElementById("p1ManaText");
const p0ManaFill = document.getElementById("p0ManaFill");
const p1ManaFill = document.getElementById("p1ManaFill");
const p0BuffTray = document.getElementById("p0BuffTray");
const p1BuffTray = document.getElementById("p1BuffTray");

// 擂台主视区能量段与机甲角色
const p0ManaSeg1 = document.getElementById("p0ManaSeg1");
const p0ManaSeg2 = document.getElementById("p0ManaSeg2");
const p0ManaSeg3 = document.getElementById("p0ManaSeg3");
const p1ManaSeg1 = document.getElementById("p1ManaSeg1");
const p1ManaSeg2 = document.getElementById("p1ManaSeg2");
const p1ManaSeg3 = document.getElementById("p1ManaSeg3");

const fighterP0 = document.getElementById("fighterP0");
const fighterP1 = document.getElementById("fighterP1");
const shieldP0 = document.getElementById("shieldP0");
const shieldP1 = document.getElementById("shieldP1");

const floaterContainer = document.getElementById("floaterContainer");
const logTerminal = document.getElementById("logTerminal");
const btnClearLogs = document.getElementById("btnClearLogs");

const btnSP1 = document.getElementById("btnSP1");
const btnSP2 = document.getElementById("btnSP2");
const btnSP3 = document.getElementById("btnSP3");
const btnToggleBlock = document.getElementById("btnToggleBlock");
const btnDashBack = document.getElementById("btnDashBack");
const btnSidestep = document.getElementById("btnSidestep");
const btnCombo5 = document.getElementById("btnCombo5");

// Modal Elements
const injectModal = document.getElementById("injectModal");
const modalTitle = document.getElementById("modalTitle");
const modalBuffSelect = document.getElementById("modalBuffSelect");
const customBuffGroup = document.getElementById("customBuffGroup");
const modalCustomBuffId = document.getElementById("modalCustomBuffId");
const modalBuffDur = document.getElementById("modalBuffDur");
const modalBuffStacks = document.getElementById("modalBuffStacks");
const btnModalClose = document.getElementById("btnModalClose");
const btnModalCancel = document.getElementById("btnModalCancel");
const btnModalApply = document.getElementById("btnModalApply");

// ---------------------------------------------------------------------------
// 初始化与数据加载
// ---------------------------------------------------------------------------
async function init() {
    await loadBots();
    setupEventHandlers();
    fetchState();
}

async function loadBots() {
    try {
        const res = await fetch("/api/bots");
        const bots = await res.json();
        p0BotSelect.innerHTML = "";
        p1BotSelect.innerHTML = "";

        bots.forEach(b => {
            const opt0 = document.createElement("option");
            opt0.value = b.bot_id;
            opt0.textContent = `${b.name_zh} (${b.bot_id})`;
            if (b.bot_id === "optimusprime_cin_tf") opt0.selected = true;
            p0BotSelect.appendChild(opt0);

            const opt1 = document.createElement("option");
            opt1.value = b.bot_id;
            opt1.textContent = `${b.name_zh} (${b.bot_id})`;
            if (b.bot_id === "bonecrusher_cin_rotf") opt1.selected = true;
            p1BotSelect.appendChild(opt1);
        });

        if (p0BotSelect.selectedIndex >= 0) {
            const t0 = p0BotSelect.options[p0BotSelect.selectedIndex].text.split(" (")[0];
            if (p0Name) p0Name.textContent = t0;
            if (stageP0Name) stageP0Name.textContent = t0;
        }
        if (p1BotSelect.selectedIndex >= 0) {
            const t1 = p1BotSelect.options[p1BotSelect.selectedIndex].text.split(" (")[0];
            if (p1Name) p1Name.textContent = t1;
            if (stageP1Name) stageP1Name.textContent = t1;
        }
    } catch (e) {
        console.error("Failed to load bots:", e);
    }
}

// ---------------------------------------------------------------------------
// 状态轮询与渲染
// ---------------------------------------------------------------------------
async function fetchState() {
    try {
        const res = await fetch("/api/state");
        const data = await res.json();
        renderState(data);
    } catch (e) {
        console.error("fetchState error:", e);
    }
}

function renderState(data) {
    if (!data || !data.p0) return;

    // 1. 时钟格式化 (ms -> mm:ss.ms)
    const ms = data.clock_ms || 0;
    const totalSec = Math.floor(ms / 1000);
    const m = String(Math.floor(totalSec / 60)).padStart(2, "0");
    const s = String(totalSec % 60).padStart(2, "0");
    const remMs = String(ms % 1000).padStart(3, "0");
    const formattedTime = `${m}:${s}.${remMs}`;
    timerDisplay.textContent = formattedTime;
    if (stageTimerDisplay) stageTimerDisplay.textContent = formattedTime;

    // 2. 广播条与中央擂台通知横幅
    if (data.announcement) {
        announcementText.textContent = data.announcement;
        if (stageCenterAnnoText) stageCenterAnnoText.textContent = `⚡ ${data.announcement}`;
    }

    // 3. 护盾与格挡状态联动
    if (shieldP0) shieldP0.classList.toggle("active", !!data.p0.is_blocking);
    if (shieldP1) shieldP1.classList.toggle("active", !!data.p1.is_blocking);

    // 4. 1P 与 2P 状态
    renderPlayer(0, data.p0);
    renderPlayer(1, data.p1);

    // 5. SP 按钮可用性
    const p0Mana = data.p0.mana || 0;
    btnSP1.disabled = (p0Mana < 1.0);
    btnSP2.disabled = (p0Mana < 2.0);
    btnSP3.disabled = (p0Mana < 3.0);
    btnSP1.style.opacity = p0Mana >= 1.0 ? "1" : "0.4";
    btnSP2.style.opacity = p0Mana >= 2.0 ? "1" : "0.4";
    btnSP3.style.opacity = p0Mana >= 3.0 ? "1" : "0.4";

    // 6. 渲染战斗浮字 (Floaters)
    if (data.floaters && data.floaters.length > 0) {
        data.floaters.forEach(spawnFloater);
    }

    // 7. 渲染日志 (Logs)
    if (data.logs && data.logs.length > 0) {
        data.logs.forEach(appendLog);
    }
}

function updateManaSegments(isP0, mana) {
    const seg1 = isP0 ? p0ManaSeg1 : p1ManaSeg1;
    const seg2 = isP0 ? p0ManaSeg2 : p1ManaSeg2;
    const seg3 = isP0 ? p0ManaSeg3 : p1ManaSeg3;
    if (!seg1 || !seg2 || !seg3) return;

    // 段1 (0.0 ~ 1.0)
    const fill1 = seg1.querySelector(".seg-fill");
    const p1 = Math.min(100, Math.max(0, mana * 100));
    fill1.style.width = `${p1}%`;
    seg1.classList.toggle("is-full", mana >= 1.0);

    // 段2 (1.0 ~ 2.0)
    const fill2 = seg2.querySelector(".seg-fill");
    const p2 = Math.min(100, Math.max(0, (mana - 1.0) * 100));
    fill2.style.width = `${p2}%`;
    seg2.classList.toggle("is-full", mana >= 2.0);

    // 段3 (2.0 ~ 3.0)
    const fill3 = seg3.querySelector(".seg-fill");
    const p3 = Math.min(100, Math.max(0, (mana - 2.0) * 100));
    fill3.style.width = `${p3}%`;
    seg3.classList.toggle("is-full", mana >= 3.0);
}

function renderPlayer(idx, p) {
    const isP0 = (idx === 0);
    const nameEl = isP0 ? p0Name : p1Name;
    const stageNameEl = isP0 ? stageP0Name : stageP1Name;
    const botIdEl = isP0 ? p0BotId : p1BotId;
    const hpTextEl = isP0 ? p0HpText : p1HpText;
    const stageHpTextEl = isP0 ? stageP0HpText : stageP1HpText;
    const hpFillEl = isP0 ? p0HpFill : p1HpFill;
    const stageHpFillEl = isP0 ? stageP0HpFill : stageP1HpFill;
    const manaTextEl = isP0 ? p0ManaText : p1ManaText;
    const manaFillEl = isP0 ? p0ManaFill : p1ManaFill;
    const buffTrayEl = isP0 ? p0BuffTray : p1BuffTray;

    botIdEl.textContent = p.bot_id;

    // HP 百分比
    const hpPct = Math.max(0, Math.min(100, (p.hp / p.max_hp) * 100));
    if (hpFillEl) hpFillEl.style.width = `${hpPct}%`;
    if (stageHpFillEl) stageHpFillEl.style.width = `${hpPct}%`;
    const hpFormatted = `${Math.round(p.hp)} / ${Math.round(p.max_hp)}`;
    if (hpTextEl) hpTextEl.textContent = hpFormatted;
    if (stageHpTextEl) stageHpTextEl.textContent = hpFormatted;

    // Mana 能量段更新
    updateManaSegments(isP0, p.mana);

    // 渲染 Buff 徽章
    if (!p.buffs || p.buffs.length === 0) {
        buffTrayEl.innerHTML = '<span class="buff-empty">暂无状态</span>';
    } else {
        buffTrayEl.innerHTML = "";
        p.buffs.forEach(b => {
            const badge = document.createElement("div");
            const isPerm = (b.rem_ms < 0);
            badge.className = `buff-badge ${isPerm ? "is-perm" : ""}`;

            let icon = "✨";
            if (b.id.includes("bleed")) icon = "🩸";
            else if (b.id.includes("shock")) icon = "⚡";
            else if (b.id.includes("armor")) icon = "🛡️";
            else if (b.id.includes("atk") || b.id.includes("melee")) icon = "⚔️";
            else if (b.id.includes("purify")) icon = "🌟";
            else if (b.id.includes("stun")) icon = "💫";
            else if (b.id.includes("dodge") || b.id.includes("evade")) icon = "💨";

            const timeStr = isPerm ? "永久" : `${(b.rem_ms / 1000).toFixed(1)}s`;
            const stackStr = (b.stacks > 1) ? ` x${b.stacks}` : "";

            badge.innerHTML = `
                <span>${icon}</span>
                <span><strong>${b.id}</strong>${stackStr} [${timeStr}]</span>
                <span class="b-close" title="驱散此Buff" onclick="removeBuff(${idx}, '${b.id}')">&times;</span>
            `;
            buffTrayEl.appendChild(badge);
        });
    }
}

// ---------------------------------------------------------------------------
// 战斗浮字与日志系统
// ---------------------------------------------------------------------------
function spawnFloater(f) {
    const el = document.createElement("div");
    el.className = `floater floater-p${f.pidx}`;

    let typeClass = "floater-dmg";
    let prefix = "-";
    if (f.type === 1) { typeClass = "floater-crit"; prefix = "⚡ 暴击 -"; }
    else if (f.type === 2) { typeClass = "floater-heal"; prefix = "💚 +"; }
    else if (f.type === 3) { typeClass = "floater-mana"; prefix = "⚡ +"; }
    else if (f.type === 4 || f.type === 5) { typeClass = "floater-text"; prefix = ""; }

    el.classList.add(typeClass);
    const valText = f.val > 0 ? Math.round(f.val) : "";
    el.textContent = `${prefix}${valText} ${f.text || ""}`;

    // 受击战士轻微晃动
    const victim = (f.pidx === 0) ? fighterP0 : fighterP1;
    if (victim && (f.type === 0 || f.type === 1)) {
        victim.classList.remove("hit-react");
        void victim.offsetWidth;
        victim.classList.add("hit-react");
        setTimeout(() => victim.classList.remove("hit-react"), 220);
    }

    // 随机微调左右位置避免文字完全重叠
    const offset = (Math.random() - 0.5) * 36;
    el.style.transform = `translateX(${offset}px)`;

    floaterContainer.appendChild(el);
    setTimeout(() => el.remove(), 1100);
}

function appendLog(line) {
    const p = document.createElement("div");
    p.className = "log-line";
    if (line.includes("OPTIMUS_MV") || line.includes("MEGATRON") || line.includes("PROWL")) {
        p.classList.add("log-skill");
    } else if (line.includes("HIT") || line.includes("ATTACK")) {
        p.classList.add("log-hit");
    } else {
        p.classList.add("log-sim");
    }
    p.textContent = `[LOG] ${line}`;
    logTerminal.appendChild(p);
    logTerminal.scrollTop = logTerminal.scrollHeight;
}

// ---------------------------------------------------------------------------
// 交互事件处理
// ---------------------------------------------------------------------------
function setupEventHandlers() {
    // 时钟控制
    btnPlay.addEventListener("click", () => {
        if (!isRunning) {
            isRunning = true;
            btnPlay.textContent = "▶ 运行中...";
            btnPlay.style.background = "#2ea043";
            tickTimer = setInterval(async () => {
                await fetch("/api/tick", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ dt_ms: 100 })
                });
                fetchState();
            }, 100);
        }
    });

    btnPause.addEventListener("click", () => {
        if (isRunning) {
            isRunning = false;
            clearInterval(tickTimer);
            btnPlay.textContent = "▶ 开始模拟";
            btnPlay.style.background = "#238636";
        }
    });

    btnStep.addEventListener("click", async () => {
        await fetch("/api/tick", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ dt_ms: 100 })
        });
        fetchState();
    });

    btnReset.addEventListener("click", async () => {
        await fetch("/api/reset", { method: "POST" });
        fetchState();
        showToast("战斗已重置");
    });

    // 代码热重载 (0.3s 重新编译)
    btnRecompile.addEventListener("click", async () => {
        btnRecompile.textContent = "⏳ 正在重编...";
        try {
            const res = await fetch("/api/recompile", { method: "POST" });
            const data = await res.json();
            if (data.ok) {
                showToast("⚡ 技能代码热重载成功 (0.3s)！");
            } else {
                alert("编译失败:\n" + data.message);
            }
        } catch (e) {
            alert("热重载通信异常: " + e);
        } finally {
            btnRecompile.textContent = "⚡ 热重载技能代码";
            fetchState();
        }
    });

    // 角色下拉选择
    p0BotSelect.addEventListener("change", applyBotMatchup);
    p1BotSelect.addEventListener("change", applyBotMatchup);

    // 出招按钮群
    document.querySelectorAll(".btn-action").forEach(btn => {
        btn.addEventListener("click", () => {
            const action = parseInt(btn.dataset.action);
            const isLast = parseInt(btn.dataset.last);
            if (!isNaN(action)) {
                sendAttack(0, action, 0, isLast);
            }
        });
    });

    // 切换格挡
    btnToggleBlock.addEventListener("click", async () => {
        p0Blocking = !p0Blocking;
        btnToggleBlock.textContent = p0Blocking ? "🛡️ 正在格挡 (点击解除)" : "🛡️ 切换格挡";
        btnToggleBlock.style.background = p0Blocking ? "#5c2b99" : "#21262d";
        await fetch("/api/block", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ player: 0, blocking: p0Blocking ? 1 : 0 })
        });
        fetchState();
    });

    // 闪避按钮绑定 (后闪与侧闪)
    if (btnDashBack) {
        btnDashBack.addEventListener("click", () => sendDodge(0, 0));
    }
    if (btnSidestep) {
        btnSidestep.addEventListener("click", () => sendDodge(0, 1));
    }

    // 一键 5 连击 (L-L-L-M-M)
    btnCombo5.addEventListener("click", async () => {
        const combo = [
            { act: 1, last: 0 },
            { act: 1, last: 0 },
            { act: 1, last: 0 },
            { act: 2, last: 0 },
            { act: 2, last: 1 },
        ];
        for (let i = 0; i < combo.length; i++) {
            await sendAttack(0, combo[i].act, i, combo[i].last);
            await new Promise(r => setTimeout(r, 180));
        }
    });

    // 预设剧本按钮
    document.getElementById("presetOptimus").addEventListener("click", setupPresetOptimus);
    document.getElementById("presetMegatron").addEventListener("click", setupPresetMegatron);
    document.getElementById("presetProwl").addEventListener("click", setupPresetProwl);
    const presetBumblebee = document.getElementById("presetBumblebee");
    if (presetBumblebee) {
        presetBumblebee.addEventListener("click", setupPresetBumblebee);
    }

    // 日志清空
    btnClearLogs.addEventListener("click", () => {
        logTerminal.innerHTML = "";
    });

    // 注入 Buff 模态框
    document.getElementById("btnInjectP0").addEventListener("click", () => openInjectModal(0));
    document.getElementById("btnInjectP1").addEventListener("click", () => openInjectModal(1));
    btnModalClose.addEventListener("click", closeInjectModal);
    btnModalCancel.addEventListener("click", closeInjectModal);

    modalBuffSelect.addEventListener("change", () => {
        customBuffGroup.style.display = (modalBuffSelect.value === "custom") ? "flex" : "none";
    });

    btnModalApply.addEventListener("click", async () => {
        let modId = modalBuffSelect.value;
        if (modId === "custom") {
            modId = modalCustomBuffId.value.trim();
        }
        const dur = parseFloat(modalBuffDur.value) || 6.0;
        const stacks = parseInt(modalBuffStacks.value) || 1;

        if (modId) {
            await fetch("/api/inject_buff", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ target: currentInjectTarget, mod_id: modId, dur, stacks })
            });
            fetchState();
            closeInjectModal();
            showToast(`已向 ${currentInjectTarget === 0 ? "1P" : "2P"} 注入 ${modId} x${stacks}`);
        }
    });
}

// ---------------------------------------------------------------------------
// 预设场景一键测试 (Presets)
// ---------------------------------------------------------------------------
async function setupPresetOptimus() {
    p0BotSelect.value = "optimusprime_cin_tf";
    p1BotSelect.value = "bonecrusher_cin_rotf";
    await applyBotMatchup();
    // 注入两层流血
    await fetch("/api/inject_buff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: 0, mod_id: "dmg_bleed", dur: 6.0, stacks: 2 })
    });
    showToast("📌 场景已装载: 斗擎挂 2 层流血！点【▶ 开始模拟】观察 1s 后净化");
    fetchState();
}

async function setupPresetMegatron() {
    p0BotSelect.value = "megatron_gs_leader2015";
    p1BotSelect.value = "sharkticon_gs_demolition";
    await applyBotMatchup();
    // 威震天充能 3 层
    await fetch("/api/inject_buff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: 0, mod_id: "megatron_fusion_cannon", dur: -1.0, stacks: 3 })
    });
    // 鲨鱼精挂感电与破甲
    await fetch("/api/inject_buff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: 1, mod_id: "megatron_sp3_shock", dur: 8.0, stacks: 1 })
    });
    await fetch("/api/inject_buff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: 1, mod_id: "megatron_sp1_armor_break", dur: 8.0, stacks: 1 })
    });
    showToast("📌 场景已装载: 威震天满充能 vs 鲨鱼精带减益！点击【💥 破防重击】验证融合");
    fetchState();
}

async function setupPresetProwl() {
    p0BotSelect.value = "prowl_gs_deluxe2016";
    p1BotSelect.value = "bonecrusher_cin_rotf";
    await applyBotMatchup();
    showToast("📌 场景已装载: 警车！点击【💨 后闪】开始充能蓄力，出手时转换为近战增益");
    fetchState();
}

async function setupPresetBumblebee() {
    p0BotSelect.value = "bumblebee_gs_kabam";
    p1BotSelect.value = "bonecrusher_cin_rotf";
    await applyBotMatchup();
    showToast("📌 场景已装载: 小黄蜂！点击【💨 后闪】获得规避，点击【💨 侧闪】叠加暴击增益");
    fetchState();
}

async function applyBotMatchup() {
    const p0 = p0BotSelect.value;
    const p1 = p1BotSelect.value;
    const p0Text = p0BotSelect.options[p0BotSelect.selectedIndex].text.split(" (")[0];
    const p1Text = p1BotSelect.options[p1BotSelect.selectedIndex].text.split(" (")[0];

    if (p0Name) p0Name.textContent = p0Text;
    if (p1Name) p1Name.textContent = p1Text;
    if (stageP0Name) stageP0Name.textContent = p0Text;
    if (stageP1Name) stageP1Name.textContent = p1Text;

    await fetch("/api/init", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ p0_bot_id: p0, p1_bot_id: p1, p0_hp: 15000, p1_hp: 15000, p0_atk: 1000, p1_atk: 1000 })
    });
    fetchState();
}

async function sendAttack(attacker, action, hit_idx, is_last) {
    const atkerFighter = (attacker === 0) ? fighterP0 : fighterP1;
    if (atkerFighter) {
        atkerFighter.classList.remove("attack-react");
        void atkerFighter.offsetWidth;
        atkerFighter.classList.add("attack-react");
        setTimeout(() => atkerFighter.classList.remove("attack-react"), 250);
    }

    await fetch("/api/attack", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ attacker, action, hit_idx, is_last, blocked: 0 })
    });
    fetchState();
}

async function sendDodge(player, type) {
    const fighter = (player === 0) ? fighterP0 : fighterP1;
    if (fighter) {
        fighter.classList.remove("dodge-react");
        void fighter.offsetWidth;
        fighter.classList.add("dodge-react");
        setTimeout(() => fighter.classList.remove("dodge-react"), 350);
    }

    await fetch("/api/dodge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ player, type })
    });
    fetchState();
}

window.removeBuff = async function(target, mod_id) {
    await fetch("/api/remove_buff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target, mod_id, count: 1 })
    });
    fetchState();
};

function openInjectModal(target) {
    currentInjectTarget = target;
    modalTitle.textContent = `💉 手动注入状态 -> ${target === 0 ? "1P 我方" : "2P 敌方"}`;
    injectModal.style.display = "flex";
}

function closeInjectModal() {
    injectModal.style.display = "none";
}

function showToast(msg) {
    const toast = document.getElementById("toast");
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 2200);
}

// 启动应用
document.addEventListener("DOMContentLoaded", init);
