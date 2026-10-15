#include "inapk_pvp.h"
#include "bot_info.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <pthread.h>
#include <android/log.h>

#define PVP_TAG "TFTF_PVP"
#define pvplog(...) __android_log_print(ANDROID_LOG_INFO, PVP_TAG, __VA_ARGS__)

extern char g_p0_bot_id[80];
extern volatile float g_p0_max_hp;
extern volatile float g_p1_max_hp;
extern volatile float g_p0_last_hp;
extern volatile float g_p1_last_hp;

typedef struct { int count; char bid[5][64]; } Team;
int tftf_get_current_team(Team *team);
const unsigned char *tftf_payload_lookup(const char *key, size_t *n);

typedef struct {
    char pvp_id[64];
    int state;               /* 0=none, 2=active, 0x80=selecting, 0x100=locking_in, 4=rewarding, 0x40=quit */
    int opponent_index;      /* 0, 1, 2 */
    int current_round;       /* 0, 1, 2 */
    int win_streak;
    int total_wins;
    int total_losses;
    int longest_streak;

    char user_heroes[3][64];
    int user_heroes_count;

    struct {
        int uid;
        char name[64];
        char tag[16];
        char bot_bids[3][64];
        int bot_ranks[3];
        int bot_levels[3];
        int bot_hp[3];
        int bot_atk[3];
        int bot_rating[3];

        char matchup_user[3][64];
        char matchup_opponent[3][64];
        int matchup_state[3];    /* 0=none, 1=inprogress, 2=resolved */
        int matchup_outcome[3];  /* 0=NONE, 1=WON, 2=LOST */
        int base_points[3];
        int actual_points[3];
        char fight_id[3][64];
    } opponents[3];
} TFTF_PVPState;

static TFTF_PVPState s_pvp = {
    .pvp_id = "arena_versus",
    .state = 0,
    .opponent_index = 0,
    .current_round = 0,
    .win_streak = 0,
    .total_wins = 0,
    .total_losses = 0,
    .longest_streak = 0,
    .user_heroes_count = 0
};

static pthread_mutex_t s_pvp_lock = PTHREAD_MUTEX_INITIALIZER;
static char s_resp_buf[65536];

static unsigned int s_rand_seed = 987654321;
static unsigned int pvp_rand(void) {
    if (s_rand_seed == 987654321) {
        s_rand_seed ^= (unsigned int)time(NULL) ^ (unsigned int)getpid();
    }
    s_rand_seed = s_rand_seed * 1103515245 + 12345;
    return (s_rand_seed >> 16) & 0x7fff;
}

static const EnemyStat* find_stat_or_default(const char *bid) {
    int count = sizeof(ENEMY_STATS) / sizeof(ENEMY_STATS[0]);
    for (int i = 0; i < count; i++) {
        if (strcmp(ENEMY_STATS[i].id, bid) == 0) return &ENEMY_STATS[i];
    }
    return &ENEMY_STATS[0];
}

static const char* const s_opponent_names[] = {
    "霸天虎·游击斥候", "汽车人·先锋禁卫", "萨克巨人亲卫", "威震天狂徒卫队",
    "红蜘蛛追击小队", "擎天柱精英突击", "方舟突击阵列", "报应号掠夺者",
    "昆塔沙审判执事", "巨无霸荒野行者", "原始兽暗夜猎手", "太空桥游荡佣兵"
};
#define OPP_NAMES_COUNT (sizeof(s_opponent_names) / sizeof(s_opponent_names[0]))

static const char* state_to_string(int s) {
    switch (s) {
        case 2: return "active";
        case 4: return "rewarding";
        case 8: return "claimed";
        case 0x10: return "newOpponent";
        case 0x20: return "completed";
        case 0x40: return "quit";
        case 0x80: return "selecting";
        case 0x100: return "locking_in";
        default: return "none";
    }
}

static const char* matchup_state_to_string(int ms) {
    switch (ms) {
        case 1: return "inprogress";
        case 2: return "resolved";
        default: return "none";
    }
}

static const char* outcome_to_string(int out) {
    switch (out) {
        case 1: return "WON";
        case 2: return "LOST";
        default: return "NONE";
    }
}

