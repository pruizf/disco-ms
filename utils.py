#coding=utf8

"""
Utilities for the DISCO / Navarro corpus analyses for the CLEA talk
"""

__author__ = 'Pablo Ruiz'
__date__ = '27/12/17'
__email__ = 'pabloruizfabo@gmail.com'


import codecs
from lxml import etree
from math import floor
import os
import roman


nspaces = {'tei': 'http://www.tei-c.org/ns/1.0'}


# Getting input files ---------------------------------------------------------

def fix_filename(fn):
    """
    Rename files so that they can be found in DISCO's Golden Age part
    """
    return fn.replace("~~", "g~~").replace(".txt", ".xml")


def filter_input_file_list(target_dir, filelist):
    """
    Get only DISCO Golden Age files from a file list
    @param target_dir: directory containing DISCO Golden Age files
    @param filelist: list with files exclusively in DISCO (not in Navarro)
    """
    paths = []
    with codecs.open(filelist, "r", "utf8") as fh:
        line = fh.readline()
        while line:
            # example line
            # xv-xvii_cvc_sonnets/Polo_de_Medina,_Jacinto__288~~A_una_rosa_antes_de_abrir__0597.txt
            if line.startswith("xv-xvii_cvc_sonnets/"):
                fn = line.strip().replace("xv-xvii_cvc_sonnets/", "")
                fn = fix_filename(fn)
                full_path = os.path.join(target_dir, fn)
                assert os.path.exists(full_path)
                paths.append(full_path)
            elif line.startswith("#"):
                line = fh.readline()
                continue
            line = fh.readline()
    return paths


def get_19th_century_file_list(disco_19th):
    """
    Return DISCO filenames for 19th century sonnets
    @note: Can also be used to get the filenames for 18th century ones,
    as done in L{cross_metrics_and_enjambment}
    """
    return [os.path.join(disco_19th, x).replace(
            "~~", "~~").replace(".txt", ".xml")
            for x in os.listdir(disco_19th)]


def get_navarro_file_list(navarro_path):
    """
    Get sonnet filenames for Navarro corpus (iterating over directories)
    """
    filelist = []
    for root, dirs, files in os.walk(navarro_path):
        for dire in dirs:
            if dire[0].isupper():
                for fname in os.listdir(os.path.join(root, dire)):
                    # skip some bad filenames
                    if " " in fname:
                        continue
                    filelist.append(os.path.join(
                        root, os.path.join(dire, fname)))
    return filelist


# external metadata -----------------------------------------------------------

def infer_production_century(br, de):
    """
    Estimate the production century for an author.
    If born on or after the 80th year of a century,
    say it's the following century.
    If no dates (only centuries), and centuries differ,
    output a .5 date (e.g. birth XVI, death XVII => 16.5).
    Output False when birth or death date missing.
    """
    if str(br) == '0' or str(de) == '0':
        return False
    try:
        byear = int(br)
        dyear = int(de)
    except ValueError:
        try:
            byear = roman.fromRoman(br)
            dyear = roman.fromRoman(de)
            if byear == dyear:
                pcen = byear
            else:
                assert dyear == byear + 1
                pcen = byear + 0.5
            return pcen
        except roman.InvalidRomanNumeralError:
            return False
    if byear % 100 >= 80:
        pcen = floor(byear / 100) + 2
        assert floor(dyear / 100) + 1 == pcen
    else:
        pcen = floor(byear / 100) + 1
    return pcen


# metrical (and enjambment) info ----------------------------------------------

def get_met_from_poem(infn, remove_alexandrines=True):
    """
    Get the metrical pattern for each line for poem in infn
    """
    try:
        tree = etree.parse(infn)
    except etree.XMLSyntaxError:
        print(u"! empty [{}]".format(infn.decode("utf8")))
        return {}, {}
    try:
        n2mets = {int(ele.attrib["n"]): render_met_as_numbers(
                  fix_met(ele.attrib["met"]))
                  for ele in tree.xpath("//tei:l", namespaces=nspaces)}
    # ValueError in Navarro given keys like c1 for copla line 1
    except (KeyError, ValueError):
        n2mets = {}
    # remove alexandrines
    if remove_alexandrines:
        for lnbr, pat in n2mets.items():
            spat = [int(position) for position in pat.split("-")]
            if spat[-1] > 10:
                n2mets = {}
    return n2mets


