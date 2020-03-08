"""
Plots metrical patterns for figure in DISCO manuscript
Inspired by https://stackoverflow.com/questions/21397549/
"""

# note: when bars add up to 100% the following format is good
# https://matplotlib.org/3.1.1/gallery/lines_bars_and_markers/horizontal_barchart_distribution.html#sphx-glr-gallery-lines-bars-and-markers-horizontal-barchart-distribution-py

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import rcParams as mrc
from matplotlib import colors as pltcolors
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter)
import os
from pandas_ods_reader import read_ods
import sys


# IO
# Data source
ods = "data/metrical_pattern_summary.ods"
# Outputs
oudir = "analyses/metrics"
of_both = os.path.join(oudir, os.path.splitext(os.path.basename(ods))[0] + ".png")
of_both_eps = os.path.join(oudir, os.path.splitext(os.path.basename(ods))[0] + ".eps")
of_both_jpg = os.path.join(oudir, os.path.splitext(os.path.basename(ods))[0] + ".jpg")
of_periods = os.path.join(oudir, os.path.splitext(os.path.basename(ods))[0] + "_per_period.png")
of_all = os.path.join(oudir,
                      os.path.splitext(os.path.basename(ods))[0] + "_all_periods.png")
if not os.path.exists(oudir):
    os.makedirs(oudir)

print("\n\n# Figure 1 - Metrical patterns - Running [{}]".format(sys.argv[0]))
print("- Writing results to [{}]".format(oudir))


# Config

separate_figures = False
# place subplots vertically or not
# (added at end, as horizontally-placed too small on print proof)
vertical_grouped = True
plotdpi = 600

plt.rcdefaults()
mrc["font.family"] = 'Liberation Sans'

# title for joint figure
fig_title = "Metrical pattern distribution in the DISCO corpus and in Navarro et al.'s Golden Age corpus"
titlesize = 14
if not vertical_grouped:
    # large
    mrc.update({'font.size': 11})
    # small
    # titlesize = 8
    # mrc.update({'font.size': 6})

# Get data
df = read_ods(ods, 1)
data = np.array(df.iloc[:, 1:5])
# respect shapes for loops that draw plot
data_old = data
data = np.transpose(data)
percentages = data_old
# row labels
patterns = df.Pattern
# group labels
labels = df.columns[1:-1]


# Stacked bar chart for period comparison =====================================

# see https://matplotlib.org/3.1.1/gallery/subplots_axes_and_figures/subplot.html
if separate_figures:
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111)
else:
    if vertical_grouped:
        fig = plt.figure(figsize=(9, 14))
        fig.subplots_adjust(top=0.95, hspace=0.15)
        ax = fig.add_subplot(211)
    else:
        # large
        fig = plt.figure(figsize=(18, 7))
        fig.subplots_adjust(top=0.9, wspace=0.15, hspace=0)
        # small
        # fig = plt.figure(figsize=(7, 2.72))
        # fig.subplots_adjust(top=0.9, wspace=0.3, hspace=0)
        ax = fig.add_subplot(121)

colors = ["tab:red", "tab:orange", "tab:green", "tab:blue", "tab:purple"]
patch_handles = []
left = np.zeros(len(patterns)) # left alignment of data starts at zero
y_pos = np.arange(len(patterns))
for i, d in enumerate(data):
    patch_handles.append(ax.barh(y_pos, d,
        color=colors[i%len(colors)], align='center', left=left,
        label=labels[i%len(labels)]))
    # accumulate the left-hand offsets
    left += d

# go through all of the bar segments and annotate
for j in xrange(len(patch_handles)):
    for i, patch in enumerate(patch_handles[j].get_children()):
        bl = patch.get_xy()
        x = 0.5*patch.get_width() + bl[0]
        if vertical_grouped:
            y = 0.6*patch.get_height() + bl[1]
        else:
            y = 0.7*patch.get_height() + bl[1] if percentages[i,j] > 2 \
                else 0.675*patch.get_height() + bl[1]
        #https://stackoverflow.com/questions/51350872/
        color = colors[i%len(colors)]
        color_rgb = pltcolors.hex2color(pltcolors.cnames[color.replace("tab:", "")])
        re, gr, bl = color_rgb
        text_color = 'white' if re * gr * bl < 0.5 else 'dimgrey'
        if vertical_grouped:
            ax.text(x,y, "{:.2f}".format(percentages[i,j]), ha='center',
                    color=text_color, fontweight='bold')
        else:
            # large
            size4font = 10 if percentages[i,j] < 2 else 11
            ax.text(x,y, "{:.2f}".format(percentages[i,j]), ha='center',
                    color=text_color, fontweight='bold', fontsize=size4font)
            # small
            # size4font = 4 if percentages[i,j] < 2 else 5
            # ax.text(x,y, "{:.2f}".format(percentages[i,j]), ha='center',
            #         color=text_color, fontweight='bold', fontsize=size4font)

