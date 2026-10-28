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
    { "relic_matrix_of_leadership", "rlc4", "matrix_of_leadership", "Matrix of Leadership", "领导模块" },
    { "relic_matrix_of_leadership_g1", "rlc14", "matrix_of_leadership_class", "Matrix of Leadership (G1)", "领导模块 (G1)" },
    { "relic_origin_matrix", "rlc8", "origin_matrix", "Origin Matrix", "原初矩阵" },
    { "relic_solus_forge", "rlc5", "solus_forge", "Forge of Solus Prime", "索拉斯之锤" },
    { "relic_dark_energon_crystal", "rlc11", "dark_energon_crystal", "Dark Energon Crystal", "黑暗能量水晶" },
    { "relic_unstable_energon_crystal", "rlc10", "unstable_energon_crystal", "Unstable Energon Crystal", "不稳定能量水晶" },
    { "relic_stasis_generator", "rlc20", "stasis_generator", "Stasis Generator", "停滞力场发生器" },
    { "relic_cloaking_field", "rlc19", "cloaking_field", "Cloaking Field Generator", "隐形发生器" },
    { "relic_fallen_titan_hand", "rlc9", "fallen_titan_hand", "Fallen Titan Hand", "堕落泰坦之手" },
    { "relic_ancient_tablet", "rlc13", "ancient_tablet", "Cybertronian Tablet", "赛博坦古老石板" },
    { "relic_goldendisk", "rlc22", "goldendisk", "Golden Disk", "金盘" },
    { "relic_shattered_disk", "rlc31d", "shattered_disk_t4", "Shattered Disk", "破碎之盘" },
    { "relic_statue_megatron", "rlc29", "statue_megatron", "Megatron Monument", "威震天纪念雕像" },
    { "relic_statue_hotrod", "rlc28", "statue_hotrod", "Hot Rod Monument", "热破英勇塑像" },
    { "relic_statue_solus", "rlc1", "statue_solus_g", "Solus Prime Monument", "索拉斯天尊塑像" },
    { "relic_jazz", "rlc_jazz_gs", "relic_jazz_t4", "Jazz Signature Relic", "爵士专属遗迹" },
    { "relic_optimus_primal", "rlc36d", "relic_optimus_primal_t4", "Optimus Primal Relic", "擎天圣专属遗迹" },
    { "relic_megatron", "rlc35d", "relic_megatron_t4", "Megatron Signature Relic", "威震天霸权遗迹" },
    { "relic_bumblebee", "rlc37d", "relic_bumblebee_t4", "Bumblebee Relic", "大黄蜂专属遗迹" },
    { "relic_blaster", "rlc40d", "relic_blaster_t4", "Blaster Sonic Relic", "录音机声波遗迹" },
    { "relic_cheetor", "rlc41d", "relic_cheetor_t4", "Cheetor Velocity Relic", "黄豹勇士极速遗迹" },
    { "relic_hound", "rlc38d", "relic_hound_t4", "Hound Hologram Relic", "探长全息遗迹" },
    { "relic_galvatron", "rlc34d", "relic_galvatron_t4", "Galvatron Particle Relic", "惊破天粒子遗迹" },
    { "relic_kickback", "rlc39d", "relic_kickback_t4", "Kickback Hive Relic", "反冲虫巢遗迹" },
    { "relic_alliance_victory", "rlc30d", "relic_ave_t4", "Alliance Victory Relic", "联盟凯旋勋章" },
    { "relic_raid_champion", "rlc33d", "relic_raid_t4", "Raid Champion Relic", "突袭冠军遗迹" },
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
    { "sock_relic_30_39", 30, 39, "relic_matrix_of_leadership_g1" }
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

