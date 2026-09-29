/* Base Relic Placement and Persistence Handler */

typedef struct {
    const char *id;
    const char *model_id;
    const char *img;
    const char *name_en;
    const char *name_zh;
} RelicDef;

static const RelicDef g_relic_defs[] = {
    { "relic_immobilizer", "rlc3", "immobilizer", "Immobilizer", "禁锢定身器" },
    { "relic_allspark", "rlc2", "allspark", "The AllSpark", "火种源" },
    { "relic_covenant_primus", "rlc7", "covenant_primus", "Covenant of Primus", "普神之约" },
    { "relic_matrix_of_leadership", "rlc14", "matrix_of_leadership", "Matrix of Leadership", "领导模块" },
    { "relic_origin_matrix", "rlc8", "origin_matrix", "Origin Matrix", "原初矩阵" },
    { "relic_ancienthead", "rlc4", "ancienthead", "Ancient Titan Core", "远古巨神核心" },
    { "relic_solus_forge", "rlc5", "solus_forge", "Forge of Solus Prime", "索拉斯之锤" },
    { "relic_dark_energon_crystal", "rlc6", "dark_energon_crystal", "Dark Energon Crystal", "黑暗能量水晶" },
    { "relic_unstable_energon_crystal", "rlc11", "unstable_energon_crystal", "Unstable Energon Crystal", "不稳定能量水晶" },
    { "relic_stasis_generator", "rlc20", "stasis_generator", "Stasis Generator", "停滞力场发生器" },
    { "relic_cloaking_field", "rlc19", "cloaking_field", "Cloaking Field Generator", "隐形发生器" },
    { "relic_fallen_titan_hand", "rlc9", "fallen_titan_hand", "Fallen Titan Hand", "堕落泰坦之手" },
    { "relic_ancient_tablet", "rlc20", "ancient_tablet", "Cybertronian Tablet", "赛博坦古老石板" },
    { "relic_goldendisk", "rlc22", "goldendisk", "Golden Disk", "金盘" },
    { "relic_shattered_disk", "rlc29", "shattered_disk_t4", "Shattered Disk", "破碎之盘" },
    { "relic_statue_op", "rlc11", "statue_op_c", "Optimus Prime Monument", "擎天柱纪念圣像" },
    { "relic_statue_megatron", "rlc13", "statue_megatron", "Megatron Monument", "威震天纪念雕像" },
    { "relic_statue_hotrod", "rlc14", "statue_hotrod", "Hot Rod Monument", "热破英勇塑像" },
    { "relic_statue_solus", "rlc28", "statue_solus_g", "Solus Prime Monument", "索拉斯天尊塑像" },
    { "relic_jazz", "rlc_jazz_gs", "relic_jazz_t4", "Jazz Signature Relic", "爵士专属遗迹" },
    { "relic_optimus_primal", "rlc34d", "relic_optimus_primal_t4", "Optimus Primal Relic", "擎天圣专属遗迹" },
    { "relic_megatron", "rlc36d", "relic_megatron_t4", "Megatron Signature Relic", "威震天霸权遗迹" },
    { "relic_bumblebee", "rlc35d", "relic_bumblebee_t4", "Bumblebee Relic", "大黄蜂专属遗迹" },
    { "relic_blaster", "rlc33d", "relic_blaster_t4", "Blaster Sonic Relic", "录音机声波遗迹" },
    { "relic_cheetor", "rlc37d", "relic_cheetor_t4", "Cheetor Velocity Relic", "黄豹勇士极速遗迹" },
    { "relic_hound", "rlc38d", "relic_hound_t4", "Hound Hologram Relic", "探长全息遗迹" },
    { "relic_galvatron", "rlc39d", "relic_galvatron_t4", "Galvatron Particle Relic", "惊破天粒子遗迹" },
    { "relic_kickback", "rlc40d", "relic_kickback_t4", "Kickback Hive Relic", "反冲虫巢遗迹" },
    { "relic_alliance_victory", "rlc41d", "relic_ave_t4", "Alliance Victory Relic", "联盟凯旋勋章" },
    { "relic_raid_champion", "rlc30d", "relic_raid_t4", "Raid Champion Relic", "突袭冠军遗迹" },
    { NULL, NULL, NULL, NULL, NULL }
};

static const RelicDef* find_relic_def(const char *rid) {
    if (!rid || !rid[0]) return &g_relic_defs[1]; /* fallback to allspark */
    for (int i = 0; g_relic_defs[i].id; i++) {
        if (strcmp(g_relic_defs[i].id, rid) == 0) return &g_relic_defs[i];
    }
    return &g_relic_defs[1];
}

