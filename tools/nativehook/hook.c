// TFTF native inline-hook library: Master Hook Coordinator
// Modular architecture:
//   - hook_common.h       : Shared structures, reflection helpers, crash safety (PROTECT)
//   - hook_quest.h/.c     : Quest progression, residual team health & KO persistence, Act names
//   - hook_ui.h/.c        : HeroPortrait decoration, rarity frame, faction glyphs, TopBar clicks
//   - hook_combat.h/.c    : Combat combo state machine, Quality Gates 1-6, SP3 timelines, swipe specials, damage filters
//   - hook_diagnostics.h/.c: Diagnostics, base lighting, base buildings, tutorial bypass, ratings

#include <android/log.h>
#include <stdarg.h>
#include <setjmp.h>
#include <signal.h>
#include <ucontext.h>
#include <stdint.h>
#include <stddef.h>
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
#include "hook_common.h"
#include "hook_quest.h"
#include "hook_ui.h"
#include "hook_combat.h"
#include "hook_diagnostics.h"

// ============================================================================
// Global Shared State Definitions
// ============================================================================

uintptr_t g_base = 0;
strnew_t g_strnew = NULL;
arraynew_t g_arraynew = NULL;
void* g_empty_tags = NULL;
FILE* g_f = NULL;
__thread sigjmp_buf g_jb;
__thread volatile int g_prot = 0;
volatile int g_inhb = 0;
volatile int g_inqs = 0;

static struct sigaction g_oldsegv, g_oldbus;

// ============================================================================
// Crash Safety & Logging
// ============================================================================

static void seg_handler(int sig, siginfo_t* si, void* uc) {
    if (g_prot) siglongjmp(g_jb, 1);
    if (uc && g_base) {
        ucontext_t* u = (ucontext_t*)uc;
        uintptr_t pc = (uintptr_t)u->uc_mcontext.pc;
        uintptr_t fa = (uintptr_t)(si ? si->si_addr : 0);
        if (pc > g_base && pc - g_base < 0x4000000)
            flog("FAULT sig=%d pc_rva=0x%lx faultaddr=0x%lx", sig, (long)(pc - g_base), (long)fa);
    }
    struct sigaction* o = (sig == SIGBUS) ? &g_oldbus : &g_oldsegv;
    if (o->sa_flags & SA_SIGINFO) { if (o->sa_sigaction) o->sa_sigaction(sig, si, uc); }
    else if (o->sa_handler && o->sa_handler != SIG_DFL && o->sa_handler != SIG_IGN) o->sa_handler(sig);
    else { signal(sig, SIG_DFL); raise(sig); }
}

void flog(const char* fmt, ...) {
    char buf[1024];
    va_list ap; va_start(ap, fmt); vsnprintf(buf, sizeof buf, fmt, ap); va_end(ap);
    __android_log_print(ANDROID_LOG_INFO, "TFTFHOOK", "%s", buf);
    if (!g_f) {
        char fname[64];
        time_t rawtime;
        time(&rawtime);
        struct tm* ti = localtime(&rawtime);
        if (ti) {
            snprintf(fname, sizeof(fname), "tftf_%04d%02d%02d_%02d%02d%02d.log",
                     ti->tm_year + 1900, ti->tm_mon + 1, ti->tm_mday,
                     ti->tm_hour, ti->tm_min, ti->tm_sec);
        } else {
            snprintf(fname, sizeof(fname), "tftf_%ld.log", (long)rawtime);
        }

        const char* dirs[] = {
            "/sdcard/Documents",
            "/storage/emulated/0/Documents",
            "/sdcard/Download",
            "/storage/emulated/0/Download",
            "/sdcard/Android/data/com.kabam.bigrobot/files",
            "/data/data/com.kabam.bigrobot/files",
            NULL
        };

        for (int i = 0; dirs[i]; i++) {
            char logpath[256];
            snprintf(logpath, sizeof(logpath), "%s/%s", dirs[i], fname);
            g_f = fopen(logpath, "w");
            if (g_f) {
                __android_log_print(ANDROID_LOG_ERROR, "TFTFHOOK", "Logging to %s", logpath);
                fprintf(g_f, "LOG FILE OPENED: %s\n", logpath);
                fflush(g_f);
                break;
            }
        }
    }
    if (!g_f) return;
    fputs(buf, g_f); fputc('\n', g_f); fflush(g_f);
}

void log_key(const char* tag, void* s) {
    if (!g_f) return;
    uintptr_t p = (uintptr_t)s;
    if (p < 0x100000 || (p & 7)) return;
    int32_t len = *(int32_t*)((char*)s + 0x10);
    if (len < 0 || len > 300) return;
    uint16_t* ch = (uint16_t*)((char*)s + 0x14);
    char buf[320]; int i;
    for (i = 0; i < len; i++) buf[i] = (ch[i] < 128) ? (char)ch[i] : '?';
    buf[len] = 0;
    if (g_inhb) fputs("HB ", g_f);
    if (g_inqs) fputs("QS ", g_f);
    fputs(tag, g_f); fputc(' ', g_f); fputs(buf, g_f); fputc('\n', g_f);
    static int n = 0; if ((++n & 63) == 0) fflush(g_f);
}

// ============================================================================
// Generic Logging Thunk Generation
// ============================================================================

#define MKHOOK(i) \
  void* hook_##i(void* a0,void* a1,void* a2,void* a3,void* a4,void* a5,void* a6,void* a7){ \
    PROTECT( \
    if (H[i].jp == 2) flog("%s", H[i].tag); \
    else if (H[i].jp == 3) { char b[64]; void* r=a2; int n=0; \
      if((uintptr_t)r>=0x100000 && !((uintptr_t)r&7)){int32_t l=*(int32_t*)((char*)r+0x10); uint16_t*c=(uint16_t*)((char*)r+0x14); if(l>=0&&l<60){for(;n<l;n++)b[n]=(char)c[n];}} b[n]=0; \
      flog("%s show=%ld reason=%s", H[i].tag, (long)a1, b); } \
    else if (H[i].jp == 4) { char nm[40]; nm[0]=0; uintptr_t s=(uintptr_t)a0; uintptr_t cls=0; \
      if(s>=0x100000 && !(s&7)){ cls=*(uintptr_t*)s; if(cls>=0x100000 && !(cls&7)){ char* p=*(char**)(cls+0x10); \
        if((uintptr_t)p>=0x100000){ int k=0; for(;k<38;k++){ char ch=p[k]; if(ch<=0||ch>=127){break;} nm[k]=ch; } nm[k]=0; } } } \
      flog("%s cls=%lx %s = %ld", H[i].tag, cls, nm, (long)a1); } \
    else if (H[i].jp == 7) log_key(H[i].tag, a1); \
    else { void* k = H[i].jp ? (a0 ? *(void**)((char*)a0 + 8) : 0) : a0; log_key(H[i].tag, k); } \
    ); \
    return H[i].orig(a0,a1,a2,a3,a4,a5,a6,a7); }

MKHOOK(0) MKHOOK(1) MKHOOK(2) MKHOOK(3) MKHOOK(4) MKHOOK(5) MKHOOK(6) MKHOOK(7)
MKHOOK(9) MKHOOK(10) MKHOOK(11) MKHOOK(12) MKHOOK(14) MKHOOK(15) MKHOOK(16)
MKHOOK(17) MKHOOK(18) MKHOOK(19) MKHOOK(20)
MKHOOK(25) MKHOOK(26) MKHOOK(27) MKHOOK(29) MKHOOK(30)