static const char g_fixed_buildings[] = "\"sock_bldg_19_26\": {\"entityType\": \"building\", \"parentEntityType\": \"building\", \"key\": \"bldg_away_team\", \"rank\": 3, \"level\": 3, \"position\": {\"x\": 19, \"y\": 26}}, \"sock_bldg_23_24\": {\"entityType\": \"building\", \"parentEntityType\": \"building\", \"key\": \"bldg_crystal_premium\", \"rank\": 3, \"level\": 3, \"position\": {\"x\": 23, \"y\": 24}}, \"sock_bldg_25_23\": {\"entityType\": \"building\", \"parentEntityType\": \"building\", \"key\": \"bldg_battle_centre\", \"rank\": 3, \"level\": 3, \"position\": {\"x\": 25, \"y\": 23}}, \"sock_bldg_27_24\": {\"entityType\": \"building\", \"parentEntityType\": \"building\", \"key\": \"bldg_crystal_free\", \"rank\": 3, \"level\": 3, \"position\": {\"x\": 27, \"y\": 24}}, \"sock_bldg_29_25\": {\"entityType\": \"building\", \"parentEntityType\": \"building\", \"key\": \"bldg_alliance_help\", \"rank\": 3, \"level\": 3, \"position\": {\"x\": 29, \"y\": 25}}";

typedef struct {
    const char *boss_sock_id;
    const char *tower_sock_id;
    int x;
    int y;
    char boss_id[64];
    char tower_id[64];
} BaseDefenderSlot;

static BaseDefenderSlot g_base_defender_slots[7] = {
    { "sock_boss_25_30", "sock_tower_25_30", 25, 30, "megatron_gs_leader2015", "mods_primemodule_01" },
    { "sock_boss_22_33", "sock_tower_22_33", 22, 33, "megatronus_gs_kabam",    "mods_paralyzer_01" },
    { "sock_boss_28_33", "sock_tower_28_33", 28, 33, "soundwave_gs",           "mods_brawlersfury_01" },
    { "sock_boss_25_36", "sock_tower_25_36", 25, 36, "megatron_cin_rotf",      "mods_tacticianstrick_02" },
    { "sock_boss_22_39", "sock_tower_22_39", 22, 39, "galvatron_gs_voyager2016", "mods_harmaccelerator_01" },
    { "sock_boss_28_39", "sock_tower_28_39", 28, 39, "shockwave_gs",          "mods_strangerefractor_01" },
    { "sock_boss_25_42", "sock_tower_25_42", 25, 42, "arcee_gs_deluxe2014",     "mods_laserguidance_01" }
};

static const char *g_base_defenders_paths[] = {
    "/data/data/com.kabam.bigrobot/files/base_defenders.json",
    "/sdcard/Android/data/com.kabam.bigrobot/files/base_defenders.json",
    NULL
};

static int g_base_defenders_loaded = 0;
static int g_base_defenders_modified = 0;

static void load_base_defenders(void) {
    if (g_base_defenders_loaded) return;
    g_base_defenders_loaded = 1;
    for (int p = 0; g_base_defenders_paths[p]; p++) {
        FILE *fp = fopen(g_base_defenders_paths[p], "rb");
        if (fp) {
            char buf[4096];
            size_t rd = fread(buf, 1, sizeof(buf) - 1, fp);
            fclose(fp);
            if (rd > 0) {
                buf[rd] = 0;
                for (int s = 0; s < 7; s++) {
                    char val[64] = {0};
                    if (json_string(buf, buf + rd, g_base_defender_slots[s].boss_sock_id, val, sizeof(val))) {
                        snprintf(g_base_defender_slots[s].boss_id, sizeof(g_base_defender_slots[s].boss_id), "%s", val);
                        g_base_defenders_modified = 1;
                        logmsg("load_base_defenders: %s -> %s", g_base_defender_slots[s].boss_sock_id, val);
                    }
                    val[0] = 0;
                    if (json_string(buf, buf + rd, g_base_defender_slots[s].tower_sock_id, val, sizeof(val))) {
                        snprintf(g_base_defender_slots[s].tower_id, sizeof(g_base_defender_slots[s].tower_id), "%s", val);
                        g_base_defenders_modified = 1;
                        logmsg("load_base_defenders: %s -> %s", g_base_defender_slots[s].tower_sock_id, val);
                    }
                }
                return;
            }
        }
    }
}