typedef struct {
    const char *sock_id;
    int x;
    int y;
    char relic_id[64];
} BaseRelicSlot;

static BaseRelicSlot g_base_relic_slots[4] = {
    { "sock_relic_20_33", 20, 33, "relic_dark_energon_crystal" },
    { "sock_relic_20_39", 20, 39, "relic_unstable_energon_crystal" },
    { "sock_relic_30_33", 30, 33, "relic_allspark" },
    { "sock_relic_30_39", 30, 39, "relic_matrix_of_leadership" }
};

static const char *g_base_relic_paths[] = {
    "/data/data/com.kabam.bigrobot/files/base_relics.json",
    "/sdcard/Android/data/com.kabam.bigrobot/files/base_relics.json",
    NULL
};

static int g_base_relics_loaded = 0;
static int g_base_relics_modified = 0;

static void load_base_relics(void) {
    if (g_base_relics_loaded) return;
    g_base_relics_loaded = 1;
    for (int p = 0; g_base_relic_paths[p]; p++) {
        FILE *fp = fopen(g_base_relic_paths[p], "rb");
        if (fp) {
            char buf[2048];
            size_t rd = fread(buf, 1, sizeof(buf) - 1, fp);
            fclose(fp);
            if (rd > 0) {
                buf[rd] = 0;
                for (int s = 0; s < 4; s++) {
                    char val[64] = {0};
                    if (json_string(buf, buf + rd, g_base_relic_slots[s].sock_id, val, sizeof(val))) {
                        if (val[0]) {
                            snprintf(g_base_relic_slots[s].relic_id, sizeof(g_base_relic_slots[s].relic_id), "%s", val);
                            g_base_relics_modified = 1;
                            logmsg("load_base_relics: %s -> %s", g_base_relic_slots[s].sock_id, val);
                        }
                    }
                }
                return;
            }
        }
    }
}

static void save_base_relics(void) {
    char json_buf[1024];
    int len = snprintf(json_buf, sizeof(json_buf),
        "{\n"
        "  \"%s\": \"%s\",\n"
        "  \"%s\": \"%s\",\n"
        "  \"%s\": \"%s\",\n"
        "  \"%s\": \"%s\"\n"
        "}\n",
        g_base_relic_slots[0].sock_id, g_base_relic_slots[0].relic_id,
        g_base_relic_slots[1].sock_id, g_base_relic_slots[1].relic_id,
        g_base_relic_slots[2].sock_id, g_base_relic_slots[2].relic_id,
        g_base_relic_slots[3].sock_id, g_base_relic_slots[3].relic_id
    );
    for (int p = 0; g_base_relic_paths[p]; p++) {
        FILE *fp = fopen(g_base_relic_paths[p], "wb");
        if (fp) {
            fwrite(json_buf, 1, len, fp);
            fclose(fp);
            logmsg("save_base_relics: written to %s", g_base_relic_paths[p]);
        }
    }
}

