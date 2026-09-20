#ifndef HOOK_DIAGNOSTICS_H
#define HOOK_DIAGNOSTICS_H

#include "hook_common.h"
#include "hook_combat.h"

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// Base Board Building FIFO & Tracking
// ============================================================================

#define BLDG_FIFO_CAP 16
#define BLDG_TRACK_CAP 24
#define BLDG_FORCED_CAP 64
#define TS_HIDDEN_CAP (BLDG_TRACK_CAP + BLDG_FORCED_CAP)

void bldg_track(void* go);
void bldg_force_track(void* go);
void bldg_fifo_push(const char* name);
int bldg_fifo_pop(char* out, int cap);

// ============================================================================
// Diagnostic & System Hooks
// ============================================================================

// Subsystems, Network & Login
void* hook_13(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_21(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_22(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_23(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_24(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_28(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// ScrollView, Roster & Textures
void* hook_37(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_42(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_43(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_44(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_45(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_50(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_52(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
float hook_8(void* a0, void* a1, void* a2, float def, void* a4);
float hook_53(void* a0, void* a1, float def, void* a3);

// Quest database & Act / Chapter Display
void* hook_67(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_68(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_69(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_70(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_71(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_72(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_73(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_74(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_75(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_76(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_77(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_78(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_79(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_80(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_81(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_82(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_83(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_84(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_85(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_86(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_87(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Base Buildings, Nodes & Camera
void* hook_88(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_89(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_90(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_92(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_93(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_94(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_95(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_96(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_97(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_98(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_99(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_100(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_101(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Relic Cards & Base Tap Fix
void* hook_102(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_103(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_104(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_105(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_106(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_107(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_108(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_109(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_110(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_111(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_112(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_113(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_114(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Base Edit Building Popup Presentation
void* hook_115(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_116(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_117(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_118(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_119(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_120(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_121(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Screen Transitions Hide / Restore (TSHIDE / RSHIDE)
void* hook_122(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_123(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_124(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_125(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_126(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_127(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_128(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_129(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_130(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_131(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_132(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_133(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_134(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_144(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Roster Scroll / Drag Fixes
void* hook_135(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_136(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_137(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Tutorial Bypass
void* hook_147(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_148(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_149(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Boss & Node Rating
void* hook_150(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_151(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_152(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Localization
void* hook_162(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

#ifdef __cplusplus
}
#endif

#endif // HOOK_DIAGNOSTICS_H
