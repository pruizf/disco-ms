#coding=utf8

"""Aggregate metrical patterns in Navarro's corpus"""


import codecs
from lxml import etree
import os
import re
import sys

# script path
import inspect
here = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
sys.path.append(here)


# cfg
MODE = "ga-navarro"
DBG = False

# io
#    input dirs
try:
    indir = sys.argv[1]
except IndexError:
    indir = "corpora/navarro/CorpusSonetosSigloDeOroWithEnjambment"

#    output files
try:
    anadir = sys.argv[2]
except IndexError:
    anadir = "analyses/metrics/patterns/counts"


if not os.path.exists(anadir):
    os.makedirs(anadir)
ofn = os.path.join(anadir, "patcounts_{}.txt".format(MODE))

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
    tree = etree.parse(infn)
    n2mets = {int(ele.attrib["n"]):
                  render_met_as_numbers(fix_met(ele.attrib["met"]))
              for ele in tree.xpath("//tei:l", namespaces=nspaces)}
    return n2mets


def get_infos_from_adso_poem(infn):
    """
    Analyze an ADSO poem output returning basic metadata and metrics
    """
    tree = etree.parse(infn)
    # author = tree.xpath("//tei:author", namespaces=nspaces)[0].text
    # title = tree.xpath("//tei:bibl/tei:title", namespaces=nspaces)[0].text
    n2mets = {int(re.sub("[a-z]", "", ele.attrib["n"])):
                  render_met_as_numbers(fix_met(ele.attrib["met"]))
              for ele in tree.xpath("//tei:l", namespaces=nspaces)}
    # return author, title, n2mets
    return n2mets


def get_mets_from_adso(idir):
    """
    Apply L{get_infos_from_adso_poem} to a directory to get
    metrical patterns
    """
    di = {}
    for root, _, fnames in os.walk(idir):
        for fname in fnames:
            if not fname.endswith(".xml"):
                continue
            ffn = os.path.join(root, fname)
            au = re.sub("_.+", "", fname)
            # print(ffn)
            n2metpats = get_infos_from_adso_poem(ffn)
            di.setdefault(au, {})
            di[au][fname] = n2metpats
    return di


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
        print("  - Start pattern counts")
    hendct = {}
    alexct = {}
    for au, infos in sorted(di.items()):
        for ti, patinfo in infos.items():
            for pat in patinfo.values():
                # last stressed syllable on hendecasyllable is 10 at most
                if int(pat.strip().split(" ")[-1]) >= 11:
                    alexct.setdefault(pat, 0)
                    alexct[pat] += 1
                else:
                    hendct.setdefault(pat, 0)
                    hendct[pat] +=1
    return hendct, alexct


def filter_for_printout(di):
    """
    Filter out likely errors in hendecasyllable scansion.
    Assumes patterns where last stress is not on 10 are wrong
    """
    keepkeys = [ke for ke in di if ke.endswith("10")]
    keepitems = {ke: di[ke] for ke in keepkeys}
    return keepitems


def write_out(di, ofnm):
    ols = []
    with codecs.open(ofnm, "w", "utf8") as ofd:
        for ke, va in sorted(di.items(), key=lambda it:-it[-1]):
            ols.append("{}\t{}".format(ke, va))
        ofd.write("\n".join(ols))


def main(indi, oufn):
    if DBG:
        global au2mets
        global hct
        global act
    print("\n# Table 2 - Subcorpus counts Navarro - Running [{}]".format(sys.argv[0]))
    print "- Writing counts to [{}]".format(oufn)

    au2mets = get_mets_from_adso(indi)
    hct, act = pattern2counts(au2mets)
    # only hendecasyllables are written out
    write_out(hct, oufn)


if __name__ == "__main__":
    main(indir, ofn)