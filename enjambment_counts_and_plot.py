"""
Generate enjambment counts for DISCO manuscript
"""

from collections import OrderedDict as od
from lxml import etree
import matplotlib.pyplot as plt
from matplotlib import rcParams as mrc
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter)
import numpy as np
import os
from pprint import pprint
from pyexcel_ods import save_data
import sys

from analyze_corpus_overlap import authors_d as ad
import utils_new as un


# Config ======================================================================
DBG = False
# whether to count Spang (1983) 'expansion' (subj/obj split from its verb)
include_expansion = False
# use files where enjambment across stanza boundary was validated by hand
use_hand_validated = True

# parts to run
#   count: create counts, stz_table: result- table at stanza boundaries, plot: separate plots per period
#   plot_grouped: single plot for all periods, validate: create line tables for manual validation
runconfig = {"count": 1, "stz_table": 1, "plot": 1, "plot_grouped": 1, "validate": 1}
if runconfig["plot"] or runconfig["plot_grouped"]:
    runconfig.update({"count": 1})

# plots
annotate_grouped_plot = True
plotdpi = 600
# colors = ["forestgreen", "mediumseagreen", "darkorange", "royalblue"]
plotcolors = ("tab:red", "tab:orange", "tab:green", "tab:blue")
# labels for plots
labels = {"navarro": "Navarro et al.\nGolden Age",
          "15th-17th": "DISCO Golden Age",
          "18th": "DISCO 18th",
          "19th": "DISCO 19th"}

figtitle_indiv = "Enjambment distribution"
figtitle_grouped = "Enjambment distribution in the DISCO corpus and in Navarro et al.'s Golden Age corpus"
titlesize = 10

# IO ==========================================================================

# Corpora -----------------------------
disco_teidir = "corpora/disco/tei"
disco_subdirs = ['15th-17th', '18th', '19th']
adso_dir = "corpora/navarro/CorpusSonetosSigloDeOroWithEnjambment"
# Selected corpora
dirs_todo = []
for sc_name in disco_subdirs:
    dirs_todo.append(os.path.join(disco_teidir,
                                  os.path.join(sc_name, "per-sonnet")))
dirs_todo.insert(0, adso_dir)
if use_hand_validated:
    dirs_todo = ["{}-validated".format(dname) for dname in dirs_todo]

# Outputs -----------------------------
oudir = "analyses/enjambment/enj_and_expansion" if include_expansion \
    else "analyses/enjambment/enj_no_expansion"
if use_hand_validated:
    oudir = oudir.replace("enjambment", "enjambment-validated")
if not os.path.exists(oudir):
    os.makedirs(oudir)
#   Tables
oufn_tp = "enjambment_counts_{}.txt" if include_expansion \
    else "enjambment_counts_noex_{}.txt"
#   ODS file for enjambment cases across stanza boundary
stz_ods = os.path.join(oudir, "enjambment_across_stanza_all.ods")
if not include_expansion:
    stz_ods = stz_ods.replace("_all", "_noex_all")
#   Plots
period_plot_tp = "plot_enjambment_{}.png" if include_expansion \
    else "plot_enjambment_noex_{}.png"
plot_grouped_fname = "plot_enjambment_grouped"
if not include_expansion:
    plot_grouped_fname = plot_grouped_fname.replace("_grouped", "_noex_grouped")


# Functions ===================================================================