#define MKENT(i) \
  void* hook_##i(void* a0,void* a1,void* a2,void* a3,void* a4,void* a5,void* a6,void* a7){ \
    void* r = H[i].orig(a0,a1,a2,a3,a4,a5,a6,a7); \
    PROTECT( int ent=-1; uintptr_t s=(uintptr_t)a0; \
      if(s>=0x100000 && !(s&7)){ uintptr_t el=*(uintptr_t*)(s+0x158); if(el>=0x100000 && !(el&7)) ent=*(int*)(el+0x18); } \
      int sz=-1; if((uintptr_t)r>=0x100000 && !((uintptr_t)r&7)) sz=*(int*)((char*)r+0x18); \
      flog("%s _entities=%d ret=%d", H[i].tag, ent, sz); ); \
    return r; }
MKENT(31) MKENT(32)

MKHOOK(34) MKHOOK(36) MKHOOK(38) MKHOOK(39) MKHOOK(40) MKHOOK(41)
MKHOOK(47) MKHOOK(48) MKHOOK(49) MKHOOK(51)
MKHOOK(54) MKHOOK(55) MKHOOK(91)

#define MKQS(i) \
  void* hook_##i(void* a0,void* a1,void* a2,void* a3,void* a4,void* a5,void* a6,void* a7){ \
    PROTECT( flog("%s begin", H[i].tag); ); \
    g_inqs++; \
    void* r = H[i].orig(a0,a1,a2,a3,a4,a5,a6,a7); \
    g_inqs--; \
    PROTECT( flog("%s end", H[i].tag); ); \
    return r; }
MKQS(59) MKQS(60) MKQS(61) MKQS(62) MKQS(63) MKQS(64) MKQS(65) MKQS(66)

// ============================================================================
// Master Hook Table H[] (179 entries)
// ============================================================================

