"""
Get descriptive statistics on DISCO corpus (also as compared to Navarro corpus),
especially combinations of binary/ternary rhythm.
"""

__author__ = 'Pablo Ruiz'
__date__ = '01/04/18'
__email__ = 'pabloruizfabo@gmail.com'

import codecs
from collections import Counter
from nltk.util import ngrams
import os
import sys

import utils
import utils_new as un


# Options

# binary/ternary classification: original, 2018 or 2019, see utils.py
bintermode = "2019"
assert bintermode in ("original", "2018", "2019", "XXX")
DBG = False

# IO

# Corpus parts
navarro_path = "corpora/navarro/CorpusSonetosSigloDeOro"
disco_ga_path = "corpora/disco/tei/15th-17th/per-sonnet"
disco_18th = "corpora/disco/tei/18th/per-sonnet"
disco_19th = "corpora/disco/tei/19th/per-sonnet"
# to avoid disco-navarro overlap
todo_list = "data/filenames_disco_only.txt"

# Outputs
anapath = "analyses/metrics/binary_ternary_{}/".format(bintermode)
bigram_out_all = anapath + "bigram_all_corpus.tsv"
bigram_binter_examples = anapath + "bigram_binary-ternary_examples_{}.txt"
binter_out = anapath + "binary-ternary_results.txt"

if not os.path.exists(anapath):
    os.makedirs(anapath)

# remove at beginning since writes in append
if os.path.exists(binter_out):
    os.remove(binter_out)


def find_metrical_info_for_collection(fiter):
    """
    Aggregate metrical info for a collection (e.g. a directory).
    Return a dictionary hashed by filename containing
    the metrical info.
    Shape of metrical info is: {line_nbr (int): pattern (e.g. 1-3-6)}
    @param fiter: Iterable with files for the collection
    """
    cmets = {}
    for idx, fn in enumerate(fiter):
        cmets[fn] = utils.get_met_from_poem(fn)
        if DBG and idx and not idx % 1000:
            print("Done {} files".format(idx))
    return cmets


def aggregate_mets(mdi, classif=False, bt=False):
    """
    Given dict mdi, of shape described in L{find_metrical_info_for_collection},
    aggregate counts for each pattern at corpus level
    @param classif: Classify or not into a small set of patterns (Heroic, Melodic etc.)
    @param bt: Classiffy or not into binary or ternary
    """
    pcounts = {}
    for fn, infos in mdi.items():
        patterns = infos.values()
        for pattern in patterns:
            if classif:
                pattern = utils.classify_pattern_exact(pattern)
            elif bt:
                pattern = utils.classify_pattern_binary_ternary(
                    pattern, mode=bintermode)
            pcounts.setdefault(pattern, {"count": 0})
            pcounts[pattern]["count"] += 1
    # add percentages
    total = sum([val["count"] for val in pcounts.values()])
    for fn, infos in pcounts.items():
        infos["percent"] = 100 * float(infos["count"]) / total
    return pcounts


def aggregate_bigrams(mdi, bt=False, patlog=None):
    """
    Given dict mdi, of shape described in L{find_metrical_info_for_collection},
    aggregate counts for each bigram-pattern at corpus level
    @param bt: directs whether to calculate binary-ternary sequences or not
    @param patlog: Path to a file to log line-positions where ternary-binary
    patterns occur (to later use positions to get sonnet text examples)
    """
    bgcounts = {}
    bgcounts_p = {}
    ter_bi_stanza_counts = {"Q1": 0, "Q2": 0, "T1": 0, "T2": 0}
    for fn, infos in mdi.items():
        patterns = infos.values()
        file_bigrams = list(ngrams(patterns, 2))
        file_bigrams_bt = \
            [tuple(utils.classify_bigram_binary_ternary(fb, bintermode)["types"])
             for fb in file_bigrams]
        if bt:
            counted_file_bigrams = Counter(file_bigrams_bt)
        else:
            counted_file_bigrams = Counter(file_bigrams)
        # log ter, bin pattern
        if bt and ("ter", "bin") in counted_file_bigrams and patlog is not None:
            ter_bi_positions = ["_".join((str(idx+1), str(idx+2)))
                                for (idx, i) in enumerate(file_bigrams_bt)
                                if i == ("ter", "bin")]
            patlog.write(u"{}\tter-bin\t{}\t{}\n".format(
                os.path.basename(fn)
                if isinstance(fn, unicode) else
                os.path.basename(fn).decode("utf8"),
                counted_file_bigrams[("ter", "bin")],
                "|".join(ter_bi_positions)))
            # figure out stanza of ocurrence of (ter, bin) bigrams
            utils.find_stanza_for_ternary_binary(
                ter_bi_stanza_counts, ter_bi_positions)
        for bigram in counted_file_bigrams:
            bgcounts.setdefault(bigram, {"count": 0})
            bgcounts[bigram]["count"] += counted_file_bigrams[bigram]
    # reformat
    total = sum([val["count"] for val in bgcounts.values()])
    for bigram, infos in bgcounts.items():
        bgcounts_p[bigram] = bgcounts[bigram]
        try:
            bgcounts_p[bigram]["percent"] = 100 * float(infos["count"]) / total
        except ZeroDivisionError:
            bgcounts_p[bigram]["percent"] = 0.0
    return bgcounts_p, ter_bi_stanza_counts


