import sys

def parse_lib(name):
    lines = open(name, "r").readlines()

    season = {"win": [], "spr": [], "sum": [], "fal": []}

    for l in lines:
        l = l.strip()
        
        w = l.split()
        if len(w) > 0 and w[0] == "EXPORT_SEASON":
            #print(l)
            #print(w[0])
            season[w[1]].append([w[2],w[3]])
    return season

out = sys.stdout


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

def write_seasons(season, region_prefix, link):
    for s in season.keys():
        out.write(f"REGION {region_prefix}{s}\n")

        for e in season[s]:
            if debug:
                out.write(f"EXPORT_EXCLUDE {e[0]} {debug_for[s]}\n")
                out.write(f"EXPORT_EXCLUDE_SEASON {s} {e[0]} {debug_for[s]}\n")
            else:
                out.write(f"EXPORT_EXCLUDE {e[0]} {link}/{e[1]}\n")
                out.write(f"EXPORT_EXCLUDE_SEASON {s} {e[0]} {link}/{e[1]}\n")

season = parse_lib("1200_forests/library.txt") 
write_seasons(season, "o4xpsm_", "1200_forests")

season = parse_lib("Global_Forests_v2/library.txt") 
write_seasons(season, "o4xpsm_", "Global_Forests_v2")


