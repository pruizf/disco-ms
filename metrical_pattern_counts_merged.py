#coding=utf8

"""
Merge pattern counts across all disco periods + navarro
"""

__author__ = 'Pablo Ruiz'
__date__ = '18/11/17'
__email__ = 'pabloruizfabo@gmail.com'


import codecs
from collections import OrderedDict
import os
import pandas as pd
from pyexcel_ods import save_data
import sys


basedir = "analyses/metrics/patterns/counts"
if not os.path.exists(basedir):
    os.makedirs(basedir)

# disco
cts_19 = os.path.join(basedir, "patcounts_19th.txt")
cts_18 = os.path.join(basedir, "patcounts_18th.txt")
cts_ga = os.path.join(basedir, "patcounts_15th-17th.txt")
# navarro
cts_ga_navarro = os.path.join(basedir, "patcounts_ga-navarro.txt")
oufi = os.path.join(basedir, "patcounts_all.txt")
ou_ods = "data/metrical_pattern_summary.ods"

DBG = False


def read_countfile(fn):
    """Read the files with metrical pattern counts, return dict"""
    if DBG:
        print "- Reading [{}]".format(fn)
    return {ll.strip().split("\t")[0]: int(ll.strip().split("\t")[1])
            for ll in codecs.open(fn, "r", "utf8")}


def analyze_pattern(pat):
    """
    Return whether has stress at positions 6 7, and
    number of stress clashes, and number of stressed positions
    """
    has_67 = False
    antis = 0
    if "6 7" in pat:
        has_67 = True
    splpat = [int(x) for x in pat.strip().split(" ")]
    for idx, stress_posi in enumerate(splpat):
        try:
            if splpat[idx+1] == stress_posi + 1:
                antis += 1
        except IndexError:
            pass
    return {"has_67": has_67, "anti_count": antis,
            "stress_count": len(splpat)}


def merge_counts(h19, h18, hga, hga_navarro):
    """
    Take the pattern-count dicts for each period and write the counts out
    and percent of pattern compared to all patterns in a period.
    Outputs all counts first then all percentages.
    """
    ols = []
    total_19 = sum(h19.values())
    total_18 = sum(h18.values())
    total_ga = sum(hga.values())
    total_ga_navarro = sum(hga_navarro.values())
    total_all = total_19 + total_18 + total_ga
    allkeys = set(h19.keys() + h18.keys() + hga.keys() + hga_navarro.keys())
    for ke in allkeys:
        ol = [ke]
        ana = analyze_pattern(ke)
        # append analysis
        ol.extend((ana["stress_count"], int(ana["has_67"]),
                   ana["anti_count"]))
        # append raw counts
        ke_all = 0
        try:
            ol.append(h19[ke])
            ke_all += h19[ke]
        except KeyError:
            ol.append(0)
        try:
            ol.append(h18[ke])
            ke_all += h18[ke]
        except KeyError:
            ol.append(0)
        try:
            ol.append(hga[ke])
            ke_all += hga[ke]
        except KeyError:
            ol.append(0)
        try:
            ol.append(hga_navarro[ke])
        except KeyError:
            ol.append(0)
        # append percentages
        try:
            ol.append(100*(float(h19[ke])/total_19))
        except KeyError:
            ol.append(0)
        try:
            ol.append(100*(float(h18[ke])/total_18))
        except KeyError:
            ol.append(0)
        try:
            ol.append(100*(float(hga[ke])/total_ga))
        except KeyError:
            ol.append(0)
        try:
            ol.append(100 * (float(hga_navarro[ke]) / total_ga_navarro))
        except KeyError:
            ol.append(0)
        # append overall count and percentage for the key
        ol.append(ke_all)
        try:
            ol.append(100 * (float(ke_all) / total_all))
        except KeyError:
            ol.append(0)
        ols.append("\t".join([str(round(it, 2))
                        if isinstance(it, float) else str(it) for it in ol]))
    return ols


def write_out(lines, ofn):
    with codecs.open(ofn, "w", "utf8") as ofd:
        # ofd.write("pat\tc19\tp19\tc18\tp18\tcGA\tpGA\n")
        ofd.write("pat\tstressed\t67\tantis\t" + \
                  "c19\tc18\tcGA\tcAGA\t" + \
                  "p19\tp18\tpGA\tpAGA\tcALL\tpALL\n")
        ofd.write("\n".join(lines))


def create_summary_for_plot(ifn, ofn, nbrrows=15):
    """
    Create an ODS sheet that the metrical pattern plot will be based on.
    """
    df = pd.read_csv(ifn, sep="\t")
    new_colnames = OrderedDict([('pat', 'Pattern'),
                                ('pAGA', "Navarro et al.\nGolden Age"),
                                ('pGA', "DISCO Golden Age"),
                                ('p18', 'DISCO 18th'),
                                ('p19', 'DISCO 19th'),
                                ('pALL', 'All periods')])
    df = df[['pat', 'pAGA', 'pGA', 'p18', 'p19', 'pALL']]
    df.rename(columns = {ke:va for (ke,va) in new_colnames.items()},
              inplace=True)
    df = df.sort_values(['All periods'], ascending=[False])
    summary = df.head(nbrrows)
    # for pyexcel_ods
    out_dict = {"Sheet1": [new_colnames.values()]}
    for idx, row in summary.iterrows():
        out_row = [row[va] for va in new_colnames.values()]
        out_dict["Sheet1"].append(out_row)
    save_data(ofn, out_dict)


def main():
    print("\n# Table 2 - Merged counts - Running [{}]".format(sys.argv[0]))
    print("- Writing all counts to [{}]".format(oufi))
    print("- Writing summary for pattern plot to [{}]".format(ou_ods))
    c19 = read_countfile(cts_19)
    c18 = read_countfile(cts_18)
    cga = read_countfile(cts_ga)
    cga_navarro = read_countfile(cts_ga_navarro)
    olines = merge_counts(c19, c18, cga, cga_navarro)
    write_out(olines, oufi)
    create_summary_for_plot(oufi, ou_ods)


if __name__ == "__main__":
    main()