static void save_base_defenders(void) {
    char json_buf[4096];
    int off = snprintf(json_buf, sizeof(json_buf), "{\n");
    for (int s = 0; s < 7; s++) {
        off += snprintf(json_buf + off, sizeof(json_buf) - off,
            "  \"%s\": \"%s\",\n"
            "  \"%s\": \"%s\"%s\n",
            g_base_defender_slots[s].boss_sock_id, g_base_defender_slots[s].boss_id,
            g_base_defender_slots[s].tower_sock_id, g_base_defender_slots[s].tower_id,
            (s == 6) ? "" : ","
        );
    }
    off += snprintf(json_buf + off, sizeof(json_buf) - off, "}\n");
    for (int p = 0; g_base_defenders_paths[p]; p++) {
        FILE *fp = fopen(g_base_defenders_paths[p], "wb");
        if (fp) {
            fwrite(json_buf, 1, off, fp);
            fclose(fp);
            logmsg("save_base_defenders: written to %s", g_base_defenders_paths[p]);
        }
    }
}

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

static char *build_placements_content(size_t *out_len) {
    load_base_relics();
    load_base_defenders();
    size_t alloc_sz = 32768;
    char *buf = (char*)malloc(alloc_sz);
    if (!buf) return NULL;
    int off = snprintf(buf, alloc_sz, "%s", g_fixed_buildings);
    for (int s = 0; s < 7; s++) {
        if (g_base_defender_slots[s].boss_id[0]) {
            off += snprintf(buf + off, alloc_sz - off,
                ",\"%s\":{\"entityType\":\"boss\",\"parentEntityType\":\"bcg\","
                "\"key\":\"%s\",\"character\":\"%s\",\"rank\":5,\"level\":50,\"sig_lvl\":60,"
                "\"position\":{\"x\":%d,\"y\":%d}}",
                g_base_defender_slots[s].boss_sock_id,
                g_base_defender_slots[s].boss_id,
                g_base_defender_slots[s].boss_id,
                g_base_defender_slots[s].x,
                g_base_defender_slots[s].y
            );
        }
    }
    for (int s = 0; s < 7; s++) {
        if (g_base_defender_slots[s].tower_id[0]) {
            off += snprintf(buf + off, alloc_sz - off,
                ",\"%s\":{\"entityType\":\"tower\",\"parentEntityType\":\"bcg\","
                "\"key\":\"%s\",\"character\":\"%s\",\"rank\":4,\"level\":50,"
                "\"position\":{\"x\":%d,\"y\":%d}}",
                g_base_defender_slots[s].tower_sock_id,
                g_base_defender_slots[s].tower_id,
                g_base_defender_slots[s].tower_id,
                g_base_defender_slots[s].x,
                g_base_defender_slots[s].y
            );
        }
    }
    for (int s = 0; s < 4; s++) {
        if (g_base_relic_slots[s].relic_id[0]) {
            append_relic_socket_json(buf, alloc_sz, &off, &g_base_relic_slots[s]);
        }
    }
    *out_len = off;
    return buf;
}