static const char g_fixed_placements[] = "\"sock_boss_25_30\": {\"entityType\": \"boss\", \"parentEntityType\": \"bcg\", \"key\": \"megatron_gs_leader2015\", \"character\": \"megatron_gs_leader2015\", \"rank\": 5, \"level\": 50, \"sig_lvl\": 60, \"position\": {\"x\": 25, \"y\": 30}}, \"sock_boss_22_33\": {\"entityType\": \"boss\", \"parentEntityType\": \"bcg\", \"key\": \"megatronus_gs_kabam\", \"character\": \"megatronus_gs_kabam\", \"rank\": 5, \"level\": 50, \"sig_lvl\": 60, \"position\": {\"x\": 22, \"y\": 33}}, \"sock_boss_28_33\": {\"entityType\": \"boss\", \"parentEntityType\": \"bcg\", \"key\": \"soundwave_gs\", \"character\": \"soundwave_gs\", \"rank\": 5, \"level\": 50, \"sig_lvl\": 30, \"position\": {\"x\": 28, \"y\": 33}}, \"sock_boss_22_39\": {\"entityType\": \"boss\", \"parentEntityType\": \"bcg\", \"key\": \"galvatron_gs_voyager2016\", \"character\": \"galvatron_gs_voyager2016\", \"rank\": 5, \"level\": 50, \"sig_lvl\": 40, \"position\": {\"x\": 22, \"y\": 39}}, \"sock_boss_25_36\": {\"entityType\": \"boss\", \"parentEntityType\": \"bcg\", \"key\": \"megatron_cin_rotf\", \"character\": \"megatron_cin_rotf\", \"rank\": 5, \"level\": 50, \"sig_lvl\": 60, \"position\": {\"x\": 25, \"y\": 36}}, \"sock_boss_25_42\": {\"entityType\": \"boss\", \"parentEntityType\": \"bcg\", \"key\": \"arcee_gs_deluxe2014\", \"character\": \"arcee_gs_deluxe2014\", \"rank\": 5, \"level\": 50, \"sig_lvl\": 40, \"position\": {\"x\": 25, \"y\": 42}}, \"sock_boss_28_39\": {\"entityType\": \"boss\", \"parentEntityType\": \"bcg\", \"key\": \"shockwave_gs\", \"character\": \"shockwave_gs\", \"rank\": 5, \"level\": 50, \"sig_lvl\": 60, \"position\": {\"x\": 28, \"y\": 39}}, \"sock_tower_25_30\": {\"entityType\": \"tower\", \"parentEntityType\": \"bcg\", \"key\": \"mods_primemodule_01\", \"character\": \"mods_primemodule_01\", \"rank\": 4, \"level\": 50, \"position\": {\"x\": 25, \"y\": 30}}, \"sock_tower_22_33\": {\"entityType\": \"tower\", \"parentEntityType\": \"bcg\", \"key\": \"mods_paralyzer_01\", \"character\": \"mods_paralyzer_01\", \"rank\": 4, \"level\": 50, \"position\": {\"x\": 22, \"y\": 33}}, \"sock_tower_28_33\": {\"entityType\": \"tower\", \"parentEntityType\": \"bcg\", \"key\": \"mods_brawlersfury_01\", \"character\": \"mods_brawlersfury_01\", \"rank\": 4, \"level\": 50, \"position\": {\"x\": 28, \"y\": 33}}, \"sock_tower_25_36\": {\"entityType\": \"tower\", \"parentEntityType\": \"bcg\", \"key\": \"mods_tacticianstrick_02\", \"character\": \"mods_tacticianstrick_02\", \"rank\": 4, \"level\": 50, \"position\": {\"x\": 25, \"y\": 36}}, \"sock_tower_22_39\": {\"entityType\": \"tower\", \"parentEntityType\": \"bcg\", \"key\": \"mods_harmaccelerator_01\", \"character\": \"mods_harmaccelerator_01\", \"rank\": 4, \"level\": 50, \"position\": {\"x\": 22, \"y\": 39}}, \"sock_tower_28_39\": {\"entityType\": \"tower\", \"parentEntityType\": \"bcg\", \"key\": \"mods_strangerefractor_01\", \"character\": \"mods_strangerefractor_01\", \"rank\": 4, \"level\": 50, \"position\": {\"x\": 28, \"y\": 39}}, \"sock_tower_25_42\": {\"entityType\": \"tower\", \"parentEntityType\": \"bcg\", \"key\": \"mods_laserguidance_01\", \"character\": \"mods_laserguidance_01\", \"rank\": 4, \"level\": 50, \"position\": {\"x\": 25, \"y\": 42}}, \"sock_bldg_19_26\": {\"entityType\": \"building\", \"parentEntityType\": \"building\", \"key\": \"bldg_away_team\", \"rank\": 3, \"level\": 3, \"position\": {\"x\": 19, \"y\": 26}}, \"sock_bldg_23_24\": {\"entityType\": \"building\", \"parentEntityType\": \"building\", \"key\": \"bldg_crystal_premium\", \"rank\": 3, \"level\": 3, \"position\": {\"x\": 23, \"y\": 24}}, \"sock_bldg_25_23\": {\"entityType\": \"building\", \"parentEntityType\": \"building\", \"key\": \"bldg_battle_centre\", \"rank\": 3, \"level\": 3, \"position\": {\"x\": 25, \"y\": 23}}, \"sock_bldg_27_24\": {\"entityType\": \"building\", \"parentEntityType\": \"building\", \"key\": \"bldg_crystal_free\", \"rank\": 3, \"level\": 3, \"position\": {\"x\": 27, \"y\": 24}}, \"sock_bldg_29_25\": {\"entityType\": \"building\", \"parentEntityType\": \"building\", \"key\": \"bldg_alliance_help\", \"rank\": 3, \"level\": 3, \"position\": {\"x\": 29, \"y\": 25}}";

