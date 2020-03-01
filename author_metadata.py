#coding=utf8

"""
Create author metadata table for paper
"""

from collections import OrderedDict
from lxml import etree
import os
import sys

# IO
corpus_dir = "corpora/disco/tei"
periods = ["15th-17th", "18th", "19th"]
period_paths = OrderedDict()
for period in periods:
    period_paths[period] = os.path.join(corpus_dir, "{}{}per-author".format(period, os.sep))
outf = "analyses/author_metadata.txt"

nspaces = {'tei': 'http://www.tei-c.org/ns/1.0'}

DBG = False


def parse_file(fpath, mdd):
    """Extract metadata from each file"""
    tree = etree.parse(fpath)
    # look for floruit first (minority of cases)
    try:
        orig = tree.xpath("//tei:floruit/tei:placeName/tei:bloc/text()", namespaces=nspaces)[0]
    except IndexError:
        # look for birth if no floruit (general case)
        try:
            orig = tree.xpath("//tei:birth/tei:location/tei:placeName/tei:bloc/text()",
                              namespaces=nspaces)[0]
        except IndexError:
            #print(u"    {}".format(fpath.decode(encoding="utf-8")))
            # this was checked manually, authors 300g and 485n are Latin American
            orig = u"América" if "disco300g" in fpath or "disco485n" in fpath \
                   else u"Europa"
    sex = tree.xpath("//tei:sex/@content",
                      namespaces=nspaces)[0]
    nbr_sonnets = tree.xpath("//tei:measure[@unit='sonnets']/text()",
                             namespaces=nspaces)[0]
    mdd[orig][sex] += 1
    mdd["sonnets"] += int(nbr_sonnets)
    return mdd


def parse_dir(dpath, mdd):
    """Apply `parse_file` to a directory"""
    for fn in os.listdir(dpath):
        ffn = os.path.join(dpath, fn)
        mdd.update(parse_file(ffn, mdd))
    return mdd


if __name__ == "__main__":
    print("# Table 1 - Author metadata - Running [{}]".format(sys.argv[0]))
    print("- Writing author metadata to [{}]".format(outf))
    # delete old version as write in append
    if os.path.exists(outf):
        os.remove(outf)
    # collect table data
    corpus_md = OrderedDict()
    for period_name, dname in period_paths.items():
        md = {u"Europa": {"F": 0, "M": 0},
              u"América": {"F": 0, "M": 0},
              "sonnets": 0}
        if DBG:
            print("- {}".format(dname))
        corpus_md[period_name] = parse_dir(dname, md)
    # write out table data
    with open(outf, "a") as oufh:
        for per, vals in corpus_md.items():
            am = sum(vals[u"América"].values())
            eu = sum(vals["Europa"].values())
            oufh.write("# {}\n".format(per))
            oufh.write("- Sonnets: {}\n".format(vals["sonnets"]))
            oufh.write("- Authors: {}\n".format(am + eu))
            oufh.write("- Female: {}\n".format(vals["Europa"]["F"] + vals[u"América"]["F"]))
            oufh.write("- Male: {}\n".format(vals["Europa"]["M"] + vals[u"América"]["M"]))
            oufh.write("- America: {}\n".format(am))
            oufh.write("- Europe: {}\n".format(eu))
