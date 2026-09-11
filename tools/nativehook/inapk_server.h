#ifndef TFTF_INAPK_SERVER_H
#define TFTF_INAPK_SERVER_H

#include <stddef.h>

typedef void (*tftf_log_fn)(const char *fmt, ...);

void tftf_server_set_logger(tftf_log_fn fn);
int tftf_server_start_blob(const void *blob, size_t len);
/* Fills out with up to max mapped APK paths, ordered most likely first. */
int tftf_apk_candidates(const char *maps_path, const char *cmdline_path,
                        char out[][4096], int max);
int tftf_server_start_from_apk(void);
const unsigned char *tftf_payload_lookup(const char *key, size_t *n);

typedef struct { char bid[5][64]; int count; } Team;

extern int g_current_is_10x_challenge;
int tftf_get_current_team(Team *team);

float tftf_get_challenge_hp_multiplier(void);
float tftf_get_enemy_mana_gain(void);
const char* tftf_get_commander_name(void);
int tftf_get_target_fps(void);
void tftf_reload_user_settings(void);

#endif