static void append_relic_socket_json(char *buf, size_t buf_size, int *offset, const BaseRelicSlot *slot) {
    const RelicDef *def = find_relic_def(slot->relic_id);
    char single[1024];
    int n = snprintf(single, sizeof(single),
        ",\"%s\":{\"entityType\":\"building\",\"parentEntityType\":\"building\","
        "\"id\":\"%s\",\"key\":\"%s\",\"modelId\":\"%s\","
        "\"name\":\"%s\",\"name_loc\":{\"en\":\"%s\",\"zh-Hans\":\"%s\"},"
        "\"img\":\"%s\",\"rank\":5,\"level\":50,"
        "\"position\":{\"x\":%d,\"y\":%d}}",
        slot->sock_id, def->id, def->id, def->model_id,
        def->name_zh, def->name_en, def->name_zh,
        def->img, slot->x, slot->y
    );
    if (*offset + n < (int)buf_size) {
        memcpy(buf + *offset, single, n);
        *offset += n;
        buf[*offset] = 0;
    }
}

static char *build_placements_response(size_t *out_len) {
    load_base_relics();
    size_t alloc_sz = 16384;
    char *buf = (char*)malloc(alloc_sz);
    if (!buf) return NULL;
    int off = snprintf(buf, alloc_sz, "{\"error\":null,\"result\":{\"success\":true,\"placements\":{%s", g_fixed_placements);
    for (int s = 0; s < 4; s++) {
        if (g_base_relic_slots[s].relic_id[0]) {
            append_relic_socket_json(buf, alloc_sz, &off, &g_base_relic_slots[s]);
        }
    }
    off += snprintf(buf + off, alloc_sz - off, "}}}");
    *out_len = off;
    return buf;
}

static int split_slash_tokens(const char *path, char tokens[12][64]) {
    int count = 0;
    const char *cur = path;
    while (*cur && count < 12) {
        while (*cur == '/') cur++;
        if (!*cur) break;
        const char *start = cur;
        while (*cur && *cur != '/' && *cur != '?' && *cur != ' ') cur++;
        size_t len = (size_t)(cur - start);
        if (len >= 64) len = 63;
        memcpy(tokens[count], start, len);
        tokens[count][len] = 0;
        count++;
    }
    return count;
}

static const unsigned char* handle_base_action(const char *p, Out *o, size_t *outn) {
    load_base_relics();
    char tokens[12][64];
    int tc = split_slash_tokens(p, tokens);
    if (strstr(p, "/base/place")) {
        /* /base/place/<base_type>/<socket_type>/<entityKey>/<missionId>/<x>/<y>/<socketId> */
        const char *sock_id = (tc >= 1) ? tokens[tc - 1] : "";
        const char *relic_id = (tc >= 5) ? tokens[4] : "";
        for (int s = 0; s < 4; s++) {
            if (strcmp(g_base_relic_slots[s].sock_id, sock_id) == 0) {
                snprintf(g_base_relic_slots[s].relic_id, sizeof(g_base_relic_slots[s].relic_id), "%s", relic_id);
                g_base_relics_modified = 1;
                save_base_relics();
                logmsg("BASE_PLACE: %s -> %s", sock_id, relic_id);
                break;
            }
        }
    } else if (strstr(p, "/base/swap")) {
        /* /base/swap/<base_type>/<missionId>/<socket1>/<socket2> */
        const char *s1 = (tc >= 2) ? tokens[tc - 2] : "";
        const char *s2 = (tc >= 1) ? tokens[tc - 1] : "";
        int idx1 = -1, idx2 = -1;
        for (int s = 0; s < 4; s++) {
            if (strcmp(g_base_relic_slots[s].sock_id, s1) == 0) idx1 = s;
            if (strcmp(g_base_relic_slots[s].sock_id, s2) == 0) idx2 = s;
        }
        if (idx1 >= 0 && idx2 >= 0) {
            char tmp[64];
            snprintf(tmp, sizeof(tmp), "%s", g_base_relic_slots[idx1].relic_id);
            snprintf(g_base_relic_slots[idx1].relic_id, sizeof(g_base_relic_slots[idx1].relic_id), "%s", g_base_relic_slots[idx2].relic_id);
            snprintf(g_base_relic_slots[idx2].relic_id, sizeof(g_base_relic_slots[idx2].relic_id), "%s", tmp);
            g_base_relics_modified = 1;
            save_base_relics();
            logmsg("BASE_SWAP: %s <-> %s", s1, s2);
        }
    } else if (strstr(p, "/base/remove")) {
        /* /base/remove/<base_type>/<missionId>/<socket>/<entityKey> */
        const char *sock_id = (tc >= 2) ? tokens[tc - 2] : "";
        for (int s = 0; s < 4; s++) {
            if (strcmp(g_base_relic_slots[s].sock_id, sock_id) == 0) {
                g_base_relic_slots[s].relic_id[0] = 0;
                g_base_relics_modified = 1;
                save_base_relics();
                logmsg("BASE_REMOVE: %s cleared", sock_id);
                break;
            }
        }
    }

    size_t rlen = 0;
    char *resp = build_placements_response(&rlen);
    if (resp && rlen > 0) {
        out_add(o, resp, rlen);
        free(resp);
        *outn = o->n;
        return (const unsigned char*)o->p;
    }
    static const unsigned char base_action_ok[] = "{\"error\":null,\"result\":{\"success\":true}}";
    *outn = strlen((const char*)base_action_ok);
    return base_action_ok;
}

