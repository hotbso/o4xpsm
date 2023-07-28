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

#include "XPLMPlugin.h"
#include "XPLMDataAccess.h"
#include "XPLMUtilities.h"
#include "XPLMProcessing.h"
#include "XPLMMenus.h"

#define VERSION "1.0b1"

static char pref_path[512];
static const char *psep;
static XPLMMenuID menu_id;
static int enable_item;
static int o4xpsm_enabled;

static XPLMDataRef date_day_dr, latitude_dr;
static int cur_day = -1;
static int season_win, season_spr, season_sum, season_fal;
static int cached_day = -10;

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

    fprintf(f, "%d,%d", o4xpsm_enabled, cur_day);  // cache current season
    fclose(f);
}


static void
load_pref()
{
    FILE *f  = fopen(pref_path, "r");
    if (NULL == f)
        return;

    if (1 <= fscanf(f, "%i,%i", &o4xpsm_enabled, &cached_day))
        log_msg("From pref: o4xpsm_enabled: %d, cached_day: %d", o4xpsm_enabled, cached_day);
    else {
        o4xpsm_enabled = 0;
        log_msg("Error readinf pref");
    }
    fclose(f);
}

// Accessor for the "o4xpsm/*" dataref
static int
read_season_acc(void *ref)
{
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
    }

    log_msg("accessor %d called, returns %d", s, val);
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

    if (day < 80)
        season_win = 1;
    else if (day < 170)
        season_spr = 1;
    else if (day < 260)
        season_sum = 1;
    else if (day < 350)
        season_fal = 1;
    else
        season_win = 1;

#if 0
    double lat = XPLMGetDatad(latitude_dr);
    if (lat < 0)
        o4xpsm_season = -o4xpsm_season;
#endif

    log_msg("day: %d->%d, season: %d, %d, %d, %d", cur_day, day,
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

    if (o4xpsm_enabled) {
        if (cached_day >= 0)
            set_season(cached_day);
        else
            set_season(XPLMGetDatai(date_day_dr));
    }

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
    /* try to catch any event that may come prior to a scenery reload */
    set_season(XPLMGetDatai(date_day_dr));
}