def count_enjambment_per_subcorpus(sd, remove_list=[]):
    """
    Compute enjambment counts and percentages per line for files in a directory.

    Skips poems where the line count is not 14.

    Parameters
    ----------
    sd : str
        Path to input directory
    remove_list : list
        List with infos re filenames to skip (e.g. avoid DISCO/Navarro overlap)

    Returns
    -------
    tuple
        Contains (1) a dict with number of enjambments at each line position
        in a corpus and percentage over the total of enjambed lines and (2)
        the number of poems skipped in the corpus (when line count not 14)
    """
    # nbr of poems in dir where nbr of lines != 14
    count_not_14 = 0
    enj = {}
    for fn in os.listdir(sd):
        keep = un.check_file_keep(fn, remove_list)
        if not keep:
            continue
        ffn = os.path.join(sd, fn)
        tree = etree.parse(ffn)
        fcounts, is_not_14 = un.find_enjambment(tree, ffn,
                                                exclude_expansion=not include_expansion)
        count_not_14 += is_not_14
        # for enjambment counts, skip poem if does not have 14 lines
        if bool(is_not_14):
            continue
        for iidx in fcounts:
            enj.setdefault(iidx, {"counts": {"B": 0, "O": 0},
                                  "percent": {"B": 0, "O": 0}})
            enj[iidx]["counts"][fcounts[iidx]] += 1
    total_enj = sum([enj[ke]["counts"]["B"] for ke in enj])
    total_not = sum([enj[ke]["counts"]["O"] for ke in enj])
    for ke in enj:
        enj[ke]["percent"]["B"] = 100 * float(enj[ke]["counts"]["B"]) / total_enj
        enj[ke]["percent"]["O"] = 100 * float(enj[ke]["counts"]["O"]) / total_not
    return enj, count_not_14


def write_table(di, of, sfx, stanza_only=False):
    of.write("# {}\n".format(sfx))
    ols = []
    for ke, va in sorted(di.items()):
        outkey = "{}-{}".format(str.zfill(str(ke), 2), str.zfill(str(ke+1), 2))
        ol = "{}\t{}\t{:0.2f}\n".format(outkey,
                                        va["counts"]["B"], va["percent"]["B"])
        if str(ke).startswith("14"):
            continue
        if stanza_only and outkey[0:2] not in ("04", "08", "11"):
            continue
        ols.append(ol)
    of.write("".join(ols))
    of.write("\n")
    of.flush()


def create_plot(di, of, label, color):
    """
    Creates one plot per period for enjambment data.

    Parameters
    ----------
    di : dict
        Data to plot.
    of : str
        Output path to save plot to.
    label : dict
        Dictionary with label keys and spelled out version of labels.
    color : str
        Name of a color from :obj:`matplotlib.colors`.
        See `color list<https://matplotlib.org/3.1.0/gallery/color/named_colors.html`_.
    """
    plt.rcdefaults()
    #mrc["font.sans-serif"].append('TexGyre Heros')
    # Liberation Sans looks better than TexGyre Heros
    mrc["font.family"] = 'Liberation Sans'
    fig, ax = plt.subplots()

    # Figure title
    # fig.subplots_adjust(top=0.85)
    # fig.suptitle(figtitle_indiv, fontsize=titlesize, fontweight="bold")

    # Data
    positions = ["{}-{}".format(str.zfill(str(ke),2),
                                str.zfill(str(ke+1), 2))
                 for ke in di if not str(ke).startswith("14")]
    values = [di[ke]["percent"]["B"]
              for ke in di if not str(ke).startswith("14")]

    values_counts = [di[ke]["counts"]["B"]
                     for ke in di if not str(ke).startswith("14")]

    ax.barh(positions, values, align='center', color=color)
    ax.set_yticks(positions)
    ax.set_yticklabels(positions)
    ax.invert_yaxis()  # labels read top-to-bottom

    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.xaxis.set_minor_locator(MultipleLocator(1))
    # set this otherwise no label printed
    ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))

    # Annotate bars https://stackoverflow.com/questions/30228069
    for i, v in enumerate(values):
        ax.text(v + 0.15, i + 0.15, "{:0.2f}".format(v), color="dimgrey")
        ax.text(v + 1.5, i + 0.15, "({})".format(values_counts[i]), color="dimgrey")
    ax.set_xlabel('Percentage of enjambments')
    ax.set_ylabel('Position')
    ax.set_title("{}".format(label))

    # Hide the right and top spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    plt.savefig(of)