ax.set_yticks(y_pos)
ax.set_yticklabels(patterns)
# need pad as no tick labels
ax.xaxis.labelpad = 20
ax.set_xlabel('Percentage of lines with pattern per period in DISCO\nand in Navarro et al.\'s Golden Age corpus')
ax.set_ylabel('Pattern')

ax.invert_yaxis()  # labels read top-to-bottom

# Hide the right and top spines
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)

# bottom ticks
ax.xaxis.set_major_locator(MultipleLocator(1))
#ax.xaxis.set_minor_locator(MultipleLocator(2.5))
# no tick labels on bottom
ax.xaxis.set_tick_params(labelbottom=False)
ax.xaxis.set_tick_params(bottom=True, top=False)
# set this if want labels to be printed instead
#ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))

# legend

# lg = plt.legend()
# lg.title = "Periods"
# lg.frameon = False
# lg.get_frame().set_linewidth(0.0)
# lg.get_frame().set_edgecolor('white')

ax.legend(title="Periods", edgecolor='white')

if separate_figures:
    plt.savefig(of_periods, dpi=plotdpi)

# Bar chart for all periods ===================================================

data_all = np.array(df.iloc[:, 5])
if separate_figures:
    fig_all = plt.figure(figsize=(10, 7))
    ax_all = fig_all.add_subplot(111)
else:
    if vertical_grouped:
        ax_all = fig.add_subplot(212)
    else:
        ax_all = fig.add_subplot(122)
    fig.suptitle(fig_title, fontsize=titlesize, fontweight="bold")


ax_all.set_yticks(y_pos)
ax_all.set_yticklabels(patterns)
ax_all.set_xlabel('Percentage of lines with pattern in the complete DISCO corpus')
ax_all.set_ylabel('Pattern')

ax_all.barh(y_pos, data_all, align='center', color=colors[-1])
for i, v in enumerate(data_all):
    if vertical_grouped:
        ax_all.text(v - 0.7, i + 0.125, "{:0.2f}".format(v), color="w",
                    fontweight='bold')
    else:
        # large
        ax_all.text(v - 0.7, i + 0.125, "{:0.2f}".format(v), color="w",
                    fontweight='bold')
        # small
        # ax_all.text(v - 0.7, i + 0.125, "{:0.2f}".format(v), color="w",
        #             fontweight='bold', fontsize=5)




ax_all.invert_yaxis()  # labels read top-to-bottom

# Hide the right and top spines
ax_all.spines['right'].set_visible(False)
ax_all.spines['top'].set_visible(False)

ax_all.xaxis.set_major_locator(MultipleLocator(1))
ax_all.xaxis.set_minor_locator(MultipleLocator(0.5))
# set this otherwise no label printed
ax_all.xaxis.set_major_formatter(FormatStrFormatter('%d'))

if separate_figures:
    plt.savefig(of_all, dpi=plotdpi)
else:
    if vertical_grouped:
        for fn in (of_both, of_both_eps, of_both_jpg):
            fn = fn.replace(".", "_vertical.")
            plt.savefig(fn, dpi=plotdpi, bbox_inches='tight')
            if "jpg" in fn:
                print("- Writing final plot to file [{}]".format(fn))
    else:
        #plt.tight_layout() # bbox_inches cropped better
        plt.savefig(of_both, dpi=plotdpi, bbox_inches='tight')
        plt.savefig(of_both_eps, dpi=plotdpi, bbox_inches='tight')
        plt.savefig(of_both_jpg, dpi=plotdpi, bbox_inches='tight')