typedef struct {
    size_t val_start;
    size_t val_end;
    int slot_idx;
} RelicReplacement;

static const unsigned char* inject_relics_into_base_active(const unsigned char *src, size_t src_len, Out *o, size_t *outn) {
    const char *p_placements = strstr((const char*)src, "\"placements\"");
    if (!p_placements) {
        *outn = src_len;
        return src;
    }
    const char *p_brace = strchr(p_placements, '{');
    if (!p_brace) {
        *outn = src_len;
        return src;
    }
    int depth = 0;
    const char *p_end = p_brace;
    while (*p_end && p_end < (const char*)src + src_len) {
        if (*p_end == '{') depth++;
        else if (*p_end == '}') {
            depth--;
            if (depth == 0) { p_end++; break; }
        }
        p_end++;
    }

    RelicReplacement reps[4];
    int rep_count = 0;
    for (int s = 0; s < 4; s++) {
        char key_search[64];
        snprintf(key_search, sizeof(key_search), "\"%s\":", g_base_relic_slots[s].sock_id);
        const char *found = strstr(p_brace, key_search);
        if (found && found < p_end) {
            const char *val_start = found + strlen(key_search);
            while (*val_start && isspace((unsigned char)*val_start)) val_start++;
            if (*val_start == '{') {
                int d = 0;
                const char *val_end = val_start;
                while (*val_end && val_end < p_end) {
                    if (*val_end == '{') d++;
                    else if (*val_end == '}') {
                        d--;
                        if (d == 0) { val_end++; break; }
                    }
                    val_end++;
                }
                reps[rep_count].val_start = (size_t)(val_start - (const char*)src);
                reps[rep_count].val_end = (size_t)(val_end - (const char*)src);
                reps[rep_count].slot_idx = s;
                rep_count++;
            }
        }
    }

    /* Sort replacements by val_start ascending */
    for (int i = 0; i < rep_count - 1; i++) {
        for (int j = i + 1; j < rep_count; j++) {
            if (reps[i].val_start > reps[j].val_start) {
                RelicReplacement tmp = reps[i];
                reps[i] = reps[j];
                reps[j] = tmp;
            }
        }
    }

    size_t last_idx = 0;
    for (int i = 0; i < rep_count; i++) {
        size_t vs = reps[i].val_start;
        size_t ve = reps[i].val_end;
        int s = reps[i].slot_idx;
        if (vs > last_idx) {
            out_add(o, (const char*)src + last_idx, vs - last_idx);
        }
        const RelicDef *def = find_relic_def(g_base_relic_slots[s].relic_id);
        char single[1024];
        int n = snprintf(single, sizeof(single),
            "{\"entityType\":\"building\",\"parentEntityType\":\"building\","
            "\"id\":\"%s\",\"key\":\"%s\",\"modelId\":\"%s\","
            "\"name\":\"%s\",\"name_loc\":{\"en\":\"%s\",\"zh-Hans\":\"%s\"},"
            "\"img\":\"%s\",\"rank\":5,\"level\":50,"
            "\"position\":{\"x\":%d,\"y\":%d}}",
            def->id, def->id, def->model_id,
            def->name_zh, def->name_en, def->name_zh,
            def->img, g_base_relic_slots[s].x, g_base_relic_slots[s].y
        );
        out_add(o, single, n);
        last_idx = ve;
    }
    if (last_idx < src_len) {
        out_add(o, (const char*)src + last_idx, src_len - last_idx);
    }
    *outn = o->n;
    return (const unsigned char*)o->p;
}