def create_plot_grouped(percents_by_period, counts_by_period, data_by_period_and_position,
                        labels_to_plot=labels,
                        colorlist=plotcolors):
    """
    Creates one plot per period for enjambment data.

    Parameters
    ----------
    percents_by_period : dict
        Percentage data to plot.
    counts_by_period : dict
        Count data to plot.
    data_by_period_and_position : dict
        Data hashed first by period then by position. Not needed for the plots,
        kept as previous version of script used it.
    labels_to_plot : dict
        Dictionary with label keys and spelled out version of labels.
    colorlist : tuple
        List of colors from :obj:`matplotlib.colors`.
        See `color list<https://matplotlib.org/3.1.0/gallery/color/named_colors.html`_.
    """
    # groups by position (not needed to plot, kept from earlier script)
    data_by_position = {}
    counts_by_position = {}
    for position in range(1, 14):
        data_by_position.setdefault(position, [])
        counts_by_position.setdefault(position, [])
        for ke in labels_to_plot:
            data_by_position[position].append(
                data_by_period_and_position[ke][position]["percent"]["B"])
            counts_by_position[position].append(
                data_by_period_and_position[ke][position]["counts"]["B"])

    if DBG:
        pprint(data_by_position)

    plt.rcdefaults()
    mrc["font.family"] = 'Liberation Sans'
    mrc['font.size'] = 8
    fig = plt.figure()

    # Figure title
    # https://stackoverflow.com/questions/55767312/how-to-position-suptitle
    #fig.subplots_adjust(top=0.83)
    fig.subplots_adjust(top=2.5)
    fig.suptitle(figtitle_grouped, fontsize=titlesize, fontweight="bold")

    ax = fig.add_subplot(111)
    bar_width = 0.2
    # plot all positions for a period
    for idx, ke in enumerate(labels_to_plot):
        # skip line 14 as never enjambed
        curbar = percents_by_period[ke][0:-1]
        curbar_counts = counts_by_period[ke][0:-1]
        yposis = [y + idx * bar_width for y in np.arange(len(curbar))]
        yposis_c = [y + idx * bar_width for y in np.arange(len(curbar_counts))]
        ax.barh(yposis, curbar, bar_width, color=colorlist[idx], edgecolor='w',
                label=labels_to_plot[ke], align='center')
        if annotate_grouped_plot:
            for i, v, w in zip(yposis, curbar, curbar_counts):
                percent = "{:0.2f}".format(v) if v != 0 else 0
                countv = "({})".format(w) if w != 0 else ""
                ax.text(v + 0.3, i + bar_width/3.25, "{} {}".format(percent, countv),
                        color="black", fontsize=3.5)
    ax.set_ylabel('Line position')
    ax.set_xlabel('Percentage of enjambments (counts in parentheses)')
    # Add yticks on the middle of the group bars
    ax.set_yticks([r + 1.5 * bar_width for r in range(
        len(percents_by_period.values()[0][0:-1]))])

    ax.xaxis.set_major_locator(MultipleLocator(1))
    ax.xaxis.set_minor_locator(MultipleLocator(0.5))
    # set this otherwise no label printed
    ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))

    # label y axis with positions
    posis = ["{}-{}".format(str.zfill(str(x), 2), str.zfill(str(x + 1), 2))
             for x in range(1, 14)]
    ax.set_yticklabels(posis)

    # labels read top-to-bottom
    ax.invert_yaxis()

    # Hide the right and top spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    # Legend on top
    plt.legend(edgecolor='white')
    # https://matplotlib.org/3.1.1/tutorials/intermediate/legend_guide.html
    plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left',
               ncol=4, mode="expand", borderaxespad=-0., edgecolor='w',
               fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(oudir, "{}.svg".format(plot_grouped_fname)))
    plt.savefig(os.path.join(oudir, "{}.png".format(plot_grouped_fname)), dpi=plotdpi)
    plt.savefig(os.path.join(oudir, "{}.jpg".format(plot_grouped_fname)), dpi=plotdpi)
    print("- Writing final plot to file [{}.jpg]\n".format(plot_grouped_fname))
    #plt.savefig(os.path.join(oudir, "{}.tif".format(plot_grouped_fname)), dpi=plotdpi)
    #plt.savefig(os.path.join(oudir, "{}.tiff".format(plot_grouped_fname)), dpi=plotdpi)
    plt.savefig(os.path.join(oudir, "{}.eps".format(plot_grouped_fname)), dpi=plotdpi)