def get_enjambment_tag_from_line_elements(tree):
    """
    Return a dict with enjambment tags hashed by line number.
    Stores type tagged with "B" (the enj that *starts* at the line)
    """
    n2enj = {}
    lines = tree.xpath("//tei:l", namespaces=nspaces)
    for line in lines:
        try:
           idx = int(line.attrib["n"])
        except ValueError:
            # ValueError in Navarro given keys like c1 for copla line 1
            continue
        n2enj[idx] = {"enjamb": None, "starts": 0, "ends": 0}
        if "enjamb" in line.attrib:
            try:
                #TODO is it not enough with the 'try' above?
                enj_types = line.attrib["enjamb"].split(" ")
                if len(enj_types) > 1:
                    enj_type = [ety for ety in enj_types
                                if ety.startswith("B")][0]
                    n2enj[idx]["starts"] = 1
                else:
                    enj_type = enj_types[0]
                    n2enj[idx]["ends"] = 1
                n2enj[idx]["enjamb"] = enj_type
            except ValueError:
                continue
        else:
            n2enj[idx]["enjamb"] = "O"
            n2enj[idx]["starts"] = -1
            n2enj[idx]["ends"] = -1
    return n2enj


def get_met_and_enj_from_poem(infn, remove_alexandrines=True):
    """
    Get the metrical pattern for each line for poem in infn
    """
    try:
        tree = etree.parse(infn)
    except etree.XMLSyntaxError:
        print(u"! empty [{}]".format(infn.decode("utf8")))
        return {}, {}
    try:
        n2mets = {int(ele.attrib["n"]): render_met_as_numbers(
                  fix_met(ele.attrib["met"]))
                  for ele in tree.xpath("//tei:l", namespaces=nspaces)}
    # ValueError in Navarro given keys like c1 for copla line 1
    except (KeyError, ValueError):
        n2mets = {}
    # remove alexandrines
    if remove_alexandrines:
        for lnbr, pat in n2mets.items():
            spat = [int(position) for position in pat.split("-")]
            if spat[-1] > 10:
                n2mets = {}
    # get enjambent
    n2enj = get_enjambment_tag_from_line_elements(tree)
    # merge metrics and enjambment
    n2mets_enj = {}
    for n, pat in n2mets.items():
        n2mets_enj[n] = {"met": pat}
        n2mets_enj[n].update(n2enj[n])
    return n2mets_enj


def render_met_as_numbers(ms):
    """
    Render the metrical annotation (ms) based on + and - as a
    string of numbers
    """
    nbrpat = "-".join([str(i+1) for i, ltr in enumerate(ms) if ltr == "+"])
    return nbrpat


def fix_met(st):
    """
    In some poems, ADSO tool outputs more than 11 syllables. Keep the 11 initial ones
    """
    if len(st.strip()) > 11 and len(st.strip()) != 14:
        return st[0:11].strip()
    else:
        return st.strip()


def classify_pattern_exact(pat):
    """
    Return a type for a pattern among heroico, melódico, sáfico
    """
    pats = {"4-8-10": "S", "3-6-10": "M", "2-6-10": "H"}
    try:
        classif = pats[pat]
    except KeyError:
        classif = "O"
    return classif


def classify_bigram_exact(big):
    """
    Return types for each pattern in a pattern-bigram
    """
    bigpats = big.split("__")
    assert len(bigpats) == 2
    classif = {"types": [], "parallel": False}
    if bigpats[0] == bigpats[1]:
        classif["parallel"] = True
    for pat in bigpats:
        classif["types"].append(classify_pattern_exact(pat))
    return classif


def classify_pattern_binary_ternary(pat, mode):
    """
    Return whether a pattern is to be considered binary or ternary
    (as defined in the function).
    """
    assert mode in ("original", "2018", "2019")
    spat = [int(p) for p in pat.split("-")]
    # Navarro 2016, p. 101
    if mode == "original":
        if ((2 in spat and 6 in spat) or (4 in spat and 8 in spat)):
            return "bin"
        elif 3 in spat and 6 in spat:
            return "ter"
        else:
            return "oth"
    # Option to exclude some possible ambiguities
    # My CLEA talk 2018, p. 88 https://zenodo.org/record/1217587
    elif mode == "2018":
        # 1-4 can be seen as ternary.
        # If accept 3 part of pattern overlaps with ternary definition
        if (((2 in spat and 6 in spat) or (4 in spat and 8 in spat and not 1 in spat))
                and not 3 in spat):
            return "bin"
        # If accept 2 can overlap with binary (2 6).
        # If accept 4, (4 6) can be seen as binary rhythm
        elif 3 in spat and 6 in spat and not (2 in spat or 4 in spat):
            return "ter"
        else:
            return "oth"
    # More strict way to control for possible pattern overlap
    elif mode == "2019":
        if ((2 in spat and 6 in spat) or (4 in spat and 8 in spat)):
            if not (3 in spat and 6 in spat):
                return "bin"
            else:
                return "oth"
        elif 3 in spat and 6 in spat:
            if not ((2 in spat and 6 in spat) or (4 in spat and 8 in spat)):
                return "ter"
        else:
            return "oth"