static char *build_placements_response(size_t *out_len) {
    size_t clen = 0;
    char *content = build_placements_content(&clen);
    if (!content) return NULL;
    size_t alloc_sz = clen + 128;
    char *buf = (char*)malloc(alloc_sz);
    if (!buf) { free(content); return NULL; }
    int off = snprintf(buf, alloc_sz, "{\"error\":null,\"result\":{\"success\":true,\"placements\":{%s}}}", content);
    free(content);
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
    load_base_defenders();
    char tokens[12][64];
    int tc = split_slash_tokens(p, tokens);
    if (strstr(p, "/base/place")) {
        /* /base/place/<base_type>/<socket_type>/<entityKey>/<missionId>/<x>/<y>/<socketId> */
        const char *sock_id = (tc >= 1) ? tokens[tc - 1] : "";
        const char *entity_key = (tc >= 5) ? tokens[4] : "";
        if (strncmp(sock_id, "sock_relic_", 11) == 0) {
            for (int s = 0; s < 4; s++) {
                if (strcmp(g_base_relic_slots[s].sock_id, sock_id) == 0) {
                    snprintf(g_base_relic_slots[s].relic_id, sizeof(g_base_relic_slots[s].relic_id), "%s", entity_key);
                    g_base_relics_modified = 1;
                    save_base_relics();
                    logmsg("BASE_PLACE_RELIC: %s -> %s", sock_id, entity_key);
                    break;
                }
            }
        } else if (strncmp(sock_id, "sock_boss_", 10) == 0) {
            for (int s = 0; s < 7; s++) {
                if (strcmp(g_base_defender_slots[s].boss_sock_id, sock_id) == 0) {
                    snprintf(g_base_defender_slots[s].boss_id, sizeof(g_base_defender_slots[s].boss_id), "%s", entity_key);
                    g_base_defenders_modified = 1;
                    save_base_defenders();
                    logmsg("BASE_PLACE_DEFENDER: %s -> %s", sock_id, entity_key);
                    break;
                }
            }
        } else if (strncmp(sock_id, "sock_tower_", 11) == 0) {
            for (int s = 0; s < 7; s++) {
                if (strcmp(g_base_defender_slots[s].tower_sock_id, sock_id) == 0) {
                    snprintf(g_base_defender_slots[s].tower_id, sizeof(g_base_defender_slots[s].tower_id), "%s", entity_key);
                    g_base_defenders_modified = 1;
                    save_base_defenders();
                    logmsg("BASE_PLACE_TOWER: %s -> %s", sock_id, entity_key);
                    break;
                }
            }
        }
    } else if (strstr(p, "/base/swap")) {
        /* /base/swap/<base_type>/<missionId>/.../<socket1>/.../<socket2> */
        const char *s1 = "";
        const char *s2 = "";
        for (int i = 0; i < tc; i++) {
            if (strncmp(tokens[i], "sock_", 5) == 0) {
                if (!s1[0]) s1 = tokens[i];
                else if (!s2[0]) { s2 = tokens[i]; break; }
            }
        }
        if (s1[0] && s2[0]) {
            if (strncmp(s1, "sock_relic_", 11) == 0 && strncmp(s2, "sock_relic_", 11) == 0) {
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
                    logmsg("BASE_SWAP_RELIC: %s <-> %s", s1, s2);
                }
            } else if (strncmp(s1, "sock_boss_", 10) == 0 && strncmp(s2, "sock_boss_", 10) == 0) {
                int idx1 = -1, idx2 = -1;
                for (int s = 0; s < 7; s++) {
                    if (strcmp(g_base_defender_slots[s].boss_sock_id, s1) == 0) idx1 = s;
                    if (strcmp(g_base_defender_slots[s].boss_sock_id, s2) == 0) idx2 = s;
                }
                if (idx1 >= 0 && idx2 >= 0) {
                    char tmp[64];
                    snprintf(tmp, sizeof(tmp), "%s", g_base_defender_slots[idx1].boss_id);
                    snprintf(g_base_defender_slots[idx1].boss_id, sizeof(g_base_defender_slots[idx1].boss_id), "%s", g_base_defender_slots[idx2].boss_id);
                    snprintf(g_base_defender_slots[idx2].boss_id, sizeof(g_base_defender_slots[idx2].boss_id), "%s", tmp);
                    g_base_defenders_modified = 1;
                    save_base_defenders();
                    logmsg("BASE_SWAP_DEFENDER: %s <-> %s", s1, s2);
                }
            } else if (strncmp(s1, "sock_tower_", 11) == 0 && strncmp(s2, "sock_tower_", 11) == 0) {
                int idx1 = -1, idx2 = -1;
                for (int s = 0; s < 7; s++) {
                    if (strcmp(g_base_defender_slots[s].tower_sock_id, s1) == 0) idx1 = s;
                    if (strcmp(g_base_defender_slots[s].tower_sock_id, s2) == 0) idx2 = s;
                }
                if (idx1 >= 0 && idx2 >= 0) {
                    char tmp[64];
                    snprintf(tmp, sizeof(tmp), "%s", g_base_defender_slots[idx1].tower_id);
                    snprintf(g_base_defender_slots[idx1].tower_id, sizeof(g_base_defender_slots[idx1].tower_id), "%s", g_base_defender_slots[idx2].tower_id);
                    snprintf(g_base_defender_slots[idx2].tower_id, sizeof(g_base_defender_slots[idx2].tower_id), "%s", tmp);
                    g_base_defenders_modified = 1;
                    save_base_defenders();
                    logmsg("BASE_SWAP_TOWER: %s <-> %s", s1, s2);
                }
            }
        }
    } else if (strstr(p, "/base/remove")) {
        /* /base/remove/<base_type>/<missionId>/<socket>/<entityKey> */
        const char *sock_id = "";
        for (int i = 0; i < tc; i++) {
            if (strncmp(tokens[i], "sock_", 5) == 0) {
                sock_id = tokens[i];
                break;
            }
        }
        if (sock_id[0]) {
            if (strncmp(sock_id, "sock_relic_", 11) == 0) {
                for (int s = 0; s < 4; s++) {
                    if (strcmp(g_base_relic_slots[s].sock_id, sock_id) == 0) {
                        g_base_relic_slots[s].relic_id[0] = 0;
                        g_base_relics_modified = 1;
                        save_base_relics();
                        logmsg("BASE_REMOVE_RELIC: %s cleared", sock_id);
                        break;
                    }
                }
            } else if (strncmp(sock_id, "sock_boss_", 10) == 0) {
                for (int s = 0; s < 7; s++) {
                    if (strcmp(g_base_defender_slots[s].boss_sock_id, sock_id) == 0) {
                        g_base_defender_slots[s].boss_id[0] = 0;
                        g_base_defenders_modified = 1;
                        save_base_defenders();
                        logmsg("BASE_REMOVE_DEFENDER: %s cleared", sock_id);
                        break;
                    }
                }
            } else if (strncmp(sock_id, "sock_tower_", 11) == 0) {
                for (int s = 0; s < 7; s++) {
                    if (strcmp(g_base_defender_slots[s].tower_sock_id, sock_id) == 0) {
                        g_base_defender_slots[s].tower_id[0] = 0;
                        g_base_defenders_modified = 1;
                        save_base_defenders();
                        logmsg("BASE_REMOVE_TOWER: %s cleared", sock_id);
                        break;
                    }
                }
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

static const unsigned char* inject_slots_into_base_active(const unsigned char *src, size_t src_len, Out *o, size_t *outn) {
    load_base_relics();
    load_base_defenders();
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

    size_t clen = 0;
    char *content = build_placements_content(&clen);
    if (!content) {
        *outn = src_len;
        return src;
    }

    size_t pre_len = (size_t)(p_brace + 1 - (const char*)src);
    out_add(o, (const char*)src, pre_len);
    out_add(o, content, clen);
    free(content);
    size_t post_offset = (size_t)(p_end - 1 - (const char*)src);
    out_add(o, (const char*)src + post_offset, src_len - post_offset);

    *outn = o->n;
    return (const unsigned char*)o->p;
}

static const struct {
    int x;
    int y;
    const char *boss_token;
    const char *tower_token;
    const char *def_boss;
    const char *def_tower;
} g_raid_slot_defs[7] = {
    { 25, 30, "%RB0%", "%RT0%", "megatron_gs_leader2015",   "mods_primemodule_01" },
    { 22, 33, "%RB1%", "%RT1%", "megatronus_gs_kabam",      "mods_paralyzer_01" },
    { 28, 33, "%RB2%", "%RT2%", "soundwave_gs",             "mods_brawlersfury_01" },
    { 25, 36, "%RB3%", "%RT3%", "megatron_cin_rotf",        "mods_tacticianstrick_02" },
    { 22, 39, "%RB4%", "%RT4%", "galvatron_gs_voyager2016", "mods_harmaccelerator_01" },
    { 28, 39, "%RB5%", "%RT5%", "shockwave_gs",            "mods_strangerefractor_01" },
    { 25, 42, "%RB6%", "%RT6%", "arcee_gs_deluxe2014",       "mods_laserguidance_01" }
};

static const struct {
    int x;
    int y;
    const char *relic_token;
    const char *model_token;
    const char *def_relic;
    const char *def_model;
} g_raid_relic_defs[4] = {
    { 20, 33, "%RR0%", "%RM0%", "relic_dark_energon_crystal",     "rlc11" },
    { 20, 39, "%RR1%", "%RM1%", "relic_unstable_energon_crystal", "rlc10" },
    { 30, 33, "%RR2%", "%RM2%", "relic_allspark",                 "rlc2" },
    { 30, 39, "%RR3%", "%RM3%", "relic_matrix_of_leadership_g1",  "rlc14" }
};

extern int g_selected_raid_opponent;

static const char *s_all_raid_mods[] = {
    "mods_primemodule_01",
    "mods_harmaccelerator_01",
    "mods_EMImodule_01",
    "mods_repairmodule_01",
    "mods_strangerefractor_01",
    "mods_superconductor_1000",
    "mods_superconductor_2000",
    "mods_paralyzer_01",
    "mods_laserguidance_01",
    "mods_nightbirdsmark_01",
    "mods_brawlersfury_01",
    "mods_demolitionscache_01",
    "mods_exofilter_01",
    "mods_fluxincapacitator_01",
    "mods_robotresource_01",
    "mods_scoutssentry_01",
    "mods_security_01",
    "mods_tacticianstrick_02",
    "mods_techconsole_01",
    "mods_warriorscall",
    "mods_generic_off_01",
    "mods_generic_def_01",
    "mods_generic_utl_01",
    "mods_attack_01",
    "mods_health_01"
};

static const char *s_all_raid_bots[] = {
    "acidstorm_gs_leader2015",
    "arcee_gs_deluxe2014",
    "barricade_cin_dotm",
    "bitstream_gs_leader2015",
    "blaster_gs_leader2016",
    "bludgeon_gs_rd20",
    "bonecrusher_cin_rotf",
    "breakdown_gs",
    "bumblebee_cin_dotm",
    "bumblebee_gs_kabam",
    "cheetor_bw_transmetal",
    "chromia_gs_kabam",
    "cliffjumper_gs_kabam",
    "cyclonus_gs_uw06",
    "deadend_gs_deluxe2015",
    "dinobot_bw_kabam",
    "dirge_gs_deluxe2008",
    "dragstrip_gs_deluxe2016",
    "drift_cin_aoe",
    "galvatron_gs_voyager2016",
    "grimlock_gs_mp08",
    "grindor_cin_rotf",
    "hotlink_gs_leader2015",
    "hotrod_cin_tlk",
    "hound_cin_tlk",
    "ionstorm_gs_leader2015",
    "ironhide_cin_rotf",
    "ironhide_gs_kabam",
    "jazz_gs_twm05",
    "jetfire_gs_leader2014",
    "kickback_gs_kabam",
    "lifeline_gs_deluxe2014",
    "megatron_cin_rotf",
    "megatron_gs_leader2015",
    "megatronus_gs_kabam",
    "mirage_gs_deluxe2016",
    "mixmaster_cin_rotf",
    "motormaster_gs_voyager2015",
    "necrotronus_gs_kabam",
    "nemesisprime_gs_voyager2015",
    "novastorm_gs_leader2015",
    "optimusprimal_bw_mp32",
    "optimusprime_cin_tf",
    "optimusprime_sg_voyager2015",
    "prowl_gs_deluxe2016",
    "ramjet_gs_deluxe2008",
    "ratchet_gs_kabam",
    "rhinox_gs_voyager2014",
    "rodimusprime_gs_mp09",
    "scorponok_bw_kabam",
    "sharkticon_gs_brawler",
    "sharkticon_gs_demolition",
    "sharkticon_gs_kabam",
    "sharkticon_gs_scout",
    "sharkticon_gs_tactician",
    "sharkticon_gs_tech",
    "sharkticon_gs_warrior",
    "shockwave_gs",
    "sideswipe_gs",
    "skywarp_gs_leader2015",
    "slipstream_gs",
    "soundblaster_gs_mp13b",
    "soundwave_gs",
    "starsaber_gs_leader2014",
    "starscream_ghost_gs",
    "sunstorm_gs_leader2015",
    "sunstreaker_gs_deluxe2008",
    "tantrum_gs_kabam",
    "thrust_gs_deluxe2008",
    "thundercracker_gs_leader2015",
    "ultramagnus_gs_leader",
    "ultramagnus_sg_leader",
    "waspinator_gs_deluxe",
    "wheeljack_gs_mp20",
    "wildrider_gs_deluxe2016",
    "windblade_gs"
};

static const char *s_all_raid_relics[][2] = {
    { "relic_dark_energon_crystal",     "rlc11" },
    { "relic_unstable_energon_crystal", "rlc10" },
    { "relic_allspark",                 "rlc2" },
    { "relic_matrix_of_leadership_g1",  "rlc14" },
    { "relic_matrix_of_leadership",     "rlc4" },
    { "relic_hound",                    "rlc38d" },
    { "relic_solus_forge",              "rlc5" },
    { "relic_origin_matrix",            "rlc8" },
    { "relic_covenant_primus",          "rlc7" },
    { "relic_statue_solus",             "rlc1" },
    { "relic_ancient_tablet",           "rlc13" },
    { "relic_immobilizer",              "rlc3" },
    { "relic_stasis_generator",         "rlc20" },
    { "relic_cloaking_field",           "rlc19" },
    { "relic_fallen_titan_hand",        "rlc9" },
    { "relic_goldendisk",               "rlc22" }
};

static char s_longxin_mods[7][64];
static char s_thirteen_bots[7][64];
static char s_thirteen_mods[7][64];
static char s_thirteen_relics[4][64];
static char s_thirteen_models[4][64];
static int s_opponents_generated = 0;

static void generate_random_raid_opponents(void) {
    int num_mods = sizeof(s_all_raid_mods) / sizeof(s_all_raid_mods[0]);
    int num_bots = sizeof(s_all_raid_bots) / sizeof(s_all_raid_bots[0]);
    int num_rels = sizeof(s_all_raid_relics) / sizeof(s_all_raid_relics[0]);

    for (int i = 0; i < 7; i++) {
        snprintf(s_longxin_mods[i], sizeof(s_longxin_mods[i]), "%s", s_all_raid_mods[rand() % num_mods]);
    }

    for (int i = 0; i < 7; i++) {
        snprintf(s_thirteen_bots[i], sizeof(s_thirteen_bots[i]), "%s", s_all_raid_bots[rand() % num_bots]);
        snprintf(s_thirteen_mods[i], sizeof(s_thirteen_mods[i]), "%s", s_all_raid_mods[rand() % num_mods]);
    }

    for (int i = 0; i < 4; i++) {
        int r = rand() % num_rels;
        snprintf(s_thirteen_relics[i], sizeof(s_thirteen_relics[i]), "%s", s_all_raid_relics[r][0]);
        snprintf(s_thirteen_models[i], sizeof(s_thirteen_models[i]), "%s", s_all_raid_relics[r][1]);
    }
    s_opponents_generated = 1;
}

static int get_raid_template_args(TemplateArg *args, int max_args) {
    if (max_args < 23) return 0;
    if (!s_opponents_generated) {
        generate_random_raid_opponents();
    }
    load_base_defenders();
    load_base_relics();
    int count = 0;

    // Opponent 0: [塞伯坦之魂]龙欣
    // 7 Sharkticons: slot 6 is warrior, slot 0 is 1000, 1-5 other sharkticons.
    // 4 Hound relics: all relic_hound with model rlc38d.
    if (g_selected_raid_opponent == 0) {
        static const char *longxin_sharks[7] = {
            "sharkticon_gs_kabam",      // Slot 0 (25, 30): 饿鲨1000守底
            "sharkticon_gs_tactician",  // Slot 1 (22, 33): 战术饿鲨
            "sharkticon_gs_tech",       // Slot 2 (28, 33): 科技饿鲨
            "sharkticon_gs_demolition", // Slot 3 (25, 36): 爆破饿鲨
            "sharkticon_gs_brawler",    // Slot 4 (22, 39): 格斗饿鲨
            "sharkticon_gs_scout",      // Slot 5 (28, 39): 侦察饿鲨
            "sharkticon_gs_warrior"     // Slot 6 (25, 42): 战士饿鲨第一只 (Entry)
        };
        for (int s = 0; s < 7; s++) {
            const char *b = longxin_sharks[s];
            const char *t = s_longxin_mods[s][0] ? s_longxin_mods[s] : g_raid_slot_defs[s].def_tower;
            args[count++] = (TemplateArg){ g_raid_slot_defs[s].boss_token, (const unsigned char*)b, strlen(b) };
            args[count++] = (TemplateArg){ g_raid_slot_defs[s].tower_token, (const unsigned char*)t, strlen(t) };
        }
        for (int r = 0; r < 4; r++) {
            const char *rel = "relic_hound";
            const char *mdl = "rlc38d";
            args[count++] = (TemplateArg){ g_raid_relic_defs[r].relic_token, (const unsigned char*)rel, strlen(rel) };
            args[count++] = (TemplateArg){ g_raid_relic_defs[r].model_token, (const unsigned char*)mdl, strlen(mdl) };
        }
        const char *opp_uid = "10001";
        args[count++] = (TemplateArg){ "%ROPP%", (const unsigned char*)opp_uid, strlen(opp_uid) };
        return count;
    }

    // Opponent 2: [塞伯坦联盟]十三元祖随机
    // Random bots and random mods
    if (g_selected_raid_opponent == 2) {
        for (int s = 0; s < 7; s++) {
            const char *b = s_thirteen_bots[s][0] ? s_thirteen_bots[s] : g_raid_slot_defs[s].def_boss;
            const char *t = s_thirteen_mods[s][0] ? s_thirteen_mods[s] : g_raid_slot_defs[s].def_tower;
            args[count++] = (TemplateArg){ g_raid_slot_defs[s].boss_token, (const unsigned char*)b, strlen(b) };
            args[count++] = (TemplateArg){ g_raid_slot_defs[s].tower_token, (const unsigned char*)t, strlen(t) };
        }
        for (int r = 0; r < 4; r++) {
            const char *rel = s_thirteen_relics[r][0] ? s_thirteen_relics[r] : g_raid_relic_defs[r].def_relic;
            const char *mdl = s_thirteen_models[r][0] ? s_thirteen_models[r] : g_raid_relic_defs[r].def_model;
            args[count++] = (TemplateArg){ g_raid_relic_defs[r].relic_token, (const unsigned char*)rel, strlen(rel) };
            args[count++] = (TemplateArg){ g_raid_relic_defs[r].model_token, (const unsigned char*)mdl, strlen(mdl) };
        }
        const char *opp_uid = "10003";
        args[count++] = (TemplateArg){ "%ROPP%", (const unsigned char*)opp_uid, strlen(opp_uid) };
        return count;
    }

    // Opponent 1: [重生]我的基地
    // Player's own base setup
    for (int s = 0; s < 7; s++) {
        const char *b = g_base_defender_slots[s].boss_id[0] ? g_base_defender_slots[s].boss_id : g_raid_slot_defs[s].def_boss;
        const char *t = g_base_defender_slots[s].tower_id[0] ? g_base_defender_slots[s].tower_id : g_raid_slot_defs[s].def_tower;
        args[count++] = (TemplateArg){ g_raid_slot_defs[s].boss_token, (const unsigned char*)b, strlen(b) };
        args[count++] = (TemplateArg){ g_raid_slot_defs[s].tower_token, (const unsigned char*)t, strlen(t) };
    }
    for (int r = 0; r < 4; r++) {
        const char *rel = g_base_relic_slots[r].relic_id[0] ? g_base_relic_slots[r].relic_id : g_raid_relic_defs[r].def_relic;
        const RelicDef *def = find_relic_def(rel);
        const char *mdl = (def && def->model_id) ? def->model_id : g_raid_relic_defs[r].def_model;
        args[count++] = (TemplateArg){ g_raid_relic_defs[r].relic_token, (const unsigned char*)rel, strlen(rel) };
        args[count++] = (TemplateArg){ g_raid_relic_defs[r].model_token, (const unsigned char*)mdl, strlen(mdl) };
    }
    const char *opp_uid = "1000000000001";
    args[count++] = (TemplateArg){ "%ROPP%", (const unsigned char*)opp_uid, strlen(opp_uid) };
    return count;
}