HookDef H[] = {
    { 0x144F534, "S",  0, 0 },   // 0 EB.Dot.String
    { 0x1451998, "O",  0, 0 },   // 1 EB.Dot.Object
    { 0x1460038, "F",  0, 0 },   // 2 EB.Dot.Find
    { 0x145FEA8, "I",  0, 0 },   // 3 EB.Dot.Integer
    { 0x14620B0, "L",  0, 0 },   // 4 EB.Dot.Long
    { 0x1464720, "fI", 1, 0 },   // 5 EB.Fast.Dot.Integer
    { 0x1451344, "fS", 1, 0 },   // 6 EB.Fast.Dot.String
    { 0x146428C, "fO", 1, 0 },   // 7 EB.Fast.Dot.Object
    { 0x1464A24, "fG", 1, 0 },   // 8 EB.Fast.Dot.Single
    { 0x1464800, "fB", 1, 0 },   // 9 EB.Fast.Dot.Bool
    { 0x1463DFC, "fF", 1, 0 },   // 10 EB.Fast.Dot.Find
    { 0x1464E0C, "fSL",1, 0 },   // 11 EB.Fast.Dot.StringList
    { 0xA62348,  "==HERO==",  2, 0 },   // 12 BCGUserHeroBase.ctor
    { 0xC15708,  "==BP==",    2, 0 },   // 13 BCGBlueprintBase.ctor
    { 0xB030A8,  "==BPtf==",  2, 0 },   // 14 TFBCGBlueprintBase.ctor
    { 0xC175E4,  "==CHAR==",  2, 0 },   // 15 BCGCharacterData.ctor
    { 0xB034E4,  "==CHARtf==",2, 0 },   // 16 TFBCGCharacterData.ctor
    { 0x158C87C, "LOADSCR",   3, 0 },   // 17 WindowManager.ShowLoadingScreen
    { 0xC5F728,  ">>HomeFlow.Enter", 2, 0 }, // 18
    { 0x15E2B90, ">>StartBranch",    2, 0 }, // 19 TutorialManager.StartBranch
    { 0x1361518, ">>DownloadAll",    2, 0 }, // 20 ODRManager.DownloadAllCoroutine
    { 0xFC35E4,  "CONNLIST",  5, 0 }, // 21 Hub.SubSystemConnecting
    { 0x1593888, "fixXlate",  6, 0 }, // 22 EB.Sparx.XlateManager.Connect
    { 0xD64370,  "fixQuestL", 6, 0 }, // 23 Legacy.QuestsManager.Connect
    { 0xD6A1B0,  "fixQuestN", 6, 0 }, // 24 Quests.QuestsManager.Connect
    { 0x15E29B8, "STARTTUT",  7, 0 }, // 25 TutorialManager.StartTutorial
    { 0x15E2A9C, "ESBRANCH",  7, 0 }, // 26 TutorialManager.EarlyStartBranch
    { 0x15E2C84, "COMPTUT",   7, 0 }, // 27 TutorialManager.CompleteTutorial
    { 0xC210D4,  "GETENT",    9, 0 }, // 28 BCGHelper.GetEntities
    { 0xC1B364,  "GETBP",     0, 0 }, // 29 BCGHelper.GetBlueprint
    { 0xC20C70,  "GBPC",      0, 0 }, // 30 BCGHelper.GetBlueprintForCharacter
    { 0xC5ADE4,  "ASF",      23, 0 }, // 31 HeroesScreen.ApplySortingAndFilter
    { 0xC5B0E4,  "GSH",      23, 0 }, // 32 HeroesScreen.GetSortedHeroes
    { 0x0E8DF9C, "RFD",       2, 0 }, // 33 HeroPortrait.RefreshFromData
    { 0xE7CDF4,  "DSREADY",   2, 0 }, // 34 Grid.onDynamicScrollReady
    { 0x0E8002C, "SEI",       2, 0 }, // 35 HeroPortrait.SetEnabledItems
    { 0x165AD44, "IPS",      21, 0 }, // 36 DynamicScrollView.CalculateItemsPerScreen
    { 0x165AF78, "CSVD",     22, 0 }, // 37 DynamicScrollView.CacheScrollViewDimensions
    { 0x165A01C, "MPS",      21, 0 }, // 38 DynamicScrollView.GetMaxPoolSize
    { 0x1659CFC, "CREATEITEM",2, 0 }, // 39 DynamicScrollView.CreateItem
    { 0x165960C, "DSVINIT",   2, 0 }, // 40 DynamicScrollView.Initialize
    { 0xE7C4C4,  "GRIDINIT",  2, 0 }, // 41 Grid.Initialize
    { 0xC57578,  "SETSCR",    2, 0 }, // 42 HeroesScreen.SetScreenType
    { 0xC584CC,  "OWNS",      8, 0 }, // 43 HeroesScreen.userOwnsBot
    { 0xE910DC, "TEXPATH",  30, 0 }, // 44 HeroPortrait.LoadTexture
    { 0xC21AC4, "==HEROBASE==",2, 0 }, // 45 BCGHeroBase..ctor
    { 0xE916B4, "TEXDONE",  31, 0 }, // 46 HeroPortrait.OnHeroTextureLoaded
    { 0xC58598, "SHOWGRID",  2, 0 }, // 47 HeroesScreen.ShowGridContainer
    { 0xC59EE4, "ANIMNEW",   2, 0 }, // 48 HeroesScreen.AnimateNewEntities
    { 0xC59E90, "INTRODONE", 2, 0 }, // 49 HeroesScreen.OnIntroTransitionComplete
    { 0x1991FD0,"SETPATH",  30, 0 }, // 50 UITextureRef.set_baseTexturePath
    { 0x1992610,"UITLOAD",   2, 0 }, // 51 UITextureRef.LoadTexture
    { 0x14641FC,"FDS2",     34, 0 }, // 52 EB.Fast.Dot.String
    { 0x1451394,"hbF",       1, 0 }, // 53 fast-dot float w/ default
    { 0x1464770,"hbI",       1, 0 }, // 54 fast-dot int w/ default
    { 0x1464ccc,"hbL",       1, 0 }, // 55 fast-dot list reader
    { 0xDAB16C, "FIXFIGHT",  2, 0 }, // 56 PlayerAttributes.Init
    { 0x12A9D94,"FIXHS",     2, 0 }, // 57 HashSet<T>..ctor
    { 0xD35130, "SETACTFIX",  2, 0 }, // 58 PlayerInput.QueuedAction.SetAction
    { 0x12E3214, "==QLIST==",  99, 0 }, // 59 QuestDB.AddQuestSummarys
    { 0x10381F0, "==QSET==",   99, 0 }, // 60 Legacy.QuestSet.AddQuestSummarys
    { 0x12E4110, "==QDET==",   99, 0 }, // 61 QuestDB.AddQuestDetails
    { 0x12E43C0, "==QACT==",   99, 0 }, // 62 QuestDB.AddActiveQuests
    { 0x12E4EC8, "==QBUILD==", 99, 0 }, // 63 QuestDB.BuildActiveQuest
    { 0x103A0E4, "==QSDET==",  99, 0 }, // 64 Legacy.QuestSet.AddQuestDetails
    { 0x122C93C, "==QSUM==",   99, 0 }, // 65 Summary.Deserialize
    { 0x12EF810, "==QMAP==",   99, 0 }, // 66 QuestMap.Deserialize
    { 0x12E30E8, "QVISCNT",  97, 0 }, // 67 QuestDB.GetQuestSetVisibleCount
    { 0x12E3024, "QSETCNT",  97, 0 }, // 68 QuestDB.GetQuestSetCount
    { 0x12E2E30, "QSETFROM", 97, 0 }, // 69 QuestDB.GetQuestSetFromCategory
    { 0x103A46C, "FORCEUNLK", 2, 0 }, // 70 QuestSummary.get_unlocked
    { 0xC2ADC8, "FORCEACT",  2, 0 }, // 71 Act.UpdateProgression
    { 0xCB2954, "FORCELOCK", 2, 0 }, // 72 QuestSelectPanelBase.get_isLocked
    { 0x00CB4980, "REFRESH_DISP", 2, 0 }, // 73 QuestSelectPanelBase.RefreshDisplay
    { 0xD13E78, "FORCECHAP", 2, 0 }, // 74 Chapter.UpdateProgression
    { 0xD15394, "CHAPCLK",   2, 0 }, // 75 ChapterPanel.OnPanelClicked
    { 0xD14470, "FORCECHAPSD", 2, 0 }, // 76 ChapterPanel.SetData
    { 0x152B570, "FIXWRAPMI", 2, 0 }, // 77 SafeAction.<Wrap>b__0<object>
    { 0xEF28CC, "NEWENTITY", 2, 0 }, // 78 Quests.Builder.NewEntity
    { 0xA6EB98, "BASEDIAG", 2, 0 }, // 79 BaseBoard.OnBaseBoardBuildComplete
    { 0xCF52DC, "BASEAPPLY", 2, 0 }, // 80 BaseRenderSettings.ApplyBaseSettings
    { 0x18C2CA4, "RSACTIVE", 2, 0 }, // 81 EBRenderSettingsBase.ApplyWhenActivated
    { 0x124BDE8, "TODAPPLY", 2, 0 },  // 82 EBTimeOfDayManager.EBTimeOfDay.Apply
    { 0x18C5150, "TODMGRAPPLY", 2, 0 }, // 83 EBTimeOfDayManager.Apply
    { 0xB64608, "FIXTERRAIN", 2, 0 }, // 84 GameboardBuilder.FixTerrain
    { 0x1ABF03C, "PRINIT", 2, 0 },   // 85 EBPlanarReflectionManager.Init
    { 0x1ABFCF0, "PRRENDER", 2, 0 }, // 86 EBPlanarReflectionManager.Render
    { 0x1ABECE4, "PRSETUP", 2, 0 },  // 87 EBPlanarReflectionManager.Setup
    { 0xDA8270,  "PRCONFIG", 2, 0 }, // 88 PerformanceManager.LoadPlanarReflectionConfig
    { 0xA6FF98, "BASENODE",   2, 0 }, // 89 BaseBoard.AttachNodeController
    { 0xCF2D30, "NODEREFRESH",2, 0 }, // 90 BaseNodeController.Refresh
    { 0xB67944, "SETBLDG",    3, 0 }, // 91 GameboardBuilder.SetBuilding
    { 0xB67AB4, "LOADBLDG",   7, 0 }, // 92 GameboardBuilder.LoadBuildingObject
    { 0xCF4854, "ONBLDSET",   2, 0 }, // 93 BaseNodeController.OnBuildingSet
    { 0x121C634, "CAMFRAME",  2, 0 }, // 94 BaseCameraController.get__CurrentPosOffset
    { 0xB67CC0, "BLDGSWAP",  2, 0 }, // 95 GameboardBuilder.SpawnBuilding
    { 0xA6F844, "BLDGLEAVE", 2, 0 }, // 96 BaseBoard.LeaveBoard
    { 0xA71810, "CARDTAP",    2, 0 }, // 97 BaseBoard.OnCardTapped
    { 0xA712FC, "TILEBLDG",   2, 0 }, // 98 BaseBoard.HandleTileBuildingInteraction
    { 0xA70A80, "EDITPOP",    3, 0 }, // 99 BaseBoard.OpenBaseEditBuildingPopup
    { 0x121D450,"POPENTER",  2, 0 }, // 100 BaseEditBuildingPopup.WindowEnter
    { 0x1220D40,"NODEPOP",   2, 0 }, // 101 BaseEditNodePopup.WindowEnter
    { 0x14F8578,"FTEBASEFIX",2, 0 }, // 102 TutorialManagerHelper.IsBranchComplete
    { 0xE27978, "RCINIT",    3, 0 }, // 103 RelicCard.Init
    { 0xE27888, "RCSHOW",    2, 0 }, // 104 RelicCard.Show
    { 0xE2791C, "RCHIDE",    2, 0 }, // 105 RelicCard.Hide
    { 0xE27B78, "RCACTIVE", 2, 0 }, // 106 RelicCard.UpdateActiveGameObject
    { 0xE27A80, "RCCOLLIDER",2, 0 }, // 107 RelicCard.UpdateCollider
    { 0xE27D94, "RCCLICK",   2, 0 }, // 108 RelicCard.OnClick
    { 0xCF3584, "CARDLOAD",  2, 0 }, // 109 BaseNodeController.OnRelicCardLoaded
    { 0xA7223C, "SHOWCARDS", 2, 0 }, // 110 BaseBoard.ShowAllNodeCards
    { 0xA708B0, "HIDECARDS", 2, 0 }, // 111 BaseBoard.HideAllNodeCards
    { 0xE27680, "RCAWAKE",   2, 0 }, // 112 RelicCard.Awake
    { 0x1BF84A4,"UICLICK",   2, 0 }, // 113 UIEventListener.OnClick
    { 0x1F82794,"BASETAPFIX",3, 0 }, // 114 UICamera.ProcessTouch
    { 0xC407D4, "POPINITSM",  1, 0 }, // 115 <DoWindowInitialization>d__11.MoveNext
    { 0x121D670,"POPINIT",    3, 0 }, // 116 BaseEditBuildingPopupPresentation.Init
    { 0x121D7EC,"POPSETPARAM",3, 0 }, // 117 BaseEditBuildingPopupPresentation.SetEnterParams
    { 0x121E540,"POPBUILD",   1, 0 }, // 118 BaseEditBuildingPopupPresentation.BuildPresentation
    { 0x121EBF8,"POPLIST",    2, 0 }, // 119 BaseEditBuildingPopupPresentation.GetBuildingList
    { 0x1220128,"POPFILTER",  3, 0 }, // 120 BaseEditBuildingPopupPresentation.FilterBuildingData
    { 0x121D89C,"POPUPDATE",  2, 0 }, // 121 BaseEditBuildingPopupPresentation.UpdatePresentation
    { 0xF9D614, "TSINIT",     0, 0 }, // 122 TeamSelectPresentation.Init
    { 0xF9E6DC, "TSPLAT",     0, 0 }, // 123 TeamSelectPresentation.SetupPlatform
    { 0xF9F9A8, "TSINTRO",    0, 0 }, // 124 TeamSelectPresentation.OnIntroTransitionEnd
    { 0xA6FAF0, "TSSHOW",     0, 0 }, // 125 BaseBoard.ResumeBoard
    { 0xA6FB54, "TSSHOWW",    0, 0 }, // 126 BaseBoard.OnWindowEntered
    { 0xF97D04, "TSDOWN",     0, 0 }, // 127 TeamSelectPresentation.TearDown
    { 0xF9FFE4, "TSOUTRO",    2, 0 }, // 128 TeamSelectPresentation.OnOutroTransitionBegin
    { 0xFA06D0, "TSOUTBG",    0, 0 }, // 129 TeamSelectPresentation.OnOutroBlurredBackgroundUp
    { 0xF97B10, "TSBACK",     2, 0 }, // 130 TeamSelectPresentation.OnBackClicked
    { 0xF9D200, "TSPODD",     0, 0 }, // 131 TeamSelectPodium.Deactivate
    { 0xF9CFE8, "TSPODC",     0, 0 }, // 132 TeamSelectPodium.Cleanup
    { 0xC587B8, "RSENTER",    0, 0 }, // 133 HeroesScreen.WindowEnter
    { 0xC595AC, "RSEXIT",     0, 0 }, // 134 HeroesScreen.WindowExit
    { 0xB210CC, "ROSTERDRAGFIX", 2, 0 }, // 135 EditTeamScreenPresentation.OnGridItemClicked
    { 0x1E5F444, "ROSTERDRAGCTX",   2, 0 }, // 136 UIScrollView.Drag
    { 0x1404E6C, "ROSTERDRAGCHOKE", 2, 0 }, // 137 UIScrollView.OnDragNotification.Invoke
    { 0xEA023C, "PROPGOACT", 2, 0 }, // 138 PropData.SetActiveInternal
    { 0x100A76C, "SP3MOVE", 2, 0 }, // 139 MoveSet.GetMove
    { 0xDE7CF4, "SP3XNEW", 2, 0 }, // 140 Simulation.RegisterComponents
    { 0x117A67C, "SP3XHOLD", 2, 0 }, // 141 PlayerController.Transform
    { 0x1174038, "SP3XIN", 2, 0 }, // 142 PlayerCinematicSpecialAttackState.OnEnter
    { 0x1174484, "SP3XOUT", 2, 0 }, // 143 PlayerCinematicSpecialAttackState.OnExit
    { 0xE746B8, "RSHOME",  0, 0 }, // 144 TransformersHomeScreen.WindowEnter
    { 0xDE8750, "SP3BEAT", 2, 0 }, // 145 Simulation.FixedUpdate
    { 0xDB1D30, "AIRANGE", 2, 0 }, // 146 AIController.Simulate
    { 0x14F4468, "BOTDUPEDCHECK", 2, 0 }, // 147 BotDuped check/start entry
    { 0x1BF0C20, "TUTUIHOOKTOGGLE", 2, 0 }, // 148 TutorialUIHook.ToggleEnabled
    { 0x1BF0D10, "TUTUIHOOKCLICK", 2, 0 }, // 149 TutorialUIHook.Clicked
    { 0xBE2230,  "CALC_RATING_CB",     0, 0 }, // 150 <CalculateNodeRating>b__0
    { 0xE50A44,  "CALC_RATING_ENTER",  0, 0 }, // 151 BossCard.CalculateNodeRating
    { 0xFEAFA0,  "HUD_PLAYER_INFO_INIT", 0, 0 }, // 152 HudPlayerInfo.Init
    { 0x1174300, "PCSPECIAL",          2, 0 }, // 153 PlayerController.SpecialAttack
    { 0x1179AF4, "PCACTION",           2, 0 }, // 154 PlayerController.Action
    { 0x0E34640, "SPEXIT",             2, 0 }, // 155 PlayerSpecialAttackState.OnExit
    { 0x0DADA6C, "ROLL_CRIT",          2, 0 }, // 156 PlayerAttributes.RollForCriticalHit
    { 0x0E3D8CC, "PREFIGHT_HP",        2, 0 }, // 157 PrefightScreenData.GetTeamMemberHealth
    { 0x10E1E54, "TEAMDATA_IS_KO",     2, 0 }, // 158 TeamData.IsKnockedOut
    { 0x10E1AE4, "TEAMDATA_GET_HP",    2, 0 }, // 159 TeamData.GetHP
    { 0x0D32A00, "BLOCKENTER",         2, 0 }, // 160 PlayerBlockState.OnEnter
    { 0xC16688,  "GET_MAP_ASSET_ID",   2, 0 }, // 161 BCGBlueprintBase.get_MapAssetID
    { 0x127F794, "LOCALIZE",           2, 0 }, // 162 Localization.Get
    { 0x11794A4, "ADDMANA",            2, 0 }, // 163 PlayerController.AddMana
    { 0xC1F2B8,  "GET_TOP_HERO_ID",    2, 0 }, // 164 BCGHelper.GetTopHeroId
    { 0x0D34E6C, "DODGEENTER",         2, 0 }, // 165 PlayerDodgeState.OnEnter
    { 0x00C2BE04, "ACT_NAME",          2, 0 }, // 166 ActPanel.get_panelDisplayNameText
    { 0x0E8F33C, "PORTRAIT_GET_HP",    2, 0 }, // 167 HeroPortrait.get_healthPercentage
    { 0x1173FA4, "PCGETSPTIER",        2, 0 }, // 168 PlayerController.GetAvailableSpecialTier
    { 0xFF05C8,  "HUDSPBTN",           2, 0 }, // 169 HudSpecialMeter.OnSpecialButtonPressed
    { 0x11CFCAC, "QUEST_TEX",          2, 0 }, // 170 SelectQuestTile.SetTexturePath
    { 0x1173848, "BLOCKENTER2",        2, 0 }, // 171 PlayerBlockState.OnEnter2 (fires)
    { 0x117E4AC, "DODGEENTER2",        2, 0 }, // 172 PlayerDodgeState.OnEnter2 (fires)
    { 0x141CD54, "ONHCCLICK",          2, 0 }, // 173 TransformersTopBarPresentation.OnHardCurrencyClick
    { 0x0DA0720, "GETDEFTAB",          2, 0 }, // 174 PayoutsModel.GetDefaultTabId
    { 0xF9A7F8,  "TS_GET_TEAM",        2, 0 }, // 175 TeamSelectModel.get_Team
    { 0xB16C54,  "ET_INIT_HEROES",     2, 0 }, // 176 EditTeamModel.InitHeroes
    { 0x0DAD5A4, "APPLY_DMG",          2, 0 }, // 177 PlayerAttributes.ApplyDamage
    { 0x0E3D688, "PFS_ENEMY_HP",       2, 0 }  // 178 PrefightScreenData.GetEnemyNormalizedHealth
};
#define NH (int)(sizeof(H)/sizeof(H[0]))

