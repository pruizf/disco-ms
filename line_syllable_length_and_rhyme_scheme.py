#coding=utf8

"""
To see which sonnets are alexandrine vs hendecasyllable and which have enclosed or alternate rhyme
"""

__author__ = 'Pablo Ruiz'
__date__ = '18/11/17'
__email__ = 'pabloruizfabo@gmail.com'


from collections import OrderedDict
import os
from pprint import pprint
from lxml import etree
import sys
import utils

# cfg
DBG = False
DISCO_ONLY = False
todo_list = "data/filenames_disco_only.txt"

nspaces = {'tei': 'http://www.tei-c.org/ns/1.0'}


# io
try:
    indir = sys.argv[2]
except IndexError:
    indir = "corpora/disco/tei/{}/per-sonnet"

outfn = "analyses/syll_and_stanza.txt"


def get_md_from_filename(fn):
    return fn.split("~~")[0], fn.split("~~")[1]


def render_met_as_numbers(ms):
    """
    Render the metrical annotation (ms) based on + and - as a
    string of numbers
    """
    nbrpat = " ".join([str(i+1) for i, ltr in enumerate(ms) if ltr == "+"])
    return nbrpat


def fix_met(st):
    """
    In some poems, ADSO scansion tool outputs more than 11 syllables.
    Keep the 11 initial ones
    """
    if len(st.strip()) > 11 and len(st.strip()) != 14:
        return st[0:11].strip()
    else:
        return st.strip()


def analyze_poem(dfn):
    """
    Extract metrical patterns and stanza types from DISCO file (dfn)
    """
    is_alex = False
    has_alternate = False
    is_latam = False
    try:
        tree = etree.parse(os.path.join(dfn))
    except IOError:
        return None, None, None
    try:
        mets = [render_met_as_numbers(fix_met(ele.attrib["met"]))
                for ele in tree.xpath("//tei:l", namespaces=nspaces)]
        for pat in mets:
            spat = [int(position) for position in pat.strip().split(" ")]
            if spat[-1] > 11:
                is_alex = True
    except KeyError:
        if DBG:
            print("    - No metrics: [{}]".format(dfn))

    stanza_types = [lg.attrib["type"] for lg in tree.xpath("//tei:lg",
                                                           namespaces=nspaces)]

    try:
        continent = tree.xpath("//tei:floruit/tei:placeName/tei:bloc/text()", namespaces=nspaces)[0]
    except IndexError:
        # look for birth if no floruit (general case)
        try:
            continent = tree.xpath("//tei:birth/tei:location/tei:placeName/tei:bloc/text()",
                              namespaces=nspaces)[0]
        except IndexError:
            #print(u"    {}".format(fpath.decode(encoding="utf-8")))
            # this was checked manually, authors 300g and 485n are Latin American
            continent = u"América" if "disco300g" in dfn or "disco485n" in dfn else u"Europa"

    if continent == u"América":
        is_latam = True
    if "serventesio" in stanza_types:
        has_alternate = True
    return is_alex, has_alternate, is_latam


def analyze_poem_dir(discodir, mode, file_list):
    """
    Apply L{analyze_poem} to a complete directory
    @param discodir: directory to apply function to
    @param mode: period (to know when remove ADSO from DISCO)
    @param file_list:
    """
    if DBG:
        print("### Extracting metadata")
    di = {}

    if DISCO_ONLY and mode == "15th-17th":
        filtered_dir = utils.filter_input_file_list(discodir, file_list)
    else:
        filtered_dir = os.listdir(discodir)

    # for fn in os.listdir(discodir):
    for fn in filtered_dir:
        # if DBG:
        #     print(u"- {}".format(fn.decode("utf8")))
        if DISCO_ONLY and mode == "15th-17th":
            dfn = fn
        else:
            dfn = os.path.join(discodir, fn)
        is_alex, has_alternate, is_latam = analyze_poem(dfn)
        if is_alex is None or has_alternate is None:
            continue
        au, ti = get_md_from_filename(fn)
        di.setdefault(au, {})
        di[au][ti] = {"is_alex": is_alex, "has_alternate": has_alternate,
                      "is_latam": is_latam}
    return di