def classify_bigram_binary_ternary(big, mode):
    """
    Apply L{classify_pattern_binary_ternary}
    to a bigram pattern.
    """
    # bigpats = big.split("__")
    bigpats = big
    assert len(bigpats) == 2
    classif = {"types": [], "parallel": False}
    if bigpats[0] == bigpats[1]:
        classif["parallel"] = True
    for pat in bigpats:
        classif["types"].append(classify_pattern_binary_ternary(pat, mode))
    return classif


def find_stanza_for_position(posi):
    """
    Return the stanza for a line number
    """
    if posi > 14:
        return None
    if posi <= 4:
        stan = "Q1"
    elif posi > 4 and posi <= 8:
        stan = "Q2"
    elif posi > 8 and posi <= 11:
        stan = "T1"
    elif posi > 11 and posi <= 14:
        stan = "T2"
    return stan


def find_stanza_for_ternary_binary(ter_bi_stanza_counts, ter_bi_positions):
    """
    Find in which stanza a ternary, binary pattern occurs and increment
    a dictionary with stanza counts
    """
    ter_bi_as_indices = [(int(tb.split("_")[0]), int(tb.split("_")[1]))
                         for tb in ter_bi_positions]
    #import pdb;pdb.set_trace()
    for tbi in ter_bi_as_indices:
        if tbi[-1] > 14:
            continue
        if tbi[-1] <= 4:
            ter_bi_stanza_counts["Q1"] += 1
        # elif tbi[-1] > 4 and tbi[-1] <= 8:
        elif tbi[-1] > 5 and tbi[-1] <= 8:
            ter_bi_stanza_counts["Q2"] += 1
        # elif tbi[-1] > 8 and tbi[-1] <= 11:
        elif tbi[-1] > 9 and tbi[-1] <= 11:
            ter_bi_stanza_counts["T1"] += 1
        # elif tbi[-1] > 11 and tbi[-1] <= 14:
        elif tbi[-1] > 12 and tbi[-1] <= 14:
            ter_bi_stanza_counts["T2"] += 1


def postprocess_ternary_binary_per_stanza(di):
    """
    Add percentages to the dictionary of counts of ternary-binary
    patterns per stanza.
    """
    ndi = {}
    total = sum(di.values())
    for key in di:
        try:
            ndi[key] = {"count": di[key], "percent": 100 * float(di[key]) / total}
        except ZeroDivisionError:
            ndi[key] = {"count": di[key], "percent": 0}
    return ndi


# data mgmt -------------------------------------------------------------------

def update_dict(old, new, featkey):
    """
    Add the content of 'new' as value for key 'newkey' in 'old'
    @param old: Dict to which you want to add
    @param new: Dict whose values you want to add
    @param featkey: Key under which the values will be added
    """
    for fname in new.keys():
        assert fname in old
        old[fname][featkey] = new[fname]
    return new


# writeout --------------------------------------------------------------------

def write_pattern_counts(fl, cts):
    """
    Write out the feature table (metrical pattern counts)
    """
    # figure out features
    print("Write out features")
    # fkeys = ["monpct", "bigpct", "tripct"]
    fkeys = ["monpct", "bigpct", "tripct"]
    # fkeys = ["monpct"]
    ftrlist = []
    for idx, (fn, infos) in enumerate(cts.items()):
        # pattype is whether unigram, bigram etc
        for pattype, patcts in infos.items():
            # print("Ftrs for {}".format(pattype))
            if pattype not in fkeys:
                continue
            for pat in patcts:
                if pat not in ftrlist:
                    pat2append = pat if isinstance(pat, tuple) else (pat, )
                    ftrlist.append(pat2append)
            ftrlist = sorted(ftrlist)
            # ftrlist.extend(sorted(set(list([(x, ) if not isinstance(x, tuple)
            #                       else x for x in patcts.keys()]))))
            if idx and not idx % 1000:
                print("Done {} files".format(idx))

    # get counts for each feature per file
    for fn, infos in cts.items():
        # output line
        ol = []
        # pattype is whether unigram, bigram etc
        for pattype, patcts in infos.items():
            # import pdb;pdb.set_trace()
            for ftr in ftrlist:
                if ftr in patcts:
                    ol.append(patcts[ftr])
                else:
                    ol.append(0)
        print(ol)