static void parse_json_string_array(const char *json, const char *key, char out_arr[][64], int *out_count, int max_items) {
    *out_count = 0;
    if (!json) return;
    char pat[64];
    snprintf(pat, sizeof pat, "\"%s\":[", key);
    const char *p = strstr(json, pat);
    if (!p) {
        snprintf(pat, sizeof pat, "\"%s\": [", key);
        p = strstr(json, pat);
    }
    if (!p) return;
    p = strchr(p, '[');
    if (!p) return;
    p++;
    while (*p && *p != ']' && *out_count < max_items) {
        while (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n' || *p == ',') p++;
        if (*p == '\"') {
            p++;
            const char *start = p;
            while (*p && *p != '\"') p++;
            if (*p == '\"') {
                size_t len = p - start;
                if (len >= 64) len = 63;
                strncpy(out_arr[*out_count], start, len);
                out_arr[*out_count][len] = '\0';
                (*out_count)++;
                p++;
            }
        } else {
            p++;
        }
    }
}

static void generate_pvp_opponents(void) {
    int total_enemies = sizeof(ENEMY_STATS) / sizeof(ENEMY_STATS[0]);
    int used_indices[9];
    int used_count = 0;

    for (int opp = 0; opp < 3; opp++) {
        s_pvp.opponents[opp].uid = 10001 + opp * 10 + (pvp_rand() % 9);
        const char *opp_name = s_opponent_names[(pvp_rand() + opp) % OPP_NAMES_COUNT];
        snprintf(s_pvp.opponents[opp].name, sizeof(s_pvp.opponents[opp].name), "%s", opp_name);
        snprintf(s_pvp.opponents[opp].tag, sizeof(s_pvp.opponents[opp].tag), "AI");

        for (int b = 0; b < 3; b++) {
            int bot_idx;
            int attempts = 0;
            do {
                bot_idx = pvp_rand() % total_enemies;
                int duplicate = 0;
                for (int u = 0; u < used_count; u++) {
                    if (used_indices[u] == bot_idx) { duplicate = 1; break; }
                }
                if (!duplicate || attempts > 20) {
                    used_indices[used_count++] = bot_idx;
                    break;
                }
                attempts++;
            } while (attempts <= 20);

            const EnemyStat *stat = &ENEMY_STATS[bot_idx];
            snprintf(s_pvp.opponents[opp].bot_bids[b], sizeof(s_pvp.opponents[opp].bot_bids[b]), "%s", stat->id);
            s_pvp.opponents[opp].bot_ranks[b] = 4;
            s_pvp.opponents[opp].bot_levels[b] = 40;
            s_pvp.opponents[opp].bot_hp[b] = stat->hp;
            s_pvp.opponents[opp].bot_atk[b] = stat->atk;
            s_pvp.opponents[opp].bot_rating[b] = stat->rating;

            if (b < s_pvp.user_heroes_count && s_pvp.user_heroes[b][0]) {
                snprintf(s_pvp.opponents[opp].matchup_user[b], sizeof(s_pvp.opponents[opp].matchup_user[b]), "%s", s_pvp.user_heroes[b]);
            } else {
                snprintf(s_pvp.opponents[opp].matchup_user[b], sizeof(s_pvp.opponents[opp].matchup_user[b]), "");
            }
            snprintf(s_pvp.opponents[opp].matchup_opponent[b], sizeof(s_pvp.opponents[opp].matchup_opponent[b]), "%s", stat->id);
            s_pvp.opponents[opp].matchup_state[b] = 0;
            s_pvp.opponents[opp].matchup_outcome[b] = 0;
            s_pvp.opponents[opp].base_points[b] = 300 + (b * 50);
            s_pvp.opponents[opp].actual_points[b] = 0;
            snprintf(s_pvp.opponents[opp].fight_id[b], sizeof(s_pvp.opponents[opp].fight_id[b]), "pvp_fight_%d_%d", opp, b);
        }
    }
}

static int append_pvp_match_data_json(char *buf, size_t max_len, int offset) {
    int n = snprintf(buf + offset, max_len - offset,
        "{\"pid\":\"%s\",\"state\":\"%s\",\"opponentIndex\":%d,\"fightRewards\":[],\"seriesRewards\":{},\"milestones\":[],\"opponents\":[",
        s_pvp.pvp_id, state_to_string(s_pvp.state), s_pvp.opponent_index);
    if (n < 0 || (size_t)n >= max_len - offset) return -1;
    offset += n;

    for (int o = 0; o < 3; o++) {
        n = snprintf(buf + offset, max_len - offset,
            "%s{\"uid\":%d,\"userData\":{\"name\":\"%s\",\"tag\":\"%s\",\"level\":30,\"portrait\":\"\",\"factionId\":\"decepticon\",\"pvpStats\":{\"pid\":\"%s\",\"winStreak\":%d,\"wins\":%d,\"losses\":%d,\"longestStreak\":%d,\"findAttempts\":0}},\"team\":[",
            (o > 0 ? "," : ""),
            s_pvp.opponents[o].uid,
            s_pvp.opponents[o].name,
            s_pvp.opponents[o].tag,
            s_pvp.pvp_id,
            s_pvp.win_streak, s_pvp.total_wins, s_pvp.total_losses, s_pvp.longest_streak);
        if (n < 0 || (size_t)n >= max_len - offset) return -1;
        offset += n;

        for (int b = 0; b < 3; b++) {
            n = snprintf(buf + offset, max_len - offset,
                "%s{\"entity_type\":\"bot\",\"bid\":\"%s\",\"rank\":%d,\"level\":%d,\"sig_lvl\":20,\"max_hp\":%d,\"attack\":%d,\"rating\":%d,\"rating_hp\":%d,\"rating_attack\":%d,\"special_attacks\":0}",
                (b > 0 ? "," : ""),
                s_pvp.opponents[o].bot_bids[b],
                s_pvp.opponents[o].bot_ranks[b],
                s_pvp.opponents[o].bot_levels[b],
                s_pvp.opponents[o].bot_hp[b],
                s_pvp.opponents[o].bot_atk[b],
                s_pvp.opponents[o].bot_rating[b],
                s_pvp.opponents[o].bot_hp[b],
                s_pvp.opponents[o].bot_atk[b]);
            if (n < 0 || (size_t)n >= max_len - offset) return -1;
            offset += n;
        }

        n = snprintf(buf + offset, max_len - offset, "],\"matchups\":[");
        if (n < 0 || (size_t)n >= max_len - offset) return -1;
        offset += n;

        for (int m = 0; m < 3; m++) {
            n = snprintf(buf + offset, max_len - offset,
                "%s{\"userHero\":\"%s\",\"opponentHero\":\"%s\",\"aip\":\"default\",\"state\":\"%s\",\"outcome\":\"%s\",\"basePoints\":%d,\"actualPoints\":%d,\"fightId\":\"%s\"}",
                (m > 0 ? "," : ""),
                s_pvp.opponents[o].matchup_user[m],
                s_pvp.opponents[o].matchup_opponent[m],
                matchup_state_to_string(s_pvp.opponents[o].matchup_state[m]),
                outcome_to_string(s_pvp.opponents[o].matchup_outcome[m]),
                s_pvp.opponents[o].base_points[m],
                s_pvp.opponents[o].actual_points[m],
                s_pvp.opponents[o].fight_id[m]);
            if (n < 0 || (size_t)n >= max_len - offset) return -1;
            offset += n;
        }

        n = snprintf(buf + offset, max_len - offset, "]}");
        if (n < 0 || (size_t)n >= max_len - offset) return -1;
        offset += n;
    }

    n = snprintf(buf + offset, max_len - offset, "]}");
    if (n < 0 || (size_t)n >= max_len - offset) return -1;
    return offset + n;
}

static int build_standard_pvp_response(char *buf, size_t max_len) {
    int offset = snprintf(buf, max_len, "{\"error\":null,\"result\":{\"pvpMatchData\":[");
    if (s_pvp.state != 0 && s_pvp.state != 0x40) {
        offset = append_pvp_match_data_json(buf, max_len, offset);
        if (offset < 0) return -1;
    }
    int n = snprintf(buf + offset, max_len - offset,
        "],\"pvpUserData\":[{\"pid\":\"%s\",\"winStreak\":%d,\"wins\":%d,\"losses\":%d,\"longestStreak\":%d,\"findAttempts\":0}],"
        "\"userData\":[{\"pid\":\"%s\",\"winStreak\":%d,\"wins\":%d,\"losses\":%d,\"longestStreak\":%d,\"findAttempts\":0}]",
        s_pvp.pvp_id, s_pvp.win_streak, s_pvp.total_wins, s_pvp.total_losses, s_pvp.longest_streak,
        s_pvp.pvp_id, s_pvp.win_streak, s_pvp.total_wins, s_pvp.total_losses, s_pvp.longest_streak);
    if (n < 0 || (size_t)n >= max_len - offset) return -1;
    offset += n;

    if (s_pvp.state != 0 && s_pvp.state != 0x40) {
        /* Append bcgData to update activeTeams for arena_versus */
        n = snprintf(buf + offset, max_len - offset,
            ",\"bcgData\":[{\"updates\":{\"activeTeams\":[{\"aid\":\"%s\",\"type\":\"pvp\",\"modes\":[\"pvp\"],\"expire\":-1,\"heroes\":{",
            s_pvp.pvp_id);
        if (n < 0 || (size_t)n >= max_len - offset) return -1;
        offset += n;

        int hero_count = s_pvp.user_heroes_count;
        if (hero_count <= 0) {
            Team def_team;
            if (tftf_get_current_team(&def_team)) {
                for (int i = 0; i < def_team.count && i < 3; i++) {
                    snprintf(s_pvp.user_heroes[i], sizeof(s_pvp.user_heroes[i]), "%s", def_team.bid[i]);
                }
                s_pvp.user_heroes_count = def_team.count < 3 ? def_team.count : 3;
                hero_count = s_pvp.user_heroes_count;
            }
        }

        for (int h = 0; h < hero_count; h++) {
            size_t vn = 0;
            char hkey[96];
            snprintf(hkey, sizeof(hkey), "@savedteam:hero:%s", s_pvp.user_heroes[h]);
            const unsigned char *hv = tftf_payload_lookup(hkey, &vn);
            if (h > 0) {
                n = snprintf(buf + offset, max_len - offset, ",");
                if (n < 0 || (size_t)n >= max_len - offset) return -1;
                offset += n;
            }
            if (hv && vn > 0) {
                const char *p_pvpb = strstr((const char*)hv, "\"pvpb\":{}");
                if (p_pvpb && (size_t)(p_pvpb - (const char*)hv) < vn) {
                    size_t pre_len = (size_t)(p_pvpb - (const char*)hv);
                    size_t post_len = vn - pre_len - 9;
                    n = snprintf(buf + offset, max_len - offset,
                        "\"%s\":%.*s\"pvpb\":{\"m\":1.0}%.*s",
                        s_pvp.user_heroes[h],
                        (int)pre_len, hv,
                        (int)post_len, p_pvpb + 9);
                } else {
                    n = snprintf(buf + offset, max_len - offset, "\"%s\":%.*s", s_pvp.user_heroes[h], (int)vn, hv);
                }
            } else {
                n = snprintf(buf + offset, max_len - offset,
                    "\"%s\":{\"bid\":\"%s\",\"rank\":4,\"level\":40,\"sig_lvl\":20,\"rating_hp\":2000,\"max_hp\":2000,\"rating_attack\":500,\"attack\":500,\"pvpb\":{\"m\":1.0}}",
                    s_pvp.user_heroes[h], s_pvp.user_heroes[h]);
            }
            if (n < 0 || (size_t)n >= max_len - offset) return -1;
            offset += n;
        }

        n = snprintf(buf + offset, max_len - offset, "}}]}}]}}");
        if (n < 0 || (size_t)n >= max_len - offset) return -1;
        return offset + n;
    } else {
        n = snprintf(buf + offset, max_len - offset, ",\"bcgData\":[]}}");
        if (n < 0 || (size_t)n >= max_len - offset) return -1;
        return offset + n;
    }
}

const unsigned char *handle_pvp_request(const char *method, const char *p, const char *body, size_t bn, size_t *outn) {
    if (!p) return NULL;

    /* 1. Clear Invalid Teams */
    if (strstr(p, "/pvp/clear-invalid-teams")) {
        pthread_mutex_lock(&s_pvp_lock);
        /* Preserve current match state; do NOT wipe s_pvp.state = 0 */
        int len = build_standard_pvp_response(s_resp_buf, sizeof s_resp_buf);
        pthread_mutex_unlock(&s_pvp_lock);
        if (len > 0) {
            *outn = (size_t)len;
            pvplog("PVP: handled /pvp/clear-invalid-teams (state=0x%x, %d bytes)", s_pvp.state, len);
            return (const unsigned char*)s_resp_buf;
        }
    }

    /* 2. Find Arena Opponent / Get New Opponent */
    if (strstr(p, "/pvp/find-arena-opponent") || strstr(p, "/pvp/get-new-opponent")) {
        pthread_mutex_lock(&s_pvp_lock);
        if (body && bn > 0) {
            const char *aid = strstr(body, "\"arenaID\":");
            if (aid) {
                aid = strchr(aid, ':');
                if (aid) {
                    while (*aid == ':' || *aid == ' ' || *aid == '\"') aid++;
                    const char *end_aid = aid;
                    while (*end_aid && *end_aid != '\"' && *end_aid != ',' && *end_aid != '}') end_aid++;
                    size_t aid_len = end_aid - aid;
                    if (aid_len > 0 && aid_len < sizeof(s_pvp.pvp_id)) {
                        strncpy(s_pvp.pvp_id, aid, aid_len);
                        s_pvp.pvp_id[aid_len] = '\0';
                    }
                }
            }
            parse_json_string_array(body, "heroes", s_pvp.user_heroes, &s_pvp.user_heroes_count, 3);
        }
        if (s_pvp.user_heroes_count <= 0) {
            Team def_team;
            if (tftf_get_current_team(&def_team)) {
                for (int i = 0; i < def_team.count && i < 3; i++) {
                    snprintf(s_pvp.user_heroes[i], sizeof(s_pvp.user_heroes[i]), "%s", def_team.bid[i]);
                }
                s_pvp.user_heroes_count = def_team.count < 3 ? def_team.count : 3;
            }
        }
        generate_pvp_opponents();
        s_pvp.state = 0x80; /* selecting */
        s_pvp.opponent_index = 0;
        s_pvp.current_round = 0;
        int len = build_standard_pvp_response(s_resp_buf, sizeof s_resp_buf);
        pthread_mutex_unlock(&s_pvp_lock);
        if (len > 0) {
            *outn = (size_t)len;
            pvplog("PVP: handled %s -> 3 opponents generated, state=selecting (%d bytes)", p, len);
            return (const unsigned char*)s_resp_buf;
        }
    }

    /* 3. Select Opponent */
    if (strstr(p, "/pvp/select-opponent")) {
        pthread_mutex_lock(&s_pvp_lock);
        const char *idx_p = strstr(body, "\"index\":");
        if (idx_p) {
            int idx = atoi(idx_p + 8);
            if (idx >= 0 && idx < 3) s_pvp.opponent_index = idx;
        }
        s_pvp.state = 0x100; /* locking_in */
        int len = build_standard_pvp_response(s_resp_buf, sizeof s_resp_buf);
        pthread_mutex_unlock(&s_pvp_lock);
        if (len > 0) {
            *outn = (size_t)len;
            pvplog("PVP: handled /pvp/select-opponent -> opponentIndex=%d, state=locking_in (%d bytes)", s_pvp.opponent_index, len);
            return (const unsigned char*)s_resp_buf;
        }
    }

    /* 4. Lock In Team Lineup */
    if (strstr(p, "/pvp/lockin")) {
        pthread_mutex_lock(&s_pvp_lock);
        char heroes[3][64];
        int count = 0;
        if (body && bn > 0) {
            parse_json_string_array(body, "heroes", heroes, &count, 3);
        }
        int cur_opp = s_pvp.opponent_index;
        for (int i = 0; i < 3; i++) {
            if (i < count && heroes[i][0]) {
                snprintf(s_pvp.opponents[cur_opp].matchup_user[i], sizeof(s_pvp.opponents[cur_opp].matchup_user[i]), "%s", heroes[i]);
            } else if (i < s_pvp.user_heroes_count && s_pvp.user_heroes[i][0]) {
                snprintf(s_pvp.opponents[cur_opp].matchup_user[i], sizeof(s_pvp.opponents[cur_opp].matchup_user[i]), "%s", s_pvp.user_heroes[i]);
            }
            s_pvp.opponents[cur_opp].matchup_state[i] = (i == 0 ? 1 : 0); /* 1st matchup is inprogress */
            s_pvp.opponents[cur_opp].matchup_outcome[i] = 0;
        }
        s_pvp.state = 2; /* active */
        s_pvp.current_round = 0;
        int len = build_standard_pvp_response(s_resp_buf, sizeof s_resp_buf);
        pthread_mutex_unlock(&s_pvp_lock);
        if (len > 0) {
            *outn = (size_t)len;
            pvplog("PVP: handled /pvp/lockin -> matchups locked, state=active (%d bytes)", len);
            return (const unsigned char*)s_resp_buf;
        }
    }

    /* 5. Match Loaded */
    if (strstr(p, "/pvp/match-loaded")) {
        static const unsigned char ok_resp[] = "{\"error\":null,\"result\":{}}";
        *outn = sizeof(ok_resp) - 1;
        pvplog("PVP: handled /pvp/match-loaded");
        return ok_resp;
    }

    /* 6. Quit Arena */
    if (strstr(p, "/pvp/quit")) {
        pthread_mutex_lock(&s_pvp_lock);
        s_pvp.state = 0x40; /* quit */
        s_pvp.win_streak = 0;
        int len = build_standard_pvp_response(s_resp_buf, sizeof s_resp_buf);
        pthread_mutex_unlock(&s_pvp_lock);
        if (len > 0) {
            *outn = (size_t)len;
            pvplog("PVP: handled /pvp/quit (%d bytes)", len);
            return (const unsigned char*)s_resp_buf;
        }
    }

    /* 7. Activate Match (FightFlow) */
    if (strstr(p, "/matches/activate-match/pvp_fight") || (strstr(p, "/matches/activate-match") && strstr(p, "pvp"))) {
        pthread_mutex_lock(&s_pvp_lock);
        int cur_opp = s_pvp.opponent_index;
        int r = s_pvp.current_round;
        const char *u_bid = s_pvp.opponents[cur_opp].matchup_user[r];
        const char *o_bid = s_pvp.opponents[cur_opp].matchup_opponent[r];
        if (!u_bid || !u_bid[0]) u_bid = "optimusprime_cin_tf";
        if (!o_bid || !o_bid[0]) o_bid = "megatron_cin_rotf";

        const EnemyStat *u_stat = find_stat_or_default(u_bid);
        const EnemyStat *o_stat = find_stat_or_default(o_bid);

        snprintf(g_p0_bot_id, sizeof g_p0_bot_id, "%s", u_bid);
        g_p0_max_hp = (float)u_stat->hp;
        g_p1_max_hp = (float)o_stat->hp;
        g_p0_last_hp = g_p0_max_hp;
        g_p1_last_hp = g_p1_max_hp;

        int offset = snprintf(s_resp_buf, sizeof s_resp_buf,
            "{\"error\":null,\"result\":{},\"async\":[{\"component\":\"PVPManager\",\"message\":\"match-activated\",\"payload\":{"
            "\"matchAttributes\":{"
                "\"userHero\":{\"bid\":\"%s\",\"rank\":5,\"level\":50,\"sig_lvl\":100,\"max_hp\":%d,\"attack\":%d,\"rating_hp\":%d,\"rating_attack\":%d,\"special_attacks\":0},"
                "\"opponentHero\":{\"bid\":\"%s\",\"rank\":4,\"level\":40,\"sig_lvl\":20,\"max_hp\":%d,\"attack\":%d,\"rating_hp\":%d,\"rating_attack\":%d,\"special_attacks\":0}"
            "},"
            "\"pvpMatchData\":[",
            u_bid, u_stat->hp, u_stat->atk, u_stat->hp, u_stat->atk,
            o_bid, o_stat->hp, o_stat->atk, o_stat->hp, o_stat->atk);

        offset = append_pvp_match_data_json(s_resp_buf, sizeof s_resp_buf, offset);
        if (offset > 0) {
            int n = snprintf(s_resp_buf + offset, sizeof(s_resp_buf) - offset, "]}}]}");
            if (n > 0) offset += n;
        }
        pthread_mutex_unlock(&s_pvp_lock);

        if (offset > 0) {
            *outn = (size_t)offset;
            pvplog("PVP: handled activate-match/pvp_fight -> round=%d user=%s(%d HP) vs opp=%s(%d HP) (%d bytes)",
                   r, u_bid, u_stat->hp, o_bid, o_stat->hp, offset);
            return (const unsigned char*)s_resp_buf;
        }
    }

    /* 8. Resolve Match (FightFlow) */
    if (strstr(p, "/matches/resolve-match/pvp_fight") || (strstr(p, "/matches/resolve-match") && strstr(p, "pvp"))) {
        pthread_mutex_lock(&s_pvp_lock);
        int is_win = (body && strstr(body, "\"WON\"") != NULL);
        int cur_opp = s_pvp.opponent_index;
        int r = s_pvp.current_round;

        s_pvp.opponents[cur_opp].matchup_outcome[r] = (is_win ? 1 : 2);
        s_pvp.opponents[cur_opp].matchup_state[r] = 2; /* resolved */
        s_pvp.opponents[cur_opp].actual_points[r] = is_win ? (s_pvp.opponents[cur_opp].base_points[r] * (10 + s_pvp.win_streak) / 10) : 0;

        if (r < 2) {
            s_pvp.current_round = r + 1;
            s_pvp.opponents[cur_opp].matchup_state[r + 1] = 1; /* inprogress */
            s_pvp.state = 2; /* active */
        } else {
            /* 3-round series finished */
            int wins = 0;
            for (int i = 0; i < 3; i++) {
                if (s_pvp.opponents[cur_opp].matchup_outcome[i] == 1) wins++;
            }
            if (wins >= 2) {
                s_pvp.win_streak++;
                s_pvp.total_wins++;
                if (s_pvp.win_streak > s_pvp.longest_streak) s_pvp.longest_streak = s_pvp.win_streak;
            } else {
                s_pvp.win_streak = 0;
                s_pvp.total_losses++;
            }
            s_pvp.state = 4; /* rewarding */
        }

        int offset = snprintf(s_resp_buf, sizeof s_resp_buf,
            "{\"error\":null,\"result\":{},\"async\":[{\"component\":\"PVPManager\",\"message\":\"match-resolved\",\"payload\":{"
            "\"pvpMatchData\":[");
        offset = append_pvp_match_data_json(s_resp_buf, sizeof s_resp_buf, offset);
        if (offset > 0) {
            int n = snprintf(s_resp_buf + offset, sizeof(s_resp_buf) - offset,
                "],\"pvpUserData\":[{\"pid\":\"%s\",\"winStreak\":%d,\"wins\":%d,\"losses\":%d,\"longestStreak\":%d,\"findAttempts\":0}]}}]}",
                s_pvp.pvp_id, s_pvp.win_streak, s_pvp.total_wins, s_pvp.total_losses, s_pvp.longest_streak);
            if (n > 0) offset += n;
        }
        pthread_mutex_unlock(&s_pvp_lock);

        if (offset > 0) {
            *outn = (size_t)offset;
            pvplog("PVP: handled resolve-match/pvp_fight -> round=%d is_win=%d streak=%d next_state=%s (%d bytes)",
                   r, is_win, s_pvp.win_streak, state_to_string(s_pvp.state), offset);
            return (const unsigned char*)s_resp_buf;
        }
    }

    return NULL;
}