def count_metadata(di):
    """
    Count alexandrine / hendecasyllable sonnets and enclosed / alternate rhyme
    """
    hend = {"alternate": {"latam": 0, "eu": 0, "total": 0},
            "enclosed": {"latam":0, "eu": 0, "total": 0}}
    alex = {"alternate": {"latam": 0, "eu": 0, "total": 0},
            "enclosed": {"latam":0, "eu": 0, "total": 0}}
    for au, ti2infos in sorted(di.items()):
        for ti, infos in ti2infos.items():
            if infos["is_alex"]:
                if infos["has_alternate"]:
                    if infos["is_latam"]:
                        alex["alternate"]["latam"] += 1
                    else:
                        alex["alternate"]["eu"] += 1
                    alex["alternate"]["total"] += 1
                else:
                    if infos["is_latam"]:
                        alex["enclosed"]["latam"] += 1
                    else:
                        alex["enclosed"]["eu"] += 1
                    alex["enclosed"]["total"] += 1
            else:
                if infos["has_alternate"]:
                    if infos["is_latam"]:
                        hend["alternate"]["latam"] += 1
                    else:
                        hend["alternate"]["eu"] += 1
                    hend["alternate"]["total"] += 1
                else:
                    if infos["is_latam"]:
                        hend["enclosed"]["latam"] += 1
                    else:
                        hend["enclosed"]["eu"] += 1
                    hend["enclosed"]["total"] += 1
    return hend, alex


def write_table(hed, ald, ofn, mode):
    """
    Write table similar to paper format
    @param hed: dict with hendecasyllable info
    @param ald: dict with alexandrine info
    @param ofn: path to output file
    @param mode: str with the corpus period
    """
    infos = OrderedDict([("Hendecasyllable", hed), ("Alexandrine", ald)])
    with open(ofn, "a") as ofd:
        ofd.write("# {}\n".format(mode))
        for ke, vals in infos.items():
            ofd.write("## {}\n".format(ke))
            ofd.write("- Enclosed : Total [{}] American [{}] European [{}]\n".format(
                vals["enclosed"]["latam"] + vals["enclosed"]["eu"],
                vals["enclosed"]["latam"],
                vals["enclosed"]["eu"]))
            ofd.write("- Alternate: Total [{}] American [{}] European [{}]\n".format(
                vals["alternate"]["latam"] + vals["alternate"]["eu"],
                vals["alternate"]["latam"],
                vals["alternate"]["eu"]))
            ofd.write("- Total    : Total [{}] American [{}] European [{}]\n\n".format(
                (vals["enclosed"]["latam"] + vals["enclosed"]["eu"] +
                 vals["alternate"]["latam"] + vals["alternate"]["eu"]),
                vals["enclosed"]["latam"] + vals["alternate"]["latam"],
                vals["enclosed"]["eu"] + vals["alternate"]["eu"]))
        ofd.write("\n\n")


def main(ddir, mode, ga_list):
    """
    Run analyses
    @param ddir: directory for one period of DISCO
    @param mode: period name (for output tables, and to remove ADSO from DISCO)
    @param ga_list: list with files only in DISCO and not in ADSO
    """
    if DBG:
        global a2infos
        global acts, hcts
    a2infos = analyze_poem_dir(ddir, mode, ga_list)
    # hendecasyllable, alexandrine
    hcts, acts = count_metadata(a2infos)
    if DBG:
        print("## {}\n".format(mode))
        print("* Alex:")
        pprint(acts)
        print("\n* Hend:")
        pprint(hcts)
        print("\n")
    write_table(hcts, acts, outfn, mode)


if __name__ == "__main__":
    print("\n\n# Table 3 - Meter and Rhyme scheme in 19th century - Running [{}]".format(sys.argv[0]))
    print("- Writing results to [{}]".format(outfn))
    # remove old versions of table as write in append
    if os.path.exists(outfn):
        os.remove(outfn)
    for mode in sorted(("15th-17th", "18th", "19th"), reverse=True):
        main(indir.format(mode), mode, todo_list)