// ============================================================================
// Master Handlers Dispatch Table
// ============================================================================

static void* handlers[] = {
    // 0..7: FastDot generic loggers
    hook_0, hook_1, hook_2, hook_3, hook_4, hook_5, hook_6, hook_7,
    // 8: FastDot Single with auto-revive logic (diagnostics)
    (void*)hook_8,
    // 9..12: FastDot generic loggers
    hook_9, hook_10, hook_11, hook_12,
    // 13: BCGBlueprintBase ctor (diagnostics)
    hook_13,
    // 14..20: Diagnostic markers & Loading Screen
    hook_14, hook_15, hook_16, hook_17, hook_18, hook_19, hook_20,
    // 21..24: Subsystem connection fixes (diagnostics)
    hook_21, hook_22, hook_23, hook_24,
    // 25..27: Tutorial markers
    hook_25, hook_26, hook_27,
    // 28: BCGHelper.GetEntities (diagnostics)
    hook_28,
    // 29..32: Roster & Blueprint loggers
    hook_29, hook_30, hook_31, hook_32,
    // 33: HeroPortrait.RefreshFromData (UI module)
    hook_HeroPortrait_RefreshFromData,
    // 34: ScrollView ready marker
    hook_34,
    // 35: HeroPortrait.SetEnabledItems (UI module)
    hook_HeroPortrait_SetEnabledItems,
    // 36..41: ScrollView & Grid markers
    hook_36, hook_37, hook_38, hook_39, hook_40, hook_41,
    // 42..45: Roster & HeroBase ctor (diagnostics)
    hook_42, hook_43, hook_44, hook_45,
    // 46: HeroPortrait.OnHeroTextureLoaded (UI module)
    hook_HeroPortrait_OnHeroTextureLoaded,
    // 47..51: Roster reveal & texture load markers
    hook_47, hook_48, hook_49, hook_50, hook_51,
    // 52..53: FastDot string & float readers (diagnostics)
    hook_52, (void*)hook_53,
    // 54..55: FastDot int & list readers
    hook_54, hook_55,
    // 56..58: Combat Initialization & Input Window (Combat module)
    hook_PlayerAttributes_Init, hook_HashSet_ctor, hook_PlayerInput_QueuedAction_SetAction,
    // 59..66: Quest DB deserialization brackets
    hook_59, hook_60, hook_61, hook_62, hook_63, hook_64, hook_65, hook_66,
    // 67..73: Quest visibility, Act/Chapter Progression (diagnostics)
    hook_67, hook_68, hook_69, hook_70, hook_71, hook_72, hook_73,
    // 74..78: ChapterPanel & SafeAction Wrap (diagnostics)
    hook_74, hook_75, hook_76, hook_77, hook_78,
    // 79..88: Base Lighting & Reflections (diagnostics)
    hook_79, hook_80, hook_81, hook_82, hook_83, hook_84, hook_85, hook_86, hook_87, hook_88,
    // 89..96: Base Board Nodes, Buildings, Camera (diagnostics)
    hook_89, hook_90, hook_91, hook_92, hook_93, hook_94, hook_95, hook_96,
    // 97..102: Base Edit Popups & FTE Tutorial Bypass (diagnostics)
    hook_97, hook_98, hook_99, hook_100, hook_101, hook_102,
    // 103..114: Relic Cards & Base Tap Input Fix (diagnostics)
    hook_103, hook_104, hook_105, hook_106, hook_107, hook_108, hook_109, hook_110, hook_111, hook_112, hook_113, hook_114,
    // 115..121: Base Edit Building Presentation (diagnostics)
    hook_115, hook_116, hook_117, hook_118, hook_119, hook_120, hook_121,
    // 122..134: Screen Transitions Hide/Restore (TSHIDE/RSHIDE) (diagnostics)
    hook_122, hook_123, hook_124, hook_125, hook_126, hook_127, hook_128, hook_129, hook_130, hook_131, hook_132, hook_133, hook_134,
    // 135..137: Roster Drag & Picker SIGSEGV Guards (diagnostics)
    hook_135, hook_136, hook_137,
    // 138..143: Alternate Form Rendering & SP3 Timelines (Combat module)
    hook_PropData_SetActiveInternal, hook_MoveSet_GetMove, hook_Simulation_RegisterComponents,
    hook_PlayerController_Transform, hook_PlayerCinematicSpecialAttackState_OnEnter, hook_PlayerCinematicSpecialAttackState_OnExit,
    // 144: TransformersHomeScreen.WindowEnter restore (diagnostics)
    hook_144,
    // 145..146: Combat Simulation Tick & AI Ranged Attacks (Combat module)
    hook_Simulation_FixedUpdate, (void*)hook_AIController_Simulate,
    // 147..152: Tutorial Bypass & Boss Card Node Rating (diagnostics)
    hook_147, hook_148, hook_149, hook_150, hook_151, hook_152,
    // 153..156: Combat Specials, Actions & Critical Hits (Combat module)
    hook_PlayerController_SpecialAttack, hook_PlayerController_Action, hook_PlayerSpecialAttackState_OnExit, hook_PlayerAttributes_RollForCriticalHit,
    // 157..159: Team Health Persistence & Knockout (Quest module)
    hook_PrefightScreenData_SetCurrentHero, (void*)hook_TeamData_IsKnockedOut, (void*)hook_TeamData_GetHP,
    // 160: Combat Guard State Enter (Combat module)
    hook_PlayerBlockState_OnEnter,
    // 161: Map Asset ID Resolution (UI module)
    hook_BCGBlueprintBase_get_MapAssetID,
    // 162: Chinese / English Localization Override (diagnostics)
    hook_162,
    // 163: Dynamic Mana Scaling (Combat module)
    hook_PlayerController_AddMana,
    // 164: Squad Leader Avatar (UI module)
    hook_BCGHelper_GetTopHeroId,
    // 165: Combat Dodge State Enter (Combat module)
    hook_PlayerDodgeState_OnEnter,
    // 166: Act Display Name Override (Quest module)
    hook_ActPanel_get_panelDisplayNameText,
    // 167: Residual Health Percentage on Portrait (UI module)
    (void*)hook_HeroPortrait_get_healthPercentage,
    // 168..169: Combat Swipe Special Tiers & Special Button (Combat module)
    hook_PlayerController_GetAvailableSpecialTier, hook_HudSpecialMeter_OnSpecialButtonPressed,
    // 170: Custom Quest Tile Textures (Quest module)
    hook_SelectQuestTile_SetTexturePath,
    // 171..172: Active Guard & Dodge Handlers (Combat module)
    hook_PlayerBlockState_OnEnter2, hook_PlayerDodgeState_OnEnter2,
    // 173..174: TopBar Currency Redirection & Payouts Model Tab Guard (UI module)
    hook_TransformersTopBarPresentation_OnHardCurrencyClick, hook_PayoutsModel_GetDefaultTabId,
    // 175..176: Team Select Persistence & Rodimus Prime Restriction (Quest module)
    hook_TeamSelectModel_get_Team, hook_EditTeamModel_InitHeroes,
    // 177: Starscream's Picnic 1.1.7 Ranged-Only Damage Filter (Combat module)
    (void*)hook_PlayerAttributes_ApplyDamage,
    // 178: Prefight Enemy Health Ratio Persistence (Quest module)
    (void*)hook_PrefightScreenData_GetEnemyNormalizedHealth
};

