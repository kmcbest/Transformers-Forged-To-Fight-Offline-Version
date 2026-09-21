#ifndef HOOK_COMMON_H
#define HOOK_COMMON_H

#include <android/log.h>
#include <stdarg.h>
#include <setjmp.h>
#include <signal.h>
#include <ucontext.h>
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/mman.h>
#include <pthread.h>
#include <link.h>
#include <dlfcn.h>
#include <time.h>
#include <jni.h>
#include <math.h>
#include "inapk_server.h"

#ifdef __cplusplus
extern "C" {
#endif

// Crash protection TLS
extern __thread sigjmp_buf g_jb;
extern __thread volatile int g_prot;

#define PROTECT(...) do { g_prot=1; if (sigsetjmp(g_jb,1)==0) { __VA_ARGS__ } g_prot=0; } while(0)
#define LOG(...) do { __android_log_print(ANDROID_LOG_ERROR, "TFTFHOOK", __VA_ARGS__); flog(__VA_ARGS__); } while(0)

#define COMBAT_ASSERT(cond, tag, fmt, ...) \
    do { \
        if (!(cond)) { \
            flog("[COMBAT_RULE_VIOLATION][%s] ASSERT FAILED: " fmt, tag, ##__VA_ARGS__); \
        } \
    } while(0)

void flog(const char* fmt, ...);
extern FILE* g_f;
extern volatile int g_inqs;
extern volatile int g_inhb;
void log_key(const char* tag, void* s);

// Core Il2Cpp and Base symbols
extern uintptr_t g_base;
typedef void* (*strnew_t)(const char*);
typedef void* (*arraynew_t)(void*, size_t);
extern strnew_t g_strnew;
extern arraynew_t g_arraynew;
extern void* g_empty_tags;

// Shared function signatures
typedef void* (*fn8)(void*,void*,void*,void*,void*,void*,void*,void*);
typedef void* (*fn1)(void*);
typedef void (*fn_ai_simulate)(void*, float, void*);

// Unity AAPCS64 HFA math types
typedef struct { float x, y, z; } V3;
typedef struct { float cx, cy, cz, ex, ey, ez; } Bounds;
typedef struct { float r, g, b, a; } COL4;

// Global Hook Table
typedef struct HookDef {
    uint32_t rva;
    const char* tag;
    int jp;
    fn8 orig;
} HookDef;
extern HookDef H[];

static inline void ensure_empty_tags(void) {
    if (g_empty_tags) return;
    if (!g_strnew || !g_arraynew) return;
    void* s = g_strnew("");
    if (s) {
        void* strclass = *(void**)s;
        if (strclass) g_empty_tags = g_arraynew(strclass, 0);
    }
}

static inline void fix_blueprint_tags(void* bpv) {
    uintptr_t bp = (uintptr_t)bpv;
    if (!g_empty_tags || bp < 0x100000 || (bp & 7)) return;
    void** tags = (void**)(bp + 0xB8);
    if (*tags == NULL) *tags = g_empty_tags;
}

// Reflection & memory helpers
static inline int obj_ok(void* p) {
    return (uintptr_t)p >= 0x100000 && (uintptr_t)p < 0x0000800000000000ULL && !((uintptr_t)p & 7);
}

static inline void* fld_p(void* o, int off) {
    return obj_ok(o) ? *(void**)((uintptr_t)o + off) : NULL;
}

static inline float fld_f(void* o, int off) {
    return obj_ok(o) ? *(float*)((uintptr_t)o + off) : -999.0f;
}

static inline int list_count(void* l) {
    return obj_ok(l) ? *(int32_t*)((uintptr_t)l + 0x18) : -1;
}

static inline uint64_t propgo_now_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000ULL + (uint64_t)(ts.tv_nsec / 1000000);
}

static inline int read_str(void* s, char* buf, int cap) {
    if (!buf || cap <= 0) return 0;
    buf[0] = 0;
    uintptr_t p = (uintptr_t)s;
    if (p < 0x100000 || (p >= 0x0000800000000000ULL) || (p & 7)) return 0;
    uintptr_t k = *(uintptr_t*)p;
    if (k < 0x100000 || (k >= 0x0000800000000000ULL) || (k & 7)) return 0;
    int32_t len = *(int32_t*)(p + 0x10);
    if (len <= 0 || len > cap - 1 || len > 2048) return 0;
    uint16_t* ch = (uint16_t*)(p + 0x14);
    for (int i = 0; i < len; i++) buf[i] = (ch[i] < 128) ? (char)ch[i] : '?';
    buf[len] = 0;
    return 1;
}

static inline int il2cpp_object_class(void* o, char* out, int cap) {
    int ok = 0;
    if (!out || cap < 2) return 0;
    out[0] = 0;
    PROTECT(
        uintptr_t p = (uintptr_t)o;
        if (p >= 0x100000 && !(p & 7)) {
            uintptr_t k = *(uintptr_t*)p;
            if (k >= 0x100000 && !(k & 7)) {
                char* n = *(char**)(k + 0x10); int i = 0;
                if ((uintptr_t)n >= 0x100000) {
                    for (; i < cap - 1; i++) {
                        char c = n[i];
                        if (!c) break;
                        if (c < 0x20 || c >= 0x7f) { i = 0; break; }
                        out[i] = c;
                    }
                    out[i] = 0;
                    ok = (i > 0);
                }
            }
        }
    );
    if (!ok) out[0] = 0;
    return ok;
}

static inline void obj_class(void* o, char* buf, int cap) {
    if (!buf || cap <= 0) return;
    buf[0] = 0;
    if (!obj_ok(o)) { snprintf(buf, cap, "<null>"); return; }
    if (!il2cpp_object_class(o, buf, cap) || buf[0] == 0) {
        snprintf(buf, cap, "<badklass>");
    }
}

static inline void fld_v3(void* o, int off, float* v) {
    if (v) {
        v[0] = v[1] = v[2] = 0.0f;
        if (obj_ok(o)) memcpy(v, (void*)((uintptr_t)o + off), 12);
    }
}

// Hook registration struct
typedef struct HookRegistration {
    uint32_t rva;              // target offset in libil2cpp.so
    const char* tag;           // short tag for log
    const char* class_method;  // e.g. "TeamData::IsKnockedOut"
    const char* signature;     // e.g. "int32_t (void* self, int slot)"
    int mode;                  // jump/call mode
    void* hook_fn;             // replacement hook function
    fn8* orig_ptr;             // pointer to store trampoline to original function
} HookRegistration;

#ifdef __cplusplus
}
#endif

#endif // HOOK_COMMON_H