# Main ========================================================================

if __name__ == "__main__":
    print("\n\n# Table 5 and Figure 2 - Enjambment - Running [{}]".format(sys.argv[0]))
    print("- Writing results to [{}]".format(oudir))
    # remove previous version since write in append mode
    try:
        os.remove(os.path.join(oudir, oufn_tp.format("all")))
        os.remove(os.path.join(oudir, oufn_tp.format("stanza_boundaries")))
    # first time
    except OSError:
        pass
    # OrderedDict for validation spreadsheet
    ods_all_data = od()
    # for grouped results
    all_enj_dicts = {}
    enj_by_period_percents = {}
    enj_by_period_counts = {}

    # iterate over subcorpora
    for idx, dirpath in enumerate(dirs_todo):
        # subcorpus name for plots etc
        sc_name = os.path.basename(os.path.split(dirpath)[0])
        # counts per line-position --------------------------------------------
        if runconfig["count"]:
            if DBG:
                print("== {} ==".format(sc_name))
            # remove_list will avoid overlap btn Navarro and DISCO
            list_to_remove = ad.keys() if "15th-17th" in dirpath else []
            # for these counts, poems with number of lines != 14 are left out
            ecounts, nbr_not_14 = count_enjambment_per_subcorpus(
                dirpath, remove_list=list_to_remove)
            if DBG:
                print(" - Poems not 14 lines [{}] of [{}] ({:.2f}%)".format(
                    nbr_not_14, len(os.listdir(dirpath)),
                    100*nbr_not_14/(float(len(os.listdir(dirpath))))))
                pprint(ecounts)
            # table with count and percent per line-position per period
            with open(os.path.join(oudir, oufn_tp.format("all")), "a") as ofh:
                write_table(ecounts, ofh, sc_name)
            # same table restricted to positions across stanza-boundary
            if runconfig["stz_table"]:
                with open(os.path.join(
                        oudir, oufn_tp.format("stanza_boundaries")), "a") as ofh:
                    write_table(ecounts, ofh, sc_name, stanza_only=True)
        # plots for above counts -----------------------------------------------
        if runconfig["plot"]:
            label = labels[sc_name]
            create_plot(ecounts, os.path.join(oudir, period_plot_tp.format(sc_name)),
                        label, plotcolors[idx])
            # feed overall dict for grouped results
            if runconfig["plot_grouped"]:
                all_enj_dicts[sc_name] = ecounts
                enj_by_period_percents[sc_name] = [va["percent"]["B"] for va in ecounts.values()]
                enj_by_period_counts[sc_name] = [va["counts"]["B"] for va in ecounts.values()]
        # tables for manual validation ----------------------------------------
        # create tables to validate enjambment across stanza boundaries
        # (no need to recreate them unless input corpus changes)
        # note: these tables contain poems with nbr lines != 14,
        #       but they are left out for counts
        if runconfig["validate"]:
            oufname = "enjambment_across_stanza_{}.txt".format(sc_name) \
                if include_expansion else "enjambment_across_stanza_noex_{}.txt".format(
                sc_name)
            stz_fn = os.path.join(
                oudir, oufname.format(sc_name))
            # puts them together in an ODS file
            ods_sc_data = un.extract_stanza_boundaries(
                dirpath, stz_fn, sc_name,
                remove_list=ad, exclude_expansion=not include_expansion)
            ods_all_data.update(ods_sc_data)
            save_data(stz_ods, ods_all_data)
    # plot grouped results ----------------------------------------------------
    if runconfig["plot_grouped"]:
        create_plot_grouped(enj_by_period_percents, enj_by_period_counts, all_enj_dicts, labels)