// ============================================================================
// Trampoline & Dynamic Hook Engine
// ============================================================================

static void write_jump(uint8_t* dst, void* target){
    uint32_t* p = (uint32_t*)dst;
    p[0] = 0x58000051;          // ldr x17, #8
    p[1] = 0xD61F0220;          // br  x17
    *(uint64_t*)(dst + 8) = (uint64_t)target;
}

static int relocate(uint8_t* tr, uint8_t* src, int ninstr){
    int o = 0;
    for (int i = 0; i < ninstr; i++){
        uint32_t in = *(uint32_t*)(src + i*4);
        uint64_t pc = (uint64_t)(src + i*4);
        if ((in & 0x7C000000) == 0x14000000){ // B / BL (imm26)
            int64_t off = (int64_t)(in << 6) >> 4; uint64_t tgt = pc + off;
            uint32_t link = in & 0x80000000;
            *(uint32_t*)(tr+o)=0x58000050; o+=4;
            *(uint32_t*)(tr+o)= link?0xD63F0200:0xD61F0200; o+=4;
            *(uint64_t*)(tr+o)=tgt; o+=8;
        } else if ((in & 0xFF000010) == 0x54000000){ // B.cond (imm19)
            int64_t off = (int64_t)((in>>5)&0x7FFFF); off=(off<<45)>>43; uint64_t tgt=pc+off;
            uint32_t cond = in & 0xF;
            *(uint32_t*)(tr+o)=0x54000000 | (0x14>>2<<5) | (cond^1); o+=4;
            *(uint32_t*)(tr+o)=0x58000050; o+=4; *(uint32_t*)(tr+o)=0xD61F0200; o+=4; *(uint64_t*)(tr+o)=tgt; o+=8;
        } else if ((in & 0x7E000000) == 0x34000000){ // CBZ/CBNZ (imm19)
            int64_t off=(int64_t)((in>>5)&0x7FFFF); off=(off<<45)>>43; uint64_t tgt=pc+off;
            uint32_t inv = in ^ 0x01000000;
            *(uint32_t*)(tr+o)=(inv & 0xFF00001F) | (0x14>>2<<5); o+=4;
            *(uint32_t*)(tr+o)=0x58000050; o+=4; *(uint32_t*)(tr+o)=0xD61F0200; o+=4; *(uint64_t*)(tr+o)=tgt; o+=8;
        } else if ((in & 0x7E000000) == 0x36000000){ // TBZ/TBNZ (imm14)
            int64_t off=(int64_t)((in>>5)&0x3FFF); off=(off<<50)>>48; uint64_t tgt=pc+off;
            uint32_t inv = in ^ 0x01000000;
            *(uint32_t*)(tr+o)=(inv & 0xFFF8001F) | (0x14>>2<<5); o+=4;
            *(uint32_t*)(tr+o)=0x58000050; o+=4; *(uint32_t*)(tr+o)=0xD61F0200; o+=4; *(uint64_t*)(tr+o)=tgt; o+=8;
        } else if ((in & 0x9F000000) == 0x10000000){ // ADR (imm)
            uint32_t rd=in&0x1F; int64_t imm=(((in>>5)&0x7FFFF)<<2)|((in>>29)&3); imm=(imm<<43)>>43;
            uint64_t tgt=pc+imm;
            *(uint32_t*)(tr+o)=0x58000040|rd; o+=4; *(uint32_t*)(tr+o)=0x14000003; o+=4; *(uint64_t*)(tr+o)=tgt; o+=8;
        } else if ((in & 0x9F000000) == 0x90000000){ // ADRP
            uint32_t rd=in&0x1F; int64_t imm=(((in>>5)&0x7FFFF)<<2)|((in>>29)&3); imm=(imm<<43)>>43; imm<<=12;
            uint64_t tgt=(pc & ~0xFFFULL)+imm;
            *(uint32_t*)(tr+o)=0x58000040|rd; o+=4; *(uint32_t*)(tr+o)=0x14000003; o+=4; *(uint64_t*)(tr+o)=tgt; o+=8;
        } else if ((in & 0x3B000000) == 0x18000000){ // LDR (literal)
            uint32_t rt=in&0x1F; int64_t off=(int64_t)((in>>5)&0x7FFFF); off=(off<<45)>>43; uint64_t tgt=pc+off;
            int is64 = (in>>30)&1;
            *(uint32_t*)(tr+o)=0x58000040|rt; o+=4; *(uint32_t*)(tr+o)=0x14000003; o+=4; *(uint64_t*)(tr+o)=tgt; o+=8;
            *(uint32_t*)(tr+o)= is64 ? (0xF9400000|rt|(rt<<5)) : (0xB9400000|rt|(rt<<5)); o+=4;
        } else {
            *(uint32_t*)(tr+o)=in; o+=4;
        }
    }
    return o;
}

