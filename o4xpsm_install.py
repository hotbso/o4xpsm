
# MIT License

# Copyright (c) 2023 Holger Teutsch

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys, os, shlex, subprocess
import logging

log = logging.getLogger("o4xpsm_install")

version = "=VERSION="

seasons = ["win", "spr", "sum", "fal"]
sh_zones = ["vcld", "cld", "tmp", "wrm", "vhot"]

debug_for = {"win": "1200_forests/sum/tree_coconut_palm_1.for",
             "spr": "1200_forests/spr/tree_aspen_1.for",
             "sum": "1200_forests/sum/tree_maple_2.for",
             "fal": "1200_forests/fal/tree_maple_2.for"}

simheaven_path = None
gfv2_path = None

def parse_lib(name, region_only = None):
    season = {"win": [], "spr": [], "sum": [], "fal": []}

    with open(name, "r") as f:
        # position to desired region
        if region_only:
            while True:
                l = f.readline()
                if not l:
                    break

                l = l.strip()
                w = l.split()
                if len(w) == 2 and w[0] == "REGION" and w[1] == region_only:
                    break

        while True:
            l = f.readline()
            if not l:
                break

            l = l.strip()
            w = l.split()

            if region_only and len(w) > 0 and w[0] == "REGION":
                break

            if len(w) > 0 and w[0] == "EXPORT_SEASON":
                #print(l)
                #print(w[0])
                season[w[1]].append([w[2], ' '.join(w[3:])])

    return season

def write_seasons(season, region_prefix, link):
    for s in season.keys():
        out.write(f"\n\nREGION {region_prefix}{s}\n")

        for e in season[s]:
            if debug:
                realpath = "1200_forests/sum/tree_maple_2.for" #debug_for[s]
            else:
                realpath = f"{link}/{e[1]}"

            #out.write(f"EXPORT_EXCLUDE {e[0]} {realpath}\n")
            out.write(f"EXPORT_SEASON win,spr,sum,fal {e[0]} {realpath}\n")
            #out.write(f"EXPORT_SEASON_RATIO win,spr,sum,fal 0.5 {e[0]} {realpath}\n")

def parse_scenery_packs():
    with open("../scenery_packs.ini", "r") as sp:
        lines = sp.readlines()
        for l in lines:
            w = l.strip().split()
            if len(w) < 2:
                continue
            if w[0] == "SCENERY_PACK" or w[0] == "SCENERY_PACK_DISABLED":
                path = ' '.join(w[1:])

                if path.find("simHeaven_X-World_Vegetation_Library") != -1:
                    log.info("simHeaven_X-World_Vegetation_Library detected")
                    global simheaven_path
                    simheaven_path = path

                if path.find("Global_Forests_v2") != -1:
                    log.info("Global_Forests_v2 detected")
                    global gfv2_path
                    gfv2_path = path

def check_and_link(name, path):
    log.debug(f"{name} -> {path}")

    if os.path.isdir(name):
        log.info(f"{name} is already linked")
        if name == "Earth nav data":
            probe = os.path.join("+00+000", "+00+000.dsf")
        else:
            probe = "library.txt"

        if os.path.isfile(os.path.join(name, probe)):
            log.info(f"link {name} looks valid")
        else:
            log.error(f"link {name} is invalid! Check!")
            exit(1)

    else:
        if not os.path.isabs(path):
            path = os.path.join("..", "..", path)
            log.info(f"path: {path}")

        if sys.platform == "win32":
            # os.symlink needs Administrator rights so create a junction
            log.info(f"creating junction {name} -> {path}")
            path = os.path.abspath(path)
            #log.info(f"path: {path}")
            out = subprocess.run(shlex.split(f'mklink /j "{name}" "{path}"'), shell = True)
            if out.returncode != 0:
                log.error(f"Can't create junction: {out}")
                exit(1)
        else:
            os.symlink(path, name)

###########
## main
###########
logging.basicConfig(level=logging.INFO,
                    handlers=[logging.FileHandler(filename = "o4xpsm_install.log", mode='w'),
                              logging.StreamHandler()])

log.info(f"Version: {version}")

log.info(f"args: {sys.argv}")

debug = False
xpl_root = None

i = 1
while i < len(sys.argv):
    if sys.argv[i] == "-debug":
        debug = True
    elif sys.argv[i] == "-root":
        i = i + 1
        if i >= len(sys.argv):
            log.error('No argument after "-root"')
            exit(1)
        xpl_root = sys.argv[i]

    i = i + 1

if debug:
    log.info("Debug mode enabled")

if xpl_root is not None:
    log.info(f'root specified as "{xpl_root}"')


install_dir = os.path.basename(os.path.normpath(os.path.join(os.getcwd(), '..')))
if install_dir != 'Custom Scenery':
    log.error("Installation error, must be installed in 'Custom Scenery'")
    exit(1)

log.info("")
log.info("Parsing scenery_packs.ini")
parse_scenery_packs()

log.info("")
log.info("Checking links")

f1200 = "Resources/default scenery/1200 forests"
if xpl_root is None:
    if not os.path.isdir(os.path.normpath(os.path.join("../..", f1200))):
        log.error('Non standard installation of X Plane detected, use: -root "path to XP12"')
        exit(1)
else:
    f1200 = os.path.normpath(os.path.join(xpl_root, f1200))
    if not os.path.isdir(f1200):
        log.error(f'directory does not exist: {f1200}')
        exit(1)

check_and_link("1200_forests", f1200)

if simheaven_path is not None:
    check_and_link("simHeaven_X-World_Vegetation_Library", simheaven_path)

if gfv2_path:
    check_and_link("Global_Forests_v2", gfv2_path)
    check_and_link("Earth nav data", os.path.join(gfv2_path, "Earth nav data"))

log.info("")
log.info("Creating library.txt")
out = open("library.txt", "w")


out.write("""A
1200
LIBRARY

# seasons ###################################

REGION_DEFINE o4xpsm_win
REGION_ALL
REGION_DREF o4xpsm/win == 1

REGION_DEFINE o4xpsm_spr
REGION_ALL
REGION_DREF o4xpsm/spr == 1

REGION_DEFINE o4xpsm_sum
REGION_ALL
REGION_DREF o4xpsm/sum == 1

REGION_DEFINE o4xpsm_fal
REGION_ALL
REGION_DREF o4xpsm/fal == 1
""")


for z in sh_zones:
    for s in seasons:
        out.write(f"\nREGION_DEFINE o4xpsm_sh_{z}_{s}\n")
        out.write(f"REGION_BITMAP simHeaven_X-World_Vegetation_Library/Maps/climate_zone_{z}.png\n")
        out.write(f"REGION_DREF o4xpsm/{s} == 1\n")

log.info("Processing XP12 native forests")
season = parse_lib("1200_forests/library.txt")
write_seasons(season, "o4xpsm_", "1200_forests")

if gfv2_path is not None:
    log.info("Processing Global_Forests_v2")
    season = parse_lib("Global_Forests_v2/library.txt")
    write_seasons(season, "o4xpsm_", "Global_Forests_v2")

if simheaven_path is not None:
    log.info("Processing simHeaven_X-World_Vegetation_Library")
    for z in sh_zones:
        season = parse_lib("simHeaven_X-World_Vegetation_Library/library.txt", "climate_zone_" + z)
        write_seasons(season, f"o4xpsm_sh_{z}_", "simHeaven_X-World_Vegetation_Library")

out.close()
log.info("Success!")
