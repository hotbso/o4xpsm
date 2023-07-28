import sys

seasons = ["win", "spr", "sum", "fal"]
sh_zones = ["vcld", "cld", "tmp", "wrm", "vhot"]

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

out = sys.stdout

def write_seasons(season, region_prefix, link):
    for s in season.keys():
        out.write(f"\n\nREGION {region_prefix}{s}\n")

        for e in season[s]:
            if debug:
                out.write(f"EXPORT_EXCLUDE {e[0]} {debug_for[s]}\n")
                out.write(f"EXPORT_EXCLUDE_SEASON {s} {e[0]} {debug_for[s]}\n")
            else:
                out.write(f"EXPORT_EXCLUDE {e[0]} {link}/{e[1]}\n")
                out.write(f"EXPORT_EXCLUDE_SEASON {s} {e[0]} {link}/{e[1]}\n")


########### main
debug = True

debug_for = {"win": "1200_forests/win/tree_oak_1.for",
             "spr": "1200_forests/spr/tree_aspen_1.for",
             "sum": "1200_forests/sum/tree_coconut_palm_1.for",
             "fal": "1200_forests/fal/tree_maple_2.for"}


out.write("""A
800
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

debug = True
season = parse_lib("1200_forests/library.txt")
write_seasons(season, "o4xpsm_", "1200_forests")

season = parse_lib("Global_Forests_v2/library.txt")
write_seasons(season, "o4xpsm_", "Global_Forests_v2")

debug = True
for z in sh_zones:
    season = parse_lib("simHeaven_X-World_Vegetation_Library/library.txt", "climate_zone_" + z)
    write_seasons(season, f"o4xpsm_sh_{z}_", "simHeaven_X-World_Vegetation_Library")

