#coding=utf8

"""
Extract metrical patterns from DISCO TEI
"""

__author__ = 'ruizfabo Ruiz'
__date__ = '26/11/17'
__email__ = 'ruizfaboruizfabo@gmail.com'


import codecs
from collections import OrderedDict
from lxml import etree
from lxml.etree import XMLSyntaxError
import os
import sys

import utils

# script path
import inspect
here = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
sys.path.append(here)


# cfg
DBG = False
split_by_origin = False
allowed_modes = ("xv-xvii", "xviii", "xix")
todo_list = "data/filenames_disco_only.txt"

nspaces = {'tei': 'http://www.tei-c.org/ns/1.0'}


def get_md_from_filename(fn):
    """
    Get author and title from filename
    """
    return fn.split("~~")[0], fn.split("~~")[1]


def fix_met(st):
    """
    In some poems, ADSO outputs more than 11 syllables. Keep the 11 initial ones
    """
    if len(st.strip()) > 11 and len(st.strip()) != 14:
        return st[0:11].strip()
    else:
        return st.strip()


def get_met_from_poem(infn):
    """
    Get the metrical pattern for each line for poem in infn
    """
    try:
        tree = etree.parse(infn)
    except XMLSyntaxError:
        print u"! empty [{}]".format(infn.decode("utf8"))
        return {}, {}
    try:
        n2mets = {int(ele.attrib["n"]): render_met_as_numbers(
                  fix_met(ele.attrib["met"]))
                  for ele in tree.xpath("//tei:l", namespaces=nspaces)}
    except KeyError:
        n2mets = {}
    #TODO: no pb cos unused, but to be complete should check floruit before birth
    try:
        origin = tree.xpath("//tei:birth/tei:location/tei:placeName/tei:bloc/text()",
                            namespaces=nspaces)
    except IndexError:
        origin = 'unk'
    return n2mets, origin


def get_mets(idir, mode, file_list):
    """
    Apply L{get_met_from_poem} on a dir to get metrical patterns for its files
    """
    if DBG:
        print "= Getting metrical patterns from DISCO output"
    a2mets = {}
    if mode == "xv-xvii":
        filtered_dir = utils.filter_input_file_list(idir, file_list)
    else:
        filtered_dir = os.listdir(idir)
    #for fn in sorted(os.listdir(idir)):
    for fn in sorted(filtered_dir):
        if DBG:
            print u"- {}".format(fn.decode("utf8"))
        fn = fn.decode("utf8") if isinstance(fn, str) else fn
        # filtered paths already contain directory name
        if mode == "xv-xvii":
            ffn = fn
        # add directory name
        else:
            ffn = os.path.join(idir, fn)
        au, ti = get_md_from_filename(fn)
        a2mets.setdefault(au, {})
        metrics, origin = get_met_from_poem(ffn)
        a2mets[au][ti] = {"metrics": metrics,
                          "origin": origin}
    return a2mets


def render_met_as_numbers(ms):
    """
    Render the metrical annotation (ms) based on + and - as a
    string of numbers
    """
    nbrpat = " ".join([str(i+1) for i, ltr in enumerate(ms) if ltr == "+"])
    return nbrpat


def pattern2counts(di):
    """
    Count metrical patterns, splitting the counts by meter length:
    alexandrine or hendecasyllable
    """
    if DBG:
        print "= Start pattern counts"
    hendct = {}
    alexct = {}
    for au, infos in sorted(di.items()):
        for ti, patinfo in infos.items():
            for pat in patinfo["metrics"].values():
                # alex
                # last stressed syllable on hendecasyllable is 10 at most
                if int(pat.strip().split(" ")[-1]) >= 11:
                    alexct.setdefault(pat, {"all": 0, "eu": 0, "am": 0})
                    alexct[pat]["all"] += 1
                    if patinfo["origin"] == "Europa":
                        alexct[pat]["eu"] += 1
                    else:
                        alexct[pat]["am"] += 1
                # hend
                else:
                    hendct.setdefault(pat, {"all": 0, "eu": 0, "am": 0})
                    hendct[pat]["all"] += 1
                    if patinfo["origin"] == "Europa":
                        hendct[pat]["eu"] += 1
                    else:
                        hendct[pat]["am"] += 1
    return hendct, alexct


def filter_for_printout(di):
    """
    Filter out likely errors in hendecasyllable scansion.
    Assumes patterns where last stress is not on 10 are wrong.
    """
    keepkeys = [ke for ke in di if ke.endswith("10")]
    keepitems = {ke: di[ke] for ke in keepkeys}
    return keepitems


def write_out_with_origin(di, ofnm):
    if DBG:
        print "\n=Writing out to [{}]".format(ofnm)
    ols = []
    with codecs.open(ofnm, "w", "utf8") as ofd:
        for ke, va in sorted(di.items(), key=lambda it: -it[-1]["all"]):
            # all eu am
            ols.append("{}\t{al}\t{eu}\t{am}".format(
                ke, al=va["all"], eu=va["eu"], am=va["am"]))
        ofd.write("\n".join(ols))


def write_out(di, ofnm):
    if DBG:
        print "\n=Writing out to [{}]".format(ofnm)
    ols = []
    with codecs.open(ofnm, "w", "utf8") as ofd:
        for ke, va in sorted(di.items(), key=lambda it: -it[-1]["all"]):
            # all eu am
            ols.append("{}\t{al}".format(
                ke, al=va["all"]))
        ofd.write("\n".join(ols))


def main(indi, oufn, mode, file_list):
    if DBG:
        global au2mets
        global hct
        global act
    au2mets = get_mets(indi, mode, file_list)
    hct, act = pattern2counts(au2mets)
    # only hendecasyllables are written out
    if split_by_origin:
        write_out_with_origin(hct, oufn)
    else:
        write_out(hct, oufn)


if __name__ == "__main__":
    outdir = "analyses/metrics/patterns/counts"
    print("\n# Table 2 - Subcorpus counts DISCO - Running [{}]".format(sys.argv[0]))
    print("- Writing counts to [{}]".format(outdir))

    dnamekeys = OrderedDict([("xv-xvii", "15th-17th"),
                             ("xviii", "18th"),
                             ("xix", "19th")])
    for mode in dnamekeys:
        assert mode in allowed_modes
        # io ----------------------------------------------
        #    input dirs
        try:
            indir = sys.argv[1]
        except IndexError:
            indir = \
                "corpora/disco/tei/{}/per-sonnet".format(dnamekeys[mode])
        #    output files
        try:
            anadir = sys.argv[2]
        except IndexError:
            anadir = outdir

        if not os.path.exists(anadir):
            os.makedirs(anadir)
        ofn = os.path.join(anadir, "patcounts_{}.txt".format(dnamekeys[mode]))
        if split_by_origin:
            ofn = ofn.replace(".txt", "_origin.txt")

        # run ---------------------------------------------
        main(indir, ofn, mode, todo_list)