def head_dictionary(di, period, dtype="mono", n=20):
    """
    Print the first `n` lines of the count-percent dictionary
    per pattern.
    @di: data for period (count and percent of patterns)
    @period: string with a label for period to print
    @dtype: whether dictionary is metrical monograms or bigrams
    (print format changes)
    @n: number of records to print
    """
    print("\n### Period: {} ###\n".format(period))
    for idx, (x, y) in enumerate(sorted(di.items(),
                   key=lambda z: -z[-1]["count"])[0:n]):
        if dtype == "mono":
            print("\t".join([x, str(y["count"]), str(y["percent"])]))
        else:
            print("\t".join(["__".join((x[0], x[1])), str(y["count"]),
                             str(y["percent"])]))


def merge_bigram_counts(di1, di2, di3, di4, ofn, header=None):
    """
    Merge bigram counts and percent from four dictionaries
    @note: This is repetitive wrt L{merge_bigram_counts} but want
    to keep both for now.
    @note: di1 through 4 are dictionaries
    """
    ols = []
    all_keys = list(set(di1.keys() + di2.keys() + di3.keys() + di4.keys()))
    no = ("0", "0")
    for key in sorted(all_keys):
        ol = ["__".join(key)]
        for dico in di1, di2, di3, di4:
            try:
                ol.extend((str(dico[key]["count"]), str(dico[key]["percent"])))
            except KeyError:
                ol.extend(no)
        ols.append("\t".join(ol))
    with codecs.open(ofn, "w", "utf8") as ofh:
        if header is not None:
            header = "\t".join([str(x) for x in header])
            ofh.write(header + "\n")
        ofh.write("\n".join(ols))


def write_binter_per_period(di, periodkey, ofn):
    """
    Dump to a file the infos for the DSH manuscript
    binary-ternary table.
    @param di: dictionary with the data
    @param periodkey: string to identify period in output files
    @param ofn: path to output file
    """
    ols = []
    # ratio ter-bin / ter-ter
    ratio_tb_tt = (di[('ter', 'bin')]["percent"] /
                   float(di[('ter', 'ter')]["percent"]))
    for ke, infos in sorted(
            di.items(), key=lambda it: (un.terbinsort[0].index(it[0][0]),
                                        un.terbinsort[1].index(it[0][1]))):
        ol = ["{}-{}".format(ke[0], ke[1]),
              str(infos["count"]), "{:.2f}".format(infos["percent"])]
        ols.append("\t".join(ol))
    with codecs.open(ofn, "a", "utf8") as ofh:
        ofh.write(
            "# Ter-Bin-Oth {}\n".format(un.periodkeys["rom2ara"][periodkey][0]))
        ofh.write("Pattern\tCount\tPercent\n")
        ofh.write("\n".join(ols))
        ofh.write("\nRatio Ter-Bin / Ter-Ter: {:.2f}".format(ratio_tb_tt))
        ofh.write("\n\n")


if __name__ == "__main__":

    print("\n\n# Table 4 - Running [{}]".format(sys.argv[0]))
    print("- Writing binary-ternary pattern data to [{}]".format(binter_out))

    all_dicts = {}

    # xvc = navarro golden age, xv: disco golden age, xviii: disco 18th, xix: disco 19th
    for period in "xvc", "xv", "xviii", "xix":
        if DBG:
            print("\n## START [{}] ==\n".format(un.periodkeys["rom2ara"][period][0]))
        # handle to log bigram examples
        exfh = codecs.open(
            bigram_binter_examples.format(
                un.periodkeys["rom2ara"][period][1]), "w", "utf8")
        # files to handle
        if period == "xv":
            inlist = utils.filter_input_file_list(disco_ga_path, todo_list)
        elif period == "xvc":
            inlist = utils.get_navarro_file_list(navarro_path)
        elif period == "xviii":
            # yes, the 19th century function gets both 19th and 18th
            inlist = utils.get_19th_century_file_list(disco_18th)
        else:
            inlist = utils.get_19th_century_file_list(disco_19th)
        # obtain infos
        mets = find_metrical_info_for_collection(inlist)
        mono_counts = aggregate_mets(mets)
        mono_classif_counts = aggregate_mets(mets, classif=True)
        mono_bt_counts = aggregate_mets(mets, bt=True)
        bigram_counts, _ = aggregate_bigrams(mets)
        bigram_bt_counts, stanza_counts = \
            aggregate_bigrams(mets, bt=True, patlog=exfh)

        stanza_counts = utils.postprocess_ternary_binary_per_stanza(stanza_counts)

        # 'mono': unigrams, 'big': bigrams; 'bt': 'binary-ternary'
        all_dicts[period] = {"mono": mono_counts,
                             "monoclass": mono_classif_counts,
                             "monobt": mono_bt_counts,
                             "big": bigram_counts,
                             "bigbt": bigram_bt_counts,
                             "bigbt_stanzas": stanza_counts}

        # log to console
        if DBG:
            head_dictionary(mono_counts, period, dtype="mono", n=30)
            head_dictionary(bigram_counts, period, dtype="bigram", n=100)

        # write binary-ternary to file
        write_binter_per_period(all_dicts[period]["bigbt"], period, binter_out)

    # merge counts

    discoga_big = all_dicts["xv"]["big"]
    navarro_big = all_dicts["xvc"]["big"]
    disco18_big = all_dicts["xviii"]["big"]
    disco19_big = all_dicts["xix"]["big"]

    # column headers: '_c' suffix  = count ; '_p' suffix = percentage
    #                  xv = disco golden age ; xvc = navarro
    merge_bigram_counts(discoga_big, navarro_big, disco18_big, disco19_big, bigram_out_all,
                        header=["key", "xv_c", "xv_p", "xvc_c", "xvc_p", "xviii_c", "xviii_p",
                                "xix_c", "xix_p"])

    # clean up
    exfh.close()
