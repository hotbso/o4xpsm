/*

MIT License

Copyright (c) 2023 Holger Teutsch

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>

#define XPLM200
#include "XPLMPlugin.h"
#include "XPLMDataAccess.h"
#include "XPLMUtilities.h"
#include "XPLMProcessing.h"
#include "XPLMMenus.h"

static char pref_path[512];
static const char *psep;
static XPLMMenuID menu_id;
static int enable_item;
static int o4xpsm_enabled;
static int airport_loaded;

static XPLMDataRef date_day_dr, latitude_dr;
static int cur_day = 999;
int nh;     // on northern hemisphere
static int season_win, season_spr, season_sum, season_fal;
static int cached_day = 999;
static const char *season_str[] = {"win", "spr", "sum", "fal"};

static void
log_msg(const char *fmt, ...)
{
    char line[1024];

    va_list ap;
    va_start(ap, fmt);
    vsnprintf(line, sizeof(line) - 3, fmt, ap);
    strcat(line, "\n");
    XPLMDebugString("o4xpsm: ");
    XPLMDebugString(line);
    va_end(ap);
}

static void
save_pref()
{
    FILE *f = fopen(pref_path, "w");
    if (NULL == f)
        return;

    /* encode southern hemisphere with negative days */
    int d = nh ? cur_day : -cur_day;
    fprintf(f, "%d,%d,%d,%d,%d,%d", o4xpsm_enabled, d,
                season_win, season_spr, season_sum, season_fal);
    fclose(f);
}

static void
load_pref()
{
    FILE *f  = fopen(pref_path, "r");
    if (NULL == f)
        return;

    nh = 1;
    if (6 == fscanf(f, "%i,%i,%i,%i,%i,%i", &o4xpsm_enabled, &cached_day,
                    &season_win, &season_spr, &season_sum, &season_fal))
        log_msg("From pref: o4xpsm_enabled: %d, cached_day: %d, seasons: %d,%d,%d,%d",
                o4xpsm_enabled, cached_day, season_win, season_spr, season_sum, season_fal);
    else {
        o4xpsm_enabled = 0;
        log_msg("Error readinf pref");
    }

    fclose(f);

    if (cached_day < 0) {
        nh = 0;
        cached_day = -cached_day;
    }
}

// Accessor for the "o4xpsm/*" dataref
static int
read_season_acc(void *ref)
{
    if (! o4xpsm_enabled)
        return 0;

    int s = (long long)ref;
    int val = 0;

    switch (s) {
        case 0:
            val = season_win;
            break;
        case 1:
            val = season_spr;
            break;
        case 2:
            val = season_sum;
            break;
        case 3:
            val = season_fal;
            break;
        default:
            log_msg("invalid season code %d", s);
            s = 0;
            val = 0;
    }

    log_msg("accessor %s called, returns %d", season_str[s], val);
    return val;
}

// set season according to standard values
static void
set_season(int day)
{
    if (! o4xpsm_enabled)
        return;

    if (day == cur_day)
        return;

    season_win = season_spr = season_sum = season_fal = 0;

    // 1. Jan = 0
    // 1. Jul = 181
    // 31. Dec = 364

    // the difference between sh and nh seems to be 151 days = (1.Jun - 1.Jan)

    if (nh) {
        if (0 <= day && day <= 60)      // Jan + Feb look like spring or summer
            season_win = 1;

        if (212 <= day && day < 262)   // August is already pretty much fall
            season_spr = 1;            // late spring looks more like summer up to 20. Sep
    } else {
        if (151 <= day && day <= 211)  // Jun + Jul look like spring or summer
            season_win = 1;

        if (61 <= day && day < 111)   // March is already pretty much fall
            season_spr = 1;           // late spring looks more like summer
    }

    log_msg("nh: %d, day: %d->%d, season: %d, %d, %d, %d", nh, cur_day, day,
            season_win, season_spr, season_sum, season_fal);
    cur_day = day;
}

static void
menu_cb(void *menu_ref, void *item_ref)
{
    if ((int *)item_ref == &o4xpsm_enabled) {
        o4xpsm_enabled = !o4xpsm_enabled;
        XPLMCheckMenuItem(menu_id, enable_item,
                          o4xpsm_enabled ? xplm_Menu_Checked : xplm_Menu_Unchecked);
        set_season(XPLMGetDatai(date_day_dr));
        save_pref();
    }
}

PLUGIN_API int
XPluginStart(char *out_name, char *out_sig, char *out_desc)
{
    XPLMMenuID menu;
    int sub_menu;

    strcpy(out_name, "o4xpsm " VERSION);
    strcpy(out_sig, "o4xpsm.hotbso");
    strcpy(out_desc, "A plugin that manages Seasons");

    /* Always use Unix-native paths on the Mac! */
    XPLMEnableFeature("XPLM_USE_NATIVE_PATHS", 1);

    psep = XPLMGetDirectorySeparator();

    /* set pref path */
    XPLMGetPrefsPath(pref_path);
    XPLMExtractFileAndPath(pref_path);
    strcat(pref_path, psep);
    strcat(pref_path, "o4xpsm.prf");

    menu = XPLMFindPluginsMenu();
    sub_menu = XPLMAppendMenuItem(menu, "o4xp Seasons Manager", NULL, 1);
    menu_id = XPLMCreateMenu("o4xp Seasons Manager", menu, sub_menu, menu_cb, NULL);
    enable_item = XPLMAppendMenuItem(menu_id, "Orthophoto mode", &o4xpsm_enabled, 0);

    load_pref();
    XPLMCheckMenuItem(menu_id, enable_item,
                      o4xpsm_enabled ? xplm_Menu_Checked : xplm_Menu_Unchecked);

    date_day_dr = XPLMFindDataRef("sim/time/local_date_days");
    latitude_dr = XPLMFindDataRef("sim/flightmodel/position/latitude");

#if 0
    if (o4xpsm_enabled) {
        if (cached_day != 999)
            set_season(cached_day);
        else
            set_season(XPLMGetDatai(date_day_dr));
    }
#endif

    XPLMRegisterDataAccessor("o4xpsm/win", xplmType_Int, 0, read_season_acc,
                             NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
                             NULL, NULL, NULL, (void *)0, NULL);

    XPLMRegisterDataAccessor("o4xpsm/spr", xplmType_Int, 0, read_season_acc,
                             NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
                             NULL, NULL, NULL, (void *)1, NULL);

    XPLMRegisterDataAccessor("o4xpsm/sum", xplmType_Int, 0, read_season_acc,
                             NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
                             NULL, NULL, NULL, (void *)2, NULL);

    XPLMRegisterDataAccessor("o4xpsm/fal", xplmType_Int, 0, read_season_acc,
                             NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
                             NULL, NULL, NULL, (void *)3, NULL);

    return 1;
}


PLUGIN_API void
XPluginStop(void)
{
}


PLUGIN_API void
XPluginDisable(void)
{
    save_pref();
}


PLUGIN_API int
XPluginEnable(void)
{
    return 1;
}

PLUGIN_API void
XPluginReceiveMessage(XPLMPluginID in_from, long in_msg, void *in_param)
{
    /* Everything before XPLM_MSG_AIRPORT_LOADED has bogus datarefs.
       Anyway it's too late for the current scenery. */
    if ((in_msg == XPLM_MSG_AIRPORT_LOADED) ||
        (airport_loaded && (in_msg == XPLM_MSG_SCENERY_LOADED))) {
        airport_loaded = 1;
        int day = XPLMGetDatai(date_day_dr);
        nh = (XPLMGetDatad(latitude_dr) >= 0.0);
        set_season(day);
    }
}
