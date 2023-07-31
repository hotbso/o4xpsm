
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
            out.write(f"EXPORT_EXCLUDE_SEASON win,spr,sum,fal {e[0]} {realpath}\n")

def parse_scenery_packs():
    with open("../scenery_packs.ini", "r") as sp:
        lines = sp.readlines()
        for l in lines:
            w = l.strip().split()
            if len(w) < 2:
                continue
            if w[0] == "SCENERY_PACK":
                path = ' '.join(w[1:])

                if path.find("simHeaven_X-World_Vegetation_Library") != -1:
                    logging.info("simHeaven_X-World_Vegetation_Library detected")
                    global simheaven_path
                    simheaven_path = path

                if path.find("Global_Forests_v2") != -1:
                    logging.info("Global_Forests_v2 detected")
                    global gfv2_path
                    gfv2_path = path

def check_and_link(name, path):
    logging.debug(f"{name} -> {path}")

    if os.path.isdir(name):
        logging.info(f"{name} is already linked")
        if os.path.isfile(os.path.join(name, "library.txt")):
            logging.info(f"link {name} is valid")
        else:
            logging.error(f"link {name} is invalid! Check!")
            exit(1)

    else:
        if not os.path.isabs(path):
            path = os.path.join("..", "..", path)
            logging.info(f"path: {path}")

        if sys.platform == "win32":
            # os.symlink needs Administrator rights so create a junction
            logging.info(f"creating junction {name} -> {path}")
            path = os.path.abspath(path)
            #logging.info(f"path: {path}")
            out = subprocess.run(shlex.split(f'mklink /j "{name}" "{path}"'), shell = True)
            if out.returncode != 0:
                logging.error(f"Can't create junction: {out}")
                exit(1)
        else:
            os.symlink(path, name)

###########
## main
###########
logging.basicConfig(level=logging.INFO,
                    handlers=[logging.FileHandler(filename = "o4xpsm_install.log", mode='w'),
                              logging.StreamHandler()])

logging.info(f"args: {sys.argv}")
debug = "-debug" in sys.argv
if debug:
    logging.info("Debug mode enabled")

install_dir = os.path.basename(os.path.normpath(os.path.join(os.getcwd(), '..')))
if install_dir != 'Custom Scenery':
    logging.error("Installation error, must be installed in 'Custom Scenery'")
    exit(1)

logging.info("Parsing scenery_packs.ini")
parse_scenery_packs()

logging.info("Checking links")
check_and_link("1200_forests", os.path.abspath("../../Resources/default scenery/1200 forests"))

if simheaven_path is not None:
    check_and_link("simHeaven_X-World_Vegetation_Library", simheaven_path)

if gfv2_path:
    check_and_link("Global_Forests_v2", gfv2_path)

logging.info("Creating library.txt")
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

logging.info("Processing XP12 native forests")
season = parse_lib("1200_forests/library.txt")
write_seasons(season, "o4xpsm_", "1200_forests")

if gfv2_path is not None:
    logging.info("Processing Global_Forests_v2")
    season = parse_lib("Global_Forests_v2/library.txt")
    write_seasons(season, "o4xpsm_", "Global_Forests_v2")

if simheaven_path is not None:
    logging.info("Processing simHeaven_X-World_Vegetation_Library")
    for z in sh_zones:
        season = parse_lib("simHeaven_X-World_Vegetation_Library/library.txt", "climate_zone_" + z)
        write_seasons(season, f"o4xpsm_sh_{z}_", "simHeaven_X-World_Vegetation_Library")

out.close()
logging.info("Success!")