static int inline_hook(void* target, void* handler, fn8* orig_out){
    uint8_t* t = (uint8_t*)target;
    uint32_t first = *(uint32_t*)t;
    uintptr_t pg = (uintptr_t)t & ~0xFFFUL;
    if (mprotect((void*)pg, 0x2000, PROT_READ|PROT_WRITE|PROT_EXEC) != 0) { LOG("mprotect fail %p", t); return -1; }
    uint8_t* tr = (uint8_t*)mmap(NULL, 256, PROT_READ|PROT_WRITE|PROT_EXEC, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
    if (tr == MAP_FAILED) { LOG("mmap fail"); return -1; }
    int trlen = relocate(tr, t, 4);
    write_jump(tr + trlen, t + 16);
    __builtin___clear_cache((char*)tr, (char*)tr + trlen + 16);
    *orig_out = (fn8)tr;
    write_jump(t, handler);
    __builtin___clear_cache((char*)t, (char*)t + 16);
    LOG("hooked %p (first was %08x) tramp=%p", t, first, tr);
    return 0;
}

static int find_cb(struct dl_phdr_info* info, size_t sz, void* data){
    if (info->dlpi_name && strstr(info->dlpi_name, "libil2cpp.so")) { g_base = (uintptr_t)info->dlpi_addr; return 1; }
    return 0;
}

static void poke32(uintptr_t rva, uint32_t word){
    uint8_t* t = (uint8_t*)(g_base + rva);
    uintptr_t pg = (uintptr_t)t & ~0xFFFUL;
    if (mprotect((void*)pg, 0x2000, PROT_READ|PROT_WRITE|PROT_EXEC) != 0){ LOG("poke mprotect fail 0x%lx", (long)rva); return; }
    uint32_t old = *(uint32_t*)t;
    *(uint32_t*)t = word;
    __builtin___clear_cache((char*)t, (char*)t + 4);
    LOG("poked 0x%lx : %08x -> %08x", (long)rva, old, word);
}

// ============================================================================
// FPS & Performance Overrides
// ============================================================================

static fn8 orig_set_targetFrameRate = NULL;
static void* hooked_set_targetFrameRate(void* fps, void* m, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7){
    int req_fps = (int)(intptr_t)fps;
    int target_fps = tftf_get_target_fps();
    if (target_fps <= 0) target_fps = 60;
    LOG("Application.set_targetFrameRate: req=%d -> forcing %d", req_fps, target_fps);
    if (orig_set_targetFrameRate) {
        return orig_set_targetFrameRate((void*)(intptr_t)target_fps, m, a2, a3, a4, a5, a6, a7);
    }
    return NULL;
}

static fn8 orig_set_vSyncCount = NULL;
static void* hooked_set_vSyncCount(void* count, void* m, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7){
    int req_vsync = (int)(intptr_t)count;
    LOG("QualitySettings.set_vSyncCount: req=%d -> forcing 0", req_vsync);
    if (orig_set_vSyncCount) {
        return orig_set_vSyncCount((void*)(intptr_t)0, m, a2, a3, a4, a5, a6, a7);
    }
    return NULL;
}

// ============================================================================
// Installer & Launcher Lifecycle
// ============================================================================

static void* installer(void* arg){
    for (int i = 0; i < 1200; i++) {           // up to 60s
        g_base = 0; dl_iterate_phdr(find_cb, NULL);
        if (g_base) break;
        usleep(50000);
    }
    if (!g_base) { LOG("libil2cpp.so NOT found"); return NULL; }
    LOG("libil2cpp.so base=%p", (void*)g_base);
    g_strnew = (strnew_t)dlsym(RTLD_DEFAULT, "il2cpp_string_new");
    if (!g_strnew) { void* h = dlopen("libil2cpp.so", RTLD_NOLOAD); if (h) g_strnew = (strnew_t)dlsym(h, "il2cpp_string_new"); }
    g_arraynew = (arraynew_t)dlsym(RTLD_DEFAULT, "il2cpp_array_new");
    if (!g_arraynew) { void* h = dlopen("libil2cpp.so", RTLD_NOLOAD); if (h) g_arraynew = (arraynew_t)dlsym(h, "il2cpp_array_new"); }

    for (int i = 0; i < NH; i++) {
        if (!H[i].rva) continue;
        inline_hook((void*)(g_base + H[i].rva), handlers[i], &H[i].orig);
    }

    // FIXSYN: BCGBlueprintBase.get_SynergyBonuses (@0xC17198) empty list on null
    poke32(0xC17278, 0xB4000640);

    // FIXSIG: BCGHeroBase.get_IsSignatureUnlocked (@0xC1C4A0) return 0 on null
    poke32(0xC1C4D8, 0xB40000A8);

    // UNLOCK_EVENT_BUTTON:
    // LevelLock.get_Locked (@0xF0C820): return false
    poke32(0xF0C820, 0x2A1F03E0);
    poke32(0xF0C824, 0xD65F03C0);

    // FightLandingPresentation.StartPendingTutorial (@0xEA8E30): return false
    poke32(0xEA8E30, 0x2A1F03E0);
    poke32(0xEA8E34, 0xD65F03C0);

    // FIXROSTER_DECO:
    poke32(0xE8E0FC, 0xD503201F);   // HeroPortrait.RefreshFromData: nop mUserOwned==0
    poke32(0xE80238, 0x52800001);   // HeroPortrait.SetEnabledItems: suppress empty progress bar
    poke32(0xC5C1C0, 0x52800361);   // HeroesScreen.OnGridItemInitialized: mask 0x1b
    poke32(0xC5C250, 0x528000A1);   // HeroesScreen: mov w1, #5 (instead of mov w1, wzr)
    poke32(0xC5C258, 0x9408D540);   // HeroesScreen: bl 0xE91758 (ForceSetRarityFrame(hp, 5))
    poke32(0xE80220, 0xD503201F);   // HeroPortrait.SetEnabledItems: nop deactivation loop
    poke32(0xC5D888, 0x52800361);   // HeroesScreen lambda: mask 0x1b

    // Graphics & Performance Enhancements
    int target_fps = tftf_get_target_fps();
    LOG("Applying target_fps setting: %d", target_fps);

    if (target_fps == 30) {
        poke32(0xDA52E0, 0x528003C0);   // mov w0, #30
        poke32(0xDA6700, 0x14000014);   // b _30NoVSync
    } else {
        poke32(0xDA52E0, 0x52800780);   // mov w0, #60
        poke32(0xDA6700, 0x14000009);   // b _60NoVSync
    }
    poke32(0xDA52F8, 0x2A1F03E0);       // vSyncCount = 0

    // GPU Particles, MRT, RT & Scene Destruction
    poke32(0xDA7E68, 0x52800020); poke32(0xDA7E6C, 0xD65F03C0); // CanDeviceRunGPUParticles
    poke32(0xDA7DF0, 0x52800020); poke32(0xDA7DF4, 0xD65F03C0); // CanDeviceRunDestruction
    poke32(0xDA7EE0, 0x52800020); poke32(0xDA7EE4, 0xD65F03C0); // CanDeviceRenderToMRT
    poke32(0xDA7FA8, 0x52800020); poke32(0xDA7FAC, 0xD65F03C0); // CanDeviceRenderToRT
    poke32(0xDA7FC0, 0x52800020); poke32(0xDA7FC4, 0xD65F03C0); // RemapCanRenderToRT
    poke32(0xDA7A08, 0x52800020); poke32(0xDA7A0C, 0xD65F03C0); // RemapDestruction
    poke32(0xDA7A14, 0x52800020); poke32(0xDA7A18, 0xD65F03C0); // RemapGPUParticles

    // Particle, Trail & Flare Quality (Force High = 2)
    poke32(0xDA7230, 0x52800040); poke32(0xDA7234, 0xD65F03C0); // RemapParticleQuality
    poke32(0xDA74F0, 0x52800040); poke32(0xDA74F4, 0xD65F03C0); // GetParticlePalQuality
    poke32(0xDA7240, 0x52800040); poke32(0xDA7244, 0xD65F03C0); // RemapTrailQuality
    poke32(0xDA7628, 0x52800040); poke32(0xDA762C, 0xD65F03C0); // GetTrailQuality
    poke32(0xDA7254, 0x52800040); poke32(0xDA7258, 0xD65F03C0); // RemapLensFlareQuality

    // Shadows (iOS High Quality)
    poke32(0xDA7264, 0x52800020); poke32(0xDA7268, 0xD65F03C0); // RemapContactShadowQuality
    poke32(0xDA79D0, 0x52800060); poke32(0xDA79D4, 0xD65F03C0); // RemapShadowQuality
    poke32(0xDA79DC, 0x52800040); poke32(0xDA79E0, 0xD65F03C0); // RemapShadowCount
    poke32(0xDA79F4, 0x52800020); poke32(0xDA79F8, 0xD65F03C0); // RemapShadowUpdate

    // PostFX, Bloom & Tone Mapping
    poke32(0xDA7840, 0x52800020); poke32(0xDA7844, 0xD65F03C0); // RemapPostFXQuality
    poke32(0xDA8154, 0x14000004); poke32(0xDA8170, 0x52800049); poke32(0xDA8174, 0x14000003); // PostFX = 2

    // Planar Reflections & MSAA
    poke32(0xDA74DC, 0x52800020); poke32(0xDA74E0, 0xD65F03C0); // RemapPlanarReflectionQuality
    poke32(0xDA83A8, 0x52800080); poke32(0xDA83AC, 0xD65F03C0); // GetMSAA (4x)
    poke32(0xDA8414, 0x52800040); poke32(0xDA8418, 0xD65F03C0); // GetPlanarReflectionMSAA (2x)

    // Anisotropic Texture Filtering
    poke32(0xDA7298, 0x52800020); poke32(0xDA729C, 0xD65F03C0);
    poke32(0xDA6BA0, 0x52800040);

    // Full 1500 LOD Shader
    poke32(0xDA6940, 0x14000003);

    // Disable Low-End Throttling
    poke32(0xDA7BC0, 0x2A1F03E0); poke32(0xDA7BC4, 0xD65F03C0); // IsLowMemoryDevice
    poke32(0xDA7CA4, 0x2A1F03E0); poke32(0xDA7CA8, 0xD65F03C0); // IsSlowDevice

    // Character Battle Damage System
    poke32(0xDA6640, 0xD503201F);
    poke32(0xD19E2C, 0xD503201F);

    // Runtime Graphics to High
    poke32(0xDA6978, 0x52800055);
    poke32(0xDA69F4, 0x52800055);

    // Global engine hooks
    inline_hook((void*)(g_base + 0x1B46108), (void*)hooked_set_targetFrameRate, &orig_set_targetFrameRate);
    inline_hook((void*)(g_base + 0x16A71C0), (void*)hooked_set_vSyncCount, &orig_set_vSyncCount);

    LOG("install done (%d hooks)", NH);
    return NULL;
}

static void inapk_log(const char* fmt, ...){
    char line[2048]; va_list ap;
    va_start(ap, fmt); vsnprintf(line, sizeof line, fmt, ap); va_end(ap);
    LOG("%s", line);
}

static void* launcher_thread(void* arg) {
    (void)arg;
    LOG("[Launcher] Launcher thread started, waiting for g_base...");
    for (int i = 0; i < 600; i++) {
        if (g_base) break;
        usleep(50000);
    }
    if (!g_base) {
        LOG("[Launcher] g_base not found");
        return NULL;
    }
    LOG("[Launcher] g_base found: %p, waiting for il2cpp JavaVM pointer...", (void*)g_base);

    JavaVM* vm = NULL;
    for (int i = 0; i < 200; i++) {
        vm = *(JavaVM**)(g_base + 0x2E4A1F8);
        if (vm) break;
        usleep(50000);
    }
    if (!vm) {
        LOG("[Launcher] JavaVM pointer at %p is null after timeout", (void*)(g_base + 0x2E4A1F8));
        return NULL;
    }
    LOG("[Launcher] JavaVM obtained: %p", vm);

    JNIEnv* env = NULL;
    jint res = (*vm)->AttachCurrentThread(vm, &env, NULL);
    if (res != JNI_OK || !env) {
        LOG("[Launcher] AttachCurrentThread failed: %d", res);
        return NULL;
    }

    // 1. Get Application ClassLoader via ActivityThread.currentApplication()
    jclass atClass = (*env)->FindClass(env, "android/app/ActivityThread");
    if (!atClass) {
        LOG("[Launcher] ActivityThread class not found");
        (*vm)->DetachCurrentThread(vm);
        return NULL;
    }
    jmethodID curAppMethod = (*env)->GetStaticMethodID(env, atClass, "currentApplication", "()Landroid/app/Application;");
    if (!curAppMethod) {
        LOG("[Launcher] ActivityThread.currentApplication method not found");
        (*vm)->DetachCurrentThread(vm);
        return NULL;
    }

    jobject app = NULL;
    for (int retry = 0; retry < 50; retry++) {
        app = (*env)->CallStaticObjectMethod(env, atClass, curAppMethod);
        if (app) break;
        usleep(100000);
    }
    if (!app) {
        LOG("[Launcher] currentApplication is null after timeout");
        (*vm)->DetachCurrentThread(vm);
        return NULL;
    }
    LOG("[Launcher] Found Application: %p", app);

    jclass appClass = (*env)->GetObjectClass(env, app);
    jmethodID getClMethod = (*env)->GetMethodID(env, appClass, "getClassLoader", "()Ljava/lang/ClassLoader;");
    jobject classLoader = (*env)->CallObjectMethod(env, app, getClMethod);
    LOG("[Launcher] Found ClassLoader: %p", classLoader);

    jclass clClass = (*env)->FindClass(env, "java/lang/ClassLoader");
    jmethodID loadClassMethod = (*env)->GetMethodID(env, clClass, "loadClass", "(Ljava/lang/String;)Ljava/lang/Class;");

    // 2. Load UnityPlayer and wait for currentActivity
    jstring upName = (*env)->NewStringUTF(env, "com.unity3d.player.UnityPlayer");
    jclass upClass = (jclass)(*env)->CallObjectMethod(env, classLoader, loadClassMethod, upName);
    (*env)->DeleteLocalRef(env, upName);

    if (!upClass || (*env)->ExceptionCheck(env)) {
        (*env)->ExceptionClear(env);
        LOG("[Launcher] Failed to load com.unity3d.player.UnityPlayer via ClassLoader");
        (*vm)->DetachCurrentThread(vm);
        return NULL;
    }

    jfieldID actField = (*env)->GetStaticFieldID(env, upClass, "currentActivity", "Landroid/app/Activity;");
    if (!actField) {
        LOG("[Launcher] currentActivity field not found");
        (*vm)->DetachCurrentThread(vm);
        return NULL;
    }

    jobject act = NULL;
    for (int retry = 0; retry < 100; retry++) {
        act = (*env)->GetStaticObjectField(env, upClass, actField);
        if (act) break;
        usleep(100000);
    }
    if (!act) {
        LOG("[Launcher] UnityPlayer.currentActivity is null after timeout");
        (*vm)->DetachCurrentThread(vm);
        return NULL;
    }
    LOG("[Launcher] Found UnityPlayer.currentActivity: %p", act);

    // 3. Load com.kabam.bigrobot.LauncherDialog
    jstring ldName = (*env)->NewStringUTF(env, "com.kabam.bigrobot.LauncherDialog");
    jclass launcherClass = (jclass)(*env)->CallObjectMethod(env, classLoader, loadClassMethod, ldName);
    (*env)->DeleteLocalRef(env, ldName);

    if (!launcherClass || (*env)->ExceptionCheck(env)) {
        (*env)->ExceptionDescribe(env);
        (*env)->ExceptionClear(env);
        LOG("[Launcher] Failed to load com.kabam.bigrobot.LauncherDialog");
        (*vm)->DetachCurrentThread(vm);
        return NULL;
    }
    LOG("[Launcher] Loaded LauncherDialog class: %p", launcherClass);

    jmethodID showMethod = (*env)->GetStaticMethodID(env, launcherClass, "show", "(Landroid/app/Activity;)V");
    if (showMethod) {
        (*env)->CallStaticVoidMethod(env, launcherClass, showMethod, act);
        LOG("[Launcher] Called LauncherDialog.show successfully!");
    } else {
        LOG("[Launcher] LauncherDialog.show method not found");
    }

    usleep(500000);
    (*vm)->DetachCurrentThread(vm);
    return NULL;
}

__attribute__((constructor))
static void init(void){
    struct sigaction sa; memset(&sa, 0, sizeof sa);
    sa.sa_sigaction = seg_handler; sa.sa_flags = SA_SIGINFO | SA_ONSTACK;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGSEGV, &sa, &g_oldsegv);
    sigaction(SIGBUS,  &sa, &g_oldbus);
    LOG("TFTFHOOK loaded (segv-guarded)");
    tftf_server_set_logger(inapk_log);
    int inapk_rc = tftf_server_start_from_apk();
    LOG("in-apk server start: %d", inapk_rc);
    pthread_t th; pthread_create(&th, NULL, installer, NULL);
    pthread_t lth; pthread_create(&lth, NULL, launcher_thread, NULL);
}
