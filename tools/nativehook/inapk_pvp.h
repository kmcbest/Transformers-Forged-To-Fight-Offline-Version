#ifndef INAPK_PVP_H
#define INAPK_PVP_H

#include <stddef.h>

// Handle /pvp/* and /matches/*-match/pvp_fight routes.
// Returns pointer to response buffer if handled, NULL otherwise.
const unsigned char *handle_pvp_request(const char *method, const char *p, const char *body, size_t bn, size_t *outn);

int tftf_pvp_is_active(void);

#endif /* INAPK_PVP_H */
